from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


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
        self.assertEqual(report["matrix_status"], "actionable_reducer_pressure")
        self.assertEqual(report["dashboard_status"], "actionable_reducer_pressure")
        self.assertEqual(report["blocked_reason"], "reducer_pressure_and_replay_metadata_growth")
        self.assertEqual(
            report["operational_readiness_check"]["readiness_status"],
            "diagnostic_only_not_operational",
        )
        self.assertFalse(report["operational_readiness_check"]["operational_candidate_allowed"])
        self.assertIn("scientific_validation", report["operational_readiness_check"]["failing_criteria"])
        self.assertIn("support_status", report["operational_readiness_check"]["failing_criteria"])
        phase_change = report["phase_change_decision_check"]
        self.assertEqual(phase_change["schema_version"], "phase_change_decision_check_v1")
        self.assertEqual(phase_change["decision_status"], "blocked_or_deferred")
        self.assertFalse(phase_change["phase_change_authorized"])
        self.assertEqual(
            phase_change["first_scientifically_useful_next_action"]["readiness_class"],
            "physical_probability",
        )
        self.assertIn("swiss_wide", phase_change["blocked_or_deferred_classes"])
        self.assertIn("distributed", phase_change["blocked_or_deferred_classes"])
        self.assertIn("non_postproc", phase_change["blocked_or_deferred_classes"])
        self.assertEqual(
            report["next_evidence_field"],
            "regional_split_projection_delta_summary",
        )
        self.assertIn("TB-407 smallest multi-zone probe evidence", report["summary"])
        self.assertIn("TB-565 and TB-566 now provide current measured regional split evidence", report["summary"])
        self.assertIn("TB-619 remains the latest measured bounded hazard-throughput evidence", report["summary"])
        self.assertIn("TB-652 adds a completed 8-zone compact diagnostic comparison point", report["summary"])
        self.assertIn("TB-450 now threads the measured regional split", report["summary"])
        self.assertIn("ranked next probe ladder now places reducer-pressure optimization first", report["summary"])
        self.assertEqual(
            report["measured_tiers"],
            [
                "single_zone",
                "target_area",
                "smallest_multi_zone",
                "four_zone_review_package",
                "two_zone_preserved_hazard_run",
                "regional_split_probe",
                "hazard_throughput_probe",
                "tb652_8_zone_diagnostic_probe",
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
            "summarize_multi_zone_reducer_pressure",
        )
        self.assertEqual(
            report["next_recommended_scaling_task"],
            "summarize_multi_zone_reducer_pressure",
        )
        self.assertEqual(len(report["next_probe_ranking"]), 3)
        self.assertEqual(
            report["next_probe_ranking"][0]["action_id"],
            "summarize_multi_zone_reducer_pressure",
        )
        self.assertEqual(report["next_probe_ranking"][0]["probe_scope"], "scratch_local_and_fixture_backed")
        self.assertEqual(
            report["next_probe_ranking"][0]["blocker"],
            "reducer_pressure_and_replay_metadata_growth_remain_the_next_bottlenecks",
        )
        self.assertIn("compact reducer manifest pressure", report["next_probe_ranking"][0]["expected_evidence_gain"])
        self.assertEqual(report["next_probe_ranking"][1]["action_id"], "measure_scenario_storage_output_tier_pressure")
        self.assertIn("scenario_cardinality_and_manifest_size", report["next_probe_ranking"][1]["blocker"])
        self.assertEqual(report["next_probe_ranking"][2]["probe_scope"], "scratch_local")
        self.assertEqual(report["next_probe_ranking"][2]["action_id"], "summarize_balfrin_target_area_candidate_stability")
        projection = report["swiss_scale_feasibility_projection"]
        self.assertEqual(projection["status"], "projection_only")
        self.assertIn("10-zone single-AOI", projection["current_practical_ceiling"])
        self.assertEqual(projection["first_bottleneck"], "reducer_pressure_and_replay_metadata_growth")
        self.assertIn("deterministic local reducer-pressure scratch roots", projection["next_measurable_step"])
        self.assertIn("regional_split_probe", projection["evidence_class_separation"]["measured"])
        self.assertIn("hazard_throughput_probe", projection["evidence_class_separation"]["measured"])
        self.assertIn("tb652_8_zone_diagnostic_probe", projection["evidence_class_separation"]["measured"])
        self.assertIn("projected_larger_aoi", projection["evidence_class_separation"]["projection_only"])
        self.assertIn("management_aoi_multi_zone_run", projection["evidence_class_separation"]["failed_closed"])
        self.assertIn("swiss_wide_execution", projection["evidence_class_separation"]["deferred"])
        self.assertIn("no Swiss-wide run", projection["authorization_boundary"])
        self.assertEqual(
            report["regional_split_status"]["classification"],
            "measured_regional_split_probe",
        )
        self.assertEqual(report["regional_split_status"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(report["regional_split_status"]["measurement_status"], "measured_regional_split_postproc")
        self.assertEqual(report["regional_split_status"]["next_blocker_category"], "replay_critical_budget_template")
        self.assertEqual(report["regional_split_status"]["job_id"], "4367244")
        self.assertEqual(report["regional_split_status"]["run_root"], "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1")
        self.assertEqual(report["regional_split_status"]["validation_output_file_count"], 130)
        self.assertEqual(report["regional_split_status"]["validation_output_bytes"], 34565330)
        self.assertEqual(report["regional_split_status"]["hazard_output_file_count"], 57)
        self.assertEqual(report["regional_split_status"]["hazard_output_bytes"], 57670915)
        self.assertEqual(report["regional_split_status"]["conditional_curve_rows"], 729600)
        self.assertEqual(report["regional_split_status"]["collector_wall_seconds"], 5.261369686049875)
        self.assertEqual(report["regional_split_status"]["memory_peak_mb"], 172.921875)
        self.assertEqual(report["regional_split_status"]["metrics_contract_status"], "complete")
        self.assertEqual(report["regional_split_status"]["preservation_status"], "ready_for_demonstration_evidence")
        self.assertEqual(report["regional_split_status"]["output_budget_audit_status"], "blocked_missing_replay_artifacts")
        self.assertEqual(report["regional_split_status"]["output_budget_blocker_category"], "replay_critical_budget_template")
        self.assertEqual(report["regional_split_status"]["supersedes_failed_closed_task"], "TB-432")
        self.assertEqual(report["regional_split_status"]["source_report"], "docs/balfrin_regional_split_run_root_metrics_tb566.md")
        self.assertEqual(report["regional_split_status"]["supersedes_regional_split_source_report"], "docs/balfrin_regional_split_run_root_metrics_tb448.md")
        self.assertEqual(
            report["hazard_throughput_status"]["classification"],
            "measured_hazard_throughput_probe",
        )
        self.assertEqual(report["hazard_throughput_status"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(report["hazard_throughput_status"]["measurement_status"], "measured_hazard_throughput_postproc")
        self.assertEqual(report["hazard_throughput_status"]["job_id"], "4372656")
        self.assertEqual(
            report["hazard_throughput_status"]["run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527",
        )
        self.assertEqual(report["hazard_throughput_status"]["runtime_seconds"], 6.930015419959091)
        self.assertEqual(report["hazard_throughput_status"]["memory_peak_mb"], 379.14453125)
        self.assertEqual(report["hazard_throughput_status"]["validation_output_file_count"], 130)
        self.assertEqual(report["hazard_throughput_status"]["validation_output_bytes"], 34565323)
        self.assertEqual(report["hazard_throughput_status"]["hazard_output_file_count"], 57)
        self.assertEqual(report["hazard_throughput_status"]["hazard_output_bytes"], 31439445)
        self.assertEqual(report["hazard_throughput_status"]["conditional_curve_rows"], 729600)
        self.assertEqual(report["hazard_throughput_status"]["metrics_contract_status"], "complete")
        self.assertEqual(report["hazard_throughput_status"]["preservation_status"], "ready_for_demonstration_evidence")
        self.assertEqual(report["hazard_throughput_status"]["source_report"], "docs/balfrin_four_zone_hazard_run_tb619.md")
        self.assertEqual(report["hazard_throughput_status"]["previous_support_source_report"], "docs/balfrin_hazard_throughput_run_tb603.md")
        self.assertEqual(report["hazard_throughput_status"]["comparison_baseline"]["baseline_task_id"], "TB-603")
        self.assertEqual(report["hazard_throughput_status"]["comparison_baseline"]["baseline_job_id"], "4372309")
        self.assertTrue(report["hazard_throughput_status"]["comparison_baseline"]["same_conditional_curve_rows"])
        tb652_row = next(row for row in report["tiers"] if row["tier_id"] == "tb652_8_zone_diagnostic_probe")
        self.assertEqual(tb652_row["job_id"], "4377075")
        self.assertEqual(tb652_row["release_zone_count"], 8)
        self.assertEqual(tb652_row["diagnostic_output_file_count"], 28)
        self.assertEqual(tb652_row["diagnostic_output_bytes"], 14397)
        self.assertEqual(tb652_row["runtime_seconds"], 2.11)
        self.assertIn("TB-619 remains latest bounded hazard-throughput support", tb652_row["comparison_anchor"])
        delta_summary = report["regional_split_projection_delta_summary"]
        self.assertFalse(delta_summary["within_expected_pressure_bands"])
        self.assertEqual(delta_summary["next_probe_class"], "summarize_multi_zone_reducer_pressure")
        self.assertEqual(delta_summary["next_bottleneck_ranked"], "reducer_pressure_and_replay_metadata_growth")
        self.assertEqual(delta_summary["projection_reference"]["tier_id"], "projected_larger_aoi")
        self.assertEqual(delta_summary["pressure_band_status"]["runtime_seconds"], "within_projected_band")
        self.assertEqual(delta_summary["pressure_band_status"]["hazard_manifest_bytes"], "above_projected_band")
        self.assertEqual(delta_summary["delta_vs_projection"]["runtime_seconds"], -439.84)
        self.assertEqual(delta_summary["delta_vs_projection"]["validation_output_file_count"], -312)
        self.assertEqual(delta_summary["delta_vs_projection"]["validation_output_bytes"], -68228322)
        self.assertEqual(delta_summary["delta_vs_projection"]["hazard_manifest_bytes"], 57483)
        self.assertEqual(
            delta_summary["reducer_pressure_projection_surface"]["recommended_default_manifest_mode"],
            "compact",
        )
        self.assertLess(delta_summary["reducer_pressure_projection_surface"]["largest_manifest_delta_bytes"], 0)
        self.assertEqual(report["regional_split_status"]["projection_delta_summary"], delta_summary)
        self.assertEqual(
            [item["action_id"] for item in report["next_backlog_recommendations"]],
            [
                "summarize_multi_zone_reducer_pressure",
                "measure_scenario_storage_output_tier_pressure",
                "summarize_balfrin_target_area_candidate_stability",
            ],
        )
        self.assertEqual(report["next_backlog_recommendations"][0]["category"], "reducer_pressure")
        self.assertEqual(report["next_backlog_recommendations"][1]["status"], "deferred_until_higher_ranked_probe_executes")
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
            report["latest_execution_efficiency_status"]["regional_split_probe"],
            "measured_regional_split_postproc_probe",
        )
        self.assertEqual(
            report["latest_execution_efficiency_status"]["hazard_throughput_probe"],
            "measured_hazard_throughput_postproc_probe",
        )
        self.assertEqual(report["latest_output_budget_status"]["regional_split_probe"], "ready_for_demonstration_evidence")
        self.assertEqual(
            report["latest_hazard_execution_status"]["hazard_throughput_probe"],
            "measured_bounded_hazard_throughput",
        )
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

        self.assertEqual(tiers["regional_split_probe"]["classification"], "measured_regional_split_probe")
        self.assertEqual(tiers["regional_split_probe"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(tiers["regional_split_probe"]["measurement_status"], "measured_regional_split_postproc")
        self.assertEqual(tiers["regional_split_probe"]["output_budget_status"], "ready_for_demonstration_evidence")
        self.assertEqual(tiers["regional_split_probe"]["output_pressure_status"], "measured_regional_split_output_pressure")
        self.assertEqual(tiers["regional_split_probe"]["reducer_pressure_status"], "measured_regional_split_reducer_pressure")
        self.assertEqual(tiers["regional_split_probe"]["hazard_execution_status"], "measured_postproc_probe")
        self.assertEqual(tiers["regional_split_probe"]["job_id"], "4367244")
        self.assertEqual(tiers["regional_split_probe"]["run_root"], "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1")
        self.assertEqual(tiers["regional_split_probe"]["validation_output_file_count"], 130)
        self.assertEqual(tiers["regional_split_probe"]["validation_output_bytes"], 34565330)
        self.assertEqual(tiers["regional_split_probe"]["hazard_output_file_count"], 57)
        self.assertEqual(tiers["regional_split_probe"]["hazard_output_bytes"], 57670915)
        self.assertEqual(tiers["regional_split_probe"]["collector_wall_seconds"], 5.261369686049875)
        self.assertEqual(tiers["regional_split_probe"]["memory_peak_mb"], 172.921875)
        self.assertEqual(tiers["regional_split_probe"]["metrics_contract_status"], "complete")
        self.assertEqual(tiers["regional_split_probe"]["preservation_status"], "ready_for_demonstration_evidence")
        self.assertEqual(tiers["regional_split_probe"]["required_run_root_entries_status"], "complete")
        self.assertEqual(tiers["regional_split_probe"]["output_family_status"], "sufficient")
        self.assertEqual(tiers["regional_split_probe"]["output_budget_audit_status"], "blocked_missing_replay_artifacts")
        self.assertEqual(tiers["regional_split_probe"]["output_budget_blocker_category"], "replay_critical_budget_template")
        self.assertEqual(tiers["regional_split_probe"]["next_recommended_action"], "compare_measured_regional_split_against_scenario_and_output_projections")
        self.assertEqual(tiers["regional_split_probe"]["next_evidence_field"], "regional_split_projection_delta_summary")
        self.assertEqual(tiers["regional_split_probe"]["supersedes_failed_closed_task"], "TB-432")
        self.assertEqual(tiers["regional_split_probe"]["superseded_failed_closed_source_report"], "docs/balfrin_regional_split_probe_gate_tb432.md")
        self.assertEqual(tiers["regional_split_probe"]["supersedes_regional_split_source_report"], "docs/balfrin_regional_split_run_root_metrics_tb448.md")
        self.assertIn("replay-critical budget blockers", tiers["regional_split_probe"]["next_recommended_action_reason"])

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
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["latest_no_submit_task"], "TB-405")
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["latest_balfrin_access_preflight_status"],
            "not_supplied",
        )
        self.assertEqual(tiers["management_aoi_multi_zone_run"]["latest_scheduler_submission_status"], "not_attempted")
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["first_persistent_unblock_action"],
            "thread the adjacent-candidate review bundle through scenario regeneration and prepared-pilot compilation instead of repeating the old source-zone-overlap repair",
        )
        self.assertEqual(
            tiers["management_aoi_multi_zone_run"]["next_evidence_field"],
            "adjacent_candidate_scenario_table",
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
        self.assertIn("regional_split_probe", text)
        self.assertIn("swiss_scale_feasibility_projection:", text)
        self.assertIn("current_practical_ceiling: 10-zone single-AOI", text)
        self.assertIn("first_bottleneck: reducer_pressure_and_replay_metadata_growth", text)
        self.assertIn("regional_split_projection_delta_summary:", text)
        self.assertIn("failed_closed_tiers: management_aoi_multi_zone_run", text)
        self.assertIn("hazard_execution_status: no_hazard_execution", text)
        self.assertIn(
            "next_recommended_scaling_task: summarize_multi_zone_reducer_pressure",
            text,
        )
        self.assertIn("next_probe_class=summarize_multi_zone_reducer_pressure", text)
        self.assertIn("next_blocker_category: replay_critical_budget_template", text)
        self.assertIn("TB-407", text)
        self.assertIn("TB-565", text)
        self.assertIn("TB-566", text)
        self.assertIn("adjacent-candidate review bundle", text)
        self.assertIn("projected_larger_aoi", text)

    def test_completed_diagnostic_run_record_enters_scale_matrix_as_measured_tier(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            record_path = Path(tmpdir) / "run_record.json"
            record_path.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_16_zone_simplified_20260525",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525",
                        "git_head": "665971e",
                        "job_id": "4367731",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 16},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:01.24", "max_rss_mb": 34.066},
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
                ),
                encoding="utf-8",
            )

            with mock.patch.object(MODULE.evidence_bundle, "DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORD", record_path):
                report = MODULE.build_report()

        row = next(row for row in report["tiers"] if row["tier_id"] == "diagnostic_16_zone_reducer_pressure")
        self.assertIn("diagnostic_16_zone_reducer_pressure", report["measured_tiers"])
        self.assertEqual(row["evidence_label"], "measured_on_balfrin")
        self.assertEqual(row["measurement_status"], "measured_diagnostic_reducer_pressure")
        self.assertEqual(row["job_id"], "4367731")
        self.assertEqual(row["run_root"], "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525")
        self.assertEqual(row["release_zone_count"], 16)
        self.assertEqual(row["diagnostic_output_file_count"], 52)
        self.assertEqual(row["diagnostic_output_bytes"], 23661)
        self.assertEqual(row["runtime_seconds"], 3.07)
        self.assertEqual(row["memory_peak_mb"], 34.066)
        self.assertEqual(row["simultaneous_release_zone_batch_max"], 16)
        self.assertEqual(row["simultaneous_release_zone_batch_max_source"], "diagnostic_single_node_postproc")
        self.assertEqual(row["next_diagnostic_release_zone_count"], 24)
        self.assertEqual(row["next_recommended_action"], "run_balfrin_diagnostic_24_zone")
        self.assertEqual(row["next_blocker_category"], "next_diagnostic_size_not_measured")
        self.assertEqual(report["diagnostic_single_node_postproc_ceiling"]["status"], "measured")
        self.assertEqual(
            report["diagnostic_single_node_postproc_ceiling"]["simultaneous_release_zone_batch_max"],
            16,
        )

    def test_32_zone_diagnostic_run_record_becomes_latest_diagnostic_tier(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            record_16 = tmp / "run_record_16.json"
            record_24 = tmp / "run_record_24.json"
            record_32 = tmp / "run_record_32.json"
            record_40 = tmp / "run_record_40.json"
            record_100 = tmp / "run_record_100.json"
            record_16.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_16_zone_simplified_20260525",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525",
                        "git_head": "665971e",
                        "job_id": "4367731",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 16},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:01.24", "max_rss_mb": 34.066},
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
                ),
                encoding="utf-8",
            )
            record_24.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_24_zone_simplified_next",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next",
                        "git_head": "d6863e2",
                        "job_id": "4368588",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 24},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:01.55", "max_rss_mb": 33.711},
                            "pressure_report": {
                                "status": "measured_scratch_root",
                                "release_zone_count": 24,
                                "output_file_count": 76,
                                "output_byte_count": 32904,
                                "manifest_size_bytes": 20170,
                                "root_file_count": 81,
                                "reducer_wall_time_seconds": 4.03,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            record_32.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_32_zone_tb599_20260526",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_32_zone_tb599_20260526",
                        "git_head": "ac1aed4",
                        "job_id": "4372124",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 32},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:00.75", "max_rss_mb": 34.168},
                            "pressure_report": {
                                "status": "measured_scratch_root",
                                "release_zone_count": 32,
                                "output_file_count": 100,
                                "output_byte_count": 42221,
                                "manifest_size_bytes": 24514,
                                "root_file_count": 105,
                                "reducer_wall_time_seconds": 5.39,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            record_40.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_40_zone_tb601_20260526",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_40_zone_tb601_20260526",
                        "git_head": "9800260",
                        "job_id": "4372257",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 40},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:01.40", "max_rss_mb": 33.902},
                            "pressure_report": {
                                "status": "measured_scratch_root",
                                "release_zone_count": 40,
                                "output_file_count": 124,
                                "output_byte_count": 51493,
                                "manifest_size_bytes": 28818,
                                "root_file_count": 129,
                                "reducer_wall_time_seconds": 6.35,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            record_100.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "run_id": "diagnostic_100_zone_tb611_20260526",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526",
                        "git_head": "4b335c0",
                        "job_id": "4372447",
                        "terminal_state": "COMPLETED",
                        "diagnostic_shape": {"release_zone_count": 100},
                        "collection": {
                            "status": "complete",
                            "time_verbose": {"elapsed": "0:01.26", "max_rss_mb": 34.16},
                            "pressure_report": {
                                "status": "measured_scratch_root",
                                "release_zone_count": 100,
                                "output_file_count": 304,
                                "output_byte_count": 121172,
                                "manifest_size_bytes": 61119,
                                "root_file_count": 309,
                                "reducer_wall_time_seconds": 13.55,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(MODULE.evidence_bundle, "DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORD", record_100),
                mock.patch.object(
                    MODULE.evidence_bundle,
                    "DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORDS",
                    (record_100, record_40, record_32, record_24, record_16),
                ),
            ):
                report = MODULE.build_report()

        row = next(row for row in report["tiers"] if row["tier_id"] == "diagnostic_100_zone_reducer_pressure")
        comparison = report["diagnostic_performance_comparison"]

        self.assertIn("diagnostic_100_zone_reducer_pressure", report["measured_tiers"])
        self.assertEqual(row["job_id"], "4372447")
        self.assertEqual(row["release_zone_count"], 100)
        self.assertEqual(row["diagnostic_output_file_count"], 304)
        self.assertEqual(row["diagnostic_output_bytes"], 121172)
        self.assertIsNone(row["next_diagnostic_release_zone_count"])
        self.assertEqual(
            row["next_recommended_action"],
            "promote_diagnostic_series_then_measure_hazard_throughput_or_scientific_validation",
        )
        self.assertEqual(row["next_blocker_category"], "scientific_validation_and_hazard_throughput")
        self.assertEqual(report["diagnostic_single_node_postproc_ceiling"]["simultaneous_release_zone_batch_max"], 100)
        self.assertIn("100-zone diagnostic", report["swiss_scale_feasibility_projection"]["current_practical_ceiling"])
        self.assertEqual(
            report["swiss_scale_feasibility_projection"]["feasibility_classes"]["24_zone"]["class"],
            "measured_repeatable_diagnostic_postproc",
        )
        self.assertEqual(
            report["swiss_scale_feasibility_projection"]["feasibility_classes"]["32_zone"]["class"],
            "measured_diagnostic_postproc",
        )
        self.assertEqual(
            report["swiss_scale_feasibility_projection"]["feasibility_classes"]["40_zone"]["class"],
            "measured_diagnostic_postproc",
        )
        self.assertEqual(
            report["swiss_scale_feasibility_projection"]["feasibility_classes"]["100_zone"]["class"],
            "measured_diagnostic_postproc",
        )
        self.assertEqual(
            report["swiss_scale_feasibility_projection"]["feasibility_classes"]["100_zone"]["next_blocker"],
            "scientific_validation_and_hazard_throughput",
        )
        self.assertEqual(comparison["status"], "measured")
        self.assertEqual(comparison["latest_diagnostic_release_zone_count"], 100)
        self.assertEqual(
            [item["tier_id"] for item in comparison["diagnostic_rows"]],
            [
                "diagnostic_16_zone_reducer_pressure",
                "diagnostic_24_zone_reducer_pressure",
                "diagnostic_32_zone_reducer_pressure",
                "diagnostic_40_zone_reducer_pressure",
                "diagnostic_100_zone_reducer_pressure",
            ],
        )
        self.assertIn("regional_split_probe", [item["tier_id"] for item in comparison["comparison_rows"]])
        self.assertIn("historical_regional_split_probe", [item["tier_id"] for item in comparison["comparison_rows"]])

    def test_repeatability_summary_reports_bounds_for_same_size_diagnostics(self) -> None:
        def record(
            *,
            run_id: str,
            job_id: str,
            max_rss_mb: float,
            output_bytes: int,
            manifest_size_bytes: int,
        ) -> dict[str, object]:
            return {
                "schema_version": "balfrin_diagnostic_run_record_v1",
                "status": "completed",
                "run_id": run_id,
                "run_root": f"/scratch/mch/olifu/rust_rockfall/diagnostics/{run_id}",
                "git_head": "5f9c937",
                "job_id": job_id,
                "terminal_state": "COMPLETED",
                "diagnostic_shape": {"release_zone_count": 24},
                "collection": {
                    "status": "complete",
                    "time_verbose": {"elapsed": "0:00.34", "max_rss_mb": max_rss_mb},
                    "pressure_report": {
                        "status": "measured_scratch_root",
                        "release_zone_count": 24,
                        "output_file_count": 76,
                        "output_byte_count": output_bytes,
                        "manifest_size_bytes": manifest_size_bytes,
                        "root_file_count": 81,
                        "reducer_wall_time_seconds": 4.03,
                    },
                },
            }

        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            record_a = tmp / "repeatability_a.json"
            record_b = tmp / "repeatability_b.json"
            record_a.write_text(
                json.dumps(
                    record(
                        run_id="diagnostic_24_zone_repeatability_a_tb581",
                        job_id="4368592",
                        max_rss_mb=34.242,
                        output_bytes=32922,
                        manifest_size_bytes=20218,
                    )
                ),
                encoding="utf-8",
            )
            record_b.write_text(
                json.dumps(
                    record(
                        run_id="diagnostic_24_zone_repeatability_b_tb581",
                        job_id="4368593",
                        max_rss_mb=39.879,
                        output_bytes=32922,
                        manifest_size_bytes=20218,
                    )
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                MODULE.evidence_bundle,
                "DEFAULT_BALFRIN_24_ZONE_REPEATABILITY_RUN_RECORDS",
                (record_a, record_b),
            ):
                report = MODULE.build_report()

        repeatability = report["diagnostic_repeatability_summary"]
        self.assertEqual(repeatability["status"], "measured_repeatability_pair")
        self.assertEqual(repeatability["release_zone_count"], 24)
        self.assertEqual(repeatability["run_count"], 2)
        self.assertEqual([row["job_id"] for row in repeatability["rows"]], ["4368592", "4368593"])
        self.assertEqual(repeatability["bounds"]["reducer_wall_time_seconds"]["min"], 4.03)
        self.assertEqual(repeatability["bounds"]["reducer_wall_time_seconds"]["max"], 4.03)
        self.assertEqual(repeatability["bounds"]["memory_peak_mb"]["min"], 34.242)
        self.assertEqual(repeatability["bounds"]["memory_peak_mb"]["max"], 39.879)
        self.assertEqual(repeatability["bounds"]["output_file_count"]["spread"], 0.0)
        self.assertEqual(repeatability["bounds"]["output_bytes"]["median"], 32922.0)

    def test_cli_emits_json_and_text_reports(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "text"])
        self.assertEqual(exit_code, 0)
        self.assertIn("matrix_status:", buffer.getvalue())
        self.assertIn("operational_readiness_check:", buffer.getvalue())
        self.assertIn("phase_change_decision_check:", buffer.getvalue())
        self.assertIn("first_next_action:", buffer.getvalue())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "json"])
        self.assertEqual(exit_code, 0)
        self.assertIn('"schema_version": "balfrin_scale_readiness_matrix_v1"', buffer.getvalue())

    def test_absent_reducer_ladder_artifacts_emit_blocked_matrix_json(self) -> None:
        MODULE._multi_zone_reducer_pressure_report.cache_clear()
        missing = FileNotFoundError(
            2,
            "No such file or directory",
            "/tmp/rust_rockfall/balfrin_scale_readiness_matrix_v1/reducer_pressure/output",
        )
        with mock.patch.object(MODULE.reducer_pressure, "build_manifest_pressure_ladder_report", side_effect=missing):
            report = MODULE.build_report()

        MODULE._multi_zone_reducer_pressure_report.cache_clear()
        self.assertEqual(report["matrix_status"], "blocked_missing_inputs")
        self.assertEqual(report["blocked_reason"], "reducer_pressure_scratch_root_missing")
        projection = report["regional_split_projection_delta_summary"]
        self.assertEqual(projection["measurement_status"], "blocked_missing_reducer_pressure_scratch_root")
        self.assertEqual(
            projection["reducer_pressure_projection_surface"]["measurement_status"],
            "blocked_missing_scratch_root",
        )
        self.assertIn("--materialize-root", projection["reducer_pressure_projection_surface"]["recovery_command"])
        self.assertIn("multi_zone_reducer_pressure_report", report["recovery_commands"])

    def test_operational_readiness_check_classifies_diagnostic_only_state(self) -> None:
        check = MODULE.build_operational_readiness_check(
            {
                "scientific_validation": {"status": "blocked", "first_missing_input": "validation_package"},
                "reproducibility": {"status": "partial", "first_missing_input": "replay_artifacts"},
                "gis_package_qa": {"status": "blocked", "first_missing_input": "gis_review"},
                "provenance": {"status": "partial", "first_missing_input": "provenance"},
                "monitoring": {"status": "partial", "first_missing_input": "monitoring"},
                "versioning": {"status": "pass"},
                "support_status": {"status": "blocked", "first_missing_input": "support_statement"},
            }
        )

        self.assertEqual(check["readiness_status"], "diagnostic_only_not_operational")
        self.assertFalse(check["operational_candidate_allowed"])
        self.assertEqual(check["first_missing_input"], "validation_package")

    def test_operational_readiness_check_classifies_review_ready_state(self) -> None:
        inputs = {
            criterion["criterion"]: {"status": "pass"}
            for criterion in MODULE.OPERATIONAL_READINESS_REQUIREMENTS
        }
        inputs["monitoring"] = {"status": "partial", "first_missing_input": "monitoring_response_plan"}
        inputs["support_status"] = {"status": "blocked", "first_missing_input": "support_statement"}

        check = MODULE.build_operational_readiness_check(inputs)

        self.assertEqual(check["readiness_status"], "review_ready_not_operational")
        self.assertFalse(check["operational_candidate_allowed"])
        self.assertEqual(check["failing_criteria"], ["monitoring", "support_status"])

    def test_operational_readiness_check_classifies_operational_candidate_state(self) -> None:
        inputs = {
            criterion["criterion"]: {"status": "pass"}
            for criterion in MODULE.OPERATIONAL_READINESS_REQUIREMENTS
        }

        check = MODULE.build_operational_readiness_check(inputs)

        self.assertEqual(check["readiness_status"], "operational_candidate_ready")
        self.assertTrue(check["operational_candidate_allowed"])
        self.assertEqual(check["failing_criteria"], [])

    def test_phase_change_decision_check_ranks_scientific_evidence_first(self) -> None:
        check = MODULE.build_phase_change_decision_check(
            operational_readiness_check={
                "readiness_status": "diagnostic_only_not_operational",
                "first_missing_input": "scientific_validation",
            },
            physical_probability_readiness_check={
                "physical_probability_claims_allowed": False,
                "first_blocking_evidence_class": "source_frequency_evidence",
            },
            swiss_wide_phase_change_readiness={
                "phase_change_status": "deferred",
                "first_missing_input": "national_public_geodata_inventory",
            },
            non_postproc_readiness={
                "readiness_status": "deferred_no_policy_or_execution_model_need",
                "next_blocker": "partition_policy",
            },
            distributed_execution_contract={
                "distributed_execution_authorized": False,
            },
            local_distributed_orchestration_dry_run={
                "remaining_cluster_side_blockers": ["scheduler submission missing"],
            },
        )

        self.assertEqual(check["decision_status"], "blocked_or_deferred")
        self.assertEqual(check["blocked_or_deferred_classes"][0], "physical_probability")
        self.assertEqual(
            check["first_scientifically_useful_next_action"]["next_task"],
            "stage_source_frequency_release_probability_block_population_and_holdout_validation_evidence",
        )
        self.assertEqual(check["ranked_next_actions"][1]["readiness_class"], "swiss_wide")
        self.assertFalse(check["phase_change_authorized"])

    def test_phase_change_decision_check_can_reach_review_ready_without_authorizing(self) -> None:
        check = MODULE.build_phase_change_decision_check(
            operational_readiness_check={
                "readiness_status": "operational_candidate_ready",
                "first_missing_input": None,
            },
            physical_probability_readiness_check={
                "physical_probability_claims_allowed": True,
                "first_blocking_evidence_class": "",
            },
            swiss_wide_phase_change_readiness={
                "phase_change_status": "ready_for_phase_change_review",
                "first_missing_input": None,
            },
            non_postproc_readiness={
                "readiness_status": "ready_to_request_non_postproc_phase_change",
                "next_blocker": None,
            },
            distributed_execution_contract={
                "distributed_execution_authorized": True,
            },
            local_distributed_orchestration_dry_run={
                "remaining_cluster_side_blockers": [],
            },
        )

        self.assertEqual(check["decision_status"], "ready_for_phase_change_review")
        self.assertEqual(check["blocked_or_deferred_classes"], [])
        self.assertEqual(check["ranked_next_actions"], [])
        self.assertIsNone(check["first_scientifically_useful_next_action"])
        self.assertFalse(check["phase_change_authorized"])


if __name__ == "__main__":
    unittest.main()
