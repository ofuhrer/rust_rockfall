#!/usr/bin/env python3
"""Validate the selected scalable conditional target-scale gate record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_GATE_STATUSES = {"blocked_missing_inputs", "target_scale_executed", "inconclusive"}
REQUIRED_ALLOWED_PRODUCTS = {
    "unweighted_diagnostic",
    "sampling_weighted_conditional",
    "conditional_intensity_exceedance",
}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "physical_probability",
    "return_period",
    "risk_map",
    "operational_hazard_map",
}
REQUIRED_UPSTREAM_RECORDS = {
    "small_gate_run_freeze",
    "scalable_execution_contract",
    "ensemble_feasibility_gate",
    "scaling_review",
    "geodata_manifest",
    "source_scenario_policy",
}
REQUIRED_MISSING_ROLES = {
    "frozen_private_validation_case",
    "processed_public_dem_metadata",
    "selected_scenario_table",
    "prior_gate_trajectory_directory",
    "prior_gate_hazard_manifest",
}
REQUIRED_EXECUTED_ROLES = {
    "frozen_private_validation_case",
    "processed_public_dem_metadata",
    "selected_scenario_table",
    "source_zone_metadata",
    "target_validation_manifest",
    "target_hazard_manifest",
}
REQUIRED_BLOCKED_REMAINING_STEPS = {
    "restore_or_regenerate_ignored_processed_dem_and_private_case",
    "run_validation_case_with_random_ensemble_workers",
    "build_hazard_layers_with_summary_only_curves",
    "record_conditional_hazard_execution_diagnostics",
    "record_output_budget_runtime_memory_and_checksums",
    "record_worker_count_parity",
    "compare_target_scale_outputs_against_small_gate",
    "keep_manual_gis_visual_qa_and_obstacle_context_limitations_visible",
}
REQUIRED_INCONCLUSIVE_REMAINING_STEPS = {
    "accept_or_reject_target_vs_small_gate_convergence",
    "complete_manual_gis_visual_qa",
    "resolve_or_bound_forest_obstacle_context_limitation",
    "reduce_or_justify_validation_debug_output_volume",
    "keep_manual_gis_visual_qa_and_obstacle_context_limitations_visible",
}
MISLEADING_PATTERNS = [
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
]


class ScalableConditionalTargetGateError(ValueError):
    """User-facing target gate validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_target_gate_record(args.record)
    except ScalableConditionalTargetGateError as exc:
        print(f"scalable conditional target gate validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "scalable conditional target gate record is valid: "
            f"{args.record} ({summary['gate_status']}, "
            f"missing_path_count={summary['missing_path_count']})"
        )
    return 0


def validate_target_gate_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "scalable_conditional_target_gate_v1",
        "schema_version must be scalable_conditional_target_gate_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    require(
        record.get("roadmap_item") == "target_11_scalable_conditional_target_scale_gate",
        "roadmap_item must be target_11_scalable_conditional_target_scale_gate",
    )
    gate_status = require_text(record.get("gate_status"), "gate_status")
    require(gate_status in SUPPORTED_GATE_STATUSES, f"gate_status must be one of {sorted(SUPPORTED_GATE_STATUSES)}")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    validate_upstream_records(require_mapping(record.get("upstream_records"), "upstream_records"))
    validate_target_execution_plan(require_mapping(record.get("target_execution_plan"), "target_execution_plan"))
    missing_path_count = validate_local_input_check(
        require_mapping(record.get("local_input_check"), "local_input_check"),
        gate_status,
    )
    validate_evidence_result(require_mapping(record.get("evidence_result"), "evidence_result"), gate_status)
    if gate_status != "blocked_missing_inputs":
        validate_target_run_provenance_policy(
            require_mapping(
                record.get("target_run_provenance_policy"),
                "target_run_provenance_policy",
            )
        )
        validate_output_profile_policy(
            require_mapping(record.get("output_profile_policy"), "output_profile_policy")
        )
    remaining = set(require_list(record.get("remaining_before_gate_reassessment"), "remaining_before_gate_reassessment"))
    required_remaining = (
        REQUIRED_BLOCKED_REMAINING_STEPS
        if gate_status == "blocked_missing_inputs"
        else REQUIRED_INCONCLUSIVE_REMAINING_STEPS
    )
    missing_remaining = sorted(required_remaining - remaining)
    require(not missing_remaining, f"remaining_before_gate_reassessment missing: {missing_remaining}")
    if gate_status != "blocked_missing_inputs":
        validate_execution_evidence(require_mapping(record.get("execution_evidence"), "execution_evidence"))
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    limitations = require_list(record.get("limitations"), "limitations")
    require(limitations, "limitations must be nonempty")
    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "gate_status": gate_status,
        "missing_path_count": missing_path_count,
    }


def validate_upstream_records(records: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_UPSTREAM_RECORDS - set(records))
    require(not missing, f"upstream_records missing: {missing}")
    for field in REQUIRED_UPSTREAM_RECORDS:
        require_text(records.get(field), f"upstream_records.{field}")


def validate_target_execution_plan(plan: dict[str, Any]) -> None:
    require(plan.get("selected_domain") == "tschamut_public_pilot", "selected_domain must be tschamut_public_pilot")
    gate_count = require_positive_int(plan.get("gate_trajectories_per_release_zone"), "gate_trajectories_per_release_zone")
    target_count = require_positive_int(plan.get("target_trajectories_per_release_zone"), "target_trajectories_per_release_zone")
    require(target_count > gate_count, "target trajectories per release zone must exceed gate count")
    require_positive_int(plan.get("release_cell_count"), "release_cell_count")
    require(plan.get("validation_runner_ensemble_workers_required") is True, "validation runner ensemble workers must be required")
    require_positive_int(plan.get("validation_runner_ensemble_workers"), "validation_runner_ensemble_workers")
    require_positive_int(plan.get("hazard_reducer_workers"), "hazard_reducer_workers")
    require(plan.get("conditional_curve_export_mode") == "summary-only", "conditional_curve_export_mode must be summary-only")
    require(plan.get("probability_mode") == "sampling_weighted_conditional", "probability_mode must be sampling_weighted_conditional")
    require(plan.get("explicit_grid_required") is True, "explicit_grid_required must be true")
    for field in ("generated_outputs_committed", "changes_physics", "changes_defaults", "changes_sampling_weights"):
        require(plan.get(field) is False, f"target_execution_plan.{field} must be false")


def validate_local_input_check(local_check: dict[str, Any], gate_status: str) -> int:
    required_paths = require_list(local_check.get("required_paths"), "local_input_check.required_paths")
    if gate_status == "blocked_missing_inputs":
        require(
            local_check.get("check_status") == "failed_missing_ignored_inputs",
            "blocked records must use check_status failed_missing_ignored_inputs",
        )
        require(local_check.get("target_execution_started") is False, "blocked records must not start target execution")
        require(local_check.get("generated_outputs_written") is False, "blocked records must not write generated outputs")
        missing_roles = {
            require_text(require_mapping(row, "required_path").get("role"), "required_path.role")
            for row in required_paths
            if require_mapping(row, "required_path").get("status") == "missing"
        }
        missing_required = sorted(REQUIRED_MISSING_ROLES - missing_roles)
        require(not missing_required, f"blocked record missing required missing path roles: {missing_required}")
    else:
        require(
            local_check.get("check_status") == "restored_or_regenerated",
            "executed or inconclusive records must use check_status restored_or_regenerated",
        )
        require(local_check.get("target_execution_started") is True, "executed or inconclusive records must start target execution")
        require(local_check.get("generated_outputs_written") is True, "executed or inconclusive records must write ignored outputs")
        roles = {
            require_text(require_mapping(row, "required_path").get("role"), "required_path.role")
            for row in required_paths
        }
        missing_roles = sorted(REQUIRED_EXECUTED_ROLES - roles)
        require(not missing_roles, f"executed or inconclusive record missing required path roles: {missing_roles}")
        for row in required_paths:
            row = require_mapping(row, "required_path")
            require(row.get("status") != "missing", "executed or inconclusive records must not list missing required paths")
    require(local_check.get("command_plan_validated") is True, "command_plan_validated must be true")
    return sum(1 for row in required_paths if isinstance(row, dict) and row.get("status") == "missing")


def validate_evidence_result(evidence: dict[str, Any], gate_status: str) -> None:
    status = require_text(evidence.get("evidence_status"), "evidence_result.evidence_status")
    require(status == gate_status, "evidence_status must match gate_status")
    if gate_status == "blocked_missing_inputs":
        require(evidence.get("target_scale_executed") is False, "blocked records must not mark target_scale_executed")
        for field, expected in (
            ("convergence_diagnostics_status", "not_recorded"),
            ("output_budget_status", "not_recorded"),
            ("worker_count_parity_status", "not_run"),
            ("reducer_manifest_status", "not_generated"),
            ("ensemble_execution_manifest_status", "not_generated"),
        ):
            require(evidence.get(field) == expected, f"evidence_result.{field} must be {expected}")
    else:
        require(evidence.get("target_scale_executed") is True, "executed or inconclusive records must mark target_scale_executed")
        require(evidence.get("output_budget_status") == "recorded", "output_budget_status must be recorded")
        require(evidence.get("worker_count_parity_status") != "not_run", "worker_count_parity_status must not be not_run")
        require(evidence.get("reducer_manifest_status") == "generated", "reducer_manifest_status must be generated")
        require(
            evidence.get("ensemble_execution_manifest_status")
            in {"generated", "partial_auxiliary_single_release_only"},
            "ensemble_execution_manifest_status must be generated or partial_auxiliary_single_release_only",
        )
    require_text(evidence.get("interpretation"), "evidence_result.interpretation")


def validate_target_run_provenance_policy(policy: dict[str, Any]) -> None:
    require(
        policy.get("schema_version") == "target_run_provenance_policy_v1",
        "target_run_provenance_policy.schema_version must be target_run_provenance_policy_v1",
    )
    require(
        policy.get("policy_status") == "closed_for_current_gate_with_caveat",
        "target_run_provenance_policy.policy_status must be closed_for_current_gate_with_caveat",
    )
    observed = require_mapping(
        policy.get("observed_release_target_run"),
        "target_run_provenance_policy.observed_release_target_run",
    )
    require(
        observed.get("scope_label") == "observed_release_target_run",
        "observed_release_target_run.scope_label must be observed_release_target_run",
    )
    require_positive_int(observed.get("release_count"), "observed_release_target_run.release_count")
    require_positive_int(
        observed.get("simulated_trajectory_count"),
        "observed_release_target_run.simulated_trajectory_count",
    )
    require(
        observed.get("represents_full_target_run") is True,
        "observed_release_target_run.represents_full_target_run must be true",
    )
    sources = set(
        require_list(
            observed.get("provenance_sources"),
            "observed_release_target_run.provenance_sources",
        )
    )
    missing_sources = sorted(
        {"validation_run_manifest", "validation_metrics", "per_trajectory_outputs"} - sources
    )
    require(not missing_sources, f"observed_release_target_run.provenance_sources missing: {missing_sources}")

    auxiliary = require_mapping(
        policy.get("auxiliary_ensemble_execution"),
        "target_run_provenance_policy.auxiliary_ensemble_execution",
    )
    require(auxiliary.get("present") is True, "auxiliary_ensemble_execution.present must be true")
    require(
        auxiliary.get("schema_version") == "local_parallel_ensemble_v1",
        "auxiliary_ensemble_execution.schema_version must be local_parallel_ensemble_v1",
    )
    require(
        auxiliary.get("scope_label") == "auxiliary_single_release_ensemble_path",
        "auxiliary_ensemble_execution.scope_label must be auxiliary_single_release_ensemble_path",
    )
    require_positive_int(
        auxiliary.get("trajectory_count"),
        "auxiliary_ensemble_execution.trajectory_count",
    )
    require(
        auxiliary.get("may_be_interpreted_as_full_observed_release_target_provenance") is False,
        "auxiliary ensemble_execution must not be interpreted as full observed-release target provenance",
    )
    require_text(policy.get("interpretation"), "target_run_provenance_policy.interpretation")
    require(
        policy.get("ensemble_size_increase_authorized") is False,
        "target_run_provenance_policy.ensemble_size_increase_authorized must be false",
    )


def validate_output_profile_policy(policy: dict[str, Any]) -> None:
    require(
        policy.get("schema_version") == "selected_output_profile_policy_v1",
        "output_profile_policy.schema_version must be selected_output_profile_policy_v1",
    )
    require(
        policy.get("policy_status") == "closed_for_current_gate",
        "output_profile_policy.policy_status must be closed_for_current_gate",
    )
    require(
        policy.get("profile_contract") == "docs/hazard_output_profile_contract.md",
        "output_profile_policy.profile_contract must reference docs/hazard_output_profile_contract.md",
    )
    current = require_mapping(
        policy.get("current_target_gate_profile"),
        "output_profile_policy.current_target_gate_profile",
    )
    require(
        current.get("profile") == "custom_or_mixed_legacy_summary_only",
        "current_target_gate_profile.profile must be custom_or_mixed_legacy_summary_only",
    )
    require_text(current.get("classification_reason"), "current_target_gate_profile.classification_reason")
    require(
        current.get("conditional_curve_export_mode") == "summary-only",
        "current_target_gate_profile.conditional_curve_export_mode must be summary-only",
    )
    require(
        current.get("grid_csv_export_mode") == "legacy_default_full_or_unrecorded",
        "current_target_gate_profile.grid_csv_export_mode must be legacy_default_full_or_unrecorded",
    )
    require(current.get("plots_enabled") is False, "current_target_gate_profile.plots_enabled must be false")
    require(
        current.get("generated_outputs_committed") is False,
        "current_target_gate_profile.generated_outputs_committed must be false",
    )
    followup = require_mapping(
        policy.get("selected_followup_profile"),
        "output_profile_policy.selected_followup_profile",
    )
    require(
        followup.get("profile") == "scalable_conditional",
        "selected_followup_profile.profile must be scalable_conditional",
    )
    controls = set(require_list(followup.get("required_controls"), "selected_followup_profile.required_controls"))
    missing_controls = sorted(
        {"--conditional-curve-export summary-only", "--grid-csv-export none", "--no-plots"} - controls
    )
    require(not missing_controls, f"selected_followup_profile.required_controls missing: {missing_controls}")
    require_text(followup.get("rationale"), "selected_followup_profile.rationale")
    audit = require_mapping(
        policy.get("provenance_audit_profile_allowed_when"),
        "output_profile_policy.provenance_audit_profile_allowed_when",
    )
    require(
        audit.get("profile") == "provenance_audit",
        "provenance_audit_profile_allowed_when.profile must be provenance_audit",
    )
    require_text(audit.get("condition"), "provenance_audit_profile_allowed_when.condition")
    debug = require_mapping(
        policy.get("validation_debug_output_budget"),
        "output_profile_policy.validation_debug_output_budget",
    )
    require(
        debug.get("status") == "blocker_retained",
        "validation_debug_output_budget.status must be blocker_retained",
    )
    require_positive_int(
        debug.get("target_validation_output_file_count"),
        "validation_debug_output_budget.target_validation_output_file_count",
    )
    require_positive_int(
        debug.get("target_validation_output_total_bytes"),
        "validation_debug_output_budget.target_validation_output_total_bytes",
    )
    require(
        debug.get("acceptable_for_next_scale_increase_without_reduction_or_justification") is False,
        "validation debug output budget must remain a blocker before another scale increase",
    )


def validate_execution_evidence(evidence: dict[str, Any]) -> None:
    validate_regenerated_inputs(require_mapping(evidence.get("regenerated_inputs"), "execution_evidence.regenerated_inputs"))
    validate_validation_run_evidence(require_mapping(evidence.get("validation_run"), "execution_evidence.validation_run"))
    validate_hazard_run_evidence(require_mapping(evidence.get("hazard_run"), "execution_evidence.hazard_run"))
    validate_worker_parity(require_mapping(evidence.get("worker_parity"), "execution_evidence.worker_parity"))


def validate_regenerated_inputs(inputs: dict[str, Any]) -> None:
    require_text(inputs.get("preparation_command"), "regenerated_inputs.preparation_command")
    require(inputs.get("geodata_manifest_validation") == "pass", "geodata_manifest_validation must be pass")
    require(inputs.get("raw_public_inputs_already_present") is True, "raw public inputs must be recorded present")
    require(inputs.get("raw_or_generated_inputs_committed") is False, "raw or generated inputs must not be committed")


def validate_validation_run_evidence(run: dict[str, Any]) -> None:
    for field in ("case_path", "manifest_path", "metrics_path", "timing_sidecar_path", "manifest_sha256"):
        require_text(run.get(field), f"validation_run.{field}")
    require(run.get("command_returncode") == 0, "validation_run.command_returncode must be 0")
    require_positive_int(run.get("validation_release_count"), "validation_release_count")
    require_positive_int(run.get("validation_simulated_trajectory_count"), "validation_simulated_trajectory_count")
    require_positive_number(run.get("wall_seconds"), "validation_run.wall_seconds")
    require_positive_int(run.get("memory_peak_bytes_on_darwin"), "validation_run.memory_peak_bytes_on_darwin")
    require_positive_int(run.get("output_file_count"), "validation_run.output_file_count")
    require_positive_int(run.get("output_total_bytes"), "validation_run.output_total_bytes")
    require(run.get("ensemble_execution_schema") == "local_parallel_ensemble_v1", "ensemble execution schema must be local_parallel_ensemble_v1")
    require_positive_int(run.get("ensemble_execution_trajectory_count"), "ensemble_execution_trajectory_count")
    require_text(run.get("ensemble_execution_scope_note"), "validation_run.ensemble_execution_scope_note")


def validate_hazard_run_evidence(run: dict[str, Any]) -> None:
    for field in (
        "manifest_path",
        "evidence_summary_path",
        "map_package_manifest_path",
        "pilot_gis_package_manifest_path",
        "timing_sidecar_path",
        "manifest_sha256",
    ):
        require_text(run.get(field), f"hazard_run.{field}")
    require(run.get("command_returncode") == 0, "hazard_run.command_returncode must be 0")
    require_positive_int(run.get("reducer_workers"), "hazard_run.reducer_workers")
    require_positive_int(run.get("reducer_chunk_count"), "hazard_run.reducer_chunk_count")
    require(run.get("reducer_merge_order") == "sorted_chunk_id", "hazard reducer merge order must be sorted_chunk_id")
    require(run.get("conditional_curve_export_mode") == "summary-only", "hazard conditional curve export must be summary-only")
    require_positive_int(run.get("conditional_curve_rows_suppressed"), "conditional_curve_rows_suppressed")
    require_positive_number(run.get("wall_seconds"), "hazard_run.wall_seconds")
    require_positive_int(run.get("memory_peak_bytes_on_darwin"), "hazard_run.memory_peak_bytes_on_darwin")
    require_positive_int(run.get("output_file_count"), "hazard_run.output_file_count")
    require_positive_int(run.get("output_total_bytes"), "hazard_run.output_total_bytes")
    require_positive_int(run.get("total_hazard_input_rows_read"), "hazard_run.total_hazard_input_rows_read")


def validate_worker_parity(parity: dict[str, Any]) -> None:
    require_text(parity.get("comparison_output_dir"), "worker_parity.comparison_output_dir")
    counts = require_list(parity.get("worker_counts_compared"), "worker_parity.worker_counts_compared")
    require(set(counts) == {1, 2}, "worker parity must compare worker counts 1 and 2")
    compared = require_mapping(parity.get("compared_output_kinds"), "worker_parity.compared_output_kinds")
    require(compared.get("hazard_layer") is True, "worker parity must match hazard_layer outputs")
    require(compared.get("deposition_points") is True, "worker parity must match deposition_points outputs")
    require(parity.get("all_compared_outputs_match") is True, "all compared worker-parity outputs must match")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    allowed = set(require_list(boundary.get("current_allowed_product_labels"), "current_allowed_product_labels"))
    missing_allowed = sorted(REQUIRED_ALLOWED_PRODUCTS - allowed)
    require(not missing_allowed, f"current allowed product labels missing: {missing_allowed}")
    for field in ("annualized", "physical_probability", "return_period", "risk_or_exposure", "operational_hazard_map"):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "unsupported_current_claims"))
    missing_unsupported = sorted(REQUIRED_UNSUPPORTED_CLAIMS - unsupported)
    require(not missing_unsupported, f"unsupported_current_claims missing: {missing_unsupported}")


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
        if any(
            marker in lower
            for marker in (
                "unsupported",
                "not_",
                "no_",
                "no ",
                "without",
                "defer",
                "future",
                "out of scope",
                "remain",
                "blocked",
                "missing",
            )
        ):
            return
        for pattern in MISLEADING_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - keep path context.
        raise ScalableConditionalTargetGateError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScalableConditionalTargetGateError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalableConditionalTargetGateError(message)


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


def require_positive_number(value: Any, field: str) -> float:
    require(isinstance(value, int | float) and value > 0, f"{field} must be a positive number")
    return float(value)


if __name__ == "__main__":
    raise SystemExit(main())
