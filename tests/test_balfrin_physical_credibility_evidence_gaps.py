from __future__ import annotations

import unittest

from scripts import summarize_balfrin_physical_credibility_evidence_gaps as helper


class BalfrinPhysicalCredibilityEvidenceGapsTests(unittest.TestCase):
    def test_measured_bundle_remains_diagnostic_only_and_not_physical_credibility(self) -> None:
        report = helper.build_report()

        self.assertEqual(report["schema_version"], helper.SCHEMA_VERSION)
        self.assertEqual(report["balfrin_evidence_gap_status"], "measured_diagnostic_only")
        self.assertEqual(report["balfrin_demo_evidence_status"], "measured")
        self.assertEqual(report["physical_credibility_state"], "no_physical_evidence")
        self.assertEqual(report["validation_calibration_state"]["physical_credibility_status"], "not_established")
        self.assertEqual(report["validation_calibration_state"]["calibration_status"], "missing")
        self.assertEqual(report["validation_calibration_state"]["validation_status"], "partial")
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])

        diagnostic = [row["requirement_key"] for row in report["diagnostic_reproducibility_only_requirements"]]
        missing = [row["requirement_key"] for row in report["missing_physical_requirements"]]
        self.assertEqual(
            diagnostic,
            [
                "observed_runout_deposition",
                "release_zone_evidence",
                "independent_holdout_validation",
            ],
        )
        self.assertEqual(
            missing,
            [
                "calibration_data_and_objective_functions",
                "multi_site_transfer_evidence",
                "block_size_and_block_population_evidence",
                "source_frequency_and_temporal_frequency_evidence",
            ],
        )
        self.assertTrue(report["diagnostic_reproducibility_evidence"])
        self.assertIn(
            "single_job_execution_summary",
            {row["section"] for row in report["diagnostic_reproducibility_evidence"]},
        )
        self.assertIn(
            "post_run_interpretation_gate_report",
            {row["section"] for row in report["diagnostic_reproducibility_evidence"]},
        )

    def test_blocked_missing_inputs_state_is_explicit(self) -> None:
        report = helper.build_report({"missing_inputs": ["docs/missing.json"]})

        self.assertEqual(report["balfrin_evidence_gap_status"], "blocked_missing_inputs")
        self.assertEqual(report["balfrin_demo_evidence_status"], "blocked_missing_inputs")
        self.assertEqual(report["physical_credibility_state"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertEqual(report["requirement_matrix"], [])
        self.assertEqual(report["diagnostic_reproducibility_only_requirements"], [])
        self.assertEqual(report["missing_physical_requirements"], [])
        self.assertEqual(report["validation_calibration_state"]["calibration_status"], "blocked_missing_inputs")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_override_can_expose_no_physical_evidence_state_without_changing_demo_measured_status(self) -> None:
        report = helper.build_report(
            {
                "balfrin_bundle_report": {
                    "bundle_status": "measured",
                    "bundle_provenance_status": "measured",
                    "bundle_summary": {
                        "bundle_status": "measured",
                        "section_counts": {"measured": 4, "fixture_backed": 0, "blocked_missing_inputs": 0},
                        "summary": "synthetic measured demo",
                    },
                    "post_run_interpretation_gate_report": {
                        "physical_credibility_check": {"status": "not_established"}
                    },
                    "evidence_sources": [],
                    "section_provenance_profile": [],
                },
                "validation_calibration_report": {
                    "physical_credibility_status": "not_established",
                    "calibration_status": "missing",
                    "validation_status": "partial",
                    "current_evidence_sources": [],
                    "claim_boundaries": helper.claim_boundaries(),
                },
                "physical_requirements_report": {
                    "physical_credibility_requirements_status": "mapped_current_gaps",
                    "evidence_requirement_categories": [],
                    "current_evidence_summary": [],
                },
                "observed_runout_intake_report": {
                    "observed_runout_deposition_intake_status": "blocked_missing_inputs",
                    "current_state_summary": [],
                },
            }
        )

        self.assertEqual(report["balfrin_demo_evidence_status"], "measured")
        self.assertEqual(report["physical_credibility_state"], "no_physical_evidence")
        self.assertEqual(report["validation_calibration_state"]["physical_credibility_status"], "not_established")
        self.assertEqual(report["validation_calibration_state"]["calibration_status"], "missing")
        self.assertEqual(report["validation_calibration_state"]["validation_status"], "partial")
        self.assertEqual(len(report["requirement_matrix"]), 7)
        self.assertEqual(report["requirement_matrix"][0]["current_repo_evidence_status"], "unknown")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
