from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_balfrin_slurm_probe_repeatability.py"
RECORD_PATH = ROOT / "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml"
SPEC = importlib.util.spec_from_file_location("validate_balfrin_slurm_probe_repeatability", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class BalfrinSlurmProbeRepeatabilityTests(unittest.TestCase):
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
            with self.assertRaisesRegex(validator.SlurmProbeRepeatabilityError, expected):
                validator.validate_probe_repeatability_record(path)
        finally:
            path.unlink(missing_ok=True)

    def test_selected_slurm_probe_repeatability_record_is_valid(self) -> None:
        summary = validator.validate_probe_repeatability_record(RECORD_PATH)
        self.assertEqual(summary["classification"], "pass_with_scope_limits")
        self.assertEqual(summary["driver_decision"], "ready_for_same_scale_selected_gate_reproduction")
        self.assertEqual(summary["repeat_run_count"], 2)

    def test_rejects_repeat_without_reused_trajectory_chunks(self) -> None:
        record = self.load_record()
        record["repeat_runs"][0]["trajectory_decision_counts"] = {"executed": 2}
        self.assert_rejected(record, "reused_completed_state")

    def test_rejects_plan_id_drift_between_repeat_runs(self) -> None:
        record = self.load_record()
        record["repeat_runs"][1]["trajectory_plan_id"] = "different-plan"
        self.assert_rejected(record, "trajectory plan ids must be stable")

    def test_rejects_changed_numeric_artifacts(self) -> None:
        record = self.load_record()
        record["numerical_artifact_stability"]["changed_artifact_count"] = 1
        record["numerical_artifact_stability"]["changed_paths"] = ["hazard/results/example.tif"]
        self.assert_rejected(record, "changed_artifact_count must be zero")

    def test_rejects_dirty_log_audit(self) -> None:
        record = self.load_record()
        record["log_audit_assessment"]["error_like_line_count"] = 1
        self.assert_rejected(record, "log audit error count must be zero")

    def test_rejects_scale_up_authorization(self) -> None:
        record = self.load_record()
        record["selected_gate_readiness_decision"]["not_authorized"].remove("ensemble_size_increase")
        self.assert_rejected(record, "not_authorized missing")

    def test_rejects_public_claim_boundary_drift(self) -> None:
        record = self.load_record()
        record["claim_boundary"]["operational_hazard_map"] = True
        self.assert_rejected(record, "operational_hazard_map must be false")


if __name__ == "__main__":
    unittest.main()
