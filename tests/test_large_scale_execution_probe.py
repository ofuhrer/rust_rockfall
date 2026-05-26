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

SWISS_WIDE_SCRIPT_PATH = ROOT / "scripts" / "estimate_swiss_wide_execution_envelope.py"
SWISS_WIDE_SPEC = importlib.util.spec_from_file_location(
    "estimate_swiss_wide_execution_envelope_for_test",
    SWISS_WIDE_SCRIPT_PATH,
)
assert SWISS_WIDE_SPEC is not None
swiss_wide = importlib.util.module_from_spec(SWISS_WIDE_SPEC)
sys.modules["estimate_swiss_wide_execution_envelope_for_test"] = swiss_wide
assert SWISS_WIDE_SPEC.loader is not None
SWISS_WIDE_SPEC.loader.exec_module(swiss_wide)


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

    def test_balfrin_small_gate_reference_approximation(self) -> None:
        scalable_reference = estimator.estimate(
            self._make_input(
                release_zone_count=10,
                trajectory_count=6,
                trajectory_workers=2,
                reducer_workers=2,
                trajectory_chunks=2,
                reducer_chunks=2,
                threshold_count=2,
                profile="scalable_conditional",
                export_geotiff=True,
            )
        )

        provenance_reference = estimator.estimate(
            self._make_input(
                release_zone_count=10,
                trajectory_count=6,
                trajectory_workers=2,
                reducer_workers=2,
                trajectory_chunks=2,
                reducer_chunks=2,
                threshold_count=2,
                profile="provenance_audit",
                export_geotiff=True,
            )
        )

        # Balfrin small-gate clean evidence is 15,579,398 bytes and 46 files
        # for 2x2 scalable output controls.
        self.assertEqual(scalable_reference.total_output_file_count, 46)
        self.assertEqual(provenance_reference.total_output_file_count, 50)
        self.assertLess(abs(scalable_reference.output_bytes - 15_579_398), 100_000)
        self.assertGreater(provenance_reference.output_bytes, scalable_reference.output_bytes)

    def test_swiss_wide_phase_change_matrix_decomposes_current_deferred_state(self) -> None:
        requirements = swiss_wide.build_swiss_wide_national_requirements(
            projected_storage_bytes={"nominal": 1_000_000, "high": 2_000_000},
            projected_file_count={"nominal": 100, "high": 200},
            projected_job_count=26,
            projected_jobs_per_aoi=1,
        )
        readiness = swiss_wide.build_swiss_wide_phase_change_readiness(
            projection_status="no_go_extrapolated_beyond_measured_evidence",
            no_go_labels=["aoi_count_exceeds_measured_support"],
            distributed_execution_authorized=False,
            national_requirements=requirements,
        )

        self.assertEqual(readiness["schema_version"], "swiss_wide_phase_change_readiness_v1")
        self.assertEqual(readiness["phase_change_status"], "deferred")
        self.assertEqual(
            readiness["blocked_classes"],
            ["compute_feasible", "data_ready", "validation_ready", "operational_ready"],
        )
        self.assertEqual(readiness["first_blocker_class"], "compute_feasible")
        self.assertEqual(
            requirements["input_data_requirements"]["estimated_total_input_bytes"],
            requirements["input_data_requirements"]["estimated_dem_bytes"]
            + requirements["input_data_requirements"]["estimated_context_bytes"],
        )
        self.assertGreater(requirements["tiling_requirements"]["estimated_tile_count"], 1)
        self.assertTrue(requirements["execution_requirements"]["requires_distributed_orchestration"])

    def test_swiss_wide_phase_change_matrix_requires_all_classes_ready(self) -> None:
        requirements = swiss_wide.build_swiss_wide_national_requirements(
            projected_storage_bytes={"nominal": 1_000_000, "high": 2_000_000},
            projected_file_count={"nominal": 100, "high": 200},
            projected_job_count=1,
            projected_jobs_per_aoi=1,
            assumptions={
                "country_area_km2": 1,
                "target_cells_per_tile": 1_000_000,
                "default_aoi_count": 1,
                "release_zones_per_aoi": 1,
                "trajectories_per_release_zone": 1,
            },
        )
        almost_ready = swiss_wide.build_swiss_wide_phase_change_readiness(
            projection_status="measured_within_support",
            no_go_labels=[],
            distributed_execution_authorized=True,
            national_requirements=requirements,
            class_overrides={
                "data_ready": {"status": "ready", "first_missing_input": None},
                "validation_ready": {"status": "ready", "first_missing_input": None},
            },
        )
        ready = swiss_wide.build_swiss_wide_phase_change_readiness(
            projection_status="measured_within_support",
            no_go_labels=[],
            distributed_execution_authorized=True,
            national_requirements=requirements,
            class_overrides={
                "data_ready": {"status": "ready", "first_missing_input": None},
                "validation_ready": {"status": "ready", "first_missing_input": None},
                "operational_ready": {"status": "ready", "first_missing_input": None},
            },
        )

        self.assertEqual(almost_ready["phase_change_status"], "deferred")
        self.assertEqual(almost_ready["blocked_classes"], ["operational_ready"])
        self.assertEqual(ready["phase_change_status"], "ready_for_phase_change_review")
        self.assertEqual(ready["blocked_classes"], [])
        self.assertIsNone(ready["first_blocker_class"])


if __name__ == "__main__":
    unittest.main()
