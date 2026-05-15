from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_dem_input_conditioning_qa.py"
SPEC = importlib.util.spec_from_file_location("validate_dem_input_conditioning_qa", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class DemInputConditioningQATests(unittest.TestCase):
    def test_current_record_is_valid(self) -> None:
        summary = validator.validate_dem_input_conditioning_qa(
            ROOT / "validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml"
        )

        self.assertEqual(summary["current_classification"], "blocked_pending_local_evidence")
        self.assertEqual(summary["qa_status"], "diagnostic_incomplete")

    def test_rejects_missing_raw_input_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["raw_input_evidence"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.DemInputConditioningQAError, "raw_input_evidence"):
                validator.validate_dem_input_conditioning_qa(path)

    def test_rejects_missing_crs_registration_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            del record["crs_and_registration_evidence"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.DemInputConditioningQAError, "crs_and_registration_evidence"):
                validator.validate_dem_input_conditioning_qa(path)

    def test_rejects_passed_while_blockers_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["current_classification"] = "passed"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.DemInputConditioningQAError, "passed records must not retain blockers"):
                validator.validate_dem_input_conditioning_qa(path)

    def test_rejects_dem_behavior_or_physics_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("stochastic_or_physics_change_claimed", "dem_behavior_change_claimed", "tuning_claimed"):
                record = self.base_record()
                record[field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.DemInputConditioningQAError, field):
                    validator.validate_dem_input_conditioning_qa(path)

    def test_rejects_annual_physical_risk_operational_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("annual_or_physical_probability_claimed", "risk_exposure_or_operational_claimed", "return_period_claimed", "validated_hazard_map_claimed"):
                record = self.base_record()
                record["claim_boundary"][field] = True
                path = self.write_record(Path(tmp), record)

                with self.assertRaisesRegex(validator.DemInputConditioningQAError, field):
                    validator.validate_dem_input_conditioning_qa(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "dem_input_conditioning_qa.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        path = ROOT / "validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
