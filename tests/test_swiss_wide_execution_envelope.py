#!/usr/bin/env python3
"""Tests for the Swiss-wide execution envelope projection helper."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


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
            measurement_notes=("synthetic coefficients for unit tests",),
        )

    def test_small_projection_stays_within_measured_support(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=1, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertEqual(report["runtime_seconds"]["nominal"], 12.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 120)
        self.assertEqual(report["file_count"]["nominal"], 6)
        self.assertEqual(report["no_go_labels"], [])

    def test_valley_scale_projection_matches_measured_pilot_shape(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertEqual(report["runtime_seconds"]["nominal"], 120.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 1200)
        self.assertEqual(report["file_count"]["nominal"], 60)
        self.assertEqual(report["no_go_labels"], [])

    def test_swiss_wide_projection_is_labeled_no_go(self) -> None:
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=26, release_zone_count=10, trajectory_count=6),
            coefficients=self._coefficients(),
        )

        self.assertEqual(report["projection_status"], "no_go_extrapolated_beyond_measured_evidence")
        self.assertEqual(report["job_count"], 26)
        self.assertEqual(report["jobs_per_aoi"], 1)
        self.assertIn("aoi_count_exceeds_measured_support", report["no_go_labels"])
        self.assertIn("total_job_count_exceeds_measured_single_job_support", report["no_go_labels"])
        self.assertEqual(report["runtime_seconds"]["nominal"], 3120.0)
        self.assertEqual(report["storage_bytes"]["nominal"], 31200)
        self.assertEqual(report["file_count"]["nominal"], 1560)

        text = estimator.render_text_report(report)
        self.assertIn("projection_status: no_go_extrapolated_beyond_measured_evidence", text)
        self.assertIn("aoi_count_exceeds_measured_support", text)

    def test_measured_loader_smoke_uses_real_summary_inputs(self) -> None:
        coefficients = estimator.load_measured_coefficients()
        report = estimator.build_report(
            estimator.ProjectionInputs(aoi_count=1, release_zone_count=10, trajectory_count=6),
            coefficients=coefficients,
        )

        self.assertEqual(report["projection_status"], "measured_within_support")
        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["no_go_labels"], [])
        self.assertIn("bounded_reducer_runtime_scaling", report["measurement_basis"]["source_commands"])
        self.assertGreater(len(coefficients.measurement_notes), 0)


if __name__ == "__main__":
    unittest.main()
