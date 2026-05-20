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
from scripts import execute_management_aoi_balfrin_run as management_aoi_execution  # noqa: E402
from scripts import generate_balfrin_multi_release_zone_demo_handoff as handoff  # noqa: E402
from scripts import preflight_balfrin_smallest_multi_zone_probe_authorization as smallest_preflight  # noqa: E402
from scripts import summarize_balfrin_next_live_run_decision_gate as decision_gate  # noqa: E402
from scripts import summarize_balfrin_single_job_execution as single_job  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_scale_readiness_matrix_v1"
EVIDENCE_LABELS = (
    "measured_on_balfrin",
    "measured_on_balfrin_postproc_microbenchmark",
    "fixture_backed",
    "scratch_local",
    "projection_only",
    "blocked_pre_submit",
    "partial",
    "failed_closed",
)
TB305_POSTPROC_MICROBENCHMARK = {
    "job_id": "4339870",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin_postproc_microbenchmark_v1/tb305_20260519T190459Z",
    "wall_seconds": 0.6338623960000405,
    "cpu_seconds": 0.048968283,
    "peak_rss_kb": 32624,
    "files_touched": 154,
    "bytes_touched": 89802,
    "file_scan_seconds": 0.1271800529975735,
    "manifest_scan_seconds": 0.2482742709980812,
    "reducer_merge_seconds": 0.17694826799925067,
    "package_seconds": 0.08144542599984561,
}
TB307_TARGET_AREA_METRICS_COMPLETION = {
    "job_id": "4339889",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v1",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:29",
    "alloc_cpus": 16,
    "batch_max_rss_kb": 5568,
    "memory_peak_mb": 5.4375,
    "validation_output_file_count": 130,
    "validation_output_bytes": 34565498,
    "hazard_output_file_count": 99,
    "hazard_output_bytes": 273194249,
    "preservation_status": "ready_for_demonstration_evidence",
    "metrics_completion_source": "new_metrics_completion_rerun",
}
TB312_FOUR_ZONE_POSTPROC_PROBE = {
    "job_id": "4340075",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/tb312_four_zone_postproc_probe_v1/tb312_20260519T224500Z",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:11",
    "alloc_cpus": 16,
    "batch_max_rss_kb": 5460,
    "memory_peak_mb": 5.33203125,
    "wall_seconds": 1.63,
    "output_file_count": 25,
    "output_bytes": 10238,
    "manifest_bytes": 12220,
    "sidecar_file_count": 10,
    "reducer_chunk_count": 2,
    "trajectory_decision_counts": {"executed": 4},
    "reducer_decision_counts": {"executed": 2},
    "preservation_status": "ready_for_demonstration_evidence",
    "output_budget_status": "accepted",
}
TB332_FOUR_ZONE_HAZARD_PROBE_GATE = {
    "preflight_status": "blocked_missing_authorization",
    "authorization_status": "blocked_missing_inputs",
    "blocked_reason": "authorization record reviewed-handoff checksum does not match",
    "reviewed_handoff_package_sha256": "5b36191cf79d0f234ef862391b23be85a364a72dc784889fa231c91e21dc950d",
    "authorization_record_sha256": "a92371d0117f39ba5657480090d8173a9cc50808174afa38101c1c80e4291fe4",
    "authorization_record_reviewed_handoff_sha256": "8e0a01fd787f941775c51ef7ade12cf18ab370796f6b518be0fd1dd9b5d6e808",
    "balfrin_access_status": "ready_for_read_only_collection",
    "remote_checkout_hygiene_status": "pass",
    "remote_head": "20cc865756f1f5afb5c5e19b2a042e94553afd3a",
    "review_readiness_status": "ready_for_review",
    "output_budget_status": "accepted",
    "submit_contract_status": "ready",
    "reducer_budget_status": "ready",
    "output_profile_status": "ready",
    "release_zone_count": 4,
    "scenario_count": 4,
    "trajectory_count_target": 2000,
    "expected_runtime_seconds": 0.997,
    "expected_storage_bytes": 10635,
    "expected_manifest_pressure_bytes": 7104,
    "expected_file_count": 21,
    "reviewed_handoff_package_path": "/private/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json",
    "authorization_record_path": "/private/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml",
    "source_report": "docs/balfrin_four_zone_hazard_probe_tb332.md",
}
TB333_FOUR_ZONE_HAZARD_NEXT_ACTION = "defer_eight_zone_probe_until_measured_hazard_execution"
TB362_TWO_ZONE_HAZARD_FAILED_CLOSED = {
    "task_id": "TB-362",
    "remote_head": "8b94c12d6d1fa89a4928e15b243805b19600d31b",
    "preflight_status": "blocked_reducer_budget",
    "ready_for_authorized_submission": False,
    "authorization_status": "authorized",
    "reducer_budget_status": "ready",
    "submit_contract_status": "ready",
    "output_budget_acceptance_status": "accepted",
    "output_profile_status": "blocked_output_profile",
    "blocked_reason": "single-job sufficiency or reducer scaling is not yet ready for the four-zone review package",
    "slurm_job_id": None,
    "run_root": None,
    "artifact_count": 7,
    "artifact_bytes": 1_362_459,
    "source_report": "docs/balfrin_two_zone_hazard_run_tb362.md",
}
TB368_TWO_ZONE_HAZARD_PRESERVED = {
    "task_id": "TB-368",
    "job_id": "4344114",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:41",
    "alloc_cpus": 16,
    "batch_max_rss_kb": 39372,
    "memory_peak_mb": 172.921875,
    "collector_wall_seconds": 6.570337791999918,
    "hazard_output_file_count": 53,
    "hazard_output_bytes": 55_829_693,
    "preservation_status": "ready_for_demonstration_evidence",
    "metrics_contract_status": "complete",
    "required_run_root_entries_status": "complete",
    "output_family_status": "sufficient",
    "missing_metrics": [],
    "missing_run_root_entries": [],
    "missing_output_families": [],
    "source_report": "docs/balfrin_two_zone_hazard_run_tb368.md",
}
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
        "standing_postproc_clearance_active": True,
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
    return {
        "tier_id": "target_area",
        "tier_label": "target-area",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured",
        "classification": "measured_metrics_completion",
        "output_budget_status": "controlled_current_boundary",
        "execution_efficiency_status": "target_area_metrics_complete",
        "metrics_completion_source": TB307_TARGET_AREA_METRICS_COMPLETION["metrics_completion_source"],
        "file_count": TB307_TARGET_AREA_METRICS_COMPLETION["validation_output_file_count"],
        "bytes": TB307_TARGET_AREA_METRICS_COMPLETION["validation_output_bytes"],
        "hazard_output_file_count": TB307_TARGET_AREA_METRICS_COMPLETION["hazard_output_file_count"],
        "hazard_output_bytes": TB307_TARGET_AREA_METRICS_COMPLETION["hazard_output_bytes"],
        "manifest_bytes": None,
        "reducer_sidecars": 2,
        "runtime_seconds": 29.0,
        "memory_peak_mb": TB307_TARGET_AREA_METRICS_COMPLETION["memory_peak_mb"],
        "run_root_preservation_status": TB307_TARGET_AREA_METRICS_COMPLETION["preservation_status"],
        "replayability_status": "measured_metrics_completion_rerun_preserved",
        "authorization_status": "authorized_for_one_metrics_completion_rerun",
        "next_evidence_field": None,
        "blocker": None,
        "slurm": {
            "job_id": TB307_TARGET_AREA_METRICS_COMPLETION["job_id"],
            "state": TB307_TARGET_AREA_METRICS_COMPLETION["slurm_state"],
            "exit_code": TB307_TARGET_AREA_METRICS_COMPLETION["exit_code"],
            "elapsed": TB307_TARGET_AREA_METRICS_COMPLETION["elapsed"],
            "alloc_cpus": TB307_TARGET_AREA_METRICS_COMPLETION["alloc_cpus"],
            "batch_max_rss_kb": TB307_TARGET_AREA_METRICS_COMPLETION["batch_max_rss_kb"],
        },
        "run_root": TB307_TARGET_AREA_METRICS_COMPLETION["run_root"],
        "summary": (
            "TB-307 completed the target-area metrics-completion rerun on Balfrin postproc; peak memory and split validation/hazard output metrics are measured and preserved."
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


def _four_zone_review_package_row() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
        report = handoff.build_report(artifact_dir=artifact_dir)

    review = dict(report.get("review_only_four_zone_package") or {})
    constraint = dict(review.get("constraint_pressure") or {})
    return {
        "tier_id": "four_zone_review_package",
        "tier_label": "four-zone postproc probe",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_postproc_probe",
        "classification": "measured_postproc_probe",
        "output_budget_status": TB312_FOUR_ZONE_POSTPROC_PROBE["output_budget_status"],
        "execution_efficiency_status": "four_zone_postproc_measured",
        "hazard_execution_status": "no_hazard_execution",
        "file_count": TB312_FOUR_ZONE_POSTPROC_PROBE["output_file_count"],
        "bytes": TB312_FOUR_ZONE_POSTPROC_PROBE["output_bytes"],
        "manifest_bytes": TB312_FOUR_ZONE_POSTPROC_PROBE["manifest_bytes"],
        "reducer_sidecars": TB312_FOUR_ZONE_POSTPROC_PROBE["sidecar_file_count"],
        "runtime_seconds": TB312_FOUR_ZONE_POSTPROC_PROBE["wall_seconds"],
        "memory_peak_mb": TB312_FOUR_ZONE_POSTPROC_PROBE["memory_peak_mb"],
        "run_root_preservation_status": TB312_FOUR_ZONE_POSTPROC_PROBE["preservation_status"],
        "replayability_status": "replay_critical_retained",
        "authorization_status": "standing_postproc_clearance_used",
        "next_evidence_field": None,
        "blocker": None,
        "summary": (
            "TB-312 measured the exact four-zone compact post-processing/reducer package on Balfrin postproc; "
            "this is not a hazard execution or scale-up claim."
        ),
        "job_id": TB312_FOUR_ZONE_POSTPROC_PROBE["job_id"],
        "run_root": TB312_FOUR_ZONE_POSTPROC_PROBE["run_root"],
        "slurm": {
            "job_id": TB312_FOUR_ZONE_POSTPROC_PROBE["job_id"],
            "state": TB312_FOUR_ZONE_POSTPROC_PROBE["slurm_state"],
            "exit_code": TB312_FOUR_ZONE_POSTPROC_PROBE["exit_code"],
            "elapsed": TB312_FOUR_ZONE_POSTPROC_PROBE["elapsed"],
            "alloc_cpus": TB312_FOUR_ZONE_POSTPROC_PROBE["alloc_cpus"],
            "batch_max_rss_kb": TB312_FOUR_ZONE_POSTPROC_PROBE["batch_max_rss_kb"],
        },
        "trajectory_decision_counts": TB312_FOUR_ZONE_POSTPROC_PROBE["trajectory_decision_counts"],
        "reducer_decision_counts": TB312_FOUR_ZONE_POSTPROC_PROBE["reducer_decision_counts"],
        "review_readiness_status": review.get("readiness_classification"),
        "review_readiness_reason": review.get("readiness_reason"),
        "output_profile_policy": review.get("output_profile_policy", {}),
        "output_budget_acceptance_threshold_profile_id": review.get("output_budget_acceptance_threshold_profile_id"),
        "output_budget_acceptance_validation": review.get("output_budget_acceptance_validation", {}),
        "manifest_pruning_status": review.get("manifest_pruning_status"),
        "promotion_status": "measured_by_tb312",
        "promotion_reason": "TB-312 explicitly authorized and measured this exact postproc package under standing postproc clearance.",
        "constraint_status": constraint.get("status"),
    }


def _four_zone_hazard_probe_blocked_row() -> dict[str, Any]:
    gate = TB332_FOUR_ZONE_HAZARD_PROBE_GATE
    return {
        "tier_id": "four_zone_hazard_probe",
        "tier_label": "four-zone hazard probe",
        "evidence_label": "blocked_pre_submit",
        "measurement_status": "blocked_pre_submit",
        "classification": "blocked_pre_submit_authorization_record_checksum",
        "output_budget_status": gate["output_budget_status"],
        "output_pressure_status": gate["output_budget_status"],
        "execution_efficiency_status": "blocked_pre_submit_not_measured",
        "hazard_execution_status": "blocked_pre_submit_no_hazard_execution",
        "file_count": gate["expected_file_count"],
        "bytes": gate["expected_storage_bytes"],
        "manifest_bytes": gate["expected_manifest_pressure_bytes"],
        "reducer_sidecars": None,
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "run_root_preservation_status": "blocked_pre_submit",
        "replayability_status": "not_measured",
        "authorization_status": gate["authorization_status"],
        "next_evidence_field": "authorization_record.reviewed_handoff_package_sha256",
        "next_recommended_action": TB333_FOUR_ZONE_HAZARD_NEXT_ACTION,
        "next_recommended_action_reason": (
            "TB-332 failed closed before hazard execution, so the four-zone branch stays deferred in blocked_pre_submit "
            "and does not justify an eight-zone probe or a hazard-builder optimization yet."
        ),
        "blocker": gate["blocked_reason"],
        "summary": (
            "TB-332 failed closed before sbatch: the four-zone hazard package, access, submit-contract, reducer-budget, "
            "and output-profile gates were otherwise ready, but the live authorization record referenced a stale reviewed "
            "handoff checksum. The branch therefore stays deferred for any eight-zone follow-on."
        ),
        "preflight_status": gate["preflight_status"],
        "balfrin_access_status": gate["balfrin_access_status"],
        "remote_checkout_hygiene_status": gate["remote_checkout_hygiene_status"],
        "remote_head": gate["remote_head"],
        "review_readiness_status": gate["review_readiness_status"],
        "submit_contract_status": gate["submit_contract_status"],
        "reducer_budget_status": gate["reducer_budget_status"],
        "output_profile_status": gate["output_profile_status"],
        "release_zone_count": gate["release_zone_count"],
        "scenario_count": gate["scenario_count"],
        "trajectory_count_target": gate["trajectory_count_target"],
        "expected_runtime_seconds": gate["expected_runtime_seconds"],
        "reviewed_handoff_package_path": gate["reviewed_handoff_package_path"],
        "reviewed_handoff_package_sha256": gate["reviewed_handoff_package_sha256"],
        "authorization_record_path": gate["authorization_record_path"],
        "authorization_record_sha256": gate["authorization_record_sha256"],
        "authorization_record_reviewed_handoff_sha256": gate["authorization_record_reviewed_handoff_sha256"],
        "source_report": gate["source_report"],
    }


def _two_zone_preserved_row() -> dict[str, Any]:
    gate = TB368_TWO_ZONE_HAZARD_PRESERVED
    return {
        "tier_id": "two_zone_preserved_hazard_run",
        "tier_label": "two-zone hazard run",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_preservation_ready",
        "classification": "measured_two_zone_preservation_ready",
        "output_budget_status": "accepted",
        "output_pressure_status": "accepted",
        "execution_efficiency_status": "measured_preservation_ready",
        "hazard_execution_status": "measured_two_zone_hazard_execution",
        "file_count": gate["hazard_output_file_count"],
        "bytes": gate["hazard_output_bytes"],
        "validation_output_file_count": None,
        "validation_output_bytes": None,
        "hazard_output_file_count": gate["hazard_output_file_count"],
        "hazard_output_bytes": gate["hazard_output_bytes"],
        "manifest_bytes": None,
        "reducer_sidecars": None,
        "runtime_seconds": gate["collector_wall_seconds"],
        "memory_peak_mb": gate["memory_peak_mb"],
        "run_root_preservation_status": gate["preservation_status"],
        "replayability_status": "preservation_gate_ready",
        "authorization_status": "authorized_for_one_bounded_probe",
        "next_evidence_field": None,
        "blocker": None,
        "metrics_contract_status": gate["metrics_contract_status"],
        "required_run_root_entries_status": gate["required_run_root_entries_status"],
        "output_family_status": gate["output_family_status"],
        "missing_metrics": gate["missing_metrics"],
        "missing_run_root_entries": gate["missing_run_root_entries"],
        "missing_output_families": gate["missing_output_families"],
        "slurm_job_id": gate["job_id"],
        "job_id": gate["job_id"],
        "run_root": gate["run_root"],
        "slurm": {
            "job_id": gate["job_id"],
            "state": gate["slurm_state"],
            "exit_code": gate["exit_code"],
            "elapsed": gate["elapsed"],
            "alloc_cpus": gate["alloc_cpus"],
            "batch_max_rss_kb": gate["batch_max_rss_kb"],
        },
        "supersedes_failed_closed_task": TB362_TWO_ZONE_HAZARD_FAILED_CLOSED["task_id"],
        "superseded_failed_closed_source_report": TB362_TWO_ZONE_HAZARD_FAILED_CLOSED["source_report"],
        "source_report": gate["source_report"],
        "summary": (
            "TB-368 completed one bounded postproc rerun and the preserved two-zone run root satisfies the preservation gate; "
            "this supersedes the older TB-362 failed-closed branch for four-zone handoff decisions."
        ),
    }


def _management_aoi_failed_closed_row() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        report = management_aoi_execution.build_report(
            artifact_dir=Path(tmpdir) / "management_aoi_execution_state",
            handoff_artifact_dir=Path(tmpdir) / "management_aoi_handoff",
            prepared_pilot_output_root=Path(tmpdir) / "management_aoi_prepared_pilot",
        )

    blocker = dict(report.get("first_persistent_blocker") or {})
    candidate = dict(report.get("candidate_evidence") or {})
    scenario = dict(report.get("scenario_generation_pressure") or {})
    return {
        "tier_id": "management_aoi_multi_zone_run",
        "tier_label": "management-AOI multi-zone Balfrin run",
        "evidence_label": "failed_closed",
        "measurement_status": "failed_closed_no_submission",
        "classification": report["execution_status"],
        "output_budget_status": "not_evaluated",
        "output_pressure_status": "not_evaluated",
        "execution_efficiency_status": "not_measured_no_submission",
        "hazard_execution_status": "failed_closed_no_hazard_execution",
        "file_count": None,
        "bytes": None,
        "validation_output_file_count": None,
        "validation_output_bytes": None,
        "hazard_output_file_count": None,
        "hazard_output_bytes": None,
        "manifest_bytes": None,
        "reducer_sidecars": None,
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "run_root_preservation_status": "fail_closed_no_run_root_created",
        "replayability_status": "blocked_missing_prepared_pilot_inputs",
        "authorization_status": "not_submitted_handoff_not_ready",
        "next_evidence_field": "non_empty_management_aoi_candidate_set",
        "blocker": blocker.get("status"),
        "summary": (
            "TB-381 failed closed before sbatch because TB-380 classified the management-AOI handoff as "
            "blocked_missing_prepared_pilot_inputs; the preserved first blocker is the empty candidate set and "
            "zero scenario rows."
        ),
        "handoff_classification": report.get("handoff_classification"),
        "first_persistent_blocker": blocker,
        "candidate_cell_count": candidate.get("candidate_cell_count"),
        "candidate_area_m2": candidate.get("candidate_area_m2"),
        "scenario_pressure_status": scenario.get("scenario_pressure_status"),
        "scenario_row_count": scenario.get("scenario_row_count"),
        "sbatch_attempted": dict(report.get("no_submit_semantics") or {}).get("sbatch_attempted"),
        "scheduler_submission_status": dict(report.get("no_submit_semantics") or {}).get(
            "scheduler_submission_status"
        ),
        "source_helper": "scripts/execute_management_aoi_balfrin_run.py",
    }


def _postproc_microbenchmark_row() -> dict[str, Any]:
    return {
        "tier_id": "postproc_microbenchmark",
        "tier_label": "TB-305 postproc microbenchmark",
        "evidence_label": "measured_on_balfrin_postproc_microbenchmark",
        "measurement_status": "measured_postproc_shell_overhead",
        "classification": "synthetic_postproc_overhead_measured",
        "output_budget_status": "synthetic_package_gate_ready",
        "execution_efficiency_status": "measured_postproc_shell_overhead_only",
        "hazard_execution_status": "no_hazard_execution",
        "file_count": TB305_POSTPROC_MICROBENCHMARK["files_touched"],
        "bytes": TB305_POSTPROC_MICROBENCHMARK["bytes_touched"],
        "manifest_bytes": 65536,
        "reducer_sidecars": 16,
        "runtime_seconds": TB305_POSTPROC_MICROBENCHMARK["wall_seconds"],
        "cpu_seconds": TB305_POSTPROC_MICROBENCHMARK["cpu_seconds"],
        "memory_peak_kb": TB305_POSTPROC_MICROBENCHMARK["peak_rss_kb"],
        "memory_peak_mb": round(TB305_POSTPROC_MICROBENCHMARK["peak_rss_kb"] / 1024, 3),
        "run_root_preservation_status": "preserved_remote_run_root",
        "replayability_status": "synthetic_package_checksummed",
        "authorization_status": "standing_postproc_clearance_used",
        "next_evidence_field": "target_area_metrics_completion",
        "blocker": None,
        "job_id": TB305_POSTPROC_MICROBENCHMARK["job_id"],
        "run_root": TB305_POSTPROC_MICROBENCHMARK["run_root"],
        "phase_seconds": {
            "file_scan": TB305_POSTPROC_MICROBENCHMARK["file_scan_seconds"],
            "manifest_scan": TB305_POSTPROC_MICROBENCHMARK["manifest_scan_seconds"],
            "reducer_merge": TB305_POSTPROC_MICROBENCHMARK["reducer_merge_seconds"],
            "package": TB305_POSTPROC_MICROBENCHMARK["package_seconds"],
        },
        "summary": (
            "TB-305 measured bounded synthetic post-processing shell overhead on Balfrin postproc; "
            "it informs efficiency status only and is not a hazard execution, multi-zone result, or scale capability upgrade."
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
            "TB-314 refreshed the local reduced-output ladder at 1, 2, 4, 8, and 12 zones; 1-4 zones remain ready, 8 and 12 zones are blocked, and the first blocked scratch-local rung stays at 8 zones on accumulation_seconds. TB-312's four-zone postproc result remains separate measured Balfrin evidence, and TB-313 did not change the accumulator implementation."
        ),
    }


def _projection_row() -> dict[str, Any]:
    return {
        "tier_id": "projected_larger_aoi",
        "tier_label": "projected larger AOI",
        "evidence_label": "projection_only",
        "measurement_status": "projection_only",
        "classification": "no_go",
        "output_budget_status": "no_go_projection_beyond_measured_support",
        "execution_efficiency_status": "projection_only_not_measured",
        "file_count": 442,
        "bytes": 102_793_652,
        "manifest_bytes": 147_566,
        "reducer_sidecars": None,
        "runtime_seconds": 463.84,
        "memory_peak_mb": 409.22,
        "run_root_preservation_status": "projection_only",
        "replayability_status": "projection_only",
        "authorization_status": "not_authorized",
        "next_evidence_field": "scale_up_authorized",
        "blocker": "projection_only_beyond_measured_support",
        "summary": (
            "Projected larger AOI planning remains a no-go extrapolation beyond measured support, with manifest growth still the first scaling bottleneck."
        ),
        "planner_decision": "no_go",
        "planner_reason": "Projection-only Swiss-wide planning remains beyond current measured support.",
    }


def build_report() -> dict[str, Any]:
    single_job_summary = single_job.build_summary()
    decision_report = decision_gate.build_report()
    rows = [
        _single_zone_row(single_job_summary),
        _target_area_row(),
        _smallest_multi_zone_row(),
        _four_zone_review_package_row(),
        _four_zone_hazard_probe_blocked_row(),
        _two_zone_preserved_row(),
        _management_aoi_failed_closed_row(),
        _postproc_microbenchmark_row(),
        _fixture_budget_gate_row(),
        _scratch_local_reducer_row(),
        _projection_row(),
    ]
    measured = [row["tier_id"] for row in rows if row["evidence_label"] == "measured_on_balfrin"]
    postproc_microbenchmarks = [
        row["tier_id"] for row in rows if row["evidence_label"] == "measured_on_balfrin_postproc_microbenchmark"
    ]
    blocked = [row["tier_id"] for row in rows if row["classification"].startswith("blocked")]
    blocked_pre_submit = [row["tier_id"] for row in rows if row["evidence_label"] == "blocked_pre_submit"]
    failed_closed = [row["tier_id"] for row in rows if row["evidence_label"] == "failed_closed"]
    fixture_backed = [row["tier_id"] for row in rows if row["evidence_label"] == "fixture_backed"]
    scratch_local = [row["tier_id"] for row in rows if row["evidence_label"] == "scratch_local"]
    projected = [row["tier_id"] for row in rows if row["measurement_status"] == "projection_only"]
    no_go = [row["tier_id"] for row in rows if row["classification"] == "no_go"]
    overall_status = "blocked_reducer_budget" if blocked else "measured"
    recommended = dict(decision_report.get("recommended_next_action") or {})
    four_zone_hazard_row = next((row for row in rows if row["tier_id"] == "four_zone_hazard_probe"), {})
    next_recommended_scaling_task = str(
        four_zone_hazard_row.get("next_recommended_action")
        or "defer_eight_zone_probe_until_measured_hazard_execution"
    )
    live_recommended_next_action = next_recommended_scaling_task or recommended.get("action_id") or recommended.get("option_id")
    next_backlog_recommendations = [
        {
            "rank": 1,
            "action_id": "repair_four_zone_handoff_and_rerun_gate",
            "category": "execution_unblock",
            "status": "recommended_next",
            "reason": (
                "TB-368 preserved two-zone evidence is ready; the four-zone handoff and live-submit gate should consume it instead of stale TB-362 text."
            ),
        },
        {
            "rank": 2,
            "action_id": "optimize_only_from_new_measured_bottleneck",
            "category": "optimization",
            "status": "defer_until_hypothesis_measured",
            "reason": (
                "Optimization should follow a new measured bottleneck; the four-zone postproc evidence and fail-closed multi-zone "
                "branch do not establish an eight-zone hazard execution bottleneck."
            ),
        },
        {
            "rank": 3,
            "action_id": "resolve_two_zone_output_profile_blocker",
            "category": "execution_unblock",
            "status": "ready_for_operator_choice",
            "reason": (
                "The current two-zone branch is blocked at output_profile_status=blocked_output_profile; repair that exact "
                "pre-submit classification before any new live two-zone attempt."
            ),
        },
        {
            "rank": 4,
            "action_id": "stage_real_public_context_for_user_aoi",
            "category": "acquisition",
            "status": "ready_for_operator_choice",
            "reason": (
                "The AOI review surface is fixture-backed and usable, but real AOI progress still depends on staged public geodata "
                "through the dry-run/local-copy/download-gated acquisition driver."
            ),
        },
        {
            "rank": 5,
            "action_id": "defer_physical_frequency_and_operational_claims",
            "category": "explicit_deferral",
            "status": "deferred_boundary",
            "reason": (
                "Observed evidence, calibration, source-frequency semantics, exposure, vulnerability, and operational approval remain absent."
            ),
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_status": overall_status,
        "dashboard_status": overall_status,
        "summary": (
            "Single-zone evidence, TB-307 target-area metrics-completion evidence, and TB-312 four-zone postproc evidence are measured; "
            "TB-314 refreshed the local scratch ladder without changing the scratch-local accumulation boundary after TB-313 rejected the accumulator micro-optimization, "
            "the smallest multi-zone hazard tier remains blocked at manifest_size_bytes, TB-368 now provides preservation-ready measured two-zone evidence for the canonical two-zone hazard path, "
            "and TB-332 failed closed before sbatch on a stale four-zone authorization checksum, "
            "TB-381 failed closed before sbatch on missing management-AOI prepared-pilot inputs, "
            "TB-309 failed closed before sbatch on the reviewed two-zone submit path, "
            "TB-305 contributes synthetic postproc efficiency evidence only, fixture and scratch-local tiers remain non-promotable, and the larger AOI projection remains a no-go."
        ),
        "evidence_label_order": list(EVIDENCE_LABELS),
        "evidence_label_definitions": {
            "measured_on_balfrin": "Preservation-checked Balfrin run-root evidence with measured execution or output fields.",
            "measured_on_balfrin_postproc_microbenchmark": (
                "Preserved Balfrin postproc evidence from a synthetic overhead microbenchmark; efficiency signal only, not hazard execution."
            ),
            "fixture_backed": "Regression or handoff evidence from fixtures; useful for guardrails but not live measured scale capability.",
            "scratch_local": "Local /tmp measurement or generated scratch evidence; useful for bottleneck discovery but not Balfrin evidence.",
            "projection_only": "Planner extrapolation from measured coefficients; not an executed scale tier.",
            "blocked_pre_submit": "A live path stopped before sbatch or live execution and promoted no measured run-root evidence.",
            "partial": "A live path produced incomplete evidence; it is distinct from measured and failed-closed outcomes.",
            "failed_closed": "A bounded path failed closed before live execution because the reviewed package or manifest contract did not match the executable run contract.",
        },
        "tiers": rows,
        "measured_tiers": measured,
        "postproc_microbenchmark_tiers": postproc_microbenchmarks,
        "blocked_tiers": blocked,
        "blocked_pre_submit_tiers": blocked_pre_submit,
        "failed_closed_tiers": failed_closed,
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
        "latest_hazard_execution_status": {
            row["tier_id"]: row.get("hazard_execution_status", row["execution_efficiency_status"]) for row in rows
        },
        "postproc_efficiency_evidence": {
            "tb305_classification": "measured_on_balfrin_postproc_microbenchmark",
            "status": "measured_postproc_shell_overhead",
            "job_id": TB305_POSTPROC_MICROBENCHMARK["job_id"],
            "run_root": TB305_POSTPROC_MICROBENCHMARK["run_root"],
            "wall_seconds": TB305_POSTPROC_MICROBENCHMARK["wall_seconds"],
            "cpu_seconds": TB305_POSTPROC_MICROBENCHMARK["cpu_seconds"],
            "peak_rss_kb": TB305_POSTPROC_MICROBENCHMARK["peak_rss_kb"],
            "files_touched": TB305_POSTPROC_MICROBENCHMARK["files_touched"],
            "bytes_touched": TB305_POSTPROC_MICROBENCHMARK["bytes_touched"],
            "hazard_execution_promoted": False,
            "source_document": "docs/balfrin_postproc_microbenchmark_tb305.md",
        },
        "live_run_authorization_status": {
            "live_submission_authorized": False,
            "standing_postproc_clearance_active": True,
            "standing_postproc_clearance_scope": (
                "GPT-5.5 workers may submit and actively monitor Balfrin postproc jobs after the exact package, access, "
                "readiness, output-budget, authorization-record/audit, preservation, and evidence gates pass."
            ),
            "decision_status": decision_report.get("decision_status"),
            "recommended_next_action": live_recommended_next_action,
            "recommended_next_action_status": recommended.get("status"),
            "blocked_reason": decision_report.get("blocked_reason"),
        },
        "next_recommended_scaling_task": next_recommended_scaling_task or "second_site_public_context_progress",
        "next_recommended_scaling_task_reason": "TB-368 supplies the measured two-zone preservation evidence needed before the four-zone gate can be rerun.",
        "next_evidence_field": next_recommended_scaling_task or "second_site_public_context_progress",
        "next_backlog_recommendations": next_backlog_recommendations,
        "blocked_reason": "four_zone_hazard_probe.authorization_record_checksum",
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
            "docs/balfrin_postproc_microbenchmark_tb305.md",
            "docs/balfrin_two_zone_hazard_run_tb368.md",
            "scripts/execute_management_aoi_balfrin_run.py",
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
        f"postproc_microbenchmark_tiers: {', '.join(report.get('postproc_microbenchmark_tiers', []))}",
        f"failed_closed_tiers: {', '.join(report.get('failed_closed_tiers', []))}",
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
                f"  output_pressure_status: {row.get('output_pressure_status')}",
                f"  execution_efficiency_status: {row.get('execution_efficiency_status')}",
                f"  hazard_execution_status: {row.get('hazard_execution_status')}",
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
                f"  next_recommended_action: {row.get('next_recommended_action')}",
                f"  blocker: {row.get('blocker')}",
                f"  summary: {row.get('summary')}",
            ]
        )
        if row.get("next_recommended_action_reason"):
            lines.append(f"  next_recommended_action_reason: {row.get('next_recommended_action_reason')}")
        if row.get("tier_id") == "smallest_multi_zone":
            lines.append(f"  compact_manifest_bytes: {row.get('compact_manifest_bytes')}")
            lines.append(f"  compact_reducer_sidecars: {row.get('compact_reducer_sidecars')}")
        if row.get("tier_id") == "postproc_microbenchmark":
            lines.append(f"  job_id: {row.get('job_id')}")
            lines.append(f"  cpu_seconds: {row.get('cpu_seconds')}")
            lines.append(f"  memory_peak_kb: {row.get('memory_peak_kb')}")
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
