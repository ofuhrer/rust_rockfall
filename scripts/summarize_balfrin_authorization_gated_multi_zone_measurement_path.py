#!/usr/bin/env python3
"""Summarize the authorization-gated Balfrin multi-zone measurement path.

This helper is read-only. It binds the reviewed handoff package, authorization
record, authorized submit command, deterministic run root, post-run collector,
preservation gate, and closure-package input contract into one checklist. It
fails closed when the TB-247 authorization preflight is not ready or when the
post-run evidence collector cannot prove measured, preservation-checked output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import preflight_balfrin_smallest_multi_zone_probe_authorization as authorization_preflight  # noqa: E402
from scripts import rehearse_balfrin_post_run_evidence_collector as post_run_collector  # noqa: E402
from scripts import summarize_balfrin_demonstration_closure_package as closure_package  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_authorization_gated_multi_zone_measurement_path_v1"
DEFAULT_PREFLIGHT_RECORD = ROOT / "validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml"
DEFAULT_SOURCE_FAMILY = "authorized_multi_zone_probe"
STATUS_READY = "ready_after_authorization"
STATUS_BLOCKED = "blocked_pre_authorization"
STATUS_PENDING_POST_RUN = "pending_authorized_post_run"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authorization-preflight",
        type=Path,
        default=DEFAULT_PREFLIGHT_RECORD,
        help="YAML or JSON authorization preflight report from TB-247.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Optional run root to inspect with the post-run evidence collector.",
    )
    parser.add_argument(
        "--balfrin-access-json",
        type=Path,
        default=None,
        help="Optional Balfrin access preflight JSON for post-run collection rehearsal.",
    )
    parser.add_argument(
        "--non-git-artifact-status",
        choices=("available", "unavailable"),
        default="available",
        help="Post-run evidence switch for preserved non-git run artifacts.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    return parser.parse_args(argv)


def _load_structured(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError(f"structured report must be a mapping: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_optional_access_report(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _preflight_source(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "source": "in_memory",
            "path": None,
            "sha256": None,
        }
    return {
        "source": "file",
        "path": str(path),
        "sha256": _sha256_file(path) if path.exists() else None,
    }


def _run_root_from_preflight(preflight: dict[str, Any], explicit_run_root: Path | None) -> Path:
    if explicit_run_root is not None:
        return explicit_run_root
    run_shape = preflight.get("smallest_multi_zone_run_shape")
    if isinstance(run_shape, dict):
        for key in ("run_root", "expected_run_root", "review_run_root"):
            value = run_shape.get(key)
            if isinstance(value, str) and value:
                return Path(value)
    return authorization_preflight.handoff.SMALLEST_MULTI_ZONE_REVIEW_RUN_ROOT


def _nested_mapping(preflight: dict[str, Any], key: str) -> dict[str, Any]:
    value = preflight.get(key)
    return dict(value) if isinstance(value, dict) else {}


def _record_status(preflight: dict[str, Any], top_key: str, nested_key: str) -> Any:
    value = preflight.get(top_key)
    if value is not None:
        return value
    return _nested_mapping(preflight, nested_key).get("status")


def _record_sha256(preflight: dict[str, Any], top_key: str, nested_key: str) -> Any:
    value = preflight.get(top_key)
    if value is not None:
        return value
    return _nested_mapping(preflight, nested_key).get("sha256")


def _access_status(preflight: dict[str, Any]) -> str:
    value = preflight.get("balfrin_access_status")
    if isinstance(value, str) and value:
        return value
    access = _nested_mapping(preflight, "access")
    status = access.get("status") or access.get("consumed_status")
    return str(status or "")


def _path_from_preflight(preflight: dict[str, Any], key: str, fallback: Path) -> str:
    value = preflight.get(key)
    if isinstance(value, str) and value:
        return value
    if key == "reviewed_handoff_package_path":
        reviewed = _nested_mapping(preflight, "reviewed_handoff_package")
        for nested_key in ("command_path", "path", "resolved_path"):
            value = reviewed.get(nested_key)
            if isinstance(value, str) and value:
                return value
    if key == "authorization_record_path":
        authorization = _nested_mapping(preflight, "authorization_record")
        for nested_key in ("command_path", "path", "resolved_path"):
            value = authorization.get(nested_key)
            if isinstance(value, str) and value:
                return value
    run_shape = preflight.get("smallest_multi_zone_run_shape")
    if isinstance(run_shape, dict):
        value = run_shape.get(key)
        if isinstance(value, str) and value:
            return value
    return str(fallback)


def _submit_command(preflight: dict[str, Any], run_root: Path) -> str:
    run_shape = preflight.get("smallest_multi_zone_run_shape")
    if isinstance(run_shape, dict):
        command = run_shape.get("authorization_submit_command")
        if isinstance(command, str) and command.strip():
            return command.strip()
    return (
        "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py "
        f"{authorization_preflight.handoff.DEFAULT_TARGET_AREA_CONTRACT} "
        f"--run-root {run_root} "
        "--run-id tschamut_public_balfrin_multi_release_zone_v1 "
        "--partition postproc --authorized-submit "
        f"--reviewed-handoff-package {authorization_preflight.handoff.DEFAULT_PACKAGE_JSON} "
        f"--authorization-record {authorization_preflight.handoff.DEFAULT_AUTHORIZATION_RECORD_PATH}"
    )


def _collector_commands(run_root: Path, access_report_path: str | None) -> dict[str, Any]:
    access_arg = f" --balfrin-access-json {access_report_path}" if access_report_path else ""
    evidence_json = run_root / "balfrin_authorized_multi_zone_post_run_evidence.json"
    preservation_json = run_root / "balfrin_probe_preservation_gate_v1.json"
    closure_input = run_root / "balfrin_authorized_multi_zone_closure_input.json"
    return {
        "collector_command": (
            "PYENV_VERSION=system uv run python scripts/rehearse_balfrin_post_run_evidence_collector.py "
            f"--run-root {run_root} --source-family {DEFAULT_SOURCE_FAMILY}{access_arg} "
            f"--format json > {evidence_json}"
        ),
        "metrics_command": (
            "PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py "
            f"--run-root {run_root} --output-json {run_root / 'balfrin_probe_metrics.json'}"
        ),
        "preservation_gate_command": (
            "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py "
            f"--run-root {run_root} --json-output {preservation_json} "
            f"--text-output {run_root / 'balfrin_probe_preservation_gate_v1.txt'} --format json"
        ),
        "closure_package_input": str(closure_input),
        "closure_package_command": (
            "PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_closure_package.py "
            f"--evidence-json {closure_input} --format json"
        ),
    }


def _closure_input_contract(run_root: Path, post_run_report: dict[str, Any] | None) -> dict[str, Any]:
    if post_run_report is None or post_run_report.get("collector_status") != "measured_complete":
        return {
            "status": "not_materialized_until_measured_post_run_evidence",
            "path": str(run_root / "balfrin_authorized_multi_zone_closure_input.json"),
            "required_conditions": [
                "collector_status=measured_complete",
                "preservation_gate_status=ready_for_demonstration_evidence",
                "closure_input_compatibility.status=compatible",
                "authorization_status=authorized_for_one_bounded_probe",
            ],
        }

    evidence_input = dict(post_run_report.get("new_measured_evidence_input") or {})
    metrics_closure_section = closure_package.build_metrics_closure_section(
        status=closure_package.METRICS_COMPLETE,
        metrics_completion_source=DEFAULT_SOURCE_FAMILY,
        metrics_contract_status="complete",
        source_paths=[str(run_root)],
    )
    new_evidence_section = {
        **evidence_input,
        "evidence_type": "measured",
        "status": "measured",
        "source_type": DEFAULT_SOURCE_FAMILY,
        "preservation_checked": True,
        "preservation_gate_status": "ready_for_demonstration_evidence",
        "authorization_status": "authorized_for_one_bounded_probe",
        "source_paths": sorted(set([str(run_root), *[str(path) for path in evidence_input.get("source_paths", [])]])),
    }
    new_evidence_section["closure_input_compatibility"] = (
        closure_package.evaluate_new_measured_evidence_compatibility(new_evidence_section)
    )
    return {
        "status": "materializable_after_measured_post_run_evidence",
        "path": str(run_root / "balfrin_authorized_multi_zone_closure_input.json"),
        "payload_template": {
            "section_overrides": {
                "metrics_closure_section": metrics_closure_section,
                "new_measured_evidence_section": new_evidence_section,
            }
        },
    }


def _preflight_blocks(preflight: dict[str, Any]) -> list[str]:
    status = str(preflight.get("preflight_status") or preflight.get("status") or "unknown")
    blocked_reason = str(preflight.get("blocked_reason") or "").strip()
    reasons = [f"authorization_preflight:{status}"]
    if blocked_reason:
        reasons.append(blocked_reason)
    authorization_record_status = str(preflight.get("authorization_record_status") or "")
    if not authorization_record_status:
        authorization_record_status = str(_nested_mapping(preflight, "authorization_record").get("status") or "")
    if authorization_record_status in {"missing", "blocked_missing_authorization"}:
        reasons.append("authorization_record:missing")
    access_status = _access_status(preflight)
    if access_status and access_status != authorization_preflight.access_preflight.STATUS_READY:
        reasons.append(f"balfrin_access:{access_status}")
    return reasons


def _post_run_gate(
    *,
    preflight: dict[str, Any],
    run_root: Path,
    run_root_was_explicit: bool,
    access_report: dict[str, Any] | None,
    non_git_artifact_available: bool,
) -> dict[str, Any]:
    preflight_status = str(preflight.get("preflight_status") or preflight.get("status") or "unknown")
    if preflight_status != authorization_preflight.STATUS_READY:
        return {
            "status": "not_checked_preflight_blocked",
            "collector_status": "not_checked_preflight_blocked",
            "run_root": str(run_root),
            "run_root_was_explicit": run_root_was_explicit,
            "measured_result_promoted": False,
            "blocked_reasons": _preflight_blocks(preflight),
        }
    if not run_root_was_explicit:
        return {
            "status": STATUS_PENDING_POST_RUN,
            "collector_status": STATUS_PENDING_POST_RUN,
            "run_root": str(run_root),
            "run_root_was_explicit": False,
            "measured_result_promoted": False,
            "blocked_reasons": ["post-run run root has not been supplied for collection"],
        }

    report = post_run_collector.build_report(
        run_root=run_root,
        source_family=DEFAULT_SOURCE_FAMILY,
        balfrin_access_preflight=access_report,
        non_git_artifact_available=non_git_artifact_available,
    )
    return {
        "status": report.get("collector_status"),
        "collector_status": report.get("collector_status"),
        "run_root": str(run_root),
        "run_root_was_explicit": True,
        "metrics_report_status": report.get("metrics_report_status"),
        "preservation_gate_status": report.get("preservation_gate_status"),
        "closure_input_compatibility": report.get("closure_input_compatibility", {}),
        "closure_package_agreement": report.get("closure_package_agreement", {}),
        "new_measured_evidence_input": report.get("new_measured_evidence_input", {}),
        "missing_fields": report.get("missing_fields", {}),
        "measured_result_promoted": bool(report.get("measured_result_promoted")),
        "blocked_reasons": [] if report.get("measured_result_promoted") else [str(report.get("collector_status"))],
    }


def build_report(
    preflight: dict[str, Any],
    *,
    preflight_path: Path | None = None,
    run_root: Path | None = None,
    access_report: dict[str, Any] | None = None,
    access_report_path: Path | None = None,
    non_git_artifact_available: bool = True,
) -> dict[str, Any]:
    selected_run_root = _run_root_from_preflight(preflight, run_root).resolve()
    run_root_was_explicit = run_root is not None
    preflight_status = str(preflight.get("preflight_status") or preflight.get("status") or "unknown")
    ready_preflight = preflight_status == authorization_preflight.STATUS_READY
    commands = _collector_commands(
        selected_run_root,
        str(access_report_path) if access_report_path is not None else None,
    )
    post_run_gate = _post_run_gate(
        preflight=preflight,
        run_root=selected_run_root,
        run_root_was_explicit=run_root_was_explicit,
        access_report=access_report,
        non_git_artifact_available=non_git_artifact_available,
    )
    closure_input = _closure_input_contract(
        selected_run_root,
        {
            "collector_status": post_run_gate.get("collector_status"),
            "new_measured_evidence_input": post_run_gate.get("new_measured_evidence_input", {}),
        }
        if post_run_gate.get("collector_status") == "measured_complete"
        else None,
    )
    measured_promotion_allowed = (
        ready_preflight
        and post_run_gate.get("collector_status") == "measured_complete"
        and post_run_gate.get("closure_input_compatibility", {}).get("status") == "compatible"
        and bool(post_run_gate.get("measured_result_promoted"))
    )
    path_status = STATUS_READY if ready_preflight else STATUS_BLOCKED
    if ready_preflight and post_run_gate.get("collector_status") != "measured_complete":
        path_status = STATUS_PENDING_POST_RUN

    reviewed_package_path = _path_from_preflight(
        preflight,
        "reviewed_handoff_package_path",
        authorization_preflight.handoff.DEFAULT_PACKAGE_JSON,
    )
    authorization_record_path = _path_from_preflight(
        preflight,
        "authorization_record_path",
        authorization_preflight.handoff.DEFAULT_AUTHORIZATION_RECORD_PATH,
    )
    submit_command = _submit_command(preflight, selected_run_root)

    checklist = [
        {
            "id": "authorization_preflight_output",
            "status": preflight_status,
            "path": _preflight_source(preflight_path)["path"],
            "sha256": _preflight_source(preflight_path)["sha256"],
            "required_status": authorization_preflight.STATUS_READY,
        },
        {
            "id": "reviewed_handoff_package",
            "status": _record_status(preflight, "reviewed_handoff_package_status", "reviewed_handoff_package"),
            "path": reviewed_package_path,
            "sha256": _record_sha256(preflight, "reviewed_handoff_package_sha256", "reviewed_handoff_package"),
        },
        {
            "id": "authorization_record",
            "status": _record_status(preflight, "authorization_record_status", "authorization_record"),
            "path": authorization_record_path,
            "sha256": _record_sha256(preflight, "authorization_record_sha256", "authorization_record"),
            "required_status": "reviewed",
        },
        {
            "id": "authorized_submit_command",
            "status": "documented_not_executed",
            "command": submit_command,
            "execution_allowed_by_this_helper": False,
            "requires_preflight_status": authorization_preflight.STATUS_READY,
        },
        {
            "id": "run_root",
            "status": "deterministic",
            "path": str(selected_run_root),
        },
        {
            "id": "post_run_metrics_collector",
            "status": "pending_measured_run" if not measured_promotion_allowed else "measured",
            "command": commands["metrics_command"],
        },
        {
            "id": "post_run_preservation_gate",
            "status": post_run_gate.get("preservation_gate_status", post_run_gate.get("status")),
            "command": commands["preservation_gate_command"],
        },
        {
            "id": "post_run_evidence_collector",
            "status": post_run_gate.get("collector_status"),
            "command": commands["collector_command"],
        },
        {
            "id": "closure_package_input",
            "status": closure_input["status"],
            "path": closure_input["path"],
            "command": commands["closure_package_command"],
        },
    ]

    blocked_report = None
    if not ready_preflight:
        blocked_report = {
            "status": preflight_status,
            "blocked_reasons": _preflight_blocks(preflight),
            "live_submission_authorized": False,
            "submit_command_executed": False,
            "measured_result_promoted": False,
        }
    elif not measured_promotion_allowed:
        blocked_report = {
            "status": str(post_run_gate.get("collector_status") or STATUS_PENDING_POST_RUN),
            "blocked_reasons": list(post_run_gate.get("blocked_reasons") or []),
            "live_submission_authorized": False,
            "submit_command_executed": False,
            "measured_result_promoted": False,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "path_status": path_status,
        "ready_for_authorized_execution_path": ready_preflight,
        "ready_for_measured_evidence_promotion": measured_promotion_allowed,
        "measured_result_promoted": measured_promotion_allowed,
        "submit_command_executed": False,
        "live_submission_authorized_by_this_report": False,
        "authorization_preflight": {
            "source": _preflight_source(preflight_path),
            "status": preflight_status,
            "blocked_reason": preflight.get("blocked_reason", ""),
            "ready_for_authorization_review": preflight.get("ready_for_authorization_review", False),
            "ready_for_authorized_submission": preflight.get("ready_for_authorized_submission", False),
        },
        "authorization_gated_execution_checklist": checklist,
        "post_run_evidence_gate": post_run_gate,
        "closure_package_input_contract": closure_input,
        "blocked_report": blocked_report,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "live_submission_requires_external_explicit_authorization": True,
        },
        "summary": summarize_report(path_status, preflight_status, post_run_gate, measured_promotion_allowed),
    }


def summarize_report(
    path_status: str,
    preflight_status: str,
    post_run_gate: dict[str, Any],
    measured_promotion_allowed: bool,
) -> str:
    if measured_promotion_allowed:
        return (
            "Authorization-gated multi-zone path has measured post-run evidence compatible with the closure package."
        )
    if path_status == STATUS_BLOCKED:
        return (
            "Authorization-gated multi-zone path is blocked before submission; "
            f"TB-247 preflight status is {preflight_status}."
        )
    return (
        "Authorization-gated multi-zone path is deterministic, but measured evidence promotion is pending "
        f"post-run collector status {post_run_gate.get('collector_status')}."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Authorization-Gated Multi-Zone Measurement Path",
        f"schema_version: {report.get('schema_version')}",
        f"path_status: {report.get('path_status')}",
        f"ready_for_authorized_execution_path: {report.get('ready_for_authorized_execution_path')}",
        f"ready_for_measured_evidence_promotion: {report.get('ready_for_measured_evidence_promotion')}",
        f"submit_command_executed: {report.get('submit_command_executed')}",
        f"summary: {report.get('summary')}",
        "authorization_gated_execution_checklist:",
    ]
    for item in report.get("authorization_gated_execution_checklist", []):
        lines.append(f"  - {item.get('id')}: status={item.get('status')}")
        if item.get("path"):
            lines.append(f"    path={item.get('path')}")
        if item.get("command"):
            lines.append(f"    command={item.get('command')}")
    blocked = report.get("blocked_report")
    if isinstance(blocked, dict):
        lines.append("blocked_report:")
        lines.append(f"  status={blocked.get('status')}")
        for reason in blocked.get("blocked_reasons", []):
            lines.append(f"  - {reason}")
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
        preflight = _load_structured(args.authorization_preflight)
        access_report = _load_optional_access_report(args.balfrin_access_json)
        report = build_report(
            preflight,
            preflight_path=args.authorization_preflight,
            run_root=args.run_root,
            access_report=access_report,
            access_report_path=args.balfrin_access_json,
            non_git_artifact_available=args.non_git_artifact_status == "available",
        )
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"balfrin authorization-gated multi-zone path error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["ready_for_measured_evidence_promotion"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
