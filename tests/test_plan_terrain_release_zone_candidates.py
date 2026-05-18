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
            self.assertEqual(first["candidate_sensitivity_report"]["variant_count"], 6)
            self.assertEqual(
                [row["variant_id"] for row in first["candidate_sensitivity_report"]["variant_summaries"]],
                [
                    "baseline",
                    "tight_threshold_band",
                    "wide_threshold_band",
                    "smoothed_3x3_mean",
                    "coarsened_2x2_mean_reexpanded",
                    "trimmed_aoi_boundary_1_cell",
                ],
            )
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_count_range"], {"min": 22793, "max": 36751})
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_area_range_m2"], {"min": 91172.0, "max": 147004.0})
            self.assertEqual(first["candidate_sensitivity_report"]["baseline_candidate_cell_count"], 29499)
            self.assertEqual(first["candidate_sensitivity_report"]["union_candidate_cell_count"], 37787)
            self.assertEqual(first["candidate_sensitivity_report"]["stable_candidate_region"]["cell_count"], 21279)
            self.assertEqual(first["candidate_sensitivity_report"]["unstable_candidate_region"]["region_class"], "unstable_across_bounded_heuristics")
            self.assertEqual(first["candidate_sensitivity_report"]["unstable_candidate_region"]["cell_count"], 16508)
            self.assertEqual(
                first["candidate_sensitivity_report"]["heuristic_sensitive_candidate_region"]["region_class"],
                "heuristic_sensitive_across_bounded_heuristics",
            )
            self.assertEqual(first["candidate_sensitivity_report"]["heuristic_sensitive_candidate_region"]["cell_count"], 16508)
            self.assertGreater(first["candidate_sensitivity_report"]["stable_candidate_region"]["component_count"], 0)
            self.assertGreater(first["candidate_sensitivity_report"]["unstable_candidate_region"]["component_count"], 0)
            self.assertLess(first["candidate_sensitivity_report"]["stable_candidate_region"]["coverage_fraction_of_union_candidate_cells"], 1.0)
            self.assertGreater(first["candidate_sensitivity_report"]["unstable_candidate_region"]["coverage_fraction_of_union_candidate_cells"], 0.0)
            self.assertEqual(len(first["candidate_sensitivity_report"]["pairwise_overlap_summary"]), 15)
            self.assertEqual(
                [row["sensitivity_dimension"] for row in first["candidate_sensitivity_report"]["candidate_sensitivity_matrix"]],
                ["slope_threshold", "smoothing", "terrain_resolution", "aoi_boundary"],
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_sensitivity_matrix"][0]["variant_ids"],
                ["tight_threshold_band", "wide_threshold_band"],
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_sensitivity_matrix"][1]["variant_ids"],
                ["smoothed_3x3_mean"],
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_sensitivity_matrix"][2]["variant_ids"],
                ["coarsened_2x2_mean_reexpanded"],
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_sensitivity_matrix"][3]["variant_ids"],
                ["trimmed_aoi_boundary_1_cell"],
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_persistence_metrics"]["stable_candidate_cell_count"],
                21279,
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_persistence_metrics"]["heuristic_sensitive_candidate_cell_count"],
                16508,
            )
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
            self.assertIn(
                "heuristic-sensitive regions are candidate-persistence summaries, not validated release zones",
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
            self.assertEqual(first["source_zone_inputs"]["release_zone_provenance_intake"]["release_zone_provenance_state"], "workflow_generated")
            self.assertTrue(first["source_zone_inputs"]["release_zone_provenance_intake"]["workflow_generated"])
            self.assertFalse(first["source_zone_inputs"]["release_zone_provenance_intake"]["field_supported"])
            self.assertEqual(first["terrain_inputs"]["terrain_download_status"], "downloaded_public_open_data_to_ignored_raw_cache")
            self.assertEqual(first["candidate_release_zone_products"]["output_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_products"]["output_mode"], "both")
            self.assertEqual(first["candidate_release_zone_products"]["candidate_release_zone_ids"], second["candidate_release_zone_products"]["candidate_release_zone_ids"])
            self.assertGreater(first["candidate_release_zone_products"]["component_count"], 0)
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertEqual(first["candidate_review_package"]["review_package_status"], "emitted")
            self.assertEqual(first["candidate_review_package"]["review_decision_options"], ["accepted", "rejected", "needs_field_review"])
            self.assertEqual(
                [row["provenance_label"] for row in first["candidate_review_package"]["provenance_label_legend"]],
                ["workflow_generated", "field_supported", "mixed_provenance", "blocked_missing_provenance"],
            )
            self.assertGreater(first["candidate_review_package"]["review_summary"]["candidate_count"], 0)
            self.assertEqual(first["candidate_review_package"]["review_summary"]["default_review_decision"], "needs_field_review")
            self.assertEqual(first["candidate_review_package"]["review_summary"]["review_decision_counts"]["needs_field_review"], first["candidate_review_package"]["review_summary"]["candidate_count"])
            self.assertEqual(first["candidate_review_package"]["review_summary"]["provenance_label_counts"]["workflow_generated"], first["candidate_review_package"]["review_summary"]["candidate_count"])
            self.assertTrue(Path(first["candidate_review_package"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_review_package"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_review_package"]["outputs"]["csv"]).exists())
            self.assertTrue(Path(first["candidate_review_package"]["outputs"]["manifest"]).exists())

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
            self.assertEqual(first_feature["properties"]["review_decision"], "needs_field_review")
            self.assertFalse(first_feature["properties"]["accepted"])
            self.assertFalse(first_feature["properties"]["rejected"])
            self.assertTrue(first_feature["properties"]["needs_field_review"])
            self.assertEqual(first_feature["properties"]["provenance_label"], "workflow_generated")
            self.assertEqual(first_feature["properties"]["candidate_sensitivity_label"], "heuristic_sensitive_across_bounded_heuristics")
            self.assertEqual(first_feature["properties"]["release_cell_count"], len(first_feature["properties"]["release_cell_ids"]))
            self.assertTrue(first_feature["properties"]["release_cell_ids"][0].startswith(first_feature["properties"]["candidate_release_zone_id"]))

            review_geojson = json.loads(Path(first["candidate_review_package"]["outputs"]["polygon"]).read_text(encoding="utf-8"))
            self.assertEqual(review_geojson["schema_version"], "terrain_release_zone_candidate_review_package_v1")
            self.assertEqual(review_geojson["review_decision_options"], ["accepted", "rejected", "needs_field_review"])
            self.assertEqual(review_geojson["provenance_label_legend"][0]["provenance_label"], "workflow_generated")
            self.assertEqual(review_geojson["features"][0]["properties"]["review_decision"], "needs_field_review")
            self.assertEqual(review_geojson["features"][0]["properties"]["candidate_sensitivity_label"], "heuristic_sensitive_across_bounded_heuristics")

            manifest = json.loads(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "terrain_release_zone_candidate_products_v1")
            self.assertEqual(manifest["candidate_release_zone_set_status"], "emitted")
            self.assertEqual(manifest["candidate_excludes_frozen_footprint"], True)
            self.assertEqual(manifest["component_count"], first["candidate_release_zone_products"]["component_count"])
            self.assertEqual(manifest["candidate_release_zone_ids"], first["candidate_release_zone_products"]["candidate_release_zone_ids"])
            self.assertEqual(first_polygon_text, Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).read_text(encoding="utf-8"))
            self.assertEqual(first_mask_text, Path(first["candidate_release_zone_products"]["outputs"]["mask"]).read_text(encoding="utf-8"))
            self.assertEqual(first_manifest_text, Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8"))

            review_manifest = json.loads(Path(first["candidate_review_package"]["outputs"]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(review_manifest["schema_version"], "terrain_release_zone_candidate_review_package_v1")
            self.assertEqual(review_manifest["review_package_status"], "emitted")
            self.assertEqual(review_manifest["review_summary"]["review_decision_counts"]["needs_field_review"], review_manifest["review_summary"]["candidate_count"])
            self.assertEqual(review_manifest["review_summary"]["provenance_label_counts"]["workflow_generated"], review_manifest["review_summary"]["candidate_count"])
            self.assertEqual(review_manifest["candidate_review_rows"][0]["review_decision"], "needs_field_review")

            text_report = planner.render_text_report(first)
            self.assertEqual(text_report, planner.render_text_report(second))
            self.assertIn("schema_version: terrain_release_zone_candidate_metrics_v1", text_report)
            self.assertIn("candidate_metrics_status: ready", text_report)
            self.assertIn("excluded_area_summary:", text_report)
            self.assertIn("candidate_sensitivity_report:", text_report)
            self.assertIn("frozen_source_zone_footprint:", text_report)
            self.assertIn("candidate_release_zone_products:", text_report)
            self.assertIn("candidate_review_package:", text_report)

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
