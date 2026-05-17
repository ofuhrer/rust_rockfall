from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_balfrin_ensemble_frontier.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_balfrin_ensemble_frontier", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BalfrinEnsembleFrontierTests(unittest.TestCase):
    def test_measured_report_identifies_a_bounded_defer_recommendation(self) -> None:
        with patch.object(MODULE, "SCIENTIFIC") as scientific_module, patch.object(MODULE, "SINGLE_JOB") as single_job_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "STABILITY") as stability_module:
            scientific_module.build_report.return_value = self.scientific_report()
            single_job_module.build_summary.return_value = self.single_job_summary()
            feasibility_module.build_report.return_value = self.feasibility_report()
            stability_module.build_report.return_value = self.stability_report()

            report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_ensemble_frontier_v1")
        self.assertEqual(report["frontier_status"], "measured_existing_artifacts")
        self.assertEqual(report["recommendation_class"], "defer_small_bounded_ensemble")
        self.assertEqual(report["minimum_useful_ensemble_recommendation"]["decision"], "defer")
        self.assertEqual(report["minimum_useful_ensemble_recommendation"]["ensemble_size"], 1000)
        self.assertEqual(report["minimum_useful_ensemble_recommendation"]["validation_output_mode"], "rebuildable_reduced_output")
        self.assertLess(report["output_growth"]["output_file_delta"], 0)
        self.assertLess(report["output_growth"]["output_byte_delta"], 0)
        self.assertGreater(report["runtime_growth"]["runtime_growth_factor_validation"], 1.0)
        self.assertTrue(report["rebuildability_cost"]["bounded_relative_to_target_validation"])
        self.assertTrue(report["rebuildability_cost"]["bounded_relative_to_target_hazard"])
        self.assertEqual(report["uncertainty_reduction"]["stability_recommendation_class"], "additional_probe_informative")
        self.assertGreater(len(report["frontier_summary"]), 0)

    def test_missing_inputs_block_the_frontier_report(self) -> None:
        report = MODULE.build_report({"missing_inputs": ["scientific_delta_report", "single_job_execution_summary"]})

        self.assertEqual(report["frontier_status"], "blocked_missing_inputs")
        self.assertEqual(report["recommendation_class"], "blocked_pending_helper_contract")
        self.assertIn("scientific_delta_report", report["recommendation_reason"])
        self.assertEqual(report["minimum_useful_ensemble_recommendation"], {})
        self.assertEqual(report["frontier_summary"], [])

    def test_blocked_feasibility_helper_blocks_the_frontier_report(self) -> None:
        with patch.object(MODULE, "SCIENTIFIC") as scientific_module, patch.object(MODULE, "SINGLE_JOB") as single_job_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "STABILITY") as stability_module:
            scientific_module.build_report.return_value = self.scientific_report()
            single_job_module.build_summary.return_value = self.single_job_summary()
            feasibility_module.build_report.return_value = {
                "schema_version": "bounded_next_ensemble_feasibility_probe_v1",
                "probe_status": "blocked_missing_optional_probabilistic_metadata",
                "bounded_probe_recommendation_status": "blocked_missing_optional_probabilistic_metadata",
                "planning_status": "blocked_missing_optional_probabilistic_metadata",
                "metadata_contract": {"status": "blocked_missing_optional_probabilistic_metadata"},
            }
            stability_module.build_report.return_value = self.stability_report()

            report = MODULE.build_report()

        self.assertEqual(report["frontier_status"], "blocked_missing_inputs")
        self.assertEqual(report["recommendation_class"], "blocked_pending_helper_contract")
        self.assertIn("feasibility_probe_status=blocked_missing_optional_probabilistic_metadata", report["recommendation_reason"])
        self.assertEqual(report["minimum_useful_ensemble_recommendation"], {})
        self.assertEqual(report["frontier_summary"], [])

    def test_complete_metadata_feasibility_path_drives_the_bounded_frontier(self) -> None:
        with patch.object(MODULE, "SCIENTIFIC") as scientific_module, patch.object(MODULE, "SINGLE_JOB") as single_job_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "STABILITY") as stability_module:
            scientific_module.build_report.return_value = self.scientific_report()
            single_job_module.build_summary.return_value = self.single_job_summary()
            feasibility_module.build_report.return_value = self.feasibility_report()
            stability_module.build_report.return_value = self.stability_report()

            report = MODULE.build_report()

        self.assertEqual(report["frontier_status"], "measured_existing_artifacts")
        self.assertEqual(report["recommendation_class"], "defer_small_bounded_ensemble")
        self.assertEqual(report["helper_statuses"]["feasibility_probe_status"], "deferred_pending_authorization")
        self.assertEqual(report["helper_statuses"]["feasibility_metadata_contract_status"], "complete")
        self.assertEqual(report["minimum_useful_ensemble_recommendation"]["decision"], "defer")
        self.assertEqual(report["minimum_useful_ensemble_recommendation"]["ensemble_size"], 1000)
        self.assertIn("measured Balfrin evidence still shows useful uncertainty spread", report["recommendation_reason"])
        self.assertGreater(len(report["frontier_summary"]), 0)

    def test_cli_emits_text_and_json_for_measured_report(self) -> None:
        with patch.object(MODULE, "SCIENTIFIC") as scientific_module, patch.object(MODULE, "SINGLE_JOB") as single_job_module, patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(MODULE, "STABILITY") as stability_module:
            scientific_module.build_report.return_value = self.scientific_report()
            single_job_module.build_summary.return_value = self.single_job_summary()
            feasibility_module.build_report.return_value = self.feasibility_report()
            stability_module.build_report.return_value = self.stability_report()

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "text"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Balfrin Practical Ensemble Frontier", buffer.getvalue())
            self.assertIn("defer_small_bounded_ensemble", buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "json"])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())

    def scientific_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_scientific_delta_report_v1",
            "scientific_delta_status": "measured_existing_artifacts",
            "scientific_delta_summary": {
                "status": "measured_existing_artifacts",
                "same_scale_focus": {
                    "uncertainty_layers": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
                    "dominant_layers_by_mean_range": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
                    "closure_limiting_layers": ["max_kinetic_energy", "max_jump_height"],
                    "deferrable_layers": ["velocity_exceedance_5mps"],
                },
            },
        }

    def single_job_summary(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_single_job_execution_sufficiency_v1",
            "decision": "defer",
            "single_job_sufficient_for_next_step": True,
            "wall_time_evidence": {
                "current_gap_runtime_seconds": 17.84,
                "reproduction_validation_wall_seconds": 55.277021307,
                "reproduction_hazard_wall_seconds": 55.12473134789616,
            },
            "output_size_evidence": {
                "current_gap_output_file_count": 191,
                "current_gap_output_bytes": 267527120,
            },
        }

    def feasibility_report(self) -> dict[str, object]:
        return {
            "schema_version": "bounded_next_ensemble_feasibility_probe_v1",
            "probe_status": "deferred_pending_optional_probabilistic_metadata",
            "bounded_probe_recommendation_status": "deferred_pending_authorization",
            "proposed_probe": {
                "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
                "trajectory_count": 1000,
                "validation_output_mode": "rebuildable_reduced_output",
                "expected_output_file_count": 6,
                "expected_output_bytes": 1884291,
                "expected_artifact_families": [
                    "diagnostics_json",
                    "manifest_json",
                    "trajectory_csv",
                    "ensemble_deposition_csv",
                ],
                "expected_command": "command",
            },
            "metadata_contract": {
                "status": "complete",
                "missing_fields": [],
            },
            "boundedness_proof": {
                "bounded_relative_to_target_validation": True,
                "bounded_relative_to_target_hazard": True,
                "output_byte_ratio_to_target_validation": 0.01,
                "output_file_ratio_to_target_validation": 0.01,
                "output_byte_ratio_to_target_hazard": 0.02,
                "output_file_ratio_to_target_hazard": 0.02,
            },
            "measured_evidence": {
                "rebuildable_reduced_output_file_count": 6,
                "rebuildable_reduced_output_bytes": 1884291,
                "target_validation_output_file_count": 2004,
                "target_validation_output_bytes": 571131205,
                "target_hazard_output_file_count": 54,
                "target_hazard_output_bytes": 75423367,
            },
        }

    def stability_report(self) -> dict[str, object]:
        return {
            "schema_version": "tschamut_same_scale_stability_frontier_v1",
            "frontier_status": "measured_existing_artifacts",
            "recommendation_class": "additional_probe_informative",
            "recommendation_reason": "measurable spread remains bounded",
            "frontier_summary": ["summary"],
            "measured_uncertainty_deltas": {
                "dominant_layer_spread": {
                    "max_kinetic_energy": {"l1_abs_diff": {"mean": 10.0}},
                    "max_jump_height": {"l1_abs_diff": {"mean": 2.0}},
                }
            },
        }


if __name__ == "__main__":
    unittest.main()
