from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_pilot_gis_visual_qa.py"
SPEC = importlib.util.spec_from_file_location("validate_pilot_gis_visual_qa", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PilotGisVisualQaTests(unittest.TestCase):
    def test_accepts_inconclusive_record_with_explicit_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_path = self.write_record(Path(tmp), self.base_record())

            summary = validator.validate_visual_qa_record(record_path)

            self.assertEqual(summary["manual_qgis_visual_qa_status"], "inconclusive")
            self.assertEqual(summary["overall_acceptance"], "inconclusive")
            self.assertFalse(summary["qgis_available"])
            self.assertEqual(summary["required_check_count"], 7)

    def test_rejects_overall_pass_without_qgis_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["status"]["manual_qgis_visual_qa_status"] = "pass"
            record["status"]["overall_acceptance"] = "pass"
            for check in record["checks"]:
                check["status"] = "pass"
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.VisualQaValidationError, "qgis_available true"):
                validator.validate_visual_qa_record(record_path)

    def test_rejects_missing_required_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["checks"] = [
                check for check in record["checks"] if check["id"] != "source_zone_overlay"
            ]
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.VisualQaValidationError, "source_zone_overlay"):
                validator.validate_visual_qa_record(record_path)

    def test_rejects_selected_record_with_manual_not_run_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["status"]["manual_qgis_visual_qa_status"] = "not-run"
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.VisualQaValidationError, "must be pass, no-go, or inconclusive"):
                validator.validate_visual_qa_record(record_path)

    def test_rejects_unqualified_risk_map_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["checks"][0]["finding"] = "This is a risk map ready for use."
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.VisualQaValidationError, "misleading current-product claim"):
                validator.validate_visual_qa_record(record_path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "visual_qa.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        return {
            "schema_version": "pilot_gis_visual_qa_record_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "package_manifest_path": "hazard/results/example_package_manifest.json",
            "review_environment": {
                "reviewer": "unit-test",
                "review_date": "2026-05-08",
                "qgis_available": False,
                "qgis_version": None,
                "execution_context": "non-GUI test",
            },
            "status": {
                "automated_package_qa_status": "pass",
                "manual_qgis_visual_qa_status": "inconclusive",
                "overall_acceptance": "inconclusive",
                "accepted_for_operational_use": False,
            },
            "checks": [
                self.check("project_crs_epsg_2056", "pass"),
                self.check("vertical_datum_ln02", "pass"),
                self.check("raster_grid_alignment", "inconclusive"),
                self.check("nodata_vs_valid_zero_styling", "inconclusive"),
                self.check("source_zone_overlay", "inconclusive"),
                self.check("layer_labels_conditional", "pass"),
                self.check("unsupported_claim_boundaries", "pass"),
            ],
            "evidence": {
                "automated_validator_command": "validate package",
                "automated_validator_result": "pass",
                "reviewed_artifacts": ["package_manifest.json"],
                "screenshots": [],
            },
            "blockers": ["QGIS was unavailable in this test environment."],
            "claim_boundary": {
                "operational_status": "research_diagnostic",
                "annualized": False,
                "physical_probability": False,
                "risk_or_exposure": False,
                "current_allowed_product_labels": [
                    "unweighted_diagnostic",
                    "sampling_weighted_conditional",
                    "conditional_intensity_exceedance",
                ],
                "deferred_or_unsupported_labels": [
                    "physical_probability",
                    "annual_intensity_frequency",
                    "return_period",
                    "risk_map",
                    "operational_hazard_map",
                ],
            },
        }

    def check(self, check_id: str, status: str) -> dict:
        return {
            "id": check_id,
            "status": status,
            "finding": f"{check_id} classified as {status}.",
            "evidence": ["unit-test evidence"],
        }


if __name__ == "__main__":
    unittest.main()
