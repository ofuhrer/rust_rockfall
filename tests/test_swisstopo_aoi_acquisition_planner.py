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
            try:
                preflight.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root

        self.assertEqual(report["planner_status"], "ready")
        self.assertEqual(report["acquisition_boundary_status"], "deferred_public_context_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertIn("Chant Sura is the clearest concrete Swiss candidate", report["candidate_selection_rationale"])
        self.assertEqual(report["acquisition_manifest_status"], "ready")
        self.assertEqual(report["public_context_acquisition_summary"]["product_count"], 5)
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 5)
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
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
            try:
                preflight.ROOT = repo_root
                report = planner.build_report(config_path)
            finally:
                preflight.ROOT = original_root

        json_report = json.dumps(report, indent=2, sort_keys=True)
        self.assertEqual(json_report, json.dumps(report, indent=2, sort_keys=True))

        text_report = planner.render_text_report(report)
        self.assertIn("schema_version: swisstopo_aoi_acquisition_dry_run_v1", text_report)
        self.assertIn("required_public_geodata_products:", text_report)
        self.assertIn("public_context_acquisition_plan:", text_report)
        self.assertIn("unresolved_acquisition_decisions:", text_report)
        self.assertIn("deferred_public_context_categories:", text_report)

    def _write_site_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
