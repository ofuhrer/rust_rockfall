#!/usr/bin/env python3
"""Validate the selected balfrin Tschamut readiness record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


READY_STATUS = "ready_for_balfrin_target_gate"
BLOCKED_STATUS = "blocked_for_balfrin_readiness"
SUPPORTED_STATUSES = {READY_STATUS, BLOCKED_STATUS}
REQUIRED_TOOLCHAIN = {"rustc", "cargo", "python3", "uv"}
REQUIRED_INPUT_ROLES = {
    "geodata_manifest",
    "terrain_metadata",
    "source_zone_metadata",
    "scenario_table",
    "source_scenario_policy",
    "frozen_private_validation_case",
}
REQUIRED_PROCESSED_ROLES = {"processed_public_dem", "processed_public_dem_metadata"}
REQUIRED_COMMANDS = {
    "validate_geodata_manifest",
    "validate_source_scenario_policy",
    "run_validation_gate",
    "build_conditional_hazard_layers",
}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "physical_probability",
    "return_period",
    "risk_map",
    "operational_hazard_map",
}
MISLEADING_PATTERNS = [
    re.compile(r"\boperational(?:ly)?\s+(?:ready|validated|approved)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
]


class BalfrinReadinessRecordError(ValueError):
    """User-facing readiness-record validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        summary = validate_balfrin_readiness_record(args.record)
    except BalfrinReadinessRecordError as exc:
        print(f"balfrin readiness record validation error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "balfrin readiness record is valid: "
            f"{args.record} ({summary['readiness_status']}, "
            f"missing_required_inputs={summary['missing_required_inputs']}, "
            f"missing_processed_artifacts={summary['missing_processed_artifacts']})"
        )
    return 0


def validate_balfrin_readiness_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "balfrin_tschamut_readiness_record_v1",
        "schema_version must be balfrin_tschamut_readiness_record_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    require(record.get("roadmap_item") == "DT-02", "roadmap_item must be DT-02")
    status = require_text(record.get("readiness_status"), "readiness_status")
    require(status in SUPPORTED_STATUSES, f"readiness_status must be one of {sorted(SUPPORTED_STATUSES)}")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    require_text(record.get("checked_at_utc"), "checked_at_utc")
    require_text(record.get("checked_host"), "checked_host")
    require_text(record.get("repo_root"), "repo_root")

    validate_checker(require_mapping(record.get("checker"), "checker"), status)
    validate_repository(require_mapping(record.get("repository"), "repository"))
    validate_toolchain(require_mapping(record.get("toolchain"), "toolchain"))
    validate_paths(require_mapping(record.get("paths"), "paths"))
    missing_inputs = validate_status_group(
        require_mapping(record.get("required_ignored_inputs"), "required_ignored_inputs"),
        required_roles=REQUIRED_INPUT_ROLES,
        context="required_ignored_inputs",
        ready_status=status == READY_STATUS,
    )
    missing_processed = validate_status_group(
        require_mapping(record.get("processed_artifacts"), "processed_artifacts"),
        required_roles=REQUIRED_PROCESSED_ROLES,
        context="processed_artifacts",
        ready_status=status == READY_STATUS,
    )
    validate_command_plan_preconditions(
        require_mapping(record.get("command_plan_preconditions"), "command_plan_preconditions"),
        status,
    )
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    require_text(record.get("conclusion"), "conclusion")
    require_text(record.get("next_step"), "next_step")
    scan_text_for_misleading_claims(record)

    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "readiness_status": status,
        "missing_required_inputs": missing_inputs,
        "missing_processed_artifacts": missing_processed,
    }


def validate_checker(checker: dict[str, Any], status: str) -> None:
    require(checker.get("script") == "scripts/check_balfrin_tschamut_readiness.py", "checker.script must be the readiness checker")
    require_text(checker.get("command"), "checker.command")
    require(isinstance(checker.get("returncode"), int), "checker.returncode must be an integer")
    require(checker.get("output_status") == status, "checker.output_status must match readiness_status")
    blocking_count = require_nonnegative_int(checker.get("blocking_check_count"), "checker.blocking_check_count")
    require_nonnegative_int(checker.get("warning_check_count"), "checker.warning_check_count")
    require(checker.get("raw_json_committed") is False, "checker.raw_json_committed must be false")
    if status == READY_STATUS:
        require(checker.get("returncode") == 0, "ready records must have checker returncode 0")
        require(blocking_count == 0, "ready records must have zero blocking checks")
    else:
        require(checker.get("returncode") != 0, "blocked records must have nonzero checker returncode")
        require(blocking_count > 0, "blocked records must include blocking checks")


def validate_repository(repository: dict[str, Any]) -> None:
    require_text(repository.get("branch"), "repository.branch")
    commit = require_text(repository.get("commit"), "repository.commit")
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "repository.commit must be a full SHA-1")
    require_text(repository.get("git_status_summary"), "repository.git_status_summary")
    require(isinstance(repository.get("untracked_files_present"), bool), "repository.untracked_files_present must be boolean")


def validate_toolchain(toolchain: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_TOOLCHAIN - set(toolchain))
    require(not missing, f"toolchain missing required tools: {missing}")
    for name in REQUIRED_TOOLCHAIN:
        entry = require_mapping(toolchain.get(name), f"toolchain.{name}")
        require(entry.get("available") is True, f"toolchain.{name}.available must be true")
        require_text(entry.get("version"), f"toolchain.{name}.version")
    qgis = require_mapping(toolchain.get("qgis"), "toolchain.qgis")
    require(qgis.get("required_for_readiness") is False, "toolchain.qgis.required_for_readiness must be false")


def validate_paths(paths: dict[str, Any]) -> None:
    for field in ("target_run_manifest", "validation_private_root", "hazard_results_root", "frozen_private_case"):
        entry = require_mapping(paths.get(field), f"paths.{field}")
        require_text(entry.get("path"), f"paths.{field}.path")
        status = require_text(entry.get("status"), f"paths.{field}.status")
        require(status in {"present", "writable"}, f"paths.{field}.status must be present or writable")


def validate_status_group(
    group: dict[str, Any],
    *,
    required_roles: set[str],
    context: str,
    ready_status: bool,
) -> int:
    status = require_text(group.get("status"), f"{context}.status")
    missing_count = require_nonnegative_int(group.get("missing_required_count"), f"{context}.missing_required_count")
    items = require_list(group.get("items"), f"{context}.items")
    roles = set()
    missing_roles = set()
    for item in items:
        row = require_mapping(item, f"{context}.items[]")
        role = require_text(row.get("role"), f"{context}.items[].role")
        roles.add(role)
        require_text(row.get("path"), f"{context}.items[{role}].path")
        row_status = require_text(row.get("status"), f"{context}.items[{role}].status")
        if row_status == "missing":
            missing_roles.add(role)
    require(not (required_roles - roles), f"{context}.items missing roles: {sorted(required_roles - roles)}")
    require(missing_count == len(missing_roles), f"{context}.missing_required_count does not match missing item count")
    if ready_status:
        require(status == "present", f"{context}.status must be present for ready records")
        require(missing_count == 0, f"{context}.missing_required_count must be 0 for ready records")
    return missing_count


def validate_command_plan_preconditions(preconditions: dict[str, Any], status: str) -> None:
    plan_status = require_text(preconditions.get("status"), "command_plan_preconditions.status")
    commands = set(require_list(preconditions.get("required_commands_present"), "command_plan_preconditions.required_commands_present"))
    missing = sorted(REQUIRED_COMMANDS - commands)
    require(not missing, f"command_plan_preconditions.required_commands_present missing: {missing}")
    require(isinstance(preconditions.get("required_inputs_present"), bool), "required_inputs_present must be boolean")
    require(
        isinstance(preconditions.get("required_output_locations_writable"), bool),
        "required_output_locations_writable must be boolean",
    )
    if status == READY_STATUS:
        require(plan_status == "pass", "ready records must have command_plan_preconditions.status pass")
        require(preconditions.get("required_inputs_present") is True, "ready records must have required inputs present")
        require(
            preconditions.get("required_output_locations_writable") is True,
            "ready records must have writable output locations",
        )


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    for field in (
        "generated_outputs_committed",
        "raw_geodata_committed",
        "changes_physics",
        "changes_defaults",
        "annualized",
        "physical_probability",
        "return_period",
        "risk_or_exposure",
        "operational_hazard_map",
    ):
        require(boundary.get(field) is False, f"claim_boundary.{field} must be false")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "claim_boundary.unsupported_current_claims"))
    require(
        REQUIRED_UNSUPPORTED_CLAIMS.issubset(unsupported),
        f"claim_boundary.unsupported_current_claims missing: {sorted(REQUIRED_UNSUPPORTED_CLAIMS - unsupported)}",
    )


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
            require(
                "out of scope" in value.lower() or "unsupported" in value.lower(),
                f"{context} contains potentially misleading phrase without out-of-scope framing: {value!r}",
            )


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should report path context.
        raise BalfrinReadinessRecordError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BalfrinReadinessRecordError(f"record must be a YAML mapping: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BalfrinReadinessRecordError(message)


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BalfrinReadinessRecordError(f"{context} must be a mapping")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise BalfrinReadinessRecordError(f"{context} must be a list")
    return value


def require_text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BalfrinReadinessRecordError(f"{context} must be a non-empty string")
    return value


def require_nonnegative_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BalfrinReadinessRecordError(f"{context} must be a non-negative integer")
    return value


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
