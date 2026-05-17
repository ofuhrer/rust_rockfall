#!/usr/bin/env python3
"""Summarize the same-scale ensemble stability frontier for the selected Tschamut pilot.

This helper composes the existing same-scale uncertainty, bounded runtime/output,
bounded next-probe feasibility, and closure-gap evidence into one conservative
frontier report. It does not run a new ensemble, change physics, or authorize
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
SCHEMA_VERSION = "tschamut_same_scale_stability_frontier_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise StabilityFrontierError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


UNCERTAINTY = _load_module("same_scale_stability_frontier_uncertainty", "summarize_same_scale_sampling_uncertainty.py")
RUNTIME = _load_module("same_scale_stability_frontier_runtime", "summarize_bounded_reducer_runtime_scaling.py")
FEASIBILITY = _load_module(
    "same_scale_stability_frontier_feasibility", "summarize_bounded_next_ensemble_feasibility_probe.py"
)
CLOSURE_GAP = _load_module("same_scale_stability_frontier_closure_gap", "summarize_tschamut_closure_gap_deltas.py")


class StabilityFrontierError(ValueError):
    """User-facing stability frontier error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report()
    except StabilityFrontierError as exc:
        print(f"same-scale stability frontier error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report), end="")
    return 0 if report["frontier_status"] == "measured_existing_artifacts" else 2


def build_report() -> dict[str, Any]:
    uncertainty = UNCERTAINTY.build_sampling_uncertainty_summary()
    runtime = RUNTIME.build_report(RUNTIME.DEFAULT_ARTIFACTS)
    feasibility = FEASIBILITY.build_report()
    closure_gap = CLOSURE_GAP.build_report()
    bounded_probe_status = str(
        feasibility.get("bounded_probe_recommendation_status")
        or feasibility.get("probe_status")
        or ""
    )

    helper_statuses = {
        "sampling_uncertainty_status": uncertainty.get("sampling_uncertainty_status"),
        "reducer_scaling_status": runtime.get("reducer_scaling_status"),
        "probe_status": bounded_probe_status,
        "closure_gap_status": closure_gap.get("closure_gap_status"),
    }
    helper_blockers = [
        f"{name}={status}"
        for name, status in helper_statuses.items()
        if status not in {
            "sampling_uncertainty_measured",
            "measured_existing_artifacts",
            "deferred_pending_authorization",
            "deferred_pending_optional_probabilistic_metadata",
            "measured_gaps_remain",
        }
    ]
    if helper_blockers:
        return blocked_report(helper_statuses, helper_blockers)

    uncertainty_pairs = index_uncertainty_pairs(uncertainty)
    runtime_pairs = {entry["label"]: entry for entry in runtime.get("comparison_pairs", [])}
    compared_trajectory_counts = build_compared_trajectory_counts(uncertainty, feasibility)
    runtime_output_footprint = build_runtime_output_footprint(runtime, feasibility, runtime_pairs)
    measured_uncertainty_deltas = build_measured_uncertainty_deltas(uncertainty, uncertainty_pairs)
    bounded_probe_feasibility = build_bounded_probe_feasibility(runtime, feasibility)
    closure_gap_context = build_closure_gap_context(closure_gap)
    recommendation_class, recommendation_reason = classify_recommendation(
        uncertainty=uncertainty,
        runtime=runtime,
        feasibility=feasibility,
        closure_gap=closure_gap,
        runtime_pairs=runtime_pairs,
    )

    frontier_summary = [
        "The current same-scale sampling envelope still shows non-zero spread on the dominant layers.",
        "The measured runtime/output footprint remains bounded, and the reduced probe stays far below the target validation root.",
        "The bounded evidence therefore supports another small probe as informative rather than as scale-up pressure.",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "frontier_status": "measured_existing_artifacts",
        "recommendation_class": recommendation_class,
        "recommendation_reason": recommendation_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "helper_statuses": helper_statuses,
        "compared_trajectory_counts": compared_trajectory_counts,
        "runtime_output_footprint": runtime_output_footprint,
        "measured_uncertainty_deltas": measured_uncertainty_deltas,
        "bounded_probe_feasibility": bounded_probe_feasibility,
        "closure_gap_context": closure_gap_context,
        "frontier_summary": frontier_summary,
        "blocked_reason": "none",
    }


def blocked_report(helper_statuses: dict[str, Any], helper_blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "frontier_status": "blocked_pending_helper_contract",
        "recommendation_class": "blocked_pending_helper_contract",
        "recommendation_reason": "helper contract unresolved: " + ", ".join(helper_blockers),
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "helper_statuses": helper_statuses,
        "compared_trajectory_counts": [],
        "runtime_output_footprint": [],
        "measured_uncertainty_deltas": {},
        "bounded_probe_feasibility": {},
        "closure_gap_context": {},
        "frontier_summary": [],
        "blocked_reason": "helper contract unresolved: " + ", ".join(helper_blockers),
    }


def index_uncertainty_pairs(uncertainty: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in uncertainty.get("comparison_pairs_run", []):
        reference = normalize_artifact_id(str(entry.get("reference_artifact_id") or ""))
        compare = normalize_artifact_id(str(entry.get("compare_artifact_id") or ""))
        if reference and compare:
            pairs[(reference, compare)] = entry
            pairs[(compare, reference)] = entry
    return pairs


def normalize_artifact_id(artifact_id: str) -> str:
    if artifact_id.startswith("validation_tschamut_public_conditional_gate_v1"):
        return "gate_v1"
    if artifact_id.startswith("validation_tschamut_public_target_gate_v1"):
        return "target_gate_v1"
    if artifact_id.startswith("validation_tschamut_public_sampling_sensitivity_v1_full"):
        return "sampling_sensitivity_v1_full"
    if artifact_id.startswith("validation_tschamut_public_sampling_sensitivity_v2_full"):
        return "sampling_sensitivity_v2_full"
    if artifact_id.startswith("validation_tschamut_public_"):
        return artifact_id.removeprefix("validation_tschamut_public_")
    return artifact_id


def build_compared_trajectory_counts(uncertainty: dict[str, Any], feasibility: dict[str, Any]) -> list[dict[str, Any]]:
    ensemble_sizes = {
        normalize_artifact_id(str(artifact_id)): ensemble_size
        for artifact_id, ensemble_size in zip(uncertainty.get("artifact_ids", []), uncertainty.get("ensemble_sizes", []))
    }
    proposed_probe = dict(feasibility.get("proposed_probe") or {})
    proposed_trajectory_count = proposed_probe.get("trajectory_count")
    if proposed_trajectory_count is None:
        proposed_trajectory_count = proposed_probe.get("ensemble_size")

    compared_counts = [
        {"comparison_label": "gate_vs_target", "left_trajectory_count": ensemble_sizes.get("gate_v1"), "right_trajectory_count": ensemble_sizes.get("target_gate_v1")},
        {
            "comparison_label": "sampling_probe_v1_vs_v2",
            "left_trajectory_count": ensemble_sizes.get("sampling_sensitivity_v1_full"),
            "right_trajectory_count": ensemble_sizes.get("sampling_sensitivity_v2_full"),
        },
        {
            "comparison_label": "target_full_vs_native_rebuildable_reduced",
            "left_trajectory_count": ensemble_sizes.get("target_gate_v1"),
            "right_trajectory_count": proposed_trajectory_count,
        },
    ]
    for item in compared_counts:
        left = item.get("left_trajectory_count")
        right = item.get("right_trajectory_count")
        item["trajectory_count_delta"] = (right - left) if isinstance(left, int) and isinstance(right, int) else None
    return compared_counts


def build_runtime_output_footprint(
    runtime: dict[str, Any],
    feasibility: dict[str, Any],
    runtime_pairs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    proposed_probe = dict(feasibility.get("proposed_probe") or {})
    boundedness = dict(feasibility.get("boundedness_proof") or {})
    return [
        {
            "comparison_label": "gate_vs_target",
            "runtime_delta_seconds": runtime_pairs.get("gate_vs_target", {}).get("validation_runtime_delta_seconds"),
            "validation_output_file_count_delta": runtime_pairs.get("gate_vs_target", {}).get("validation_file_count_delta"),
            "validation_output_byte_count_delta": runtime_pairs.get("gate_vs_target", {}).get("byte_count_delta"),
            "hazard_output_file_count_delta": runtime_pairs.get("gate_vs_target", {}).get("hazard_file_count_delta"),
            "hazard_output_byte_count_delta": runtime_pairs.get("gate_vs_target", {}).get("hazard_byte_count_delta"),
        },
        {
            "comparison_label": "sampling_probe_v1_vs_v2",
            "runtime_delta_seconds": runtime_pairs.get("sampling_probe_v1_vs_v2", {}).get("validation_runtime_delta_seconds"),
            "validation_output_file_count_delta": runtime_pairs.get("sampling_probe_v1_vs_v2", {}).get("validation_file_count_delta"),
            "validation_output_byte_count_delta": runtime_pairs.get("sampling_probe_v1_vs_v2", {}).get("byte_count_delta"),
            "hazard_output_file_count_delta": runtime_pairs.get("sampling_probe_v1_vs_v2", {}).get("hazard_file_count_delta"),
            "hazard_output_byte_count_delta": runtime_pairs.get("sampling_probe_v1_vs_v2", {}).get("hazard_byte_count_delta"),
        },
        {
            "comparison_label": "target_full_vs_native_rebuildable_reduced",
            "runtime_delta_seconds": runtime_pairs.get("target_full_vs_native_rebuildable_reduced", {}).get(
                "validation_runtime_delta_seconds"
            ),
            "validation_output_file_count_delta": runtime_pairs.get("target_full_vs_native_rebuildable_reduced", {}).get(
                "validation_file_count_delta"
            ),
            "validation_output_byte_count_delta": runtime_pairs.get("target_full_vs_native_rebuildable_reduced", {}).get(
                "byte_count_delta"
            ),
            "hazard_output_file_count_delta": runtime_pairs.get("target_full_vs_native_rebuildable_reduced", {}).get(
                "hazard_file_count_delta"
            ),
            "hazard_output_byte_count_delta": runtime_pairs.get("target_full_vs_native_rebuildable_reduced", {}).get(
                "hazard_byte_count_delta"
            ),
            "proposed_probe_trajectory_count": proposed_probe.get("trajectory_count"),
            "proposed_probe_output_file_count": proposed_probe.get("expected_output_file_count"),
            "proposed_probe_output_bytes": proposed_probe.get("expected_output_bytes"),
            "bounded_relative_to_target_validation": boundedness.get("bounded_relative_to_target_validation"),
            "bounded_relative_to_target_hazard": boundedness.get("bounded_relative_to_target_hazard"),
        },
    ]


def build_measured_uncertainty_deltas(
    uncertainty: dict[str, Any],
    pair_index: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    dominant = uncertainty.get("dominant_layer_spread") or {}
    gate_target = pair_index.get(("gate_v1", "target_gate_v1"), {})
    sampling_probe = pair_index.get(("sampling_sensitivity_v1_full", "sampling_sensitivity_v2_full"), {})
    layer_metrics = sampling_probe.get("layer_metrics") or {}
    selected_layers = {
        layer_key: layer_metrics.get(layer_key)
        for layer_key in ("max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps")
        if layer_metrics.get(layer_key) is not None
    }
    return {
        "pairwise_comparison_count": uncertainty.get("pairwise_comparison_count"),
        "shared_cellwise_layer_counts": uncertainty.get("shared_cellwise_layer_counts"),
        "dominant_layer_spread": {
            "max_kinetic_energy": dominant.get("max_kinetic_energy"),
            "max_jump_height": dominant.get("max_jump_height"),
            "velocity_exceedance_5mps": dominant.get("velocity_exceedance_5mps"),
        },
        "support_or_nodata_sensitivity": uncertainty.get("support_or_nodata_sensitivity"),
        "gate_vs_target_pair": summarize_pair_metrics(gate_target) if gate_target else {},
        "sampling_probe_v1_vs_v2_pair": summarize_pair_metrics(sampling_probe) if sampling_probe else {},
        "sampling_probe_v1_vs_v2_layers": selected_layers,
    }


def summarize_pair_metrics(pair: dict[str, Any]) -> dict[str, Any]:
    if not pair:
        return {}
    return {
        "comparison_status": pair.get("status"),
        "shared_cellwise_layer_count": pair.get("shared_cellwise_layer_count"),
        "cellwise_l1_abs_diff_sum": pair.get("cellwise_l1_abs_diff_sum"),
        "cellwise_linf_abs_diff_max": pair.get("cellwise_linf_abs_diff_max"),
        "cellwise_rmse_max": pair.get("cellwise_rmse_max"),
        "cellwise_nonzero_jaccard_min": pair.get("cellwise_nonzero_jaccard_min"),
        "cellwise_nodata_mismatch_count": pair.get("cellwise_nodata_mismatch_count"),
        "output_checksum_match_count": pair.get("output_checksum_match_count"),
        "output_checksum_mismatch_count": pair.get("output_checksum_mismatch_count"),
        "output_checksum_missing_count": pair.get("output_checksum_missing_count"),
    }


def build_bounded_probe_feasibility(runtime: dict[str, Any], feasibility: dict[str, Any]) -> dict[str, Any]:
    proposed_probe = dict(feasibility.get("proposed_probe") or {})
    boundedness = dict(feasibility.get("boundedness_proof") or {})
    runtime_benefit = next(
        (entry for entry in runtime.get("comparison_pairs", []) if entry.get("label") == "target_full_vs_native_rebuildable_reduced"),
        {},
    )
    bounded_probe_status = feasibility.get("bounded_probe_recommendation_status") or feasibility.get("probe_status")
    return {
        "probe_status": feasibility.get("probe_status"),
        "bounded_probe_recommendation_status": bounded_probe_status,
        "planning_status": feasibility.get("planning_status"),
        "proposed_probe": {
            "probe_id": proposed_probe.get("probe_id"),
            "trajectory_count": proposed_probe.get("trajectory_count"),
            "validation_output_mode": proposed_probe.get("validation_output_mode"),
            "expected_output_file_count": proposed_probe.get("expected_output_file_count"),
            "expected_output_bytes": proposed_probe.get("expected_output_bytes"),
        },
        "boundedness_proof": {
            "bounded_relative_to_target_validation": boundedness.get("bounded_relative_to_target_validation"),
            "bounded_relative_to_target_hazard": boundedness.get("bounded_relative_to_target_hazard"),
            "output_byte_ratio_to_target_validation": boundedness.get("output_byte_ratio_to_target_validation"),
            "output_file_ratio_to_target_validation": boundedness.get("output_file_ratio_to_target_validation"),
            "output_byte_ratio_to_target_hazard": boundedness.get("output_byte_ratio_to_target_hazard"),
            "output_file_ratio_to_target_hazard": boundedness.get("output_file_ratio_to_target_hazard"),
        },
        "runtime_benefit": {
            "validation_runtime_delta_seconds": runtime_benefit.get("validation_runtime_delta_seconds"),
            "validation_file_count_delta": runtime_benefit.get("validation_file_count_delta"),
            "byte_count_delta": runtime_benefit.get("byte_count_delta"),
        },
    }


def build_closure_gap_context(closure_gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "closure_gap_status": closure_gap.get("closure_gap_status"),
        "current_closure_status": closure_gap.get("current_closure_status"),
        "current_interpretation_status": closure_gap.get("current_interpretation_status"),
        "closure_limiting_layers": closure_gap.get("closure_limiting_layers"),
        "deferrable_layers": closure_gap.get("deferrable_layers"),
        "scientific_blocker_deltas": closure_gap.get("scientific_blocker_deltas"),
        "workflow_product_blocker_deltas": closure_gap.get("workflow_product_blocker_deltas"),
        "claim_boundaries": closure_gap.get("claim_boundaries"),
    }


def classify_recommendation(
    *,
    uncertainty: dict[str, Any],
    runtime: dict[str, Any],
    feasibility: dict[str, Any],
    closure_gap: dict[str, Any],
    runtime_pairs: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    if any(status == "blocked_missing_inputs" for status in (uncertainty.get("sampling_uncertainty_status"), runtime.get("reducer_scaling_status"), closure_gap.get("closure_gap_status"))):
        return "blocked_pending_helper_contract", "one or more helper summaries are blocked on missing inputs"
    if feasibility.get("probe_status") == "blocked_pending_evidence":
        return "blocked_pending_helper_contract", "bounded next-probe helper is still blocked on evidence"

    probe_pair = runtime_pairs.get("sampling_probe_v1_vs_v2", {})
    probe_runtime_delta = abs(float(probe_pair.get("validation_runtime_delta_seconds") or 0.0))
    probe_byte_delta = abs(int(probe_pair.get("byte_count_delta") or 0))
    dominant = uncertainty.get("dominant_layer_spread") or {}
    max_ke = dominant.get("max_kinetic_energy") or {}
    max_jump = dominant.get("max_jump_height") or {}
    ke_mean = float((max_ke.get("l1_abs_diff") or {}).get("mean") or 0.0)
    jump_mean = float((max_jump.get("l1_abs_diff") or {}).get("mean") or 0.0)
    boundedness = dict(feasibility.get("boundedness_proof") or {})

    if (
        boundedness.get("bounded_relative_to_target_validation")
        and boundedness.get("bounded_relative_to_target_hazard")
        and runtime.get("local_single_job_sufficient_for_next_step") is True
        and ke_mean > 0.0
        and jump_mean > 0.0
        and (probe_runtime_delta > 0.0 or probe_byte_delta > 0)
    ):
        return (
            "additional_probe_informative",
            "the same-scale uncertainty envelope still has measurable spread while the probe footprint remains bounded and local",
        )

    return (
        "additional_probe_low_value",
        "the current same-scale evidence is already bounded enough that another small probe is unlikely to change the frontier materially",
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "# Same-Scale Ensemble Stability Frontier",
        f"- Frontier status: `{report['frontier_status']}`",
        f"- Recommendation: `{report['recommendation_class']}`",
        f"- Reason: {report['recommendation_reason']}",
        "- Compared trajectory counts:",
    ]
    for item in report.get("compared_trajectory_counts", []):
        lines.append(
            "  - "
            f"{item['comparison_label']}: left `{item.get('left_trajectory_count')}`, "
            f"right `{item.get('right_trajectory_count')}`, delta `{item.get('trajectory_count_delta')}`"
        )
    lines.append("- Runtime/output footprint:")
    for item in report.get("runtime_output_footprint", []):
        lines.append(
            "  - "
            f"{item['comparison_label']}: runtime delta `{item.get('runtime_delta_seconds')}`, "
            f"validation bytes delta `{item.get('validation_output_byte_count_delta')}`, "
            f"validation files delta `{item.get('validation_output_file_count_delta')}`"
        )
    lines.append("- Uncertainty deltas:")
    uncertainty = report.get("measured_uncertainty_deltas") or {}
    dominant = uncertainty.get("dominant_layer_spread") or {}
    for layer_key in ("max_kinetic_energy", "max_jump_height", "velocity_exceedance_5mps"):
        layer = dominant.get(layer_key) or {}
        l1 = layer.get("l1_abs_diff") or {}
        lines.append(
            "  - "
            f"{layer_key}: l1 mean `{l1.get('mean')}`, l1 range `{l1.get('range')}`, "
            f"jaccard mean `{(layer.get('nonzero_jaccard') or {}).get('mean')}`"
        )
    bounded = report.get("bounded_probe_feasibility") or {}
    lines.append("- Bounded probe feasibility:")
    lines.append(
        "  - "
        f"proposed probe trajectory count `{(bounded.get('proposed_probe') or {}).get('trajectory_count')}`, "
        f"expected output bytes `{(bounded.get('proposed_probe') or {}).get('expected_output_bytes')}`, "
        f"bounded relative to target validation `{(bounded.get('boundedness_proof') or {}).get('bounded_relative_to_target_validation')}`"
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
