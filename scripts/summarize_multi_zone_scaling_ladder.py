#!/usr/bin/env python3
"""Measure a deterministic reduced-output scaling ladder for multi-zone fixtures.

The helper stays local and fixture-backed. It materializes a 1, 2, 4, 8, and
12-zone ladder, runs the hazard builder in reduced-output mode on each rung,
and records output, reducer, manifest, and hazard-builder timing together with
the existing budget classifications that decide when another live Balfrin
scale step would need more evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.build_hazard_layers as hazard
import scripts.generate_balfrin_multi_release_zone_demo_handoff as handoff
import scripts.summarize_multi_zone_hazard_throughput_profile as throughput
import scripts.summarize_multi_zone_reducer_pressure as reducer_pressure


SCHEMA_VERSION = "multi_zone_scaling_ladder_v1"
DEFAULT_LADDER_ROOT = Path("/tmp/rust_rockfall/multi_zone_scaling_ladder_v1")
DEFAULT_ZONE_COUNTS = (1, 2, 4, 8, 12)
DEFAULT_REDUCER_WORKER_COUNT = 2
DEFAULT_REDUCER_CHUNK_COUNT = 2
DEFAULT_TRAJECTORY_SAMPLES_PER_ZONE = 4
DEFAULT_IMPACT_ROWS_PER_ZONE = 1
DEFAULT_GRID_XMIN = throughput.DEFAULT_GRID_XMIN
DEFAULT_GRID_YMIN = throughput.DEFAULT_GRID_YMIN
DEFAULT_GRID_NCOLS = throughput.DEFAULT_GRID_NCOLS
DEFAULT_GRID_NROWS = throughput.DEFAULT_GRID_NROWS
DEFAULT_GRID_CELLSIZE = throughput.DEFAULT_GRID_CELLSIZE
DEFAULT_THRESHOLD_J = throughput.DEFAULT_THRESHOLD_J
DEFAULT_THRESHOLD_M = throughput.DEFAULT_THRESHOLD_M
DEFAULT_THRESHOLD_MPS = throughput.DEFAULT_THRESHOLD_MPS
LADDER_PRESSURE_OUTPUT_FAMILY_MIX = (
    "trajectory_csv",
    "deposition_csv",
    "impact_events_csv",
    "trajectory_chunk_manifest",
    "reducer_chunk_manifest",
    "trajectory_merge_state",
    "reducer_merge_state",
)


class MultiZoneScalingLadderError(ValueError):
    """User-facing ladder error."""


@dataclass(frozen=True)
class LadderFixture:
    ladder_root: Path
    rung_root: Path
    case_path: Path
    trajectory_dir: Path
    deposition_path: Path
    impact_event_dir: Path
    diagnostics_path: Path
    fixture_manifest_path: Path
    command_plan_path: Path
    release_zone_count: int
    reducer_worker_count: int
    reducer_chunk_count: int
    scenario_count: int
    fixture_fingerprint: str


@dataclass(frozen=True)
class PressureFixture:
    pressure_root: Path
    probe_manifest_path: Path
    command_plan_path: Path
    output_manifest_path: Path
    release_zone_count: int
    reducer_worker_count: int
    reducer_chunk_count: int
    scenario_count: int
    pressure_fingerprint: str


@dataclass(frozen=True)
class LadderRungResult:
    release_zone_count: int
    rung_root: Path
    pressure_report: dict[str, Any]
    fixture: dict[str, Any]
    command_plan_path: Path
    hazard_manifest_path: Path
    hazard_manifest: dict[str, Any]
    timing_breakdown: dict[str, Any]
    output_pressure: dict[str, Any]
    output_budget_validation: dict[str, Any]
    budget_projection: dict[str, Any]
    budget_status: str
    first_budget_failure: dict[str, Any] | None
    hazard_bottleneck: dict[str, Any]
    manifest_size_bytes: int
    reducer_manifest_file_count: int
    reducer_manifest_bytes: int
    sidecar_file_count: int
    sidecar_byte_count: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ladder-root", type=Path, default=None, help="Existing ladder root to summarize.")
    parser.add_argument(
        "--materialize-root",
        type=Path,
        default=None,
        help="Create the deterministic ladder root at this path before summarizing it.",
    )
    parser.add_argument(
        "--zone-counts",
        default=",".join(str(count) for count in DEFAULT_ZONE_COUNTS),
        help="Comma-separated zone counts to materialize in the ladder.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    zone_counts = parse_zone_counts(args.zone_counts)
    try:
        if args.materialize_root is not None:
            report = build_report(args.materialize_root, zone_counts=zone_counts)
        else:
            ladder_root = args.ladder_root or DEFAULT_LADDER_ROOT
            report = build_report(ladder_root, zone_counts=zone_counts)
    except MultiZoneScalingLadderError as exc:
        print(f"multi-zone scaling ladder error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["ladder_status"] == "measured_scratch_root" else 2


def parse_zone_counts(raw_value: str) -> tuple[int, ...]:
    try:
        counts = tuple(int(value.strip()) for value in raw_value.split(",") if value.strip())
    except ValueError as exc:
        raise MultiZoneScalingLadderError("--zone-counts must be a comma-separated list of integers") from exc
    if not counts:
        raise MultiZoneScalingLadderError("--zone-counts must contain at least one rung")
    if len(set(counts)) != len(counts):
        raise MultiZoneScalingLadderError("--zone-counts must not contain duplicates")
    if any(count <= 0 for count in counts):
        raise MultiZoneScalingLadderError("--zone-counts must be greater than 0")
    if tuple(sorted(counts)) != counts:
        raise MultiZoneScalingLadderError("--zone-counts must be in ascending order")
    return counts


def build_report(ladder_root: Path, *, zone_counts: tuple[int, ...] = DEFAULT_ZONE_COUNTS) -> dict[str, Any]:
    ladder_root = ladder_root.resolve()
    if ladder_root.exists():
        shutil.rmtree(ladder_root)
    ladder_root.mkdir(parents=True, exist_ok=True)

    rung_reports: list[dict[str, Any]] = []
    for zone_count in zone_counts:
        result = run_ladder_rung(ladder_root=ladder_root, release_zone_count=zone_count)
        rung_reports.append(rung_result_to_dict(result))

    blocked_rungs = [rung for rung in rung_reports if rung["budget_status"] != "probe_ready"]
    first_blocked_rung = blocked_rungs[0] if blocked_rungs else None
    first_blocked_zone_count = first_blocked_rung["release_zone_count"] if first_blocked_rung else None
    first_blocked_metric = first_blocked_rung["first_bottleneck"] if first_blocked_rung else None

    measurement_command = (
        "PYENV_VERSION=system uv run python scripts/summarize_multi_zone_scaling_ladder.py "
        f"--materialize-root {ladder_root} --format json"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "ladder_status": "measured_scratch_root",
        "ladder_root": str(ladder_root),
        "zone_counts": list(zone_counts),
        "rung_count": len(rung_reports),
        "rungs": rung_reports,
        "blocked_rungs": blocked_rungs,
        "first_blocked_rung": first_blocked_rung,
        "first_blocked_zone_count": first_blocked_zone_count,
        "first_blocked_metric": first_blocked_metric,
        "first_budget_blocker": first_blocked_rung.get("first_budget_failure") if first_blocked_rung else None,
        "output_budget_thresholds": handoff.build_output_budget_acceptance_thresholds(),
        "measurement_command": measurement_command,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "summary": summarize_report(rung_reports, first_blocked_zone_count, first_blocked_metric),
    }
    return report


def summarize_report(rungs: list[dict[str, Any]], first_blocked_zone_count: int | None, first_blocked_metric: str | None) -> str:
    budget_statuses = [rung["budget_status"] for rung in rungs]
    return (
        "Reduced-output multi-zone ladder measured "
        f"{len(rungs)} rungs with budget statuses {budget_statuses}. "
        + (
            f"The first blocked rung is {first_blocked_zone_count} zones"
            + (f" at {first_blocked_metric}" if first_blocked_metric else "")
            + "."
            if first_blocked_zone_count is not None
            else "No rung exceeded the current budget thresholds."
        )
    )


def run_ladder_rung(*, ladder_root: Path, release_zone_count: int) -> LadderRungResult:
    rung_root = ladder_root / f"zones_{release_zone_count:02d}"
    pressure_root = ladder_root / "pressure" / f"zones_{release_zone_count:02d}"
    pressure_fixture = materialize_pressure_probe_root(
        pressure_root,
        release_zone_count=release_zone_count,
        reducer_worker_count=DEFAULT_REDUCER_WORKER_COUNT if release_zone_count > 1 else 1,
        reducer_chunk_count=min(DEFAULT_REDUCER_CHUNK_COUNT, release_zone_count),
        output_family_mix=LADDER_PRESSURE_OUTPUT_FAMILY_MIX,
    )
    pressure_report = reducer_pressure.build_report(pressure_root)
    pressure_bottlenecks = reducer_pressure.classify_bottlenecks(
        manifest_size_bytes=int(pressure_report.get("manifest_size_bytes") or 0),
        manifest_file_count=1,
        output_file_count=int(pressure_report.get("output_file_count") or 0),
        output_byte_count=int(pressure_report.get("output_byte_count") or 0),
        reducer_manifest_bytes=int(pressure_report.get("reducer_manifest_bytes") or 0),
        sidecar_file_count=int(pressure_report.get("sidecar_file_count") or 0),
        sidecar_byte_count=int(pressure_report.get("sidecar_byte_count") or 0),
        reducer_wall_seconds=float(pressure_report.get("reducer_wall_time_seconds") or 0.0),
        merge_order=str(pressure_report.get("merge_order") or ""),
        merge_order_independent=bool(pressure_report.get("merge_order_independent")),
    )
    fixture = materialize_ladder_fixture_root(
        rung_root,
        release_zone_count=release_zone_count,
        reducer_worker_count=DEFAULT_REDUCER_WORKER_COUNT if release_zone_count > 1 else 1,
        reducer_chunk_count=min(DEFAULT_REDUCER_CHUNK_COUNT, release_zone_count),
    )
    command_plan_path = fixture.command_plan_path

    timing = {"trajectory_read_seconds": 0.0, "input_read_seconds": 0.0, "reducer_merge_seconds": 0.0}
    read_started = time.perf_counter()
    _ = load_json(fixture.diagnostics_path)
    timing["input_read_seconds"] += time.perf_counter() - read_started

    original_read_trajectory = hazard.read_trajectory_sample_batch
    original_read_deposition = hazard.read_deposition_batch
    original_read_impact_csv_batches = hazard.read_impact_event_csv_batches
    original_read_impact_parquet_batches = hazard.read_impact_event_parquet_batches
    original_merge = hazard.HazardAccumulator.merge

    def timed_trajectory_reader(path: Path, warnings: list[str], *, phase_telemetry: Any | None = None, **_: Any) -> Any:
        started = time.perf_counter()
        try:
            return original_read_trajectory(path, warnings, phase_telemetry=phase_telemetry)
        finally:
            elapsed = time.perf_counter() - started
            timing["trajectory_read_seconds"] += elapsed
            timing["input_read_seconds"] += elapsed

    def timed_deposition_reader(
        path: Path | None,
        warnings: list[str],
        *,
        phase_telemetry: Any | None = None,
        **_: Any,
    ) -> Any:
        started = time.perf_counter()
        try:
            return original_read_deposition(path, warnings, phase_telemetry=phase_telemetry)
        finally:
            timing["input_read_seconds"] += time.perf_counter() - started

    def timed_impact_csv_reader(
        paths: list[Path],
        warnings: list[str],
        *,
        phase_telemetry: Any | None = None,
        **_: Any,
    ) -> Iterator[Any]:
        started = time.perf_counter()
        try:
            for batch in original_read_impact_csv_batches(paths, warnings, phase_telemetry=phase_telemetry):
                yield batch
        finally:
            timing["input_read_seconds"] += time.perf_counter() - started

    def timed_impact_parquet_reader(
        paths: list[Path],
        warnings: list[str],
        *,
        phase_telemetry: Any | None = None,
        **_: Any,
    ) -> Iterator[Any]:
        started = time.perf_counter()
        try:
            for batch in original_read_impact_parquet_batches(paths, warnings, phase_telemetry=phase_telemetry):
                yield batch
        finally:
            timing["input_read_seconds"] += time.perf_counter() - started

    def timed_merge(self: Any, other: Any) -> Any:
        started = time.perf_counter()
        try:
            return original_merge(self, other)
        finally:
            timing["reducer_merge_seconds"] += time.perf_counter() - started

    hazard_output_root = rung_root / "output" / "hazard"
    hazard_output_root.mkdir(parents=True, exist_ok=True)
    case_id = f"multi_zone_scaling_ladder_z{release_zone_count:02d}"
    args = [
        "--case",
        str(fixture.case_path),
        "--output-dir",
        str(hazard_output_root),
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--trajectory-workers",
        "1",
        "--reducer-workers",
        str(fixture.reducer_worker_count),
        "--diagnostics",
        str(fixture.diagnostics_path),
        "--ensemble-trajectories-dir",
        str(fixture.trajectory_dir),
        "--deposition",
        str(fixture.deposition_path),
        "--ensemble-impact-events-dir",
        str(fixture.impact_event_dir),
        "--grid-xmin",
        str(DEFAULT_GRID_XMIN),
        "--grid-ymin",
        str(DEFAULT_GRID_YMIN),
        "--grid-ncols",
        str(DEFAULT_GRID_NCOLS),
        "--grid-nrows",
        str(DEFAULT_GRID_NROWS),
        "--grid-cell-size",
        str(DEFAULT_GRID_CELLSIZE),
        "--no-plots",
    ]

    with throughput.patch_hazard_timing_functions(
        hazard,
        timed_trajectory_reader,
        timed_deposition_reader,
        timed_impact_csv_reader,
        timed_impact_parquet_reader,
        timed_merge,
    ):
        with open(os.devnull, "w", encoding="utf-8") as stdout_sink, open(
            os.devnull, "w", encoding="utf-8"
        ) as stderr_sink:
            with redirect_stdout(stdout_sink), redirect_stderr(stderr_sink):
                status = hazard.main_with_args(args)

    if status != 0:
        raise MultiZoneScalingLadderError(f"hazard builder exited with status {status} for {release_zone_count} zones")

    hazard_manifest_path = hazard_output_root / f"{case_id}_manifest.json"
    if not hazard_manifest_path.exists():
        raise MultiZoneScalingLadderError(f"missing hazard manifest: {hazard_manifest_path}")
    hazard_manifest = load_json(hazard_manifest_path)
    performance = hazard_manifest.get("performance") or {}
    outputs = hazard_manifest.get("outputs") or []
    if not isinstance(performance, dict) or not isinstance(outputs, list):
        raise MultiZoneScalingLadderError("hazard manifest missing performance or outputs sections")

    output_pressure = throughput.summarize_output_pressure(outputs)
    timing_breakdown = throughput.summarize_timing_breakdown(
        performance,
        timing,
        bounds_discovery_seconds=throughput.number_or_zero(performance.get("bounds_discovery_seconds")),
        report_render_seconds=throughput.number_or_zero(performance.get("plot_render_seconds")),
    )
    hazard_bottleneck = throughput.classify_bottleneck(output_pressure, timing_breakdown)
    projection = build_budget_projection(
        fixture=fixture,
        command_plan_path=pressure_fixture.command_plan_path,
        hazard_manifest_path=pressure_fixture.output_manifest_path,
        output_family_file_counts=dict(pressure_report.get("output_family_file_counts") or {}),
        output_family_bytes=dict(pressure_report.get("output_family_bytes") or {}),
        manifest_size_bytes=int(pressure_report.get("manifest_size_bytes") or 0),
        output_file_count=int(pressure_report.get("output_file_count") or 0),
        output_byte_count=int(pressure_report.get("output_byte_count") or 0),
        reducer_manifest_file_count=int(pressure_report.get("reducer_manifest_file_count") or 0),
        reducer_manifest_bytes=int(pressure_report.get("reducer_manifest_bytes") or 0),
        sidecar_file_count=int(pressure_report.get("sidecar_file_count") or 0),
        sidecar_byte_count=int(pressure_report.get("sidecar_byte_count") or 0),
    )
    thresholds = handoff.build_output_budget_acceptance_thresholds()
    budget_validation = handoff.validate_output_budget_acceptance(projection=projection, thresholds=thresholds)
    first_budget_failure = budget_validation["failures"][0] if budget_validation["failures"] else None

    return LadderRungResult(
        release_zone_count=release_zone_count,
        rung_root=rung_root,
        pressure_report=pressure_report,
        fixture={
            "profile_root": str(fixture.rung_root),
            "case_path": str(fixture.case_path),
            "trajectory_dir": str(fixture.trajectory_dir),
            "deposition_path": str(fixture.deposition_path),
            "impact_event_dir": str(fixture.impact_event_dir),
            "diagnostics_path": str(fixture.diagnostics_path),
            "fixture_manifest_path": str(fixture.fixture_manifest_path),
            "command_plan_path": str(fixture.command_plan_path),
            "release_zone_count": fixture.release_zone_count,
            "reducer_worker_count": fixture.reducer_worker_count,
            "reducer_chunk_count": fixture.reducer_chunk_count,
            "scenario_count": fixture.scenario_count,
            "fixture_fingerprint": fixture.fixture_fingerprint,
        },
        command_plan_path=command_plan_path,
        hazard_manifest_path=hazard_manifest_path,
        hazard_manifest=hazard_manifest,
        timing_breakdown=timing_breakdown,
        output_pressure=output_pressure,
        output_budget_validation=budget_validation,
        budget_projection=projection,
        budget_status=str(pressure_bottlenecks.get("probe_blocker", {}).get("label") or "unknown"),
        first_budget_failure=first_budget_failure,
        hazard_bottleneck=hazard_bottleneck,
        manifest_size_bytes=projection["manifest_size_bytes"],
        reducer_manifest_file_count=projection["reducer_manifest_file_count"],
        reducer_manifest_bytes=projection["reducer_manifest_bytes"],
        sidecar_file_count=projection["sidecar_file_count"],
        sidecar_byte_count=projection["sidecar_byte_count"],
    )


def materialize_ladder_fixture_root(
    rung_root: Path,
    *,
    release_zone_count: int,
    reducer_worker_count: int,
    reducer_chunk_count: int,
    trajectory_samples_per_zone: int = DEFAULT_TRAJECTORY_SAMPLES_PER_ZONE,
    impact_rows_per_zone: int = DEFAULT_IMPACT_ROWS_PER_ZONE,
) -> LadderFixture:
    if release_zone_count <= 0:
        raise MultiZoneScalingLadderError("release_zone_count must be greater than 0")
    if reducer_worker_count <= 0:
        raise MultiZoneScalingLadderError("reducer_worker_count must be greater than 0")
    if reducer_chunk_count <= 0:
        raise MultiZoneScalingLadderError("reducer_chunk_count must be greater than 0")
    if reducer_chunk_count > release_zone_count:
        raise MultiZoneScalingLadderError("reducer_chunk_count cannot exceed release_zone_count")

    rung_root = rung_root.resolve()
    if rung_root.exists():
        shutil.rmtree(rung_root)
    rung_root.mkdir(parents=True, exist_ok=True)

    input_root = rung_root / "input"
    trajectory_dir = input_root / "trajectories"
    impact_event_dir = input_root / "impact_events"
    for path in (input_root, trajectory_dir, impact_event_dir):
        path.mkdir(parents=True, exist_ok=True)

    release_zones = reducer_pressure.build_release_zones(release_zone_count)
    scenario_rows = reducer_pressure.build_scenario_rows(release_zones, reducer_chunk_count=reducer_chunk_count)

    deposition_rows: list[dict[str, Any]] = []
    impact_rows: list[dict[str, Any]] = []
    for index, zone in enumerate(release_zones):
        trajectory_rows = throughput.build_trajectory_rows(zone["source_zone_id"], index, trajectory_samples_per_zone)
        zone_deposition_rows = throughput.build_deposition_rows(zone["source_zone_id"], index)
        zone_impact_rows = throughput.build_impact_event_rows(zone["source_zone_id"], index, impact_rows_per_zone)
        deposition_rows.extend(zone_deposition_rows)
        impact_rows.extend(zone_impact_rows)
        throughput.write_csv(
            trajectory_dir / f"{zone['source_zone_id']}.csv",
            fieldnames=(
                "trajectory_id",
                "time_s",
                "x_m",
                "y_m",
                "z_m",
                "vx_mps",
                "vy_mps",
                "vz_mps",
                "speed_mps",
                "kinetic_j",
                "potential_j",
                "total_energy_j",
                "contact_state",
            ),
            rows=trajectory_rows,
        )
        throughput.write_csv(
            impact_event_dir / f"{zone['source_zone_id']}.csv",
            fieldnames=(
                "trajectory_id",
                "impact_index",
                "time_s",
                "x_m",
                "y_m",
                "z_m",
                "incoming_normal_speed_mps",
                "scarring_energy_loss_j",
            ),
            rows=zone_impact_rows,
        )

    deposition_path = input_root / "deposition.csv"
    impact_path = input_root / "impact_events.csv"
    throughput.write_csv(
        deposition_path,
        fieldnames=("trajectory_id", "x_m", "y_m", "z_m", "deposition_mass_kg"),
        rows=deposition_rows,
    )
    throughput.write_csv(
        impact_path,
        fieldnames=(
            "trajectory_id",
            "impact_index",
            "time_s",
            "x_m",
            "y_m",
            "z_m",
            "incoming_normal_speed_mps",
            "scarring_energy_loss_j",
        ),
        rows=impact_rows,
    )

    diagnostics_path = input_root / "diagnostics.json"
    throughput.write_json(
        diagnostics_path,
        {
            "schema_version": "multi_zone_scaling_ladder_diagnostics_v1",
            "note": "deterministic reduced-output scaling ladder fixture",
            "release_zone_count": release_zone_count,
            "reducer_chunk_count": reducer_chunk_count,
            "reducer_worker_count": reducer_worker_count,
        },
    )

    case_path = input_root / "multi_zone_scaling_ladder_case.yaml"
    case = throughput.build_case(
        profile_root=rung_root,
        release_zone_count=release_zone_count,
        trajectory_dir=trajectory_dir,
        deposition_path=deposition_path,
        impact_event_dir=impact_event_dir,
    )
    case["case_id"] = f"multi_zone_scaling_ladder_z{release_zone_count:02d}"
    case["title"] = f"Multi-Zone Scaling Ladder: {release_zone_count} Zones"
    case["hazard_output_volume"] = {
        "conditional_curve_export": "summary-only",
        "grid_csv_export": "none",
        "no_plots": True,
    }
    case["diagnostics"] = {
        "profile_root": str(rung_root),
        "release_zone_count": release_zone_count,
        "reducer_chunk_count": reducer_chunk_count,
        "reducer_worker_count": reducer_worker_count,
    }
    throughput.write_yaml(case_path, case)

    fixture_manifest_path = input_root / "multi_zone_scaling_ladder_fixture_manifest.json"
    fixture_manifest = {
        "schema_version": "multi_zone_scaling_ladder_fixture_manifest_v1",
        "profile_root": str(rung_root),
        "case_path": str(case_path),
        "trajectory_dir": str(trajectory_dir),
        "deposition_path": str(deposition_path),
        "impact_event_dir": str(impact_event_dir),
        "diagnostics_path": str(diagnostics_path),
        "release_zone_count": release_zone_count,
        "scenario_count": len(scenario_rows),
        "reducer_worker_count": reducer_worker_count,
        "reducer_chunk_count": reducer_chunk_count,
        "trajectory_samples_per_zone": trajectory_samples_per_zone,
        "impact_rows_per_zone": impact_rows_per_zone,
        "release_zone_ids": [zone["source_zone_id"] for zone in release_zones],
        "output_controls": {
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "no_plots": True,
        },
        "grid": {
            "xmin": DEFAULT_GRID_XMIN,
            "ymin": DEFAULT_GRID_YMIN,
            "ncols": DEFAULT_GRID_NCOLS,
            "nrows": DEFAULT_GRID_NROWS,
            "cell_size": DEFAULT_GRID_CELLSIZE,
        },
    }
    fixture_manifest["fixture_fingerprint"] = throughput.fixture_fingerprint(fixture_manifest)
    throughput.write_json(fixture_manifest_path, fixture_manifest)

    command_plan_path = rung_root / "command_plan.json"
    command_plan = build_command_plan(
        rung_root=rung_root,
        case_path=case_path,
        output_root=rung_root / "output" / "hazard",
        reducer_worker_count=reducer_worker_count,
    )
    throughput.write_json(command_plan_path, command_plan)

    return LadderFixture(
        ladder_root=rung_root.parent,
        rung_root=rung_root,
        case_path=case_path,
        trajectory_dir=trajectory_dir,
        deposition_path=deposition_path,
        impact_event_dir=impact_event_dir,
        diagnostics_path=diagnostics_path,
        fixture_manifest_path=fixture_manifest_path,
        command_plan_path=command_plan_path,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        scenario_count=len(scenario_rows),
        fixture_fingerprint=fixture_manifest["fixture_fingerprint"],
    )


def materialize_pressure_probe_root(
    pressure_root: Path,
    *,
    release_zone_count: int,
    reducer_worker_count: int,
    reducer_chunk_count: int,
    output_family_mix: tuple[str, ...],
) -> PressureFixture:
    if release_zone_count <= 0:
        raise MultiZoneScalingLadderError("release_zone_count must be greater than 0")
    if reducer_worker_count <= 0:
        raise MultiZoneScalingLadderError("reducer_worker_count must be greater than 0")
    if reducer_chunk_count <= 0:
        raise MultiZoneScalingLadderError("reducer_chunk_count must be greater than 0")
    if reducer_chunk_count > release_zone_count:
        raise MultiZoneScalingLadderError("reducer_chunk_count cannot exceed release_zone_count")

    pressure_root = pressure_root.resolve()
    if pressure_root.exists():
        shutil.rmtree(pressure_root)
    pressure_root.mkdir(parents=True, exist_ok=True)

    input_root = pressure_root / "input"
    output_root = pressure_root / "output"
    trajectory_root = output_root / "trajectories"
    deposition_root = output_root / "deposition"
    impact_root = output_root / "impact_events"
    trajectory_chunk_root = output_root / "trajectory_chunks"
    reducer_chunk_root = output_root / "chunks"
    for path in (input_root, output_root, trajectory_root, deposition_root, impact_root, trajectory_chunk_root, reducer_chunk_root):
        path.mkdir(parents=True, exist_ok=True)

    output_family_mix = reducer_pressure.normalize_output_family_mix(output_family_mix)
    release_zones = reducer_pressure.build_release_zones(release_zone_count)
    scenario_rows = reducer_pressure.build_scenario_rows(release_zones, reducer_chunk_count=reducer_chunk_count)
    trajectory_chunks = reducer_pressure.build_trajectory_chunks(release_zones)
    reducer_chunks = reducer_pressure.build_reducer_chunks(release_zones, reducer_chunk_count=reducer_chunk_count)
    trajectory_execution = reducer_pressure.build_trajectory_execution(trajectory_chunks)
    reducer_execution = reducer_pressure.build_reducer_execution(reducer_chunks, reducer_worker_count=reducer_worker_count)
    probe_manifest = reducer_pressure.build_probe_manifest(
        probe_root=pressure_root,
        release_zones=release_zones,
        scenario_rows=scenario_rows,
        trajectory_execution=trajectory_execution,
        reducer_execution=reducer_execution,
        output_family_mix=output_family_mix,
    )
    command_plan = reducer_pressure.build_command_plan(
        probe_root=pressure_root,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        output_family_mix=output_family_mix,
    )
    probe_manifest_path = input_root / "multi_zone_reducer_pressure_probe_manifest.json"
    command_plan_path = pressure_root / "command_plan.json"
    output_manifest_path = output_root / "validation_multi_zone_reducer_pressure_manifest.json"
    reducer_pressure.write_json(probe_manifest_path, probe_manifest)
    reducer_pressure.write_json(command_plan_path, command_plan)
    reducer_pressure.materialize_input_tables(input_root, release_zones, scenario_rows)
    output_entries = reducer_pressure.build_output_entries(
        trajectory_root=trajectory_root,
        deposition_root=deposition_root,
        impact_root=impact_root,
        trajectory_chunk_root=trajectory_chunk_root,
        reducer_chunk_root=reducer_chunk_root,
        release_zones=release_zones,
        trajectory_chunks=trajectory_chunks,
        reducer_chunks=reducer_chunks,
        output_family_mix=output_family_mix,
    )
    output_manifest = reducer_pressure.build_output_manifest(
        probe_root=pressure_root,
        release_zones=release_zones,
        scenario_rows=scenario_rows,
        trajectory_execution=trajectory_execution,
        reducer_execution=reducer_execution,
        outputs=output_entries,
        output_family_mix=output_family_mix,
        manifest_mode="compact",
    )
    reducer_pressure.write_json(output_manifest_path, output_manifest)
    return PressureFixture(
        pressure_root=pressure_root,
        probe_manifest_path=probe_manifest_path,
        command_plan_path=command_plan_path,
        output_manifest_path=output_manifest_path,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        scenario_count=len(scenario_rows),
        pressure_fingerprint=throughput.fixture_fingerprint(
            {
                "probe_manifest": probe_manifest,
                "command_plan": command_plan,
                "output_manifest": output_manifest,
            }
        ),
    )


def build_command_plan(*, rung_root: Path, case_path: Path, output_root: Path, reducer_worker_count: int) -> dict[str, Any]:
    command = [
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/build_hazard_layers.py",
        "--case",
        str(case_path),
        "--output-dir",
        str(output_root),
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--trajectory-workers",
        "1",
        "--reducer-workers",
        str(reducer_worker_count),
        "--diagnostics",
        str(rung_root / "input" / "diagnostics.json"),
        "--ensemble-trajectories-dir",
        str(rung_root / "input" / "trajectories"),
        "--deposition",
        str(rung_root / "input" / "deposition.csv"),
        "--ensemble-impact-events-dir",
        str(rung_root / "input" / "impact_events"),
        "--grid-xmin",
        str(DEFAULT_GRID_XMIN),
        "--grid-ymin",
        str(DEFAULT_GRID_YMIN),
        "--grid-ncols",
        str(DEFAULT_GRID_NCOLS),
        "--grid-nrows",
        str(DEFAULT_GRID_NROWS),
        "--grid-cell-size",
        str(DEFAULT_GRID_CELLSIZE),
        "--no-plots",
    ]
    return {
        "schema_version": "multi_zone_scaling_ladder_command_plan_v1",
        "rung_root": str(rung_root),
        "command": command,
    }


def summarize_output_family_roles(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    family_file_counts: dict[str, int] = {}
    family_bytes: dict[str, int] = {}
    primary_output_file_count = 0
    primary_output_byte_count = 0
    reducer_manifest_file_count = 0
    reducer_manifest_bytes = 0
    sidecar_file_count = 0
    sidecar_byte_count = 0

    for output in outputs:
        kind = str(output.get("kind") or "unknown")
        file_count = int(output.get("file_count") or 0)
        total_bytes = int(output.get("total_bytes") or 0)
        family_file_counts[kind] = family_file_counts.get(kind, 0) + file_count
        family_bytes[kind] = family_bytes.get(kind, 0) + total_bytes

        if kind in reducer_pressure.PRIMARY_OUTPUT_FAMILIES:
            primary_output_file_count += file_count
            primary_output_byte_count += total_bytes
        elif kind == reducer_pressure.REDUCER_MANIFEST_FAMILY:
            reducer_manifest_file_count += file_count
            reducer_manifest_bytes += total_bytes
            sidecar_file_count += file_count
            sidecar_byte_count += total_bytes
        elif kind in reducer_pressure.SIDECAR_OUTPUT_FAMILIES:
            sidecar_file_count += file_count
            sidecar_byte_count += total_bytes

    output_file_count = sum(family_file_counts.values())
    output_byte_count = sum(family_bytes.values())
    return {
        "output_family_file_counts": family_file_counts,
        "output_family_bytes": family_bytes,
        "primary_output_file_count": primary_output_file_count,
        "primary_output_byte_count": primary_output_byte_count,
        "reducer_manifest_file_count": reducer_manifest_file_count,
        "reducer_manifest_bytes": reducer_manifest_bytes,
        "sidecar_file_count": sidecar_file_count,
        "sidecar_byte_count": sidecar_byte_count,
        "output_file_count": output_file_count,
        "output_byte_count": output_byte_count,
    }


def build_budget_projection(
    *,
    fixture: LadderFixture,
    command_plan_path: Path,
    hazard_manifest_path: Path,
    output_family_file_counts: dict[str, int],
    output_family_bytes: dict[str, int],
    manifest_size_bytes: int,
    output_file_count: int,
    output_byte_count: int,
    reducer_manifest_file_count: int,
    reducer_manifest_bytes: int,
    sidecar_file_count: int,
    sidecar_byte_count: int,
) -> dict[str, Any]:
    retained_families = [
        family
        for family in reducer_pressure.REPLAY_CRITICAL_OUTPUT_FAMILIES
        if output_family_file_counts.get(family, 0) > 0
    ]
    return {
        "release_zone_count": fixture.release_zone_count,
        "reducer_chunk_count": fixture.reducer_chunk_count,
        "reducer_worker_count": fixture.reducer_worker_count,
        "manifest_size_bytes": manifest_size_bytes,
        "output_file_count": output_file_count,
        "output_byte_count": output_byte_count,
        "reducer_manifest_file_count": reducer_manifest_file_count,
        "reducer_manifest_bytes": reducer_manifest_bytes,
        "sidecar_file_count": sidecar_file_count,
        "sidecar_byte_count": sidecar_byte_count,
        "output_family_file_counts": output_family_file_counts,
        "output_family_bytes": output_family_bytes,
        "replay_critical_retained_output_families": retained_families,
        "projection_file_hashes": {
            "probe_manifest_sha256": sha256_file(fixture.fixture_manifest_path),
            "command_plan_sha256": sha256_file(command_plan_path),
            "output_manifest_sha256": sha256_file(hazard_manifest_path),
        },
    }


def rung_result_to_dict(result: LadderRungResult) -> dict[str, Any]:
    return {
        "release_zone_count": result.release_zone_count,
        "rung_root": str(result.rung_root),
        "pressure_report": result.pressure_report,
        "fixture": result.fixture,
        "command_plan_path": str(result.command_plan_path),
        "hazard_manifest_path": str(result.hazard_manifest_path),
        "manifest_size_bytes": result.manifest_size_bytes,
        "reducer_manifest_file_count": result.reducer_manifest_file_count,
        "reducer_manifest_bytes": result.reducer_manifest_bytes,
        "sidecar_file_count": result.sidecar_file_count,
        "sidecar_byte_count": result.sidecar_byte_count,
        "output_pressure": result.output_pressure,
        "timings": result.timing_breakdown,
        "hazard_bottleneck": result.hazard_bottleneck,
        "budget_projection": result.budget_projection,
        "output_budget_validation": result.output_budget_validation,
        "budget_status": result.budget_status,
        "first_budget_failure": result.first_budget_failure,
        "hazard_manifest": {
            "schema_version": result.hazard_manifest.get("schema_version"),
            "case_id": result.hazard_manifest.get("case_id"),
            "completion_status": result.hazard_manifest.get("completion_status"),
            "execution_status": result.hazard_manifest.get("execution_status"),
            "performance": result.hazard_manifest.get("performance"),
            "outputs": result.hazard_manifest.get("outputs"),
            "conditional_execution": result.hazard_manifest.get("conditional_execution"),
        },
        "phase_seconds": result.timing_breakdown.get("phase_seconds", {}),
        "output_file_count": result.budget_projection["output_file_count"],
        "output_byte_count": result.budget_projection["output_byte_count"],
        "reducer_chunk_count": result.budget_projection["reducer_chunk_count"],
        "reducer_worker_count": result.budget_projection["reducer_worker_count"],
        "first_bottleneck": first_bottleneck(result),
        "budget_threshold_profile_id": result.output_budget_validation.get("threshold_profile_id"),
    }


def first_bottleneck(result: LadderRungResult) -> str:
    return first_pressure_bottleneck_metric(result.pressure_report) or str(result.hazard_bottleneck.get("label") or "unknown")


def first_pressure_bottleneck_metric(pressure_report: dict[str, Any]) -> str | None:
    bottlenecks = reducer_pressure.classify_bottlenecks(
        manifest_size_bytes=int(pressure_report.get("manifest_size_bytes") or 0),
        manifest_file_count=1,
        output_file_count=int(pressure_report.get("output_file_count") or 0),
        output_byte_count=int(pressure_report.get("output_byte_count") or 0),
        reducer_manifest_bytes=int(pressure_report.get("reducer_manifest_bytes") or 0),
        sidecar_file_count=int(pressure_report.get("sidecar_file_count") or 0),
        sidecar_byte_count=int(pressure_report.get("sidecar_byte_count") or 0),
        reducer_wall_seconds=float(pressure_report.get("reducer_wall_time_seconds") or 0.0),
        merge_order=str(pressure_report.get("merge_order") or ""),
        merge_order_independent=bool(pressure_report.get("merge_order_independent")),
    ).get("bottleneck_labels") or {}
    for metric in ("manifest_size", "output_pressure", "reducer_runtime"):
        label = bottlenecks.get(metric, {}).get("label")
        if label not in {None, "manifest_bounded", "output_pressure_bounded", "reducer_runtime_bounded", "probe_ready"}:
            return metric
    probe_blocker = bottlenecks.get("probe_blocker", {}).get("label")
    if probe_blocker and probe_blocker != "probe_ready":
        return "probe_blocker"
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context.
        raise MultiZoneScalingLadderError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MultiZoneScalingLadderError(f"JSON document must be an object: {path}")
    return payload


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"ladder_status: {report['ladder_status']}",
        f"ladder_root: {report['ladder_root']}",
        f"zone_counts: {','.join(str(value) for value in report['zone_counts'])}",
        f"first_blocked_zone_count: {report['first_blocked_zone_count']}",
        f"first_blocked_metric: {report['first_blocked_metric']}",
        "rungs:",
    ]
    for rung in report["rungs"]:
        lines.append(
            f"- {rung['release_zone_count']}: budget={rung['budget_status']}, first_bottleneck={rung['first_bottleneck']}, "
            f"manifest={rung['manifest_size_bytes']} bytes, sidecars={rung['sidecar_file_count']}, "
            f"output_files={rung['output_file_count']}, total_wall={rung['timings']['total_wall_seconds']}"
        )
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Multi-Zone Scaling Ladder",
        "",
        f"- ladder_status: `{report['ladder_status']}`",
        f"- ladder_root: `{report['ladder_root']}`",
        f"- zone_counts: `{','.join(str(value) for value in report['zone_counts'])}`",
        f"- first_blocked_zone_count: `{report['first_blocked_zone_count']}`",
        f"- first_blocked_metric: `{report['first_blocked_metric']}`",
        "",
        "## Rungs",
    ]
    for rung in report["rungs"]:
        lines.extend(
            [
                f"- `{rung['release_zone_count']}` zones: budget `{rung['budget_status']}`, first bottleneck `{rung['first_bottleneck']}`",
                f"  - manifest bytes: `{rung['manifest_size_bytes']}`",
                f"  - reducer sidecars: `{rung['sidecar_file_count']}` files / `{rung['sidecar_byte_count']}` bytes",
                f"  - output files: `{rung['output_file_count']}` / `{rung['output_byte_count']}` bytes",
                f"  - total wall seconds: `{rung['timings']['total_wall_seconds']}`",
            ]
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
