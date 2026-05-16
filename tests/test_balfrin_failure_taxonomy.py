from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_failure_taxonomy.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_failure_taxonomy", SCRIPT_PATH)
assert SPEC is not None
taxonomy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(taxonomy)


class BalfrinFailureTaxonomyTests(unittest.TestCase):
    def test_catalog_contains_representative_classes_and_boundaries(self) -> None:
        report = taxonomy.build_report()

        self.assertEqual(report["schema_version"], "balfrin_failure_taxonomy_v1")
        self.assertEqual(report["taxonomy_status"], "catalog_only")
        self.assertEqual(len(report["failure_classes"]), 7)
        self.assertIn("readiness_blocked", [entry["class_id"] for entry in report["failure_classes"]])
        self.assertIn("scientific_state_failure", [entry["class_id"] for entry in report["failure_classes"]])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_evidence_classifies_observed_and_scope_limited_states(self) -> None:
        report = taxonomy.build_report(
            {
                "pilot_id": "tschamut_public_pilot",
                "run_id": "tschamut_public_balfrin_single_release_zone_v1",
                "readiness_check": {
                    "status": "blocked_for_balfrin_readiness",
                    "blocking_checks": ["input_freeze.terrain_metadata_path"],
                },
                "submission_report": {
                    "status": "scheduler_submission_failed",
                    "submitted_job_id": "",
                },
                "runtime_report": {"status": "failed"},
                "probe_metrics": {
                    "metrics_contract_status": "blocked_missing_inputs",
                    "metrics_contract_missing_metrics": [
                        "validation_output.file_count",
                        "hazard_output.file_count",
                        "wall_time_seconds",
                    ],
                    "log_audit": {"error_like_line_count": 2},
                },
                "post_run_report": {
                    "interpretation_status": "inconclusive_conditional_diagnostic",
                    "readiness_check": {"status": "ready_for_balfrin_single_release_zone_pilot"},
                },
                "gis_report": {
                    "gis_cog_readiness_status": "metadata_only",
                },
            }
        )

        failure_map = {entry["class_id"]: entry for entry in report["failure_classes"]}
        self.assertEqual(report["taxonomy_status"], "observed_with_boundaries")
        self.assertEqual(failure_map["readiness_blocked"]["current_status"], "observed")
        self.assertEqual(failure_map["scheduler_submission_failed"]["current_status"], "observed")
        self.assertEqual(failure_map["runtime_failure"]["current_status"], "observed")
        self.assertEqual(failure_map["partial_output_incomplete"]["current_status"], "observed")
        self.assertEqual(failure_map["metrics_blocked"]["current_status"], "observed")
        self.assertEqual(failure_map["gis_export_blocked"]["current_status"], "scope_limited")
        self.assertEqual(failure_map["scientific_state_failure"]["current_status"], "scope_limited")
        self.assertGreaterEqual(report["status_counts"]["observed"], 5)


if __name__ == "__main__":
    unittest.main()
