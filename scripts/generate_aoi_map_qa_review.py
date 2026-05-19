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
    return {"manifest": str(manifest_path), "html": str(html_path)}


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
    layer_rows = []
    for layer in report.get("layers") or []:
        layer_rows.append(
            "<tr>"
            f"<td>{html.escape(str(layer.get('source') or ''))}</td>"
            f"<td>{html.escape(str(layer.get('layer_name') or ''))}</td>"
            f"<td>{html.escape(str(layer.get('format') or ''))}</td>"
            f"<td>{html.escape(str(layer.get('path') or ''))}</td>"
            f"<td>{html.escape('yes' if layer.get('cloud_optimized') else 'no')}</td>"
            f"<td>{html.escape('yes' if layer.get('weighted') else 'no')}</td>"
            "</tr>"
        )

    warning_items = "".join(f"<li>{html.escape(warning)}</li>" for warning in report.get("warnings") or []) or "<li>No warnings.</li>"
    layer_presence = report.get("layer_presence") or {}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AOI Map QA Review</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; line-height: 1.45; color: #172033; }}
    h1, h2 {{ line-height: 1.15; }}
    .badge {{ display: inline-block; padding: 0.15rem 0.45rem; border-radius: 0.35rem; background: #e8f0fe; color: #174ea6; font-size: 0.86rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.45rem; text-align: left; vertical-align: top; }}
    th {{ background: #f5f7fb; }}
    code {{ background: #f5f7fb; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>AOI Map QA Review</h1>
  <p><span class="badge">{html.escape(str(report.get("status") or "unknown"))}</span> <span class="badge">diagnostic review only</span> <span class="badge">not operational</span></p>
  <p>This static review surface overlays terrain, release-zone metadata, scenario metadata, hazard-layer inventory, and context availability from existing manifests. It does not change hazard values, authorize operational use, or imply physical-probability or annual-frequency semantics.</p>
  <h2>Inputs</h2>
  <ul>
    <li>Input root: <code>{html.escape(str(report.get("input_root") or ""))}</code></li>
    <li>Map package manifest: <code>{html.escape(str(report.get("map_package_manifest_path") or "missing"))}</code></li>
    <li>Pilot GIS package manifest: <code>{html.escape(str(report.get("pilot_gis_package_manifest_path") or "missing"))}</code></li>
    <li>Hazard manifest: <code>{html.escape(str(report.get("hazard_manifest_path") or "missing"))}</code></li>
  </ul>
  <h2>Layer Presence</h2>
  <ul>
    <li>Terrain: {html.escape(str(layer_presence.get("terrain", {}).get("present", False)))}</li>
    <li>Release zone metadata: {html.escape(str(layer_presence.get("release_zone", {}).get("present", False)))}</li>
    <li>Scenario metadata: {html.escape(str(layer_presence.get("scenario_metadata", {}).get("present", False)))}</li>
    <li>Hazard layers: {html.escape(str(layer_presence.get("hazard_layers", {}).get("count", 0)))}</li>
    <li>Context layers: {html.escape(str(layer_presence.get("context_layers", {}).get("count", 0)))}</li>
  </ul>
  <h2>Layer Inventory</h2>
  <table>
    <thead><tr><th>Source</th><th>Layer</th><th>Format</th><th>Path</th><th>COG</th><th>Weighted</th></tr></thead>
    <tbody>{''.join(layer_rows) if layer_rows else '<tr><td colspan="6">No layers recorded.</td></tr>'}</tbody>
  </table>
  <h2>Warnings</h2>
  <ul>{warning_items}</ul>
  <h2>Claim Boundary</h2>
  <ul>
    <li>Operational status: <code>{html.escape(str(report.get("claim_boundary", {}).get("operational_status") or "unknown"))}</code></li>
    <li>Operational claims allowed: <code>{html.escape(str(report.get("claim_boundary", {}).get("operational_claims_allowed", False)))}</code></li>
    <li>Current allowed product labels: <code>{html.escape(", ".join(report.get("claim_boundary", {}).get("current_allowed_product_labels") or []))}</code></li>
    <li>Unsupported product labels: <code>{html.escape(", ".join(report.get("claim_boundary", {}).get("future_unsupported_product_labels") or []))}</code></li>
  </ul>
</body>
</html>
"""


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
