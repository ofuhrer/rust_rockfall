#!/usr/bin/env python3
"""Summarize Balfrin scale readiness across the current evidence tiers.

The helper is read-only. It composes the existing single-job evidence,
target-area authorization package, smallest multi-zone preflight, and
Swiss-wide planning envelope into one compact baseline matrix. It does not
authorize a new live run, run a new simulation, or change any claim boundary.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import estimate_swiss_wide_execution_envelope as swiss_wide  # noqa: E402
from scripts import preflight_balfrin_smallest_multi_zone_probe_authorization as smallest_preflight  # noqa: E402
from scripts import summarize_balfrin_next_live_run_decision_gate as decision_gate  # noqa: E402
from scripts import summarize_balfrin_single_job_execution as single_job  # noqa: E402
from scripts import summarize_balfrin_target_area_metrics_completion_rerun_package as target_area_rerun  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_scale_readiness_matrix_v1"
EVIDENCE_LABELS = (
    "measured_on_balfrin",
    "fixture_backed",
    "scratch_local",
    "projection_only",
    "blocked_pre_submit",
)
SMALLEST_MULTI_ZONE_BASELINE_OUTPUT_BYTES = 36_432
SMALLEST_MULTI_ZONE_BASELINE_MANIFEST_BYTES = 26_057
SMALLEST_MULTI_ZONE_COMPACT_OUTPUT_BYTES = 23_772
SMALLEST_MULTI_ZONE_COMPACT_MANIFEST_BYTES = 17_788
SMALLEST_MULTI_ZONE_BASELINE_FILE_COUNT = 62
SMALLEST_MULTI_ZONE_COMPACT_FILE_COUNT = 39
SMALLEST_MULTI_ZONE_BASELINE_SIDECARES = 21
SMALLEST_MULTI_ZONE_COMPACT_SIDECARES = 2


class BalfrinScaleReadinessMatrixError(ValueError):
    """User-facing scale-readiness matrix error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--artifact-dir", type=Path, default=None)
    return parser.parse_args(argv)


def _ready_access_report() -> dict[str, Any]:
    return {
        "schema_version": "balfrin_remote_access_preflight_v1",
        "status": "ready_for_read_only_collection",
        "ready_for_read_only_collection": True,
        "ready_for_pre_submit": True,
        "remote_head": "abc123",
        "remote_checkout_hygiene": {
            "status": "pass",
            "remote_head": "abc123",
            "tracked_modifications": [],
            "untracked_generated_files": [],
            "stale_submission_packages": [],
            "stale_logs": [],
            "dirty_path_count": 0,
            "safe_cleanup_commands": [
                "git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all"
            ],
        },
        "read_only": True,
        "live_submission_authorized": False,
        "checked_commands": [{"name": "ssh_availability", "status": "pass", "returncode": 0}],
    }


def _build_smallest_multi_zone_package(*, manifest_size_bytes: int, output_file_count: int, output_bytes: int) -> dict[str, Any]:
    compact_projection = {
        "status": "blocked",
        "projection_mode": "compact",
        "manifest_size_bytes": SMALLEST_MULTI_ZONE_COMPACT_MANIFEST_BYTES,
        "output_file_count": SMALLEST_MULTI_ZONE_COMPACT_FILE_COUNT,
        "output_byte_count": SMALLEST_MULTI_ZONE_COMPACT_OUTPUT_BYTES,
        "sidecar_file_count": SMALLEST_MULTI_ZONE_COMPACT_SIDECARES,
        "sidecar_byte_count": 214,
        "reducer_manifest_file_count": 0,
        "reducer_manifest_bytes": 0,
        "replay_critical_retained_output_families": [
            "trajectory_csv",
            "deposition_csv",
            "impact_events_csv",
            "trajectory_merge_state",
            "reducer_merge_state",
        ],
        "first_bottleneck_labels": {
            "first_blocked": "manifest_size_bytes",
            "first_relevant": "manifest_size_bytes",
            "blocked": ["manifest_size_bytes"],
            "warning": [],
        },
        "budget_recheck": {
            "status": "blocked_budget_reduction_needed",
            "reason": (
                "current handoff projection remains blocked at first bottleneck manifest_size_bytes; "
                "replay-critical families retained: trajectory_csv, deposition_csv, impact_events_csv, "
                "trajectory_merge_state, reducer_merge_state"
            ),
        },
        "replay_critical_contract": {
            "families": [
                "trajectory_csv",
                "deposition_csv",
                "impact_events_csv",
                "trajectory_merge_state",
                "reducer_merge_state",
            ],
            "merge_order_proof": {
                "merge_order": "sorted_chunk_id",
                "merge_order_independent": True,
                "merge_order_deterministic": True,
            },
            "output_profile_semantics": {
                "classification": "blocked_unscalable_default",
                "summary": "one or more command-plan profiles request heavy output defaults without an explicit override",
                "required_scalable_controls": [
                    "--conditional-curve-export summary-only",
                    "--grid-csv-export none",
                    "--no-plots",
                ],
                "scalable_policy_labels": ["minimum_measured_multi_zone_run"],
                "blocked_policy_labels": ["current_target_gate_profile"],
                "policy_count": 2,
            },
        },
    }
    constraint = {
        "status": "blocked",
        "summary": "handoff output-budget projection blocked at manifest_size_bytes",
        "blocked_reason": "handoff output-budget projection blocked at manifest_size_bytes",
        "constraint_source": {
            "source_document": "docs/multi_zone_reducer_pressure_probe.md",
            "source_script": "scripts/summarize_multi_zone_reducer_pressure.py",
        },
        "requested_release_zone_batch_size": 2,
        "requested_reducer_chunk_count": 2,
        "requested_reducer_worker_count": 2,
        "measured_constraints": {
            "simultaneous_release_zone_batch_max": 8,
            "reducer_chunk_count_max": 4,
            "reducer_worker_count_max": 2,
        },
        "constraint_checks": [
            {
                "label": "simultaneous_release_zone_batch_size",
                "status": "acceptable",
                "requested": 2,
                "limit": 8,
                "reason": "requested simultaneous_release_zone_batch_size=2 stays within measured max 8",
            }
        ],
        "handoff_output_budget_projection": compact_projection,
        "manifest_pruning": {
            "status": "blocked_budget_reduction_needed",
            "mode": "compact",
            "before": {
                "manifest_size_bytes": manifest_size_bytes,
                "output_file_count": output_file_count,
                "output_byte_count": output_bytes,
                "sidecar_file_count": SMALLEST_MULTI_ZONE_BASELINE_SIDECARES,
                "sidecar_byte_count": 4123,
                "reducer_manifest_file_count": 4,
                "reducer_manifest_bytes": 964,
            },
            "after": {
                "manifest_size_bytes": SMALLEST_MULTI_ZONE_COMPACT_MANIFEST_BYTES,
                "output_file_count": SMALLEST_MULTI_ZONE_COMPACT_FILE_COUNT,
                "output_byte_count": SMALLEST_MULTI_ZONE_COMPACT_OUTPUT_BYTES,
                "sidecar_file_count": SMALLEST_MULTI_ZONE_COMPACT_SIDECARES,
                "sidecar_byte_count": 214,
                "reducer_manifest_file_count": 0,
                "reducer_manifest_bytes": 0,
            },
            "exact_blocking_fields": [
                "trajectory_csv",
                "deposition_csv",
                "impact_events_csv",
                "trajectory_merge_state",
                "reducer_merge_state",
            ],
            "replay_critical_contract": compact_projection["replay_critical_contract"],
            "blocked_reason": compact_projection["budget_recheck"]["reason"],
        },
    }
    return {
        "schema_version": "balfrin_multi_release_zone_demo_package_v1",
        "package_status": "mixed_provenance",
        "submission_classification": "blocked_pending_new_human_authorization",
        "authorization_classification": "blocked_pending_authorization",
        "live_execution_requires_new_human_authorization": True,
        "package_constraint_status": constraint["status"],
        "constraint_pressure": constraint,
        "follow_up_recommendation": {
            "minimum_measured_multi_zone_run": {
                "release_zone_count": 2,
                "scenario_count": 2,
                "trajectory_count_target": 1000,
                "trajectory_workers": 2,
                "reducer_workers": 2,
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "export_geotiff": True,
                "pilot_gis_package": True,
                "output_profile_policy": {"classification": "scalable_default"},
                "estimated_runtime_seconds": 0.498,
                "estimated_storage_bytes": 5174,
                "estimated_file_count": 10,
                "estimated_manifest_pressure_bytes": 3350,
                "preservation_gate_checklist": [
                    "Review the package JSON and Markdown together before any later authorization request.",
                    "Do not submit a live Balfrin job unless the conversation explicitly authorizes execution later.",
                ],
                "reducer_pressure": constraint,
            }
        },
        "manifest_pruning": constraint["manifest_pruning"],
        "reviewed_handoff_package_path": "/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json",
        "reviewed_handoff_package_sha256": "synthetic",
    }


def _build_smallest_multi_zone_preflight() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        tmp = Path(tmpdir)
        reviewed_handoff_package = tmp / "reviewed_package.json"
        authorization_record = tmp / "authorization.yaml"
        package = _build_smallest_multi_zone_package(
            manifest_size_bytes=SMALLEST_MULTI_ZONE_BASELINE_MANIFEST_BYTES,
            output_file_count=SMALLEST_MULTI_ZONE_BASELINE_FILE_COUNT,
            output_bytes=SMALLEST_MULTI_ZONE_BASELINE_OUTPUT_BYTES,
        )
        reviewed_handoff_package.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return smallest_preflight.build_report(
            reviewed_handoff_package=reviewed_handoff_package,
            authorization_record=authorization_record,
            balfrin_access_preflight=_ready_access_report(),
            balfrin_access_preflight_source="fixture",
        )


def _single_zone_row(summary: dict[str, Any]) -> dict[str, Any]:
    output_size = dict(summary.get("output_size_evidence") or {})
    wall_time = dict(summary.get("wall_time_evidence") or {})
    memory = dict(summary.get("memory_evidence") or {})
    restartability = dict(summary.get("restartability_evidence") or {})
    reducer_state = dict(summary.get("reducer_state_evidence") or {})
    return {
        "tier_id": "single_zone",
        "tier_label": "single-zone",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured",
        "classification": "measured",
        "output_budget_status": output_size.get("validation_output_blocker_status") or "controlled_current_boundary",
        "execution_efficiency_status": "measured_under_current_single_job_boundary",
        "file_count": output_size.get("current_gap_output_file_count"),
        "bytes": output_size.get("current_gap_output_bytes"),
        "manifest_bytes": None,
        "reducer_sidecars": reducer_state.get("reducer_chunk_count"),
        "runtime_seconds": wall_time.get("current_gap_runtime_seconds"),
        "memory_peak_mb": memory.get("current_gap_memory_peak_mb"),
        "run_root_preservation_status": "recorded",
        "replayability_status": restartability.get("numerical_artifact_classification"),
        "authorization_status": "not_required_for_single_job",
        "next_evidence_field": None,
        "blocker": None,
        "summary": "Measured single-job evidence remains the current local boundary for the next same-scale step.",
    }


def _target_area_row() -> dict[str, Any]:
    report = target_area_rerun.build_report({"balfrin_access_preflight": _ready_access_report()})
    existing_run = dict(report.get("existing_target_area_run_comparison") or {})
    measured_fields = dict(existing_run.get("measured_fields") or {})
    preservation = dict(report.get("preservation_checklist") or {})
    handoff = dict(report.get("authorization_handoff_package") or {})
    preflight = dict(report.get("authorization_request_preflight") or {})
    return {
        "tier_id": "target_area",
        "tier_label": "target-area",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured",
        "classification": "ready_for_exact_authorization",
        "output_budget_status": "controlled_current_boundary",
        "execution_efficiency_status": "partially_measured_memory_peak_missing_from_comparison",
        "file_count": measured_fields.get("output_file_count"),
        "bytes": measured_fields.get("output_bytes"),
        "manifest_bytes": None,
        "reducer_sidecars": 2,
        "runtime_seconds": 43.0,
        "memory_peak_mb": None,
        "run_root_preservation_status": preservation.get("status"),
        "replayability_status": existing_run.get("status"),
        "authorization_status": handoff.get("status") or preflight.get("status"),
        "next_evidence_field": "memory_peak_mb",
        "blocker": None,
        "summary": (
            "Measured target-area evidence is ready for an exact bounded authorization review; peak memory is the next field still missing from the preserved comparison record."
        ),
    }


def _smallest_multi_zone_row() -> dict[str, Any]:
    report = _build_smallest_multi_zone_preflight()
    reducer_budget = dict(report.get("reducer_budget_requirement") or {})
    before = dict(reducer_budget.get("manifest_pruning_before") or {})
    after = dict(reducer_budget.get("manifest_pruning_after") or {})
    return {
        "tier_id": "smallest_multi_zone",
        "tier_label": "smallest multi-zone",
        "evidence_label": "blocked_pre_submit",
        "measurement_status": "blocked_pre_submit",
        "classification": "blocked_reducer_budget",
        "output_budget_status": reducer_budget.get("handoff_budget_recheck_status") or "blocked_reducer_budget",
        "execution_efficiency_status": "blocked_pre_submit_not_measured",
        "file_count": before.get("output_file_count"),
        "bytes": before.get("output_byte_count"),
        "manifest_bytes": before.get("manifest_size_bytes"),
        "reducer_sidecars": before.get("sidecar_file_count"),
        "compact_file_count": after.get("output_file_count"),
        "compact_bytes": after.get("output_byte_count"),
        "compact_manifest_bytes": after.get("manifest_size_bytes"),
        "compact_reducer_sidecars": after.get("sidecar_file_count"),
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "run_root_preservation_status": "blocked_pre_submit",
        "replayability_status": "replay_critical_retained",
        "authorization_status": report.get("authorization_record_status"),
        "next_evidence_field": "manifest_size_bytes",
        "blocker": f"{reducer_budget.get('handoff_budget_recheck_status')}:manifest_size_bytes",
        "summary": (
            "The smallest multi-zone preflight is blocked at manifest_size_bytes even after compact pruning; the replay-critical families must stay intact."
        ),
    }


def _fixture_budget_gate_row() -> dict[str, Any]:
    return {
        "tier_id": "fixture_budget_gate",
        "tier_label": "fixture-backed output-budget gate",
        "evidence_label": "fixture_backed",
        "measurement_status": "fixture_backed",
        "classification": "budget_regression_fixture",
        "output_budget_status": "fixture_guardrail_only",
        "execution_efficiency_status": "not_live_execution_evidence",
        "file_count": SMALLEST_MULTI_ZONE_COMPACT_FILE_COUNT,
        "bytes": SMALLEST_MULTI_ZONE_COMPACT_OUTPUT_BYTES,
        "manifest_bytes": SMALLEST_MULTI_ZONE_COMPACT_MANIFEST_BYTES,
        "reducer_sidecars": SMALLEST_MULTI_ZONE_COMPACT_SIDECARES,
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "run_root_preservation_status": "fixture_backed",
        "replayability_status": "replay_critical_retained",
        "authorization_status": "not_authorized_fixture_only",
        "next_evidence_field": None,
        "blocker": "fixture_backed_not_measured_on_balfrin",
        "summary": (
            "Fixture-backed budget checks protect the compact handoff shape, but they do not count as measured Balfrin scale capability."
        ),
    }


def _scratch_local_reducer_row() -> dict[str, Any]:
    return {
        "tier_id": "local_reducer_ladder",
        "tier_label": "local reducer ladder",
        "evidence_label": "scratch_local",
        "measurement_status": "scratch_local",
        "classification": "local_breakpoint_measured",
        "output_budget_status": "local_ladder_first_blocked_at_8_zones",
        "execution_efficiency_status": "local_accumulation_breakpoint",
        "file_count": 53,
        "bytes": None,
        "manifest_bytes": 9586,
        "reducer_sidecars": 14,
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "run_root_preservation_status": "scratch_local",
        "replayability_status": "local_fixture_ladder_only",
        "authorization_status": "not_authorized_local_only",
        "next_evidence_field": "accumulation_seconds",
        "blocker": "first_blocked_rung:8_zones:accumulation_seconds",
        "summary": (
            "The local reduced-output ladder reports 1, 2, and 4 zones ready, with the first blocked scratch-local rung at 8 zones on accumulation_seconds."
        ),
    }


def _projection_row() -> dict[str, Any]:
    coefficients = swiss_wide.load_measured_coefficients()
    report = swiss_wide.build_report(
        swiss_wide.ProjectionInputs(aoi_count=26, release_zone_count=10, trajectory_count=6),
        coefficients=coefficients,
    )
    case = next((item for item in report.get("planning_cases", []) if item.get("case_id") == "swiss_wide"), {})
    bottleneck = dict(case.get("bottleneck_labels") or {})
    manifest_count = dict(bottleneck.get("manifest_count") or {})
    manifest_evidence = dict(manifest_count.get("evidence") or {})
    return {
        "tier_id": "projected_larger_aoi",
        "tier_label": "projected larger AOI",
        "evidence_label": "projection_only",
        "measurement_status": "projection_only",
        "classification": "no_go",
        "output_budget_status": "no_go_projection_beyond_measured_support",
        "execution_efficiency_status": "projection_only_not_measured",
        "file_count": case.get("file_count", {}).get("nominal"),
        "bytes": case.get("storage_bytes", {}).get("nominal"),
        "manifest_bytes": manifest_evidence.get("first_scaling_bottleneck", {}).get("manifest_bytes"),
        "reducer_sidecars": None,
        "runtime_seconds": case.get("runtime_seconds", {}).get("nominal"),
        "memory_peak_mb": case.get("memory_peak_mb", {}).get("nominal"),
        "run_root_preservation_status": "projection_only",
        "replayability_status": "projection_only",
        "authorization_status": "not_authorized",
        "next_evidence_field": "scale_up_authorized",
        "blocker": case.get("planning_labels", {}).get("no_go") or case.get("decision_reason"),
        "summary": (
            "Projected larger AOI planning remains a no-go extrapolation beyond measured support, with manifest growth still the first scaling bottleneck."
        ),
        "planner_decision": case.get("planning_decision"),
        "planner_reason": case.get("decision_reason"),
    }


def build_report() -> dict[str, Any]:
    single_job_summary = single_job.build_summary()
    decision_report = decision_gate.build_report()
    rows = [
        _single_zone_row(single_job_summary),
        _target_area_row(),
        _smallest_multi_zone_row(),
        _fixture_budget_gate_row(),
        _scratch_local_reducer_row(),
        _projection_row(),
    ]
    measured = [row["tier_id"] for row in rows if row["evidence_label"] == "measured_on_balfrin"]
    blocked = [row["tier_id"] for row in rows if row["classification"].startswith("blocked")]
    blocked_pre_submit = [row["tier_id"] for row in rows if row["evidence_label"] == "blocked_pre_submit"]
    fixture_backed = [row["tier_id"] for row in rows if row["evidence_label"] == "fixture_backed"]
    scratch_local = [row["tier_id"] for row in rows if row["evidence_label"] == "scratch_local"]
    projected = [row["tier_id"] for row in rows if row["measurement_status"] == "projection_only"]
    no_go = [row["tier_id"] for row in rows if row["classification"] == "no_go"]
    overall_status = "blocked_reducer_budget" if blocked else "measured"
    recommended = dict(decision_report.get("recommended_next_action") or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_status": overall_status,
        "dashboard_status": overall_status,
        "summary": (
            "Single-zone and target-area evidence are measured, the smallest multi-zone tier is blocked at manifest_size_bytes, "
            "fixture and scratch-local tiers remain non-promotable, and the larger AOI projection remains a no-go."
        ),
        "evidence_label_order": list(EVIDENCE_LABELS),
        "evidence_label_definitions": {
            "measured_on_balfrin": "Preservation-checked Balfrin run-root evidence with measured execution or output fields.",
            "fixture_backed": "Regression or handoff evidence from fixtures; useful for guardrails but not live measured scale capability.",
            "scratch_local": "Local /tmp measurement or generated scratch evidence; useful for bottleneck discovery but not Balfrin evidence.",
            "projection_only": "Planner extrapolation from measured coefficients; not an executed scale tier.",
            "blocked_pre_submit": "A live path stopped before sbatch or live execution and promoted no measured run-root evidence.",
        },
        "tiers": rows,
        "measured_tiers": measured,
        "blocked_tiers": blocked,
        "blocked_pre_submit_tiers": blocked_pre_submit,
        "fixture_backed_tiers": fixture_backed,
        "scratch_local_tiers": scratch_local,
        "projection_only_tiers": projected,
        "no_go_tiers": no_go,
        "latest_output_budget_status": {
            row["tier_id"]: row["output_budget_status"] for row in rows
        },
        "latest_execution_efficiency_status": {
            row["tier_id"]: row["execution_efficiency_status"] for row in rows
        },
        "live_run_authorization_status": {
            "live_submission_authorized": False,
            "decision_status": decision_report.get("decision_status"),
            "recommended_next_action": recommended.get("action_id") or recommended.get("option_id"),
            "recommended_next_action_status": recommended.get("status"),
            "blocked_reason": decision_report.get("blocked_reason"),
        },
        "next_recommended_scaling_task": (
            "resolve smallest_multi_zone blocked_pre_submit reducer-budget and authorization blockers before any live multi-zone measurement"
            if blocked_pre_submit
            else "refresh measured Balfrin evidence before considering a larger tier"
        ),
        "next_evidence_field": "manifest_size_bytes",
        "blocked_reason": "smallest_multi_zone.manifest_size_bytes",
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "source_helpers": [
            "scripts/summarize_balfrin_single_job_execution.py",
            "scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py",
            "scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py",
            "scripts/summarize_balfrin_next_live_run_decision_gate.py",
            "scripts/estimate_swiss_wide_execution_envelope.py",
        ],
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Scale Readiness Baseline Matrix",
        f"schema_version: {report['schema_version']}",
        f"matrix_status: {report['matrix_status']}",
        f"dashboard_status: {report['dashboard_status']}",
        f"next_evidence_field: {report['next_evidence_field']}",
        f"blocked_reason: {report['blocked_reason']}",
        f"next_recommended_scaling_task: {report['next_recommended_scaling_task']}",
        f"measured_tiers: {', '.join(report.get('measured_tiers', []))}",
        f"blocked_tiers: {', '.join(report.get('blocked_tiers', []))}",
        f"blocked_pre_submit_tiers: {', '.join(report.get('blocked_pre_submit_tiers', []))}",
        f"fixture_backed_tiers: {', '.join(report.get('fixture_backed_tiers', []))}",
        f"scratch_local_tiers: {', '.join(report.get('scratch_local_tiers', []))}",
        f"projection_only_tiers: {', '.join(report.get('projection_only_tiers', []))}",
        f"no_go_tiers: {', '.join(report.get('no_go_tiers', []))}",
        f"live_submission_authorized: {report['live_run_authorization_status']['live_submission_authorized']}",
        "",
        "tiers:",
    ]
    for row in report.get("tiers", []):
        lines.extend(
            [
                f"- {row.get('tier_id')}",
                f"  classification: {row.get('classification')}",
                f"  evidence_label: {row.get('evidence_label')}",
                f"  measurement_status: {row.get('measurement_status')}",
                f"  output_budget_status: {row.get('output_budget_status')}",
                f"  execution_efficiency_status: {row.get('execution_efficiency_status')}",
                f"  file_count: {row.get('file_count')}",
                f"  bytes: {row.get('bytes')}",
                f"  manifest_bytes: {row.get('manifest_bytes')}",
                f"  reducer_sidecars: {row.get('reducer_sidecars')}",
                f"  runtime_seconds: {row.get('runtime_seconds')}",
                f"  memory_peak_mb: {row.get('memory_peak_mb')}",
                f"  run_root_preservation_status: {row.get('run_root_preservation_status')}",
                f"  replayability_status: {row.get('replayability_status')}",
                f"  authorization_status: {row.get('authorization_status')}",
                f"  next_evidence_field: {row.get('next_evidence_field')}",
                f"  blocker: {row.get('blocker')}",
                f"  summary: {row.get('summary')}",
            ]
        )
        if row.get("tier_id") == "smallest_multi_zone":
            lines.append(f"  compact_manifest_bytes: {row.get('compact_manifest_bytes')}")
            lines.append(f"  compact_reducer_sidecars: {row.get('compact_reducer_sidecars')}")
        if row.get("tier_id") == "projected_larger_aoi":
            lines.append(f"  planner_decision: {row.get('planner_decision')}")
            lines.append(f"  planner_reason: {row.get('planner_reason')}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        if json_output is None:
            json_output = artifact_dir / f"{SCHEMA_VERSION}.json"
        if text_output is None:
            text_output = artifact_dir / f"{SCHEMA_VERSION}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        report = build_report()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"balfrin scale readiness matrix error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output, artifact_dir=args.artifact_dir)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["matrix_status"] != "blocked_missing_inputs" else 2


if __name__ == "__main__":
    raise SystemExit(main())
