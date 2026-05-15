from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_stochastic_sampling_audit.py"
SPEC = importlib.util.spec_from_file_location("validate_stochastic_sampling_audit", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class StochasticSamplingAuditTests(unittest.TestCase):
    def test_current_record_is_valid(self) -> None:
        summary = validator.validate_stochastic_sampling_audit(
            ROOT / "validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml"
        )

        self.assertEqual(summary["current_classification"], "diagnostic_incomplete")
        self.assertFalse(summary["stochastic_validity_accepted"])
        self.assertFalse(summary["scale_up_authorized"])

    def test_rejects_missing_stream_separation_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["stream_separation_assessment"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.StochasticSamplingAuditError, "stream_separation_assessment"):
                validator.validate_stochastic_sampling_audit(path)

    def test_rejects_missing_distribution_truncation_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["distribution_truncation_support"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.StochasticSamplingAuditError, "distribution_truncation_support"):
                validator.validate_stochastic_sampling_audit(path)

    def test_rejects_stochastic_validity_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["stochastic_validity_accepted"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.StochasticSamplingAuditError, "stochastic_validity_accepted"):
                validator.validate_stochastic_sampling_audit(path)

    def test_rejects_rng_default_or_physics_change_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in (
                "physics_changes_claimed",
                "rng_changes_claimed",
                "stochastic_default_changes_claimed",
            ):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.StochasticSamplingAuditError, field):
                    validator.validate_stochastic_sampling_audit(path)

    def test_rejects_annual_physical_risk_operational_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in (
                "annual_or_physical_probability_claimed",
                "risk_exposure_or_operational_claimed",
                "accepted_stochastic_validity_claimed",
            ):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.StochasticSamplingAuditError, field):
                    validator.validate_stochastic_sampling_audit(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "stochastic_sampling_audit.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
