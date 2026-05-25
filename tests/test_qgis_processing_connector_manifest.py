from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "qgis_processing_connector_manifest_v1.json"
STYLE_BUNDLE_PATH = ROOT / "qgis" / "styles" / "aoi_qgis_style_bundle.json"
AOI_MANUAL_PATH = ROOT / "docs" / "aoi_user_manual.md"
WORKFLOW_SCRIPT_PATH = ROOT / "scripts" / "run_aoi_hazard_workflow.py"


def load_supported_commands() -> set[str]:
    source = WORKFLOW_SCRIPT_PATH.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "SUPPORTED_COMMANDS":
                supported = ast.literal_eval(node.value)
                return set(supported)
    raise AssertionError(f"could not find SUPPORTED_COMMANDS in {WORKFLOW_SCRIPT_PATH}")


def extract_manual_commands() -> set[str]:
    manual = AOI_MANUAL_PATH.read_text(encoding="utf-8")
    return {
        match.group(1)
        for match in re.finditer(r"scripts/run_aoi_hazard_workflow\.py\s+([a-z0-9-]+)", manual)
    }


class QgisProcessingConnectorManifestTests(unittest.TestCase):
    def test_manifest_reuses_existing_front_doors_commands_and_styles(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        style_bundle = json.loads(STYLE_BUNDLE_PATH.read_text(encoding="utf-8"))
        supported_commands = load_supported_commands()
        manual_commands = extract_manual_commands()

        self.assertEqual(
            manifest["schema_version"],
            "aoi_qgis_processing_connector_manifest_v1",
            "update the manifest fixture if the connector schema version changes",
        )
        self.assertEqual(
            manifest["status"],
            "prototype_only",
            "the QGIS connector manifest should remain prototype-only until a real plugin exists",
        )
        self.assertIn("manifest-only", manifest["deferred_full_plugin_note"])
        self.assertIn("deferred", manifest["deferred_full_plugin_note"])
        self.assertIn("plugin", manifest["deferred_full_plugin_note"])

        included_actions = manifest["included_actions"]
        included_command_names = [action["command_name"] for action in included_actions]
        expected_command_names = [
            "describe-config",
            "prepare",
            "candidate-review",
            "package-map",
            "workflow",
        ]
        self.assertEqual(
            included_command_names,
            expected_command_names,
            "rename the manifest actions and the manual command path together when the AOI front door changes",
        )
        self.assertTrue(
            set(included_command_names).issubset(manual_commands),
            "the QGIS connector manifest actions must remain documented in the AOI manual",
        )
        self.assertTrue(
            set(included_command_names).issubset(supported_commands),
            f"manifest action names must stay within the supported CLI subcommands: missing={sorted(set(included_command_names) - supported_commands)}",
        )

        for action in included_actions:
            self.assertIn(
                "PYENV_VERSION=system uv run python scripts/",
                action["cli_command"],
                f"{action['action_id']} should invoke the tracked AOI front door directly",
            )
            self.assertIn(
                action["command_name"],
                action["cli_command"],
                f"{action['action_id']} cli_command should mention the documented subcommand name",
            )
            entrypoint = ROOT / action["entrypoint"]
            self.assertTrue(entrypoint.exists(), f"manifest entrypoint missing: {entrypoint}")
            self.assertTrue(action["expected_inputs"], f"{action['action_id']} must declare expected inputs")
            self.assertTrue(action["expected_outputs"], f"{action['action_id']} must declare expected outputs")

        self.assertEqual(
            manifest["front_door"],
            "scripts/run_aoi_hazard_workflow.py",
            "rename the manifest front door together with the AOI workflow script",
        )
        self.assertEqual(
            manifest["package_front_door"],
            "scripts/package_aoi_hazard_map.py",
            "rename the package front door together with the AOI packager script",
        )
        self.assertTrue((ROOT / manifest["front_door"]).exists(), f"front door missing: {manifest['front_door']}")
        self.assertTrue((ROOT / manifest["package_front_door"]).exists(), f"package front door missing: {manifest['package_front_door']}")

        style_bundle_assets = manifest["style_bundle"]["style_assets"]
        self.assertEqual(
            manifest["style_bundle"]["schema_version"],
            "aoi_qgis_style_bundle_v1",
            "update the manifest style bundle schema version if the tracked style bundle format changes",
        )
        self.assertTrue(
            (ROOT / manifest["style_bundle"]["path"]).exists(),
            f"style bundle index missing: {manifest['style_bundle']['path']}",
        )
        self.assertEqual(
            len(style_bundle_assets),
            len(style_bundle["styles"]),
            "the manifest style bundle asset list must stay aligned with the tracked QGIS style bundle",
        )

        for asset in style_bundle_assets:
            asset_path = ROOT / asset["path"]
            self.assertTrue(asset_path.exists(), f"tracked style asset missing: {asset['path']}")

        bundle_by_style_id = {style["style_id"]: style for style in style_bundle["styles"]}
        manifest_by_style_id = {asset["style_id"]: asset for asset in style_bundle_assets}
        self.assertSetEqual(
            set(manifest_by_style_id),
            set(bundle_by_style_id),
            "rename the tracked style IDs in the manifest and bundle together",
        )
        for style_id, manifest_asset in manifest_by_style_id.items():
            bundle_asset = bundle_by_style_id[style_id]
            self.assertEqual(
                Path(manifest_asset["path"]).name,
                bundle_asset["filename"],
                f"style asset filename drift for {style_id}: update the manifest and qgis/styles bundle together",
            )
            self.assertEqual(
                manifest_asset["path"],
                f"qgis/styles/{bundle_asset['filename']}",
                f"style asset path drift for {style_id}: keep the manifest path in sync with the tracked QGIS bundle",
            )

        deferred_names = {entry["command_name"] for entry in manifest["deferred_commands"]}
        self.assertSetEqual(
            deferred_names,
            {"run-local-smoke", "run-prepared-pilot-local", "submit-balfrin", "collect"},
            "the deferred command list changed; update the manifest and the manual notes together",
        )
        self.assertTrue(
            deferred_names.issubset(supported_commands),
            f"deferred command names must stay within the supported CLI subcommands: missing={sorted(deferred_names - supported_commands)}",
        )

        package_action = next(action for action in included_actions if action["command_name"] == "package-map")
        self.assertIn(
            "qgis/styles/",
            package_action["style_usage"],
            "package-map should continue to document that it copies the tracked QGIS styles",
        )
        self.assertIn(
            "diagnostic",
            package_action["claim_boundary"].lower(),
            "package-map claim boundaries must remain diagnostic-only",
        )


if __name__ == "__main__":
    unittest.main()
