from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_conditional_pilot_acceptance.py"
SPEC = importlib.util.spec_from_file_location("summarize_conditional_pilot_acceptance", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary_script)


class ConditionalPilotAcceptanceSummaryTests(unittest.TestCase):
    def test_selected_records_produce_inconclusive_summary(self) -> None:
        summary = summary_script.build_acceptance_summary()

        self.assertEqual(summary["final_classification"], "inconclusive")
        self.assertFalse(summary["accepted_conditional_diagnostic_pilot"])
        self.assertFalse(summary["scale_up_authorized"])
        self.assertEqual(summary["convergence_status"], "inconclusive")
        self.assertEqual(summary["output_budget_status"], "blocked_before_scale_up")
        self.assertEqual(summary["blocker_status"], "present")
        self.assertIn("validation debug-output volume remains a blocker", summary["classification_rationale"])

    def test_markdown_report_includes_key_sections(self) -> None:
        summary = summary_script.build_acceptance_summary()
        markdown = summary_script.render_markdown_report(summary)

        self.assertIn("# Measured Conditional Pilot Acceptance Summary", markdown)
        self.assertIn("Final classification: `inconclusive`", markdown)
        self.assertIn("## Remaining Unresolved", markdown)
        self.assertIn("## Evidence Records Read", markdown)

    def test_missing_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            convergence = self.load_record(ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml")
            del convergence["assessment"]["evidence"]["convergence_indicators"]
            convergence_path = self.write_record(Path(tmp), convergence)

            with self.assertRaisesRegex(summary_script.ConditionalPilotAcceptanceSummaryError, "convergence_record"):
                summary_script.build_acceptance_summary(
                    convergence_record=convergence_path,
                )

    def load_record(self, path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "record.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
