from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_scalable_conditional_target_gate.py"
SPEC = importlib.util.spec_from_file_location("validate_scalable_conditional_target_gate", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ScalableConditionalTargetGateTests(unittest.TestCase):
    def test_selected_blocked_missing_inputs_record_is_valid(self) -> None:
        summary = validator.validate_target_gate_record(
            ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
        )

        self.assertEqual(summary["gate_status"], "blocked_missing_inputs")
        self.assertEqual(summary["missing_path_count"], 5)

    def test_rejects_full_curve_export_for_target_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["target_execution_plan"]["conditional_curve_export_mode"] = "full"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalTargetGateError, "summary-only"):
                validator.validate_target_gate_record(path)

    def test_rejects_missing_validation_runner_workers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["target_execution_plan"]["validation_runner_ensemble_workers_required"] = False
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalTargetGateError, "ensemble workers"):
                validator.validate_target_gate_record(path)

    def test_rejects_blocked_record_that_started_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["local_input_check"]["target_execution_started"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalTargetGateError, "must not start"):
                validator.validate_target_gate_record(path)

    def test_rejects_missing_required_path_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["local_input_check"]["required_paths"] = [
                row
                for row in record["local_input_check"]["required_paths"]
                if row["role"] != "selected_scenario_table"
            ]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalTargetGateError, "selected_scenario_table"):
                validator.validate_target_gate_record(path)

    def test_rejects_physical_probability_claim_boundary_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["claim_boundary"]["physical_probability"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ScalableConditionalTargetGateError, "physical_probability"):
                validator.validate_target_gate_record(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "target_gate.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
