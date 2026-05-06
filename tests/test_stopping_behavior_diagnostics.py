#!/usr/bin/env python3
"""Tests for stopping-behavior diagnostic summaries."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import scripts.summarize_stopping_behavior as stopping


class StoppingBehaviorDiagnosticsTests(unittest.TestCase):
    def test_trajectory_summary_reports_stop_and_impact_proxies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trajectory.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "trajectory_id",
                        "time_s",
                        "x_m",
                        "y_m",
                        "z_m",
                        "speed_mps",
                        "kinetic_j",
                        "contact_state",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "trajectory_id": "a",
                            "time_s": "0.0",
                            "x_m": "0.0",
                            "y_m": "0.0",
                            "z_m": "1.0",
                            "speed_mps": "1.0",
                            "kinetic_j": "10.0",
                            "contact_state": "airborne",
                        },
                        {
                            "trajectory_id": "a",
                            "time_s": "0.1",
                            "x_m": "1.0",
                            "y_m": "0.0",
                            "z_m": "0.5",
                            "speed_mps": "0.6",
                            "kinetic_j": "3.0",
                            "contact_state": "impact",
                        },
                        {
                            "trajectory_id": "a",
                            "time_s": "0.2",
                            "x_m": "3.0",
                            "y_m": "4.0",
                            "z_m": "0.5",
                            "speed_mps": "0.0",
                            "kinetic_j": "0.0",
                            "contact_state": "stopped",
                        },
                    ]
                )

            row = stopping.summarize_trajectory_csv(stopping.InputSpec("fixture", path))

        self.assertEqual(row["trajectory_count"], 1)
        self.assertEqual(row["final_status_counts"], {"stopped": 1})
        self.assertEqual(row["stop_reason_counts"], {"explicit_stopped_state": 1})
        self.assertEqual(row["impact_count_total"], 1)
        self.assertEqual(row["significant_impact_count_total"], 1)
        self.assertEqual(row["low_energy_contact_count_total"], 1)
        self.assertAlmostEqual(row["distance_last_significant_impact_to_final_mean_m"], 4.472135955)
        self.assertFalse(row["terrain_slope_near_stop_available"])
        self.assertTrue(row["instrumentation_gaps"])

    def test_deposition_summary_reports_final_speed_and_runout_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deposition.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["trajectory_id", "runout_m", "final_speed_mps"],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {"trajectory_id": "a", "runout_m": "10.0", "final_speed_mps": "0.01"},
                        {"trajectory_id": "b", "runout_m": "20.0", "final_speed_mps": "0.20"},
                    ]
                )

            row = stopping.summarize_deposition_csv(stopping.InputSpec("deposition", path))

        self.assertEqual(row["trajectory_count"], 2)
        self.assertEqual(
            row["stop_reason_counts"],
            {
                "deposition_row_final_speed_above_threshold": 1,
                "final_speed_below_stop_threshold_proxy": 1,
            },
        )
        self.assertAlmostEqual(row["runout_mean_m"], 15.0)
        self.assertIsNone(row["impact_count_total"])
        self.assertIn("contact_state history is unavailable", row["instrumentation_gaps"][0])

    def test_manifest_summary_reports_aggregate_counts_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "performance": {
                            "trajectory_count": 3,
                            "impact_event_count": 12,
                        },
                    }
                ),
                encoding="utf-8",
            )

            row = stopping.summarize_manifest(stopping.InputSpec("manifest", path))

        self.assertEqual(row["trajectory_count"], 3)
        self.assertEqual(row["impact_count_total"], 12)
        self.assertIsNone(row["final_speed_mean_mps"])
        self.assertTrue(row["instrumentation_gaps"])


if __name__ == "__main__":
    unittest.main()
