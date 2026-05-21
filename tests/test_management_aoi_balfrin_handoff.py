from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_management_aoi_balfrin_handoff.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_management_aoi_balfrin_handoff", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class ManagementAoiBalfrinHandoffTests(unittest.TestCase):
    def _prepared_report(self) -> dict[str, object]:
        return {
            "workflow_status": "blocked_missing_prepared_pilot_inputs",
            "prepared_pilot_input_classification": "ready_real",
            "prepared_pilot_compiler": {
                "classification": "blocked_missing_prepared_pilot_inputs",
                "first_blocker": {
                    "status": "blocked_missing_prepared_pilot_inputs",
                    "blocked_reason": "prepared-pilot inputs are missing",
                },
            },
            "case_skeleton_output": {
                "status": "blocked_missing_prepared_pilot_inputs",
                "blocked_execution_status": "blocked_missing_prepared_pilot_inputs",
                "case_skeleton_path": "/tmp/prepared/aoi_to_prepared_pilot_case_skeleton.yaml",
            },
            "workflow_ignored_output_roots": ["/tmp/prepared"],
        }

    def _scenario_pressure_report(self) -> dict[str, object]:
        return {
            "schema_version": "management_aoi_scenario_pressure_v1",
            "scenario_pressure_status": "ready",
            "blocked_reason": "",
            "required_upstream_replacement": "",
            "candidate_evidence": {
                "candidate_release_zone_set_status": "emitted",
                "candidate_cell_count": 3419,
                "candidate_area_m2": 13676.0,
                "review_summary": {"candidate_count": 3419, "review_row_count": 1},
            },
            "scenario_generation_pressure": {
                "scenario_row_count": 3,
                "scenario_table_total_bytes": 22718,
                "manifest_pressure": {"scenario_table_manifest_pressure": "ready"},
            },
            "output_paths": {"scenario_pressure_report_json": "/tmp/scenario_pressure.json"},
            "source_inputs": {"candidate_metrics_manifest_path": "candidate_manifest.json"},
        }

    def test_current_prepared_pilot_inputs_block_the_balfrin_handoff(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            artifact_dir = Path(tmp) / "handoff"
            report = MODULE.build_report(
                artifact_dir=artifact_dir,
                prepared_pilot_output_root=Path(tmp) / "prepared",
                prepared_pilot_report_override=self._prepared_report(),
                scenario_pressure_report_override=self._scenario_pressure_report(),
                access_preflight_report={
                    "schema_version": "balfrin_remote_access_preflight_v1",
                    "status": "ready_for_read_only_collection",
                    "ready_for_pre_submit": True,
                },
                access_preflight_source="/tmp/access.json",
            )
            MODULE.materialize_artifacts(report)

            self.assertTrue((artifact_dir / "management_aoi_balfrin_handoff_v1.json").exists())
            self.assertTrue((artifact_dir / "management_aoi_balfrin_handoff_v1.txt").exists())
            auth = yaml.safe_load((artifact_dir / "management_aoi_balfrin_authorization_audit_v1.yaml").read_text())

        self.assertEqual(report["schema_version"], "management_aoi_balfrin_handoff_v1")
        self.assertEqual(report["handoff_classification"], "blocked_missing_prepared_pilot_inputs")
        self.assertFalse(report["ready_for_live_management_aoi_postproc_run"])
        self.assertEqual(report["partition"], "postproc")
        self.assertIn("/scratch/mch/olifu/rust_rockfall/probes/management-aoi", report["exact_run_root"])
        self.assertEqual(report["candidate_evidence"]["candidate_cell_count"], 3419)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_row_count"], 3)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_pressure_status"], "ready")
        self.assertEqual(report["budget_checks"][0]["gate"], "prepared_pilot_inputs")
        self.assertEqual(report["budget_checks"][0]["status"], "blocked")
        self.assertEqual(report["budget_checks"][2]["status"], "not_evaluated")
        self.assertEqual(report["authorization_audit"]["access_preflight_status"], "ready_for_read_only_collection")
        self.assertFalse(report["authorization_audit"]["live_submission_authorized_by_this_record"])
        self.assertEqual(auth["status"], "blocked_missing_prepared_pilot_inputs")
        submit_command = next(command for command in report["command_list"] if command["command_id"] == "future_authorized_submit")
        self.assertFalse(submit_command["runnable_now"])
        self.assertIn("--partition postproc", submit_command["command"])
        self.assertIn("Do not run while the handoff is blocked", submit_command["boundary_note"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

        text = MODULE.render_text_report(report)
        self.assertIn("handoff_classification: `blocked_missing_prepared_pilot_inputs`", text)
        self.assertIn("scenario_row_count: `3`", text)

    def test_cli_writes_blocked_package_and_returns_nonzero_for_nonready(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            artifact_dir = Path(tmp) / "handoff"
            access_path = Path(tmp) / "access.json"
            access_path.write_text(
                json.dumps({"schema_version": "balfrin_remote_access_preflight_v1", "status": "ready_for_read_only_collection"}),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--artifact-dir",
                        str(artifact_dir),
                        "--prepared-pilot-output-root",
                        str(Path(tmp) / "prepared"),
                        "--balfrin-access-preflight-json",
                        str(access_path),
                        "--format",
                        "json",
                    ]
                )
            report = json.loads(buffer.getvalue())

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["handoff_classification"], "blocked_missing_prepared_pilot_inputs")
            self.assertTrue((artifact_dir / "management_aoi_balfrin_handoff_v1.json").exists())
            self.assertTrue((artifact_dir / "management_aoi_balfrin_authorization_audit_v1.yaml").exists())


if __name__ == "__main__":
    unittest.main()
