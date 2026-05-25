#!/usr/bin/env python3
"""Recommend the next local scientific backlog from current audit outputs.

The helper is read-only. It consolidates local denominator, traceability,
fragility, second-site, holdout, and calibration-separation reports into a
ranked follow-up queue. It does not edit the backlog, access Balfrin, authorize
scale-up, or upgrade physical, annual-frequency, operational, risk, or
distributed-execution claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_chant_sura_holdout_split as holdout_split
from scripts import audit_conditional_denominator_provenance as denominator
from scripts import audit_trajectory_deposition_traceability as traceability
from scripts import check_calibration_separation_preflight as calibration
from scripts import inventory_second_site_local_blockers as second_site
from scripts import print_agent_task_context as task_context
from scripts import rank_local_hazard_layer_fragility as fragility
from scripts import summarize_extreme_layer_sensitivity_smoke as sensitivity
from scripts.lib import local_scientific_progress as local_progress


SCHEMA_VERSION = "local_scientific_backlog_recommendation_v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        choices=("backlog", "progress"),
        default="backlog",
        help="Report to render. 'progress' replaces the retired summarize_local_scientific_progress.py script.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_progress_report() if args.report == "progress" else build_report()
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.report == "progress":
        print(local_progress.render_text_report(report))
    else:
        print(render_text_report(report))
    return 0


def build_progress_report() -> dict[str, Any]:
    return local_progress.build_report()


def build_report() -> dict[str, Any]:
    source_reports = build_source_reports()
    active_tasks = task_context.parse_active_tasks(task_context.read_backlog())
    recommendations = attach_next_execution_plans(build_recommendations(source_reports))
    interpretation_gate = build_local_map_interpretation_gate(
        source_reports["denominator"],
        source_reports["traceability"],
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "recommendation_status": "ready",
        "active_task_count": len(active_tasks),
        "active_task_ids": [task.task_id for task in active_tasks],
        "source_report_statuses": source_statuses(source_reports),
        "local_map_interpretation_gate": interpretation_gate,
        "next_command_coverage": build_next_command_coverage(recommendations),
        "ranked_followups": recommendations,
        "claim_boundaries": {
            "live_balfrin_access_required": False,
            "distributed_execution_authorized": False,
            "scale_up_authorized": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "operational_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "backlog_modified": False,
        },
        "recommended_backlog_size": len(recommendations),
}


def build_local_map_interpretation_gate(
    denominator_report: dict[str, Any],
    traceability_report: dict[str, Any],
) -> dict[str, Any]:
    denominator_ready = denominator_report.get("audit_status") == "complete"
    traceability_ready = traceability_report.get("audit_status") == "traceable"
    failing_evidence = []
    if not denominator_ready:
        failing_evidence.append(
            {
                "audit": "conditional_denominator_provenance",
                "status": denominator_report.get("audit_status", "unknown"),
                "missing_or_failed": list(denominator_report.get("missing_evidence") or []),
                "next_local_follow_up": denominator_report.get("next_local_follow_up", ""),
            }
        )
    if not traceability_ready:
        failing_evidence.append(
            {
                "audit": "trajectory_deposition_traceability",
                "status": traceability_report.get("audit_status", "unknown"),
                "missing_or_failed": list(traceability_report.get("missing_or_failed_checks") or []),
                "next_local_follow_up": traceability_report.get("next_local_follow_up", ""),
            }
        )
    return {
        "schema_version": "local_map_interpretation_gate_v1",
        "gate_status": "ready_for_conditional_map_interpretation" if not failing_evidence else "blocked_missing_interpretation_evidence",
        "denominator_audit_status": denominator_report.get("audit_status", "unknown"),
        "traceability_audit_status": traceability_report.get("audit_status", "unknown"),
        "failing_evidence": failing_evidence,
        "required_command": (
            "PYENV_VERSION=system uv run python scripts/audit_conditional_denominator_provenance.py --format json "
            "&& PYENV_VERSION=system uv run python scripts/audit_trajectory_deposition_traceability.py --format json"
        ),
        "next_local_recovery_command": (
            failing_evidence[0]["next_local_follow_up"]
            if failing_evidence
            else "Proceed only with conditional diagnostic map interpretation; preserve denominator and deposition traceability in the interpretation note."
        ),
        "claim_boundaries": {
            "conditional_diagnostic_interpretation_only": True,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "operational_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
    }


def build_source_reports() -> dict[str, dict[str, Any]]:
    return {
        "local_progress": local_progress.build_report(),
        "denominator": denominator.build_report(),
        "traceability": traceability.build_report(),
        "fragility": fragility.build_report(),
        "sensitivity": sensitivity.build_report(),
        "second_site": second_site.build_report(),
        "holdout_split": holdout_split.build_report(),
        "calibration_separation": calibration.build_report(),
    }


def source_statuses(source_reports: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        "local_progress": source_reports["local_progress"]["scientific_status"]["physical_credibility_status"],
        "denominator": source_reports["denominator"]["audit_status"],
        "traceability": source_reports["traceability"]["audit_status"],
        "fragility": source_reports["fragility"]["ranking_status"],
        "sensitivity": source_reports["sensitivity"]["smoke_status"],
        "second_site": source_reports["second_site"]["inventory_status"],
        "holdout_split": source_reports["holdout_split"]["audit_status"],
        "calibration_separation": source_reports["calibration_separation"]["preflight_status"],
    }


def build_recommendations(source_reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    second_site_report = source_reports["second_site"]
    sensitivity_report = source_reports["sensitivity"]
    denominator_report = source_reports["denominator"]
    traceability_report = source_reports["traceability"]
    holdout_report = source_reports["holdout_split"]
    calibration_report = source_reports["calibration_separation"]

    items = [
        {
            "rank": 1,
            "task_seed": "Repair Chant Sura Terrain Crop Extent QA",
            "track_id": "second_site_terrain_crop_extent_repair",
            "source_reports": ["second_site"],
            "dependency_status": second_site_report["first_blocking_group"],
            "why_now": "Second-site progress is blocked locally because the staged terrain crop does not contain the configured AOI extent.",
            "suggested_command": second_site_report["next_local_unblock_command"],
            "expected_measurement": "terrain_domain_qa_status becomes ready or reports the next concrete terrain blocker",
            "claim_boundary": "local input staging only; no download is authorized by this recommendation",
        },
        {
            "rank": 2,
            "task_seed": "Stage Or Review Chant Sura Public Context Inputs",
            "track_id": "second_site_public_context_unblock",
            "source_reports": ["second_site"],
            "dependency_status": public_context_status(second_site_report),
            "why_now": "Prepared-pilot work remains blocked after terrain by deferred public context products.",
            "suggested_command": public_context_command(second_site_report),
            "expected_measurement": "public context blocker group changes from deferred/missing to staged, partial, or explicitly accepted deferred",
            "claim_boundary": "planning/review only unless a separate data-staging task authorizes downloads",
        },
        {
            "rank": 3,
            "task_seed": "Drill Down Extreme-Layer Support/Nodata Sensitivity",
            "track_id": "extreme_layer_support_nodata_drilldown",
            "source_reports": ["fragility", "sensitivity"],
            "dependency_status": sensitivity_report["smoke_status"],
            "why_now": "Max kinetic energy and max jump height are the fragile surfaces with measured gate-target deltas.",
            "suggested_command": "PYENV_VERSION=system uv run python scripts/summarize_extreme_layer_sensitivity_smoke.py --format json",
            "expected_measurement": "separate support/nodata effects from shared-support magnitude effects for the extreme layers",
            "claim_boundary": "diagnostic sensitivity only; no physical credibility or operational threshold claim",
        },
        {
            "rank": 4,
            "task_seed": "Promote Denominator And Deposition Audits Into A Local Interpretation Gate",
            "track_id": "conditional_layer_interpretation_gate",
            "source_reports": ["denominator", "traceability"],
            "dependency_status": build_local_map_interpretation_gate(denominator_report, traceability_report)["gate_status"],
            "why_now": "The denominator and deposition traceability checks are complete and can guard future map interpretation tasks.",
            "suggested_command": "PYENV_VERSION=system uv run python scripts/audit_conditional_denominator_provenance.py --format json && PYENV_VERSION=system uv run python scripts/audit_trajectory_deposition_traceability.py --format json",
            "expected_measurement": "one local gate report names denominator provenance and deposition traceability before map interpretation",
            "claim_boundary": "conditional diagnostics only; no annual frequency, risk, or operational map claim",
        },
        {
            "rank": 5,
            "task_seed": "Wire Holdout And Calibration Separation Into Future Validation Checks",
            "track_id": "holdout_calibration_guardrail_integration",
            "source_reports": ["holdout_split", "calibration_separation"],
            "dependency_status": f"holdout={holdout_report['audit_status']}; calibration={calibration_report['preflight_status']}",
            "why_now": "The split and calibration guardrails now pass locally and should protect future validation changes.",
            "suggested_command": "PYENV_VERSION=system uv run python scripts/audit_chant_sura_holdout_split.py --format json && PYENV_VERSION=system uv run python scripts/check_calibration_separation_preflight.py --format json",
            "expected_measurement": "future validation changes fail closed on split overlap or calibration selected-parameter leakage",
            "claim_boundary": "guardrail only; no calibration, tuning, or external validation claim",
        },
        {
            "rank": 6,
            "task_seed": "Refresh Worker-Facing Scientific State Docs",
            "track_id": "local_scientific_state_doc_refresh",
            "source_reports": ["local_progress", "denominator", "traceability", "fragility", "sensitivity", "second_site", "holdout_split", "calibration_separation"],
            "dependency_status": "all local audit surfaces available",
            "why_now": "The local scientific workflow now has executable entrypoints that should replace broad manual onboarding.",
            "suggested_command": "PYENV_VERSION=system uv run python scripts/recommend_local_scientific_backlog.py --format json",
            "expected_measurement": "docs route workers to the local audit commands and preserve claim boundaries",
            "claim_boundary": "documentation/routing only; no scale-up or claim upgrade",
        },
    ]
    return items


def attach_next_execution_plans(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for item in items:
        command = normalize_repo_command(str(item["suggested_command"]))
        expected_measurement = str(item["expected_measurement"])
        planned_item = dict(item)
        planned_item["suggested_command"] = command
        planned_item["next_executable_command"] = command
        planned_item["expected_artifact_or_measurement"] = expected_measurement
        planned_item["next_execution"] = {
            "command": command,
            "expected_artifact_or_measurement": expected_measurement,
            "local_only": True,
            "repo_checkout_executable": True,
            "placeholder_command": contains_placeholder(command),
            "measurement_required": bool(expected_measurement.strip()),
        }
        planned.append(planned_item)
    return planned


def build_next_command_coverage(items: list[dict[str, Any]]) -> dict[str, Any]:
    missing_command_track_ids = [
        str(item["track_id"])
        for item in items
        if not str(item.get("next_executable_command") or "").strip()
    ]
    placeholder_command_track_ids = [
        str(item["track_id"])
        for item in items
        if item.get("next_execution", {}).get("placeholder_command")
    ]
    missing_measurement_track_ids = [
        str(item["track_id"])
        for item in items
        if not str(item.get("expected_artifact_or_measurement") or "").strip()
    ]
    return {
        "coverage_status": "ready"
        if not missing_command_track_ids and not placeholder_command_track_ids and not missing_measurement_track_ids
        else "blocked_incomplete_next_execution",
        "total_ranked_followups": len(items),
        "entries_with_next_command": len(items) - len(missing_command_track_ids),
        "entries_with_expected_measurement": len(items) - len(missing_measurement_track_ids),
        "missing_command_track_ids": missing_command_track_ids,
        "placeholder_command_track_ids": placeholder_command_track_ids,
        "missing_measurement_track_ids": missing_measurement_track_ids,
    }


def normalize_repo_command(command: str) -> str:
    return command.replace(str(ROOT) + "/", "")


def contains_placeholder(command: str) -> bool:
    return "<" in command or ">" in command or "TODO" in command


def public_context_status(second_site_report: dict[str, Any]) -> str:
    group = next((item for item in second_site_report["blocker_groups"] if item["group_id"] == "public_context_inputs"), {})
    return str(group.get("status") or "unknown")


def public_context_command(second_site_report: dict[str, Any]) -> str:
    group = next((item for item in second_site_report["blocker_groups"] if item["group_id"] == "public_context_inputs"), {})
    return str(group.get("next_local_command") or "PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --format text")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"recommendation_status: {report['recommendation_status']}",
        f"recommended_backlog_size: {report['recommended_backlog_size']}",
        "source_report_statuses:",
    ]
    for key, value in report["source_report_statuses"].items():
        lines.append(f"  {key}: {value}")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    gate = report["local_map_interpretation_gate"]
    lines.append("local_map_interpretation_gate:")
    lines.append(f"  gate_status: {gate['gate_status']}")
    lines.append(f"  denominator_audit_status: {gate['denominator_audit_status']}")
    lines.append(f"  traceability_audit_status: {gate['traceability_audit_status']}")
    lines.append(f"  required_command: {gate['required_command']}")
    if gate["failing_evidence"]:
        lines.append("  failing_evidence:")
        for item in gate["failing_evidence"]:
            lines.append(f"    - {item['audit']}: {item['status']}")
    coverage = report["next_command_coverage"]
    lines.append("next_command_coverage:")
    lines.append(f"  coverage_status: {coverage['coverage_status']}")
    lines.append(f"  entries_with_next_command: {coverage['entries_with_next_command']}")
    lines.append(f"  entries_with_expected_measurement: {coverage['entries_with_expected_measurement']}")
    lines.append("ranked_followups:")
    for item in report["ranked_followups"]:
        lines.append(f"  {item['rank']}. {item['track_id']}: {item['task_seed']}")
        lines.append(f"     dependency_status: {item['dependency_status']}")
        lines.append(f"     next_executable_command: {item['next_executable_command']}")
        lines.append(f"     expected_artifact_or_measurement: {item['expected_artifact_or_measurement']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
