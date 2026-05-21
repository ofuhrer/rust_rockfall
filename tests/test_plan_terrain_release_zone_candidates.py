from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
RESTAGE_SCRIPT_PATH = ROOT / "scripts" / "stage_management_aoi_restaged_terrain.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_terrain_release_zone_candidates")
staging = load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_terrain_candidate_test")
restager = load_module(RESTAGE_SCRIPT_PATH, "stage_management_aoi_restaged_terrain_for_candidate_tests")


def square_feature(
    candidate_id: str,
    xmin: float,
    ymin: float,
    size: float,
    *,
    provenance_label: str = "workflow_generated",
    review_decision: str = "needs_field_review",
    accepted: bool | None = None,
    rejected: bool | None = None,
    needs_field_review: bool | None = None,
) -> dict[str, object]:
    accepted = review_decision == "accepted" if accepted is None else accepted
    rejected = review_decision == "rejected" if rejected is None else rejected
    needs_field_review = review_decision == "needs_field_review" if needs_field_review is None else needs_field_review
    return {
        "type": "Feature",
        "id": candidate_id,
        "properties": {
            "candidate_release_zone_id": candidate_id,
            "review_decision": review_decision,
            "accepted": accepted,
            "rejected": rejected,
            "needs_field_review": needs_field_review,
            "candidate_generation_label": "heuristic_candidate_generation_only",
            "candidate_sensitivity_label": "heuristic_sensitive_across_bounded_heuristics",
            "candidate_stability_label": "sensitive",
            "candidate_stability_class": "sensitive",
            "candidate_stability_rank": 1,
            "candidate_stability_score": 0.75,
            "candidate_minimum_retention_fraction": 0.75,
            "candidate_mean_retention_fraction": 0.8,
            "candidate_variant_presence_fraction": 0.9,
            "release_cell_count": 1,
            "release_cell_ids": [f"{candidate_id}__cell_000"],
            "provenance_label": provenance_label,
            "component_cell_count": 1,
            "component_area_m2": 4.0,
            "component_slope_min_deg": 31.0,
            "component_slope_max_deg": 31.0,
            "component_slope_mean_deg": 31.0,
            "component_slope_median_deg": 31.0,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [xmin, ymin],
                    [xmin + size, ymin],
                    [xmin + size, ymin + size],
                    [xmin, ymin + size],
                    [xmin, ymin],
                ]
            ],
        },
    }


class TerrainReleaseZoneCandidateMetricsTests(unittest.TestCase):
    def test_committed_tschamut_inputs_produce_deterministic_candidate_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "candidate_products"
            first = planner.build_report(output_root=output_root, output_mode="both")
            first_polygon_text = Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).read_text(encoding="utf-8")
            first_mask_text = Path(first["candidate_release_zone_products"]["outputs"]["mask"]).read_text(encoding="utf-8")
            first_manifest_text = Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).read_text(encoding="utf-8")
            second = planner.build_report(output_root=output_root, output_mode="both")

            first_sanitized = copy.deepcopy(first)
            second_sanitized = copy.deepcopy(second)
            first_sanitized["candidate_sweep_measurements"]["runtime_seconds"] = 0.0
            second_sanitized["candidate_sweep_measurements"]["runtime_seconds"] = 0.0
            self.assertEqual(first_sanitized, second_sanitized)

            self.assertEqual(first["schema_version"], "terrain_release_zone_candidate_metrics_v1")
            self.assertEqual(first["candidate_metrics_status"], "ready")
            self.assertEqual(first["candidate_release_zone_set_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_interpretation"], "heuristic_workflow_input_only")
            self.assertEqual(first["candidate_site_id"], "tschamut_public_pilot")
            self.assertEqual(first["candidate_site_name"], "Balfrin / Tschamut AOI")
            self.assertEqual(first["screening_criteria"]["candidate_screening_mode"], "expanded_steep_terrain_source_zone_v1")
            self.assertEqual(first["screening_criteria"]["candidate_slope_min_deg"], 45.0)
            self.assertEqual(first["screening_criteria"]["candidate_slope_max_deg"], 75.0)
            self.assertEqual(first["screening_criteria"]["slope_algorithm"], "horn_3x3_cell_center_deg")
            self.assertGreater(first["candidate_summary"]["candidate_cell_count"], 0)
            self.assertGreater(first["candidate_summary"]["candidate_area_m2"], 0)
            self.assertGreater(first["candidate_summary"]["candidate_fraction_of_screenable_cells"], 0.0)
            self.assertEqual(first["candidate_summary"]["workflow_generated_candidate_cell_count"], 2958)
            self.assertEqual(first["candidate_summary"]["reviewed_candidate_cell_count"], 461)
            self.assertEqual(first["candidate_summary"]["review_only_terrain_cell_count"], 0)
            self.assertEqual(
                first["candidate_summary"]["candidate_generation_class_counts"],
                {"workflow_generated": 2958, "reviewed_candidate": 461, "review_only": 0},
            )
            self.assertGreaterEqual(first["candidate_summary"]["candidate_slope_min_deg"], 35.0)
            self.assertLessEqual(first["candidate_summary"]["candidate_slope_max_deg"], 75.0)
            self.assertGreaterEqual(first["candidate_summary"]["candidate_smoothed_slope_min_deg"], 45.0)
            self.assertLessEqual(first["candidate_summary"]["candidate_smoothed_slope_max_deg"], 75.0)
            self.assertEqual(first["candidate_release_zone_separation_summary"]["separation_status"], "review_ready")
            self.assertEqual(first["candidate_release_zone_separation_summary"]["deterministic_candidate_count"], 65)
            self.assertEqual(first["candidate_release_zone_separation_summary"]["accepted_release_zone_count"], 0)
            self.assertEqual(first["candidate_release_zone_separation_summary"]["accepted_release_zone_ids"], [])
            self.assertEqual(first["candidate_sweep_measurements"]["output_file_count"], 7)
            self.assertGreater(first["candidate_sweep_measurements"]["runtime_seconds"], 0.0)
            self.assertGreater(first["candidate_sweep_measurements"]["output_total_bytes"], 0)
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
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_count_range"], {"min": 3077, "max": 3419})
            self.assertEqual(first["candidate_sensitivity_report"]["candidate_area_range_m2"], {"min": 12308.0, "max": 13676.0})
            self.assertEqual(first["candidate_sensitivity_report"]["baseline_candidate_cell_count"], 3419)
            self.assertEqual(first["candidate_sensitivity_report"]["union_candidate_cell_count"], 3579)
            self.assertEqual(first["candidate_sensitivity_report"]["stable_candidate_region"]["cell_count"], 2828)
            self.assertEqual(first["candidate_sensitivity_report"]["unstable_candidate_region"]["region_class"], "unstable_across_bounded_heuristics")
            self.assertEqual(first["candidate_sensitivity_report"]["unstable_candidate_region"]["cell_count"], 751)
            self.assertEqual(
                first["candidate_sensitivity_report"]["heuristic_sensitive_candidate_region"]["region_class"],
                "heuristic_sensitive_across_bounded_heuristics",
            )
            self.assertEqual(first["candidate_sensitivity_report"]["heuristic_sensitive_candidate_region"]["cell_count"], 751)
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
                2828,
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["candidate_persistence_metrics"]["heuristic_sensitive_candidate_cell_count"],
                751,
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["selected_candidate_assessment"]["candidate_release_zone_id"],
                "tschamut_public_lps_release_bbox_candidate_058",
            )
            self.assertEqual(first["candidate_sensitivity_report"]["selected_candidate_assessment"]["candidate_stability_class"], "stable")
            self.assertEqual(
                first["candidate_sensitivity_report"]["selected_candidate_assessment"]["selected_candidate_classification"],
                "stable",
            )
            self.assertEqual(
                first["candidate_sensitivity_report"]["selected_candidate_assessment"]["selected_candidate_recommendation"]["status"],
                "adequate_for_bounded_engineering_probe",
            )
            self.assertIn(
                "persists under the bounded slope, smoothing, resolution, and AOI-boundary variants",
                first["candidate_sensitivity_report"]["selected_candidate_assessment"]["selected_candidate_recommendation"]["reason"],
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
                    "slope_below_workflow_generated_band",
                    "workflow_generated_candidate_band",
                    "reviewed_candidate_band",
                    "review_only_terrain_band",
                    "slope_above_review_only_band",
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
            self.assertEqual(first["candidate_release_zone_products"]["component_count"], 65)
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertEqual(first["candidate_review_package"]["review_package_status"], "emitted")
            self.assertEqual(first["candidate_review_package"]["review_decision_options"], ["accepted", "rejected", "needs_field_review"])
            self.assertEqual(
                [row["provenance_label"] for row in first["candidate_review_package"]["provenance_label_legend"]],
                ["workflow_generated", "field_supported", "mixed_provenance", "blocked_missing_provenance"],
            )
            self.assertEqual(first["candidate_review_package"]["review_summary"]["candidate_count"], 65)
            self.assertEqual(first["candidate_review_package"]["review_summary"]["default_review_decision"], "needs_field_review")
            self.assertEqual(first["candidate_review_package"]["review_summary"]["review_decision_counts"]["needs_field_review"], first["candidate_review_package"]["review_summary"]["candidate_count"])
            self.assertEqual(first["candidate_review_package"]["review_summary"]["provenance_label_counts"]["workflow_generated"], first["candidate_review_package"]["review_summary"]["candidate_count"])
            self.assertEqual(
                first["candidate_review_package"]["candidate_stability_summary"]["selected_candidate_assessment"]["selected_candidate_classification"],
                "stable",
            )
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
            self.assertEqual(first["candidate_release_zone_separation_summary"]["candidate_release_zone_set_status"], "review_ready")
            self.assertEqual(first["candidate_release_zone_separation_summary"]["candidate_review_package_status"], "emitted")

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
            self.assertEqual(
                normalize_report_text(text_report),
                normalize_report_text(planner.render_text_report(second)),
            )
            self.assertIn("schema_version: terrain_release_zone_candidate_metrics_v1", text_report)
            self.assertIn("candidate_metrics_status: ready", text_report)
            self.assertIn("excluded_area_summary:", text_report)
            self.assertIn("candidate_sensitivity_report:", text_report)
            self.assertIn("frozen_source_zone_footprint:", text_report)
            self.assertIn("candidate_release_zone_products:", text_report)
            self.assertIn("candidate_review_package:", text_report)

    def test_selected_candidate_assessment_maps_stable_sensitive_and_rejected_verdicts(self) -> None:
        stable = planner.build_selected_candidate_assessment(
            [
                {
                    "candidate_release_zone_id": "stable_candidate",
                    "candidate_stability_class": "stable",
                    "stability_rank": 1,
                    "stability_score": 0.95,
                    "minimum_retention_fraction": 0.95,
                    "mean_retention_fraction": 0.98,
                    "variant_presence_fraction": 1.0,
                }
            ]
        )
        sensitive = planner.build_selected_candidate_assessment(
            [
                {
                    "candidate_release_zone_id": "sensitive_candidate",
                    "candidate_stability_class": "sensitive",
                    "stability_rank": 1,
                    "stability_score": 0.75,
                    "minimum_retention_fraction": 0.75,
                    "mean_retention_fraction": 0.8,
                    "variant_presence_fraction": 0.9,
                }
            ]
        )
        rejected = planner.build_selected_candidate_assessment(
            [
                {
                    "candidate_release_zone_id": "rejected_candidate",
                    "candidate_stability_class": "unstable",
                    "stability_rank": 1,
                    "stability_score": 0.2,
                    "minimum_retention_fraction": 0.2,
                    "mean_retention_fraction": 0.3,
                    "variant_presence_fraction": 0.5,
                }
            ]
        )

        self.assertEqual(stable["selected_candidate_classification"], "stable")
        self.assertEqual(stable["selected_candidate_recommendation"]["status"], "adequate_for_bounded_engineering_probe")
        self.assertEqual(sensitive["selected_candidate_classification"], "sensitive")
        self.assertEqual(sensitive["selected_candidate_recommendation"]["status"], "replacement_candidate_recommended")
        self.assertEqual(rejected["selected_candidate_classification"], "rejected")
        self.assertEqual(rejected["selected_candidate_recommendation"]["status"], "replacement_candidate_recommended")

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
        self.assertEqual(report["candidate_review_package"]["selection_manifest_template"]["selected_candidate_ids"], [])
        self.assertEqual(
            report["candidate_review_package"]["selection_manifest_template"]["unselected_candidate_ids"],
            report["candidate_review_package"]["candidate_release_zone_ids"],
        )
        self.assertGreater(len(report["candidate_review_package"]["map_overlays"]), 0)
        self.assertEqual(report["candidate_review_package"]["map_overlays"][0]["overlay_id"], "candidate_polygons")
        self.assertIn("demonstration only", " ".join(report["candidate_review_package"]["non_operational_warnings"]))
        self.assertEqual(
            set(report["candidate_review_package"]["candidate_stability_summary"]["class_counts"].keys()),
            {"stable", "sensitive", "unstable"},
        )

    def test_real_chant_sura_fluelapass_inputs_emit_gis_ready_candidate_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "candidate_products"
            report = planner.build_report(
                repo_root=ROOT,
                terrain_crop_path=ROOT
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc",
                terrain_metadata_path=ROOT
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml",
                source_zone_metadata_path=ROOT
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                output_root=output_root,
            )
            self.assertEqual(report["candidate_metrics_status"], "ready")
            self.assertEqual(report["terrain_preprocessing"]["terrain_preprocessing_status"], "ready")
            self.assertEqual(report["terrain_preprocessing"]["terrain_provenance"]["classification"], "real_staged")
            self.assertEqual(report["terrain_inputs"]["terrain_preprocessing_status"], "ready")
            self.assertEqual(report["terrain_inputs"]["terrain_preprocessing_package"]["terrain_provenance"]["classification"], "real_staged")
            self.assertEqual(report["candidate_summary"]["candidate_cell_count"], 0)
            self.assertEqual(report["candidate_summary"]["candidate_area_m2"], 0.0)
            self.assertTrue(report["candidate_footprint_comparison"]["candidate_excludes_frozen_footprint"])
            self.assertEqual(report["candidate_sweep_measurements"]["output_file_count"], 7)
            self.assertGreater(report["candidate_sweep_measurements"]["output_total_bytes"], 0)
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["manifest"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["csv"]).exists())
            self.assertIn("candidate_polygons", [entry["overlay_id"] for entry in report["candidate_review_package"]["map_overlays"]])
            self.assertIn("candidate_mask", [entry["overlay_id"] for entry in report["candidate_review_package"]["map_overlays"]])
            self.assertEqual(report["candidate_release_zone_products"]["candidate_release_zone_ids"], [])
            self.assertEqual(report["candidate_review_package"]["candidate_release_zone_ids"], [])

    def test_restaged_management_aoi_inputs_emit_nonempty_candidate_bundle(self) -> None:
        if shutil.which("gdal_translate") is None or shutil.which("gdalinfo") is None:
            self.skipTest("gdal_translate and gdalinfo are required for the real-data restage test")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            restaged_root = workdir / "restaged_management_aoi"
            restage_report = restager.stage_management_aoi_restaged_inputs(
                repo_root=ROOT,
                output_root=restaged_root,
                raw_terrain_path=ROOT
                / "data"
                / "raw"
                / "swisstopo"
                / "chant_sura_fluelapass_portability_example_v1"
                / "swissalti3d_2019_2793-1180_2_2056_5728.tif",
                source_zone_metadata_path=ROOT
                / "data"
                / "processed"
                / "swisstopo"
                / "chant_sura_fluelapass_portability_example_v1"
                / "input"
                / "source_zone_metadata.yaml",
                aoi_tile_catalog_path=ROOT
                / "data"
                / "processed"
                / "swisstopo"
                / "chant_sura_fluelapass_portability_example_v1"
                / "input"
                / "aoi_tile_catalog.yaml",
                terrain_metadata_template_path=ROOT
                / "data"
                / "processed"
                / "swisstopo"
                / "chant_sura_fluelapass_portability_example_v1"
                / "input"
                / "terrain_metadata.yaml",
            )
            report = planner.build_report(
                repo_root=ROOT,
                terrain_crop_path=Path(restage_report["terrain_crop_path"]),
                terrain_metadata_path=Path(restage_report["terrain_metadata_path"]),
                source_zone_metadata_path=Path(restage_report["source_zone_metadata_path"]),
                output_root=workdir / "candidate_products",
                output_mode="both",
            )

            self.assertEqual(restage_report["restage_status"], "ready")
            self.assertEqual(restage_report["diagnostic"]["diagnostic_status"], "candidates_present")
            self.assertEqual(restage_report["first_blocker"]["blocker_id"], "none")
            self.assertEqual(report["candidate_metrics_status"], "ready")
            self.assertEqual(report["candidate_release_zone_set_status"], "emitted")
            self.assertEqual(report["candidate_summary"]["candidate_cell_count"], 12312)
            self.assertEqual(report["candidate_summary"]["candidate_area_m2"], 49248.0)
            self.assertGreater(report["candidate_summary"]["workflow_generated_candidate_cell_count"], 0)
            self.assertGreater(report["candidate_summary"]["reviewed_candidate_cell_count"], 0)
            self.assertEqual(report["candidate_release_zone_products"]["component_count"], 169)
            self.assertEqual(report["candidate_release_zone_products"]["polygon_feature_count"], 169)
            self.assertTrue(report["candidate_release_zone_products"]["candidate_excludes_frozen_footprint"])
            self.assertEqual(report["candidate_release_zone_separation_summary"]["deterministic_candidate_count"], 169)
            self.assertEqual(report["candidate_release_zone_separation_summary"]["separation_status"], "review_ready")
            self.assertEqual(report["candidate_sweep_measurements"]["output_file_count"], 7)
            self.assertGreater(report["candidate_sweep_measurements"]["runtime_seconds"], 0.0)
            self.assertGreater(report["candidate_sweep_measurements"]["output_total_bytes"], 0)
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(report["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["manifest"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(report["candidate_review_package"]["outputs"]["csv"]).exists())

    def test_candidate_review_overlay_bundle_writes_topographic_and_orthophoto_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            candidate_output_root = repo_root / "candidate_products"
            overlay_root = repo_root / "candidate_review_overlays"
            orthophoto_root = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"
            orthophoto_root.mkdir(parents=True, exist_ok=True)
            self._write_fake_png(orthophoto_root / "orthophoto.png")

            candidate_report = planner.build_report(
                repo_root=repo_root,
                terrain_crop_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc",
                terrain_metadata_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml",
                source_zone_metadata_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                output_root=candidate_output_root,
            )
            overlay_report = planner.build_candidate_review_overlay_report(
                candidate_report=candidate_report,
                repo_root=repo_root,
                output_root=overlay_root,
                orthophoto_background_root=orthophoto_root,
                overwrite=True,
            )
            self.assertEqual(overlay_report["candidate_review_overlay_status"], "ready")
            self.assertEqual(overlay_report["backgrounds"][0]["background_id"], "topographic_map")
            self.assertEqual(overlay_report["backgrounds"][0]["status"], "ready")
            self.assertEqual(overlay_report["backgrounds"][1]["background_id"], "orthophoto")
            self.assertEqual(overlay_report["backgrounds"][1]["status"], "ready")
            self.assertEqual(len(overlay_report["overlay_images"]), 2)
            self.assertTrue(Path(overlay_report["overlay_manifest_path"]).exists())
            self.assertTrue(Path(overlay_report["overlay_images"][0]["path"]).exists())
            self.assertTrue(Path(overlay_report["overlay_images"][1]["path"]).exists())

    def test_candidate_review_overlay_bundle_reports_blocked_missing_orthophoto_background(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            candidate_output_root = repo_root / "candidate_products"
            overlay_root = repo_root / "candidate_review_overlays"
            candidate_report = planner.build_report(
                repo_root=repo_root,
                terrain_crop_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc",
                terrain_metadata_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml",
                source_zone_metadata_path=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                output_root=candidate_output_root,
            )
            overlay_report = planner.build_candidate_review_overlay_report(
                candidate_report=candidate_report,
                repo_root=repo_root,
                output_root=overlay_root,
                orthophoto_background_root=repo_root / "missing_swissimage_root",
                overwrite=True,
            )
            self.assertEqual(overlay_report["candidate_review_overlay_status"], "blocked_missing_backgrounds")
            self.assertEqual(overlay_report["first_blocker"]["code"], "missing_orthophoto_background")
            self.assertEqual(overlay_report["backgrounds"][0]["status"], "ready")
            self.assertEqual(len(overlay_report["overlay_images"]), 1)
            self.assertTrue(Path(overlay_report["overlay_manifest_path"]).exists())
            self.assertTrue(Path(overlay_report["overlay_images"][0]["path"]).exists())

    def test_review_apply_edits_candidates_and_validates_provenance(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            review_package_path = self._write_review_package(
                workdir,
                rows=[
                    square_feature("cand_accept", 2600000.0, 1200000.0, 2.0, review_decision="accepted"),
                    square_feature("cand_reject", 2600010.0, 1200010.0, 2.0),
                    square_feature("cand_hold", 2600020.0, 1200020.0, 2.0),
                ],
            )
            output_root = workdir / "reviewed"

            report = planner.build_review_apply_report(
                review_package_path=review_package_path,
                candidate_review_decisions={
                    "cand_accept": "accepted",
                    "cand_reject": "rejected",
                    "cand_hold": "needs_field_review",
                },
                output_root=output_root,
            )

            manifest = json.loads(Path(report["outputs"]["manifest"]).read_text(encoding="utf-8"))
            geojson = json.loads(Path(report["outputs"]["polygon"]).read_text(encoding="utf-8"))

        self.assertEqual(report["review_package_status"], "review_applied")
        self.assertEqual(report["review_application_status"], "validated")
        self.assertEqual(report["candidate_metrics_status"], "ready")
        self.assertEqual(report["accepted_candidate_ids"], ["cand_accept"])
        self.assertEqual(report["rejected_candidate_ids"], ["cand_reject"])
        self.assertEqual(report["needs_field_review_candidate_ids"], ["cand_hold"])
        self.assertEqual(report["review_application"]["validation_status"], "validated")
        self.assertEqual(report["review_application"]["accepted_candidate_ids"], ["cand_accept"])
        self.assertEqual(report["review_application"]["validation_checks"]["allowed_provenance_labels"], list(planner.PROVENANCE_LABELS))
        self.assertEqual(report["candidate_release_zone_separation_summary"]["separation_status"], "review_applied")
        self.assertEqual(report["candidate_release_zone_separation_summary"]["accepted_release_zone_count"], 1)
        self.assertEqual(report["candidate_release_zone_separation_summary"]["accepted_release_zone_ids"], ["cand_accept"])
        self.assertEqual(report["selection_manifest"]["selection_manifest_status"], "selected_subset_ready")
        self.assertEqual(report["selection_manifest"]["selected_candidate_ids"], ["cand_accept"])
        self.assertEqual(report["selection_manifest"]["unselected_candidate_ids"], ["cand_reject", "cand_hold"])
        self.assertEqual(report["selection_manifest"]["candidate_selection_rows"][0]["provenance_label"], "workflow_generated")
        self.assertEqual(report["selection_manifest"]["candidate_selection_rows"][1]["selection_traceability"], "unselected")
        self.assertIn("demonstration only", " ".join(report["selection_manifest"]["non_operational_warnings"]))
        self.assertEqual(report["selection_manifest"]["candidate_selection_rows"][0]["candidate_stability_label"], "sensitive")
        self.assertEqual(manifest["review_package_status"], "review_applied")
        self.assertEqual(manifest["review_application_status"], "validated")
        self.assertEqual(manifest["review_summary"]["review_decision_counts"]["accepted"], 1)
        self.assertEqual(geojson["features"][0]["properties"]["review_decision"], "accepted")
        self.assertTrue(geojson["features"][0]["properties"]["accepted"])
        self.assertEqual(geojson["features"][1]["properties"]["review_decision"], "rejected")
        self.assertEqual(geojson["features"][2]["properties"]["review_decision"], "needs_field_review")
        self.assertIn("Candidate Review Apply", planner.render_review_apply_text_report(report))
        self.assertIn("Candidate vs Accepted Summary", planner.render_review_apply_text_report(report))

    def test_review_apply_rejects_unknown_ids_unreviewed_accepts_overclaims_and_empty_acceptance(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            review_package_path = self._write_review_package(workdir)

            with self.assertRaisesRegex(planner.TerrainReleaseZoneCandidateMetricsError, "unknown candidate ids"):
                planner.build_review_apply_report(
                    review_package_path=review_package_path,
                    candidate_review_decisions={"cand_accept": "accepted", "bogus_candidate": "rejected"},
                    output_root=workdir / "reviewed_unknown",
                )

            with self.assertRaisesRegex(planner.TerrainReleaseZoneCandidateMetricsError, "unreviewed accepted candidates"):
                planner.build_review_apply_report(
                    review_package_path=review_package_path,
                    candidate_review_decisions={"cand_reject": "rejected", "cand_hold": "needs_field_review"},
                    output_root=workdir / "reviewed_unreviewed",
                )

            overclaim_path = self._write_review_package(
                workdir,
                rows=[
                    square_feature("cand_accept", 2600000.0, 1200000.0, 2.0, review_decision="accepted"),
                    square_feature("cand_reject", 2600010.0, 1200010.0, 2.0, provenance_label="mixed_provenance"),
                ],
            )
            with self.assertRaisesRegex(planner.TerrainReleaseZoneCandidateMetricsError, "mixed-provenance overclaims"):
                planner.build_review_apply_report(
                    review_package_path=overclaim_path,
                    candidate_review_decisions={"cand_accept": "accepted", "cand_reject": "rejected"},
                    output_root=workdir / "reviewed_overclaim",
                )

            empty_review_package_path = self._write_review_package(
                workdir,
                rows=[
                    square_feature("cand_accept", 2600000.0, 1200000.0, 2.0),
                    square_feature("cand_reject", 2600010.0, 1200010.0, 2.0),
                    square_feature("cand_hold", 2600020.0, 1200020.0, 2.0),
                ],
            )
            with self.assertRaisesRegex(planner.TerrainReleaseZoneCandidateMetricsError, "at least one accepted candidate"):
                planner.build_review_apply_report(
                    review_package_path=empty_review_package_path,
                    candidate_review_decisions={"cand_accept": "rejected", "cand_reject": "rejected", "cand_hold": "needs_field_review"},
                    output_root=workdir / "reviewed_empty",
                )

    def _write_fake_png(self, path: Path) -> None:
        from PIL import Image  # type: ignore

        grid = np.linspace(0.15, 0.85, 16, dtype=float).reshape(4, 4)
        image = np.dstack([grid, grid[::-1], np.full_like(grid, 0.55)])
        rgba = np.clip(np.round(image * 255.0), 0, 255).astype(np.uint8)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba, mode="RGB").save(path)

    def _write_review_package(self, workdir: Path, rows: list[dict[str, object]] | None = None) -> Path:
        rows = rows or [
            square_feature("cand_accept", 2600000.0, 1200000.0, 2.0, review_decision="accepted"),
            square_feature("cand_reject", 2600010.0, 1200010.0, 2.0),
            square_feature("cand_hold", 2600020.0, 1200020.0, 2.0),
        ]
        geojson_path = workdir / "candidate_review.geojson"
        mask_path = workdir / "candidate_review_mask.asc"
        csv_path = workdir / "candidate_review.csv"
        manifest_path = workdir / "candidate_review_manifest.json"
        geojson_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "type": "FeatureCollection",
                    "candidate_site_id": "test_site",
                    "candidate_site_name": "Test Site",
                    "source_zone_id": "test_source_zone",
                    "candidate_generation_label": "heuristic_candidate_generation_only",
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": planner.provenance_label_legend(),
                    "features": rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        mask_path.write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
        csv_path.write_text("candidate_release_zone_id\n", encoding="utf-8")
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "review_package_status": "emitted",
                    "candidate_site_id": "test_site",
                    "candidate_site_name": "Test Site",
                    "source_zone_id": "test_source_zone",
                    "candidate_release_zone_set_status": "review_ready",
                    "candidate_release_zone_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": planner.provenance_label_legend(),
                    "review_summary": {
                        "review_row_count": len(rows),
                        "candidate_count": len(rows),
                        "review_decision_counts": {"accepted": 0, "rejected": 0, "needs_field_review": len(rows)},
                        "provenance_label_counts": {"workflow_generated": len(rows), "field_supported": 0, "mixed_provenance": 0, "blocked_missing_provenance": 0},
                        "candidate_stability_class_counts": {"stable": 0, "sensitive": len(rows), "unstable": 0},
                        "default_review_decision": "needs_field_review",
                    },
                    "candidate_review_rows": [row["properties"] for row in rows],
                    "candidate_stability_summary": {
                        "stability_score_method": "minimum_retention_fraction_across_bounded_heuristic_variants",
                        "ranking_count": len(rows),
                        "class_counts": {"stable": 0, "sensitive": len(rows), "unstable": 0},
                        "stable_candidate_ids": [],
                        "sensitive_candidate_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                        "unstable_candidate_ids": [],
                        "bounded_probe_candidate_selection": {
                            "selection_sizes": [2, 4, 8],
                            "selection_by_size": {
                                "2": {
                                    "selection_size": 2,
                                    "candidate_release_zone_ids": [row["properties"]["candidate_release_zone_id"] for row in rows[:2]],
                                    "candidate_rankings": [],
                                },
                                "4": {
                                    "selection_size": 4,
                                    "candidate_release_zone_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                                    "candidate_rankings": [],
                                },
                                "8": {
                                    "selection_size": 8,
                                    "candidate_release_zone_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                                    "candidate_rankings": [],
                                },
                            },
                        },
                    },
                    "candidate_sensitivity_summary": {},
                    "candidate_footprint_comparison": {},
                    "frozen_source_zone_footprint": {},
                    "map_overlays": [],
                    "non_operational_warnings": planner.candidate_review_non_operational_warnings(),
                    "claim_boundaries": {
                        "heuristic_workflow_input_only": True,
                        "validated_release_zone_evidence": False,
                        "field_validation_claims_allowed": False,
                        "physical_release_probability_claims_allowed": False,
                        "scale_up_authorized": False,
                        "operational_claims_allowed": False,
                        "notes": [
                            "candidate review rows remain workflow review inputs until the source zone is frozen",
                            "accepted, rejected, and needs_field_review are editable review states, not evidence claims",
                            "selection is for demonstration only and does not authorize operational approval",
                        ],
                    },
                    "selection_manifest_template": {
                        "schema_version": "terrain_release_zone_candidate_selection_manifest_v1",
                        "selection_manifest_status": "template",
                        "selection_mode": "bounded_subset_for_scenario_generation",
                        "candidate_site_id": "test_site",
                        "candidate_site_name": "Test Site",
                        "source_zone_id": "test_source_zone",
                        "review_package_status": "emitted",
                        "review_application_status": "not_applied",
                        "review_package_manifest_path": str(manifest_path),
                        "review_package_manifest_sha256": None,
                        "output_root": str(workdir),
                        "repo_root": str(workdir),
                        "candidate_release_zone_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                        "selected_candidate_ids": [],
                        "unselected_candidate_ids": [row["properties"]["candidate_release_zone_id"] for row in rows],
                        "selected_candidate_count": 0,
                        "unselected_candidate_count": len(rows),
                        "candidate_selection_rows": [],
                        "selected_candidate_rows": [],
                        "unselected_candidate_rows": [],
                        "selected_candidate_ids_by_size": {"2": [], "4": [], "8": []},
                        "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                        "provenance_label_legend": planner.provenance_label_legend(),
                        "candidate_stability_summary": {},
                        "candidate_sensitivity_summary": {},
                        "map_overlays": [],
                        "non_operational_warnings": planner.candidate_review_non_operational_warnings(),
                        "claim_boundaries": {
                            "heuristic_workflow_input_only": True,
                            "validated_release_zone_evidence": False,
                            "field_validation_claims_allowed": False,
                            "physical_release_probability_claims_allowed": False,
                            "scale_up_authorized": False,
                            "operational_claims_allowed": False,
                            "selection_for_demonstration_only": True,
                            "notes": [
                                "candidate review rows remain workflow review inputs until the source zone is frozen",
                                "accepted, rejected, and needs_field_review are editable review states, not evidence claims",
                                "selection is for demonstration only and does not authorize operational approval",
                                "unselected candidates remain traceable in the review package for auditability",
                            ],
                        },
                    },
                    "outputs": {
                        "polygon": str(geojson_path),
                        "mask": str(mask_path),
                        "csv": str(csv_path),
                        "manifest": str(manifest_path),
                    },
                    "output_root": str(workdir),
                    "repo_root": str(workdir),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def _write_site_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


def normalize_report_text(text: str) -> str:
    return re.sub(r"(- runtime_seconds: )\d+(?:\.\d+)?", r"\1<measured>", text)


if __name__ == "__main__":
    unittest.main()
