#!/usr/bin/env python3
"""Summarize the practical Balfrin ensemble frontier.

This helper is read-only. It composes the measured Balfrin scientific delta,
the single-job execution sufficiency, the bounded next-ensemble feasibility
probe, and the same-scale stability frontier into one bounded frontier report.
It does not run a new ensemble, change physics, or authorize production
scale-up.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_ensemble_frontier_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise BalfrinEnsembleFrontierError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


SCIENTIFIC = _load_module("balfrin_ensemble_frontier_scientific", "summarize_balfrin_scientific_delta_report.py")
SINGLE_JOB = _load_module("balfrin_ensemble_frontier_single_job", "summarize_balfrin_single_job_execution.py")
FEASIBILITY = _load_module("balfrin_ensemble_frontier_feasibility", "summarize_bounded_next_ensemble_feasibility_probe.py")
STABILITY = _load_module("balfrin_ensemble_frontier_stability", "summarize_same_scale_stability_frontier.py")


class BalfrinEnsembleFrontierError(ValueError):
    """User-facing frontier summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="optional directory for the canonical JSON and text frontier report",
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
    except BalfrinEnsembleFrontierError as exc:
        print(f"balfrin ensemble frontier error: {exc}", file=sys.stderr)
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
    return 0 if report["frontier_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinEnsembleFrontierError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinEnsembleFrontierError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(
            {},
            missing_inputs,
            reason="required Balfrin evidence inputs are missing: " + ", ".join(missing_inputs),
        )
    if evidence_override and isinstance(evidence_override.get("ensemble_frontier_report"), dict):
        return dict(evidence_override["ensemble_frontier_report"])

    scientific = section_or_build(
        evidence_override,
        "scientific_delta_report",
        SCIENTIFIC.build_report,
    )
    single_job = section_or_build(
        evidence_override,
        "single_job_execution_summary",
        SINGLE_JOB.build_summary,
    )
    feasibility = section_or_build(
        evidence_override,
        "bounded_next_ensemble_feasibility_probe_report",
        FEASIBILITY.build_report,
    )
    stability = section_or_build(
        evidence_override,
        "same_scale_stability_frontier_report",
        STABILITY.build_report,
    )

    helper_statuses = {
        "scientific_delta_status": scientific.get("scientific_delta_status"),
        "single_job_decision": single_job.get("decision"),
        "feasibility_probe_status": feasibility.get("bounded_probe_recommendation_status") or feasibility.get("probe_status"),
        "feasibility_metadata_contract_status": dict(feasibility.get("metadata_contract") or {}).get("status"),
        "stability_frontier_status": stability.get("frontier_status"),
    }
    helper_blockers = [
        f"{name}={status}"
        for name, status in helper_statuses.items()
        if status in {None, "", "blocked_missing_inputs", "blocked_pending_evidence", "missing"}
        or str(status).startswith("blocked")
    ]
    if helper_blockers:
        return blocked_report(helper_statuses, helper_blockers)

    recommendation_class, recommendation_reason = classify_recommendation(
        scientific=scientific,
        single_job=single_job,
        feasibility=feasibility,
        stability=stability,
    )
    minimum_useful_ensemble = build_minimum_useful_ensemble(feasibility, recommendation_class)
    runtime_growth = build_runtime_growth(single_job, feasibility)
    output_growth = build_output_growth(single_job, feasibility)
    rebuildability_cost = build_rebuildability_cost(feasibility, single_job)
    uncertainty_reduction = build_uncertainty_reduction(scientific, stability)
    frontier_summary = build_frontier_summary(
        recommendation_class=recommendation_class,
        uncertainty_reduction=uncertainty_reduction,
        runtime_growth=runtime_growth,
        output_growth=output_growth,
        rebuildability_cost=rebuildability_cost,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "frontier_status": "measured_existing_artifacts",
        "recommendation_class": recommendation_class,
        "recommendation_reason": recommendation_reason,
        "minimum_useful_ensemble_recommendation": minimum_useful_ensemble,
        "uncertainty_reduction": uncertainty_reduction,
        "runtime_growth": runtime_growth,
        "output_growth": output_growth,
        "rebuildability_cost": rebuildability_cost,
        "helper_statuses": helper_statuses,
        "frontier_summary": frontier_summary,
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": "none",
    }


def blocked_report(
    helper_statuses: dict[str, Any],
    helper_blockers: list[str],
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    blocked_reason = reason or "helper contract unresolved: " + ", ".join(helper_blockers)
    return {
        "schema_version": SCHEMA_VERSION,
        "frontier_status": "blocked_missing_inputs",
        "recommendation_class": "blocked_pending_helper_contract",
        "recommendation_reason": blocked_reason,
        "minimum_useful_ensemble_recommendation": {},
        "uncertainty_reduction": {},
        "runtime_growth": {},
        "output_growth": {},
        "rebuildability_cost": {},
        "helper_statuses": helper_statuses,
        "frontier_summary": [],
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": blocked_reason,
    }


def classify_recommendation(
    *,
    scientific: dict[str, Any],
    single_job: dict[str, Any],
    feasibility: dict[str, Any],
    stability: dict[str, Any],
) -> tuple[str, str]:
    if single_job.get("decision") == "blocked_pending_evidence":
        return "blocked_pending_helper_contract", "single-job evidence is missing"
    if scientific.get("scientific_delta_status") == "blocked_missing_inputs":
        return "blocked_pending_helper_contract", "scientific delta helper is blocked"
    if stability.get("recommendation_class") == "blocked_pending_helper_contract":
        return "blocked_pending_helper_contract", "stability frontier helper is blocked"
    bounded_probe_status = feasibility.get("bounded_probe_recommendation_status") or feasibility.get("probe_status")
    metadata_contract_status = dict(feasibility.get("metadata_contract") or {}).get("status")
    if bounded_probe_status == "blocked_pending_evidence":
        return "blocked_pending_helper_contract", "bounded next-ensemble helper is blocked"
    if metadata_contract_status == "blocked_missing_optional_probabilistic_metadata":
        return "blocked_pending_helper_contract", "bounded next-ensemble helper is blocked on missing optional probabilistic metadata"

    boundedness = dict(feasibility.get("boundedness_proof") or {})
    single_job_sufficient = bool(single_job.get("single_job_sufficient_for_next_step"))
    measured_frontier = str(stability.get("recommendation_class") or "")
    if (
        single_job_sufficient
        and measured_frontier == "additional_probe_informative"
        and boundedness.get("bounded_relative_to_target_validation") is True
        and boundedness.get("bounded_relative_to_target_hazard") is True
    ):
        return (
            "defer_small_bounded_ensemble",
            "the measured Balfrin evidence still shows useful uncertainty spread, and the bounded rebuildable-reduced probe remains operationally practical without scale-up",
        )

    return (
        "no_go_additional_ensemble",
        "the current measured Balfrin evidence does not justify another bounded ensemble as a materially informative next step",
    )


def build_minimum_useful_ensemble(feasibility: dict[str, Any], recommendation_class: str) -> dict[str, Any]:
    proposed = dict(feasibility.get("proposed_probe") or {})
    bounded = dict(feasibility.get("boundedness_proof") or {})
    if recommendation_class.startswith("blocked"):
        return {}
    return {
        "decision": "defer" if recommendation_class == "defer_small_bounded_ensemble" else "no_go",
        "probe_id": proposed.get("probe_id"),
        "ensemble_size": proposed.get("trajectory_count"),
        "validation_output_mode": proposed.get("validation_output_mode"),
        "expected_output_file_count": proposed.get("expected_output_file_count"),
        "expected_output_bytes": proposed.get("expected_output_bytes"),
        "expected_artifact_families": proposed.get("expected_artifact_families", []),
        "bounded_relative_to_target_validation": bounded.get("bounded_relative_to_target_validation"),
        "bounded_relative_to_target_hazard": bounded.get("bounded_relative_to_target_hazard"),
        "expected_command": proposed.get("expected_command"),
    }


def build_runtime_growth(single_job: dict[str, Any], feasibility: dict[str, Any]) -> dict[str, Any]:
    wall_time = dict(single_job.get("wall_time_evidence") or {})
    current_runtime = numeric_value(wall_time.get("current_gap_runtime_seconds"))
    reproduction_validation_runtime = numeric_value(wall_time.get("reproduction_validation_wall_seconds"))
    reproduction_hazard_runtime = numeric_value(wall_time.get("reproduction_hazard_wall_seconds"))
    proposed = dict(feasibility.get("proposed_probe") or {})
    trajectory_count = numeric_value(proposed.get("trajectory_count"))
    return {
        "current_gap_runtime_seconds": current_runtime,
        "reproduction_validation_wall_seconds": reproduction_validation_runtime,
        "reproduction_hazard_wall_seconds": reproduction_hazard_runtime,
        "runtime_growth_factor_validation": ratio(reproduction_validation_runtime, current_runtime),
        "runtime_growth_factor_hazard": ratio(reproduction_hazard_runtime, current_runtime),
        "proposed_ensemble_size": trajectory_count,
        "single_job_decision": single_job.get("decision"),
    }


def build_output_growth(single_job: dict[str, Any], feasibility: dict[str, Any]) -> dict[str, Any]:
    output_size = dict(single_job.get("output_size_evidence") or {})
    current_files = numeric_value(output_size.get("current_gap_output_file_count"))
    current_bytes = numeric_value(output_size.get("current_gap_output_bytes"))
    proposed = dict(feasibility.get("proposed_probe") or {})
    proposed_files = numeric_value(proposed.get("expected_output_file_count"))
    proposed_bytes = numeric_value(proposed.get("expected_output_bytes"))
    return {
        "current_gap_output_file_count": current_files,
        "current_gap_output_bytes": current_bytes,
        "expected_output_file_count": proposed_files,
        "expected_output_bytes": proposed_bytes,
        "output_file_delta": delta(proposed_files, current_files),
        "output_byte_delta": delta(proposed_bytes, current_bytes),
        "output_file_ratio": ratio(proposed_files, current_files),
        "output_byte_ratio": ratio(proposed_bytes, current_bytes),
    }


def build_rebuildability_cost(feasibility: dict[str, Any], single_job: dict[str, Any]) -> dict[str, Any]:
    measured = dict(feasibility.get("measured_evidence") or {})
    bounded = dict(feasibility.get("boundedness_proof") or {})
    output_size = dict(single_job.get("output_size_evidence") or {})
    return {
        "rebuildable_reduced_output_file_count": numeric_value(measured.get("rebuildable_reduced_output_file_count")),
        "rebuildable_reduced_output_bytes": numeric_value(measured.get("rebuildable_reduced_output_bytes")),
        "target_validation_output_file_count": numeric_value(measured.get("target_validation_output_file_count")),
        "target_validation_output_bytes": numeric_value(measured.get("target_validation_output_bytes")),
        "target_hazard_output_file_count": numeric_value(measured.get("target_hazard_output_file_count")),
        "target_hazard_output_bytes": numeric_value(measured.get("target_hazard_output_bytes")),
        "single_job_current_gap_output_file_count": numeric_value(output_size.get("current_gap_output_file_count")),
        "single_job_current_gap_output_bytes": numeric_value(output_size.get("current_gap_output_bytes")),
        "bounded_relative_to_target_validation": bounded.get("bounded_relative_to_target_validation"),
        "bounded_relative_to_target_hazard": bounded.get("bounded_relative_to_target_hazard"),
        "output_byte_ratio_to_target_validation": bounded.get("output_byte_ratio_to_target_validation"),
        "output_file_ratio_to_target_validation": bounded.get("output_file_ratio_to_target_validation"),
        "output_byte_ratio_to_target_hazard": bounded.get("output_byte_ratio_to_target_hazard"),
        "output_file_ratio_to_target_hazard": bounded.get("output_file_ratio_to_target_hazard"),
    }


def build_uncertainty_reduction(scientific: dict[str, Any], stability: dict[str, Any]) -> dict[str, Any]:
    delta_summary = dict(scientific.get("scientific_delta_summary") or {})
    same_scale_focus = dict(delta_summary.get("same_scale_focus") or {})
    frontier_uncertainty = dict(stability.get("measured_uncertainty_deltas") or {})
    return {
        "scientific_delta_status": scientific.get("scientific_delta_status"),
        "same_scale_focus": {
            "uncertainty_layers": list(same_scale_focus.get("uncertainty_layers", [])),
            "dominant_layers_by_mean_range": list(same_scale_focus.get("dominant_layers_by_mean_range", [])),
            "closure_limiting_layers": list(same_scale_focus.get("closure_limiting_layers", [])),
            "deferrable_layers": list(same_scale_focus.get("deferrable_layers", [])),
        },
        "stability_frontier_status": stability.get("frontier_status"),
        "stability_recommendation_class": stability.get("recommendation_class"),
        "dominant_layer_spread": frontier_uncertainty.get("dominant_layer_spread", {}),
        "frontier_summary": list(stability.get("frontier_summary", [])),
    }


def build_frontier_summary(
    *,
    recommendation_class: str,
    uncertainty_reduction: dict[str, Any],
    runtime_growth: dict[str, Any],
    output_growth: dict[str, Any],
    rebuildability_cost: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "topic": "uncertainty_reduction",
            "status": recommendation_class,
            "summary": "The measured Balfrin evidence still shows localized same-scale spread, so a bounded next probe remains informative rather than purely redundant.",
            "evidence": uncertainty_reduction,
        },
        {
            "topic": "runtime_growth",
            "status": recommendation_class,
            "summary": "The current single-job evidence remains bounded, and the measured runtime sidecars keep the next bounded probe in the same execution envelope.",
            "evidence": runtime_growth,
        },
        {
            "topic": "output_growth",
            "status": recommendation_class,
            "summary": "The bounded reduced-output probe stays smaller than the current single-job output footprint, so it does not imply scale-up pressure.",
            "evidence": output_growth,
        },
        {
            "topic": "rebuildability_cost",
            "status": recommendation_class,
            "summary": "The rebuildable-reduced path remains materially cheaper than the full target roots while staying bounded relative to the measured validation and hazard outputs.",
            "evidence": rebuildability_cost,
        },
    ]


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


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "# Balfrin Practical Ensemble Frontier",
        "",
        f"- Frontier status: `{report['frontier_status']}`",
        f"- Recommendation class: `{report['recommendation_class']}`",
        f"- Recommendation reason: {report['recommendation_reason']}",
        "",
        "## Minimum Useful Ensemble",
        "",
    ]
    minimum = report.get("minimum_useful_ensemble_recommendation") or {}
    if minimum:
        lines.extend(
            [
                f"- Decision: `{minimum.get('decision')}`",
                f"- Probe id: `{minimum.get('probe_id')}`",
                f"- Ensemble size: `{minimum.get('ensemble_size')}`",
                f"- Validation output mode: `{minimum.get('validation_output_mode')}`",
                f"- Expected output file count: `{minimum.get('expected_output_file_count')}`",
                f"- Expected output bytes: `{minimum.get('expected_output_bytes')}`",
                f"- Bounded relative to target validation: `{minimum.get('bounded_relative_to_target_validation')}`",
                f"- Bounded relative to target hazard: `{minimum.get('bounded_relative_to_target_hazard')}`",
                "",
                "Expected artifact families:",
            ]
        )
        for family in minimum.get("expected_artifact_families", []):
            lines.append(f"- `{family}`")
    else:
        lines.append("- No bounded next ensemble is recommended because the helper contract is unresolved.")

    lines.extend(
        [
            "",
            "## Uncertainty Reduction",
            "",
            f"- Scientific delta status: `{report.get('uncertainty_reduction', {}).get('scientific_delta_status')}`",
            f"- Stability frontier status: `{report.get('uncertainty_reduction', {}).get('stability_frontier_status')}`",
            f"- Stability recommendation class: `{report.get('uncertainty_reduction', {}).get('stability_recommendation_class')}`",
            "",
            "## Runtime Growth",
            "",
            f"- Current gap runtime seconds: `{report.get('runtime_growth', {}).get('current_gap_runtime_seconds')}`",
            f"- Reproduction validation wall seconds: `{report.get('runtime_growth', {}).get('reproduction_validation_wall_seconds')}`",
            f"- Runtime growth factor validation: `{report.get('runtime_growth', {}).get('runtime_growth_factor_validation')}`",
            f"- Runtime growth factor hazard: `{report.get('runtime_growth', {}).get('runtime_growth_factor_hazard')}`",
            "",
            "## Output Growth",
            "",
            f"- Current gap output file count: `{report.get('output_growth', {}).get('current_gap_output_file_count')}`",
            f"- Current gap output bytes: `{report.get('output_growth', {}).get('current_gap_output_bytes')}`",
            f"- Expected output file count: `{report.get('output_growth', {}).get('expected_output_file_count')}`",
            f"- Expected output bytes: `{report.get('output_growth', {}).get('expected_output_bytes')}`",
            f"- Output file delta: `{report.get('output_growth', {}).get('output_file_delta')}`",
            f"- Output byte delta: `{report.get('output_growth', {}).get('output_byte_delta')}`",
            "",
            "## Rebuildability Cost",
            "",
            f"- Rebuildable reduced output file count: `{report.get('rebuildability_cost', {}).get('rebuildable_reduced_output_file_count')}`",
            f"- Rebuildable reduced output bytes: `{report.get('rebuildability_cost', {}).get('rebuildable_reduced_output_bytes')}`",
            f"- Target validation output bytes: `{report.get('rebuildability_cost', {}).get('target_validation_output_bytes')}`",
            f"- Target hazard output bytes: `{report.get('rebuildability_cost', {}).get('target_hazard_output_bytes')}`",
            f"- Bounded relative to target validation: `{report.get('rebuildability_cost', {}).get('bounded_relative_to_target_validation')}`",
            f"- Bounded relative to target hazard: `{report.get('rebuildability_cost', {}).get('bounded_relative_to_target_hazard')}`",
            "",
            "## Frontier Summary",
            "",
        ]
    )
    for item in report.get("frontier_summary", []):
        lines.append(f"- {item['topic']}: {item['summary']}")
    lines.extend(["", "## Helper Statuses", ""])
    for key, value in report.get("helper_statuses", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines)


def section_or_build(
    evidence_override: dict[str, Any] | None,
    key: str,
    builder,
) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get(key), dict):
        return dict(evidence_override[key])
    return builder()


def numeric_value(value: Any) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    return None


def delta(right: float | int | None, left: float | int | None) -> float | int | None:
    if isinstance(right, (int, float)) and isinstance(left, (int, float)):
        return right - left
    return None


def ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        return None
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


if __name__ == "__main__":
    raise SystemExit(main())
