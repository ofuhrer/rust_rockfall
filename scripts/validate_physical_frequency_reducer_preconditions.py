#!/usr/bin/env python3
"""Validate inactive physical frequency reducer precondition records.

The schema is a gate input for future design review only. It does not authorize
annual frequency, physical probability, return-period, operational, or risk
products.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import partial
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.workflow_validation import (
    require as shared_require,
    require_false_fields as shared_require_false_fields,
    require_list as shared_require_list,
    require_mapping as shared_require_mapping,
    require_text as shared_require_text,
    read_yaml as shared_read_yaml,
    render_status_message,
    scan_text_for_misleading_claims,
)


STATUSES = {
    "preconditions_not_satisfied",
    "candidate_not_authorized",
    "accepted_for_design_review",
}
PRECONDITION_MODE = "physical_frequency_reducer_preconditions_only"
ALLOWED_OVERLAP_POLICIES = {
    "mutually_exclusive_partition",
    "documented_overlap_adjustment",
}
REQUIRED_UNCERTAINTY_COMPONENTS = {
    "source_event_rate_uncertainty",
    "block_scenario_probability_uncertainty",
    "release_cell_probability_uncertainty",
    "trajectory_aleatory_uncertainty",
    "terrain_model_form_uncertainty",
}
REQUIRED_INPUT_RECORDS = {
    "source_frequency_evidence_v1",
    "block_release_probability_evidence_v1",
}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]


class PhysicalFrequencyReducerPreconditionsError(ValueError):
    """User-facing reducer precondition validation error."""


require = partial(shared_require, error_cls=PhysicalFrequencyReducerPreconditionsError)
require_false_fields = partial(shared_require_false_fields, error_cls=PhysicalFrequencyReducerPreconditionsError)
require_list = partial(shared_require_list, error_cls=PhysicalFrequencyReducerPreconditionsError)
require_mapping = partial(shared_require_mapping, error_cls=PhysicalFrequencyReducerPreconditionsError)
require_text = partial(shared_require_text, error_cls=PhysicalFrequencyReducerPreconditionsError)
read_yaml = partial(shared_read_yaml, error_cls=PhysicalFrequencyReducerPreconditionsError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_physical_frequency_reducer_preconditions(args.record)
    except PhysicalFrequencyReducerPreconditionsError as exc:
        print(f"physical frequency reducer preconditions validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            render_status_message(
                "physical frequency reducer preconditions record",
                args.record,
                summary,
                "record_status",
                extra_fields=(("selected_overlap_policy", "overlap_policy"),),
            )
        )
    return 0


def validate_physical_frequency_reducer_preconditions(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "physical_frequency_reducer_preconditions_v1",
        "schema_version must be physical_frequency_reducer_preconditions_v1",
    )
    require_text(record.get("record_id"), "record_id")
    status = require_text(record.get("record_status"), "record_status")
    require(status in STATUSES, f"record_status must be one of {sorted(STATUSES)}")
    require(record.get("prototype_authorized") is False, "prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    require(record.get("precondition_mode") == PRECONDITION_MODE, f"precondition_mode must be {PRECONDITION_MODE}")

    validate_source_zone_scope(require_mapping(record.get("source_zone_scope"), "source_zone_scope"), status)
    selected_policy = validate_overlap_policy(require_mapping(record.get("overlap_policy"), "overlap_policy"), status)
    validate_reducer_contract(require_mapping(record.get("reducer_contract"), "reducer_contract"), status)
    validate_uncertainty_propagation(
        require_mapping(record.get("uncertainty_propagation"), "uncertainty_propagation"),
        status,
    )
    validate_dataset_separation(record)
    require_false_fields(
        require_mapping(record.get("claim_boundary"), "claim_boundary"),
        (
            "annual_frequency_supported",
            "physical_probability_supported",
            "return_period_supported",
            "operational_hazard_map_supported",
            "risk_or_exposure_supported",
        ),
    )
    limitations = require_list(record.get("limitations"), "limitations")
    require(limitations, "limitations must be nonempty")
    scan_text_for_misleading_claims(
        record,
        require_fn=lambda condition, message: require(condition, message),
        patterns=MISLEADING_PATTERNS,
    )

    return {
        "schema_version": record["schema_version"],
        "record_id": record["record_id"],
        "record_status": status,
        "selected_overlap_policy": selected_policy,
        "prototype_authorized": False,
    }


def validate_source_zone_scope(scope: dict[str, Any], status: str) -> None:
    source_zone_ids = require_list(scope.get("source_zone_ids"), "source_zone_scope.source_zone_ids")
    require(scope.get("geometry_versions_required") is True, "source_zone_scope.geometry_versions_required must be true")
    require(scope.get("geometry_hashes_required") is True, "source_zone_scope.geometry_hashes_required must be true")
    require(scope.get("crs_epsg") == 2056, "source_zone_scope.crs_epsg must be 2056")
    require(scope.get("vertical_datum") == "LN02", "source_zone_scope.vertical_datum must be LN02")
    if status != "preconditions_not_satisfied":
        require(source_zone_ids, "candidate records require at least one source_zone_id")
        for index, source_zone_id in enumerate(source_zone_ids):
            require_text(source_zone_id, f"source_zone_scope.source_zone_ids[{index}]")


def validate_overlap_policy(policy: dict[str, Any], status: str) -> str | None:
    policy_status = require_text(policy.get("status"), "overlap_policy.status")
    selected = policy.get("selected_policy")
    allowed = set(require_list(policy.get("allowed_policies"), "overlap_policy.allowed_policies"))
    missing = sorted(ALLOWED_OVERLAP_POLICIES - allowed)
    require(not missing, f"overlap_policy.allowed_policies missing: {missing}")
    require(policy.get("double_counting_guard_required") is True, "overlap_policy.double_counting_guard_required must be true")
    require(policy.get("reducer_reports_overlap_adjustment") is True, "overlap_policy.reducer_reports_overlap_adjustment must be true")
    require_text(policy.get("shared_release_cell_rule"), "overlap_policy.shared_release_cell_rule")

    if status == "preconditions_not_satisfied":
        require(policy_status == "not_implemented", "template overlap_policy.status must be not_implemented")
        require(selected is None, "template overlap_policy.selected_policy must be empty")
        return None

    require(policy_status in {"defined_for_design_review", "accepted_for_design_review"}, "candidate overlap_policy.status must be defined for review")
    require(isinstance(selected, str), "candidate overlap_policy.selected_policy must be set")
    require(selected in ALLOWED_OVERLAP_POLICIES, f"selected overlap policy must be one of {sorted(ALLOWED_OVERLAP_POLICIES)}")
    require(
        policy["shared_release_cell_rule"] != "required_before_prototype",
        "candidate overlap_policy.shared_release_cell_rule must be explicit",
    )
    return selected


def validate_reducer_contract(contract: dict[str, Any], status: str) -> None:
    contract_status = require_text(contract.get("status"), "reducer_contract.status")
    require(contract.get("deterministic_merge_required") is True, "reducer_contract.deterministic_merge_required must be true")
    require(contract.get("order_independent_required") is True, "reducer_contract.order_independent_required must be true")
    require(contract.get("chunk_manifest_required") is True, "reducer_contract.chunk_manifest_required must be true")
    require(contract.get("output_unit_support_active") is False, "reducer_contract.output_unit_support_active must be false")
    require(
        contract.get("annual_or_physical_output_supported") is False,
        "reducer_contract.annual_or_physical_output_supported must be false",
    )
    records = set(require_list(contract.get("required_input_records"), "reducer_contract.required_input_records"))
    missing = sorted(REQUIRED_INPUT_RECORDS - records)
    require(not missing, f"reducer_contract.required_input_records missing: {missing}")
    if status == "preconditions_not_satisfied":
        require(contract_status == "not_implemented", "template reducer_contract.status must be not_implemented")
    else:
        require(contract_status in {"defined_for_design_review", "accepted_for_design_review"}, "candidate reducer_contract.status must be defined for review")


def validate_uncertainty_propagation(uncertainty: dict[str, Any], status: str) -> None:
    uncertainty_status = require_text(uncertainty.get("status"), "uncertainty_propagation.status")
    components = set(require_list(uncertainty.get("required_components"), "uncertainty_propagation.required_components"))
    missing = sorted(REQUIRED_UNCERTAINTY_COMPONENTS - components)
    require(not missing, f"uncertainty_propagation.required_components missing: {missing}")
    require(uncertainty.get("seed_provenance_required") is True, "uncertainty_propagation.seed_provenance_required must be true")
    require(
        uncertainty.get("calibration_uncertainty_separated_from_validation") is True,
        "uncertainty_propagation.calibration_uncertainty_separated_from_validation must be true",
    )
    summary_fields = require_list(uncertainty.get("output_summary_fields"), "uncertainty_propagation.output_summary_fields")
    method = uncertainty.get("propagation_method")
    if status == "preconditions_not_satisfied":
        require(uncertainty_status == "not_implemented", "template uncertainty_propagation.status must be not_implemented")
        require(method is None, "template uncertainty_propagation.propagation_method must be empty")
        require(not summary_fields, "template uncertainty_propagation.output_summary_fields must be empty")
    else:
        require(
            uncertainty_status in {"defined_for_design_review", "accepted_for_design_review"},
            "candidate uncertainty_propagation.status must be defined for review",
        )
        require_text(method, "uncertainty_propagation.propagation_method")
        require(summary_fields, "candidate uncertainty_propagation.output_summary_fields must be nonempty")
        for index, field in enumerate(summary_fields):
            require_text(field, f"uncertainty_propagation.output_summary_fields[{index}]")


def validate_dataset_separation(record: dict[str, Any]) -> None:
    calibration = set(require_list(record.get("calibration_dataset_ids"), "calibration_dataset_ids"))
    validation = set(require_list(record.get("validation_dataset_ids"), "validation_dataset_ids"))
    overlap = sorted(calibration & validation)
    require(not overlap, f"calibration and validation dataset ids must be separate: {overlap}")
    invalid_validation = sorted(dataset for dataset in validation if "swisstopo" in str(dataset).lower())
    require(not invalid_validation, f"swisstopo geodata must not be listed as validation evidence: {invalid_validation}")


if __name__ == "__main__":
    raise SystemExit(main())
