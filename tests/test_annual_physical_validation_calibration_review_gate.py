from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_annual_physical_validation_calibration_review_gate.py"
SPEC = importlib.util.spec_from_file_location("validate_annual_physical_validation_calibration_review_gate", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class AnnualPhysicalValidationCalibrationReviewGateTests(unittest.TestCase):
    def test_selected_template_records_review_not_passed(self) -> None:
        summary = validator.validate_annual_physical_validation_calibration_review_gate(
            ROOT / "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "review_not_passed")
        self.assertFalse(summary["prototype_authorized"])
        self.assertEqual(summary["validation_dataset_count"], 0)

    def test_accepts_complete_candidate_for_design_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_record(Path(tmp), self.candidate_record())

            summary = validator.validate_annual_physical_validation_calibration_review_gate(path)

            self.assertEqual(summary["record_status"], "candidate_not_authorized")
            self.assertEqual(summary["calibration_dataset_count"], 1)
            self.assertEqual(summary["validation_dataset_count"], 1)
            self.assertEqual(summary["holdout_dataset_count"], 1)
            self.assertFalse(summary["prototype_authorized"])

    def test_rejects_missing_record_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["required_record_references"]["source_frequency_evidence_record"] = None
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "source_frequency_evidence_record"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_missing_no_tuning_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["calibration_review"]["no_tuning_to_validation_or_map_pattern"] = False
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "no_tuning"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_missing_validation_maturity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_review"]["maturity_target"] = None
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "maturity_target"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_calibration_validation_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_review"]["dataset_ids"] = ["frequency_calibration_v1"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "calibration/validation"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_validation_holdout_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["holdout_review"]["dataset_ids"] = ["frequency_validation_v1"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "validation/holdout"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_swisstopo_as_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_review"]["dataset_ids"] = ["swisstopo_swissalti3d_context"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "swisstopo"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_claim_boundary_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["claim_boundary"]["operational_hazard_map_supported"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "operational_hazard_map_supported"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def test_rejects_prototype_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.AnnualPhysicalValidationCalibrationReviewGateError, "prototype_authorized"):
                validator.validate_annual_physical_validation_calibration_review_gate(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "annual_physical_validation_calibration_review_gate.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def candidate_record(self) -> dict:
        return {
            "schema_version": "annual_physical_validation_calibration_review_gate_v1",
            "record_id": "synthetic_candidate_annual_physical_review_gate_v1",
            "record_status": "candidate_not_authorized",
            "prototype_authorized": False,
            "operational_status": "research_diagnostic",
            "review_mode": "annual_physical_validation_calibration_review_only",
            "product_scope": {
                "current_products": [
                    "unweighted_diagnostic",
                    "sampling_weighted_conditional",
                    "conditional_intensity_exceedance",
                ],
                "future_products_reviewed": [
                    "physical_probability",
                    "annual_intensity_frequency",
                ],
                "runtime_support_added": False,
            },
            "required_record_references": {
                "source_frequency_evidence_record": "source_frequency_evidence_v1.yaml",
                "block_release_probability_evidence_record": "block_release_probability_evidence_v1.yaml",
                "physical_frequency_reducer_preconditions_record": "physical_frequency_reducer_preconditions_v1.yaml",
            },
            "calibration_review": {
                "status": "defined_for_design_review",
                "objective": "Synthetic calibration review fixture.",
                "dataset_ids": ["frequency_calibration_v1"],
                "no_tuning_to_validation_or_map_pattern": True,
            },
            "validation_review": {
                "status": "defined_for_design_review",
                "objective": "Synthetic validation review fixture.",
                "dataset_ids": ["frequency_validation_v1"],
                "maturity_target": "V3",
                "current_maturity_cap": "V2",
            },
            "holdout_review": {
                "status": "defined_for_design_review",
                "dataset_ids": ["frequency_holdout_v1"],
                "external_generalization_required": True,
            },
            "dataset_role_boundaries": {
                "calibration_validation_holdout_overlap_allowed": False,
                "swisstopo_input_geodata_is_validation_evidence": False,
                "exposure_or_vulnerability_required_for_risk": True,
            },
            "claim_boundary": {
                "annual_frequency_supported": False,
                "physical_probability_supported": False,
                "return_period_supported": False,
                "operational_hazard_map_supported": False,
                "risk_or_exposure_supported": False,
            },
            "limitations": ["synthetic schema fixture only", "not used by runtime products"],
        }


if __name__ == "__main__":
    unittest.main()
