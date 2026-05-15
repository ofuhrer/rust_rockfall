#!/usr/bin/env python3
"""Measure corridor-level hazard/context overlap for the selected Tschamut pilot.

The overlap report is diagnostic and non-operational. It combines selected
same-scale hazard raster cells from the restored target manifest with the staged
swissTLM3D archive queried at corridor level. The report quantifies how many of
the highest-relevance hazard cells lie near limiting roads, barrier/protection,
and water/channel features, without inferring obstacle absence or changing any
physics, thresholds, or validation baselines.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_hazard_context_overlap_v1"
DEFAULT_HAZARD_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
DEFAULT_CONTEXT_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json"
DEFAULT_SCOPE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml"
DEFAULT_SELECTED_LAYER_GROUPS = [
    ("reach_probability", ("reach_probability", "weighted_reach_probability")),
    ("deposition_density", ("deposition_density", "weighted_deposition_density")),
    ("max_kinetic_energy", ("max_kinetic_energy",)),
    ("max_jump_height", ("max_jump_height",)),
    ("velocity_exceedance_5mps", ("velocity_exceedance_5mps", "weighted_velocity_exceedance_5mps")),
]
DEFAULT_BUFFER_RADII_M = (5.0, 10.0, 20.0, 40.0, 80.0)
DEFAULT_TOP_CELL_COUNT = 10
TARGET_CONVERGENCE_INTERPRETATION = "inconclusive"
VALIDATION_OUTPUT_CONTEXT = "summary_only"
OVERLAP_CONTEXT_CATEGORIES = ("roads_or_transport", "barriers_or_protection", "water_or_channel")
INTERPRETATION_BOUNDARY_NOTE = (
    "Context overlap is measured evidence only; it does not implement obstacle physics, "
    "does not validate hazard-map skill, and does not authorize scale-up."
)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


INSPECTOR = load_module(ROOT / "scripts" / "inspect_tschamut_public_context_layers.py", "tschamut_context_inspector_for_overlap")
SWISSTLM3D_QUERY_SPEC = INSPECTOR.SWISSTLM3D_CORRIDOR_QUERY_SPEC
SWISSTLM3D_ARCHIVE_MEMBER_ROOT = INSPECTOR.SWISSTLM3D_ARCHIVE_MEMBER_ROOT


class HazardContextOverlapError(ValueError):
    """User-facing overlap measurement error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hazard-manifest", type=Path, default=DEFAULT_HAZARD_MANIFEST)
    parser.add_argument("--context-metadata", type=Path, default=DEFAULT_CONTEXT_METADATA)
    parser.add_argument("--scope-record", type=Path, default=DEFAULT_SCOPE_RECORD)
    parser.add_argument(
        "--hazard-layer",
        action="append",
        dest="hazard_layers",
        default=None,
        help="Optional hazard layer name to analyze; may be repeated.",
    )
    parser.add_argument("--top-cell-count", type=int, default=DEFAULT_TOP_CELL_COUNT)
    parser.add_argument(
        "--buffer-radii-m",
        type=float,
        nargs="*",
        default=list(DEFAULT_BUFFER_RADII_M),
        help="Ordered search radii used to classify cell proximity.",
    )
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        report = build_summary(
            hazard_manifest_path=args.hazard_manifest,
            context_metadata_path=args.context_metadata,
            scope_record_path=args.scope_record,
            hazard_layers=args.hazard_layers,
            top_cell_count=args.top_cell_count,
            buffer_radii_m=args.buffer_radii_m,
        )
    except HazardContextOverlapError as exc:
        print(f"hazard-context overlap error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(
            "hazard-context overlap summary: "
            f"{report['final_classification']} "
            f"(hazard_status={report['hazard_context_overlap_status']}, "
            f"context_status={report['context_archive_status']}, "
            f"layers={len(report['selected_hazard_layers'])})"
        )
    return 0


def build_summary(
    *,
    hazard_manifest_path: Path = DEFAULT_HAZARD_MANIFEST,
    context_metadata_path: Path = DEFAULT_CONTEXT_METADATA,
    scope_record_path: Path = DEFAULT_SCOPE_RECORD,
    hazard_layers: list[str] | None = None,
    top_cell_count: int = DEFAULT_TOP_CELL_COUNT,
    buffer_radii_m: list[float] | tuple[float, ...] = DEFAULT_BUFFER_RADII_M,
) -> dict[str, Any]:
    context_metadata_path = require_existing_path(context_metadata_path, "context_metadata_path")
    scope_record_path = require_existing_path(scope_record_path, "scope_record_path")
    if not hazard_manifest_path.exists():
        context_metadata = read_json(context_metadata_path)
        selected_extent = load_selected_extent(scope_record_path, context_metadata_path)
        archive_path = resolve_archive_path(context_metadata, root=ROOT)
        return build_blocked_report(
            hazard_manifest_path=hazard_manifest_path,
            context_metadata_path=context_metadata_path,
            scope_record_path=scope_record_path,
            selected_extent=selected_extent,
            context_metadata=context_metadata,
            archive_path=archive_path,
            context_archive_status="blocked_missing_inputs",
            blocked_reason=f"hazard manifest is absent at {hazard_manifest_path}",
            target_layer_entries=[],
        )

    hazard_manifest_path = require_existing_path(hazard_manifest_path, "hazard_manifest_path")

    hazard_manifest = read_json(hazard_manifest_path)
    if hazard_manifest.get("schema_version") != "run_manifest_v1":
        raise HazardContextOverlapError("hazard manifest must use schema_version run_manifest_v1")
    target_layer_entries = require_list(hazard_manifest.get("cellwise_layers"), "hazard_manifest.cellwise_layers")
    selected_extent = load_selected_extent(scope_record_path, context_metadata_path)
    context_metadata = read_json(context_metadata_path)
    archive_path = resolve_archive_path(context_metadata, root=ROOT)
    context_archive_status, blocked_reason = resolve_context_archive_status(context_metadata, archive_path)
    if blocked_reason is not None:
        return build_blocked_report(
            hazard_manifest_path=hazard_manifest_path,
            context_metadata_path=context_metadata_path,
            scope_record_path=scope_record_path,
            selected_extent=selected_extent,
            context_metadata=context_metadata,
            archive_path=archive_path,
            context_archive_status=context_archive_status,
            blocked_reason=blocked_reason,
            target_layer_entries=target_layer_entries,
        )

    context_report = build_context_baseline_report(context_metadata, archive_path, selected_extent)

    if hazard_layers:
        requested = list(hazard_layers)
    else:
        requested = [group[0] for group in DEFAULT_SELECTED_LAYER_GROUPS]

    selected_layers: list[dict[str, Any]] = []
    hazard_mask_criteria: list[dict[str, Any]] = []
    layer_lookup = {entry["layer_name"]: entry for entry in target_layer_entries}
    for requested_name in requested:
        layer_entry, resolved_name = select_layer_entry(layer_lookup, requested_name)
        grid_path = ROOT / require_text(layer_entry.get("grid_path"), f"cellwise_layers.{resolved_name}.grid_path")
        if not grid_path.exists():
            raise HazardContextOverlapError(f"hazard grid is absent at {grid_path}")
        grid = read_esri_ascii_grid(grid_path)
        selected_cells = select_high_relevance_cells(grid["cells"], top_cell_count)
        selected_layers.append(
            {
                "requested_layer_name": requested_name,
                "layer_name": resolved_name,
                "grid_path": str(grid_path),
                "format": require_text(layer_entry.get("format"), f"cellwise_layers.{resolved_name}.format"),
                "thresholds": layer_entry.get("thresholds", []),
                "positive_cell_count": grid["positive_cell_count"],
                "selected_cell_count": len(selected_cells),
                "max_value": grid["max_value"],
                "selection_value_cutoff": selected_cells[-1]["value"] if selected_cells else None,
                "cell_size_m": grid["cell_size"],
                "extent_lv95_m": grid["extent_lv95_m"],
            }
        )
        hazard_mask_criteria.append(
            {
                "requested_layer_name": requested_name,
                "selected_layer_name": resolved_name,
                "selection_method": "top_positive_cells",
                "top_cell_count": min(top_cell_count, grid["positive_cell_count"]),
                "positive_cell_count": grid["positive_cell_count"],
                "selected_cell_count": len(selected_cells),
                "selection_value_cutoff": selected_cells[-1]["value"] if selected_cells else None,
                "buffer_radii_m": list(buffer_radii_m),
                "notes": "Top positive-valued cells are used as a transparent high-relevance mask; no acceptance threshold is implied.",
            }
        )

    if not selected_layers:
        raise HazardContextOverlapError("no hazard layers could be selected")

    per_layer_results = []
    aggregate_category_totals = {category: 0 for category in OVERLAP_CONTEXT_CATEGORIES}
    aggregate_category_selected = {category: 0 for category in OVERLAP_CONTEXT_CATEGORIES}
    aggregate_cell_fractions: dict[str, dict[str, float | None]] = {}
    overlap_cell_counts: dict[str, dict[str, dict[str, int]]] = {}
    overlap_cell_fractions: dict[str, dict[str, dict[str, float | None]]] = {}
    nearest_distances_m: dict[str, dict[str, float | None]] = {}
    selected_cell_total = 0

    for layer_summary in selected_layers:
        grid_path = Path(layer_summary["grid_path"])
        grid = read_esri_ascii_grid(grid_path)
        selected_cells = select_high_relevance_cells(grid["cells"], top_cell_count)
        selected_cell_total += len(selected_cells)
        layer_counts: dict[str, dict[str, int]] = {}
        layer_fractions: dict[str, dict[str, float | None]] = {}
        layer_nearest: dict[str, float | None] = {}
        selected_points = [cell for cell in selected_cells]
        for category in OVERLAP_CONTEXT_CATEGORIES:
            layer_specs = SWISSTLM3D_QUERY_SPEC[category]
            hit_within_10m = 0
            hit_within_20m = 0
            nearest_distance = None
            per_cell_distances: list[float] = []
            for cell in selected_points:
                distance = first_hit_radius_m(
                    archive_path=archive_path,
                    category=category,
                    x=cell["x"],
                    y=cell["y"],
                    radii_m=buffer_radii_m,
                    layer_specs=layer_specs,
                )
                if distance is not None:
                    per_cell_distances.append(distance)
                    if distance <= 10:
                        hit_within_10m += 1
                    if distance <= 20:
                        hit_within_20m += 1
            if per_cell_distances:
                nearest_distance = min(per_cell_distances)
            layer_counts[category] = {
                "within_10m_cell_count": hit_within_10m,
                "within_20m_cell_count": hit_within_20m,
            }
            layer_fractions[category] = {
                "within_10m_fraction": fraction(hit_within_10m, len(selected_points)),
                "within_20m_fraction": fraction(hit_within_20m, len(selected_points)),
            }
            layer_nearest[category] = nearest_distance
            aggregate_category_totals[category] += hit_within_20m
            aggregate_category_selected[category] += len(selected_points)
        overlap_cell_counts[layer_summary["layer_name"]] = layer_counts
        overlap_cell_fractions[layer_summary["layer_name"]] = layer_fractions
        nearest_distances_m[layer_summary["layer_name"]] = layer_nearest
        aggregate_cell_fractions[layer_summary["layer_name"]] = {
            category: fraction(values["within_20m_cell_count"], len(selected_points))
            for category, values in layer_counts.items()
        }
        per_layer_results.append(
            {
                "layer_name": layer_summary["layer_name"],
                "selected_cell_count": len(selected_points),
                "hazard_mask_criterion": next(
                    item for item in hazard_mask_criteria if item["selected_layer_name"] == layer_summary["layer_name"]
                ),
                "roads_or_transport_overlap": category_overlap_summary(layer_counts["roads_or_transport"], layer_fractions["roads_or_transport"], layer_nearest["roads_or_transport"]),
                "barriers_or_protection_overlap": category_overlap_summary(layer_counts["barriers_or_protection"], layer_fractions["barriers_or_protection"], layer_nearest["barriers_or_protection"]),
                "water_or_channel_overlap": category_overlap_summary(layer_counts["water_or_channel"], layer_fractions["water_or_channel"], layer_nearest["water_or_channel"]),
            }
        )

    final_classification = determine_final_classification(per_layer_results, context_report)
    return {
        "report_schema_version": SCHEMA_VERSION,
        "pilot_id": context_metadata.get("pilot_id", "tschamut_public_pilot"),
        "hazard_manifest_path": str(hazard_manifest_path),
        "context_metadata_path": str(context_metadata_path),
        "hazard_context_overlap_status": "measured",
        "context_archive_status": context_archive_status,
        "context_classification": context_report["classification"],
        "selected_extent_or_corridor": context_report["selected_extent_or_corridor"],
        "selected_hazard_layers": selected_layers,
        "hazard_mask_criteria": hazard_mask_criteria,
        "context_categories_queried": list(OVERLAP_CONTEXT_CATEGORIES),
        "roads_or_transport_overlap": summarize_category_from_layers(per_layer_results, "roads_or_transport"),
        "barriers_or_protection_overlap": summarize_category_from_layers(per_layer_results, "barriers_or_protection"),
        "water_or_channel_overlap": summarize_category_from_layers(per_layer_results, "water_or_channel"),
        "overlap_cell_counts": overlap_cell_counts,
        "overlap_cell_fractions": overlap_cell_fractions,
        "nearest_distances_m": nearest_distances_m,
        "selected_cell_total": selected_cell_total,
        "target_convergence_interpretation": TARGET_CONVERGENCE_INTERPRETATION,
        "validation_output_context": VALIDATION_OUTPUT_CONTEXT,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": None,
        "interpretation_impact": build_interpretation_impact(context_report, per_layer_results),
        "final_classification": final_classification,
        "status": final_classification,
    }


def build_blocked_report(
    *,
    hazard_manifest_path: Path,
    context_metadata_path: Path,
    scope_record_path: Path,
    selected_extent: dict[str, Any],
    context_metadata: dict[str, Any],
    archive_path: Path,
    context_archive_status: str,
    blocked_reason: str,
    target_layer_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "report_schema_version": SCHEMA_VERSION,
        "pilot_id": context_metadata.get("pilot_id", "tschamut_public_pilot"),
        "hazard_manifest_path": str(hazard_manifest_path),
        "context_metadata_path": str(context_metadata_path),
        "scope_record_path": str(scope_record_path),
        "hazard_context_overlap_status": "blocked_missing_inputs",
        "context_archive_status": context_archive_status,
        "context_classification": context_metadata.get("review_classification", "unresolved"),
        "selected_extent_or_corridor": {
            "extent_lv95_m": selected_extent.get("extent_lv95_m", {}),
            "coordinate_reference_system": selected_extent.get("coordinate_reference_system", {}),
        },
        "selected_hazard_layers": [],
        "hazard_mask_criteria": [],
        "context_categories_queried": list(OVERLAP_CONTEXT_CATEGORIES),
        "roads_or_transport_overlap": empty_category_overlap(),
        "barriers_or_protection_overlap": empty_category_overlap(),
        "water_or_channel_overlap": empty_category_overlap(),
        "overlap_cell_counts": {},
        "overlap_cell_fractions": {},
        "nearest_distances_m": {},
        "selected_cell_total": 0,
        "target_convergence_interpretation": TARGET_CONVERGENCE_INTERPRETATION,
        "validation_output_context": VALIDATION_OUTPUT_CONTEXT,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": blocked_reason,
        "interpretation_impact": {
            "summary": "Overlap measurement is blocked until the hazard manifest and context archive can both be queried.",
            "current_effect": "No overlap or proximity claims are made from absent inputs.",
            "target_convergence_interpretation": TARGET_CONVERGENCE_INTERPRETATION,
            "validation_output_context": VALIDATION_OUTPUT_CONTEXT,
            "operational_claims_allowed": False,
        },
        "final_classification": "blocked_missing_inputs",
        "status": "blocked_missing_inputs",
        "missing_inputs": {
            "hazard_manifest_path": str(hazard_manifest_path),
            "context_archive_path": str(archive_path),
            "target_layer_count": len(target_layer_entries),
        },
    }


def build_context_baseline_report(
    context_metadata: dict[str, Any],
    archive_path: Path,
    selected_extent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "classification": context_metadata.get("review_classification", "unresolved"),
        "selected_extent_or_corridor": {
            "extent_lv95_m": selected_extent.get("extent_lv95_m", {}),
            "coordinate_reference_system": selected_extent.get("coordinate_reference_system", {}),
        },
        "archive_path": str(archive_path),
        "archive_sha256": context_metadata.get("local_asset_sha256") or context_metadata.get("raw_asset_sha256"),
        "archive_size_bytes": context_metadata.get("local_asset_bytes") or context_metadata.get("raw_asset_head_content_length_bytes"),
        "coordinate_reference_system": context_metadata.get("coordinate_reference_system"),
        "review_classification": context_metadata.get("review_classification"),
    }


def resolve_context_archive_status(context_metadata: dict[str, Any], archive_path: Path) -> tuple[str, str | None]:
    if not archive_path.exists():
        return "blocked_missing_inputs", f"staged swissTLM3D archive is absent at {archive_path}"
    if not context_metadata.get("staged_asset_present", False):
        return "blocked_missing_inputs", "swissTLM3D metadata does not mark the staged archive as present"
    ogrinfo = shutil.which("ogrinfo")
    if ogrinfo is None:
        return "blocked_tooling_or_missing_dependency", "ogrinfo is unavailable in the current environment"
    return "measured_corridor_relevance", None


def load_selected_extent(scope_record_path: Path, context_metadata_path: Path) -> dict[str, Any]:
    scope = read_yaml(scope_record_path)
    selected = scope.get("selected_domain") or {}
    if not selected:
        selected = read_json(context_metadata_path)
    extent = selected.get("selected_extent_lv95_m") or selected.get("extent_lv95_m") or {}
    crs = selected.get("coordinate_reference_system") or context_metadata_path
    return {
        "extent_lv95_m": extent,
        "coordinate_reference_system": selected.get("coordinate_reference_system")
        or read_json(context_metadata_path).get("coordinate_reference_system"),
    }


def resolve_archive_path(metadata: dict[str, Any], *, root: Path) -> Path:
    for key in ("local_asset_path", "raw_asset_path"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            path = Path(value)
            return path if path.is_absolute() else root / path
    raise HazardContextOverlapError("swissTLM3D metadata is missing an archive path")


def select_layer_entry(layer_lookup: dict[str, dict[str, Any]], requested_layer_name: str) -> tuple[dict[str, Any], str]:
    for candidate in next(
        (candidates for desired, candidates in DEFAULT_SELECTED_LAYER_GROUPS if desired == requested_layer_name),
        (requested_layer_name,),
    ):
        if candidate in layer_lookup:
            return layer_lookup[candidate], candidate
    if requested_layer_name in layer_lookup:
        return layer_lookup[requested_layer_name], requested_layer_name
    raise HazardContextOverlapError(f"hazard layer {requested_layer_name!r} is missing from the manifest")


def select_high_relevance_cells(cells: list[dict[str, Any]], top_cell_count: int) -> list[dict[str, Any]]:
    positive = [cell for cell in cells if cell["value"] > 0]
    positive.sort(key=lambda cell: (-cell["value"], cell["y"], cell["x"]))
    return positive[: max(0, top_cell_count)]


def read_esri_ascii_grid(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6:
        raise HazardContextOverlapError(f"ASCII grid is too short: {path}")
    header = {}
    for line in lines[:6]:
        key, value = line.split(None, 1)
        header[key.lower()] = float(value)
    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cellsize = float(header["cellsize"])
    nodata = float(header.get("nodata_value", -9999.0))
    xll = header.get("xllcorner", header.get("xllcenter"))
    yll = header.get("yllcorner", header.get("yllcenter"))
    if xll is None or yll is None:
        raise HazardContextOverlapError(f"ASCII grid missing lower-left origin: {path}")
    if "xllcenter" in header:
        xll -= cellsize / 2.0
    if "yllcenter" in header:
        yll -= cellsize / 2.0
    rows = lines[6 : 6 + nrows]
    if len(rows) != nrows:
        raise HazardContextOverlapError(f"ASCII grid row count mismatch: {path}")
    cells: list[dict[str, Any]] = []
    max_value = None
    positive_cell_count = 0
    for row_index, row in enumerate(rows):
        values = row.split()
        if len(values) != ncols:
            raise HazardContextOverlapError(f"ASCII grid column count mismatch in row {row_index}: {path}")
        y = yll + (nrows - row_index - 0.5) * cellsize
        for col_index, raw_value in enumerate(values):
            value = float(raw_value)
            if math.isclose(value, nodata):
                continue
            x = xll + (col_index + 0.5) * cellsize
            cells.append(
                {
                    "value": value,
                    "x": x,
                    "y": y,
                    "row_index": row_index,
                    "col_index": col_index,
                }
            )
            if value > 0:
                positive_cell_count += 1
            max_value = value if max_value is None else max(max_value, value)
    extent_lv95_m = {
        "xmin": xll,
        "ymin": yll,
        "xmax": xll + ncols * cellsize,
        "ymax": yll + nrows * cellsize,
    }
    return {
        "cells": cells,
        "cell_size": cellsize,
        "positive_cell_count": positive_cell_count,
        "max_value": max_value,
        "extent_lv95_m": extent_lv95_m,
    }


def query_feature_count(
    *,
    archive_path: Path,
    layer_name: str,
    bbox: dict[str, float],
    member_path: str | None = None,
) -> int:
    ogrinfo = shutil.which("ogrinfo")
    if ogrinfo is None:
        raise HazardContextOverlapError("ogrinfo is unavailable in the current environment")
    datasource_path, layer_arg = build_datasource_path(archive_path, layer_name=layer_name, member_path=member_path)
    cmd = [
        ogrinfo,
        "-ro",
        "-so",
        "-geom=NO",
        "-al",
        "-spat",
        str(bbox["xmin"]),
        str(bbox["ymin"]),
        str(bbox["xmax"]),
        str(bbox["ymax"]),
        datasource_path,
    ]
    if layer_arg is not None:
        cmd.append(layer_arg)
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        raise HazardContextOverlapError(f"ogrinfo timed out for {layer_name}: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        raise HazardContextOverlapError(
            f"ogrinfo failed for {layer_name}: {exc.stderr or exc.stdout or exc}"
        ) from exc
    match = re.search(r"Feature Count:\s*(\d+)", completed.stdout)
    if match is None:
        raise HazardContextOverlapError(f"ogrinfo did not report a feature count for {layer_name}")
    return int(match.group(1))


def build_datasource_path(
    archive_path: Path,
    *,
    layer_name: str,
    member_path: str | None,
) -> tuple[str, str | None]:
    if archive_path.suffix.lower() == ".zip":
        if member_path is None:
            raise HazardContextOverlapError("zip archive queries require a member_path")
        return f"/vsizip/{archive_path}/{SWISSTLM3D_ARCHIVE_MEMBER_ROOT}/{member_path}", None
    return str(archive_path), layer_name


def first_hit_radius_m(
    *,
    archive_path: Path,
    category: str,
    x: float,
    y: float,
    radii_m: list[float] | tuple[float, ...],
    layer_specs: list[dict[str, Any]],
) -> float | None:
    for radius in sorted(set(radii_m)):
        bbox = {"xmin": x - radius, "ymin": y - radius, "xmax": x + radius, "ymax": y + radius}
        total = 0
        for spec in layer_specs:
            total += query_feature_count(
                archive_path=archive_path,
                layer_name=spec["layer_name"],
                member_path=spec.get("member_path"),
                bbox=bbox,
            )
        if total > 0:
            return radius
    return None


def category_overlap_summary(
    counts: dict[str, int],
    fractions: dict[str, float | None],
    nearest_distance_m: float | None,
) -> dict[str, Any]:
    selected_fraction = fractions.get("within_20m_fraction")
    classification = "limiting" if counts.get("within_20m_cell_count", 0) > 0 else "unresolved"
    return {
        "classification": classification,
        "within_10m_cell_count": counts.get("within_10m_cell_count", 0),
        "within_20m_cell_count": counts.get("within_20m_cell_count", 0),
        "within_10m_fraction": fractions.get("within_10m_fraction"),
        "within_20m_fraction": selected_fraction,
        "nearest_distance_m": nearest_distance_m,
    }


def summarize_category_from_layers(per_layer_results: list[dict[str, Any]], category: str) -> dict[str, Any]:
    total_selected = 0
    within_10m = 0
    within_20m = 0
    nearest_distances: list[float] = []
    per_layer: list[dict[str, Any]] = []
    for layer in per_layer_results:
        overlap = layer[f"{category}_overlap"]
        selected = layer["selected_cell_count"]
        total_selected += selected
        within_10m += overlap["within_10m_cell_count"]
        within_20m += overlap["within_20m_cell_count"]
        if overlap["nearest_distance_m"] is not None:
            nearest_distances.append(overlap["nearest_distance_m"])
        per_layer.append(
            {
                "layer_name": layer["layer_name"],
                "selected_cell_count": selected,
                "within_10m_cell_count": overlap["within_10m_cell_count"],
                "within_20m_cell_count": overlap["within_20m_cell_count"],
                "nearest_distance_m": overlap["nearest_distance_m"],
            }
        )
    return {
        "classification": "limiting" if within_20m > 0 else "unresolved",
        "selected_cell_count_total": total_selected,
        "within_10m_cell_count": within_10m,
        "within_20m_cell_count": within_20m,
        "within_10m_fraction": fraction(within_10m, total_selected),
        "within_20m_fraction": fraction(within_20m, total_selected),
        "within_10m_cell_count_total": within_10m,
        "within_20m_cell_count_total": within_20m,
        "within_10m_fraction_total": fraction(within_10m, total_selected),
        "within_20m_fraction_total": fraction(within_20m, total_selected),
        "nearest_distance_m": min(nearest_distances) if nearest_distances else None,
        "per_layer": per_layer,
    }


def determine_final_classification(per_layer_results: list[dict[str, Any]], context_report: dict[str, Any]) -> str:
    if context_report["classification"] == "invalidating":
        return "invalidating"
    if any(layer["roads_or_transport_overlap"]["within_20m_cell_count"] > 0 for layer in per_layer_results):
        return "limiting"
    if any(layer["barriers_or_protection_overlap"]["within_20m_cell_count"] > 0 for layer in per_layer_results):
        return "limiting"
    if any(layer["water_or_channel_overlap"]["within_20m_cell_count"] > 0 for layer in per_layer_results):
        return "limiting"
    return "unresolved"


def build_interpretation_impact(context_report: dict[str, Any], per_layer_results: list[dict[str, Any]]) -> dict[str, Any]:
    summary_bits = []
    for category in OVERLAP_CONTEXT_CATEGORIES:
        summary_bits.append(
            f"{category}: {summarize_category_from_layers(per_layer_results, category)['classification']}"
        )
    return {
        "summary": "Hazard/context overlap is measured as bounded diagnostic evidence only.",
        "current_effect": (
            "Limiting corridor features now have quantitative proximity evidence against the highest-relevance "
            "same-scale hazard cells, but that remains interpretive evidence and not obstacle physics."
        ),
        "context_classification": context_report["classification"],
        "target_convergence_interpretation": TARGET_CONVERGENCE_INTERPRETATION,
        "validation_output_context": VALIDATION_OUTPUT_CONTEXT,
        "category_summary": summary_bits,
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "boundaries": INTERPRETATION_BOUNDARY_NOTE,
    }


def empty_category_overlap() -> dict[str, Any]:
    return {
        "classification": "blocked_missing_inputs",
        "within_10m_cell_count": 0,
        "within_20m_cell_count": 0,
        "within_10m_fraction": None,
        "within_20m_fraction": None,
        "nearest_distance_m": None,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Hazard-Context Overlap",
        "",
        f"- Pilot id: `{report['pilot_id']}`",
        f"- Final classification: `{report['final_classification']}`",
        f"- Hazard-context overlap status: `{report['hazard_context_overlap_status']}`",
        f"- Context archive status: `{report['context_archive_status']}`",
        f"- Target convergence interpretation: `{report['target_convergence_interpretation']}`",
        f"- Validation output context: `{report['validation_output_context']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        "",
        "## Selected Hazard Layers",
    ]
    for item in report["selected_hazard_layers"]:
        lines.append(
            f"- `{item['layer_name']}`: top `{item['selected_cell_count']}` positive cells from `{item['grid_path']}`"
        )
    lines.extend(["", "## Context Categories Queried"])
    lines.extend(f"- `{item}`" for item in report["context_categories_queried"])
    lines.extend(["", "## Overlap"])
    for category in OVERLAP_CONTEXT_CATEGORIES:
        overlap = report[f"{category}_overlap"]
        lines.extend(
            [
                "",
                f"### {category}",
                f"- Classification: `{overlap['classification']}`",
                f"- Within 10 m cell count: `{overlap['within_10m_cell_count']}`",
                f"- Within 20 m cell count: `{overlap['within_20m_cell_count']}`",
                f"- Within 10 m fraction: `{overlap['within_10m_fraction']}`",
                f"- Within 20 m fraction: `{overlap['within_20m_fraction']}`",
                f"- Nearest distance m: `{overlap['nearest_distance_m']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation Impact",
            "",
            f"- {report['interpretation_impact']['summary']}",
            f"- {report['interpretation_impact']['current_effect']}",
            f"- {report['interpretation_impact']['boundaries']}",
            "",
            "## Limitations",
            "",
            "- No obstacle physics are implemented here.",
            "- No operational or annual-frequency claim is implied.",
            "- No absence claim is made from a zero-overlap result.",
        ]
    )
    return "\n".join(lines) + "\n"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise HazardContextOverlapError(f"{label} must be a list")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise HazardContextOverlapError(f"{label} must be a non-empty string")
    return value


def require_existing_path(path: Path, label: str) -> Path:
    if not path.exists():
        raise HazardContextOverlapError(f"{label} is absent at {path}")
    return path


def fraction(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


if __name__ == "__main__":
    raise SystemExit(main())
