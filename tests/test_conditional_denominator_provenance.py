from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_conditional_denominator_provenance as audit


class ConditionalDenominatorProvenanceTests(unittest.TestCase):
    def test_default_manifest_has_complete_conditional_denominator_evidence(self) -> None:
        report = audit.build_report()

        self.assertEqual(report["schema_version"], audit.SCHEMA_VERSION)
        self.assertEqual(report["audit_status"], "complete")
        self.assertGreater(report["trajectory_denominator_evidence"]["trajectory_count"], 0)
        self.assertGreater(report["trajectory_denominator_evidence"]["trajectory_sample_count"], 0)
        self.assertEqual(report["trajectory_denominator_evidence"]["status"], "present")
        self.assertGreater(report["denominator_layer_count"], 0)
        self.assertEqual(report["missing_denominator_layers"], [])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])

    def test_maximum_layers_do_not_require_denominators(self) -> None:
        report = audit.build_report()
        rows = {row["layer_name"]: row for row in report["layer_denominator_audit"]}

        self.assertFalse(rows["max_kinetic_energy"]["denominator_required"])
        self.assertFalse(rows["max_jump_height"]["denominator_required"])
        self.assertTrue(rows["reach_probability"]["denominator_required"])

    def test_missing_denominator_blocks_report(self) -> None:
        manifest = {
            "case_id": "synthetic_missing_denominator",
            "inputs": {
                "trajectory_count": 10,
                "trajectory_sample_count": 100,
            },
            "conditional_execution": {
                "annualized": False,
                "physical_probability": False,
                "risk_or_exposure": False,
            },
            "conditional_intensity_exceedance_curves": {
                "enabled": True,
                "annualized": False,
            },
            "layer_semantics": [
                {
                    "layer_name": "reach_probability",
                    "denominator": None,
                    "conditioned_on": ["source_zone_id=fixture"],
                    "annualized": False,
                    "weighted": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            report = audit.build_report(path)

        self.assertEqual(report["audit_status"], "blocked_missing_denominator_evidence")
        self.assertEqual(report["missing_denominator_layers"], ["reach_probability"])
        self.assertIn("build_hazard_layers.py", report["next_local_follow_up"])

    def test_text_report_names_non_probability_boundary(self) -> None:
        text = audit.render_text_report(audit.build_report())

        self.assertIn("audit_status: complete", text)
        self.assertIn("physical_probability_claims_allowed: False", text)
        self.assertIn("annual_frequency_claims_allowed: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
