from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_regional_split_submission_package.py"
SPEC = importlib.util.spec_from_file_location("generate_balfrin_regional_split_submission_package", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinRegionalSplitSubmissionPackageTests(unittest.TestCase):
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
                "safe_cleanup_commands": [],
            },
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [{"name": "ssh_availability", "status": "pass"}],
        }

    def test_default_package_fails_closed_when_access_preflight_is_not_supplied(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            report = MODULE.build_report(artifact_dir=artifact_dir)
            MODULE.materialize_artifacts(report)
            text = (artifact_dir / "balfrin_regional_split_submission_package_v1.txt").read_text(
                encoding="utf-8"
            )

        self.assertEqual(report["schema_version"], "balfrin_regional_split_submission_package_v1")
        self.assertEqual(report["submission_package_status"], "failed_closed_output_budget")
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertEqual(report["authorization_preflight_status"], "blocked_reducer_budget")
        self.assertEqual(
            report["authorization_preflight"]["balfrin_access_status"],
            "blocked_balfrin_access_not_checked",
        )
        self.assertEqual(report["regional_split_merge_contract"]["status"], "ready")
        self.assertEqual(report["regional_split_merge_contract"]["split_count"], 12)
        self.assertEqual(report["writable_remote_roots"]["status"], "ready")
        self.assertEqual(report["output_budget"]["status"], "blocked_output_budget")
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])
        self.assertFalse(report["no_submit_semantics"]["submit_command_executed"])
        self.assertFalse(report["command_contract"]["contains_generate_only_flag"])
        self.assertTrue(report["command_contract"]["contains_authorized_submit_flag"])
        self.assertTrue(report["command_contract"]["no_non_postproc_partition"])
        self.assertIn("sbatch_attempted: `False`", text)

    def test_ready_access_fixture_preserves_exact_command_and_fails_closed_on_current_budget(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"

            def fail_scheduler(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                raise AssertionError("package generation must not call subprocess.run or sbatch")

            with patch.object(MODULE.preflight.submit_driver.subprocess, "run", side_effect=fail_scheduler):
                report = MODULE.build_report(
                    artifact_dir=artifact_dir,
                    balfrin_access_preflight=self._ready_access(),
                    balfrin_access_preflight_source="fixture",
                )

        self.assertEqual(report["submission_package_status"], "failed_closed_output_budget")
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertEqual(report["first_blocker"]["gate"], "output_budget")
        self.assertEqual(report["authorization_preflight_status"], "blocked_reducer_budget")
        self.assertEqual(
            report["writable_remote_roots"]["run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
        )
        self.assertEqual(report["writable_remote_roots"]["writability_status"], "reviewed_balfrin_scratch_root")
        self.assertEqual(report["output_budget"]["status"], "blocked_output_budget")
        self.assertEqual(report["output_budget"]["acceptance_status"], "blocked_threshold_exceeded")
        self.assertEqual(report["output_budget"]["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertIn("scripts/submit_balfrin_probe.py", report["exact_bounded_postproc_command"])
        self.assertIn("--partition postproc", report["exact_bounded_postproc_command"])
        self.assertIn("--authorized-submit", report["exact_bounded_postproc_command"])
        self.assertNotIn("sbatch ", report["exact_bounded_postproc_command"])
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])

    def test_missing_regional_merge_manifest_fails_closed_before_ready_package(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            handoff_artifact_dir = artifact_dir / "handoff"
            pressure_probe_root = artifact_dir / "regional_split_probe"
            handoff_report = MODULE.handoff.build_report(
                artifact_dir=handoff_artifact_dir,
                pressure_probe_root=pressure_probe_root,
            )
            merge_manifest = pressure_probe_root / MODULE.REGIONAL_MERGE_MANIFEST_RELATIVE
            merge_manifest.unlink()

            report = MODULE.build_report(
                artifact_dir=artifact_dir,
                handoff_artifact_dir=handoff_artifact_dir,
                pressure_probe_root=pressure_probe_root,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
                handoff_report_override=handoff_report,
            )

        self.assertEqual(report["submission_package_status"], "failed_closed_package_contract")
        self.assertEqual(report["package_contract_status"]["status"], "blocked_package_contract")
        self.assertEqual(report["first_blocker"]["gate"], "package_contract")
        self.assertIn("missing regional merge manifest", report["first_blocker"]["reason"])
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])


if __name__ == "__main__":
    unittest.main()
