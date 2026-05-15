#!/usr/bin/env python3
"""Validate the balfrin selected Tschamut target-gate reproduction record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_UPSTREAM_RECORDS = {
    "balfrin_readiness",
    "slurm_probe_repeatability",
    "target_gate_local_record",
    "ensemble_feasibility_gate",
    "scaling_review",
}
REQUIRED_CHECKSUMS = {
    "validation_manifest",
    "hazard_manifest",
    "map_package_manifest",
    "pilot_gis_package_manifest",
    "scaling_summary",
}
MISLEADING_PATTERNS = [
    re.compile(r"\boperational(?:ly)?\s+(?:ready|validated|approved)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
]


class BalfrinTargetGateReproductionError(ValueError):
    """User-facing validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_target_gate_reproduction_record(args.record)
    except BalfrinTargetGateReproductionError as exc:
        print(f"balfrin target-gate reproduction validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "balfrin target-gate reproduction record is valid: "
            f"{args.record} ({summary['reproducibility_classification']}, "
            f"trajectories={summary['simulated_trajectory_count']})"
        )
    return 0


def validate_target_gate_reproduction_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "balfrin_target_gate_reproduction_v1",
        "schema_version must be balfrin_target_gate_reproduction_v1",
    )
    require(record.get("roadmap_item") == "DT-04", "roadmap_item must be DT-04")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    require(record.get("execution_status") == "completed", "execution_status must be completed")
    classification = record.get("reproducibility_classification")
    require(classification in {"passed", "failed", "inconclusive"}, "reproducibility_classification is invalid")
    require(classification == "inconclusive", "current DT-04 record must remain inconclusive")
    require_text(record.get("classification_rationale"), "classification_rationale")
    validate_upstream_records(require_mapping(record.get("upstream_records"), "upstream_records"))
    validate_environment(require_mapping(record.get("run_environment"), "run_environment"))
    validate_case_generation(require_mapping(record.get("case_generation"), "case_generation"))
    validate_input_freeze(require_mapping(record.get("input_freeze"), "input_freeze"))
    validate_physics_and_sampling(require_mapping(record.get("physics_and_sampling"), "physics_and_sampling"))
    validate_hazard_output_profile(require_mapping(record.get("hazard_output_profile"), "hazard_output_profile"))
    validate_validation_metrics(require_mapping(record.get("validation_metrics"), "validation_metrics"))
    validate_performance(require_mapping(record.get("performance"), "performance"))
    validate_conditional_execution(require_mapping(record.get("conditional_execution"), "conditional_execution"))
    validate_checksums(require_mapping(record.get("checksums"), "checksums"))
    validate_log_audit(require_mapping(record.get("log_audit"), "log_audit"))
    validate_wrapper_attempts(require_list(record.get("wrapper_attempts"), "wrapper_attempts"))
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    validate_limitations(require_list(record.get("limitations"), "limitations"))
    require_text(record.get("next_step"), "next_step")
    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "run_id": record["run_id"],
        "reproducibility_classification": classification,
        "simulated_trajectory_count": record["physics_and_sampling"]["simulated_trajectory_count"],
        "job_id": record["run_environment"]["job_id"],
    }


def validate_upstream_records(upstream: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_UPSTREAM_RECORDS - set(upstream))
    require(not missing, f"upstream_records missing: {missing}")
    for key in REQUIRED_UPSTREAM_RECORDS:
        require_text(upstream.get(key), f"upstream_records.{key}")


def validate_environment(env: dict[str, Any]) -> None:
    require(env.get("host") == "balfrin.cscs.ch", "run_environment.host must be balfrin.cscs.ch")
    require_text(env.get("repo_root"), "run_environment.repo_root")
    commit = require_text(env.get("commit"), "run_environment.commit")
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "run_environment.commit must be a full SHA-1")
    require_positive_int(env.get("cpus_per_task"), "run_environment.cpus_per_task")
    require(env.get("single_job_driver") is True, "run_environment.single_job_driver must be true")
    require(env.get("slurm_arrays_or_distributed_reducers") is False, "SLURM arrays/distributed reducers must be false")
    require_text(env.get("run_root"), "run_environment.run_root")
    require_text(env.get("job_id"), "run_environment.job_id")
    require(env.get("slurm_state") == "COMPLETED", "run_environment.slurm_state must be COMPLETED")
    require(env.get("slurm_exit_code") == "0:0", "run_environment.slurm_exit_code must be 0:0")


def validate_case_generation(case_generation: dict[str, Any]) -> None:
    require_text(case_generation.get("case_path"), "case_generation.case_path")
    require(case_generation.get("generated_output_committed") is False, "generated target case must remain uncommitted")
    require_text(case_generation.get("source_case_path"), "case_generation.source_case_path")
    policy = require_text(case_generation.get("generation_policy"), "case_generation.generation_policy").lower()
    for term in ("ensemble_size", "100", "ensemble_workers", "2", "unchanged"):
        require(term in policy, f"case_generation.generation_policy must mention {term!r}")


def validate_input_freeze(input_freeze: dict[str, Any]) -> None:
    for field in (
        "geodata_manifest_path",
        "terrain_metadata_path",
        "source_zone_metadata_path",
        "scenario_table_path",
        "source_scenario_policy_path",
        "release_points_csv",
        "deposition_points_csv",
    ):
        require_text(input_freeze.get(field), f"input_freeze.{field}")


def validate_physics_and_sampling(physics: dict[str, Any]) -> None:
    require(physics.get("contact_model") == "translational_v0", "contact model must remain translational_v0")
    require(physics.get("roughness_model") == "stochastic_contact_v1", "roughness model must remain stochastic_contact_v1")
    require(physics.get("random_seed") == 34014, "random seed must remain 34014")
    require(physics.get("release_cell_count") == 10, "release_cell_count must be 10")
    require(physics.get("trajectories_per_release_cell") == 100, "trajectories_per_release_cell must be 100")
    require(physics.get("simulated_trajectory_count") == 1000, "simulated_trajectory_count must be 1000")
    require(physics.get("trajectory_workers") == 2, "trajectory_workers must be 2")
    require(physics.get("reducer_workers") == 2, "reducer_workers must be 2")
    for field in ("changes_physics", "changes_defaults", "changes_release_assumptions", "changes_thresholds"):
        require(physics.get(field) is False, f"physics_and_sampling.{field} must be false")


def validate_hazard_output_profile(profile: dict[str, Any]) -> None:
    require(profile.get("profile") == "scalable_conditional", "hazard output profile must be scalable_conditional")
    require(profile.get("probability_mode") == "sampling_weighted_conditional", "probability_mode must be sampling_weighted_conditional")
    require(profile.get("normalization_scope") == "conditioned_on_filter", "normalization_scope must be conditioned_on_filter")
    require(profile.get("conditional_curve_export") == "summary-only", "conditional_curve_export must be summary-only")
    require(profile.get("conditional_curve_csv_written") is False, "conditional curve CSV must not be written")
    require(profile.get("conditional_curve_row_count") == 729600, "conditional_curve_row_count must be 729600")
    require(profile.get("grid_csv_export") == "none", "grid_csv_export must be none")
    require(profile.get("grid_csv_written") is False, "grid CSV must not be written")
    require(profile.get("export_geotiff") is True, "GeoTIFF export must be enabled")
    require(profile.get("no_plots") is True, "plots must remain disabled")
    require(profile.get("manual_gis_qa_status") == "not-run", "manual GIS QA must remain not-run")


def validate_validation_metrics(metrics: dict[str, Any]) -> None:
    require(metrics.get("validation_release_count") == 10.0, "validation_release_count must be 10.0")
    require(metrics.get("validation_simulated_trajectory_count") == 1000.0, "validation_simulated_trajectory_count must be 1000.0")
    for field in (
        "observed_mean_runout_m",
        "simulated_mean_runout_m",
        "runout_distance_error_m",
        "deposition_centroid_error_m",
        "deposition_cloud_mean_nearest_error_m",
        "deposition_cloud_overlap_fraction",
        "lateral_spread_error_m",
    ):
        require_number(metrics.get(field), f"validation_metrics.{field}")


def validate_performance(performance: dict[str, Any]) -> None:
    for field in (
        "validation_time_file_seconds",
        "hazard_time_file_seconds",
        "validation_total_wall_seconds",
        "validation_simulation_seconds",
        "validation_output_write_seconds",
        "hazard_total_wall_seconds",
        "hazard_accumulation_seconds",
        "hazard_output_write_seconds",
    ):
        require_positive_number(performance.get(field), f"performance.{field}")
    for field in (
        "validation_output_file_count",
        "validation_output_bytes",
        "validation_impact_event_count",
        "hazard_output_file_count",
        "hazard_output_bytes",
        "hazard_total_input_rows_read",
        "hazard_impact_event_count",
    ):
        require_positive_int(performance.get(field), f"performance.{field}")


def validate_conditional_execution(execution: dict[str, Any]) -> None:
    require(
        execution.get("schema_version") == "conditional_hazard_execution_diagnostics_v1",
        "conditional_execution schema_version is invalid",
    )
    trajectory = require_mapping(execution.get("trajectory_generation"), "conditional_execution.trajectory_generation")
    reducer = require_mapping(execution.get("reducer"), "conditional_execution.reducer")
    for context, section in (("trajectory_generation", trajectory), ("reducer", reducer)):
        require(section.get("mode") == "chunked_local_threads", f"{context}.mode must be chunked_local_threads")
        require(section.get("worker_count") == 2, f"{context}.worker_count must be 2")
        require(section.get("chunk_count") == 2, f"{context}.chunk_count must be 2")
        require(section.get("chunk_manifest_count") == 2, f"{context}.chunk_manifest_count must be 2")
        require(section.get("merge_order") == "sorted_chunk_id", f"{context}.merge_order must be sorted_chunk_id")
    require(reducer.get("merge_order_independent") is True, "reducer.merge_order_independent must be true")
    diagnostics = require_mapping(execution.get("convergence_diagnostics"), "conditional_execution.convergence_diagnostics")
    require(diagnostics.get("probability_standard_error_layers_present") is False, "probability SE layers must be absent")
    require(
        diagnostics.get("requires_trajectory_count_sensitivity_before_scale_up") is True,
        "trajectory-count sensitivity must be required before scale-up",
    )
    require(
        diagnostics.get("requires_worker_count_reducer_parity_before_scale_up") is True,
        "worker-count reducer parity must be required before scale-up",
    )


def validate_checksums(checksums: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_CHECKSUMS - set(checksums))
    require(not missing, f"checksums missing: {missing}")
    for key in REQUIRED_CHECKSUMS:
        item = require_mapping(checksums.get(key), f"checksums.{key}")
        require_text(item.get("path"), f"checksums.{key}.path")
        sha = require_text(item.get("sha256"), f"checksums.{key}.sha256")
        require(re.fullmatch(r"[0-9a-f]{64}", sha) is not None, f"checksums.{key}.sha256 must be 64 lowercase hex chars")
        require_positive_int(item.get("bytes"), f"checksums.{key}.bytes")


def validate_log_audit(audit: dict[str, Any]) -> None:
    require(audit.get("classification") == "pass_clean", "log audit classification must be pass_clean")
    require(audit.get("matched_line_count") == 0, "log audit matched line count must be zero")
    require(audit.get("warning_like_line_count") == 0, "log audit warning count must be zero")
    require(audit.get("error_like_line_count") == 0, "log audit error count must be zero")
    require(require_list(audit.get("affected_log_paths"), "log_audit.affected_log_paths") == [], "affected log paths must be empty")


def validate_wrapper_attempts(attempts: list[Any]) -> None:
    require(len(attempts) >= 2, "wrapper_attempts must record failed wrapper attempts")
    statuses = {require_mapping(value, "wrapper_attempt").get("status") for value in attempts}
    require("failed_wrapper_before_hazard" in statuses, "wrapper_attempts must record pre-hazard wrapper failure")
    require("failed_postprocessing_after_hazard" in statuses, "wrapper_attempts must record postprocessing wrapper failure")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "generated_outputs_committed",
        "raw_geodata_committed",
        "changes_physics",
        "changes_defaults",
        "changes_sampling_weights",
        "annualized",
        "physical_probability",
        "return_period",
        "risk_or_exposure",
        "operational_hazard_map",
        "validated_hazard_map",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")


def validate_limitations(limitations: list[Any]) -> None:
    require(len(limitations) >= 4, "limitations must include key scope limits")
    text = "\n".join(str(item).lower() for item in limitations)
    for term in ("convergence", "gis/qgis", "forest", "ignored"):
        require(term in text, f"limitations must mention {term}")


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
                "not" in lowered
                or "false" in lowered
                or "out of scope" in lowered
                or "does not authorize" in lowered,
                f"{context} contains potentially misleading phrase without limiting context: {value!r}",
            )


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should report path context.
        raise BalfrinTargetGateReproductionError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BalfrinTargetGateReproductionError(f"record must be a YAML mapping: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BalfrinTargetGateReproductionError(message)


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BalfrinTargetGateReproductionError(f"{context} must be a mapping")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise BalfrinTargetGateReproductionError(f"{context} must be a list")
    return value


def require_text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BalfrinTargetGateReproductionError(f"{context} must be a non-empty string")
    return value


def require_number(value: Any, context: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise BalfrinTargetGateReproductionError(f"{context} must be a number")
    return float(value)


def require_positive_number(value: Any, context: str) -> float:
    number = require_number(value, context)
    if number <= 0:
        raise BalfrinTargetGateReproductionError(f"{context} must be positive")
    return number


def require_positive_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise BalfrinTargetGateReproductionError(f"{context} must be a positive integer")
    return value


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
