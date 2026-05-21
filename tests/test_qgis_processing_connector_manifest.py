from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "qgis_processing_connector_manifest_v1.json"
STYLE_BUNDLE_PATH = ROOT / "qgis" / "styles" / "aoi_qgis_style_bundle.json"


class QgisProcessingConnectorManifestTests(unittest.TestCase):
    def test_manifest_reuses_existing_front_doors_and_styles(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        style_bundle = json.loads(STYLE_BUNDLE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], "aoi_qgis_processing_connector_manifest_v1")
        self.assertEqual(manifest["status"], "prototype_only")
        self.assertIn("manifest-only", manifest["deferred_full_plugin_note"])
        self.assertIn("deferred", manifest["deferred_full_plugin_note"])
        self.assertIn("plugin", manifest["deferred_full_plugin_note"])

        included_actions = manifest["included_actions"]
        self.assertEqual(
            [action["command_name"] for action in included_actions],
            ["describe-config", "prepare", "candidate-review", "package-map", "workflow"],
        )

        for action in included_actions:
            self.assertIn("PYENV_VERSION=system uv run python scripts/", action["cli_command"])
            self.assertIn(action["command_name"], action["cli_command"])
            entrypoint = ROOT / action["entrypoint"]
            self.assertTrue(entrypoint.exists(), entrypoint)
            self.assertTrue(action["expected_inputs"])
            self.assertTrue(action["expected_outputs"])

        self.assertEqual(manifest["front_door"], "scripts/run_aoi_hazard_workflow.py")
        self.assertEqual(manifest["package_front_door"], "scripts/package_aoi_hazard_map.py")
        self.assertTrue((ROOT / manifest["front_door"]).exists())
        self.assertTrue((ROOT / manifest["package_front_door"]).exists())

        style_bundle_assets = manifest["style_bundle"]["style_assets"]
        self.assertEqual(manifest["style_bundle"]["schema_version"], "aoi_qgis_style_bundle_v1")
        self.assertTrue((ROOT / manifest["style_bundle"]["path"]).exists())
        self.assertEqual(len(style_bundle_assets), len(style_bundle["styles"]))

        for asset in style_bundle_assets:
            self.assertTrue((ROOT / asset["path"]).exists(), asset["path"])

        bundle_filenames = {style["filename"] for style in style_bundle["styles"]}
        manifest_filenames = {Path(asset["path"]).name for asset in style_bundle_assets}
        self.assertEqual(manifest_filenames, bundle_filenames)

        deferred_names = {entry["command_name"] for entry in manifest["deferred_commands"]}
        self.assertEqual(deferred_names, {"run-local-smoke", "run-prepared-pilot-local", "submit-balfrin", "collect"})

        package_action = next(action for action in included_actions if action["command_name"] == "package-map")
        self.assertIn("qgis/styles/", package_action["style_usage"])
        self.assertIn("diagnostic", package_action["claim_boundary"].lower())


if __name__ == "__main__":
    unittest.main()
