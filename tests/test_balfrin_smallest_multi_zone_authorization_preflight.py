from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "preflight_balfrin_smallest_multi_zone_probe_authorization",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BalfrinSmallestMultiZoneAuthorizationPreflightTests(unittest.TestCase):
    def _ready_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "ready_for_read_only_collection",
            "ready_for_read_only_collection": True,
            "ready_for_pre_submit": True,
            "remote_head": "abc123",
            "remote_checkout_hygiene": {
                "status": "pass",
                "remote_head": "abc123",
                "tracked_modifications": [],
                "untracked_generated_files": [],
                "stale_submission_packages": [],
                "stale_logs": [],
                "dirty_path_count": 0,
                "safe_cleanup_commands": ["git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all"],
            },
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [{"name": "ssh_availability", "status": "pass"}],
        }

    def _expired_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "blocked_ssh_unavailable",
            "ready_for_read_only_collection": False,
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [{"name": "ssh_availability", "status": "fail"}],
        }

    def _write_package(
        self,
        path: Path,
        *,
        reducer_status: str = "acceptable",
        compact_handoff_budget_status: str | None = None,
        budget_acceptance_status: str = "accepted",
        review_readiness_classification: str = "ready_for_review",
        review_readiness_reason: str = (
            "four-zone review package is ready for review with compact manifests, reduced-output defaults, "
            "objective budget validation, and replay-critical families retained"
        ),
    ) -> str:
        budget_acceptance_validation = {
            "schema_version": "balfrin_multi_zone_output_budget_acceptance_v1",
            "status": budget_acceptance_status,
            "threshold_profile_id": "smallest_live_two_zone_probe",
            "failures": [],
            "exceeded_thresholds": [],
            "compressible_excesses": [],
            "replay_critical_excesses": [],
            "summary": "output budget accepted",
        }
        if budget_acceptance_status == "blocked_threshold_exceeded":
            failure = {
                "metric": "manifest_size_bytes",
                "measured": 11001,
                "threshold": 11000,
                "excess": 1,
                "excess_classification": "compressible",
                "replay_critical": False,
                "compressible": True,
                "reason": "manifest_size_bytes=11001 exceeds smallest_live_two_zone_probe.max_manifest_size_bytes=11000",
            }
            budget_acceptance_validation.update(
                {
                    "failures": [failure],
                    "exceeded_thresholds": ["manifest_size_bytes"],
                    "compressible_excesses": [failure],
                    "summary": failure["reason"],
                }
            )
        constraint = {
            "status": reducer_status,
            "summary": f"{reducer_status}: requested multi-zone settings stay within measured reducer constraints",
            "constraint_source": {
                "source_document": "docs/multi_zone_reducer_pressure_probe.md",
                "source_script": "scripts/summarize_multi_zone_reducer_pressure.py",
            },
            "requested_release_zone_batch_size": 2,
            "requested_reducer_chunk_count": 2,
            "requested_reducer_worker_count": 2,
            "measured_constraints": {
                "simultaneous_release_zone_batch_max": 8,
                "reducer_chunk_count_max": 4,
                "reducer_worker_count_max": 2,
            },
            "constraint_checks": [
                {
                    "label": "simultaneous_release_zone_batch_size",
                    "status": "acceptable" if reducer_status != "blocked" else "blocked",
                    "requested": 2,
                    "limit": 8,
                    "reason": "requested simultaneous_release_zone_batch_size=2 stays within measured max 8",
                }
            ],
            "handoff_output_budget_projection": {
                "budget_acceptance_validation": budget_acceptance_validation,
                "budget_acceptance_thresholds": {
                    "schema_version": "balfrin_multi_zone_output_budget_acceptance_v1",
                    "profiles": {"smallest_live_two_zone_probe": {"max_manifest_size_bytes": 11000}},
                },
            },
        }
        if reducer_status == "blocked":
            constraint["blocked_reason"] = "requested reducer settings exceed measured max"
        authorization_record_path = path.parent / "authorization.yaml"
        authorization_submit_command = MODULE.handoff.build_authorized_submit_command(
            reviewed_handoff_package_path=path,
            authorization_record_path=authorization_record_path,
        )
        manifest_pruning = None
        if compact_handoff_budget_status is not None:
            compact_projection = {
                "status": "blocked" if compact_handoff_budget_status == "blocked_budget_reduction_needed" else "ready",
                "projection_mode": "compact",
                "manifest_size_bytes": 17788,
                "output_file_count": 39,
                "output_byte_count": 22563,
                "sidecar_file_count": 2,
                "sidecar_byte_count": 214,
                "reducer_manifest_file_count": 0,
                "reducer_manifest_bytes": 0,
                "replay_critical_retained_output_families": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
                "first_bottleneck_labels": {
                    "first_blocked": "manifest_size_bytes"
                    if compact_handoff_budget_status == "blocked_budget_reduction_needed"
                    else None,
                    "first_relevant": "manifest_size_bytes"
                    if compact_handoff_budget_status == "blocked_budget_reduction_needed"
                    else "ready",
                    "blocked": ["manifest_size_bytes"]
                    if compact_handoff_budget_status == "blocked_budget_reduction_needed"
                    else [],
                    "warning": [],
                },
                "budget_recheck": {
                    "status": compact_handoff_budget_status,
                    "reason": (
                        "current handoff projection remains blocked at first bottleneck manifest_size_bytes; "
                        "replay-critical families retained: trajectory_csv, deposition_csv, impact_events_csv, "
                        "trajectory_merge_state, reducer_merge_state"
                    ),
                },
                "replay_critical_contract": {
                    "families": [
                        "trajectory_csv",
                        "deposition_csv",
                        "impact_events_csv",
                        "trajectory_merge_state",
                        "reducer_merge_state",
                    ],
                    "merge_order_proof": {
                        "merge_order": "sorted_chunk_id",
                        "merge_order_independent": True,
                        "merge_order_deterministic": True,
                    },
                    "output_profile_semantics": {
                        "classification": "blocked_unscalable_default",
                        "summary": "one or more command-plan profiles request heavy output defaults without an explicit override",
                        "required_scalable_controls": [
                            "--conditional-curve-export summary-only",
                            "--grid-csv-export none",
                            "--no-plots",
                        ],
                        "scalable_policy_labels": ["minimum_measured_multi_zone_run"],
                        "blocked_policy_labels": ["current_target_gate_profile"],
                        "policy_count": 2,
                    },
                },
            }
            compact_projection["budget_acceptance_validation"] = budget_acceptance_validation
            compact_projection["budget_acceptance_thresholds"] = constraint["handoff_output_budget_projection"][
                "budget_acceptance_thresholds"
            ]
            constraint["handoff_output_budget_projection"] = compact_projection
            if compact_handoff_budget_status == "blocked_budget_reduction_needed":
                constraint["status"] = "blocked"
                constraint["summary"] = "handoff output-budget projection blocked at manifest_size_bytes"
                constraint["blocked_reason"] = constraint["summary"]
            manifest_pruning = {
                "status": compact_handoff_budget_status,
                "mode": "compact",
                "before": {
                    "manifest_size_bytes": 24042,
                    "output_file_count": 62,
                    "sidecar_file_count": 21,
                    "sidecar_byte_count": 4123,
                    "reducer_manifest_file_count": 4,
                    "reducer_manifest_bytes": 964,
                },
                "after": {
                    "manifest_size_bytes": 17788,
                    "output_file_count": 39,
                    "sidecar_file_count": 2,
                    "sidecar_byte_count": 214,
                    "reducer_manifest_file_count": 0,
                    "reducer_manifest_bytes": 0,
                },
                "exact_blocking_fields": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
                "replay_critical_contract": compact_projection["replay_critical_contract"],
                "blocked_reason": compact_projection["budget_recheck"]["reason"],
            }
        payload = {
            "schema_version": "balfrin_multi_release_zone_demo_package_v1",
            "package_status": "mixed_provenance",
            "submission_classification": "blocked_pending_new_human_authorization",
            "authorization_classification": "blocked_pending_authorization",
            "live_execution_requires_new_human_authorization": True,
            "package_constraint_status": constraint["status"],
            "constraint_pressure": constraint,
            "output_budget_acceptance_validation": budget_acceptance_validation,
            "output_budget_acceptance_thresholds": constraint["handoff_output_budget_projection"][
                "budget_acceptance_thresholds"
            ],
            "follow_up_recommendation": {
                "minimum_measured_multi_zone_run": {
                    "release_zone_count": 2,
                    "scenario_count": 2,
                    "trajectory_count_target": 1000,
                    "trajectory_workers": 2,
                    "reducer_workers": 2,
                    "conditional_curve_export": "summary-only",
                    "grid_csv_export": "none",
                    "export_geotiff": True,
                    "pilot_gis_package": True,
                    "output_profile_policy": {"classification": "scalable_default"},
                    "estimated_runtime_seconds": 0.498,
                    "estimated_storage_bytes": 5174,
                    "estimated_file_count": 10,
                    "estimated_manifest_pressure_bytes": 3350,
                    "preservation_gate_checklist": [
                        "Review the package JSON and Markdown together before any later authorization request.",
                        "Do not submit a live Balfrin job unless the conversation explicitly authorizes execution later.",
                    ],
                    "reducer_pressure": constraint,
                    "authorization_submit_command": authorization_submit_command,
                }
            },
        }
        payload["four_zone_hazard_execution_package"] = {
            "status": review_readiness_classification,
            "readiness_classification": review_readiness_classification,
            "readiness_reason": review_readiness_reason,
            "command_plan": {
                "schema_version": "balfrin_multi_release_zone_demo_command_plan_v1",
                "command_plan_status": "mixed_provenance",
                "command_plan_source": "scripts/generate_balfrin_multi_release_zone_demo_handoff.py",
                "command_plan_source_command": "PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --format json",
                "command_count": 6,
                "command_ids": [
                    "candidate_stability_sweep",
                    "target_area_handoff_bundle",
                    "multi_zone_reducer_pressure_summary",
                    "scientific_delta_report",
                    "authorization_review_command",
                    "package_materialization",
                ],
                "blocked_template_commands": [],
                "output_profile_policy": {"classification": "blocked_unscalable_default"},
            },
            "authorization_audit_record": {
                "status": "reviewed",
                "reviewed_handoff_package_path": str(path.resolve()),
                "authorization_record_path": str(authorization_record_path.resolve()),
                "authorization_review_command": MODULE.handoff.build_authorized_submit_command(
                    reviewed_handoff_package_path=path,
                    authorization_record_path=authorization_record_path,
                ),
                "authorization_submit_command": authorization_submit_command,
                "reviewed_handoff_package_sha256": None,
                "live_execution_requires_new_human_authorization": True,
            },
            "reduced_output_settings": {
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "no_plots": True,
                "output_profile_policy": {"classification": "scalable_default"},
            },
            "expected_output_budget": {
                "status": budget_acceptance_status,
                "threshold_profile_id": "next_larger_four_zone_review_only_probe",
                "summary": budget_acceptance_validation["summary"],
                "thresholds": {
                    "schema_version": "balfrin_multi_zone_output_budget_acceptance_v1",
                    "profiles": {"next_larger_four_zone_review_only_probe": {"max_manifest_size_bytes": 14000}},
                },
                "validation": budget_acceptance_validation,
                "projection": {
                    "status": "acceptable",
                    "projection_mode": "compact",
                    "manifest_size_bytes": 17788,
                    "output_file_count": 39,
                    "sidecar_file_count": 2,
                },
                "manifest_pruning_status": compact_handoff_budget_status or "budget_passes_no_reduction_needed",
                "manifest_pruning_summary": (
                    "current handoff projection stays within the current budget thresholds"
                    if compact_handoff_budget_status is None
                    else "handoff output-budget projection blocked at manifest_size_bytes"
                ),
                "manifest_pruning": manifest_pruning or {},
            },
            "preservation_instructions": {
                "status": "ready_for_review" if budget_acceptance_status == "accepted" else "blocked_output_budget",
                "checklist": [
                    "Review the package JSON and Markdown together before any later authorization request.",
                    "Do not submit a live Balfrin job unless the conversation explicitly authorizes execution later.",
                ],
                "ignored_output_roots": [str(path.parent / "scratch"), str(path.parent / "logs")],
                "do_not_commit_paths": [str(path), str(authorization_record_path)],
                "notes": [
                    "Keep generated scratch roots under /tmp or validation/private only.",
                    "Do not commit live Balfrin outputs, scratch-root artifacts, or generated package files.",
                ],
            },
        }
        if manifest_pruning is not None:
            payload["manifest_pruning"] = manifest_pruning
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_authorization(self, path: Path, package_path: Path, package_sha256: str) -> None:
        payload = {
            "schema_version": "balfrin_multi_zone_live_authorization_v1",
            "authorization_status": "authorized_for_one_bounded_probe",
            "authorized_task": "TB-322",
            "no_rerun_without_renewed_authorization": True,
            "reviewed_handoff_package_path": str(package_path.resolve()),
            "reviewed_handoff_package_sha256": package_sha256,
        }
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def test_ready_package_reports_smallest_run_shape_without_granting_authorization(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package)
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "ready_for_authorization_review")
        self.assertTrue(report["ready_for_authorization_review"])
        self.assertTrue(report["ready_for_authorized_submission"])
        self.assertFalse(report["authorization_granted_by_preflight"])
        self.assertFalse(report["live_submission_authorized"])
        self.assertEqual(report["balfrin_access_status"], "ready_for_read_only_collection")
        self.assertTrue(report["balfrin_access_preflight_requirement"]["ready_for_pre_submit"])
        self.assertEqual(report["balfrin_access_preflight_requirement"]["remote_checkout_hygiene"]["status"], "pass")
        self.assertEqual(report["reducer_budget_status"], "ready")
        self.assertEqual(report["output_profile_status"], "ready")
        self.assertEqual(report["submit_contract_status"], "ready")
        self.assertTrue(
            report["submit_contract_requirement"]["probe_manifest_path"].endswith(
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
            )
        )
        self.assertEqual(report["output_budget_acceptance_status"], "accepted")
        self.assertEqual(
            report["reducer_budget_requirement"]["output_budget_acceptance_threshold_profile_id"],
            "smallest_live_two_zone_probe",
        )
        self.assertEqual(report["smallest_multi_zone_run_shape"]["release_zone_count"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["scenario_count"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["reducer_workers"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["reducer_chunk_count"], 2)
        self.assertEqual(
            report["smallest_multi_zone_run_shape"]["output_profile"]["classification"],
            "scalable_default",
        )
        self.assertGreaterEqual(len(report["smallest_multi_zone_run_shape"]["preservation_checklist"]), 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["hazard_package"]["status"], "ready_for_review")
        self.assertGreater(report["smallest_multi_zone_run_shape"]["hazard_package"]["command_plan"]["command_count"], 0)
        self.assertEqual(
            report["smallest_multi_zone_run_shape"]["hazard_package"]["expected_output_budget"]["status"],
            "accepted",
        )
        self.assertTrue(report["smallest_multi_zone_run_shape"]["hazard_package"]["preservation_instructions"]["checklist"])
        text_report = MODULE.render_text_report(report)
        self.assertIn("Before manifest bytes", text_report)
        self.assertIn("Exact blocking fields", text_report)
        self.assertIn("Replay-critical contract families", text_report)
        self.assertIn("Submit contract status", text_report)

    def test_generated_handoff_uses_executable_smallest_submit_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            artifact_dir = Path(tmpdir) / "balfrin_multi_release_zone_demo_v1"
            MODULE.handoff.build_report(
                artifact_dir=artifact_dir,
                pressure_probe_root=artifact_dir / "pressure_probe",
            )
            package = artifact_dir / "balfrin_multi_release_zone_demo_package_v1.json"
            auth = artifact_dir / "balfrin_multi_zone_live_authorization_record_v1.yaml"

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        submit_contract = report["submit_contract_requirement"]
        run_shape = report["smallest_multi_zone_run_shape"]
        command = submit_contract["command"]

        self.assertEqual(report["preflight_status"], "ready_for_authorization_review")
        self.assertEqual(report["submit_contract_status"], "ready")
        self.assertEqual(report["reducer_budget_status"], "ready")
        self.assertEqual(report["output_profile_status"], "ready")
        self.assertTrue(
            submit_contract["probe_manifest_path"].endswith(
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
            )
        )
        self.assertNotIn("validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml", command)
        self.assertNotIn("--run-root /scratch/rust_rockfall", command)
        self.assertEqual(
            submit_contract["run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
        )
        self.assertEqual(submit_contract["run_root_writability_status"], "reviewed_balfrin_scratch_root")
        self.assertEqual(run_shape["release_zone_count"], 2)
        self.assertEqual(run_shape["scenario_count"], 2)
        self.assertEqual(run_shape["output_profile"]["conditional_curve_export"], "summary-only")
        self.assertEqual(run_shape["output_profile"]["grid_csv_export"], "none")
        self.assertEqual(run_shape["output_profile"]["classification"], "scalable_default")
        self.assertEqual(
            report["reducer_budget_requirement"]["output_budget_acceptance_threshold_profile_id"],
            "smallest_live_two_zone_probe",
        )
        self.assertNotEqual(
            report["reducer_budget_requirement"]["output_budget_acceptance_threshold_profile_id"],
            "next_larger_four_zone_review_only_probe",
        )

    def test_four_zone_review_package_efficiency_does_not_block_smallest_two_zone_output_profile(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(
                package,
                review_readiness_classification="blocked_efficiency",
                review_readiness_reason="single-job sufficiency or reducer scaling is not yet ready for the four-zone review package",
            )
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "ready_for_authorization_review")
        self.assertEqual(report["output_profile_status"], "ready")
        self.assertEqual(report["reducer_budget_status"], "ready")
        self.assertEqual(report["submit_contract_status"], "ready")
        self.assertEqual(report["output_budget_acceptance_status"], "accepted")
        self.assertEqual(
            report["smallest_multi_zone_run_shape"]["output_profile"]["classification"],
            "scalable_default",
        )

    def test_missing_authorization_record_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            package_sha = self._write_package(package)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=tmp / "missing_authorization.yaml",
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(package_sha, report["reviewed_handoff_package_sha256"])
        self.assertEqual(report["preflight_status"], "blocked_missing_authorization")
        self.assertIn("authorization record", report["blocked_reason"])
        self.assertFalse(report["ready_for_authorization_review"])
        self.assertFalse(report["ready_for_authorized_submission"])

    def test_stale_authorization_checksum_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package)
            self._write_authorization(auth, package, package_sha)
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["package_summary"] = {"status": "mutated_after_authorization"}
            package.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_missing_authorization")
        self.assertIn("checksum does not match", report["blocked_reason"])
        self.assertNotEqual(report["reviewed_handoff_package_sha256"], package_sha)

    def test_wrong_reviewed_package_schema_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            self._write_package(package)
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["schema_version"] = "wrong_schema_v1"
            package.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_reviewed_package")
        self.assertIn("schema", report["blocked_reason"])
        self.assertFalse(report["ready_for_authorized_submission"])

    def test_unreviewed_unwritable_balfrin_run_root_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            self._write_package(package)
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["follow_up_recommendation"]["minimum_measured_multi_zone_run"][
                "authorization_submit_command"
            ] = (
                "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py "
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml "
                "--run-root /scratch/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 "
                "--run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --authorized-submit "
                f"--reviewed-handoff-package {package} --authorization-record {auth}"
            )
            package.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_submit_contract")
        self.assertEqual(report["submit_contract_status"], "blocked_submit_contract")
        self.assertEqual(report["submit_contract_requirement"]["run_root_writability_status"], "blocked_submit_contract")
        self.assertIn("unreviewed Balfrin scratch root", report["blocked_reason"])

    def test_expired_balfrin_access_status_maps_to_blocked_access_and_preserves_consumed_status(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package)
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._expired_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_access")
        self.assertEqual(
            report["balfrin_access_preflight_requirement"]["consumed_status"],
            "blocked_ssh_unavailable",
        )
        self.assertIn("blocked_ssh_unavailable", report["blocked_reason"])

    def test_target_area_wrapper_submit_contract_fails_closed_before_access(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package)
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["follow_up_recommendation"]["minimum_measured_multi_zone_run"][
                "authorization_submit_command"
            ] = (
                "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py "
                "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml "
                "--run-root /scratch/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 "
                "--run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --authorized-submit "
                f"--reviewed-handoff-package {package} --authorization-record {auth}"
            )
            package.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_submit_contract")
        self.assertEqual(report["submit_contract_status"], "blocked_submit_contract")
        self.assertIn("schema_version must be public_real_site_conditional_pilot_run_v1", report["blocked_reason"])

    def test_dirty_remote_checkout_blocks_multi_zone_pre_submit_gate(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_dirty_remote_checkout"
        access["ready_for_read_only_collection"] = False
        access["ready_for_pre_submit"] = False
        access["remote_checkout_hygiene"] = {
            "status": "fail",
            "remote_head": "deadbeef",
            "tracked_modifications": ["M scripts/submit_balfrin_probe.py"],
            "untracked_generated_files": ["validation/private/tb264/balfrin_submission_package.json"],
            "stale_submission_packages": ["validation/private/tb264/balfrin_submission_package.json"],
            "stale_logs": ["logs/slurm-123.out"],
            "dirty_path_count": 3,
            "safe_cleanup_commands": [
                "git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all",
                "git -C /users/olifu/work/rust_rockfall clean -n -- validation/private/tb264/balfrin_submission_package.json logs/slurm-123.out",
            ],
        }
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package)
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=access,
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_access")
        self.assertIn("blocked_dirty_remote_checkout", report["blocked_reason"])
        requirement = report["balfrin_access_preflight_requirement"]
        self.assertFalse(requirement["ready_for_pre_submit"])
        self.assertEqual(requirement["remote_checkout_hygiene"]["remote_head"], "deadbeef")

    def test_reducer_budget_blocked_path_blocks_submission_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            auth = tmp / "authorization.yaml"
            package_sha = self._write_package(package, reducer_status="blocked")
            self._write_authorization(auth, package, package_sha)

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=auth,
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_reducer_budget")
        self.assertEqual(report["reducer_budget_requirement"]["status"], "blocked_reducer_budget")
        self.assertIn("requested reducer settings", report["blocked_reason"])

    def test_compact_handoff_budget_blocker_precedes_missing_authorization(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            self._write_package(package, compact_handoff_budget_status="blocked_budget_reduction_needed")

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=tmp / "missing_authorization.yaml",
                balfrin_access_preflight=self._ready_access(),
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_reducer_budget")
        self.assertEqual(
            report["reducer_budget_requirement"]["handoff_budget_recheck_status"],
            "blocked_budget_reduction_needed",
        )
        self.assertEqual(report["reducer_budget_requirement"]["manifest_pruning_status"], "blocked_budget_reduction_needed")
        self.assertIn("replay-critical families retained", report["reducer_budget_requirement"]["handoff_budget_recheck_reason"])
        self.assertIn("Before manifest bytes", MODULE.render_text_report(report))
        self.assertIn("manifest_size_bytes", report["blocked_reason"])
        self.assertEqual(report["authorization_record_status"], "missing")
        self.assertEqual(
            report["reducer_budget_requirement"]["manifest_pruning_replay_critical_contract"]["families"],
            ["trajectory_csv", "deposition_csv", "impact_events_csv", "trajectory_merge_state", "reducer_merge_state"],
        )

    def test_threshold_failure_remains_distinct_from_missing_authorization_and_dirty_access(self) -> None:
        access = self._ready_access()
        access["status"] = "blocked_dirty_remote_checkout"
        access["ready_for_pre_submit"] = False
        access["remote_checkout_hygiene"] = {
            "status": "fail",
            "remote_head": "deadbeef",
            "tracked_modifications": [],
            "untracked_generated_files": ["validation/private/tb293/stale.json"],
            "stale_submission_packages": ["validation/private/tb293/stale.json"],
            "stale_logs": [],
            "dirty_path_count": 1,
            "safe_cleanup_commands": ["git -C /users/olifu/work/rust_rockfall status --short --untracked-files=all"],
        }
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            self._write_package(package, budget_acceptance_status="blocked_threshold_exceeded")

            report = MODULE.build_report(
                reviewed_handoff_package=package,
                authorization_record=tmp / "missing_authorization.yaml",
                balfrin_access_preflight=access,
                balfrin_access_preflight_source="fixture",
            )

        self.assertEqual(report["preflight_status"], "blocked_reducer_budget")
        self.assertEqual(report["authorization_record_status"], "missing")
        self.assertEqual(report["balfrin_access_status"], "blocked_dirty_remote_checkout")
        self.assertEqual(report["output_budget_acceptance_status"], "blocked_threshold_exceeded")
        self.assertIn("manifest_size_bytes", report["blocked_reason"])
        self.assertEqual(
            report["output_budget_acceptance_validation"]["failures"][0]["excess_classification"],
            "compressible",
        )

    def test_budget_threshold_validation_mode_ignores_missing_authorization_and_access(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            tmp = Path(tmpdir)
            package = tmp / "reviewed_package.json"
            self._write_package(package, budget_acceptance_status="blocked_threshold_exceeded")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--reviewed-handoff-package",
                        str(package),
                        "--authorization-record",
                        str(tmp / "missing_authorization.yaml"),
                        "--validation-mode",
                        "budget-thresholds",
                        "--format",
                        "json",
                    ]
                )

        self.assertEqual(exit_code, 2)
        validation = json.loads(buffer.getvalue())
        self.assertEqual(validation["status"], "blocked_threshold_exceeded")
        self.assertEqual(validation["threshold_profile_id"], "smallest_live_two_zone_probe")
        self.assertIn("manifest_size_bytes", validation["summary"])


if __name__ == "__main__":
    unittest.main()
