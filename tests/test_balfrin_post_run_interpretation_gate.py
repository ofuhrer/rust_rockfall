from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_post_run_interpretation_gate.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_post_run_interpretation_gate", SCRIPT_PATH)
assert SPEC is not None
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


class BalfrinPostRunInterpretationGateTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_measured_state_accepts_conditional_diagnostic_artifact(self) -> None:
        report = gate.build_report(self.measured_evidence())

        self.assertEqual(report["schema_version"], "balfrin_post_run_interpretation_gate_v1")
        self.assertEqual(report["interpretation_status"], "measured_conditional_diagnostic")
        self.assertEqual(report["artifact_acceptance_status"], "accepted_conditional_diagnostic")
        self.assertTrue(report["usable_as_conditional_diagnostic_artifact"])
        self.assertEqual(report["readiness_check"]["status"], "measured")
        self.assertEqual(report["convergence_stability_check"]["status"], "measured")
        self.assertEqual(report["output_check"]["status"], "measured")
        self.assertEqual(report["gis_cog_check"]["status"], "measured")
        self.assertEqual(report["physical_credibility_check"]["status"], "not_established")
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["physical_probability_claims_allowed"])
        self.assertIn("conditional diagnostics are not physical probabilities", report["claim_boundaries"]["notes"])

    def test_inconclusive_state_still_accepts_the_artifact_but_keeps_the_boundary_explicit(self) -> None:
        evidence = self.measured_evidence()
        evidence["convergence_stability_check"]["status"] = "inconclusive"
        evidence["output_check"]["status"] = "summary_only_not_rebuildable"
        evidence["gis_cog_check"]["status"] = "gis_package_ready_cog_blocked"

        report = gate.build_report(evidence)

        self.assertEqual(report["interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(report["artifact_acceptance_status"], "accepted_conditional_diagnostic")
        self.assertTrue(report["usable_as_conditional_diagnostic_artifact"])
        self.assertEqual(report["convergence_stability_check"]["status"], "inconclusive")
        self.assertEqual(report["output_check"]["status"], "inconclusive")
        self.assertEqual(report["gis_cog_check"]["status"], "inconclusive")
        self.assertIn("physical-probability claim", report["physical_credibility_check"]["summary"])

    def test_missing_inputs_block_the_gate(self) -> None:
        report = gate.build_report({"missing_inputs": ["post_run_evidence_bundle"]})

        self.assertEqual(report["interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["artifact_acceptance_status"], "blocked_missing_inputs")
        self.assertFalse(report["usable_as_conditional_diagnostic_artifact"])
        self.assertEqual(report["missing_inputs"], ["post_run_evidence_bundle"])
        self.assertEqual(report["required_checks"][0]["status"], "blocked_missing_inputs")

    def test_cli_emits_json_and_text_for_measured_and_returns_blocked_status_when_inputs_missing(self) -> None:
        measured_path = self.write_json(self.measured_evidence())
        blocked_path = self.write_json({"missing_inputs": ["post_run_evidence_bundle"]})
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = gate.main(["--format", "text", "--evidence-json", str(measured_path)])
            self.assertEqual(exit_code, 0)
            self.assertIn("Balfrin Post-Run Interpretation Gate", buffer.getvalue())
            self.assertIn("measured_conditional_diagnostic", buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = gate.main(["--format", "json", "--evidence-json", str(measured_path)])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = gate.main(["--format", "text", "--evidence-json", str(blocked_path)])
            self.assertEqual(exit_code, 2)
            self.assertIn("blocked_missing_inputs", buffer.getvalue())
        finally:
            measured_path.unlink(missing_ok=True)
            blocked_path.unlink(missing_ok=True)

    def measured_evidence(self) -> dict[str, object]:
        return {
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_balfrin_single_release_zone_v1",
            "contract_path": "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml",
            "readiness_check": {
                "status": "ready_for_balfrin_single_release_zone_pilot",
                "summary": "Frozen Balfrin pilot contract and local inputs are ready.",
            },
            "convergence_stability_check": {
                "status": "measured",
                "summary": "Convergence and repeatability are measured.",
            },
            "output_check": {
                "status": "rebuildable_reduced_output",
                "summary": "The output footprint is bounded and reproducible.",
            },
            "gis_cog_check": {
                "status": "gis_package_ready",
                "summary": "GIS package and COG readiness are available.",
            },
            "physical_credibility_check": {
                "status": "not_established",
                "summary": "Physical credibility remains unestablished and is not used for physical-probability claims.",
            },
        }


if __name__ == "__main__":
    unittest.main()
