#!/usr/bin/env python3
"""Generate a static AOI map QA review surface from existing package manifests.

This helper is review-only. It assembles a compact HTML index and machine-
readable manifest from an existing AOI map package, pilot GIS package, and
optional hazard manifest. It does not change hazard values, run GIS software,
or claim operational hazard-map status.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - environment setup.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_map_qa_review_v1"
DEFAULT_OUTPUT_ROOT = ROOT / "validation/private/aoi_map_qa_review"


class AoiMapQaReviewError(ValueError):
    """User-facing AOI map QA review error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, type=Path, help="existing AOI hazard output root")
    parser.add_argument("--output-root", type=Path, default=None, help="ignored review output root")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output root")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    try:
        report = build_review_surface(
            input_root=args.input_root,
            output_root=args.output_root,
            overwrite=args.overwrite,
        )
    except AoiMapQaReviewError as exc:
        print(f"AOI map QA review error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))

    return 0 if report["status"] in {"review_ready", "review_ready_with_warnings"} else 2


def build_review_surface(
    *,
    input_root: Path,
    output_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    input_root = Path(input_root)
    output_root = Path(output_root) if output_root is not None else DEFAULT_OUTPUT_ROOT / input_root.name

    if output_root.exists() and overwrite:
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    map_manifest_path, map_manifest_missing = discover_single_manifest(input_root, "*map_package_manifest*.json")
    pilot_manifest_path, pilot_manifest_missing = discover_single_manifest(input_root, "*pilot_gis_package_manifest*.json")

    if map_manifest_path is None:
        report = blocked_report(
            input_root=input_root,
            output_root=output_root,
            missing_paths=[path for path in [map_manifest_missing, pilot_manifest_missing] if path],
            reason="missing map package manifest",
        )
    else:
        map_manifest = load_json(map_manifest_path)
        pilot_manifest = load_json(pilot_manifest_path) if pilot_manifest_path is not None else {}
        hazard_manifest = load_hazard_manifest(map_manifest, pilot_manifest)
        report = assemble_report(
            input_root=input_root,
            output_root=output_root,
            map_manifest_path=map_manifest_path,
            pilot_manifest_path=pilot_manifest_path,
            map_manifest=map_manifest,
            pilot_manifest=pilot_manifest,
            hazard_manifest=hazard_manifest,
        )

    report["review_surface_paths"] = write_review_surface(output_root, report)
    return report


def blocked_report(
    *,
    input_root: Path,
    output_root: Path,
    missing_paths: list[str],
    reason: str,
) -> dict[str, Any]:
    warnings = [f"blocked_missing_map_package: {reason}"]
    if missing_paths:
        warnings.append(f"missing_paths: {', '.join(missing_paths)}")
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked_missing_map_package",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "map_package_manifest_path": None,
        "pilot_gis_package_manifest_path": None,
        "hazard_manifest_path": None,
        "package_id": input_root.name,
        "layer_presence": {
            "terrain": {"present": False, "reason": "missing map package manifest"},
            "release_zone": {"present": False, "reason": "missing map package manifest"},
            "scenario_metadata": {"present": False, "reason": "missing map package manifest"},
            "hazard_layers": {"present": False, "count": 0},
            "context_layers": {"present": False, "count": 0},
        },
        "layers": [],
        "warnings": warnings,
        "warning_details": [{"code": "missing_map_package", "severity": "blocked", "message": warnings[0]}],
        "diagnostic_hazard_outputs": {
            "schema_version": SCHEMA_VERSION,
            "role": "diagnostic_hazard_outputs",
            "status": "absent",
            "claim_boundary": "diagnostic hazard outputs are unavailable until the map package manifest is present",
            "items": [],
        },
        "vector_overlays": [],
        "observed_evidence_overlays": {
            "schema_version": SCHEMA_VERSION,
            "role": "observed_evidence_overlays",
            "status": "blocked_missing_map_package",
            "claim_boundary": "observed evidence overlays are unavailable until the map package manifest is present",
            "items": [],
            "blockers": {
                "observed_runout_deposition": [],
                "release_zone_provenance": [],
            },
        },
        "package_manifest_details": {
            "map_product_id": None,
            "map_product_version": None,
            "probability_mode": None,
            "normalization_scope": None,
            "source_zone_id": None,
            "operational_status": "unknown",
        },
        "claim_boundary": {
            "operational_status": "unknown",
            "current_allowed_product_labels": [
                "unweighted_diagnostic",
                "sampling_weighted_conditional",
                "conditional_intensity_exceedance",
            ],
            "future_unsupported_product_labels": [
                "physical_probability",
                "annual_intensity_frequency",
                "return_period",
                "risk_map",
                "operational_hazard_map",
            ],
            "annualized": False,
            "operational_claims_allowed": False,
        },
    }
    return report


def assemble_report(
    *,
    input_root: Path,
    output_root: Path,
    map_manifest_path: Path,
    pilot_manifest_path: Path | None,
    map_manifest: dict[str, Any],
    pilot_manifest: dict[str, Any],
    hazard_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    layers = collect_layers(map_manifest, pilot_manifest, hazard_manifest)
    vector_overlays = [entry for entry in list(map_manifest.get("vector_overlays") or []) if isinstance(entry, dict)]
    observed_evidence_overlays = [
        entry for entry in list((map_manifest.get("observed_evidence_overlays") or {}).get("items") or []) if isinstance(entry, dict)
    ]
    warnings: list[str] = []
    warning_details: list[dict[str, Any]] = []
    layer_presence = {
        "terrain": classify_terrain_presence(pilot_manifest),
        "release_zone": classify_release_zone_presence(map_manifest),
        "scenario_metadata": classify_scenario_metadata_presence(map_manifest),
        "hazard_layers": classify_hazard_layer_presence(layers),
        "context_layers": classify_context_presence(pilot_manifest),
    }

    missing_context = layer_presence["context_layers"]["count"] == 0
    if missing_context:
        add_warning(
            warnings,
            warning_details,
            code="missing_context_layers",
            message="missing context layers: no source-zone context overlays were recorded in the pilot GIS package",
        )

    cog_blocked = [layer["layer_name"] for layer in layers if layer.get("format") == "geotiff" and not layer.get("cloud_optimized", False)]
    if cog_blocked:
        add_warning(
            warnings,
            warning_details,
            code="cog_blocked_rasters",
            message=f"COG-blocked rasters: {', '.join(cog_blocked)}",
        )

    fixture_inputs = collect_fixture_inputs(map_manifest, pilot_manifest, hazard_manifest)
    if fixture_inputs:
        add_warning(
            warnings,
            warning_details,
            code="fixture_backed_inputs",
            message=f"fixture-backed inputs: {', '.join(fixture_inputs)}",
        )

    conditional_layers = [layer["layer_name"] for layer in layers if layer.get("weighted")]
    if str(map_manifest.get("probability_mode") or "") == "sampling_weighted_conditional" or conditional_layers:
        add_warning(
            warnings,
            warning_details,
            code="conditional_only_weights",
            message=(
                "conditional-only weights: sampling_weighted_conditional layers remain conditioned on the documented "
                "filter/scenario set"
            ),
        )

    operational_statuses = [
        str(map_manifest.get("operational_status") or "").strip(),
        str(pilot_manifest.get("operational_status") or "").strip(),
        str((pilot_manifest.get("visual_qa") or {}).get("accepted_for_operational_use", False)).lower(),
    ]
    if any(status in {"research_diagnostic", "diagnostic", "false"} for status in operational_statuses):
        add_warning(
            warnings,
            warning_details,
            code="non_operational_status",
            message=(
                "non-operational status: the current package is marked for local diagnostic review only and does not "
                "authorise operational use"
            ),
        )

    if hazard_manifest is None:
        add_warning(
            warnings,
            warning_details,
            code="missing_hazard_manifest",
            message="missing hazard manifest: no run-manifest cellwise layer inventory could be loaded",
        )

    status = "review_ready_with_warnings" if warnings else "review_ready"
    hazard_layer_inventory = [layer for layer in layers if layer.get("kind") == "hazard_layer"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "input_root": str(input_root),
        "output_root": str(output_root),
        "package_id": str(map_manifest.get("map_product_id") or pilot_manifest.get("case_id") or input_root.name),
        "map_package_manifest_path": str(map_manifest_path),
        "pilot_gis_package_manifest_path": str(pilot_manifest_path) if pilot_manifest_path is not None else None,
        "hazard_manifest_path": str((hazard_manifest or {}).get("path")) if isinstance(hazard_manifest, dict) and hazard_manifest.get("path") else None,
        "layer_presence": layer_presence,
        "layers": layers,
        "diagnostic_hazard_outputs": {
            "schema_version": SCHEMA_VERSION,
            "role": "diagnostic_hazard_outputs",
            "status": "present" if hazard_layer_inventory else "absent",
            "claim_boundary": "diagnostic hazard outputs only; not calibration, holdout, or frequency evidence",
            "items": list(hazard_layer_inventory),
        },
        "vector_overlays": vector_overlays,
        "observed_evidence_overlays": {
            "schema_version": SCHEMA_VERSION,
            "role": "observed_evidence_overlays",
            "status": str((map_manifest.get("observed_evidence_overlays") or {}).get("status") or "blocked_missing_evidence"),
            "claim_boundary": "observed evidence overlays are optional and do not imply calibration, physical probability, annual frequency, risk, or operational readiness",
            "items": observed_evidence_overlays,
            "blockers": (map_manifest.get("observed_evidence_overlays") or {}).get("blockers")
            or {
                "observed_runout_deposition": [],
                "release_zone_provenance": [],
            },
        },
        "package_manifest_details": {
            "map_product_id": map_manifest.get("map_product_id"),
            "map_product_version": map_manifest.get("map_product_version"),
            "probability_mode": map_manifest.get("probability_mode"),
            "normalization_scope": map_manifest.get("normalization_scope"),
            "source_zone_id": map_manifest.get("source_zone_id"),
            "operational_status": map_manifest.get("operational_status") or pilot_manifest.get("operational_status") or "unknown",
            "source_zone_metadata_path": str(map_manifest.get("source_zone_metadata_path") or ""),
            "scenario_table_path": str(map_manifest.get("scenario_table_path") or ""),
            "terrain_path": str((pilot_manifest.get("terrain") or {}).get("path") or ""),
            "terrain_metadata_path": str((pilot_manifest.get("terrain") or {}).get("metadata_path") or (pilot_manifest.get("terrain_metadata") or {}).get("path") or ""),
        },
        "warnings": warnings,
        "warning_details": warning_details,
        "claim_boundary": claim_boundary(map_manifest, pilot_manifest),
        "review_surface_paths": {},
    }
    return report


def collect_layers(
    map_manifest: dict[str, Any],
    pilot_manifest: dict[str, Any],
    hazard_manifest: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for source, manifest in (("map_package", map_manifest), ("pilot_gis_package", pilot_manifest)):
        for output in list(manifest.get("raster_outputs") or []):
            if not isinstance(output, dict):
                continue
            layers.append(
                {
                    "source": source,
                    "layer_name": str(output.get("layer_name") or output.get("kind") or "unnamed"),
                    "path": str(output.get("path") or ""),
                    "format": str(output.get("format") or ""),
                    "cloud_optimized": bool(output.get("cloud_optimized", False)),
                    "weighted": bool(output.get("weighted", False)) or str(output.get("layer_name") or "").startswith("weighted_"),
                    "annualized": bool(output.get("annualized", False) or output.get("is_annualized", False)),
                    "kind": str(output.get("kind") or "hazard_layer"),
                }
            )

    if isinstance(hazard_manifest, dict):
        for entry in list(hazard_manifest.get("cellwise_layers") or []):
            if not isinstance(entry, dict):
                continue
            layers.append(
                {
                    "source": "hazard_manifest",
                    "layer_name": str(entry.get("layer_name") or "unnamed"),
                    "path": str(entry.get("grid_path") or ""),
                    "format": str(entry.get("format") or ""),
                    "cloud_optimized": False,
                    "weighted": str(entry.get("layer_name") or "").startswith("weighted_"),
                    "annualized": False,
                    "kind": "cellwise_layer",
                }
            )
    return dedupe_layers(layers)


def dedupe_layers(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for layer in layers:
        key = str(layer.get("layer_name", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(layer)
    return unique


def classify_terrain_presence(pilot_manifest: dict[str, Any]) -> dict[str, Any]:
    terrain = pilot_manifest.get("terrain") if isinstance(pilot_manifest.get("terrain"), dict) else {}
    terrain_metadata = pilot_manifest.get("terrain_metadata") if isinstance(pilot_manifest.get("terrain_metadata"), dict) else {}
    return {
        "present": bool(terrain),
        "path": terrain.get("path"),
        "metadata_path": terrain.get("metadata_path") or terrain_metadata.get("path"),
        "epsg": terrain.get("epsg"),
        "vertical_datum": terrain.get("vertical_datum"),
    }


def classify_release_zone_presence(map_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "present": bool(map_manifest.get("source_zone_metadata_path")),
        "path": map_manifest.get("source_zone_metadata_path"),
        "source_zone_id": map_manifest.get("source_zone_id"),
    }


def classify_scenario_metadata_presence(map_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "present": bool(map_manifest.get("scenario_table_path")),
        "path": map_manifest.get("scenario_table_path"),
        "probability_mode": map_manifest.get("probability_mode"),
        "normalization_scope": map_manifest.get("normalization_scope"),
    }


def classify_hazard_layer_presence(layers: list[dict[str, Any]]) -> dict[str, Any]:
    hazard_layers = [layer for layer in layers if layer.get("kind") == "hazard_layer"]
    return {
        "present": bool(hazard_layers),
        "count": len(hazard_layers),
        "cog_blocked_count": sum(1 for layer in hazard_layers if not layer.get("cloud_optimized", False)),
    }


def classify_context_presence(pilot_manifest: dict[str, Any]) -> dict[str, Any]:
    context = [entry for entry in list(pilot_manifest.get("source_zone_context") or []) if isinstance(entry, dict)]
    return {
        "present": bool(context),
        "count": len(context),
        "paths": [entry.get("path") for entry in context if entry.get("path")],
    }


def collect_fixture_inputs(*manifests: dict[str, Any]) -> list[str]:
    fixture_paths: list[str] = []
    for manifest in manifests:
        for key in ("source_zone_metadata_path", "scenario_table_path"):
            path = manifest.get(key)
            if looks_fixture_backed(path):
                fixture_paths.append(str(path))
        for output in list(manifest.get("raster_outputs") or []):
            if isinstance(output, dict) and looks_fixture_backed(output.get("path")):
                fixture_paths.append(str(output.get("path")))
        for entry in list(manifest.get("source_zone_context") or []):
            if isinstance(entry, dict) and looks_fixture_backed(entry.get("path")):
                fixture_paths.append(str(entry.get("path")))
    return sorted(dict.fromkeys(fixture_paths))


def looks_fixture_backed(path_text: Any) -> bool:
    if not isinstance(path_text, str) or not path_text:
        return False
    path = Path(path_text)
    parts = {part.lower() for part in path.parts}
    return "fixture" in parts or "fixtures" in parts or "fixture" in path_text.lower()


def add_warning(
    warnings: list[str],
    warning_details: list[dict[str, Any]],
    *,
    code: str,
    message: str,
    severity: str = "warning",
) -> None:
    warnings.append(message)
    warning_details.append({"code": code, "severity": severity, "message": message})


def claim_boundary(map_manifest: dict[str, Any], pilot_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "operational_status": str(map_manifest.get("operational_status") or pilot_manifest.get("operational_status") or "unknown"),
        "annualized": False,
        "operational_claims_allowed": False,
        "current_allowed_product_labels": [
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "conditional_intensity_exceedance",
        ],
        "future_unsupported_product_labels": [
            "physical_probability",
            "annual_intensity_frequency",
            "return_period",
            "risk_map",
            "operational_hazard_map",
        ],
    }


def load_hazard_manifest(
    map_manifest: dict[str, Any],
    pilot_manifest: dict[str, Any],
) -> dict[str, Any] | None:
    candidate_paths = list(map_manifest.get("hazard_manifest_paths") or []) or list(pilot_manifest.get("hazard_manifest_paths") or [])
    for candidate in candidate_paths:
        if not isinstance(candidate, str) or not candidate:
            continue
        path = resolve_path(candidate)
        if path.exists():
            data = load_json(path)
            data["path"] = str(path)
            return data
    return None


def write_review_surface(output_root: Path, report: dict[str, Any]) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "aoi_map_qa_review_manifest.json"
    html_path = output_root / "index.html"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(render_html_report(report), encoding="utf-8")
    return {"manifest": str(manifest_path), "html": str(html_path), "entrypoint": str(html_path)}


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"aoi map qa review status: {report.get('status')}",
        f"input_root: {report.get('input_root')}",
        f"output_root: {report.get('output_root')}",
        f"package_id: {report.get('package_id')}",
        f"warnings: {len(report.get('warnings') or [])}",
    ]
    for warning in report.get("warnings") or []:
        lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def render_html_report(report: dict[str, Any]) -> str:
    layer_presence = report.get("layer_presence") or {}
    package_details = report.get("package_manifest_details") or {}
    diagnostic_hazard_outputs = report.get("diagnostic_hazard_outputs") or {"items": []}
    vector_overlays = report.get("vector_overlays") or []
    observed_overlays_section = report.get("observed_evidence_overlays") or {"items": [], "blockers": {}}
    observed_overlays = observed_overlays_section.get("items") or []
    missing_context_paths = layer_presence.get("context_layers", {}).get("paths") or []
    warning_items = report.get("warning_details") or []
    if not warning_items and report.get("warnings"):
        warning_items = [{"severity": "warning", "message": warning} for warning in report.get("warnings") or []]

    hazard_rows = "".join(render_hazard_row(layer) for layer in diagnostic_hazard_outputs.get("items") or [])
    vector_rows = "".join(render_overlay_row(layer, "overlay") for layer in vector_overlays)
    observed_rows = "".join(render_overlay_row(layer, "evidence") for layer in observed_overlays)
    warning_rows = "".join(
        f"<li class='warning-{html.escape(str(item.get('severity') or 'warning'))}'><strong>{html.escape(str(item.get('code') or 'warning'))}</strong>: {html.escape(str(item.get('message') or ''))}</li>"
        for item in warning_items
    ) or "<li>No warnings.</li>"
    context_rows = "".join(f"<li>{render_path_link(path)}</li>" for path in missing_context_paths) or "<li>No context layers were recorded.</li>"
    package_rows = [
        ("Map product", package_details.get("map_product_id")),
        ("Map version", package_details.get("map_product_version")),
        ("Probability mode", package_details.get("probability_mode")),
        ("Normalization scope", package_details.get("normalization_scope")),
        ("Source zone id", package_details.get("source_zone_id")),
        ("Operational status", package_details.get("operational_status")),
        ("Map package manifest", report.get("map_package_manifest_path")),
        ("Pilot GIS package manifest", report.get("pilot_gis_package_manifest_path")),
        ("Hazard manifest", report.get("hazard_manifest_path")),
        ("Output root", report.get("output_root")),
        ("Input root", report.get("input_root")),
        ("Source-zone metadata", package_details.get("source_zone_metadata_path")),
        ("Scenario table", package_details.get("scenario_table_path")),
        ("Terrain", package_details.get("terrain_path")),
        ("Terrain metadata", package_details.get("terrain_metadata_path")),
    ]
    path_like_labels = {
        "Map package manifest",
        "Pilot GIS package manifest",
        "Hazard manifest",
        "Output root",
        "Input root",
        "Source-zone metadata",
        "Scenario table",
        "Terrain",
        "Terrain metadata",
    }
    package_rows_html = "".join(
        f"<tr><th>{html.escape(str(label))}</th><td>{render_path_link(value) if label in path_like_labels else render_value(value)}</td></tr>"
        for label, value in package_rows
    )
    claim = report.get("claim_boundary") or {}
    claim_current = "".join(f"<li>{html.escape(str(label))}</li>" for label in claim.get("current_allowed_product_labels") or [])
    claim_future = "".join(f"<li>{html.escape(str(label))}</li>" for label in claim.get("future_unsupported_product_labels") or [])
    vector_overlays_summary = render_overlay_summary(vector_overlays)
    observed_overlays_summary = render_overlay_summary(observed_overlays)
    diagnostic_summary = render_overlay_summary(diagnostic_hazard_outputs.get("items") or [])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AOI Map QA Review</title>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #546179; --paper: #f7f8fb; --panel: #ffffff; --line: #d9e0ea; --hazard: #264653; --overlay: #8d4f12; --evidence: #6b3f93; --context: #4b6a3b; --boundary: #8c2f2f; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; line-height: 1.5; color: var(--ink); background: linear-gradient(180deg, #f8fbff, #eef3f9 54%, #f5f7fb); }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    h1, h2, h3 {{ line-height: 1.15; margin: 0 0 0.75rem; }}
    p {{ margin: 0 0 1rem; }}
    .hero {{ background: linear-gradient(135deg, #ffffff, #f3f7fc); border: 1px solid var(--line); border-radius: 1rem; padding: 1.2rem 1.4rem; box-shadow: 0 12px 32px rgba(17, 24, 39, 0.05); }}
    .badges, .legend {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.28rem 0.55rem; border-radius: 999px; background: #e8f0fe; color: #174ea6; font-size: 0.86rem; }}
    .badge.neutral {{ background: #eef2f7; color: var(--muted); }}
    .badge.hazard {{ background: #e5f3f0; color: var(--hazard); }}
    .badge.overlay {{ background: #f6ebe0; color: var(--overlay); }}
    .badge.evidence {{ background: #f1e8f8; color: var(--evidence); }}
    .badge.context {{ background: #e8f2e2; color: var(--context); }}
    .badge.boundary {{ background: #fbeaea; color: var(--boundary); }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 1rem; padding: 1rem 1.1rem; box-shadow: 0 8px 24px rgba(17, 24, 39, 0.04); }}
    .panel h2 {{ margin-bottom: 0.5rem; }}
    .legend-item {{ padding: 0.25rem 0.5rem; border-radius: 999px; background: var(--paper); border: 1px solid var(--line); font-size: 0.88rem; }}
    .togglebar {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin: 1rem 0; }}
    .togglebar label {{ display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.7rem; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); cursor: pointer; }}
    details {{ background: var(--panel); border: 1px solid var(--line); border-radius: 1rem; margin-top: 1rem; overflow: hidden; }}
    details > summary {{ cursor: pointer; list-style: none; padding: 0.9rem 1rem; font-weight: 700; }}
    details > summary::-webkit-details-marker {{ display: none; }}
    details .inner {{ padding: 0 1rem 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0 0.25rem; }}
    th, td {{ border: 1px solid var(--line); padding: 0.45rem; text-align: left; vertical-align: top; }}
    th {{ background: var(--paper); width: 20%; }}
    code, pre {{ background: #f5f7fb; padding: 0.08rem 0.25rem; border-radius: 0.3rem; }}
    pre {{ white-space: pre-wrap; word-break: break-word; }}
    ul, ol {{ margin: 0.45rem 0 0.8rem 1.2rem; }}
    .warning-block {{ border-left: 4px solid var(--boundary); padding-left: 0.75rem; }}
    .section-note {{ color: var(--muted); font-size: 0.92rem; }}
    .layer-row[data-role="hazard"] td:first-child {{ color: var(--hazard); }}
    .layer-row[data-role="overlay"] td:first-child {{ color: var(--overlay); }}
    .layer-row[data-role="evidence"] td:first-child {{ color: var(--evidence); }}
    .layer-row[data-role="context"] td:first-child {{ color: var(--context); }}
    .layer-row[data-role="boundary"] td:first-child {{ color: var(--boundary); }}
    .stack {{ display: grid; gap: 0.75rem; }}
    .stack .panel + .panel {{ margin-top: 0; }}
  </style>
  <script>
    document.addEventListener("DOMContentLoaded", () => {{
      document.querySelectorAll("[data-toggle-target]").forEach((control) => {{
        const target = document.getElementById(control.getAttribute("data-toggle-target"));
        if (!target) {{
          return;
        }}
        const sync = () => {{
          target.hidden = !control.checked;
        }};
        control.addEventListener("change", sync);
        sync();
      }});
    }});
  </script>
</head>
<body>
<main>
  <section class="hero">
    <h1>AOI Map QA Review</h1>
    <div class="badges">
      <span class="badge">{html.escape(str(report.get("status") or "unknown"))}</span>
      <span class="badge neutral">diagnostic review only</span>
      <span class="badge neutral">single openable bundle</span>
      <span class="badge boundary">not operational</span>
    </div>
    <p>This static review bundle keeps the diagnostic hazard layers, release and scenario overlays, optional observed evidence, provenance, warnings, and claim boundaries in one openable entrypoint. It does not change hazard values, authorize operational use, or imply physical-probability or annual-frequency semantics.</p>
    <div class="legend">
      <span class="legend-item">Hazard: diagnostic rasters and cellwise layers</span>
      <span class="legend-item">Overlay: release-zone and scenario geometry</span>
      <span class="legend-item">Evidence: optional observed evidence overlays</span>
      <span class="legend-item">Context: missing or present source-zone context</span>
      <span class="legend-item">Boundary: non-operational claim limits</span>
    </div>
  </section>

  <div class="togglebar">
    <label><input type="checkbox" checked data-toggle-target="diagnostic-panel">Diagnostic hazard layers</label>
    <label><input type="checkbox" checked data-toggle-target="overlay-panel">Release and scenario overlays</label>
    <label><input type="checkbox" checked data-toggle-target="evidence-panel">Optional observed evidence</label>
    <label><input type="checkbox" checked data-toggle-target="context-panel">Missing context</label>
    <label><input type="checkbox" checked data-toggle-target="provenance-panel">Provenance and package manifest</label>
    <label><input type="checkbox" checked data-toggle-target="boundary-panel">Claim boundaries</label>
  </div>

  <details id="diagnostic-panel" open>
    <summary>Diagnostic hazard layers</summary>
    <div class="inner">
      <p class="section-note">{html.escape(diagnostic_summary)}</p>
      <table>
        <thead><tr><th>Layer</th><th>Source</th><th>Format</th><th>Path</th><th>COG</th><th>Weighted</th></tr></thead>
        <tbody>{hazard_rows or '<tr><td colspan="6">No diagnostic hazard layers recorded.</td></tr>'}</tbody>
      </table>
    </div>
  </details>

  <details id="overlay-panel" open>
    <summary>Release and scenario overlays</summary>
    <div class="inner">
      <p class="section-note">{html.escape(vector_overlays_summary)}</p>
      <table>
        <thead><tr><th>Overlay</th><th>Role</th><th>Path</th><th>Claim boundary</th></tr></thead>
        <tbody>{vector_rows or '<tr><td colspan="4">No release or scenario overlays recorded.</td></tr>'}</tbody>
      </table>
    </div>
  </details>

  <details id="evidence-panel" open>
    <summary>Optional observed evidence</summary>
    <div class="inner">
      <p class="section-note">{html.escape(observed_overlays_summary)}</p>
      <table>
        <thead><tr><th>Evidence</th><th>Role</th><th>Path</th><th>Claim boundary</th></tr></thead>
        <tbody>{observed_rows or '<tr><td colspan="4">No observed evidence overlays recorded.</td></tr>'}</tbody>
      </table>
    </div>
  </details>

  <details id="context-panel" open>
    <summary>Missing context</summary>
    <div class="inner">
      <p class="section-note">Terrain and release-zone provenance are separated from context availability. When context layers are absent, that absence is surfaced here instead of being folded into the hazard layer table.</p>
      <ul>
        <li>Terrain present: <code>{html.escape(str(layer_presence.get("terrain", {}).get("present", False)))}</code></li>
        <li>Release zone metadata present: <code>{html.escape(str(layer_presence.get("release_zone", {}).get("present", False)))}</code></li>
        <li>Scenario metadata present: <code>{html.escape(str(layer_presence.get("scenario_metadata", {}).get("present", False)))}</code></li>
        <li>Context layer count: <code>{html.escape(str(layer_presence.get("context_layers", {}).get("count", 0)))}</code></li>
      </ul>
      <ul>{context_rows}</ul>
    </div>
  </details>

  <details id="provenance-panel" open>
    <summary>Provenance and package manifest</summary>
    <div class="inner">
      <table>
        <tbody>{package_rows_html}</tbody>
      </table>
      <p class="section-note">The manifest details are shown here so the bundle can be reviewed without opening raw JSON first.</p>
    </div>
  </details>

  <details id="boundary-panel" open>
    <summary>Claim boundaries</summary>
    <div class="inner warning-block">
      <p>This bundle is diagnostic and non-operational. It does not assert annual frequency, physical probability, risk, exposure, vulnerability, or distributed-execution semantics.</p>
      <table>
        <tbody>
          <tr><th>Operational status</th><td><code>{html.escape(str(claim.get("operational_status") or "unknown"))}</code></td></tr>
          <tr><th>Annualized</th><td><code>{html.escape(str(claim.get("annualized", False)))}</code></td></tr>
          <tr><th>Operational claims allowed</th><td><code>{html.escape(str(claim.get("operational_claims_allowed", False)))}</code></td></tr>
          <tr><th>Current allowed labels</th><td><ul>{claim_current or '<li>None recorded</li>'}</ul></td></tr>
          <tr><th>Deferred or unsupported labels</th><td><ul>{claim_future or '<li>None recorded</li>'}</ul></td></tr>
        </tbody>
      </table>
    </div>
  </details>

  <details open>
    <summary>Warnings</summary>
    <div class="inner warning-block">
      <ul>{warning_rows}</ul>
    </div>
  </details>
</main>
</body>
</html>
"""


def render_hazard_row(layer: dict[str, Any]) -> str:
    label = layer.get("layer_name") or layer.get("overlay_role") or "hazard_layer"
    role_text = layer.get("source") or "hazard"
    path_text = str(layer.get("path") or "")
    claim = str(layer.get("claim_boundary") or "")
    return (
        f'<tr class="layer-row" data-role="hazard">'
        f"<td>{render_value(label)}</td>"
        f"<td>{html.escape(str(role_text))}</td>"
        f"<td>{render_value(layer.get('format') or layer.get('evidence_category') or '')}</td>"
        f"<td>{render_path_link(path_text)}</td>"
        f"<td>{html.escape('yes' if layer.get('cloud_optimized') else 'no')}</td>"
        f"<td>{html.escape('yes' if layer.get('weighted') else 'no')}</td>"
        f"</tr>"
        f"<tr class=\"layer-row\" data-role=\"hazard\">"
        f"<td colspan=\"6\"><span class=\"section-note\">{html.escape(claim)}</span></td>"
        "</tr>"
    )


def render_overlay_row(layer: dict[str, Any], role: str) -> str:
    label = layer.get("layer_name") or layer.get("overlay_role") or role
    role_text = layer.get("overlay_role") or layer.get("evidence_category") or role
    path_text = str(layer.get("path") or layer.get("source_path") or layer.get("source_record_path") or "")
    claim = str(layer.get("claim_boundary") or "")
    return (
        f'<tr class="layer-row" data-role="{html.escape(role)}">'
        f"<td>{render_value(label)}</td>"
        f"<td>{html.escape(str(role_text))}</td>"
        f"<td>{render_path_link(path_text)}</td>"
        f"<td>{html.escape(claim)}</td>"
        "</tr>"
    )


def render_overlay_summary(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No overlay records are available for this category."
    labels = []
    for item in items:
        label = item.get("layer_name") or item.get("overlay_role") or item.get("evidence_category") or "overlay"
        labels.append(str(label))
    return f"{len(items)} item(s): {', '.join(labels)}"


def render_value(value: Any) -> str:
    if value in (None, ""):
        return "<em>missing</em>"
    return html.escape(str(value))


def render_path_link(value: Any) -> str:
    if value in (None, ""):
        return "<em>missing</em>"
    text = str(value)
    path = Path(text)
    if path.is_absolute():
        return f'<a href="{html.escape(path.as_uri())}" target="_blank" rel="noreferrer">{html.escape(text)}</a>'
    return html.escape(text)


def discover_single_manifest(root: Path, pattern: str) -> tuple[Path | None, str | None]:
    if not root.exists():
        return None, str(root)
    matches = sorted(root.glob(pattern))
    if not matches:
        return None, str(root / pattern)
    return matches[0], None


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AoiMapQaReviewError(f"JSON document must be an object: {path}")
    return data


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
