from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_probe_metrics_report.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_probe_metrics_report", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinProbeMetricsReportTests(unittest.TestCase):
    def test_live_run_like_summary_is_classified_with_next_run_required_metrics(self) -> None:
        report = MODULE.build_report(self.live_like_summary())

        self.assertEqual(report["schema_version"], "balfrin_probe_metrics_report_v1")
        self.assertEqual(report["report_status"], "blocked_missing_inputs")
        self.assertEqual(report["run_root_status"], "measured_run_root")
        self.assertEqual(
            report["classification"]["mandatory"]["blocked"],
            [
                "hazard_output.bytes",
                "hazard_output.file_count",
                "memory_peak_mb",
                "validation_output.bytes",
                "validation_output.file_count",
            ],
        )
        self.assertEqual(
            report["classification"]["ancillary"]["unavailable"],
            ["output_write_kind_bytes", "output_write_kind_seconds", "validation_output_mode"],
        )
        self.assertEqual(
            report["classification"]["next_run_required_metrics"],
            [
                "memory_peak_mb",
                "validation_output.file_count",
                "validation_output.bytes",
                "hazard_output.file_count",
                "hazard_output.bytes",
                "validation_output_mode",
                "output_write_kind_seconds",
                "output_write_kind_bytes",
            ],
        )
        self.assertIn("5 mandatory metrics blocked", report["summary"])
        self.assertIn("3 ancillary metrics unavailable", report["summary"])
        rendered = MODULE.render_text_report(report)
        self.assertIn("Balfrin Probe Metrics Report", rendered)
        self.assertIn("mandatory_blocked:", rendered)
        self.assertIn("next_run_required_metrics:", rendered)

    def test_missing_run_root_produces_blocked_report(self) -> None:
        run_root = Path("/scratch/mch/olifu/rust_rockfall/probes/missing-run-root")
        report = MODULE.build_report(None, run_root=run_root)

        self.assertEqual(report["report_status"], "blocked_missing_run_root")
        self.assertEqual(report["run_root_status"], "missing_run_root")
        self.assertEqual(report["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["metrics_completion_outcome"], "blocked")
        self.assertEqual(report["metrics_remediation"]["status"], "blocked_missing_run_root")
        self.assertEqual(report["classification"]["next_run_required_metrics"], [])
        self.assertIn(str(run_root), report["missing_run_root_reason"])

    def test_complete_run_root_is_classified_as_recovered_existing_run_root(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        report = MODULE.build_report(None, run_root=run_root)

        self.assertEqual(report["report_status"], "complete")
        self.assertEqual(report["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(report["metrics_completion_outcome"], "recovered")
        self.assertIn("metrics_completion_source=recovered_existing_run_root", report["summary"])
        self.assertIn("metrics_completion_source:", MODULE.render_text_report(report))

    def test_explicit_new_metrics_completion_rerun_source_is_preserved(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        report = MODULE.build_report(None, run_root=run_root)
        report["metrics_completion_source"] = "new_metrics_completion_rerun"
        report.pop("metrics_completion_outcome", None)

        rebuilt = MODULE.build_report(report)

        self.assertEqual(rebuilt["metrics_completion_source"], "new_metrics_completion_rerun")
        self.assertEqual(rebuilt["metrics_completion_outcome"], "measured")

    def test_tb264_no_submission_attempt_is_incomplete_not_measured(self) -> None:
        evidence = self.live_like_summary()
        evidence.update(
            {
                "run_root": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v2",
                "metrics_completion_source": "blocked_missing_metrics",
                "metrics_completion_attempt_status": "blocked_remote_checkout_dirty",
                "tb_reference": "TB-264",
                "slurm_job_id": None,
                "sacct_fields_collected": False,
            }
        )

        report = MODULE.build_report(evidence)

        self.assertEqual(report["report_status"], "blocked_missing_inputs")
        self.assertEqual(report["metrics_completion_source"], "blocked_missing_metrics")
        self.assertEqual(report["metrics_completion_outcome"], "incomplete")
        self.assertEqual(report["metrics_completion_attempt_status"], "blocked_remote_checkout_dirty")
        self.assertIn("memory_peak_mb", report["classification"]["missing_mandatory_metrics"])
        self.assertIn("metrics_completion_outcome=incomplete", report["summary"])

    def test_cli_writes_json_and_text_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            evidence_path = tmp / "evidence.json"
            evidence_path.write_text(json.dumps(self.live_like_summary(), indent=2), encoding="utf-8")
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1"

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--evidence-json",
                        str(evidence_path),
                        "--artifact-dir",
                        str(artifact_dir),
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_probe_metrics_report_v1.json"
            text_path = artifact_dir / "balfrin_probe_metrics_report_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "balfrin_probe_metrics_report_v1")
            self.assertIn("Balfrin Probe Metrics Report", text_path.read_text(encoding="utf-8"))

    def live_like_summary(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_probe_metrics_v1",
            "run_root": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517",
            "output_root": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/output",
            "probe_manifest_path": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/probe_manifest.yaml",
            "command_plan_path": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/command_plan.json",
            "hazard_manifest_path": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/output/validation_tschamut_public_target_gate_v1_manifest.json",
            "metrics_contract_status": "blocked_missing_inputs",
            "metrics_contract_missing_metrics": [
                "memory_peak_mb",
                "validation_output.file_count",
                "validation_output.bytes",
                "hazard_output.file_count",
                "hazard_output.bytes",
            ],
            "metrics_contract_ancillary_unavailable_metrics": [
                "validation_output_mode",
                "output_write_kind_seconds",
                "output_write_kind_bytes",
            ],
            "metric_statuses": {
                "mandatory": {
                    "wall_time_seconds": {"status": "measured", "source": "performance.total_wall_seconds", "value": 12.611904342891648},
                    "memory_peak_mb": {"status": "blocked", "source": "performance.memory_peak_mb", "value": None, "reason": "missing required peak-memory evidence"},
                    "validation_output.file_count": {"status": "blocked", "source": "performance.validation_output_file_count", "value": None, "reason": "missing required validation output file count"},
                    "validation_output.bytes": {"status": "blocked", "source": "performance.validation_output_bytes", "value": None, "reason": "missing required validation output byte count"},
                    "hazard_output.file_count": {"status": "blocked", "source": "performance.hazard_output_file_count", "value": None, "reason": "missing required hazard output file count"},
                    "hazard_output.bytes": {"status": "blocked", "source": "performance.hazard_output_bytes", "value": None, "reason": "missing required hazard output byte count"},
                    "conditional_curve_row_count": {"status": "measured", "source": "conditional_execution.conditional_curve_export.row_count", "value": 729600},
                    "restartability_metadata.trajectory_plan_id": {"status": "measured", "source": "conditional_execution.trajectory_generation.plan_id", "value": "validation_tschamut_public_conditional_gate_v1__trajectory_execution_plan__ec29c17a15d14be158e5b29f"},
                    "restartability_metadata.reducer_plan_id": {"status": "measured", "source": "conditional_execution.reducer.trajectory_execution_plan_id", "value": "validation_tschamut_public_conditional_gate_v1__execution_plan__671312f4083331a0220e0597"},
                    "restartability_metadata.trajectory_decision_counts": {"status": "measured", "source": "trajectory_chunks/*.json::orchestration_decision", "value": {"executed": 4}},
                    "restartability_metadata.reducer_decision_counts": {"status": "measured", "source": "chunks/*.json::orchestration_decision", "value": {"reused_completed_state": 2, "executed": 2}},
                },
                "ancillary": {
                    "validation_output_mode": {"status": "unavailable", "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.validation_output_mode", "value": None, "reason": "the canonical bundle does not retain reduced-output family counts for this field"},
                    "output_write_kind_seconds": {"status": "unavailable", "source": "output_root.scaling_summary.output_write_kind_seconds", "value": {}, "reason": "the canonical bundle does not retain output_root.scaling_summary"},
                    "output_write_kind_bytes": {"status": "unavailable", "source": "output_root.scaling_summary.output_write_kind_bytes", "value": {}, "reason": "the canonical bundle does not retain output_root.scaling_summary"},
                },
                "measured": [
                    "conditional_curve_row_count",
                    "restartability_metadata.reducer_decision_counts",
                    "restartability_metadata.reducer_plan_id",
                    "restartability_metadata.trajectory_decision_counts",
                    "restartability_metadata.trajectory_plan_id",
                    "wall_time_seconds",
                ],
                "unavailable": ["output_write_kind_bytes", "output_write_kind_seconds", "validation_output_mode"],
                "blocked": [
                    "hazard_output.bytes",
                    "hazard_output.file_count",
                    "memory_peak_mb",
                    "validation_output.bytes",
                    "validation_output.file_count",
                ],
            },
            "metrics_remediation": {
                "schema_version": "balfrin_probe_metrics_remediation_v1",
                "status": "action_required",
                "missing_mandatory_metrics": [
                    "memory_peak_mb",
                    "validation_output.file_count",
                    "validation_output.bytes",
                    "hazard_output.file_count",
                    "hazard_output.bytes",
                ],
                "unavailable_ancillary_metrics": [
                    "validation_output_mode",
                    "output_write_kind_seconds",
                    "output_write_kind_bytes",
                ],
                "next_run_required_metrics": [
                    "memory_peak_mb",
                    "validation_output.file_count",
                    "validation_output.bytes",
                    "hazard_output.file_count",
                    "hazard_output.bytes",
                    "validation_output_mode",
                    "output_write_kind_seconds",
                    "output_write_kind_bytes",
                ],
                "next_run_collection_checklist": [],
            },
            "output_file_count": 58,
            "output_bytes": 192350243,
            "output_write_seconds": 9.882050781976432,
            "total_wall_seconds": 12.611904342891648,
            "memory_peak_mb": None,
            "validation_output_file_count": None,
            "validation_output_bytes": None,
            "hazard_output_file_count": None,
            "hazard_output_bytes": None,
            "conditional_curve_row_count": 729600,
            "trajectory_plan_id": "validation_tschamut_public_conditional_gate_v1__trajectory_execution_plan__ec29c17a15d14be158e5b29f",
            "reducer_plan_id": "validation_tschamut_public_conditional_gate_v1__execution_plan__671312f4083331a0220e0597",
            "trajectory_decision_counts": {"executed": 4},
            "reducer_decision_counts": {"reused_completed_state": 2, "executed": 2},
            "ancillary_metrics": {
                "validation_output_mode": {
                    "status": "unavailable",
                    "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.validation_output_mode",
                    "value": None,
                },
                "output_write_kind_seconds": {
                    "status": "unavailable",
                    "source": "output_root.scaling_summary.output_write_kind_seconds",
                    "value": {},
                },
                "output_write_kind_bytes": {
                    "status": "unavailable",
                    "source": "output_root.scaling_summary.output_write_kind_bytes",
                    "value": {},
                },
            },
            "log_audit": {
                "logs_root": "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/logs",
                "file_count": 1,
                "matched_line_count": 1,
                "warning_like_line_count": 0,
                "error_like_line_count": 0,
                "affected_log_paths": [],
                "files": [],
            },
        }


if __name__ == "__main__":
    unittest.main()
