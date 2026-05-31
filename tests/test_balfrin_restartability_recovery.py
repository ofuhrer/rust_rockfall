from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_restartability_recovery.py"
FIXTURE_PATH = ROOT / "tests/fixtures/balfrin_restartability_recovery/fixture_v1.json"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_restartability_recovery", SCRIPT_PATH)
assert SPEC is not None
recovery = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recovery)


class BalfrinRestartabilityRecoveryTests(unittest.TestCase):
    def test_fixture_backed_recovery_classifies_as_fixture_proven(self) -> None:
        report = recovery.build_report()

        self.assertEqual(report["schema_version"], "balfrin_restartability_recovery_v1")
        self.assertEqual(report["recovery_status"], "fixture_proven")
        self.assertEqual(report["evidence_status"], "fixture")
        self.assertEqual(report["reused_chunks"], ["trajectory/chunk_000000", "reducer/chunk_000000"])
        self.assertEqual(report["executed_chunks"], ["trajectory/chunk_000001", "reducer/chunk_000001"])
        self.assertEqual(report["numerical_artifact_stability"]["classification"], "pass_hash_stable")
        self.assertEqual(report["numerical_artifact_stability"]["changed_artifact_count"], 0)
        self.assertEqual(report["artifact_hygiene"]["classification"], "pass_clean")
        self.assertEqual(report["rerun_fraction_summary"]["total_chunks"], 4)
        self.assertEqual(report["rerun_fraction_summary"]["rerun_fraction"], 0.5)
        self.assertEqual(report["preserved_artifact_summary"]["changed_artifact_count"], 0)
        self.assertIn("fixture-backed recovery evidence only", report["explicit_limits"][0])

    def test_measured_override_classifies_as_measured(self) -> None:
        report = recovery.build_report(
            {
                "evidence_type": "measured",
                "partial_state": {"status": "partial"},
                "recovery_timing": {
                    "interrupted_job_id": 4325958,
                    "interrupted_cancelled_at": "2026-05-17T01:08:36",
                    "resumed_job_id": 4326021,
                    "resumed_started_at": "2026-05-17T01:17:26",
                    "resume_gap_seconds": 530,
                    "recovered_job_elapsed": "00:00:06",
                    "merge_job_elapsed": "00:01:01",
                },
                "resume_commands": ["resume"],
                "recovery_outcome": {
                    "reused_chunks": ["trajectory/chunk_000000"],
                    "executed_chunks": ["trajectory/chunk_000001"],
                    "reused_chunk_counts": {"trajectory": 1},
                    "executed_chunk_counts": {"trajectory": 1},
                    "numerical_artifact_stability": {
                        "classification": "pass_hash_stable",
                        "baseline_file_count": 37,
                        "recovered_file_count": 37,
                        "changed_artifact_count": 0,
                        "changed_paths": [],
                    },
                },
                "artifact_continuity": {
                    "trajectory_merge_state": "ready",
                    "reducer_merge_state": "ready",
                },
                "artifact_hygiene": {"classification": "pass_clean"},
            }
        )

        self.assertEqual(report["recovery_status"], "measured")
        self.assertEqual(report["reused_chunks"], ["trajectory/chunk_000000"])
        self.assertEqual(report["executed_chunks"], ["trajectory/chunk_000001"])
        self.assertEqual(report["recovery_timing"]["interrupted_job_id"], 4325958)
        self.assertEqual(report["rerun_fraction_summary"]["rerun_fraction"], 0.5)
        self.assertEqual(report["recovery_elapsed_summary"]["total_elapsed_seconds"], 67)
        self.assertEqual(report["preserved_artifact_summary"]["stable_artifact_count"], 37)
        self.assertEqual(report["artifact_continuity"]["reducer_merge_state"], "ready")
        rendered = recovery.render_text_report(report)
        self.assertIn("Recovery Timing", rendered)
        self.assertIn("Artifact Continuity", rendered)
        self.assertIn("Rerun fraction summary", rendered)

    def test_missing_inputs_are_reported_as_blocked_missing_inputs(self) -> None:
        report = recovery.build_report({"missing_inputs": ["partial_state", "resume_commands"]})

        self.assertEqual(report["recovery_status"], "blocked_missing_inputs")
        self.assertEqual(report["evidence_status"], "blocked_missing_inputs")
        self.assertEqual(report["resume_commands"], [])
        self.assertIn("partial_state", report["explicit_limits"])
        self.assertIn("resume_commands", report["explicit_limits"])

    def test_cli_can_write_json_and_text_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            json_output = tmp / "recovery.json"
            text_output = tmp / "recovery.md"

            exit_code = recovery.main(
                [
                    "--evidence-json",
                    str(FIXTURE_PATH),
                    "--json-output",
                    str(json_output),
                    "--text-output",
                    str(text_output),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(json_output.exists())
            self.assertTrue(text_output.exists())
            self.assertIn("Balfrin Restartability Recovery Report", text_output.read_text(encoding="utf-8"))

    def test_largest_hazard_run_recovery_compares_payload_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source"
            recovered = tmp / "recovered"
            for root in (source, recovered):
                write_largest_run_fixture(root)

            report = recovery.build_largest_hazard_run_recovery_report(
                source_run_root=source,
                recovered_run_root=recovered,
                job_id="4379371",
                release_zones=384,
            )

            self.assertEqual(report["schema_version"], "balfrin_largest_hazard_run_recovery_v1")
            self.assertEqual(report["recovery_status"], "measured")
            self.assertTrue(report["manifest_comparison"]["checksum_match"])
            self.assertEqual(report["mandatory_artifacts"]["missing"], [])
            self.assertEqual(report["regenerated_metrics"]["release_zone_count"], 384)
            self.assertEqual(report["regenerated_metrics"]["output_bytes"], 1536400)
            self.assertTrue(
                report["replay_critical_artifacts"]["sufficient_for_copy_inspection_and_metric_regeneration"]
            )
            self.assertEqual(report["support_limit"]["classification"], "output_budget_blocked")
            self.assertIn("Largest Hazard Run Recovery", recovery.render_report(report))

    def test_largest_hazard_run_recovery_reports_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source"
            recovered = tmp / "recovered"
            for root in (source, recovered):
                write_largest_run_fixture(root)
            (recovered / "tb682_time.txt").unlink()

            report = recovery.build_largest_hazard_run_recovery_report(
                source_run_root=source,
                recovered_run_root=recovered,
                job_id="4379371",
                release_zones=384,
            )

            self.assertEqual(report["recovery_status"], "blocked_missing_inputs")
            self.assertIn("tb682_time.txt", report["mandatory_artifacts"]["missing"])
            self.assertEqual(
                report["replay_critical_artifacts"]["first_blocker"],
                "missing mandatory artifact: tb682_time.txt",
            )


def write_largest_run_fixture(root: Path) -> None:
    profile_path = root / "tb682_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "profile_id": "multi_zone_384_zone_custom",
                "fixture": {
                    "release_zone_count": 384,
                    "trajectory_file_count": 384,
                    "impact_file_count": 384,
                },
                "profile_scale": {
                    "output_file_count": 29,
                    "output_bytes": 1536400,
                    "hazard_layer_seconds": 0.3593194429995492,
                    "total_wall_seconds": 0.5879617109894753,
                },
                "larger_than_four_zone_package_profile": {
                    "local_pre_submit_proof": {
                        "manifest_size_bytes": 325518,
                        "first_blocker": "within_output_byte_budget",
                        "blockers": [
                            "within_output_byte_budget",
                            "within_manifest_byte_budget",
                        ],
                        "replay_critical_coverage": {"complete": True},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    for relative in [
        "tb682_profile.md",
        "tb682_time.txt",
        "tb682_pressure.sbatch",
        "tb682_du_bytes.txt",
        "tb682_files.txt",
        "profile/input/multi_zone_hazard_profile_fixture_manifest.json",
        "profile/output/explicit/hazard/multi_zone_hazard_profile_manifest.json",
        "profile/output/explicit/hazard/multi_zone_hazard_profile_execution_plan_v1.json",
        "profile/output/explicit/hazard/multi_zone_hazard_profile_reducer_execution_index_v1.json",
        "profile/output/explicit/hazard/multi_zone_hazard_profile_reducer_merge_state_v1.json",
        "slurm-4379371.out",
        "slurm-4379371.err",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{relative}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
