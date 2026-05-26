from __future__ import annotations

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_management_demo_package.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_management_demo_package", SCRIPT_PATH)
assert SPEC is not None
package = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(package)


class BalfrinManagementDemoPackageTests(unittest.TestCase):
    def test_current_package_report_keeps_measured_and_fixture_backed_sections_distinct(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        report = package.build_report(run_root=run_root, artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"))

        self.assertEqual(report["schema_version"], "balfrin_management_demo_package_v1")
        self.assertEqual(report["package_status"], "mixed_provenance")
        self.assertEqual(report["package_provenance_status"], "mixed_provenance")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 10,
                "fixture_backed": 1,
                "unavailable": 2,
                "blocked_missing_inputs": 1,
                "projection_only": 1,
                "failed_closed": 1,
                "deferred": 1,
            },
        )
        self.assertEqual(report["replay_section"]["status"], "replayable")
        self.assertEqual(report["replay_section"]["run_root_provenance"], "fixture_backed")
        self.assertEqual(report["target_area_aoi_automation_section"]["status"], "template_only")
        self.assertEqual(report["target_area_aoi_automation_section"]["evidence_type"], "unavailable")
        self.assertEqual(report["target_area_release_scenario_section"]["status"], "template_only")
        self.assertEqual(report["target_area_probe_metrics_section"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["target_area_canonical_bundle_section"]["status"], "measured")
        self.assertEqual(report["runtime_section"]["status"], "measured")
        self.assertEqual(report["restartability_section"]["status"], "measured")
        self.assertEqual(report["gis_scope_section"]["status"], "full_scope")
        self.assertEqual(report["uncertainty_section"]["status"], "measured")
        self.assertEqual(report["claim_boundary_section"]["status"], "guarded")
        self.assertEqual(report["scaling_section"]["status"], "measured")
        self.assertEqual(report["diagnostic_performance_section"]["status"], "measured")
        self.assertEqual(report["diagnostic_performance_section"]["latest_diagnostic"]["job_id"], "4372447")
        self.assertEqual(report["diagnostic_performance_section"]["latest_diagnostic"]["release_zone_count"], 100)
        self.assertEqual(report["diagnostic_performance_section"]["repeatability_pair"]["status"], "measured_repeatability_pair")
        self.assertEqual(report["diagnostic_performance_section"]["repeatability_pair"]["bounds"]["reducer_wall_time_seconds"]["spread"], 0.0)
        self.assertEqual(report["physical_credibility_section"]["status"], "measured_diagnostic_only")
        self.assertEqual(report["physical_credibility_section"]["physical_credibility_state"], "no_physical_evidence")
        self.assertEqual(report["swiss_wide_extension_section"]["status"], "no_go_extrapolated_beyond_measured_evidence")
        self.assertEqual(
            report["swiss_wide_extension_section"]["no_go_labels"],
            ["aoi_count_exceeds_measured_support", "total_job_count_exceeds_measured_single_job_support"],
        )
        self.assertEqual(report["swiss_scale_feasibility_projection_section"]["status"], "projection_only")
        self.assertEqual(report["swiss_scale_feasibility_projection_section"]["projection_classification"]["10_zone"], "hazard_planning_boundary")
        self.assertEqual(
            report["swiss_scale_feasibility_projection_section"]["projection_classification"]["24_zone"],
            "measured_repeatable_diagnostic_postproc",
        )
        self.assertEqual(report["swiss_scale_feasibility_projection_section"]["projection_classification"]["regional_split_probe"], "measured")
        self.assertEqual(
            report["swiss_scale_feasibility_projection_section"]["upstream_data_blockers"],
            ["source_frequency", "calibration_holdout", "physical_probability_evidence"],
        )
        self.assertEqual(
            report["swiss_scale_feasibility_projection_section"]["top_blockers"],
            [
                "scientific_evidence",
                "hazard_throughput",
                "reducer_pressure",
                "output_bytes",
            ],
        )
        self.assertEqual(report["failed_closed_section"]["status"], "failed_closed")
        self.assertIn("TB-432 is still historical failed-closed/no-submit regional split evidence", report["failed_closed_section"]["summary"])
        self.assertEqual(report["next_decision_section"]["evidence_type"], "deferred")
        self.assertTrue(report["scaling_section"]["single_job_sufficient_for_next_step"])
        self.assertFalse(report["scaling_section"]["scale_up_authorized"])
        self.assertEqual(report["next_decision_section"]["status"], "deferred")
        self.assertEqual(report["next_decision_section"]["recommended_next_authorized_step"], "management review of this package")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertIn("replay is fixture-backed", report["package_summary"]["summary"])
        self.assertIn("AOI automation is template-only", report["package_summary"]["summary"])
        self.assertIn("Swiss-scale feasibility is projection-only", report["package_summary"]["summary"])
        self.assertIn("failed closed before live execution", report["package_summary"]["summary"])
        self.assertIn("100-zone is measured diagnostic postproc reducer-pressure evidence", report["swiss_scale_feasibility_projection_section"]["summary"])
        self.assertIn("scientific evidence", report["swiss_scale_feasibility_projection_section"]["summary"])
        self.assertIn("adjacent-candidate review bundle", report["failed_closed_section"]["summary"])
        self.assertIn("next authorized step is management review", report["package_summary"]["summary"])
        self.assertEqual(len(report["regeneration_commands"]), 5)
        self.assertIn("summarize_balfrin_management_demo_package.py", report["regeneration_commands"][-1])
        self.assertIn("section_provenance_profile:", package.render_text_report(report))
        self.assertIn("next_decision_section:", package.render_text_report(report))
        self.assertIn("target_area_aoi_automation_section:", package.render_text_report(report))
        self.assertIn("swiss_wide_extension_section:", package.render_text_report(report))
        self.assertIn("swiss_scale_feasibility_projection_section:", package.render_text_report(report))
        self.assertIn("diagnostic_performance_section:", package.render_text_report(report))
        self.assertIn("failed_closed_section:", package.render_text_report(report))

    def test_readiness_matrix_tracks_required_gates_and_claim_boundaries(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        report = package.build_report(
            run_root=run_root,
            artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            balfrin_access_preflight={
                "status": "ready_for_read_only_collection",
                "ready_for_pre_submit": True,
                "remote_head": "reviewed-head",
                "remote_checkout_hygiene": {"status": "pass", "dirty_path_count": 0},
                "live_submission_authorized": False,
            },
        )
        matrix = report["readiness_matrix"]

        self.assertEqual(matrix["schema_version"], "balfrin_full_scale_readiness_matrix_v1")
        self.assertEqual(matrix["status"], "blocked")
        self.assertEqual(matrix["clean_checkout_probe"]["status"], "blocked_missing_run_root")
        self.assertEqual(matrix["recommended_next_milestone"]["recommendation"], "reducer-pressure optimization")
        self.assertEqual(matrix["recommended_next_milestone"]["source_action_id"], "reducer_pressure_optimization")
        self.assertEqual(matrix["current_evidence"]["balfrin_access_status"], "ready_for_read_only_collection")
        self.assertEqual(matrix["current_evidence"]["balfrin_remote_head"], "reviewed-head")

        gates = {row["gate"] for row in matrix["rows"]}
        self.assertEqual(
            gates,
            {
                "measured_multi_zone_execution",
                "regional_split_projection_comparison",
                "diagnostic_performance_repeatability",
                "preservation_gate",
                "reducer_constraints",
                "scenario_batching_cap",
                "candidate_stability",
                "output_budget",
                "restart_replay",
                "gis_package_scope",
                "command_plan_reproducibility",
                "clean_checkout_behavior",
                "scientific_claim_boundaries",
                "live_execution_authorization",
            },
        )
        statuses = {row["status"] for row in matrix["rows"]}
        self.assertIn("measured", statuses)
        self.assertIn("fixture_backed", statuses)
        self.assertIn("ready", statuses)
        self.assertIn("dry_run", statuses)
        self.assertIn("blocked", statuses)
        self.assertIn("unauthorized", statuses)

        command_plan_row = next(row for row in matrix["rows"] if row["gate"] == "command_plan_reproducibility")
        self.assertEqual(command_plan_row["evidence_status"], "dry_run")
        measured_multi_zone_row = next(row for row in matrix["rows"] if row["gate"] == "measured_multi_zone_execution")
        self.assertEqual(measured_multi_zone_row["status"], "measured")
        self.assertEqual(measured_multi_zone_row["evidence_status"], "measured")
        self.assertEqual(measured_multi_zone_row["current_evidence"]["job_id"], "4347579")
        self.assertEqual(measured_multi_zone_row["current_evidence"]["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertEqual(measured_multi_zone_row["current_evidence"]["validation_output_file_count"], 130)
        self.assertEqual(measured_multi_zone_row["current_evidence"]["hazard_output_file_count"], 53)
        self.assertEqual(measured_multi_zone_row["current_evidence"]["metrics_contract_status"], "complete")
        self.assertEqual(measured_multi_zone_row["current_evidence"]["preservation_status"], "ready_for_demonstration_evidence")
        self.assertIn("TB-407", measured_multi_zone_row["summary"])
        regional_split_row = next(row for row in matrix["rows"] if row["gate"] == "regional_split_projection_comparison")
        self.assertEqual(regional_split_row["status"], "analysis_only")
        self.assertEqual(regional_split_row["evidence_status"], "measured")
        self.assertEqual(regional_split_row["current_evidence"]["classification"], "measured_regional_split_probe")
        self.assertEqual(regional_split_row["current_evidence"]["evidence_label"], "measured_on_balfrin")
        self.assertEqual(regional_split_row["current_evidence"]["job_id"], "4367244")
        self.assertEqual(regional_split_row["current_evidence"]["supersedes_failed_closed_task"], "TB-432")
        self.assertIn("comparison work", regional_split_row["summary"])
        diagnostic_row = next(row for row in matrix["rows"] if row["gate"] == "diagnostic_performance_repeatability")
        self.assertEqual(diagnostic_row["status"], "measured")
        self.assertEqual(diagnostic_row["gate_status"], "measured_repeatability_pair")
        self.assertEqual(diagnostic_row["current_evidence"]["latest_diagnostic"]["job_id"], "4372447")
        self.assertEqual(
            diagnostic_row["current_evidence"]["repeatability_pair"]["bounds"]["output_bytes"]["spread"],
            0,
        )
        scenario_row = next(row for row in matrix["rows"] if row["gate"] == "scenario_batching_cap")
        self.assertEqual(scenario_row["status"], "ready")
        self.assertEqual(scenario_row["evidence_status"], "scratch_local")
        self.assertEqual(scenario_row["current_evidence"]["scenario_batching_cap"], 8)
        self.assertEqual(scenario_row["current_evidence"]["prepared_pilot_smoke_status"], "ready")
        candidate_row = next(row for row in matrix["rows"] if row["gate"] == "candidate_stability")
        self.assertEqual(candidate_row["status"], "ready")
        self.assertEqual(candidate_row["evidence_status"], "scratch_local")
        self.assertEqual(
            candidate_row["current_evidence"]["selected_candidate_id"],
            "tschamut_public_lps_release_bbox_candidate_058",
        )
        self.assertEqual(candidate_row["current_evidence"]["selected_candidate_class"], "stable")
        clean_checkout_row = next(row for row in matrix["rows"] if row["gate"] == "clean_checkout_behavior")
        self.assertEqual(clean_checkout_row["evidence_status"], "blocked")
        self.assertIn("does not exist", clean_checkout_row["current_evidence"]["missing_run_root_reason"])

        self.assertFalse(matrix["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(matrix["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(matrix["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(matrix["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertIn("Full-scale Balfrin demonstration readiness remains blocked", matrix["summary"])
        self.assertNotIn("operational hazard map", matrix["summary"].lower())
        self.assertNotIn("annual-frequency", matrix["summary"].lower())
        self.assertNotIn("physical-probability", matrix["summary"].lower())
        self.assertNotIn("risk map", matrix["summary"].lower())
        self.assertIn("readiness_matrix:", package.render_text_report(report))

    def test_fixture_backed_override_stays_fixture_backed(self) -> None:
        report = package.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            evidence_override={"package_report": self.fixture_backed_package_report()},
        )

        self.assertEqual(report["package_status"], "fixture_backed")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 0,
                "fixture_backed": 16,
                "unavailable": 0,
                "blocked_missing_inputs": 0,
                "projection_only": 0,
                "failed_closed": 0,
                "deferred": 0,
            },
        )
        self.assertTrue(all(section["evidence_type"] == "fixture_backed" for section in report["section_provenance_profile"]))
        self.assertIn("fixture-backed", report["package_summary"]["summary"])
        self.assertEqual(report["replay_section"]["status"], "fixture_backed")

    def test_missing_inputs_block_the_package(self) -> None:
        report = package.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            evidence_override={"missing_inputs": ["replay_section"]},
        )

        self.assertEqual(report["package_status"], "blocked_missing_inputs")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 0,
                "fixture_backed": 0,
                "unavailable": 0,
                "blocked_missing_inputs": 17,
                "projection_only": 0,
                "failed_closed": 0,
                "deferred": 0,
            },
        )
        self.assertTrue(all(section["evidence_type"] == "blocked" for section in report["section_provenance_profile"]))
        self.assertEqual(report["missing_inputs"], ["replay_section"])
        self.assertIn("blocked because one or more required sections are missing", report["package_summary"]["summary"])

    def test_cli_writes_json_and_text_package_artifacts(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_management_demo_package_v1"
            evidence_path = Path(tmpdir) / "fixture_backed_evidence.json"
            evidence_path.write_text(
                json.dumps({"package_report": self.fixture_backed_package_report()}),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = package.main(
                    [
                        "--run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--evidence-json",
                        str(evidence_path),
                        "--json-output",
                        str(artifact_dir / "balfrin_management_demo_package_v1.json"),
                        "--text-output",
                        str(artifact_dir / "balfrin_management_demo_package_v1.txt"),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["schema_version"], "balfrin_management_demo_package_v1")
            self.assertTrue((artifact_dir / "balfrin_management_demo_package_v1.json").exists())
            self.assertTrue((artifact_dir / "balfrin_management_demo_package_v1.txt").exists())
            self.assertEqual(report["replay_section"]["run_root_provenance"], "fixture_backed")
            self.assertIn("claim_boundary_section", package.render_text_report(report))
            self.assertIn("target_area_release_scenario_section", package.render_text_report(report))
            self.assertIn("swiss_wide_extension_section", package.render_text_report(report))

    def fixture_backed_package_report(self) -> dict[str, object]:
        report = copy.deepcopy(
            package.build_report(
                run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
                artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            )
        )
        report["package_status"] = "fixture_backed"
        report["package_provenance_status"] = "fixture_backed"
        report["package_summary"]["status"] = "fixture_backed"
        report["package_summary"]["summary"] = "fixture-backed management package."
        report["package_summary"]["section_counts"] = {
            "measured": 0,
            "fixture_backed": 16,
            "unavailable": 0,
            "blocked_missing_inputs": 0,
            "projection_only": 0,
            "failed_closed": 0,
            "deferred": 0,
        }
        report["section_provenance_profile"] = [
            {**section, "status": "fixture_backed", "evidence_type": "fixture_backed"}
            for section in report["section_provenance_profile"]
        ]
        for key in (
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
            "physical_credibility_section",
            "swiss_wide_extension_section",
            "swiss_scale_feasibility_projection_section",
            "failed_closed_section",
            "next_decision_section",
        ):
            if isinstance(report.get(key), dict):
                report[key]["status"] = "fixture_backed"
                report[key]["evidence_type"] = "fixture_backed"
        return report


if __name__ == "__main__":
    unittest.main()
