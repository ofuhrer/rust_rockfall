from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_management_demo_package.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_management_demo_package", SCRIPT_PATH)
assert SPEC is not None
package = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(package)


class BalfrinManagementDemoPackageTests(unittest.TestCase):
    def test_current_package_report_keeps_measured_and_fixture_backed_sections_distinct(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        report = package.build_report(run_root=run_root, artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"))

        self.assertEqual(report["schema_version"], "balfrin_management_demo_package_v1")
        self.assertEqual(report["package_status"], "mixed_provenance")
        self.assertEqual(report["package_provenance_status"], "mixed_provenance")
        self.assertEqual(report["package_summary"]["section_counts"], {"measured": 7, "fixture_backed": 1, "blocked_missing_inputs": 0})
        self.assertEqual(report["replay_section"]["status"], "replayable")
        self.assertEqual(report["replay_section"]["run_root_provenance"], "fixture_backed")
        self.assertEqual(report["runtime_section"]["status"], "measured")
        self.assertEqual(report["restartability_section"]["status"], "measured")
        self.assertEqual(report["gis_scope_section"]["status"], "full_scope")
        self.assertEqual(report["uncertainty_section"]["status"], "measured")
        self.assertEqual(report["claim_boundary_section"]["status"], "guarded")
        self.assertEqual(report["scaling_section"]["status"], "measured")
        self.assertTrue(report["scaling_section"]["single_job_sufficient_for_next_step"])
        self.assertFalse(report["scaling_section"]["scale_up_authorized"])
        self.assertEqual(report["next_decision_section"]["status"], "deferred")
        self.assertEqual(report["next_decision_section"]["recommended_next_authorized_step"], "management review of this package")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertIn("replay is fixture-backed", report["package_summary"]["summary"])
        self.assertIn("next authorized step is management review", report["package_summary"]["summary"])
        self.assertEqual(len(report["regeneration_commands"]), 3)
        self.assertIn("summarize_balfrin_management_demo_package.py", report["regeneration_commands"][-1])
        self.assertIn("section_provenance_profile:", package.render_text_report(report))
        self.assertIn("next_decision_section:", package.render_text_report(report))

    def test_fixture_backed_override_stays_fixture_backed(self) -> None:
        report = package.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            evidence_override=self.fixture_backed_override(),
        )

        self.assertEqual(report["package_status"], "fixture_backed")
        self.assertEqual(report["package_summary"]["section_counts"], {"measured": 0, "fixture_backed": 8, "blocked_missing_inputs": 0})
        self.assertTrue(all(section["evidence_type"] == "fixture_backed" for section in report["section_provenance_profile"]))
        self.assertIn("fixture-backed", report["package_summary"]["summary"])
        self.assertEqual(report["replay_section"]["status"], "replayable")

    def test_missing_inputs_block_the_package(self) -> None:
        report = package.build_report(
            run_root=ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root",
            artifact_dir=Path("/tmp/balfrin_management_demo_package_v1"),
            evidence_override={"missing_inputs": ["replay_section"]},
        )

        self.assertEqual(report["package_status"], "blocked_missing_inputs")
        self.assertEqual(report["package_summary"]["section_counts"], {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 8})
        self.assertTrue(all(section["evidence_type"] == "blocked" for section in report["section_provenance_profile"]))
        self.assertEqual(report["missing_inputs"], ["replay_section"])
        self.assertIn("blocked because one or more required sections are missing", report["package_summary"]["summary"])

    def test_cli_writes_json_and_text_package_artifacts(self) -> None:
        run_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"

        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_management_demo_package_v1"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = package.main(
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
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["schema_version"], "balfrin_management_demo_package_v1")
            self.assertTrue((artifact_dir / "balfrin_management_demo_package_v1.json").exists())
            self.assertTrue((artifact_dir / "balfrin_management_demo_package_v1.txt").exists())
            self.assertEqual(report["replay_section"]["run_root_provenance"], "fixture_backed")
            self.assertIn("claim_boundary_section", package.render_text_report(report))

    def fixture_backed_override(self) -> dict[str, object]:
        fixture_root = "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        return {
            "runtime_section": {
                "status": "measured",
                "summary": "Runtime is measured.",
                "source_paths": ["/var/measured/runtime.json"],
                "evidence_type": "fixture_backed",
            },
            "replay_section": {
                "status": "replayable",
                "summary": "Replay is fixture-backed.",
                "source_paths": [fixture_root],
                "evidence_type": "fixture_backed",
            },
            "restartability_section": {
                "status": "measured",
                "summary": "Restartability is measured.",
                "source_paths": ["/var/measured/restartability.json"],
                "evidence_type": "fixture_backed",
            },
            "gis_scope_section": {
                "status": "full_scope",
                "summary": "GIS scope is measured.",
                "source_paths": ["/var/measured/gis_scope.json"],
                "evidence_type": "fixture_backed",
            },
            "uncertainty_section": {
                "status": "measured",
                "summary": "Uncertainty is measured.",
                "source_paths": ["/var/measured/uncertainty.json"],
                "evidence_type": "fixture_backed",
            },
            "claim_boundary_section": {
                "status": "guarded",
                "summary": "Claim boundaries remain false.",
                "claim_boundaries": {
                    "operational_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                    "annual_frequency_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                    "scale_up_authorized": False,
                    "distributed_execution_authorized": False,
                },
                "source_paths": ["/var/measured/claim_boundaries.md"],
                "evidence_type": "fixture_backed",
            },
            "scaling_section": {
                "status": "measured",
                "summary": "Scaling stays bounded.",
                "single_job_sufficient_for_next_step": True,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
                "scaling_implication": "Keep the next step at the single-job boundary.",
                "source_paths": ["/var/measured/scaling.json"],
                "evidence_type": "fixture_backed",
            },
            "next_decision_section": {
                "status": "deferred",
                "summary": "Management review only.",
                "recommended_next_authorized_step": "management review of this package",
                "recommendation": "The next authorized step is management review of this package.",
                "source_paths": ["/var/measured/next_decision.md"],
                "evidence_type": "fixture_backed",
            },
        }


if __name__ == "__main__":
    unittest.main()
