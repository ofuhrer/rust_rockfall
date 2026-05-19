#!/usr/bin/env python3
"""Summarize Balfrin probe metrics completeness for a measured run root.

This helper is read-only. It packages the collected Balfrin probe metrics into a
deterministic JSON/text report that explicitly separates mandatory metrics,
ancillary metrics, unavailable metrics, and next-run-required metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import collect_balfrin_probe_metrics as probe_metrics  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_probe_metrics_report_v1"
REPORT_BASENAME = "balfrin_probe_metrics_report_v1"
ALLOWED_METRICS_COMPLETION_SOURCES = {
    "recovered_existing_run_root",
    "new_metrics_completion_rerun",
    "blocked_missing_metrics",
    "blocked_pre_submit",
}
ALLOWED_METRICS_COMPLETION_OUTCOMES = {
    "measured",
    "recovered",
    "blocked",
    "incomplete",
}
METRICS_COMPLETION_RERUN_MARKERS = (
    "metrics_completion",
    "metrics-completion",
    "metrics_completion_v1",
    "metrics_completion_rerun",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Measured run root produced by submit_balfrin_probe.py.",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional pre-collected probe metrics JSON.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional JSON path to write the report.",
    )
    parser.add_argument(
        "--text-output",
        type=Path,
        default=None,
        help="Optional text path to write the report.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Optional directory for the JSON and text report.",
    )
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and str(item)]


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _collect_source_paths(source_paths: dict[str, Any] | None) -> list[str]:
    if not isinstance(source_paths, dict):
        return []
    collected: list[str] = []
    for value in source_paths.values():
        if isinstance(value, str) and value:
            collected.append(value)
        elif isinstance(value, list):
            collected.extend(str(item) for item in value if isinstance(item, str) and item)
        elif isinstance(value, dict):
            collected.extend(_collect_source_paths(value))
    return collected


def classify_metrics_completion_source(
    *,
    report_status: str,
    metrics_contract_status: str,
    source_paths: dict[str, Any] | None = None,
    explicit_source: str | None = None,
) -> str:
    if explicit_source in ALLOWED_METRICS_COMPLETION_SOURCES:
        return explicit_source
    if report_status == "blocked_missing_run_root" or metrics_contract_status != "complete":
        return "blocked_missing_metrics"
    for source_path in _collect_source_paths(source_paths):
        if any(marker in source_path for marker in METRICS_COMPLETION_RERUN_MARKERS):
            return "new_metrics_completion_rerun"
    return "recovered_existing_run_root"


def classify_metrics_completion_outcome(
    *,
    report_status: str,
    metrics_contract_status: str,
    metrics_completion_source: str,
    explicit_outcome: str | None = None,
    attempt_status: str | None = None,
) -> str:
    if explicit_outcome in ALLOWED_METRICS_COMPLETION_OUTCOMES:
        return explicit_outcome
    if attempt_status in {
        "blocked_before_submission",
        "blocked_remote_checkout_dirty",
        "no_slurm_job_submitted",
        "incomplete_no_submission",
    }:
        return "incomplete"
    if report_status == "complete" and metrics_contract_status == "complete":
        if metrics_completion_source == "new_metrics_completion_rerun":
            return "measured"
        if metrics_completion_source == "recovered_existing_run_root":
            return "recovered"
    if report_status in {"blocked_missing_run_root", "blocked_missing_inputs"}:
        return "blocked"
    return "blocked"


def _sorted_metrics_by_status(group_statuses: dict[str, Any], status: str) -> list[str]:
    metrics: list[str] = []
    for metric_name in sorted(group_statuses):
        entry = group_statuses.get(metric_name)
        if not isinstance(entry, dict):
            continue
        if entry.get("status") == status:
            metrics.append(metric_name)
    return metrics


def _classification(metric_statuses: dict[str, Any], metrics_remediation: dict[str, Any]) -> dict[str, Any]:
    mandatory_statuses = metric_statuses.get("mandatory", {}) if isinstance(metric_statuses, dict) else {}
    ancillary_statuses = metric_statuses.get("ancillary", {}) if isinstance(metric_statuses, dict) else {}
    measured_metrics = _safe_list(metric_statuses.get("measured")) if isinstance(metric_statuses, dict) else []
    unavailable_metrics = _safe_list(metric_statuses.get("unavailable")) if isinstance(metric_statuses, dict) else []
    blocked_metrics = _safe_list(metric_statuses.get("blocked")) if isinstance(metric_statuses, dict) else []
    missing_mandatory_metrics = _safe_list(metrics_remediation.get("missing_mandatory_metrics"))
    unavailable_ancillary_metrics = _safe_list(metrics_remediation.get("unavailable_ancillary_metrics"))
    next_run_required_metrics = _safe_list(metrics_remediation.get("next_run_required_metrics"))
    return {
        "mandatory": {
            "measured": _sorted_metrics_by_status(mandatory_statuses, "measured"),
            "blocked": _sorted_metrics_by_status(mandatory_statuses, "blocked"),
        },
        "ancillary": {
            "measured": _sorted_metrics_by_status(ancillary_statuses, "measured"),
            "unavailable": _sorted_metrics_by_status(ancillary_statuses, "unavailable"),
        },
        "measured_metrics": measured_metrics,
        "blocked_metrics": blocked_metrics,
        "unavailable_metrics": unavailable_metrics,
        "missing_mandatory_metrics": missing_mandatory_metrics,
        "unavailable_ancillary_metrics": unavailable_ancillary_metrics,
        "next_run_required_metrics": next_run_required_metrics,
    }


def build_report(
    evidence: dict[str, Any] | None = None,
    *,
    run_root: Path | None = None,
) -> dict[str, Any]:
    if evidence is None:
        if run_root is None:
            return blocked_missing_run_root_report(Path("missing-run-root"))
        if not run_root.exists():
            return blocked_missing_run_root_report(run_root)
        evidence = probe_metrics.collect_run_metrics(run_root)

    report_status = "complete"
    if evidence.get("metrics_contract_status") == "blocked_missing_inputs":
        report_status = "blocked_missing_inputs"
    elif evidence.get("metrics_contract_status") != "complete":
        report_status = str(evidence.get("metrics_contract_status") or "unknown")

    metric_statuses = evidence.get("metric_statuses", {}) if isinstance(evidence, dict) else {}
    metrics_remediation = evidence.get("metrics_remediation", {}) if isinstance(evidence, dict) else {}
    classification = _classification(metric_statuses, metrics_remediation)
    source_paths = {
        "run_root": evidence.get("run_root"),
        "output_root": evidence.get("output_root"),
        "probe_manifest_path": evidence.get("probe_manifest_path"),
        "command_plan_path": evidence.get("command_plan_path"),
        "hazard_manifest_path": evidence.get("hazard_manifest_path"),
    }
    metrics_completion_source = classify_metrics_completion_source(
        report_status=report_status,
        metrics_contract_status=str(evidence.get("metrics_contract_status") or "unknown"),
        source_paths=source_paths,
        explicit_source=str(evidence.get("metrics_completion_source"))
        if isinstance(evidence.get("metrics_completion_source"), str)
        else None,
    )
    metrics_completion_outcome = classify_metrics_completion_outcome(
        report_status=report_status,
        metrics_contract_status=str(evidence.get("metrics_contract_status") or "unknown"),
        metrics_completion_source=metrics_completion_source,
        explicit_outcome=str(evidence.get("metrics_completion_outcome"))
        if isinstance(evidence.get("metrics_completion_outcome"), str)
        else None,
        attempt_status=str(evidence.get("metrics_completion_attempt_status"))
        if isinstance(evidence.get("metrics_completion_attempt_status"), str)
        else None,
    )
    evidence_with_source = dict(evidence)
    evidence_with_source["metrics_completion_source"] = metrics_completion_source
    evidence_with_source["metrics_completion_outcome"] = metrics_completion_outcome
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": report_status,
        "run_root_status": "measured_run_root" if run_root is None or run_root.exists() else "missing_run_root",
        "run_root": str(run_root) if run_root is not None else evidence.get("run_root"),
        "metrics_completion_source": metrics_completion_source,
        "metrics_completion_outcome": metrics_completion_outcome,
        "metrics_completion_attempt_status": evidence.get("metrics_completion_attempt_status"),
        "metrics_contract_status": evidence.get("metrics_contract_status"),
        "metrics_contract_missing_metrics": _safe_list(evidence.get("metrics_contract_missing_metrics")),
        "metrics_contract_ancillary_unavailable_metrics": _safe_list(
            evidence.get("metrics_contract_ancillary_unavailable_metrics")
        ),
        "metric_statuses": metric_statuses,
        "metrics_remediation": metrics_remediation,
        "classification": classification,
        "source_paths": source_paths,
        "summary": summarize_report(report_status, classification, evidence_with_source),
    }
    return report


def blocked_missing_run_root_report(run_root: Path) -> dict[str, Any]:
    classification = {
        "mandatory": {"measured": [], "blocked": []},
        "ancillary": {"measured": [], "unavailable": []},
        "measured_metrics": [],
        "blocked_metrics": [],
        "unavailable_metrics": [],
        "missing_mandatory_metrics": [],
        "unavailable_ancillary_metrics": [],
        "next_run_required_metrics": [],
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": "blocked_missing_run_root",
        "run_root_status": "missing_run_root",
        "run_root": str(run_root),
        "metrics_completion_source": "blocked_missing_metrics",
        "metrics_completion_outcome": "blocked",
        "metrics_completion_attempt_status": None,
        "missing_run_root_reason": f"run root does not exist: {run_root}",
        "metrics_contract_status": "blocked_missing_run_root",
        "metrics_contract_missing_metrics": [],
        "metrics_contract_ancillary_unavailable_metrics": [],
        "metric_statuses": {},
        "metrics_remediation": {
            "schema_version": "balfrin_probe_metrics_remediation_v1",
            "status": "blocked_missing_run_root",
            "missing_mandatory_metrics": [],
            "unavailable_ancillary_metrics": [],
            "next_run_required_metrics": [],
            "next_run_collection_checklist": [],
        },
        "classification": classification,
        "source_paths": {
            "run_root": str(run_root),
            "output_root": None,
            "probe_manifest_path": None,
            "command_plan_path": None,
            "hazard_manifest_path": None,
        },
    }
    report["summary"] = summarize_report(report["report_status"], classification, report)
    return report


def summarize_report(
    report_status: str,
    classification: dict[str, Any],
    evidence: dict[str, Any],
) -> str:
    if report_status == "blocked_missing_run_root":
        return (
            "Balfrin metrics report is blocked because the run root is missing: "
            f"{evidence.get('run_root')} (metrics_completion_source: blocked_missing_metrics)"
        )

    mandatory_measured = classification.get("mandatory", {}).get("measured", [])
    mandatory_blocked = classification.get("mandatory", {}).get("blocked", [])
    ancillary_unavailable = classification.get("ancillary", {}).get("unavailable", [])
    next_run_required = classification.get("next_run_required_metrics", [])
    metrics_completion_source = evidence.get("metrics_completion_source", "unknown")
    return (
        "Balfrin metrics completeness report for the measured run root: "
        f"{len(mandatory_measured)} mandatory metrics measured, "
        f"{len(mandatory_blocked)} mandatory metrics blocked, "
        f"{len(ancillary_unavailable)} ancillary metrics unavailable, "
        f"{len(next_run_required)} next-run-required metrics, "
        f"metrics_completion_source={metrics_completion_source}, "
        f"metrics_completion_outcome={evidence.get('metrics_completion_outcome', 'unknown')}."
    )


def render_text_report(report: dict[str, Any]) -> str:
    classification = report.get("classification", {}) if isinstance(report, dict) else {}
    metric_statuses = report.get("metric_statuses", {}) if isinstance(report, dict) else {}
    mandatory_statuses = metric_statuses.get("mandatory", {}) if isinstance(metric_statuses, dict) else {}
    ancillary_statuses = metric_statuses.get("ancillary", {}) if isinstance(metric_statuses, dict) else {}

    lines = [
        "Balfrin Probe Metrics Report",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"report_status: {report.get('report_status', 'unknown')}",
        f"run_root_status: {report.get('run_root_status', 'unknown')}",
        f"run_root: {report.get('run_root', 'unknown')}",
        f"metrics_completion_source: {report.get('metrics_completion_source', 'unknown')}",
        f"metrics_completion_outcome: {report.get('metrics_completion_outcome', 'unknown')}",
        f"metrics_completion_attempt_status: {report.get('metrics_completion_attempt_status', 'unknown')}",
        f"metrics_contract_status: {report.get('metrics_contract_status', 'unknown')}",
        f"metrics_contract_missing_metrics: {report.get('metrics_contract_missing_metrics', [])}",
        f"metrics_contract_ancillary_unavailable_metrics: {report.get('metrics_contract_ancillary_unavailable_metrics', [])}",
        f"summary: {report.get('summary', '')}",
    ]

    if classification:
        lines.append("classification:")
        lines.append(f"  mandatory_measured: {classification.get('mandatory', {}).get('measured', [])}")
        lines.append(f"  mandatory_blocked: {classification.get('mandatory', {}).get('blocked', [])}")
        lines.append(f"  ancillary_measured: {classification.get('ancillary', {}).get('measured', [])}")
        lines.append(f"  ancillary_unavailable: {classification.get('ancillary', {}).get('unavailable', [])}")
        lines.append(f"  measured_metrics: {classification.get('measured_metrics', [])}")
        lines.append(f"  blocked_metrics: {classification.get('blocked_metrics', [])}")
        lines.append(f"  unavailable_metrics: {classification.get('unavailable_metrics', [])}")
        lines.append(f"  missing_mandatory_metrics: {classification.get('missing_mandatory_metrics', [])}")
        lines.append(
            f"  unavailable_ancillary_metrics: {classification.get('unavailable_ancillary_metrics', [])}"
        )
        lines.append(f"  next_run_required_metrics: {classification.get('next_run_required_metrics', [])}")

    if mandatory_statuses:
        lines.append("mandatory_metric_statuses:")
        for key in sorted(mandatory_statuses):
            entry = mandatory_statuses[key]
            reason = f" ({entry.get('reason')})" if entry.get("reason") else ""
            lines.append(f"  - {key}: {entry.get('status', 'unknown')}{reason}")

    if ancillary_statuses:
        lines.append("ancillary_metric_statuses:")
        for key in sorted(ancillary_statuses):
            entry = ancillary_statuses[key]
            reason = f" ({entry.get('reason')})" if entry.get("reason") else ""
            lines.append(f"  - {key}: {entry.get('status', 'unknown')}{reason}")

    remediation = report.get("metrics_remediation", {}) if isinstance(report, dict) else {}
    if remediation:
        lines.append("metrics_remediation:")
        lines.append(f"  status: {remediation.get('status', 'unknown')}")
        lines.append(f"  missing_mandatory_metrics: {remediation.get('missing_mandatory_metrics', [])}")
        lines.append(
            f"  unavailable_ancillary_metrics: {remediation.get('unavailable_ancillary_metrics', [])}"
        )
        lines.append(f"  next_run_required_metrics: {remediation.get('next_run_required_metrics', [])}")

    source_paths = report.get("source_paths", {}) if isinstance(report, dict) else {}
    if source_paths:
        lines.append("source_paths:")
        for key in ("run_root", "output_root", "probe_manifest_path", "command_plan_path", "hazard_manifest_path"):
            if key in source_paths:
                lines.append(f"  {key}: {source_paths.get(key)}")

    missing_reason = report.get("missing_run_root_reason")
    if missing_reason:
        lines.append(f"missing_run_root_reason: {missing_reason}")

    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        json_output = json_output or artifact_dir / f"{REPORT_BASENAME}.json"
        text_output = text_output or artifact_dir / f"{REPORT_BASENAME}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.evidence_json is not None:
            evidence = _load_json(args.evidence_json)
            if evidence is None:
                raise ValueError(f"evidence JSON is missing or invalid: {args.evidence_json}")
            report = build_report(evidence, run_root=args.run_root)
        else:
            report = build_report(None, run_root=args.run_root)
    except (OSError, ValueError) as exc:
        print(f"balfrin metrics report error: {exc}", file=sys.stderr)
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
    return 0 if report["report_status"] != "blocked_missing_run_root" else 2


if __name__ == "__main__":
    raise SystemExit(main())
