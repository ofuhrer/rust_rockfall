from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_balfrin_target_gate_reproduction.py"
RECORD_PATH = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml"
SPEC = importlib.util.spec_from_file_location("validate_balfrin_target_gate_reproduction", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class BalfrinTargetGateReproductionTests(unittest.TestCase):
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
            with self.assertRaisesRegex(validator.BalfrinTargetGateReproductionError, expected):
                validator.validate_target_gate_reproduction_record(path)
        finally:
            path.unlink(missing_ok=True)

    def test_selected_balfrin_target_gate_reproduction_record_is_valid(self) -> None:
        summary = validator.validate_target_gate_reproduction_record(RECORD_PATH)
        self.assertEqual(summary["reproducibility_classification"], "inconclusive")
        self.assertEqual(summary["simulated_trajectory_count"], 1000)
        self.assertEqual(summary["job_id"], "4318941")

    def test_rejects_non_target_trajectory_count(self) -> None:
        record = self.load_record()
        record["physics_and_sampling"]["simulated_trajectory_count"] = 999
        self.assert_rejected(record, "simulated_trajectory_count must be 1000")

    def test_rejects_full_conditional_curve_csv(self) -> None:
        record = self.load_record()
        record["hazard_output_profile"]["conditional_curve_export"] = "full-csv"
        record["hazard_output_profile"]["conditional_curve_csv_written"] = True
        self.assert_rejected(record, "conditional_curve_export must be summary-only")

    def test_rejects_grid_csv_export(self) -> None:
        record = self.load_record()
        record["hazard_output_profile"]["grid_csv_export"] = "full"
        self.assert_rejected(record, "grid_csv_export must be none")

    def test_rejects_missing_checksum(self) -> None:
        record = self.load_record()
        del record["checksums"]["hazard_manifest"]
        self.assert_rejected(record, "checksums missing")

    def test_rejects_dirty_log_audit(self) -> None:
        record = self.load_record()
        record["log_audit"]["warning_like_line_count"] = 1
        self.assert_rejected(record, "log audit warning count must be zero")

    def test_rejects_operational_claim_boundary(self) -> None:
        record = self.load_record()
        record["claim_boundary"]["operational_hazard_map"] = True
        self.assert_rejected(record, "operational_hazard_map must be false")

    def test_rejects_scale_up_classification(self) -> None:
        record = self.load_record()
        record["reproducibility_classification"] = "passed"
        self.assert_rejected(record, "current DT-04 record must remain inconclusive")


if __name__ == "__main__":
    unittest.main()
