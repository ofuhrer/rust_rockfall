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
        self.assertEqual(report["package_status"], "complete_rerun_package")
        self.assertTrue(report["authorization_request_preflight"]["ready_for_authorization_request"])
        self.assertFalse(report["authorization_request_preflight"]["authorization_granted"])
        self.assertFalse(report["authorization_request_preflight"]["live_submission_authorized"])
        self.assertEqual(
            report["balfrin_access_preflight_requirement"]["consumed_status"],
            "ready_for_read_only_collection",
        )
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
        self.assertIn("Balfrin Target-Area Metrics Completion Rerun Package", MODULE.render_text_report(report))

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

    def test_missing_package_inputs_return_a_fail_closed_report(self) -> None:
        report = MODULE.build_report(
            {
                "balfrin_access_preflight": self._ready_access(),
                "missing_inputs": ["existing_target_area_run"],
            }
        )

        self.assertEqual(report["preflight_status"], "blocked_incomplete_package")
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
