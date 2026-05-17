from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_target_area_interpretation.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_target_area_interpretation", SCRIPT_PATH)
assert SPEC is not None
interpretation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(interpretation)


class BalfrinTargetAreaInterpretationTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_override_report_remains_conservative_and_sectioned(self) -> None:
        report = interpretation.build_report(self.override_evidence())

        self.assertEqual(report["schema_version"], "balfrin_target_area_diagnostic_interpretation_v1")
        self.assertEqual(report["interpretation_status"], "mixed_provenance")
        self.assertEqual(report["diagnostic_acceptance_status"], "not_accepted")
        self.assertFalse(report["usable_as_conditional_diagnostic_artifact"])
        self.assertEqual(report["sections"]["execution"]["status"], "mixed_provenance")
        self.assertEqual(report["sections"]["gis"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["sections"]["physical_credibility"]["status"], "mapped_current_gaps")
        self.assertEqual(report["sections"]["baseline_comparison"]["status"], "baseline_unchanged")
        self.assertIn("does not improve the current Tschamut/Balfrin baseline", report["sections"]["baseline_comparison"]["comparison_summary"])
        self.assertIn("probe_metrics_report", [blocker["name"] for blocker in report["dominant_blockers"]])
        self.assertIn("claim_boundaries_explicit", [criterion["name"] for criterion in report["satisfied_workflow_criteria"]])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertIn("target-area diagnostic interpretation remains non-operational", report["claim_boundaries"]["notes"])

    def test_cli_emits_json_and_text_bundle(self) -> None:
        evidence_path = self.write_json(self.override_evidence())
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_target_area_interpretation_v1"
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = interpretation.main(
                        [
                            "--artifact-dir",
                            str(artifact_dir),
                            "--evidence-json",
                            str(evidence_path),
                        ]
                    )
                self.assertEqual(exit_code, 0)
                json_path = artifact_dir / "balfrin_target_area_diagnostic_interpretation_v1.json"
                text_path = artifact_dir / "balfrin_target_area_diagnostic_interpretation_v1.txt"
                self.assertTrue(json_path.exists())
                self.assertTrue(text_path.exists())
                json_report = json.loads(json_path.read_text(encoding="utf-8"))
                text_report = text_path.read_text(encoding="utf-8")
                self.assertEqual(json_report["interpretation_status"], "mixed_provenance")
                self.assertIn("Balfrin Target-Area Diagnostic Interpretation", text_report)
                self.assertIn("baseline_comparison:", text_report)
                self.assertIn("dominant_blockers:", text_report)
        finally:
            evidence_path.unlink(missing_ok=True)

    def test_missing_inputs_are_reported_explicitly(self) -> None:
        report = interpretation.build_report({"missing_inputs": ["target_area_evidence_bundle_report"]})

        self.assertEqual(report["interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["diagnostic_acceptance_status"], "blocked_missing_inputs")
        self.assertEqual(report["dominant_blockers"], ["target_area_evidence_bundle_report"])
        self.assertFalse(report["usable_as_conditional_diagnostic_artifact"])

    def override_evidence(self) -> dict[str, object]:
        return {
            "target_area_evidence_bundle_report": {
                "schema_version": "balfrin_target_area_evidence_bundle_v1",
                "pilot_id": "tschamut_public_pilot",
                "run_id": "tschamut_public_balfrin_target_area_demo_v1",
                "bundle_status": "mixed_provenance",
                "bundle_summary": {
                    "status": "mixed_provenance",
                    "summary": "Target-area Balfrin evidence combines a template-only handoff, a blocked probe-metrics report, and the measured canonical bundle; handoff=template_only, metrics=blocked_missing_inputs, claim boundaries remain false.",
                    "blockers": ["probe_metrics_report"],
                    "section_counts": {
                        "measured": 1,
                        "fixture_backed": 0,
                        "unavailable": 1,
                        "blocked_missing_inputs": 1,
                    },
                },
                "section_provenance_profile": [
                    {"section": "target_area_demo_handoff_report", "status": "template_only", "evidence_type": "unavailable"},
                    {"section": "probe_metrics_report", "status": "blocked_missing_inputs", "evidence_type": "blocked"},
                    {"section": "canonical_evidence_bundle", "status": "measured", "evidence_type": "measured"},
                ],
                "claim_boundaries": {
                    "operational_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                    "annual_frequency_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                    "scale_up_authorized": False,
                    "distributed_execution_authorized": False,
                    "notes": ["conditional diagnostics are not operational hazard maps"],
                },
                "probe_metrics_report": {
                    "report_status": "blocked_missing_inputs",
                    "metrics_contract_status": "blocked_missing_inputs",
                    "metrics_contract_missing_metrics": ["memory_peak_mb", "validation_output.bytes"],
                    "metrics_contract_ancillary_unavailable_metrics": ["validation_output_mode"],
                    "missing_inputs": ["metrics_contract_report"],
                    "summary": "mandatory metrics remain missing",
                },
                "source_paths": {"probe_metrics_report": "validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1/balfrin_probe_metrics_report_v1.json"},
            },
            "target_area_gis_scope_report": {
                "schema_version": "balfrin_target_area_gis_cog_scope_audit_v1",
                "report_status": "blocked_missing_inputs",
                "scope_classification": "blocked_missing_products",
                "demo_usability_status": "blocked_missing_products",
                "demo_usability_summary": "The target-area demo remains blocked because the converted COG package is missing or incomplete.",
                "target_area_demo_non_operational_boundaries": {
                    "operational_claims_allowed": False,
                    "hazard_layers_generated": False,
                    "cog_export_generated": False,
                    "scale_up_authorized": False,
                    "distributed_execution_authorized": False,
                    "annual_frequency_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                },
                "target_area_demo_cog_export_expectation": {
                    "status": "template_only",
                    "generated_now": False,
                    "hazard_layers_generated": False,
                    "cog_export_generated": False,
                    "downstream_template_only_command_ids": ["materialize_target_area_handoff_bundle"],
                    "summary": "The target-area handoff stops before hazard build; any GIS package or COG export remains a downstream template-only expectation.",
                },
                "claim_boundaries": {
                    "operational_claims_allowed": False,
                    "annual_frequency_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                    "scale_up_authorized": False,
                    "distributed_execution_authorized": False,
                },
                "source_paths": {"artifact_root": "hazard/results/tschamut_public_pilot/target_gate_v1"},
            },
            "tschamut_closure_report": {
                "schema_version": "tschamut_conditional_pilot_closure_v1",
                "closure_status": "inconclusive",
                "current_blockers": ["summary_only_not_rebuildable"],
                "current_follow_up_blockers": ["standard_gis_roots_cog_blocked"],
            },
            "tschamut_diagnostic_report": {
                "schema_version": "tschamut_conditional_diagnostic_interpretation_v1",
                "scientific_delta_status": "measured_existing_artifacts",
                "interpretation_status": "inconclusive_conditional_diagnostic",
                "canonical_interpretation": {
                    "summary": {"status": "inconclusive", "summary": "Measured Balfrin evidence remains bounded and does not reclassify the current inconclusive diagnostic interpretation."},
                    "interpretation_delta": {
                        "status": "leaves_current_inconclusive_interpretation_unchanged",
                        "summary": "Measured Balfrin evidence remains bounded and does not reclassify the current inconclusive diagnostic interpretation.",
                    },
                    "closure_semantics": {
                        "current_closure_status": "inconclusive",
                        "current_interpretation_status": "inconclusive_conditional_diagnostic",
                    },
                    "blockers": {
                        "closure_limiting_layers": {"layer_keys": ["max_kinetic_energy", "max_jump_height"], "deferrable_layer_keys": ["velocity_exceedance_5mps"]},
                        "runtime_output_sufficiency": {"status": "bounded_runtime_sufficient_output_blocked"},
                        "gis_product_scope": {"status": "gis_product_scope_blocked"},
                        "portability_status": {"status": "public_context_inputs_deferred"},
                        "physical_credibility_limits": {"status": "not_established"},
                    },
                },
            },
            "physical_credibility_report": {
                "schema_version": "physical_credibility_evidence_requirements_v1",
                "physical_credibility_requirements_status": "mapped_current_gaps",
                "current_physical_credibility_status": "not_established",
                "calibration_status": "missing",
                "validation_status": "partial",
                "evidence_acquisition_summary": {
                    "first_actionable_category": "observed_runout_deposition",
                    "deferred_category": "source_frequency_and_temporal_frequency_evidence",
                    "priority_order": [
                        "observed_runout_deposition",
                        "release_zone_evidence",
                        "independent_holdout_validation",
                        "calibration_data_and_objective_functions",
                        "multi_site_transfer_evidence",
                        "block_size_and_block_population_evidence",
                        "source_frequency_and_temporal_frequency_evidence",
                    ],
                },
                "claim_boundaries": {
                    "operational_claims_allowed": False,
                    "physical_probability_claims_allowed": False,
                    "annual_frequency_claims_allowed": False,
                    "risk_exposure_vulnerability_claims_allowed": False,
                    "scale_up_authorized": False,
                    "distributed_execution_authorized": False,
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
