from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_spatial_same_scale_uncertainty.py"
SPEC = importlib.util.spec_from_file_location("summarize_spatial_same_scale_uncertainty", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = summary_script
SPEC.loader.exec_module(summary_script)


class SpatialSameScaleUncertaintyTests(unittest.TestCase):
    def test_reports_spatial_concentration_and_json_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = self._write_artifacts(Path(tmp))
            read_only_report = summary_script.build_report(artifacts, summary_script.DEFAULT_HAZARD_LAYERS, top_n=3)
            self.assertIsNone(read_only_report["layer_summaries"]["max_kinetic_energy"]["mask_evidence"]["mask_path"])
            mask_output_dir = Path(tmp) / "masks"
            report = summary_script.build_report(
                artifacts,
                summary_script.DEFAULT_HAZARD_LAYERS,
                top_n=3,
                mask_output_dir=mask_output_dir,
            )

            self.assertEqual(report["spatial_uncertainty_status"], "measured_existing_artifacts")
            self.assertEqual(report["selected_layers"], list(summary_script.DEFAULT_HAZARD_LAYERS))
            self.assertFalse(report["scale_up_authorized"])
            self.assertFalse(report["operational_claims_allowed"])
            self.assertEqual(report["mask_status"], "available")
            self.assertEqual(report["layer_summaries"]["max_kinetic_energy"]["uncertainty_concentration_class"], "spatially_localized_shared_support_magnitude")
            self.assertEqual(report["layer_summaries"]["max_jump_height"]["uncertainty_concentration_class"], "dominated_by_nodata_support_differences")
            self.assertEqual(report["layer_summaries"]["velocity_exceedance_5mps"]["uncertainty_concentration_class"], "diffuse_across_shared_support")
            self.assertGreater(report["layer_summaries"]["max_kinetic_energy"]["high_uncertainty_cell_count"], 0)
            self.assertGreaterEqual(len(report["layer_summaries"]["max_kinetic_energy"]["top_high_uncertainty_cells"]), 1)
            self.assertLessEqual(len(report["layer_summaries"]["max_kinetic_energy"]["top_high_uncertainty_cells"]), 3)
            self.assertIsNotNone(report["layer_summaries"]["max_kinetic_energy"]["high_uncertainty_bbox"])
            self.assertLess(report["layer_summaries"]["max_kinetic_energy"]["nodata_disagreement_fraction"], 0.15)

            kinetic_mask = report["layer_summaries"]["max_kinetic_energy"]["mask_evidence"]
            jump_mask = report["layer_summaries"]["max_jump_height"]["mask_evidence"]
            velocity_mask = report["layer_summaries"]["velocity_exceedance_5mps"]["mask_evidence"]
            self.assertEqual(kinetic_mask["mask_status"], "available")
            self.assertEqual(kinetic_mask["closure_role"], "closure_limiting")
            self.assertEqual(kinetic_mask["high_uncertainty_cell_count"], 1)
            self.assertGreater(kinetic_mask["shared_support_magnitude_cell_count"], 0)
            self.assertGreaterEqual(kinetic_mask["mask_cell_count"], kinetic_mask["high_uncertainty_cell_count"])
            self.assertIsNotNone(kinetic_mask["mask_bbox"])
            self.assertIsNotNone(kinetic_mask["mask_path"])
            self.assertTrue(Path(kinetic_mask["mask_path"]).exists())
            self.assertEqual(jump_mask["closure_role"], "closure_limiting")
            self.assertEqual(jump_mask["mask_status"], "available")
            self.assertGreater(jump_mask["support_nodata_cell_count"], 0)
            self.assertIsNotNone(velocity_mask["mask_path"])
            self.assertTrue(Path(velocity_mask["mask_path"]).exists())
            self.assertEqual(velocity_mask["closure_role"], "unresolved")

            rendered = summary_script.render_text(report)
            self.assertIn("spatial same-scale uncertainty: measured_existing_artifacts", rendered)
            self.assertIn("max_kinetic_energy", rendered)
            self.assertIn("dominated_by_nodata_support_differences", rendered)
            self.assertIn("mask role=", rendered)

            payload = json.loads(json.dumps(report))
            self.assertEqual(payload["schema_version"], summary_script.SCHEMA_VERSION)

            expected_mask_files = {
                mask_output_dir / "max_kinetic_energy_mask_summary.json",
                mask_output_dir / "max_jump_height_mask_summary.json",
                mask_output_dir / "velocity_exceedance_5mps_mask_summary.json",
            }
            self.assertTrue(expected_mask_files.issubset({path for path in mask_output_dir.iterdir()}))

    def test_layer_selection_deduplicates(self) -> None:
        self.assertEqual(
            summary_script.normalize_layer_selection(["max_kinetic_energy", "max_kinetic_energy", "max_jump_height"]),
            ("max_kinetic_energy", "max_jump_height"),
        )

    def test_missing_inputs_are_blocked_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = list(self._write_artifacts(Path(tmp)))
            target_manifest = Path(artifacts[1])
            missing_grid = target_manifest.parent / "missing.asc"
            data = json.loads(target_manifest.read_text())
            data["cellwise_layers"][0]["grid_path"] = str(missing_grid)
            target_manifest.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            report = summary_script.build_report(tuple(artifacts), summary_script.DEFAULT_HAZARD_LAYERS, top_n=2)
            self.assertEqual(report["spatial_uncertainty_status"], "blocked_missing_inputs")
            self.assertIn("missing", report["blocked_reason"])
            self.assertTrue(report["missing_input_paths"])

    def _write_artifacts(self, root: Path):
        artifact_specs = []
        values_by_layer = {
            "max_kinetic_energy": [
                [
                    [1, 1, 1],
                    [1, 10, 1],
                    [1, 1, 1],
                ],
                [
                    [1, 1, 1],
                    [1, 15, 1],
                    [1, 1, 1],
                ],
                [
                    [1, 1, 1],
                    [1, 20, 1],
                    [1, 1, 1],
                ],
                [
                    [1, 1, 1],
                    [1, 25, 1],
                    [1, 1, 1],
                ],
            ],
            "max_jump_height": [
                [
                    [None, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                ],
                [
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                ],
                [
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                ],
                [
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, None],
                    [0.5, 0.5, 0.5],
                ],
            ],
            "velocity_exceedance_5mps": [
                [
                    [0, 0, 1],
                    [1, 1, 1],
                    [0, 0, 1],
                ],
                [
                    [1, 0, 1],
                    [1, 2, 1],
                    [0, 0, 1],
                ],
                [
                    [0, 1, 1],
                    [2, 1, 1],
                    [0, 1, 1],
                ],
                [
                    [1, 1, 1],
                    [1, 1, 2],
                    [1, 0, 1],
                ],
            ],
        }
        artifact_ids = ("gate_v1", "target_gate_v1", "sampling_sensitivity_v1_full", "sampling_sensitivity_v2_full")
        for index, artifact_id in enumerate(artifact_ids):
            manifest_dir = root / artifact_id
            manifest_dir.mkdir(parents=True, exist_ok=True)
            cellwise_layers = []
            for layer_key, grids in values_by_layer.items():
                grid_path = manifest_dir / f"{layer_key}.asc"
                self._write_ascii_grid(grid_path, grids[index])
                cellwise_layers.append(
                    {
                        "key": layer_key,
                        "layer_name": layer_key,
                        "grid_path": str(grid_path),
                        "kind": "hazard_layer",
                        "format": "esri_ascii_grid",
                        "thresholds": [5.0] if "velocity" in layer_key else [],
                    }
                )
            manifest = {
                "schema_version": "run_manifest_v1",
                "case_id": artifact_id,
                "grid": {
                    "ncols": 3,
                    "nrows": 3,
                    "xllcorner": 100.0,
                    "yllcorner": 200.0,
                    "cellsize": 2.0,
                },
                "cellwise_layers": cellwise_layers,
                "layers": [
                    {
                        "key": layer_key,
                        "summary": {
                            "valid_cell_count": 9,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "sum": 1.0,
                            "nonzero_cell_count": 1,
                        },
                    }
                    for layer_key in values_by_layer
                ],
                "outputs": [
                    {
                        "kind": "hazard_layer",
                        "format": "esri_ascii_grid",
                        "layer_name": layer_key,
                        "path": str(manifest_dir / f"{layer_key}.asc"),
                        "total_bytes": 1,
                        "sha256": f"{artifact_id}-{layer_key}",
                    }
                    for layer_key in values_by_layer
                ],
            }
            manifest_path = manifest_dir / f"{artifact_id}.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            artifact_specs.append(manifest_path)
        return tuple(artifact_specs)

    def _write_ascii_grid(self, path: Path, grid: list[list[float | None]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "ncols 3",
            "nrows 3",
            "xllcorner 100",
            "yllcorner 200",
            "cellsize 2",
            "NODATA_value -9999",
        ]
        for row in grid:
            rendered = []
            for value in row:
                rendered.append("-9999" if value is None else str(value))
            lines.append(" ".join(rendered))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
