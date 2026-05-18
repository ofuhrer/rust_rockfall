from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_multi_zone_hazard_throughput_profile.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_multi_zone_hazard_throughput_profile", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


def read_layer(path: Path) -> dict[tuple[int, int], float]:
    values: dict[tuple[int, int], float] = {}
    with path.open(newline="") as file:
        import csv

        for row in csv.DictReader(file):
            values[(int(row["row"]), int(row["col"]))] = float(row["value"])
    return values


class MultiZoneHazardThroughputProfileTests(unittest.TestCase):
    def test_materialized_fixture_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            first = MODULE.materialize_fixture_root(profile_root)
            first_manifest = json.loads(first.fixture_manifest_path.read_text(encoding="utf-8"))
            first_fingerprint = first_manifest["fixture_fingerprint"]

            second = MODULE.materialize_fixture_root(profile_root)
            second_manifest = json.loads(second.fixture_manifest_path.read_text(encoding="utf-8"))
            second_fingerprint = second_manifest["fixture_fingerprint"]

            self.assertEqual(first.release_zone_count, 12)
            self.assertEqual(first.trajectory_file_count, 12)
            self.assertEqual(first.impact_file_count, 12)
            self.assertEqual(first.deposition_row_count, 12)
            self.assertEqual(first.impact_row_count, 24)
            self.assertEqual(first_fingerprint, second_fingerprint)
            self.assertEqual(first_manifest["release_zone_count"], 12)
            self.assertEqual(first_manifest["scenario_count"], 12)
            self.assertEqual(second_manifest["trajectory_file_count"], 12)

    def test_profile_report_schema_and_pressure_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            MODULE.materialize_fixture_root(profile_root)
            report = MODULE.build_report(profile_root)

            self.assertEqual(report["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(report["profile_id"], MODULE.DEFAULT_PROFILE_ID)
            self.assertEqual(report["profile_status"], "profiled_scratch_root")
            self.assertEqual(report["fixture"]["release_zone_count"], 12)
            self.assertEqual(report["fixture"]["trajectory_file_count"], 12)
            self.assertEqual(report["fixture"]["impact_file_count"], 12)
            self.assertTrue(report["fixture"]["measure_bounds_discovery"])
            self.assertFalse(report["fixture"]["render_report"])
            self.assertIn("fixture_fingerprint", report["fixture"])
            self.assertIn("auto", report["runs"])
            self.assertIn("explicit", report["runs"])
            self.assertGreater(report["profile_scale"]["output_file_count"], 0)
            self.assertGreater(report["profile_scale"]["output_bytes"], 0)
            self.assertIn("trajectory_read_seconds", report["timings"]["phase_seconds"])
            self.assertIn("bounds_discovery_seconds", report["timings"]["phase_seconds"])
            self.assertGreater(report["runs"]["auto"]["timings"]["phase_seconds"]["bounds_discovery_seconds"], 0.0)
            self.assertEqual(report["runs"]["explicit"]["timings"]["phase_seconds"]["bounds_discovery_seconds"], 0.0)
            self.assertIn("accumulation_seconds", report["timings"]["phase_seconds"])
            self.assertIn("reducer_merge_seconds", report["timings"]["phase_seconds"])
            self.assertIn("manifest_seconds", report["timings"]["phase_seconds"])
            self.assertIn("raster_write_seconds", report["timings"]["phase_seconds"])
            self.assertIn("report_render_seconds", report["timings"]["phase_seconds"])
            self.assertEqual(report["cog_gis_pressure"]["status"], "not_applicable")
            self.assertIn("layer_family_bytes", report["output_pressure"])
            self.assertIn("file_family_bytes", report["output_pressure"])
            self.assertIn("manifest_family_bytes", report["output_pressure"])
            self.assertGreater(len(report["output_pressure"]["largest_layer_families"]), 0)
            self.assertGreater(len(report["output_pressure"]["largest_file_families"]), 0)
            self.assertGreater(len(report["output_pressure"]["largest_manifest_families"]), 0)
            self.assertEqual(report["bottleneck"]["label"], "accumulation_seconds")
            self.assertEqual(report["recommendation"]["status"], "bounded_optimization")
            self.assertEqual(report["recommendation"]["label"], "trajectory_accumulator_batching")
            self.assertIn("proposal", report["recommendation"])
            self.assertIn("required_tests", report["recommendation"]["proposal"])
            self.assertIn("reason", report["recommendation"])

    def test_smoke_profile_remains_routine_and_uses_explicit_run_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            MODULE.materialize_fixture_root(profile_root, profile_spec=MODULE.PROFILE_SPECS[MODULE.SMOKE_PROFILE_ID])
            report = MODULE.build_report(profile_root)

            self.assertEqual(report["profile_id"], MODULE.SMOKE_PROFILE_ID)
            self.assertEqual(report["recommendation"]["status"], "bounded_optimization")
            self.assertEqual(report["fixture"]["release_zone_count"], 2)
            self.assertEqual(set(report["runs"]), {"explicit"})
            self.assertEqual(report["timings"]["phase_seconds"]["bounds_discovery_seconds"], 0.0)

    def test_smoke_profile_guardrail_preserves_outputs_and_manifest_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            fixture = MODULE.materialize_fixture_root(profile_root, profile_spec=MODULE.PROFILE_SPECS[MODULE.SMOKE_PROFILE_ID])
            report = MODULE.build_report(profile_root)
            profiled_dir = profile_root / "output" / "explicit" / "hazard"
            control_dir = profile_root / "control"

            self.assertEqual(
                MODULE.hazard.main_with_args(
                    [
                        "--case",
                        str(fixture.case_path),
                        "--output-dir",
                        str(control_dir),
                        "--grid-xmin",
                        str(MODULE.DEFAULT_GRID_XMIN),
                        "--grid-ymin",
                        str(MODULE.DEFAULT_GRID_YMIN),
                        "--grid-ncols",
                        str(MODULE.DEFAULT_GRID_NCOLS),
                        "--grid-nrows",
                        str(MODULE.DEFAULT_GRID_NROWS),
                        "--grid-cell-size",
                        str(MODULE.DEFAULT_GRID_CELLSIZE),
                        "--conditional-curve-export",
                        "summary-only",
                        "--grid-csv-export",
                        "none",
                        "--trajectory-workers",
                        "1",
                        "--reducer-workers",
                        str(MODULE.PROFILE_SPECS[MODULE.SMOKE_PROFILE_ID].reducer_workers),
                        "--diagnostics",
                        str(fixture.diagnostics_path),
                        "--ensemble-trajectories-dir",
                        str(fixture.trajectory_dir),
                        "--deposition",
                        str(fixture.deposition_path),
                        "--ensemble-impact-events-dir",
                        str(fixture.impact_event_dir),
                        "--export-geotiff",
                        "--no-plots",
                    ]
                ),
                0,
            )

            profiled_manifest = json.loads((profiled_dir / "multi_zone_hazard_profile_manifest.json").read_text())
            control_manifest = json.loads((control_dir / "multi_zone_hazard_profile_manifest.json").read_text())

            def semantic_manifest_view(manifest: dict[str, object]) -> dict[str, object]:
                conditional_execution = manifest["conditional_execution"]
                return {
                    "case_id": manifest["case_id"],
                    "grid": manifest["grid"],
                    "hazard_statistics": manifest["hazard_statistics"],
                    "layer_semantics": manifest["layer_semantics"],
                    "layers": manifest["layers"],
                    "cellwise_layers": [
                        {
                            "key": entry["key"],
                            "layer_name": entry["layer_name"],
                            "thresholds": entry["thresholds"],
                            "format": entry.get("format"),
                            "units": entry.get("units"),
                        }
                        for entry in manifest["cellwise_layers"]
                    ],
                    "conditional_execution": {
                        "schema_version": conditional_execution["schema_version"],
                        "grid_cell_count": conditional_execution["grid_cell_count"],
                        "conditional_curve_export": {
                            "mode": conditional_execution["conditional_curve_export"]["mode"],
                            "csv_table_written": conditional_execution["conditional_curve_export"]["csv_table_written"],
                            "row_count": conditional_execution["conditional_curve_export"]["row_count"],
                            "table_suppressed_for_output_budget": conditional_execution["conditional_curve_export"][
                                "table_suppressed_for_output_budget"
                            ],
                        },
                        "reducer": {
                            "mode": conditional_execution["reducer"]["mode"],
                            "worker_count": conditional_execution["reducer"]["worker_count"],
                            "chunk_count": conditional_execution["reducer"]["chunk_count"],
                            "chunk_manifest_count": conditional_execution["reducer"].get("chunk_manifest_count", 0),
                            "merge_order": conditional_execution["reducer"]["merge_order"],
                            "merge_order_independent": conditional_execution["reducer"]["merge_order_independent"],
                            "chunk_ids": conditional_execution["reducer"]["chunk_ids"],
                        },
                        "curve_contract": conditional_execution["curve_contract"],
                        "output_budget": conditional_execution["output_budget"],
                    },
                }

            self.assertEqual(semantic_manifest_view(profiled_manifest), semantic_manifest_view(control_manifest))
            def hazard_layer_signatures(manifest: dict[str, object]) -> list[tuple[object, object, object, object]]:
                return sorted(
                    (
                        output["kind"],
                        output["format"],
                        output.get("layer_name"),
                        output["sha256"],
                    )
                    for output in manifest["outputs"]
                    if output["kind"] == "hazard_layer"
                )

            self.assertEqual(hazard_layer_signatures(profiled_manifest), hazard_layer_signatures(control_manifest))
            self.assertGreaterEqual(report["runs"]["explicit"]["hazard_manifest"]["performance"]["accumulation_seconds"], 0.0)

    def test_cli_materialize_root_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--materialize-root",
                        str(profile_root),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["profile_status"], "profiled_scratch_root")
            self.assertEqual(report["schema_version"], MODULE.SCHEMA_VERSION)

    def test_missing_fixture_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_root = Path(tmpdir) / "profile"
            with self.assertRaises(MODULE.MultiZoneHazardThroughputProfileError) as ctx:
                MODULE.build_report(profile_root)

            self.assertIn("missing fixture inputs", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
