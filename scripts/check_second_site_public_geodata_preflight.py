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
    candidate_site_id = text_value(config.get("candidate_site_id")) or site_id or DEFAULT_CANDIDATE_SITE_ID
    candidate_site_id = candidate_site_id.strip()
    candidate_site_name = text_value(config.get("candidate_site_name")) or "unspecified"
    site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}

    paths = default_paths(candidate_site_id)
    requirements = build_requirements(candidate_site_id, site_extent, paths)
    missing_required = [req for req in requirements if req["required"] and req["status"] != "ready"]

    report = {
        "portability_preflight_status": "ready" if not missing_required else "blocked_missing_inputs",
        "readiness_status": "ready" if not missing_required else "blocked_missing_inputs",
        "candidate_site_id": candidate_site_id,
        "reusable_workflow_components": reusable_workflow_components(),
        "site_specific_required_inputs": [req for req in requirements if req["required"]],
        "required_public_geodata_products": [req for req in requirements if req["kind"] == "public_geodata_product"],
        "required_metadata_records": [req for req in requirements if req["kind"] == "metadata_record"],
        "required_case_generation_inputs": [req for req in requirements if req["kind"] == "case_generation_input"],
        "expected_artifact_roots": [req for req in requirements if req["kind"] == "artifact_root"],
        "missing_input_categories": [req["category"] for req in missing_required],
        "missing_input_paths_or_patterns": [req["path_or_pattern"] for req in missing_required],
        "acquisition_or_staging_checklist": build_checklist(candidate_site_id, candidate_site_name, paths, site_extent, missing_required),
        "blocked_reason": build_blocked_reason(candidate_site_id, site_extent, missing_required, site_config),
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


def default_paths(site_id: str) -> dict[str, Path]:
    processed_root = ROOT / "data/processed/swisstopo" / site_id
    validation_root = ROOT / "validation/private" / site_id
    hazard_root = ROOT / "hazard/results" / site_id
    policy_root = ROOT / "validation/policies"
    context_root = processed_root / "context"
    input_root = processed_root / "input"
    return {
        "terrain_crop": input_root / "terrain.asc",
        "terrain_metadata": input_root / "terrain_metadata.yaml",
        "source_zone_metadata": input_root / "source_zone_metadata.yaml",
        "scenario_table": input_root / "scenario_table.csv",
        "source_scenario_policy": policy_root / f"{site_id}_source_scenario_policy_v1.yaml",
        "swissimage_context": context_root / "swissimage",
        "swisstlm3d_context": context_root / "swisstlm3d",
        "swisstlm3d_metadata": context_root / "swisstlm3d" / "metadata.json",
        "swisssurface3d_context": context_root / "swisssurface3d",
        "swisssurface3d_raster_context": context_root / "swisssurface3d_raster",
        "swissbuildings3d_context": context_root / "swissbuildings3d",
        "barrier_inventory": context_root / "barriers",
        "validation_observations": processed_root / "validation/observations",
        "validation_case_root": validation_root,
        "hazard_results_root": hazard_root,
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
        status="ready" if paths["swissimage_context"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Orthophoto context is reusable as a workflow category but site-specific in content.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisstlm3d_context",
        product="swissTLM3D",
        path_or_pattern=str(paths["swisstlm3d_metadata"]),
        required=True,
        status="ready" if paths["swisstlm3d_metadata"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Archive metadata contract is reusable; archive contents remain site-specific.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisssurface3d_context",
        product="swissSURFACE3D",
        path_or_pattern=str(paths["swisssurface3d_context"]),
        required=True,
        status="ready" if paths["swisssurface3d_context"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Context layer is optional for some pilots but should be enumerated up front.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swisssurface3d_raster_context",
        product="swissSURFACE3D Raster",
        path_or_pattern=str(paths["swisssurface3d_raster_context"]),
        required=True,
        status="ready" if paths["swisssurface3d_raster_context"].exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="Raster context can be used for canopy / surface-height QA when available.",
    )
    add_requirement(
        kind="public_geodata_product",
        category="swissbuildings3d_context",
        product="swissBUILDINGS3D",
        path_or_pattern=str(paths["swissbuildings3d_context"]),
        required=True,
        status="ready" if paths["swissbuildings3d_context"].exists() else "blocked_missing_inputs",
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
        path_or_pattern=f"data/processed/swisstopo/{site_id}/input",
        required=True,
        status="ready" if (ROOT / f"data/processed/swisstopo/{site_id}/input").exists() else "blocked_missing_inputs",
        reusable_from_tschamut=True,
        notes="The processed-input root is reusable, but its contents are site-specific.",
    )
    add_requirement(
        kind="artifact_root",
        category="processed_context_root",
        product="processed public-context root",
        path_or_pattern=f"data/processed/swisstopo/{site_id}/context",
        required=True,
        status="ready" if (ROOT / f"data/processed/swisstopo/{site_id}/context").exists() else "blocked_missing_inputs",
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
    missing_required: list[dict[str, Any]],
) -> list[str]:
    checklist = [
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
    if missing_required:
        checklist.append("Fill the missing required categories before attempting a second-site port.")
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
    site_config: Path | None,
) -> str:
    if not missing_required:
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
        "Optional barrier / protection inventories may exist only for some sites and must not be assumed.",
        "Validation or field-observation evidence is not portable without an explicit site-specific source record.",
        "A site-specific output-root naming convention still needs to be frozen before any second-site ensemble.",
        f"The placeholder command plan for {candidate_site_id} is still a template until the site id and extent are fixed.",
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"portability_preflight_status: {report['portability_preflight_status']}",
        f"readiness_status: {report['readiness_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "required_public_geodata_products:",
    ]
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
    lines.append("acquisition_or_staging_checklist:")
    lines.extend(f"- {item}" for item in report["acquisition_or_staging_checklist"])
    return "\n".join(lines)


def _render_entries(entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            f"- {entry['category']}: {entry['status']} ({entry['path_or_pattern']})"
        )
    if not lines:
        lines.append("- none")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
