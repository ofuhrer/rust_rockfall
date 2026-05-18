from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py"
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
