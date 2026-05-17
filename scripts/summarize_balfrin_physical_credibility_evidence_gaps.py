#!/usr/bin/env python3
"""Summarize Balfrin demo evidence against the physical-credibility boundary.

This helper is read-only. It composes the measured Balfrin evidence bundle,
the validation/calibration gap assessment, the physical-credibility evidence
requirements, and the observed runout/deposition intake contract into a
Balfrin-specific evidence-gap report.

The report keeps the distinction explicit between:

- measured Balfrin demo evidence;
- diagnostic/reproducibility evidence that does not establish physical
  credibility;
- missing physical-credibility, validation, calibration, and frequency
  evidence.

It does not calibrate, fit, or authorize annual-frequency, physical
probability, risk, exposure, vulnerability, or operational claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import assess_validation_calibration_evidence_gaps as validation_gaps
from scripts import map_physical_credibility_evidence_requirements as physical_requirements
from scripts import summarize_balfrin_evidence_bundle as balfrin_bundle
from scripts import summarize_observed_runout_deposition_intake_contract as observed_intake


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_physical_credibility_evidence_gaps_v1"

DIAGNOSTIC_ONLY_REQUIREMENTS = {
    "observed_runout_deposition",
    "release_zone_evidence",
    "independent_holdout_validation",
}

MEASURED_BUNDLE_SECTIONS = {"single_job_execution_summary", "probe_metrics", "post_run_interpretation_gate_report", "gis_cog_readiness_report"}


class BalfrinPhysicalCredibilityEvidenceGapsError(ValueError):
    """User-facing evidence-gap report error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinPhysicalCredibilityEvidenceGapsError as exc:
        print(f"balfrin physical-credibility evidence gap error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["balfrin_evidence_gap_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinPhysicalCredibilityEvidenceGapsError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinPhysicalCredibilityEvidenceGapsError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    bundle_report = section_or_build(evidence_override, "balfrin_bundle_report", balfrin_bundle.build_report)
    if bundle_report.get("bundle_status") == "blocked_missing_inputs":
        return blocked_report(list(bundle_report.get("missing_inputs", [])), reason="required evidence inputs are missing")

    validation_report = section_or_build(evidence_override, "validation_calibration_report", validation_gaps.build_report)
    physical_report = section_or_build(
        evidence_override,
        "physical_requirements_report",
        physical_requirements.build_report,
    )
    observed_report = section_or_build(
        evidence_override,
        "observed_runout_intake_report",
        observed_intake.build_report,
    )

    requirement_matrix = build_requirement_matrix(
        physical_report=physical_report,
        bundle_report=bundle_report,
        validation_report=validation_report,
        observed_report=observed_report,
    )
    diagnostic_only_requirements = [row for row in requirement_matrix if row["balfrin_evidence_state"] == "diagnostic_reproducibility_only"]
    missing_requirements = [row for row in requirement_matrix if row["balfrin_evidence_state"] == "missing_physical_evidence"]

    return {
        "schema_version": SCHEMA_VERSION,
        "balfrin_evidence_gap_status": "measured_diagnostic_only",
        "balfrin_demo_evidence_status": bundle_report.get("bundle_status", "unknown"),
        "physical_credibility_state": derive_physical_credibility_state(bundle_report=bundle_report, validation_report=validation_report),
        "validation_calibration_state": {
            "physical_credibility_status": validation_report.get("physical_credibility_status", "unknown"),
            "calibration_status": validation_report.get("calibration_status", "unknown"),
            "validation_status": validation_report.get("validation_status", "unknown"),
            "observed_runout_deposition_intake_status": observed_report.get("observed_runout_deposition_intake_status", "unknown"),
            "physical_credibility_requirements_status": physical_report.get(
                "physical_credibility_requirements_status", "unknown"
            ),
        },
        "bundle_summary": summarize_bundle(bundle_report),
        "requirement_matrix": requirement_matrix,
        "diagnostic_reproducibility_only_requirements": diagnostic_only_requirements,
        "missing_physical_requirements": missing_requirements,
        "diagnostic_reproducibility_evidence": diagnostic_reproducibility_evidence(bundle_report),
        "claim_boundaries": claim_boundaries(validation_report),
        "blocked_reason": None,
        "missing_inputs": [],
        "current_evidence_sources": {
            "balfrin_bundle": bundle_report.get("evidence_sources", []),
            "validation_calibration": validation_report.get("current_evidence_summary", []),
            "physical_requirements": physical_report.get("current_evidence_summary", []),
            "observed_runout_deposition_intake": observed_report.get("current_state_summary", []),
        },
    }


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "balfrin_evidence_gap_status": "blocked_missing_inputs",
        "balfrin_demo_evidence_status": "blocked_missing_inputs",
        "physical_credibility_state": "blocked_missing_inputs",
        "validation_calibration_state": {
            "physical_credibility_status": "blocked_missing_inputs",
            "calibration_status": "blocked_missing_inputs",
            "validation_status": "blocked_missing_inputs",
            "observed_runout_deposition_intake_status": "blocked_missing_inputs",
            "physical_credibility_requirements_status": "blocked_missing_inputs",
        },
        "bundle_summary": {
            "bundle_status": "blocked_missing_inputs",
            "bundle_provenance_status": "blocked_missing_inputs",
            "section_counts": {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 0},
            "summary": reason,
        },
        "requirement_matrix": [],
        "diagnostic_reproducibility_only_requirements": [],
        "missing_physical_requirements": [],
        "diagnostic_reproducibility_evidence": [],
        "claim_boundaries": claim_boundaries(),
        "blocked_reason": reason,
        "missing_inputs": sorted(set(missing_inputs)),
        "current_evidence_sources": {
            "balfrin_bundle": [],
            "validation_calibration": [],
            "physical_requirements": [],
            "observed_runout_deposition_intake": [],
        },
    }


def summarize_bundle(bundle_report: dict[str, Any]) -> dict[str, Any]:
    bundle_summary = dict(bundle_report.get("bundle_summary") or {})
    section_counts = dict(bundle_summary.get("section_counts") or {})
    return {
        "bundle_status": bundle_report.get("bundle_status", "unknown"),
        "bundle_provenance_status": bundle_report.get("bundle_provenance_status", bundle_report.get("bundle_status", "unknown")),
        "section_counts": section_counts,
        "summary": bundle_summary.get("summary", ""),
        "physical_credibility_check_status": dict(bundle_report.get("post_run_interpretation_gate_report") or {})
        .get("physical_credibility_check", {})
        .get("status", "unknown"),
    }


def build_requirement_matrix(
    *,
    physical_report: dict[str, Any],
    bundle_report: dict[str, Any],
    validation_report: dict[str, Any],  # noqa: ARG001 - kept for future report expansion.
    observed_report: dict[str, Any],
) -> list[dict[str, Any]]:
    categories = {entry["category"]: entry for entry in physical_report.get("evidence_requirement_categories", [])}
    matrix: list[dict[str, Any]] = []
    for requirement_key in (
        "observed_runout_deposition",
        "release_zone_evidence",
        "independent_holdout_validation",
        "calibration_data_and_objective_functions",
        "multi_site_transfer_evidence",
        "block_size_and_block_population_evidence",
        "source_frequency_and_temporal_frequency_evidence",
    ):
        category = categories.get(requirement_key, {})
        balfrin_state = (
            "diagnostic_reproducibility_only"
            if requirement_key in DIAGNOSTIC_ONLY_REQUIREMENTS
            else "missing_physical_evidence"
        )
        row = {
            "requirement_key": requirement_key,
            "requirement_label": requirement_label(requirement_key),
            "current_repo_evidence_status": category.get("current_repo_evidence_status", "unknown"),
            "balfrin_evidence_state": balfrin_state,
            "current_repo_evidence_sources": category.get("current_repo_evidence_sources", []),
            "future_acquisition_classes": category.get("future_acquisition_classes", []),
            "why_it_matters": category.get("why_it_matters", ""),
            "diagnostic_or_reproducibility_evidence": diagnostic_reproducibility_evidence(bundle_report)
            if balfrin_state == "diagnostic_reproducibility_only"
            else [],
            "missing_physical_evidence": category.get("current_repo_gap", category.get("why_it_matters", "")),
            "observed_runout_deposition_intake_status": observed_report.get("observed_runout_deposition_intake_status", "unknown"),
        }
        matrix.append(row)
    return matrix


def requirement_label(requirement_key: str) -> str:
    labels = {
        "observed_runout_deposition": "Observed runout/deposition benchmark",
        "release_zone_evidence": "Release-zone provenance",
        "independent_holdout_validation": "Independent holdout validation",
        "calibration_data_and_objective_functions": "Calibration data and objective functions",
        "multi_site_transfer_evidence": "Multi-site transfer evidence",
        "block_size_and_block_population_evidence": "Block-size and block-population evidence",
        "source_frequency_and_temporal_frequency_evidence": "Source-frequency and temporal-frequency evidence",
    }
    return labels.get(requirement_key, requirement_key)


def diagnostic_reproducibility_evidence(bundle_report: dict[str, Any]) -> list[dict[str, Any]]:
    profile = list(bundle_report.get("section_provenance_profile") or [])
    return [
        {
            "section": item.get("section", "unknown"),
            "status": item.get("status", "unknown"),
            "evidence_type": item.get("evidence_type", "unknown"),
        }
        for item in profile
        if item.get("section") in MEASURED_BUNDLE_SECTIONS and item.get("evidence_type") in {"measured", "fixture_backed"}
    ]


def derive_physical_credibility_state(
    *,
    bundle_report: dict[str, Any],
    validation_report: dict[str, Any],
) -> str:
    bundle_status = str(bundle_report.get("bundle_status") or "")
    physical_status = str(validation_report.get("physical_credibility_status") or "")
    if bundle_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if physical_status in {"not_established", "missing", "partial"}:
        return "no_physical_evidence"
    return "physical_credibility_not_established"


def claim_boundaries(validation_report: dict[str, Any] | None = None) -> dict[str, bool]:
    boundaries = dict((validation_report or {}).get("claim_boundaries") or {})
    if not boundaries:
        boundaries = {
            "annual_frequency_claims_allowed": False,
            "distributed_execution_authorized": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
        }
    boundaries.setdefault("annual_frequency_claims_allowed", False)
    boundaries.setdefault("distributed_execution_authorized", False)
    boundaries.setdefault("operational_claims_allowed", False)
    boundaries.setdefault("physical_probability_claims_allowed", False)
    boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    boundaries.setdefault("scale_up_authorized", False)
    return boundaries


def section_or_build(
    evidence_override: dict[str, Any] | None,
    key: str,
    builder,
) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get(key), dict):
        return dict(evidence_override[key])
    return builder()


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Physical-Credibility Evidence Gaps",
        f"schema_version: {report['schema_version']}",
        f"balfrin_evidence_gap_status: {report['balfrin_evidence_gap_status']}",
        f"balfrin_demo_evidence_status: {report['balfrin_demo_evidence_status']}",
        f"physical_credibility_state: {report['physical_credibility_state']}",
        "validation_calibration_state:",
        f"  physical_credibility_status: {report['validation_calibration_state'].get('physical_credibility_status', 'unknown')}",
        f"  calibration_status: {report['validation_calibration_state'].get('calibration_status', 'unknown')}",
        f"  validation_status: {report['validation_calibration_state'].get('validation_status', 'unknown')}",
        f"  observed_runout_deposition_intake_status: {report['validation_calibration_state'].get('observed_runout_deposition_intake_status', 'unknown')}",
        f"  physical_credibility_requirements_status: {report['validation_calibration_state'].get('physical_credibility_requirements_status', 'unknown')}",
        "bundle_summary:",
        f"  bundle_status: {report['bundle_summary'].get('bundle_status', 'unknown')}",
        f"  physical_credibility_check_status: {report['bundle_summary'].get('physical_credibility_check_status', 'unknown')}",
        f"  section_counts: {report['bundle_summary'].get('section_counts', {})}",
        "diagnostic_reproducibility_only_requirements:",
    ]
    for item in report["diagnostic_reproducibility_only_requirements"]:
        lines.append(
            f"- {item['requirement_key']}: {item['balfrin_evidence_state']} | {item['current_repo_evidence_status']}"
        )
    lines.append("missing_physical_requirements:")
    for item in report["missing_physical_requirements"]:
        lines.append(
            f"- {item['requirement_key']}: {item['balfrin_evidence_state']} | {item['current_repo_evidence_status']}"
        )
    lines.append("requirement_matrix:")
    for item in report["requirement_matrix"]:
        lines.append(
            f"- {item['requirement_key']}: {item['balfrin_evidence_state']} | "
            f"current_repo={item['current_repo_evidence_status']}"
        )
    lines.append("diagnostic_reproducibility_evidence:")
    for item in report["diagnostic_reproducibility_evidence"]:
        lines.append(f"- {item['section']}: {item['evidence_type']} | {item['status']}")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        for item in report["missing_inputs"]:
            lines.append(f"- {item}")
    if report.get("blocked_reason"):
        lines.append(f"blocked_reason: {report['blocked_reason']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
