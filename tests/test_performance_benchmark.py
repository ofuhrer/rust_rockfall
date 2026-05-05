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
                terrain_size=16,
                cell_size=2.0,
                dt=0.05,
                t_max=0.2,
                seed=123,
            )

            self.assertEqual(len(runs), len(perf.CONTACT_MODELS) * len(perf.OUTPUT_MODES))
            self.assertTrue((output_root / "inputs" / "synthetic_scale_dem.asc").exists())
            self.assertTrue((output_root / "inputs" / "synthetic_scale_terrain_metadata.yaml").exists())
            self.assertTrue((output_root / "inputs" / "release_zone_2.yaml").exists())

            summary_only = next(run for run in runs if run.mode_name == "summary_only")
            case = yaml.safe_load(summary_only.case_path.read_text())
            self.assertEqual(case["case_id"], summary_only.run_id)
            self.assertEqual(case["expected"]["values"]["release_zone_point_count"], 2.0)
            self.assertNotIn("ensemble_trajectories_dir", case["outputs"])
            self.assertNotIn("ensemble_impact_events_dir", case["outputs"])

            full_output = next(run for run in runs if run.mode_name == "trajectories_impacts")
            full_case = yaml.safe_load(full_output.case_path.read_text())
            self.assertIn("ensemble_trajectories_dir", full_case["outputs"])
            self.assertIn("ensemble_impact_events_dir", full_case["outputs"])
            self.assertEqual(full_case["simulation"]["max_steps"], 4)

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
                write_impacts=False,
                case_path=output_root / "case.yaml",
                manifest_path=manifest,
                diagnostics_path=output_root / "metrics.json",
            )

            row = perf.row_from_manifest(run=run, stage="validation", manifest_path=manifest)
            self.assertEqual(row["trajectories_per_second"], 10.0)
            self.assertEqual(row["impacts_per_second"], 4.0)
            self.assertEqual(row["output_bytes"], 1024)

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
