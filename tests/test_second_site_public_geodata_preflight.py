from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
SPEC = importlib.util.spec_from_file_location("check_second_site_public_geodata_preflight", SCRIPT_PATH)
assert SPEC is not None
preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)


class SecondSitePublicGeodataPreflightTests(unittest.TestCase):
    def test_ready_fixture_reports_required_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path())

        self.assertEqual(report["portability_preflight_status"], "ready")
        self.assertEqual(report["readiness_status"], "ready")
        self.assertEqual(report["second_site_manifest_status"], "staged_placeholder_manifest")
        self.assertEqual(report["candidate_site_id"], "placeholder_second_site_v1")
        self.assertEqual(report["candidate_site_name"], "Placeholder Second Site")
        self.assertEqual(report["candidate_selection_rationale"], "site selection remains blocked or unspecified")
        self.assertEqual(report["site_extent_or_placeholder"]["crs"], "EPSG:2056")
        self.assertEqual(report["terrain_manifest_status"], "ready")
        self.assertEqual(report["source_zone_manifest_status"], "ready")
        self.assertEqual(report["scenario_manifest_status"], "ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual(report["missing_input_categories"], [])
        self.assertEqual(report["missing_input_paths_or_patterns"], [])

        required_products = {entry["category"]: entry for entry in report["required_public_geodata_products"]}
        self.assertEqual(required_products["terrain_crop"]["status"], "ready")
        self.assertEqual(required_products["swisstlm3d_context"]["status"], "ready")
        self.assertFalse(required_products["barrier_inventory"]["required"])

        metadata_records = {entry["category"]: entry for entry in report["required_metadata_records"]}
        self.assertEqual(metadata_records["site_extent_definition"]["status"], "ready")
        self.assertEqual(metadata_records["terrain_crs_vertical_datum"]["status"], "ready")

        self.assertIn("validate_public_real_site_geodata_manifest.py", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertIn("prepare_<site_id>_public_benchmark.py", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertEqual(
            set(report.keys()),
            {
                "acquisition_or_staging_checklist",
                "assumptions_not_yet_generalized",
                "blocked_reason",
                "candidate_site_id",
                "candidate_site_name",
                "candidate_selection_rationale",
                "expected_artifact_roots",
                "missing_input_categories",
                "missing_input_paths_or_patterns",
                "operational_claims_allowed",
                "portability_preflight_status",
                "readiness_status",
                "second_site_manifest_status",
                "required_case_generation_inputs",
                "required_metadata_records",
                "required_public_geodata_products",
                "reusable_workflow_components",
                "scale_up_authorized",
                "scenario_manifest_status",
                "source_zone_manifest_status",
                "source_zone_scenario_contract",
                "site_extent_or_placeholder",
                "site_specific_required_inputs",
                "terrain_manifest_status",
            },
        )

    def test_candidate_example_fixture_is_blocked_and_records_manifest_contract(self) -> None:
        report = preflight.build_report(self._candidate_example_config_path())

        self.assertEqual(report["second_site_manifest_status"], "staged_candidate_manifest")
        self.assertEqual(report["portability_preflight_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertIn("Chant Sura is the clearest concrete Swiss candidate", report["candidate_selection_rationale"])
        self.assertEqual(report["terrain_manifest_status"], "blocked_missing_inputs")
        self.assertEqual(report["source_zone_manifest_status"], "blocked_missing_inputs")
        self.assertEqual(report["scenario_manifest_status"], "blocked_missing_inputs")
        self.assertIn("source_zone_scenario_contract", report)
        self.assertIn("source_zone_id_pattern", report["source_zone_scenario_contract"])
        self.assertIn("Candidate selection rationale", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertIn("Chant Sura / Flüelapass portability example", "\n".join(report["acquisition_or_staging_checklist"]))

    def test_missing_context_metadata_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit=["swisstlm3d_metadata"])

        self.assertEqual(report["portability_preflight_status"], "blocked_missing_inputs")
        self.assertIn("swisstlm3d_context", report["missing_input_categories"])
        self.assertIn(
            str(root / "data/processed/swisstopo/placeholder_second_site_v1/context/swisstlm3d/metadata.json"),
            report["missing_input_paths_or_patterns"],
        )
        self.assertIn("missing required portability inputs", report["blocked_reason"])

    def test_missing_site_extent_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._build_inputs(root)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit_site_extent=True)

        self.assertEqual(report["portability_preflight_status"], "blocked_missing_inputs")
        self.assertIn("site_extent_definition", report["missing_input_categories"])

    def test_text_report_mentions_commands_and_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit=["swisstlm3d_metadata"])

        text = preflight.render_text_report(report)
        self.assertIn("portability_preflight_status: blocked_missing_inputs", text)
        self.assertIn("validate_public_real_site_conditional_pilot_run.py", text)
        self.assertIn("missing_input_categories:", text)
        self.assertIn("second_site_manifest_status: staged_placeholder_manifest", text)

    def _fixture_config_path(self) -> Path:
        return ROOT / "tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml"

    def _candidate_example_config_path(self) -> Path:
        return ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"

    def _build_report(
        self,
        root: Path,
        *,
        site_config: Path | None = None,
        omit_site_extent: bool = False,
        omit: list[str] | None = None,
    ) -> dict[str, object]:
        original_root = preflight.ROOT
        try:
            preflight.ROOT = root
            self._build_inputs(root, omit=omit)
            if omit_site_extent:
                config = yaml.safe_load(self._fixture_config_path().read_text(encoding="utf-8"))
                config.pop("site_extent", None)
                site_config = root / "site_config.yaml"
                site_config.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            config_path = site_config or self._fixture_config_path()
            preflight.ROOT = root
            return preflight.build_report(config_path)
        finally:
            preflight.ROOT = original_root

    def _build_inputs(self, root: Path, omit: list[str] | None = None) -> None:
        omit = omit or []
        config = yaml.safe_load(self._fixture_config_path().read_text(encoding="utf-8"))
        site_id = config["candidate_site_id"]
        paths = preflight.build_paths(site_id, config)
        input_root = paths["processed_input_root"]
        context_root = paths["processed_context_root"]
        validation_root = paths["validation_case_root"]
        hazard_root = paths["hazard_results_root"]
        policy_root = root / "validation/policies"

        for path in [
            input_root,
            context_root / "swissimage",
            context_root / "swisstlm3d",
            context_root / "swisssurface3d",
            context_root / "swisssurface3d_raster",
            context_root / "swissbuildings3d",
            validation_root,
            hazard_root,
            policy_root,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        files = {
            "terrain_crop": (paths["terrain_crop"], "terrain\n"),
            "terrain_metadata": (paths["terrain_metadata"], "crs: EPSG:2056\nvertical_datum: LN02\n"),
            "source_zone_metadata": (paths["source_zone_metadata"], "source_zone_id: fixture_zone\n"),
            "scenario_table": (paths["scenario_table"], "scenario_id,probability\nA,1.0\n"),
            "source_scenario_policy": (paths["source_scenario_policy"], "policy_id: fixture_policy\n"),
            "swisstlm3d_metadata": (
                paths["swisstlm3d_metadata"],
                json.dumps({"source_product": "swissTLM3D", "staged_asset_present": True}),
            ),
            "swissimage_context": (paths["swissimage_context"] / "tile.txt", "image\n"),
            "swisssurface3d_context": (paths["swisssurface3d_context"] / "tile.txt", "surface\n"),
            "swisssurface3d_raster_context": (paths["swisssurface3d_raster_context"] / "tile.txt", "raster\n"),
            "swissbuildings3d_context": (paths["swissbuildings3d_context"] / "tile.txt", "buildings\n"),
        }
        for key, (path, content) in files.items():
            if key in omit:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
