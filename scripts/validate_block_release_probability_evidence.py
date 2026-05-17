#!/usr/bin/env python3
"""Validate inactive block/release probability evidence records.

The schema is a gate input for future design review only. It does not authorize
annual frequency, physical probability, return-period, operational, or risk
products.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from functools import partial
from collections import defaultdict
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
    "no_accepted_block_release_probability_evidence",
    "candidate_not_authorized",
    "accepted_for_design_review",
}
PROBABILITY_MODE = "block_release_probability_evidence_only"
BLOCK_DENOMINATOR = "conditional_probability_given_source_event"
RELEASE_DENOMINATOR = "conditional_probability_given_source_event_and_block_scenario"
EVIDENCE_TYPES = {
    "none_available",
    "inventory_measurement",
    "expert_elicitation",
    "calibrated_model",
    "literature_distribution",
    "external_authority_record",
}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]
SUM_TOLERANCE = 1e-9


class BlockReleaseProbabilityEvidenceError(ValueError):
    """User-facing block/release probability evidence validation error."""


require = partial(shared_require, error_cls=BlockReleaseProbabilityEvidenceError)
require_false_fields = partial(shared_require_false_fields, error_cls=BlockReleaseProbabilityEvidenceError)
require_list = partial(shared_require_list, error_cls=BlockReleaseProbabilityEvidenceError)
require_mapping = partial(shared_require_mapping, error_cls=BlockReleaseProbabilityEvidenceError)
require_text = partial(shared_require_text, error_cls=BlockReleaseProbabilityEvidenceError)
read_yaml = partial(shared_read_yaml, error_cls=BlockReleaseProbabilityEvidenceError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_block_release_probability_evidence(args.record)
    except BlockReleaseProbabilityEvidenceError as exc:
        print(f"block/release probability evidence validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            render_status_message(
                "block/release probability evidence record",
                args.record,
                summary,
                "record_status",
                extra_fields=(
                    ("block_scenario_count", "block_scenario_count"),
                    ("release_cell_count", "release_cell_count"),
                ),
            )
        )
    return 0


def validate_block_release_probability_evidence(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "block_release_probability_evidence_v1",
        "schema_version must be block_release_probability_evidence_v1",
    )
    require_text(record.get("record_id"), "record_id")
    status = require_text(record.get("record_status"), "record_status")
    require(status in STATUSES, f"record_status must be one of {sorted(STATUSES)}")
    require(record.get("prototype_authorized") is False, "prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    require(record.get("probability_mode") == PROBABILITY_MODE, f"probability_mode must be {PROBABILITY_MODE}")
    require_text(record.get("source_zone_id"), "source_zone_id")
    require_text(record.get("source_geometry_version"), "source_geometry_version")
    require_text(record.get("source_geometry_hash"), "source_geometry_hash")
    require(record.get("crs_epsg") == 2056, "crs_epsg must be 2056")
    require(record.get("vertical_datum") == "LN02", "vertical_datum must be LN02")
    require_text(record.get("source_event_class_id"), "source_event_class_id")

    block_ids = validate_block_distribution(
        require_mapping(record.get("block_scenario_distribution"), "block_scenario_distribution"),
        status,
    )
    release_count = validate_release_distribution(
        require_mapping(record.get("release_cell_distribution"), "release_cell_distribution"),
        block_ids,
        status,
    )
    validate_sampling_weight_boundary(
        require_mapping(record.get("sampling_weight_boundary"), "sampling_weight_boundary")
    )
    validate_uncertainty(require_mapping(record.get("uncertainty"), "uncertainty"), status)
    validate_evidence_basis(require_mapping(record.get("evidence_basis"), "evidence_basis"), status)
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
        "block_scenario_count": len(block_ids),
        "release_cell_count": release_count,
        "prototype_authorized": False,
    }


def validate_block_distribution(distribution: dict[str, Any], status: str) -> set[str]:
    require(distribution.get("denominator") == BLOCK_DENOMINATOR, f"block_scenario_distribution.denominator must be {BLOCK_DENOMINATOR}")
    scenarios = require_list(distribution.get("scenarios"), "block_scenario_distribution.scenarios")
    total = distribution.get("total_probability")
    if status == "no_accepted_block_release_probability_evidence":
        require(not scenarios, "template records must leave block scenarios empty")
        require(total is None, "template records must leave block total_probability empty")
        return set()

    require(isinstance(total, int | float), "candidate records require block_scenario_distribution.total_probability")
    require_probability_sum(float(total), "block_scenario_distribution.total_probability")
    require(scenarios, "candidate records require at least one block scenario")
    seen: set[str] = set()
    probability_sum = 0.0
    for index, scenario in enumerate(scenarios):
        item = require_mapping(scenario, f"block_scenario_distribution.scenarios[{index}]")
        scenario_id = require_text(item.get("block_scenario_id"), f"block_scenario_distribution.scenarios[{index}].block_scenario_id")
        require(scenario_id not in seen, f"duplicate block_scenario_id: {scenario_id}")
        seen.add(scenario_id)
        require_text(item.get("block_size_class"), f"{scenario_id}.block_size_class")
        require_text(item.get("block_shape_class"), f"{scenario_id}.block_shape_class")
        probability = item.get("probability")
        require(isinstance(probability, int | float) and probability > 0, f"{scenario_id}.probability must be positive")
        probability_sum += float(probability)
        require_text(item.get("evidence_basis"), f"{scenario_id}.evidence_basis")
    require_probability_sum(probability_sum, "block scenario probabilities")
    return seen


def validate_release_distribution(distribution: dict[str, Any], block_ids: set[str], status: str) -> int:
    require(distribution.get("denominator") == RELEASE_DENOMINATOR, f"release_cell_distribution.denominator must be {RELEASE_DENOMINATOR}")
    totals = require_list(distribution.get("total_probability_by_block_scenario"), "release_cell_distribution.total_probability_by_block_scenario")
    cells = require_list(distribution.get("release_cells"), "release_cell_distribution.release_cells")
    if status == "no_accepted_block_release_probability_evidence":
        require(not totals, "template records must leave release totals empty")
        require(not cells, "template records must leave release cells empty")
        return 0

    require(block_ids, "candidate release distribution requires block scenarios")
    expected_totals = validate_release_totals(totals, block_ids)
    seen_cells: set[tuple[str, str]] = set()
    probability_by_block: dict[str, float] = defaultdict(float)
    for index, cell in enumerate(cells):
        item = require_mapping(cell, f"release_cell_distribution.release_cells[{index}]")
        block_id = require_text(item.get("block_scenario_id"), f"release_cell_distribution.release_cells[{index}].block_scenario_id")
        require(block_id in block_ids, f"release cell references unknown block_scenario_id: {block_id}")
        cell_id = require_text(item.get("release_cell_id"), f"{block_id}.release_cell_id")
        key = (block_id, cell_id)
        require(key not in seen_cells, f"duplicate release_cell_id for block scenario: {block_id}/{cell_id}")
        seen_cells.add(key)
        probability = item.get("probability")
        require(isinstance(probability, int | float) and probability >= 0, f"{block_id}/{cell_id}.probability must be nonnegative")
        probability_by_block[block_id] += float(probability)
        require_text(item.get("evidence_basis"), f"{block_id}/{cell_id}.evidence_basis")
    for block_id in sorted(block_ids):
        require(block_id in probability_by_block, f"release cells missing for block_scenario_id: {block_id}")
        require_probability_sum(probability_by_block[block_id], f"release-cell probabilities for {block_id}")
        require_probability_sum(expected_totals[block_id], f"release-cell total for {block_id}")
    return len(cells)


def validate_release_totals(totals: list[Any], block_ids: set[str]) -> dict[str, float]:
    require(totals, "candidate records require release totals by block scenario")
    expected: dict[str, float] = {}
    for index, total in enumerate(totals):
        item = require_mapping(total, f"release_cell_distribution.total_probability_by_block_scenario[{index}]")
        block_id = require_text(item.get("block_scenario_id"), f"release total[{index}].block_scenario_id")
        require(block_id in block_ids, f"release total references unknown block_scenario_id: {block_id}")
        require(block_id not in expected, f"duplicate release total for block_scenario_id: {block_id}")
        value = item.get("total_probability")
        require(isinstance(value, int | float), f"release total for {block_id} must be numeric")
        expected[block_id] = float(value)
    missing = sorted(block_ids - set(expected))
    require(not missing, f"release totals missing block_scenario_id values: {missing}")
    return expected


def validate_sampling_weight_boundary(boundary: dict[str, Any]) -> None:
    require(
        boundary.get("sampling_weights_are_physical_probability") is False,
        "sampling_weights_are_physical_probability must be false",
    )
    require(
        boundary.get("sampling_weight_column_allowed_as_probability") is False,
        "sampling_weight_column_allowed_as_probability must be false",
    )


def validate_uncertainty(uncertainty: dict[str, Any], status: str) -> None:
    uncertainty_type = require_text(uncertainty.get("type"), "uncertainty.type")
    require(uncertainty.get("required_before_prototype") is True, "uncertainty.required_before_prototype must be true")
    if status == "no_accepted_block_release_probability_evidence":
        require(uncertainty_type == "not_available", "template records must mark uncertainty not_available")
        return
    require(uncertainty_type in {"interval", "distribution", "expert_range"}, "candidate uncertainty must be interval, distribution, or expert_range")
    require_text(uncertainty.get("notes"), "uncertainty.notes")


def validate_evidence_basis(evidence: dict[str, Any], status: str) -> None:
    block = require_text(evidence.get("block_distribution"), "evidence_basis.block_distribution")
    release = require_text(evidence.get("release_cell_distribution"), "evidence_basis.release_cell_distribution")
    require(block in EVIDENCE_TYPES, f"evidence_basis.block_distribution must be one of {sorted(EVIDENCE_TYPES)}")
    require(release in EVIDENCE_TYPES, f"evidence_basis.release_cell_distribution must be one of {sorted(EVIDENCE_TYPES)}")
    if status != "no_accepted_block_release_probability_evidence":
        require(block != "none_available", "candidate block evidence basis must not be none_available")
        require(release != "none_available", "candidate release evidence basis must not be none_available")


def validate_dataset_separation(record: dict[str, Any]) -> None:
    calibration = set(require_list(record.get("calibration_dataset_ids"), "calibration_dataset_ids"))
    validation = set(require_list(record.get("validation_dataset_ids"), "validation_dataset_ids"))
    overlap = sorted(calibration & validation)
    require(not overlap, f"calibration and validation dataset ids must be separate: {overlap}")
    invalid_validation = sorted(dataset for dataset in validation if "swisstopo" in str(dataset).lower())
    require(not invalid_validation, f"swisstopo geodata must not be listed as validation evidence: {invalid_validation}")


def require_probability_sum(value: float, field: str) -> None:
    require(math.isfinite(value), f"{field} must be finite")
    require(abs(value - 1.0) <= SUM_TOLERANCE, f"{field} must sum to 1.0")


if __name__ == "__main__":
    raise SystemExit(main())
