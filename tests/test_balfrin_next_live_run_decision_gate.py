from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_next_live_run_decision_gate.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_next_live_run_decision_gate", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

FIXTURE_ROOT = ROOT / "tests/fixtures/balfrin_next_live_run_decision_gate"


class BalfrinNextLiveRunDecisionGateTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def test_ready_fixture_prefers_metrics_completion_rerun(self) -> None:
        report = MODULE.build_report(self.load_fixture("default_bundle.json"))

        self.assertEqual(report["schema_version"], "balfrin_next_live_run_decision_gate_v1")
        self.assertEqual(report["decision_status"], "ready")
        self.assertEqual(report["recommended_next_action"]["action_id"], "metrics_completion_rerun")
        self.assertEqual(report["recommended_next_action"]["classification"], "ready")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-206")
        self.assertEqual(report["next_follow_up_package_task"], "TB-206")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "ready")
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["status"], "missing")
        self.assertEqual(report["criteria"]["preservation_gate_readiness"]["status"], "ready")
        self.assertIn("metrics rerun", report["decision_summary"])
        self.assertIn("missing target-area metrics", report["recommended_next_action"]["summary"].lower())
        rendered = MODULE.render_text_report(report)
        self.assertIn("Balfrin Next Live-Run Decision Gate", rendered)
        self.assertIn("metrics_completion_rerun", rendered)
        self.assertIn("smallest_bounded_multi_zone_probe", rendered)
        self.assertIn("defer_portability_or_physical_evidence", rendered)

    def test_missing_inputs_fixture_fails_closed(self) -> None:
        report = MODULE.build_report(self.load_fixture("blocked_bundle.json"))

        self.assertEqual(report["decision_status"], "blocked")
        self.assertEqual(report["recommended_next_action"]["classification"], "blocked")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-206")
        self.assertIn("missing", report["blocked_reason"])
        self.assertEqual(report["evidence_sources"]["probe_metrics_report"], None)
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["defer_portability_or_physical_evidence"]["status"], "blocked")

    def test_defer_fixture_prefers_portability_or_physical_evidence_work(self) -> None:
        report = MODULE.build_report(self.load_fixture("defer_bundle.json"))

        self.assertEqual(report["decision_status"], "defer")
        self.assertEqual(report["recommended_next_action"]["action_id"], "defer_portability_or_physical_evidence")
        self.assertEqual(report["recommended_next_action"]["classification"], "defer")
        self.assertEqual(report["recommended_next_action"]["follow_up_task"], "TB-207")
        self.assertEqual(report["option_assessments"]["metrics_completion_rerun"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["smallest_bounded_multi_zone_probe"]["status"], "blocked")
        self.assertEqual(report["option_assessments"]["defer_portability_or_physical_evidence"]["status"], "defer")
        self.assertEqual(report["criteria"]["missing_target_area_metrics"]["status"], "complete")
        self.assertEqual(report["criteria"]["multi_zone_package_readiness"]["status"], "blocked")
        self.assertIn("portability or physical-evidence", report["recommended_next_action"]["summary"])

    def test_cli_writes_report_artifacts_from_default_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_next_live_run_decision_gate_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--evidence-json",
                        str(FIXTURE_ROOT / "default_bundle.json"),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_next_live_run_decision_gate_v1.json"
            text_path = artifact_dir / "balfrin_next_live_run_decision_gate_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["decision_status"], "ready")
            self.assertIn("Balfrin Next Live-Run Decision Gate", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
