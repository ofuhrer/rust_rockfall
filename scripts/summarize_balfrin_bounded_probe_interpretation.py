#!/usr/bin/env python3
"""Summarize a bounded Balfrin probe against the existing same-scale evidence.

This helper is read-only. It composes the bounded-next feasibility probe with
the measured same-scale uncertainty, stability frontier, and closure-gap
evidence, then classifies the interpretation as unchanged, improved, worsened,
or blocked. It keeps the closure status explicit and does not authorize
operational, probabilistic, or scale-up claims.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_bounded_probe_interpretation_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise BalfrinBoundedProbeInterpretationError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


FEASIBILITY = _load_module(
    "balfrin_bounded_probe_interpretation_feasibility",
    "summarize_bounded_next_ensemble_feasibility_probe.py",
)
SPATIAL = _load_module(
    "balfrin_bounded_probe_interpretation_spatial",
    "summarize_spatial_same_scale_uncertainty.py",
)
STABILITY = _load_module(
    "balfrin_bounded_probe_interpretation_stability",
    "summarize_same_scale_stability_frontier.py",
)
CLOSURE_GAP = _load_module(
    "balfrin_bounded_probe_interpretation_closure_gap",
    "summarize_tschamut_closure_gap_deltas.py",
)


class BalfrinBoundedProbeInterpretationError(ValueError):
    """User-facing bounded-probe interpretation error."""


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
    except BalfrinBoundedProbeInterpretationError as exc:
        print(f"balfrin bounded probe interpretation error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["probe_interpretation_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinBoundedProbeInterpretationError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinBoundedProbeInterpretationError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")
    if evidence_override and isinstance(evidence_override.get("bounded_probe_interpretation_report"), dict):
        return dict(evidence_override["bounded_probe_interpretation_report"])

    probe_report = section_or_build(
        evidence_override,
        "bounded_probe_report",
        FEASIBILITY.build_report,
    )
    same_scale_uncertainty_report = section_or_build(
        evidence_override,
        "same_scale_uncertainty_report",
        build_same_scale_uncertainty_report,
    )
    same_scale_stability_frontier_report = section_or_build(
        evidence_override,
        "same_scale_stability_frontier_report",
        STABILITY.build_report,
    )
    closure_gap_deltas_report = section_or_build(
        evidence_override,
        "closure_gap_deltas_report",
        CLOSURE_GAP.build_report,
    )

    report_status = classify_report_status(
        probe_report=probe_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        evidence_override=evidence_override,
    )
    if report_status == "blocked_missing_inputs":
        missing_inputs = collect_missing_inputs(
            evidence_override,
            probe_report=probe_report,
            same_scale_uncertainty_report=same_scale_uncertainty_report,
            same_scale_stability_frontier_report=same_scale_stability_frontier_report,
            closure_gap_deltas_report=closure_gap_deltas_report,
        )
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    closure_status = str(closure_gap_deltas_report.get("current_closure_status") or "unknown")
    closure_interpretation_status = str(closure_gap_deltas_report.get("current_interpretation_status") or "unknown")
    keep_closure_inconclusive = closure_status == "inconclusive" or closure_interpretation_status.startswith("inconclusive")

    comparison_summary = build_comparison_summary(
        report_status=report_status,
        probe_report=probe_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        keep_closure_inconclusive=keep_closure_inconclusive,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "probe_interpretation_status": report_status,
        "bounded_probe_status": probe_report.get("probe_status", "unknown"),
        "same_scale_uncertainty_status": same_scale_uncertainty_report.get("spatial_uncertainty_status", "unknown"),
        "same_scale_stability_frontier_status": same_scale_stability_frontier_report.get("frontier_status", "unknown"),
        "closure_gap_status": closure_gap_deltas_report.get("closure_gap_status", "unknown"),
        "closure_status": closure_status,
        "closure_interpretation_status": closure_interpretation_status,
        "keep_closure_inconclusive": keep_closure_inconclusive,
        "comparison_summary": comparison_summary,
        "probe_evidence": summarize_probe_evidence(probe_report),
        "same_scale_evidence": summarize_same_scale_evidence(
            same_scale_uncertainty_report,
            same_scale_stability_frontier_report,
            closure_gap_deltas_report,
        ),
        "claim_boundaries": claim_boundaries(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "blocked_reason": "none",
    }


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "probe_interpretation_status": "blocked_missing_inputs",
        "bounded_probe_status": "blocked_missing_inputs",
        "same_scale_uncertainty_status": "blocked_missing_inputs",
        "same_scale_stability_frontier_status": "blocked_missing_inputs",
        "closure_gap_status": "blocked_missing_inputs",
        "closure_status": "blocked_missing_inputs",
        "closure_interpretation_status": "blocked_missing_inputs",
        "keep_closure_inconclusive": True,
        "comparison_summary": {
            "status": "blocked_missing_inputs",
            "summary": "Measured Balfrin bounded-probe evidence is incomplete, so no interpretation delta can be stated.",
            "closure_status": "blocked_missing_inputs",
            "closure_criterion_changed": False,
        },
        "probe_evidence": {},
        "same_scale_evidence": {},
        "claim_boundaries": claim_boundaries(),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "missing_inputs": missing_inputs,
        "blocked_reason": reason,
    }


def classify_report_status(
    *,
    probe_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    evidence_override: dict[str, Any] | None,
) -> str:
    explicit_status = str((evidence_override or {}).get("probe_interpretation_status") or "").strip()
    if explicit_status in {"unchanged", "improved", "worsened", "blocked_missing_inputs"}:
        return explicit_status
    if evidence_override and str(evidence_override.get("comparison_status") or "").strip() in {
        "unchanged",
        "improved",
        "worsened",
        "blocked_missing_inputs",
    }:
        return str(evidence_override["comparison_status"])

    statuses = [
        str(probe_report.get("probe_status") or ""),
        str(same_scale_uncertainty_report.get("spatial_uncertainty_status") or ""),
        str(same_scale_stability_frontier_report.get("frontier_status") or ""),
        str(closure_gap_deltas_report.get("closure_gap_status") or ""),
    ]
    if any(status.startswith("blocked") or status == "missing" for status in statuses):
        return "blocked_missing_inputs"

    closure_status = str(closure_gap_deltas_report.get("current_closure_status") or "")
    closure_interpretation_status = str(closure_gap_deltas_report.get("current_interpretation_status") or "")
    if closure_status in {"measured", "accepted", "closed"}:
        return "improved"
    if closure_interpretation_status in {"measured_conditional_diagnostic", "accepted_conditional_diagnostic"}:
        return "improved"

    probe_status = str(probe_report.get("probe_status") or "")
    if probe_status.startswith("blocked") or probe_status == "missing":
        return "worsened"
    return "unchanged"


def build_comparison_summary(
    *,
    report_status: str,
    probe_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    keep_closure_inconclusive: bool,
) -> dict[str, Any]:
    closure_status = str(closure_gap_deltas_report.get("current_closure_status") or "unknown")
    closure_interpretation_status = str(closure_gap_deltas_report.get("current_interpretation_status") or "unknown")
    closure_criterion_changed = report_status == "improved"
    if report_status == "worsened":
        closure_criterion_changed = False
    summary = {
        "status": report_status,
        "summary": summarize_comparison_text(
            report_status=report_status,
            probe_report=probe_report,
            same_scale_uncertainty_report=same_scale_uncertainty_report,
            same_scale_stability_frontier_report=same_scale_stability_frontier_report,
            closure_gap_deltas_report=closure_gap_deltas_report,
            keep_closure_inconclusive=keep_closure_inconclusive,
        ),
        "closure_status": closure_status,
        "closure_interpretation_status": closure_interpretation_status,
        "closure_criterion_changed": closure_criterion_changed,
        "keep_closure_inconclusive": keep_closure_inconclusive,
    }
    return summary


def summarize_comparison_text(
    *,
    report_status: str,
    probe_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    keep_closure_inconclusive: bool,
) -> str:
    if report_status == "blocked_missing_inputs":
        return "The bounded probe comparison remains blocked because required evidence inputs are missing."

    probe_status = str(probe_report.get("probe_status") or "unknown")
    uncertainty_status = str(same_scale_uncertainty_report.get("spatial_uncertainty_status") or "unknown")
    frontier_status = str(same_scale_stability_frontier_report.get("frontier_status") or "unknown")
    closure_gap_status = str(closure_gap_deltas_report.get("closure_gap_status") or "unknown")
    closure_status = str(closure_gap_deltas_report.get("current_closure_status") or "unknown")

    if report_status == "improved":
        return (
            "The bounded probe materially changes the closure criterion, so the closure interpretation is no longer "
            f"purely inconclusive ({closure_status})."
        )
    if report_status == "worsened":
        return (
            "The bounded probe does not close the gap and the comparison is less useful than the current same-scale "
            "baseline, so the closure interpretation stays conservative."
        )

    keep_phrase = "keeps closure inconclusive" if keep_closure_inconclusive else "does not yet change the closure criterion"
    return (
        "The bounded probe confirms the current same-scale envelope: "
        f"probe_status={probe_status}, spatial_uncertainty_status={uncertainty_status}, "
        f"frontier_status={frontier_status}, closure_gap_status={closure_gap_status}; "
        f"the comparison {keep_phrase}."
    )


def summarize_probe_evidence(probe_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_status": probe_report.get("probe_status", "unknown"),
        "planning_status": probe_report.get("planning_status", "unknown"),
        "proposed_probe": dict(probe_report.get("proposed_probe") or {}),
        "boundedness_proof": dict(probe_report.get("boundedness_proof") or {}),
        "measured_evidence": dict(probe_report.get("measured_evidence") or {}),
    }


def summarize_same_scale_evidence(
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "same_scale_uncertainty": {
            "status": same_scale_uncertainty_report.get("spatial_uncertainty_status", "unknown"),
            "selected_layers": list(same_scale_uncertainty_report.get("selected_layers", [])),
            "dominant_layers_by_mean_range": list(
                same_scale_uncertainty_report.get("dominant_layers_by_mean_range", [])
            ),
        },
        "same_scale_stability_frontier": {
            "status": same_scale_stability_frontier_report.get("frontier_status", "unknown"),
            "recommendation_class": same_scale_stability_frontier_report.get("recommendation_class", "unknown"),
        },
        "closure_gap": {
            "status": closure_gap_deltas_report.get("closure_gap_status", "unknown"),
            "current_closure_status": closure_gap_deltas_report.get("current_closure_status", "unknown"),
            "current_interpretation_status": closure_gap_deltas_report.get(
                "current_interpretation_status", "unknown"
            ),
            "closure_limiting_layers": [
                item.get("layer_key")
                for item in closure_gap_deltas_report.get("closure_limiting_layers", [])
                if isinstance(item, dict) and item.get("layer_key")
            ],
            "deferrable_layers": [
                item.get("layer_key")
                for item in closure_gap_deltas_report.get("deferrable_layers", [])
                if isinstance(item, dict) and item.get("layer_key")
            ],
        },
    }


def build_same_scale_uncertainty_report() -> dict[str, Any]:
    return SPATIAL.build_report(
        manifest_paths=list(SPATIAL.DEFAULT_MANIFESTS),
        hazard_layers=tuple(SPATIAL.DEFAULT_HAZARD_LAYERS),
        top_n=8,
    )


def collect_missing_inputs(
    evidence_override: dict[str, Any] | None,
    *,
    probe_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
) -> list[str]:
    if evidence_override and evidence_override.get("missing_inputs"):
        return [str(item) for item in evidence_override.get("missing_inputs", [])]
    missing: list[str] = []
    for label, report, status_key in (
        ("bounded_probe_report", probe_report, "probe_status"),
        ("same_scale_uncertainty_report", same_scale_uncertainty_report, "spatial_uncertainty_status"),
        ("same_scale_stability_frontier_report", same_scale_stability_frontier_report, "frontier_status"),
        ("closure_gap_deltas_report", closure_gap_deltas_report, "closure_gap_status"),
    ):
        status = str((report or {}).get(status_key) or "")
        if not status or status.startswith("blocked") or status == "missing":
            missing.append(label)
    return missing


def section_or_build(
    evidence_override: dict[str, Any] | None,
    key: str,
    builder,
) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get(key), dict):
        return dict(evidence_override[key])
    return builder()


def claim_boundaries() -> dict[str, bool]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Bounded Probe Interpretation",
        f"probe_interpretation_status: {report['probe_interpretation_status']}",
        f"bounded_probe_status: {report['bounded_probe_status']}",
        f"same_scale_uncertainty_status: {report['same_scale_uncertainty_status']}",
        f"same_scale_stability_frontier_status: {report['same_scale_stability_frontier_status']}",
        f"closure_gap_status: {report['closure_gap_status']}",
        f"closure_status: {report['closure_status']}",
        f"closure_interpretation_status: {report['closure_interpretation_status']}",
        f"keep_closure_inconclusive: {str(report['keep_closure_inconclusive']).lower()}",
        "",
        "## Comparison Summary",
        "",
        f"- status: `{report['comparison_summary']['status']}`",
        f"- summary: {report['comparison_summary']['summary']}",
        f"- closure_criterion_changed: `{report['comparison_summary']['closure_criterion_changed']}`",
        "",
        "## Probe Evidence",
        "",
        f"- probe_status: `{report['probe_evidence'].get('probe_status')}`",
        f"- planning_status: `{report['probe_evidence'].get('planning_status')}`",
        "",
        "## Same-Scale Evidence",
        "",
        json.dumps(report["same_scale_evidence"], sort_keys=True),
        "",
        "## Claim Boundaries",
        "",
        json.dumps(report["claim_boundaries"], sort_keys=True),
    ]
    if report.get("blocked_reason") and report["blocked_reason"] != "none":
        lines.extend(["", f"Blocked reason: {report['blocked_reason']}"])
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
