from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts import summarize_observed_runout_deposition_intake_contract as helper


class ObservedRunoutDepositionIntakeContractTests(unittest.TestCase):
    def test_contract_shape_and_field_requirements(self) -> None:
        report = helper.build_report()

        expected_keys = {
            "schema_version",
            "observed_runout_deposition_intake_status",
            "benchmark_intake_contract",
            "benchmark_intake_manifest",
            "field_requirement_map",
            "current_repo_state",
            "acquisition_blocker_matrix",
            "next_action_recommendation",
            "physical_credibility_gap_update",
            "fixture_acceptance_smoke",
            "dataset_role_classification",
            "claim_boundaries",
            "blocked_reason",
            "missing_inputs",
            "current_state_summary",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["schema_version"], helper.SCHEMA_VERSION)
        self.assertEqual(report["observed_runout_deposition_intake_status"], "blocked_missing_inputs")

        contract = report["benchmark_intake_contract"]
        self.assertEqual(contract["geometry"]["required_crs"], "EPSG:2056")
        self.assertIn("source_polygon", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("runout_axis_line", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("deposition_footprint_polygon", contract["geometry"]["allowed_geometry_roles"])
        self.assertIn("event_id", contract["event_source_metadata"]["required_fields"])
        self.assertIn("source_id", contract["event_source_metadata"]["required_fields"])
        self.assertIn("geometry_tolerance_m", contract["uncertainty"]["required_fields"])
        self.assertIn("runout_endpoint_error_m", contract["objective_function_placeholders"]["required_fields"])
        self.assertEqual(contract["objective_function_placeholders"]["objective_status"], "placeholder_only")
        self.assertEqual(report["physical_credibility_gap_update"]["current_physical_credibility_status"], "not_established")
        self.assertEqual(report["fixture_acceptance_smoke"]["fixture_status"], "fixture_backed")
        self.assertEqual(report["fixture_acceptance_smoke"]["fixture_classification"]["acceptance_status"], "ready")
        self.assertEqual(
            report["fixture_acceptance_smoke"]["fixture_classification"]["calibration_validation_role"]["calibration"],
            "not_allowed",
        )
        self.assertEqual(
            report["fixture_acceptance_smoke"]["fixture_classification"]["calibration_validation_role"]["validation"],
            "benchmark_intake_only",
        )
        self.assertFalse(report["fixture_acceptance_smoke"]["fixture_classification"]["holdout_eligibility"])
        self.assertEqual(report["fixture_acceptance_smoke"]["physical_evidence_status"], "not_established")
        self.assertEqual(
            report["physical_credibility_gap_update"]["physical_credibility_requirements_status"],
            "mapped_current_gaps",
        )
        self.assertEqual(
            report["next_action_recommendation"]["first_acquisition_action"],
            "Stage an independent observed runout/deposition benchmark manifest and the matching observed geometry record(s).",
        )
        self.assertEqual(report["benchmark_intake_manifest"]["manifest_status"], "report_only")
        self.assertEqual(len(report["acquisition_blocker_matrix"]), 6)
        self.assertEqual(report["next_action_recommendation"]["primary_track"], "data_acquisition")
        self.assertIn("geometry", report["acquisition_blocker_matrix"][0]["required_fields"])
        self.assertTrue(report["acquisition_blocker_matrix"][0]["acceptable_provenance"])
        self.assertFalse(report["acquisition_blocker_matrix"][0]["holdout_eligibility"])
        self.assertEqual(
            [entry["dataset_role"] for entry in report["dataset_role_classification"]],
            [
                "observed_runout_deposition_benchmark",
                "release_zone_provenance",
                "block_population_evidence",
                "calibration_inputs",
                "validation_inputs",
                "holdout_data",
            ],
        )
        self.assertEqual(report["dataset_role_classification"][4]["status"], "present")
        self.assertEqual(report["dataset_role_classification"][5]["status"], "present")
        self.assertEqual(report["acquisition_blocker_matrix"][4]["acceptance_status"], "ready")
        self.assertEqual(report["acquisition_blocker_matrix"][5]["acceptance_status"], "ready")
        self.assertEqual(
            report["benchmark_intake_manifest"]["calibration_validation_separation"]["validation_inputs_status"],
            "present",
        )
        self.assertEqual(
            report["benchmark_intake_manifest"]["calibration_validation_separation"]["holdout_data_status"],
            "present",
        )

        mapping = {entry["field_path"]: entry["physical_credibility_requirement"] for entry in report["field_requirement_map"]}
        self.assertEqual(mapping["geometry.geometry_role=runout_axis_line"], "observed_runout_deposition")
        self.assertEqual(mapping["geometry.geometry_role=deposition_footprint_polygon"], "observed_runout_deposition")
        self.assertEqual(mapping["geometry.geometry_encoding"], "observed_runout_deposition")
        self.assertEqual(mapping["event_source_metadata.observer"], "observed_runout_deposition")
        self.assertEqual(mapping["event_source_metadata.source_id"], "release_zone_evidence")
        self.assertEqual(mapping["event_source_metadata.source_reference_frame"], "terrain_and_context_evidence")
        self.assertEqual(mapping["uncertainty.qa_status"], "observed_runout_deposition")
        self.assertEqual(
            mapping["objective_function_placeholders.deposition_footprint_iou"],
            "calibration_data_and_objective_functions",
        )
        self.assertEqual(
            mapping["objective_function_placeholders.objective_status"],
            "calibration_data_and_objective_functions",
        )

    def test_blocked_current_state_and_boundaries_are_explicit(self) -> None:
        report = helper.build_report()

        current_state = report["current_repo_state"]
        self.assertEqual(current_state["benchmark_intake_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(current_state["calibration_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(current_state["benchmark_intake_dataset_status"], "absent")
        self.assertEqual(current_state["calibration_dataset_status"], "absent")
        self.assertEqual(report["dataset_role_classification"][0]["status"], "missing")
        self.assertEqual(report["dataset_role_classification"][1]["status"], "missing")
        self.assertEqual(report["dataset_role_classification"][2]["status"], "missing")
        self.assertEqual(report["dataset_role_classification"][3]["status"], "missing")
        self.assertEqual(report["dataset_role_classification"][4]["status"], "present")
        self.assertEqual(report["dataset_role_classification"][5]["status"], "present")
        self.assertIn(str(helper.EXPECTED_BENCHMARK_MANIFEST), current_state["missing_inputs"])
        self.assertIn(str(helper.EXPECTED_BENCHMARK_GEOMETRY), current_state["missing_inputs"])
        self.assertIn(str(helper.EXPECTED_CALIBRATION_ROOT), current_state["calibration_missing_inputs"])
        self.assertTrue(
            any(
                item["classification"] == "diagnostic_only" and item["status"] == "present"
                for item in current_state["adjacent_diagnostic_materials"]
            )
        )
        self.assertIn("no independent observed runout/deposition benchmark intake", report["blocked_reason"])
        self.assertFalse(report["claim_boundaries"]["calibration_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertEqual(report["physical_credibility_gap_update"]["current_physical_credibility_status"], "not_established")
        self.assertEqual(report["fixture_acceptance_smoke"]["physical_evidence_status"], "not_established")
        self.assertEqual(report["fixture_acceptance_smoke"]["fixture_classification"]["acceptance_status"], "ready")
        self.assertIn("missing_inputs", report["acquisition_blocker_matrix"][0]["blocking_reasons"])
        self.assertIn("missing_inputs", report["acquisition_blocker_matrix"][2]["blocking_reasons"])
        self.assertEqual(report["acquisition_blocker_matrix"][3]["acceptance_status"], "blocked_missing_inputs")
        self.assertEqual(report["acquisition_blocker_matrix"][4]["acceptance_status"], "ready")
        self.assertEqual(report["acquisition_blocker_matrix"][5]["acceptance_status"], "ready")

    def test_benchmark_ready_without_calibration_is_reported_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            benchmark_root = tmp_path / "validation/data/processed/observed_runout_deposition_benchmark"
            benchmark_root.mkdir(parents=True, exist_ok=True)
            (benchmark_root / "manifest.json").write_text("{}", encoding="utf-8")
            (benchmark_root / "observed_runout_deposition.geojson").write_text("{}", encoding="utf-8")

            with patch.object(helper, "EXPECTED_BENCHMARK_ROOT", benchmark_root), patch.object(
                helper, "EXPECTED_BENCHMARK_MANIFEST", benchmark_root / "manifest.json"
            ), patch.object(
                helper, "EXPECTED_BENCHMARK_GEOMETRY", benchmark_root / "observed_runout_deposition.geojson"
            ), patch.object(
                helper, "EXPECTED_BENCHMARK_INPUTS", (
                    benchmark_root / "manifest.json",
                    benchmark_root / "observed_runout_deposition.geojson",
                )
            ), patch.object(helper, "EXPECTED_CALIBRATION_ROOT", tmp_path / "validation/data/processed/observed_runout_deposition_calibration"):
                report = helper.build_report()

        current_state = report["current_repo_state"]
        self.assertEqual(report["observed_runout_deposition_intake_status"], "ready")
        self.assertIsNone(report["blocked_reason"])
        self.assertEqual(report["missing_inputs"], [])
        self.assertEqual(current_state["benchmark_intake_readiness_status"], "ready")
        self.assertEqual(current_state["calibration_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(current_state["benchmark_intake_dataset_status"], "present")
        self.assertEqual(current_state["calibration_dataset_status"], "absent")
        self.assertEqual(current_state["benchmark_intake_missing_inputs"], [])
        self.assertEqual(
            current_state["calibration_missing_inputs"],
            [str(tmp_path / "validation/data/processed/observed_runout_deposition_calibration")],
        )
        self.assertEqual(report["dataset_role_classification"][0]["status"], "present")
        self.assertEqual(report["dataset_role_classification"][1]["status"], "present")
        self.assertEqual(report["dataset_role_classification"][4]["status"], "present")
        self.assertEqual(report["dataset_role_classification"][5]["status"], "present")
        self.assertEqual(report["benchmark_intake_manifest"]["manifest_status"], "report_only")
        self.assertEqual(report["benchmark_intake_manifest"]["observed_geometry"]["required_crs"], "EPSG:2056")
        self.assertEqual(report["next_action_recommendation"]["primary_track"], "data_acquisition")
        self.assertEqual(
            report["current_state_summary"][0]["status"],
            "ready",
        )
        self.assertEqual(
            report["current_state_summary"][1]["status"],
            "blocked_missing_inputs",
        )

    def test_text_output_mentions_placeholder_and_split_readiness(self) -> None:
        text = helper.render_text_report(helper.build_report())

        self.assertIn("observed_runout_deposition_intake_status: blocked_missing_inputs", text)
        self.assertIn("benchmark_intake_manifest:", text)
        self.assertIn("fixture_acceptance_smoke:", text)
        self.assertIn("physical_credibility_gap_update:", text)
        self.assertIn("dataset_role_classification:", text)
        self.assertIn("geometry.geometry_role=runout_axis_line -> observed_runout_deposition", text)
        self.assertIn("objective_function_placeholders.runout_endpoint_error_m -> calibration_data_and_objective_functions", text)
        self.assertIn("benchmark_intake_readiness_status: blocked_missing_inputs", text)
        self.assertIn("calibration_readiness_status: blocked_missing_inputs", text)
        self.assertIn("benchmark_intake_dataset_status: absent", text)
        self.assertIn("physical_evidence_status: not_established", text)
        self.assertIn("No calibration dataset is available for objective fitting.", text)
        self.assertIn("first_acquisition_action: Stage an independent observed runout/deposition benchmark manifest", text)
        self.assertIn("acquisition_blocker_matrix:", text)
        self.assertIn("next_action_recommendation:", text)

    def test_all_missing_state_reports_benchmark_and_calibration_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            benchmark_root = tmp_path / "validation/data/processed/observed_runout_deposition_benchmark"
            calibration_root = tmp_path / "validation/data/processed/observed_runout_deposition_calibration"

            with patch.object(helper, "EXPECTED_BENCHMARK_ROOT", benchmark_root), patch.object(
                helper, "EXPECTED_BENCHMARK_MANIFEST", benchmark_root / "manifest.json"
            ), patch.object(
                helper, "EXPECTED_BENCHMARK_GEOMETRY", benchmark_root / "observed_runout_deposition.geojson"
            ), patch.object(
                helper, "EXPECTED_BENCHMARK_INPUTS", (
                    benchmark_root / "manifest.json",
                    benchmark_root / "observed_runout_deposition.geojson",
                )
            ), patch.object(helper, "EXPECTED_CALIBRATION_ROOT", calibration_root):
                report = helper.build_report()

        current_state = report["current_repo_state"]
        self.assertEqual(report["observed_runout_deposition_intake_status"], "blocked_missing_inputs")
        self.assertEqual(current_state["benchmark_intake_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(current_state["calibration_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(
            report["missing_inputs"],
            [
                str(benchmark_root / "manifest.json"),
                str(benchmark_root / "observed_runout_deposition.geojson"),
            ],
        )
        self.assertEqual(
            current_state["calibration_missing_inputs"],
            [str(calibration_root)],
        )

    def test_acquisition_fixture_classifier_accepts_complete_shape(self) -> None:
        fixture = helper.load_yaml_fixture(helper.EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
        classified = helper.classify_acquisition_fixture_row("observed_runout_deposition", fixture)

        self.assertEqual(classified["acceptance_status"], "ready")
        self.assertEqual(classified["missing_geometry_fields"], [])
        self.assertEqual(classified["missing_provenance_fields"], [])
        self.assertEqual(classified["missing_uncertainty_fields"], [])
        self.assertEqual(classified["calibration_validation_role_status"], "clear")
        self.assertEqual(classified["calibration_validation_role"]["calibration"], "not_allowed")
        self.assertEqual(classified["calibration_validation_role"]["validation"], "benchmark_intake_only")
        self.assertFalse(classified["holdout_eligibility"])

    def test_acquisition_fixture_classifier_flags_missing_geometry(self) -> None:
        fixture = helper.load_yaml_fixture(helper.EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
        fixture["geometry"].pop("geometry_value")
        classified = helper.classify_acquisition_fixture_row("observed_runout_deposition", fixture)

        self.assertEqual(classified["acceptance_status"], "blocked_schema_gap")
        self.assertIn("geometry_value", classified["missing_geometry_fields"])
        self.assertIn("missing_geometry", classified["blocking_reasons"])

    def test_acquisition_fixture_classifier_flags_missing_provenance(self) -> None:
        fixture = helper.load_yaml_fixture(helper.EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
        fixture["provenance"].pop("provenance_uri")
        classified = helper.classify_acquisition_fixture_row("observed_runout_deposition", fixture)

        self.assertEqual(classified["acceptance_status"], "blocked_schema_gap")
        self.assertIn("provenance_uri", classified["missing_provenance_fields"])
        self.assertIn("missing_provenance", classified["blocking_reasons"])

    def test_acquisition_fixture_classifier_flags_missing_uncertainty(self) -> None:
        fixture = helper.build_acquisition_fixture_template("validation_inputs")
        fixture["uncertainty"].pop("validation_scoring_notes")
        classified = helper.classify_acquisition_fixture_row("validation_inputs", fixture)

        self.assertEqual(classified["acceptance_status"], "blocked_schema_gap")
        self.assertIn("validation_scoring_notes", classified["missing_uncertainty_fields"])
        self.assertIn("missing_uncertainty", classified["blocking_reasons"])

    def test_acquisition_fixture_classifier_flags_unclear_calibration_role(self) -> None:
        fixture = helper.build_acquisition_fixture_template("holdout_data")
        fixture["calibration_validation_role"] = "unclear"
        classified = helper.classify_acquisition_fixture_row("holdout_data", fixture)

        self.assertEqual(classified["acceptance_status"], "blocked_role_unclear")
        self.assertEqual(classified["calibration_validation_role_status"], "unclear")
        self.assertIn("unclear_calibration_role", classified["blocking_reasons"])

    def test_acquisition_fixture_classifier_refuses_overclaimed_blocked_statuses(self) -> None:
        fixture = helper.build_acquisition_fixture_template("holdout_data")
        fixture["blocked_status"] = "blocked_missing_inputs"
        classified = helper.classify_acquisition_fixture_row("holdout_data", fixture)

        self.assertEqual(classified["acceptance_status"], "blocked_claim_overclaim")
        self.assertIn("overclaimed_blocked_status", classified["blocking_reasons"])

    def test_readiness_pack_writes_template_non_evidence_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "observed_runout_deposition_intake_readiness_pack_v1"
            report = helper.build_report(output_root=output_root)
            pack = report["readiness_pack"]
            acquisition_checklist_path = Path(pack["generated_files"]["acquisition_checklist"])
            dataset_inventory_path = Path(pack["generated_files"]["required_dataset_inventory"])
            geometry_template_path = Path(pack["generated_files"]["geometry_template"])
            provenance_template_path = Path(pack["generated_files"]["provenance_template"])
            objective_placeholders_path = Path(pack["generated_files"]["objective_function_placeholders"])
            blocked_no_evidence_report_path = Path(pack["generated_files"]["blocked_no_evidence_report"])
            template_manifest_path = Path(pack["generated_files"]["template_manifest"])
            benchmark_intake_manifest_path = Path(pack["generated_files"]["benchmark_intake_manifest"])
            validation_summary_path = Path(pack["generated_files"]["validation_summary"])

            self.assertEqual(pack["readiness_pack_status"], "written")
            self.assertEqual(pack["artifact_classification"], "template_non_evidence")
            self.assertEqual(Path(pack["readiness_pack_root"]), output_root)
            self.assertTrue(acquisition_checklist_path.exists())
            self.assertTrue(dataset_inventory_path.exists())
            self.assertTrue(geometry_template_path.exists())
            self.assertTrue(provenance_template_path.exists())
            self.assertTrue(objective_placeholders_path.exists())
            self.assertTrue(blocked_no_evidence_report_path.exists())
            self.assertTrue(template_manifest_path.exists())
            self.assertTrue(benchmark_intake_manifest_path.exists())
            self.assertTrue(validation_summary_path.exists())

            acquisition_checklist = acquisition_checklist_path.read_text(encoding="utf-8")
            dataset_inventory = yaml.safe_load(dataset_inventory_path.read_text(encoding="utf-8"))
            geometry_template = yaml.safe_load(geometry_template_path.read_text(encoding="utf-8"))
            provenance_template = yaml.safe_load(provenance_template_path.read_text(encoding="utf-8"))
            objective_placeholders = yaml.safe_load(objective_placeholders_path.read_text(encoding="utf-8"))
            blocked_no_evidence_report = blocked_no_evidence_report_path.read_text(encoding="utf-8")
            template_manifest = yaml.safe_load(template_manifest_path.read_text(encoding="utf-8"))
            benchmark_intake_manifest = yaml.safe_load(benchmark_intake_manifest_path.read_text(encoding="utf-8"))
            validation_summary = json.loads(validation_summary_path.read_text(encoding="utf-8"))

            self.assertEqual(template_manifest["artifact_classification"], "template_non_evidence")
            self.assertEqual(template_manifest["pack_status"], "dry_run_template")
            self.assertIn("observed_runout_deposition_intake_status", template_manifest)
            self.assertEqual(template_manifest["validation_boundary"], "diagnostic_only_until_independent_benchmark_is_staged")
            self.assertEqual(
                [entry["dataset_role"] for entry in dataset_inventory["dataset_roles"]],
                [
                    "independent_observed_runout_deposition_benchmark",
                    "release_zone_provenance",
                    "block_population_evidence",
                    "calibration_inputs",
                    "validation_inputs",
                    "holdout_data",
                ],
            )
            self.assertEqual(dataset_inventory["dataset_roles"][0]["status"], "missing")
            self.assertEqual(dataset_inventory["dataset_roles"][1]["status"], "missing")
            self.assertEqual(dataset_inventory["dataset_roles"][2]["status"], "missing")
            self.assertEqual(dataset_inventory["dataset_roles"][3]["status"], "missing")
            self.assertEqual(dataset_inventory["dataset_roles"][4]["status"], "present")
            self.assertEqual(dataset_inventory["dataset_roles"][5]["status"], "present")
            self.assertEqual(benchmark_intake_manifest["manifest_status"], "dry_run_template")
            self.assertEqual(
                benchmark_intake_manifest["physical_credibility_gap_update"]["current_physical_credibility_status"],
                "not_established",
            )
            self.assertFalse(benchmark_intake_manifest["calibration_validation_separation"]["calibration_validation_overlap_allowed"])
            self.assertEqual(geometry_template["artifact_classification"], "template_non_evidence")
            self.assertEqual(geometry_template["template_status"], "dry_run_template")
            self.assertIn("source_polygon", geometry_template["allowed_geometry_roles"])
            self.assertEqual(provenance_template["artifact_classification"], "template_non_evidence")
            self.assertIn("event_id", provenance_template["required_provenance_fields"])
            self.assertEqual(objective_placeholders["artifact_classification"], "template_non_evidence")
            self.assertEqual(objective_placeholders["objective_status"], "placeholder_only")
            self.assertFalse(objective_placeholders["fit_record_required"])
            self.assertEqual(validation_summary["artifact_classification"], "template_non_evidence")
            self.assertEqual(validation_summary["validation_status"], "ready")
            self.assertEqual(validation_summary["missing_files"], [])
            self.assertIn("independent observed runout/deposition benchmark manifest", acquisition_checklist)
            self.assertIn("First acquisition action:", acquisition_checklist)
            self.assertIn("Stage an independent observed runout/deposition benchmark manifest", acquisition_checklist)
            self.assertIn("Keep the benchmark intake separate from calibration data and fit targets.", acquisition_checklist)
            self.assertIn("blocked_missing_inputs", blocked_no_evidence_report)
            self.assertIn("Acquisition blocker matrix:", blocked_no_evidence_report)
            self.assertIn("Next-action recommendation:", blocked_no_evidence_report)
            self.assertIn("first_acquisition_action: Stage an independent observed runout/deposition benchmark manifest", blocked_no_evidence_report)
            self.assertIn("calibration_readiness_status: blocked_missing_inputs", blocked_no_evidence_report)
            self.assertIn("physical_credibility_requirements_status: mapped_current_gaps", blocked_no_evidence_report)
            self.assertIn("current_physical_credibility_status: not_established", blocked_no_evidence_report)
            self.assertIn("holdout_data: present", blocked_no_evidence_report)
            self.assertIn("This report is a blocker summary only and does not encode benchmark evidence.", blocked_no_evidence_report)

    def test_main_writes_pack_and_exits_successfully_when_output_root_is_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "observed_runout_deposition_intake_readiness_pack_v1"
            exit_code = helper.main(["--output-root", str(output_root), "--format", "json"])
            self.assertEqual(exit_code, 0)
            self.assertTrue((output_root / "template_manifest.yaml").exists())
            self.assertTrue((output_root / "benchmark_intake_manifest.yaml").exists())
            self.assertTrue((output_root / "blocked_no_evidence_report.md").exists())
            self.assertTrue((output_root / "validation_summary.json").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
