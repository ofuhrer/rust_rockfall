from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_scale_readiness_matrix.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_scale_readiness_matrix", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinScaleReadinessMatrixTests(unittest.TestCase):
    def test_build_report_composes_the_authoritative_baseline_matrix(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_scale_readiness_matrix_v1")
        self.assertEqual(report["matrix_status"], "blocked_reducer_budget")
        self.assertEqual(report["next_evidence_field"], "manifest_size_bytes")
        self.assertEqual(report["measured_tiers"], ["single_zone", "target_area"])
        self.assertEqual(report["blocked_tiers"], ["smallest_multi_zone"])
        self.assertEqual(report["projection_only_tiers"], ["projected_larger_aoi"])
        self.assertEqual(report["no_go_tiers"], ["projected_larger_aoi"])

        tiers = {row["tier_id"]: row for row in report["tiers"]}
        self.assertEqual(tiers["single_zone"]["classification"], "measured")
        self.assertEqual(tiers["single_zone"]["file_count"], 191)
        self.assertEqual(tiers["single_zone"]["bytes"], 267527120)
        self.assertEqual(tiers["single_zone"]["memory_peak_mb"], 409.22)
        self.assertEqual(tiers["single_zone"]["replayability_status"], "pass_hash_stable")

        self.assertEqual(tiers["target_area"]["classification"], "ready_for_exact_authorization")
        self.assertEqual(tiers["target_area"]["file_count"], 58)
        self.assertEqual(tiers["target_area"]["bytes"], 192350243)
        self.assertEqual(tiers["target_area"]["authorization_status"], "ready_for_authorization_review")
        self.assertEqual(tiers["target_area"]["next_evidence_field"], "memory_peak_mb")

        self.assertEqual(tiers["smallest_multi_zone"]["classification"], "blocked_reducer_budget")
        self.assertEqual(tiers["smallest_multi_zone"]["manifest_bytes"], 26057)
        self.assertEqual(tiers["smallest_multi_zone"]["reducer_sidecars"], 21)
        self.assertEqual(tiers["smallest_multi_zone"]["compact_manifest_bytes"], 17788)
        self.assertEqual(tiers["smallest_multi_zone"]["compact_reducer_sidecars"], 2)
        self.assertEqual(tiers["smallest_multi_zone"]["next_evidence_field"], "manifest_size_bytes")
        self.assertIn("manifest_size_bytes", tiers["smallest_multi_zone"]["blocker"])

        self.assertEqual(tiers["projected_larger_aoi"]["classification"], "no_go")
        self.assertEqual(tiers["projected_larger_aoi"]["file_count"], 442)
        self.assertEqual(tiers["projected_larger_aoi"]["bytes"], 102793652)
        self.assertEqual(tiers["projected_larger_aoi"]["runtime_seconds"], 463.84)
        self.assertEqual(tiers["projected_larger_aoi"]["memory_peak_mb"], 409.22)
        self.assertEqual(tiers["projected_larger_aoi"]["manifest_bytes"], 147566)
        self.assertEqual(tiers["projected_larger_aoi"]["planner_decision"], "no_go")

        text = MODULE.render_text_report(report)
        self.assertIn("Balfrin Scale Readiness Baseline Matrix", text)
        self.assertIn("single_zone", text)
        self.assertIn("smallest_multi_zone", text)
        self.assertIn("manifest_size_bytes", text)
        self.assertIn("projected_larger_aoi", text)

    def test_cli_emits_json_and_text_reports(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "text"])
        self.assertEqual(exit_code, 0)
        self.assertIn("matrix_status:", buffer.getvalue())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "json"])
        self.assertEqual(exit_code, 0)
        self.assertIn('"schema_version": "balfrin_scale_readiness_matrix_v1"', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
