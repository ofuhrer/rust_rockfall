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
    selected_run_path = ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
    selected_run_id = "tschamut_public_conditional_gate_v1"

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

    def test_predeclared_run_without_scalable_controls_keeps_default_command(self) -> None:
        manifest = self.predeclared_manifest()
        plan = validator.build_command_plan(manifest)
        hazard_command = plan["commands"][-1]["command"]

        self.assertNotIn("--conditional-curve-export", hazard_command)
        self.assertNotIn("--grid-csv-export", hazard_command)
        self.assertNotIn("--trajectory-workers", hazard_command)

    def test_predeclared_run_with_scalable_controls_emits_flags(self) -> None:
        manifest = self.predeclared_manifest()
        manifest["hazard_output_plan"].update(
            {
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "trajectory_workers": 3,
            }
        )
        plan = validator.build_command_plan(manifest)
        hazard_command = plan["commands"][-1]["command"]

        conditional_index = hazard_command.index("--conditional-curve-export")
        grid_csv_index = hazard_command.index("--grid-csv-export")
        trajectory_worker_index = hazard_command.index("--trajectory-workers")
        self.assertEqual(hazard_command[conditional_index + 1], "summary-only")
        self.assertEqual(hazard_command[grid_csv_index + 1], "none")
        self.assertEqual(hazard_command[trajectory_worker_index + 1], "3")

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

    def test_completed_gate_rejects_invalid_optional_artifact_checksum(self) -> None:
        for key in ("dem_sensitivity_summary_sha256", "scaling_summary_sha256"):
            with self.subTest(key=key):
                manifest = self.completed_gate_manifest()
                manifest["run_evidence"]["artifact_checksums"][key] = "INVALIDHEX"
                with self.assertRaisesRegex(validator.PilotRunError, key):
                    validator.validate_pilot_run(manifest)

    def test_selected_tschamut_gate_contract_is_valid(self) -> None:
        manifest = self.selected_tschamut_gate_manifest()

        validator.validate_pilot_run(manifest)

    def test_selected_tschamut_completed_gate_builds_execution_command_plan(self) -> None:
        manifest = self.selected_tschamut_gate_manifest()

        plan = validator.build_command_plan(manifest)

        self.assertEqual(plan["run_status"], "gate_run_completed")
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
        self.assertNotIn("--allow-missing-source-dem", hazard_command)
        self.assertIn("--pilot-gis-package", hazard_command)
        self.assertIn("--reducer-workers", hazard_command)
        self.assertIn("validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml", hazard_command)

    def test_selected_tschamut_contract_keeps_gate_run_completed_inconclusive_state(self) -> None:
        manifest = self.selected_tschamut_gate_manifest()

        validator.validate_pilot_run(manifest)
        self.assertEqual(manifest["run_status"], "gate_run_completed")
        self.assertEqual(manifest["run_evidence"]["evidence_status"], "gate_run_completed")
        self.assertEqual(manifest["report_plan"]["current_classification"], "inconclusive")
        self.assertEqual(manifest["report_plan"]["report_path"], "docs/tschamut_public_conditional_pilot_gate_report.md")

    def test_selected_tschamut_contract_requires_expected_evidence_paths_and_hashes(self) -> None:
        manifest = self.selected_tschamut_gate_manifest()
        evidence = manifest["run_evidence"]

        self.assertEqual(evidence["validation_manifest_path"], "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json")
        self.assertEqual(evidence["hazard_manifest_path"], "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json")
        self.assertEqual(evidence["conditional_curve_table_path"], "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_conditional_intensity_exceedance_curves.csv")
        self.assertEqual(evidence["map_package_manifest_path"], "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json")
        self.assertEqual(evidence["pilot_gis_package_manifest_path"], "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json")
        self.assertEqual(evidence["reducer_chunk_manifest_dir"], "hazard/results/tschamut_public_pilot/gate_v1/chunks")
        self.assertEqual(evidence["dem_sensitivity_summary_path"], "validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1/dem_terrain_sensitivity_summary.json")
        self.assertEqual(evidence["scaling_summary_path"], "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json")

        checksums = evidence["artifact_checksums"]
        for key in (
            "validation_manifest_sha256",
            "hazard_manifest_sha256",
            "conditional_curve_table_sha256",
            "map_package_manifest_sha256",
            "pilot_gis_package_manifest_sha256",
            "dem_sensitivity_summary_sha256",
            "scaling_summary_sha256",
        ):
            self.assertRegex(checksums[key], validator.HEX_SHA256_RE)

        for key in (
            "validation_manifest_path",
            "hazard_manifest_path",
            "conditional_curve_table_path",
            "map_package_manifest_path",
            "pilot_gis_package_manifest_path",
            "reducer_chunk_manifest_dir",
            "dem_sensitivity_summary_path",
            "scaling_summary_path",
        ):
            self.assertTrue(evidence[key].startswith(("validation/", "hazard/results/")))

        for key in (
            "validation_manifest_path",
            "hazard_manifest_path",
            "conditional_curve_table_path",
            "map_package_manifest_path",
            "pilot_gis_package_manifest_path",
        ):
            self.assertIn(self.selected_run_id, evidence[key], f"{key} should reference selected run id")

    def test_selected_tschamut_contract_rejects_report_checksum_mismatch(self) -> None:
        manifest = copy.deepcopy(self.selected_tschamut_gate_manifest())
        manifest["run_evidence"]["artifact_checksums"]["hazard_manifest_sha256"] = "0" * 64

        with self.assertRaisesRegex(
            validator.PilotRunError,
            "report checksum mismatch",
        ):
            validator.validate_pilot_run(manifest)

    def test_selected_tschamut_contract_command_plan_is_exact_shape(self) -> None:
        manifest = self.selected_tschamut_gate_manifest()
        plan = validator.build_command_plan(manifest)
        hazard_command = plan["commands"][-1]["command"]
        self.assertEqual(hazard_command[0:4], ["uv", "run", "python", "scripts/build_hazard_layers.py"])

        expected_pairs = [
            ("--case", "validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml"),
            ("--output-dir", "hazard/results/tschamut_public_pilot/gate_v1"),
            ("--grid-xmin", "2696376.0"),
            ("--grid-ymin", "1167384.0"),
            ("--grid-ncols", "300"),
            ("--grid-nrows", "304"),
            ("--grid-cell-size", "2.0"),
            ("--map-product-id", "tschamut_public_conditional_gate_v1"),
            ("--source-zone-metadata-path", "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"),
            ("--scenario-table-path", "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"),
            ("--map-package-manifest-json", "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json"),
            ("--pilot-gis-package-manifest-json", "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"),
            ("--reducer-workers", "2"),
            ("--kinetic-energy-exceedance-j", "1000.0"),
            ("--jump-height-exceedance-m", "1.0"),
        ]
        for flag, value in expected_pairs:
            self.assertIn(flag, hazard_command)
            idx = hazard_command.index(flag)
            self.assertLess(idx + 1, len(hazard_command))
            self.assertEqual(hazard_command[idx + 1], value)
        self.assertEqual(hazard_command.count("--kinetic-energy-exceedance-j"), 2)
        for threshold in ("1000.0", "10000.0"):
            indices = [i for i, value in enumerate(hazard_command) if value == "--kinetic-energy-exceedance-j"]
            self.assertTrue(any(hazard_command[i + 1] == threshold for i in indices))
        self.assertEqual(hazard_command.count("--jump-height-exceedance-m"), 2)
        for threshold in ("1.0", "2.0"):
            indices = [i for i, value in enumerate(hazard_command) if value == "--jump-height-exceedance-m"]
            self.assertTrue(any(hazard_command[i + 1] == threshold for i in indices))
        self.assertEqual(hazard_command.count("--diagnostics"), 1)
        self.assertEqual(hazard_command.count("--trajectory"), 1)
        self.assertEqual(hazard_command.count("--ensemble-trajectories-dir"), 1)
        self.assertEqual(hazard_command.count("--deposition"), 1)
        self.assertEqual(hazard_command.count("--ensemble-impact-events-dir"), 1)
        self.assertNotIn("--allow-missing-source-dem", hazard_command)
        self.assertNotIn("--ensemble-impact-events-parquet", hazard_command)

        for path in (
            "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json",
            "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv",
            "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories",
            "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv",
            "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts",
        ):
            self.assertIn(path, hazard_command)
        report_text = (ROOT / validator.read_yaml(self.selected_run_path)["report_plan"]["report_path"]).read_text(encoding="utf-8")
        self.assertIn(f"Run id: `{self.selected_run_id}`", report_text)
        self.assertIn("Current classification: `inconclusive`", report_text)
        self.assertIn("research diagnostic", report_text.lower())

    def test_no_go_gate_requires_explicit_blocker(self) -> None:
        manifest = self.no_go_manifest()
        del manifest["no_go_blocker"]

        with self.assertRaisesRegex(validator.PilotRunError, "no_go_blocker"):
            validator.validate_pilot_run(manifest)

    def test_no_go_gate_builds_blocker_command_plan(self) -> None:
        plan = validator.build_command_plan(self.no_go_manifest())

        self.assertEqual(plan["run_status"], "no_go")
        self.assertEqual(plan["blocker"]["blocker_id"], "missing_processed_tschamut_public_dem")
        command_names = [entry["name"] for entry in plan["commands"]]
        self.assertEqual(
            command_names,
            [
                "validate_geodata_manifest",
                "validate_source_scenario_policy",
                "record_dem_sensitivity_blocker",
            ],
        )
        blocker_command = plan["commands"][-1]["command"]
        self.assertIn("--allow-missing-source-dem", blocker_command)
        self.assertIn("validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1", blocker_command)

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

    def no_go_manifest(self) -> dict:
        manifest = self.predeclared_manifest()
        manifest["run_status"] = "no_go"
        manifest["input_freeze"]["freeze_status"] = "blocked_missing_processed_dem"
        for key in ("benchmark_case_path", "terrain_metadata_path", "source_zone_metadata_path", "scenario_table_path"):
            manifest["input_freeze"][key] = None
        manifest["workflow_gates"].update(
            {
                "benchmark_case_frozen": "no-go",
                "small_gate_run_completed": "no-go",
                "conditional_curves_generated": "no-go",
                "gis_package_generated": "no-go",
                "convergence_diagnostics_recorded": "no-go",
                "output_budget_recorded": "no-go",
                "visual_qa_recorded": "no-go",
                "report_classification": "no-go",
            }
        )
        manifest["run_evidence"].update(
            {
                "evidence_status": "no-go",
                "validation_manifest_path": None,
                "hazard_manifest_path": None,
                "conditional_curve_table_path": None,
                "map_package_manifest_path": None,
                "pilot_gis_package_manifest_path": None,
                "reducer_chunk_manifest_dir": None,
                "runtime_seconds": None,
                "memory_peak_mb": None,
                "output_file_count": None,
                "output_total_bytes": None,
                "trajectory_count": None,
                "release_cell_count": None,
                "convergence_diagnostics": {
                    "status": "no-go",
                    "notes": ["required processed DEM inputs are absent; this is not a model result"],
                },
                "artifact_checksums": {
                    "validation_manifest_sha256": None,
                    "hazard_manifest_sha256": None,
                    "conditional_curve_table_sha256": None,
                    "map_package_manifest_sha256": None,
                    "pilot_gis_package_manifest_sha256": None,
                },
            }
        )
        manifest["no_go_blocker"] = {
            "blocker_id": "missing_processed_tschamut_public_dem",
            "status": "active",
            "classification": "no-go",
            "evidence_output_dir": "validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1",
            "missing_paths": [
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
            ],
            "recovery_commands": [
                "UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/prepare_tschamut_public_benchmark.py --output-root data/processed/swisstopo/tschamut_public_pilot --padding-m 250 --force",
            ],
            "notes": ["this no-go gate is not a model result"],
        }
        manifest["report_plan"]["current_classification"] = "no-go"
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

    def selected_tschamut_gate_manifest(self) -> dict:
        return validator.read_yaml(self.selected_run_path)


if __name__ == "__main__":
    unittest.main()
