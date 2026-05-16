from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_release_zone_heuristic_dry_run.py"
PREFLIGHT_SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = _load_module(SCRIPT_PATH, "plan_release_zone_heuristic_dry_run")
preflight = _load_module(PREFLIGHT_SCRIPT_PATH, "check_second_site_public_geodata_preflight_for_release_zone_heuristic_test")
staging = _load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_release_zone_heuristic_test")


class ReleaseZoneHeuristicDryRunTests(unittest.TestCase):
    def test_candidate_fixture_reports_deferred_public_context_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = planner.build_report(config_path, repo_root=repo_root)

        self.assertEqual(report["heuristic_dry_run_status"], "deferred_public_context_inputs")
        self.assertEqual(report["candidate_release_zone_set_status"], "not_generated")
        self.assertEqual(report["candidate_release_zone_interpretation"], "not_claimed")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertEqual(
            report["release_zone_candidate_generation_contract"]["candidate_generation_label"],
            "heuristic_candidate_generation_only",
        )
        self.assertEqual(
            report["release_zone_candidate_generation_contract"]["validated_release_zone_evidence_status"],
            "not_claimed",
        )
        self.assertEqual(report["release_zone_candidate_generation_contract"]["output_geometry_schema"]["crs"], "EPSG:2056")
        self.assertEqual(
            report["release_zone_candidate_generation_contract"]["screening_inputs"][0]["input_id"],
            "terrain_crop",
        )
        self.assertEqual(
            report["release_zone_candidate_generation_contract"]["terrain_derivatives"][0]["derivative_id"],
            "slope",
        )
        self.assertEqual(
            report["release_zone_candidate_generation_contract"]["context_exclusions"][0]["category"],
            "swisstlm3d_context",
        )
        self.assertEqual(report["heuristic_summary"]["deferred_public_context_inputs_status"], "deferred_public_context_inputs")

        requirement_rows = {entry["requirement_id"]: entry for entry in report["heuristic_requirements"]}
        self.assertEqual(requirement_rows["finite_aoi_extent"]["status"], "ready")
        self.assertEqual(requirement_rows["terrain_screening"]["status"], "ready")
        self.assertEqual(requirement_rows["source_zone_contract"]["status"], "ready")
        self.assertEqual(requirement_rows["public_context_prerequisites"]["status"], "deferred_public_context_inputs")
        self.assertEqual(requirement_rows["candidate_release_zone_set"]["status"], "not_generated")

        heuristic_inputs = {entry["category"]: entry for entry in report["heuristic_inputs"]}
        self.assertEqual(heuristic_inputs["site_extent_definition"]["status"], "ready")
        self.assertEqual(heuristic_inputs["terrain_crop"]["status"], "ready")
        self.assertEqual(heuristic_inputs["source_scenario_policy"]["status"], "ready")
        self.assertEqual(heuristic_inputs["swisstlm3d_metadata"]["status"], "deferred_public_context")
        self.assertEqual(
            heuristic_inputs["swissimage_context"]["path_or_pattern"],
            "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage",
        )

        blocked_categories = [entry["category"] for entry in report["blocked_missing_products"]]
        self.assertEqual(
            blocked_categories,
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisstlm3d_metadata",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )
        deferred_categories = [entry["category"] for entry in report["deferred_public_context_inputs"]]
        self.assertEqual(
            deferred_categories,
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisstlm3d_metadata",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )
        self.assertIn("no candidate release-zone set is claimed", report["blocked_reason"])
        self.assertEqual(report["evidence_labels"][1]["status"], "not_claimed")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_text_output_remains_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = planner.build_report(config_path, repo_root=repo_root)

        text_report = planner.render_text_report(report)
        self.assertEqual(text_report, planner.render_text_report(report))
        self.assertIn("schema_version: release_zone_heuristic_dry_run_v1", text_report)
        self.assertIn("release_zone_candidate_generation_contract:", text_report)
        self.assertIn("heuristic_requirements:", text_report)
        self.assertIn("blocked_missing_products:", text_report)
        self.assertIn("deferred_public_context_inputs:", text_report)
        self.assertIn("heuristic_assumptions:", text_report)
        self.assertIn("evidence_labels:", text_report)

    def test_minimal_synthetic_aoi_fixture_emits_candidate_generation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._minimal_synthetic_aoi_config_path(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = planner.build_report(config_path, repo_root=repo_root)

        contract = report["release_zone_candidate_generation_contract"]
        self.assertEqual(report["candidate_site_id"], "minimal_synthetic_aoi_v1")
        self.assertEqual(report["candidate_site_name"], "Minimal Synthetic AOI")
        self.assertEqual(contract["synthetic_fixture_profile"], "minimal_synthetic_aoi_v1")
        self.assertEqual(contract["candidate_generation_label"], "heuristic_candidate_generation_only")
        self.assertEqual(contract["validated_release_zone_evidence_label"], "not_claimed")
        self.assertEqual(contract["terrain_derivatives"][1]["derivative_id"], "roughness")
        self.assertEqual(contract["output_geometry_schema"]["label"], "candidate_generation_only")
        self.assertEqual(contract["required_provenance"][0]["field"], "source_product_name")
        self.assertEqual(contract["screening_inputs"][2]["category"], "swisstlm3d_context")
        self.assertEqual(report["evidence_labels"][0]["label_id"], "candidate_generation_only")
        self.assertIn("candidate_generation_only", planner.render_text_report(report))

    def _write_site_config(self, root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _minimal_synthetic_aoi_config_path(self, root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/minimal_synthetic_aoi.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_path = root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
