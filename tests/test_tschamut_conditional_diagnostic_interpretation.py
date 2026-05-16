from __future__ import annotations

import unittest

from scripts import summarize_tschamut_conditional_diagnostic_interpretation as summary


class TschamutConditionalDiagnosticInterpretationTest(unittest.TestCase):
    def _fixture_report(self) -> dict[str, object]:
        return {
            "schema_version": "tschamut_conditional_diagnostic_interpretation_v1",
            "interpretation_status": "inconclusive_conditional_diagnostic",
            "closure_status": "inconclusive",
            "same_scale_readiness_status": "ready",
            "spatial_uncertainty_status": "measured_existing_artifacts",
            "dominant_scientific_blockers": [
                "closure_status_inconclusive",
                "spatial_uncertainty_support_nodata_dominates_closure",
                "max_kinetic_energy_closure_limiting",
                "max_jump_height_closure_limiting",
                "velocity_exceedance_5mps_deferrable",
            ],
            "scientific_closure_blockers": [],
            "scientific_blockers": [
                "closure_status_inconclusive",
                "spatial_uncertainty_support_nodata_dominates_closure",
                "max_kinetic_energy_closure_limiting",
                "max_jump_height_closure_limiting",
                "velocity_exceedance_5mps_deferrable",
            ],
            "workflow_product_blockers": [
                "summary_only_not_rebuildable",
                "standard_gis_roots_cog_blocked",
            ],
            "workflow_blockers": [
                "summary_only_not_rebuildable",
                "standard_gis_roots_cog_blocked",
            ],
            "product_path_statuses": {
                "legacy_summary_only_status": "summary_only_not_rebuildable",
                "native_rebuildable_reduced_status": "rebuildable_reduced_output",
                "standard_gis_root_status": "gis_package_ready_cog_blocked",
                "converted_package_readiness_status": "converted_package_ready",
                "any_converted_package_ready": True,
                "command_plan_addressable": {
                    "native_rebuildable_reduced_output": True,
                    "gis_cog_package_conversion": True,
                },
            },
            "workflow_mitigations": [
                {
                    "path": "native_rebuildable_reduced_output",
                    "status": "rebuildable_reduced_output",
                    "mitigates": ["summary_only_not_rebuildable"],
                    "command_plan_addressable": True,
                },
                {
                    "path": "converted_gis_cog_package",
                    "status": "converted_package_ready",
                    "mitigates": ["standard_gis_roots_cog_blocked"],
                    "command_plan_addressable": True,
                },
            ],
            "portability_blockers": ["public_context_inputs_deferred"],
            "physical_credibility_blockers": ["physical_credibility_not_established"],
            "output_profile_status": {
                "target_summary_only": "summary_only_not_rebuildable",
                "legacy_summary_only_status": "summary_only_not_rebuildable",
                "target_rebuildable_reduced": "rebuildable_reduced_output",
                "native_rebuildable_reduced_status": "rebuildable_reduced_output",
                "command_plan_addressable": True,
            },
            "gis_cog_status": {
                "standard_package_status": "gis_package_ready_cog_blocked",
                "converted_package_readiness_status": "converted_package_ready",
                "any_converted_package_ready": True,
            },
            "runtime_scaling_status": {
                "reducer_scaling_status": "measured_existing_artifacts",
                "local_single_job_sufficient_for_next_step": True,
                "distributed_execution_authorized": False,
            },
            "portability_status": {
                "portability_preflight_status": "deferred_public_context_inputs",
            },
            "physical_credibility_status": "not_established",
            "claim_boundaries": {
                "scale_up_authorized": False,
                "operational_claims_allowed": False,
                "annual_frequency_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
                "distributed_execution_authorized": False,
            },
            "recommended_next_decision": "Retain the conditional diagnostic interpretation as inconclusive.",
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "distributed_execution_authorized": False,
            "current_evidence": {
                "closure": {
                    "stability_zone_summary": {
                        "stability_zone_status": "measured_existing_artifacts",
                        "overall_closure_role_change": "no_change",
                    }
                }
            },
            "evidence_sources": [],
        }

    def _fixture_override(self) -> dict[str, object]:
        return {"diagnostic_interpretation_report": self._fixture_report()}

    def test_json_shape_includes_required_fields(self) -> None:
        report = summary.build_report(self._fixture_override())

        expected_keys = {
            "schema_version",
            "interpretation_status",
            "closure_status",
            "same_scale_readiness_status",
            "spatial_uncertainty_status",
            "dominant_scientific_blockers",
            "scientific_blockers",
            "workflow_product_blockers",
            "workflow_blockers",
            "product_path_statuses",
            "workflow_mitigations",
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
        report = summary.build_report(self._fixture_override())

        blockers = report["dominant_scientific_blockers"]
        self.assertIn("closure_status_inconclusive", blockers)
        self.assertIn("spatial_uncertainty_support_nodata_dominates_closure", blockers)
        self.assertIn("max_kinetic_energy_closure_limiting", blockers)
        self.assertIn("max_jump_height_closure_limiting", blockers)
        self.assertIn("velocity_exceedance_5mps_deferrable", blockers)
        self.assertEqual(report["scientific_blockers"], blockers)
        self.assertIn("summary_only_not_rebuildable", report["workflow_product_blockers"])
        self.assertIn("standard_gis_roots_cog_blocked", report["workflow_product_blockers"])
        self.assertEqual(report["workflow_blockers"], report["workflow_product_blockers"])
        self.assertEqual(report["product_path_statuses"]["legacy_summary_only_status"], "summary_only_not_rebuildable")
        self.assertEqual(report["product_path_statuses"]["native_rebuildable_reduced_status"], "rebuildable_reduced_output")
        self.assertEqual(report["product_path_statuses"]["standard_gis_root_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["product_path_statuses"]["converted_package_readiness_status"], "converted_package_ready")
        self.assertTrue(report["product_path_statuses"]["any_converted_package_ready"])
        self.assertTrue(report["product_path_statuses"]["command_plan_addressable"]["native_rebuildable_reduced_output"])
        self.assertTrue(report["product_path_statuses"]["command_plan_addressable"]["gis_cog_package_conversion"])
        mitigation_paths = {item["path"] for item in report["workflow_mitigations"]}
        self.assertIn("native_rebuildable_reduced_output", mitigation_paths)
        self.assertIn("converted_gis_cog_package", mitigation_paths)
        self.assertIn("public_context_inputs_deferred", report["portability_blockers"])
        self.assertIn("physical_credibility_not_established", report["physical_credibility_blockers"])
        self.assertEqual(report["output_profile_status"]["target_summary_only"], "summary_only_not_rebuildable")
        self.assertEqual(report["output_profile_status"]["target_rebuildable_reduced"], "rebuildable_reduced_output")
        self.assertEqual(report["output_profile_status"]["legacy_summary_only_status"], "summary_only_not_rebuildable")
        self.assertEqual(report["output_profile_status"]["native_rebuildable_reduced_status"], "rebuildable_reduced_output")
        self.assertTrue(report["output_profile_status"]["command_plan_addressable"])
        self.assertEqual(report["gis_cog_status"]["standard_package_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["gis_cog_status"]["converted_package_readiness_status"], "converted_package_ready")
        self.assertTrue(report["gis_cog_status"]["any_converted_package_ready"])
        self.assertEqual(report["runtime_scaling_status"]["reducer_scaling_status"], "measured_existing_artifacts")
        self.assertTrue(report["runtime_scaling_status"]["local_single_job_sufficient_for_next_step"])
        self.assertFalse(report["runtime_scaling_status"]["distributed_execution_authorized"])
        self.assertEqual(report["portability_status"]["portability_preflight_status"], "deferred_public_context_inputs")
        self.assertEqual(report["physical_credibility_status"], "not_established")
        self.assertEqual(
            report["current_evidence"]["closure"]["stability_zone_summary"]["stability_zone_status"],
            "measured_existing_artifacts",
        )
        self.assertEqual(
            report["current_evidence"]["closure"]["stability_zone_summary"]["overall_closure_role_change"],
            "no_change",
        )

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
        text = summary.render_text_report(summary.build_report(self._fixture_override()))

        self.assertIn("interpretation_status: inconclusive_conditional_diagnostic", text)
        self.assertIn("scientific_blockers:", text)
        self.assertIn("max_kinetic_energy_closure_limiting", text)
        self.assertIn("workflow_blockers:", text)
        self.assertIn("summary_only_not_rebuildable", text)
        self.assertIn("legacy_summary_only_status", text)
        self.assertIn("native_rebuildable_reduced_status", text)
        self.assertIn("product_path_statuses:", text)
        self.assertIn("workflow_mitigations:", text)
        self.assertIn("portability_blockers:", text)
        self.assertIn("physical_credibility_blockers:", text)
        self.assertIn("stability_zone_summary", text)
        self.assertIn("converted_package_readiness_status", text)
        self.assertIn("scale_up_authorized: false", text)
        self.assertIn("operational_claims_allowed: false", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
