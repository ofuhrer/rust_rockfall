from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "inspect_tschamut_public_context_layers.py"
SPEC = importlib.util.spec_from_file_location("inspect_tschamut_public_context_layers", SCRIPT_PATH)
assert SPEC is not None
inspector = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = inspector
SPEC.loader.exec_module(inspector)

FIXTURE = ROOT / "tests" / "fixtures" / "tschamut_context_layers" / "available"


class TschamutPublicContextLayerInspectionTests(unittest.TestCase):
    def test_missing_context_root_returns_blocked_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            context_root = Path(tmp) / "context"
            report = inspector.inspect_context_layers(
                scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                datasets_registry_path=ROOT / "data/datasets.yaml",
                context_root=context_root,
        )

        self.assertEqual(report["status"], inspector.BLOCKED)
        self.assertEqual(report["classification"], inspector.BLOCKED)
        self.assertEqual(report["context_review_status"], inspector.BLOCKED_REVIEW_STATUS)
        self.assertEqual(report["target_scale_context_review_status"], inspector.BLOCKED_REVIEW_STATUS)
        self.assertFalse(report["context_root_present"])
        self.assertGreater(report["blocked_context_layer_count"], 0)
        self.assertEqual(report["layers_available"], [])
        self.assertEqual(len(report["layers_missing"]), report["context_layer_count"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertTrue(
            any(item["dataset_id"] == "swisstopo_swissimage" for item in report["acquisition_checklist"])
        )
        self.assertTrue(report["source_products"])
        self.assertEqual(report["local_cache_paths"]["context_root"], str(context_root))
        self.assertEqual(report["checksums"]["available_layers"], [])

    def test_metadata_only_fixture_reports_file_stats_and_layer_classification(self) -> None:
        report = inspector.inspect_context_layers(
            scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
            datasets_registry_path=ROOT / "data/datasets.yaml",
            context_root=FIXTURE,
        )

        self.assertEqual(report["status"], "limiting")
        self.assertEqual(report["classification"], "limiting")
        self.assertEqual(report["context_review_status"], inspector.BLOCKED_REVIEW_STATUS)
        self.assertTrue(report["context_root_present"])
        self.assertEqual(report["context_layer_count"], 6)
        self.assertEqual(len(report["layers_available"]), 6)
        self.assertEqual(len(report["layers_missing"]), 0)
        canopy = next(layer for layer in report["expected_context_layers"] if layer["category"] == "forest_or_canopy")
        self.assertEqual(canopy["classification"], "acceptable")
        self.assertEqual(canopy["file_count"], 1)
        self.assertIsNotNone(canopy["combined_sha256"])
        self.assertIn("coordinate_reference_system", canopy["metadata"])
        self.assertTrue(report["checksums"]["available_layers"])
        self.assertTrue(report["crs_or_spatial_reference"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual(report["spatial_relevance_summary"]["acceptable"], ["forest_or_canopy"])

    def test_json_serializable_output_schema_is_stable(self) -> None:
        report = inspector.inspect_context_layers(
            scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
            datasets_registry_path=ROOT / "data/datasets.yaml",
            context_root=FIXTURE,
        )
        payload = json.loads(json.dumps(report))

        self.assertEqual(payload["schema_version"], inspector.SCHEMA_VERSION)
        self.assertIn("acquisition_checklist", payload)
        self.assertEqual(
            sorted(payload.keys()),
            [
                "acquisition_checklist",
                "adjacent_context_products",
                "blocked_context_layer_count",
                "blocked_missing_context_layers",
                "checksums",
                "classification",
                "context_layer_count",
                "context_review_status",
                "context_root",
                "context_root_present",
                "crs_or_spatial_reference",
                "evidence",
                "expected_context_layers",
                "interpretation_impact",
                "layers_available",
                "layers_expected",
                "layers_missing",
                "local_cache_paths",
                "operational_claims_allowed",
                "pilot_id",
                "reviewed_context_count",
                "run_id",
                "schema_version",
                "scope_record_path",
                "source_products",
                "spatial_relevance_summary",
                "status",
                "target_scale_context_review_status",
                "target_scale_review",
            ],
        )
        self.assertFalse(payload["operational_claims_allowed"])
        self.assertFalse(payload["interpretation_impact"]["operational_claims_allowed"])


if __name__ == "__main__":
    unittest.main()
