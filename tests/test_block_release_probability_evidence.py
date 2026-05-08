from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_block_release_probability_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_block_release_probability_evidence", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class BlockReleaseProbabilityEvidenceTests(unittest.TestCase):
    def test_selected_template_records_no_accepted_block_release_probability_evidence(self) -> None:
        summary = validator.validate_block_release_probability_evidence(
            ROOT / "validation/templates/block_release_probability_evidence_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "no_accepted_block_release_probability_evidence")
        self.assertEqual(summary["block_scenario_count"], 0)
        self.assertEqual(summary["release_cell_count"], 0)

    def test_accepts_complete_candidate_for_design_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_record(Path(tmp), self.candidate_record())

            summary = validator.validate_block_release_probability_evidence(path)

            self.assertEqual(summary["record_status"], "candidate_not_authorized")
            self.assertEqual(summary["block_scenario_count"], 2)
            self.assertEqual(summary["release_cell_count"], 4)
            self.assertFalse(summary["prototype_authorized"])

    def test_design_review_fixture_is_valid_but_not_runtime_authorized(self) -> None:
        summary = validator.validate_block_release_probability_evidence(
            ROOT / "tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "accepted_for_design_review")
        self.assertEqual(summary["block_scenario_count"], 2)
        self.assertEqual(summary["release_cell_count"], 4)
        self.assertFalse(summary["prototype_authorized"])

    def test_rejects_block_probabilities_that_do_not_sum_to_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["block_scenario_distribution"]["scenarios"][0]["probability"] = 0.4
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "block scenario probabilities"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_release_probabilities_that_do_not_sum_by_block_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["release_cell_distribution"]["release_cells"][0]["probability"] = 0.9
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "release-cell probabilities"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_release_cell_for_unknown_block_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["release_cell_distribution"]["release_cells"][0]["block_scenario_id"] = "unknown_block"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "unknown block_scenario_id"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_sampling_weight_reuse_as_physical_probability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["sampling_weight_boundary"]["sampling_weights_are_physical_probability"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "sampling_weights_are_physical_probability"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_missing_candidate_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["uncertainty"]["type"] = "not_available"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "candidate uncertainty"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_calibration_validation_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["block_inventory_review_v1"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "separate"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_swisstopo_as_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["swisstopo_swissimage_context"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "swisstopo"):
                validator.validate_block_release_probability_evidence(path)

    def test_rejects_prototype_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.BlockReleaseProbabilityEvidenceError, "prototype_authorized"):
                validator.validate_block_release_probability_evidence(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "block_release_probability_evidence.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def candidate_record(self) -> dict:
        return {
            "schema_version": "block_release_probability_evidence_v1",
            "record_id": "synthetic_candidate_block_release_probability_evidence_v1",
            "record_status": "candidate_not_authorized",
            "prototype_authorized": False,
            "operational_status": "research_diagnostic",
            "probability_model_id": "synthetic_block_release_model_v1",
            "probability_mode": "block_release_probability_evidence_only",
            "source_zone_id": "synthetic_source_zone_a",
            "source_geometry_version": "synthetic_source_zone_a_v1",
            "source_geometry_hash": "sha256:synthetic",
            "crs_epsg": 2056,
            "vertical_datum": "LN02",
            "source_event_class_id": "synthetic_detachment_class",
            "block_scenario_distribution": {
                "denominator": "conditional_probability_given_source_event",
                "total_probability": 1.0,
                "scenarios": [
                    {
                        "block_scenario_id": "block_small_sphere",
                        "block_size_class": "small",
                        "block_shape_class": "sphere",
                        "probability": 0.3,
                        "evidence_basis": "synthetic schema fixture",
                    },
                    {
                        "block_scenario_id": "block_large_sphere",
                        "block_size_class": "large",
                        "block_shape_class": "sphere",
                        "probability": 0.7,
                        "evidence_basis": "synthetic schema fixture",
                    },
                ],
            },
            "release_cell_distribution": {
                "denominator": "conditional_probability_given_source_event_and_block_scenario",
                "total_probability_by_block_scenario": [
                    {"block_scenario_id": "block_small_sphere", "total_probability": 1.0},
                    {"block_scenario_id": "block_large_sphere", "total_probability": 1.0},
                ],
                "release_cells": [
                    {
                        "block_scenario_id": "block_small_sphere",
                        "release_cell_id": "release_cell_001",
                        "probability": 0.6,
                        "evidence_basis": "synthetic schema fixture",
                    },
                    {
                        "block_scenario_id": "block_small_sphere",
                        "release_cell_id": "release_cell_002",
                        "probability": 0.4,
                        "evidence_basis": "synthetic schema fixture",
                    },
                    {
                        "block_scenario_id": "block_large_sphere",
                        "release_cell_id": "release_cell_001",
                        "probability": 0.5,
                        "evidence_basis": "synthetic schema fixture",
                    },
                    {
                        "block_scenario_id": "block_large_sphere",
                        "release_cell_id": "release_cell_002",
                        "probability": 0.5,
                        "evidence_basis": "synthetic schema fixture",
                    },
                ],
            },
            "sampling_weight_boundary": {
                "sampling_weights_are_physical_probability": False,
                "sampling_weight_column_allowed_as_probability": False,
            },
            "uncertainty": {
                "type": "expert_range",
                "required_before_prototype": True,
                "notes": "Synthetic candidate uncertainty for schema review only.",
            },
            "evidence_basis": {
                "block_distribution": "expert_elicitation",
                "release_cell_distribution": "inventory_measurement",
            },
            "calibration_dataset_ids": ["block_inventory_review_v1"],
            "validation_dataset_ids": ["independent_holdout_review_v1"],
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
