from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import package_aoi_hazard_map as packager
from scripts.hazard_output_writers import sha256_file


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1"
MAP_MANIFEST = FIXTURE_ROOT / "tschamut_public_conditional_gate_v1_map_package_manifest.json"
PILOT_MANIFEST = FIXTURE_ROOT / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"


class AoiHazardMapPackagerTests(unittest.TestCase):
    def test_fixture_hazard_outputs_package_into_cog_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            summary = (output_root / "aoi_hazard_map_package_summary.txt").read_text(encoding="utf-8")
            release_overlay = json.loads((output_root / "overlays/release_zone.geojson").read_text(encoding="utf-8"))
            scenario_overlay = json.loads((output_root / "overlays/scenario_table.geojson").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "map_package_ready")
            self.assertEqual(manifest["package_status"], "map_package_ready")
            self.assertEqual(manifest["layer_inventory_status"], "parity_match")
            self.assertEqual(manifest["claim_boundary"]["operational_status"], "research_diagnostic")
            self.assertFalse(manifest["claim_boundary"]["annualized"])
            self.assertEqual(len(manifest["raster_outputs"]), len(report["raster_outputs"]))
            self.assertEqual(len(manifest["layer_inventory"]), len(report["inventory"]))
            self.assertTrue(all(entry["cloud_optimized"] for entry in manifest["raster_outputs"]))
            self.assertEqual(release_overlay["schema_version"], "aoi_release_zone_overlay_v1")
            self.assertEqual(release_overlay["type"], "FeatureCollection")
            self.assertEqual(len(release_overlay["features"]), 1)
            self.assertEqual(release_overlay["features"][0]["geometry"]["type"], "Polygon")
            self.assertEqual(scenario_overlay["schema_version"], "aoi_scenario_overlay_v1")
            self.assertEqual(len(scenario_overlay["features"]), 1)
            self.assertIn("map_package_ready", summary)
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").exists())
            self.assertTrue((output_root / "rasters" / "weighted_reach_probability.tif").exists())

    def test_missing_layer_reports_blocked_missing_hazard_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = tmp_path / "fixture_root"
            input_root.mkdir(parents=True, exist_ok=True)
            self.copy_fixture_manifests(input_root)
            map_manifest_path = input_root / MAP_MANIFEST.name
            map_manifest = json.loads(map_manifest_path.read_text(encoding="utf-8"))
            map_manifest["raster_outputs"][0]["path"] = str(tmp_path / "missing" / "reach_probability.tif")
            map_manifest_path.write_text(json.dumps(map_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report = packager.package_aoi_hazard_map(input_root, tmp_path / "package", overwrite=True)

        self.assertEqual(report["status"], "blocked_missing_hazard_outputs")
        self.assertTrue(report["missing_hazard_outputs"])
        self.assertIn("reach_probability.tif", report["missing_hazard_outputs"][0])

    def test_cog_conversion_failure_reports_cog_blocked_and_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            def fake_failure(input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
                return {
                    "status": "conversion_failed",
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "error": "simulated conversion failure",
                }

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=fake_failure):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "cog_blocked")
            self.assertTrue(report["cog_blockers"])
            self.assertFalse(all(entry["cloud_optimized"] for entry in manifest["raster_outputs"]))
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").exists())
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").stat().st_size > 0)

    def test_manifest_inventory_matches_written_files_and_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["layer_inventory_status"], "parity_match")
            self.assertEqual(len(manifest["layer_inventory"]), len(report["inventory"]))
            for entry in manifest["layer_inventory"]:
                path = Path(entry["path"])
                self.assertTrue(path.exists())
                self.assertEqual(entry["sha256"], sha256_file(path))
                self.assertEqual(entry["total_bytes"], path.stat().st_size)
            self.assertEqual(manifest["summary_sha256"], sha256_file(output_root / "aoi_hazard_map_package_summary.txt"))

    def fake_cog_conversion_ready(self, input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(f"converted:{input_path.name}".encode("utf-8"))
        return {
            "status": "cog_conversion_sample_ready",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "verification": {
                "status": "ok",
                "sample_raster_tiled": True,
                "sample_raster_overviews": True,
                "sample_raster_cog_layout": True,
            },
            "output_exists": True,
            "output_bytes": output_path.stat().st_size,
            "blockers": [],
        }

    def copy_fixture_manifests(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / MAP_MANIFEST.name).write_text(MAP_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
        (root / PILOT_MANIFEST.name).write_text(PILOT_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
