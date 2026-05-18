from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_probe_preservation_gate.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_probe_preservation_gate", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinProbePreservationGateTests(unittest.TestCase):
    def test_complete_run_root_passes_the_preservation_gate(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        report = MODULE.build_report(run_root=run_root)

        self.assertEqual(report["schema_version"], "balfrin_probe_preservation_gate_v1")
        self.assertEqual(report["gate_status"], "ready_for_demonstration_evidence")
        self.assertTrue(report["future_live_run_would_satisfy_evidence_preservation_contract"])
        self.assertEqual(report["run_root_status"], "measured_run_root")
        self.assertEqual(report["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(report["metrics_completion_outcome"], "recovered")
        self.assertEqual(report["metrics_contract_status"], "complete")
        self.assertEqual(report["required_run_root_entries_status"], "complete")
        self.assertEqual(report["missing_run_root_entries"], [])
        self.assertEqual(report["output_family_summaries"]["status"], "sufficient")
        self.assertEqual(report["output_family_summaries"]["measured_family_counts"]["map_package_manifest"], 1)
        self.assertEqual(report["output_family_summaries"]["measured_family_counts"]["pilot_gis_package_manifest"], 1)
        self.assertEqual(report["output_family_summaries"]["measured_family_counts"]["trajectory_chunk_manifest"], 2)
        self.assertEqual(report["output_family_summaries"]["measured_family_counts"]["reducer_chunk_manifest"], 2)
        self.assertEqual(report["spatial_gis_artifact_paths"]["status"], "declared")
        self.assertGreaterEqual(len(report["spatial_gis_artifact_paths"]["declared_artifacts"]), 4)
        self.assertIn("JobID", report["slurm_accounting_contract"]["required_fields"])
        self.assertIn("MaxRSS", report["slurm_accounting_contract"]["required_fields"])
        self.assertIn("Balfrin preservation gate ready_for_demonstration_evidence", report["summary"])
        rendered = MODULE.render_text_report(report)
        self.assertIn("Balfrin Probe Preservation Gate", rendered)
        self.assertIn("metrics_completion_source:", rendered)
        self.assertIn("required_run_root_entries:", rendered)
        self.assertIn("slurm_accounting_contract:", rendered)
        self.assertIn("spatial_gis_artifact_paths:", rendered)

    def test_partial_run_root_blocks_on_missing_metrics_and_contract_entries(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root"
        report = MODULE.build_report(run_root=run_root)

        self.assertEqual(report["gate_status"], "blocked_missing_inputs")
        self.assertFalse(report["future_live_run_would_satisfy_evidence_preservation_contract"])
        self.assertEqual(report["run_root_status"], "measured_run_root")
        self.assertEqual(report["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["metrics_completion_outcome"], "blocked")
        self.assertEqual(report["metrics_contract_status"], "blocked_missing_inputs")
        self.assertIn("memory_peak_mb", report["metrics_contract_missing_metrics"])
        self.assertIn("validation_output.file_count", report["metrics_contract_missing_metrics"])
        self.assertIn("hazard_output.file_count", report["metrics_contract_missing_metrics"])
        self.assertIn("conditional_curve_row_count", report["metrics_contract_missing_metrics"])
        self.assertIn("reduced_output_family_counts", report["metrics_contract_missing_metrics"])
        self.assertEqual(report["required_run_root_entries_status"], "blocked_missing_inputs")
        self.assertIn("output/validation_balfrin_probe_manifest.json", report["missing_run_root_entries"])
        self.assertIn("output/validation_balfrin_probe_scaling_summary.json", report["missing_run_root_entries"])
        self.assertEqual(report["output_family_summaries"]["status"], "blocked_missing_measured_output")
        self.assertEqual(report["spatial_gis_artifact_paths"]["status"], "blocked_missing_inputs")
        self.assertIn("hazard manifest outputs are unavailable", report["spatial_gis_artifact_paths"]["missing_reason"])
        self.assertIn("metrics_contract:blocked_missing_inputs", report["blocked_reasons"])
        self.assertIn("output_tier:blocked_missing_measured_output", report["blocked_reasons"])

    def test_missing_run_root_returns_a_fail_closed_report(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/does-not-exist"
        report = MODULE.build_report(run_root=run_root)

        self.assertEqual(report["gate_status"], "blocked_missing_run_root")
        self.assertEqual(report["run_root_status"], "missing_run_root")
        self.assertEqual(report["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["metrics_completion_outcome"], "blocked")
        self.assertFalse(report["future_live_run_would_satisfy_evidence_preservation_contract"])
        self.assertIn(str(run_root), report["missing_run_root_reason"])
        self.assertEqual(report["missing_run_root_entries"], [entry["path"] for entry in report["required_run_root_entries"]])
        self.assertEqual(report["output_family_summaries"]["status"], "blocked_missing_run_root")
        self.assertEqual(report["spatial_gis_artifact_paths"]["status"], "blocked_missing_run_root")

    def test_tb264_no_submission_attempt_is_incomplete_and_not_preserved(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/does-not-exist"
        report = MODULE.build_report(
            {
                "run_root": str(run_root),
                "metrics_completion_source": "blocked_missing_metrics",
                "metrics_completion_attempt_status": "blocked_remote_checkout_dirty",
                "metrics_contract_status": "blocked_missing_inputs",
            }
        )

        self.assertEqual(report["gate_status"], "blocked_missing_run_root")
        self.assertEqual(report["metrics_completion_outcome"], "incomplete")
        self.assertEqual(report["metrics_completion_attempt_status"], "blocked_remote_checkout_dirty")
        self.assertFalse(report["future_live_run_would_satisfy_evidence_preservation_contract"])

    def test_cli_writes_gate_artifacts_without_needing_submission(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_probe_preservation_gate_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_probe_preservation_gate_v1.json"
            text_path = artifact_dir / "balfrin_probe_preservation_gate_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["gate_status"], "ready_for_demonstration_evidence")
            self.assertIn(
                "Balfrin preservation gate ready_for_demonstration_evidence",
                text_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
