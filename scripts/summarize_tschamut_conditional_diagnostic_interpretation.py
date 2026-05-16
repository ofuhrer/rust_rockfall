#!/usr/bin/env python3
"""Summarize the canonical conditional diagnostic interpretation for Tschamut.

This helper is read-only. It composes existing evidence helpers into one
measured interpretation artifact without rerunning simulations, hazard
rebuilds, COG conversions, or second-site workflows.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_conditional_diagnostic_interpretation_v1"
DEFAULT_SECOND_SITE_CONFIG = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
)
DEFAULT_CO_G_PACKAGE_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1_cog_poc"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


READINESS = _load_module("tschamut_conditional_diagnostic_readiness", "check_same_scale_artifact_readiness.py")
UNCERTAINTY = _load_module("tschamut_conditional_diagnostic_uncertainty", "summarize_same_scale_sampling_uncertainty.py")
CLOSURE = _load_module("tschamut_conditional_diagnostic_closure", "summarize_tschamut_conditional_pilot_closure.py")
OUTPUT_PROFILE = _load_module("tschamut_conditional_diagnostic_output_profile", "check_hazard_rebuild_output_profile.py")
SPATIAL = _load_module("tschamut_conditional_diagnostic_spatial", "summarize_spatial_same_scale_uncertainty.py")
GIS = _load_module("tschamut_conditional_diagnostic_gis", "audit_gis_cog_package_readiness.py")
REDUCER = _load_module("tschamut_conditional_diagnostic_reducer", "summarize_bounded_reducer_runtime_scaling.py")
PHYSICAL = _load_module("tschamut_conditional_diagnostic_physical", "assess_validation_calibration_evidence_gaps.py")
PORTABILITY = _load_module("tschamut_conditional_diagnostic_portability", "check_second_site_public_geodata_preflight.py")
CONTRACT = _load_module("tschamut_conditional_diagnostic_contract", "audit_multisite_source_scenario_contract.py")


class DiagnosticInterpretationError(ValueError):
    """User-facing diagnostic interpretation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except DiagnosticInterpretationError as exc:
        print(f"tschamut diagnostic interpretation error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["interpretation_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise DiagnosticInterpretationError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DiagnosticInterpretationError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")
    if evidence_override and isinstance(evidence_override.get("diagnostic_interpretation_report"), dict):
        return dict(evidence_override["diagnostic_interpretation_report"])

    return _build_current_report()


@lru_cache(maxsize=1)
def _build_current_report() -> dict[str, Any]:
    readiness = CLOSURE.summarize_readiness(READINESS.build_readiness_report())
    uncertainty = CLOSURE.summarize_uncertainty(UNCERTAINTY.build_sampling_uncertainty_summary())
    spatial_raw = _build_spatial_evidence()
    spatial_summary = CLOSURE.summarize_spatial_uncertainty(spatial_raw)
    output_profile_report = OUTPUT_PROFILE.build_report(list(OUTPUT_PROFILE.DEFAULT_PROFILE_SPECS))
    output_profile_status = summarize_output_profile_status(output_profile_report)
    gis = CLOSURE.summarize_gis_cog(
        GIS.build_gis_cog_readiness_report(converted_package_roots=[DEFAULT_CO_G_PACKAGE_ROOT])
    )
    reducer = CLOSURE.summarize_reducer_scaling(REDUCER.build_report(REDUCER.DEFAULT_ARTIFACTS, allow_missing=True))
    physical = PHYSICAL.build_report()
    context_scope = CLOSURE.summarize_context_scope(_build_context_scope())
    portability_report = PORTABILITY.build_report(DEFAULT_SECOND_SITE_CONFIG, site_id=None)
    portability = CLOSURE.summarize_portability(portability_report)
    contract_report = CONTRACT.build_report(DEFAULT_SECOND_SITE_CONFIG)

    criteria_matrix = CLOSURE.build_criteria_matrix(
        readiness=readiness,
        uncertainty={
            "sampling_uncertainty_status": uncertainty.get("sampling_uncertainty_status"),
            "comparison_pairs_run": uncertainty.get("comparison_pairs_run"),
            "target_convergence_interpretation": uncertainty.get("target_convergence_interpretation"),
        },
        spatial_uncertainty={
            "spatial_uncertainty_status": spatial_raw.get("spatial_uncertainty_status"),
            "spatial_interpretation": spatial_raw.get("spatial_interpretation"),
            "overall_closure_role": spatial_raw.get("overall_closure_role"),
            "layer_summaries": spatial_raw.get("layer_summaries"),
            "dominant_layers_by_mean_range": spatial_raw.get("dominant_layers_by_mean_range", []),
            "dominant_layer_summaries": spatial_raw.get("dominant_layer_summaries", []),
            "mask_status": spatial_raw.get("mask_status"),
            "blocked_reason": spatial_raw.get("blocked_reason", ""),
        },
        output_profile={
            "validation_output_blocker_status": (
                "blocker_retained" if output_profile_report["profile_classifications"].get("target_summary_only") == "summary_only_not_rebuildable" else "clear"
            ),
            "validation_output_reduced": output_profile_report["profile_classifications"].get("target_summary_only")
            != "summary_only_not_rebuildable",
        },
        reducer_scaling=reducer,
        gis_cog=gis,
        context_scope=context_scope,
        portability=portability,
        contract_audit=contract_report,
    )
    closure_status = CLOSURE.derive_closure_status(criteria_matrix)
    current_blockers = CLOSURE.current_blockers(
        {
            "validation_output_blocker_status": (
                "blocker_retained" if output_profile_report["profile_classifications"].get("target_summary_only") == "summary_only_not_rebuildable" else "clear"
            ),
            "validation_output_reduced": output_profile_report["profile_classifications"].get("target_summary_only")
            != "summary_only_not_rebuildable",
        },
        gis,
        context_scope,
        portability,
        contract_report,
        {
            "spatial_interpretation": spatial_raw.get("spatial_interpretation"),
        },
    )
    follow_up_blockers = CLOSURE.follow_up_blockers(
        {
            "validation_output_blocker_status": (
                "blocker_retained" if output_profile_report["profile_classifications"].get("target_summary_only") == "summary_only_not_rebuildable" else "clear"
            ),
            "validation_output_reduced": output_profile_report["profile_classifications"].get("target_summary_only")
            != "summary_only_not_rebuildable",
        },
        gis,
        portability,
        contract_report,
    )
    claim_boundaries = summarize_claim_boundaries(physical)
    gis_cog_status = summarize_gis_cog_status(gis)
    runtime_status = summarize_runtime_status(reducer)
    portability_status = summarize_portability_status(portability_report, contract_report)

    report = {
        "schema_version": SCHEMA_VERSION,
        "interpretation_status": derive_interpretation_status(
            closure={"closure_status": closure_status},
            output_profile_status=output_profile_status,
            gis_cog_status=gis_cog_status,
            runtime_status=runtime_status,
            portability_status=portability_status,
            physical_status=physical,
        ),
        "closure_status": closure_status,
        "same_scale_readiness_status": readiness.get("readiness_status", "unknown"),
        "spatial_uncertainty_status": spatial_raw.get("spatial_uncertainty_status", "unknown"),
        "spatial_uncertainty_interpretation": spatial_summary,
        "dominant_scientific_blockers": dominant_scientific_blockers(
            {
                "closure_status": closure_status,
                "spatial_uncertainty_interpretation": spatial_summary,
                "criteria_matrix": criteria_matrix,
            }
        ),
        "scientific_closure_blockers": scientific_closure_blockers(
            {"current_blockers": current_blockers, "closure_status": closure_status}
        ),
        "workflow_product_blockers": workflow_product_blockers(output_profile_status, gis_cog_status),
        "portability_blockers": portability_blockers(portability_status),
        "physical_credibility_blockers": physical_credibility_blockers(physical),
        "output_profile_status": output_profile_status,
        "gis_cog_status": gis_cog_status,
        "runtime_scaling_status": runtime_status,
        "portability_status": portability_status,
        "physical_credibility_status": physical.get("physical_credibility_status", "unknown"),
        "claim_boundaries": claim_boundaries,
        "recommended_next_decision": recommended_next_decision(
            closure={"closure_status": closure_status},
            output_profile_status=output_profile_status,
            gis_cog_status=gis_cog_status,
            runtime_status=runtime_status,
            portability_status=portability_status,
            physical_status=physical,
        ),
        "current_evidence": {
            "readiness": {
                "readiness_status": readiness.get("readiness_status"),
                "missing_paths": readiness.get("missing_paths", []),
            },
            "closure": {
                "closure_status": closure_status,
                "current_blockers": current_blockers,
                "current_follow_up_blockers": follow_up_blockers,
                "spatial_uncertainty_interpretation": spatial_summary,
            },
            "output_profile": output_profile_status,
            "gis_cog": gis_cog_status,
            "runtime_scaling": runtime_status,
            "physical_credibility": {
                "physical_credibility_status": physical.get("physical_credibility_status", "unknown"),
                "calibration_status": physical.get("calibration_status", "unknown"),
                "validation_status": physical.get("validation_status", "unknown"),
            },
            "portability": portability_status,
            "source_scenario_contract": {
                "source_scenario_contract_audit_status": contract_report.get("source_scenario_contract_audit_status", "unknown"),
                "second_site_portability_status": contract_report.get("second_site_portability_status", "unknown"),
                "portable_contract_fields": contract_report.get("portable_contract_fields", []),
                "site_specific_contract_fields": contract_report.get("site_specific_contract_fields", []),
                "synthetic_contract_fixture_status": contract_report.get("synthetic_contract_fixture_status", {}),
            },
            "command_plan": {
                "command_plan_status": "ready",
                "command_group_key": "tschamut_same_scale::rebuildable_reduced_output",
                "command_group_present": True,
                "read_only": True,
                "blocked_template_commands": [],
            },
        },
        "evidence_sources": [
            "scripts/check_same_scale_artifact_readiness.py",
            "scripts/summarize_tschamut_conditional_pilot_closure.py",
            "scripts/check_hazard_rebuild_output_profile.py",
            "scripts/audit_gis_cog_package_readiness.py",
            "scripts/summarize_bounded_reducer_runtime_scaling.py",
            "scripts/assess_validation_calibration_evidence_gaps.py",
            "scripts/check_second_site_public_geodata_preflight.py",
            "scripts/audit_multisite_source_scenario_contract.py",
            "scripts/generate_pilot_command_plan.py",
            "docs/tschamut_public_conditional_pilot_gate_report.md",
            "docs/tschamut_public_same_scale_uncertainty_envelope.md",
            "docs/tschamut_public_bounded_validation_output_profile.md",
            "docs/public_real_site_geodata_preparation.md",
            "docs/swisstopo_data_strategy.md",
            "docs/balfrin_single_job_execution_sufficiency.md",
        ],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": runtime_status.get("distributed_execution_authorized", False),
    }
    return report


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    claim_boundaries = {
        "workflow_reproducibility": "present",
        "conditional_diagnostic_interpretation": "present",
        "physical_probability": "missing",
        "annual_frequency": "out_of_scope",
        "risk_exposure_vulnerability": "out_of_scope",
        "operational_use": "out_of_scope",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "interpretation_status": "blocked_missing_inputs",
        "closure_status": "blocked_missing_inputs",
        "same_scale_readiness_status": "blocked_missing_inputs",
        "spatial_uncertainty_status": "blocked_missing_inputs",
        "dominant_scientific_blockers": [],
        "scientific_closure_blockers": [],
        "workflow_product_blockers": [],
        "portability_blockers": [],
        "physical_credibility_blockers": [],
        "output_profile_status": {"status": "blocked_missing_inputs"},
        "gis_cog_status": {"status": "blocked_missing_inputs"},
        "runtime_scaling_status": {"status": "blocked_missing_inputs"},
        "portability_status": {"status": "blocked_missing_inputs"},
        "physical_credibility_status": "blocked_missing_inputs",
        "claim_boundaries": claim_boundaries,
        "recommended_next_decision": reason,
        "current_evidence": {"missing_inputs": list(missing_inputs)},
        "evidence_sources": [],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "blocked_reason": reason,
        "missing_inputs": list(missing_inputs),
    }


def summarize_output_profile_status(output_profile: dict[str, Any]) -> dict[str, Any]:
    classifications = output_profile.get("profile_classifications", {})
    summary_only_status = classifications.get("target_summary_only", "unknown")
    rebuildable_reduced_status = classifications.get("target_rebuildable_reduced", "unknown")
    return {
        "target_summary_only": summary_only_status,
        "legacy_summary_only_status": summary_only_status,
        "target_rebuildable_reduced": rebuildable_reduced_status,
        "native_rebuildable_reduced_status": rebuildable_reduced_status,
        "rebuildable_reduced_profile": output_profile.get("rebuildable_reduced_profile", {}),
        "hazard_rebuild_output_profile_status": output_profile.get("hazard_rebuild_output_profile_status", "unknown"),
        "missing_summary_only_artifacts": output_profile.get("missing_summary_only_artifacts", {}),
        "command_plan_addressable": True,
        "command_plan_group_key": "tschamut_same_scale::rebuildable_reduced_output",
        "command_plan_group_present": True,
    }


def summarize_gis_cog_status(gis: dict[str, Any]) -> dict[str, Any]:
    converted_package_status = gis.get("converted_package_status", {})
    return {
        "standard_package_status": gis.get("gis_cog_readiness_status", "unknown"),
        "readiness_status": gis.get("readiness_status", "unknown"),
        "converted_sample_status": gis.get("converted_sample_status", "not_provided"),
        "converted_package_readiness_status": gis.get("converted_package_readiness_status", "not_provided"),
        "any_converted_package_ready": gis.get("any_converted_package_ready", False),
        "converted_package_status": converted_package_status,
        "qgis_manual_qa_status": gis.get("qgis_manual_qa_status", "not_run"),
        "scientific_acceptance_status": gis.get("scientific_acceptance_status", "inconclusive"),
        "command_plan_addressable": True,
        "command_plan_group_key": "tschamut_same_scale::gis_cog_package_conversion",
    }


def summarize_runtime_status(reducer: dict[str, Any]) -> dict[str, Any]:
    return {
        "reducer_scaling_status": reducer.get("reducer_scaling_status", "unknown"),
        "bottleneck_classification": reducer.get("bottleneck_classification", "unknown"),
        "local_single_job_sufficient_for_next_step": reducer.get("local_single_job_sufficient_for_next_step", False),
        "distributed_execution_authorized": reducer.get("distributed_execution_authorized", False),
        "comparison_pairs": reducer.get("comparison_pairs", []),
        "file_counts": reducer.get("file_counts", {}),
        "byte_counts": reducer.get("byte_counts", {}),
    }


def summarize_portability_status(portability: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "portability_preflight_status": portability.get("portability_preflight_status", "unknown"),
        "candidate_site_id": portability.get("candidate_site_id", "unknown"),
        "candidate_site_name": portability.get("candidate_site_name", "unknown"),
        "candidate_selection_rationale": portability.get("candidate_selection_rationale", ""),
        "missing_input_categories": portability.get("missing_input_categories", []),
        "missing_input_paths_or_patterns": portability.get("missing_input_paths_or_patterns", []),
        "source_scenario_contract_audit_status": contract.get("source_scenario_contract_audit_status", "unknown"),
        "reusable_workflow_components": contract.get("portable_contract_fields", []),
        "site_specific_required_inputs": contract.get("site_specific_contract_fields", []),
        "deferred_public_context_status": portability.get("portability_preflight_status") == "deferred_public_context_inputs",
    }


def summarize_claim_boundaries(physical: dict[str, Any]) -> dict[str, Any]:
    matrix = physical.get("claim_boundary_matrix", [])
    return {
        "matrix": matrix,
        "physical_credibility_status": physical.get("physical_credibility_status", "unknown"),
        "calibration_status": physical.get("calibration_status", "unknown"),
        "validation_status": physical.get("validation_status", "unknown"),
        "annual_frequency_claims_allowed": physical.get("annual_frequency_claims_allowed", False),
        "risk_exposure_vulnerability_claims_allowed": physical.get("risk_exposure_vulnerability_claims_allowed", False),
        "operational_claims_allowed": physical.get("operational_claims_allowed", False),
        "scale_up_authorized": physical.get("scale_up_authorized", False),
    }


def _build_spatial_evidence() -> dict[str, Any]:
    return SPATIAL.build_report(
        manifest_paths=list(SPATIAL.DEFAULT_MANIFESTS),
        hazard_layers=tuple(SPATIAL.DEFAULT_HAZARD_LAYERS),
        top_n=3,
    )


def _build_context_scope() -> dict[str, Any]:
    context_module = _load_module("tschamut_conditional_diagnostic_context", "inspect_tschamut_public_context_layers.py")
    return context_module.inspect_context_layers(
        scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
        datasets_registry_path=ROOT / "data/datasets.yaml",
        context_root=ROOT / "data/processed/swisstopo/tschamut_public_pilot/context",
    )


def dominant_scientific_blockers(closure: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if closure.get("closure_status") == "inconclusive":
        blockers.append("closure_status_inconclusive")
    spatial = closure.get("spatial_uncertainty_interpretation", {})
    if spatial.get("overall_closure_role") == "closure_limiting":
        blockers.append("spatial_uncertainty_support_nodata_dominates_closure")
    layer_roles = spatial.get("layer_roles", {})
    for layer_key in ("max_kinetic_energy", "max_jump_height"):
        role = (layer_roles.get(layer_key) or {}).get("closure_role")
        if role == "closure_limiting":
            blockers.append(f"{layer_key}_closure_limiting")
    if (layer_roles.get("velocity_exceedance_5mps") or {}).get("closure_role") == "deferrable":
        blockers.append("velocity_exceedance_5mps_deferrable")
    if closure.get("criteria_matrix"):
        for entry in closure["criteria_matrix"]:
            if entry.get("criterion") == "context_obstacle_interpretation" and entry.get("current_state") == "unresolved":
                blockers.append("context_interpretation_remains_limiting")
    return blockers


def scientific_closure_blockers(closure: dict[str, Any]) -> list[str]:
    return [
        blocker
        for blocker in closure.get("current_blockers", [])
        if blocker
        in {
            "convergence_inconclusive",
            "spatial_uncertainty_support_nodata_dominates_closure",
            "context_interpretation_still_limiting",
            "max_kinetic_energy_closure_limiting",
            "max_jump_height_closure_limiting",
        }
    ]


def workflow_product_blockers(output_profile_status: dict[str, Any], gis_cog_status: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if output_profile_status.get("target_summary_only") == "summary_only_not_rebuildable":
        blockers.append("summary_only_not_rebuildable")
    if gis_cog_status.get("standard_package_status") == "gis_package_ready_cog_blocked":
        blockers.append("standard_gis_roots_cog_blocked")
    return blockers


def portability_blockers(portability_status: dict[str, Any]) -> list[str]:
    blockers = []
    if portability_status.get("portability_preflight_status") == "deferred_public_context_inputs":
        blockers.append("public_context_inputs_deferred")
    if portability_status.get("portability_preflight_status") == "blocked_missing_inputs":
        blockers.append("public_context_inputs_missing")
    if portability_status.get("source_scenario_contract_audit_status") == "blocked_missing_inputs":
        blockers.append("source_scenario_contract_still_partial")
    return blockers


def physical_credibility_blockers(physical: dict[str, Any]) -> list[str]:
    blockers = []
    if physical.get("physical_credibility_status") == "not_established":
        blockers.append("physical_credibility_not_established")
    if physical.get("calibration_status") == "missing":
        blockers.append("calibration_missing")
    if physical.get("validation_status") == "partial":
        blockers.append("validation_partial")
    return blockers


def derive_interpretation_status(
    *,
    closure: dict[str, Any],
    output_profile_status: dict[str, Any],
    gis_cog_status: dict[str, Any],
    runtime_status: dict[str, Any],
    portability_status: dict[str, Any],
    physical_status: dict[str, Any],
) -> str:
    if any(
        key == "blocked_missing_inputs"
        for key in (
            closure.get("closure_status"),
            output_profile_status.get("target_summary_only"),
            gis_cog_status.get("standard_package_status"),
            portability_status.get("portability_preflight_status"),
            physical_status.get("physical_credibility_status"),
        )
    ):
        return "blocked_missing_inputs"
    if closure.get("closure_status") == "accepted_diagnostic":
        return "accepted_diagnostic"
    if closure.get("closure_status") == "no_go":
        return "no_go"
    if closure.get("closure_status") == "deferred":
        return "deferred"
    if runtime_status.get("local_single_job_sufficient_for_next_step") is False:
        return "deferred"
    return "inconclusive_conditional_diagnostic"


def recommended_next_decision(
    *,
    closure: dict[str, Any],
    output_profile_status: dict[str, Any],
    gis_cog_status: dict[str, Any],
    runtime_status: dict[str, Any],
    portability_status: dict[str, Any],
    physical_status: dict[str, Any],
) -> str:
    if closure.get("closure_status") == "inconclusive":
        return (
            "Retain the conditional diagnostic interpretation as inconclusive; "
            "use the command-plan-addressable reduced-output and COG proof paths for workflow work, "
            "but do not claim acceptance, no-go, scale-up, or operational readiness."
        )
    if portability_status.get("portability_preflight_status") == "deferred_public_context_inputs":
        return (
            "Keep the pilot diagnostic; portable public-context staging remains deferred and "
            "physical credibility is still not established."
        )
    return (
        "Continue with the current conservative interpretation and keep physical, operational, "
        "and scale-up claims out of scope."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"interpretation_status: {report['interpretation_status']}",
        f"closure_status: {report['closure_status']}",
        f"same_scale_readiness_status: {report['same_scale_readiness_status']}",
        f"spatial_uncertainty_status: {report['spatial_uncertainty_status']}",
        "dominant_scientific_blockers:",
    ]
    for blocker in report.get("dominant_scientific_blockers", []):
        lines.append(f"  - {blocker}")
    lines.append("workflow_product_blockers:")
    for blocker in report.get("workflow_product_blockers", []):
        lines.append(f"  - {blocker}")
    lines.append("portability_blockers:")
    for blocker in report.get("portability_blockers", []):
        lines.append(f"  - {blocker}")
    lines.append("physical_credibility_blockers:")
    for blocker in report.get("physical_credibility_blockers", []):
        lines.append(f"  - {blocker}")
    lines.extend(
        [
            f"legacy_summary_only_status: {report['output_profile_status'].get('legacy_summary_only_status')}",
            f"native_rebuildable_reduced_status: {report['output_profile_status'].get('native_rebuildable_reduced_status')}",
            f"standard_gis_root_status: {report['gis_cog_status'].get('standard_package_status')}",
            f"converted_package_readiness_status: {report['gis_cog_status'].get('converted_package_readiness_status')}",
            f"any_converted_package_ready: {str(report['gis_cog_status'].get('any_converted_package_ready', False)).lower()}",
            f"output_profile_status: {json.dumps(report['output_profile_status'], sort_keys=True)}",
            f"gis_cog_status: {json.dumps(report['gis_cog_status'], sort_keys=True)}",
            f"runtime_scaling_status: {json.dumps(report['runtime_scaling_status'], sort_keys=True)}",
            f"portability_status: {json.dumps(report['portability_status'], sort_keys=True)}",
            f"physical_credibility_status: {report['physical_credibility_status']}",
            f"claim_boundaries: {json.dumps(report['claim_boundaries'], sort_keys=True)}",
            f"recommended_next_decision: {report['recommended_next_decision']}",
            f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
            f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
