from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_selected_zone_counts_generate_scratch_root_pressure_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            package = self._write_review_package(
                Path(tmp) / "selected_zone_review_package.yaml",
                self._build_review_package_payload(),
            )

            report = preview.build_report(
                review_package_paths=[package],
                trajectory_count=None,
                selected_zone_counts=(2, 4, 8, 12),
            )

        self.assertEqual(report["schema_version"], preview.SELECTED_ZONE_SCHEMA_VERSION)
        self.assertEqual(report["preview_mode"], "selected_zone_counts")
        self.assertEqual(report["preview_status"], "ready")
        self.assertEqual(report["selected_zone_counts"], [2, 4, 8, 12])
        self.assertEqual(report["reviewed_candidate_pool_count"], 12)
        self.assertEqual(report["largest_selected_zone_count"], 12)
        self.assertEqual([row["selected_zone_count"] for row in report["selected_zone_count_reports"]], [2, 4, 8, 12])
        self.assertEqual(
            report["selected_zone_count_reports"][0]["selected_candidate_ids"],
            [f"stable_candidate_{index:03d}" for index in range(1, 3)],
        )
        self.assertEqual(
            report["selected_zone_count_reports"][-1]["selected_candidate_ids"],
            [f"stable_candidate_{index:03d}" for index in range(1, 13)],
        )
        self.assertEqual(report["selected_zone_count_reports"][0]["scenario_cardinality"]["source_zone_count"], 2)
        self.assertEqual(report["selected_zone_count_reports"][0]["scenario_cardinality"]["row_count"], 6)
        self.assertEqual(report["selected_zone_count_reports"][-1]["scenario_cardinality"]["source_zone_count"], 12)
        self.assertEqual(report["selected_zone_count_reports"][-1]["scenario_cardinality"]["row_count"], 36)
        self.assertTrue(
            report["selected_zone_count_reports"][0]["output_root"].startswith("/tmp")
            or report["selected_zone_count_reports"][0]["output_root"].startswith("/private/tmp")
        )
        self.assertTrue(report["selected_zone_count_reports"][0]["manifest_bytes"] > 0)
        self.assertTrue(report["selected_zone_count_reports"][0]["csv_bytes"] > 0)
        self.assertTrue(report["selected_zone_count_reports"][0]["projected_files"]["nominal"] > 0)
        self.assertTrue(report["selected_zone_count_reports"][0]["projected_bytes"]["nominal"] > 0)
        self.assertTrue(report["selected_zone_count_reports"][0]["estimated_runtime_seconds"]["nominal"] > 0.0)
        self.assertEqual(report["selected_zone_count_reports"][-1]["seed_policy"], "fixed_integer_recorded_before_simulation")
        self.assertGreaterEqual(report["selected_zone_count_reports"][-1]["manifest_bytes"], report["selected_zone_count_reports"][0]["manifest_bytes"])
        self.assertEqual(report["execution_target"]["target"], report["largest_selected_zone_report"]["execution_target"]["target"])
        self.assertIn("Largest Selected Zone Count", preview.render_text_report(report))

    def test_projection_zone_counts_generate_companion_cost_ladder(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            package = self._write_review_package(
                Path(tmp) / "projection_zone_review_package.yaml",
                self._build_review_package_payload(),
            )

            with mock.patch.object(
                preview,
                "load_balfrin_scale_classification_surface",
                return_value=self._projection_classification_surface(),
            ), mock.patch.object(
                preview.FREEZER,
                "build_freezer_report",
                return_value=self._projection_freezer_report(),
            ), mock.patch.object(
                preview.LARGE_SCALE,
                "estimate",
                side_effect=self._projection_large_scale_estimate,
            ):
                report = preview.build_aoi_cost_projection_report(
                    review_package_paths=[package],
                    trajectory_count=None,
                    projection_zone_counts=(2, 4, 8, 12, 50, 100),
                )

        self.assertEqual(report["schema_version"], preview.COST_PROJECTION_SCHEMA_VERSION)
        self.assertEqual(report["preview_mode"], "aoi_cost_projection_counts")
        self.assertEqual(report["projection_status"], "ready")
        self.assertEqual(report["projection_zone_counts"], [2, 4, 8, 12, 50, 100])
        self.assertEqual(report["reviewed_candidate_pool_count"], 12)
        self.assertEqual(report["reference_block_family_count"], 3)
        self.assertEqual(report["projection_classification_summary"]["measured_tiers"], ["single_zone", "target_area"])
        self.assertEqual(report["projection_classification_summary"]["scratch_local"], [2, 4, 8, 12])
        self.assertEqual(report["projection_classification_summary"]["projection_only"], [50])
        self.assertEqual(report["projection_classification_summary"]["no_go"], [100])
        self.assertEqual(report["projection_classification_summary"]["plausible"], [2, 4])
        self.assertEqual(report["projection_classification_summary"]["blocked"], [8, 12, 50])
        self.assertEqual(report["projection_classification_summary"]["out_of_reach"], [100])
        self.assertEqual(report["planning_case_pressure_thresholds"]["planning_zone_counts"], [10, 50, 100])
        self.assertEqual(
            [row["planning_zone_count"] for row in report["planning_case_pressure_thresholds"]["planning_case_thresholds"]],
            [10, 50, 100],
        )
        self.assertEqual(report["planning_case_pressure_thresholds"]["planning_case_thresholds"][0]["scenario_cardinality"]["row_count"], 30)
        self.assertEqual(report["planning_case_pressure_thresholds"]["planning_case_thresholds"][-1]["scenario_cardinality"]["row_count"], 300)
        self.assertEqual(report["planning_case_pressure_thresholds"]["largest_planning_case"]["planning_zone_count"], 100)
        self.assertEqual(
            [row["projection_zone_count"] for row in report["projection_zone_count_reports"]],
            [2, 4, 8, 12, 50, 100],
        )
        self.assertEqual(
            [row["evidence_label"] for row in report["projection_zone_count_reports"]],
            ["scratch_local", "scratch_local", "scratch_local", "scratch_local", "projection_only", "no_go"],
        )
        self.assertEqual(
            [row["suitability_classification"] for row in report["projection_zone_count_reports"]],
            ["plausible", "plausible", "blocked", "blocked", "blocked", "out_of_reach"],
        )
        self.assertEqual(report["largest_projection_zone_count"], 100)
        self.assertEqual(report["largest_projection_zone_report"]["projection_zone_count"], 100)
        self.assertIn("AOI Cost Projection Preview", preview.render_text_report(report))
        self.assertIn("Projection Assumptions", preview.render_text_report(report))

    def _write_review_package(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def _build_review_package_payload(self) -> dict:
        accepted_ids = [f"stable_candidate_{index:03d}" for index in range(1, 13)]
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

    def _projection_classification_surface(self) -> dict:
        return {
            "measured_tiers": ["single_zone", "target_area"],
            "scratch_local_tiers": ["local_reducer_ladder"],
            "projection_only_tiers": ["projected_larger_aoi"],
            "no_go_tiers": ["projected_larger_aoi"],
            "summary": "Measured, scratch-local, projection-only, and no-go evidence remain separated.",
            "next_recommended_scaling_task": "TB-338",
            "evidence_label_definitions": {
                "measured_on_balfrin": "Preserved Balfrin run-root evidence with measured execution or output fields.",
                "scratch_local": "Local /tmp measurement or generated scratch evidence; useful for bottleneck discovery but not Balfrin evidence.",
                "projection_only": "Planner extrapolation from measured coefficients; not an executed scale tier.",
                "no_go": "Planner extrapolation that exceeds measured support.",
            },
        }

    def _projection_freezer_report(self) -> dict:
        return {
            "accepted_candidate_count": 12,
            "block_family_ids": [
                "policy_block_family_v1",
                "policy_block_family_v2",
                "policy_block_family_v3",
            ],
        }

    def _projection_large_scale_estimate(self, inputs):
        total_units = inputs.release_zone_count * inputs.trajectory_count * inputs.ensemble_size
        job_count = max(1, (total_units + 59) // 60)
        return mock.Mock(
            trajectory_chunks=max(1, min(2, inputs.release_zone_count)),
            reducer_chunks=max(1, min(2, total_units)),
            total_output_file_count=42 + max(1, min(2, inputs.release_zone_count)) + max(1, min(2, total_units)),
            output_bytes=inputs.release_zone_count * 100,
            chunk_counts={
                "trajectory_chunks": max(1, min(2, inputs.release_zone_count)),
                "reducer_chunks": max(1, min(2, total_units)),
            },
        )


if __name__ == "__main__":
    unittest.main()
