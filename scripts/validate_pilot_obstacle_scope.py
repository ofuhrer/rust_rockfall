#!/usr/bin/env python3
"""Validate a pilot forest/obstacle omission scope record.

The record is a share-safe interpretation gate. It does not download context
geodata, add obstacle physics, define exposure/vulnerability, or approve an
operational hazard product.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CONTEXT_CATEGORIES = {
    "forest_or_canopy",
    "buildings_or_structures",
    "roads_or_transport",
    "barriers_or_protection",
    "water_or_channel",
    "orthophoto_visual_context",
}
CLASSIFICATIONS = {"acceptable", "limiting", "invalidating"}
DATASET_STATUSES = {
    "available_reviewed",
    "documented_not_downloaded",
    "not_available",
    "deferred",
}
MISLEADING_PATTERNS = [
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\bexpected\s+loss\b", re.IGNORECASE),
    re.compile(r"\bexposure\s+model\b", re.IGNORECASE),
    re.compile(r"\bvulnerability\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
]


class ObstacleScopeError(ValueError):
    """User-facing obstacle scope validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_scope_record(args.record)
    except ObstacleScopeError as exc:
        print(f"pilot obstacle scope validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "pilot obstacle scope record is valid: "
            f"{args.record} "
            f"({summary['classification']}, {summary['context_category_count']} categories)"
        )
    return 0


def validate_scope_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "pilot_obstacle_scope_v1",
        "schema_version must be pilot_obstacle_scope_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    classification = require_text(record.get("classification"), "classification")
    require(classification in CLASSIFICATIONS, f"classification must be one of {sorted(CLASSIFICATIONS)}")
    require_text(record.get("classification_rationale"), "classification_rationale")

    inputs = require_mapping(record.get("input_scope"), "input_scope")
    require(inputs.get("changes_physics") is False, "input_scope.changes_physics must be false")
    require(inputs.get("changes_defaults") is False, "input_scope.changes_defaults must be false")
    require(inputs.get("adds_obstacle_model") is False, "input_scope.adds_obstacle_model must be false")
    require(inputs.get("adds_risk_or_exposure_model") is False, "input_scope.adds_risk_or_exposure_model must be false")

    contexts = validate_context_inventory(require_list(record.get("context_inventory"), "context_inventory"))
    limitation = require_mapping(record.get("omission_interpretation"), "omission_interpretation")
    require_text(limitation.get("summary"), "omission_interpretation.summary")
    require_text(limitation.get("required_before_interpretation"), "omission_interpretation.required_before_interpretation")
    require_list(limitation.get("do_not_tune_to_absorb_omission"), "omission_interpretation.do_not_tune_to_absorb_omission")

    claim_boundary = require_mapping(record.get("claim_boundary"), "claim_boundary")
    require(claim_boundary.get("operational_status") == "research_diagnostic", "claim_boundary.operational_status must remain research_diagnostic")
    require(claim_boundary.get("annualized") is False, "claim_boundary.annualized must be false")
    require(claim_boundary.get("physical_probability") is False, "claim_boundary.physical_probability must be false")
    require(claim_boundary.get("risk_or_exposure") is False, "claim_boundary.risk_or_exposure must be false")
    require(claim_boundary.get("obstacle_physics_implemented") is False, "claim_boundary.obstacle_physics_implemented must be false")

    evidence = require_mapping(record.get("evidence"), "evidence")
    require_list(evidence.get("reviewed_documents"), "evidence.reviewed_documents")
    require_list(evidence.get("required_future_context_downloads"), "evidence.required_future_context_downloads")

    if classification == "acceptable":
        reviewed = [item for item in contexts if item["status"] == "available_reviewed"]
        require(reviewed, "acceptable classification requires at least one reviewed context dataset")
        require(
            not evidence.get("required_future_context_downloads"),
            "acceptable classification cannot require future context downloads",
        )
    elif classification == "limiting":
        require(
            evidence.get("required_future_context_downloads"),
            "limiting classification requires explicit future context downloads or review actions",
        )
    elif classification == "invalidating":
        require_text(record.get("invalidating_reason"), "invalidating_reason")

    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "classification": classification,
        "context_category_count": len(contexts),
        "reviewed_context_count": sum(1 for item in contexts if item["status"] == "available_reviewed"),
        "future_context_download_count": len(evidence.get("required_future_context_downloads", [])),
        "operational_status": claim_boundary["operational_status"],
    }


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise ObstacleScopeError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ObstacleScopeError(f"YAML document must be an object: {path}")
    return data


def validate_context_inventory(raw_items: list[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    for index, raw in enumerate(raw_items):
        item = require_mapping(raw, f"context_inventory[{index}]")
        category = require_text(item.get("category"), f"context_inventory[{index}].category")
        require(category not in seen_categories, f"duplicate context category: {category}")
        seen_categories.add(category)
        dataset_id = require_text(item.get("dataset_id"), f"context_inventory[{index}].dataset_id")
        require(dataset_id.startswith("swisstopo_") or dataset_id.startswith("local_"), f"unsupported dataset id: {dataset_id}")
        status = require_text(item.get("status"), f"context_inventory[{index}].status")
        require(status in DATASET_STATUSES, f"context_inventory[{index}].status must be one of {sorted(DATASET_STATUSES)}")
        role = require_text(item.get("role"), f"context_inventory[{index}].role")
        require("risk" not in role.lower(), f"context_inventory[{index}].role must not define risk semantics")
        require_text(item.get("interpretation"), f"context_inventory[{index}].interpretation")
        items.append({"category": category, "dataset_id": dataset_id, "status": status, "role": role})
    missing = sorted(REQUIRED_CONTEXT_CATEGORIES - seen_categories)
    require(not missing, f"missing required context categories: {missing}")
    return items


def scan_text_for_misleading_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"claim_boundary", "deferred_or_unsupported_labels"}:
                continue
            scan_text_for_misleading_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("unsupported", "not ", "no ", "without ", "defer", "future", "out of scope")):
            return
        for pattern in MISLEADING_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ObstacleScopeError(message)


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
