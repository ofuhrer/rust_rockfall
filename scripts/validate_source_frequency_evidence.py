#!/usr/bin/env python3
"""Validate inactive source-frequency evidence records.

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
    "no_accepted_frequency_evidence",
    "candidate_not_authorized",
    "accepted_for_design_review",
}
EVIDENCE_TYPES = {
    "none_available",
    "inventory_count",
    "expert_elicitation",
    "calibrated_model",
    "external_authority_record",
    "literature_rate",
}
FREQUENCY_UNIT = "events_per_source_zone_per_year"
FREQUENCY_MODE = "source_event_rate_evidence_only"
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]


class SourceFrequencyEvidenceError(ValueError):
    """User-facing source-frequency evidence validation error."""


require = partial(shared_require, error_cls=SourceFrequencyEvidenceError)
require_false_fields = partial(shared_require_false_fields, error_cls=SourceFrequencyEvidenceError)
require_list = partial(shared_require_list, error_cls=SourceFrequencyEvidenceError)
require_mapping = partial(shared_require_mapping, error_cls=SourceFrequencyEvidenceError)
require_text = partial(shared_require_text, error_cls=SourceFrequencyEvidenceError)
read_yaml = partial(shared_read_yaml, error_cls=SourceFrequencyEvidenceError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_source_frequency_evidence(args.record)
    except SourceFrequencyEvidenceError as exc:
        print(f"source-frequency evidence validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            render_status_message(
                "source-frequency evidence record",
                args.record,
                summary,
                "record_status",
                extra_fields=(("source_event_rate_available", "rate_available"),),
            )
        )
    return 0


def validate_source_frequency_evidence(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(record.get("schema_version") == "source_frequency_evidence_v1", "schema_version must be source_frequency_evidence_v1")
    require_text(record.get("record_id"), "record_id")
    status = require_text(record.get("record_status"), "record_status")
    require(status in STATUSES, f"record_status must be one of {sorted(STATUSES)}")
    require(record.get("prototype_authorized") is False, "prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    require(record.get("frequency_mode") == FREQUENCY_MODE, f"frequency_mode must be {FREQUENCY_MODE}")
    require_text(record.get("source_zone_id"), "source_zone_id")
    require_text(record.get("source_geometry_version"), "source_geometry_version")
    require_text(record.get("source_geometry_hash"), "source_geometry_hash")
    require(record.get("crs_epsg") == 2056, "crs_epsg must be 2056")
    require(record.get("vertical_datum") == "LN02", "vertical_datum must be LN02")
    require(record.get("frequency_unit") == FREQUENCY_UNIT, f"frequency_unit must be {FREQUENCY_UNIT}")

    validate_event_class(require_mapping(record.get("source_event_class"), "source_event_class"))
    validate_evidence_type(record)
    rate = validate_rate(record, status)
    validate_uncertainty(require_mapping(record.get("rate_uncertainty"), "rate_uncertainty"), rate, status)
    validate_observation_period(require_mapping(record.get("rate_observation_period"), "rate_observation_period"), status)
    validate_provenance(require_mapping(record.get("rate_provenance"), "rate_provenance"), status)
    validate_overlap_policy(require_mapping(record.get("source_zone_overlap_policy"), "source_zone_overlap_policy"), status)
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
        "source_zone_id": record["source_zone_id"],
        "source_event_rate_available": rate is not None,
        "prototype_authorized": False,
    }


def validate_event_class(event_class: dict[str, Any]) -> None:
    require_text(event_class.get("event_class_id"), "source_event_class.event_class_id")
    require_text(event_class.get("description"), "source_event_class.description")
    require_text(event_class.get("occurrence_denominator"), "source_event_class.occurrence_denominator")


def validate_evidence_type(record: dict[str, Any]) -> None:
    evidence_type = require_text(record.get("rate_evidence_type"), "rate_evidence_type")
    require(evidence_type in EVIDENCE_TYPES, f"rate_evidence_type must be one of {sorted(EVIDENCE_TYPES)}")
    if record["record_status"] != "no_accepted_frequency_evidence":
        require(evidence_type != "none_available", "candidate records require a concrete rate_evidence_type")


def validate_rate(record: dict[str, Any], status: str) -> float | None:
    value = record.get("source_event_rate_per_year")
    if status == "no_accepted_frequency_evidence":
        require(value is None, "no_accepted_frequency_evidence must leave source_event_rate_per_year empty")
        require(record.get("rate_time_window_years") is None, "no_accepted_frequency_evidence must leave rate_time_window_years empty")
        return None
    require(isinstance(value, int | float) and value > 0, "candidate records require positive source_event_rate_per_year")
    window = record.get("rate_time_window_years")
    require(isinstance(window, int | float) and window > 0, "candidate records require positive rate_time_window_years")
    return float(value)


def validate_uncertainty(uncertainty: dict[str, Any], rate: float | None, status: str) -> None:
    uncertainty_type = require_text(uncertainty.get("type"), "rate_uncertainty.type")
    if status == "no_accepted_frequency_evidence":
        require(uncertainty_type == "not_available", "template records must mark uncertainty not_available")
        require(uncertainty.get("lower_per_year") is None, "template uncertainty lower_per_year must be empty")
        require(uncertainty.get("upper_per_year") is None, "template uncertainty upper_per_year must be empty")
        return
    require(uncertainty_type in {"interval", "distribution"}, "candidate uncertainty must be interval or distribution")
    lower = uncertainty.get("lower_per_year")
    upper = uncertainty.get("upper_per_year")
    require(isinstance(lower, int | float) and lower >= 0, "rate_uncertainty.lower_per_year must be nonnegative")
    require(isinstance(upper, int | float) and upper >= lower, "rate_uncertainty.upper_per_year must be >= lower")
    require(rate is not None and lower <= rate <= upper, "rate uncertainty interval must contain source_event_rate_per_year")


def validate_observation_period(period: dict[str, Any], status: str) -> None:
    start = period.get("start_year")
    end = period.get("end_year")
    if status == "no_accepted_frequency_evidence":
        require(start is None and end is None, "template observation period must be empty")
        return
    require(isinstance(start, int), "candidate observation period requires integer start_year")
    require(isinstance(end, int), "candidate observation period requires integer end_year")
    require(end >= start, "rate_observation_period.end_year must be >= start_year")


def validate_provenance(provenance: dict[str, Any], status: str) -> None:
    source = require_text(provenance.get("source"), "rate_provenance.source")
    citation = require_text(provenance.get("citation_or_url"), "rate_provenance.citation_or_url")
    require_text(provenance.get("license"), "rate_provenance.license")
    if status != "no_accepted_frequency_evidence":
        require(source != "none_available", "candidate provenance source must not be none_available")
        require(citation != "none_available", "candidate provenance citation_or_url must not be none_available")


def validate_overlap_policy(policy: dict[str, Any], status: str) -> None:
    policy_name = require_text(policy.get("policy"), "source_zone_overlap_policy.policy")
    adjustment = require_text(policy.get("overlap_adjustment"), "source_zone_overlap_policy.overlap_adjustment")
    if status == "no_accepted_frequency_evidence":
        require(policy_name == "not_defined", "template overlap policy must be not_defined")
        require(adjustment == "required_before_prototype", "template overlap adjustment must remain required")
    else:
        require(
            policy_name in {"mutually_exclusive_partition", "documented_overlap_adjustment"},
            "candidate overlap policy must be mutually_exclusive_partition or documented_overlap_adjustment",
        )
        require(adjustment != "required_before_prototype", "candidate overlap adjustment must be explicit")


def validate_dataset_separation(record: dict[str, Any]) -> None:
    calibration = set(require_list(record.get("calibration_dataset_ids"), "calibration_dataset_ids"))
    validation = set(require_list(record.get("validation_dataset_ids"), "validation_dataset_ids"))
    overlap = sorted(calibration & validation)
    require(not overlap, f"calibration and validation dataset ids must be separate: {overlap}")
    invalid_validation = sorted(dataset for dataset in validation if "swisstopo" in str(dataset).lower())
    require(not invalid_validation, f"swisstopo geodata must not be listed as validation evidence: {invalid_validation}")


if __name__ == "__main__":
    raise SystemExit(main())
