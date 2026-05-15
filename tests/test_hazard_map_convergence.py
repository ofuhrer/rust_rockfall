from __future__ import annotations

import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "compare_hazard_map_convergence.py"
SPEC = importlib.util.spec_from_file_location("compare_hazard_map_convergence", SCRIPT_PATH)
assert SPEC is not None
diagnostic = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = diagnostic
SPEC.loader.exec_module(diagnostic)

FIXTURE = ROOT / "tests" / "fixtures" / "hazard" / "convergence"


class HazardMapConvergenceTests(unittest.TestCase):
    def test_identical_inputs_report_zero_difference(self) -> None:
        reference = FIXTURE / "reference_manifest.json"
        result = diagnostic.compare_hazard_map_convergence([reference, reference])

        self.assertEqual(result["schema_version"], diagnostic.SCHEMA_VERSION)
        self.assertEqual(result["status"], diagnostic.OK_STATUS)
        self.assertEqual(result["reference_run"]["manifest_path"], str(reference))
        self.assertEqual(result["comparisons"][0]["metrics"]["shared_layer_count"], 4)
        self.assertEqual(result["comparisons"][0]["metrics"]["layer_summary_max_abs_diff"], 0.0)
        self.assertEqual(result["comparisons"][0]["metrics"]["layer_summary_sum_abs_diff"], 0.0)
        self.assertEqual(result["comparisons"][0]["metrics"]["conditional_curve_row_count_abs_diff"], 0)
        self.assertEqual(result["comparisons"][0]["metrics"]["output_checksum_mismatch_count"], 0)
        self.assertTrue(result["comparisons"][0]["metrics"]["manifest_checksum_match"])

    def test_changed_metrics_are_detected(self) -> None:
        reference = FIXTURE / "reference_manifest.json"
        candidate = FIXTURE / "perturbed_manifest.json"
        result = diagnostic.compare_hazard_map_convergence([reference, candidate])

        comparison = result["comparisons"][0]
        self.assertGreater(comparison["metrics"]["layer_summary_max_abs_diff"], 0.0)
        self.assertGreater(comparison["metrics"]["layer_summary_sum_abs_diff"], 0.0)
        self.assertEqual(comparison["metrics"]["conditional_curve_row_count_abs_diff"], 1)
        self.assertEqual(comparison["metrics"]["output_checksum_mismatch_count"], 1)
        self.assertEqual(comparison["output_checksum_comparison"]["mismatch_count"], 1)
        self.assertEqual(comparison["layer_comparisons"][0]["layer_key"], "deposition_density")

    def test_missing_inputs_are_reported_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "missing_run"
            result = diagnostic.compare_hazard_map_convergence(
                [FIXTURE / "reference_manifest.json", missing_path]
            )

        self.assertEqual(result["status"], diagnostic.BLOCKED_MISSING_INPUTS)
        self.assertEqual(result["missing_inputs"][0]["requested_path"], str(missing_path))
        self.assertIn("does not exist", result["missing_inputs"][0]["reason"])

    def test_output_schema_fields_remain_stable(self) -> None:
        result = diagnostic.compare_hazard_map_convergence(
            [FIXTURE / "reference_manifest.json", FIXTURE / "perturbed_manifest.json"]
        )

        self.assertEqual(
            sorted(result.keys()),
            [
                "available_input_count",
                "comparisons",
                "invalid_inputs",
                "missing_inputs",
                "overall_metrics",
                "reference_run",
                "requested_input_count",
                "schema_version",
                "status",
            ],
        )
        comparison = result["comparisons"][0]
        self.assertEqual(
            sorted(comparison.keys()),
            [
                "compare_run",
                "compatibility",
                "conditional_curve_comparison",
                "layer_comparisons",
                "metrics",
                "output_checksum_comparison",
                "reference_run",
            ],
        )
        self.assertEqual(
            sorted(comparison["metrics"].keys()),
            [
                "compare_only_layer_count",
                "conditional_curve_measure_symdiff_count",
                "conditional_curve_probability_mode_symdiff_count",
                "conditional_curve_row_count_abs_diff",
                "layer_summary_max_abs_diff",
                "layer_summary_mean_abs_diff",
                "layer_summary_sum_abs_diff",
                "manifest_checksum_match",
                "output_checksum_match_count",
                "output_checksum_mismatch_count",
                "output_checksum_missing_count",
                "output_file_count_abs_diff",
                "output_total_bytes_abs_diff",
                "reference_only_layer_count",
                "shared_layer_count",
            ],
        )


if __name__ == "__main__":
    unittest.main()
