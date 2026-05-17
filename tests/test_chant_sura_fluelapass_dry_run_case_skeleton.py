from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_chant_sura_fluelapass_dry_run_case_skeleton.py"
SPEC = importlib.util.spec_from_file_location("generate_chant_sura_fluelapass_dry_run_case_skeleton", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ChantSuraFluelapassDryRunCaseSkeletonTests(unittest.TestCase):
    def test_dry_run_skeleton_writes_expected_references_and_placeholders(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temp_root, tempfile.TemporaryDirectory(dir="/tmp") as output_root:
            repo_root = Path(temp_root)
            site_config = self._write_site_config(repo_root)
            self._stage_core_inputs(repo_root, site_config)

            original_root = MODULE.PREFLIGHT.ROOT
            try:
                MODULE.PREFLIGHT.ROOT = repo_root
                report = MODULE.build_report(site_config, Path(output_root))
            finally:
                MODULE.PREFLIGHT.ROOT = original_root

            case_path = Path(report["generated_case_path"])
            case = yaml.safe_load(case_path.read_text(encoding="utf-8"))

            self.assertEqual(report["case_skeleton_status"], "ready")
            self.assertEqual(report["reference_validation_status"], "ready")
            self.assertEqual(report["preflight_status"], "deferred_public_context_inputs")
            self.assertEqual(report["ensemble_execution_status"], "blocked_template_only")
            self.assertFalse(report["scale_up_authorized"])
            self.assertFalse(report["operational_claims_allowed"])
            self.assertEqual(report["write_status"], "written")
            self.assertIn("deferred_public_context_inputs", report["blocked_reason"])
            self.assertTrue(case_path.exists())
            self.assertEqual(case["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(case["mode"], "dry_run")
            self.assertEqual(case["generation_boundary"]["preflight_status"], "deferred_public_context_inputs")
            self.assertEqual(case["generation_boundary"]["ensemble_execution_status"], "blocked_template_only")
            self.assertEqual(case["generation_boundary"]["blocked_reason"], "deferred_public_context_inputs")
            self.assertEqual(case["references"]["terrain"]["terrain_crop"], str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"))
            self.assertEqual(case["references"]["terrain"]["terrain_metadata"], str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"))
            self.assertEqual(case["references"]["source_zone"]["source_zone_metadata"], str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"))
            self.assertEqual(case["references"]["scenario"]["scenario_table"], str(repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv"))
            self.assertEqual(case["references"]["policy"]["source_scenario_policy"], str(repo_root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml"))
            self.assertEqual(
                set(case["deferred_public_context_placeholders"]),
                {
                    "swissimage_context",
                    "swisstlm3d_context",
                    "swisstlm3d_metadata",
                    "swisssurface3d_context",
                    "swisssurface3d_raster_context",
                    "swissbuildings3d_context",
                },
            )
            for placeholder in case["deferred_public_context_placeholders"].values():
                self.assertEqual(placeholder["status"], "deferred_public_context_inputs")
            self.assertIn("no ensemble execution", " ".join(case["notes"]))
            self.assertFalse(case["claim_boundaries"]["operational_claims_allowed"])

    def test_main_returns_blocked_report_when_core_inputs_are_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temp_root, tempfile.TemporaryDirectory(dir="/tmp") as output_root:
            repo_root = Path(temp_root)
            site_config = self._write_site_config(repo_root)

            original_root = MODULE.PREFLIGHT.ROOT
            try:
                MODULE.PREFLIGHT.ROOT = repo_root
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = MODULE.main(
                        [
                            "--site-config",
                            str(site_config),
                            "--output-root",
                            str(Path(output_root)),
                            "--format",
                            "json",
                        ]
                    )
            finally:
                MODULE.PREFLIGHT.ROOT = original_root

            report = json.loads(buffer.getvalue())
            self.assertEqual(exit_code, 2)
            self.assertEqual(report["case_skeleton_status"], "blocked_missing_inputs")
            self.assertEqual(report["reference_validation_status"], "blocked_missing_inputs")
            self.assertEqual(report["ensemble_execution_status"], "blocked_template_only")
            self.assertIn("blocked_missing_inputs", report["blocked_reason"])
            self.assertEqual(report["write_status"], "blocked")

    def test_output_root_outside_tmp_or_ignored_paths_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = Path(temp_root)
            site_config = self._write_site_config(repo_root)
            self._stage_core_inputs(repo_root, site_config)
            forbidden_output_root = repo_root / "not_allowed"

            original_root = MODULE.PREFLIGHT.ROOT
            try:
                MODULE.PREFLIGHT.ROOT = repo_root
                with self.assertRaises(MODULE.CaseSkeletonError):
                    MODULE.build_report(site_config, forbidden_output_root)
            finally:
                MODULE.PREFLIGHT.ROOT = original_root

    def _write_site_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _stage_core_inputs(self, repo_root: Path, site_config: Path) -> None:
        config = yaml.safe_load(site_config.read_text(encoding="utf-8"))
        site_id = config["candidate_site_id"]
        original_root = MODULE.PREFLIGHT.ROOT
        try:
            MODULE.PREFLIGHT.ROOT = repo_root
            paths = MODULE.PREFLIGHT.build_paths(site_id, config)
        finally:
            MODULE.PREFLIGHT.ROOT = original_root

        for path in [
            paths["processed_input_root"],
            paths["processed_context_root"],
            paths["validation_case_root"],
            paths["hazard_results_root"],
            paths["source_scenario_policy"].parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        files = {
            paths["terrain_crop"]: "terrain\n",
            paths["terrain_metadata"]: "crs: EPSG:2056\nvertical_datum: LN02\n",
            paths["source_zone_metadata"]: "source_zone_id: chant_sura_example\n",
            paths["scenario_table"]: "scenario_id,probability\nA,1.0\n",
            paths["source_scenario_policy"]: "policy_id: chant_sura_example\n",
            paths["aoi_tile_catalog"]: (
                "catalog_status: ready\n"
                "swissalti3d:\n"
                "  tiles:\n"
                "    - tile_id: \"2793-1180\"\n"
                "      product_id: swissALTI3D\n"
                "      source_product: swissALTI3D\n"
                "      expected_staging_root: data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissalti3d\n"
                "      expected_staged_path: data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissalti3d/2793-1180.asc\n"
            ),
        }
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
