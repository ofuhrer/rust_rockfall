from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_release_plan_dry_run.py"
PREFLIGHT_SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


planner = _load_module(SCRIPT_PATH, "plan_release_plan_dry_run")
preflight = _load_module(PREFLIGHT_SCRIPT_PATH, "check_second_site_public_geodata_preflight_for_release_plan_test")
staging = _load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_release_plan_test")


class ReleasePlanDryRunTests(unittest.TestCase):
    def test_candidate_fixture_reports_deterministic_release_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=config_path,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )

            report = planner.build_report(config_path, repo_root=repo_root)

        self.assertEqual(report["release_plan_dry_run_status"], "deferred_public_context_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["candidate_site_name"], "Chant Sura / Flüelapass portability example")
        self.assertEqual(report["release_plan_summary"]["release_point_count"], 1)
        self.assertEqual(report["release_plan_summary"]["release_row_count"], 1)
        self.assertEqual(report["release_plan_summary"]["block_scenario_row_count"], 1)
        self.assertEqual(report["release_plan_summary"]["release_sampling_seed_policy"]["seed"], 34014)
        self.assertEqual(report["release_plan_summary"]["release_sampling_seed_policy"]["seed_policy"], "fixed_integer_recorded_before_simulation")
        self.assertEqual(report["deterministic_release_rows"][0]["release_point_id"], "chant_sura_fluelapass_fixture_release_001")
        self.assertEqual(report["deterministic_block_scenario_rows"][0]["scenario_id"], "chant_sura_fluelapass_fixture_scenario_001")

        reusable = report["reusable_semantics"]
        self.assertEqual(reusable["release_point_table_shape"], "one row per release point")
        self.assertEqual(reusable["block_scenario_table_shape"], "CSV table with one row per block / scenario record")
        self.assertEqual(reusable["scenario_probability_semantics"], "normalized within a block family; no annual frequency claim")

        site_specific = report["site_specific_inputs"]
        self.assertEqual(site_specific["source_zone_record"]["zone_id"], "chant_sura_fluelapass_fixture_zone_001")
        self.assertEqual(site_specific["source_zone_record"]["release_points"][0]["release_point_id"], "chant_sura_fluelapass_fixture_release_001")
        self.assertEqual(site_specific["scenario_table_rows"][0]["scenario_id"], "chant_sura_fluelapass_fixture_scenario_001")
        self.assertTrue(site_specific["expected_paths"]["source_zone_metadata"].endswith("source_zone_metadata.yaml"))

        heuristics = report["tschamut_only_heuristics"]
        self.assertEqual(heuristics["release_sampling_seed_policy"]["release_cell_id_prefix"], "tschamut_public_release_cell")
        self.assertEqual(heuristics["release_sampling_seed_policy"]["requested_release_cell_count"], 10)
        self.assertEqual(len(heuristics["reference_block_scenario_classes"]), 3)
        self.assertEqual(heuristics["reference_block_scenario_classes"][0]["block_scenario_id"], "tschamut_public_block_small")

        distinction = report["machine_readable_distinction"]
        self.assertIn("release_point_table_shape", distinction["reusable_semantics"])
        self.assertIn("source_zone_record", distinction["site_specific_inputs"])
        self.assertIn("reference_block_scenario_classes", distinction["tschamut_only_heuristics"])

        blocked_template = report["blocked_second_site_execution_template"]
        self.assertEqual(blocked_template["status"], "template_only")
        self.assertIn("generate_second_site_release_plan.py", blocked_template["command"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

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
        self.assertIn("schema_version: release_plan_dry_run_v1", text_report)
        self.assertIn("release_plan_summary:", text_report)
        self.assertIn("tschamut_only_heuristics:", text_report)
        self.assertIn("deterministic_release_rows:", text_report)
        self.assertIn("deterministic_block_scenario_rows:", text_report)

    def _write_site_config(self, root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
