#!/usr/bin/env python3
"""Validate the selected balfrin SLURM probe repeatability record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_CONTROLS = {
    "single_job_slurm_driver",
    "trajectory_workers_2",
    "reducer_workers_2",
    "conditional_curve_export_summary_only",
    "grid_csv_export_none",
    "no_plots",
    "generated_outputs_ignored",
}
REQUIRED_NOT_AUTHORIZED = {
    "ensemble_size_increase",
    "slurm_arrays",
    "distributed_reducers",
    "mpi",
    "gpu_execution",
    "annual_or_physical_probability_products",
    "operational_hazard_map_claims",
}
REQUIRED_ARTIFACT_FAMILIES = {"geotiff", "esri_ascii_grid", "geojson", "csv"}
MISLEADING_PATTERNS = [
    re.compile(r"\boperational(?:ly)?\s+(?:ready|validated|approved)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
]


class SlurmProbeRepeatabilityError(ValueError):
    """User-facing validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_probe_repeatability_record(args.record)
    except SlurmProbeRepeatabilityError as exc:
        print(f"balfrin SLURM probe repeatability validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "balfrin SLURM probe repeatability record is valid: "
            f"{args.record} ({summary['classification']}, "
            f"repeat_runs={summary['repeat_run_count']})"
        )
    return 0


def validate_probe_repeatability_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "balfrin_slurm_probe_repeatability_v1",
        "schema_version must be balfrin_slurm_probe_repeatability_v1",
    )
    require(record.get("roadmap_item") == "DT-03", "roadmap_item must be DT-03")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    require(record.get("classification") == "pass_with_scope_limits", "classification must be pass_with_scope_limits")
    require(
        record.get("driver_decision") == "ready_for_same_scale_selected_gate_reproduction",
        "driver_decision must allow only same-scale selected-gate reproduction",
    )
    validate_environment(require_mapping(record.get("checked_environment"), "checked_environment"))
    validate_probe_definition(require_mapping(record.get("probe_definition"), "probe_definition"))
    validate_baseline(require_mapping(record.get("fresh_baseline"), "fresh_baseline"))
    repeat_runs = validate_repeat_runs(require_list(record.get("repeat_runs"), "repeat_runs"))
    validate_repeatability(require_mapping(record.get("repeatability_assessment"), "repeatability_assessment"))
    validate_numerical_stability(require_mapping(record.get("numerical_artifact_stability"), "numerical_artifact_stability"))
    validate_log_audit(require_mapping(record.get("log_audit_assessment"), "log_audit_assessment"), repeat_runs)
    validate_decision(require_mapping(record.get("selected_gate_readiness_decision"), "selected_gate_readiness_decision"))
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    limitations = require_list(record.get("limitations"), "limitations")
    require(limitations, "limitations must be nonempty")
    require_text(record.get("next_step"), "next_step")
    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "probe_id": record["probe_id"],
        "classification": record["classification"],
        "driver_decision": record["driver_decision"],
        "repeat_run_count": len(repeat_runs),
    }


def validate_environment(env: dict[str, Any]) -> None:
    require_text(env.get("host"), "checked_environment.host")
    require_text(env.get("repo_root"), "checked_environment.repo_root")
    commit = require_text(env.get("commit"), "checked_environment.commit")
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "checked_environment.commit must be a full SHA-1")
    require(env.get("single_job_driver") is True, "checked_environment.single_job_driver must be true")
    require(env.get("slurm_arrays_or_distributed_reducers") is False, "SLURM arrays/distributed reducers must be false")


def validate_probe_definition(defn: dict[str, Any]) -> None:
    require_text(defn.get("manifest_path"), "probe_definition.manifest_path")
    require_positive_int(defn.get("release_cell_count"), "probe_definition.release_cell_count")
    require_positive_int(defn.get("trajectories_per_release_cell"), "probe_definition.trajectories_per_release_cell")
    require_positive_int(defn.get("expected_simulated_trajectory_count"), "probe_definition.expected_simulated_trajectory_count")
    output_profile = require_mapping(defn.get("output_profile"), "probe_definition.output_profile")
    require(output_profile.get("conditional_curve_export") == "summary-only", "conditional_curve_export must be summary-only")
    require(output_profile.get("grid_csv_export") == "none", "grid_csv_export must be none")
    require(output_profile.get("export_geotiff") is True, "export_geotiff must be true")
    require(output_profile.get("no_plots") is True, "no_plots must be true")
    workers = require_mapping(defn.get("workers"), "probe_definition.workers")
    require(workers.get("trajectory_workers") == 2, "trajectory_workers must be 2")
    require(workers.get("reducer_workers") == 2, "reducer_workers must be 2")


def validate_baseline(baseline: dict[str, Any]) -> None:
    require_text(baseline.get("job_id"), "fresh_baseline.job_id")
    require_text(baseline.get("run_root"), "fresh_baseline.run_root")
    require(baseline.get("chunk_state") == "executed", "fresh baseline must be executed")
    require_decision_count(baseline.get("trajectory_decision_counts"), "executed", 2, "fresh_baseline.trajectory_decision_counts")
    require_decision_count(baseline.get("reducer_decision_counts"), "executed", 2, "fresh_baseline.reducer_decision_counts")
    require_positive_number(baseline.get("total_wall_seconds"), "fresh_baseline.total_wall_seconds")
    require_positive_int(baseline.get("output_file_count"), "fresh_baseline.output_file_count")
    log_review = require_mapping(baseline.get("log_audit_review"), "fresh_baseline.log_audit_review")
    require(log_review.get("classification") == "pass_clean", "fresh_baseline.log_audit_review.classification must be pass_clean")
    require(log_review.get("warning_like_line_count") == 0, "fresh baseline warning count must be zero")
    require(log_review.get("error_like_line_count") == 0, "fresh baseline error count must be zero")


def validate_repeat_runs(runs: list[Any]) -> list[dict[str, Any]]:
    require(len(runs) >= 2, "at least two repeat runs must be recorded")
    normalized = []
    trajectory_plan_ids = set()
    reducer_plan_ids = set()
    for idx, value in enumerate(runs):
        run = require_mapping(value, f"repeat_runs[{idx}]")
        require_text(run.get("job_id"), f"repeat_runs[{idx}].job_id")
        require_text(run.get("run_root"), f"repeat_runs[{idx}].run_root")
        require(run.get("slurm_state") == "COMPLETED", f"repeat_runs[{idx}].slurm_state must be COMPLETED")
        require(run.get("slurm_exit_code") == "0:0", f"repeat_runs[{idx}].slurm_exit_code must be 0:0")
        require_decision_count(run.get("trajectory_decision_counts"), "reused_completed_state", 2, f"repeat_runs[{idx}].trajectory_decision_counts")
        require_decision_count(run.get("reducer_decision_counts"), "reused_completed_state", 2, f"repeat_runs[{idx}].reducer_decision_counts")
        require_positive_number(run.get("total_wall_seconds"), f"repeat_runs[{idx}].total_wall_seconds")
        require_positive_int(run.get("output_file_count"), f"repeat_runs[{idx}].output_file_count")
        trajectory_plan_ids.add(require_text(run.get("trajectory_plan_id"), f"repeat_runs[{idx}].trajectory_plan_id"))
        reducer_plan_ids.add(require_text(run.get("reducer_plan_id"), f"repeat_runs[{idx}].reducer_plan_id"))
        log_audit = require_mapping(run.get("log_audit"), f"repeat_runs[{idx}].log_audit")
        require(log_audit.get("classification") == "pass_clean", f"repeat_runs[{idx}].log_audit.classification must be pass_clean")
        require(log_audit.get("warning_like_line_count") == 0, f"repeat_runs[{idx}].warning_like_line_count must be zero")
        require(log_audit.get("error_like_line_count") == 0, f"repeat_runs[{idx}].error_like_line_count must be zero")
        normalized.append(run)
    require(len(trajectory_plan_ids) == 1, "repeat trajectory plan ids must be stable")
    require(len(reducer_plan_ids) == 1, "repeat reducer plan ids must be stable")
    return normalized


def validate_repeatability(assessment: dict[str, Any]) -> None:
    require(assessment.get("repeat_reuse_classification") == "pass_reuse_stable", "repeat reuse classification must pass")
    require(assessment.get("plan_id_stability") == "pass", "plan_id_stability must pass")
    for field in (
        "trajectory_plan_id_stable",
        "reducer_plan_id_stable",
        "trajectory_reuse_decisions_stable",
        "reducer_reuse_decisions_stable",
        "output_file_count_stable",
    ):
        require(assessment.get(field) is True, f"repeatability_assessment.{field} must be true")
    require(assessment.get("metadata_byte_identity_required") is False, "metadata byte identity must not be required")


def validate_numerical_stability(stability: dict[str, Any]) -> None:
    require(stability.get("classification") == "pass_hash_stable", "numerical artifact stability must pass")
    families = set(require_list(stability.get("artifact_families"), "numerical_artifact_stability.artifact_families"))
    require(REQUIRED_ARTIFACT_FAMILIES.issubset(families), f"artifact families missing: {sorted(REQUIRED_ARTIFACT_FAMILIES - families)}")
    before = require_positive_int(stability.get("artifact_count_before"), "artifact_count_before")
    after = require_positive_int(stability.get("artifact_count_after"), "artifact_count_after")
    require(before == after, "artifact counts must match")
    require(stability.get("total_bytes_before") == stability.get("total_bytes_after"), "numeric artifact bytes must match")
    require(stability.get("changed_artifact_count") == 0, "changed_artifact_count must be zero")
    require(require_list(stability.get("changed_paths"), "changed_paths") == [], "changed_paths must be empty")


def validate_log_audit(audit: dict[str, Any], repeat_runs: list[dict[str, Any]]) -> None:
    require(audit.get("classification") == "pass_clean", "log audit classification must be pass_clean")
    reviewed = {str(value) for value in require_list(audit.get("reviewed_repeat_jobs"), "reviewed_repeat_jobs")}
    run_jobs = {str(run.get("job_id")) for run in repeat_runs}
    require(run_jobs.issubset(reviewed), "log audit must review every repeat job")
    require(audit.get("warning_like_line_count") == 0, "log audit warning count must be zero")
    require(audit.get("error_like_line_count") == 0, "log audit error count must be zero")
    require(require_list(audit.get("affected_log_paths"), "affected_log_paths") == [], "affected_log_paths must be empty")


def validate_decision(decision: dict[str, Any]) -> None:
    require(decision.get("driver_ready_for_selected_gate_use") is True, "driver must be ready for selected gate use")
    require(
        decision.get("allowed_next_use") == "same_scale_selected_tschamut_conditional_hazard_map_reproduction",
        "allowed_next_use must be same-scale selected reproduction",
    )
    controls = set(require_list(decision.get("required_controls"), "selected_gate_readiness_decision.required_controls"))
    missing_controls = sorted(REQUIRED_CONTROLS - controls)
    require(not missing_controls, f"required_controls missing: {missing_controls}")
    not_authorized = set(require_list(decision.get("not_authorized"), "selected_gate_readiness_decision.not_authorized"))
    missing_forbidden = sorted(REQUIRED_NOT_AUTHORIZED - not_authorized)
    require(not missing_forbidden, f"not_authorized missing: {missing_forbidden}")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "generated_outputs_committed",
        "raw_geodata_committed",
        "changes_physics",
        "changes_defaults",
        "changes_sampling_weights",
        "public_benchmark_enabled",
        "annualized",
        "physical_probability",
        "return_period",
        "risk_or_exposure",
        "operational_hazard_map",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")


def require_decision_count(value: Any, key: str, expected: int, context: str) -> None:
    mapping = require_mapping(value, context)
    require(mapping.get(key) == expected, f"{context}.{key} must be {expected}")


def scan_text_for_misleading_claims(value: Any, context: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_text_for_misleading_claims(child, f"{context}.{key}")
        return
    if isinstance(value, list):
        for idx, child in enumerate(value):
            scan_text_for_misleading_claims(child, f"{context}[{idx}]")
        return
    if not isinstance(value, str):
        return
    for pattern in MISLEADING_PATTERNS:
        if pattern.search(value):
            lowered = value.lower()
            require(
                "not_authorized" in context
                or "out of scope" in lowered
                or "not authorize" in lowered
                or "does not authorize" in lowered,
                f"{context} contains potentially misleading phrase without out-of-scope framing: {value!r}",
            )


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should report path context.
        raise SlurmProbeRepeatabilityError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SlurmProbeRepeatabilityError(f"record must be a YAML mapping: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SlurmProbeRepeatabilityError(message)


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SlurmProbeRepeatabilityError(f"{context} must be a mapping")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise SlurmProbeRepeatabilityError(f"{context} must be a list")
    return value


def require_text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SlurmProbeRepeatabilityError(f"{context} must be a non-empty string")
    return value


def require_positive_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise SlurmProbeRepeatabilityError(f"{context} must be a positive integer")
    return value


def require_positive_number(value: Any, context: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise SlurmProbeRepeatabilityError(f"{context} must be a positive number")
    return float(value)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
