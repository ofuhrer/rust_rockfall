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
            self.assertIn("Reach probability", html)


def read_layer(path: Path, key: str) -> dict[tuple[int, int], float]:
    values: dict[tuple[int, int], float] = {}
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            values[(int(row["row"]), int(row["col"]))] = float(row[key])
    return values


if __name__ == "__main__":
    unittest.main()
