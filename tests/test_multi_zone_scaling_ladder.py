from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_multi_zone_scaling_ladder.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_multi_zone_scaling_ladder", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class MultiZoneScalingLadderTests(unittest.TestCase):
    def test_materialized_fixture_is_deterministic_for_the_same_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rung_root = Path(tmpdir) / "zones_01"
            first = MODULE.materialize_ladder_fixture_root(
                rung_root,
                release_zone_count=1,
                reducer_worker_count=1,
                reducer_chunk_count=1,
            )
            first_manifest = json.loads((rung_root / "input" / "multi_zone_scaling_ladder_fixture_manifest.json").read_text(encoding="utf-8"))
            first_command_plan = json.loads((rung_root / "command_plan.json").read_text(encoding="utf-8"))

            second = MODULE.materialize_ladder_fixture_root(
                rung_root,
                release_zone_count=1,
                reducer_worker_count=1,
                reducer_chunk_count=1,
            )
            second_manifest = json.loads((rung_root / "input" / "multi_zone_scaling_ladder_fixture_manifest.json").read_text(encoding="utf-8"))
            second_command_plan = json.loads((rung_root / "command_plan.json").read_text(encoding="utf-8"))

            self.assertEqual(first.fixture_fingerprint, second.fixture_fingerprint)
            self.assertEqual(first_manifest["fixture_fingerprint"], second_manifest["fixture_fingerprint"])
            self.assertEqual(first_command_plan, second_command_plan)
            self.assertEqual(first.release_zone_count, 1)
            self.assertEqual(first.scenario_count, 1)
            self.assertEqual(first.reducer_chunk_count, 1)

    def test_budget_validation_classifies_accepted_and_blocked_rungs(self) -> None:
        thresholds = MODULE.handoff.build_output_budget_acceptance_thresholds()
        accepted = MODULE.handoff.validate_output_budget_acceptance(
            projection={
                "release_zone_count": 2,
                "reducer_chunk_count": 2,
                "reducer_worker_count": 2,
                "manifest_size_bytes": 9000,
                "output_file_count": 18,
                "output_byte_count": 12000,
                "reducer_manifest_file_count": 2,
                "reducer_manifest_bytes": 250,
                "sidecar_file_count": 9,
                "sidecar_byte_count": 900,
                "output_family_file_counts": {
                    "trajectory_csv": 2,
                    "deposition_csv": 2,
                    "impact_events_csv": 2,
                    "trajectory_merge_state": 1,
                    "reducer_merge_state": 1,
                },
                "replay_critical_retained_output_families": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
                "projection_file_hashes": {
                    "probe_manifest_sha256": "a" * 64,
                    "command_plan_sha256": "b" * 64,
                    "output_manifest_sha256": "c" * 64,
                },
            },
            thresholds=thresholds,
        )
        blocked = MODULE.handoff.validate_output_budget_acceptance(
            projection={
                "release_zone_count": 8,
                "reducer_chunk_count": 2,
                "reducer_worker_count": 2,
                "manifest_size_bytes": 15000,
                "output_file_count": 29,
                "output_byte_count": 22000,
                "reducer_manifest_file_count": 2,
                "reducer_manifest_bytes": 300,
                "sidecar_file_count": 10,
                "sidecar_byte_count": 1200,
                "output_family_file_counts": {
                    "trajectory_csv": 8,
                    "deposition_csv": 8,
                    "impact_events_csv": 8,
                    "trajectory_merge_state": 1,
                    "reducer_merge_state": 1,
                },
                "replay_critical_retained_output_families": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
                "projection_file_hashes": {
                    "probe_manifest_sha256": "d" * 64,
                    "command_plan_sha256": "e" * 64,
                    "output_manifest_sha256": "f" * 64,
                },
            },
            thresholds=thresholds,
        )

        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(accepted["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertEqual(blocked["status"], "blocked_threshold_exceeded")
        self.assertEqual(blocked["threshold_profile_id"], "next_larger_four_zone_review_only_probe")
        self.assertIn("output_file_count", blocked["exceeded_thresholds"])
        self.assertTrue(blocked["replay_critical_excesses"] or blocked["compressible_excesses"])


if __name__ == "__main__":
    unittest.main()
