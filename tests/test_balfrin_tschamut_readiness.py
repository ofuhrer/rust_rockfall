from __future__ import annotations

import importlib.util
import tempfile
import types
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_balfrin_tschamut_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_balfrin_tschamut_readiness", SCRIPT_PATH)
assert SPEC is not None
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class _FixtureValidator:
    def __init__(self, command_plan: dict) -> None:
        self._command_plan = command_plan

    def validate_pilot_run(self, manifest: dict, manifest_path: Path | None = None) -> None:  # noqa: ARG002 - test shim
        return None

    def build_command_plan(self, manifest: dict) -> dict:  # noqa: ARG002 - test shim
        return self._command_plan


def _fake_tool_probe_factory(qgis_available: bool = False) -> object:
    def probe(binary: str) -> dict:
        if binary == "qgis":
            return {
                "binary": binary,
                "required": False,
                "available": qgis_available,
                "version": "QGIS 3.34.0" if qgis_available else None,
                "path": "/usr/bin/qgis" if qgis_available else None,
            }
        return {
            "binary": binary,
            "required": True,
            "available": True,
            "version": f"{binary} 1.2.3",
            "path": f"/usr/bin/{binary}",
        }

    return probe


def _fake_git_probe(_: Path) -> dict:
    return {"status": "ok", "branch": "main", "commit": "abc123"}


class BalfrinReadinessTests(unittest.TestCase):
    def write_file(self, path: Path, text: str = "") -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def command_plan(self, paths: dict[str, Path]) -> dict:
        return {
            "schema_version": "public_real_site_conditional_pilot_command_plan_v1",
            "run_id": "tschamut_public_conditional_gate_v1",
            "run_status": "predeclared_ready",
            "operational_status": "research_diagnostic",
            "generated_outputs_committed": False,
            "commands": [
                {
                    "name": "validate_geodata_manifest",
                    "command": ["uv", "run", "python", "scripts/validate_public_real_site_geodata_manifest.py", str(paths["geodata_manifest"])],
                },
                {
                    "name": "validate_source_scenario_policy",
                    "command": ["uv", "run", "python", "scripts/validate_source_scenario_policy.py", str(paths["source_scenario_policy"])],
                },
                {
                    "name": "run_validation_gate",
                    "command": ["cargo", "run", "--", "validate", "--case", str(paths["benchmark_case"])],
                },
                {
                    "name": "build_conditional_hazard_layers",
                    "command": [
                        "uv",
                        "run",
                        "python",
                        "scripts/build_hazard_layers.py",
                        "--case",
                        str(paths["benchmark_case"]),
                        "--output-dir",
                        str(paths["hazard_output_dir"]),
                        "--source-zone-metadata-path",
                        str(paths["source_zone_metadata"]),
                        "--scenario-table-path",
                        str(paths["scenario_table"]),
                        "--map-package-manifest-json",
                        str(paths["hazard_output_dir"] / "manifest.json"),
                        "--pilot-gis-package-manifest-json",
                        str(paths["hazard_output_dir"] / "gis_manifest.json"),
                        "--diagnostics",
                        str(paths["diagnostics_csv"]),
                        "--trajectory",
                        str(paths["trajectory_csv"]),
                        "--ensemble-trajectories-dir",
                        str(paths["trajectory_dir"]),
                        "--deposition",
                        str(paths["deposition_csv"]),
                        "--ensemble-impact-events-dir",
                        str(paths["impact_dir"]),
                    ],
                },
            ],
        }

    def make_synthetic_manifest(self, root: Path, *, missing_scenario: bool = False) -> tuple[Path, dict[str, Path]]:
        geodata_manifest = root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_manifest.yaml"
        terrain_metadata = root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml"
        source_zone_metadata = root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata.yaml"
        scenario_table = root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table.csv"
        source_scenario_policy = root / "validation/policies/tschamut_public_source_scenario_policy.yaml"
        benchmark_case = root / "validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml"
        output_root = root / "hazard/results/tschamut_public_pilot/gate_v1"
        validation_output_root = root / "validation/private/tschamut_public_pilot/gate_v1"
        case_dir = benchmark_case.parent

        self.write_file(geodata_manifest, yaml.safe_dump({
            "schema_version": 1,
            "required_datasets": [
                {
                    "dataset_id": "swissalti3d",
                    "processed_outputs": [
                        {
                            "path": str(geodata_manifest.with_name("tschamut_public_swissalti3d_crop.asc").relative_to(root)),
                            "metadata_path": str(terrain_metadata.relative_to(root)),
                        }
                    ],
                }
            ],
        }, sort_keys=False))

        dem_path = geodata_manifest.with_name("tschamut_public_swissalti3d_crop.asc")
        self.write_file(dem_path, "DEM")
        self.write_file(terrain_metadata, "metadata")
        self.write_file(source_zone_metadata, "metadata")
        if not missing_scenario:
            self.write_file(scenario_table, "source,weight\n")
        self.write_file(source_scenario_policy, "policy")
        self.write_file(benchmark_case, "case")
        output_root.mkdir(parents=True, exist_ok=True)
        validation_output_root.mkdir(parents=True, exist_ok=True)

        diagnostics_csv = validation_output_root / "validation_tschamut_public_conditional_gate_v1_diagnostics.csv"
        trajectory_csv = validation_output_root / "validation_tschamut_public_conditional_gate_v1_trajectory.csv"
        trajectory_dir = validation_output_root / "trajectories"
        deposition_csv = validation_output_root / "validation_tschamut_public_conditional_gate_v1_deposition.csv"
        impact_dir = validation_output_root / "impacts"
        for value in (diagnostics_csv, trajectory_csv, deposition_csv):
            self.write_file(value, "")
        trajectory_dir.mkdir(parents=True, exist_ok=True)
        impact_dir.mkdir(parents=True, exist_ok=True)

        run_manifest_path = root / "validation/pilot_runs/sschamut_balfrin_readiness_fixture.yaml"
        manifest = {
            "schema_version": "public_real_site_conditional_pilot_run_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "run_status": "predeclared_ready",
            "operational_status": "research_diagnostic",
            "input_freeze": {
                "geodata_manifest_path": str(geodata_manifest.relative_to(root)),
                "source_scenario_policy_path": str(source_scenario_policy.relative_to(root)),
                "benchmark_case_path": str(benchmark_case.relative_to(root)),
                "terrain_metadata_path": str(terrain_metadata.relative_to(root)),
                "source_zone_metadata_path": str(source_zone_metadata.relative_to(root)),
                "scenario_table_path": str(scenario_table.relative_to(root)),
                "map_product_id": "tschamut_public_conditional_gate_v1",
                "freeze_status": "frozen",
            },
            "hazard_output_plan": {
                "output_roots": {
                    "validation_results": str(validation_output_root.relative_to(root)),
                    "hazard_results": str(output_root.relative_to(root)),
                }
            },
            "claim_boundary": {
                "unsupported_current_claims": [
                    "annual_frequency",
                    "return_period",
                    "physical_probability",
                    "risk_map",
                    "operational_hazard_map",
                ]
            },
            "workflow_gates": {},
            "output_budget": {},
            "run_evidence": {},
            "report_plan": {
                "allowed_classifications": ["inconclusive"],
                "current_classification": "inconclusive",
            },
            "physics_freeze": {
                "parameters_status": "frozen",
                "defaults_changed": False,
                "simulator_behavior_changed": False,
                "contact_model": "translational_v0",
                "soil_interaction_model": "none",
                "roughness_model": "stochastic_contact_v1",
                "tuning_after_output_review_allowed": False,
            },
            "sampling_plan": {
                "release_cell_policy": "deterministic_grid",
                "scenario_weight_semantics": "conditional_sampling_only",
                "reducer_mode": "deterministic_local_reducer",
                "random_seed": 1,
                "gate_run_trajectories_per_release_zone": 1,
                "target_trajectories_per_release_zone": 2,
                "worker_count": 1,
            },
        }
        self.write_file(run_manifest_path, yaml.safe_dump(manifest, sort_keys=False))

        command_plan_paths = {
            "geodata_manifest": geodata_manifest,
            "source_scenario_policy": source_scenario_policy,
            "benchmark_case": benchmark_case,
            "source_zone_metadata": source_zone_metadata,
            "scenario_table": scenario_table,
            "hazard_output_dir": output_root,
            "trajectory_dir": trajectory_dir,
            "deposition_csv": deposition_csv,
            "impact_dir": impact_dir,
            "diagnostics_csv": diagnostics_csv,
            "trajectory_csv": trajectory_csv,
        }

        return run_manifest_path, command_plan_paths

    def test_ready_report_with_required_inputs_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_manifest_path, paths = self.make_synthetic_manifest(root)
            validator = _FixtureValidator(self.command_plan(paths))
            report = checker.collect_readiness_report(
                repo_root=root,
                run_manifest_path=run_manifest_path,
                tool_probe=_fake_tool_probe_factory(qgis_available=False),
                git_probe=_fake_git_probe,
                validator_module=validator,
            )

            self.assertEqual(report["status"], checker.STATUS_READY)
            self.assertEqual(report["repo_path"], str(root))
            blockers = [check for check in report["checks"] if check["required"] and check["status"] == "fail"]
            self.assertFalse(blockers)
            qgis_check = next(check for check in report["checks"] if check["name"] == "tool.qgis")
            self.assertEqual(qgis_check["status"], "warn")

    def test_ready_report_accepts_the_frozen_balfrin_contract_schema(self) -> None:
        report = checker.collect_readiness_report(
            repo_root=ROOT,
            run_manifest_path=ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml",
            tool_probe=_fake_tool_probe_factory(qgis_available=False),
            git_probe=_fake_git_probe,
        )

        self.assertEqual(report["status"], checker.STATUS_READY)
        self.assertTrue(any(check["name"] == "run_manifest.schema_version" and check["status"] == "pass" for check in report["checks"]))
        self.assertTrue(any(check["name"] == "balfrin_contract.summary" and check["status"] == "pass" for check in report["checks"]))
        self.assertTrue(any(check["name"] == "balfrin_case_plan.status" and check["status"] == "pass" for check in report["checks"]))
        self.assertFalse(
            any(
                "schema_version must be public_real_site_conditional_pilot_run_v1" in check["message"]
                for check in report["checks"]
            )
        )

    def test_ready_report_blocks_missing_scenario_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_manifest_path, paths = self.make_synthetic_manifest(root, missing_scenario=True)
            validator = _FixtureValidator(self.command_plan(paths))
            report = checker.collect_readiness_report(
                repo_root=root,
                run_manifest_path=run_manifest_path,
                tool_probe=_fake_tool_probe_factory(qgis_available=False),
                git_probe=_fake_git_probe,
                validator_module=validator,
            )

            self.assertEqual(report["status"], checker.STATUS_BLOCKED)
            required_failures = [check["name"] for check in report["checks"] if check["required"] and check["status"] == "fail"]
            self.assertIn("input_freeze.scenario_table_path", required_failures)

    def test_report_can_parse_and_include_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_manifest_path, paths = self.make_synthetic_manifest(root)
            validator = _FixtureValidator(self.command_plan(paths))
            report = checker.collect_readiness_report(
                repo_root=root,
                run_manifest_path=run_manifest_path,
                tool_probe=_fake_tool_probe_factory(qgis_available=True),
                git_probe=_fake_git_probe,
                validator_module=validator,
            )

            self.assertEqual(report["command_plan"]["schema_version"], "public_real_site_conditional_pilot_command_plan_v1")
            self.assertEqual(report["status"], checker.STATUS_READY)
            self.assertIn("command_plan[build_conditional_hazard_layers].--case", {
                check["name"] for check in report["checks"]
            })


if __name__ == "__main__":
    unittest.main()
