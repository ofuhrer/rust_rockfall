from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_single_job_execution.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_single_job_execution", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary_script)


class BalfrinSingleJobExecutionSummaryTests(unittest.TestCase):
    def load_record(self, path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def write_record(self, record: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        with tmp:
            yaml.safe_dump(record, tmp, sort_keys=False)
        return Path(tmp.name)

    def assert_rejected(self, **record_paths: Path) -> None:
        summary = summary_script.build_summary(**record_paths)
        self.assertEqual(summary["decision"], "blocked_pending_evidence")
        self.assertFalse(summary["single_job_sufficient_for_next_step"])

    def test_current_records_classify_as_defer_and_expose_contract_fields(self) -> None:
        summary = summary_script.build_summary()

        self.assertEqual(summary["schema_version"], "balfrin_single_job_execution_sufficiency_v1")
        self.assertEqual(summary["decision"], "defer")
        self.assertEqual(summary["feasibility_decision"], "defer")
        self.assertEqual(summary["final_classification"], "defer")
        self.assertTrue(summary["single_job_sufficient_for_next_step"])
        self.assertFalse(summary["distributed_execution_authorized"])
        self.assertFalse(summary["defaults_changed"])
        self.assertEqual(summary["validation_output_blocker_status"], "blocker_retained")
        self.assertEqual(summary["file_family_pressure"], "validation_debug_artifacts")
        self.assertEqual(summary["restartability_evidence"]["driver_ready_for_selected_gate_use"], True)
        self.assertEqual(summary["reducer_state_evidence"]["reducer_workers"], 2)
        self.assertEqual(summary["reducer_state_evidence"]["reducer_chunk_count"], 2)
        self.assertEqual(summary["wall_time_evidence"]["current_gap_runtime_seconds"], 17.84)
        self.assertEqual(summary["memory_evidence"]["current_gap_memory_peak_mb"], 409.22)
        self.assertEqual(summary["output_size_evidence"]["current_gap_output_file_count"], 191)
        self.assertEqual(summary["output_size_evidence"]["current_gap_output_bytes"], 267527120)
        blocker_names = {entry["name"] for entry in summary["scientific_blockers"]}
        self.assertIn("validation_debug_output_budget_retained", blocker_names)
        self.assertIn("forest_obstacle_context_limiting", blocker_names)
        self.assertEqual(summary["recommended_next_step"].startswith("Continue using the single-job Balfrin"), True)

    def test_schema_field_names_remain_stable_for_downstream_acceptance_summaries(self) -> None:
        summary = summary_script.build_summary()
        expected_keys = {
            "schema_version",
            "pilot_id",
            "run_id",
            "measurement_status",
            "decision",
            "feasibility_decision",
            "final_classification",
            "single_job_sufficient_for_next_step",
            "distributed_execution_authorized",
            "defaults_changed",
            "file_family_pressure",
            "validation_output_blocker_status",
            "record_paths",
            "wall_time_evidence",
            "memory_evidence",
            "output_size_evidence",
            "restartability_evidence",
            "reducer_state_evidence",
            "scientific_blockers",
            "execution_blockers",
            "required_inputs",
            "current_pressure",
            "limitations",
            "recommended_next_step",
        }
        self.assertTrue(expected_keys.issubset(summary.keys()))

    def test_rejects_missing_inputs_as_blocked_pending_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            summary = summary_script.build_summary(
                repeatability_record=work / "missing-repeatability.yaml",
                reproduction_record=work / "missing-reproduction.yaml",
                output_budget_record=work / "missing-output-budget.yaml",
                convergence_record=work / "missing-convergence.yaml",
                feasibility_record=work / "missing-feasibility.yaml",
                current_gap_record=work / "missing-current-gap.yaml",
            )

            self.assertEqual(summary["decision"], "blocked_pending_evidence")
            self.assertEqual(summary["measurement_status"], "blocked_pending_evidence")
            self.assertEqual(summary["feasibility_decision"], "blocked_pending_evidence")
            self.assertFalse(summary["distributed_execution_authorized"])
            self.assertEqual(len(summary["missing_required_inputs"]), 6)

    def test_design_needed_when_restartability_is_not_demonstrated(self) -> None:
        repeatability = self.load_record(ROOT / "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml")
        repeatability["selected_gate_readiness_decision"]["driver_ready_for_selected_gate_use"] = False

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            repeatability_path = self.write_record(repeatability)
            try:
                summary = summary_script.build_summary(
                    repeatability_record=repeatability_path,
                    reproduction_record=ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                    output_budget_record=ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml",
                    convergence_record=ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
                    feasibility_record=ROOT / "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
                    current_gap_record=ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                )
            finally:
                repeatability_path.unlink(missing_ok=True)

        self.assertEqual(summary["decision"], "design_needed")
        self.assertFalse(summary["single_job_sufficient_for_next_step"])
        self.assertFalse(summary["distributed_execution_authorized"])


if __name__ == "__main__":
    unittest.main()
