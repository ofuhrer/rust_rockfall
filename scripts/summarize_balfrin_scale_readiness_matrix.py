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
from functools import lru_cache
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import estimate_swiss_wide_execution_envelope as swiss_wide  # noqa: E402
from scripts import generate_balfrin_multi_release_zone_demo_handoff as handoff  # noqa: E402
from scripts import measure_scenario_storage_output_tier_pressure as scenario_pressure  # noqa: E402
from scripts import preflight_balfrin_smallest_multi_zone_probe_authorization as smallest_preflight  # noqa: E402
from scripts import summarize_balfrin_evidence_bundle as evidence_bundle  # noqa: E402
from scripts import summarize_balfrin_next_live_run_decision_gate as decision_gate  # noqa: E402
from scripts import summarize_balfrin_single_job_execution as single_job  # noqa: E402
from scripts import summarize_multi_zone_reducer_pressure as reducer_pressure  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_scale_readiness_matrix_v1"
REDUCER_PRESSURE_REGENERATION_COMMAND = (
    "PYENV_VERSION=system uv run python scripts/validate_multi_zone_reducer_pressure_gate.py "
    "--materialize-root /tmp/rust_rockfall/balfrin_scale_readiness_matrix_v1/reducer_pressure --format json"
)
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
    "source_report": "docs/balfrin_multi_zone_hazard_run_tb407.md",
}
TB447_REGIONAL_SPLIT_RUN = {
    "task_id": "TB-447",
    "job_id": "4350232",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:24",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "source_report": "docs/balfrin_regional_split_probe_gate_tb432.md",
}
TB448_REGIONAL_SPLIT_METRICS = {
    "task_id": "TB-448",
    "job_id": "4350232",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "collection_time": "2026-05-22T00:40:53Z",
    "metrics_contract_status": "complete",
    "validation_output_file_count": 130,
    "validation_output_bytes": 34565323,
    "hazard_output_file_count": 53,
    "hazard_output_bytes": 55837701,
    "conditional_curve_rows": 729600,
    "collector_wall_seconds": 6.738646155004972,
    "collector_peak_memory_mb": 172.921875,
    "preservation_status": "ready_for_demonstration_evidence",
    "source_report": "docs/balfrin_regional_split_run_root_metrics_tb448.md",
}
TB448_REGIONAL_SPLIT_HAZARD_MANIFEST_BYTES = 92458
TB565_REGIONAL_SPLIT_RUN = {
    "task_id": "TB-565",
    "job_id": "4367244",
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:24",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "source_report": "docs/balfrin_regional_split_postproc_run_tb565.md",
}
TB566_REGIONAL_SPLIT_METRICS = {
    "task_id": "TB-566",
    "job_id": "4367244",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "metrics_contract_status": "complete",
    "validation_output_file_count": 130,
    "validation_output_bytes": 34_565_330,
    "hazard_output_file_count": 57,
    "hazard_output_bytes": 57_670_915,
    "conditional_curve_rows": 729_600,
    "collector_wall_seconds": 5.261369686049875,
    "collector_peak_memory_mb": 172.921875,
    "preservation_status": "ready_for_demonstration_evidence",
    "required_run_root_entries_status": "complete",
    "output_family_status": "sufficient",
    "output_budget_audit_status": "blocked_missing_replay_artifacts",
    "output_budget_blocker_category": "replay_critical_budget_template",
    "source_report": "docs/balfrin_regional_split_run_root_metrics_tb566.md",
}
TB566_REGIONAL_SPLIT_HAZARD_MANIFEST_BYTES = 205049
TB432_REGIONAL_SPLIT_FAILED_CLOSED = {
    "task_id": "TB-432",
    "submission_package_status": "failed_closed_preflight",
    "measurement_status": "failed_closed_no_submission",
    "classification": "failed_closed_remote_hygiene_preflight",
    "regional_split_merge_contract_status": "ready",
    "regional_split_count": 12,
    "ready_for_bounded_postproc_submission": False,
    "sbatch_attempted": False,
    "balfrin_job_submitted": False,
    "preflight_status": "blocked_dirty_remote_checkout",
    "remote_checkout_hygiene_status_at_gate": "fail",
    "dirty_path_count_at_gate": 3,
    "stale_generated_file_pattern": "validation/private/tb407_repaired_handoff_remote/**/command_plan.json",
    "post_task_cleanup_status": "remote_hygiene_blocker_cleared",
    "post_cleanup_access_preflight_status": "ready_for_read_only_collection",
    "post_cleanup_ready_for_pre_submit": True,
    "post_cleanup_remote_checkout_hygiene_status": "pass",
    "post_cleanup_dirty_path_count": 0,
    "next_blocker_category": "evidence_collection",
    "next_recommended_action": "regenerate_ready_regional_split_package_and_retry_bounded_postproc_probe",
    "next_evidence_field": "regional_split_bounded_postproc_probe_run_root",
    "source_report": "docs/balfrin_regional_split_probe_gate_tb432.md",
}
TB405_ADJACENT_CANDIDATE_SCENARIO_PATH = {
    "task_id": "TB-405",
    "scenario_state": "adjacent_candidate_review_path",
    "unblock_action": (
        "thread the adjacent-candidate review bundle through scenario regeneration and prepared-pilot "
        "compilation instead of repeating the old source-zone-overlap repair"
    ),
    "next_evidence_field": "adjacent_candidate_scenario_table",
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


@lru_cache(maxsize=1)
def _scenario_storage_pressure_report() -> dict[str, Any]:
    return scenario_pressure.build_report()


@lru_cache(maxsize=1)
def _multi_zone_reducer_pressure_report() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="scale_matrix_reducer_ladder_") as tmpdir:
        return reducer_pressure.build_manifest_pressure_ladder_report(ladder_root=Path(tmpdir) / "ladder")


def _decision_gate_summary_for_scale_matrix() -> dict[str, Any]:
    return {
        "decision_status": "blocked_reducer_budget",
        "blocked_reason": "reducer_pressure_and_replay_metadata_growth",
        "recommended_next_action": {
            "action_id": "summarize_multi_zone_reducer_pressure",
            "status": "recommended_next",
        },
    }


def _regional_split_projection_delta_summary() -> dict[str, Any]:
    measured = _regional_split_measured_row()
    scenario_report = _scenario_storage_pressure_report()
    try:
        reducer_report = _multi_zone_reducer_pressure_report()
    except FileNotFoundError as exc:
        return _blocked_reducer_projection_delta_summary(exc)
    projected_row = _projection_row()
    measured_runtime_seconds = float(measured.get("runtime_seconds") or 0.0)
    measured_file_count = int(measured.get("validation_output_file_count") or 0)
    measured_bytes = int(measured.get("validation_output_bytes") or 0)
    measured_manifest_bytes = TB566_REGIONAL_SPLIT_HAZARD_MANIFEST_BYTES
    projected_runtime_seconds = float(projected_row.get("runtime_seconds") or 0.0)
    projected_file_count = int(projected_row.get("file_count") or 0)
    projected_bytes = int(projected_row.get("bytes") or 0)
    projected_manifest_bytes = int(projected_row.get("manifest_bytes") or 0)
    runtime_within_band = measured_runtime_seconds <= projected_runtime_seconds
    file_count_within_band = measured_file_count <= projected_file_count
    bytes_within_band = measured_bytes <= projected_bytes
    manifest_within_band = measured_manifest_bytes <= projected_manifest_bytes
    reducer_mode = str(reducer_report.get("recommended_default_manifest_mode") or "unknown")
    compact_rung = next(
        (rung for rung in reducer_report.get("rungs", []) if int(rung.get("release_zone_count") or 0) == 12),
        {},
    )
    compact_reduced_delta = dict(compact_rung.get("combined_delta") or {})
    return {
        "schema_version": "regional_split_projection_delta_summary_v1",
        "measurement_status": "measured_existing_artifacts",
        "evidence_label": measured.get("evidence_label"),
        "measured_regional_split": {
            "job_id": measured.get("job_id"),
            "runtime_seconds": measured_runtime_seconds,
            "validation_output_file_count": measured_file_count,
            "validation_output_bytes": measured_bytes,
            "hazard_manifest_bytes": measured_manifest_bytes,
            "hazard_output_file_count": int(measured.get("hazard_output_file_count") or 0),
            "hazard_output_bytes": int(measured.get("hazard_output_bytes") or 0),
            "collector_wall_seconds": TB566_REGIONAL_SPLIT_METRICS["collector_wall_seconds"],
            "collector_peak_memory_mb": TB566_REGIONAL_SPLIT_METRICS["collector_peak_memory_mb"],
        },
        "projection_reference": {
            "tier_id": projected_row.get("tier_id"),
            "tier_label": projected_row.get("tier_label"),
            "runtime_seconds": projected_runtime_seconds,
            "file_count": projected_file_count,
            "bytes": projected_bytes,
            "manifest_bytes": projected_manifest_bytes,
            "memory_peak_mb": projected_row.get("memory_peak_mb"),
            "planner_decision": projected_row.get("planner_decision"),
        },
        "delta_vs_projection": {
            "runtime_seconds": round(measured_runtime_seconds - projected_runtime_seconds, 3),
            "validation_output_file_count": measured_file_count - projected_file_count,
            "validation_output_bytes": measured_bytes - projected_bytes,
            "hazard_manifest_bytes": measured_manifest_bytes - projected_manifest_bytes,
            "memory_peak_mb": round(float(measured.get("memory_peak_mb") or 0.0) - float(projected_row.get("memory_peak_mb") or 0.0), 3),
        },
        "pressure_band_status": {
            "runtime_seconds": "within_projected_band" if runtime_within_band else "above_projected_band",
            "validation_output_file_count": "within_projected_band" if file_count_within_band else "above_projected_band",
            "validation_output_bytes": "within_projected_band" if bytes_within_band else "above_projected_band",
            "hazard_manifest_bytes": "within_projected_band" if manifest_within_band else "above_projected_band",
        },
        "scenario_cardinality_projection_surface": {
            "measurement_status": scenario_report.get("measurement_status"),
            "candidate_repeat_counts": [
                row.get("candidate_repeat_count")
                for row in scenario_report.get("expanded_candidate_set_measurements", [])
                if isinstance(row, dict)
            ],
            "recommended_batching_rule": dict(scenario_report.get("next_balfrin_package_batching_rule") or {}),
            "replay_recommendation": dict(scenario_report.get("balfrin_demonstration_replay_recommendation") or {}),
            "next_scale_bottleneck": dict(scenario_report.get("next_scale_bottleneck") or {}),
        },
        "reducer_pressure_projection_surface": {
            "measurement_status": reducer_report.get("ladder_status"),
            "recommended_default_manifest_mode": reducer_mode,
            "summary": reducer_report.get("summary"),
            "largest_manifest_delta_bytes": int((compact_reduced_delta.get("manifest_size_bytes_delta") or 0)),
            "largest_output_file_count_delta": int((compact_reduced_delta.get("output_file_count_delta") or 0)),
            "largest_reducer_manifest_bytes_delta": int((compact_reduced_delta.get("reducer_manifest_bytes_delta") or 0)),
        },
        "within_expected_pressure_bands": runtime_within_band and file_count_within_band and bytes_within_band and manifest_within_band,
        "next_probe_class": "summarize_multi_zone_reducer_pressure" if reducer_mode == "compact" else "measure_scenario_storage_output_tier_pressure",
        "next_bottleneck_ranked": "reducer_pressure_and_replay_metadata_growth",
        "summary": (
            "The measured regional split run root stays within the projected larger-AOI runtime, file-count, byte, and manifest bands. "
            "Scenario-cardinality pressure remains bounded by the current batching recommendation, and the reducer ladder still recommends compact manifest mode, so reducer/replay metadata is the next ranked bottleneck."
        ),
    }


def _blocked_reducer_projection_delta_summary(exc: FileNotFoundError) -> dict[str, Any]:
    return {
        "schema_version": "regional_split_projection_delta_summary_v1",
        "measurement_status": "blocked_missing_reducer_pressure_scratch_root",
        "evidence_label": "blocked_pre_submit",
        "blocked_reason": "reducer_pressure_scratch_root_missing",
        "missing_path": str(getattr(exc, "filename", "") or exc),
        "reducer_pressure_projection_surface": {
            "measurement_status": "blocked_missing_scratch_root",
            "recommended_default_manifest_mode": "unknown",
            "summary": "Reducer-pressure scratch artifacts are absent; regenerate them before using this projection surface.",
            "largest_manifest_delta_bytes": 0,
            "largest_output_file_count_delta": 0,
            "largest_reducer_manifest_bytes_delta": 0,
            "recovery_command": REDUCER_PRESSURE_REGENERATION_COMMAND,
        },
        "within_expected_pressure_bands": False,
        "next_probe_class": "validate_multi_zone_reducer_pressure_gate",
        "next_bottleneck_ranked": "reducer_pressure_scratch_root_missing",
        "recovery_commands": {
            "multi_zone_reducer_pressure_report": REDUCER_PRESSURE_REGENERATION_COMMAND,
        },
        "summary": "The regional split projection comparison is blocked until reducer-pressure scratch artifacts are regenerated.",
    }


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
    return {
        "tier_id": "smallest_multi_zone",
        "tier_label": "smallest live two-zone probe",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_preservation_ready",
        "classification": "measured_smallest_multi_zone_probe",
        "output_budget_status": "ready_for_demonstration_evidence",
        "execution_efficiency_status": "measured_smallest_multi_zone_probe",
        "file_count": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_file_count"],
        "bytes": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_bytes"],
        "validation_output_file_count": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_file_count"],
        "validation_output_bytes": TB407_SMALL_MULTI_ZONE_PROBE["validation_output_bytes"],
        "hazard_output_file_count": TB407_SMALL_MULTI_ZONE_PROBE["hazard_output_file_count"],
        "hazard_output_bytes": TB407_SMALL_MULTI_ZONE_PROBE["hazard_output_bytes"],
        "manifest_bytes": None,
        "reducer_sidecars": None,
        "runtime_seconds": 29.0,
        "memory_peak_mb": None,
        "run_root_preservation_status": TB407_SMALL_MULTI_ZONE_PROBE["preservation_status"],
        "replayability_status": "preservation_gate_ready",
        "authorization_status": "authorized_for_one_bounded_probe",
        "next_evidence_field": None,
        "blocker": None,
        "metrics_contract_status": TB407_SMALL_MULTI_ZONE_PROBE["metrics_contract_status"],
        "threshold_profile_id": TB407_SMALL_MULTI_ZONE_PROBE["threshold_profile_id"],
        "conditional_curve_rows": TB407_SMALL_MULTI_ZONE_PROBE["conditional_curve_rows"],
        "slurm_job_id": TB407_SMALL_MULTI_ZONE_PROBE["job_id"],
        "job_id": TB407_SMALL_MULTI_ZONE_PROBE["job_id"],
        "run_root": TB407_SMALL_MULTI_ZONE_PROBE["run_root"],
        "slurm": {
            "job_id": TB407_SMALL_MULTI_ZONE_PROBE["job_id"],
            "state": TB407_SMALL_MULTI_ZONE_PROBE["slurm_state"],
            "exit_code": TB407_SMALL_MULTI_ZONE_PROBE["exit_code"],
            "elapsed": TB407_SMALL_MULTI_ZONE_PROBE["elapsed"],
            "alloc_cpus": TB407_SMALL_MULTI_ZONE_PROBE["alloc_cpus"],
        },
        "source_report": TB407_SMALL_MULTI_ZONE_PROBE["source_report"],
        "summary": (
            "TB-407 completed the smallest bounded multi-zone Balfrin postproc submission and preserved measured run-root evidence; "
            "this is measured diagnostic evidence, not operational hazard assessment or scale-up authorization."
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
    adjacent_candidate_path = TB405_ADJACENT_CANDIDATE_SCENARIO_PATH
    return {
        "tier_id": "management_aoi_multi_zone_run",
        "tier_label": "management-AOI multi-zone Balfrin run",
        "evidence_label": "failed_closed",
        "measurement_status": "failed_closed_no_submission",
        "classification": "failed_closed",
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
        "next_evidence_field": adjacent_candidate_path["next_evidence_field"],
        "blocker": "blocked_missing_prepared_pilot_inputs",
        "summary": (
            "TB-405 and TB-404 moved the management-AOI path onto the adjacent-candidate review bundle and "
            "generated scenario table; the failed-closed row now tracks the current candidate/scenario unblock "
            "action instead of the stale source-zone-overlap repair, and no live postproc job was submitted."
        ),
        "latest_no_submit_task": adjacent_candidate_path["task_id"],
        "latest_balfrin_access_preflight_status": "not_supplied",
        "latest_remote_checkout_hygiene_status": "pass",
        "latest_remote_head": "adjacent_candidate_review_applied",
        "latest_scheduler_submission_status": "not_attempted",
        "latest_no_submit_run_id": "management_aoi_multi_zone_v1",
        "latest_no_submit_run_root": None,
        "first_persistent_unblock_action": adjacent_candidate_path["unblock_action"],
        "handoff_classification": "blocked_missing_prepared_pilot_inputs",
        "first_persistent_blocker": {"status": "blocked_missing_prepared_pilot_inputs"},
        "candidate_cell_count": 1,
        "candidate_area_m2": None,
        "scenario_pressure_status": "ready",
        "scenario_row_count": 3,
        "sbatch_attempted": False,
        "scheduler_submission_status": "not_attempted",
        "source_helper": "scripts/execute_management_aoi_balfrin_run.py",
    }


def _regional_split_measured_row() -> dict[str, Any]:
    return {
        "tier_id": "regional_split_probe",
        "tier_label": "regional split postproc probe",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_regional_split_postproc",
        "classification": "measured_regional_split_probe",
        "output_budget_status": "ready_for_demonstration_evidence",
        "output_pressure_status": "measured_regional_split_output_pressure",
        "reducer_pressure_status": "measured_regional_split_reducer_pressure",
        "execution_efficiency_status": "measured_regional_split_postproc_probe",
        "hazard_execution_status": "measured_postproc_probe",
        "file_count": TB566_REGIONAL_SPLIT_METRICS["validation_output_file_count"],
        "bytes": TB566_REGIONAL_SPLIT_METRICS["validation_output_bytes"],
        "validation_output_file_count": TB566_REGIONAL_SPLIT_METRICS["validation_output_file_count"],
        "validation_output_bytes": TB566_REGIONAL_SPLIT_METRICS["validation_output_bytes"],
        "hazard_output_file_count": TB566_REGIONAL_SPLIT_METRICS["hazard_output_file_count"],
        "hazard_output_bytes": TB566_REGIONAL_SPLIT_METRICS["hazard_output_bytes"],
        "manifest_bytes": None,
        "reducer_sidecars": None,
        "runtime_seconds": 24.0,
        "collector_wall_seconds": TB566_REGIONAL_SPLIT_METRICS["collector_wall_seconds"],
        "memory_peak_mb": TB566_REGIONAL_SPLIT_METRICS["collector_peak_memory_mb"],
        "run_root_preservation_status": TB566_REGIONAL_SPLIT_METRICS["preservation_status"],
        "replayability_status": "preservation_gate_ready",
        "authorization_status": "standing_postproc_clearance_used",
        "next_evidence_field": "regional_split_projection_delta_summary",
        "next_recommended_action": "compare_measured_regional_split_against_scenario_and_output_projections",
        "next_recommended_action_reason": (
            "TB-565 and TB-566 now provide current measured regional split evidence: one bounded postproc run completed on Balfrin and the preserved run root recorded validation, hazard, preservation, and output-budget blocker metrics. "
            "The next action remains reducer/output pressure work, not another immediate retry: thread the measured replay-critical budget blockers into the next larger handoff before any further live recommendation."
        ),
        "next_blocker_category": "replay_critical_budget_template",
        "blocker": None,
        "current_blocker": None,
        "summary": (
            "TB-565 executed one bounded regional split Balfrin postproc job and TB-566 collected preservation, metrics, and output-budget evidence for the same run root; this supersedes TB-448 as the latest regional split evidence while staying bounded diagnostic evidence, not operational hazard assessment."
        ),
        "latest_measured_task": TB566_REGIONAL_SPLIT_METRICS["task_id"],
        "job_id": TB566_REGIONAL_SPLIT_METRICS["job_id"],
        "slurm": {
            "job_id": TB565_REGIONAL_SPLIT_RUN["job_id"],
            "state": TB565_REGIONAL_SPLIT_RUN["slurm_state"],
            "exit_code": TB565_REGIONAL_SPLIT_RUN["exit_code"],
            "elapsed": TB565_REGIONAL_SPLIT_RUN["elapsed"],
        },
        "run_root": TB565_REGIONAL_SPLIT_RUN["run_root"],
        "metrics_contract_status": TB566_REGIONAL_SPLIT_METRICS["metrics_contract_status"],
        "conditional_curve_rows": TB566_REGIONAL_SPLIT_METRICS["conditional_curve_rows"],
        "preservation_status": TB566_REGIONAL_SPLIT_METRICS["preservation_status"],
        "required_run_root_entries_status": TB566_REGIONAL_SPLIT_METRICS["required_run_root_entries_status"],
        "output_family_status": TB566_REGIONAL_SPLIT_METRICS["output_family_status"],
        "output_budget_audit_status": TB566_REGIONAL_SPLIT_METRICS["output_budget_audit_status"],
        "output_budget_blocker_category": TB566_REGIONAL_SPLIT_METRICS["output_budget_blocker_category"],
        "supersedes_failed_closed_task": TB432_REGIONAL_SPLIT_FAILED_CLOSED["task_id"],
        "superseded_failed_closed_source_report": TB432_REGIONAL_SPLIT_FAILED_CLOSED["source_report"],
        "source_report": TB566_REGIONAL_SPLIT_METRICS["source_report"],
        "supersedes_regional_split_source_report": TB448_REGIONAL_SPLIT_METRICS["source_report"],
    }


def _diagnostic_run_record_row(evidence: dict[str, Any]) -> dict[str, Any] | None:
    if evidence.get("status") != "measured" or evidence.get("output_mode") != "diagnostic_reducer_pressure":
        return None
    release_zone_count = evidence.get("release_zone_count")
    next_diagnostic_release_zone_count = release_zone_count + 8 if isinstance(release_zone_count, int) else None
    next_reason = (
        f"The simplified Balfrin diagnostic runner produced measured {release_zone_count}-zone reducer-pressure evidence; "
        f"the next step is a {next_diagnostic_release_zone_count}-zone diagnostic run with fixed reducer fan-out before treating this as anything beyond diagnostic postproc evidence."
        if next_diagnostic_release_zone_count
        else "The simplified Balfrin diagnostic runner produced measured reducer-pressure evidence; collect the latest run record before planning another diagnostic step."
    )
    return {
        "tier_id": f"diagnostic_{release_zone_count}_zone_reducer_pressure",
        "tier_label": f"{release_zone_count}-zone diagnostic reducer-pressure run",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_diagnostic_reducer_pressure",
        "classification": "measured_diagnostic_reducer_pressure",
        "output_budget_status": "single_run_record_complete",
        "output_pressure_status": "measured_diagnostic_output_pressure",
        "reducer_pressure_status": "measured_diagnostic_reducer_pressure",
        "execution_efficiency_status": "measured_postproc_diagnostic_run",
        "hazard_execution_status": "no_hazard_execution_reducer_diagnostic_only",
        "file_count": evidence.get("diagnostic_output_file_count"),
        "bytes": evidence.get("diagnostic_output_bytes"),
        "diagnostic_output_file_count": evidence.get("diagnostic_output_file_count"),
        "diagnostic_output_bytes": evidence.get("diagnostic_output_bytes"),
        "manifest_bytes": evidence.get("diagnostic_manifest_size_bytes"),
        "root_file_count": evidence.get("diagnostic_root_file_count"),
        "runtime_seconds": evidence.get("reducer_wall_time_seconds"),
        "memory_peak_mb": evidence.get("memory_peak_mb"),
        "run_root_preservation_status": evidence.get("preservation_gate_status"),
        "replayability_status": evidence.get("required_run_root_entries_status"),
        "authorization_status": "standing_postproc_clearance_used",
        "simultaneous_release_zone_batch_max": release_zone_count,
        "simultaneous_release_zone_batch_max_source": "diagnostic_single_node_postproc",
        "next_diagnostic_release_zone_count": next_diagnostic_release_zone_count,
        "next_evidence_field": "diagnostic_single_node_postproc_ceiling",
        "next_recommended_action": f"run_balfrin_diagnostic_{next_diagnostic_release_zone_count}_zone"
        if next_diagnostic_release_zone_count
        else "collect_latest_diagnostic_run_record",
        "next_recommended_action_reason": next_reason,
        "next_blocker_category": "next_diagnostic_size_not_measured",
        "blocker": None,
        "current_blocker": None,
        "summary": evidence.get("summary"),
        "latest_measured_task": "simplified_balfrin_diagnostic_runner",
        "job_id": evidence.get("slurm_job_id"),
        "slurm": {
            "job_id": evidence.get("slurm_job_id"),
            "state": evidence.get("slurm_state"),
            "exit_code": evidence.get("exit_code"),
            "elapsed": evidence.get("elapsed"),
        },
        "run_root": evidence.get("run_root"),
        "release_zone_count": release_zone_count,
        "metrics_contract_status": "single_run_record_complete",
        "preservation_status": evidence.get("preservation_gate_status"),
        "required_run_root_entries_status": evidence.get("required_run_root_entries_status"),
        "output_family_status": evidence.get("output_family_status"),
        "source_report": first_source_path(evidence, "run_record.json"),
        "claim_boundary": evidence.get("claim_boundary"),
    }


def _diagnostic_single_node_postproc_ceiling(diagnostic_row: dict[str, Any] | None) -> dict[str, Any]:
    if diagnostic_row is None:
        return {
            "status": "missing",
            "provenance_label": "diagnostic_single_node_postproc",
            "simultaneous_release_zone_batch_max": None,
            "next_diagnostic_release_zone_count": None,
        }
    return {
        "status": "measured",
        "provenance_label": "diagnostic_single_node_postproc",
        "simultaneous_release_zone_batch_max": diagnostic_row["simultaneous_release_zone_batch_max"],
        "release_zone_count": diagnostic_row["release_zone_count"],
        "next_diagnostic_release_zone_count": diagnostic_row["next_diagnostic_release_zone_count"],
        "job_id": diagnostic_row["job_id"],
        "run_root": diagnostic_row["run_root"],
        "claim_boundary": diagnostic_row["claim_boundary"],
    }


def _diagnostic_record_performance_row(path: Path) -> dict[str, Any] | None:
    record = evidence_bundle.load_json_object(path)
    if record is None:
        return None
    evidence = evidence_bundle.build_multi_zone_balfrin_evidence(record)
    if evidence.get("status") != "measured" or evidence.get("output_mode") != "diagnostic_reducer_pressure":
        return None
    return {
        "tier_id": f"diagnostic_{evidence.get('release_zone_count')}_zone_reducer_pressure",
        "evidence_label": "measured_on_balfrin",
        "measurement_status": "measured_diagnostic_reducer_pressure",
        "release_zone_count": evidence.get("release_zone_count"),
        "job_id": evidence.get("slurm_job_id"),
        "run_root": evidence.get("run_root"),
        "runtime_seconds": evidence.get("reducer_wall_time_seconds"),
        "memory_peak_mb": evidence.get("memory_peak_mb"),
        "output_file_count": evidence.get("diagnostic_output_file_count"),
        "output_bytes": evidence.get("diagnostic_output_bytes"),
        "manifest_bytes": evidence.get("diagnostic_manifest_size_bytes"),
        "source_path": str(path),
        "claim_boundary": evidence.get("claim_boundary"),
    }


def build_diagnostic_performance_comparison() -> dict[str, Any]:
    diagnostic_paths = tuple(
        dict.fromkeys(
            (
                evidence_bundle.DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORD,
                *evidence_bundle.DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORDS,
            )
        )
    )
    diagnostic_rows = [
        row
        for row in (_diagnostic_record_performance_row(path) for path in diagnostic_paths)
        if row is not None
    ]
    diagnostic_rows.sort(key=lambda row: int(row.get("release_zone_count") or 0))
    comparison_rows = [
        {
            "tier_id": "regional_split_probe",
            "evidence_label": "measured_on_balfrin",
            "measurement_status": "measured_regional_split_postproc",
            "release_zone_count": 12,
            "job_id": TB566_REGIONAL_SPLIT_METRICS["job_id"],
            "run_root": TB566_REGIONAL_SPLIT_METRICS["run_root"],
            "runtime_seconds": 24.0,
            "memory_peak_mb": TB566_REGIONAL_SPLIT_METRICS["collector_peak_memory_mb"],
            "output_file_count": TB566_REGIONAL_SPLIT_METRICS["hazard_output_file_count"],
            "output_bytes": TB566_REGIONAL_SPLIT_METRICS["hazard_output_bytes"],
            "manifest_bytes": TB566_REGIONAL_SPLIT_HAZARD_MANIFEST_BYTES,
            "source_path": TB566_REGIONAL_SPLIT_METRICS["source_report"],
            "claim_boundary": "measured regional split postproc evidence; not operational or physical-probability evidence",
        },
        {
            "tier_id": "historical_regional_split_probe",
            "evidence_label": "measured_on_balfrin",
            "measurement_status": "superseded_measured_regional_split_postproc",
            "release_zone_count": 12,
            "job_id": TB448_REGIONAL_SPLIT_METRICS["job_id"],
            "run_root": TB448_REGIONAL_SPLIT_METRICS["run_root"],
            "runtime_seconds": 24.0,
            "memory_peak_mb": TB448_REGIONAL_SPLIT_METRICS["collector_peak_memory_mb"],
            "output_file_count": TB448_REGIONAL_SPLIT_METRICS["hazard_output_file_count"],
            "output_bytes": TB448_REGIONAL_SPLIT_METRICS["hazard_output_bytes"],
            "manifest_bytes": TB448_REGIONAL_SPLIT_HAZARD_MANIFEST_BYTES,
            "source_path": TB448_REGIONAL_SPLIT_METRICS["source_report"],
            "claim_boundary": "historical measured comparison evidence; superseded by current regional split and diagnostics",
        },
        *diagnostic_rows,
    ]
    latest_diagnostic = diagnostic_rows[-1] if diagnostic_rows else None
    return {
        "schema_version": "balfrin_diagnostic_performance_comparison_v1",
        "status": "measured" if latest_diagnostic else "waiting_for_diagnostic_run_records",
        "comparison_rows": comparison_rows,
        "diagnostic_rows": diagnostic_rows,
        "latest_diagnostic_release_zone_count": latest_diagnostic.get("release_zone_count") if latest_diagnostic else None,
        "latest_diagnostic_tier_id": latest_diagnostic.get("tier_id") if latest_diagnostic else None,
        "claim_boundary": "performance comparison only; no operational, physical-probability, Swiss-wide, distributed, or non-postproc claim",
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2, 6)


def _bounds(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return {"min": None, "median": None, "max": None, "spread": None}
    return {
        "min": min(values),
        "median": _median(values),
        "max": max(values),
        "spread": round(max(values) - min(values), 6),
    }


def build_diagnostic_repeatability_summary() -> dict[str, Any]:
    rows = [
        row
        for row in (
            _diagnostic_record_performance_row(path)
            for path in evidence_bundle.DEFAULT_BALFRIN_24_ZONE_REPEATABILITY_RUN_RECORDS
        )
        if row is not None
    ]
    rows.sort(key=lambda row: str(row.get("job_id") or ""))
    release_zone_counts = sorted({row.get("release_zone_count") for row in rows})
    same_size = len(release_zone_counts) == 1
    status = "measured_repeatability_pair" if len(rows) >= 2 and same_size else "waiting_for_repeatability_pair"
    return {
        "schema_version": "balfrin_diagnostic_repeatability_summary_v1",
        "status": status,
        "evidence_label": "measured_on_balfrin" if status == "measured_repeatability_pair" else "partial",
        "release_zone_count": release_zone_counts[0] if same_size and release_zone_counts else None,
        "run_count": len(rows),
        "rows": rows,
        "bounds": {
            "reducer_wall_time_seconds": _bounds(rows, "runtime_seconds"),
            "memory_peak_mb": _bounds(rows, "memory_peak_mb"),
            "output_file_count": _bounds(rows, "output_file_count"),
            "output_bytes": _bounds(rows, "output_bytes"),
            "manifest_bytes": _bounds(rows, "manifest_bytes"),
        },
        "claim_boundary": "repeatability summary only; no operational, physical-probability, Swiss-wide, distributed, or non-postproc claim",
    }


def first_source_path(evidence: dict[str, Any], default: str) -> str:
    source_paths = evidence.get("source_paths")
    if isinstance(source_paths, list):
        for path in source_paths:
            text = str(path or "").strip()
            if text:
                return text
    return default


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
    decision_report = _decision_gate_summary_for_scale_matrix()
    regional_split_projection_delta_summary = _regional_split_projection_delta_summary()
    latest_multi_zone_evidence = evidence_bundle.build_latest_multi_zone_balfrin_evidence()
    diagnostic_row = _diagnostic_run_record_row(latest_multi_zone_evidence)
    diagnostic_ceiling = _diagnostic_single_node_postproc_ceiling(diagnostic_row)
    diagnostic_performance_comparison = build_diagnostic_performance_comparison()
    diagnostic_repeatability_summary = build_diagnostic_repeatability_summary()
    rows = [
        _single_zone_row(single_job_summary),
        _target_area_row(),
        _smallest_multi_zone_row(),
        _four_zone_review_package_row(),
        _four_zone_hazard_probe_blocked_row(),
        _two_zone_preserved_row(),
        _management_aoi_failed_closed_row(),
        _regional_split_measured_row(),
        *([diagnostic_row] if diagnostic_row is not None else []),
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
    reducer_projection_blocked = (
        regional_split_projection_delta_summary.get("measurement_status")
        == "blocked_missing_reducer_pressure_scratch_root"
    )
    overall_status = "blocked_missing_inputs" if reducer_projection_blocked else "blocked_reducer_budget" if blocked else "measured"
    recommended = dict(decision_report.get("recommended_next_action") or {})
    regional_split_row = next((row for row in rows if row["tier_id"] == "regional_split_probe"), {})
    next_probe_ranking = decision_gate.build_reducer_first_probe_ranking()
    next_recommended_scaling_task = str(next_probe_ranking[0]["action_id"]) if next_probe_ranking else "second_site_public_context_progress"
    live_recommended_next_action = next_recommended_scaling_task or recommended.get("action_id") or recommended.get("option_id")
    next_backlog_recommendations = [
        {
            "rank": item["rank"],
            "action_id": item["action_id"],
            "category": item["category"],
            "status": "recommended_next" if item["rank"] == 1 else "deferred_until_higher_ranked_probe_executes",
            "reason": item["summary"],
        }
        for item in next_probe_ranking
    ]
    operational_readiness_check = build_operational_readiness_check(default_operational_readiness_inputs(rows))
    projection_summary = {
        "status": "projection_only",
        "current_practical_ceiling": (
            f"{diagnostic_ceiling.get('simultaneous_release_zone_batch_max')}-zone diagnostic single-node/postproc reducer-pressure ceiling; "
            "10-zone single-AOI remains the hazard-planning boundary"
            if diagnostic_ceiling.get("simultaneous_release_zone_batch_max")
            else "10-zone single-AOI planning class under the current single-node/postproc evidence boundary"
        ),
        "first_bottleneck": (
            "scientific_evidence_then_queue_policy_for_larger_diagnostics"
            if diagnostic_ceiling.get("simultaneous_release_zone_batch_max")
            else "reducer_pressure_and_replay_metadata_growth"
        ),
        "planning_precondition": "scenario_cardinality_and_manifest_size_must_stay_within_compact_batch_caps",
        "next_measurable_step": (
            f"run a {diagnostic_ceiling.get('next_diagnostic_release_zone_count')}-zone diagnostic on postproc if queue policy remains favorable; "
            "keep regional, Swiss-wide, distributed, operational, and physical-probability claims separate"
            if diagnostic_ceiling.get("next_diagnostic_release_zone_count")
            else "regenerate deterministic local reducer-pressure scratch roots and rerun the reducer-pressure gate before any larger live recommendation"
        ),
        "diagnostic_ceiling": diagnostic_ceiling,
        "diagnostic_repeatability_status": diagnostic_repeatability_summary.get("status"),
        "feasibility_classes": {
            "10_zone": {
                "class": "hazard_planning_boundary",
                "evidence": "measured_single_job_and_small_multi_zone_context",
                "next_blocker": "reducer_pressure",
            },
            "16_zone": {
                "class": "measured_diagnostic_postproc",
                "evidence": "completed diagnostic run record",
                "next_blocker": "scientific_evidence",
            },
            "24_zone": {
                "class": "measured_repeatable_diagnostic_postproc",
                "evidence": "completed diagnostic run record plus repeatability pair",
                "next_blocker": "queue_policy",
            },
            "100_zone": {
                "class": "projection_only_deferred",
                "evidence": "extrapolated from diagnostic and older output-pressure evidence",
                "next_blocker": "reducer_pressure",
            },
            "regional": {
                "class": "deferred_multi_aoi",
                "evidence": "bounded regional split comparison only",
                "next_blocker": "queue_policy",
            },
            "swiss_wide": {
                "class": "deferred_phase_change",
                "evidence": "no measured Swiss-wide execution",
                "next_blocker": "missing_scientific_evidence",
            },
        },
        "evidence_class_separation": {
            "measured": measured,
            "projection_only": projected,
            "failed_closed": failed_closed,
            "blocked_pre_submit": blocked_pre_submit,
            "deferred": [
                "regional_workflows",
                "swiss_wide_execution",
            ],
        },
        "authorization_boundary": "no Swiss-wide run, distributed execution phase change, operational claim, or scale-up authorization",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_status": overall_status,
        "dashboard_status": overall_status,
        "summary": (
            "Single-zone evidence, TB-307 target-area metrics-completion evidence, TB-312 four-zone postproc evidence, TB-368 preserved two-zone evidence, and TB-407 smallest multi-zone probe evidence are measured; "
            "TB-314 refreshed the local scratch ladder without changing the scratch-local accumulation boundary after TB-313 rejected the accumulator micro-optimization, "
            "TB-332 failed closed before sbatch on a stale four-zone authorization checksum, "
            "the management-AOI Balfrin decision failed closed before sbatch on source-zone footprint overlap, "
            "TB-565 and TB-566 now provide current measured regional split evidence from one bounded postproc run root, while TB-432 remains historical failed-closed/no-submit evidence and TB-448 remains superseded measured evidence, "
            "TB-309 failed closed before sbatch on the reviewed two-zone submit path, "
            "TB-305 contributes synthetic postproc efficiency evidence only, fixture and scratch-local tiers remain non-promotable, "
            "TB-450 now threads the measured regional split through the scenario-cardinality, output-tier, and reducer-pressure projections, the ranked next probe ladder now places reducer-pressure optimization first, then scenario batching and local evidence collection, and the larger AOI projection remains a no-go."
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
        "diagnostic_single_node_postproc_ceiling": diagnostic_ceiling,
        "diagnostic_performance_comparison": diagnostic_performance_comparison,
        "diagnostic_repeatability_summary": diagnostic_repeatability_summary,
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
        "operational_readiness_check": operational_readiness_check,
        "next_probe_ranking": next_probe_ranking,
        "swiss_scale_feasibility_projection": projection_summary,
        "next_recommended_scaling_task": next_recommended_scaling_task or "second_site_public_context_progress",
        "next_recommended_scaling_task_reason": "TB-450 now threads the measured regional split into the scenario-cardinality, output-tier, and reducer-pressure projections, so the ranked next scale action is reducer-pressure optimization rather than another comparison pass.",
        "regional_split_status": {
            "classification": regional_split_row.get("classification"),
            "evidence_label": regional_split_row.get("evidence_label"),
            "measurement_status": regional_split_row.get("measurement_status"),
            "job_id": regional_split_row.get("job_id"),
            "run_root": regional_split_row.get("run_root"),
            "validation_output_file_count": regional_split_row.get("validation_output_file_count"),
            "validation_output_bytes": regional_split_row.get("validation_output_bytes"),
            "hazard_output_file_count": regional_split_row.get("hazard_output_file_count"),
            "hazard_output_bytes": regional_split_row.get("hazard_output_bytes"),
            "conditional_curve_rows": regional_split_row.get("conditional_curve_rows"),
            "collector_wall_seconds": regional_split_row.get("collector_wall_seconds"),
            "memory_peak_mb": regional_split_row.get("memory_peak_mb"),
            "metrics_contract_status": regional_split_row.get("metrics_contract_status"),
            "preservation_status": regional_split_row.get("preservation_status"),
            "next_blocker_category": regional_split_row.get("next_blocker_category"),
            "next_recommended_action": regional_split_row.get("next_recommended_action"),
            "output_budget_audit_status": regional_split_row.get("output_budget_audit_status"),
            "output_budget_blocker_category": regional_split_row.get("output_budget_blocker_category"),
            "supersedes_failed_closed_task": regional_split_row.get("supersedes_failed_closed_task"),
            "superseded_failed_closed_source_report": regional_split_row.get("superseded_failed_closed_source_report"),
            "supersedes_regional_split_source_report": regional_split_row.get("supersedes_regional_split_source_report"),
            "source_report": regional_split_row.get("source_report"),
            "projection_delta_summary": regional_split_projection_delta_summary,
        },
        "regional_split_projection_delta_summary": regional_split_projection_delta_summary,
        "next_evidence_field": "regional_split_projection_delta_summary",
        "next_backlog_recommendations": next_backlog_recommendations,
        "blocked_reason": (
            "reducer_pressure_scratch_root_missing"
            if reducer_projection_blocked
            else "four_zone_hazard_probe.authorization_record_checksum"
        ),
        "recovery_commands": regional_split_projection_delta_summary.get("recovery_commands", {}),
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
            "scripts/measure_scenario_storage_output_tier_pressure.py",
            "scripts/summarize_multi_zone_reducer_pressure.py",
            "docs/balfrin_postproc_microbenchmark_tb305.md",
            "docs/balfrin_two_zone_hazard_run_tb368.md",
            "docs/balfrin_multi_zone_hazard_run_tb407.md",
            "docs/balfrin_regional_split_probe_gate_tb432.md",
            "docs/balfrin_regional_split_run_root_metrics_tb448.md",
            "docs/swiss_scale_feasibility_projection.md",
            "docs/multi_zone_reducer_pressure_probe.md",
            "scripts/execute_management_aoi_balfrin_run.py",
        ],
    }


OPERATIONAL_READINESS_REQUIREMENTS = (
    {
        "criterion": "scientific_validation",
        "required_status": "pass",
        "acceptance_criteria": [
            "physical-probability or accepted conditional-use validation evidence is present",
            "calibration/holdout separation is accepted",
            "multi-site or held-out evidence supports the intended use",
        ],
    },
    {
        "criterion": "reproducibility",
        "required_status": "pass",
        "acceptance_criteria": [
            "run commands, inputs, output manifests, hashes, and replay-critical artifacts are preserved",
            "local and CI checks can reproduce the package-level evidence",
        ],
    },
    {
        "criterion": "gis_package_qa",
        "required_status": "pass",
        "acceptance_criteria": [
            "GIS package manifests, raster metadata, and visual/automated QA are complete for the intended product",
            "manual review blockers are resolved or explicitly accepted for the intended use",
        ],
    },
    {
        "criterion": "provenance",
        "required_status": "pass",
        "acceptance_criteria": [
            "terrain, source-zone, scenario, calibration, validation, and run-root provenance are traceable",
            "source licenses and non-production boundaries are recorded",
        ],
    },
    {
        "criterion": "monitoring",
        "required_status": "pass",
        "acceptance_criteria": [
            "runtime, memory, output volume, scheduler state, and failure modes are monitored",
            "regressions have a reviewed response path",
        ],
    },
    {
        "criterion": "versioning",
        "required_status": "pass",
        "acceptance_criteria": [
            "model version, code commit, data versions, and output schema versions are pinned",
            "breaking changes are isolated from operational candidates",
        ],
    },
    {
        "criterion": "support_status",
        "required_status": "pass",
        "acceptance_criteria": [
            "the product is no longer labelled research_diagnostic for the intended use",
            "user warnings and unsupported-use boundaries are explicit",
        ],
    },
)


def default_operational_readiness_inputs(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    measured_preserved = [
        row["tier_id"]
        for row in rows
        if row.get("evidence_label") == "measured_on_balfrin"
        and str(row.get("preservation_status", "")).startswith("ready")
    ]
    return {
        "scientific_validation": {
            "status": "blocked",
            "evidence": "physical probability, calibration, and independent validation evidence remain incomplete",
            "first_missing_input": "accepted_scientific_validation_package",
        },
        "reproducibility": {
            "status": "pass" if measured_preserved else "partial",
            "evidence": f"preserved measured tiers: {', '.join(measured_preserved) or 'none'}",
            "first_missing_input": "" if measured_preserved else "preserved_replayable_run_root",
        },
        "gis_package_qa": {
            "status": "blocked",
            "evidence": "automated package checks exist, but operational visual/review acceptance is absent",
            "first_missing_input": "accepted_operational_gis_package_qa",
        },
        "provenance": {
            "status": "partial",
            "evidence": "run-root and public-geodata provenance are recorded for diagnostics, but operational provenance is incomplete",
            "first_missing_input": "complete_operational_product_provenance",
        },
        "monitoring": {
            "status": "partial",
            "evidence": "CI performance and Balfrin diagnostic monitoring exist, but operational monitoring is not defined",
            "first_missing_input": "operational_monitoring_response_plan",
        },
        "versioning": {
            "status": "pass",
            "evidence": "crate/model version and git commits are recorded in reports and run records",
            "first_missing_input": "",
        },
        "support_status": {
            "status": "blocked",
            "evidence": "current products remain research_diagnostic and explicitly non-operational",
            "first_missing_input": "operational_candidate_support_statement",
        },
    }


def build_operational_readiness_check(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = []
    for requirement in OPERATIONAL_READINESS_REQUIREMENTS:
        criterion = str(requirement["criterion"])
        current = dict(inputs.get(criterion) or {})
        status = str(current.get("status") or "missing")
        passed = status == requirement["required_status"]
        checks.append(
            {
                "criterion": criterion,
                "required_status": requirement["required_status"],
                "current_status": status,
                "check_status": "pass" if passed else "fail",
                "evidence": str(current.get("evidence") or ""),
                "first_missing_input": "" if passed else str(current.get("first_missing_input") or criterion),
                "acceptance_criteria": list(requirement["acceptance_criteria"]),
            }
        )

    failing = [check for check in checks if check["check_status"] != "pass"]
    passing_count = len(checks) - len(failing)
    if not failing:
        readiness_status = "operational_candidate_ready"
    elif passing_count >= len(checks) - 2:
        readiness_status = "review_ready_not_operational"
    else:
        readiness_status = "diagnostic_only_not_operational"

    return {
        "schema_version": "operational_readiness_check_v1",
        "readiness_status": readiness_status,
        "operational_candidate_allowed": not failing,
        "passing_criteria_count": passing_count,
        "required_criteria_count": len(checks),
        "failing_criteria": [check["criterion"] for check in failing],
        "first_missing_input": failing[0]["first_missing_input"] if failing else "",
        "criteria": checks,
        "boundary_note": (
            "Operational readiness requires scientific validation, reproducibility, GIS/package QA, provenance, "
            "monitoring, versioning, and support-status evidence. Performance evidence alone cannot pass this check."
        ),
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
        "operational_readiness_check:",
        f"  readiness_status: {report['operational_readiness_check']['readiness_status']}",
        f"  passing_criteria_count: {report['operational_readiness_check']['passing_criteria_count']}/{report['operational_readiness_check']['required_criteria_count']}",
        f"  failing_criteria: {', '.join(report['operational_readiness_check']['failing_criteria']) or 'none'}",
        f"  first_missing_input: {report['operational_readiness_check']['first_missing_input'] or 'none'}",
        "swiss_scale_feasibility_projection:",
        f"  current_practical_ceiling: {report['swiss_scale_feasibility_projection']['current_practical_ceiling']}",
        f"  first_bottleneck: {report['swiss_scale_feasibility_projection']['first_bottleneck']}",
        f"  next_measurable_step: {report['swiss_scale_feasibility_projection']['next_measurable_step']}",
        "next_probe_ranking:",
    ]
    for row in report.get("next_probe_ranking", []):
        lines.extend(
            [
                f"- rank {row.get('rank', '?')}: {row.get('action_id', 'unknown')}",
                f"  category: {row.get('category')}",
                f"  blocker: {row.get('blocker')}",
                f"  expected_evidence_gain: {row.get('expected_evidence_gain')}",
                f"  required_pre_submit_gates: {', '.join(row.get('required_pre_submit_gates', []))}",
                f"  probe_scope: {row.get('probe_scope')}",
            ]
        )
        if row.get("summary"):
            lines.append(f"  summary: {row.get('summary')}")
    delta = report.get("regional_split_projection_delta_summary") or {}
    measured = dict(delta.get("measured_regional_split") or {})
    projection = dict(delta.get("projection_reference") or {})
    deltas = dict(delta.get("delta_vs_projection") or {})
    pressure_band_status = dict(delta.get("pressure_band_status") or {})
    if delta:
        lines.extend(
            [
                "regional_split_projection_delta_summary:",
                f"  status: {delta.get('measurement_status')}",
                f"  within_expected_pressure_bands: {delta.get('within_expected_pressure_bands')}",
                f"  runtime_seconds: measured={measured.get('runtime_seconds')} projected={projection.get('runtime_seconds')} delta={deltas.get('runtime_seconds')}",
                f"  validation_output_file_count: measured={measured.get('validation_output_file_count')} projected={projection.get('file_count')} delta={deltas.get('validation_output_file_count')}",
                f"  validation_output_bytes: measured={measured.get('validation_output_bytes')} projected={projection.get('bytes')} delta={deltas.get('validation_output_bytes')}",
                f"  hazard_manifest_bytes: measured={measured.get('hazard_manifest_bytes')} projected={projection.get('manifest_bytes')} delta={deltas.get('hazard_manifest_bytes')}",
                f"  reducer_pressure: next_probe_class={delta.get('next_probe_class')} next_bottleneck={delta.get('next_bottleneck_ranked')} reducer_mode={dict(delta.get('reducer_pressure_projection_surface') or {}).get('recommended_default_manifest_mode')}",
                f"  pressure_band_status: runtime={pressure_band_status.get('runtime_seconds')} file_count={pressure_band_status.get('validation_output_file_count')} bytes={pressure_band_status.get('validation_output_bytes')} manifest={pressure_band_status.get('hazard_manifest_bytes')}",
            ]
        )
    lines.extend(
        [
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
    )
    for row in report.get("tiers", []):
        lines.extend(
            [
                f"- {row.get('tier_id')}",
                f"  classification: {row.get('classification')}",
                f"  evidence_label: {row.get('evidence_label')}",
                f"  measurement_status: {row.get('measurement_status')}",
                f"  output_budget_status: {row.get('output_budget_status')}",
                f"  output_pressure_status: {row.get('output_pressure_status')}",
                f"  reducer_pressure_status: {row.get('reducer_pressure_status')}",
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
                f"  next_blocker_category: {row.get('next_blocker_category')}",
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
