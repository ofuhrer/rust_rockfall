from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_same_scale_stability_frontier.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_same_scale_stability_frontier", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class SameScaleStabilityFrontierTests(unittest.TestCase):
    def test_report_combines_frontier_evidence_and_recommends_informative(self) -> None:
        with patch.object(MODULE, "UNCERTAINTY") as uncertainty_module, patch.object(MODULE, "RUNTIME") as runtime_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "CLOSURE_GAP") as closure_module:
            uncertainty_module.build_sampling_uncertainty_summary.return_value = self._uncertainty_report()
            runtime_module.DEFAULT_ARTIFACTS = ("sentinel",)
            runtime_module.build_report.return_value = self._runtime_report()
            feasibility_module.build_report.return_value = self._feasibility_report()
            closure_module.build_report.return_value = self._closure_report()

            report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "tschamut_same_scale_stability_frontier_v1")
        self.assertEqual(report["frontier_status"], "measured_existing_artifacts")
        self.assertEqual(report["recommendation_class"], "additional_probe_informative")
        self.assertIn("measurable spread", report["recommendation_reason"])
        self.assertEqual(report["compared_trajectory_counts"][1]["trajectory_count_delta"], 0)
        self.assertEqual(report["runtime_output_footprint"][1]["comparison_label"], "sampling_probe_v1_vs_v2")
        self.assertEqual(report["runtime_output_footprint"][2]["proposed_probe_trajectory_count"], 1000)
        self.assertTrue(report["bounded_probe_feasibility"]["boundedness_proof"]["bounded_relative_to_target_validation"])
        self.assertTrue(report["bounded_probe_feasibility"]["boundedness_proof"]["bounded_relative_to_target_hazard"])
        self.assertIn("max_kinetic_energy", report["measured_uncertainty_deltas"]["dominant_layer_spread"])
        self.assertGreater(len(report["frontier_summary"]), 0)

    def test_blocked_helpers_return_pending_contract(self) -> None:
        with patch.object(MODULE, "UNCERTAINTY") as uncertainty_module, patch.object(MODULE, "RUNTIME") as runtime_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "CLOSURE_GAP") as closure_module:
            uncertainty_module.build_sampling_uncertainty_summary.return_value = {"sampling_uncertainty_status": "blocked_missing_inputs"}
            runtime_module.build_report.return_value = {"reducer_scaling_status": "blocked_missing_inputs"}
            feasibility_module.build_report.return_value = {
                "probe_status": "blocked_pending_evidence",
                "bounded_probe_recommendation_status": "blocked_pending_evidence",
            }
            closure_module.build_report.return_value = {"closure_gap_status": "blocked_missing_inputs"}

            report = MODULE.build_report()

        self.assertEqual(report["frontier_status"], "blocked_pending_helper_contract")
        self.assertEqual(report["recommendation_class"], "blocked_pending_helper_contract")
        self.assertIn("helper contract unresolved", report["blocked_reason"])

    def test_text_and_json_smoke(self) -> None:
        with patch.object(MODULE, "UNCERTAINTY") as uncertainty_module, patch.object(MODULE, "RUNTIME") as runtime_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "CLOSURE_GAP") as closure_module:
            uncertainty_module.build_sampling_uncertainty_summary.return_value = self._uncertainty_report()
            runtime_module.DEFAULT_ARTIFACTS = ("sentinel",)
            runtime_module.build_report.return_value = self._runtime_report()
            feasibility_module.build_report.return_value = self._feasibility_report()
            closure_module.build_report.return_value = self._closure_report()

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "text"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Same-Scale Ensemble Stability Frontier", buffer.getvalue())
            self.assertIn("additional_probe_informative", buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "json"])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())

    def _uncertainty_report(self) -> dict[str, object]:
        return {
            "sampling_uncertainty_status": "sampling_uncertainty_measured",
            "pairwise_comparison_count": 6,
            "artifact_ids": [
                "validation_tschamut_public_conditional_gate_v1",
                "validation_tschamut_public_target_gate_v1",
                "validation_tschamut_public_sampling_sensitivity_v1_full",
                "validation_tschamut_public_sampling_sensitivity_v2_full",
            ],
            "ensemble_sizes": [6, 100, 12, 12],
            "comparison_pairs_run": [
                {
                    "reference_artifact_id": "validation_tschamut_public_conditional_gate_v1",
                    "compare_artifact_id": "validation_tschamut_public_target_gate_v1",
                    "shared_cellwise_layer_count": 22,
                    "cellwise_l1_abs_diff_sum": 100.0,
                    "cellwise_linf_abs_diff_max": 3.0,
                    "cellwise_rmse_max": 1.0,
                    "cellwise_nonzero_jaccard_min": 0.5,
                    "cellwise_nodata_mismatch_count": 4,
                    "output_checksum_match_count": 8,
                    "output_checksum_mismatch_count": 36,
                    "output_checksum_missing_count": 13,
                    "status": "ok",
                    "layer_metrics": {
                        "max_kinetic_energy": {"l1_abs_diff": 2.0, "nonzero_jaccard": 1.0},
                        "max_jump_height": {"l1_abs_diff": 1.0, "nonzero_jaccard": 0.75},
                        "velocity_exceedance_5mps": {"l1_abs_diff": 0.25, "nonzero_jaccard": 0.8},
                    },
                },
                {
                    "reference_artifact_id": "validation_tschamut_public_sampling_sensitivity_v1_full",
                    "compare_artifact_id": "validation_tschamut_public_sampling_sensitivity_v2_full",
                    "shared_cellwise_layer_count": 22,
                    "cellwise_l1_abs_diff_sum": 12.0,
                    "cellwise_linf_abs_diff_max": 0.2,
                    "cellwise_rmse_max": 0.01,
                    "cellwise_nonzero_jaccard_min": 0.7,
                    "cellwise_nodata_mismatch_count": 0,
                    "output_checksum_match_count": 5,
                    "output_checksum_mismatch_count": 3,
                    "output_checksum_missing_count": 0,
                    "status": "ok",
                    "layer_metrics": {
                        "max_kinetic_energy": {"l1_abs_diff": 4.0, "nonzero_jaccard": 1.0},
                        "max_jump_height": {"l1_abs_diff": 0.8, "nonzero_jaccard": 0.8},
                        "velocity_exceedance_5mps": {"l1_abs_diff": 0.1, "nonzero_jaccard": 0.9},
                    },
                },
            ],
            "dominant_layer_spread": {
                "max_kinetic_energy": {
                    "l1_abs_diff": {"mean": 10.0, "range": 4.0},
                    "nonzero_jaccard": {"mean": 1.0},
                },
                "max_jump_height": {
                    "l1_abs_diff": {"mean": 2.0, "range": 1.0},
                    "nonzero_jaccard": {"mean": 0.8},
                },
                "velocity_exceedance_5mps": {
                    "l1_abs_diff": {"mean": 0.2, "range": 0.05},
                    "nonzero_jaccard": {"mean": 0.85},
                },
            },
            "support_or_nodata_sensitivity": {},
        }

    def _runtime_report(self) -> dict[str, object]:
        return {
            "reducer_scaling_status": "measured_existing_artifacts",
            "local_single_job_sufficient_for_next_step": True,
            "comparison_pairs": [
                {
                    "label": "gate_vs_target",
                    "validation_runtime_delta_seconds": 100.0,
                    "validation_file_count_delta": 10,
                    "byte_count_delta": 1000,
                    "hazard_file_count_delta": 0,
                    "hazard_byte_count_delta": 20,
                },
                {
                    "label": "sampling_probe_v1_vs_v2",
                    "validation_runtime_delta_seconds": 0.5,
                    "validation_file_count_delta": 0,
                    "byte_count_delta": 25,
                    "hazard_file_count_delta": 1,
                    "hazard_byte_count_delta": 10,
                },
                {
                    "label": "target_full_vs_native_rebuildable_reduced",
                    "validation_runtime_delta_seconds": -90.0,
                    "validation_file_count_delta": -90,
                    "byte_count_delta": -9000,
                    "hazard_file_count_delta": -8,
                    "hazard_byte_count_delta": -80,
                },
            ],
        }

    def _feasibility_report(self) -> dict[str, object]:
        return {
            "probe_status": "deferred_pending_authorization",
            "bounded_probe_recommendation_status": "deferred_pending_authorization",
            "planning_status": "deferred_pending_authorization",
            "proposed_probe": {
                "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
                "trajectory_count": 1000,
                "validation_output_mode": "rebuildable_reduced_output",
                "expected_output_file_count": 6,
                "expected_output_bytes": 1884291,
            },
            "boundedness_proof": {
                "bounded_relative_to_target_validation": True,
                "bounded_relative_to_target_hazard": True,
                "output_byte_ratio_to_target_validation": 0.01,
                "output_file_ratio_to_target_validation": 0.01,
                "output_byte_ratio_to_target_hazard": 0.02,
                "output_file_ratio_to_target_hazard": 0.02,
            },
        }

    def _closure_report(self) -> dict[str, object]:
        return {
            "closure_gap_status": "measured_gaps_remain",
            "current_closure_status": "inconclusive",
            "current_interpretation_status": "inconclusive_conditional_diagnostic",
            "closure_limiting_layers": ["max_kinetic_energy", "max_jump_height"],
            "deferrable_layers": ["velocity_exceedance_5mps"],
            "scientific_blocker_deltas": [],
            "workflow_product_blocker_deltas": [],
            "claim_boundaries": {},
        }


if __name__ == "__main__":
    unittest.main()
