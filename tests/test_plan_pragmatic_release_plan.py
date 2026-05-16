from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_pragmatic_release_plan.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_pragmatic_release_plan")


class PragmaticReleasePlanTests(unittest.TestCase):
    def test_report_is_deterministic_from_frozen_inputs(self) -> None:
        first = planner.build_report()
        second = planner.build_report()

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_block_scenario_sensitivity_plan_v1")
        self.assertEqual(first["scenario_plan_status"], "ready")
        self.assertTrue(first["read_only"])
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertEqual(first["source_policy_provenance"]["policy_id"], "tschamut_public_source_scenario_policy_v1")
        self.assertEqual(first["source_policy_provenance"]["policy_path"], "validation/policies/tschamut_public_source_scenario_policy_v1.yaml")
        self.assertEqual(first["source_policy_provenance"]["release_sampling_mode"], "deterministic_grid")
        self.assertEqual(first["scenario_plan_summary"]["block_size_bin_count"], 3)
        self.assertEqual(first["scenario_plan_summary"]["reference_row_count"], 1)
        self.assertEqual(first["scenario_plan_summary"]["policy_sampling_weight_total"], 10.0)
        self.assertEqual(first["scenario_plan_summary"]["normalized_sampling_share_total"], 1.0)

        bins = first["block_size_bins"]
        self.assertEqual([entry["bin_label"] for entry in bins], ["small", "medium", "large"])
        self.assertEqual([entry["block_scenario_id"] for entry in bins], [
            "tschamut_public_block_small",
            "tschamut_public_block_medium",
            "tschamut_public_block_large",
        ])
        self.assertEqual([entry["normalized_sampling_share"] for entry in bins], [0.3, 0.5, 0.2])
        self.assertTrue(all("conditional_sampling_only" in entry["non_frequency_labels"] for entry in bins))
        self.assertTrue(all(entry["plan_label"] == "pragmatic_sensitivity_bin" for entry in bins))

        weighting = first["weighting_semantics"]
        self.assertEqual(weighting["sampling_weight_semantics"], "conditional_sampling_only")
        self.assertEqual(weighting["scenario_probability_semantics"], "normalized within a block family; no annual frequency claim")
        self.assertTrue(weighting["sampling_weight_is_not_physical_probability"])
        self.assertTrue(weighting["sampling_weight_is_not_annual_frequency"])

        reference = first["reference_scenario_table"]
        self.assertEqual(reference["role"], "frozen_reference_record")
        self.assertEqual(reference["row_count"], 1)
        self.assertEqual(reference["row_ids"], ["tschamut_public_block_observed_rows"])
        self.assertEqual(reference["block_scenario_ids"], ["tschamut_public_observed_rows"])
        self.assertIn("annual_frequency_per_year", reference["non_frequency_columns"])
        self.assertEqual(reference["rows"][0]["release_probability"], "")
        self.assertEqual(reference["rows"][0]["scenario_probability"], "")
        self.assertEqual(reference["rows"][0]["annual_frequency_per_year"], "")
        self.assertEqual(reference["rows"][0]["time_horizon_years"], "")

        self.assertFalse(first["claim_boundary"]["annual_frequency_supported"])
        self.assertFalse(first["claim_boundary"]["physical_probability_supported"])
        self.assertIn("conditional_sampling_only", first["explicit_non_frequency_labels"])
        self.assertEqual(first["same_scale_reference"]["document_status"], "available")

    def test_missing_inputs_block_generation_and_list_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_policy = root / "missing_policy.yaml"
            missing_table = root / "missing_table.csv"
            report = planner.build_report(policy_path=missing_policy, scenario_table_path=missing_table)

        self.assertEqual(report["scenario_plan_status"], "blocked_missing_inputs")
        self.assertIn(str(missing_policy), report["missing_inputs"][0])
        self.assertIn(str(missing_table), report["missing_inputs"][1])
        self.assertEqual(report["scenario_plan_summary"]["block_size_bin_count"], 0)
        self.assertEqual(report["reference_scenario_table"]["row_count"], 0)
        self.assertTrue(report["pragmatic_coverage_boundary"]["coverage_is_not_physical_frequency"])
        self.assertTrue(report["weighting_semantics"]["sampling_weights_are_not_physical_probabilities"])

    def test_text_output_is_stable(self) -> None:
        report = planner.build_report()
        text = planner.render_text_report(report)
        self.assertEqual(text, planner.render_text_report(report))
        self.assertIn("Balfrin Block-Scenario Sensitivity Plan", text)
        self.assertIn("Scenario plan status: `ready`", text)
        self.assertIn("Block-Size Bins", text)
        self.assertIn("Pragmatic Coverage Boundary", text)
        self.assertIn("not_annual_frequency", text)
        self.assertIn("Same-Scale Reference", text)


if __name__ == "__main__":
    unittest.main()
