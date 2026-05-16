from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_scientific_delta_report.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_scientific_delta_report", SCRIPT_PATH)
assert SPEC is not None
delta = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(delta)


class BalfrinScientificDeltaReportTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_measured_state_compares_balfrin_against_same_scale_evidence(self) -> None:
        report = delta.build_report(self.measured_evidence())

        self.assertEqual(report["schema_version"], "balfrin_scientific_delta_report_v1")
        self.assertEqual(report["scientific_delta_status"], "measured_existing_artifacts")
        self.assertEqual(report["balfrin_post_run_interpretation_gate_report"]["interpretation_status"], "measured_conditional_diagnostic")
        self.assertEqual(report["same_scale_uncertainty_report"]["spatial_uncertainty_status"], "measured_existing_artifacts")
        self.assertEqual(report["same_scale_stability_frontier_report"]["frontier_status"], "measured_existing_artifacts")
        self.assertEqual(report["closure_gap_deltas_report"]["closure_gap_status"], "measured_gaps_remain")
        self.assertEqual(report["hotspot_provenance_report"]["hotspot_provenance_status"], "measured_existing_artifacts")
        self.assertGreater(len(report["scientific_delta_summary"]["confirmed"]), 0)
        self.assertIn("same-scale uncertainty envelope", report["scientific_delta_summary"]["comparisons"][0]["summary"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_inconclusive_state_keeps_the_scientific_boundary_explicit(self) -> None:
        evidence = self.measured_evidence()
        evidence["post_run_interpretation_gate_report"]["interpretation_status"] = "inconclusive_conditional_diagnostic"
        evidence["same_scale_stability_frontier_report"]["frontier_status"] = "inconclusive_existing_artifacts"

        report = delta.build_report(evidence)

        self.assertEqual(report["scientific_delta_status"], "inconclusive_existing_artifacts")
        self.assertIn("incompletely resolved", report["scientific_delta_summary"]["confirmed"][0])
        self.assertIn("does not reclassify", report["scientific_delta_summary"]["unchanged"][0])
        self.assertEqual(report["same_scale_stability_frontier_report"]["frontier_status"], "inconclusive_existing_artifacts")

    def test_missing_inputs_block_the_delta_report(self) -> None:
        report = delta.build_report({"missing_inputs": ["same_scale_uncertainty_report", "hotspot_provenance_report"]})

        self.assertEqual(report["scientific_delta_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["same_scale_uncertainty_report", "hotspot_provenance_report"])
        self.assertEqual(report["same_scale_uncertainty_report"]["spatial_uncertainty_status"], "blocked_missing_inputs")
        self.assertEqual(report["scientific_delta_summary"]["status"], "blocked_missing_inputs")
        self.assertFalse(report["scale_up_authorized"])

    def test_cli_emits_json_and_text_for_measured_report(self) -> None:
        evidence_path = self.write_json(self.measured_evidence())
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = delta.main(["--format", "text", "--evidence-json", str(evidence_path)])
            self.assertEqual(exit_code, 0)
            self.assertIn("Balfrin Scientific Delta Report", buffer.getvalue())
            self.assertIn("scientific_delta_status: measured_existing_artifacts", buffer.getvalue())

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = delta.main(["--format", "json", "--evidence-json", str(evidence_path)])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())
        finally:
            evidence_path.unlink(missing_ok=True)

    def measured_evidence(self) -> dict[str, object]:
        return {
            "post_run_interpretation_gate_report": {
                "schema_version": "balfrin_post_run_interpretation_gate_v1",
                "interpretation_status": "measured_conditional_diagnostic",
                "artifact_acceptance_status": "accepted_conditional_diagnostic",
                "usable_as_conditional_diagnostic_artifact": True,
                "claim_boundaries": self.claim_boundaries(),
            },
            "same_scale_uncertainty_report": {
                "schema_version": "spatial_same_scale_uncertainty_v1",
                "spatial_uncertainty_status": "measured_existing_artifacts",
                "selected_layers": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
                "dominant_layers_by_mean_range": ["max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"],
                "layer_summaries": {
                    "max_kinetic_energy": {"closure_role": "closure_limiting"},
                    "max_jump_height": {"closure_role": "closure_limiting"},
                    "velocity_exceedance_5mps": {"closure_role": "deferrable"},
                },
            },
            "same_scale_stability_frontier_report": {
                "schema_version": "tschamut_same_scale_stability_frontier_v1",
                "frontier_status": "measured_existing_artifacts",
                "recommendation_class": "additional_probe_informative",
            },
            "closure_gap_deltas_report": {
                "schema_version": "tschamut_closure_gap_deltas_v1",
                "closure_gap_status": "measured_gaps_remain",
                "current_closure_status": "inconclusive",
                "current_interpretation_status": "inconclusive_conditional_diagnostic",
                "closure_limiting_layers": [
                    {"layer_key": "max_kinetic_energy"},
                    {"layer_key": "max_jump_height"},
                ],
                "deferrable_layers": [{"layer_key": "velocity_exceedance_5mps"}],
                "accepted_diagnostic_gap": {"status": "not_met"},
                "deferred_gap": {"status": "closer_to_deferred_than_no_go"},
                "no_go_gap": {"status": "not_supported_by_current_evidence"},
            },
            "hotspot_provenance_report": {
                "schema_version": "tschamut_hotspot_provenance_v1",
                "hotspot_provenance_status": "measured_existing_artifacts",
                "hotspot_provenance_classes": {
                    "max_kinetic_energy": "source_zone_and_scenario_committed_cell_lineage_unknown",
                    "max_jump_height": "source_zone_and_scenario_committed_cell_lineage_unknown",
                    "velocity_exceedance_5mps": "source_zone_and_scenario_committed_cell_lineage_unknown",
                },
                "attribution_limits": {
                    "cannot_attribute": [
                        "individual hotspot cells to specific trajectory_ids",
                        "cell-level causality from the run-level trajectory/deposition outputs alone",
                    ]
                },
            },
        }

    def claim_boundaries(self) -> dict[str, object]:
        return {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        }


if __name__ == "__main__":
    unittest.main()
