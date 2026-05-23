from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_chant_sura_holdout_split as audit


class ChantSuraHoldoutSplitAuditTests(unittest.TestCase):
    def test_default_split_is_disjoint(self) -> None:
        report = audit.build_report()

        self.assertEqual(report["schema_version"], audit.SCHEMA_VERSION)
        self.assertEqual(report["audit_status"], "passed")
        self.assertEqual(report["split_counts"]["model_selection_trajectory_count"], 5)
        self.assertEqual(report["split_counts"]["held_out_trajectory_count"], 6)
        self.assertEqual(report["shared_trajectory_ids"], [])
        self.assertTrue(report["consistency_checks"]["recorded_overlap_matches_computed"])
        self.assertFalse(report["claim_boundaries"]["calibration_performed"])
        self.assertFalse(report["claim_boundaries"]["external_validation_claimed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])

    def test_overlap_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            split_path = root / "metadata_contact_split.json"
            evidence_path = root / "holdout_validation_evidence_manifest.json"
            split_path.write_text(
                json.dumps(
                    {
                        "dataset_id": "fixture",
                        "model_selection_subset": {"trajectory_ids": ["A", "B"], "role": "selection"},
                        "held_out_evaluation_subset": {"trajectory_ids": ["B", "C"], "role": "holdout"},
                        "overlap": ["B"],
                    }
                ),
                encoding="utf-8",
            )
            evidence_path.write_text(json.dumps({"overlap_check": {"shared_trajectory_ids": ["B"]}}), encoding="utf-8")

            report = audit.build_report(split_metadata_path=split_path, evidence_manifest_path=evidence_path)

        self.assertEqual(report["audit_status"], "blocked_overlap_detected")
        self.assertEqual(report["shared_trajectory_ids"], ["B"])
        self.assertEqual(report["split_counts"]["shared_trajectory_count"], 1)

    def test_duplicate_ids_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            split_path = root / "metadata_contact_split.json"
            evidence_path = root / "holdout_validation_evidence_manifest.json"
            split_path.write_text(
                json.dumps(
                    {
                        "dataset_id": "fixture",
                        "model_selection_subset": {"trajectory_ids": ["A", "A"], "role": "selection"},
                        "held_out_evaluation_subset": {"trajectory_ids": ["B"], "role": "holdout"},
                        "overlap": [],
                    }
                ),
                encoding="utf-8",
            )
            evidence_path.write_text(json.dumps({"overlap_check": {"shared_trajectory_ids": []}}), encoding="utf-8")

            report = audit.build_report(split_metadata_path=split_path, evidence_manifest_path=evidence_path)

        self.assertEqual(report["audit_status"], "passed")
        self.assertFalse(report["consistency_checks"]["no_duplicate_model_selection_ids"])

    def test_text_report_names_overlap_and_boundaries(self) -> None:
        text = audit.render_text_report(audit.build_report())

        self.assertIn("audit_status: passed", text)
        self.assertIn("shared_trajectory_ids: none", text)
        self.assertIn("physical_probability_claims_allowed: False", text)
        self.assertIn("operational_claims_allowed: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
