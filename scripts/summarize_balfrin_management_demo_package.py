#!/usr/bin/env python3
"""Summarize the Balfrin management demonstration package.

This helper composes the measured Balfrin evidence bundle with a replay smoke
check into one compact review package. It keeps runtime, replay,
restartability, GIS scope, uncertainty, and claim-boundary sections separate
so a non-developer reviewer can see what the demo proves and what it does not
prove without collapsing fixture-backed replay evidence into measured evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gis_cog_package_readiness as gis_cog
from scripts import summarize_balfrin_demonstration_replay_smoke as replay_smoke
from scripts import summarize_balfrin_evidence_bundle as bundle
from scripts import generate_balfrin_multi_release_zone_demo_handoff as multi_zone_handoff
from scripts import summarize_balfrin_next_live_run_decision_gate as next_live_decision
from scripts import summarize_balfrin_output_tier_audit as output_tier
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate
from scripts import summarize_balfrin_physical_credibility_evidence_gaps as physical_gaps
from scripts import summarize_balfrin_post_run_interpretation_gate as post_run_gate
from scripts import summarize_balfrin_target_area_evidence_bundle as target_bundle
from scripts import summarize_balfrin_single_job_execution as single_job


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_management_demo_package_v1"
READINESS_MATRIX_SCHEMA_VERSION = "balfrin_full_scale_readiness_matrix_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_management_demo_package_v1"
DEFAULT_REPLAY_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_TARGET_AREA_BUNDLE_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1"
DEFAULT_PHYSICAL_CREDIBILITY_GAP_DIR = (
    ROOT / "validation/private/tschamut_public_pilot/balfrin_physical_credibility_evidence_gaps_v1"
)
DEFAULT_READINESS_MATRIX_CLEAN_CHECKOUT_RUN_ROOT = (
    ROOT / "validation/private/tschamut_public_pilot/balfrin_full_scale_readiness_matrix_v1/clean_checkout_missing_run_root"
)
TB407_SMALL_MULTI_ZONE_PROBE = {
    "task_id": "TB-407",
    "job_id": "4347579",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:29",
    "alloc_cpus": 16,
    "validation_output_file_count": 130,
    "validation_output_bytes": 34565330,
    "hazard_output_file_count": 53,
    "hazard_output_bytes": 55831799,
    "conditional_curve_rows": 729600,
    "preservation_status": "ready_for_demonstration_evidence",
    "metrics_contract_status": "complete",
    "threshold_profile_id": "smallest_live_two_zone_probe",
    "source_report": "archive/task_reports/balfrin_multi_zone_hazard_run_tb407.md",
}


class BalfrinManagementDemoPackageError(ValueError):
    """User-facing management package error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_REPLAY_RUN_ROOT)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate package snapshots",
    )
    parser.add_argument(
        "--balfrin-access-preflight-json",
        type=Path,
        default=None,
        help="optional current Balfrin access preflight JSON to thread into the next-decision section",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            run_root=args.run_root,
            artifact_dir=args.artifact_dir,
            evidence_override=load_evidence_override(args.evidence_json),
            balfrin_access_preflight=next_live_decision.load_access_preflight(args.balfrin_access_preflight_json),
        )
    except BalfrinManagementDemoPackageError as exc:
        print(f"balfrin management demo package error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["package_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinManagementDemoPackageError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinManagementDemoPackageError("evidence override must be a JSON object")
    return data


def build_report(
    *,
    run_root: Path,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    evidence_override: dict[str, Any] | None = None,
    balfrin_access_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if evidence_override is None:
        return build_current_report(
            run_root=run_root,
            artifact_dir=artifact_dir,
            balfrin_access_preflight=balfrin_access_preflight,
        )
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(
            missing_inputs,
            reason="required package inputs are missing",
            run_root=run_root,
            artifact_dir=artifact_dir,
        )
    if isinstance(evidence_override.get("package_report"), dict):
        return dict(evidence_override["package_report"])

    required_keys = (
        "runtime_section",
        "replay_section",
        "target_area_aoi_automation_section",
        "target_area_release_scenario_section",
        "target_area_probe_metrics_section",
        "target_area_canonical_bundle_section",
        "restartability_section",
        "gis_scope_section",
        "uncertainty_section",
        "claim_boundary_section",
        "scaling_section",
        "diagnostic_performance_section",
        "physical_credibility_section",
        "swiss_wide_extension_section",
        "swiss_scale_feasibility_projection_section",
        "failed_closed_section",
        "next_decision_section",
    )
    if any(key in evidence_override for key in required_keys):
        missing_inputs = [key for key in required_keys if key not in evidence_override]
        if missing_inputs:
            return blocked_report(
                missing_inputs,
                reason="required package sections are missing",
                run_root=run_root,
                artifact_dir=artifact_dir,
            )
        return assemble_package_report(
            runtime_section=dict(evidence_override["runtime_section"]),
            replay_section=dict(evidence_override["replay_section"]),
            target_area_aoi_automation_section=dict(evidence_override["target_area_aoi_automation_section"]),
            target_area_release_scenario_section=dict(evidence_override["target_area_release_scenario_section"]),
            target_area_probe_metrics_section=dict(evidence_override["target_area_probe_metrics_section"]),
            target_area_canonical_bundle_section=dict(evidence_override["target_area_canonical_bundle_section"]),
            restartability_section=dict(evidence_override["restartability_section"]),
            gis_scope_section=dict(evidence_override["gis_scope_section"]),
            uncertainty_section=dict(evidence_override["uncertainty_section"]),
            claim_boundary_section=dict(evidence_override["claim_boundary_section"]),
            scaling_section=dict(evidence_override["scaling_section"]),
            diagnostic_performance_section=dict(evidence_override["diagnostic_performance_section"]),
            physical_credibility_section=dict(evidence_override["physical_credibility_section"]),
            swiss_wide_extension_section=dict(evidence_override["swiss_wide_extension_section"]),
            swiss_scale_feasibility_projection_section=dict(
                evidence_override["swiss_scale_feasibility_projection_section"]
            ),
            failed_closed_section=dict(evidence_override["failed_closed_section"]),
            next_decision_section=dict(evidence_override["next_decision_section"]),
            source_artifacts=as_mapping(evidence_override.get("source_artifacts")),
            regeneration_commands=listify(evidence_override.get("regeneration_commands")),
            package_artifact_dir=Path(str(evidence_override.get("package_artifact_dir") or artifact_dir)),
            run_root=Path(str(evidence_override.get("run_root") or run_root)),
        )

    return build_current_report(run_root=run_root, artifact_dir=artifact_dir)


def build_current_report(
    *,
    run_root: Path,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    balfrin_access_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not run_root.exists():
        return blocked_report(
            [str(run_root)],
            reason=f"run root is missing: {run_root}",
            run_root=run_root,
            artifact_dir=artifact_dir,
        )

    bundle_report = bundle.build_current_report()
    smoke_report = replay_smoke.build_report(run_root=run_root, artifact_dir=artifact_dir / "replay_smoke_v1")
    target_area_bundle_report = target_bundle.build_current_report()
    physical_credibility_report = physical_gaps.build_report()
    post_run_report = dict(bundle_report.get("post_run_interpretation_gate_report") or {})
    if not post_run_report:
        post_run_report = post_run_gate.build_report(
            {
                "single_job_execution_summary": bundle_report.get("single_job_execution_summary", {}),
                "probe_metrics": bundle_report.get("probe_metrics", {}),
                "post_run_interpretation_gate_report": bundle_report.get(
                    "post_run_interpretation_gate_report", {}
                ),
                "gis_cog_readiness_report": bundle_report.get("gis_cog_readiness_report", {}),
            }
        )

    package_report = assemble_package_report(
        runtime_section=build_runtime_section(bundle_report),
        replay_section=build_replay_section(smoke_report),
        target_area_aoi_automation_section=build_target_area_aoi_automation_section(target_area_bundle_report),
        target_area_release_scenario_section=build_target_area_release_scenario_section(target_area_bundle_report),
        target_area_probe_metrics_section=build_target_area_probe_metrics_section(target_area_bundle_report),
        target_area_canonical_bundle_section=build_target_area_canonical_bundle_section(target_area_bundle_report),
        restartability_section=build_restartability_section(bundle_report),
        gis_scope_section=build_gis_scope_section(bundle_report),
        uncertainty_section=build_uncertainty_section(bundle_report, smoke_report),
        claim_boundary_section=build_claim_boundary_section(post_run_report),
        scaling_section=build_scaling_section(bundle_report, post_run_report),
        diagnostic_performance_section=build_diagnostic_performance_section(),
        physical_credibility_section=build_physical_credibility_section(physical_credibility_report),
        swiss_wide_extension_section=build_swiss_wide_extension_section(
            bundle_report=bundle_report,
            physical_credibility_report=physical_credibility_report,
        ),
        swiss_scale_feasibility_projection_section=build_swiss_scale_feasibility_projection_section(),
        failed_closed_section=build_failed_closed_section(),
        next_decision_section=build_next_decision_section(bundle_report, post_run_report),
        source_artifacts=build_source_artifacts(
            bundle_report=bundle_report,
            smoke_report=smoke_report,
            target_area_bundle_report=target_area_bundle_report,
            physical_credibility_report=physical_credibility_report,
            package_artifact_dir=artifact_dir,
            run_root=run_root,
        ),
        regeneration_commands=build_regeneration_commands(run_root=run_root, package_artifact_dir=artifact_dir),
        package_artifact_dir=artifact_dir,
        run_root=run_root,
    )
    multi_zone_handoff_artifact_dir = Path("/tmp/rust_rockfall") / "balfrin_full_scale_readiness_matrix_v1" / "multi_zone_handoff"
    try:
        multi_zone_handoff_report = multi_zone_handoff.build_report(artifact_dir=multi_zone_handoff_artifact_dir)
    except multi_zone_handoff.BalfrinMultiReleaseZoneDemoHandoffError as exc:
        multi_zone_handoff_report = {
            "report_status": "blocked_missing_reducer_constraints",
            "constraint_pressure": {"status": "blocked_missing_reducer_constraints", "blocked_reason": str(exc)},
            "multi_zone_pressure": {},
            "follow_up_recommendation": {"action": "refresh_diagnostic_reducer_pressure_evidence"},
        }
    package_report["readiness_matrix"] = build_readiness_matrix(
        run_root=run_root,
        artifact_dir=artifact_dir,
        package_report=package_report,
        bundle_report=bundle_report,
        replay_report=smoke_report,
        output_tier_report=output_tier.build_report(dict(bundle_report.get("probe_metrics") or {})),
        preservation_report=preservation_gate.build_report(run_root=run_root),
        multi_zone_handoff_report=multi_zone_handoff_report,
        next_live_decision_report=next_live_decision.build_report(
            balfrin_access_preflight=balfrin_access_preflight
        ),
    )
    return package_report


def assemble_package_report(
    *,
    runtime_section: dict[str, Any],
    replay_section: dict[str, Any],
    target_area_aoi_automation_section: dict[str, Any],
    target_area_release_scenario_section: dict[str, Any],
    target_area_probe_metrics_section: dict[str, Any],
    target_area_canonical_bundle_section: dict[str, Any],
    restartability_section: dict[str, Any],
    gis_scope_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    claim_boundary_section: dict[str, Any],
    scaling_section: dict[str, Any],
    diagnostic_performance_section: dict[str, Any],
    physical_credibility_section: dict[str, Any],
    swiss_wide_extension_section: dict[str, Any],
    swiss_scale_feasibility_projection_section: dict[str, Any],
    failed_closed_section: dict[str, Any],
    next_decision_section: dict[str, Any],
    source_artifacts: dict[str, Any],
    regeneration_commands: list[str],
    package_artifact_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    sections = [
        ("runtime_section", runtime_section, build_section_source_paths(runtime_section)),
        ("replay_section", replay_section, build_section_source_paths(replay_section)),
        (
            "target_area_aoi_automation_section",
            target_area_aoi_automation_section,
            build_section_source_paths(target_area_aoi_automation_section),
        ),
        (
            "target_area_release_scenario_section",
            target_area_release_scenario_section,
            build_section_source_paths(target_area_release_scenario_section),
        ),
        (
            "target_area_probe_metrics_section",
            target_area_probe_metrics_section,
            build_section_source_paths(target_area_probe_metrics_section),
        ),
        (
            "target_area_canonical_bundle_section",
            target_area_canonical_bundle_section,
            build_section_source_paths(target_area_canonical_bundle_section),
        ),
        ("restartability_section", restartability_section, build_section_source_paths(restartability_section)),
        ("gis_scope_section", gis_scope_section, build_section_source_paths(gis_scope_section)),
        ("uncertainty_section", uncertainty_section, build_section_source_paths(uncertainty_section)),
        ("claim_boundary_section", claim_boundary_section, build_section_source_paths(claim_boundary_section)),
        ("scaling_section", scaling_section, build_section_source_paths(scaling_section)),
        (
            "diagnostic_performance_section",
            diagnostic_performance_section,
            build_section_source_paths(diagnostic_performance_section),
        ),
        (
            "physical_credibility_section",
            physical_credibility_section,
            build_section_source_paths(physical_credibility_section),
        ),
        (
            "swiss_wide_extension_section",
            swiss_wide_extension_section,
            build_section_source_paths(swiss_wide_extension_section),
        ),
        (
            "swiss_scale_feasibility_projection_section",
            swiss_scale_feasibility_projection_section,
            build_section_source_paths(swiss_scale_feasibility_projection_section),
        ),
        (
            "failed_closed_section",
            failed_closed_section,
            build_section_source_paths(failed_closed_section),
        ),
        ("next_decision_section", next_decision_section, build_section_source_paths(next_decision_section)),
    ]
    section_provenance_profile = []
    for section_name, section_payload, source_paths in sections:
        section_provenance_profile.append(
            {
                "section": section_name,
                "status": section_status(section_payload),
                "evidence_type": classify_evidence_type(section_payload, source_paths),
                "source_paths": source_paths,
            }
        )

    package_status = derive_package_status(section_provenance_profile)
    package_summary = {
        "status": package_status,
        "summary": summarize_package(
            package_status,
            runtime_section,
            replay_section,
            target_area_aoi_automation_section,
            target_area_release_scenario_section,
            target_area_probe_metrics_section,
            target_area_canonical_bundle_section,
            uncertainty_section,
            claim_boundary_section,
            scaling_section,
            diagnostic_performance_section,
            physical_credibility_section,
            swiss_wide_extension_section,
            swiss_scale_feasibility_projection_section,
            failed_closed_section,
            next_decision_section,
        ),
        "section_counts": section_provenance_counts(section_provenance_profile),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": package_status,
        "package_provenance_status": package_status,
        "package_artifact_dir": str(package_artifact_dir),
        "run_root": str(run_root),
        "package_summary": package_summary,
        "runtime_section": runtime_section,
        "replay_section": replay_section,
        "target_area_aoi_automation_section": target_area_aoi_automation_section,
        "target_area_release_scenario_section": target_area_release_scenario_section,
        "target_area_probe_metrics_section": target_area_probe_metrics_section,
        "target_area_canonical_bundle_section": target_area_canonical_bundle_section,
        "restartability_section": restartability_section,
        "gis_scope_section": gis_scope_section,
        "uncertainty_section": uncertainty_section,
        "claim_boundary_section": claim_boundary_section,
        "scaling_section": scaling_section,
        "diagnostic_performance_section": diagnostic_performance_section,
        "physical_credibility_section": physical_credibility_section,
        "swiss_wide_extension_section": swiss_wide_extension_section,
        "swiss_scale_feasibility_projection_section": swiss_scale_feasibility_projection_section,
        "failed_closed_section": failed_closed_section,
        "next_decision_section": next_decision_section,
        "claim_boundaries": claim_boundary_section.get("claim_boundaries", post_run_gate.claim_boundaries()),
        "section_provenance_profile": section_provenance_profile,
        "source_artifacts": source_artifacts,
        "regeneration_commands": regeneration_commands,
        "evidence_sources": evidence_sources(source_artifacts),
    }


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    run_root: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    claim_boundaries = post_run_gate.claim_boundaries()
    section_names = (
        "runtime_section",
        "replay_section",
        "target_area_aoi_automation_section",
        "target_area_release_scenario_section",
        "target_area_probe_metrics_section",
        "target_area_canonical_bundle_section",
        "restartability_section",
        "gis_scope_section",
        "uncertainty_section",
        "claim_boundary_section",
        "scaling_section",
        "diagnostic_performance_section",
        "physical_credibility_section",
        "swiss_wide_extension_section",
        "swiss_scale_feasibility_projection_section",
        "failed_closed_section",
        "next_decision_section",
    )
    section_provenance_profile = [
        {
            "section": section_name,
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        }
        for section_name in section_names
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": "blocked_missing_inputs",
        "package_provenance_status": "blocked_missing_inputs",
        "package_artifact_dir": str(artifact_dir),
        "run_root": str(run_root),
        "package_summary": {
            "status": "blocked_missing_inputs",
            "summary": "Balfrin management package is blocked because one or more required sections are missing.",
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "runtime_section": {"status": "blocked_missing_inputs"},
        "replay_section": {"status": "blocked_missing_inputs", "missing_inputs": list(missing_inputs)},
        "target_area_aoi_automation_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "target_area_release_scenario_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "target_area_probe_metrics_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "target_area_canonical_bundle_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "restartability_section": {"status": "blocked_missing_inputs"},
        "gis_scope_section": {"status": "blocked_missing_inputs"},
        "uncertainty_section": {"status": "blocked_missing_inputs"},
        "claim_boundary_section": {
            "status": "blocked_missing_inputs",
            "claim_boundaries": claim_boundaries,
        },
        "scaling_section": {"status": "blocked_missing_inputs"},
        "diagnostic_performance_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "physical_credibility_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "swiss_wide_extension_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "swiss_scale_feasibility_projection_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "failed_closed_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "next_decision_section": {"status": "blocked_missing_inputs"},
        "claim_boundaries": claim_boundaries,
        "section_provenance_profile": section_provenance_profile,
        "source_artifacts": {
            "package_artifact_dir": str(artifact_dir),
            "run_root": str(run_root),
            "target_area_bundle_artifact_dir": str(DEFAULT_TARGET_AREA_BUNDLE_DIR),
            "physical_credibility_artifact_dir": str(DEFAULT_PHYSICAL_CREDIBILITY_GAP_DIR),
        },
        "regeneration_commands": build_regeneration_commands(run_root=run_root, package_artifact_dir=artifact_dir),
        "evidence_sources": evidence_sources({"run_root": str(run_root)}),
        "missing_inputs": list(missing_inputs),
        "blocked_reason": reason,
    }


def build_readiness_matrix(
    *,
    run_root: Path,
    artifact_dir: Path,
    package_report: dict[str, Any],
    bundle_report: dict[str, Any],
    replay_report: dict[str, Any],
    output_tier_report: dict[str, Any],
    preservation_report: dict[str, Any],
    multi_zone_handoff_report: dict[str, Any],
    next_live_decision_report: dict[str, Any],
) -> dict[str, Any]:
    clean_checkout_report = preservation_gate.build_report(run_root=DEFAULT_READINESS_MATRIX_CLEAN_CHECKOUT_RUN_ROOT)
    claim_boundaries = dict(package_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    multi_zone_bundle_evidence = dict(bundle_report.get("multi_zone_balfrin_evidence") or {})
    multi_zone_pressure = dict(multi_zone_handoff_report.get("multi_zone_pressure") or {})
    follow_up_recommendation = dict(multi_zone_handoff_report.get("follow_up_recommendation") or {})
    next_action = dict(next_live_decision_report.get("recommended_next_action") or {})
    next_criteria = dict(next_live_decision_report.get("criteria") or {})
    scenario_cap = dict(next_criteria.get("scenario_batching_cap") or {})
    candidate_result = dict(next_criteria.get("candidate_stability_result") or {})

    rows = [
        matrix_row(
            gate="measured_multi_zone_execution",
            status="measured",
            gate_status=TB407_SMALL_MULTI_ZONE_PROBE["metrics_contract_status"],
            evidence_status="measured",
            summary=(
                "TB-407 completed the smallest bounded multi-zone Balfrin postproc submission and preserved measured run-root evidence; "
                "this remains bounded diagnostic evidence and does not authorize scale-up or operational hazard claims."
            ),
            helper_sources=[
                "archive/task_reports/balfrin_multi_zone_hazard_run_tb407.md",
                "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
            ],
            current_evidence={
                "task_id": TB407_SMALL_MULTI_ZONE_PROBE["task_id"],
                "job_id": TB407_SMALL_MULTI_ZONE_PROBE["job_id"],
                "run_root": TB407_SMALL_MULTI_ZONE_PROBE["run_root"],
                "slurm_state": TB407_SMALL_MULTI_ZONE_PROBE["slurm_state"],
                "exit_code": TB407_SMALL_MULTI_ZONE_PROBE["exit_code"],
                "elapsed": TB407_SMALL_MULTI_ZONE_PROBE["elapsed"],
                "alloc_cpus": TB407_SMALL_MULTI_ZONE_PROBE["alloc_cpus"],
                "validation_output_file_count": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_file_count"],
                "validation_output_bytes": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_bytes"],
                "hazard_output_file_count": TB407_SMALL_MULTI_ZONE_PROBE["hazard_output_file_count"],
                "hazard_output_bytes": TB407_SMALL_MULTI_ZONE_PROBE["hazard_output_bytes"],
                "conditional_curve_rows": TB407_SMALL_MULTI_ZONE_PROBE["conditional_curve_rows"],
                "metrics_contract_status": TB407_SMALL_MULTI_ZONE_PROBE["metrics_contract_status"],
                "preservation_status": TB407_SMALL_MULTI_ZONE_PROBE["preservation_status"],
                "threshold_profile_id": TB407_SMALL_MULTI_ZONE_PROBE["threshold_profile_id"],
                "source_report": TB407_SMALL_MULTI_ZONE_PROBE["source_report"],
            },
        ),
        matrix_row(
            gate="regional_split_projection_comparison",
            status="analysis_only",
            gate_status="measured_regional_split_available",
            evidence_status="measured",
            summary=(
                "TB-447/TB-448 supply measured regional split evidence; the next step is comparison work against the "
                "scenario-cardinality and output-tier projection surfaces, not another regional split retry."
            ),
            helper_sources=[
                "scripts/summarize_balfrin_scale_readiness_matrix.py",
                "archive/task_reports/balfrin_regional_split_run_root_metrics_tb566.md",
                "archive/task_reports/balfrin_regional_split_probe_gate_tb432.md",
            ],
            current_evidence={
                "classification": "measured_regional_split_probe",
                "evidence_label": "measured_on_balfrin",
                "job_id": "4367244",
                "validation_output_file_count": 130,
                "hazard_output_file_count": 57,
                "conditional_curve_rows": 729600,
                "preservation_status": "ready_for_demonstration_evidence",
                "next_recommended_action": "compare_measured_regional_split_against_scenario_and_output_projections",
                "supersedes_failed_closed_task": "TB-432",
                "source_report": "archive/task_reports/balfrin_regional_split_run_root_metrics_tb566.md",
            },
        ),
        matrix_row(
            gate="diagnostic_performance_repeatability",
            status="measured",
            gate_status="measured_repeatability_pair",
            evidence_status="measured",
            summary=(
                "TB-579 measured a 24-zone diagnostic reducer-pressure run and TB-581 repeated the same diagnostic shape twice; "
                "this is current diagnostic performance evidence, not hazard-throughput or operational evidence."
            ),
            helper_sources=[
                "scripts/run_balfrin_diagnostic.py",
                "scripts/summarize_balfrin_scale_readiness_matrix.py",
                "archive/task_reports/balfrin_diagnostic_series_tb613.md",
            ],
            current_evidence=build_diagnostic_performance_section(),
        ),
        matrix_row(
            gate="preservation_gate",
            status="fixture_backed",
            gate_status=str(preservation_report.get("gate_status") or "blocked_missing_inputs"),
            evidence_status=str(preservation_report.get("run_root_provenance") or "fixture_backed"),
            summary=(
                "The preservation gate is ready on the fixture-backed preserved run root and stays blocked when the run root is absent."
            ),
            helper_sources=["scripts/summarize_balfrin_probe_preservation_gate.py"],
            current_evidence={
                "run_root_status": preservation_report.get("run_root_status"),
                "run_root_provenance": preservation_report.get("run_root_provenance"),
                "required_run_root_entries_status": preservation_report.get("required_run_root_entries_status"),
            },
        ),
        matrix_row(
            gate="reducer_constraints",
            status="measured",
            gate_status=str((multi_zone_handoff_report.get("constraint_pressure") or {}).get("status") or "unknown"),
            evidence_status="measured",
            summary=(
                "Measured scratch-root reducer pressure caps the next multi-zone probe at 8 simultaneous release zones, "
                "4 reducer chunks, and 2 reducer workers."
            ),
            helper_sources=[
                "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
                "scripts/summarize_multi_zone_reducer_pressure.py",
            ],
            current_evidence=dict(multi_zone_handoff_report.get("multi_zone_pressure") or {}),
        ),
        matrix_row(
            gate="scenario_batching_cap",
            status=str(scenario_cap.get("status") or "blocked_missing_inputs"),
            gate_status=str(scenario_cap.get("prepared_pilot_smoke_status") or "blocked_missing_inputs"),
            evidence_status="scratch_local",
            summary=(
                "Scenario batching is ready for local planning at the current cap of "
                f"{scenario_cap.get('scenario_batching_cap')} candidate expansions; this is a scratch/local planning cap, not a live execution authorization."
            ),
            helper_sources=[
                "scripts/summarize_management_aoi_scenario_pressure.py",
                "scripts/generate_candidate_source_zone_scenarios.py",
            ],
            current_evidence={
                "scenario_batching_cap": scenario_cap.get("scenario_batching_cap"),
                "candidate_expansion_counts": scenario_cap.get("candidate_expansion_counts", []),
                "scenario_row_count": scenario_cap.get("scenario_row_count"),
                "prepared_pilot_smoke_status": scenario_cap.get("prepared_pilot_smoke_status"),
            },
        ),
        matrix_row(
            gate="candidate_stability",
            status=str(candidate_result.get("status") or "blocked_missing_inputs"),
            gate_status=str(candidate_result.get("selected_candidate_status") or "blocked_missing_inputs"),
            evidence_status="scratch_local",
            summary=(
                "Candidate-stability evidence selects "
                f"{candidate_result.get('selected_candidate_id')} as {candidate_result.get('selected_candidate_class')} "
                "for bounded engineering follow-up; this does not promote the candidate to validation or physical evidence."
            ),
            helper_sources=["scripts/summarize_balfrin_target_area_candidate_stability.py"],
            current_evidence={
                "selected_candidate_id": candidate_result.get("selected_candidate_id"),
                "selected_candidate_class": candidate_result.get("selected_candidate_class"),
                "stability_score": candidate_result.get("stability_score"),
                "minimum_retention_fraction": candidate_result.get("minimum_retention_fraction"),
                "variant_count": candidate_result.get("variant_count"),
                "stable_candidate_cell_count": candidate_result.get("stable_candidate_cell_count"),
            },
        ),
        matrix_row(
            gate="output_budget",
            status="fixture_backed",
            gate_status=str(output_tier_report.get("rebuildability_status") or "unknown"),
            evidence_status=str(output_tier_report.get("evidence_provenance_status") or "fixture_backed"),
            summary=(
                "The output budget remains bounded by the replayable fixture-backed bundle and the measured reduced-output contract; "
                "it is not yet a full-scale execution budget."
            ),
            helper_sources=[
                "scripts/summarize_balfrin_output_tier_audit.py",
                "scripts/summarize_balfrin_management_demo_package.py",
            ],
            current_evidence={
                "rebuildability_status": output_tier_report.get("rebuildability_status"),
                "metrics_contract_status": output_tier_report.get("metrics_contract_status"),
                "measured_family_counts": output_tier_report.get("measured_family_counts", {}),
            },
        ),
        matrix_row(
            gate="restart_replay",
            status="fixture_backed",
            gate_status=str(replay_report.get("smoke_status") or "blocked_missing_inputs"),
            evidence_status=str(replay_report.get("run_root_provenance") or "fixture_backed"),
            summary=(
                "Restart and replay are deterministic on the preserved fixture-backed run root, but they remain bounded by the current single-job evidence."
            ),
            helper_sources=[
                "scripts/summarize_balfrin_demonstration_replay_smoke.py",
                "scripts/summarize_balfrin_evidence_bundle.py",
            ],
            current_evidence={
                "smoke_status": replay_report.get("smoke_status"),
                "run_root_status": replay_report.get("run_root_status"),
                "bundle_status": replay_report.get("bundle_status"),
                "post_run_interpretation_status": replay_report.get("post_run_interpretation_status"),
            },
        ),
        matrix_row(
            gate="gis_package_scope",
            status="measured",
            gate_status=str((package_report.get("gis_scope_section") or {}).get("status") or "blocked_missing_inputs"),
            evidence_status=str((package_report.get("gis_scope_section") or {}).get("evidence_type") or "measured"),
            summary=(
                "GIS package scope is measured and explicit, but it remains a conditional diagnostic scope rather than an operational hazard product."
            ),
            helper_sources=[
                "scripts/audit_gis_cog_package_readiness.py",
                "scripts/summarize_balfrin_management_demo_package.py",
            ],
            current_evidence=dict(package_report.get("gis_scope_section") or {}),
            claim_boundaries=dict(claim_boundaries),
        ),
        matrix_row(
            gate="command_plan_reproducibility",
            status="dry_run",
            gate_status=str(follow_up_recommendation.get("status") or "deferred_pending_authorization"),
            evidence_status="dry_run",
            summary=(
                "The generated command plan is reproducible and reviewable, but it remains a dry-run handoff and not a live execution authorization."
            ),
            helper_sources=[
                "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
                "scripts/summarize_balfrin_next_live_run_decision_gate.py",
            ],
            current_evidence={
                "authorization_review_command": follow_up_recommendation.get("authorization_review_command"),
                "authorization_submit_command": follow_up_recommendation.get("authorization_submit_command"),
                "command_plan_path": follow_up_recommendation.get("minimum_measured_multi_zone_run", {}).get("command_plan_path"),
            },
        ),
        matrix_row(
            gate="clean_checkout_behavior",
            status="blocked",
            gate_status=str(clean_checkout_report.get("gate_status") or "blocked_missing_run_root"),
            evidence_status="blocked",
            summary=(
                "A clean checkout or missing mounted run root fails closed instead of fabricating full-scale readiness evidence."
            ),
            helper_sources=[
                "scripts/summarize_balfrin_probe_preservation_gate.py",
                "scripts/summarize_balfrin_management_demo_package.py",
            ],
            current_evidence={
                "missing_run_root_reason": clean_checkout_report.get("missing_run_root_reason"),
                "missing_run_root_entries": clean_checkout_report.get("missing_run_root_entries", []),
            },
        ),
        matrix_row(
            gate="scientific_claim_boundaries",
            status="measured",
            gate_status=str((package_report.get("claim_boundary_section") or {}).get("status") or "guarded"),
            evidence_status="measured",
            summary=(
                "Full-scale readiness stays separate from operational, annual-frequency, physical-probability, and risk claims."
            ),
            helper_sources=[
                "scripts/summarize_balfrin_post_run_interpretation_gate.py",
                "docs/balfrin_single_job_execution_sufficiency.md",
            ],
            current_evidence=dict(claim_boundaries),
            claim_boundaries=dict(claim_boundaries),
        ),
        matrix_row(
            gate="live_execution_authorization",
            status="unauthorized",
            gate_status=str(follow_up_recommendation.get("authorization_classification") or "blocked_pending_authorization"),
            evidence_status="unauthorized",
            summary=(
                "Live multi-zone Balfrin execution remains unauthorized until a new human authorization records the reviewed handoff package."
            ),
            helper_sources=[
                "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
                "scripts/summarize_balfrin_next_live_run_decision_gate.py",
            ],
            current_evidence={
                "live_execution_requires_new_human_authorization": follow_up_recommendation.get(
                    "live_execution_requires_new_human_authorization"
                ),
                "blocked_reason": follow_up_recommendation.get("blocked_reason"),
            },
        ),
    ]

    matrix_status = "blocked"
    if any(row["status"] == "blocked" for row in rows):
        matrix_status = "blocked"
    elif any(row["status"] == "unauthorized" for row in rows):
        matrix_status = "unauthorized"
    elif any(row["status"] == "unavailable" for row in rows):
        matrix_status = "unavailable"
    elif any(row["status"] == "dry_run" for row in rows):
        matrix_status = "dry_run"
    elif any(row["status"] == "fixture_backed" for row in rows):
        matrix_status = "fixture_backed"
    else:
        matrix_status = "measured"

    return {
        "schema_version": READINESS_MATRIX_SCHEMA_VERSION,
        "status": matrix_status,
        "summary": (
            "Full-scale Balfrin demonstration readiness remains blocked by the absence of larger measured multi-zone execution and by the still-unauthorized live-run boundary; the next decision surface ranks reducer-pressure optimization first, with scenario batching and candidate-stability evidence as bounded scratch/local support."
        ),
        "rows": rows,
        "recommended_next_milestone": build_next_milestone_recommendation(next_live_decision_report),
        "claim_boundaries": dict(claim_boundaries),
        "source_helpers": [
            "scripts/summarize_balfrin_management_demo_package.py",
            "scripts/summarize_balfrin_probe_preservation_gate.py",
            "scripts/summarize_balfrin_output_tier_audit.py",
            "scripts/summarize_balfrin_demonstration_replay_smoke.py",
            "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
            "scripts/summarize_balfrin_next_live_run_decision_gate.py",
            "scripts/summarize_balfrin_post_run_interpretation_gate.py",
            "docs/balfrin_single_job_execution_sufficiency.md",
        ],
        "clean_checkout_probe": {
            "run_root": str(DEFAULT_READINESS_MATRIX_CLEAN_CHECKOUT_RUN_ROOT),
            "status": clean_checkout_report.get("gate_status"),
        },
        "current_evidence": {
            "preservation_gate_status": preservation_report.get("gate_status"),
            "output_tier_status": output_tier_report.get("rebuildability_status"),
            "replay_status": replay_report.get("smoke_status"),
            "multi_zone_package_status": multi_zone_handoff_report.get("package_status"),
            "next_action": next_action.get("action_id"),
            "scenario_batching_cap": scenario_cap.get("scenario_batching_cap"),
            "selected_candidate_id": candidate_result.get("selected_candidate_id"),
            "balfrin_access_status": (next_criteria.get("balfrin_access") or {}).get("status"),
            "balfrin_remote_head": (next_criteria.get("balfrin_access") or {}).get("remote_head"),
        },
    }


def matrix_row(
    *,
    gate: str,
    status: str,
    gate_status: str,
    evidence_status: str,
    summary: str,
    helper_sources: list[str],
    current_evidence: dict[str, Any],
    claim_boundaries: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "gate": gate,
        "status": status,
        "gate_status": gate_status,
        "evidence_status": evidence_status,
        "summary": summary,
        "helper_sources": helper_sources,
        "current_evidence": current_evidence,
    }
    if claim_boundaries is not None:
        row["claim_boundaries"] = claim_boundaries
    return row


def build_next_milestone_recommendation(next_live_decision_report: dict[str, Any]) -> dict[str, Any]:
    next_action = dict(next_live_decision_report.get("recommended_next_action") or {})
    action_id = str(next_action.get("action_id") or "")
    recommendation = next_live_decision.describe_next_action(action_id)
    return {
        "status": recommendation.replace(" ", "_"),
        "recommendation": recommendation,
        "reason": str(next_action.get("summary") or next_live_decision_report.get("decision_summary") or ""),
        "source_helper": "scripts/summarize_balfrin_next_live_run_decision_gate.py",
        "source_action_id": action_id,
        "follow_up_task": str(next_action.get("follow_up_task") or ""),
    }


def build_runtime_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    probe_metrics = dict(bundle_report.get("probe_metrics") or {})
    metrics_contract = dict(single_job_summary.get("metrics_contract") or {})
    mandatory_metrics = dict(metrics_contract.get("mandatory_metrics") or {})
    section = {
        "status": str(bundle_report.get("bundle_status") or metrics_contract.get("status") or "blocked_missing_inputs"),
        "summary": (
            "Measured runtime, memory, and output footprint show the Balfrin demo is replayable without implying an operational hazard-map claim."
        ),
        "decision": single_job_summary.get("decision"),
        "single_job_sufficient_for_next_step": bool(single_job_summary.get("single_job_sufficient_for_next_step")),
        "wall_time_seconds": probe_metrics.get("wall_time_seconds"),
        "memory_peak_mb": probe_metrics.get("memory_peak_mb"),
        "validation_output": probe_metrics.get("validation_output", {}),
        "hazard_output": probe_metrics.get("hazard_output", {}),
        "conditional_curve_row_count": probe_metrics.get("conditional_curve_row_count"),
        "metrics_contract_status": metrics_contract.get("status"),
        "source_paths": build_runtime_source_paths(bundle_report),
    }
    if mandatory_metrics:
        section["restartability_metadata"] = mandatory_metrics.get("restartability_metadata", {})
    return section


def build_replay_section(smoke_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": str(smoke_report.get("smoke_status") or "blocked_missing_inputs"),
        "summary": (
            "Replay smoke proves the command path can be rerun from a present run root; fixture-backed replay remains distinct from measured runtime evidence."
        ),
        "replay_smoke_recommendation": (
            "Use replay smoke as fixture-backed restart evidence for review only; do not treat it as a new measured Balfrin run or live-run authorization."
        ),
        "run_root": smoke_report.get("run_root"),
        "run_root_provenance": smoke_report.get("run_root_provenance"),
        "run_root_status": smoke_report.get("run_root_status"),
        "bundle_status": smoke_report.get("bundle_status"),
        "post_run_interpretation_status": smoke_report.get("post_run_interpretation_status"),
        "missing_inputs": smoke_report.get("missing_inputs", []),
        "source_paths": build_section_source_paths(smoke_report),
    }


def build_target_area_aoi_automation_section(target_area_bundle_report: dict[str, Any]) -> dict[str, Any]:
    handoff_report = dict(target_area_bundle_report.get("target_area_demo_handoff_report") or {})
    source_paths = dict(target_area_bundle_report.get("source_paths") or {})
    return {
        "status": str(handoff_report.get("bundle_status") or handoff_report.get("status") or "blocked_missing_inputs"),
        "evidence_type": "unavailable",
        "summary": (
            "AOI automation stays template-only: the frozen handoff records the case skeleton and output-root contract, but it does not authorize execution."
        ),
        "bundle_status": handoff_report.get("bundle_status"),
        "bundle_execution_boundary": handoff_report.get("bundle_execution_boundary"),
        "case_skeleton_path": handoff_report.get("case_skeleton_path"),
        "expected_output_roots_path": handoff_report.get("expected_output_roots_path"),
        "command_manifest_path": handoff_report.get("command_manifest_path"),
        "scenario_generation_handoff_path": handoff_report.get("scenario_generation_handoff_path"),
        "source_paths": {
            "target_area_demo_handoff_report_path": source_paths.get("target_area_demo_handoff_report_path"),
            "case_skeleton_path": handoff_report.get("case_skeleton_path"),
            "expected_output_roots_path": handoff_report.get("expected_output_roots_path"),
        },
    }


def build_target_area_release_scenario_section(target_area_bundle_report: dict[str, Any]) -> dict[str, Any]:
    handoff_report = dict(target_area_bundle_report.get("target_area_demo_handoff_report") or {})
    source_paths = dict(target_area_bundle_report.get("source_paths") or {})
    return {
        "status": str(handoff_report.get("bundle_status") or handoff_report.get("status") or "blocked_missing_inputs"),
        "evidence_type": "unavailable",
        "summary": (
            "Release/scenario automation stays template-only: the frozen handoff captures the command manifest, scenario-generation handoff, and GIS scope summary, but it does not emit a live release plan."
        ),
        "bundle_status": handoff_report.get("bundle_status"),
        "bundle_execution_boundary": handoff_report.get("bundle_execution_boundary"),
        "command_manifest_path": handoff_report.get("command_manifest_path"),
        "scenario_generation_handoff_path": handoff_report.get("scenario_generation_handoff_path"),
        "gis_scope_summary_path": handoff_report.get("gis_scope_summary_path"),
        "case_skeleton_path": handoff_report.get("case_skeleton_path"),
        "source_paths": {
            "target_area_demo_handoff_report_path": source_paths.get("target_area_demo_handoff_report_path"),
            "command_manifest_path": handoff_report.get("command_manifest_path"),
            "scenario_generation_handoff_path": handoff_report.get("scenario_generation_handoff_path"),
            "gis_scope_summary_path": handoff_report.get("gis_scope_summary_path"),
        },
    }


def build_target_area_probe_metrics_section(target_area_bundle_report: dict[str, Any]) -> dict[str, Any]:
    probe_report = dict(target_area_bundle_report.get("probe_metrics_report") or {})
    source_paths = dict(target_area_bundle_report.get("source_paths") or {})
    return {
        "status": str(probe_report.get("report_status") or probe_report.get("metrics_contract_status") or "blocked_missing_inputs"),
        "evidence_type": "blocked",
        "summary": (
            "Target-area probe metrics remain blocked because the preserved run root is not mounted locally; the blocked state stays separate from the measured canonical bundle."
        ),
        "report_status": probe_report.get("report_status"),
        "metrics_contract_status": probe_report.get("metrics_contract_status"),
        "run_root_status": probe_report.get("run_root_status"),
        "run_root": probe_report.get("run_root"),
        "missing_run_root_reason": probe_report.get("missing_run_root_reason"),
        "missing_inputs": probe_report.get("missing_inputs", []),
        "source_paths": {
            "probe_metrics_report_path": source_paths.get("probe_metrics_report_path"),
            "probe_metrics_report_sources": source_paths.get("probe_metrics_report_sources", {}),
        },
    }


def build_target_area_canonical_bundle_section(target_area_bundle_report: dict[str, Any]) -> dict[str, Any]:
    canonical_report = dict(target_area_bundle_report.get("canonical_evidence_bundle") or {})
    source_paths = dict(target_area_bundle_report.get("source_paths") or {})
    return {
        "status": str(canonical_report.get("bundle_status") or canonical_report.get("status") or "blocked_missing_inputs"),
        "evidence_type": "measured",
        "summary": (
            "The canonical target-area bundle is measured, but it remains separate from the target-area handoff and probe-metrics gaps."
        ),
        "bundle_status": canonical_report.get("bundle_status"),
        "bundle_provenance_status": canonical_report.get("bundle_provenance_status"),
        "section_counts": dict((canonical_report.get("bundle_summary") or {}).get("section_counts") or {}),
        "claim_boundaries": dict(canonical_report.get("claim_boundaries") or {}),
        "source_paths": {
            "canonical_bundle_path": source_paths.get("canonical_bundle_path"),
            "canonical_bundle_sources": source_paths.get("canonical_bundle_sources", {}),
        },
    }


def build_restartability_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    restartability = dict((single_job_summary.get("restartability_evidence") or {}))
    return {
        "status": str(bundle_report.get("bundle_status") or single_job_summary.get("metrics_contract", {}).get("status") or "blocked_missing_inputs"),
        "summary": (
            "The single-job path records repeatable job IDs and reducer state, while distributed execution stays deferred."
        ),
        "driver_ready_for_selected_gate_use": restartability.get("driver_ready_for_selected_gate_use"),
        "fresh_baseline_job_id": restartability.get("fresh_baseline_job_id"),
        "repeat_job_ids": restartability.get("repeat_job_ids", []),
        "repeat_reuse_classification": restartability.get("repeat_reuse_classification"),
        "trajectory_plan_id_stable": restartability.get("trajectory_plan_id_stable"),
        "reducer_plan_id_stable": restartability.get("reducer_plan_id_stable"),
        "numerical_artifact_classification": restartability.get("numerical_artifact_classification"),
        "changed_artifact_count": restartability.get("changed_artifact_count"),
        "output_file_count_stable": restartability.get("output_file_count_stable"),
        "metadata_byte_identity_required": restartability.get("metadata_byte_identity_required"),
        "local_restartability_status": restartability.get("local_restartability_status"),
        "reducer_state": bundle_report.get("single_job_execution_summary", {})
        .get("metrics_contract", {})
        .get("mandatory_metrics", {})
        .get("restartability_metadata", {}),
        "source_paths": build_runtime_source_paths(bundle_report),
    }


def build_diagnostic_performance_section() -> dict[str, Any]:
    return {
        "status": "measured",
        "evidence_type": "measured",
        "summary": (
            "Balfrin now has measured single-node postproc diagnostic evidence through 100 zones plus a 24-zone same-size repeatability pair. "
            "TB-652 adds a completed 8-zone compact diagnostic comparison point and TB-665 adds a fresh 32-zone compact diagnostic point from the simplified runner. "
            "The measurements bound reducer wall time, memory, output footprint, and manifest footprint for diagnostic reducer pressure only."
        ),
        "latest_current_diagnostic_probe": {
            "task_id": "TB-665",
            "run_id": "tb665_32_zone_20260527",
            "job_id": "4377419",
            "git_head": "4b335c03e02e7d2e65704a3ae74e9662a3f2d42f",
            "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527",
            "run_record": "/scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527/run_record.json",
            "release_zone_count": 32,
            "scenario_count": 32,
            "reducer_wall_time_seconds": 5.39,
            "max_rss_mb": 33.531,
            "output_file_count": 100,
            "output_bytes": 42188,
            "manifest_bytes": 24426,
            "comparison_anchor": "diagnostic reducer-pressure only; TB-669 is the latest bounded hazard-throughput support point",
        },
        "latest_bounded_diagnostic_probe": {
            "task_id": "TB-652",
            "run_id": "tb652_8_zone_20260527",
            "job_id": "4377075",
            "git_head": "4b335c03e02e7d2e65704a3ae74e9662a3f2d42f",
            "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527",
            "run_record": "/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527/run_record.json",
            "release_zone_count": 8,
            "scenario_count": 8,
            "reducer_wall_time_seconds": 2.11,
            "max_rss_mb": 34.223,
            "output_file_count": 28,
            "output_bytes": 14397,
            "manifest_bytes": 11458,
            "comparison_anchor": "diagnostic reducer-pressure only; TB-669 is the latest bounded hazard-throughput support point",
        },
        "latest_diagnostic": {
            "task_id": "TB-612",
            "run_id": "diagnostic_100_zone_tb611_20260526",
            "job_id": "4372447",
            "git_head": "4b335c0",
            "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526",
            "run_record": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/run_record.json",
            "release_zone_count": 100,
            "reducer_wall_time_seconds": 13.55,
            "max_rss_mb": 34.16,
            "output_file_count": 304,
            "output_bytes": 121172,
            "manifest_bytes": 61119,
        },
        "repeatability_pair": {
            "task_id": "TB-581",
            "status": "measured_repeatability_pair",
            "release_zone_count": 24,
            "runs": [
                {
                    "run_id": "diagnostic_24_zone_repeatability_a_tb581",
                    "job_id": "4368592",
                    "git_head": "5f9c93790cfa89855fdbbb3d30be81a31298bb50",
                    "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_a_tb581",
                    "run_record": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_a_tb581/run_record.json",
                    "reducer_wall_time_seconds": 4.03,
                    "max_rss_mb": 34.242,
                    "output_file_count": 76,
                    "output_bytes": 32922,
                    "manifest_bytes": 20218,
                },
                {
                    "run_id": "diagnostic_24_zone_repeatability_b_tb581",
                    "job_id": "4368593",
                    "git_head": "5f9c93790cfa89855fdbbb3d30be81a31298bb50",
                    "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_b_tb581",
                    "run_record": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_b_tb581/run_record.json",
                    "reducer_wall_time_seconds": 4.03,
                    "max_rss_mb": 39.879,
                    "output_file_count": 76,
                    "output_bytes": 32922,
                    "manifest_bytes": 20218,
                },
            ],
            "bounds": {
                "reducer_wall_time_seconds": {"min": 4.03, "median": 4.03, "max": 4.03, "spread": 0.0},
                "max_rss_mb": {"min": 34.242, "median": 37.0605, "max": 39.879, "spread": 5.637},
                "output_file_count": {"min": 76, "median": 76, "max": 76, "spread": 0},
                "output_bytes": {"min": 32922, "median": 32922, "max": 32922, "spread": 0},
                "manifest_bytes": {"min": 20218, "median": 20218, "max": 20218, "spread": 0},
            },
        },
        "reproduction_commands": [
            "PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 100 --reducer-chunks 4 --reducer-workers 4 --manifest-mode compact --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526 --partition postproc --time 00:30:00",
            "PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 24 --reducer-chunks 2 --reducer-workers 2 --manifest-mode compact --run-id diagnostic_24_zone_repeatability_a_tb581 --partition postproc --time 00:30:00",
            "PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 24 --reducer-chunks 2 --reducer-workers 2 --manifest-mode compact --run-id diagnostic_24_zone_repeatability_b_tb581 --partition postproc --time 00:30:00",
        ],
        "claim_boundary": (
            "diagnostic reducer-pressure performance only; no operational, physical-probability, Swiss-wide, distributed, or non-postproc claim"
        ),
        "source_paths": [
            "archive/task_reports/balfrin_diagnostic_series_tb613.md",
            "scripts/run_balfrin_diagnostic.py",
            "scripts/summarize_balfrin_scale_readiness_matrix.py",
        ],
    }


def build_physical_credibility_section(physical_credibility_report: dict[str, Any]) -> dict[str, Any]:
    validation_state = dict(physical_credibility_report.get("validation_calibration_state") or {})
    source_paths = dict(physical_credibility_report.get("current_evidence_sources") or {})
    return {
        "status": str(physical_credibility_report.get("balfrin_evidence_gap_status") or "blocked_missing_inputs"),
        "evidence_type": "measured",
        "summary": (
            "Measured diagnostic evidence exists, but physical credibility is not established; calibration is missing and the validation evidence remains partial."
        ),
        "balfrin_demo_evidence_status": physical_credibility_report.get("balfrin_demo_evidence_status"),
        "physical_credibility_state": physical_credibility_report.get("physical_credibility_state"),
        "validation_calibration_state": validation_state,
        "diagnostic_reproducibility_only_requirements": list(
            physical_credibility_report.get("diagnostic_reproducibility_only_requirements") or []
        ),
        "design_review_candidate_requirements": list(
            physical_credibility_report.get("design_review_candidate_requirements") or []
        ),
        "missing_physical_requirements": list(physical_credibility_report.get("missing_physical_requirements") or []),
        "claim_boundaries": dict(physical_credibility_report.get("claim_boundaries") or {}),
        "source_paths": source_paths,
    }


def build_swiss_wide_extension_section(
    *,
    bundle_report: dict[str, Any],
    physical_credibility_report: dict[str, Any],
) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    claim_boundaries = dict(bundle_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    no_go_labels = [
        "aoi_count_exceeds_measured_support",
        "total_job_count_exceeds_measured_single_job_support",
    ]
    planning_labels = {
        "no_go": "no_go_extrapolated_beyond_measured_evidence",
        "defer": "defer_scale_up_authorized_false",
        "allowed_next_probe": "allowed_next_probe_measured_existing_artifacts",
    }
    blockers = [
        "aoi_count_exceeds_measured_support",
        "total_job_count_exceeds_measured_single_job_support",
        "distributed_execution_authorized remains false",
        "physical_credibility_status is not_established",
        "calibration_status is missing",
        "validation_status is partial",
        "observed_runout_deposition_intake_status is blocked_missing_inputs",
        "source_frequency_and_temporal_frequency_evidence remains missing",
    ]
    summary = (
        "The architecture is plausibly extensible at the workflow level, but Swiss-wide execution is a no-go on the current evidence because the measured support only covers a single-job, single-AOI boundary and the physical-credibility / calibration gaps remain open."
    )
    return {
        "status": "no_go_extrapolated_beyond_measured_evidence",
        "evidence_type": "measured",
        "summary": summary,
        "architecture_plausibility": "plausibly_extensible",
        "answer": "Plausibly extensible in architecture, but not authorized for Swiss-wide execution.",
        "measurement_status": "measured_existing_artifacts",
        "single_job_sufficient_for_next_step": bool(single_job_summary.get("single_job_sufficient_for_next_step")),
        "no_go_labels": no_go_labels,
        "planning_labels": planning_labels,
        "blockers": blockers,
        "measured_support": {
            "aoi_count": 1,
            "release_zone_count": 10,
            "trajectory_count": 6,
            "single_job_boundary": "one-job",
        },
        "claim_boundaries": {
            "operational_claims_allowed": bool(claim_boundaries.get("operational_claims_allowed", False)),
            "physical_probability_claims_allowed": bool(claim_boundaries.get("physical_probability_claims_allowed", False)),
            "annual_frequency_claims_allowed": bool(claim_boundaries.get("annual_frequency_claims_allowed", False)),
            "risk_exposure_vulnerability_claims_allowed": bool(claim_boundaries.get("risk_exposure_vulnerability_claims_allowed", False)),
            "scale_up_authorized": bool(claim_boundaries.get("scale_up_authorized", False)),
            "distributed_execution_authorized": bool(claim_boundaries.get("distributed_execution_authorized", False)),
        },
        "physical_credibility_state": physical_credibility_report.get("physical_credibility_state"),
        "validation_calibration_state": physical_credibility_report.get("validation_calibration_state"),
        "source_paths": {
            "management_summary_sources": [
                "docs/balfrin_single_job_execution_sufficiency.md",
                "docs/current_maturity_snapshot.md",
                "scripts/summarize_balfrin_physical_credibility_evidence_gaps.py",
                "scripts/estimate_swiss_wide_execution_envelope.py",
            ],
        },
    }


def build_swiss_scale_feasibility_projection_section() -> dict[str, Any]:
    return {
        "status": "projection_only",
        "evidence_type": "projection_only",
        "summary": (
            "Swiss-scale feasibility remains bounded: 10-zone is the hazard-planning boundary, 100-zone is measured diagnostic postproc reducer-pressure evidence, "
            "and broader regional plus Swiss-wide workflows remain phase changes. "
            "TB-669 is the measured 12-zone hazard-throughput support point; TB-652 and TB-665 are diagnostic comparison points, not larger hazard-throughput support points. "
            "The next blockers are scientific evidence for physical use, larger hazard-throughput scaling, and reducer/replay pressure before larger claims."
        ),
        "projection_classification": {
            "10_zone": "hazard_planning_boundary",
            "16_zone": "measured_diagnostic_postproc",
            "24_zone": "measured_repeatable_diagnostic_postproc",
            "32_zone": "measured_diagnostic_postproc",
            "40_zone": "measured_diagnostic_postproc",
            "100_zone": "measured_diagnostic_postproc",
            "regional_split_probe": "measured",
            "regional": "deferred_phase_change",
            "swiss_wide": "deferred_phase_change",
        },
        "upstream_data_blockers": [
            "source_frequency",
            "calibration_holdout",
            "physical_probability_evidence",
        ],
        "top_blockers": [
            "scientific_evidence",
            "hazard_throughput",
            "reducer_pressure",
            "output_bytes",
        ],
        "measured_basis": {
            "aoi_count": 1,
            "release_zone_count": 10,
            "trajectory_count": 6,
            "single_node_postproc_boundary": True,
            "adjacent_candidate_review_path": True,
            "diagnostic_release_zone_count": 100,
            "diagnostic_latest_job_id": "4372447",
            "diagnostic_repeatability_job_ids": ["4368592", "4368593"],
            "diagnostic_reducer_wall_time_seconds": 13.55,
            "diagnostic_output_file_count": 304,
            "diagnostic_output_bytes": 121172,
            "diagnostic_memory_peak_mb_bounds": {"min": 33.711, "max": 39.879},
            "latest_bounded_diagnostic_task_id": "TB-652",
            "latest_bounded_diagnostic_job_id": "4377075",
            "latest_bounded_diagnostic_release_zone_count": 8,
            "latest_bounded_diagnostic_reducer_wall_time_seconds": 2.11,
            "latest_bounded_diagnostic_output_file_count": 28,
            "latest_bounded_diagnostic_output_bytes": 14397,
            "hazard_throughput_latest_job_id": "4378015",
            "hazard_throughput_latest_task_id": "TB-669",
            "hazard_throughput_latest_release_zone_count": 12,
            "hazard_throughput_latest_wall_seconds": 0.288978714030236,
            "hazard_throughput_latest_memory_peak_mb": 47.016,
            "hazard_throughput_latest_hazard_output_file_count": 29,
            "hazard_throughput_latest_hazard_output_bytes": 1148530,
            "hazard_throughput_latest_conditional_curve_rows": 36864,
            "hazard_throughput_previous_job_id": "4372656",
            "hazard_throughput_previous_task_id": "TB-619",
            "regional_split_job_id": "4367244",
            "regional_split_validation_output_file_count": 130,
            "regional_split_hazard_output_file_count": 57,
            "regional_split_conditional_curve_rows": 729600,
            "regional_split_preservation_status": "ready_for_demonstration_evidence",
        },
        "source_paths": [
            "scripts/estimate_large_scale_execution.py",
            "scripts/summarize_balfrin_scale_readiness_matrix.py",
            "docs/swiss_scale_feasibility_projection.md",
            "docs/current_maturity_snapshot.md",
            "archive/task_reports/balfrin_multi_zone_hazard_run_tb407.md",
            "archive/task_reports/balfrin_diagnostic_series_tb613.md",
            "archive/task_reports/balfrin_regional_split_run_root_metrics_tb566.md",
            "archive/task_reports/balfrin_regional_split_probe_gate_tb432.md",
            "docs/balfrin_scale_demonstration_management_package.md",
        ],
    }


def build_failed_closed_section() -> dict[str, Any]:
    return {
        "status": "failed_closed",
        "evidence_type": "failed_closed",
        "summary": (
            "The recent submit branches, including the canonical TB-362 two-zone hazard path and the rebuilt TB-386 management-AOI path on the adjacent-candidate review bundle and generated scenario table, "
            "failed closed before live execution, so they remain guardrail evidence rather than measured scale capability. TB-432 is still historical failed-closed/no-submit regional split evidence, while TB-407 and TB-448 are separate measured evidence and do not change those failed-closed classifications."
        ),
        "failed_closed_branches": [
            {
                "task": "TB-362",
                "branch": "two-zone hazard submit",
                "failure_point": "remote pre-submit blocked with output_profile_status=blocked_output_profile before sbatch",
                "classification": "failed_closed",
                "preflight_status": "blocked_reducer_budget",
                "authorization_status": "authorized",
                "reducer_budget_status": "ready",
                "submit_contract_status": "ready",
                "output_budget_acceptance_status": "accepted",
                "source_report": "archive/task_reports/balfrin_two_zone_hazard_run_tb362.md",
            },
            {
                "task": "TB-352",
                "branch": "smallest multi-zone hazard",
                "failure_point": "scheduler submission blocked by reducer-budget preflight before sbatch",
                "classification": "failed_closed",
            },
            {
                "task": "TB-332/TB-333",
                "branch": "four-zone hazard submit",
                "failure_point": "authorization checksum mismatch before sbatch",
                "classification": "failed_closed",
            },
            {
                "task": "TB-321",
                "branch": "live-shape repair",
                "failure_point": "reviewed command targeted the four-zone review-only profile and an unwritable /scratch/rust_rockfall path",
                "classification": "failed_closed",
            },
            {
                "task": "TB-309",
                "branch": "reviewed two-zone submit package",
                "failure_point": "target-area wrapper manifest used instead of the executable contract",
                "classification": "failed_closed",
            },
            {
                "task": "TB-432",
                "branch": "regional split postproc probe",
                "failure_point": "remote checkout hygiene stopped the live gate before sbatch",
                "classification": "failed_closed",
                "preflight_status": "blocked_dirty_remote_checkout",
                "source_report": "archive/task_reports/balfrin_regional_split_probe_gate_tb432.md",
            },
        ],
        "top_blockers": [
            "output_profile_status_blocked_output_profile",
            "authorization_record_checksum_mismatch",
            "review_only_profile_mismatch",
            "submit_contract_manifest_mismatch",
            "remote_checkout_hygiene",
        ],
        "source_paths": [
            "docs/current_maturity_snapshot.md",
            "archive/task_reports/balfrin_two_zone_hazard_run_tb362.md",
            "docs/multi_zone_reducer_pressure_probe.md",
            "docs/balfrin_single_job_execution_sufficiency.md",
            "archive/task_reports/balfrin_regional_split_probe_gate_tb432.md",
        ],
    }


def build_gis_scope_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    gis_scope_report = dict(bundle_report.get("gis_cog_scope_report") or {})
    gis_report = dict(bundle_report.get("gis_cog_readiness_report") or {})
    return {
        "status": str(gis_scope_report.get("scope_status") or gis_report.get("gis_cog_readiness_status") or "blocked_missing_inputs"),
        "summary": (
            "GIS scope is explicit: the package distinguishes full scope, bounded scope, and blocked inputs without calling the result an operational map."
        ),
        "scope_status": gis_scope_report.get("scope_status"),
        "scope_delta_status": gis_scope_report.get("scope_delta_status"),
        "parity_status": gis_scope_report.get("parity_status"),
        "standard_package_readiness_status": gis_report.get("standard_package_readiness_status"),
        "converted_package_readiness_status": gis_report.get("converted_package_readiness_status"),
        "converted_package_layer_inventory_status": gis_report.get("converted_package_layer_inventory_status"),
        "layer_counts": bundle_report.get("gis_cog_parity_report", {}).get("layer_counts", {}),
        "scope_delta": bundle_report.get("gis_cog_parity_report", {}).get("scope_delta", {}),
        "manifest_consistency": bundle_report.get("gis_cog_parity_report", {}).get("manifest_consistency", {}),
        "source_paths": build_gis_source_paths(bundle_report),
    }


def build_uncertainty_section(bundle_report: dict[str, Any], smoke_report: dict[str, Any]) -> dict[str, Any]:
    post_run_report = dict(bundle_report.get("post_run_interpretation_gate_report") or {})
    failure_report = dict(bundle_report.get("failure_taxonomy_report") or {})
    return {
        "status": str(bundle_report.get("bundle_status") or post_run_report.get("interpretation_status") or "blocked_missing_inputs"),
        "evidence_type": "measured",
        "summary": (
            "Scientific meaning remains conditional and non-operational; the package separates measured evidence from fixture-backed replay and keeps the false claim boundaries intact."
        ),
        "bundle_status": bundle_report.get("bundle_status"),
        "bundle_summary": bundle_report.get("bundle_summary", {}),
        "interpretation_status": post_run_report.get("interpretation_status"),
        "artifact_acceptance_status": post_run_report.get("artifact_acceptance_status"),
        "taxonomy_status": failure_report.get("taxonomy_status"),
        "status_counts": failure_report.get("status_counts", {}),
        "section_counts": bundle_report.get("section_provenance_profile", []),
        "probe_metrics_status": bundle_report.get("probe_metrics", {}).get("status"),
        "smoke_status": smoke_report.get("smoke_status"),
        "smoke_missing_inputs": smoke_report.get("missing_inputs", []),
        "source_paths": build_uncertainty_source_paths(bundle_report, smoke_report),
    }


def build_claim_boundary_section(post_run_report: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    return {
        "status": "guarded",
        "summary": (
            "Claim boundaries stay false: the package is a conditional diagnostic review artifact, not an operational, physical-probability, annual-frequency, or risk product."
        ),
        "claim_boundaries": claim_boundaries,
        "source_paths": [str(post_run_gate.DEFAULT_CONTRACT), "docs/balfrin_post_run_interpretation_gate.md"],
    }


def build_scaling_section(bundle_report: dict[str, Any], post_run_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    single_job_sufficient = bool(single_job_summary.get("single_job_sufficient_for_next_step"))
    scale_up_authorized = bool(claim_boundaries.get("scale_up_authorized", False))
    distributed_execution_authorized = bool(claim_boundaries.get("distributed_execution_authorized", False))
    if single_job_sufficient:
        scaling_implication = (
            "Keep the next step at the single-job boundary; scale-up and distributed execution stay deferred."
        )
    else:
        scaling_implication = (
            "Do not infer a scale-up path from this package; the current evidence does not justify moving beyond the single-job boundary."
        )
    return {
        "status": "measured",
        "summary": "Scaling stays bounded by the measured single-job path and the measured smallest multi-zone probe; the package does not authorize a larger execution mode.",
        "single_job_sufficient_for_next_step": single_job_sufficient,
        "scale_up_authorized": scale_up_authorized,
        "distributed_execution_authorized": distributed_execution_authorized,
        "scaling_implication": scaling_implication,
        "source_paths": build_runtime_source_paths(bundle_report),
    }


def build_next_decision_section(bundle_report: dict[str, Any], post_run_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    next_authorized_step = "management review of this package"
    if bool(single_job_summary.get("single_job_sufficient_for_next_step")) and not bool(
        claim_boundaries.get("scale_up_authorized", False)
    ):
        recommendation = (
            "The next authorized step is management review of this package; no new Balfrin submission, scale-up, or distributed execution is authorized here."
        )
    else:
        recommendation = (
            "The package stays advisory only; a separate authorization would be required before any further Balfrin execution."
        )
    return {
        "status": "deferred",
        "summary": "This package is for review and decision-making, not for launching another Balfrin job; reducer-pressure optimization is the next ranked executable action, while scenario batching, replay smoke, and candidate-stability evidence remain bounded support surfaces.",
        "recommended_next_authorized_step": next_authorized_step,
        "recommendation": recommendation,
        "evidence_type": "deferred",
        "source_paths": [str(post_run_gate.DEFAULT_CONTRACT), "docs/balfrin_single_job_execution_sufficiency.md"],
    }


def build_source_artifacts(
    *,
    bundle_report: dict[str, Any],
    smoke_report: dict[str, Any],
    target_area_bundle_report: dict[str, Any],
    physical_credibility_report: dict[str, Any],
    package_artifact_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    return {
        "package_artifact_dir": str(package_artifact_dir),
        "bundle_artifact_dir": str(Path(bundle_report.get("canonical_bundle_path") or DEFAULT_ARTIFACT_DIR / "balfrin_evidence_bundle_v1")),
        "smoke_artifact_dir": str(smoke_report.get("artifact_dir") or (package_artifact_dir / "replay_smoke_v1")),
        "target_area_bundle_artifact_dir": str(
            Path(
                target_area_bundle_report.get("canonical_bundle_path")
                or DEFAULT_TARGET_AREA_BUNDLE_DIR
            )
        ),
        "physical_credibility_artifact_dir": str(DEFAULT_PHYSICAL_CREDIBILITY_GAP_DIR),
        "replay_run_root": str(run_root),
        "bundle_canonical_path": str(bundle_report.get("canonical_bundle_path") or ""),
        "smoke_run_root_provenance": smoke_report.get("run_root_provenance"),
        "target_area_bundle_status": target_area_bundle_report.get("bundle_status"),
        "physical_credibility_status": physical_credibility_report.get("balfrin_evidence_gap_status"),
    }


def build_regeneration_commands(*, run_root: Path, package_artifact_dir: Path) -> list[str]:
    bundle_artifact_dir = package_artifact_dir / "balfrin_evidence_bundle_v1"
    smoke_artifact_dir = package_artifact_dir / "balfrin_demonstration_replay_smoke_v1"
    target_area_bundle_artifact_dir = package_artifact_dir / "balfrin_target_area_evidence_bundle_v1"
    physical_credibility_artifact_dir = package_artifact_dir / "balfrin_physical_credibility_evidence_gaps_v1"
    return [
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_evidence_bundle.py",
                "--artifact-dir",
                str(bundle_artifact_dir),
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_demonstration_replay_smoke.py",
                "--run-root",
                str(run_root),
                "--artifact-dir",
                str(smoke_artifact_dir),
                "--format",
                "json",
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_target_area_evidence_bundle.py",
                "--artifact-dir",
                str(target_area_bundle_artifact_dir),
                "--format",
                "json",
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_physical_credibility_evidence_gaps.py",
                "--format",
                "json",
                "--json-output",
                str(physical_credibility_artifact_dir / f"{physical_gaps.SCHEMA_VERSION}.json"),
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_management_demo_package.py",
                "--run-root",
                str(run_root),
                "--artifact-dir",
                str(package_artifact_dir),
                "--format",
                "json",
            ]
        ),
    ]


def render_text_report(report: dict[str, Any]) -> str:
    readiness_matrix = dict(report.get("readiness_matrix") or {})
    lines = [
        "Balfrin Management Demonstration Package",
        f"schema_version: {report['schema_version']}",
        f"package_status: {report['package_status']}",
        f"package_provenance_status: {report.get('package_provenance_status', report['package_status'])}",
        f"package_artifact_dir: {report['package_artifact_dir']}",
        f"run_root: {report['run_root']}",
        "package_summary:",
        f"  status: {report['package_summary']['status']}",
        f"  summary: {report['package_summary']['summary']}",
        "  section_counts:",
    ]
    for key in (
        "measured",
        "fixture_backed",
        "unavailable",
        "blocked_missing_inputs",
        "projection_only",
        "failed_closed",
        "deferred",
    ):
        if key in report["package_summary"]["section_counts"]:
            lines.append(f"    {key}: {report['package_summary']['section_counts'][key]}")
    lines.extend(
        [
            "runtime_section:",
            f"  status: {report['runtime_section'].get('status', 'unknown')}",
            f"  wall_time_seconds: {report['runtime_section'].get('wall_time_seconds', 'unknown')}",
            f"  memory_peak_mb: {report['runtime_section'].get('memory_peak_mb', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['runtime_section'].get('single_job_sufficient_for_next_step', False)}",
            "replay_section:",
            f"  status: {report['replay_section'].get('status', 'unknown')}",
            f"  run_root_provenance: {report['replay_section'].get('run_root_provenance', 'unknown')}",
            f"  run_root_status: {report['replay_section'].get('run_root_status', 'unknown')}",
            f"  replay_smoke_recommendation: {report['replay_section'].get('replay_smoke_recommendation', '')}",
            "target_area_aoi_automation_section:",
            f"  status: {report['target_area_aoi_automation_section'].get('status', 'unknown')}",
            f"  bundle_status: {report['target_area_aoi_automation_section'].get('bundle_status', 'unknown')}",
            "target_area_release_scenario_section:",
            f"  status: {report['target_area_release_scenario_section'].get('status', 'unknown')}",
            f"  command_manifest_path: {report['target_area_release_scenario_section'].get('command_manifest_path', 'unknown')}",
            "target_area_probe_metrics_section:",
            f"  status: {report['target_area_probe_metrics_section'].get('status', 'unknown')}",
            f"  report_status: {report['target_area_probe_metrics_section'].get('report_status', 'unknown')}",
            "target_area_canonical_bundle_section:",
            f"  status: {report['target_area_canonical_bundle_section'].get('status', 'unknown')}",
            f"  bundle_status: {report['target_area_canonical_bundle_section'].get('bundle_status', 'unknown')}",
            "restartability_section:",
            f"  status: {report['restartability_section'].get('status', 'unknown')}",
            f"  repeat_reuse_classification: {report['restartability_section'].get('repeat_reuse_classification', 'unknown')}",
            f"  trajectory_plan_id_stable: {report['restartability_section'].get('trajectory_plan_id_stable', False)}",
            f"  reducer_plan_id_stable: {report['restartability_section'].get('reducer_plan_id_stable', False)}",
            "gis_scope_section:",
            f"  status: {report['gis_scope_section'].get('status', 'unknown')}",
            f"  scope_status: {report['gis_scope_section'].get('scope_status', 'unknown')}",
            f"  scope_delta_status: {report['gis_scope_section'].get('scope_delta_status', 'unknown')}",
            "uncertainty_section:",
            f"  status: {report['uncertainty_section'].get('status', 'unknown')}",
            f"  interpretation_status: {report['uncertainty_section'].get('interpretation_status', 'unknown')}",
            f"  taxonomy_status: {report['uncertainty_section'].get('taxonomy_status', 'unknown')}",
            "claim_boundary_section:",
            f"  status: {report['claim_boundary_section'].get('status', 'unknown')}",
            f"  operational_claims_allowed: {report['claim_boundaries'].get('operational_claims_allowed', False)}",
            f"  physical_probability_claims_allowed: {report['claim_boundaries'].get('physical_probability_claims_allowed', False)}",
            f"  annual_frequency_claims_allowed: {report['claim_boundaries'].get('annual_frequency_claims_allowed', False)}",
            f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries'].get('risk_exposure_vulnerability_claims_allowed', False)}",
            f"  scale_up_authorized: {report['claim_boundaries'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['claim_boundaries'].get('distributed_execution_authorized', False)}",
            "scaling_section:",
            f"  status: {report['scaling_section'].get('status', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['scaling_section'].get('single_job_sufficient_for_next_step', False)}",
            f"  scale_up_authorized: {report['scaling_section'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['scaling_section'].get('distributed_execution_authorized', False)}",
            f"  scaling_implication: {report['scaling_section'].get('scaling_implication', 'unknown')}",
            "diagnostic_performance_section:",
            f"  status: {report['diagnostic_performance_section'].get('status', 'unknown')}",
            f"  latest_job_id: {report['diagnostic_performance_section'].get('latest_diagnostic', {}).get('job_id', 'unknown')}",
            f"  latest_release_zone_count: {report['diagnostic_performance_section'].get('latest_diagnostic', {}).get('release_zone_count', 'unknown')}",
            f"  repeatability_status: {report['diagnostic_performance_section'].get('repeatability_pair', {}).get('status', 'unknown')}",
            f"  claim_boundary: {report['diagnostic_performance_section'].get('claim_boundary', 'unknown')}",
            "physical_credibility_section:",
            f"  status: {report['physical_credibility_section'].get('status', 'unknown')}",
            f"  physical_credibility_state: {report['physical_credibility_section'].get('physical_credibility_state', 'unknown')}",
            "swiss_wide_extension_section:",
            f"  status: {report['swiss_wide_extension_section'].get('status', 'unknown')}",
            f"  answer: {report['swiss_wide_extension_section'].get('answer', 'unknown')}",
            f"  no_go_labels: {report['swiss_wide_extension_section'].get('no_go_labels', [])}",
            "swiss_scale_feasibility_projection_section:",
            f"  status: {report['swiss_scale_feasibility_projection_section'].get('status', 'unknown')}",
            f"  projection_classification: {report['swiss_scale_feasibility_projection_section'].get('projection_classification', {})}",
            f"  top_blockers: {report['swiss_scale_feasibility_projection_section'].get('top_blockers', [])}",
            "failed_closed_section:",
            f"  status: {report['failed_closed_section'].get('status', 'unknown')}",
            f"  failed_closed_branches: {len(report['failed_closed_section'].get('failed_closed_branches', []))}",
            "next_decision_section:",
            f"  status: {report['next_decision_section'].get('status', 'unknown')}",
            f"  recommended_next_authorized_step: {report['next_decision_section'].get('recommended_next_authorized_step', 'unknown')}",
            f"  recommendation: {report['next_decision_section'].get('recommendation', 'unknown')}",
            "readiness_matrix:",
            f"  status: {readiness_matrix.get('status', 'unknown')}",
            f"  summary: {readiness_matrix.get('summary', 'unknown')}",
            f"  recommended_next_milestone: {readiness_matrix.get('recommended_next_milestone', {}).get('recommendation', 'unknown')}",
            f"  recommended_next_milestone_reason: {readiness_matrix.get('recommended_next_milestone', {}).get('reason', 'unknown')}",
            "  rows:",
        ]
    )
    for row in readiness_matrix.get("rows", []):
        lines.append(
            f"    - {row.get('gate', 'unknown')}: {row.get('status', 'unknown')} | {row.get('gate_status', 'unknown')} | {row.get('evidence_status', 'unknown')}"
        )
    lines.extend(
        [
            "section_provenance_profile:",
        ]
    )
    for section in report["section_provenance_profile"]:
        lines.append(
            f"  - {section.get('section', 'unknown')}: {section.get('evidence_type', 'unknown')} | {section.get('status', 'unknown')}"
        )
    lines.append("regeneration_commands:")
    for command in report.get("regeneration_commands", []):
        lines.append(f"  - {command}")
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        lines.extend(f"  - {item}" for item in report["missing_inputs"])
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["package_artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    json_output = json_output or artifact_dir / f"{SCHEMA_VERSION}.json"
    text_output = text_output or artifact_dir / f"{SCHEMA_VERSION}.txt"
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_output.write_text(render_text_report(report), encoding="utf-8")


def section_status(section_payload: dict[str, Any]) -> str:
    status = str(
        section_payload.get("status")
        or section_payload.get("run_root_status")
        or section_payload.get("scope_status")
        or section_payload.get("interpretation_status")
        or ""
    ).strip()
    return status or "blocked_missing_inputs"


def classify_evidence_type(section_payload: dict[str, Any], source_paths: list[str]) -> str:
    status = section_status(section_payload)
    evidence_type = str(section_payload.get("evidence_type") or "").strip()
    if evidence_type in {"measured", "fixture_backed", "unavailable", "blocked", "projection_only", "failed_closed", "deferred"}:
        return evidence_type
    if evidence_type == "blocked_missing_inputs":
        return "blocked"
    if status.startswith("blocked") or status == "missing":
        return "blocked"
    if evidence_type:
        return evidence_type
    if any(bundle.is_fixture_path(path) for path in source_paths):
        return "fixture_backed"
    return "measured"


def derive_package_status(section_provenance_profile: list[dict[str, Any]]) -> str:
    evidence_types = {str(section.get("evidence_type") or "blocked") for section in section_provenance_profile}
    if evidence_types == {"blocked"}:
        return "blocked_missing_inputs"
    if "measured" in evidence_types and "fixture_backed" in evidence_types:
        return "mixed_provenance"
    if evidence_types == {"fixture_backed"}:
        return "fixture_backed"
    if "unavailable" in evidence_types or "blocked" in evidence_types:
        return "mixed_provenance"
    return "measured"


def summarize_package(
    package_status: str,
    runtime_section: dict[str, Any],
    replay_section: dict[str, Any],
    target_area_aoi_automation_section: dict[str, Any],
    target_area_release_scenario_section: dict[str, Any],
    target_area_probe_metrics_section: dict[str, Any],
    target_area_canonical_bundle_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    claim_boundary_section: dict[str, Any],
    scaling_section: dict[str, Any],
    diagnostic_performance_section: dict[str, Any],
    physical_credibility_section: dict[str, Any],
    swiss_wide_extension_section: dict[str, Any],
    swiss_scale_feasibility_projection_section: dict[str, Any],
    failed_closed_section: dict[str, Any],
    next_decision_section: dict[str, Any],
) -> str:
    if package_status == "blocked_missing_inputs":
        return "Balfrin management package is blocked because one or more required sections are missing."
    replay_status = str(replay_section.get("run_root_provenance") or "unknown")
    aoi_status = str(target_area_aoi_automation_section.get("status") or "unknown").replace("_", "-")
    release_status = str(target_area_release_scenario_section.get("status") or "unknown").replace("_", "-")
    probe_status = str(target_area_probe_metrics_section.get("status") or "unknown").replace("_", "-")
    physical_state = str(
        physical_credibility_section.get("physical_credibility_state")
        or physical_credibility_section.get("status")
        or "unknown"
    )
    swiss_wide_answer = str(swiss_wide_extension_section.get("answer") or "Swiss-wide extension remains deferred.")
    projection_summary = str(
        swiss_scale_feasibility_projection_section.get("summary")
        or "Swiss-scale feasibility remains projection-only."
    )
    diagnostic_summary = str(
        diagnostic_performance_section.get("summary")
        or "Balfrin diagnostic performance evidence is not yet packaged."
    )
    failed_closed_summary = str(
        failed_closed_section.get("summary")
        or "Failed-closed branches remain separate from measured evidence."
    )
    scaling_implication = str(scaling_section.get("scaling_implication") or "Scaling stays bounded by the single-job path.")
    next_step = str(next_decision_section.get("recommended_next_authorized_step") or "management review of this package")
    if package_status == "mixed_provenance":
        return (
            "Runtime, restartability, GIS scope, uncertainty, and claim boundaries are measured; "
            f"replay is fixture-backed, AOI automation is {aoi_status}, release/scenario automation is {release_status}, "
            f"target-area probe metrics are {probe_status}, Swiss-scale feasibility is projection-only, and failed-closed branches stay separate. "
            f"{diagnostic_summary} {projection_summary} {failed_closed_summary} {swiss_wide_answer} Physical credibility is {physical_state}. "
            f"{scaling_implication} The next authorized step is {next_step}."
        )
    if package_status == "fixture_backed":
        return (
            f"All package sections are fixture-backed, so the manifest is replayable but does not represent live measured evidence. {scaling_implication} The next authorized step is {next_step}."
        )
    return (
        f"Runtime, replay, restartability, GIS scope, uncertainty, and claim boundaries are explicit; replay provenance is {replay_status} and operational, annual-frequency, physical-probability, scale-up, and distributed-execution claims remain false. {projection_summary} {failed_closed_summary} {swiss_wide_answer} {scaling_implication} The next authorized step is {next_step}."
    )


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "measured": 0,
        "fixture_backed": 0,
        "unavailable": 0,
        "blocked_missing_inputs": 0,
        "projection_only": 0,
        "failed_closed": 0,
        "deferred": 0,
    }
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type == "measured":
            counts["measured"] += 1
        elif evidence_type == "fixture_backed":
            counts["fixture_backed"] += 1
        elif evidence_type == "unavailable":
            counts["unavailable"] += 1
        elif evidence_type == "projection_only":
            counts["projection_only"] += 1
        elif evidence_type == "failed_closed":
            counts["failed_closed"] += 1
        elif evidence_type == "deferred":
            counts["deferred"] += 1
        else:
            counts["blocked_missing_inputs"] += 1
    return counts


def build_section_source_paths(section_payload: dict[str, Any]) -> list[str]:
    paths = section_payload.get("source_paths")
    if isinstance(paths, list):
        return [str(item) for item in paths if isinstance(item, str) and item]
    if isinstance(paths, dict):
        collected: list[str] = []
        for value in paths.values():
            if isinstance(value, str) and value:
                collected.append(value)
            elif isinstance(value, list):
                collected.extend(str(item) for item in value if isinstance(item, str) and item)
        return collected
    if isinstance(paths, str) and paths:
        return [paths]
    return []


def build_runtime_source_paths(bundle_report: dict[str, Any]) -> list[str]:
    source_paths = dict(bundle_report.get("source_paths") or {})
    record_paths = source_paths.get("single_job_record_paths")
    if isinstance(record_paths, dict):
        return [str(value) for value in record_paths.values() if isinstance(value, str) and value]
    return []


def build_gis_source_paths(bundle_report: dict[str, Any]) -> list[str]:
    source_paths = dict(bundle_report.get("source_paths") or {})
    artifact_roots = source_paths.get("gis_artifact_roots")
    if isinstance(artifact_roots, list):
        return [str(value) for value in artifact_roots if isinstance(value, str) and value]
    return []


def build_uncertainty_source_paths(bundle_report: dict[str, Any], smoke_report: dict[str, Any]) -> list[str]:
    paths = []
    source_paths = dict(bundle_report.get("source_paths") or {})
    contract_path = source_paths.get("post_run_contract_path")
    if isinstance(contract_path, str) and contract_path:
        paths.append(contract_path)
    smoke_root = smoke_report.get("run_root")
    if isinstance(smoke_root, str) and smoke_root:
        paths.append(smoke_root)
    return paths


def evidence_sources(source_artifacts: dict[str, Any]) -> list[str]:
    sources = [
        "scripts/summarize_balfrin_evidence_bundle.py",
        "scripts/summarize_balfrin_demonstration_replay_smoke.py",
        "scripts/summarize_balfrin_target_area_evidence_bundle.py",
        "scripts/summarize_balfrin_physical_credibility_evidence_gaps.py",
        "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        "scripts/summarize_balfrin_single_job_execution.py",
        "scripts/audit_gis_cog_package_readiness.py",
        "docs/swiss_scale_feasibility_projection.md",
        "docs/balfrin_single_job_execution_sufficiency.md",
        "docs/current_maturity_snapshot.md",
        "docs/target_area_physical_evidence_acquisition_pack.md",
        "scripts/estimate_swiss_wide_execution_envelope.py",
    ]
    if source_artifacts:
        sources.append(str(source_artifacts.get("package_artifact_dir") or DEFAULT_ARTIFACT_DIR))
    return sources


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


if __name__ == "__main__":
    raise SystemExit(main())
