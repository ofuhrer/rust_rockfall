from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "execute_management_aoi_balfrin_run.py"


def load_module():
    spec = importlib.util.spec_from_file_location("execute_management_aoi_balfrin_run", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class ManagementAoiBalfrinExecutionStateTests(unittest.TestCase):
    def _blocked_handoff_report(self, artifact_dir: Path) -> dict[str, object]:
        return {
            "schema_version": "management_aoi_balfrin_handoff_v1",
            "handoff_classification": "blocked_missing_prepared_pilot_inputs",
            "handoff_status": "blocked_missing_prepared_pilot_inputs",
            "ready_for_live_management_aoi_postproc_run": False,
            "blocked_reason": "prepared-pilot inputs are missing",
            "package_json_path": str(artifact_dir / "management_aoi_balfrin_handoff_v1.json"),
            "authorization_record_path": str(artifact_dir / "management_aoi_balfrin_authorization_audit_v1.yaml"),
            "exact_run_root": "/scratch/mch/olifu/rust_rockfall/probes/management-aoi/test",
            "run_id": "test",
            "partition": "postproc",
            "candidate_evidence": {
                "candidate_cell_count": 3419,
                "candidate_area_m2": 13676.0,
            },
            "scenario_generation_pressure": {
                "scenario_pressure_status": "ready",
                "scenario_row_count": 3,
            },
            "budget_checks": [
                {"gate": "prepared_pilot_inputs", "status": "blocked"},
                {"gate": "output_budget", "status": "not_evaluated"},
            ],
            "authorization_audit": {
                "status": "blocked_missing_prepared_pilot_inputs",
                "live_submission_authorized_by_this_record": False,
            },
            "command_list": [
                {
                    "command_id": "future_authorized_submit",
                    "status": "blocked_missing_prepared_pilot_inputs",
                    "runnable_now": False,
                }
            ],
        }

    def test_blocked_handoff_produces_no_submit_failed_closed_state(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            artifact_dir = Path(tmp) / "execution"
            report = MODULE.build_report(
                artifact_dir=artifact_dir,
                handoff_report_override=self._blocked_handoff_report(Path(tmp) / "handoff"),
                access_preflight_report={"status": "ready_for_read_only_collection"},
                access_preflight_source="/tmp/access.json",
            )
            MODULE.materialize_artifacts(report)

            self.assertTrue((artifact_dir / "management_aoi_balfrin_execution_state_v1.json").exists())
            self.assertTrue((artifact_dir / "management_aoi_balfrin_execution_state_v1.txt").exists())

        self.assertEqual(report["schema_version"], "management_aoi_balfrin_execution_state_v1")
        self.assertEqual(report["execution_status"], "failed_closed")
        self.assertEqual(report["measurement_status"], "not_measured")
        self.assertEqual(report["handoff_classification"], "blocked_missing_prepared_pilot_inputs")
        self.assertIsNone(report["job_id"])
        self.assertIsNone(report["runtime_seconds"])
        self.assertIsNone(report["memory_peak_mb"])
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])
        self.assertEqual(report["no_submit_semantics"]["scheduler_submission_status"], "not_attempted")
        self.assertFalse(report["no_submit_semantics"]["future_submit_command_runnable_now"])
        self.assertEqual(report["first_persistent_blocker"]["status"], "blocked_missing_prepared_pilot_inputs")
        self.assertEqual(report["first_persistent_blocker"]["scenario_row_count"], 3)
        self.assertEqual(report["validation_output_pressure"]["status"], "not_evaluated")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

        text = MODULE.render_text_report(report)
        self.assertIn("execution_status: `failed_closed`", text)
        self.assertIn("sbatch_attempted: `False`", text)

    def test_cli_writes_report_and_returns_nonzero_for_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            artifact_dir = Path(tmp) / "execution"
            handoff_dir = Path(tmp) / "handoff"
            access_path = Path(tmp) / "access.json"
            access_path.write_text(json.dumps({"status": "ready_for_read_only_collection"}), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--artifact-dir",
                        str(artifact_dir),
                        "--handoff-artifact-dir",
                        str(handoff_dir),
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
            self.assertEqual(report["execution_status"], "failed_closed")
            self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])
            self.assertEqual(report["first_persistent_blocker"]["status"], "blocked_missing_prepared_pilot_inputs")
            self.assertTrue((artifact_dir / "management_aoi_balfrin_execution_state_v1.json").exists())


if __name__ == "__main__":
    unittest.main()
