from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_bounded_validation_output_profile.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "bounded_validation_output_profile"
SPEC = importlib.util.spec_from_file_location("summarize_bounded_validation_output_profile", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary_script)


class BoundedValidationOutputProfileTests(unittest.TestCase):
    def test_summary_records_measured_pressure_and_bounded_profile(self) -> None:
        summary = summary_script.build_summary()

        self.assertEqual(summary["measurement_status"], "record_based_measurement")
        self.assertEqual(summary["acceptance_classification"], "no_go")
        self.assertEqual(summary["final_classification"], "no_go")
        self.assertEqual(summary["feasibility_decision"], "no_go")
        self.assertFalse(summary["scale_up_authorized"])
        self.assertFalse(summary["validation_output_reduced"])
        self.assertEqual(summary["validation_output_blocker_status"], "blocker_retained")
        self.assertEqual(summary["file_family_pressure"], "validation_debug_artifacts")
        self.assertFalse(summary["defaults_changed"])
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
        self.assertEqual(summary["validation_output_audit"]["status"], "blocked_missing_outputs")
        self.assertEqual(summary["validation_output_audit"]["required_for_audit"], ["validation_manifest"])

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

    def test_validation_output_manifest_audit_breaks_down_file_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            trajectories = work / "run_trajectories"
            impacts = work / "run_impacts"
            trajectories.mkdir()
            impacts.mkdir()

            (trajectories / "trajectory_000000.csv").write_text("sample-a\n", encoding="utf-8")
            (trajectories / "trajectory_000001.csv").write_text("sample-b\n", encoding="utf-8")
            (impacts / "trajectory_000000.csv").write_text("impact-a\n", encoding="utf-8")

            manifest = {
                "schema_version": "run_manifest_v1",
                "outputs": [
                    {
                        "kind": "ensemble_trajectories",
                        "format": "csv_directory",
                        "path": str(trajectories),
                        "file_count": 2,
                        "total_bytes": 16,
                        "row_count": 2,
                        "skipped_empty_files": 0,
                        "sha256": "a" * 64,
                    },
                    {
                        "kind": "ensemble_impact_events",
                        "format": "csv_directory",
                        "path": str(impacts),
                        "file_count": 1,
                        "total_bytes": 8,
                        "row_count": 1,
                        "skipped_empty_files": 1,
                        "sha256": "b" * 64,
                    },
                    {
                        "kind": "trajectory_metadata",
                        "format": "csv",
                        "path": str(work / "trajectory_metadata.csv"),
                        "file_count": 1,
                        "total_bytes": 7,
                        "row_count": 1,
                        "sha256": "c" * 64,
                    },
                    {
                        "kind": "pilot_gis_package_manifest",
                        "format": "json",
                        "path": str(work / "pilot_gis_package_manifest.json"),
                        "file_count": 1,
                        "total_bytes": 11,
                        "sha256": "d" * 64,
                    },
                ],
            }
            manifest_path = work / "validation_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            audit = summary_script.summarize_validation_output_audit(manifest_path)

            self.assertEqual(audit["status"], "available")
            self.assertEqual(audit["family_count"], 4)
            self.assertEqual(audit["total_file_count"], 5)
            self.assertEqual(audit["total_bytes"], 42)
            families = {family["family"]: family for family in audit["families"]}
            self.assertEqual(families["ensemble_trajectories_dir"]["file_count"], 2)
            self.assertEqual(families["ensemble_trajectories_dir"]["total_bytes"], 16)
            self.assertEqual(families["ensemble_impact_events_dir"]["file_count"], 1)
            self.assertEqual(families["trajectory_metadata_csv"]["kind"], "trajectory_metadata")
            self.assertEqual(families["pilot_gis_package_manifest_json"]["format"], "json")

    def test_validation_output_manifest_audit_blocks_when_missing(self) -> None:
        audit = summary_script.summarize_validation_output_audit(None)

        self.assertEqual(audit["status"], "blocked_missing_outputs")
        self.assertFalse(audit["reduced"])

    def test_validation_output_comparison_blocks_when_fixture_inputs_are_missing(self) -> None:
        comparison = summary_script.summarize_validation_output_comparison(
            baseline_manifest_path=None,
            reduced_manifest_path=FIXTURE_DIR / "reduced_manifest.json",
        )

        self.assertEqual(comparison["status"], "blocked_missing_outputs")
        self.assertFalse(comparison["validation_output_reduced"])
        self.assertEqual(comparison["validation_output_mode"], None)
        self.assertIn("baseline_validation_manifest", comparison["missing_paths"])

    def test_validation_output_comparison_reports_before_after_accounting(self) -> None:
        summary = summary_script.build_summary(
            validation_output_baseline_manifest_path=FIXTURE_DIR / "baseline_manifest.json",
            validation_output_reduced_manifest_path=FIXTURE_DIR / "reduced_manifest.json",
        )

        self.assertEqual(summary["validation_output_mode"], "summary_only")
        self.assertTrue(summary["validation_output_reduced"])
        self.assertEqual(summary["baseline_file_count"], 14)
        self.assertEqual(summary["reduced_file_count"], 4)
        self.assertEqual(summary["baseline_bytes"], 2848)
        self.assertEqual(summary["reduced_bytes"], 456)
        self.assertEqual(summary["reduction_file_count_delta"], 10)
        self.assertEqual(summary["reduction_bytes_delta"], 2392)
        self.assertEqual(
            summary["retained_output_classes"],
            [
                "diagnostics_json",
                "ensemble_deposition_csv",
                "stop_state_summary_csv",
                "trajectory_metadata_csv",
            ],
        )
        self.assertEqual(
            summary["omitted_or_sampled_output_classes"],
            [
                "ensemble_impact_events_dir",
                "ensemble_impact_events_parquet",
                "ensemble_trajectories_dir",
                "impact_events_csv",
                "impact_events_json",
                "trajectory_csv",
            ],
        )
        self.assertTrue(summary["required_provenance_retained"])
        self.assertFalse(summary["defaults_changed"])
        self.assertFalse(summary["scale_up_authorized"])
        comparison = summary["validation_output_comparison"]
        self.assertEqual(comparison["status"], "available")
        self.assertEqual(comparison["validation_output_mode"], "summary_only")
        self.assertEqual(comparison["baseline"]["family_count"], 10)
        self.assertEqual(comparison["reduced"]["family_count"], 4)

    def test_markdown_mentions_missing_local_outputs_and_final_classification(self) -> None:
        markdown = summary_script.render_markdown(summary_script.build_summary())

        self.assertIn("Final classification: `no_go`", markdown)
        self.assertIn("Feasibility decision: `no_go`", markdown)
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
        self.assertFalse(summary["defaults_changed"])


if __name__ == "__main__":
    unittest.main()
