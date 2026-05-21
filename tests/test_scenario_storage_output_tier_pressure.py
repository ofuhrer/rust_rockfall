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
