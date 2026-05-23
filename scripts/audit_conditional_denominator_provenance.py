#!/usr/bin/env python3
"""Audit denominator provenance for local conditional hazard layers.

The audit is read-only. It checks existing hazard manifests for the trajectory
and sample counts, conditioning fields, denominator semantics, and explicit
non-annual/non-physical claim boundaries needed to interpret conditional reach
and threshold layers without upgrading them to physical probability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT
    / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
)
SCHEMA_VERSION = "conditional_denominator_provenance_audit_v1"


class ConditionalDenominatorAuditError(ValueError):
    """User-facing denominator audit error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.manifest)
    except ConditionalDenominatorAuditError as exc:
        print(f"conditional denominator audit error: {exc}")
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["audit_status"] == "complete" else 2


def build_report(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise ConditionalDenominatorAuditError(f"manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    inputs = manifest.get("inputs") or {}
    trajectory_count = inputs.get("trajectory_count")
    trajectory_sample_count = inputs.get("trajectory_sample_count")
    input_failures = []
    if not isinstance(trajectory_count, int) or trajectory_count <= 0:
        input_failures.append("inputs.trajectory_count must be a positive integer")
    if not isinstance(trajectory_sample_count, int) or trajectory_sample_count <= 0:
        input_failures.append("inputs.trajectory_sample_count must be a positive integer")

    layer_rows = [audit_layer_semantics(row) for row in manifest.get("layer_semantics") or []]
    denominator_layers = [row for row in layer_rows if row["denominator_required"]]
    missing_denominator_layers = [
        row["layer_name"]
        for row in denominator_layers
        if not row["denominator_present"] or not row["conditioning_present"] or row["annualized"] is not False
    ]
    conditional_execution = manifest.get("conditional_execution") or {}
    curve_summary = manifest.get("conditional_intensity_exceedance_curves") or {}
    claim_boundary = {
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "operational_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "source_frequency_inferred": False,
        "balfrin_required": False,
    }
    boundary_failures = []
    if conditional_execution.get("annualized") is not False:
        boundary_failures.append("conditional_execution.annualized must be false")
    if conditional_execution.get("physical_probability") is not False:
        boundary_failures.append("conditional_execution.physical_probability must be false")
    if conditional_execution.get("risk_or_exposure") is not False:
        boundary_failures.append("conditional_execution.risk_or_exposure must be false")
    if curve_summary.get("enabled") and curve_summary.get("annualized") is not False:
        boundary_failures.append("conditional_intensity_exceedance_curves.annualized must be false")

    missing_evidence = [*input_failures, *boundary_failures]
    missing_evidence.extend(
        f"layer_semantics[{layer}] is missing denominator, conditioning, or annualized=false"
        for layer in missing_denominator_layers
    )
    audit_status = "complete" if not missing_evidence and denominator_layers else "blocked_missing_denominator_evidence"

    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_path": str(manifest_path),
        "case_id": manifest.get("case_id"),
        "audit_status": audit_status,
        "trajectory_denominator_evidence": {
            "trajectory_count": trajectory_count,
            "trajectory_sample_count": trajectory_sample_count,
            "status": "present" if not input_failures else "missing_or_invalid",
        },
        "conditional_curve_summary": {
            "enabled": bool(curve_summary.get("enabled")),
            "mode": curve_summary.get("mode"),
            "row_count": curve_summary.get("row_count"),
            "csv_table_written": curve_summary.get("csv_table_written"),
            "probability_modes": list(curve_summary.get("probability_modes") or []),
            "annualized": curve_summary.get("annualized"),
        },
        "denominator_layer_count": len(denominator_layers),
        "missing_denominator_layers": missing_denominator_layers,
        "layer_denominator_audit": layer_rows,
        "claim_boundaries": claim_boundary,
        "missing_evidence": missing_evidence,
        "next_local_follow_up": next_follow_up(audit_status, missing_evidence),
    }


def audit_layer_semantics(row: dict[str, Any]) -> dict[str, Any]:
    layer_name = str(row.get("layer_name") or "")
    denominator_required = is_conditional_denominator_layer(layer_name)
    denominator = row.get("denominator")
    conditioned_on = row.get("conditioned_on")
    return {
        "layer_name": layer_name,
        "denominator_required": denominator_required,
        "denominator_present": bool(denominator),
        "denominator": denominator,
        "conditioning_present": isinstance(conditioned_on, list) and bool(conditioned_on),
        "conditioned_on": conditioned_on if isinstance(conditioned_on, list) else [],
        "weighted": bool(row.get("weighted")),
        "annualized": row.get("annualized"),
        "physical_probability_claim": False,
    }


def is_conditional_denominator_layer(layer_name: str) -> bool:
    if layer_name in {"reach_probability", "weighted_reach_probability"}:
        return True
    return "exceedance" in layer_name


def next_follow_up(audit_status: str, missing_evidence: list[str]) -> str:
    if audit_status == "complete":
        return "Use this denominator audit before interpreting conditional reach or exceedance layers; next local task is trajectory-to-deposition traceability."
    return "Patch build_hazard_layers.py to emit the missing denominator provenance fields before using this manifest for scientific interpretation: " + "; ".join(missing_evidence)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"audit_status: {report['audit_status']}",
        f"case_id: {report['case_id']}",
        f"manifest_path: {report['manifest_path']}",
        "trajectory_denominator_evidence:",
        f"  trajectory_count: {report['trajectory_denominator_evidence']['trajectory_count']}",
        f"  trajectory_sample_count: {report['trajectory_denominator_evidence']['trajectory_sample_count']}",
        f"  status: {report['trajectory_denominator_evidence']['status']}",
        f"denominator_layer_count: {report['denominator_layer_count']}",
        f"missing_denominator_layers: {', '.join(report['missing_denominator_layers']) or 'none'}",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append(f"next_local_follow_up: {report['next_local_follow_up']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
