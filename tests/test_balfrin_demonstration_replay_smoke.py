from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_demonstration_replay_smoke.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_demonstration_replay_smoke", SCRIPT_PATH)
assert SPEC is not None
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(smoke)


class BalfrinDemonstrationReplaySmokeTests(unittest.TestCase):
    def test_present_run_root_replays_bundle_and_gate_outputs(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_smoke_artifacts"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = smoke.main(
                    [
                        "--run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["schema_version"], "balfrin_demonstration_replay_smoke_v1")
            self.assertEqual(report["smoke_status"], "replayable")
            self.assertEqual(report["run_root_status"], "present")
            self.assertEqual(report["run_root_provenance"], "fixture_backed")
            self.assertEqual(report["replay_tier_recommendation"]["recommended_replay_tier"], "rebuildable_reduced")
            self.assertEqual(report["replay_tier_recommendation"]["recommended_output_tier"], "rebuildable_reduced_output")
            self.assertEqual(
                report["replay_tier_recommendation"]["recommendation_status"],
                "supported_by_current_evidence",
            )
            self.assertEqual(report["replay_tier_recommendation"]["missing_output_follow_up"], [])
            self.assertEqual(report["output_tier_audit_report"]["rebuildability_status"], "sufficient")
            self.assertEqual(
                report["output_tier_audit_report"]["rebuildability_classification"],
                "rebuildable_reduced_output",
            )
            self.assertEqual(report["bundle_status"], report["bundle_report"]["bundle_status"])
            self.assertEqual(
                report["post_run_interpretation_status"],
                report["post_run_interpretation_gate_report"]["interpretation_status"],
            )
            self.assertTrue((artifact_dir / "balfrin_demonstration_replay_smoke_v1.json").exists())
            self.assertTrue((artifact_dir / "balfrin_demonstration_replay_smoke_v1.txt").exists())
            self.assertTrue((artifact_dir / "balfrin_evidence_bundle_v1.json").exists())
            self.assertTrue((artifact_dir / "balfrin_post_run_interpretation_gate_v1.json").exists())
            self.assertEqual(report["missing_inputs"], [])

    def test_present_non_fixture_run_root_is_classified_as_live_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "balfrin_live_run_root"
            run_root.mkdir(parents=True)

            artifact_dir = Path(tmpdir) / "balfrin_smoke_artifacts"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = smoke.main(
                    [
                        "--run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 2)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["run_root_status"], "present")
            self.assertEqual(report["run_root_provenance"], "live_run_root")
            self.assertEqual(report["smoke_status"], "blocked_missing_inputs")
            self.assertEqual(
                report["replay_tier_recommendation"]["recommendation_status"],
                "blocked_missing_inputs",
            )
            self.assertGreater(len(report["replay_tier_recommendation"]["missing_output_follow_up"]), 0)
            self.assertGreater(len(report["missing_inputs"]), 0)

    def test_missing_run_root_fails_closed(self) -> None:
        missing_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/does-not-exist"

        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_smoke_artifacts"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = smoke.main(
                    [
                        "--run-root",
                        str(missing_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "text",
                    ]
                )

            self.assertEqual(exit_code, 2)
            text = buffer.getvalue()
            self.assertIn("Balfrin Demonstration Replay Smoke", text)
            self.assertIn("blocked_missing_inputs", text)
            self.assertIn(str(missing_root), text)
            smoke_report = json.loads((artifact_dir / "balfrin_demonstration_replay_smoke_v1.json").read_text(encoding="utf-8"))
            self.assertEqual(smoke_report["smoke_status"], "blocked_missing_inputs")
            self.assertEqual(smoke_report["run_root_status"], "missing")
            self.assertEqual(smoke_report["run_root_provenance"], "missing")
            self.assertEqual(smoke_report["missing_inputs"], [str(missing_root)])
            self.assertEqual(
                smoke_report["replay_tier_recommendation"]["recommendation_status"],
                "blocked_missing_inputs",
            )
            self.assertEqual(
                json.loads((artifact_dir / "balfrin_post_run_interpretation_gate_v1.json").read_text(encoding="utf-8"))["interpretation_status"],
                "blocked_missing_inputs",
            )

    def test_replay_tier_recommendation_preserves_output_tier_with_metric_follow_up(self) -> None:
        output_tier_report = {
            "evidence_provenance_status": "blocked_missing_inputs",
            "rebuildability_status": "blocked_missing_measured_output",
            "rebuildability_classification": "blocked_missing_measured_output",
            "blocked_reasons": ["memory_peak_mb"],
            "metrics_contract_missing_metrics": ["memory_peak_mb"],
            "required_family_counts_status": {
                "map_package_manifest": True,
                "pilot_gis_package_manifest": True,
                "trajectory_chunk_manifest": True,
                "reducer_chunk_manifest": True,
            },
            "curve_availability": {"available": True, "row_count": 729600},
        }

        recommendation = smoke.build_replay_tier_recommendation(
            smoke_status="blocked_missing_inputs",
            output_tier_report=output_tier_report,
        )

        self.assertEqual(recommendation["recommended_replay_tier"], "rebuildable_reduced")
        self.assertEqual(
            recommendation["recommendation_status"],
            "supported_by_replay_outputs_with_metric_follow_up",
        )
        self.assertEqual(recommendation["missing_output_follow_up"], [])
        self.assertEqual(recommendation["missing_metric_follow_up"], ["memory_peak_mb"])


if __name__ == "__main__":
    unittest.main()
