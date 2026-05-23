from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_trajectory_deposition_traceability as audit


class TrajectoryDepositionTraceabilityTests(unittest.TestCase):
    def test_default_target_package_is_traceable(self) -> None:
        report = audit.build_report()

        self.assertEqual(report["schema_version"], audit.SCHEMA_VERSION)
        self.assertEqual(report["audit_status"], "traceable")
        self.assertEqual(report["missing_or_failed_checks"], [])
        checks = {check["check_id"]: check for check in report["consistency_checks"]}
        self.assertEqual(checks["deposition_rows_match_hazard_input"]["status"], "pass")
        self.assertEqual(checks["trajectory_rows_match_hazard_input"]["status"], "pass")
        self.assertFalse(report["claim_boundaries"]["field_validation_claim_added"])
        self.assertFalse(report["claim_boundaries"]["operational_map_claim_added"])
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])

    def test_missing_deposition_layer_blocks_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            validation_manifest = root / "validation.json"
            hazard_manifest = root / "hazard.json"
            validation_manifest.write_text(
                json.dumps(
                    {
                        "outputs": [
                            {"kind": "trajectory", "path": ".", "file_count": 1, "row_count": 2},
                            {"kind": "ensemble_trajectories", "path": ".", "file_count": 1, "row_count": 8},
                            {"kind": "ensemble_deposition", "path": ".", "file_count": 1, "row_count": 3},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            hazard_manifest.write_text(
                json.dumps(
                    {
                        "inputs": {"trajectory_sample_count": 10, "deposition_point_count": 3},
                        "outputs": [],
                    }
                ),
                encoding="utf-8",
            )

            report = audit.build_report(validation_manifest, hazard_manifest)

        self.assertEqual(report["audit_status"], "blocked_missing_traceability")
        self.assertIn("hazard_deposition_density_layer", report["missing_or_failed_checks"])
        self.assertIn("Regenerate or repair", report["next_local_follow_up"])

    def test_text_report_names_traceability_and_boundaries(self) -> None:
        text = audit.render_text_report(audit.build_report())

        self.assertIn("audit_status: traceable", text)
        self.assertIn("deposition_layer_path:", text)
        self.assertIn("field_validation_claim_added: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
