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
SCRIPT = ROOT / "scripts" / "hazard_accumulation_benchmark.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hazard_accumulation_benchmark", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class HazardAccumulationBenchmarkTests(unittest.TestCase):
    def test_benchmark_report_includes_baseline_control_and_acceptance_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_root = Path(tmpdir) / "bench"
            report = MODULE.build_report(benchmark_root)

            self.assertEqual(report["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(report["benchmark_status"], "baseline_recorded")
            self.assertEqual(report["baseline_profile_id"], "smallest_multi_zone_baseline")
            self.assertEqual(report["profile_root_count"], 3)
            self.assertIn("single_zone_control", report["profiles"])
            self.assertIn("smallest_multi_zone_baseline", report["profiles"])
            self.assertIn("output_heavy_guardrail", report["profiles"])
            self.assertEqual(report["fixtures"]["single_zone_control"]["release_zone_count"], 1)
            self.assertEqual(report["fixtures"]["smallest_multi_zone_baseline"]["release_zone_count"], 2)
            self.assertEqual(report["fixtures"]["output_heavy_guardrail"]["release_zone_count"], 12)
            self.assertEqual(report["no_op_control_result"]["role"], "no_op_control")
            self.assertEqual(report["baseline_result"]["role"], "performance_baseline")
            self.assertEqual(report["acceptance_criteria"]["schema_version"], MODULE.ACCEPTANCE_SCHEMA_VERSION)
            self.assertAlmostEqual(report["acceptance_criteria"]["speedup_floor_fraction"], 0.9)
            self.assertAlmostEqual(report["acceptance_criteria"]["memory_growth_ceiling_fraction"], 0.1)
            self.assertFalse(report["acceptance_criteria"]["claim_boundaries"]["operational_claims_allowed"])
            self.assertTrue(report["comparison_contract"]["before_required"])
            self.assertTrue(report["comparison_contract"]["after_required"])
            self.assertTrue(report["determinism"]["baseline_replay_match"])
            self.assertTrue(report["determinism"]["layer_signature_match"])
            self.assertEqual(
                report["baseline_result"]["stable_manifest_sha256"],
                report["baseline_replay_result"]["stable_manifest_sha256"],
            )
            self.assertGreaterEqual(
                report["output_heavy_result"]["profile_scale"]["output_file_count"],
                report["baseline_result"]["profile_scale"]["output_file_count"],
            )

    def test_benchmark_report_stable_manifest_view_is_deterministic_on_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_root = Path(tmpdir) / "bench"
            report = MODULE.build_report(benchmark_root)

            baseline = report["baseline_result"]
            replay = report["baseline_replay_result"]
            self.assertEqual(baseline["stable_manifest_view"], replay["stable_manifest_view"])
            self.assertEqual(baseline["stable_manifest_sha256"], replay["stable_manifest_sha256"])
            self.assertEqual(
                [entry["sha256"] for entry in baseline["stable_manifest_view"]["outputs"]],
                [entry["sha256"] for entry in replay["stable_manifest_view"]["outputs"]],
            )

    def test_cli_materialize_root_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_root = Path(tmpdir) / "bench"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--benchmark-root",
                        str(benchmark_root),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["benchmark_status"], "baseline_recorded")
            self.assertIn("acceptance_criteria", report)
            self.assertIn("baseline_result", report)


if __name__ == "__main__":
    unittest.main()
