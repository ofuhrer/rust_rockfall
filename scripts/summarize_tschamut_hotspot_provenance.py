#!/usr/bin/env python3
"""Summarize hotspot provenance evidence for the Tschamut same-scale runs.

This helper is read-only. It maps the selected high-uncertainty cells from the
same-scale uncertainty summary onto the committed source-zone metadata,
scenario rows, trajectory/deposition evidence, and artifact roots without
running new simulations or treating the result as operational evidence.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_hotspot_provenance_v1"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_TRAJECTORY_METADATA = (
    ROOT / "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory_metadata.csv"
)
DEFAULT_DEPOSITION = ROOT / "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise HotspotProvenanceError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


SPATIAL = _load_module("tschamut_hotspot_provenance_spatial", "summarize_spatial_same_scale_uncertainty.py")
CLOSURE_GAP = _load_module("tschamut_hotspot_provenance_closure_gap", "summarize_tschamut_closure_gap_deltas.py")


class HotspotProvenanceError(ValueError):
    """User-facing hotspot provenance error."""


@dataclass(frozen=True)
class ProvenanceInputPaths:
    source_zone_metadata: Path
    scenario_table: Path
    trajectory_metadata: Path
    deposition: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except HotspotProvenanceError as exc:
        print(f"tschamut hotspot provenance error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["hotspot_provenance_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise HotspotProvenanceError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise HotspotProvenanceError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    spatial_report = build_spatial_report(evidence_override)
    closure_gap_report = build_closure_gap_report(evidence_override)
    provenance_paths = resolve_provenance_paths(evidence_override)

    source_zone = load_yaml(provenance_paths.source_zone_metadata)
    scenario_rows = load_csv_rows(provenance_paths.scenario_table)
    trajectory_rows = load_csv_rows(provenance_paths.trajectory_metadata)
    deposition_rows = load_csv_rows(provenance_paths.deposition)

    source_zone_summary = summarize_source_zone(source_zone, provenance_paths.source_zone_metadata)
    scenario_summary = summarize_scenario_table(scenario_rows, provenance_paths.scenario_table)
    trajectory_deposition_summary = summarize_trajectory_deposition(
        trajectory_rows=trajectory_rows,
        deposition_rows=deposition_rows,
        trajectory_metadata_path=provenance_paths.trajectory_metadata,
        deposition_path=provenance_paths.deposition,
    )

    artifact_roots = summarize_artifact_roots(spatial_report, provenance_paths)
    layer_summaries = build_layer_provenance_summaries(
        spatial_report=spatial_report,
        source_zone_summary=source_zone_summary,
        scenario_summary=scenario_summary,
        trajectory_deposition_summary=trajectory_deposition_summary,
        artifact_roots=artifact_roots,
        closure_gap_report=closure_gap_report,
    )

    attribution_limits = summarize_attribution_limits(
        source_zone_summary=source_zone_summary,
        scenario_summary=scenario_summary,
        trajectory_deposition_summary=trajectory_deposition_summary,
        layer_summaries=layer_summaries,
    )
    prioritized_unknowns = prioritize_unknowns(closure_gap_report, layer_summaries)

    return {
        "schema_version": SCHEMA_VERSION,
        "hotspot_provenance_status": "measured_existing_artifacts",
        "readiness_status": "ready",
        "selected_layers": list(spatial_report.get("selected_layers", [])),
        "source_zone_evidence": source_zone_summary,
        "scenario_evidence": scenario_summary,
        "trajectory_deposition_evidence": trajectory_deposition_summary,
        "artifact_roots": artifact_roots,
        "layer_provenance_summaries": layer_summaries,
        "attribution_limits": attribution_limits,
        "prioritized_unknowns": prioritized_unknowns,
        "hotspot_provenance_classes": {
            layer_key: summary["hotspot_provenance_class"] for layer_key, summary in layer_summaries.items()
        },
        "measurement_commands": {
            "spatial_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "closure_gap_deltas": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format json",
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "blocked_reason": "",
    }


def build_spatial_report(evidence_override: dict[str, Any] | None) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get("same_scale_uncertainty_report"), dict):
        return dict(evidence_override["same_scale_uncertainty_report"])
    if evidence_override and isinstance(evidence_override.get("spatial_report"), dict):
        return dict(evidence_override["spatial_report"])
    return SPATIAL.build_report(
        manifest_paths=list(SPATIAL.DEFAULT_MANIFESTS),
        hazard_layers=SPATIAL.DEFAULT_HAZARD_LAYERS,
        top_n=8,
    )


def build_closure_gap_report(evidence_override: dict[str, Any] | None) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get("closure_gap_report"), dict):
        return dict(evidence_override["closure_gap_report"])
    return CLOSURE_GAP.build_report()


def resolve_provenance_paths(evidence_override: dict[str, Any] | None) -> ProvenanceInputPaths:
    return ProvenanceInputPaths(
        source_zone_metadata=Path(
            str((evidence_override or {}).get("source_zone_metadata_path") or DEFAULT_SOURCE_ZONE_METADATA)
        ),
        scenario_table=Path(str((evidence_override or {}).get("scenario_table_path") or DEFAULT_SCENARIO_TABLE)),
        trajectory_metadata=Path(
            str((evidence_override or {}).get("trajectory_metadata_path") or DEFAULT_TRAJECTORY_METADATA)
        ),
        deposition=Path(str((evidence_override or {}).get("deposition_path") or DEFAULT_DEPOSITION)),
    )


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HotspotProvenanceError(f"required YAML input is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise HotspotProvenanceError(f"required CSV input is missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def summarize_source_zone(source_zone: dict[str, Any], path: Path) -> dict[str, Any]:
    geometry = source_zone.get("geometry") or {}
    vertices = geometry.get("vertices") or []
    polygon = [(float(item[0]), float(item[1])) for item in vertices if isinstance(item, list) and len(item) >= 2]
    bbox = polygon_bbox(polygon)
    release_sampling_policy = dict(source_zone.get("release_sampling_policy") or {})
    return {
        "path": str(path),
        "source_zone_id": source_zone.get("source_zone_id"),
        "schema_version": source_zone.get("schema_version"),
        "crs_epsg": source_zone.get("crs_epsg"),
        "vertical_datum": source_zone.get("vertical_datum"),
        "geometry_type": geometry.get("type"),
        "vertex_count": len(polygon),
        "polygon": [{"x": x, "y": y} for x, y in polygon],
        "polygon_bbox": bbox,
        "release_sampling_policy": release_sampling_policy,
        "annual_release_frequency_per_year": source_zone.get("annual_release_frequency_per_year"),
        "provenance": dict(source_zone.get("provenance") or {}),
        "provenance_class": "single_source_zone_polygon",
    }


def summarize_scenario_table(rows: list[dict[str, str]], path: Path) -> dict[str, Any]:
    scenarios = [row for row in rows if any(value.strip() for value in row.values() if value is not None)]
    scenario_ids = unique_values(scenarios, "scenario_id")
    source_zone_ids = unique_values(scenarios, "source_zone_id")
    return {
        "path": str(path),
        "row_count": len(scenarios),
        "scenario_ids": scenario_ids,
        "source_zone_ids": source_zone_ids,
        "rows": scenarios,
        "scenario_family_class": "single_committed_scenario_row" if len(scenarios) == 1 else "multi_row_scenario_table",
        "attribution_class": "single_scenario_row_only" if len(scenarios) == 1 else "multi_row_scenario_family",
    }


def summarize_trajectory_deposition(
    *,
    trajectory_rows: list[dict[str, str]],
    deposition_rows: list[dict[str, str]],
    trajectory_metadata_path: Path,
    deposition_path: Path,
) -> dict[str, Any]:
    trajectory_source_zone_ids = unique_values(trajectory_rows, "source_zone_id")
    trajectory_scenario_ids = unique_values(trajectory_rows, "scenario_id")
    trajectory_release_ids = unique_values(trajectory_rows, "release_id")
    deposition_trajectory_ids = unique_values(deposition_rows, "trajectory_id")
    return {
        "trajectory_metadata_path": str(trajectory_metadata_path),
        "deposition_path": str(deposition_path),
        "trajectory_metadata_row_count": len(trajectory_rows),
        "deposition_row_count": len(deposition_rows),
        "trajectory_source_zone_ids": trajectory_source_zone_ids,
        "trajectory_scenario_ids": trajectory_scenario_ids,
        "trajectory_release_ids": trajectory_release_ids,
        "deposition_trajectory_ids": deposition_trajectory_ids,
        "trajectory_metadata_sample_rows": trajectory_rows[:3],
        "deposition_sample_rows": deposition_rows[:3],
        "traceability_class": "run_level_traceable_without_cell_lineage"
        if trajectory_rows and deposition_rows
        else "insufficient_run_level_evidence",
        "cell_lineage_class": "not_available_from_committed_artifacts",
        "can_attribute": [
            "run-level trajectory/deposition evidence exists",
            "shared source-zone and scenario identifiers are recorded in committed metadata",
        ],
        "cannot_attribute": [
            "individual hotspot cells to specific trajectory_ids",
            "specific hotspot cells to a committed cell-level lineage table",
        ],
    }


def summarize_artifact_roots(spatial_report: dict[str, Any], provenance_paths: ProvenanceInputPaths) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    for artifact in spatial_report.get("artifacts_measured", []):
        manifest_text = str(artifact.get("manifest_path") or "").strip()
        if not manifest_text:
            continue
        manifest_path = Path(manifest_text)
        hazard_root = manifest_path.parent
        roots.append(
            {
                "root_type": "hazard_manifest_root",
                "artifact_id": artifact.get("artifact_id"),
                "path": str(hazard_root),
                "manifest_path": str(manifest_path),
            }
        )
        private_root = map_private_root(manifest_path)
        if private_root is not None:
            roots.append(
                {
                    "root_type": "validation_private_root",
                    "artifact_id": artifact.get("artifact_id"),
                    "path": str(private_root),
                    "manifest_path": str(manifest_path),
                }
            )
    roots.extend(
        [
            {
                "root_type": "input_root",
                "artifact_id": "tschamut_public_inputs",
                "path": str(provenance_paths.source_zone_metadata.parent),
                "manifest_path": str(provenance_paths.source_zone_metadata),
            },
            {
                "root_type": "input_root",
                "artifact_id": "tschamut_public_scenario_table",
                "path": str(provenance_paths.scenario_table.parent),
                "manifest_path": str(provenance_paths.scenario_table),
            },
            {
                "root_type": "validation_private_root",
                "artifact_id": "tschamut_public_conditional_gate_v1_trajectory_metadata",
                "path": str(provenance_paths.trajectory_metadata.parent),
                "manifest_path": str(provenance_paths.trajectory_metadata),
            },
            {
                "root_type": "validation_private_root",
                "artifact_id": "tschamut_public_conditional_gate_v1_deposition",
                "path": str(provenance_paths.deposition.parent),
                "manifest_path": str(provenance_paths.deposition),
            },
        ]
    )
    return unique_root_entries(roots)


def build_layer_provenance_summaries(
    *,
    spatial_report: dict[str, Any],
    source_zone_summary: dict[str, Any],
    scenario_summary: dict[str, Any],
    trajectory_deposition_summary: dict[str, Any],
    artifact_roots: list[dict[str, Any]],
    closure_gap_report: dict[str, Any],
) -> dict[str, Any]:
    layer_roles = closure_gap_layer_roles(closure_gap_report)
    summaries: dict[str, Any] = {}
    polygon = [(item["x"], item["y"]) for item in source_zone_summary.get("polygon", [])]
    for layer_key in spatial_report.get("selected_layers", []):
        layer_summary = dict((spatial_report.get("layer_summaries") or {}).get(layer_key) or {})
        top_cells = list(layer_summary.get("top_high_uncertainty_cells") or [])
        cell_summaries = [summarize_hotspot_cell(cell, polygon) for cell in top_cells]
        source_zone_class = summarize_source_zone_class(cell_summaries)
        scenario_class = scenario_summary["attribution_class"]
        trajectory_class = trajectory_deposition_summary["traceability_class"]
        layer_role = layer_roles.get(layer_key) or layer_summary.get("mask_evidence", {}).get("closure_role") or "unknown"
        hotspot_provenance_class = combine_provenance_class(
            layer_role=layer_role,
            source_zone_class=source_zone_class,
            scenario_class=scenario_class,
            trajectory_class=trajectory_class,
        )
        summaries[layer_key] = {
            "layer_key": layer_key,
            "closure_role": layer_role,
            "uncertainty_concentration_class": layer_summary.get("uncertainty_concentration_class"),
            "disagreement_decomposition_class": layer_summary.get("disagreement_decomposition", {}).get("classification"),
            "hotspot_provenance_class": hotspot_provenance_class,
            "source_zone_attribution_class": source_zone_class,
            "scenario_attribution_class": scenario_class,
            "trajectory_deposition_attribution_class": trajectory_class,
            "artifact_root_class": "committed_same_scale_artifact_roots",
            "hotspot_cell_count": len(cell_summaries),
            "top_high_uncertainty_cells": cell_summaries,
            "hotspot_support_summary": summarize_hotspot_support(cell_summaries),
            "artifact_roots": artifact_roots,
            "evidence_can_attribute": [
                "high-uncertainty cells are located by row/column and LV95 center points",
                "source-zone geometry and release policy are committed metadata",
                "scenario row contents are committed as a single table row",
                "trajectory and deposition evidence are committed at run level",
                "artifact roots for the measured layers are explicit and repeatable",
            ],
            "evidence_cannot_attribute": [
                "individual hotspot cells to specific trajectory_ids",
                "source-zone family differences beyond the single committed source polygon",
                "scenario-family differences beyond the single committed scenario row",
                "cell-level causality from the run-level trajectory/deposition outputs alone",
            ],
        }
    return summaries


def summarize_hotspot_cell(cell: dict[str, Any], polygon: list[tuple[float, float]]) -> dict[str, Any]:
    x_center = float(cell.get("x_center") or 0.0)
    y_center = float(cell.get("y_center") or 0.0)
    relation = classify_point_to_polygon(x_center, y_center, polygon)
    values_by_artifact = dict(cell.get("values_by_artifact") or {})
    support_flags_by_artifact = dict(cell.get("support_flags_by_artifact") or {})
    valid_flags_by_artifact = dict(cell.get("valid_flags_by_artifact") or {})
    return {
        "row": int(cell.get("row") or 0),
        "col": int(cell.get("col") or 0),
        "x_center": x_center,
        "y_center": y_center,
        "range": float(cell.get("range") or 0.0),
        "values_by_artifact": values_by_artifact,
        "artifact_support_count": sum(1 for value in support_flags_by_artifact.values() if bool(value)),
        "artifact_valid_count": sum(1 for value in valid_flags_by_artifact.values() if bool(value)),
        "source_zone_relation_class": relation["source_zone_relation_class"],
        "distance_to_source_zone_m": relation["distance_to_source_zone_m"],
        "inside_source_zone_polygon": relation["inside_source_zone_polygon"],
    }


def summarize_hotspot_support(cell_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not cell_summaries:
        return {
            "hotspot_cell_count": 0,
            "all_hotspots_supported_by_all_artifacts": False,
            "all_hotspots_outside_source_zone_polygon": False,
            "minimum_source_zone_distance_m": None,
            "maximum_source_zone_distance_m": None,
        }
    distances = [float(item.get("distance_to_source_zone_m") or 0.0) for item in cell_summaries]
    support_counts = [int(item.get("artifact_support_count") or 0) for item in cell_summaries]
    valid_counts = [int(item.get("artifact_valid_count") or 0) for item in cell_summaries]
    all_artifacts = max(valid_counts) if valid_counts else 0
    return {
        "hotspot_cell_count": len(cell_summaries),
        "all_hotspots_supported_by_all_artifacts": all(count == all_artifacts for count in valid_counts) and all(
            count == all_artifacts for count in support_counts
        ),
        "all_hotspots_outside_source_zone_polygon": all(not bool(item.get("inside_source_zone_polygon")) for item in cell_summaries),
        "minimum_source_zone_distance_m": min(distances) if distances else None,
        "maximum_source_zone_distance_m": max(distances) if distances else None,
    }


def summarize_source_zone_class(cell_summaries: list[dict[str, Any]]) -> str:
    if not cell_summaries:
        return "source_zone_relation_unresolved"
    if any(bool(item.get("inside_source_zone_polygon")) for item in cell_summaries):
        return "source_zone_polygon_overlap_present"
    return "outside_source_zone_polygon"


def combine_provenance_class(
    *,
    layer_role: str,
    source_zone_class: str,
    scenario_class: str,
    trajectory_class: str,
) -> str:
    role = layer_role if layer_role in {"closure_limiting", "deferrable"} else "unclassified"
    return f"{role}_{source_zone_class}_{scenario_class}_{trajectory_class}"


def summarize_attribution_limits(
    *,
    source_zone_summary: dict[str, Any],
    scenario_summary: dict[str, Any],
    trajectory_deposition_summary: dict[str, Any],
    layer_summaries: dict[str, Any],
) -> dict[str, Any]:
    can_attribute = [
        "source-zone identity, CRS, vertical datum, and committed polygon geometry",
        "scenario table identity and the single committed scenario row",
        "run-level trajectory and deposition output presence",
        "top hotspot cell row/column and LV95 center-point positions",
        "the fact that the measured hotspots are shared across the current same-scale artifact set",
    ]
    cannot_attribute = [
        "individual hotspot cells to specific trajectory_ids",
        "scenario-family causality beyond the single committed scenario row",
        "source-zone family differences beyond the single committed source polygon",
        "physical-probability, annual-frequency, or operational significance from these artifacts alone",
    ]
    if any(summary["source_zone_attribution_class"] == "source_zone_polygon_overlap_present" for summary in layer_summaries.values()):
        can_attribute.append("direct overlap between hotspot cells and the source-zone polygon")
    else:
        cannot_attribute.append("direct source-zone overlap for the current hotspot cells")
    return {
        "can_attribute": unique_ordered(can_attribute),
        "cannot_attribute": unique_ordered(cannot_attribute),
        "source_zone_limit": (
            "single committed polygon only; no source-zone family split is supported"
            if source_zone_summary.get("provenance_class") == "single_source_zone_polygon"
            else "source-zone provenance is incomplete"
        ),
        "scenario_limit": (
            "single committed scenario row only; no scenario family split is supported"
            if scenario_summary.get("scenario_family_class") == "single_committed_scenario_row"
            else "scenario provenance is incomplete"
        ),
        "trajectory_deposition_limit": (
            "run-level trajectory/deposition evidence exists, but cell-level lineage is absent"
            if trajectory_deposition_summary.get("traceability_class") == "run_level_traceable_without_cell_lineage"
            else "trajectory/deposition provenance is incomplete"
        ),
    }


def prioritize_unknowns(closure_gap_report: dict[str, Any], layer_summaries: dict[str, Any]) -> list[dict[str, Any]]:
    layer_roles = closure_gap_layer_roles(closure_gap_report)
    ordered_layers = [
        layer_key
        for layer_key in layer_summaries.keys()
        if layer_roles.get(layer_key) == "closure_limiting"
    ]
    ordered_layers.extend(
        layer_key
        for layer_key in layer_summaries.keys()
        if layer_roles.get(layer_key) == "deferrable" and layer_key not in ordered_layers
    )

    unknowns: list[dict[str, Any]] = []
    for index, layer_key in enumerate(ordered_layers, start=1):
        summary = layer_summaries[layer_key]
        if summary["closure_role"] == "closure_limiting":
            unknowns.append(
                {
                    "priority": index,
                    "layer_key": layer_key,
                    "unknown": "Would the hotspot cluster remain in the same LV95 neighborhood if the committed source polygon were split into smaller release-cell families?",
                    "why_it_matters": "This is the first bounded question for a later ensemble because the closure-limiting layers are the dominant blockers.",
                    "next_probe": "bounded source-zone subdivision with the current scenario table held fixed",
                }
            )
        else:
            unknowns.append(
                {
                    "priority": index,
                    "layer_key": layer_key,
                    "unknown": "Would the deferrable hotspot cluster remain localized under the same bounded source-zone subdivision probe?",
                    "why_it_matters": "The deferrable layer is the comparator that should remain localized if the hotspot family is genuinely stable.",
                    "next_probe": "bounded source-zone subdivision with the current scenario table held fixed",
                }
            )
    unknowns.append(
        {
            "priority": len(unknowns) + 1,
            "layer_key": "all_selected_layers",
            "unknown": "Which hotspot cells can be linked to specific trajectory_ids or member files if a future lineage table is emitted?",
            "why_it_matters": "Current run-level evidence cannot distinguish cell causality from run-level support only.",
            "next_probe": "per-trajectory lineage table plus a compact bounded ensemble replay",
        }
    )
    unknowns.append(
        {
            "priority": len(unknowns) + 1,
            "layer_key": "all_selected_layers",
            "unknown": "Would an alternate committed scenario row or block family shift the hotspot family enough to change the layer ordering?",
            "why_it_matters": "The current scenario table has a single committed row, so scenario-family attribution is not yet testable.",
            "next_probe": "small bounded scenario-family expansion after source-zone subdivision is characterized",
        }
    )
    return unknowns


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    values = []
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def unique_root_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique_entries: list[dict[str, Any]] = []
    for entry in entries:
        key = (str(entry.get("root_type")), str(entry.get("artifact_id")), str(entry.get("path")))
        if key in seen:
            continue
        seen.add(key)
        unique_entries.append(entry)
    return unique_entries


def unique_ordered(items: list[str]) -> list[str]:
    ordered: list[str] = []
    for item in items:
        if item not in ordered:
            ordered.append(item)
    return ordered


def closure_gap_layer_roles(closure_gap_report: dict[str, Any]) -> dict[str, str]:
    layer_roles: dict[str, str] = {}
    for item in closure_gap_report.get("closure_limiting_layers", []):
        layer_key = str(item.get("layer_key") or "").strip()
        if layer_key:
            layer_roles[layer_key] = "closure_limiting"
    for item in closure_gap_report.get("deferrable_layers", []):
        layer_key = str(item.get("layer_key") or "").strip()
        if layer_key:
            layer_roles.setdefault(layer_key, "deferrable")
    return layer_roles


def map_private_root(manifest_path: Path) -> Path | None:
    parts = manifest_path.parts
    if "hazard" not in parts:
        return None
    try:
        pilot_index = parts.index("tschamut_public_pilot")
    except ValueError:
        return None
    suffix = Path(*parts[pilot_index + 1 : -1])
    if not suffix.parts:
        return None
    return ROOT / "validation/private/tschamut_public_pilot" / suffix


def polygon_bbox(polygon: list[tuple[float, float]]) -> dict[str, float] | None:
    if not polygon:
        return None
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return {"xmin": min(xs), "xmax": max(xs), "ymin": min(ys), "ymax": max(ys)}


def classify_point_to_polygon(
    x: float,
    y: float,
    polygon: list[tuple[float, float]],
) -> dict[str, Any]:
    if len(polygon) < 3:
        return {
            "inside_source_zone_polygon": False,
            "source_zone_relation_class": "source_zone_relation_unresolved",
            "distance_to_source_zone_m": None,
        }
    inside = point_in_polygon(x, y, polygon)
    distance = 0.0 if inside else point_to_polygon_distance(x, y, polygon)
    relation = "inside_source_zone_polygon" if inside else "outside_source_zone_polygon"
    return {
        "inside_source_zone_polygon": inside,
        "source_zone_relation_class": relation,
        "distance_to_source_zone_m": distance,
    }


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    if len(polygon) < 3:
        return False
    previous_index = len(polygon) - 1
    for index, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[previous_index]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else sys.float_info.epsilon) + xi
        )
        if intersects:
            inside = not inside
        previous_index = index
    return inside


def point_to_polygon_distance(x: float, y: float, polygon: list[tuple[float, float]]) -> float:
    distances = [
        point_to_segment_distance(x, y, polygon[index], polygon[(index + 1) % len(polygon)])
        for index in range(len(polygon))
    ]
    return min(distances) if distances else math.nan


def point_to_segment_distance(
    x: float,
    y: float,
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0.0 and dy == 0.0:
        return math.hypot(x - x1, y - y1)
    projection = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    if projection <= 0.0:
        closest_x, closest_y = x1, y1
    elif projection >= 1.0:
        closest_x, closest_y = x2, y2
    else:
        closest_x = x1 + projection * dx
        closest_y = y1 + projection * dy
    return math.hypot(x - closest_x, y - closest_y)


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "hotspot_provenance_status": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "selected_layers": [],
        "source_zone_evidence": {},
        "scenario_evidence": {},
        "trajectory_deposition_evidence": {},
        "artifact_roots": [],
        "layer_provenance_summaries": {},
        "attribution_limits": {
            "can_attribute": [],
            "cannot_attribute": [],
            "source_zone_limit": reason,
            "scenario_limit": reason,
            "trajectory_deposition_limit": reason,
        },
        "prioritized_unknowns": [],
        "hotspot_provenance_classes": {},
        "measurement_commands": {
            "spatial_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "closure_gap_deltas": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format json",
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "blocked_reason": reason + ": " + ", ".join(missing_inputs),
        "missing_inputs": missing_inputs,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"hotspot_provenance_status: {report['hotspot_provenance_status']}",
        f"selected_layers: {', '.join(report.get('selected_layers', []))}",
    ]
    if report["hotspot_provenance_status"] != "measured_existing_artifacts":
        lines.append(f"blocked reason: {report['blocked_reason']}")
        for path in report.get("missing_inputs", []):
            lines.append(f"- missing: {path}")
        return "\n".join(lines)

    source_zone = report.get("source_zone_evidence", {})
    scenario = report.get("scenario_evidence", {})
    trajectory = report.get("trajectory_deposition_evidence", {})
    lines.append(
        f"source zone: {source_zone.get('source_zone_id')} | "
        f"vertices={source_zone.get('vertex_count')} | "
        f"polygon class={source_zone.get('provenance_class')}"
    )
    lines.append(
        f"scenario rows: {scenario.get('row_count')} | "
        f"class={scenario.get('attribution_class')} | "
        f"scenario_ids={', '.join(scenario.get('scenario_ids', []))}"
    )
    lines.append(
        f"trajectory/deposition: trajectory_rows={trajectory.get('trajectory_metadata_row_count')} | "
        f"deposition_rows={trajectory.get('deposition_row_count')} | "
        f"class={trajectory.get('traceability_class')}"
    )
    for layer_key in report.get("selected_layers", []):
        summary = report["layer_provenance_summaries"][layer_key]
        lines.append(
            f"- {layer_key}: {summary['hotspot_provenance_class']} | "
            f"cells={summary['hotspot_cell_count']} | "
            f"source_zone={summary['source_zone_attribution_class']} | "
            f"scenario={summary['scenario_attribution_class']} | "
            f"trajectory={summary['trajectory_deposition_attribution_class']}"
        )
        lines.append(
            f"  top-cell support: all_artifacts={summary['hotspot_support_summary']['all_hotspots_supported_by_all_artifacts']} | "
            f"outside_source_zone={summary['hotspot_support_summary']['all_hotspots_outside_source_zone_polygon']} | "
            f"min_distance_m={summary['hotspot_support_summary']['minimum_source_zone_distance_m']}"
        )
    lines.append("attribution_limits:")
    for item in report.get("attribution_limits", {}).get("can_attribute", []):
        lines.append(f"  can: {item}")
    for item in report.get("attribution_limits", {}).get("cannot_attribute", []):
        lines.append(f"  cannot: {item}")
    lines.append("prioritized_unknowns:")
    for item in report.get("prioritized_unknowns", []):
        lines.append(
            f"  {item['priority']}. {item['layer_key']} | {item['unknown']} | next={item['next_probe']}"
        )
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
