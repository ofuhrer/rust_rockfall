from __future__ import annotations

import unittest

from scripts import summarize_tschamut_conditional_pilot_closure as summary


class TschamutConditionalPilotClosureTest(unittest.TestCase):
    def test_current_status_is_inconclusive(self) -> None:
        report = summary.build_closure_report()
        self.assertEqual(report["closure_status"], "inconclusive")
        self.assertEqual(report["readiness_status"], "ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_criteria_matrix_shape_and_required_statuses(self) -> None:
        report = summary.build_closure_report()
        matrix = report["criteria_matrix"]
        criteria = {entry["criterion"] for entry in matrix}
        self.assertGreaterEqual(len(matrix), 10)
        self.assertTrue(
            {
                "same_scale_readiness",
                "convergence_and_uncertainty_envelope",
                "validation_output_profile",
                "gis_cog_readiness",
                "reducer_runtime_scaling",
            }.issubset(criteria)
        )
        self.assertIn("accepted_diagnostic_criteria", report)
        self.assertIn("no_go_criteria", report)
        self.assertIn("deferred_criteria", report)
        self.assertIn("spatial_uncertainty_interpretation", report)

    def test_current_mapping_contains_satisfied_and_blocked_states(self) -> None:
        report = summary.build_closure_report()
        matrix = {entry["criterion"]: entry for entry in report["criteria_matrix"]}
        self.assertEqual(matrix["same_scale_readiness"]["current_state"], "satisfied")
        self.assertEqual(matrix["convergence_and_uncertainty_envelope"]["current_state"], "unresolved")
        self.assertEqual(matrix["dominant_disagreement_layers"]["current_state"], "closure_limiting")
        self.assertEqual(matrix["max_kinetic_energy_behavior"]["current_state"], "closure_limiting")
        self.assertEqual(matrix["max_jump_height_support_nodata_sensitivity"]["current_state"], "closure_limiting")
        self.assertEqual(matrix["velocity_exceedance_behavior"]["current_state"], "deferrable")
        self.assertEqual(matrix["hazard_rebuild_output_compatibility"]["current_state"], "blocked")
        self.assertEqual(matrix["gis_cog_readiness"]["current_state"], "blocked")
        self.assertEqual(matrix["reducer_runtime_scaling"]["current_state"], "satisfied")
        self.assertEqual(matrix["physical_annual_risk_operational_boundaries"]["current_state"], "out_of_scope")
        spatial = report["spatial_uncertainty_interpretation"]
        self.assertEqual(spatial["spatial_interpretation"], "nodata_support_dominated")
        self.assertEqual(spatial["overall_closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["closure_role"], "deferrable")
        self.assertIn("spatial_uncertainty_support_nodata_dominates_closure", report["current_blockers"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_blocked_missing_input_override(self) -> None:
        report = summary.build_closure_report({"missing_inputs": ["docs/missing.json"]})
        self.assertEqual(report["closure_status"], "blocked_missing_inputs")
        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
