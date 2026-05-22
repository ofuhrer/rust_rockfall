from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_SCRIPT_PATH = ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py"
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_regional_split_submission_package.py"
TB432_STALE_COMMAND_PLAN_PATHS = [
    "validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/"
    "four_zone_review_only/handoff_output_budget_projection_compact_root/command_plan.json",
    "validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/"
    "four_zone_review_only/handoff_output_budget_projection_full_root/command_plan.json",
    "validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/"
    "handoff_output_budget_projection_full_root/command_plan.json",
]
SCENARIO_SPEC = importlib.util.spec_from_file_location("generate_candidate_source_zone_scenarios", SCENARIO_SCRIPT_PATH)
SPEC = importlib.util.spec_from_file_location("generate_balfrin_regional_split_submission_package", SCRIPT_PATH)
assert SCENARIO_SPEC is not None
SCENARIO_MODULE = importlib.util.module_from_spec(SCENARIO_SPEC)
assert SCENARIO_SPEC.loader is not None
SCENARIO_SPEC.loader.exec_module(SCENARIO_MODULE)
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

    def _tb432_dirty_access(self) -> dict[str, object]:
        access = dict(self._ready_access())
        access.update(
            {
                "status": "blocked_dirty_remote_checkout",
                "ready_for_read_only_collection": False,
                "ready_for_pre_submit": False,
                "remote_checkout_hygiene": {
                    "status": "fail",
                    "remote_head": "tb432-stale-head",
                    "tracked_modifications": [],
                    "untracked_generated_files": TB432_STALE_COMMAND_PLAN_PATHS,
                    "stale_submission_packages": TB432_STALE_COMMAND_PLAN_PATHS,
                    "stale_logs": [],
                    "dirty_path_count": 3,
                    "safe_cleanup_commands": [],
                },
            }
        )
        return access

    def test_default_package_fails_closed_when_access_preflight_is_not_supplied(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            report = MODULE.build_report(artifact_dir=artifact_dir)
            MODULE.materialize_artifacts(report)
            text = (artifact_dir / "balfrin_regional_split_submission_package_v1.txt").read_text(
                encoding="utf-8"
            )

        self.assertEqual(report["schema_version"], "balfrin_regional_split_submission_package_v1")
        self.assertEqual(report["submission_package_status"], "failed_closed_preflight")
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertEqual(report["scratch_package_freshness"]["status"], "ready_clean_scratch")
        self.assertTrue(report["scratch_package_freshness"]["fresh"])
        self.assertEqual(report["authorization_preflight_status"], "blocked_access")
        self.assertEqual(
            report["authorization_preflight"]["balfrin_access_status"],
            "blocked_balfrin_access_not_checked",
        )
        self.assertEqual(report["regional_split_merge_contract"]["status"], "ready")
        self.assertEqual(report["regional_split_merge_contract"]["split_count"], 12)
        self.assertEqual(report["writable_remote_roots"]["status"], "ready")
        self.assertEqual(report["output_budget"]["status"], "ready")
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

        self.assertEqual(report["submission_package_status"], "ready_for_bounded_postproc_submission")
        self.assertTrue(report["ready_for_bounded_postproc_submission"])
        self.assertIsNone(report["first_blocker"])
        self.assertEqual(report["generation_inputs"]["balfrin_remote_head"], "abc123")
        self.assertEqual(report["generation_inputs"]["balfrin_access_preflight_path"], "fixture")
        self.assertEqual(report["scratch_package_freshness"]["status"], "ready_clean_scratch")
        self.assertEqual(report["remote_head_alignment"]["status"], "not_checked_fixture_or_missing_preflight")
        self.assertEqual(report["compact_manifest_freshness"]["status"], "ready_compact_manifest_current")
        self.assertEqual(report["compact_manifest_freshness"]["manifest_mode"], "compact")
        self.assertEqual(report["authorization_preflight_status"], "ready_for_authorization_review")
        self.assertEqual(
            report["writable_remote_roots"]["run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
        )
        self.assertEqual(report["writable_remote_roots"]["writability_status"], "reviewed_balfrin_scratch_root")
        self.assertEqual(report["output_budget"]["status"], "ready")
        self.assertEqual(report["output_budget"]["acceptance_status"], "accepted")
        self.assertEqual(report["output_budget"]["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertIn("scripts/submit_balfrin_probe.py", report["exact_bounded_postproc_command"])
        self.assertIn("--partition postproc", report["exact_bounded_postproc_command"])
        self.assertIn("--authorized-submit", report["exact_bounded_postproc_command"])
        self.assertNotIn("sbatch ", report["exact_bounded_postproc_command"])
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])

    def test_file_backed_ready_access_fails_closed_when_remote_head_is_not_local_head(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            with patch.object(MODULE, "local_git_head", return_value="local-head"):
                report = MODULE.build_report(
                    artifact_dir=artifact_dir,
                    balfrin_access_preflight=self._ready_access(),
                    balfrin_access_preflight_source="/tmp/current_access.json",
                )

        self.assertEqual(report["submission_package_status"], "failed_closed_remote_head_mismatch")
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertEqual(report["first_blocker"]["gate"], "remote_head_alignment")
        self.assertEqual(report["remote_head_alignment"]["status"], "blocked_remote_head_mismatch")
        self.assertEqual(report["remote_head_alignment"]["remote_head"], "abc123")
        self.assertEqual(report["remote_head_alignment"]["local_head"], "local-head")
        self.assertEqual(report["compact_manifest_freshness"]["status"], "ready_compact_manifest_current")

    def test_file_backed_ready_access_records_remote_head_alignment(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            with patch.object(MODULE, "local_git_head", return_value="abc123"):
                report = MODULE.build_report(
                    artifact_dir=artifact_dir,
                    balfrin_access_preflight=self._ready_access(),
                    balfrin_access_preflight_source="/tmp/current_access.json",
                )

        self.assertEqual(report["submission_package_status"], "ready_for_bounded_postproc_submission")
        self.assertEqual(report["remote_head_alignment"]["status"], "ready_remote_head_aligned")
        self.assertTrue(report["remote_head_alignment"]["aligned"])
        self.assertEqual(report["generation_inputs"]["local_package_source_head"], "abc123")

    def test_tb432_dirty_preflight_fixture_fails_closed_without_silent_reuse(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            report = MODULE.build_report(
                artifact_dir=artifact_dir,
                balfrin_access_preflight=self._tb432_dirty_access(),
                balfrin_access_preflight_source="/tmp/tb432_balfrin_access_preflight.json",
            )

        self.assertEqual(report["submission_package_status"], "failed_closed_preflight")
        self.assertFalse(report["ready_for_bounded_postproc_submission"])
        self.assertEqual(report["first_blocker"]["gate"], "authorization_preflight")
        self.assertIn("blocked_dirty_remote_checkout", report["first_blocker"]["reason"])
        access_requirement = report["authorization_preflight"]["balfrin_access_preflight_requirement"]
        self.assertEqual(access_requirement["source"], "/tmp/tb432_balfrin_access_preflight.json")
        self.assertEqual(access_requirement["consumed_status"], "blocked_dirty_remote_checkout")
        self.assertEqual(
            access_requirement["remote_checkout_hygiene"]["stale_submission_packages"],
            self._tb432_dirty_access()["remote_checkout_hygiene"]["stale_submission_packages"],
        )
        self.assertFalse(report["no_submit_semantics"]["sbatch_attempted"])
        self.assertFalse(report["no_submit_semantics"]["balfrin_job_submitted"])

    def test_stale_scratch_package_fails_closed_before_reuse(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "regional_split_package"
            old_access = self._ready_access()
            old_access["remote_head"] = "old-head"
            old_access["remote_checkout_hygiene"]["remote_head"] = "old-head"
            old_report = MODULE.build_report(
                artifact_dir=artifact_dir,
                balfrin_access_preflight=old_access,
                balfrin_access_preflight_source="/tmp/old_access.json",
            )
            MODULE.materialize_artifacts(old_report)

            fresh_report = MODULE.build_report(
                artifact_dir=artifact_dir,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="/tmp/current_access.json",
            )

        self.assertEqual(fresh_report["submission_package_status"], "failed_closed_stale_scratch_package")
        self.assertFalse(fresh_report["ready_for_bounded_postproc_submission"])
        self.assertEqual(fresh_report["first_blocker"]["gate"], "scratch_package_freshness")
        freshness = fresh_report["scratch_package_freshness"]
        self.assertEqual(freshness["status"], "blocked_stale_scratch_package")
        self.assertFalse(freshness["fresh"])
        self.assertIn("balfrin_remote_head", freshness["mismatches"][0])
        self.assertIn("preserve_before_retry.tgz", freshness["preserve_command"])
        self.assertIn("rm -rf", freshness["clean_command"])

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

    def test_batched_scenario_smoke_package_tracks_contract_without_submitting(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp_root = Path(tmpdir)
            scenario_output_root = tmp_root / "validation/private/tschamut_public_pilot/candidate_source_zone_stress_v1"
            scenario_report = SCENARIO_MODULE.build_report(
                policy_path=SCENARIO_MODULE.DEFAULT_POLICY,
                release_points_path=SCENARIO_MODULE.DEFAULT_RELEASE_POINTS,
                output_root=scenario_output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )
            smoke_artifact_dir = tmp_root / "validation/private/balfrin_scenario_batch_smoke"
            smoke_report = MODULE.build_batched_scenario_smoke_package(
                scenario_batching_contract=scenario_report["scenario_batching_contract"],
                artifact_dir=smoke_artifact_dir,
            )
            MODULE.materialize_batched_scenario_smoke_artifacts(smoke_report)
            text = Path(smoke_report["package_text_path"]).read_text(encoding="utf-8")

        self.assertEqual(smoke_report["schema_version"], "balfrin_scenario_batch_smoke_package_v1")
        self.assertEqual(smoke_report["package_status"], "ready_for_batched_scenario_smoke")
        self.assertTrue(smoke_report["ready_for_batched_scenario_smoke"])
        self.assertIsNone(smoke_report["first_blocker"])
        self.assertFalse(smoke_report["no_submit_semantics"]["sbatch_attempted"])
        self.assertFalse(smoke_report["no_submit_semantics"]["submit_command_executed"])
        self.assertTrue(smoke_report["no_submit_semantics"]["smoke_only"])
        self.assertEqual(smoke_report["scenario_batch_count"], scenario_report["scenario_batching_contract"]["batch_count"])
        self.assertEqual(smoke_report["scenario_batching_summary"]["batch_count"], 4)
        self.assertIn("Batch count: `4`", text)
        self.assertIn("package_generation_only: `True`", text)


if __name__ == "__main__":
    unittest.main()
