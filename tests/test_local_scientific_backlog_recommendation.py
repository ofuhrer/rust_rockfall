from __future__ import annotations

import unittest

from scripts import recommend_local_scientific_backlog as recommendation


class LocalScientificBacklogRecommendationTests(unittest.TestCase):
    def test_report_ranks_local_followups(self) -> None:
        report = recommendation.build_report()

        self.assertEqual(report["schema_version"], recommendation.SCHEMA_VERSION)
        self.assertEqual(report["recommendation_status"], "ready")
        self.assertGreaterEqual(len(report["ranked_followups"]), 5)
        self.assertEqual(report["ranked_followups"][0]["track_id"], "second_site_terrain_crop_extent_repair")
        self.assertEqual(report["ranked_followups"][2]["track_id"], "extreme_layer_support_nodata_drilldown")
        self.assertEqual(report["source_report_statuses"]["denominator"], "complete")
        self.assertEqual(report["source_report_statuses"]["traceability"], "traceable")
        self.assertEqual(report["source_report_statuses"]["sensitivity"], "measured")
        self.assertEqual(
            report["local_map_interpretation_gate"]["gate_status"],
            "ready_for_conditional_map_interpretation",
        )
        self.assertIn(
            "audit_conditional_denominator_provenance.py",
            report["local_map_interpretation_gate"]["required_command"],
        )
        self.assertEqual(report["next_command_coverage"]["coverage_status"], "ready")
        self.assertEqual(
            report["next_command_coverage"]["entries_with_next_command"],
            len(report["ranked_followups"]),
        )

    def test_recommendations_include_dependencies_and_boundaries(self) -> None:
        report = recommendation.build_report()

        for item in report["ranked_followups"]:
            self.assertTrue(item["dependency_status"])
            self.assertTrue(item["suggested_command"])
            self.assertTrue(item["next_executable_command"])
            self.assertTrue(item["claim_boundary"])
            self.assertTrue(item["expected_measurement"])
            self.assertEqual(item["next_execution"]["command"], item["next_executable_command"])
            self.assertEqual(item["next_execution"]["expected_artifact_or_measurement"], item["expected_artifact_or_measurement"])
            self.assertTrue(item["next_execution"]["local_only"])
            self.assertTrue(item["next_execution"]["repo_checkout_executable"])
            self.assertFalse(item["next_execution"]["placeholder_command"])
            self.assertTrue(item["next_execution"]["measurement_required"])
            self.assertNotIn(str(recommendation.ROOT), item["next_executable_command"])

        boundaries = report["claim_boundaries"]
        self.assertFalse(boundaries["live_balfrin_access_required"])
        self.assertFalse(boundaries["distributed_execution_authorized"])
        self.assertFalse(boundaries["scale_up_authorized"])
        self.assertFalse(boundaries["physical_probability_claims_allowed"])
        self.assertFalse(boundaries["operational_claims_allowed"])
        self.assertFalse(boundaries["backlog_modified"])

        gate_boundaries = report["local_map_interpretation_gate"]["claim_boundaries"]
        self.assertTrue(gate_boundaries["conditional_diagnostic_interpretation_only"])
        self.assertFalse(gate_boundaries["physical_probability_claims_allowed"])

    def test_next_command_coverage_fails_closed_for_missing_or_placeholder_commands(self) -> None:
        coverage = recommendation.build_next_command_coverage(
            recommendation.attach_next_execution_plans(
                [
                    {
                        "track_id": "missing_command",
                        "suggested_command": "",
                        "expected_measurement": "measurement",
                    },
                    {
                        "track_id": "placeholder_command",
                        "suggested_command": "PYENV_VERSION=system uv run python scripts/<placeholder>.py",
                        "expected_measurement": "",
                    },
                ]
            )
        )

        self.assertEqual(coverage["coverage_status"], "blocked_incomplete_next_execution")
        self.assertIn("missing_command", coverage["missing_command_track_ids"])
        self.assertIn("placeholder_command", coverage["placeholder_command_track_ids"])
        self.assertIn("placeholder_command", coverage["missing_measurement_track_ids"])

    def test_interpretation_gate_fails_closed_on_missing_evidence(self) -> None:
        gate = recommendation.build_local_map_interpretation_gate(
            {
                "audit_status": "blocked_missing_denominator_evidence",
                "missing_evidence": ["missing denominator"],
                "next_local_follow_up": "repair denominator command",
            },
            {
                "audit_status": "blocked_missing_traceability",
                "missing_or_failed_checks": ["hazard_deposition_density_layer"],
                "next_local_follow_up": "repair traceability command",
            },
        )

        self.assertEqual(gate["gate_status"], "blocked_missing_interpretation_evidence")
        self.assertEqual([item["audit"] for item in gate["failing_evidence"]], [
            "conditional_denominator_provenance",
            "trajectory_deposition_traceability",
        ])
        self.assertEqual(gate["next_local_recovery_command"], "repair denominator command")

    def test_text_report_names_tracks(self) -> None:
        text = recommendation.render_text_report(recommendation.build_report())

        self.assertIn("second_site_terrain_crop_extent_repair", text)
        self.assertIn("conditional_layer_interpretation_gate", text)
        self.assertIn("local_map_interpretation_gate:", text)
        self.assertIn("next_command_coverage:", text)
        self.assertIn("next_executable_command:", text)
        self.assertIn("expected_artifact_or_measurement:", text)
        self.assertIn("ready_for_conditional_map_interpretation", text)
        self.assertIn("holdout_calibration_guardrail_integration", text)
        self.assertIn("scale_up_authorized: False", text)

    def test_progress_report_is_available_through_existing_command_module(self) -> None:
        report = recommendation.build_progress_report()

        self.assertEqual(report["schema_version"], "local_scientific_progress_summary_v1")
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])
        self.assertEqual(report["ranked_local_tracks"][0]["track_id"], "conditional_denominator_provenance")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
