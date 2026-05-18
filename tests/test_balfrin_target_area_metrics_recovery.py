from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "recover_balfrin_target_area_metrics_from_run_root.py"
SPEC = importlib.util.spec_from_file_location("recover_balfrin_target_area_metrics_from_run_root", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinTargetAreaMetricsRecoveryTests(unittest.TestCase):
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

    def _blocked_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "blocked_ssh_unavailable",
            "ready_for_read_only_collection": False,
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [
                {"name": "ssh_availability", "status": "fail", "returncode": 255},
            ],
        }

    def test_complete_fixture_recovers_all_target_area_gap_metrics(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        report = MODULE.build_report(access_report=self._ready_access(), local_run_root=run_root)

        self.assertEqual(report["schema_version"], "balfrin_target_area_metrics_recovery_v1")
        self.assertEqual(report["report_status"], "complete_gap_closed")
        self.assertEqual(report["recovery"]["status_counts"], {"recovered": 5})
        self.assertEqual(report["recovery"]["unrecovered_metrics"], [])
        self.assertEqual(report["rerun_comparison"]["status"], "rerun_not_necessary_for_required_metrics")
        self.assertFalse(report["rerun_comparison"]["rerun_still_necessary"])
        self.assertEqual(report["rerun_comparison"]["current_rerun_package_closure_targets"], MODULE.REQUIRED_RECOVERY_METRICS)
        self.assertFalse(report["claim_boundaries"]["live_submission_authorized"])

    def test_incomplete_fixture_keeps_target_area_metrics_still_missing(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root"

        report = MODULE.build_report(access_report=self._ready_access(), local_run_root=run_root)

        self.assertEqual(report["report_status"], "rerun_still_required")
        self.assertEqual(report["recovery"]["status_counts"], {"still_missing": 5})
        self.assertEqual(report["rerun_comparison"]["status"], "rerun_still_required")
        self.assertTrue(report["rerun_comparison"]["rerun_still_necessary"])
        self.assertEqual(report["rerun_comparison"]["unrecovered_metrics"], MODULE.REQUIRED_RECOVERY_METRICS)
        self.assertIn("validation_output.file_count", report["recovery"]["by_metric"])

    def test_precollected_read_only_values_recover_without_collector_statuses(self) -> None:
        evidence = {
            "schema_version": "balfrin_preserved_run_root_remote_snapshot_v1",
            "run_root": "/scratch/mch/olifu/rust_rockfall/probes/target/run",
            "run_root_status": "measured_run_root",
            "memory_peak_mb": 200.88671875,
            "validation_output_file_count": 123,
            "validation_output_bytes": 34476866,
            "hazard_output_file_count": 98,
            "hazard_output_bytes": 273191876,
            "recovery_metric_sources": {
                "memory_peak_mb": "sacct.MaxRSS",
                "validation_output.file_count": "command_plan.validation_output_paths",
                "validation_output.bytes": "command_plan.validation_output_paths",
                "hazard_output.file_count": "command_plan.output_dir",
                "hazard_output.bytes": "command_plan.output_dir",
            },
        }

        report = MODULE.build_report(access_report=self._ready_access(), evidence=evidence)

        self.assertEqual(report["report_status"], "complete_gap_closed")
        self.assertEqual(report["recovery"]["status_counts"], {"recovered": 5})
        self.assertEqual(report["recovery"]["by_metric"]["memory_peak_mb"]["collector_source"], "sacct.MaxRSS")
        self.assertFalse(report["rerun_comparison"]["rerun_still_necessary"])

    def test_access_blocked_fails_closed_without_remote_collection(self) -> None:
        report = MODULE.build_report(access_report=self._blocked_access())

        self.assertEqual(report["report_status"], "blocked_access")
        self.assertEqual(report["collection"]["status"], "not_run")
        self.assertEqual(report["recovery"]["status_counts"], {"blocked_access": 5})
        self.assertIsNone(report["rerun_comparison"]["rerun_still_necessary"])
        self.assertEqual(report["rerun_comparison"]["current_rerun_package_preflight_status"], "blocked_ssh_unavailable")
        for metric in MODULE.REQUIRED_RECOVERY_METRICS:
            self.assertEqual(report["recovery"]["by_metric"][metric]["status"], "blocked_access")

    def test_cli_writes_recovery_artifacts_from_local_fixture(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            access_json = tmp / "access.json"
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_target_area_metrics_recovery_v1"
            access_json.write_text(json.dumps(self._ready_access()), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--balfrin-access-json",
                        str(access_json),
                        "--local-run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_target_area_metrics_recovery_v1.json"
            text_path = artifact_dir / "balfrin_target_area_metrics_recovery_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["report_status"], "complete_gap_closed")
            self.assertIn("Balfrin Target-Area Metrics Recovery", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
