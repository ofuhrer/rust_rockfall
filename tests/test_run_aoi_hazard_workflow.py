from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_aoi_hazard_workflow.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


workflow = _load_module(SCRIPT_PATH, "run_aoi_hazard_workflow")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_front_door_tests",
)


class RunAoiHazardWorkflowTests(unittest.TestCase):
    def test_command_dispatch_routes_to_the_expected_backend_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            with mock.patch.object(
                workflow,
                "build_aoi_workflow_report",
                return_value={
                    "schema_version": "aoi_workflow_stub_v1",
                    "workflow_classification": "blocked_fixture_backed_inputs",
                    "prepared_pilot_input_classification": "fixture_backed",
                    "workflow_steps": [],
                    "blocked_missing_inputs": [],
                    "ready_for_next_step": {
                        "status": "blocked_fixture_backed_inputs",
                        "next_step": "none",
                        "requires_explicit_permission": False,
                        "permission_recorded": False,
                        "permission_note": "",
                    },
                    "claim_boundaries": {"operational_claims_allowed": False},
                },
            ), mock.patch.object(
                workflow,
                "build_package_report",
                return_value={
                    "schema_version": "gis_cog_stub_v1",
                    "gis_cog_readiness_status": "gis_package_ready",
                    "blocked_missing_inputs": [],
                    "claim_boundaries": {"operational_claims_allowed": False},
                },
            ), mock.patch.object(
                workflow.COMMAND_PLAN,
                "build_report",
                return_value={
                    "schema_version": "portable_pilot_command_plan_v1",
                    "command_plan_status": "ready",
                    "blocked_template_commands": [],
                    "ignored_output_paths": [],
                },
            ):
                status_report = workflow.build_report(
                    command="status",
                    site_config=config_path,
                    repo_root=repo_root,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                )
                package_report = workflow.build_report(
                    command="package-map",
                    site_config=config_path,
                    repo_root=repo_root,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                )

        self.assertEqual(status_report["command"], "status")
        self.assertEqual(status_report["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(status_report["next_action"], "plan")
        self.assertEqual(package_report["command"], "package-map")
        self.assertEqual(package_report["status"], "gis_package_ready")
        self.assertEqual(package_report["next_action"], "collect")

    def test_clean_checkout_status_reports_the_first_blocker_and_prepare_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            report = workflow.build_report(
                command="status",
                site_config=config_path,
                repo_root=repo_root,
                acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
            )

        self.assertEqual(report["schema_version"], "aoi_hazard_workflow_front_door_v1")
        self.assertEqual(report["status"], "blocked_missing_real_core_inputs")
        self.assertEqual(report["next_action"], "prepare")
        self.assertTrue(report["first_blocker"]["blocked_reason"])
        self.assertTrue(report["expected_paths"]["required_inputs"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_fixture_backed_status_aggregation_surfaces_expected_paths_and_claim_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as scratch:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._write_real_core_inputs(
                repo_root,
                categories={
                    "terrain_crop",
                    "terrain_metadata",
                    "aoi_tile_catalog",
                    "source_zone_metadata",
                    "scenario_table",
                    "source_scenario_policy",
                },
            )
            acquisition_package_path = self._write_acquisition_package(repo_root, classification="fixture_backed")
            self._write_real_context_cache_manifest(repo_root)
            artifact_root = Path(scratch) / "hazard/results/tschamut_public_pilot/target_gate_v1"
            artifact_root.mkdir(parents=True, exist_ok=True)

            report = workflow.build_report(
                command="status",
                site_config=config_path,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
                artifact_root=artifact_root,
            )

        self.assertEqual(report["workflow_summary"]["prepared_pilot_input_classification"], "fixture_backed")
        self.assertEqual(report["workflow_summary"]["workflow_classification"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["next_action"], "plan")
        self.assertEqual(report["first_blocker"]["step_id"], "public_context_readiness")
        self.assertEqual(report["first_blocker"]["blocked_reason"], "deferred_public_context_inputs")
        self.assertTrue(report["expected_paths"]["case_skeleton_path"])
        self.assertTrue(report["expected_paths"]["portable_command_plan_ignored_roots"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertEqual(report["delegate_statuses"]["aoi_workflow"], report["workflow_summary"]["workflow_classification"])

    def test_local_tiny_aoi_smoke_run_writes_reduced_outputs_and_hazard_layers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            smoke_root = Path(tmp) / "tb263_smoke"

            with mock.patch.object(
                workflow.COMMAND_PLAN,
                "build_report",
                return_value={
                    "schema_version": "portable_pilot_command_plan_v1",
                    "command_plan_status": "ready",
                },
            ):
                first = workflow.build_report(
                    command="run-local-smoke",
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    repo_root=ROOT,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                    smoke_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                    smoke_output_root=smoke_root,
                )
                stable_keys = (
                    "validation_trajectory",
                    "validation_metadata",
                    "validation_deposition",
                    "hazard_reach_probability_asc",
                    "hazard_reach_probability_tif",
                    "map_package_manifest",
                )
                first_artifacts = {key: first["smoke_run"]["artifact_sha256"][key] for key in stable_keys}
                first_map_package = first["smoke_run"]["map_package_manifest_json"]

                second = workflow.build_report(
                    command="run-local-smoke",
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    repo_root=ROOT,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                    smoke_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                    smoke_output_root=smoke_root,
                )

                smoke = first["smoke_run"]
                second_smoke = second["smoke_run"]
                validation_root = Path(smoke["validation_output_root"])
                hazard_root = Path(smoke["hazard_output_root"])

                self.assertEqual(first["status"], "smoke_completed")
                self.assertEqual(first["next_action"], "collect")
                self.assertEqual(smoke["no_heavy_debug_defaults"]["validation_output_mode"], "rebuildable_reduced_output")
                self.assertTrue(smoke["no_heavy_debug_defaults"]["plots_enabled"] is False)
                self.assertEqual(smoke["no_heavy_debug_defaults"]["conditional_curve_export"], "summary-only")
                self.assertEqual(smoke["no_heavy_debug_defaults"]["grid_csv_export"], "none")
                self.assertFalse(smoke["claim_boundaries"]["operational_claims_allowed"])
                self.assertFalse(smoke["claim_boundaries"]["scale_up_authorized"])
                self.assertFalse(smoke["claim_boundaries"]["physical_probability_claims_allowed"])
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_trajectory.csv").exists())
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv").exists())
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_deposition.csv").exists())
                self.assertFalse((validation_root / "probabilistic_phase1_smoke_trajectories").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_map_package_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_pilot_gis_package_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_reach_probability.asc").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_reach_probability.tif").exists())
                self.assertFalse(list(hazard_root.glob("*.csv")))
                self.assertEqual(
                    smoke["hazard_manifest"]["conditional_execution"]["raster_exports"]["grid_csv_export"],
                    "none",
                )
                self.assertFalse(
                    smoke["hazard_manifest"]["conditional_execution"]["raster_exports"]["grid_csv_written"]
                )
                self.assertEqual(
                    smoke["hazard_manifest"]["conditional_execution"]["conditional_curve_export"]["mode"],
                    "summary-only",
                )
                self.assertFalse(smoke["hazard_manifest"]["performance"]["plots_enabled"])
                self.assertEqual(
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                    False,
                )
                self.assertIn(
                    "return_period",
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["future_unsupported_product_labels"],
                )
                second_artifacts = {key: second_smoke["artifact_sha256"][key] for key in stable_keys}
                self.assertEqual(first_artifacts, second_artifacts)
                self.assertEqual(first_map_package, second_smoke["map_package_manifest_json"])
                self.assertEqual(
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                    second_smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                )

    def _write_candidate_config(
        self,
        repo_root: Path,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
        candidate_site_name: str = "Chant Sura / Flüelapass portability example",
    ) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data = self._rewrite_strings(config_data, "chant_sura_fluelapass_portability_example_v1", candidate_site_id)
        config_data = self._rewrite_strings(config_data, "Chant Sura / Flüelapass portability example", candidate_site_name)
        config_data["candidate_site_id"] = candidate_site_id
        config_data["candidate_site_name"] = candidate_site_name
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _write_acquisition_package(
        self,
        repo_root: Path,
        *,
        classification: str | None = None,
        classification_map: dict[str, str] | None = None,
    ) -> Path:
        package_source = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
        package = yaml.safe_load(package_source.read_text(encoding="utf-8"))
        assert isinstance(package, dict)
        for row in package.get("required_acquisition_items") or []:
            if not isinstance(row, dict):
                continue
            category = str(row.get("category") or "")
            row_classification = (classification_map or {}).get(
                category,
                classification or str(row.get("classification") or row.get("current_status") or "missing"),
            )
            row["classification"] = row_classification
            row["current_status"] = row_classification
        package_path = repo_root / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package_path.write_text(yaml.safe_dump(package, sort_keys=False), encoding="utf-8")
        return package_path

    def _write_real_context_cache_manifest(
        self,
        repo_root: Path,
        *,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
        candidate_site_name: str = "Chant Sura / Flüelapass portability example",
    ) -> None:
        manifest_path = repo_root / f"data/processed/swisstopo/{candidate_site_id}/input/public_geodata_cache_manifest.yaml"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        records = []
        product_ids = [
            "swissimage_context",
            "swisstlm3d_context",
            "swisssurface3d_context",
            "swisssurface3d_raster_context",
            "swissbuildings3d_context",
        ]
        for index, product_id in enumerate(product_ids, start=1):
            staged_path = manifest_path.parent / f"{product_id}.bin"
            metadata_path = manifest_path.parent / f"{product_id}.yaml"
            payload = f"expected-{product_id}".encode("utf-8")
            staged_path.write_bytes(payload)
            metadata = {
                "source_product_id": product_id,
                "source_product_name": product_id.replace("_", " "),
                "source_url_or_download_record": f"https://example.invalid/{product_id}",
                "product_version_or_date": "2026-05-17",
                "tile_id_or_delivery_identifier": f"tile-{index}",
                "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                "crs": "EPSG:2056",
                "resolution_m": 1.0,
                "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                "license_or_terms_reference": "example terms",
            }
            metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
            records.append(
                {
                    "product_id": product_id,
                    "source_product_id": product_id,
                    "source_product_name": product_id.replace("_", " "),
                    "source_url_or_download_record": f"https://example.invalid/{product_id}",
                    "product_version_or_date": "2026-05-17",
                    "tile_id_or_delivery_identifier": f"tile-{index}",
                    "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                    "crs": "EPSG:2056",
                    "resolution_m": 1.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "example terms",
                    "staged_path": str(staged_path),
                    "metadata_path": str(metadata_path),
                }
            )
        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name,
            "products": records,
        }
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    def _write_real_core_inputs(self, repo_root: Path, *, categories: set[str]) -> None:
        base = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1"
        (base / "input").mkdir(parents=True, exist_ok=True)
        (repo_root / "validation/policies").mkdir(parents=True, exist_ok=True)
        if "terrain_crop" in categories:
            (base / "input/terrain.asc").write_text(
                "\n".join(
                    [
                        "ncols 4",
                        "nrows 4",
                        "xllcorner 2793000.0",
                        "yllcorner 1180200.0",
                        "cellsize 2.0",
                        "NODATA_value -9999",
                        "2475.0 2475.5 2476.0 2476.5",
                        "2474.0 2474.5 2475.0 2475.5",
                        "2473.0 2473.5 2474.0 2474.5",
                        "2472.0 2472.5 2473.0 2473.5",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        if "terrain_metadata" in categories:
            (base / "input/terrain_metadata.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "tile_id": "chant_sura_fluelapass_real_lv95_crop",
                        "source_dataset": "real_chant_sura_fluelapass_core_input",
                        "source_product": "swissALTI3D",
                        "source_url": "https://example.invalid/chant_sura_fluelapass/swissalti3d",
                        "source_filename": "chant_sura_fluelapass_real_core_input.asc",
                        "source_file_present": True,
                        "download_status": "processed_real",
                        "license": "real staged input for repository tests; classifier-safe content only",
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                            "coordinate_unit": "m",
                            "height_unit": "m",
                        },
                        "raster": {
                            "format": "ESRI ASCII GRID",
                            "resolution_m": 2.0,
                            "width_px": 4,
                            "height_px": 4,
                            "nodata": -9999.0,
                        },
                        "extent_lv95_m": {
                            "xmin": 2793000.0,
                            "ymin": 1180200.0,
                            "xmax": 2793008.0,
                            "ymax": 1180208.0,
                        },
                        "preprocessing": {
                            "status": "staged_real",
                            "crop_extent_lv95_m": {
                                "xmin": 2793000.0,
                                "ymin": 1180200.0,
                                "xmax": 2793008.0,
                                "ymax": 1180208.0,
                            },
                            "resampling_method": "none",
                            "raw_sha256": None,
                            "processed_sha256": None,
                            "tool": "manual test input",
                            "processed_utc": None,
                        },
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
                            "notes": [
                                "Real-looking DEM values staged for dry-run coverage.",
                                "No classifier-trigger words are present in this file.",
                            ],
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "aoi_tile_catalog" in categories:
            (base / "input/aoi_tile_catalog.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "swisstopo_aoi_tile_catalog_v1",
                        "catalog_status": "ready",
                        "source_product": "swissALTI3D",
                        "product_id": "swissalti3d_2m",
                        "crs": "EPSG:2056",
                        "resolution_m": 2,
                        "tiles": [
                            {
                                "tile_id": "2793-1180",
                                "source_product": "swissALTI3D",
                                "source_url": "https://www.swisstopo.admin.ch/en/height-model-swissalti3d",
                                "extent_lv95_m": {
                                    "xmin": 2793000.0,
                                    "ymin": 1180000.0,
                                    "xmax": 2794000.0,
                                    "ymax": 1181000.0,
                                },
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "source_zone_metadata" in categories:
            (base / "input/source_zone_metadata.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "zone_id": "chant_sura_fluelapass_real_zone_001",
                        "source_zone_id": "chant_sura_fluelapass_real_zone_001",
                        "crs_epsg": 2056,
                        "vertical_datum": "LN02",
                        "release_sampling_policy": {
                            "source_zone_id_pattern": "chant_sura_fluelapass_real_*",
                            "source_zone_geometry": "LV95 polygon",
                            "release_point_table": "one row per release point",
                            "block_scenario_table": "CSV table with one row per block / scenario record",
                            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
                        },
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                        },
                        "geometry": {
                            "type": "polygon",
                            "coordinates": [
                                [2793001.0, 1180201.0],
                                [2793006.0, 1180201.0],
                                [2793006.0, 1180206.0],
                                [2793001.0, 1180206.0],
                            ],
                        },
                        "release_points": [
                            {
                                "release_point_id": "chant_sura_fluelapass_real_release_001",
                                "x": 2793002.0,
                                "y": 1180202.0,
                                "z_offset_m": 0.05,
                                "notes": "real staged test input",
                            }
                        ],
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
                            "source": "unit test",
                            "license": "real staged input for repository tests",
                            "notes": [
                                "Real-looking source-zone geometry staged for dry-run coverage.",
                                "No classifier-trigger words are present in this file.",
                            ],
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "scenario_table" in categories:
            (base / "input/scenario_table.csv").write_text(
                "\n".join(
                    [
                        "scenario_id,source_zone_id,block_family,relative_weight,probability_semantics,release_point_id",
                        "chant_sura_fluelapass_real_scenario_001,chant_sura_fluelapass_real_zone_001,real_block_family,1.0,normalized within a block family; no annual frequency claim,chant_sura_fluelapass_real_release_001",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        if "source_scenario_policy" in categories:
            (repo_root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "policy_id": "chant_sura_fluelapass_real_source_scenario_policy_v1",
                        "site_id": "chant_sura_fluelapass_portability_example_v1",
                        "source_zone_id_pattern": "chant_sura_fluelapass_real_*",
                        "source_zone_geometry": "LV95 polygon",
                        "release_point_table": "one row per release point",
                        "block_scenario_table": "CSV table with one row per block / scenario record",
                        "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

    def _rewrite_strings(self, payload: object, source: str, target: str) -> object:
        if isinstance(payload, str):
            return payload.replace(source, target)
        if isinstance(payload, list):
            return [self._rewrite_strings(item, source, target) for item in payload]
        if isinstance(payload, dict):
            return {key: self._rewrite_strings(value, source, target) for key, value in payload.items()}
        return payload


if __name__ == "__main__":
    unittest.main()
