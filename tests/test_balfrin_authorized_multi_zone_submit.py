from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


submit_driver = _load_module(ROOT / "scripts/submit_balfrin_probe.py", "submit_balfrin_probe_authorized")
collect_driver = _load_module(ROOT / "scripts/collect_balfrin_probe_metrics.py", "collect_balfrin_probe_metrics_authorized")


class BalfrinAuthorizedMultiZoneSubmitTests(unittest.TestCase):
    def _write_manifest(self, path: Path) -> None:
        path.write_text("run_id: tb211_authorized\ncommands: []\n", encoding="utf-8")

    def _write_reviewed_package(self, path: Path) -> str:
        constraint = {
            "status": "acceptable",
            "summary": "acceptable: requested multi-zone settings stay below measured reducer constraints",
            "requested_release_zone_batch_size": 2,
            "requested_reducer_chunk_count": 2,
            "requested_reducer_worker_count": 2,
            "measured_constraints": {
                "simultaneous_release_zone_batch_max": 8,
                "reducer_chunk_count_max": 4,
                "reducer_worker_count_max": 2,
            },
            "constraint_checks": [],
        }
        payload = {
            "schema_version": "balfrin_multi_release_zone_demo_package_v1",
            "package_status": "mixed_provenance",
            "submission_classification": "blocked_pending_new_human_authorization",
            "authorization_classification": "blocked_pending_authorization",
            "live_execution_requires_new_human_authorization": True,
            "package_mode": "generate-only",
            "package_constraint_status": "acceptable",
            "constraint_pressure": constraint,
            "follow_up_recommendation": {
                "minimum_measured_multi_zone_run": {
                    "release_zone_count": 2,
                    "scenario_count": 2,
                    "trajectory_count_target": 1000,
                    "trajectory_workers": 2,
                    "reducer_workers": 2,
                    "conditional_curve_export": "summary-only",
                    "grid_csv_export": "none",
                    "export_geotiff": True,
                    "pilot_gis_package": True,
                    "output_profile_policy": {"classification": "scalable_default"},
                    "preservation_gate_checklist": [
                        "Review the package JSON and Markdown together before any later authorization request."
                    ],
                    "reducer_pressure": constraint,
                }
            },
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_access_report(self, path: Path) -> None:
        payload = {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "ready_for_read_only_collection",
            "ready_for_read_only_collection": True,
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [{"name": "ssh_availability", "status": "pass"}],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _write_authorization_record(self, path: Path, package_path: Path, package_sha256: str) -> None:
        payload = {
            "schema_version": "balfrin_multi_zone_live_authorization_v1",
            "authorization_status": "authorized_for_one_bounded_probe",
            "authorized_task": "TB-211",
            "no_rerun_without_renewed_authorization": True,
            "reviewed_handoff_package_path": str(package_path.resolve()),
            "reviewed_handoff_package_sha256": package_sha256,
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def test_authorized_submit_blocks_without_authorization_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            manifest = tmp / "manifest.yaml"
            run_root = tmp / "run-root"
            package_path = tmp / "reviewed_package.json"
            package_sha256 = self._write_reviewed_package(package_path)
            self._write_authorization_record(tmp / "authorization_record.yaml", package_path, package_sha256)
            access_path = tmp / "balfrin_access.json"
            self._write_access_report(access_path)

            with patch.object(
                submit_driver,
                "_read_command_plan",
                return_value=({"run_id": "tb211_authorized", "commands": []}, "tb211_authorized"),
            ), patch.object(
                submit_driver,
                "_build_submission_package_report",
                return_value={"input_checks": {"status": "ready_for_balfrin_target_gate", "blocking_checks": [], "checks": []}},
            ), patch.object(submit_driver, "_write_outputs") as write_outputs_mock, patch.object(
                submit_driver.subprocess,
                "run",
            ) as run_mock:
                self._write_manifest(manifest)
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = submit_driver.main(
                        [
                            str(manifest),
                            "--authorized-submit",
                            "--run-root",
                            str(run_root),
                            "--run-id",
                            "tb211_authorized",
                            "--partition",
                            "postproc",
                            "--reviewed-handoff-package",
                            str(package_path),
                            "--authorization-record",
                            str(tmp / "missing_authorization_record.yaml"),
                            "--balfrin-access-preflight-json",
                            str(access_path),
                        ]
                    )

            self.assertEqual(exit_code, 2)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["status"], "blocked_missing_authorization")
            self.assertEqual(report["submission_status"], "blocked_missing_authorization")
            self.assertIn("authorization record", report["blocked_reason"])
            write_outputs_mock.assert_not_called()
            run_mock.assert_not_called()

    def test_authorized_submit_accepts_reviewed_package_and_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            manifest = tmp / "manifest.yaml"
            run_root = tmp / "run-root"
            package_path = tmp / "reviewed_package.json"
            package_sha256 = self._write_reviewed_package(package_path)
            auth_path = tmp / "authorization_record.yaml"
            self._write_authorization_record(auth_path, package_path, package_sha256)
            access_path = tmp / "balfrin_access.json"
            self._write_access_report(access_path)

            command_plan = {"run_id": "tb211_authorized", "commands": []}
            package_report = {
                "input_checks": {"status": "ready_for_balfrin_target_gate", "blocking_checks": [], "checks": []},
            }
            sbatch_path = run_root / "probe.sbatch"

            with patch.object(submit_driver, "_read_command_plan", return_value=(command_plan, "tb211_authorized")), patch.object(
                submit_driver,
                "_build_submission_package_report",
                return_value=package_report,
            ), patch.object(
                submit_driver,
                "_write_outputs",
                return_value=(run_root / "command_plan.json", sbatch_path),
            ), patch.object(
                submit_driver.subprocess,
                "run",
                return_value=type("CompletedProcess", (), {"returncode": 0, "stdout": "987654\n", "stderr": ""})(),
            ) as run_mock:
                self._write_manifest(manifest)
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = submit_driver.main(
                        [
                            str(manifest),
                            "--authorized-submit",
                            "--run-root",
                            str(run_root),
                            "--run-id",
                            "tb211_authorized",
                            "--partition",
                            "postproc",
                            "--reviewed-handoff-package",
                            str(package_path),
                            "--authorization-record",
                            str(auth_path),
                            "--balfrin-access-preflight-json",
                            str(access_path),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            self.assertEqual(buffer.getvalue().strip(), "submitted_job_id=987654")
            run_mock.assert_called_once()

    def test_authorized_submit_blocks_when_required_inputs_are_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            manifest = tmp / "manifest.yaml"
            run_root = tmp / "run-root"
            package_path = tmp / "reviewed_package.json"
            package_sha256 = self._write_reviewed_package(package_path)
            auth_path = tmp / "authorization_record.yaml"
            self._write_authorization_record(auth_path, package_path, package_sha256)
            access_path = tmp / "balfrin_access.json"
            self._write_access_report(access_path)

            with patch.object(
                submit_driver,
                "_read_command_plan",
                return_value=({"run_id": "tb211_authorized", "commands": []}, "tb211_authorized"),
            ), patch.object(
                submit_driver,
                "_build_submission_package_report",
                return_value={
                    "input_checks": {
                        "status": "blocked_missing_inputs",
                        "blocking_checks": [{"name": "terrain_crop", "status": "fail"}],
                        "checks": [],
                    }
                },
            ), patch.object(submit_driver, "_write_outputs") as write_outputs_mock, patch.object(
                submit_driver.subprocess,
                "run",
            ) as run_mock:
                self._write_manifest(manifest)
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = submit_driver.main(
                        [
                            str(manifest),
                            "--authorized-submit",
                            "--run-root",
                            str(run_root),
                            "--run-id",
                            "tb211_authorized",
                            "--partition",
                            "postproc",
                            "--reviewed-handoff-package",
                            str(package_path),
                            "--authorization-record",
                            str(auth_path),
                            "--balfrin-access-preflight-json",
                            str(access_path),
                        ]
                    )

            self.assertEqual(exit_code, 2)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["status"], "blocked_missing_inputs")
            self.assertEqual(report["submission_status"], "blocked_missing_inputs")
            self.assertIn("required inputs are missing", report["blocked_reason"])
            write_outputs_mock.assert_not_called()
            run_mock.assert_not_called()

    def test_collect_run_metrics_distinguishes_measured_and_incomplete_roots(self) -> None:
        complete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        incomplete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root"

        complete = collect_driver.collect_run_metrics(complete_root)
        incomplete = collect_driver.collect_run_metrics(incomplete_root)

        self.assertEqual(complete["run_root_status"], "measured_run_root")
        self.assertEqual(complete["report_status"], "measured_run_root")
        self.assertEqual(complete["checksums"]["status"], "complete")
        self.assertEqual(complete["manifest_pressure"]["status"], "measured")
        self.assertEqual(complete["reducer_pressure"]["merge_order"], "sorted_chunk_id")
        self.assertEqual(complete["reducer_pressure"]["merge_order_independent"], True)
        self.assertEqual(complete["manifest_pressure"]["validation_output_file_count"], 2005)
        self.assertEqual(complete["manifest_pressure"]["hazard_output_file_count"], 46)
        self.assertEqual(complete["failure_behavior"]["status"], "log_failure_signals")
        self.assertEqual(complete["failure_behavior"]["warning_like_line_count"], 2)
        self.assertEqual(complete["failure_behavior"]["error_like_line_count"], 2)
        self.assertEqual(complete["failure_behavior"]["log_audit_status"], "observed")
        self.assertGreaterEqual(len(complete["checksums"]["entries"]), 4)

        self.assertEqual(incomplete["run_root_status"], "incomplete_run_root")
        self.assertEqual(incomplete["report_status"], "incomplete_run_root")
        self.assertEqual(incomplete["checksums"]["status"], "blocked_missing_inputs")
        self.assertEqual(incomplete["manifest_pressure"]["status"], "blocked_missing_inputs")
        self.assertEqual(incomplete["failure_behavior"]["status"], "incomplete_run_root")
        self.assertIn("incomplete", incomplete["report_summary"])


if __name__ == "__main__":
    unittest.main()
