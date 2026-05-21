from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py"
PREVIEW_SCRIPT_PATH = ROOT / "scripts" / "preview_aoi_scenario_cost_estimate.py"
POLICY_PATH = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
RELEASE_POINTS_PATH = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"

from scripts.lib.workflow_validation import (
    build_release_candidate_physical_meaning_firewall,
    build_release_zone_provenance_intake,
    validate_release_candidate_physical_meaning_firewall,
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(SCRIPT_PATH, "generate_candidate_source_zone_scenarios")
PREVIEW_MODULE = _load_module(PREVIEW_SCRIPT_PATH, "preview_aoi_scenario_cost_estimate")


class CandidateSourceZoneScenarioStressTests(unittest.TestCase):
    def test_deterministic_release_candidates_generate_a_large_manifest_rich_table(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            output_root = Path(tmp) / "validation/private/tschamut_public_pilot/candidate_source_zone_stress_v1"

            first = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=RELEASE_POINTS_PATH,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )
            second = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=RELEASE_POINTS_PATH,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )

            manifest_path = Path(first["output_paths"]["scenario_table_manifest_json"])
            csv_path = Path(first["output_paths"]["scenario_table_csv"])
            report_path = Path(first["output_paths"]["stress_report_json"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            csv_text = csv_path.read_text(encoding="utf-8")
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(first["generated_scenario_table_rows"], second["generated_scenario_table_rows"])
        self.assertEqual(first["scenario_table_manifest"], second["scenario_table_manifest"])
        self.assertEqual(first["storage_measurements"], second["storage_measurements"])
        self.assertEqual(first["first_scaling_bottleneck"], second["first_scaling_bottleneck"])
        self.assertEqual(first["tb_183_planning_input"], second["tb_183_planning_input"])
        self.assertEqual(first["stress_test_status"], "ready")
        self.assertEqual(first["candidate_repeat_count"], 3)
        self.assertEqual(first["candidate_release_zone_record_count"], 30)
        self.assertEqual(first["scenario_row_count"], 120)
        self.assertTrue(first["tb_183_planning_input"]["ready_for_tb_183"])
        self.assertEqual(first["tb_183_planning_input"]["status"], "ready")
        self.assertEqual(first["release_candidate_physical_meaning_firewall"]["release_candidate_provenance_state"], "workflow_generated")
        self.assertEqual(first["release_candidate_physical_meaning_firewall"]["firewall_status"], "workflow_generated")
        self.assertEqual(first["release_candidate_physical_meaning_firewall"]["release_candidate_provenance_state_counts"]["workflow_generated"], 30)
        self.assertEqual(first["release_candidate_physical_meaning_firewall"]["scenario_row_count"], 120)
        self.assertEqual(first["release_candidate_physical_meaning_firewall"]["sampling_weight_semantics"], "conditional_sampling_only")
        self.assertEqual(first["scenario_table_manifest"]["release_candidate_physical_meaning_firewall"]["release_candidate_provenance_state"], "workflow_generated")
        self.assertEqual(first["scenario_table_manifest"]["row_summaries"][0]["release_candidate_provenance_state"], "workflow_generated")
        self.assertEqual(first["forest_realization_plan"]["plan_status"], "forest_context_deferred_missing_public_context")
        self.assertFalse(first["forest_realization_plan"]["silent_omission"])
        self.assertEqual(first["forest_realization_plan"]["physical_model_behavior"], "unchanged_no_tree_impact_physics")
        self.assertGreater(first["storage_measurements"]["csv_bytes"], 0)
        self.assertGreater(first["storage_measurements"]["manifest_bytes"], first["storage_measurements"]["csv_bytes"])
        self.assertGreater(first["runtime_measurements"]["total_seconds"], 0.0)
        self.assertEqual(first["first_scaling_bottleneck"]["name"], "manifest_size")

        self.assertEqual(manifest["candidate_release_zone_record_count"], 30)
        self.assertEqual(manifest["scenario_row_count"], 120)
        self.assertEqual(manifest["candidate_repeat_count"], 3)
        self.assertEqual(manifest["candidate_cardinality"][0]["row_count"], 4)
        self.assertEqual(manifest["candidate_cardinality"][0]["template_count"], 2)
        self.assertEqual(manifest["source_zone_family_cardinality"], [
            {"group_id": "release_block_1", "row_count": 60},
            {"group_id": "release_block_2", "row_count": 24},
            {"group_id": "release_block_4", "row_count": 36},
        ])
        self.assertEqual(manifest["scenario_family_template_cardinality"], [
            {"group_id": "candidate_release_point_summary_v1", "row_count": 30},
            {"group_id": "policy_block_family_v1", "row_count": 90},
        ])
        self.assertEqual(manifest["row_ids"][0], "v004__repeat_000__candidate_release_point_summary")
        self.assertTrue(csv_text.startswith("scenario_id,"))
        self.assertIn("release_candidate_physical_meaning_firewall", report_text)
        self.assertIn("workflow_generated", report_text)
        self.assertIn("candidate_release_point_summary_v1", report_text)
        self.assertIn("policy_block_family_v1", report_text)

    def test_selected_zone_prefixes_stay_deterministic_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            review_package = self._write_review_package(
                tmp_root / "review_package.yaml",
                self._build_review_package_payload(),
            )
            accepted_ids = [f"stable_candidate_{index:03d}" for index in range(1, 13)]

            first_runs = []
            second_runs = []
            previous_manifest_bytes = 0
            previous_csv_bytes = 0
            for count in (2, 4, 8, 12):
                output_root = tmp_root / f"selected_zone_{count:02d}"
                first = MODULE.build_freezer_report(
                    review_package_path=review_package,
                    accepted_candidate_ids=accepted_ids[:count],
                    output_root=output_root,
                    trajectory_count=6,
                    seed=MODULE.DEFAULT_FREEZER_SEED + count,
                )
                second = MODULE.build_freezer_report(
                    review_package_path=review_package,
                    accepted_candidate_ids=accepted_ids[:count],
                    output_root=output_root,
                    trajectory_count=6,
                    seed=MODULE.DEFAULT_FREEZER_SEED + count,
                )
                first_runs.append(first)
                second_runs.append(second)

                self.assertEqual(first["accepted_candidate_ids"], accepted_ids[:count])
                self.assertEqual(first["accepted_candidate_count"], count)
                self.assertEqual(first["scenario_row_count"], count * 3)
                self.assertEqual(first["block_family_ids"], [
                    "reviewed_block_family_small",
                    "reviewed_block_family_medium",
                    "reviewed_block_family_large",
                ])
                self.assertEqual(first["seed_policy"], "fixed_integer_recorded_before_simulation")
                self.assertEqual(first["release_row_count"], count)
                self.assertEqual(len(first["output_paths"]), 5)
                csv_bytes = Path(first["output_paths"]["scenario_table"]).stat().st_size
                manifest_bytes = Path(first["output_paths"]["manifest"]).stat().st_size
                self.assertTrue(Path(first["output_paths"]["scenario_table"]).exists())
                self.assertTrue(Path(first["output_paths"]["manifest"]).exists())
                self.assertGreater(csv_bytes, previous_csv_bytes)
                self.assertGreater(manifest_bytes, previous_manifest_bytes)
                self.assertLess(csv_bytes, 20_000)
                self.assertLess(manifest_bytes, 80_000)

                previous_csv_bytes = csv_bytes
                previous_manifest_bytes = manifest_bytes

            self.assertEqual(first_runs, second_runs)

    def test_selected_zone_pressure_ladder_captures_10_50_100_candidate_sizes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            review_package = self._write_review_package(
                tmp_root / "review_package.yaml",
                self._build_review_package_payload(candidate_count=100),
            )

            report = PREVIEW_MODULE.build_selected_zone_pressure_report(
                review_package_path=review_package,
                selected_zone_counts=(10, 50, 100),
                trajectory_count=6,
                output_root=tmp_root / "selected_zone_pressure",
            )
            self.assertEqual(report["preview_status"], "ready")
            self.assertEqual(report["selected_zone_counts"], [10, 50, 100])
            self.assertEqual(report["largest_selected_zone_count"], 100)
            self.assertEqual(report["conditional_weight_summary"]["conditional_weight_semantics"], "conditional_sampling_only")
            self.assertEqual(report["conditional_weight_summary"]["conditional_weight_total"], 10.0)
            self.assertEqual(report["conditional_weight_summary"]["block_family_count"], 3)
            self.assertEqual(report["conditional_weight_summary"]["block_family_ids"], [
                "reviewed_block_family_small",
                "reviewed_block_family_medium",
                "reviewed_block_family_large",
            ])

            counts = [row["selected_zone_count"] for row in report["selected_zone_count_reports"]]
            self.assertEqual(counts, [10, 50, 100])
            previous_manifest_bytes = 0
            previous_csv_bytes = 0
            for row in report["selected_zone_count_reports"]:
                self.assertEqual(row["scenario_cardinality"]["source_zone_count"], row["selected_zone_count"])
                self.assertEqual(row["scenario_cardinality"]["scenario_family_count"], 3)
                self.assertEqual(row["scenario_cardinality"]["row_count"], row["selected_zone_count"] * 3)
                self.assertEqual(row["conditional_weight_summary"]["conditional_weight_semantics"], "conditional_sampling_only")
                self.assertEqual(row["conditional_weight_summary"]["conditional_weight_total"], 10.0)
                csv_path = Path(row["output_paths"]["scenario_table"])
                manifest_path = Path(row["output_paths"]["manifest"])
                self.assertTrue(csv_path.exists())
                self.assertTrue(manifest_path.exists())
                self.assertGreater(csv_path.stat().st_size, previous_csv_bytes)
                self.assertGreater(manifest_path.stat().st_size, previous_manifest_bytes)
                self.assertEqual(row["expected_output_file_count"], 5)
                previous_csv_bytes = csv_path.stat().st_size
                previous_manifest_bytes = manifest_path.stat().st_size

    def test_selected_zone_counts_fail_closed_when_requested_count_exceeds_reviewed_pool(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            review_package = self._write_review_package(
                tmp_root / "review_package.yaml",
                self._build_review_package_payload(candidate_count=12),
            )

            report = PREVIEW_MODULE.build_selected_zone_pressure_report(
                review_package_path=review_package,
                selected_zone_counts=(10, 50, 100),
                trajectory_count=6,
                output_root=tmp_root / "selected_zone_pressure",
            )

        self.assertEqual(report["preview_status"], "blocked_missing_reviewed_candidates")
        self.assertIn("selected-zone count exceeds reviewed candidate pool", report["blocked_reason"])

    def _build_review_package_payload(self, candidate_count: int = 12) -> dict[str, object]:
        accepted_ids = [f"stable_candidate_{index:03d}" for index in range(1, candidate_count + 1)]
        return {
            "review_package_status": "review_applied",
            "source_zone_id": "stable_review_zone",
            "candidate_site_id": "stable_preview_site",
            "candidate_site_name": "Stable Preview Site",
            "trajectory_count_target": 6,
            "review_application": {
                "validation_status": "validated",
                "accepted_candidate_ids": accepted_ids,
            },
            "candidate_review_rows": [
                {
                    "candidate_release_zone_id": candidate_id,
                    "accepted": True,
                    "rejected": False,
                    "review_decision": "accepted",
                    "candidate_sensitivity_label": "reviewed",
                    "provenance_label": "workflow_generated",
                    "release_cell_ids": f"stable_review_zone_release_cell_{index:03d}",
                    "release_cell_count": 1,
                    "component_bbox_lv95_m": {
                        "xmin": 2793000.0 + (index * 2.0),
                        "ymin": 1180200.0 + (index * 2.0),
                        "xmax": 2793001.0 + (index * 2.0),
                        "ymax": 1180201.0 + (index * 2.0),
                    },
                }
                for index, candidate_id in enumerate(accepted_ids, start=1)
            ],
        }

    def _write_review_package(self, path: Path, payload: dict[str, object]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def test_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            output_root = Path(tmp) / "validation/private/tschamut_public_pilot/candidate_source_zone_stress_v1"
            missing_release_points = Path(tmp) / "missing_release_points.csv"

            report = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=missing_release_points,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )

        self.assertEqual(report["stress_test_status"], "blocked_missing_inputs")
        self.assertIn("missing_release_points.csv", " ".join(report["scenario_table_manifest"]["missing_inputs"]))
        self.assertEqual(report["candidate_release_zone_record_count"], 0)
        self.assertEqual(report["scenario_row_count"], 0)
        self.assertEqual(report["tb_183_planning_input"]["status"], "blocked_missing_inputs")

    def test_field_supported_provenance_stays_conditional_only(self) -> None:
        field_supported_intake = build_release_zone_provenance_intake(
            {
                "release_zone_provenance_state": "field_supported",
                "provenance_note": "field-supported release-zone intake",
                "provenance_source": "field notebook",
            }
        )
        policy = MODULE.load_yaml(POLICY_PATH)
        candidate_records = MODULE.build_candidate_release_zone_records(
            release_points=[
                {
                    "trajectory_id": "field_point_001",
                    "mass_kg": "12.0",
                    "radius_m": "0.4",
                    "block_id": "field",
                }
            ],
            release_points_path=RELEASE_POINTS_PATH,
            candidate_repeat_count=1,
            source_zone_id="field_supported_source_zone",
            release_zone_provenance_intake=field_supported_intake,
        )
        rows = MODULE.build_rows(
            candidate_records=candidate_records,
            block_scenarios=[
                {
                    "block_scenario_id": "field_block_small",
                    "block_size_class": "field_small",
                    "block_shape_class": "sphere",
                    "block_radius_m": 0.12,
                    "block_mass_kg": 18.0,
                    "sampling_weight": 2.5,
                }
            ],
            template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            policy=policy,
        )
        MODULE.normalize_row_shares(rows)
        firewall = MODULE.build_release_candidate_firewall(candidate_records=candidate_records, rows=rows)

        self.assertEqual(candidate_records[0]["release_zone_provenance_intake"]["release_zone_provenance_state"], "field_supported")
        self.assertEqual(candidate_records[0]["release_candidate_provenance_state"], "field_supported")
        self.assertEqual(rows[0]["release_candidate_provenance_state"], "field_supported")
        self.assertEqual(firewall["release_candidate_provenance_state"], "field_supported")
        self.assertEqual(firewall["sampling_weight_semantics"], "conditional_sampling_only")
        self.assertEqual(
            firewall["sampling_weight_boundary"],
            "not occurrence probability, physical probability, annual frequency, return period, or risk",
        )
        self.assertTrue(all(row["release_probability"] == "" for row in rows))
        self.assertTrue(all(row["scenario_probability"] == "" for row in rows))
        self.assertTrue(all(row["annual_frequency_per_year"] == "" for row in rows))
        self.assertTrue(all(row["time_horizon_years"] == "" for row in rows))
        self.assertTrue(all(row["normalized_sampling_share"] is not None for row in rows))
        validate_release_candidate_physical_meaning_firewall(
            firewall,
            error_cls=MODULE.CandidateSourceZoneScenarioStressError,
        )

    def test_release_candidate_firewall_labels_supported_states_and_blocks_overclaims(self) -> None:
        firewall = build_release_candidate_physical_meaning_firewall(
            [
                {
                    "candidate_release_zone_record_id": "workflow",
                    "candidate_release_zone_record_kind": "workflow_generated",
                    "workflow_generated": True,
                    "field_supported": False,
                    "blocked_missing_provenance": False,
                    "provenance_note": "workflow-generated candidate",
                },
                {
                    "candidate_release_zone_record_id": "field",
                    "candidate_release_zone_record_kind": "field_supported",
                    "workflow_generated": False,
                    "field_supported": True,
                    "blocked_missing_provenance": False,
                    "provenance_note": "field-supported candidate",
                },
                {
                    "candidate_release_zone_record_id": "mixed",
                    "candidate_release_zone_record_kind": "mixed_provenance",
                    "workflow_generated": True,
                    "field_supported": True,
                    "blocked_missing_provenance": False,
                    "provenance_note": "mixed provenance candidate",
                },
                {
                    "candidate_release_zone_record_id": "blocked",
                    "candidate_release_zone_record_kind": "blocked_missing_provenance",
                    "workflow_generated": False,
                    "field_supported": False,
                    "blocked_missing_provenance": True,
                    "provenance_note": "missing provenance",
                },
            ]
        )
        self.assertEqual(firewall["release_candidate_provenance_state"], "blocked_missing_provenance")
        self.assertEqual(
            firewall["release_candidate_provenance_state_counts"],
            {
                "workflow_generated": 1,
                "field_supported": 1,
                "mixed_provenance": 1,
                "blocked_missing_provenance": 1,
            },
        )
        self.assertEqual(firewall["release_candidate_provenance_profile"][0]["provenance_state"], "workflow_generated")
        self.assertEqual(firewall["release_candidate_provenance_profile"][1]["provenance_state"], "field_supported")
        self.assertEqual(firewall["release_candidate_provenance_profile"][2]["provenance_state"], "mixed_provenance")
        self.assertEqual(firewall["release_candidate_provenance_profile"][3]["provenance_state"], "blocked_missing_provenance")
        validate_release_candidate_physical_meaning_firewall(
            firewall,
            error_cls=MODULE.CandidateSourceZoneScenarioStressError,
        )

        overclaim = dict(firewall)
        overclaim["sampling_weight_boundary"] = "occurrence probability"
        with self.assertRaises(MODULE.CandidateSourceZoneScenarioStressError):
            validate_release_candidate_physical_meaning_firewall(
                overclaim,
                error_cls=MODULE.CandidateSourceZoneScenarioStressError,
            )

    def test_review_decision_blocks_field_supported_overclaims_but_keeps_unreviewed_workflow_generated(self) -> None:
        unreviewed_intake = build_release_zone_provenance_intake(
            {
                "review_decision": "needs_field_review",
                "provenance_note": "candidate still under review",
                "provenance_source": "terrain review package",
            }
        )
        overclaimed_intake = build_release_zone_provenance_intake(
            {
                "review_decision": "needs_field_review",
                "release_zone_provenance_state": "field_supported",
                "provenance_note": "unreviewed candidate overclaimed as field-supported",
                "provenance_source": "terrain review package",
            }
        )

        self.assertEqual(unreviewed_intake["review_decision"], "needs_field_review")
        self.assertEqual(unreviewed_intake["release_zone_provenance_state"], "workflow_generated")
        self.assertFalse(unreviewed_intake["field_supported"])
        self.assertEqual(overclaimed_intake["review_decision"], "needs_field_review")
        self.assertEqual(overclaimed_intake["release_zone_provenance_state"], "blocked_missing_provenance")
        self.assertFalse(overclaimed_intake["field_supported"])

        policy = MODULE.load_yaml(POLICY_PATH)
        candidate_records = MODULE.build_candidate_release_zone_records(
            release_points=[
                {
                    "trajectory_id": "review_point_001",
                    "mass_kg": "11.0",
                    "radius_m": "0.3",
                    "block_id": "review",
                }
            ],
            release_points_path=RELEASE_POINTS_PATH,
            candidate_repeat_count=1,
            source_zone_id="reviewed_source_zone",
            release_zone_provenance_intake=overclaimed_intake,
        )
        rows = MODULE.build_rows(
            candidate_records=candidate_records,
            block_scenarios=[
                {
                    "block_scenario_id": "review_block_small",
                    "block_size_class": "review_small",
                    "block_shape_class": "sphere",
                    "block_radius_m": 0.12,
                    "block_mass_kg": 18.0,
                    "sampling_weight": 1.0,
                }
            ],
            template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            policy=policy,
        )

        self.assertEqual(candidate_records[0]["candidate_release_zone_record_kind"], "blocked_missing_provenance")
        self.assertEqual(rows[0]["release_candidate_provenance_state"], "blocked_missing_provenance")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
