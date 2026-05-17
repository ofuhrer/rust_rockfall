from __future__ import annotations

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
    def test_ready_core_inputs_and_deferred_public_context_products(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        self.assertEqual(report["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["readiness_status"], "ready_for_real_context_acquisition")
        self.assertEqual(report["core_input_status"], "ready")
        self.assertEqual(report["deferred_public_context_status"], "deferred_public_context_inputs")
        self.assertFalse(report["synthetic_core_inputs_are_public_context_evidence"])
        self.assertEqual(report["public_geodata_workflow_contract"]["public_geodata_contract_readiness_status"], "ready")
        self.assertEqual(report["public_geodata_workflow_contract"]["synthetic_fixture_readiness_status"], "not_applicable")
        self.assertIn("swissALTI3D", report["public_geodata_workflow_contract"]["swisstopo_product_classes"][0]["products"])

        ready_core_inputs = {entry["category"]: entry for entry in report["local_core_inputs"]}
        self.assertEqual(
            set(ready_core_inputs),
            {
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
        self.assertEqual(report["local_staged_summary"]["ready_core_input_count"], 5)
        self.assertEqual(report["local_staged_summary"]["ready_supporting_root_count"], 4)
        self.assertFalse(report["local_staged_summary"]["synthetic_core_inputs_are_public_context_evidence"])

    def test_text_output_mentions_boundary_and_next_acquisition_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._stage_minimal_inputs(repo_root)

            report = gate.build_report(self._site_config_path(), repo_root=repo_root)

        text_report = gate.render_text_report(report)
        self.assertEqual(text_report, gate.render_text_report(report))
        self.assertIn("schema_version: chant_sura_real_context_readiness_gate_v1", text_report)
        self.assertIn("real_context_readiness_gate_status: ready_for_real_context_acquisition", text_report)
        self.assertIn("local_core_inputs:", text_report)
        self.assertIn("deterministic_acquisition_plan:", text_report)
        self.assertIn("public_geodata_workflow_contract:", text_report)
        self.assertIn("next_acquisition_decisions:", text_report)
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
