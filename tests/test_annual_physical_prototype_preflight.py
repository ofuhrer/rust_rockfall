from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_annual_physical_prototype_preflight.py"
SPEC = importlib.util.spec_from_file_location("validate_annual_physical_prototype_preflight", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class AnnualPhysicalPrototypePreflightTests(unittest.TestCase):
    def test_selected_preflight_is_valid_and_blocked(self) -> None:
        summary = validator.validate_prototype_preflight(
            ROOT / "validation/templates/annual_physical_prototype_preflight_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "blocked_by_design_gate")
        self.assertFalse(summary["prototype_authorized"])
        self.assertEqual(summary["design_gate_decision"], "deferred")
        self.assertFalse(summary["design_gate_authorized"])
        self.assertEqual(summary["remaining_blocker_count"], 5)

    def test_rejects_prototype_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalPrototypePreflightError, "prototype_authorized"):
                validator.validate_prototype_preflight(path)

    def test_rejects_runtime_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["runtime_support_added"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalPrototypePreflightError, "runtime_support_added"):
                validator.validate_prototype_preflight(path)

    def test_rejects_missing_remaining_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["remaining_blockers"].remove("implemented_uncertainty_propagation")
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalPrototypePreflightError, "remaining_blockers"):
                validator.validate_prototype_preflight(path)

    def test_rejects_observed_gate_decision_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["observed_design_gate_decision"] = "authorize_prototype"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalPrototypePreflightError, "observed_design_gate_decision"):
                validator.validate_prototype_preflight(path)

    def test_rejects_missing_gate_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["design_gate_record"] = "validation/pilot_runs/missing_design_gate.yaml"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalPrototypePreflightError, "does not exist"):
                validator.validate_prototype_preflight(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "annual_physical_prototype_preflight.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/templates/annual_physical_prototype_preflight_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
