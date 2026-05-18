from __future__ import annotations

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "rehearse_balfrin_post_run_evidence_collector.py"
SPEC = importlib.util.spec_from_file_location("rehearse_balfrin_post_run_evidence_collector", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinPostRunEvidenceCollectorRehearsalTests(unittest.TestCase):
    def test_matrix_covers_expected_classifications_for_both_source_families(self) -> None:
        report = MODULE.build_rehearsal_matrix()

        self.assertEqual(report["schema_version"], "balfrin_post_run_evidence_collector_rehearsal_v1")
        self.assertEqual(report["matrix_status"], "fixture_backed_rehearsal")
        self.assertEqual(report["case_count"], 10)
        self.assertFalse(report["measured_result_promoted"])
        self.assertEqual(
            report["classification_counts"],
            {
                "blocked_incomplete_run_root": 2,
                "blocked_missing_run_root": 2,
                "blocked_non_git_artifact_unavailable": 2,
                "blocked_ssh_unavailable": 2,
                "fixture_backed_complete": 2,
            },
        )
        self.assertEqual(
            {case["source_family"] for case in report["cases"]},
            {"metrics_completion_rerun", "authorized_multi_zone_probe"},
        )
        self.assertTrue(
            all(case["closure_input_compatibility"]["status"] == "blocked_missing_inputs" for case in report["cases"])
        )
        self.assertTrue(
            all(case["closure_package_agreement"]["status"] == "agrees_blocked" for case in report["cases"])
        )

    def test_complete_fixture_is_complete_but_not_measured_closure_evidence(self) -> None:
        report = MODULE.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            source_family="metrics_completion_rerun",
        )

        self.assertEqual(report["collector_status"], "fixture_backed_complete")
        self.assertEqual(report["metrics_report_status"], "complete")
        self.assertEqual(report["preservation_gate_status"], "ready_for_demonstration_evidence")
        self.assertEqual(report["new_measured_evidence_input"]["evidence_type"], "fixture_backed")
        self.assertEqual(report["closure_input_compatibility"]["status"], "blocked_missing_inputs")
        self.assertIn(
            "new_measured_evidence.evidence_type=measured",
            report["closure_input_compatibility"]["missing_fields"],
        )
        self.assertTrue(report["closure_package_agreement"]["preserves_fixture_backed_boundary"])
        self.assertFalse(report["measured_result_promoted"])

    def test_incomplete_fixture_remains_blocked_with_missing_field_semantics(self) -> None:
        report = MODULE.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root",
            source_family="authorized_multi_zone_probe",
        )

        self.assertEqual(report["collector_status"], "blocked_incomplete_run_root")
        self.assertEqual(report["metrics_report_status"], "blocked_missing_inputs")
        self.assertEqual(report["preservation_gate_status"], "blocked_missing_inputs")
        self.assertIn("memory_peak_mb", report["missing_fields"]["metrics"])
        self.assertIn("output/validation_balfrin_probe_manifest.json", report["missing_fields"]["run_root_entries"])
        self.assertIn(
            "metrics:memory_peak_mb",
            report["new_measured_evidence_input"]["missing_fields"],
        )
        self.assertEqual(report["new_measured_evidence_input"]["evidence_type"], "blocked")
        self.assertEqual(report["closure_input_compatibility"]["status"], "blocked_missing_inputs")
        self.assertFalse(report["measured_result_promoted"])

    def test_missing_and_access_blocked_paths_fail_closed_with_exact_status(self) -> None:
        missing = MODULE.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/does-not-exist",
            source_family="metrics_completion_rerun",
        )
        blocked_access = MODULE.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            source_family="metrics_completion_rerun",
            balfrin_access_preflight=MODULE._blocked_ssh_access_report(),
        )

        self.assertEqual(missing["collector_status"], "blocked_missing_run_root")
        self.assertEqual(missing["metrics_report_status"], "blocked_missing_run_root")
        self.assertEqual(missing["preservation_gate_status"], "blocked_missing_run_root")
        self.assertEqual(blocked_access["collector_status"], "blocked_ssh_unavailable")
        self.assertEqual(blocked_access["balfrin_access_preflight_status"], "blocked_ssh_unavailable")
        self.assertEqual(blocked_access["non_git_artifact_status"], "not_checked_due_to_access")

    def test_non_git_artifact_unavailable_blocks_before_collection(self) -> None:
        report = MODULE.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            source_family="authorized_multi_zone_probe",
            non_git_artifact_available=False,
        )

        self.assertEqual(report["collector_status"], "blocked_non_git_artifact_unavailable")
        self.assertEqual(report["non_git_artifact_status"], "blocked_non_git_artifact_unavailable")
        self.assertEqual(report["metrics_report_status"], "blocked_non_git_artifact_unavailable")
        self.assertEqual(report["preservation_gate_status"], "blocked_non_git_artifact_unavailable")
        self.assertFalse(report["measured_result_promoted"])

    def test_cli_matrix_outputs_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--matrix", "--format", "json"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["case_count"], 10)


if __name__ == "__main__":
    unittest.main()
