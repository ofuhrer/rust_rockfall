from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_pilot_command_plan.py"
SECOND_SITE_CONFIG = ROOT / "tests" / "fixtures" / "second_site_public_geodata_preflight" / "chant_sura_fluelapass_candidate.yaml"


def load_module():
    spec = importlib.util.spec_from_file_location("test_generate_pilot_command_plan", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class PilotCommandPlanTest(unittest.TestCase):
    def _readiness_ready(self) -> dict[str, object]:
        return {"readiness_status": "ready"}

    def _readiness_blocked(self) -> dict[str, object]:
        return {"readiness_status": "blocked_missing_inputs"}

    def _output_profile_measured(self) -> dict[str, object]:
        return {
            "hazard_rebuild_output_profile_status": "measured",
            "profile_classifications": {
                "target_rebuildable_reduced": "rebuildable_reduced_output",
                "native_rebuildable_reduced_output": "rebuildable_reduced_output",
            },
        }

    def _second_site_deferred(self) -> dict[str, object]:
        return {
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Fluelapass",
            "portability_preflight_status": "deferred_public_context_inputs",
            "public_context_boundary_status": "deferred_public_context_inputs",
            "deferred_public_context_categories": ["swissimage_context", "swisstlm3d_context"],
            "public_context_product_requirements": [],
            "blocked_second_site_commands": [
                {"command_id": "second_site_benchmark_preparation_template", "blocked_status": "template_only"}
            ],
            "blocked_reason": "deferred_public_context_inputs",
            "claim_boundaries": {
                "scale_up_authorized": False,
                "operational_claims_allowed": False,
            },
        }

    def _contract_measured(self) -> dict[str, object]:
        return {"source_scenario_contract_audit_status": "measured"}

    def _fixture_report(self, site: str) -> dict[str, object]:
        with patch.object(MODULE.READINESS, "build_readiness_report", return_value=self._readiness_ready()), patch.object(
            MODULE.OUTPUT_PROFILE,
            "build_report",
            return_value=self._output_profile_measured(),
        ), patch.object(MODULE.PORTABILITY, "build_report", return_value=self._second_site_deferred()), patch.object(
            MODULE.CONTRACT,
            "build_report",
            return_value=self._contract_measured(),
        ):
            return MODULE.build_report(site, SECOND_SITE_CONFIG)

    def test_tschamut_plan_json_has_stable_groups(self) -> None:
        report = self._fixture_report("tschamut_same_scale")

        self.assertEqual(report["command_plan_status"], "ready")
        self.assertTrue(report["read_only"])
        self.assertEqual(report["tschamut_readiness_status"], "ready")
        self.assertEqual(
            [group["id"] for group in report["command_groups"]],
            [
                "readiness_checks",
                "case_generation",
                "validation_runs",
                "hazard_builds",
                "gis_cog_package_conversion",
                "convergence_comparisons",
                "output_profile_checks",
                "rebuildable_reduced_output",
                "context_inspection",
                "hazard_context_overlap",
                "uncertainty_summary",
            ],
        )
        self.assertEqual(
            report["command_group_keys"],
            [
                "tschamut_same_scale::readiness_checks",
                "tschamut_same_scale::case_generation",
                "tschamut_same_scale::validation_runs",
                "tschamut_same_scale::hazard_builds",
                "tschamut_same_scale::gis_cog_package_conversion",
                "tschamut_same_scale::convergence_comparisons",
                "tschamut_same_scale::output_profile_checks",
                "tschamut_same_scale::rebuildable_reduced_output",
                "tschamut_same_scale::context_inspection",
                "tschamut_same_scale::hazard_context_overlap",
                "tschamut_same_scale::uncertainty_summary",
            ],
        )
        self.assertIn("tschamut_case_generation", report["command_ids"])
        self.assertIn("tschamut_terrain_release_zone_candidate_metrics", report["command_ids"])
        self.assertIn("tschamut_target_hazard_build", report["command_ids"])
        self.assertIn("tschamut_output_profile_summary", report["command_ids"])
        self.assertIn("tschamut_standard_package_audit", report["command_ids"])
        self.assertIn("tschamut_converted_package_audit", report["command_ids"])
        self.assertIn("tschamut_package_cog_export", report["command_ids"])
        self.assertIn("tschamut_reduced_profile_validation", report["command_ids"])
        self.assertIn("tschamut_next_ensemble_feasibility_probe_template", report["command_ids"])
        self.assertIn("tschamut_reduced_profile_derivation", report["command_ids"])
        self.assertIn("tschamut_reduced_profile_hazard_rebuild", report["command_ids"])
        native_reduced_command = next(
            command for command in report["commands"] if command["id"] == "tschamut_reduced_profile_validation"
        )
        self.assertIn(
            "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            native_reduced_command["command"],
        )
        self.assertIn(
            "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            native_reduced_command["expected_inputs"],
        )
        self.assertTrue(native_reduced_command["may_produce_ignored_outputs"])
        self.assertEqual(report["tschamut_hazard_rebuild_output_profile_status"], "measured")
        self.assertEqual(report["tschamut_rebuildable_reduced_profile_classification"], "rebuildable_reduced_output")
        self.assertEqual(report["tschamut_native_rebuildable_reduced_profile_classification"], "rebuildable_reduced_output")
        self.assertIn("validation/private/tschamut_public_pilot/target_gate_v1_summary_only", report["ignored_output_paths"])
        self.assertIn("hazard/results/tschamut_public_pilot/gate_v1_cog_poc", report["ignored_output_paths"])
        self.assertIn(
            "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
            report["ignored_output_paths"],
        )
        self.assertEqual(report["blocked_template_commands"], ["tschamut_next_ensemble_feasibility_probe_template"])
        probe_template_command = next(
            command for command in report["commands"] if command["id"] == "tschamut_next_ensemble_feasibility_probe_template"
        )
        self.assertEqual(probe_template_command["blocked_reason"], "execution deferred until explicitly authorized")
        self.assertTrue(probe_template_command["may_produce_ignored_outputs"])
        self.assertIn(
            "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            probe_template_command["command"],
        )

        export_command = next(command for command in report["commands"] if command["id"] == "tschamut_package_cog_export")
        self.assertIn("scripts/build_hazard_layers.py", export_command["command"])
        self.assertIn("--export-cog", export_command["command"])
        self.assertIn("--jump-height-exceedance-m 0.5", export_command["command"])
        self.assertIn(
            "--cog-package-output-root hazard/results/tschamut_public_pilot/gate_v1_cog_export",
            export_command["command"],
        )
        self.assertEqual(export_command["cog_scope_intent"]["status"], "full_scope")
        self.assertEqual(export_command["cog_scope_intent"]["reference_layer_count"], 22)
        self.assertIn("jump_height_exceedance_0p5m", export_command["cog_scope_intent"]["reference_layer_names"])
        self.assertEqual(export_command["cog_scope_intent"]["omitted_layer_names"], [])
        self.assertEqual(
            export_command["cog_scope_intent"]["included_jump_height_layers_m"],
            [0.5, 1.0, 2.0],
        )
        self.assertIn("hazard/results/tschamut_public_pilot/gate_v1_cog_export", export_command["expected_outputs"])
        self.assertTrue(export_command["may_produce_ignored_outputs"])
        self.assertIn("hazard/results/tschamut_public_pilot/gate_v1_cog_export", export_command["ignored_output_paths"])

        converted_audit_command = next(command for command in report["commands"] if command["id"] == "tschamut_converted_package_audit")
        self.assertIn("scripts/audit_gis_cog_package_readiness.py", converted_audit_command["command"])
        self.assertIn("--converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_export", converted_audit_command["command"])
        self.assertTrue(converted_audit_command["read_only"])

    def test_tschamut_plan_remains_structured_when_readiness_is_blocked(self) -> None:
        with patch.object(MODULE.READINESS, "build_readiness_report", return_value=self._readiness_blocked()), patch.object(
            MODULE.OUTPUT_PROFILE,
            "build_report",
            return_value=self._output_profile_measured(),
        ), patch.object(MODULE.PORTABILITY, "build_report", return_value=self._second_site_deferred()), patch.object(
            MODULE.CONTRACT,
            "build_report",
            return_value=self._contract_measured(),
        ):
            report = MODULE.build_report("tschamut_same_scale", SECOND_SITE_CONFIG)

        self.assertEqual(report["tschamut_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(
            [group["id"] for group in report["command_groups"]],
            [
                "readiness_checks",
                "case_generation",
                "validation_runs",
                "hazard_builds",
                "gis_cog_package_conversion",
                "convergence_comparisons",
                "output_profile_checks",
                "rebuildable_reduced_output",
                "context_inspection",
                "hazard_context_overlap",
                "uncertainty_summary",
            ],
        )
        self.assertIn("tschamut_package_cog_export", report["command_ids"])
        self.assertIn("tschamut_reduced_profile_validation", report["command_ids"])
        self.assertIn("tschamut_next_ensemble_feasibility_probe_template", report["command_ids"])
        self.assertIn("tschamut_converted_package_audit", report["command_ids"])
        self.assertIn("tschamut_same_scale::rebuildable_reduced_output", report["command_group_keys"])
        self.assertEqual(report["blocked_template_commands"], ["tschamut_next_ensemble_feasibility_probe_template"])

    def test_second_site_plan_marks_templates_blocked(self) -> None:
        # The Chant Sura / Flüelapass plan is intentionally metadata-only here:
        # it should surface ignored output roots and blocked template commands
        # without requiring any staged public-context artifacts.
        report = self._fixture_report("chant_sura_fluelapass")

        self.assertEqual(report["second_site_portability_status"], "deferred_public_context_inputs")
        self.assertEqual(report["public_context_boundary_status"], "deferred_public_context_inputs")
        self.assertIn("swissimage_context", report["deferred_public_context_categories"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertEqual(
            [group["id"] for group in report["command_groups"]],
            [
                "readiness_checks",
                "multisite_source_scenario_contract",
                "second_site_case_generation",
                "second_site_release_plan",
                "second_site_portability",
            ],
        )
        self.assertIn("second_site_case_skeleton_dry_run", report["command_ids"])
        self.assertIn("second_site_release_plan_dry_run", report["command_ids"])
        self.assertIn("second_site_release_plan_execution_template", report["command_ids"])
        self.assertIn("second_site_aoi_acquisition_dry_run_planner", report["command_ids"])
        self.assertIn("second_site_acquisition_manifest_review", report["command_ids"])
        self.assertIn("validation/private/chant_sura_fluelapass_portability_example_v1", report["ignored_output_paths"])
        self.assertIn("hazard/results/chant_sura_fluelapass_portability_example_v1", report["ignored_output_paths"])
        self.assertEqual(
            set(report["blocked_template_commands"]),
            {
                "second_site_benchmark_preparation_template",
                "second_site_geodata_manifest_validation",
                "second_site_hazard_build_template",
                "second_site_release_plan_execution_template",
                "second_site_run_freeze_validation",
                "second_site_validation_template",
            },
        )
        self.assertTrue(report["blocked_second_site_commands"])
        self.assertEqual(report["blocked_second_site_commands"][0]["blocked_status"], "template_only")
        planner_command = next(
            command for command in report["commands"] if command["id"] == "second_site_aoi_acquisition_dry_run_planner"
        )
        self.assertFalse(planner_command["blocked_reason"])
        self.assertTrue(planner_command["read_only"])
        self.assertIn("plan_swisstopo_aoi_acquisition.py", planner_command["command"])
        self.assertIn(
            "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            planner_command["expected_inputs"],
        )
        dry_run_command = next(command for command in report["commands"] if command["id"] == "second_site_case_skeleton_dry_run")
        self.assertFalse(dry_run_command["blocked_reason"])
        self.assertFalse(dry_run_command["read_only"])
        self.assertFalse(dry_run_command["may_produce_ignored_outputs"])
        self.assertIn("/tmp/tb062_chant_sura_fluelapass_case_skeleton/chant_sura_fluelapass_dry_run_case_skeleton.yaml", dry_run_command["expected_outputs"])
        contract_plan = report["site_plans"]["chant_sura_fluelapass"]
        self.assertEqual(contract_plan["contract_audit_status"], "measured")
        self.assertFalse(contract_plan["read_only"])
        self.assertIn(
            "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            contract_plan["commands"][0]["expected_inputs"],
        )

    def test_all_site_group_keys_are_unique_when_group_ids_repeat(self) -> None:
        report = self._fixture_report("all")

        self.assertGreater(report["command_group_ids"].count("readiness_checks"), 1)
        self.assertEqual(len(report["command_group_keys"]), len(set(report["command_group_keys"])))
        self.assertIn("tschamut_same_scale::readiness_checks", report["command_group_keys"])
        self.assertIn("chant_sura_fluelapass::readiness_checks", report["command_group_keys"])
        self.assertIn("chant_sura_fluelapass::second_site_release_plan", report["command_group_keys"])
        self.assertIn("tschamut_same_scale::gis_cog_package_conversion", report["command_group_keys"])
        self.assertIn("tschamut_same_scale::rebuildable_reduced_output", report["command_group_keys"])

    def test_text_output_smoke(self) -> None:
        buffer = io.StringIO()
        with patch.object(MODULE.READINESS, "build_readiness_report", return_value=self._readiness_ready()), patch.object(
            MODULE.OUTPUT_PROFILE,
            "build_report",
            return_value=self._output_profile_measured(),
        ), patch.object(MODULE.PORTABILITY, "build_report", return_value=self._second_site_deferred()), patch.object(
            MODULE.CONTRACT,
            "build_report",
            return_value=self._contract_measured(),
        ), redirect_stdout(buffer):
            exit_code = MODULE.main(["--site", "tschamut_same_scale", "--format", "text"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("command_plan_status: ready", output)
        self.assertIn("blocked_template_commands:", output)
        self.assertIn("tschamut_same_scale::case_generation", output)
        self.assertIn("tschamut_same_scale::gis_cog_package_conversion", output)
        self.assertIn("tschamut_same_scale::rebuildable_reduced_output", output)
        self.assertIn("tschamut_next_ensemble_feasibility_probe_template", output)


if __name__ == "__main__":
    unittest.main()
