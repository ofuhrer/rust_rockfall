from __future__ import annotations

import unittest

from scripts import summarize_tschamut_conditional_diagnostic_interpretation as summary


class TschamutConditionalDiagnosticInterpretationTest(unittest.TestCase):
    def test_json_shape_includes_required_fields(self) -> None:
        report = summary.build_report()

        expected_keys = {
            "schema_version",
            "interpretation_status",
            "closure_status",
            "same_scale_readiness_status",
            "spatial_uncertainty_status",
            "dominant_scientific_blockers",
            "output_profile_status",
            "gis_cog_status",
            "runtime_scaling_status",
            "portability_status",
            "physical_credibility_status",
            "claim_boundaries",
            "recommended_next_decision",
            "scale_up_authorized",
            "operational_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "distributed_execution_authorized",
            "current_evidence",
            "evidence_sources",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["closure_status"], "inconclusive")
        self.assertEqual(report["interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(report["same_scale_readiness_status"], "ready")
        self.assertEqual(report["spatial_uncertainty_status"], "measured_existing_artifacts")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["annual_frequency_claims_allowed"])
        self.assertFalse(report["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["distributed_execution_authorized"])

    def test_closure_and_blocker_summary_remains_conservative(self) -> None:
        report = summary.build_report()

        blockers = report["dominant_scientific_blockers"]
        self.assertIn("closure_status_inconclusive", blockers)
        self.assertIn("spatial_uncertainty_support_nodata_dominates_closure", blockers)
        self.assertIn("max_kinetic_energy_closure_limiting", blockers)
        self.assertIn("max_jump_height_closure_limiting", blockers)
        self.assertIn("velocity_exceedance_5mps_deferrable", blockers)
        self.assertIn("summary_only_not_rebuildable", report["workflow_product_blockers"])
        self.assertIn("standard_gis_roots_cog_blocked", report["workflow_product_blockers"])
        self.assertIn("public_context_inputs_deferred", report["portability_blockers"])
        self.assertIn("physical_credibility_not_established", report["physical_credibility_blockers"])
        self.assertEqual(report["output_profile_status"]["target_summary_only"], "summary_only_not_rebuildable")
        self.assertEqual(report["output_profile_status"]["target_rebuildable_reduced"], "rebuildable_reduced_output")
        self.assertTrue(report["output_profile_status"]["command_plan_addressable"])
        self.assertEqual(report["gis_cog_status"]["standard_package_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["runtime_scaling_status"]["reducer_scaling_status"], "measured_existing_artifacts")
        self.assertTrue(report["runtime_scaling_status"]["local_single_job_sufficient_for_next_step"])
        self.assertFalse(report["runtime_scaling_status"]["distributed_execution_authorized"])
        self.assertEqual(report["portability_status"]["portability_preflight_status"], "deferred_public_context_inputs")
        self.assertEqual(report["physical_credibility_status"], "not_established")

    def test_missing_evidence_override_reports_blocked_status(self) -> None:
        report = summary.build_report({"missing_inputs": ["docs/missing.json"]})

        self.assertEqual(report["interpretation_status"], "blocked_missing_inputs")
        self.assertEqual(report["closure_status"], "blocked_missing_inputs")
        self.assertEqual(report["same_scale_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(report["physical_credibility_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_text_output_mentions_dominant_and_workflow_blockers(self) -> None:
        text = summary.render_text_report(summary.build_report())

        self.assertIn("interpretation_status: inconclusive_conditional_diagnostic", text)
        self.assertIn("dominant_scientific_blockers:", text)
        self.assertIn("max_kinetic_energy_closure_limiting", text)
        self.assertIn("workflow_product_blockers:", text)
        self.assertIn("summary_only_not_rebuildable", text)
        self.assertIn("portability_blockers:", text)
        self.assertIn("physical_credibility_blockers:", text)
        self.assertIn("scale_up_authorized: false", text)
        self.assertIn("operational_claims_allowed: false", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
