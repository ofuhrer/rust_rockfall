#!/usr/bin/env python3
"""Plan swisstopo acquisition needs from a small AOI/site config.

This helper is a dry-run planner only. It does not download public geodata,
stage tiles, or authorize any ensemble work. Instead, it translates a candidate
AOI/site configuration into the public swisstopo product categories, expected
staging paths, and unresolved acquisition decisions that still need a real
staging choice.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "swisstopo_aoi_acquisition_dry_run_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_ACQUISITION_MANIFEST = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
}


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("swisstopo_aoi_planner_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["planner_status"] == "ready" else 2


def build_report(site_config: Path | None, site_id: str | None = None) -> dict[str, Any]:
    config = PREFLIGHT.load_site_config(site_config) if site_config is not None and site_config.exists() else {}
    config_base = site_config.parent if site_config is not None else ROOT

    candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or site_id or "unspecified_second_site"
    candidate_site_id = candidate_site_id.strip()
    candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
    selection_rationale = PREFLIGHT.text_value(config.get("candidate_selection_rationale"))
    site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}

    acquisition_manifest_path = PREFLIGHT.resolve_repo_path(
        config.get("acquisition_manifest_path"),
        DEFAULT_ACQUISITION_MANIFEST,
        base=config_base,
    )
    acquisition_manifest = PREFLIGHT.load_site_config(acquisition_manifest_path) if acquisition_manifest_path.exists() else {}
    path_layout = PREFLIGHT.text_value(config.get("path_layout"))
    path_base = config_base if path_layout == "site_root_relative" else PREFLIGHT.ROOT
    paths = PREFLIGHT.build_paths(candidate_site_id, config, base=path_base)
    acquisition_report = PREFLIGHT.build_report(site_config)
    public_context_acquisition_plan = PREFLIGHT.build_public_context_acquisition_plan(acquisition_manifest, [])
    workflow_contract = acquisition_report["public_geodata_workflow_contract"]
    aoi_tile_discovery = acquisition_report["aoi_tile_discovery"]

    product_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    unresolved_acquisition_decisions: list[dict[str, Any]] = []
    expected_staging_paths: dict[str, str] = {}

    for entry in acquisition_manifest.get("expected_products") or []:
        if not isinstance(entry, dict):
            continue

        category = PREFLIGHT.text_value(entry.get("category"))
        product = PREFLIGHT.text_value(entry.get("product"))
        required = bool(entry.get("required"))
        expected_path = PREFLIGHT.text_value(entry.get("expected_staged_path"))
        source_reference = PREFLIGHT.text_value(entry.get("source_reference"))
        notes = PREFLIGHT.text_value(entry.get("notes"))
        resolved_path = PREFLIGHT.resolve_repo_path(expected_path, base=config_base) if expected_path else None
        staged = PREFLIGHT.is_staged_path(resolved_path) if resolved_path is not None else False

        if not expected_path and category in paths:
            expected_path = str(paths[category])
        expected_staging_paths[category] = expected_path

        row = {
            "category": category,
            "product": product,
            "required": required,
            "expected_staged_path": expected_path,
            "current_status": current_status(category, required, staged),
            "staged": staged,
            "source_reference": source_reference,
            "notes": notes,
        }

        if category in metadata_category_set():
            metadata_rows.append(row)
        else:
            product_rows.append(row)

        if should_record_unresolved(category, required, staged):
            unresolved_acquisition_decisions.append(
                {
                    "decision_id": f"stage_{category}",
                    "category": category,
                    "product": product,
                    "required": required,
                    "expected_staged_path": expected_path,
                    "decision_type": decision_type(category, required),
                    "current_status": row["current_status"],
                    "reason": notes or "staging has not been completed yet",
                    "source_reference": source_reference,
                }
            )

    boundary_status = acquisition_boundary_status(product_rows)
    boundary_categories = [
        row["category"]
        for row in product_rows
        if row["required"] and row["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and row["current_status"] != "ready"
    ]
    planner_status = "ready"
    if not acquisition_manifest_path.exists():
        planner_status = "blocked_missing_inputs"
    elif acquisition_report.get("aoi_tile_discovery", {}).get("discovery_status") == "blocked_missing_inputs":
        planner_status = "blocked_missing_inputs"

    report = {
        "schema_version": SCHEMA_VERSION,
        "planner_status": planner_status,
        "acquisition_boundary_status": boundary_status,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "candidate_selection_rationale": selection_rationale or "site selection remains blocked or unspecified",
        "site_extent": site_extent if site_extent else "placeholder_extent_missing",
        "acquisition_manifest_path": str(acquisition_manifest_path),
        "acquisition_manifest_status": "ready" if acquisition_manifest_path.exists() else "blocked_missing_inputs",
        "public_context_acquisition_summary": PREFLIGHT.build_public_context_acquisition_summary(public_context_acquisition_plan),
        "public_context_acquisition_plan": public_context_acquisition_plan,
        "aoi_tile_discovery": aoi_tile_discovery,
        "public_geodata_workflow_contract": workflow_contract,
        "required_public_geodata_products": product_rows,
        "required_metadata_records": metadata_rows,
        "expected_staging_paths": expected_staging_paths,
        "unresolved_acquisition_decisions": unresolved_acquisition_decisions,
        "deferred_public_context_categories": boundary_categories,
        "deferred_public_context_status": boundary_status,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def metadata_category_set() -> set[str]:
    return {
        "aoi_tile_catalog",
        "terrain_metadata",
        "swisstlm3d_metadata",
        "source_zone_metadata",
        "scenario_table",
        "source_scenario_policy",
        "release_observation_evidence",
    }


def current_status(category: str, required: bool, staged: bool) -> str:
    if staged:
        return "ready"
    if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES:
        return "deferred_public_context"
    if required:
        return "missing"
    return "optional"


def decision_type(category: str, required: bool) -> str:
    if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES:
        return "deferred_public_context_staging"
    if required:
        return "required_metadata_or_product_staging"
    return "optional_acquisition_choice"


def should_record_unresolved(category: str, required: bool, staged: bool) -> bool:
    if staged:
        return False
    if category == "barrier_inventory":
        return False
    return required or category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES


def acquisition_boundary_status(product_rows: list[dict[str, Any]]) -> str:
    core_missing = [
        row
        for row in product_rows
        if row["required"] and row["category"] not in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and row["current_status"] != "ready"
    ]
    if core_missing:
        return "blocked_missing_inputs"
    deferred_missing = [
        row
        for row in product_rows
        if row["required"] and row["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and row["current_status"] != "ready"
    ]
    if deferred_missing:
        return "deferred_public_context_inputs"
    return "ready"


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"planner_status: {report['planner_status']}",
        f"acquisition_boundary_status: {report['acquisition_boundary_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        "",
        "public_geodata_workflow_contract:",
    ]
    lines.extend(PREFLIGHT._render_public_geodata_workflow_contract(report["public_geodata_workflow_contract"]))
    lines.extend([
        "",
        "site_extent:",
    ])
    site_extent = report["site_extent"]
    if isinstance(site_extent, dict):
        for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
            if key in site_extent:
                lines.append(f"  {key}: {site_extent[key]}")
    else:
        lines.append(f"  {site_extent}")

    lines.append("")
    lines.append("public_context_acquisition_summary:")
    if report.get("public_context_acquisition_summary"):
        for key, value in report["public_context_acquisition_summary"].items():
            if isinstance(value, list):
                lines.append(f"- {key}: {', '.join(value) if value else 'none'}")
            elif isinstance(value, dict):
                lines.append(f"- {key}:")
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, list):
                        lines.append(f"  - {subkey}: {', '.join(subvalue) if subvalue else 'none'}")
                    else:
                        lines.append(f"  - {subkey}: {subvalue}")
            else:
                lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("public_context_acquisition_plan:")
    lines.extend(render_acquisition_plan_rows(report.get("public_context_acquisition_plan") or []))
    lines.append("")
    lines.append("aoi_tile_discovery:")
    lines.extend(render_aoi_tile_discovery_rows(report.get("aoi_tile_discovery") or {}))
    lines.append("")
    lines.append("required_public_geodata_products:")
    lines.extend(render_rows(report["required_public_geodata_products"]))

    lines.append("")
    lines.append("required_metadata_records:")
    lines.extend(render_rows(report["required_metadata_records"]))

    lines.append("")
    lines.append("expected_staging_paths:")
    for category, path in report["expected_staging_paths"].items():
        lines.append(f"- {category}: {path}")

    lines.append("")
    lines.append("unresolved_acquisition_decisions:")
    lines.extend(render_decision_rows(report["unresolved_acquisition_decisions"]))

    lines.append("")
    lines.append("deferred_public_context_categories:")
    lines.extend(f"- {category}" for category in report["deferred_public_context_categories"])
    return "\n".join(lines)


def render_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: product={row['product']}, required={row['required']}, "
            f"current_status={row['current_status']}, expected_staged_path={row['expected_staged_path']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_acquisition_plan_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: {row['current_status']}, "
            f"staging_root={row['expected_staging_root']}, "
            f"expected_staged_path={row['expected_staged_path']}, "
            f"metadata_contract={', '.join(row['metadata_contract'])}, "
            f"staging_mode={row['staging_mode']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_aoi_tile_discovery_rows(report: dict[str, Any]) -> list[str]:
    if not report:
        return ["- none"]
    rendered = [
        f"- schema_version: {report.get('schema_version', '')}",
        f"- discovery_status: {report.get('discovery_status', '')}",
        f"- resolver_status: {report.get('resolver_status', '')}",
        f"- catalog_path: {report.get('catalog_path', '')}",
        f"- catalog_status: {report.get('catalog_status', '')}",
        f"- catalog_blockers: {', '.join(report.get('catalog_blockers') or []) if report.get('catalog_blockers') else 'none'}",
        f"- catalog_manifest: {report.get('catalog_manifest', {})}",
        f"- tile_catalog_status: {report.get('tile_catalog_status', '')}",
        f"- tile_candidate_count: {report.get('tile_candidate_count', 0)}",
        f"- product_candidate_count: {report.get('product_candidate_count', 0)}",
    ]
    if report.get("missing_catalog_inputs"):
        rendered.append("- missing_catalog_inputs:")
        rendered.extend(f"  - {item}" for item in report["missing_catalog_inputs"])
    else:
        rendered.append("- missing_catalog_inputs: none")
    if report.get("tile_candidates"):
        rendered.append("- tile_candidates:")
        for entry in report["tile_candidates"]:
            rendered.append(
                f"  - {entry.get('tile_id', '')}: product_id={entry.get('product_id', '')}, "
                f"source_product={entry.get('source_product', '')}, resolution_m={entry.get('resolution_m', '')}, "
                f"crs={entry.get('crs', '')}, source_filename={entry.get('source_filename', '')}"
            )
    else:
        rendered.append("- tile_candidates: none")
    if report.get("product_candidates"):
        rendered.append("- product_candidates:")
        for entry in report["product_candidates"]:
            rendered.append(
                f"  - {entry.get('product_id', '')}: tile_ids={', '.join(entry.get('tile_ids') or []) or 'none'}, "
                f"resolution_m={entry.get('resolution_m', '')}, crs={entry.get('crs', '')}, "
                f"expected_staging_root={entry.get('expected_staging_root', '')}"
            )
    else:
        rendered.append("- product_candidates: none")
    if report.get("required_products"):
        rendered.append("- required_products:")
        for entry in report["required_products"]:
            rendered.append(
                f"  - {entry.get('category', '')}: {entry.get('coverage_descriptor', '')}, "
                f"staging_root={entry.get('expected_staging_root', '')}, "
                f"tile_candidate_count={entry.get('tile_candidate_count', 0)}, "
                f"product_candidate_count={entry.get('product_candidate_count', 0)}"
            )
    else:
        rendered.append("- required_products: none")
    if report.get("product_resolution_rows"):
        rendered.append("- product_resolution_rows:")
        for entry in report["product_resolution_rows"]:
            rendered.append(
                f"  - {entry.get('product_label', '')}: tile_resolution_status={entry.get('tile_resolution_status', '')}, "
                f"expected_tile_ids={', '.join(entry.get('expected_tile_ids') or []) or 'none'}, "
                f"raw_path={entry.get('raw_path', '')}, processed_path={entry.get('processed_path', '')}, "
                f"blockers={', '.join(entry.get('tile_blockers') or []) or 'none'}"
            )
    else:
        rendered.append("- product_resolution_rows: none")
    rendered.append("- no_download_boundary:")
    for key, value in (report.get("no_download_boundary") or {}).items():
        rendered.append(f"  - {key}: {value}")
    return rendered


def render_decision_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['decision_id']}: category={row['category']}, decision_type={row['decision_type']}, "
            f"current_status={row['current_status']}, expected_staged_path={row['expected_staged_path']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


if __name__ == "__main__":
    raise SystemExit(main())
