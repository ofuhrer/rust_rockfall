from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_physical_frequency_reducer_preconditions.py"
SPEC = importlib.util.spec_from_file_location("validate_physical_frequency_reducer_preconditions", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PhysicalFrequencyReducerPreconditionsTests(unittest.TestCase):
    def test_selected_template_records_unsatisfied_preconditions(self) -> None:
        summary = validator.validate_physical_frequency_reducer_preconditions(
            ROOT / "validation/templates/physical_frequency_reducer_preconditions_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "preconditions_not_satisfied")
        self.assertIsNone(summary["selected_overlap_policy"])
        self.assertFalse(summary["prototype_authorized"])

    def test_accepts_complete_candidate_for_design_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_record(Path(tmp), self.candidate_record())

            summary = validator.validate_physical_frequency_reducer_preconditions(path)

            self.assertEqual(summary["record_status"], "candidate_not_authorized")
            self.assertEqual(summary["selected_overlap_policy"], "mutually_exclusive_partition")
            self.assertFalse(summary["prototype_authorized"])

    def test_design_review_fixture_is_valid_but_not_runtime_authorized(self) -> None:
        summary = validator.validate_physical_frequency_reducer_preconditions(
            ROOT / "tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml"
        )

        self.assertEqual(summary["record_status"], "accepted_for_design_review")
        self.assertEqual(summary["selected_overlap_policy"], "documented_overlap_adjustment")
        self.assertFalse(summary["prototype_authorized"])

    def test_rejects_missing_overlap_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["overlap_policy"]["selected_policy"] = None
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "selected_policy"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_missing_double_counting_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["overlap_policy"]["double_counting_guard_required"] = False
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "double_counting_guard"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_nondeterministic_reducer_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["reducer_contract"]["order_independent_required"] = False
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "order_independent"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_active_annual_or_physical_output_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["reducer_contract"]["annual_or_physical_output_supported"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "annual_or_physical_output_supported"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_missing_uncertainty_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["uncertainty_propagation"]["required_components"].remove("terrain_model_form_uncertainty")
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "terrain_model_form_uncertainty"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_missing_uncertainty_output_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["uncertainty_propagation"]["output_summary_fields"] = []
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "output_summary_fields"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_calibration_validation_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["frequency_reducer_calibration_v1"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "separate"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_swisstopo_as_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["validation_dataset_ids"] = ["swisstopo_swissalti3d_context"]
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "swisstopo"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def test_rejects_prototype_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.candidate_record()
            record["prototype_authorized"] = True
            path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.PhysicalFrequencyReducerPreconditionsError, "prototype_authorized"):
                validator.validate_physical_frequency_reducer_preconditions(path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "physical_frequency_reducer_preconditions.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def candidate_record(self) -> dict:
        return {
            "schema_version": "physical_frequency_reducer_preconditions_v1",
            "record_id": "synthetic_candidate_physical_frequency_reducer_preconditions_v1",
            "record_status": "candidate_not_authorized",
            "prototype_authorized": False,
            "operational_status": "research_diagnostic",
            "precondition_mode": "physical_frequency_reducer_preconditions_only",
            "source_zone_scope": {
                "source_zone_ids": ["synthetic_source_zone_a"],
                "geometry_versions_required": True,
                "geometry_hashes_required": True,
                "crs_epsg": 2056,
                "vertical_datum": "LN02",
            },
            "overlap_policy": {
                "status": "defined_for_design_review",
                "selected_policy": "mutually_exclusive_partition",
                "allowed_policies": [
                    "mutually_exclusive_partition",
                    "documented_overlap_adjustment",
                ],
                "double_counting_guard_required": True,
                "shared_release_cell_rule": "synthetic zones are non-overlapping",
                "reducer_reports_overlap_adjustment": True,
            },
            "reducer_contract": {
                "status": "defined_for_design_review",
                "deterministic_merge_required": True,
                "order_independent_required": True,
                "chunk_manifest_required": True,
                "output_unit_support_active": False,
                "annual_or_physical_output_supported": False,
                "required_input_records": [
                    "source_frequency_evidence_v1",
                    "block_release_probability_evidence_v1",
                ],
            },
            "uncertainty_propagation": {
                "status": "defined_for_design_review",
                "propagation_method": "nested_monte_carlo_design_review_only",
                "required_components": [
                    "source_event_rate_uncertainty",
                    "block_scenario_probability_uncertainty",
                    "release_cell_probability_uncertainty",
                    "trajectory_aleatory_uncertainty",
                    "terrain_model_form_uncertainty",
                ],
                "output_summary_fields": [
                    "mean_exceedance_rate",
                    "p05_exceedance_rate",
                    "p95_exceedance_rate",
                ],
                "seed_provenance_required": True,
                "calibration_uncertainty_separated_from_validation": True,
            },
            "calibration_dataset_ids": ["frequency_reducer_calibration_v1"],
            "validation_dataset_ids": ["frequency_reducer_holdout_v1"],
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
