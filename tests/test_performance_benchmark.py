#!/usr/bin/env python3
"""Tests for the opt-in synthetic performance benchmark harness."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import yaml

import scripts.run_performance_benchmark as perf


class PerformanceBenchmarkScriptTests(unittest.TestCase):
    def test_prepare_benchmark_inputs_generates_tiny_opt_in_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            runs = perf.prepare_benchmark_inputs(
                output_root=output_root,
                counts=[2],
                contact_models=["translational_v0"],
                output_modes=["summary_only", "trajectories", "csv_parquet"],
                terrain_size=16,
                cell_size=2.0,
                dt=0.05,
                t_max=0.2,
                seed=123,
            )

            self.assertEqual(len(runs), 3)
            self.assertTrue((output_root / "inputs" / "synthetic_scale_dem.asc").exists())
            self.assertTrue((output_root / "inputs" / "synthetic_scale_terrain_metadata.yaml").exists())
            self.assertTrue((output_root / "inputs" / "release_zone_2.yaml").exists())

            summary_only = next(run for run in runs if run.mode_name == "summary_only")
            case = yaml.safe_load(summary_only.case_path.read_text())
            self.assertEqual(case["case_id"], summary_only.run_id)
            self.assertEqual(case["expected"]["values"]["release_zone_point_count"], 2.0)
            self.assertNotIn("ensemble_trajectories_dir", case["outputs"])
            self.assertNotIn("ensemble_impact_events_dir", case["outputs"])
            self.assertNotIn("ensemble_impact_events_parquet", case["outputs"])

            full_output = next(run for run in runs if run.mode_name == "trajectories_csv_parquet_impacts")
            self.assertEqual(full_output.grid_xmin, 2_601_000.0)
            self.assertEqual(full_output.grid_ymin, 1_201_000.0)
            self.assertEqual(full_output.grid_ncols, 16)
            self.assertEqual(full_output.grid_nrows, 16)
            self.assertEqual(full_output.grid_cell_size, 2.0)
            full_case = yaml.safe_load(full_output.case_path.read_text())
            self.assertIn("ensemble_trajectories_dir", full_case["outputs"])
            self.assertIn("ensemble_impact_events_dir", full_case["outputs"])
            self.assertIn("ensemble_impact_events_parquet", full_case["outputs"])
            self.assertIn("trajectory_metadata_csv", full_case["outputs"])
            self.assertEqual(full_case["simulation"]["max_steps"], 4)

    def test_profiles_resolve_expected_matrix_defaults(self) -> None:
        smoke = perf.resolve_benchmark_config(perf.parse_args(["--profile", "smoke"]))
        self.assertEqual(smoke.counts, (5,))
        self.assertEqual(smoke.contact_models, ("translational_v0",))
        self.assertEqual(smoke.output_modes, ("trajectories", "parquet"))
        self.assertEqual(smoke.hazard_plots, "no-plots")
        self.assertEqual(smoke.hazard_grid, "explicit")

        standard = perf.resolve_benchmark_config(perf.parse_args([]))
        self.assertEqual(standard.profile, "standard")
        self.assertEqual(standard.counts, (10,))
        self.assertEqual(standard.contact_models, perf.CONTACT_MODELS)
        self.assertEqual(standard.output_modes, ("trajectories", "parquet"))
        self.assertEqual(standard.hazard_plots, "no-plots")
        self.assertEqual(standard.weighted_hazard, "representative")
        self.assertEqual(standard.hazard_grid, "explicit")
        self.assertEqual(standard.t_max, 3.0)
        self.assertNotIn("csv", standard.output_modes)
        self.assertNotIn("csv_parquet", standard.output_modes)

        scale = perf.resolve_benchmark_config(perf.parse_args(["--profile", "scale"]))
        self.assertEqual(scale.counts, (500, 1000))
        self.assertIn("csv_parquet", scale.output_modes)
        self.assertEqual(scale.weighted_hazard, "representative")
        self.assertEqual(scale.hazard_grid, "explicit")

    def test_custom_profile_requires_counts_and_modes(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --counts and --output-modes"):
            perf.resolve_benchmark_config(perf.parse_args(["--profile", "custom"]))

        custom = perf.resolve_benchmark_config(
            perf.parse_args(
                [
                    "--profile",
                    "custom",
                    "--counts",
                    "3",
                    "4",
                    "--output-modes",
                    "trajectories",
                    "parquet",
                    "--contact-models",
                    "translational_v0",
                ]
            )
        )
        self.assertEqual(custom.counts, (3, 4))
        self.assertEqual(custom.output_modes, ("trajectories", "parquet"))
        self.assertEqual(custom.contact_models, ("translational_v0",))
        self.assertEqual(custom.hazard_grid, "explicit")

        auto = perf.resolve_benchmark_config(
            perf.parse_args(
                [
                    "--profile",
                    "custom",
                    "--counts",
                    "3",
                    "--output-modes",
                    "trajectories",
                    "--weighted-hazard",
                    "none",
                    "--hazard-grid",
                    "auto",
                ]
            )
        )
        self.assertEqual(auto.hazard_grid, "auto")

    def test_benchmark_selection_rejects_empty_and_incompatible_modes(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one contact model"):
            perf.prepare_benchmark_inputs(
                output_root=Path("/tmp/unused"),
                counts=[1],
                contact_models=[],
                output_modes=["trajectories"],
                terrain_size=16,
                cell_size=2.0,
                dt=0.05,
                t_max=0.2,
                seed=123,
            )

        with self.assertRaisesRegex(ValueError, "at least one output mode"):
            perf.prepare_benchmark_inputs(
                output_root=Path("/tmp/unused"),
                counts=[1],
                contact_models=["translational_v0"],
                output_modes=[],
                terrain_size=16,
                cell_size=2.0,
                dt=0.05,
                t_max=0.2,
                seed=123,
            )

        with self.assertRaisesRegex(ValueError, "requires an output mode with Parquet"):
            perf.resolve_benchmark_config(
                perf.parse_args(
                    [
                        "--profile",
                        "custom",
                        "--counts",
                        "3",
                        "--output-modes",
                        "trajectories",
                        "--weighted-hazard",
                        "representative",
                    ]
                )
            )

    def test_summary_report_uses_manifest_performance_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            manifest = output_root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "performance": {
                            "total_wall_seconds": 2.0,
                            "terrain_load_seconds": 0.1,
                            "release_generation_seconds": 0.2,
                            "simulation_seconds": 1.0,
                            "output_write_seconds": 0.5,
                            "hazard_layer_seconds": None,
                            "trajectory_count": 10,
                            "impact_event_count": 4,
                            "output_file_count": 3,
                            "output_bytes": 1024,
                        }
                    }
                )
            )
            run = perf.BenchmarkRun(
                run_id="synthetic_scale_n10_baseline_summary_only",
                release_count=10,
                contact_model="translational_v0",
                mode_name="summary_only",
                write_trajectories=False,
                impact_output_mode="none",
                case_path=output_root / "case.yaml",
                manifest_path=manifest,
                diagnostics_path=output_root / "metrics.json",
                grid_xmin=0.0,
                grid_ymin=0.0,
                grid_ncols=10,
                grid_nrows=10,
                grid_cell_size=1.0,
            )

            row = perf.row_from_manifest(run=run, stage="validation", manifest_path=manifest)
            self.assertEqual(row["hazard_grid_source"], "")
            self.assertEqual(row["trajectories_per_second"], 10.0)
            self.assertEqual(row["impacts_per_second"], 4.0)
            self.assertEqual(row["output_bytes"], 1024)
            self.assertEqual(row["bounds_discovery_seconds"], "")
            self.assertEqual(row["trajectory_sample_rows_read"], 0)
            self.assertEqual(row["hazard_input_rows_per_second"], "")

            perf.write_summary_reports(output_root, [row])
            summary_csv = output_root / "summary.csv"
            summary_md = output_root / "summary.md"
            self.assertTrue(summary_csv.exists())
            self.assertTrue(summary_md.exists())
            with summary_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["run_id"], run.run_id)
            self.assertIn("Synthetic Scale Performance Benchmark Summary", summary_md.read_text())


if __name__ == "__main__":
    unittest.main()
