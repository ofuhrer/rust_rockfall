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
    def test_clean_checkout_blocks_and_marks_public_context_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        readiness = report["real_context_product_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_missing_inputs")
        self.assertEqual(readiness["readiness_status"], "missing")
        self.assertEqual(readiness["ready_product_count"], 0)
        self.assertEqual(readiness["missing_product_count"], 6)
        self.assertEqual(readiness["deferred_product_count"], 5)
        self.assertEqual(readiness["metadata_mismatch_product_count"], 0)
        self.assertEqual(report["real_context_staging_checklist_state"], "deferred")
        self.assertEqual(checklist["checklist_state"], "deferred")
        self.assertEqual(checklist["verified_product_count"], 0)
        self.assertEqual(checklist["missing_product_count"], 0)
        self.assertEqual(checklist["deferred_product_count"], 5)
        self.assertEqual(checklist["partially_staged_product_count"], 0)
        self.assertEqual(checklist["claim_boundary_note"], gate.CHECKLIST_BOUNDARY_NOTE)
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
        self.assertEqual([entry["classification"] for entry in readiness["products"][:6]], ["missing"] * 6)
        self.assertEqual([entry["classification"] for entry in readiness["products"][6:]], ["deferred"] * 5)
        self.assertTrue(all(entry["readiness_impact"] for entry in checklist["products"]))

    def test_fixture_backed_minimal_inputs_keep_public_context_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        readiness = report["real_context_product_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(readiness["readiness_status"], "deferred")
        self.assertEqual(readiness["ready_product_count"], 6)
        self.assertEqual(readiness["missing_product_count"], 0)
        self.assertEqual(readiness["deferred_product_count"], 5)
        self.assertEqual(readiness["metadata_mismatch_product_count"], 0)
        self.assertEqual(report["real_context_staging_checklist_state"], "deferred")
        self.assertEqual(checklist["checklist_state"], "deferred")
        self.assertEqual(checklist["verified_product_count"], 0)
        self.assertEqual(checklist["missing_product_count"], 0)
        self.assertEqual(checklist["deferred_product_count"], 5)
        row_states = {entry["category"]: entry["classification"] for entry in readiness["products"]}
        self.assertEqual(row_states["aoi_tile_catalog"], "ready")
        self.assertEqual(row_states["terrain_crop"], "ready")
        self.assertEqual(row_states["terrain_crs_vertical_datum"], "ready")
        self.assertEqual(row_states["source_zone_metadata"], "ready")
        self.assertEqual(row_states["scenario_table"], "ready")
        self.assertEqual(row_states["source_scenario_policy"], "ready")
        self.assertEqual(row_states["swissimage_context"], "deferred")
        self.assertEqual(row_states["swisstlm3d_context"], "deferred")
        self.assertEqual(row_states["swisssurface3d_context"], "deferred")
        self.assertEqual(row_states["swisssurface3d_raster_context"], "deferred")
        self.assertEqual(row_states["swissbuildings3d_context"], "deferred")
        self.assertTrue(all(entry["checklist_state"] == "deferred" for entry in checklist["products"]))

    def test_partially_staged_real_context_checklist_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
            self._write_real_context_cache_manifest(
                repo_root,
                staged_categories={"swissimage_context", "swisstlm3d_context", "swisssurface3d_context"},
                mismatched_categories={"swisssurface3d_context"},
            )

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        readiness = report["real_context_product_readiness"]
        checklist = report["real_context_staging_checklist"]
        self.assertEqual(report["real_context_readiness_gate_status"], "blocked_missing_inputs")
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
        self.assertEqual(checklist["partially_staged_product_count"], 1)
        row_states = {entry["category"]: entry["classification"] for entry in readiness["products"]}
        self.assertEqual(row_states["swissimage_context"], "ready")
        self.assertEqual(row_states["swisstlm3d_context"], "ready")
        self.assertEqual(row_states["swisssurface3d_context"], "metadata_mismatch")
        self.assertEqual(row_states["swisssurface3d_raster_context"], "missing")
        self.assertEqual(row_states["swissbuildings3d_context"], "missing")

    def test_ready_core_inputs_and_deferred_public_context_products(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
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

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        readiness = report["real_context_product_readiness"]
        self.assertEqual(report["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["readiness_status"], "ready_for_real_context_acquisition")
        self.assertEqual(readiness["readiness_status"], "ready")
        self.assertEqual(readiness["ready_product_count"], 11)
        self.assertEqual(readiness["missing_product_count"], 0)
        self.assertEqual(readiness["deferred_product_count"], 0)
        self.assertEqual(readiness["metadata_mismatch_product_count"], 0)
        self.assertEqual(report["real_context_staging_checklist_state"], "verifier_ready")
        self.assertEqual(report["core_input_status"], "ready")
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
        self.assertFalse(report["synthetic_core_inputs_are_public_context_evidence"])
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

    def test_text_output_mentions_boundary_and_next_acquisition_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)
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

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        text_report = gate.render_text_report(report)
        self.assertEqual(text_report, gate.render_text_report(report))
        self.assertIn("schema_version: chant_sura_real_context_readiness_gate_v1", text_report)
        self.assertIn("real_context_readiness_gate_status: ready_for_real_context_acquisition", text_report)
        self.assertIn("real_context_staging_checklist_state: verifier_ready", text_report)
        self.assertIn("local_core_inputs:", text_report)
        self.assertIn("real_context_product_readiness:", text_report)
        self.assertIn("deterministic_acquisition_plan:", text_report)
        self.assertIn("public_geodata_workflow_contract:", text_report)
        self.assertIn("next_acquisition_decisions:", text_report)
        self.assertIn("real_context_product_readiness:", text_report)
        self.assertIn("real_context_staging_checklist:", text_report)
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
