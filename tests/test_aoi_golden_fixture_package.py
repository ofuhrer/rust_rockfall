from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from scripts import bootstrap_aoi_manifest as bootstrap
from scripts import build_hazard_layers as hazard
from scripts import check_second_site_public_geodata_preflight as preflight
from scripts import generate_aoi_map_qa_review as qa_review
from scripts import package_aoi_hazard_map as packager
from scripts import plan_aoi_to_prepared_pilot_dry_run as prepared_planner
from scripts import plan_aoi_terrain_preprocessing as terrain_planner


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1"
SITE_CONFIG_SOURCE = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
ACQUISITION_MANIFEST_SOURCE = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"


class AoiGoldenFixturePackageTests(unittest.TestCase):
    def test_clean_checkout_fixture_package_supports_bootstrap_preflight_and_prepared_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as bootstrap_tmp:
            repo_root = Path(tmp)
            site_config = self._stage_fixture_package(repo_root)
            release_polygon = self._write_release_polygon(repo_root)

            bootstrap_report = bootstrap.build_report(
                output_root=Path(bootstrap_tmp) / "bootstrap_fixture",
                site_id="chant_sura_fluelapass_portability_example_v1",
                site_name="Chant Sura / Fluelapass portability example",
                crs="EPSG:2056",
                vertical_datum="LN02",
                bounds=[2793000.0, 1180200.0, 2793008.0, 1180208.0],
            )
            cache_report = preflight.verify_public_geodata_cache(
                repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml"
            )
            terrain_report = terrain_planner.build_report(repo_root=repo_root, site_config=site_config)
            prepared_input_report = terrain_planner.build_prepared_input_report(
                repo_root=repo_root,
                site_config=site_config,
                prepared_input_root=repo_root
                / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/prepared_input",
            )
            prepared_input_manifest_exists = Path(prepared_input_report["prepared_input_manifest_path"]).exists()
            planning_report = prepared_planner.build_report(
                site_config,
                repo_root=repo_root,
                release_polygon_path=release_polygon,
                skeleton_output_root=Path(bootstrap_tmp)
                / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run",
            )

        self.assertEqual(bootstrap_report["bootstrap_status"], "ready")
        self.assertTrue(bootstrap_report["validation_notes"])
        self.assertIn("metadata-only", " ".join(bootstrap_report["validation_notes"]))

        self.assertEqual(cache_report["verification_status"], "verified")
        self.assertEqual(cache_report["product_count"], 1)
        self.assertEqual(cache_report["products"][0]["verification_status"], "verified")
        self.assertEqual(cache_report["products"][0]["product_id"], "terrain_crop")

        self.assertEqual(terrain_report["terrain_preprocessing_status"], "ready")
        self.assertEqual(terrain_report["terrain_preprocessing_package"]["source_tile_ids"], ["2793-1180"])
        self.assertEqual(terrain_report["terrain_summary"]["resolution_m"], 2.0)
        self.assertEqual(terrain_report["terrain_summary"]["extent_lv95_m"]["xmin"], 2793000.0)

        self.assertEqual(prepared_input_report["prepared_input_status"], "partial_context")
        self.assertTrue(prepared_input_report["prepared_input_written"])
        self.assertTrue(prepared_input_manifest_exists)
        self.assertTrue(
            prepared_input_report["context_availability_summary"]["missing_context_count"] > 0
        )
        self.assertEqual(prepared_input_report["terrain_qa_summary"]["summary_status"], "partial_context")

        self.assertEqual(planning_report["workflow_status"], "blocked_missing_inputs")
        self.assertIn("command_plan_hooks", planning_report)
        self.assertTrue(planning_report["command_plan_hooks"])
        self.assertTrue(
            any(
                hook["command_id"] == "second_site_release_plan_dry_run"
                for hook in planning_report["command_plan_hooks"]
            )
        )
        self.assertTrue(planning_report["case_skeleton_output"]["case_skeleton_path"].endswith("case_skeleton.yaml"))

    def test_clean_checkout_fixture_package_supports_tiny_smoke_packaging_and_qa_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._stage_fixture_package(repo_root)
            smoke_root = repo_root / "smoke_hazard"
            output_root = repo_root / "smoke_package"

            with mock.patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self._fake_cog_conversion_ready):
                status = hazard.main_with_args(
                    [
                        "--case",
                        str(ROOT / "tests/fixtures/hazard/plane_case.yaml"),
                        "--diagnostics",
                        str(ROOT / "tests/fixtures/hazard/diagnostics.json"),
                        "--output-dir",
                        str(smoke_root),
                        "--cell-size",
                        "1.0",
                        "--no-plots",
                        "--export-geotiff",
                        "--pilot-gis-package",
                        "--pilot-gis-package-manifest-json",
                        str(smoke_root / "plane_pilot_gis_package_manifest.json"),
                        "--map-package-manifest-json",
                        str(smoke_root / "plane_map_package_manifest.json"),
                        "--source-zone-metadata-path",
                        str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"),
                        "--scenario-table-path",
                        str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv"),
                        "--map-product-id",
                        "aoi_to_map_golden_fixture",
                        "--probability-mode",
                        "unweighted_diagnostic",
                        "--normalization-scope",
                        "conditioned_on_filter",
                        "--pilot-gis-qa-status",
                        "inconclusive",
                        "--pilot-gis-qa-note",
                        "Regression fixture-backed AOI smoke package.",
                    ]
                )
                package_report = packager.package_aoi_hazard_map(smoke_root, output_root, overwrite=True)
                package_manifest_exists = Path(package_report["package_manifest_path"]).exists()
                summary_exists = Path(package_report["summary_path"]).exists()
            review_report = qa_review.build_review_surface(input_root=output_root, output_root=repo_root / "review")

        self.assertEqual(status, 0)
        self.assertEqual(package_report["status"], "map_package_ready")
        self.assertEqual(package_report["map_product_id"], "aoi_to_map_golden_fixture")
        self.assertEqual(package_report["claim_boundary"]["operational_status"], "research_diagnostic")
        self.assertTrue(package_manifest_exists)
        self.assertTrue(summary_exists)
        self.assertEqual(review_report["status"], "review_ready_with_warnings")
        self.assertEqual(review_report["layer_presence"]["context_layers"]["count"], 0)
        self.assertIn("missing context layers", "\n".join(review_report["warnings"]))
        self.assertIn("non-operational status", "\n".join(review_report["warnings"]))
        self.assertEqual(review_report["layer_presence"]["hazard_layers"]["count"], len(package_report["raster_outputs"]))

    def _stage_fixture_package(self, repo_root: Path) -> Path:
        fixture_root = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1"
        fixture_root.mkdir(parents=True, exist_ok=True)
        (fixture_root / "input").mkdir(parents=True, exist_ok=True)
        (fixture_root / "validation" / "policies").mkdir(parents=True, exist_ok=True)
        (repo_root / "validation" / "policies").mkdir(parents=True, exist_ok=True)

        for relative_path in [
            "README.md",
            "aoi_manifest.yaml",
            "input/aoi_tile_catalog.yaml",
            "input/public_geodata_cache_manifest.yaml",
            "input/terrain.asc",
            "input/terrain_metadata.yaml",
            "input/source_zone_metadata.yaml",
            "input/scenario_table.csv",
        ]:
            shutil.copy2(FIXTURE_ROOT / relative_path, fixture_root / relative_path)

        shutil.copy2(
            ROOT / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml",
            repo_root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml",
        )

        acquisition_manifest = yaml.safe_load(ACQUISITION_MANIFEST_SOURCE.read_text(encoding="utf-8"))
        config = yaml.safe_load(SITE_CONFIG_SOURCE.read_text(encoding="utf-8"))
        config["acquisition_manifest_path"] = "chant_sura_fluelapass_public_geodata_acquisition.yaml"
        config["fixture_profile"] = "chant_sura_fluelapass_real_aoi_golden_fixture_v1"
        config["candidate_selection_rationale"] = (
            "Clean-checkout AOI regression fixture with real-like public-data metadata and a tiny terrain crop."
        )
        (repo_root / "site_config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        (repo_root / "chant_sura_fluelapass_public_geodata_acquisition.yaml").write_text(
            yaml.safe_dump(acquisition_manifest, sort_keys=False),
            encoding="utf-8",
        )
        return repo_root / "site_config.yaml"

    def _write_release_polygon(self, repo_root: Path) -> Path:
        path = repo_root / "release_polygon.geojson"
        payload = {
            "type": "Polygon",
            "coordinates": [
                [
                    [2793001.0, 1180201.0],
                    [2793006.0, 1180201.0],
                    [2793006.0, 1180206.0],
                    [2793001.0, 1180206.0],
                    [2793001.0, 1180201.0],
                ]
            ],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def _fake_cog_conversion_ready(self, input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(f"converted:{input_path.name}".encode("utf-8"))
        return {
            "status": "cog_conversion_sample_ready",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "verification": {
                "status": "ok",
                "sample_raster_tiled": True,
                "sample_raster_overviews": True,
                "sample_raster_cog_layout": True,
            },
            "output_exists": True,
            "output_bytes": output_path.stat().st_size,
            "blockers": [],
        }


if __name__ == "__main__":
    unittest.main()
