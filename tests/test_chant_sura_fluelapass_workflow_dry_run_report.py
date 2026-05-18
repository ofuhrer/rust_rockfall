from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_chant_sura_fluelapass_dry_run_report.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


reporter = _load_module(SCRIPT_PATH, "summarize_chant_sura_fluelapass_dry_run_report")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_chant_sura_workflow_report_test",
)


class ChantSuraFluelapassWorkflowDryRunReportTests(unittest.TestCase):
    def test_real_core_inputs_are_ready_for_next_step_even_with_deferred_public_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=site_config,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._write_real_core_inputs(
                repo_root=repo_root,
                categories={
                    "terrain_crop",
                    "terrain_metadata",
                    "aoi_tile_catalog",
                    "source_zone_metadata",
                    "scenario_table",
                    "source_scenario_policy",
                },
            )
            acquisition_package_path = self._write_acquisition_package(repo_root, classification="real_staged")

            first = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
            )
            repeat = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
            )
            second = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
                allow_tiny_ensemble_handoff=True,
                tiny_ensemble_note="explicitly permitted for dry-run handoff coverage",
            )

        self.assertEqual(first["workflow_classification"], "ready_for_next_step")
        self.assertEqual(second["workflow_classification"], "ready_for_next_step")
        self.assertEqual(first, repeat)
        self.assertEqual(first["prepared_pilot_provenance"]["status"], "real_staged")
        self.assertEqual(first["prepared_pilot_input_classification"], "ready_real")
        self.assertEqual(first["first_missing_real_input_category"], "")
        self.assertEqual(first["first_missing_real_input_classification"], "")
        self.assertEqual(first["blocked_fixture_backed_inputs"], [])
        self.assertEqual(first["blocked_partial_real_inputs"], [])
        self.assertEqual(first["public_context_readiness"]["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(first["public_context_readiness"]["prepared_pilot_input_classification"], "ready_real")
        self.assertEqual(first["public_context_readiness"]["first_missing_real_input_category"], "")
        self.assertEqual(first["public_context_readiness"]["real_input_acquisition_handoff"]["first_missing_real_input_category"], "")
        self.assertEqual(first["real_input_acquisition_handoff"]["first_missing_real_input_category"], "")
        self.assertEqual(first["aoi_preparation"]["case_skeleton_status"], "ready")
        self.assertEqual(first["release_candidate_generation"]["candidate_metrics_status"], "ready")
        self.assertEqual(first["scenario_generation"]["scenario_plan_status"], "ready")
        self.assertEqual(first["command_planning"]["command_plan_status"], "ready")
        self.assertEqual(first["tiny_bounded_ensemble_handoff"]["status"], "blocked_missing_permission")
        self.assertEqual(second["tiny_bounded_ensemble_handoff"]["status"], "ready")
        self.assertTrue(second["tiny_bounded_ensemble_handoff"]["permission_note"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["public_context_readiness"]["synthetic_core_inputs_are_public_context_evidence"])
        self.assertTrue(first["aoi_preparation"]["case_skeleton"]["claim_boundaries"]["operational_claims_allowed"] is False)
        self.assertTrue(first["workflow_steps"])
        self.assertEqual(
            [step["step_id"] for step in first["workflow_steps"]],
            [
                "public_context_readiness",
                "aoi_preparation",
                "release_candidate_generation",
                "scenario_generation",
                "command_planning",
                "tiny_bounded_ensemble_handoff",
            ],
        )
        self.assertEqual(first["blocked_missing_inputs"], [])
        self.assertIn("ready_for_next_step", first["ready_for_next_step"]["status"])

        text_report = reporter.render_text_report(first)
        self.assertEqual(text_report, reporter.render_text_report(first))
        self.assertIn("workflow_classification: ready_for_next_step", text_report)
        self.assertIn("prepared_pilot_input_classification: ready_real", text_report)
        self.assertIn("prepared_pilot_provenance:", text_report)
        self.assertIn("public_context_readiness:", text_report)
        self.assertIn("real_input_acquisition_handoff:", text_report)
        self.assertIn("tiny_bounded_ensemble_handoff:", text_report)
        self.assertIn("ready_for_next_step:", text_report)

    def test_fixture_backed_inputs_fail_closed_even_when_paths_are_staged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)
            config_data = yaml.safe_load(site_config.read_text(encoding="utf-8"))
            config_data["fixture_profile"] = "minimal_synthetic_aoi_v1"
            site_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=site_config,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            acquisition_package_path = self._write_acquisition_package(repo_root, classification="fixture_backed")
            self._write_real_context_cache_manifest(
                repo_root,
            )

            report = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
            )

        self.assertEqual(report["workflow_classification"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["prepared_pilot_provenance"]["status"], "fixture_backed")
        self.assertEqual(report["prepared_pilot_input_classification"], "fixture_backed")
        self.assertEqual(report["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(report["first_missing_real_input_classification"], "fixture_backed")
        self.assertEqual(report["prepared_pilot_provenance"]["synthetic_fixture_profile"], "minimal_synthetic_aoi_v1")
        self.assertEqual(report["blocked_missing_inputs"], [])
        self.assertTrue(report["blocked_fixture_backed_inputs"])
        self.assertEqual(report["blocked_partial_real_inputs"], [])
        self.assertIn("synthetic fixture inputs are not public evidence", report["blocked_fixture_backed_inputs"][0])
        self.assertEqual(report["ready_for_next_step"]["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["ready_for_next_step"]["next_step"], "none")
        self.assertEqual(report["tiny_bounded_ensemble_handoff"]["status"], "blocked_fixture_backed_inputs")
        self.assertIn("synthetic fixture inputs are not public evidence", report["tiny_bounded_ensemble_handoff"]["blocked_reason"])
        self.assertEqual(report["public_context_readiness"]["prepared_pilot_input_classification"], "fixture_backed")
        self.assertEqual(report["public_context_readiness"]["first_missing_real_input_category"], "terrain_crop")

        text_report = reporter.render_text_report(report)
        self.assertIn("workflow_classification: blocked_fixture_backed_inputs", text_report)
        self.assertIn("prepared_pilot_input_classification: fixture_backed", text_report)
        self.assertIn("prepared_pilot_provenance:", text_report)
        self.assertIn("blocked_fixture_backed_inputs:", text_report)
        self.assertIn("synthetic fixture inputs are not public evidence", text_report)

    def test_partial_real_inputs_fail_closed_with_machine_readable_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=site_config,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            acquisition_package_path = self._write_acquisition_package(
                repo_root,
                classification_map={
                    "terrain_crop": "real_staged",
                    "terrain_metadata": "real_staged",
                    "aoi_tile_catalog": "real_staged",
                    "source_zone_metadata": "fixture_backed",
                    "scenario_table": "fixture_backed",
                    "source_scenario_policy": "fixture_backed",
                },
            )
            self._write_real_context_cache_manifest(repo_root)

            report = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
            )

        self.assertEqual(report["workflow_classification"], "blocked_partial_real_inputs")
        self.assertEqual(report["prepared_pilot_provenance"]["status"], "partial_real")
        self.assertEqual(report["prepared_pilot_input_classification"], "partial_real")
        self.assertEqual(report["first_missing_real_input_category"], "swissimage_context")
        self.assertEqual(report["first_missing_real_input_classification"], "deferred")
        self.assertEqual(report["public_context_readiness"]["real_context_readiness_gate_status"], "blocked_partial_real_inputs")
        self.assertEqual(report["public_context_readiness"]["prepared_pilot_input_classification"], "partial_real")
        self.assertEqual(report["blocked_missing_inputs"], [])
        self.assertFalse(report["blocked_fixture_backed_inputs"])
        self.assertTrue(report["blocked_partial_real_inputs"])
        self.assertIn("partially real", report["blocked_partial_real_inputs"][0])
        self.assertEqual(report["ready_for_next_step"]["status"], "blocked_partial_real_inputs")
        self.assertEqual(report["tiny_bounded_ensemble_handoff"]["status"], "blocked_partial_real_inputs")
        self.assertIn("partially real", report["tiny_bounded_ensemble_handoff"]["blocked_reason"])
        text_report = reporter.render_text_report(report)
        self.assertIn("workflow_classification: blocked_partial_real_inputs", text_report)
        self.assertIn("prepared_pilot_input_classification: partial_real", text_report)
        self.assertIn("blocked_partial_real_inputs:", text_report)

    def test_missing_fixture_inputs_fail_closed_as_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=site_config,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            acquisition_package_path = self._write_acquisition_package(repo_root, classification="missing")
            self._write_real_context_cache_manifest(repo_root)

            report = reporter.build_report(
                site_config,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
            )

        self.assertEqual(report["workflow_classification"], "blocked_missing_real_core_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "missing")
        self.assertEqual(report["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(report["first_missing_real_input_classification"], "missing")
        self.assertEqual(report["real_input_acquisition_handoff"]["first_missing_real_input_category"], "terrain_crop")
        self.assertIn("terrain_crop", report["real_input_acquisition_handoff"]["stop_condition"])
        self.assertEqual(report["aoi_preparation"]["case_skeleton_status"], "ready")
        self.assertEqual(report["release_candidate_generation"]["candidate_metrics_status"], "ready")
        self.assertEqual(report["scenario_generation"]["scenario_plan_status"], "ready")
        self.assertEqual(report["command_planning"]["command_plan_status"], "ready")
        self.assertEqual(report["tiny_bounded_ensemble_handoff"]["status"], "blocked_missing_real_core_inputs")
        self.assertTrue(report["blocked_missing_inputs"])
        self.assertFalse(report["blocked_fixture_backed_inputs"])
        self.assertFalse(report["blocked_partial_real_inputs"])
        self.assertIn("missing real input category", report["blocked_missing_inputs"][0])
        self.assertIn("TB-250 acquisition handoff", report["blocked_missing_inputs"][1])
        self.assertIn("blocked_missing_real_core_inputs", report["ready_for_next_step"]["status"])

    def _write_site_config(self, repo_root: Path, *, config_source: Path | None = None) -> Path:
        config_source = config_source or ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
