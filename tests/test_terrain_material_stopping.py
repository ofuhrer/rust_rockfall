#!/usr/bin/env python3
"""Tests for terrain/material-aware stopping summaries."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import scripts.summarize_stopping_behavior as stopping


class TerrainMaterialStoppingTests(unittest.TestCase):
    def test_stop_state_summary_groups_by_final_terrain_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stop_state.csv"
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
                        "terrain_material_context_available",
                        "final_terrain_class_id",
                        "final_terrain_class_name",
                        "final_terrain_class_source",
                        "last_significant_impact_terrain_class_id",
                        "last_significant_impact_terrain_class_name",
                        "last_significant_impact_terrain_class_source",
                        "significant_impact_terrain_class_counts",
                        "significant_impact_terrain_class_sequence_head",
                        "significant_impact_terrain_class_sequence_tail",
                        "significant_impact_terrain_class_sequence_truncated",
                        "significant_impact_terrain_class_unavailable_count",
                        "terrain_material_instrumentation_gaps",
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
                            "low_energy_contact_count": "2",
                            "terrain_normal_x": "0.0",
                            "terrain_normal_y": "0.0",
                            "terrain_normal_z": "1.0",
                            "terrain_slope_abs": "0.0",
                            "terrain_material_context_available": "true",
                            "final_terrain_class_id": "1",
                            "final_terrain_class_name": "synthetic_bedrock",
                            "final_terrain_class_source": "fixture_classes",
                            "last_significant_impact_terrain_class_id": "2",
                            "last_significant_impact_terrain_class_name": "synthetic_talus",
                            "last_significant_impact_terrain_class_source": "fixture_classes",
                            "significant_impact_terrain_class_counts": (
                                '{"2:synthetic_talus": 2}'
                            ),
                            "significant_impact_terrain_class_sequence_head": (
                                '["2:synthetic_talus","2:synthetic_talus"]'
                            ),
                            "significant_impact_terrain_class_sequence_tail": "[]",
                            "significant_impact_terrain_class_sequence_truncated": "false",
                            "significant_impact_terrain_class_unavailable_count": "0",
                            "terrain_material_instrumentation_gaps": "[]",
                            "runout_m": "4.0",
                        },
                        {
                            "release_id": "r2",
                            "trajectory_id": "t2",
                            "seed": "2",
                            "stop_reason": "t_max_reached_in_contact_state",
                            "final_contact_state": "impact",
                            "final_speed_mps": "1.0",
                            "final_kinetic_j": "10.0",
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
                            "terrain_normal_x": "0.0",
                            "terrain_normal_y": "0.0",
                            "terrain_normal_z": "1.0",
                            "terrain_slope_abs": "0.0",
                            "terrain_material_context_available": "true",
                            "final_terrain_class_id": "2",
                            "final_terrain_class_name": "synthetic_talus",
                            "final_terrain_class_source": "fixture_classes",
                            "last_significant_impact_terrain_class_id": "",
                            "last_significant_impact_terrain_class_name": "",
                            "last_significant_impact_terrain_class_source": "",
                            "significant_impact_terrain_class_counts": "{}",
                            "significant_impact_terrain_class_sequence_head": "[]",
                            "significant_impact_terrain_class_sequence_tail": "[]",
                            "significant_impact_terrain_class_sequence_truncated": "false",
                            "significant_impact_terrain_class_unavailable_count": "1",
                            "terrain_material_instrumentation_gaps": '["no impact class"]',
                            "runout_m": "8.0",
                        },
                    ]
                )

            aggregate = stopping.summarize_stop_state_csv(stopping.InputSpec("fixture", path))
            grouped = stopping.summarize_stop_state_csv_by_terrain_material(
                stopping.InputSpec("fixture", path)
            )
            grouped_by_impact = stopping.summarize_stop_state_csv_by_impact_terrain_material(
                stopping.InputSpec("fixture", path)
            )

        self.assertEqual(aggregate["terrain_material_context_available_count"], 2)
        self.assertEqual(
            aggregate["final_terrain_class_counts"],
            {"1:synthetic_bedrock": 1, "2:synthetic_talus": 1},
        )
        self.assertEqual(
            aggregate["last_significant_impact_terrain_class_counts"],
            {"2:synthetic_talus": 1},
        )
        self.assertEqual(
            aggregate["significant_impact_terrain_class_counts"],
            {"2:synthetic_talus": 2},
        )
        self.assertEqual(aggregate["significant_impact_count_total"], 3)
        self.assertEqual(
            aggregate["significant_impact_terrain_class_unavailable_count_total"], 1
        )
        self.assertEqual(len(grouped), 2)
        by_name = {row["final_terrain_class_name"]: row for row in grouped}
        self.assertEqual(by_name["synthetic_bedrock"]["trajectory_count"], 1)
        self.assertEqual(by_name["synthetic_bedrock"]["final_speed_mean_mps"], 0.0)
        self.assertEqual(by_name["synthetic_talus"]["final_speed_mean_mps"], 1.0)
        by_impact = {row["significant_impact_terrain_class_label"]: row for row in grouped_by_impact}
        self.assertEqual(by_impact["2:synthetic_talus"]["trajectory_count"], 1)
        self.assertEqual(by_impact["unknown"]["significant_impact_count_total"], 1)

    def test_missing_terrain_material_context_reports_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stop_state.csv"
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
                        "low_energy_contact_count",
                        "terrain_material_context_available",
                        "final_terrain_class_id",
                        "final_terrain_class_name",
                        "final_terrain_class_source",
                        "terrain_material_instrumentation_gaps",
                        "runout_m",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "release_id": "r1",
                        "trajectory_id": "t1",
                        "seed": "1",
                        "stop_reason": "explicit_stopped_state",
                        "final_contact_state": "stopped",
                        "final_speed_mps": "0.0",
                        "final_kinetic_j": "0.0",
                        "low_energy_contact_count": "1",
                        "terrain_material_context_available": "false",
                        "final_terrain_class_id": "",
                        "final_terrain_class_name": "",
                        "final_terrain_class_source": "",
                        "terrain_material_instrumentation_gaps": (
                            '["final position has no terrain/material class"]'
                        ),
                        "runout_m": "1.0",
                    }
                )

            row = stopping.summarize_stop_state_csv(stopping.InputSpec("missing", path))

        self.assertFalse(row["terrain_material_context_available"])
        self.assertEqual(row["final_terrain_class_counts"], {})
        self.assertTrue(
            any("final position has no terrain/material class" in gap for gap in row["instrumentation_gaps"])
        )


if __name__ == "__main__":
    unittest.main()
