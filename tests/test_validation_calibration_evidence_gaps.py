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
            "post_diagnostic_scale_context",
            "evidence_gap_categories",
            "claim_boundary_matrix",
            "validation_leakage_guardrails",
            "next_concrete_scientific_tasks",
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
        self.assertEqual(
            report["post_diagnostic_scale_context"]["status"],
            "diagnostic_scale_progress_does_not_close_scientific_gaps",
        )
        self.assertFalse(
            report["post_diagnostic_scale_context"]["claim_boundaries"]["scientific_validity_upgraded"]
        )
        self.assertEqual(report["validation_leakage_guardrails"]["guardrail_status"], "passed")
        self.assertTrue(report["validation_leakage_guardrails"]["interpretation_allowed"])
        self.assertEqual(report["validation_leakage_guardrails"]["failing_checks"], [])
        self.assertFalse(
            report["validation_leakage_guardrails"]["claim_boundaries"]["validation_acceptance_claimed"]
        )

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
                "source_frequency_and_temporal_frequency_evidence",
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
        self.assertEqual(
            categories["release_zone_evidence"]["first_missing_input"],
            "site_specific_release_zone_geometry_package",
        )
        self.assertEqual(categories["calibration_evidence"]["classification"], "missing")
        self.assertEqual(categories["holdout_and_validation_evidence"]["classification"], "partial")
        self.assertEqual(
            categories["block_size_and_block_population_evidence"]["first_missing_input"],
            "block_size_survey_or_photogrammetry_census",
        )
        self.assertEqual(
            categories["source_frequency_and_temporal_frequency_evidence"]["first_missing_input"],
            "historical_rockfall_event_catalogue",
        )
        self.assertTrue(
            categories["source_frequency_and_temporal_frequency_evidence"][
                "conditional_sampling_weights_are_not_frequency_evidence"
            ]
        )
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

    def test_validation_leakage_guardrails_fail_closed(self) -> None:
        guardrails = assessment.build_validation_leakage_guardrails(
            {
                "audit_status": "blocked_overlap_detected",
                "dataset_id": "fixture_split",
                "shared_trajectory_ids": ["A"],
            },
            {
                "preflight_status": "blocked_forbidden_validation_reference",
                "calibration_root": "calibration",
                "failure_replay": {
                    "missing_evidence_or_invalid_coupling": "bad_case selected_parameters_path=calibration/experiments/example/selected_parameters.yaml",
                    "first_blocker": {
                        "case_path": "validation/cases/bad_case.yaml",
                        "value": "calibration/experiments/example/selected_parameters.yaml",
                    },
                },
            },
        )

        self.assertEqual(guardrails["guardrail_status"], "blocked_validation_leakage_risk")
        self.assertFalse(guardrails["interpretation_allowed"])
        self.assertEqual(
            [item["guardrail"] for item in guardrails["failing_checks"]],
            ["holdout_split_independence", "calibration_validation_separation"],
        )
        self.assertIn("audit_chant_sura_holdout_split.py", guardrails["next_local_recovery_command"])

    def test_missing_evidence_is_not_inferred_as_present(self) -> None:
        report = assessment.build_report()
        site_map = {entry["site"]: entry for entry in report["site_reference_evidence"]}
        self.assertEqual(site_map["Schiers"]["classification"], "missing")
        self.assertEqual(site_map["Balfrin"]["classification"], "not_inferred")
        self.assertNotEqual(report["physical_credibility_status"], "present")
        self.assertNotEqual(report["physical_credibility_status"], "accepted")

    def test_text_report_names_validation_leakage_guardrails(self) -> None:
        text = assessment.render_text_report(assessment.build_report())

        self.assertIn("validation_leakage_guardrails:", text)
        self.assertIn("guardrail_status: passed", text)
        self.assertIn("failing_checks: none", text)
        self.assertIn("post_diagnostic_scale_context:", text)
        self.assertIn("next_concrete_scientific_tasks:", text)

    def test_next_concrete_scientific_tasks_rank_data_acquisition_before_more_performance_reports(self) -> None:
        report = assessment.build_report()
        tasks = report["next_concrete_scientific_tasks"]

        self.assertEqual(tasks[0]["task_id"], "stage_independent_holdout_deposition_runout_evidence")
        self.assertEqual(tasks[1]["task_id"], "stage_source_frequency_catalogue")
        self.assertEqual(tasks[2]["task_id"], "stage_block_population_survey")
        self.assertTrue(all("claim" in item["claim_boundary"] for item in tasks))
        self.assertIn("scientific evidence", tasks[0]["why_now"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
