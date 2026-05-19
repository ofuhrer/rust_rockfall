from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_chant_sura_real_context_readiness_gate.py"
PREFLIGHT_SCRIPT_PATH = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"
POST_RUN_GATE_SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_post_run_interpretation_gate.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gate = _load_module(SCRIPT_PATH, "check_chant_sura_real_context_readiness_gate")
preflight = _load_module(PREFLIGHT_SCRIPT_PATH, "check_second_site_public_geodata_preflight_for_real_context_gate_test")
staging = _load_module(STAGING_SCRIPT_PATH, "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_real_context_gate_test")
post_run_gate = _load_module(POST_RUN_GATE_SCRIPT_PATH, "summarize_balfrin_post_run_interpretation_gate_for_real_context_gate_test")


class ChantSuraRealContextReadinessGateTests(unittest.TestCase):
    def test_acquisition_package_freeze_separates_required_roots_and_fixture_only_paths(self) -> None:
        freeze_report = yaml.safe_load(self._freeze_package_path().read_text(encoding="utf-8"))

        self.assertEqual(
            freeze_report["schema_version"],
            "chant_sura_fluelapass_public_context_acquisition_package_v1",
        )
        self.assertEqual(freeze_report["freeze_status"], "blocked_missing_inputs")
        self.assertEqual(
            freeze_report["classification_taxonomy"],
            ["real_staged", "fixture_backed", "missing", "deferred"],
        )
        self.assertEqual(freeze_report["status_summary"]["real_staged_count"], 0)
        self.assertEqual(freeze_report["status_summary"]["fixture_backed_count"], 5)
        self.assertEqual(freeze_report["status_summary"]["missing_count"], 7)
        self.assertEqual(freeze_report["status_summary"]["deferred_count"], 5)

        required_rows = {entry["category"]: entry for entry in freeze_report["required_acquisition_items"]}
        self.assertEqual(required_rows["terrain_crop"]["classification"], "missing")
        self.assertEqual(required_rows["terrain_metadata"]["classification"], "missing")
        self.assertEqual(required_rows["aoi_tile_catalog"]["classification"], "missing")
        self.assertEqual(required_rows["swissimage_context"]["classification"], "deferred")
        self.assertEqual(required_rows["swisstlm3d_context"]["classification"], "deferred")
        self.assertEqual(required_rows["swisstlm3d_metadata"]["classification"], "deferred")
        self.assertEqual(required_rows["swisssurface3d_context"]["classification"], "deferred")
        self.assertEqual(required_rows["swisssurface3d_raster_context"]["classification"], "deferred")
        self.assertEqual(required_rows["swissbuildings3d_context"]["classification"], "deferred")
        self.assertEqual(required_rows["source_zone_metadata"]["classification"], "missing")
        self.assertEqual(required_rows["scenario_table"]["classification"], "missing")
        self.assertEqual(required_rows["source_scenario_policy"]["classification"], "missing")
        self.assertTrue(
            all(entry["classification"] in {"missing", "deferred"} for entry in freeze_report["required_acquisition_items"])
        )
        self.assertEqual(
            [entry["classification"] for entry in freeze_report["expected_local_roots"]],
            ["missing", "missing", "missing", "missing"],
        )
        self.assertTrue(all(entry["classification"] == "fixture_backed" for entry in freeze_report["fixture_only_paths"]))
        self.assertEqual(
            [entry["classification"] for entry in freeze_report["optional_paths"]],
            ["deferred", "deferred"],
        )

    def test_clean_checkout_blocks_and_marks_public_context_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            package_path = self._write_acquisition_package(repo_root, classification="missing")
            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        core_readiness = report["real_context_product_readiness"]
        readiness = report["prepared_pilot_real_input_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_missing_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "missing")
        self.assertEqual(report["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(report["first_missing_real_input_classification"], "missing")
        self.assertTrue(str(report["first_missing_real_input_path"]).endswith("terrain.asc"))
        self.assertEqual(readiness["input_classification"], "missing")
        self.assertEqual(readiness["required_real_input_count"], 6)
        self.assertEqual(readiness["real_staged_real_input_count"], 0)
        self.assertEqual(readiness["fixture_backed_real_input_count"], 0)
        self.assertEqual(readiness["metadata_mismatch_real_input_count"], 0)
        self.assertEqual(readiness["missing_real_input_count"], 6)
        self.assertEqual(readiness["missing_row_count"], 0)
        self.assertEqual(readiness["missing_file_count"], 6)
        self.assertEqual(readiness["deferred_real_input_count"], 6)
        self.assertEqual(readiness["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(readiness["first_missing_real_input_classification"], "missing")
        self.assertTrue(str(readiness["first_missing_real_input_path"]).endswith("terrain.asc"))
        self.assertEqual(readiness["first_missing_real_input_missing_fields"], ["file_present", "non_empty"])
        self.assertEqual(report["real_context_staging_checklist_state"], "deferred")
        self.assertEqual(checklist["checklist_state"], "deferred")
        self.assertEqual(checklist["verified_product_count"], 0)
        self.assertEqual(checklist["missing_product_count"], 0)
        self.assertEqual(checklist["deferred_product_count"], 5)
        self.assertEqual(checklist["partially_staged_product_count"], 0)
        self.assertEqual(checklist["metadata_mismatch_product_count"], 0)
        self.assertEqual(checklist["claim_boundary_note"], gate.CHECKLIST_BOUNDARY_NOTE)
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["input_classification"], "missing")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_classification"], "missing")
        self.assertTrue(str(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_path"]).endswith("terrain.asc"))
        expected_manifest_path = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml"
        expected_verifier_command = (
            "PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py "
            f"--cache-manifest {expected_manifest_path} --format json"
        )
        self.assertEqual(checklist["cache_manifest_path"], str(expected_manifest_path))
        self.assertEqual(checklist["verifier_command"], expected_verifier_command)
        self.assertIn("verify_public_geodata_cache.py", checklist["verifier_command"])
        self.assertTrue(all(entry["classification"] == "deferred" for entry in checklist["products"]))
        self.assertTrue(all(entry["checklist_state"] == "deferred" for entry in checklist["products"]))
        self.assertEqual([entry["classification"] for entry in readiness["required_real_inputs"]], ["missing"] * 6)
        self.assertEqual([entry["classification"] for entry in readiness["deferred_public_context_inputs"]], ["deferred"] * 6)
        self.assertTrue(all(entry["readiness_impact"] for entry in checklist["products"]))

    def test_fixture_backed_minimal_inputs_block_second_site_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            package_path = self._write_acquisition_package(repo_root, classification="fixture_backed")

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        readiness = report["real_context_product_readiness"]
        prepared = report["prepared_pilot_real_input_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_fixture_backed_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "fixture_backed")
        self.assertEqual(report["first_missing_real_input_category"], "")
        self.assertEqual(report["first_missing_real_input_classification"], "")
        self.assertEqual(report["first_missing_real_input_path"], "")
        self.assertEqual(report["first_fixture_backed_real_input_category"], "terrain_crop")
        self.assertEqual(report["first_fixture_backed_real_input_classification"], "fixture_backed")
        self.assertTrue(str(report["first_fixture_backed_real_input_path"]).endswith("terrain.asc"))
        self.assertEqual(readiness["readiness_status"], "deferred")
        self.assertEqual(prepared["required_real_input_count"], 6)
        self.assertEqual(prepared["real_staged_real_input_count"], 0)
        self.assertEqual(prepared["fixture_backed_real_input_count"], 6)
        self.assertEqual(prepared["metadata_mismatch_real_input_count"], 0)
        self.assertEqual(prepared["missing_real_input_count"], 0)
        self.assertEqual(prepared["missing_row_count"], 0)
        self.assertEqual(prepared["missing_file_count"], 0)
        self.assertEqual(prepared["deferred_real_input_count"], 6)
        self.assertEqual(report["real_context_staging_checklist_state"], "deferred")
        self.assertEqual(checklist["checklist_state"], "deferred")
        self.assertEqual(checklist["verified_product_count"], 0)
        self.assertEqual(checklist["missing_product_count"], 0)
        self.assertEqual(checklist["deferred_product_count"], 5)
        self.assertEqual(prepared["input_classification"], "fixture_backed")
        self.assertEqual(prepared["first_missing_real_input_category"], "")
        self.assertEqual(prepared["first_missing_real_input_classification"], "")
        self.assertEqual(prepared["first_missing_real_input_path"], "")
        self.assertEqual(prepared["first_fixture_backed_real_input_category"], "terrain_crop")
        self.assertEqual(prepared["first_fixture_backed_real_input_classification"], "fixture_backed")
        self.assertTrue(str(prepared["first_fixture_backed_real_input_path"]).endswith("terrain.asc"))
        self.assertEqual(prepared["first_missing_non_synthetic_input"], {})
        row_states = {entry["category"]: entry["classification"] for entry in prepared["required_real_inputs"]}
        self.assertEqual(row_states["aoi_tile_catalog"], "fixture_backed")
        self.assertEqual(row_states["terrain_crop"], "fixture_backed")
        self.assertEqual(row_states["terrain_metadata"], "fixture_backed")
        self.assertEqual(row_states["source_zone_metadata"], "fixture_backed")
        self.assertEqual(row_states["scenario_table"], "fixture_backed")
        self.assertEqual(row_states["source_scenario_policy"], "fixture_backed")
        deferred_states = {entry["category"]: entry["classification"] for entry in prepared["deferred_public_context_inputs"]}
        self.assertEqual(deferred_states["swissimage_context"], "deferred")
        self.assertEqual(deferred_states["swisstlm3d_context"], "deferred")
        self.assertEqual(deferred_states["swisstlm3d_metadata"], "deferred")
        self.assertEqual(deferred_states["swisssurface3d_context"], "deferred")
        self.assertEqual(deferred_states["swisssurface3d_raster_context"], "deferred")
        self.assertEqual(deferred_states["swissbuildings3d_context"], "deferred")
        self.assertTrue(all(entry["checklist_state"] == "deferred" for entry in checklist["products"]))

    def test_partial_real_inputs_block_second_site_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            self._write_real_core_inputs(repo_root, {"terrain_crop"})
            package_path = self._write_acquisition_package(
                repo_root,
                classification_map={
                    "terrain_crop": "real_staged",
                    "terrain_metadata": "fixture_backed",
                    "aoi_tile_catalog": "fixture_backed",
                    "source_zone_metadata": "fixture_backed",
                    "scenario_table": "fixture_backed",
                    "source_scenario_policy": "fixture_backed",
                },
            )
            self._write_real_context_cache_manifest(
                repo_root,
                staged_categories={"swissimage_context", "swisstlm3d_context", "swisssurface3d_context"},
                mismatched_categories={"swisssurface3d_context"},
            )

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        readiness = report["real_context_product_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_partial_real_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "partial_real")
        self.assertEqual(report["first_missing_real_input_category"], "terrain_metadata")
        self.assertEqual(report["first_missing_real_input_classification"], "fixture_backed")
        self.assertTrue(str(report["first_missing_real_input_path"]).endswith("terrain_metadata.yaml"))
        self.assertEqual(report["first_missing_real_input_missing_fields"], [])
        self.assertEqual(report["first_fixture_backed_real_input_category"], "terrain_metadata")
        self.assertEqual(report["first_fixture_backed_real_input_classification"], "fixture_backed")
        self.assertTrue(str(report["first_fixture_backed_real_input_path"]).endswith("terrain_metadata.yaml"))
        self.assertEqual(readiness["readiness_status"], "metadata_mismatch")
        self.assertEqual(readiness["ready_product_count"], 8)
        self.assertEqual(readiness["missing_product_count"], 2)
        self.assertEqual(readiness["deferred_product_count"], 0)
        self.assertEqual(readiness["metadata_mismatch_product_count"], 1)
        self.assertEqual(report["real_context_staging_checklist_state"], "partially_staged")
        self.assertEqual(checklist["checklist_state"], "partially_staged")
        self.assertEqual(checklist["verified_product_count"], 2)
        self.assertEqual(checklist["missing_product_count"], 2)
        self.assertEqual(checklist["deferred_product_count"], 0)
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["input_classification"], "partial_real")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], "terrain_metadata")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_classification"], "fixture_backed")
        self.assertTrue(str(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_path"]).endswith("terrain_metadata.yaml"))
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_missing_fields"], [])
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_category"], "terrain_metadata")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_classification"], "fixture_backed")
        self.assertTrue(str(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_path"]).endswith("terrain_metadata.yaml"))
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_non_synthetic_input"]["category"], "terrain_metadata")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_non_synthetic_input"]["classification"], "fixture_backed")
        row_states = {
            entry["category"]: entry["classification"] for entry in report["prepared_pilot_real_input_readiness"]["required_real_inputs"]
        }
        self.assertEqual(row_states["terrain_crop"], "real_staged")
        self.assertEqual(row_states["terrain_metadata"], "fixture_backed")
        self.assertEqual(row_states["aoi_tile_catalog"], "fixture_backed")
        self.assertEqual(row_states["source_zone_metadata"], "fixture_backed")
        self.assertEqual(row_states["scenario_table"], "fixture_backed")
        self.assertEqual(row_states["source_scenario_policy"], "fixture_backed")

    def test_metadata_mismatch_real_inputs_block_second_site_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            self._write_real_core_inputs(
                repo_root,
                {"terrain_crop", "terrain_metadata", "aoi_tile_catalog", "source_zone_metadata", "scenario_table", "source_scenario_policy"},
            )
            self._corrupt_core_inputs_for_metadata_mismatch(repo_root)
            package_path = self._write_acquisition_package(
                repo_root,
                classification="real_staged",
            )

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        readiness = report["prepared_pilot_real_input_readiness"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_metadata_mismatch_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "metadata_mismatch")
        self.assertEqual(report["first_missing_real_input_category"], "terrain_crop")
        self.assertEqual(report["first_missing_real_input_classification"], "metadata_mismatch")
        self.assertTrue(str(report["first_missing_real_input_path"]).endswith("terrain.asc"))
        self.assertEqual(report["first_missing_real_input_missing_fields"], ["non_empty"])
        self.assertEqual(readiness["input_classification"], "metadata_mismatch")
        self.assertEqual(readiness["real_staged_real_input_count"], 0)
        self.assertEqual(readiness["fixture_backed_real_input_count"], 0)
        self.assertEqual(readiness["metadata_mismatch_real_input_count"], 6)
        self.assertEqual(readiness["missing_real_input_count"], 0)
        self.assertEqual(readiness["missing_row_count"], 0)
        self.assertEqual(readiness["missing_file_count"], 0)
        self.assertEqual(readiness["first_missing_non_synthetic_input"]["classification"], "metadata_mismatch")
        self.assertEqual(readiness["first_missing_non_synthetic_input"]["missing_reason"], "metadata_mismatch")
        self.assertTrue(str(readiness["first_missing_non_synthetic_input"]["expected_path"]).endswith("terrain.asc"))
        row_states = {entry["category"]: entry["classification"] for entry in readiness["required_real_inputs"]}
        self.assertEqual(row_states["terrain_crop"], "metadata_mismatch")
        self.assertEqual(row_states["terrain_metadata"], "metadata_mismatch")
        self.assertEqual(row_states["aoi_tile_catalog"], "metadata_mismatch")
        self.assertEqual(row_states["source_zone_metadata"], "metadata_mismatch")
        self.assertEqual(row_states["scenario_table"], "metadata_mismatch")
        self.assertEqual(row_states["source_scenario_policy"], "metadata_mismatch")

    def test_missing_row_is_reported_separately_from_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            package_path = self._write_acquisition_package(
                repo_root,
                classification="fixture_backed",
                omit_categories={"source_scenario_policy"},
            )

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        readiness = report["prepared_pilot_real_input_readiness"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_missing_inputs")
        self.assertEqual(report["prepared_pilot_input_classification"], "missing")
        self.assertEqual(report["first_missing_real_input_category"], "source_scenario_policy")
        self.assertEqual(report["first_missing_real_input_classification"], "missing")
        self.assertTrue(
            str(report["first_missing_real_input_path"]).endswith(
                "chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml"
            )
        )
        self.assertEqual(
            report["first_missing_real_input_missing_fields"],
            [
                "policy_id",
                "site_id",
                "source_zone_id_pattern",
                "source_zone_geometry",
                "release_point_table",
                "block_scenario_table",
                "scenario_probability_semantics",
            ],
        )
        self.assertEqual(readiness["missing_row_count"], 1)
        self.assertEqual(readiness["missing_file_count"], 0)
        self.assertEqual(readiness["missing_real_input_count"], 1)
        self.assertEqual(readiness["first_missing_non_synthetic_input"]["classification"], "missing")
        self.assertEqual(readiness["first_missing_non_synthetic_input"]["missing_reason"], "missing_row")
        self.assertTrue(
            str(readiness["first_missing_non_synthetic_input"]["expected_path"]).endswith(
                "chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml"
            )
        )
        row_states = {entry["category"]: entry["classification"] for entry in readiness["required_real_inputs"]}
        self.assertEqual(row_states["source_scenario_policy"], "missing")

    def test_ready_real_inputs_allow_second_site_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            self._write_real_core_inputs(
                repo_root,
                {"terrain_crop", "terrain_metadata", "aoi_tile_catalog", "source_zone_metadata", "scenario_table", "source_scenario_policy"},
            )
            package_path = self._write_acquisition_package(
                repo_root,
                classification="real_staged",
            )
            self._write_real_context_cache_manifest(
                repo_root,
                staged_categories={
                    "swissimage_context",
                    "swisstlm3d_context",
                    "swisssurface3d_context",
                    "swisssurface3d_raster_context",
                    "swissbuildings3d_context",
                },
            )

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        readiness = report["real_context_product_readiness"]
        self.assertEqual(report["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["readiness_status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["prepared_pilot_input_classification"], "ready_real")
        self.assertEqual(report["first_missing_real_input_category"], "")
        self.assertEqual(report["first_missing_real_input_classification"], "")
        self.assertEqual(report["first_missing_real_input_path"], "")
        self.assertEqual(report["first_missing_real_input_missing_fields"], [])
        self.assertEqual(report["first_fixture_backed_real_input_category"], "")
        self.assertEqual(report["first_fixture_backed_real_input_classification"], "")
        self.assertEqual(report["first_fixture_backed_real_input_path"], "")
        self.assertEqual(readiness["readiness_status"], "ready")
        self.assertEqual(readiness["ready_product_count"], 11)
        self.assertEqual(readiness["missing_product_count"], 0)
        self.assertEqual(readiness["deferred_product_count"], 0)
        self.assertEqual(readiness["metadata_mismatch_product_count"], 0)
        self.assertEqual(report["real_context_staging_checklist_state"], "verifier_ready")
        self.assertEqual(report["core_input_status"], "ready")
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
        self.assertFalse(report["synthetic_core_inputs_are_public_context_evidence"])
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["input_classification"], "ready_real")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], "")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_classification"], "")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_path"], "")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_missing_fields"], [])
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_non_synthetic_input"], {})
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_category"], "")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_classification"], "")
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_fixture_backed_real_input_path"], "")
        self.assertEqual(report["real_input_acquisition_handoff"]["next_action_recommendation"], "ready_no_handoff_needed")
        self.assertEqual(report["real_input_acquisition_handoff"]["authorization_or_defer_status"], "no_action_needed")
        self.assertEqual(report["real_input_acquisition_handoff"]["first_missing_real_input_category"], "")
        self.assertEqual(report["real_input_acquisition_handoff"]["expected_source_product"], "")
        self.assertEqual(report["real_input_acquisition_handoff"]["expected_local_path"], "")
        self.assertEqual(report["real_input_acquisition_handoff"]["metadata_contract"], [])
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(checklist["verification_fields"], report["public_geodata_workflow_contract"]["public_geodata_cache_contract"]["verification_fields"])
        self.assertTrue(checklist["products"][0]["expected_staging_root"].endswith("/context/swissimage"))
        self.assertEqual(
            checklist["products"][0]["readiness_impact"],
            "staged files and metadata are ready for deterministic cache verification",
        )
        self.assertTrue(all(entry["classification"] == "ready" for entry in readiness["products"]))
        self.assertEqual(report["public_geodata_workflow_contract"]["public_geodata_contract_readiness_status"], "ready")
        self.assertEqual(report["public_geodata_workflow_contract"]["synthetic_fixture_readiness_status"], "not_applicable")
        self.assertIn("swissALTI3D", report["public_geodata_workflow_contract"]["swisstopo_product_classes"][0]["products"])

        ready_core_inputs = {entry["category"]: entry for entry in report["local_core_inputs"]}
        self.assertEqual(
            set(ready_core_inputs),
            {
                "aoi_tile_catalog",
                "terrain_crop",
                "terrain_crs_vertical_datum",
                "source_zone_metadata",
                "scenario_table",
                "source_scenario_policy",
            },
        )
        self.assertTrue(all(entry["status"] == "ready" for entry in ready_core_inputs.values()))
        self.assertTrue(all(entry["filesystem_state"]["kind"] == "file" for entry in ready_core_inputs.values()))

        supporting_roots = {entry["category"]: entry for entry in report["supporting_local_roots"]}
        self.assertEqual(supporting_roots["processed_context_root"]["filesystem_state"]["kind"], "empty_directory")
        self.assertEqual(supporting_roots["validation_case_root"]["status"], "ready")
        self.assertEqual(supporting_roots["hazard_results_root"]["status"], "ready")

        acquisition_plan = {entry["category"]: entry for entry in report["deterministic_acquisition_plan"]}
        self.assertEqual(
            set(acquisition_plan),
            {
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            },
        )
        self.assertTrue(all(entry["current_status"] == "deferred_public_context" for entry in acquisition_plan.values()))
        self.assertTrue(
            all(
                entry["expected_staged_path"].startswith(
                    "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/"
                )
                for entry in acquisition_plan.values()
            )
        )

        next_decisions = {entry["category"]: entry for entry in report["next_acquisition_decisions"]}
        self.assertEqual(set(next_decisions), set(acquisition_plan))
        self.assertEqual(report["balfrin_trigger_summary"]["trigger_state"], "blocked_missing_inputs")
        self.assertTrue(all(entry["next_acquisition_decision"] == "hold_for_balfrin_evidence" for entry in next_decisions.values()))

        deferred_products = {entry["category"]: entry for entry in report["deferred_public_context_products"]}
        self.assertEqual(set(deferred_products), set(acquisition_plan))
        self.assertEqual(report["public_context_acquisition_summary"]["deferred_product_count"], 5)
        self.assertEqual(report["gate_boundary_summary"]["deferred_public_context_product_count"], 5)
        self.assertFalse(report["gate_boundary_summary"]["synthetic_core_inputs_are_public_context_evidence"])
        self.assertEqual(report["local_staged_summary"]["ready_core_input_count"], 6)
        self.assertEqual(report["local_staged_summary"]["ready_supporting_root_count"], 4)
        self.assertFalse(report["local_staged_summary"]["synthetic_core_inputs_are_public_context_evidence"])

    def test_missing_terrain_metadata_requests_local_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml").unlink()
            self._write_real_core_inputs(
                repo_root,
                {"terrain_crop", "aoi_tile_catalog", "source_zone_metadata", "scenario_table", "source_scenario_policy"},
            )
            package_path = self._write_acquisition_package(repo_root, classification="real_staged")

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        handoff = report["real_input_acquisition_handoff"]
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], "terrain_metadata")
        self.assertEqual(handoff["next_action_recommendation"], "stage_local_existing_input")
        self.assertEqual(handoff["authorization_or_defer_status"], "local_staging_needed")
        self.assertEqual(handoff["first_missing_real_input_category"], "terrain_metadata")
        self.assertEqual(handoff["first_missing_real_input_classification"], "missing")
        self.assertTrue(handoff["expected_local_path"].endswith("terrain_metadata.yaml"))
        self.assertEqual(handoff["expected_source_product"], "swissALTI3D terrain metadata")
        self.assertIn("crs", handoff["metadata_contract"])
        self.assertFalse(handoff["authorization_required"])

    def test_missing_aoi_tile_catalog_requests_local_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml").unlink()
            self._write_real_core_inputs(
                repo_root,
                {"terrain_crop", "terrain_metadata", "source_zone_metadata", "scenario_table", "source_scenario_policy"},
            )
            package_path = self._write_acquisition_package(repo_root, classification="real_staged")

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        handoff = report["real_input_acquisition_handoff"]
        self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], "aoi_tile_catalog")
        self.assertEqual(handoff["next_action_recommendation"], "stage_local_existing_input")
        self.assertEqual(handoff["authorization_or_defer_status"], "local_staging_needed")
        self.assertEqual(handoff["first_missing_real_input_category"], "aoi_tile_catalog")
        self.assertTrue(handoff["expected_local_path"].endswith("aoi_tile_catalog.yaml"))
        self.assertEqual(handoff["expected_source_product"], "AOI tile catalog for deterministic swisstopo discovery")
        self.assertIn("tile_id", handoff["metadata_contract"])
        self.assertFalse(handoff["authorization_required"])

    def test_missing_source_scenario_policy_records_request_local_staging(self) -> None:
        missing_cases = [
            ("source_zone_metadata", "source_zone_metadata.yaml", "release / source-zone metadata", "geometry"),
            ("scenario_table", "scenario_table.csv", "block / scenario table", "scenario_id"),
            (
                "source_scenario_policy",
                "chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml",
                "source-scenario policy record",
                "policy_id",
            ),
        ]

        for category, suffix, expected_source_product, field_name in missing_cases:
            with self.subTest(category=category):
                with tempfile.TemporaryDirectory() as tmp:
                    repo_root = Path(tmp)
                    self._stage_minimal_inputs(repo_root)
                    missing_path = {
                        "source_zone_metadata": repo_root
                        / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                        "scenario_table": repo_root
                        / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv",
                        "source_scenario_policy": repo_root
                        / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml",
                    }[category]
                    missing_path.unlink()
                    real_categories = {
                        "terrain_crop",
                        "terrain_metadata",
                        "aoi_tile_catalog",
                        "source_zone_metadata",
                        "scenario_table",
                        "source_scenario_policy",
                    }
                    real_categories.remove(category)
                    self._write_real_core_inputs(
                        repo_root,
                        real_categories,
                    )
                    package_path = self._write_acquisition_package(repo_root, classification="real_staged")

                    report = gate.build_report(
                        self._site_config_path(),
                        repo_root=repo_root,
                        acquisition_package_path=package_path,
                    )

                handoff = report["real_input_acquisition_handoff"]
                self.assertEqual(report["prepared_pilot_real_input_readiness"]["first_missing_real_input_category"], category)
                self.assertEqual(handoff["next_action_recommendation"], "stage_local_existing_input")
                self.assertEqual(handoff["authorization_or_defer_status"], "local_staging_needed")
                self.assertEqual(handoff["first_missing_real_input_category"], category)
                self.assertTrue(handoff["expected_local_path"].endswith(suffix))
                self.assertEqual(handoff["expected_source_product"], expected_source_product)
                self.assertIn(field_name, handoff["metadata_contract"])
                self.assertFalse(handoff["authorization_required"])

    def test_text_output_mentions_boundary_and_next_acquisition_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            self._write_real_core_inputs(
                repo_root,
                {"terrain_crop", "terrain_metadata", "aoi_tile_catalog", "source_zone_metadata", "scenario_table", "source_scenario_policy"},
            )
            package_path = self._write_acquisition_package(repo_root, classification="real_staged")
            self._write_real_context_cache_manifest(
                repo_root,
                staged_categories={
                    "swissimage_context",
                    "swisstlm3d_context",
                    "swisssurface3d_context",
                    "swisssurface3d_raster_context",
                    "swissbuildings3d_context",
                },
            )

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                acquisition_package_path=package_path,
            )

        text_report = gate.render_text_report(report)
        self.assertEqual(text_report, gate.render_text_report(report))
        self.assertIn("schema_version: chant_sura_real_context_readiness_gate_v1", text_report)
        self.assertIn("real_context_readiness_gate_status: ready_for_real_context_acquisition", text_report)
        self.assertIn("real_context_staging_checklist_state: verifier_ready", text_report)
        self.assertIn("prepared_pilot_input_classification: ready_real", text_report)
        self.assertIn("first_missing_real_input_category: ", text_report)
        self.assertIn("first_missing_real_input_classification: ", text_report)
        self.assertIn("first_missing_real_input_path: ", text_report)
        self.assertIn("real_input_acquisition_handoff:", text_report)
        self.assertIn("next_action_recommendation: ready_no_handoff_needed", text_report)
        self.assertIn("local_core_inputs:", text_report)
        self.assertIn("real_context_product_readiness:", text_report)
        self.assertIn("deterministic_acquisition_plan:", text_report)
        self.assertIn("public_geodata_workflow_contract:", text_report)
        self.assertIn("next_acquisition_decisions:", text_report)
        self.assertIn("real_context_product_readiness:", text_report)
        self.assertIn("real_context_staging_checklist:", text_report)
        self.assertIn("prepared_pilot_real_input_readiness:", text_report)
        self.assertIn("claim_boundary_note: Checklist only; it does not authorize downloads", text_report)
        self.assertIn("synthetic_core_inputs_are_public_context_evidence: false", text_report)
        self.assertIn("processed_context_root", text_report)
        self.assertIn("empty_directory", text_report)

    def test_balfrin_trigger_matrix_reports_proceed_defer_and_blocked_states(self) -> None:
        measured_report = post_run_gate.build_report(self._measured_balfrin_evidence())
        inconclusive_report = post_run_gate.build_report(self._inconclusive_balfrin_evidence())

        measured_matrix = gate.build_balfrin_trigger_matrix(measured_report)
        inconclusive_matrix = gate.build_balfrin_trigger_matrix(inconclusive_report)
        blocked_matrix = gate.build_balfrin_trigger_matrix(None)

        self.assertEqual(len(measured_matrix), 5)
        self.assertEqual({row["trigger_state"] for row in measured_matrix}, {"proceed"})
        self.assertEqual({row["next_acquisition_decision"] for row in measured_matrix}, {"proceed_real_context_staging"})
        self.assertEqual(
            [row["category"] for row in measured_matrix],
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
        )

        self.assertEqual({row["trigger_state"] for row in inconclusive_matrix}, {"defer"})
        self.assertEqual({row["next_acquisition_decision"] for row in inconclusive_matrix}, {"defer_real_context_staging"})

        self.assertEqual({row["trigger_state"] for row in blocked_matrix}, {"blocked_missing_inputs"})
        self.assertEqual({row["next_acquisition_decision"] for row in blocked_matrix}, {"hold_for_balfrin_evidence"})

    def test_build_report_includes_balfrin_trigger_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)

            report = gate.build_report(
                self._site_config_path(),
                repo_root=repo_root,
                balfrin_evidence_json=ROOT / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/balfrin_evidence_bundle_v1.json",
            )

        self.assertEqual(report["balfrin_trigger_summary"]["trigger_state"], "defer")
        self.assertEqual(report["balfrin_trigger_summary"]["proceed_product_count"], 0)
        self.assertEqual(report["balfrin_trigger_summary"]["defer_product_count"], 5)
        self.assertEqual(report["balfrin_trigger_summary"]["blocked_product_count"], 0)
        self.assertEqual(report["next_acquisition_decisions"][0]["balfrin_trigger_state"], "defer")
        self.assertEqual(report["next_acquisition_decisions"][0]["balfrin_next_decision"], "defer_real_context_staging")
        self.assertTrue(report["balfrin_evidence_path"].endswith("balfrin_evidence_bundle_v1.json"))

    def _stage_minimal_inputs(self, repo_root: Path) -> None:
        staging.stage_minimal_inputs(
            repo_root=repo_root,
            site_config=self._site_config_path(),
            fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
        )

    def _site_config_path(self) -> Path:
        return ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"

    def _freeze_package_path(self) -> Path:
        return ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"

    def _write_acquisition_package(
        self,
        repo_root: Path,
        *,
        classification: str | None = None,
        classification_map: dict[str, str] | None = None,
        omit_categories: set[str] | None = None,
    ) -> Path:
        package = yaml.safe_load(self._freeze_package_path().read_text(encoding="utf-8"))
        assert isinstance(package, dict)
        omit_categories = omit_categories or set()
        required_items = []
        for row in package.get("required_acquisition_items") or []:
            if not isinstance(row, dict):
                continue
            category = str(row.get("category") or "")
            if category in omit_categories:
                continue
            row_classification = (classification_map or {}).get(category, classification or str(row.get("classification") or row.get("current_status") or "missing"))
            row["classification"] = row_classification
            row["current_status"] = row_classification
            required_items.append(row)
        package["required_acquisition_items"] = required_items
        package_path = repo_root / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package_path.write_text(yaml.safe_dump(package, sort_keys=False), encoding="utf-8")
        return package_path

    def _write_real_context_cache_manifest(
        self,
        repo_root: Path,
        *,
        staged_categories: set[str],
        mismatched_categories: set[str] | None = None,
    ) -> Path:
        mismatched_categories = mismatched_categories or set()
        manifest_path = (
            repo_root
            / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml"
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        records = []
        for index, category in enumerate(
            [
                "swissimage_context",
                "swisstlm3d_context",
                "swisssurface3d_context",
                "swisssurface3d_raster_context",
                "swissbuildings3d_context",
            ],
            start=1,
        ):
            staged_path = manifest_path.parent / f"{category}.bin"
            metadata_path = manifest_path.parent / f"{category}.yaml"
            expected_bytes = f"expected-{category}".encode("utf-8")
            actual_bytes = expected_bytes if category in staged_categories and category not in mismatched_categories else None
            if category in staged_categories:
                staged_path.write_bytes(actual_bytes if actual_bytes is not None else f"actual-{category}".encode("utf-8"))
                metadata = {
                    "source_product_id": category,
                    "source_product_name": category.replace("_", " "),
                    "source_url": f"https://example.invalid/{category}",
                    "product_version": "2026-05-17",
                    "tile_id": f"tile-{index}",
                    "crs": "EPSG:2056",
                    "resolution_m": 1.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "example terms",
                }
                metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
                checksum_source = expected_bytes
            else:
                checksum_source = expected_bytes

            records.append(
                {
                    "product_id": category,
                    "source_product_id": category,
                    "source_product_name": category.replace("_", " "),
                    "source_url_or_download_record": f"https://example.invalid/{category}",
                    "product_version_or_date": "2026-05-17",
                    "tile_id_or_delivery_identifier": f"tile-{index}",
                    "checksum_sha256": hashlib.sha256(checksum_source).hexdigest(),
                    "crs": "EPSG:2056",
                    "resolution_m": 1.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "example terms",
                    "staged_path": str(staged_path),
                    "metadata_path": str(metadata_path),
                }
            )

        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "products": records,
        }
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        return manifest_path

    def _corrupt_core_inputs_for_metadata_mismatch(self, repo_root: Path) -> None:
        (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc").write_text(
            "",
            encoding="utf-8",
        )
        (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml").write_text(
            "schema_version: 1\n",
            encoding="utf-8",
        )
        (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml").write_text(
            "schema_version: swisstopo_aoi_tile_catalog_v1\ncatalog_status: metadata_only\n",
            encoding="utf-8",
        )
        (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml").write_text(
            "schema_version: 1\nzone_id: chant_sura_fluelapass_real_zone_001\n",
            encoding="utf-8",
        )
        (repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv").write_text(
            "scenario_id,source_zone_id\nbroken_scenario,broken_zone\n",
            encoding="utf-8",
        )
        (repo_root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml").write_text(
            "schema_version: 1\npolicy_id: broken_policy\n",
            encoding="utf-8",
        )

    def _write_real_core_inputs(self, repo_root: Path, categories: set[str]) -> None:
        base = repo_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1"
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
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                        },
                        "preprocessing": {
                            "status": "staged_real",
                            "crop_extent_lv95_m": {
                                "xmin": 2793000.0,
                                "ymin": 1180200.0,
                                "xmax": 2793008.0,
                                "ymax": 1180208.0,
                            },
                        },
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
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
                            }
                        ],
                        "provenance": {
                            "intended_use": "chant_sura_fluelapass_real_core_input_staging",
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

    def _measured_balfrin_evidence(self) -> dict[str, object]:
        return {
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_balfrin_single_release_zone_v1",
            "contract_path": "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml",
            "readiness_check": {
                "status": "ready_for_balfrin_single_release_zone_pilot",
                "summary": "Frozen Balfrin pilot contract and local inputs are ready.",
            },
            "convergence_stability_check": {
                "status": "measured",
                "summary": "Convergence and repeatability are measured.",
            },
            "output_check": {
                "status": "rebuildable_reduced_output",
                "summary": "The output footprint is bounded and reproducible.",
            },
            "gis_cog_check": {
                "status": "gis_package_ready",
                "summary": "GIS package and COG readiness are available.",
            },
            "physical_credibility_check": {
                "status": "not_established",
                "summary": "Physical credibility remains unestablished and is not used for physical-probability claims.",
            },
        }

    def _inconclusive_balfrin_evidence(self) -> dict[str, object]:
        evidence = self._measured_balfrin_evidence()
        evidence["convergence_stability_check"] = {
            "status": "inconclusive",
            "summary": "Convergence and repeatability remain conservative.",
        }
        evidence["output_check"] = {
            "status": "summary_only_not_rebuildable",
            "summary": "The output footprint is still inspectable but not fully bounded.",
        }
        evidence["gis_cog_check"] = {
            "status": "gis_package_ready_cog_blocked",
            "summary": "GIS packaging is present but COG readiness remains blocked.",
        }
        return evidence


if __name__ == "__main__":
    unittest.main()
