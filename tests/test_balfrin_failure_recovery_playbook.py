from __future__ import annotations

import json
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readiness = _load_module(ROOT / "scripts/check_balfrin_tschamut_readiness.py", "check_balfrin_tschamut_readiness_playbook")
metrics = _load_module(ROOT / "scripts/collect_balfrin_probe_metrics.py", "collect_balfrin_probe_metrics_playbook")
gate = _load_module(ROOT / "scripts/summarize_balfrin_post_run_interpretation_gate.py", "summarize_balfrin_post_run_interpretation_gate_playbook")
gis = _load_module(ROOT / "scripts/audit_gis_cog_package_readiness.py", "audit_gis_cog_package_readiness_playbook")


def _fake_tool_probe(binary: str) -> dict[str, object]:
    if binary == "qgis":
        return {"binary": binary, "required": False, "available": False, "version": None, "path": None}
    return {"binary": binary, "required": True, "available": True, "version": f"{binary} 1.0", "path": f"/usr/bin/{binary}"}


def _fake_git_probe(_: Path) -> dict[str, object]:
    return {"status": "ok", "branch": "main", "commit": "abc123"}


def _fixture_validator(command_plan: dict[str, object]):
    class _Validator:
        def validate_pilot_run(self, manifest: dict, manifest_path: Path | None = None) -> None:  # noqa: ARG002
            return None

        def build_command_plan(self, manifest: dict) -> dict[str, object]:  # noqa: ARG002
            return command_plan

    return _Validator()


class BalfrinFailureRecoveryPlaybookSmokeTests(unittest.TestCase):
    def test_readiness_status_exposes_blocking_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            geodata_manifest = root / "data/processed/swisstopo/tschamut_public_pilot/input/geodata.yaml"
            terrain_metadata = root / "data/processed/swisstopo/tschamut_public_pilot/input/terrain_metadata.yaml"
            source_zone_metadata = root / "data/processed/swisstopo/tschamut_public_pilot/input/source_zone_metadata.yaml"
            scenario_table = root / "data/processed/swisstopo/tschamut_public_pilot/input/scenario_table.csv"
            source_scenario_policy = root / "validation/policies/source_scenario_policy.yaml"
            benchmark_case = root / "validation/private/tschamut_public_pilot/gate_v1/case.yaml"
            output_root = root / "hazard/results/tschamut_public_pilot/gate_v1"
            validation_root = root / "validation/private/tschamut_public_pilot/gate_v1"

            geodata_manifest.parent.mkdir(parents=True, exist_ok=True)
            validation_root.mkdir(parents=True, exist_ok=True)
            output_root.mkdir(parents=True, exist_ok=True)

            geodata_manifest.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "required_datasets": [
                            {
                                "dataset_id": "swissalti3d",
                                "processed_outputs": [
                                    {
                                        "path": "data/processed/swisstopo/tschamut_public_pilot/input/terrain.asc",
                                        "metadata_path": str(terrain_metadata.relative_to(root)),
                                    }
                                ],
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            geodata_manifest.parent.mkdir(parents=True, exist_ok=True)
            (geodata_manifest.parent / "terrain.asc").write_text("DEM", encoding="utf-8")
            terrain_metadata.write_text("metadata", encoding="utf-8")
            source_zone_metadata.write_text("metadata", encoding="utf-8")
            source_scenario_policy.parent.mkdir(parents=True, exist_ok=True)
            source_scenario_policy.write_text("policy", encoding="utf-8")
            benchmark_case.parent.mkdir(parents=True, exist_ok=True)
            benchmark_case.write_text("case", encoding="utf-8")

            run_manifest = root / "validation/pilot_runs/readiness_fixture.yaml"
            run_manifest.parent.mkdir(parents=True, exist_ok=True)
            run_manifest.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "public_real_site_conditional_pilot_run_v1",
                        "pilot_id": "tschamut_public_pilot",
                        "run_id": "tschamut_public_conditional_gate_v1",
                        "run_status": "predeclared_ready",
                        "operational_status": "research_diagnostic",
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
                        "input_freeze": {
                            "geodata_manifest_path": str(geodata_manifest.relative_to(root)),
                            "terrain_metadata_path": str(terrain_metadata.relative_to(root)),
                            "source_zone_metadata_path": str(source_zone_metadata.relative_to(root)),
                            "scenario_table_path": str(scenario_table.relative_to(root)),
                            "source_scenario_policy_path": str(source_scenario_policy.relative_to(root)),
                            "benchmark_case_path": str(benchmark_case.relative_to(root)),
                            "freeze_status": "frozen",
                        },
                        "hazard_output_plan": {
                            "output_roots": {
                                "validation_results": str(validation_root.relative_to(root)),
                                "hazard_results": str(output_root.relative_to(root)),
                            }
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            command_plan = {
                "schema_version": "public_real_site_conditional_pilot_command_plan_v1",
                "run_id": "tschamut_public_conditional_gate_v1",
                "run_status": "predeclared_ready",
                "commands": [
                    {
                        "name": "build_conditional_hazard_layers",
                        "command": [
                            "python3",
                            "scripts/build_hazard_layers.py",
                            "--case",
                            str(benchmark_case),
                            "--output-dir",
                            str(output_root),
                            "--diagnostics",
                            str(validation_root / "metrics.json"),
                            "--trajectory",
                            str(validation_root / "trajectory.csv"),
                            "--ensemble-trajectories-dir",
                            str(validation_root / "trajectories"),
                            "--deposition",
                            str(validation_root / "deposition.csv"),
                            "--ensemble-impact-events-dir",
                            str(validation_root / "impacts"),
                            "--map-package-manifest-json",
                            str(output_root / "manifest.json"),
                            "--pilot-gis-package-manifest-json",
                            str(output_root / "gis_manifest.json"),
                        ],
                    }
                ],
            }
            report = readiness.collect_readiness_report(
                repo_root=root,
                run_manifest_path=run_manifest,
                tool_probe=_fake_tool_probe,
                git_probe=_fake_git_probe,
                validator_module=_fixture_validator(command_plan),
            )

        self.assertEqual(report["status"], readiness.STATUS_BLOCKED)
        self.assertIn("input_freeze.scenario_table_path", report["blocking_checks"])
        self.assertIn("checks", report)

    def test_metrics_contract_exposes_missing_fields_and_log_audit(self) -> None:
        complete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        incomplete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root"

        complete = metrics.collect_run_metrics(complete_root)
        incomplete = metrics.collect_run_metrics(incomplete_root)

        self.assertEqual(complete["metrics_contract_status"], "complete")
        self.assertIn("log_audit", complete)
        self.assertIn("trajectory_decision_counts", complete)
        self.assertEqual(incomplete["metrics_contract_status"], "blocked_missing_inputs")
        self.assertIn("metrics_contract_missing_metrics", incomplete)
        self.assertGreater(len(incomplete["metrics_contract_missing_metrics"]), 0)
        self.assertIn("error_like_line_count", incomplete["log_audit"])

    def test_post_run_gate_exposes_measured_inconclusive_and_blocked_states(self) -> None:
        measured = gate.build_report(
            {
                "readiness_check": {"status": "ready_for_balfrin_single_release_zone_pilot"},
                "convergence_stability_check": {"status": "measured"},
                "output_check": {"status": "rebuildable_reduced_output"},
                "gis_cog_check": {"status": "gis_package_ready"},
                "physical_credibility_check": {"status": "not_established"},
            }
        )
        inconclusive = gate.build_report(
            {
                "readiness_check": {"status": "ready_for_balfrin_single_release_zone_pilot"},
                "convergence_stability_check": {"status": "inconclusive"},
                "output_check": {"status": "summary_only_not_rebuildable"},
                "gis_cog_check": {"status": "gis_package_ready_cog_blocked"},
                "physical_credibility_check": {"status": "not_established"},
            }
        )
        blocked = gate.build_report({"missing_inputs": ["post_run_evidence_bundle"]})

        self.assertEqual(measured["interpretation_status"], "measured_conditional_diagnostic")
        self.assertEqual(inconclusive["interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(blocked["interpretation_status"], "blocked_missing_inputs")
        self.assertIn("required_checks", measured)
        self.assertIn("required_checks", inconclusive)
        self.assertIn("missing_inputs", blocked)

    def test_gis_cog_readiness_surfaces_ready_blocked_and_scope_delta_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            standard_root = root / "gate_v1"
            converted_root = root / "gate_v1_cog_export"
            standard_root.mkdir(parents=True, exist_ok=True)
            converted_root.mkdir(parents=True, exist_ok=True)
            self._write_gis_manifests(standard_root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            self._write_gis_manifests(converted_root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            report = gis.build_gis_cog_readiness_report(
                artifact_roots=[standard_root],
                converted_package_roots=[converted_root],
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready")
        self.assertEqual(report["converted_package_readiness_status"], "cog_package_ready")
        self.assertEqual(report["qgis_manual_qa_status"], "not_run")
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["scale_up_authorized"])

    def _write_gis_manifests(self, root: Path, *, artifact_id: str) -> None:
        layer_names = ["reach_probability", "max_kinetic_energy"]
        raster_outputs = []
        for layer_name in layer_names:
            raster_path = root / f"{artifact_id}_{layer_name}.tif"
            raster_path.write_bytes(b"placeholder")
            raster_outputs.append(
                {
                    "layer_name": layer_name,
                    "path": str(raster_path),
                    "format": "geotiff",
                    "cloud_optimized": True,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "placeholder",
                    "total_bytes": 1,
                }
            )
        map_manifest = {
            "schema_version": "map_package_manifest_v1",
            "map_product_id": artifact_id,
            "map_product_version": "v1",
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_id": "source_zone_a",
            "source_zone_metadata_path": str(root.parent / "input" / "source_zone_metadata.yaml"),
            "scenario_table_path": str(root.parent / "input" / "scenario_table.csv"),
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": raster_outputs,
            "layer_semantics": [
                {
                    "layer_name": layer_name,
                    "units": "dimensionless",
                    "numerator": f"{layer_name} numerator",
                    "denominator": "trajectory count conditioned on source/scenario metadata",
                    "is_annualized": False,
                    "weighted": layer_name.startswith("weighted_"),
                }
                for layer_name in layer_names
            ],
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
        }
        pilot_manifest = {
            "schema_version": "pilot_gis_package_manifest_v1",
            "package_version": "v1",
            "case_id": artifact_id,
            "grid": {
                "cell_size_m": 2.0,
                "ncols": 300,
                "nrows": 304,
                "source": "explicit",
                "xmin_m": 1.0,
                "ymin_m": 2.0,
            },
            "terrain": {
                "crs": "CH1903+ / LV95",
                "epsg": 2056,
                "extent": {"xmin": 1.0, "xmax": 601.0, "ymin": 2.0, "ymax": 610.0},
                "license": "test",
                "metadata_path": str(root.parent / "input" / "terrain_metadata.yaml"),
                "nodata": -9999.0,
                "path": str(root.parent / "input" / "terrain.asc"),
                "processed_sha256": "abc",
                "resolution_m": 2.0,
                "source_dataset": "swisstopo_swissalti3d",
                "source_filename": "source.tif",
                "source_product": "swissALTI3D 2 m COG",
                "terrain_type": "ascii_dem_clamped",
                "vertical_datum": "LN02",
            },
            "terrain_metadata": {
                "file_count": 1,
                "format": "yaml",
                "kind": "terrain_metadata",
                "path": str(root.parent / "input" / "terrain_metadata.yaml"),
                "sha256": "abc",
                "total_bytes": 1,
            },
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": map_manifest["raster_outputs"],
            "manifest_outputs": [],
            "parity_outputs": [],
            "conditional_intensity_exceedance_curve_outputs": [],
            "visual_qa": {
                "status": "not-run",
                "accepted_for_operational_use": False,
                "reviewed_artifacts": [],
                "note": "manual qa not run",
                "acceptance_scope": "local diagnostic GIS/QGIS review only",
            },
            "raster_contract": {
                "cloud_optimized": True,
                "csv_ascii_parity_required": True,
                "geopackage_included": False,
                "geotiff_required": True,
                "qgis_project_included": False,
            },
            "probability_claim_boundary": {"annualized": False, "operational": False, "risk": False},
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
            "source_zone_context": {},
        }
        (root / f"{artifact_id}_map_package_manifest.json").write_text(
            json.dumps(map_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (root / f"{artifact_id}_pilot_gis_package_manifest.json").write_text(
            json.dumps(pilot_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _fake_cog_metadata(self, path: Path) -> dict[str, object]:  # noqa: ARG002
        return {
            "status": "ok",
            "driver": "GTiff",
            "size": [300, 304],
            "epsg": 2056,
            "geo_transform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
            "block_size": [256, 256],
            "nodata": -9999.0,
            "overview_count": 2,
            "image_structure": {"INTERLEAVE": "BAND", "LAYOUT": "COG", "COMPRESSION": "ZSTD"},
            "sample_raster_cog_layout": True,
            "sample_raster_tiled": True,
            "sample_raster_overviews": True,
        }


if __name__ == "__main__":
    unittest.main()
