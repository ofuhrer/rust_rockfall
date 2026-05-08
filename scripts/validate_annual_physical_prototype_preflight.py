#!/usr/bin/env python3
"""Validate the annual/physical prototype preflight record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_STATUS = "blocked_by_design_gate"
REQUIRED_REMAINING_BLOCKERS = {
    "accepted_source_frequency_evidence",
    "accepted_block_release_probability_evidence",
    "implemented_overlap_adjusted_reducers",
    "implemented_uncertainty_propagation",
    "accepted_validation_calibration_review",
}
REQUIRED_FUTURE_MODES = {"physical_probability", "annual_intensity_frequency"}
MISLEADING_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
]


class AnnualPhysicalPrototypePreflightError(ValueError):
    """User-facing preflight validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_prototype_preflight(args.record)
    except AnnualPhysicalPrototypePreflightError as exc:
        print(f"annual/physical prototype preflight validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "annual/physical prototype preflight record is valid: "
            f"{args.record} ({summary['record_status']}, "
            f"prototype_authorized={summary['prototype_authorized']})"
        )
    return 0


def validate_prototype_preflight(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "annual_physical_prototype_preflight_v1",
        "schema_version must be annual_physical_prototype_preflight_v1",
    )
    require_text(record.get("record_id"), "record_id")
    require(record.get("record_status") == REQUIRED_STATUS, f"record_status must be {REQUIRED_STATUS}")
    require(record.get("prototype_authorized") is False, "prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must be research_diagnostic")
    require(
        record.get("preflight_mode") == "annual_physical_prototype_preflight_only",
        "preflight_mode must be annual_physical_prototype_preflight_only",
    )
    require(record.get("runtime_support_added") is False, "runtime_support_added must be false")

    future_modes = set(require_list(record.get("requested_future_product_modes"), "requested_future_product_modes"))
    missing_modes = sorted(REQUIRED_FUTURE_MODES - future_modes)
    require(not missing_modes, f"requested_future_product_modes missing: {missing_modes}")

    blockers = set(require_list(record.get("remaining_blockers"), "remaining_blockers"))
    missing_blockers = sorted(REQUIRED_REMAINING_BLOCKERS - blockers)
    require(not missing_blockers, f"remaining_blockers missing: {missing_blockers}")

    gate_summary = validate_design_gate_reference(record)
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    limitations = set(require_list(record.get("limitations"), "limitations"))
    require(
        any("blocked by the deferred design gate" in str(item) for item in limitations),
        "limitations must state the prototype is blocked by the deferred design gate",
    )
    require(
        any("no annual frequency or physical probability runtime support" in str(item) for item in limitations),
        "limitations must state no annual/physical runtime support is implemented",
    )
    scan_text_for_misleading_claims(record)

    return {
        "schema_version": record["schema_version"],
        "record_id": record["record_id"],
        "record_status": record["record_status"],
        "prototype_authorized": record["prototype_authorized"],
        "design_gate_decision": gate_summary["decision"],
        "design_gate_authorized": gate_summary["authorized"],
        "remaining_blocker_count": len(blockers),
    }


def validate_design_gate_reference(record: dict[str, Any]) -> dict[str, Any]:
    path_text = require_text(record.get("design_gate_record"), "design_gate_record")
    gate_path = (REPO_ROOT / path_text).resolve()
    require(gate_path.is_file(), f"design_gate_record does not exist: {path_text}")
    require(REPO_ROOT in gate_path.parents, "design_gate_record must stay inside the repository")
    gate = read_yaml(gate_path)
    require(
        gate.get("schema_version") == "physical_source_frequency_design_gate_v1",
        "design_gate_record must be physical_source_frequency_design_gate_v1",
    )
    observed_decision = require_text(record.get("observed_design_gate_decision"), "observed_design_gate_decision")
    observed_authorized = record.get("observed_design_gate_authorized")
    require(isinstance(observed_authorized, bool), "observed_design_gate_authorized must be boolean")
    require(observed_decision == gate.get("decision"), "observed_design_gate_decision must match design gate")
    require(
        observed_authorized == gate.get("annual_physical_prototype_authorized"),
        "observed_design_gate_authorized must match design gate",
    )
    required_decision = require_text(
        record.get("required_design_gate_decision_before_prototype"),
        "required_design_gate_decision_before_prototype",
    )
    require(required_decision == "authorize_prototype", "required design gate decision must be authorize_prototype")
    require(gate.get("decision") == "deferred", "current preflight expects the design gate to remain deferred")
    require(
        gate.get("annual_physical_prototype_authorized") is False,
        "current preflight expects prototype authorization to remain false",
    )
    require(
        gate.get("gate_reassessment", {}).get("assessment_status") == "deferred_after_inactive_contract_review",
        "design gate must record deferred inactive-contract reassessment",
    )
    blocker_contracts = require_list(gate.get("blocker_contracts"), "design_gate.blocker_contracts")
    require(blocker_contracts, "design gate must list blocker contracts")
    require(
        all(require_mapping(item, "design_gate.blocker_contracts[]").get("prototype_blocker") is True for item in blocker_contracts),
        "all inactive design-gate contracts must remain prototype blockers",
    )
    return {
        "decision": gate["decision"],
        "authorized": gate["annual_physical_prototype_authorized"],
    }


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "annual_frequency_supported",
        "physical_probability_supported",
        "return_period_supported",
        "operational_hazard_map_supported",
        "risk_or_exposure_supported",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")


def scan_text_for_misleading_claims(record: dict[str, Any]) -> None:
    text = yaml.safe_dump(record, sort_keys=True)
    allowed_phrases = {
        "return_period_supported",
        "risk_or_exposure_supported",
        "operational_hazard_map_supported",
    }
    scrubbed = text
    for phrase in allowed_phrases:
        scrubbed = scrubbed.replace(phrase, "")
    for pattern in MISLEADING_PATTERNS:
        match = pattern.search(scrubbed)
        if match is not None:
            raise AnnualPhysicalPrototypePreflightError(
                f"unsupported claim language found: {match.group(0)!r}"
            )


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AnnualPhysicalPrototypePreflightError(f"unable to read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise AnnualPhysicalPrototypePreflightError(f"invalid YAML in {path}: {exc}") from exc
    require(isinstance(data, dict), f"{path} must contain a YAML mapping")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AnnualPhysicalPrototypePreflightError(message)


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be a mapping")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
