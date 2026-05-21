from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py"
PLANNER_SCRIPT_PATH = ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"
POLICY_VALIDATOR_PATH = ROOT / "scripts" / "validate_source_scenario_policy.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


freezer = load_module(SCRIPT_PATH, "generate_candidate_source_zone_scenarios_freezer")
planner = load_module(PLANNER_SCRIPT_PATH, "plan_terrain_release_zone_candidates_for_freezer_tests")
policy_validator = load_module(POLICY_VALIDATOR_PATH, "validate_source_scenario_policy_for_freezer_tests")


def square_feature(candidate_id: str, xmin: float, ymin: float, size: float) -> dict[str, object]:
    return {
        "type": "Feature",
        "id": candidate_id,
        "properties": {
            "candidate_release_zone_id": candidate_id,
            "review_decision": "accepted" if candidate_id != "cand_rejected" else "rejected",
            "accepted": candidate_id != "cand_rejected",
            "rejected": candidate_id == "cand_rejected",
            "needs_field_review": False,
            "candidate_generation_label": "heuristic_candidate_generation_only",
            "candidate_sensitivity_label": "heuristic_sensitive_across_bounded_heuristics",
            "release_cell_count": 1,
            "release_cell_ids": [f"{candidate_id}__cell_000"],
            "provenance_label": "workflow_generated",
            "component_bbox_lv95_m": {
                "crs": "EPSG:2056",
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmin + size,
                "ymax": ymin + size,
            },
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


def write_prau_mulins_review_package(workdir: Path) -> Path:
    review_root = workdir / "validation/private/source_zone_review"
    review_root.mkdir(parents=True, exist_ok=True)
    review_package_path = review_root / "tschamut_adjacent_prau_mulins_candidate_v1_review_manifest.json"
    geojson_path = review_root / "tschamut_adjacent_prau_mulins_candidate_v1_review.geojson"
    csv_path = review_root / "tschamut_adjacent_prau_mulins_candidate_v1_review.csv"
    mask_path = review_root / "tschamut_adjacent_prau_mulins_candidate_v1_review_mask.asc"

    bbox = {
        "crs": "EPSG:2056",
        "xmin": 2696440.0,
        "xmax": 2696525.0,
        "ymin": 1167485.0,
        "ymax": 1167575.0,
    }
    review_package = {
        "schema_version": "terrain_release_zone_candidate_review_package_v1",
        "review_package_status": "review_applied",
        "review_application_status": "validated",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "source_zone_id": "tschamut_adjacent_prau_mulins_reviewed_source_zone_v1",
        "candidate_release_zone_set_status": "review_applied",
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "candidate_release_zone_ids": ["tschamut_adjacent_prau_mulins_candidate_v1"],
        "accepted_candidate_ids": ["tschamut_adjacent_prau_mulins_candidate_v1"],
        "rejected_candidate_ids": [],
        "needs_field_review_candidate_ids": [],
        "review_decision_options": ["accepted", "rejected", "needs_field_review"],
        "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
        "provenance_label_legend": planner.provenance_label_legend(),
        "review_summary": {
            "review_row_count": 1,
            "candidate_count": 1,
            "review_decision_counts": {"accepted": 1, "rejected": 0, "needs_field_review": 0},
            "provenance_label_counts": {"workflow_generated": 1, "field_supported": 0, "mixed_provenance": 0, "blocked_missing_provenance": 0},
            "candidate_stability_class_counts": {"stable": 0, "sensitive": 1, "unstable": 0},
            "default_review_decision": "needs_field_review",
        },
        "candidate_review_rows": [
            {
                "candidate_release_zone_id": "tschamut_adjacent_prau_mulins_candidate_v1",
                "candidate_generation_label": "heuristic_candidate_generation_only",
                "review_decision": "accepted",
                "accepted": True,
                "rejected": False,
                "needs_field_review": False,
                "provenance_label": "workflow_generated",
                "candidate_stability_label": "sensitive",
                "candidate_stability_class": "sensitive",
                "candidate_stability_rank": 1,
                "candidate_stability_score": 0.88,
                "candidate_minimum_retention_fraction": 0.88,
                "candidate_mean_retention_fraction": 0.9,
                "candidate_variant_presence_fraction": 1.0,
                "candidate_sensitivity_label": "heuristic_sensitive_across_bounded_heuristics",
                "release_cell_count": 1,
                "release_cell_ids": ["tschamut_adjacent_prau_mulins_candidate_v1__cell_000"],
                "component_cell_count": 1,
                "component_area_m2": 7650.0,
                "component_bbox_lv95_m": bbox,
                "component_slope_min_deg": 53.5,
                "component_slope_max_deg": 53.5,
                "component_slope_mean_deg": 53.5,
                "component_slope_median_deg": 53.5,
                "candidate_review_note": "Selected from expanded terrain-screening plus user visual review; not field validation.",
                "review_provenance_note": "Selected from expanded terrain-screening plus user visual review; not field validation.",
                "provenance_ref": "terrain_and_user_visual_review",
                "review_editable": True,
                "comparison_to_frozen_footprint_excludes_source_zone": True,
                "comparison_to_frozen_footprint_cell_count": 0,
                "source_inputs": [
                    "validation/private/source_zone_review/tschamut_expanded_source_zone_candidate_report.json",
                ],
                "candidate_site_id": "tschamut_public_pilot",
            }
        ],
        "candidate_footprint_comparison": {
            "comparison_status": "ready",
            "comparison_mode": "candidate_mask_vs_frozen_source_zone_footprint_mask",
            "candidate_excludes_frozen_footprint": True,
            "candidate_cell_count": 1,
            "frozen_footprint_cell_count": 9,
            "candidate_and_frozen_footprint_intersection_cell_count": 0,
            "candidate_and_frozen_footprint_intersection_area_m2": 0.0,
            "candidate_overlap_fraction_of_candidate_cells": 0.0,
            "candidate_overlap_fraction_of_frozen_footprint_cells": 0.0,
        },
        "frozen_source_zone_footprint": {
            "source_zone_id": "tschamut_public_lps_release_bbox",
            "geometry_type": "polygon",
            "polygon_area_m2_exact": 327.01513671875,
            "masked_cell_count_on_terrain_grid": 0,
            "masked_area_m2_on_terrain_grid": 0.0,
            "vertex_count": 4,
            "vertex_coordinates": [
                [2696622.482, 1167728.092],
                [2696640.895, 1167728.092],
                [2696640.895, 1167745.852],
                [2696622.482, 1167745.852],
            ],
            "bbox_lv95_m": {
                "crs": "EPSG:2056",
                "xmin": 2696622.482,
                "xmax": 2696640.895,
                "ymin": 1167728.092,
                "ymax": 1167745.852,
            },
        },
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
                "selected from expanded terrain-screening plus user visual review; not field validation",
            ],
        },
        "review_application": {
            "schema_version": "terrain_release_zone_candidate_review_application_v1",
            "review_package_path": str(review_package_path.relative_to(workdir)),
            "output_root": "validation/private/source_zone_review",
            "validation_status": "validated",
            "validation_checks": {
                "unknown_candidate_ids": [],
                "unreviewed_accepted_candidate_ids": [],
                "mixed_provenance_overclaim_candidate_ids": [],
                "accepted_missing_validation_candidate_ids": [],
                "accepted_candidate_count": 1,
                "reviewed_candidate_count": 1,
                "allowed_provenance_labels": list(planner.PROVENANCE_LABELS),
            },
            "reviewed_candidate_ids": ["tschamut_adjacent_prau_mulins_candidate_v1"],
            "explicit_reviewed_candidate_ids": ["tschamut_adjacent_prau_mulins_candidate_v1"],
            "accepted_candidate_ids": ["tschamut_adjacent_prau_mulins_candidate_v1"],
            "rejected_candidate_ids": [],
            "needs_field_review_candidate_ids": [],
            "validated_candidate_count": 1,
        },
        "map_overlays": [
            {
                "overlay_id": "candidate_polygons",
                "overlay_kind": "vector",
                "label": "Candidate polygons",
                "path": str(geojson_path.relative_to(workdir)),
                "label_fields": [
                    "candidate_release_zone_id",
                    "candidate_stability_label",
                    "candidate_sensitivity_label",
                    "provenance_label",
                    "review_decision",
                ],
                "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                "traceability": "candidate ids, stability labels, sensitivity labels, and provenance stay attached to each feature",
            },
            {
                "overlay_id": "candidate_mask",
                "overlay_kind": "raster_mask",
                "label": "Candidate mask",
                "path": str(mask_path.relative_to(workdir)),
                "label_fields": ["candidate_release_zone_id"],
                "traceability": "the mask preserves the deterministic heuristic footprint that generated the polygons",
            },
        ],
        "non_operational_warnings": [
            "candidate review is for demonstration only and human selection only",
            "candidate review does not validate, calibrate, or approve operational hazard products",
            "selection may be used to choose a bounded scenario-generation subset, but it does not change claim boundaries",
            "unselected candidates remain traceable and must be preserved in the review package for auditability",
        ],
        "outputs": {
            "polygon": str(geojson_path.relative_to(workdir)),
            "mask": str(mask_path.relative_to(workdir)),
            "csv": str(csv_path.relative_to(workdir)),
            "manifest": str(review_package_path.relative_to(workdir)),
        },
        "output_root": "validation/private/source_zone_review",
        "repo_root": ".",
    }

    geojson = {
        "schema_version": "terrain_release_zone_candidate_review_package_v1",
        "type": "FeatureCollection",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "source_zone_id": "tschamut_adjacent_prau_mulins_reviewed_source_zone_v1",
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "review_decision_options": ["accepted", "rejected", "needs_field_review"],
        "provenance_label_legend": planner.provenance_label_legend(),
        "features": [
            {
                "type": "Feature",
                "id": "tschamut_adjacent_prau_mulins_candidate_v1",
                "properties": review_package["candidate_review_rows"][0],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox["xmin"], bbox["ymin"]],
                        [bbox["xmax"], bbox["ymin"]],
                        [bbox["xmax"], bbox["ymax"]],
                        [bbox["xmin"], bbox["ymax"]],
                        [bbox["xmin"], bbox["ymin"]],
                    ]],
                },
            }
        ],
    }

    review_package_path.write_text(json.dumps(review_package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    geojson_path.write_text(json.dumps(geojson, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path.write_text(
        "candidate_release_zone_id,candidate_generation_label,review_decision,accepted,rejected,needs_field_review,provenance_label,candidate_stability_label,candidate_stability_class,candidate_stability_rank,candidate_stability_score,candidate_minimum_retention_fraction,candidate_mean_retention_fraction,candidate_variant_presence_fraction,candidate_sensitivity_label,release_cell_count,release_cell_ids,component_cell_count,component_area_m2,component_slope_min_deg,component_slope_max_deg,component_slope_mean_deg,component_slope_median_deg\n"
        "tschamut_adjacent_prau_mulins_candidate_v1,heuristic_candidate_generation_only,accepted,true,false,false,workflow_generated,sensitive,sensitive,1,0.88,0.88,0.9,1.0,heuristic_sensitive_across_bounded_heuristics,1,tschamut_adjacent_prau_mulins_candidate_v1__cell_000,1,7650.0,53.5,53.5,53.5,53.5\n",
        encoding="utf-8",
    )
    mask_path.write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
    return review_package_path


class ReviewedCandidateSourceZoneFreezerTests(unittest.TestCase):
    def _write_review_package(self, workdir: Path) -> Path:
        emitted_geojson_path = workdir / "review_candidates.geojson"
        emitted_mask_path = workdir / "review_candidates_mask.asc"
        emitted_csv_path = workdir / "review_candidates.csv"
        emitted_manifest_path = workdir / "review_package_emitted.json"
        features = [
            square_feature("cand_accept_a", 2600000.0, 1200000.0, 2.0),
            square_feature("cand_rejected", 2600010.0, 1200010.0, 2.0),
            square_feature("cand_accept_b", 2600020.0, 1200020.0, 2.0),
        ]
        emitted_geojson_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "type": "FeatureCollection",
                    "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                    "candidate_site_name": "Chant Sura / Fluelapass portability example",
                    "source_zone_id": "chant_sura_reviewed_source_zone",
                    "candidate_generation_label": "heuristic_candidate_generation_only",
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": planner.provenance_label_legend(),
                    "features": features,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        emitted_mask_path.write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
        emitted_csv_path.write_text("candidate_release_zone_id\n", encoding="utf-8")
        emitted_manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "review_package_status": "emitted",
                    "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                    "candidate_site_name": "Chant Sura / Fluelapass portability example",
                    "source_zone_id": "chant_sura_reviewed_source_zone",
                    "candidate_release_zone_set_status": "review_ready",
                    "candidate_release_zone_ids": [feature["properties"]["candidate_release_zone_id"] for feature in features],
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": planner.provenance_label_legend(),
                    "review_summary": {
                        "review_row_count": len(features),
                        "candidate_count": len(features),
                        "review_decision_counts": {"accepted": 0, "rejected": 0, "needs_field_review": len(features)},
                        "provenance_label_counts": {"workflow_generated": len(features), "field_supported": 0, "mixed_provenance": 0, "blocked_missing_provenance": 0},
                        "default_review_decision": "needs_field_review",
                    },
                    "candidate_review_rows": [feature["properties"] for feature in features],
                    "candidate_sensitivity_summary": {},
                    "candidate_footprint_comparison": {},
                    "frozen_source_zone_footprint": {},
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
                        ],
                    },
                    "outputs": {
                        "polygon": str(emitted_geojson_path),
                        "mask": str(emitted_mask_path),
                        "csv": str(emitted_csv_path),
                        "manifest": str(emitted_manifest_path),
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
        reviewed_output_root = workdir / "reviewed"
        reviewed = planner.build_review_apply_report(
            review_package_path=emitted_manifest_path,
            candidate_review_decisions={
                "cand_accept_a": "accepted",
                "cand_rejected": "rejected",
                "cand_accept_b": "accepted",
            },
            output_root=reviewed_output_root,
        )
        return Path(reviewed["outputs"]["manifest"])

    def test_freezer_generates_deterministic_ids_and_excludes_rejected_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            review_package_path = self._write_review_package(workdir)
            output_root = workdir / "validation/private/chant_sura_fluelapass_portability_example_v1"
            review_manifest = json.loads(review_package_path.read_text(encoding="utf-8"))

            first = freezer.build_freezer_report(
                review_package_path=review_package_path,
                accepted_candidate_ids=["cand_accept_a", "cand_accept_b"],
                output_root=output_root,
                trajectory_count=24,
                seed=34014,
            )
            second = freezer.build_freezer_report(
                review_package_path=review_package_path,
                accepted_candidate_ids=["cand_accept_a", "cand_accept_b"],
                output_root=output_root,
                trajectory_count=24,
                seed=34014,
            )

            source_zone_path = Path(first["output_paths"]["source_zone_metadata"])
            release_rows_path = Path(first["output_paths"]["release_rows"])
            scenario_table_path = Path(first["output_paths"]["scenario_table"])
            policy_path = Path(first["output_paths"]["policy"])
            manifest_path = Path(first["output_paths"]["manifest"])

            source_zone = json.loads(source_zone_path.read_text(encoding="utf-8")) if source_zone_path.suffix == ".json" else None
            release_rows = release_rows_path.read_text(encoding="utf-8").splitlines()
            scenario_rows = scenario_table_path.read_text(encoding="utf-8").splitlines()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            policy = policy_validator.read_yaml(policy_path)

        self.assertEqual(first, second)
        self.assertEqual(first["freezer_status"], "ready")
        self.assertEqual(review_manifest["review_package_status"], "review_applied")
        self.assertEqual(review_manifest["review_application_status"], "validated")
        self.assertEqual(first["accepted_candidate_ids"], ["cand_accept_a", "cand_accept_b"])
        self.assertEqual(first["rejected_candidate_ids"], ["cand_rejected"])
        self.assertEqual(first["release_row_count"], 2)
        self.assertEqual(first["scenario_row_count"], 6)
        self.assertEqual(first["block_family_ids"], ["reviewed_block_family_small", "reviewed_block_family_medium", "reviewed_block_family_large"])
        self.assertTrue(all(row["annual_frequency_per_year"] == "" for row in first["release_rows"]))
        self.assertTrue(all(row["annual_frequency_per_year"] == "" for row in first["scenario_table_rows"]))
        self.assertTrue(all(row["time_horizon_years"] == "" for row in first["release_rows"]))
        self.assertTrue(all(row["time_horizon_years"] == "" for row in first["scenario_table_rows"]))
        self.assertNotIn("cand_rejected", "\n".join(release_rows))
        self.assertNotIn("cand_rejected", "\n".join(scenario_rows))
        self.assertEqual(manifest["accepted_candidate_ids"], ["cand_accept_a", "cand_accept_b"])
        self.assertEqual(manifest["rejected_candidate_ids"], ["cand_rejected"])
        self.assertEqual(manifest["conditional_weight_semantics"], "conditional_sampling_only")
        self.assertEqual(policy["policy_status"], "ready_for_conditional_pilot")
        policy_validator.validate_policy(policy)

    def test_freezer_rejects_invalid_block_weights(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            review_package_path = self._write_review_package(workdir)

            with self.assertRaisesRegex(freezer.CandidateSourceZoneFreezerError, "positive value"):
                freezer.build_freezer_report(
                    review_package_path=review_package_path,
                    accepted_candidate_ids=["cand_accept_a"],
                    output_root=workdir / "validation/private/chant_sura_fluelapass_portability_example_v1",
                    trajectory_count=24,
                    seed=34014,
                    block_scenarios=[
                        {
                            "block_scenario_id": "invalid_zero_weight",
                            "block_family_id": "invalid_family",
                            "block_size_class": "invalid",
                            "block_shape_class": "sphere",
                            "block_radius_m": 0.1,
                            "block_mass_kg": 1.0,
                            "sampling_weight": 0.0,
                        }
                    ],
                )

            with self.assertRaisesRegex(freezer.CandidateSourceZoneFreezerError, "nonnegative"):
                freezer.build_freezer_report(
                    review_package_path=review_package_path,
                    accepted_candidate_ids=["cand_accept_a"],
                    output_root=workdir / "validation/private/chant_sura_fluelapass_portability_example_v1",
                    trajectory_count=24,
                    seed=34014,
                    block_scenarios=[
                        {
                            "block_scenario_id": "invalid_negative_weight",
                            "block_family_id": "invalid_family",
                            "block_size_class": "invalid",
                            "block_shape_class": "sphere",
                            "block_radius_m": 0.1,
                            "block_mass_kg": 1.0,
                            "sampling_weight": -1.0,
                        }
                    ],
                )

    def test_freezer_loads_the_adjacent_prau_mulins_review_candidate_southwest_of_the_frozen_footprint(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workdir = Path(tmp)
            review_package_path = write_prau_mulins_review_package(workdir)
            report = freezer.build_freezer_report(
                review_package_path=review_package_path,
                accepted_candidate_ids=["tschamut_adjacent_prau_mulins_candidate_v1"],
                output_root=workdir / "validation/private/source_zone_review_freeze",
                trajectory_count=24,
                seed=34014,
            )

        source_zone_metadata = report["source_zone_metadata"]
        bbox = source_zone_metadata["geometry"]["vertices"]
        xmin = min(vertex[0] for vertex in bbox)
        xmax = max(vertex[0] for vertex in bbox)
        ymin = min(vertex[1] for vertex in bbox)
        ymax = max(vertex[1] for vertex in bbox)

        self.assertEqual(report["freezer_status"], "ready")
        self.assertEqual(report["accepted_candidate_ids"], ["tschamut_adjacent_prau_mulins_candidate_v1"])
        self.assertEqual(source_zone_metadata["source_zone_id"], "tschamut_adjacent_prau_mulins_reviewed_source_zone_v1")
        self.assertEqual(
            source_zone_metadata["source_review_package_path"],
            str(review_package_path.resolve()),
        )
        self.assertGreaterEqual(xmin, 2696440.0)
        self.assertLessEqual(xmax, 2696525.0)
        self.assertGreaterEqual(ymin, 1167485.0)
        self.assertLessEqual(ymax, 1167575.0)
        self.assertLess(xmax, 2696622.482)
        self.assertLess(ymax, 1167728.092)


if __name__ == "__main__":
    unittest.main()
