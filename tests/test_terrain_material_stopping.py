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
                        "significant_impact_count",
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
                            "significant_impact_count": "2",
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
                            "significant_impact_count": "1",
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

    def test_terrain_material_exposure_summary_groups_by_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exposure.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "release_id",
                        "trajectory_id",
                        "seed",
                        "terrain_class_id",
                        "terrain_class_name",
                        "terrain_class_source",
                        "terrain_material_context_status",
                        "sample_count",
                        "segment_count",
                        "duration_s",
                        "path_length_m",
                        "airborne_sample_count",
                        "impact_sample_count",
                        "sliding_sample_count",
                        "rolling_sample_count",
                        "stopped_sample_count",
                        "contact_sample_count",
                        "contact_duration_s",
                        "contact_path_length_m",
                        "instrumentation_gaps",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "release_id": "r1",
                            "trajectory_id": "t1",
                            "seed": "1",
                            "terrain_class_id": "1",
                            "terrain_class_name": "synthetic_bedrock",
                            "terrain_class_source": "fixture_classes",
                            "terrain_material_context_status": "classified",
                            "sample_count": "10",
                            "segment_count": "1",
                            "duration_s": "0.9",
                            "path_length_m": "2.0",
                            "airborne_sample_count": "4",
                            "impact_sample_count": "6",
                            "sliding_sample_count": "0",
                            "rolling_sample_count": "0",
                            "stopped_sample_count": "0",
                            "contact_sample_count": "6",
                            "contact_duration_s": "0.5",
                            "contact_path_length_m": "1.0",
                            "instrumentation_gaps": "[]",
                        },
                        {
                            "release_id": "r1",
                            "trajectory_id": "t1",
                            "seed": "1",
                            "terrain_class_id": "",
                            "terrain_class_name": "",
                            "terrain_class_source": "fixture_classes",
                            "terrain_material_context_status": "unavailable",
                            "sample_count": "2",
                            "segment_count": "1",
                            "duration_s": "0.1",
                            "path_length_m": "0.2",
                            "airborne_sample_count": "2",
                            "impact_sample_count": "0",
                            "sliding_sample_count": "0",
                            "rolling_sample_count": "0",
                            "stopped_sample_count": "0",
                            "contact_sample_count": "0",
                            "contact_duration_s": "0.0",
                            "contact_path_length_m": "0.0",
                            "instrumentation_gaps": '["sample position has no terrain/material class"]',
                        },
                    ]
                )

            rows = stopping.summarize_terrain_material_exposure_csv(
                stopping.InputSpec("exposure", path)
            )

        self.assertEqual(len(rows), 3)
        aggregate = rows[0]
        self.assertEqual(aggregate["exposure_sample_count"], 12)
        self.assertEqual(aggregate["exposure_classified_sample_count"], 10)
        self.assertEqual(aggregate["exposure_unavailable_sample_count"], 2)
        grouped = {row["exposure_terrain_class_label"]: row for row in rows[1:]}
        self.assertEqual(grouped["1:synthetic_bedrock"]["contact_exposure_sample_count"], 6)
        self.assertEqual(grouped["unavailable"]["exposure_sample_count"], 2)

    def test_impact_terrain_material_summary_groups_by_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "impact_material"
            directory.mkdir()
            path = directory / "trajectory_000000.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "trajectory_id",
                        "seed",
                        "impact_index",
                        "time_s",
                        "x_m",
                        "y_m",
                        "z_m",
                        "significant_impact",
                        "incoming_normal_speed_mps",
                        "terrain_class_id",
                        "terrain_class_name",
                        "terrain_class_source",
                        "terrain_material_context_status",
                        "active_parameter_override_count",
                        "active_parameter_override_fields",
                        "instrumentation_gaps",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "trajectory_id": "t1",
                            "seed": "1",
                            "impact_index": "1",
                            "time_s": "0.1",
                            "x_m": "1.0",
                            "y_m": "2.0",
                            "z_m": "3.0",
                            "significant_impact": "true",
                            "incoming_normal_speed_mps": "1.2",
                            "terrain_class_id": "1",
                            "terrain_class_name": "synthetic_bedrock",
                            "terrain_class_source": "fixture_classes",
                            "terrain_material_context_status": "classified",
                            "active_parameter_override_count": "2",
                            "active_parameter_override_fields": '["restitution_n","friction_mu"]',
                            "instrumentation_gaps": "[]",
                        },
                        {
                            "trajectory_id": "t1",
                            "seed": "1",
                            "impact_index": "2",
                            "time_s": "0.2",
                            "x_m": "2.0",
                            "y_m": "3.0",
                            "z_m": "4.0",
                            "significant_impact": "false",
                            "incoming_normal_speed_mps": "0.01",
                            "terrain_class_id": "",
                            "terrain_class_name": "",
                            "terrain_class_source": "fixture_classes",
                            "terrain_material_context_status": "unavailable",
                            "active_parameter_override_count": "0",
                            "active_parameter_override_fields": "[]",
                            "instrumentation_gaps": (
                                '["impact position has no terrain/material class"]'
                            ),
                        },
                    ]
                )

            rows = stopping.summarize_impact_terrain_material_csv(
                stopping.InputSpec("impact_material", directory)
            )

        self.assertEqual(len(rows), 3)
        aggregate = rows[0]
        self.assertEqual(aggregate["impact_count_total"], 2)
        self.assertEqual(aggregate["significant_impact_count_total"], 1)
        self.assertEqual(aggregate["impact_terrain_material_classified_count"], 1)
        self.assertEqual(aggregate["impact_terrain_material_unavailable_count"], 1)
        self.assertEqual(
            aggregate["impact_terrain_class_counts"],
            {"1:synthetic_bedrock": 1, "unavailable": 1},
        )
        self.assertEqual(
            aggregate["impact_active_parameter_override_field_counts"],
            {"friction_mu": 1, "restitution_n": 1},
        )
        grouped = {row["impact_terrain_class_label"]: row for row in rows[1:]}
        self.assertEqual(grouped["1:synthetic_bedrock"]["impact_count_total"], 1)
        self.assertEqual(grouped["unavailable"]["impact_terrain_material_unavailable_count"], 1)


if __name__ == "__main__":
    unittest.main()
