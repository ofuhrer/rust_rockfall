#!/usr/bin/env python3
"""Plan swisstopo acquisition needs from a small AOI/site config.

The helper supports a read-only dry run and an explicit-acquire package
materialization mode. It does not download public geodata, stage raw swisstopo
products, or authorize any ensemble work. Instead, it translates a candidate
AOI/site configuration into the public swisstopo product categories, expected
staging paths, tile manifests, and unresolved acquisition decisions that still
need a real staging choice.
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
ACQUISITION_COMMAND_SET_SCHEMA_VERSION = "swisstopo_aoi_acquisition_command_set_v1"
ACQUISITION_MODES = {"dry-run", "explicit-acquire"}
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
    parser.add_argument("--mode", choices=sorted(ACQUISITION_MODES), default="dry-run")
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, mode=args.mode, output_root=args.output_root)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["planner_status"] == "ready" else 2


def build_report(
    site_config: Path | None,
    site_id: str | None = None,
    *,
    mode: str = "dry-run",
    output_root: Path | None = None,
) -> dict[str, Any]:
    if mode not in ACQUISITION_MODES:
        raise ValueError(f"unsupported acquisition mode: {mode}")
    config = PREFLIGHT.load_site_config(site_config) if site_config is not None and site_config.exists() else {}
    config_base = site_config.parent if site_config is not None else ROOT

    candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or site_id or "unspecified_second_site"
    candidate_site_id = candidate_site_id.strip()
    candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
    selection_rationale = PREFLIGHT.text_value(config.get("candidate_selection_rationale"))
    site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}
    aoi_definition_status, aoi_definition_blockers = classify_aoi_definition(candidate_site_id, site_extent)

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
    tile_manifest = build_tile_manifest(candidate_site_id, candidate_site_name, site_extent, aoi_tile_discovery)
    product_manifest = build_product_manifest(candidate_site_id, candidate_site_name, public_context_acquisition_plan, aoi_tile_discovery)
    acquisition_command_set = build_acquisition_command_set(acquisition_report)
    generated_root_warnings = build_generated_root_warnings(candidate_site_id, paths, acquisition_manifest, repo_root=PREFLIGHT.ROOT)
    acquisition_package_paths: dict[str, str] = {}
    acquisition_package_status = "not_requested"
    if mode == "explicit-acquire":
        if aoi_definition_status == "ready" and acquisition_manifest_path.exists() and aoi_tile_discovery.get("discovery_status") != "blocked_missing_inputs":
            resolved_output_root = resolve_acquisition_output_root(
                output_root or paths["processed_input_root"],
                repo_root=PREFLIGHT.ROOT,
            )
            acquisition_package_paths = materialize_explicit_acquisition_package(
                output_root=resolved_output_root,
                repo_root=PREFLIGHT.ROOT,
                report_base={
                    "candidate_site_id": candidate_site_id,
                    "candidate_site_name": candidate_site_name,
                    "site_extent": site_extent,
                    "acquisition_manifest": acquisition_manifest,
                    "aoi_tile_discovery": aoi_tile_discovery,
                    "public_geodata_workflow_contract": workflow_contract,
                    "tile_manifest": tile_manifest,
                    "product_manifest": product_manifest,
                },
                acquisition_manifest=acquisition_manifest,
                aoi_tile_discovery=aoi_tile_discovery,
                public_context_acquisition_plan=public_context_acquisition_plan,
            )
            acquisition_package_status = "materialized"
        else:
            acquisition_package_status = "blocked_missing_inputs"

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
    if aoi_definition_status != "ready":
        planner_status = "blocked_missing_inputs"
    elif not acquisition_manifest_path.exists():
        planner_status = "blocked_missing_inputs"
    elif acquisition_report.get("aoi_tile_discovery", {}).get("discovery_status") == "blocked_missing_inputs":
        planner_status = "blocked_missing_inputs"

    report = {
        "schema_version": SCHEMA_VERSION,
        "acquisition_mode": mode,
        "planner_status": planner_status,
        "acquisition_boundary_status": boundary_status,
        "aoi_definition_status": aoi_definition_status,
        "aoi_definition_blockers": aoi_definition_blockers,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "candidate_selection_rationale": selection_rationale or "site selection remains blocked or unspecified",
        "site_extent": site_extent if site_extent else "placeholder_extent_missing",
        "acquisition_manifest_path": str(acquisition_manifest_path),
        "acquisition_manifest_status": "ready" if acquisition_manifest_path.exists() else "blocked_missing_inputs",
        "acquisition_package_status": acquisition_package_status,
        "acquisition_package_paths": acquisition_package_paths,
        "public_context_acquisition_summary": PREFLIGHT.build_public_context_acquisition_summary(public_context_acquisition_plan),
        "public_context_acquisition_plan": public_context_acquisition_plan,
        "aoi_tile_discovery": aoi_tile_discovery,
        "tile_manifest": tile_manifest,
        "product_manifest": product_manifest,
        "acquisition_command_set": acquisition_command_set,
        "public_geodata_workflow_contract": workflow_contract,
        "required_public_geodata_products": product_rows,
        "required_metadata_records": metadata_rows,
        "expected_staging_paths": expected_staging_paths,
        "unresolved_acquisition_decisions": unresolved_acquisition_decisions,
        "deferred_public_context_categories": boundary_categories,
        "deferred_public_context_status": boundary_status,
        "generated_root_warnings": generated_root_warnings,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_acquisition_command_set(report: dict[str, Any]) -> dict[str, Any]:
    workflow_contract = report.get("public_geodata_workflow_contract") or {}
    cache_contract = workflow_contract.get("public_geodata_cache_contract") or {}
    cache_layout = cache_contract.get("cache_layout") or {}
    stage_commands = list(cache_contract.get("stage_commands") or [])
    verify_commands = list(cache_contract.get("verify_commands") or [])
    product_rows = []
    for row in report.get("aoi_tile_discovery", {}).get("product_resolution_rows") or []:
        product_rows.append(
            {
                "product_id": row.get("source_product_id", ""),
                "product_label": row.get("product_label", ""),
                "category": row.get("category", ""),
                "expected_local_root": row.get("expected_staging_root", ""),
                "expected_staged_path": row.get("processed_path", ""),
                "expected_tile_ids": row.get("expected_tile_ids", []),
                "source_url_or_download_record": row.get("source_url_or_download_record", ""),
                "staging_mode": row.get("tile_resolution_strategy", ""),
            }
        )

    return {
        "schema_version": ACQUISITION_COMMAND_SET_SCHEMA_VERSION,
        "candidate_site_id": report.get("candidate_site_id", ""),
        "candidate_site_name": report.get("candidate_site_name", ""),
        "site_extent": report.get("site_extent", "placeholder_extent_missing"),
        "cache_manifest_path": cache_layout.get("cache_manifest_path", ""),
        "dry_run_stage_command": stage_commands[0]["command"] if len(stage_commands) > 0 else "",
        "local_copy_stage_command": stage_commands[1]["command"] if len(stage_commands) > 1 else "",
        "download_stage_command": stage_commands[2]["command"] if len(stage_commands) > 2 else "",
        "cache_verification_command": verify_commands[0]["command"] if verify_commands else "",
        "stage_commands": stage_commands,
        "verify_commands": verify_commands,
        "products": product_rows,
    }


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


def classify_aoi_definition(candidate_site_id: str, site_extent: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not candidate_site_id or candidate_site_id == "unspecified_second_site":
        blockers.append("missing AOI candidate_site_id")
    if not isinstance(site_extent, dict) or not site_extent:
        blockers.append("missing AOI site_extent")
        return ("blocked_missing_inputs", blockers)
    if PREFLIGHT.text_value(site_extent.get("crs")) != "EPSG:2056":
        blockers.append("site_extent.crs must be EPSG:2056")
    for key in ("xmin", "ymin", "xmax", "ymax"):
        if key not in site_extent or site_extent.get(key) in (None, ""):
            blockers.append(f"site_extent.{key} is required")
    return ("ready" if not blockers else "blocked_missing_inputs", blockers)


def build_tile_manifest(
    candidate_site_id: str,
    candidate_site_name: str,
    site_extent: dict[str, Any],
    aoi_tile_discovery: dict[str, Any],
) -> dict[str, Any]:
    tile_candidates = aoi_tile_discovery.get("tile_candidates") or []
    return {
        "schema_version": "swisstopo_aoi_tile_manifest_v1",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_extent": site_extent if site_extent else "placeholder_extent_missing",
        "tile_candidate_count": len(tile_candidates),
        "tile_ids": [entry.get("tile_id", "") for entry in tile_candidates if entry.get("tile_id")],
        "tiles": [
            {
                "tile_id": entry.get("tile_id", ""),
                "product_id": entry.get("product_id", ""),
                "source_product": entry.get("source_product", ""),
                "resolution_m": entry.get("resolution_m", ""),
                "crs": entry.get("crs", ""),
                "source_filename": entry.get("source_filename", ""),
                "source_url": entry.get("source_url", ""),
            }
            for entry in tile_candidates
        ],
    }


def build_product_manifest(
    candidate_site_id: str,
    candidate_site_name: str,
    public_context_acquisition_plan: list[dict[str, Any]],
    aoi_tile_discovery: dict[str, Any],
) -> dict[str, Any]:
    terrain_rows = []
    for row in aoi_tile_discovery.get("product_resolution_rows") or []:
        terrain_rows.append(
            {
                "product_label": row.get("product_label", ""),
                "category": row.get("category", ""),
                "source_product_id": row.get("source_product_id", ""),
                "source_product_name": row.get("source_product_name", ""),
                "source_url_or_download_record": row.get("source_url_or_download_record", ""),
                "product_version_or_date": row.get("product_version_or_date", ""),
                "license_or_terms_reference": row.get("license_or_terms_reference", ""),
                "expected_tile_ids": row.get("expected_tile_ids", []),
                "expected_staged_path": row.get("processed_path", ""),
                "expected_staging_root": row.get("expected_staging_root", ""),
                "resolver_status": row.get("resolver_status", ""),
                "tile_resolution_status": row.get("tile_resolution_status", ""),
                "tile_blockers": row.get("tile_blockers", []),
            }
        )
    return {
        "schema_version": "swisstopo_aoi_public_geodata_product_manifest_v1",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "products": [
            {
                "category": entry.get("category", ""),
                "product": entry.get("product", ""),
                "required": entry.get("required", False),
                "current_status": entry.get("current_status", ""),
                "expected_staged_path": entry.get("expected_staged_path", ""),
                "expected_staging_root": entry.get("expected_staging_root", ""),
                "source_reference": entry.get("source_reference", ""),
                "notes": entry.get("notes", ""),
                "metadata_contract": entry.get("metadata_contract", []),
                "staging_mode": entry.get("staging_mode", ""),
            }
            for entry in public_context_acquisition_plan
        ],
        "terrain_rows": terrain_rows,
    }


def build_generated_root_warnings(
    candidate_site_id: str,
    paths: dict[str, Path],
    acquisition_manifest: dict[str, Any],
    *,
    repo_root: Path,
) -> list[str]:
    raw_cache_root = repo_root / "data" / "raw" / "swisstopo" / candidate_site_id
    validation_root = paths.get("validation_private_root") or paths["validation_case_root"]
    warnings = [
        f"do not commit generated AOI acquisition outputs under {paths['processed_input_root']}",
        f"do not commit generated AOI context outputs under {paths['processed_context_root']}",
        f"do not commit generated validation outputs under {validation_root}",
        f"do not commit generated hazard outputs under {paths['hazard_results_root']}",
        f"do not commit raw swisstopo inputs under {raw_cache_root}",
    ]
    for root in acquisition_manifest.get("expected_ignored_output_roots") or []:
        warnings.append(f"keep ignored output root untracked: {root}")
    return warnings


def resolve_acquisition_output_root(output_root: Path, *, repo_root: Path) -> Path:
    resolved = output_root if output_root.is_absolute() else repo_root / output_root
    if not is_allowed_acquisition_output_root(resolved, repo_root):
        raise ValueError(f"acquisition output root must stay under /tmp or ignored AOI roots: {resolved}")
    return resolved


def is_allowed_acquisition_output_root(output_root: Path, repo_root: Path) -> bool:
    resolved = output_root.resolve()
    allowed_roots = [
        Path("/tmp").resolve(),
        (repo_root / "data/processed/swisstopo").resolve(),
        (repo_root / "validation/private").resolve(),
        (repo_root / "hazard/results").resolve(),
    ]
    return any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots)


def materialize_explicit_acquisition_package(
    *,
    output_root: Path,
    repo_root: Path,
    report_base: dict[str, Any],
    acquisition_manifest: dict[str, Any],
    aoi_tile_discovery: dict[str, Any],
    public_context_acquisition_plan: list[dict[str, Any]],
) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    plan_json_path = output_root / "public_geodata_acquisition_plan.json"
    plan_yaml_path = output_root / "public_geodata_acquisition_plan.yaml"
    cache_manifest_path = output_root / "public_geodata_cache_manifest.yaml"
    plan_payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate_site_id": report_base["candidate_site_id"],
        "candidate_site_name": report_base["candidate_site_name"],
        "site_extent": report_base["site_extent"],
        "tile_manifest": report_base["tile_manifest"],
        "product_manifest": report_base["product_manifest"],
        "generated_root_warnings": build_generated_root_warnings(
            report_base["candidate_site_id"],
            {
                "processed_input_root": output_root,
                "processed_context_root": repo_root / "data" / "processed" / "swisstopo" / report_base["candidate_site_id"] / "context",
                "validation_private_root": repo_root / "validation" / "private" / report_base["candidate_site_id"],
                "hazard_results_root": repo_root / "hazard" / "results" / report_base["candidate_site_id"],
                "validation_case_root": repo_root / "validation" / "private" / report_base["candidate_site_id"],
            },
            acquisition_manifest,
            repo_root=repo_root,
        ),
        "public_geodata_workflow_contract": report_base["public_geodata_workflow_contract"],
        "aoi_tile_discovery": aoi_tile_discovery,
        "public_context_acquisition_plan": public_context_acquisition_plan,
    }
    plan_json_path.write_text(json.dumps(plan_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan_yaml_path.write_text(yaml.safe_dump(plan_payload, sort_keys=False), encoding="utf-8")

    cache_manifest_template = PREFLIGHT.build_public_geodata_cache_manifest_template(
        candidate_site_id=report_base["candidate_site_id"],
        candidate_site_name=report_base["candidate_site_name"],
        paths={
            "processed_input_root": output_root,
            "processed_context_root": repo_root / "data" / "processed" / "swisstopo" / report_base["candidate_site_id"] / "context",
            "validation_case_root": repo_root / "validation" / "private" / report_base["candidate_site_id"],
            "hazard_results_root": repo_root / "hazard" / "results" / report_base["candidate_site_id"],
        },
        acquisition_manifest=acquisition_manifest,
        aoi_tile_discovery=aoi_tile_discovery,
    )
    cache_manifest_path.write_text(yaml.safe_dump(cache_manifest_template, sort_keys=False), encoding="utf-8")
    return {
        "output_root": str(output_root),
        "public_geodata_acquisition_plan_json": str(plan_json_path),
        "public_geodata_acquisition_plan_yaml": str(plan_yaml_path),
        "public_geodata_cache_manifest_yaml": str(cache_manifest_path),
    }


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
        f"acquisition_mode: {report['acquisition_mode']}",
        f"planner_status: {report['planner_status']}",
        f"acquisition_boundary_status: {report['acquisition_boundary_status']}",
        f"aoi_definition_status: {report['aoi_definition_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        f"acquisition_package_status: {report['acquisition_package_status']}",
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
    lines.append("tile_manifest:")
    lines.extend(render_manifest_rows(report.get("tile_manifest") or {}))
    lines.append("")
    lines.append("product_manifest:")
    lines.extend(render_manifest_rows(report.get("product_manifest") or {}))
    lines.append("")
    lines.append("acquisition_command_set:")
    lines.extend(render_acquisition_command_set_rows(report.get("acquisition_command_set") or {}))
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
    lines.append("")
    lines.append("generated_root_warnings:")
    lines.extend(f"- {warning}" for warning in report["generated_root_warnings"])
    if report.get("acquisition_package_paths"):
        lines.append("")
        lines.append("acquisition_package_paths:")
        for key, path in report["acquisition_package_paths"].items():
            lines.append(f"- {key}: {path}")
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


def render_manifest_rows(report: dict[str, Any]) -> list[str]:
    if not report:
        return ["- none"]
    rendered = [f"- schema_version: {report.get('schema_version', '')}"]
    for key in ("candidate_site_id", "candidate_site_name", "tile_candidate_count"):
        if key in report:
            rendered.append(f"- {key}: {report.get(key, '')}")
    if report.get("site_extent"):
        rendered.append("- site_extent:")
        site_extent = report["site_extent"]
        if isinstance(site_extent, dict):
            for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
                if key in site_extent:
                    rendered.append(f"  - {key}: {site_extent[key]}")
        else:
            rendered.append(f"  - {site_extent}")
    if report.get("tile_ids"):
        rendered.append(f"- tile_ids: {', '.join(report['tile_ids'])}")
    if report.get("tiles"):
        rendered.append("- tiles:")
        for entry in report["tiles"]:
            rendered.append(
                f"  - {entry.get('tile_id', '')}: product_id={entry.get('product_id', '')}, "
                f"resolution_m={entry.get('resolution_m', '')}, crs={entry.get('crs', '')}, "
                f"source_url={entry.get('source_url', '')}"
            )
    if report.get("products"):
        rendered.append("- products:")
        for entry in report["products"]:
            rendered.append(
                f"  - {entry.get('category', '')}: product={entry.get('product', '')}, "
                f"current_status={entry.get('current_status', '')}, "
                f"expected_staged_path={entry.get('expected_staged_path', '')}"
            )
    if report.get("terrain_rows"):
        rendered.append("- terrain_rows:")
        for entry in report["terrain_rows"]:
            rendered.append(
                f"  - {entry.get('product_label', '')}: source_product_id={entry.get('source_product_id', '')}, "
                f"source_url_or_download_record={entry.get('source_url_or_download_record', '')}"
            )
    return rendered


def render_acquisition_command_set_rows(report: dict[str, Any]) -> list[str]:
    if not report:
        return ["- none"]
    products = list(report.get("products") or [])
    rendered = [
        f"- schema_version: {report.get('schema_version', '')}",
        f"- candidate_site_id: {report.get('candidate_site_id', '')}",
        f"- candidate_site_name: {report.get('candidate_site_name', '')}",
        f"- cache_manifest_path: {report.get('cache_manifest_path', '')}",
        f"- dry_run_stage_command: {report.get('dry_run_stage_command', '')}",
        f"- local_copy_stage_command: {report.get('local_copy_stage_command', '')}",
        f"- download_stage_command: {report.get('download_stage_command', '')}",
        f"- cache_verification_command: {report.get('cache_verification_command', '')}",
        "- stage_commands:",
    ]
    for entry in report.get("stage_commands") or []:
        rendered.append(f"  - {entry.get('command_id', '')}: {entry.get('command', '')}")
    rendered.append("- verify_commands:")
    for entry in report.get("verify_commands") or []:
        rendered.append(f"  - {entry.get('command_id', '')}: {entry.get('command', '')}")
    if products:
        rendered.append("- products:")
        for entry in products:
            rendered.append(
                f"  - {entry.get('product_id', '')}: product_label={entry.get('product_label', '')}, "
                f"category={entry.get('category', '')}, expected_local_root={entry.get('expected_local_root', '')}, "
                f"expected_staged_path={entry.get('expected_staged_path', '')}, expected_tile_ids={', '.join(entry.get('expected_tile_ids') or []) or 'none'}"
            )
    else:
        rendered.append("- products: none")
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
