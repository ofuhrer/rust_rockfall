#!/usr/bin/env python3
"""Validate the DT-06 stochastic sampling and RNG stream audit record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_CODE_PATHS = (
    "src/stochastic.rs",
    "src/simulation.rs",
    "src/integrator.rs",
)
REQUIRED_DOC_PATHS = (
    "docs/hazard_map_semantics.md",
    "docs/probabilistic_scenario_model_design.md",
    "docs/conditional_hazard_convergence_acceptance_protocol.md",
    "docs/next_development_targets.md",
    "docs/real_case_intensity_frequency_implementation_roadmap.md",
    "docs/roadmap_recommendation_matrix.md",
)
REQUIRED_RECORD_PATHS = (
    "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
    "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
    "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
)
REQUIRED_STREAM_AXES = (
    "case_id",
    "trajectory_id",
    "worker_id",
    "stochastic_variable_family",
    "retry_or_chunk_execution",
    "draw_index",
)
REQUIRED_FAMILIES = {
    "trajectory_seed",
    "release_perturbation",
    "roughness_contact",
    "scenario_sampling_weight",
    "block_mass_shape_restitution",
}
REQUIRED_BLOCKERS = {
    "stream_separation_audit_incomplete",
    "distribution_truncation_support_incomplete",
    "weighted_uncertainty_semantics_incomplete",
    "stochastic_validity_not_accepted",
    "scale_up_authorization_not_granted",
}
REQUIRED_NON_BLOCKERS = {
    "current_seed_derivation_is_deterministic",
    "current_conditional_products_remain_diagnostic",
    "no_physics_change_is_required_for_this_audit",
}


class StochasticSamplingAuditError(ValueError):
    """User-facing stochastic audit validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_stochastic_sampling_audit(args.record)
    except StochasticSamplingAuditError as exc:
        print(f"stochastic sampling audit validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "stochastic sampling audit record is valid: "
            f"{args.record} ({summary['current_classification']}, "
            f"stochastic_validity_accepted={summary['stochastic_validity_accepted']})"
        )
    return 0


def validate_stochastic_sampling_audit(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "stochastic_sampling_audit_v1",
        "schema_version must be stochastic_sampling_audit_v1",
    )
    require_text(record.get("record_id"), "record_id")
    require_text(record.get("pilot_id"), "pilot_id")
    require(record.get("roadmap_item") == "DT-06", "roadmap_item must be DT-06")
    current_classification = require_text(record.get("current_classification"), "current_classification")
    require(
        current_classification == "diagnostic_incomplete",
        "current_classification must be diagnostic_incomplete",
    )
    require(record.get("stochastic_validity_accepted") is False, "stochastic_validity_accepted must be false")
    require(record.get("scale_up_authorized") is False, "scale_up_authorized must be false")

    validate_required_paths(record, "assessed_code", REQUIRED_CODE_PATHS)
    validate_required_paths(record, "assessed_docs", REQUIRED_DOC_PATHS)
    validate_required_paths(record, "assessed_records", REQUIRED_RECORD_PATHS)

    validate_stochastic_variable_families(require_list(record.get("stochastic_variable_families"), "stochastic_variable_families"))
    validate_stream_separation_assessment(require_mapping(record.get("stream_separation_assessment"), "stream_separation_assessment"))
    validate_release_perturbation_semantics(require_mapping(record.get("release_perturbation_semantics"), "release_perturbation_semantics"))
    validate_roughness_contact_semantics(require_mapping(record.get("roughness_contact_semantics"), "roughness_contact_semantics"))
    validate_distribution_truncation_support(require_mapping(record.get("distribution_truncation_support"), "distribution_truncation_support"))
    validate_weighted_uncertainty_assessment(require_mapping(record.get("weighted_uncertainty_assessment"), "weighted_uncertainty_assessment"))
    validate_impact_on_tschamut_pilot_interpretation(require_mapping(record.get("impact_on_tschamut_pilot_interpretation"), "impact_on_tschamut_pilot_interpretation"))
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))

    blockers = set(require_list(record.get("blockers"), "blockers"))
    require(not (REQUIRED_BLOCKERS - blockers), f"blockers missing: {sorted(REQUIRED_BLOCKERS - blockers)}")
    non_blockers = set(require_list(record.get("non_blockers"), "non_blockers"))
    require(not (REQUIRED_NON_BLOCKERS - non_blockers), f"non_blockers missing: {sorted(REQUIRED_NON_BLOCKERS - non_blockers)}")

    required_future_evidence = require_list(record.get("required_future_evidence"), "required_future_evidence")
    require(required_future_evidence, "required_future_evidence must be nonempty")
    notes = require_list(record.get("notes"), "notes")
    require(notes, "notes must be nonempty")
    for index, note in enumerate(notes):
        require_text(note, f"notes[{index}]")

    return {
        "schema_version": record["schema_version"],
        "record_id": record["record_id"],
        "current_classification": current_classification,
        "stochastic_validity_accepted": False,
        "scale_up_authorized": False,
    }


def validate_required_paths(record: dict[str, Any], field: str, required_paths: tuple[str, ...]) -> None:
    values = require_list(record.get(field), field)
    missing = sorted(set(required_paths) - {require_text(item, f"{field}[]") for item in values})
    require(not missing, f"{field} missing required paths: {missing}")


def validate_stochastic_variable_families(families: list[Any]) -> None:
    require(families, "stochastic_variable_families must be nonempty")
    seen = set()
    for family in families:
        family = require_mapping(family, "stochastic_variable_families[]")
        family_id = require_text(family.get("family_id"), "stochastic_variable_families[].family_id")
        require(family_id in REQUIRED_FAMILIES, f"unknown family_id {family_id!r}")
        require(family_id not in seen, f"duplicate family_id {family_id!r}")
        seen.add(family_id)
        require_text(family.get("current_status"), "stochastic_variable_families[].current_status")
        require_text(family.get("notes"), "stochastic_variable_families[].notes")
    require(not (REQUIRED_FAMILIES - seen), f"stochastic_variable_families missing: {sorted(REQUIRED_FAMILIES - seen)}")


def validate_stream_separation_assessment(assessment: dict[str, Any]) -> None:
    require_text(assessment.get("current_status"), "stream_separation_assessment.current_status")
    axes = require_list(assessment.get("separation_axes"), "stream_separation_assessment.separation_axes")
    require(tuple(axes) == REQUIRED_STREAM_AXES, f"stream_separation_assessment.separation_axes must be {REQUIRED_STREAM_AXES}")
    current_behavior = require_mapping(assessment.get("current_derivation_behavior"), "stream_separation_assessment.current_derivation_behavior")
    require_text(current_behavior.get("hash_algorithm"), "stream_separation_assessment.current_derivation_behavior.hash_algorithm")
    hash_inputs = require_list(current_behavior.get("hash_inputs"), "stream_separation_assessment.current_derivation_behavior.hash_inputs")
    require(hash_inputs == ["global_seed", "case_id", "trajectory_id"], "stream_separation_assessment must document the current hash inputs")
    limitations = require_list(assessment.get("limitations"), "stream_separation_assessment.limitations")
    require(limitations, "stream_separation_assessment.limitations must be nonempty")
    future_tests = require_list(assessment.get("future_tests"), "stream_separation_assessment.future_tests")
    require(future_tests, "stream_separation_assessment.future_tests must be nonempty")


def validate_release_perturbation_semantics(assessment: dict[str, Any]) -> None:
    require_text(assessment.get("model"), "release_perturbation_semantics.model")
    require_text(assessment.get("current_status"), "release_perturbation_semantics.current_status")
    axes = require_list(assessment.get("axes"), "release_perturbation_semantics.axes")
    require(set(axes) == {"x", "y", "z"}, "release_perturbation_semantics.axes must cover x, y, and z")
    require_text(assessment.get("position_half_width_source"), "release_perturbation_semantics.position_half_width_source")
    require_text(assessment.get("velocity_half_width_source"), "release_perturbation_semantics.velocity_half_width_source")
    limitations = require_list(assessment.get("limitations"), "release_perturbation_semantics.limitations")
    require(limitations, "release_perturbation_semantics.limitations must be nonempty")


def validate_roughness_contact_semantics(assessment: dict[str, Any]) -> None:
    require_text(assessment.get("model"), "roughness_contact_semantics.model")
    require_text(assessment.get("current_status"), "roughness_contact_semantics.current_status")
    require_text(assessment.get("contact_seed_source"), "roughness_contact_semantics.contact_seed_source")
    perturbations = require_list(assessment.get("perturbations"), "roughness_contact_semantics.perturbations")
    require(perturbations, "roughness_contact_semantics.perturbations must be nonempty")
    limitations = require_list(assessment.get("limitations"), "roughness_contact_semantics.limitations")
    require(limitations, "roughness_contact_semantics.limitations must be nonempty")


def validate_distribution_truncation_support(assessment: dict[str, Any]) -> None:
    require_text(assessment.get("current_status"), "distribution_truncation_support.current_status")
    topics = require_list(assessment.get("topics"), "distribution_truncation_support.topics")
    require(topics, "distribution_truncation_support.topics must be nonempty")
    limitations = require_list(assessment.get("limitations"), "distribution_truncation_support.limitations")
    require(limitations, "distribution_truncation_support.limitations must be nonempty")


def validate_weighted_uncertainty_assessment(assessment: dict[str, Any]) -> None:
    require_text(assessment.get("current_status"), "weighted_uncertainty_assessment.current_status")
    notes = require_list(assessment.get("notes"), "weighted_uncertainty_assessment.notes")
    require(notes, "weighted_uncertainty_assessment.notes must be nonempty")


def validate_impact_on_tschamut_pilot_interpretation(assessment: dict[str, Any]) -> None:
    require(assessment.get("current_classification") == "diagnostic_incomplete", "impact_on_tschamut_pilot_interpretation.current_classification must be diagnostic_incomplete")
    require(assessment.get("stochastic_validity_accepted") is False, "impact_on_tschamut_pilot_interpretation.stochastic_validity_accepted must be false")
    notes = require_list(assessment.get("notes"), "impact_on_tschamut_pilot_interpretation.notes")
    require(notes, "impact_on_tschamut_pilot_interpretation.notes must be nonempty")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "physics_changes_claimed",
        "rng_changes_claimed",
        "stochastic_default_changes_claimed",
        "annual_or_physical_probability_claimed",
        "risk_exposure_or_operational_claimed",
        "accepted_stochastic_validity_claimed",
        "scale_up_authorized",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise StochasticSamplingAuditError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise StochasticSamplingAuditError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StochasticSamplingAuditError(message)


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
