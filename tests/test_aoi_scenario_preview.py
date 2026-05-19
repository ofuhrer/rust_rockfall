from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "preview_aoi_scenario_cost_estimate.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "aoi_scenario_preview"
SPEC = importlib.util.spec_from_file_location("preview_aoi_scenario_cost_estimate", SCRIPT_PATH)
assert SPEC is not None
preview = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(preview)


class AoiScenarioPreviewTests(unittest.TestCase):
    def test_tiny_reviewed_fixture_is_ready_for_local_smoke(self) -> None:
        report = preview.build_report(
            review_package_paths=[FIXTURE_DIR / "tiny_review_package.yaml"],
            trajectory_count=None,
        )

        self.assertEqual(report["preview_status"], "ready")
        self.assertEqual(report["execution_target"]["target"], "local_smoke")
        self.assertEqual(report["scenario_cardinality"]["source_zone_count"], 1)
        self.assertEqual(report["scenario_cardinality"]["row_count"], 3)
        self.assertEqual(report["rows"][0]["output_profile_choice"], "scalable_default")
        self.assertGreater(report["projected_files"]["nominal"], 0)
        self.assertGreater(report["projected_bytes"]["nominal"], 0)
        self.assertGreater(report["estimated_runtime_seconds"]["nominal"], 0.0)

    def test_multi_zone_fixture_aggregates_rows_and_supports_balfrin_postproc(self) -> None:
        report = preview.build_report(
            review_package_paths=[
                FIXTURE_DIR / "multi_zone_review_package_a.yaml",
                FIXTURE_DIR / "multi_zone_review_package_b.yaml",
            ],
            trajectory_count=None,
        )

        self.assertEqual(report["preview_status"], "ready")
        self.assertEqual(report["scenario_cardinality"]["source_zone_count"], 2)
        self.assertEqual(report["scenario_cardinality"]["row_count"], 6)
        self.assertEqual(sorted({row["source_zone_id"] for row in report["rows"]}), ["multi_review_zone_a", "multi_review_zone_b"])
        self.assertEqual(report["rows"][0]["recommended_execution_target"], report["execution_target"]["target"])
        self.assertIn(report["execution_target"]["target"], {"local_smoke", "balfrin_postproc"})

    def test_missing_reviewed_candidates_block_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            package = self._write_review_package(
                Path(tmp) / "missing_reviewed_candidates.yaml",
                {
                    "review_package_status": "review_applied",
                    "source_zone_id": "missing_review_zone",
                    "candidate_site_id": "missing_site",
                    "review_application": {
                        "validation_status": "validated",
                        "accepted_candidate_ids": [],
                    },
                    "candidate_review_rows": [],
                },
            )

            report = preview.build_report(review_package_paths=[package], trajectory_count=None)

        self.assertEqual(report["preview_status"], preview.BLOCKED_MISSING_REVIEWED_CANDIDATES)
        self.assertIn("missing reviewed candidates", report["blocked_reason"])
        self.assertEqual(report["execution_target"]["target"], "blocked")

    def test_unknown_trajectory_budget_block_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            package = self._write_review_package(
                Path(tmp) / "unknown_trajectory_budget.yaml",
                {
                    "review_package_status": "review_applied",
                    "source_zone_id": "unknown_trajectory_zone",
                    "candidate_site_id": "unknown_site",
                    "review_application": {
                        "validation_status": "validated",
                        "accepted_candidate_ids": ["unknown_candidate_001"],
                    },
                    "candidate_review_rows": [
                        {
                            "candidate_release_zone_id": "unknown_candidate_001",
                            "accepted": True,
                            "rejected": False,
                            "review_decision": "accepted",
                            "release_cell_ids": "unknown_trajectory_zone_release_cell_001",
                            "release_cell_count": 1,
                            "component_bbox_lv95_m": {
                                "xmin": 2793300.0,
                                "ymin": 1180500.0,
                                "xmax": 2793301.0,
                                "ymax": 1180501.0,
                            },
                        }
                    ],
                },
            )

            report = preview.build_report(review_package_paths=[package], trajectory_count=None)

        self.assertEqual(report["preview_status"], preview.BLOCKED_UNKNOWN_TRAJECTORY_BUDGET)
        self.assertIn("trajectory budget", report["blocked_reason"])

    def test_unsupported_profile_blocks_closed(self) -> None:
        report = preview.build_report(
            review_package_paths=[FIXTURE_DIR / "tiny_review_package.yaml"],
            trajectory_count=1,
            output_profile_policy=OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export="full",
                grid_csv_export="full",
                no_plots=False,
                explicit_debug_override=False,
                label="unsupported_profile_fixture",
            ),
        )

        self.assertEqual(report["preview_status"], preview.BLOCKED_UNSUPPORTED_PROFILE)
        self.assertIn("unsupported output profile", report["blocked_reason"])

    def test_budget_exceeded_blocks_closed(self) -> None:
        report = preview.build_report(
            review_package_paths=[FIXTURE_DIR / "tiny_review_package.yaml"],
            trajectory_count=100000,
        )

        self.assertEqual(report["preview_status"], preview.BLOCKED_OUTPUT_BUDGET_EXCEEDED)
        self.assertEqual(report["execution_target"]["target"], "blocked")
        self.assertIn("budget", report["blocked_reason"])

    def _write_review_package(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
