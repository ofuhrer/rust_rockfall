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

    def test_template_run_rejects_command_plan(self) -> None:
        with self.assertRaisesRegex(validator.PilotRunError, "template_not_run"):
            validator.build_command_plan(self.load_template())

    def test_predeclared_run_builds_dry_run_command_plan(self) -> None:
        plan = validator.build_command_plan(self.predeclared_manifest())

        self.assertEqual(
            plan["schema_version"],
            "public_real_site_conditional_pilot_command_plan_v1",
        )
        command_names = [entry["name"] for entry in plan["commands"]]
        self.assertEqual(
            command_names,
            [
                "validate_geodata_manifest",
                "validate_source_scenario_policy",
                "run_validation_gate",
                "build_conditional_hazard_layers",
            ],
        )
        hazard_command = plan["commands"][-1]["command"]
        self.assertIn("--export-geotiff", hazard_command)
        self.assertIn("--pilot-gis-package", hazard_command)
        self.assertIn("--reducer-workers", hazard_command)
        self.assertIn("--grid-xmin", hazard_command)
        self.assertIn("--kinetic-energy-exceedance-j", hazard_command)
        self.assertIn("validation/results/probabilistic_phase1_smoke_trajectory.csv", hazard_command)
        self.assertIn("validation/results/probabilistic_phase1_smoke_trajectories", hazard_command)
        self.assertIn("hazard/results/public_real_site_pilot_template", hazard_command)

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

    def test_completed_gate_requires_run_evidence(self) -> None:
        manifest = self.completed_gate_manifest()
        manifest["run_evidence"]["evidence_status"] = "not_run"

        with self.assertRaisesRegex(validator.PilotRunError, "matching run_evidence"):
            validator.validate_pilot_run(manifest)

    def test_completed_gate_accepts_share_safe_evidence(self) -> None:
        validator.validate_pilot_run(self.completed_gate_manifest())

    def test_completed_gate_rejects_invalid_artifact_checksum(self) -> None:
        manifest = self.completed_gate_manifest()
        manifest["run_evidence"]["artifact_checksums"]["hazard_manifest_sha256"] = "ABC123"

        with self.assertRaisesRegex(validator.PilotRunError, "hazard_manifest_sha256"):
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

    def completed_gate_manifest(self) -> dict:
        manifest = self.predeclared_manifest()
        manifest["run_status"] = "gate_run_completed"
        manifest["workflow_gates"].update(
            {
                "small_gate_run_completed": "pass",
                "conditional_curves_generated": "pass",
                "gis_package_generated": "pass",
                "convergence_diagnostics_recorded": "pass",
                "output_budget_recorded": "pass",
                "visual_qa_recorded": "inconclusive",
                "report_classification": "inconclusive",
            }
        )
        manifest["run_evidence"].update(
            {
                "evidence_status": "gate_run_completed",
                "validation_manifest_path": "validation/private/public_real_site_pilot_template/gate_run_manifest.json",
                "hazard_manifest_path": "hazard/results/public_real_site_pilot_template/gate_run_manifest.json",
                "conditional_curve_table_path": "hazard/results/public_real_site_pilot_template/gate_conditional_intensity_exceedance_curves.csv",
                "map_package_manifest_path": "hazard/results/public_real_site_pilot_template/gate_map_package_manifest.json",
                "pilot_gis_package_manifest_path": "hazard/results/public_real_site_pilot_template/gate_pilot_gis_package_manifest.json",
                "reducer_chunk_manifest_dir": "hazard/results/public_real_site_pilot_template/chunks",
                "runtime_seconds": 12.5,
                "memory_peak_mb": 512.0,
                "output_file_count": 8,
                "output_total_bytes": 2048,
                "trajectory_count": 4,
                "release_cell_count": 2,
                "convergence_diagnostics": {
                    "status": "inconclusive",
                    "notes": ["gate run completed; target-scale convergence is not established"],
                },
                "artifact_checksums": {
                    "validation_manifest_sha256": "a" * 64,
                    "hazard_manifest_sha256": "b" * 64,
                    "conditional_curve_table_sha256": "c" * 64,
                    "map_package_manifest_sha256": "d" * 64,
                    "pilot_gis_package_manifest_sha256": "e" * 64,
                },
            }
        )
        return manifest


if __name__ == "__main__":
    unittest.main()
