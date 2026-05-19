from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_evidence_bundle.py"
SPEC = importlib.util.spec_from_file_location("summarize_balfrin_evidence_bundle", SCRIPT_PATH)
assert SPEC is not None
bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bundle)


class BalfrinEvidenceBundleTests(unittest.TestCase):
    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)

    def test_complete_bundle_is_reported_as_measured_and_preserves_boundaries(self) -> None:
        report = bundle.build_report({"bundle_report": self.complete_bundle_report()})

        self.assertEqual(report["schema_version"], "balfrin_evidence_bundle_v1")
        self.assertEqual(report["bundle_status"], "complete")
        self.assertEqual(report["bundle_summary"]["status"], "complete")
        self.assertIn("readiness, metrics, outputs, GIS / COG status", report["bundle_summary"]["summary"])
        self.assertEqual(report["post_run_interpretation_gate_report"]["interpretation_status"], "measured_conditional_diagnostic")
        self.assertEqual(report["failure_taxonomy_report"]["taxonomy_status"], "scope_limited")
        self.assertEqual(report["gis_cog_readiness_report"]["gis_cog_readiness_status"], "gis_package_ready")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_incomplete_bundle_remains_incomplete_without_blocking_claim_boundaries(self) -> None:
        report = bundle.build_report({"bundle_report": self.incomplete_bundle_report()})

        self.assertEqual(report["bundle_status"], "incomplete")
        self.assertEqual(report["bundle_summary"]["status"], "incomplete")
        self.assertEqual(report["post_run_interpretation_gate_report"]["interpretation_status"], "inconclusive_conditional_diagnostic")
        self.assertEqual(report["failure_taxonomy_report"]["taxonomy_status"], "scope_limited")
        self.assertEqual(report["gis_cog_readiness_report"]["gis_cog_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])
        self.assertIn("scope-limited", report["bundle_summary"]["summary"])

    def test_missing_inputs_bundle_is_blocked(self) -> None:
        report = bundle.build_report({"missing_inputs": ["single_job_execution_summary", "gis_cog_readiness_report"]})

        self.assertEqual(report["bundle_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["single_job_execution_summary", "gis_cog_readiness_report"])
        self.assertEqual(report["bundle_summary"]["blockers"], ["single_job_execution_summary", "gis_cog_readiness_report"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_cli_writes_json_and_text_bundle_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            override_path = self.write_json({"bundle_report": self.complete_bundle_report()})
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"

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
            json_path = artifact_dir / "balfrin_evidence_bundle_v1.json"
            text_path = artifact_dir / "balfrin_evidence_bundle_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            json_report = json.loads(json_path.read_text(encoding="utf-8"))
            text_report = text_path.read_text(encoding="utf-8")
            self.assertEqual(json_report["bundle_status"], "complete")
            self.assertIn("Balfrin Evidence Bundle", text_report)
            self.assertIn("canonical_bundle_path:", text_report)
            self.assertIn("operational_claims_allowed: False", text_report)

    def test_gis_cog_parity_report_marks_ready_package_as_ready(self) -> None:
        report = bundle.build_bundle_report(
            single_job_summary=self.single_job_summary(),
            probe_metrics=self.probe_metrics(),
            post_run_report=self.post_run_report(),
            gis_report=self.ready_gis_report(),
            source_paths={"single_job_record_paths": {}, "post_run_contract_path": "validation/pilot_runs/contract.yaml"},
            canonical_bundle_path=Path("validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"),
        )

        parity = report["gis_cog_parity_report"]
        self.assertEqual(parity["parity_status"], "ready")
        self.assertEqual(parity["layer_counts"]["standard"]["validation_balfrin_probe"], 22)
        self.assertEqual(parity["cog_metadata"]["standard_package_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(parity["curve_linkage"]["status"], "linked")
        self.assertEqual(parity["curve_linkage"]["conditional_curve_row_count"], 729600)
        self.assertEqual(parity["manifest_consistency"]["status"], "consistent")
        self.assertEqual(parity["scope_delta"]["status"], "parity_match")
        self.assertEqual(report["gis_cog_scope_report"]["scope_status"], "full_scope")
        self.assertEqual(report["gis_cog_scope_report"]["scope_delta_status"], "parity_match")

    def test_gis_cog_parity_report_marks_missing_inputs_as_blocked(self) -> None:
        report = bundle.build_bundle_report(
            single_job_summary=self.single_job_summary(curve_row_count=None),
            probe_metrics=self.probe_metrics(),
            post_run_report=self.post_run_report(),
            gis_report=self.blocked_gis_report(),
            source_paths={"single_job_record_paths": {}, "post_run_contract_path": "validation/pilot_runs/contract.yaml"},
            canonical_bundle_path=Path("validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"),
        )

        parity = report["gis_cog_parity_report"]
        self.assertEqual(parity["parity_status"], "blocked_missing_inputs")
        self.assertEqual(parity["curve_linkage"]["status"], "blocked_missing_inputs")
        self.assertEqual(parity["manifest_consistency"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["gis_cog_scope_report"]["scope_status"], "blocked_missing_inputs")
        self.assertEqual(report["gis_cog_scope_report"]["scope_delta_status"], "parity_match")

    def test_gis_cog_parity_report_marks_scope_delta_as_bounded_scope(self) -> None:
        report = bundle.build_bundle_report(
            single_job_summary=self.single_job_summary(),
            probe_metrics=self.probe_metrics(),
            post_run_report=self.post_run_report(),
            gis_report=self.bounded_scope_gis_report(),
            source_paths={"single_job_record_paths": {}, "post_run_contract_path": "validation/pilot_runs/contract.yaml"},
            canonical_bundle_path=Path("validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"),
        )

        parity = report["gis_cog_parity_report"]
        self.assertEqual(parity["parity_status"], "bounded_scope")
        self.assertEqual(parity["scope_delta"]["status"], "scope_delta")
        self.assertEqual(parity["scope_delta"]["converted_package_layer_inventory_status"], "scope_reduced")
        self.assertEqual(parity["layer_counts"]["converted"]["validation_balfrin_probe"], 20)
        self.assertEqual(parity["curve_linkage"]["status"], "linked")
        self.assertEqual(report["gis_cog_scope_report"]["scope_status"], "bounded_scope")
        self.assertEqual(report["gis_cog_scope_report"]["scope_delta_status"], "scope_delta")
        self.assertEqual(
            report["gis_cog_scope_report"]["converted_package_scope_deltas"]["validation_balfrin_probe"]["missing_layer_names"],
            ["jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"],
        )

    def test_current_report_is_measured_and_tracks_section_provenance(self) -> None:
        report = bundle.build_current_report()

        self.assertEqual(report["bundle_status"], "measured")
        self.assertEqual(report["bundle_provenance_status"], "measured")
        self.assertEqual(
            report["bundle_summary"]["section_counts"],
            {"measured": 6, "fixture_backed": 0, "blocked_missing_inputs": 0},
        )
        self.assertTrue(all(section["evidence_type"] == "measured" for section in report["section_provenance_profile"]))
        self.assertEqual(report["probe_metrics"]["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(report["gis_cog_scope_report"]["scope_status"], "full_scope")
        self.assertEqual(report["gis_cog_scope_report"]["scope_delta_status"], "parity_match")
        self.assertIn("section_provenance_profile:", bundle.render_text_report(report))
        self.assertIn("bundle_provenance_status: measured", bundle.render_text_report(report))
        self.assertIn("metrics_completion_source:", bundle.render_text_report(report))
        self.assertEqual(
            report["probe_metrics"]["ancillary_unavailable_metrics"],
            ["validation_output_mode", "output_write_kind_seconds", "output_write_kind_bytes"],
        )
        self.assertEqual(report["probe_metrics"]["ancillary_metrics"]["validation_output_mode"]["status"], "unavailable")
        self.assertEqual(report["probe_metrics"]["ancillary_metrics"]["output_write_kind_seconds"]["status"], "unavailable")
        self.assertEqual(report["probe_metrics"]["ancillary_metrics"]["output_write_kind_bytes"]["status"], "unavailable")
        self.assertEqual(report["probe_metrics"]["metric_statuses"]["mandatory"]["wall_time_seconds"]["status"], "measured")
        self.assertEqual(report["probe_metrics"]["metric_statuses"]["mandatory"]["memory_peak_mb"]["status"], "measured")
        self.assertEqual(report["probe_metrics"]["metric_statuses"]["ancillary"]["validation_output_mode"]["status"], "unavailable")
        self.assertEqual(
            report["probe_metrics"]["metric_statuses"]["unavailable"],
            ["output_write_kind_bytes", "output_write_kind_seconds", "validation_output_mode"],
        )
        self.assertEqual(report["probe_metrics"]["metric_statuses"]["blocked"], [])
        self.assertEqual(report["probe_metrics"]["metrics_remediation"]["missing_mandatory_metrics"], [])
        self.assertEqual(
            report["probe_metrics"]["metrics_remediation"]["unavailable_ancillary_metrics"],
            ["validation_output_mode", "output_write_kind_seconds", "output_write_kind_bytes"],
        )
        self.assertEqual(
            report["probe_metrics"]["metrics_remediation"]["next_run_required_metrics"],
            ["validation_output_mode", "output_write_kind_seconds", "output_write_kind_bytes"],
        )
        self.assertEqual(
            [item["metric"] for item in report["probe_metrics"]["metrics_remediation"]["next_run_collection_checklist"]],
            ["validation_output_mode", "output_write_kind_seconds", "output_write_kind_bytes"],
        )
        self.assertIn("ancillary unavailable states", report["bundle_summary"]["summary"])
        self.assertIn("metric_statuses:", bundle.render_text_report(report))
        self.assertIn("ancillary_unavailable_metrics:", bundle.render_text_report(report))
        self.assertIn("metrics_remediation:", bundle.render_text_report(report))

    def test_current_multi_zone_evidence_records_tb267_blocker(self) -> None:
        report = bundle.build_current_report()
        multi_zone = report["multi_zone_balfrin_evidence"]

        self.assertEqual(multi_zone["status"], "blocked_incomplete")
        self.assertEqual(multi_zone["evidence_type"], "blocked")
        self.assertEqual(multi_zone["preflight_status"], "blocked_reducer_budget")
        self.assertEqual(multi_zone["first_bottleneck_label"], "manifest_size_bytes")
        self.assertIsNone(multi_zone["slurm_job_id"])
        self.assertFalse(multi_zone["metrics_json_promoted"])
        self.assertFalse(multi_zone["preservation_gate_promoted"])
        self.assertFalse(multi_zone["post_run_collector_promoted"])
        self.assertIn("multi_zone_balfrin_evidence:", bundle.render_text_report(report))

    def test_multi_zone_evidence_classifier_distinguishes_root_classes(self) -> None:
        scratch = bundle.build_multi_zone_balfrin_evidence(
            {"probe_status": "measured_scratch_root", "run_root": "/tmp/rust_rockfall/probe"}
        )
        fixture = bundle.build_multi_zone_balfrin_evidence(
            {"run_root": "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"}
        )
        measured = bundle.build_multi_zone_balfrin_evidence(
            {
                "status": "measured",
                "run_root": "/scratch/rust_rockfall/probes/balfrin-demo/two_zone",
                "release_zone_count": 2,
                "metrics_json_promoted": True,
                "preservation_checked": True,
                "preservation_gate_promoted": True,
                "post_run_collector_promoted": True,
            }
        )

        self.assertEqual(scratch["root_class"], "scratch_reducer_probe")
        self.assertEqual(scratch["evidence_type"], "fixture_backed")
        self.assertEqual(fixture["root_class"], "fixture_backed_multi_zone_root")
        self.assertEqual(fixture["evidence_type"], "fixture_backed")
        self.assertEqual(measured["root_class"], "measured_multi_zone_balfrin_root")
        self.assertEqual(measured["evidence_type"], "measured")

    def test_metrics_evidence_state_propagates_recovered_run_root_fields(self) -> None:
        summary = self.single_job_summary()
        summary["metrics_contract"]["status"] = "complete"
        summary["metrics_contract"]["mandatory_metrics"].update(
            {
                "memory_peak_mb": {"value": 512.5},
                "validation_output": {"file_count": 2005, "bytes": 571377719},
                "hazard_output": {"file_count": 46, "bytes": 16613900},
            }
        )
        summary["run_root_hashes"] = {
            "run_root_manifest_sha256": "abc123",
            "command_plan_sha256": "def456",
        }
        summary["submission_report"] = {
            "submitted_job_id": "4329024",
            "slurm_state": "COMPLETED",
            "exit_code": "0:0",
            "MaxRSS": "525M",
        }
        summary["preservation_gate_report"] = {"gate_status": "ready_for_demonstration_evidence"}
        summary["preservation_checked"] = True

        metrics = bundle.build_probe_metrics(summary)
        state = metrics["metrics_evidence_state"]

        self.assertEqual(metrics["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(state["metrics_completion_source"], "recovered_existing_run_root")
        self.assertEqual(state["memory_peak_mb"], 512.5)
        self.assertEqual(state["validation_output"], {"file_count": 2005, "bytes": 571377719})
        self.assertEqual(state["hazard_output"], {"file_count": 46, "bytes": 16613900})
        self.assertEqual(state["run_root_hashes"]["run_root_manifest_sha256"], "abc123")
        self.assertEqual(state["slurm"]["job_id"], "4329024")
        self.assertEqual(state["slurm"]["state"], "COMPLETED")
        self.assertEqual(state["slurm"]["max_rss"], "525M")
        self.assertEqual(state["preservation_status"], "ready_for_demonstration_evidence")
        self.assertTrue(state["preservation_checked"])

    def test_metrics_evidence_state_accepts_new_rerun_and_blocked_pre_submit_classifiers(self) -> None:
        summary = self.single_job_summary()
        summary["metrics_completion_source"] = "new_metrics_completion_rerun"
        summary["metrics_contract"]["status"] = "complete"
        summary["metrics_contract"]["mandatory_metrics"].update(
            {
                "memory_peak_mb": {"value": 640.0},
                "validation_output": {"file_count": 2100, "bytes": 600000000},
                "hazard_output": {"file_count": 50, "bytes": 20000000},
            }
        )
        rerun_metrics = bundle.build_probe_metrics(summary)
        self.assertEqual(rerun_metrics["metrics_completion_source"], "new_metrics_completion_rerun")
        self.assertEqual(rerun_metrics["metrics_completion_outcome"], "measured")
        self.assertEqual(rerun_metrics["metrics_evidence_state"]["memory_peak_mb"], 640.0)

        blocked_summary = self.single_job_summary()
        blocked_summary["metrics_completion_source"] = "blocked_pre_submit"
        blocked_summary["metrics_contract"]["status"] = "blocked_missing_inputs"
        blocked_summary["metrics_contract"]["metrics_completion_attempt_status"] = "blocked_remote_checkout_dirty"
        blocked_metrics = bundle.build_probe_metrics(blocked_summary)
        self.assertEqual(blocked_metrics["metrics_completion_source"], "blocked_pre_submit")
        self.assertEqual(blocked_metrics["metrics_completion_outcome"], "incomplete")
        self.assertEqual(
            blocked_metrics["metrics_evidence_state"]["metrics_completion_attempt_status"],
            "blocked_remote_checkout_dirty",
        )

    def test_fixture_backed_override_stays_fixture_backed(self) -> None:
        fixture_path = "tests/fixtures/balfrin_restartability_recovery/fixture_v1.json"
        report = bundle.build_report(
            {
                "single_job_execution_summary": {
                    "metrics_contract": {
                        "status": "complete",
                        "mandatory_metrics": {
                            "wall_time_seconds": {"value": 10.0},
                            "memory_peak_mb": {"value": 12.0},
                            "validation_output": {"file_count": 2, "bytes": 10},
                            "hazard_output": {"file_count": 2, "bytes": 10},
                            "reduced_output_family_counts": {"validation_output_mode": "summary_only"},
                            "conditional_curve_row_count": 1,
                            "restartability_metadata": {
                                "trajectory_plan_id": "fixture-trajectory-plan",
                                "reducer_plan_id": "fixture-reducer-plan",
                            },
                        },
                    },
                    "decision": "defer",
                    "single_job_sufficient_for_next_step": True,
                    "record_paths": {"repeatability_record": fixture_path},
                    "submission_report": {"submitted_job_id": "fixture-job-1", "status": "submitted"},
                    "runtime_report": {"status": "complete"},
                    "validation_output_blocker_status": "clear",
                },
                "probe_metrics": {
                    "status": "complete",
                    "metrics_contract_status": "complete",
                    "metrics_contract_missing_metrics": [],
                    "log_audit": {"error_like_line_count": 0},
                    "run_root": fixture_path,
                    "probe_manifest_path": fixture_path,
                    "command_plan_path": fixture_path,
                    "hazard_manifest_path": fixture_path,
                    "output_root": fixture_path,
                },
                "post_run_interpretation_gate_report": {
                    "interpretation_status": "measured_conditional_diagnostic",
                    "artifact_acceptance_status": "accepted_conditional_diagnostic",
                    "readiness_check": {"status": "ready"},
                    "convergence_stability_check": {"status": "measured"},
                    "output_check": {"status": "measured"},
                    "gis_cog_check": {"status": "gis_package_ready"},
                    "physical_credibility_check": {"status": "not_established"},
                    "claim_boundaries": {
                        "operational_claims_allowed": False,
                        "physical_probability_claims_allowed": False,
                        "annual_frequency_claims_allowed": False,
                        "risk_exposure_vulnerability_claims_allowed": False,
                        "scale_up_authorized": False,
                        "distributed_execution_authorized": False,
                    },
                },
                "gis_cog_readiness_report": {
                    "gis_cog_readiness_status": "gis_package_ready",
                    "artifact_roots": [fixture_path],
                    "hazard_manifest_paths": {"fixture": fixture_path},
                    "map_package_manifest_paths": {"fixture": fixture_path},
                    "pilot_gis_package_manifest_paths": {"fixture": fixture_path},
                    "standard_package_readiness_status": "gis_package_ready",
                    "converted_package_readiness_status": "gis_package_ready",
                    "converted_package_layer_inventory_status": "scope_reduced",
                    "converted_package_scope_deltas": {"fixture": {"status": "scope_delta"}},
                    "standard_package_layer_counts": {},
                    "converted_package_layer_counts": {},
                    "cog_readiness_indicators": {},
                },
                "source_paths": {
                    "single_job_record_paths": {
                        "repeatability_record": fixture_path,
                    },
                    "post_run_contract_path": fixture_path,
                    "gis_artifact_roots": [fixture_path],
                },
            }
        )

        self.assertEqual(report["bundle_status"], "fixture_backed")
        self.assertEqual(report["bundle_provenance_status"], "fixture_backed")
        self.assertTrue(all(section["evidence_type"] == "fixture_backed" for section in report["section_provenance_profile"]))
        self.assertEqual(report["bundle_summary"]["section_counts"]["fixture_backed"], 6)
        self.assertIn("fixture-backed rather than measured", report["bundle_summary"]["summary"])

    def test_blocked_override_marks_sections_blocked(self) -> None:
        report = bundle.build_report({"missing_inputs": ["probe_metrics"]})

        self.assertEqual(report["bundle_status"], "blocked_missing_inputs")
        self.assertEqual(report["bundle_provenance_status"], "blocked_missing_inputs")
        self.assertEqual(report["bundle_summary"]["section_counts"]["blocked_missing_inputs"], 6)
        self.assertTrue(all(section["evidence_type"] == "blocked" for section in report["section_provenance_profile"]))
        self.assertIn("required evidence inputs are missing", bundle.render_text_report(report))

    def complete_bundle_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_evidence_bundle_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_balfrin_single_release_zone_v1",
            "canonical_bundle_path": "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1",
            "bundle_status": "complete",
            "bundle_summary": {
                "status": "complete",
                "summary": (
                    "Balfrin readiness, metrics, outputs, GIS / COG status, restartability, and interpretation checks are all present and measurably aligned."
                ),
                "blockers": [],
            },
            "single_job_execution_summary": {
                "schema_version": "balfrin_single_job_execution_sufficiency_v1",
                "decision": "defer",
                "single_job_sufficient_for_next_step": True,
                "metrics_contract": {"status": "complete"},
            },
            "probe_metrics": {
                "status": "complete",
                "wall_time_seconds": 17.84,
                "memory_peak_mb": 409.22,
            },
            "post_run_interpretation_gate_report": {
                "schema_version": "balfrin_post_run_interpretation_gate_v1",
                "interpretation_status": "measured_conditional_diagnostic",
                "artifact_acceptance_status": "accepted_conditional_diagnostic",
                "usable_as_conditional_diagnostic_artifact": True,
                "claim_boundaries": self.claim_boundaries(),
            },
            "failure_taxonomy_report": {
                "schema_version": "balfrin_failure_taxonomy_v1",
                "taxonomy_status": "scope_limited",
                "status_counts": {"observed": 0, "scope_limited": 0, "clear": 0, "not_observed": 0},
                "observed_failure_classes": [],
                "scope_limited_failure_classes": [],
                "failure_classes": [],
                "claim_boundaries": self.claim_boundaries(),
            },
            "gis_cog_readiness_report": {
                "schema_version": "tschamut_gis_cog_package_readiness_v1",
                "gis_cog_readiness_status": "gis_package_ready",
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
            },
            "claim_boundaries": self.claim_boundaries(),
            "source_paths": {"single_job_record_paths": {}, "post_run_contract_path": "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml"},
            "evidence_sources": [
                "scripts/summarize_balfrin_single_job_execution.py",
                "scripts/summarize_balfrin_post_run_interpretation_gate.py",
                "scripts/audit_gis_cog_package_readiness.py",
                "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1",
            ],
            "missing_inputs": [],
        }

    def incomplete_bundle_report(self) -> dict[str, object]:
        report = self.complete_bundle_report()
        report["bundle_status"] = "incomplete"
        report["bundle_summary"] = {
            "status": "incomplete",
            "summary": (
                "Balfrin evidence is present, but one or more sections remain inconclusive or scope-limited; the bundle keeps the diagnostic boundaries explicit."
            ),
            "blockers": [],
        }
        report["post_run_interpretation_gate_report"] = {
            "schema_version": "balfrin_post_run_interpretation_gate_v1",
            "interpretation_status": "inconclusive_conditional_diagnostic",
            "artifact_acceptance_status": "accepted_conditional_diagnostic",
            "usable_as_conditional_diagnostic_artifact": True,
            "claim_boundaries": self.claim_boundaries(),
        }
        report["failure_taxonomy_report"] = {
            "schema_version": "balfrin_failure_taxonomy_v1",
            "taxonomy_status": "scope_limited",
            "status_counts": {"observed": 0, "scope_limited": 0, "clear": 0, "not_observed": 0},
            "observed_failure_classes": [],
            "scope_limited_failure_classes": [],
            "failure_classes": [],
            "claim_boundaries": self.claim_boundaries(),
        }
        report["gis_cog_readiness_report"] = {
            "schema_version": "tschamut_gis_cog_package_readiness_v1",
            "gis_cog_readiness_status": "gis_package_ready_cog_blocked",
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
        }
        return report

    def ready_gis_report(self) -> dict[str, object]:
        artifact_id = "validation_balfrin_probe"
        return {
            "schema_version": "tschamut_gis_cog_package_readiness_v1",
            "gis_cog_readiness_status": "gis_package_ready_cog_blocked",
            "readiness_status": "gis_package_ready_cog_blocked",
            "standard_package_readiness_status": "gis_package_ready_cog_blocked",
            "standard_package_layer_counts": {artifact_id: 22},
            "standard_package_status": {artifact_id: "gis_package_ready_cog_blocked"},
            "converted_package_readiness_status": "not_provided",
            "converted_package_layer_inventory_status": "not_provided",
            "converted_package_layer_counts": {},
            "converted_package_status": {},
            "converted_package_scope_boundaries": {},
            "converted_package_scope_deltas": {},
            "hazard_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_manifest.json",
            },
            "map_package_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_map_package_manifest.json",
            },
            "pilot_gis_package_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_pilot_gis_package_manifest.json",
            },
            "cog_readiness_indicators": {
                "gdalinfo_available": True,
                "sample_raster_cog_layout": True,
                "sample_raster_tiled": True,
                "sample_raster_overviews": True,
            },
            "converted_sample_status": "not_provided",
            "qgis_manual_qa_status": "not_run",
            "artifacts_audited": 1,
            "artifact_roots": ["hazard/results/tschamut_public_pilot/balfrin_demo_v1"],
        }

    def blocked_gis_report(self) -> dict[str, object]:
        return {
            "schema_version": "tschamut_gis_cog_package_readiness_v1",
            "gis_cog_readiness_status": "blocked_missing_inputs",
            "readiness_status": "blocked_missing_inputs",
            "standard_package_readiness_status": "blocked_missing_inputs",
            "standard_package_layer_counts": {},
            "standard_package_status": {},
            "converted_package_readiness_status": "not_provided",
            "converted_package_layer_inventory_status": "not_provided",
            "converted_package_layer_counts": {},
            "converted_package_status": {},
            "converted_package_scope_boundaries": {},
            "converted_package_scope_deltas": {},
            "hazard_manifest_paths": {},
            "map_package_manifest_paths": {},
            "pilot_gis_package_manifest_paths": {},
            "cog_readiness_indicators": {
                "gdalinfo_available": False,
                "sample_raster_cog_layout": False,
                "sample_raster_tiled": False,
                "sample_raster_overviews": False,
            },
            "converted_sample_status": "blocked_missing_inputs",
            "qgis_manual_qa_status": "not_run",
            "artifacts_audited": 0,
            "artifact_roots": [],
        }

    def bounded_scope_gis_report(self) -> dict[str, object]:
        artifact_id = "validation_balfrin_probe"
        return {
            "schema_version": "tschamut_gis_cog_package_readiness_v1",
            "gis_cog_readiness_status": "gis_package_ready_cog_blocked",
            "readiness_status": "gis_package_ready_cog_blocked",
            "standard_package_readiness_status": "gis_package_ready_cog_blocked",
            "standard_package_layer_counts": {artifact_id: 22},
            "standard_package_status": {artifact_id: "gis_package_ready_cog_blocked"},
            "converted_package_readiness_status": "cog_package_ready_with_scope_delta",
            "converted_package_layer_inventory_status": "scope_reduced",
            "converted_package_layer_counts": {artifact_id: 20},
            "converted_package_status": {artifact_id: "cog_package_ready_with_scope_delta"},
            "converted_package_scope_boundaries": {
                artifact_id: {
                    "status": "bounded_scope",
                    "reference_layer_count": 22,
                    "exported_layer_count": 20,
                    "omitted_layer_count": 2,
                    "extra_layer_count": 0,
                }
            },
            "converted_package_scope_deltas": {
                artifact_id: {
                    "status": "scope_delta",
                    "missing_layer_count": 2,
                    "missing_layer_names": ["jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"],
                    "extra_layer_count": 0,
                    "extra_layer_names": [],
                }
            },
            "hazard_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_manifest.json",
            },
            "map_package_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_map_package_manifest.json",
            },
            "pilot_gis_package_manifest_paths": {
                artifact_id: "hazard/results/tschamut_public_pilot/balfrin_demo_v1/validation_balfrin_probe_pilot_gis_package_manifest.json",
            },
            "cog_readiness_indicators": {
                "gdalinfo_available": True,
                "sample_raster_cog_layout": True,
                "sample_raster_tiled": True,
                "sample_raster_overviews": True,
            },
            "converted_sample_status": "cog_conversion_sample_ready",
            "qgis_manual_qa_status": "not_run",
            "artifacts_audited": 1,
            "artifact_roots": ["hazard/results/tschamut_public_pilot/balfrin_demo_v1"],
        }

    def single_job_summary(self, *, curve_row_count: int | None = 729600) -> dict[str, object]:
        return {
            "schema_version": "balfrin_single_job_execution_sufficiency_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "decision": "defer",
            "single_job_sufficient_for_next_step": True,
            "metrics_contract": {
                "status": "complete",
                "mandatory_metrics": {
                    "conditional_curve_row_count": curve_row_count,
                    "restartability_metadata": {
                        "trajectory_plan_id": "trajectory-plan",
                        "reducer_plan_id": "reducer-plan",
                    },
                },
            },
            "record_paths": {},
        }

    def probe_metrics(self) -> dict[str, object]:
        return {
            "status": "complete",
            "wall_time_seconds": 17.84,
            "memory_peak_mb": 409.22,
            "validation_output": {"file_count": 2005, "bytes": 571377719},
            "hazard_output": {"file_count": 46, "bytes": 16613900},
        }

    def post_run_report(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_post_run_interpretation_gate_v1",
            "interpretation_status": "measured_conditional_diagnostic",
            "artifact_acceptance_status": "accepted_conditional_diagnostic",
            "usable_as_conditional_diagnostic_artifact": True,
            "claim_boundaries": self.claim_boundaries(),
        }

    def claim_boundaries(self) -> dict[str, bool]:
        return {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        }


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
