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
    def test_selected_target_scope_is_blocked_pending_local_evidence_with_blocked_context_review(self) -> None:
        summary = validator.validate_scope_record(
            ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml"
        )

        self.assertEqual(summary["run_id"], "tschamut_public_scalable_conditional_target_gate_v1")
        self.assertEqual(summary["classification"], "blocked_pending_local_evidence")
        self.assertEqual(summary["target_scale_context_review_status"], "blocked_missing_context_layers")
        self.assertGreater(summary["missing_context_artifact_count"], 0)

    def test_accepts_blocked_scope_with_future_context_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_path = self.write_record(Path(tmp), self.base_record())

            summary = validator.validate_scope_record(record_path)

            self.assertEqual(summary["classification"], "blocked_pending_local_evidence")
            self.assertEqual(summary["context_category_count"], 6)
            self.assertEqual(summary["future_context_download_count"], 3)
            self.assertEqual(summary["target_scale_context_review_status"], "blocked_missing_context_layers")

    def test_rejects_missing_required_context_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["context_inventory"] = [
                item for item in record["context_inventory"] if item["category"] != "barriers_or_protection"
            ]
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "barriers_or_protection"):
                validator.validate_scope_record(record_path)

    def test_rejects_blocked_scope_without_future_actions(self) -> None:
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

    def test_rejects_blocked_context_review_with_reviewed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["target_scale_review"]["reviewed_context_artifact_paths"] = ["context/swissimage.tif"]
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "must not list reviewed context artifacts"):
                validator.validate_scope_record(record_path)

    def test_rejects_acceptable_classification_without_reviewed_target_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self.base_record()
            record["classification"] = "acceptable"
            record["evidence"]["required_future_context_downloads"] = []
            record["context_inventory"][0]["status"] = "available_reviewed"
            record_path = self.write_record(Path(tmp), record)

            with self.assertRaisesRegex(validator.ObstacleScopeError, "reviewed_accepting_omission"):
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
            "classification": "blocked_pending_local_evidence",
            "classification_rationale": "Context layers were not reviewed, so omission is blocked pending local evidence.",
            "input_scope": {
                "changes_physics": False,
                "changes_defaults": False,
                "adds_obstacle_model": False,
                "adds_risk_or_exposure_model": False,
            },
            "target_scale_review": {
                "target_gate_record_path": "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "target_gate_status": "inconclusive",
                "target_package_visual_qa_record_path": "validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml",
                "target_package_visual_qa_status": "blocked",
                "local_context_review_status": "blocked_missing_context_layers",
                "context_artifacts_committed": False,
                "context_downloads_or_crops_present_in_checkout": False,
                "reviewed_context_artifact_paths": [],
                "missing_context_artifact_paths": ["data/processed/swisstopo/tschamut_public_pilot/context/swissimage/"],
                "interpretation": "No local context layers are reviewed for this unit-test fixture.",
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
                "summary": "Omission is blocked pending local evidence for interpretation.",
                "required_before_interpretation": "Review public context layers before scale-up.",
                "do_not_tune_to_absorb_omission": ["restitution", "roughness"],
            },
            "evidence": {
                "reviewed_documents": ["docs/swisstopo_data_strategy.md"],
                "local_artifact_probe": {
                    "context_root": "data/processed/swisstopo/tschamut_public_pilot/context",
                    "context_root_present": False,
                    "raw_context_products_present": False,
                    "probe_date": "2026-05-09",
                },
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
