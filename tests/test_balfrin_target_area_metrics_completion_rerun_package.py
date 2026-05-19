from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_target_area_metrics_completion_rerun_package.py"
SPEC = importlib.util.spec_from_file_location(
    "summarize_balfrin_target_area_metrics_completion_rerun_package",
    SCRIPT_PATH,
)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinTargetAreaMetricsCompletionRerunPackageTests(unittest.TestCase):
    def _ready_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "ready_for_read_only_collection",
            "ready_for_read_only_collection": True,
            "ready_for_pre_submit": True,
            "remote_head": "abc123",
            "remote_checkout_hygiene": {
                "status": "pass",
                "remote_head": "abc123",
                "tracked_modifications": [],
                "untracked_generated_files": [],
                "stale_submission_packages": [],
                "stale_logs": [],
                "dirty_path_count": 0,
                "safe_cleanup_commands": ["git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all"],
            },
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [
                {"name": "ssh_availability", "status": "pass", "returncode": 0},
                {"name": "remote_clone", "status": "pass", "returncode": 0},
                {"name": "run_root_visibility", "status": "pass", "returncode": 0},
                {"name": "scheduler_query", "status": "pass", "returncode": 0},
            ],
        }

    def test_ready_report_is_authorization_request_preflight_for_metrics_completion(self) -> None:
        report = MODULE.build_report({"balfrin_access_preflight": self._ready_access()})

        self.assertEqual(report["schema_version"], "balfrin_target_area_metrics_completion_rerun_package_v1")
        self.assertEqual(report["preflight_status"], "ready_for_authorization_request")
        self.assertEqual(report["authorization_request_preflight_status"], "ready_for_authorization_request")
        self.assertEqual(report["authorization_handoff_status"], "ready_for_authorization_review")
        self.assertEqual(report["package_status"], "complete_rerun_package")
        self.assertTrue(report["authorization_request_preflight"]["ready_for_authorization_request"])
        self.assertFalse(report["authorization_request_preflight"]["authorization_granted"])
        self.assertFalse(report["authorization_request_preflight"]["live_submission_authorized"])
        handoff = report["authorization_handoff_package"]
        self.assertTrue(handoff["ready_for_authorization_review"])
        self.assertEqual(handoff["status"], "ready_for_authorization_review")
        self.assertEqual(handoff["tb240_unrecovered_metrics"], MODULE.TB240_UNRECOVERED_METRICS)
        self.assertIn("metrics_completion_v1/probe.sbatch", handoff["sbatch_command"])
        self.assertIn("collect_balfrin_probe_metrics.py", handoff["collection_command"])
        self.assertIn("summarize_balfrin_probe_preservation_gate.py", handoff["preservation_gate_command"])
        self.assertEqual(handoff["access_preflight_status"], "ready_for_read_only_collection")
        self.assertEqual(
            handoff["fail_closed_classifications"]["missing_explicit_authorization"]["status"],
            "blocked_missing_explicit_authorization",
        )
        self.assertEqual(report["post_attempt_integration_notes"]["status"], "no_authorization")
        self.assertFalse(report["post_attempt_integration_notes"]["submit_command_executed"])
        self.assertFalse(report["post_attempt_integration_notes"]["measured_evidence_promoted"])
        self.assertIn(
            "separate_explicit_user_authorization",
            report["post_attempt_integration_notes"]["exact_remaining_precondition"],
        )
        self.assertFalse(handoff["live_submission_authorized"])
        self.assertEqual(
            report["balfrin_access_preflight_requirement"]["consumed_status"],
            "ready_for_read_only_collection",
        )
        self.assertTrue(report["balfrin_access_preflight_requirement"]["ready_for_pre_submit"])
        self.assertEqual(report["balfrin_access_preflight_requirement"]["remote_checkout_hygiene"]["status"], "pass")
        self.assertIn("check_balfrin_remote_access_preflight.py", report["balfrin_access_preflight_requirement"]["command"])
        self.assertEqual(report["package_provenance_status"], "mixed_provenance")
        self.assertEqual(report["preservation_checklist"]["status"], "complete")
        self.assertEqual(report["preservation_checklist"]["missing_metrics"], [])
        self.assertEqual(report["preservation_checklist"]["missing_run_root_entries"], [])
        self.assertEqual(report["preservation_checklist"]["missing_replay_metadata"], [])
        self.assertEqual(report["existing_target_area_run_comparison"]["closure_targets"], MODULE.REQUIRED_METRICS)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["output_file_count"], 58)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["output_bytes"], 192350243)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["conditional_curve_row_count"], 729600)
        self.assertIn("peak-memory and split validation/hazard output metrics", report["existing_target_area_run_comparison"]["summary"])
        expected_metrics = report["authorization_request_preflight"]["expected_metrics"]["required_metrics"]
        self.assertEqual([entry["metric"] for entry in expected_metrics], MODULE.REQUIRED_METRICS)
        preservation_files = report["authorization_request_preflight"]["preservation_files"]
        self.assertEqual(
            [entry["path"] for entry in preservation_files["required_run_root_entries"]],
            [entry["path"] for entry in MODULE.REQUIRED_RUN_ROOT_ENTRIES],
        )
        collection_commands = report["authorization_request_preflight"]["post_run_collection_commands"]
        self.assertIn("collect_probe_metrics", [entry["name"] for entry in collection_commands])
        self.assertIn("summarize_preservation_gate", [entry["name"] for entry in collection_commands])
        self.assertIn("collect_slurm_accounting", [entry["name"] for entry in collection_commands])
        self.assertIn("--dry-run", report["rerun_command_plan"]["dry_run_command"])
        self.assertIn("--generate-only", report["rerun_command_plan"]["generate_only_command"])
        self.assertIn("no live submission is authorized", report["package_summary"]["summary"])
        self.assertIn("preflight_status: ready_for_authorization_request", MODULE.render_text_report(report))
        self.assertIn("authorization_handoff_status: ready_for_authorization_review", MODULE.render_text_report(report))
        self.assertIn("post_attempt_integration_notes:", MODULE.render_text_report(report))
        self.assertIn("Balfrin Target-Area Metrics Completion Rerun Package", MODULE.render_text_report(report))

    def test_authorization_handoff_ready_for_authorization_review(self) -> None:
        report = MODULE.build_report({"balfrin_access_preflight": self._ready_access()})
        handoff = report["authorization_handoff_package"]

        self.assertEqual(handoff["status"], "ready_for_authorization_review")
        self.assertEqual(handoff["exact_run_root"], str(MODULE.DEFAULT_RERUN_RUN_ROOT.resolve()))
        self.assertEqual(handoff["probe_manifest"], str(MODULE.DEFAULT_PROBE_MANIFEST.resolve()))
        self.assertEqual(handoff["tb240_unrecovered_metrics"], MODULE.TB240_UNRECOVERED_METRICS)
        self.assertEqual(handoff["fail_closed_classifications"]["missing_access"]["status"], "complete")
        self.assertEqual(handoff["fail_closed_classifications"]["missing_package"]["status"], "complete")
        self.assertEqual(handoff["fail_closed_classifications"]["stale_comparison_basis"]["status"], "complete")
        self.assertEqual(handoff["fail_closed_classifications"]["no_unrecovered_metrics"]["status"], "complete")
        self.assertEqual(handoff["reviewer_decision"]["status"], "blocked_missing_explicit_authorization")

    def test_authorization_handoff_blocks_missing_access(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_ssh_unavailable"
        access["ready_for_read_only_collection"] = False

        report = MODULE.build_report({"balfrin_access_preflight": access})
        handoff = report["authorization_handoff_package"]

        self.assertEqual(handoff["status"], "blocked_missing_access")
        self.assertFalse(handoff["ready_for_authorization_review"])
        self.assertEqual(
            handoff["fail_closed_classifications"]["missing_access"]["consumed_status"],
            "blocked_ssh_unavailable",
        )
        self.assertIn("missing_access", handoff["blocked_reasons"])

    def test_authorization_handoff_blocks_no_unrecovered_metrics(self) -> None:
        report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "tb240_unrecovered_metrics": [],
            }
        )
        handoff = report["authorization_handoff_package"]

        self.assertEqual(handoff["status"], "blocked_no_unrecovered_metrics")
        self.assertFalse(handoff["ready_for_authorization_review"])
        self.assertEqual(handoff["tb240_unrecovered_metrics"], [])
        self.assertEqual(
            handoff["fail_closed_classifications"]["no_unrecovered_metrics"]["status"],
            "blocked_no_unrecovered_metrics",
        )

    def test_authorization_handoff_blocks_missing_package(self) -> None:
        report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "missing_inputs": ["existing_target_area_run"],
            }
        )
        handoff = report["authorization_handoff_package"]

        self.assertEqual(handoff["status"], "blocked_missing_package")
        self.assertFalse(handoff["ready_for_authorization_review"])
        self.assertEqual(
            handoff["fail_closed_classifications"]["missing_package"]["status"],
            "blocked_missing_package",
        )
        self.assertIn("missing_package", handoff["blocked_reasons"])

    def test_partial_package_blocks_when_required_declarations_are_missing(self) -> None:
        report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "declared_metrics": MODULE.REQUIRED_METRICS[:-1],
                "declared_run_root_entries": [entry["path"] for entry in MODULE.REQUIRED_RUN_ROOT_ENTRIES[:-1]],
                "declared_replay_metadata": MODULE.REQUIRED_REPLAY_METADATA[:-1],
            }
        )

        self.assertEqual(report["preflight_status"], "blocked_incomplete_package")
        self.assertEqual(report["authorization_handoff_status"], "blocked_missing_package")
        self.assertFalse(report["authorization_request_preflight"]["ready_for_authorization_request"])
        self.assertEqual(report["package_status"], "partial_rerun_package")
        self.assertEqual(report["preservation_checklist"]["status"], "blocked_missing_inputs")
        self.assertIn("hazard_output.bytes", report["preservation_checklist"]["missing_metrics"])
        self.assertIn("output/chunks", report["preservation_checklist"]["missing_run_root_entries"])
        self.assertIn("git_commit", report["preservation_checklist"]["missing_replay_metadata"])
        self.assertIn("preservation_checklist", report["authorization_request_preflight"]["blocked_reasons"])
        self.assertIn("fails closed until every required metric", report["preservation_checklist"]["summary"])

    def test_balfrin_access_missing_run_root_fails_closed_with_exact_status(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_missing_run_root"
        access["ready_for_read_only_collection"] = False
        access["checked_commands"] = [
            {"name": "ssh_availability", "status": "pass", "returncode": 0},
            {"name": "remote_clone", "status": "pass", "returncode": 0},
            {"name": "run_root_visibility", "status": "fail", "returncode": 1},
        ]

        report = MODULE.build_report({"balfrin_access_preflight": access})

        self.assertEqual(report["preflight_status"], "blocked_missing_run_root")
        self.assertEqual(
            report["authorization_request_preflight"]["balfrin_access_preflight_requirement"]["consumed_status"],
            "blocked_missing_run_root",
        )
        self.assertIn("balfrin_access:blocked_missing_run_root", report["authorization_request_preflight"]["blocked_reasons"])

    def test_balfrin_access_blocked_fails_closed_with_exact_status(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_ssh_unavailable"
        access["ready_for_read_only_collection"] = False
        access["checked_commands"] = [
            {"name": "ssh_availability", "status": "fail", "returncode": 255},
        ]

        report = MODULE.build_report({"balfrin_access_preflight": access})

        self.assertEqual(report["preflight_status"], "blocked_ssh_unavailable")
        self.assertEqual(
            report["balfrin_access_preflight_requirement"]["consumed_status"],
            "blocked_ssh_unavailable",
        )
        self.assertFalse(report["authorization_request_preflight"]["live_submission_authorized"])

    def test_dirty_remote_checkout_fails_closed_with_hygiene_cleanup_actions(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_dirty_remote_checkout"
        access["ready_for_read_only_collection"] = False
        access["ready_for_pre_submit"] = False
        access["remote_checkout_hygiene"] = {
            "status": "fail",
            "remote_head": "deadbeef",
            "tracked_modifications": ["M scripts/submit_balfrin_probe.py"],
            "untracked_generated_files": ["validation/private/tb264/balfrin_submission_package.json"],
            "stale_submission_packages": ["validation/private/tb264/balfrin_submission_package.json"],
            "stale_logs": ["logs/slurm-123.err"],
            "dirty_path_count": 3,
            "safe_cleanup_commands": [
                "git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all",
                "git -C /users/olifu/work/rust_rockfall clean -n -- validation/private/tb264/balfrin_submission_package.json logs/slurm-123.err",
            ],
        }

        report = MODULE.build_report({"balfrin_access_preflight": access})

        self.assertEqual(report["preflight_status"], "blocked_dirty_remote_checkout")
        requirement = report["balfrin_access_preflight_requirement"]
        self.assertFalse(requirement["ready_for_pre_submit"])
        self.assertEqual(requirement["remote_checkout_hygiene"]["remote_head"], "deadbeef")
        self.assertIn("clean -n", requirement["remote_checkout_hygiene"]["safe_cleanup_commands"][1])
        self.assertIn(
            "balfrin_access:blocked_dirty_remote_checkout",
            report["authorization_request_preflight"]["blocked_reasons"],
        )
        self.assertEqual(report["post_attempt_integration_notes"]["status"], "blocked_pre_submit")
        self.assertEqual(
            report["post_attempt_integration_notes"]["exact_remaining_precondition"],
            "blocked_dirty_remote_checkout",
        )
        self.assertFalse(report["post_attempt_integration_notes"]["measured_evidence_promoted"])

    def test_post_attempt_notes_distinguish_failed_closed_and_submitted_without_promotion(self) -> None:
        failed_report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "post_attempt_status": "failed_closed",
                "submission_report": {"status": "failed"},
            }
        )

        self.assertEqual(failed_report["post_attempt_integration_notes"]["status"], "failed_closed")
        self.assertTrue(failed_report["post_attempt_integration_notes"]["submit_command_executed"])
        self.assertFalse(failed_report["post_attempt_integration_notes"]["measured_evidence_promoted"])

        submitted_report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "submission_report": {"status": "submitted", "submitted_job_id": "987654"},
            }
        )

        self.assertEqual(submitted_report["post_attempt_integration_notes"]["status"], "submitted")
        self.assertEqual(submitted_report["post_attempt_integration_notes"]["submitted_job_id"], "987654")
        self.assertFalse(submitted_report["post_attempt_integration_notes"]["measured_evidence_promoted"])

    def test_missing_package_inputs_return_a_fail_closed_report(self) -> None:
        report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "missing_inputs": ["existing_target_area_run"],
            }
        )

        self.assertEqual(report["preflight_status"], "blocked_incomplete_package")
        self.assertEqual(report["authorization_handoff_status"], "blocked_missing_package")
        self.assertEqual(report["package_status"], "missing_rerun_package")
        self.assertEqual(report["package_provenance_status"], "blocked_missing_inputs")
        self.assertEqual(report["rerun_command_plan"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["preservation_checklist"]["status"], "blocked_missing_inputs")
        self.assertIn("required rerun-package inputs are missing", report["package_summary"]["summary"])
        self.assertTrue(all(section["status"] == "blocked_missing_inputs" for section in report["section_provenance_profile"]))

    def test_cli_writes_json_and_text_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_target_area_metrics_completion_rerun_package_v1"
            access_json = Path(tmpdir) / "balfrin_access.json"
            access_json.write_text(json.dumps(self._ready_access()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--artifact-dir",
                        str(artifact_dir),
                        "--balfrin-access-json",
                        str(access_json),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_target_area_metrics_completion_rerun_package_v1.json"
            text_path = artifact_dir / "balfrin_target_area_metrics_completion_rerun_package_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["preflight_status"], "ready_for_authorization_request")
            self.assertEqual(report["package_status"], "complete_rerun_package")
            text = text_path.read_text(encoding="utf-8")
            self.assertIn("balfrin_access_preflight_requirement", text)
            self.assertIn("post_run_collection_commands", text)


if __name__ == "__main__":
    unittest.main()
