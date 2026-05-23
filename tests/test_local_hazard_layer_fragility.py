from __future__ import annotations

import unittest

from scripts import rank_local_hazard_layer_fragility as fragility


class LocalHazardLayerFragilityTests(unittest.TestCase):
    def test_extreme_layers_rank_ahead_of_footprint_summaries(self) -> None:
        report = fragility.build_report()

        self.assertEqual(report["schema_version"], fragility.SCHEMA_VERSION)
        self.assertEqual(report["ranking_status"], "ready")
        self.assertEqual(report["highest_priority_layers"], ["max_kinetic_energy", "max_jump_height"])

        ranks = {row["layer_key"]: row["rank"] for row in report["ranked_layers"]}
        self.assertEqual(ranks["max_kinetic_energy"], 1)
        self.assertEqual(ranks["max_jump_height"], 2)
        self.assertLess(ranks["max_kinetic_energy"], ranks["reach_probability"])
        self.assertLess(ranks["max_jump_height"], ranks["deposition_density"])

    def test_ranking_preserves_claim_boundaries(self) -> None:
        report = fragility.build_report()
        boundaries = report["claim_boundaries"]

        self.assertFalse(boundaries["annual_frequency_claims_allowed"])
        self.assertFalse(boundaries["operational_claims_allowed"])
        self.assertFalse(boundaries["physical_probability_claims_allowed"])
        self.assertFalse(boundaries["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(boundaries["scale_up_authorized"])
        self.assertFalse(boundaries["balfrin_required"])
        self.assertFalse(boundaries["tuning_performed"])

    def test_layer_rows_record_reasons_and_follow_ups(self) -> None:
        report = fragility.build_report()
        rows = {row["layer_key"]: row for row in report["ranked_layers"]}

        self.assertEqual(rows["max_kinetic_energy"]["scientific_fragility_level"], "highest")
        self.assertEqual(rows["max_jump_height"]["scientific_fragility_level"], "high")
        self.assertIn("maxima", rows["max_kinetic_energy"]["reason"].lower())
        self.assertIn("support/nodata", rows["max_jump_height"]["reason"].lower())
        self.assertIn("sensitivity", rows["max_kinetic_energy"]["recommended_local_follow_up"])
        self.assertEqual(rows["max_kinetic_energy"]["physical_credibility_status"], "not_established")
        self.assertEqual(rows["max_kinetic_energy"]["operational_status"], "not_authorized")

    def test_text_report_names_layers_and_boundaries(self) -> None:
        text = fragility.render_text_report(fragility.build_report())

        self.assertIn("max_kinetic_energy", text)
        self.assertIn("max_jump_height", text)
        self.assertIn("operational_claims_allowed: False", text)
        self.assertIn("physical_probability_claims_allowed: False", text)
        self.assertIn("scripts/summarize_extreme_layer_sensitivity_smoke.py", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
