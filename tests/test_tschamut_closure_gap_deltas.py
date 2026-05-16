from __future__ import annotations

import unittest

from scripts import summarize_tschamut_closure_gap_deltas as summary


class TschamutClosureGapDeltaTests(unittest.TestCase):
    def test_json_shape_and_statuses(self) -> None:
        report = summary.build_report(self._evidence_override())

        expected_keys = {
            "schema_version",
            "closure_gap_status",
            "current_closure_status",
            "current_interpretation_status",
            "same_scale_readiness_status",
            "closure_limiting_layers",
            "deferrable_layers",
            "scientific_blocker_deltas",
            "workflow_product_blocker_deltas",
            "accepted_diagnostic_gap",
            "deferred_gap",
            "no_go_gap",
            "claim_boundaries",
            "current_evidence",
            "scale_up_authorized",
            "operational_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "distributed_execution_authorized",
            "physical_probability_claims_allowed",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["closure_gap_status"], "measured_gaps_remain")
        self.assertEqual(report["current_closure_status"], "inconclusive")
        self.assertEqual(report["current_interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(report["same_scale_readiness_status"], "ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["annual_frequency_claims_allowed"])
        self.assertFalse(report["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["distributed_execution_authorized"])
        self.assertFalse(report["physical_probability_claims_allowed"])

    def test_gap_summary_distinguishes_deferred_from_no_go(self) -> None:
        report = summary.build_report(self._evidence_override())

        self.assertEqual([item["layer_key"] for item in report["closure_limiting_layers"]], ["max_jump_height", "max_kinetic_energy"])
        self.assertEqual([item["layer_key"] for item in report["deferrable_layers"]], ["velocity_exceedance_5mps"])
        self.assertEqual(report["accepted_diagnostic_gap"]["status"], "not_met")
        self.assertEqual(report["deferred_gap"]["status"], "closer_to_deferred_than_no_go")
        self.assertEqual(report["no_go_gap"]["status"], "not_supported_by_current_evidence")
        self.assertIn("closure_status_inconclusive", report["accepted_diagnostic_gap"]["blocking_scientific_fields"])
        self.assertIn("max_kinetic_energy", report["accepted_diagnostic_gap"]["blocking_layers"])
        self.assertIn("max_jump_height", report["accepted_diagnostic_gap"]["blocking_layers"])
        self.assertIn("velocity_exceedance_5mps", report["deferred_gap"]["supporting_layers"])
        self.assertIn("summary_only_not_rebuildable", {item["blocker_key"] for item in report["workflow_product_blocker_deltas"]})
        self.assertIn("standard_gis_roots_cog_blocked", {item["blocker_key"] for item in report["workflow_product_blocker_deltas"]})

        scientific = {item["layer_key"]: item for item in report["scientific_blocker_deltas"]}
        self.assertGreater(scientific["max_jump_height"]["support_nodata_fraction_delta"], 0.0)
        self.assertGreaterEqual(scientific["max_kinetic_energy"]["shared_support_magnitude_fraction_delta"], 0.0)
        self.assertIn("persistent diffuse spatial disagreement", report["no_go_gap"]["would_require"][0])
        self.assertIn("support/nodata", report["no_go_gap"]["would_require"][1])

    def test_text_output_names_key_layers_and_blockers(self) -> None:
        text = summary.render_text_report(summary.build_report(self._evidence_override()))
        self.assertIn("closure_gap_status: measured_gaps_remain", text)
        self.assertIn("max_kinetic_energy", text)
        self.assertIn("max_jump_height", text)
        self.assertIn("velocity_exceedance_5mps", text)
        self.assertIn("workflow_product_blocker_deltas:", text)
        self.assertIn("summary_only_not_rebuildable", text)
        self.assertIn("claim_boundaries:", text)
        self.assertIn("operational_claims_allowed: false", text)
        self.assertIn("scale_up_authorized: false", text)

    def test_missing_inputs_override_reports_blocked_status(self) -> None:
        report = summary.build_report({"missing_inputs": ["docs/missing.json"]})
        self.assertEqual(report["closure_gap_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_closure_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def _evidence_override(self) -> dict[str, object]:
        return {
            "diagnostic_report": {
                "schema_version": "tschamut_conditional_diagnostic_interpretation_v1",
                "interpretation_status": "inconclusive_conditional_diagnostic",
                "closure_status": "inconclusive",
                "same_scale_readiness_status": "ready",
                "spatial_uncertainty_status": "measured_existing_artifacts",
                "dominant_scientific_blockers": [
                    "closure_status_inconclusive",
                    "spatial_uncertainty_support_nodata_dominates_closure",
                    "max_kinetic_energy_closure_limiting",
                    "max_jump_height_closure_limiting",
                    "velocity_exceedance_5mps_deferrable",
                ],
                "workflow_product_blockers": [
                    "summary_only_not_rebuildable",
                    "standard_gis_roots_cog_blocked",
                ],
                "portability_blockers": [
                    "public_context_inputs_deferred",
                ],
                "physical_credibility_blockers": [
                    "physical_credibility_not_established",
                ],
                "output_profile_status": {"target_summary_only": "summary_only_not_rebuildable"},
                "gis_cog_status": {"standard_package_status": "gis_package_ready_cog_blocked"},
                "runtime_scaling_status": {
                    "reducer_scaling_status": "measured_existing_artifacts",
                    "local_single_job_sufficient_for_next_step": True,
                    "distributed_execution_authorized": False,
                },
                "portability_status": {
                    "portability_preflight_status": "deferred_public_context_inputs",
                    "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                    "missing_input_categories": ["processed_context_root"],
                },
                "physical_credibility_status": "not_established",
                "claim_boundaries": {
                    "scale_up_authorized": False,
                    "operational_claims_allowed": False,
                    "annual_frequency_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                    "distributed_execution_authorized": False,
                    "physical_probability_claims_allowed": False,
                },
                "current_evidence": {
                    "closure": {
                        "current_blockers": [
                            "closure_status_inconclusive",
                            "spatial_uncertainty_support_nodata_dominates_closure",
                            "max_kinetic_energy_closure_limiting",
                            "max_jump_height_closure_limiting",
                        ],
                        "spatial_uncertainty_interpretation": {
                            "spatial_interpretation": "nodata_support_dominated",
                            "overall_closure_role": "closure_limiting",
                            "layer_roles": {
                                "max_kinetic_energy": {
                                    "closure_role": "closure_limiting",
                                    "disagreement_decomposition_class": "shared_support_magnitude_dominated",
                                    "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                                    "high_uncertainty_cell_count": 4,
                                    "high_uncertainty_cell_fraction": 0.05,
                                    "high_uncertainty_support_nodata_fraction": 0.0,
                                    "high_uncertainty_shared_support_magnitude_fraction": 1.0,
                                    "support_only_disagreement_count": 0,
                                    "nodata_disagreement_count": 10,
                                    "magnitude_only_disagreement_count": 20,
                                    "shared_valid_cell_count": 50,
                                    "analysis_cell_count": 100,
                                    "high_uncertainty_bbox": {
                                        "row_min": 1,
                                        "row_max": 2,
                                        "col_min": 1,
                                        "col_max": 2,
                                    },
                                    "disagreement_decomposition": {
                                        "shared_support_magnitude_range_summary": {"mean_range": 10.0},
                                    },
                                },
                                "max_jump_height": {
                                    "closure_role": "closure_limiting",
                                    "disagreement_decomposition_class": "mixed_support_and_magnitude",
                                    "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                                    "high_uncertainty_cell_count": 2,
                                    "high_uncertainty_cell_fraction": 0.02,
                                    "high_uncertainty_support_nodata_fraction": 0.75,
                                    "high_uncertainty_shared_support_magnitude_fraction": 0.25,
                                    "support_only_disagreement_count": 12,
                                    "nodata_disagreement_count": 8,
                                    "magnitude_only_disagreement_count": 18,
                                    "shared_valid_cell_count": 50,
                                    "analysis_cell_count": 100,
                                    "high_uncertainty_bbox": {
                                        "row_min": 2,
                                        "row_max": 3,
                                        "col_min": 2,
                                        "col_max": 3,
                                    },
                                    "disagreement_decomposition": {
                                        "shared_support_magnitude_range_summary": {"mean_range": 2.0},
                                    },
                                },
                                "velocity_exceedance_5mps": {
                                    "closure_role": "deferrable",
                                    "disagreement_decomposition_class": "shared_support_magnitude_dominated",
                                    "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
                                    "high_uncertainty_cell_count": 1,
                                    "high_uncertainty_cell_fraction": 0.01,
                                    "high_uncertainty_support_nodata_fraction": 0.0,
                                    "high_uncertainty_shared_support_magnitude_fraction": 1.0,
                                    "support_only_disagreement_count": 1,
                                    "nodata_disagreement_count": 0,
                                    "magnitude_only_disagreement_count": 5,
                                    "shared_valid_cell_count": 50,
                                    "analysis_cell_count": 100,
                                    "high_uncertainty_bbox": {
                                        "row_min": 4,
                                        "row_max": 4,
                                        "col_min": 4,
                                        "col_max": 4,
                                    },
                                    "disagreement_decomposition": {
                                        "shared_support_magnitude_range_summary": {"mean_range": 1.0},
                                    },
                                },
                            },
                        },
                    }
                },
            }
        }


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
