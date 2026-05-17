#!/usr/bin/env python3
"""Summarize the target-area Balfrin diagnostic interpretation.

This helper composes the target-area evidence bundle, target-area GIS/COG
scope, same-scale closure baseline, same-scale diagnostic baseline, and the
physical-credibility evidence map into one deterministic JSON/text
interpretation artifact. It stays inside the non-operational boundary and
does not authorize scale-up, annual-frequency, physical-probability, or
operational claims.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_diagnostic_interpretation_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_interpretation_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


TARGET_BUNDLE = _load_module("balfrin_target_area_interpretation_bundle", "summarize_balfrin_target_area_evidence_bundle.py")
TARGET_GIS = _load_module("balfrin_target_area_interpretation_gis", "summarize_balfrin_target_area_gis_cog_scope.py")
TSCHAMUT_CLOSURE = _load_module("balfrin_target_area_interpretation_closure", "summarize_tschamut_conditional_pilot_closure.py")
TSCHAMUT_DIAGNOSTIC = _load_module(
    "balfrin_target_area_interpretation_diagnostic",
    "summarize_tschamut_conditional_diagnostic_interpretation.py",
)
PHYSICAL = _load_module("balfrin_target_area_interpretation_physical", "map_physical_credibility_evidence_requirements.py")


class BalfrinTargetAreaInterpretationError(ValueError):
    """User-facing interpretation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="optional directory for the canonical JSON and text interpretation artifact",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinTargetAreaInterpretationError as exc:
        print(f"balfrin target-area interpretation error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(
        report,
        json_output=args.json_output,
        text_output=args.text_output,
        artifact_dir=args.artifact_dir,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["diagnostic_acceptance_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinTargetAreaInterpretationError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinTargetAreaInterpretationError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is not None and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required target-area interpretation inputs are missing")
    if evidence_override is not None and isinstance(evidence_override.get("target_area_diagnostic_interpretation_report"), dict):
        return dict(evidence_override["target_area_diagnostic_interpretation_report"])

    if evidence_override is None:
        return build_current_report()
    return build_current_report_with_override(evidence_override)


def build_current_report() -> dict[str, Any]:
    target_area_bundle = section_or_build(
        None,
        "target_area_evidence_bundle_report",
        TARGET_BUNDLE.build_current_report,
    )
    target_area_gis_scope = section_or_build(
        None,
        "target_area_gis_scope_report",
        TARGET_GIS.build_report,
        artifact_root=TARGET_GIS.DEFAULT_ARTIFACT_ROOT,
        converted_package_root=None,
        scope_summary_path=TARGET_GIS.DEFAULT_SCOPE_SUMMARY_PATH,
    )
    tschamut_closure = section_or_build(
        None,
        "tschamut_closure_report",
        TSCHAMUT_CLOSURE.build_closure_report,
    )
    tschamut_diagnostic = section_or_build(
        None,
        "tschamut_diagnostic_report",
        TSCHAMUT_DIAGNOSTIC.build_report,
    )
    physical_report = section_or_build(
        None,
        "physical_credibility_report",
        PHYSICAL.build_report,
    )

    return assemble_report(
        target_area_bundle=target_area_bundle,
        target_area_gis_scope=target_area_gis_scope,
        tschamut_closure=tschamut_closure,
        tschamut_diagnostic=tschamut_diagnostic,
        physical_report=physical_report,
    )


def build_current_report_with_override(evidence_override: dict[str, Any]) -> dict[str, Any]:
    target_area_bundle = section_or_build(
        evidence_override,
        "target_area_evidence_bundle_report",
        TARGET_BUNDLE.build_current_report,
    )
    target_area_gis_scope = section_or_build(
        evidence_override,
        "target_area_gis_scope_report",
        TARGET_GIS.build_report,
        artifact_root=TARGET_GIS.DEFAULT_ARTIFACT_ROOT,
        converted_package_root=None,
        scope_summary_path=TARGET_GIS.DEFAULT_SCOPE_SUMMARY_PATH,
    )
    tschamut_closure = section_or_build(
        evidence_override,
        "tschamut_closure_report",
        TSCHAMUT_CLOSURE.build_closure_report,
    )
    tschamut_diagnostic = section_or_build(
        evidence_override,
        "tschamut_diagnostic_report",
        TSCHAMUT_DIAGNOSTIC.build_report,
    )
    physical_report = section_or_build(
        evidence_override,
        "physical_credibility_report",
        PHYSICAL.build_report,
    )

    return assemble_report(
        target_area_bundle=target_area_bundle,
        target_area_gis_scope=target_area_gis_scope,
        tschamut_closure=tschamut_closure,
        tschamut_diagnostic=tschamut_diagnostic,
        physical_report=physical_report,
    )


def section_or_build(
    evidence_override: dict[str, Any] | None,
    section_key: str,
    builder: Any,
    *builder_args: Any,
    **builder_kwargs: Any,
) -> dict[str, Any]:
    if evidence_override is not None and isinstance(evidence_override.get(section_key), dict):
        return dict(evidence_override[section_key])
    return dict(builder(*builder_args, **builder_kwargs))


def assemble_report(
    *,
    target_area_bundle: dict[str, Any],
    target_area_gis_scope: dict[str, Any],
    tschamut_closure: dict[str, Any],
    tschamut_diagnostic: dict[str, Any],
    physical_report: dict[str, Any],
) -> dict[str, Any]:
    execution_section = summarize_execution(target_area_bundle)
    output_section = summarize_output(target_area_bundle)
    uncertainty_section = summarize_uncertainty(tschamut_closure, tschamut_diagnostic)
    gis_section = summarize_gis(target_area_gis_scope)
    physical_section = summarize_physical(physical_report)
    baseline_comparison = summarize_baseline_comparison(
        target_area_bundle=target_area_bundle,
        target_area_gis_scope=target_area_gis_scope,
        tschamut_closure=tschamut_closure,
        tschamut_diagnostic=tschamut_diagnostic,
        physical_report=physical_report,
    )
    dominant_blockers = build_dominant_blockers(
        execution_section=execution_section,
        uncertainty_section=uncertainty_section,
        gis_section=gis_section,
        output_section=output_section,
        physical_section=physical_section,
        baseline_comparison=baseline_comparison,
    )
    satisfied_workflow_criteria = build_satisfied_workflow_criteria(
        execution_section=execution_section,
        gis_section=gis_section,
        output_section=output_section,
        physical_section=physical_section,
    )
    interpretation_status = derive_interpretation_status(
        execution_section=execution_section,
        uncertainty_section=uncertainty_section,
        gis_section=gis_section,
        output_section=output_section,
        physical_section=physical_section,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "target_area_id": str(target_area_bundle.get("pilot_id") or target_area_bundle.get("target_area_id") or "tschamut_public_pilot"),
        "run_id": str(target_area_bundle.get("run_id") or "tschamut_public_balfrin_target_area_demo_v1"),
        "interpretation_status": interpretation_status,
        "diagnostic_acceptance_status": "not_accepted" if interpretation_status != "measured_existing_artifacts" else "accepted_conditional_diagnostic",
        "usable_as_conditional_diagnostic_artifact": interpretation_status == "measured_existing_artifacts",
        "sections": {
            "execution": execution_section,
            "uncertainty": uncertainty_section,
            "gis": gis_section,
            "output": output_section,
            "physical_credibility": physical_section,
            "baseline_comparison": baseline_comparison,
            "scientific_meaning": build_scientific_meaning(interpretation_status, dominant_blockers, baseline_comparison),
        },
        "dominant_blockers": dominant_blockers,
        "satisfied_workflow_criteria": satisfied_workflow_criteria,
        "claim_boundaries": claim_boundaries(target_area_bundle, physical_section),
        "evidence_sources": evidence_sources(),
        "source_paths": source_paths(target_area_bundle, target_area_gis_scope, physical_report),
        "blocked_reason": "none" if interpretation_status != "blocked_missing_inputs" else "required target-area interpretation inputs are missing",
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def summarize_execution(target_area_bundle: dict[str, Any]) -> dict[str, Any]:
    bundle_summary = dict(target_area_bundle.get("bundle_summary") or {})
    return {
        "status": str(target_area_bundle.get("bundle_status") or "unknown"),
        "summary": str(bundle_summary.get("summary") or "target-area evidence bundle summary unavailable"),
        "blockers": list(bundle_summary.get("blockers") or []),
        "section_counts": dict(bundle_summary.get("section_counts") or {}),
        "section_provenance_profile": list(target_area_bundle.get("section_provenance_profile") or []),
        "claim_boundaries": dict(target_area_bundle.get("claim_boundaries") or {}),
    }


def summarize_uncertainty(tschamut_closure: dict[str, Any], tschamut_diagnostic: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(tschamut_diagnostic.get("canonical_interpretation") or {})
    blocker_fields = dict(canonical.get("blockers") or {})
    closure_semantics = dict(canonical.get("closure_semantics") or {})
    summary = dict(canonical.get("summary") or {})
    return {
        "status": str(tschamut_diagnostic.get("scientific_delta_status") or "unknown"),
        "summary": str(summary.get("summary") or canonical.get("interpretation_delta", {}).get("summary") or "same-scale uncertainty remains bounded but unresolved"),
        "closure_status": str(tschamut_closure.get("closure_status") or "unknown"),
        "interpretation_status": str(tschamut_diagnostic.get("interpretation_status") or "unknown"),
        "same_scale_closure_status": str(closure_semantics.get("current_closure_status") or tschamut_closure.get("closure_status") or "unknown"),
        "same_scale_interpretation_status": str(
            closure_semantics.get("current_interpretation_status") or tschamut_diagnostic.get("interpretation_status") or "unknown"
        ),
        "closure_limiting_layers": list(blocker_fields.get("closure_limiting_layers", {}).get("layer_keys") or []),
        "deferrable_layers": list(blocker_fields.get("closure_limiting_layers", {}).get("deferrable_layer_keys") or []),
        "physical_credibility_limits": dict(blocker_fields.get("physical_credibility_limits") or {}),
        "runtime_output_sufficiency": dict(blocker_fields.get("runtime_output_sufficiency") or {}),
        "gis_product_scope": dict(blocker_fields.get("gis_product_scope") or {}),
        "portability_status": dict(blocker_fields.get("portability_status") or {}),
    }


def summarize_gis(target_area_gis_scope: dict[str, Any]) -> dict[str, Any]:
    target_summary = dict(target_area_gis_scope.get("target_area_demo_scope_summary") or {})
    non_operational = dict(target_area_gis_scope.get("target_area_demo_non_operational_boundaries") or {})
    cog_expectation = dict(target_area_gis_scope.get("target_area_demo_cog_export_expectation") or {})
    return {
        "status": str(target_area_gis_scope.get("report_status") or "unknown"),
        "scope_classification": str(target_area_gis_scope.get("scope_classification") or "unknown"),
        "demo_usability_status": str(target_area_gis_scope.get("demo_usability_status") or "unknown"),
        "summary": str(target_area_gis_scope.get("demo_usability_summary") or target_summary.get("summary") or "GIS scope summary unavailable"),
        "non_operational_boundaries": non_operational,
        "cog_export_expectation": cog_expectation,
        "claim_boundaries": dict(target_area_gis_scope.get("claim_boundaries") or {}),
        "target_area_demo_scope_summary": target_summary,
    }


def summarize_output(target_area_bundle: dict[str, Any]) -> dict[str, Any]:
    probe_metrics = dict(target_area_bundle.get("probe_metrics_report") or {})
    return {
        "status": str(probe_metrics.get("report_status") or probe_metrics.get("metrics_contract_status") or "unknown"),
        "metrics_contract_status": str(probe_metrics.get("metrics_contract_status") or "unknown"),
        "summary": str(
            probe_metrics.get("summary")
            or probe_metrics.get("metrics_contract_summary")
            or "probe-metrics evidence remains blocked or unavailable"
        ),
        "missing_mandatory_metrics": list(
            probe_metrics.get("metrics_contract_missing_metrics")
            or probe_metrics.get("missing_mandatory_metrics")
            or []
        ),
        "unavailable_ancillary_metrics": list(
            probe_metrics.get("metrics_contract_ancillary_unavailable_metrics")
            or probe_metrics.get("unavailable_ancillary_metrics")
            or []
        ),
        "blockers": list(probe_metrics.get("missing_inputs") or probe_metrics.get("blockers") or []),
    }


def summarize_physical(physical_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": str(physical_report.get("physical_credibility_requirements_status") or "unknown"),
        "current_physical_credibility_status": str(physical_report.get("current_physical_credibility_status") or "unknown"),
        "calibration_status": str(physical_report.get("calibration_status") or "unknown"),
        "validation_status": str(physical_report.get("validation_status") or "unknown"),
        "summary": str(
            (physical_report.get("evidence_acquisition_summary") or {}).get("first_actionable_category")
            or "physical-credibility evidence requirements remain mapped to current gaps"
        ),
        "evidence_acquisition_summary": dict(physical_report.get("evidence_acquisition_summary") or {}),
        "claim_boundaries": dict(physical_report.get("claim_boundaries") or {}),
    }


def summarize_baseline_comparison(
    *,
    target_area_bundle: dict[str, Any],
    target_area_gis_scope: dict[str, Any],
    tschamut_closure: dict[str, Any],
    tschamut_diagnostic: dict[str, Any],
    physical_report: dict[str, Any],
) -> dict[str, Any]:
    diagnostic_summary = dict((tschamut_diagnostic.get("canonical_interpretation") or {}).get("summary") or {})
    diagnostic_delta = dict((tschamut_diagnostic.get("canonical_interpretation") or {}).get("interpretation_delta") or {})
    return {
        "status": "baseline_unchanged" if target_area_bundle.get("bundle_status") == "mixed_provenance" else "blocked_missing_inputs",
        "tschamut_baseline": {
            "closure_status": str(tschamut_closure.get("closure_status") or "unknown"),
            "current_blockers": list(tschamut_closure.get("current_blockers") or []),
            "current_follow_up_blockers": list(tschamut_closure.get("current_follow_up_blockers") or []),
        },
        "balfrin_baseline": {
            "scientific_delta_status": str(tschamut_diagnostic.get("scientific_delta_status") or "unknown"),
            "interpretation_delta_status": str(diagnostic_delta.get("status") or "unknown"),
            "interpretation_delta_summary": str(diagnostic_delta.get("summary") or "Balfrin evidence does not reclassify the current baseline"),
            "scientific_delta_summary": str(diagnostic_summary.get("summary") or diagnostic_delta.get("summary") or "baseline summary unavailable"),
        },
        "target_area_bundle": {
            "bundle_status": str(target_area_bundle.get("bundle_status") or "unknown"),
            "summary": str((target_area_bundle.get("bundle_summary") or {}).get("summary") or "target-area evidence bundle summary unavailable"),
        },
        "target_area_gis_scope": {
            "report_status": str(target_area_gis_scope.get("report_status") or "unknown"),
            "demo_usability_status": str(target_area_gis_scope.get("demo_usability_status") or "unknown"),
        },
        "physical_credibility": {
            "physical_credibility_requirements_status": str(
                physical_report.get("physical_credibility_requirements_status") or "unknown"
            ),
            "current_physical_credibility_status": str(physical_report.get("current_physical_credibility_status") or "unknown"),
        },
        "comparison_summary": (
            "The target-area package records real, deterministic evidence, but it does not improve the current Tschamut/Balfrin baseline: "
            "closure remains unaccepted, GIS scope remains non-operational, and physical credibility remains unestablished."
        ),
    }


def build_dominant_blockers(
    *,
    execution_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    gis_section: dict[str, Any],
    output_section: dict[str, Any],
    physical_section: dict[str, Any],
    baseline_comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers = [
        {
            "name": "probe_metrics_report",
            "status": output_section["status"],
            "summary": "The preserved probe-metrics report remains blocked or incomplete, so mandatory output evidence is missing.",
        },
        {
            "name": "target_area_gis_scope",
            "status": gis_section["status"],
            "summary": "The target-area GIS/COG scope remains blocked or template-only, so the GIS package is not a closure signal.",
        },
        {
            "name": "physical_credibility",
            "status": physical_section["status"],
            "summary": "Physical credibility remains mapped to current gaps and is not upgraded by the target-area run.",
        },
        {
            "name": "same_scale_baseline",
            "status": uncertainty_section["closure_status"],
            "summary": "The current Tschamut baseline closure and diagnostic interpretation remain inconclusive.",
        },
    ]
    if execution_section["status"] == "mixed_provenance":
        blockers.insert(
            0,
            {
                "name": "target_area_bundle_mixed_provenance",
                "status": execution_section["status"],
                "summary": "The target-area evidence bundle is mixed provenance, with measured, unavailable, and blocked sections kept separate.",
            },
        )
    return blockers


def build_satisfied_workflow_criteria(
    *,
    execution_section: dict[str, Any],
    gis_section: dict[str, Any],
    output_section: dict[str, Any],
    physical_section: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "deterministic_bundle_composition",
            "status": execution_section["status"],
            "summary": "The target-area evidence bundle is deterministic and keeps measured, unavailable, and blocked sections separate.",
        },
        {
            "name": "non_operational_gis_boundary",
            "status": gis_section["status"],
            "summary": "The GIS/COG scope summary preserves explicit non-operational boundaries and does not imply a hazard product.",
        },
        {
            "name": "claim_boundaries_explicit",
            "status": "present",
            "summary": "Operational, annual-frequency, physical-probability, risk, scale-up, and distributed-execution claims remain out of scope.",
        },
        {
            "name": "physical_credibility_boundaries_preserved",
            "status": physical_section["status"],
            "summary": "The physical-credibility evidence map keeps the current gaps visible instead of upgrading them.",
        },
        {
            "name": "output_blocker_visible",
            "status": output_section["status"],
            "summary": "The output blocker is preserved rather than hidden, so missing metrics remain explicit.",
        },
    ]


def derive_interpretation_status(
    *,
    execution_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    gis_section: dict[str, Any],
    output_section: dict[str, Any],
    physical_section: dict[str, Any],
) -> str:
    statuses = {
        execution_section["status"],
        uncertainty_section["status"],
        gis_section["status"],
        output_section["status"],
        physical_section["status"],
    }
    if statuses == {"blocked_missing_inputs"}:
        return "blocked_missing_inputs"
    if {"mixed_provenance", "template_only", "blocked_missing_inputs", "unavailable"} & statuses:
        return "mixed_provenance"
    return "measured_existing_artifacts"


def build_scientific_meaning(
    interpretation_status: str,
    dominant_blockers: list[dict[str, Any]],
    baseline_comparison: dict[str, Any],
) -> dict[str, Any]:
    blocker_names = [item["name"] for item in dominant_blockers]
    if interpretation_status == "blocked_missing_inputs":
        summary = (
            "The target-area interpretation is blocked because required evidence inputs are missing. "
            "No closure or scientific upgrade can be claimed."
        )
        meaning = "blocked"
    else:
        summary = (
            "The target-area run is a deterministic, non-operational diagnostic package. "
            "It demonstrates the frozen handoff and measured canonical evidence, but it does not close the scientific question or upgrade physical credibility."
        )
        meaning = "bounded_non_operational"
    return {
        "status": meaning,
        "summary": summary,
        "dominant_blockers": blocker_names,
        "baseline_position": baseline_comparison.get("comparison_summary"),
        "interpretation_rule": "do_not_accept_diagnostic_unless_criteria_are_actually_met",
    }


def claim_boundaries(target_area_bundle: dict[str, Any], physical_section: dict[str, Any]) -> dict[str, Any]:
    boundaries = dict(target_area_bundle.get("claim_boundaries") or {})
    boundaries.setdefault("operational_claims_allowed", False)
    boundaries.setdefault("physical_probability_claims_allowed", False)
    boundaries.setdefault("annual_frequency_claims_allowed", False)
    boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    boundaries.setdefault("scale_up_authorized", False)
    boundaries.setdefault("distributed_execution_authorized", False)
    physical_boundaries = dict(physical_section.get("claim_boundaries") or {})
    for key, value in physical_boundaries.items():
        if key.endswith("_allowed") or key == "scale_up_authorized":
            boundaries[key] = bool(value)
    boundaries.setdefault("notes", [])
    if not boundaries["operational_claims_allowed"]:
        notes = list(boundaries.get("notes") or [])
        notes.append("target-area diagnostic interpretation remains non-operational")
        boundaries["notes"] = notes
    return boundaries


def source_paths(
    target_area_bundle: dict[str, Any],
    target_area_gis_scope: dict[str, Any],
    physical_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "target_area_evidence_bundle": target_area_bundle.get("source_paths", {}),
        "target_area_gis_scope": target_area_gis_scope.get("source_paths", {}),
        "physical_credibility_requirements": "scripts/map_physical_credibility_evidence_requirements.py",
        "current_maturity_snapshot": "docs/current_maturity_snapshot.md",
    }


def evidence_sources() -> list[str]:
    return [
        "scripts/summarize_balfrin_target_area_evidence_bundle.py",
        "scripts/summarize_balfrin_target_area_gis_cog_scope.py",
        "scripts/summarize_tschamut_conditional_pilot_closure.py",
        "scripts/summarize_tschamut_conditional_diagnostic_interpretation.py",
        "scripts/map_physical_credibility_evidence_requirements.py",
        "docs/current_maturity_snapshot.md",
    ]


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "target_area_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_balfrin_target_area_demo_v1",
        "interpretation_status": "blocked_missing_inputs",
        "diagnostic_acceptance_status": "blocked_missing_inputs",
        "usable_as_conditional_diagnostic_artifact": False,
        "sections": {
            "execution": {"status": "blocked_missing_inputs", "summary": reason, "blockers": list(missing_inputs)},
            "uncertainty": {"status": "blocked_missing_inputs", "summary": reason, "blockers": list(missing_inputs)},
            "gis": {"status": "blocked_missing_inputs", "summary": reason, "blockers": list(missing_inputs)},
            "output": {"status": "blocked_missing_inputs", "summary": reason, "blockers": list(missing_inputs)},
            "physical_credibility": {"status": "blocked_missing_inputs", "summary": reason, "blockers": list(missing_inputs)},
            "baseline_comparison": {"status": "blocked_missing_inputs", "comparison_summary": reason},
            "scientific_meaning": {"status": "blocked", "summary": reason, "dominant_blockers": list(missing_inputs)},
        },
        "dominant_blockers": list(missing_inputs),
        "satisfied_workflow_criteria": [],
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "notes": ["target-area diagnostic interpretation remains blocked"],
        },
        "evidence_sources": [],
        "source_paths": {},
        "blocked_reason": reason,
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Diagnostic Interpretation",
        f"schema_version: {report['schema_version']}",
        f"interpretation_status: {report['interpretation_status']}",
        f"diagnostic_acceptance_status: {report['diagnostic_acceptance_status']}",
        f"usable_as_conditional_diagnostic_artifact: {report['usable_as_conditional_diagnostic_artifact']}",
    ]
    for section_name in ("execution", "uncertainty", "gis", "output", "physical_credibility", "baseline_comparison", "scientific_meaning"):
        section = report["sections"][section_name]
        lines.append(f"{section_name}:")
        for key, value in section.items():
            if key == "summary":
                lines.append(f"  summary: {value}")
            elif key == "comparison_summary":
                lines.append(f"  comparison_summary: {value}")
            elif isinstance(value, list):
                lines.append(f"  {key}: {json.dumps(value, sort_keys=True)}")
            elif isinstance(value, dict):
                lines.append(f"  {key}: {json.dumps(value, sort_keys=True)}")
            else:
                lines.append(f"  {key}: {value}")
    lines.append("dominant_blockers:")
    for blocker in report["dominant_blockers"]:
        lines.append(f"  - {blocker['name']} [{blocker['status']}] {blocker['summary']}")
    lines.append("satisfied_workflow_criteria:")
    for criterion in report["satisfied_workflow_criteria"]:
        lines.append(f"  - {criterion['name']} [{criterion['status']}] {criterion['summary']}")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        if key == "notes":
            lines.append(f"  notes: {', '.join(value) if value else 'none'}")
        else:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        json_output = json_output or artifact_dir / f"{SCHEMA_VERSION}.json"
        text_output = text_output or artifact_dir / f"{SCHEMA_VERSION}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
