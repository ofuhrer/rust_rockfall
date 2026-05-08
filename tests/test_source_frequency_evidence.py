from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_source_frequency_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_source_frequency_evidence", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class SourceFrequencyEvidenceTests(unittest.TestCase):
    def test_selected_template_records_no_accepted_frequency_evidence(self) -> None:
        summary = validator.validate_source_frequency_evidence(
            ROOT / "validation/templates/source_frequency_evidence_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "no_accepted_frequency_evidence")
        self.assertFalse(summary["source_event_rate_available"])

    def test_accepts_complete_candidate_for_design_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_record(Path(tmp), self.candidate_record())

            summary = validator.validate_source_frequency_evidence(path)

            self.assertEqual(summary["record_status"], "candidate_not_authorized")
            self.assertTrue(summary["source_event_rate_available"])
            self.assertFalse(summary["prototype_authorized"])

    def test_design_review_fixture_is_valid_but_not_runtime_authorized(self) -> None:
        summary = validator.validate_source_frequency_evidence(
            ROOT / "tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "accepted_for_design_review")
        self.assertTrue(summary["source_event_rate_available"])
        self.assertFalse(summary["prototype_authorized"])

    def test_rejects_candidate_missing_source_rate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["source_event_rate_per_year"] = None
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "source_event_rate_per_year"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_invalid_frequency_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["frequency_unit"] = "sampling_weight"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "frequency_unit"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_uncertainty_that_excludes_rate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["rate_uncertainty"]["lower_per_year"] = 0.0
            record["rate_uncertainty"]["upper_per_year"] = 0.001
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "interval"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_missing_overlap_adjustment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["source_zone_overlap_policy"]["overlap_adjustment"] = "required_before_prototype"
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "overlap adjustment"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_calibration_validation_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["inventory_rate_review_v1"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "separate"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_swisstopo_as_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["swisstopo_swissalti3d_tile_2696_1167"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "swisstopo"):
                validator.validate_source_frequency_evidence(path)

    def test_rejects_prototype_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.SourceFrequencyEvidenceError, "prototype_authorized"):
                validator.validate_source_frequency_evidence(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "source_frequency_evidence.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def candidate_record(self) -> dict:
        return {
            "schema_version": "source_frequency_evidence_v1",
            "record_id": "synthetic_candidate_source_frequency_evidence_v1",
            "record_status": "candidate_not_authorized",
            "prototype_authorized": False,
            "operational_status": "research_diagnostic",
            "frequency_model_id": "synthetic_frequency_model_v1",
            "frequency_mode": "source_event_rate_evidence_only",
            "source_zone_id": "synthetic_source_zone_a",
            "source_geometry_version": "synthetic_source_zone_a_v1",
            "source_geometry_hash": "sha256:synthetic",
            "crs_epsg": 2056,
            "vertical_datum": "LN02",
            "source_event_class": {
                "event_class_id": "synthetic_detachment_class",
                "description": "Synthetic schema fixture for design review only.",
                "occurrence_denominator": "source_zone_event_class",
            },
            "frequency_unit": "events_per_source_zone_per_year",
            "source_event_rate_per_year": 0.02,
            "rate_time_window_years": 50,
            "rate_observation_period": {
                "start_year": 1970,
                "end_year": 2020,
            },
            "rate_evidence_type": "inventory_count",
            "rate_provenance": {
                "source": "synthetic fixture",
                "citation_or_url": "synthetic fixture only",
                "license": "not applicable",
            },
            "rate_uncertainty": {
                "type": "interval",
                "lower_per_year": 0.005,
                "upper_per_year": 0.08,
            },
            "source_zone_overlap_policy": {
                "policy": "mutually_exclusive_partition",
                "overlap_adjustment": "not_needed_for_synthetic_partition",
            },
            "calibration_dataset_ids": ["inventory_rate_review_v1"],
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
