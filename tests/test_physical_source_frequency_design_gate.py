from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_physical_source_frequency_design_gate.py"
SPEC = importlib.util.spec_from_file_location("validate_physical_source_frequency_design_gate", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PhysicalSourceFrequencyDesignGateTests(unittest.TestCase):
    def test_selected_gate_record_is_valid_and_deferred(self) -> None:
        summary = validator.validate_design_gate_record(
            ROOT / "validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml"
        )

        self.assertEqual(summary["decision"], "deferred")
        self.assertFalse(summary["annual_physical_prototype_authorized"])

    def test_rejects_authorized_prototype_in_current_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["decision"] = "authorize_prototype"
            record["annual_physical_prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalSourceFrequencyGateError, "unsupported"):
                validator.validate_design_gate_record(path)

    def test_rejects_missing_source_rate_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["required_frequency_units"].pop("source_event_rate")
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalSourceFrequencyGateError, "source_event_rate"):
                validator.validate_design_gate_record(path)

    def test_rejects_sampling_weight_reused_as_physical_probability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["required_evidence"]["block_scenario_distribution"].remove(
                "sampling_weight_not_reused_as_physical_probability"
            )
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalSourceFrequencyGateError, "sampling-weight reuse"):
                validator.validate_design_gate_record(path)

    def test_rejects_missing_overlap_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["overlap_policy"]["requirements"] = []
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalSourceFrequencyGateError, "overlap_policy"):
                validator.validate_design_gate_record(path)

    def test_rejects_missing_rejection_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["rejection_tests_required_before_prototype"].remove("missing_rate_uncertainty")
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalSourceFrequencyGateError, "missing_rate_uncertainty"):
                validator.validate_design_gate_record(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "physical_source_frequency_design_gate.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
