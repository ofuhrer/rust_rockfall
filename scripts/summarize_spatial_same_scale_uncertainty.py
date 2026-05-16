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
UNCERTAINTY_LAYER_SCHEMA_VERSION = "spatial_uncertainty_layer_summary_v1"
DEFAULT_HAZARD_LAYERS = (
    "max_kinetic_energy",
    "max_jump_height",
    "velocity_exceedance_5mps",
)
UNCERTAINTY_REGION_KIND_ORDER = (
    "persistent_agreement",
    "support_nodata_sensitive",
    "shared_support_magnitude",
    "persistent_disagreement",
    "closure_limiting_disagreement",
    "deferrable_disagreement",
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
    parser.add_argument("--top-cell-count", "--top-n", dest="top_n", type=int, default=8)
    parser.add_argument(
        "--mask-output-dir",
        type=Path,
        default=None,
        help="optional ignored output directory for compact mask summary artifacts",
    )
    parser.add_argument(
        "--gis-output-dir",
        type=Path,
        default=None,
        help="optional ignored output directory for JSON/CSV/GeoJSON diagnostic uncertainty products",
    )
    args = parser.parse_args(argv)

    report = build_report(
        manifest_paths=args.manifests or list(DEFAULT_MANIFESTS),
        hazard_layers=tuple(args.hazard_layers or DEFAULT_HAZARD_LAYERS),
        top_n=args.top_n,
        mask_output_dir=args.mask_output_dir,
    )

    if args.gis_output_dir is not None and report["spatial_uncertainty_status"] == "measured_existing_artifacts":
        write_uncertainty_layer_products(report, args.gis_output_dir)

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
    mask_output_dir: Path | None = None,
) -> dict[str, Any]:
    manifests = [resolve_manifest(path) for path in manifest_paths]
    selected_layers = normalize_layer_selection(hazard_layers)

    missing_paths = [str(item) for item in collect_missing_paths(manifests, selected_layers)]
    if missing_paths:
        return blocked_report(manifests, selected_layers, missing_paths, reason="required same-scale spatial uncertainty inputs are missing")

    artifacts = [summarize_artifact(manifest) for manifest in manifests]
    mask_output_dir = Path(mask_output_dir) if mask_output_dir is not None else None
    if mask_output_dir is not None:
        mask_output_dir.mkdir(parents=True, exist_ok=True)
    layer_summaries = {
        layer_key: summarize_layer(layer_key, artifacts, top_n=top_n, mask_output_dir=mask_output_dir)
        for layer_key in selected_layers
    }
    dominant_layers = sorted(
        layer_summaries.values(),
        key=lambda item: (item["range_summary"]["mean_range"] or 0.0, item["nodata_disagreement_fraction"]),
        reverse=True,
    )
    uncertainty_layer_summary = build_uncertainty_layer_summary(
        spatial_report={
            "spatial_uncertainty_status": "measured_existing_artifacts",
            "selected_layers": list(selected_layers),
            "layer_summaries": layer_summaries,
            "dominant_layers_by_mean_range": [item["layer_key"] for item in dominant_layers],
            "dominant_layer_summaries": dominant_layers,
            "blocked_reason": "",
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "spatial_uncertainty_status": "measured_existing_artifacts",
        "stability_zone_status": "measured_existing_artifacts",
        "readiness_status": "ready",
        "command_plan_status": "ready",
        "artifacts_measured": artifacts,
        "selected_layers": list(selected_layers),
        "layer_summaries": layer_summaries,
        "dominant_layers_by_mean_range": [item["layer_key"] for item in dominant_layers],
        "dominant_layer_summaries": dominant_layers,
        "uncertainty_layer_summary": uncertainty_layer_summary,
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": "",
        "measurement_command": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
        "spatial_interpretation": spatial_interpretation(dominant_layers),
        "mask_status": "available",
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
        "stability_zone_status": "blocked_missing_inputs",
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
        "mask_status": "blocked_missing_inputs",
        "uncertainty_layer_summary": {
            "schema_version": UNCERTAINTY_LAYER_SCHEMA_VERSION,
            "summary_status": "blocked_missing_inputs",
            "layer_summaries": [],
            "region_products": [],
            "stable_region_status": "blocked_missing_inputs",
            "unstable_region_status": "blocked_missing_inputs",
        },
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
        decomposition = summary.get("disagreement_decomposition") or {}
        if decomposition:
            fractions = decomposition.get("high_uncertainty_fraction_explained") or {}
            lines.append(
                f"  decomposition={decomposition.get('classification')} | "
                f"support/nodata={fractions.get('support_nodata', 0.0):.6g} | "
                f"shared-support magnitude={fractions.get('shared_support_magnitude', 0.0):.6g}"
            )
        mask = summary.get("mask_evidence") or {}
        if mask:
            lines.append(
                f"  mask role={mask.get('closure_role')} status={mask.get('mask_status')} | "
                f"high={mask.get('high_uncertainty_cell_count')} "
                f"support/nodata={mask.get('support_nodata_cell_count')} "
                f"shared-support={mask.get('shared_support_magnitude_cell_count')}"
            )
        stability = summary.get("stability_zone_summary") or {}
        if stability:
            zone_counts = stability.get("zone_counts") or {}
            zone_fractions = stability.get("zone_fractions") or {}
            lines.append(
                f"  stability zone={stability.get('layer_stability_zone_class')} "
                f"dominant={stability.get('dominant_zone_category')} "
                f"high-uncertainty={stability.get('dominant_high_uncertainty_zone_category')}"
            )
            lines.append(
                "  zones: "
                f"support/nodata_sensitive={zone_counts.get('support_nodata_sensitive', 0)} "
                f"({zone_fractions.get('support_nodata_sensitive', 0.0):.6g}), "
                f"shared_support_magnitude={zone_counts.get('shared_support_magnitude', 0)} "
                f"({zone_fractions.get('shared_support_magnitude', 0.0):.6g}), "
                f"persistent_agreement={zone_counts.get('persistent_agreement', 0)} "
                f"({zone_fractions.get('persistent_agreement', 0.0):.6g})"
            )
        if summary["high_uncertainty_bbox"] is not None:
            bbox = summary["high_uncertainty_bbox"]
            lines.append(
                "  high-uncertainty bbox: "
                f"rows {bbox['row_min']}..{bbox['row_max']}, cols {bbox['col_min']}..{bbox['col_max']}, "
                f"LV95 x {bbox['xmin']:.2f}..{bbox['xmax']:.2f}, y {bbox['ymin']:.2f}..{bbox['ymax']:.2f}"
            )
        if mask and mask.get("mask_bbox") is not None:
            bbox = mask["mask_bbox"]
            lines.append(
                "  mask bbox: "
                f"rows {bbox['row_min']}..{bbox['row_max']}, cols {bbox['col_min']}..{bbox['col_max']}, "
                f"LV95 x {bbox['xmin']:.2f}..{bbox['xmax']:.2f}, y {bbox['ymin']:.2f}..{bbox['ymax']:.2f}"
            )
        if mask and mask.get("mask_path"):
            lines.append(f"  mask path: {mask['mask_path']}")
        lines.append(f"  top cells: {len(summary['top_high_uncertainty_cells'])}")
    uncertainty_layer_summary = report.get("uncertainty_layer_summary") or {}
    if uncertainty_layer_summary:
        lines.append(
            "uncertainty layer summary: "
            f"{uncertainty_layer_summary.get('summary_status')} | "
            f"stable={uncertainty_layer_summary.get('stable_region_status')} | "
            f"unstable={uncertainty_layer_summary.get('unstable_region_status')}"
        )
        for layer in uncertainty_layer_summary.get("layer_summaries", []):
            lines.append(
                f"- {layer['layer_key']}: confidence={layer['confidence_class']} | "
                f"uncertainty={layer['uncertainty_concentration_class']} | "
                f"stable={layer['stable_region']['cell_count']} | "
                f"unstable={layer['unstable_region']['cell_count']}"
            )
    return "\n".join(lines)


def build_uncertainty_layer_summary(spatial_report: dict[str, Any]) -> dict[str, Any]:
    if spatial_report.get("spatial_uncertainty_status") != "measured_existing_artifacts":
        return {
            "schema_version": UNCERTAINTY_LAYER_SCHEMA_VERSION,
            "summary_status": spatial_report.get("spatial_uncertainty_status", "blocked_missing_inputs"),
            "layer_summaries": [],
            "region_products": [],
            "stable_region_status": "blocked_missing_inputs",
            "unstable_region_status": "blocked_missing_inputs",
            "blocked_reason": spatial_report.get("blocked_reason", ""),
        }

    layer_summaries: list[dict[str, Any]] = []
    region_products: list[dict[str, Any]] = []
    total_stable_cells = 0
    total_unstable_cells = 0
    for layer_key in spatial_report.get("selected_layers", []):
        layer = dict((spatial_report.get("layer_summaries") or {}).get(layer_key) or {})
        stability = dict(layer.get("stability_zone_summary") or {})
        layer_summary = summarize_uncertainty_layer(layer_key, layer, stability)
        layer_summaries.append(layer_summary)
        region_products.extend(layer_summary["region_products"])
        total_stable_cells += int(layer_summary["stable_region"]["cell_count"])
        total_unstable_cells += int(layer_summary["unstable_region"]["cell_count"])

    layer_summaries.sort(key=lambda item: item["layer_key"])
    region_products.sort(
        key=lambda item: (
            item["layer_key"],
            UNCERTAINTY_REGION_KIND_ORDER.index(item["region_kind"]) if item["region_kind"] in UNCERTAINTY_REGION_KIND_ORDER else 99,
        )
    )
    return {
        "schema_version": UNCERTAINTY_LAYER_SCHEMA_VERSION,
        "summary_status": spatial_report.get("spatial_uncertainty_status"),
        "layer_summaries": layer_summaries,
        "region_products": region_products,
        "stable_region_status": "measured_existing_artifacts" if total_stable_cells >= 0 else "blocked_missing_inputs",
        "unstable_region_status": "measured_existing_artifacts" if total_unstable_cells >= 0 else "blocked_missing_inputs",
        "stable_region_cell_count": total_stable_cells,
        "unstable_region_cell_count": total_unstable_cells,
        "blocked_reason": spatial_report.get("blocked_reason", ""),
    }


def summarize_uncertainty_layer(layer_key: str, layer: dict[str, Any], stability: dict[str, Any]) -> dict[str, Any]:
    zone_counts = dict(stability.get("zone_counts") or {})
    zone_fractions = dict(stability.get("zone_fractions") or {})
    zone_bboxes = dict(stability.get("zone_bboxes") or {})
    high_uncertainty_zone_counts = dict(stability.get("high_uncertainty_zone_counts") or {})
    high_uncertainty_zone_fractions = dict(stability.get("high_uncertainty_zone_fractions") or {})
    closure_role = str(layer.get("closure_role") or "unresolved")
    confidence_class = derive_confidence_class(layer_key, layer, stability)

    persistent_agreement = summarize_region(
        layer_key=layer_key,
        region_kind="persistent_agreement",
        confidence_class=confidence_class,
        closure_role=closure_role,
        cell_count=int(zone_counts.get("persistent_agreement", 0) or 0),
        cell_fraction=float(zone_fractions.get("persistent_agreement", 0.0) or 0.0),
        bbox=zone_bboxes.get("persistent_agreement"),
    )
    support_nodata_sensitive = summarize_region(
        layer_key=layer_key,
        region_kind="support_nodata_sensitive",
        confidence_class=confidence_class,
        closure_role=closure_role,
        cell_count=int(zone_counts.get("support_nodata_sensitive", 0) or 0),
        cell_fraction=float(zone_fractions.get("support_nodata_sensitive", 0.0) or 0.0),
        bbox=zone_bboxes.get("support_nodata_sensitive"),
    )
    shared_support_magnitude = summarize_region(
        layer_key=layer_key,
        region_kind="shared_support_magnitude",
        confidence_class=confidence_class,
        closure_role=closure_role,
        cell_count=int(zone_counts.get("shared_support_magnitude", 0) or 0),
        cell_fraction=float(zone_fractions.get("shared_support_magnitude", 0.0) or 0.0),
        bbox=zone_bboxes.get("shared_support_magnitude"),
    )
    persistent_disagreement = summarize_region(
        layer_key=layer_key,
        region_kind="persistent_disagreement",
        confidence_class=confidence_class,
        closure_role=closure_role,
        cell_count=int(zone_counts.get("support_nodata_sensitive", 0) or 0) + int(zone_counts.get("shared_support_magnitude", 0) or 0),
        cell_fraction=float(zone_fractions.get("support_nodata_sensitive", 0.0) or 0.0)
        + float(zone_fractions.get("shared_support_magnitude", 0.0) or 0.0),
        bbox=merge_bboxes(zone_bboxes.get("support_nodata_sensitive"), zone_bboxes.get("shared_support_magnitude")),
    )
    umbrella_kind = "closure_limiting_disagreement" if closure_role == "closure_limiting" else "deferrable_disagreement" if closure_role == "deferrable" else "persistent_disagreement"
    umbrella_region = summarize_region(
        layer_key=layer_key,
        region_kind=umbrella_kind,
        confidence_class=confidence_class,
        closure_role=closure_role,
        cell_count=persistent_disagreement["cell_count"],
        cell_fraction=persistent_disagreement["cell_fraction"],
        bbox=persistent_disagreement["bbox"],
    )
    stable_vs_unstable_fraction = {
        "stable_fraction": persistent_agreement["cell_fraction"],
        "unstable_fraction": persistent_disagreement["cell_fraction"],
        "stable_cell_count": persistent_agreement["cell_count"],
        "unstable_cell_count": persistent_disagreement["cell_count"],
    }
    return {
        "layer_key": layer_key,
        "closure_role": closure_role,
        "confidence_class": confidence_class,
        "uncertainty_concentration_class": layer.get("uncertainty_concentration_class"),
        "stability_zone_class": layer.get("stability_zone_class"),
        "dominant_zone_category": layer.get("stability_zone_dominant_category"),
        "dominant_high_uncertainty_zone_category": layer.get("stability_zone_dominant_high_uncertainty_category"),
        "zone_counts": zone_counts,
        "zone_fractions": zone_fractions,
        "high_uncertainty_zone_counts": high_uncertainty_zone_counts,
        "high_uncertainty_zone_fractions": high_uncertainty_zone_fractions,
        "stable_region": persistent_agreement,
        "unstable_region": persistent_disagreement,
        "umbrella_region": umbrella_region,
        "region_products": [
            persistent_agreement,
            support_nodata_sensitive,
            shared_support_magnitude,
            persistent_disagreement,
            umbrella_region,
        ],
        "stable_vs_unstable": stable_vs_unstable_fraction,
        "stable_region_status": "measured_existing_artifacts",
        "unstable_region_status": "measured_existing_artifacts",
    }


def derive_confidence_class(layer_key: str, layer: dict[str, Any], stability: dict[str, Any]) -> str:
    stability_zone_class = str(stability.get("layer_stability_zone_class") or layer.get("stability_zone_class") or "mixed_stability_zone")
    if stability_zone_class == "persistent_closure_limiting":
        return "closure_limiting_disagreement"
    if stability_zone_class == "deferrable_localized":
        return "deferrable_disagreement"
    if stability_zone_class == "stable_low_disagreement":
        return "stable_low_disagreement"
    if layer_key == "velocity_exceedance_5mps" and layer.get("closure_role") == "deferrable":
        return "deferrable_disagreement"
    return "mixed_stability_zone"


def summarize_region(
    *,
    layer_key: str,
    region_kind: str,
    confidence_class: str,
    closure_role: str,
    cell_count: int,
    cell_fraction: float,
    bbox: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "layer_key": layer_key,
        "region_kind": region_kind,
        "confidence_class": confidence_class,
        "closure_role": closure_role,
        "cell_count": cell_count,
        "cell_fraction": cell_fraction,
        "bbox": bbox,
        "geometry": bbox_to_polygon(bbox) if bbox is not None else None,
        "region_status": "measured_existing_artifacts",
    }


def merge_bboxes(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any] | None:
    if left is None:
        return right
    if right is None:
        return left
    return {
        "row_min": min(int(left["row_min"]), int(right["row_min"])),
        "row_max": max(int(left["row_max"]), int(right["row_max"])),
        "col_min": min(int(left["col_min"]), int(right["col_min"])),
        "col_max": max(int(left["col_max"]), int(right["col_max"])),
        "xmin": min(float(left["xmin"]), float(right["xmin"])),
        "xmax": max(float(left["xmax"]), float(right["xmax"])),
        "ymin": min(float(left["ymin"]), float(right["ymin"])),
        "ymax": max(float(left["ymax"]), float(right["ymax"])),
    }


def bbox_to_polygon(bbox: dict[str, Any] | None) -> dict[str, Any] | None:
    if bbox is None:
        return None
    xmin = float(bbox["xmin"])
    xmax = float(bbox["xmax"])
    ymin = float(bbox["ymin"])
    ymax = float(bbox["ymax"])
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [xmin, ymin],
                [xmin, ymax],
                [xmax, ymax],
                [xmax, ymin],
                [xmin, ymin],
            ]
        ],
    }


def write_uncertainty_layer_products(report: dict[str, Any], output_dir: Path) -> list[Path]:
    summary = report.get("uncertainty_layer_summary") or build_uncertainty_layer_summary(report)
    if summary.get("summary_status") != "measured_existing_artifacts":
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    summary_path = output_dir / "spatial_uncertainty_layer_summary.json"
    summary_payload = {
        **summary,
        "region_products": [region_product_for_serialization(region) for region in summary.get("region_products", [])],
        "layer_summaries": [
            {
                **layer_summary,
                "region_products": [region_product_for_serialization(region) for region in layer_summary.get("region_products", [])],
            }
            for layer_summary in summary.get("layer_summaries", [])
        ],
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written_paths.append(summary_path)

    csv_path = output_dir / "spatial_uncertainty_region_products.csv"
    csv_lines = ["layer_key,region_kind,confidence_class,closure_role,cell_count,cell_fraction,xmin,ymin,xmax,ymax"]
    for region in summary.get("region_products", []):
        bbox = region.get("bbox") or {}
        csv_lines.append(
            ",".join(
                [
                    csv_escape(region.get("layer_key")),
                    csv_escape(region.get("region_kind")),
                    csv_escape(region.get("confidence_class")),
                    csv_escape(region.get("closure_role")),
                    str(region.get("cell_count")),
                    format_float(region.get("cell_fraction")),
                    format_float(bbox.get("xmin")),
                    format_float(bbox.get("ymin")),
                    format_float(bbox.get("xmax")),
                    format_float(bbox.get("ymax")),
                ]
            )
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
    written_paths.append(csv_path)

    geojson_path = output_dir / "spatial_uncertainty_region_products.geojson"
    geojson_features = [region_feature(region) for region in summary.get("region_products", [])]
    geojson_payload = {
        "type": "FeatureCollection",
        "schema_version": UNCERTAINTY_LAYER_SCHEMA_VERSION,
        "features": geojson_features,
    }
    geojson_path.write_text(json.dumps(geojson_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written_paths.append(geojson_path)
    return written_paths


def region_product_for_serialization(region: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer_key": region.get("layer_key"),
        "region_kind": region.get("region_kind"),
        "confidence_class": region.get("confidence_class"),
        "closure_role": region.get("closure_role"),
        "cell_count": region.get("cell_count"),
        "cell_fraction": region.get("cell_fraction"),
        "bbox": region.get("bbox"),
        "region_status": region.get("region_status"),
    }


def region_feature(region: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": region.get("geometry"),
        "properties": region_product_for_serialization(region),
    }


def csv_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    if any(character in text for character in (",", "\"", "\n", "\r")):
        return "\"" + text.replace("\"", "\"\"") + "\""
    return text


def format_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.12g}"


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


def summarize_layer(
    layer_key: str,
    artifacts: list[dict[str, Any]],
    *,
    top_n: int,
    mask_output_dir: Path | None = None,
) -> dict[str, Any]:
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
    support_nodata_cells: list[dict[str, Any]] = []
    shared_support_magnitude_cells: list[dict[str, Any]] = []
    support_nodata_sensitive_cells: list[dict[str, Any]] = []

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

    support_nodata_sensitive_cells = [
        cell
        for cell in cells
        if (any(cell["valid_flags"]) and not all(cell["valid_flags"]))
        or (all(cell["valid_flags"]) and len(set(cell["support_flags"])) > 1)
    ]
    support_only_disagreement_cells = [
        cell for cell in cells if all(cell["valid_flags"]) and len(set(cell["support_flags"])) > 1
    ]
    magnitude_only_disagreement_cells = [
        cell
        for cell in cells
        if all(cell["valid_flags"]) and all(cell["support_flags"]) and cell["range"] is not None and cell["range"] > 0
    ]
    stable_shared_support_cells = [
        cell
        for cell in cells
        if all(cell["valid_flags"]) and len(set(cell["support_flags"])) <= 1 and all(cell["support_flags"]) and (cell["range"] is None or cell["range"] == 0)
    ]
    support_nodata_disagreement_count = nodata_disagreement_count + len(support_only_disagreement_cells)

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

    high_uncertainty_support_nodata_count = sum(
        1
        for cell in high_uncertainty
        if (not all(cell["valid_flags"])) or (all(cell["valid_flags"]) and len(set(cell["support_flags"])) > 1)
    )
    high_uncertainty_magnitude_only_count = sum(
        1
        for cell in high_uncertainty
        if all(cell["valid_flags"]) and all(cell["support_flags"]) and cell["range"] is not None and cell["range"] > 0
    )
    decomposition_class = classify_decomposition(
        nodata_count=nodata_disagreement_count,
        support_only_count=len(support_only_disagreement_cells),
        magnitude_only_count=len(magnitude_only_disagreement_cells),
        shared_valid_count=shared_valid_count,
    )
    shared_support_magnitude_ranges = [float(cell["range"]) for cell in magnitude_only_disagreement_cells if cell["range"] is not None]
    shared_support_magnitude_range_summary = {
        "max_range": max(shared_support_magnitude_ranges) if shared_support_magnitude_ranges else 0.0,
        "mean_range": mean(shared_support_magnitude_ranges) if shared_support_magnitude_ranges else 0.0,
        "p50_range": percentile(shared_support_magnitude_ranges, 0.50) if shared_support_magnitude_ranges else 0.0,
        "p90_range": percentile(shared_support_magnitude_ranges, 0.90) if shared_support_magnitude_ranges else 0.0,
        "p95_range": percentile(shared_support_magnitude_ranges, 0.95) if shared_support_magnitude_ranges else 0.0,
    }

    support_nodata_cells = [cell for cell in cells if any(cell["valid_flags"]) and not all(cell["valid_flags"])]
    shared_support_magnitude_cells = [
        cell for cell in cells if cell["range"] is not None and cell["range"] >= range_threshold
    ]
    interpretation = classify_layer(
        layer_key,
        nodata_disagreement_count=nodata_disagreement_count,
        any_valid_count=any_valid_count,
        shared_valid_count=shared_valid_count,
        nonzero_union_count=nonzero_union_count,
        nonzero_intersection_count=nonzero_intersection_count,
        high_uncertainty_bbox=bbox_for_cells(high_uncertainty, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        analysis_cell_count=analysis_cell_count,
        high_uncertainty_count=len(high_uncertainty),
    )

    bbox = bbox_for_cells(high_uncertainty, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
    centroid = centroid_for_cells(high_uncertainty, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
    stability_zone_summary = summarize_stability_zones(
        layer_key=layer_key,
        cells=cells,
        support_nodata_sensitive_cells=support_nodata_sensitive_cells,
        shared_support_magnitude_cells=magnitude_only_disagreement_cells,
        persistent_agreement_cells=stable_shared_support_cells,
        any_valid_count=any_valid_count,
        analysis_cell_count=analysis_cell_count,
        high_uncertainty_cells=high_uncertainty,
        nrows=nrows,
        cellsize=cellsize,
        xllcorner=xllcorner,
        yllcorner=yllcorner,
        closure_role=mask_closure_role(layer_key, interpretation["uncertainty_concentration_class"]),
    )
    mask_cells = dedupe_cells(high_uncertainty + support_nodata_cells + shared_support_magnitude_cells)
    mask_bbox = bbox_for_cells(mask_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
    mask_path = None
    if mask_output_dir is not None:
        mask_path = write_mask_summary(
            output_dir=mask_output_dir,
            layer_key=layer_key,
            layer_grids=layer_grids,
            nrows=nrows,
            cellsize=cellsize,
            xllcorner=xllcorner,
            yllcorner=yllcorner,
            high_uncertainty_cells=high_uncertainty,
            support_nodata_cells=support_nodata_cells,
            shared_support_magnitude_cells=shared_support_magnitude_cells,
            mask_cells=mask_cells,
            range_threshold=range_threshold,
            interpretation=interpretation,
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
        "support_only_disagreement_count": len(support_only_disagreement_cells),
        "nodata_only_disagreement_count": nodata_disagreement_count,
        "support_nodata_disagreement_count": support_nodata_disagreement_count,
        "magnitude_only_disagreement_count": len(magnitude_only_disagreement_cells),
        "stable_shared_support_count": len(stable_shared_support_cells),
        "nodata_disagreement_fraction": nodata_disagreement_count / any_valid_count if any_valid_count else 0.0,
        "support_only_disagreement_fraction": len(support_only_disagreement_cells) / any_valid_count if any_valid_count else 0.0,
        "magnitude_only_disagreement_fraction": len(magnitude_only_disagreement_cells) / any_valid_count if any_valid_count else 0.0,
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
        "high_uncertainty_support_nodata_fraction": high_uncertainty_support_nodata_count / len(high_uncertainty) if high_uncertainty else 0.0,
        "high_uncertainty_shared_support_magnitude_fraction": high_uncertainty_magnitude_only_count / len(high_uncertainty) if high_uncertainty else 0.0,
        "high_uncertainty_bbox": bbox,
        "high_uncertainty_centroid": centroid,
        "shared_support_magnitude_range_summary": shared_support_magnitude_range_summary,
        "disagreement_decomposition": {
            "classification": decomposition_class,
            "cell_counts": {
                "any_valid_cell_count": any_valid_count,
                "shared_valid_cell_count": shared_valid_count,
                "nodata_disagreement_count": nodata_disagreement_count,
                "support_only_disagreement_count": len(support_only_disagreement_cells),
                "support_nodata_disagreement_count": support_nodata_disagreement_count,
                "magnitude_only_disagreement_count": len(magnitude_only_disagreement_cells),
                "stable_shared_support_count": len(stable_shared_support_cells),
            },
            "high_uncertainty_fraction_explained": {
                "support_nodata": high_uncertainty_support_nodata_count / len(high_uncertainty) if high_uncertainty else 0.0,
                "shared_support_magnitude": high_uncertainty_magnitude_only_count / len(high_uncertainty) if high_uncertainty else 0.0,
            },
            "shared_support_magnitude_range_summary": shared_support_magnitude_range_summary,
            "interpretation_note": decomposition_note(
                layer_key=layer_key,
                classification=decomposition_class,
                support_nodata_count=support_nodata_disagreement_count,
                magnitude_only_count=len(magnitude_only_disagreement_cells),
                high_uncertainty_support_nodata_count=high_uncertainty_support_nodata_count,
                high_uncertainty_magnitude_only_count=high_uncertainty_magnitude_only_count,
            ),
        },
        "top_high_uncertainty_cells": [
            format_high_uncertainty_cell(cell, layer_grids, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
            for cell in high_uncertainty
        ],
        "stability_zone_summary": stability_zone_summary,
        "mask_evidence": build_mask_evidence(
            layer_key=layer_key,
            layer_grids=layer_grids,
            mask_status="available",
            closure_role=mask_closure_role(layer_key, interpretation["uncertainty_concentration_class"]),
            nrows=nrows,
            cellsize=cellsize,
            xllcorner=xllcorner,
            yllcorner=yllcorner,
            high_uncertainty_cells=high_uncertainty,
            support_nodata_cells=support_nodata_cells,
            shared_support_magnitude_cells=shared_support_magnitude_cells,
            mask_cells=mask_cells,
            mask_bbox=mask_bbox,
            mask_path=mask_path,
            range_threshold=range_threshold,
        ),
        "uncertainty_concentration_class": interpretation["uncertainty_concentration_class"],
        "interpretation_note": interpretation["interpretation_note"],
    }


def summarize_stability_zones(
    *,
    layer_key: str,
    cells: list[dict[str, Any]],
    support_nodata_sensitive_cells: list[dict[str, Any]],
    shared_support_magnitude_cells: list[dict[str, Any]],
    persistent_agreement_cells: list[dict[str, Any]],
    any_valid_count: int,
    analysis_cell_count: int,
    high_uncertainty_cells: list[dict[str, Any]],
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
    closure_role: str,
) -> dict[str, Any]:
    zone_cells = {
        "support_nodata_sensitive": support_nodata_sensitive_cells,
        "shared_support_magnitude": shared_support_magnitude_cells,
        "persistent_agreement": persistent_agreement_cells,
    }
    zone_counts = {key: len(value) for key, value in zone_cells.items()}
    dominant_zone_category = max(
        zone_counts,
        key=lambda key: (zone_counts[key], -zone_zone_priority(key)),
    ) if zone_counts else "unknown"
    if closure_role == "closure_limiting":
        layer_stability_zone_class = "persistent_closure_limiting"
    elif closure_role == "deferrable":
        layer_stability_zone_class = "deferrable_localized"
    elif dominant_zone_category == "persistent_agreement":
        layer_stability_zone_class = "stable_low_disagreement"
    elif dominant_zone_category in {"support_nodata_sensitive", "shared_support_magnitude"}:
        layer_stability_zone_class = dominant_zone_category
    else:
        layer_stability_zone_class = "mixed_stability_zone"

    high_uncertainty_zone_cells = {
        "support_nodata_sensitive": [
            cell
            for cell in high_uncertainty_cells
            if (not all(cell["valid_flags"])) or (all(cell["valid_flags"]) and len(set(cell["support_flags"])) > 1)
        ],
        "shared_support_magnitude": [
            cell
            for cell in high_uncertainty_cells
            if all(cell["valid_flags"]) and all(cell["support_flags"]) and cell["range"] is not None and cell["range"] > 0
        ],
        "persistent_agreement": [
            cell
            for cell in high_uncertainty_cells
            if all(cell["valid_flags"]) and all(cell["support_flags"]) and (cell["range"] is None or cell["range"] == 0)
        ],
    }
    zone_bboxes = {key: bbox_for_cells(value, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner) for key, value in zone_cells.items()}
    high_uncertainty_zone_bboxes = {
        key: bbox_for_cells(value, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
        for key, value in high_uncertainty_zone_cells.items()
    }

    zone_fractions = {
        key: (len(value) / any_valid_count if any_valid_count else 0.0)
        for key, value in zone_cells.items()
    }
    high_uncertainty_zone_fractions = {
        key: (len(value) / len(high_uncertainty_cells) if high_uncertainty_cells else 0.0)
        for key, value in high_uncertainty_zone_cells.items()
    }
    dominant_high_uncertainty_zone_category = max(
        high_uncertainty_zone_cells,
        key=lambda key: (len(high_uncertainty_zone_cells[key]), -zone_zone_priority(key)),
    ) if high_uncertainty_zone_cells else "unknown"
    return {
        "zone_status": "available",
        "layer_key": layer_key,
        "closure_role": closure_role,
        "layer_stability_zone_class": layer_stability_zone_class,
        "dominant_zone_category": dominant_zone_category,
        "dominant_high_uncertainty_zone_category": dominant_high_uncertainty_zone_category,
        "closure_role_impact": "no_change",
        "analysis_cell_count": analysis_cell_count,
        "evaluated_cell_count": any_valid_count,
        "all_nodata_cell_count": analysis_cell_count - any_valid_count,
        "all_nodata_fraction_of_analysis": (analysis_cell_count - any_valid_count) / analysis_cell_count if analysis_cell_count else 0.0,
        "zone_counts": zone_counts,
        "zone_fractions": zone_fractions,
        "zone_bboxes": zone_bboxes,
        "high_uncertainty_zone_counts": {key: len(value) for key, value in high_uncertainty_zone_cells.items()},
        "high_uncertainty_zone_fractions": high_uncertainty_zone_fractions,
        "high_uncertainty_zone_bboxes": high_uncertainty_zone_bboxes,
        "high_uncertainty_bbox": bbox_for_cells(high_uncertainty_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        "high_uncertainty_cell_count": len(high_uncertainty_cells),
        "high_uncertainty_cell_fraction": len(high_uncertainty_cells) / any_valid_count if any_valid_count else 0.0,
        "high_uncertainty_shared_support_magnitude_fraction": high_uncertainty_zone_fractions["shared_support_magnitude"],
        "high_uncertainty_support_nodata_fraction": high_uncertainty_zone_fractions["support_nodata_sensitive"],
        "interpretation_note": (
            f"{layer_key} stability zones: {layer_stability_zone_class}; "
            f"dominant={dominant_zone_category}; high-uncertainty={dominant_high_uncertainty_zone_category}"
        ),
    }


def zone_zone_priority(zone_key: str) -> int:
    priorities = {
        "support_nodata_sensitive": 0,
        "shared_support_magnitude": 1,
        "persistent_agreement": 2,
    }
    return priorities.get(zone_key, 99)


def build_mask_evidence(
    *,
    layer_key: str,
    layer_grids: list[LayerGrid],
    mask_status: str,
    closure_role: str,
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
    high_uncertainty_cells: list[dict[str, Any]],
    support_nodata_cells: list[dict[str, Any]],
    shared_support_magnitude_cells: list[dict[str, Any]],
    mask_cells: list[dict[str, Any]],
    mask_bbox: dict[str, Any] | None,
    mask_path: str | None,
    range_threshold: float,
) -> dict[str, Any]:
    return {
        "mask_status": mask_status,
        "closure_role": closure_role,
        "high_uncertainty_cell_count": len(high_uncertainty_cells),
        "support_nodata_cell_count": len(support_nodata_cells),
        "shared_support_magnitude_cell_count": len(shared_support_magnitude_cells),
        "high_uncertainty_bbox": bbox_for_cells(high_uncertainty_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        "support_nodata_bbox": bbox_for_cells(support_nodata_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        "shared_support_magnitude_bbox": bbox_for_cells(shared_support_magnitude_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        "mask_bbox": mask_bbox,
        "mask_path": mask_path,
        "mask_cell_count": len(mask_cells),
        "mask_selection_threshold": range_threshold,
    }


def mask_closure_role(layer_key: str, concentration_class: str) -> str:
    if concentration_class == "dominated_by_nodata_support_differences":
        return "closure_limiting"
    if concentration_class == "spatially_localized_shared_support_magnitude":
        return "deferrable" if layer_key == "velocity_exceedance_5mps" else "closure_limiting"
    if concentration_class in {"shared_support_magnitude_diffuse", "diffuse_across_shared_support"}:
        return "unresolved"
    return "unresolved"


def dedupe_cells(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    deduped: list[dict[str, Any]] = []
    for cell in sorted(cells, key=lambda cell: (cell["row"], cell["col"], -(cell["range"] if cell["range"] is not None else -1.0))):
        key = (cell["row"], cell["col"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cell)
    return deduped


def write_mask_summary(
    *,
    output_dir: Path,
    layer_key: str,
    layer_grids: list[LayerGrid],
    nrows: int,
    cellsize: float,
    xllcorner: float,
    yllcorner: float,
    high_uncertainty_cells: list[dict[str, Any]],
    support_nodata_cells: list[dict[str, Any]],
    shared_support_magnitude_cells: list[dict[str, Any]],
    mask_cells: list[dict[str, Any]],
    range_threshold: float,
    interpretation: dict[str, str] | None,
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{layer_key}_mask_summary.json"
    preview_limit = 25
    preview_high_uncertainty = high_uncertainty_cells[:preview_limit]
    preview_support_nodata = support_nodata_cells[:preview_limit]
    preview_shared_support_magnitude = sorted(
        shared_support_magnitude_cells,
        key=lambda cell: (-float(cell["range"] if cell["range"] is not None else -1.0), cell["row"], cell["col"]),
    )[:preview_limit]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "layer_key": layer_key,
        "artifact_ids": [layer.artifact_id for layer in layer_grids],
        "mask_status": "available",
        "closure_role": mask_closure_role(layer_key, (interpretation or {}).get("uncertainty_concentration_class", "")),
        "mask_selection_threshold": range_threshold,
        "mask_bbox": bbox_for_cells(mask_cells, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner),
        "preview_cell_count": preview_limit,
        "high_uncertainty_cells": [
            format_high_uncertainty_cell(cell, layer_grids, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
            for cell in preview_high_uncertainty
        ],
        "support_nodata_cells": [
            format_high_uncertainty_cell(cell, layer_grids, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
            for cell in preview_support_nodata
        ],
        "shared_support_magnitude_cells": [
            format_high_uncertainty_cell(cell, layer_grids, nrows=nrows, cellsize=cellsize, xllcorner=xllcorner, yllcorner=yllcorner)
            for cell in preview_shared_support_magnitude
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


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


def classify_decomposition(
    *,
    nodata_count: int,
    support_only_count: int,
    magnitude_only_count: int,
    shared_valid_count: int,
) -> str:
    support_nodata_count = nodata_count + support_only_count
    if support_nodata_count == 0 and magnitude_only_count == 0:
        return "mixed_support_and_magnitude"
    if support_nodata_count == 0:
        return "shared_support_magnitude_dominated"
    if magnitude_only_count == 0:
        return "support_nodata_dominated"

    support_fraction = support_nodata_count / shared_valid_count if shared_valid_count else 0.0
    magnitude_fraction = magnitude_only_count / shared_valid_count if shared_valid_count else 0.0
    if support_fraction >= max(0.15, magnitude_fraction * 1.5):
        return "support_nodata_dominated"
    if magnitude_fraction >= max(0.15, support_fraction * 1.5):
        return "shared_support_magnitude_dominated"
    return "mixed_support_and_magnitude"


def decomposition_note(
    *,
    layer_key: str,
    classification: str,
    support_nodata_count: int,
    magnitude_only_count: int,
    high_uncertainty_support_nodata_count: int,
    high_uncertainty_magnitude_only_count: int,
) -> str:
    return (
        f"{layer_key} decomposition={classification} "
        f"(support/nodata={support_nodata_count}, magnitude-only={magnitude_only_count}, "
        f"high-support/nodata={high_uncertainty_support_nodata_count}, "
        f"high-magnitude-only={high_uncertainty_magnitude_only_count})"
    )


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
