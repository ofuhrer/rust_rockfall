#!/usr/bin/env python3
"""Summarize the canonical Balfrin evidence bundle.

This helper is read-only. It assembles the measured Balfrin readiness,
metrics, outputs, restartability, GIS / COG status, and post-run
interpretation checks into one auditable JSON or text bundle. It preserves
claim boundaries explicitly and returns ``blocked_missing_inputs`` rather than
guessing when required evidence is absent.
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
from scripts import summarize_balfrin_post_run_interpretation_gate as post_run_gate
from scripts import summarize_balfrin_single_job_execution as single_job


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_evidence_bundle_v1"
CANONICAL_BUNDLE_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1"
DEFAULT_PILOT_ID = "tschamut_public_pilot"
DEFAULT_RUN_ID = "tschamut_public_balfrin_single_release_zone_v1"


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
    bundle_status, bundle_blockers = derive_bundle_status(
        single_job_summary=single_job_summary,
        probe_metrics=probe_metrics,
        post_run_report=post_run_report,
        gis_report=gis_report,
    )
    claim_boundaries = claim_boundaries_from(post_run_report)
    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": str(single_job_summary.get("pilot_id") or DEFAULT_PILOT_ID),
        "run_id": str(single_job_summary.get("run_id") or DEFAULT_RUN_ID),
        "canonical_bundle_path": str(canonical_bundle_path),
        "bundle_status": bundle_status,
        "bundle_summary": {
            "status": bundle_status,
            "summary": summarize_bundle(bundle_status, single_job_summary, post_run_report, gis_report),
            "blockers": bundle_blockers,
        },
        "single_job_execution_summary": single_job_summary,
        "probe_metrics": probe_metrics,
        "post_run_interpretation_gate_report": post_run_report,
        "gis_cog_readiness_report": gis_report,
        "claim_boundaries": claim_boundaries,
        "source_paths": source_paths,
        "evidence_sources": evidence_sources(source_paths),
        "missing_inputs": bundle_blockers if bundle_status == "blocked_missing_inputs" else [],
    }
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    canonical_bundle_path: Path = CANONICAL_BUNDLE_DIR,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": DEFAULT_PILOT_ID,
        "run_id": DEFAULT_RUN_ID,
        "canonical_bundle_path": str(canonical_bundle_path),
        "bundle_status": "blocked_missing_inputs",
        "bundle_summary": {
            "status": "blocked_missing_inputs",
            "summary": reason,
            "blockers": list(missing_inputs),
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
        "gis_cog_readiness_report": {
            "schema_version": gis_cog.SCHEMA_VERSION,
            "gis_cog_readiness_status": "blocked_missing_inputs",
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
        },
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
        f"canonical_bundle_path: {report['canonical_bundle_path']}",
        "bundle_summary:",
        f"  status: {report['bundle_summary']['status']}",
        f"  summary: {report['bundle_summary']['summary']}",
    ]
    blockers = report["bundle_summary"].get("blockers") or []
    if blockers:
        lines.append("  blockers:")
        lines.extend(f"    - {blocker}" for blocker in blockers)
    lines.extend(
        [
            "single_job_execution_summary:",
            f"  decision: {report['single_job_execution_summary'].get('decision', 'unknown')}",
            f"  metrics_contract_status: {report['single_job_execution_summary'].get('metrics_contract', {}).get('status', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['single_job_execution_summary'].get('single_job_sufficient_for_next_step', False)}",
            "probe_metrics:",
            f"  status: {report['probe_metrics'].get('status', 'unknown')}",
            f"  wall_time_seconds: {report['probe_metrics'].get('wall_time_seconds', 'unknown')}",
            f"  memory_peak_mb: {report['probe_metrics'].get('memory_peak_mb', 'unknown')}",
            "post_run_interpretation_gate_report:",
            f"  interpretation_status: {report['post_run_interpretation_gate_report'].get('interpretation_status', 'unknown')}",
            f"  artifact_acceptance_status: {report['post_run_interpretation_gate_report'].get('artifact_acceptance_status', 'unknown')}",
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


def build_probe_metrics(single_job_summary: dict[str, Any]) -> dict[str, Any]:
    metrics = single_job_summary.get("metrics_contract", {})
    mandatory = metrics.get("mandatory_metrics", {}) if isinstance(metrics, dict) else {}
    wall_time = mandatory.get("wall_time_seconds", {}) if isinstance(mandatory, dict) else {}
    memory_peak = mandatory.get("memory_peak_mb", {}) if isinstance(mandatory, dict) else {}
    validation_output = mandatory.get("validation_output", {}) if isinstance(mandatory, dict) else {}
    hazard_output = mandatory.get("hazard_output", {}) if isinstance(mandatory, dict) else {}
    restartability = mandatory.get("restartability_metadata", {}) if isinstance(mandatory, dict) else {}
    return {
        "status": metrics.get("status", "blocked_missing_inputs"),
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
        "conditional_curve_row_count": mandatory.get("conditional_curve_row_count"),
        "restartability_metadata": restartability,
    }


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

    complete = (
        probe_metrics.get("status") == "complete"
        and single_job_summary.get("metrics_contract", {}).get("status") == "complete"
        and single_job_summary.get("single_job_sufficient_for_next_step") is True
        and post_run_report.get("interpretation_status") == "measured_conditional_diagnostic"
        and post_run_report.get("artifact_acceptance_status") == "accepted_conditional_diagnostic"
        and gis_report.get("gis_cog_readiness_status") in {"gis_package_ready", "cog_package_ready"}
        and claim_boundary_bools(post_run_report)
    )
    return ("complete" if complete else "incomplete"), blockers


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
    if bundle_status == "complete":
        return "Balfrin readiness, metrics, outputs, GIS / COG status, restartability, and interpretation checks are all present and measurably aligned."
    return (
        "Balfrin evidence is present, but one or more sections remain inconclusive or scope-limited; "
        "the bundle keeps the diagnostic boundaries explicit."
    )


def evidence_sources(source_paths: dict[str, Any]) -> list[str]:
    sources = [
        "scripts/summarize_balfrin_single_job_execution.py",
        "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        "scripts/audit_gis_cog_package_readiness.py",
    ]
    if source_paths:
        sources.append("validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1")
    return sources


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
