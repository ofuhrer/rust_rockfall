from __future__ import annotations

import unittest

from scripts import map_physical_credibility_evidence_requirements as helper


class PhysicalCredibilityEvidenceRequirementsTest(unittest.TestCase):
    def test_json_shape_and_current_statuses(self) -> None:
        report = helper.build_report()

        expected_keys = {
            "schema_version",
            "physical_credibility_requirements_status",
            "current_physical_credibility_status",
            "calibration_status",
            "validation_status",
            "release_zone_first_missing_input",
            "release_zone_blockers",
            "release_zone_future_gate_prerequisites",
            "evidence_requirement_categories",
            "evidence_acquisition_matrix",
            "candidate_data_sources",
            "missing_acquisition_classes",
            "calibration_split_requirements",
            "holdout_validation_requirements",
            "source_frequency_requirements",
            "intensity_frequency_status",
            "layer_credibility_boundaries",
            "block_population_first_missing_input",
            "block_population_blockers",
            "block_population_future_gate_prerequisites",
            "source_frequency_first_missing_input",
            "source_frequency_blockers",
            "source_frequency_future_gate_prerequisites",
            "source_frequency_sampling_weights_are_not_frequency_evidence",
            "physical_evidence_triage",
            "evidence_acquisition_summary",
            "claim_boundaries",
            "blocked_reason",
            "missing_inputs",
            "current_evidence_summary",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["physical_credibility_requirements_status"], "mapped_current_gaps")
        self.assertEqual(report["current_physical_credibility_status"], "not_established")
        self.assertEqual(report["calibration_status"], "missing")
        self.assertEqual(report["validation_status"], "partial")
        self.assertEqual(report["intensity_frequency_status"], "deferred_unsupported")
        self.assertEqual(report["release_zone_first_missing_input"], "site_specific_release_zone_geometry_package")
        self.assertTrue(report["release_zone_blockers"])
        self.assertTrue(report["release_zone_future_gate_prerequisites"])
        self.assertEqual(
            [entry["layer_key"] for entry in report["layer_credibility_boundaries"]],
            [
                "reach_probability",
                "deposition_density",
                "max_kinetic_energy",
                "max_jump_height",
                "conditional_intensity_exceedance_layers",
            ],
        )
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])
        self.assertEqual(report["evidence_acquisition_summary"]["first_actionable_category"], "observed_runout_deposition")
        self.assertEqual(report["evidence_acquisition_summary"]["deferred_category"], "source_frequency_and_temporal_frequency_evidence")
        self.assertEqual(
            [entry["classification"] for entry in report["physical_evidence_triage"]],
            ["candidate", "candidate", "defer"],
        )
        self.assertEqual(
            [entry["first_missing_input"] for entry in report["physical_evidence_triage"]],
            [
                "site_specific_release_zone_geometry_package",
                "block_size_survey_or_photogrammetry_census",
                "historical_rockfall_event_catalogue",
            ],
        )
        self.assertEqual(
            report["evidence_acquisition_summary"]["priority_order"],
            [
                "observed_runout_deposition",
                "release_zone_evidence",
                "independent_holdout_validation",
                "calibration_data_and_objective_functions",
                "multi_site_transfer_evidence",
                "block_size_and_block_population_evidence",
                "source_frequency_and_temporal_frequency_evidence",
            ],
        )
        self.assertEqual(report["block_population_first_missing_input"], "block_size_survey_or_photogrammetry_census")
        self.assertEqual(report["source_frequency_first_missing_input"], "historical_rockfall_event_catalogue")
        self.assertTrue(report["block_population_blockers"])
        self.assertTrue(report["source_frequency_blockers"])
        self.assertTrue(report["source_frequency_sampling_weights_are_not_frequency_evidence"])

    def test_requirement_categories_and_candidate_sources_are_distinct(self) -> None:
        report = helper.build_report()
        categories = {entry["category"]: entry for entry in report["evidence_requirement_categories"]}
        matrix = {entry["category"]: entry for entry in report["evidence_acquisition_matrix"]}
        current_summary_by_class = {
            entry.get("artifact_class"): entry
            for entry in report["current_evidence_summary"]
            if entry.get("artifact_class")
        }
        self.assertEqual(
            set(categories),
            {
                "observed_runout_deposition",
                "release_zone_evidence",
                "block_size_and_block_population_evidence",
                "terrain_and_context_evidence",
                "source_frequency_and_temporal_frequency_evidence",
                "calibration_data_and_objective_functions",
                "independent_holdout_validation",
                "multi_site_transfer_evidence",
            },
        )
        self.assertEqual(categories["observed_runout_deposition"]["current_repo_evidence_status"], "partial")
        self.assertEqual(categories["release_zone_evidence"]["acquisition_classification"], "candidate")
        self.assertEqual(categories["release_zone_evidence"]["first_missing_input"], "site_specific_release_zone_geometry_package")
        self.assertEqual(categories["block_size_and_block_population_evidence"]["current_repo_evidence_status"], "missing")
        self.assertEqual(categories["block_size_and_block_population_evidence"]["first_missing_input"], "block_size_survey_or_photogrammetry_census")
        self.assertEqual(categories["block_size_and_block_population_evidence"]["acquisition_classification"], "candidate")
        self.assertEqual(categories["source_frequency_and_temporal_frequency_evidence"]["first_missing_input"], "historical_rockfall_event_catalogue")
        self.assertEqual(categories["source_frequency_and_temporal_frequency_evidence"]["acquisition_classification"], "defer")
        self.assertTrue(categories["source_frequency_and_temporal_frequency_evidence"]["conditional_sampling_weights_are_not_frequency_evidence"])
        self.assertEqual(categories["independent_holdout_validation"]["current_repo_evidence_status"], "partial")
        self.assertEqual(matrix["observed_runout_deposition"]["priority"], 1)
        self.assertEqual(matrix["observed_runout_deposition"]["current_repo_gap"], helper.EVIDENCE_ACQUISITION_PRIORITY_BLUEPRINTS[0]["current_repo_gap"])
        self.assertTrue(matrix["observed_runout_deposition"]["required_data"])
        self.assertTrue(matrix["observed_runout_deposition"]["current_repo_evidence"])
        self.assertTrue(matrix["observed_runout_deposition"]["future_field_or_reference_data_needs"])
        self.assertEqual(matrix["release_zone_evidence"]["acquisition_classification"], "candidate")
        self.assertEqual(matrix["release_zone_evidence"]["first_missing_input"], "site_specific_release_zone_geometry_package")
        self.assertEqual(matrix["block_size_and_block_population_evidence"]["first_missing_input"], "block_size_survey_or_photogrammetry_census")
        self.assertEqual(matrix["block_size_and_block_population_evidence"]["acquisition_classification"], "candidate")
        self.assertEqual(matrix["source_frequency_and_temporal_frequency_evidence"]["first_missing_input"], "historical_rockfall_event_catalogue")
        self.assertEqual(matrix["source_frequency_and_temporal_frequency_evidence"]["acquisition_classification"], "defer")
        self.assertTrue(matrix["source_frequency_and_temporal_frequency_evidence"]["conditional_sampling_weights_are_not_frequency_evidence"])
        self.assertTrue(categories["source_frequency_and_temporal_frequency_evidence"]["future_acquisition_classes"])
        self.assertIn(
            "independent_holdout_field_deposition_runout_benchmark",
            report["missing_acquisition_classes"],
        )
        self.assertIn("block_population_count_or_size_class_record", report["missing_acquisition_classes"])
        self.assertIn("historical_rockfall_event_catalogue", report["missing_acquisition_classes"])
        self.assertTrue(
            any(
                source["source_kind"] == "current_repo_evidence"
                and source["label"].startswith("Tschamut 2014")
                for source in report["candidate_data_sources"]
            )
        )
        self.assertTrue(
            any(
                source["source_kind"] == "future_acquisition_class"
                and source["label"] == "Historical rockfall event catalogue"
                for source in report["candidate_data_sources"]
            )
        )
        self.assertEqual(current_summary_by_class["aoi_cache_verification_and_terrain_preprocessing"]["status"], "workflow_provenance_only")
        self.assertEqual(current_summary_by_class["aoi_release_zone_candidates"]["status"], "workflow_provenance_only")
        self.assertEqual(current_summary_by_class["aoi_scenario_tables"]["status"], "workflow_provenance_only")
        self.assertEqual(current_summary_by_class["aoi_case_skeletons"]["status"], "workflow_provenance_only")
        self.assertEqual(
            current_summary_by_class["aoi_case_skeletons"]["physical_claim_boundary"],
            "not_calibration_or_validation_evidence",
        )
        self.assertIn(
            "AOI cache verification report",
            {source["label"] for source in categories["terrain_and_context_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "AOI terrain preprocessing report",
            {source["label"] for source in categories["terrain_and_context_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "AOI release-zone candidate metrics report",
            {source["label"] for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "AOI candidate release-zone products",
            {source["label"] for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "Release-zone provenance intake bridge",
            {source["label"] for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertEqual(
            next(
                source
                for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]
                if source["label"] == "Chant Sura / Flüelapass candidate acquisition manifest"
            )["status"],
            "partial",
        )
        self.assertIn(
            "deferred public-context bundle",
            next(
                source
                for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]
                if source["label"] == "Chant Sura / Flüelapass candidate acquisition manifest"
            )["notes"].lower(),
        )
        self.assertIn(
            "Release-candidate physical-meaning firewall",
            {source["label"] for source in categories["release_zone_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "AOI scenario-table dry-run plan",
            {source["label"] for source in categories["source_frequency_and_temporal_frequency_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertIn(
            "Candidate source-zone scenario stress report",
            {source["label"] for source in categories["source_frequency_and_temporal_frequency_evidence"]["current_repo_evidence_sources"]},
        )
        self.assertEqual(report["block_population_blockers"][0]["first_missing_input"], "block_size_survey_or_photogrammetry_census")
        self.assertEqual(report["source_frequency_blockers"][0]["first_missing_input"], "historical_rockfall_event_catalogue")
        self.assertIn(
            "AOI dry-run case skeleton bundle",
            {source["label"] for source in categories["calibration_data_and_objective_functions"]["current_repo_evidence_sources"]},
        )
        self.assertTrue(
            any("conditional workflow outputs" in item.lower() for item in report["source_frequency_requirements"][0]["current_repo_evidence"])
        )
        self.assertTrue(
            any("not a source-occurrence catalogue" in item.lower() for item in report["source_frequency_requirements"][0]["current_repo_evidence"])
        )

    def test_text_output_names_required_evidence_categories(self) -> None:
        text = helper.render_text_report(helper.build_report())
        self.assertIn("Tschamut", text)
        self.assertIn("Chant Sura", text)
        self.assertIn("block_size_and_block_population_evidence", text)
        self.assertIn("source_frequency_and_temporal_frequency_evidence", text)
        self.assertIn("independent_holdout_validation", text)
        self.assertIn("evidence_acquisition_matrix", text)
        self.assertIn("priority 1: observed_runout_deposition", text)
        self.assertIn("layer_credibility_boundaries", text)
        self.assertIn("max_kinetic_energy", text)
        self.assertIn("workflow_provenance_only", text)
        self.assertIn("Release-candidate and scenario-table firewalls", text)

    def test_missing_inputs_return_blocked_status(self) -> None:
        report = helper.build_report({"missing_inputs": ["docs/missing.json"]})

        self.assertEqual(report["physical_credibility_requirements_status"], "blocked_missing_inputs")
        self.assertEqual(report["current_physical_credibility_status"], "blocked_missing_inputs")
        self.assertEqual(report["calibration_status"], "blocked_missing_inputs")
        self.assertEqual(report["validation_status"], "blocked_missing_inputs")
        self.assertEqual(report["intensity_frequency_status"], "blocked_missing_inputs")
        self.assertEqual(report["layer_credibility_boundaries"], [])
        self.assertEqual(report["evidence_acquisition_matrix"], [])
        self.assertEqual(report["evidence_acquisition_summary"]["first_actionable_category"], None)
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
