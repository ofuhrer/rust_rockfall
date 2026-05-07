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
                        {
                            "trajectory_id": "b",
                            "time_s": "0.0",
                            "x_m": "0.0",
                            "y_m": "0.0",
                            "z_m": "0.5",
                            "speed_mps": "0.04",
                            "kinetic_j": "0.001",
                            "contact_state": "impact",
                        },
                        {
                            "trajectory_id": "b",
                            "time_s": "0.1",
                            "x_m": "0.01",
                            "y_m": "0.0",
                            "z_m": "0.5",
                            "speed_mps": "0.03",
                            "kinetic_j": "0.001",
                            "contact_state": "sliding",
                        },
                    ]
                )

            row = stopping.summarize_trajectory_csv(stopping.InputSpec("fixture", path))

        self.assertEqual(row["trajectory_count"], 2)
        self.assertEqual(row["final_status_counts"], {"sliding": 1, "stopped": 1})
        self.assertEqual(
            row["stop_reason_counts"],
            {"explicit_stopped_state": 1, "final_speed_below_stop_threshold_proxy": 1},
        )
        self.assertEqual(row["impact_count_total"], 2)
        self.assertEqual(row["significant_impact_count_total"], 1)
        self.assertEqual(row["low_energy_contact_count_total"], 3)
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

    def test_stop_state_sidecar_summary_uses_explicit_per_trajectory_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ensemble_stop_state.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "release_id",
                        "trajectory_id",
                        "seed",
                        "stop_reason",
                        "final_contact_state",
                        "final_speed_mps",
                        "final_kinetic_j",
                        "termination_low_velocity",
                        "termination_max_steps",
                        "termination_t_max",
                        "termination_domain_exit",
                        "termination_terrain_error",
                        "last_significant_impact_time_s",
                        "last_significant_impact_x_m",
                        "last_significant_impact_y_m",
                        "last_significant_impact_z_m",
                        "distance_last_significant_impact_to_final_m",
                        "low_energy_contact_count",
                        "terrain_normal_x",
                        "terrain_normal_y",
                        "terrain_normal_z",
                        "terrain_slope_abs",
                        "runout_m",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "release_id": "r1",
                            "trajectory_id": "t1",
                            "seed": "1",
                            "stop_reason": "explicit_stopped_state",
                            "final_contact_state": "stopped",
                            "final_speed_mps": "0.0",
                            "final_kinetic_j": "0.0",
                            "termination_low_velocity": "true",
                            "termination_max_steps": "false",
                            "termination_t_max": "false",
                            "termination_domain_exit": "false",
                            "termination_terrain_error": "false",
                            "last_significant_impact_time_s": "0.5",
                            "last_significant_impact_x_m": "1.0",
                            "last_significant_impact_y_m": "0.0",
                            "last_significant_impact_z_m": "0.5",
                            "distance_last_significant_impact_to_final_m": "2.0",
                            "low_energy_contact_count": "3",
                            "terrain_normal_x": "0.0",
                            "terrain_normal_y": "0.0",
                            "terrain_normal_z": "1.0",
                            "terrain_slope_abs": "0.0",
                            "runout_m": "10.0",
                        },
                        {
                            "release_id": "r2",
                            "trajectory_id": "t2",
                            "seed": "2",
                            "stop_reason": "t_max_reached_airborne",
                            "final_contact_state": "airborne",
                            "final_speed_mps": "2.0",
                            "final_kinetic_j": "20.0",
                            "termination_low_velocity": "false",
                            "termination_max_steps": "true",
                            "termination_t_max": "true",
                            "termination_domain_exit": "false",
                            "termination_terrain_error": "false",
                            "last_significant_impact_time_s": "",
                            "last_significant_impact_x_m": "",
                            "last_significant_impact_y_m": "",
                            "last_significant_impact_z_m": "",
                            "distance_last_significant_impact_to_final_m": "",
                            "low_energy_contact_count": "0",
                            "terrain_normal_x": "",
                            "terrain_normal_y": "",
                            "terrain_normal_z": "",
                            "terrain_slope_abs": "",
                            "runout_m": "20.0",
                        },
                    ]
                )

            row = stopping.summarize_stop_state_csv(stopping.InputSpec("sidecar", path))

        self.assertEqual(row["source_kind"], "ensemble_stop_state_csv")
        self.assertTrue(row["explicit_stop_state_available"])
        self.assertEqual(row["trajectory_count"], 2)
        self.assertEqual(
            row["stop_reason_counts"],
            {"explicit_stopped_state": 1, "t_max_reached_airborne": 1},
        )
        self.assertEqual(row["final_status_counts"], {"airborne": 1, "stopped": 1})
        self.assertEqual(row["low_energy_contact_count_total"], 3)
        self.assertEqual(row["distance_last_significant_impact_to_final_mean_m"], 2.0)
        self.assertEqual(row["runout_mean_m"], 15.0)
        self.assertTrue(row["terrain_slope_near_stop_available"])

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

    def test_manifest_summary_prefers_ensemble_stop_state_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "performance": {
                            "trajectory_count": 4,
                            "impact_event_count": 8,
                        },
                        "stop_state_summary": {
                            "schema_version": "stop_state_summary_v1",
                            "path": "validation/results/example_stop_state.csv",
                            "trajectory_count": 4,
                            "explicit_stop_state_count": 4,
                            "stop_reason_counts": {"explicit_stopped_state": 4},
                            "final_contact_state_counts": {"stopped": 4},
                            "low_energy_contact_count_total": 12,
                            "terrain_slope_available_count": 4,
                            "final_speed_mean_mps": 0.01,
                            "final_speed_max_mps": 0.02,
                            "final_kinetic_mean_j": 0.1,
                            "final_kinetic_max_j": 0.2,
                            "limitations": ["diagnostic only"],
                        },
                        "stop_state": {
                            "stop_reason": "t_max_reached_airborne",
                            "final_contact_state": "airborne",
                            "final_speed_mps": 9.0,
                            "final_kinetic_j": 81.0,
                            "termination_flags": {
                                "low_velocity": False,
                                "max_steps": True,
                                "t_max": True,
                                "domain_exit": False,
                                "terrain_error": False,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            row = stopping.summarize_manifest(stopping.InputSpec("manifest", path))

        self.assertEqual(row["source_kind"], "run_manifest_stop_state_summary_v1")
        self.assertEqual(row["trajectory_count"], 4)
        self.assertEqual(row["impact_count_total"], 8)
        self.assertEqual(row["stop_reason_counts"], {"explicit_stopped_state": 4})
        self.assertEqual(row["final_status_counts"], {"stopped": 4})
        self.assertEqual(row["final_speed_mean_mps"], 0.01)
        self.assertEqual(row["low_energy_contact_count_total"], 12)
        self.assertTrue(row["terrain_slope_near_stop_available"])

    def test_manifest_summary_prefers_explicit_stop_state_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "performance": {
                            "trajectory_count": 1,
                            "impact_event_count": 2,
                        },
                        "stop_state": {
                            "stop_reason": "t_max_reached_airborne",
                            "final_contact_state": "airborne",
                            "final_speed_mps": 1.25,
                            "final_kinetic_j": 7.8125,
                            "termination_flags": {
                                "low_velocity": False,
                                "max_steps": True,
                                "t_max": True,
                                "domain_exit": False,
                                "terrain_error": False,
                            },
                            "last_significant_impact_time_s": None,
                            "last_significant_impact_x_m": None,
                            "last_significant_impact_y_m": None,
                            "last_significant_impact_z_m": None,
                            "distance_last_significant_impact_to_final_m": None,
                            "low_energy_contact_count": 0,
                            "terrain_normal_x": 0.0,
                            "terrain_normal_y": 0.0,
                            "terrain_normal_z": 1.0,
                            "terrain_slope_abs": 0.0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            row = stopping.summarize_manifest(stopping.InputSpec("manifest", path))

        self.assertTrue(row["explicit_stop_state_available"])
        self.assertEqual(row["stop_reason"], "t_max_reached_airborne")
        self.assertEqual(row["final_contact_state"], "airborne")
        self.assertEqual(row["stop_reason_counts"], {"t_max_reached_airborne": 1})
        self.assertEqual(row["final_status_counts"], {"airborne": 1})
        self.assertEqual(row["final_speed_mean_mps"], 1.25)
        self.assertEqual(row["final_kinetic_mean_j"], 7.8125)
        self.assertTrue(row["termination_t_max"])
        self.assertTrue(row["termination_max_steps"])
        self.assertFalse(row["termination_low_velocity"])
        self.assertTrue(row["terrain_slope_near_stop_available"])
        self.assertEqual(row["terrain_normal_z"], 1.0)
        self.assertEqual(row["low_energy_contact_count_total"], 0)
        self.assertIn(
            "no significant impact reached",
            "; ".join(row["instrumentation_gaps"]),
        )

    def test_diagnostics_summary_reads_explicit_stop_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "diagnostics.json"
            path.write_text(
                json.dumps(
                    {
                        "case_id": "validation_chant_sura_contact",
                        "metrics": {
                            "validation_trajectory_count": 3,
                            "contact_event_compared_count": 2,
                        },
                        "stop_state": {
                            "stop_reason": "t_max_reached_airborne",
                            "final_contact_state": "airborne",
                            "final_speed_mps": 5.0,
                            "final_kinetic_j": 100.0,
                            "termination_flags": {
                                "low_velocity": False,
                                "max_steps": True,
                                "t_max": True,
                                "domain_exit": False,
                                "terrain_error": False,
                            },
                            "low_energy_contact_count": 0,
                            "terrain_normal_x": 0.0,
                            "terrain_normal_y": 0.0,
                            "terrain_normal_z": 1.0,
                            "terrain_slope_abs": 0.0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            row = stopping.summarize_diagnostics_json(
                stopping.InputSpec("chant_sura_contact", path)
            )

        self.assertEqual(row["source_kind"], "diagnostics_json")
        self.assertTrue(row["explicit_stop_state_available"])
        self.assertEqual(row["trajectory_count"], 3)
        self.assertEqual(row["impact_count_total"], 2)
        self.assertEqual(row["stop_reason"], "t_max_reached_airborne")


if __name__ == "__main__":
    unittest.main()
