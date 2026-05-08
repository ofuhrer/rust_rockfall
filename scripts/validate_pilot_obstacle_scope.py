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
TARGET_REVIEW_STATUSES = {
    "blocked_missing_context_layers",
    "reviewed_accepting_omission",
    "reviewed_limiting_omission",
    "reviewed_invalidating_omission",
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
    target_review = validate_target_scale_review(
        require_mapping(record.get("target_scale_review"), "target_scale_review"),
        classification,
    )

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
    validate_local_artifact_probe(require_mapping(evidence.get("local_artifact_probe"), "evidence.local_artifact_probe"), target_review)

    if classification == "acceptable":
        reviewed = [item for item in contexts if item["status"] == "available_reviewed"]
        require(reviewed, "acceptable classification requires at least one reviewed context dataset")
        require(
            target_review["status"] == "reviewed_accepting_omission",
            "acceptable classification requires reviewed_accepting_omission target-scale review",
        )
        require(
            not evidence.get("required_future_context_downloads"),
            "acceptable classification cannot require future context downloads",
        )
    elif classification == "limiting":
        require(
            evidence.get("required_future_context_downloads"),
            "limiting classification requires explicit future context downloads or review actions",
        )
        require(
            target_review["status"] in {"blocked_missing_context_layers", "reviewed_limiting_omission"},
            "limiting classification requires blocked or reviewed limiting target-scale context status",
        )
    elif classification == "invalidating":
        require_text(record.get("invalidating_reason"), "invalidating_reason")
        require(
            target_review["status"] == "reviewed_invalidating_omission",
            "invalidating classification requires reviewed_invalidating_omission target-scale review",
        )

    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "classification": classification,
        "context_category_count": len(contexts),
        "reviewed_context_count": sum(1 for item in contexts if item["status"] == "available_reviewed"),
        "target_scale_context_review_status": target_review["status"],
        "missing_context_artifact_count": target_review["missing_context_artifact_count"],
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


def validate_target_scale_review(section: dict[str, Any], classification: str) -> dict[str, Any]:
    require_text(section.get("target_gate_record_path"), "target_scale_review.target_gate_record_path")
    require(section.get("target_gate_status") == "inconclusive", "target_scale_review.target_gate_status must be inconclusive")
    require_text(
        section.get("target_package_visual_qa_record_path"),
        "target_scale_review.target_package_visual_qa_record_path",
    )
    require(
        section.get("target_package_visual_qa_status") in {"blocked", "pass", "no-go", "inconclusive"},
        "target_scale_review.target_package_visual_qa_status must be classified",
    )
    status = require_text(section.get("local_context_review_status"), "target_scale_review.local_context_review_status")
    require(status in TARGET_REVIEW_STATUSES, f"target_scale_review.local_context_review_status must be one of {sorted(TARGET_REVIEW_STATUSES)}")
    require(section.get("context_artifacts_committed") is False, "target_scale_review.context_artifacts_committed must be false")
    require_text(section.get("interpretation"), "target_scale_review.interpretation")
    reviewed_paths = require_list(
        section.get("reviewed_context_artifact_paths"),
        "target_scale_review.reviewed_context_artifact_paths",
    )
    missing_paths = require_list(
        section.get("missing_context_artifact_paths"),
        "target_scale_review.missing_context_artifact_paths",
    )
    if status == "blocked_missing_context_layers":
        require(
            section.get("context_downloads_or_crops_present_in_checkout") is False,
            "blocked target-scale context review must record no local context downloads or crops",
        )
        require(not reviewed_paths, "blocked target-scale context review must not list reviewed context artifacts")
        require(missing_paths, "blocked target-scale context review must list missing context artifacts")
    else:
        require(
            section.get("context_downloads_or_crops_present_in_checkout") is True,
            "reviewed target-scale context status requires local context downloads or crops",
        )
        require(reviewed_paths, "reviewed target-scale context status requires reviewed context artifacts")
    return {
        "status": status,
        "classification": classification,
        "missing_context_artifact_count": len(missing_paths),
    }


def validate_local_artifact_probe(probe: dict[str, Any], target_review: dict[str, Any]) -> None:
    require_text(probe.get("context_root"), "evidence.local_artifact_probe.context_root")
    require_text(probe.get("probe_date"), "evidence.local_artifact_probe.probe_date")
    require(isinstance(probe.get("context_root_present"), bool), "evidence.local_artifact_probe.context_root_present must be boolean")
    require(isinstance(probe.get("raw_context_products_present"), bool), "evidence.local_artifact_probe.raw_context_products_present must be boolean")
    if target_review["status"] == "blocked_missing_context_layers":
        require(
            probe.get("context_root_present") is False,
            "blocked target-scale context review requires local_artifact_probe.context_root_present false",
        )
        require(
            probe.get("raw_context_products_present") is False,
            "blocked target-scale context review requires local_artifact_probe.raw_context_products_present false",
        )


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
