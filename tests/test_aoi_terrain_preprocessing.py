from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "plan_aoi_terrain_preprocessing.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
PREPARED_CONFIG_PATH = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
PREPARED_FIXTURE_ROOT = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


helper = _load_module(HELPER_PATH, "plan_aoi_terrain_preprocessing")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_terrain_preprocessing_test",
)


class AoiTerrainPreprocessingTests(unittest.TestCase):
    def test_fixture_terrain_reports_deterministic_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=PREPARED_FIXTURE_ROOT,
            )

            report = helper.build_report(repo_root=repo_root, site_config=config_path)
            second = helper.build_report(repo_root=repo_root, site_config=config_path)

        self.assertEqual(report, second)
        self.assertEqual(report["terrain_preprocessing_status"], "ready")
        self.assertEqual(report["terrain_preprocessing_package"]["crop_extent_lv95_m"]["xmin"], 2793000.0)
        self.assertEqual(report["terrain_preprocessing_package"]["crop_extent_lv95_m"]["ymax"], 1180208.0)
        self.assertEqual(report["terrain_preprocessing_package"]["resolution_m"], 2.0)
        self.assertEqual(report["terrain_preprocessing_package"]["crs_epsg"], 2056)
        self.assertEqual(report["terrain_preprocessing_package"]["nodata"], -9999.0)
        self.assertEqual(report["terrain_preprocessing_package"]["source_tile_ids"], ["2793-1180"])
        self.assertEqual(report["terrain_preprocessing_package"]["source_tiles"][0]["tile_id"], "2793-1180")
        self.assertTrue(report["output_roots"]["processed_input_root"].endswith("data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input"))
        self.assertEqual(report["blocked_reason"], "")

    def test_missing_tile_blocks_preprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=PREPARED_FIXTURE_ROOT,
            )
            catalog_path = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
            catalog["tiles"] = [tile for tile in catalog.get("tiles", []) if tile.get("tile_id") != "2793-1180"]
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")

            report = helper.build_report(repo_root=repo_root, site_config=config_path)

        self.assertEqual(report["terrain_preprocessing_status"], "blocked_missing_tile")
        self.assertEqual(report["missing_tile_ids"], ["2793-1180"])
        self.assertIn("missing AOI tile catalog coverage", report["blocked_reason"])
        self.assertEqual(report["terrain_preprocessing_package"]["source_tile_count"], 0)

    def test_metadata_mismatch_blocks_preprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=PREPARED_FIXTURE_ROOT,
            )
            metadata_path = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
            metadata["raster"]["resolution_m"] = 4.0
            metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")

            report = helper.build_report(repo_root=repo_root, site_config=config_path)

        self.assertEqual(report["terrain_preprocessing_status"], "metadata_mismatch")
        self.assertIn("resolution_m", report["metadata_mismatches"])
        self.assertIn("terrain metadata does not match staged crop", report["blocked_reason"])
        self.assertEqual(report["terrain_preprocessing_package"]["resolution_m"], 2.0)

    def _write_candidate_config(self, repo_root: Path) -> Path:
        config_data = yaml.safe_load(PREPARED_CONFIG_PATH.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
