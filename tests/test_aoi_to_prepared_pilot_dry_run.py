from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
import shutil
import unittest
from pathlib import Path

import yaml
import scripts.build_hazard_layers as hazard
from scripts.audit_gis_cog_package_readiness import build_gis_cog_readiness_report


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
            self._write_verified_cache_manifest(repo_root, "chant_sura_fluelapass_portability_example_v1")
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
        self.assertEqual(first["cache_verification"]["verification_status"], "verified")
        self.assertEqual(first["preparation_input"]["cache_verification"]["cache_verification_status"], "ready")
        self.assertEqual(first["preparation_input"]["cache_verification"]["blocked_missing_inputs"], [])
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
        self.assertEqual(first["preparation_input"]["gis_scope_summary"]["cache_verification"]["verification_status"], "verified")
        self.assertIn("planned_raster_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("planned_vector_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("template_only_products", first["preparation_input"]["gis_scope_summary"])
        self.assertIn("blocked_missing_inputs", first["preparation_input"]["gis_scope_summary"])
        self.assertTrue(any(entry["product_kind"] == "raster" for entry in first["preparation_input"]["gis_scope_summary"]["planned_products"]))
        self.assertTrue(any(entry["product_kind"] == "vector" for entry in first["preparation_input"]["gis_scope_summary"]["planned_products"]))
        self.assertIn("public_geodata_cache_verification", [step["step_id"] for step in first["workflow_steps"]])
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
        self.assertIn("cache_verification:", text_report)
        self.assertIn("scenario_generation_inputs:", text_report)
        self.assertIn("output_root_planning:", text_report)
        self.assertIn("terrain_manifests:", text_report)
        self.assertIn("context_manifests:", text_report)
        self.assertIn("command_plan_hooks:", text_report)
        self.assertIn("ignored_output_roots:", text_report)
        self.assertIn("ignored_root_layout:", text_report)
        self.assertIn("generic_candidate_source_zone_provenance", text_report)
        self.assertIn("scenario_generation_handoff", text_report)

    def test_ready_compiler_fixture_emits_manifest_plan_and_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_compiler_inputs(repo_root, config_path)
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

            compiler = first["prepared_pilot_compiler"]
            run_manifest = yaml.safe_load(Path(compiler["run_manifest_path"]).read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(compiler["schema_version"], "aoi_to_prepared_pilot_compiler_v1")
        self.assertEqual(compiler["classification"], "ready_for_balfrin_postproc")
        self.assertEqual(compiler["first_blocker"]["step_id"], "prepared_pilot_command_plan")
        self.assertEqual(compiler["execution_hints"]["local"]["status"], "ready_for_local_smoke")
        self.assertEqual(compiler["execution_hints"]["balfrin"]["status"], "ready_for_balfrin_postproc")
        self.assertIn("second_site_release_plan_execution_template", compiler["run_manifest"]["command_plan"]["blocked_template_commands"])
        self.assertEqual(compiler["command_plan"]["command_plan_status"], "ready")
        self.assertEqual(compiler["output_profile"]["command_profile_policy"]["classification"], "scalable_default")
        self.assertEqual(compiler["output_profile"]["command_profile_validation"]["status"], "ready")
        self.assertEqual(compiler["command_plan"]["output_profile_validation"]["status"], "ready")
        self.assertEqual(run_manifest["classification"], "ready_for_balfrin_postproc")
        self.assertEqual(run_manifest["first_blocker"]["step_id"], "prepared_pilot_command_plan")
        self.assertEqual(run_manifest["expected_io_inventory"]["schema_version"], "aoi_to_prepared_pilot_expected_io_inventory_v1")
        self.assertTrue(run_manifest["expected_io_inventory"]["prepared_validation_root"].endswith("validation/private/chant_sura_fluelapass_portability_example_v1"))
        self.assertTrue(run_manifest["expected_io_inventory"]["command_plan_expected_inputs"])
        self.assertTrue(run_manifest["expected_io_inventory"]["command_plan_expected_outputs"])
        self.assertTrue(run_manifest["execution_hints"]["balfrin"]["output_root"].endswith("hazard/results/chant_sura_fluelapass_portability_example_v1"))
        self.assertTrue(run_manifest["execution_hints"]["local"]["output_root"].endswith("aoi_to_prepared_pilot_dry_run"))
        self.assertIn("aoi_to_prepared_pilot_run_manifest.yaml", compiler["run_manifest_path"])
        self.assertIn("aoi_to_prepared_pilot_run_manifest.yaml", first["case_skeleton_output"]["run_manifest_path"])

    def test_aoi_to_map_regression_fixture_produces_smoke_map_package_and_qa_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_compiler_inputs(repo_root, config_path)
            release_polygon_path = self._write_release_polygon(repo_root)
            dry_run_root = (
                Path(output_tmp)
                / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"
            )

            first = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=dry_run_root,
            )
            second = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=dry_run_root,
            )
            smoke = self._build_aoi_to_map_smoke_fixture(repo_root, output_tmp)

        self.assertEqual(first, second)
        self.assertEqual(first["workflow_status"], "deferred_public_context_inputs")
        self.assertEqual(first["prepared_pilot_compiler"]["classification"], "ready_for_balfrin_postproc")
        self.assertEqual(first["prepared_pilot_compiler"]["first_blocker"]["step_id"], "prepared_pilot_command_plan")
        self.assertEqual(
            first["prepared_pilot_compiler"]["first_blocker"]["first_missing_input"],
            "second_site_benchmark_preparation_template",
        )
        self.assertTrue(first["case_skeleton_output"]["output_root"].startswith("/tmp/"))
        self.assertIn(
            "validation/private/chant_sura_fluelapass_portability_example_v1",
            first["case_skeleton_output"]["case_skeleton"]["expected_output_roots"],
        )
        self.assertFalse(first["scenario_generation_inputs"]["claim_boundary"]["annual_frequency_supported"])
        self.assertFalse(first["scenario_generation_inputs"]["claim_boundary"]["physical_probability_supported"])
        self.assertFalse(first["scenario_generation_inputs"]["claim_boundary"]["return_period_supported"])
        self.assertFalse(first["scenario_generation_inputs"]["claim_boundary"]["risk_or_exposure_supported"])
        self.assertFalse(first["scenario_generation_inputs"]["claim_boundary"]["operational_hazard_map_supported"])
        self.assertFalse(first["preparation_input"]["gis_scope_summary"]["non_operational_gis_boundaries"]["distributed_execution_authorized"])
        self.assertFalse(first["preparation_input"]["gis_scope_summary"]["non_operational_gis_boundaries"]["annual_frequency_claims_allowed"])
        self.assertFalse(first["preparation_input"]["gis_scope_summary"]["non_operational_gis_boundaries"]["physical_probability_claims_allowed"])
        self.assertTrue(any(step["step_id"] == "prepared_pilot_command_plan" for step in first["workflow_steps"]))
        self.assertTrue(first["workflow_generated_output_roots"])

        hazard_manifest = smoke["hazard_manifest"]
        map_manifest = smoke["map_manifest"]
        pilot_manifest = smoke["pilot_manifest"]
        audit_report = smoke["audit_report"]

        self.assertEqual(hazard_manifest["schema_version"], "run_manifest_v1")
        self.assertTrue(any(output["kind"] == "hazard_layer" for output in hazard_manifest["outputs"]))
        self.assertTrue(any(output["kind"] == "map_package_manifest" for output in hazard_manifest["outputs"]))
        self.assertTrue(any(output["kind"] == "pilot_gis_package_manifest" for output in hazard_manifest["outputs"]))
        self.assertGreater(len(hazard_manifest["layers"]), 0)
        self.assertEqual(map_manifest["schema_version"], "map_package_manifest_v1")
        self.assertEqual(map_manifest["map_product_id"], "aoi_to_map_smoke_fixture")
        self.assertEqual(map_manifest["map_product_version"], "map_package_v1")
        self.assertEqual(map_manifest["operational_status"], "research_diagnostic")
        self.assertEqual(map_manifest["probability_mode"], "unweighted_diagnostic")
        self.assertEqual(map_manifest["normalization_scope"], "conditioned_on_filter")
        self.assertEqual(map_manifest["source_zone_id"], "tschamut_public_lps_release_bbox")
        self.assertEqual(
            map_manifest["scenario_table_path"],
            str(
                repo_root
                / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
            ),
        )
        self.assertEqual(pilot_manifest["schema_version"], "pilot_gis_package_manifest_v1")
        self.assertEqual(pilot_manifest["package_version"], "pilot_gis_package_v1")
        self.assertEqual(pilot_manifest["operational_status"], "research_diagnostic")
        self.assertFalse(pilot_manifest["probability_claim_boundary"]["annualized"])
        self.assertIn("return_period", pilot_manifest["probability_claim_boundary"]["future_unsupported_product_labels"])
        self.assertEqual(pilot_manifest["visual_qa"]["status"], "inconclusive")
        self.assertFalse(pilot_manifest["visual_qa"]["accepted_for_operational_use"])

        self.assertEqual(audit_report["gis_cog_readiness_status"], "gis_package_ready_cog_blocked")
        audit_artifact_id = next(iter(audit_report["manifest_completeness"]))
        self.assertEqual(audit_report["manifest_completeness"][audit_artifact_id]["map_package_manifest_complete"], True)
        self.assertEqual(audit_report["manifest_completeness"][audit_artifact_id]["pilot_gis_package_manifest_complete"], True)
        self.assertEqual(audit_report["manifest_completeness"][audit_artifact_id]["missing_raster_outputs"], [])
        self.assertEqual(audit_report["blockers"][audit_artifact_id], ["manifest_cloud_optimized_false"])

        summary = self._build_first_failure_summary(first, audit_report)
        self.assertEqual(summary["first_broken_step_id"], "prepared_pilot_command_plan")
        self.assertEqual(summary["first_broken_input"], "second_site_benchmark_preparation_template")
        self.assertIn("gis_package_ready_cog_blocked", summary["summary"])
        self.assertIn("prepared_pilot_command_plan", summary["summary"])

    def test_missing_terrain_blocks_compiler(self) -> None:
        report = self._compiler_report_with_missing_prepared_input("terrain.asc")
        compiler = report["prepared_pilot_compiler"]

        self.assertEqual(compiler["classification"], "blocked_missing_inputs")
        self.assertEqual(compiler["first_blocker"]["status"], "blocked_missing_inputs")
        self.assertTrue(any(item.endswith("terrain.asc") for item in compiler["first_blocker"]["missing_inputs"]))

    def test_missing_reviewed_source_zones_blocks_compiler(self) -> None:
        report = self._compiler_report_with_missing_prepared_input(
            "tschamut_public_source_zone_metadata_v1.yaml",
            under_tschamut=True,
        )
        compiler = report["prepared_pilot_compiler"]

        self.assertEqual(compiler["classification"], "blocked_missing_inputs")
        self.assertEqual(compiler["first_blocker"]["status"], "blocked_missing_inputs")
        self.assertTrue(any(item.endswith("tschamut_public_source_zone_metadata_v1.yaml") for item in compiler["first_blocker"]["missing_inputs"]))

    def test_missing_scenario_plan_blocks_compiler(self) -> None:
        report = self._compiler_report_with_missing_prepared_input("tschamut_public_scenario_table_v1.csv", under_tschamut=True)
        compiler = report["prepared_pilot_compiler"]

        self.assertEqual(compiler["classification"], "blocked_missing_inputs")
        self.assertEqual(compiler["first_blocker"]["status"], "blocked_missing_inputs")
        self.assertTrue(any(item.endswith("tschamut_public_scenario_table_v1.csv") for item in compiler["first_blocker"]["missing_inputs"]))

    def test_compiler_command_plan_shape_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_compiler_inputs(repo_root, config_path)
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

        self.assertEqual(first["prepared_pilot_compiler"]["command_plan"], second["prepared_pilot_compiler"]["command_plan"])
        self.assertEqual(first["prepared_pilot_compiler"]["expected_io_inventory"], second["prepared_pilot_compiler"]["expected_io_inventory"])
        self.assertEqual(first["prepared_pilot_compiler"]["output_profile"], second["prepared_pilot_compiler"]["output_profile"])
        self.assertEqual(first["prepared_pilot_compiler"]["execution_hints"], second["prepared_pilot_compiler"]["execution_hints"])
        self.assertEqual(first["prepared_pilot_compiler"]["run_manifest"], second["prepared_pilot_compiler"]["run_manifest"])
        self.assertEqual(first["prepared_pilot_compiler"]["command_plan"]["command_ids"], second["prepared_pilot_compiler"]["command_plan"]["command_ids"])
        self.assertEqual(first["prepared_pilot_compiler"]["command_plan"]["command_group_keys"], second["prepared_pilot_compiler"]["command_plan"]["command_group_keys"])

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
            self._write_verified_cache_manifest(repo_root, "chant_sura_fluelapass_portability_example_v1")
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
        self.assertIn("public_geodata_cache_verification", [step["step_id"] for step in first["workflow_steps"]])
        self.assertEqual(case["expected_output_roots"], skeleton["expected_output_roots"])
        self.assertEqual(len(case["command_sequence"]), 5)
        self.assertEqual(case["command_sequence"][0]["step_id"], "aoi_acquisition")
        self.assertEqual(case["command_sequence"][1]["step_id"], "public_geodata_cache_verification")
        self.assertEqual(expected_output_roots["expected_output_roots"], skeleton["expected_output_roots"])
        self.assertEqual(case["scenario_generation_handoff"]["blocked_execution_status"], "deferred_public_context_inputs")
        self.assertTrue(case["scenario_generation_handoff"]["scenario_table_manifest_path"].endswith("scenario_table_manifest.json"))
        self.assertIn("generate_tschamut_block_scenario_tables.py", case["scenario_generation_handoff"]["command"])
        self.assertTrue(case["scenario_generation_handoff"]["conditional_only_weighting"])

    def test_forbidden_output_root_blocks_dry_run_bundle_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            release_polygon_path = self._write_release_polygon(repo_root)
            self._write_verified_cache_manifest(repo_root, "chant_sura_fluelapass_portability_example_v1")

            with self.assertRaises(ValueError) as ctx:
                planner.build_report(
                    config_path,
                    repo_root=repo_root,
                    release_polygon_path=release_polygon_path,
                    skeleton_output_root=repo_root / "not_allowed",
                )

        self.assertIn("output root must stay under /tmp or validation/private", str(ctx.exception))

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
        self.assertEqual(first["cache_verification"]["cache_verification_status"], "blocked_missing_inputs")
        self.assertTrue(any("terrain_crop" in item for item in first["cache_verification"]["blocked_missing_inputs"]))
        self.assertTrue(any("public_geodata_cache_manifest.yaml" in item for item in first["blocked_missing_inputs"]))
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
        self.assertIn("cache_verification:", text_report)
        self.assertIn("blocked_missing_inputs:", text_report)
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

    def _stage_ready_compiler_inputs(self, repo_root: Path, config_path: Path) -> None:
        staging.stage_minimal_inputs(
            repo_root=repo_root,
            site_config=config_path,
            fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
        )
        self._copy_repo_file(
            ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
            repo_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
        )
        self._copy_repo_file(
            ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
            repo_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
        )
        self._copy_repo_file(
            ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
            repo_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
        )
        self._copy_repo_file(
            ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
            repo_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
        )
        catalog_path = repo_root / "data/processed/swisstopo/tschamut_public_pilot/input/aoi_tile_catalog.yaml"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": "swisstopo_aoi_tile_catalog_v1",
                    "catalog_status": "metadata_only",
                    "source_product": "swissALTI3D",
                    "product_id": "swissalti3d_2m",
                    "crs": "EPSG:2056",
                    "resolution_m": 2,
                    "expected_staging_root": "data/raw/swisstopo/tschamut_public_pilot",
                    "tile_size_m": 1000,
                    "tiles": [
                        {
                            "tile_id": "2696-1167",
                            "source_product": "swissALTI3D",
                            "source_filename": "swissalti3d_2019_2696-1167_2_2056_5728.tif",
                            "source_url": "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/swissalti3d_2019_2696-1167/swissalti3d_2019_2696-1167_2_2056_5728.tif",
                            "product_version": "2019",
                            "product_date": "2019-01-01",
                            "license": "swisstopo open data terms",
                            "extent_lv95_m": {
                                "xmin": 2696000.0,
                                "ymin": 1167000.0,
                                "xmax": 2697000.0,
                                "ymax": 1168000.0,
                            },
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        self._copy_repo_file(
            ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
            repo_root / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
        )
        self._write_verified_cache_manifest(repo_root, "chant_sura_fluelapass_portability_example_v1")

    def _compiler_report_with_missing_prepared_input(
        self,
        missing_relative_path: str,
        *,
        under_tschamut: bool = False,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_compiler_inputs(repo_root, config_path)
            missing_root = "data/processed/swisstopo/tschamut_public_pilot/input" if under_tschamut else "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input"
            self._remove_repo_file(repo_root, f"{missing_root}/{missing_relative_path}")
            release_polygon_path = self._write_release_polygon(repo_root)
            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"
            return planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=output_root,
            )

    def _copy_repo_file(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def _remove_repo_file(self, repo_root: Path, relative_path: str) -> None:
        path = repo_root / relative_path
        if path.exists():
            path.unlink()

    def _build_aoi_to_map_smoke_fixture(self, repo_root: Path, output_tmp: str) -> dict[str, object]:
        output_dir = Path(output_tmp) / "smoke" / "hazard"
        output_dir.mkdir(parents=True, exist_ok=True)
        status = hazard.main_with_args(
            [
                "--case",
                str(ROOT / "tests/fixtures/hazard/plane_case.yaml"),
                "--diagnostics",
                str(ROOT / "tests/fixtures/hazard/diagnostics.json"),
                "--output-dir",
                str(output_dir),
                "--cell-size",
                "1.0",
                "--no-plots",
                "--export-geotiff",
                "--pilot-gis-package",
                "--pilot-gis-package-manifest-json",
                str(output_dir / "plane_pilot_gis_package_manifest.json"),
                "--map-package-manifest-json",
                str(output_dir / "plane_map_package_manifest.json"),
                "--source-zone-metadata-path",
                str(
                    repo_root
                    / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
                ),
                "--scenario-table-path",
                str(
                    repo_root
                    / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
                ),
                "--map-product-id",
                "aoi_to_map_smoke_fixture",
                "--probability-mode",
                "unweighted_diagnostic",
                "--normalization-scope",
                "conditioned_on_filter",
                "--pilot-gis-qa-status",
                "inconclusive",
                "--pilot-gis-qa-note",
                "Fixture-backed AOI-to-map regression summary.",
            ]
        )
        self.assertEqual(status, 0)

        hazard_manifest = json.loads((output_dir / "hazard_fixture_plane_manifest.json").read_text(encoding="utf-8"))
        map_manifest = json.loads((output_dir / "plane_map_package_manifest.json").read_text(encoding="utf-8"))
        pilot_manifest = json.loads((output_dir / "plane_pilot_gis_package_manifest.json").read_text(encoding="utf-8"))
        audit_report = build_gis_cog_readiness_report(
            [output_dir],
            raster_metadata_provider=lambda path: {
                "status": "ok",
                "driver": "GTiff",
                "epsg": 2056,
                "overview_count": 1,
                "block_size": [16, 16],
                "size": [32, 32],
                "image_structure": {"LAYOUT": "COG"},
            },
        )
        return {
            "output_dir": output_dir,
            "hazard_manifest": hazard_manifest,
            "map_manifest": map_manifest,
            "pilot_manifest": pilot_manifest,
            "audit_report": audit_report,
        }

    def _build_first_failure_summary(self, dry_run_report: dict[str, object], audit_report: dict[str, object]) -> dict[str, str]:
        blocker = dry_run_report["prepared_pilot_compiler"]["first_blocker"]  # type: ignore[index]
        return {
            "first_broken_step_id": str(blocker.get("step_id", "")),
            "first_broken_step_label": str(blocker.get("label", "")),
            "first_broken_input": str(blocker.get("first_missing_input", "")),
            "summary": (
                f"first broken workflow step: {blocker.get('step_id', '')} "
                f"({blocker.get('label', '')}); next input: {blocker.get('first_missing_input', '')}; "
                f"qa_status={audit_report.get('gis_cog_readiness_status', '')}"
            ),
        }

    def _write_verified_cache_manifest(self, repo_root: Path, candidate_site_id: str) -> None:
        cache_root = repo_root / "data/processed/swisstopo" / candidate_site_id / "input"
        terrain_path = cache_root / "terrain.asc"
        terrain_metadata_path = cache_root / "terrain_metadata.yaml"
        terrain_bytes = terrain_path.read_bytes()
        terrain_checksum = hashlib.sha256(terrain_bytes).hexdigest()
        terrain_metadata = yaml.safe_load(terrain_metadata_path.read_text(encoding="utf-8"))
        terrain_metadata["source_product_id"] = "swissalti3d_fixture_terrain_crop"
        terrain_metadata["source_product_name"] = "swissALTI3D"
        terrain_metadata["source_url_or_download_record"] = "https://example.invalid/swisstopo"
        terrain_metadata["product_version_or_date"] = "fixture-2019"
        terrain_metadata["tile_id_or_delivery_identifier"] = "fixture-tile-2793-1180"
        terrain_metadata["checksum_sha256"] = terrain_checksum
        terrain_metadata["license_or_terms_reference"] = terrain_metadata.get(
            "license",
            "synthetic fixture for repository tests; real swisstopo data remain subject to swisstopo terms",
        )
        terrain_metadata["crs"] = "EPSG:2056"
        terrain_metadata["resolution_m"] = 2.0
        terrain_metadata["crop_extent_lv95_m"] = terrain_metadata["extent_lv95_m"]
        terrain_metadata_path.write_text(yaml.safe_dump(terrain_metadata, sort_keys=False), encoding="utf-8")

        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "products": [
                {
                    "product_id": "terrain_crop",
                    "source_product_id": "swissalti3d_fixture_terrain_crop",
                    "source_product_name": "swissALTI3D",
                    "source_url_or_download_record": "https://example.invalid/swisstopo",
                    "product_version_or_date": "fixture-2019",
                    "tile_id_or_delivery_identifier": "fixture-tile-2793-1180",
                    "checksum_sha256": terrain_checksum,
                    "crs": "EPSG:2056",
                    "resolution_m": 2.0,
                    "crop_extent_lv95_m": terrain_metadata["extent_lv95_m"],
                    "license_or_terms_reference": terrain_metadata["license_or_terms_reference"],
                    "staged_path": "terrain.asc",
                    "metadata_path": "terrain_metadata.yaml",
                }
            ],
        }
        manifest_path = cache_root / "public_geodata_cache_manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

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
