#!/usr/bin/env python3
"""Summarize where same-scale hazard uncertainty concentrates spatially.

This helper is read-only. It compares the existing same-scale Tschamut hazard
artifacts and reports cell-wise concentration, support/nodata disagreement, and
high-uncertainty locations for a small selected layer set.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "spatial_same_scale_uncertainty_v1"
DEFAULT_HAZARD_LAYERS = (
    "max_kinetic_energy",
    "max_jump_height",
    "velocity_exceedance_5mps",
)
DEFAULT_MANIFESTS = (
    ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full/validation_tschamut_public_sampling_sensitivity_v2_full_manifest.json",
)


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SpatialSameScaleUncertaintyError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CONVERGENCE = _load_module("spatial_same_scale_uncertainty_compare", "compare_hazard_map_convergence.py")


class SpatialSameScaleUncertaintyError(ValueError):
    """User-facing spatial uncertainty error."""


@dataclass(frozen=True)
class ManifestArtifact:
    requested_path: Path
    manifest_path: Path
    manifest: dict[str, Any]


@dataclass(frozen=True)
class GridHeader:
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata_value: float | None


@dataclass(frozen=True)
class LayerGrid:
    artifact_id: str
    layer_key: str
    grid_path: Path
    header: GridHeader
    grid: list[list[float | None]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        dest="manifests",
        help="hazard manifest file or run directory; may be repeated",
    )
    parser.add_argument(
        "--hazard-layer",
        action="append",
        dest="hazard_layers",
        help="hazard layer key to analyze; may be repeated",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--top-n", type=int, default=8)
    args = parser.parse_args(argv)

    report = build_report(
        manifest_paths=args.manifests or list(DEFAULT_MANIFESTS),
        hazard_layers=tuple(args.hazard_layers or DEFAULT_HAZARD_LAYERS),
        top_n=args.top_n,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["spatial_uncertainty_status"] == "measured_existing_artifacts" else 2


def build_report(
    manifest_paths: Iterable[Path],
    hazard_layers: Iterable[str],
    *,
    top_n: int,
) -> dict[str, Any]:
    manifests = [resolve_manifest(path) for path in manifest_paths]
    selected_layers = normalize_layer_selection(hazard_layers)

    missing_paths = [str(item) for item in collect_missing_paths(manifests, selected_layers)]
    if missing_paths:
        return blocked_report(manifests, selected_layers, missing_paths, reason="required same-scale spatial uncertainty inputs are missing")

    artifacts = [summarize_artifact(manifest) for manifest in manifests]
    layer_summaries = {
        layer_key: summarize_layer(layer_key, artifacts, top_n=top_n)
        for layer_key in selected_layers
    }
    dominant_layers = sorted(
        layer_summaries.values(),
        key=lambda item: (item["range_summary"]["mean_range"] or 0.0, item["nodata_disagreement_fraction"]),
        reverse=True,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "spatial_uncertainty_status": "measured_existing_artifacts",
        "readiness_status": "ready",
        "command_plan_status": "ready",
        "artifacts_measured": artifacts,
        "selected_layers": list(selected_layers),
        "layer_summaries": layer_summaries,
        "dominant_layers_by_mean_range": [item["layer_key"] for item in dominant_layers],
        "dominant_layer_summaries": dominant_layers,
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": "",
        "measurement_command": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
        "spatial_interpretation": spatial_interpretation(dominant_layers),
    }


def blocked_report(
    manifests: list[ManifestArtifact],
    selected_layers: tuple[str, ...],
    missing_paths: list[str],
    *,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "spatial_uncertainty_status": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "command_plan_status": "ready",
        "artifacts_measured": [summarize_manifest_identity(item) for item in manifests if item.manifest_path.exists()],
        "selected_layers": list(selected_layers),
        "layer_summaries": {},
        "dominant_layers_by_mean_range": [],
        "dominant_layer_summaries": [],
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": reason,
        "missing_input_paths": missing_paths,
        "measurement_command": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
        "spatial_interpretation": "blocked_missing_inputs",
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"spatial same-scale uncertainty: {report['spatial_uncertainty_status']}",
        f"selected layers: {', '.join(report.get('selected_layers', []))}",
    ]
    if report["spatial_uncertainty_status"] != "measured_existing_artifacts":
        lines.append(f"blocked reason: {report['blocked_reason']}")
        for path in report.get("missing_input_paths", []):
            lines.append(f"- missing: {path}")
        return "\n".join(lines)

    for layer_key in report["selected_layers"]:
        summary = report["layer_summaries"][layer_key]
        lines.append(
            f"- {layer_key}: {summary['uncertainty_concentration_class']} | "
            f"shared_valid={summary['shared_valid_cell_count']}/{summary['analysis_cell_count']} | "
            f"nodata_disagreement={summary['nodata_disagreement_count']} | "
            f"stability={summary['nonzero_support_stability_fraction']:.6g} | "
            f"range_p95={summary['range_summary']['p95_range']:.6g}"
        )
        if summary["high_uncertainty_bbox"] is not None:
            bbox = summary["high_uncertainty_bbox"]
            lines.append(
                "  high-uncertainty bbox: "
                f"rows {bbox['row_min']}..{bbox['row_max']}, cols {bbox['col_min']}..{bbox['col_max']}, "
                f"LV95 x {bbox['xmin']:.2f}..{bbox['xmax']:.2f}, y {bbox['ymin']:.2f}..{bbox['ymax']:.2f}"
            )
        lines.append(f"  top cells: {len(summary['top_high_uncertainty_cells'])}")
    return "\n".join(lines)


def summarize_manifest_identity(manifest: ManifestArtifact) -> dict[str, Any]:
    return {
        "requested_path": str(manifest.requested_path),
        "manifest_path": str(manifest.manifest_path),
        "case_id": manifest.manifest.get("case_id"),
        "cellwise_layer_count": len(manifest.manifest.get("cellwise_layers") or []),
    }


def summarize_artifact(manifest: ManifestArtifact) -> dict[str, Any]:
    case_id = manifest.manifest.get("case_id") or manifest.manifest_path.parent.name
    grid = manifest.manifest.get("grid") or {}
    return {
        "artifact_id": case_id,
        "requested_path": str(manifest.requested_path),
        "manifest_path": str(manifest.manifest_path),
        "cellwise_layer_count": len(manifest.manifest.get("cellwise_layers") or []),
        "grid": {
            "ncols": grid.get("ncols"),
            "nrows": grid.get("nrows"),
            "xllcorner": grid.get("xllcorner"),
            "yllcorner": grid.get("yllcorner"),
            "cellsize": grid.get("cellsize"),
        },
    }


def summarize_layer(layer_key: str, artifacts: list[dict[str, Any]], *, top_n: int) -> dict[str, Any]:
    layer_grids = [load_layer_grid(artifact["manifest_path"], layer_key) for artifact in artifacts]
    nrows = layer_grids[0].header.nrows
    ncols = layer_grids[0].header.ncols
    xllcorner = layer_grids[0].header.xllcorner
    yllcorner = layer_grids[0].header.yllcorner
    cellsize = layer_grids[0].header.cellsize

    for layer in layer_grids[1:]:
        if layer.header.nrows != nrows or layer.header.ncols != ncols or layer.header.cellsize != cellsize:
            raise SpatialSameScaleUncertaintyError(f"layer grid shape mismatch for {layer_key}")

    analysis_cell_count = nrows * ncols
    shared_valid_ranges: list[float] = []
    any_valid_count = 0
    shared_valid_count = 0
    all_nodata_count = 0
    nodata_disagreement_count = 0
    nonzero_union_count = 0
    nonzero_intersection_count = 0
    high_uncertainty_cells: list[dict[str, Any]] = []

    cells: list[dict[str, Any]] = []
    for row in range(nrows):
        for col in range(ncols):
            values = [layer.grid[row][col] for layer in layer_grids]
            valid_flags = [value is not None for value in values]
            valid_values = [float(value) for value in values if value is not None]
            any_valid = bool(valid_values)
            all_valid = all(valid_flags)
            if any_valid:
                any_valid_count += 1
            if all_valid:
                shared_valid_count += 1
                value_range = max(valid_values) - min(valid_values)
                shared_valid_ranges.append(value_range)
            else:
                value_range = None
                if any(valid_flags) and not all(valid_flags):
                    nodata_disagreement_count += 1
                elif not any_valid:
                    all_nodata_count += 1

            support_flags = [bool(value not in (None, 0.0)) for value in values]
            if any(support_flags):
                nonzero_union_count += 1
            if all(support_flags):
                nonzero_intersection_count += 1

            cells.append(
                {
                    "row": row,
                    "col": col,
                    "values": values,
                    "valid_flags": valid_flags,
                    "support_flags": support_flags,
                    "range": value_range,
                }
            )

    if not shared_valid_ranges:
        raise SpatialSameScaleUncertaintyError(f"no shared-valid cells found for {layer_key}")

    p50 = percentile(shared_valid_ranges, 0.50)
    p90 = percentile(shared_valid_ranges, 0.90)
    p95 = percentile(shared_valid_ranges, 0.95)
    range_threshold = p95
    high_uncertainty = [
        cell
        for cell in cells
        if cell["range"] is not None and cell["range"] >= range_threshold
    ]
    high_uncertainty.sort(key=lambda cell: (-float(cell["range"]), cell["row"], cell["col"]))
    high_uncertainty = high_uncertainty[: max(top_n, 1)] if top_n > 0 else []

    bbox = bbox_for_cells(high_uncertainty, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
    centroid = centroid_for_cells(high_uncertainty, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)

    interpretation = classify_layer(
        layer_key,
        nodata_disagreement_count=nodata_disagreement_count,
        any_valid_count=any_valid_count,
        shared_valid_count=shared_valid_count,
        nonzero_union_count=nonzero_union_count,
        nonzero_intersection_count=nonzero_intersection_count,
        high_uncertainty_bbox=bbox,
        analysis_cell_count=analysis_cell_count,
        high_uncertainty_count=len(high_uncertainty),
    )

    return {
        "layer_key": layer_key,
        "artifact_count": len(layer_grids),
        "artifact_ids": [layer.artifact_id for layer in layer_grids],
        "grid_shape": {
            "nrows": nrows,
            "ncols": ncols,
            "cellsize": cellsize,
            "xllcorner": xllcorner,
            "yllcorner": yllcorner,
        },
        "analysis_cell_count": analysis_cell_count,
        "any_valid_cell_count": any_valid_count,
        "shared_valid_cell_count": shared_valid_count,
        "all_nodata_cell_count": all_nodata_count,
        "nodata_disagreement_count": nodata_disagreement_count,
        "nodata_disagreement_fraction": nodata_disagreement_count / any_valid_count if any_valid_count else 0.0,
        "nonzero_support_union_count": nonzero_union_count,
        "nonzero_support_intersection_count": nonzero_intersection_count,
        "nonzero_support_stability_fraction": (
            nonzero_intersection_count / nonzero_union_count if nonzero_union_count else 1.0
        ),
        "range_summary": {
            "max_range": max(shared_valid_ranges),
            "mean_range": mean(shared_valid_ranges),
            "p50_range": p50,
            "p90_range": p90,
            "p95_range": p95,
        },
        "high_uncertainty_threshold": range_threshold,
        "high_uncertainty_cell_count": len(high_uncertainty),
        "high_uncertainty_cell_fraction": len(high_uncertainty) / shared_valid_count if shared_valid_count else 0.0,
        "high_uncertainty_bbox": bbox,
        "high_uncertainty_centroid": centroid,
        "top_high_uncertainty_cells": [
            format_high_uncertainty_cell(cell, layer_grids, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
            for cell in high_uncertainty
        ],
        "uncertainty_concentration_class": interpretation["uncertainty_concentration_class"],
        "interpretation_note": interpretation["interpretation_note"],
    }


def classify_layer(
    layer_key: str,
    *,
    nodata_disagreement_count: int,
    any_valid_count: int,
    shared_valid_count: int,
    nonzero_union_count: int,
    nonzero_intersection_count: int,
    high_uncertainty_bbox: dict[str, Any] | None,
    analysis_cell_count: int,
    high_uncertainty_count: int,
) -> dict[str, str]:
    nodata_fraction = nodata_disagreement_count / any_valid_count if any_valid_count else 0.0
    if nodata_fraction >= 0.15:
        return {
            "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
            "interpretation_note": (
                f"{layer_key} shows substantial nodata/support disagreement across artifacts "
                f"({nodata_disagreement_count} cells / {any_valid_count} valid-any cells)."
            ),
        }

    if high_uncertainty_bbox is None:
        return {
            "uncertainty_concentration_class": "shared_support_magnitude_diffuse",
            "interpretation_note": f"{layer_key} has no selected high-uncertainty cells to localize.",
        }

    bbox_cells = (high_uncertainty_bbox["row_max"] - high_uncertainty_bbox["row_min"] + 1) * (
        high_uncertainty_bbox["col_max"] - high_uncertainty_bbox["col_min"] + 1
    )
    bbox_fraction = bbox_cells / analysis_cell_count if analysis_cell_count else 1.0
    high_fraction = high_uncertainty_count / shared_valid_count if shared_valid_count else 1.0
    stability = nonzero_intersection_count / nonzero_union_count if nonzero_union_count else 1.0

    if bbox_fraction <= 0.12 and high_fraction <= 0.12:
        return {
            "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
            "interpretation_note": (
                f"{layer_key} concentrates in a small shared-support cluster "
                f"(bbox fraction {bbox_fraction:.3f}, high-cell fraction {high_fraction:.3f}, "
                f"stability {stability:.3f})."
            ),
        }

    return {
        "uncertainty_concentration_class": "diffuse_across_shared_support",
        "interpretation_note": (
            f"{layer_key} spreads across the shared support rather than a tight cluster "
            f"(bbox fraction {bbox_fraction:.3f}, high-cell fraction {high_fraction:.3f}, stability {stability:.3f})."
        ),
    }


def format_high_uncertainty_cell(
    cell: dict[str, Any],
    layer_grids: list[LayerGrid],
    *,
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
) -> dict[str, Any]:
    row = cell["row"]
    col = cell["col"]
    x = xllcorner + (col + 0.5) * cellsize
    y = yllcorner + ((nrows - row - 0.5) * cellsize)
    values_by_artifact = {
        layer.artifact_id: value
        for layer, value in zip(layer_grids, cell["values"], strict=True)
    }
    return {
        "row": row,
        "col": col,
        "x_center": x,
        "y_center": y,
        "range": cell["range"],
        "values_by_artifact": values_by_artifact,
        "valid_flags_by_artifact": {
            layer.artifact_id: valid
            for layer, valid in zip(layer_grids, cell["valid_flags"], strict=True)
        },
        "support_flags_by_artifact": {
            layer.artifact_id: support
            for layer, support in zip(layer_grids, cell["support_flags"], strict=True)
        },
    }


def bbox_for_cells(
    cells: list[dict[str, Any]],
    *,
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
) -> dict[str, Any] | None:
    if not cells:
        return None
    row_min = min(cell["row"] for cell in cells)
    row_max = max(cell["row"] for cell in cells)
    col_min = min(cell["col"] for cell in cells)
    col_max = max(cell["col"] for cell in cells)
    xmin = xllcorner + col_min * cellsize
    xmax = xllcorner + (col_max + 1) * cellsize
    ymax = yllcorner + (nrows - row_min) * cellsize
    ymin = yllcorner + (nrows - (row_max + 1)) * cellsize
    return {
        "row_min": row_min,
        "row_max": row_max,
        "col_min": col_min,
        "col_max": col_max,
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
    }


def centroid_for_cells(
    cells: list[dict[str, Any]],
    *,
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
) -> dict[str, float] | None:
    if not cells:
        return None
    xs = [xllcorner + (cell["col"] + 0.5) * cellsize for cell in cells]
    ys = [yllcorner + ((nrows - cell["row"] - 0.5) * cellsize) for cell in cells]
    return {"x": mean(xs), "y": mean(ys)}


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def normalize_layer_selection(hazard_layers: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    selection: list[str] = []
    for layer in hazard_layers:
        if layer not in seen:
            selection.append(layer)
            seen.add(layer)
    if not selection:
        raise SpatialSameScaleUncertaintyError("provide at least one hazard layer")
    return tuple(selection)


def collect_missing_paths(manifests: list[ManifestArtifact], selected_layers: tuple[str, ...]) -> list[Path]:
    missing: list[Path] = []
    for manifest in manifests:
        if not manifest.manifest_path.exists():
            missing.append(manifest.manifest_path)
            continue
        selected_entries = layer_entries_for_selection(manifest.manifest, selected_layers)
        if len(selected_entries) != len(selected_layers):
            missing.extend(
                manifest.manifest_path.parent / f"missing_layer_{layer_key}"
                for layer_key in selected_layers
                if layer_key not in selected_entries
            )
            continue
        for layer_key, entry in selected_entries.items():
            grid_path = resolve_artifact_path(entry["grid_path"], manifest.manifest_path.parent)
            if not grid_path.exists():
                missing.append(grid_path)
    return missing


def layer_entries_for_selection(manifest: dict[str, Any], selected_layers: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("cellwise_layers")
    if not isinstance(entries, list):
        raise SpatialSameScaleUncertaintyError("manifest is missing cellwise_layers")
    index: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        layer_key = entry.get("key") or entry.get("layer_name")
        if isinstance(layer_key, str):
            index[layer_key] = entry
    return {layer_key: index[layer_key] for layer_key in selected_layers if layer_key in index}


def load_layer_grid(manifest_path: Path, layer_key: str) -> LayerGrid:
    resolved = CONVERGENCE.resolve_manifest(Path(manifest_path))
    entries = layer_entries_for_selection(resolved.manifest, (layer_key,))
    if layer_key not in entries:
        raise SpatialSameScaleUncertaintyError(f"manifest does not include layer {layer_key}: {manifest_path}")
    entry = entries[layer_key]
    grid_path = resolve_artifact_path(str(entry.get("grid_path")), resolved.manifest_path.parent)
    grid, header = load_grid_with_header(grid_path)
    artifact_id = resolved.manifest.get("case_id") or resolved.manifest_path.parent.name
    return LayerGrid(artifact_id=artifact_id, layer_key=layer_key, grid_path=grid_path, header=header, grid=grid)


def load_grid_with_header(path: Path) -> tuple[list[list[float | None]], GridHeader]:
    try:
        lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        raise SpatialSameScaleUncertaintyError(f"unable to read cell grid: {path}") from exc
    if len(lines) < 6:
        raise SpatialSameScaleUncertaintyError(f"cell grid is too short to contain an ASCII header: {path}")

    header: dict[str, str] = {}
    for line in lines[:6]:
        parts = line.split()
        if len(parts) < 2:
            raise SpatialSameScaleUncertaintyError(f"malformed ASCII grid header in {path}")
        header[parts[0].lower()] = parts[1]

    try:
        ncols = int(header["ncols"])
        nrows = int(header["nrows"])
        xllcorner = float(header["xllcorner"])
        yllcorner = float(header["yllcorner"])
        cellsize = float(header["cellsize"])
    except KeyError as exc:
        raise SpatialSameScaleUncertaintyError(f"ASCII grid header missing required fields in {path}") from exc
    except ValueError as exc:
        raise SpatialSameScaleUncertaintyError(f"ASCII grid header has invalid numeric values in {path}") from exc

    nodata_value = None
    if "nodata_value" in header:
        try:
            nodata_value = float(header["nodata_value"])
        except ValueError as exc:
            raise SpatialSameScaleUncertaintyError(f"ASCII grid nodata_value is invalid in {path}") from exc

    data_lines = lines[6:]
    if len(data_lines) != nrows:
        raise SpatialSameScaleUncertaintyError(f"ASCII grid row count mismatch in {path}")

    grid: list[list[float | None]] = []
    for line in data_lines:
        values = line.split()
        if len(values) != ncols:
            raise SpatialSameScaleUncertaintyError(f"ASCII grid column count mismatch in {path}")
        grid.append([normalize_grid_value(value, nodata_value) for value in values])

    return grid, GridHeader(
        ncols=ncols,
        nrows=nrows,
        xllcorner=xllcorner,
        yllcorner=yllcorner,
        cellsize=cellsize,
        nodata_value=nodata_value,
    )


def normalize_grid_value(value: str, nodata_value: float | None) -> float | None:
    numeric = float(value)
    if nodata_value is not None and numeric == nodata_value:
        return None
    return numeric


def resolve_manifest(requested_path: Path) -> ManifestArtifact:
    if not requested_path.exists():
        return ManifestArtifact(requested_path=requested_path, manifest_path=requested_path, manifest={})
    resolved = CONVERGENCE.resolve_manifest(requested_path)
    return ManifestArtifact(
        requested_path=requested_path,
        manifest_path=resolved.manifest_path,
        manifest=resolved.manifest,
    )


def resolve_artifact_path(path_value: str, manifest_dir: Path) -> Path:
    return CONVERGENCE.resolve_artifact_path(path_value, manifest_dir)


def spatial_interpretation(dominant_layers: list[dict[str, Any]]) -> str:
    if not dominant_layers:
        return "blocked_missing_inputs"
    most = dominant_layers[0]
    if most["uncertainty_concentration_class"] == "dominated_by_nodata_support_differences":
        return "nodata_support_dominated"
    if most["uncertainty_concentration_class"] == "spatially_localized_shared_support_magnitude":
        return "spatially_localized"
    return "diffuse_across_shared_support"


if __name__ == "__main__":
    raise SystemExit(main())
