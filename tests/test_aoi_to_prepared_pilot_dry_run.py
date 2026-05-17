from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_aoi_to_prepared_pilot_dry_run.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = _load_module(SCRIPT_PATH, "plan_aoi_to_prepared_pilot_dry_run")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_aoi_to_prepared_pilot_test",
)


class AoiToPreparedPilotDryRunTests(unittest.TestCase):
    def test_staged_aoi_with_release_polygon_emits_preparation_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            release_polygon_path = self._write_release_polygon(repo_root)
            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"

            first = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )
            second = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )

            skeleton = first["case_skeleton_output"]
            case = yaml.safe_load(Path(skeleton["case_skeleton_path"]).read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "aoi_to_prepared_pilot_dry_run_v1")
        self.assertEqual(first["workflow_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_input"]["input_mode"], "aoi_extent_with_release_polygon")
        self.assertEqual(first["preparation_input"]["release_polygon"]["geometry_type"], "Polygon")
        self.assertEqual(first["preparation_input"]["release_polygon"]["vertex_count"], 4)
        self.assertEqual(first["preparation_input"]["release_polygon"]["extent_lv95_m"]["xmin"], 2793020.0)
        self.assertEqual(first["preparation_input"]["release_polygon"]["extent_lv95_m"]["ymax"], 1180780.0)
        self.assertTrue(first["preparation_input"]["site_config_path"].endswith("site_config.yaml"))
        self.assertEqual(first["preparation_input"]["aoi_tile_discovery"]["discovery_status"], "ready")
        self.assertEqual(first["preparation_input"]["aoi_tile_discovery"]["tile_candidate_count"], 1)
        self.assertEqual(first["candidate_source_zones"]["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertTrue(first["candidate_source_zones"]["blocked_missing_inputs"])
        self.assertEqual(first["candidate_source_zones"]["candidate_release_zone_set_status"], "not_emitted")
        self.assertEqual(first["candidate_source_zones"]["candidate_release_zone_interpretation"], "not_claimed")
        self.assertIn("terrain_inputs", first["candidate_source_zones"])
        self.assertIn("source_zone_inputs", first["candidate_source_zones"])
        self.assertEqual(first["scenario_generation_inputs"]["scenario_plan_status"], "ready")
        self.assertEqual(first["scenario_generation_inputs"]["scenario_plan_summary"]["block_size_bin_count"], 3)
        self.assertEqual(first["scenario_generation_inputs"]["blocked_execution_status"], "deferred_public_context_inputs")
        self.assertTrue(first["scenario_generation_inputs"]["conditional_only_weighting"])
        self.assertEqual(
            first["scenario_generation_inputs"]["source_policy_provenance"]["policy_id"],
            "tschamut_public_source_scenario_policy_v1",
        )
        self.assertEqual(first["output_root_planning"]["prepared_validation_root"], "validation/private/chant_sura_fluelapass_portability_example_v1")
        self.assertIn(
            "second_site_release_plan_execution_template",
            first["output_root_planning"]["blocked_command_ids"],
        )

        terrain_categories = [row["category"] for row in first["terrain_manifests"]]
        self.assertEqual(terrain_categories, ["terrain_crop", "terrain_metadata"])
        self.assertTrue(
            first["terrain_manifests"][0]["expected_staged_path"].endswith(
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"
            )
        )

        context_categories = [row["category"] for row in first["context_manifests"]]
        self.assertIn("swissimage_context", context_categories)
        self.assertIn("swisstlm3d_context", context_categories)
        self.assertTrue(
            first["release_scenario_placeholders"]["source_scenario_policy_path"].endswith(
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
            )
        )
        self.assertTrue(
            first["release_scenario_placeholders"]["scenario_table_path"].endswith(
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
            )
        )
        self.assertTrue(
            first["release_scenario_placeholders"]["scenario_table_manifest_path"].endswith("scenario_table_manifest.json")
        )
        self.assertIn(
            "generate_tschamut_block_scenario_tables.py",
            first["release_scenario_placeholders"]["scenario_generation_command"],
        )
        self.assertTrue(
            first["release_scenario_placeholders"]["same_scale_reference_path"].endswith(
                "docs/tschamut_public_same_scale_uncertainty_envelope.md"
            )
        )
        hook_ids = [row["command_id"] for row in first["command_plan_hooks"]]
        self.assertIn("second_site_aoi_acquisition_dry_run_planner", hook_ids)
        self.assertIn("second_site_release_plan_dry_run", hook_ids)
        self.assertIn("second_site_benchmark_preparation_template", hook_ids)
        self.assertEqual(first["preparation_input"]["gis_scope_summary"], skeleton["case_skeleton"]["gis_scope_summary"])
        self.assertEqual(case["gis_scope_summary"], skeleton["case_skeleton"]["gis_scope_summary"])
        self.assertEqual(first["preparation_input"]["gis_scope_summary"]["schema_version"], "aoi_to_prepared_pilot_gis_scope_summary_v1")
        self.assertEqual(first["preparation_input"]["gis_scope_summary"]["status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_input"]["gis_scope_summary"]["cog_export_expectation"]["status"], "template_only")
        self.assertTrue(first["preparation_input"]["gis_scope_summary"]["no_hazard_layers_generated"])
        self.assertIn("planned_raster_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("planned_vector_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("template_only_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("blocked_missing_inputs", first["preparation_input"]["gis_scope_summary"])
        self.assertTrue(any(entry["product_kind"] == "raster" for entry in first["preparation_input"]["gis_scope_summary"]["planned_products"]))
        self.assertTrue(any(entry["product_kind"] == "vector" for entry in first["preparation_input"]["gis_scope_summary"]["planned_products"]))
        self.assertTrue(
            any(path.endswith("validation/private/chant_sura_fluelapass_portability_example_v1") for path in first["ignored_output_roots"])
        )
        self.assertTrue(
            any(path.endswith("hazard/results/chant_sura_fluelapass_portability_example_v1") for path in first["ignored_output_roots"])
        )

        text_report = planner.render_text_report(first)
        self.assertIn("preparation_input:", text_report)
        self.assertIn("aoi_tile_discovery:", text_report)
        self.assertIn("candidate_source_zones:", text_report)
        self.assertIn("scenario_generation_inputs:", text_report)
        self.assertIn("output_root_planning:", text_report)
        self.assertIn("terrain_manifests:", text_report)
        self.assertIn("context_manifests:", text_report)
        self.assertIn("command_plan_hooks:", text_report)
        self.assertIn("ignored_output_roots:", text_report)
        self.assertIn("generic_candidate_source_zone_provenance", text_report)
        self.assertIn("scenario_generation_handoff", text_report)

    def test_output_root_mode_writes_deterministic_case_skeleton_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            release_polygon_path = self._write_release_polygon(repo_root)
            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"

            first = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )
            second = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )

            skeleton = first["case_skeleton_output"]
            case = yaml.safe_load(Path(skeleton["case_skeleton_path"]).read_text(encoding="utf-8"))
            command_manifest = json.loads(Path(skeleton["command_manifest_path"]).read_text(encoding="utf-8"))
            expected_output_roots = yaml.safe_load(Path(skeleton["expected_output_roots_path"]).read_text(encoding="utf-8"))
            blocked_execution = json.loads(Path(skeleton["blocked_execution_path"]).read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(first["workflow_status"], "blocked_missing_inputs")
        self.assertEqual(skeleton["status"], "blocked_missing_inputs")
        self.assertEqual(skeleton["write_status"], "written")
        self.assertEqual(skeleton["blocked_execution_status"], "blocked_missing_inputs")
        self.assertIn("second_site_aoi_acquisition_dry_run_planner", skeleton["runnable_command_ids"])
        self.assertIn("second_site_release_plan_execution_template", skeleton["template_only_command_ids"])
        self.assertEqual(case["schema_version"], "aoi_to_prepared_pilot_case_skeleton_v1")
        self.assertEqual(case["write_status"], "written")
        self.assertEqual(case["blocked_execution_status"], "blocked_missing_inputs")
        self.assertEqual(command_manifest["schema_version"], "aoi_to_prepared_pilot_command_manifest_v1")
        self.assertEqual(command_manifest["blocked_execution_status"], "blocked_missing_inputs")
        self.assertEqual(expected_output_roots["schema_version"], "aoi_to_prepared_pilot_expected_output_roots_v1")
        self.assertEqual(blocked_execution["schema_version"], "aoi_to_prepared_pilot_blocked_execution_v1")
        self.assertEqual(blocked_execution["blocked_execution_status"], "blocked_missing_inputs")
        self.assertEqual(blocked_execution["case_skeleton_status"], "blocked_missing_inputs")
        self.assertEqual(case["expected_output_roots"], skeleton["expected_output_roots"])
        self.assertEqual(len(case["command_sequence"]), 4)
        self.assertEqual(case["command_sequence"][0]["step_id"], "aoi_acquisition")
        self.assertEqual(expected_output_roots["expected_output_roots"], skeleton["expected_output_roots"])
        self.assertEqual(case["scenario_generation_handoff"]["blocked_execution_status"], "deferred_public_context_inputs")
        self.assertTrue(case["scenario_generation_handoff"]["scenario_table_manifest_path"].endswith("scenario_table_manifest.json"))
        self.assertIn("generate_tschamut_block_scenario_tables.py", case["scenario_generation_handoff"]["command"])
        self.assertTrue(case["scenario_generation_handoff"]["conditional_only_weighting"])

    def test_missing_inputs_remain_blocked_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            missing_config = repo_root / "missing_site_config.yaml"
            output_root = Path(output_tmp) / "validation/private/unspecified_second_site/aoi_to_prepared_pilot_dry_run"
            first = planner.build_report(
                missing_config,
                repo_root=repo_root,
                skeleton_output_root=output_root,
            )
            second = planner.build_report(
                missing_config,
                repo_root=repo_root,
                skeleton_output_root=output_root,
            )

            skeleton = first["case_skeleton_output"]
            case = yaml.safe_load(Path(skeleton["case_skeleton_path"]).read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(first["workflow_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_status"], "blocked_missing_inputs")
        self.assertEqual(first["preparation_input"]["input_mode"], "missing_inputs")
        self.assertEqual(first["preparation_input"]["candidate_site_id"], "unspecified_second_site")
        self.assertEqual(first["candidate_source_zones"]["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertEqual(first["scenario_generation_inputs"]["scenario_plan_status"], "ready")
        self.assertTrue(first["terrain_manifests"])
        self.assertTrue(first["context_manifests"])
        self.assertEqual(first["preparation_input"]["gis_scope_summary"], skeleton["case_skeleton"]["gis_scope_summary"])
        self.assertTrue(
            first["terrain_manifests"][0]["expected_staged_path"].endswith(
                "data/processed/swisstopo/unspecified_second_site/input/terrain.asc"
            )
        )
        self.assertTrue(
            any(path.endswith("validation/private/unspecified_second_site") for path in first["ignored_output_roots"])
        )
        self.assertTrue(
            any(path.endswith("hazard/results/unspecified_second_site") for path in first["ignored_output_roots"])
        )
        self.assertEqual(skeleton["status"], "blocked_missing_inputs")
        self.assertEqual(skeleton["blocked_execution_status"], "blocked_missing_inputs")
        self.assertEqual(skeleton["write_status"], "written")
        self.assertEqual(case["case_skeleton_status"], "blocked_missing_inputs")
        self.assertEqual(case["blocked_execution_status"], "blocked_missing_inputs")
        self.assertEqual(case["write_status"], "written")
        self.assertEqual(case["gis_scope_summary"]["schema_version"], "aoi_to_prepared_pilot_gis_scope_summary_v1")
        self.assertEqual(case["gis_scope_summary"]["status"], "blocked_missing_inputs")
        self.assertEqual(case["gis_scope_summary"]["cog_export_expectation"]["status"], "template_only")
        self.assertIn("blocked_missing_inputs", case["gis_scope_summary"])
        self.assertTrue(case["gis_scope_summary"]["no_hazard_layers_generated"])
        self.assertEqual(case["gis_scope_summary"], first["preparation_input"]["gis_scope_summary"])

        text_report = planner.render_text_report(first)
        self.assertIn("schema_version: aoi_to_prepared_pilot_dry_run_v1", text_report)
        self.assertIn("workflow_status: blocked_missing_inputs", text_report)
        self.assertIn("preparation_input:", text_report)
        self.assertIn("candidate_source_zones:", text_report)
        self.assertIn("scenario_generation_inputs:", text_report)
        self.assertIn("gis_scope_summary:", text_report)

    def test_synthetic_non_tschamut_candidate_exposes_generic_scenario_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(
                repo_root,
                candidate_site_id="synthetic_candidate_alpha",
                candidate_site_name="Synthetic Candidate Alpha",
            )
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._rewrite_synthetic_staged_inputs(repo_root, "synthetic_candidate_alpha", "synthetic_candidate_zone_alpha")
            release_polygon_path = self._write_release_polygon(repo_root)
            output_root = Path(output_tmp) / "validation/private/synthetic_candidate_alpha/aoi_to_prepared_pilot_dry_run"

            first = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )
            second = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )

        self.assertEqual(first, second)
        scenario_inputs = first["scenario_generation_inputs"]
        self.assertEqual(
            scenario_inputs["generic_candidate_source_zone_provenance"]["candidate_source_zone_id"],
            "synthetic_candidate_zone_alpha",
        )
        self.assertEqual(
            scenario_inputs["generic_candidate_source_zone_provenance"]["source_zone_id_source"],
            "candidate_source_zone_metadata",
        )
        self.assertEqual(scenario_inputs["blocked_execution_status"], "deferred_public_context_inputs")
        self.assertTrue(
            scenario_inputs["generic_scenario_generation"]["command"].startswith(
                "PYENV_VERSION=system uv run python scripts/generate_tschamut_block_scenario_tables.py"
            )
        )
        self.assertIn("--template policy_block_family_v1", scenario_inputs["generic_scenario_generation"]["command"])
        self.assertTrue(scenario_inputs["scenario_table_manifest_path"].endswith("scenario_table_manifest.json"))

        handoff = first["case_skeleton_output"]["case_skeleton"]["scenario_generation_handoff"]
        self.assertEqual(handoff["blocked_execution_status"], "deferred_public_context_inputs")
        self.assertEqual(
            handoff["generic_candidate_source_zone_provenance"]["candidate_source_zone_id"],
            "synthetic_candidate_zone_alpha",
        )
        self.assertTrue(handoff["scenario_table_manifest_path"].endswith("scenario_table_manifest.json"))

    def _write_candidate_config(
        self,
        repo_root: Path,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
        candidate_site_name: str = "Chant Sura / Flüelapass portability example",
    ) -> Path:
        return self._write_candidate_config_with_identity(repo_root, candidate_site_id, candidate_site_name)

    def _write_candidate_config_with_identity(
        self,
        repo_root: Path,
        candidate_site_id: str,
        candidate_site_name: str,
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

    def _rewrite_synthetic_staged_inputs(self, repo_root: Path, candidate_site_id: str, source_zone_id: str) -> None:
        source_zone_path = repo_root / "data/processed/swisstopo" / candidate_site_id / "input" / "source_zone_metadata.yaml"
        source_zone = yaml.safe_load(source_zone_path.read_text(encoding="utf-8"))
        source_zone["zone_id"] = source_zone_id
        source_zone["source_zone_id"] = source_zone_id
        source_zone["title"] = "Synthetic Candidate Alpha"
        if isinstance(source_zone.get("release_sampling_policy"), dict):
            source_zone["release_sampling_policy"]["release_cell_id_prefix"] = "synthetic_candidate_cell"
        source_zone_path.write_text(yaml.safe_dump(source_zone, sort_keys=False), encoding="utf-8")

        scenario_table_path = repo_root / "data/processed/swisstopo" / candidate_site_id / "input" / "scenario_table.csv"
        with scenario_table_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
            fieldnames = list(rows[0].keys()) if rows else []
        for row in rows:
            row["source_zone_id"] = source_zone_id
            if row.get("scenario_id"):
                row["scenario_id"] = f"{source_zone_id}__synthetic_candidate_block_001"
            if row.get("block_scenario_id"):
                row["block_scenario_id"] = "synthetic_candidate_block_001"
        with scenario_table_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def _rewrite_strings(self, payload: object, source: str, target: str) -> object:
        if isinstance(payload, str):
            return payload.replace(source, target)
        if isinstance(payload, list):
            return [self._rewrite_strings(item, source, target) for item in payload]
        if isinstance(payload, dict):
            return {key: self._rewrite_strings(value, source, target) for key, value in payload.items()}
        return payload

    def _write_release_polygon(self, repo_root: Path) -> Path:
        polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [2793020.0, 1180220.0],
                    [2793180.0, 1180220.0],
                    [2793180.0, 1180780.0],
                    [2793020.0, 1180780.0],
                    [2793020.0, 1180220.0],
                ]
            ],
        }
        polygon_path = repo_root / "release_polygon.yaml"
        polygon_path.write_text(yaml.safe_dump({"geometry": polygon}, sort_keys=False), encoding="utf-8")
        return polygon_path


if __name__ == "__main__":
    unittest.main()
