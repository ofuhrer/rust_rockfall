from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.lib import command_plan_contract as COMMAND_PLAN


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_multi_release_zone_demo_handoff.py"
SPEC = importlib.util.spec_from_file_location("generate_balfrin_multi_release_zone_demo_handoff", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PRESSURE_SCRIPT_PATH = ROOT / "scripts" / "summarize_multi_zone_reducer_pressure.py"
PRESSURE_SPEC = importlib.util.spec_from_file_location("summarize_multi_zone_reducer_pressure", PRESSURE_SCRIPT_PATH)
assert PRESSURE_SPEC is not None
PRESSURE_MODULE = importlib.util.module_from_spec(PRESSURE_SPEC)
assert PRESSURE_SPEC.loader is not None
sys.modules["summarize_multi_zone_reducer_pressure"] = PRESSURE_MODULE
PRESSURE_SPEC.loader.exec_module(PRESSURE_MODULE)


class BalfrinMultiReleaseZoneDemoHandoffTests(unittest.TestCase):
    def test_package_report_is_deterministic_and_records_measured_constraints(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            pressure_probe_root = Path(tmpdir) / "multi_zone_pressure_probe"

            first = MODULE.build_report(artifact_dir=artifact_dir, pressure_probe_root=pressure_probe_root)
            second = MODULE.build_report(artifact_dir=artifact_dir, pressure_probe_root=pressure_probe_root)

            command_plan = json.loads(Path(first["command_plan_path"]).read_text(encoding="utf-8"))
            package = json.loads(Path(first["package_json_path"]).read_text(encoding="utf-8"))
            authorization_record_path = artifact_dir / "balfrin_multi_zone_live_authorization_record_v1.yaml"
            authorization_record = yaml.safe_load(authorization_record_path.read_text(encoding="utf-8"))
            package_sha256 = MODULE.file_sha256(Path(first["package_json_path"]))
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
            self.assertTrue(authorization_record_path.exists())
            self.assertTrue(Path(first["candidate_output_root"]).exists())
            self.assertTrue(Path(first["target_area_output_root"]).exists())
            self.assertTrue(Path(first["multi_zone_pressure"]["pressure_artifact_dir"]).exists())
            self.assertTrue(pressure_report_path.exists())
            self.assertEqual(pressure_report["probe_status"], "measured_scratch_root")

        self.assertEqual(first["schema_version"], second["schema_version"])
        self.assertEqual(first["package_status"], second["package_status"])
        self.assertEqual(first["package_constraint_status"], second["package_constraint_status"])
        self.assertEqual(first["submission_classification"], second["submission_classification"])
        self.assertEqual(first["handoff_output_budget_projection"]["status"], second["handoff_output_budget_projection"]["status"])
        self.assertEqual(
            first["handoff_output_budget_projection"]["budget_acceptance_validation"]["status"],
            second["handoff_output_budget_projection"]["budget_acceptance_validation"]["status"],
        )
        self.assertEqual(first["manifest_pruning"]["status"], second["manifest_pruning"]["status"])
        self.assertEqual(first["schema_version"], "balfrin_multi_release_zone_demo_package_v1")
        self.assertEqual(authorization_record["authorized_task"], "TB-371")
        self.assertEqual(authorization_record["authorization_status"], "authorized_for_one_bounded_probe")
        self.assertEqual(authorization_record["reviewed_handoff_package_path"], str(Path(first["package_json_path"]).resolve()))
        self.assertEqual(authorization_record["reviewed_handoff_package_sha256"], package_sha256)
        self.assertIn("/scratch/mch/olifu/rust_rockfall/probes", authorization_record["run_root"])
        self.assertEqual(first["package_status"], "mixed_provenance")
        self.assertEqual(first["package_constraint_status"], "warning")
        self.assertEqual(first["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertEqual(first["authorization_classification"], "blocked_pending_authorization")
        self.assertTrue(first["live_execution_requires_new_human_authorization"])
        self.assertEqual(first["output_profile_policy"]["classification"], "scalable_default")
        self.assertEqual(
            first["output_profile_policy_provenance"]["legacy_current_target_gate_profile"]["classification"],
            "blocked_unscalable_default",
        )
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
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["reducer_chunk_count_max"], 2)
        self.assertEqual(first["multi_zone_pressure"]["measured_reducer_constraints"]["reducer_worker_count_max"], 2)
        self.assertEqual(
            first["multi_zone_pressure"]["measured_reducer_constraints"]["manifest_size_bytes_max"],
            pressure_report["measured_reducer_constraints"]["manifest_size_bytes_max"],
        )
        self.assertGreaterEqual(
            first["multi_zone_pressure"]["measured_reducer_constraints"]["manifest_size_bytes_max"],
            first["multi_zone_pressure"]["manifest_size_bytes"],
        )
        self.assertEqual(first["constraint_pressure"]["status"], "warning")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][0]["status"], "acceptable")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][1]["status"], "warning")
        self.assertEqual(first["constraint_pressure"]["constraint_checks"][2]["status"], "warning")
        self.assertEqual(first["constraint_pressure"]["requested_constraint_status"], "warning")
        self.assertNotIn("handoff output-budget projection blocked", first["constraint_pressure"]["summary"])
        self.assertIn("requested reducer_worker_count=2 reaches measured max 2", first["constraint_pressure"]["summary"])
        output_budget_projection = first["handoff_output_budget_projection"]
        self.assertEqual(output_budget_projection["status"], "acceptable")
        self.assertEqual(output_budget_projection["gate_status"], "fixture_backed_ready")
        self.assertEqual(output_budget_projection["projection_provenance"], "handoff_command_plan")
        self.assertEqual(output_budget_projection["projection_mode"], "full")
        self.assertEqual(output_budget_projection["release_zone_count"], 2)
        self.assertEqual(output_budget_projection["reducer_chunk_count"], 2)
        self.assertEqual(output_budget_projection["reducer_worker_count"], 2)
        self.assertEqual(output_budget_projection["primary_output_file_count"], 6)
        self.assertEqual(output_budget_projection["sidecar_file_count"], 9)
        self.assertEqual(output_budget_projection["reducer_manifest_file_count"], 0)
        self.assertEqual(output_budget_projection["reducer_manifest_bytes"], 0)
        self.assertEqual(output_budget_projection["output_file_count"], 17)
        self.assertEqual(
            output_budget_projection["replay_critical_retained_output_families"],
            ["trajectory_csv", "deposition_csv", "impact_events_csv", "trajectory_merge_state", "reducer_merge_state"],
        )
        self.assertGreater(output_budget_projection["primary_output_byte_count"], 0)
        self.assertGreater(output_budget_projection["sidecar_byte_count"], 0)
        self.assertGreater(output_budget_projection["manifest_size_bytes"], 0)
        self.assertIsNone(output_budget_projection["first_bottleneck_labels"]["first_blocked"])
        self.assertEqual(output_budget_projection["first_bottleneck_labels"]["first_relevant"], "ready")
        self.assertEqual(output_budget_projection["budget_recheck"]["status"], "budget_passes_no_reduction_needed")
        self.assertIn("accepted by smallest_live_two_zone_probe thresholds", output_budget_projection["budget_recheck"]["reason"])
        self.assertEqual(first["output_budget_acceptance_thresholds"]["schema_version"], "balfrin_multi_zone_output_budget_acceptance_v1")
        self.assertIn("smallest_live_two_zone_probe", first["output_budget_acceptance_thresholds"]["profiles"])
        self.assertIn("next_larger_four_zone_review_only_probe", first["output_budget_acceptance_thresholds"]["profiles"])
        self.assertEqual(output_budget_projection["budget_acceptance_validation"]["status"], "accepted")
        self.assertEqual(
            output_budget_projection["budget_acceptance_validation"]["threshold_profile_id"],
            "smallest_live_two_zone_probe",
        )
        self.assertEqual(output_budget_projection["budget_acceptance_validation"]["failures"], [])
        no_submit_contract = first["no_submit_handoff_contract"]
        self.assertEqual(no_submit_contract["schema_version"], "balfrin_no_submit_handoff_contract_v1")
        self.assertEqual(no_submit_contract["status"], "ready_for_review")
        self.assertIsNone(no_submit_contract["first_blocker"])
        self.assertFalse(no_submit_contract["submit_gate_explicitly_invoked"])
        self.assertTrue(no_submit_contract["command_contains_generate_only_flag"])
        self.assertTrue(no_submit_contract["command_contains_authorized_submit_flag"])
        self.assertFalse(no_submit_contract["review_command_contains_authorized_submit_flag"])
        self.assertIn("scripts/submit_balfrin_probe.py", no_submit_contract["exact_review_command"])
        self.assertIn("--generate-only", no_submit_contract["exact_review_command"])
        self.assertIn("--authorized-submit", no_submit_contract["exact_later_submit_gate_command"])
        self.assertFalse(no_submit_contract["no_submit_semantics"]["sbatch_attempted"])
        self.assertFalse(no_submit_contract["no_submit_semantics"]["submit_command_executed"])
        self.assertFalse(no_submit_contract["no_submit_semantics"]["balfrin_job_submitted"])
        self.assertTrue(no_submit_contract["no_submit_semantics"]["package_generation_only"])
        self.assertTrue(no_submit_contract["no_submit_semantics"]["requires_explicit_submit_gate"])
        self.assertEqual(no_submit_contract["output_mode"], "rebuildable_reduced_output")
        self.assertEqual(
            no_submit_contract["reduced_output_defaults"],
            {"conditional_curve_export": "summary-only", "grid_csv_export": "none", "no_plots": True},
        )
        self.assertEqual(no_submit_contract["reducer_limits"]["requested_release_zone_batch_size"], 2)
        self.assertEqual(no_submit_contract["reducer_limits"]["requested_reducer_chunk_count"], 2)
        self.assertEqual(no_submit_contract["reducer_limits"]["requested_reducer_worker_count"], 2)
        self.assertEqual(no_submit_contract["reducer_limits"]["measured_reducer_chunk_count_max"], 2)
        self.assertEqual(no_submit_contract["scenario_limits"]["release_zone_count"], 2)
        self.assertEqual(no_submit_contract["scenario_limits"]["review_release_zone_count"], 4)
        self.assertFalse(no_submit_contract["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(no_submit_contract["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(no_submit_contract["claim_boundaries"]["distributed_execution_authorized"])
        self.assertIn(first["artifact_dir"], no_submit_contract["ignored_output_roots"])
        self.assertEqual(first["output_budget_acceptance_validation"]["status"], "accepted")
        smallest_thresholds = first["output_budget_acceptance_thresholds"]["profiles"]["smallest_live_two_zone_probe"]
        self.assertEqual(smallest_thresholds["max_manifest_size_bytes"], 18000)
        self.assertEqual(smallest_thresholds["max_total_output_files"], 20)
        self.assertEqual(smallest_thresholds["max_sidecar_files"], 11)
        self.assertEqual(smallest_thresholds["max_reducer_chunks"], 2)
        self.assertEqual(
            smallest_thresholds["required_replay_critical_families"],
            ["trajectory_csv", "deposition_csv", "impact_events_csv", "trajectory_merge_state", "reducer_merge_state"],
        )
        self.assertEqual(
            smallest_thresholds["required_package_hashes"],
            ["probe_manifest_sha256", "command_plan_sha256", "output_manifest_sha256"],
        )
        self.assertEqual(
            set(output_budget_projection["replay_critical_field_inventory"]),
            {
                "command_plan",
                "projection",
                "thresholds",
                "constraints",
                "scenario_pressure",
                "smallest_run",
                "manifest_pruning",
            },
        )
        self.assertEqual(
            output_budget_projection["replay_critical_field_inventory"]["command_plan"]["prefix"],
            "command_plan.commands[id=multi_zone_reducer_pressure_summary].",
        )
        self.assertIn("command", output_budget_projection["replay_critical_field_inventory"]["command_plan"]["fields"])
        self.assertEqual(
            output_budget_projection["replay_critical_field_inventory"]["projection"]["prefix"],
            "handoff_output_budget_projection.",
        )
        self.assertIn("manifest_size_bytes", output_budget_projection["replay_critical_field_inventory"]["projection"]["fields"])
        self.assertIn(
            "measured_constraints.manifest_size_bytes_max",
            output_budget_projection["replay_critical_field_inventory"]["constraints"]["fields"],
        )
        self.assertEqual(
            output_budget_projection["replay_critical_field_inventory"]["manifest_pruning"]["prefix"],
            "manifest_pruning.",
        )
        self.assertIn("exact_blocking_fields", output_budget_projection["replay_critical_field_inventory"]["manifest_pruning"]["fields"])
        self.assertIn("manifest_size_bytes", [check["metric"] for check in output_budget_projection["budget_checks"]])
        self.assertIn(
            "trajectory_csv",
            [check["kind"] for check in output_budget_projection["family_count_checks"]],
        )
        self.assertEqual(
            first["constraint_pressure"]["handoff_output_budget_projection"]["first_bottleneck_labels"][
                "first_relevant"
            ],
            "ready",
        )
        self.assertEqual(
            first["constraint_pressure"]["constraint_source"]["source_document"],
            "docs/multi_zone_reducer_pressure_probe.md",
        )
        manifest_pruning = first["manifest_pruning"]
        self.assertEqual(manifest_pruning["status"], "budget_passes_no_reduction_needed")
        self.assertEqual(manifest_pruning["before"]["manifest_size_bytes"], output_budget_projection["manifest_size_bytes"])
        self.assertEqual(manifest_pruning["after"]["manifest_size_bytes"], output_budget_projection["manifest_size_bytes"])
        self.assertLess(
            manifest_pruning["after"]["manifest_size_bytes"],
            first["multi_zone_pressure"]["measured_reducer_constraints"]["manifest_size_bytes_max"],
        )
        self.assertEqual(manifest_pruning["before"]["sidecar_file_count"], 9)
        self.assertEqual(manifest_pruning["after"]["sidecar_file_count"], 9)
        self.assertEqual(manifest_pruning["before"]["output_file_count"], 17)
        self.assertEqual(manifest_pruning["after"]["output_file_count"], 17)
        self.assertEqual(manifest_pruning["before"]["reducer_manifest_file_count"], 0)
        self.assertEqual(manifest_pruning["after"]["reducer_manifest_file_count"], 0)
        self.assertEqual(manifest_pruning["before"]["reducer_manifest_bytes"], 0)
        self.assertEqual(manifest_pruning["after"]["reducer_manifest_bytes"], 0)
        self.assertNotIn("exact_blocking_fields", manifest_pruning)
        self.assertEqual(
            manifest_pruning["replay_critical_output_families"],
            ["trajectory_csv", "deposition_csv", "impact_events_csv", "trajectory_merge_state", "reducer_merge_state"],
        )
        self.assertEqual(
            manifest_pruning["replay_critical_contract"]["families"],
            ["trajectory_csv", "deposition_csv", "impact_events_csv", "trajectory_merge_state", "reducer_merge_state"],
        )
        self.assertEqual(
            manifest_pruning["replay_critical_contract"]["merge_order_proof"],
            {"merge_order": "sorted_chunk_id", "merge_order_independent": True, "merge_order_deterministic": True},
        )
        self.assertEqual(
            manifest_pruning["replay_critical_contract"]["output_profile_semantics"]["classification"],
            "scalable_default",
        )
        self.assertIn(
            "minimum_measured_multi_zone_run",
            manifest_pruning["replay_critical_contract"]["output_profile_semantics"]["scalable_policy_labels"],
        )
        self.assertEqual(manifest_pruning["retained_output_families"], list(output_budget_projection["output_family_mix"]))
        self.assertEqual(first["command_plan"]["output_profile_policy"]["classification"], "scalable_default")
        review_package = first["review_only_four_zone_package"]
        self.assertEqual(review_package["readiness_classification"], "ready_for_review")
        self.assertEqual(review_package["output_budget_acceptance_status"], "accepted")
        self.assertEqual(review_package["output_budget_acceptance_threshold_profile_id"], "next_larger_four_zone_review_only_probe")
        self.assertEqual(review_package["release_zone_count"], 4)
        self.assertEqual(review_package["scenario_count"], 4)
        self.assertEqual(review_package["output_profile_policy"]["classification"], "scalable_default")
        self.assertEqual(review_package["reduced_output_defaults"], {
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "no_plots": True,
        })
        self.assertEqual(review_package["manifest_pruning_status"], "budget_passes_no_reduction_needed")
        self.assertEqual(review_package["promotion_status"], "blocked_pending_later_task")
        self.assertEqual(first["review_readiness_classification"], "ready_for_review")
        self.assertIn("four-zone review package is ready for review", first["review_readiness_reason"])
        hazard_package = first["four_zone_hazard_execution_package"]
        self.assertEqual(hazard_package["status"], "ready_for_submit")
        self.assertEqual(hazard_package["readiness_classification"], "ready_for_submit")
        self.assertEqual(hazard_package["decision"], "ready_for_submit")
        self.assertEqual(hazard_package["decision_status"], "ready")
        self.assertTrue(hazard_package["ready_for_submit"])
        self.assertIn("Measured two-zone evidence is present", hazard_package["readiness_reason"])
        self.assertEqual(hazard_package["command_plan"]["command_plan_status"], "ready")
        self.assertEqual(
            hazard_package["command_plan"]["output_profile_policy"]["classification"],
            "scalable_default",
        )
        self.assertGreater(hazard_package["command_plan"]["command_count"], 0)
        self.assertIn("multi_zone_reducer_pressure_summary", hazard_package["command_plan"]["command_ids"])
        self.assertEqual(
            hazard_package["authorization_audit_record"]["authorization_review_command"],
            first["authorization_review_command"],
        )
        self.assertEqual(
            hazard_package["authorization_audit_record"]["authorization_submit_command"],
            first["authorization_submit_command"],
        )
        self.assertEqual(hazard_package["authorization_audit_record"]["status"], "reviewed")
        self.assertEqual(hazard_package["reduced_output_settings"]["conditional_curve_export"], "summary-only")
        self.assertEqual(hazard_package["reduced_output_settings"]["grid_csv_export"], "none")
        self.assertTrue(hazard_package["preservation_instructions"]["checklist"])
        self.assertIn(first["package_json_path"], hazard_package["preservation_instructions"]["do_not_commit_paths"])
        self.assertEqual(
            hazard_package["expected_output_budget"]["threshold_profile_id"],
            "next_larger_four_zone_review_only_probe",
        )
        self.assertEqual(hazard_package["expected_output_budget"]["status"], "accepted")
        self.assertEqual(hazard_package["expected_output_budget"]["validation"]["status"], "accepted")
        self.assertEqual(hazard_package["expected_output_budget"]["projection"]["status"], "acceptable")
        self.assertEqual(hazard_package["expected_output_budget"]["manifest_pruning_status"], "budget_passes_no_reduction_needed")
        self.assertEqual(hazard_package["measured_two_zone_evidence"]["status"], "measured")
        self.assertEqual(
            hazard_package["measured_two_zone_evidence"]["classification"],
            "measured_two_zone_evidence_present",
        )
        self.assertTrue(hazard_package["measured_two_zone_evidence"]["measured_on_balfrin"])
        self.assertEqual(hazard_package["measured_two_zone_evidence"]["source_task"], "TB-368")
        self.assertEqual(
            hazard_package["measured_two_zone_evidence"]["preservation_gate_status"],
            "ready_for_demonstration_evidence",
        )
        self.assertEqual(
            hazard_package["expected_artifact_roots"],
            {
                "artifact_dir": first["artifact_dir"],
                "candidate_output_root": first["candidate_output_root"],
                "target_area_output_root": first["target_area_output_root"],
                "pressure_artifact_dir": first["pressure_artifact_dir"],
                "pressure_probe_root": first["pressure_probe_root"],
            },
        )
        self.assertEqual(first["uncertainty_post_processing"]["status"], "planned")
        self.assertEqual(first["uncertainty_post_processing"]["post_run_interpretation_gate_status"], "not_run")
        smallest_run = first["follow_up_recommendation"]["minimum_measured_multi_zone_run"]
        self.assertEqual(smallest_run["output_profile_policy"]["classification"], "scalable_default")
        self.assertEqual(smallest_run["output_mode"], "rebuildable_reduced_output")
        self.assertEqual(
            smallest_run["bounded_gis_cog_settings"],
            {
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "no_plots": True,
                "export_geotiff": True,
                "pilot_gis_package": True,
                "probability_mode": "sampling_weighted_conditional",
                "normalization_scope": "conditioned_on_filter",
                "trajectory_workers": 2,
                "reducer_workers": 2,
                "manual_gis_qa_status": "not-run",
            },
        )
        self.assertEqual(smallest_run["release_zone_count"], 2)
        self.assertEqual(smallest_run["scenario_count"], 2)
        self.assertEqual(smallest_run["trajectory_count_target"], 1000)
        self.assertEqual(smallest_run["release_cell_count"], 10)
        self.assertEqual(smallest_run["seed_policy"]["seed"], 34014)
        self.assertEqual(smallest_run["seed_policy"]["mode"], "deterministic_grid")
        self.assertEqual(smallest_run["estimated_runtime_seconds"], 0.432)
        self.assertGreater(smallest_run["estimated_storage_bytes"], 0)
        self.assertGreater(smallest_run["estimated_file_count"], 0)
        self.assertGreater(smallest_run["estimated_manifest_pressure_bytes"], 0)
        self.assertLessEqual(
            smallest_run["estimated_manifest_pressure_bytes"],
            first["multi_zone_pressure"]["measured_reducer_constraints"]["manifest_size_bytes_max"],
        )
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
        self.assertIn("--release-zone-count 2", pressure_command)
        self.assertIn("--reducer-workers 2", pressure_command)
        self.assertIn("--reducer-chunk-count 2", pressure_command)
        self.assertIn("--output-family-mix", pressure_command)
        self.assertIn("scripts/submit_balfrin_probe.py", authorization_review_command)
        self.assertIn("validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml", authorization_review_command)
        self.assertNotIn("validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml", authorization_review_command)
        self.assertIn("--generate-only", authorization_review_command)
        self.assertIn("/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo", authorization_review_command)
        self.assertNotIn("--run-root /scratch/rust_rockfall", authorization_review_command)
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
        self.assertIn(
            "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
            smallest_run["authorization_submit_command"],
        )
        self.assertNotIn(
            "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml",
            smallest_run["authorization_submit_command"],
        )
        self.assertIn("--authorization-record", smallest_run["authorization_submit_command"])
        self.assertIn("balfrin_multi_zone_live_authorization_record_v1.yaml", smallest_run["authorization_submit_command"])
        self.assertIn("Deterministic merge order: sorted_chunk_id", sbatch_script)
        self.assertIn("Restart/replay checkpoints:", sbatch_script)
        self.assertIn("summarize_multi_zone_reducer_pressure.py", sbatch_script)
        rendered = MODULE.render_text_report(package)
        self.assertIn("Balfrin Multi-Release-Zone Demo Package", rendered)
        self.assertIn("## Four-Zone Review Package", rendered)
        self.assertIn("## Smallest Run Estimates", rendered)
        self.assertIn("Blocked classification: `blocked_pending_authorization`", rendered)
        self.assertIn("## Measured Two-Zone Evidence", rendered)
        self.assertIn("ready_for_submit", rendered)
        self.assertIn("## Four-Zone Hazard Execution Package", rendered)
        self.assertEqual(package["submission_classification"], "blocked_pending_new_human_authorization")
        self.assertEqual(package["authorization_classification"], "blocked_pending_authorization")
        self.assertEqual(package["constraint_pressure"]["status"], "warning")
        self.assertEqual(smallest_run["trajectory_workers"], 2)
        self.assertEqual(smallest_run["reducer_workers"], 2)
        self.assertEqual(Path(smallest_run["output_roots"]["artifact_dir"]), artifact_dir.resolve())
        self.assertIn("preservation_gate_checklist", smallest_run)
        self.assertEqual(first["deterministic_scenarios"]["command_manifest"]["status"], "planned")
        self.assertEqual(first["deterministic_scenarios"]["template_only_command_ids"], ["target_area_handoff_bundle"])

    def test_four_zone_live_hazard_decision_falls_back_to_no_go_when_budgets_exceed(self) -> None:
        decision = MODULE.classify_four_zone_hazard_execution_decision(
            measured_two_zone_evidence={
                "status": "measured",
                "classification": "measured_two_zone_evidence_present",
                "decision": "measured",
                "summary": "measured two-zone evidence is present",
            },
            output_budget_validation={
                "status": "blocked_threshold_exceeded",
                "summary": "manifest size exceeded the acceptance threshold",
            },
            constraint_pressure={
                "status": "blocked",
                "summary": "reducer budget exceeded the measured constraint",
            },
            manifest_pruning={
                "status": "blocked_budget_reduction_needed",
                "summary": "manifest pruning still requires reduction",
            },
        )

        self.assertEqual(decision["decision"], "no_go")
        self.assertEqual(decision["decision_status"], "blocked")
        self.assertEqual(decision["classification"], "no_go_output_budget_exceeded")
        self.assertFalse(decision["ready_for_submit"])
        self.assertIn("manifest size exceeded", decision["no_go_reason"])

    def test_compact_manifest_mode_preserves_replay_critical_report_shape(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            full_root = tmp / "full_probe"
            compact_root = tmp / "compact_probe"

            PRESSURE_MODULE.materialize_probe_root(full_root, manifest_mode="full")
            PRESSURE_MODULE.materialize_probe_root(compact_root, manifest_mode="compact")

            full_report = PRESSURE_MODULE.build_report(full_root)
            compact_report = PRESSURE_MODULE.build_report(compact_root)
            compact_manifest = json.loads(
                (compact_root / "output" / "validation_multi_zone_reducer_pressure_manifest.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(compact_manifest["manifest_encoding"]["mode"], "compact_v1")
        self.assertIn("shared_output_family_metadata", compact_manifest["manifest_encoding"])
        self.assertIn("shared_command_plan_fields", compact_manifest["manifest_encoding"])
        self.assertLess(compact_report["manifest_size_bytes"], full_report["manifest_size_bytes"])
        self.assertEqual(compact_report["merge_order"], "sorted_chunk_id")
        self.assertTrue(compact_report["merge_order_independent"])
        self.assertEqual(compact_report["output_family_file_counts"], full_report["output_family_file_counts"])
        self.assertEqual(compact_report["output_family_bytes"], full_report["output_family_bytes"])
        self.assertLessEqual(compact_report["manifest_size_by_path"]["output_manifest"], 11_000)

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
        self.assertEqual(projection["budget_recheck"]["status"], "budget_passes_no_reduction_needed")
        self.assertIn(
            "command",
            projection["replay_critical_field_inventory"]["command_plan"]["fields"],
        )
        self.assertIn(
            "measured_constraints.reducer_worker_count_max",
            projection["replay_critical_field_inventory"]["constraints"]["fields"],
        )

    def test_budget_recheck_reports_no_reduction_needed_when_projection_is_ready(self) -> None:
        ready_projection = {
            "status": "acceptable",
            "gate_status": "fixture_backed_ready",
            "budget_recheck": {"status": "budget_passes_no_reduction_needed", "reason": "current handoff projection stays within the current budget thresholds"},
            "first_bottleneck_labels": {"first_relevant": "ready"},
        }

        recheck = MODULE.build_handoff_budget_recheck(
            handoff_output_budget_projection=ready_projection,
            first_bottleneck_labels={"first_relevant": "ready"},
        )

        self.assertEqual(recheck["status"], "budget_passes_no_reduction_needed")
        self.assertIn("within the current budget thresholds", recheck["reason"])

    def test_budget_acceptance_validator_classifies_compressible_and_replay_critical_failures(self) -> None:
        validation = MODULE.validate_output_budget_acceptance(
            projection={
                "release_zone_count": 2,
                "reducer_chunk_count": 3,
                "manifest_size_bytes": 18001,
                "output_file_count": 21,
                "sidecar_file_count": 12,
                "reducer_manifest_file_count": 2,
                "reducer_manifest_bytes": 401,
                "output_family_file_counts": {"trajectory_csv": 3, "trajectory_chunk_manifest": 3},
                "replay_critical_retained_output_families": ["trajectory_csv", "deposition_csv"],
                "projection_file_hashes": {"probe_manifest_sha256": "a" * 64},
            }
        )

        self.assertEqual(validation["status"], "blocked_threshold_exceeded")
        self.assertEqual(validation["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertIn("manifest_size_bytes", validation["exceeded_thresholds"])
        self.assertTrue(any(failure["compressible"] for failure in validation["failures"]))
        self.assertTrue(any(failure["replay_critical"] for failure in validation["failures"]))
        self.assertIn("required_package_hashes", validation["exceeded_thresholds"])

    def test_budget_acceptance_validator_accepts_sixteen_zone_compact_diagnostic_projection(self) -> None:
        validation = MODULE.validate_output_budget_acceptance(
            projection={
                "release_zone_count": 16,
                "reducer_chunk_count": 2,
                "projection_mode": "compact",
                "manifest_size_bytes": 15_954,
                "output_file_count": 52,
                "sidecar_file_count": 2,
                "reducer_manifest_file_count": 0,
                "reducer_manifest_bytes": 0,
                "estimated_storage_bytes": 23_682,
                "output_family_file_counts": {
                    "trajectory_csv": 16,
                    "deposition_csv": 16,
                    "impact_events_csv": 16,
                    "trajectory_merge_state": 1,
                    "reducer_merge_state": 1,
                },
                "replay_critical_retained_output_families": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
                "projection_file_hashes": {
                    "probe_manifest_sha256": "a" * 64,
                    "command_plan_sha256": "b" * 64,
                    "output_manifest_sha256": "c" * 64,
                },
            }
        )

        self.assertEqual(validation["status"], "accepted")
        self.assertEqual(
            validation["threshold_profile_id"],
            MODULE.DIAGNOSTIC_16_ZONE_BUDGET_PROFILE_ID,
        )
        self.assertEqual(validation["failures"], [])
        self.assertEqual(validation["threshold_profile"]["required_projection_mode"], "compact")
        self.assertEqual(
            validation["threshold_profile"]["required_zero_metrics"],
            ["reducer_manifest_file_count", "reducer_manifest_bytes"],
        )
        self.assertEqual(validation["threshold_profile"]["max_estimated_storage_bytes"], 25_000)

    def test_scenario_pressure_projection_exposes_planning_thresholds(self) -> None:
        pressure_report = {
            "status": "measured_scratch_root",
            "measured_reducer_constraints": {
                "simultaneous_release_zone_batch_max": 100,
                "reducer_chunk_count_max": 4,
                "reducer_worker_count_max": 2,
                "manifest_size_bytes_max": 1,
                "root_file_count_max": 100,
                "output_file_count_max": 100,
            },
            "reducer_wall_time_seconds": 2.59,
            "output_file_count": 48,
            "output_byte_count": 26105,
            "manifest_size_bytes": 18274,
        }
        source_scenario_policy = {
            "block_scenario_policy": {
                "scenarios": [
                    {"block_scenario_id": "block_a"},
                    {"block_scenario_id": "block_b"},
                    {"block_scenario_id": "block_c"},
                ]
            }
        }

        projection = MODULE.build_scenario_pressure_projection(
            pressure_report=pressure_report,
            source_scenario_policy=source_scenario_policy,
            requested_release_zone_batch_size=10,
        )

        self.assertEqual(projection["threshold_profiles"][0]["profile_id"], "planning_case_10_zone")
        self.assertEqual([profile["release_zone_count"] for profile in projection["threshold_profiles"]], [10, 50, 100])
        self.assertEqual(projection["selected_threshold_profile"]["profile_id"], "planning_case_10_zone")
        self.assertEqual(projection["status"], "blocked")
        self.assertEqual(projection["first_bottleneck_labels"]["first_relevant"], "manifest_size_bytes")
        self.assertIn("manifest_size_bytes", projection["summary"])

    def test_scenario_pressure_projection_blocks_over_planning_ceiling(self) -> None:
        pressure_report = {
            "status": "measured_scratch_root",
            "measured_reducer_constraints": {
                "simultaneous_release_zone_batch_max": 100,
                "reducer_chunk_count_max": 4,
                "reducer_worker_count_max": 2,
                "manifest_size_bytes_max": 200000,
                "root_file_count_max": 100,
                "output_file_count_max": 100,
            },
            "reducer_wall_time_seconds": 2.59,
            "output_file_count": 48,
            "output_byte_count": 26105,
            "manifest_size_bytes": 18274,
        }
        source_scenario_policy = {
            "block_scenario_policy": {
                "scenarios": [
                    {"block_scenario_id": "block_a"},
                    {"block_scenario_id": "block_b"},
                ]
            }
        }

        projection = MODULE.build_scenario_pressure_projection(
            pressure_report=pressure_report,
            source_scenario_policy=source_scenario_policy,
            requested_release_zone_batch_size=101,
        )

        self.assertEqual(projection["status"], "blocked")
        self.assertEqual(projection["first_bottleneck_labels"]["first_relevant"], "release_zone_count")
        self.assertIn("planning ceiling", projection["summary"])

    def test_manifest_pruning_refuses_to_drop_replay_critical_fields(self) -> None:
        with self.assertRaises(MODULE.BalfrinMultiReleaseZoneDemoHandoffError):
            MODULE.prune_manifest_output_family_mix(
                tuple(
                    family
                    for family in MODULE.FULL_OUTPUT_FAMILY_MIX
                    if family not in {"trajectory_merge_state"}
                )
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

    def test_sixteen_zone_handoff_is_unblocked_by_accepted_diagnostic_budget(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "tb569_16_zone_handoff"
            pressure_probe_root = Path(tmpdir) / "tb569_16_zone_pressure"

            report = MODULE.build_report(
                artifact_dir=artifact_dir,
                pressure_probe_root=pressure_probe_root,
                requested_release_zone_batch_size=16,
                requested_reducer_chunk_count=2,
                requested_reducer_worker_count=2,
            )

        self.assertEqual(report["package_constraint_status"], "warning")
        self.assertEqual(report["no_submit_handoff_contract"]["status"], "ready_for_review")
        self.assertFalse(report["no_submit_handoff_contract"]["no_submit_semantics"]["sbatch_attempted"])
        self.assertFalse(report["no_submit_handoff_contract"]["no_submit_semantics"]["balfrin_job_submitted"])
        self.assertTrue(report["constraint_pressure"]["diagnostic_handoff_budget_accepted"])
        self.assertEqual(report["constraint_pressure"]["status"], "warning")
        self.assertEqual(report["constraint_pressure"]["constraint_checks"][0]["status"], "warning")
        self.assertEqual(report["constraint_pressure"]["constraint_checks"][0]["limit"], 16)
        self.assertEqual(report["constraint_pressure"]["constraint_checks"][1]["status"], "warning")
        self.assertEqual(report["constraint_pressure"]["constraint_checks"][2]["status"], "warning")
        self.assertNotIn("requested simultaneous_release_zone_batch_size=16 exceeds measured max 8", report["constraint_pressure"]["summary"])
        self.assertNotIn("scenario pressure blocked", report["constraint_pressure"]["summary"])
        self.assertEqual(report["handoff_output_budget_projection"]["budget_acceptance_validation"]["status"], "accepted")
        self.assertEqual(
            report["handoff_output_budget_projection"]["budget_acceptance_validation"]["threshold_profile_id"],
            MODULE.DIAGNOSTIC_16_ZONE_BUDGET_PROFILE_ID,
        )
        self.assertEqual(report["handoff_output_budget_projection"]["budget_acceptance_validation"]["failures"], [])
        self.assertEqual(
            report["handoff_output_budget_projection"]["budget_recheck"]["status"],
            "budget_passes_no_reduction_needed",
        )
        self.assertEqual(report["manifest_pruning"]["status"], "budget_passes_no_reduction_needed")
        self.assertGreater(report["handoff_output_budget_projection"]["estimated_storage_bytes"], 0)
        self.assertEqual(
            report["handoff_output_budget_projection"]["estimated_storage_bytes"],
            report["handoff_output_budget_projection"]["output_byte_count"],
        )
        self.assertLess(report["handoff_output_budget_projection"]["estimated_storage_bytes"], 25_000)
        self.assertEqual(
            report["scenario_pressure_projection"]["first_bottleneck_labels"]["first_blocked"],
            "release_zone_count",
        )
        self.assertEqual(
            report["handoff_output_budget_projection"]["first_bottleneck_labels"]["first_blocked"],
            "manifest_size_bytes",
        )
        self.assertEqual(report["handoff_output_budget_projection"]["reducer_manifest_file_count"], 0)
        self.assertEqual(report["handoff_output_budget_projection"]["reducer_manifest_bytes"], 0)
        self.assertEqual(report["follow_up_recommendation"]["minimum_measured_multi_zone_run"]["release_zone_count"], 2)
        self.assertEqual(report["no_submit_handoff_contract"]["scenario_limits"]["release_zone_count"], 2)
        first_blocker = report["no_submit_handoff_contract"]["first_blocker"]
        self.assertIsNone(first_blocker)

    def test_diagnostic_no_submit_contract_ignores_unrelated_four_zone_efficiency_blocker(self) -> None:
        report = {
            "artifact_dir": "/scratch/mch/olifu/rust_rockfall/tb574_unblocked_16_zone_handoff",
            "package_status": "ready",
            "package_constraint_status": "warning",
            "review_readiness_classification": "blocked_efficiency",
            "review_readiness_reason": "single-job sufficiency or reducer scaling is not yet ready for the four-zone review package",
            "authorization_review_command": "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only",
            "authorization_submit_command": "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --authorized-submit",
            "constraint_pressure": {
                "status": "warning",
                "diagnostic_handoff_budget_accepted": True,
                "requested_release_zone_batch_size": 16,
                "requested_reducer_chunk_count": 2,
                "requested_reducer_worker_count": 2,
                "measured_constraints": {},
            },
            "follow_up_recommendation": {
                "minimum_measured_multi_zone_run": {
                    "output_mode": "rebuildable_reduced_output",
                    "conditional_curve_export": "summary-only",
                    "grid_csv_export": "none",
                    "bounded_gis_cog_settings": {"no_plots": True},
                }
            },
        }

        contract = MODULE.build_no_submit_handoff_contract(report)

        self.assertEqual(contract["status"], "ready_for_review")
        self.assertIsNone(contract["first_blocker"])

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
