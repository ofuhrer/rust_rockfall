#!/usr/bin/env python3
"""Dry-run estimator for large-scale conditional hazard execution behavior."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path


# Anchor values from clean balfrin Tschamut gate evidence (small-gate scale).
# These are used for calibration only, not as truth for larger runs.
ANCHOR = {
    "release_zones": 10,
    "ensemble_size": 1,
    "trajectories_per_zone": 6,
    "grid_rows": 304,
    "grid_cols": 300,
    "trajectory_chunks": 2,
    "reducer_chunks": 2,
    "output_bytes_scalable_profile": 15_579_398,
    "output_file_count_scalable_profile": 46,
}

REFERENCE_GRID_CELLS = ANCHOR["grid_rows"] * ANCHOR["grid_cols"]
REFERENCE_TOTAL_TRAJECTORIES = (
    ANCHOR["release_zones"] * ANCHOR["ensemble_size"] * ANCHOR["trajectories_per_zone"]
)
REFERENCE_TOTAL_CHUNKS = ANCHOR["trajectory_chunks"] + ANCHOR["reducer_chunks"]
REFERENCE_THRESHOLD_COUNT = 2

# Raster-size calibration on the small-gate run.
BASE_RASTER_ASCII_BYTES = 3_700_000
BASE_RASTER_GEOTIFF_BYTES = 11_700_000
BASE_SIDE_CAR_BYTES = 100_000

# Per-unit growth terms (all intentionally conservative and approximate).
CSV_GRID_BYTES_PER_CELL = 653
TRAJECTORY_TRAILING_BYTES = 250
CHUNK_MANAGEMENT_BYTES = 4_500
PROVENANCE_AUDIT_BYTES = 180_000
SUMMARY_CURVE_BYTES_PER_THRESHOLD = 40_000
FULL_CURVE_MULTIPLIER = 3.2


SUPPORTED_PROFILES = {
    "full_debug",
    "scalable_conditional",
    "provenance_audit",
}


@dataclass(frozen=True)
class EstimateInputs:
    release_zone_count: int
    ensemble_size: int
    trajectory_count: int
    grid_rows: int
    grid_cols: int
    trajectory_workers: int
    reducer_workers: int
    trajectory_chunks: int | None
    reducer_chunks: int | None
    threshold_count: int
    profile: str
    export_geotiff: bool


@dataclass(frozen=True)
class Estimate:
    profile: str
    release_zone_count: int
    trajectory_count: int
    ensemble_size: int
    grid_rows: int
    grid_cols: int
    trajectory_chunks: int
    reducer_chunks: int
    estimated_total_trajectories: int
    total_output_file_count: int
    output_bytes: int
    output_bytes_by_class: dict[str, int]
    file_counts_by_class: dict[str, int]
    dominant_output_classes: list[str]
    chunk_counts: dict[str, int]
    output_file_growth_notes: list[str]
    assumptions: list[str]


def _coerce_positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"{name} must be non-negative")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate output and replay-side artifact scaling for large conditional hazard runs "
            "without executing trajectories or reducers."
        )
    )
    parser.add_argument("--release-zone-count", type=lambda v: _coerce_positive_int(v, "release zone count"), default=ANCHOR["release_zones"])
    parser.add_argument("--ensemble-size", type=lambda v: _coerce_positive_int(v, "ensemble size"), default=ANCHOR["ensemble_size"])
    parser.add_argument(
        "--trajectory-count",
        type=lambda v: _coerce_positive_int(v, "trajectory count per release-zone"),
        default=ANCHOR["trajectories_per_zone"],
    )
    parser.add_argument("--grid-rows", type=lambda v: _coerce_positive_int(v, "grid rows"), default=ANCHOR["grid_rows"])
    parser.add_argument("--grid-cols", type=lambda v: _coerce_positive_int(v, "grid cols"), default=ANCHOR["grid_cols"])
    parser.add_argument("--trajectory-workers", type=lambda v: _coerce_positive_int(v, "trajectory workers"), default=2)
    parser.add_argument("--reducer-workers", type=lambda v: _coerce_positive_int(v, "reducer workers"), default=2)
    parser.add_argument("--trajectory-chunks", type=lambda v: _coerce_positive_int(v, "trajectory chunks"), default=0)
    parser.add_argument("--reducer-chunks", type=lambda v: _coerce_positive_int(v, "reducer chunks"), default=0)
    parser.add_argument("--threshold-count", type=lambda v: _coerce_positive_int(v, "threshold count"), default=2)
    parser.add_argument(
        "--profile",
        choices=sorted(SUPPORTED_PROFILES),
        default="scalable_conditional",
        help="Output profile to estimate.",
    )
    parser.add_argument("--export-geotiff", action="store_true", help="Estimate with GeoTIFF outputs enabled")
    parser.add_argument(
        "--no-export-geotiff",
        action="store_true",
        help="Estimate with GeoTIFF outputs disabled",
    )
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    parser.add_argument("--output-json", type=Path, help="Write JSON summary to this path")
    return parser.parse_args(argv)


def _resolve_export_geotiff(profile: str, export_geotiff: bool, no_export_geotiff: bool) -> bool:
    if export_geotiff and no_export_geotiff:
        raise ValueError("cannot set both --export-geotiff and --no-export-geotiff")
    if no_export_geotiff:
        return False
    if export_geotiff:
        return True
    # Profile defaults: all output profiles are raster-capable by default.
    # Use --no-export-geotiff to model raster-minimal scenarios explicitly.
    return profile in {"full_debug", "scalable_conditional", "provenance_audit"}


def _infer_chunks(total_units: int, workers: int, explicit_chunks: int | None) -> int:
    if explicit_chunks and explicit_chunks > 0:
        return explicit_chunks
    if total_units <= 0:
        return 1
    return max(1, min(workers if workers > 0 else 1, total_units))


def _safe_div(num: int, den: int) -> float:
    if den == 0:
        return 0.0
    return float(num) / float(den)


def _dominant_classes(items: dict[str, int], limit: int = 4) -> list[str]:
    ordered = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
    return [name for name, _value in ordered[:limit]]


def estimate(inputs: EstimateInputs) -> Estimate:
    if inputs.release_zone_count <= 0:
        raise ValueError("release_zone_count must be > 0")
    if inputs.ensemble_size <= 0:
        raise ValueError("ensemble_size must be > 0")
    if inputs.trajectory_count <= 0:
        raise ValueError("trajectory_count must be > 0")

    grid_cells = inputs.grid_rows * inputs.grid_cols
    if grid_cells <= 0:
        raise ValueError("grid rows and cols must be > 0")

    total_trajectories = inputs.release_zone_count * inputs.ensemble_size * inputs.trajectory_count

    trajectory_chunk_units = max(1, inputs.release_zone_count * max(1, inputs.ensemble_size))
    reducer_chunk_units = max(1, total_trajectories)

    trajectory_chunks = _infer_chunks(
        trajectory_chunk_units,
        max(1, inputs.trajectory_workers),
        inputs.trajectory_chunks,
    )
    reducer_chunks = _infer_chunks(
        reducer_chunk_units,
        max(1, inputs.reducer_workers),
        inputs.reducer_chunks,
    )

    cell_scale = _safe_div(grid_cells, REFERENCE_GRID_CELLS)
    trajectory_scale = _safe_div(total_trajectories, REFERENCE_TOTAL_TRAJECTORIES)
    threshold_scale = max(1.0, 1.0 + 0.05 * max(0, inputs.threshold_count - REFERENCE_THRESHOLD_COUNT))
    include_csv = inputs.profile == "full_debug"
    include_full_curves = inputs.profile == "full_debug"
    include_audit_artifacts = inputs.profile == "provenance_audit"

    raster_ascii_bytes = int(BASE_RASTER_ASCII_BYTES * cell_scale * threshold_scale)
    raster_geotiff_bytes = int(BASE_RASTER_GEOTIFF_BYTES * cell_scale * threshold_scale)
    if not inputs.export_geotiff:
        raster_geotiff_bytes = 0

    grid_csv_bytes = int(CSV_GRID_BYTES_PER_CELL * grid_cells) if include_csv else 0

    curve_bytes = int(
        SUMMARY_CURVE_BYTES_PER_THRESHOLD
        * inputs.threshold_count
        * trajectory_scale
        * math.sqrt(max(1.0, cell_scale))
    )
    if include_full_curves:
        curve_bytes = int(curve_bytes * FULL_CURVE_MULTIPLIER)

    sidecar_fixed_bytes = int(
        BASE_SIDE_CAR_BYTES
        * (0.7 + 0.3 * min(2.0, trajectory_scale))
        * (0.9 + 0.1 * threshold_scale)
    )
    # Approximate chunk metadata scales with chunk cardinality, not quadratic cardinality.
    chunk_bytes = int((trajectory_chunks + reducer_chunks) * CHUNK_MANAGEMENT_BYTES)
    trajectory_meta_bytes = total_trajectories * TRAJECTORY_TRAILING_BYTES

    provenance_bytes = PROVENANCE_AUDIT_BYTES if include_audit_artifacts else 0

    total_bytes = (
        raster_ascii_bytes
        + raster_geotiff_bytes
        + grid_csv_bytes
        + curve_bytes
        + sidecar_fixed_bytes
        + chunk_bytes
        + trajectory_meta_bytes
        + provenance_bytes
    )

    base_file_count = {
        "scalable_conditional": 42,
        "provenance_audit": 46,
        "full_debug": 50,
    }[inputs.profile]

    raster_ascii_files = 2 + max(0, inputs.threshold_count - 1)
    raster_geotiff_files = 0 if raster_geotiff_bytes == 0 else (1 + max(0, inputs.threshold_count - 1))
    curve_files = 1
    csv_grid_files = 1 if include_csv else 0

    file_counts_by_class: dict[str, int] = {
        "hazard_raster_ascii": raster_ascii_files,
        "hazard_raster_geotiff": raster_geotiff_files,
        "conditional_curve": curve_files,
        "grid_csv": csv_grid_files,
        "trajectory_artifacts": trajectory_chunks,
        "reducer_artifacts": reducer_chunks,
    }

    if include_audit_artifacts:
        file_counts_by_class["provenance_manifests"] = 4

    file_counts_by_class["trajectory_chunk_pairs"] = trajectory_chunks
    file_counts_by_class["reducer_chunk_pairs"] = reducer_chunks

    file_count_known = sum(file_counts_by_class.values())
    file_count_fixed_core = max(0, base_file_count + 0 - file_count_known)
    file_counts_by_class["other_outputs"] = file_count_fixed_core

    total_file_count = base_file_count + trajectory_chunks + reducer_chunks

    bytes_by_class = {
        "ascii_raster": raster_ascii_bytes,
        "geotiff_raster": raster_geotiff_bytes,
        "grid_csv": grid_csv_bytes,
        "conditional_curve": curve_bytes,
        "chunk_management": chunk_bytes,
        "trajectory_replay": trajectory_meta_bytes,
        "sidecar_metadata": sidecar_fixed_bytes,
    }
    if include_audit_artifacts:
        bytes_by_class["provenance_artifacts"] = provenance_bytes
    bytes_by_class["remainder_bytes"] = max(0, total_bytes - sum(bytes_by_class.values()))

    growth_notes = []
    if total_trajectories > ANCHOR["release_zones"] * ANCHOR["trajectories_per_zone"]:
        growth_notes.append("trajectory count exceeds reference: replay and metadata pressure increase")
    if grid_cells > REFERENCE_GRID_CELLS:
        growth_notes.append("grid surface larger than reference: raster bytes dominate first")
    if trajectory_chunks > ANCHOR["trajectory_chunks"] or reducer_chunks > ANCHOR["reducer_chunks"]:
        growth_notes.append("chunk count increase increases metadata/artifact cardinality")

    assumptions = [
        "projection-only estimate (no execution performed)",
        "output families and coefficients are tied to current conditional profile behavior and balfrin gate evidence",
        "file count model is approximate and includes replay/provenance sidecars",
    ]
    if inputs.profile in {"scalable_conditional", "provenance_audit"}:
        assumptions.append("scalable/provenance profiles assume conditional-curve summary and CSV-grid suppression by intent")

    return Estimate(
        profile=inputs.profile,
        release_zone_count=inputs.release_zone_count,
        trajectory_count=inputs.trajectory_count,
        ensemble_size=inputs.ensemble_size,
        grid_rows=inputs.grid_rows,
        grid_cols=inputs.grid_cols,
        trajectory_chunks=trajectory_chunks,
        reducer_chunks=reducer_chunks,
        estimated_total_trajectories=total_trajectories,
        total_output_file_count=total_file_count,
        output_bytes=total_bytes,
        output_bytes_by_class=bytes_by_class,
        file_counts_by_class=file_counts_by_class,
        dominant_output_classes=_dominant_classes(bytes_by_class),
        chunk_counts={"trajectory_chunks": trajectory_chunks, "reducer_chunks": reducer_chunks},
        output_file_growth_notes=growth_notes,
        assumptions=assumptions,
    )


def format_report(estimate: Estimate) -> str:
    byte_lines = [
        "  " + f"{name}: {value}"
        for name, value in estimate.output_bytes_by_class.items()
    ]
    file_lines = [
        "  " + f"{name}: {value}"
        for name, value in estimate.file_counts_by_class.items()
    ]
    growth_lines = ["  " + entry for entry in estimate.output_file_growth_notes]
    assumption_lines = ["  " + entry for entry in estimate.assumptions]

    return "\n".join(
        [
            f"Profile: {estimate.profile}",
            f"Release zones: {estimate.release_zone_count}",
            f"Ensemble size: {estimate.ensemble_size}",
            f"Trajectories per zone: {estimate.trajectory_count}",
            f"Estimated total trajectories: {estimate.estimated_total_trajectories}",
            f"Grid: {estimate.grid_cols} x {estimate.grid_rows}",
            f"Trajectory chunks: {estimate.trajectory_chunks}",
            f"Reducer chunks: {estimate.reducer_chunks}",
            f"Estimated output bytes: {estimate.output_bytes}",
            f"Estimated output file count: {estimate.total_output_file_count}",
            "Estimated output bytes by class:",
            *byte_lines,
            "Estimated file counts by class:",
            *file_lines,
            "Dominant output classes:",
            "  " + ", ".join(estimate.dominant_output_classes),
            "Growth notes:",
            *(growth_lines or ["  - none"]),
            "Assumptions:",
            *(assumption_lines or ["  - none"]),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        export_geotiff = _resolve_export_geotiff(
            profile=args.profile,
            export_geotiff=args.export_geotiff,
            no_export_geotiff=args.no_export_geotiff,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    try:
        estimate_result = estimate(
            EstimateInputs(
                release_zone_count=args.release_zone_count,
                ensemble_size=max(1, args.ensemble_size),
                trajectory_count=max(1, args.trajectory_count),
                grid_rows=args.grid_rows,
                grid_cols=args.grid_cols,
                trajectory_workers=max(1, args.trajectory_workers),
                reducer_workers=max(1, args.reducer_workers),
                trajectory_chunks=args.trajectory_chunks or None,
                reducer_chunks=args.reducer_chunks or None,
                threshold_count=max(1, args.threshold_count),
                profile=args.profile,
                export_geotiff=export_geotiff,
            )
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    output = {
        "estimate": {
            "profile": estimate_result.profile,
            "release_zone_count": estimate_result.release_zone_count,
            "ensemble_size": estimate_result.ensemble_size,
            "trajectory_count_per_zone": estimate_result.trajectory_count,
            "estimated_total_trajectories": estimate_result.estimated_total_trajectories,
            "grid_rows": estimate_result.grid_rows,
            "grid_cols": estimate_result.grid_cols,
            "trajectory_chunks": estimate_result.trajectory_chunks,
            "reducer_chunks": estimate_result.reducer_chunks,
            "estimated_output_bytes": estimate_result.output_bytes,
            "estimated_output_file_count": estimate_result.total_output_file_count,
            "output_bytes_by_class": estimate_result.output_bytes_by_class,
            "file_counts_by_class": estimate_result.file_counts_by_class,
            "dominant_output_classes": estimate_result.dominant_output_classes,
            "chunk_counts": estimate_result.chunk_counts,
            "growth_notes": estimate_result.output_file_growth_notes,
            "assumptions": estimate_result.assumptions,
        }
    }

    if args.output_json:
        args.output_json.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")

    if args.format in {"text", "both"}:
        print(format_report(estimate_result))
    if args.format in {"json", "both"}:
        print(json.dumps(output, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
