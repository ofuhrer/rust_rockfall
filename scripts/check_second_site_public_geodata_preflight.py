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
DEFAULT_CANDIDATE_SITE_ID = "unspecified_second_site"
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
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
        "terrain_manifest_status": terrain_manifest_status,
        "source_zone_manifest_status": source_zone_manifest_status,
        "scenario_manifest_status": scenario_manifest_status,
        "acquisition_manifest_status": "ready" if acquisition_manifest_path.exists() else "blocked_missing_inputs",
        "acquisition_manifest_path": str(acquisition_manifest_path),
        "acquisition_manifest_category_count": len(acquisition_manifest.get("expected_products") or []),
        "acquisition_manifest_expected_ignored_roots": acquisition_manifest.get("expected_ignored_output_roots") or [],
        "acquisition_manifest_command_template_count": len(acquisition_manifest.get("command_templates") or []),
        "acquisition_manifest_product_summaries": [
            {
                "category": entry.get("category"),
                "product": entry.get("product"),
                "status": entry.get("status"),
                "required": entry.get("required"),
                "expected_staged_path": entry.get("expected_staged_path"),
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
        ),
        "blocked_reason": build_blocked_reason(
            candidate_site_id, site_extent, missing_required, deferred_required, site_config
        ),
        "assumptions_not_yet_generalized": assumptions_not_yet_generalized(candidate_site_id),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


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
) -> list[str]:
    checklist = [
        f"Review acquisition manifest at {acquisition_manifest_path}.",
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
        "acquisition_manifest_product_summaries:",
    ]
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


if __name__ == "__main__":
    raise SystemExit(main())
