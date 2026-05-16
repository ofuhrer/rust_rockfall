from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
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
    def test_tschamut_plan_json_has_stable_groups(self) -> None:
        report = MODULE.build_report("tschamut_same_scale", SECOND_SITE_CONFIG)

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
        self.assertIn("tschamut_target_hazard_build", report["command_ids"])
        self.assertIn("tschamut_output_profile_summary", report["command_ids"])
        self.assertIn("tschamut_standard_package_audit", report["command_ids"])
        self.assertIn("tschamut_package_cog_conversion", report["command_ids"])
        self.assertIn("tschamut_converted_package_audit", report["command_ids"])
        self.assertIn("tschamut_reduced_profile_validation", report["command_ids"])
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
        self.assertIn("validation/private/tschamut_public_pilot/target_gate_v1_summary_only", report["ignored_output_paths"])
        self.assertIn("hazard/results/tschamut_public_pilot/gate_v1_cog_poc", report["ignored_output_paths"])
        self.assertIn(
            "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
            report["ignored_output_paths"],
        )
        self.assertEqual(report["blocked_template_commands"], [])

        conversion_command = next(command for command in report["commands"] if command["id"] == "tschamut_package_cog_conversion")
        self.assertIn("scripts/convert_same_scale_package_to_cog.py", conversion_command["command"])
        self.assertIn("--output-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc", conversion_command["command"])
        self.assertTrue(conversion_command["may_produce_ignored_outputs"])
        self.assertIn("hazard/results/tschamut_public_pilot/gate_v1_cog_poc", conversion_command["ignored_output_paths"])

        converted_audit_command = next(command for command in report["commands"] if command["id"] == "tschamut_converted_package_audit")
        self.assertIn("scripts/audit_gis_cog_package_readiness.py", converted_audit_command["command"])
        self.assertIn("--converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc", converted_audit_command["command"])
        self.assertTrue(converted_audit_command["read_only"])

    def test_second_site_plan_marks_templates_blocked(self) -> None:
        report = MODULE.build_report("chant_sura_fluelapass", SECOND_SITE_CONFIG)

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
                "second_site_portability",
            ],
        )
        self.assertIn("second_site_acquisition_manifest_review", report["command_ids"])
        self.assertIn("validation/private/chant_sura_fluelapass_portability_example_v1", report["ignored_output_paths"])
        self.assertIn("hazard/results/chant_sura_fluelapass_portability_example_v1", report["ignored_output_paths"])
        self.assertEqual(
            set(report["blocked_template_commands"]),
            {
                "second_site_benchmark_preparation_template",
                "second_site_geodata_manifest_validation",
                "second_site_hazard_build_template",
                "second_site_run_freeze_validation",
                "second_site_validation_template",
            },
        )
        self.assertTrue(report["blocked_second_site_commands"])
        self.assertEqual(report["blocked_second_site_commands"][0]["blocked_status"], "template_only")
        contract_plan = report["site_plans"]["chant_sura_fluelapass"]
        self.assertEqual(contract_plan["contract_audit_status"], "measured")
        self.assertFalse(contract_plan["read_only"])
        self.assertIn(
            "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            contract_plan["commands"][0]["expected_inputs"],
        )

    def test_all_site_group_keys_are_unique_when_group_ids_repeat(self) -> None:
        report = MODULE.build_report("all", SECOND_SITE_CONFIG)

        self.assertGreater(report["command_group_ids"].count("readiness_checks"), 1)
        self.assertEqual(len(report["command_group_keys"]), len(set(report["command_group_keys"])))
        self.assertIn("tschamut_same_scale::readiness_checks", report["command_group_keys"])
        self.assertIn("chant_sura_fluelapass::readiness_checks", report["command_group_keys"])
        self.assertIn("tschamut_same_scale::gis_cog_package_conversion", report["command_group_keys"])
        self.assertIn("tschamut_same_scale::rebuildable_reduced_output", report["command_group_keys"])

    def test_text_output_smoke(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--site", "tschamut_same_scale", "--format", "text"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("command_plan_status: ready", output)
        self.assertIn("blocked_template_commands:", output)
        self.assertIn("tschamut_same_scale::case_generation", output)
        self.assertIn("tschamut_same_scale::gis_cog_package_conversion", output)
        self.assertIn("tschamut_same_scale::rebuildable_reduced_output", output)


if __name__ == "__main__":
    unittest.main()
