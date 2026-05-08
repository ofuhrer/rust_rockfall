from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_source_scenario_policy.py"
SPEC = importlib.util.spec_from_file_location("validate_source_scenario_policy", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class SourceScenarioPolicyTests(unittest.TestCase):
    def load_template(self) -> dict:
        return validator.read_yaml(
            ROOT / "validation/templates/public_real_site_source_scenario_policy_v1.yaml"
        )

    def test_template_policy_is_valid(self) -> None:
        validator.validate_policy(self.load_template())

    def test_prepared_policy_requires_source_criteria(self) -> None:
        policy = self.load_template()
        policy["policy_status"] = "draft_predeclared"

        with self.assertRaisesRegex(validator.PolicyError, "derivation criteria"):
            validator.validate_policy(policy)

    def test_prepared_policy_accepts_conditional_block_scenarios(self) -> None:
        policy = self.load_template()
        policy["policy_status"] = "draft_predeclared"
        policy["source_zone_policy"]["source_zone_id"] = "pilot_zone_a"
        policy["source_zone_policy"]["derivation_criteria"]["status"] = "predeclared_manual_review"
        policy["block_scenario_policy"]["scenarios"] = [
            {
                "block_scenario_id": "block_small",
                "block_size_class": "small",
                "block_shape_class": "sphere",
                "block_radius_m": 0.25,
                "block_mass_kg": 45.0,
                "sampling_weight": 1.0,
            }
        ]

        validator.validate_policy(policy)

    def test_rejects_annual_block_frequency(self) -> None:
        policy = self.load_template()
        policy["policy_status"] = "draft_predeclared"
        policy["source_zone_policy"]["source_zone_id"] = "pilot_zone_a"
        policy["source_zone_policy"]["derivation_criteria"]["status"] = "predeclared_manual_review"
        policy["block_scenario_policy"]["scenarios"] = [
            {
                "block_scenario_id": "block_small",
                "block_size_class": "small",
                "block_shape_class": "sphere",
                "block_radius_m": 0.25,
                "sampling_weight": 1.0,
                "annual_frequency_per_year": 0.01,
            }
        ]

        with self.assertRaisesRegex(validator.PolicyError, "annual_frequency_per_year"):
            validator.validate_policy(policy)

    def test_rejects_missing_risk_boundary(self) -> None:
        policy = copy.deepcopy(self.load_template())
        policy["claim_boundary"]["unsupported_current_claims"].remove("risk_map")

        with self.assertRaisesRegex(validator.PolicyError, "risk_map"):
            validator.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
