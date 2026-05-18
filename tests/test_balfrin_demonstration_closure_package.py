from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_demonstration_closure_package.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_demonstration_closure_package", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinDemonstrationClosurePackageTests(unittest.TestCase):
    def test_blocked_no_new_measured_evidence_classification(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_demonstration_closure_package_v1")
        self.assertEqual(report["closure_status"], "blocked_no_new_measured_evidence")
        self.assertEqual(report["closure_provenance_status"], "blocked_no_new_measured_evidence")
        self.assertFalse(report["maturity_label_update_allowed"])
        self.assertEqual(report["new_measured_evidence_section"]["evidence_type"], "blocked")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 5,
                "fixture_backed": 1,
                "dry_run": 2,
                "blocked": 1,
                "unavailable": 0,
                "unauthorized": 1,
                "historical": 1,
            },
        )
        self.assertIn("fails closed", report["package_summary"]["summary"])
        self.assertIn("larger Swiss workflows", report["reviewer_answer"])
        self.assertIn("blocked_no_new_measured_evidence", MODULE.render_text_report(report))

    def test_mixed_provenance_warning_requires_new_measured_evidence(self) -> None:
        report = MODULE.build_report(
            {
                "new_measured_evidence": {
                    "status": "measured",
                    "evidence_type": "measured",
                    "source_type": "metrics_completion_rerun",
                    "preservation_checked": True,
                    "preservation_gate_status": "ready_for_demonstration_evidence",
                    "authorization_status": "authorized",
                    "summary": "Measured metrics-completion rerun with preservation-check evidence.",
                }
            }
        )

        self.assertEqual(report["closure_status"], "mixed_provenance_warning")
        self.assertFalse(report["maturity_label_update_allowed"])
        self.assertEqual(report["new_measured_evidence_section"]["evidence_type"], "measured")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 6,
                "fixture_backed": 1,
                "dry_run": 2,
                "blocked": 0,
                "unavailable": 0,
                "unauthorized": 1,
                "historical": 1,
            },
        )
        self.assertIn("mixed provenance", report["reviewer_answer"])
        self.assertIn("useful for review", report["package_summary"]["summary"])
        self.assertEqual(
            report["new_measured_evidence_section"]["closure_input_compatibility"]["status"],
            "compatible",
        )

    def test_authorized_multi_zone_probe_is_a_supported_new_measured_source_family(self) -> None:
        report = MODULE.build_report(
            {
                "new_measured_evidence": {
                    "status": "measured",
                    "evidence_type": "measured",
                    "source_type": "authorized_multi_zone_probe",
                    "preservation_checked": True,
                    "preservation_gate_status": "ready_for_demonstration_evidence",
                    "authorization_status": "authorized_for_one_bounded_probe",
                    "summary": "Measured authorized multi-zone probe with preservation-check evidence.",
                }
            }
        )

        self.assertEqual(report["closure_status"], "mixed_provenance_warning")
        self.assertEqual(
            report["new_measured_evidence_section"]["closure_input_compatibility"]["status"],
            "compatible",
        )

    def test_fixture_backed_new_evidence_input_remains_blocked(self) -> None:
        report = MODULE.build_report(
            {
                "new_measured_evidence": {
                    "status": "fixture_backed_complete",
                    "evidence_type": "fixture_backed",
                    "source_type": "metrics_completion_rerun",
                    "preservation_checked": True,
                    "preservation_gate_status": "ready_for_demonstration_evidence",
                    "authorization_status": "authorized",
                    "summary": "Fixture-backed rehearsal only.",
                }
            }
        )

        self.assertEqual(report["closure_status"], "blocked_no_new_measured_evidence")
        self.assertEqual(report["new_measured_evidence_section"]["evidence_type"], "blocked")
        compatibility = report["new_measured_evidence_section"]["closure_input_compatibility"]
        self.assertEqual(compatibility["status"], "blocked_missing_inputs")
        self.assertIn("new_measured_evidence.evidence_type=measured", compatibility["missing_fields"])

    def test_complete_measured_report_allows_label_upgrade(self) -> None:
        report = MODULE.build_report(self.complete_measured_override())

        self.assertEqual(report["closure_status"], "complete_measured_closure")
        self.assertTrue(report["maturity_label_update_allowed"])
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 11,
                "fixture_backed": 0,
                "dry_run": 0,
                "blocked": 0,
                "unavailable": 0,
                "unauthorized": 0,
                "historical": 0,
            },
        )
        self.assertIn("larger Swiss workflows", report["reviewer_answer"])
        self.assertIn("complete enough", report["reviewer_answer"])
        self.assertIn("Measured closure is complete", report["package_summary"]["summary"])

    def test_cli_materializes_artifacts_for_a_complete_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_demonstration_closure_package_v1"
            override_path = self.write_json(self.complete_measured_override())
            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    exit_code = MODULE.main(
                        [
                            "--evidence-json",
                            str(override_path),
                            "--artifact-dir",
                            str(artifact_dir),
                            "--format",
                            "json",
                        ]
                    )
            finally:
                override_path.unlink(missing_ok=True)

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_demonstration_closure_package_v1.json"
            text_path = artifact_dir / "balfrin_demonstration_closure_package_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["closure_status"], "complete_measured_closure")
            self.assertIn("Balfrin Demonstration Closure Package", text_path.read_text(encoding="utf-8"))

    def complete_measured_override(self) -> dict[str, object]:
        section_overrides = {
            name: {"status": "measured", "evidence_type": "measured"}
            for name in MODULE.SECTION_NAMES
        }
        section_overrides["preservation_section"] = {
            "status": "ready_for_demonstration_evidence",
            "evidence_type": "measured",
        }
        section_overrides["replay_section"] = {"status": "measured", "evidence_type": "measured"}
        section_overrides["scientific_claim_boundaries_section"] = {
            "status": "measured",
            "evidence_type": "measured",
        }
        section_overrides["second_site_portability_section"] = {
            "status": "measured",
            "evidence_type": "measured",
        }
        return {
            "new_measured_evidence": {
                "status": "measured",
                "evidence_type": "measured",
                "source_type": "metrics_completion_rerun",
                "preservation_checked": True,
                "preservation_gate_status": "ready_for_demonstration_evidence",
                "authorization_status": "authorized",
                "summary": "Measured metrics-completion rerun with preservation-check evidence.",
            },
            "section_overrides": section_overrides,
        }

    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)


if __name__ == "__main__":
    unittest.main()
