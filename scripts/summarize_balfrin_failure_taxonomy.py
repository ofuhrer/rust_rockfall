#!/usr/bin/env python3
"""Summarize the Balfrin operational failure taxonomy.

This helper is read-only. It normalizes the Balfrin failure classes used by the
runbook and post-run bundle so operators can separate infrastructure and
orchestration problems from scientific interpretation boundaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_failure_taxonomy_v1"
DEFAULT_RUN_ID = "tschamut_public_balfrin_single_release_zone_v1"
DEFAULT_PILOT_ID = "tschamut_public_pilot"


class BalfrinFailureTaxonomyError(ValueError):
    """User-facing taxonomy error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional override JSON file for tests or alternate evidence snapshots.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinFailureTaxonomyError as exc:
        print(f"balfrin failure taxonomy error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinFailureTaxonomyError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinFailureTaxonomyError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence_override = evidence_override or {}
    classes = build_failure_classes(evidence_override)
    status_counts = count_statuses(classes)
    observed_classes = [failure_class for failure_class in classes if failure_class["current_status"] == "observed"]
    scope_limited_classes = [failure_class for failure_class in classes if failure_class["current_status"] == "scope_limited"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": str(evidence_override.get("pilot_id") or DEFAULT_PILOT_ID),
        "run_id": str(evidence_override.get("run_id") or DEFAULT_RUN_ID),
        "taxonomy_status": derive_taxonomy_status(classes, evidence_override),
        "status_counts": status_counts,
        "observed_failure_classes": observed_classes,
        "scope_limited_failure_classes": scope_limited_classes,
        "failure_classes": classes,
        "claim_boundaries": claim_boundaries(),
        "evidence_sources": evidence_sources(),
        "source_paths": source_paths(evidence_override),
    }
    return report


def build_failure_classes(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    readiness = as_mapping(section_for(evidence, "readiness_check", "readiness_report", "readiness"))
    submission = as_mapping(section_for(evidence, "submission_report", "scheduler_report", "scheduler_check"))
    runtime = as_mapping(section_for(evidence, "runtime_report", "runtime_check", "run_state"))
    probe_metrics = as_mapping(evidence.get("probe_metrics"))
    post_run = as_mapping(evidence.get("post_run_report"))
    gis_report = as_mapping(evidence.get("gis_report"))
    single_job_summary = as_mapping(evidence.get("single_job_summary"))

    classes = [
        {
            "class_id": "readiness_blocked",
            "domain": "readiness",
            "current_status": classify_readiness(readiness),
            "evidence_status": str(readiness.get("status") or "").strip() or "missing",
            "signals": [
                "readiness helper returns blocked_for_balfrin_readiness",
                "blocking_checks or blocking_checks-like fields are non-empty",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py "
                '"$RUN_MANIFEST" --format json'
            ),
            "recovery_action": (
                "repair the reported readiness blocker, then rerun the readiness helper "
                "with the same RUN_MANIFEST and run identifiers"
            ),
            "escalation_boundary": (
                "do not submit, collect, or infer scientific no-go from an infrastructure blocker"
            ),
            "source_helper": "scripts/check_balfrin_tschamut_readiness.py",
            "escalate_to": "environment or data owner",
        },
        {
            "class_id": "scheduler_submission_failed",
            "domain": "scheduler",
            "current_status": classify_scheduler(submission),
            "evidence_status": str(submission.get("status") or submission.get("submission_status") or "").strip() or "missing",
            "signals": [
                "submission helper exits non-zero or does not emit submitted_job_id",
                "submission package or sbatch handoff cannot be regenerated cleanly",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py "
                '"$RUN_MANIFEST" --run-root "$RUN_ROOT" --run-id "$RUN_ID" --generate-only'
            ),
            "recovery_action": (
                "regenerate the same submission package and retry submit with the same run root and run id"
            ),
            "escalation_boundary": (
                "scheduler failures are operational; they should not be reclassified as scientific outcomes"
            ),
            "source_helper": "scripts/submit_balfrin_probe.py",
            "escalate_to": "scheduler or operator support",
        },
        {
            "class_id": "runtime_failure",
            "domain": "runtime",
            "current_status": classify_runtime(runtime, probe_metrics, single_job_summary),
            "evidence_status": str(
                runtime.get("status")
                or probe_metrics.get("status")
                or single_job_summary.get("status")
                or ""
            ).strip() or "missing",
            "signals": [
                "the submitted job fails before metrics collection can complete",
                "run root logs show an execution failure before stable outputs appear",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root \"$RUN_ROOT\""
            ),
            "recovery_action": (
                "preserve the run root, inspect logs, and replay the same submit command only after the job is cleared"
            ),
            "escalation_boundary": (
                "runtime failure is an execution problem; do not treat it as a scientific interpretation result"
            ),
            "source_helper": "scripts/submit_balfrin_probe.py",
            "escalate_to": "operator on the same run root",
        },
        {
            "class_id": "partial_output_incomplete",
            "domain": "partial_output",
            "current_status": classify_partial_output(probe_metrics, single_job_summary),
            "evidence_status": str(probe_metrics.get("metrics_contract_status") or single_job_summary.get("status") or "").strip() or "missing",
            "signals": [
                "validation_output or hazard_output fields are missing from the collector summary",
                "the metrics contract reports blocked_missing_inputs for output-family fields",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root \"$RUN_ROOT\""
            ),
            "recovery_action": (
                "keep the partial tree, rerun collection on the same run root, and only replay execution if the job cannot recover"
            ),
            "escalation_boundary": (
                "partial output should be handled as an operational recovery case, not a scientific no-go"
            ),
            "source_helper": "scripts/collect_balfrin_probe_metrics.py",
            "escalate_to": "collector or run-root owner",
        },
        {
            "class_id": "metrics_blocked",
            "domain": "metrics",
            "current_status": classify_metrics(probe_metrics),
            "evidence_status": str(
                probe_metrics.get("metrics_contract_status")
                or probe_metrics.get("status")
                or ""
            ).strip() or "missing",
            "signals": [
                "metrics contract missing fields outside the output families",
                "log audit records error-like lines in the run root",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root \"$RUN_ROOT\" --output-json /tmp/balfrin_probe_metrics.json"
            ),
            "recovery_action": (
                "rerun the collector on the same run root, then inspect the missing metrics and logs before replaying execution"
            ),
            "escalation_boundary": (
                "metrics collection failures stay in the diagnostics layer and do not change interpretation criteria"
            ),
            "source_helper": "scripts/collect_balfrin_probe_metrics.py",
            "escalate_to": "metrics or log-audit reviewer",
        },
        {
            "class_id": "gis_export_blocked",
            "domain": "gis_export",
            "current_status": classify_gis_export(gis_report),
            "evidence_status": str(gis_report.get("gis_cog_readiness_status") or gis_report.get("status") or "").strip() or "missing",
            "signals": [
                "GIS readiness is blocked missing inputs or metadata-only",
                "COG or review-package readiness remains blocked by raster layout or manifest fields",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json"
            ),
            "recovery_action": (
                "repair the missing package or raster fields, then rerun the GIS/COG audit on the same artifact roots"
            ),
            "escalation_boundary": (
                "GIS/export scope limits do not authorize operational hazard claims"
            ),
            "source_helper": "scripts/audit_gis_cog_package_readiness.py",
            "escalate_to": "GIS reviewer or artifact owner",
        },
        {
            "class_id": "scientific_state_failure",
            "domain": "scientific_state",
            "current_status": classify_scientific_state(post_run),
            "evidence_status": str(post_run.get("interpretation_status") or post_run.get("status") or "").strip() or "missing",
            "signals": [
                "post-run interpretation gate is blocked_missing_inputs",
                "post-run interpretation gate is inconclusive_conditional_diagnostic",
            ],
            "command": (
                "PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py "
                "--format json --evidence-json \"$RUN_ROOT/balfrin_post_run_evidence.json\""
            ),
            "recovery_action": (
                "rebuild the evidence bundle and rerun the interpretation gate on the same evidence JSON"
            ),
            "escalation_boundary": (
                "scientific-state scope limits must not change the gate's claim boundaries"
            ),
            "source_helper": "scripts/summarize_balfrin_post_run_interpretation_gate.py",
            "escalate_to": "post-run evidence reviewer",
        },
    ]
    return classes


def classify_readiness(readiness: dict[str, Any]) -> str:
    status = str(readiness.get("status") or "").strip()
    blockers = listify(readiness.get("blocking_checks") or readiness.get("blockers"))
    if status in {"blocked_for_balfrin_readiness", "blocked_missing_inputs"} or blockers:
        return "observed"
    if status in {"ready_for_balfrin_target_gate", "ready"}:
        return "clear"
    if status:
        return "scope_limited"
    return "not_observed"


def classify_scheduler(submission: dict[str, Any]) -> str:
    status = str(submission.get("status") or submission.get("submission_status") or "").strip()
    submitted_job_id = str(submission.get("submitted_job_id") or submission.get("job_id") or "").strip()
    if status in {"failed", "blocked_missing_inputs", "error"}:
        return "observed"
    if submitted_job_id:
        return "clear"
    if status:
        return "scope_limited"
    return "not_observed"


def classify_runtime(runtime: dict[str, Any], probe_metrics: dict[str, Any], single_job_summary: dict[str, Any]) -> str:
    status = str(runtime.get("status") or "").strip()
    if status in {"failed", "blocked_missing_inputs", "error"}:
        return "observed"
    if status in {"complete", "ready"}:
        return "clear"
    log_audit = as_mapping(probe_metrics.get("log_audit"))
    if log_audit.get("error_like_line_count", 0):
        return "observed"
    if single_job_summary.get("status") in {"blocked_missing_inputs", "failed"}:
        return "observed"
    if status:
        return "scope_limited"
    return "not_observed"


def classify_partial_output(probe_metrics: dict[str, Any], single_job_summary: dict[str, Any]) -> str:
    metrics_status = str(probe_metrics.get("metrics_contract_status") or probe_metrics.get("status") or "").strip()
    missing_metrics = listify(probe_metrics.get("metrics_contract_missing_metrics"))
    output_family_missing = any(
        item.startswith("validation_output.")
        or item.startswith("hazard_output.")
        or item in {"reduced_output_family_counts", "conditional_curve_row_count"}
        for item in missing_metrics
    )
    if metrics_status in {"blocked_missing_inputs", "failed"} and output_family_missing:
        return "observed"
    if metrics_status == "complete" and not output_family_missing:
        return "clear"
    if single_job_summary.get("validation_output_blocker_status") == "blocker_retained":
        return "scope_limited"
    if metrics_status:
        return "scope_limited"
    return "not_observed"


def classify_metrics(probe_metrics: dict[str, Any]) -> str:
    missing_metrics = listify(probe_metrics.get("metrics_contract_missing_metrics"))
    log_audit = as_mapping(probe_metrics.get("log_audit"))
    if log_audit.get("error_like_line_count", 0):
        return "observed"
    if any(
        item in {"wall_time_seconds", "memory_peak_mb"} or item.startswith("restartability_metadata.")
        for item in missing_metrics
    ):
        return "observed"
    if probe_metrics.get("metrics_contract_status") == "complete" and not missing_metrics:
        return "clear"
    if probe_metrics.get("metrics_contract_status"):
        return "scope_limited"
    return "not_observed"


def classify_gis_export(gis_report: dict[str, Any]) -> str:
    status = str(gis_report.get("gis_cog_readiness_status") or gis_report.get("status") or "").strip()
    if status in {"blocked_missing_inputs"}:
        return "observed"
    if status in {"metadata_only", "gis_package_ready_cog_blocked"}:
        return "scope_limited"
    if status in {"gis_package_ready", "cog_package_ready"}:
        return "clear"
    if status:
        return "scope_limited"
    return "not_observed"


def classify_scientific_state(post_run: dict[str, Any]) -> str:
    status = str(post_run.get("interpretation_status") or post_run.get("status") or "").strip()
    if status == "blocked_missing_inputs":
        return "observed"
    if status == "inconclusive_conditional_diagnostic":
        return "scope_limited"
    if status == "measured_conditional_diagnostic":
        return "clear"
    if status:
        return "scope_limited"
    return "not_observed"


def derive_taxonomy_status(classes: list[dict[str, Any]], evidence: dict[str, Any]) -> str:
    if not evidence:
        return "catalog_only"
    if any(entry["current_status"] == "observed" for entry in classes):
        return "observed_with_boundaries"
    if any(entry["current_status"] in {"scope_limited", "not_observed"} for entry in classes):
        return "scope_limited"
    if all(entry["current_status"] == "clear" for entry in classes):
        return "clear"
    return "catalog_only"


def count_statuses(classes: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"observed": 0, "scope_limited": 0, "clear": 0, "not_observed": 0}
    for entry in classes:
        status = str(entry.get("current_status") or "not_observed")
        counts[status] = counts.get(status, 0) + 1
    return counts


def source_paths(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_report_path": evidence.get("readiness_report_path"),
        "submission_report_path": evidence.get("submission_report_path"),
        "probe_metrics_path": evidence.get("probe_metrics_path"),
        "post_run_report_path": evidence.get("post_run_report_path"),
        "gis_report_path": evidence.get("gis_report_path"),
    }


def section_for(evidence: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = evidence.get(key)
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            return {"status": value}
    return {}


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def claim_boundaries() -> dict[str, Any]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "notes": [
            "failure taxonomy separates operational recovery from scientific interpretation",
            "scope-limited states are not operational hazard conclusions",
            "the taxonomy does not change claim boundaries or interpretation criteria",
        ],
    }


def evidence_sources() -> list[str]:
    return [
        "scripts/check_balfrin_tschamut_readiness.py",
        "scripts/submit_balfrin_probe.py",
        "scripts/collect_balfrin_probe_metrics.py",
        "scripts/audit_gis_cog_package_readiness.py",
        "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        "docs/balfrin_tschamut_pilot_runbook.md",
        "docs/balfrin_failure_recovery_playbook.md",
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Failure Taxonomy",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Taxonomy status: `{report['taxonomy_status']}`",
        f"- Pilot id: `{report['pilot_id']}`",
        f"- Run id: `{report['run_id']}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in report["status_counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Failure Classes", ""])
    for failure_class in report["failure_classes"]:
        lines.extend(
            [
                f"- {failure_class['class_id']} ({failure_class['domain']}): `{failure_class['current_status']}`",
                f"  - evidence status: `{failure_class['evidence_status']}`",
                f"  - signals: {', '.join(failure_class['signals'])}",
                f"  - command: {failure_class['command']}",
                f"  - recovery action: {failure_class['recovery_action']}",
                f"  - escalation boundary: {failure_class['escalation_boundary']}",
            ]
        )
    lines.extend(["", "## Claim Boundaries", ""])
    for key, value in report["claim_boundaries"].items():
        if key == "notes":
            continue
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("Notes:")
    for note in report["claim_boundaries"].get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
