from __future__ import annotations

import unittest

from scripts import assess_validation_calibration_evidence_gaps as assessment


class ValidationCalibrationEvidenceGapsTest(unittest.TestCase):
    def test_json_shape_and_boundaries(self) -> None:
        report = assessment.build_report()

        expected_keys = {
            "schema_version",
            "physical_credibility_status",
            "calibration_status",
            "validation_status",
            "annual_frequency_claims_allowed",
            "operational_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "scale_up_authorized",
            "evidence_gap_categories",
            "claim_boundary_matrix",
            "product_layer_claim_boundaries",
            "site_reference_evidence",
            "required_evidence_for_physical_credibility",
            "current_evidence_sources",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["physical_credibility_status"], "not_established")
        self.assertEqual(report["calibration_status"], "missing")
        self.assertEqual(report["validation_status"], "partial")
        self.assertFalse(report["annual_frequency_claims_allowed"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["scale_up_authorized"])

    def test_layer_claim_boundaries_distinguish_diagnostics_from_credibility(self) -> None:
        report = assessment.build_report()
        layers = {entry["layer_key"]: entry for entry in report["product_layer_claim_boundaries"]}
        self.assertEqual(
            list(layers),
            [
                "reach_probability",
                "deposition_density",
                "max_kinetic_energy",
                "max_jump_height",
                "conditional_intensity_exceedance_layers",
            ],
        )
        self.assertEqual(layers["reach_probability"]["diagnostic_usefulness"]["status"], "present")
        self.assertEqual(layers["reach_probability"]["physical_credibility"]["status"], "not_established")
        self.assertEqual(layers["deposition_density"]["reproducibility"]["status"], "present")
        self.assertEqual(layers["max_kinetic_energy"]["scientific_fragility"]["level"], "highest")
        self.assertEqual(layers["max_jump_height"]["scientific_fragility"]["level"], "high")
        self.assertEqual(
            layers["conditional_intensity_exceedance_layers"]["operational_inadmissibility"]["status"],
            "not_authorized",
        )
        self.assertTrue(
            any(
                item["class_name"] == "instrumented_impact_energy_benchmark"
                for item in layers["max_kinetic_energy"]["evidence_classes_needed"]
            )
        )
        self.assertTrue(
            any(
                item["class_name"] == "threshold_tagged_holdout_benchmark"
                for item in layers["conditional_intensity_exceedance_layers"]["evidence_classes_needed"]
            )
        )

    def test_categories_and_claim_boundaries_are_classified(self) -> None:
        report = assessment.build_report()
        categories = {entry["category"]: entry for entry in report["evidence_gap_categories"]}
        self.assertEqual(
            set(categories),
            {
                "observed_deposition_runout_evidence",
                "release_zone_evidence",
                "block_size_and_block_population_evidence",
                "terrain_and_context_evidence",
                "calibration_evidence",
                "holdout_and_validation_evidence",
                "multi_site_transfer_evidence",
            },
        )
        for entry in categories.values():
            self.assertIn(entry["classification"], {"present", "partial", "missing", "out_of_scope", "not_inferred"})

        boundary_map = {entry["boundary"]: entry for entry in report["claim_boundary_matrix"]}
        self.assertEqual(boundary_map["workflow_reproducibility"]["classification"], "present")
        self.assertEqual(boundary_map["conditional_diagnostic_interpretation"]["classification"], "present")
        self.assertEqual(boundary_map["release_candidate_physical_meaning"]["classification"], "present")
        self.assertEqual(boundary_map["physical_probability"]["classification"], "missing")
        self.assertEqual(boundary_map["annual_frequency"]["classification"], "out_of_scope")
        self.assertEqual(boundary_map["risk_exposure_vulnerability"]["classification"], "out_of_scope")
        self.assertEqual(boundary_map["operational_use"]["classification"], "out_of_scope")
        self.assertIn(
            "workflow_generated",
            " ".join(boundary_map["release_candidate_physical_meaning"]["evidence"]),
        )

    def test_diagnostic_vs_calibration_and_holdout_distinction(self) -> None:
        report = assessment.build_report()
        categories = {entry["category"]: entry for entry in report["evidence_gap_categories"]}
        self.assertEqual(categories["observed_deposition_runout_evidence"]["classification"], "partial")
        self.assertEqual(categories["calibration_evidence"]["classification"], "missing")
        self.assertEqual(categories["holdout_and_validation_evidence"]["classification"], "partial")
        self.assertTrue(
            any("calibration dataset" in item.lower() for item in categories["calibration_evidence"]["what_is_missing"])
        )
        self.assertTrue(
            any(
                "independent holdout benchmark" in item.lower()
                for item in categories["holdout_and_validation_evidence"]["what_is_missing"]
            )
        )
        self.assertIn(
            "not used to fit the model",
            categories["observed_deposition_runout_evidence"]["minimum_additional_evidence_needed"].lower(),
        )

    def test_missing_evidence_is_not_inferred_as_present(self) -> None:
        report = assessment.build_report()
        site_map = {entry["site"]: entry for entry in report["site_reference_evidence"]}
        self.assertEqual(site_map["Schiers"]["classification"], "missing")
        self.assertEqual(site_map["Balfrin"]["classification"], "not_inferred")
        self.assertNotEqual(report["physical_credibility_status"], "present")
        self.assertNotEqual(report["physical_credibility_status"], "accepted")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
