#!/usr/bin/env python3
"""Summarize the Balfrin demonstration closure package.

This helper is a fail-closed synthesis layer. It combines the current Balfrin
management package with the metrics-completion rerun package, the
multi-release-zone handoff, the preservation gate, and a new-measured-evidence
gate so reviewers can answer whether the evidence is ready to be extended
toward larger Swiss workflows without rereading the repository.

The package only upgrades when a new preservation-checked measured evidence
record is present. Otherwise it stays blocked and labels the mixed provenance
explicitly.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as multi_zone_handoff
from scripts import summarize_balfrin_management_demo_package as management
from scripts import summarize_balfrin_evidence_bundle as evidence_bundle
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate
from scripts import summarize_balfrin_next_live_run_decision_gate as next_live_decision
from scripts import summarize_balfrin_target_area_metrics_completion_rerun_package as metrics_rerun


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_demonstration_closure_package_v1"
REPORT_BASENAME = "balfrin_demonstration_closure_package_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_demonstration_closure_package_v1"
DEFAULT_MANAGEMENT_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_PRESERVATION_RUN_ROOT = DEFAULT_MANAGEMENT_RUN_ROOT
DEFAULT_MANAGEMENT_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "management_demo_package_v1"
DEFAULT_METRICS_RERUN_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "metrics_completion_rerun_package_v1"
DEFAULT_MULTI_ZONE_ARTIFACT_DIR = Path("/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1")

METRICS_COMPLETE = "metrics_complete"
METRICS_UNRECOVERABLE_DEFERRED = "metrics_unrecoverable_deferred"
METRICS_INCOMPLETE = "metrics_incomplete"
BLOCKED_NO_NEW_MEASURED_EVIDENCE = "blocked_no_new_measured_evidence"
DEFAULT_METRICS_COMPLETION_SOURCE = "blocked_missing_metrics"
DEFAULT_SPATIAL_ARTIFACT_STATUS = "not_evaluated_in_closure_refresh"
DEFAULT_NEXT_ACTION_STATUS = "blocked"

SECTION_NAMES = (
    "runtime_section",
    "replay_section",
    "preservation_section",
    "restartability_section",
    "reducer_output_scaling_section",
    "aoi_release_scenario_automation_section",
    "gis_readiness_section",
    "second_site_portability_section",
    "scientific_claim_boundaries_section",
    "metrics_completion_rerun_section",
    "metrics_closure_section",
    "target_area_spatial_artifact_section",
    "next_measured_action_section",
    "new_measured_evidence_section",
)

ALLOWED_EVIDENCE_TYPES = {
    "measured",
    "fixture_backed",
    "dry_run",
    "blocked",
    "unavailable",
    "unauthorized",
    "historical",
}

ALLOWED_MEASURED_EVIDENCE_SOURCES = {
    "metrics_completion_rerun",
    "authorized_multi_zone_probe",
}


class BalfrinDemonstrationClosurePackageError(ValueError):
    """User-facing closure-package error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--evidence-json", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            evidence_override=load_evidence_override(args.evidence_json),
            artifact_dir=args.artifact_dir,
        )
    except BalfrinDemonstrationClosurePackageError as exc:
        print(f"balfrin demonstration closure package error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report.get("closure_status") == METRICS_COMPLETE else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinDemonstrationClosurePackageError(f"evidence override file is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BalfrinDemonstrationClosurePackageError("evidence override must be a JSON object")
    return payload


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    if evidence_override is not None and isinstance(evidence_override.get("closure_report"), dict):
        return dict(evidence_override["closure_report"])

    if evidence_override is not None and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", []) if str(item)]
        return blocked_report(
            missing_inputs,
            reason="required closure-package inputs are missing",
            artifact_dir=artifact_dir,
        )

    report = build_current_report(artifact_dir=artifact_dir)
    if evidence_override is None:
        return report

    apply_overrides(report, evidence_override)
    finalize_report(report)
    return report


def build_current_report(*, artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> dict[str, Any]:
    management_report = management.build_report(
        run_root=DEFAULT_MANAGEMENT_RUN_ROOT,
        artifact_dir=DEFAULT_MANAGEMENT_ARTIFACT_DIR,
    )
    preservation_report = preservation_gate.build_report(run_root=DEFAULT_PRESERVATION_RUN_ROOT)
    metrics_rerun_report = metrics_rerun.build_report()
    multi_zone_report = multi_zone_handoff.build_report(
        artifact_dir=DEFAULT_MULTI_ZONE_ARTIFACT_DIR,
    )
    metrics_closure_section = build_metrics_closure_section(
        status=BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        metrics_completion_source=DEFAULT_METRICS_COMPLETION_SOURCE,
        metrics_contract_status=str(metrics_rerun_report.get("package_status") or "blocked_missing_inputs"),
        summary=(
            "No new measured or recovered target-area metrics were supplied, so the closure package remains blocked."
        ),
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "closure_status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        "closure_provenance_status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        "maturity_label_update_allowed": False,
        "reviewer_answer": build_reviewer_answer(BLOCKED_NO_NEW_MEASURED_EVIDENCE),
        "package_summary": {
            "status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
            "summary": (
                "No new measured or recovered target-area metrics are present, so the closure package remains blocked."
            ),
            "section_counts": {},
        },
        "runtime_section": annotate_section(management_report["runtime_section"], "measured"),
        "replay_section": annotate_section(management_report["replay_section"], "fixture_backed"),
        "preservation_section": annotate_section(
            preservation_report,
            "measured" if preservation_report.get("gate_status") == "ready_for_demonstration_evidence" else "blocked",
            status=str(preservation_report.get("gate_status") or "blocked_missing_inputs"),
        ),
        "restartability_section": annotate_section(management_report["restartability_section"], "measured"),
        "reducer_output_scaling_section": annotate_section(management_report["scaling_section"], "measured"),
        "aoi_release_scenario_automation_section": build_aoi_release_scenario_automation_section(management_report),
        "gis_readiness_section": annotate_section(management_report["gis_scope_section"], "measured"),
        "second_site_portability_section": build_second_site_portability_section(multi_zone_report),
        "scientific_claim_boundaries_section": build_scientific_claim_boundaries_section(management_report),
        "metrics_completion_rerun_section": build_metrics_completion_rerun_section(metrics_rerun_report),
        "metrics_closure_section": metrics_closure_section,
        "target_area_spatial_artifact_section": build_target_area_spatial_artifact_section(),
        "multi_zone_balfrin_evidence_section": evidence_bundle.build_multi_zone_balfrin_evidence(),
        "next_measured_action_section": build_next_measured_action_section(metrics_closure_section),
        "new_measured_evidence_section": build_new_measured_evidence_section(metrics_closure_section),
        "claim_boundaries": dict(management_report.get("claim_boundaries") or {}),
        "source_artifacts": build_source_artifacts(artifact_dir),
        "regeneration_commands": build_regeneration_commands(artifact_dir),
    }
    finalize_report(report)
    return report


def annotate_section(section: dict[str, Any], evidence_type: str, *, status: str | None = None) -> dict[str, Any]:
    payload = copy.deepcopy(section)
    payload["evidence_type"] = evidence_type
    if status is not None:
        payload["status"] = status
    return payload


def build_aoi_release_scenario_automation_section(management_report: dict[str, Any]) -> dict[str, Any]:
    section = {
        "status": str(management_report["target_area_aoi_automation_section"].get("status") or "blocked_missing_inputs"),
        "release_scenario_status": str(
            management_report["target_area_release_scenario_section"].get("status") or "blocked_missing_inputs"
        ),
        "summary": (
            "AOI and release/scenario automation stay dry-run or template-only until a new preservation-checked "
            "measured evidence record exists."
        ),
        "source_paths": [
            *collect_source_paths(management_report["target_area_aoi_automation_section"]),
            *collect_source_paths(management_report["target_area_release_scenario_section"]),
        ],
    }
    return annotate_section(section, "dry_run")


def build_second_site_portability_section(multi_zone_report: dict[str, Any]) -> dict[str, Any]:
    follow_up = dict(multi_zone_report.get("follow_up_recommendation") or {})
    pressure = dict(multi_zone_report.get("pressure_checkpoints") or {})
    section = {
        "status": str(follow_up.get("authorization_classification") or "blocked_pending_authorization"),
        "package_status": str(multi_zone_report.get("package_status") or "blocked_missing_inputs"),
        "summary": (
            "Second-site portability remains unauthorized until the reviewed multi-zone path is backed by new "
            "preservation-checked measured evidence."
        ),
        "authorization_classification": follow_up.get("authorization_classification"),
        "authorization_review_command": follow_up.get("authorization_review_command"),
        "authorization_submit_command": follow_up.get("authorization_submit_command"),
        "pressure_status": pressure.get("output_pressure", {}).get("status"),
        "source_paths": collect_source_paths(multi_zone_report),
    }
    return annotate_section(section, "unauthorized")


def build_scientific_claim_boundaries_section(management_report: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = dict(management_report.get("claim_boundaries") or {})
    swiss_wide = dict(management_report.get("swiss_wide_extension_section") or {})
    section = {
        "status": "historical_boundary",
        "summary": (
            "Scientific claim boundaries are historical guardrails: the package stays non-operational, non-risk, "
            "non-annual-frequency, and non-scale-up regardless of the closure status."
        ),
        "answer": swiss_wide.get("answer"),
        "claim_boundaries": claim_boundaries,
        "source_paths": [
            "docs/balfrin_single_job_execution_sufficiency.md",
            "docs/current_maturity_snapshot.md",
            "scripts/estimate_swiss_wide_execution_envelope.py",
        ],
    }
    return annotate_section(section, "historical", status="historical_boundary")


def build_metrics_completion_rerun_section(metrics_rerun_report: dict[str, Any]) -> dict[str, Any]:
    section = {
        "status": str(metrics_rerun_report.get("package_status") or "blocked_missing_inputs"),
        "summary": (
            "The metrics-completion rerun package is a dry-run plan until a measured rerun result is supplied."
        ),
        "preservation_checklist_status": metrics_rerun_report.get("preservation_checklist", {}).get("status"),
        "existing_target_area_run_comparison": metrics_rerun_report.get("existing_target_area_run_comparison", {}),
        "source_paths": [
            *collect_source_paths(metrics_rerun_report.get("rerun_command_plan", {})),
            *collect_source_paths(metrics_rerun_report.get("preservation_checklist", {})),
        ],
    }
    return annotate_section(section, "dry_run")


def build_metrics_closure_section(
    *,
    status: str = BLOCKED_NO_NEW_MEASURED_EVIDENCE,
    metrics_completion_source: str = DEFAULT_METRICS_COMPLETION_SOURCE,
    metrics_completion_outcome: str | None = None,
    metrics_completion_attempt_status: str | None = None,
    metrics_contract_status: str = "blocked_missing_inputs",
    summary: str | None = None,
    source_paths: list[str] | None = None,
    metrics_evidence_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = str(status or BLOCKED_NO_NEW_MEASURED_EVIDENCE)
    if summary is None:
        if status == METRICS_COMPLETE:
            summary = (
                "Target-area metrics are complete and can support a closure refresh, while spatial artifacts stay separate."
            )
        elif status == METRICS_UNRECOVERABLE_DEFERRED:
            summary = (
                "Target-area metrics remain unrecovered but explicitly deferred, so the closure refresh can rank the next measured action without fabricating missing evidence."
            )
        elif status == METRICS_INCOMPLETE:
            summary = (
                "The metrics-completion attempt is incomplete: no preservation-checked measured run-root evidence was supplied."
            )
        else:
            summary = (
                "No new measured or recovered target-area metrics were supplied, so the closure package remains blocked."
            )
    section = {
        "status": status,
        "metrics_completion_source": metrics_completion_source,
        "metrics_completion_outcome": metrics_completion_outcome or (
            "measured"
            if status == METRICS_COMPLETE and metrics_completion_source == "new_metrics_completion_rerun"
            else "recovered"
            if status == METRICS_COMPLETE and metrics_completion_source == "recovered_existing_run_root"
            else "incomplete"
            if status == METRICS_INCOMPLETE
            else "blocked"
        ),
        "metrics_completion_attempt_status": metrics_completion_attempt_status,
        "metrics_contract_status": metrics_contract_status,
        "metrics_evidence_state": dict(metrics_evidence_state or {}),
        "summary": summary,
        "source_paths": list(source_paths or []),
    }
    evidence_type = "measured" if status == METRICS_COMPLETE else "unavailable" if status == METRICS_UNRECOVERABLE_DEFERRED else "blocked"
    return annotate_section(section, evidence_type)


def build_target_area_spatial_artifact_section(spatial_artifact_report: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(spatial_artifact_report, dict):
        section = {
            "status": DEFAULT_SPATIAL_ARTIFACT_STATUS,
            "recovery_status": "not_supplied",
            "spatial_artifact_classification": "not_required_for_execution_metrics_closure",
            "summary": (
                "TB-243 spatial-artifact classification is kept separate from execution-metrics closure; no spatial recovery report was supplied to this synthesis helper."
            ),
            "status_counts": {},
            "recovered_artifacts": [],
            "unrecovered_artifacts": [],
            "execution_metrics_closure_separation": {
                "status": "separated_from_spatial_artifacts",
                "spatial_artifact_classification": "not_required_for_execution_metrics_closure",
            },
            "spatial_interpretation_evidence": {
                "status": DEFAULT_SPATIAL_ARTIFACT_STATUS,
                "usable_as_target_area_spatial_interpretation_evidence": False,
                "unrecovered_artifacts": [],
                "physical_validation_evidence_status": "not_established",
                "usable_as_physical_validation_evidence": False,
                "summary": "Spatial artifacts were not supplied to the closure refresh.",
            },
            "source_paths": [
                "docs/balfrin_single_job_execution_sufficiency.md",
                "scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py",
            ],
        }
        return annotate_section(section, "unavailable")

    recovery = dict(spatial_artifact_report.get("spatial_artifact_recovery") or spatial_artifact_report)
    separation = dict(spatial_artifact_report.get("execution_metrics_closure_separation") or {})
    interpretation = dict(spatial_artifact_report.get("spatial_interpretation_evidence") or {})
    status = str(spatial_artifact_report.get("report_status") or recovery.get("status") or interpretation.get("status") or "unknown")
    section = {
        "status": status,
        "recovery_status": str(recovery.get("status") or status),
        "spatial_artifact_classification": str(
            separation.get("spatial_artifact_classification") or "not_required_for_execution_metrics_closure"
        ),
        "summary": str(
            spatial_artifact_report.get("summary")
            or interpretation.get("summary")
            or "Target-area spatial-artifact classification remains separate from execution-metrics closure."
        ),
        "status_counts": dict(recovery.get("status_counts") or {}),
        "recovered_artifacts": list(recovery.get("recovered_artifacts") or []),
        "unrecovered_artifacts": list(recovery.get("unrecovered_artifacts") or interpretation.get("unrecovered_artifacts") or []),
        "execution_metrics_closure_separation": separation or {
            "status": "separated_from_spatial_artifacts",
            "spatial_artifact_classification": "not_required_for_execution_metrics_closure",
        },
        "spatial_interpretation_evidence": interpretation or {
            "status": status,
            "usable_as_target_area_spatial_interpretation_evidence": False,
            "unrecovered_artifacts": list(recovery.get("unrecovered_artifacts") or []),
            "physical_validation_evidence_status": "not_established",
            "usable_as_physical_validation_evidence": False,
            "summary": "Spatial artifacts remain explicit deferrals and are not physical validation evidence.",
        },
        "source_paths": collect_source_paths(spatial_artifact_report),
    }
    evidence_type = "measured" if status == "spatial_artifacts_recovered" else "unavailable"
    return annotate_section(section, evidence_type)


def build_next_measured_action_section(
    metrics_closure_section: dict[str, Any],
    decision_gate_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    closure_status = str(metrics_closure_section.get("status") or BLOCKED_NO_NEW_MEASURED_EVIDENCE)
    if closure_status in {BLOCKED_NO_NEW_MEASURED_EVIDENCE, METRICS_INCOMPLETE}:
        section = {
            "status": DEFAULT_NEXT_ACTION_STATUS,
            "metrics_closure_status": closure_status,
            "summary": (
                "No next measured-action recommendation is available until target-area metrics are complete or explicitly deferred."
            ),
            "ranked_actions": [],
            "recommended_next_action": {},
            "selected_action_id": None,
            "source_paths": [
                "scripts/summarize_balfrin_next_live_run_decision_gate.py",
                "docs/balfrin_single_job_execution_sufficiency.md",
            ],
        }
        return annotate_section(section, "blocked")

    decision_gate_report = dict(decision_gate_report or {})
    option_assessments = dict(decision_gate_report.get("option_assessments") or {})
    ranked_actions = _build_closure_ranked_actions(option_assessments)
    selected_action = next(
        (action for action in ranked_actions if action.get("status") in {"ready", "defer"}),
        ranked_actions[0] if ranked_actions else {},
    )
    selected_action_id = str(selected_action.get("action_id") or "") or None
    selected_action_status = str(selected_action.get("status") or "blocked")
    section = {
        "status": "ready" if selected_action_id else "blocked",
        "metrics_closure_status": closure_status,
        "summary": _summarize_next_measured_action(closure_status, selected_action, ranked_actions),
        "ranked_actions": ranked_actions,
        "recommended_next_action": selected_action,
        "selected_action_id": selected_action_id,
        "decision_gate_status": str(decision_gate_report.get("decision_status") or "unknown"),
        "source_paths": [
            "scripts/summarize_balfrin_next_live_run_decision_gate.py",
            "docs/balfrin_single_job_execution_sufficiency.md",
        ],
    }
    return annotate_section(section, "dry_run", status=selected_action_status if selected_action_id else "blocked")


def build_new_measured_evidence_section(metrics_closure_section: dict[str, Any]) -> dict[str, Any]:
    closure_status = str(metrics_closure_section.get("status") or BLOCKED_NO_NEW_MEASURED_EVIDENCE)
    if closure_status == METRICS_COMPLETE:
        metrics_completion_source = str(metrics_closure_section.get("metrics_completion_source") or DEFAULT_METRICS_COMPLETION_SOURCE)
        source_type = (
            metrics_completion_source
            if metrics_completion_source in ALLOWED_MEASURED_EVIDENCE_SOURCES
            else "metrics_completion_rerun"
        )
        section = {
            "status": "measured",
            "source_type": source_type,
            "preservation_checked": True,
            "preservation_gate_status": "ready_for_demonstration_evidence",
            "authorization_status": "authorized",
            "summary": (
                "A preservation-checked measured metrics-completion record is present, so the closure refresh can proceed."
            ),
            "source_paths": [
                "scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py",
                "docs/balfrin_single_job_execution_sufficiency.md",
            ],
        }
        section["closure_input_compatibility"] = evaluate_new_measured_evidence_compatibility(section)
        return annotate_section(section, "measured")
    if closure_status == METRICS_UNRECOVERABLE_DEFERRED:
        section = {
            "status": "unavailable",
            "source_type": None,
            "preservation_checked": False,
            "preservation_gate_status": "not_applicable",
            "authorization_status": "not_applicable",
            "summary": (
                "Metrics are explicitly unrecoverable and deferred, so no preservation-checked measured evidence record is being claimed."
            ),
            "source_paths": [
                "docs/current_maturity_snapshot.md",
                "docs/balfrin_single_job_execution_sufficiency.md",
            ],
        }
        section["closure_input_compatibility"] = evaluate_new_measured_evidence_compatibility(
            {
                **section,
                "evidence_type": "unavailable",
            }
        )
        return annotate_section(section, "unavailable")
    if closure_status == METRICS_INCOMPLETE:
        section = {
            "status": METRICS_INCOMPLETE,
            "source_type": None,
            "preservation_checked": False,
            "preservation_gate_status": METRICS_INCOMPLETE,
            "authorization_status": "blocked_before_submission",
            "summary": (
                "The metrics-completion attempt stopped before live submission, so no measured evidence record is present."
            ),
            "source_paths": [
                "docs/agent_work_log.md",
                "scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py",
            ],
        }
        section["closure_input_compatibility"] = evaluate_new_measured_evidence_compatibility(section)
        return annotate_section(section, "blocked")
    section = {
        "status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        "source_type": None,
        "preservation_checked": False,
        "preservation_gate_status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        "authorization_status": BLOCKED_NO_NEW_MEASURED_EVIDENCE,
        "summary": (
            "No new preservation-checked measured evidence from a metrics-completion rerun or authorized multi-zone probe is present."
        ),
        "source_paths": [],
    }
    section["closure_input_compatibility"] = evaluate_new_measured_evidence_compatibility(section)
    return annotate_section(section, "blocked")


def _build_closure_ranked_actions(option_assessments: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, action_id in enumerate(
        (
            next_live_decision.OPTION_MULTI_ZONE,
            next_live_decision.OPTION_PHYSICAL_EVIDENCE,
            next_live_decision.OPTION_SECOND_SITE,
            next_live_decision.OPTION_DEFER,
        ),
        start=1,
    ):
        option = dict(option_assessments.get(action_id) or {})
        rows.append(
            {
                "rank": rank,
                "action_id": action_id,
                "status": option.get("status", "blocked"),
                "path_state": option.get("path_state", "blocked"),
                "follow_up_task": option.get("follow_up_task", "unknown"),
                "summary": option.get("summary", ""),
                "exact_evidence_blockers": list(option.get("exact_evidence_blockers") or []),
                "boundary_that_prevents_claim_upgrade": option.get("boundary_that_prevents_claim_upgrade", ""),
            }
        )
    return rows


def _summarize_next_measured_action(
    closure_status: str,
    selected_action: dict[str, Any],
    ranked_actions: list[dict[str, Any]],
) -> str:
    if not selected_action:
        return "No next measured-action recommendation is available."
    action_label = str(selected_action.get("action_id") or "unknown").replace("_", " ")
    if closure_status == METRICS_COMPLETE:
        return (
            f"Target-area metrics are complete, so the next ranked measured action is {action_label} "
            f"(rank {selected_action.get('rank', '?')})."
        )
    if closure_status == METRICS_UNRECOVERABLE_DEFERRED:
        return (
            f"Target-area metrics are explicitly deferred, so the next ranked measured action is {action_label} "
            f"(rank {selected_action.get('rank', '?')})."
        )
    return "No next measured-action recommendation is available until metrics are complete or explicitly deferred."


def collect_source_paths(value: Any) -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for item in value.values():
            paths.extend(collect_source_paths(item))
        return paths
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    if isinstance(value, str) and value:
        return [value]
    return []


def build_source_artifacts(artifact_dir: Path) -> dict[str, Any]:
    return {
        "closure_artifact_dir": str(artifact_dir),
        "management_artifact_dir": str(artifact_dir / "management_demo_package_v1"),
        "metrics_completion_rerun_artifact_dir": str(artifact_dir / "metrics_completion_rerun_package_v1"),
        "next_live_run_decision_gate_artifact_dir": str(artifact_dir / "next_live_run_decision_gate_v1"),
        "target_area_spatial_artifact_recovery_artifact_dir": str(artifact_dir / "target_area_spatial_artifact_recovery_v1"),
        "multi_zone_handoff_artifact_dir": str(DEFAULT_MULTI_ZONE_ARTIFACT_DIR),
        "preservation_gate_run_root": str(DEFAULT_PRESERVATION_RUN_ROOT),
        "management_run_root": str(DEFAULT_MANAGEMENT_RUN_ROOT),
    }


def build_regeneration_commands(artifact_dir: Path) -> list[str]:
    return [
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py "
        f"--run-root {DEFAULT_PRESERVATION_RUN_ROOT} --artifact-dir {artifact_dir / 'preservation_gate_v1'}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py "
        f"--artifact-dir {artifact_dir / 'metrics_completion_rerun_package_v1'}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_next_live_run_decision_gate.py "
        f"--artifact-dir {artifact_dir / 'next_live_run_decision_gate_v1'}",
        "PYENV_VERSION=system uv run python scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py "
        f"--balfrin-access-json /tmp/balfrin_access_preflight.json --format json --artifact-dir {artifact_dir / 'target_area_spatial_artifact_recovery_v1'}",
        "PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py "
        f"--artifact-dir {DEFAULT_MULTI_ZONE_ARTIFACT_DIR}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py "
        f"--run-root {DEFAULT_MANAGEMENT_RUN_ROOT} --artifact-dir {artifact_dir / 'management_demo_package_v1'}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_closure_package.py "
        f"--artifact-dir {artifact_dir}",
    ]


def apply_overrides(report: dict[str, Any], evidence_override: dict[str, Any]) -> None:
    section_overrides = evidence_override.get("section_overrides")
    if isinstance(section_overrides, dict):
        for section_name, override in section_overrides.items():
            if section_name not in report or not isinstance(report[section_name], dict) or not isinstance(override, dict):
                continue
            report[section_name].update(copy.deepcopy(override))

    if isinstance(evidence_override.get("new_measured_evidence"), dict):
        report["new_measured_evidence_section"].update(copy.deepcopy(evidence_override["new_measured_evidence"]))
    if isinstance(evidence_override.get("preservation_section"), dict):
        report["preservation_section"].update(copy.deepcopy(evidence_override["preservation_section"]))
    enforce_new_measured_evidence_compatibility(report["new_measured_evidence_section"])


def evaluate_new_measured_evidence_compatibility(section: dict[str, Any]) -> dict[str, Any]:
    source_type = str(section.get("source_type") or "")
    evidence_type = str(section.get("evidence_type") or "")
    status = str(section.get("status") or "")
    preservation_gate_status = str(section.get("preservation_gate_status") or "")
    authorization_status = str(section.get("authorization_status") or "")
    missing_fields: list[str] = []

    if source_type not in ALLOWED_MEASURED_EVIDENCE_SOURCES:
        missing_fields.append("new_measured_evidence.source_type")
    if status != "measured":
        missing_fields.append("new_measured_evidence.status=measured")
    if evidence_type != "measured":
        missing_fields.append("new_measured_evidence.evidence_type=measured")
    if section.get("preservation_checked") is not True:
        missing_fields.append("new_measured_evidence.preservation_checked=true")
    if preservation_gate_status != "ready_for_demonstration_evidence":
        missing_fields.append("new_measured_evidence.preservation_gate_status=ready_for_demonstration_evidence")
    if authorization_status not in {"authorized", "authorized_for_one_bounded_probe"}:
        missing_fields.append("new_measured_evidence.authorization_status")

    return {
        "schema_version": "balfrin_closure_new_measured_evidence_input_compatibility_v1",
        "status": "compatible" if not missing_fields else "blocked_missing_inputs",
        "allowed_source_types": sorted(ALLOWED_MEASURED_EVIDENCE_SOURCES),
        "source_type": source_type or None,
        "missing_fields": missing_fields,
        "preserves_fixture_backed_boundary": evidence_type != "fixture_backed" or bool(missing_fields),
        "summary": (
            "New measured evidence input is compatible with closure-package semantics."
            if not missing_fields
            else "New measured evidence input is blocked; closure requires measured provenance, preservation gate readiness, and authorization."
        ),
    }


def enforce_new_measured_evidence_compatibility(section: dict[str, Any]) -> None:
    compatibility = evaluate_new_measured_evidence_compatibility(section)
    section["closure_input_compatibility"] = compatibility
    if compatibility["status"] == "compatible":
        return
    section["status"] = str(section.get("status") or "blocked_missing_inputs")
    section["evidence_type"] = "blocked"
    section["preservation_checked"] = bool(section.get("preservation_checked", False))


def finalize_report(report: dict[str, Any]) -> None:
    profile = build_section_provenance_profile(report)
    report["section_provenance_profile"] = profile
    report["package_summary"]["section_counts"] = section_provenance_counts(profile)
    report["closure_status"] = derive_closure_status(report)
    report["closure_provenance_status"] = report["closure_status"]
    report["maturity_label_update_allowed"] = report["closure_status"] == METRICS_COMPLETE
    report["reviewer_answer"] = build_reviewer_answer(report["closure_status"])
    report["package_summary"]["status"] = report["closure_status"]
    report["package_summary"]["summary"] = summarize_package(report)


def build_section_provenance_profile(report: dict[str, Any]) -> list[dict[str, Any]]:
    profile: list[dict[str, Any]] = []
    for section_name in SECTION_NAMES:
        section = dict(report.get(section_name) or {})
        profile.append(
            {
                "section": section_name,
                "status": str(section.get("status") or "blocked_missing_inputs"),
                "evidence_type": classify_evidence_type(section),
                "source_paths": collect_source_paths(section.get("source_paths")),
            }
        )
    return profile


def classify_evidence_type(section: dict[str, Any]) -> str:
    evidence_type = str(section.get("evidence_type") or "").strip()
    if evidence_type in ALLOWED_EVIDENCE_TYPES:
        return evidence_type
    status = str(section.get("status") or "").strip()
    if status.startswith("blocked") or status in {"missing", "blocked"}:
        return "blocked"
    if status in {METRICS_UNRECOVERABLE_DEFERRED, DEFAULT_SPATIAL_ARTIFACT_STATUS, "deferred_missing_spatial_artifacts"}:
        return "unavailable"
    if status in {METRICS_COMPLETE, "complete_measured_closure"} or status.startswith("measured"):
        return "measured"
    if "fixture" in status:
        return "fixture_backed"
    if "unauthor" in status:
        return "unauthorized"
    if "defer" in status:
        return "unavailable"
    if "template_only" in status or "dry_run" in status or "rerun" in status:
        return "dry_run"
    if "historical" in status:
        return "historical"
    source_paths = collect_source_paths(section.get("source_paths"))
    if any(path.startswith("docs/") for path in source_paths):
        return "historical"
    if any("tests/fixtures" in path for path in source_paths):
        return "fixture_backed"
    return "measured"


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in ALLOWED_EVIDENCE_TYPES}
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type in counts:
            counts[evidence_type] += 1
        else:
            counts["blocked"] += 1
    return counts


def derive_closure_status(report: dict[str, Any]) -> str:
    metrics_section = dict(report.get("metrics_closure_section") or {})
    status = str(metrics_section.get("status") or BLOCKED_NO_NEW_MEASURED_EVIDENCE)
    if status in {METRICS_COMPLETE, METRICS_UNRECOVERABLE_DEFERRED, METRICS_INCOMPLETE, BLOCKED_NO_NEW_MEASURED_EVIDENCE}:
        return status
    return BLOCKED_NO_NEW_MEASURED_EVIDENCE


def build_reviewer_answer(closure_status: str) -> str:
    if closure_status == METRICS_COMPLETE:
        return (
            "Yes. The target-area metrics are complete enough to support a closure refresh, and the package keeps spatial-artifact classification separate from execution-metrics closure."
        )
    if closure_status == METRICS_UNRECOVERABLE_DEFERRED:
        return (
            "Not yet. The target-area metrics are explicitly unrecoverable and deferred, so the closure refresh can rank the next measured action but cannot upgrade maturity labels."
        )
    if closure_status == METRICS_INCOMPLETE:
        return (
            "No. The metrics-completion attempt is incomplete because no live job, run-root metrics, sacct fields, or preservation-gate output were promoted."
        )
    if closure_status == BLOCKED_NO_NEW_MEASURED_EVIDENCE:
        return (
            "No. The package fails closed because there is no new measured or recovered target-area metrics record, so it cannot claim a completion refresh."
        )
    return "No. Required closure-package inputs are missing."


def summarize_package(report: dict[str, Any]) -> str:
    closure_status = str(report.get("closure_status") or "blocked_missing_inputs")
    counts = report.get("package_summary", {}).get("section_counts", {})
    measured = counts.get("measured", 0) if isinstance(counts, dict) else 0
    blocked = counts.get("blocked", 0) if isinstance(counts, dict) else 0
    metrics_section = dict(report.get("metrics_closure_section") or {})
    spatial_section = dict(report.get("target_area_spatial_artifact_section") or {})
    next_action = dict(report.get("next_measured_action_section") or {})
    if closure_status == METRICS_COMPLETE:
        return (
            f"Target-area metrics are complete across {measured} measured sections; spatial artifacts stay separate ({spatial_section.get('status', 'unknown')}), and the next measured action is {next_action.get('selected_action_id', 'unknown')}."
        )
    if closure_status == METRICS_UNRECOVERABLE_DEFERRED:
        return (
            f"Target-area metrics are explicitly unrecoverable and deferred; {measured} sections are measured, {blocked} remain blocked, spatial artifacts stay separate ({spatial_section.get('status', 'unknown')}), and the next measured action is {next_action.get('selected_action_id', 'unknown')}."
        )
    if closure_status == METRICS_INCOMPLETE:
        return (
            f"Target-area metrics completion is incomplete; {measured} sections are measured, {blocked} remain blocked, and no next measured action is promoted."
        )
    if closure_status == BLOCKED_NO_NEW_MEASURED_EVIDENCE:
        return (
            "No new measured or recovered target-area metrics have been supplied, so the closure package fails closed."
        )
    return "The closure package is blocked because required inputs are missing."


def blocked_report(missing_inputs: list[str], *, reason: str, artifact_dir: Path) -> dict[str, Any]:
    report = {
        "schema_version": SCHEMA_VERSION,
        "closure_status": "blocked_missing_inputs",
        "closure_provenance_status": "blocked_missing_inputs",
        "maturity_label_update_allowed": False,
        "reviewer_answer": "No. Required closure-package inputs are missing.",
        "package_summary": {
            "status": "blocked_missing_inputs",
            "summary": reason,
            "section_counts": {label: 0 for label in ALLOWED_EVIDENCE_TYPES},
        },
        "runtime_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "replay_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "preservation_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "restartability_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "reducer_output_scaling_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "aoi_release_scenario_automation_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "gis_readiness_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "second_site_portability_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "scientific_claim_boundaries_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "metrics_completion_rerun_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "metrics_closure_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "target_area_spatial_artifact_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "next_measured_action_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "new_measured_evidence_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "section_provenance_profile": [
            {
                "section": section_name,
                "status": "blocked_missing_inputs",
                "evidence_type": "blocked",
                "source_paths": [],
            }
            for section_name in SECTION_NAMES
        ],
        "missing_inputs": list(missing_inputs),
        "source_artifacts": build_source_artifacts(artifact_dir),
        "regeneration_commands": build_regeneration_commands(artifact_dir),
    }
    return report


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(str(report.get("source_artifacts", {}).get("closure_artifact_dir") or DEFAULT_ARTIFACT_DIR))
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or artifact_dir / f"{REPORT_BASENAME}.json"
        text_output = text_output or artifact_dir / f"{REPORT_BASENAME}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Demonstration Closure Package",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"closure_status: {report.get('closure_status', 'unknown')}",
        f"closure_provenance_status: {report.get('closure_provenance_status', 'unknown')}",
        f"maturity_label_update_allowed: {report.get('maturity_label_update_allowed', False)}",
        f"reviewer_answer: {report.get('reviewer_answer', '')}",
        f"summary: {report.get('package_summary', {}).get('summary', '')}",
        "",
        "section_provenance_profile:",
    ]
    for section in report.get("section_provenance_profile", []):
        lines.append(
            f"  - {section.get('section')}: {section.get('status')} "
            f"[{section.get('evidence_type')}]"
        )
    lines.extend(["", "claim_boundaries:"])
    for key, value in sorted((report.get("claim_boundaries") or {}).items()):
        lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "metrics_closure_section:",
            f"  status: {report.get('metrics_closure_section', {}).get('status', 'unknown')}",
            f"  metrics_completion_source: {report.get('metrics_closure_section', {}).get('metrics_completion_source', 'unknown')}",
            f"  metrics_completion_outcome: {report.get('metrics_closure_section', {}).get('metrics_completion_outcome', 'unknown')}",
            f"  metrics_completion_attempt_status: {report.get('metrics_closure_section', {}).get('metrics_completion_attempt_status', 'unknown')}",
            f"  metrics_contract_status: {report.get('metrics_closure_section', {}).get('metrics_contract_status', 'unknown')}",
            "target_area_spatial_artifact_section:",
            f"  status: {report.get('target_area_spatial_artifact_section', {}).get('status', 'unknown')}",
            f"  recovery_status: {report.get('target_area_spatial_artifact_section', {}).get('recovery_status', 'unknown')}",
            f"  spatial_artifact_classification: {report.get('target_area_spatial_artifact_section', {}).get('spatial_artifact_classification', 'unknown')}",
            "multi_zone_balfrin_evidence_section:",
            f"  status: {report.get('multi_zone_balfrin_evidence_section', {}).get('status', 'unknown')}",
            f"  evidence_type: {report.get('multi_zone_balfrin_evidence_section', {}).get('evidence_type', 'unknown')}",
            f"  first_bottleneck_label: {report.get('multi_zone_balfrin_evidence_section', {}).get('first_bottleneck_label', 'unknown')}",
            "next_measured_action_section:",
            f"  status: {report.get('next_measured_action_section', {}).get('status', 'unknown')}",
            f"  selected_action_id: {report.get('next_measured_action_section', {}).get('selected_action_id', 'unknown')}",
            f"  summary: {report.get('next_measured_action_section', {}).get('summary', '')}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
