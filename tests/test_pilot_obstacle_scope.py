from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_pilot_obstacle_scope.py"
SPEC = importlib.util.spec_from_file_location("validate_pilot_obstacle_scope", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PilotObstacleScopeTests(unittest.TestCase):
    def test_accepts_limiting_scope_with_future_context_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_path = self.write_record(Path(tmp), self.base_record())

            summary = validator.validate_scope_record(record_path)

            self.assertEqual(summary["classification"], "limiting")
            self.assertEqual(summary["context_category_count"], 6)
            self.assertEqual(summary["future_context_download_count"], 3)

    def test_rejects_missing_required_context_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["context_inventory"] = [
                item for item in record["context_inventory"] if item["category"] != "barriers_or_protection"
            ]
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "barriers_or_protection"):
                validator.validate_scope_record(record_path)

    def test_rejects_limiting_scope_without_future_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["evidence"]["required_future_context_downloads"] = []
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "future context"):
                validator.validate_scope_record(record_path)

    def test_rejects_claimed_obstacle_physics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["input_scope"]["adds_obstacle_model"] = True
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "adds_obstacle_model"):
                validator.validate_scope_record(record_path)

    def test_rejects_unqualified_risk_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["classification_rationale"] = "This is a risk map for decisions."
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "misleading current-product claim"):
                validator.validate_scope_record(record_path)

    def write_record(self, work: Path, record: dict) -> Path:
        path = work / "obstacle_scope.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        return path

    def base_record(self) -> dict:
        return {
            "schema_version": "pilot_obstacle_scope_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "classification": "limiting",
            "classification_rationale": "Context layers were not reviewed, so omission is limiting.",
            "input_scope": {
                "changes_physics": False,
                "changes_defaults": False,
                "adds_obstacle_model": False,
                "adds_risk_or_exposure_model": False,
            },
            "context_inventory": [
                self.context("forest_or_canopy", "swisstopo_swisssurface3d_raster"),
                self.context("buildings_or_structures", "swisstopo_swissbuildings3d"),
                self.context("roads_or_transport", "swisstopo_swisstlm3d"),
                self.context("barriers_or_protection", "swisstopo_swisstlm3d"),
                self.context("water_or_channel", "swisstopo_swisstlm3d"),
                self.context("orthophoto_visual_context", "swisstopo_swissimage"),
            ],
            "omission_interpretation": {
                "summary": "Omission is limiting for interpretation.",
                "required_before_interpretation": "Review public context layers before scale-up.",
                "do_not_tune_to_absorb_omission": ["restitution", "roughness"],
            },
            "evidence": {
                "reviewed_documents": ["docs/swisstopo_data_strategy.md"],
                "required_future_context_downloads": [
                    "swisstopo_swissimage",
                    "swisstopo_swisstlm3d",
                    "swisstopo_swisssurface3d_raster",
                ],
            },
            "claim_boundary": {
                "operational_status": "research_diagnostic",
                "annualized": False,
                "physical_probability": False,
                "risk_or_exposure": False,
                "obstacle_physics_implemented": False,
            },
        }

    def context(self, category: str, dataset_id: str) -> dict:
        return {
            "category": category,
            "dataset_id": dataset_id,
            "status": "documented_not_downloaded",
            "role": f"{category}_context",
            "interpretation": f"{category} was not reviewed for this fixture.",
        }


if __name__ == "__main__":
    unittest.main()
