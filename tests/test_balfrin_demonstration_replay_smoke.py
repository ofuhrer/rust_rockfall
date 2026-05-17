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
                json.loads((artifact_dir / "balfrin_post_run_interpretation_gate_v1.json").read_text(encoding="utf-8"))["interpretation_status"],
                "blocked_missing_inputs",
            )


if __name__ == "__main__":
    unittest.main()
