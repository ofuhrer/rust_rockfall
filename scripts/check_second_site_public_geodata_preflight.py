#!/usr/bin/env python3
"""Check what a second Swiss public-geodata site would need before porting Tschamut.

The preflight is metadata-only and read-only. It does not download data,
generate cases, run ensembles, or create a new acceptance gate. Instead, it
identifies which pieces of the current Tschamut workflow are reusable and
which site-specific public-geodata inputs still need to be staged for another
Swiss site.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "second_site_public_geodata_preflight_v1"
PUBLIC_GEODATA_WORKFLOW_CONTRACT_SCHEMA_VERSION = "swiss_public_geodata_workflow_contract_v1"
DEFAULT_CANDIDATE_SITE_ID = "unspecified_second_site"
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
}

PUBLIC_CONTEXT_ACQUISITION_PLAN_CATEGORIES = [
    "swissimage_context",
    "swisstlm3d_context",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
]

PUBLIC_CONTEXT_PRODUCT_METADATA_REQUIREMENTS = {
    "swissimage_context": [
        "expected_staged_path",
        "site-specific product record or download reference when staged",
    ],
    "swisstlm3d_context": [
        "expected_staged_path",
        "archive or delivery reference when staged",
    ],
    "swisstlm3d_metadata": [
        "metadata.json",
        "source_product",
        "staged_asset_present",
    ],
    "swisssurface3d_context": [
        "expected_staged_path",
        "site-specific product record when staged",
    ],
    "swisssurface3d_raster_context": [
        "expected_staged_path",
        "site-specific product record when staged",
    ],
    "swissbuildings3d_context": [
        "expected_staged_path",
        "site-specific product record when staged",
    ],
    "barrier_inventory": [
        "expected_staged_path",
        "only if a site policy explicitly references barriers or nets",
    ],
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=None, help="optional site config YAML")
    parser.add_argument("--site-id", type=str, default=None, help="optional site id override")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, site_id=args.site_id)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["portability_preflight_status"] == "ready" else 2


def build_report(site_config: Path | None, site_id: str | None = None) -> dict[str, Any]:
    config = load_site_config(site_config) if site_config is not None and site_config.exists() else {}
    config_base = site_config.parent if site_config is not None else ROOT
    candidate_site_id = text_value(config.get("candidate_site_id")) or site_id or DEFAULT_CANDIDATE_SITE_ID
    candidate_site_id = candidate_site_id.strip()
    candidate_site_name = text_value(config.get("candidate_site_name")) or "unspecified"
    candidate_selection_rationale = text_value(config.get("candidate_selection_rationale"))
    site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}
    source_zone_scenario_contract = (
        config.get("source_zone_scenario_contract")
        if isinstance(config.get("source_zone_scenario_contract"), dict)
        else {}
    )
    fixture_profile = text_value(config.get("fixture_profile"))
    default_acquisition_manifest = (
        (site_config.parent if site_config is not None else ROOT / "tests/fixtures/second_site_public_geodata_preflight")
        / "chant_sura_fluelapass_public_geodata_acquisition.yaml"
    )
    acquisition_manifest_path = resolve_repo_path(
        config.get("acquisition_manifest_path"),
        default_acquisition_manifest,
        base=config_base,
    )
    acquisition_manifest = load_site_config(acquisition_manifest_path) if acquisition_manifest_path.exists() else {}

    paths = build_paths(candidate_site_id, config)
    requirements = build_requirements(candidate_site_id, site_extent, paths)
    missing_required = [
        req
        for req in requirements
        if req["required"]
        and req["status"] != "ready"
        and req["category"] not in DEFERRED_PUBLIC_CONTEXT_CATEGORIES
    ]
    deferred_required = [
        req for req in requirements if req["required"] and req["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and req["status"] != "ready"
    ]
    terrain_manifest_status = manifest_status(paths["terrain_crop"], paths["terrain_metadata"])
    source_zone_manifest_status = manifest_status(paths["source_zone_metadata"])
    scenario_manifest_status = manifest_status(paths["scenario_table"], paths["source_scenario_policy"])
    public_context_acquisition_plan = build_public_context_acquisition_plan(acquisition_manifest, requirements)
    core_input_status = "ready" if not missing_required else "blocked_missing_inputs"
    deferred_context_status = "deferred_public_context_inputs" if deferred_required and not missing_required else "ready"
    overall_status = "ready" if not missing_required and not deferred_required else deferred_context_status if not missing_required else core_input_status

    report = {
        "second_site_manifest_status": (
            "staged_candidate_manifest"
            if candidate_selection_rationale
            else "staged_placeholder_manifest"
            if site_config is not None and site_config.exists()
            else "missing_manifest_config"
        ),
        "portability_preflight_status": overall_status,
        "readiness_status": overall_status,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "candidate_selection_rationale": candidate_selection_rationale or "site selection remains blocked or unspecified",
        "site_extent_or_placeholder": site_extent if site_extent else "placeholder_extent_missing",
        "core_input_status": core_input_status,
        "deferred_public_context_status": deferred_context_status,
        "public_context_boundary_status": build_public_context_boundary_status(missing_required, deferred_required),
        "terrain_manifest_status": terrain_manifest_status,
        "source_zone_manifest_status": source_zone_manifest_status,
        "scenario_manifest_status": scenario_manifest_status,
        "acquisition_manifest_status": "ready" if acquisition_manifest_path.exists() else "blocked_missing_inputs",
        "acquisition_manifest_path": str(acquisition_manifest_path),
        "acquisition_manifest_category_count": len(acquisition_manifest.get("expected_products") or []),
        "acquisition_manifest_expected_ignored_roots": acquisition_manifest.get("expected_ignored_output_roots") or [],
        "acquisition_manifest_command_template_count": len(acquisition_manifest.get("command_templates") or []),
        "public_context_acquisition_summary": build_public_context_acquisition_summary(public_context_acquisition_plan),
        "public_context_acquisition_plan": public_context_acquisition_plan,
        "public_geodata_workflow_contract": build_public_geodata_workflow_contract(
            candidate_site_id=candidate_site_id,
            candidate_site_name=candidate_site_name,
            site_extent=site_extent,
            paths=paths,
            source_zone_scenario_contract=source_zone_scenario_contract,
            fixture_profile=fixture_profile,
        ),
        "acquisition_manifest_product_summaries": [
            {
                "category": entry.get("category"),
                "product": entry.get("product"),
                "status": entry.get("status"),
                "required": entry.get("required"),
                "expected_staged_path": entry.get("expected_staged_path"),
                "expected_staging_root": entry.get("expected_staging_root"),
                "metadata_contract": entry.get("metadata_contract"),
                "staging_mode": entry.get("staging_mode"),
                "current_status": entry.get("current_status"),
            }
            for entry in acquisition_manifest.get("expected_products") or []
            if isinstance(entry, dict)
        ],
        "source_zone_scenario_contract": source_zone_scenario_contract,
        "reusable_workflow_components": reusable_workflow_components(),
        "site_specific_required_inputs": [req for req in requirements if req["required"]],
        "required_public_geodata_products": [req for req in requirements if req["kind"] == "public_geodata_product"],
        "required_metadata_records": [req for req in requirements if req["kind"] == "metadata_record"],
        "required_case_generation_inputs": [req for req in requirements if req["kind"] == "case_generation_input"],
        "expected_artifact_roots": [req for req in requirements if req["kind"] == "artifact_root"],
        "public_context_product_requirements": build_public_context_product_requirements(acquisition_manifest, requirements),
        "expected_local_paths": build_expected_local_paths(requirements),
        "metadata_requirements": build_metadata_requirements(site_extent, requirements),
        "synthetic_fixture_boundaries": synthetic_fixture_boundaries(),
        "blocked_second_site_commands": build_blocked_second_site_commands(acquisition_manifest),
        "claim_boundaries": claim_boundaries(),
        "missing_input_categories": [req["category"] for req in missing_required],
        "missing_input_paths_or_patterns": [req["path_or_pattern"] for req in missing_required],
        "deferred_public_context_categories": [req["category"] for req in deferred_required],
        "deferred_public_context_paths_or_patterns": [req["path_or_pattern"] for req in deferred_required],
        "deferred_public_context_references": {
            req["category"]: req["notes"] for req in deferred_required
        },
        "acquisition_or_staging_checklist": build_checklist(
            candidate_site_id,
            candidate_site_name,
            paths,
            site_extent,
            source_zone_scenario_contract,
            missing_required,
            deferred_required,
            candidate_selection_rationale,
            acquisition_manifest_path,
            public_context_acquisition_plan,
        ),
        "blocked_reason": build_blocked_reason(
            candidate_site_id, site_extent, missing_required, deferred_required, site_config
        ),
        "assumptions_not_yet_generalized": assumptions_not_yet_generalized(candidate_site_id),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_public_context_boundary_status(missing_required: list[dict[str, Any]], deferred_required: list[dict[str, Any]]) -> str:
    if missing_required:
        return "blocked_missing_inputs"
    if deferred_required:
        return "deferred_public_context_inputs"
    return "ready"


def build_public_context_product_requirements(
    acquisition_manifest: dict[str, Any],
    requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    requirement_by_category = {req["category"]: req for req in requirements}
    acquisition_plan_by_category = {
        entry["category"]: entry for entry in build_public_context_acquisition_plan(acquisition_manifest, requirements)
    }
    products: list[dict[str, Any]] = []
    for entry in acquisition_manifest.get("expected_products") or []:
        if not isinstance(entry, dict):
            continue
        category = text_value(entry.get("category"))
        requirement = requirement_by_category.get(category)
        expected_path = text_value(entry.get("expected_staged_path")) or (requirement or {}).get("path_or_pattern", "")
        notes = text_value(entry.get("notes"))
        resolved_path = resolve_repo_path(expected_path) if expected_path else None
        plan_entry = acquisition_plan_by_category.get(category, {})
        if resolved_path is not None and resolved_path.exists():
            current_status = "ready"
        elif category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES:
            current_status = "deferred_public_context"
        elif bool(entry.get("required")):
            current_status = "blocked_missing_inputs"
        else:
            current_status = text_value(entry.get("status")) or "optional"
        products.append(
            {
                "category": category,
                "product": text_value(entry.get("product")),
                "required": bool(entry.get("required")),
                "current_status": current_status,
                "expected_local_path": expected_path,
                "expected_staged_path": expected_path,
                "staged": is_staged_path(resolved_path) if resolved_path is not None else False,
                "synthetic_fixture_allowed": False if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES else bool(entry.get("required")),
                "metadata_requirements": PUBLIC_CONTEXT_PRODUCT_METADATA_REQUIREMENTS.get(category, ["expected_staged_path"]),
                "source_reference": text_value(entry.get("source_reference")),
                "notes": notes,
                "expected_staging_root": plan_entry.get("expected_staging_root"),
                "metadata_contract": plan_entry.get("metadata_contract"),
                "staging_mode": plan_entry.get("staging_mode"),
                "acquisition_mode": plan_entry.get("acquisition_mode"),
                "dry_run_status": plan_entry.get("dry_run_status"),
            }
        )
    return products


def build_public_context_acquisition_plan(
    acquisition_manifest: dict[str, Any],
    requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    requirement_by_category = {req["category"]: req for req in requirements}
    manifest_by_category: dict[str, dict[str, Any]] = {}
    for entry in acquisition_manifest.get("expected_products") or []:
        if isinstance(entry, dict) and text_value(entry.get("category")):
            manifest_by_category[text_value(entry.get("category"))] = entry

    plan: list[dict[str, Any]] = []
    for category in PUBLIC_CONTEXT_ACQUISITION_PLAN_CATEGORIES:
        entry = manifest_by_category.get(category, {})
        requirement = requirement_by_category.get(category, {})
        expected_path = text_value(entry.get("expected_staged_path")) or text_value(requirement.get("path_or_pattern"))
        if not expected_path:
            continue
        expected_path_obj = resolve_repo_path(expected_path)
        staging_root = expected_path_obj.parent if expected_path_obj.name == "metadata.json" else expected_path_obj
        current_status = (
            "ready"
            if expected_path_obj.exists() or is_staged_path(expected_path_obj)
            else "deferred_public_context"
        )
        if category not in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and current_status != "ready":
            current_status = "blocked_missing_inputs"
        plan.append(
            {
                "category": category,
                "product": text_value(entry.get("product")) or text_value(requirement.get("product")),
                "required": bool(entry.get("required", True)),
                "current_status": current_status,
                "expected_staged_path": expected_path,
                "expected_staging_root": str(staging_root),
                "metadata_contract": PUBLIC_CONTEXT_PRODUCT_METADATA_REQUIREMENTS.get(category, ["expected_staged_path"]),
                "staging_mode": "metadata_file" if expected_path_obj.name == "metadata.json" else "directory_bundle",
                "acquisition_mode": "dry_run_only",
                "dry_run_status": "deferred_public_context" if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES else "blocked_missing_inputs",
                "source_reference": text_value(entry.get("source_reference")),
                "notes": text_value(entry.get("notes")),
            }
        )
    return plan


def build_public_context_acquisition_summary(plan: list[dict[str, Any]]) -> dict[str, Any]:
    deferred = [entry["category"] for entry in plan if entry["current_status"] == "deferred_public_context"]
    ready = [entry["category"] for entry in plan if entry["current_status"] == "ready"]
    return {
        "product_count": len(plan),
        "ready_product_count": len(ready),
        "deferred_product_count": len(deferred),
        "ready_categories": ready,
        "deferred_categories": deferred,
        "expected_staging_roots": [entry["expected_staging_root"] for entry in plan],
        "metadata_contracts": {
            entry["category"]: entry["metadata_contract"] for entry in plan
        },
    }


def build_public_geodata_workflow_contract(
    *,
    candidate_site_id: str,
    candidate_site_name: str,
    site_extent: dict[str, Any],
    paths: dict[str, Path],
    source_zone_scenario_contract: dict[str, Any],
    fixture_profile: str,
) -> dict[str, Any]:
    aoi_extent_ready = bool(
        text_value(site_extent.get("crs"))
        and all(k in site_extent and site_extent[k] not in (None, "") for k in ("xmin", "ymin", "xmax", "ymax"))
    )
    contract_status = "ready" if aoi_extent_ready and candidate_site_id else "blocked_missing_inputs"
    if fixture_profile:
        synthetic_fixture_status = "ready"
    else:
        synthetic_fixture_status = "not_applicable"

    return {
        "schema_version": PUBLIC_GEODATA_WORKFLOW_CONTRACT_SCHEMA_VERSION,
        "public_geodata_contract_readiness_status": contract_status,
        "synthetic_fixture_readiness_status": synthetic_fixture_status,
        "synthetic_fixture_profile": fixture_profile or "none",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "required_aoi_metadata": build_required_aoi_metadata(site_extent, source_zone_scenario_contract),
        "crs_grid_assumptions": build_crs_grid_assumptions(site_extent),
        "swisstopo_product_classes": build_swisstopo_product_classes(),
        "cache_paths": build_cache_paths(candidate_site_id, paths),
        "provenance_requirements": build_provenance_requirements(),
        "deferred_optional_context": build_deferred_optional_context(paths),
        "claim_boundaries": claim_boundaries(),
    }


def build_required_aoi_metadata(
    site_extent: dict[str, Any],
    source_zone_scenario_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    extent_ready = bool(
        text_value(site_extent.get("crs"))
        and all(k in site_extent and site_extent[k] not in (None, "") for k in ("xmin", "ymin", "xmax", "ymax"))
    )
    return [
        {
            "field": "candidate_site_id",
            "required": True,
            "ready": True,
            "purpose": "stable site identifier for reusable AOI bookkeeping",
        },
        {
            "field": "candidate_site_name",
            "required": True,
            "ready": True,
            "purpose": "human-readable site label for report output and cache paths",
        },
        {
            "field": "site_extent.crs",
            "required": True,
            "ready": bool(text_value(site_extent.get("crs"))),
            "purpose": "AOI CRS must be explicit before any Swiss preprocessing",
        },
        {
            "field": "site_extent.xmin/ymin/xmax/ymax",
            "required": True,
            "ready": extent_ready,
            "purpose": "AOI bounds must be finite and metre-based before crop planning",
        },
        {
            "field": "source_zone_scenario_contract.source_zone_id_pattern",
            "required": True,
            "ready": bool(text_value(source_zone_scenario_contract.get("source_zone_id_pattern"))),
            "purpose": "release/source-zone family must be explicit before release planning",
        },
        {
            "field": "source_zone_scenario_contract.block_scenario_table",
            "required": True,
            "ready": bool(text_value(source_zone_scenario_contract.get("block_scenario_table"))),
            "purpose": "block/scenario semantics must be fixed before hazard generation",
        },
    ]


def build_crs_grid_assumptions(site_extent: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "assumption": "EPSG:2056 / LV95 horizontal coordinates",
            "required": True,
            "ready": bool(text_value(site_extent.get("crs")) == "EPSG:2056"),
        },
        {
            "assumption": "LN02 vertical datum unless explicitly transformed",
            "required": True,
            "ready": True,
        },
        {
            "assumption": "AOI bounds are finite metre coordinates",
            "required": True,
            "ready": bool(all(k in site_extent and site_extent[k] not in (None, "") for k in ("xmin", "ymin", "xmax", "ymax"))),
        },
        {
            "assumption": "terrain crop extent and output grid are site-specific and must be recorded before preprocessing",
            "required": True,
            "ready": True,
        },
        {
            "assumption": "resolution, nodata policy, and resampling method belong in terrain metadata, not implicit defaults",
            "required": True,
            "ready": True,
        },
    ]


def build_swisstopo_product_classes() -> list[dict[str, Any]]:
    return [
        {
            "class": "required_terrain",
            "required": True,
            "products": ["swissALTI3D"],
            "workflow_role": "terrain foundation for Swiss AOI preprocessing",
        },
        {
            "class": "required_metadata_records",
            "required": True,
            "products": ["terrain_metadata", "source_zone_metadata", "scenario_table", "source_scenario_policy"],
            "workflow_role": "metadata records that freeze the site-specific contract",
        },
        {
            "class": "deferred_optional_context",
            "required": False,
            "products": [
                "SWISSIMAGE",
                "swissTLM3D",
                "swissSURFACE3D",
                "swissSURFACE3D Raster",
                "swissBUILDINGS3D",
            ],
            "workflow_role": "context layers that remain optional until a site-specific QA or context need exists",
        },
        {
            "class": "optional_local_context",
            "required": False,
            "products": ["barrier_inventory", "validation_observations"],
            "workflow_role": "site-specific QA or protection context, only when explicitly available",
        },
    ]


def build_cache_paths(candidate_site_id: str, paths: dict[str, Path]) -> dict[str, str]:
    return {
        "raw_swisstopo_cache_root": str(ROOT / "data/raw/swisstopo" / candidate_site_id),
        "processed_input_root": str(paths["processed_input_root"]),
        "processed_context_root": str(paths["processed_context_root"]),
        "validation_private_root": str(paths["validation_case_root"]),
        "hazard_results_root": str(paths["hazard_results_root"]),
    }


def build_provenance_requirements() -> list[dict[str, Any]]:
    return [
        {
            "field": "source_product_name",
            "required": True,
            "purpose": "identify the exact swisstopo product family used for the AOI",
        },
        {
            "field": "product_version_or_date",
            "required": True,
            "purpose": "freeze the public product revision or delivery date when known",
        },
        {
            "field": "tile_id_or_delivery_identifier",
            "required": True,
            "purpose": "link the AOI crop back to the specific swisstopo source tiles",
        },
        {
            "field": "source_url_or_download_record",
            "required": True,
            "purpose": "record where the public geodata was acquired or documented",
        },
        {
            "field": "raw_checksum",
            "required": True,
            "purpose": "prove the raw input was not silently altered",
        },
        {
            "field": "processed_checksum",
            "required": True,
            "purpose": "track the cropped or converted output used by the workflow",
        },
        {
            "field": "license_or_terms_reference",
            "required": True,
            "purpose": "keep reuse and redistribution claims bounded by the source terms",
        },
        {
            "field": "preprocessing_command_and_timestamp",
            "required": True,
            "purpose": "make the crop or conversion step reproducible",
        },
    ]


def build_deferred_optional_context(paths: dict[str, Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for category in (
        "swissimage_context",
        "swisstlm3d_context",
        "swisssurface3d_context",
        "swisssurface3d_raster_context",
        "swissbuildings3d_context",
    ):
        expected_path = paths[category]
        staging_root = expected_path.parent if expected_path.name == "metadata.json" else expected_path
        entries.append(
            {
                "category": category,
                "product": {
                    "swissimage_context": "SWISSIMAGE",
                    "swisstlm3d_context": "swissTLM3D",
                    "swisssurface3d_context": "swissSURFACE3D",
                    "swisssurface3d_raster_context": "swissSURFACE3D Raster",
                    "swissbuildings3d_context": "swissBUILDINGS3D",
                }[category],
                "required": False,
                "expected_staged_path": str(expected_path),
                "expected_staging_root": str(staging_root),
                "status": "deferred_optional_context",
                "meaning": "context layers are intentionally deferred until the site-specific workflow asks for them",
            }
        )
    return entries


def build_expected_local_paths(requirements: list[dict[str, Any]]) -> dict[str, str]:
    return {
        req["category"]: req["path_or_pattern"]
        for req in requirements
        if req["kind"] in {"public_geodata_product", "metadata_record", "case_generation_input", "artifact_root"}
    }


def is_staged_path(path: Path) -> bool:
    return path.is_file() or (path.is_dir() and any(path.iterdir()))


def build_metadata_requirements(site_extent: dict[str, Any], requirements: list[dict[str, Any]]) -> dict[str, list[str]]:
    metadata: dict[str, list[str]] = {
        "site_extent_definition": ["crs", "xmin", "ymin", "xmax", "ymax"],
        "terrain_metadata": ["crs", "vertical_datum", "crop_provenance", "checksum"],
        "source_zone_metadata": ["source_zone_id or equivalent site-specific release-zone identifier"],
        "scenario_table": ["scenario_id", "probability", "site-specific scenario rows"],
        "source_scenario_policy": ["policy_id or equivalent site-specific policy identifier", "site-specific policy content"],
        "swisstlm3d_metadata": ["metadata.json", "source_product", "staged_asset_present"],
    }
    if site_extent:
        metadata["site_extent_definition"].append("declared candidate extent")
    for req in requirements:
        if req["category"] in PUBLIC_CONTEXT_PRODUCT_METADATA_REQUIREMENTS:
            metadata[req["category"]] = list(PUBLIC_CONTEXT_PRODUCT_METADATA_REQUIREMENTS[req["category"]])
    return metadata


def synthetic_fixture_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "scope": "core_fixture",
            "allowed": True,
            "meaning": "Tiny synthetic fixtures may satisfy terrain, source-zone, scenario, and policy core readiness only.",
        },
        {
            "scope": "public_context",
            "allowed": False,
            "meaning": "Synthetic fixtures must not satisfy SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, or swissBUILDINGS3D readiness.",
        },
        {
            "scope": "physical_evidence",
            "allowed": False,
            "meaning": "Synthetic fixture data are not real swisstopo public-context evidence and must not be treated as validation evidence.",
        },
    ]


def build_blocked_second_site_commands(acquisition_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for entry in acquisition_manifest.get("command_templates") or []:
        if not isinstance(entry, dict):
            continue
        commands.append(
            {
                "id": text_value(entry.get("id")),
                "command": text_value(entry.get("command")),
                "blocked_status": "template_only",
                "expected_outputs": entry.get("expected_outputs") or [],
            }
        )
    return commands


def claim_boundaries() -> dict[str, bool]:
    return {
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
    }


def load_site_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def resolve_repo_path(value: Any, default: Path | None = None, *, base: Path | None = None) -> Path:
    text = text_value(value)
    if not text:
        if default is None:
            raise ValueError("missing path value and no default provided")
        return default
    path = Path(text)
    return path if path.is_absolute() else (base or ROOT) / path


def manifest_status(*paths: Path) -> str:
    return "ready" if all(path.exists() for path in paths) else "blocked_missing_inputs"


def staged_context_status(path: Path, category: str) -> str:
    if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES:
        if path.is_file():
            return "ready"
        if path.is_dir() and any(path.iterdir()):
            return "ready"
        return "deferred_public_context"
    return "ready" if path.exists() else "blocked_missing_inputs"


def build_paths(site_id: str, config: dict[str, Any]) -> dict[str, Path]:
    processed_root = resolve_repo_path(
        config.get("expected_processed_input_root"),
        ROOT / "data/processed/swisstopo" / site_id / "input",
    )
    context_root = resolve_repo_path(
        config.get("expected_processed_context_root"),
        ROOT / "data/processed/swisstopo" / site_id / "context",
    )
    validation_root = resolve_repo_path(
        config.get("expected_validation_private_root"),
        ROOT / "validation/private" / site_id,
    )
    hazard_root = resolve_repo_path(
        config.get("expected_hazard_results_root"),
        ROOT / "hazard/results" / site_id,
    )
    policy_root = ROOT / "validation/policies"
    input_root = processed_root
    return {
        "terrain_crop": resolve_repo_path(config.get("expected_terrain_crop_path"), input_root / "terrain.asc"),
        "terrain_metadata": resolve_repo_path(config.get("expected_terrain_metadata_path"), input_root / "terrain_metadata.yaml"),
        "source_zone_metadata": resolve_repo_path(config.get("expected_source_zone_metadata_path"), input_root / "source_zone_metadata.yaml"),
        "scenario_table": resolve_repo_path(config.get("expected_scenario_table_path"), input_root / "scenario_table.csv"),
        "source_scenario_policy": resolve_repo_path(config.get("expected_source_scenario_policy_path"), policy_root / f"{site_id}_source_scenario_policy_v1.yaml"),
        "swissimage_context": resolve_repo_path(config.get("expected_swissimage_context_root"), context_root / "swissimage"),
        "swisstlm3d_context": resolve_repo_path(config.get("expected_swisstlm3d_context_root"), context_root / "swisstlm3d"),
        "swisstlm3d_metadata": resolve_repo_path(config.get("expected_swisstlm3d_metadata_path"), context_root / "swisstlm3d" / "metadata.json"),
        "swisssurface3d_context": resolve_repo_path(config.get("expected_swisssurface3d_context_root"), context_root / "swisssurface3d"),
        "swisssurface3d_raster_context": resolve_repo_path(config.get("expected_swisssurface3d_raster_context_root"), context_root / "swisssurface3d_raster"),
        "swissbuildings3d_context": resolve_repo_path(config.get("expected_swissbuildings3d_context_root"), context_root / "swissbuildings3d"),
        "barrier_inventory": resolve_repo_path(config.get("expected_barrier_inventory_root"), context_root / "barriers"),
        "validation_observations": resolve_repo_path(config.get("expected_validation_observations_root"), processed_root / "validation/observations"),
        "validation_case_root": validation_root,
        "hazard_results_root": hazard_root,
        "processed_input_root": processed_root,
        "processed_context_root": context_root,
    }


def build_requirements(site_id: str, site_extent: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    extent_ready = bool(
        text_value(site_extent.get("crs"))
        and all(k in site_extent and site_extent[k] not in (None, "") for k in ("xmin", "ymin", "xmax", "ymax"))
    )

    requirements: list[dict[str, Any]] = []

    def add_requirement(
        *,
        kind: str,
        category: str,
        path_or_pattern: str,
        required: bool,
        status: str,
        product: str,
        reusable_from_tschamut: bool,
        notes: str,
    ) -> None:
        requirements.append(
            {
                "kind": kind,
                "category": category,
                "product": product,
                "required": required,
                "status": status,
                "path_or_pattern": path_or_pattern,
                "reusable_from_tschamut": reusable_from_tschamut,
                "notes": notes,
            }
        )

    def required_status(path: Path, category: str) -> str:
        if path.exists():
            return "ready"
        return "deferred_public_context" if category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES else "blocked_missing_inputs"

    # Public geodata products.
    add_requirement(
        kind="public_geodata_product",
        category="terrain_crop",
        product="swissALTI3D or equivalent terrain raster",
        path_or_pattern=str(paths["terrain_crop"]),
        required=True,
        status="ready" if paths["terrain_crop"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=False,
        notes="Terrain crop and extent must be site-specific and share-safe.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swissimage_context",
        product="SWISSIMAGE",
        path_or_pattern=str(paths["swissimage_context"]),
        required=True,
        status=staged_context_status(paths["swissimage_context"], "swissimage_context"),
        reusable_from_tschamut=True,
        notes="Orthophoto context is reusable as a workflow category but site-specific in content.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisstlm3d_context",
        product="swissTLM3D",
        path_or_pattern=str(paths["swisstlm3d_metadata"]),
        required=True,
        status=staged_context_status(paths["swisstlm3d_metadata"], "swisstlm3d_context"),
        reusable_from_tschamut=True,
        notes="Archive metadata contract is reusable; archive contents remain site-specific.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisssurface3d_context",
        product="swissSURFACE3D",
        path_or_pattern=str(paths["swisssurface3d_context"]),
        required=True,
        status=staged_context_status(paths["swisssurface3d_context"], "swisssurface3d_context"),
        reusable_from_tschamut=True,
        notes="Context layer is optional for some pilots but should be enumerated up front.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisssurface3d_raster_context",
        product="swissSURFACE3D Raster",
        path_or_pattern=str(paths["swisssurface3d_raster_context"]),
        required=True,
        status=staged_context_status(paths["swisssurface3d_raster_context"], "swisssurface3d_raster_context"),
        reusable_from_tschamut=True,
        notes="Raster context can be used for canopy / surface-height QA when available.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swissbuildings3d_context",
        product="swissBUILDINGS3D",
        path_or_pattern=str(paths["swissbuildings3d_context"]),
        required=True,
        status=staged_context_status(paths["swissbuildings3d_context"], "swissbuildings3d_context"),
        reusable_from_tschamut=True,
        notes="Building context is optional for hazard-only work but required for portability review.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="barrier_inventory",
        product="optional barrier / protection inventory",
        path_or_pattern=str(paths["barrier_inventory"]),
        required=False,
        status="optional" if not paths["barrier_inventory"].exists() else "ready",
        reusable_from_tschamut=True,
        notes="Optional unless the second site explicitly references a barrier inventory.",
    )

    # Required metadata records.
    add_requirement(
        kind="metadata_record",
        category="site_extent_definition",
        product="candidate site extent in LV95 / EPSG:2056",
        path_or_pattern="site_extent.crs + site_extent.xmin/ymin/xmax/ymax",
        required=True,
        status="ready" if extent_ready else "blocked_missing_inputs",
        reusable_from_tschamut=False,
        notes="A second site needs its own extent and CRS definition before any porting step.",
    )
    add_requirement(
        kind="metadata_record",
        category="terrain_crs_vertical_datum",
        product="terrain metadata CRS and vertical datum",
        path_or_pattern=str(paths["terrain_metadata"]),
        required=True,
        status="ready" if paths["terrain_metadata"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=False,
        notes="Terrain metadata should carry CRS, vertical datum, and resolution.",
    )
    add_requirement(
        kind="metadata_record",
        category="source_zone_metadata",
        product="release / source-zone metadata",
        path_or_pattern=str(paths["source_zone_metadata"]),
        required=True,
        status="ready" if paths["source_zone_metadata"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=False,
        notes="Porting requires a site-specific source-zone contract, not the Tschamut one.",
    )
    add_requirement(
        kind="metadata_record",
        category="scenario_table",
        product="block / scenario table",
        path_or_pattern=str(paths["scenario_table"]),
        required=True,
        status="ready" if paths["scenario_table"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=False,
        notes="The scenario table is site-specific even when the formatting is reusable.",
    )
    add_requirement(
        kind="metadata_record",
        category="source_scenario_policy",
        product="source-scenario policy record",
        path_or_pattern=str(paths["source_scenario_policy"]),
        required=True,
        status="ready" if paths["source_scenario_policy"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Policy structure is reusable; content and named inputs remain site-specific.",
    )

    # Case-generation inputs.
    add_requirement(
        kind="case_generation_input",
        category="validation_case_root",
        product="ignored validation/private output root",
        path_or_pattern=str(paths["validation_case_root"]),
        required=True,
        status="ready" if paths["validation_case_root"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="The ignored private-case root convention is reusable across sites.",
    )
    add_requirement(
        kind="case_generation_input",
        category="hazard_results_root",
        product="ignored hazard/results output root",
        path_or_pattern=str(paths["hazard_results_root"]),
        required=True,
        status="ready" if paths["hazard_results_root"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="The ignored hazard-results root convention is reusable across sites.",
    )
    add_requirement(
        kind="case_generation_input",
        category="validation_observations",
        product="validation or field-observation evidence",
        path_or_pattern=str(paths["validation_observations"]),
        required=False,
        status="optional" if not paths["validation_observations"].exists() else "ready",
        reusable_from_tschamut=False,
        notes="Optional unless a second site has site-specific observational QA evidence.",
    )

    # Command-plan anchors that remain site-specific.
    add_requirement(
        kind="artifact_root",
        category="processed_input_root",
        product="processed public-input root",
        path_or_pattern=str(paths["processed_input_root"]),
        required=True,
        status="ready" if paths["processed_input_root"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="The processed-input root is reusable, but its contents are site-specific.",
    )
    add_requirement(
        kind="artifact_root",
        category="processed_context_root",
        product="processed public-context root",
        path_or_pattern=str(paths["processed_context_root"]),
        required=True,
        status="ready" if paths["processed_context_root"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Context root layout is reusable, but product availability is site-specific.",
    )

    return requirements


def reusable_workflow_components() -> list[dict[str, Any]]:
    return [
        {
            "component": "same-scale readiness preflight",
            "reusable": True,
            "why": "Provides a read-only artifact state check and regeneration-command inventory.",
        },
        {
            "component": "same-scale case regeneration",
            "reusable": True,
            "why": "Regenerates case YAMLs from frozen records without changing physics or thresholds.",
        },
        {
            "component": "cell-wise convergence comparison",
            "reusable": True,
            "why": "Compares grid outputs and isolates numeric versus mask / support differences.",
        },
        {
            "component": "bounded validation-output profile summary",
            "reusable": True,
            "why": "Separates summary-only from full-output pressure before any larger workflow port.",
        },
        {
            "component": "public context inspection and overlap diagnostics",
            "reusable": True,
            "why": "Checks corridor relevance and hazard-context overlap without implementing obstacle physics.",
        },
        {
            "component": "same-scale uncertainty-envelope summary",
            "reusable": True,
            "why": "Composes convergence, output profile, context, and execution-sufficiency evidence.",
        },
        {
            "component": "public real-site geodata manifest validator",
            "reusable": True,
            "why": "Checks share-safe geodata provenance, CRS, and extent contracts before any run.",
        },
        {
            "component": "public real-site conditional pilot run validator",
            "reusable": True,
            "why": "Validates frozen run plans and expected command-plan assumptions for new sites.",
        },
    ]


def build_checklist(
    candidate_site_id: str,
    candidate_site_name: str,
    paths: dict[str, Path],
    site_extent: dict[str, Any],
    source_zone_scenario_contract: dict[str, Any],
    missing_required: list[dict[str, Any]],
    deferred_required: list[dict[str, Any]],
    candidate_selection_rationale: str,
    acquisition_manifest_path: Path,
    public_context_acquisition_plan: list[dict[str, Any]],
) -> list[str]:
    checklist = [
        f"Review acquisition manifest at {acquisition_manifest_path}.",
        "Use the acquisition manifest as a dry-run staging contract only; do not download any public-context products during the plan review.",
        f"PYENV_VERSION=system uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/{candidate_site_id}_manifest.yaml",
        "PYENV_VERSION=system uv run python scripts/validate_public_real_site_conditional_pilot_run.py validation/templates/public_real_site_conditional_pilot_run_v1.yaml",
        f"PYENV_VERSION=system uv run python scripts/prepare_<site_id>_public_benchmark.py --output-root data/processed/swisstopo/{candidate_site_id} --padding-m <buffer> --force",
        f"Stage a site-specific terrain crop and terrain metadata under {paths['terrain_crop'].parent} and {paths['terrain_metadata'].parent}.",
        f"Stage release / source-zone metadata and the block / scenario table under {paths['source_zone_metadata'].parent}.",
        f"Populate the source-scenario policy at {paths['source_scenario_policy']}.",
        f"Stage public context products under {paths['swissimage_context'].parent}, including SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D.",
        "Add a barrier / protection inventory only if the chosen site-specific workflow references one explicitly.",
        f"Keep validation and hazard outputs under {paths['validation_case_root']} and {paths['hazard_results_root']}.",
        "Use the existing Tschamut same-scale diagnostic scripts as reusable patterns, but do not treat them as second-site evidence.",
    ]
    if public_context_acquisition_plan:
        checklist.append(
            "Public-context acquisition plan roots: "
            + ", ".join(
                f"{entry['category']}={entry['expected_staging_root']}" for entry in public_context_acquisition_plan
            )
        )
    if candidate_selection_rationale:
        checklist.append(f"Candidate selection rationale: {candidate_selection_rationale}")
    if source_zone_scenario_contract:
        checklist.append(
            "Source-zone/scenario contract: "
            + ", ".join(
                [
                    f"source_zone_id_pattern={text_value(source_zone_scenario_contract.get('source_zone_id_pattern')) or 'missing'}",
                    f"source_zone_geometry={text_value(source_zone_scenario_contract.get('source_zone_geometry')) or 'missing'}",
                    f"release_point_table={text_value(source_zone_scenario_contract.get('release_point_table')) or 'missing'}",
                    f"observed_deposition_or_field_observation={text_value(source_zone_scenario_contract.get('observed_deposition_or_field_observation')) or 'missing'}",
                    f"scenario_probability_semantics={text_value(source_zone_scenario_contract.get('scenario_probability_semantics')) or 'missing'}",
                ]
            )
        )
    if missing_required:
        checklist.append("Fill the missing required categories before attempting a second-site port.")
    if deferred_required:
        checklist.append(
            "Public-context products are intentionally deferred until staged: "
            + ", ".join(req["category"] for req in deferred_required)
            + ". Use the acquisition manifest as the staging contract; do not confuse these with missing core inputs."
        )
    if candidate_site_name != "unspecified":
        checklist.append(f"Candidate site label: {candidate_site_name}.")
    if site_extent:
        checklist.append(
            "Recorded site extent: "
            + ", ".join(
                [
                    f"crs={text_value(site_extent.get('crs')) or 'missing'}",
                    f"xmin={site_extent.get('xmin', 'missing')}",
                    f"ymin={site_extent.get('ymin', 'missing')}",
                    f"xmax={site_extent.get('xmax', 'missing')}",
                    f"ymax={site_extent.get('ymax', 'missing')}",
                ]
            )
        )
    return checklist


def build_blocked_reason(
    candidate_site_id: str,
    site_extent: dict[str, Any],
    missing_required: list[dict[str, Any]],
    deferred_required: list[dict[str, Any]],
    site_config: Path | None,
) -> str:
    if not missing_required:
        if deferred_required:
            return (
                f"public-context products are intentionally deferred until staged for {candidate_site_id}; "
                + ", ".join(req["category"] for req in deferred_required)
            )
        return "none"
    if site_config is None:
        return (
            f"no second-site config was provided for {candidate_site_id}; "
            "site-specific public geodata, metadata records, and command-plan inputs remain only as templates"
        )
    missing = ", ".join(req["category"] for req in missing_required)
    if not site_extent:
        return f"site config is missing candidate extent metadata; required categories remain missing: {missing}"
    return f"missing required portability inputs: {missing}"


def assumptions_not_yet_generalized(candidate_site_id: str) -> list[str]:
    return [
        "A second site still needs its own LV95 extent and CRS definition before any local porting step.",
        "Terrain crop selection, source-zone geometry, and block-scenario tables are site-specific even when file formats are shared.",
        "The Tschamut source-zone / scenario policy record is a reusable template, not a second-site contract.",
        "Public context availability is site-specific; SWISSIMAGE, swissTLM3D, swissSURFACE3D, and swissBUILDINGS3D must be staged or verified locally.",
        "The Chant Sura acquisition manifest is a metadata-only staging contract, not a substitute for staged public geodata.",
        "Optional barrier / protection inventories may exist only for some sites and must not be assumed.",
        "Validation or field-observation evidence is not portable without an explicit site-specific source record.",
        "A site-specific output-root naming convention still needs to be frozen before any second-site ensemble.",
        f"The placeholder command plan for {candidate_site_id} is still a template until the site id and extent are fixed.",
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"second_site_manifest_status: {report['second_site_manifest_status']}",
        f"portability_preflight_status: {report['portability_preflight_status']}",
        f"readiness_status: {report['readiness_status']}",
        f"public_context_boundary_status: {report['public_context_boundary_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"site_extent_or_placeholder: {report['site_extent_or_placeholder']}",
        f"core_input_status: {report['core_input_status']}",
        f"deferred_public_context_status: {report['deferred_public_context_status']}",
        f"terrain_manifest_status: {report['terrain_manifest_status']}",
        f"source_zone_manifest_status: {report['source_zone_manifest_status']}",
        f"scenario_manifest_status: {report['scenario_manifest_status']}",
        f"acquisition_manifest_status: {report['acquisition_manifest_status']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "public_context_product_requirements:",
    ]
    lines.extend(_render_entries(report["public_context_product_requirements"]))
    lines.append("")
    lines.append("public_geodata_workflow_contract:")
    lines.extend(_render_public_geodata_workflow_contract(report["public_geodata_workflow_contract"]))
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
    lines.extend(_render_public_context_acquisition_plan(report.get("public_context_acquisition_plan") or []))
    lines.append("")
    lines.append("expected_local_paths:")
    if report.get("expected_local_paths"):
        lines.extend(f"- {key}: {value}" for key, value in report["expected_local_paths"].items())
    else:
        lines.append("- none")
    lines.append("")
    lines.append("metadata_requirements:")
    if report.get("metadata_requirements"):
        for key, value in report["metadata_requirements"].items():
            lines.append(f"- {key}: {', '.join(value)}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("synthetic_fixture_boundaries:")
    lines.extend(f"- {item['scope']}: {item['meaning']}" for item in report["synthetic_fixture_boundaries"])
    lines.append("")
    lines.append("blocked_second_site_commands:")
    lines.extend(
        f"- {item['id']}: {item['blocked_status']} ({item['command']})" for item in report["blocked_second_site_commands"]
    )
    lines.append("")
    lines.append("claim_boundaries:")
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in report["claim_boundaries"].items())
    lines.append("")
    lines.append("acquisition_manifest_product_summaries:")
    lines.extend(_render_entries(report["acquisition_manifest_product_summaries"]))
    lines.append("")
    lines.append("required_public_geodata_products:")
    lines.extend(_render_entries(report["required_public_geodata_products"]))
    lines.append("")
    lines.append("required_metadata_records:")
    lines.extend(_render_entries(report["required_metadata_records"]))
    lines.append("")
    lines.append("required_case_generation_inputs:")
    lines.extend(_render_entries(report["required_case_generation_inputs"]))
    lines.append("")
    lines.append("expected_artifact_roots:")
    lines.extend(_render_entries(report["expected_artifact_roots"]))
    lines.append("")
    lines.append("deferred_public_context_categories:")
    if report.get("deferred_public_context_categories"):
        lines.extend(f"- {item}" for item in report["deferred_public_context_categories"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("deferred_public_context_paths_or_patterns:")
    if report.get("deferred_public_context_paths_or_patterns"):
        lines.extend(f"- {item}" for item in report["deferred_public_context_paths_or_patterns"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("missing_input_categories:")
    if report["missing_input_categories"]:
        lines.extend(f"- {item}" for item in report["missing_input_categories"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("missing_input_paths_or_patterns:")
    if report["missing_input_paths_or_patterns"]:
        lines.extend(f"- {item}" for item in report["missing_input_paths_or_patterns"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append(f"blocked_reason: {report['blocked_reason']}")
    lines.append("")
    lines.append("acquisition_or_staging_checklist:")
    lines.extend(f"- {item}" for item in report["acquisition_or_staging_checklist"])
    return "\n".join(lines)


def _render_entries(entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        if "path_or_pattern" in entry:
            lines.append(
                f"- {entry['category']}: {entry['status']} ({entry['path_or_pattern']})"
            )
        else:
            lines.append(
                f"- {entry.get('category')}: {entry.get('status')} ({entry.get('expected_staged_path')})"
            )
    if not lines:
        lines.append("- none")
    return lines


def _render_public_context_acquisition_plan(entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            f"- {entry.get('category')}: {entry.get('current_status')} "
            f"(staging_root={entry.get('expected_staging_root')}, "
            f"expected_staged_path={entry.get('expected_staged_path')}, "
            f"metadata_contract={', '.join(entry.get('metadata_contract') or [])}, "
            f"staging_mode={entry.get('staging_mode')})"
        )
    if not lines:
        lines.append("- none")
    return lines


def _render_public_geodata_workflow_contract(contract: dict[str, Any]) -> list[str]:
    lines = [
        f"- schema_version: {contract['schema_version']}",
        f"- public_geodata_contract_readiness_status: {contract['public_geodata_contract_readiness_status']}",
        f"- synthetic_fixture_readiness_status: {contract['synthetic_fixture_readiness_status']}",
        f"- synthetic_fixture_profile: {contract['synthetic_fixture_profile']}",
        f"- candidate_site_id: {contract['candidate_site_id']}",
        f"- candidate_site_name: {contract['candidate_site_name']}",
        "- required_aoi_metadata:",
    ]
    for entry in contract["required_aoi_metadata"]:
        lines.append(
            f"  - {entry['field']}: required={str(entry['required']).lower()}, ready={str(entry['ready']).lower()}, purpose={entry['purpose']}"
        )
    lines.append("- crs_grid_assumptions:")
    for entry in contract["crs_grid_assumptions"]:
        lines.append(
            f"  - {entry['assumption']}: required={str(entry['required']).lower()}, ready={str(entry['ready']).lower()}"
        )
    lines.append("- swisstopo_product_classes:")
    for entry in contract["swisstopo_product_classes"]:
        lines.append(
            f"  - {entry['class']}: required={str(entry['required']).lower()}, products={', '.join(entry['products'])}, workflow_role={entry['workflow_role']}"
        )
    lines.append("- cache_paths:")
    for key, value in contract["cache_paths"].items():
        lines.append(f"  - {key}: {value}")
    lines.append("- provenance_requirements:")
    for entry in contract["provenance_requirements"]:
        lines.append(f"  - {entry['field']}: required={str(entry['required']).lower()}, purpose={entry['purpose']}")
    lines.append("- deferred_optional_context:")
    for entry in contract["deferred_optional_context"]:
        lines.append(
            f"  - {entry['category']}: {entry['expected_staged_path']} ({entry['meaning']})"
        )
    lines.append("- claim_boundaries:")
    lines.extend(f"  - {key}: {str(value).lower()}" for key, value in contract["claim_boundaries"].items())
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
