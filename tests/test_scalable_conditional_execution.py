from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_scalable_conditional_execution.py"
SPEC = importlib.util.spec_from_file_location("validate_scalable_conditional_execution", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ScalableConditionalExecutionTests(unittest.TestCase):
    def test_selected_tschamut_record_is_valid_and_not_authorized_for_scale_up(self) -> None:
        summary = validator.validate_scalable_conditional_execution(
            ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml"
        )

        self.assertEqual(summary["decision"], "design_ready_not_authorized_for_scale_up")
        self.assertEqual(summary["remaining_blocker_count"], 4)

    def test_rejects_full_curve_table_for_scale_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["execution_contract"]["conditional_curve_export"][
                "full_curve_table_allowed_for_scale_up"
            ] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalExecutionError, "full curve table"):
                validator.validate_scalable_conditional_execution(path)

    def test_rejects_nondeterministic_merge_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["execution_contract"]["deterministic_chunking"]["merge_order"] = "completion_order"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalExecutionError, "sorted_chunk_id"):
                validator.validate_scalable_conditional_execution(path)

    def test_rejects_missing_convergence_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["convergence_diagnostics"]["required_before_increase"].remove(
                "worker_count_reducer_parity"
            )
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalExecutionError, "worker_count_reducer_parity"):
                validator.validate_scalable_conditional_execution(path)

    def test_rejects_physical_probability_claim_boundary_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["claim_boundary"]["physical_probability"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalExecutionError, "physical_probability"):
                validator.validate_scalable_conditional_execution(path)

    def test_rejects_unqualified_risk_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["decision_rationale"] = "Proceed to a risk map."
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalExecutionError, "misleading current-product claim"):
                validator.validate_scalable_conditional_execution(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "scalable_conditional_execution.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
