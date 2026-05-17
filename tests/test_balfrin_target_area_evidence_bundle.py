from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_target_area_evidence_bundle.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_target_area_evidence_bundle", SCRIPT_PATH)
assert SPEC is not None
bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bundle)


class BalfrinTargetAreaEvidenceBundleTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_current_report_combines_measured_unavailable_and_blocked_sections(self) -> None:
        report = bundle.build_current_report()

        self.assertEqual(report["schema_version"], "balfrin_target_area_evidence_bundle_v1")
        self.assertEqual(report["bundle_status"], "mixed_provenance")
        self.assertEqual(report["bundle_provenance_status"], "mixed_provenance")
        self.assertEqual(
            report["bundle_summary"]["section_counts"],
            {
                "measured": 1,
                "fixture_backed": 0,
                "unavailable": 1,
                "blocked_missing_inputs": 1,
            },
        )
        self.assertEqual(report["section_provenance_profile"][0]["evidence_type"], "unavailable")
        self.assertEqual(report["section_provenance_profile"][1]["evidence_type"], "blocked")
        self.assertEqual(report["section_provenance_profile"][2]["evidence_type"], "measured")
        self.assertEqual(report["target_area_demo_handoff_report"]["bundle_status"], "template_only")
        self.assertEqual(report["probe_metrics_report"]["report_status"], "blocked_missing_inputs")
        self.assertEqual(report["canonical_evidence_bundle"]["bundle_status"], "measured")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])
        self.assertIn("template-only handoff", report["bundle_summary"]["summary"])
        self.assertIn("section_provenance_profile:", bundle.render_text_report(report))
        self.assertIn("probe_metrics_report:", bundle.render_text_report(report))

    def test_fixture_backed_override_stays_fixture_backed(self) -> None:
        report = bundle.build_report(
            {
                "bundle_report": {
                    "schema_version": "balfrin_target_area_evidence_bundle_v1",
                    "pilot_id": "tschamut_public_pilot",
                    "run_id": "tschamut_public_balfrin_target_area_demo_v1",
                    "canonical_bundle_path": "validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1",
                    "bundle_status": "fixture_backed",
                    "bundle_provenance_status": "fixture_backed",
                    "bundle_summary": {
                        "status": "fixture_backed",
                        "summary": "Fixture-backed target-area evidence bundle.",
                        "blockers": [],
                        "section_counts": {
                            "measured": 0,
                            "fixture_backed": 3,
                            "unavailable": 0,
                            "blocked_missing_inputs": 0,
                        },
                    },
                    "target_area_demo_handoff_report": {
                        "bundle_status": "fixture_backed",
                        "status": "fixture_backed",
                        "source_paths": ["tests/fixtures/balfrin_target_area_bundle/handoff.json"],
                    },
                    "probe_metrics_report": {
                        "report_status": "fixture_backed",
                        "status": "fixture_backed",
                        "source_paths": ["tests/fixtures/balfrin_target_area_bundle/probe_metrics.json"],
                    },
                    "canonical_evidence_bundle": {
                        "bundle_status": "fixture_backed",
                        "status": "fixture_backed",
                        "source_paths": ["tests/fixtures/balfrin_target_area_bundle/bundle.json"],
                    },
                    "claim_boundaries": {
                        "operational_claims_allowed": False,
                        "physical_probability_claims_allowed": False,
                        "annual_frequency_claims_allowed": False,
                        "risk_exposure_vulnerability_claims_allowed": False,
                        "scale_up_authorized": False,
                        "distributed_execution_authorized": False,
                    },
                    "section_provenance_profile": [
                        {
                            "section": "target_area_demo_handoff_report",
                            "status": "fixture_backed",
                            "evidence_type": "fixture_backed",
                            "source_paths": ["tests/fixtures/balfrin_target_area_bundle/handoff.json"],
                        },
                        {
                            "section": "probe_metrics_report",
                            "status": "fixture_backed",
                            "evidence_type": "fixture_backed",
                            "source_paths": ["tests/fixtures/balfrin_target_area_bundle/probe_metrics.json"],
                        },
                        {
                            "section": "canonical_evidence_bundle",
                            "status": "fixture_backed",
                            "evidence_type": "fixture_backed",
                            "source_paths": ["tests/fixtures/balfrin_target_area_bundle/bundle.json"],
                        },
                    ],
                    "source_paths": {
                        "target_area_demo_handoff_report_path": "tests/fixtures/balfrin_target_area_bundle/handoff.json",
                        "probe_metrics_report_path": "tests/fixtures/balfrin_target_area_bundle/probe_metrics.json",
                        "canonical_bundle_path": "tests/fixtures/balfrin_target_area_bundle/bundle.json",
                    },
                    "evidence_sources": ["tests/fixtures/balfrin_target_area_bundle"],
                    "missing_inputs": [],
                }
            }
        )

        self.assertEqual(report["bundle_status"], "fixture_backed")
        self.assertEqual(report["bundle_summary"]["section_counts"], {"measured": 0, "fixture_backed": 3, "unavailable": 0, "blocked_missing_inputs": 0})
        self.assertTrue(all(section["evidence_type"] == "fixture_backed" for section in report["section_provenance_profile"]))

    def test_missing_inputs_bundle_is_blocked(self) -> None:
        report = bundle.build_report({"missing_inputs": ["canonical_evidence_bundle", "probe_metrics_report"]})

        self.assertEqual(report["bundle_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["canonical_evidence_bundle", "probe_metrics_report"])
        self.assertEqual(report["bundle_summary"]["blockers"], ["canonical_evidence_bundle", "probe_metrics_report"])
        self.assertEqual(report["bundle_summary"]["section_counts"], {"measured": 0, "fixture_backed": 0, "unavailable": 0, "blocked_missing_inputs": 3})
        self.assertTrue(all(section["evidence_type"] == "blocked" for section in report["section_provenance_profile"]))
        self.assertIn("required target-area evidence inputs are missing", bundle.render_text_report(report))

    def test_cli_writes_json_and_text_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            override_path = self.write_json({"bundle_report": self.fixture_backed_bundle_report()})
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1"

            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    exit_code = bundle.main(
                        [
                            "--artifact-dir",
                            str(artifact_dir),
                            "--evidence-json",
                            str(override_path),
                        ]
                    )
            finally:
                override_path.unlink(missing_ok=True)

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_target_area_evidence_bundle_v1.json"
            text_path = artifact_dir / "balfrin_target_area_evidence_bundle_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            json_report = json.loads(json_path.read_text(encoding="utf-8"))
            text_report = text_path.read_text(encoding="utf-8")
            self.assertEqual(json_report["bundle_status"], "fixture_backed")
            self.assertIn("Balfrin Target-Area Evidence Bundle", text_report)
            self.assertIn("canonical_bundle_path:", text_report)
            self.assertIn("bundle_status: fixture_backed", text_report)

    def fixture_backed_bundle_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_target_area_evidence_bundle_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_balfrin_target_area_demo_v1",
            "canonical_bundle_path": "validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1",
            "bundle_status": "fixture_backed",
            "bundle_provenance_status": "fixture_backed",
            "bundle_summary": {
                "status": "fixture_backed",
                "summary": "Fixture-backed target-area evidence bundle.",
                "blockers": [],
                "section_counts": {
                    "measured": 0,
                    "fixture_backed": 3,
                    "unavailable": 0,
                    "blocked_missing_inputs": 0,
                },
            },
            "target_area_demo_handoff_report": {
                "bundle_status": "fixture_backed",
                "status": "fixture_backed",
                "source_paths": ["tests/fixtures/balfrin_target_area_bundle/handoff.json"],
            },
            "probe_metrics_report": {
                "report_status": "fixture_backed",
                "status": "fixture_backed",
                "source_paths": ["tests/fixtures/balfrin_target_area_bundle/probe_metrics.json"],
            },
            "canonical_evidence_bundle": {
                "bundle_status": "fixture_backed",
                "status": "fixture_backed",
                "source_paths": ["tests/fixtures/balfrin_target_area_bundle/bundle.json"],
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "annual_frequency_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
            },
            "section_provenance_profile": [
                {
                    "section": "target_area_demo_handoff_report",
                    "status": "fixture_backed",
                    "evidence_type": "fixture_backed",
                    "source_paths": ["tests/fixtures/balfrin_target_area_bundle/handoff.json"],
                },
                {
                    "section": "probe_metrics_report",
                    "status": "fixture_backed",
                    "evidence_type": "fixture_backed",
                    "source_paths": ["tests/fixtures/balfrin_target_area_bundle/probe_metrics.json"],
                },
                {
                    "section": "canonical_evidence_bundle",
                    "status": "fixture_backed",
                    "evidence_type": "fixture_backed",
                    "source_paths": ["tests/fixtures/balfrin_target_area_bundle/bundle.json"],
                },
            ],
            "source_paths": {
                "target_area_demo_handoff_report_path": "tests/fixtures/balfrin_target_area_bundle/handoff.json",
                "probe_metrics_report_path": "tests/fixtures/balfrin_target_area_bundle/probe_metrics.json",
                "canonical_bundle_path": "tests/fixtures/balfrin_target_area_bundle/bundle.json",
            },
            "evidence_sources": ["tests/fixtures/balfrin_target_area_bundle"],
            "missing_inputs": [],
        }


if __name__ == "__main__":
    unittest.main()
