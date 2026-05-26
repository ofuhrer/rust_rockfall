from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_next_live_run_decision_gate.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_next_live_run_decision_gate", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

FIXTURE_ROOT = ROOT / "tests/fixtures/balfrin_next_live_run_decision_gate"


class BalfrinNextLiveRunDecisionGateTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def test_ready_fixture_prefers_metrics_completion_rerun(self) -> None:
        report = MODULE.build_report(self.load_fixture("default_bundle.json"))

        self.assertEqual(report["schema_version"], "balfrin_next_live_run_decision_gate_v1")
        self.assertEqual(report["decision_status"], "ready")
        self.assertEqual(report["recommended_next_action"]["action_id"], "metrics_completion_rerun")
        self.assertEqual(report["recommended_next_action"]["classification"], "ready")
        self.assertEqual(report["recommended_next_action"]["path_state"], "measured")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-223")
        self.assertEqual(report["next_follow_up_package_task"], "TB-223")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "ready")
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["second_site_public_context_progress"]["path_state"], "unavailable")
        self.assertEqual(report["option_assessments"]["physical_evidence_acquisition"]["path_state"], "blocked")
        self.assertEqual(report["option_assessments"]["hazard_builder_accumulation_optimization"]["path_state"], "fixture_backed")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["status"], "missing")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["criteria"]["preservation_gate_readiness"]["status"], "ready")
        self.assertEqual(report["criteria"]["balfrin_access"]["status"], "not_checked_not_needed_for_decision_refresh")
        self.assertEqual(
            report["non_postproc_readiness"]["readiness_status"],
            "deferred_no_policy_or_execution_model_need",
        )
        self.assertEqual(report["non_postproc_readiness"]["next_blocker"], "partition_policy")
        self.assertFalse(report["non_postproc_readiness"]["phase_change_authorized"])
        self.assertFalse(report["criteria"]["balfrin_access"]["hard_live_run_blocker"])
        self.assertEqual(report["ranked_actions"][0]["action_id"], "metrics_completion_rerun")
        self.assertIn("annual frequency", report["recommended_next_action"]["boundary_that_prevents_claim_upgrade"])
        self.assertIn("metrics rerun", report["decision_summary"])
        self.assertIn("missing target-area metrics", report["recommended_next_action"]["summary"].lower())
        rendered = MODULE.render_text_report(report)
        self.assertIn("Balfrin Next Live-Run Decision Gate", rendered)
        self.assertIn("metrics_completion_rerun", rendered)
        self.assertIn("metrics_completion_source:", rendered)
        self.assertIn("smallest_bounded_multi_zone_probe", rendered)
        self.assertIn("second_site_public_context_progress", rendered)
        self.assertIn("physical_evidence_acquisition", rendered)
        self.assertIn("hazard_builder_accumulation_optimization", rendered)
        self.assertIn("defer_portability_or_physical_evidence", rendered)
        self.assertIn("non_postproc_readiness:", rendered)

    def test_multi_zone_branch_lists_exact_blockers(self) -> None:
        report = MODULE.build_report(self.load_fixture("default_bundle.json"))
        multi_zone = report["option_assessments"]["smallest_bounded_multi_zone_probe"]

        self.assertEqual(multi_zone["status"], "blocked")
        self.assertEqual(multi_zone["path_state"], "blocked")
        self.assertIn("missing_target_area_metrics", multi_zone["exact_evidence_blockers"])
        self.assertIn("reducer_pressure:multi_zone_dry_run_blocked", multi_zone["exact_evidence_blockers"])
        self.assertIn("multi_zone_package:mixed_provenance", multi_zone["exact_evidence_blockers"])
        self.assertIn("output_pressure:no_go", multi_zone["exact_evidence_blockers"])
        self.assertIn(
            "multi_zone_evidence:blocked_reducer_budget:blocked_output_profile",
            multi_zone["exact_evidence_blockers"],
        )
        self.assertIn("live_multi_zone_measurement_unauthorized", multi_zone["exact_evidence_blockers"])
        self.assertEqual(multi_zone["scaling_frontier_branch"], "failed_closed_two_zone_boundary")
        self.assertIn("repair or rerun the reviewed two-zone package", multi_zone["next_safe_expansion"])
        self.assertIn("distributed execution", multi_zone["boundary_that_prevents_claim_upgrade"])

    def test_measured_two_zone_evidence_moves_frontier_without_authorizing_larger_run(self) -> None:
        bundle = self.load_fixture("defer_bundle.json")
        bundle["multi_zone_balfrin_evidence"] = {
            "status": "measured",
            "evidence_type": "measured",
            "run_root": "/scratch/rust_rockfall/probes/balfrin-demo/measured_two_zone",
            "release_zone_count": 2,
            "metrics_json_promoted": True,
            "preservation_checked": True,
            "preservation_gate_promoted": True,
            "post_run_collector_promoted": True,
            "authorization_status": "authorized_for_one_bounded_probe",
        }
        bundle["balfrin_access"]["live_submission_authorized"] = False

        report = MODULE.build_report(bundle)
        multi_zone = report["option_assessments"]["smallest_bounded_multi_zone_probe"]

        self.assertEqual(report["criteria"]["multi_zone_balfrin_evidence"]["status"], "measured")
        self.assertEqual(
            report["criteria"]["multi_zone_balfrin_evidence"]["scaling_frontier_branch"],
            "measured_two_zone_boundary",
        )
        self.assertEqual(multi_zone["scaling_frontier_branch"], "measured_two_zone_boundary")
        self.assertIn("live_multi_zone_measurement_unauthorized", multi_zone["exact_evidence_blockers"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])

    def test_failed_closed_two_zone_evidence_keeps_live_scale_blocked(self) -> None:
        bundle = self.load_fixture("defer_bundle.json")
        bundle["multi_zone_balfrin_evidence"] = {
            "status": "failed_closed",
            "evidence_type": "failed_closed",
            "run_root": "/scratch/rust_rockfall/probes/balfrin-demo/failed_closed_two_zone",
            "release_zone_count": 2,
            "preflight_status": "ready_for_authorization_review",
            "authorization_record_status": "reviewed",
            "next_blocker": "failed_closed:public_real_site_conditional_pilot_run_v1_schema_mismatch",
        }
        bundle["balfrin_access"]["live_submission_authorized"] = False

        report = MODULE.build_report(bundle)
        multi_zone = report["option_assessments"]["smallest_bounded_multi_zone_probe"]

        self.assertEqual(report["criteria"]["multi_zone_balfrin_evidence"]["status"], "failed_closed")
        self.assertEqual(
            report["criteria"]["multi_zone_balfrin_evidence"]["scaling_frontier_branch"],
            "failed_closed_two_zone_boundary",
        )
        self.assertEqual(multi_zone["scaling_frontier_branch"], "failed_closed_two_zone_boundary")
        self.assertIn("repair or rerun the reviewed two-zone package", report["criteria"]["multi_zone_balfrin_evidence"]["next_safe_expansion"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])

    def test_missing_inputs_fixture_fails_closed(self) -> None:
        report = MODULE.build_report(self.load_fixture("blocked_bundle.json"))

        self.assertEqual(report["decision_status"], "blocked")
        self.assertEqual(report["recommended_next_action"]["classification"], "blocked")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-223")
        self.assertIn("missing", report["blocked_reason"])
        self.assertEqual(report["evidence_sources"]["probe_metrics_report"], None)
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["defer_portability_or_physical_evidence"]["status"], "blocked")

    def test_absent_reducer_scratch_artifacts_emit_blocked_json(self) -> None:
        missing = FileNotFoundError(
            2,
            "No such file or directory",
            "/tmp/rust_rockfall/balfrin_next_live_run_decision_gate_v1/reducer_pressure/output",
        )
        with mock.patch.object(MODULE.reducer_pressure, "build_report", side_effect=missing):
            report = MODULE.build_report()

        self.assertEqual(report["decision_status"], "blocked")
        self.assertEqual(report["blocked_reason"], "reducer_pressure_scratch_root_missing")
        self.assertEqual(report["recommended_next_action"]["action_id"], "reducer_pressure_optimization")
        self.assertEqual(report["criteria"]["reducer_pressure"]["status"], "blocked_missing_scratch_root")
        self.assertIn("--materialize-root", report["criteria"]["reducer_pressure"]["recovery_command"])
        self.assertIn(
            "reducer_pressure_scratch_root_missing",
            report["option_assessments"]["reducer_pressure_optimization"]["exact_evidence_blockers"],
        )
        self.assertIn("multi_zone_reducer_pressure_report", report["recovery_commands"])

    def test_balfrin_ssh_expired_fixture_fails_closed_for_live_paths(self) -> None:
        bundle = self.load_fixture("default_bundle.json")
        bundle["balfrin_access"] = {
            "status": "ssh_access_expired",
            "path_state": "ssh_access_expired",
            "ssh_access_state": "expired",
            "live_submission_authorized": False,
            "blockers": ["ssh_authentication_expired"],
            "summary": "Balfrin SSH access expired before this decision refresh could inspect remote artifacts.",
        }

        report = MODULE.build_report(bundle)

        self.assertEqual(report["decision_status"], "blocked")
        self.assertEqual(report["recommended_next_action"]["classification"], "ssh_access_expired")
        self.assertEqual(report["recommended_next_action"]["path_state"], "ssh_access_expired")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-223")
        self.assertIn("Balfrin SSH access expired", report["blocked_reason"])
        self.assertIn("balfrin_ssh_access:ssh_access_expired", report["option_assessments"]["metrics_completion_rerun"]["exact_evidence_blockers"])
        self.assertIn(
            "balfrin_ssh_access:ssh_access_expired",
            report["option_assessments"]["smallest_bounded_multi_zone_probe"]["exact_evidence_blockers"],
        )

    def test_blocked_pre_submit_metrics_state_fails_closed_with_evidence_details(self) -> None:
        bundle = self.load_fixture("default_bundle.json")
        bundle["probe_metrics_report"]["metrics_completion_source"] = "blocked_pre_submit"
        bundle["probe_metrics_report"]["metrics_completion_outcome"] = "incomplete"
        bundle["probe_metrics_report"]["metrics_completion_attempt_status"] = "blocked_remote_checkout_dirty"
        bundle["probe_metrics_report"]["metrics_evidence_state"] = {
            "schema_version": "balfrin_target_area_metrics_evidence_state_v1",
            "metrics_completion_source": "blocked_pre_submit",
            "metrics_completion_outcome": "incomplete",
            "metrics_completion_attempt_status": "blocked_remote_checkout_dirty",
            "memory_peak_mb": 512.5,
            "validation_output": {"file_count": 2005, "bytes": 571377719},
            "hazard_output": {"file_count": 46, "bytes": 16613900},
            "run_root_hashes": {"run_root_manifest_sha256": "abc123"},
            "slurm": {"job_id": None, "state": None, "exit_code": None, "max_rss": None},
            "preservation_status": "blocked_remote_checkout_dirty",
            "preservation_checked": False,
        }

        report = MODULE.build_report(bundle)
        metrics = report["criteria"]["missing_target_area_metrics"]

        self.assertEqual(report["decision_status"], "blocked")
        self.assertEqual(metrics["status"], "blocked_pre_submit")
        self.assertEqual(metrics["metrics_completion_source"], "blocked_pre_submit")
        self.assertEqual(metrics["metrics_completion_outcome"], "incomplete")
        self.assertEqual(metrics["metrics_completion_attempt_status"], "blocked_remote_checkout_dirty")
        self.assertEqual(metrics["metrics_evidence_state"]["memory_peak_mb"], 512.5)
        self.assertEqual(metrics["metrics_evidence_state"]["validation_output"]["file_count"], 2005)
        self.assertEqual(metrics["metrics_evidence_state"]["hazard_output"]["bytes"], 16613900)
        self.assertEqual(metrics["metrics_evidence_state"]["run_root_hashes"]["run_root_manifest_sha256"], "abc123")
        self.assertIn(
            "metrics_completion_pre_submit:blocked_remote_checkout_dirty",
            report["option_assessments"]["metrics_completion_rerun"]["exact_evidence_blockers"],
        )
        self.assertIn(
            "target_area_metrics_blocked_pre_submit",
            report["option_assessments"]["smallest_bounded_multi_zone_probe"]["exact_evidence_blockers"],
        )
        self.assertIn("blocked before submit", metrics["summary"])

    def test_defer_fixture_prefers_portability_or_physical_evidence_work(self) -> None:
        report = MODULE.build_report(self.load_fixture("defer_bundle.json"))

        self.assertEqual(report["decision_status"], "defer")
        self.assertEqual(report["recommended_next_action"]["action_id"], "second_site_public_context_progress")
        self.assertEqual(report["recommended_next_action"]["classification"], "defer")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-231")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "complete")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["path_state"], "closed")
        self.assertEqual(
            report["option_assessments"]["metrics_completion_rerun"]["metrics_completion_source"],
            "recovered_existing_run_root",
        )
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["defer_portability_or_physical_evidence"]["status"], "defer")
        self.assertEqual(report["option_assessments"]["second_site_public_context_progress"]["status"], "defer")
        self.assertEqual(report["option_assessments"]["physical_evidence_acquisition"]["status"], "defer")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["status"], "complete")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(report["criteria"]["multi_zone_package_readiness"]["status"], "blocked")
        self.assertNotEqual(report["ranked_actions"][0]["action_id"], "metrics_completion_rerun")
        self.assertIn("second-site public-context acquisition", report["recommended_next_action"]["summary"])

    def test_current_evidence_with_ready_access_prefers_reducer_first(self) -> None:
        access = {
            "status": "ready_for_read_only_collection",
            "ready_for_pre_submit": True,
            "remote_head": "reviewed-head",
            "remote_checkout_hygiene": {"status": "pass", "dirty_path_count": 0},
            "live_submission_authorized": False,
        }

        report = MODULE.build_report(balfrin_access_preflight=access)

        self.assertEqual(report["decision_status"], "defer")
        self.assertEqual(report["recommended_next_action"]["action_id"], "reducer_pressure_optimization")
        self.assertEqual(report["recommended_next_action"]["classification"], "reducer_first")
        self.assertEqual(report["criteria"]["balfrin_access"]["status"], "ready_for_read_only_collection")
        self.assertEqual(report["criteria"]["balfrin_access"]["path_state"], "ready_for_pre_submit")
        self.assertEqual(report["criteria"]["balfrin_access"]["remote_head"], "reviewed-head")
        self.assertEqual(report["criteria"]["balfrin_access"]["remote_checkout_hygiene_status"], "pass")
        self.assertEqual(report["criteria"]["reducer_pressure"]["probe_status"], "measured_scratch_root")
        self.assertEqual(report["criteria"]["scenario_batching_cap"]["status"], "ready")
        self.assertEqual(report["criteria"]["candidate_stability_result"]["status"], "ready")
        self.assertEqual(report["criteria"]["multi_zone_balfrin_evidence"]["task_id"], "TB-565")
        self.assertEqual(report["criteria"]["multi_zone_balfrin_evidence"]["slurm_job_id"], "4367244")
        self.assertEqual(
            report["criteria"]["multi_zone_balfrin_evidence"]["scaling_frontier_branch"],
            "measured_regional_split_boundary",
        )
        self.assertEqual(
            report["criteria"]["multi_zone_balfrin_evidence"]["output_budget_audit_status"],
            "blocked_missing_replay_artifacts",
        )

    def test_diagnostic_run_record_moves_frontier_to_single_node_postproc_ceiling(self) -> None:
        bundle = self.load_fixture("defer_bundle.json")
        bundle["multi_zone_balfrin_evidence"] = {
            "schema_version": "balfrin_diagnostic_run_record_v1",
            "status": "completed",
            "terminal_state": "COMPLETED",
            "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525",
            "job_id": "4367731",
            "diagnostic_shape": {"release_zone_count": 16},
            "collection": {
                "status": "complete",
                "pressure_report": {
                    "status": "measured_scratch_root",
                    "release_zone_count": 16,
                    "output_file_count": 52,
                    "output_byte_count": 23661,
                    "manifest_size_bytes": 15898,
                    "root_file_count": 57,
                    "reducer_wall_time_seconds": 3.07,
                },
            },
        }
        bundle["balfrin_access"]["live_submission_authorized"] = False

        report = MODULE.build_report(bundle)
        criteria = report["criteria"]["multi_zone_balfrin_evidence"]
        multi_zone = report["option_assessments"]["smallest_bounded_multi_zone_probe"]

        self.assertEqual(criteria["status"], "measured")
        self.assertEqual(criteria["output_mode"], "diagnostic_reducer_pressure")
        self.assertEqual(criteria["scaling_frontier_branch"], "diagnostic_single_node_postproc_boundary")
        self.assertEqual(
            criteria["diagnostic_single_node_postproc_ceiling"]["simultaneous_release_zone_batch_max"],
            16,
        )
        self.assertEqual(criteria["diagnostic_single_node_postproc_ceiling"]["next_diagnostic_release_zone_count"], 24)
        self.assertIn("24-zone diagnostic", criteria["next_safe_expansion"])
        self.assertIn("scripts/run_balfrin_diagnostic.py", criteria["next_safe_expansion"])
        self.assertEqual(multi_zone["scaling_frontier_branch"], "diagnostic_single_node_postproc_boundary")
        self.assertIn("diagnostic single-node postproc evidence", multi_zone["next_safe_expansion"])

    def test_queue_aware_diagnostic_planner_classifies_run_now_and_batch_now(self) -> None:
        access = {
            "status": "ready_for_read_only_collection",
            "ready_for_pre_submit": True,
            "remote_head": "abc123",
            "captured_at": "2026-05-26T20:00:00Z",
            "postproc_queue_snapshot": {
                "partition": "postproc",
                "idle_nodes": 4,
                "total_nodes": 8,
                "running_jobs": 40,
                "pending_jobs": 0,
                "current_user_jobs": 0,
            },
        }
        now = dt.datetime(2026, 5, 26, 20, 10, tzinfo=dt.UTC)

        single = MODULE.build_diagnostic_run_planner(
            access,
            now=now,
            local_head="abc123",
            diagnostic_job_count=1,
            expected_wall_minutes=30,
        )
        batch = MODULE.build_diagnostic_run_planner(
            access,
            now=now,
            local_head="abc123",
            diagnostic_job_count=3,
            expected_wall_minutes=30,
        )

        self.assertEqual(single["classification"], "run_now")
        self.assertEqual(batch["classification"], "run_batch_now")
        self.assertFalse(single["stale_preflight"])
        self.assertTrue(single["expected_walltime_ok"])
        self.assertTrue(single["six_hour_partition_fill_ok"])

    def test_queue_snapshot_parser_reads_preflight_scheduler_stdout(self) -> None:
        snapshot = MODULE.parse_postproc_queue_snapshot(
            "\n".join(
                [
                    "captured_at=2026-05-26T20:00:00Z",
                    "partition=postproc",
                    "__NODE_STATES__",
                    "idle|11|1-00:00:00",
                    "alloc|1|1-00:00:00",
                    "mix|1|1-00:00:00",
                    "__QUEUE_COUNTS__",
                    "running_jobs=141",
                    "pending_jobs=0",
                    "current_user_jobs=0",
                ]
            )
        )

        self.assertEqual(snapshot["idle_nodes"], 11)
        self.assertEqual(snapshot["total_nodes"], 13)
        self.assertEqual(snapshot["running_jobs"], 141)
        self.assertEqual(snapshot["pending_jobs"], 0)
        self.assertEqual(snapshot["current_user_jobs"], 0)

    def test_queue_aware_diagnostic_planner_fails_closed_on_stale_or_mismatched_preflight(self) -> None:
        access = {
            "status": "ready_for_read_only_collection",
            "ready_for_pre_submit": True,
            "remote_head": "remote-old",
            "captured_at": "2026-05-26T18:00:00Z",
            "postproc_queue_snapshot": {
                "partition": "postproc",
                "idle_nodes": 8,
                "total_nodes": 8,
                "running_jobs": 0,
                "pending_jobs": 0,
            },
        }
        planner = MODULE.build_diagnostic_run_planner(
            access,
            now=dt.datetime(2026, 5, 26, 20, 0, tzinfo=dt.UTC),
            local_head="local-new",
            diagnostic_job_count=1,
            expected_wall_minutes=30,
        )

        self.assertEqual(planner["classification"], "unknown")
        self.assertIn("stale_preflight_or_missing_timestamp", planner["blockers"])
        self.assertIn("remote_head_mismatch", planner["blockers"])

    def test_queue_aware_diagnostic_planner_defers_partition_fill_over_six_hours(self) -> None:
        access = {
            "status": "ready_for_read_only_collection",
            "ready_for_pre_submit": True,
            "remote_head": "abc123",
            "captured_at": "2026-05-26T20:00:00Z",
            "postproc_queue_snapshot": {
                "partition": "postproc",
                "idle_nodes": 8,
                "total_nodes": 8,
                "pending_jobs": 0,
            },
        }
        planner = MODULE.build_diagnostic_run_planner(
            access,
            now=dt.datetime(2026, 5, 26, 20, 10, tzinfo=dt.UTC),
            local_head="abc123",
            diagnostic_job_count=8,
            expected_wall_minutes=420,
        )

        self.assertEqual(planner["classification"], "defer_due_to_capacity")
        self.assertFalse(planner["expected_walltime_ok"])
        self.assertFalse(planner["six_hour_partition_fill_ok"])
        self.assertIn("expected_walltime_exceeds_six_hours", planner["blockers"])
        self.assertIn("partition_fill_exceeds_six_hours", planner["blockers"])

    def test_non_postproc_readiness_identifies_resource_and_policy_blockers(self) -> None:
        resource_blocked = MODULE.build_non_postproc_readiness_from_dimensions(
            {
                "cpu_count": {"status": "pass"},
                "memory": {"status": "blocked", "blocker": "memory", "evidence": "peak exceeds node memory"},
                "runtime": {"status": "pass"},
                "io_volume": {"status": "pass"},
                "walltime": {"status": "pass"},
                "partition_policy": {"status": "deferred", "blocker": "partition_policy"},
                "execution_model": {"status": "deferred", "blocker": "unsupported_execution_model"},
            },
            measured_release_zones=24,
        )
        policy_deferred = MODULE.build_non_postproc_readiness_from_dimensions(
            {
                "cpu_count": {"status": "pass"},
                "memory": {"status": "pass"},
                "runtime": {"status": "pass"},
                "io_volume": {"status": "pass"},
                "walltime": {"status": "pass"},
                "partition_policy": {"status": "deferred", "blocker": "partition_policy"},
                "execution_model": {"status": "deferred", "blocker": "unsupported_execution_model"},
            },
            measured_release_zones=24,
        )

        self.assertEqual(resource_blocked["readiness_status"], "blocked_measured_resource_or_evidence_gap")
        self.assertEqual(resource_blocked["next_blocker"], "memory")
        self.assertEqual(policy_deferred["readiness_status"], "deferred_no_policy_or_execution_model_need")
        self.assertEqual(policy_deferred["next_blocker"], "partition_policy")
        self.assertFalse(policy_deferred["phase_change_authorized"])

    def test_cli_writes_report_artifacts_from_default_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_next_live_run_decision_gate_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--evidence-json",
                        str(FIXTURE_ROOT / "default_bundle.json"),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_next_live_run_decision_gate_v1.json"
            text_path = artifact_dir / "balfrin_next_live_run_decision_gate_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["decision_status"], "ready")
            self.assertIn("Balfrin Next Live-Run Decision Gate", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
