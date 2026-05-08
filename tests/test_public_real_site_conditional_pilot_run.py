from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_public_real_site_conditional_pilot_run.py"
SPEC = importlib.util.spec_from_file_location("validate_public_real_site_conditional_pilot_run", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PublicRealSiteConditionalPilotRunTests(unittest.TestCase):
    def load_template(self) -> dict:
        return validator.read_yaml(
            ROOT / "validation/templates/public_real_site_conditional_pilot_run_v1.yaml"
        )

    def test_template_run_contract_is_valid(self) -> None:
        validator.validate_pilot_run(self.load_template())

    def test_non_template_run_requires_frozen_inputs(self) -> None:
        manifest = self.load_template()
        manifest["run_status"] = "predeclared_ready"

        with self.assertRaisesRegex(validator.PilotRunError, "freeze_status"):
            validator.validate_pilot_run(manifest)

    def test_predeclared_run_accepts_explicit_grid_thresholds_and_budget(self) -> None:
        manifest = self.predeclared_manifest()

        validator.validate_pilot_run(manifest)

    def test_rejects_missing_claim_boundary(self) -> None:
        manifest = copy.deepcopy(self.load_template())
        manifest["claim_boundary"]["unsupported_current_claims"].remove("risk_map")

        with self.assertRaisesRegex(validator.PilotRunError, "risk_map"):
            validator.validate_pilot_run(manifest)

    def test_completed_gate_requires_core_gate_passes(self) -> None:
        manifest = self.predeclared_manifest()
        manifest["run_status"] = "gate_run_completed"

        with self.assertRaisesRegex(validator.PilotRunError, "small_gate_run_completed"):
            validator.validate_pilot_run(manifest)

    def predeclared_manifest(self) -> dict:
        manifest = copy.deepcopy(self.load_template())
        manifest["run_status"] = "predeclared_ready"
        manifest["input_freeze"].update(
            {
                "benchmark_case_path": "validation/cases/probabilistic_phase1_smoke.yaml",
                "terrain_metadata_path": "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml",
                "source_zone_metadata_path": "validation/data/processed/probabilistic_phase1/source_zone_smoke.yaml",
                "scenario_table_path": "validation/data/processed/probabilistic_phase1/scenario_table_smoke.csv",
                "map_product_id": "phase1_smoke_map",
                "freeze_status": "frozen",
            }
        )
        manifest["physics_freeze"]["parameters_status"] = "frozen"
        manifest["sampling_plan"].update(
            {
                "random_seed": 2056003,
                "gate_run_trajectories_per_release_zone": 1,
                "target_trajectories_per_release_zone": 2,
                "worker_count": 2,
            }
        )
        manifest["hazard_output_plan"].update(
            {
                "kinetic_energy_exceedance_j": [5.0],
                "jump_height_exceedance_m": [0.05],
                "velocity_exceedance_mps": [1.0],
                "explicit_grid": {
                    "xmin": 2600000.0,
                    "ymin": 1200000.0,
                    "ncols": 2,
                    "nrows": 2,
                    "cell_size_m": 2.0,
                },
            }
        )
        manifest["workflow_gates"].update(
            {
                "geodata_manifest_validated": "pass",
                "source_scenario_policy_validated": "pass",
                "benchmark_case_frozen": "pass",
            }
        )
        manifest["output_budget"].update(
            {
                "max_private_file_count": 100,
                "max_private_total_bytes": 10_000_000,
            }
        )
        manifest["report_plan"]["current_classification"] = "inconclusive"
        return manifest


if __name__ == "__main__":
    unittest.main()
