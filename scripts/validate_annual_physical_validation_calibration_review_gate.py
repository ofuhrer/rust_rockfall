#!/usr/bin/env python3
"""Validate inactive annual/physical validation-calibration review records.

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
    "review_not_passed",
    "candidate_not_authorized",
    "accepted_for_design_review",
}
REVIEW_MODE = "annual_physical_validation_calibration_review_only"
REQUIRED_CURRENT_PRODUCTS = {
    "unweighted_diagnostic",
    "sampling_weighted_conditional",
    "conditional_intensity_exceedance",
}
REQUIRED_FUTURE_PRODUCTS = {
    "physical_probability",
    "annual_intensity_frequency",
}
REQUIRED_REFERENCE_FIELDS = {
    "source_frequency_evidence_record",
    "block_release_probability_evidence_record",
    "physical_frequency_reducer_preconditions_record",
}
ALLOWED_MATURITY_LEVELS = {"V0", "V1", "V2", "V3", "V4", "V5"}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]


class AnnualPhysicalValidationCalibrationReviewGateError(ValueError):
    """User-facing validation/calibration review gate error."""


require = partial(shared_require, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)
require_false_fields = partial(shared_require_false_fields, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)
require_list = partial(shared_require_list, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)
require_mapping = partial(shared_require_mapping, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)
require_text = partial(shared_require_text, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)
read_yaml = partial(shared_read_yaml, error_cls=AnnualPhysicalValidationCalibrationReviewGateError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_annual_physical_validation_calibration_review_gate(args.record)
    except AnnualPhysicalValidationCalibrationReviewGateError as exc:
        print(f"annual/physical validation-calibration review gate error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            render_status_message(
                "annual/physical validation-calibration review gate record",
                args.record,
                summary,
                "record_status",
                extra_fields=(("prototype_authorized", "prototype_authorized"),),
            )
        )
    return 0


def validate_annual_physical_validation_calibration_review_gate(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "annual_physical_validation_calibration_review_gate_v1",
        "schema_version must be annual_physical_validation_calibration_review_gate_v1",
    )
    require_text(record.get("record_id"), "record_id")
    status = require_text(record.get("record_status"), "record_status")
    require(status in STATUSES, f"record_status must be one of {sorted(STATUSES)}")
    require(record.get("prototype_authorized") is False, "prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    require(record.get("review_mode") == REVIEW_MODE, f"review_mode must be {REVIEW_MODE}")

    validate_product_scope(require_mapping(record.get("product_scope"), "product_scope"))
    validate_references(require_mapping(record.get("required_record_references"), "required_record_references"), status)
    calibration = validate_review_section(
        require_mapping(record.get("calibration_review"), "calibration_review"),
        "calibration_review",
        status,
        require_objective=True,
    )
    validation = validate_review_section(
        require_mapping(record.get("validation_review"), "validation_review"),
        "validation_review",
        status,
        require_objective=True,
    )
    holdout = validate_review_section(
        require_mapping(record.get("holdout_review"), "holdout_review"),
        "holdout_review",
        status,
        require_objective=False,
    )
    validate_maturity(require_mapping(record.get("validation_review"), "validation_review"), status)
    validate_dataset_role_boundaries(require_mapping(record.get("dataset_role_boundaries"), "dataset_role_boundaries"))
    validate_dataset_separation(calibration, validation, holdout)
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
        "prototype_authorized": False,
        "calibration_dataset_count": len(calibration),
        "validation_dataset_count": len(validation),
        "holdout_dataset_count": len(holdout),
    }


def validate_product_scope(scope: dict[str, Any]) -> None:
    current = set(require_list(scope.get("current_products"), "product_scope.current_products"))
    missing_current = sorted(REQUIRED_CURRENT_PRODUCTS - current)
    require(not missing_current, f"product_scope.current_products missing: {missing_current}")
    future = set(require_list(scope.get("future_products_reviewed"), "product_scope.future_products_reviewed"))
    missing_future = sorted(REQUIRED_FUTURE_PRODUCTS - future)
    require(not missing_future, f"product_scope.future_products_reviewed missing: {missing_future}")
    require(scope.get("runtime_support_added") is False, "product_scope.runtime_support_added must be false")


def validate_references(references: dict[str, Any], status: str) -> None:
    missing = sorted(REQUIRED_REFERENCE_FIELDS - set(references))
    require(not missing, f"required_record_references missing: {missing}")
    if status == "review_not_passed":
        for field in REQUIRED_REFERENCE_FIELDS:
            require(references.get(field) is None, f"template required_record_references.{field} must be empty")
        return
    for field in REQUIRED_REFERENCE_FIELDS:
        require_text(references.get(field), f"required_record_references.{field}")


def validate_review_section(section: dict[str, Any], name: str, status: str, *, require_objective: bool) -> set[Any]:
    review_status = require_text(section.get("status"), f"{name}.status")
    dataset_ids = set(require_list(section.get("dataset_ids"), f"{name}.dataset_ids"))
    if status == "review_not_passed":
        require(review_status == "not_reviewed", f"template {name}.status must be not_reviewed")
        require(not dataset_ids, f"template {name}.dataset_ids must be empty")
        if require_objective:
            require(section.get("objective") is None, f"template {name}.objective must be empty")
    else:
        require(review_status in {"defined_for_design_review", "accepted_for_design_review"}, f"candidate {name}.status must be defined for review")
        require(dataset_ids, f"candidate {name}.dataset_ids must be nonempty")
        if require_objective:
            require_text(section.get("objective"), f"{name}.objective")
    if name == "calibration_review":
        require(
            section.get("no_tuning_to_validation_or_map_pattern") is True,
            "calibration_review.no_tuning_to_validation_or_map_pattern must be true",
        )
    if name == "holdout_review":
        require(
            section.get("external_generalization_required") is True,
            "holdout_review.external_generalization_required must be true",
        )
    return dataset_ids


def validate_maturity(validation_review: dict[str, Any], status: str) -> None:
    target = validation_review.get("maturity_target")
    cap = validation_review.get("current_maturity_cap")
    if status == "review_not_passed":
        require(target is None, "template validation_review.maturity_target must be empty")
        require(cap is None, "template validation_review.current_maturity_cap must be empty")
        return
    require(target in ALLOWED_MATURITY_LEVELS, "validation_review.maturity_target must be a maturity level")
    require(cap in ALLOWED_MATURITY_LEVELS, "validation_review.current_maturity_cap must be a maturity level")
    require(
        int(str(cap)[1:]) <= int(str(target)[1:]),
        "validation_review.current_maturity_cap must not exceed maturity_target",
    )


def validate_dataset_role_boundaries(boundaries: dict[str, Any]) -> None:
    require(
        boundaries.get("calibration_validation_holdout_overlap_allowed") is False,
        "dataset_role_boundaries.calibration_validation_holdout_overlap_allowed must be false",
    )
    require(
        boundaries.get("swisstopo_input_geodata_is_validation_evidence") is False,
        "dataset_role_boundaries.swisstopo_input_geodata_is_validation_evidence must be false",
    )
    require(
        boundaries.get("exposure_or_vulnerability_required_for_risk") is True,
        "dataset_role_boundaries.exposure_or_vulnerability_required_for_risk must be true",
    )


def validate_dataset_separation(calibration: set[Any], validation: set[Any], holdout: set[Any]) -> None:
    overlaps = {
        "calibration/validation": sorted(calibration & validation),
        "calibration/holdout": sorted(calibration & holdout),
        "validation/holdout": sorted(validation & holdout),
    }
    for label, overlap in overlaps.items():
        require(not overlap, f"{label} dataset ids must be separate: {overlap}")
    invalid = sorted(
        dataset
        for dataset in validation | holdout
        if "swisstopo" in str(dataset).lower()
    )
    require(not invalid, f"swisstopo geodata must not be listed as validation or holdout evidence: {invalid}")


if __name__ == "__main__":
    raise SystemExit(main())
