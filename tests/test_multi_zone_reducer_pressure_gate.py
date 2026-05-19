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
SCRIPT = ROOT / "scripts" / "validate_multi_zone_reducer_pressure_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_multi_zone_reducer_pressure_gate", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class MultiZoneReducerPressureGateTests(unittest.TestCase):
    def test_ready_profile_is_fixture_backed_and_reports_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "ready-probe"
            report = MODULE.build_report(
                materialize_root=probe_root,
                release_zone_count=8,
                reducer_chunk_count=2,
                reducer_workers=2,
            )

            self.assertEqual(report["schema_version"], "multi_zone_reducer_pressure_gate_v1")
            self.assertEqual(report["gate_status"], "fixture_backed_ready")
            self.assertEqual(report["threshold_provenance"], "fixture_backed")
            self.assertEqual(report["target_profile"]["output_family_mix"], list(MODULE.DEFAULT_OUTPUT_FAMILY_MIX))
            self.assertEqual(report["validation_output_inventory"]["validation_output_mode"], "rebuildable_reduced_output")
            self.assertIn("trajectory_csv", report["validation_output_inventory"]["replay_critical_output_families"])
            self.assertIn("diagnostics_json", report["validation_output_inventory"]["replay_critical_output_families"])
            self.assertIn("trajectory_chunk_manifest", report["validation_output_inventory"]["diagnostic_debug_output_families"])
            self.assertEqual(report["thresholds"]["warning"]["output_family_mix"], list(MODULE.DEFAULT_OUTPUT_FAMILY_MIX))
            self.assertEqual(report["thresholds"]["blocked"]["output_family_mix"], list(MODULE.DEFAULT_OUTPUT_FAMILY_MIX))
            self.assertEqual(report["thresholds"]["warning"]["release_zone_count"], 9)
            self.assertEqual(report["thresholds"]["blocked"]["release_zone_count"], 11)
            self.assertTrue(report["merge_order_check"]["merge_order_deterministic"])
            self.assertEqual(report["merge_order_check"]["status"], "ready")
            self.assertGreater(len(report["budget_checks"]), 0)
            self.assertGreater(len(report["family_count_checks"]), 0)
            self.assertGreater(len(report["family_byte_checks"]), 0)
            self.assertGreater(report["validation_output_inventory"]["family_budgets"]["trajectory_csv"]["file_count"], 0)
            self.assertGreater(report["validation_output_inventory"]["family_budgets"]["trajectory_csv"]["bytes"], 0)
            self.assertGreaterEqual(report["validation_output_inventory"]["family_budgets"]["trajectory_chunk_manifest"]["file_count"], 0)
            self.assertIn("deterministic merge order preserved", report["summary"])
            self.assertFalse(report["warning_reasons"])
            self.assertFalse(report["blocked_reasons"])

    def test_warning_profile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "warning-probe"
            report = MODULE.build_report(
                materialize_root=probe_root,
                release_zone_count=10,
                reducer_chunk_count=3,
                reducer_workers=2,
            )

            self.assertEqual(report["gate_status"], "fixture_backed_warning")
            self.assertIn("warning", report["summary"])
            self.assertGreater(len(report["warning_reasons"]), 0)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--materialize-root",
                        str(Path(tmpdir) / "warning-cli"),
                        "--release-zone-count",
                        "10",
                        "--reducer-chunk-count",
                        "3",
                        "--reducer-workers",
                        "2",
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 2)
            cli_report = json.loads(buffer.getvalue())
            self.assertEqual(cli_report["gate_status"], "fixture_backed_warning")

    def test_merge_order_regression_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "blocked-probe"
            MODULE.build_report(
                materialize_root=probe_root,
                release_zone_count=8,
                reducer_chunk_count=2,
                reducer_workers=2,
            )
            output_manifest_path = probe_root / "output" / "validation_multi_zone_reducer_pressure_manifest.json"
            payload = json.loads(output_manifest_path.read_text(encoding="utf-8"))
            payload["reducer_execution"]["merge_order"] = "completion_order"
            payload["reducer_execution"]["merge_order_independent"] = False
            output_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report = MODULE.build_report(probe_root=probe_root)

            self.assertEqual(report["gate_status"], "blocked_fixture_backed")
            self.assertEqual(report["merge_order_check"]["status"], "blocked")
            self.assertFalse(report["merge_order_check"]["merge_order_deterministic"])
            self.assertIn("merge_order_determinism", report["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
