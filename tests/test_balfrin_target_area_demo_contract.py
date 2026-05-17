from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"


class BalfrinTargetAreaDemoContractTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_target_area_contract_is_machine_readable_and_frozen(self) -> None:
        contract = self.load_contract()

        self.assertEqual(contract["schema_version"], "balfrin_target_area_demo_v1")
        self.assertEqual(contract["contract_status"], "ready_for_balfrin_target_area_demo")
        self.assertEqual(contract["target_area"]["target_area_id"], "tschamut_public_pilot")
        self.assertEqual(contract["target_area"]["site_extent"]["crs"], "EPSG:2056")
        self.assertEqual(
            contract["input_freeze"]["target_gate_reproduction_record_path"],
            "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        )
        self.assertEqual(
            contract["input_freeze"]["target_gate_execution_contract_path"],
            "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        )
        self.assertEqual(contract["input_freeze"]["scenario_family_basis"], "conditional_sampling_only")
        self.assertEqual(contract["output_mode"]["validation_output_mode"], "scalable_conditional")
        self.assertEqual(contract["output_mode"]["conditional_curve_export"], "summary-only")
        self.assertEqual(contract["output_mode"]["gis_package_mode"], "pilot_gis_package")
        self.assertTrue(contract["output_mode"]["pilot_gis_package"])
        self.assertEqual(contract["balfrin_execution_boundary"]["execution_boundary"], "single_job_balfrin_slurm")
        self.assertEqual(contract["balfrin_execution_boundary"]["run_id_policy"], "deterministic_frozen_run_id")
        self.assertIn("--local-command-plan", contract["balfrin_execution_boundary"]["command_plan_hook"]["command"])
        self.assertIn(
            "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
            contract["balfrin_execution_boundary"]["probe_manifest_path"],
        )
        self.assertEqual(
            contract["balfrin_execution_boundary"]["expected_ignored_output_roots"],
            [
                "validation/private/tschamut_public_pilot/target_gate_v1",
                "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
                "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
                "hazard/results/tschamut_public_pilot/target_gate_v1",
            ],
        )
        self.assertFalse(contract["claim_boundary"]["operational_claims_allowed"])
        self.assertFalse(contract["claim_boundary"]["physical_probability_claims_allowed"])
        self.assertFalse(contract["claim_boundary"]["scale_up_authorized"])
        self.assertIn("conditional_intensity_exceedance", contract["claim_boundary"]["current_allowed_product_labels"])
