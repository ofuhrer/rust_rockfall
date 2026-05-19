#!/usr/bin/env python3
"""Summarize the canonical Balfrin evidence bundle.

This helper is read-only. It assembles the measured Balfrin readiness,
metrics, outputs, restartability, GIS / COG status, and post-run
interpretation checks into one auditable JSON or text bundle. It preserves
claim boundaries explicitly and reports measured, fixture-backed, and blocked
sections rather than guessing when required evidence is absent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gis_cog_package_readiness as gis_cog
from scripts import summarize_balfrin_failure_taxonomy as failure_taxonomy
from scripts import summarize_balfrin_probe_metrics_report as metrics_report
from scripts import summarize_balfrin_post_run_interpretation_gate as post_run_gate
from scripts import summarize_balfrin_single_job_execution as single_job


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_evidence_bundle_v1"
GIS_COG_PARITY_SCHEMA_VERSION = "balfrin_gis_cog_parity_report_v1"
GIS_COG_SCOPE_SCHEMA_VERSION = "balfrin_gis_cog_scope_report_v1"
CANONICAL_BUNDLE_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"
DEFAULT_PILOT_ID = "tschamut_public_pilot"
DEFAULT_RUN_ID = "tschamut_public_balfrin_single_release_zone_v1"
FIXTURE_PATH_MARKERS = (("tests", "fixtures"),)
TB267_MULTI_ZONE_BLOCKED_EVIDENCE = {
    "status": "blocked_incomplete",
    "evidence_type": "blocked",
    "root_class": "blocked_pre_authorization",
    "preflight_status": "blocked_reducer_budget",
    "authorization_record_status": "missing",
    "first_bottleneck_label": "manifest_size_bytes",
    "slurm_job_id": None,
    "metrics_json_promoted": False,
    "preservation_gate_promoted": False,
    "post_run_collector_promoted": False,
    "release_zone_count": 2,
    "source_paths": ["docs/agent_work_log.md"],
    "summary": (
        "TB-267 stopped before live submission: Balfrin read-only access passed, but the smallest "
        "multi-zone authorization preflight failed closed at reducer budget first bottleneck "
        "manifest_size_bytes and the authorization record was missing."
    ),
}
ALLOWED_METRICS_COMPLETION_SOURCES = {
    "recovered_existing_run_root",
    "new_metrics_completion_rerun",
    "blocked_missing_metrics",
}
METRICS_COMPLETION_RERUN_MARKERS = (
    "metrics_completion",
    "metrics-completion",
    "metrics_completion_v1",
    "metrics_completion_rerun",
)


class BalfrinEvidenceBundleError(ValueError):
    """User-facing evidence-bundle error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="optional directory for the canonical JSON and text bundle",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinEvidenceBundleError as exc:
        print(f"balfrin evidence bundle error: {exc}", file=sys.stderr)
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
    return 0 if report["bundle_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinEvidenceBundleError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinEvidenceBundleError("evidence override must be a JSON object")
    return data


def _metrics_completion_source(single_job_summary: dict[str, Any], probe_metrics_status: str) -> str:
    explicit_source = single_job_summary.get("metrics_completion_source")
    if isinstance(explicit_source, str) and explicit_source in ALLOWED_METRICS_COMPLETION_SOURCES:
        return explicit_source
    if probe_metrics_status != "complete":
        return "blocked_missing_metrics"
    source_paths = _flatten_source_paths(single_job_summary.get("record_paths", {}))
    source_paths.extend(_flatten_source_paths(single_job_summary.get("source_paths", {})))
    if any(marker in path for path in source_paths for marker in METRICS_COMPLETION_RERUN_MARKERS):
        return "new_metrics_completion_rerun"
    return "recovered_existing_run_root"


def _flatten_source_paths(value: Any) -> list[str]:
    if isinstance(value, dict):
        collected: list[str] = []
        for item in value.values():
            collected.extend(_flatten_source_paths(item))
        return collected
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    if isinstance(value, str) and value:
        return [value]
    return []


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is None:
        return build_current_report()
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")
    if isinstance(evidence_override.get("bundle_report"), dict):
        return dict(evidence_override["bundle_report"])

    required_keys = (
        "single_job_execution_summary",
        "probe_metrics",
        "post_run_interpretation_gate_report",
        "gis_cog_readiness_report",
    )
    if any(key in evidence_override for key in required_keys):
        missing_inputs = [key for key in required_keys if key not in evidence_override]
        if missing_inputs:
            return blocked_report(missing_inputs, reason="required bundle sections are missing")
        return build_bundle_report(
            single_job_summary=dict(evidence_override["single_job_execution_summary"]),
            probe_metrics=dict(evidence_override["probe_metrics"]),
            post_run_report=dict(evidence_override["post_run_interpretation_gate_report"]),
            gis_report=dict(evidence_override["gis_cog_readiness_report"]),
            source_paths=as_mapping(evidence_override.get("source_paths")),
            canonical_bundle_path=Path(
                str(evidence_override.get("canonical_bundle_path") or CANONICAL_BUNDLE_DIR)
            ),
        )

    return build_current_report()


def build_current_report() -> dict[str, Any]:
    single_job_summary = single_job.build_summary()
    probe_metrics = build_probe_metrics(single_job_summary)
    gis_report = gis_cog.build_gis_cog_readiness_report()
    post_run_report = post_run_gate.build_report(
        build_post_run_evidence(single_job_summary=single_job_summary, gis_report=gis_report, probe_metrics=probe_metrics)
    )
    return build_bundle_report(
        single_job_summary=single_job_summary,
        probe_metrics=probe_metrics,
        post_run_report=post_run_report,
        gis_report=gis_report,
        source_paths=build_source_paths(single_job_summary=single_job_summary, gis_report=gis_report),
        canonical_bundle_path=CANONICAL_BUNDLE_DIR,
    )


def build_bundle_report(
    *,
    single_job_summary: dict[str, Any],
    probe_metrics: dict[str, Any],
    post_run_report: dict[str, Any],
    gis_report: dict[str, Any],
    source_paths: dict[str, Any] | None = None,
    canonical_bundle_path: Path = CANONICAL_BUNDLE_DIR,
) -> dict[str, Any]:
    source_paths = source_paths or {}
    gis_cog_parity_report = build_gis_cog_parity_report(single_job_summary=single_job_summary, gis_report=gis_report)
    gis_cog_scope_report = build_gis_cog_scope_report(
        gis_cog_parity_report=gis_cog_parity_report,
        gis_report=gis_report,
    )
    section_provenance_profile = build_section_provenance_profile(
        single_job_summary=single_job_summary,
        probe_metrics=probe_metrics,
        post_run_report=post_run_report,
        gis_report=gis_report,
        source_paths=source_paths,
    )
    bundle_status, bundle_blockers = derive_bundle_status(
        single_job_summary=single_job_summary,
        probe_metrics=probe_metrics,
        post_run_report=post_run_report,
        gis_report=gis_report,
        section_provenance_profile=section_provenance_profile,
    )
    claim_boundaries = claim_boundaries_from(post_run_report)
    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": str(single_job_summary.get("pilot_id") or DEFAULT_PILOT_ID),
        "run_id": str(single_job_summary.get("run_id") or DEFAULT_RUN_ID),
        "canonical_bundle_path": str(canonical_bundle_path),
        "bundle_status": bundle_status,
        "bundle_provenance_status": bundle_status,
        "bundle_summary": {
            "status": bundle_status,
            "summary": summarize_bundle(bundle_status, single_job_summary, post_run_report, gis_report),
            "blockers": bundle_blockers,
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "single_job_execution_summary": single_job_summary,
        "probe_metrics": probe_metrics,
        "post_run_interpretation_gate_report": post_run_report,
        "failure_taxonomy_report": build_failure_taxonomy_report(
            single_job_summary=single_job_summary,
            probe_metrics=probe_metrics,
            post_run_report=post_run_report,
            gis_report=gis_report,
        ),
        "gis_cog_readiness_report": gis_report,
        "gis_cog_parity_report": gis_cog_parity_report,
        "gis_cog_scope_report": gis_cog_scope_report,
        "multi_zone_balfrin_evidence": build_multi_zone_balfrin_evidence(
            source_paths.get("multi_zone_balfrin_evidence")
        ),
        "section_provenance_profile": section_provenance_profile,
        "claim_boundaries": claim_boundaries,
        "source_paths": source_paths,
        "evidence_sources": evidence_sources(source_paths),
        "missing_inputs": bundle_blockers if bundle_status == "blocked_missing_inputs" else [],
    }
    return report


def build_multi_zone_balfrin_evidence(evidence: Any = None) -> dict[str, Any]:
    if evidence is None:
        return dict(TB267_MULTI_ZONE_BLOCKED_EVIDENCE)
    if isinstance(evidence, str):
        return classify_multi_zone_balfrin_root({"run_root": evidence, "source_paths": [evidence]})
    if not isinstance(evidence, dict):
        return dict(TB267_MULTI_ZONE_BLOCKED_EVIDENCE)
    if evidence.get("preflight_status") == "blocked_reducer_budget" or evidence.get("status") in {
        "blocked_incomplete",
        "blocked_reducer_budget",
    }:
        payload = dict(TB267_MULTI_ZONE_BLOCKED_EVIDENCE)
        payload.update(evidence)
        payload["status"] = "blocked_incomplete"
        payload["evidence_type"] = "blocked"
        payload["root_class"] = "blocked_pre_authorization"
        payload["first_bottleneck_label"] = str(payload.get("first_bottleneck_label") or "manifest_size_bytes")
        payload["next_blocker"] = f"blocked_reducer_budget:{payload['first_bottleneck_label']}"
        return payload
    return classify_multi_zone_balfrin_root(evidence)


def classify_multi_zone_balfrin_root(evidence: dict[str, Any]) -> dict[str, Any]:
    run_root = str(evidence.get("run_root") or "")
    source_paths = [str(path) for path in evidence.get("source_paths", []) if str(path)] if isinstance(evidence.get("source_paths"), list) else []
    all_paths = [run_root, *source_paths]
    if any("tests/fixtures" in path for path in all_paths):
        status = "fixture_backed"
        evidence_type = "fixture_backed"
        root_class = "fixture_backed_multi_zone_root"
    elif evidence.get("probe_status") == "measured_scratch_root" or run_root.startswith("/tmp/"):
        status = "scratch_root"
        evidence_type = "fixture_backed"
        root_class = "scratch_reducer_probe"
    else:
        measured_flags = (
            evidence.get("status") == "measured"
            and evidence.get("preservation_checked") is True
            and evidence.get("post_run_collector_promoted") is True
            and evidence.get("metrics_json_promoted") is True
        )
        status = "measured" if measured_flags else "blocked_incomplete"
        evidence_type = "measured" if measured_flags else "blocked"
        root_class = "measured_multi_zone_balfrin_root" if measured_flags else "incomplete_multi_zone_root"
    first_bottleneck = str(evidence.get("first_bottleneck_label") or evidence.get("first_bottleneck") or "none")
    release_zone_count = evidence.get("release_zone_count")
    return {
        "status": status,
        "evidence_type": evidence_type,
        "root_class": root_class,
        "run_root": run_root or None,
        "release_zone_count": release_zone_count,
        "first_bottleneck_label": first_bottleneck,
        "slurm_job_id": evidence.get("slurm_job_id"),
        "metrics_json_promoted": bool(evidence.get("metrics_json_promoted")),
        "preservation_checked": bool(evidence.get("preservation_checked")),
        "preservation_gate_promoted": bool(evidence.get("preservation_gate_promoted")),
        "post_run_collector_promoted": bool(evidence.get("post_run_collector_promoted")),
        "authorization_status": evidence.get("authorization_status"),
        "source_paths": source_paths,
        "next_blocker": (
            "none"
            if status == "measured"
            else "fixture_backed_not_measured"
            if status == "fixture_backed"
            else "scratch_root_not_live_balfrin"
            if status == "scratch_root"
            else f"incomplete_multi_zone_evidence:{first_bottleneck}"
        ),
        "summary": (
            f"Measured multi-zone Balfrin evidence is present for {release_zone_count} release zones."
            if status == "measured"
            else "Multi-zone evidence is not measured Balfrin evidence and cannot move the scaling frontier by itself."
        ),
    }


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    canonical_bundle_path: Path = CANONICAL_BUNDLE_DIR,
) -> dict[str, Any]:
    section_provenance_profile = [
        {
            "section": "single_job_execution_summary",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "probe_metrics",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "post_run_interpretation_gate_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "failure_taxonomy_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "gis_cog_readiness_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "gis_cog_parity_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
    ]
    gis_cog_parity_report = build_gis_cog_parity_report()
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": DEFAULT_PILOT_ID,
        "run_id": DEFAULT_RUN_ID,
        "canonical_bundle_path": str(canonical_bundle_path),
        "bundle_status": "blocked_missing_inputs",
        "bundle_provenance_status": "blocked_missing_inputs",
        "bundle_summary": {
            "status": "blocked_missing_inputs",
            "summary": reason,
            "blockers": list(missing_inputs),
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "single_job_execution_summary": {
            "schema_version": "balfrin_single_job_execution_sufficiency_v1",
            "status": "blocked_missing_inputs",
        },
        "probe_metrics": {"status": "blocked_missing_inputs"},
        "post_run_interpretation_gate_report": {
            "schema_version": post_run_gate.SCHEMA_VERSION,
            "interpretation_status": "blocked_missing_inputs",
            "artifact_acceptance_status": "blocked_missing_inputs",
            "usable_as_conditional_diagnostic_artifact": False,
            "claim_boundaries": post_run_gate.claim_boundaries(),
        },
        "failure_taxonomy_report": failure_taxonomy.build_report({}),
        "gis_cog_readiness_report": {
            "schema_version": gis_cog.SCHEMA_VERSION,
            "gis_cog_readiness_status": "blocked_missing_inputs",
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
        },
        "gis_cog_parity_report": gis_cog_parity_report,
        "gis_cog_scope_report": build_gis_cog_scope_report(
            gis_cog_parity_report=gis_cog_parity_report,
            gis_report={"gis_cog_readiness_status": "blocked_missing_inputs", "blockers": {}},
        ),
        "multi_zone_balfrin_evidence": build_multi_zone_balfrin_evidence(
            {"status": "blocked_incomplete", "first_bottleneck_label": "missing_inputs"}
        ),
        "section_provenance_profile": section_provenance_profile,
        "claim_boundaries": post_run_gate.claim_boundaries(),
        "source_paths": {},
        "evidence_sources": evidence_sources({}),
        "missing_inputs": list(missing_inputs),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Evidence Bundle",
        f"schema_version: {report['schema_version']}",
        f"bundle_status: {report['bundle_status']}",
        f"bundle_provenance_status: {report.get('bundle_provenance_status', report['bundle_status'])}",
        f"canonical_bundle_path: {report['canonical_bundle_path']}",
        "bundle_summary:",
        f"  status: {report['bundle_summary']['status']}",
        f"  summary: {report['bundle_summary']['summary']}",
    ]
    blockers = report["bundle_summary"].get("blockers") or []
    if blockers:
        lines.append("  blockers:")
        lines.extend(f"    - {blocker}" for blocker in blockers)
    section_counts = report["bundle_summary"].get("section_counts") or {}
    if section_counts:
        lines.append("  section_counts:")
        for key in ("measured", "fixture_backed", "blocked_missing_inputs"):
            if key in section_counts:
                lines.append(f"    {key}: {section_counts[key]}")
    lines.extend(
        [
            "single_job_execution_summary:",
            f"  decision: {report['single_job_execution_summary'].get('decision', 'unknown')}",
            f"  metrics_contract_status: {report['single_job_execution_summary'].get('metrics_contract', {}).get('status', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['single_job_execution_summary'].get('single_job_sufficient_for_next_step', False)}",
            "probe_metrics:",
            f"  status: {report['probe_metrics'].get('status', 'unknown')}",
            f"  metrics_completion_source: {report['probe_metrics'].get('metrics_completion_source', 'unknown')}",
            f"  metrics_completion_outcome: {report['probe_metrics'].get('metrics_completion_outcome', 'unknown')}",
            f"  metrics_completion_attempt_status: {report['probe_metrics'].get('metrics_completion_attempt_status', 'unknown')}",
            f"  wall_time_seconds: {report['probe_metrics'].get('wall_time_seconds', 'unknown')}",
            f"  memory_peak_mb: {report['probe_metrics'].get('memory_peak_mb', 'unknown')}",
            f"  reduced_output_family_counts: {report['probe_metrics'].get('reduced_output_family_counts', {})}",
        ]
    )
    metric_statuses = report["probe_metrics"].get("metric_statuses") or {}
    if metric_statuses:
        lines.append("  metric_statuses:")
        for group_name in ("mandatory", "ancillary"):
            group_statuses = metric_statuses.get(group_name) or {}
            if not group_statuses:
                continue
            lines.append(f"    {group_name}:")
            for key in sorted(group_statuses):
                entry = group_statuses[key]
                line = f"      {key}: {entry.get('status', 'unknown')}"
                reason = entry.get("reason")
                if reason:
                    line += f" ({reason})"
                lines.append(line)
        for key in ("measured", "unavailable", "blocked"):
            values = metric_statuses.get(key)
            if values is not None:
                lines.append(f"    {key}: {values}")
        reduced_counts = metric_statuses.get("reduced_output_family_counts")
        if isinstance(reduced_counts, dict):
            lines.append("    reduced_output_family_counts:")
            lines.append(f"      status: {reduced_counts.get('status', 'unknown')}")
            lines.append(f"      source: {reduced_counts.get('source', 'unknown')}")
            if reduced_counts.get("reason"):
                lines.append(f"      reason: {reduced_counts.get('reason')}")
    metrics_remediation = report["probe_metrics"].get("metrics_remediation") or {}
    if metrics_remediation:
        lines.append("  metrics_remediation:")
        lines.append(f"    status: {metrics_remediation.get('status', 'unknown')}")
        lines.append(f"    missing_mandatory_metrics: {metrics_remediation.get('missing_mandatory_metrics', [])}")
        lines.append(
            f"    unavailable_ancillary_metrics: {metrics_remediation.get('unavailable_ancillary_metrics', [])}"
        )
        lines.append(
            f"    next_run_required_metrics: {metrics_remediation.get('next_run_required_metrics', [])}"
        )
        checklist = metrics_remediation.get("next_run_collection_checklist") or []
        if checklist:
            lines.append("    next_run_collection_checklist:")
            for item in checklist:
                lines.append(
                    "      - "
                    f"{item.get('metric', 'unknown')}: "
                    f"{item.get('group', 'unknown')} | "
                    f"{item.get('status', 'unknown')}"
                )
    lines.extend(
        [
            "ancillary_metrics:",
            f"  validation_output_mode: {report['probe_metrics'].get('ancillary_metrics', {}).get('validation_output_mode', {}).get('status', 'unknown')}",
            f"  output_write_kind_seconds: {report['probe_metrics'].get('ancillary_metrics', {}).get('output_write_kind_seconds', {}).get('status', 'unknown')}",
            f"  output_write_kind_bytes: {report['probe_metrics'].get('ancillary_metrics', {}).get('output_write_kind_bytes', {}).get('status', 'unknown')}",
            f"  ancillary_unavailable_metrics: {report['probe_metrics'].get('ancillary_unavailable_metrics', [])}",
            "post_run_interpretation_gate_report:",
            f"  interpretation_status: {report['post_run_interpretation_gate_report'].get('interpretation_status', 'unknown')}",
            f"  artifact_acceptance_status: {report['post_run_interpretation_gate_report'].get('artifact_acceptance_status', 'unknown')}",
            "failure_taxonomy_report:",
            f"  taxonomy_status: {report['failure_taxonomy_report'].get('taxonomy_status', 'unknown')}",
            f"  observed_failure_classes: {len(report['failure_taxonomy_report'].get('observed_failure_classes', []))}",
            "gis_cog_readiness_report:",
            f"  gis_cog_readiness_status: {report['gis_cog_readiness_report'].get('gis_cog_readiness_status', 'unknown')}",
            "claim_boundaries:",
            f"  operational_claims_allowed: {report['claim_boundaries'].get('operational_claims_allowed', False)}",
            f"  physical_probability_claims_allowed: {report['claim_boundaries'].get('physical_probability_claims_allowed', False)}",
            f"  annual_frequency_claims_allowed: {report['claim_boundaries'].get('annual_frequency_claims_allowed', False)}",
            f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries'].get('risk_exposure_vulnerability_claims_allowed', False)}",
            f"  scale_up_authorized: {report['claim_boundaries'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['claim_boundaries'].get('distributed_execution_authorized', False)}",
        ]
    )
    parity_report = report.get("gis_cog_parity_report")
    if isinstance(parity_report, dict):
        lines.extend(
            [
                "gis_cog_parity_report:",
                f"  parity_status: {parity_report.get('parity_status', 'unknown')}",
                f"  layer_counts: {parity_report.get('layer_counts', {})}",
                f"  curve_linkage: {parity_report.get('curve_linkage', {})}",
                f"  manifest_consistency: {parity_report.get('manifest_consistency', {})}",
                f"  scope_delta: {parity_report.get('scope_delta', {})}",
            ]
        )
    scope_report = report.get("gis_cog_scope_report")
    if isinstance(scope_report, dict):
        lines.extend(
            [
                "gis_cog_scope_report:",
                f"  scope_status: {scope_report.get('scope_status', 'unknown')}",
                f"  scope_delta_status: {scope_report.get('scope_delta_status', 'unknown')}",
                f"  parity_status: {scope_report.get('parity_status', 'unknown')}",
            ]
        )
    multi_zone = report.get("multi_zone_balfrin_evidence")
    if isinstance(multi_zone, dict):
        lines.extend(
            [
                "multi_zone_balfrin_evidence:",
                f"  status: {multi_zone.get('status', 'unknown')}",
                f"  evidence_type: {multi_zone.get('evidence_type', 'unknown')}",
                f"  root_class: {multi_zone.get('root_class', 'unknown')}",
                f"  first_bottleneck_label: {multi_zone.get('first_bottleneck_label', 'unknown')}",
                f"  next_blocker: {multi_zone.get('next_blocker', 'unknown')}",
            ]
        )
    section_provenance_profile = report.get("section_provenance_profile") or []
    if section_provenance_profile:
        lines.append("section_provenance_profile:")
        for section in section_provenance_profile:
            lines.append(
                f"  - {section.get('section', 'unknown')}: "
                f"{section.get('evidence_type', 'unknown')} | "
                f"{section.get('status', 'unknown')}"
            )
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        lines.extend(f"  - {item}" for item in report["missing_inputs"])
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        json_output = json_output or artifact_dir / f"{SCHEMA_VERSION}.json"
        text_output = text_output or artifact_dir / f"{SCHEMA_VERSION}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report), encoding="utf-8")


def build_source_paths(*, single_job_summary: dict[str, Any], gis_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "single_job_record_paths": single_job_summary.get("record_paths", {}),
        "post_run_contract_path": post_run_gate.DEFAULT_CONTRACT.as_posix(),
        "gis_artifact_roots": gis_report.get("artifact_roots", []),
    }


def build_gis_cog_parity_report(
    *,
    single_job_summary: dict[str, Any] | None = None,
    gis_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    single_job_summary = single_job_summary or {}
    gis_report = gis_report or {}
    standard_package_readiness_status = str(gis_report.get("standard_package_readiness_status") or "blocked_missing_inputs")
    converted_package_readiness_status = str(gis_report.get("converted_package_readiness_status") or "not_provided")
    converted_package_layer_inventory_status = str(gis_report.get("converted_package_layer_inventory_status") or "not_provided")
    standard_layer_counts = gis_report.get("standard_package_layer_counts") or {}
    converted_layer_counts = gis_report.get("converted_package_layer_counts") or {}
    converted_scope_deltas = gis_report.get("converted_package_scope_deltas") or {}
    converted_scope_boundaries = gis_report.get("converted_package_scope_boundaries") or {}
    hazard_manifest_paths = gis_report.get("hazard_manifest_paths") or {}
    map_package_manifest_paths = gis_report.get("map_package_manifest_paths") or {}
    pilot_gis_package_manifest_paths = gis_report.get("pilot_gis_package_manifest_paths") or {}
    curve_row_count = (
        single_job_summary.get("metrics_contract", {})
        .get("mandatory_metrics", {})
        .get("conditional_curve_row_count")
    )
    curve_linked = curve_row_count is not None and curve_row_count > 0
    hazard_keys = set(hazard_manifest_paths) if isinstance(hazard_manifest_paths, dict) else set()
    map_keys = set(map_package_manifest_paths) if isinstance(map_package_manifest_paths, dict) else set()
    pilot_keys = set(pilot_gis_package_manifest_paths) if isinstance(pilot_gis_package_manifest_paths, dict) else set()
    manifest_keys = sorted(hazard_keys | map_keys | pilot_keys)
    manifest_consistent = bool(manifest_keys) and hazard_keys == map_keys == pilot_keys
    has_scope_delta = converted_package_layer_inventory_status in {"scope_reduced", "scope_extended", "inventory_mismatch"}
    has_scope_delta = has_scope_delta or any(
        isinstance(delta, dict) and delta.get("status") == "scope_delta" for delta in converted_scope_deltas.values()
    )
    if gis_report.get("gis_cog_readiness_status") == "blocked_missing_inputs":
        parity_status = "blocked_missing_inputs"
    elif not manifest_consistent or not curve_linked:
        parity_status = "blocked_missing_inputs"
    elif has_scope_delta:
        parity_status = "bounded_scope"
    else:
        parity_status = "ready"
    return {
        "schema_version": GIS_COG_PARITY_SCHEMA_VERSION,
        "parity_status": parity_status,
        "readiness_status": parity_status,
        "layer_counts": {
            "standard": standard_layer_counts,
            "converted": converted_layer_counts,
        },
        "cog_metadata": {
            "standard_package_readiness_status": standard_package_readiness_status,
            "converted_package_readiness_status": converted_package_readiness_status,
            "standard_package_status": gis_report.get("standard_package_status", {}),
            "converted_package_status": gis_report.get("converted_package_status", {}),
            "cog_readiness_indicators": gis_report.get("cog_readiness_indicators", {}),
            "converted_sample_status": gis_report.get("converted_sample_status", "not_provided"),
            "qgis_manual_qa_status": gis_report.get("qgis_manual_qa_status", "not_run"),
        },
        "curve_linkage": {
            "status": "linked" if curve_linked else "blocked_missing_inputs",
            "conditional_curve_row_count": curve_row_count,
            "trajectory_plan_id": single_job_summary.get("metrics_contract", {})
            .get("mandatory_metrics", {})
            .get("restartability_metadata", {})
            .get("trajectory_plan_id"),
            "reducer_plan_id": single_job_summary.get("metrics_contract", {})
            .get("mandatory_metrics", {})
            .get("restartability_metadata", {})
            .get("reducer_plan_id"),
        },
        "manifest_consistency": {
            "status": "consistent" if manifest_consistent else "blocked_missing_inputs",
            "artifact_ids": manifest_keys,
            "hazard_manifest_paths": hazard_manifest_paths,
            "map_package_manifest_paths": map_package_manifest_paths,
            "pilot_gis_package_manifest_paths": pilot_gis_package_manifest_paths,
        },
        "scope_delta": {
            "status": "scope_delta" if has_scope_delta else "parity_match",
            "converted_package_layer_inventory_status": converted_package_layer_inventory_status,
            "converted_package_scope_boundaries": converted_scope_boundaries,
            "converted_package_scope_deltas": converted_scope_deltas,
        },
        "sources": {
            "single_job_summary": single_job_summary.get("record_paths", {}),
            "gis_artifact_roots": gis_report.get("artifact_roots", []),
        },
    }


def build_gis_cog_scope_report(
    *,
    gis_cog_parity_report: dict[str, Any],
    gis_report: dict[str, Any],
) -> dict[str, Any]:
    parity_status = str(gis_cog_parity_report.get("parity_status") or "blocked_missing_inputs")
    scope_delta = gis_cog_parity_report.get("scope_delta")
    if not isinstance(scope_delta, dict):
        scope_delta = {}
    if parity_status == "blocked_missing_inputs":
        scope_status = "blocked_missing_inputs"
    elif parity_status == "bounded_scope":
        scope_status = "bounded_scope"
    elif parity_status == "ready":
        scope_status = "full_scope"
    else:
        scope_status = "inconclusive"
    return {
        "schema_version": GIS_COG_SCOPE_SCHEMA_VERSION,
        "scope_status": scope_status,
        "status": scope_status,
        "parity_status": parity_status,
        "readiness_status": str(gis_report.get("gis_cog_readiness_status") or "blocked_missing_inputs"),
        "scope_delta_status": str(scope_delta.get("status") or "parity_match"),
        "converted_package_layer_inventory_status": str(
            scope_delta.get("converted_package_layer_inventory_status") or "not_provided"
        ),
        "converted_package_scope_boundaries": scope_delta.get("converted_package_scope_boundaries") or {},
        "converted_package_scope_deltas": scope_delta.get("converted_package_scope_deltas") or {},
        "blockers": gis_report.get("blockers", {}),
    }


def _metric_status_from_value(
    value: Any,
    *,
    source: str,
    unavailable_reason: str,
    blocked_reason: str,
) -> dict[str, Any]:
    status = "measured"
    reason = ""
    if value is None:
        status = "blocked" if blocked_reason else "unavailable"
        reason = blocked_reason if status == "blocked" else unavailable_reason
    elif isinstance(value, dict) and not value:
        status = "unavailable"
        reason = unavailable_reason
    payload = {
        "status": status,
        "source": source,
        "value": value,
    }
    if reason:
        payload["reason"] = reason
    return payload


def _build_metrics_remediation(metric_statuses: dict[str, Any]) -> dict[str, Any]:
    mandatory_statuses = metric_statuses.get("mandatory", {}) if isinstance(metric_statuses, dict) else {}
    ancillary_statuses = metric_statuses.get("ancillary", {}) if isinstance(metric_statuses, dict) else {}
    ordered_fields = [
        ("mandatory", "wall_time_seconds"),
        ("mandatory", "memory_peak_mb"),
        ("mandatory", "validation_output.file_count"),
        ("mandatory", "validation_output.bytes"),
        ("mandatory", "hazard_output.file_count"),
        ("mandatory", "hazard_output.bytes"),
        ("mandatory", "conditional_curve_row_count"),
        ("mandatory", "restartability_metadata.trajectory_plan_id"),
        ("mandatory", "restartability_metadata.reducer_plan_id"),
        ("mandatory", "restartability_metadata.trajectory_decision_counts"),
        ("mandatory", "restartability_metadata.reducer_decision_counts"),
        ("ancillary", "validation_output_mode"),
        ("ancillary", "output_write_kind_seconds"),
        ("ancillary", "output_write_kind_bytes"),
    ]
    checklist: list[dict[str, Any]] = []
    missing_mandatory_metrics: list[str] = []
    unavailable_ancillary_metrics: list[str] = []
    next_run_required_metrics: list[str] = []

    for group_name, metric_name in ordered_fields:
        group_statuses = mandatory_statuses if group_name == "mandatory" else ancillary_statuses
        entry = group_statuses.get(metric_name, {}) if isinstance(group_statuses, dict) else {}
        status = str(entry.get("status") or "unknown")
        if status not in {"blocked", "unavailable"}:
            continue
        checklist.append(
            {
                "metric": metric_name,
                "group": group_name,
                "status": status,
                "source": entry.get("source"),
                "reason": entry.get("reason", ""),
                "next_run_required": True,
            }
        )
        next_run_required_metrics.append(metric_name)
        if group_name == "mandatory":
            missing_mandatory_metrics.append(metric_name)
        else:
            unavailable_ancillary_metrics.append(metric_name)

    remediation_status = "complete" if not next_run_required_metrics else "action_required"
    return {
        "schema_version": "balfrin_probe_metrics_remediation_v1",
        "status": remediation_status,
        "missing_mandatory_metrics": missing_mandatory_metrics,
        "unavailable_ancillary_metrics": unavailable_ancillary_metrics,
        "next_run_required_metrics": next_run_required_metrics,
        "next_run_collection_checklist": checklist,
    }


def _derive_metric_statuses(
    *,
    mandatory: dict[str, Any],
    ancillary_metrics: dict[str, Any],
) -> dict[str, Any]:
    wall_time = mandatory.get("wall_time_seconds", {}) if isinstance(mandatory, dict) else {}
    memory_peak = mandatory.get("memory_peak_mb", {}) if isinstance(mandatory, dict) else {}
    validation_output = mandatory.get("validation_output", {}) if isinstance(mandatory, dict) else {}
    hazard_output = mandatory.get("hazard_output", {}) if isinstance(mandatory, dict) else {}
    restartability = mandatory.get("restartability_metadata", {}) if isinstance(mandatory, dict) else {}
    reduced_output_family_counts = (
        mandatory.get("reduced_output_family_counts", {}) if isinstance(mandatory, dict) else {}
    )

    mandatory_statuses = {
        "wall_time_seconds": _metric_status_from_value(
            wall_time.get("value"),
            source="single_job_summary.metrics_contract.mandatory_metrics.wall_time_seconds.value",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required wall-time evidence",
        ),
        "memory_peak_mb": _metric_status_from_value(
            memory_peak.get("value"),
            source="single_job_summary.metrics_contract.mandatory_metrics.memory_peak_mb.value",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required peak-memory evidence",
        ),
        "validation_output.file_count": _metric_status_from_value(
            validation_output.get("file_count"),
            source="single_job_summary.metrics_contract.mandatory_metrics.validation_output.file_count",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required validation output file count",
        ),
        "validation_output.bytes": _metric_status_from_value(
            validation_output.get("bytes"),
            source="single_job_summary.metrics_contract.mandatory_metrics.validation_output.bytes",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required validation output byte count",
        ),
        "hazard_output.file_count": _metric_status_from_value(
            hazard_output.get("file_count"),
            source="single_job_summary.metrics_contract.mandatory_metrics.hazard_output.file_count",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required hazard output file count",
        ),
        "hazard_output.bytes": _metric_status_from_value(
            hazard_output.get("bytes"),
            source="single_job_summary.metrics_contract.mandatory_metrics.hazard_output.bytes",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required hazard output byte count",
        ),
        "conditional_curve_row_count": _metric_status_from_value(
            mandatory.get("conditional_curve_row_count"),
            source="single_job_summary.metrics_contract.mandatory_metrics.conditional_curve_row_count",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required conditional-curve row count",
        ),
        "restartability_metadata.trajectory_plan_id": _metric_status_from_value(
            restartability.get("trajectory_plan_id"),
            source="single_job_summary.metrics_contract.mandatory_metrics.restartability_metadata.trajectory_plan_id",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required trajectory plan identifier",
        ),
        "restartability_metadata.reducer_plan_id": _metric_status_from_value(
            restartability.get("reducer_plan_id"),
            source="single_job_summary.metrics_contract.mandatory_metrics.restartability_metadata.reducer_plan_id",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required reducer plan identifier",
        ),
        "restartability_metadata.trajectory_decision_counts": _metric_status_from_value(
            restartability.get("trajectory_decision_counts"),
            source="single_job_summary.metrics_contract.mandatory_metrics.restartability_metadata.trajectory_decision_counts",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required trajectory decision counts",
        ),
        "restartability_metadata.reducer_decision_counts": _metric_status_from_value(
            restartability.get("reducer_decision_counts"),
            source="single_job_summary.metrics_contract.mandatory_metrics.restartability_metadata.reducer_decision_counts",
            unavailable_reason="not retained in the canonical bundle snapshot",
            blocked_reason="missing required reducer decision counts",
        ),
    }
    ancillary_statuses = {
        "validation_output_mode": _metric_status_from_value(
            ancillary_metrics.get("validation_output_mode", {}).get("value") if isinstance(ancillary_metrics, dict) else None,
            source="single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.validation_output_mode",
            unavailable_reason="the canonical bundle does not retain reduced-output family counts for this field",
            blocked_reason="",
        ),
        "output_write_kind_seconds": _metric_status_from_value(
            ancillary_metrics.get("output_write_kind_seconds", {}).get("value") if isinstance(ancillary_metrics, dict) else None,
            source="output_root.scaling_summary.output_write_kind_seconds",
            unavailable_reason="the canonical bundle does not retain output_root.scaling_summary",
            blocked_reason="",
        ),
        "output_write_kind_bytes": _metric_status_from_value(
            ancillary_metrics.get("output_write_kind_bytes", {}).get("value") if isinstance(ancillary_metrics, dict) else None,
            source="output_root.scaling_summary.output_write_kind_bytes",
            unavailable_reason="the canonical bundle does not retain output_root.scaling_summary",
            blocked_reason="",
        ),
    }
    measured = sorted(
        [
            name
            for name, entry in {**mandatory_statuses, **ancillary_statuses}.items()
            if entry.get("status") == "measured"
        ]
    )
    unavailable = sorted(
        [name for name, entry in ancillary_statuses.items() if entry.get("status") == "unavailable"]
    )
    blocked = sorted([name for name, entry in mandatory_statuses.items() if entry.get("status") == "blocked"])
    return {
        "mandatory": mandatory_statuses,
        "ancillary": ancillary_statuses,
        "measured": measured,
        "unavailable": unavailable,
        "blocked": blocked,
        "reduced_output_family_counts": {
            "status": "measured" if reduced_output_family_counts else "unavailable",
            "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts",
            "value": reduced_output_family_counts,
            "reason": (
                ""
                if reduced_output_family_counts
                else "the canonical bundle does not retain the split-output family counts for this summary"
            ),
        },
    }


def build_probe_metrics(single_job_summary: dict[str, Any]) -> dict[str, Any]:
    metrics = single_job_summary.get("metrics_contract", {})
    mandatory = metrics.get("mandatory_metrics", {}) if isinstance(metrics, dict) else {}
    wall_time = mandatory.get("wall_time_seconds", {}) if isinstance(mandatory, dict) else {}
    memory_peak = mandatory.get("memory_peak_mb", {}) if isinstance(mandatory, dict) else {}
    validation_output = mandatory.get("validation_output", {}) if isinstance(mandatory, dict) else {}
    hazard_output = mandatory.get("hazard_output", {}) if isinstance(mandatory, dict) else {}
    restartability = mandatory.get("restartability_metadata", {}) if isinstance(mandatory, dict) else {}
    reduced_output_family_counts = mandatory.get("reduced_output_family_counts", {}) if isinstance(mandatory, dict) else {}
    ancillary_metrics = (
        metrics.get("ancillary_metrics", {}) if isinstance(metrics, dict) and metrics.get("ancillary_metrics") else {}
    )
    if not ancillary_metrics:
        ancillary_metrics = {
            "validation_output_mode": {
                "status": "unavailable" if reduced_output_family_counts.get("validation_output_mode") is None else "available",
                "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.validation_output_mode",
                "value": reduced_output_family_counts.get("validation_output_mode"),
            },
            "output_write_kind_seconds": {
                "status": "unavailable" if reduced_output_family_counts.get("output_write_kind_seconds") is None else "available",
                "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.output_write_kind_seconds",
                "value": reduced_output_family_counts.get("output_write_kind_seconds"),
            },
            "output_write_kind_bytes": {
                "status": "unavailable" if reduced_output_family_counts.get("output_write_kind_bytes") is None else "available",
                "source": "single_job_summary.metrics_contract.mandatory_metrics.reduced_output_family_counts.output_write_kind_bytes",
                "value": reduced_output_family_counts.get("output_write_kind_bytes"),
            },
        }
    ancillary_unavailable_metrics = (
        metrics.get("ancillary_unavailable_metrics")
        if isinstance(metrics, dict) and isinstance(metrics.get("ancillary_unavailable_metrics"), list)
        else [name for name, metric in ancillary_metrics.items() if metric.get("status") == "unavailable"]
    )
    metric_statuses = metrics.get("metric_statuses")
    if not isinstance(metric_statuses, dict):
        metric_statuses = _derive_metric_statuses(mandatory=mandatory, ancillary_metrics=ancillary_metrics)
    metrics_remediation = metrics.get("metrics_remediation")
    if not isinstance(metrics_remediation, dict):
        metrics_remediation = _build_metrics_remediation(metric_statuses)
    metrics_completion_source = _metrics_completion_source(
        single_job_summary,
        str(metrics.get("status") or "blocked_missing_inputs"),
    )
    metrics_completion_outcome = metrics_report.classify_metrics_completion_outcome(
        report_status="complete"
        if metrics.get("status") == "complete"
        else str(metrics.get("status") or "blocked_missing_inputs"),
        metrics_contract_status=str(metrics.get("status") or "blocked_missing_inputs"),
        metrics_completion_source=metrics_completion_source,
        explicit_outcome=metrics.get("metrics_completion_outcome")
        if isinstance(metrics.get("metrics_completion_outcome"), str)
        else None,
        attempt_status=metrics.get("metrics_completion_attempt_status")
        if isinstance(metrics.get("metrics_completion_attempt_status"), str)
        else None,
    )
    return {
        "status": metrics.get("status", "blocked_missing_inputs"),
        "metrics_completion_source": metrics_completion_source,
        "metrics_completion_outcome": metrics_completion_outcome,
        "metrics_completion_attempt_status": metrics.get("metrics_completion_attempt_status"),
        "wall_time_seconds": wall_time.get("value"),
        "memory_peak_mb": memory_peak.get("value"),
        "validation_output": {
            "file_count": validation_output.get("file_count"),
            "bytes": validation_output.get("bytes"),
        },
        "hazard_output": {
            "file_count": hazard_output.get("file_count"),
            "bytes": hazard_output.get("bytes"),
        },
        "reduced_output_family_counts": reduced_output_family_counts,
        "conditional_curve_row_count": mandatory.get("conditional_curve_row_count"),
        "restartability_metadata": restartability,
        "ancillary_metrics": ancillary_metrics,
        "ancillary_unavailable_metrics": ancillary_unavailable_metrics,
        "metric_statuses": metric_statuses,
        "metrics_remediation": metrics_remediation,
        "output_write_kind_seconds": ancillary_metrics.get("output_write_kind_seconds", {}).get("value", {}),
        "output_write_kind_bytes": ancillary_metrics.get("output_write_kind_bytes", {}).get("value", {}),
    }


def build_section_provenance_profile(
    *,
    single_job_summary: dict[str, Any],
    probe_metrics: dict[str, Any],
    post_run_report: dict[str, Any],
    gis_report: dict[str, Any],
    source_paths: dict[str, Any],
) -> list[dict[str, Any]]:
    failure_report = build_failure_taxonomy_report(
        single_job_summary=single_job_summary,
        probe_metrics=probe_metrics,
        post_run_report=post_run_report,
        gis_report=gis_report,
    )
    parity_report = build_gis_cog_parity_report(single_job_summary=single_job_summary, gis_report=gis_report)
    sections = [
        (
            "single_job_execution_summary",
            single_job_summary,
            collect_source_paths(source_paths, "single_job_record_paths"),
        ),
        ("probe_metrics", probe_metrics, collect_probe_metric_paths(probe_metrics)),
        (
            "post_run_interpretation_gate_report",
            post_run_report,
            [source_paths.get("post_run_contract_path")],
        ),
        (
            "failure_taxonomy_report",
            failure_report,
            [source_paths.get("post_run_contract_path")],
        ),
        ("gis_cog_readiness_report", gis_report, collect_source_paths(source_paths, "gis_artifact_roots")),
        (
            "gis_cog_parity_report",
            parity_report,
            collect_source_paths(source_paths, "gis_artifact_roots"),
        ),
    ]
    profile: list[dict[str, Any]] = []
    for section_name, section_payload, section_paths in sections:
        normalized_paths = [path for path in section_paths if isinstance(path, str) and path]
        profile.append(
            {
                "section": section_name,
                "status": section_status(section_name, section_payload),
                "evidence_type": classify_evidence_type(section_name, section_payload, normalized_paths),
                "source_paths": normalized_paths,
            }
        )
    return profile


def collect_source_paths(source_paths: dict[str, Any], key: str) -> list[str]:
    value = source_paths.get(key)
    if isinstance(value, dict):
        collected: list[str] = []
        for item in value.values():
            if isinstance(item, str) and item:
                collected.append(item)
            elif isinstance(item, list):
                collected.extend(str(entry) for entry in item if isinstance(entry, str) and entry)
        return collected
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    if isinstance(value, str) and value:
        return [value]
    return []


def collect_probe_metric_paths(probe_metrics: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("run_root", "probe_manifest_path", "command_plan_path", "hazard_manifest_path", "output_root"):
        value = probe_metrics.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    return paths


def section_status(section_name: str, section_payload: dict[str, Any]) -> str:
    if section_name == "single_job_execution_summary":
        status = str(
            section_payload.get("metrics_contract", {}).get("status")
            or section_payload.get("decision")
            or section_payload.get("status")
            or ""
        ).strip()
    elif section_name == "failure_taxonomy_report":
        status = str(section_payload.get("taxonomy_status") or section_payload.get("status") or "").strip()
    elif section_name == "gis_cog_parity_report":
        status = str(section_payload.get("parity_status") or section_payload.get("status") or "").strip()
    else:
        status = str(
            section_payload.get("status")
            or section_payload.get("interpretation_status")
            or section_payload.get("gis_cog_readiness_status")
            or ""
        ).strip()
    return status or "blocked_missing_inputs"


def classify_evidence_type(section_name: str, section_payload: dict[str, Any], source_paths: list[str]) -> str:
    status = section_status(section_name, section_payload)
    if status.startswith("blocked") or status == "missing":
        return "blocked"
    if any(is_fixture_path(path) for path in source_paths):
        return "fixture_backed"
    return "measured"


def is_fixture_path(path: str) -> bool:
    candidate = Path(path)
    for marker in FIXTURE_PATH_MARKERS:
        marker_length = len(marker)
        for index in range(len(candidate.parts) - marker_length + 1):
            if tuple(candidate.parts[index : index + marker_length]) == marker:
                return True
    return False


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 0}
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type == "measured":
            counts["measured"] += 1
        elif evidence_type == "fixture_backed":
            counts["fixture_backed"] += 1
        else:
            counts["blocked_missing_inputs"] += 1
    return counts


def build_post_run_evidence(
    *,
    single_job_summary: dict[str, Any],
    gis_report: dict[str, Any],
    probe_metrics: dict[str, Any],
) -> dict[str, Any]:
    restartability = single_job_summary.get("restartability_evidence", {})
    readiness_status = "ready_with_scope_limits" if single_job_summary.get("decision") == "defer" else "ready"
    convergence_status = (
        "measured"
        if probe_metrics.get("status") == "complete"
        and restartability.get("repeat_reuse_classification") == "pass_reuse_stable"
        and restartability.get("trajectory_plan_id_stable") is True
        and restartability.get("reducer_plan_id_stable") is True
        and restartability.get("changed_artifact_count", 1) == 0
        else "inconclusive"
    )
    output_status = (
        "summary_only_not_rebuildable"
        if single_job_summary.get("validation_output_blocker_status") == "blocker_retained"
        else "measured"
    )
    return {
        "pilot_id": single_job_summary.get("pilot_id") or DEFAULT_PILOT_ID,
        "run_id": single_job_summary.get("run_id") or DEFAULT_RUN_ID,
        "contract_path": str(post_run_gate.DEFAULT_CONTRACT),
        "readiness_check": {
            "status": readiness_status,
            "summary": "Balfrin single-job evidence is present, but the bundle keeps the release-zone scope explicit.",
        },
        "convergence_stability_check": {
            "status": convergence_status,
            "summary": "Restartability and output evidence are carried into the canonical bundle without implying operational closure.",
        },
        "output_check": {
            "status": output_status,
            "summary": "Output pressure remains explicit in the bundled evidence.",
        },
        "gis_cog_check": {
            "status": gis_report.get("gis_cog_readiness_status", "blocked_missing_inputs"),
            "summary": "GIS / COG readiness is copied into the bundle as a read-only review signal.",
        },
        "physical_credibility_check": {
            "status": "not_established",
            "summary": "Physical credibility remains unestablished and stays outside any probability claim.",
        },
    }


def claim_boundaries_from(post_run_report: dict[str, Any]) -> dict[str, Any]:
    boundaries = post_run_report.get("claim_boundaries")
    if isinstance(boundaries, dict):
        return dict(boundaries)
    return post_run_gate.claim_boundaries()


def derive_bundle_status(
    *,
    single_job_summary: dict[str, Any],
    probe_metrics: dict[str, Any],
    post_run_report: dict[str, Any],
    gis_report: dict[str, Any],
    section_provenance_profile: list[dict[str, Any]] | None = None,
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if probe_metrics.get("status") == "blocked_missing_inputs":
        blockers.append("probe_metrics")
    if single_job_summary.get("metrics_contract", {}).get("status") == "blocked_pending_evidence":
        blockers.append("single_job_execution_summary")
    if post_run_report.get("interpretation_status") == "blocked_missing_inputs":
        blockers.append("post_run_interpretation_gate_report")
    if gis_report.get("gis_cog_readiness_status") == "blocked_missing_inputs":
        blockers.append("gis_cog_readiness_report")
    if blockers:
        return "blocked_missing_inputs", blockers

    profile = section_provenance_profile or []
    has_fixture_sections = any(section.get("evidence_type") == "fixture_backed" for section in profile)
    has_measured_sections = any(section.get("evidence_type") == "measured" for section in profile)
    if has_fixture_sections and not has_measured_sections:
        return "fixture_backed", blockers
    return "measured", blockers


def claim_boundary_bools(post_run_report: dict[str, Any]) -> bool:
    boundaries = post_run_report.get("claim_boundaries")
    if not isinstance(boundaries, dict):
        return False
    return all(
        boundaries.get(key) is False
        for key in (
            "operational_claims_allowed",
            "physical_probability_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "scale_up_authorized",
            "distributed_execution_authorized",
        )
    )


def summarize_bundle(
    bundle_status: str,
    single_job_summary: dict[str, Any],
    post_run_report: dict[str, Any],
    gis_report: dict[str, Any],
) -> str:
    if bundle_status == "blocked_missing_inputs":
        return "Balfrin evidence is blocked because one or more required source sections are absent."
    if bundle_status == "measured":
        return (
            "Balfrin readiness, metrics, outputs, GIS / COG status, ancillary unavailable states, "
            "restartability, interpretation checks, and next-run remediation fields are measured and bundled with claim boundaries intact."
        )
    if bundle_status == "fixture_backed":
        return "Balfrin evidence is fixture-backed rather than measured; the bundle keeps that distinction explicit."
    return (
        "Balfrin evidence is present, but one or more sections remain inconclusive or scope-limited; "
        "the bundle keeps the diagnostic boundaries explicit."
    )


def evidence_sources(source_paths: dict[str, Any]) -> list[str]:
    sources = [
        "scripts/summarize_balfrin_single_job_execution.py",
        "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        "scripts/summarize_balfrin_failure_taxonomy.py",
        "scripts/audit_gis_cog_package_readiness.py",
        "docs/balfrin_restartability_recovery_report.md",
    ]
    if source_paths:
        sources.append("validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1")
    return sources


def build_failure_taxonomy_report(
    *,
    single_job_summary: dict[str, Any],
    probe_metrics: dict[str, Any],
    post_run_report: dict[str, Any],
    gis_report: dict[str, Any],
) -> dict[str, Any]:
    return failure_taxonomy.build_report(
        {
            "pilot_id": single_job_summary.get("pilot_id"),
            "run_id": single_job_summary.get("run_id"),
            "single_job_summary": single_job_summary,
            "probe_metrics": probe_metrics,
            "post_run_report": post_run_report,
            "readiness_check": post_run_report.get("readiness_check"),
            "gis_report": gis_report,
            "runtime_report": single_job_summary.get("runtime_report"),
            "submission_report": single_job_summary.get("submission_report"),
        }
    )


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
