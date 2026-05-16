#!/usr/bin/env python3
"""Plan a deterministic release-zone heuristic dry run from a small AOI/site config.

This helper stays at the dry-run boundary. It does not download public data,
generate release zones, tune release-zone physics, or authorize an ensemble.
Instead, it turns a candidate AOI/site configuration into a deterministic
report of heuristic requirements, concrete inputs, and blocked or missing
products so the real-site gap stays explicit.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "release_zone_heuristic_dry_run_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
}


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("release_zone_heuristic_dry_run_preflight", path)
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
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--site-id", type=str, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, repo_root=args.repo_root, site_id=args.site_id)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["heuristic_dry_run_status"] == "ready" else 2


def build_report(site_config: Path | None, repo_root: Path | None = None, site_id: str | None = None) -> dict[str, Any]:
    if site_config is not None and not site_config.exists():
        raise SystemExit(f"missing site config: {site_config}")

    repo_root = repo_root or ROOT
    original_root = PREFLIGHT.ROOT
    try:
        PREFLIGHT.ROOT = repo_root
        preflight_report = PREFLIGHT.build_report(site_config, site_id=site_id)
    finally:
        PREFLIGHT.ROOT = original_root

    heuristic_inputs = build_heuristic_inputs(preflight_report)
    heuristic_requirements = build_heuristic_requirements(preflight_report)
    blocked_missing_products = [
        entry
        for entry in preflight_report["public_context_product_requirements"]
        if entry["required"] and entry["current_status"] != "ready"
    ]
    deferred_public_context_inputs = [
        entry for entry in blocked_missing_products if entry["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES
    ]

    heuristic_dry_run_status = preflight_report["core_input_status"]
    if heuristic_dry_run_status == "ready":
        heuristic_dry_run_status = "deferred_public_context_inputs" if deferred_public_context_inputs else "ready"

    report = {
        "schema_version": SCHEMA_VERSION,
        "heuristic_dry_run_status": heuristic_dry_run_status,
        "candidate_release_zone_set_status": "not_generated",
        "candidate_release_zone_interpretation": "not_claimed",
        "candidate_site_id": preflight_report["candidate_site_id"],
        "candidate_site_name": preflight_report["candidate_site_name"],
        "candidate_selection_rationale": preflight_report["candidate_selection_rationale"],
        "site_extent": preflight_report["site_extent_or_placeholder"],
        "heuristic_summary": {
            "heuristic_requirement_count": len(heuristic_requirements),
            "heuristic_input_count": len(heuristic_inputs),
            "blocked_missing_product_count": len(blocked_missing_products),
            "deferred_public_context_count": len(deferred_public_context_inputs),
            "deferred_public_context_inputs_status": "deferred_public_context_inputs" if deferred_public_context_inputs else "ready",
        },
        "heuristic_requirements": heuristic_requirements,
        "heuristic_inputs": heuristic_inputs,
        "blocked_missing_products": blocked_missing_products,
        "deferred_public_context_inputs": deferred_public_context_inputs,
        "heuristic_assumptions": heuristic_assumptions(),
        "blocked_reason": build_blocked_reason(preflight_report, deferred_public_context_inputs),
        "acquisition_manifest_path": preflight_report["acquisition_manifest_path"],
        "acquisition_manifest_status": preflight_report["acquisition_manifest_status"],
        "claim_boundaries": preflight_report["claim_boundaries"],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_heuristic_inputs(preflight_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in preflight_report["required_metadata_records"]:
        rows.append(
            {
                "category": entry["category"],
                "kind": entry["kind"],
                "status": entry["status"],
                "required": entry["required"],
                "path_or_pattern": entry["path_or_pattern"],
                "product": entry["product"],
                "why": heuristic_input_why(entry["category"]),
            }
        )
    for entry in preflight_report["public_context_product_requirements"]:
        rows.append(
            {
                "category": entry["category"],
                "kind": "public_geodata_product",
                "status": entry["current_status"],
                "required": entry["required"],
                "path_or_pattern": entry["expected_local_path"],
                "product": entry["product"],
                "why": heuristic_input_why(entry["category"]),
            }
        )
    return rows


def build_heuristic_requirements(preflight_report: dict[str, Any]) -> list[dict[str, Any]]:
    terrain_ready = any(
        entry["category"] == "terrain_crop" and entry["current_status"] == "ready"
        for entry in preflight_report["public_context_product_requirements"]
    ) and any(
        entry["category"] == "terrain_crs_vertical_datum" and entry["status"] == "ready"
        for entry in preflight_report["required_metadata_records"]
    )
    source_contract_ready = all(
        entry["status"] == "ready"
        for entry in preflight_report["required_metadata_records"]
        if entry["category"] in {"source_zone_metadata", "scenario_table", "source_scenario_policy"}
    )
    has_deferred_context = bool(preflight_report["deferred_public_context_categories"])

    return [
        {
            "requirement_id": "finite_aoi_extent",
            "status": "ready" if isinstance(preflight_report["site_extent_or_placeholder"], dict) else "blocked_missing_inputs",
            "required_inputs": ["site_extent_definition"],
            "why": "The heuristic must stay tied to a finite LV95 AOI and not a free-floating label.",
        },
        {
            "requirement_id": "terrain_screening",
            "status": "ready" if terrain_ready else "blocked_missing_inputs",
            "required_inputs": ["terrain_crop", "terrain_metadata"],
            "why": "The screening heuristic can only reason about slope and terrain quality when terrain is staged.",
        },
        {
            "requirement_id": "source_zone_contract",
            "status": "ready" if source_contract_ready else "blocked_missing_inputs",
            "required_inputs": ["source_zone_metadata", "scenario_table", "source_scenario_policy"],
            "why": "A candidate release-zone set needs a frozen site-specific contract before it can be interpreted.",
        },
        {
            "requirement_id": "public_context_prerequisites",
            "status": "deferred_public_context_inputs" if has_deferred_context else "ready",
            "required_inputs": [
                "swissimage_context",
                "swisstlm3d_context",
                "swisstlm3d_metadata",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
            "why": "Real-site interpretation needs public context, but the dry run keeps those products deferred when absent.",
        },
        {
            "requirement_id": "candidate_release_zone_set",
            "status": "not_generated",
            "required_inputs": ["heuristic_requirements", "heuristic_inputs"],
            "why": "This helper stops at the heuristic dry run and does not emit a release-zone interpretation.",
        },
    ]


def heuristic_input_why(category: str) -> str:
    return {
        "site_extent_definition": "The site extent gives the deterministic AOI boundary for the heuristic.",
        "terrain_crop": "Terrain is the minimum input for slope-based screening.",
        "terrain_crs_vertical_datum": "Terrain metadata must confirm CRS and vertical datum before interpretation.",
        "terrain_metadata": "Terrain metadata anchors provenance, resolution, and crop context.",
        "source_zone_metadata": "Source-zone metadata freezes the release-zone contract shape.",
        "scenario_table": "Scenario rows keep the block / release plan deterministic and auditable.",
        "source_scenario_policy": "The site policy states which assumptions are frozen and which are deferred.",
        "swissimage_context": "Orthophotos support visual QA once real public context is staged.",
        "swisstlm3d_context": "Transport and context layers help review exclusions and corridor features.",
        "swisstlm3d_metadata": "Metadata keeps the archive contract auditable without claiming the raw product is present.",
        "swisssurface3d_context": "Surface context can refine future terrain interpretation.",
        "swisssurface3d_raster_context": "Raster surface context can refine canopy or obstacle screening.",
        "swissbuildings3d_context": "Building context may matter for future real-site interpretation but is deferred here.",
        "barrier_inventory": "Barrier inventories are optional and only used if a site policy explicitly references them.",
    }.get(category, "Heuristic input placeholder.")


def heuristic_assumptions() -> list[dict[str, Any]]:
    return [
        {
            "assumption_id": "deterministic_screening",
            "status": "frozen",
            "text": "The dry run is deterministic and does not tune release-zone physics.",
        },
        {
            "assumption_id": "slope_screening_only",
            "status": "frozen",
            "text": "Candidate release-zone identification is only a heuristic screen based on terrain and documented context, not a field-derived interpretation.",
        },
        {
            "assumption_id": "context_is_required_for_real_interpretation",
            "status": "frozen",
            "text": "SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D stay deferred until staged or verified locally.",
        },
        {
            "assumption_id": "synthetic_fixture_not_evidence",
            "status": "frozen",
            "text": "Synthetic fixtures do not count as public-geodata evidence or release-zone field evidence.",
        },
        {
            "assumption_id": "no_annual_frequency_claim",
            "status": "frozen",
            "text": "The report does not introduce annual-frequency, physical-probability, risk, exposure, or vulnerability semantics.",
        },
    ]


def build_blocked_reason(preflight_report: dict[str, Any], deferred_public_context_inputs: list[dict[str, Any]]) -> str:
    if preflight_report["core_input_status"] != "ready":
        return preflight_report["blocked_reason"]
    if deferred_public_context_inputs:
        categories = ", ".join(entry["category"] for entry in deferred_public_context_inputs)
        return f"public-context inputs are intentionally deferred for the dry run: {categories}; no candidate release-zone set is claimed"
    return "none"


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"heuristic_dry_run_status: {report['heuristic_dry_run_status']}",
        f"candidate_release_zone_set_status: {report['candidate_release_zone_set_status']}",
        f"candidate_release_zone_interpretation: {report['candidate_release_zone_interpretation']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        "",
        "site_extent:",
    ]
    site_extent = report["site_extent"]
    if isinstance(site_extent, dict):
        for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
            if key in site_extent:
                lines.append(f"  {key}: {site_extent[key]}")
    else:
        lines.append(f"  {site_extent}")

    lines.append("")
    lines.append("heuristic_summary:")
    for key, value in report["heuristic_summary"].items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("heuristic_requirements:")
    lines.extend(render_rows(report["heuristic_requirements"]))

    lines.append("")
    lines.append("heuristic_inputs:")
    lines.extend(render_rows(report["heuristic_inputs"]))

    lines.append("")
    lines.append("blocked_missing_products:")
    lines.extend(render_rows(report["blocked_missing_products"]))

    lines.append("")
    lines.append("deferred_public_context_inputs:")
    lines.extend(render_rows(report["deferred_public_context_inputs"]))

    lines.append("")
    lines.append("heuristic_assumptions:")
    for item in report["heuristic_assumptions"]:
        lines.append(f"- {item['assumption_id']}: {item['text']}")

    lines.append("")
    lines.append(f"blocked_reason: {report['blocked_reason']}")
    lines.append(f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}")
    lines.append(f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}")
    return "\n".join(lines)


def render_rows(rows: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not rows:
        return ["- none"]
    for row in rows:
        lines.append(
            "- "
            + ", ".join(
                [
                    f"category={row.get('category')}",
                    f"status={row.get('status')}",
                    f"required={str(row.get('required')).lower()}",
                    f"product={row.get('product')}",
                ]
            )
        )
        if row.get("path_or_pattern"):
            lines.append(f"  path_or_pattern: {row['path_or_pattern']}")
        if row.get("why"):
            lines.append(f"  why: {row['why']}")
        if row.get("required_inputs"):
            lines.append(f"  required_inputs: {', '.join(row['required_inputs'])}")
        if row.get("requirement_id"):
            lines.append(f"  requirement_id: {row['requirement_id']}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
