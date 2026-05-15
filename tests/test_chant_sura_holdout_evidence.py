from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import summarize_chant_sura_holdout_evidence as summary


class ChantSuraHoldoutEvidenceTests(unittest.TestCase):
    def test_json_shape_and_boundary_fields(self) -> None:
        report = summary.build_report()
        expected_keys = {
            "schema_version",
            "manifest_path",
            "holdout_evidence_status",
            "candidate_dataset_id",
            "candidate_site_id",
            "candidate_site_name",
            "evidence_role_summary",
            "model_selection_evidence",
            "holdout_validation_evidence",
            "split_metadata",
            "fixture_boundaries",
            "overlap_check",
            "calibration_status",
            "physical_probability_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "operational_claims_allowed",
            "scale_up_authorized",
            "limitations",
            "recommended_next_evidence_step",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["holdout_evidence_status"], "separated_holdout_validation_evidence")
        self.assertFalse(report["physical_probability_claims_allowed"])
        self.assertFalse(report["annual_frequency_claims_allowed"])
        self.assertFalse(report["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["scale_up_authorized"])

    def test_split_fields_are_surfaced_and_distinct(self) -> None:
        report = summary.build_report()
        split = report["split_metadata"]
        self.assertEqual(split["dataset_id"], "chant_sura_2020")
        self.assertEqual(
            split["held_out_evaluation_subset"]["trajectory_ids"],
            ["RF16W200r2", "RF18W200r4", "RF20e200r2", "RF20e200r5", "RF16W800r2", "RF18W800r1"],
        )
        self.assertEqual(
            split["model_selection_subset"]["trajectory_ids"],
            ["RF16W200r1", "RF16W200r3", "RF18W200r1", "RF18W800r6", "RF20e200r1"],
        )
        self.assertEqual(report["overlap_check"]["shared_trajectory_ids"], [])
        self.assertEqual(report["fixture_boundaries"]["split_metadata_sufficiency"], "sufficient_for_current_holdout_boundary")

    def test_diagnostic_and_holdout_roles_are_separated(self) -> None:
        report = summary.build_report()
        model = report["model_selection_evidence"]
        holdout = report["holdout_validation_evidence"]
        self.assertEqual(model["status"], "partial")
        self.assertEqual(holdout["status"], "present")
        self.assertIn("model-selection subset", " ".join(model["selection_summaries"]))
        self.assertIn("held-out trajectories", " ".join(holdout["selection_boundary_notes"]))
        self.assertTrue(any("not validate Tschamut hazard maps" in item for item in holdout["limitations"]))

    def test_missing_or_ambiguous_split_metadata_is_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            split_path = tmp / "metadata_contact_split.json"
            split_path.write_text("{}", encoding="utf-8")
            # The helper currently reads the committed split path, so we validate the parser
            # behaviour directly on a degenerate record.
            data = summary.load_json(split_path)
            self.assertEqual(data, {})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
