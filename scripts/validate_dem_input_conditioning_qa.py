#!/usr/bin/env python3
"""Validate the DT-07 real-site DEM/input conditioning QA record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_CLASSIFICATIONS = {
    "passed",
    "blocked_pending_local_evidence",
    "diagnostic_incomplete",
    "no_go",
}
REQUIRED_REFERENCES = {
    "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
    "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
    "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
    "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
    "docs/public_real_site_geodata_preparation.md",
    "docs/swiss_terrain_ingestion_pilot.md",
    "docs/dem_terrain_sensitivity_benchmark.md",
}
REQUIRED_BLOCKERS = {
    "raw_inputs_not_locally_reverified",
    "processed_artifacts_not_locally_reexecuted",
    "registration_and_transform_not_locally_rechecked",
    "nodata_and_boundary_checks_not_revalidated",
    "slope_sink_spike_screens_not_reexecuted",
    "strict_vs_clamped_behavior_requires_explicit_interpretation",
}
PROHIBITED_PATTERNS = [
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bphysical\s+probability\b", re.IGNORECASE),
    re.compile(r"\btune(?:d|ing)?\b", re.IGNORECASE),
    re.compile(r"\bphysics\s+change\b", re.IGNORECASE),
    re.compile(r"\bDEM\s+behavior\s+change\b", re.IGNORECASE),
]


class DemInputConditioningQAError(ValueError):
    """User-facing DEM/input QA validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_dem_input_conditioning_qa(args.record)
    except DemInputConditioningQAError as exc:
        print(f"DEM/input QA validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "DEM/input QA record is valid: "
            f"{args.record} ({summary['current_classification']}, "
            f"qa_status={summary['qa_status']})"
        )
    return 0


def validate_dem_input_conditioning_qa(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(record.get("schema_version") == "dem_input_conditioning_qa_v1", "schema_version must be dem_input_conditioning_qa_v1")
    require_text(record.get("record_id"), "record_id")
    require_text(record.get("pilot_id"), "pilot_id")
    require(record.get("roadmap_item") == "DT-07", "roadmap_item must be DT-07")
    require(record.get("stochastic_or_physics_change_claimed") is False, "stochastic_or_physics_change_claimed must be false")
    require(record.get("dem_behavior_change_claimed") is False, "dem_behavior_change_claimed must be false")
    require(record.get("tuning_claimed") is False, "tuning_claimed must be false")
    require(record.get("operational_or_annual_claimed") is False, "operational_or_annual_claimed must be false")
    assessed = require_mapping(record.get("assessed_domain"), "assessed_domain")
    require_text(assessed.get("name"), "assessed_domain.name")
    require_text(assessed.get("selected_manifest_path"), "assessed_domain.selected_manifest_path")
    require_text(assessed.get("selected_pilot_classification"), "assessed_domain.selected_pilot_classification")
    input_freeze = require_mapping(record.get("input_freeze"), "input_freeze")
    for field in (
        "geodata_manifest_path",
        "terrain_metadata_path",
        "source_zone_metadata_path",
        "scenario_table_path",
        "source_scenario_policy_path",
    ):
        require_text(input_freeze.get(field), f"input_freeze.{field}")
    current_classification = require_text(record.get("current_classification"), "current_classification")
    require(current_classification in ALLOWED_CLASSIFICATIONS, f"current_classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}")
    qa_status = require_text(record.get("qa_status"), "qa_status")
    require(qa_status in {"diagnostic_incomplete", "blocked_pending_local_evidence", "passed", "no_go"}, "qa_status must be conservative")

    validate_status_block(require_mapping(record.get("raw_input_evidence"), "raw_input_evidence"), "raw_input_evidence")
    validate_status_block(require_mapping(record.get("atomic_ingest_and_checksum"), "atomic_ingest_and_checksum"), "atomic_ingest_and_checksum")
    validate_status_block(require_mapping(record.get("crs_and_registration_evidence"), "crs_and_registration_evidence"), "crs_and_registration_evidence")
    validate_status_block(require_mapping(record.get("nodata_policy"), "nodata_policy"), "nodata_policy")
    validate_status_block(require_mapping(record.get("terrain_sanity_checks"), "terrain_sanity_checks"), "terrain_sanity_checks")
    validate_status_block(require_mapping(record.get("boundary_and_terrain_error_semantics"), "boundary_and_terrain_error_semantics"), "boundary_and_terrain_error_semantics")
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))

    references = require_list(record.get("referenced_records"), "referenced_records")
    reference_values = [require_text(reference, f"referenced_records[{index}]") for index, reference in enumerate(references)]
    missing_refs = sorted(REQUIRED_REFERENCES - set(reference_values))
    require(not missing_refs, f"referenced_records missing: {missing_refs}")

    blockers = require_list(record.get("required_blockers"), "required_blockers")
    blocker_values = [require_text(blocker, f"required_blockers[{index}]") for index, blocker in enumerate(blockers)]
    blocker_set = set(blocker_values)
    if current_classification != "passed":
        missing_blockers = sorted(REQUIRED_BLOCKERS - blocker_set)
        require(not missing_blockers, f"required_blockers missing: {missing_blockers}")
        require(blockers, "non-passed records must keep blockers or limitations visible")
        limitations = require_list(record.get("limitations"), "limitations")
        require(limitations, "non-passed records must keep limitations visible")
    else:
        require(not blockers, "passed records must not retain blockers")
        for section_name in (
            "raw_input_evidence",
            "atomic_ingest_and_checksum",
            "crs_and_registration_evidence",
            "nodata_policy",
            "terrain_sanity_checks",
            "boundary_and_terrain_error_semantics",
        ):
            require(
                record[section_name].get("status") == "complete",
                f"passed records require {section_name}.status = complete",
            )
        limitations = require_list(record.get("limitations", []), "limitations")
        require(not limitations, "passed records must not retain limitations")

    notes = require_list(record.get("notes"), "notes")
    require(notes, "notes must be nonempty")
    for index, note in enumerate(notes):
        require_text(note, f"notes[{index}]")

    scan_text_for_prohibited_claims(record)
    return {
        "schema_version": record["schema_version"],
        "record_id": record["record_id"],
        "current_classification": current_classification,
        "qa_status": qa_status,
    }


def validate_status_block(section: dict[str, Any], field: str) -> None:
    require_text(section.get("status"), f"{field}.status")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "physics_changes_claimed",
        "dem_behavior_changes_claimed",
        "tuning_claimed",
        "annual_or_physical_probability_claimed",
        "risk_exposure_or_operational_claimed",
        "return_period_claimed",
        "validated_hazard_map_claimed",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")


def scan_text_for_prohibited_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_text_for_prohibited_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_prohibited_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in PROHIBITED_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains prohibited current-product claim: {value!r}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise DemInputConditioningQAError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DemInputConditioningQAError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DemInputConditioningQAError(message)


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
