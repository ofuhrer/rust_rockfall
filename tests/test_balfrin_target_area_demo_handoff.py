from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_target_area_demo_handoff.py"
SPEC = importlib.util.spec_from_file_location("generate_balfrin_target_area_demo_handoff", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinTargetAreaDemoHandoffTests(unittest.TestCase):
    def test_target_area_handoff_bundle_is_template_only_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            output_root = Path(output_tmp) / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"

            first = MODULE.build_report(MODULE.DEFAULT_CONTRACT, output_root)
            second = MODULE.build_report(MODULE.DEFAULT_CONTRACT, output_root)

            case_output = first["case_skeleton_output"]
            case = yaml.safe_load(Path(case_output["case_skeleton_path"]).read_text(encoding="utf-8"))
            command_manifest = json.loads(Path(case_output["command_manifest_path"]).read_text(encoding="utf-8"))
            expected_output_roots = yaml.safe_load(Path(case_output["expected_output_roots_path"]).read_text(encoding="utf-8"))
            scenario_handoff = yaml.safe_load(Path(case_output["scenario_generation_handoff_path"]).read_text(encoding="utf-8"))
            gis_scope_summary = yaml.safe_load(Path(case_output["gis_scope_summary_path"]).read_text(encoding="utf-8"))
            bundle_report = yaml.safe_load(Path(case_output["bundle_report_path"]).read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_target_area_demo_handoff_v1")
        self.assertEqual(first["bundle_status"], "template_only")
        self.assertEqual(first["bundle_runnable_status"], "runnable")
        self.assertEqual(first["target_area_id"], "tschamut_public_pilot")
        self.assertEqual(first["target_area_name"], "Tschamut public pilot")
        self.assertEqual(first["blocked_reason"], "template_only frozen target-area handoff")
        self.assertTrue(first["scale_up_authorized"] is False)
        self.assertTrue(first["distributed_execution_authorized"] is False)
        self.assertTrue(first["operational_claims_allowed"] is False)
        self.assertEqual(case["schema_version"], "balfrin_target_area_demo_case_skeleton_v1")
        self.assertEqual(case["case_skeleton_status"], "template_only")
        self.assertEqual(case["blocked_execution_status"], "template_only")
        self.assertEqual(case["bundle_status"], "template_only")
        self.assertEqual(case["mode"], "template_only")
        self.assertEqual(case["scenario_generation_handoff"]["status"], "template_only")
        self.assertEqual(case["gis_scope_summary"]["status"], "template_only")
        self.assertEqual(case["scenario_generation_handoff"], scenario_handoff)
        self.assertEqual(case["gis_scope_summary"], gis_scope_summary)
        self.assertEqual(bundle_report["bundle_status"], "template_only")
        self.assertEqual(bundle_report["bundle_runnable_status"], "runnable")
        self.assertEqual(bundle_report["target_area_id"], "tschamut_public_pilot")
        self.assertEqual(command_manifest["schema_version"], "balfrin_target_area_demo_command_manifest_v1")
        self.assertIn("target_area_handoff_materialization", command_manifest["command_groups"][1]["id"])
        self.assertEqual(command_manifest["blocked_template_commands"], ["materialize_target_area_handoff_bundle"])
        self.assertEqual(command_manifest["commands"][0]["execution_class"], "runnable")
        self.assertEqual(command_manifest["commands"][1]["execution_class"], "template_only")
        self.assertEqual(expected_output_roots["schema_version"], "balfrin_target_area_demo_expected_output_roots_v1")
        self.assertIn(str(Path(output_tmp) / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"), first["expected_output_roots"])
        self.assertIn(
            "validation/private/tschamut_public_pilot/target_gate_v1",
            first["expected_output_roots"],
        )
        self.assertTrue(case["command_sequence"][1]["blocked_reason"])
        self.assertTrue(case["gis_scope_summary"]["planned_raster_products"])
        self.assertTrue(case["gis_scope_summary"]["planned_vector_products"])
        self.assertTrue(case["gis_scope_summary"]["no_hazard_layers_generated"])
        self.assertIn("scenario_generation_handoff:", MODULE.render_text_report(first))
        self.assertIn("bundle_status: template_only", MODULE.render_text_report(first))
        self.assertTrue(
            case["scenario_generation_handoff"]["target_gate_case_path"].endswith(
                "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml"
            )
        )
        self.assertTrue(
            case["scenario_generation_handoff"]["source_zone_metadata_path"].endswith(
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
            )
        )
        self.assertGreater(case["scenario_generation_handoff"]["scenario_table_row_count"], 0)
        self.assertTrue(case["gis_scope_summary"]["conditional_gate_case_path"].endswith("tschamut_public_target_gate_case.yaml"))


if __name__ == "__main__":
    unittest.main()
