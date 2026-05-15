from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_conditional_convergence_protocol.py"
SPEC = importlib.util.spec_from_file_location("validate_conditional_convergence_protocol", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ConditionalConvergenceProtocolTests(unittest.TestCase):
    def test_selected_protocol_record_is_valid(self) -> None:
        summary = validator.validate_protocol_record(
            ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
        )

        self.assertEqual(summary["current_classification"], "inconclusive")
        self.assertFalse(summary["scale_up_authorized"])
        self.assertEqual(summary["blocking_reason_count"], 4)

    def test_rejects_missing_dt04_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["assessment"]["assessed_records"]["dt04_balfrin_reproduction_record"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ConditionalConvergenceProtocolError, "DT-04 Balfrin record"):
                validator.validate_protocol_record(path)

    def test_rejects_missing_convergence_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["assessment"]["evidence"]["convergence_indicators"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ConditionalConvergenceProtocolError, "all required categories"):
                validator.validate_protocol_record(path)

    def test_rejects_operational_annual_and_risk_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["classification_rationale"] = "This is an operational hazard map with annual frequency and risk-map semantics."
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ConditionalConvergenceProtocolError, "misleading"):
                validator.validate_protocol_record(path)

    def test_rejects_scale_up_authorization_without_passed_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["assessment"]["scale_up_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ConditionalConvergenceProtocolError, "non-pass records must not authorize scale-up"):
                validator.validate_protocol_record(path)

    def test_rejects_unsupported_classification_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["assessment"]["current_classification"] = "maybe"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ConditionalConvergenceProtocolError, "current_classification is invalid"):
                validator.validate_protocol_record(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "conditional_convergence_protocol.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
