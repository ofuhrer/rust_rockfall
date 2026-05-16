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
SPATIAL = _load_module("tschamut_closure_spatial", "summarize_spatial_same_scale_uncertainty.py")
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
    spatial_uncertainty = evidence["spatial_uncertainty"]
    output_profile = evidence["validation_output_profile"]
    reducer_scaling = evidence["reducer_runtime_scaling"]
    gis_cog = evidence["gis_cog"]
    context_scope = evidence["context_scope"]
    portability = evidence["portability"]
    contract_audit = evidence["contract_audit"]

    criteria_matrix = build_criteria_matrix(
        readiness=readiness,
        uncertainty=uncertainty,
        spatial_uncertainty=spatial_uncertainty,
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
        "spatial_uncertainty_interpretation": summarize_spatial_uncertainty(spatial_uncertainty),
        "current_evidence": {
            "readiness": summarize_readiness(readiness),
            "uncertainty": summarize_uncertainty(uncertainty),
            "spatial_uncertainty_interpretation": summarize_spatial_uncertainty(spatial_uncertainty),
            "validation_output_profile": summarize_output_profile(output_profile),
            "reducer_runtime_scaling": summarize_reducer_scaling(reducer_scaling),
            "gis_cog": summarize_gis_cog(gis_cog),
            "context_scope": summarize_context_scope(context_scope),
            "portability": summarize_portability(portability),
            "contract_audit": summarize_contract_audit(contract_audit),
        },
        "current_blockers": current_blockers(
            output_profile,
            gis_cog,
            context_scope,
            portability,
            contract_audit,
            spatial_uncertainty,
        ),
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
    spatial_uncertainty = SPATIAL.build_report(
        manifest_paths=list(SPATIAL.DEFAULT_MANIFESTS),
        hazard_layers=tuple(SPATIAL.DEFAULT_HAZARD_LAYERS),
        top_n=8,
    )
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
        "spatial_uncertainty": spatial_uncertainty,
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
        "scripts/summarize_spatial_same_scale_uncertainty.py",
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
        "spatial uncertainty is localized rather than support/nodata dominated",
        "dominant disagreement layers are not closure-limiting",
        "max_kinetic_energy no longer dominates the shared-grid disagreement envelope",
        "max_jump_height support or nodata sensitivity is resolved or explicitly bounded",
        "velocity exceedance layers remain measured but are deferrable rather than blocking closure",
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
        "spatial uncertainty remains support/nodata dominated in a closure-limiting layer",
        "convergence remains inconclusive under the measured multi-seed envelope",
        "a closure decision is recorded to stop further diagnostic expansion rather than to accept the pilot",
    ]


def deferred_requirements() -> list[str]:
    return [
        "same-scale readiness is ready",
        "convergence remains inconclusive but the evidence set is bounded and reusable",
        "spatial uncertainty is localized but one or more dominant layers remain unresolved",
        "reducer / runtime scaling shows the local single-job path is sufficient for the next step",
        "follow-up blockers are concrete and executable rather than roadmap-only",
        "the pilot remains non-operational and scale-up unauthorized",
    ]


def spatial_summary_state(overall_role: str | None) -> str:
    if overall_role in {"closure_limiting", "nodata_support_dominated"}:
        return "closure_limiting"
    if overall_role in {"deferrable", "spatially_localized"}:
        return "deferrable"
    if overall_role in {"unresolved", "diffuse_across_shared_support"}:
        return "unresolved"
    return "blocked"


def spatial_layer_summary(spatial_uncertainty: dict[str, Any], layer_key: str) -> dict[str, Any]:
    return dict((spatial_uncertainty.get("layer_summaries") or {}).get(layer_key) or {})


def layer_closure_role(spatial_uncertainty: dict[str, Any], layer_key: str) -> str:
    layer = spatial_layer_summary(spatial_uncertainty, layer_key)
    concentration = layer.get("uncertainty_concentration_class")
    if concentration == "dominated_by_nodata_support_differences":
        return "closure_limiting"
    if concentration == "spatially_localized_shared_support_magnitude":
        return "deferrable" if layer_key == "velocity_exceedance_5mps" else "compatible_with_future_threshold"
    if concentration in {"shared_support_magnitude_diffuse", "diffuse_across_shared_support"}:
        return "unresolved"
    return "unresolved"


def summarize_spatial_uncertainty(spatial_uncertainty: dict[str, Any]) -> dict[str, Any]:
    layer_roles = {}
    stability_zone_layer_summaries = {}
    for layer_key in ("max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"):
        layer = spatial_layer_summary(spatial_uncertainty, layer_key)
        mask = layer.get("mask_evidence") or {}
        decomposition = layer.get("disagreement_decomposition") or {}
        stability_zone = layer.get("stability_zone_summary") or {}
        layer_roles[layer_key] = {
            "uncertainty_concentration_class": layer.get("uncertainty_concentration_class"),
            "closure_role": layer_closure_role(spatial_uncertainty, layer_key),
            "interpretation_note": layer.get("interpretation_note"),
            "nodata_disagreement_count": layer.get("nodata_disagreement_count"),
            "support_only_disagreement_count": layer.get("support_only_disagreement_count"),
            "magnitude_only_disagreement_count": layer.get("magnitude_only_disagreement_count"),
            "shared_valid_cell_count": layer.get("shared_valid_cell_count"),
            "analysis_cell_count": layer.get("analysis_cell_count"),
            "nonzero_support_stability_fraction": layer.get("nonzero_support_stability_fraction"),
            "high_uncertainty_cell_fraction": layer.get("high_uncertainty_cell_fraction"),
            "high_uncertainty_support_nodata_fraction": layer.get("high_uncertainty_support_nodata_fraction"),
            "high_uncertainty_shared_support_magnitude_fraction": layer.get("high_uncertainty_shared_support_magnitude_fraction"),
            "disagreement_decomposition_class": decomposition.get("classification"),
            "disagreement_decomposition": decomposition,
            "stability_zone_class": stability_zone.get("layer_stability_zone_class"),
            "stability_zone_dominant_category": stability_zone.get("dominant_zone_category"),
            "stability_zone_dominant_high_uncertainty_category": stability_zone.get("dominant_high_uncertainty_zone_category"),
            "stability_zone_closure_role_impact": stability_zone.get("closure_role_impact"),
            "stability_zone_summary": stability_zone,
            "mask_status": mask.get("mask_status"),
            "mask_closure_role": mask.get("closure_role"),
            "high_uncertainty_cell_count": mask.get("high_uncertainty_cell_count"),
            "support_nodata_cell_count": mask.get("support_nodata_cell_count"),
            "shared_support_magnitude_cell_count": mask.get("shared_support_magnitude_cell_count"),
            "mask_bbox": mask.get("mask_bbox"),
            "mask_path": mask.get("mask_path"),
        }
        stability_zone_layer_summaries[layer_key] = stability_zone
    overall_role = spatial_uncertainty.get("spatial_interpretation")
    if overall_role == "nodata_support_dominated":
        overall_closure_role = "closure_limiting"
    elif overall_role == "spatially_localized":
        overall_closure_role = "deferrable"
    elif overall_role == "diffuse_across_shared_support":
        overall_closure_role = "unresolved"
    else:
        overall_closure_role = "blocked"
    return {
        "spatial_uncertainty_status": spatial_uncertainty.get("spatial_uncertainty_status"),
        "spatial_interpretation": overall_role,
        "overall_closure_role": overall_closure_role,
        "layer_roles": layer_roles,
        "stability_zone_summary": {
            "stability_zone_status": spatial_uncertainty.get("stability_zone_status"),
            "layer_summaries": stability_zone_layer_summaries,
            "overall_closure_role_change": stability_zone_overall_change(stability_zone_layer_summaries),
        },
        "dominant_layers": spatial_uncertainty.get("dominant_layers_by_mean_range", []),
        "dominant_layer_summaries": spatial_uncertainty.get("dominant_layer_summaries", []),
        "mask_status": spatial_uncertainty.get("mask_status"),
        "blocked_reason": spatial_uncertainty.get("blocked_reason", ""),
    }


def stability_zone_overall_change(stability_zone_layer_summaries: dict[str, Any]) -> str:
    if not stability_zone_layer_summaries:
        return "blocked"
    if all((layer or {}).get("closure_role_impact") == "no_change" for layer in stability_zone_layer_summaries.values()):
        return "no_change"
    return "mixed"


def build_criteria_matrix(
    *,
    readiness: dict[str, Any],
    uncertainty: dict[str, Any],
    spatial_uncertainty: dict[str, Any],
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
            accepted_requirement="no single layer remains structurally limiting and spatial uncertainty is not support/nodata dominated",
            no_go_requirement="dominant layers remain support/nodata dominated and block closure interpretation",
            deferred_requirement="dominant layers are localized but one or more remain unresolved",
            current_state=spatial_summary_state(spatial_uncertainty.get("spatial_interpretation")),
            current_evidence_summary={
                "spatial_uncertainty_status": spatial_uncertainty.get("spatial_uncertainty_status"),
                "spatial_interpretation": spatial_uncertainty.get("spatial_interpretation"),
                "overall_closure_role": spatial_uncertainty.get("overall_closure_role"),
                "dominant_layer_spread": uncertainty.get("dominant_layer_spread", {}),
                "dominant_layers": spatial_uncertainty.get("dominant_layers", []),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md", "scripts/summarize_spatial_same_scale_uncertainty.py"],
        ),
        criterion_entry(
            criterion="max_kinetic_energy_behavior",
            accepted_requirement="max_kinetic_energy no longer dominates the shared-grid disagreement envelope",
            no_go_requirement="max_kinetic_energy remains the dominant disagreement driver with material support/nodata disagreement",
            deferred_requirement="max_kinetic_energy remains localized but unresolved",
            current_state=layer_closure_role(spatial_uncertainty, "max_kinetic_energy"),
            current_evidence_summary={
                "max_kinetic_energy_uncertainty": uncertainty.get("max_kinetic_energy_uncertainty", {}),
                "spatial_layer": spatial_layer_summary(spatial_uncertainty, "max_kinetic_energy"),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md", "scripts/summarize_spatial_same_scale_uncertainty.py"],
        ),
        criterion_entry(
            criterion="max_jump_height_support_nodata_sensitivity",
            accepted_requirement="support and nodata sensitivity are no longer closure-limiting",
            no_go_requirement="support or nodata sensitivity still drives the measured envelope",
            deferred_requirement="support and nodata sensitivity are measured and bounded but not eliminated",
            current_state=layer_closure_role(spatial_uncertainty, "max_jump_height"),
            current_evidence_summary={
                "max_jump_height_uncertainty": uncertainty.get("max_jump_height_uncertainty", {}),
                "spatial_layer": spatial_layer_summary(spatial_uncertainty, "max_jump_height"),
            },
            evidence_refs=[
                "docs/tschamut_public_same_scale_uncertainty_envelope.md",
                "docs/tschamut_public_obstacle_context_scope.md",
                "scripts/summarize_spatial_same_scale_uncertainty.py",
            ],
        ),
        criterion_entry(
            criterion="velocity_exceedance_behavior",
            accepted_requirement="velocity exceedance spread is measured and no longer closure-limiting",
            no_go_requirement="velocity exceedance layers remain part of the measured spread",
            deferred_requirement="velocity exceedance layers remain localized and deferrable",
            current_state=layer_closure_role(spatial_uncertainty, "velocity_exceedance_5mps"),
            current_evidence_summary={
                "velocity_exceedance_uncertainty": uncertainty.get("velocity_exceedance_uncertainty", {}),
                "spatial_layer": spatial_layer_summary(spatial_uncertainty, "velocity_exceedance_5mps"),
            },
            evidence_refs=["docs/tschamut_public_same_scale_uncertainty_envelope.md", "scripts/summarize_spatial_same_scale_uncertainty.py"],
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
    spatial_uncertainty: dict[str, Any] | None = None,
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
    if spatial_uncertainty is not None and spatial_summary_state(spatial_uncertainty.get("spatial_interpretation")) == "closure_limiting":
        blockers.append("spatial_uncertainty_support_nodata_dominates_closure")
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
        "spatial_uncertainty_interpretation": {
            "spatial_uncertainty_status": "blocked_missing_inputs",
            "overall_closure_role": "blocked",
            "layer_roles": {},
            "stability_zone_summary": {
                "stability_zone_status": "blocked_missing_inputs",
                "overall_closure_role_change": "blocked",
                "layer_summaries": {},
            },
        },
        "current_evidence": {
            "closure": {
                "stability_zone_summary": {
                    "stability_zone_status": "blocked_missing_inputs",
                    "overall_closure_role_change": "blocked",
                }
            }
        },
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
    spatial = report.get("spatial_uncertainty_interpretation", {})
    lines.append("spatial uncertainty interpretation:")
    if spatial:
        lines.append(
            f"- overall: {spatial.get('spatial_interpretation')} -> {spatial.get('overall_closure_role')}"
        )
        for layer_key, layer in spatial.get("layer_roles", {}).items():
            lines.append(
                f"- {layer_key}: {layer.get('uncertainty_concentration_class')} -> {layer.get('closure_role')}"
            )
            decomposition = layer.get("disagreement_decomposition") or {}
            if decomposition:
                fractions = decomposition.get("high_uncertainty_fraction_explained") or {}
                lines.append(
                    f"  decomposition={decomposition.get('classification')} | "
                    f"support/nodata={fractions.get('support_nodata', 0.0):.6g} | "
                    f"shared-support magnitude={fractions.get('shared_support_magnitude', 0.0):.6g}"
                )
            stability_zone = layer.get("stability_zone_summary") or {}
            if stability_zone:
                zone_counts = stability_zone.get("zone_counts") or {}
                zone_fractions = stability_zone.get("zone_fractions") or {}
                lines.append(
                    f"  stability={stability_zone.get('layer_stability_zone_class')} | "
                    f"dominant={stability_zone.get('dominant_zone_category')} | "
                    f"high-uncertainty={stability_zone.get('dominant_high_uncertainty_zone_category')} | "
                    f"closure-role-change={stability_zone.get('closure_role_impact')}"
                )
                lines.append(
                    "  zone counts="
                    f"{zone_counts.get('support_nodata_sensitive', 0)}/"
                    f"{zone_counts.get('shared_support_magnitude', 0)}/"
                    f"{zone_counts.get('persistent_agreement', 0)}"
                    " (support/nodata-sensitive / shared-support magnitude / persistent agreement)"
                )
                lines.append(
                    "  zone fractions="
                    f"{zone_fractions.get('support_nodata_sensitive', 0.0):.6g}/"
                    f"{zone_fractions.get('shared_support_magnitude', 0.0):.6g}/"
                    f"{zone_fractions.get('persistent_agreement', 0.0):.6g}"
                )
    lines.append(
        "scale_up_authorized=false operational_claims_allowed=false"
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
