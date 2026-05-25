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
            "candidate_runout_failure_diagnostic",
            "candidate_geometry_ablation",
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
        self.assertEqual(report["closure_limiting_layers"][0]["stability_zone_class"], "persistent_closure_limiting")
        self.assertEqual(report["deferrable_layers"][0]["stability_zone_class"], "deferrable_localized")

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
        self.assertIn("stability=persistent_closure_limiting", text)
        self.assertIn("workflow_product_blocker_deltas:", text)
        self.assertIn("summary_only_not_rebuildable", text)
        self.assertIn("claim_boundaries:", text)
        self.assertIn("candidate_runout_failure_diagnostic:", text)
        self.assertIn("source_placement_displaced_with_local_early_stopping", text)
        self.assertIn("candidate_geometry_ablation:", text)
        self.assertIn("source_offset_dominates_with_candidate_local_stopping_signal", text)
        self.assertIn("operational_claims_allowed: false", text)
        self.assertIn("scale_up_authorized: false", text)

    def test_candidate_failure_classifier_separates_source_and_physics_modes(self) -> None:
        self.assertEqual(
            summary.classify_candidate_failure_mode(
                runout_ratio=0.05,
                source_displacement_fraction=1.4,
                centroid_error=220.0,
                source_displacement=145.0,
            ),
            "source_placement_displaced_with_local_early_stopping",
        )
        self.assertEqual(
            summary.classify_candidate_failure_mode(
                runout_ratio=0.05,
                source_displacement_fraction=0.2,
                centroid_error=20.0,
                source_displacement=20.0,
            ),
            "local_early_stopping_or_excess_dissipation",
        )
        self.assertEqual(
            summary.classify_candidate_failure_mode(
                runout_ratio=0.7,
                source_displacement_fraction=1.0,
                centroid_error=30.0,
                source_displacement=100.0,
            ),
            "source_placement_displaced",
        )

    def test_centroid_reads_reviewed_release_cell_centers(self) -> None:
        centroid = summary.centroid_xy(
            [
                {"release_cell_center_lv95_m": "[2696482.5, 1167530.0]"},
                {"release_cell_center_lv95_m": "[2696486.5, 1167534.0]"},
            ]
        )

        self.assertEqual(centroid, {"x_m": 2696484.5, "y_m": 1167532.0})

    def test_candidate_geometry_ablation_separates_source_offset_from_stopping(self) -> None:
        ablation = summary.summarize_candidate_geometry_ablation()

        self.assertEqual(ablation["ablation_status"], "fixture_replay_ready")
        self.assertEqual(
            ablation["dominant_effect"],
            "source_offset_dominates_with_candidate_local_stopping_signal",
        )
        self.assertGreater(
            ablation["deltas"]["deposition_centroid_error_delta_candidate_minus_source_aligned_m"],
            200.0,
        )
        self.assertGreater(
            ablation["source_aligned_variant"]["simulated_to_observed_runout_ratio"],
            0.25,
        )
        self.assertLess(
            ablation["candidate_aligned_variant"]["simulated_to_observed_runout_ratio"],
            0.25,
        )
        self.assertFalse(ablation["claim_boundaries"]["parameter_tuning_authorized"])
        self.assertFalse(ablation["claim_boundaries"]["candidate_acceptance_upgrade"])

    def test_candidate_geometry_ablation_fails_closed_on_missing_metrics(self) -> None:
        ablation = summary.summarize_candidate_geometry_ablation(
            {
                "candidate_local_comparison_record": "validation/pilot_runs/does_not_exist.yaml",
            }
        )

        self.assertEqual(ablation["ablation_status"], "blocked_missing_inputs")
        self.assertEqual(ablation["dominant_effect"], "unknown")
        self.assertIn("validation/pilot_runs/does_not_exist.yaml", ablation["missing_inputs"])
        self.assertFalse(ablation["claim_boundaries"]["parameter_tuning_authorized"])

    def test_missing_inputs_override_reports_blocked_status(self) -> None:
        report = summary.build_report({"missing_inputs": ["docs/missing.json"]})
        self.assertEqual(report["closure_gap_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_closure_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertEqual(report["candidate_runout_failure_diagnostic"]["diagnostic_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_geometry_ablation"]["ablation_status"], "blocked_missing_inputs")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def _evidence_override(self) -> dict[str, object]:
        return {
            "candidate_runout_failure_diagnostic": {
                "diagnostic_status": "ready",
                "dominant_failure_mode": "source_placement_displaced_with_local_early_stopping",
                "smallest_next_scientific_action": "compare an alternate reviewed candidate before physics tuning",
                "candidate_vs_observed_geometry": {
                    "candidate_release_to_observed_release_centroid_m": 145.0,
                },
                "runout_diagnostics": {
                    "simulated_to_observed_runout_ratio": 0.055,
                },
                "claim_boundaries": {
                    "diagnostic_only": True,
                    "candidate_acceptance_upgrade": False,
                    "parameter_tuning_authorized": False,
                    "operational_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                },
            },
            "candidate_geometry_ablation": {
                "ablation_status": "fixture_replay_ready",
                "dominant_effect": "source_offset_dominates_with_candidate_local_stopping_signal",
                "source_aligned_variant": {
                    "simulated_to_observed_runout_ratio": 0.692689,
                },
                "candidate_aligned_variant": {
                    "simulated_to_observed_runout_ratio": 0.055825,
                },
                "deltas": {
                    "runout_distance_error_delta_candidate_minus_source_aligned_m": 65.493787,
                    "deposition_centroid_error_delta_candidate_minus_source_aligned_m": 204.866829,
                    "deposition_overlap_delta_candidate_minus_source_aligned": -0.433333,
                },
                "smallest_next_scientific_action": "test a source-aligned reviewed candidate before any physics tuning",
                "claim_boundaries": {
                    "candidate_acceptance_upgrade": False,
                    "parameter_tuning_authorized": False,
                    "operational_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                },
            },
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
                            "stability_zone_summary": {
                                "stability_zone_status": "measured_existing_artifacts",
                                "overall_closure_role_change": "no_change",
                            },
                            "layer_roles": {
                                "max_kinetic_energy": {
                                    "closure_role": "closure_limiting",
                                    "stability_zone_class": "persistent_closure_limiting",
                                    "stability_zone_dominant_category": "shared_support_magnitude",
                                    "stability_zone_dominant_high_uncertainty_category": "shared_support_magnitude",
                                    "stability_zone_closure_role_impact": "no_change",
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
                                    "stability_zone_class": "persistent_closure_limiting",
                                    "stability_zone_dominant_category": "persistent_agreement",
                                    "stability_zone_dominant_high_uncertainty_category": "support_nodata_sensitive",
                                    "stability_zone_closure_role_impact": "no_change",
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
                                    "stability_zone_class": "deferrable_localized",
                                    "stability_zone_dominant_category": "persistent_agreement",
                                    "stability_zone_dominant_high_uncertainty_category": "shared_support_magnitude",
                                    "stability_zone_closure_role_impact": "no_change",
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
