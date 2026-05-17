#!/usr/bin/env python3
"""Summarize the target-area Balfrin evidence bundle.

This helper composes the frozen target-area handoff report, the preserved
probe-metrics report, and the measured canonical Balfrin evidence bundle into
one deterministic JSON/text artifact. It keeps the target-area contract,
measured evidence, blocked metrics report, and claim boundaries separate so
reviewers can see what is measured, what is unavailable, and what remains
blocked without overclaiming.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_target_area_demo_handoff as target_handoff
from scripts import summarize_balfrin_evidence_bundle as canonical_bundle
from scripts import summarize_balfrin_probe_metrics_report as probe_metrics_report


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_evidence_bundle_v1"
CANONICAL_BUNDLE_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1"
TARGET_AREA_HANDOFF_REPORT_PATH = (
    ROOT
    / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"
    / "tschamut_public_balfrin_target_area_demo_bundle_report.json"
)
PROBE_METRICS_REPORT_PATH = (
    ROOT / "validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1/balfrin_probe_metrics_report_v1.json"
)
DEFAULT_PILOT_ID = "tschamut_public_pilot"
DEFAULT_RUN_ID = "tschamut_public_balfrin_target_area_demo_v1"


class BalfrinTargetAreaEvidenceBundleError(ValueError):
    """User-facing target-area evidence bundle error."""


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
    except BalfrinTargetAreaEvidenceBundleError as exc:
        print(f"balfrin target-area evidence bundle error: {exc}", file=sys.stderr)
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
        raise BalfrinTargetAreaEvidenceBundleError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinTargetAreaEvidenceBundleError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is None:
        return build_current_report()
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required target-area evidence inputs are missing")
    if isinstance(evidence_override.get("bundle_report"), dict):
        return dict(evidence_override["bundle_report"])
    required_keys = (
        "target_area_demo_handoff_report",
        "probe_metrics_report",
        "canonical_evidence_bundle",
    )
    if any(key in evidence_override for key in required_keys):
        missing_inputs = [key for key in required_keys if key not in evidence_override]
        if missing_inputs:
            return blocked_report(missing_inputs, reason="required target-area evidence sections are missing")
        return assemble_report(
            target_area_demo_handoff_report=dict(evidence_override["target_area_demo_handoff_report"]),
            probe_metrics_report=dict(evidence_override["probe_metrics_report"]),
            canonical_evidence_bundle=dict(evidence_override["canonical_evidence_bundle"]),
            source_paths=as_mapping(evidence_override.get("source_paths")),
            canonical_bundle_path=Path(
                str(evidence_override.get("canonical_bundle_path") or CANONICAL_BUNDLE_DIR)
            ),
        )
    return build_current_report()


def build_current_report() -> dict[str, Any]:
    canonical_evidence_bundle = canonical_bundle.build_current_report()
    target_area_demo_handoff_report = load_target_area_demo_handoff_report()
    probe_metrics_report_report = load_probe_metrics_report(canonical_evidence_bundle)
    return assemble_report(
        target_area_demo_handoff_report=target_area_demo_handoff_report,
        probe_metrics_report=probe_metrics_report_report,
        canonical_evidence_bundle=canonical_evidence_bundle,
        source_paths=build_source_paths(
            target_area_demo_handoff_report=target_area_demo_handoff_report,
            probe_metrics_report=probe_metrics_report_report,
            canonical_evidence_bundle=canonical_evidence_bundle,
        ),
        canonical_bundle_path=CANONICAL_BUNDLE_DIR,
    )


def assemble_report(
    *,
    target_area_demo_handoff_report: dict[str, Any],
    probe_metrics_report: dict[str, Any],
    canonical_evidence_bundle: dict[str, Any],
    source_paths: dict[str, Any] | None = None,
    canonical_bundle_path: Path = CANONICAL_BUNDLE_DIR,
) -> dict[str, Any]:
    source_paths = source_paths or {}
    section_provenance_profile = build_section_provenance_profile(
        target_area_demo_handoff_report=target_area_demo_handoff_report,
        probe_metrics_report=probe_metrics_report,
        canonical_evidence_bundle=canonical_evidence_bundle,
        source_paths=source_paths,
    )
    bundle_status, bundle_blockers = derive_bundle_status(section_provenance_profile)
    claim_boundaries = claim_boundaries_from(
        target_area_demo_handoff_report=target_area_demo_handoff_report,
        canonical_evidence_bundle=canonical_evidence_bundle,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": str(
            target_area_demo_handoff_report.get("target_area_id")
            or canonical_evidence_bundle.get("pilot_id")
            or DEFAULT_PILOT_ID
        ),
        "run_id": str(
            target_area_demo_handoff_report.get("run_id")
            or canonical_evidence_bundle.get("run_id")
            or DEFAULT_RUN_ID
        ),
        "canonical_bundle_path": str(canonical_bundle_path),
        "bundle_status": bundle_status,
        "bundle_provenance_status": bundle_status,
        "bundle_summary": {
            "status": bundle_status,
            "summary": summarize_bundle(bundle_status, target_area_demo_handoff_report, probe_metrics_report),
            "blockers": bundle_blockers,
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "target_area_demo_handoff_report": target_area_demo_handoff_report,
        "probe_metrics_report": probe_metrics_report,
        "canonical_evidence_bundle": canonical_evidence_bundle,
        "claim_boundaries": claim_boundaries,
        "section_provenance_profile": section_provenance_profile,
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
    section_provenance_profile = [
        {
            "section": "target_area_demo_handoff_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "probe_metrics_report",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
        {
            "section": "canonical_evidence_bundle",
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        },
    ]
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
        "target_area_demo_handoff_report": {
            "schema_version": target_handoff.SCHEMA_VERSION,
            "bundle_status": "blocked_missing_inputs",
            "status": "blocked_missing_inputs",
        },
        "probe_metrics_report": {
            "schema_version": probe_metrics_report.SCHEMA_VERSION,
            "report_status": "blocked_missing_inputs",
            "status": "blocked_missing_inputs",
        },
        "canonical_evidence_bundle": {
            "schema_version": canonical_bundle.SCHEMA_VERSION,
            "bundle_status": "blocked_missing_inputs",
            "status": "blocked_missing_inputs",
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "section_provenance_profile": section_provenance_profile,
        "source_paths": {},
        "evidence_sources": evidence_sources({}),
        "missing_inputs": list(missing_inputs),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Evidence Bundle",
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
        for key in ("measured", "fixture_backed", "unavailable", "blocked_missing_inputs"):
            if key in section_counts:
                lines.append(f"    {key}: {section_counts[key]}")
    lines.extend(
        [
            "target_area_demo_handoff_report:",
            f"  bundle_status: {report['target_area_demo_handoff_report'].get('bundle_status', 'unknown')}",
            f"  status: {report['target_area_demo_handoff_report'].get('status', 'unknown')}",
            "probe_metrics_report:",
            f"  report_status: {report['probe_metrics_report'].get('report_status', 'unknown')}",
            f"  metrics_contract_status: {report['probe_metrics_report'].get('metrics_contract_status', 'unknown')}",
            "canonical_evidence_bundle:",
            f"  bundle_status: {report['canonical_evidence_bundle'].get('bundle_status', 'unknown')}",
            f"  bundle_provenance_status: {report['canonical_evidence_bundle'].get('bundle_provenance_status', 'unknown')}",
            "claim_boundaries:",
            f"  operational_claims_allowed: {report['claim_boundaries'].get('operational_claims_allowed', False)}",
            f"  physical_probability_claims_allowed: {report['claim_boundaries'].get('physical_probability_claims_allowed', False)}",
            f"  annual_frequency_claims_allowed: {report['claim_boundaries'].get('annual_frequency_claims_allowed', False)}",
            f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries'].get('risk_exposure_vulnerability_claims_allowed', False)}",
            f"  scale_up_authorized: {report['claim_boundaries'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['claim_boundaries'].get('distributed_execution_authorized', False)}",
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


def build_source_paths(
    *,
    target_area_demo_handoff_report: dict[str, Any],
    probe_metrics_report: dict[str, Any],
    canonical_evidence_bundle: dict[str, Any],
) -> dict[str, Any]:
    return {
        "target_area_demo_handoff_report_path": str(TARGET_AREA_HANDOFF_REPORT_PATH),
        "probe_metrics_report_path": str(PROBE_METRICS_REPORT_PATH),
        "canonical_bundle_path": str(CANONICAL_BUNDLE_DIR),
        "target_area_demo_handoff_sources": target_area_demo_handoff_report.get("raw_inputs", {}),
        "probe_metrics_report_sources": probe_metrics_report.get("source_paths", {}),
        "canonical_bundle_sources": canonical_evidence_bundle.get("source_paths", {}),
    }


def build_section_provenance_profile(
    *,
    target_area_demo_handoff_report: dict[str, Any],
    probe_metrics_report: dict[str, Any],
    canonical_evidence_bundle: dict[str, Any],
    source_paths: dict[str, Any],
) -> list[dict[str, Any]]:
    sections = [
        (
            "target_area_demo_handoff_report",
            target_area_demo_handoff_report,
            [source_paths.get("target_area_demo_handoff_report_path")],
        ),
        (
            "probe_metrics_report",
            probe_metrics_report,
            [source_paths.get("probe_metrics_report_path")],
        ),
        (
            "canonical_evidence_bundle",
            canonical_evidence_bundle,
            [source_paths.get("canonical_bundle_path")],
        ),
    ]
    profile: list[dict[str, Any]] = []
    for section_name, section_payload, section_paths in sections:
        normalized_paths = [path for path in section_paths if isinstance(path, str) and path]
        profile.append(
            {
                "section": section_name,
                "status": section_status(section_name, section_payload),
                "evidence_type": classify_evidence_type(section_payload, normalized_paths),
                "source_paths": normalized_paths,
            }
        )
    return profile


def section_status(section_name: str, section_payload: dict[str, Any]) -> str:
    if section_name == "target_area_demo_handoff_report":
        status = str(section_payload.get("bundle_status") or section_payload.get("status") or "").strip()
    elif section_name == "probe_metrics_report":
        status = str(section_payload.get("report_status") or section_payload.get("status") or "").strip()
    elif section_name == "canonical_evidence_bundle":
        status = str(section_payload.get("bundle_status") or section_payload.get("status") or "").strip()
    else:
        status = str(section_payload.get("status") or "").strip()
    return status or "blocked_missing_inputs"


def classify_evidence_type(section_payload: dict[str, Any], source_paths: list[str]) -> str:
    status = str(section_payload.get("bundle_status") or section_payload.get("report_status") or section_payload.get("status") or "").strip()
    if status.startswith("blocked") or status == "missing":
        return "blocked"
    if status in {"template_only", "unavailable", "metadata_only", "not_provided"}:
        return "unavailable"
    if any(is_fixture_path(path) for path in source_paths):
        return "fixture_backed"
    return "measured"


def is_fixture_path(path: str) -> bool:
    candidate = Path(path)
    return "tests" in candidate.parts and "fixtures" in candidate.parts


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "measured": 0,
        "fixture_backed": 0,
        "unavailable": 0,
        "blocked_missing_inputs": 0,
    }
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type == "measured":
            counts["measured"] += 1
        elif evidence_type == "fixture_backed":
            counts["fixture_backed"] += 1
        elif evidence_type == "unavailable":
            counts["unavailable"] += 1
        else:
            counts["blocked_missing_inputs"] += 1
    return counts


def derive_bundle_status(profile: list[dict[str, Any]]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    has_measured = any(section.get("evidence_type") == "measured" for section in profile)
    has_fixture_backed = any(section.get("evidence_type") == "fixture_backed" for section in profile)
    has_unavailable = any(section.get("evidence_type") == "unavailable" for section in profile)
    has_blocked = any(section.get("evidence_type") == "blocked" for section in profile)
    if has_blocked and not has_measured and not has_fixture_backed and not has_unavailable:
        blockers.extend(section["section"] for section in profile)
        return "blocked_missing_inputs", blockers
    if has_blocked:
        blockers.extend(section["section"] for section in profile if section.get("evidence_type") == "blocked")
    if has_fixture_backed and not has_measured and not has_unavailable:
        return "fixture_backed", blockers
    if has_unavailable or has_blocked:
        return "mixed_provenance", blockers
    return "measured", blockers


def summarize_bundle(
    bundle_status: str,
    target_area_demo_handoff_report: dict[str, Any],
    probe_metrics_report_payload: dict[str, Any],
) -> str:
    handoff_status = str(target_area_demo_handoff_report.get("bundle_status") or "unknown")
    metrics_status = str(
        probe_metrics_report_payload.get("report_status")
        or probe_metrics_report_payload.get("metrics_contract_status")
        or "unknown"
    )
    if bundle_status == "blocked_missing_inputs":
        return "Target-area evidence is blocked because one or more required source sections are absent."
    if bundle_status == "measured":
        return (
            "Target-area Balfrin evidence is measured end-to-end and bundled with claim boundaries intact."
        )
    return (
        "Target-area Balfrin evidence combines a template-only handoff, a blocked probe-metrics report, "
        f"and the measured canonical bundle; handoff={handoff_status}, metrics={metrics_status}, "
        "claim boundaries remain false."
    )


def claim_boundaries_from(
    *,
    target_area_demo_handoff_report: dict[str, Any],
    canonical_evidence_bundle: dict[str, Any],
) -> dict[str, Any]:
    boundaries = target_area_demo_handoff_report.get("claim_boundary")
    if isinstance(boundaries, dict):
        return dict(boundaries)
    boundaries = canonical_evidence_bundle.get("claim_boundaries")
    if isinstance(boundaries, dict):
        return dict(boundaries)
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def load_target_area_demo_handoff_report() -> dict[str, Any]:
    report = load_json(TARGET_AREA_HANDOFF_REPORT_PATH)
    if report is not None:
        return report
    with tempfile.TemporaryDirectory(prefix="balfrin_target_area_handoff_") as tmpdir:
        return target_handoff.build_report(target_handoff.DEFAULT_CONTRACT, Path(tmpdir) / "balfrin_target_area_demo_v1")


def load_probe_metrics_report(canonical_evidence_bundle: dict[str, Any]) -> dict[str, Any]:
    report = load_json(PROBE_METRICS_REPORT_PATH)
    if report is not None:
        return report
    nested_probe_metrics = canonical_evidence_bundle.get("probe_metrics")
    if isinstance(nested_probe_metrics, dict):
        return probe_metrics_report.build_report(nested_probe_metrics)
    return probe_metrics_report.build_report({})


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def evidence_sources(source_paths: dict[str, Any]) -> list[str]:
    sources = [
        "scripts/generate_balfrin_target_area_demo_handoff.py",
        "scripts/summarize_balfrin_probe_metrics_report.py",
        "scripts/summarize_balfrin_evidence_bundle.py",
        "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_bundle_report.json",
        "validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1/balfrin_probe_metrics_report_v1.json",
        "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/balfrin_evidence_bundle_v1.json",
    ]
    if source_paths:
        sources.append("validation/private/tschamut_public_pilot/balfrin_target_area_evidence_bundle_v1")
    return sources


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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
