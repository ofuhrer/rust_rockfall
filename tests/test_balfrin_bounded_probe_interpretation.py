from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_balfrin_bounded_probe_interpretation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_balfrin_bounded_probe_interpretation", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BalfrinBoundedProbeInterpretationTests(unittest.TestCase):
    def test_measured_probe_keeps_the_closure_inconclusive(self) -> None:
        with patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(
            MODULE, "SPATIAL"
        ) as spatial_module, patch.object(MODULE, "STABILITY") as stability_module, patch.object(
            MODULE, "CLOSURE_GAP"
        ) as closure_module:
            feasibility_module.build_report.return_value = self.probe_report()
            spatial_module.build_report.return_value = self.same_scale_uncertainty_report()
            stability_module.build_report.return_value = self.same_scale_stability_report()
            closure_module.build_report.return_value = self.closure_gap_report()

            report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_bounded_probe_interpretation_v1")
        self.assertEqual(report["probe_interpretation_status"], "unchanged")
        self.assertEqual(report["bounded_probe_status"], "deferred_pending_authorization")
        self.assertEqual(report["closure_status"], "inconclusive")
        self.assertTrue(report["keep_closure_inconclusive"])
        self.assertFalse(report["comparison_summary"]["closure_criterion_changed"])
        self.assertIn("keeps closure inconclusive", report["comparison_summary"]["summary"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_no_change_override_is_preserved_in_the_summary(self) -> None:
        with patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(
            MODULE, "SPATIAL"
        ) as spatial_module, patch.object(MODULE, "STABILITY") as stability_module, patch.object(
            MODULE, "CLOSURE_GAP"
        ) as closure_module:
            feasibility_module.build_report.return_value = self.probe_report()
            spatial_module.build_report.return_value = self.same_scale_uncertainty_report()
            stability_module.build_report.return_value = self.same_scale_stability_report()
            closure_module.build_report.return_value = self.closure_gap_report()

            report = MODULE.build_report({"comparison_status": "unchanged"})

        self.assertEqual(report["probe_interpretation_status"], "unchanged")
        self.assertEqual(report["comparison_summary"]["status"], "unchanged")
        self.assertTrue(report["comparison_summary"]["keep_closure_inconclusive"])
        self.assertEqual(report["comparison_summary"]["closure_status"], "inconclusive")

    def test_missing_probe_blocks_the_report(self) -> None:
        report = MODULE.build_report({"missing_inputs": ["bounded_probe_report"]})

        self.assertEqual(report["probe_interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["comparison_summary"]["status"], "blocked_missing_inputs")
        self.assertTrue(report["keep_closure_inconclusive"])
        self.assertEqual(report["missing_inputs"], ["bounded_probe_report"])

    def test_cli_emits_json_and_text_for_measured_report(self) -> None:
        with patch.object(MODULE, "FEASIBILITY") as feasibility_module, patch.object(
            MODULE, "SPATIAL"
        ) as spatial_module, patch.object(MODULE, "STABILITY") as stability_module, patch.object(
            MODULE, "CLOSURE_GAP"
        ) as closure_module:
            feasibility_module.build_report.return_value = self.probe_report()
            spatial_module.build_report.return_value = self.same_scale_uncertainty_report()
            stability_module.build_report.return_value = self.same_scale_stability_report()
            closure_module.build_report.return_value = self.closure_gap_report()

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "text"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Balfrin Bounded Probe Interpretation", buffer.getvalue())
            self.assertIn("probe_interpretation_status: unchanged", buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "json"])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())

    def probe_report(self) -> dict[str, object]:
        return {
            "schema_version": "bounded_next_ensemble_feasibility_probe_v1",
            "probe_status": "deferred_pending_authorization",
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

    def same_scale_uncertainty_report(self) -> dict[str, object]:
        return {
            "schema_version": "spatial_same_scale_uncertainty_v1",
            "spatial_uncertainty_status": "measured_existing_artifacts",
            "selected_layers": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
            "dominant_layers_by_mean_range": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
        }

    def same_scale_stability_report(self) -> dict[str, object]:
        return {
            "schema_version": "tschamut_same_scale_stability_frontier_v1",
            "frontier_status": "measured_existing_artifacts",
            "recommendation_class": "additional_probe_informative",
        }

    def closure_gap_report(self) -> dict[str, object]:
        return {
            "schema_version": "tschamut_closure_gap_deltas_v1",
            "closure_gap_status": "measured_gaps_remain",
            "current_closure_status": "inconclusive",
            "current_interpretation_status": "inconclusive_conditional_diagnostic",
            "closure_limiting_layers": [{"layer_key": "max_kinetic_energy"}, {"layer_key": "max_jump_height"}],
            "deferrable_layers": [{"layer_key": "velocity_exceedance_5mps"}],
            "workflow_product_blocker_deltas": [],
        }


if __name__ == "__main__":
    unittest.main()
