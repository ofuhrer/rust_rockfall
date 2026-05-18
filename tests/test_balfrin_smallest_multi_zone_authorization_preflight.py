from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
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
    ) -> str:
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
        }
        if reducer_status == "blocked":
            constraint["blocked_reason"] = "requested reducer settings exceed measured max"
        manifest_pruning = None
        if compact_handoff_budget_status is not None:
            compact_projection = {
                "status": "blocked" if compact_handoff_budget_status == "blocked_budget_reduction_needed" else "ready",
                "projection_mode": "compact",
                "manifest_size_bytes": 17788,
                "output_file_count": 39,
                "sidecar_file_count": 2,
                "reducer_manifest_bytes": 0,
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
                    "reason": "current handoff projection remains blocked at first bottleneck manifest_size_bytes",
                },
            }
            constraint["handoff_output_budget_projection"] = compact_projection
            if compact_handoff_budget_status == "blocked_budget_reduction_needed":
                constraint["status"] = "blocked"
                constraint["summary"] = "handoff output-budget projection blocked at manifest_size_bytes"
                constraint["blocked_reason"] = constraint["summary"]
            manifest_pruning = {
                "status": compact_handoff_budget_status,
                "mode": "compact",
                "before": {"manifest_size_bytes": 26057, "output_file_count": 62, "sidecar_file_count": 21},
                "after": {"manifest_size_bytes": 17788, "output_file_count": 39, "sidecar_file_count": 2},
                "exact_blocking_fields": [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_merge_state",
                    "reducer_merge_state",
                ],
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
                }
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
            "authorized_task": "TB-226",
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
        self.assertEqual(report["reducer_budget_status"], "ready")
        self.assertEqual(report["output_profile_status"], "ready")
        self.assertEqual(report["smallest_multi_zone_run_shape"]["release_zone_count"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["scenario_count"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["reducer_workers"], 2)
        self.assertEqual(report["smallest_multi_zone_run_shape"]["reducer_chunk_count"], 2)
        self.assertEqual(
            report["smallest_multi_zone_run_shape"]["output_profile"]["classification"],
            "scalable_default",
        )
        self.assertGreaterEqual(len(report["smallest_multi_zone_run_shape"]["preservation_checklist"]), 2)

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
        self.assertIn("manifest_size_bytes", report["blocked_reason"])
        self.assertEqual(report["authorization_record_status"], "missing")


if __name__ == "__main__":
    unittest.main()
