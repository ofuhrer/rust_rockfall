#!/usr/bin/env python3
"""Build the management-AOI Balfrin multi-zone handoff classification.

This helper turns the current management-AOI prepared-pilot state into a
bounded Balfrin handoff package without submitting a job or pretending that a
runnable multi-zone scenario table exists.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib import workflow_validation as WORKFLOW_VALIDATION  # noqa: E402


SCHEMA_VERSION = "management_aoi_balfrin_handoff_v1"
DEFAULT_ARTIFACT_DIR = Path("/tmp/rust_rockfall/tb386_management_aoi_balfrin_handoff")
DEFAULT_PREPARED_PILOT_OUTPUT_ROOT = Path("/tmp/rust_rockfall/tb386_management_aoi_prepared_pilot")
DEFAULT_PACKAGE_JSON = DEFAULT_ARTIFACT_DIR / "management_aoi_balfrin_handoff_v1.json"
DEFAULT_PACKAGE_TXT = DEFAULT_ARTIFACT_DIR / "management_aoi_balfrin_handoff_v1.txt"
DEFAULT_AUTHORIZATION_RECORD = DEFAULT_ARTIFACT_DIR / "management_aoi_balfrin_authorization_audit_v1.yaml"
DEFAULT_RUN_ROOT = Path(
    "/scratch/mch/olifu/rust_rockfall/probes/management-aoi/"
    "chant_sura_fluelapass_management_aoi_multi_zone_v1"
)
DEFAULT_RUN_ID = "chant_sura_fluelapass_management_aoi_multi_zone_v1"
ACCESS_PREFLIGHT_COMMAND = (
    WORKFLOW_VALIDATION.render_shell_command(
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/check_balfrin_remote_access_preflight.py",
        "--format",
        "json",
    )
)


class ManagementAoiBalfrinHandoffError(ValueError):
    """User-facing handoff package error."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


PREPARED_PILOT = _load_module(
    "management_aoi_handoff_prepared_pilot",
    "plan_aoi_to_prepared_pilot_dry_run.py",
)
SCENARIO_PRESSURE = _load_module(
    "management_aoi_handoff_scenario_pressure",
    "summarize_management_aoi_scenario_pressure.py",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--prepared-pilot-output-root", type=Path, default=DEFAULT_PREPARED_PILOT_OUTPUT_ROOT)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--balfrin-access-preflight-json", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        access_preflight_report = load_json(args.balfrin_access_preflight_json) if args.balfrin_access_preflight_json else None
        report = build_report(
            artifact_dir=args.artifact_dir,
            prepared_pilot_output_root=args.prepared_pilot_output_root,
            run_root=args.run_root,
            run_id=args.run_id,
            access_preflight_report=access_preflight_report,
            access_preflight_source=str(args.balfrin_access_preflight_json) if args.balfrin_access_preflight_json else None,
        )
    except ManagementAoiBalfrinHandoffError as exc:
        print(f"management AOI Balfrin handoff error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["handoff_classification"] == "ready" else 2


def build_report(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    prepared_pilot_output_root: Path = DEFAULT_PREPARED_PILOT_OUTPUT_ROOT,
    run_root: Path = DEFAULT_RUN_ROOT,
    run_id: str = DEFAULT_RUN_ID,
    prepared_pilot_report_override: dict[str, Any] | None = None,
    scenario_pressure_report_override: dict[str, Any] | None = None,
    access_preflight_report: dict[str, Any] | None = None,
    access_preflight_source: str | None = None,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    prepared_pilot_output_root = resolve_output_root(prepared_pilot_output_root)
    if not is_allowed_output_root(artifact_dir) or not is_allowed_output_root(prepared_pilot_output_root):
        raise ManagementAoiBalfrinHandoffError("artifact roots must stay under /tmp or validation/private")

    prepared_pilot_report = prepared_pilot_report_override or PREPARED_PILOT.build_report(
        PREPARED_PILOT.DEFAULT_SITE_CONFIG,
        repo_root=ROOT,
        skeleton_output_root=prepared_pilot_output_root,
    )
    prepared_pilot_state = WORKFLOW_VALIDATION.summarize_prepared_pilot_state(prepared_pilot_report)
    scenario_pressure_report = scenario_pressure_report_override or dict(
        prepared_pilot_report.get("management_aoi_scenario_pressure") or {}
    )
    if not scenario_pressure_report:
        scenario_pressure_report = SCENARIO_PRESSURE.build_report(output_root=artifact_dir / "scenario_pressure")

    classification = classify_handoff(prepared_pilot_report, scenario_pressure_report)
    blocked_reason = build_blocked_reason(prepared_pilot_state, scenario_pressure_report, classification)
    budget_checks = build_budget_checks(classification, scenario_pressure_report)
    command_list = build_command_list(
        artifact_dir=artifact_dir,
        prepared_pilot_output_root=prepared_pilot_output_root,
        run_root=run_root,
        run_id=run_id,
        classification=classification,
    )
    authorization_audit = build_authorization_audit(
        artifact_dir=artifact_dir,
        run_root=run_root,
        run_id=run_id,
        classification=classification,
        blocked_reason=blocked_reason,
        access_preflight_report=access_preflight_report,
        access_preflight_source=access_preflight_source,
    )

    candidate_evidence = dict(scenario_pressure_report.get("candidate_evidence") or {})
    scenario_generation_pressure = dict(scenario_pressure_report.get("scenario_generation_pressure") or {})
    report = {
        "schema_version": SCHEMA_VERSION,
        "handoff_status": classification,
        "handoff_classification": classification,
        "submission_classification": classification,
        "ready_for_live_management_aoi_postproc_run": classification == "ready",
        "blocked_reason": blocked_reason,
        "artifact_dir": str(artifact_dir),
        "package_json_path": str(artifact_dir / DEFAULT_PACKAGE_JSON.name),
        "package_text_path": str(artifact_dir / DEFAULT_PACKAGE_TXT.name),
        "authorization_record_path": str(artifact_dir / DEFAULT_AUTHORIZATION_RECORD.name),
        "prepared_pilot_output_root": str(prepared_pilot_output_root),
        "exact_run_root": str(run_root),
        "run_id": run_id,
        "partition": "postproc",
        "live_submission_permitted_by_this_task": False,
        "prepared_pilot_summary": {
            "workflow_status": prepared_pilot_state["classification"],
            "prepared_pilot_compiler_classification": prepared_pilot_state["classification"],
            "prepared_pilot_input_classification": prepared_pilot_state["input_classification"],
            "case_skeleton_status": dict(prepared_pilot_report.get("case_skeleton_output") or {}).get("status"),
            "case_skeleton_path": dict(prepared_pilot_report.get("case_skeleton_output") or {}).get("case_skeleton_path"),
            "blocked_execution_status": dict(prepared_pilot_report.get("case_skeleton_output") or {}).get(
                "blocked_execution_status"
            ),
        },
        "candidate_evidence": {
            "candidate_cell_count": int(candidate_evidence.get("candidate_cell_count") or 0),
            "candidate_area_m2": float(candidate_evidence.get("candidate_area_m2") or 0.0),
            "candidate_release_zone_set_status": candidate_evidence.get("candidate_release_zone_set_status", ""),
            "review_summary": dict(candidate_evidence.get("review_summary") or {}),
        },
        "scenario_generation_pressure": {
            "scenario_pressure_status": scenario_pressure_report.get("scenario_pressure_status"),
            "scenario_row_count": int(scenario_generation_pressure.get("scenario_row_count") or 0),
            "scenario_table_total_bytes": int(scenario_generation_pressure.get("scenario_table_total_bytes") or 0),
            "manifest_pressure": dict(scenario_generation_pressure.get("manifest_pressure") or {}),
        },
        "reduced_output_mode": {
            "validation_output_mode": "rebuildable_reduced_output",
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "no_plots": True,
            "export_geotiff": True,
            "pilot_gis_package": True,
            "status": "specified_but_not_runnable" if classification != "ready" else "ready",
        },
        "budget_checks": budget_checks,
        "authorization_audit": authorization_audit,
        "command_list": command_list,
        "preservation_plan": build_preservation_plan(artifact_dir, prepared_pilot_output_root, run_root, classification),
        "source_evidence": {
            "scenario_pressure_report": dict(scenario_pressure_report.get("output_paths") or {}).get(
                "scenario_pressure_report_json"
            ),
            "candidate_source_inputs": dict(scenario_pressure_report.get("source_inputs") or {}),
            "prepared_pilot_ignored_output_roots": list(prepared_pilot_report.get("workflow_ignored_output_roots") or []),
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "live_submission_authorized": False,
            "postproc_only_for_future_live_work": True,
        },
        "decision_note": (
            "A live management-AOI postproc run cannot be attempted until the current prepared-pilot blocker is "
            "resolved; the current handoff is a blocked evidence package."
            if classification != "ready"
            else "Review all gates before any future live submission."
        ),
    }
    return report


def classify_handoff(prepared_pilot_report: dict[str, Any], scenario_pressure_report: dict[str, Any]) -> str:
    ordered_statuses = [
        str(scenario_pressure_report.get("scenario_pressure_status") or ""),
        str(dict(prepared_pilot_report.get("prepared_pilot_compiler") or {}).get("classification") or ""),
        str(prepared_pilot_report.get("workflow_status") or ""),
        str(prepared_pilot_report.get("prepared_pilot_input_classification") or ""),
    ]
    for status in ordered_statuses:
        if status == "blocked_missing_inputs":
            return "blocked_missing_prepared_pilot_inputs"
        if status.startswith("blocked_"):
            return status
    statuses = {
        str(prepared_pilot_report.get("workflow_status") or ""),
        str(dict(prepared_pilot_report.get("prepared_pilot_compiler") or {}).get("classification") or ""),
        str(scenario_pressure_report.get("scenario_pressure_status") or ""),
    }
    if "blocked_missing_inputs" in statuses:
        return "blocked_missing_prepared_pilot_inputs"
    return "ready"


def build_blocked_reason(
    prepared_pilot_report: dict[str, Any],
    scenario_pressure_report: dict[str, Any],
    classification: str,
) -> str:
    if classification == "ready":
        return ""
    scenario_reason = str(scenario_pressure_report.get("blocked_reason") or "").strip()
    if scenario_reason:
        return scenario_reason
    first_blocker = dict(prepared_pilot_report.get("first_blocker") or {})
    return str(first_blocker.get("blocked_reason") or first_blocker.get("status") or classification)


def build_budget_checks(classification: str, scenario_pressure_report: dict[str, Any]) -> list[dict[str, Any]]:
    scenario_pressure = dict(scenario_pressure_report.get("scenario_generation_pressure") or {})
    if classification != "ready":
        return [
            {
                "gate": "prepared_pilot_inputs",
                "status": "blocked",
                "classification": classification,
                "reason": "no executable prepared-pilot scenario table exists",
            },
            {
                "gate": "scenario_rows",
                "status": "blocked",
                "scenario_row_count": int(scenario_pressure.get("scenario_row_count") or 0),
                "reason": "zero scenario rows means output and reducer budgets cannot be accepted for a live run",
            },
            {
                "gate": "output_budget",
                "status": "not_evaluated",
                "classification": classification,
                "reason": "budget acceptance requires a resolved prepared-pilot contract, concrete multi-zone validation paths, and hazard output paths",
            },
        ]
    return [
        {
            "gate": "prepared_pilot_inputs",
            "status": "ready",
            "reason": "prepared-pilot inputs are present",
        }
    ]


def build_command_list(
    *,
    artifact_dir: Path,
    prepared_pilot_output_root: Path,
    run_root: Path,
    run_id: str,
    classification: str,
) -> list[dict[str, Any]]:
    command_status = classification if classification != "ready" else "ready"
    future_submit_command = (
        WORKFLOW_VALIDATION.render_shell_command(
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            "scripts/submit_balfrin_probe.py",
            "<management_aoi_prepared_pilot_contract.yaml>",
            "--run-root",
            WORKFLOW_VALIDATION.render_shell_arg(run_root),
            "--run-id",
            run_id,
            "--partition",
            "postproc",
            "--time",
            "00:30:00",
            "--nodes",
            "1",
            "--ntasks",
            "1",
            "--cpus-per-task",
            "16",
            "--authorized-submit",
            "--reviewed-handoff-package",
            WORKFLOW_VALIDATION.render_shell_arg(artifact_dir / DEFAULT_PACKAGE_JSON.name),
            "--authorization-record",
            WORKFLOW_VALIDATION.render_shell_arg(artifact_dir / DEFAULT_AUTHORIZATION_RECORD.name),
        )
    )
    return [
        {
            "command_id": "prepared_pilot_compiler",
            "status": command_status,
            "command": WORKFLOW_VALIDATION.render_shell_command(
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/plan_aoi_to_prepared_pilot_dry_run.py",
                "--output-root",
                WORKFLOW_VALIDATION.render_shell_arg(prepared_pilot_output_root),
                "--format",
                "json",
            ),
            "writes_only_ignored_outputs": True,
        },
        {
            "command_id": "scenario_pressure_summary",
            "status": command_status,
            "command": WORKFLOW_VALIDATION.render_shell_command(
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_management_aoi_scenario_pressure.py",
                "--format",
                "json",
            ),
            "writes_only_ignored_outputs": True,
        },
        {
            "command_id": "balfrin_access_preflight",
            "status": "read_only_preflight",
            "command": ACCESS_PREFLIGHT_COMMAND,
            "read_only": True,
        },
        {
            "command_id": "future_authorized_submit",
            "status": classification if classification != "ready" else "deferred_pending_authorization_audit",
            "command": future_submit_command,
            "runnable_now": classification == "ready",
            "boundary_note": "Do not run while the handoff is blocked; future live work must stay on postproc and pass all gates first.",
        },
    ]


def build_authorization_audit(
    *,
    artifact_dir: Path,
    run_root: Path,
    run_id: str,
    classification: str,
    blocked_reason: str,
    access_preflight_report: dict[str, Any] | None,
    access_preflight_source: str | None,
) -> dict[str, Any]:
    access_status = access_preflight_report.get("status") if access_preflight_report else "not_supplied_to_package"
    return {
        "schema_version": "management_aoi_balfrin_authorization_audit_v1",
        "status": classification,
        "authorization_record_path": str(artifact_dir / DEFAULT_AUTHORIZATION_RECORD.name),
        "run_root": str(run_root),
        "run_id": run_id,
        "partition": "postproc",
        "live_submission_authorized_by_this_record": False,
        "task_allows_live_submission": False,
        "access_preflight_status": access_status,
        "access_preflight_source": access_preflight_source or ACCESS_PREFLIGHT_COMMAND,
        "blocked_reason": blocked_reason,
        "standing_clearance_note": (
            "Standing postproc clearance remains a future-run audit input only; this blocked handoff permits no live submission."
        ),
    }


def build_preservation_plan(
    artifact_dir: Path,
    prepared_pilot_output_root: Path,
    run_root: Path,
    classification: str,
) -> dict[str, Any]:
    return {
        "status": classification,
        "scratch_handoff_artifact_dir": str(artifact_dir),
        "prepared_pilot_output_root": str(prepared_pilot_output_root),
        "future_balfrin_run_root": str(run_root),
        "do_not_commit_paths": [str(artifact_dir), str(prepared_pilot_output_root), str(run_root)],
        "required_future_evidence_before_submit": [
            "non-empty management-AOI candidate release-zone set",
            "non-empty deterministic scenario table",
            "prepared-pilot case contract with reduced-output controls",
            "accepted output-budget and reducer-pressure gates",
            "authorization/audit record generated for the exact run root",
        ],
    }


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    package_json = Path(report["package_json_path"])
    package_text = Path(report["package_text_path"])
    authorization_record = Path(report["authorization_record_path"])
    package_json.parent.mkdir(parents=True, exist_ok=True)
    package_text.parent.mkdir(parents=True, exist_ok=True)
    authorization_record.parent.mkdir(parents=True, exist_ok=True)
    package_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    package_text.write_text(render_text_report(report) + "\n", encoding="utf-8")
    if json_output is not None and Path(json_output) != package_json:
        Path(json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(json_output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None and Path(text_output) != package_text:
        Path(text_output).parent.mkdir(parents=True, exist_ok=True)
        Path(text_output).write_text(render_text_report(report) + "\n", encoding="utf-8")
    authorization_record.write_text(yaml.safe_dump(report["authorization_audit"], sort_keys=True), encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Management AOI Balfrin Handoff",
        "",
        f"- handoff_classification: `{report['handoff_classification']}`",
        f"- ready_for_live_management_aoi_postproc_run: `{report['ready_for_live_management_aoi_postproc_run']}`",
        f"- blocked_reason: {report.get('blocked_reason', '')}",
        f"- exact_run_root: `{report['exact_run_root']}`",
        f"- run_id: `{report['run_id']}`",
        f"- partition: `{report['partition']}`",
        f"- package_json_path: `{report['package_json_path']}`",
        f"- authorization_record_path: `{report['authorization_record_path']}`",
        "",
        "Prepared Pilot",
        f"- workflow_status: `{report['prepared_pilot_summary']['workflow_status']}`",
        f"- compiler_classification: `{report['prepared_pilot_summary']['prepared_pilot_compiler_classification']}`",
        f"- blocked_execution_status: `{report['prepared_pilot_summary']['blocked_execution_status']}`",
        "",
        "Candidate And Scenario Evidence",
        f"- candidate_cell_count: `{report['candidate_evidence']['candidate_cell_count']}`",
        f"- candidate_area_m2: `{report['candidate_evidence']['candidate_area_m2']}`",
        f"- scenario_pressure_status: `{report['scenario_generation_pressure']['scenario_pressure_status']}`",
        f"- scenario_row_count: `{report['scenario_generation_pressure']['scenario_row_count']}`",
        "",
        "Budget Checks",
    ]
    for check in report.get("budget_checks", []):
        lines.append(f"- {check.get('gate')}: {check.get('status')} ({check.get('reason', '')})")
    lines.extend(["", "Command List"])
    for command in report.get("command_list", []):
        lines.append(f"- {command.get('command_id')}: `{command.get('status')}`")
        lines.append(f"  {command.get('command')}")
    lines.extend(["", "Boundary", f"- {report['decision_note']}"])
    return "\n".join(lines)


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def resolve_output_root(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_allowed_output_root(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    allowed_roots = [
        Path("/tmp").resolve(strict=False),
        Path("/private/tmp").resolve(strict=False),
        (ROOT / "validation/private").resolve(strict=False),
    ]
    return any(resolved == root or root in resolved.parents for root in allowed_roots)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
