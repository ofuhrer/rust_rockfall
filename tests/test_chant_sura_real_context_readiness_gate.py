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
        self.assertTrue(all(entry["next_acquisition_decision"] == "acquire_and_stage_public_context_product" for entry in next_decisions.values()))

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

    def _stage_minimal_inputs(self, repo_root: Path) -> None:
        staging.stage_minimal_inputs(
            repo_root=repo_root,
            site_config=self._site_config_path(),
            fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
        )

    def _site_config_path(self) -> Path:
        return ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"


if __name__ == "__main__":
    unittest.main()
