from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_bounded_validation_output_profile.py"
SPEC = importlib.util.spec_from_file_location("summarize_bounded_validation_output_profile", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary_script)


class BoundedValidationOutputProfileTests(unittest.TestCase):
    def test_summary_records_measured_pressure_and_bounded_profile(self) -> None:
        summary = summary_script.build_summary()

        self.assertEqual(summary["measurement_status"], "record_based_measurement")
        self.assertEqual(summary["acceptance_classification"], "inconclusive")
        self.assertFalse(summary["scale_up_authorized"])
        self.assertEqual(summary["bounded_profile"]["profile"], "scalable_conditional")
        self.assertEqual(summary["bounded_profile"]["hazard_output_file_count"], 46)
        self.assertEqual(summary["bounded_profile"]["hazard_output_bytes"], 16613900)
        self.assertEqual(summary["bounded_profile"]["validation_output_file_count"], 2005)
        self.assertEqual(summary["bounded_profile"]["validation_output_bytes"], 571377719)
        self.assertEqual(summary["bounded_profile"]["command_recipe"]["profile_controls"]["conditional_curve_export"], "summary-only")
        self.assertEqual(summary["bounded_profile"]["command_recipe"]["profile_controls"]["grid_csv_export"], "none")
        self.assertTrue(summary["bounded_profile"]["command_recipe"]["profile_controls"]["no_plots"])
        self.assertEqual(summary["current_pressure"]["current_file_count"], 191)
        self.assertEqual(summary["current_pressure"]["current_total_bytes"], 267527120)
        self.assertEqual(summary["current_pressure"]["file_count_margin"], 9)
        self.assertEqual(summary["current_pressure"]["byte_margin"], -17527120)
        self.assertEqual(summary["measured_savings"]["hazard_output_file_count_delta_vs_target_budget"], -8)
        self.assertEqual(summary["measured_savings"]["hazard_output_bytes_delta_vs_target_budget"], -58809467)
        self.assertEqual(summary["measured_savings"]["validation_output_file_count_delta_vs_target_budget"], 1)
        self.assertEqual(summary["measured_savings"]["validation_output_bytes_delta_vs_target_budget"], 246514)
        self.assertEqual(summary["output_budget_gate"]["current_classification"], "blocked_before_scale_up")
        self.assertEqual(summary["output_budget_gate"]["inode_and_file_family_budget"]["file_family_pressure"], "validation_debug_artifacts")
        self.assertEqual(summary["convergence"]["status"], "inconclusive")
        self.assertEqual(summary["ensemble_feasibility"]["decision"], "no_go")
        self.assertEqual(summary["local_output_audit"]["status"], "blocked_missing_outputs")
        self.assertEqual(len(summary["local_output_audit"]["missing_paths"]), 4)

    def test_tiny_tree_accounting_counts_files_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a").mkdir()
            (root / "b").mkdir()
            (root / "a" / "one.txt").write_text("hello", encoding="utf-8")
            (root / "b" / "two.txt").write_bytes(b"world!!")

            summary = summary_script.summarize_tree(root)

            self.assertEqual(summary["file_count"], 2)
            self.assertEqual(summary["total_bytes"], 12)

    def test_markdown_mentions_missing_local_outputs_and_final_classification(self) -> None:
        markdown = summary_script.render_markdown(summary_script.build_summary())

        self.assertIn("Final classification: `inconclusive`", markdown)
        self.assertIn("Status: `blocked_missing_outputs`", markdown)
        self.assertIn("validation_debug_artifacts", markdown)
        self.assertIn("Hazard file-count delta: `-8`", markdown)

    def test_rejects_missing_current_pressure_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_budget = ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
            convergence = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
            feasibility = ROOT / "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml"

            with self.assertRaisesRegex(summary_script.BoundedValidationOutputProfileError, "current_pressure_record_path"):
                summary_script.build_summary(
                    current_pressure_record_path=Path(tmp) / "missing_current_pressure.yaml",
                    bounded_profile_record_path=ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                    output_budget_record_path=output_budget,
                    convergence_record_path=convergence,
                    ensemble_feasibility_record_path=feasibility,
                )

    def test_rendered_summary_is_yaml_serializable(self) -> None:
        summary = summary_script.build_summary()
        yaml.safe_dump(summary, sort_keys=False)

    def test_defaults_preserve_public_boundaries_and_non_authorized_scale_up(self) -> None:
        summary = summary_script.build_summary()

        self.assertFalse(summary["bounded_profile"]["claim_boundary"]["changes_physics"])
        self.assertFalse(summary["bounded_profile"]["claim_boundary"]["changes_defaults"])
        self.assertFalse(summary["bounded_profile"]["claim_boundary"]["changes_sampling_weights"])
        self.assertFalse(summary["bounded_profile"]["claim_boundary"]["generated_outputs_committed"])
        self.assertFalse(summary["output_budget_gate"]["scale_up_authorized"])
        self.assertEqual(summary["current_target_gate_profile"]["profile"], "custom_or_mixed_legacy_summary_only")


if __name__ == "__main__":
    unittest.main()
