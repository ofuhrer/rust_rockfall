from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "measure_scenario_storage_output_tier_pressure.py"
SPEC = importlib.util.spec_from_file_location("measure_scenario_storage_output_tier_pressure", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScenarioStorageOutputTierPressureTests(unittest.TestCase):
    def test_default_report_measures_fixture_real_candidate_and_tiers(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "scenario_storage_output_tier_pressure_v1")
        self.assertEqual(report["measurement_status"], "ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertEqual(report["fixture_measurement"]["measurement_status"], "ready")
        self.assertEqual(report["fixture_measurement"]["scenario_row_count"], 3)
        self.assertGreater(report["fixture_measurement"]["scenario_bundle"]["total_bytes"], 0)
        self.assertEqual(report["real_aoi_candidate_measurement"]["measurement_status"], "ready")
        self.assertEqual(report["real_aoi_candidate_measurement"]["scenario_row_count"], 3)
        self.assertGreater(report["real_aoi_candidate_measurement"]["candidate_bundle"]["total_bytes"], 0)

        ladder = report["expanded_candidate_set_measurements"]
        self.assertEqual([row["candidate_repeat_count"] for row in ladder], [1, 3, 8])
        self.assertEqual([row["candidate_release_zone_record_count"] for row in ladder], [10, 30, 80])
        self.assertEqual([row["scenario_row_count"] for row in ladder], [100, 300, 800])
        self.assertEqual(
            ladder[0]["scenario_family_template_cardinality"],
            [
                {"group_id": "candidate_release_point_summary_v1", "row_count": 10},
                {"group_id": "policy_block_family_v1", "row_count": 90},
            ],
        )
        self.assertEqual(
            ladder[1]["source_zone_family_cardinality"],
            [
                {"group_id": "release_block_1", "row_count": 150},
                {"group_id": "release_block_2", "row_count": 60},
                {"group_id": "release_block_4", "row_count": 90},
            ],
        )
        self.assertEqual(
            ladder[2]["block_family_cardinality"],
            [
                {"group_id": "candidate_release_point_summary", "row_count": 80},
                {"group_id": "tschamut_public_block_large", "row_count": 240},
                {"group_id": "tschamut_public_block_medium", "row_count": 240},
                {"group_id": "tschamut_public_block_small", "row_count": 240},
            ],
        )
        self.assertLess(ladder[0]["csv_bytes"], ladder[1]["csv_bytes"])
        self.assertLess(ladder[1]["csv_bytes"], ladder[2]["csv_bytes"])
        self.assertLess(ladder[0]["manifest_bytes"], ladder[1]["manifest_bytes"])
        self.assertLess(ladder[1]["manifest_bytes"], ladder[2]["manifest_bytes"])
        self.assertEqual(
            report["next_balfrin_package_batching_rule"]["recommended_cap_candidate_repeat_count"],
            3,
        )
        self.assertEqual(
            report["next_balfrin_package_batching_rule"]["recommended_cap_candidate_release_zone_record_count"],
            30,
        )
        self.assertEqual(
            report["next_balfrin_package_batching_rule"]["recommended_cap_scenario_row_count"],
            300,
        )
        self.assertIn("3-repeat", report["next_balfrin_package_batching_rule"]["reason"])

        tiers = {row["tier_id"]: row for row in report["tier_comparison"]}
        self.assertEqual(set(tiers), {"minimal", "rebuildable_reduced", "gis", "research_full"})
        self.assertEqual(tiers["minimal"]["replay_suitability"], "insufficient_missing_trajectory_outputs")
        self.assertEqual(tiers["rebuildable_reduced"]["replay_suitability"], "sufficient")
        self.assertEqual(
            report["balfrin_demonstration_replay_recommendation"]["recommended_tier"],
            "rebuildable_reduced",
        )
        self.assertEqual(report["next_scale_bottleneck"]["bottleneck_id"], "gis_and_research_full_output_growth")
        self.assertIn("Scenario Storage", MODULE.render_text_report(report))

    def test_missing_real_candidate_inputs_block_candidate_without_blocking_fixture_tiers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            report = MODULE.build_report(
                candidate_metrics_manifest=tmp_root / "missing_metrics.json",
                candidate_review_manifest=tmp_root / "missing_review.json",
                policy_path=tmp_root / "missing_policy.yaml",
            )

        self.assertEqual(report["fixture_measurement"]["measurement_status"], "ready")
        self.assertEqual(
            report["real_aoi_candidate_measurement"]["measurement_status"],
            "blocked_missing_inputs",
        )
        self.assertEqual(
            report["next_scale_bottleneck"]["bottleneck_id"],
            "real_aoi_candidate_scenario_generation",
        )

    def test_recommendation_falls_back_when_reduced_root_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            reduced_root = Path(tmp) / "reduced"
            reduced_root.mkdir()
            (reduced_root / "validation_metrics.json").write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")

            report = MODULE.build_report(rebuildable_reduced_root=reduced_root)

        self.assertEqual(
            report["balfrin_demonstration_replay_recommendation"]["recommendation_status"],
            "fallback_required",
        )
        self.assertEqual(
            report["balfrin_demonstration_replay_recommendation"]["recommended_tier"],
            "research_full",
        )


if __name__ == "__main__":
    unittest.main()
