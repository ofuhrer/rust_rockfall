#!/usr/bin/env python3
"""Validate the conditional hazard-map convergence acceptance protocol record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "conditional_hazard_convergence_protocol_v1"
ROADMAP_ITEM = "DT-05"
DT04_RECORD_PATH = "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml"
TARGET_GATE_RECORD_PATH = "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
PROTOCOL_STATUS = "applied_to_dt04_evidence"
VALID_CLASSIFICATIONS = {"pass", "inconclusive", "no_go"}
REQUIRED_EVIDENCE_CATEGORIES = (
    "target_run_provenance",
    "input_freeze",
    "trajectory_and_release_counts",
    "deterministic_seed_order_chunk_metadata",
    "reducer_parity_or_repeatability",
    "output_profile",
    "output_budget",
    "checksum_provenance",
    "log_audit",
    "convergence_indicators",
    "known_interpretation_blockers",
)
PROHIBITED_CLAIM_PATTERNS = [
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\bphysical\s+probability\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:validated|ready|approved|hazard)\b", re.IGNORECASE),
    re.compile(r"\bexposure\b", re.IGNORECASE),
    re.compile(r"\bvulnerability\b", re.IGNORECASE),
]


class ConditionalConvergenceProtocolError(ValueError):
    """User-facing validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        summary = validate_protocol_record(args.record)
    except ConditionalConvergenceProtocolError as exc:
        print(f"conditional convergence protocol validation error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "conditional convergence protocol record is valid: "
            f"{args.record} ({summary['current_classification']}, "
            f"scale_up_authorized={summary['scale_up_authorized']})"
        )
    return 0


def validate_protocol_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(record.get("schema_version") == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    require(record.get("roadmap_item") == ROADMAP_ITEM, f"roadmap_item must be {ROADMAP_ITEM}")
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    require(
        record.get("protocol_status") == PROTOCOL_STATUS,
        f"protocol_status must be {PROTOCOL_STATUS}",
    )
    validate_scope(require_mapping(record.get("scope"), "scope"))

    required_categories = require_list(record.get("required_evidence_categories"), "required_evidence_categories")
    require(
        required_categories == list(REQUIRED_EVIDENCE_CATEGORIES),
        "required_evidence_categories must match the DT-05 protocol categories",
    )
    required_gates = require_mapping(record.get("required_gates"), "required_gates")
    require(
        set(required_gates) == set(REQUIRED_EVIDENCE_CATEGORIES),
        "required_gates must include all required evidence categories",
    )

    assessment = require_mapping(record.get("assessment"), "assessment")
    current_classification = require_text(assessment.get("current_classification"), "assessment.current_classification")
    require(current_classification in VALID_CLASSIFICATIONS, "current_classification is invalid")
    scale_up_authorized = assessment.get("scale_up_authorized")
    require(isinstance(scale_up_authorized, bool), "assessment.scale_up_authorized must be boolean")
    if current_classification == "pass":
        require(scale_up_authorized is True, "pass records must authorize scale-up")
    else:
        require(scale_up_authorized is False, "non-pass records must not authorize scale-up")

    require(
        require_mapping(assessment.get("assessed_records"), "assessment.assessed_records").get(
            "dt04_balfrin_reproduction_record"
        )
        == DT04_RECORD_PATH,
        "assessment.assessed_records.dt04_balfrin_reproduction_record must reference the DT-04 Balfrin record",
    )
    require(
        require_mapping(assessment.get("assessed_records"), "assessment.assessed_records").get(
            "dt04_target_gate_record"
        )
        == TARGET_GATE_RECORD_PATH,
        "assessment.assessed_records.dt04_target_gate_record must reference the DT-04 target-gate record",
    )

    blocking_reasons = require_list(assessment.get("blocking_reasons"), "assessment.blocking_reasons")
    if current_classification == "pass":
        require(not blocking_reasons, "pass records must not list blocking reasons")
    else:
        require(blocking_reasons, "non-pass records must list blocking reasons")

    evidence = require_mapping(assessment.get("evidence"), "assessment.evidence")
    require(set(evidence) == set(REQUIRED_EVIDENCE_CATEGORIES), "assessment.evidence must include all required categories")
    validate_target_run_provenance(require_mapping(evidence.get("target_run_provenance"), "assessment.evidence.target_run_provenance"))
    validate_input_freeze(require_mapping(evidence.get("input_freeze"), "assessment.evidence.input_freeze"))
    validate_counts(require_mapping(evidence.get("trajectory_and_release_counts"), "assessment.evidence.trajectory_and_release_counts"))
    validate_determinism(require_mapping(evidence.get("deterministic_seed_order_chunk_metadata"), "assessment.evidence.deterministic_seed_order_chunk_metadata"))
    validate_reducer_parity(require_mapping(evidence.get("reducer_parity_or_repeatability"), "assessment.evidence.reducer_parity_or_repeatability"))
    validate_output_profile(require_mapping(evidence.get("output_profile"), "assessment.evidence.output_profile"))
    validate_output_budget(require_mapping(evidence.get("output_budget"), "assessment.evidence.output_budget"))
    validate_checksums(require_mapping(evidence.get("checksum_provenance"), "assessment.evidence.checksum_provenance"))
    validate_log_audit(require_mapping(evidence.get("log_audit"), "assessment.evidence.log_audit"))
    validate_convergence_indicators(require_mapping(evidence.get("convergence_indicators"), "assessment.evidence.convergence_indicators"), current_classification)
    validate_blockers(require_mapping(evidence.get("known_interpretation_blockers"), "assessment.evidence.known_interpretation_blockers"), current_classification)

    if current_classification == "pass":
        require(all(status == "pass" for status in required_gates.values()), "pass records require every gate to pass")
    else:
        require(
            any(status != "pass" for status in required_gates.values()),
            "non-pass records must retain at least one non-pass gate",
        )
        require(required_gates["convergence_indicators"] in {"inconclusive", "no_go"}, "convergence_indicators must be inconclusive or no_go when the record is not a pass")

    rationale = require_text(record.get("classification_rationale"), "classification_rationale")
    notes = require_text(record.get("notes"), "notes")
    scan_text_for_misleading_claims(rationale, "classification_rationale")
    scan_text_for_misleading_claims(notes, "notes")

    return {
        "schema_version": record["schema_version"],
        "roadmap_item": record["roadmap_item"],
        "current_classification": current_classification,
        "scale_up_authorized": scale_up_authorized,
        "blocking_reason_count": len(blocking_reasons),
    }


def validate_scope(scope: dict[str, Any]) -> None:
    require(scope.get("product_scope") == "conditional_hazard_map_only", "scope.product_scope must be conditional_hazard_map_only")
    require(scope.get("gis_qgis_qa_role") == "secondary", "scope.gis_qgis_qa_role must be secondary")
    require(scope.get("no_tuning") is True, "scope.no_tuning must be true")
    for field in (
        "annual_or_physical_probability_supported",
        "return_period_supported",
        "risk_exposure_or_vulnerability_supported",
        "operational_validity_supported",
    ):
        require(scope.get(field) is False, f"scope.{field} must be false")
    labels = require_list(scope.get("allowed_current_product_labels"), "scope.allowed_current_product_labels")
    require(
        labels == [
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "conditional_intensity_exceedance",
        ],
        "scope.allowed_current_product_labels must match the current conditional product labels",
    )
    prohibited_claims = set(require_list(scope.get("prohibited_claims"), "scope.prohibited_claims"))
    require(
        prohibited_claims == {
            "annual_frequency",
            "physical_probability",
            "return_period",
            "risk_map",
            "exposure",
            "vulnerability",
            "operational_hazard_map",
        },
        "scope.prohibited_claims must enumerate the unsupported current claims",
    )


def validate_target_run_provenance(provenance: dict[str, Any]) -> None:
    require(provenance.get("status") == "pass", "target_run_provenance must pass")
    require(provenance.get("host") == "balfrin.cscs.ch", "target_run_provenance.host must be balfrin.cscs.ch")
    commit = require_text(provenance.get("commit"), "target_run_provenance.commit")
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "target_run_provenance.commit must be a full SHA-1")
    require_text(provenance.get("job_id"), "target_run_provenance.job_id")
    for field in (
        "release_cell_count",
        "trajectories_per_release_cell",
        "simulated_trajectory_count",
        "validation_release_count",
        "validation_simulated_trajectory_count",
    ):
        require_positive_int(provenance.get(field), f"target_run_provenance.{field}")


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
    require(input_freeze.get("status") == "pass", "input_freeze must pass")


def validate_counts(counts: dict[str, Any]) -> None:
    require(counts.get("status") == "pass", "trajectory_and_release_counts must pass")
    require(counts.get("release_cell_count") == 10, "release_cell_count must be 10")
    require(counts.get("trajectories_per_release_cell") == 100, "trajectories_per_release_cell must be 100")
    require(counts.get("simulated_trajectory_count") == 1000, "simulated_trajectory_count must be 1000")


def validate_determinism(determinism: dict[str, Any]) -> None:
    require(determinism.get("status") == "pass", "deterministic_seed_order_chunk_metadata must pass")
    require(determinism.get("random_seed") == 34014, "random_seed must be 34014")
    require(determinism.get("trajectory_merge_order") == "requested_trajectory_index", "trajectory_merge_order must be requested_trajectory_index")
    require(determinism.get("reducer_merge_order") == "sorted_chunk_id", "reducer_merge_order must be sorted_chunk_id")
    require(determinism.get("chunk_count") == 2, "chunk_count must be 2")
    require(determinism.get("reducer_workers") == 2, "reducer_workers must be 2")


def validate_reducer_parity(parity: dict[str, Any]) -> None:
    require(parity.get("status") == "pass", "reducer_parity_or_repeatability must pass")
    require(parity.get("all_compared_outputs_match") is True, "reducer parity must match")
    compared_workers = require_list(parity.get("compared_workers"), "reducer_parity_or_repeatability.compared_workers")
    require(compared_workers == [1, 2], "reducer parity must compare workers [1, 2]")
    compared_outputs = require_mapping(parity.get("compared_outputs"), "reducer_parity_or_repeatability.compared_outputs")
    require(compared_outputs.get("deposition_points") is True, "reducer parity must compare deposition_points")
    require(compared_outputs.get("hazard_layer") is True, "reducer parity must compare hazard_layer")


def validate_output_profile(profile: dict[str, Any]) -> None:
    require(profile.get("status") == "pass", "output_profile must pass")
    require(profile.get("profile") == "scalable_conditional", "output profile must be scalable_conditional")
    require(profile.get("conditional_curve_export") == "summary-only", "conditional_curve_export must be summary-only")
    require(profile.get("grid_csv_export") == "none", "grid_csv_export must be none")
    require(profile.get("export_geotiff") is True, "export_geotiff must be true")
    require(profile.get("no_plots") is True, "no_plots must be true")


def validate_output_budget(budget: dict[str, Any]) -> None:
    require(budget.get("status") in {"pass", "blocker_retained"}, "output_budget status is invalid")
    for field in ("validation_output_file_count", "validation_output_bytes", "hazard_output_file_count", "hazard_output_bytes"):
        require_positive_int(budget.get(field), f"output_budget.{field}")
    require(
        budget.get("validation_debug_output_budget_blocker") is True,
        "output_budget must retain the validation debug output budget blocker",
    )


def validate_checksums(checksums: dict[str, Any]) -> None:
    require(checksums.get("status") == "pass", "checksum_provenance must pass")
    for field in (
        "validation_manifest_sha256",
        "hazard_manifest_sha256",
        "map_package_manifest_sha256",
        "pilot_gis_package_manifest_sha256",
        "scaling_summary_sha256",
    ):
        checksum = require_text(checksums.get(field), f"checksum_provenance.{field}")
        require(re.fullmatch(r"[0-9a-f]{64}", checksum) is not None, f"{field} must be 64 lowercase hex characters")


def validate_log_audit(log_audit: dict[str, Any]) -> None:
    require(log_audit.get("status") == "pass_clean", "log_audit must be pass_clean")
    require(log_audit.get("classification") == "pass_clean", "log_audit.classification must be pass_clean")
    require(log_audit.get("warning_like_line_count") == 0, "log audit warning count must be zero")
    require(log_audit.get("error_like_line_count") == 0, "log audit error count must be zero")


def validate_convergence_indicators(convergence: dict[str, Any], current_classification: str) -> None:
    require(convergence.get("status") in {"pass", "inconclusive", "no_go"}, "convergence_indicators status is invalid")
    require(
        convergence.get("target_vs_small_gate_convergence_accepted") is False,
        "current DT-04 evidence must not claim accepted convergence",
    )
    require_text(convergence.get("manual_gis_visual_qa_status"), "convergence_indicators.manual_gis_visual_qa_status")
    require_text(convergence.get("forest_obstacle_context_status"), "convergence_indicators.forest_obstacle_context_status")
    require_text(convergence.get("validation_debug_output_volume_status"), "convergence_indicators.validation_debug_output_volume_status")
    if current_classification == "pass":
        require(convergence.get("status") == "pass", "pass records require convergence_indicators to pass")
    else:
        require(convergence.get("status") in {"inconclusive", "no_go"}, "non-pass records require convergence to be inconclusive or no_go")


def validate_blockers(blockers: dict[str, Any], current_classification: str) -> None:
    require(blockers.get("status") in {"pass", "present", "limiting"}, "known_interpretation_blockers status is invalid")
    blocker_list = require_list(blockers.get("blockers"), "known_interpretation_blockers.blockers")
    if current_classification == "pass":
        require(not blocker_list, "pass records must not carry blockers")
    else:
        require(blocker_list, "non-pass records must include blockers")
        for blocker in (
            "target_vs_small_gate_convergence_not_accepted",
            "manual_gis_visual_qa_secondary_only",
            "forest_obstacle_context_limiting",
            "validation_debug_output_budget_retained",
        ):
            require(blocker in blocker_list, f"known_interpretation_blockers must include {blocker}")


def scan_text_for_misleading_claims(text: str, context: str) -> None:
    lowered = text.lower()
    for pattern, label in (
        (re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE), "annual/physical claim"),
        (re.compile(r"\bphysical\s+probability\b", re.IGNORECASE), "physical probability claim"),
        (re.compile(r"\breturn[- ]?period\b", re.IGNORECASE), "return-period claim"),
        (re.compile(r"\brisk[- ]?map\b", re.IGNORECASE), "risk-map claim"),
        (re.compile(r"\boperational(?:ly)?\s+(?:validated|ready|approved|hazard)\b", re.IGNORECASE), "operational-validity claim"),
        (re.compile(r"\bexposure\b", re.IGNORECASE), "exposure claim"),
        (re.compile(r"\bvulnerability\b", re.IGNORECASE), "vulnerability claim"),
    ):
        if pattern.search(text) and not any(term in lowered for term in ("not", "no", "unsupported", "deferred", "out of scope", "secondary", "blocked")):
            require(False, f"{context} contains a misleading {label}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - filesystem failure
        raise ConditionalConvergenceProtocolError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConditionalConvergenceProtocolError(f"{path} did not contain a mapping")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConditionalConvergenceProtocolError(message)


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConditionalConvergenceProtocolError(f"{label} must be a non-empty string")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ConditionalConvergenceProtocolError(f"{label} must be a list")
    return value


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConditionalConvergenceProtocolError(f"{label} must be a mapping")
    return value


def require_positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ConditionalConvergenceProtocolError(f"{label} must be a positive integer")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
