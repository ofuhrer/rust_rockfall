#!/usr/bin/env python3
"""Recover target-area metric gaps from the preserved Balfrin run root.

This helper is read-only. It consumes the Balfrin access preflight, inspects
the existing authorized target-area run root, and classifies the current
metrics-completion rerun targets as recovered or still blocked by preserved
evidence. It does not submit jobs, cancel jobs, write remote files, or grant
authorization.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import check_balfrin_remote_access_preflight as access_preflight  # noqa: E402
from scripts import collect_balfrin_probe_metrics as probe_metrics  # noqa: E402
from scripts import summarize_balfrin_target_area_metrics_completion_rerun_package as rerun_package  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_metrics_recovery_v1"
REPORT_BASENAME = "balfrin_target_area_metrics_recovery_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_metrics_recovery_v1"
ACCESS_READY_STATUS = access_preflight.STATUS_READY
REQUIRED_RECOVERY_METRICS = list(rerun_package.REQUIRED_METRICS)

STATUS_COMPLETE = "complete_gap_closed"
STATUS_RERUN_STILL_REQUIRED = "rerun_still_required"
STATUS_BLOCKED_ACCESS = "blocked_access"
STATUS_COLLECTION_FAILED = "blocked_collection_failed"

RECOVERY_RECOVERED = "recovered"
RECOVERY_STILL_MISSING = "still_missing"
RECOVERY_UNAVAILABLE_FROM_ROOT = "unavailable_from_preserved_root"
RECOVERY_BLOCKED_ACCESS = "blocked_access"

Runner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        default=str(access_preflight.DEFAULT_RUN_ROOT),
        help="Existing authorized Balfrin target-area run root.",
    )
    parser.add_argument(
        "--remote-repo-root",
        default=access_preflight.DEFAULT_REMOTE_REPO_ROOT,
        help="Balfrin git checkout used for read-only remote collection.",
    )
    parser.add_argument(
        "--ssh-target",
        default=access_preflight.DEFAULT_SSH_TARGET,
        help="SSH host alias for Balfrin.",
    )
    parser.add_argument(
        "--connect-timeout",
        type=int,
        default=10,
        help="SSH ConnectTimeout in seconds.",
    )
    parser.add_argument(
        "--balfrin-access-json",
        type=Path,
        default=None,
        help="Optional TB-223 Balfrin access preflight JSON.",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional pre-collected probe metrics JSON.",
    )
    parser.add_argument(
        "--local-run-root",
        type=Path,
        default=None,
        help="Local fixture or mounted run root. Skips SSH collection.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Optional directory for the JSON and text report.",
    )
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _metric_value(evidence: dict[str, Any], metric: str) -> Any:
    if metric == "memory_peak_mb":
        return evidence.get("memory_peak_mb")
    if metric == "validation_output.file_count":
        return evidence.get("validation_output_file_count")
    if metric == "validation_output.bytes":
        return evidence.get("validation_output_bytes")
    if metric == "hazard_output.file_count":
        return evidence.get("hazard_output_file_count")
    if metric == "hazard_output.bytes":
        return evidence.get("hazard_output_bytes")
    return None


def _metric_status_entry(evidence: dict[str, Any], metric: str) -> dict[str, Any]:
    metric_statuses = _safe_mapping(evidence.get("metric_statuses"))
    mandatory_statuses = _safe_mapping(metric_statuses.get("mandatory"))
    return _safe_mapping(mandatory_statuses.get(metric))


def _classify_metric(
    evidence: dict[str, Any],
    metric: str,
    *,
    collection_mode: str,
) -> dict[str, Any]:
    status_entry = _metric_status_entry(evidence, metric)
    value = _metric_value(evidence, metric)
    if status_entry.get("status") == "measured" and value is not None:
        recovery_status = RECOVERY_RECOVERED
        reason = ""
    else:
        run_root_status = str(evidence.get("run_root_status") or evidence.get("report_status") or "unknown")
        if run_root_status == "measured_run_root":
            recovery_status = RECOVERY_UNAVAILABLE_FROM_ROOT
            reason = (
                "the preserved run root was readable, but this metric was not retained "
                "in the collector-visible run-root evidence"
            )
        else:
            recovery_status = RECOVERY_STILL_MISSING
            reason = (
                "the preserved run root did not provide enough collector-visible inputs "
                "to classify this metric as recovered"
            )
    return {
        "metric": metric,
        "status": recovery_status,
        "value": value,
        "collector_status": status_entry.get("status", "unknown"),
        "collector_source": status_entry.get("source"),
        "collector_reason": status_entry.get("reason", ""),
        "recovery_source": collection_mode,
        "reason": reason,
    }


def _blocked_metric(metric: str, access_status: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "status": RECOVERY_BLOCKED_ACCESS,
        "value": None,
        "collector_status": "not_run",
        "collector_source": None,
        "collector_reason": "",
        "recovery_source": "balfrin_access_preflight",
        "reason": f"Balfrin read-only access preflight status is {access_status}",
    }


def _collection_failed_metric(metric: str, reason: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "status": RECOVERY_BLOCKED_ACCESS,
        "value": None,
        "collector_status": "collection_failed",
        "collector_source": None,
        "collector_reason": reason,
        "recovery_source": "remote_collector",
        "reason": reason,
    }


def _ssh_base_args(ssh_target: str, connect_timeout: int) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        ssh_target,
    ]


def _remote_collect_command(remote_repo_root: str, run_root: str) -> str:
    return (
        "cd "
        + shlex.quote(str(PurePosixPath(remote_repo_root)))
        + " && PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root "
        + shlex.quote(str(PurePosixPath(run_root)))
    )


def _trim(value: str | None, limit: int = 1200) -> str:
    if value is None:
        return ""
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _collect_remote_evidence(
    *,
    ssh_target: str,
    remote_repo_root: str,
    run_root: str,
    connect_timeout: int,
    runner: Runner,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    remote_command = _remote_collect_command(remote_repo_root, run_root)
    command = [*_ssh_base_args(ssh_target, connect_timeout), remote_command]
    try:
        result = runner(command, check=False, capture_output=True, text=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, {
            "status": STATUS_COLLECTION_FAILED,
            "command": command,
            "remote_command": remote_command,
            "returncode": None,
            "stdout": "",
            "stderr": _trim(str(exc)),
        }

    diagnostic = {
        "status": "complete" if result.returncode == 0 else STATUS_COLLECTION_FAILED,
        "command": command,
        "remote_command": remote_command,
        "returncode": result.returncode,
        "stdout": _trim(result.stdout),
        "stderr": _trim(result.stderr),
    }
    if result.returncode != 0:
        return None, diagnostic
    try:
        evidence = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        diagnostic["status"] = STATUS_COLLECTION_FAILED
        diagnostic["stderr"] = _trim(f"{diagnostic['stderr']}\ninvalid JSON from remote collector: {exc}")
        return None, diagnostic
    if not isinstance(evidence, dict):
        diagnostic["status"] = STATUS_COLLECTION_FAILED
        diagnostic["stderr"] = _trim(f"{diagnostic['stderr']}\nremote collector did not return a JSON object")
        return None, diagnostic
    diagnostic["stdout"] = "<json elided>"
    return evidence, diagnostic


def _access_report_from_inputs(
    explicit_access_preflight: dict[str, Any] | None,
    *,
    ssh_target: str,
    remote_repo_root: str,
    run_root: str,
    connect_timeout: int,
    runner: Runner,
    run_preflight: bool,
) -> dict[str, Any]:
    if explicit_access_preflight is not None:
        return dict(explicit_access_preflight)
    if not run_preflight:
        return {
            "schema_version": access_preflight.SCHEMA_VERSION,
            "status": "not_required_for_local_or_evidence_input",
            "ready_for_read_only_collection": True,
            "read_only": True,
            "live_submission_authorized": False,
            "ssh_target": ssh_target,
            "remote_repo_root": str(PurePosixPath(remote_repo_root)),
            "run_root": str(PurePosixPath(run_root)),
            "checked_commands": [],
        }
    return access_preflight.collect_preflight_report(
        ssh_target=ssh_target,
        remote_repo_root=remote_repo_root,
        run_root=run_root,
        connect_timeout=connect_timeout,
        runner=runner,
    )


def _build_rerun_comparison(
    *,
    access_report: dict[str, Any],
    recovery_entries: list[dict[str, Any]],
    run_root: str,
) -> dict[str, Any]:
    unrecovered = [
        entry["metric"]
        for entry in recovery_entries
        if entry.get("status") != RECOVERY_RECOVERED
    ]
    access_status = str(access_report.get("status") or "unknown")
    if any(entry.get("status") == RECOVERY_BLOCKED_ACCESS for entry in recovery_entries):
        status = STATUS_BLOCKED_ACCESS
        rerun_still_necessary: bool | None = None
        summary = "Read-only access is blocked, so the helper cannot determine whether the rerun is still necessary."
    elif unrecovered:
        status = STATUS_RERUN_STILL_REQUIRED
        rerun_still_necessary = True
        summary = (
            "The preserved target-area run root does not close every required metrics gap; "
            "the metrics-completion rerun remains necessary for unrecovered fields."
        )
    else:
        status = "rerun_not_necessary_for_required_metrics"
        rerun_still_necessary = False
        summary = (
            "The preserved target-area run root closes the required metrics gap; "
            "the current metrics-completion rerun package is not necessary for these fields."
        )

    rerun_report = rerun_package.build_report(
        {"balfrin_access_preflight": access_report},
        run_root=rerun_package.DEFAULT_RERUN_RUN_ROOT,
        probe_manifest=rerun_package.DEFAULT_PROBE_MANIFEST,
        artifact_dir=rerun_package.DEFAULT_ARTIFACT_DIR,
        balfrin_access_preflight=access_report,
        balfrin_access_preflight_source="embedded_in_recovery_report",
    )
    return {
        "schema_version": "balfrin_target_area_metrics_recovery_rerun_comparison_v1",
        "status": status,
        "rerun_still_necessary": rerun_still_necessary,
        "required_recovery_metrics": list(REQUIRED_RECOVERY_METRICS),
        "recovered_metrics": [
            entry["metric"]
            for entry in recovery_entries
            if entry.get("status") == RECOVERY_RECOVERED
        ],
        "unrecovered_metrics": unrecovered,
        "current_rerun_package_status": rerun_report.get("package_status"),
        "current_rerun_package_preflight_status": rerun_report.get("preflight_status"),
        "current_rerun_package_closure_targets": rerun_report.get("existing_target_area_run_comparison", {}).get(
            "closure_targets",
            [],
        ),
        "existing_target_area_run_root": run_root,
        "balfrin_access_status": access_status,
        "summary": summary,
    }


def build_report(
    *,
    access_report: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    local_run_root: Path | None = None,
    run_root: str = str(access_preflight.DEFAULT_RUN_ROOT),
    remote_repo_root: str = access_preflight.DEFAULT_REMOTE_REPO_ROOT,
    ssh_target: str = access_preflight.DEFAULT_SSH_TARGET,
    connect_timeout: int = 10,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    collection_diagnostic: dict[str, Any] = {"status": "not_run"}
    collection_mode = "precollected_evidence"
    should_run_preflight = evidence is None and local_run_root is None
    access = _access_report_from_inputs(
        access_report,
        ssh_target=ssh_target,
        remote_repo_root=remote_repo_root,
        run_root=run_root,
        connect_timeout=connect_timeout,
        runner=runner,
        run_preflight=should_run_preflight,
    )
    access_status = str(access.get("status") or "unknown")

    if evidence is None and local_run_root is None and access_status != ACCESS_READY_STATUS:
        recovery_entries = [_blocked_metric(metric, access_status) for metric in REQUIRED_RECOVERY_METRICS]
        comparison = _build_rerun_comparison(access_report=access, recovery_entries=recovery_entries, run_root=run_root)
        return {
            "schema_version": SCHEMA_VERSION,
            "report_status": STATUS_BLOCKED_ACCESS,
            "read_only": True,
            "live_submission_authorized": False,
            "run_root": run_root,
            "remote_repo_root": remote_repo_root,
            "ssh_target": ssh_target,
            "balfrin_access_preflight": access,
            "collection": collection_diagnostic,
            "recovery": _recovery_summary(recovery_entries),
            "rerun_comparison": comparison,
            "claim_boundaries": _claim_boundaries(),
            "summary": comparison["summary"],
        }

    if evidence is None and local_run_root is not None:
        collection_mode = "local_run_root"
        evidence = probe_metrics.collect_run_metrics(local_run_root)
        collection_diagnostic = {
            "status": "complete",
            "mode": collection_mode,
            "run_root": str(local_run_root),
        }
    elif evidence is None:
        collection_mode = "remote_read_only_collector"
        evidence, collection_diagnostic = _collect_remote_evidence(
            ssh_target=ssh_target,
            remote_repo_root=remote_repo_root,
            run_root=run_root,
            connect_timeout=connect_timeout,
            runner=runner,
        )

    if evidence is None:
        reason = str(collection_diagnostic.get("stderr") or "remote collection failed")
        recovery_entries = [_collection_failed_metric(metric, reason) for metric in REQUIRED_RECOVERY_METRICS]
        comparison = _build_rerun_comparison(access_report=access, recovery_entries=recovery_entries, run_root=run_root)
        return {
            "schema_version": SCHEMA_VERSION,
            "report_status": STATUS_COLLECTION_FAILED,
            "read_only": True,
            "live_submission_authorized": False,
            "run_root": run_root,
            "remote_repo_root": remote_repo_root,
            "ssh_target": ssh_target,
            "balfrin_access_preflight": access,
            "collection": collection_diagnostic,
            "recovery": _recovery_summary(recovery_entries),
            "rerun_comparison": comparison,
            "claim_boundaries": _claim_boundaries(),
            "summary": comparison["summary"],
        }

    evidence_run_root = str(evidence.get("run_root") or (local_run_root if local_run_root is not None else run_root))
    recovery_entries = [
        _classify_metric(evidence, metric, collection_mode=collection_mode)
        for metric in REQUIRED_RECOVERY_METRICS
    ]
    comparison = _build_rerun_comparison(access_report=access, recovery_entries=recovery_entries, run_root=evidence_run_root)
    report_status = STATUS_COMPLETE if comparison["rerun_still_necessary"] is False else STATUS_RERUN_STILL_REQUIRED
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": report_status,
        "read_only": True,
        "live_submission_authorized": False,
        "run_root": evidence_run_root,
        "remote_repo_root": remote_repo_root,
        "ssh_target": ssh_target,
        "balfrin_access_preflight": access,
        "collection": collection_diagnostic,
        "source_metrics_contract": {
            "status": evidence.get("metrics_contract_status"),
            "run_root_status": evidence.get("run_root_status"),
            "missing_metrics": _safe_list(evidence.get("metrics_contract_missing_metrics")),
            "ancillary_unavailable_metrics": _safe_list(
                evidence.get("metrics_contract_ancillary_unavailable_metrics")
            ),
            "hazard_manifest_path": evidence.get("hazard_manifest_path"),
        },
        "recovery": _recovery_summary(recovery_entries),
        "rerun_comparison": comparison,
        "claim_boundaries": _claim_boundaries(),
    }
    report["summary"] = summarize_report(report)
    return report


def _recovery_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    by_metric: dict[str, dict[str, Any]] = {}
    for entry in entries:
        status = str(entry.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        by_metric[str(entry.get("metric"))] = entry
    return {
        "status": "complete" if counts.get(RECOVERY_RECOVERED, 0) == len(REQUIRED_RECOVERY_METRICS) else "incomplete",
        "required_metrics": list(REQUIRED_RECOVERY_METRICS),
        "entries": entries,
        "by_metric": by_metric,
        "status_counts": counts,
        "recovered_metrics": [entry["metric"] for entry in entries if entry.get("status") == RECOVERY_RECOVERED],
        "unrecovered_metrics": [entry["metric"] for entry in entries if entry.get("status") != RECOVERY_RECOVERED],
    }


def _claim_boundaries() -> dict[str, bool]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "live_submission_authorized": False,
    }


def summarize_report(report: dict[str, Any]) -> str:
    recovery = report.get("recovery", {}) if isinstance(report, dict) else {}
    counts = recovery.get("status_counts", {}) if isinstance(recovery, dict) else {}
    comparison = report.get("rerun_comparison", {}) if isinstance(report, dict) else {}
    return (
        "Balfrin target-area metrics recovery "
        f"{report.get('report_status', 'unknown')}: "
        f"{counts.get(RECOVERY_RECOVERED, 0)} recovered, "
        f"{counts.get(RECOVERY_STILL_MISSING, 0)} still missing, "
        f"{counts.get(RECOVERY_UNAVAILABLE_FROM_ROOT, 0)} unavailable from preserved root, "
        f"{counts.get(RECOVERY_BLOCKED_ACCESS, 0)} blocked by access. "
        f"{comparison.get('summary', '')}"
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Metrics Recovery",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"report_status: {report.get('report_status', 'unknown')}",
        f"read_only: {report.get('read_only', True)}",
        f"live_submission_authorized: {report.get('live_submission_authorized', False)}",
        f"run_root: {report.get('run_root', 'unknown')}",
        f"ssh_target: {report.get('ssh_target', 'unknown')}",
        f"remote_repo_root: {report.get('remote_repo_root', 'unknown')}",
        f"summary: {report.get('summary', '')}",
    ]
    access = report.get("balfrin_access_preflight", {}) if isinstance(report, dict) else {}
    lines.extend(
        [
            "balfrin_access_preflight:",
            f"  status: {access.get('status', 'unknown')}",
            f"  ready_for_read_only_collection: {access.get('ready_for_read_only_collection', False)}",
            f"  live_submission_authorized: {access.get('live_submission_authorized', False)}",
        ]
    )
    collection = report.get("collection", {}) if isinstance(report, dict) else {}
    lines.extend(
        [
            "collection:",
            f"  status: {collection.get('status', 'unknown')}",
            f"  mode: {collection.get('mode', '')}",
            f"  returncode: {collection.get('returncode')}",
        ]
    )
    recovery = report.get("recovery", {}) if isinstance(report, dict) else {}
    lines.append("recovery:")
    lines.append(f"  status: {recovery.get('status', 'unknown')}")
    lines.append(f"  status_counts: {recovery.get('status_counts', {})}")
    for entry in recovery.get("entries", []):
        lines.append(
            "  - "
            f"{entry.get('metric')}: {entry.get('status')} value={entry.get('value')} "
            f"collector_status={entry.get('collector_status')} reason={entry.get('reason', '')}"
        )
    comparison = report.get("rerun_comparison", {}) if isinstance(report, dict) else {}
    lines.extend(
        [
            "rerun_comparison:",
            f"  status: {comparison.get('status', 'unknown')}",
            f"  rerun_still_necessary: {comparison.get('rerun_still_necessary')}",
            f"  recovered_metrics: {comparison.get('recovered_metrics', [])}",
            f"  unrecovered_metrics: {comparison.get('unrecovered_metrics', [])}",
            f"  current_rerun_package_status: {comparison.get('current_rerun_package_status', '')}",
            f"  current_rerun_package_preflight_status: {comparison.get('current_rerun_package_preflight_status', '')}",
            f"  current_rerun_package_closure_targets: {comparison.get('current_rerun_package_closure_targets', [])}",
            f"  summary: {comparison.get('summary', '')}",
        ]
    )
    boundaries = report.get("claim_boundaries", {}) if isinstance(report, dict) else {}
    lines.append("claim_boundaries:")
    for key in (
        "operational_claims_allowed",
        "physical_probability_claims_allowed",
        "annual_frequency_claims_allowed",
        "risk_exposure_vulnerability_claims_allowed",
        "scale_up_authorized",
        "distributed_execution_authorized",
        "live_submission_authorized",
    ):
        lines.append(f"  {key}: {boundaries.get(key)}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or (artifact_dir / f"{REPORT_BASENAME}.json")
        text_output = text_output or (artifact_dir / f"{REPORT_BASENAME}.txt")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        access_report = _load_json(args.balfrin_access_json)
        evidence = _load_json(args.evidence_json)
        report = build_report(
            access_report=access_report,
            evidence=evidence,
            local_run_root=args.local_run_root,
            run_root=args.run_root,
            remote_repo_root=args.remote_repo_root,
            ssh_target=args.ssh_target,
            connect_timeout=args.connect_timeout,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"balfrin target-area metrics recovery error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(
        report,
        json_output=args.json_output,
        text_output=args.text_output,
        artifact_dir=args.artifact_dir,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 2 if report["report_status"] in {STATUS_BLOCKED_ACCESS, STATUS_COLLECTION_FAILED} else 0


if __name__ == "__main__":
    raise SystemExit(main())
