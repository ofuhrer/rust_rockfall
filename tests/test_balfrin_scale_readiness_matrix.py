from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_scale_readiness_matrix.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_scale_readiness_matrix", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinScaleReadinessMatrixTests(unittest.TestCase):
    def test_build_report_composes_the_authoritative_baseline_matrix(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_scale_readiness_matrix_v1")
        self.assertEqual(report["matrix_status"], "blocked_reducer_budget")
        self.assertEqual(report["dashboard_status"], "blocked_reducer_budget")
        self.assertEqual(report["next_evidence_field"], "optimize_only_from_new_measured_bottleneck")
        self.assertIn("TB-407 smallest multi-zone probe evidence", report["summary"])
        self.assertIn("management-AOI Balfrin decision failed closed before sbatch", report["summary"])
        self.assertEqual(
            report["measured_tiers"],
            [
                "single_zone",
                "target_area",
                "smallest_multi_zone",
                "four_zone_review_package",
                "two_zone_preserved_hazard_run",
            ],
        )
        self.assertEqual(report["blocked_tiers"], ["four_zone_hazard_probe"])
        self.assertEqual(report["blocked_pre_submit_tiers"], ["four_zone_hazard_probe"])
        self.assertEqual(report["failed_closed_tiers"], ["management_aoi_multi_zone_run"])
        self.assertEqual(report["postproc_microbenchmark_tiers"], ["postproc_microbenchmark"])
        self.assertEqual(report["fixture_backed_tiers"], ["fixture_budget_gate"])
        self.assertEqual(report["scratch_local_tiers"], ["local_reducer_ladder"])
        self.assertEqual(report["projection_only_tiers"], ["projected_larger_aoi"])
        self.assertEqual(report["no_go_tiers"], ["projected_larger_aoi"])
        self.assertFalse(report["live_run_authorization_status"]["live_submission_authorized"])
        self.assertTrue(report["live_run_authorization_status"]["standing_postproc_clearance_active"])
        self.assertEqual(
            report["live_run_authorization_status"]["recommended_next_action"],
            "optimize_only_from_new_measured_bottleneck",
        )
        self.assertEqual(
            report["next_recommended_scaling_task"],
            "optimize_only_from_new_measured_bottleneck",
        )
        self.assertEqual(
            [item["action_id"] for item in report["next_backlog_recommendations"]],
            [
                "optimize_only_from_new_measured_bottleneck",
                "repair_four_zone_handoff_and_rerun_gate",
                "resolve_two_zone_output_profile_blocker",
                "stage_real_public_context_for_user_aoi",
                "defer_physical_frequency_and_operational_claims",
            ],
        )
        self.assertEqual(report["next_backlog_recommendations"][0]["category"], "optimization")
        self.assertEqual(
            report["evidence_label_order"],
            [
                "measured_on_balfrin",
                "measured_on_balfrin_postproc_microbenchmark",
                "fixture_backed",
                "scratch_local",
                "projection_only",
                "blocked_pre_submit",
                "partial",
                "failed_closed",
            ],
        )
        self.assertIn("measured_on_balfrin_postproc_microbenchmark", report["evidence_label_definitions"])
        self.assertIn("blocked_pre_submit", report["evidence_label_definitions"])
        self.assertIn("partial", report["evidence_label_definitions"])
        self.assertIn("failed_closed", report["evidence_label_definitions"])
        self.assertIn("smallest_multi_zone", report["latest_output_budget_status"])
        self.assertIn("single_zone", report["latest_execution_efficiency_status"])
        self.assertEqual(
            report["latest_execution_efficiency_status"]["postproc_microbenchmark"],
            "measured_postproc_shell_overhead_only",
        )
        self.assertEqual(report["latest_hazard_execution_status"]["postproc_microbenchmark"], "no_hazard_execution")
        self.assertEqual(
            report["postproc_efficiency_evidence"]["tb305_classification"],
            "measured_on_balfrin_postproc_microbenchmark",
        )
        self.assertFalse(report["postproc_efficiency_evidence"]["hazard_execution_promoted"])

        tiers = {row["tier_id"]: row for row in report["tiers"]}
        self.assertEqual(
            {row["evidence_label"] for row in report["tiers"]},
            {
                "measured_on_balfrin",
                "measured_on_balfrin_postproc_microbenchmark",
                "fixture_backed",
                "scratch_local",
                "projection_only",
                "blocked_pre_submit",
                "failed_closed",
            },
        )
        self.assertEqual(tiers["single_zone"]["classification"], "measured")
        self.assertEqual(tiers["single_zone"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(tiers["single_zone"]["file_count"], 191)
        self.assertEqual(tiers["single_zone"]["bytes"], 267527120)
        self.assertEqual(tiers["single_zone"]["memory_peak_mb"], 409.22)
        self.assertEqual(tiers["single_zone"]["replayability_status"], "pass_hash_stable")

        self.assertEqual(tiers["target_area"]["classification"], "measured_metrics_completion")
        self.assertEqual(tiers["target_area"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(tiers["target_area"]["file_count"], 130)
        self.assertEqual(tiers["target_area"]["bytes"], 34565498)
        self.assertEqual(tiers["target_area"]["hazard_output_file_count"], 99)
        self.assertEqual(tiers["target_area"]["hazard_output_bytes"], 273194249)
        self.assertEqual(tiers["target_area"]["memory_peak_mb"], 5.4375)
        self.assertEqual(tiers["target_area"]["authorization_status"], "authorized_for_one_metrics_completion_rerun")
        self.assertIsNone(tiers["target_area"]["next_evidence_field"])

        self.assertEqual(tiers["smallest_multi_zone"]["classification"], "measured_smallest_multi_zone_probe")
        self.assertEqual(tiers["smallest_multi_zone"]["evidence_label"], "measured_on_balfrin")
        self.assertIn("smallest_multi_zone", report["measured_tiers"])
        self.assertEqual(tiers["smallest_multi_zone"]["job_id"], "4347579")
        self.assertEqual(tiers["smallest_multi_zone"]["run_root"], "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1")
        self.assertEqual(tiers["smallest_multi_zone"]["validation_output_file_count"], 130)
        self.assertEqual(tiers["smallest_multi_zone"]["validation_output_bytes"], 34565330)
        self.assertEqual(tiers["smallest_multi_zone"]["hazard_output_file_count"], 53)
        self.assertEqual(tiers["smallest_multi_zone"]["hazard_output_bytes"], 55831799)
        self.assertEqual(tiers["smallest_multi_zone"]["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertIsNone(tiers["smallest_multi_zone"]["next_evidence_field"])
        self.assertIsNone(tiers["smallest_multi_zone"]["blocker"])
        self.assertEqual(tiers["smallest_multi_zone"]["measurement_status"], "measured_preservation_ready")
        self.assertEqual(
            report["latest_execution_efficiency_status"]["smallest_multi_zone"],
            "measured_smallest_multi_zone_probe",
        )
        self.assertEqual(tiers["four_zone_review_package"]["classification"], "measured_postproc_probe")
        self.assertEqual(tiers["four_zone_review_package"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(tiers["four_zone_review_package"]["measurement_status"], "measured_postproc_probe")
        self.assertEqual(tiers["four_zone_review_package"]["output_budget_status"], "accepted")
        self.assertEqual(tiers["four_zone_review_package"]["hazard_execution_status"], "no_hazard_execution")
        self.assertEqual(tiers["four_zone_review_package"]["job_id"], "4340075")
        self.assertEqual(tiers["four_zone_review_package"]["runtime_seconds"], 1.63)
        self.assertEqual(tiers["four_zone_review_package"]["memory_peak_mb"], 5.33203125)
        self.assertEqual(tiers["four_zone_review_package"]["file_count"], 25)
        self.assertEqual(tiers["four_zone_review_package"]["manifest_bytes"], 12220)
        self.assertEqual(tiers["four_zone_review_package"]["run_root_preservation_status"], "ready_for_demonstration_evidence")
        self.assertEqual(tiers["four_zone_review_package"]["review_readiness_status"], "ready_for_review")
        self.assertIn("TB-312 measured", tiers["four_zone_review_package"]["summary"])

        self.assertEqual(tiers["four_zone_hazard_probe"]["classification"], "blocked_pre_submit_authorization_record_checksum")
        self.assertEqual(tiers["four_zone_hazard_probe"]["evidence_label"], "blocked_pre_submit")
        self.assertEqual(tiers["four_zone_hazard_probe"]["measurement_status"], "blocked_pre_submit")
        self.assertEqual(tiers["four_zone_hazard_probe"]["hazard_execution_status"], "blocked_pre_submit_no_hazard_execution")
        self.assertEqual(tiers["four_zone_hazard_probe"]["preflight_status"], "blocked_missing_authorization")
        self.assertEqual(tiers["four_zone_hazard_probe"]["authorization_status"], "blocked_missing_inputs")
        self.assertEqual(tiers["four_zone_hazard_probe"]["balfrin_access_status"], "ready_for_read_only_collection")
        self.assertEqual(tiers["four_zone_hazard_probe"]["output_budget_status"], "accepted")
        self.assertEqual(tiers["four_zone_hazard_probe"]["output_pressure_status"], "accepted")
        self.assertEqual(tiers["four_zone_hazard_probe"]["submit_contract_status"], "ready")
        self.assertEqual(tiers["four_zone_hazard_probe"]["reducer_budget_status"], "ready")
        self.assertEqual(tiers["four_zone_hazard_probe"]["output_profile_status"], "ready")
        self.assertEqual(
            tiers["four_zone_hazard_probe"]["next_recommended_action"],
            "defer_eight_zone_probe_until_measured_hazard_execution",
        )
        self.assertIn("deferred", tiers["four_zone_hazard_probe"]["next_recommended_action_reason"])
        self.assertIn("checksum does not match", tiers["four_zone_hazard_probe"]["blocker"])
        self.assertEqual(
            tiers["four_zone_hazard_probe"]["next_evidence_field"],
            "authorization_record.reviewed_handoff_package_sha256",
        )
        self.assertNotEqual(
            tiers["four_zone_hazard_probe"]["reviewed_handoff_package_sha256"],
            tiers["four_zone_hazard_probe"]["authorization_record_reviewed_handoff_sha256"],
        )

        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["classification"], "measured_two_zone_preservation_ready")
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["next_evidence_field"], None)
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["metrics_contract_status"], "complete")
        self.assertEqual(
            tiers["two_zone_preserved_hazard_run"]["run_root_preservation_status"],
            "ready_for_demonstration_evidence",
        )
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["job_id"], "4344114")
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["hazard_output_file_count"], 53)
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["hazard_output_bytes"], 55829693)
        self.assertEqual(tiers["two_zone_preserved_hazard_run"]["blocker"], None)
        self.assertEqual(
            report["latest_execution_efficiency_status"]["two_zone_preserved_hazard_run"],
            "measured_preservation_ready",
        )

        self.assertEqual(tiers["management_aoi_multi_zone_run"]["classification"], "failed_closed")
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["evidence_label"], "failed_closed")
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["measurement_status"],
            "failed_closed_no_submission",
        )
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["hazard_execution_status"],
            "failed_closed_no_hazard_execution",
        )
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["blocker"], "blocked_missing_prepared_pilot_inputs")
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["candidate_cell_count"], 1)
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["scenario_row_count"], 3)
        self.assertFalse(tiers["management_aoi_multi_zone_run"]["sbatch_attempted"])
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["latest_no_submit_task"], "TB-393")
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["latest_balfrin_access_preflight_status"],
            "ready_for_read_only_collection",
        )
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["latest_scheduler_submission_status"], "not_attempted")
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["first_persistent_unblock_action"],
            "prepared-pilot inputs are missing",
        )
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["next_evidence_field"],
            "larger_real_staged_management_aoi_crop_with_source_zone_footprint_restaged",
        )

        self.assertEqual(tiers["postproc_microbenchmark"]["classification"], "synthetic_postproc_overhead_measured")
        self.assertEqual(
            tiers["postproc_microbenchmark"]["evidence_label"],
            "measured_on_balfrin_postproc_microbenchmark",
        )
        self.assertEqual(tiers["postproc_microbenchmark"]["measurement_status"], "measured_postproc_shell_overhead")
        self.assertEqual(tiers["postproc_microbenchmark"]["hazard_execution_status"], "no_hazard_execution")
        self.assertEqual(tiers["postproc_microbenchmark"]["job_id"], "4339870")
        self.assertEqual(tiers["postproc_microbenchmark"]["runtime_seconds"], 0.6338623960000405)
        self.assertEqual(tiers["postproc_microbenchmark"]["cpu_seconds"], 0.048968283)
        self.assertEqual(tiers["postproc_microbenchmark"]["memory_peak_kb"], 32624)
        self.assertEqual(tiers["postproc_microbenchmark"]["file_count"], 154)
        self.assertEqual(tiers["postproc_microbenchmark"]["bytes"], 89802)

        self.assertEqual(tiers["fixture_budget_gate"]["evidence_label"], "fixture_backed")
        self.assertEqual(tiers["fixture_budget_gate"]["classification"], "budget_regression_fixture")
        self.assertEqual(tiers["fixture_budget_gate"]["output_budget_status"], "fixture_guardrail_only")

        self.assertEqual(tiers["local_reducer_ladder"]["evidence_label"], "scratch_local")
        self.assertEqual(tiers["local_reducer_ladder"]["classification"], "local_breakpoint_measured")
        self.assertIn("8_zones", tiers["local_reducer_ladder"]["blocker"])
        self.assertIn("1, 2, 4, 8, and 12 zones", tiers["local_reducer_ladder"]["summary"])
        self.assertIn("accumulation_seconds", tiers["local_reducer_ladder"]["summary"])

        self.assertEqual(tiers["projected_larger_aoi"]["classification"], "no_go")
        self.assertEqual(tiers["projected_larger_aoi"]["evidence_label"], "projection_only")
        self.assertEqual(tiers["projected_larger_aoi"]["file_count"], 442)
        self.assertEqual(tiers["projected_larger_aoi"]["bytes"], 102793652)
        self.assertEqual(tiers["projected_larger_aoi"]["runtime_seconds"], 463.84)
        self.assertEqual(tiers["projected_larger_aoi"]["memory_peak_mb"], 409.22)
        self.assertEqual(tiers["projected_larger_aoi"]["manifest_bytes"], 147566)
        self.assertEqual(tiers["projected_larger_aoi"]["planner_decision"], "no_go")

        text = MODULE.render_text_report(report)
        self.assertIn("Balfrin Scale Readiness Baseline Matrix", text)
        self.assertIn("evidence_label: blocked_pre_submit", text)
        self.assertIn("two_zone_preserved_hazard_run", text)
        self.assertIn("single_zone", text)
        self.assertIn("smallest_multi_zone", text)
        self.assertIn("postproc_microbenchmark", text)
        self.assertIn("management_aoi_multi_zone_run", text)
        self.assertIn("failed_closed_tiers: management_aoi_multi_zone_run", text)
        self.assertIn("hazard_execution_status: no_hazard_execution", text)
        self.assertIn("next_recommended_scaling_task: optimize_only_from_new_measured_bottleneck", text)
        self.assertIn("TB-407", text)
        self.assertIn("projected_larger_aoi", text)

    def test_cli_emits_json_and_text_reports(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "text"])
        self.assertEqual(exit_code, 0)
        self.assertIn("matrix_status:", buffer.getvalue())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "json"])
        self.assertEqual(exit_code, 0)
        self.assertIn('"schema_version": "balfrin_scale_readiness_matrix_v1"', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
