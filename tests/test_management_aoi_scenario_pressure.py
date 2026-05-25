from __future__ import annotations

import importlib.util
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_management_aoi_scenario_pressure.py"
POLICY_PATH = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
ADJACENT_CANDIDATE_METRICS_PATH = ROOT / "validation/private/source_zone_review/tschamut_expanded_source_zone_candidate_report.json"
ADJACENT_CANDIDATE_REVIEW_PATH = ROOT / "validation/private/source_zone_review/tschamut_adjacent_prau_mulins_candidate_v1_review_manifest.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module(SCRIPT_PATH, "summarize_management_aoi_scenario_pressure")


class ManagementAoiScenarioPressureTests(unittest.TestCase):
    def test_zero_candidate_set_preserves_the_named_deferral(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            bundle_root = tmp_root / "validation/private/chant_sura_fluelapass_portability_example_v1/tb377_candidate_stability"
            bundle_root.mkdir(parents=True, exist_ok=True)
            metrics_path = bundle_root / "tschamut_public_pilot_release_zone_candidates_manifest.json"
            review_path = bundle_root / "tschamut_public_pilot_release_zone_candidate_review_manifest.json"

            metrics_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_products_v1",
                        "candidate_release_zone_set_status": "emitted",
                        "candidate_cell_count": 0,
                        "candidate_area_m2": 0.0,
                        "candidate_summary": {
                            "candidate_cell_count": 0,
                            "candidate_area_m2": 0.0,
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            review_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_selection_manifest_v1",
                        "review_package_status": "emitted",
                        "candidate_release_zone_set_status": "review_ready",
                        "candidate_release_zone_ids": [],
                        "review_summary": {
                            "candidate_count": 0,
                            "review_row_count": 0,
                            "review_decision_counts": {"accepted": 0, "rejected": 0, "needs_field_review": 0},
                            "candidate_stability_class_counts": {"stable": 0, "unstable": 0, "sensitive": 0},
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_root / "candidate_mask.asc").write_text("mask\n", encoding="utf-8")
            (bundle_root / "candidate_review.geojson").write_text("{\"type\":\"FeatureCollection\",\"features\":[]}\n", encoding="utf-8")

            output_root = tmp_root / "scenario_pressure"
            report = MODULE.build_report(
                candidate_metrics_manifest_path=metrics_path,
                candidate_review_manifest_path=review_path,
                policy_path=POLICY_PATH,
                output_root=output_root,
            )
            report_path = output_root / "management_aoi_scenario_pressure_report.json"
            self.assertTrue(report_path.exists())

        self.assertEqual(report["schema_version"], "management_aoi_scenario_pressure_v1")
        self.assertEqual(report["scenario_pressure_status"], "blocked_source_zone_footprint_overlap")
        self.assertEqual(report["candidate_evidence"]["candidate_release_zone_set_status"], "emitted")
        self.assertEqual(report["candidate_evidence"]["candidate_cell_count"], 0)
        self.assertEqual(report["candidate_evidence"]["candidate_area_m2"], 0.0)
        self.assertEqual(report["candidate_evidence"]["bundle_measurements"]["file_count"], 4)
        self.assertGreater(report["candidate_evidence"]["bundle_measurements"]["total_bytes"], 0)
        self.assertEqual(report["candidate_evidence"]["review_summary"]["candidate_count"], 0)
        self.assertEqual(report["deferral_record"]["blocker_type"], "source_zone_footprint_overlap")
        self.assertEqual(report["deferral_record"]["slope_band_status"], "not_reached")
        self.assertIn("source-zone footprint", report["blocked_reason"])
        self.assertIn("larger real-staged AOI crop", report["required_upstream_replacement"])
        self.assertEqual(report["scenario_generation_pressure"]["scenario_row_count"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["cardinality_pressure_summary"]["scenario_count"], 0)
        self.assertEqual(
            report["scenario_generation_pressure"]["cardinality_pressure_summary"]["first_cardinality_growth_driver"],
            "single_scenario_baseline",
        )
        self.assertEqual(
            report["scenario_generation_pressure"]["prepared_pilot_smoke_handoff"]["smoke_status"],
            "blocked_missing_inputs",
        )
        self.assertEqual(
            report["scenario_generation_pressure"]["prepared_pilot_smoke_handoff"]["command_plan_target"],
            "second_site_aoi_to_prepared_pilot_dry_run",
        )
        self.assertIn(
            "source_candidate_id",
            report["scenario_generation_pressure"]["prepared_pilot_smoke_handoff"]["missing_fields"],
        )
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_csv_bytes"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_manifest_bytes"], 0)
        self.assertEqual(
            [row["block_family_id"] for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]],
            ["tschamut_public_block_small", "tschamut_public_block_medium", "tschamut_public_block_large"],
        )
        self.assertTrue(all(row["row_count"] == 0 for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]))
        self.assertEqual(report["command_plan_implications"][1]["command_id"], "second_site_release_plan_execution_template")
        self.assertEqual(report["command_plan_implications"][1]["status"], "blocked_source_zone_footprint_overlap")
        self.assertIn("real-staged AOI crop", report["command_plan_implications"][1]["implication"])
        self.assertEqual(report["claim_boundary"]["annual_frequency_supported"], False)

        text = MODULE.render_text_report(report)
        self.assertIn("Management AOI Scenario Pressure", text)
        self.assertIn("scenario_pressure_status: `blocked_source_zone_footprint_overlap`", text)
        self.assertIn("second_site_release_plan_execution_template", text)

    def test_non_empty_candidate_package_reports_ready_pressure(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            bundle_root = tmp_root / "validation/private/chant_sura_fluelapass_portability_example_v1/tb377_candidate_stability"
            bundle_root.mkdir(parents=True, exist_ok=True)
            metrics_path = bundle_root / "tschamut_public_pilot_release_zone_candidates_manifest.json"
            review_path = bundle_root / "tschamut_public_pilot_release_zone_candidate_review_manifest.json"

            metrics_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_products_v1",
                        "candidate_release_zone_set_status": "emitted",
                        "candidate_cell_count": 2,
                        "candidate_area_m2": 8.0,
                        "candidate_summary": {
                            "candidate_cell_count": 2,
                            "candidate_area_m2": 8.0,
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            review_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_selection_manifest_v1",
                        "review_package_status": "emitted",
                        "candidate_release_zone_set_status": "review_ready",
                        "candidate_release_zone_ids": ["candidate_a", "candidate_b"],
                        "candidate_review_rows": [
                            {
                                "candidate_release_zone_id": "candidate_a",
                                "review_decision": "needs_field_review",
                                "accepted": False,
                                "rejected": False,
                                "needs_field_review": True,
                                "provenance_label": "workflow_generated",
                                "component_bbox_lv95_m": {"crs": "EPSG:2056", "xmin": 2600000.0, "ymin": 1200000.0, "xmax": 2600002.0, "ymax": 1200002.0},
                            },
                            {
                                "candidate_release_zone_id": "candidate_b",
                                "review_decision": "needs_field_review",
                                "accepted": False,
                                "rejected": False,
                                "needs_field_review": True,
                                "provenance_label": "workflow_generated",
                                "component_bbox_lv95_m": {"crs": "EPSG:2056", "xmin": 2600010.0, "ymin": 1200010.0, "xmax": 2600012.0, "ymax": 1200012.0},
                            },
                        ],
                        "review_summary": {
                            "candidate_count": 2,
                            "review_row_count": 2,
                            "review_decision_counts": {"accepted": 2, "rejected": 0, "needs_field_review": 0},
                            "candidate_stability_class_counts": {"stable": 2, "unstable": 0, "sensitive": 0},
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_root / "candidate_mask.asc").write_text("mask\n", encoding="utf-8")
            (bundle_root / "candidate_review.geojson").write_text("{\"type\":\"FeatureCollection\",\"features\":[]}\n", encoding="utf-8")

            report = MODULE.build_report(
                candidate_metrics_manifest_path=metrics_path,
                candidate_review_manifest_path=review_path,
                policy_path=POLICY_PATH,
                output_root=tmp_root / "scenario_pressure_ready",
                scenario_output_root=tmp_root / "scenario_table_ready",
            )

        self.assertEqual(report["scenario_pressure_status"], "ready")
        self.assertEqual(report["candidate_evidence"]["candidate_cell_count"], 2)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_row_count"], 6)
        self.assertEqual(report["scenario_generation_pressure"]["cardinality_pressure_summary"]["scenario_count"], 6)
        self.assertEqual(report["scenario_generation_pressure"]["cardinality_pressure_summary"]["expected_trajectory_count"], 360)
        self.assertEqual(
            report["scenario_generation_pressure"]["cardinality_pressure_summary"]["first_cardinality_growth_driver"],
            "source_zone_count",
        )
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_file_count"], 5)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_csv_bytes"], 0)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_manifest_bytes"], 0)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_total_bytes"], 0)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_runtime_seconds"], 0.0)
        self.assertEqual([row["row_count"] for row in report["scenario_generation_pressure"]["scenario_family_cardinality"]], [2, 2, 2])
        self.assertEqual([row["row_count"] for row in report["scenario_generation_pressure"]["release_zone_cardinality"]], [3, 3])
        self.assertTrue(all(row["row_count"] == 6 for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]))
        self.assertEqual(report["scenario_table_generation"]["accepted_candidate_count"], 2)
        smoke_handoff = report["scenario_table_generation"]["prepared_pilot_smoke_handoff"]
        self.assertEqual(smoke_handoff["smoke_status"], "ready")
        self.assertEqual(smoke_handoff["source_candidate_id"], "candidate_a")
        self.assertEqual(smoke_handoff["source_candidate_ids"], ["candidate_a", "candidate_b"])
        self.assertEqual(smoke_handoff["scenario_table_id"], "scenario_table_ready")
        self.assertEqual(smoke_handoff["command_plan_target"], "second_site_aoi_to_prepared_pilot_dry_run")
        self.assertTrue(smoke_handoff["scenario_table_csv"].endswith("scenario_table.csv"))
        self.assertEqual(report["scenario_generation_pressure"]["prepared_pilot_smoke_handoff"], smoke_handoff)
        self.assertEqual(report["prepared_pilot_smoke_handoff"], smoke_handoff)
        self.assertEqual(report["scenario_table_generation"]["scenario_row_count"], 6)
        self.assertEqual(report["scenario_table_generation"]["file_count"], 5)
        self.assertEqual(report["scenario_table_generation"]["review_application_status"], "validated")
        self.assertEqual(report["command_plan_implications"][1]["status"], "ready")
        self.assertFalse(report["unblock_guidance"]["scenario_generation_should_remain_blocked"])

    def test_adjacent_candidate_bundle_reports_ready_pressure_with_positive_scenario_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            report = MODULE.build_report(
                candidate_metrics_manifest_path=ADJACENT_CANDIDATE_METRICS_PATH,
                candidate_review_manifest_path=ADJACENT_CANDIDATE_REVIEW_PATH,
                policy_path=POLICY_PATH,
                output_root=tmp_root / "scenario_pressure_adjacent",
                scenario_output_root=tmp_root / "scenario_table_adjacent",
            )
            with Path(report["scenario_table_generation"]["scenario_table_csv"]).open(encoding="utf-8", newline="") as handle:
                first_row = next(csv.DictReader(handle))

        self.assertEqual(report["scenario_pressure_status"], "ready")
        self.assertEqual(report["candidate_evidence"]["review_summary"]["candidate_count"], 1)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_row_count"], 3)
        self.assertEqual(report["scenario_generation_pressure"]["cardinality_pressure_summary"]["scenario_count"], 3)
        self.assertEqual(report["scenario_generation_pressure"]["cardinality_pressure_summary"]["expected_trajectory_count"], 180)
        self.assertEqual(
            report["scenario_generation_pressure"]["cardinality_pressure_summary"]["first_cardinality_growth_driver"],
            "block_family_count",
        )
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_file_count"], 5)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_csv_bytes"], 0)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_manifest_bytes"], 0)
        self.assertGreater(report["scenario_generation_pressure"]["scenario_table_total_bytes"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["candidate_expansion_counts"], [1, 2, 4, 8])
        self.assertEqual(
            [row["candidate_count"] for row in report["scenario_generation_pressure"]["candidate_expansion_ladder"]],
            [1, 2, 4, 8],
        )
        self.assertEqual(
            [row["scenario_row_count"] for row in report["scenario_generation_pressure"]["candidate_expansion_ladder"]],
            [3, 6, 12, 24],
        )
        self.assertTrue(
            all(
                row["scenario_table_csv_bytes"] > 0
                and row["scenario_table_manifest_bytes"] > 0
                and row["scenario_table_total_bytes"] >= row["scenario_table_csv_bytes"] + row["scenario_table_manifest_bytes"]
                and row["output_pressure_labels"]["target"] in {"local_smoke", "balfrin_postproc", "blocked"}
                for row in report["scenario_generation_pressure"]["candidate_expansion_ladder"]
            )
        )
        self.assertEqual(report["scenario_generation_pressure"]["candidate_expansion_ladder_summary"]["smallest_useful_candidate_count"], 1)
        self.assertEqual(report["scenario_generation_pressure"]["candidate_expansion_threshold"]["status"], "blocked_output_budget_exceeded")
        self.assertEqual(report["scenario_generation_pressure"]["candidate_expansion_threshold"]["threshold_candidate_count"], 4)
        self.assertEqual(
            report["scenario_generation_pressure"]["candidate_expansion_threshold"]["search_counts"],
            [1, 2, 4],
        )
        self.assertEqual(report["first_blocker"]["status"], "candidates_present")
        self.assertEqual(report["scenario_table_generation"]["review_application_status"], "validated")
        self.assertEqual(report["scenario_table_generation"]["accepted_candidate_count"], 1)
        smoke_handoff = report["scenario_table_generation"]["prepared_pilot_smoke_handoff"]
        self.assertEqual(smoke_handoff["smoke_status"], "ready")
        self.assertEqual(smoke_handoff["source_candidate_id"], "tschamut_adjacent_prau_mulins_candidate_v1")
        self.assertEqual(smoke_handoff["source_candidate_ids"], ["tschamut_adjacent_prau_mulins_candidate_v1"])
        self.assertEqual(smoke_handoff["scenario_table_id"], "scenario_table_adjacent")
        self.assertEqual(smoke_handoff["command_plan_target"], "second_site_aoi_to_prepared_pilot_dry_run")
        self.assertTrue(smoke_handoff["scenario_table_csv"].endswith("scenario_table.csv"))
        self.assertTrue(smoke_handoff["scenario_table_manifest_path"].endswith("reviewed_candidate_source_zone_freezer_manifest.json"))
        self.assertEqual(report["scenario_table_generation"]["scenario_row_count"], 3)
        self.assertEqual(report["scenario_table_generation"]["file_count"], 5)
        self.assertEqual(report["scenario_table_generation"]["scenario_table_manifest"]["conditional_weight_semantics"], "conditional_sampling_only")
        self.assertTrue(report["scenario_table_generation"]["scenario_table_manifest"]["conditional_weight_semantics"] == "conditional_sampling_only")
        self.assertGreater(
            report["scenario_table_generation"]["manifest_compaction"]["before"]["bytes"],
            report["scenario_table_generation"]["manifest_compaction"]["after"]["bytes"],
        )
        self.assertGreater(
            report["scenario_table_generation"]["manifest_compaction"]["before"]["field_count"],
            report["scenario_table_generation"]["manifest_compaction"]["after"]["field_count"],
        )
        self.assertEqual(
            [row["row_count"] for row in report["scenario_generation_pressure"]["scenario_family_cardinality"]],
            [1, 1, 1],
        )
        self.assertEqual(
            [row["row_count"] for row in report["scenario_generation_pressure"]["release_zone_cardinality"]],
            [3],
        )
        self.assertEqual(
            [row["row_count"] for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]],
            [3, 3, 3],
        )
        self.assertEqual(report["scenario_table_generation"]["row_payload_materialization"]["retained_in_report"], False)
        self.assertEqual(report["scenario_table_generation"]["scenario_table_rows"], [])
        self.assertEqual(float(first_row["conditional_weight"]), 3.0)
        self.assertEqual(first_row["annual_frequency_per_year"], "")
        self.assertEqual(first_row["scenario_probability"], "")

    def test_candidate_expansion_threshold_fail_closes_when_budget_search_overruns(self) -> None:
        candidate_review = {
            "candidate_release_zone_ids": ["candidate_a"],
            "candidate_review_rows": [
                {
                    "candidate_release_zone_id": "candidate_a",
                    "accepted": True,
                    "rejected": False,
                    "review_decision": "accepted",
                    "candidate_sensitivity_label": "workflow_generated",
                    "provenance_label": "workflow_generated",
                    "release_cell_count": 1,
                    "release_cell_ids": "candidate_a__cell_000",
                    "component_bbox_lv95_m": {
                        "xmin": 2600000.0,
                        "ymin": 1200000.0,
                        "xmax": 2600002.0,
                        "ymax": 1200002.0,
                    },
                }
            ],
            "review_application": {
                "validation_status": "validated",
                "accepted_candidate_ids": ["candidate_a"],
            },
            "review_summary": {
                "candidate_count": 1,
                "review_row_count": 1,
            },
        }
        budget_summary = {
            "current_pressure": {},
            "output_budget_gate": {
                "validation_output_budget": {"file_count": 1, "bytes": 1},
                "hazard_output_budget": {"file_count": 1, "bytes": 1},
            },
        }
        output_profile_policy = MODULE.AOI_PREVIEW.default_output_profile_policy()

        with mock.patch.object(
            MODULE.AOI_PREVIEW,
            "estimate_output_pressure",
            return_value={
                "projected_files": {"low": 1, "nominal": 1, "high": 1},
                "projected_bytes": {"low": 1, "nominal": 1, "high": 1},
                "estimated_runtime_seconds": {"low": 0.1, "nominal": 0.1, "high": 0.1},
            },
        ), mock.patch.object(MODULE.AOI_PREVIEW, "recommend_execution_target") as recommend:
            recommend.side_effect = [
                {
                    "target_status": "local_smoke",
                    "target": "local_smoke",
                    "blocked_reason": "",
                    "local_assessment": {"status": "safe"},
                    "balfrin_assessment": {"status": "not_required"},
                },
                {
                    "target_status": "local_smoke",
                    "target": "local_smoke",
                    "blocked_reason": "",
                    "local_assessment": {"status": "safe"},
                    "balfrin_assessment": {"status": "not_required"},
                },
                {
                    "target_status": MODULE.AOI_PREVIEW.BLOCKED_TARGET,
                    "target": MODULE.AOI_PREVIEW.BLOCKED_TARGET,
                    "blocked_reason": "projected files or bytes exceed the preview budget ceiling",
                    "local_assessment": {"status": "output_budget_exceeded"},
                    "balfrin_assessment": {"status": "output_budget_exceeded"},
                },
            ]
            threshold = MODULE.build_candidate_expansion_threshold(
                candidate_review=candidate_review,
                policy=MODULE.load_yaml(POLICY_PATH),
                trajectory_count=1,
                output_profile_policy=output_profile_policy,
                budget_summary=budget_summary,
            )

        self.assertEqual(threshold["status"], "blocked_output_budget_exceeded")
        self.assertEqual(threshold["blocking_label"], MODULE.AOI_PREVIEW.BLOCKED_OUTPUT_BUDGET_EXCEEDED)
        self.assertEqual(threshold["threshold_candidate_count"], 4)
        self.assertEqual(threshold["last_ready_candidate_count"], 2)
        self.assertEqual(threshold["search_counts"], [1, 2, 4])


if __name__ == "__main__":
    unittest.main()
