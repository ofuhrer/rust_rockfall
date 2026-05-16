#!/usr/bin/env python3
"""Summarize whether the measured Balfrin output tier is sufficient.

This helper is read-only. It consumes the existing Balfrin probe metrics
collector output, reports the measured output families, file counts, bytes,
and conditional-curve availability, and classifies whether the measured
``rebuildable_reduced_output`` tier is sufficient, insufficient, or blocked by
missing measured evidence.
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
SCHEMA_VERSION = "balfrin_output_tier_audit_v1"
OUTPUT_TIER = "rebuildable_reduced_output"
REQUIRED_FAMILY_COUNTS = {
    "map_package_manifest": 1,
    "pilot_gis_package_manifest": 1,
    "trajectory_chunk_manifest": 1,
    "reducer_chunk_manifest": 1,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Run root produced by submit_balfrin_probe.py.",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional explicit evidence JSON for tests or alternate snapshots.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional JSON path to write the audit.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        help="Optional markdown path to write the audit.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)
    if args.run_root is None and args.evidence_json is None:
        parser.error("one of --run-root or --evidence-json is required")
    return args


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_evidence(args: argparse.Namespace) -> dict[str, Any]:
    if args.evidence_json is not None:
        payload = _load_json(args.evidence_json)
        if payload is None:
            raise ValueError(f"evidence JSON is missing or invalid: {args.evidence_json}")
        return payload
    assert args.run_root is not None
    return probe_metrics.collect_run_metrics(args.run_root)


def _family_counts(metrics: dict[str, Any]) -> dict[str, int]:
    counts = metrics.get("reduced_output_family_counts")
    if not isinstance(counts, dict):
        return {}
    result: dict[str, int] = {}
    for key, value in counts.items():
        if isinstance(key, str):
            safe_value = _safe_int(value)
            if safe_value is not None:
                result[key] = safe_value
    return result


def _missing_required_families(counts: dict[str, int]) -> list[str]:
    missing: list[str] = []
    for family, expected_count in REQUIRED_FAMILY_COUNTS.items():
        if counts.get(family, 0) < expected_count:
            missing.append(family)
    return missing


def _curve_availability(metrics: dict[str, Any]) -> dict[str, Any]:
    row_count = _safe_int(metrics.get("conditional_curve_row_count"))
    return {
        "available": row_count is not None,
        "row_count": row_count,
    }


def _output_sizes(metrics: dict[str, Any]) -> dict[str, dict[str, int | None]]:
    return {
        "validation_output": {
            "file_count": _safe_int(metrics.get("validation_output_file_count")),
            "bytes": _safe_int(metrics.get("validation_output_bytes")),
        },
        "hazard_output": {
            "file_count": _safe_int(metrics.get("hazard_output_file_count")),
            "bytes": _safe_int(metrics.get("hazard_output_bytes")),
        },
        "output_root": {
            "file_count": _safe_int(metrics.get("output_file_count")),
            "bytes": _safe_int(metrics.get("output_bytes")),
        },
    }


def _build_omitted_implications(
    *,
    family_counts: dict[str, int],
    missing_families: list[str],
    curve_available: bool,
    metrics_complete: bool,
) -> list[str]:
    implications: list[str] = []
    if not metrics_complete:
        implications.append(
            "The run cannot be judged on output-tier sufficiency because the measured metrics contract is incomplete."
        )
        return implications

    if missing_families:
        implications.append(
            "Required measured output families are omitted, so the tier cannot be treated as rebuildable."
        )
        implications.extend(
            f"{family} is below the minimum measured count of {REQUIRED_FAMILY_COUNTS[family]}"
            for family in missing_families
        )
    else:
        implications.append(
            "The measured reduced tier preserves the required manifest and chunk families needed for replay and audit."
        )
        extra_families = sorted(set(family_counts) - set(REQUIRED_FAMILY_COUNTS))
        if extra_families:
            implications.append(
                "The remaining measured families are advisory only and do not change rebuildability."
            )
    if not curve_available:
        implications.append(
            "Conditional-curve output is unavailable, so the post-run curve audit remains incomplete."
        )
    else:
        implications.append(
            "Conditional-curve rows are available, so the curve audit can be used as measured evidence."
        )
    implications.append(
        "This audit does not reclassify summary_only as rebuildable; only the measured rebuildable_reduced_output tier is considered here."
    )
    return implications


def classify_rebuildability(
    *,
    metrics: dict[str, Any],
    family_counts: dict[str, int],
    curve_available: bool,
) -> tuple[str, str, list[str]]:
    metrics_status = str(metrics.get("metrics_contract_status") or "")
    missing_metrics = [str(item) for item in metrics.get("metrics_contract_missing_metrics", []) if isinstance(item, str)]

    if metrics_status != "complete":
        return (
            "blocked_missing_measured_output",
            "blocked_missing_measured_output",
            missing_metrics or ["metrics_contract_status"],
        )

    missing_families = _missing_required_families(family_counts)
    missing_reasons = list(missing_families)
    if not curve_available:
        missing_reasons.append("conditional_curve_row_count")

    if missing_reasons:
        return "insufficient", "rebuildable_reduced_output_insufficient", missing_reasons

    return "sufficient", "rebuildable_reduced_output", []


def build_report(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics = dict(evidence or {})
    family_counts = _family_counts(metrics)
    curve = _curve_availability(metrics)
    audit_status, rebuildability_classification, blockers = classify_rebuildability(
        metrics=metrics,
        family_counts=family_counts,
        curve_available=bool(curve["available"]),
    )
    missing_metrics = [
        str(item)
        for item in metrics.get("metrics_contract_missing_metrics", [])
        if isinstance(item, str)
    ]
    omitted_implications = _build_omitted_implications(
        family_counts=family_counts,
        missing_families=_missing_required_families(family_counts),
        curve_available=bool(curve["available"]),
        metrics_complete=metrics.get("metrics_contract_status") == "complete",
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "audit_status": "measured" if audit_status != "blocked_missing_measured_output" else "blocked_missing_inputs",
        "output_tier": OUTPUT_TIER,
        "rebuildability_status": audit_status,
        "rebuildability_classification": rebuildability_classification,
        "blocked_reasons": blockers,
        "metrics_contract_status": metrics.get("metrics_contract_status"),
        "metrics_contract_missing_metrics": missing_metrics,
        "required_family_counts": dict(REQUIRED_FAMILY_COUNTS),
        "measured_family_counts": family_counts,
        "required_family_counts_status": {
            family: family_counts.get(family, 0) >= expected
            for family, expected in REQUIRED_FAMILY_COUNTS.items()
        },
        "file_counts": _output_sizes(metrics),
        "curve_availability": curve,
        "omitted_output_implications": omitted_implications,
        "source_paths": {
            "run_root": metrics.get("run_root"),
            "output_root": metrics.get("output_root"),
            "hazard_manifest_path": metrics.get("hazard_manifest_path"),
            "probe_metrics_path": metrics.get("probe_manifest_path"),
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
    }
    return report


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Output-Tier Audit",
        f"schema_version: {report['schema_version']}",
        f"output_tier: {report['output_tier']}",
        f"rebuildability_status: {report['rebuildability_status']}",
        f"rebuildability_classification: {report['rebuildability_classification']}",
        f"audit_status: {report['audit_status']}",
        "required_family_counts:",
    ]
    for family, count in report["required_family_counts"].items():
        measured = report["measured_family_counts"].get(family, 0)
        status = report["required_family_counts_status"].get(family, False)
        lines.append(f"  - {family}: required={count} measured={measured} status={status}")
    lines.extend(
        [
            "file_counts:",
            f"  validation_output: files={report['file_counts']['validation_output']['file_count']} bytes={report['file_counts']['validation_output']['bytes']}",
            f"  hazard_output: files={report['file_counts']['hazard_output']['file_count']} bytes={report['file_counts']['hazard_output']['bytes']}",
            f"  output_root: files={report['file_counts']['output_root']['file_count']} bytes={report['file_counts']['output_root']['bytes']}",
            "curve_availability:",
            f"  available: {report['curve_availability']['available']}",
            f"  row_count: {report['curve_availability']['row_count']}",
        ]
    )
    if report["blocked_reasons"]:
        lines.append("blocked_reasons:")
        lines.extend(f"  - {reason}" for reason in report["blocked_reasons"])
    lines.append("omitted_output_implications:")
    lines.extend(f"  - {item}" for item in report["omitted_output_implications"])
    lines.extend(
        [
            "claim_boundaries:",
            f"  operational_claims_allowed: {report['claim_boundaries']['operational_claims_allowed']}",
            f"  physical_probability_claims_allowed: {report['claim_boundaries']['physical_probability_claims_allowed']}",
            f"  annual_frequency_claims_allowed: {report['claim_boundaries']['annual_frequency_claims_allowed']}",
            f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries']['risk_exposure_vulnerability_claims_allowed']}",
            f"  scale_up_authorized: {report['claim_boundaries']['scale_up_authorized']}",
            f"  distributed_execution_authorized: {report['claim_boundaries']['distributed_execution_authorized']}",
        ]
    )
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    output_json: Path | None = None,
    output_md: Path | None = None,
) -> None:
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_md is not None:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_text_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        evidence = _load_evidence(args)
        report = build_report(evidence)
    except (OSError, ValueError) as exc:
        print(f"balfrin output-tier audit error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, output_json=args.output_json, output_md=args.output_md)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["rebuildability_status"] != "blocked_missing_measured_output" else 2


if __name__ == "__main__":
    raise SystemExit(main())
