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
            report = self._build_report(root)

        self.assertEqual(report["portability_preflight_status"], "ready")
        self.assertEqual(report["readiness_status"], "ready")
        self.assertEqual(report["candidate_site_id"], "fixture_second_site")
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
                "expected_artifact_roots",
                "missing_input_categories",
                "missing_input_paths_or_patterns",
                "operational_claims_allowed",
                "portability_preflight_status",
                "readiness_status",
                "required_case_generation_inputs",
                "required_metadata_records",
                "required_public_geodata_products",
                "reusable_workflow_components",
                "scale_up_authorized",
                "site_specific_required_inputs",
            },
        )

    def test_missing_context_metadata_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_report(root, omit=["swisstlm3d_metadata"])

        self.assertEqual(report["portability_preflight_status"], "blocked_missing_inputs")
        self.assertIn("swisstlm3d_context", report["missing_input_categories"])
        self.assertIn(
            str(root / "data/processed/swisstopo/fixture_second_site/context/swisstlm3d/metadata.json"),
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
            report = self._build_report(root, omit=["swisstlm3d_metadata"])

        text = preflight.render_text_report(report)
        self.assertIn("portability_preflight_status: blocked_missing_inputs", text)
        self.assertIn("validate_public_real_site_conditional_pilot_run.py", text)
        self.assertIn("missing_input_categories:", text)

    def _fixture_config_path(self) -> Path:
        return ROOT / "tests/fixtures/second_site_public_geodata_preflight/site_template.yaml"

    def _build_report(
        self,
        root: Path,
        *,
        site_config: Path | None = None,
        omit_site_extent: bool = False,
        omit: list[str] | None = None,
    ) -> dict[str, object]:
        self._build_inputs(root, omit=omit)
        if omit_site_extent:
            config = yaml.safe_load(self._fixture_config_path().read_text(encoding="utf-8"))
            config.pop("site_extent", None)
            site_config = root / "site_config.yaml"
            site_config.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        config_path = site_config or self._fixture_config_path()
        original_root = preflight.ROOT
        try:
            preflight.ROOT = root
            return preflight.build_report(config_path)
        finally:
            preflight.ROOT = original_root

    def _build_inputs(self, root: Path, omit: list[str] | None = None) -> None:
        omit = omit or []
        site_id = "fixture_second_site"
        input_root = root / f"data/processed/swisstopo/{site_id}/input"
        context_root = root / f"data/processed/swisstopo/{site_id}/context"
        validation_root = root / f"validation/private/{site_id}"
        hazard_root = root / f"hazard/results/{site_id}"
        policy_root = root / "validation/policies"

        for path in [
            input_root,
            context_root / "swissimage",
            context_root / "swisstlm3d",
            context_root / "swisssurface3d",
            context_root / "swisssurface3d_raster",
            context_root / "swissbuildings3d",
            context_root / "barriers",
            validation_root,
            hazard_root,
            policy_root,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        files = {
            "terrain_crop": (input_root / "terrain.asc", "terrain\n"),
            "terrain_metadata": (input_root / "terrain_metadata.yaml", "crs: EPSG:2056\nvertical_datum: LN02\n"),
            "source_zone_metadata": (input_root / "source_zone_metadata.yaml", "source_zone_id: fixture_zone\n"),
            "scenario_table": (input_root / "scenario_table.csv", "scenario_id,probability\nA,1.0\n"),
            "source_scenario_policy": (policy_root / f"{site_id}_source_scenario_policy_v1.yaml", "policy_id: fixture_policy\n"),
            "swisstlm3d_metadata": (
                context_root / "swisstlm3d" / "metadata.json",
                json.dumps({"source_product": "swissTLM3D", "staged_asset_present": True}),
            ),
            "swissimage_context": (context_root / "swissimage" / "tile.txt", "image\n"),
            "swisssurface3d_context": (context_root / "swisssurface3d" / "tile.txt", "surface\n"),
            "swisssurface3d_raster_context": (context_root / "swisssurface3d_raster" / "tile.txt", "raster\n"),
            "swissbuildings3d_context": (context_root / "swissbuildings3d" / "tile.txt", "buildings\n"),
        }
        for key, (path, content) in files.items():
            if key in omit:
                continue
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
