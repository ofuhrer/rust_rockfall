from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_adaptive_aoi_ensemble_convergence_controller.py"
SPEC = importlib.util.spec_from_file_location("summarize_adaptive_aoi_ensemble_convergence_controller", SCRIPT)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

FIXTURE = ROOT / "tests" / "fixtures" / "hazard" / "convergence"


class AdaptiveAoiEnsembleConvergenceControllerTests(unittest.TestCase):
    def test_identical_fixture_reports_converged_and_stops(self) -> None:
        report = MODULE.build_report(
            current_manifest=FIXTURE / "reference_manifest.json",
            candidate_manifest=FIXTURE / "reference_manifest.json",
            current_trajectory_count=60,
            output_budget_override=self.budget_report(blocked=False),
            frontier_override=self.frontier_report(),
            feasibility_override=self.feasibility_report(),
            current_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
            candidate_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
        )

        self.assertEqual(report["controller_status"], "converged")
        self.assertEqual(report["execution_mode"], "local")
        self.assertEqual(report["adaptive_plan"]["status"], "local_only")
        self.assertEqual(report["adaptive_plan"]["trajectory_schedule"]["planned_trajectory_counts"], [90, 150, 270])
        self.assertEqual(report["adaptive_plan"]["stop_criteria"][0]["status"], "converged")
        self.assertEqual(report["adaptive_plan"]["stop_criteria"][1]["status"], "budget_open")

    def test_budget_blocked_branch_stops_before_escalation(self) -> None:
        report = MODULE.build_report(
            current_manifest=FIXTURE / "reference_manifest.json",
            candidate_manifest=FIXTURE / "perturbed_manifest.json",
            current_trajectory_count=60,
            output_budget_override=self.budget_report(blocked=True),
            frontier_override=self.frontier_report(),
            feasibility_override=self.feasibility_report(),
            current_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
            candidate_manifest_report_override=self.manifest_report(FIXTURE / "perturbed_manifest.json"),
        )

        self.assertEqual(report["controller_status"], "budget_stopped")
        self.assertEqual(report["execution_mode"], "local")
        self.assertEqual(report["adaptive_plan"]["status"], "local_only")
        self.assertEqual(report["adaptive_plan"]["stop_criteria"][1]["status"], "budget_stopped")
        self.assertIn("budget blocks another escalation", report["adaptive_plan"]["stop_criteria"][1]["reason"])

    def test_inconclusive_branch_emits_balfrin_ready_command_plan(self) -> None:
        report = MODULE.build_report(
            current_manifest=FIXTURE / "reference_manifest.json",
            candidate_manifest=FIXTURE / "perturbed_manifest.json",
            current_trajectory_count=60,
            output_budget_override=self.budget_report(blocked=False),
            frontier_override=self.frontier_report(),
            feasibility_override=self.feasibility_report(),
            current_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
            candidate_manifest_report_override=self.manifest_report(FIXTURE / "perturbed_manifest.json"),
        )

        self.assertEqual(report["controller_status"], "inconclusive")
        self.assertEqual(report["execution_mode"], "balfrin_ready")
        self.assertEqual(report["adaptive_plan"]["status"], "ready")
        self.assertEqual(report["adaptive_plan"]["recommended_probe"]["trajectory_count"], 90)
        self.assertIn("submit_balfrin_probe.py", report["adaptive_plan"]["command_templates"][1]["command"])
        self.assertEqual(
            report["adaptive_plan"]["trajectory_schedule"]["step_rows"][0]["expected_validation_output_file_count"],
            6,
        )

    def test_json_report_stays_machine_readable(self) -> None:
        report = MODULE.build_report(
            current_manifest=FIXTURE / "reference_manifest.json",
            candidate_manifest=FIXTURE / "reference_manifest.json",
            current_trajectory_count=60,
            output_budget_override=self.budget_report(blocked=False),
            frontier_override=self.frontier_report(),
            feasibility_override=self.feasibility_report(),
            current_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
            candidate_manifest_report_override=self.manifest_report(FIXTURE / "reference_manifest.json"),
        )

        json.dumps(report)

    def budget_report(self, *, blocked: bool) -> dict[str, object]:
        status = "blocker_retained" if blocked else "recorded"
        return {
            "schema_version": "output_budget_reducer_gate_v1",
            "current_classification": "blocked_before_scale_up" if blocked else "diagnostic",
            "output_profile": {
                "current_target_gate_profile": {
                    "profile": "legacy_custom_summary_only",
                    "conditional_curve_export_mode": "summary-only",
                    "grid_csv_export_mode": "legacy_default_full_or_unrecorded",
                    "plots_enabled": False,
                    "generated_outputs_committed": False,
                },
                "selected_followup_profile": {
                    "profile": "scalable_conditional",
                    "required_controls": [
                        "--conditional-curve-export summary-only",
                        "--grid-csv-export none",
                        "--no-plots",
                    ],
                },
            },
            "validation_output_budget": {
                "status": status,
                "file_count": 2004,
                "bytes": 571131205,
            },
            "hazard_output_budget": {
                "status": "recorded",
                "file_count": 54,
                "bytes": 75423367,
            },
            "reducer_scaling": {
                "status": "recorded" if not blocked else "blocked_before_scale_up",
                "local_restartability_status": "recorded",
                "reducer_chunk_manifest_status": "generated",
                "reducer_execution_index_status": "generated",
                "reducer_merge_state_status": "generated",
            },
        }

    def frontier_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_ensemble_frontier_v1",
            "frontier_status": "measured_existing_artifacts",
            "recommendation_class": "defer_small_bounded_ensemble",
            "recommendation_reason": "bounded feasibility remains informative",
            "minimum_useful_ensemble_recommendation": {
                "decision": "defer",
                "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
                "trajectory_count": 1000,
                "validation_output_mode": "rebuildable_reduced_output",
                "expected_output_file_count": 6,
                "expected_output_bytes": 1884291,
                "expected_artifact_families": [
                    "diagnostics_json",
                    "manifest_json",
                    "trajectory_csv",
                    "ensemble_deposition_csv",
                ],
                "expected_command": "command",
            },
        }

    def feasibility_report(self) -> dict[str, object]:
        return {
            "schema_version": "bounded_next_ensemble_feasibility_probe_v1",
            "probe_status": "deferred_pending_authorization",
            "bounded_probe_recommendation_status": "deferred_pending_authorization",
            "proposed_probe": {
                "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
                "trajectory_count": 1000,
                "validation_output_mode": "rebuildable_reduced_output",
                "expected_output_file_count": 6,
                "expected_output_bytes": 1884291,
                "expected_artifact_families": [
                    "diagnostics_json",
                    "manifest_json",
                    "trajectory_csv",
                    "ensemble_deposition_csv",
                ],
                "expected_command": "command",
            },
            "boundedness_proof": {
                "bounded_relative_to_target_validation": True,
                "bounded_relative_to_target_hazard": True,
            },
            "metadata_contract": {"status": "complete"},
            "command_plan_template": {
                "command": "PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case case.yaml"
            },
        }

    def manifest_report(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
