from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_evidence_bundle.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_evidence_bundle", SCRIPT_PATH)
assert SPEC is not None
bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bundle)


class BalfrinEvidenceBundleTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_complete_bundle_is_reported_as_complete_and_preserves_boundaries(self) -> None:
        report = bundle.build_report({"bundle_report": self.complete_bundle_report()})

        self.assertEqual(report["schema_version"], "balfrin_evidence_bundle_v1")
        self.assertEqual(report["bundle_status"], "complete")
        self.assertEqual(report["bundle_summary"]["status"], "complete")
        self.assertIn("readiness, metrics, outputs, GIS / COG status", report["bundle_summary"]["summary"])
        self.assertEqual(report["post_run_interpretation_gate_report"]["interpretation_status"], "measured_conditional_diagnostic")
        self.assertEqual(report["gis_cog_readiness_report"]["gis_cog_readiness_status"], "gis_package_ready")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_incomplete_bundle_remains_incomplete_without_blocking_claim_boundaries(self) -> None:
        report = bundle.build_report({"bundle_report": self.incomplete_bundle_report()})

        self.assertEqual(report["bundle_status"], "incomplete")
        self.assertEqual(report["bundle_summary"]["status"], "incomplete")
        self.assertEqual(report["post_run_interpretation_gate_report"]["interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(report["gis_cog_readiness_report"]["gis_cog_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertIn("scope-limited", report["bundle_summary"]["summary"])

    def test_missing_inputs_bundle_is_blocked(self) -> None:
        report = bundle.build_report({"missing_inputs": ["single_job_execution_summary", "gis_cog_readiness_report"]})

        self.assertEqual(report["bundle_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["single_job_execution_summary", "gis_cog_readiness_report"])
        self.assertEqual(report["bundle_summary"]["blockers"], ["single_job_execution_summary", "gis_cog_readiness_report"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_cli_writes_json_and_text_bundle_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            override_path = self.write_json({"bundle_report": self.complete_bundle_report()})
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"

            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    exit_code = bundle.main(
                        [
                            "--artifact-dir",
                            str(artifact_dir),
                            "--evidence-json",
                            str(override_path),
                        ]
                    )
            finally:
                override_path.unlink(missing_ok=True)

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_evidence_bundle_v1.json"
            text_path = artifact_dir / "balfrin_evidence_bundle_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            json_report = json.loads(json_path.read_text(encoding="utf-8"))
            text_report = text_path.read_text(encoding="utf-8")
            self.assertEqual(json_report["bundle_status"], "complete")
            self.assertIn("Balfrin Evidence Bundle", text_report)
            self.assertIn("canonical_bundle_path:", text_report)
            self.assertIn("operational_claims_allowed: False", text_report)

    def complete_bundle_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_evidence_bundle_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_balfrin_single_release_zone_v1",
            "canonical_bundle_path": "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1",
            "bundle_status": "complete",
            "bundle_summary": {
                "status": "complete",
                "summary": (
                    "Balfrin readiness, metrics, outputs, GIS / COG status, restartability, and interpretation checks are all present and measurably aligned."
                ),
                "blockers": [],
            },
            "single_job_execution_summary": {
                "schema_version": "balfrin_single_job_execution_sufficiency_v1",
                "decision": "defer",
                "single_job_sufficient_for_next_step": True,
                "metrics_contract": {"status": "complete"},
            },
            "probe_metrics": {
                "status": "complete",
                "wall_time_seconds": 17.84,
                "memory_peak_mb": 409.22,
            },
            "post_run_interpretation_gate_report": {
                "schema_version": "balfrin_post_run_interpretation_gate_v1",
                "interpretation_status": "measured_conditional_diagnostic",
                "artifact_acceptance_status": "accepted_conditional_diagnostic",
                "usable_as_conditional_diagnostic_artifact": True,
                "claim_boundaries": self.claim_boundaries(),
            },
            "gis_cog_readiness_report": {
                "schema_version": "tschamut_gis_cog_package_readiness_v1",
                "gis_cog_readiness_status": "gis_package_ready",
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
            },
            "claim_boundaries": self.claim_boundaries(),
            "source_paths": {"single_job_record_paths": {}, "post_run_contract_path": "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml"},
            "evidence_sources": [
                "scripts/summarize_balfrin_single_job_execution.py",
                "scripts/summarize_balfrin_post_run_interpretation_gate.py",
                "scripts/audit_gis_cog_package_readiness.py",
                "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1",
            ],
            "missing_inputs": [],
        }

    def incomplete_bundle_report(self) -> dict[str, object]:
        report = self.complete_bundle_report()
        report["bundle_status"] = "incomplete"
        report["bundle_summary"] = {
            "status": "incomplete",
            "summary": (
                "Balfrin evidence is present, but one or more sections remain inconclusive or scope-limited; the bundle keeps the diagnostic boundaries explicit."
            ),
            "blockers": [],
        }
        report["post_run_interpretation_gate_report"] = {
            "schema_version": "balfrin_post_run_interpretation_gate_v1",
            "interpretation_status": "inconclusive_conditional_diagnostic",
            "artifact_acceptance_status": "accepted_conditional_diagnostic",
            "usable_as_conditional_diagnostic_artifact": True,
            "claim_boundaries": self.claim_boundaries(),
        }
        report["gis_cog_readiness_report"] = {
            "schema_version": "tschamut_gis_cog_package_readiness_v1",
            "gis_cog_readiness_status": "gis_package_ready_cog_blocked",
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
        }
        return report

    def claim_boundaries(self) -> dict[str, bool]:
        return {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        }


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
