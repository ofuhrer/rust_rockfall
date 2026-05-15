from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_balfrin_tschamut_readiness_record.py"
RECORD_PATH = ROOT / "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml"
SPEC = importlib.util.spec_from_file_location("validate_balfrin_tschamut_readiness_record", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class BalfrinReadinessRecordTests(unittest.TestCase):
    def load_record(self) -> dict:
        return yaml.safe_load(RECORD_PATH.read_text(encoding="utf-8"))

    def write_record(self, record: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        with tmp:
            yaml.safe_dump(record, tmp, sort_keys=False)
        return Path(tmp.name)

    def assert_rejected(self, record: dict, expected: str) -> None:
        path = self.write_record(record)
        try:
            with self.assertRaisesRegex(validator.BalfrinReadinessRecordError, expected):
                validator.validate_balfrin_readiness_record(path)
        finally:
            path.unlink(missing_ok=True)

    def test_selected_balfrin_readiness_record_is_valid(self) -> None:
        summary = validator.validate_balfrin_readiness_record(RECORD_PATH)
        self.assertEqual(summary["readiness_status"], "ready_for_balfrin_target_gate")
        self.assertEqual(summary["missing_required_inputs"], 0)
        self.assertEqual(summary["missing_processed_artifacts"], 0)

    def test_rejects_ready_record_with_missing_required_input(self) -> None:
        record = self.load_record()
        record["required_ignored_inputs"]["items"][0]["status"] = "missing"
        record["required_ignored_inputs"]["missing_required_count"] = 1
        self.assert_rejected(record, "missing_required_count must be 0")

    def test_rejects_record_without_processed_dem_artifact(self) -> None:
        record = self.load_record()
        record["processed_artifacts"]["items"] = [
            row for row in record["processed_artifacts"]["items"] if row["role"] != "processed_public_dem"
        ]
        self.assert_rejected(record, "processed_artifacts.items missing roles")

    def test_rejects_ready_record_with_blocking_checker_count(self) -> None:
        record = self.load_record()
        record["checker"]["blocking_check_count"] = 1
        self.assert_rejected(record, "zero blocking checks")

    def test_rejects_missing_command_plan_precondition(self) -> None:
        record = self.load_record()
        record["command_plan_preconditions"]["required_commands_present"].remove("run_validation_gate")
        self.assert_rejected(record, "required_commands_present missing")

    def test_rejects_operational_claim_boundary_drift(self) -> None:
        record = self.load_record()
        record["claim_boundary"]["operational_hazard_map"] = True
        self.assert_rejected(record, "operational_hazard_map must be false")

    def test_blocked_record_requires_nonzero_checker_returncode_and_blocker(self) -> None:
        record = copy.deepcopy(self.load_record())
        record["readiness_status"] = "blocked_for_balfrin_readiness"
        record["checker"]["output_status"] = "blocked_for_balfrin_readiness"
        self.assert_rejected(record, "nonzero checker returncode")
        record["checker"]["returncode"] = 2
        self.assert_rejected(record, "blocking checks")


if __name__ == "__main__":
    unittest.main()
