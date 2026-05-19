from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_aoi_map_qa_review.py"
SPEC = importlib.util.spec_from_file_location("generate_aoi_map_qa_review", SCRIPT_PATH)
assert SPEC is not None
review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(review)


class AoiMapQaReviewTests(unittest.TestCase):
    def test_review_surface_surfaces_layers_and_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            input_root = work / "aoi_case"
            input_root.mkdir(parents=True, exist_ok=True)
            source_zone = work / "fixtures" / "source_zone.yaml"
            scenario_table = work / "fixtures" / "scenario_table.csv"
            source_zone.parent.mkdir(parents=True, exist_ok=True)
            source_zone.write_text("source_zone_id: source_a\n", encoding="utf-8")
            scenario_table.write_text("scenario_id,weight\ns1,1.0\n", encoding="utf-8")

            hazard_manifest_path = input_root / "case_manifest.json"
            map_manifest_path = input_root / "case_map_package_manifest.json"
            pilot_manifest_path = input_root / "case_pilot_gis_package_manifest.json"
            hazard_manifest = {
                "schema_version": "run_manifest_v1",
                "cellwise_layers": [
                    {
                        "layer_name": "reach_probability",
                        "format": "esri_ascii_grid",
                        "grid_path": str(input_root / "reach_probability.asc"),
                    },
                    {
                        "layer_name": "weighted_reach_probability",
                        "format": "geotiff",
                        "grid_path": str(input_root / "weighted_reach_probability.tif"),
                    },
                ],
            }
            map_manifest = {
                "schema_version": "map_package_manifest_v1",
                "map_product_id": "aoi_case",
                "map_product_version": "v1",
                "probability_mode": "sampling_weighted_conditional",
                "normalization_scope": "conditioned_on_filter",
                "source_zone_id": "source_zone_a",
                "source_zone_metadata_path": str(source_zone),
                "scenario_table_path": str(scenario_table),
                "hazard_manifest_paths": [str(hazard_manifest_path)],
                "raster_outputs": [
                    self.artifact(input_root / "reach_probability.tif", "geotiff", "reach_probability", cloud_optimized=False),
                    self.artifact(input_root / "weighted_reach_probability.tif", "geotiff", "weighted_reach_probability", cloud_optimized=False, weighted=True),
                ],
                "limitations": ["Research diagnostic only; not operational."],
                "operational_status": "research_diagnostic",
            }
            pilot_manifest = {
                "schema_version": "pilot_gis_package_manifest_v1",
                "package_version": "pilot_gis_package_v1",
                "case_id": "aoi_case",
                "terrain": {
                    "path": str(input_root / "terrain.asc"),
                    "metadata_path": str(input_root / "terrain_metadata.yaml"),
                    "epsg": 2056,
                    "vertical_datum": "LN02",
                },
                "terrain_metadata": {
                    "path": str(input_root / "terrain_metadata.yaml"),
                    "format": "yaml",
                },
                "hazard_manifest_paths": [str(hazard_manifest_path)],
                "raster_outputs": [
                    self.artifact(input_root / "reach_probability.tif", "geotiff", "reach_probability", cloud_optimized=False),
                    self.artifact(input_root / "weighted_reach_probability.tif", "geotiff", "weighted_reach_probability", cloud_optimized=False, weighted=True),
                ],
                "source_zone_context": [],
                "visual_qa": {
                    "status": "inconclusive",
                    "note": "manual QA not run",
                    "reviewed_artifacts": [],
                    "acceptance_scope": "local diagnostic GIS/QGIS review only",
                    "accepted_for_operational_use": False,
                },
                "operational_status": "research_diagnostic",
                "raster_contract": {
                    "geotiff_required": True,
                    "csv_ascii_parity_required": True,
                    "cloud_optimized": False,
                    "qgis_project_included": False,
                    "geopackage_included": False,
                },
                "probability_claim_boundary": {
                    "annualized": False,
                    "current_allowed_product_labels": [
                        "unweighted_diagnostic",
                        "sampling_weighted_conditional",
                        "conditional_intensity_exceedance",
                    ],
                    "future_unsupported_product_labels": [
                        "physical_probability",
                        "annual_intensity_frequency",
                        "return_period",
                        "risk_map",
                        "operational_hazard_map",
                    ],
                },
            }
            hazard_manifest_path.write_text(json.dumps(hazard_manifest, indent=2, sort_keys=True), encoding="utf-8")
            map_manifest_path.write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")
            pilot_manifest_path.write_text(json.dumps(pilot_manifest, indent=2, sort_keys=True), encoding="utf-8")

            report = review.build_review_surface(input_root=input_root, output_root=work / "review")

            self.assertEqual(report["status"], "review_ready_with_warnings")
            self.assertTrue(report["layer_presence"]["terrain"]["present"])
            self.assertTrue(report["layer_presence"]["release_zone"]["present"])
            self.assertTrue(report["layer_presence"]["scenario_metadata"]["present"])
            self.assertEqual(report["layer_presence"]["hazard_layers"]["count"], 2)
            self.assertEqual(report["layer_presence"]["context_layers"]["count"], 0)
            self.assertIn("missing context layers", "\n".join(report["warnings"]))
            self.assertIn("COG-blocked rasters", "\n".join(report["warnings"]))
            self.assertIn("fixture-backed inputs", "\n".join(report["warnings"]))
            self.assertIn("conditional-only weights", "\n".join(report["warnings"]))
            self.assertIn("non-operational status", "\n".join(report["warnings"]))
            self.assertTrue((work / "review" / "index.html").exists())
            self.assertTrue((work / "review" / "aoi_map_qa_review_manifest.json").exists())
            html = (work / "review" / "index.html").read_text(encoding="utf-8")
            self.assertIn("AOI Map QA Review", html)
            self.assertIn("release zone metadata", html.lower())

    def test_blocked_missing_map_package_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            input_root = work / "missing_map"
            input_root.mkdir(parents=True, exist_ok=True)
            pilot_manifest_path = input_root / "case_pilot_gis_package_manifest.json"
            pilot_manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "pilot_gis_package_manifest_v1",
                        "package_version": "pilot_gis_package_v1",
                        "case_id": "missing_map",
                        "terrain": {"path": str(input_root / "terrain.asc"), "metadata_path": str(input_root / "terrain_metadata.yaml")},
                        "terrain_metadata": {"path": str(input_root / "terrain_metadata.yaml"), "format": "yaml"},
                        "raster_outputs": [],
                        "source_zone_context": [],
                        "visual_qa": {
                            "status": "inconclusive",
                            "note": "manual QA not run",
                            "reviewed_artifacts": [],
                            "acceptance_scope": "local diagnostic GIS/QGIS review only",
                            "accepted_for_operational_use": False,
                        },
                        "operational_status": "research_diagnostic",
                        "raster_contract": {
                            "geotiff_required": True,
                            "csv_ascii_parity_required": True,
                            "cloud_optimized": False,
                            "qgis_project_included": False,
                            "geopackage_included": False,
                        },
                        "probability_claim_boundary": {
                            "annualized": False,
                            "current_allowed_product_labels": [
                                "unweighted_diagnostic",
                                "sampling_weighted_conditional",
                                "conditional_intensity_exceedance",
                            ],
                            "future_unsupported_product_labels": [
                                "physical_probability",
                                "annual_intensity_frequency",
                                "return_period",
                                "risk_map",
                                "operational_hazard_map",
                            ],
                        },
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            report = review.build_review_surface(input_root=input_root, output_root=work / "review")

            self.assertEqual(report["status"], "blocked_missing_map_package")
            self.assertIn("missing map package manifest", "\n".join(report["warnings"]))
            self.assertTrue((work / "review" / "index.html").exists())

    def artifact(
        self,
        path: Path,
        format_name: str,
        layer_name: str,
        *,
        cloud_optimized: bool,
        weighted: bool = False,
    ) -> dict[str, object]:
        return {
            "path": str(path),
            "format": format_name,
            "layer_name": layer_name,
            "cloud_optimized": cloud_optimized,
            "weighted": weighted,
            "annualized": False,
            "is_annualized": False,
            "kind": "hazard_layer",
            "sha256": "0" * 64,
            "total_bytes": 1,
        }


if __name__ == "__main__":
    unittest.main()
