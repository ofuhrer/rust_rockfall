#!/usr/bin/env python3
"""Fail-closed authorization preflight for the smallest multi-zone Balfrin probe."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import check_balfrin_remote_access_preflight as access_preflight  # noqa: E402


SCHEMA_VERSION = "balfrin_smallest_multi_zone_probe_authorization_preflight_v1"
STATUS_READY = "ready_for_authorization_review"
STATUS_BLOCKED_MISSING_AUTHORIZATION = "blocked_missing_authorization"
STATUS_BLOCKED_MISSING_PACKAGE = "blocked_missing_reviewed_package"
STATUS_BLOCKED_REDUCER_BUDGET = "blocked_reducer_budget"
STATUS_BLOCKED_ACCESS = "blocked_access"
STATUS_BLOCKED_PACKAGE = "blocked_reviewed_package"
STATUS_BLOCKED_ACCESS_NOT_CHECKED = "blocked_balfrin_access_not_checked"
STATUS_BLOCKED_SUBMIT_CONTRACT = "blocked_submit_contract"
REVIEWED_BALFRIN_RUN_ROOT_PREFIX = Path("/scratch/mch/olifu/rust_rockfall/probes")

ACCESS_PREFLIGHT_COMMAND = (
    "PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json"
)


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


handoff = _load_module(
    "balfrin_smallest_multi_zone_handoff",
    "generate_balfrin_multi_release_zone_demo_handoff.py",
)
submit_driver = _load_module(
    "balfrin_smallest_multi_zone_submit",
    "submit_balfrin_probe.py",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reviewed-handoff-package",
        type=Path,
        default=handoff.DEFAULT_PACKAGE_JSON,
        help="Reviewed multi-zone handoff package JSON.",
    )
    parser.add_argument(
        "--authorization-record",
        type=Path,
        default=handoff.DEFAULT_AUTHORIZATION_RECORD_PATH,
        help="Live-run authorization record YAML or JSON.",
    )
    parser.add_argument(
        "--balfrin-access-preflight-json",
        type=Path,
        default=None,
        help="Optional JSON output from check_balfrin_remote_access_preflight.py.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument(
        "--validation-mode",
        choices=("authorization-preflight", "budget-thresholds"),
        default="authorization-preflight",
        help="Use budget-thresholds to report only the output-budget acceptance validation.",
    )
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    return parser.parse_args(argv)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_access_report(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is not None:
        return _load_json(path), str(path)
    return access_preflight.collect_preflight_report(), ACCESS_PREFLIGHT_COMMAND


def _missing_access_report() -> dict[str, Any]:
    return {
        "schema_version": access_preflight.SCHEMA_VERSION,
        "status": STATUS_BLOCKED_ACCESS_NOT_CHECKED,
        "ready_for_read_only_collection": False,
        "read_only": True,
        "live_submission_authorized": False,
        "checked_commands": [],
        "boundary_note": "Balfrin access preflight was not supplied or run.",
    }


def _extract_run_shape(package: dict[str, Any]) -> dict[str, Any]:
    hazard_package = dict(
        package.get("four_zone_hazard_execution_package")
        or package.get("review_only_four_zone_package")
        or {}
    )
    review_only = dict(package.get("review_only_four_zone_package") or hazard_package or {})
    follow_up = dict(package.get("follow_up_recommendation") or {})
    minimum = dict(
        follow_up.get("minimum_measured_multi_zone_run")
        or package.get("smallest_measured_multi_zone_run")
        or hazard_package
        or review_only
        or {}
    )
    reducer_pressure = dict(
        minimum.get("reducer_pressure")
        or package.get("constraint_pressure")
        or review_only.get("constraint_pressure")
        or {}
    )
    output_profile_policy = dict(
        minimum.get("output_profile_policy")
        or hazard_package.get("reduced_output_settings", {}).get("output_profile_policy")
        or review_only.get("output_profile_policy")
        or {}
    )
    return {
        "hazard_package": hazard_package,
        "review_package": review_only,
        "release_zone_count": minimum.get("release_zone_count"),
        "scenario_count": minimum.get("scenario_count"),
        "trajectory_count_target": minimum.get("trajectory_count_target"),
        "release_cell_count": minimum.get("release_cell_count"),
        "seed_policy": minimum.get("seed_policy", {}),
        "trajectory_workers": minimum.get("trajectory_workers"),
        "reducer_workers": minimum.get("reducer_workers")
        or reducer_pressure.get("requested_reducer_worker_count"),
        "reducer_chunk_count": minimum.get("reducer_chunk_count")
        or reducer_pressure.get("requested_reducer_chunk_count"),
        "release_zone_batch_size": reducer_pressure.get("requested_release_zone_batch_size")
        or minimum.get("release_zone_count"),
        "review_readiness_status": review_only.get("readiness_classification"),
        "review_readiness_reason": review_only.get("readiness_reason"),
        "promotion_status": review_only.get("promotion_status"),
        "promotion_reason": review_only.get("promotion_reason"),
        "output_profile": {
            "output_mode": minimum.get("output_mode"),
            "conditional_curve_export": hazard_package.get("reduced_output_settings", {}).get("conditional_curve_export")
            or review_only.get("reduced_output_defaults", {}).get("conditional_curve_export")
            or minimum.get("conditional_curve_export"),
            "grid_csv_export": hazard_package.get("reduced_output_settings", {}).get("grid_csv_export")
            or review_only.get("reduced_output_defaults", {}).get("grid_csv_export")
            or minimum.get("grid_csv_export"),
            "export_geotiff": minimum.get("export_geotiff"),
            "pilot_gis_package": minimum.get("pilot_gis_package"),
            "classification": output_profile_policy.get("classification"),
            "policy": output_profile_policy,
        },
        "estimates": {
            "runtime_seconds": review_only.get("expected_runtime_seconds") or minimum.get("estimated_runtime_seconds"),
            "storage_bytes": review_only.get("expected_storage_bytes") or minimum.get("estimated_storage_bytes"),
            "file_count": review_only.get("expected_file_count") or minimum.get("estimated_file_count"),
            "manifest_pressure_bytes": review_only.get("expected_manifest_pressure_bytes")
            or minimum.get("estimated_manifest_pressure_bytes"),
        },
        "preservation_checklist": list(minimum.get("preservation_gate_checklist") or review_only.get("preservation_gate_checklist") or []),
        "preservation_instructions": dict(hazard_package.get("preservation_instructions") or {}),
        "output_roots": dict(minimum.get("output_roots") or {}),
        "reviewed_handoff_package_path": minimum.get("reviewed_handoff_package_path"),
        "authorization_record_path": minimum.get("authorization_record_path"),
        "authorization_review_command": minimum.get("authorization_review_command")
        or follow_up.get("authorization_review_command")
        or package.get("authorization_review_command"),
        "authorization_submit_command": minimum.get("authorization_submit_command")
        or follow_up.get("authorization_submit_command")
        or package.get("authorization_submit_command"),
    }


def _reducer_budget_status(package: dict[str, Any], run_shape: dict[str, Any]) -> dict[str, Any]:
    review_only = dict(
        package.get("four_zone_hazard_execution_package")
        or package.get("review_only_four_zone_package")
        or {}
    )
    minimum = dict(
        dict(package.get("follow_up_recommendation") or {}).get("minimum_measured_multi_zone_run")
        or package.get("smallest_measured_multi_zone_run")
        or {}
    )
    constraint = dict(
        minimum.get("reducer_pressure")
        or package.get("constraint_pressure")
        or package.get("package_constraint_summary")
        or {}
    )
    status = str(constraint.get("status") or package.get("package_constraint_status") or "")
    handoff_projection = dict(
        constraint.get("handoff_output_budget_projection")
        or package.get("handoff_output_budget_projection")
        or review_only.get("constraint_pressure", {}).get("handoff_output_budget_projection")
        or review_only.get("projection")
        or {}
    )
    review_readiness = str(review_only.get("readiness_classification") or package.get("review_readiness_classification") or "")
    budget_recheck = dict(handoff_projection.get("budget_recheck") or {})
    output_budget_acceptance_validation = dict(
        handoff_projection.get("budget_acceptance_validation")
        or package.get("output_budget_acceptance_validation")
        or review_only.get("output_budget_acceptance_validation")
        or {}
    )
    manifest_pruning = dict(package.get("manifest_pruning") or review_only.get("manifest_pruning") or {})
    blocked_reasons: list[str] = []

    def add_blocked_reason(reason: Any) -> None:
        text = str(reason or "").strip()
        if text and text not in blocked_reasons:
            blocked_reasons.append(text)

    if status in {"blocked", "blocked_missing_inputs"}:
        add_blocked_reason(constraint.get("blocked_reason") or constraint.get("summary") or status)
    for check in constraint.get("constraint_checks") or []:
        if isinstance(check, dict) and check.get("status") == "blocked":
            add_blocked_reason(check.get("reason") or check.get("label") or "blocked reducer check")
    if budget_recheck.get("status") == "blocked_budget_reduction_needed":
        add_blocked_reason(budget_recheck.get("reason") or "current compact handoff budget remains blocked")
    if output_budget_acceptance_validation.get("status") == "blocked_threshold_exceeded":
        add_blocked_reason(output_budget_acceptance_validation.get("summary") or "output-budget acceptance threshold exceeded")
    if manifest_pruning.get("status") == "blocked_budget_reduction_needed":
        add_blocked_reason(manifest_pruning.get("blocked_reason") or manifest_pruning.get("summary"))
    if not run_shape.get("preservation_checklist"):
        add_blocked_reason("smallest run preservation checklist is missing")
    if not run_shape.get("output_profile", {}).get("classification"):
        add_blocked_reason("smallest run output profile policy is missing")
    return {
        "status": STATUS_BLOCKED_REDUCER_BUDGET if blocked_reasons else "ready",
        "review_readiness_status": review_readiness or review_only.get("status") or package.get("review_readiness_classification"),
        "review_readiness_reason": review_only.get("readiness_reason") or package.get("review_readiness_reason"),
        "package_constraint_status": status,
        "constraint_summary": constraint.get("summary"),
        "constraint_source": constraint.get("constraint_source", {}),
        "requested_release_zone_batch_size": constraint.get("requested_release_zone_batch_size"),
        "requested_reducer_chunk_count": constraint.get("requested_reducer_chunk_count"),
        "requested_reducer_worker_count": constraint.get("requested_reducer_worker_count"),
        "measured_constraints": constraint.get("measured_constraints", {}),
        "constraint_checks": list(constraint.get("constraint_checks") or []),
        "handoff_output_budget_projection_status": handoff_projection.get("status"),
        "handoff_output_budget_projection_mode": handoff_projection.get("projection_mode"),
        "handoff_budget_recheck_status": budget_recheck.get("status"),
        "handoff_budget_recheck_reason": budget_recheck.get("reason"),
        "output_budget_acceptance_thresholds": dict(
            handoff_projection.get("budget_acceptance_thresholds")
            or package.get("output_budget_acceptance_thresholds")
            or {}
        ),
        "output_budget_acceptance_validation": output_budget_acceptance_validation,
        "output_budget_acceptance_status": output_budget_acceptance_validation.get("status"),
        "output_budget_acceptance_threshold_profile_id": output_budget_acceptance_validation.get("threshold_profile_id"),
        "output_budget_acceptance_failures": list(output_budget_acceptance_validation.get("failures") or []),
        "manifest_pruning_status": manifest_pruning.get("status"),
        "manifest_pruning_mode": manifest_pruning.get("mode"),
        "manifest_pruning_before": manifest_pruning.get("before"),
        "manifest_pruning_after": manifest_pruning.get("after"),
        "manifest_pruning_replay_critical_contract": manifest_pruning.get("replay_critical_contract", {}),
        "manifest_pruning_exact_blocking_fields": list(manifest_pruning.get("exact_blocking_fields") or []),
        "blocked_reasons": blocked_reasons,
    }


def _output_profile_status(run_shape: dict[str, Any]) -> dict[str, Any]:
    output_profile = dict(run_shape.get("output_profile") or {})
    classification = str(output_profile.get("classification") or "").strip()
    blocked_reasons: list[str] = []
    if not classification:
        blocked_reasons.append("smallest run output profile policy is missing")
    if output_profile.get("conditional_curve_export") != "summary-only":
        blocked_reasons.append("smallest run must keep summary-only conditional curves")
    if output_profile.get("grid_csv_export") != "none":
        blocked_reasons.append("smallest run must keep grid CSV export disabled")
    return {
        "status": "ready" if not blocked_reasons else "blocked_output_profile",
        "classification": classification or None,
        "output_mode": output_profile.get("output_mode"),
        "conditional_curve_export": output_profile.get("conditional_curve_export"),
        "grid_csv_export": output_profile.get("grid_csv_export"),
        "export_geotiff": output_profile.get("export_geotiff"),
        "pilot_gis_package": output_profile.get("pilot_gis_package"),
        "policy": output_profile.get("policy", {}),
        "blocked_reasons": blocked_reasons,
    }


def _package_review_status(path: Path, package_status: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    if package_status["status"] == "missing":
        return {
            "status": STATUS_BLOCKED_MISSING_PACKAGE,
            "path": str(path),
            "sha256": None,
            "blocked_reason": package_status["blocked_reason"],
        }
    blocked_reasons: list[str] = []
    if package.get("schema_version") != handoff.SCHEMA_VERSION:
        blocked_reasons.append("reviewed handoff package schema is not the multi-zone handoff schema")
    if package.get("package_status") == "blocked_missing_inputs":
        blocked_reasons.append("reviewed handoff package is blocked_missing_inputs")
    if package.get("submission_classification") != "blocked_pending_new_human_authorization":
        blocked_reasons.append("reviewed handoff package does not preserve the pending-authorization classification")
    if package.get("live_execution_requires_new_human_authorization") is not True:
        blocked_reasons.append("reviewed handoff package does not require new human authorization")
    return {
        "status": STATUS_BLOCKED_PACKAGE if blocked_reasons else "reviewed",
        "path": str(path),
        "sha256": package_status["sha256"],
        "blocked_reasons": blocked_reasons,
        "blocked_reason": "; ".join(blocked_reasons),
    }


def _authorization_requirement(
    *,
    reviewed_handoff_package: Path,
    authorization_record: Path,
) -> dict[str, Any]:
    report = submit_driver._validate_authorized_submission(
        reviewed_handoff_package=reviewed_handoff_package,
        authorization_record=authorization_record,
        run_root=handoff.SMALLEST_MULTI_ZONE_REVIEW_RUN_ROOT,
    )
    return {
        "status": report.get("status"),
        "authorization_status": report.get("authorization_status"),
        "reviewed_handoff_package_status": report.get("reviewed_handoff_package_status"),
        "authorization_record_status": report.get("authorization_record_status"),
        "reviewed_handoff_package_sha256": report.get("reviewed_handoff_package_sha256"),
        "authorization_record_sha256": report.get("authorization_record_sha256"),
        "blocked_reason": report.get("blocked_reason", ""),
        "remediation": report.get("remediation", ""),
    }


def _parse_option(tokens: list[str], option: str) -> str | None:
    for idx, token in enumerate(tokens):
        if token == option and idx + 1 < len(tokens):
            return tokens[idx + 1]
        if token.startswith(f"{option}="):
            return token.split("=", 1)[1]
    return None


def _local_run_root_writability_status(run_root: Path) -> dict[str, Any]:
    run_root = run_root.expanduser()
    existing = run_root if run_root.exists() else run_root.parent
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    if not existing.exists():
        return {
            "status": "not_checked",
            "reason": f"no existing ancestor for run root {run_root}",
            "checked_path": str(existing),
        }
    writable = os.access(existing, os.W_OK | os.X_OK)
    return {
        "status": "ready" if writable else STATUS_BLOCKED_SUBMIT_CONTRACT,
        "reason": "" if writable else f"run-root ancestor is not writable: {existing}",
        "checked_path": str(existing),
    }


def _reviewed_run_root_contract_status(run_root_token: str | None) -> dict[str, Any]:
    if not run_root_token:
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "run_root": None,
            "writability_status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "blocked_reason": "authorization submit command is missing --run-root",
        }
    run_root = Path(run_root_token).expanduser()
    if run_root.is_absolute() and str(run_root).startswith("/scratch/"):
        try:
            run_root.relative_to(REVIEWED_BALFRIN_RUN_ROOT_PREFIX)
        except ValueError:
            return {
                "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
                "run_root": str(run_root),
                "writability_status": STATUS_BLOCKED_SUBMIT_CONTRACT,
                "blocked_reason": (
                    "authorization submit command targets an unreviewed Balfrin scratch root; "
                    f"expected a path under {REVIEWED_BALFRIN_RUN_ROOT_PREFIX}"
                ),
            }
        return {
            "status": "ready",
            "run_root": str(run_root),
            "writability_status": "reviewed_balfrin_scratch_root",
            "blocked_reason": "",
        }
    local_status = _local_run_root_writability_status(run_root)
    return {
        "status": local_status["status"],
        "run_root": str(run_root),
        "writability_status": local_status["status"],
        "checked_path": local_status["checked_path"],
        "blocked_reason": local_status["reason"],
    }


def _submit_contract_status(run_shape: dict[str, Any]) -> dict[str, Any]:
    command = str(run_shape.get("authorization_submit_command") or "").strip()
    if not command:
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "command": command,
            "probe_manifest_path": None,
            "run_id": None,
            "blocked_reason": "authorization submit command is missing from the reviewed handoff package",
        }
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "command": command,
            "probe_manifest_path": None,
            "run_id": None,
            "blocked_reason": f"authorization submit command could not be parsed: {exc}",
        }

    manifest_token: str | None = None
    for idx, token in enumerate(tokens):
        if token.endswith("scripts/submit_balfrin_probe.py") or token == "submit_balfrin_probe.py":
            if idx + 1 < len(tokens):
                manifest_token = tokens[idx + 1]
            break
    if manifest_token is None:
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "command": command,
            "probe_manifest_path": None,
            "run_id": None,
            "blocked_reason": "authorization submit command does not name a probe manifest after scripts/submit_balfrin_probe.py",
        }

    manifest_path = Path(manifest_token)
    if not manifest_path.is_absolute():
        manifest_path = (ROOT / manifest_path).resolve()
    try:
        _command_plan, run_id = submit_driver._read_command_plan(manifest_path)
    except Exception as exc:
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "command": command,
            "probe_manifest_path": str(manifest_path),
            "run_id": None,
            "blocked_reason": str(exc),
        }
    run_root_contract = _reviewed_run_root_contract_status(_parse_option(tokens, "--run-root"))
    if run_root_contract["status"] != "ready":
        return {
            "status": STATUS_BLOCKED_SUBMIT_CONTRACT,
            "command": command,
            "probe_manifest_path": str(manifest_path),
            "run_id": run_id,
            "run_root": run_root_contract.get("run_root"),
            "run_root_writability_status": run_root_contract.get("writability_status"),
            "blocked_reason": run_root_contract.get("blocked_reason", ""),
        }
    return {
        "status": "ready",
        "command": command,
        "probe_manifest_path": str(manifest_path),
        "run_id": run_id,
        "run_root": run_root_contract.get("run_root"),
        "run_root_writability_status": run_root_contract.get("writability_status"),
        "blocked_reason": "",
    }


def _overall_status(
    *,
    package_review: dict[str, Any],
    authorization_requirement: dict[str, Any],
    submit_contract: dict[str, Any],
    access_report: dict[str, Any],
    reducer_budget: dict[str, Any],
    output_profile: dict[str, Any],
) -> tuple[str, str]:
    if package_review["status"] != "reviewed":
        return package_review["status"], package_review.get("blocked_reason", "")
    if reducer_budget["status"] != "ready":
        return STATUS_BLOCKED_REDUCER_BUDGET, "; ".join(reducer_budget["blocked_reasons"])
    if output_profile["status"] != "ready":
        return STATUS_BLOCKED_REDUCER_BUDGET, "; ".join(output_profile["blocked_reasons"])
    if submit_contract["status"] != "ready":
        return STATUS_BLOCKED_SUBMIT_CONTRACT, submit_contract.get("blocked_reason", "")
    access_status = str(access_report.get("status") or STATUS_BLOCKED_ACCESS_NOT_CHECKED)
    if access_status != access_preflight.STATUS_READY:
        return STATUS_BLOCKED_ACCESS, f"Balfrin access preflight status is {access_status}"
    if authorization_requirement.get("status") != "authorized":
        status = str(authorization_requirement.get("status") or STATUS_BLOCKED_MISSING_AUTHORIZATION)
        if status == "blocked_missing_inputs":
            status = STATUS_BLOCKED_MISSING_AUTHORIZATION
        return status, str(authorization_requirement.get("blocked_reason") or "authorization record is not ready")
    return STATUS_READY, ""


def build_report(
    *,
    reviewed_handoff_package: Path = handoff.DEFAULT_PACKAGE_JSON,
    authorization_record: Path = handoff.DEFAULT_AUTHORIZATION_RECORD_PATH,
    balfrin_access_preflight: dict[str, Any] | None = None,
    balfrin_access_preflight_source: str = "embedded_or_missing",
) -> dict[str, Any]:
    package_status = submit_driver._structured_document_status(
        reviewed_handoff_package,
        label="reviewed handoff package",
    )
    package = dict(package_status.get("value") or {})
    run_shape = _extract_run_shape(package)
    package_review = _package_review_status(reviewed_handoff_package, package_status, package)
    authorization_requirement = _authorization_requirement(
        reviewed_handoff_package=reviewed_handoff_package,
        authorization_record=authorization_record,
    )
    access_report = dict(balfrin_access_preflight or _missing_access_report())
    reducer_budget = _reducer_budget_status(package, run_shape)
    output_profile = _output_profile_status(run_shape)
    submit_contract = _submit_contract_status(run_shape)
    preflight_status, blocked_reason = _overall_status(
        package_review=package_review,
        authorization_requirement=authorization_requirement,
        submit_contract=submit_contract,
        access_report=access_report,
        reducer_budget=reducer_budget,
        output_profile=output_profile,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": preflight_status,
        "preflight_status": preflight_status,
        "submission_gate_status": preflight_status,
        "ready_for_authorization_review": preflight_status == STATUS_READY,
        "ready_for_authorized_submission": preflight_status == STATUS_READY,
        "authorization_granted_by_preflight": False,
        "live_submission_authorized": False,
        "blocked_reason": blocked_reason,
        "authorization_status": authorization_requirement.get("authorization_status"),
        "reviewed_handoff_package_status": package_review.get("status"),
        "authorization_record_status": authorization_requirement.get("authorization_record_status"),
        "review_readiness_status": run_shape.get("review_readiness_status"),
        "review_readiness_reason": run_shape.get("review_readiness_reason"),
        "reviewed_handoff_package_sha256": package_review.get("sha256")
        or authorization_requirement.get("reviewed_handoff_package_sha256"),
        "authorization_record_sha256": authorization_requirement.get("authorization_record_sha256"),
        "balfrin_access_status": access_report.get("status"),
        "reducer_budget_status": reducer_budget.get("status"),
        "output_profile_status": output_profile.get("status"),
        "submit_contract_status": submit_contract.get("status"),
        "output_budget_acceptance_status": reducer_budget.get("output_budget_acceptance_status"),
        "output_budget_acceptance_validation": reducer_budget.get("output_budget_acceptance_validation", {}),
        "output_budget_acceptance_thresholds": reducer_budget.get("output_budget_acceptance_thresholds", {}),
        "authorization_record_allows_one_bounded_probe": authorization_requirement.get("status") == "authorized",
        "reviewed_handoff_package_requirement": package_review,
        "authorization_record_requirement": authorization_requirement,
        "submit_contract_requirement": submit_contract,
        "balfrin_access_preflight_requirement": {
            "required": True,
            "command": ACCESS_PREFLIGHT_COMMAND,
            "source": balfrin_access_preflight_source,
            "consumed_status": access_report.get("status"),
            "ready_for_read_only_collection": access_report.get("ready_for_read_only_collection"),
            "ready_for_pre_submit": access_report.get(
                "ready_for_pre_submit",
                access_report.get("ready_for_read_only_collection"),
            ),
            "remote_head": access_report.get("remote_head"),
            "remote_checkout_hygiene": access_report.get("remote_checkout_hygiene", {}),
            "report": access_report,
        },
        "reducer_budget_requirement": reducer_budget,
        "output_profile_requirement": output_profile,
        "smallest_multi_zone_run_shape": run_shape,
        "reviewed_handoff_package_path": str(reviewed_handoff_package),
        "authorization_record_path": str(authorization_record),
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "preflight_does_not_grant_authorization": True,
        },
    }


def render_text_report(report: dict[str, Any]) -> str:
    run_shape = dict(report.get("smallest_multi_zone_run_shape") or {})
    reducer_budget = dict(report.get("reducer_budget_requirement") or {})
    access_requirement = dict(report.get("balfrin_access_preflight_requirement") or {})
    submit_contract = dict(report.get("submit_contract_requirement") or {})
    manifest_pruning_before = dict(reducer_budget.get("manifest_pruning_before") or {})
    manifest_pruning_after = dict(reducer_budget.get("manifest_pruning_after") or {})
    lines = [
        "Balfrin Smallest Multi-Zone Probe Authorization Preflight",
        "",
        f"- Preflight status: `{report.get('preflight_status')}`",
        f"- Ready for authorization review: `{report.get('ready_for_authorization_review')}`",
        f"- Preflight grants authorization: `{report.get('authorization_granted_by_preflight')}`",
        f"- Live submission authorized by preflight: `{report.get('live_submission_authorized')}`",
        f"- Blocked reason: {report.get('blocked_reason') or 'none'}",
        f"- Review readiness: `{report.get('review_readiness_status')}`",
        f"- Review readiness reason: {report.get('review_readiness_reason') or 'none'}",
        f"- Reviewed package: `{report.get('reviewed_handoff_package_path')}`",
        f"- Reviewed package SHA-256: `{report.get('reviewed_handoff_package_sha256')}`",
        f"- Authorization record: `{report.get('authorization_record_path')}`",
        f"- Authorization record status: `{report.get('authorization_record_status')}`",
        f"- Submit contract status: `{submit_contract.get('status')}`",
        f"- Submit probe manifest: `{submit_contract.get('probe_manifest_path')}`",
        f"- Balfrin access status: `{access_requirement.get('consumed_status')}`",
        "",
        "## Smallest Run Shape",
        "",
        f"- Release zones: `{run_shape.get('release_zone_count')}`",
        f"- Scenarios: `{run_shape.get('scenario_count')}`",
        f"- Trajectory target: `{run_shape.get('trajectory_count_target')}`",
        f"- Trajectory workers: `{run_shape.get('trajectory_workers')}`",
        f"- Reducer workers: `{run_shape.get('reducer_workers')}`",
        f"- Reducer chunks: `{run_shape.get('reducer_chunk_count')}`",
        f"- Output profile: `{run_shape.get('output_profile', {}).get('classification')}`",
        f"- Output profile status: `{report.get('output_profile_status')}`",
        "",
        "## Reducer Budget",
        "",
        f"- Status: `{reducer_budget.get('status')}`",
        f"- Package constraint status: `{reducer_budget.get('package_constraint_status')}`",
        f"- Handoff budget recheck status: `{reducer_budget.get('handoff_budget_recheck_status')}`",
        f"- Acceptance threshold profile: `{reducer_budget.get('output_budget_acceptance_threshold_profile_id')}`",
        f"- Acceptance threshold status: `{reducer_budget.get('output_budget_acceptance_status')}`",
        f"- Manifest pruning status: `{reducer_budget.get('manifest_pruning_status')}`",
        f"- Before manifest bytes: `{manifest_pruning_before.get('manifest_size_bytes')}`",
        f"- After manifest bytes: `{manifest_pruning_after.get('manifest_size_bytes')}`",
        f"- Before sidecar files: `{manifest_pruning_before.get('sidecar_file_count')}`",
        f"- After sidecar files: `{manifest_pruning_after.get('sidecar_file_count')}`",
        f"- Before reducer manifest files: `{manifest_pruning_before.get('reducer_manifest_file_count')}`",
        f"- After reducer manifest files: `{manifest_pruning_after.get('reducer_manifest_file_count')}`",
        f"- Before output files: `{manifest_pruning_before.get('output_file_count')}`",
        f"- After output files: `{manifest_pruning_after.get('output_file_count')}`",
        f"- Before reducer manifest bytes: `{manifest_pruning_before.get('reducer_manifest_bytes')}`",
        f"- After reducer manifest bytes: `{manifest_pruning_after.get('reducer_manifest_bytes')}`",
        f"- Replay-critical contract families: `{reducer_budget.get('manifest_pruning_replay_critical_contract', {}).get('families', [])}`",
        f"- Replay-critical merge proof: `{reducer_budget.get('manifest_pruning_replay_critical_contract', {}).get('merge_order_proof', {})}`",
        f"- Replay-critical output-profile semantics: `{reducer_budget.get('manifest_pruning_replay_critical_contract', {}).get('output_profile_semantics', {})}`",
        f"- Exact blocking fields: `{reducer_budget.get('manifest_pruning_exact_blocking_fields')}`",
        f"- Constraint summary: {reducer_budget.get('constraint_summary')}",
        f"- Acceptance summary: {dict(reducer_budget.get('output_budget_acceptance_validation') or {}).get('summary')}",
        "",
        "## Preservation Checklist",
        "",
    ]
    for item in run_shape.get("preservation_checklist") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.validation_mode == "budget-thresholds" and args.balfrin_access_preflight_json is None:
            access_report, access_source = _missing_access_report(), "budget-thresholds-mode"
        else:
            access_report, access_source = _load_access_report(args.balfrin_access_preflight_json)
        report = build_report(
            reviewed_handoff_package=args.reviewed_handoff_package,
            authorization_record=args.authorization_record,
            balfrin_access_preflight=access_report,
            balfrin_access_preflight_source=access_source,
        )
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"balfrin smallest multi-zone authorization preflight error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.validation_mode == "budget-thresholds":
        validation = dict(report.get("output_budget_acceptance_validation") or {})
        if args.format == "json":
            print(json.dumps(validation, indent=2, sort_keys=True, default=str))
        else:
            print(validation.get("summary") or "output-budget acceptance validation unavailable")
        return 0 if validation.get("status") == "accepted" else 2
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["preflight_status"] == STATUS_READY else 2


if __name__ == "__main__":
    raise SystemExit(main())
