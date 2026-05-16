from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest import mock


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
            self.assertEqual(report["spatial_relevance_status"], inspector.BLOCKED)
            self.assertIn("real processed Tschamut context crops are absent", report["blocked_reason"])
            self.assertEqual(report["swisstlm3d_archive_status"], inspector.BLOCKED)
            self.assertFalse(report["context_root_present"])
            self.assertGreater(report["blocked_context_layer_count"], 0)
            self.assertEqual(report["layers_available"], [])
            self.assertEqual(len(report["layers_missing"]), report["context_layer_count"])
            self.assertFalse(report["operational_claims_allowed"])
            self.assertEqual(
                report["selected_extent_or_corridor"]["name"],
                "Tschamut 2014 public release/deposition corridor",
            )
            self.assertTrue(
                any(item["dataset_id"] == "swisstopo_swissimage" for item in report["acquisition_checklist"])
            )
            self.assertTrue(report["source_products"])
            self.assertEqual(report["local_cache_paths"]["context_root"], str(context_root))
            self.assertEqual(report["checksums"]["available_layers"], [])
            self.assertEqual(report["spatial_relevance_indicators"]["available_layer_count"], 0)
            self.assertEqual(
                report["spatial_relevance_indicators"]["classification_summary"]["unresolved"],
                [
                    "forest_or_canopy",
                    "buildings_or_structures",
                    "roads_or_transport",
                    "barriers_or_protection",
                    "water_or_channel",
                    "orthophoto_visual_context",
                ],
            )

    def test_metadata_only_fixture_reports_file_stats_and_layer_classification(self) -> None:
        report = inspector.inspect_context_layers(
            scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
            datasets_registry_path=ROOT / "data/datasets.yaml",
            context_root=FIXTURE,
        )

        self.assertEqual(report["status"], "limiting")
        self.assertEqual(report["classification"], "limiting")
        self.assertEqual(report["context_review_status"], "fixture_reviewed_context")
        self.assertEqual(report["target_scale_context_review_status"], inspector.BLOCKED_REVIEW_STATUS)
        self.assertEqual(report["spatial_relevance_status"], "fixture_reviewed_context")
        self.assertIsNone(report["blocked_reason"])
        self.assertEqual(report["swisstlm3d_archive_status"], inspector.BLOCKED)
        self.assertIn("missing an archive path", report["swisstlm3d_archive_blocked_reason"])
        self.assertTrue(report["context_root_present"])
        self.assertEqual(report["context_layer_count"], 6)
        self.assertEqual(len(report["layers_available"]), 6)
        self.assertEqual(len(report["layers_missing"]), 0)
        self.assertEqual(report["selected_extent_or_corridor"]["extent_lv95_m"]["xmin"], 2696376.0)
        canopy = next(layer for layer in report["expected_context_layers"] if layer["category"] == "forest_or_canopy")
        self.assertEqual(canopy["classification"], "acceptable")
        self.assertEqual(canopy["file_count"], 1)
        self.assertIsNotNone(canopy["combined_sha256"])
        self.assertIn("coordinate_reference_system", canopy["metadata"])
        self.assertTrue(report["checksums"]["available_layers"])
        self.assertTrue(report["crs_or_spatial_reference"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual(report["spatial_relevance_summary"]["acceptable"], ["forest_or_canopy"])
        self.assertEqual(report["spatial_relevance_indicators"]["available_layer_count"], 6)
        self.assertEqual(report["spatial_relevance_indicators"]["missing_layer_count"], 0)
        self.assertTrue(
            report["spatial_relevance_indicators"]["spatial_extent_alignment"]["all_reviewed_layers_share_selected_epsg"]
        )
        self.assertEqual(
            report["spatial_relevance_indicators"]["classification_summary"]["acceptable"],
            ["forest_or_canopy"],
        )
        self.assertEqual(
            report["spatial_relevance_indicators"]["classification_summary"]["limiting"],
            ["buildings_or_structures", "orthophoto_visual_context"],
        )
        self.assertIn("per_layer_metadata_indicators", report["spatial_relevance_indicators"])
        self.assertEqual(report["roads_or_transport_relevance"]["classification"], "unresolved")
        self.assertEqual(report["final_classification"], "limiting")

    @unittest.skipUnless(shutil.which("ogrinfo"), "ogrinfo is unavailable")
    def test_vector_layer_count_on_tiny_geojson_fixture_detects_intersection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roads = root / "roads.geojson"
            roads.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {"kind": "road"},
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": [[0.0, 0.0], [10.0, 10.0]],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            empty = root / "barriers.geojson"
            empty.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {"kind": "barrier"},
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": [[100.0, 100.0], [120.0, 120.0]],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            bbox = {"xmin": -1.0, "ymin": -1.0, "xmax": 11.0, "ymax": 11.0}
            roads_result = inspector.query_vector_layer_count(
                ogrinfo=shutil.which("ogrinfo"),
                datasource_path=str(roads),
                layer_name="roads",
                bbox=bbox,
                category="roads_or_transport",
                member_path="roads.geojson",
            )
            barriers_result = inspector.query_vector_layer_count(
                ogrinfo=shutil.which("ogrinfo"),
                datasource_path=str(empty),
                layer_name="barriers",
                bbox=bbox,
                category="barriers_or_protection",
                member_path="barriers.geojson",
            )

            self.assertEqual(roads_result["status"], "ok")
            self.assertEqual(roads_result["intersecting_feature_count"], 1)
            self.assertEqual(roads_result["nearest_feature_distance_m"], 0.0)
            self.assertEqual(barriers_result["status"], "ok")
            self.assertEqual(barriers_result["intersecting_feature_count"], 0)
            self.assertIsNone(barriers_result["nearest_feature_distance_m"])

    def test_staged_archive_corridor_summary_aggregates_layer_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_root = root / "context"
            archive_dir = context_root / "swisstlm3d"
            archive_dir.mkdir(parents=True)
            archive_path = root / "raw_swisstlm3d.zip"
            archive_path.write_bytes(b"fake archive")
            metadata = {
                "source_product": "swissTLM3D",
                "source_url": "https://example.test/swisstlm3d",
                "local_asset_path": str(archive_path),
                "local_asset_sha256": "abc123",
                "local_asset_bytes": archive_path.stat().st_size,
                "coordinate_reference_system": {"epsg": 2056, "horizontal_name": "CH1903+ / LV95", "vertical_datum": "LN02"},
            }
            (archive_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

            counts = {
                "swissTLM3D_TLM_STRASSE": 22,
                "swissTLM3D_TLM_STRASSENINFO": 16,
                "swissTLM3D_TLM_MAUER": 2,
                "swissTLM3D_TLM_VERBAUUNG": 4,
                "swissTLM3D_TLM_STAUBAUTE": 0,
                "swissTLM3D_TLM_FLIESSGEWAESSER": 24,
                "swissTLM3D_TLM_STEHENDES_GEWAESSER": 0,
                "swissTLM3D_TLM_GEBAEUDE_FOOTPRINT": 0,
                "swissTLM3D_TLM_VERKEHRSBAUTE_LIN": 0,
                "swissTLM3D_TLM_VERKEHRSBAUTE_PLY": 0,
                "swissTLM3D_TLM_VERSORGUNGS_BAUTE_LIN": 0,
                "swissTLM3D_TLM_VERSORGUNGS_BAUTE_PKT": 0,
            }

            def fake_query(**kwargs):
                layer_name = kwargs["layer_name"]
                return {
                    "status": "ok",
                    "category": kwargs["category"],
                    "layer_name": layer_name,
                    "member_path": kwargs["member_path"],
                    "datasource_path": kwargs["archive_path"].as_posix(),
                    "intersecting_feature_count": counts[layer_name],
                    "nearest_feature_distance_m": 0.0 if counts[layer_name] > 0 else None,
                }

            with mock.patch.object(inspector.shutil, "which", return_value="/usr/bin/ogrinfo"), mock.patch.object(
                inspector,
                "query_swisstlm3d_layer_count",
                side_effect=fake_query,
            ):
                report = inspector.inspect_swisstlm3d_corridor_relevance(
                    context_root=context_root,
                    selected_extent_or_corridor={
                        "extent_lv95_m": {
                            "xmin": 2696376.0,
                            "ymin": 1167384.0,
                            "xmax": 2696976.0,
                            "ymax": 1167992.0,
                        }
                    },
                    registry={
                        "swisstopo_swisstlm3d": {
                            "source_url": "https://example.test/swisstlm3d",
                        }
                    },
                )

            self.assertEqual(report["archive_status"], "measured_corridor_relevance")
            self.assertEqual(report["roads_or_transport_relevance"]["classification"], "limiting")
            self.assertEqual(report["roads_or_transport_relevance"]["feature_count"], 38)
            self.assertEqual(report["barriers_or_protection_relevance"]["feature_count"], 6)
            self.assertEqual(report["water_or_channel_relevance"]["feature_count"], 24)
            self.assertEqual(report["constructed_feature_relevance"]["classification"], "unresolved")
            self.assertEqual(report["feature_counts"]["roads_or_transport"]["by_layer"]["swissTLM3D_TLM_STRASSE"], 22)
            self.assertEqual(report["intersecting_feature_counts"]["barriers_or_protection"], 6)
            self.assertEqual(report["queried_layers"][0]["category"], "roads_or_transport")
            self.assertFalse(report["blocked_reason"])

    def test_json_serializable_output_schema_is_stable(self) -> None:
        report = inspector.inspect_context_layers(
            scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
            datasets_registry_path=ROOT / "data/datasets.yaml",
            context_root=FIXTURE,
        )
        payload = json.loads(json.dumps(report))

        self.assertEqual(payload["schema_version"], inspector.SCHEMA_VERSION)
        self.assertIn("acquisition_checklist", payload)
        self.assertCountEqual(
            payload.keys(),
            [
                "acquisition_checklist",
                "adjacent_context_products",
                "barriers_or_protection_relevance",
                "blocked_context_layer_count",
                "blocked_missing_context_layers",
                "blocked_reason",
                "checksums",
                "classification",
                "constructed_feature_relevance",
                "context_layer_count",
                "context_review_status",
                "context_root",
                "context_root_present",
                "crs_or_spatial_reference",
                "evidence",
                "expected_context_layers",
                "feature_counts",
                "final_classification",
                "interpretation_impact",
                "intersecting_feature_counts",
                "layers_available",
                "layers_expected",
                "layers_missing",
                "local_cache_paths",
                "nearest_feature_distances_m",
                "operational_claims_allowed",
                "pilot_id",
                "queried_layers",
                "reviewed_context_count",
                "run_id",
                "schema_version",
                "scope_record_path",
                "selected_extent_or_corridor",
                "roads_or_transport_relevance",
                "source_products",
                "spatial_relevance_indicators",
                "spatial_relevance_status",
                "spatial_relevance_summary",
                "swisstlm3d_archive_blocked_reason",
                "swisstlm3d_archive_status",
                "status",
                "target_scale_context_review_status",
                "target_scale_review",
                "water_or_channel_relevance",
            ],
        )
        self.assertFalse(payload["operational_claims_allowed"])
        self.assertFalse(payload["interpretation_impact"]["operational_claims_allowed"])


if __name__ == "__main__":
    unittest.main()
