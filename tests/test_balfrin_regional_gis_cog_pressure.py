from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import summarize_balfrin_regional_gis_cog_pressure as pressure


class BalfrinRegionalGisCogPressureTests(unittest.TestCase):
    def test_measured_regional_pressure_summary_reports_blocked_standard_root_and_ready_conversion(self) -> None:
        report = pressure.build_report(
            artifact_root=Path("hazard/results/tschamut_public_pilot/target_gate_v1"),
            converted_package_root=Path("hazard/results/tschamut_public_pilot/gate_v1_cog_export"),
            raster_metadata_provider=self._fake_cog_metadata,
        )

        self.assertEqual(report["pressure_state"], "measured_blocked")
        self.assertEqual(report["evidence_class"], "measured")
        self.assertEqual(report["standard_root"]["readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["standard_root"]["file_count"], 56)
        self.assertEqual(report["standard_root"]["byte_count"], 79160991)
        self.assertEqual(report["standard_root"]["raster_count"], 22)
        self.assertEqual(report["standard_root"]["blockers"], ["manifest_cloud_optimized_false"])
        self.assertIn("convert_same_scale_package_to_cog.py", report["standard_root"]["next_unblock_action"])
        self.assertEqual(report["converted_package_readiness_status"], "cog_package_ready_with_scope_delta")
        self.assertEqual(report["converted_package"]["file_count"], 52)
        self.assertEqual(report["converted_package"]["byte_count"], 55873028)
        self.assertEqual(report["converted_package"]["raster_count"], 20)
        self.assertEqual(report["converted_package"]["cog_package_status"], "cog_package_ready_with_scope_delta")
        regional = report["measured_regional_split_comparison"]
        self.assertEqual(regional["measurement_status"], "measured_existing_balfrin_artifacts")
        self.assertEqual(regional["job_id"], "4350232")
        self.assertEqual(regional["hazard_output_file_count"], 53)
        self.assertEqual(regional["hazard_output_bytes"], 55837701)
        self.assertTrue(regional["within_standard_root_band"])
        self.assertFalse(regional["within_converted_package_band"])
        self.assertEqual(
            regional["next_measured_run_candidate"],
            "bounded_reduced_output_regional_split_retry_after_standard_root_cog_conversion",
        )
        self.assertEqual(report["pressure_summary"].startswith("Measured regional GIS/COG pressure is blocked"), True)
        json.dumps(report, sort_keys=True)
        text = pressure.render_text_report(report)
        self.assertIn("pressure_state: measured_blocked", text)
        self.assertIn("standard_root_readiness_status: gis_package_ready_cog_blocked", text)
        self.assertIn("converted_package_readiness_status: cog_package_ready_with_scope_delta", text)
        self.assertIn("measured_regional_split_comparison:", text)
        self.assertIn("within_standard_root_band: True", text)

    def test_missing_inputs_report_blocks_and_names_unblock_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact_root = tmp_path / "missing_target_gate_v1"
            converted_root = tmp_path / "gate_v1_cog_export"
            report = pressure.build_report(
                artifact_root=artifact_root,
                converted_package_root=converted_root,
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["pressure_state"], "blocked_missing_inputs")
        self.assertEqual(report["standard_root"]["readiness_status"], "blocked_missing_inputs")
        self.assertEqual(report["standard_root"]["next_unblock_action"], f"restore the missing package manifests under {artifact_root}")
        self.assertIn("cannot be summarized", report["pressure_summary"])

    def _fake_cog_metadata(self, path: Path) -> dict[str, object]:
        return {
            "status": "ok",
            "driver": "GTiff",
            "size": [300, 304],
            "epsg": 2056,
            "geo_transform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
            "block_size": [256, 256],
            "nodata": -9999.0,
            "overview_count": 2,
            "image_structure": {"INTERLEAVE": "BAND", "LAYOUT": "COG", "COMPRESSION": "ZSTD"},
        }


if __name__ == "__main__":
    unittest.main()
