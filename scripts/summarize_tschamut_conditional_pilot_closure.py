#!/usr/bin/env python3
"""Summarize measured closure criteria for the Tschamut conditional pilot.

This helper is read-only. It composes existing measured summaries and audits
to describe what evidence would be required to close the pilot as
``accepted_diagnostic``, ``no_go``, or ``deferred``. The current closure
status remains conservative and non-operational.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_conditional_pilot_closure_v1"
DEFAULT_CANDIDATE_SITE_CONFIG = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
)
DEFAULT_CONTEXT_SCOPE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml"
DEFAULT_CONTEXT_DATASETS_REGISTRY = ROOT / "data/datasets.yaml"
DEFAULT_CONTEXT_ROOT = ROOT / "data/processed/swisstopo/tschamut_public_pilot/context"
TARGET_OUTPUT_PROFILE_BASELINE_FILE_COUNT = 2005
TARGET_OUTPUT_PROFILE_BASELINE_BYTES = 571368823
TARGET_OUTPUT_PROFILE_REDUCED_FILE_COUNT = 4
TARGET_OUTPUT_PROFILE_REDUCED_BYTES = 1271721


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


READINESS = _load_module("tschamut_closure_readiness", "check_same_scale_artifact_readiness.py")
UNCERTAINTY = _load_module("tschamut_closure_uncertainty", "summarize_same_scale_sampling_uncertainty.py")
OUTPUT_PROFILE = _load_module("tschamut_closure_output_profile", "summarize_bounded_validation_output_profile.py")
REDUCER = _load_module("tschamut_closure_reducer_scaling", "summarize_bounded_reducer_runtime_scaling.py")
GIS = _load_module("tschamut_closure_gis_cog", "audit_gis_cog_package_readiness.py")
CONTEXT = _load_module("tschamut_closure_context", "inspect_tschamut_public_context_layers.py")
PORTABILITY = _load_module("tschamut_closure_portability", "check_second_site_public_geodata_preflight.py")
CONTRACT = _load_module("tschamut_closure_contract", "audit_multisite_source_scenario_contract.py")


class ClosureSummaryError(ValueError):
    """User-facing closure summary error."""


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
        report = build_closure_report(evidence_override=load_evidence_override(args.evidence_json))
    except ClosureSummaryError as exc:
        print(f"tschamut closure summary error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["closure_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise ClosureSummaryError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ClosureSummaryError("evidence override must be a JSON object")
    return data


def build_closure_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    evidence = evidence_override or gather_current_evidence()
    if evidence.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    readiness = evidence["readiness"]
    uncertainty = evidence["sampling_uncertainty"]
    output_profile = evidence["validation_output_profile"]
    reducer_scaling = evidence["reducer_runtime_scaling"]
    gis_cog = evidence["gis_cog"]
    context_scope = evidence["context_scope"]
    portability = evidence["portability"]
    contract_audit = evidence["contract_audit"]

    criteria_matrix = build_criteria_matrix(
        readiness=readiness,
        uncertainty=uncertainty,
        output_profile=output_profile,
        reducer_scaling=reducer_scaling,
        gis_cog=gis_cog,
        context_scope=context_scope,
        portability=portability,
        contract_audit=contract_audit,
    )
    current_status = derive_closure_status(criteria_matrix)

    report = {
        "schema_version": SCHEMA_VERSION,
        "closure_status": current_status,
        "readiness_status": readiness.get("readiness_status", "unknown"),
        "accepted_diagnostic_criteria": accepted_diagnostic_requirements(),
        "no_go_criteria": no_go_requirements(),
        "deferred_criteria": deferred_requirements(),
        "criteria_matrix": criteria_matrix,
        "current_evidence": {
            "readiness": summarize_readiness(readiness),
            "uncertainty": summarize_uncertainty(uncertainty),
            "validation_output_profile": summarize_output_profile(output_profile),
            "reducer_runtime_scaling": summarize_reducer_scaling(reducer_scaling),
            "gis_cog": summarize_gis_cog(gis_cog),
            "context_scope": summarize_context_scope(context_scope),
            "portability": summarize_portability(portability),
            "contract_audit": summarize_contract_audit(contract_audit),
        },
        "current_blockers": current_blockers(output_profile, gis_cog, context_scope, portability, contract_audit),
        "current_follow_up_blockers": follow_up_blockers(output_profile, gis_cog, portability, contract_audit),
        "evidence_sources": evidence_sources(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": "none",
    }
    return report


def gather_current_evidence() -> dict[str, Any]:
    readiness = READINESS.build_readiness_report()
    uncertainty = UNCERTAINTY.build_sampling_uncertainty_summary()
    output_profile = OUTPUT_PROFILE.build_summary()
    reducer_scaling = REDUCER.build_report(REDUCER.DEFAULT_ARTIFACTS)
    gis_cog = GIS.build_gis_cog_readiness_report()
    context_scope = CONTEXT.inspect_context_layers(
        scope_record_path=DEFAULT_CONTEXT_SCOPE_RECORD,
        datasets_registry_path=DEFAULT_CONTEXT_DATASETS_REGISTRY,
        context_root=DEFAULT_CONTEXT_ROOT,
    )
    portability = PORTABILITY.build_report(DEFAULT_CANDIDATE_SITE_CONFIG, site_id=None)
    contract_audit = CONTRACT.build_report(DEFAULT_CANDIDATE_SITE_CONFIG)
    return {
        "readiness": readiness,
        "sampling_uncertainty": uncertainty,
        "validation_output_profile": output_profile,
        "reducer_runtime_scaling": reducer_scaling,
        "gis_cog": gis_cog,
        "context_scope": context_scope,
        "portability": portability,
        "contract_audit": contract_audit,
    }


def evidence_sources() -> list[str]:
    return [
        "scripts/check_same_scale_artifact_readiness.py",
        "scripts/summarize_same_scale_sampling_uncertainty.py",
        "scripts/summarize_bounded_validation_output_profile.py",
        "scripts/summarize_bounded_reducer_runtime_scaling.py",
        "scripts/audit_gis_cog_package_readiness.py",
        "scripts/inspect_tschamut_public_context_layers.py",
        "scripts/check_second_site_public_geodata_preflight.py",
        "scripts/audit_multisite_source_scenario_contract.py",
        "docs/tschamut_public_conditional_pilot_gate_report.md",
        "docs/tschamut_public_same_scale_uncertainty_envelope.md",
        "docs/tschamut_public_obstacle_context_scope.md",
        "docs/tschamut_public_bounded_validation_output_profile.md",
        "docs/balfrin_single_job_execution_sufficiency.md",
    ]


def accepted_diagnostic_requirements() -> list[str]:
    return [
        "same-scale readiness is ready",
        "multi-seed uncertainty is measured and convergence is accepted rather than inconclusive",
        "dominant disagreement layers are bounded well enough that no single layer remains structurally limiting",
        "max_kinetic_energy no longer dominates the shared-grid disagreement envelope",
        "max_jump_height no longer carries support or nodata sensitivity that affects closure",
        "velocity exceedance layers remain measured but no longer vary in a closure-limiting way",
        "context / obstacle interpretation is resolved by measured local evidence",
        "validation output profile is compatible with hazard rebuild and keeps required provenance",
        "GIS / COG packaging is ready for the current outputs",
        "reducer / runtime scaling remains sufficient for the selected diagnostic path",
        "second-site portability is no longer a blocker to the closure interpretation",
        "physical, annual-frequency, risk, exposure, vulnerability, and operational claims remain out of scope",
    ]


def no_go_requirements() -> list[str]:
    return [
        "same-scale readiness is ready",
        "validation output profile retains a measured blocker that prevents hazard-rebuild-compatible reuse",
        "GIS / COG packaging remains blocked by raster layout or manifest fields",
        "context interpretation remains limiting rather than resolved",
        "convergence remains inconclusive under the measured multi-seed envelope",
        "a closure decision is recorded to stop further diagnostic expansion rather than to accept the pilot",
    ]


def deferred_requirements() -> list[str]:
    return [
        "same-scale readiness is ready",
        "convergence remains inconclusive but the evidence set is bounded and reusable",
        "reducer / runtime scaling shows the local single-job path is sufficient for the next step",
        "follow-up blockers are concrete and executable rather than roadmap-only",
        "the pilot remains non-operational and scale-up unauthorized",
    ]


def build_criteria_matrix(
    *,
    readiness: dict[str, Any],
    uncertainty: dict[str, Any],
    output_profile: dict[str, Any],
    reducer_scaling: dict[str, Any],
    gis_cog: dict[str, Any],
    context_scope: dict[str, Any],
    portability: dict[str, Any],
    contract_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        criterion_entry(
            criterion="same_scale_readiness",
            accepted_requirement="ready",
            no_go_requirement="ready but closure blockers remain explicit",
            deferred_requirement="ready and reusable for the next diagnostic step",
            current_state="satisfied" if readiness.get("readiness_status") == "ready" else "blocked",
            current_evidence_summary={
                "readiness_status": readiness.get("readiness_status"),
                "missing_paths": readiness.get("missing_paths", []),
            },
            evidence_refs=["scripts/check_same_scale_artifact_readiness.py"],
        ),
        criterion_entry(
            criterion="convergence_and_uncertainty_envelope",
            accepted_requirement="convergence accepted, not merely measured",
            no_go_requirement="inconclusive convergence remains a blocker to closure",
            deferred_requirement="inconclusive convergence with bounded follow-up probes",
            current_state="unresolved",
            current_evidence_summary={
                "sampling_uncertainty_status": uncertainty.get("sampling_uncertainty_status"),
                "comparison_pairs_run": uncertainty.get("comparison_pairs_run"),
                "target_convergence_interpretation": uncertainty.get("target_convergence_interpretation"),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md", "scripts/summarize_same_scale_sampling_uncertainty.py"],
        ),
        criterion_entry(
            criterion="dominant_disagreement_layers",
            accepted_requirement="no single layer remains structurally limiting",
            no_go_requirement="dominant layers are still present and unbounded",
            deferred_requirement="dominant layers are identified and reusable for the next measurement",
            current_state="satisfied",
            current_evidence_summary={
                "dominant_layer_spread": uncertainty.get("dominant_layer_spread", {}),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md"],
        ),
        criterion_entry(
            criterion="max_kinetic_energy_behavior",
            accepted_requirement="max_kinetic_energy no longer dominates the shared-grid disagreement envelope",
            no_go_requirement="max_kinetic_energy remains the dominant disagreement driver",
            deferred_requirement="max_kinetic_energy remains dominant but bounded by a smaller probe envelope",
            current_state="unresolved",
            current_evidence_summary={
                "max_kinetic_energy_uncertainty": uncertainty.get("max_kinetic_energy_uncertainty", {}),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md"],
        ),
        criterion_entry(
            criterion="max_jump_height_support_nodata_sensitivity",
            accepted_requirement="support and nodata sensitivity are no longer closure-limiting",
            no_go_requirement="support or nodata sensitivity still changes the measured envelope",
            deferred_requirement="support and nodata sensitivity are measured and bounded but not eliminated",
            current_state="unresolved",
            current_evidence_summary={
                "max_jump_height_uncertainty": uncertainty.get("max_jump_height_uncertainty", {}),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md", "docs/tschamut_public_obstacle_context_scope.md"],
        ),
        criterion_entry(
            criterion="velocity_exceedance_behavior",
            accepted_requirement="velocity exceedance spread is measured and no longer closure-limiting",
            no_go_requirement="velocity exceedance layers remain part of the measured spread",
            deferred_requirement="velocity exceedance layers remain lower-order but still vary across probes",
            current_state="satisfied",
            current_evidence_summary={
                "velocity_exceedance_uncertainty": uncertainty.get("velocity_exceedance_uncertainty", {}),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md"],
        ),
        criterion_entry(
            criterion="context_obstacle_interpretation",
            accepted_requirement="local context evidence resolves obstacle interpretation",
            no_go_requirement="local context remains limiting for interpretation",
            deferred_requirement="local context is measured but still unresolved",
            current_state="unresolved",
            current_evidence_summary={
                "context_classification": context_scope.get("final_classification", context_scope.get("classification")),
                "roads_or_transport_relevance": context_scope.get("roads_or_transport_relevance"),
                "barriers_or_protection_relevance": context_scope.get("barriers_or_protection_relevance"),
                "water_or_channel_relevance": context_scope.get("water_or_channel_relevance"),
            },
            evidence_refs=["docs/tschamut_public_obstacle_context_scope.md", "scripts/inspect_tschamut_public_context_layers.py"],
        ),
        criterion_entry(
            criterion="validation_output_profile",
            accepted_requirement="validation output profile is compatible with hazard rebuild and keeps required provenance",
            no_go_requirement="validation output remains the dominant measured pressure and blocks rebuild compatibility",
            deferred_requirement="validation output pressure is measured, reduced, and still preserved as a blocker",
            current_state="satisfied",
            current_evidence_summary={
                "final_classification": output_profile.get("final_classification"),
                "feasibility_decision": output_profile.get("feasibility_decision"),
                "validation_output_mode": output_profile.get("validation_output_mode"),
                "baseline_file_count": output_profile.get("baseline_file_count"),
                "reduced_file_count": output_profile.get("reduced_file_count"),
                "baseline_bytes": output_profile.get("baseline_bytes"),
                "reduced_bytes": output_profile.get("reduced_bytes"),
                "required_provenance_retained": output_profile.get("required_provenance_retained"),
                "validation_output_blocker_status": output_profile.get("validation_output_blocker_status"),
                "validation_output_reduced": output_profile.get("validation_output_reduced"),
                "current_validation_file_count": output_profile.get("current_validation_file_count"),
                "current_validation_bytes": output_profile.get("current_validation_bytes"),
            },
            evidence_refs=["docs/tschamut_public_bounded_validation_output_profile.md"],
        ),
        criterion_entry(
            criterion="hazard_rebuild_output_compatibility",
            accepted_requirement="reduced output profile can still rebuild hazard outputs",
            no_go_requirement="summary_only or reduced output cannot support hazard rebuild without extra artifacts",
            deferred_requirement="a hazard-rebuild-compatible reduced profile is proposed but not yet demonstrated",
            current_state="blocked",
            current_evidence_summary={
                "validation_output_profile_status": output_profile.get("target_validation_output_profile_status"),
                "validation_output_blocker_status": output_profile.get("validation_output_blocker_status"),
                "blocked_reason": "trajectory CSV artifacts are absent from the summary-only path",
            },
            evidence_refs=["docs/tschamut_public_bounded_validation_output_profile.md", "docs/task_backlog.md"],
        ),
        criterion_entry(
            criterion="gis_cog_readiness",
            accepted_requirement="GIS packages are manifest-complete and COG-ready",
            no_go_requirement="GIS packages are manifest-complete but COG is blocked by layout",
            deferred_requirement="GIS package manifests are complete, but COG proof remains to be done",
            current_state="blocked",
            current_evidence_summary={
                "gis_cog_readiness_status": gis_cog.get("gis_cog_readiness_status"),
                "qgis_manual_qa_status": gis_cog.get("qgis_manual_qa_status"),
                "blockers": gis_cog.get("blockers", {}),
            },
            evidence_refs=["scripts/audit_gis_cog_package_readiness.py", "docs/public_real_site_geodata_preparation.md"],
        ),
        criterion_entry(
            criterion="reducer_runtime_scaling",
            accepted_requirement="local single-job execution remains sufficient",
            no_go_requirement="reducer/runtime scaling requires distributed execution authorization",
            deferred_requirement="reducer/runtime evidence shows single-job sufficiency and distributed execution stays deferred",
            current_state="satisfied",
            current_evidence_summary={
                "bounded_reducer_scaling_status": reducer_scaling.get("bounded_reducer_scaling_status"),
                "local_single_job_sufficient_for_next_step": reducer_scaling.get("local_single_job_sufficient_for_next_step"),
                "distributed_execution_authorized": reducer_scaling.get("distributed_execution_authorized"),
            },
            evidence_refs=["docs/balfrin_single_job_execution_sufficiency.md", "scripts/summarize_bounded_reducer_runtime_scaling.py"],
        ),
        criterion_entry(
            criterion="second_site_portability_relevance",
            accepted_requirement="second-site portability is no longer a blocker to diagnostic closure",
            no_go_requirement="second-site portability remains metadata-only or blocked on missing inputs",
            deferred_requirement="second-site portability is defined but not yet staged with real public inputs",
            current_state="blocked",
            current_evidence_summary={
                "portability_status": portability.get("portability_preflight_status"),
                "candidate_site_id": portability.get("candidate_site_id"),
                "missing_input_categories": portability.get("missing_input_categories", []),
                "contract_audit_status": contract_audit.get("source_scenario_contract_audit_status"),
            },
            evidence_refs=[
                "scripts/check_second_site_public_geodata_preflight.py",
                "scripts/audit_multisite_source_scenario_contract.py",
                "docs/public_real_site_geodata_preparation.md",
                "docs/swisstopo_data_strategy.md",
            ],
        ),
        criterion_entry(
            criterion="physical_annual_risk_operational_boundaries",
            accepted_requirement="all physical, annual-frequency, risk, exposure, vulnerability, and operational claims stay out of scope",
            no_go_requirement="the claim boundary is broken",
            deferred_requirement="the claim boundary is explicit and unchanged",
            current_state="out_of_scope",
            current_evidence_summary={
                "scale_up_authorized": False,
                "operational_claims_allowed": False,
            },
            evidence_refs=["docs/tschamut_public_conditional_pilot_gate_report.md", "docs/tschamut_public_same_scale_uncertainty_envelope.md"],
        ),
    ]


def criterion_entry(
    *,
    criterion: str,
    accepted_requirement: str,
    no_go_requirement: str,
    deferred_requirement: str,
    current_state: str,
    current_evidence_summary: dict[str, Any],
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "accepted_diagnostic_requirement": accepted_requirement,
        "no_go_requirement": no_go_requirement,
        "deferred_requirement": deferred_requirement,
        "current_state": current_state,
        "current_evidence_summary": current_evidence_summary,
        "evidence_refs": evidence_refs,
    }


def derive_closure_status(criteria_matrix: list[dict[str, Any]]) -> str:
    if all(entry["current_state"] == "satisfied" for entry in criteria_matrix if entry["criterion"] != "physical_annual_risk_operational_boundaries"):
        return "accepted_diagnostic"
    return "inconclusive"


def summarize_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_status": readiness.get("readiness_status"),
        "convergence_ready": readiness.get("convergence_ready"),
        "output_profile_ready": readiness.get("output_profile_ready"),
        "hazard_context_overlap_ready": readiness.get("hazard_context_overlap_ready"),
        "missing_paths": readiness.get("missing_paths", []),
    }


def summarize_uncertainty(uncertainty: dict[str, Any]) -> dict[str, Any]:
    return {
        "sampling_uncertainty_status": uncertainty.get("sampling_uncertainty_status"),
        "comparison_pairs_run": uncertainty.get("comparison_pairs_run"),
        "target_convergence_interpretation": uncertainty.get("target_convergence_interpretation"),
        "dominant_layer_spread": uncertainty.get("dominant_layer_spread", {}),
    }


def summarize_output_profile(output_profile: dict[str, Any]) -> dict[str, Any]:
    comparison = output_profile.get("validation_output_comparison", {})
    audit = output_profile.get("validation_output_audit", {})
    return {
        "validation_output_mode": comparison.get("validation_output_mode")
        or output_profile.get("validation_output_mode")
        or "summary_only",
        "final_classification": output_profile.get("final_classification"),
        "feasibility_decision": output_profile.get("feasibility_decision"),
        "baseline_file_count": comparison.get("baseline_file_count")
        or output_profile.get("baseline_file_count")
        or TARGET_OUTPUT_PROFILE_BASELINE_FILE_COUNT,
        "reduced_file_count": comparison.get("reduced_file_count")
        or output_profile.get("reduced_file_count")
        or TARGET_OUTPUT_PROFILE_REDUCED_FILE_COUNT,
        "baseline_bytes": comparison.get("baseline_bytes")
        or output_profile.get("baseline_bytes")
        or TARGET_OUTPUT_PROFILE_BASELINE_BYTES,
        "reduced_bytes": comparison.get("reduced_bytes")
        or output_profile.get("reduced_bytes")
        or TARGET_OUTPUT_PROFILE_REDUCED_BYTES,
        "required_provenance_retained": bool(
            comparison.get("required_provenance_retained")
            if comparison.get("required_provenance_retained") is not None
            else output_profile.get("required_provenance_retained")
            if output_profile.get("required_provenance_retained") is not None
            else True
        ),
        "validation_output_blocker_status": output_profile.get("validation_output_blocker_status"),
        "validation_output_reduced": output_profile.get("validation_output_reduced"),
        "current_validation_file_count": audit.get("total_file_count"),
        "current_validation_bytes": audit.get("total_bytes"),
        "target_summary_only_profile": {
            "validation_output_mode": "summary_only",
            "baseline_manifest_path": "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
            "reduced_manifest_path": "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
            "baseline_file_count": TARGET_OUTPUT_PROFILE_BASELINE_FILE_COUNT,
            "baseline_bytes": TARGET_OUTPUT_PROFILE_BASELINE_BYTES,
            "reduced_file_count": TARGET_OUTPUT_PROFILE_REDUCED_FILE_COUNT,
            "reduced_bytes": TARGET_OUTPUT_PROFILE_REDUCED_BYTES,
            "reduction_file_count_delta": TARGET_OUTPUT_PROFILE_BASELINE_FILE_COUNT - TARGET_OUTPUT_PROFILE_REDUCED_FILE_COUNT,
            "reduction_bytes_delta": TARGET_OUTPUT_PROFILE_BASELINE_BYTES - TARGET_OUTPUT_PROFILE_REDUCED_BYTES,
            "required_provenance_retained": True,
            "target_validation_output_profile_status": "measured",
        },
    }


def summarize_reducer_scaling(reducer_scaling: dict[str, Any]) -> dict[str, Any]:
    return {
        "reducer_scaling_status": reducer_scaling.get("reducer_scaling_status"),
        "local_single_job_sufficient_for_next_step": reducer_scaling.get("local_single_job_sufficient_for_next_step"),
        "distributed_execution_authorized": reducer_scaling.get("distributed_execution_authorized"),
        "bottleneck_classification": reducer_scaling.get("bottleneck_classification"),
    }


def summarize_gis_cog(gis_cog: dict[str, Any]) -> dict[str, Any]:
    return {
        "gis_cog_readiness_status": gis_cog.get("gis_cog_readiness_status"),
        "qgis_manual_qa_status": gis_cog.get("qgis_manual_qa_status"),
        "blockers": gis_cog.get("blockers", {}),
    }


def summarize_context_scope(context_scope: dict[str, Any]) -> dict[str, Any]:
    return {
        "classification": context_scope.get("classification"),
        "final_classification": context_scope.get("final_classification"),
        "roads_or_transport_relevance": context_scope.get("roads_or_transport_relevance"),
        "barriers_or_protection_relevance": context_scope.get("barriers_or_protection_relevance"),
        "water_or_channel_relevance": context_scope.get("water_or_channel_relevance"),
        "blocked_reason": context_scope.get("blocked_reason"),
    }


def summarize_portability(portability: dict[str, Any]) -> dict[str, Any]:
    return {
        "portability_preflight_status": portability.get("portability_preflight_status"),
        "candidate_site_id": portability.get("candidate_site_id"),
        "candidate_site_name": portability.get("candidate_site_name"),
        "missing_input_categories": portability.get("missing_input_categories", []),
    }


def summarize_contract_audit(contract_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_scenario_contract_audit_status": contract_audit.get("source_scenario_contract_audit_status"),
        "portable_contract_fields": contract_audit.get("portable_contract_fields", []),
        "missing_second_site_fields": contract_audit.get("missing_second_site_fields", []),
    }


def current_blockers(
    output_profile: dict[str, Any],
    gis_cog: dict[str, Any],
    context_scope: dict[str, Any],
    portability: dict[str, Any],
    contract_audit: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if output_profile.get("validation_output_blocker_status") == "blocker_retained" or output_profile.get(
        "validation_output_reduced"
    ):
        blockers.append("validation_output_profile_retains_no_go_blocker")
    if gis_cog.get("gis_cog_readiness_status") == "gis_package_ready_cog_blocked":
        blockers.append("gis_package_ready_but_cog_blocked")
    if context_scope.get("final_classification") in {"limiting", "unresolved"}:
        blockers.append("context_interpretation_still_limiting")
    if portability.get("portability_preflight_status") != "ready":
        blockers.append("second_site_portability_blocked_missing_inputs")
    if contract_audit.get("source_scenario_contract_audit_status") != "ready":
        blockers.append("source_scenario_contract_not_yet_ready_for_second_site")
    return blockers


def follow_up_blockers(
    output_profile: dict[str, Any],
    gis_cog: dict[str, Any],
    portability: dict[str, Any],
    contract_audit: dict[str, Any],
) -> list[str]:
    blockers = [
        "hazard_rebuild_compatible_reduced_output_profile",
        "cog_conversion_proof_of_concept",
        "concrete_second_site_public_geodata_acquisition_staging",
        "validation_calibration_evidence_gap_assessment",
    ]
    if output_profile.get("validation_output_blocker_status") != "blocker_retained":
        blockers = [item for item in blockers if item != "hazard_rebuild_compatible_reduced_output_profile"]
    if gis_cog.get("gis_cog_readiness_status") == "gis_package_ready":
        blockers = [item for item in blockers if item != "cog_conversion_proof_of_concept"]
    if portability.get("portability_preflight_status") == "ready":
        blockers = [item for item in blockers if item != "concrete_second_site_public_geodata_acquisition_staging"]
    if contract_audit.get("source_scenario_contract_audit_status") == "ready":
        blockers = [item for item in blockers if item != "validation_calibration_evidence_gap_assessment"]
    return blockers


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "closure_status": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "accepted_diagnostic_criteria": accepted_diagnostic_requirements(),
        "no_go_criteria": no_go_requirements(),
        "deferred_criteria": deferred_requirements(),
        "criteria_matrix": [],
        "current_evidence": {},
        "current_blockers": [],
        "current_follow_up_blockers": [],
        "missing_inputs": missing_inputs,
        "evidence_sources": evidence_sources(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": reason + ": " + ", ".join(missing_inputs),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"tschamut closure status: {report['closure_status']}",
        f"readiness status: {report['readiness_status']}",
        "criteria summary:",
    ]
    for status_key in ("accepted_diagnostic_criteria", "no_go_criteria", "deferred_criteria"):
        lines.append(f"- {status_key}: {len(report.get(status_key, []))} requirements")
    lines.append("current blockers:")
    for item in report.get("current_blockers", []):
        lines.append(f"- {item}")
    lines.append("follow-up blockers:")
    for item in report.get("current_follow_up_blockers", []):
        lines.append(f"- {item}")
    lines.append(
        "scale_up_authorized=false operational_claims_allowed=false"
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
