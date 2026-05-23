from __future__ import annotations

import unittest

from scripts import summarize_local_scientific_progress as progress


class LocalScientificProgressTests(unittest.TestCase):
    def test_report_ranks_local_non_balfrin_tracks(self) -> None:
        report = progress.build_report()

        self.assertEqual(report["schema_version"], progress.SCHEMA_VERSION)
        self.assertEqual(report["scientific_status"]["physical_credibility_status"], "not_established")
        self.assertEqual(report["scientific_status"]["calibration_status"], "missing")
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])

        track_ids = [track["track_id"] for track in report["ranked_local_tracks"]]
        self.assertEqual(
            track_ids[:6],
            [
                "conditional_denominator_provenance",
                "trajectory_deposition_traceability",
                "extreme_layer_fragility",
                "second_site_local_blockers",
                "chant_sura_holdout_split",
                "calibration_separation",
            ],
        )
        self.assertTrue(all("balfrin" not in track["track_id"] for track in report["ranked_local_tracks"]))
        self.assertTrue(all(track["next_command"].startswith("PYENV_VERSION=system uv run python") for track in report["ranked_local_tracks"]))

    def test_fragile_layers_are_explicit(self) -> None:
        report = progress.build_report()
        layers = {layer["layer_key"]: layer for layer in report["most_fragile_layers"]}

        self.assertEqual(layers["max_kinetic_energy"]["fragility"], "highest")
        self.assertEqual(layers["max_jump_height"]["fragility"], "high")
        self.assertIn("maxima", layers["max_kinetic_energy"]["reason"].lower())

    def test_text_report_names_boundaries_and_commands(self) -> None:
        text = progress.render_text_report(progress.build_report())

        self.assertIn("physical_credibility_status: not_established", text)
        self.assertIn("balfrin_required: False", text)
        self.assertIn("conditional_denominator_provenance", text)
        self.assertIn("scripts/audit_conditional_denominator_provenance.py", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
