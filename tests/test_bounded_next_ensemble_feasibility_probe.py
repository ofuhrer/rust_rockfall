from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest


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
    def test_report_records_bounded_same_scale_probe_and_deferred_execution(self) -> None:
        self.assertNotIn("probabilistic_metadata", MODULE.load_yaml(MODULE.REDUCED_CASE))
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "bounded_next_ensemble_feasibility_probe_v1")
        self.assertEqual(report["probe_status"], "deferred_pending_optional_probabilistic_metadata")
        self.assertEqual(report["planning_status"], "deferred_pending_optional_probabilistic_metadata")
        self.assertEqual(
            report["planning_blocker"],
            "optional probabilistic metadata is absent from the current reduced-output fixture",
        )
        self.assertTrue(report["read_only"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["distributed_execution_authorized"])
        self.assertEqual(report["proposed_probe"]["validation_output_mode"], "rebuildable_reduced_output")
        self.assertEqual(report["proposed_probe"]["seed"], 123)
        self.assertEqual(report["proposed_probe"]["ensemble_size"], 1000)
        self.assertIsNone(report["proposed_probe"]["scenario_id"])
        self.assertEqual(
            report["proposed_probe"]["probabilistic_metadata_status"],
            "optional_probabilistic_metadata_missing",
        )
        self.assertIsNone(report["proposed_probe"]["source_zone_id"])
        self.assertEqual(
            report["proposed_probe"]["source_zone_status"],
            "missing_optional_hazard_probability",
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
            "optional probabilistic metadata is absent from the current reduced-output fixture",
        )
        self.assertEqual(report["command_plan_template"]["command_id"], "tschamut_next_ensemble_feasibility_probe_template")
        self.assertEqual(report["command_plan_template"]["group"], "rebuildable_reduced_output")

    def test_text_output_mentions_boundedness_and_go_no_go_criteria(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "text"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Bounded Next-Ensemble Feasibility Probe", output)
        self.assertIn("Bounded relative to target validation: `True`", output)
        self.assertIn("Planning blocker: `optional probabilistic metadata is absent from the current reduced-output fixture`", output)
        self.assertIn("Go / No-Go Criteria", output)
        self.assertIn("tschamut_next_ensemble_feasibility_probe_template", output)

    def test_json_output_smoke(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--format", "json"])

        self.assertEqual(exit_code, 0)
        json.loads(buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
