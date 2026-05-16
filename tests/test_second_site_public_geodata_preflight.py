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
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
SPEC = importlib.util.spec_from_file_location("check_second_site_public_geodata_preflight", SCRIPT_PATH)
assert SPEC is not None
preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)

STAGING_SPEC = importlib.util.spec_from_file_location(
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs",
    STAGING_SCRIPT_PATH,
)
assert STAGING_SPEC is not None
staging = importlib.util.module_from_spec(STAGING_SPEC)
assert STAGING_SPEC.loader is not None
sys.modules[STAGING_SPEC.name] = staging
STAGING_SPEC.loader.exec_module(staging)


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
        self.assertEqual(report["public_context_boundary_status"], "ready")
        self.assertEqual(report["acquisition_manifest_status"], "ready")
        self.assertTrue(report["acquisition_manifest_path"].endswith("chant_sura_fluelapass_public_geodata_acquisition.yaml"))
        self.assertGreaterEqual(report["acquisition_manifest_category_count"], 10)
        self.assertEqual(report["public_context_acquisition_summary"]["product_count"], 5)
        self.assertEqual(report["public_context_acquisition_summary"]["ready_product_count"], 0)
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 5)
        self.assertTrue(
            report["public_context_acquisition_summary"]["expected_staging_roots"][0].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"
            )
        )
        self.assertIn("Review acquisition manifest at", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["distributed_execution_authorized"])
        self.assertEqual(report["missing_input_categories"], [])
        self.assertEqual(report["missing_input_paths_or_patterns"], [])
        self.assertEqual(report["core_input_status"], "ready")
        self.assertEqual(report["deferred_public_context_status"], "ready")
        self.assertEqual(report["deferred_public_context_categories"], [])
        self.assertEqual(report["deferred_public_context_paths_or_patterns"], [])
        self.assertEqual(report["deferred_public_context_references"], {})
        self.assertEqual(report["blocked_second_site_commands"][0]["blocked_status"], "template_only")
        self.assertEqual(report["synthetic_fixture_boundaries"][1]["allowed"], False)

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
                "acquisition_manifest_category_count",
                "acquisition_manifest_command_template_count",
                "acquisition_manifest_expected_ignored_roots",
                "acquisition_manifest_path",
                "acquisition_manifest_product_summaries",
                "acquisition_manifest_status",
                "assumptions_not_yet_generalized",
                "blocked_second_site_commands",
                "core_input_status",
                "blocked_reason",
                "candidate_site_id",
                "candidate_site_name",
                "candidate_selection_rationale",
                "claim_boundaries",
                "deferred_public_context_categories",
                "deferred_public_context_paths_or_patterns",
                "deferred_public_context_references",
                "deferred_public_context_status",
                "expected_local_paths",
                "expected_artifact_roots",
                "missing_input_categories",
                "missing_input_paths_or_patterns",
                "metadata_requirements",
                "operational_claims_allowed",
                "public_context_acquisition_plan",
                "public_context_acquisition_summary",
                "public_context_boundary_status",
                "public_context_product_requirements",
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
                "synthetic_fixture_boundaries",
                "terrain_manifest_status",
            },
        )

    def test_candidate_example_fixture_is_blocked_and_records_manifest_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(
                root,
                site_config=self._candidate_example_config_path(),
                omit=[
                    "swissimage_context",
                    "swisstlm3d_metadata",
                    "swisssurface3d_context",
                    "swisssurface3d_raster_context",
                    "swissbuildings3d_context",
                ],
            )

        self.assertEqual(report["second_site_manifest_status"], "staged_candidate_manifest")
        self.assertEqual(report["portability_preflight_status"], "deferred_public_context_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertIn("Chant Sura is the clearest concrete Swiss candidate", report["candidate_selection_rationale"])
        self.assertEqual(report["acquisition_manifest_status"], "ready")
        self.assertTrue(report["acquisition_manifest_path"].endswith("chant_sura_fluelapass_public_geodata_acquisition.yaml"))
        self.assertGreater(report["acquisition_manifest_command_template_count"], 0)
        self.assertEqual(report["public_context_acquisition_summary"]["product_count"], 5)
        self.assertEqual(report["public_context_acquisition_summary"]["ready_product_count"], 5)
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 0)
        self.assertEqual(
            report["public_context_acquisition_plan"][0]["expected_staging_root"],
            str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"),
        )
        self.assertEqual(report["public_context_acquisition_plan"][1]["metadata_contract"][0], "expected_staged_path")
        self.assertEqual(report["terrain_manifest_status"], "ready")
        self.assertEqual(report["source_zone_manifest_status"], "ready")
        self.assertEqual(report["scenario_manifest_status"], "ready")
        self.assertEqual(report["public_context_boundary_status"], "deferred_public_context_inputs")
        self.assertIn("source_zone_scenario_contract", report)
        self.assertIn("source_zone_id_pattern", report["source_zone_scenario_contract"])
        self.assertIn("Candidate selection rationale", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertIn("Chant Sura / Flüelapass portability example", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertIn("Public-context acquisition plan roots", "\n".join(report["acquisition_or_staging_checklist"]))
        self.assertEqual(report["core_input_status"], "ready")
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
        self.assertEqual(
            set(report["deferred_public_context_categories"]),
            {
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            },
        )
        self.assertEqual(report["missing_input_categories"], [])
        self.assertIn("public-context products are intentionally deferred", report["blocked_reason"])
        product_requirements = {entry["category"]: entry for entry in report["public_context_product_requirements"]}
        self.assertFalse(product_requirements["swissimage_context"]["synthetic_fixture_allowed"])
        self.assertFalse(product_requirements["swissimage_context"]["staged"])
        self.assertEqual(
            product_requirements["swissimage_context"]["expected_staging_root"],
            str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"),
        )
        self.assertTrue(
            report["expected_local_paths"]["swissimage_context"].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"
            ),
        )
        self.assertIn("metadata.json", report["metadata_requirements"]["swisstlm3d_metadata"])

    def test_missing_context_metadata_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit=["swisstlm3d_metadata"])

        self.assertEqual(report["portability_preflight_status"], "deferred_public_context_inputs")
        self.assertEqual(report["public_context_boundary_status"], "deferred_public_context_inputs")
        self.assertIn("swisstlm3d_context", report["deferred_public_context_categories"])
        self.assertIn(
            str(root / "data/processed/swisstopo/placeholder_second_site_v1/context/swisstlm3d/metadata.json"),
            report["deferred_public_context_paths_or_patterns"],
        )
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 5)
        self.assertIn("public-context products are intentionally deferred", report["blocked_reason"])
        product_requirements = {entry["category"]: entry for entry in report["public_context_product_requirements"]}
        self.assertEqual(product_requirements["swisstlm3d_metadata"]["current_status"], "deferred_public_context")

    def test_missing_site_extent_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit_site_extent=True)

        self.assertEqual(report["portability_preflight_status"], "blocked_missing_inputs")
        self.assertIn("site_extent_definition", report["missing_input_categories"])

    def test_text_report_mentions_commands_and_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, site_config=self._fixture_config_path(), omit=["swisstlm3d_metadata"])

        text = preflight.render_text_report(report)
        self.assertIn("portability_preflight_status: deferred_public_context_inputs", text)
        self.assertIn("public_context_boundary_status: deferred_public_context_inputs", text)
        self.assertIn("public_context_acquisition_summary:", text)
        self.assertIn("public_context_acquisition_plan:", text)
        self.assertIn("validate_public_real_site_conditional_pilot_run.py", text)
        self.assertIn("acquisition_manifest_status:", text)
        self.assertIn("public_context_product_requirements:", text)
        self.assertIn("deferred_public_context_categories:", text)
        self.assertIn("blocked_second_site_commands:", text)
        self.assertIn("second_site_manifest_status: staged_placeholder_manifest", text)
        self.assertIn("public-context products are intentionally deferred", text)

    def test_minimal_staging_helper_reduces_core_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging.stage_minimal_inputs(
                repo_root=root,
                site_config=self._candidate_example_config_path(),
                fixture_root=ROOT
                / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            original_root = preflight.ROOT
            try:
                preflight.ROOT = root
                report = preflight.build_report(self._candidate_example_config_path())
            finally:
                preflight.ROOT = original_root

        self.assertEqual(report["portability_preflight_status"], "deferred_public_context_inputs")
        self.assertEqual(report["public_context_boundary_status"], "deferred_public_context_inputs")
        self.assertEqual(report["terrain_manifest_status"], "ready")
        self.assertEqual(report["source_zone_manifest_status"], "ready")
        self.assertEqual(report["scenario_manifest_status"], "ready")
        self.assertEqual(report["missing_input_categories"], [])
        self.assertEqual(
            set(report["deferred_public_context_categories"]),
            {
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            },
        )
        self.assertNotIn("terrain_crop", report["deferred_public_context_categories"])
        self.assertNotIn("source_zone_metadata", report["deferred_public_context_categories"])
        self.assertNotIn("scenario_table", report["deferred_public_context_categories"])
        self.assertNotIn("source_scenario_policy", report["deferred_public_context_categories"])
        self.assertNotIn("validation_case_root", report["deferred_public_context_categories"])
        self.assertNotIn("hazard_results_root", report["deferred_public_context_categories"])
        self.assertNotIn("processed_input_root", report["deferred_public_context_categories"])
        self.assertNotIn("processed_context_root", report["deferred_public_context_categories"])
        self.assertTrue(report["synthetic_fixture_boundaries"][0]["allowed"])

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
            config_source = site_config or self._fixture_config_path()
            config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
            acquisition_manifest_name = Path(
                config_data.get("acquisition_manifest_path", "chant_sura_fluelapass_public_geodata_acquisition.yaml")
            ).name
            config_data["acquisition_manifest_path"] = str(
                (config_source.parent / acquisition_manifest_name).resolve()
            )
            config_path = root / "site_config.yaml"
            config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
            self._build_inputs(root, config_path=config_path, omit=omit)
            if omit_site_extent:
                config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                config.pop("site_extent", None)
                config_path = root / "site_config.yaml"
                config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            preflight.ROOT = root
            return preflight.build_report(config_path)
        finally:
            preflight.ROOT = original_root

    def _build_inputs(self, root: Path, *, config_path: Path, omit: list[str] | None = None) -> None:
        omit = omit or []
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
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
