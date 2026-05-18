#!/usr/bin/env python3
"""Rehearse Balfrin post-run evidence collection on fixture roots.

This helper is intentionally read-only and fixture-oriented. It exercises the
same metrics and preservation gates that a future post-run collector would use,
while preserving access-blocked, missing-root, incomplete-root, and
fixture-backed provenance so rehearsals cannot be promoted to measured evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import check_balfrin_remote_access_preflight as access_preflight  # noqa: E402
from scripts import summarize_balfrin_demonstration_closure_package as closure_package  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as metrics_report  # noqa: E402
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_post_run_evidence_collector_rehearsal_v1"
SOURCE_FAMILIES = tuple(sorted(closure_package.ALLOWED_MEASURED_EVIDENCE_SOURCES))
STATUS_NON_GIT_ARTIFACT_UNAVAILABLE = "blocked_non_git_artifact_unavailable"

FIXTURE_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract"
DEFAULT_COMPLETE_RUN_ROOT = FIXTURE_ROOT / "complete_run_root"
DEFAULT_INCOMPLETE_RUN_ROOT = FIXTURE_ROOT / "incomplete_run_root"
DEFAULT_MISSING_RUN_ROOT = FIXTURE_ROOT / "missing_run_root"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=None)
    parser.add_argument("--source-family", choices=SOURCE_FAMILIES, default="metrics_completion_rerun")
    parser.add_argument("--balfrin-access-json", type=Path, default=None)
    parser.add_argument(
        "--non-git-artifact-status",
        choices=("available", "unavailable"),
        default="available",
        help="Fixture switch for mounted/non-git Balfrin run artifacts.",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Emit the standard complete/incomplete/missing/access/artifact fixture matrix for both source families.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _ready_access_report() -> dict[str, Any]:
    return {
        "schema_version": access_preflight.SCHEMA_VERSION,
        "status": access_preflight.STATUS_READY,
        "ready_for_read_only_collection": True,
        "read_only": True,
        "live_submission_authorized": False,
        "checked_commands": [
            {"name": "ssh_availability", "status": "pass", "returncode": 0},
            {"name": "remote_clone", "status": "pass", "returncode": 0},
            {"name": "run_root_visibility", "status": "pass", "returncode": 0},
            {"name": "scheduler_query", "status": "pass", "returncode": 0},
        ],
        "source": "fixture_ready_access",
    }


def _blocked_ssh_access_report() -> dict[str, Any]:
    return {
        "schema_version": access_preflight.SCHEMA_VERSION,
        "status": access_preflight.STATUS_BLOCKED_SSH,
        "ready_for_read_only_collection": False,
        "read_only": True,
        "live_submission_authorized": False,
        "checked_commands": [{"name": "ssh_availability", "status": "fail", "returncode": 255}],
        "source": "fixture_blocked_ssh_access",
    }


def _is_fixture_path(path: Path) -> bool:
    parts = path.resolve().parts
    return "tests" in parts and "fixtures" in parts


def _missing_fields(
    metrics: dict[str, Any] | None,
    preservation: dict[str, Any] | None,
) -> dict[str, list[str]]:
    metrics_missing = []
    if isinstance(metrics, dict):
        metrics_missing = [
            *[str(item) for item in metrics.get("metrics_contract_missing_metrics", [])],
            *[str(item) for item in metrics.get("metrics_contract_ancillary_unavailable_metrics", [])],
        ]

    missing_run_root_entries = []
    missing_output_families = []
    if isinstance(preservation, dict):
        missing_run_root_entries = [str(item) for item in preservation.get("missing_run_root_entries", [])]
        families = preservation.get("output_family_summaries", {}).get("missing_required_families", {})
        missing_output_families = [str(item) for item in families]

    return {
        "metrics": sorted(set(metrics_missing)),
        "run_root_entries": sorted(set(missing_run_root_entries)),
        "output_families": sorted(set(missing_output_families)),
    }


def _source_authorization_status(source_family: str, collector_status: str) -> str:
    if collector_status != "fixture_backed_complete":
        return collector_status
    if source_family == "authorized_multi_zone_probe":
        return "authorized_for_one_bounded_probe"
    return "authorized"


def _collector_status(
    *,
    run_root: Path,
    metrics: dict[str, Any],
    preservation: dict[str, Any],
) -> str:
    if metrics.get("report_status") == "blocked_missing_run_root":
        return "blocked_missing_run_root"
    if preservation.get("gate_status") == "blocked_missing_run_root":
        return "blocked_missing_run_root"
    if preservation.get("gate_status") == "ready_for_demonstration_evidence":
        return "fixture_backed_complete" if _is_fixture_path(run_root) else "measured_complete"
    return "blocked_incomplete_run_root"


def _new_evidence_input(
    *,
    source_family: str,
    collector_status: str,
    run_root: Path | None,
    preservation_status: str,
    missing_fields: dict[str, list[str]],
) -> dict[str, Any]:
    complete = collector_status in {"fixture_backed_complete", "measured_complete"}
    evidence_type = "fixture_backed" if collector_status == "fixture_backed_complete" else "measured" if complete else "blocked"
    status = "measured" if collector_status == "measured_complete" else collector_status
    missing = [
        f"metrics:{field}" for field in missing_fields.get("metrics", [])
    ] + [
        f"run_root_entries:{field}" for field in missing_fields.get("run_root_entries", [])
    ] + [
        f"output_families:{field}" for field in missing_fields.get("output_families", [])
    ]
    return {
        "status": status,
        "evidence_type": evidence_type,
        "source_type": source_family,
        "preservation_checked": preservation_status == "ready_for_demonstration_evidence",
        "preservation_gate_status": preservation_status,
        "authorization_status": _source_authorization_status(source_family, collector_status),
        "run_root": str(run_root) if run_root is not None else None,
        "missing_fields": sorted(set(missing)),
        "summary": (
            "Fixture-backed collector rehearsal only; do not promote to measured evidence."
            if evidence_type == "fixture_backed"
            else "Collector rehearsal is blocked before measured evidence compatibility."
            if evidence_type == "blocked"
            else "Measured post-run evidence input is preservation checked."
        ),
        "source_paths": [str(run_root)] if run_root is not None else [],
    }


def _closure_package_agreement(
    *,
    evidence_input: dict[str, Any],
    compatibility: dict[str, Any],
) -> dict[str, Any]:
    evidence_type = str(evidence_input.get("evidence_type") or "blocked")
    compatibility_status = str(compatibility.get("status") or "blocked_missing_inputs")
    promoted = compatibility_status == "compatible" and evidence_type == "measured"
    return {
        "schema_version": "balfrin_post_run_closure_package_agreement_v1",
        "status": "compatible" if promoted else "agrees_blocked",
        "closure_package_helper": "scripts/summarize_balfrin_demonstration_closure_package.py",
        "new_measured_evidence_source_type": evidence_input.get("source_type"),
        "collector_evidence_type": evidence_type,
        "collector_missing_fields": list(evidence_input.get("missing_fields", [])),
        "closure_input_compatibility_status": compatibility_status,
        "closure_missing_fields": list(compatibility.get("missing_fields", [])),
        "measured_result_promoted": promoted,
        "preserves_fixture_backed_boundary": bool(compatibility.get("preserves_fixture_backed_boundary")),
    }


def _blocked_report(
    *,
    source_family: str,
    run_root: Path | None,
    collector_status: str,
    access_report: dict[str, Any],
    non_git_artifact_status: str,
    reason: str,
) -> dict[str, Any]:
    missing = {"metrics": [], "run_root_entries": [], "output_families": []}
    evidence_input = _new_evidence_input(
        source_family=source_family,
        collector_status=collector_status,
        run_root=run_root,
        preservation_status=collector_status,
        missing_fields=missing,
    )
    compatibility = closure_package.evaluate_new_measured_evidence_compatibility(evidence_input)
    closure_agreement = _closure_package_agreement(
        evidence_input=evidence_input,
        compatibility=compatibility,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "rehearsal_status": collector_status,
        "collector_status": collector_status,
        "source_family": source_family,
        "run_root": str(run_root) if run_root is not None else None,
        "run_root_status": collector_status,
        "balfrin_access_preflight_status": str(access_report.get("status") or "unknown"),
        "balfrin_access_preflight": access_report,
        "non_git_artifact_status": non_git_artifact_status,
        "metrics_report_status": collector_status,
        "preservation_gate_status": collector_status,
        "missing_fields": missing,
        "new_measured_evidence_input": evidence_input,
        "closure_input_compatibility": compatibility,
        "closure_package_agreement": closure_agreement,
        "measured_result_promoted": False,
        "claim_boundaries": _claim_boundaries(),
        "summary": reason,
    }


def build_report(
    *,
    run_root: Path,
    source_family: str,
    balfrin_access_preflight: dict[str, Any] | None = None,
    non_git_artifact_available: bool = True,
) -> dict[str, Any]:
    access_report = dict(balfrin_access_preflight or _ready_access_report())
    access_status = str(access_report.get("status") or "unknown")
    if access_status != access_preflight.STATUS_READY:
        return _blocked_report(
            source_family=source_family,
            run_root=run_root,
            collector_status=access_status,
            access_report=access_report,
            non_git_artifact_status="not_checked_due_to_access",
            reason=f"Balfrin read-only collection is blocked by access status: {access_status}",
        )

    if not non_git_artifact_available:
        return _blocked_report(
            source_family=source_family,
            run_root=run_root,
            collector_status=STATUS_NON_GIT_ARTIFACT_UNAVAILABLE,
            access_report=access_report,
            non_git_artifact_status=STATUS_NON_GIT_ARTIFACT_UNAVAILABLE,
            reason="Balfrin non-git run artifacts are unavailable for read-only collection.",
        )

    metrics = metrics_report.build_report(None, run_root=run_root)
    preservation = preservation_gate.build_report(run_root=run_root)
    collector_status = _collector_status(run_root=run_root, metrics=metrics, preservation=preservation)
    missing = _missing_fields(metrics, preservation)
    evidence_input = _new_evidence_input(
        source_family=source_family,
        collector_status=collector_status,
        run_root=run_root,
        preservation_status=str(preservation.get("gate_status") or collector_status),
        missing_fields=missing,
    )
    compatibility = closure_package.evaluate_new_measured_evidence_compatibility(evidence_input)
    closure_agreement = _closure_package_agreement(
        evidence_input=evidence_input,
        compatibility=compatibility,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "rehearsal_status": collector_status,
        "collector_status": collector_status,
        "source_family": source_family,
        "run_root": str(run_root),
        "run_root_status": str(metrics.get("run_root_status") or preservation.get("run_root_status") or collector_status),
        "balfrin_access_preflight_status": access_status,
        "balfrin_access_preflight": access_report,
        "non_git_artifact_status": "available",
        "metrics_report_status": str(metrics.get("report_status") or "unknown"),
        "preservation_gate_status": str(preservation.get("gate_status") or "unknown"),
        "metrics_report": metrics,
        "preservation_gate": preservation,
        "missing_fields": missing,
        "new_measured_evidence_input": evidence_input,
        "closure_input_compatibility": compatibility,
        "closure_package_agreement": closure_agreement,
        "measured_result_promoted": closure_agreement["measured_result_promoted"],
        "claim_boundaries": _claim_boundaries(),
        "summary": summarize_report(collector_status, source_family, compatibility),
    }


def build_rehearsal_matrix(
    *,
    access_preflight_ready: dict[str, Any] | None = None,
    access_preflight_blocked: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ready_access = access_preflight_ready or _ready_access_report()
    blocked_access = access_preflight_blocked or _blocked_ssh_access_report()
    cases: list[dict[str, Any]] = []
    for source_family in SOURCE_FAMILIES:
        case_specs = [
            ("complete", DEFAULT_COMPLETE_RUN_ROOT, ready_access, True),
            ("incomplete", DEFAULT_INCOMPLETE_RUN_ROOT, ready_access, True),
            ("missing_root", DEFAULT_MISSING_RUN_ROOT, ready_access, True),
            ("ssh_unavailable", DEFAULT_COMPLETE_RUN_ROOT, blocked_access, True),
            ("non_git_artifact_unavailable", DEFAULT_COMPLETE_RUN_ROOT, ready_access, False),
        ]
        for case_id, run_root, access_report, artifacts_available in case_specs:
            case_report = build_report(
                run_root=run_root,
                source_family=source_family,
                balfrin_access_preflight=access_report,
                non_git_artifact_available=artifacts_available,
            )
            cases.append({"case_id": f"{source_family}:{case_id}", **case_report})

    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_status": "fixture_backed_rehearsal",
        "case_count": len(cases),
        "cases": cases,
        "classification_counts": _classification_counts(cases),
        "measured_result_promoted": any(case.get("measured_result_promoted") for case in cases),
        "claim_boundaries": _claim_boundaries(),
        "summary": (
            "Fixture-backed rehearsal covered complete, incomplete, missing-root, SSH-unavailable, "
            "and non-git-artifact-unavailable classifications for both next live-run source families."
        ),
    }


def _classification_counts(cases: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in cases:
        status = str(case.get("collector_status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _claim_boundaries() -> dict[str, bool]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "fixture_backed_rehearsal_only": True,
    }


def summarize_report(
    collector_status: str,
    source_family: str,
    compatibility: dict[str, Any],
) -> str:
    return (
        f"{source_family} post-run collector rehearsal classified {collector_status}; "
        f"closure input compatibility is {compatibility.get('status')}. "
        "Fixture-backed rehearsal results are not measured evidence."
    )


def render_text_report(report: dict[str, Any]) -> str:
    if "cases" in report:
        lines = [
            "Balfrin Post-Run Evidence Collector Rehearsal Matrix",
            f"schema_version: {report.get('schema_version', 'unknown')}",
            f"matrix_status: {report.get('matrix_status', 'unknown')}",
            f"case_count: {report.get('case_count', 0)}",
            f"measured_result_promoted: {report.get('measured_result_promoted', False)}",
            f"classification_counts: {report.get('classification_counts', {})}",
        ]
        for case in report.get("cases", []):
            lines.append(
                f"- {case.get('case_id')}: collector_status={case.get('collector_status')} "
                f"closure_input_compatibility={case.get('closure_input_compatibility', {}).get('status')}"
            )
        return "\n".join(lines)

    compatibility = report.get("closure_input_compatibility", {})
    closure_agreement = report.get("closure_package_agreement", {})
    lines = [
        "Balfrin Post-Run Evidence Collector Rehearsal",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"source_family: {report.get('source_family', 'unknown')}",
        f"collector_status: {report.get('collector_status', 'unknown')}",
        f"run_root_status: {report.get('run_root_status', 'unknown')}",
        f"balfrin_access_preflight_status: {report.get('balfrin_access_preflight_status', 'unknown')}",
        f"non_git_artifact_status: {report.get('non_git_artifact_status', 'unknown')}",
        f"metrics_report_status: {report.get('metrics_report_status', 'unknown')}",
        f"preservation_gate_status: {report.get('preservation_gate_status', 'unknown')}",
        f"closure_input_compatibility: {compatibility.get('status', 'unknown')}",
        f"closure_package_agreement: {closure_agreement.get('status', 'unknown')}",
        f"closure_missing_fields: {compatibility.get('missing_fields', [])}",
        f"measured_result_promoted: {report.get('measured_result_promoted', False)}",
        f"summary: {report.get('summary', '')}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    access_report = _load_json(args.balfrin_access_json) if args.balfrin_access_json is not None else None
    if args.matrix or args.run_root is None:
        report = build_rehearsal_matrix(access_preflight_ready=access_report)
    else:
        report = build_report(
            run_root=args.run_root,
            source_family=args.source_family,
            balfrin_access_preflight=access_report,
            non_git_artifact_available=args.non_git_artifact_status == "available",
        )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if not str(report.get("collector_status") or report.get("matrix_status") or "").startswith("blocked") else 2


if __name__ == "__main__":
    raise SystemExit(main())
