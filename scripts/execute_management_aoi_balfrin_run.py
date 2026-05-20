#!/usr/bin/env python3
"""Build the TB-381 management-AOI Balfrin execution state.

This helper is intentionally fail-closed for the current management-AOI state:
it consumes the TB-380 handoff package classification and records that no
Balfrin job was submitted when prepared-pilot inputs are missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_management_aoi_balfrin_handoff as handoff  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "management_aoi_balfrin_execution_state_v1"
DEFAULT_ARTIFACT_DIR = Path("/tmp/rust_rockfall/tb381_management_aoi_balfrin_execution_state")
DEFAULT_REPORT_JSON = DEFAULT_ARTIFACT_DIR / "management_aoi_balfrin_execution_state_v1.json"
DEFAULT_REPORT_TXT = DEFAULT_ARTIFACT_DIR / "management_aoi_balfrin_execution_state_v1.txt"


class ManagementAoiBalfrinExecutionStateError(ValueError):
    """User-facing execution-state error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--handoff-artifact-dir", type=Path, default=handoff.DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--prepared-pilot-output-root", type=Path, default=handoff.DEFAULT_PREPARED_PILOT_OUTPUT_ROOT)
    parser.add_argument("--run-root", type=Path, default=handoff.DEFAULT_RUN_ROOT)
    parser.add_argument("--run-id", default=handoff.DEFAULT_RUN_ID)
    parser.add_argument("--balfrin-access-preflight-json", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        access_preflight_report = load_json(args.balfrin_access_preflight_json) if args.balfrin_access_preflight_json else None
        report = build_report(
            artifact_dir=args.artifact_dir,
            handoff_artifact_dir=args.handoff_artifact_dir,
            prepared_pilot_output_root=args.prepared_pilot_output_root,
            run_root=args.run_root,
            run_id=args.run_id,
            access_preflight_report=access_preflight_report,
            access_preflight_source=str(args.balfrin_access_preflight_json) if args.balfrin_access_preflight_json else None,
        )
    except ManagementAoiBalfrinExecutionStateError as exc:
        print(f"management AOI Balfrin execution-state error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["execution_status"] == "measured" else 2


def build_report(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    handoff_artifact_dir: Path = handoff.DEFAULT_ARTIFACT_DIR,
    prepared_pilot_output_root: Path = handoff.DEFAULT_PREPARED_PILOT_OUTPUT_ROOT,
    run_root: Path = handoff.DEFAULT_RUN_ROOT,
    run_id: str = handoff.DEFAULT_RUN_ID,
    handoff_report_override: dict[str, Any] | None = None,
    access_preflight_report: dict[str, Any] | None = None,
    access_preflight_source: str | None = None,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    handoff_artifact_dir = resolve_output_root(handoff_artifact_dir)
    prepared_pilot_output_root = resolve_output_root(prepared_pilot_output_root)
    if not all(
        is_allowed_output_root(path)
        for path in (artifact_dir, handoff_artifact_dir, prepared_pilot_output_root)
    ):
        raise ManagementAoiBalfrinExecutionStateError("artifact roots must stay under /tmp or validation/private")

    handoff_report = handoff_report_override or handoff.build_report(
        artifact_dir=handoff_artifact_dir,
        prepared_pilot_output_root=prepared_pilot_output_root,
        run_root=run_root,
        run_id=run_id,
        access_preflight_report=access_preflight_report,
        access_preflight_source=access_preflight_source,
    )
    handoff_status = str(handoff_report.get("handoff_classification") or handoff_report.get("handoff_status") or "")
    first_blocker = first_persistent_blocker(handoff_report, handoff_status)
    no_submit = build_no_submit_semantics(handoff_report, handoff_status, first_blocker, access_preflight_report)
    execution_status = "failed_closed" if handoff_status != "ready" else "ready_not_submitted"

    return {
        "schema_version": SCHEMA_VERSION,
        "execution_status": execution_status,
        "execution_classification": execution_status,
        "measurement_status": "not_measured",
        "task_id": "TB-381",
        "handoff_schema_version": handoff_report.get("schema_version"),
        "handoff_classification": handoff_status,
        "ready_for_live_management_aoi_postproc_run": handoff_report.get(
            "ready_for_live_management_aoi_postproc_run", False
        ),
        "first_persistent_blocker": first_blocker,
        "blocked_reason": first_blocker.get("blocked_reason", ""),
        "artifact_dir": str(artifact_dir),
        "report_json_path": str(artifact_dir / DEFAULT_REPORT_JSON.name),
        "report_text_path": str(artifact_dir / DEFAULT_REPORT_TXT.name),
        "handoff_package_json_path": handoff_report.get("package_json_path"),
        "handoff_authorization_record_path": handoff_report.get("authorization_record_path"),
        "run_root": handoff_report.get("exact_run_root") or str(run_root),
        "run_id": handoff_report.get("run_id") or run_id,
        "partition": handoff_report.get("partition") or "postproc",
        "job_id": None,
        "runtime_seconds": None,
        "memory_peak_mb": None,
        "validation_output_pressure": {
            "status": "not_evaluated",
            "reason": "no validation outputs exist because no Balfrin job was submitted",
        },
        "hazard_output_pressure": {
            "status": "not_evaluated",
            "reason": "no hazard outputs exist because no Balfrin job was submitted",
        },
        "reducer_pressure": {
            "status": "not_evaluated",
            "reason": "reducer pressure cannot be measured without prepared-pilot scenario rows",
        },
        "preservation_evidence": {
            "status": "fail_closed_no_run_root_created",
            "scratch_report_dir": str(artifact_dir),
            "handoff_artifact_dir": str(handoff_artifact_dir),
            "balfrin_run_root_created": False,
            "do_not_commit_paths": [
                str(artifact_dir),
                str(handoff_artifact_dir),
                str(prepared_pilot_output_root),
                str(handoff_report.get("exact_run_root") or run_root),
            ],
        },
        "candidate_evidence": dict(handoff_report.get("candidate_evidence") or {}),
        "scenario_generation_pressure": dict(handoff_report.get("scenario_generation_pressure") or {}),
        "budget_checks": list(handoff_report.get("budget_checks") or []),
        "authorization_audit": dict(handoff_report.get("authorization_audit") or {}),
        "no_submit_semantics": no_submit,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "live_submission_authorized": False,
        },
        "decision_note": (
            "TB-381 did not submit a Balfrin job because TB-380 classified the management-AOI handoff as "
            "`blocked_missing_prepared_pilot_inputs`; the first persistent blocker is the preserved empty candidate set."
            if handoff_status != "ready"
            else "The handoff reports ready, but this helper does not submit jobs; use the reviewed live-submit path."
        ),
    }


def first_persistent_blocker(handoff_report: dict[str, Any], handoff_status: str) -> dict[str, Any]:
    scenario = dict(handoff_report.get("scenario_generation_pressure") or {})
    candidate = dict(handoff_report.get("candidate_evidence") or {})
    blocked_reason = str(handoff_report.get("blocked_reason") or "").strip()
    if int(candidate.get("candidate_cell_count") or 0) == 0:
        return {
            "status": "blocked_empty_candidate_set",
            "source_status": scenario.get("scenario_pressure_status") or "blocked_empty_candidate_set",
            "handoff_classification": handoff_status,
            "blocked_reason": blocked_reason
            or "zero management-AOI candidate cells prevent scenario-row generation",
            "candidate_cell_count": int(candidate.get("candidate_cell_count") or 0),
            "candidate_area_m2": float(candidate.get("candidate_area_m2") or 0.0),
            "scenario_row_count": int(scenario.get("scenario_row_count") or 0),
        }
    return {
        "status": handoff_status or "blocked_missing_prepared_pilot_inputs",
        "handoff_classification": handoff_status,
        "blocked_reason": blocked_reason or handoff_status,
        "scenario_row_count": int(scenario.get("scenario_row_count") or 0),
    }


def build_no_submit_semantics(
    handoff_report: dict[str, Any],
    handoff_status: str,
    first_blocker: dict[str, Any],
    access_preflight_report: dict[str, Any] | None,
) -> dict[str, Any]:
    access_status = access_preflight_report.get("status") if access_preflight_report else "not_supplied"
    return {
        "sbatch_attempted": False,
        "scheduler_submission_status": "not_attempted",
        "balfrin_job_submitted": False,
        "live_submission_authorized": False,
        "read_only_access_preflight_status": access_status,
        "handoff_ready": handoff_status == "ready",
        "blocked_before_scheduler_gate": handoff_status != "ready",
        "first_scheduler_safe_blocker": first_blocker.get("status"),
        "future_submit_command_runnable_now": any(
            command.get("command_id") == "future_authorized_submit" and command.get("runnable_now") is True
            for command in handoff_report.get("command_list", [])
        ),
        "boundary_note": "No sbatch command was run; TB-381 preserves fail-closed evidence only.",
    }


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_json = Path(report["report_json_path"])
    report_text = Path(report["report_text_path"])
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_text.write_text(render_text_report(report) + "\n", encoding="utf-8")
    if json_output is not None and Path(json_output) != report_json:
        Path(json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(json_output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None and Path(text_output) != report_text:
        Path(text_output).parent.mkdir(parents=True, exist_ok=True)
        Path(text_output).write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    blocker = dict(report.get("first_persistent_blocker") or {})
    lines = [
        "Management AOI Balfrin Execution State",
        "",
        f"- execution_status: `{report['execution_status']}`",
        f"- handoff_classification: `{report['handoff_classification']}`",
        f"- sbatch_attempted: `{report['no_submit_semantics']['sbatch_attempted']}`",
        f"- first_persistent_blocker: `{blocker.get('status')}`",
        f"- blocked_reason: {blocker.get('blocked_reason', '')}",
        f"- candidate_cell_count: `{blocker.get('candidate_cell_count', 0)}`",
        f"- scenario_row_count: `{blocker.get('scenario_row_count', 0)}`",
        f"- run_root: `{report['run_root']}`",
        f"- partition: `{report['partition']}`",
        f"- report_json_path: `{report['report_json_path']}`",
        "",
        "Measured Outputs",
        "- job_id: `None`",
        "- runtime_seconds: `None`",
        "- memory_peak_mb: `None`",
        f"- validation_output_pressure: `{report['validation_output_pressure']['status']}`",
        f"- hazard_output_pressure: `{report['hazard_output_pressure']['status']}`",
        f"- reducer_pressure: `{report['reducer_pressure']['status']}`",
        "",
        "Boundary",
        f"- {report['decision_note']}",
    ]
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
