from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_aoi_to_prepared_pilot_dry_run.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = _load_module(SCRIPT_PATH, "plan_aoi_to_prepared_pilot_dry_run")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_aoi_to_prepared_pilot_test",
)


class AoiToPreparedPilotDryRunTests(unittest.TestCase):
    def test_staged_aoi_with_release_polygon_emits_preparation_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            release_polygon_path = self._write_release_polygon(repo_root)

            first = planner.build_report(config_path, repo_root=repo_root, release_polygon_path=release_polygon_path)
            second = planner.build_report(config_path, repo_root=repo_root, release_polygon_path=release_polygon_path)

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "aoi_to_prepared_pilot_dry_run_v1")
        self.assertEqual(first["workflow_status"], "deferred_public_context_inputs")
        self.assertEqual(first["preparation_status"], "deferred_public_context_inputs")
        self.assertEqual(first["preparation_input"]["input_mode"], "aoi_extent_with_release_polygon")
        self.assertEqual(first["preparation_input"]["release_polygon"]["geometry_type"], "Polygon")
        self.assertEqual(first["preparation_input"]["release_polygon"]["vertex_count"], 4)
        self.assertEqual(first["preparation_input"]["release_polygon"]["extent_lv95_m"]["xmin"], 2793020.0)
        self.assertEqual(first["preparation_input"]["release_polygon"]["extent_lv95_m"]["ymax"], 1180780.0)
        self.assertTrue(first["preparation_input"]["site_config_path"].endswith("site_config.yaml"))

        terrain_categories = [row["category"] for row in first["terrain_manifests"]]
        self.assertEqual(terrain_categories, ["terrain_crop", "terrain_metadata"])
        self.assertTrue(
            first["terrain_manifests"][0]["expected_staged_path"].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"
            )
        )

        context_categories = [row["category"] for row in first["context_manifests"]]
        self.assertIn("swissimage_context", context_categories)
        self.assertIn("swisstlm3d_context", context_categories)
        self.assertTrue(
            first["release_scenario_placeholders"]["source_zone_metadata"].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"
            )
        )
        self.assertTrue(
            first["release_scenario_placeholders"]["scenario_table"].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv"
            )
        )
        self.assertTrue(
            first["release_scenario_placeholders"]["source_scenario_policy"].endswith(
                "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml"
            )
        )
        hook_ids = [row["command_id"] for row in first["command_plan_hooks"]]
        self.assertIn("second_site_aoi_acquisition_dry_run_planner", hook_ids)
        self.assertIn("second_site_release_plan_dry_run", hook_ids)
        self.assertIn("second_site_benchmark_preparation_template", hook_ids)
        self.assertTrue(
            any(path.endswith("validation/private/chant_sura_fluelapass_portability_example_v1") for path in first["ignored_output_roots"])
        )
        self.assertTrue(
            any(path.endswith("hazard/results/chant_sura_fluelapass_portability_example_v1") for path in first["ignored_output_roots"])
        )

        text_report = planner.render_text_report(first)
        self.assertIn("preparation_input:", text_report)
        self.assertIn("terrain_manifests:", text_report)
        self.assertIn("context_manifests:", text_report)
        self.assertIn("command_plan_hooks:", text_report)
        self.assertIn("ignored_output_roots:", text_report)

    def test_missing_inputs_remain_blocked_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            missing_config = repo_root / "missing_site_config.yaml"
            first = planner.build_report(missing_config, repo_root=repo_root)
            second = planner.build_report(missing_config, repo_root=repo_root)

        self.assertEqual(first, second)
        self.assertEqual(first["workflow_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_input"]["input_mode"], "missing_inputs")
        self.assertEqual(first["preparation_input"]["candidate_site_id"], "unspecified_second_site")
        self.assertTrue(first["terrain_manifests"])
        self.assertTrue(first["context_manifests"])
        self.assertTrue(
            first["terrain_manifests"][0]["expected_staged_path"].endswith(
                "data/processed/swisstopo/unspecified_second_site/input/terrain.asc"
            )
        )
        self.assertTrue(
            any(path.endswith("validation/private/unspecified_second_site") for path in first["ignored_output_roots"])
        )
        self.assertTrue(
            any(path.endswith("hazard/results/unspecified_second_site") for path in first["ignored_output_roots"])
        )

        text_report = planner.render_text_report(first)
        self.assertIn("schema_version: aoi_to_prepared_pilot_dry_run_v1", text_report)
        self.assertIn("workflow_status: blocked_missing_inputs", text_report)
        self.assertIn("preparation_input:", text_report)

    def _write_candidate_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _write_release_polygon(self, repo_root: Path) -> Path:
        polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [2793020.0, 1180220.0],
                    [2793180.0, 1180220.0],
                    [2793180.0, 1180780.0],
                    [2793020.0, 1180780.0],
                    [2793020.0, 1180220.0],
                ]
            ],
        }
        polygon_path = repo_root / "release_polygon.yaml"
        polygon_path.write_text(yaml.safe_dump({"geometry": polygon}, sort_keys=False), encoding="utf-8")
        return polygon_path


if __name__ == "__main__":
    unittest.main()
