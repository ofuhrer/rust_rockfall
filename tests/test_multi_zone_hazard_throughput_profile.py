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
            self.assertEqual(report["profile_status"], "profiled_scratch_root")
            self.assertEqual(report["fixture"]["release_zone_count"], 12)
            self.assertEqual(report["fixture"]["trajectory_file_count"], 12)
            self.assertEqual(report["fixture"]["impact_file_count"], 12)
            self.assertIn("fixture_fingerprint", report["fixture"])
            self.assertGreater(report["profile_scale"]["output_file_count"], 0)
            self.assertGreater(report["profile_scale"]["output_bytes"], 0)
            self.assertIn("read_seconds", report["timings"]["phase_seconds"])
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
            self.assertIn(report["bottleneck"]["label"], {"accumulation_seconds", "no_change", "report_render_seconds", "raster_write_seconds"})
            self.assertIn(report["recommendation"]["label"], {"accumulator_focus", "no_change", "report_render_focus", "raster_write_focus"})
            self.assertIn("reason", report["recommendation"])

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
