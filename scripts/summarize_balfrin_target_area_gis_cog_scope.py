#!/usr/bin/env python3
"""Summarize the target-area GIS/COG scope for the frozen Balfrin demo.

This helper composes the committed target-area GIS package audit, an optional
scratch COG conversion package, and the frozen target-area GIS scope summary.
It keeps the committed target root, the converted scratch proof, and the
template-only handoff boundaries separate so the report can state whether the
target-area demo is full-scope, bounded-scope, or blocked without implying an
operational hazard product.
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
    raise SystemExit("PyYAML is required; install with `uv run --with PyYAML python ...`") from exc

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gis_cog_package_readiness as gis_cog


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_gis_cog_scope_audit_v1"
DEFAULT_ARTIFACT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_SCOPE_SUMMARY_PATH = (
    ROOT
    / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"
    / "tschamut_public_balfrin_target_area_demo_gis_scope_summary.yaml"
)


class BalfrinTargetAreaGisCogScopeError(ValueError):
    """User-facing target-area GIS/COG scope error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument(
        "--converted-package-root",
        type=Path,
        default=None,
        help="optional scratch COG package root to compare against the committed target package",
    )
    parser.add_argument("--scope-summary-path", type=Path, default=DEFAULT_SCOPE_SUMMARY_PATH)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            artifact_root=args.artifact_root,
            converted_package_root=args.converted_package_root,
            scope_summary_path=args.scope_summary_path,
            raster_metadata_provider=gis_cog.inspect_raster_metadata,
        )
    except BalfrinTargetAreaGisCogScopeError as exc:
        print(f"balfrin target-area GIS/COG scope audit error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output is not None:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(render_text_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["report_status"] != "blocked_missing_inputs" else 2


def build_report(
    *,
    artifact_root: Path,
    converted_package_root: Path | None = None,
    scope_summary_path: Path | None = None,
    raster_metadata_provider: Any | None = None,
    scope_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_root = Path(artifact_root)
    converted_package_root = Path(converted_package_root) if converted_package_root is not None else None
    provider = raster_metadata_provider or gis_cog.inspect_raster_metadata
    gis_report = gis_cog.build_gis_cog_readiness_report(
        artifact_roots=[artifact_root],
        converted_package_roots=[converted_package_root] if converted_package_root is not None else None,
        raster_metadata_provider=provider,
    )
    target_artifact = gis_report["artifacts"][0] if gis_report.get("artifacts") else {}
    converted_package = gis_report["converted_packages"][0] if gis_report.get("converted_packages") else {}
    summary = scope_summary or load_scope_summary(scope_summary_path)
    scope_status = classify_scope_status(converted_package)
    parity_status = str(converted_package.get("layer_inventory_status") or "blocked_missing_inputs")
    summary_status = str(summary.get("status") or "").strip()
    report_status = (
        "blocked_missing_inputs"
        if scope_status == "blocked_missing_products" or summary_status.startswith("blocked")
        else "ready"
    )

    target_summary = summarize_target_scope_summary(summary)
    demo_usability = summarize_demo_usability(scope_status, gis_report, summary, target_summary)

    return {
        "schema_version": SCHEMA_VERSION,
        "report_status": report_status,
        "scope_classification": scope_status,
        "demo_usability_status": demo_usability["status"],
        "demo_usability_summary": demo_usability["summary"],
        "artifact_root": str(artifact_root),
        "converted_package_root": str(converted_package_root) if converted_package_root is not None else None,
        "scope_summary_path": str(scope_summary_path) if scope_summary_path is not None else None,
        "target_area_demo_scope_summary": target_summary,
        "target_area_demo_non_operational_boundaries": target_summary.get("non_operational_gis_boundaries", {}),
        "target_area_demo_cog_export_expectation": target_summary.get("cog_export_expectation", {}),
        "gis_cog_readiness_status": gis_report.get("gis_cog_readiness_status"),
        "standard_package_readiness_status": gis_report.get("standard_package_readiness_status"),
        "converted_package_readiness_status": gis_report.get("converted_package_readiness_status"),
        "standard_package_status": gis_report.get("standard_package_status", {}),
        "converted_package_status": gis_report.get("converted_package_status", {}),
        "layer_parity": summarize_layer_parity(converted_package, target_artifact),
        "cog_conversion_scope": summarize_cog_conversion_scope(converted_package, target_artifact),
        "missing_layer_summary": summarize_missing_layers(converted_package),
        "visual_qa": summarize_visual_qa(target_artifact, summary),
        "claim_boundaries": summarize_claim_boundaries(summary, target_artifact),
        "source_paths": {
            "artifact_root": str(artifact_root),
            "converted_package_root": str(converted_package_root) if converted_package_root is not None else None,
            "scope_summary_path": str(scope_summary_path) if scope_summary_path is not None else None,
            "audit_helper": "scripts/audit_gis_cog_package_readiness.py",
            "scope_summary_helper": "scripts/generate_balfrin_target_area_demo_handoff.py",
        },
        "gis_report": gis_report,
    }


def load_scope_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "status": "blocked_missing_inputs",
            "summary": "missing target-area GIS scope summary",
            "no_hazard_layers_generated": True,
            "non_operational_gis_boundaries": {
                "operational_claims_allowed": False,
                "hazard_layers_generated": False,
                "cog_export_generated": False,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "cog_export_expectation": {"status": "blocked_missing_inputs", "generated_now": False},
        }
    if not path.exists():
        return {
            "status": "blocked_missing_inputs",
            "summary": f"missing target-area GIS scope summary: {path}",
            "no_hazard_layers_generated": True,
            "non_operational_gis_boundaries": {
                "operational_claims_allowed": False,
                "hazard_layers_generated": False,
                "cog_export_generated": False,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "cog_export_expectation": {"status": "blocked_missing_inputs", "generated_now": False},
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def classify_scope_status(converted_package: dict[str, Any]) -> str:
    status = str((converted_package or {}).get("cog_scope", {}).get("status") or "").strip()
    if status in {"full_scope", "bounded_scope"}:
        return status
    return "blocked_missing_products"


def summarize_layer_parity(converted_package: dict[str, Any], target_artifact: dict[str, Any]) -> dict[str, Any]:
    if not converted_package:
        return {
            "status": "blocked_missing_products",
            "reference_layer_count": len(target_artifact.get("layer_names", [])),
            "exported_layer_count": 0,
            "missing_layer_count": 0,
            "missing_layer_names": [],
            "extra_layer_count": 0,
            "extra_layer_names": [],
        }
    cog_scope = converted_package.get("cog_scope", {})
    return {
        "status": str(converted_package.get("layer_inventory_status") or "blocked_missing_inputs"),
        "reference_layer_count": cog_scope.get("reference_layer_count"),
        "exported_layer_count": cog_scope.get("exported_layer_count"),
        "missing_layer_count": cog_scope.get("omitted_layer_count"),
        "missing_layer_names": list(cog_scope.get("omitted_layer_names") or []),
        "extra_layer_count": cog_scope.get("extra_layer_count"),
        "extra_layer_names": list(cog_scope.get("extra_layer_names") or []),
    }


def summarize_cog_conversion_scope(converted_package: dict[str, Any], target_artifact: dict[str, Any]) -> dict[str, Any]:
    if not converted_package:
        return {
            "status": "blocked_missing_products",
            "reference_layer_count": len(target_artifact.get("layer_names", [])),
            "exported_layer_count": 0,
            "omitted_layer_count": len(target_artifact.get("layer_names", [])),
            "omitted_layer_names": list(target_artifact.get("layer_names", [])),
            "extra_layer_count": 0,
            "extra_layer_names": [],
        }
    cog_scope = converted_package.get("cog_scope", {})
    return {
        "status": str(cog_scope.get("status") or "blocked_missing_inputs"),
        "reference_layer_count": cog_scope.get("reference_layer_count"),
        "reference_layer_names": list(cog_scope.get("reference_layer_names") or []),
        "exported_layer_count": cog_scope.get("exported_layer_count"),
        "exported_layer_names": list(cog_scope.get("exported_layer_names") or []),
        "omitted_layer_count": cog_scope.get("omitted_layer_count"),
        "omitted_layer_names": list(cog_scope.get("omitted_layer_names") or []),
        "extra_layer_count": cog_scope.get("extra_layer_count"),
        "extra_layer_names": list(cog_scope.get("extra_layer_names") or []),
    }


def summarize_missing_layers(converted_package: dict[str, Any]) -> dict[str, Any]:
    if not converted_package:
        return {"status": "blocked_missing_products", "missing_layer_names": [], "extra_layer_names": []}
    return {
        "status": str(converted_package.get("layer_inventory_status") or "blocked_missing_inputs"),
        "missing_layer_names": list(converted_package.get("missing_layer_names") or []),
        "extra_layer_names": list(converted_package.get("extra_layer_names") or []),
    }


def summarize_target_scope_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": summary.get("schema_version"),
        "status": summary.get("status"),
        "summary": summary.get("summary"),
        "no_hazard_layers_generated": bool(summary.get("no_hazard_layers_generated", False)),
        "cog_export_expectation": summary.get("cog_export_expectation", {}),
        "non_operational_gis_boundaries": summary.get("non_operational_gis_boundaries", {}),
        "planned_raster_products": summary.get("planned_raster_products", []),
        "planned_vector_products": summary.get("planned_vector_products", []),
        "template_only_products": summary.get("template_only_products", []),
    }


def summarize_demo_usability(
    scope_status: str,
    gis_report: dict[str, Any],
    summary: dict[str, Any],
    target_summary: dict[str, Any],
) -> dict[str, Any]:
    target_status = str(gis_report.get("gis_cog_readiness_status") or "blocked_missing_inputs")
    summary_status = str(summary.get("status") or "").strip()
    if summary_status.startswith("blocked"):
        return {
            "status": "blocked_missing_inputs",
            "summary": "The target-area demo remains blocked because the frozen target-area GIS scope summary is missing.",
        }
    if scope_status == "blocked_missing_products":
        return {
            "status": "blocked_missing_products",
            "summary": "The target-area demo remains blocked because the converted COG package is missing or incomplete.",
        }
    if target_status == "gis_package_ready_cog_blocked":
        return {
            "status": "usable_for_local_diagnostic_review",
            "summary": (
                "The committed target package is visually useful for local diagnostic review, while the scratch COG conversion demonstrates full-scope parity and keeps the non-operational boundaries explicit."
            ),
        }
    return {
        "status": "usable_for_local_diagnostic_review",
        "summary": (
            "The target-area GIS package is visually useful for local diagnostic review, and the converted package remains bounded by the frozen handoff boundaries."
        ),
    }


def summarize_visual_qa(target_artifact: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    visual_qa = target_artifact.get("cog_readiness_indicators", {}).get("visual_qa", {})
    if not isinstance(visual_qa, dict):
        visual_qa = {}
    return {
        "status": visual_qa.get("status") or "not_run",
        "accepted_for_operational_use": bool(visual_qa.get("accepted_for_operational_use", False)),
        "note": visual_qa.get("note") or "manual GIS/QGIS inspection has not been run for this package",
        "acceptance_scope": visual_qa.get("acceptance_scope") or "local diagnostic GIS/QGIS review only",
        "non_operational_scope": summary.get("non_operational_gis_boundaries", {}),
    }


def summarize_claim_boundaries(summary: dict[str, Any], target_artifact: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = summary.get("claim_boundary")
    if not isinstance(claim_boundaries, dict):
        claim_boundaries = target_artifact.get("cog_readiness_indicators", {})
    if not isinstance(claim_boundaries, dict):
        claim_boundaries = {}
    return {
        "operational_claims_allowed": bool(claim_boundaries.get("operational_claims_allowed", False)),
        "annual_frequency_claims_allowed": bool(claim_boundaries.get("annual_frequency_claims_allowed", False)),
        "physical_probability_claims_allowed": bool(claim_boundaries.get("physical_probability_claims_allowed", False)),
        "risk_exposure_vulnerability_claims_allowed": bool(
            claim_boundaries.get("risk_exposure_vulnerability_claims_allowed", False)
        ),
        "scale_up_authorized": bool(claim_boundaries.get("scale_up_authorized", False)),
        "distributed_execution_authorized": bool(claim_boundaries.get("distributed_execution_authorized", False)),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area GIS/COG Scope Audit",
        f"schema_version: {report['schema_version']}",
        f"report_status: {report['report_status']}",
        f"scope_classification: {report['scope_classification']}",
        f"demo_usability_status: {report['demo_usability_status']}",
        f"demo_usability_summary: {report['demo_usability_summary']}",
        f"artifact_root: {report['artifact_root']}",
        f"converted_package_root: {report['converted_package_root']}",
        f"gis_cog_readiness_status: {report['gis_cog_readiness_status']}",
        f"standard_package_readiness_status: {report['standard_package_readiness_status']}",
        f"converted_package_readiness_status: {report['converted_package_readiness_status']}",
        "layer_parity:",
        f"  status: {report['layer_parity']['status']}",
        f"  reference_layer_count: {report['layer_parity']['reference_layer_count']}",
        f"  exported_layer_count: {report['layer_parity']['exported_layer_count']}",
        f"  missing_layer_count: {report['layer_parity']['missing_layer_count']}",
        f"  missing_layer_names: {', '.join(report['layer_parity']['missing_layer_names']) or 'none'}",
        f"  extra_layer_count: {report['layer_parity']['extra_layer_count']}",
        f"  extra_layer_names: {', '.join(report['layer_parity']['extra_layer_names']) or 'none'}",
        "cog_conversion_scope:",
        f"  status: {report['cog_conversion_scope']['status']}",
        f"  omitted_layer_count: {report['cog_conversion_scope']['omitted_layer_count']}",
        f"  omitted_layer_names: {', '.join(report['cog_conversion_scope']['omitted_layer_names']) or 'none'}",
        f"  extra_layer_names: {', '.join(report['cog_conversion_scope']['extra_layer_names']) or 'none'}",
        "visual_qa:",
        f"  status: {report['visual_qa']['status']}",
        f"  accepted_for_operational_use: {report['visual_qa']['accepted_for_operational_use']}",
        f"  acceptance_scope: {report['visual_qa']['acceptance_scope']}",
        "claim_boundaries:",
        f"  operational_claims_allowed: {report['claim_boundaries']['operational_claims_allowed']}",
        f"  annual_frequency_claims_allowed: {report['claim_boundaries']['annual_frequency_claims_allowed']}",
        f"  physical_probability_claims_allowed: {report['claim_boundaries']['physical_probability_claims_allowed']}",
        f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries']['risk_exposure_vulnerability_claims_allowed']}",
        f"  scale_up_authorized: {report['claim_boundaries']['scale_up_authorized']}",
        f"  distributed_execution_authorized: {report['claim_boundaries']['distributed_execution_authorized']}",
        "target_area_demo_scope_summary:",
        f"  status: {report['target_area_demo_scope_summary']['status']}",
        f"  summary: {report['target_area_demo_scope_summary']['summary']}",
        f"  no_hazard_layers_generated: {report['target_area_demo_scope_summary']['no_hazard_layers_generated']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
