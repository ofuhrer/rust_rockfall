#!/usr/bin/env python3
"""Benchmark harness for hazard-accumulation optimization hypotheses.

The harness is fixture-backed and local. It materializes three representative
hazard profiles, runs the existing hazard-layer builder with explicit-grid
controls, and records baseline evidence that future optimization tasks must
beat before they can be accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
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
import scripts.summarize_multi_zone_hazard_throughput_profile as throughput
import scripts.summarize_multi_zone_reducer_pressure as reducer_pressure

SCHEMA_VERSION = "hazard_accumulation_hypothesis_benchmark_v1"
ACCEPTANCE_SCHEMA_VERSION = "hazard_accumulation_hypothesis_acceptance_v1"
DEFAULT_BENCHMARK_ROOT = Path("/tmp/rust_rockfall/hazard_accumulation_hypothesis_benchmark_v1")
DEFAULT_PROFILE_XMIN = throughput.DEFAULT_GRID_XMIN
DEFAULT_PROFILE_YMIN = throughput.DEFAULT_GRID_YMIN
DEFAULT_PROFILE_NCOLS = throughput.DEFAULT_GRID_NCOLS
DEFAULT_PROFILE_NROWS = throughput.DEFAULT_GRID_NROWS
DEFAULT_PROFILE_CELLSIZE = throughput.DEFAULT_GRID_CELLSIZE
BASELINE_SPEEDUP_FLOOR = 0.90
MEMORY_GROWTH_CEILING = 0.10


class HazardAccumulationBenchmarkError(ValueError):
    """User-facing benchmark error."""


@dataclass(frozen=True)
class BenchmarkProfileSpec:
    profile_id: str
    role: str
    release_zone_count: int
    reducer_workers: int
    reducer_chunk_count: int
    trajectory_samples_per_zone: int
    impact_rows_per_zone: int
    conditional_curve_export: str
    grid_csv_export: str
    export_geotiff: bool
    no_plots: bool
    repeat_for_determinism: bool = False


@dataclass(frozen=True)
class BenchmarkFixture:
    profile_root: Path
    case_path: Path
    trajectory_dir: Path
    deposition_path: Path
    impact_event_dir: Path
    diagnostics_path: Path
    fixture_manifest_path: Path
    release_zone_count: int
    trajectory_file_count: int
    impact_file_count: int
    deposition_row_count: int
    impact_row_count: int
    fixture_fingerprint: str


@dataclass(frozen=True)
class BenchmarkRun:
    profile_id: str
    role: str
    run_label: str
    output_dir: Path
    hazard_manifest_path: Path
    hazard_manifest: dict[str, Any]
    stable_manifest_view: dict[str, Any]
    stable_manifest_sha256: str
    performance: dict[str, Any]
    output_pressure: dict[str, Any]
    timing_breakdown: dict[str, Any]
    timing: dict[str, float]


PROFILE_SPECS: dict[str, BenchmarkProfileSpec] = {
    "single_zone_control": BenchmarkProfileSpec(
        profile_id="single_zone_control",
        role="no_op_control",
        release_zone_count=1,
        reducer_workers=1,
        reducer_chunk_count=1,
        trajectory_samples_per_zone=4,
        impact_rows_per_zone=0,
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        export_geotiff=False,
        no_plots=True,
    ),
    "smallest_multi_zone_baseline": BenchmarkProfileSpec(
        profile_id="smallest_multi_zone_baseline",
        role="performance_baseline",
        release_zone_count=2,
        reducer_workers=2,
        reducer_chunk_count=2,
        trajectory_samples_per_zone=5,
        impact_rows_per_zone=1,
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        export_geotiff=False,
        no_plots=True,
        repeat_for_determinism=True,
    ),
    "output_heavy_guardrail": BenchmarkProfileSpec(
        profile_id="output_heavy_guardrail",
        role="output_guardrail",
        release_zone_count=12,
        reducer_workers=2,
        reducer_chunk_count=4,
        trajectory_samples_per_zone=8,
        impact_rows_per_zone=3,
        conditional_curve_export="full",
        grid_csv_export="full",
        export_geotiff=True,
        no_plots=True,
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=DEFAULT_BENCHMARK_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(args.benchmark_root)
    except HazardAccumulationBenchmarkError as exc:
        print(f"hazard accumulation benchmark error: {exc}", file=sys.stderr)
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
    return 0 if report["benchmark_status"] == "baseline_recorded" else 2


def build_report(benchmark_root: Path) -> dict[str, Any]:
    benchmark_root = benchmark_root.resolve()
    if benchmark_root.exists():
        shutil.rmtree(benchmark_root)
    benchmark_root.mkdir(parents=True, exist_ok=True)

    profile_results: dict[str, BenchmarkRun] = {}
    fixture_reports: dict[str, dict[str, Any]] = {}
    for profile_id, profile_spec in PROFILE_SPECS.items():
        fixture = materialize_fixture_root(benchmark_root / profile_id, profile_spec=profile_spec)
        fixture_reports[profile_id] = {
            "schema_version": "hazard_accumulation_fixture_v1",
            "profile_id": profile_id,
            "role": profile_spec.role,
            "profile_root": str(fixture.profile_root),
            "case_path": str(fixture.case_path),
            "trajectory_dir": str(fixture.trajectory_dir),
            "deposition_path": str(fixture.deposition_path),
            "impact_event_dir": str(fixture.impact_event_dir),
            "diagnostics_path": str(fixture.diagnostics_path),
            "release_zone_count": fixture.release_zone_count,
            "trajectory_file_count": fixture.trajectory_file_count,
            "impact_file_count": fixture.impact_file_count,
            "deposition_row_count": fixture.deposition_row_count,
            "impact_row_count": fixture.impact_row_count,
            "fixture_fingerprint": fixture.fixture_fingerprint,
        }
        first_run = run_profiled_hazard_build(
            benchmark_root=benchmark_root,
            profile_spec=profile_spec,
            fixture=fixture,
            run_label="baseline",
        )
        profile_results[profile_id] = first_run
        if profile_spec.repeat_for_determinism:
            replay = run_profiled_hazard_build(
                benchmark_root=benchmark_root,
                profile_spec=profile_spec,
                fixture=fixture,
                run_label="replay",
            )
            profile_results[f"{profile_id}_replay"] = replay

    baseline = profile_results["smallest_multi_zone_baseline"]
    baseline_replay = profile_results["smallest_multi_zone_baseline_replay"]
    no_op_control = profile_results["single_zone_control"]
    output_heavy = profile_results["output_heavy_guardrail"]

    acceptance_criteria = {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "baseline_profile_id": baseline.profile_id,
        "baseline_run_label": baseline.run_label,
        "speedup_floor_fraction": BASELINE_SPEEDUP_FLOOR,
        "memory_growth_ceiling_fraction": MEMORY_GROWTH_CEILING,
        "speedup_requirement": (
            "future candidate accumulation_seconds must be at least 10% faster than the smallest multi-zone baseline"
        ),
        "memory_requirement": (
            "future candidate peak_rss_kb must stay within 10% of the baseline when both runs report RSS"
        ),
        "output_parity_requirement": {
            "stable_manifest_view_match_required": True,
            "hazard_layer_sha256_match_required": True,
            "hazard_manifest_schema_match_required": True,
        },
        "determinism_requirement": {
            "baseline_replay_required": True,
            "stable_manifest_view_match_required": True,
            "layer_signature_match_required": True,
        },
        "claim_boundaries": {
            "annual_frequency_claims_allowed": False,
            "distributed_execution_authorized": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
        },
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_status": "baseline_recorded",
        "benchmark_root": str(benchmark_root),
        "profile_root_count": len(PROFILE_SPECS),
        "profiles": {
            profile_id: profile_result_to_dict(result)
            for profile_id, result in sorted(profile_results.items())
        },
        "fixtures": fixture_reports,
        "baseline_profile_id": baseline.profile_id,
        "baseline_result": profile_result_to_dict(baseline),
        "baseline_replay_result": profile_result_to_dict(baseline_replay),
        "no_op_control_result": profile_result_to_dict(no_op_control),
        "output_heavy_result": profile_result_to_dict(output_heavy),
        "acceptance_criteria": acceptance_criteria,
        "comparison_contract": {
            "before_required": True,
            "after_required": True,
            "before_profile_id": baseline.profile_id,
            "after_profile_id": baseline.profile_id,
            "before_run_label": baseline.run_label,
            "after_run_label": "candidate",
            "required_evidence": [
                "baseline result",
                "candidate result",
                "stable manifest hash comparison",
                "hazard layer output signature comparison",
                "memory comparison when RSS is available",
            ],
        },
        "determinism": {
            "baseline_replay_match": runs_match(baseline, baseline_replay),
            "stable_manifest_sha256": baseline.stable_manifest_sha256,
            "replay_stable_manifest_sha256": baseline_replay.stable_manifest_sha256,
            "layer_signature_match": hazard_layer_signatures(baseline.hazard_manifest)
            == hazard_layer_signatures(baseline_replay.hazard_manifest),
        },
        "claim_boundary_note": (
            "Benchmark evidence only; no hazard-value change, no operational claim, no annual-frequency claim, "
            "no physical-probability claim, no risk/exposure/vulnerability claim, and no scale-up authorization."
        ),
        "analysis_notes": [
            "single_zone_control is the no-op baseline and should remain cheap.",
            "smallest_multi_zone_baseline is the comparison baseline future optimization work must beat.",
            "output_heavy_guardrail preserves output parity and claim boundaries while exercising the largest writer fan-out.",
        ],
    }
    return report


def materialize_fixture_root(
    profile_root: Path,
    *,
    profile_spec: BenchmarkProfileSpec,
) -> BenchmarkFixture:
    release_zone_count = profile_spec.release_zone_count
    reducer_workers = profile_spec.reducer_workers
    reducer_chunk_count = profile_spec.reducer_chunk_count
    trajectory_rows_per_zone = profile_spec.trajectory_samples_per_zone
    impact_rows_per_zone = profile_spec.impact_rows_per_zone
    if release_zone_count <= 0:
        raise HazardAccumulationBenchmarkError("release_zone_count must be greater than 0")
    if reducer_workers <= 0:
        raise HazardAccumulationBenchmarkError("reducer_workers must be greater than 0")
    if reducer_chunk_count <= 0:
        raise HazardAccumulationBenchmarkError("reducer_chunk_count must be greater than 0")
    if reducer_chunk_count > release_zone_count:
        raise HazardAccumulationBenchmarkError("reducer_chunk_count cannot exceed release_zone_count")

    profile_root = profile_root.resolve()
    if profile_root.exists():
        shutil.rmtree(profile_root)
    profile_root.mkdir(parents=True, exist_ok=True)

    input_root = profile_root / "input"
    trajectory_dir = input_root / "trajectories"
    impact_event_dir = input_root / "impact_events"
    for path in (input_root, trajectory_dir, impact_event_dir):
        path.mkdir(parents=True, exist_ok=True)

    release_zones = reducer_pressure.build_release_zones(release_zone_count)
    scenario_rows = reducer_pressure.build_scenario_rows(release_zones, reducer_chunk_count=reducer_chunk_count)

    deposition_rows: list[dict[str, Any]] = []
    impact_rows: list[dict[str, Any]] = []
    for index, zone in enumerate(release_zones):
        trajectory_path = trajectory_dir / f"{zone['source_zone_id']}.csv"
        impact_path = impact_event_dir / f"{zone['source_zone_id']}.csv"
        trajectory_rows = throughput.build_trajectory_rows(zone["source_zone_id"], index, trajectory_rows_per_zone)
        zone_deposition_rows = throughput.build_deposition_rows(zone["source_zone_id"], index)
        zone_impact_rows = throughput.build_impact_event_rows(zone["source_zone_id"], index, impact_rows_per_zone)
        deposition_rows.extend(zone_deposition_rows)
        impact_rows.extend(zone_impact_rows)
        throughput.write_csv(
            trajectory_path,
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
            "schema_version": "hazard_accumulation_benchmark_diagnostics_v1",
            "note": "deterministic fixture for hazard-accumulation benchmark evidence",
            "profile_id": profile_spec.profile_id,
            "release_zone_count": release_zone_count,
        },
    )

    case_path = input_root / f"{profile_spec.profile_id}_case.yaml"
    case = throughput.build_case(
        profile_root=profile_root,
        release_zone_count=release_zone_count,
        trajectory_dir=trajectory_dir,
        deposition_path=deposition_path,
        impact_event_dir=impact_event_dir,
    )
    case["case_id"] = f"{profile_spec.profile_id}_hazard_accumulation_benchmark"
    case["title"] = f"Hazard Accumulation Benchmark: {profile_spec.profile_id}"
    case["description"] = (
        "Deterministic scratch fixture used to benchmark hazard accumulation without changing hazard semantics."
    )
    case["hazard_output_volume"] = {
        "conditional_curve_export": profile_spec.conditional_curve_export,
        "grid_csv_export": profile_spec.grid_csv_export,
        "export_geotiff": profile_spec.export_geotiff,
        "no_plots": profile_spec.no_plots,
    }
    case["diagnostics"] = {"profile_root": str(profile_root), "profile_id": profile_spec.profile_id}
    throughput.write_yaml(case_path, case)

    fixture_manifest_path = input_root / f"{profile_spec.profile_id}_fixture_manifest.json"
    fixture_manifest = {
        "schema_version": "hazard_accumulation_fixture_manifest_v1",
        "profile_id": profile_spec.profile_id,
        "role": profile_spec.role,
        "profile_root": str(profile_root),
        "case_path": str(case_path),
        "trajectory_dir": str(trajectory_dir),
        "deposition_path": str(deposition_path),
        "impact_event_dir": str(impact_event_dir),
        "diagnostics_path": str(diagnostics_path),
        "release_zone_count": release_zone_count,
        "trajectory_file_count": release_zone_count,
        "impact_file_count": release_zone_count,
        "deposition_row_count": len(deposition_rows),
        "impact_row_count": len(impact_rows),
        "release_zone_ids": [zone["source_zone_id"] for zone in release_zones],
        "scenario_count": len(scenario_rows),
        "trajectory_rows_per_zone": trajectory_rows_per_zone,
        "impact_rows_per_zone": impact_rows_per_zone,
        "conditional_curve_export": profile_spec.conditional_curve_export,
        "grid_csv_export": profile_spec.grid_csv_export,
        "export_geotiff": profile_spec.export_geotiff,
        "no_plots": profile_spec.no_plots,
        "grid": {
            "xmin": DEFAULT_PROFILE_XMIN,
            "ymin": DEFAULT_PROFILE_YMIN,
            "ncols": DEFAULT_PROFILE_NCOLS,
            "nrows": DEFAULT_PROFILE_NROWS,
            "cell_size": DEFAULT_PROFILE_CELLSIZE,
        },
    }
    fixture_manifest["fixture_fingerprint"] = throughput.fixture_fingerprint(fixture_manifest)
    throughput.write_json(fixture_manifest_path, fixture_manifest)

    return BenchmarkFixture(
        profile_root=profile_root,
        case_path=case_path,
        trajectory_dir=trajectory_dir,
        deposition_path=deposition_path,
        impact_event_dir=impact_event_dir,
        diagnostics_path=diagnostics_path,
        fixture_manifest_path=fixture_manifest_path,
        release_zone_count=release_zone_count,
        trajectory_file_count=release_zone_count,
        impact_file_count=release_zone_count,
        deposition_row_count=len(deposition_rows),
        impact_row_count=len(impact_rows),
        fixture_fingerprint=fixture_manifest["fixture_fingerprint"],
    )


def run_profiled_hazard_build(
    *,
    benchmark_root: Path,
    profile_spec: BenchmarkProfileSpec,
    fixture: BenchmarkFixture,
    run_label: str,
) -> BenchmarkRun:
    profile_output_root = benchmark_root / profile_spec.profile_id / "output" / run_label
    if profile_output_root.exists():
        shutil.rmtree(profile_output_root)
    profile_output_root.mkdir(parents=True, exist_ok=True)

    timing = {"trajectory_read_seconds": 0.0, "input_read_seconds": 0.0, "reducer_merge_seconds": 0.0}
    read_started = time.perf_counter()
    _ = throughput.load_json(fixture.diagnostics_path)
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

    args = [
        "--case",
        str(fixture.case_path),
        "--output-dir",
        str(profile_output_root / "hazard"),
        "--grid-xmin",
        str(DEFAULT_PROFILE_XMIN),
        "--grid-ymin",
        str(DEFAULT_PROFILE_YMIN),
        "--grid-ncols",
        str(DEFAULT_PROFILE_NCOLS),
        "--grid-nrows",
        str(DEFAULT_PROFILE_NROWS),
        "--grid-cell-size",
        str(DEFAULT_PROFILE_CELLSIZE),
        "--conditional-curve-export",
        profile_spec.conditional_curve_export,
        "--grid-csv-export",
        profile_spec.grid_csv_export,
        "--trajectory-workers",
        "1",
        "--reducer-workers",
        str(profile_spec.reducer_workers),
        "--diagnostics",
        str(fixture.diagnostics_path),
        "--ensemble-trajectories-dir",
        str(fixture.trajectory_dir),
        "--deposition",
        str(fixture.deposition_path),
        "--ensemble-impact-events-dir",
        str(fixture.impact_event_dir),
    ]
    if profile_spec.export_geotiff:
        args.append("--export-geotiff")
    if profile_spec.no_plots:
        args.append("--no-plots")

    with throughput.patch_hazard_timing_functions(
        hazard,
        timed_trajectory_reader,
        timed_deposition_reader,
        timed_impact_csv_reader,
        timed_impact_parquet_reader,
        timed_merge,
    ):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = hazard.main_with_args(args)

    if status != 0:
        raise HazardAccumulationBenchmarkError(
            f"hazard builder exited with status {status} for profile {profile_spec.profile_id} ({run_label})"
        )

    case = throughput.load_yaml(fixture.case_path)
    case_id = str(case.get("case_id") or profile_spec.profile_id)
    hazard_manifest_path = profile_output_root / "hazard" / f"{case_id}_manifest.json"
    if not hazard_manifest_path.exists():
        raise HazardAccumulationBenchmarkError(f"missing hazard manifest: {hazard_manifest_path}")
    hazard_manifest = throughput.load_json(hazard_manifest_path)
    performance = hazard_manifest.get("performance") or {}
    outputs = hazard_manifest.get("outputs") or []
    if not isinstance(performance, dict) or not isinstance(outputs, list):
        raise HazardAccumulationBenchmarkError("hazard manifest missing performance or outputs sections")

    output_pressure = throughput.summarize_output_pressure(outputs)
    timing_breakdown = throughput.summarize_timing_breakdown(
        performance,
        timing,
        bounds_discovery_seconds=0.0,
        report_render_seconds=throughput.number_or_zero(performance.get("plot_render_seconds")),
    )
    stable_view = stable_manifest_view(hazard_manifest)
    stable_sha = sha256_text(json.dumps(stable_view, sort_keys=True, separators=(",", ":")))

    return BenchmarkRun(
        profile_id=profile_spec.profile_id,
        role=profile_spec.role,
        run_label=run_label,
        output_dir=profile_output_root / "hazard",
        hazard_manifest_path=hazard_manifest_path,
        hazard_manifest=hazard_manifest,
        stable_manifest_view=stable_view,
        stable_manifest_sha256=stable_sha,
        performance=performance,
        output_pressure=output_pressure,
        timing_breakdown=timing_breakdown,
        timing=timing,
    )


def stable_manifest_view(manifest: dict[str, Any]) -> dict[str, Any]:
    conditional_execution = manifest.get("conditional_execution") or {}
    reducer = conditional_execution.get("reducer") or {}
    outputs = []
    for output in manifest.get("outputs") or []:
        if not isinstance(output, dict):
            continue
        if output.get("kind") != "hazard_layer":
            continue
        outputs.append(
            {
                "kind": output.get("kind"),
                "format": output.get("format"),
                "layer_name": output.get("layer_name"),
                "sha256": output.get("sha256"),
                "file_count": output.get("file_count"),
                "total_bytes": output.get("total_bytes"),
            }
        )
    outputs.sort(key=lambda item: (str(item["kind"]), str(item["format"]), str(item["layer_name"]), str(item["sha256"])))
    cellwise_layers = []
    for layer in manifest.get("cellwise_layers") or []:
        if not isinstance(layer, dict):
            continue
        cellwise_layers.append(
            {
                "key": layer.get("key"),
                "layer_name": layer.get("layer_name"),
                "thresholds": layer.get("thresholds"),
                "format": layer.get("format"),
                "units": layer.get("units"),
            }
        )
    cellwise_layers.sort(key=lambda item: (str(item["key"]), str(item["layer_name"])))
    return {
        "schema_version": manifest.get("schema_version"),
        "case_id": manifest.get("case_id"),
        "grid": manifest.get("grid"),
        "hazard_statistics": manifest.get("hazard_statistics"),
        "layer_semantics": manifest.get("layer_semantics"),
        "cellwise_layers": cellwise_layers,
        "conditional_execution": {
            "schema_version": conditional_execution.get("schema_version"),
            "grid_cell_count": conditional_execution.get("grid_cell_count"),
            "conditional_curve_export": conditional_execution.get("conditional_curve_export"),
            "reducer": {
                "mode": reducer.get("mode"),
                "worker_count": reducer.get("worker_count"),
                "chunk_count": reducer.get("chunk_count"),
                "chunk_manifest_count": reducer.get("chunk_manifest_count"),
                "merge_order": reducer.get("merge_order"),
                "merge_order_independent": reducer.get("merge_order_independent"),
                "chunk_ids": reducer.get("chunk_ids"),
            },
        },
        "outputs": outputs,
        "warnings": manifest.get("warnings") or [],
    }


def profile_result_to_dict(result: BenchmarkRun) -> dict[str, Any]:
    return {
        "profile_id": result.profile_id,
        "role": result.role,
        "run_label": result.run_label,
        "hazard_manifest_path": str(result.hazard_manifest_path),
        "stable_manifest_sha256": result.stable_manifest_sha256,
        "stable_manifest_view": result.stable_manifest_view,
        "hazard_manifest": {
            "schema_version": result.hazard_manifest.get("schema_version"),
            "case_id": result.hazard_manifest.get("case_id"),
            "completion_status": result.hazard_manifest.get("completion_status"),
            "execution_status": result.hazard_manifest.get("execution_status"),
            "conditional_execution": result.hazard_manifest.get("conditional_execution"),
            "performance": {
                "trajectory_read_seconds": round(result.timing["trajectory_read_seconds"], 6),
                "input_read_seconds": round(result.timing["input_read_seconds"], 6),
                "accumulation_seconds": throughput.number_or_zero(result.performance.get("accumulation_seconds")),
                "reducer_merge_seconds": round(result.timing["reducer_merge_seconds"], 6),
                "manifest_seconds": round(
                    throughput.number_or_zero(result.performance.get("manifest_write_seconds"))
                    + throughput.number_or_zero(result.performance.get("json_serialization_seconds")),
                    6,
                ),
                "raster_write_seconds": round(
                    sum(
                        throughput.number_or_zero(value)
                        for key, value in (result.performance.get("output_write_kind_seconds") or {}).items()
                        if key in {"csv_grid", "esri_ascii_grid", "geotiff"}
                    ),
                    6,
                ),
                "report_render_seconds": round(throughput.number_or_zero(result.performance.get("plot_render_seconds")), 6),
                "bounds_discovery_seconds": 0.0,
                "cog_export_seconds": None,
            },
        },
        "performance": result.performance,
        "output_pressure": result.output_pressure,
        "timings": result.timing_breakdown,
        "profile_scale": {
            "output_file_count": throughput.number_or_zero(result.performance.get("output_file_count")),
            "output_bytes": throughput.number_or_zero(result.performance.get("output_bytes")),
            "hazard_layer_seconds": throughput.number_or_zero(result.performance.get("hazard_layer_seconds")),
            "total_wall_seconds": throughput.number_or_zero(result.performance.get("total_wall_seconds")),
            "peak_rss_kb": result.performance.get("peak_rss_kb"),
        },
    }


def runs_match(left: BenchmarkRun, right: BenchmarkRun) -> bool:
    return (
        left.stable_manifest_sha256 == right.stable_manifest_sha256
        and hazard_layer_signatures(left.hazard_manifest) == hazard_layer_signatures(right.hazard_manifest)
    )


def hazard_layer_signatures(manifest: dict[str, Any]) -> list[tuple[Any, Any, Any, Any]]:
    return sorted(
        (
            output.get("kind"),
            output.get("format"),
            output.get("layer_name"),
            output.get("sha256"),
        )
        for output in manifest.get("outputs") or []
        if isinstance(output, dict) and output.get("kind") == "hazard_layer"
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_text(report: dict[str, Any]) -> str:
    acceptance = report["acceptance_criteria"]
    baseline = report["baseline_result"]
    replay = report["baseline_replay_result"]
    lines = [
        f"benchmark_status: {report['benchmark_status']}",
        f"schema_version: {report['schema_version']}",
        f"benchmark_root: {report['benchmark_root']}",
        f"baseline_profile_id: {report['baseline_profile_id']}",
        f"baseline_stable_manifest_sha256: {baseline['stable_manifest_sha256']}",
        f"baseline_replay_match: {report['determinism']['baseline_replay_match']}",
        f"baseline_replay_stable_manifest_sha256: {replay['stable_manifest_sha256']}",
        f"speedup_floor_fraction: {acceptance['speedup_floor_fraction']}",
        f"memory_growth_ceiling_fraction: {acceptance['memory_growth_ceiling_fraction']}",
        "profiles:",
    ]
    for profile_id, profile in sorted(report["profiles"].items()):
        lines.append(
            f"- {profile_id}: role={profile['role']}, accumulation={profile['hazard_manifest']['performance']['accumulation_seconds']}, "
            f"files={profile['profile_scale']['output_file_count']}, bytes={profile['profile_scale']['output_bytes']}"
        )
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    acceptance = report["acceptance_criteria"]
    lines = [
        "# Hazard Accumulation Hypothesis Benchmark",
        "",
        f"- benchmark_status: `{report['benchmark_status']}`",
        f"- schema_version: `{report['schema_version']}`",
        f"- benchmark_root: `{report['benchmark_root']}`",
        f"- baseline_profile_id: `{report['baseline_profile_id']}`",
        f"- baseline replay match: `{report['determinism']['baseline_replay_match']}`",
        f"- speedup floor: `{acceptance['speedup_floor_fraction']}`",
        f"- memory growth ceiling: `{acceptance['memory_growth_ceiling_fraction']}`",
        "",
        "## Profiles",
    ]
    for profile_id, profile in sorted(report["profiles"].items()):
        lines.extend(
            [
                f"- `{profile_id}` ({profile['role']}): accumulation=`{profile['hazard_manifest']['performance']['accumulation_seconds']}`",
                f"  - files: `{profile['profile_scale']['output_file_count']}`",
                f"  - bytes: `{profile['profile_scale']['output_bytes']}`",
                f"  - stable manifest: `{profile['stable_manifest_sha256']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            f"- {acceptance['speedup_requirement']}",
            f"- {acceptance['memory_requirement']}",
            "",
            "## Boundary",
            f"- {report['claim_boundary_note']}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
