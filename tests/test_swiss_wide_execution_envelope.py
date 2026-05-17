#!/usr/bin/env python3
"""Tests for the Swiss-wide execution envelope projection helper."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "estimate_swiss_wide_execution_envelope.py"
SPEC = importlib.util.spec_from_file_location("estimate_swiss_wide_execution_envelope", SCRIPT_PATH)
assert SPEC is not None
estimator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = estimator
assert SPEC.loader is not None
SPEC.loader.exec_module(estimator)


class SwissWideExecutionEnvelopeTests(unittest.TestCase):
    def _coefficients(self) -> estimator.MeasuredCoefficients:
        return estimator.MeasuredCoefficients(
            measured_aoi_count=1,
            measured_release_zone_count=10,
            measured_trajectory_count=6,
            measured_units_per_job=60,
            runtime_seconds_per_unit_low=1.0,
            runtime_seconds_per_unit_nominal=2.0,
            runtime_seconds_per_unit_high=4.0,
            storage_bytes_per_unit_low=10.0,
            storage_bytes_per_unit_nominal=20.0,
            storage_bytes_per_unit_high=40.0,
            file_count_per_unit_low=0.5,
            file_count_per_unit_nominal=1.0,
            file_count_per_unit_high=2.0,
            memory_peak_mb_low=3.5,
            memory_peak_mb_nominal=4.0,
            memory_peak_mb_high=4.5,
            measurement_notes=("synthetic coefficients for unit tests",),
            bounded_probe_recommendation_status="deferred_pending_authorization",
        )

    def test_small_projection_stays_within_measured_support(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=1, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["measurement_status"], "measured_existing_artifacts")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertEqual(report["runtime_seconds"]["nominal"], 12.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 120)
        self.assertEqual(report["file_count"]["nominal"], 6)
        self.assertEqual(report["memory_peak_mb"]["nominal"], 4.0)
        self.assertEqual(report["no_go_labels"], [])

    def test_valley_scale_projection_matches_measured_pilot_shape(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["measurement_status"], "measured_existing_artifacts")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertEqual(report["runtime_seconds"]["nominal"], 120.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 1200)
        self.assertEqual(report["file_count"]["nominal"], 60)
        self.assertEqual(report["memory_peak_mb"]["nominal"], 4.0)
        self.assertEqual(report["no_go_labels"], [])

    def test_swiss_wide_projection_is_labeled_no_go(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=26, release_zone_count=10, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "no_go_extrapolated_beyond_measured_evidence")
        self.assertEqual(report["measurement_status"], "measured_existing_artifacts")
        self.assertEqual(report["job_count"], 26)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertIn("aoi_count_exceeds_measured_support", report["no_go_labels"])
        self.assertIn("total_job_count_exceeds_measured_single_job_support", report["no_go_labels"])
        self.assertEqual(report["planning_labels"]["no_go"], "no_go_extrapolated_beyond_measured_evidence")
        self.assertEqual(report["planning_labels"]["defer"], "defer_scale_up_authorized_false")
        self.assertEqual(
            report["planning_labels"]["allowed_next_probe"],
            "allowed_next_probe_measured_existing_artifacts",
        )
        self.assertEqual(report["measurement_basis"]["bounded_probe_recommendation_status"], "deferred_pending_authorization")
        self.assertEqual(report["runtime_seconds"]["nominal"], 3120.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 31200)
        self.assertEqual(report["file_count"]["nominal"], 1560)
        self.assertEqual(report["memory_peak_mb"]["nominal"], 4.0)

        text = estimator.render_text_report(report)
        self.assertIn("projection_status: no_go_extrapolated_beyond_measured_evidence", text)
        self.assertIn("measurement_status: measured_existing_artifacts", text)
        self.assertIn("aoi_count_exceeds_measured_support", text)
        self.assertIn("planning_labels:", text)
        self.assertIn("allowed_next_probe: allowed_next_probe_measured_existing_artifacts", text)
        self.assertIn("bounded_probe_recommendation_status: deferred_pending_authorization", text)
        self.assertIn("balfrin_demo_run_root:", text)

    def test_measured_loader_smoke_uses_real_summary_inputs(self) -> None:
        coefficients = estimator.load_measured_coefficients()
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6),
            coefficients=coefficients,
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["measurement_status"], "measured_existing_artifacts")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["no_go_labels"], [])
        self.assertIn("bounded_reducer_runtime_scaling", report["measurement_basis"]["source_commands"])
        self.assertIn("memory frontier is anchored", report["measurement_basis"]["measurement_notes"][2])
        self.assertGreater(len(coefficients.measurement_notes), 0)
        self.assertEqual(
            report["measurement_basis"]["balfrin_demo_run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3",
        )
        self.assertEqual(report["measurement_basis"]["bounded_probe_recommendation_status"], "deferred_pending_authorization")
        self.assertEqual(report["planning_labels"]["no_go"], "no_go_not_triggered")
        self.assertEqual(
            report["planning_labels"]["allowed_next_probe"],
            "allowed_next_probe_measured_existing_artifacts",
        )

    def test_missing_measured_evidence_returns_blocked_report(self) -> None:
        estimator.load_measured_coefficients.cache_clear()
        try:
            with mock.patch.object(
                estimator.RUNTIME_SCALING,
                "build_report",
                return_value={"artifacts_measured": []},
            ):
                report = estimator.build_report_from_available_evidence(
                    estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6)
                )
        finally:
            estimator.load_measured_coefficients.cache_clear()

        self.assertEqual(report["measurement_status"], "blocked_missing_inputs")
        self.assertEqual(report["projection_status"], "blocked_missing_inputs")
        self.assertIsNone(report["job_count"])
        self.assertIsNone(report["jobs_per_aoi"])
        self.assertEqual(report["no_go_labels"], [])
        self.assertEqual(report["planning_labels"]["no_go"], "no_go_not_triggered")
        self.assertEqual(
            report["planning_labels"]["allowed_next_probe"],
            "allowed_next_probe_blocked_missing_inputs",
        )
        self.assertEqual(report["planning_case_summary"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["planning_cases"], [])
        self.assertEqual(report["bottleneck_labels"]["validation_output"]["label"], "blocked_missing_inputs")
        self.assertIsNone(report["measurement_basis"]["bounded_probe_recommendation_status"])
        self.assertIn("measured reduced-output artifact target_rebuildable_reduced is missing", report["blocked_reason"])
        self.assertIsNone(report["runtime_seconds"]["nominal"])
        self.assertIn("measured Balfrin evidence was unavailable", report["measurement_basis"]["measurement_notes"][0])
        self.assertEqual(
            report["measurement_basis"]["balfrin_demo_run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3",
        )

    def test_canonical_planning_cases_cover_all_scale_labels(self) -> None:
        with mock.patch.object(estimator.SINGLE_JOB, "build_summary", return_value=self._single_job_summary()), mock.patch.object(
            estimator.FEASIBILITY,
            "build_report",
            return_value=self._feasibility_report(),
        ), mock.patch.object(
            estimator,
            "load_canonical_bundle_report",
            return_value=self._canonical_bundle_report(),
        ), mock.patch.object(
            estimator,
            "load_target_area_probe_report",
            return_value=self._target_area_probe_report(),
        ), mock.patch.object(
            estimator,
            "load_generated_scenario_table_evidence",
            return_value=self._generated_scenario_table_report(),
        ):
            report = estimator.build_report(
                estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6),
                coefficients=self._coefficients(),
            )

        self.assertEqual(report["planning_case_summary"]["case_count"], 4)
        self.assertEqual(report["planning_case_summary"]["next_probe"], ["10_zone"])
        self.assertEqual(report["planning_case_summary"]["defer"], ["100_zone"])
        self.assertEqual(report["planning_case_summary"]["no_go"], ["regional", "swiss_wide"])
        self.assertEqual([case["case_id"] for case in report["planning_cases"]], ["10_zone", "100_zone", "regional", "swiss_wide"])

        ten_zone_case = report["planning_cases"][0]
        hundred_zone_case = report["planning_cases"][1]
        regional_case = report["planning_cases"][2]
        swiss_wide_case = report["planning_cases"][3]

        self.assertEqual(ten_zone_case["planning_decision"], "next_probe")
        self.assertEqual(ten_zone_case["planning_labels"]["allowed_next_probe"], "allowed_next_probe_measured_existing_artifacts")
        self.assertEqual(hundred_zone_case["planning_decision"], "defer")
        self.assertEqual(hundred_zone_case["planning_labels"]["defer"], "defer_scale_up_authorized_false")
        self.assertEqual(regional_case["planning_decision"], "no_go")
        self.assertEqual(regional_case["planning_labels"]["no_go"], "no_go_extrapolated_beyond_measured_evidence")
        self.assertEqual(swiss_wide_case["planning_decision"], "no_go")
        self.assertEqual(swiss_wide_case["bottleneck_labels"]["scheduler_practicality"]["label"], "scheduler_practicality_requires_authorization")
        self.assertEqual(swiss_wide_case["bottleneck_labels"]["manifest_count"]["label"], "manifest_size")

        text = estimator.render_text_report(report)
        self.assertIn("planning_case_summary:", text)
        self.assertIn("planning_cases:", text)
        self.assertIn("case_id: 10_zone", text)
        self.assertIn("planning_decision: next_probe", text)
        self.assertIn("scheduler_practicality_bottleneck: scheduler_practicality_requires_authorization", text)

    def _single_job_summary(self) -> dict[str, object]:
        return {
            "decision": "defer",
            "final_classification": "defer",
            "single_job_sufficient_for_next_step": True,
            "current_pressure": "validation_output_size",
            "output_size_evidence": {
                "current_gap_output_bytes": 267527120,
                "current_gap_output_file_count": 191,
            },
        }

    def _feasibility_report(self) -> dict[str, object]:
        return {
            "measured_evidence": {
                "rebuildable_reduced_output_bytes": 1884291,
                "rebuildable_reduced_output_file_count": 6,
            }
        }

    def _canonical_bundle_report(self) -> dict[str, object]:
        return {
            "bundle_status": "measured_existing_artifacts",
            "bundle_summary": {"status": "measured_existing_artifacts", "section_counts": {"measured": 6}},
        }

    def _target_area_probe_report(self) -> dict[str, object]:
        return {
            "report_status": "measured_existing_artifacts",
            "wall_time_seconds": 347.825,
            "memory_peak_mb": 409.22,
            "validation_output": {"file_count": 2004, "bytes": 571131205},
            "hazard_output": {"file_count": 54, "bytes": 75423367},
        }

    def _generated_scenario_table_report(self) -> dict[str, object]:
        return {
            "stress_test_status": "ready",
            "candidate_repeat_count": 3,
            "candidate_release_zone_record_count": 30,
            "scenario_row_count": 120,
            "scenario_table_manifest": {"table_status": "ready"},
            "first_scaling_bottleneck": {"name": "manifest_size"},
        }


if __name__ == "__main__":
    unittest.main()
