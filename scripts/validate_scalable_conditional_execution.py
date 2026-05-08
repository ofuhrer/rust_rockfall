#!/usr/bin/env python3
"""Validate a scalable conditional execution decision record.

The record covers conditional hazard-map scaling only. It does not authorize
annual frequency, physical probability, return-period, operational, or risk
products.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


DECISIONS = {"design_ready_not_authorized_for_scale_up", "no_go", "inconclusive"}
REQUIRED_ALLOWED_PRODUCTS = {
    "unweighted_diagnostic",
    "sampling_weighted_conditional",
    "conditional_intensity_exceedance",
}
REQUIRED_REMAINING_BLOCKERS = {
    "target_scale_convergence_not_established",
    "manual_gis_visual_qa_inconclusive",
    "forest_obstacle_omission_limiting",
    "target_scale_output_budget_not_measured",
}
REQUIRED_DIAGNOSTICS = {
    "trajectory_count_sensitivity_between_gate_and_target_count",
    "conditional_curve_stability_by_threshold",
    "supporting_raster_stability",
    "probability_standard_error_layers",
    "worker_count_reducer_parity",
}
REQUIRED_OUTPUT_BUDGET_FIELDS = {
    "output_file_count",
    "output_bytes",
    "total_wall_seconds",
    "hazard_input_rows_per_second",
    "chunk_manifest_count",
}
REQUIRED_MANIFEST_FIELDS = {
    "product_modes",
    "grid_cell_count",
    "conditional_curve_export",
    "reducer",
    "output_budget",
    "convergence_diagnostics",
}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
]


class ScalableConditionalExecutionError(ValueError):
    """User-facing scalable conditional execution validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_scalable_conditional_execution(args.record)
    except ScalableConditionalExecutionError as exc:
        print(f"scalable conditional execution validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "scalable conditional execution record is valid: "
            f"{args.record} ({summary['decision']}, "
            f"blocker_count={summary['remaining_blocker_count']})"
        )
    return 0


def validate_scalable_conditional_execution(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "scalable_conditional_execution_v1",
        "schema_version must be scalable_conditional_execution_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    require(
        record.get("roadmap_item") == "scalable_conditional_intensity_exceedance_pilot",
        "roadmap_item must be scalable_conditional_intensity_exceedance_pilot",
    )
    decision = require_text(record.get("decision"), "decision")
    require(decision in DECISIONS, f"decision must be one of {sorted(DECISIONS)}")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    validate_input_evidence(require_mapping(record.get("input_evidence"), "input_evidence"))
    validate_execution_contract(require_mapping(record.get("execution_contract"), "execution_contract"))
    validate_output_budget(require_mapping(record.get("output_budget"), "output_budget"))
    validate_convergence(require_mapping(record.get("convergence_diagnostics"), "convergence_diagnostics"))
    blockers = set(require_list(record.get("remaining_blockers_before_ensemble_increase"), "remaining_blockers_before_ensemble_increase"))
    missing_blockers = sorted(REQUIRED_REMAINING_BLOCKERS - blockers)
    require(not missing_blockers, f"remaining blockers missing: {missing_blockers}")
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    limitations = require_list(record.get("limitations"), "limitations")
    require(limitations, "limitations must be nonempty")
    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "decision": decision,
        "remaining_blocker_count": len(blockers),
    }


def validate_input_evidence(inputs: dict[str, Any]) -> None:
    for field in (
        "run_freeze_path",
        "ensemble_feasibility_path",
        "scaling_review_path",
        "selected_domain",
        "selected_run_status",
    ):
        require_text(inputs.get(field), f"input_evidence.{field}")
    require(inputs.get("selected_run_status") == "gate_run_completed", "selected_run_status must be gate_run_completed")
    gate = require_positive_int(inputs.get("gate_trajectories_per_release_zone"), "gate_trajectories_per_release_zone")
    proposed = require_positive_int(inputs.get("proposed_trajectories_per_release_zone"), "proposed_trajectories_per_release_zone")
    require(proposed > gate, "proposed trajectories per release zone must exceed the gate count")
    require_positive_int(inputs.get("release_cell_count"), "release_cell_count")


def validate_execution_contract(contract: dict[str, Any]) -> None:
    require(contract.get("status") == "design_ready", "execution_contract.status must be design_ready")
    require(contract.get("runner") == "scripts/build_hazard_layers.py", "execution runner must be scripts/build_hazard_layers.py")
    require(contract.get("runtime_support_added") is True, "execution_contract.runtime_support_added must be true")
    for field in ("changes_physics", "changes_defaults", "changes_sampling_weights"):
        require(contract.get(field) is False, f"execution_contract.{field} must be false")
    chunking = require_mapping(contract.get("deterministic_chunking"), "execution_contract.deterministic_chunking")
    require(chunking.get("status") == "required", "deterministic_chunking.status must be required")
    require(chunking.get("worker_argument") == "--reducer-workers", "deterministic chunking must use --reducer-workers")
    require(chunking.get("chunk_manifest_schema") == "hazard_reducer_chunk_manifest_v1", "chunk manifest schema mismatch")
    require(chunking.get("merge_order") == "sorted_chunk_id", "merge_order must be sorted_chunk_id")
    require(chunking.get("merge_order_independent") is True, "merge must be order independent")
    require(chunking.get("local_threads_only") is True, "only local threads are authorized")
    curves = require_mapping(contract.get("conditional_curve_export"), "execution_contract.conditional_curve_export")
    require(curves.get("required_mode_for_scale_up") == "summary-only", "scale-up must require summary-only curves")
    require(curves.get("full_curve_table_allowed_for_scale_up") is False, "full curve table must not be allowed for scale-up")
    require(curves.get("metadata_summary_required") is True, "metadata summary must remain required")
    manifest = require_mapping(contract.get("manifest_diagnostics"), "execution_contract.manifest_diagnostics")
    require(manifest.get("schema_version") == "conditional_hazard_execution_diagnostics_v1", "manifest diagnostics schema mismatch")
    fields = set(require_list(manifest.get("required_fields"), "manifest_diagnostics.required_fields"))
    missing = sorted(REQUIRED_MANIFEST_FIELDS - fields)
    require(not missing, f"manifest diagnostics required_fields missing: {missing}")


def validate_output_budget(output_budget: dict[str, Any]) -> None:
    require(
        output_budget.get("status") == "design_ready_not_measured_at_target",
        "output_budget.status must be design_ready_not_measured_at_target",
    )
    fields = set(require_list(output_budget.get("required_before_scale_up"), "output_budget.required_before_scale_up"))
    missing_fields = sorted(REQUIRED_OUTPUT_BUDGET_FIELDS - fields)
    require(not missing_fields, f"output budget fields missing: {missing_fields}")
    controls = set(require_list(output_budget.get("controls"), "output_budget.controls"))
    for control in ("summary_only_conditional_curves", "explicit_grid", "generated_outputs_ignored", "no_full_curve_table_for_scale_up"):
        require(control in controls, f"output budget controls missing: {control}")


def validate_convergence(convergence: dict[str, Any]) -> None:
    require(
        convergence.get("status") == "required_before_scale_up",
        "convergence status must be required_before_scale_up",
    )
    required = set(require_list(convergence.get("required_before_increase"), "convergence.required_before_increase"))
    missing = sorted(REQUIRED_DIAGNOSTICS - required)
    require(not missing, f"convergence diagnostics missing: {missing}")
    require(
        convergence.get("current_gate_status") == "insufficient_for_scale_up",
        "current_gate_status must be insufficient_for_scale_up",
    )


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    allowed = set(require_list(boundary.get("current_allowed_product_labels"), "current_allowed_product_labels"))
    missing_allowed = sorted(REQUIRED_ALLOWED_PRODUCTS - allowed)
    require(not missing_allowed, f"current allowed product labels missing: {missing_allowed}")
    for field in ("annualized", "physical_probability", "return_period", "risk_or_exposure", "operational_hazard_map"):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "unsupported_current_claims"))
    for claim in ("annual_frequency", "physical_probability", "return_period", "risk_map", "operational_hazard_map"):
        require(claim in unsupported, f"unsupported_current_claims missing: {claim}")


def scan_text_for_misleading_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"claim_boundary", "unsupported_current_claims"}:
                continue
            scan_text_for_misleading_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("unsupported", "not_", "no_", "no ", "without", "defer", "future", "out of scope", "remain")):
            return
        for pattern in MISLEADING_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise ScalableConditionalExecutionError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScalableConditionalExecutionError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalableConditionalExecutionError(message)


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string")
    return value


def require_positive_int(value: Any, field: str) -> int:
    require(isinstance(value, int) and value > 0, f"{field} must be a positive integer")
    return int(value)


if __name__ == "__main__":
    raise SystemExit(main())
