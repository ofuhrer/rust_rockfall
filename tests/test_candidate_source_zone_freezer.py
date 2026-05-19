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


if __name__ == "__main__":
    unittest.main()
