from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts.lib import command_plan_contract as COMMAND_PLAN


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_multi_release_zone_demo_handoff.py"
SPEC = importlib.util.spec_from_file_location("generate_balfrin_multi_release_zone_demo_handoff", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinMultiReleaseZoneDemoHandoffTests(unittest.TestCase):
    def test_package_report_is_deterministic_and_records_measured_constraints(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"

            first = MODULE.build_report(artifact_dir=artifact_dir)
            second = MODULE.build_report(artifact_dir=artifact_dir)

            command_plan = json.loads(Path(first["command_plan_path"]).read_text(encoding="utf-8"))
            package = json.loads(Path(first["package_json_path"]).read_text(encoding="utf-8"))
            sbatch_script = Path(first["sbatch_script_path"]).read_text(encoding="utf-8")
            pressure_report_path = Path(first["multi_zone_pressure"]["pressure_artifact_dir"]) / (
                "multi_zone_reducer_pressure_probe_v1.json"
            )
            pressure_report = json.loads(pressure_report_path.read_text(encoding="utf-8"))

            self.assertTrue((artifact_dir / "logs").exists())
            self.assertTrue(Path(first["command_plan_path"]).exists())
            self.assertTrue(Path(first["sbatch_script_path"]).exists())
            self.assertTrue(Path(first["package_json_path"]).exists())
            self.assertTrue(Path(first["package_md_path"]).exists())
            self.assertTrue(Path(first["candidate_output_root"]).exists())
            self.assertTrue(Path(first["target_area_output_root"]).exists())
            self.assertTrue(Path(first["multi_zone_pressure"]["pressure_artifact_dir"]).exists())
            self.assertTrue(pressure_report_path.exists())
            self.assertEqual(pressure_report["probe_status"], "measured_scratch_root")

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_multi_release_zone_demo_package_v1")
        self.assertEqual(first["package_status"], "mixed_provenance")
        self.assertEqual(first["package_constraint_status"], "blocked")
        self.assertEqual(first["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertEqual(first["authorization_classification"], "blocked_pending_authorization")
        self.assertTrue(first["live_execution_requires_new_human_authorization"])
        self.assertEqual(first["output_profile_policy"]["classification"], "blocked_unscalable_default")
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
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["simultaneous_release_zone_batch_max"], 8)
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["reducer_chunk_count_max"], 4)
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["reducer_worker_count_max"], 2)
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["manifest_size_bytes_max"], 21312)
        self.assertEqual(first["constraint_pressure"]["status"], "blocked")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][0]["status"], "acceptable")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][1]["status"], "acceptable")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][2]["status"], "warning")
        self.assertEqual(first["constraint_pressure"]["requested_constraint_status"], "warning")
        self.assertIn("handoff output-budget projection blocked", first["constraint_pressure"]["summary"])
        output_budget_projection = first["handoff_output_budget_projection"]
        self.assertEqual(output_budget_projection["status"], "blocked")
        self.assertEqual(output_budget_projection["gate_status"], "blocked_fixture_backed")
        self.assertEqual(output_budget_projection["projection_provenance"], "handoff_command_plan")
        self.assertEqual(output_budget_projection["release_zone_count"], 12)
        self.assertEqual(output_budget_projection["reducer_chunk_count"], 4)
        self.assertEqual(output_budget_projection["reducer_worker_count"], 2)
        self.assertEqual(output_budget_projection["primary_output_file_count"], 36)
        self.assertEqual(output_budget_projection["sidecar_file_count"], 21)
        self.assertEqual(output_budget_projection["reducer_manifest_file_count"], 4)
        self.assertGreater(output_budget_projection["primary_output_byte_count"], 0)
        self.assertGreater(output_budget_projection["sidecar_byte_count"], 0)
        self.assertGreater(output_budget_projection["reducer_manifest_bytes"], 0)
        self.assertGreater(output_budget_projection["manifest_size_bytes"], 0)
        self.assertEqual(output_budget_projection["first_bottleneck_labels"]["first_blocked"], "manifest_size_bytes")
        self.assertEqual(output_budget_projection["budget_recheck"]["status"], "blocked_budget_reduction_needed")
        self.assertIn("manifest_size_bytes", output_budget_projection["budget_recheck"]["reason"])
        self.assertEqual(
            set(output_budget_projection["replay_critical_field_inventory"]),
            {"command_plan", "projection", "thresholds", "constraints", "smallest_run"},
        )
        self.assertIn(
            "command_plan.commands[id=multi_zone_reducer_pressure_summary].command",
            output_budget_projection["replay_critical_field_inventory"]["command_plan"],
        )
        self.assertIn(
            "constraint_pressure.measured_constraints.manifest_size_bytes_max",
            output_budget_projection["replay_critical_field_inventory"]["constraints"],
        )
        self.assertIn("manifest_size_bytes", [check["metric"] for check in output_budget_projection["budget_checks"]])
        self.assertIn(
            "trajectory_csv",
            [check["kind"] for check in output_budget_projection["family_count_checks"]],
        )
        self.assertEqual(
            first["constraint_pressure"]["handoff_output_budget_projection"]["first_bottleneck_labels"][
                "first_blocked"
            ],
            "manifest_size_bytes",
        )
        self.assertEqual(
            first["constraint_pressure"]["constraint_source"]["source_document"],
            "docs/multi_zone_reducer_pressure_probe.md",
        )
        self.assertEqual(first["command_plan"]["output_profile_policy"]["classification"], "blocked_unscalable_default")
        self.assertEqual(first["uncertainty_post_processing"]["status"], "planned")
        self.assertEqual(first["uncertainty_post_processing"]["post_run_interpretation_gate_status"], "not_run")
        smallest_run = first["follow_up_recommendation"]["minimum_measured_multi_zone_run"]
        self.assertEqual(smallest_run["output_profile_policy"]["classification"], "scalable_default")
        self.assertEqual(smallest_run["release_zone_count"], 2)
        self.assertEqual(smallest_run["scenario_count"], 2)
        self.assertEqual(smallest_run["trajectory_count_target"], 1000)
        self.assertEqual(smallest_run["release_cell_count"], 10)
        self.assertEqual(smallest_run["seed_policy"]["seed"], 34014)
        self.assertEqual(smallest_run["seed_policy"]["mode"], "deterministic_grid")
        self.assertEqual(smallest_run["estimated_runtime_seconds"], 0.498)
        self.assertEqual(smallest_run["estimated_storage_bytes"], 5318)
        self.assertEqual(smallest_run["estimated_file_count"], 10)
        self.assertEqual(smallest_run["estimated_manifest_pressure_bytes"], 3552)
        self.assertEqual(first["authorization_review_command"], smallest_run["authorization_review_command"])
        self.assertEqual(first["authorization_submit_command"], smallest_run["authorization_submit_command"])
        self.assertIn("candidate_stability_sweep", [command["id"] for command in command_plan["commands"]])
        self.assertIn("target_area_handoff_bundle", [command["id"] for command in command_plan["commands"]])
        self.assertIn("multi_zone_reducer_pressure_summary", [command["id"] for command in command_plan["commands"]])
        self.assertIn("authorization_review_command", [command["id"] for command in command_plan["commands"]])
        self.assertIn("scientific_delta_report", [command["id"] for command in command_plan["commands"]])
        self.assertIn("package_materialization", [command["id"] for command in command_plan["commands"]])
        authorization_review_command = next(
            command["command"] for command in command_plan["commands"] if command["id"] == "authorization_review_command"
        )
        pressure_command = next(
            command["command"] for command in command_plan["commands"] if command["id"] == "multi_zone_reducer_pressure_summary"
        )
        self.assertIn("--release-zone-count 12", pressure_command)
        self.assertIn("--reducer-workers 2", pressure_command)
        self.assertIn("--reducer-chunk-count 4", pressure_command)
        self.assertIn("--output-family-mix", pressure_command)
        self.assertIn("scripts/submit_balfrin_probe.py", authorization_review_command)
        self.assertIn("--generate-only", authorization_review_command)
        self.assertIn("generate_balfrin_multi_release_zone_demo_handoff.py", command_plan["commands"][-1]["command"])
        self.assertEqual(command_plan["command_ids"], COMMAND_PLAN.command_ids(command_plan["commands"]))
        self.assertEqual(command_plan["command_descriptions"], COMMAND_PLAN.command_descriptions(command_plan["commands"]))
        self.assertEqual(command_plan["blocked_template_commands"], COMMAND_PLAN.blocked_command_ids(command_plan["commands"]))
        for group in command_plan["command_groups"]:
            self.assertEqual(set(group), {"id", "description", "command_ids", "status"})
        for command in command_plan["commands"]:
            self.assertIn("id", command)
            self.assertIn("command", command)
            self.assertIn("expected_inputs", command)
            self.assertIn("expected_outputs", command)
            self.assertIn("read_only", command)
            self.assertIn("may_produce_ignored_outputs", command)
            self.assertIn("ignored_output_paths", command)
            self.assertIn("blocked_reason", command)
            self.assertIsInstance(command["expected_inputs"], list)
            self.assertIsInstance(command["expected_outputs"], list)
            self.assertIsInstance(command["ignored_output_paths"], list)
            self.assertIsInstance(command["read_only"], bool)
            self.assertIsInstance(command["may_produce_ignored_outputs"], bool)
        self.assertIn("Live execution requires new human authorization", sbatch_script)
        self.assertIn("Blocked classification: blocked_pending_authorization", sbatch_script)
        self.assertIn("Later review command:", sbatch_script)
        self.assertIn("--authorized-submit", smallest_run["authorization_submit_command"])
        self.assertIn("--authorization-record", smallest_run["authorization_submit_command"])
        self.assertIn("balfrin_multi_zone_live_authorization_record_v1.yaml", smallest_run["authorization_submit_command"])
        self.assertIn("Deterministic merge order: sorted_chunk_id", sbatch_script)
        self.assertIn("Restart/replay checkpoints:", sbatch_script)
        self.assertIn("summarize_multi_zone_reducer_pressure.py", sbatch_script)
        rendered = MODULE.render_text_report(package)
        self.assertIn("Balfrin Multi-Release-Zone Demo Package", rendered)
        self.assertIn("## Smallest Run Estimates", rendered)
        self.assertIn("Blocked classification: `blocked_pending_authorization`", rendered)
        self.assertEqual(package["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertEqual(package["authorization_classification"], "blocked_pending_authorization")
        self.assertEqual(package["constraint_pressure"]["status"], "blocked")
        self.assertEqual(smallest_run["trajectory_workers"], 2)
        self.assertEqual(smallest_run["reducer_workers"], 2)
        self.assertEqual(Path(smallest_run["output_roots"]["artifact_dir"]), artifact_dir.resolve())
        self.assertIn("preservation_gate_checklist", smallest_run)
        self.assertEqual(first["deterministic_scenarios"]["command_manifest"]["status"], "planned")
        self.assertEqual(first["deterministic_scenarios"]["template_only_command_ids"], ["target_area_handoff_bundle"])

    def test_handoff_budget_projection_consumes_shared_command_plan_contract_without_mutating_semantics(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            call_count = 0
            original_build_command_record = MODULE.COMMAND_PLAN.build_command_record

            def tracking_build_command_record(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return original_build_command_record(*args, **kwargs)

            with patch.object(MODULE.COMMAND_PLAN, "build_command_record", side_effect=tracking_build_command_record):
                report = MODULE.build_report(artifact_dir=artifact_dir)

            self.assertGreater(call_count, 0)
            command_plan = json.loads(Path(report["command_plan_path"]).read_text(encoding="utf-8"))
            command_plan_snapshot = json.loads(json.dumps(command_plan, sort_keys=True))
            projection = MODULE.build_handoff_output_budget_projection(
                command_plan=command_plan,
                pressure_artifact_dir=Path(report["multi_zone_pressure"]["pressure_artifact_dir"]),
            )

        self.assertEqual(command_plan, command_plan_snapshot)
        self.assertEqual(projection["budget_recheck"]["status"], "blocked_budget_reduction_needed")
        self.assertIn(
            "command_plan.commands[id=multi_zone_reducer_pressure_summary].command",
            projection["replay_critical_field_inventory"]["command_plan"],
        )
        self.assertIn(
            "constraint_pressure.measured_constraints.reducer_worker_count_max",
            projection["replay_critical_field_inventory"]["constraints"],
        )

    def test_constraint_pressure_classification_covers_acceptable_warning_and_blocked_cases(self) -> None:
        pressure_report = {
            "status": "measured_scratch_root",
            "constraint_source": {
                "source_document": "docs/multi_zone_reducer_pressure_probe.md",
                "source_script": "scripts/summarize_multi_zone_reducer_pressure.py",
            },
            "measured_reducer_constraints": {
                "simultaneous_release_zone_batch_max": 8,
                "reducer_chunk_count_max": 4,
                "reducer_worker_count_max": 2,
                "manifest_size_bytes_max": 20101,
                "root_file_count_max": 66,
                "output_file_count_max": 62,
            },
        }

        acceptable = MODULE.build_constraint_pressure_report(
            pressure_report=pressure_report,
            requested_release_zone_batch_size=2,
            requested_reducer_chunk_count=2,
            requested_reducer_worker_count=1,
        )
        warning = MODULE.build_constraint_pressure_report(
            pressure_report=pressure_report,
            requested_release_zone_batch_size=8,
            requested_reducer_chunk_count=2,
            requested_reducer_worker_count=1,
        )
        blocked = MODULE.build_constraint_pressure_report(
            pressure_report=pressure_report,
            requested_release_zone_batch_size=9,
            requested_reducer_chunk_count=5,
            requested_reducer_worker_count=3,
        )

        self.assertEqual(acceptable["status"], "acceptable")
        self.assertEqual(acceptable["constraint_checks"][0]["status"], "acceptable")
        self.assertEqual(acceptable["constraint_checks"][1]["status"], "acceptable")
        self.assertEqual(acceptable["constraint_checks"][2]["status"], "acceptable")
        self.assertIn("stay below measured reducer constraints", acceptable["summary"])

        self.assertEqual(warning["status"], "warning")
        self.assertEqual(warning["constraint_checks"][0]["status"], "warning")
        self.assertEqual(warning["constraint_checks"][1]["status"], "acceptable")
        self.assertEqual(warning["constraint_checks"][2]["status"], "acceptable")
        self.assertIn("warning:", warning["summary"])

        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["constraint_checks"][0]["status"], "blocked")
        self.assertEqual(blocked["constraint_checks"][1]["status"], "blocked")
        self.assertEqual(blocked["constraint_checks"][2]["status"], "blocked")
        self.assertIn("blocked:", blocked["summary"])

    def test_json_cli_emits_a_blocked_package_for_oversized_requests(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--artifact-dir",
                        str(artifact_dir),
                        "--requested-release-zone-batch-size",
                        "9",
                        "--requested-reducer-chunk-count",
                        "5",
                        "--requested-reducer-worker-count",
                        "3",
                        "--format",
                        "json",
                    ]
                )

        self.assertEqual(exit_code, 2)
        report = json.loads(buffer.getvalue())
        self.assertEqual(report["package_constraint_status"], "blocked")
        self.assertEqual(report["constraint_pressure"]["status"], "blocked")
        self.assertTrue(any(check["status"] == "blocked" for check in report["constraint_pressure"]["constraint_checks"]))
        self.assertEqual(report["submission_classification"], "blocked_pending_new_human_authorization")

    def test_missing_required_inputs_fail_closed_with_a_blocked_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            missing_contract = Path(tmpdir) / "missing_target_area_contract.yaml"

            with patch.object(MODULE, "DEFAULT_TARGET_AREA_CONTRACT", missing_contract):
                report = MODULE.build_report(artifact_dir=artifact_dir)

        self.assertEqual(report["package_status"], "blocked_missing_inputs")
        self.assertEqual(report["authorization_classification"], "blocked_missing_inputs")
        self.assertIn("missing_target_area_contract.yaml", " ".join(report["missing_inputs"]))
        self.assertIn("review command", MODULE.render_text_report(report).lower())
        self.assertEqual(report["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["release_zone_count"], 2)
        self.assertEqual(
            report["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["authorization_review_command"],
            report["authorization_review_command"],
        )


if __name__ == "__main__":
    unittest.main()
