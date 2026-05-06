#!/usr/bin/env python3
"""Tests for first-pass hazard-layer post-processing."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import scripts.build_hazard_layers as hazard
import scripts.prepare_tschamut_swissalti3d_pilot as tschamut_pilot


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hazard"
SWISS_PILOT = ROOT / "validation" / "data" / "processed" / "swisstopo_pilot"


class HazardLayerTests(unittest.TestCase):
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
        self.assertEqual(batches[0].significant_points, ((2.0, 0.0),))
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
            [(2.0, 0.0), (3.0, 1.0)],
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
            self.assertTrue(any(output["kind"] == "hazard_layer" for output in manifest["outputs"]))
            self.assertFalse(any(output["kind"] == "hazard_report" for output in manifest["outputs"]))
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
            self.assertGreater(len(list(plotted_dir.glob("*.png"))), 0)

            manifest = json.loads((plotted_dir / "hazard_fixture_plane_manifest.json").read_text())
            self.assertTrue(manifest["performance"]["plots_enabled"])
            self.assertGreaterEqual(manifest["performance"]["plot_render_seconds"], 0.0)
            self.assertGreaterEqual(manifest["performance"]["core_output_write_seconds"], 0.0)
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
            self.assertIn(
                "kinetic_energy_exceedance_10j",
                manifest["hazard_statistics"]["generated_layer_names"],
            )
            self.assertTrue(
                any(layer["key"] == "velocity_exceedance_1p5mps" for layer in manifest["layers"])
            )

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
            self.assertEqual(metadata["hazard_probability"], probability)

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


if __name__ == "__main__":
    unittest.main()
