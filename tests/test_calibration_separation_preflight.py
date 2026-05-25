from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import check_calibration_separation_preflight as preflight


class CalibrationSeparationPreflightTests(unittest.TestCase):
    def test_default_preflight_keeps_calibration_diagnostic(self) -> None:
        report = preflight.build_report()

        self.assertEqual(report["schema_version"], preflight.SCHEMA_VERSION)
        self.assertEqual(report["preflight_status"], "passed")
        self.assertGreaterEqual(report["calibration_artifact_count"], 1)
        self.assertGreaterEqual(report["validation_case_count"], 1)
        self.assertEqual(report["prohibited_crossings"], [])
        self.assertEqual(report["failure_replay"]["status"], "not_triggered")
        self.assertFalse(report["failure_replay"]["tuning_performed"])
        self.assertTrue(report["separation_summary"]["calibration_records_are_diagnostic"])
        self.assertFalse(report["separation_summary"]["selected_parameters_promoted_to_validation"])
        self.assertFalse(report["claim_boundaries"]["selected_parameters_promoted"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_forbidden_validation_reference_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calibration_root = root / "calibration"
            experiment = calibration_root / "experiments" / "example"
            experiment.mkdir(parents=True)
            (experiment / "selected_parameters.yaml").write_text(
                "\n".join(
                    [
                        "experiment_id: example",
                        "dataset_id: fixture",
                        "limitations:",
                        "- not validation",
                    ]
                ),
                encoding="utf-8",
            )
            validation_root = root / "validation" / "cases"
            validation_root.mkdir(parents=True)
            (validation_root / "bad_case.yaml").write_text(
                "\n".join(
                    [
                        "case_id: bad_case",
                        "model:",
                        "  selected_parameters_path: calibration/experiments/example/selected_parameters.yaml",
                    ]
                ),
                encoding="utf-8",
            )

            report = preflight.build_report(calibration_root=calibration_root, validation_case_root=validation_root)

        self.assertEqual(report["preflight_status"], "blocked_forbidden_validation_reference")
        self.assertEqual(len(report["prohibited_crossings"]), 2)
        self.assertEqual(report["failure_replay"]["status"], "blocked")
        self.assertEqual(report["failure_replay"]["classification"], "invalid_calibration_validation_coupling")
        self.assertEqual(report["failure_replay"]["invalid_coupling_count"], 2)
        self.assertFalse(report["failure_replay"]["tuning_performed"])
        self.assertFalse(report["failure_replay"]["validation_acceptance_upgrade_allowed"])
        self.assertIn("selected_parameters_path", report["failure_replay"]["missing_evidence_or_invalid_coupling"])
        self.assertTrue(report["separation_summary"]["selected_parameters_promoted_to_validation"])

    def test_text_report_names_artifacts_and_boundaries(self) -> None:
        text = preflight.render_text_report(preflight.build_report())

        self.assertIn("preflight_status: passed", text)
        self.assertIn("diagnostic_non_default", text)
        self.assertIn("prohibited_crossings:", text)
        self.assertIn("operational_claims_allowed: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
