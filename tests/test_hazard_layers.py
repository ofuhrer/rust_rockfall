#!/usr/bin/env python3
"""Tests for first-pass hazard-layer post-processing."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import scripts.build_hazard_layers as hazard


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hazard"


class HazardLayerTests(unittest.TestCase):
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
            self.assertTrue(metadata["hazard_only"])
            self.assertFalse(metadata["risk_modeling_included"])
            self.assertEqual(metadata["inputs"]["trajectory_count"], 2)
            self.assertEqual(metadata["inputs"]["deposition_point_count"], 2)
            self.assertEqual(metadata["inputs"]["impact_event_count"], 2)
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

            html = (output_dir / "index.html").read_text()
            self.assertIn("not operational risk", html)
            self.assertIn("How to Read Hazard Layers", html)
            self.assertIn("Reach probability", html)

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


def read_layer(path: Path, key: str) -> dict[tuple[int, int], float]:
    values: dict[tuple[int, int], float] = {}
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            values[(int(row["row"]), int(row["col"]))] = float(row[key])
    return values


if __name__ == "__main__":
    unittest.main()
