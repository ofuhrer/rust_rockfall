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

    def load_tschamut_policy(self) -> dict:
        return validator.read_yaml(
            ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
        )

    def test_template_policy_is_valid(self) -> None:
        validator.validate_policy(self.load_template())

    def test_tschamut_public_policy_is_valid(self) -> None:
        validator.validate_policy(self.load_tschamut_policy())

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
        policy["source_zone_policy"]["derivation_criteria"][
            "manual_interpretation_notes"
        ] = "manual LV95 source-zone interpretation before simulation"
        policy["source_zone_policy"]["geometry"] = {
            "type": "polygon",
            "coordinates": [
                [2600000.0, 1200000.0],
                [2600002.0, 1200000.0],
                [2600002.0, 1200002.0],
                [2600000.0, 1200002.0],
            ],
        }
        policy["source_zone_policy"]["release_sampling"].update(
            {
                "seed": 2056001,
                "release_cell_id_prefix": "pilot_zone_a_cell",
                "requested_release_cell_count": 1,
                "release_cells": [
                    {
                        "release_cell_id": "pilot_zone_a_cell_000",
                        "center_lv95_m": [2600001.0, 1200001.0],
                        "sampling_weight": 1.0,
                    }
                ],
            }
        )
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
        policy = self.load_tschamut_policy()
        policy["block_scenario_policy"]["scenarios"][0]["annual_frequency_per_year"] = 0.01

        with self.assertRaisesRegex(validator.PolicyError, "annual_frequency_per_year"):
            validator.validate_policy(policy)

    def test_tschamut_policy_rejects_physical_release_probability(self) -> None:
        policy = self.load_tschamut_policy()
        policy["source_zone_policy"]["release_sampling"]["release_cells"][0][
            "physical_release_probability"
        ] = 0.1

        with self.assertRaisesRegex(validator.PolicyError, "physical_release_probability"):
            validator.validate_policy(policy)

    def test_tschamut_policy_rejects_release_cell_count_mismatch(self) -> None:
        policy = self.load_tschamut_policy()
        policy["source_zone_policy"]["release_sampling"]["release_cells"].pop()

        with self.assertRaisesRegex(validator.PolicyError, "requested_release_cell_count"):
            validator.validate_policy(policy)

    def test_rejects_missing_risk_boundary(self) -> None:
        policy = copy.deepcopy(self.load_template())
        policy["claim_boundary"]["unsupported_current_claims"].remove("risk_map")

        with self.assertRaisesRegex(validator.PolicyError, "risk_map"):
            validator.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
