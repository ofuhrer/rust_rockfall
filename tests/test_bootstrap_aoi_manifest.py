from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "bootstrap_aoi_manifest.py"
PREFLIGHT_SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
PLANNER_SCRIPT_PATH = ROOT / "scripts" / "plan_swisstopo_aoi_acquisition.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


bootstrap = _load_module(SCRIPT_PATH, "bootstrap_aoi_manifest")
preflight = _load_module(PREFLIGHT_SCRIPT_PATH, "check_second_site_public_geodata_preflight_for_bootstrap_tests")
planner = _load_module(PLANNER_SCRIPT_PATH, "plan_swisstopo_aoi_acquisition_for_bootstrap_tests")


class AoiManifestBootstrapTests(unittest.TestCase):
    def test_bootstrap_from_bounds_writes_consumable_manifest_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "bootstrap_site"
            report = bootstrap.build_report(
                output_root=output_root,
                site_id="demo_bootstrap_site_v1",
                site_name="Demo Bootstrap Site",
                crs="EPSG:2056",
                vertical_datum="LN02",
                bounds=[2699000.0, 1179000.0, 2700000.0, 1180000.0],
            )

            site_config_path = output_root / "aoi_manifest.yaml"
            site_config = yaml.safe_load(site_config_path.read_text(encoding="utf-8"))
            preflight_report = preflight.build_report(site_config_path, site_id=None)
            planner_report = planner.build_report(site_config_path)

            self.assertEqual(report["bootstrap_status"], "ready")
            self.assertEqual(report["candidate_site_id"], "demo_bootstrap_site_v1")
            self.assertEqual(report["candidate_site_name"], "Demo Bootstrap Site")
            self.assertTrue(site_config_path.exists())
            self.assertTrue((output_root / "input" / "aoi_tile_catalog.yaml").exists())
            self.assertTrue((output_root / "input" / "public_geodata_acquisition.yaml").exists())
            self.assertTrue((output_root / "validation" / "policies" / "demo_bootstrap_site_v1_source_scenario_policy_v1.yaml").exists())
            self.assertEqual(site_config["schema_version"], 1)
            self.assertEqual(site_config["manifest_type"], "aoi_manifest_bootstrap_v1")
            self.assertEqual(site_config["site_extent"]["crs"], "EPSG:2056")
            self.assertEqual(site_config["site_extent"]["xmin"], 2699000.0)
            self.assertEqual(site_config["expected_aoi_tile_catalog_path"], "input/aoi_tile_catalog.yaml")
            self.assertEqual(site_config["expected_source_scenario_policy_path"], "validation/policies/demo_bootstrap_site_v1_source_scenario_policy_v1.yaml")
            self.assertEqual(preflight_report["candidate_site_id"], "demo_bootstrap_site_v1")
            self.assertEqual(preflight_report["aoi_tile_discovery"]["discovery_status"], "ready")
            self.assertEqual(preflight_report["aoi_tile_discovery"]["tile_candidate_count"], 1)
            self.assertEqual(preflight_report["aoi_tile_discovery"]["product_candidate_count"], 1)
            self.assertEqual(planner_report["planner_status"], "ready")
            self.assertEqual(planner_report["aoi_tile_discovery"]["discovery_status"], "ready")

    def test_bootstrap_manifest_id_is_deterministic_for_identical_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = bootstrap.build_report(
                output_root=root / "first",
                site_id="demo_bootstrap_site_v1",
                site_name="Demo Bootstrap Site",
                crs="EPSG:2056",
                vertical_datum="LN02",
                bounds=[2699000.0, 1179000.0, 2700000.0, 1180000.0],
            )
            second = bootstrap.build_report(
                output_root=root / "second",
                site_id="demo_bootstrap_site_v1",
                site_name="Demo Bootstrap Site",
                crs="EPSG:2056",
                vertical_datum="LN02",
                bounds=[2699000.0, 1179000.0, 2700000.0, 1180000.0],
            )

        self.assertEqual(first["manifest_id"], second["manifest_id"])

    def test_rejects_invalid_crs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "bootstrap_site"
            with self.assertRaises(bootstrap.BootstrapError):
                bootstrap.build_report(
                    output_root=output_root,
                    site_id="demo_bootstrap_site_v1",
                    site_name="Demo Bootstrap Site",
                    crs="EPSG:4326",
                    vertical_datum="LN02",
                    bounds=[2699000.0, 1179000.0, 2700000.0, 1180000.0],
                )

    def test_rejects_missing_aoi_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "bootstrap_site"
            with self.assertRaises(bootstrap.BootstrapError):
                bootstrap.build_report(
                    output_root=output_root,
                    site_id="demo_bootstrap_site_v1",
                    site_name="Demo Bootstrap Site",
                    crs="EPSG:2056",
                    vertical_datum="LN02",
                )


if __name__ == "__main__":
    unittest.main()
