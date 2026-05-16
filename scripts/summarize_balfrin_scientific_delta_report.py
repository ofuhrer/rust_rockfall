#!/usr/bin/env python3
"""Summarize the Balfrin scientific delta against same-scale evidence.

This helper is read-only. It compares the measured Balfrin post-run evidence
against the existing same-scale uncertainty, stability frontier, closure-gap,
and hotspot provenance summaries. It does not rerun the model, tune physics,
or authorize operational, probabilistic, or scale-up claims.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_scientific_delta_report_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise BalfrinScientificDeltaReportError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


POST_RUN = _load_module("balfrin_scientific_delta_post_run", "summarize_balfrin_post_run_interpretation_gate.py")
SPATIAL = _load_module("balfrin_scientific_delta_spatial", "summarize_spatial_same_scale_uncertainty.py")
STABILITY = _load_module("balfrin_scientific_delta_stability", "summarize_same_scale_stability_frontier.py")
CLOSURE_GAP = _load_module("balfrin_scientific_delta_closure_gap", "summarize_tschamut_closure_gap_deltas.py")
HOTSPOT = _load_module("balfrin_scientific_delta_hotspot", "summarize_tschamut_hotspot_provenance.py")


class BalfrinScientificDeltaReportError(ValueError):
    """User-facing scientific delta report error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate delta snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinScientificDeltaReportError as exc:
        print(f"balfrin scientific delta report error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["scientific_delta_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinScientificDeltaReportError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinScientificDeltaReportError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")
    if evidence_override and isinstance(evidence_override.get("scientific_delta_report"), dict):
        return dict(evidence_override["scientific_delta_report"])

    post_run_report = section_or_build(
        evidence_override,
        "post_run_interpretation_gate_report",
        POST_RUN.build_report,
    )
    same_scale_uncertainty_report = section_or_build(
        evidence_override,
        "same_scale_uncertainty_report",
        build_spatial_report,
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
    hotspot_provenance_report = section_or_build(
        evidence_override,
        "hotspot_provenance_report",
        HOTSPOT.build_report,
    )

    report_status = classify_status(
        post_run_report=post_run_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        hotspot_provenance_report=hotspot_provenance_report,
    )
    if report_status == "blocked_missing_inputs":
        missing_inputs = collect_missing_inputs(
            evidence_override,
            post_run_report=post_run_report,
            same_scale_uncertainty_report=same_scale_uncertainty_report,
            same_scale_stability_frontier_report=same_scale_stability_frontier_report,
            closure_gap_deltas_report=closure_gap_deltas_report,
            hotspot_provenance_report=hotspot_provenance_report,
        )
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    scientific_delta_summary = summarize_scientific_delta(
        post_run_report=post_run_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        hotspot_provenance_report=hotspot_provenance_report,
        report_status=report_status,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "scientific_delta_status": report_status,
        "balfrin_post_run_interpretation_gate_report": post_run_report,
        "same_scale_uncertainty_report": same_scale_uncertainty_report,
        "same_scale_stability_frontier_report": same_scale_stability_frontier_report,
        "closure_gap_deltas_report": closure_gap_deltas_report,
        "hotspot_provenance_report": hotspot_provenance_report,
        "scientific_delta_summary": scientific_delta_summary,
        "claim_boundaries": claim_boundaries(post_run_report),
        "measurement_commands": {
            "post_run_interpretation_gate": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json",
            "same_scale_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "same_scale_stability_frontier": "PYENV_VERSION=system uv run python scripts/summarize_same_scale_stability_frontier.py --format json",
            "closure_gap_deltas": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format json",
            "hotspot_provenance": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_hotspot_provenance.py --format json",
        },
        "blocked_reason": "none",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
    }


def section_or_build(
    evidence_override: dict[str, Any] | None,
    key: str,
    builder,
) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get(key), dict):
        return dict(evidence_override[key])
    return builder()


def build_spatial_report() -> dict[str, Any]:
    return SPATIAL.build_report(
        manifest_paths=list(SPATIAL.DEFAULT_MANIFESTS),
        hazard_layers=tuple(SPATIAL.DEFAULT_HAZARD_LAYERS),
        top_n=8,
    )


def collect_missing_inputs(
    evidence_override: dict[str, Any] | None,
    *,
    post_run_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    hotspot_provenance_report: dict[str, Any],
) -> list[str]:
    if evidence_override and evidence_override.get("missing_inputs"):
        return [str(item) for item in evidence_override.get("missing_inputs", [])]
    missing: list[str] = []
    for label, report, status_key in (
        ("post_run_interpretation_gate_report", post_run_report, "interpretation_status"),
        ("same_scale_uncertainty_report", same_scale_uncertainty_report, "spatial_uncertainty_status"),
        ("same_scale_stability_frontier_report", same_scale_stability_frontier_report, "frontier_status"),
        ("closure_gap_deltas_report", closure_gap_deltas_report, "closure_gap_status"),
        ("hotspot_provenance_report", hotspot_provenance_report, "hotspot_provenance_status"),
    ):
        status = str((report or {}).get(status_key) or "")
        if not status or status.startswith("blocked") or status == "missing":
            missing.append(label)
    return missing


def classify_status(
    *,
    post_run_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    hotspot_provenance_report: dict[str, Any],
) -> str:
    statuses = [
        str(post_run_report.get("interpretation_status") or ""),
        str(same_scale_uncertainty_report.get("spatial_uncertainty_status") or ""),
        str(same_scale_stability_frontier_report.get("frontier_status") or ""),
        str(closure_gap_deltas_report.get("closure_gap_status") or ""),
        str(hotspot_provenance_report.get("hotspot_provenance_status") or ""),
    ]
    if any(status.startswith("blocked") or status == "missing" for status in statuses):
        return "blocked_missing_inputs"
    measured_statuses = {
        "measured_conditional_diagnostic",
        "measured_existing_artifacts",
        "measured_gaps_remain",
    }
    if (
        statuses[0] in measured_statuses
        and statuses[1] == "measured_existing_artifacts"
        and statuses[2] == "measured_existing_artifacts"
        and statuses[3] == "measured_gaps_remain"
        and statuses[4] == "measured_existing_artifacts"
    ):
        return "measured_existing_artifacts"
    return "inconclusive_existing_artifacts"


def summarize_scientific_delta(
    *,
    post_run_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    hotspot_provenance_report: dict[str, Any],
    report_status: str,
) -> dict[str, Any]:
    uncertainty_layers = same_scale_uncertainty_report.get("selected_layers", [])
    dominant_layers = list(same_scale_uncertainty_report.get("dominant_layers_by_mean_range", []))
    closure_limiting_layers = [item.get("layer_key") for item in closure_gap_deltas_report.get("closure_limiting_layers", []) if item.get("layer_key")]
    deferrable_layers = [item.get("layer_key") for item in closure_gap_deltas_report.get("deferrable_layers", []) if item.get("layer_key")]
    hotspot_classes = dict(hotspot_provenance_report.get("hotspot_provenance_classes") or {})
    hotspot_limitations = list(hotspot_provenance_report.get("attribution_limits", {}).get("cannot_attribute", []))

    comparisons = [
        {
            "topic": "same_scale_uncertainty",
            "source_status": same_scale_uncertainty_report.get("spatial_uncertainty_status"),
            "delta_class": "confirmed_same_scale_state",
            "summary": "The measured Balfrin run does not reclassify the current same-scale uncertainty envelope.",
        },
        {
            "topic": "stability_frontier",
            "source_status": same_scale_stability_frontier_report.get("frontier_status"),
            "delta_class": "bounded_and_informative",
            "summary": "The measured Balfrin run remains consistent with a bounded frontier rather than a scale-up trigger.",
        },
        {
            "topic": "closure_gap_deltas",
            "source_status": closure_gap_deltas_report.get("closure_gap_status"),
            "delta_class": "gap_remains_open",
            "summary": "The measured Balfrin run does not convert the closure-gap deltas into accepted closure evidence.",
        },
        {
            "topic": "hotspot_provenance",
            "source_status": hotspot_provenance_report.get("hotspot_provenance_status"),
            "delta_class": "run_level_traceable_cell_level_unknown",
            "summary": "The measured Balfrin run confirms run-level hotspot provenance, but not cell-level lineage.",
        },
    ]

    if report_status == "measured_existing_artifacts":
        confirmed = [
            "Balfrin measured evidence is readable as a conditional diagnostic artifact.",
            "The measured run confirms the current same-scale evidence remains the scientific boundary for closure interpretation.",
            "The measured run keeps the local single-job path sufficient for the next same-scale step.",
        ]
        unchanged = [
            "Same-scale uncertainty remains closure-limiting where the existing helpers already classify it as closure-limiting.",
            "The closure-gap interpretation remains closer to deferred than to no-go.",
            "Hotspot provenance remains committed-source-zone and scenario traceable, but cell-level lineage is still unavailable.",
        ]
    else:
        confirmed = [
            "Balfrin evidence is present, but the scientific comparison remains incompletely resolved.",
        ]
        unchanged = [
            "The report does not reclassify the same-scale uncertainty envelope.",
            "The report does not turn the closure gap into accepted closure evidence.",
        ]

    return {
        "status": report_status,
        "confirmed": confirmed,
        "unchanged": unchanged,
        "not_addressed": [
            "No physical validation, operational authorization, annual-frequency claim, or risk/exposure/vulnerability claim is introduced here.",
            "No new measured evidence reclassifies Tschamut closure beyond the current same-scale interpretation structure.",
        ],
        "comparisons": comparisons,
        "same_scale_focus": {
            "uncertainty_layers": list(uncertainty_layers),
            "dominant_layers_by_mean_range": dominant_layers,
            "closure_limiting_layers": closure_limiting_layers,
            "deferrable_layers": deferrable_layers,
            "hotspot_classes": hotspot_classes,
            "hotspot_limitations": hotspot_limitations,
        },
    }


def claim_boundaries(post_run_report: dict[str, Any]) -> dict[str, Any]:
    boundaries = dict(post_run_report.get("claim_boundaries") or {})
    if not boundaries:
        boundaries = POST_RUN.claim_boundaries()
    boundaries.setdefault("operational_claims_allowed", False)
    boundaries.setdefault("physical_probability_claims_allowed", False)
    boundaries.setdefault("annual_frequency_claims_allowed", False)
    boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    boundaries.setdefault("scale_up_authorized", False)
    boundaries.setdefault("distributed_execution_authorized", False)
    return boundaries


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scientific_delta_status": "blocked_missing_inputs",
        "balfrin_post_run_interpretation_gate_report": {
            "schema_version": POST_RUN.SCHEMA_VERSION,
            "interpretation_status": "blocked_missing_inputs",
            "artifact_acceptance_status": "blocked_missing_inputs",
            "usable_as_conditional_diagnostic_artifact": False,
            "claim_boundaries": POST_RUN.claim_boundaries(),
        },
        "same_scale_uncertainty_report": {
            "schema_version": SPATIAL.SCHEMA_VERSION,
            "spatial_uncertainty_status": "blocked_missing_inputs",
        },
        "same_scale_stability_frontier_report": {
            "schema_version": STABILITY.SCHEMA_VERSION,
            "frontier_status": "blocked_missing_inputs",
        },
        "closure_gap_deltas_report": {
            "schema_version": CLOSURE_GAP.SCHEMA_VERSION,
            "closure_gap_status": "blocked_missing_inputs",
        },
        "hotspot_provenance_report": {
            "schema_version": HOTSPOT.SCHEMA_VERSION,
            "hotspot_provenance_status": "blocked_missing_inputs",
        },
        "scientific_delta_summary": {
            "status": "blocked_missing_inputs",
            "confirmed": [],
            "unchanged": [],
            "not_addressed": [],
            "comparisons": [],
            "same_scale_focus": {},
        },
        "claim_boundaries": POST_RUN.claim_boundaries(),
        "measurement_commands": {
            "post_run_interpretation_gate": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json",
            "same_scale_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "same_scale_stability_frontier": "PYENV_VERSION=system uv run python scripts/summarize_same_scale_stability_frontier.py --format json",
            "closure_gap_deltas": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format json",
            "hotspot_provenance": "PYENV_VERSION=system uv run python scripts/summarize_tschamut_hotspot_provenance.py --format json",
        },
        "missing_inputs": missing_inputs,
        "blocked_reason": reason,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Scientific Delta Report",
        f"scientific_delta_status: {report['scientific_delta_status']}",
        f"post_run_interpretation_status: {report['balfrin_post_run_interpretation_gate_report'].get('interpretation_status', 'unknown')}",
        f"same_scale_uncertainty_status: {report['same_scale_uncertainty_report'].get('spatial_uncertainty_status', 'unknown')}",
        f"same_scale_stability_frontier_status: {report['same_scale_stability_frontier_report'].get('frontier_status', 'unknown')}",
        f"closure_gap_status: {report['closure_gap_deltas_report'].get('closure_gap_status', 'unknown')}",
        f"hotspot_provenance_status: {report['hotspot_provenance_report'].get('hotspot_provenance_status', 'unknown')}",
        "",
        "## Confirmed",
    ]
    for item in report.get("scientific_delta_summary", {}).get("confirmed", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Unchanged"])
    for item in report.get("scientific_delta_summary", {}).get("unchanged", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Not Addressed"])
    for item in report.get("scientific_delta_summary", {}).get("not_addressed", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Comparisons"])
    for item in report.get("scientific_delta_summary", {}).get("comparisons", []):
        lines.append(
            f"- {item['topic']}: {item['delta_class']} | "
            f"source_status={item['source_status']} | {item['summary']}"
        )
    lines.extend(["", "## Same-Scale Focus"])
    focus = report.get("scientific_delta_summary", {}).get("same_scale_focus", {})
    lines.append(f"- uncertainty_layers: {', '.join(focus.get('uncertainty_layers', []))}")
    lines.append(f"- dominant_layers_by_mean_range: {', '.join(focus.get('dominant_layers_by_mean_range', []))}")
    lines.append(f"- closure_limiting_layers: {', '.join(focus.get('closure_limiting_layers', []))}")
    lines.append(f"- deferrable_layers: {', '.join(focus.get('deferrable_layers', []))}")
    if focus.get("hotspot_classes"):
        lines.append(f"- hotspot_classes: {json.dumps(focus['hotspot_classes'], sort_keys=True)}")
    if report.get("missing_inputs"):
        lines.extend(["", "## Missing Inputs", ""])
        for item in report["missing_inputs"]:
            lines.append(f"- {item}")
    if report.get("blocked_reason") and report["blocked_reason"] != "none":
        lines.extend(["", f"Blocked reason: {report['blocked_reason']}"])
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
