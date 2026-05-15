from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_output_budget_reducer_gate.py"
SPEC = importlib.util.spec_from_file_location("validate_output_budget_reducer_gate", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class OutputBudgetReducerGateTests(unittest.TestCase):
    def test_current_record_is_valid(self) -> None:
        summary = validator.validate_output_budget_reducer_gate(
            ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
        )

        self.assertEqual(summary["current_classification"], "blocked_before_scale_up")
        self.assertEqual(summary["qa_status"], "diagnostic_incomplete")

    def test_rejects_missing_validation_output_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["validation_output_budget"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, "validation_output_budget"):
                validator.validate_output_budget_reducer_gate(path)

    def test_rejects_missing_hazard_output_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["hazard_output_budget"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, "hazard_output_budget"):
                validator.validate_output_budget_reducer_gate(path)

    def test_rejects_missing_reducer_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["reducer_scaling"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, "reducer_scaling"):
                validator.validate_output_budget_reducer_gate(path)

    def test_rejects_passed_while_blockers_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["current_classification"] = "passed"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, "passed records must not retain blockers"):
                validator.validate_output_budget_reducer_gate(path)

    def test_rejects_scale_up_authorization_while_blockers_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["scale_up_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, "scale_up_authorized must be false"):
                validator.validate_output_budget_reducer_gate(path)

    def test_rejects_scalable_output_default_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("full_curve_csv_default_claimed", "grid_csv_default_claimed"):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, field):
                    validator.validate_output_budget_reducer_gate(path)

    def test_rejects_physics_reducer_behavior_and_output_default_change_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("physics_changes_claimed", "reducer_behavior_changes_claimed", "output_default_changes_claimed", "distributed_execution_claimed"):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, field):
                    validator.validate_output_budget_reducer_gate(path)

    def test_rejects_annual_physical_risk_operational_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("ensemble_size_increase_claimed", "annual_or_physical_claimed", "risk_exposure_or_operational_claimed", "return_period_claimed", "validated_hazard_map_claimed"):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.OutputBudgetReducerGateError, field):
                    validator.validate_output_budget_reducer_gate(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "output_budget_reducer_gate.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
