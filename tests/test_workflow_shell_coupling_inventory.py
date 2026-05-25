from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inventory_workflow_shell_coupling.py"


def load_module():
    spec = importlib.util.spec_from_file_location("test_workflow_shell_coupling_inventory", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class WorkflowShellCouplingInventoryTests(unittest.TestCase):
    def test_inventory_flags_stale_script_reference_and_ignored_root_only_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "docs" / "fake_command_plan.md"
            ignored_only_path = root / "scripts" / "temporary_ignored_only.py"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            ignored_only_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                "# Fake command plan\n\n"
                "This command plan keeps the reference explicit.\n\n"
                "PYENV_VERSION=system uv run python scripts/does_not_exist.py --format json\n",
                encoding="utf-8",
            )
            ignored_only_path.write_text(
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parents[1]\n"
                "value = (ROOT / \"validation/private/example_case/manifest.json\").read_text(encoding=\"utf-8\")\n",
                encoding="utf-8",
            )

            inventory = MODULE.build_inventory([plan_path, ignored_only_path], root=root)

        command_plan_family = next(
            family for family in inventory["families"] if family["family"] == "command_plan_script_references"
        )
        ignored_root_family = next(
            family for family in inventory["families"] if family["family"] == "ignored_root_path_assumptions"
        )

        self.assertEqual(command_plan_family["severity"], "stale_reference_risk")
        self.assertIn("scripts/does_not_exist.py", command_plan_family["entries"][0]["stale_script_references"])
        self.assertEqual(ignored_root_family["severity"], "hidden_local_state_risk")
        self.assertEqual(ignored_root_family["summary"]["ignored_root_only_file_count"], 1)
        self.assertTrue(ignored_root_family["entries"][0]["ignored_root_only_dependency"])

    def test_inventory_preserves_dynamic_import_visibility_after_shared_loader_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loader_path = root / "scripts" / "shared_loader_user.py"
            loader_path.parent.mkdir(parents=True, exist_ok=True)
            loader_path.write_text(
                "from pathlib import Path\n"
                "from scripts.lib.workflow_validation import load_repo_script_module\n"
                "ROOT = Path(__file__).resolve().parents[1]\n"
                "HELPER = load_repo_script_module(ROOT, \"fixture_helper\", \"check_same_scale_artifact_readiness.py\")\n",
                encoding="utf-8",
            )

            inventory = MODULE.build_inventory([loader_path], root=root)

        dynamic_import_family = next(
            family for family in inventory["families"] if family["family"] == "dynamic_import_by_path"
        )
        self.assertEqual(dynamic_import_family["severity"], "needs_shared_helper")
        self.assertEqual(
            dynamic_import_family["entries"][0]["dynamic_imports"],
            ["scripts/check_same_scale_artifact_readiness.py"],
        )

    def test_script_audience_inventory_classifies_representative_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_text = {
                "scripts/run_aoi_hazard_workflow.py": '"""Front door."""\nimport argparse\n',
                "scripts/run_ci_local.py": "import argparse\n",
                "scripts/check_balfrin_remote_access_preflight.py": "import argparse\n",
                "scripts/archive/old_probe.py": "import argparse\n",
                "scripts/lib/path_helper.py": "def helper():\n    return None\n",
            }
            paths = []
            for rel_path, text in script_text.items():
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                paths.append(path)

            inventory = MODULE.build_inventory(paths, root=root)

        audience_family = next(
            family for family in inventory["families"] if family["family"] == "script_audience_inventory"
        )
        by_path = {entry["path"]: entry["audience"] for entry in audience_family["entries"]}

        self.assertEqual(audience_family["severity"], "routing_inventory")
        self.assertEqual(by_path["scripts/run_aoi_hazard_workflow.py"], "workflow_front_door")
        self.assertEqual(by_path["scripts/run_ci_local.py"], "user_facing")
        self.assertEqual(by_path["scripts/check_balfrin_remote_access_preflight.py"], "balfrin_only")
        self.assertEqual(by_path["scripts/archive/old_probe.py"], "historical_archival")
        self.assertEqual(by_path["scripts/lib/path_helper.py"], "internal_helper")
        self.assertEqual(
            audience_family["summary"]["audience_counts"],
            {
                "balfrin_only": 1,
                "historical_archival": 1,
                "internal_helper": 1,
                "user_facing": 1,
                "workflow_front_door": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
