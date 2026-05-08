from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_pilot_scaling.py"
SPEC = importlib.util.spec_from_file_location("summarize_pilot_scaling", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary_script)


class PilotScalingSummaryTests(unittest.TestCase):
    def test_summarizes_manifest_runtime_outputs_and_reducer_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            validation_manifest = work / "validation_manifest.json"
            hazard_manifest = work / "hazard_manifest.json"
            gis_manifest = work / "gis_manifest.json"
            validation_manifest.write_text(json.dumps(self.validation_manifest()), encoding="utf-8")
            hazard_manifest.write_text(json.dumps(self.hazard_manifest()), encoding="utf-8")
            gis_manifest.write_text(json.dumps(self.gis_manifest()), encoding="utf-8")
            (work / "validation_time.txt").write_text(
                "elapsed_seconds=11.5\nmax_rss_kb=204800\n",
                encoding="utf-8",
            )

            summary = summary_script.build_summary(
                validation_manifest,
                hazard_manifest,
                gis_manifest,
                validation_time_file=work / "validation_time.txt",
            )

            self.assertEqual(summary["measurement_status"], "completed_local_manifest_measurement")
            self.assertEqual(summary["validation_stage"]["external_time"]["max_rss_kb"], 204800)
            self.assertEqual(summary["hazard_stage"]["outputs"]["total_row_count"], 1200)
            self.assertEqual(summary["hazard_stage"]["outputs"]["total_file_count"], 4)
            self.assertEqual(summary["hazard_stage"]["reducer_execution"]["chunk_count"], 2)
            self.assertEqual(
                summary["decision"]["primary_bottleneck"],
                "hazard_conditional_curve_output_volume",
            )
            self.assertEqual(summary["gis_package_stage"]["geotiff_count"], 1)

    def test_requires_ignored_outputs_unless_allow_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            with self.assertRaisesRegex(summary_script.ScalingSummaryError, "required ignored pilot output"):
                summary_script.build_summary(
                    work / "missing_validation.json",
                    work / "missing_hazard.json",
                    work / "missing_gis.json",
                )

            summary = summary_script.build_summary(
                work / "missing_validation.json",
                work / "missing_hazard.json",
                work / "missing_gis.json",
                allow_missing=True,
            )

            self.assertEqual(summary["measurement_status"], "blocked_missing_outputs")
            self.assertEqual(summary["decision"]["status"], "blocked")

    def test_rejects_missing_performance_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            validation_manifest = work / "validation_manifest.json"
            hazard_manifest = work / "hazard_manifest.json"
            validation = self.validation_manifest()
            validation.pop("performance")
            validation_manifest.write_text(json.dumps(validation), encoding="utf-8")
            hazard_manifest.write_text(json.dumps(self.hazard_manifest()), encoding="utf-8")

            with self.assertRaisesRegex(summary_script.ScalingSummaryError, "validation.performance"):
                summary_script.build_summary(validation_manifest, hazard_manifest, work / "missing_gis.json")

    def validation_manifest(self) -> dict:
        return {
            "schema_version": "run_manifest_v1",
            "case_id": "validation_tschamut_public_conditional_gate_v1",
            "terrain": {"epsg": 2056, "vertical_datum": "LN02", "cell_size_m": 2.0},
            "performance": {
                "total_wall_seconds": 10.0,
                "simulation_seconds": 6.0,
                "output_write_seconds": 2.0,
                "trajectory_count": 60,
                "impact_event_count": 900,
                "output_file_count": 10,
                "output_bytes": 5000,
            },
            "outputs": [
                {
                    "kind": "ensemble_trajectories",
                    "format": "csv_directory",
                    "path": "validation/trajectories",
                    "file_count": 2,
                    "row_count": 300,
                    "total_bytes": 3000,
                },
                {
                    "kind": "ensemble_impact_events",
                    "format": "csv_directory",
                    "path": "validation/impact_events",
                    "file_count": 2,
                    "row_count": 600,
                    "total_bytes": 2000,
                },
            ],
        }

    def hazard_manifest(self) -> dict:
        return {
            "schema_version": "run_manifest_v1",
            "case_id": "validation_tschamut_public_conditional_gate_v1",
            "performance": {
                "total_wall_seconds": 20.0,
                "accumulation_seconds": 4.0,
                "output_write_seconds": 12.0,
                "total_hazard_input_rows_read": 1200,
                "output_file_count": 4,
                "output_bytes": 25000,
            },
            "outputs": [
                {
                    "kind": "conditional_intensity_curve_table",
                    "format": "csv",
                    "path": "hazard/curves.csv",
                    "file_count": 1,
                    "row_count": 1000,
                    "total_bytes": 20000,
                },
                {
                    "kind": "geotiff_rasters",
                    "format": "geotiff",
                    "path": "hazard/rasters",
                    "file_count": 3,
                    "row_count": 200,
                    "total_bytes": 5000,
                },
            ],
            "reducer_execution": {
                "schema_version": "deterministic_local_reducer_v1",
                "mode": "chunked_local_threads",
                "worker_count": 2,
                "chunk_count": 2,
                "merge_order": "sorted_chunk_id",
                "merge_order_independent": True,
                "partial_state_storage": "in_memory",
                "full_trajectory_output_default": False,
            },
        }

    def gis_manifest(self) -> dict:
        return {
            "schema_version": "pilot_gis_package_manifest_v1",
            "operational_status": "research_diagnostic",
            "raster_outputs": [{"format": "geotiff"}],
            "parity_outputs": [{"format": "csv_grid"}, {"format": "esri_ascii_grid"}],
            "visual_qa": {"status": "not-run"},
        }


if __name__ == "__main__":
    unittest.main()
