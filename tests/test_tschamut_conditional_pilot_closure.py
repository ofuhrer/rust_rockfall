from __future__ import annotations

import unittest

from scripts import summarize_tschamut_conditional_pilot_closure as summary


class TschamutConditionalPilotClosureTest(unittest.TestCase):
    def test_current_status_is_inconclusive(self) -> None:
        report = summary.build_closure_report(self._evidence_override())
        self.assertEqual(report["closure_status"], "inconclusive")
        self.assertEqual(report["readiness_status"], "ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_criteria_matrix_shape_and_required_statuses(self) -> None:
        report = summary.build_closure_report(self._evidence_override())
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
        report = summary.build_closure_report(self._evidence_override())
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
        self.assertEqual(spatial["stability_zone_summary"]["stability_zone_status"], "measured_existing_artifacts")
        self.assertEqual(spatial["stability_zone_summary"]["overall_closure_role_change"], "no_change")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["closure_role"], "deferrable")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["disagreement_decomposition_class"], "mixed_support_and_magnitude")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["disagreement_decomposition_class"], "support_nodata_dominated")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["disagreement_decomposition_class"], "shared_support_magnitude_dominated")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["stability_zone_class"], "persistent_closure_limiting")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["stability_zone_class"], "persistent_closure_limiting")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["stability_zone_class"], "deferrable_localized")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["stability_zone_dominant_category"], "shared_support_magnitude")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["stability_zone_dominant_category"], "persistent_agreement")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["stability_zone_dominant_category"], "persistent_agreement")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["stability_zone_closure_role_impact"], "no_change")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["stability_zone_closure_role_impact"], "no_change")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["stability_zone_closure_role_impact"], "no_change")
        self.assertEqual(spatial["uncertainty_layer_summary"]["summary_status"], "measured_existing_artifacts")
        self.assertEqual(
            [layer["confidence_class"] for layer in spatial["uncertainty_layer_summary"]["layer_summaries"]],
            ["closure_limiting_disagreement", "closure_limiting_disagreement", "deferrable_disagreement"],
        )
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["mask_status"], "available")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["mask_closure_role"], "closure_limiting")
        self.assertGreaterEqual(spatial["layer_roles"]["max_kinetic_energy"]["high_uncertainty_cell_count"], 0)
        self.assertGreaterEqual(spatial["layer_roles"]["max_jump_height"]["support_nodata_cell_count"], 0)
        self.assertEqual(spatial["mask_status"], "available")
        self.assertEqual(
            spatial["stability_zone_summary"]["layer_summaries"]["velocity_exceedance_5mps"]["closure_role_impact"],
            "no_change",
        )
        self.assertIn("spatial_uncertainty_support_nodata_dominates_closure", report["current_blockers"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_blocked_missing_input_override(self) -> None:
        report = summary.build_closure_report({"missing_inputs": ["docs/missing.json"]})
        self.assertEqual(report["closure_status"], "blocked_missing_inputs")
        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        self.assertEqual(report["spatial_uncertainty_interpretation"]["stability_zone_summary"]["stability_zone_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_text_output_mentions_stability_zone_changes(self) -> None:
        text = summary.render_text_report(summary.build_closure_report(self._evidence_override()))
        self.assertIn("stability=persistent_closure_limiting", text)
        self.assertIn("stability=deferrable_localized", text)
        self.assertIn("closure-role-change=no_change", text)
        self.assertIn("uncertainty layer summary:", text)
        self.assertIn("confidence=closure_limiting_disagreement", text)

    def _evidence_override(self) -> dict[str, object]:
        return {
            "readiness": {
                "readiness_status": "ready",
                "convergence_ready": True,
                "output_profile_ready": True,
                "hazard_context_overlap_ready": True,
                "missing_paths": [],
            },
            "sampling_uncertainty": {
                "sampling_uncertainty_status": "measured",
                "comparison_pairs_run": ["gate_vs_target"],
                "target_convergence_interpretation": "inconclusive",
                "dominant_layer_spread": {},
            },
                "spatial_uncertainty": {
                    "spatial_uncertainty_status": "measured_existing_artifacts",
                    "spatial_interpretation": "nodata_support_dominated",
                    "overall_closure_role": "closure_limiting",
                    "mask_status": "available",
                    "stability_zone_status": "measured_existing_artifacts",
                    "uncertainty_layer_summary": {
                        "schema_version": "spatial_uncertainty_layer_summary_v1",
                        "summary_status": "measured_existing_artifacts",
                        "stable_region_status": "measured_existing_artifacts",
                        "unstable_region_status": "measured_existing_artifacts",
                        "layer_summaries": [
                            {
                                "layer_key": "max_kinetic_energy",
                                "confidence_class": "closure_limiting_disagreement",
                                "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                                "stable_region": {"cell_count": 5},
                                "unstable_region": {"cell_count": 20},
                            },
                            {
                                "layer_key": "max_jump_height",
                                "confidence_class": "closure_limiting_disagreement",
                                "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                                "stable_region": {"cell_count": 12},
                                "unstable_region": {"cell_count": 13},
                            },
                            {
                                "layer_key": "velocity_exceedance_5mps",
                                "confidence_class": "deferrable_disagreement",
                                "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
                                "stable_region": {"cell_count": 20},
                                "unstable_region": {"cell_count": 5},
                            },
                        ],
                    },
                    "layer_summaries": {
                        "max_kinetic_energy": {
                            "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                            "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 12,
                        "support_only_disagreement_count": 2,
                        "magnitude_only_disagreement_count": 6,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 0.5,
                        "high_uncertainty_cell_fraction": 0.1,
                        "high_uncertainty_support_nodata_fraction": 0.75,
                        "high_uncertainty_shared_support_magnitude_fraction": 0.25,
                        "disagreement_decomposition": {
                            "classification": "mixed_support_and_magnitude",
                            "high_uncertainty_fraction_explained": {
                                "support_nodata": 0.75,
                                "shared_support_magnitude": 0.25,
                            },
                        },
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "closure_limiting",
                            "high_uncertainty_cell_count": 2,
                            "support_nodata_cell_count": 12,
                            "shared_support_magnitude_cell_count": 4,
                            "mask_bbox": {"row_min": 1, "row_max": 2, "col_min": 1, "col_max": 2, "xmin": 1.0, "xmax": 3.0, "ymin": 1.0, "ymax": 3.0},
                            "mask_path": None,
                        },
                        "stability_zone_summary": {
                            "layer_stability_zone_class": "persistent_closure_limiting",
                            "dominant_zone_category": "shared_support_magnitude",
                            "dominant_high_uncertainty_zone_category": "shared_support_magnitude",
                            "closure_role_impact": "no_change",
                            "zone_counts": {
                                "support_nodata_sensitive": 6,
                                "shared_support_magnitude": 14,
                                "persistent_agreement": 5,
                            },
                            "zone_fractions": {
                                "support_nodata_sensitive": 0.24,
                                "shared_support_magnitude": 0.56,
                                "persistent_agreement": 0.2,
                            },
                        },
                    },
                    "max_jump_height": {
                        "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                        "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 8,
                        "support_only_disagreement_count": 1,
                        "magnitude_only_disagreement_count": 1,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 0.7,
                        "high_uncertainty_cell_fraction": 0.05,
                        "high_uncertainty_support_nodata_fraction": 0.8,
                        "high_uncertainty_shared_support_magnitude_fraction": 0.2,
                        "disagreement_decomposition": {
                            "classification": "support_nodata_dominated",
                            "high_uncertainty_fraction_explained": {
                                "support_nodata": 0.8,
                                "shared_support_magnitude": 0.2,
                            },
                        },
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "closure_limiting",
                            "high_uncertainty_cell_count": 1,
                            "support_nodata_cell_count": 8,
                            "shared_support_magnitude_cell_count": 3,
                            "mask_bbox": {"row_min": 0, "row_max": 1, "col_min": 0, "col_max": 1, "xmin": 0.0, "xmax": 2.0, "ymin": 2.0, "ymax": 4.0},
                            "mask_path": None,
                        },
                        "stability_zone_summary": {
                            "layer_stability_zone_class": "persistent_closure_limiting",
                            "dominant_zone_category": "persistent_agreement",
                            "dominant_high_uncertainty_zone_category": "support_nodata_sensitive",
                            "closure_role_impact": "no_change",
                            "zone_counts": {
                                "support_nodata_sensitive": 9,
                                "shared_support_magnitude": 4,
                                "persistent_agreement": 12,
                            },
                            "zone_fractions": {
                                "support_nodata_sensitive": 0.36,
                                "shared_support_magnitude": 0.16,
                                "persistent_agreement": 0.48,
                            },
                        },
                    },
                    "velocity_exceedance_5mps": {
                        "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
                        "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 0,
                        "support_only_disagreement_count": 1,
                        "magnitude_only_disagreement_count": 4,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 1.0,
                        "high_uncertainty_cell_fraction": 0.1,
                        "high_uncertainty_support_nodata_fraction": 0.2,
                        "high_uncertainty_shared_support_magnitude_fraction": 0.8,
                        "disagreement_decomposition": {
                            "classification": "shared_support_magnitude_dominated",
                            "high_uncertainty_fraction_explained": {
                                "support_nodata": 0.2,
                                "shared_support_magnitude": 0.8,
                            },
                        },
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "deferrable",
                            "high_uncertainty_cell_count": 2,
                            "support_nodata_cell_count": 0,
                            "shared_support_magnitude_cell_count": 2,
                            "mask_bbox": {"row_min": 2, "row_max": 3, "col_min": 1, "col_max": 3, "xmin": 1.0, "xmax": 3.0, "ymin": 0.0, "ymax": 2.0},
                            "mask_path": None,
                        },
                        "stability_zone_summary": {
                            "layer_stability_zone_class": "deferrable_localized",
                            "dominant_zone_category": "persistent_agreement",
                            "dominant_high_uncertainty_zone_category": "shared_support_magnitude",
                            "closure_role_impact": "no_change",
                            "zone_counts": {
                                "support_nodata_sensitive": 1,
                                "shared_support_magnitude": 4,
                                "persistent_agreement": 20,
                            },
                            "zone_fractions": {
                                "support_nodata_sensitive": 0.04,
                                "shared_support_magnitude": 0.16,
                                "persistent_agreement": 0.8,
                            },
                        },
                    },
                },
                "stability_zone_summary": {
                    "stability_zone_status": "measured_existing_artifacts",
                    "overall_closure_role_change": "no_change",
                    "layer_summaries": {
                        "max_kinetic_energy": {
                            "layer_stability_zone_class": "persistent_closure_limiting",
                            "dominant_zone_category": "shared_support_magnitude",
                            "dominant_high_uncertainty_zone_category": "shared_support_magnitude",
                            "closure_role_impact": "no_change",
                        },
                        "max_jump_height": {
                            "layer_stability_zone_class": "persistent_closure_limiting",
                            "dominant_zone_category": "persistent_agreement",
                            "dominant_high_uncertainty_zone_category": "support_nodata_sensitive",
                            "closure_role_impact": "no_change",
                        },
                        "velocity_exceedance_5mps": {
                            "layer_stability_zone_class": "deferrable_localized",
                            "dominant_zone_category": "persistent_agreement",
                            "dominant_high_uncertainty_zone_category": "shared_support_magnitude",
                            "closure_role_impact": "no_change",
                        },
                    },
                },
                "dominant_layers_by_mean_range": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
                "dominant_layer_summaries": [],
            },
            "validation_output_profile": {
                "final_classification": "no_go",
                "feasibility_decision": "no_go",
                "validation_output_mode": "summary_only",
                "validation_output_blocker_status": "blocker_retained",
                "validation_output_reduced": False,
                "current_validation_file_count": 2005,
                "current_validation_bytes": 571368823,
                "required_provenance_retained": True,
            },
            "reducer_runtime_scaling": {
                "bounded_reducer_scaling_status": "measured",
                "local_single_job_sufficient_for_next_step": True,
                "distributed_execution_authorized": False,
            },
            "gis_cog": {
                "gis_cog_readiness_status": "gis_package_ready_cog_blocked",
                "qgis_manual_qa_status": "not-run",
                "blockers": {"cog_layout": True},
            },
            "context_scope": {
                "final_classification": "blocked_missing_inputs",
                "roads_or_transport_relevance": "unresolved",
                "barriers_or_protection_relevance": "unresolved",
                "water_or_channel_relevance": "unresolved",
            },
            "portability": {
                "portability_preflight_status": "blocked_missing_inputs",
                "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                "missing_input_categories": ["processed_context_root"],
            },
            "contract_audit": {
                "source_scenario_contract_audit_status": "blocked_missing_inputs",
            },
        }


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
