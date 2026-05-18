from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_target_area_metrics_completion_rerun_package.py"
SPEC = importlib.util.spec_from_file_location(
    "summarize_balfrin_target_area_metrics_completion_rerun_package",
    SCRIPT_PATH,
)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinTargetAreaMetricsCompletionRerunPackageTests(unittest.TestCase):
    def test_default_report_is_complete_and_scoped_to_metrics_completion(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_target_area_metrics_completion_rerun_package_v1")
        self.assertEqual(report["package_status"], "complete_rerun_package")
        self.assertEqual(report["package_provenance_status"], "mixed_provenance")
        self.assertEqual(report["preservation_checklist"]["status"], "complete")
        self.assertEqual(report["preservation_checklist"]["missing_metrics"], [])
        self.assertEqual(report["preservation_checklist"]["missing_run_root_entries"], [])
        self.assertEqual(report["preservation_checklist"]["missing_replay_metadata"], [])
        self.assertEqual(report["existing_target_area_run_comparison"]["closure_targets"], MODULE.REQUIRED_METRICS)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["output_file_count"], 58)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["output_bytes"], 192350243)
        self.assertEqual(report["existing_target_area_run_comparison"]["measured_fields"]["conditional_curve_row_count"], 729600)
        self.assertIn("peak-memory and split validation/hazard output metrics", report["existing_target_area_run_comparison"]["summary"])
        self.assertIn("--dry-run", report["rerun_command_plan"]["dry_run_command"])
        self.assertIn("--generate-only", report["rerun_command_plan"]["generate_only_command"])
        self.assertIn("no live submission is authorized", report["package_summary"]["summary"])
        self.assertIn("Balfrin Target-Area Metrics Completion Rerun Package", MODULE.render_text_report(report))

    def test_partial_package_blocks_when_required_declarations_are_missing(self) -> None:
        report = MODULE.build_report(
            {
                "declared_metrics": MODULE.REQUIRED_METRICS[:-1],
                "declared_run_root_entries": [entry["path"] for entry in MODULE.REQUIRED_RUN_ROOT_ENTRIES[:-1]],
                "declared_replay_metadata": MODULE.REQUIRED_REPLAY_METADATA[:-1],
            }
        )

        self.assertEqual(report["package_status"], "partial_rerun_package")
        self.assertEqual(report["preservation_checklist"]["status"], "blocked_missing_inputs")
        self.assertIn("hazard_output.bytes", report["preservation_checklist"]["missing_metrics"])
        self.assertIn("output/chunks", report["preservation_checklist"]["missing_run_root_entries"])
        self.assertIn("git_commit", report["preservation_checklist"]["missing_replay_metadata"])
        self.assertIn("fails closed until every required metric", report["preservation_checklist"]["summary"])

    def test_missing_package_inputs_return_a_fail_closed_report(self) -> None:
        report = MODULE.build_report({"missing_inputs": ["existing_target_area_run"]})

        self.assertEqual(report["package_status"], "missing_rerun_package")
        self.assertEqual(report["package_provenance_status"], "blocked_missing_inputs")
        self.assertEqual(report["rerun_command_plan"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["preservation_checklist"]["status"], "blocked_missing_inputs")
        self.assertIn("required rerun-package inputs are missing", report["package_summary"]["summary"])
        self.assertTrue(all(section["status"] == "blocked_missing_inputs" for section in report["section_provenance_profile"]))

    def test_cli_writes_json_and_text_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_target_area_metrics_completion_rerun_package_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_target_area_metrics_completion_rerun_package_v1.json"
            text_path = artifact_dir / "balfrin_target_area_metrics_completion_rerun_package_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["package_status"], "complete_rerun_package")
            self.assertIn("preservation_checklist", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
