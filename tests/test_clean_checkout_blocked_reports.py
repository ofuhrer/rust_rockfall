from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import io


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_clean_checkout_blocked_reports.py"
SPEC = importlib.util.spec_from_file_location("summarize_clean_checkout_blocked_reports", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CleanCheckoutBlockedReportsTests(unittest.TestCase):
    def test_clean_checkout_report_marks_key_helpers_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = MODULE.build_report(Path(tmpdir))

        self.assertEqual(report["schema_version"], "clean_checkout_blocked_reports_v1")
        self.assertEqual(report["clean_checkout_status"], "blocked_missing_inputs")
        self.assertIn("same-scale=blocked_missing_inputs", report["summary"])
        helpers = report["helper_statuses"]
        self.assertEqual(helpers["same_scale_artifact_readiness"]["readiness_status"], "blocked_missing_inputs")
        self.assertTrue(helpers["same_scale_artifact_readiness"]["missing_paths"])
        self.assertEqual(helpers["balfrin_probe_metrics_report"]["report_status"], "blocked_missing_run_root")
        self.assertIn("missing-run-root", helpers["balfrin_probe_metrics_report"]["run_root"])
        self.assertEqual(helpers["balfrin_target_area_evidence_bundle"]["bundle_status"], "blocked_missing_inputs")
        self.assertEqual(
            helpers["second_site_public_geodata_preflight"]["portability_preflight_status"],
            "blocked_missing_inputs",
        )
        inventory = report["evidence_inventory"]
        self.assertIn("scripts/check_same_scale_artifact_readiness.py", inventory["tracked"])
        self.assertIn(str(ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"), inventory["fixture_backed"])
        self.assertIn("validation/private/tschamut_public_pilot/gate_v1", "\n".join(inventory["ignored_local"]))
        self.assertIn("balfrin_probe_metrics_report -> blocked_missing_run_root", inventory["unavailable"])
        self.assertGreaterEqual(len(report["readiness_commands"]), 4)

    def test_cli_writes_report_artifacts_and_returns_blocked_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/clean_checkout_blocked_reports_v1"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = MODULE.main(["--artifact-dir", str(artifact_dir), "--format", "json"])

            self.assertEqual(exit_code, 2)
            json_path = artifact_dir / "clean_checkout_blocked_reports_v1.json"
            text_path = artifact_dir / "clean_checkout_blocked_reports_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["clean_checkout_status"], "blocked_missing_inputs")
            self.assertIn("Clean Checkout Blocked Reports", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
