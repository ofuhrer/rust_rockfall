#!/usr/bin/env python3
"""Tests for terrain/material diagnostic matrix summaries."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import scripts.build_terrain_material_diagnostic_matrix as matrix


class TerrainMaterialDiagnosticMatrixTests(unittest.TestCase):
    def test_explicit_stop_state_rows_are_binned_without_proxy_relabelling(self) -> None:
        rows = [
            {
                "source_label": "explicit",
                "dataset_role": "verification_or_synthetic",
                "contact_model": "translational_v0",
                "trajectory_count": "1",
                "explicit_stop_state_available": "True",
                "stop_reason": "explicit_stopped_state",
                "final_contact_state": "stopped",
                "terrain_slope_abs": "0.1",
                "low_energy_contact_count_total": "3",
                "impact_count_total": "0",
                "final_speed_mean_mps": "0.0",
                "final_kinetic_mean_j": "0.0",
                "runout_mean_m": "",
                "instrumentation_gaps": "[]",
            }
        ]

        [summary] = matrix.build_matrix(rows)

        self.assertEqual(summary["evidence_mode"], "explicit_stop_state")
        self.assertEqual(summary["stop_reason"], "explicit_stopped_state")
        self.assertEqual(summary["final_contact_state"], "stopped")
        self.assertEqual(summary["terrain_slope_abs_bin"], "flat_to_low")
        self.assertEqual(summary["low_energy_contact_count_bin"], "low")
        self.assertEqual(summary["impact_count_bin"], "none")
        self.assertEqual(summary["final_speed_bin"], "stopped_or_near_stopped")

    def test_proxy_rows_preserve_inferred_reason_labels(self) -> None:
        rows = [
            {
                "source_label": "proxy",
                "dataset_role": "tschamut_diagnostic_only",
                "contact_model": "sphere_rotational_v1",
                "trajectory_count": "480",
                "explicit_stop_state_available": "",
                "stop_reason": "",
                "final_contact_state": "",
                "terrain_slope_abs": "",
                "low_energy_contact_count_total": "",
                "impact_count_total": "71729",
                "final_speed_mean_mps": "6.725",
                "runout_mean_m": "202.953",
                "stop_reason_counts": '{"deposition_row_final_speed_above_threshold": 480}',
                "final_status_counts": "{}",
                "instrumentation_gaps": '["proxy fallback"]',
            }
        ]

        [summary] = matrix.build_matrix(rows)

        self.assertEqual(summary["evidence_mode"], "proxy_fallback")
        self.assertEqual(summary["stop_reason"], "deposition_row_final_speed_above_threshold")
        self.assertEqual(summary["terrain_slope_abs_bin"], "unknown")
        self.assertEqual(summary["impact_count_bin"], "high")
        self.assertEqual(summary["final_speed_bin"], "high_speed")
        self.assertEqual(summary["runout_class"], "long")

    def test_csv_round_trip_writes_frozen_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix.csv"
            rows = matrix.build_matrix(
                [
                    {
                        "source_label": "explicit",
                        "dataset_role": "verification_or_synthetic",
                        "contact_model": "translational_v0",
                        "trajectory_count": "1",
                        "explicit_stop_state_available": "true",
                        "stop_reason": "t_max_reached_airborne",
                        "final_contact_state": "airborne",
                        "terrain_slope_abs": "0.0",
                        "low_energy_contact_count_total": "0",
                        "impact_count_total": "0",
                        "final_speed_mean_mps": "1.0",
                        "runout_mean_m": "",
                    }
                ]
            )
            matrix.write_csv(rows, path)
            with path.open(newline="", encoding="utf-8") as handle:
                [row] = list(csv.DictReader(handle))

        self.assertEqual(row["dataset_role"], "verification_or_synthetic")
        self.assertEqual(row["evidence_mode"], "explicit_stop_state")
        self.assertEqual(row["stop_reason"], "t_max_reached_airborne")
        self.assertIn("terrain_slope_abs_bin", row)
        self.assertIn("instrumentation_gaps", row)


if __name__ == "__main__":
    unittest.main()
