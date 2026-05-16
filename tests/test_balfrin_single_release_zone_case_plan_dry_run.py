from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_balfrin_single_release_zone_case_dry_run.py"
COMMAND_PLAN_SCRIPT_PATH = ROOT / "scripts" / "generate_pilot_command_plan.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_balfrin_single_release_zone_case_dry_run")
command_plan = load_module(COMMAND_PLAN_SCRIPT_PATH, "generate_pilot_command_plan_for_balfrin_case_plan_test")


class BalfrinSingleReleaseZoneCasePlanDryRunTests(unittest.TestCase):
    def test_report_is_deterministic_and_explicitly_not_an_executed_case(self) -> None:
        first = planner.build_report()
        second = planner.build_report()

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_single_release_zone_case_plan_dry_run_v1")
        self.assertEqual(first["case_plan_status"], "ready")
        self.assertEqual(first["case_execution_status"], "blocked_template_only")
        self.assertTrue(first["read_only"])
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["distributed_execution_authorized"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertEqual(first["validation_output"]["validation_output_mode"], "rebuildable_reduced_output")
        self.assertEqual(first["deterministic_generation_evidence"]["release_sampling_seed"], 34014)
        self.assertEqual(first["deterministic_generation_evidence"]["release_cell_count"], 10)
        self.assertEqual(first["deterministic_generation_evidence"]["release_zone_count"], 1)
        self.assertEqual(first["deterministic_generation_evidence"]["trajectory_count_target"], 1000)
        self.assertEqual(first["deterministic_generation_evidence"]["trajectories_per_release_cell"], 100)
        self.assertEqual(first["deterministic_generation_evidence"]["policy_block_scenario_count"], 3)
        self.assertEqual(first["deterministic_generation_evidence"]["scenario_table_row_count"], 1)
        self.assertEqual(
            first["deterministic_generation_evidence"]["scenario_table_row_ids"],
            ["tschamut_public_block_observed_rows"],
        )
        self.assertEqual(
            first["deterministic_generation_evidence"]["policy_block_scenario_ids"],
            [
                "tschamut_public_block_small",
                "tschamut_public_block_medium",
                "tschamut_public_block_large",
            ],
        )
        self.assertIn("validation/results/", first["ignored_output_roots"])
        self.assertIn("hazard/results/", first["ignored_output_roots"])
        self.assertEqual(
            first["planned_case_output_roots"],
            [
                "validation/private/tschamut_public_pilot/balfrin_single_release_zone_v1",
                "hazard/results/tschamut_public_pilot/balfrin_single_release_zone_v1",
            ],
        )
        self.assertEqual(
            first["blocked_case_execution_template"]["status"],
            "template_only",
        )
        self.assertIn("dry-run only", first["blocked_case_execution_template"]["blocked_reason"])
        self.assertIn("validate --case", first["blocked_case_execution_template"]["command"])

    def test_text_output_is_stable(self) -> None:
        report = planner.build_report()
        text = planner.render_text_report(report)
        self.assertEqual(text, planner.render_text_report(report))
        self.assertIn("Balfrin Single-Release-Zone Case Plan Dry Run", text)
        self.assertIn("Validation output mode: `rebuildable_reduced_output`", text)
        self.assertIn("Block scenario count: `3`", text)
        self.assertIn("Blocked Execution Template", text)

    def test_command_plan_includes_the_dry_run_helper(self) -> None:
        report = command_plan.build_report("tschamut_same_scale", command_plan.DEFAULT_SECOND_SITE_CONFIG)
        commands = report["commands"]
        matching = [command for command in commands if command["id"] == "tschamut_balfrin_single_release_zone_case_plan_dry_run"]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["group"], "balfrin_single_release_zone_plan")
        self.assertTrue(matching[0]["read_only"])
        self.assertFalse(matching[0]["may_produce_ignored_outputs"])

    def test_json_output_smoke(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = planner.main(["--format", "json"])

        self.assertEqual(exit_code, 0)
        json.loads(buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
