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
FEASIBILITY = _load_module("balfrin_scientific_delta_feasibility", "summarize_bounded_next_ensemble_feasibility_probe.py")
CLOSURE_GAP = _load_module("balfrin_scientific_delta_closure_gap", "summarize_tschamut_closure_gap_deltas.py")
HOTSPOT = _load_module("balfrin_scientific_delta_hotspot", "summarize_tschamut_hotspot_provenance.py")
BOUNDED_PROBE = _load_module(
    "balfrin_scientific_delta_bounded_probe",
    "summarize_balfrin_bounded_probe_interpretation.py",
)


class BalfrinScientificDeltaReportError(ValueError):
    """User-facing scientific delta report error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="optional directory for the canonical JSON and text interpretation artifact",
    )
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
    bounded_probe_interpretation_report = section_or_build(
        evidence_override,
        "bounded_probe_interpretation_report",
        lambda: BOUNDED_PROBE.build_report(
            {
                "bounded_probe_report": (
                    dict(same_scale_stability_frontier_report.get("bounded_probe_feasibility") or {})
                    or FEASIBILITY.build_report()
                ),
                "same_scale_uncertainty_report": same_scale_uncertainty_report,
                "same_scale_stability_frontier_report": same_scale_stability_frontier_report,
                "closure_gap_deltas_report": closure_gap_deltas_report,
            }
        ),
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
        bounded_probe_interpretation_report=bounded_probe_interpretation_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        hotspot_provenance_report=hotspot_provenance_report,
        report_status=report_status,
    )
    canonical_interpretation = build_canonical_interpretation(
        post_run_report=post_run_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        bounded_probe_interpretation_report=bounded_probe_interpretation_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        hotspot_provenance_report=hotspot_provenance_report,
        report_status=report_status,
        scientific_delta_summary=scientific_delta_summary,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "scientific_delta_status": report_status,
        "balfrin_post_run_interpretation_gate_report": post_run_report,
        "same_scale_uncertainty_report": same_scale_uncertainty_report,
        "bounded_probe_interpretation_report": bounded_probe_interpretation_report,
        "same_scale_stability_frontier_report": same_scale_stability_frontier_report,
        "closure_gap_deltas_report": closure_gap_deltas_report,
        "hotspot_provenance_report": hotspot_provenance_report,
        "scientific_delta_summary": scientific_delta_summary,
        "canonical_interpretation": canonical_interpretation,
        "machine_readable_blockers": canonical_interpretation.get("blockers", {}),
        "machine_readable_boundaries": canonical_interpretation.get("boundaries", {}),
        "claim_boundaries": claim_boundaries(post_run_report),
        "measurement_commands": {
            "post_run_interpretation_gate": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json",
            "same_scale_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "bounded_probe_interpretation": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_bounded_probe_interpretation.py --format json",
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


def build_canonical_interpretation(
    *,
    post_run_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    bounded_probe_interpretation_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    hotspot_provenance_report: dict[str, Any],
    report_status: str,
    scientific_delta_summary: dict[str, Any],
) -> dict[str, Any]:
    interpretation_status = str(post_run_report.get("interpretation_status") or "unknown")
    closure_status = str(closure_gap_deltas_report.get("current_closure_status") or "unknown")
    closure_gap_status = str(closure_gap_deltas_report.get("closure_gap_status") or "unknown")
    bounded_probe_status = str(bounded_probe_interpretation_report.get("probe_interpretation_status") or "unknown")
    interpretation_delta = derive_interpretation_delta(
        report_status=report_status,
        closure_gap_status=closure_gap_status,
        current_closure_status=closure_status,
        current_interpretation_status=interpretation_status,
    )
    blockers = build_machine_readable_blockers(
        post_run_report=post_run_report,
        same_scale_uncertainty_report=same_scale_uncertainty_report,
        bounded_probe_interpretation_report=bounded_probe_interpretation_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
        closure_gap_deltas_report=closure_gap_deltas_report,
        hotspot_provenance_report=hotspot_provenance_report,
        scientific_delta_summary=scientific_delta_summary,
    )
    boundaries = build_machine_readable_boundaries(
        post_run_report=post_run_report,
        same_scale_stability_frontier_report=same_scale_stability_frontier_report,
    )
    return {
        "schema_version": "balfrin_scientific_delta_interpretation_v1",
        "interpretation_delta": interpretation_delta,
        "bounded_probe_interpretation": {
            "status": bounded_probe_status,
            "summary": bounded_probe_interpretation_report.get("comparison_summary", {}).get("summary"),
            "keep_closure_inconclusive": bounded_probe_interpretation_report.get("keep_closure_inconclusive", True),
        },
        "closure_semantics": {
            "current_closure_status": closure_status,
            "current_interpretation_status": interpretation_status,
            "closure_gap_status": closure_gap_status,
            "bounded_probe_interpretation_status": bounded_probe_status,
        },
        "blockers": blockers,
        "boundaries": boundaries,
        "summary": {
            "status": interpretation_delta["status"],
            "summary": interpretation_delta["summary"],
            "closure_limiting_layers": list(scientific_delta_summary.get("same_scale_focus", {}).get("closure_limiting_layers", [])),
            "deferrable_layers": list(scientific_delta_summary.get("same_scale_focus", {}).get("deferrable_layers", [])),
            "bounded_probe_interpretation": dict(scientific_delta_summary.get("bounded_probe_interpretation") or {}),
        },
    }


def derive_interpretation_delta(
    *,
    report_status: str,
    closure_gap_status: str,
    current_closure_status: str,
    current_interpretation_status: str,
) -> dict[str, Any]:
    if report_status == "blocked_missing_inputs":
        return {
            "status": "blocked_missing_inputs",
            "current_closure_status": current_closure_status,
            "current_interpretation_status": current_interpretation_status,
            "closure_gap_status": closure_gap_status,
            "summary": "Measured Balfrin evidence is incomplete, so no diagnostic delta can be stated.",
        }
    if report_status == "measured_existing_artifacts":
        return {
            "status": "leaves_current_inconclusive_interpretation_unchanged",
            "current_closure_status": current_closure_status,
            "current_interpretation_status": current_interpretation_status,
            "closure_gap_status": closure_gap_status,
            "summary": "Measured Balfrin evidence remains bounded and does not reclassify the current inconclusive diagnostic interpretation.",
        }
    return {
        "status": "weakens_current_inconclusive_interpretation",
        "current_closure_status": current_closure_status,
        "current_interpretation_status": current_interpretation_status,
        "closure_gap_status": closure_gap_status,
        "summary": "The measured Balfrin evidence narrows the diagnostic boundary but still leaves closure inconclusive.",
    }


def build_machine_readable_blockers(
    *,
    post_run_report: dict[str, Any],
    same_scale_uncertainty_report: dict[str, Any],
    bounded_probe_interpretation_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
    closure_gap_deltas_report: dict[str, Any],
    hotspot_provenance_report: dict[str, Any],
    scientific_delta_summary: dict[str, Any],
) -> dict[str, Any]:
    focus = dict(scientific_delta_summary.get("same_scale_focus") or {})
    blocker_deltas = list(closure_gap_deltas_report.get("workflow_product_blocker_deltas", []))
    blocker_index = {
        str(item.get("blocker_key") or ""): dict(item)
        for item in blocker_deltas
        if item.get("blocker_key")
    }
    portability_blocker = blocker_index.get("public_context_inputs_deferred", {})
    runtime_blocker = blocker_index.get("runtime_scaling_sufficient", {})
    output_blocker = blocker_index.get("summary_only_not_rebuildable", {})
    gis_blocker = blocker_index.get("standard_gis_roots_cog_blocked", {})
    return {
        "closure_limiting_layers": {
            "status": "closure_limiting",
            "layer_keys": list(focus.get("closure_limiting_layers", [])),
            "deferrable_layer_keys": list(focus.get("deferrable_layers", [])),
            "same_scale_interpretation": str(same_scale_uncertainty_report.get("spatial_interpretation") or "unknown"),
            "closure_gap_status": str(closure_gap_deltas_report.get("closure_gap_status") or "unknown"),
            "current_closure_status": str(closure_gap_deltas_report.get("current_closure_status") or "unknown"),
            "bounded_probe_interpretation_status": str(
                bounded_probe_interpretation_report.get("probe_interpretation_status") or "unknown"
            ),
        },
        "gis_product_scope": {
            "status": gis_product_scope_status(blocker_index),
            "blocker_keys": [key for key in ("summary_only_not_rebuildable", "standard_gis_roots_cog_blocked") if key in blocker_index],
            "blockers": [blocker_index[key] for key in ("summary_only_not_rebuildable", "standard_gis_roots_cog_blocked") if key in blocker_index],
            "standard_package_status": str(gis_blocker.get("current_status") or "unknown"),
            "output_reuse_status": str(output_blocker.get("blocker_state") or "unknown"),
        },
        "runtime_output_sufficiency": {
            "status": runtime_output_sufficiency_status(blocker_index),
            "blocker_keys": [key for key in ("runtime_scaling_sufficient", "summary_only_not_rebuildable") if key in blocker_index],
            "runtime": runtime_blocker,
            "output": output_blocker,
            "same_scale_stability_frontier_status": str(same_scale_stability_frontier_report.get("frontier_status") or "unknown"),
        },
        "portability_status": {
            "status": portability_status(blocker_index),
            "blocker_key": "public_context_inputs_deferred" if "public_context_inputs_deferred" in blocker_index else "",
            "blocker": portability_blocker,
            "missing_input_categories": list(portability_blocker.get("delta_to_public_context_ready", []))
            if isinstance(portability_blocker.get("delta_to_public_context_ready", []), list)
            else [],
        },
        "physical_credibility_limits": {
            "status": physical_credibility_status(post_run_report),
            "required_physical_credibility": dict(post_run_report.get("required_physical_credibility") or {}),
            "claim_boundaries": dict(post_run_report.get("claim_boundaries") or {}),
            "hotspot_attribution_limits": dict(hotspot_provenance_report.get("attribution_limits") or {}),
        },
    }


def build_machine_readable_boundaries(
    *,
    post_run_report: dict[str, Any],
    same_scale_stability_frontier_report: dict[str, Any],
) -> dict[str, Any]:
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or {})
    if not claim_boundaries:
        claim_boundaries = POST_RUN.claim_boundaries()
    claim_boundaries.setdefault("operational_claims_allowed", False)
    claim_boundaries.setdefault("physical_probability_claims_allowed", False)
    claim_boundaries.setdefault("annual_frequency_claims_allowed", False)
    claim_boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    claim_boundaries.setdefault("scale_up_authorized", False)
    claim_boundaries.setdefault("distributed_execution_authorized", False)
    return {
        "claim_boundaries": claim_boundaries,
        "same_scale_stability_frontier_status": str(same_scale_stability_frontier_report.get("frontier_status") or "unknown"),
        "notes": list(claim_boundaries.get("notes", [])),
    }


def gis_product_scope_status(blocker_index: dict[str, dict[str, Any]]) -> str:
    if "standard_gis_roots_cog_blocked" in blocker_index:
        return "gis_product_scope_blocked"
    if "summary_only_not_rebuildable" in blocker_index:
        return "output_reuse_blocked"
    return "unknown"


def runtime_output_sufficiency_status(blocker_index: dict[str, dict[str, Any]]) -> str:
    if "runtime_scaling_sufficient" in blocker_index and "summary_only_not_rebuildable" in blocker_index:
        return "bounded_runtime_sufficient_output_blocked"
    if "runtime_scaling_sufficient" in blocker_index:
        return "runtime_sufficient"
    if "summary_only_not_rebuildable" in blocker_index:
        return "output_blocked"
    return "unknown"


def portability_status(blocker_index: dict[str, dict[str, Any]]) -> str:
    if "public_context_inputs_deferred" in blocker_index:
        return str(blocker_index["public_context_inputs_deferred"].get("blocker_state") or "public_context_inputs_deferred")
    return "unknown"


def physical_credibility_status(post_run_report: dict[str, Any]) -> str:
    physical = dict(post_run_report.get("required_physical_credibility") or {})
    if physical:
        return str(physical.get("status") or physical.get("evidence_status") or "not_established")
    return "not_established"


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, Path]:
    written: dict[str, Path] = {}
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        if json_output is None:
            json_output = artifact_dir / f"{SCHEMA_VERSION}.json"
        if text_output is None:
            text_output = artifact_dir / f"{SCHEMA_VERSION}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written["json_output"] = json_output
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")
        written["text_output"] = text_output
    return written


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
    bounded_probe_interpretation_report: dict[str, Any],
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
    probe_summary = dict(bounded_probe_interpretation_report.get("comparison_summary") or {})

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
            "topic": "bounded_probe_interpretation",
            "source_status": bounded_probe_interpretation_report.get("probe_interpretation_status"),
            "delta_class": probe_summary.get("status", "unknown"),
            "summary": probe_summary.get("summary")
            or "The bounded Balfrin probe is compared against the current same-scale evidence without changing the closure boundary.",
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
            "The bounded probe comparison keeps the closure status inconclusive unless a closure criterion actually changes.",
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
            "bounded_probe_interpretation": {
                "status": probe_summary.get("status", bounded_probe_interpretation_report.get("probe_interpretation_status", "unknown")),
                "closure_criterion_changed": bool(probe_summary.get("closure_criterion_changed", False)),
                "keep_closure_inconclusive": bool(
                    probe_summary.get(
                        "keep_closure_inconclusive",
                        bounded_probe_interpretation_report.get("keep_closure_inconclusive", True),
                    )
                ),
            },
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
        "bounded_probe_interpretation_report": {
            "schema_version": BOUNDED_PROBE.SCHEMA_VERSION,
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
                "keep_closure_inconclusive": True,
            },
            "probe_evidence": {},
            "same_scale_evidence": {},
            "claim_boundaries": POST_RUN.claim_boundaries(),
            "blocked_reason": "required evidence inputs are missing",
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
            "bounded_probe_interpretation": {},
        },
        "canonical_interpretation": {
            "schema_version": "balfrin_scientific_delta_interpretation_v1",
            "interpretation_delta": {
                "status": "blocked_missing_inputs",
                "current_closure_status": "blocked_missing_inputs",
                "current_interpretation_status": "blocked_missing_inputs",
                "closure_gap_status": "blocked_missing_inputs",
                "summary": "Measured Balfrin evidence is incomplete, so no diagnostic delta can be stated.",
            },
            "closure_semantics": {
                "current_closure_status": "blocked_missing_inputs",
                "current_interpretation_status": "blocked_missing_inputs",
                "closure_gap_status": "blocked_missing_inputs",
                "bounded_probe_interpretation_status": "blocked_missing_inputs",
            },
            "blockers": {
                "closure_limiting_layers": {
                    "status": "blocked_missing_inputs",
                    "layer_keys": [],
                    "deferrable_layer_keys": [],
                },
                "gis_product_scope": {
                    "status": "blocked_missing_inputs",
                    "blocker_keys": [],
                    "blockers": [],
                },
                "runtime_output_sufficiency": {
                    "status": "blocked_missing_inputs",
                    "blocker_keys": [],
                    "runtime": {},
                    "output": {},
                },
                "portability_status": {
                    "status": "blocked_missing_inputs",
                    "blocker_key": "",
                    "blocker": {},
                    "missing_input_categories": [],
                },
                "physical_credibility_limits": {
                    "status": "blocked_missing_inputs",
                    "required_physical_credibility": {},
                    "claim_boundaries": POST_RUN.claim_boundaries(),
                    "hotspot_attribution_limits": {},
                },
            },
            "boundaries": {
                "claim_boundaries": POST_RUN.claim_boundaries(),
                "same_scale_stability_frontier_status": "blocked_missing_inputs",
                "notes": [],
            },
            "summary": {
                "status": "blocked_missing_inputs",
                "summary": "Measured Balfrin evidence is incomplete, so no diagnostic delta can be stated.",
                "closure_limiting_layers": [],
                "deferrable_layers": [],
                "bounded_probe_interpretation": {},
            },
        },
        "machine_readable_blockers": {
            "closure_limiting_layers": {"status": "blocked_missing_inputs", "layer_keys": [], "deferrable_layer_keys": []},
            "gis_product_scope": {"status": "blocked_missing_inputs", "blocker_keys": [], "blockers": []},
            "runtime_output_sufficiency": {"status": "blocked_missing_inputs", "blocker_keys": [], "runtime": {}, "output": {}},
            "portability_status": {"status": "blocked_missing_inputs", "blocker_key": "", "blocker": {}, "missing_input_categories": []},
            "physical_credibility_limits": {
                "status": "blocked_missing_inputs",
                "required_physical_credibility": {},
                "claim_boundaries": POST_RUN.claim_boundaries(),
                "hotspot_attribution_limits": {},
            },
        },
        "machine_readable_boundaries": {
            "claim_boundaries": POST_RUN.claim_boundaries(),
            "same_scale_stability_frontier_status": "blocked_missing_inputs",
            "notes": [],
        },
        "claim_boundaries": POST_RUN.claim_boundaries(),
        "measurement_commands": {
            "post_run_interpretation_gate": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json",
            "same_scale_uncertainty": "PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json",
            "bounded_probe_interpretation": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_bounded_probe_interpretation.py --format json",
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
        f"bounded_probe_interpretation_status: {report['bounded_probe_interpretation_report'].get('probe_interpretation_status', 'unknown')}",
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
    lines.append(f"- bounded_probe_interpretation: {json.dumps(focus.get('bounded_probe_interpretation', {}), sort_keys=True)}")
    if focus.get("hotspot_classes"):
        lines.append(f"- hotspot_classes: {json.dumps(focus['hotspot_classes'], sort_keys=True)}")
    lines.extend(["", "## Canonical Interpretation"])
    canonical = report.get("canonical_interpretation", {})
    interpretation_delta = canonical.get("interpretation_delta", {})
    lines.append(f"- interpretation_delta: {interpretation_delta.get('status', 'unknown')}")
    lines.append(f"- interpretation_summary: {interpretation_delta.get('summary', 'unknown')}")
    lines.append(f"- closure_semantics: {json.dumps(canonical.get('closure_semantics', {}), sort_keys=True)}")
    lines.append(f"- machine_readable_blockers: {json.dumps(report.get('machine_readable_blockers', {}), sort_keys=True)}")
    lines.append(f"- machine_readable_boundaries: {json.dumps(report.get('machine_readable_boundaries', {}), sort_keys=True)}")
    if report.get("missing_inputs"):
        lines.extend(["", "## Missing Inputs", ""])
        for item in report["missing_inputs"]:
            lines.append(f"- {item}")
    if report.get("blocked_reason") and report["blocked_reason"] != "none":
        lines.extend(["", f"Blocked reason: {report['blocked_reason']}"])
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
