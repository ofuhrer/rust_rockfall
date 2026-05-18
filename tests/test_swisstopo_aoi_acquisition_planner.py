from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_swisstopo_aoi_acquisition.py"
PREFLIGHT_SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
NESTED_CATALOG_FIXTURE = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/catalog_shapes/nested_product_variants.yaml"
)
BLOCKED_CATALOG_FIXTURE = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/catalog_shapes/blocked_missing_metadata.yaml"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = _load_module(SCRIPT_PATH, "plan_swisstopo_aoi_acquisition")
preflight = _load_module(PREFLIGHT_SCRIPT_PATH, "check_second_site_public_geodata_preflight_for_aoi_planner_test")
staging = _load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_aoi_planner_test")


class SwisstopoAoiAcquisitionPlannerTests(unittest.TestCase):
    def test_candidate_fixture_reports_current_deferred_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            original_root = preflight.ROOT
            original_planner_root = planner.PREFLIGHT.ROOT
            try:
                preflight.ROOT = repo_root
                planner.PREFLIGHT.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root
                planner.PREFLIGHT.ROOT = original_planner_root

        self.assertEqual(report["planner_status"], "ready")
        self.assertEqual(report["acquisition_boundary_status"], "deferred_public_context_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertIn("Chant Sura is the clearest concrete Swiss candidate", report["candidate_selection_rationale"])
        self.assertEqual(report["acquisition_manifest_status"], "ready")
        self.assertEqual(report["public_context_acquisition_summary"]["product_count"], 5)
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 5)
        self.assertEqual(report["aoi_tile_discovery"]["discovery_status"], "ready")
        self.assertEqual(report["aoi_tile_discovery"]["tile_candidate_count"], 1)
        self.assertEqual(report["aoi_tile_discovery"]["tile_candidates"][0]["tile_id"], "2793-1180")
        self.assertEqual(report["aoi_tile_discovery"]["catalog_manifest"]["catalog_product_id"], "swissalti3d_2m")
        self.assertEqual(report["aoi_tile_discovery"]["product_candidate_count"], 1)
        self.assertEqual(report["aoi_tile_discovery"]["product_candidates"][0]["product_id"], "swissalti3d_2m")
        self.assertTrue(
            report["aoi_tile_discovery"]["product_candidates"][0]["expected_staging_root"].endswith(
                "data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1"
            )
        )
        self.assertEqual(report["aoi_tile_discovery"]["resolver_status"], "ready")
        resolution_rows = {entry["category"]: entry for entry in report["aoi_tile_discovery"]["product_resolution_rows"]}
        self.assertEqual(
            list(resolution_rows),
            [
                "terrain_crop",
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )
        self.assertEqual(resolution_rows["terrain_crop"]["tile_resolution_status"], "resolved")
        self.assertEqual(resolution_rows["terrain_crop"]["expected_tile_ids"], ["2793-1180"])
        self.assertIn("<product_version_or_date>", resolution_rows["terrain_crop"]["raw_path"])
        self.assertIn("<tile_id_or_delivery_identifier>", resolution_rows["terrain_crop"]["raw_path"])
        self.assertEqual(resolution_rows["swissimage_context"]["tile_resolution_status"], "blocked_unresolved_tile_ids")
        self.assertTrue(resolution_rows["swissimage_context"]["tile_blockers"])
        cache_template = report["public_geodata_workflow_contract"]["public_geodata_cache_contract"]["cache_manifest_template"]
        self.assertEqual(cache_template["schema_version"], "swiss_public_geodata_cache_manifest_template_v1")
        self.assertEqual(cache_template["retry_resume_fields"], [
            "attempt_count",
            "last_attempt_at",
            "resume_token",
            "resume_status",
            "retry_authorized",
            "resume_authorized",
        ])
        self.assertEqual(cache_template["products"][0]["product_label"], "swissALTI3D")
        self.assertEqual(cache_template["products"][0]["checksum_sha256"], "")
        self.assertEqual(cache_template["products"][0]["retry_resume"]["attempt_count"], 0)
        self.assertFalse(Path(cache_template["cache_manifest_path"]).exists())
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
        self.assertEqual(report["public_geodata_workflow_contract"]["public_geodata_contract_readiness_status"], "ready")
        self.assertEqual(report["public_geodata_workflow_contract"]["synthetic_fixture_readiness_status"], "not_applicable")
        self.assertEqual(
            report["deferred_public_context_categories"],
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )

        product_rows = {entry["category"]: entry for entry in report["required_public_geodata_products"]}
        self.assertEqual(product_rows["terrain_crop"]["current_status"], "ready")
        self.assertEqual(product_rows["swissimage_context"]["current_status"], "deferred_public_context")
        self.assertEqual(product_rows["swissimage_context"]["expected_staged_path"], report["expected_staging_paths"]["swissimage_context"])
        self.assertFalse(product_rows["barrier_inventory"]["required"])
        plan_rows = {entry["category"]: entry for entry in report["public_context_acquisition_plan"]}
        self.assertTrue(plan_rows["swissimage_context"]["expected_staging_root"].endswith("data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"))

        metadata_rows = {entry["category"]: entry for entry in report["required_metadata_records"]}
        self.assertEqual(metadata_rows["terrain_metadata"]["current_status"], "ready")
        self.assertEqual(metadata_rows["swisstlm3d_metadata"]["current_status"], "missing")

        unresolved_categories = [entry["category"] for entry in report["unresolved_acquisition_decisions"]]
        self.assertEqual(
            unresolved_categories,
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisstlm3d_metadata",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )
        self.assertNotIn("barrier_inventory", unresolved_categories)
        self.assertEqual(report["claim_boundaries"]["operational_claims_allowed"], False)
        self.assertEqual(report["claim_boundaries"]["scale_up_authorized"], False)
        self.assertTrue(report["public_context_acquisition_plan"][0]["expected_staging_root"].endswith("data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"))

    def test_text_and_json_output_remain_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            original_root = preflight.ROOT
            original_planner_root = planner.PREFLIGHT.ROOT
            try:
                preflight.ROOT = repo_root
                planner.PREFLIGHT.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root
                planner.PREFLIGHT.ROOT = original_planner_root

        json_report = json.dumps(report, indent=2, sort_keys=True)
        self.assertEqual(json_report, json.dumps(report, indent=2, sort_keys=True))

        text_report = planner.render_text_report(report)
        self.assertIn("schema_version: swisstopo_aoi_acquisition_dry_run_v1", text_report)
        self.assertIn("public_geodata_workflow_contract:", text_report)
        self.assertIn("aoi_tile_discovery:", text_report)
        self.assertIn("resolver_status:", text_report)
        self.assertIn("product_resolution_rows:", text_report)
        self.assertIn("cache_manifest_template:", text_report)
        self.assertIn("public_geodata_contract_readiness_status: ready", text_report)
        self.assertIn("required_public_geodata_products:", text_report)
        self.assertIn("public_context_acquisition_plan:", text_report)
        self.assertIn("unresolved_acquisition_decisions:", text_report)
        self.assertIn("deferred_public_context_categories:", text_report)
        self.assertIn("catalog_blockers:", text_report)
        self.assertIn("product_candidates:", text_report)

    def test_nested_catalog_variants_report_multiple_product_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._set_catalog_fixture(config_path, NESTED_CATALOG_FIXTURE)

            original_root = preflight.ROOT
            original_planner_root = planner.PREFLIGHT.ROOT
            try:
                preflight.ROOT = repo_root
                planner.PREFLIGHT.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root
                planner.PREFLIGHT.ROOT = original_planner_root

        discovery = report["aoi_tile_discovery"]
        self.assertEqual(discovery["discovery_status"], "ready")
        self.assertEqual(discovery["tile_candidate_count"], 2)
        self.assertEqual(discovery["product_candidate_count"], 2)
        self.assertEqual(
            [entry["product_id"] for entry in discovery["product_candidates"]],
            ["swissalti3d_0_5m", "swissalti3d_2m"],
        )
        self.assertEqual([entry["resolution_m"] for entry in discovery["product_candidates"]], [0.5, 2])
        self.assertEqual([entry["tile_id"] for entry in discovery["tile_candidates"]], ["2793-1180", "2793-1180"])
        self.assertEqual([entry["product_id"] for entry in discovery["tile_candidates"]], ["swissalti3d_0_5m", "swissalti3d_2m"])
        self.assertTrue(
            discovery["product_candidates"][0]["expected_staging_root"].endswith(
                "data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1/variant_0_5m"
            )
        )
        self.assertTrue(
            discovery["product_candidates"][1]["expected_staging_root"].endswith(
                "data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1/variant_2m"
            )
        )

    def test_blocked_catalog_fixture_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._set_catalog_fixture(config_path, BLOCKED_CATALOG_FIXTURE)

            original_root = preflight.ROOT
            original_planner_root = planner.PREFLIGHT.ROOT
            try:
                preflight.ROOT = repo_root
                planner.PREFLIGHT.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root
                planner.PREFLIGHT.ROOT = original_planner_root

        discovery = report["aoi_tile_discovery"]
        self.assertEqual(discovery["discovery_status"], "blocked_missing_inputs")
        self.assertEqual(discovery["catalog_status"], "blocked_missing_inputs")
        self.assertTrue(discovery["catalog_blockers"])
        self.assertEqual(discovery["tile_candidate_count"], 0)
        self.assertEqual(discovery["product_candidate_count"], 0)
        self.assertEqual(discovery["tile_candidates"], [])
        self.assertEqual(discovery["product_candidates"], [])
        self.assertEqual(report["planner_status"], "blocked_missing_inputs")
        self.assertEqual(report["acquisition_boundary_status"], "deferred_public_context_inputs")

    def _write_site_config(self, repo_root: Path, catalog_fixture: Path | None = None) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _set_catalog_fixture(self, config_path: Path, catalog_fixture: Path) -> None:
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config_data["expected_aoi_tile_catalog_path"] = str(catalog_fixture)
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
