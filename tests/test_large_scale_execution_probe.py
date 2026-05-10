#!/usr/bin/env python3
"""Tests for large-scale execution projection model."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "estimate_large_scale_execution.py"
MODULE_NAME = "estimate_large_scale_execution"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
assert SPEC is not None
estimator = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = estimator
assert SPEC.loader is not None
SPEC.loader.exec_module(estimator)


class EstimateLargeScaleExecutionProbeTests(unittest.TestCase):
    def _make_input(self, **kwargs):
        return estimator.EstimateInputs(
            release_zone_count=kwargs.get("release_zone_count", 10),
            ensemble_size=kwargs.get("ensemble_size", 1),
            trajectory_count=kwargs.get("trajectory_count", 6),
            grid_rows=kwargs.get("grid_rows", 304),
            grid_cols=kwargs.get("grid_cols", 300),
            trajectory_workers=kwargs.get("trajectory_workers", 2),
            reducer_workers=kwargs.get("reducer_workers", 2),
            trajectory_chunks=kwargs.get("trajectory_chunks"),
            reducer_chunks=kwargs.get("reducer_chunks"),
            threshold_count=kwargs.get("threshold_count", 2),
            profile=kwargs.get("profile", "scalable_conditional"),
            export_geotiff=kwargs.get("export_geotiff", True),
        )

    def test_profile_scaling_behavior(self) -> None:
        scalable = estimator.estimate(
            self._make_input(
                profile="scalable_conditional",
                export_geotiff=True,
            )
        )
        full = estimator.estimate(
            self._make_input(
                profile="full_debug",
                export_geotiff=True,
            )
        )
        provenance = estimator.estimate(
            self._make_input(profile="provenance_audit", export_geotiff=True)
        )

        self.assertGreater(full.output_bytes, scalable.output_bytes)
        self.assertGreater(full.file_counts_by_class.get("grid_csv", 0), 0)
        self.assertEqual(scalable.file_counts_by_class.get("grid_csv", 0), 0)
        self.assertIn("provenance_manifests", provenance.file_counts_by_class)

    def test_chunk_count_growth_increases_artifacts(self) -> None:
        small_chunks = estimator.estimate(
            self._make_input(
                trajectory_chunks=2,
                reducer_chunks=2,
                trajectory_workers=8,
                reducer_workers=8,
                export_geotiff=True,
            )
        )
        larger_chunks = estimator.estimate(
            self._make_input(
                trajectory_chunks=4,
                reducer_chunks=4,
                trajectory_workers=8,
                reducer_workers=8,
                export_geotiff=True,
            )
        )

        self.assertGreater(larger_chunks.total_output_file_count, small_chunks.total_output_file_count)
        self.assertGreater(
            larger_chunks.file_counts_by_class["trajectory_artifacts"],
            small_chunks.file_counts_by_class["trajectory_artifacts"],
        )
        self.assertGreater(
            larger_chunks.output_bytes_by_class["chunk_management"],
            small_chunks.output_bytes_by_class["chunk_management"],
        )

    def test_deterministic_estimate_for_fixed_inputs(self) -> None:
        first = estimator.estimate(
            self._make_input(
                release_zone_count=12,
                ensemble_size=2,
                trajectory_count=5,
                grid_rows=400,
                grid_cols=450,
                trajectory_workers=3,
                reducer_workers=3,
                threshold_count=3,
                profile="scalable_conditional",
                export_geotiff=False,
            )
        )
        second = estimator.estimate(
            self._make_input(
                release_zone_count=12,
                ensemble_size=2,
                trajectory_count=5,
                grid_rows=400,
                grid_cols=450,
                trajectory_workers=3,
                reducer_workers=3,
                threshold_count=3,
                profile="scalable_conditional",
                export_geotiff=False,
            )
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
