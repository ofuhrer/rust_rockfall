from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

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
staging = _load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_aoi_to_prepared_pilot_test")


class AoiToPreparedPilotDryRunTests(unittest.TestCase):
    def test_candidate_fixture_reports_an_ordered_deferred_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = planner.build_report(config_path, repo_root=repo_root)

        self.assertEqual(report["schema_version"], "aoi_to_prepared_pilot_dry_run_v1")
        self.assertEqual(report["workflow_status"], "deferred_public_context_inputs")
        self.assertEqual(
            report["step_order"],
            [
                "aoi_acquisition",
                "public_context_gate",
                "release_zone_heuristic_dry_run",
                "release_plan_dry_run",
                "prepared_pilot_command_plan",
            ],
        )
        self.assertEqual(report["workflow_steps"][0]["status"], "deferred_public_context_inputs")
        self.assertEqual(report["workflow_steps"][1]["status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["workflow_steps"][2]["status"], "deferred_public_context_inputs")
        self.assertEqual(report["workflow_steps"][3]["status"], "deferred_public_context_inputs")
        self.assertEqual(report["workflow_steps"][4]["status"], "deferred_public_context_inputs")

        acquisition_step = report["workflow_steps"][0]
        self.assertEqual(
            [Path(path).name for path in acquisition_step["generated_output_roots"]],
            ["swissimage", "swisstlm3d", "swisssurface3d", "swisssurface3d_raster", "swissbuildings3d"],
        )
        self.assertTrue(
            any(path.endswith("validation/private/chant_sura_fluelapass_portability_example_v1") for path in report["workflow_ignored_output_roots"])
        )
        self.assertTrue(
            any(path.endswith("hazard/results/chant_sura_fluelapass_portability_example_v1") for path in report["workflow_ignored_output_roots"])
        )
        self.assertTrue(
            any(
                path.endswith("data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml")
                for path in report["expected_inputs_by_step"]["release_zone_heuristic_dry_run"]
            )
        )
        self.assertTrue(
            any(
                path.endswith("data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv")
                for path in report["expected_inputs_by_step"]["release_zone_heuristic_dry_run"]
            )
        )
        self.assertTrue(
            any(
                path.endswith("validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml")
                for path in report["expected_inputs_by_step"]["release_plan_dry_run"]
            )
        )
        self.assertIn("second_site_release_plan_execution_template", report["command_plan_report"]["blocked_template_commands"])
        self.assertIn("validation/private/chant_sura_fluelapass_portability_example_v1", report["command_plan_report"]["ignored_output_paths"])
        self.assertGreaterEqual(report["workflow_blocker_count"], 4)

        text_report = planner.render_text_report(report)
        self.assertIn("schema_version: aoi_to_prepared_pilot_dry_run_v1", text_report)
        self.assertIn("workflow_status: deferred_public_context_inputs", text_report)
        self.assertIn("prepared_pilot_command_plan", text_report)

    def test_main_composes_stubbed_helper_reports_without_execution(self) -> None:
        acquisition_report = {
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "candidate_selection_rationale": "metadata-only candidate",
            "site_extent": {"crs": "EPSG:2056", "xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
            "acquisition_boundary_status": "deferred_public_context_inputs",
            "acquisition_manifest_path": "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            "public_context_acquisition_summary": {
                "expected_staging_roots": [
                    "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage",
                ]
            },
            "required_public_geodata_products": [
                {"expected_staged_path": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"},
            ],
            "required_metadata_records": [
                {"path_or_pattern": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"},
            ],
            "acquisition_manifest_expected_ignored_roots": [
                "validation/private/chant_sura_fluelapass_portability_example_v1",
            ],
            "deferred_public_context_categories": ["swissimage_context"],
        }
        real_context_report = {
            "real_context_readiness_gate_status": "deferred_public_context_inputs",
            "blocked_reason": "public-context products are intentionally deferred",
            "local_core_inputs": [
                {"expected_path": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"},
            ],
            "supporting_local_roots": [
                {"expected_path": "validation/private/chant_sura_fluelapass_portability_example_v1"},
            ],
            "deferred_public_context_categories": ["swissimage_context"],
            "claim_boundaries": {"scale_up_authorized": False, "operational_claims_allowed": False},
        }
        release_zone_report = {
            "heuristic_dry_run_status": "deferred_public_context_inputs",
            "blocked_reason": "no candidate release-zone set is claimed",
            "heuristic_inputs": [
                {"path_or_pattern": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"},
            ],
            "blocked_missing_products": [{"category": "swissimage_context"}],
        }
        release_plan_report = {
            "release_plan_dry_run_status": "deferred_public_context_inputs",
            "blocked_reason": "public-context products are intentionally deferred",
            "site_specific_inputs": {
                "expected_paths": {
                    "source_zone_metadata": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                    "scenario_table": "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv",
                    "source_scenario_policy": "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml",
                }
            },
            "blocked_second_site_execution_template": {
                "expected_outputs": [
                    "validation/private/chant_sura_fluelapass_portability_example_v1/release_plan_case.yaml",
                    "validation/private/chant_sura_fluelapass_portability_example_v1/release_plan_manifest.json",
                ]
            },
        }
        command_plan_report = {
            "second_site_portability_status": "deferred_public_context_inputs",
            "blocked_template_commands": ["second_site_release_plan_execution_template"],
            "ignored_output_paths": [
                "validation/private/chant_sura_fluelapass_portability_example_v1",
                "hazard/results/chant_sura_fluelapass_portability_example_v1",
            ],
            "commands": [
                {"expected_inputs": ["tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"]},
            ],
        }

        with patch.object(planner.AOI_ACQUISITION, "build_report", return_value=acquisition_report), patch.object(
            planner.REAL_CONTEXT_GATE, "build_report", return_value=real_context_report
        ), patch.object(planner.RELEASE_ZONE, "build_report", return_value=release_zone_report), patch.object(
            planner.RELEASE_PLAN, "build_report", return_value=release_plan_report
        ), patch.object(planner.COMMAND_PLAN, "build_report", return_value=command_plan_report):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = planner.main(["--format", "json"])

        self.assertEqual(exit_code, 2)
        rendered = json.loads(buffer.getvalue())
        self.assertEqual(rendered["workflow_status"], "deferred_public_context_inputs")
        self.assertEqual(rendered["step_order"][0], "aoi_acquisition")
        self.assertIn("prepared_pilot_command_plan", rendered["step_order"])
        self.assertIn("validation/private/chant_sura_fluelapass_portability_example_v1", rendered["workflow_ignored_output_roots"])

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
