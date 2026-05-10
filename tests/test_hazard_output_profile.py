from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_hazard_output_profile.py"
SPEC = importlib.util.spec_from_file_location("check_hazard_output_profile", SCRIPT_PATH)
assert SPEC is not None
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


VALIDATOR_PATH = ROOT / "scripts" / "validate_public_real_site_conditional_pilot_run.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_public_real_site_conditional_pilot_run",
    VALIDATOR_PATH,
)
assert VALIDATOR_SPEC is not None
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(validator)


class HazardOutputProfileTests(unittest.TestCase):
    def test_classify_full_debug_command(self) -> None:
        result = checker.classify_profile(
            command=[
                "python",
                "scripts/build_hazard_layers.py",
                "--case",
                "validation/private/fixtures/commands.yaml",
                "--output-dir",
                "hazard/results/fixture",
            ]
        )

        self.assertEqual(result["profile"], "full_debug")
        self.assertIn("controls", result)
        self.assertFalse(result["controls"]["no_plots"])

    def test_classify_scalable_conditional_command(self) -> None:
        result = checker.classify_profile(
            command=[
                "uv",
                "run",
                "python",
                "scripts/build_hazard_layers.py",
                "--case",
                "validation/private/fixtures/commands.yaml",
                "--output-dir",
                "hazard/results/fixture",
                "--conditional-curve-export",
                "summary-only",
                "--grid-csv-export",
                "none",
                "--no-plots",
            ]
        )

        self.assertEqual(result["profile"], "scalable_conditional")
        self.assertIn("--conditional-curve-export summary-only", result["matched_controls"])
        self.assertIn("--grid-csv-export none", result["matched_controls"])
        self.assertIn("--no-plots", result["matched_controls"])

    def test_classify_provenance_audit_command(self) -> None:
        result = checker.classify_profile(
            command=[
                "python",
                "scripts/build_hazard_layers.py",
                "--case",
                "validation/private/fixtures/commands.yaml",
                "--output-dir",
                "hazard/results/fixture",
                "--conditional-curve-export",
                "summary-only",
                "--grid-csv-export",
                "none",
                "--no-plots",
                "--trajectory-workers",
                "4",
                "--reducer-workers",
                "4",
            ]
        )

        self.assertEqual(result["profile"], "provenance_audit")
        self.assertIn("trajectory/reducer provenance lineage", result["matched_controls"])
        self.assertNotIn("--map-package-manifest-json", result["missing_controls"])

    def test_classify_custom_or_mixed_command(self) -> None:
        result = checker.classify_profile(
            command=[
                "uv",
                "run",
                "python",
                "scripts/build_hazard_layers.py",
                "--case",
                "validation/private/fixtures/commands.yaml",
                "--output-dir",
                "hazard/results/fixture",
                "--conditional-curve-export",
                "summary-only",
                "--grid-csv-export",
                "full",
                "--export-geotiff",
            ]
        )

        self.assertEqual(result["profile"], "custom_or_mixed")
        self.assertIn("conditional summary-only with full grid CSV output", result["unsupported_or_ambiguous_controls"])

    def test_classify_from_command_plan_fixture(self) -> None:
        command_plan_path = ROOT / "tests" / "fixtures" / "hazard_output_profile" / "command_plan_scalable.json"
        payload = json.loads(command_plan_path.read_text(encoding="utf-8"))

        result = checker.classify_profile(command_plan=command_plan_path)

        self.assertEqual(result["profile"], "provenance_audit")
        self.assertEqual(result["input"]["source"], "command-plan")
        self.assertEqual(result["input"]["command"], payload["commands"][1]["command"])

    def test_classify_tschamut_committed_plan_full_debug(self) -> None:
        command_plan_path = ROOT / "tests" / "fixtures" / "hazard_output_profile" / "command_plan_full_debug.json"
        payload = json.loads(command_plan_path.read_text(encoding="utf-8"))

        result = checker.classify_profile(command_plan=command_plan_path)

        self.assertEqual(result["profile"], "full_debug")
        self.assertIn("--no-plots", result["matched_controls"])
        self.assertIn("controls", result)

    def test_classify_generated_command_plan_from_manifest_with_scalable_controls(self) -> None:
        manifest = validator.read_yaml(
            ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
        )
        manifest["hazard_output_plan"].update(
            {
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "trajectory_workers": 2,
            }
        )
        plan = validator.build_command_plan(manifest)
        hazard_command = plan["commands"][-1]["command"]
        result = checker.classify_profile(command=hazard_command)

        self.assertEqual(result["profile"], "provenance_audit")
        self.assertIn("--conditional-curve-export summary-only", result["matched_controls"])
        self.assertIn("--grid-csv-export none", result["matched_controls"])
        self.assertIn("trajectory/reducer provenance lineage", result["matched_controls"])

    def test_classify_minimal_scalable_no_provenance_markers(self) -> None:
        result = checker.classify_profile(
            command=[
                "uv",
                "run",
                "python",
                "scripts/build_hazard_layers.py",
                "--case",
                "validation/private/fixtures/commands.yaml",
                "--output-dir",
                "hazard/results/fixture",
                "--conditional-curve-export",
                "summary-only",
                "--grid-csv-export",
                "none",
                "--no-plots",
                "--export-geotiff",
            ]
        )

        self.assertEqual(result["profile"], "scalable_conditional")
        self.assertIn("--conditional-curve-export summary-only", result["matched_controls"])
        self.assertIn("--grid-csv-export none", result["matched_controls"])
        self.assertNotIn("trajectory/reducer provenance lineage", result["matched_controls"])


if __name__ == "__main__":
    unittest.main()
