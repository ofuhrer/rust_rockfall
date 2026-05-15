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
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["max_jump_height"]["closure_role"], "closure_limiting")
        self.assertEqual(spatial["layer_roles"]["velocity_exceedance_5mps"]["closure_role"], "deferrable")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["mask_status"], "available")
        self.assertEqual(spatial["layer_roles"]["max_kinetic_energy"]["mask_closure_role"], "closure_limiting")
        self.assertGreaterEqual(spatial["layer_roles"]["max_kinetic_energy"]["high_uncertainty_cell_count"], 0)
        self.assertGreaterEqual(spatial["layer_roles"]["max_jump_height"]["support_nodata_cell_count"], 0)
        self.assertEqual(spatial["mask_status"], "available")
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
                "layer_summaries": {
                    "max_kinetic_energy": {
                        "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                        "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 12,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 0.5,
                        "high_uncertainty_cell_fraction": 0.1,
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "closure_limiting",
                            "high_uncertainty_cell_count": 2,
                            "support_nodata_cell_count": 12,
                            "shared_support_magnitude_cell_count": 4,
                            "mask_bbox": {"row_min": 1, "row_max": 2, "col_min": 1, "col_max": 2, "xmin": 1.0, "xmax": 3.0, "ymin": 1.0, "ymax": 3.0},
                            "mask_path": None,
                        },
                    },
                    "max_jump_height": {
                        "uncertainty_concentration_class": "dominated_by_nodata_support_differences",
                        "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 8,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 0.7,
                        "high_uncertainty_cell_fraction": 0.05,
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "closure_limiting",
                            "high_uncertainty_cell_count": 1,
                            "support_nodata_cell_count": 8,
                            "shared_support_magnitude_cell_count": 3,
                            "mask_bbox": {"row_min": 0, "row_max": 1, "col_min": 0, "col_max": 1, "xmin": 0.0, "xmax": 2.0, "ymin": 2.0, "ymax": 4.0},
                            "mask_path": None,
                        },
                    },
                    "velocity_exceedance_5mps": {
                        "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
                        "interpretation_note": "synthetic",
                        "nodata_disagreement_count": 0,
                        "shared_valid_cell_count": 20,
                        "analysis_cell_count": 25,
                        "nonzero_support_stability_fraction": 1.0,
                        "high_uncertainty_cell_fraction": 0.1,
                        "mask_evidence": {
                            "mask_status": "available",
                            "closure_role": "deferrable",
                            "high_uncertainty_cell_count": 2,
                            "support_nodata_cell_count": 0,
                            "shared_support_magnitude_cell_count": 2,
                            "mask_bbox": {"row_min": 2, "row_max": 3, "col_min": 1, "col_max": 3, "xmin": 1.0, "xmax": 3.0, "ymin": 0.0, "ymax": 2.0},
                            "mask_path": None,
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
