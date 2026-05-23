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

    def test_recommendations_include_dependencies_and_boundaries(self) -> None:
        report = recommendation.build_report()

        for item in report["ranked_followups"]:
            self.assertTrue(item["dependency_status"])
            self.assertTrue(item["suggested_command"])
            self.assertTrue(item["claim_boundary"])
            self.assertTrue(item["expected_measurement"])

        boundaries = report["claim_boundaries"]
        self.assertFalse(boundaries["live_balfrin_access_required"])
        self.assertFalse(boundaries["distributed_execution_authorized"])
        self.assertFalse(boundaries["scale_up_authorized"])
        self.assertFalse(boundaries["physical_probability_claims_allowed"])
        self.assertFalse(boundaries["operational_claims_allowed"])
        self.assertFalse(boundaries["backlog_modified"])

    def test_text_report_names_tracks(self) -> None:
        text = recommendation.render_text_report(recommendation.build_report())

        self.assertIn("second_site_terrain_crop_extent_repair", text)
        self.assertIn("conditional_layer_interpretation_gate", text)
        self.assertIn("holdout_calibration_guardrail_integration", text)
        self.assertIn("scale_up_authorized: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
