from __future__ import annotations

import io
import hashlib
import json
import importlib.util
import shutil
import tempfile
import unittest
import time
from pathlib import Path
from contextlib import redirect_stdout
from unittest import mock

import yaml
from scripts.lib import workflow_validation


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT_PATH = ROOT / "scripts" / "bootstrap_aoi_manifest.py"
SCRIPT_PATH = ROOT / "scripts" / "run_aoi_hazard_workflow.py"
PACKAGE_SCRIPT_PATH = ROOT / "scripts" / "package_aoi_hazard_map.py"
PLANNER_SCRIPT_PATH = ROOT / "scripts" / "plan_aoi_to_prepared_pilot_dry_run.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
MANAGEMENT_SCENARIO_PRESSURE_BUNDLE_ROOT = (
    ROOT / "validation/private/source_zone_review"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


workflow = _load_module(SCRIPT_PATH, "run_aoi_hazard_workflow")
bootstrap = _load_module(BOOTSTRAP_SCRIPT_PATH, "bootstrap_aoi_manifest_for_front_door_tests")
package = _load_module(PACKAGE_SCRIPT_PATH, "package_aoi_hazard_map_for_front_door_tests")
planner = _load_module(PLANNER_SCRIPT_PATH, "plan_aoi_to_prepared_pilot_dry_run_for_front_door_tests")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_front_door_tests",
)
freezer = _load_module(
    ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py",
    "generate_candidate_source_zone_scenarios_for_front_door_tests",
)


class RunAoiHazardWorkflowTests(unittest.TestCase):
    def _run_module_main(self, module, args: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = module.main(args)
        return code, stdout.getvalue().strip()

    def _run_main(self, args: list[str]) -> tuple[int, str]:
        return self._run_module_main(workflow, args)

    def test_command_dispatch_routes_to_the_expected_backend_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            with mock.patch.object(
                workflow,
                "build_aoi_workflow_report",
                return_value={
                    "schema_version": "aoi_workflow_stub_v1",
                    "workflow_classification": "blocked_fixture_backed_inputs",
                    "prepared_pilot_input_classification": "fixture_backed",
                    "workflow_steps": [],
                    "blocked_missing_inputs": [],
                    "ready_for_next_step": {
                        "status": "blocked_fixture_backed_inputs",
                        "next_step": "none",
                        "requires_explicit_permission": False,
                        "permission_recorded": False,
                        "permission_note": "",
                    },
                    "claim_boundaries": {"operational_claims_allowed": False},
                },
            ), mock.patch.object(
                workflow,
                "build_package_report",
                return_value={
                    "schema_version": "gis_cog_stub_v1",
                    "gis_cog_readiness_status": "gis_package_ready",
                    "blocked_missing_inputs": [],
                    "claim_boundaries": {"operational_claims_allowed": False},
                },
            ), mock.patch.object(
                workflow.COMMAND_PLAN,
                "build_report",
                return_value={
                    "schema_version": "portable_pilot_command_plan_v1",
                    "command_plan_status": "ready",
                    "blocked_template_commands": [],
                    "ignored_output_paths": [],
                },
            ):
                status_report = workflow.build_report(
                    command="status",
                    site_config=config_path,
                    repo_root=repo_root,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                )
                package_report = workflow.build_report(
                    command="package-map",
                    site_config=config_path,
                    repo_root=repo_root,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                )

        self.assertEqual(status_report["command"], "status")
        self.assertEqual(status_report["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(status_report["next_action"], "plan")
        self.assertEqual(package_report["command"], "package-map")
        self.assertEqual(package_report["status"], "gis_package_ready")
        self.assertEqual(package_report["next_action"], "collect")

    def test_clean_checkout_status_reports_the_first_blocker_and_prepare_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            report = workflow.build_report(
                command="status",
                site_config=config_path,
                repo_root=repo_root,
                acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
            )

        self.assertEqual(report["schema_version"], "aoi_hazard_workflow_front_door_v1")
        self.assertEqual(report["status"], "blocked_missing_real_core_inputs")
        self.assertEqual(report["next_action"], "prepare")
        self.assertTrue(report["first_blocker"]["blocked_reason"])
        self.assertTrue(report["expected_paths"]["required_inputs"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_prepare_clean_checkout_reports_product_resolution_as_the_first_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
            )

        self.assertEqual(report["schema_version"], "aoi_hazard_prepare_front_door_v1")
        self.assertEqual(report["status"], "blocked_missing_inputs")
        self.assertEqual(report["first_blocker"]["step_id"], "product_resolution")
        self.assertIn("plan_swisstopo_aoi_acquisition.py", report["next_command"])
        self.assertTrue(report["workflow_steps"][0]["status"] == "ready")
        self.assertEqual(report["workflow_steps"][1]["status"], "blocked_missing_inputs")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_prepare_partial_path_reports_release_candidate_planning_as_the_first_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._write_real_public_context_bundles(repo_root)
            self._write_real_context_cache_manifest(repo_root)
            self._write_real_core_inputs(
                repo_root,
                categories={
                    "terrain_crop",
                    "terrain_metadata",
                    "aoi_tile_catalog",
                },
            )

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
            )

        self.assertEqual(report["first_blocker"]["step_id"], "release_candidate_planning")
        self.assertEqual(report["workflow_steps"][1]["status"], "ready")
        self.assertEqual(report["workflow_steps"][2]["status"], "ready")
        self.assertEqual(report["workflow_steps"][3]["status"], "ready")
        self.assertEqual(report["workflow_steps"][4]["status"], "blocked_missing_inputs")
        self.assertIn("plan_terrain_release_zone_candidates.py", report["next_command"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_prepare_reports_the_adjacent_candidate_scenario_table_when_the_bundle_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_prepared_pilot_inputs(repo_root, config_path)
            self._copy_management_scenario_pressure_bundle(repo_root)
            self._write_real_context_cache_manifest(repo_root)
            output_root = (
                Path(output_tmp)
                / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"
            )

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
                prepared_pilot_output_root=output_root,
            )

        self.assertEqual(report["status"], "ready_for_planning")
        self.assertEqual(report["next_step"], "release_candidate_planning")
        self.assertIn("plan_terrain_release_zone_candidates.py", report["next_command"])
        self.assertEqual(report["workflow_steps"][5]["status"], "ready")
        self.assertNotIn("source-zone footprint", report["workflow_steps"][5]["blocked_reason"])
        self.assertEqual(report["prepared_pilot_compiler"]["classification"], "ready_for_balfrin_postproc")
        self.assertEqual(report["prepared_pilot_compiler"]["first_blocker"]["step_id"], "prepared_pilot_command_plan")
        self.assertEqual(report["prepared_pilot_compiler"]["first_blocker"]["status"], "deferred_public_context_inputs")
        self.assertIn("tb404_management_aoi_scenario_table/scenario_table.csv", report["prepared_pilot_compiler_report"]["case_skeleton_output"]["case_skeleton"]["scenario_generation_handoff"]["expected_scenario_table_path"])
        self.assertIn("tb404_management_aoi_scenario_table", report["prepared_pilot_compiler_report"]["case_skeleton_output"]["case_skeleton"]["scenario_generation_handoff"]["scenario_table_manifest_path"])
        self.assertTrue(
            any(
                item.get("command_id") == "second_site_release_plan_execution_template"
                for item in report["prepared_pilot_compiler"]["run_manifest"]["management_aoi_scenario_pressure"]["command_plan_implications"]
            )
        )

    def test_prepare_fixture_backed_cache_blocks_terrain_preprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._write_real_context_cache_manifest(repo_root, provenance_classification="fixture_backed")

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
            )

        self.assertEqual(report["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["first_blocker"]["step_id"], "public_geodata_cache_verification")
        self.assertIn("fixture-backed", report["first_blocker"]["blocked_reason"])
        self.assertEqual(report["workflow_steps"][0]["status"], "ready")
        self.assertEqual(report["workflow_steps"][1]["status"], "ready")
        self.assertEqual(report["workflow_steps"][2]["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["workflow_steps"][3]["status"], "ready")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_prepare_ready_path_reports_release_candidate_planning_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._write_real_public_context_bundles(repo_root)
            self._write_real_context_cache_manifest(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
            )

        self.assertEqual(report["status"], "ready_for_planning")
        self.assertIsNone(report["first_blocker"])
        self.assertEqual(report["next_step"], "release_candidate_planning")
        self.assertIn("plan_terrain_release_zone_candidates.py", report["next_command"])
        self.assertTrue(all(step["status"] == "ready" for step in report["workflow_steps"]))
        self.assertEqual(report["workflow_summary"]["blocked_step_count"], 0)
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_prepare_command_materializes_prepared_pilot_bundle_when_output_root_is_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_prepared_pilot_inputs(repo_root, config_path)
            self._write_real_context_cache_manifest(repo_root)
            output_root = (
                Path(output_tmp)
                / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run"
            )

            report = workflow.build_report(
                command="prepare",
                site_config=config_path,
                repo_root=repo_root,
                prepared_pilot_output_root=output_root,
            )

            self.assertEqual(report["status"], "ready_for_planning")
            self.assertIn("prepared_pilot_compiler", report)
            self.assertIn("prepared_pilot_compiler_report", report)
            self.assertEqual(report["prepared_pilot_compiler"]["classification"], "ready_for_balfrin_postproc")
            self.assertEqual(report["prepared_pilot_compiler_report"]["case_skeleton_output"]["write_status"], "written")
            self.assertTrue(
                Path(report["prepared_pilot_compiler_report"]["case_skeleton_output"]["run_manifest_path"]).exists()
            )
            self.assertTrue(
                Path(report["prepared_pilot_compiler_report"]["case_skeleton_output"]["case_skeleton_path"]).exists()
            )

    def test_status_main_renders_concise_text_and_json_for_ready_report(self) -> None:
        ready_report = {
            "schema_version": workflow.SCHEMA_VERSION,
            "command": "status",
            "workflow_status": "ready",
            "next_action": "submit-balfrin",
            "first_blocker": None,
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py submit-balfrin --format json",
            "expected_inputs": [],
            "expected_outputs": ["submission request", "submission summary"],
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
        }

        with mock.patch.object(workflow, "build_status_report", return_value=ready_report):
            text_code, text_output = self._run_main(["status", "--format", "text"])
            json_code, json_output = self._run_main(["status", "--format", "json"])

        self.assertEqual(text_code, 0)
        self.assertEqual(json_code, 0)
        self.assertIn("workflow_status: ready", text_output)
        self.assertIn("next_command: PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py submit-balfrin --format json", text_output)
        self.assertIn("required_inputs:", text_output)
        self.assertIn("generated_outputs:", text_output)
        self.assertIn("claim_boundaries:", text_output)
        self.assertNotIn("delegate_statuses", text_output)
        self.assertLessEqual(len(text_output.splitlines()), 15)
        parsed = json.loads(json_output)
        self.assertEqual(parsed["workflow_status"], "ready")
        self.assertEqual(parsed["next_action"], "submit-balfrin")
        self.assertEqual(parsed["expected_outputs"], ["submission request", "submission summary"])

    def test_workflow_main_renders_compact_text_summary_for_copy_paste(self) -> None:
        workflow_report = {
            "schema_version": workflow.WORKFLOW_SCHEMA_VERSION,
            "command": "workflow",
            "status": "blocked_missing_inputs",
            "current_stage": "status",
            "next_action": "prepare",
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --format json",
            "first_blocker": {
                "step_id": "tiny_bounded_ensemble_handoff",
                "label": "AOI guided workflow",
                "status": "blocked_missing_inputs",
                "blocked_reason": "read-only front door only",
                "missing_inputs": [
                    "/tmp/aoi_smoke/site/aoi_manifest.yaml",
                    "/tmp/aoi_workflow/bootstrap",
                ],
            },
            "command_sequence": [
                "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py status --format json",
                "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --format json",
            ],
            "generated_artifact_paths": {
                "bootstrap_output_root": "/tmp/aoi_workflow/bootstrap",
                "workflow_output_root": "/tmp/aoi_workflow",
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "candidate_site_id": "guided_fixture",
            "candidate_site_name": "Guided Fixture",
        }

        with mock.patch.object(workflow, "build_workflow_report", return_value=workflow_report):
            code, text_output = self._run_main(
                [
                    "workflow",
                    "--site-config",
                    str(ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"),
                    "--workflow-output-root",
                    "/tmp/aoi_workflow",
                    "--format",
                    "text",
                ]
            )

        self.assertEqual(code, 2)
        self.assertIn("workflow_status: blocked_missing_inputs", text_output)
        self.assertIn("next_command: PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --format json", text_output)
        self.assertIn("first_blocker:", text_output)
        self.assertIn("required_inputs:", text_output)
        self.assertIn("generated_outputs:", text_output)
        self.assertIn("workflow_output_root=/tmp/aoi_workflow", text_output)
        self.assertNotIn("command_sequence:", text_output)
        self.assertLessEqual(len(text_output.splitlines()), 16)

    def test_help_includes_the_simple_bounds_to_review_example(self) -> None:
        help_text = workflow.build_parser().format_help()

        self.assertIn("Simplest bounds-to-review dry run:", help_text)
        self.assertIn("scripts/run_aoi_hazard_workflow.py workflow", help_text)
        self.assertIn("--workflow-output-root /tmp/aoi_workflow", help_text)
        self.assertIn("--format text", help_text)

    def test_fixture_backed_status_aggregation_surfaces_expected_paths_and_claim_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as scratch:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._write_real_core_inputs(
                repo_root,
                categories={
                    "terrain_crop",
                    "terrain_metadata",
                    "aoi_tile_catalog",
                    "source_zone_metadata",
                    "scenario_table",
                    "source_scenario_policy",
                },
            )
            acquisition_package_path = self._write_acquisition_package(repo_root, classification="fixture_backed")
            self._write_real_context_cache_manifest(repo_root)
            artifact_root = Path(scratch) / "hazard/results/tschamut_public_pilot/target_gate_v1"
            artifact_root.mkdir(parents=True, exist_ok=True)

            report = workflow.build_report(
                command="status",
                site_config=config_path,
                repo_root=repo_root,
                acquisition_package_path=acquisition_package_path,
                artifact_root=artifact_root,
            )

        self.assertEqual(report["workflow_summary"]["prepared_pilot_input_classification"], "fixture_backed")
        self.assertEqual(report["workflow_summary"]["workflow_classification"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["next_action"], "plan")
        self.assertEqual(report["first_blocker"]["step_id"], "public_context_readiness")
        self.assertEqual(report["first_blocker"]["blocked_reason"], "deferred_public_context_inputs")
        self.assertTrue(report["expected_paths"]["case_skeleton_path"])
        self.assertTrue(report["expected_paths"]["portable_command_plan_ignored_roots"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertEqual(report["delegate_statuses"]["aoi_workflow"], report["workflow_summary"]["workflow_classification"])

    def test_status_main_reports_blocked_missing_inputs_in_text_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            text_code, text_output = self._run_main([
                "status",
                "--site-config",
                str(config_path),
                "--repo-root",
                str(repo_root),
                "--format",
                "text",
            ])
            json_code, json_output = self._run_main([
                "status",
                "--site-config",
                str(config_path),
                "--repo-root",
                str(repo_root),
                "--format",
                "json",
            ])

        self.assertEqual(text_code, 2)
        self.assertEqual(json_code, 2)
        self.assertIn("workflow_status:", text_output)
        self.assertIn("first_blocker:", text_output)
        parsed = json.loads(json_output)
        self.assertTrue(parsed["workflow_status"].startswith("blocked"))
        self.assertTrue(parsed["next_command"])
        self.assertIsInstance(parsed["expected_inputs"], list)

    def test_status_main_rejects_invalid_site_config_with_exit_code_64(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            bad_config = repo_root / "site_config.yaml"
            bad_config.write_text("candidate_site_id: [unterminated\n", encoding="utf-8")

            code, output = self._run_main([
                "status",
                "--site-config",
                str(bad_config),
                "--repo-root",
                str(repo_root),
                "--format",
                "json",
            ])

        self.assertEqual(code, 64)
        parsed = json.loads(output)
        self.assertEqual(parsed["workflow_status"], "blocked_invalid_input")
        self.assertEqual(parsed["first_blocker"]["step_id"], "site_config")
        self.assertTrue(parsed["next_command"])

    def test_status_build_report_marks_unsupported_command_state_as_invalid_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)

            report = workflow.build_status_report(
                command="bogus",
                site_config=config_path,
                repo_root=repo_root,
                acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
            )

        self.assertEqual(report["workflow_status"], "blocked_invalid_input")
        self.assertEqual(report["first_blocker"]["step_id"], "command")
        self.assertIn("run_aoi_hazard_workflow.py status", report["next_command"])
        self.assertEqual(workflow.status_exit_code(report), 64)

    def test_workflow_command_bootstraps_bounds_and_reports_the_first_blocker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workflow_root = Path(tmp) / "guided_workflow"

            code, output = self._run_module_main(
                workflow,
                [
                    "workflow",
                    "--bounds",
                    "2696376",
                    "1167384",
                    "2696476",
                    "1167484",
                    "--workflow-output-root",
                    str(workflow_root),
                    "--format",
                    "json",
                ],
            )

        report = json.loads(output)
        self.assertEqual(code, 2)
        self.assertEqual(report["command"], "workflow")
        self.assertEqual(report["current_stage"], "status")
        self.assertTrue(report["status"].startswith("blocked"))
        self.assertTrue(report["first_blocker"])
        self.assertIn("prepare", report["next_command"])
        self.assertTrue(report["generated_artifact_paths"]["bootstrap_output_root"].endswith("/bootstrap"))
        self.assertTrue(report["command_sequence"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])

    def test_workflow_command_reports_ready_fixture_sequence_without_running_local_steps(self) -> None:
        ready_status_report = {
            "schema_version": "aoi_hazard_workflow_front_door_v1",
            "command": "status",
            "workflow_status": "ready_for_next_step",
            "next_action": "run-local-smoke",
            "first_blocker": None,
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-local-smoke --format json",
            "expected_paths": {
                "required_inputs": ["validation/cases/probabilistic_phase1_smoke.yaml"],
                "case_skeleton_path": "",
                "case_skeleton_paths": [],
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "candidate_site_id": "guided_fixture",
            "candidate_site_name": "Guided Fixture",
        }
        ready_prepare_report = {
            "schema_version": "aoi_hazard_prepare_front_door_v1",
            "command": "prepare",
            "status": "ready_for_planning",
            "next_step": "release_candidate_planning",
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-local-smoke --format json",
            "first_blocker": None,
            "expected_paths": {
                "site_config": "/tmp/guided_fixture/aoi_manifest.yaml",
                "acquisition_manifest": "/tmp/guided_fixture/input/public_geodata_acquisition.yaml",
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "workflow_steps": [],
            "workflow_summary": {"blocked_step_count": 0},
        }

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workflow_root = Path(tmp) / "guided_workflow"
            with mock.patch.object(workflow, "build_status_report", return_value=ready_status_report), mock.patch.object(
                workflow,
                "build_prepare_report",
                return_value=ready_prepare_report,
            ):
                report = workflow.build_workflow_report(
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    bounds=None,
                    site_id=None,
                    site_name=None,
                    workflow_output_root=workflow_root,
                    repo_root=ROOT,
                    execute_safe_local_steps=False,
                )

        self.assertEqual(report["status"], "ready_for_local_smoke")
        self.assertEqual(report["current_stage"], "run-local-smoke")
        self.assertEqual(report["next_action"], "run-local-smoke")
        self.assertIn("run-local-smoke", report["next_command"])
        self.assertEqual(len(report["command_sequence"]), 5)
        self.assertTrue(report["generated_artifact_paths"]["smoke_output_root"].endswith("/smoke"))
        self.assertTrue(report["generated_artifact_paths"]["package_output_root"].endswith("/package"))
        self.assertTrue(report["generated_artifact_paths"]["review_output_root"].endswith("/review"))

    def test_workflow_command_executes_safe_local_smoke_package_and_review_path(self) -> None:
        ready_status_report = {
            "schema_version": "aoi_hazard_workflow_front_door_v1",
            "command": "status",
            "workflow_status": "ready_for_next_step",
            "next_action": "run-local-smoke",
            "first_blocker": None,
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-local-smoke --format json",
            "expected_paths": {"required_inputs": []},
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "candidate_site_id": "guided_fixture",
            "candidate_site_name": "Guided Fixture",
        }
        ready_prepare_report = {
            "schema_version": "aoi_hazard_prepare_front_door_v1",
            "command": "prepare",
            "status": "ready_for_planning",
            "next_step": "release_candidate_planning",
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-local-smoke --format json",
            "first_blocker": None,
            "expected_paths": {},
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "workflow_steps": [],
            "workflow_summary": {"blocked_step_count": 0},
        }
        smoke_root = Path("/tmp") / "tb315_workflow_smoke"
        package_root = Path("/tmp") / "tb315_workflow_package"
        review_root = Path("/tmp") / "tb315_workflow_review"
        smoke_report = {
            "schema_version": "aoi_local_tiny_smoke_run_v1",
            "status": "smoke_completed",
            "validation_output_root": str(smoke_root / "validation" / "results"),
            "hazard_output_root": str(smoke_root / "hazard" / "results" / "probabilistic_phase1_smoke"),
            "commands": {"validation": ["validate"], "hazard": ["hazard"]},
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
        }
        package_report = {
            "schema_version": "aoi_hazard_map_package_v1",
            "status": "cog_blocked",
            "claim_boundary": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "cog_blockers": ["reach_probability:blocked"],
            "missing_hazard_outputs": [],
            "review_surface_paths": {"manifest": str(package_root / "aoi_map_qa_review_manifest.json"), "html": str(package_root / "index.html")},
        }
        review_report = {
            "schema_version": "aoi_map_qa_review_v1",
            "status": "review_ready_with_warnings",
            "review_surface_paths": {"manifest": str(review_root / "aoi_map_qa_review_manifest.json"), "html": str(review_root / "index.html")},
            "claim_boundary": {
                "operational_claims_allowed": False,
                "annualized": False,
            },
        }

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            workflow_root = Path(tmp) / "guided_workflow"
            with mock.patch.object(workflow, "build_status_report", return_value=ready_status_report), mock.patch.object(
                workflow,
                "build_prepare_report",
                return_value=ready_prepare_report,
            ), mock.patch.object(
                workflow,
                "build_local_smoke_report",
                return_value=smoke_report,
            ), mock.patch.object(
                workflow.PACKAGE_AOI,
                "package_aoi_hazard_map",
                return_value=package_report,
            ), mock.patch.object(
                workflow.QA_REVIEW,
                "build_review_surface",
                return_value=review_report,
            ):
                report = workflow.build_workflow_report(
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    bounds=None,
                    site_id=None,
                    site_name=None,
                    workflow_output_root=workflow_root,
                    repo_root=ROOT,
                    execute_safe_local_steps=True,
                )

        self.assertEqual(report["current_stage"], "qa-review")
        self.assertEqual(report["status"], "review_ready_with_warnings")
        self.assertEqual(report["next_action"], "inspect qa review")
        self.assertEqual(report["stage_reports"]["run-local-smoke"]["status"], "smoke_completed")
        self.assertEqual(report["stage_reports"]["package-map"]["status"], "cog_blocked")
        self.assertEqual(report["stage_reports"]["qa-review"]["status"], "review_ready_with_warnings")
        self.assertTrue(report["generated_artifact_paths"]["review_html"].endswith("index.html"))
        self.assertEqual(len(report["command_sequence"]), 5)

    def test_candidate_review_command_renders_overlay_report(self) -> None:
        fake_report = {
            "schema_version": "aoi_candidate_review_front_door_v1",
            "command": "candidate-review",
            "status": "ready",
            "candidate_site_id": "guided_fixture",
            "candidate_site_name": "Guided Fixture",
            "candidate_review_output_root": "/tmp/tb409_aoi_candidate_review",
            "candidate_product_output_root": "/tmp/tb409_aoi_candidate_review/candidate_products",
            "candidate_review_overlay_output_root": "/tmp/tb409_aoi_candidate_review/candidate_review_overlays",
            "candidate_review_manifest_path": "/tmp/tb409_aoi_candidate_review/candidate_review_overlays/guided_fixture_candidate_review_overlay_manifest.json",
            "candidate_review_overlay_paths": {
                "topographic_map": "/tmp/tb409_aoi_candidate_review/candidate_review_overlays/guided_fixture_topographic_map_review_overlay.png",
                "orthophoto": "/tmp/tb409_aoi_candidate_review/candidate_review_overlays/guided_fixture_orthophoto_review_overlay.png",
            },
            "first_blocker": {
                "step_id": "candidate-review",
                "blocked_reason": "",
            },
            "next_action": "inspect candidate overlays",
            "next_command": "PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py candidate-review --candidate-review-output-root /tmp/tb409_aoi_candidate_review --format json",
            "expected_paths": {
                "candidate_products_root": "/tmp/tb409_aoi_candidate_review/candidate_products",
                "candidate_review_overlay_root": "/tmp/tb409_aoi_candidate_review/candidate_review_overlays",
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "non_operational_warnings": [],
        }

        with mock.patch.object(workflow, "build_candidate_review_report", return_value=fake_report) as build_candidate_review_report:
            code, output = self._run_main(
                [
                    "candidate-review",
                    "--candidate-review-output-root",
                    "/tmp/tb409_aoi_candidate_review",
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(code, 0)
        build_candidate_review_report.assert_called_once()
        parsed = json.loads(output)
        self.assertEqual(parsed["command"], "candidate-review")
        self.assertEqual(parsed["status"], "ready")
        self.assertEqual(parsed["candidate_review_manifest_path"], fake_report["candidate_review_manifest_path"])
        self.assertIn("topographic_map", parsed["candidate_review_overlay_paths"])
        self.assertIn("orthophoto", parsed["candidate_review_overlay_paths"])

    def test_workflow_command_rejects_invalid_aoi_input(self) -> None:
        report = workflow.build_workflow_report(
            site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
            bounds=[2696476.0, 1167484.0, 2696376.0, 1167384.0],
            site_id="guided_invalid_bounds",
            site_name="Guided Invalid",
            workflow_output_root=Path("/tmp") / "tb315_invalid_workflow",
            repo_root=ROOT,
        )

        self.assertEqual(report["status"], "blocked_invalid_input")
        self.assertEqual(report["current_stage"], "workflow")
        self.assertEqual(report["first_blocker"]["step_id"], "workflow")
        self.assertIn("xmax", report["first_blocker"]["blocked_reason"])

    def test_documented_aoi_bounds_to_review_map_command_chain_smoke(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            work_root = Path(tmp)
            site_root = work_root / "site"
            smoke_root = work_root / "smoke"
            review_root = work_root / "review"

            bootstrap_code, bootstrap_output = self._run_module_main(
                bootstrap,
                [
                    "--output-root",
                    str(site_root),
                    "--site-id",
                    "chant_sura_fluelapass_portability_example_v1",
                    "--bounds",
                    "2696376",
                    "1167384",
                    "2696476",
                    "1167484",
                    "--format",
                    "json",
                ],
            )
            self.assertEqual(bootstrap_code, 0)
            bootstrap_report = json.loads(bootstrap_output)
            self.assertEqual(bootstrap_report["bootstrap_status"], "ready")
            self.assertTrue((site_root / "aoi_manifest.yaml").exists())
            self.assertTrue((site_root / "input" / "public_geodata_acquisition.yaml").exists())

            status_code, status_output = self._run_main(
                [
                    "status",
                    "--site-config",
                    str(site_root / "aoi_manifest.yaml"),
                    "--repo-root",
                    str(ROOT),
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(status_code, 2)
            status_report = json.loads(status_output)
            self.assertEqual(status_report["workflow_status"], "blocked_missing_inputs")
            self.assertEqual(status_report["next_action"], "prepare")
            self.assertEqual(status_report["first_blocker"]["step_id"], "tiny_bounded_ensemble_handoff")

            prepare_code, prepare_output = self._run_main(
                [
                    "prepare",
                    "--site-config",
                    str(site_root / "aoi_manifest.yaml"),
                    "--repo-root",
                    str(ROOT),
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(prepare_code, 2)
            prepare_report = json.loads(prepare_output)
            self.assertEqual(prepare_report["status"], "blocked_missing_inputs")
            self.assertEqual(prepare_report["first_blocker"]["step_id"], "public_geodata_cache_verification")
            self.assertIn("verify_public_geodata_cache.py", prepare_report["next_command"])

            smoke_code, smoke_output = self._run_main(
                [
                    "run-local-smoke",
                    "--repo-root",
                    str(ROOT),
                    "--smoke-output-root",
                    str(smoke_root),
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(smoke_code, 0)
            smoke_report = json.loads(smoke_output)
            self.assertEqual(smoke_report["status"], "smoke_completed")
            self.assertEqual(smoke_report["next_action"], "collect")
            self.assertTrue((smoke_root / "validation" / "results" / "probabilistic_phase1_smoke_manifest.json").exists())
            self.assertTrue((smoke_root / "hazard" / "results" / "probabilistic_phase1_smoke" / "probabilistic_phase1_smoke_map_package_manifest.json").exists())
            self.assertFalse(smoke_report["claim_boundaries"]["operational_claims_allowed"])

            package_code, package_output = self._run_module_main(
                package,
                [
                    "--input-root",
                    str(smoke_root / "hazard" / "results" / "probabilistic_phase1_smoke"),
                    "--output-root",
                    str(review_root),
                    "--overwrite",
                    "--format",
                    "json",
                ],
            )
            self.assertEqual(package_code, 1)
            package_report = json.loads(package_output)
            self.assertEqual(package_report["status"], "cog_blocked")
            self.assertEqual(package_report["review_surface_status"], "review_ready_with_warnings")
            self.assertTrue(package_report["review_surface_paths"]["html"].endswith("index.html"))
            self.assertTrue((review_root / "aoi_hazard_map_package_manifest.json").exists())
            self.assertTrue((review_root / "aoi_hazard_map_package_summary.txt").exists())
            self.assertTrue((review_root / "aoi_map_qa_review_manifest.json").exists())
            self.assertTrue((review_root / "index.html").exists())
            self.assertFalse(package_report["claim_boundary"]["annualized"])

    def test_user_defined_aoi_bounds_guided_front_door_prepared_pilot_and_review_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            work_root = Path(tmp)
            repo_root = work_root / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            site_root = work_root / "site"
            workflow_root = work_root / "workflow"
            bounds = [2696376.0, 1167384.0, 2696476.0, 1167484.0]

            bootstrap_code, bootstrap_output = self._run_module_main(
                bootstrap,
                [
                    "--output-root",
                    str(site_root),
                    "--site-id",
                    "chant_sura_fluelapass_portability_example_v1",
                    "--bounds",
                    *[str(value) for value in bounds],
                    "--format",
                    "json",
                ],
            )
            self.assertEqual(bootstrap_code, 0)
            bootstrap_report = json.loads(bootstrap_output)
            self.assertEqual(bootstrap_report["bootstrap_status"], "ready")
            self.assertTrue((site_root / "aoi_manifest.yaml").exists())

            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_prepared_pilot_inputs(repo_root, config_path)
            self._write_real_context_cache_manifest(repo_root)
            guided_input_root = repo_root / "input"
            guided_input_root.mkdir(parents=True, exist_ok=True)
            staged_input_root = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input"
            for filename in (
                "terrain.asc",
                "terrain_metadata.yaml",
                "aoi_tile_catalog.yaml",
                "source_zone_metadata.yaml",
                "scenario_table.csv",
                "public_geodata_cache_manifest.yaml",
            ):
                self._copy_repo_file(staged_input_root / filename, guided_input_root / filename)
            release_polygon_path = self._write_release_polygon(repo_root)

            guided_report = workflow.build_workflow_report(
                site_config=site_root / "aoi_manifest.yaml",
                bounds=bounds,
                site_id="chant_sura_fluelapass_portability_example_v1",
                site_name="Chant Sura / Flüelapass portability example",
                workflow_output_root=workflow_root,
                repo_root=repo_root,
                execute_safe_local_steps=False,
            )
            self.assertEqual(guided_report["status"], "blocked_missing_inputs")
            self.assertEqual(guided_report["next_action"], "prepare")
            self.assertEqual(guided_report["first_blocker"]["step_id"], "tiny_bounded_ensemble_handoff")
            self.assertEqual(guided_report["stage_reports"]["status"]["workflow_status"], "blocked_missing_inputs")
            self.assertEqual(guided_report["stage_reports"]["prepare"]["status"], "ready_for_planning")
            self.assertEqual(guided_report["workflow_steps"][0]["status"], "blocked_missing_inputs")
            self.assertEqual(guided_report["workflow_steps"][1]["status"], "ready_for_planning")
            self.assertEqual([step["step_id"] for step in guided_report["workflow_steps"]], ["status", "prepare"])
            self.assertTrue(guided_report["generated_artifact_paths"]["workflow_output_root"].endswith("workflow"))

            prepared_report = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=Path(output_tmp)
                / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run",
            )
            prepared_report_path = repo_root / "prepared_pilot_report.yaml"
            prepared_report_path.write_text(yaml.safe_dump(prepared_report, sort_keys=False), encoding="utf-8")

            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/prepared_local_execution"
            def fake_cog_conversion_ready(input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
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

            with mock.patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=fake_cog_conversion_ready):
                local_report = workflow.build_report(
                    command="run-prepared-pilot-local",
                    site_config=config_path,
                    repo_root=ROOT,
                    prepared_pilot_report_path=prepared_report_path,
                    prepared_pilot_output_root=output_root,
                    validation_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                    overwrite=True,
                )

            self.assertEqual(prepared_report["prepared_pilot_compiler"]["classification"], "ready_for_balfrin_postproc")
            self.assertEqual(prepared_report["prepared_pilot_compiler"]["execution_hints"]["local"]["status"], "ready_for_local_smoke")
            self.assertEqual(local_report["status"], "local_execution_ready")
            self.assertEqual(local_report["workflow_steps"][0]["status"], "smoke_completed")
            self.assertIn(local_report["workflow_steps"][1]["status"], {"map_package_ready", "cog_blocked"})
            self.assertTrue(str(local_report["workflow_steps"][2]["status"]).startswith("review_ready"))
            self.assertTrue(Path(local_report["expected_paths"]["qa_review_html"]).exists())
            self.assertFalse(local_report["claim_boundaries"]["operational_claims_allowed"])
            self.assertFalse(local_report["claim_boundaries"]["annual_frequency_claims_allowed"])
            self.assertFalse(local_report["package_report"]["claim_boundary"]["annualized"])
            self.assertIn(
                "conditional-only weights",
                "\n".join(local_report["review_report"]["warnings"]),
            )
            self.assertIn(
                "non-operational status",
                "\n".join(local_report["review_report"]["warnings"]),
            )
            self.assertIn(
                "annual_intensity_frequency",
                local_report["review_report"]["claim_boundary"]["future_unsupported_product_labels"],
            )

    def test_local_tiny_aoi_smoke_run_writes_reduced_outputs_and_hazard_layers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            smoke_root = Path(tmp) / "tb263_smoke"

            with mock.patch.object(
                workflow.COMMAND_PLAN,
                "build_report",
                return_value={
                    "schema_version": "portable_pilot_command_plan_v1",
                    "command_plan_status": "ready",
                },
            ):
                first = workflow.build_report(
                    command="run-local-smoke",
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    repo_root=ROOT,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                    smoke_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                    smoke_output_root=smoke_root,
                )
                stable_keys = (
                    "validation_trajectory",
                    "validation_metadata",
                    "validation_deposition",
                    "hazard_reach_probability_asc",
                    "hazard_reach_probability_tif",
                    "map_package_manifest",
                )
                first_artifacts = {key: first["smoke_run"]["artifact_sha256"][key] for key in stable_keys}
                first_map_package = first["smoke_run"]["map_package_manifest_json"]

                second = workflow.build_report(
                    command="run-local-smoke",
                    site_config=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    repo_root=ROOT,
                    acquisition_package_path=ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml",
                    artifact_root=ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
                    smoke_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                    smoke_output_root=smoke_root,
                )

                smoke = first["smoke_run"]
                second_smoke = second["smoke_run"]
                validation_root = Path(smoke["validation_output_root"])
                hazard_root = Path(smoke["hazard_output_root"])

                self.assertEqual(first["status"], "smoke_completed")
                self.assertEqual(first["next_action"], "collect")
                self.assertEqual(smoke["no_heavy_debug_defaults"]["validation_output_mode"], "rebuildable_reduced_output")
                self.assertTrue(smoke["no_heavy_debug_defaults"]["plots_enabled"] is False)
                self.assertEqual(smoke["no_heavy_debug_defaults"]["conditional_curve_export"], "summary-only")
                self.assertEqual(smoke["no_heavy_debug_defaults"]["grid_csv_export"], "none")
                self.assertFalse(smoke["claim_boundaries"]["operational_claims_allowed"])
                self.assertFalse(smoke["claim_boundaries"]["scale_up_authorized"])
                self.assertFalse(smoke["claim_boundaries"]["physical_probability_claims_allowed"])
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_trajectory.csv").exists())
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv").exists())
                self.assertTrue((validation_root / "probabilistic_phase1_smoke_deposition.csv").exists())
                self.assertFalse((validation_root / "probabilistic_phase1_smoke_trajectories").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_map_package_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_pilot_gis_package_manifest.json").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_reach_probability.asc").exists())
                self.assertTrue((hazard_root / "probabilistic_phase1_smoke_reach_probability.tif").exists())
                self.assertFalse(list(hazard_root.glob("*.csv")))
                self.assertEqual(
                    smoke["hazard_manifest"]["conditional_execution"]["raster_exports"]["grid_csv_export"],
                    "none",
                )
                self.assertFalse(
                    smoke["hazard_manifest"]["conditional_execution"]["raster_exports"]["grid_csv_written"]
                )
                self.assertEqual(
                    smoke["hazard_manifest"]["conditional_execution"]["conditional_curve_export"]["mode"],
                    "summary-only",
                )
                self.assertFalse(smoke["hazard_manifest"]["performance"]["plots_enabled"])
                self.assertEqual(
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                    False,
                )
                self.assertIn(
                    "return_period",
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["future_unsupported_product_labels"],
                )
                second_artifacts = {key: second_smoke["artifact_sha256"][key] for key in stable_keys}
                self.assertEqual(first_artifacts, second_artifacts)
                self.assertEqual(first_map_package, second_smoke["map_package_manifest_json"])
                self.assertEqual(
                    smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                    second_smoke["pilot_gis_package_manifest_json"]["probability_claim_boundary"]["annualized"],
                )

    def test_prepared_pilot_local_execution_writes_validation_hazard_package_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_prepared_pilot_inputs(repo_root, config_path)
            release_polygon_path = self._write_release_polygon(repo_root)
            prepared_report = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run",
            )
            self.assertEqual(prepared_report["prepared_pilot_compiler"]["classification"], "ready_for_balfrin_postproc")
            prepared_report_path = repo_root / "prepared_pilot_report.yaml"
            prepared_report_path.write_text(yaml.safe_dump(prepared_report, sort_keys=False), encoding="utf-8")

            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/prepared_local_execution"
            report = workflow.build_report(
                command="run-prepared-pilot-local",
                site_config=config_path,
                repo_root=ROOT,
                prepared_pilot_report_path=prepared_report_path,
                prepared_pilot_output_root=output_root,
                validation_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
                overwrite=True,
            )
            self.assertEqual(report["status"], "local_execution_ready")
            self.assertEqual(report["prepared_pilot_classification"], "ready_for_balfrin_postproc")
            self.assertEqual(report["first_failure"], None)
            prepared_state = workflow_validation.summarize_prepared_pilot_state(prepared_report)
            self.assertEqual(prepared_state["classification"], "ready_for_balfrin_postproc")
            self.assertEqual(prepared_state["first_blocker"]["step_id"], "prepared_pilot_command_plan")
            path_state = workflow_validation.build_prepared_pilot_local_execution_paths(
                prepared_pilot_report_path=prepared_report_path,
                prepared_pilot_output_root=output_root,
                validation_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
            )
            self.assertEqual(report["output_root"], path_state["output_root"])
            self.assertEqual(report["expected_paths"]["prepared_pilot_report_path"], path_state["expected_paths"]["prepared_pilot_report_path"])
            self.assertTrue(Path(report["validation_output_root"]).exists())
            self.assertTrue(Path(report["hazard_output_root"]).exists())
            self.assertTrue(Path(report["package_output_root"]).exists())
            self.assertTrue(Path(report["review_output_root"]).exists())
            self.assertTrue(Path(report["expected_paths"]["qa_review_html"]).exists())
            self.assertEqual(report["workflow_steps"][0]["status"], "smoke_completed")
            self.assertIn(report["workflow_steps"][1]["status"], {"map_package_ready", "cog_blocked"})
            self.assertTrue(str(report["workflow_steps"][2]["status"]).startswith("review_ready"))
            self.assertTrue(report["manifest_checksums"]["validation_manifest_sha256"])
            self.assertTrue(report["manifest_checksums"]["map_package_manifest_sha256"])
            self.assertTrue(report["manifest_checksums"]["qa_review_manifest_sha256"])
            self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
            self.assertFalse(report["claim_boundaries"]["risk_exposure_vulnerability_claims_allowed"])

    def test_prepared_pilot_local_execution_blocks_overwrite_and_reports_first_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            self._stage_ready_prepared_pilot_inputs(repo_root, config_path)
            release_polygon_path = self._write_release_polygon(repo_root)
            prepared_report = planner.build_report(
                config_path,
                repo_root=repo_root,
                release_polygon_path=release_polygon_path,
                skeleton_output_root=Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/aoi_to_prepared_pilot_dry_run",
            )
            prepared_report_path = repo_root / "prepared_pilot_report.yaml"
            prepared_report_path.write_text(yaml.safe_dump(prepared_report, sort_keys=False), encoding="utf-8")

            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/prepared_local_execution"
            output_root.mkdir(parents=True, exist_ok=True)
            report = workflow.build_report(
                command="run-prepared-pilot-local",
                site_config=config_path,
                repo_root=ROOT,
                prepared_pilot_report_path=prepared_report_path,
                prepared_pilot_output_root=output_root,
                validation_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
            )

        self.assertEqual(report["status"], "blocked_local_execution")
        self.assertEqual(report["first_blocker"]["step_id"], "output_root")
        self.assertTrue(report["first_failure"]["blocked_reason"])
        self.assertIn("overwrite is disabled", report["first_failure"]["blocked_reason"])
        self.assertEqual(report["output_root"], str(output_root))
        path_state = workflow_validation.build_prepared_pilot_local_execution_paths(
            prepared_pilot_report_path=prepared_report_path,
            prepared_pilot_output_root=output_root,
            validation_case_path=ROOT / "validation/cases/probabilistic_phase1_smoke.yaml",
        )
        self.assertEqual(report["expected_paths"], path_state["expected_paths"])

    def test_prepared_pilot_local_execution_uses_two_candidate_freezer_inputs_and_reports_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            repo_root = Path(tmp)
            config_path = self._write_candidate_config(repo_root)
            review_package_path = self._write_two_candidate_review_package(repo_root)
            freezer_output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/freezer"
            freezer_report = freezer.build_freezer_report(
                review_package_path=review_package_path,
                accepted_candidate_ids=["cand_accept_a", "cand_accept_b"],
                output_root=freezer_output_root,
                trajectory_count=24,
                seed=34014,
            )

            smoke_case_path = self._write_multi_zone_smoke_case(
                repo_root=repo_root,
                source_zone_metadata_path=Path(freezer_report["output_paths"]["source_zone_metadata"]),
                scenario_table_path=Path(freezer_report["output_paths"]["scenario_table"]),
            )
            prepared_report_path = self._write_ready_prepared_pilot_report(repo_root)
            output_root = Path(output_tmp) / "validation/private/chant_sura_fluelapass_portability_example_v1/prepared_local_execution"

            started_at = time.perf_counter()
            report = workflow.build_report(
                command="run-prepared-pilot-local",
                site_config=config_path,
                repo_root=ROOT,
                prepared_pilot_report_path=prepared_report_path,
                prepared_pilot_output_root=output_root,
                validation_case_path=smoke_case_path,
                overwrite=True,
            )
            runtime_seconds = time.perf_counter() - started_at
            qa_review_html_exists = Path(report["expected_paths"]["qa_review_html"]).exists()

        self.assertEqual(freezer_report["accepted_candidate_count"], 2)
        self.assertEqual(freezer_report["release_row_count"], 2)
        self.assertEqual(freezer_report["scenario_row_count"], 6)
        self.assertEqual(report["status"], "local_execution_ready")
        self.assertEqual(report["workflow_steps"][0]["status"], "smoke_completed")
        self.assertIn(report["workflow_steps"][1]["status"], {"map_package_ready", "cog_blocked"})
        self.assertTrue(str(report["workflow_steps"][2]["status"]).startswith("review_ready"))
        self.assertGreater(report["measured_runtime_seconds"], 0.0)
        self.assertGreater(runtime_seconds, 0.0)
        self.assertGreater(report["package_file_count"], 0)
        self.assertGreater(report["package_byte_count"], 0)
        self.assertIn("generate_aoi_map_qa_review.py", report["qa_review_entrypoint"])
        self.assertTrue(qa_review_html_exists)
        self.assertTrue(report["package_report"]["review_surface_status"].startswith("review_ready"))
        self.assertEqual(report["review_report"]["layer_presence"]["context_layers"]["count"], 0)
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["annual_frequency_claims_allowed"])

    def _write_candidate_config(
        self,
        repo_root: Path,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
        candidate_site_name: str = "Chant Sura / Flüelapass portability example",
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
        input_root = repo_root / "data/processed/swisstopo" / candidate_site_id / "input"
        context_root = repo_root / "data/processed/swisstopo" / candidate_site_id / "context"
        validation_root = repo_root / "validation/private" / candidate_site_id
        hazard_root = repo_root / "hazard/results" / candidate_site_id
        policy_root = repo_root / "validation/policies"
        config_data["expected_processed_input_root"] = str(input_root)
        config_data["expected_processed_context_root"] = str(context_root)
        config_data["expected_validation_private_root"] = str(validation_root)
        config_data["expected_hazard_results_root"] = str(hazard_root)
        config_data["expected_terrain_crop_path"] = str(input_root / "terrain.asc")
        config_data["expected_terrain_metadata_path"] = str(input_root / "terrain_metadata.yaml")
        config_data["expected_source_zone_metadata_path"] = str(input_root / "source_zone_metadata.yaml")
        config_data["expected_scenario_table_path"] = str(input_root / "scenario_table.csv")
        config_data["expected_aoi_tile_catalog_path"] = str(input_root / "aoi_tile_catalog.yaml")
        config_data["expected_source_scenario_policy_path"] = str(
            policy_root / f"{candidate_site_id}_source_scenario_policy_v1.yaml"
        )
        config_data["expected_swissimage_context_root"] = str(context_root / "swissimage")
        config_data["expected_swisstlm3d_context_root"] = str(context_root / "swisstlm3d")
        config_data["expected_swisstlm3d_metadata_path"] = str(context_root / "swisstlm3d" / "metadata.json")
        config_data["expected_swisssurface3d_context_root"] = str(context_root / "swisssurface3d")
        config_data["expected_swisssurface3d_raster_context_root"] = str(context_root / "swisssurface3d_raster")
        config_data["expected_swissbuildings3d_context_root"] = str(context_root / "swissbuildings3d")
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _stage_ready_prepared_pilot_inputs(self, repo_root: Path, config_path: Path) -> None:
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
        self._write_real_context_cache_manifest(repo_root)

    def _copy_management_scenario_pressure_bundle(self, repo_root: Path, candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1") -> None:
        destination = repo_root / "validation/private/source_zone_review"
        shutil.copytree(MANAGEMENT_SCENARIO_PRESSURE_BUNDLE_ROOT, destination, dirs_exist_ok=True)

    def _write_acquisition_package(
        self,
        repo_root: Path,
        *,
        classification: str | None = None,
        classification_map: dict[str, str] | None = None,
    ) -> Path:
        package_source = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
        package = yaml.safe_load(package_source.read_text(encoding="utf-8"))
        assert isinstance(package, dict)
        for row in package.get("required_acquisition_items") or []:
            if not isinstance(row, dict):
                continue
            category = str(row.get("category") or "")
            row_classification = (classification_map or {}).get(
                category,
                classification or str(row.get("classification") or row.get("current_status") or "missing"),
            )
            row["classification"] = row_classification
            row["current_status"] = row_classification
        package_path = repo_root / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package_path.write_text(yaml.safe_dump(package, sort_keys=False), encoding="utf-8")
        return package_path

    def _write_real_context_cache_manifest(
        self,
        repo_root: Path,
        *,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
        candidate_site_name: str = "Chant Sura / Flüelapass portability example",
        provenance_classification: str = "real_staged",
    ) -> None:
        manifest_path = repo_root / f"data/processed/swisstopo/{candidate_site_id}/input/public_geodata_cache_manifest.yaml"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        context_root = repo_root / f"data/processed/swisstopo/{candidate_site_id}/context"
        records = []
        product_ids = [
            "swissimage_context",
            "swisstlm3d_context",
            "swisssurface3d_context",
            "swisssurface3d_raster_context",
            "swissbuildings3d_context",
        ]
        for index, product_id in enumerate(product_ids, start=1):
            staged_path = manifest_path.parent / f"{product_id}.bin"
            metadata_path = manifest_path.parent / f"{product_id}.yaml"
            payload = f"expected-{product_id}".encode("utf-8")
            staged_path.write_bytes(payload)
            metadata = {
                "source_product_id": product_id,
                "source_product_name": product_id.replace("_", " "),
                "source_url_or_download_record": f"https://example.invalid/{product_id}",
                "product_version_or_date": "2026-05-17",
                "tile_id_or_delivery_identifier": f"tile-{index}",
                "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                "crs": "EPSG:2056",
                "resolution_m": 1.0,
                "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                "license_or_terms_reference": "example terms",
            }
            metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
            product_root = context_root / product_id.replace("_context", "")
            product_root.mkdir(parents=True, exist_ok=True)
            (product_root / "payload.bin").write_bytes(payload)
            if product_id == "swisstlm3d_context":
                (product_root / "metadata.json").write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
            records.append(
                {
                    "product_id": product_id,
                    "source_product_id": product_id,
                    "source_product_name": product_id.replace("_", " "),
                    "source_url_or_download_record": f"https://example.invalid/{product_id}",
                    "product_version_or_date": "2026-05-17",
                    "tile_id_or_delivery_identifier": f"tile-{index}",
                    "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                    "crs": "EPSG:2056",
                    "resolution_m": 1.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "example terms",
                    "provenance_classification": provenance_classification,
                    "staged_path": str(staged_path),
                    "metadata_path": str(metadata_path),
                }
            )
        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name,
            "products": records,
        }
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    def _copy_repo_file(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

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

    def _write_two_candidate_review_package(self, repo_root: Path) -> Path:
        workdir = repo_root / "review_package"
        workdir.mkdir(parents=True, exist_ok=True)
        polygon_path = workdir / "review_candidates.geojson"
        mask_path = workdir / "review_candidates_mask.asc"
        csv_path = workdir / "review_candidates.csv"
        manifest_path = workdir / "review_package_emitted.json"
        features = [
            self._candidate_feature("cand_accept_a", 2600000.0, 1200000.0, 2.0),
            self._candidate_feature("cand_rejected", 2600010.0, 1200010.0, 2.0),
            self._candidate_feature("cand_accept_b", 2600020.0, 1200020.0, 2.0),
        ]
        polygon_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "type": "FeatureCollection",
                    "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                    "candidate_site_name": "Chant Sura / Fluelapass portability example",
                    "source_zone_id": "chant_sura_reviewed_source_zone",
                    "candidate_generation_label": "heuristic_candidate_generation_only",
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": [
                        {
                            "provenance_label": "workflow_generated",
                            "meaning": "Candidate generated from workflow terrain and context screening only.",
                        },
                        {
                            "provenance_label": "field_supported",
                            "meaning": "Candidate can only be treated as field-supported once review has explicitly accepted it.",
                        },
                        {
                            "provenance_label": "mixed_provenance",
                            "meaning": "Candidate combines workflow generation with accepted field support.",
                        },
                        {
                            "provenance_label": "blocked_missing_provenance",
                            "meaning": "Candidate cannot be treated as evidence because provenance is missing or overclaimed.",
                        },
                    ],
                    "features": features,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        mask_path.write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
        csv_path.write_text("candidate_release_zone_id\n", encoding="utf-8")
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": "terrain_release_zone_candidate_review_package_v1",
                    "review_package_status": "review_applied",
                    "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
                    "candidate_site_name": "Chant Sura / Fluelapass portability example",
                    "source_zone_id": "chant_sura_reviewed_source_zone",
                    "candidate_release_zone_set_status": "review_ready",
                    "candidate_release_zone_ids": [feature["properties"]["candidate_release_zone_id"] for feature in features],
                    "review_decision_options": ["accepted", "rejected", "needs_field_review"],
                    "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
                    "provenance_label_legend": [
                        {
                            "provenance_label": "workflow_generated",
                            "meaning": "Candidate generated from workflow terrain and context screening only.",
                        },
                        {
                            "provenance_label": "field_supported",
                            "meaning": "Candidate can only be treated as field-supported once review has explicitly accepted it.",
                        },
                        {
                            "provenance_label": "mixed_provenance",
                            "meaning": "Candidate combines workflow generation with accepted field support.",
                        },
                        {
                            "provenance_label": "blocked_missing_provenance",
                            "meaning": "Candidate cannot be treated as evidence because provenance is missing or overclaimed.",
                        },
                    ],
                    "review_application": {
                        "validation_status": "validated",
                        "accepted_candidate_ids": ["cand_accept_a", "cand_accept_b"],
                    },
                    "review_summary": {
                        "review_row_count": len(features),
                        "candidate_count": len(features),
                        "review_decision_counts": {"accepted": 0, "rejected": 0, "needs_field_review": len(features)},
                        "provenance_label_counts": {
                            "workflow_generated": len(features),
                            "field_supported": 0,
                            "mixed_provenance": 0,
                            "blocked_missing_provenance": 0,
                        },
                        "default_review_decision": "needs_field_review",
                    },
                    "candidate_review_rows": [feature["properties"] for feature in features],
                    "candidate_sensitivity_summary": {},
                    "candidate_footprint_comparison": {},
                    "frozen_source_zone_footprint": {},
                    "claim_boundaries": {
                        "heuristic_workflow_input_only": True,
                        "validated_release_zone_evidence": False,
                        "field_validation_claims_allowed": False,
                        "physical_release_probability_claims_allowed": False,
                        "scale_up_authorized": False,
                        "operational_claims_allowed": False,
                        "notes": [
                            "candidate review rows remain workflow review inputs until the source zone is frozen",
                            "accepted, rejected, and needs_field_review are editable review states, not evidence claims",
                        ],
                    },
                    "outputs": {
                        "polygon": str(polygon_path),
                        "mask": str(mask_path),
                        "csv": str(csv_path),
                        "manifest": str(manifest_path),
                    },
                    "output_root": str(workdir),
                    "repo_root": str(repo_root),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def _candidate_feature(self, candidate_id: str, xmin: float, ymin: float, size: float) -> dict[str, object]:
        return {
            "type": "Feature",
            "id": candidate_id,
            "properties": {
                "candidate_release_zone_id": candidate_id,
                "review_decision": "accepted" if candidate_id != "cand_rejected" else "rejected",
                "accepted": candidate_id != "cand_rejected",
                "rejected": candidate_id == "cand_rejected",
                "needs_field_review": False,
                "candidate_generation_label": "heuristic_candidate_generation_only",
                "candidate_sensitivity_label": "heuristic_sensitive_across_bounded_heuristics",
                "release_cell_count": 1,
                "release_cell_ids": [f"{candidate_id}__cell_000"],
                "provenance_label": "workflow_generated",
                "component_bbox_lv95_m": {
                    "crs": "EPSG:2056",
                    "xmin": xmin,
                    "ymin": ymin,
                    "xmax": xmin + size,
                    "ymax": ymin + size,
                },
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [xmin, ymin],
                        [xmin + size, ymin],
                        [xmin + size, ymin + size],
                        [xmin, ymin + size],
                        [xmin, ymin],
                    ]
                ],
            },
        }

    def _write_multi_zone_smoke_case(
        self,
        *,
        repo_root: Path,
        source_zone_metadata_path: Path,
        scenario_table_path: Path,
    ) -> Path:
        case_path = repo_root / "multi_zone_probabilistic_phase1_smoke.yaml"
        case = yaml.safe_load((ROOT / "validation/cases/probabilistic_phase1_smoke.yaml").read_text(encoding="utf-8"))
        case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
        return case_path

    def _write_ready_prepared_pilot_report(self, repo_root: Path) -> Path:
        path = repo_root / "prepared_pilot_report.yaml"
        payload = {
            "schema_version": "aoi_to_prepared_pilot_dry_run_v1",
            "workflow_status": "ready_for_local_smoke",
            "prepared_pilot_compiler": {
                "classification": "ready_for_local_smoke",
                "execution_hints": {
                    "local": {"status": "ready_for_local_smoke"},
                },
                "first_blocker": {
                    "step_id": "none",
                    "blocked_reason": "",
                    "missing_inputs": [],
                },
            },
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def _write_real_public_context_bundles(
        self,
        repo_root: Path,
        *,
        candidate_site_id: str = "chant_sura_fluelapass_portability_example_v1",
    ) -> None:
        context_root = repo_root / f"data/processed/swisstopo/{candidate_site_id}/context"
        for product_id in [
            "swissimage_context",
            "swisstlm3d_context",
            "swisssurface3d_context",
            "swisssurface3d_raster_context",
            "swissbuildings3d_context",
        ]:
            product_root = context_root / product_id
            product_root.mkdir(parents=True, exist_ok=True)
            (product_root / "payload.bin").write_bytes(f"payload-{product_id}".encode("utf-8"))
            if product_id == "swisstlm3d_context":
                (product_root / "metadata.json").write_text(
                    yaml.safe_dump(
                        {
                            "schema_version": 1,
                            "source_product_id": product_id,
                            "source_product_name": "swissTLM3D",
                            "source_url_or_download_record": "https://example.invalid/swisstlm3d",
                            "product_version_or_date": "2026-05-17",
                            "tile_id_or_delivery_identifier": "tile-1",
                            "checksum_sha256": hashlib.sha256(f"payload-{product_id}".encode("utf-8")).hexdigest(),
                            "crs": "EPSG:2056",
                            "resolution_m": 1.0,
                            "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                            "license_or_terms_reference": "example terms",
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

    def _write_real_core_inputs(self, repo_root: Path, *, categories: set[str]) -> None:
        base = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1"
        (base / "input").mkdir(parents=True, exist_ok=True)
        (repo_root / "validation/policies").mkdir(parents=True, exist_ok=True)
        if "terrain_crop" in categories:
            (base / "input/terrain.asc").write_text(
                "\n".join(
                    [
                        "ncols 4",
                        "nrows 4",
                        "xllcorner 2793000.0",
                        "yllcorner 1180200.0",
                        "cellsize 2.0",
                        "NODATA_value -9999",
                        "2475.0 2475.5 2476.0 2476.5",
                        "2474.0 2474.5 2475.0 2475.5",
                        "2473.0 2473.5 2474.0 2474.5",
                        "2472.0 2472.5 2473.0 2473.5",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        if "terrain_metadata" in categories:
            (base / "input/terrain_metadata.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "tile_id": "chant_sura_fluelapass_real_lv95_crop",
                        "source_dataset": "real_chant_sura_fluelapass_core_input",
                        "source_product": "swissALTI3D",
                        "source_url": "https://example.invalid/chant_sura_fluelapass/swissalti3d",
                        "source_filename": "chant_sura_fluelapass_real_core_input.asc",
                        "source_file_present": True,
                        "download_status": "processed_real",
                        "license": "real staged input for repository tests; classifier-safe content only",
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                            "coordinate_unit": "m",
                            "height_unit": "m",
                        },
                        "raster": {
                            "format": "ESRI ASCII GRID",
                            "resolution_m": 2.0,
                            "width_px": 4,
                            "height_px": 4,
                            "nodata": -9999.0,
                        },
                        "extent_lv95_m": {
                            "xmin": 2793000.0,
                            "ymin": 1180200.0,
                            "xmax": 2793008.0,
                            "ymax": 1180208.0,
                        },
                        "preprocessing": {
                            "status": "staged_real",
                            "crop_extent_lv95_m": {
                                "xmin": 2793000.0,
                                "ymin": 1180200.0,
                                "xmax": 2793008.0,
                                "ymax": 1180208.0,
                            },
                            "resampling_method": "none",
                            "raw_sha256": None,
                            "processed_sha256": None,
                            "tool": "manual test input",
                            "processed_utc": None,
                        },
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
                            "notes": [
                                "Real-looking DEM values staged for dry-run coverage.",
                                "No classifier-trigger words are present in this file.",
                            ],
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "aoi_tile_catalog" in categories:
            (base / "input/aoi_tile_catalog.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "swisstopo_aoi_tile_catalog_v1",
                        "catalog_status": "ready",
                        "source_product": "swissALTI3D",
                        "product_id": "swissalti3d_2m",
                        "crs": "EPSG:2056",
                        "resolution_m": 2,
                        "tiles": [
                            {
                                "tile_id": "2793-1180",
                                "source_product": "swissALTI3D",
                                "source_url": "https://www.swisstopo.admin.ch/en/height-model-swissalti3d",
                                "extent_lv95_m": {
                                    "xmin": 2793000.0,
                                    "ymin": 1180000.0,
                                    "xmax": 2794000.0,
                                    "ymax": 1181000.0,
                                },
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "source_zone_metadata" in categories:
            (base / "input/source_zone_metadata.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "zone_id": "chant_sura_fluelapass_real_zone_001",
                        "source_zone_id": "chant_sura_fluelapass_real_zone_001",
                        "crs_epsg": 2056,
                        "vertical_datum": "LN02",
                        "release_sampling_policy": {
                            "source_zone_id_pattern": "chant_sura_fluelapass_real_*",
                            "source_zone_geometry": "LV95 polygon",
                            "release_point_table": "one row per release point",
                            "block_scenario_table": "CSV table with one row per block / scenario record",
                            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
                        },
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                        },
                        "geometry": {
                            "type": "polygon",
                            "coordinates": [
                                [2793001.0, 1180201.0],
                                [2793006.0, 1180201.0],
                                [2793006.0, 1180206.0],
                                [2793001.0, 1180206.0],
                            ],
                        },
                        "release_points": [
                            {
                                "release_point_id": "chant_sura_fluelapass_real_release_001",
                                "x": 2793002.0,
                                "y": 1180202.0,
                                "z_offset_m": 0.05,
                                "notes": "real staged test input",
                            }
                        ],
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
                            "source": "unit test",
                            "license": "real staged input for repository tests",
                            "notes": [
                                "Real-looking source-zone geometry staged for dry-run coverage.",
                                "No classifier-trigger words are present in this file.",
                            ],
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        if "scenario_table" in categories:
            (base / "input/scenario_table.csv").write_text(
                "\n".join(
                    [
                        "scenario_id,source_zone_id,block_family,relative_weight,probability_semantics,release_point_id",
                        "chant_sura_fluelapass_real_scenario_001,chant_sura_fluelapass_real_zone_001,real_block_family,1.0,normalized within a block family; no annual frequency claim,chant_sura_fluelapass_real_release_001",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        if "source_scenario_policy" in categories:
            (repo_root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "policy_id": "chant_sura_fluelapass_real_source_scenario_policy_v1",
                        "site_id": "chant_sura_fluelapass_portability_example_v1",
                        "source_zone_id_pattern": "chant_sura_fluelapass_real_*",
                        "source_zone_geometry": "LV95 polygon",
                        "release_point_table": "one row per release point",
                        "block_scenario_table": "CSV table with one row per block / scenario record",
                        "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

    def _rewrite_strings(self, payload: object, source: str, target: str) -> object:
        if isinstance(payload, str):
            return payload.replace(source, target)
        if isinstance(payload, list):
            return [self._rewrite_strings(item, source, target) for item in payload]
        if isinstance(payload, dict):
            return {key: self._rewrite_strings(value, source, target) for key, value in payload.items()}
        return payload


if __name__ == "__main__":
    unittest.main()
