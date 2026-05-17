from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_terrain_release_zone_candidates")
staging = load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_terrain_candidate_test")


class TerrainReleaseZoneCandidateMetricsTests(unittest.TestCase):
    def test_committed_tschamut_inputs_produce_deterministic_candidate_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "candidate_products"
            first = planner.build_report(output_root=output_root, output_mode="both")
            first_polygon_text = Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).read_text(encoding="utf-8")
            first_mask_text = Path(first["candidate_release_zone_products"]["outputs"]["mask"]).read_text(encoding="utf-8")
            first_manifest_text = Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8")
            second = planner.build_report(output_root=output_root, output_mode="both")

            self.assertEqual(first, second)

            self.assertEqual(first["schema_version"], "terrain_release_zone_candidate_metrics_v1")
            self.assertEqual(first["candidate_metrics_status"], "ready")
            self.assertEqual(first["candidate_release_zone_set_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_interpretation"], "heuristic_workflow_input_only")
            self.assertEqual(first["candidate_site_id"], "tschamut_public_pilot")
            self.assertEqual(first["candidate_site_name"], "Balfrin / Tschamut AOI")
            self.assertEqual(first["screening_criteria"]["candidate_slope_min_deg"], 30.0)
            self.assertEqual(first["screening_criteria"]["candidate_slope_max_deg"], 55.0)
            self.assertEqual(first["screening_criteria"]["slope_algorithm"], "horn_3x3_cell_center_deg")
            self.assertGreater(first["candidate_summary"]["candidate_cell_count"], 0)
            self.assertGreater(first["candidate_summary"]["candidate_area_m2"], 0)
            self.assertGreater(first["candidate_summary"]["candidate_fraction_of_screenable_cells"], 0.0)
            self.assertGreaterEqual(first["candidate_summary"]["candidate_slope_min_deg"], 30.0)
            self.assertLessEqual(first["candidate_summary"]["candidate_slope_max_deg"], 55.0)
            self.assertEqual(first["candidate_sensitivity_report"]["sensitivity_status"], "ready")
            self.assertEqual(first["candidate_sensitivity_report"]["baseline_variant_id"], "baseline")
            self.assertEqual(first["candidate_sensitivity_report"]["variant_count"], 4)
            self.assertEqual(
                [row["variant_id"] for row in first["candidate_sensitivity_report"]["variant_summaries"]],
                [
                    "baseline",
                    "tight_threshold_band",
                    "wide_threshold_band",
                    "buffered_footprint",
                ],
            )
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_count_range"], {"min": 22793, "max": 36751})
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_area_range_m2"], {"min": 91172.0, "max": 147004.0})
            self.assertEqual(first["candidate_sensitivity_report"]["baseline_candidate_cell_count"], 29499)
            self.assertEqual(first["candidate_sensitivity_report"]["union_candidate_cell_count"], 36751)
            self.assertEqual(first["candidate_sensitivity_report"]["stable_candidate_region"]["cell_count"], 22770)
            self.assertEqual(first["candidate_sensitivity_report"]["unstable_candidate_region"]["cell_count"], 13981)
            self.assertGreater(first["candidate_sensitivity_report"]["stable_candidate_region"]["component_count"], 0)
            self.assertGreater(first["candidate_sensitivity_report"]["unstable_candidate_region"]["component_count"], 0)
            self.assertLess(first["candidate_sensitivity_report"]["stable_candidate_region"]["coverage_fraction_of_union_candidate_cells"], 1.0)
            self.assertGreater(first["candidate_sensitivity_report"]["unstable_candidate_region"]["coverage_fraction_of_union_candidate_cells"], 0.0)
            self.assertEqual(len(first["candidate_sensitivity_report"]["pairwise_overlap_summary"]), 6)
            self.assertTrue(first["candidate_footprint_comparison"]["candidate_excludes_frozen_footprint"])
            self.assertEqual(first["candidate_footprint_comparison"]["candidate_and_frozen_footprint_intersection_cell_count"], 0)
            self.assertIn(
                "candidate cells are heuristic workflow inputs, not validated release zones",
                " ".join(first["claim_boundaries"]["notes"]),
            )
            self.assertIn(
                "stable regions are agreement regions across bounded heuristic settings, not validated release zones",
                " ".join(first["candidate_sensitivity_report"]["claim_boundaries"]["notes"]),
            )
            self.assertEqual(
                [row["category"] for row in first["excluded_area_summary"]],
                [
                    "nodata_or_invalid",
                    "incomplete_neighborhood",
                    "frozen_release_zone_footprint",
                    "slope_below_candidate_band",
                    "slope_above_candidate_band",
                    "candidate_band",
                ],
            )
            self.assertEqual(first["source_zone_inputs"]["source_zone_id"], "tschamut_public_lps_release_bbox")
            self.assertAlmostEqual(first["source_zone_inputs"]["footprint"]["polygon_area_m2_exact"], 327.01513671875, places=6)
            self.assertEqual(first["terrain_inputs"]["terrain_download_status"], "downloaded_public_open_data_to_ignored_raw_cache")
            self.assertEqual(first["candidate_release_zone_products"]["output_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_products"]["output_mode"], "both")
            self.assertEqual(first["candidate_release_zone_products"]["candidate_release_zone_ids"], second["candidate_release_zone_products"]["candidate_release_zone_ids"])
            self.assertGreater(first["candidate_release_zone_products"]["component_count"], 0)
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).exists())

            geojson = json.loads(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).read_text(encoding="utf-8"))
            self.assertEqual(geojson["schema_version"], "terrain_release_zone_candidate_products_v1")
            self.assertEqual(geojson["type"], "FeatureCollection")
            self.assertGreater(len(geojson["features"]), 0)
            first_feature = geojson["features"][0]
            self.assertEqual(first_feature["properties"]["candidate_generation_label"], "heuristic_candidate_generation_only")
            self.assertEqual(first_feature["properties"]["candidate_site_id"], "tschamut_public_pilot")
            self.assertTrue(first_feature["properties"]["candidate_release_zone_id"].startswith("tschamut_public_lps_release_bbox_candidate_"))
            self.assertEqual(first_feature["geometry"]["type"], "MultiPolygon")
            self.assertTrue(first_feature["properties"]["comparison_to_frozen_footprint_excludes_source_zone"])

            manifest = json.loads(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "terrain_release_zone_candidate_products_v1")
            self.assertEqual(manifest["candidate_release_zone_set_status"], "emitted")
            self.assertEqual(manifest["candidate_excludes_frozen_footprint"], True)
            self.assertEqual(manifest["component_count"], first["candidate_release_zone_products"]["component_count"])
            self.assertEqual(manifest["candidate_release_zone_ids"], first["candidate_release_zone_products"]["candidate_release_zone_ids"])
            self.assertEqual(first_polygon_text, Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).read_text(encoding="utf-8"))
            self.assertEqual(first_mask_text, Path(first["candidate_release_zone_products"]["outputs"]["mask"]).read_text(encoding="utf-8"))
            self.assertEqual(first_manifest_text, Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8"))

            text_report = planner.render_text_report(first)
            self.assertEqual(text_report, planner.render_text_report(second))
            self.assertIn("schema_version: terrain_release_zone_candidate_metrics_v1", text_report)
            self.assertIn("candidate_metrics_status: ready", text_report)
            self.assertIn("excluded_area_summary:", text_report)
            self.assertIn("candidate_sensitivity_report:", text_report)
            self.assertIn("frozen_source_zone_footprint:", text_report)
            self.assertIn("candidate_release_zone_products:", text_report)

    def test_missing_public_inputs_are_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            output_root = repo_root / "candidate_products"
            report = planner.build_report(repo_root=repo_root, output_root=output_root)

        self.assertEqual(report["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_release_zone_set_status"], "not_emitted")
        self.assertEqual(report["candidate_release_zone_interpretation"], "not_claimed")
        self.assertGreaterEqual(len(report["blocked_missing_inputs"]), 3)
        self.assertIn("required public inputs are missing", report["blocked_reason"])
        self.assertEqual(report["terrain_summary"], {})
        self.assertEqual(report["candidate_summary"], {})
        self.assertEqual(report["candidate_sensitivity_report"]["sensitivity_status"], "blocked_missing_inputs")
        self.assertEqual(report["excluded_area_summary"], [])
        self.assertEqual(report["candidate_footprint_comparison"]["comparison_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_release_zone_products"]["output_status"], "not_emitted")
        self.assertFalse(output_root.exists())
        self.assertEqual(report["provenance"], {})

    def test_fixture_terrain_package_fields_feed_candidate_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            terrain_crop = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"
            terrain_metadata = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"
            source_zone_metadata = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"

            report = planner.build_report(
                repo_root=repo_root,
                terrain_crop_path=terrain_crop,
                terrain_metadata_path=terrain_metadata,
                source_zone_metadata_path=source_zone_metadata,
                output_root=repo_root / "candidate_products",
            )

        self.assertEqual(report["candidate_metrics_status"], "ready")
        self.assertEqual(report["terrain_preprocessing"]["terrain_preprocessing_status"], "ready")
        self.assertEqual(report["terrain_inputs"]["terrain_preprocessing_status"], "ready")
        self.assertEqual(report["terrain_preprocessing"]["terrain_preprocessing_package"]["source_tile_ids"], ["2793-1180"])
        self.assertEqual(report["screening_criteria"]["terrain_crop_extent_lv95_m"]["xmin"], 2793000.0)
        self.assertEqual(report["screening_criteria"]["terrain_resolution_m"], 2.0)
        self.assertEqual(report["terrain_inputs"]["terrain_preprocessing_package"]["output_roots"]["processed_input_root"], report["terrain_preprocessing"]["output_roots"]["processed_input_root"])

    def _write_site_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
