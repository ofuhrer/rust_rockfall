#!/usr/bin/env python3
"""Tests for first-pass hazard-layer post-processing."""

from __future__ import annotations

import csv
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import scripts.build_hazard_layers as hazard
import scripts.prepare_tschamut_swissalti3d_pilot as tschamut_pilot


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hazard"
SWISS_PILOT = ROOT / "validation" / "data" / "processed" / "swisstopo_pilot"
PHASE1_SMOKE_CASE = ROOT / "validation" / "cases" / "probabilistic_phase1_smoke.yaml"
PHASE1_SMOKE_OUTPUTS = [
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_metrics.json",
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_manifest.json",
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectory.csv",
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectory_metadata.csv",
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_release_points.csv",
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_deposition.csv",
]
PHASE1_SMOKE_DIRS = [
    ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectories",
]

_CHUNK_STATE_EXECUTION_FIELDS = (
    "status",
    "completion_state",
    "row_count",
    "rows_written",
    "output_bytes",
    "execution_attempt",
    "merge_group_id",
    "retry_count",
    "failure_reason",
)


def matplotlib_available() -> bool:
    try:
        import matplotlib  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


class HazardLayerTests(unittest.TestCase):
    def assert_chunk_state_accumulator_only(self, state_path: Path) -> dict[str, Any]:
        state = json.loads(state_path.read_text())
        for field in _CHUNK_STATE_EXECUTION_FIELDS:
            self.assertNotIn(field, state)
        self.assertEqual(state.get("schema_version"), hazard.CHUNK_PARTIAL_STATE_SCHEMA_VERSION)
        self.assertEqual(state.get("execution_state_schema_version"), hazard.CHUNK_EXECUTION_MANIFEST_SCHEMA_VERSION)
        return state

    def _weighted_map_package_case(
        self,
        work: Path,
        map_product_id: str,
        metadata_path: Path | None = None,
    ) -> tuple[Path, Path, Path, Path]:
        metadata_rows = fixture_weight_rows()
        for index, row in enumerate(metadata_rows):
            row["source_zone_id"] = "zone_a"
            row["scenario_id"] = "scenario_a" if index == 0 else "scenario_b"
        metadata_path = metadata_path or (work / "weighted_metadata.csv")
        write_metadata_csv(metadata_path, metadata_rows)
        case_path = write_weighted_case(work / "weighted_case.yaml", metadata_path)
        source_zone_metadata_path = work / "source_zone_metadata.yaml"
        shutil.copy(
            str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "source_zone_valid.yaml"),
            source_zone_metadata_path,
        )
        scenario_table_path = work / "scenario_table.csv"
        shutil.copy(
            str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "scenario_level2_weighted.csv"),
            scenario_table_path,
        )
        map_package_manifest_json = work / f"{map_product_id}_map_package_manifest.json"
        return case_path, source_zone_metadata_path, scenario_table_path, map_package_manifest_json

    def _weighted_map_package_args(
        self,
        case_path: Path,
        source_zone_metadata_path: Path,
        scenario_table_path: Path,
        map_package_manifest_json: Path,
        output_dir: Path,
    ) -> list[str]:
        return [
            "--case",
            str(case_path),
            "--output-dir",
            str(output_dir),
            "--cell-size",
            "1.0",
            "--no-plots",
            "--reducer-workers",
            "2",
            "--map-product-id",
            "phase1_zone_a_weighted",
            "--probability-mode",
            "sampling_weighted_conditional",
            "--normalization-scope",
            "conditioned_on_filter",
            "--source-zone-metadata-path",
            str(source_zone_metadata_path),
            "--scenario-table-path",
            str(scenario_table_path),
            "--map-package-manifest-json",
            str(map_package_manifest_json),
            "--export-geotiff",
        ]

    def _pilot_gis_case(
        self,
        work: Path,
        *,
        output_dir: Path,
        manifest_path: Path | None = None,
    ) -> tuple[Path, Path]:
        case = yaml_load(FIXTURE / "ensemble_case.yaml")
        case["terrain"] = {
            "type": "ascii_dem_clamped",
            "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
            "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
        }
        package_manifest_json = output_dir / "hazard_fixture_ensemble_pilot_gis_package_manifest.json"
        case["pilot_gis_package"] = {
            "enabled": True,
            "visual_qa_status": "inconclusive",
            "visual_qa_note": "pilot-gis replay policy regression fixture",
            "package_manifest_json": str(
                manifest_path
                if manifest_path is not None
                else package_manifest_json
            ),
        }
        case_path = work / "pilot_gis_case.yaml"
        write_yaml(case_path, case)
        return case_path, package_manifest_json

    def assert_chunk_state_row_counts_align_with_manifest(self, state: dict[str, Any], manifest: dict[str, Any]) -> None:
        self.assertEqual(state.get("trajectory_count"), manifest.get("reducer_counts", {}).get("trajectory_count"))
        self.assertEqual(state.get("trajectory_sample_count"), manifest.get("input_rows", {}).get("trajectory_sample_rows"))
        self.assertEqual(state.get("deposition_point_count"), manifest.get("input_rows", {}).get("deposition_rows"))
        self.assertEqual(state.get("impact_event_count"), manifest.get("input_rows", {}).get("impact_event_rows"))
        self.assertEqual(
            state.get("significant_impact_count"),
            manifest.get("input_rows", {}).get("significant_impact_rows"),
        )

    def test_trajectory_csv_batch_reader_preserves_samples_and_id(self) -> None:
        warnings: list[str] = []
        batch = hazard.read_trajectory_sample_batch(FIXTURE / "trajectory_a.csv", warnings)

        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(batch.trajectory_id, "trajectory_a")
        self.assertEqual(len(batch.samples), 3)
        self.assertEqual(warnings, [])
        self.assertAlmostEqual(batch.samples[0].x_m or 0.0, 0.0)
        self.assertAlmostEqual(batch.samples[1].kinetic_j or 0.0, 10.0)
        self.assertAlmostEqual(batch.samples[2].speed_mps or 0.0, 0.5)

    def test_trajectory_csv_batch_reader_tolerates_missing_optional_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "minimal_trajectory.csv"
            path.write_text("time_s,x_m,y_m\n0.0,1.0,2.0\n")
            warnings: list[str] = []
            batch = hazard.read_trajectory_sample_batch(path, warnings)

        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(batch.trajectory_id, "minimal_trajectory")
        self.assertEqual(len(batch.samples), 1)
        self.assertAlmostEqual(batch.samples[0].x_m or 0.0, 1.0)
        self.assertAlmostEqual(batch.samples[0].y_m or 0.0, 2.0)
        self.assertIsNone(batch.samples[0].z_m)
        self.assertIsNone(batch.samples[0].kinetic_j)
        self.assertIsNone(batch.samples[0].speed_mps)
        self.assertEqual(warnings, [])

    def test_empty_trajectory_batch_preserves_legacy_counting_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty_trajectory.csv"
            path.write_text("time_s,x_m,y_m,z_m\n")
            warnings: list[str] = []
            batch = hazard.read_trajectory_sample_batch(path, warnings)

        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(batch.trajectory_id, None)
        self.assertEqual(batch.samples, ())
        self.assertEqual(warnings, [])

    def test_trajectory_csv_batch_reader_rejects_mixed_trajectory_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed_trajectory.csv"
            path.write_text(
                "trajectory_id,time_s,x_m,y_m,z_m\n"
                "trajectory_a,0.0,0.0,0.0,1.0\n"
                "trajectory_b,0.1,1.0,0.0,1.0\n"
            )
            warnings: list[str] = []

            with self.assertRaisesRegex(SystemExit, "multiple trajectory_id values"):
                hazard.read_trajectory_sample_batch(path, warnings)

    def test_hazard_layers_are_idempotent_and_do_not_mutate_counts(self) -> None:
        grid = hazard.GridSpec(xmin=0.0, ymin=0.0, ncols=1, nrows=1, cell_size=1.0)
        accumulator = hazard.HazardAccumulator(
            grid=grid,
            terrain=hazard.PlaneTerrain(z0=0.0, slope_x=0.0, slope_y=0.0),
            block_radius_m=0.0,
            statistics=hazard.HazardStatisticConfig(kinetic_energy_exceedance_j=(1.0,)),
        )
        for index in range(2):
            accumulator.accumulate_trajectory(
                hazard.TrajectorySampleBatch(
                    path=Path(f"trajectory_{index}.csv"),
                    trajectory_id=f"trajectory_{index}",
                    samples=(
                        hazard.TrajectorySample(
                            x_m=0.5,
                            y_m=0.5,
                            z_m=1.0,
                            kinetic_j=2.0,
                            speed_mps=1.0,
                        ),
                    ),
                )
            )

        first_layers, _ = accumulator.layers()
        second_layers, _ = accumulator.layers()

        def layer_value(layers: list[hazard.RasterLayer], key: str) -> float:
            return next(layer for layer in layers if layer.key == key).values[0][0]

        self.assertEqual(accumulator.reach[0][0], 2.0)
        self.assertEqual(accumulator.kinetic_exceedance[1.0][0][0], 2.0)
        self.assertEqual(layer_value(first_layers, "reach_probability"), 1.0)
        self.assertEqual(layer_value(second_layers, "reach_probability"), 1.0)
        self.assertEqual(layer_value(first_layers, "kinetic_energy_exceedance_1j"), 1.0)
        self.assertEqual(layer_value(second_layers, "kinetic_energy_exceedance_1j"), 1.0)

    def test_deposition_batch_reader_preserves_coordinates_and_properties(self) -> None:
        warnings: list[str] = []
        batch = hazard.read_deposition_batch(FIXTURE / "deposition.csv", warnings)

        self.assertEqual(len(batch.points), 2)
        self.assertAlmostEqual(batch.points[0].x_m or 0.0, 2.0)
        self.assertAlmostEqual(batch.points[0].y_m or 0.0, 0.0)
        self.assertIn("trajectory_id", batch.points[0].properties)
        self.assertNotIn("x_m", batch.points[0].properties)
        self.assertNotIn("y_m", batch.points[0].properties)
        self.assertEqual(warnings, [])

    def test_impact_csv_batch_reader_preserves_significant_event_semantics(self) -> None:
        warnings: list[str] = []
        batches = list(hazard.read_impact_event_csv_batches([FIXTURE / "impacts.csv"], warnings))

        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].event_count, 2)
        self.assertEqual(batches[0].significant_event_count, 1)
        self.assertEqual(
            batches[0].significant_points,
            (hazard.SignificantImpactPoint(x_m=2.0, y_m=0.0, trajectory_id=None),),
        )
        self.assertEqual(warnings, [])

    def test_projected_parquet_impact_batch_reader_preserves_counts(self) -> None:
        try:
            import pyarrow  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("pyarrow is required for Parquet impact-event fixtures")

        with tempfile.TemporaryDirectory() as tmp:
            parquet_path = Path(tmp) / "impact_events.parquet"
            write_impact_parquet_fixture(parquet_path, FIXTURE / "ensemble_impacts")
            warnings: list[str] = []
            batches = list(hazard.read_impact_event_parquet_batches([parquet_path], warnings))

        self.assertEqual(sum(batch.event_count for batch in batches), 2)
        self.assertEqual(sum(batch.significant_event_count for batch in batches), 2)
        self.assertEqual(
            [point for batch in batches for point in batch.significant_points],
            [
                hazard.SignificantImpactPoint(x_m=2.0, y_m=0.0, trajectory_id="trajectory_000000"),
                hazard.SignificantImpactPoint(x_m=3.0, y_m=1.0, trajectory_id="trajectory_000001"),
            ],
        )
        self.assertEqual(warnings, [])

    def test_python_terrain_sampler_matches_rust_case_parameter_names(self) -> None:
        paraboloid = hazard.TerrainSampler.from_case(
            {
                "terrain": {
                    "type": "paraboloid",
                    "parameters": {"z0_m": 2.0, "ax": 0.5, "ay": 0.25},
                }
            }
        )
        self.assertAlmostEqual(paraboloid.height(2.0, 4.0), 8.0)

        step = hazard.TerrainSampler.from_case(
            {
                "terrain": {
                    "type": "step",
                    "parameters": {"step_x_m": 10.0, "high_z_m": 5.0, "low_z_m": 1.0},
                }
            }
        )
        self.assertAlmostEqual(step.height(9.0, 0.0), 5.0)
        self.assertAlmostEqual(step.height(10.0, 0.0), 1.0)

    def test_fixture_layers_are_reproducible_and_interpretable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            status = hazard.main_with_args(
                [
                    "--case",
                    str(FIXTURE / "plane_case.yaml"),
                    "--diagnostics",
                    str(FIXTURE / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                ]
            )
            self.assertEqual(status, 0)

            metadata = json.loads((output_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertTrue(metadata["hazard_only"])
            self.assertFalse(metadata["risk_modeling_included"])
            self.assertEqual(metadata["inputs"]["trajectory_count"], 2)
            self.assertEqual(metadata["inputs"]["deposition_point_count"], 2)
            self.assertEqual(metadata["inputs"]["impact_event_count"], 2)
            self.assertEqual(manifest["schema_version"], "run_manifest_v1")
            self.assertEqual(manifest["completion_status"], "completed")
            self.assertEqual(manifest["execution_status"], "completed")
            self.assertEqual(manifest["scientific_status"], "not_evaluated")
            self.assertEqual(manifest["grid"]["source"], "auto")
            self.assertEqual(manifest["inputs"]["trajectory_sample_count"], 6)
            self.assertGreaterEqual(manifest["performance"]["total_wall_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["hazard_layer_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["output_write_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["accumulation_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["core_output_write_seconds"], 0.0)
            self.assertEqual(manifest["performance"]["plot_render_seconds"], 0.0)
            self.assertFalse(manifest["performance"]["plots_enabled"])
            self.assertGreaterEqual(manifest["performance"]["bounds_discovery_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["deposition_accumulation_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["trajectory_accumulation_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["impact_accumulation_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["normalization_seconds"], 0.0)
            self.assertEqual(manifest["performance"]["trajectory_count"], 2)
            self.assertEqual(manifest["performance"]["impact_event_count"], 2)
            self.assertEqual(manifest["performance"]["trajectory_sample_rows_read"], 6)
            self.assertEqual(manifest["performance"]["deposition_rows_read"], 2)
            self.assertEqual(manifest["performance"]["impact_event_rows_read"], 2)
            self.assertEqual(manifest["performance"]["total_hazard_input_rows_read"], 10)
            self.assertEqual(manifest["performance"]["trajectory_files_scanned"], 2)
            self.assertEqual(manifest["performance"]["deposition_files_scanned"], 1)
            self.assertEqual(manifest["performance"]["impact_csv_files_scanned"], 1)
            self.assertEqual(manifest["performance"]["impact_parquet_tables_scanned"], 0)
            self.assertEqual(manifest["performance"]["bounds_trajectory_files_scanned"], 2)
            self.assertEqual(manifest["performance"]["bounds_deposition_files_scanned"], 1)
            self.assertEqual(manifest["performance"]["bounds_impact_csv_files_scanned"], 1)
            self.assertEqual(manifest["performance"]["bounds_impact_parquet_tables_scanned"], 0)
            self.assertEqual(manifest["performance"]["bounds_input_rows_scanned"], 10)
            self.assertGreater(manifest["performance"]["hazard_input_rows_per_second"], 0.0)
            self.assertGreater(manifest["performance"]["output_file_count"], 0)
            self.assertIsInstance(manifest["performance"]["output_write_kind_seconds"], dict)
            self.assertIsInstance(manifest["performance"]["output_write_kind_bytes"], dict)
            self.assertIn("json", manifest["performance"]["output_write_kind_bytes"])
            self.assertGreaterEqual(manifest["performance"]["json_serialization_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["manifest_write_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["output_write_kind_seconds"].get("json", 0.0), 0.0)
            hazard_outputs = [output for output in manifest["outputs"] if output["kind"] == "hazard_layer"]
            self.assertTrue(hazard_outputs)
            self.assertRegex(hazard_outputs[0]["sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(any(output["kind"] == "hazard_report" for output in manifest["outputs"]))
            artifacts = {artifact["kind"]: artifact for artifact in manifest["input_artifacts"]}
            self.assertEqual(artifacts["trajectory_samples"]["file_count"], 2)
            self.assertRegex(artifacts["trajectory_samples"]["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(
                artifacts["trajectory_samples"]["path_hash_policy"],
                "sha256 over sorted member path, byte size, and file sha256",
            )
            self.assertFalse(artifacts["trajectory_samples"]["members_truncated"])
            self.assertEqual(len(artifacts["trajectory_samples"]["members"]), 2)
            self.assertTrue(
                all(
                    set(member) == {"path", "total_bytes", "sha256"}
                    for member in artifacts["trajectory_samples"]["members"]
                )
            )
            self.assertTrue(
                all(
                    len(member["sha256"]) == 64
                    for member in artifacts["trajectory_samples"]["members"]
                )
            )
            self.assertRegex(artifacts["diagnostics"]["sha256"], r"^[0-9a-f]{64}$")
            reach_summary = next(
                layer["summary"] for layer in metadata["layers"] if layer["key"] == "reach_probability"
            )
            self.assertEqual(reach_summary["nonzero_cell_count"], 4)
            self.assertAlmostEqual(reach_summary["maximum"], 1.0)

            reach = read_layer(output_dir / "hazard_fixture_plane_reach_probability.csv", "reach_probability")
            self.assertAlmostEqual(max(reach.values()), 1.0)
            self.assertIn(0.5, reach.values())

            deposition = read_layer(output_dir / "hazard_fixture_plane_deposition_density.csv", "deposition_density")
            self.assertAlmostEqual(sum(deposition.values()), 1.0)
            self.assertEqual(sorted(value for value in deposition.values() if value > 0.0), [0.5, 0.5])

            impacts = read_layer(
                output_dir / "hazard_fixture_plane_significant_impact_density.csv",
                "significant_impact_density",
            )
            self.assertAlmostEqual(sum(impacts.values()), 1.0)
            self.assertEqual(len([value for value in impacts.values() if value > 0.0]), 1)

            max_ke = read_layer(output_dir / "hazard_fixture_plane_max_kinetic_energy.csv", "max_kinetic_energy")
            self.assertAlmostEqual(max(max_ke.values()), 12.0)

            asc_header = (output_dir / "hazard_fixture_plane_reach_probability.asc").read_text().splitlines()[:6]
            self.assertEqual(asc_header[0], "ncols 5")
            self.assertEqual(asc_header[1], "nrows 3")

            self.assertFalse((output_dir / "index.html").exists())
            self.assertEqual(list(output_dir.glob("*.png")), [])

    def test_hazard_manifest_includes_terrain_metadata_sidecar_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml_load(FIXTURE / "plane_case.yaml")
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            }
            case_path = work / "terrain_metadata_case.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--diagnostics",
                    str(FIXTURE / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                ]
            )

            self.assertEqual(status, 0)
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            terrain = manifest["terrain"]
            self.assertEqual(terrain["metadata_path"], str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"))
            self.assertEqual(terrain["crs"], "CH1903+ / LV95")
            self.assertEqual(terrain["epsg"], 2056)
            self.assertEqual(terrain["vertical_datum"], "LN02")
            self.assertEqual(terrain["resolution_m"], 2.0)
            self.assertEqual(terrain["nodata"], -9999.0)
            self.assertEqual(terrain["source_dataset"], "swisstopo_swissalti3d")
            self.assertEqual(terrain["source_product"], "swissALTI3D")
            self.assertEqual(terrain["extent"]["xmin"], 2600000.0)
            self.assertEqual(manifest["warnings"], [])

    def test_default_grid_csv_export_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml_load(FIXTURE / "plane_case.yaml")
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            }
            case_path = work / "terrain_metadata_case.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertEqual(manifest["raster_exports"]["grid_csv_export"], "full")
            self.assertTrue(any(output["format"] == "csv_grid" for output in manifest["outputs"]))

    def test_grid_csv_export_none_omits_grid_csv_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml_load(FIXTURE / "plane_case.yaml")
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            }
            case["conditional_curve_export"] = {"mode": "summary-only"}
            case_path = work / "terrain_metadata_case.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                        "--export-geotiff",
                        "--grid-csv-export",
                        "none",
                    ]
                ),
                0,
            )

            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertEqual(manifest["raster_exports"]["grid_csv_export"], "none")
            self.assertFalse(any(output["format"] == "csv_grid" for output in manifest["outputs"]))
            self.assertTrue(any(output["format"] == "esri_ascii_grid" for output in manifest["outputs"]))
            self.assertTrue(any(output["format"] == "geotiff" for output in manifest["outputs"]))
            self.assertEqual(manifest["conditional_execution"]["raster_exports"]["grid_csv_export"], "none")
            self.assertFalse(manifest["conditional_execution"]["raster_exports"]["grid_csv_written"])
            self.assertFalse((output_dir / "hazard_fixture_plane_reach_probability.csv").exists())
            self.assertTrue((output_dir / "hazard_fixture_plane_reach_probability.asc").exists())
            self.assertTrue((output_dir / "hazard_fixture_plane_reach_probability.tif").exists())

    def test_geotiff_export_preserves_values_grid_and_crs_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml_load(FIXTURE / "plane_case.yaml")
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            }
            case_path = work / "terrain_metadata_case.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--diagnostics",
                    str(FIXTURE / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                    "--export-geotiff",
                ]
            )

            self.assertEqual(status, 0)
            csv_values = read_layer(output_dir / "hazard_fixture_plane_reach_probability.csv", "reach_probability")
            tif_path = output_dir / "hazard_fixture_plane_reach_probability.tif"
            tif_values, tags = read_geotiff_values(tif_path)
            self.assertEqual(tif_values, csv_values)
            self.assertEqual(tuple(tags[33550]), (1.0, 1.0, 0.0))
            self.assertEqual(tuple(tags[33922]), (0.0, 0.0, 0.0, -1.0, 2.0, 0.0))
            self.assertEqual(str(tags[42113]), "-9999.0")
            self.assertIn(2056, tuple(tags[34735]))

            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            geotiff_outputs = [output for output in manifest["outputs"] if output["format"] == "geotiff"]
            self.assertTrue(geotiff_outputs)
            reach_output = [output for output in geotiff_outputs if output["layer_name"] == "reach_probability"][0]
            self.assertEqual(reach_output["raster"]["epsg"], 2056)
            self.assertEqual(reach_output["raster"]["vertical_datum"], "LN02")
            self.assertEqual(reach_output["raster"]["affine_transform"], [1.0, 0.0, -1.0, 0.0, -1.0, 2.0])
            self.assertEqual(reach_output["raster"]["nodata"], -9999.0)
            self.assertFalse(reach_output["raster"]["cloud_optimized"])
            self.assertEqual(reach_output["raster"]["compression"], "none")
            self.assertFalse(reach_output["cloud_optimized"])
            self.assertFalse(reach_output["probability_semantics"]["annualized"])
            self.assertRegex(reach_output["sha256"], r"^[0-9a-f]{64}$")

    def test_pilot_gis_package_manifest_records_review_artifacts_and_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source_zone_path = ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "source_zone_valid.yaml"
            case = yaml_load(FIXTURE / "plane_case.yaml")
            case["terrain"] = {
                "type": "ascii_dem_clamped",
                "path": str(SWISS_PILOT / "swissalti3d_pilot_crop.asc"),
                "metadata_path": str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            }
            case["pilot_gis_package"] = {
                "enabled": True,
                "visual_qa_status": "inconclusive",
                "visual_qa_note": "Tiny fixture generated for package contract inspection.",
                "reviewed_artifacts": ["manifest", "GeoTIFF"],
                "source_zone_context_paths": [str(source_zone_path)],
            }
            case_path = work / "pilot_gis_package_case.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--diagnostics",
                    str(FIXTURE / "diagnostics.json"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                    "--export-geotiff",
                ]
            )

            self.assertEqual(status, 0)
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            package_path = output_dir / "hazard_fixture_plane_pilot_gis_package_manifest.json"
            package = json.loads(package_path.read_text())
            self.assertTrue(any(output["kind"] == "pilot_gis_package_manifest" for output in manifest["outputs"]))
            self.assertEqual(package["schema_version"], "pilot_gis_package_manifest_v1")
            self.assertEqual(package["operational_status"], "research_diagnostic")
            self.assertTrue(any(output["format"] == "geotiff" for output in package["raster_outputs"]))
            self.assertTrue(any(output["format"] == "csv_grid" for output in package["parity_outputs"]))
            self.assertTrue(any(output["format"] == "esri_ascii_grid" for output in package["parity_outputs"]))
            self.assertEqual(package["source_zone_context"][0]["path"], str(source_zone_path))
            self.assertEqual(package["terrain_metadata"]["path"], str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"))
            self.assertFalse(package["raster_contract"]["cloud_optimized"])
            self.assertFalse(package["raster_contract"]["qgis_project_included"])
            self.assertFalse(package["probability_claim_boundary"]["annualized"])
            self.assertIn("return_period", package["probability_claim_boundary"]["future_unsupported_product_labels"])
            self.assertEqual(package["visual_qa"]["status"], "inconclusive")
            self.assertFalse(package["visual_qa"]["accepted_for_operational_use"])

    def test_pilot_gis_package_requires_geotiff_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(SystemExit, "pilot_gis_package requires GeoTIFF export"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(Path(tmp) / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                        "--pilot-gis-package",
                    ]
                )

    def test_cog_export_is_explicitly_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(SystemExit, "COG export is not implemented"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(Path(tmp) / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                        "--export-cog",
                    ]
                )

    def test_plotted_mode_preserves_report_outputs_without_changing_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            no_plot_dir = Path(tmp) / "no_plots"
            plotted_dir = Path(tmp) / "plotted"
            base_args = [
                "--case",
                str(FIXTURE / "plane_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
            ]
            self.assertEqual(
                hazard.main_with_args([*base_args, "--output-dir", str(no_plot_dir), "--no-plots"]),
                0,
            )
            self.assertEqual(
                hazard.main_with_args([*base_args, "--output-dir", str(plotted_dir)]),
                0,
            )

            for layer in (
                "reach_probability",
                "deposition_density",
                "max_kinetic_energy",
                "max_jump_height",
                "significant_impact_density",
            ):
                self.assertEqual(
                    read_layer(no_plot_dir / f"hazard_fixture_plane_{layer}.csv", layer),
                    read_layer(plotted_dir / f"hazard_fixture_plane_{layer}.csv", layer),
                )

            html = (plotted_dir / "index.html").read_text()
            self.assertIn("not operational risk", html)
            self.assertIn("How to Read Hazard Layers", html)
            self.assertIn("Reach probability", html)
            png_files = list(plotted_dir.glob("*.png"))
            if matplotlib_available():
                self.assertGreater(len(png_files), 0)
            else:
                self.assertEqual(png_files, [])

            manifest = json.loads((plotted_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertTrue(manifest["performance"]["plots_enabled"])
            self.assertGreaterEqual(manifest["performance"]["plot_render_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["core_output_write_seconds"], 0.0)
            if matplotlib_available():
                self.assertIn("png", manifest["performance"]["output_write_kind_seconds"])
            self.assertIn("html", manifest["performance"]["output_write_kind_seconds"])
            self.assertTrue(any(output["kind"] == "hazard_report" for output in manifest["outputs"]))

    def test_exceedance_layers_are_additive_and_manifested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = Path(tmp) / "baseline"
            exceedance_dir = Path(tmp) / "exceedance"
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(baseline_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(exceedance_dir),
                        "--cell-size",
                        "1.0",
                        "--kinetic-energy-exceedance-j",
                        "10",
                        "--jump-height-exceedance-m",
                        "0.4",
                        "--velocity-exceedance-mps",
                        "1.5",
                        "--no-plots",
                    ]
                ),
                0,
            )

            baseline_reach = read_layer(
                baseline_dir / "hazard_fixture_plane_reach_probability.csv",
                "reach_probability",
            )
            exceedance_reach = read_layer(
                exceedance_dir / "hazard_fixture_plane_reach_probability.csv",
                "reach_probability",
            )
            self.assertEqual(baseline_reach, exceedance_reach)

            kinetic = read_layer(
                exceedance_dir / "hazard_fixture_plane_kinetic_energy_exceedance_10j.csv",
                "kinetic_energy_exceedance_10j",
            )
            self.assertAlmostEqual(max(kinetic.values()), 1.0)
            self.assertAlmostEqual(sum(value for value in kinetic.values() if value > 0.0), 1.0)

            jump = read_layer(
                exceedance_dir / "hazard_fixture_plane_jump_height_exceedance_0p4m.csv",
                "jump_height_exceedance_0p4m",
            )
            self.assertGreater(max(jump.values()), 0.0)

            velocity = read_layer(
                exceedance_dir / "hazard_fixture_plane_velocity_exceedance_1p5mps.csv",
                "velocity_exceedance_1p5mps",
            )
            self.assertAlmostEqual(max(velocity.values()), 0.5)

            metadata = json.loads((exceedance_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((exceedance_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertEqual(metadata["hazard_statistics"]["kinetic_energy_exceedance_j"], [10.0])
            curve_path = exceedance_dir / "hazard_fixture_plane_conditional_intensity_exceedance_curves.csv"
            with curve_path.open(newline="") as file:
                curve_rows = list(csv.DictReader(file))
            self.assertTrue(curve_rows)
            kinetic_curve_rows = [
                row for row in curve_rows if row["layer_name"] == "kinetic_energy_exceedance_10j"
            ]
            self.assertEqual({row["probability_mode"] for row in kinetic_curve_rows}, {"unweighted_diagnostic"})
            self.assertEqual({row["normalization_scope"] for row in kinetic_curve_rows}, {"supplied_trajectory_count"})
            self.assertEqual({row["annualized"] for row in curve_rows}, {"false"})
            self.assertAlmostEqual(float(kinetic_curve_rows[0]["denominator"]), 2.0)
            self.assertEqual(
                metadata["conditional_intensity_exceedance_curves"]["schema_version"],
                "conditional_intensity_exceedance_curves_v1",
            )
            self.assertEqual(
                metadata["conditional_intensity_exceedance_curves"]["row_count"],
                len(curve_rows),
            )
            self.assertTrue(
                any(output["kind"] == "conditional_intensity_exceedance_curves" for output in manifest["outputs"])
            )
            self.assertIn(
                "kinetic_energy_exceedance_10j",
                manifest["hazard_statistics"]["generated_layer_names"],
            )
            self.assertTrue(
                any(layer["key"] == "velocity_exceedance_1p5mps" for layer in manifest["layers"])
            )

    def test_probability_standard_error_layers_are_opt_in_and_binomial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--kinetic-energy-exceedance-j",
                        "10",
                        "--velocity-exceedance-mps",
                        "1.5",
                        "--probability-standard-error",
                        "--no-plots",
                    ]
                ),
                0,
            )

            reach = read_layer(output_dir / "hazard_fixture_plane_reach_probability.csv", "reach_probability")
            reach_se = read_layer(
                output_dir / "hazard_fixture_plane_reach_probability_standard_error.csv",
                "reach_probability_standard_error",
            )
            for cell, probability in reach.items():
                expected = (probability * (1.0 - probability) / 2.0) ** 0.5
                self.assertAlmostEqual(reach_se[cell], expected)
            self.assertIn(0.0, {round(value, 12) for value in reach_se.values()})

            velocity = read_layer(
                output_dir / "hazard_fixture_plane_velocity_exceedance_1p5mps.csv",
                "velocity_exceedance_1p5mps",
            )
            velocity_se = read_layer(
                output_dir / "hazard_fixture_plane_velocity_exceedance_1p5mps_standard_error.csv",
                "velocity_exceedance_1p5mps_standard_error",
            )
            for cell, probability in velocity.items():
                expected = (probability * (1.0 - probability) / 2.0) ** 0.5
                self.assertAlmostEqual(velocity_se[cell], expected)

            metadata = json.loads((output_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertTrue(metadata["hazard_statistics"]["probability_standard_error"])
            self.assertIn(
                "reach_probability_standard_error",
                manifest["hazard_statistics"]["generated_layer_names"],
            )
            semantics = [
                layer
                for layer in manifest["layer_semantics"]
                if layer["layer_name"] == "reach_probability_standard_error"
            ][0]
            self.assertEqual(semantics["numerator"], "estimated standard error of trajectory-level probability")
            self.assertEqual(semantics["denominator"], "supplied trajectory count")

    def test_conditional_curve_summary_only_suppresses_large_curve_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--diagnostics",
                        str(FIXTURE / "diagnostics.json"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--kinetic-energy-exceedance-j",
                        "10",
                        "--conditional-curve-export",
                        "summary-only",
                        "--no-plots",
                    ]
                ),
                0,
            )

            curve_path = output_dir / "hazard_fixture_plane_conditional_intensity_exceedance_curves.csv"
            self.assertFalse(curve_path.exists())
            metadata = json.loads((output_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            curves = metadata["conditional_intensity_exceedance_curves"]
            self.assertTrue(curves["enabled"])
            self.assertEqual(curves["mode"], "summary-only")
            self.assertFalse(curves["csv_table_written"])
            self.assertGreater(curves["row_count"], 0)
            self.assertFalse(
                any(output["kind"] == "conditional_intensity_exceedance_curves" for output in manifest["outputs"])
            )
            self.assertTrue(
                any(output["path"].endswith("_kinetic_energy_exceedance_10j.csv") for output in manifest["outputs"])
            )
            execution = manifest["conditional_execution"]
            self.assertEqual(execution["schema_version"], "conditional_hazard_execution_diagnostics_v1")
            self.assertIn("conditional_intensity_exceedance", execution["product_modes"])
            self.assertFalse(execution["annualized"])
            self.assertFalse(execution["physical_probability"])
            self.assertFalse(execution["risk_or_exposure"])
            self.assertEqual(execution["conditional_curve_export"]["mode"], "summary-only")
            self.assertFalse(execution["conditional_curve_export"]["csv_table_written"])
            self.assertTrue(execution["conditional_curve_export"]["table_suppressed_for_output_budget"])
            self.assertEqual(execution["conditional_curve_export"]["row_count"], curves["row_count"])
            self.assertEqual(execution["reducer"]["mode"], "serial")
            self.assertEqual(execution["reducer"]["merge_order"], "single_serial_accumulator")
            self.assertGreater(execution["grid_cell_count"], 0)
            self.assertEqual(
                execution["output_budget"]["output_file_count"],
                manifest["performance"]["output_file_count"],
            )
            self.assertTrue(execution["output_budget"]["summary_only_curve_export_required_for_scale_up"])
            self.assertTrue(execution["convergence_diagnostics"]["requires_trajectory_count_sensitivity_before_scale_up"])

    def test_sampling_weighted_layers_equal_unweighted_when_weights_are_uniform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "uniform_metadata.csv"
            rows = fixture_weight_rows()
            for row in rows:
                row["sampling_weight"] = "1.0"
            write_metadata_csv(metadata_path, rows)
            case_path = write_weighted_case(work / "uniform_case.yaml", metadata_path)
            output_dir = work / "hazard"

            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            for weighted_key, unweighted_key in (
                ("weighted_reach_probability", "reach_probability"),
                ("weighted_deposition_density", "deposition_density"),
                ("weighted_kinetic_energy_exceedance_10j", "kinetic_energy_exceedance_10j"),
                ("weighted_jump_height_exceedance_0p4m", "jump_height_exceedance_0p4m"),
                ("weighted_velocity_exceedance_1p5mps", "velocity_exceedance_1p5mps"),
            ):
                self.assertEqual(
                    read_layer(output_dir / f"hazard_fixture_weighted_{weighted_key}.csv", weighted_key),
                    read_layer(output_dir / f"hazard_fixture_weighted_{unweighted_key}.csv", unweighted_key),
                )

    def test_sampling_weighted_layers_use_nonuniform_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "weighted_case.yaml"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            unweighted = read_layer(
                output_dir / "hazard_fixture_weighted_reach_probability.csv",
                "reach_probability",
            )
            weighted = read_layer(
                output_dir / "hazard_fixture_weighted_weighted_reach_probability.csv",
                "weighted_reach_probability",
            )
            self.assertNotEqual(weighted, unweighted)
            nonzero_values = sorted({round(value, 8) for value in weighted.values() if value > 0.0})
            self.assertEqual(nonzero_values, [0.25, 0.75, 1.0])

            unweighted_deposition = read_layer(
                output_dir / "hazard_fixture_weighted_deposition_density.csv",
                "deposition_density",
            )
            weighted_deposition = read_layer(
                output_dir / "hazard_fixture_weighted_weighted_deposition_density.csv",
                "weighted_deposition_density",
            )
            self.assertNotEqual(weighted_deposition, unweighted_deposition)
            self.assertEqual(
                sorted(round(value, 8) for value in weighted_deposition.values() if value > 0.0),
                [0.25, 0.75],
            )

            weighted_velocity = read_layer(
                output_dir / "hazard_fixture_weighted_weighted_velocity_exceedance_1p5mps.csv",
                "weighted_velocity_exceedance_1p5mps",
            )
            self.assertAlmostEqual(max(weighted_velocity.values()), 0.75)

            metadata = json.loads((output_dir / "hazard_fixture_weighted_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_weighted_manifest.json").read_text())
            probability = manifest["hazard_probability"]
            self.assertEqual(probability["probability_model"], "sampling_weighted")
            self.assertEqual(probability["weight_column"], "sampling_weight")
            self.assertEqual(probability["normalization_convention"], "conditioned_on_filter")
            self.assertAlmostEqual(probability["total_input_weight"], 4.0)
            self.assertAlmostEqual(probability["total_filtered_weight"], 4.0)
            self.assertIn("weighted_reach_probability", probability["generated_weighted_layer_names"])
            self.assertIn("weighted_deposition_density", probability["generated_weighted_layer_names"])
            self.assertEqual(metadata["hazard_probability"], probability)
            curve_path = output_dir / "hazard_fixture_weighted_conditional_intensity_exceedance_curves.csv"
            with curve_path.open(newline="") as file:
                curve_rows = list(csv.DictReader(file))
            weighted_curve_rows = [
                row for row in curve_rows if row["layer_name"] == "weighted_velocity_exceedance_1p5mps"
            ]
            self.assertTrue(weighted_curve_rows)
            self.assertEqual(
                {row["probability_mode"] for row in weighted_curve_rows},
                {"sampling_weighted_conditional"},
            )
            self.assertEqual(
                {row["normalization_scope"] for row in weighted_curve_rows},
                {"conditioned_on_filter"},
            )
            self.assertAlmostEqual(float(weighted_curve_rows[0]["denominator"]), 4.0)

    def test_map_package_metadata_labels_weighted_outputs_without_changing_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "phase1_metadata.csv"
            rows = fixture_weight_rows()
            rows[0]["source_zone_id"] = "zone_a"
            rows[0]["scenario_id"] = "scenario_a"
            rows[1]["source_zone_id"] = "zone_a"
            rows[1]["scenario_id"] = "scenario_b"
            write_metadata_csv(metadata_path, rows)
            case_path = write_weighted_case(work / "weighted_case.yaml", metadata_path)
            baseline_dir = work / "baseline"
            labelled_dir = work / "labelled"
            package_path = work / "phase1_map_package.json"

            base_args = [
                "--case",
                str(case_path),
                "--cell-size",
                "1.0",
                "--no-plots",
            ]
            self.assertEqual(hazard.main_with_args([*base_args, "--output-dir", str(baseline_dir)]), 0)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *base_args,
                        "--output-dir",
                        str(labelled_dir),
                        "--map-product-id",
                        "phase1_zone_a_weighted",
                        "--probability-mode",
                        "sampling_weighted_conditional",
                        "--normalization-scope",
                        "conditioned_on_filter",
                        "--source-zone-metadata-path",
                        str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "source_zone_valid.yaml"),
                        "--scenario-table-path",
                        str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "scenario_level2_weighted.csv"),
                        "--map-package-manifest-json",
                        str(package_path),
                        "--export-geotiff",
                    ]
                ),
                0,
            )

            for layer in (
                "weighted_reach_probability",
                "weighted_kinetic_energy_exceedance_10j",
                "weighted_jump_height_exceedance_0p4m",
                "weighted_velocity_exceedance_1p5mps",
            ):
                self.assertEqual(
                    read_layer(baseline_dir / f"hazard_fixture_weighted_{layer}.csv", layer),
                    read_layer(labelled_dir / f"hazard_fixture_weighted_{layer}.csv", layer),
                )

            manifest = json.loads((labelled_dir / "hazard_fixture_weighted_manifest.json").read_text())
            package = json.loads(package_path.read_text())
            self.assertEqual(manifest["hazard_map_package"]["map_product_id"], "phase1_zone_a_weighted")
            self.assertEqual(manifest["hazard_map_package"]["probability_mode"], "sampling_weighted_conditional")
            self.assertEqual(manifest["hazard_map_package"]["normalization_scope"], "conditioned_on_filter")
            self.assertEqual(manifest["hazard_map_package"]["source_zone_id"], "zone_a")
            self.assertEqual(manifest["hazard_map_package"]["scenario_ids"], ["scenario_a", "scenario_b"])
            self.assertFalse(manifest["hazard_map_package"]["annual_frequency_fields_present"])
            self.assertAlmostEqual(manifest["hazard_map_package"]["total_filtered_weight"], 4.0)
            weighted_semantics = [
                layer for layer in manifest["layer_semantics"] if layer["layer_name"] == "weighted_reach_probability"
            ][0]
            self.assertTrue(weighted_semantics["weighted"])
            self.assertFalse(weighted_semantics["is_annualized"])
            self.assertEqual(weighted_semantics["units"], "dimensionless")
            self.assertIn("source_zone_id=zone_a", weighted_semantics["conditioned_on"])
            self.assertEqual(package["schema_version"], "map_package_manifest_v1")
            self.assertEqual(package["probability_mode"], "sampling_weighted_conditional")
            self.assertEqual(package["operational_status"], "research_diagnostic")
            self.assertEqual(package["hazard_manifest_paths"], [str(labelled_dir / "hazard_fixture_weighted_manifest.json")])
            self.assertTrue(package["layer_semantics"])
            self.assertTrue(all(not layer["is_annualized"] for layer in package["layer_semantics"]))
            self.assertTrue(any(output["kind"] == "map_package_manifest" for output in manifest["outputs"]))
            geotiff_outputs = [output for output in manifest["outputs"] if output["format"] == "geotiff"]
            self.assertTrue(any(output["layer_name"] == "weighted_reach_probability" for output in geotiff_outputs))
            self.assertTrue(package["raster_outputs"])
            self.assertTrue(any(output["layer_name"] == "weighted_reach_probability" for output in package["raster_outputs"]))
            self.assertTrue(all(not output["is_annualized"] for output in package["raster_outputs"]))

    def test_map_package_metadata_rejects_annual_frequency_and_source_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "phase1_metadata.csv"
            rows = fixture_weight_rows()
            for index, row in enumerate(rows):
                row["source_zone_id"] = "zone_a"
                row["scenario_id"] = f"scenario_{'a' if index == 0 else 'b'}"
            write_metadata_csv(metadata_path, rows)
            case_path = write_weighted_case(work / "weighted_case.yaml", metadata_path)
            common = [
                "--case",
                str(case_path),
                "--output-dir",
                str(work / "hazard"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--map-product-id",
                "phase1_zone_a_weighted",
                "--source-zone-metadata-path",
                str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "source_zone_valid.yaml"),
            ]

            with self.assertRaisesRegex(SystemExit, "Level 3"):
                hazard.main_with_args(
                    [
                        *common,
                        "--probability-mode",
                        "annual_frequency",
                        "--normalization-scope",
                        "annual_frequency_sum",
                        "--scenario-table-path",
                        str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "scenario_level2_weighted.csv"),
                    ]
                )

            with self.assertRaisesRegex(SystemExit, "source_zone_id"):
                hazard.main_with_args(
                    [
                        *common,
                        "--probability-mode",
                        "sampling_weighted_conditional",
                        "--normalization-scope",
                        "conditioned_on_filter",
                        "--scenario-table-path",
                        str(
                            ROOT
                            / "tests"
                            / "fixtures"
                            / "probabilistic_phase1"
                            / "scenario_source_zone_mismatch_invalid.csv"
                        ),
                    ]
                )

            rows[1]["source_zone_id"] = "zone_b"
            write_metadata_csv(metadata_path, rows)
            with self.assertRaisesRegex(SystemExit, "trajectory metadata source_zone_id"):
                hazard.main_with_args(
                    [
                        *common,
                        "--probability-mode",
                        "sampling_weighted_conditional",
                        "--normalization-scope",
                        "conditioned_on_filter",
                        "--scenario-table-path",
                        str(ROOT / "tests" / "fixtures" / "probabilistic_phase1" / "scenario_level2_weighted.csv"),
                    ]
                )

    def test_phase1_smoke_example_runs_validation_and_labelled_hazard_package(self) -> None:
        cleanup_phase1_smoke_outputs()
        self.addCleanup(cleanup_phase1_smoke_outputs)
        subprocess.run(
            ["cargo", "run", "--quiet", "--", "validate", "--case", str(PHASE1_SMOKE_CASE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        trajectory_metadata = ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectory_metadata.csv"
        self.assertTrue(trajectory_metadata.exists())
        first_metadata_row = read_first_metadata_row(trajectory_metadata)
        self.assertEqual(first_metadata_row["map_product_id"], "phase1_smoke_map")
        self.assertEqual(first_metadata_row["source_zone_id"], "swissalti3d_pilot_source_area")
        self.assertEqual(first_metadata_row["scenario_id"], "phase1_smoke_scenario")
        self.assertEqual(first_metadata_row["block_scenario_id"], "phase1_smoke_block")
        self.assertEqual(first_metadata_row["terrain_material_assumption_id"], "uniform_global_parameters")
        self.assertEqual(first_metadata_row["model_configuration_id"], "translational_v0")
        self.assertEqual(first_metadata_row["sampling_weight"], "1.0")
        self.assertEqual(first_metadata_row["probability_mode"], "sampling_weighted_conditional")
        self.assertEqual(first_metadata_row["normalization_scope"], "conditioned_on_scenario")
        self.assertEqual(first_metadata_row["annual_frequency_per_year"], "")

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            unlabelled_case = yaml_load(PHASE1_SMOKE_CASE)
            unlabelled_case.pop("hazard_map_package", None)
            unlabelled_case_path = work / "probabilistic_phase1_smoke_unlabelled.yaml"
            write_yaml(unlabelled_case_path, unlabelled_case)
            unweighted_case = yaml_load(PHASE1_SMOKE_CASE)
            unweighted_case.pop("hazard_map_package", None)
            unweighted_case.pop("hazard_probability", None)
            unweighted_case_path = work / "probabilistic_phase1_smoke_unweighted.yaml"
            write_yaml(unweighted_case_path, unweighted_case)
            unweighted_dir = work / "unweighted"
            unlabelled_dir = work / "unlabelled"
            labelled_dir = work / "labelled"
            package_path = work / "map_package_manifest.json"
            representative_trajectory = (
                ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectory.csv"
            )
            ensemble_trajectory_dir = (
                ROOT / "validation" / "results" / "probabilistic_phase1_smoke_trajectories"
            )

            common = [
                "--trajectory",
                str(representative_trajectory),
                "--ensemble-trajectories-dir",
                str(ensemble_trajectory_dir),
                "--cell-size",
                "2.0",
                "--no-plots",
            ]
            self.assertEqual(
                hazard.main_with_args(
                    ["--case", str(unweighted_case_path), "--output-dir", str(unweighted_dir), *common]
                ),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    ["--case", str(unlabelled_case_path), "--output-dir", str(unlabelled_dir), *common]
                ),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(PHASE1_SMOKE_CASE),
                        "--output-dir",
                        str(labelled_dir),
                        "--map-package-manifest-json",
                        str(package_path),
                        "--export-geotiff",
                        *common,
                    ]
                ),
                0,
            )

            for weighted_key, unweighted_key in (
                ("weighted_reach_probability", "reach_probability"),
                ("weighted_kinetic_energy_exceedance_5j", "kinetic_energy_exceedance_5j"),
                ("weighted_jump_height_exceedance_0p05m", "jump_height_exceedance_0p05m"),
                ("weighted_velocity_exceedance_1mps", "velocity_exceedance_1mps"),
            ):
                self.assertEqual(
                    read_layer(unlabelled_dir / f"probabilistic_phase1_smoke_{weighted_key}.csv", weighted_key),
                    read_layer(unweighted_dir / f"probabilistic_phase1_smoke_{unweighted_key}.csv", unweighted_key),
                )
                self.assertEqual(
                    read_layer(unlabelled_dir / f"probabilistic_phase1_smoke_{weighted_key}.csv", weighted_key),
                    read_layer(labelled_dir / f"probabilistic_phase1_smoke_{weighted_key}.csv", weighted_key),
                )
            weighted_deposition = read_layer(
                labelled_dir / "probabilistic_phase1_smoke_weighted_deposition_density.csv",
                "weighted_deposition_density",
            )
            self.assertAlmostEqual(sum(weighted_deposition.values()), 0.8)

            manifest = json.loads((labelled_dir / "probabilistic_phase1_smoke_manifest.json").read_text())
            package = json.loads(package_path.read_text())
            self.assertEqual(manifest["hazard_map_package"]["map_product_id"], "phase1_smoke_map")
            self.assertEqual(manifest["hazard_map_package"]["probability_mode"], "sampling_weighted_conditional")
            self.assertEqual(manifest["hazard_map_package"]["scenario_ids"], ["phase1_smoke_scenario"])
            self.assertFalse(manifest["hazard_map_package"]["annual_frequency_fields_present"])
            self.assertTrue(manifest["layer_semantics"])
            self.assertTrue(all(not layer["is_annualized"] for layer in manifest["layer_semantics"]))
            self.assertEqual(package["schema_version"], "map_package_manifest_v1")
            self.assertEqual(package["map_product_id"], "phase1_smoke_map")
            self.assertEqual(package["probability_mode"], "sampling_weighted_conditional")
            self.assertEqual(package["operational_status"], "research_diagnostic")
            self.assertTrue(all(not layer["is_annualized"] for layer in package["layer_semantics"]))
            self.assertTrue(package["raster_outputs"])
            self.assertTrue(all(not output["is_annualized"] for output in package["raster_outputs"]))
            smoke_tif = labelled_dir / "probabilistic_phase1_smoke_weighted_reach_probability.tif"
            tif_values, tags = read_geotiff_values(smoke_tif)
            self.assertEqual(
                tif_values,
                read_layer(
                    labelled_dir / "probabilistic_phase1_smoke_weighted_reach_probability.csv",
                    "weighted_reach_probability",
                )
            )
            self.assertEqual(tuple(tags[33550]), (2.0, 2.0, 0.0))

    def test_sampling_weighted_layers_reject_negative_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "negative_metadata.csv"
            rows = fixture_weight_rows()
            rows[1]["sampling_weight"] = "-0.5"
            write_metadata_csv(metadata_path, rows)
            case_path = write_weighted_case(work / "negative_case.yaml", metadata_path)

            with self.assertRaisesRegex(SystemExit, "non-negative"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(work / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                )

    def test_sampling_weighted_layers_require_metadata_for_all_trajectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "missing_metadata.csv"
            write_metadata_csv(metadata_path, fixture_weight_rows()[:1])
            case_path = write_weighted_case(work / "missing_case.yaml", metadata_path)

            with self.assertRaisesRegex(SystemExit, "missing from"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(work / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                )

    def test_sampling_weighted_deposition_requires_trajectory_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            deposition_path = work / "deposition_without_ids.csv"
            with deposition_path.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["x_m", "y_m", "z_m"])
                writer.writeheader()
                writer.writerow({"x_m": "2.0", "y_m": "0.0", "z_m": "0.5"})
            case = yaml_load(FIXTURE / "weighted_case.yaml")
            case["outputs"]["ensemble_deposition_csv"] = str(deposition_path)
            case_path = work / "weighted_missing_deposition_ids.yaml"
            write_yaml(case_path, case)

            with self.assertRaisesRegex(SystemExit, "requires trajectory_id in deposition CSV"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(work / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                )

    def test_sampling_weighted_significant_impact_density_uses_event_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            case = yaml_load(FIXTURE / "weighted_case.yaml")
            case["outputs"]["ensemble_impact_events_dir"] = str(FIXTURE / "ensemble_impacts")
            case_path = work / "weighted_impacts.yaml"
            write_yaml(case_path, case)
            output_dir = work / "hazard"

            status = hazard.main_with_args(
                [
                    "--case",
                    str(case_path),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                ]
            )
            self.assertEqual(status, 0)

            unweighted = read_layer(
                output_dir / "hazard_fixture_weighted_significant_impact_density.csv",
                "significant_impact_density",
            )
            weighted = read_layer(
                output_dir / "hazard_fixture_weighted_weighted_significant_impact_density.csv",
                "weighted_significant_impact_density",
            )
            self.assertNotEqual(weighted, unweighted)
            self.assertEqual(sorted(round(value, 8) for value in unweighted.values() if value > 0.0), [0.5, 0.5])
            self.assertEqual(sorted(round(value, 8) for value in weighted.values() if value > 0.0), [0.25, 0.75])

            manifest = json.loads((output_dir / "hazard_fixture_weighted_manifest.json").read_text())
            probability = manifest["hazard_probability"]
            self.assertIn("weighted_significant_impact_density", probability["generated_weighted_layer_names"])
            semantics = [
                layer
                for layer in manifest["layer_semantics"]
                if layer["layer_name"] == "weighted_significant_impact_density"
            ][0]
            self.assertEqual(semantics["denominator"], "filtered significant impact event sampling_weight sum")
            self.assertTrue(semantics["weighted"])

    def test_sampling_weighted_significant_impact_density_requires_trajectory_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            impact_path = work / "impacts_without_ids.csv"
            with impact_path.open("w", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["impact_index", "x_m", "y_m", "incoming_normal_speed_mps"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "impact_index": "0",
                        "x_m": "2.0",
                        "y_m": "0.0",
                        "incoming_normal_speed_mps": "0.2",
                    }
                )
            case = yaml_load(FIXTURE / "weighted_case.yaml")
            case["outputs"]["impact_events_csv"] = str(impact_path)
            case_path = work / "weighted_missing_impact_ids.yaml"
            write_yaml(case_path, case)

            with self.assertRaisesRegex(SystemExit, "requires trajectory_id in impact-event input"):
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(work / "hazard"),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                )

    def test_sampling_weighted_filters_apply_to_metadata_and_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            metadata_path = work / "filtered_metadata.csv"
            write_metadata_csv(metadata_path, fixture_weight_rows())
            case_path = write_weighted_case(
                work / "filtered_case.yaml",
                metadata_path,
                filters={
                    "source_zone_ids": ["zone_a"],
                    "scenario_ids": [],
                    "block_mass_kg_min": None,
                    "block_mass_kg_max": 15.0,
                },
            )
            output_dir = work / "hazard"

            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--trajectory",
                        str(FIXTURE / "ensemble_trajectories" / "trajectory_000000.csv"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            weighted = read_layer(
                output_dir / "hazard_fixture_weighted_weighted_reach_probability.csv",
                "weighted_reach_probability",
            )
            self.assertEqual(sorted({value for value in weighted.values() if value > 0.0}), [1.0])
            manifest = json.loads((output_dir / "hazard_fixture_weighted_manifest.json").read_text())
            self.assertAlmostEqual(manifest["hazard_probability"]["total_input_weight"], 4.0)
            self.assertAlmostEqual(manifest["hazard_probability"]["total_filtered_weight"], 1.0)

    def test_unweighted_mode_does_not_emit_weighted_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "plane_case.yaml"),
                        "--output-dir",
                        str(output_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )
            metadata = json.loads((output_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertIsNone(metadata["hazard_probability"])
            self.assertIsNone(manifest["hazard_probability"])
            self.assertIsNone(metadata["hazard_map_package"])
            self.assertIsNone(manifest["hazard_map_package"])
            self.assertFalse(list(output_dir.glob("*weighted*.csv")))

    def test_explicit_grid_mode_records_reference_grid_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            status = hazard.main_with_args(
                [
                    "--case",
                    str(FIXTURE / "plane_case.yaml"),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "99.0",
                    "--grid-xmin",
                    "-1.0",
                    "--grid-ymin",
                    "-1.0",
                    "--grid-ncols",
                    "6",
                    "--grid-nrows",
                    "4",
                    "--grid-cell-size",
                    "1.0",
                    "--no-plots",
                ]
            )
            self.assertEqual(status, 0)

            metadata = json.loads((output_dir / "hazard_fixture_plane_metadata.json").read_text())
            manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertEqual(metadata["grid"]["source"], "explicit")
            self.assertEqual(metadata["grid"]["ncols"], 6)
            self.assertEqual(metadata["grid"]["nrows"], 4)
            self.assertEqual(manifest["grid"]["source"], "explicit")
            self.assertEqual(manifest["performance"]["bounds_discovery_seconds"], 0.0)
            self.assertEqual(manifest["performance"]["bounds_input_rows_scanned"], 0)
            asc_header = (output_dir / "hazard_fixture_plane_reach_probability.asc").read_text().splitlines()[:6]
            self.assertEqual(asc_header[0], "ncols 6")
            self.assertEqual(asc_header[1], "nrows 4")

    def test_explicit_grid_can_match_auto_grid_when_extent_is_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            auto_dir = work / "auto"
            explicit_dir = work / "explicit"
            base_args = [
                "--case",
                str(FIXTURE / "plane_case.yaml"),
                "--cell-size",
                "1.0",
                "--no-plots",
            ]
            self.assertEqual(
                hazard.main_with_args([*base_args, "--output-dir", str(auto_dir)]),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *base_args,
                        "--output-dir",
                        str(explicit_dir),
                        "--grid-xmin",
                        "-1.0",
                        "--grid-ymin",
                        "-1.0",
                        "--grid-ncols",
                        "5",
                        "--grid-nrows",
                        "3",
                        "--grid-cell-size",
                        "1.0",
                    ]
                ),
                0,
            )

            for layer in (
                "reach_probability",
                "deposition_density",
                "max_kinetic_energy",
                "max_jump_height",
                "significant_impact_density",
            ):
                self.assertEqual(
                    read_layer(auto_dir / f"hazard_fixture_plane_{layer}.csv", layer),
                    read_layer(explicit_dir / f"hazard_fixture_plane_{layer}.csv", layer),
                )

    def test_tschamut_swissalti3d_pilot_preparation_uses_synthetic_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            generated = tschamut_pilot.prepare_pilot_cases(
                dem_path=SWISS_PILOT / "swissalti3d_pilot_crop.asc",
                terrain_metadata_path=SWISS_PILOT / "swissalti3d_pilot_metadata.yaml",
                release_zone_metadata_path=SWISS_PILOT / "release_zone_source_area.yaml",
                terrain_classes_metadata_path=SWISS_PILOT / "terrain_classes_metadata.yaml",
                case_dir=work / "cases",
                results_dir=work / "results",
                seed=1234,
                ensemble_size=2,
                force=False,
            )
            self.assertEqual(
                [path.name for path in generated],
                ["tschamut_swissalti3d_baseline.yaml", "tschamut_swissalti3d_rotational.yaml"],
            )

            baseline = yaml_load(generated[0])
            rotational = yaml_load(generated[1])
            self.assertEqual(baseline["parameters"]["contact_model"], "translational_v0")
            self.assertEqual(rotational["parameters"]["contact_model"], "sphere_rotational_v1")
            self.assertEqual(baseline["random"]["seed"], 1234)
            self.assertEqual(baseline["random"]["ensemble_size"], 2)
            self.assertEqual(
                baseline["terrain"]["metadata_path"],
                str(SWISS_PILOT / "swissalti3d_pilot_metadata.yaml"),
            )
            self.assertEqual(
                baseline["terrain_classes"]["metadata_path"],
                str(SWISS_PILOT / "terrain_classes_metadata.yaml"),
            )
            self.assertIn("hazard_layers", baseline)
            self.assertIn("ensemble_trajectories_dir", baseline["outputs"])

    def test_tschamut_swissalti3d_pilot_preparation_reports_missing_private_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                tschamut_pilot.PilotError,
                "missing private swissALTI3D-style DEM crop",
            ):
                tschamut_pilot.prepare_pilot_cases(
                    dem_path=Path(tmp) / "missing.asc",
                    terrain_metadata_path=SWISS_PILOT / "swissalti3d_pilot_metadata.yaml",
                    release_zone_metadata_path=SWISS_PILOT / "release_zone_source_area.yaml",
                    terrain_classes_metadata_path=None,
                    case_dir=Path(tmp) / "cases",
                    results_dir=Path(tmp) / "results",
                    seed=1234,
                    ensemble_size=1,
                    force=False,
                )

    def test_nonfinite_coordinate_rows_are_dropped_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            trajectory = work / "trajectory.csv"
            trajectory.write_text(
                "time_s,x_m,y_m,z_m,kinetic_j,contact_state\n"
                "0.0,nan,0.0,1.0,1.0,airborne\n"
                "1.0,1.0,0.0,1.0,2.0,airborne\n"
            )
            output_dir = work / "hazard"
            status = hazard.main_with_args(
                [
                    "--trajectory",
                    str(trajectory),
                    "--output-dir",
                    str(output_dir),
                    "--cell-size",
                    "1.0",
                    "--no-plots",
                    "--prefix",
                    "nonfinite",
                ]
            )
            self.assertEqual(status, 0)
            metadata = json.loads((output_dir / "nonfinite_metadata.json").read_text())
            self.assertIn("dropped 1 non-finite coordinate rows", "\n".join(metadata["warnings"]))

    def test_case_prefers_full_ensemble_trajectory_directory_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            full_dir = Path(tmp) / "full"
            representative_dir = Path(tmp) / "representative"
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "ensemble_case.yaml"),
                        "--output-dir",
                        str(full_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "ensemble_case.yaml"),
                        "--trajectory",
                        str(FIXTURE / "trajectory_a.csv"),
                        "--output-dir",
                        str(representative_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            full_metadata = json.loads((full_dir / "hazard_fixture_ensemble_metadata.json").read_text())
            representative_metadata = json.loads(
                (representative_dir / "hazard_fixture_ensemble_metadata.json").read_text()
            )
            self.assertEqual(full_metadata["inputs"]["trajectory_count"], 2)
            self.assertEqual(full_metadata["inputs"]["impact_event_count"], 2)
            self.assertEqual(representative_metadata["inputs"]["trajectory_count"], 1)

            full_reach = read_layer(full_dir / "hazard_fixture_ensemble_reach_probability.csv", "reach_probability")
            representative_reach = read_layer(
                representative_dir / "hazard_fixture_ensemble_reach_probability.csv",
                "reach_probability",
            )
            self.assertNotEqual(full_reach, representative_reach)
            self.assertIn(0.5, full_reach.values())
            full_ke = read_layer(full_dir / "hazard_fixture_ensemble_max_kinetic_energy.csv", "max_kinetic_energy")
            representative_ke = read_layer(
                representative_dir / "hazard_fixture_ensemble_max_kinetic_energy.csv",
                "max_kinetic_energy",
            )
            self.assertGreater(max(full_ke.values()), max(representative_ke.values()))
            full_impacts = read_layer(
                full_dir / "hazard_fixture_ensemble_significant_impact_density.csv",
                "significant_impact_density",
            )
            self.assertAlmostEqual(sum(full_impacts.values()), 1.0)
            self.assertEqual(len([value for value in full_impacts.values() if value > 0.0]), 2)

    def test_chunked_reducer_matches_serial_outputs_and_writes_chunk_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            serial_dir = work / "serial"
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--kinetic-energy-exceedance-j",
                "10",
            ]

            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(serial_dir)]), 0)
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *common_args,
                        "--output-dir",
                        str(chunked_dir),
                        "--reducer-workers",
                        "3",
                    ]
                ),
                0,
            )

            for layer in (
                "reach_probability",
                "kinetic_energy_exceedance_10j",
                "max_kinetic_energy",
                "max_jump_height",
                "deposition_density",
                "significant_impact_density",
            ):
                self.assertEqual(
                    read_layer(serial_dir / f"hazard_fixture_ensemble_{layer}.csv", layer),
                    read_layer(chunked_dir / f"hazard_fixture_ensemble_{layer}.csv", layer),
                )

            manifest = json.loads((chunked_dir / "hazard_fixture_ensemble_manifest.json").read_text())
            reducer = manifest["reducer_execution"]
            self.assertEqual(reducer["schema_version"], "deterministic_local_reducer_v1")
            self.assertEqual(reducer["worker_count"], 3)
            self.assertEqual(reducer["chunk_count"], 3)
            self.assertEqual(reducer["merge_order"], "sorted_chunk_id")
            self.assertTrue(reducer["merge_order_independent"])
            self.assertEqual(reducer["chunk_ids"], sorted(reducer["chunk_ids"]))
            self.assertEqual(reducer["retry_policy"], "deterministic_chunk_retry_count_by_manifest")
            self.assertTrue(any(output["kind"] == "reducer_chunk_manifest" for output in manifest["outputs"]))
            self.assertTrue(any(output["kind"] == "reducer_execution_plan" for output in manifest["outputs"]))
            chunk_manifests = sorted((chunked_dir / "chunks").glob("*_manifest.json"))
            self.assertEqual(len(chunk_manifests), 3)
            first_chunk = json.loads(chunk_manifests[0].read_text())
            self.assertEqual(first_chunk["schema_version"], "hazard_reducer_chunk_manifest_v1")
            self.assertEqual(first_chunk["completion_status"], "completed")
            self.assertEqual(first_chunk["execution_status"], "completed")
            self.assertEqual(first_chunk["status"], "completed")
            self.assertEqual(first_chunk["completion_state"], "completed")
            self.assertEqual(first_chunk["execution_state_schema_version"], "chunk_execution_manifest_v1")
            self.assertIsNotNone(first_chunk["row_count"])
            self.assertIsNotNone(first_chunk["rows_written"])
            self.assertIsNotNone(first_chunk["execution_attempt"])
            self.assertGreater(first_chunk["rows_written"], 0)
            self.assertGreater(first_chunk["output_bytes"], 0)
            self.assertIsNone(first_chunk["failure_reason"])
            self.assertIn("reach_counts", first_chunk["reducer_contract"])
            for chunk_path in chunk_manifests:
                chunk_record = json.loads(chunk_path.read_text())
                chunk_id = chunk_record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                chunk_state_path = chunked_dir / "chunks" / f"{chunk_id}_state.json"
                state = self.assert_chunk_state_accumulator_only(chunk_state_path)
                self.assert_chunk_state_row_counts_align_with_manifest(state, chunk_record)
            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            self.assertTrue(execution_plan_path.exists())
            execution_plan = json.loads(execution_plan_path.read_text())
            self.assertEqual(execution_plan["schema_version"], "execution_plan_v1")
            self.assertEqual(execution_plan["plan_status"], "completed")
            self.assertEqual(execution_plan["chunk_count"], 3)
            self.assertEqual(execution_plan["chunk_id_policy"], "stable_prefix_sorted_chunk_index")
            self.assertTrue(all(record["completion_status"] == "completed" for record in execution_plan["chunk_manifests"]))
            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            self.assertEqual(execution_index.get("schema_version"), "reducer_execution_index_v1")
            self.assertEqual(len(execution_index.get("chunk_records") or []), 3)
            for record in execution_index.get("chunk_records", []):
                self.assertEqual(record.get("status"), record.get("completion_status"))
                self.assertEqual(record.get("completion_state"), record.get("completion_status"))
                self.assertGreaterEqual(int(record.get("output_bytes") or 0), 0)
                self.assertGreaterEqual(int(record.get("execution_attempt") or 0), 1)
                self.assertIsNotNone(record.get("row_count"))
                self.assertIsNotNone(record.get("rows_written"))
            merge_state = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json").read_text())
            self.assertEqual(merge_state.get("schema_version"), "reducer_merge_state_v1")
            self.assertEqual(merge_state.get("status"), "ready")
            self.assertEqual(merge_state.get("completion_state"), "ready")
            self.assertEqual(len(merge_state.get("merge_index") or []), 3)
            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            chunk_ids = {record.get("chunk_id") for record in execution_index.get("chunk_records", [])}
            for record in merge_state.get("merge_index", []):
                self.assertIn(record.get("status"), {"completed", "failed", None})
                self.assertIn(record.get("completion_state"), {"completed", "failed", None})
                self.assertIn(record.get("chunk_id"), chunk_ids)

            execution = manifest["conditional_execution"]
            self.assertEqual(execution["reducer"]["mode"], "chunked_local_threads")
            self.assertEqual(execution["reducer"]["worker_count"], 3)
            self.assertEqual(execution["reducer"]["chunk_count"], 3)
            self.assertEqual(execution["reducer"]["chunk_manifest_count"], 3)
            self.assertEqual(execution["reducer"]["chunk_ids"], sorted(execution["reducer"]["chunk_ids"]))
            self.assertEqual(execution["reducer"]["merge_order"], "sorted_chunk_id")
            self.assertTrue(execution["reducer"]["merge_order_independent"])
            self.assertFalse(execution["annualized"])
            self.assertFalse(execution["physical_probability"])
            self.assertFalse(execution["risk_or_exposure"])
            self.assertEqual(
                execution["output_budget"]["output_file_count"],
                manifest["performance"]["output_file_count"],
            )
            self.assertEqual(
                execution["output_budget"]["output_bytes"],
                manifest["performance"]["output_bytes"],
            )
            self.assertTrue(execution["output_budget"]["generated_outputs_should_remain_ignored"])
            self.assertTrue(execution["convergence_diagnostics"]["requires_worker_count_reducer_parity_before_scale_up"])

            self.assertEqual(execution["reducer"]["chunk_ids"], sorted(execution["reducer"]["chunk_ids"]))

    def test_chunk_execution_plan_is_deterministic_between_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "3",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            first_state_snapshots = {
                path.name: json.loads(path.read_text())
                for path in sorted((chunked_dir / "chunks").glob("*_state.json"))
            }
            self.assertEqual(first_plan["schema_version"], "execution_plan_v1")
            self.assertEqual(first_plan["plan_status"], "completed")
            self.assertIn("__execution_plan__", first_plan["plan_id"])
            self.assertEqual(
                first_plan["chunk_id_policy"],
                "stable_prefix_sorted_chunk_index",
            )

            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            second_plan = json.loads(execution_plan_path.read_text())
            second_state_snapshots = {
                path.name: json.loads(path.read_text())
                for path in sorted((chunked_dir / "chunks").glob("*_state.json"))
            }
            self.assertEqual(second_plan["schema_version"], "execution_plan_v1")
            self.assertEqual(second_plan["plan_status"], "completed")
            self.assertEqual(first_plan["plan_id"], second_plan["plan_id"])
            self.assertEqual(first_state_snapshots, second_state_snapshots)

    def test_chunk_execution_plan_records_failed_chunks(self) -> None:
        original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

        def fail_first_trajectory(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch | None:
            if path.name == "trajectory_000000.csv":
                raise RuntimeError("simulated chunk execution failure")
            return original_read_trajectory_sample_batch(path, warnings)

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "3",
            ]
            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_first_trajectory):
                with self.assertRaises(SystemExit):
                    hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)])

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            failed_plan = json.loads(execution_plan_path.read_text())
            self.assertEqual(failed_plan["schema_version"], "execution_plan_v1")
            self.assertEqual(failed_plan["plan_status"], "failed")
            failed_chunks = [record for record in failed_plan.get("chunk_manifests", []) if record.get("completion_status") == "failed"]
            completed_chunks = [
                record
                for record in failed_plan.get("chunk_manifests", [])
                if record.get("completion_status") == "completed"
            ]
            self.assertEqual(len(failed_chunks), 1)
            self.assertEqual(len(completed_chunks), len(failed_plan.get("chunk_manifests", [])) - 1)
            self.assertIn("simulated chunk execution failure", failed_chunks[0].get("completion_reason") or "")
            self.assertEqual(failed_chunks[0].get("retry_count"), 1)
            self.assertEqual(failed_chunks[0].get("status"), "failed")
            self.assertEqual(failed_chunks[0].get("completion_state"), "failed")
            self.assertEqual(failed_chunks[0].get("failure_reason"), failed_chunks[0].get("completion_reason"))
            self.assertEqual(failed_chunks[0].get("output_bytes"), 0)
            failed_chunk_id = failed_chunks[0].get("chunk_id")
            completed_chunk_id = completed_chunks[0].get("chunk_id")
            self.assertIsNotNone(failed_chunk_id)
            self.assertIsNotNone(completed_chunk_id)
            self.assertFalse((chunked_dir / "chunks" / f'{failed_chunk_id}_state.json').exists())
            completed_chunk_state_path = chunked_dir / "chunks" / f'{completed_chunk_id}_state.json'
            completed_state = self.assert_chunk_state_accumulator_only(completed_chunk_state_path)
            self.assert_chunk_state_row_counts_align_with_manifest(completed_state, completed_chunks[0])
            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            self.assertEqual(execution_index.get("schema_version"), "reducer_execution_index_v1")
            failed_index_records = [
                record for record in execution_index.get("chunk_records", []) if record.get("completion_status") == "failed"
            ]
            self.assertEqual(len(failed_index_records), 1)
            self.assertEqual(failed_index_records[0].get("status"), "failed")
            self.assertEqual(failed_index_records[0].get("completion_state"), "failed")
            self.assertEqual(failed_index_records[0].get("failure_reason"), failed_index_records[0].get("completion_reason"))

    def test_chunked_reducer_retries_failed_chunks_on_restart(self) -> None:
        original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

        def fail_first_trajectory_once(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch | None:
            if path.name == "trajectory_000000.csv":
                raise RuntimeError("simulated transient chunk failure")
            return original_read_trajectory_sample_batch(path, warnings)

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
                "--chunk-owner-id",
                "recovery_owner",
            ]
            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_first_trajectory_once):
                with self.assertRaises(SystemExit):
                    hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)])

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            failed_plan = json.loads(execution_plan_path.read_text())
            failed_chunks = [
                record for record in failed_plan.get("chunk_manifests", []) if record.get("completion_status") == "failed"
            ]
            self.assertEqual(len(failed_chunks), 1)
            failed_chunk_id = failed_chunks[0].get("chunk_id")
            self.assertEqual(failed_chunks[0].get("attempt_count"), 1)
            self.assertEqual(failed_chunks[0].get("execution_attempt"), 1)
            self.assertEqual(failed_chunks[0].get("retry_count"), 1)
            self.assertIn("simulated transient chunk failure", failed_chunks[0].get("completion_reason") or "")
            self.assertFalse((chunked_dir / "chunks" / f'{failed_chunk_id}_state.json').exists())

            self.assertEqual(
                hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]),
                0,
            )
            recovered_plan = json.loads(execution_plan_path.read_text())
            self.assertEqual(recovered_plan.get("plan_status"), "completed")
            recovered_failed = [record for record in recovered_plan.get("chunk_manifests", []) if record.get("chunk_id") == failed_chunk_id]
            self.assertEqual(len(recovered_failed), 1)
            self.assertEqual(recovered_failed[0].get("completion_status"), "completed")
            self.assertEqual(recovered_failed[0].get("status"), "completed")
            self.assertEqual(recovered_failed[0].get("completion_state"), "completed")
            self.assertEqual(recovered_failed[0].get("attempt_count"), 2)
            self.assertEqual(recovered_failed[0].get("retry_count"), 1)
            recovered_execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            recovered_record = [
                record
                for record in recovered_execution_index.get("chunk_records", [])
                if record.get("chunk_id") == failed_chunk_id
            ]
            self.assertEqual(len(recovered_record), 1)
            self.assertEqual(recovered_record[0].get("execution_attempt"), 2)
            self.assertEqual(recovered_record[0].get("completion_state"), "completed")
            self.assertIsNone(recovered_record[0].get("failure_reason"))
            self.assertGreater(int(recovered_record[0].get("row_count") or 0), 0)
            recovered_state_path = chunked_dir / "chunks" / f'{failed_chunk_id}_state.json'
            recovered_state = self.assert_chunk_state_accumulator_only(recovered_state_path)
            self.assert_chunk_state_row_counts_align_with_manifest(
                recovered_state,
                [
                    record
                    for record in recovered_plan.get("chunk_manifests", [])
                    if record.get("chunk_id") == failed_chunk_id
                ][0],
            )
            self.assertGreaterEqual(recovered_state["trajectory_count"], 0)

    def test_chunk_execution_attempt_is_one_on_fresh_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)

            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            for record in execution_index.get("chunk_records", []):
                self.assertEqual(record.get("attempt_count"), 1)
                self.assertEqual(record.get("execution_attempt"), 1)

    def test_chunk_execution_attempt_is_cumulative_on_retained_state_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            first_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            first_attempts = {
                record.get("chunk_id"): int(record.get("execution_attempt") or 0)
                for record in first_index.get("chunk_records", [])
            }
            self.assertTrue(first_attempts)

            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            for record in second_index.get("chunk_records", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                self.assertEqual(record.get("attempt_count"), first_attempts[chunk_id])
                self.assertEqual(record.get("execution_attempt"), first_attempts[chunk_id])

            second_plan = json.loads(execution_plan_path.read_text())
            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                manifest_path = record.get("manifest_path")
                self.assertIsNotNone(manifest_path)
                manifest = json.loads((chunked_dir / manifest_path).read_text()) if isinstance(manifest_path, str) else {}
                if manifest:
                    self.assertEqual(manifest.get("attempt_count"), first_attempts[chunk_id])
                    self.assertEqual(manifest.get("execution_attempt"), first_attempts[chunk_id])
                    self.assertEqual(manifest.get("orchestration_decision"), "reused_completed_state")

            first_decisions = {
                record.get("chunk_id"): record.get("orchestration_decision")
                for record in first_plan.get("chunk_manifests", [])
            }
            second_decisions = {
                record.get("chunk_id"): record.get("orchestration_decision")
                for record in second_plan.get("chunk_manifests", [])
            }
            for chunk_id, first_decision in first_decisions.items():
                self.assertIn(chunk_id, second_decisions)
                self.assertEqual(first_decision, "executed")
                self.assertEqual(second_decisions[chunk_id], "reused_completed_state")
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            for record in second_index.get("chunk_records", []):
                self.assertEqual(record.get("orchestration_decision"), "reused_completed_state")
                self.assertGreaterEqual(int(record.get("execution_attempt") or 0), 1)

    def test_chunked_reducer_recovers_stale_claim_before_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            completed_records = [
                record for record in first_plan.get("chunk_manifests", []) if record.get("completion_status") == "completed"
            ]
            self.assertTrue(completed_records)
            target_record = completed_records[0]
            target_chunk_id = target_record.get("chunk_id")
            self.assertIsNotNone(target_chunk_id)
            target_record["ownership"] = {
                "state": "claimed",
                "owner_id": "stale_recovery_owner",
                "claimed_at_unix_s": 1,
                "lease_expires_unix_s": 1,
                "released_at_unix_s": None,
                "release_reason": None,
                "updated_unix_s": 1,
            }
            target_record["execution_status"] = "not_started"
            execution_plan_path.write_text(json.dumps(first_plan, indent=2, sort_keys=True) + "\n")

            self.assertEqual(
                hazard.main_with_args(
                    [
                        *common_args,
                        "--chunk-owner-id",
                        "recovery_engine",
                        "--output-dir",
                        str(chunked_dir),
                    ]
                ),
                0,
            )
            second_plan = json.loads(execution_plan_path.read_text())
            second_records = {
                record.get("chunk_id"): record for record in second_plan.get("chunk_manifests", [])
            }
            self.assertIn(target_chunk_id, second_records)
            second_record = second_records[target_chunk_id]
            self.assertEqual(second_record.get("orchestration_decision"), "stale_claim_recovered")
            self.assertEqual(second_record.get("completion_status"), "completed")
            manifest_path = chunked_dir / "chunks" / f"{target_chunk_id}_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest.get("orchestration_decision"), "stale_claim_recovered")
            self.assertEqual(manifest.get("completion_status"), "completed")
            self.assertGreater(int(second_record.get("attempt_count") or 0), 0)

    def test_chunked_reducer_stale_claim_with_missing_partial_state_forces_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            target_record = next(
                record
                for record in first_plan.get("chunk_manifests", [])
                if record.get("completion_status") == "completed"
            )
            target_chunk_id = target_record.get("chunk_id")
            self.assertIsNotNone(target_chunk_id)
            target_record["ownership"] = {
                "state": "claimed",
                "owner_id": "stale_owner",
                "claimed_at_unix_s": 1,
                "lease_expires_unix_s": 1,
                "released_at_unix_s": None,
                "release_reason": None,
                "updated_unix_s": 1,
            }
            target_record["completion_status"] = "completed"
            target_record["execution_status"] = "not_started"
            state_path = Path(str(target_record.get("partial_state_path")))
            if state_path.exists():
                state_path.unlink()

            execution_plan_path.write_text(json.dumps(first_plan, indent=2, sort_keys=True) + "\n")
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *common_args,
                        "--chunk-owner-id",
                        "rerun_owner",
                        "--output-dir",
                        str(chunked_dir),
                    ]
                ),
                0,
            )

            second_plan = json.loads(execution_plan_path.read_text())
            target = next(
                record
                for record in second_plan.get("chunk_manifests", [])
                if record.get("chunk_id") == target_chunk_id
            )
            self.assertEqual(target.get("orchestration_decision"), "executed")
            self.assertEqual(target.get("completion_status"), "completed")

    def test_chunked_reducer_stale_claim_with_schema_mismatch_forces_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            target_record = next(
                record
                for record in first_plan.get("chunk_manifests", [])
                if record.get("completion_status") == "completed"
            )
            target_chunk_id = target_record.get("chunk_id")
            self.assertIsNotNone(target_chunk_id)
            state_path = Path(str(target_record.get("partial_state_path")))
            state = json.loads(state_path.read_text())
            state["schema_version"] = "legacy_reducer_chunk_state_v0"
            state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
            target_record["ownership"] = {
                "state": "claimed",
                "owner_id": "stale_owner",
                "claimed_at_unix_s": 1,
                "lease_expires_unix_s": 1,
                "released_at_unix_s": None,
                "release_reason": None,
                "updated_unix_s": 1,
            }
            target_record["completion_status"] = "completed"
            target_record["execution_status"] = "not_started"

            execution_plan_path.write_text(json.dumps(first_plan, indent=2, sort_keys=True) + "\n")
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *common_args,
                        "--chunk-owner-id",
                        "rerun_owner",
                        "--output-dir",
                        str(chunked_dir),
                    ]
                ),
                0,
            )
            second_plan = json.loads(execution_plan_path.read_text())
            target = next(
                record
                for record in second_plan.get("chunk_manifests", [])
                if record.get("chunk_id") == target_chunk_id
            )
            self.assertEqual(target.get("orchestration_decision"), "executed")
            self.assertEqual(target.get("completion_status"), "completed")

    def test_chunked_reducer_reuse_blocked_when_output_policy_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            execution_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): {
                    "execution_signature": record.get("execution_signature"),
                    "input_signature": record.get("input_signature"),
                }
                for record in execution_plan.get("chunk_manifests", [])
            }

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            self.assertEqual(
                hazard.main_with_args(
                    [
                        *common_args,
                        "--grid-csv-export",
                        "none",
                        "--output-dir",
                        str(chunked_dir),
                    ]
                ),
                0,
            )
            second_plan = json.loads(execution_plan_path.read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            second_merge_path = chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json"
            second_merge = json.loads(second_merge_path.read_text()) if second_merge_path.exists() else None
            second_merge_index = {
                record.get("chunk_id"): record
                for record in (second_merge.get("merge_index", []) if second_merge is not None else ())
                if isinstance(record.get("chunk_id"), str)
            }
            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                self.assertEqual(record.get("input_signature"), first_signatures[chunk_id]["input_signature"])
                self.assertNotEqual(record.get("execution_signature"), first_signatures[chunk_id]["execution_signature"])
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertIn(
                    record.get("orchestration_decision"),
                    {"executed", "completed_state_reset_for_rerun"},
                )
                merge_record = second_merge_index.get(chunk_id)
                if merge_record is not None:
                    self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                    self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))
            for record in second_index.get("chunk_records", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                first_signatures_record = first_signatures[chunk_id]
                self.assertEqual(record.get("input_signature"), first_signatures_record["input_signature"])
                self.assertNotEqual(record.get("execution_signature"), first_signatures_record["execution_signature"])
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertIn(
                    record.get("orchestration_decision"),
                    {"executed", "completed_state_reset_for_rerun"},
                )
                self.assertIsNotNone(record.get("execution_signature"))
                merge_record = second_merge_index.get(chunk_id)
                if merge_record is not None:
                    self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                    self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))

    def test_chunked_reducer_replay_fingerprint_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            output_dir = chunked_dir
            case_path, source_zone_metadata_path, scenario_table_path, package_manifest_json = self._weighted_map_package_case(
                work,
                map_product_id="phase1_zone_a_weighted",
            )
            common_args = self._weighted_map_package_args(
                case_path,
                source_zone_metadata_path,
                scenario_table_path,
                package_manifest_json,
                output_dir,
            )
            self.assertEqual(hazard.main_with_args(common_args), 0)
            execution_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): {
                    "execution_signature": record.get("execution_signature"),
                    "input_signature": record.get("input_signature"),
                }
                for record in execution_plan.get("chunk_manifests", [])
            }
            self.assertTrue(first_signatures)
            for chunk_id, signatures in first_signatures.items():
                self.assertIsNotNone(chunk_id)
                self.assertIsNotNone(signatures["execution_signature"])
                self.assertIsNotNone(signatures["input_signature"])

            read_calls: list[Path] = []
            original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

            def fail_on_trajectory_read(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch:
                read_calls.append(path)
                return original_read_trajectory_sample_batch(path, warnings)

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_on_trajectory_read):
                self.assertEqual(hazard.main_with_args(common_args), 0)
            self.assertEqual(read_calls, [])

            # no-ops without changing metadata/replay-relevant inputs
            second_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_execution_index_v1.json").read_text())
            merge_state = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_merge_state_v1.json").read_text())
            second_merge_index = {
                record.get("chunk_id"): record
                for record in merge_state.get("merge_index", [])
                if isinstance(record.get("chunk_id"), str)
            }
            second_index_by_chunk = {
                record.get("chunk_id"): record
                for record in second_index.get("chunk_records", [])
            }

            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                first_signature = first_signatures.get(chunk_id)
                self.assertIsNotNone(first_signature)
                self.assertEqual(record.get("execution_signature"), first_signature["execution_signature"])
                self.assertEqual(record.get("input_signature"), first_signature["input_signature"])
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                merge_record = second_merge_index.get(chunk_id)
                index_record = second_index_by_chunk.get(chunk_id)
                self.assertIsNotNone(index_record)
                self.assertIsNotNone(merge_record)
                self.assertEqual(index_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(index_record.get("input_signature"), record.get("input_signature"))
                self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))
                self.assertNotEqual(index_record.get("orchestration_decision"), "executed")
                self.assertNotEqual(merge_record.get("orchestration_decision"), "executed")
                self.assertEqual(manifest.get("orchestration_decision"), index_record.get("orchestration_decision"))

    def test_chunked_reducer_pilot_gis_manifest_rewrite_does_not_forfeit_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            output_dir = chunked_dir
            case_path, pilot_gis_manifest_path = self._pilot_gis_case(work=work, output_dir=output_dir)
            common_args = [
                "--case",
                str(case_path),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--output-dir",
                str(output_dir),
                "--cell-size",
                "10.0",
                "--no-plots",
                "--reducer-workers",
                "2",
                "--export-geotiff",
            ]

            self.assertEqual(hazard.main_with_args(common_args), 0)
            first_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): {
                    "execution_signature": record.get("execution_signature"),
                    "input_signature": record.get("input_signature"),
                }
                for record in first_plan.get("chunk_manifests", [])
            }
            self.assertTrue(first_signatures)

            pilot_package = json.loads(pilot_gis_manifest_path.read_text())
            pilot_package["visual_qa"]["note"] = "non-semantic replay policy regression edit"
            pilot_package["pilot_gis_replay_probe"] = "manifest_rewrite_without_reexecution"
            pilot_gis_manifest_path.write_text(json.dumps(pilot_package, indent=2, sort_keys=True) + "\n")

            read_calls: list[Path] = []
            original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

            def fail_if_rerun(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch:
                read_calls.append(path)
                return original_read_trajectory_sample_batch(path, warnings)

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_if_rerun):
                self.assertEqual(hazard.main_with_args(common_args), 0)
            self.assertEqual(read_calls, [])

            second_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            second_merge = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json").read_text())
            second_merge_index = {
                record.get("chunk_id"): record
                for record in second_merge.get("merge_index", [])
                if isinstance(record.get("chunk_id"), str)
            }
            second_index_by_chunk = {
                record.get("chunk_id"): record
                for record in second_index.get("chunk_records", [])
            }
            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                first_signature = first_signatures.get(chunk_id)
                self.assertIsNotNone(first_signature)
                self.assertEqual(record.get("execution_signature"), first_signature["execution_signature"])
                self.assertEqual(record.get("input_signature"), first_signature["input_signature"])
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertNotEqual(record.get("orchestration_decision"), "executed")
                index_record = second_index_by_chunk.get(chunk_id)
                if index_record is not None:
                    self.assertEqual(index_record.get("execution_signature"), first_signature["execution_signature"])
                    self.assertEqual(index_record.get("orchestration_decision"), record.get("orchestration_decision"))
                merge_record = second_merge_index.get(chunk_id)
                if merge_record is not None:
                    self.assertEqual(merge_record.get("execution_signature"), first_signature["execution_signature"])
                    self.assertEqual(merge_record.get("orchestration_decision"), record.get("orchestration_decision"))

    def test_chunked_reducer_source_filter_change_forces_reexecution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            output_dir = chunked_dir
            case_path, source_zone_metadata_path, scenario_table_path, package_manifest_json = self._weighted_map_package_case(
                work,
                map_product_id="phase1_zone_a_weighted",
            )
            common_args = self._weighted_map_package_args(
                case_path,
                source_zone_metadata_path,
                scenario_table_path,
                package_manifest_json,
                output_dir,
            )
            case = yaml_load(case_path)
            metadata_rows = []
            metadata_path = Path(case["hazard_probability"]["metadata_path"])
            with metadata_path.open(newline="") as file:
                metadata_rows = [dict(row) for row in csv.DictReader(file)]
            for row in metadata_rows:
                row["scenario_id"] = "scenario_a"
            write_csv_rows(metadata_path, metadata_rows)
            self.assertEqual(hazard.main_with_args(common_args), 0)
            first_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): record.get("execution_signature")
                for record in first_plan.get("chunk_manifests", [])
            }
            self.assertTrue(first_signatures)

            filtered_case = yaml_load(case_path)
            filtered_case.setdefault("hazard_probability", {})
            filtered_case["hazard_probability"]["filters"] = {
                "source_zone_ids": ["zone_a"],
                "scenario_ids": ["scenario_a"],
                "block_mass_kg_min": None,
                "block_mass_kg_max": None,
            }
            write_yaml(case_path, filtered_case)

            read_calls: list[Path] = []
            original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

            def spy_read_trajectory_sample_batch(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch:
                read_calls.append(path)
                return original_read_trajectory_sample_batch(path, warnings)

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=spy_read_trajectory_sample_batch):
                self.assertEqual(hazard.main_with_args(common_args), 0)
            self.assertTrue(read_calls)

            second_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            second_signatures = {
                record.get("chunk_id"): record.get("execution_signature")
                for record in second_plan.get("chunk_manifests", [])
            }
            for chunk_id, first_signature in first_signatures.items():
                self.assertIsNotNone(first_signature)
                self.assertNotEqual(second_signatures.get(chunk_id), first_signature)

    def test_chunked_reducer_source_zone_metadata_content_fingerprint_forces_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            output_dir = chunked_dir
            case_path, source_zone_metadata_path, scenario_table_path, package_manifest_json = self._weighted_map_package_case(
                work,
                map_product_id="phase1_zone_a_weighted",
            )
            common_args = self._weighted_map_package_args(
                case_path,
                source_zone_metadata_path,
                scenario_table_path,
                package_manifest_json,
                output_dir,
            )
            self.assertEqual(hazard.main_with_args(common_args), 0)
            first_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): record.get("execution_signature")
                for record in first_plan.get("chunk_manifests", [])
            }

            source_zone_metadata = yaml_load(source_zone_metadata_path)
            provenance_notes = list(source_zone_metadata.get("provenance", {}).get("notes", []))
            provenance_notes.append("fingerprint regression coverage: content changed")
            source_zone_metadata.setdefault("provenance", {})
            source_zone_metadata["provenance"]["notes"] = provenance_notes
            write_yaml(source_zone_metadata_path, source_zone_metadata)

            read_calls: list[Path] = []
            original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

            def spy_read_trajectory_sample_batch(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch:
                read_calls.append(path)
                return original_read_trajectory_sample_batch(path, warnings)

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=spy_read_trajectory_sample_batch):
                self.assertEqual(hazard.main_with_args(common_args), 0)
            second_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_execution_index_v1.json").read_text())
            merge_state = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_merge_state_v1.json").read_text())
            second_merge_index = {
                record.get("chunk_id"): record
                for record in merge_state.get("merge_index", [])
                if isinstance(record.get("chunk_id"), str)
            }
            second_index_by_chunk = {
                record.get("chunk_id"): record
                for record in second_index.get("chunk_records", [])
            }
            self.assertTrue(read_calls)
            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                self.assertNotEqual(record.get("execution_signature"), first_signatures.get(chunk_id))
                self.assertIn(record.get("orchestration_decision"), {"executed", "completed_state_reset_for_rerun"})
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                index_record = second_index_by_chunk.get(chunk_id)
                merge_record = second_merge_index.get(chunk_id)
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertEqual(index_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(index_record.get("input_signature"), record.get("input_signature"))
                self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))

            execution_plan_signature_values = {record.get("execution_signature") for record in first_plan.get("chunk_manifests", [])}
            second_signature_values = {record.get("execution_signature") for record in second_plan.get("chunk_manifests", [])}
            self.assertNotEqual(execution_plan_signature_values, second_signature_values)

    def test_chunked_reducer_scenario_table_content_fingerprint_forces_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            output_dir = chunked_dir
            case_path, source_zone_metadata_path, scenario_table_path, package_manifest_json = self._weighted_map_package_case(
                work,
                map_product_id="phase1_zone_a_weighted",
            )
            common_args = self._weighted_map_package_args(
                case_path,
                source_zone_metadata_path,
                scenario_table_path,
                package_manifest_json,
                output_dir,
            )
            self.assertEqual(hazard.main_with_args(common_args), 0)
            first_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            first_signatures = {
                record.get("chunk_id"): record.get("execution_signature")
                for record in first_plan.get("chunk_manifests", [])
            }

            with scenario_table_path.open(newline="") as file:
                rows = list(csv.DictReader(file))
            rows[0]["sampling_weight"] = f"{float(rows[0]['sampling_weight']) + 0.01:.3f}"
            write_csv_rows(scenario_table_path, rows)

            read_calls: list[Path] = []
            original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

            def spy_read_trajectory_sample_batch(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch:
                read_calls.append(path)
                return original_read_trajectory_sample_batch(path, warnings)

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=spy_read_trajectory_sample_batch):
                self.assertEqual(hazard.main_with_args(common_args), 0)
            second_plan = json.loads((chunked_dir / "hazard_fixture_weighted_execution_plan_v1.json").read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_execution_index_v1.json").read_text())
            merge_state = json.loads((chunked_dir / "hazard_fixture_weighted_reducer_merge_state_v1.json").read_text())
            second_merge_index = {
                record.get("chunk_id"): record
                for record in merge_state.get("merge_index", [])
                if isinstance(record.get("chunk_id"), str)
            }
            second_index_by_chunk = {
                record.get("chunk_id"): record
                for record in second_index.get("chunk_records", [])
            }
            self.assertTrue(read_calls)
            for record in second_plan.get("chunk_manifests", []):
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                self.assertNotEqual(record.get("execution_signature"), first_signatures.get(chunk_id))
                self.assertIn(record.get("orchestration_decision"), {"executed", "completed_state_reset_for_rerun"})
                manifest_path = chunked_dir / "chunks" / f"{chunk_id}_manifest.json"
                manifest = json.loads(manifest_path.read_text())
                index_record = second_index_by_chunk.get(chunk_id)
                merge_record = second_merge_index.get(chunk_id)
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                self.assertEqual(index_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(index_record.get("input_signature"), record.get("input_signature"))
                self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))

            execution_plan_signature_values = {record.get("execution_signature") for record in first_plan.get("chunk_manifests", [])}
            second_signature_values = {record.get("execution_signature") for record in second_plan.get("chunk_manifests", [])}
            self.assertNotEqual(execution_plan_signature_values, second_signature_values)

    def test_chunked_reducer_skips_chunks_claimed_by_other_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            target_record = next(record for record in first_plan.get("chunk_manifests", []) if record.get("chunk_id") is not None)
            target_chunk_id = target_record.get("chunk_id")
            target_record["ownership"] = {
                "state": "claimed",
                "owner_id": "other_owner",
                "claimed_at_unix_s": 1_000_000_000,
                "lease_expires_unix_s": 2_000_000_000,
                "released_at_unix_s": None,
                "release_reason": None,
                "updated_unix_s": 10_000_000,
            }
            target_record["completion_status"] = "not_started"
            target_record["execution_status"] = "not_started"
            execution_plan_path.write_text(json.dumps(first_plan, indent=2, sort_keys=True) + "\n")

            try:
                hazard.main_with_args(
                    [
                        *common_args,
                        "--chunk-owner-id",
                        "local_owner",
                        "--output-dir",
                        str(chunked_dir),
                    ]
                )
            except SystemExit:
                pass
            second_plan = json.loads(execution_plan_path.read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            plan_record = next(
                record
                for record in second_plan.get("chunk_manifests", [])
                if record.get("chunk_id") == target_chunk_id
            )
            index_record = next(
                record
                for record in second_index.get("chunk_records", [])
                if record.get("chunk_id") == target_chunk_id
            )
            manifest = json.loads((chunked_dir / "chunks" / f"{target_chunk_id}_manifest.json").read_text())
            self.assertEqual(plan_record.get("orchestration_decision"), "skipped_by_other_owner")
            self.assertEqual(index_record.get("orchestration_decision"), "skipped_by_other_owner")
            self.assertEqual(plan_record.get("execution_signature"), index_record.get("execution_signature"))
            self.assertEqual(plan_record.get("execution_signature"), manifest.get("execution_signature"))
            self.assertEqual(plan_record.get("input_signature"), index_record.get("input_signature"))
            self.assertEqual(plan_record.get("input_signature"), manifest.get("input_signature"))

    def test_chunked_reducer_max_attempts_exceeded(self) -> None:
        def fail_all_trajectory_paths(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch | None:
            raise RuntimeError("max attempts test failure")

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
                "--max-chunk-attempts",
                "1",
            ]
            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_all_trajectory_paths):
                with self.assertRaises(SystemExit):
                    hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)])
            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_all_trajectory_paths):
                with self.assertRaises(SystemExit):
                    hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)])

            execution_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            max_attempts_records = [
                record
                for record in execution_plan.get("chunk_manifests", [])
                if record.get("orchestration_decision") == "max_attempts_exceeded"
            ]
            self.assertEqual(len(max_attempts_records), len(execution_plan.get("chunk_manifests", [])))
            failed_record = max_attempts_records[0]
            self.assertGreaterEqual(int(failed_record.get("retry_count") or 0), 1)
            self.assertTrue(
                all(record.get("orchestration_decision") == "max_attempts_exceeded" for record in max_attempts_records)
            )
            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            execution_merge = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json").read_text())
            merge_index_by_chunk = {
                record.get("chunk_id"): record
                for record in execution_merge.get("merge_index", [])
                if isinstance(record.get("chunk_id"), str)
            }
            max_attempts_index_records = [
                record
                for record in execution_index.get("chunk_records", [])
                if record.get("orchestration_decision") == "max_attempts_exceeded"
            ]
            self.assertEqual(len(max_attempts_index_records), len(execution_plan.get("chunk_manifests", [])))
            for record in max_attempts_index_records:
                chunk_id = record.get("chunk_id")
                self.assertIsNotNone(chunk_id)
                manifest = json.loads((chunked_dir / "chunks" / f"{chunk_id}_manifest.json").read_text())
                self.assertEqual(record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(record.get("input_signature"), manifest.get("input_signature"))
                if manifest.get("orchestration_decision") == "max_attempts_exceeded":
                    self.assertEqual(record.get("orchestration_decision"), "max_attempts_exceeded")
                else:
                    self.assertEqual(manifest.get("orchestration_decision"), "executed")
                self.assertEqual(int(record.get("output_bytes") or 0), 0)
                merge_record = merge_index_by_chunk.get(record.get("chunk_id"))
                if merge_record is not None:
                    self.assertEqual(merge_record.get("execution_signature"), record.get("execution_signature"))
                    self.assertEqual(merge_record.get("input_signature"), record.get("input_signature"))
                    self.assertEqual(merge_record.get("orchestration_decision"), record.get("orchestration_decision"))
                self.assertIsNotNone(record.get("completion_state"))

    def test_chunked_reducer_mixed_orchestration_and_artifact_agreement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
            ]
            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)

            execution_plan_path = chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json"
            first_plan = json.loads(execution_plan_path.read_text())
            first_records = first_plan.get("chunk_manifests", [])
            self.assertTrue(len(first_records) >= 2)

            stale_record = first_records[0]
            execute_record = first_records[1]
            stale_record["ownership"] = {
                "state": "claimed",
                "owner_id": "stale_owner",
                "claimed_at_unix_s": 1,
                "lease_expires_unix_s": 1,
                "released_at_unix_s": None,
                "release_reason": None,
                "updated_unix_s": 1,
            }
            stale_record["completion_status"] = "completed"
            stale_record["execution_status"] = "completed"
            execute_record["completion_status"] = "failed"
            execute_record["retry_count"] = 0
            execute_record["attempt_count"] = 1
            execution_plan_path.write_text(json.dumps(first_plan, indent=2, sort_keys=True) + "\n")

            self.assertEqual(hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]), 0)
            second_plan = json.loads(execution_plan_path.read_text())
            second_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            second_merge = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json").read_text())
            stale_chunk_id = stale_record.get("chunk_id")
            execute_chunk_id = execute_record.get("chunk_id")

            plan_decisions = {
                record.get("chunk_id"): record.get("orchestration_decision")
                for record in second_plan.get("chunk_manifests", [])
            }
            self.assertEqual(plan_decisions[stale_chunk_id], "stale_claim_recovered")
            self.assertEqual(plan_decisions[execute_chunk_id], "executed")
            self.assertIn("stale_claim_recovered", plan_decisions.values())
            self.assertIn("executed", plan_decisions.values())

            merge_index = {
                record.get("chunk_id"): record
                for record in second_merge.get("merge_index", [])
            }
            index_by_chunk = {
                record.get("chunk_id"): record
                for record in second_index.get("chunk_records", [])
            }
            for chunk_id, plan_record in {
                record.get("chunk_id"): record
                for record in second_plan.get("chunk_manifests", [])
            }.items():
                if not chunk_id:
                    continue
                manifest = json.loads((chunked_dir / "chunks" / f"{chunk_id}_manifest.json").read_text())
                index_record = index_by_chunk[chunk_id]
                merge_record = merge_index[chunk_id]
                self.assertIsNotNone(plan_record.get("execution_signature"))
                self.assertIsNotNone(plan_record.get("input_signature"))
                self.assertEqual(index_record.get("status"), manifest.get("status"))
                self.assertEqual(index_record.get("completion_state"), manifest.get("completion_state"))
                self.assertEqual(index_record.get("orchestration_decision"), manifest.get("orchestration_decision"))
                self.assertEqual(merge_record.get("status"), manifest.get("status"))
                self.assertEqual(merge_record.get("completion_state"), manifest.get("completion_state"))
                self.assertEqual(merge_record.get("orchestration_decision"), manifest.get("orchestration_decision"))
                self.assertEqual(plan_record.get("execution_signature"), index_record.get("execution_signature"))
                self.assertEqual(plan_record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(plan_record.get("input_signature"), index_record.get("input_signature"))
                self.assertEqual(plan_record.get("input_signature"), manifest.get("input_signature"))
                self.assertEqual(index_record.get("execution_signature"), manifest.get("execution_signature"))
                self.assertEqual(index_record.get("input_signature"), manifest.get("input_signature"))

    def test_chunked_reducer_reuses_partial_state_without_reexecution(self) -> None:
        original_read_trajectory_sample_batch = hazard.read_trajectory_sample_batch

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
                "--scheduler-count",
                "2",
                "--scheduler-index",
                "0",
                "--chunk-owner-id",
                "reuse_owner",
            ]
            self.assertEqual(
                hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]),
                0,
            )
            first_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            first_completed_records = [
                record for record in first_index.get("chunk_records", []) if record.get("completion_status") == "completed"
            ]
            self.assertEqual(len(first_completed_records), 1)
            first_completed_record = first_completed_records[0]
            first_chunk_id = first_completed_record.get("chunk_id")
            self.assertIsNotNone(first_chunk_id)
            first_chunk_state_path = chunked_dir / "chunks" / f"{first_chunk_id}_state.json"
            first_state_signature = json.dumps(
                self.assert_chunk_state_accumulator_only(first_chunk_state_path),
                sort_keys=True,
            )
            first_chunk_manifest_path = chunked_dir / "chunks" / f"{first_chunk_id}_manifest.json"
            first_chunk_manifest = json.loads(first_chunk_manifest_path.read_text())
            self.assert_chunk_state_row_counts_align_with_manifest(
                json.loads(first_chunk_state_path.read_text()),
                first_chunk_manifest,
            )

            read_calls: list[Path] = []

            def fail_if_rerun(path: Path, warnings: list[str]) -> hazard.TrajectorySampleBatch | None:
                read_calls.append(path)
                raise AssertionError(
                    f"trajectory reader should not run for reused chunk on resume: {path}"
                )

            with patch("scripts.build_hazard_layers.read_trajectory_sample_batch", side_effect=fail_if_rerun):
                self.assertEqual(
                    hazard.main_with_args([*common_args, "--output-dir", str(chunked_dir)]),
                    0,
                )
            self.assertEqual(read_calls, [])
            execution_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            chunk_records = execution_plan.get("chunk_manifests", [])
            completed = [record for record in chunk_records if record.get("completion_status") == "completed"]
            self.assertEqual(len(completed), 1)

            execution_index = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_execution_index_v1.json").read_text())
            self.assertEqual(execution_index.get("schema_version"), "reducer_execution_index_v1")
            self.assertEqual(execution_index.get("scheduled_chunk_count"), 1)
            self.assertEqual(execution_index.get("completed_chunk_count"), 1)
            completed_records = [
                record for record in execution_index.get("chunk_records", []) if record.get("completion_status") == "completed"
            ]
            self.assertEqual(len(completed_records), 1)
            completed_record = completed_records[0]
            self.assertEqual(completed_record.get("status"), "completed")
            self.assertIsNone(completed_record.get("failure_reason"))
            self.assertGreater(int(completed_record.get("rows_written") or 0), 0)
            chunk_manifest_path = Path(completed_record.get("chunk_manifest_path") or "")
            if not chunk_manifest_path:
                candidate = next(
                    (
                        path
                        for path in (chunked_dir / "chunks").glob(f'{completed_record.get("chunk_id", "")}_manifest.json')
                    ),
                    None,
                )
                self.assertIsNotNone(candidate)
                chunk_manifest_path = candidate
            else:
                self.assertNotEqual(str(chunk_manifest_path), str(chunked_dir))
            if not chunk_manifest_path.is_absolute():
                chunk_manifest_path = chunked_dir / chunk_manifest_path
            manifest_record_dict = json.loads(chunk_manifest_path.read_text())
            self.assertEqual(manifest_record_dict.get("rows_written"), completed_record.get("rows_written"))
            self.assertEqual(manifest_record_dict.get("row_count"), completed_record.get("row_count"))
            self.assertGreater(int(completed_record.get("row_count") or 0), 0)
            self.assertEqual(completed_record.get("row_count"), first_completed_record.get("row_count"))
            self.assertEqual(completed_record.get("rows_written"), first_completed_record.get("rows_written"))
            self.assertEqual(completed_record.get("output_bytes"), first_completed_record.get("output_bytes"))
            second_chunk_state = self.assert_chunk_state_accumulator_only(first_chunk_state_path)
            self.assert_chunk_state_row_counts_align_with_manifest(second_chunk_state, manifest_record_dict)
            self.assertEqual(
                json.dumps(second_chunk_state, sort_keys=True),
                first_state_signature,
            )

    def test_chunked_reducer_cross_partition_scheduler_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            chunked_dir = work / "chunked"
            common_args = [
                "--case",
                str(FIXTURE / "ensemble_case.yaml"),
                "--diagnostics",
                str(FIXTURE / "diagnostics.json"),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--reducer-workers",
                "2",
                "--scheduler-count",
                "2",
                "--chunk-owner-id",
                "cross_partition_owner",
            ]
            self.assertEqual(
                hazard.main_with_args([*common_args, "--scheduler-index", "0", "--output-dir", str(chunked_dir)]),
                0,
            )
            partition_zero_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            self.assertEqual(partition_zero_plan.get("plan_status"), "completed")
            partition_zero_completed = [
                record for record in partition_zero_plan.get("chunk_manifests", []) if record.get("completion_status") == "completed"
            ]
            self.assertEqual(len(partition_zero_completed), 1)

            self.assertEqual(
                hazard.main_with_args([*common_args, "--scheduler-index", "1", "--output-dir", str(chunked_dir)]),
                0,
            )
            final_plan = json.loads((chunked_dir / "hazard_fixture_ensemble_execution_plan_v1.json").read_text())
            self.assertEqual(final_plan.get("plan_status"), "completed")
            self.assertEqual(final_plan.get("scheduled_chunk_count"), 1)
            self.assertEqual(len([record for record in final_plan.get("chunk_manifests", []) if record.get("completion_status") == "completed"]), 2)
            merge_state = json.loads((chunked_dir / "hazard_fixture_ensemble_reducer_merge_state_v1.json").read_text())
            self.assertEqual(merge_state.get("schema_version"), "reducer_merge_state_v1")
            self.assertEqual(merge_state.get("merge_status"), "ready")

    def test_parquet_impact_events_match_csv_impact_density(self) -> None:
        try:
            import pyarrow  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("pyarrow is required for Parquet impact-event fixtures")

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            parquet_path = work / "impact_events.parquet"
            write_impact_parquet_fixture(parquet_path, FIXTURE / "ensemble_impacts")
            parquet_case = yaml_load(FIXTURE / "ensemble_case.yaml")
            parquet_case["outputs"]["ensemble_impact_events_parquet"] = str(parquet_path)
            case_path = work / "parquet_case.yaml"
            write_yaml(case_path, parquet_case)

            csv_dir = work / "csv"
            parquet_dir = work / "parquet"
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(FIXTURE / "ensemble_case.yaml"),
                        "--output-dir",
                        str(csv_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )
            self.assertEqual(
                hazard.main_with_args(
                    [
                        "--case",
                        str(case_path),
                        "--output-dir",
                        str(parquet_dir),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                    ]
                ),
                0,
            )

            self.assertEqual(
                read_layer(
                    csv_dir / "hazard_fixture_ensemble_significant_impact_density.csv",
                    "significant_impact_density",
                ),
                read_layer(
                    parquet_dir / "hazard_fixture_ensemble_significant_impact_density.csv",
                    "significant_impact_density",
                ),
            )
            metadata = json.loads((parquet_dir / "hazard_fixture_ensemble_metadata.json").read_text())
            self.assertEqual(metadata["inputs"]["impact_event_count"], 2)
            self.assertEqual(metadata["inputs"]["significant_impact_count"], 2)


def read_layer(path: Path, key: str) -> dict[tuple[int, int], float]:
    values: dict[tuple[int, int], float] = {}
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            values[(int(row["row"]), int(row["col"]))] = float(row[key])
    return values


def read_geotiff_values(path: Path) -> tuple[dict[tuple[int, int], float], dict[int, Any]]:
    data = path.read_bytes()
    if data[:4] != b"II*\0":
        raise AssertionError(f"{path} is not a little-endian classic TIFF")
    ifd_offset = struct.unpack_from("<I", data, 4)[0]
    entry_count = struct.unpack_from("<H", data, ifd_offset)[0]
    tags: dict[int, Any] = {}
    for index in range(entry_count):
        offset = ifd_offset + 2 + 12 * index
        tag, field_type, count = struct.unpack_from("<HHI", data, offset)
        value_or_offset = data[offset + 8 : offset + 12]
        tags[tag] = parse_tiff_value(data, field_type, count, value_or_offset)

    width = int(tags[256])
    height = int(tags[257])
    strip_offset = int(tags[273])
    byte_count = int(tags[279])
    if int(tags[258]) != 64 or int(tags[339]) != 3:
        raise AssertionError(f"{path} is not a float64 GeoTIFF fixture")
    values = {}
    for index in range(width * height):
        start = strip_offset + 8 * index
        if start + 8 > strip_offset + byte_count:
            raise AssertionError(f"{path} has truncated raster data")
        values[(index // width, index % width)] = struct.unpack_from("<d", data, start)[0]
    return values, tags


def parse_tiff_value(data: bytes, field_type: int, count: int, value_or_offset: bytes) -> Any:
    type_sizes = {2: 1, 3: 2, 4: 4, 12: 8}
    size = type_sizes[field_type] * count
    value_bytes = value_or_offset[:size] if size <= 4 else data[struct.unpack("<I", value_or_offset)[0] :][:size]
    if field_type == 2:
        return value_bytes.rstrip(b"\0").decode("ascii")
    if field_type == 3:
        values = struct.unpack("<" + "H" * count, value_bytes)
    elif field_type == 4:
        values = struct.unpack("<" + "I" * count, value_bytes)
    elif field_type == 12:
        values = struct.unpack("<" + "d" * count, value_bytes)
    else:
        raise AssertionError(f"unsupported TIFF field type {field_type}")
    return values[0] if count == 1 else values


def yaml_load(path: Path) -> dict:
    import yaml  # type: ignore

    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, value: dict) -> None:
    import yaml  # type: ignore

    path.write_text(yaml.safe_dump(value, sort_keys=False))


def write_impact_parquet_fixture(path: Path, impact_dir: Path) -> None:
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore

    rows: list[dict[str, object]] = []
    for csv_path in sorted(impact_dir.glob("*.csv")):
        with csv_path.open(newline="") as file:
            for row in csv.DictReader(file):
                incoming = float(row["incoming_normal_speed_mps"])
                rows.append(
                    {
                        "trajectory_id": csv_path.stem,
                        "impact_index": int(row["impact_index"]),
                        "time_s": float(row["time_s"]),
                        "x_m": float(row["x_m"]),
                        "y_m": float(row["y_m"]),
                        "z_m": float(row["z_m"]),
                        "incoming_normal_speed_mps": incoming,
                        "significant_impact": incoming >= hazard.SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS,
                    }
                )
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def write_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("\n")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_weighted_case(
    path: Path,
    metadata_path: Path,
    filters: dict | None = None,
) -> Path:
    import yaml  # type: ignore

    case = yaml_load(FIXTURE / "weighted_case.yaml")
    case["hazard_probability"]["metadata_path"] = str(metadata_path)
    if filters is not None:
        case["hazard_probability"]["filters"] = filters
    path.write_text(yaml.safe_dump(case, sort_keys=False))
    return path


def fixture_weight_rows() -> list[dict[str, str]]:
    with (FIXTURE / "weighted_metadata.csv").open(newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def write_metadata_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_first_metadata_row(path: Path) -> dict[str, str]:
    with path.open(newline="") as file:
        return dict(next(csv.DictReader(file)))


def cleanup_phase1_smoke_outputs() -> None:
    for path in PHASE1_SMOKE_OUTPUTS:
        path.unlink(missing_ok=True)
    for path in PHASE1_SMOKE_DIRS:
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
