from __future__ import annotations

import importlib.util
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
        self.assertIn("fixture-backed recovery evidence only", report["explicit_limits"][0])

    def test_measured_override_classifies_as_measured(self) -> None:
        report = recovery.build_report(
            {
                "evidence_type": "measured",
                "partial_state": {"status": "partial"},
                "resume_commands": ["resume"],
                "recovery_outcome": {
                    "reused_chunks": ["trajectory/chunk_000000"],
                    "executed_chunks": ["trajectory/chunk_000001"],
                    "reused_chunk_counts": {"trajectory": 1},
                    "executed_chunk_counts": {"trajectory": 1},
                    "numerical_artifact_stability": {"classification": "pass_hash_stable", "changed_artifact_count": 0, "changed_paths": []},
                },
                "artifact_hygiene": {"classification": "pass_clean"},
            }
        )

        self.assertEqual(report["recovery_status"], "measured")
        self.assertEqual(report["reused_chunks"], ["trajectory/chunk_000000"])
        self.assertEqual(report["executed_chunks"], ["trajectory/chunk_000001"])

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


if __name__ == "__main__":
    unittest.main()
