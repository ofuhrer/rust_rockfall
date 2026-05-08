from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_repo_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_repo_consistency", SCRIPT_PATH)
assert SPEC is not None
check_repo_consistency = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_repo_consistency)


class HazardClaimHygieneTests(unittest.TestCase):
    def test_rejects_tracked_copy_suffix_docs(self) -> None:
        tracked = [
            "docs/next_development_targets.md",
            "docs/next_development_targets 2.md",
            "docs/archive/old copy.md",
        ]

        self.assertEqual(
            check_repo_consistency.find_copy_suffix_doc_paths(tracked),
            ["docs/next_development_targets 2.md", "docs/archive/old copy.md"],
        )

    def test_rejects_bare_annual_current_product_claim(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current hazard layers report annual frequency for each cell.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("annual frequency claim", errors[0])

    def test_allows_explicit_future_annual_boundary(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Future annual frequency products require source-frequency contracts.",
            "fixture.md",
        )

        self.assertEqual(errors, [])

    def test_rejects_bare_intensity_frequency_for_current_products(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current threshold layers are intensity-frequency products.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("intensity-frequency", errors[0])

    def test_allows_current_conditional_intensity_exceedance(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current threshold layers are conditional intensity-exceedance products.",
            "fixture.md",
        )

        self.assertEqual(errors, [])

    def test_rejects_bare_risk_map_language(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "The generated package is a risk map for the pilot area.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("risk-map claim", errors[0])


if __name__ == "__main__":
    unittest.main()
