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

from scripts import summarize_balfrin_next_live_run_decision_gate as DECISION_GATE


class BalfrinDemonstrationClosurePackageTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict[str, object]:
        fixture_root = ROOT / "tests/fixtures/balfrin_next_live_run_decision_gate"
        return json.loads((fixture_root / name).read_text(encoding="utf-8"))

    def test_blocked_no_new_measured_evidence_classification(self) -> None:
        report = MODULE.build_report()

        self.assertEqual(report["schema_version"], "balfrin_demonstration_closure_package_v1")
        self.assertEqual(report["closure_status"], "blocked_no_new_measured_evidence")
        self.assertEqual(report["closure_provenance_status"], "blocked_no_new_measured_evidence")
        self.assertFalse(report["maturity_label_update_allowed"])
        self.assertEqual(report["metrics_closure_section"]["status"], "blocked_no_new_measured_evidence")
        self.assertEqual(report["target_area_spatial_artifact_section"]["status"], "not_evaluated_in_closure_refresh")
        self.assertEqual(report["next_measured_action_section"]["status"], "blocked")
        self.assertEqual(report["new_measured_evidence_section"]["evidence_type"], "blocked")
        self.assertEqual(
            report["package_summary"]["section_counts"],
            {
                "measured": 5,
                "fixture_backed": 1,
                "dry_run": 2,
                "blocked": 3,
                "unavailable": 1,
                "unauthorized": 1,
                "historical": 1,
            },
        )
        self.assertIn("fails closed", report["package_summary"]["summary"])
        self.assertIn("no new measured or recovered target-area metrics", report["reviewer_answer"].lower())
        self.assertIn("blocked_no_new_measured_evidence", MODULE.render_text_report(report))

    def test_metrics_complete_branch_ranks_next_measured_action_after_metrics_completion(self) -> None:
        report = MODULE.build_report(
            self.metrics_complete_override()
        )

        self.assertEqual(report["closure_status"], "metrics_complete")
        self.assertTrue(report["maturity_label_update_allowed"])
        self.assertEqual(report["metrics_closure_section"]["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(report["metrics_closure_section"]["evidence_type"], "measured")
        self.assertEqual(report["target_area_spatial_artifact_section"]["status"], "spatial_artifacts_deferred")
        self.assertEqual(report["target_area_spatial_artifact_section"]["spatial_artifact_classification"], "not_required_for_execution_metrics_closure")
        self.assertEqual(report["next_measured_action_section"]["status"], "defer")
        self.assertEqual(report["next_measured_action_section"]["selected_action_id"], "physical_evidence_acquisition")
        self.assertEqual(
            [row["action_id"] for row in report["next_measured_action_section"]["ranked_actions"]],
            [
                "smallest_bounded_multi_zone_probe",
                "physical_evidence_acquisition",
                "second_site_public_context_progress",
                "defer_portability_or_physical_evidence",
            ],
        )
        self.assertEqual(
            report["next_measured_action_section"]["ranked_actions"][1]["status"],
            "defer",
        )
        self.assertIn("metrics are complete", report["package_summary"]["summary"].lower())
        self.assertIn("next measured action is physical_evidence_acquisition", report["package_summary"]["summary"])
        self.assertEqual(
            report["new_measured_evidence_section"]["closure_input_compatibility"]["status"],
            "compatible",
        )

    def test_metrics_unrecoverable_deferred_branch_keeps_spatial_deferral_explicit(self) -> None:
        report = MODULE.build_report(
            self.metrics_unrecoverable_override()
        )

        self.assertEqual(report["closure_status"], "metrics_unrecoverable_deferred")
        self.assertFalse(report["maturity_label_update_allowed"])
        self.assertEqual(report["metrics_closure_section"]["evidence_type"], "unavailable")
        self.assertEqual(report["target_area_spatial_artifact_section"]["status"], "spatial_artifacts_deferred")
        self.assertEqual(report["target_area_spatial_artifact_section"]["spatial_artifact_classification"], "not_required_for_execution_metrics_closure")
        self.assertEqual(report["next_measured_action_section"]["status"], "defer")
        self.assertEqual(report["next_measured_action_section"]["selected_action_id"], "physical_evidence_acquisition")
        self.assertEqual(
            report["new_measured_evidence_section"]["closure_input_compatibility"]["status"],
            "blocked_missing_inputs",
        )
        self.assertIn("explicitly unrecoverable and deferred", report["reviewer_answer"].lower())
        self.assertIn("target-area metrics are explicitly unrecoverable and deferred", report["package_summary"]["summary"].lower())

    def test_cli_materializes_artifacts_for_a_metrics_complete_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "validation/private/tschamut_public_pilot/balfrin_demonstration_closure_package_v1"
            override_path = self.write_json(self.metrics_complete_override())
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
            self.assertEqual(report["closure_status"], "metrics_complete")
            self.assertIn("Balfrin Demonstration Closure Package", text_path.read_text(encoding="utf-8"))

    def metrics_complete_override(self) -> dict[str, object]:
        decision_gate_bundle = self.load_fixture("defer_bundle.json")
        decision_gate_report = DECISION_GATE.build_report(decision_gate_bundle)
        metrics_closure_section = MODULE.build_metrics_closure_section(
            status=MODULE.METRICS_COMPLETE,
            metrics_completion_source="recovered_existing_run_root",
            metrics_contract_status="complete",
        )
        spatial_artifact_section = MODULE.build_target_area_spatial_artifact_section(self.spatial_artifact_report())
        next_action_section = MODULE.build_next_measured_action_section(
            metrics_closure_section,
            decision_gate_report=decision_gate_report,
        )
        new_evidence_section = MODULE.build_new_measured_evidence_section(metrics_closure_section)

        section_overrides = {
            "metrics_closure_section": metrics_closure_section,
            "target_area_spatial_artifact_section": spatial_artifact_section,
            "next_measured_action_section": next_action_section,
            "new_measured_evidence_section": new_evidence_section,
            "preservation_section": {
                "status": "ready_for_demonstration_evidence",
                "evidence_type": "measured",
            },
            "replay_section": {"status": "measured", "evidence_type": "measured"},
            "scientific_claim_boundaries_section": {
                "status": "measured",
                "evidence_type": "measured",
            },
            "second_site_portability_section": {
                "status": "measured",
                "evidence_type": "measured",
            },
        }
        return {"section_overrides": section_overrides}

    def metrics_unrecoverable_override(self) -> dict[str, object]:
        decision_gate_bundle = self.load_fixture("defer_bundle.json")
        decision_gate_report = DECISION_GATE.build_report(decision_gate_bundle)
        metrics_closure_section = MODULE.build_metrics_closure_section(
            status=MODULE.METRICS_UNRECOVERABLE_DEFERRED,
            metrics_completion_source="blocked_missing_metrics",
            metrics_contract_status="blocked_missing_inputs",
        )
        spatial_artifact_section = MODULE.build_target_area_spatial_artifact_section(self.spatial_artifact_report())
        next_action_section = MODULE.build_next_measured_action_section(
            metrics_closure_section,
            decision_gate_report=decision_gate_report,
        )
        new_evidence_section = MODULE.build_new_measured_evidence_section(metrics_closure_section)
        section_overrides = {
            "metrics_closure_section": metrics_closure_section,
            "target_area_spatial_artifact_section": spatial_artifact_section,
            "next_measured_action_section": next_action_section,
            "new_measured_evidence_section": new_evidence_section,
        }
        return {"section_overrides": section_overrides}

    def spatial_artifact_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_target_area_spatial_artifact_recovery_v1",
            "report_status": "spatial_artifacts_deferred",
            "spatial_artifact_recovery": {
                "status": "spatial_artifacts_deferred",
                "status_counts": {
                    "recovered": 3,
                    "unavailable_from_preserved_root": 6,
                },
                "recovered_artifacts": [
                    "hazard_manifest",
                    "map_package_manifest",
                    "pilot_gis_package_manifest",
                ],
                "unrecovered_artifacts": [
                    "max_kinetic_energy",
                    "max_jump_height",
                    "velocity_exceedance_5mps",
                    "spatial_uncertainty_layer_summary",
                    "spatial_uncertainty_region_products",
                    "spatial_confidence_product_manifest",
                ],
            },
            "execution_metrics_closure_separation": {
                "status": "separated_from_spatial_artifacts",
                "spatial_artifact_classification": "not_required_for_execution_metrics_closure",
                "artifact_count": 9,
            },
            "spatial_interpretation_evidence": {
                "status": "deferred_missing_spatial_artifacts",
                "usable_as_target_area_spatial_interpretation_evidence": False,
                "unrecovered_artifacts": [
                    "max_kinetic_energy",
                    "max_jump_height",
                    "velocity_exceedance_5mps",
                    "spatial_uncertainty_layer_summary",
                    "spatial_uncertainty_region_products",
                    "spatial_confidence_product_manifest",
                ],
                "physical_validation_evidence_status": "not_established",
                "usable_as_physical_validation_evidence": False,
                "summary": "Spatial artifacts remain explicit deferrals and are not physical validation evidence.",
            },
            "summary": "Balfrin target-area spatial artifact recovery spatial_artifacts_deferred: 3 recovered, 6 unavailable from preserved root. spatial_interpretation_evidence=deferred_missing_spatial_artifacts; spatial artifacts are not required for execution-metrics closure.",
        }

    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)


if __name__ == "__main__":
    unittest.main()
