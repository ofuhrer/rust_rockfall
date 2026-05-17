from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_multi_release_zone_demo_handoff.py"
SPEC = importlib.util.spec_from_file_location("generate_balfrin_multi_release_zone_demo_handoff", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinMultiReleaseZoneDemoHandoffTests(unittest.TestCase):
    def test_package_report_is_deterministic_and_writes_scratch_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"

            first = MODULE.build_report(artifact_dir=artifact_dir)
            second = MODULE.build_report(artifact_dir=artifact_dir)

            command_plan = json.loads(Path(first["command_plan_path"]).read_text(encoding="utf-8"))
            package = json.loads(Path(first["package_json_path"]).read_text(encoding="utf-8"))
            sbatch_script = Path(first["sbatch_script_path"]).read_text(encoding="utf-8")
            target_area_bundle_path = (
                Path(first["target_area_output_root"]) / "tschamut_public_balfrin_target_area_demo_bundle_report.json"
            )

            self.assertTrue((artifact_dir / "logs").exists())
            self.assertTrue(Path(first["command_plan_path"]).exists())
            self.assertTrue(Path(first["sbatch_script_path"]).exists())
            self.assertTrue(Path(first["package_json_path"]).exists())
            self.assertTrue(Path(first["package_md_path"]).exists())
            self.assertTrue(Path(first["candidate_output_root"]).exists())
            self.assertTrue(Path(first["target_area_output_root"]).exists())
            self.assertFalse(target_area_bundle_path.exists())

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_multi_release_zone_demo_package_v1")
        self.assertEqual(first["package_status"], "mixed_provenance")
        self.assertEqual(first["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertTrue(first["live_execution_requires_new_human_authorization"])
        self.assertEqual(first["candidate_release_candidates"]["status"], "ready")
        self.assertEqual(first["candidate_release_candidates"]["multi_zone_stress_test_readiness"]["status"], "ready")
        self.assertEqual(first["deterministic_scenarios"]["status"], "template_only")
        self.assertEqual(first["deterministic_scenarios"]["bundle_runnable_status"], "planned")
        self.assertEqual(first["deterministic_scenarios"]["scenario_generation_handoff"]["status"], "template_only")
        self.assertGreater(first["deterministic_scenarios"]["scenario_table_row_count"], 0)
        self.assertIn(
            "generate_balfrin_target_area_scenario_tables.py",
            first["deterministic_scenarios"]["scenario_generation_command"],
        )
        self.assertEqual(first["deterministic_scenarios"]["gis_scope_summary"]["status"], "template_only")
        self.assertTrue(first["deterministic_scenarios"]["gis_scope_summary"]["no_hazard_layers_generated"])
        self.assertEqual(first["pressure_checkpoints"]["output_pressure"]["validation_output_blocker_status"], "blocker_retained")
        self.assertTrue(first["pressure_checkpoints"]["restartability"]["single_job_sufficient_for_next_step"])
        self.assertEqual(first["pressure_checkpoints"]["reducer_chunk_pressure"]["status"], "measured_existing_artifacts")
        self.assertEqual(first["uncertainty_post_processing"]["status"], "planned")
        self.assertEqual(first["uncertainty_post_processing"]["post_run_interpretation_gate_status"], "not_run")
        self.assertEqual(first["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["release_zone_count"], 2)
        self.assertIn("candidate_stability_sweep", [command["id"] for command in command_plan["commands"]])
        self.assertIn("target_area_handoff_bundle", [command["id"] for command in command_plan["commands"]])
        self.assertIn("scientific_delta_report", [command["id"] for command in command_plan["commands"]])
        self.assertIn("package_materialization", [command["id"] for command in command_plan["commands"]])
        self.assertIn("generate_balfrin_multi_release_zone_demo_handoff.py", command_plan["commands"][-1]["command"])
        self.assertIn("Live execution requires new human authorization", sbatch_script)
        self.assertIn("Balfrin Multi-Release-Zone Demo Package", MODULE.render_text_report(package))
        self.assertEqual(package["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertEqual(package["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["trajectory_workers"], 2)
        self.assertEqual(package["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["reducer_workers"], 2)
        self.assertEqual(first["deterministic_scenarios"]["command_manifest"]["status"], "planned")
        self.assertEqual(first["deterministic_scenarios"]["template_only_command_ids"], ["target_area_handoff_bundle"])

    def test_json_cli_emits_a_valid_package_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--artifact-dir", str(artifact_dir), "--format", "json"])

        self.assertEqual(exit_code, 0)
        json.loads(buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
