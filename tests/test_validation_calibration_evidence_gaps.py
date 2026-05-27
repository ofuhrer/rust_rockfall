from __future__ import annotations

import unittest

from scripts import assess_validation_calibration_evidence_gaps as assessment


class ValidationCalibrationEvidenceGapsTest(unittest.TestCase):
    def test_json_shape_and_boundaries(self) -> None:
        report = assessment.build_report()

        expected_keys = {
            "schema_version",
            "physical_credibility_status",
            "physical_probability_claims_allowed",
            "physical_probability_readiness_check",
            "calibration_status",
            "validation_status",
            "annual_frequency_claims_allowed",
            "operational_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "scale_up_authorized",
            "post_diagnostic_scale_context",
            "source_frequency_intake",
            "block_population_intake",
            "evidence_gap_categories",
            "claim_boundary_matrix",
            "validation_leakage_guardrails",
            "calibration_holdout_separation_check",
            "next_concrete_scientific_tasks",
            "product_layer_claim_boundaries",
            "site_reference_evidence",
            "required_evidence_for_physical_credibility",
            "current_evidence_sources",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["physical_credibility_status"], "not_established")
        self.assertFalse(report["physical_probability_claims_allowed"])
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
        self.assertEqual(report["source_frequency_intake"]["intake_classification"], "accepted")
        self.assertEqual(
            report["calibration_holdout_separation_check"]["separation_status"],
            "separated_holdout_ready",
        )
        self.assertTrue(report["validation_leakage_guardrails"]["interpretation_allowed"])
        self.assertEqual(report["validation_leakage_guardrails"]["failing_checks"], [])
        self.assertFalse(
            report["validation_leakage_guardrails"]["claim_boundaries"]["validation_acceptance_claimed"]
        )
        readiness = report["physical_probability_readiness_check"]
        self.assertEqual(readiness["schema_version"], "physical_probability_readiness_check_v1")
        self.assertFalse(readiness["physical_probability_claims_allowed"])
        self.assertIn(readiness["readiness_status"], {
            "blocked_missing_required_evidence",
            "partial_evidence_missing_critical_inputs",
        })
        self.assertNotIn("source_frequency_evidence", readiness["failing_evidence_classes"])
        self.assertNotIn("release_probability_model", readiness["failing_evidence_classes"])
        self.assertNotIn("block_population_evidence", readiness["failing_evidence_classes"])
        self.assertEqual(readiness["first_blocking_evidence_class"], "calibration_evidence")
        self.assertIn("calibration_evidence", readiness["failing_evidence_classes"])
        self.assertEqual(report["block_release_probability_intake"]["intake_classification"], "present")
        self.assertEqual(report["block_population_intake"]["intake_classification"], "present")

    def test_block_population_candidate_validates_as_design_review_evidence(self) -> None:
        summary = assessment.validate_block_population_evidence_record(
            assessment.DEFAULT_BLOCK_POPULATION_EVIDENCE_PATH
        )

        self.assertEqual(summary["record_id"], "tschamut_public_block_population_candidate_v1")
        self.assertEqual(summary["record_status"], "accepted_for_design_review")
        self.assertEqual(summary["source_zone_id"], "tschamut_public_lps_release_bbox")
        self.assertEqual(summary["block_population_class_count"], 3)
        self.assertEqual(summary["total_count"], 3)
        self.assertFalse(summary["prototype_authorized"])

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
        self.assertEqual(categories["observed_deposition_runout_evidence"]["classification"], "present")
        self.assertEqual(categories["release_zone_evidence"]["classification"], "present")
        self.assertEqual(
            categories["release_zone_evidence"]["first_missing_input"],
            "",
        )
        self.assertEqual(categories["calibration_evidence"]["classification"], "missing")
        self.assertEqual(categories["holdout_and_validation_evidence"]["classification"], "present")
        self.assertEqual(categories["block_size_and_block_population_evidence"]["classification"], "present")
        self.assertEqual(
            categories["block_size_and_block_population_evidence"]["first_missing_input"],
            "",
        )
        self.assertEqual(categories["source_frequency_and_temporal_frequency_evidence"]["classification"], "present")
        self.assertEqual(categories["source_frequency_and_temporal_frequency_evidence"]["first_missing_input"], "")
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
                "deposition-footprint" in item.lower()
                for item in categories["holdout_and_validation_evidence"]["what_is_missing"]
            )
        )
        self.assertIn(
            "runout-axis intake is staged",
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

    def test_calibration_holdout_check_reports_missing_holdout(self) -> None:
        check = assessment.build_calibration_holdout_separation_check(
            [
                {
                    "dataset_id": "calibration_a",
                    "site_id": "site_a",
                    "event_id": "event_a",
                    "sample_id": "sample_a",
                    "role": "calibration",
                },
                {
                    "dataset_id": "validation_a",
                    "site_id": "site_b",
                    "event_id": "event_b",
                    "sample_id": "sample_b",
                    "role": "validation",
                },
            ]
        )

        self.assertEqual(check["separation_status"], "blocked_missing_holdout_or_calibration_record")
        self.assertIn("missing_explicit_holdout_validation_label", check["missing_reasons"])
        self.assertIn("holdout_validation", check["next_required_acquisition_step"])

    def test_calibration_holdout_check_rejects_overlapping_holdout(self) -> None:
        check = assessment.build_calibration_holdout_separation_check(
            [
                {
                    "dataset_id": "shared_dataset",
                    "site_id": "site_a",
                    "event_id": "event_a",
                    "sample_id": "sample_a",
                    "role": "calibration",
                },
                {
                    "dataset_id": "holdout_a",
                    "site_id": "site_a",
                    "event_id": "event_a",
                    "sample_id": "sample_a",
                    "role": "holdout_validation",
                },
            ]
        )

        self.assertEqual(check["separation_status"], "blocked_calibration_validation_overlap")
        self.assertEqual(check["overlap_count"], 1)
        self.assertIn("event_id", check["overlaps"][0]["shared_keys"])
        self.assertIn("sample_id", check["overlaps"][0]["shared_keys"])
        self.assertFalse(check["stronger_scientific_conclusions_allowed"])

    def test_calibration_holdout_check_accepts_separated_holdout(self) -> None:
        check = assessment.build_calibration_holdout_separation_check(
            [
                {
                    "dataset_id": "calibration_a",
                    "site_id": "site_a",
                    "event_id": "event_a",
                    "sample_id": "sample_a",
                    "role": "calibration",
                },
                {
                    "dataset_id": "holdout_b",
                    "site_id": "site_b",
                    "event_id": "event_b",
                    "sample_id": "sample_b",
                    "role": "holdout_validation",
                },
            ]
        )

        self.assertEqual(check["separation_status"], "separated_holdout_ready")
        self.assertEqual(check["overlap_count"], 0)
        self.assertTrue(check["stronger_scientific_conclusions_allowed"])

    def test_missing_evidence_is_not_inferred_as_present(self) -> None:
        report = assessment.build_report()
        site_map = {entry["site"]: entry for entry in report["site_reference_evidence"]}
        self.assertEqual(site_map["Schiers"]["classification"], "missing")
        self.assertEqual(site_map["Balfrin"]["classification"], "not_inferred")
        self.assertNotEqual(report["physical_credibility_status"], "present")
        self.assertNotEqual(report["physical_credibility_status"], "accepted")

    def test_text_report_names_validation_leakage_guardrails(self) -> None:
        text = assessment.render_text_report(assessment.build_report())

        self.assertIn("physical_probability_readiness_check:", text)
        self.assertIn("physical_probability_claims_allowed: false", text)
        self.assertIn("source_frequency_intake: accepted", text)
        self.assertIn("validation_leakage_guardrails:", text)
        self.assertIn("calibration_holdout_separation_check:", text)
        self.assertIn("guardrail_status: passed", text)
        self.assertIn("failing_checks: none", text)
        self.assertIn("post_diagnostic_scale_context:", text)
        self.assertIn("next_concrete_scientific_tasks:", text)

    def test_next_concrete_scientific_tasks_rank_data_acquisition_before_more_performance_reports(self) -> None:
        report = assessment.build_report()
        tasks = report["next_concrete_scientific_tasks"]

        self.assertEqual(tasks[0]["task_id"], "define_calibration_dataset_and_objective")
        self.assertEqual(tasks[1]["task_id"], "stage_second_site_public_geodata_inputs")
        self.assertNotIn("stage_independent_holdout_deposition_runout_evidence", [task["task_id"] for task in tasks])
        self.assertNotIn("stage_source_frequency_catalogue", [task["task_id"] for task in tasks])
        self.assertNotIn("stage_block_population_survey", [task["task_id"] for task in tasks])
        self.assertTrue(all("claim" in item["claim_boundary"] for item in tasks))
        self.assertIn("scientific evidence", tasks[0]["why_now"])

    def test_physical_probability_readiness_fails_for_conditional_only_state(self) -> None:
        check = assessment.build_physical_probability_readiness_check(
            [
                {"category": "source_frequency_and_temporal_frequency_evidence", "classification": "missing", "first_missing_input": "historical_rockfall_event_catalogue"},
                {"category": "release_zone_evidence", "classification": "partial", "first_missing_input": "site_specific_release_zone_geometry_package"},
                {"category": "block_size_and_block_population_evidence", "classification": "missing", "first_missing_input": "block_size_survey_or_photogrammetry_census"},
                {"category": "calibration_evidence", "classification": "missing", "first_missing_input": "calibration_dataset"},
                {"category": "holdout_and_validation_evidence", "classification": "partial", "first_missing_input": "independent_holdout_benchmark"},
            ],
            denominator_audit={"audit_status": "complete"},
            traceability_audit={"audit_status": "traceable"},
        )

        self.assertEqual(check["readiness_status"], "partial_evidence_missing_critical_inputs")
        self.assertFalse(check["physical_probability_claims_allowed"])
        self.assertEqual(check["first_blocking_evidence_class"], "source_frequency_evidence")
        self.assertIn("block_population_evidence", check["failing_evidence_classes"])

    def test_physical_probability_readiness_distinguishes_partially_calibrated_state(self) -> None:
        check = assessment.build_physical_probability_readiness_check(
            [
                {"category": "source_frequency_and_temporal_frequency_evidence", "classification": "missing", "first_missing_input": "historical_rockfall_event_catalogue"},
                {"category": "release_zone_evidence", "classification": "present"},
                {"category": "block_size_and_block_population_evidence", "classification": "partial", "first_missing_input": "block_count_or_size_class_record"},
                {"category": "calibration_evidence", "classification": "present"},
                {"category": "holdout_and_validation_evidence", "classification": "present"},
            ],
            denominator_audit={"audit_status": "complete"},
            traceability_audit={"audit_status": "traceable"},
        )

        self.assertEqual(check["readiness_status"], "partial_evidence_missing_critical_inputs")
        self.assertEqual(check["passing_evidence_count"], 5)
        self.assertEqual(
            check["failing_evidence_classes"],
            ["source_frequency_evidence", "block_population_evidence"],
        )

    def test_physical_probability_readiness_can_pass_for_fully_evidence_ready_state(self) -> None:
        check = assessment.build_physical_probability_readiness_check(
            [
                {"category": "source_frequency_and_temporal_frequency_evidence", "classification": "present"},
                {"category": "release_zone_evidence", "classification": "present"},
                {"category": "block_size_and_block_population_evidence", "classification": "present"},
                {"category": "calibration_evidence", "classification": "present"},
                {"category": "holdout_and_validation_evidence", "classification": "present"},
            ],
            denominator_audit={"audit_status": "complete"},
            traceability_audit={"audit_status": "traceable"},
        )

        self.assertEqual(check["readiness_status"], "ready_for_physical_probability_product")
        self.assertTrue(check["physical_probability_claims_allowed"])
        self.assertEqual(check["failing_evidence_classes"], [])

    def test_accepted_source_frequency_fixture_moves_readiness_to_next_missing_class(self) -> None:
        report = assessment.build_report(
            assessment.ROOT / "tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml"
        )

        categories = {entry["category"]: entry for entry in report["evidence_gap_categories"]}
        self.assertEqual(
            categories["source_frequency_and_temporal_frequency_evidence"]["classification"],
            "present",
        )
        self.assertEqual(report["source_frequency_intake"]["intake_classification"], "accepted")
        readiness = report["physical_probability_readiness_check"]
        self.assertNotIn("source_frequency_evidence", readiness["failing_evidence_classes"])
        self.assertNotIn("release_probability_model", readiness["failing_evidence_classes"])
        self.assertNotIn("block_population_evidence", readiness["failing_evidence_classes"])
        self.assertEqual(readiness["first_blocking_evidence_class"], "calibration_evidence")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
