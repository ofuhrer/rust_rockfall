from __future__ import annotations

import json
import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

import scripts.build_hazard_layers as hazard
import yaml


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

    def test_cellwise_identical_inputs_report_zero_differences_by_layer(self) -> None:
        reference = FIXTURE / "cellwise" / "reference_manifest.json"
        result = diagnostic.compare_hazard_map_convergence([reference, reference])

        comparison = result["comparisons"][0]
        cellwise = comparison["cellwise_metrics"]
        self.assertEqual(
            sorted(cellwise.keys()),
            [
                "compare_only_layer_count",
                "layer_comparisons",
                "layer_count",
                "overall_metrics",
                "reference_only_layer_count",
                "shared_layer_count",
            ],
        )
        self.assertEqual(cellwise["layer_count"], 4)
        self.assertEqual(cellwise["shared_layer_count"], 4)
        self.assertEqual(cellwise["overall_metrics"]["cellwise_linf_abs_diff_max"], 0.0)
        self.assertEqual(cellwise["overall_metrics"]["cellwise_l1_abs_diff_sum"], 0.0)
        self.assertEqual(cellwise["overall_metrics"]["cellwise_rmse_max"], 0.0)
        self.assertEqual(cellwise["overall_metrics"]["cellwise_nodata_mismatch_count"], 0)
        reach = next(layer for layer in cellwise["layer_comparisons"] if layer["layer_key"] == "reach_probability")
        self.assertEqual(
            sorted(reach.keys()),
            [
                "compare_missing_cell_count",
                "compare_nonzero_cell_count",
                "compared_cell_count",
                "grid_shape",
                "l1_abs_diff",
                "layer_key",
                "layer_name",
                "linf_abs_diff",
                "missing_cell_metrics",
                "nodata_mismatch_count",
                "nonzero_jaccard",
                "nonzero_metrics",
                "nonzero_overlap_count",
                "nonzero_union_count",
                "reference_missing_cell_count",
                "reference_nonzero_cell_count",
                "rmse",
                "threshold_exceedance_disagreement",
                "threshold_exceedance_disagreement_count",
                "value_metrics",
            ],
        )
        self.assertEqual(reach["value_metrics"]["linf_abs_diff"], 0.0)
        self.assertEqual(reach["value_metrics"]["l1_abs_diff"], 0.0)
        self.assertEqual(reach["value_metrics"]["rmse"], 0.0)
        self.assertEqual(reach["nonzero_metrics"]["nonzero_jaccard"], 1.0)
        self.assertEqual(reach["threshold_exceedance_disagreement"][0]["disagreement_cell_count"], 0)

    def test_cellwise_shifted_grids_are_detected_even_when_summaries_match(self) -> None:
        reference = FIXTURE / "cellwise" / "reference_manifest.json"
        candidate = FIXTURE / "cellwise" / "shifted_manifest.json"
        result = diagnostic.compare_hazard_map_convergence([reference, candidate])

        comparison = result["comparisons"][0]
        summary_reach = next(layer for layer in comparison["layer_comparisons"] if layer["layer_key"] == "reach_probability")
        cellwise_reach = next(
            layer for layer in comparison["cellwise_metrics"]["layer_comparisons"] if layer["layer_key"] == "reach_probability"
        )
        self.assertEqual(summary_reach["max_abs_diff"], 0.0)
        self.assertGreater(cellwise_reach["value_metrics"]["linf_abs_diff"], 0.0)
        self.assertGreater(cellwise_reach["value_metrics"]["l1_abs_diff"], 0.0)
        self.assertEqual(cellwise_reach["nonzero_metrics"]["nonzero_jaccard"], 0.0)
        self.assertEqual(cellwise_reach["threshold_exceedance_disagreement"][0]["disagreement_cell_count"], 4)
        jump = next(layer for layer in comparison["cellwise_metrics"]["layer_comparisons"] if layer["layer_key"] == "max_jump_height")
        self.assertEqual(jump["missing_cell_metrics"]["nodata_mismatch_count"], 1)
        self.assertEqual(comparison["cellwise_metrics"]["overall_metrics"]["cellwise_nodata_mismatch_count"], 1)

    def test_cellwise_shape_mismatches_fail_clearly(self) -> None:
        reference = FIXTURE / "cellwise" / "reference_manifest.json"
        candidate = FIXTURE / "cellwise" / "shape_mismatch_manifest.json"
        result = diagnostic.compare_hazard_map_convergence([reference, candidate])

        self.assertEqual(result["status"], diagnostic.BLOCKED_INVALID_INPUTS)
        self.assertEqual(
            result["invalid_inputs"][0]["requested_path"],
            str((FIXTURE / "cellwise" / "shape_mismatch" / "reach_probability.asc").resolve()),
        )
        self.assertIn("shape mismatch", result["invalid_inputs"][0]["reason"])

    def test_missing_cellwise_grid_files_are_reported_as_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            reference = json.loads((FIXTURE / "cellwise" / "reference_manifest.json").read_text())
            missing_manifest = work / "missing_cellwise_manifest.json"
            reference["cellwise_layers"][0]["grid_path"] = "cellwise/reference/missing_reach_probability.asc"
            missing_manifest.write_text(json.dumps(reference), encoding="utf-8")

            result = diagnostic.compare_hazard_map_convergence(
                [FIXTURE / "cellwise" / "reference_manifest.json", missing_manifest]
            )

        self.assertEqual(result["status"], diagnostic.BLOCKED_MISSING_INPUTS)
        self.assertEqual(result["invalid_inputs"], [])
        self.assertEqual(
            result["missing_inputs"][0]["requested_path"],
            str((work / "cellwise/reference/missing_reach_probability.asc").resolve()),
        )
        self.assertIn("cellwise grid file does not exist", result["missing_inputs"][0]["reason"])

    def test_emitted_hazard_manifest_cellwise_paths_feed_convergence_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml.safe_load((ROOT / "tests" / "fixtures" / "hazard" / "plane_case.yaml").read_text())
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(ROOT / "validation" / "data" / "processed" / "swisstopo_pilot" / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(
                    ROOT / "validation" / "data" / "processed" / "swisstopo_pilot" / "swissalti3d_pilot_metadata.yaml"
                ),
            }
            case_path = work / "plane_case.yaml"
            case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--diagnostics",
                    str(ROOT / "tests" / "fixtures" / "hazard" / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                    "--kinetic-energy-exceedance-j",
                    "5.0",
                    "--jump-height-exceedance-m",
                    "0.25",
                ]
            )

            self.assertEqual(status, 0)
            manifest_path = output_dir / "hazard_fixture_plane_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            self.assertTrue(manifest["cellwise_layers"])
            self.assertTrue(all(entry["grid_path"].endswith(".asc") for entry in manifest["cellwise_layers"]))

            stripped_manifest_path = work / "hazard_fixture_plane_manifest_without_cellwise.json"
            stripped_manifest = dict(manifest)
            stripped_manifest.pop("cellwise_layers", None)
            stripped_manifest_path.write_text(json.dumps(stripped_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = diagnostic.compare_hazard_map_convergence([stripped_manifest_path, stripped_manifest_path])

            self.assertEqual(result["status"], diagnostic.OK_STATUS)
            self.assertIsNotNone(result["comparisons"][0]["cellwise_metrics"])
            reach = next(
                layer
                for layer in result["comparisons"][0]["cellwise_metrics"]["layer_comparisons"]
                if layer["layer_name"] == "reach_probability"
            )
            self.assertEqual(reach["layer_key"], "reach_probability")
            self.assertIn("linf_abs_diff", reach)
            self.assertIn("nonzero_jaccard", reach)

    def test_emitted_hazard_manifest_missing_cellwise_grid_is_reported_as_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml.safe_load((ROOT / "tests" / "fixtures" / "hazard" / "plane_case.yaml").read_text())
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(ROOT / "validation" / "data" / "processed" / "swisstopo_pilot" / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(
                    ROOT / "validation" / "data" / "processed" / "swisstopo_pilot" / "swissalti3d_pilot_metadata.yaml"
                ),
            }
            case_path = work / "plane_case.yaml"
            case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--diagnostics",
                    str(ROOT / "tests" / "fixtures" / "hazard" / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                ]
            )

            self.assertEqual(status, 0)
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            missing_manifest_path = work / "hazard_fixture_plane_manifest_missing_grid.json"
            manifest["cellwise_layers"][0]["grid_path"] = "missing/reach_probability.asc"
            missing_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = diagnostic.compare_hazard_map_convergence([missing_manifest_path, missing_manifest_path])

            self.assertEqual(result["status"], diagnostic.BLOCKED_MISSING_INPUTS)
            self.assertTrue(result["missing_inputs"])
            self.assertIn("cellwise grid file does not exist", result["missing_inputs"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
