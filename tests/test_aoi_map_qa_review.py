from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1"
SCRIPT_PATH = ROOT / "scripts" / "generate_aoi_map_qa_review.py"
SPEC = importlib.util.spec_from_file_location("generate_aoi_map_qa_review", SCRIPT_PATH)
assert SPEC is not None
review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(review)

from scripts import package_aoi_hazard_map as packager


class AoiMapQaReviewTests(unittest.TestCase):
    def test_review_surface_surfaces_layers_and_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            output_root = work / "package"
            review_root = work / "review"

            def fake_cog_conversion_ready(input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(f"converted:{input_path.name}".encode("utf-8"))
                return {
                    "status": "cog_conversion_sample_ready",
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "verification": {
                        "status": "ok",
                        "sample_raster_tiled": True,
                        "sample_raster_overviews": True,
                        "sample_raster_cog_layout": True,
                    },
                    "output_exists": True,
                    "output_bytes": output_path.stat().st_size,
                    "blockers": [],
                }

            with unittest.mock.patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=fake_cog_conversion_ready):
                package_report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            report = review.build_review_surface(input_root=output_root, output_root=review_root)

            self.assertEqual(report["status"], "review_ready_with_warnings")
            self.assertTrue(report["layer_presence"]["release_zone"]["present"])
            self.assertTrue(report["layer_presence"]["scenario_metadata"]["present"])
            self.assertEqual(report["layer_presence"]["hazard_layers"]["count"], len(package_report["raster_outputs"]))
            self.assertGreaterEqual(len(report["vector_overlays"]), 2)
            self.assertIn("missing context layers", "\n".join(report["warnings"]))
            self.assertIn("non-operational status", "\n".join(report["warnings"]))
            self.assertEqual(report["diagnostic_hazard_outputs"]["status"], "present")
            self.assertEqual(report["observed_evidence_overlays"]["status"], "blocked_missing_evidence")
            self.assertTrue((review_root / "index.html").exists())
            self.assertTrue((review_root / "aoi_map_qa_review_manifest.json").exists())
            html = (review_root / "index.html").read_text(encoding="utf-8")
            self.assertIn("AOI Map QA Review", html)
            self.assertIn("Diagnostic hazard layers", html)
            self.assertIn("Release and scenario overlays", html)
            self.assertIn("Optional observed evidence", html)
            self.assertIn("Claim boundaries", html)
            self.assertIn("diagnostic review only", html)
            self.assertIn("single openable bundle", html)
            self.assertIn("release zone metadata", html.lower())
            self.assertIn("data-toggle-target", html)
            self.assertEqual(package_report["review_surface_status"], "review_ready_with_warnings")
            self.assertEqual(package_report["review_surface_paths"]["entrypoint"], str(output_root / "index.html"))

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
