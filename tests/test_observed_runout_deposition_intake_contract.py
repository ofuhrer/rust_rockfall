from __future__ import annotations

import unittest

from scripts import summarize_observed_runout_deposition_intake_contract as helper


class ObservedRunoutDepositionIntakeContractTests(unittest.TestCase):
    def test_contract_shape_and_field_requirements(self) -> None:
        report = helper.build_report()

        expected_keys = {
            "schema_version",
            "observed_runout_deposition_intake_status",
            "benchmark_intake_contract",
            "field_requirement_map",
            "current_repo_state",
            "claim_boundaries",
            "blocked_reason",
            "missing_inputs",
            "current_state_summary",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["schema_version"], helper.SCHEMA_VERSION)
        self.assertEqual(report["observed_runout_deposition_intake_status"], "blocked_missing_inputs")

        contract = report["benchmark_intake_contract"]
        self.assertEqual(contract["geometry"]["required_crs"], "EPSG:2056")
        self.assertIn("source_polygon", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("runout_axis_line", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("deposition_footprint_polygon", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("event_id", contract["event_source_metadata"]["required_fields"])
        self.assertIn("source_id", contract["event_source_metadata"]["required_fields"])
        self.assertIn("geometry_tolerance_m", contract["uncertainty"]["required_fields"])
        self.assertIn("runout_endpoint_error_m", contract["objective_function_placeholders"]["required_fields"])
        self.assertEqual(contract["objective_function_placeholders"]["objective_status"], "placeholder_only")

        mapping = {entry["field_path"]: entry["physical_credibility_requirement"] for entry in report["field_requirement_map"]}
        self.assertEqual(mapping["geometry.geometry_role=runout_axis_line"], "observed_runout_deposition")
        self.assertEqual(mapping["geometry.geometry_role=deposition_footprint_polygon"], "observed_runout_deposition")
        self.assertEqual(mapping["geometry.geometry_encoding"], "observed_runout_deposition")
        self.assertEqual(mapping["event_source_metadata.observer"], "observed_runout_deposition")
        self.assertEqual(mapping["event_source_metadata.source_id"], "release_zone_evidence")
        self.assertEqual(mapping["event_source_metadata.source_reference_frame"], "terrain_and_context_evidence")
        self.assertEqual(mapping["uncertainty.qa_status"], "observed_runout_deposition")
        self.assertEqual(
            mapping["objective_function_placeholders.deposition_footprint_iou"],
            "calibration_data_and_objective_functions",
        )
        self.assertEqual(
            mapping["objective_function_placeholders.objective_status"],
            "calibration_data_and_objective_functions",
        )

    def test_blocked_current_state_and_boundaries_are_explicit(self) -> None:
        report = helper.build_report()

        current_state = report["current_repo_state"]
        self.assertEqual(current_state["benchmark_intake_dataset_status"], "absent")
        self.assertEqual(current_state["calibration_dataset_status"], "absent")
        self.assertIn(str(helper.EXPECTED_BENCHMARK_MANIFEST), current_state["missing_inputs"])
        self.assertIn(str(helper.EXPECTED_BENCHMARK_GEOMETRY), current_state["missing_inputs"])
        self.assertIn(str(helper.EXPECTED_CALIBRATION_ROOT), current_state["missing_inputs"])
        self.assertTrue(
            any(
                item["classification"] == "diagnostic_only" and item["status"] == "present"
                for item in current_state["adjacent_diagnostic_materials"]
            )
        )
        self.assertIn("no independent observed runout/deposition benchmark intake", report["blocked_reason"])
        self.assertFalse(report["claim_boundaries"]["calibration_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_text_output_mentions_placeholder_and_blocked_state(self) -> None:
        text = helper.render_text_report(helper.build_report())

        self.assertIn("observed_runout_deposition_intake_status: blocked_missing_inputs", text)
        self.assertIn("geometry.geometry_role=runout_axis_line -> observed_runout_deposition", text)
        self.assertIn("objective_function_placeholders.runout_endpoint_error_m -> calibration_data_and_objective_functions", text)
        self.assertIn("benchmark_intake_dataset_status: absent", text)
        self.assertIn("No calibration dataset is available for objective fitting.", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
