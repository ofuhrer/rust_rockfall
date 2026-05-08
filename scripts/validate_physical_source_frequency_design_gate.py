#!/usr/bin/env python3
"""Validate the physical/source-frequency semantics design gate record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {"deferred", "authorize_prototype"}
REQUIRED_UNITS = {
    "source_event_rate": "events_per_source_zone_per_year",
    "block_scenario_probability": "conditional_probability_given_source_event",
    "release_cell_probability": "conditional_probability_given_source_and_block",
    "cell_exceedance_output": "exceedances_per_cell_per_year",
}
REQUIRED_SCHEMA_FIELDS = {
    "frequency_model_id",
    "frequency_mode",
    "source_zone_id",
    "source_geometry_version",
    "source_event_class",
    "source_event_rate_per_year",
    "rate_time_window_years",
    "rate_evidence_type",
    "rate_provenance",
    "rate_uncertainty",
    "block_scenario_id",
    "block_scenario_probability",
    "release_cell_id",
    "release_cell_probability",
    "source_zone_overlap_policy",
    "calibration_dataset_ids",
    "validation_dataset_ids",
    "operational_status",
}
REQUIRED_REJECTION_TESTS = {
    "missing_source_event_rate_per_year",
    "invalid_or_missing_frequency_units",
    "sampling_weight_reused_as_physical_probability",
    "missing_source_zone_overlap_policy",
    "missing_rate_uncertainty",
    "missing_calibration_validation_separation",
}
REQUIRED_CURRENT_PRODUCTS = {
    "unweighted_diagnostic",
    "sampling_weighted_conditional",
    "conditional_intensity_exceedance",
}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "return_period",
    "physical_probability",
    "risk_map",
    "operational_hazard_map",
}
REQUIRED_BLOCKER_CONTRACTS = {
    "source_frequency_evidence": {
        "schema_version": "source_frequency_evidence_v1",
        "record_path": "validation/templates/source_frequency_evidence_v1.yaml",
        "current_blocking_status": "no_accepted_frequency_evidence",
        "required_status_before_prototype": "accepted_for_design_review",
    },
    "block_release_probability_evidence": {
        "schema_version": "block_release_probability_evidence_v1",
        "record_path": "validation/templates/block_release_probability_evidence_v1.yaml",
        "current_blocking_status": "no_accepted_block_release_probability_evidence",
        "required_status_before_prototype": "accepted_for_design_review",
    },
    "physical_frequency_reducer_preconditions": {
        "schema_version": "physical_frequency_reducer_preconditions_v1",
        "record_path": "validation/templates/physical_frequency_reducer_preconditions_v1.yaml",
        "current_blocking_status": "preconditions_not_satisfied",
        "required_status_before_prototype": "accepted_for_design_review",
    },
    "annual_physical_validation_calibration_review_gate": {
        "schema_version": "annual_physical_validation_calibration_review_gate_v1",
        "record_path": "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml",
        "current_blocking_status": "review_not_passed",
        "required_status_before_prototype": "accepted_for_design_review",
    },
}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]


class PhysicalSourceFrequencyGateError(ValueError):
    """User-facing design gate validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_design_gate_record(args.record)
    except PhysicalSourceFrequencyGateError as exc:
        print(f"physical source-frequency design gate validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "physical source-frequency design gate record is valid: "
            f"{args.record} ({summary['decision']}, "
            f"prototype_authorized={summary['annual_physical_prototype_authorized']})"
        )
    return 0


def validate_design_gate_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "physical_source_frequency_design_gate_v1",
        "schema_version must be physical_source_frequency_design_gate_v1",
    )
    require_text(record.get("design_gate_id"), "design_gate_id")
    require(
        record.get("roadmap_item") == "target_9_physical_source_frequency_semantics",
        "roadmap_item must be target_9_physical_source_frequency_semantics",
    )
    decision = require_text(record.get("decision"), "decision")
    require(decision in DECISIONS, f"decision must be one of {sorted(DECISIONS)}")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    authorized = record.get("annual_physical_prototype_authorized")
    require(isinstance(authorized, bool), "annual_physical_prototype_authorized must be boolean")
    if decision == "deferred":
        require(authorized is False, "deferred decision must not authorize annual/physical prototype")
    else:
        require(False, "authorize_prototype is intentionally unsupported until this validator is extended")

    current = set(require_list(record.get("current_supported_products"), "current_supported_products"))
    missing_current = sorted(REQUIRED_CURRENT_PRODUCTS - current)
    require(not missing_current, f"current_supported_products missing: {missing_current}")
    future_modes = set(require_list(record.get("future_product_modes"), "future_product_modes"))
    require("physical_probability" in future_modes, "future_product_modes must include physical_probability")
    require("annual_intensity_frequency" in future_modes, "future_product_modes must include annual_intensity_frequency")

    validate_units(require_mapping(record.get("required_frequency_units"), "required_frequency_units"))
    validate_required_evidence(require_mapping(record.get("required_evidence"), "required_evidence"))
    validate_status_requirements(require_mapping(record.get("overlap_policy"), "overlap_policy"), "overlap_policy")
    validate_status_requirements(require_mapping(record.get("uncertainty_model"), "uncertainty_model"), "uncertainty_model")
    validate_status_requirements(
        require_mapping(record.get("validation_calibration_separation"), "validation_calibration_separation"),
        "validation_calibration_separation",
    )
    contract_summary = validate_gate_reassessment(record, decision, authorized)
    validate_schema_plan(require_mapping(record.get("required_schema_plan"), "required_schema_plan"))
    validate_rejection_tests(require_list(record.get("rejection_tests_required_before_prototype"), "rejection_tests_required_before_prototype"))
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    limitations = set(require_list(record.get("limitations"), "limitations"))
    require("no_annual_frequency_or_physical_probability_runtime_support_implemented" in limitations, "limitations must state no runtime support")
    require("no_operational_validation_or_risk_semantics" in limitations, "limitations must state no operational/risk semantics")
    scan_text_for_misleading_claims(record)

    return {
        "schema_version": record["schema_version"],
        "design_gate_id": record["design_gate_id"],
        "decision": decision,
        "annual_physical_prototype_authorized": authorized,
        "blocker_contract_count": contract_summary["blocker_contract_count"],
        "blocking_contract_count": contract_summary["blocking_contract_count"],
        "required_schema_field_count": len(record["required_schema_plan"]["required_fields"]),
        "rejection_test_count": len(record["rejection_tests_required_before_prototype"]),
    }


def validate_units(units: dict[str, Any]) -> None:
    for key, expected in REQUIRED_UNITS.items():
        require(units.get(key) == expected, f"required_frequency_units.{key} must be {expected}")


def validate_required_evidence(evidence: dict[str, Any]) -> None:
    source = set(require_list(evidence.get("source_event_rate"), "required_evidence.source_event_rate"))
    require("uncertainty_interval_or_distribution" in source, "source_event_rate evidence must include uncertainty")
    require("calibration_validation_separation" in source, "source_event_rate evidence must separate calibration and validation")
    block = set(require_list(evidence.get("block_scenario_distribution"), "required_evidence.block_scenario_distribution"))
    require(
        "sampling_weight_not_reused_as_physical_probability" in block,
        "block_scenario_distribution evidence must reject sampling-weight reuse",
    )
    release = set(require_list(evidence.get("release_cell_allocation"), "required_evidence.release_cell_allocation"))
    require("stable_release_cell_id" in release, "release_cell_allocation evidence must include stable release-cell ids")


def validate_status_requirements(section: dict[str, Any], field: str) -> None:
    require(section.get("status") == "required_before_prototype", f"{field}.status must be required_before_prototype")
    require(require_list(section.get("requirements") or section.get("required_components") or section.get("rules"), field), f"{field} must list requirements")


def validate_gate_reassessment(record: dict[str, Any], decision: str, authorized: bool) -> dict[str, int]:
    reassessment = require_mapping(record.get("gate_reassessment"), "gate_reassessment")
    require_text(reassessment.get("reassessment_id"), "gate_reassessment.reassessment_id")
    require(
        reassessment.get("assessment_status") == "deferred_after_inactive_contract_review",
        "gate_reassessment.assessment_status must be deferred_after_inactive_contract_review",
    )
    require(
        reassessment.get("prototype_authorization_basis")
        == "all_required_contracts_present_but_not_accepted_or_implemented",
        "gate_reassessment.prototype_authorization_basis must record inactive blocker contracts",
    )
    contracts = require_list(record.get("blocker_contracts"), "blocker_contracts")
    require(
        reassessment.get("checked_contract_count") == len(contracts),
        "gate_reassessment.checked_contract_count must match blocker_contracts length",
    )
    require(
        len(contracts) == len(REQUIRED_BLOCKER_CONTRACTS),
        f"blocker_contracts must list {len(REQUIRED_BLOCKER_CONTRACTS)} required contracts",
    )

    by_id: dict[str, dict[str, Any]] = {}
    for contract in contracts:
        mapping = require_mapping(contract, "blocker_contracts[]")
        blocker_id = require_text(mapping.get("blocker_id"), "blocker_contracts[].blocker_id")
        require(blocker_id not in by_id, f"duplicate blocker_contracts entry: {blocker_id}")
        by_id[blocker_id] = mapping

    missing = sorted(set(REQUIRED_BLOCKER_CONTRACTS) - set(by_id))
    require(not missing, f"blocker_contracts missing: {missing}")

    blocking_count = 0
    for blocker_id, expected in REQUIRED_BLOCKER_CONTRACTS.items():
        contract = by_id[blocker_id]
        validate_blocker_contract_entry(blocker_id, contract, expected)
        observed = contract["observed_status"]
        required = contract["required_status_before_prototype"]
        if observed != required:
            blocking_count += 1
            require(
                contract.get("prototype_blocker") is True,
                f"blocker_contracts.{blocker_id}.prototype_blocker must be true while status is not accepted",
            )

    if decision == "deferred":
        require(blocking_count > 0, "deferred gate decision must list at least one blocking contract")
        require(authorized is False, "deferred gate decision must keep prototype authorization false")
    else:
        require(blocking_count == 0, "prototype authorization requires all blocker contracts accepted")

    return {
        "blocker_contract_count": len(contracts),
        "blocking_contract_count": blocking_count,
    }


def validate_blocker_contract_entry(blocker_id: str, contract: dict[str, Any], expected: dict[str, str]) -> None:
    record_path = require_text(contract.get("record_path"), f"blocker_contracts.{blocker_id}.record_path")
    require(
        record_path == expected["record_path"],
        f"blocker_contracts.{blocker_id}.record_path must be {expected['record_path']}",
    )
    require(
        contract.get("required_schema_version") == expected["schema_version"],
        f"blocker_contracts.{blocker_id}.required_schema_version must be {expected['schema_version']}",
    )
    require(
        contract.get("required_status_before_prototype") == expected["required_status_before_prototype"],
        f"blocker_contracts.{blocker_id}.required_status_before_prototype must be "
        f"{expected['required_status_before_prototype']}",
    )

    referenced_record = read_yaml(REPO_ROOT / record_path)
    require(
        referenced_record.get("schema_version") == expected["schema_version"],
        f"{record_path} schema_version must be {expected['schema_version']}",
    )
    observed_status = require_text(contract.get("observed_status"), f"blocker_contracts.{blocker_id}.observed_status")
    actual_status = require_text(referenced_record.get("record_status"), f"{record_path}.record_status")
    require(
        observed_status == actual_status,
        f"blocker_contracts.{blocker_id}.observed_status must match {record_path}.record_status",
    )
    if observed_status == expected["current_blocking_status"]:
        require(
            contract.get("prototype_blocker") is True,
            f"blocker_contracts.{blocker_id}.prototype_blocker must be true for {observed_status}",
        )


def validate_schema_plan(plan: dict[str, Any]) -> None:
    require(plan.get("status") == "deferred_schema_not_implemented", "required_schema_plan.status must be deferred_schema_not_implemented")
    fields = set(require_list(plan.get("required_fields"), "required_schema_plan.required_fields"))
    missing = sorted(REQUIRED_SCHEMA_FIELDS - fields)
    require(not missing, f"required_schema_plan.required_fields missing: {missing}")


def validate_rejection_tests(tests: list[Any]) -> None:
    names = set(tests)
    missing = sorted(REQUIRED_REJECTION_TESTS - names)
    require(not missing, f"rejection_tests_required_before_prototype missing: {missing}")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "annual_frequency_supported",
        "physical_probability_supported",
        "return_period_supported",
        "risk_or_exposure_supported",
        "operational_hazard_map_supported",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "claim_boundary.unsupported_current_claims"))
    missing = sorted(REQUIRED_UNSUPPORTED_CLAIMS - unsupported)
    require(not missing, f"claim_boundary.unsupported_current_claims missing: {missing}")


def scan_text_for_misleading_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"claim_boundary", "unsupported_current_claims", "future_product_modes", "required_schema_plan"}:
                continue
            scan_text_for_misleading_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("unsupported", "not_", "no_", "no ", "without", "defer", "future", "out of scope", "required")):
            return
        for pattern in MISLEADING_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise PhysicalSourceFrequencyGateError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PhysicalSourceFrequencyGateError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhysicalSourceFrequencyGateError(message)


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
