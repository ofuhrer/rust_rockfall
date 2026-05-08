#!/usr/bin/env python3
"""Tests for the DEM and terrain-representation sensitivity dry-run fixture."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import scripts.run_dem_terrain_sensitivity as dem_sensitivity


class DemTerrainSensitivityTests(unittest.TestCase):
    def test_build_summary_writes_deterministic_variants_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            summary = dem_sensitivity.build_summary(
                dem_sensitivity.DEFAULT_SOURCE_DEM,
                output_dir,
            )
            summary_path = output_dir / "dem_terrain_sensitivity_summary.json"
            report_path = output_dir / "dem_terrain_sensitivity_report.md"

            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(summary["schema_version"], dem_sensitivity.SCHEMA_VERSION)
            self.assertFalse(summary["invariants"]["contact_parameter_tuning_allowed"])
            self.assertIn("Do not tune", summary["invariants"]["note"])

            variants = {item["id"]: item for item in summary["terrain_variants"]}
            self.assertEqual(
                set(variants),
                {"baseline", "smooth_3x3_mean", "coarsen_2x2_mean_reexpanded"},
            )
            for variant in variants.values():
                self.assertTrue(Path(variant["path"]).exists())
                self.assertTrue(variant["same_grid_as_source"])
                self.assertRegex(variant["sha256"], r"^[0-9a-f]{64}$")

            comparisons = summary["pairwise_baseline_comparisons"]
            self.assertEqual(len(comparisons), 2)
            compared_variants = {item["comparison_variant"] for item in comparisons}
            self.assertEqual(
                compared_variants,
                {"smooth_3x3_mean", "coarsen_2x2_mean_reexpanded"},
            )
            for comparison in comparisons:
                metrics = comparison["metrics"]
                self.assertGreater(metrics["compared_cell_count"], 0)
                self.assertIn("rmse_elevation_delta_m", metrics)
                self.assertIn("mean_abs_slope_proxy_delta", metrics)
                self.assertIn("nodata_mismatch_count", metrics)

            with summary_path.open("r", encoding="utf-8") as handle:
                persisted = json.load(handle)
            self.assertEqual(persisted, summary)

            first_hashes = {variant_id: data["sha256"] for variant_id, data in variants.items()}

        with tempfile.TemporaryDirectory() as tmp:
            rerun_summary = dem_sensitivity.build_summary(
                dem_sensitivity.DEFAULT_SOURCE_DEM,
                Path(tmp),
            )
            rerun_hashes = {
                item["id"]: item["sha256"] for item in rerun_summary["terrain_variants"]
            }
            self.assertEqual(rerun_hashes, first_hashes)

    def test_report_contains_required_sections_and_no_tuning_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            dem_sensitivity.build_summary(dem_sensitivity.DEFAULT_SOURCE_DEM, output_dir)
            report = (output_dir / "dem_terrain_sensitivity_report.md").read_text(
                encoding="utf-8"
            )

        for heading in (
            "## Terrain Representation Inventory",
            "## Invariant Configuration",
            "## Command Log",
            "## Metric Comparison",
            "## Gate Table",
            "## Limitations",
            "## No-Tuning Warning",
        ):
            self.assertIn(heading, report)
        self.assertIn(dem_sensitivity.NO_TUNING_WARNING, report)

    def test_invalid_dem_shape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_dem = Path(tmp) / "bad.asc"
            bad_dem.write_text(
                "\n".join(
                    [
                        "ncols 2",
                        "nrows 2",
                        "xllcorner 0",
                        "yllcorner 0",
                        "cellsize 1",
                        "NODATA_value -9999",
                        "1 2",
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaises(dem_sensitivity.DemSensitivityError):
                dem_sensitivity.build_summary(bad_dem, Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
