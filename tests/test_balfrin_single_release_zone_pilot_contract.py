from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_single_release_zone_pilot_contract.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_single_release_zone_pilot_contract", SCRIPT_PATH)
assert SPEC is not None
contract_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(contract_script)


class BalfrinSingleReleaseZonePilotContractTests(unittest.TestCase):
    def load_contract(self, path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def write_contract(self, contract: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        with tmp:
            yaml.safe_dump(contract, tmp, sort_keys=False)
        return Path(tmp.name)

    def test_current_contract_is_ready_and_names_the_non_operational_boundary(self) -> None:
        report = contract_script.build_report()

        self.assertEqual(report["schema_version"], "balfrin_single_release_zone_pilot_contract_v1")
        self.assertEqual(report["contract_status"], "ready_for_balfrin_single_release_zone_pilot")
        self.assertEqual(report["minimal_demo_status"], "ready")
        self.assertEqual(report["conditional_diagnostic_feasibility_status"], "ready_for_balfrin_single_release_zone_pilot")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["physical_frequency_authorized"])
        self.assertIn("summarize_contract_json", [command["command_id"] for command in report["minimal_demo_contract"]["commands"]])
        self.assertIn("contract_table", [item["visual_product_id"] for item in report["minimal_demo_contract"]["visual_products"]])
        self.assertIn("scientific_closure", report["minimal_demo_contract"]["non_goals"])
        self.assertEqual(report["release_zone_scope"]["release_zone_count"], 1)
        self.assertEqual(report["release_zone_scope"]["trajectory_count_target"], 1000)
        self.assertEqual(report["validation_output"]["validation_output_mode"], "rebuildable_reduced_output")
        self.assertEqual(report["validation_output"]["hazard_output_profile"], "scalable_conditional")
        self.assertIn("conditional_intensity_exceedance", report["hazard_layer_products"])
        self.assertIn("single_job_balfrin_slurm", report["balfrin_resource_assumptions"]["execution_boundary"])
        self.assertIn("physical_probability", report["no_go_boundaries"])
        self.assertIn("scientific_closure", report["no_go_boundaries"])
        self.assertEqual(report["missing_required_inputs"], [])
        self.assertEqual(report["scope_creep_reasons"], [])
        self.assertIn("one release zone is frozen for the next Balfrin minimal demo", report["contract_boundary_summary"][0])

    def test_missing_required_input_blocks_contract_and_keeps_authorization_false(self) -> None:
        contract = self.load_contract(ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml")
        contract["minimal_demo_contract"]["required_inputs"][0] = "docs/does-not-exist-for-balfrin-contract.md"
        contract["required_inputs"][0] = "docs/does-not-exist-for-balfrin-contract.md"

        path = self.write_contract(contract)
        try:
            report = contract_script.build_report(path)
        finally:
            path.unlink(missing_ok=True)

        self.assertEqual(report["contract_status"], "blocked_missing_inputs")
        self.assertEqual(report["minimal_demo_status"], "blocked_missing_inputs")
        self.assertEqual(report["conditional_diagnostic_feasibility_status"], "blocked_missing_inputs")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["physical_frequency_authorized"])
        self.assertEqual(report["missing_required_inputs"], [str((ROOT / "docs/does-not-exist-for-balfrin-contract.md").resolve())])
        self.assertEqual(report["feasibility_vs_authorization"]["scale_up_authorized"], False)
        self.assertEqual(report["feasibility_vs_authorization"]["physical_frequency_authorized"], False)
        self.assertIn("one or more required inputs are missing", report["blocker"])

    def test_scope_creep_blocks_the_contract_when_claim_boundaries_widen(self) -> None:
        contract = self.load_contract(ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml")
        contract["minimal_demo_contract"]["claim_boundaries"]["scale_up_authorized"] = True

        path = self.write_contract(contract)
        try:
            report = contract_script.build_report(path)
        finally:
            path.unlink(missing_ok=True)

        self.assertEqual(report["contract_status"], "blocked_scope_creep")
        self.assertEqual(report["minimal_demo_status"], "blocked_scope_creep")
        self.assertEqual(report["conditional_diagnostic_feasibility_status"], "blocked_scope_creep")
        self.assertIn("scale_up_authorized", report["blocker"])
        self.assertTrue(report["scope_creep_reasons"])

    def test_text_report_remains_stable(self) -> None:
        report = contract_script.build_report()
        text = contract_script.render_text_report(report)
        self.assertEqual(text, contract_script.render_text_report(report))
        self.assertIn("Balfrin Minimal Demonstration Contract", text)
        self.assertIn("Conditional diagnostic feasibility", text)
        self.assertIn("Scale-up authorized: `False`", text)
        self.assertIn("Physical frequency authorized: `False`", text)
        self.assertIn("single_job_balfrin_slurm", text)
        self.assertIn("Minimal Demo vs Scientific Closure", text)

    def test_cli_emits_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = contract_script.main(["--format", "json"])

        self.assertEqual(exit_code, 0)
        json.loads(buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
