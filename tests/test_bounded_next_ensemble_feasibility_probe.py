from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_bounded_next_ensemble_feasibility_probe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_bounded_next_ensemble_feasibility_probe", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BoundedNextEnsembleFeasibilityProbeTests(unittest.TestCase):
    def test_reduced_fixture_reports_blocked_optional_metadata_contract(self) -> None:
        self.assertNotIn("probabilistic_metadata", MODULE.load_yaml(MODULE.REDUCED_CASE))
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "bounded_next_ensemble_feasibility_probe_v1")
        self.assertEqual(report["probe_status"], "blocked_missing_optional_probabilistic_metadata")
        self.assertEqual(report["planning_status"], "blocked_missing_optional_probabilistic_metadata")
        self.assertEqual(
            report["planning_blocker"],
            "the smallest useful probe requires optional probabilistic metadata fields that are missing: "
            "probabilistic_metadata.source_zone_metadata_path, "
            "probabilistic_metadata.scenario_table_path, "
            "probabilistic_metadata.map_product_id, "
            "probabilistic_metadata.probability_mode, "
            "probabilistic_metadata.normalization_scope, "
            "probabilistic_metadata.scenario_id, "
            "hazard_probability.probability_model, "
            "hazard_probability.metadata_path, "
            "hazard_probability.weight_column, "
            "hazard_probability.normalization_convention, "
            "hazard_probability.filters.source_zone_ids, "
            "hazard_probability.filters.scenario_ids",
        )
        self.assertEqual(report["metadata_contract"]["status"], "blocked_missing_optional_probabilistic_metadata")
        self.assertEqual(report["metadata_contract"]["missing_fields"], report["proposed_probe"]["missing_metadata_fields"])
        self.assertIn("probabilistic_metadata.source_zone_metadata_path", report["metadata_contract"]["missing_fields"])
        self.assertIn("hazard_probability.filters.scenario_ids", report["metadata_contract"]["missing_fields"])
        self.assertTrue(report["read_only"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["distributed_execution_authorized"])
        self.assertEqual(report["proposed_probe"]["validation_output_mode"], "rebuildable_reduced_output")
        self.assertEqual(report["proposed_probe"]["seed"], 123)
        self.assertEqual(report["proposed_probe"]["ensemble_size"], 1000)
        self.assertIsNone(report["proposed_probe"]["scenario_id"])
        self.assertEqual(report["proposed_probe"]["probabilistic_metadata_status"], "missing_optional_probabilistic_metadata")
        self.assertIsNone(report["proposed_probe"]["source_zone_id"])
        self.assertEqual(report["proposed_probe"]["source_zone_status"], "missing_optional_hazard_probability")
        self.assertEqual(
            report["command_plan_template"]["status"], "blocked_missing_optional_probabilistic_metadata"
        )
        self.assertEqual(
            report["proposed_probe"]["expected_artifact_families"],
            [
                "diagnostics_json",
                "manifest_json",
                "trajectory_csv",
                "ensemble_deposition_csv",
                "trajectory_metadata_csv",
                "impact_events_csv",
            ],
        )
        self.assertIn(
            "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            report["proposed_probe"]["expected_command"],
        )
        self.assertTrue(report["boundedness_proof"]["bounded_relative_to_target_validation"])
        self.assertTrue(report["boundedness_proof"]["bounded_relative_to_target_hazard"])
        self.assertLess(report["boundedness_proof"]["output_byte_ratio_to_target_validation"], 0.01)
        self.assertLess(report["boundedness_proof"]["output_byte_ratio_to_target_hazard"], 0.1)
        self.assertEqual(report["measured_evidence"]["rebuildable_reduced_profile_classification"], "rebuildable_reduced_output")
        self.assertEqual(report["measured_evidence"]["single_job_decision"], "defer")
        self.assertTrue(report["measured_evidence"]["single_job_sufficient_for_next_step"])
        self.assertIn("target-vs-small-gate convergence interpretation", report["expected_closure_question"])
        self.assertEqual(
            report["command_plan_template"]["blocked_reason"],
            report["planning_blocker"],
        )
        self.assertEqual(report["command_plan_template"]["command_id"], "tschamut_next_ensemble_feasibility_probe_template")
        self.assertEqual(report["command_plan_template"]["group"], "rebuildable_reduced_output")

    def test_full_metadata_case_is_deferred_but_not_blocked(self) -> None:
        case_path = self.write_case(
            {
                **MODULE.load_yaml(MODULE.REDUCED_CASE),
                "probabilistic_metadata": {
                    "source_zone_metadata_path": "data/processed/swisstopo/tschamut_public_pilot/input/source_zone_metadata.yaml",
                    "scenario_table_path": "data/processed/swisstopo/tschamut_public_pilot/input/scenario_table.csv",
                    "map_product_id": "tschamut_public_conditional_gate_v1",
                    "probability_mode": "sampling_weighted_conditional",
                    "normalization_scope": "conditioned_on_filter",
                    "scenario_id": "synthetic_optional_metadata_scenario",
                },
                "hazard_probability": {
                    "probability_model": "sampling_weighted",
                    "metadata_path": "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/trajectory_metadata.csv",
                    "weight_column": "sampling_weight",
                    "normalization_convention": "conditioned_on_filter",
                    "filters": {
                        "source_zone_ids": ["synthetic_source_zone"],
                        "scenario_ids": ["synthetic_optional_metadata_scenario"],
                    },
                },
            }
        )

        report = MODULE.build_report(reduced_case_path=case_path)

        self.assertEqual(report["probe_status"], "deferred_pending_authorization")
        self.assertEqual(report["planning_status"], "deferred_pending_authorization")
        self.assertEqual(report["planning_blocker"], "execution deferred until explicitly authorized")
        self.assertEqual(report["metadata_contract"]["status"], "complete")
        self.assertEqual(report["metadata_contract"]["missing_fields"], [])
        self.assertEqual(report["command_plan_template"]["status"], "ready")
        self.assertEqual(report["proposed_probe"]["probabilistic_metadata_status"], "present")
        self.assertEqual(report["proposed_probe"]["source_zone_status"], "present")
        self.assertEqual(report["proposed_probe"]["scenario_id"], "synthetic_optional_metadata_scenario")
        self.assertEqual(report["proposed_probe"]["source_zone_id"], "synthetic_source_zone")

    def test_partial_metadata_case_reports_exact_missing_fields(self) -> None:
        case_path = self.write_case(
            {
                **MODULE.load_yaml(MODULE.REDUCED_CASE),
                "probabilistic_metadata": {
                    "source_zone_metadata_path": "data/processed/swisstopo/tschamut_public_pilot/input/source_zone_metadata.yaml",
                    "scenario_table_path": "data/processed/swisstopo/tschamut_public_pilot/input/scenario_table.csv",
                    "map_product_id": "tschamut_public_conditional_gate_v1",
                    "probability_mode": "sampling_weighted_conditional",
                    "normalization_scope": "conditioned_on_filter",
                    "scenario_id": "synthetic_partial_metadata_scenario",
                },
            }
        )

        report = MODULE.build_report(reduced_case_path=case_path)

        self.assertEqual(report["probe_status"], "blocked_missing_optional_probabilistic_metadata")
        self.assertIn("hazard_probability.probability_model", report["metadata_contract"]["missing_fields"])
        self.assertIn("hazard_probability.filters.source_zone_ids", report["metadata_contract"]["missing_fields"])
        self.assertEqual(report["proposed_probe"]["probabilistic_metadata_status"], "present")
        self.assertEqual(report["proposed_probe"]["source_zone_status"], "missing_optional_hazard_probability")
        self.assertIsNone(report["proposed_probe"]["source_zone_id"])

    def test_text_output_mentions_boundedness_and_metadata_contract(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "text"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Bounded Next-Ensemble Feasibility Probe", output)
        self.assertIn("Bounded relative to target validation: `True`", output)
        self.assertIn(
            "Planning blocker: `the smallest useful probe requires optional probabilistic metadata fields that are missing:",
            output,
        )
        self.assertIn("## Metadata Contract", output)
        self.assertIn("Command-plan status: `blocked_missing_optional_probabilistic_metadata`", output)
        self.assertIn("Go / No-Go Criteria", output)
        self.assertIn("tschamut_next_ensemble_feasibility_probe_template", output)

    def test_json_output_smoke(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "json"])

        self.assertEqual(exit_code, 0)
        json.loads(buffer.getvalue())

    def write_case(self, case: dict[str, object]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="tb143_bounded_next_probe_"))
        case_path = temp_dir / "case.yaml"
        case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
        return case_path


if __name__ == "__main__":
    unittest.main()
