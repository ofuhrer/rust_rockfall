from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import sys
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_multi_zone_reducer_pressure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_multi_zone_reducer_pressure", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class MultiZoneReducerPressureProbeTests(unittest.TestCase):
    def test_materialized_probe_is_deterministic_and_reports_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            first = MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=12,
                reducer_worker_count=2,
                reducer_chunk_count=4,
            )
            first_report = MODULE.build_report(probe_root)

            second = MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=12,
                reducer_worker_count=2,
                reducer_chunk_count=4,
            )
            second_report = MODULE.build_report(probe_root)

            self.assertEqual(first.release_zone_count, 12)
            self.assertEqual(first.reducer_chunk_count, 4)
            self.assertEqual(first.scenario_count, 12)
            self.assertEqual(second.release_zone_count, 12)
            self.assertEqual(first_report, second_report)
            self.assertEqual(first_report["probe_status"], "measured_scratch_root")
            self.assertEqual(first_report["release_zone_count"], 12)
            self.assertEqual(first_report["trajectory_chunk_count"], 12)
            self.assertEqual(first_report["reducer_chunk_count"], 4)
            self.assertEqual(first_report["merge_order"], "sorted_chunk_id")
            self.assertTrue(first_report["merge_order_independent"])
            self.assertTrue(first_report["multi_zone_dry_run_blocked"])
            self.assertEqual(first_report["bottleneck_labels"]["merge_order"]["label"], "sorted_chunk_id_deterministic")
            self.assertEqual(first_report["bottleneck_labels"]["probe_blocker"]["label"], "multi_zone_dry_run_blocked")
            self.assertGreater(first_report["manifest_size_bytes"], 0)
            self.assertGreater(first_report["root_file_count"], first_report["release_zone_count"])
            self.assertEqual(first_report["output_family_file_counts"]["trajectory_csv"], 12)
            self.assertEqual(first_report["output_family_file_counts"]["reducer_chunk_manifest"], 4)
            self.assertGreater(len(first_report["largest_output_families_by_bytes"]), 0)
            self.assertIn("kind", first_report["largest_output_families_by_bytes"][0])

    def test_cli_materialize_root_uses_requested_release_zone_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "custom-probe"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--materialize-root",
                        str(probe_root),
                        "--release-zone-count",
                        "8",
                        "--reducer-workers",
                        "2",
                        "--reducer-chunk-count",
                        "2",
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["release_zone_count"], 8)
            self.assertEqual(report["reducer_chunk_count"], 2)
            self.assertEqual(report["trajectory_chunk_count"], 8)
            self.assertEqual(report["probe_status"], "measured_scratch_root")

            command_plan = json.loads((probe_root / "command_plan.json").read_text(encoding="utf-8"))
            command = command_plan["commands"][0]["command"]
            self.assertIn("--release-zone-count", command)
            self.assertIn("8", command)


if __name__ == "__main__":
    unittest.main()
