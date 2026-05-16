from __future__ import annotations

import unittest

from scripts import map_physical_credibility_evidence_requirements as helper


class PhysicalCredibilityEvidenceRequirementsTest(unittest.TestCase):
    def test_json_shape_and_current_statuses(self) -> None:
        report = helper.build_report()

        expected_keys = {
            "schema_version",
            "physical_credibility_requirements_status",
            "current_physical_credibility_status",
            "calibration_status",
            "validation_status",
            "evidence_requirement_categories",
            "candidate_data_sources",
            "missing_acquisition_classes",
            "calibration_split_requirements",
            "holdout_validation_requirements",
            "source_frequency_requirements",
            "intensity_frequency_status",
            "claim_boundaries",
            "blocked_reason",
            "missing_inputs",
            "current_evidence_summary",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["physical_credibility_requirements_status"], "mapped_current_gaps")
        self.assertEqual(report["current_physical_credibility_status"], "not_established")
        self.assertEqual(report["calibration_status"], "missing")
        self.assertEqual(report["validation_status"], "partial")
        self.assertEqual(report["intensity_frequency_status"], "deferred_unsupported")
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])

    def test_requirement_categories_and_candidate_sources_are_distinct(self) -> None:
        report = helper.build_report()
        categories = {entry["category"]: entry for entry in report["evidence_requirement_categories"]}
        self.assertEqual(
            set(categories),
            {
                "observed_runout_deposition",
                "release_zone_evidence",
                "block_size_and_block_population_evidence",
                "terrain_and_context_evidence",
                "source_frequency_and_temporal_frequency_evidence",
                "calibration_data_and_objective_functions",
                "independent_holdout_validation",
                "multi_site_transfer_evidence",
            },
        )
        self.assertEqual(categories["observed_runout_deposition"]["current_repo_evidence_status"], "partial")
        self.assertEqual(categories["block_size_and_block_population_evidence"]["current_repo_evidence_status"], "missing")
        self.assertEqual(categories["independent_holdout_validation"]["current_repo_evidence_status"], "partial")
        self.assertTrue(categories["source_frequency_and_temporal_frequency_evidence"]["future_acquisition_classes"])
        self.assertIn(
            "independent_holdout_field_deposition_runout_benchmark",
            report["missing_acquisition_classes"],
        )
        self.assertIn("source_occurrence_temporal_frequency_catalogue", report["missing_acquisition_classes"])
        self.assertTrue(
            any(
                source["source_kind"] == "current_repo_evidence"
                and source["label"].startswith("Tschamut 2014")
                for source in report["candidate_data_sources"]
            )
        )
        self.assertTrue(
            any(
                source["source_kind"] == "future_acquisition_class"
                and source["label"] == "Historical rockfall event catalogue"
                for source in report["candidate_data_sources"]
            )
        )

    def test_text_output_names_required_evidence_categories(self) -> None:
        text = helper.render_text_report(helper.build_report())
        self.assertIn("Tschamut", text)
        self.assertIn("Chant Sura", text)
        self.assertIn("block_size_and_block_population_evidence", text)
        self.assertIn("source_frequency_and_temporal_frequency_evidence", text)
        self.assertIn("independent_holdout_validation", text)

    def test_missing_inputs_return_blocked_status(self) -> None:
        report = helper.build_report({"missing_inputs": ["docs/missing.json"]})

        self.assertEqual(report["physical_credibility_requirements_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_physical_credibility_status"], "blocked_missing_inputs")
        self.assertEqual(report["calibration_status"], "blocked_missing_inputs")
        self.assertEqual(report["validation_status"], "blocked_missing_inputs")
        self.assertEqual(report["intensity_frequency_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
