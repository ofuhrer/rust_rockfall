from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_pilot_ensemble_feasibility.py"
SPEC = importlib.util.spec_from_file_location("validate_pilot_ensemble_feasibility", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PilotEnsembleFeasibilityTests(unittest.TestCase):
    def test_accepts_no_go_feasibility_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_path = self.write_record(Path(tmp), self.base_record())

            summary = validator.validate_feasibility_record(record_path)

            self.assertEqual(summary["decision"], "no_go")
            self.assertEqual(summary["gate_trajectories_per_release_zone"], 6)
            self.assertEqual(summary["proposed_trajectories_per_release_zone"], 100)
            self.assertEqual(summary["convergence_status"], "no-go")
            self.assertEqual(summary["target_scale_status"], "inconclusive")

    def test_rejects_no_go_without_required_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["blockers"].remove("forest_obstacle_omission_limiting")
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "forest_obstacle_omission_limiting"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_non_increasing_trajectory_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["input_evidence"]["proposed_trajectories_per_release_zone"] = 6
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "must be larger"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_full_curve_table_for_increase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["output_budget_assessment"]["required_curve_export_mode"] = "full"
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "summary-only"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_missing_precondition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["required_preconditions_before_increase"].remove("review_manual_gis_visual_qa")
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "review_manual_gis_visual_qa"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_missing_target_scale_provenance_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["blockers"].remove(
                "validation_runner_parallel_provenance_partial_for_observed_release_outputs"
            )
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "parallel_provenance"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_target_scale_without_summary_only_curves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["target_scale_evidence"]["conditional_curve_export_mode"] = "full"
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "summary-only"):
                validator.validate_feasibility_record(record_path)

    def test_rejects_unqualified_risk_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["decision_rationale"] = "Proceed to a risk map."
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.EnsembleFeasibilityError, "misleading current-product claim"):
                validator.validate_feasibility_record(record_path)

    def test_selected_tschamut_record_is_valid(self) -> None:
        summary = validator.validate_feasibility_record(
            ROOT / "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml"
        )

        self.assertEqual(summary["decision"], "no_go")

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "ensemble_feasibility.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        return {
            "schema_version": "pilot_ensemble_feasibility_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "roadmap_item": "target_5_ensemble_size_feasibility",
            "decision": "no_go",
            "decision_rationale": "The selected gate is reproducible, but scale-up evidence is incomplete.",
            "operational_status": "research_diagnostic",
            "input_evidence": {
                "run_freeze_path": "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "scaling_review_path": "docs/tschamut_public_pilot_scaling_review.md",
                "obstacle_scope_path": "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                "visual_qa_record_path": "validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml",
                "target_gate_record_path": "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "small_gate_status": "gate_run_completed",
                "target_gate_status": "inconclusive",
                "gate_trajectories_per_release_zone": 6,
                "proposed_trajectories_per_release_zone": 100,
                "release_cell_count": 10,
            },
            "convergence_assessment": {
                "status": "no-go",
                "diagnostics_reviewed": ["small_gate_conditional_curves"],
                "missing_diagnostics": [
                    "accepted_target_vs_small_gate_convergence_interpretation",
                    "validation_runner_parallel_provenance_for_observed_release_ensembles",
                ],
                "interpretation": "Target-scale convergence is not established.",
            },
            "output_budget_assessment": {
                "status": "no-go",
                "gate_output_total_bytes": 226925754,
                "gate_output_file_count": 186,
                "target_validation_output_total_bytes": 571131205,
                "target_validation_output_file_count": 2004,
                "target_hazard_output_total_bytes": 75423367,
                "target_hazard_output_file_count": 54,
                "target_validation_wall_seconds": 77.0243719999853,
                "target_hazard_wall_seconds": 57.85906245899969,
                "target_validation_memory_peak_bytes_on_darwin": 367017984,
                "target_hazard_memory_peak_bytes_on_darwin": 411058176,
                "target_conditional_curve_rows_suppressed": 729600,
                "required_curve_export_mode": "summary-only",
                "full_curve_table_export_allowed_for_increase": False,
                "budget_controls": ["conditional_curve_summary_only"],
                "interpretation": "The large curve table must stay disabled for an increase.",
            },
            "target_scale_evidence": {
                "status": "inconclusive",
                "target_gate_record_path": "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "validation_manifest_path": "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                "hazard_manifest_path": "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                "evidence_summary_path": "hazard/results/tschamut_public_pilot/target_gate_v1/target_gate_evidence_summary.json",
                "validation_manifest_sha256": "73b5db351727522264c10e48f24a646150122903d2296457c08eb34814819fc0",
                "hazard_manifest_sha256": "2d743fbd28fc4af2d65dfcc00cf3801aad9805126b87362a32de8b5f767fbc8b",
                "target_scale_executed": True,
                "validation_simulated_trajectory_count": 1000,
                "conditional_curve_export_mode": "summary-only",
                "reducer_worker_counts_compared": [1, 2],
                "reducer_parity_compared_outputs_match": True,
                "generated_outputs_committed": False,
                "interpretation": "The target gate executed but remains inconclusive.",
            },
            "execution_plan": {
                "run_now": False,
                "generated_outputs_committed": False,
                "changes_physics": False,
                "changes_defaults": False,
                "changes_sampling_weights": False,
                "next_command_when_authorized": (
                    "UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py "
                    "--conditional-curve-export summary-only --reducer-workers 2"
                ),
            },
            "blockers": [
                "target_scale_convergence_inconclusive",
                "manual_gis_visual_qa_inconclusive",
                "forest_obstacle_omission_limiting",
                "validation_runner_parallel_provenance_partial_for_observed_release_outputs",
                "validation_debug_output_budget_too_large_for_next_increase",
            ],
            "required_preconditions_before_increase": [
                "use_summary_only_conditional_curve_export",
                "record_convergence_diagnostics",
                "record_output_budget",
                "review_manual_gis_visual_qa",
                "review_forest_obstacle_context",
                "clarify_validation_runner_parallel_provenance",
                "reduce_or_justify_validation_debug_output_volume",
            ],
            "claim_boundary": {
                "operational_status": "research_diagnostic",
                "annualized": False,
                "physical_probability": False,
                "risk_or_exposure": False,
                "current_allowed_product_labels": ["conditional_intensity_exceedance"],
                "unsupported_current_claims": [
                    "annual_frequency",
                    "return_period",
                    "physical_probability",
                    "risk_map",
                    "operational_hazard_map",
                ],
            },
        }


if __name__ == "__main__":
    unittest.main()
