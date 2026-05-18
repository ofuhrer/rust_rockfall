#!/usr/bin/env python3
"""Profile multi-zone hazard-layer post-processing on a deterministic scratch fixture.

The helper is intentionally local and fixture-backed. It materializes a
multi-zone hazard corpus with real coordinate-bearing trajectory, deposition,
and impact-event inputs, runs the existing hazard-layer builder with explicit
grid controls, and summarizes the measured read, accumulation, reducer-merge,
manifest, raster-write, and report-rendering phases together with output
pressure by family.
"""

from __future__ import annotations

import argparse
import csv
import io
import hashlib
import json
import shutil
import sys
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_hazard_layers as hazard
from scripts import summarize_multi_zone_reducer_pressure as reducer_pressure


SCHEMA_VERSION = "multi_zone_hazard_throughput_profile_v1"
DEFAULT_PROFILE_ROOT = Path("/tmp/rust_rockfall/multi_zone_hazard_throughput_profile_v1")
DEFAULT_RELEASE_ZONE_COUNT = 12
DEFAULT_REDUCER_WORKERS = 2
DEFAULT_REDUCER_CHUNK_COUNT = 4
DEFAULT_TRAJECTORY_SAMPLES_PER_ZONE = 5
DEFAULT_IMPACT_ROWS_PER_ZONE = 2
DEFAULT_GRID_XMIN = 0.0
DEFAULT_GRID_YMIN = 0.0
DEFAULT_GRID_CELLSIZE = 1.0
DEFAULT_GRID_NCOLS = 96
DEFAULT_GRID_NROWS = 96
DEFAULT_THRESHOLD_J = (1.0, 5.0)
DEFAULT_THRESHOLD_M = (0.25,)
DEFAULT_THRESHOLD_MPS = (0.75,)
DEFAULT_OUTPUT_BYTES_NO_CHANGE_LIMIT = 250_000
DEFAULT_OUTPUT_FILES_NO_CHANGE_LIMIT = 40
DEFAULT_PHASE_NO_CHANGE_LIMIT_SECONDS = 0.5


class MultiZoneHazardThroughputProfileError(ValueError):
    """User-facing profiler error."""


@dataclass(frozen=True)
class MultiZoneHazardProfileFixture:
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize-root", type=Path, default=None, help="Create the deterministic scratch fixture here first.")
    parser.add_argument("--profile-root", type=Path, default=None, help="Existing scratch fixture root to profile.")
    parser.add_argument("--release-zone-count", type=int, default=DEFAULT_RELEASE_ZONE_COUNT)
    parser.add_argument("--reducer-workers", type=int, default=DEFAULT_REDUCER_WORKERS)
    parser.add_argument("--reducer-chunk-count", type=int, default=DEFAULT_REDUCER_CHUNK_COUNT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.materialize_root is not None:
            fixture = materialize_fixture_root(
                args.materialize_root,
                release_zone_count=args.release_zone_count,
                reducer_workers=args.reducer_workers,
                reducer_chunk_count=args.reducer_chunk_count,
            )
            profile_root = fixture.profile_root
        else:
            profile_root = args.profile_root or DEFAULT_PROFILE_ROOT
        report = build_report(profile_root)
    except MultiZoneHazardThroughputProfileError as exc:
        print(f"multi-zone hazard throughput profile error: {exc}", file=sys.stderr)
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
    return 0 if report["profile_status"] == "profiled_scratch_root" else 2


def materialize_fixture_root(
    profile_root: Path,
    *,
    release_zone_count: int = DEFAULT_RELEASE_ZONE_COUNT,
    reducer_workers: int = DEFAULT_REDUCER_WORKERS,
    reducer_chunk_count: int = DEFAULT_REDUCER_CHUNK_COUNT,
) -> MultiZoneHazardProfileFixture:
    if release_zone_count <= 1:
        raise MultiZoneHazardThroughputProfileError("release_zone_count must be greater than 1")
    if reducer_workers <= 0:
        raise MultiZoneHazardThroughputProfileError("reducer_workers must be greater than 0")
    if reducer_chunk_count <= 0:
        raise MultiZoneHazardThroughputProfileError("reducer_chunk_count must be greater than 0")
    if reducer_chunk_count > release_zone_count:
        raise MultiZoneHazardThroughputProfileError("reducer_chunk_count cannot exceed release_zone_count")

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
    trajectory_rows_per_zone = DEFAULT_TRAJECTORY_SAMPLES_PER_ZONE
    impact_rows_per_zone = DEFAULT_IMPACT_ROWS_PER_ZONE

    deposition_rows: list[dict[str, Any]] = []
    impact_rows: list[dict[str, Any]] = []
    for index, zone in enumerate(release_zones):
        trajectory_path = trajectory_dir / f"{zone['source_zone_id']}.csv"
        impact_path = impact_event_dir / f"{zone['source_zone_id']}.csv"
        trajectory_rows = build_trajectory_rows(zone["source_zone_id"], index, trajectory_rows_per_zone)
        zone_deposition_rows = build_deposition_rows(zone["source_zone_id"], index)
        zone_impact_rows = build_impact_event_rows(zone["source_zone_id"], index, impact_rows_per_zone)
        deposition_rows.extend(zone_deposition_rows)
        impact_rows.extend(zone_impact_rows)
        write_csv(
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
        write_csv(
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
    write_csv(
        deposition_path,
        fieldnames=("trajectory_id", "x_m", "y_m", "z_m", "deposition_mass_kg"),
        rows=deposition_rows,
    )
    write_csv(
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
    write_json(
        diagnostics_path,
        {
            "schema_version": "multi_zone_hazard_profile_diagnostics_v1",
            "note": "deterministic synthetic multi-zone hazard profile fixture",
            "release_zone_count": release_zone_count,
        },
    )

    case_path = input_root / "multi_zone_hazard_profile_case.yaml"
    case = build_case(
        profile_root=profile_root,
        release_zone_count=release_zone_count,
        trajectory_dir=trajectory_dir,
        deposition_path=deposition_path,
        impact_event_dir=impact_event_dir,
    )
    write_yaml(case_path, case)

    fixture_manifest_path = input_root / "multi_zone_hazard_profile_fixture_manifest.json"
    fixture_manifest = {
        "schema_version": "multi_zone_hazard_profile_fixture_manifest_v1",
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
        "grid": {
            "xmin": DEFAULT_GRID_XMIN,
            "ymin": DEFAULT_GRID_YMIN,
            "ncols": DEFAULT_GRID_NCOLS,
            "nrows": DEFAULT_GRID_NROWS,
            "cell_size": DEFAULT_GRID_CELLSIZE,
        },
    }
    fixture_manifest["fixture_fingerprint"] = fixture_fingerprint(fixture_manifest)
    write_json(fixture_manifest_path, fixture_manifest)

    return MultiZoneHazardProfileFixture(
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


def build_report(profile_root: Path) -> dict[str, Any]:
    profile_root = profile_root.resolve()
    fixture_manifest_path = profile_root / "input" / "multi_zone_hazard_profile_fixture_manifest.json"
    case_path = profile_root / "input" / "multi_zone_hazard_profile_case.yaml"
    trajectory_dir = profile_root / "input" / "trajectories"
    deposition_path = profile_root / "input" / "deposition.csv"
    impact_event_dir = profile_root / "input" / "impact_events"
    diagnostics_path = profile_root / "input" / "diagnostics.json"
    missing_paths = [
        str(path)
        for path in (
            fixture_manifest_path,
            case_path,
            trajectory_dir,
            deposition_path,
            impact_event_dir,
            diagnostics_path,
        )
        if not path.exists()
    ]
    if missing_paths:
        raise MultiZoneHazardThroughputProfileError("missing fixture inputs: " + ", ".join(missing_paths))

    fixture_manifest = load_json(fixture_manifest_path)
    case = load_yaml(case_path)
    case["_path"] = str(case_path)
    profile_output_root = profile_root / "output"
    if profile_output_root.exists():
        shutil.rmtree(profile_output_root)
    profile_output_root.mkdir(parents=True, exist_ok=True)

    timing = {"read_seconds": 0.0, "reducer_merge_seconds": 0.0}
    read_started = time.perf_counter()
    _ = load_json(diagnostics_path)
    timing["read_seconds"] += time.perf_counter() - read_started

    original_read_trajectory = hazard.read_trajectory_sample_batch
    original_read_deposition = hazard.read_deposition_batch
    original_read_impact_csv_batches = hazard.read_impact_event_csv_batches
    original_read_impact_parquet_batches = hazard.read_impact_event_parquet_batches
    original_merge = hazard.HazardAccumulator.merge

    def timed_trajectory_reader(path: Path, warnings: list[str]) -> Any:
        started = time.perf_counter()
        try:
            return original_read_trajectory(path, warnings)
        finally:
            timing["read_seconds"] += time.perf_counter() - started

    def timed_deposition_reader(path: Path | None, warnings: list[str]) -> Any:
        started = time.perf_counter()
        try:
            return original_read_deposition(path, warnings)
        finally:
            timing["read_seconds"] += time.perf_counter() - started

    def timed_impact_csv_reader(paths: list[Path], warnings: list[str]) -> Iterator[Any]:
        started = time.perf_counter()
        try:
            for batch in original_read_impact_csv_batches(paths, warnings):
                yield batch
        finally:
            timing["read_seconds"] += time.perf_counter() - started

    def timed_impact_parquet_reader(paths: list[Path], warnings: list[str]) -> Iterator[Any]:
        started = time.perf_counter()
        try:
            for batch in original_read_impact_parquet_batches(paths, warnings):
                yield batch
        finally:
            timing["read_seconds"] += time.perf_counter() - started

    def timed_merge(self: Any, other: Any) -> Any:
        started = time.perf_counter()
        try:
            return original_merge(self, other)
        finally:
            timing["reducer_merge_seconds"] += time.perf_counter() - started

    output_dir = profile_output_root / "hazard"
    args = [
        "--case",
        str(case_path),
        "--output-dir",
        str(output_dir),
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
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--trajectory-workers",
        "1",
        "--reducer-workers",
        "2",
        "--export-geotiff",
        "--diagnostics",
        str(diagnostics_path),
        "--ensemble-trajectories-dir",
        str(trajectory_dir),
        "--deposition",
        str(deposition_path),
        "--ensemble-impact-events-dir",
        str(impact_event_dir),
    ]

    with patch_hazard_timing_functions(
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
        raise MultiZoneHazardThroughputProfileError(f"hazard builder exited with status {status}")

    hazard_manifest_path = output_dir / "multi_zone_hazard_profile_manifest.json"
    if not hazard_manifest_path.exists():
        raise MultiZoneHazardThroughputProfileError(f"missing hazard manifest: {hazard_manifest_path}")
    hazard_manifest = load_json(hazard_manifest_path)
    performance = hazard_manifest.get("performance") or {}
    outputs = hazard_manifest.get("outputs") or []
    if not isinstance(performance, dict) or not isinstance(outputs, list):
        raise MultiZoneHazardThroughputProfileError("hazard manifest missing performance or outputs sections")

    output_pressure = summarize_output_pressure(outputs)
    timing_breakdown = summarize_timing_breakdown(performance, timing)
    bottleneck = classify_bottleneck(output_pressure, timing_breakdown)
    recommendation = recommend_optimization(bottleneck, output_pressure, timing_breakdown)

    report = {
        "schema_version": SCHEMA_VERSION,
        "profile_status": "profiled_scratch_root",
        "profile_root": str(profile_root),
        "fixture": {
            "schema_version": fixture_manifest.get("schema_version"),
            "fixture_manifest_path": str(fixture_manifest_path),
            "case_path": str(case_path),
            "trajectory_dir": str(trajectory_dir),
            "deposition_path": str(deposition_path),
            "impact_event_dir": str(impact_event_dir),
            "diagnostics_path": str(diagnostics_path),
            "release_zone_count": fixture_manifest.get("release_zone_count"),
            "trajectory_file_count": fixture_manifest.get("trajectory_file_count"),
            "impact_file_count": fixture_manifest.get("impact_file_count"),
            "deposition_row_count": fixture_manifest.get("deposition_row_count"),
            "impact_row_count": fixture_manifest.get("impact_row_count"),
            "fixture_fingerprint": fixture_manifest.get("fixture_fingerprint"),
        },
        "hazard_manifest_path": str(hazard_manifest_path),
        "hazard_manifest": {
            "schema_version": hazard_manifest.get("schema_version"),
            "case_id": hazard_manifest.get("case_id"),
            "completion_status": hazard_manifest.get("completion_status"),
            "execution_status": hazard_manifest.get("execution_status"),
            "conditional_execution": hazard_manifest.get("conditional_execution"),
            "performance": {
                "read_seconds": round(timing["read_seconds"], 6),
                "accumulation_seconds": number_or_zero(performance.get("accumulation_seconds")),
                "reducer_merge_seconds": round(timing["reducer_merge_seconds"], 6),
                "manifest_seconds": round(
                    number_or_zero(performance.get("manifest_write_seconds"))
                    + number_or_zero(performance.get("json_serialization_seconds")),
                    6,
                ),
                "raster_write_seconds": round(
                    sum(
                        number_or_zero(value)
                        for key, value in (performance.get("output_write_kind_seconds") or {}).items()
                        if key in {"csv_grid", "esri_ascii_grid", "geotiff"}
                    ),
                    6,
                ),
                "report_render_seconds": round(number_or_zero(performance.get("plot_render_seconds")), 6),
                "cog_export_seconds": None,
            },
        },
        "timings": timing_breakdown,
        "output_pressure": output_pressure,
        "cog_gis_pressure": {
            "status": "not_applicable",
            "reason": "the default fixture does not materialize a map package or pilot GIS package, so COG export is skipped",
            "file_family_bytes": {},
            "manifest_family_bytes": {},
            "file_family_file_counts": {},
            "manifest_family_file_counts": {},
        },
        "bottleneck": bottleneck,
        "recommendation": recommendation,
        "profile_scale": {
            "output_file_count": number_or_zero(performance.get("output_file_count")),
            "output_bytes": number_or_zero(performance.get("output_bytes")),
            "hazard_layer_seconds": number_or_zero(performance.get("hazard_layer_seconds")),
            "total_wall_seconds": number_or_zero(performance.get("total_wall_seconds")),
        },
        "analysis_notes": [
            "The fixture is explicit-grid and summary-only to keep the profile focused on post-processing fan-out.",
            "COG/GIS export is not applicable in the default fixture because the helper does not materialize a map package.",
        ],
    }
    return report


@contextmanager
def patch_hazard_timing_functions(
    module: Any,
    read_trajectory_reader: Any,
    read_deposition_reader: Any,
    read_impact_csv_reader: Any,
    read_impact_parquet_reader: Any,
    merge_hook: Any,
) -> Iterator[None]:
    original = (
        module.read_trajectory_sample_batch,
        module.read_deposition_batch,
        module.read_impact_event_csv_batches,
        module.read_impact_event_parquet_batches,
        module.HazardAccumulator.merge,
    )
    module.read_trajectory_sample_batch = read_trajectory_reader
    module.read_deposition_batch = read_deposition_reader
    module.read_impact_event_csv_batches = read_impact_csv_reader
    module.read_impact_event_parquet_batches = read_impact_parquet_reader
    module.HazardAccumulator.merge = merge_hook
    try:
        yield
    finally:
        (
            module.read_trajectory_sample_batch,
            module.read_deposition_batch,
            module.read_impact_event_csv_batches,
            module.read_impact_event_parquet_batches,
            module.HazardAccumulator.merge,
        ) = original


def build_case(
    *,
    profile_root: Path,
    release_zone_count: int,
    trajectory_dir: Path,
    deposition_path: Path,
    impact_event_dir: Path,
) -> dict[str, Any]:
    title = "Multi-Zone Hazard Throughput Profile"
    return {
        "case_id": "multi_zone_hazard_profile",
        "title": title,
        "level": 4,
        "description": (
            "Deterministic scratch fixture used to profile hazard-layer post-processing on a multi-zone corpus."
        ),
        "terrain": {
            "type": "plane",
            "parameters": {"z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0},
        },
        "block": {"mass": 10.0, "radius": 0.5},
        "release": {"position": [0.0, 0.0, 1.5], "velocity": [1.0, 0.0, 0.0]},
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.5,
            "tangential_restitution": 0.8,
            "friction_coefficient": 0.3,
        },
        "simulation": {"dt": 0.1, "t_max": 2.0, "stop_velocity": 0.1},
        "random": {"seed": 7, "ensemble_size": release_zone_count},
        "outputs": {
            "ensemble_trajectories_dir": str(trajectory_dir),
            "ensemble_deposition_csv": str(deposition_path),
            "ensemble_impact_events_dir": str(impact_event_dir),
        },
        "hazard_layers": {
            "statistics": {
                "kinetic_energy_exceedance_j": list(DEFAULT_THRESHOLD_J),
                "jump_height_exceedance_m": list(DEFAULT_THRESHOLD_M),
                "velocity_exceedance_mps": list(DEFAULT_THRESHOLD_MPS),
            }
        },
        "hazard_output_volume": {
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
        },
        "diagnostics": {
            "profile_root": str(profile_root),
        },
    }


def build_trajectory_rows(trajectory_id: str, zone_index: int, sample_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_x = 4.0 + zone_index * 5.0
    base_y = 6.0 + (zone_index % 4) * 5.0
    base_z = 2.5 + zone_index * 0.1
    for step in range(sample_count):
        rows.append(
            {
                "trajectory_id": trajectory_id,
                "time_s": round(step * 0.5, 3),
                "x_m": round(base_x + step * 0.8, 3),
                "y_m": round(base_y + (step % 2) * 0.4, 3),
                "z_m": round(max(0.5, base_z - step * 0.5), 3),
                "vx_mps": round(1.0 + 0.05 * zone_index, 3),
                "vy_mps": round(0.1 * (step % 3), 3),
                "vz_mps": round(-0.3 * step, 3),
                "speed_mps": round(1.0 + 0.05 * zone_index + 0.1 * step, 3),
                "kinetic_j": round(4.0 + zone_index * 0.5 + step * 0.75, 3),
                "potential_j": round(100.0 - zone_index * 1.2 - step * 2.5, 3),
                "total_energy_j": round(104.0 + zone_index * 0.2 - step * 1.5, 3),
                "contact_state": "airborne" if step < sample_count - 1 else "stopped",
            }
        )
    return rows


def build_deposition_rows(trajectory_id: str, zone_index: int) -> list[dict[str, Any]]:
    return [
        {
            "trajectory_id": trajectory_id,
            "x_m": round(6.0 + zone_index * 5.0, 3),
            "y_m": round(7.0 + (zone_index % 4) * 5.0, 3),
            "z_m": round(0.5 + zone_index * 0.05, 3),
            "deposition_mass_kg": round(120.0 + zone_index * 3.0, 3),
        }
    ]


def build_impact_event_rows(trajectory_id: str, zone_index: int, row_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for impact_index in range(row_count):
        rows.append(
            {
                "trajectory_id": trajectory_id,
                "impact_index": impact_index,
                "time_s": round(0.8 + impact_index * 0.15, 3),
                "x_m": round(6.2 + zone_index * 5.0 + impact_index * 0.1, 3),
                "y_m": round(7.2 + (zone_index % 4) * 5.0, 3),
                "z_m": round(0.5 + zone_index * 0.05, 3),
                "incoming_normal_speed_mps": round(0.2 + impact_index * 0.15, 3),
                "scarring_energy_loss_j": round(0.8 + zone_index * 0.2 + impact_index * 0.1, 3),
            }
        )
    return rows


def summarize_output_pressure(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    layer_family_bytes: dict[str, int] = {}
    layer_family_file_counts: dict[str, int] = {}
    file_family_bytes: dict[str, int] = {}
    file_family_file_counts: dict[str, int] = {}
    manifest_family_bytes: dict[str, int] = {}
    manifest_family_file_counts: dict[str, int] = {}
    for output in outputs:
        kind = str(output.get("kind") or "unknown")
        format_name = str(output.get("format") or "unknown")
        total_bytes = int(output.get("total_bytes") or 0)
        file_count = int(output.get("file_count") or 0)
        layer_name = str(output.get("layer_name") or kind)
        if kind == "hazard_layer":
            layer_family_bytes[layer_name] = layer_family_bytes.get(layer_name, 0) + total_bytes
            layer_family_file_counts[layer_name] = layer_family_file_counts.get(layer_name, 0) + file_count
        file_family_bytes[format_name] = file_family_bytes.get(format_name, 0) + total_bytes
        file_family_file_counts[format_name] = file_family_file_counts.get(format_name, 0) + file_count
        if "manifest" in kind or kind.endswith("_index") or kind.endswith("_plan") or kind == "hazard_metadata":
            manifest_family_bytes[kind] = manifest_family_bytes.get(kind, 0) + total_bytes
            manifest_family_file_counts[kind] = manifest_family_file_counts.get(kind, 0) + file_count
    return {
        "layer_family_bytes": layer_family_bytes,
        "layer_family_file_counts": layer_family_file_counts,
        "file_family_bytes": file_family_bytes,
        "file_family_file_counts": file_family_file_counts,
        "manifest_family_bytes": manifest_family_bytes,
        "manifest_family_file_counts": manifest_family_file_counts,
        "largest_layer_families": largest_families(layer_family_bytes, layer_family_file_counts),
        "largest_file_families": largest_families(file_family_bytes, file_family_file_counts),
        "largest_manifest_families": largest_families(manifest_family_bytes, manifest_family_file_counts),
    }


def summarize_timing_breakdown(performance: dict[str, Any], helper_timing: dict[str, float]) -> dict[str, Any]:
    read_seconds = round(helper_timing["read_seconds"], 6)
    accumulation_seconds = round(number_or_zero(performance.get("accumulation_seconds")), 6)
    reducer_merge_seconds = round(helper_timing["reducer_merge_seconds"], 6)
    manifest_seconds = round(
        number_or_zero(performance.get("manifest_write_seconds"))
        + number_or_zero(performance.get("json_serialization_seconds")),
        6,
    )
    raster_write_seconds = round(
        sum(
            number_or_zero(value)
            for key, value in (performance.get("output_write_kind_seconds") or {}).items()
            if key in {"csv_grid", "esri_ascii_grid", "geotiff"}
        ),
        6,
    )
    report_render_seconds = round(number_or_zero(performance.get("plot_render_seconds")), 6)
    phase_seconds = {
        "read_seconds": read_seconds,
        "accumulation_seconds": accumulation_seconds,
        "reducer_merge_seconds": reducer_merge_seconds,
        "manifest_seconds": manifest_seconds,
        "raster_write_seconds": raster_write_seconds,
        "report_render_seconds": report_render_seconds,
    }
    return {
        "phase_seconds": phase_seconds,
        "largest_phase": max(phase_seconds.items(), key=lambda item: (item[1], phase_rank(item[0]))),
        "total_wall_seconds": round(number_or_zero(performance.get("total_wall_seconds")), 6),
        "output_file_count": number_or_zero(performance.get("output_file_count")),
        "output_bytes": number_or_zero(performance.get("output_bytes")),
    }


def phase_rank(name: str) -> int:
    order = {
        "read_seconds": 0,
        "accumulation_seconds": 1,
        "reducer_merge_seconds": 2,
        "manifest_seconds": 3,
        "raster_write_seconds": 4,
        "report_render_seconds": 5,
    }
    return order.get(name, 99)


def classify_bottleneck(output_pressure: dict[str, Any], timing_breakdown: dict[str, Any]) -> dict[str, Any]:
    largest_phase_name, largest_phase_seconds = timing_breakdown["largest_phase"]
    file_families = output_pressure["largest_file_families"]
    largest_file_family = file_families[0] if file_families else {"kind": "unknown", "total_bytes": 0, "file_count": 0}
    largest_layer_family = (
        output_pressure["largest_layer_families"][0]
        if output_pressure["largest_layer_families"]
        else {"kind": "unknown", "total_bytes": 0, "file_count": 0}
    )
    largest_manifest_family = (
        output_pressure["largest_manifest_families"][0]
        if output_pressure["largest_manifest_families"]
        else {"kind": "unknown", "total_bytes": 0, "file_count": 0}
    )
    profile_small = (
        timing_breakdown["output_file_count"] < DEFAULT_OUTPUT_FILES_NO_CHANGE_LIMIT
        and timing_breakdown["output_bytes"] < DEFAULT_OUTPUT_BYTES_NO_CHANGE_LIMIT
        and largest_phase_seconds < DEFAULT_PHASE_NO_CHANGE_LIMIT_SECONDS
    )
    if profile_small:
        return {
            "label": "no_change",
            "reason": (
                "profile is too small to justify an optimization; "
                f"largest phase is {largest_phase_name} at {largest_phase_seconds:.3f}s and "
                f"output pressure tops out at {largest_file_family['kind']} "
                f"({largest_file_family['file_count']} files / {largest_file_family['total_bytes']} bytes)"
            ),
            "dominant_phase": {
                "name": largest_phase_name,
                "seconds": largest_phase_seconds,
            },
            "dominant_file_family": largest_file_family,
            "dominant_layer_family": largest_layer_family,
            "dominant_manifest_family": largest_manifest_family,
        }
    return {
        "label": str(largest_phase_name),
        "reason": (
            f"{largest_phase_name} dominates at {largest_phase_seconds:.3f}s; "
            f"layer-family pressure is led by {largest_layer_family['kind']} "
            f"({largest_layer_family['file_count']} files / {largest_layer_family['total_bytes']} bytes)"
        ),
        "dominant_phase": {
            "name": largest_phase_name,
            "seconds": largest_phase_seconds,
        },
        "dominant_file_family": largest_file_family,
        "dominant_layer_family": largest_layer_family,
        "dominant_manifest_family": largest_manifest_family,
    }


def recommend_optimization(
    bottleneck: dict[str, Any],
    output_pressure: dict[str, Any],
    timing_breakdown: dict[str, Any],
) -> dict[str, Any]:
    if bottleneck["label"] == "no_change":
        return {
            "label": "no_change",
            "status": "insufficient_scale",
            "reason": bottleneck["reason"],
            "evidence": {
                "output_file_count": timing_breakdown["output_file_count"],
                "output_bytes": timing_breakdown["output_bytes"],
                "dominant_phase": bottleneck["dominant_phase"],
                "dominant_file_family": bottleneck["dominant_file_family"],
            },
        }
    if bottleneck["label"] == "raster_write_seconds":
        return {
            "label": "raster_write_focus",
            "status": "bounded_optimization",
            "reason": (
                "raster writes dominate, so the next bounded optimization should target ancillary "
                "raster fan-out before changing hazard semantics"
            ),
            "evidence": {
                "dominant_phase": bottleneck["dominant_phase"],
                "dominant_file_family": bottleneck["dominant_file_family"],
                "largest_layer_family": bottleneck["dominant_layer_family"],
                "largest_manifest_family": bottleneck["dominant_manifest_family"],
            },
        }
    if bottleneck["label"] == "report_render_seconds":
        return {
            "label": "report_render_focus",
            "status": "bounded_optimization",
            "reason": "report rendering dominates, so suppressing plots for throughput-only runs is the next bounded move",
            "evidence": {
                "dominant_phase": bottleneck["dominant_phase"],
                "dominant_file_family": bottleneck["dominant_file_family"],
                "largest_layer_family": bottleneck["dominant_layer_family"],
            },
        }
    return {
        "label": "accumulator_focus",
        "status": "bounded_optimization",
        "reason": "accumulation dominates, so the next bounded optimization should target accumulator batching or merge handling",
        "evidence": {
            "dominant_phase": bottleneck["dominant_phase"],
            "dominant_file_family": bottleneck["dominant_file_family"],
            "largest_layer_family": bottleneck["dominant_layer_family"],
        },
    }


def largest_families(
    family_bytes: dict[str, int],
    family_file_counts: dict[str, int],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ordered = sorted(family_bytes.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [
        {
            "kind": kind,
            "total_bytes": total_bytes,
            "file_count": family_file_counts.get(kind, 0),
        }
        for kind, total_bytes in ordered
    ]


def fixture_fingerprint(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for key in sorted(payload):
        if key == "fixture_fingerprint":
            continue
        digest.update(str(key).encode("utf-8"))
        digest.update(b"\0")
        value = payload[key]
        digest.update(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_csv(path: Path, *, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context.
        raise MultiZoneHazardThroughputProfileError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MultiZoneHazardThroughputProfileError(f"JSON document must be an object: {path}")
    return payload


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - user-facing path context.
        raise MultiZoneHazardThroughputProfileError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MultiZoneHazardThroughputProfileError(f"YAML document must be a mapping: {path}")
    return payload


def number_or_zero(value: Any) -> int | float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return 0


def render_text(report: dict[str, Any]) -> str:
    timings = report["timings"]["phase_seconds"]
    pressure = report["output_pressure"]
    bottleneck = report["bottleneck"]
    recommendation = report["recommendation"]
    lines = [
        f"profile_status: {report['profile_status']}",
        f"release_zone_count: {report['fixture']['release_zone_count']}",
        f"trajectory_file_count: {report['fixture']['trajectory_file_count']}",
        f"impact_file_count: {report['fixture']['impact_file_count']}",
        f"read_seconds: {timings['read_seconds']}",
        f"accumulation_seconds: {timings['accumulation_seconds']}",
        f"reducer_merge_seconds: {timings['reducer_merge_seconds']}",
        f"manifest_seconds: {timings['manifest_seconds']}",
        f"raster_write_seconds: {timings['raster_write_seconds']}",
        f"report_render_seconds: {timings['report_render_seconds']}",
        f"bottleneck: {bottleneck['label']}",
        f"recommendation: {recommendation['label']}",
        "largest_layer_families:",
    ]
    for item in pressure["largest_layer_families"]:
        lines.append(f"- {item['kind']}: files={item['file_count']}, bytes={item['total_bytes']}")
    lines.append("largest_file_families:")
    for item in pressure["largest_file_families"]:
        lines.append(f"- {item['kind']}: files={item['file_count']}, bytes={item['total_bytes']}")
    lines.append("largest_manifest_families:")
    for item in pressure["largest_manifest_families"]:
        lines.append(f"- {item['kind']}: files={item['file_count']}, bytes={item['total_bytes']}")
    lines.append(f"reason: {bottleneck['reason']}")
    lines.append(f"recommendation_reason: {recommendation['reason']}")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    timings = report["timings"]["phase_seconds"]
    pressure = report["output_pressure"]
    bottleneck = report["bottleneck"]
    recommendation = report["recommendation"]
    lines = [
        "# Multi-Zone Hazard Throughput Profile",
        "",
        f"- profile_status: `{report['profile_status']}`",
        f"- release_zone_count: `{report['fixture']['release_zone_count']}`",
        f"- read_seconds: `{timings['read_seconds']}`",
        f"- accumulation_seconds: `{timings['accumulation_seconds']}`",
        f"- reducer_merge_seconds: `{timings['reducer_merge_seconds']}`",
        f"- manifest_seconds: `{timings['manifest_seconds']}`",
        f"- raster_write_seconds: `{timings['raster_write_seconds']}`",
        f"- report_render_seconds: `{timings['report_render_seconds']}`",
        f"- bottleneck: `{bottleneck['label']}`",
        f"- recommendation: `{recommendation['label']}`",
        "",
        "## Layer Families",
    ]
    lines.extend(
        f"- `{item['kind']}`: `{item['file_count']}` files / `{item['total_bytes']}` bytes"
        for item in pressure["largest_layer_families"]
    )
    lines.append("")
    lines.append("## File Families")
    lines.extend(
        f"- `{item['kind']}`: `{item['file_count']}` files / `{item['total_bytes']}` bytes"
        for item in pressure["largest_file_families"]
    )
    lines.append("")
    lines.append("## Manifest Families")
    lines.extend(
        f"- `{item['kind']}`: `{item['file_count']}` files / `{item['total_bytes']}` bytes"
        for item in pressure["largest_manifest_families"]
    )
    lines.extend(
        [
            "",
            "## Bottleneck",
            f"- {bottleneck['reason']}",
            "",
            "## Recommendation",
            f"- {recommendation['reason']}",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
