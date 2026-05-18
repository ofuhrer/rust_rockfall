from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_authorization_gated_multi_zone_measurement_path", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _ready_access() -> dict[str, object]:
    return {
        "schema_version": "balfrin_remote_access_preflight_v1",
        "status": "ready_for_read_only_collection",
        "ready_for_read_only_collection": True,
        "read_only": True,
        "live_submission_authorized": False,
    }


def _blocked_access() -> dict[str, object]:
    return {
        "schema_version": "balfrin_remote_access_preflight_v1",
        "status": "blocked_ssh_unavailable",
        "ready_for_read_only_collection": False,
        "read_only": True,
        "live_submission_authorized": False,
    }


def _preflight(status: str = "ready_for_authorization_review") -> dict[str, object]:
    return {
        "schema_version": "balfrin_smallest_multi_zone_probe_authorization_preflight_v1",
        "status": status,
        "preflight_status": status,
        "submission_gate_status": status,
        "ready_for_authorization_review": status == "ready_for_authorization_review",
        "ready_for_authorized_submission": status == "ready_for_authorization_review",
        "authorization_granted_by_preflight": False,
        "live_submission_authorized": False,
        "blocked_reason": "" if status == "ready_for_authorization_review" else "fixture blocker",
        "authorization_status": "authorized" if status == "ready_for_authorization_review" else status,
        "reviewed_handoff_package_status": "reviewed",
        "authorization_record_status": "reviewed" if status == "ready_for_authorization_review" else "missing",
        "reviewed_handoff_package_sha256": "reviewed-sha",
        "authorization_record_sha256": "auth-sha" if status == "ready_for_authorization_review" else None,
        "balfrin_access_status": "ready_for_read_only_collection",
        "reviewed_handoff_package_path": "/tmp/reviewed_package.json",
        "authorization_record_path": "/tmp/authorization_record.yaml",
        "smallest_multi_zone_run_shape": {
            "release_zone_count": 2,
            "scenario_count": 2,
            "trajectory_count_target": 1000,
            "authorization_submit_command": (
                "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py manifest.yaml "
                "--run-root /scratch/rust_rockfall/probes/balfrin-demo/test "
                "--authorized-submit --reviewed-handoff-package /tmp/reviewed_package.json "
                "--authorization-record /tmp/authorization_record.yaml"
            ),
        },
    }


class BalfrinAuthorizationGatedMultiZoneMeasurementPathTests(unittest.TestCase):
    def test_ready_preflight_binds_exact_checklist_without_submission(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            preflight_path = Path(tmpdir) / "preflight.json"
            preflight_path.write_text(json.dumps(_preflight(), indent=2), encoding="utf-8")
            report = MODULE.build_report(
                json.loads(preflight_path.read_text(encoding="utf-8")),
                preflight_path=preflight_path,
            )

        self.assertEqual(report["path_status"], "pending_authorized_post_run")
        self.assertTrue(report["ready_for_authorized_execution_path"])
        self.assertFalse(report["ready_for_measured_evidence_promotion"])
        self.assertFalse(report["submit_command_executed"])
        checklist = {entry["id"]: entry for entry in report["authorization_gated_execution_checklist"]}
        self.assertEqual(checklist["authorization_preflight_output"]["path"], str(preflight_path))
        self.assertEqual(checklist["reviewed_handoff_package"]["path"], "/tmp/reviewed_package.json")
        self.assertEqual(checklist["authorization_record"]["path"], "/tmp/authorization_record.yaml")
        self.assertIn("--authorized-submit", checklist["authorized_submit_command"]["command"])
        self.assertIn("collect_balfrin_probe_metrics.py", checklist["post_run_metrics_collector"]["command"])
        self.assertIn("summarize_balfrin_demonstration_closure_package.py", checklist["closure_package_input"]["command"])

    def test_missing_authorization_blocks_before_evidence_promotion(self) -> None:
        report = MODULE.build_report(_preflight("blocked_missing_authorization"))

        self.assertEqual(report["path_status"], "blocked_pre_authorization")
        self.assertFalse(report["ready_for_authorized_execution_path"])
        self.assertFalse(report["ready_for_measured_evidence_promotion"])
        self.assertEqual(report["blocked_report"]["status"], "blocked_missing_authorization")
        self.assertIn("authorization_record:missing", report["blocked_report"]["blocked_reasons"])
        self.assertEqual(report["post_run_evidence_gate"]["collector_status"], "not_checked_preflight_blocked")

    def test_incomplete_run_root_cannot_be_promoted_to_measured_evidence(self) -> None:
        report = MODULE.build_report(
            _preflight(),
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root",
            access_report=_ready_access(),
        )

        self.assertEqual(report["path_status"], "pending_authorized_post_run")
        self.assertEqual(report["post_run_evidence_gate"]["collector_status"], "blocked_incomplete_run_root")
        self.assertEqual(
            report["post_run_evidence_gate"]["closure_input_compatibility"]["status"],
            "blocked_missing_inputs",
        )
        self.assertFalse(report["ready_for_measured_evidence_promotion"])
        self.assertFalse(report["measured_result_promoted"])

    def test_access_loss_cannot_be_promoted_to_measured_evidence(self) -> None:
        preflight = _preflight("blocked_access")
        preflight["balfrin_access_status"] = "blocked_ssh_unavailable"
        report = MODULE.build_report(
            preflight,
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            access_report=_blocked_access(),
        )

        self.assertEqual(report["path_status"], "blocked_pre_authorization")
        self.assertFalse(report["ready_for_measured_evidence_promotion"])
        self.assertEqual(report["post_run_evidence_gate"]["collector_status"], "not_checked_preflight_blocked")
        self.assertIn("balfrin_access:blocked_ssh_unavailable", report["blocked_report"]["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
