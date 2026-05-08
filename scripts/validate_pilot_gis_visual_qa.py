#!/usr/bin/env python3
"""Validate a pilot GIS/QGIS visual QA review record.

The record is a share-safe checklist for human or environment-constrained GIS
review. It does not open QGIS, certify QGZ/COG packaging, or approve
operational hazard-map use.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_VALIDATOR_PATH = ROOT / "scripts" / "validate_pilot_gis_package.py"
REQUIRED_CHECK_IDS = {
    "project_crs_epsg_2056",
    "vertical_datum_ln02",
    "raster_grid_alignment",
    "nodata_vs_valid_zero_styling",
    "source_zone_overlay",
    "layer_labels_conditional",
    "unsupported_claim_boundaries",
}
QA_STATUSES = {"pass", "no-go", "inconclusive", "blocked", "not-run"}
FINAL_STATUSES = {"pass", "no-go", "inconclusive", "blocked"}
MISLEADING_CLAIM_PATTERNS = [
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
]


class VisualQaValidationError(ValueError):
    """User-facing visual QA record validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument(
        "--require-existing-package",
        action="store_true",
        help="validate the referenced local pilot GIS package manifest and files",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="summary output format",
    )
    args = parser.parse_args(argv)
    try:
        summary = validate_visual_qa_record(
            args.record,
            require_existing_package=args.require_existing_package,
        )
    except VisualQaValidationError as exc:
        print(f"pilot GIS visual QA validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "pilot GIS visual QA record is valid: "
            f"{args.record} "
            f"(manual={summary['manual_qgis_visual_qa_status']}, "
            f"overall={summary['overall_acceptance']})"
        )
    return 0


def validate_visual_qa_record(
    record_path: Path,
    *,
    require_existing_package: bool = False,
) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "pilot_gis_visual_qa_record_v1",
        "schema_version must be pilot_gis_visual_qa_record_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")

    package_manifest_path = require_text(record.get("package_manifest_path"), "package_manifest_path")
    package_summary = None
    if require_existing_package:
        package_summary = validate_package_manifest(package_manifest_path)

    environment = require_mapping(record.get("review_environment"), "review_environment")
    qgis_available = require_bool(environment.get("qgis_available"), "review_environment.qgis_available")
    qgis_version = environment.get("qgis_version")
    if qgis_available:
        require_text(qgis_version, "review_environment.qgis_version")
    else:
        require(qgis_version in (None, ""), "review_environment.qgis_version must be empty when qgis_available is false")
    require_text(environment.get("reviewer"), "review_environment.reviewer")
    require_text(environment.get("review_date"), "review_environment.review_date")

    status = require_mapping(record.get("status"), "status")
    automated_status = require_status(status.get("automated_package_qa_status"), "status.automated_package_qa_status")
    manual_status = require_status(status.get("manual_qgis_visual_qa_status"), "status.manual_qgis_visual_qa_status")
    overall = require_final_status(status.get("overall_acceptance"), "status.overall_acceptance")
    require(status.get("accepted_for_operational_use") is False, "status.accepted_for_operational_use must be false")

    checks = validate_checks(require_list(record.get("checks"), "checks"))
    evidence = require_mapping(record.get("evidence"), "evidence")
    reviewed_artifacts = require_list(evidence.get("reviewed_artifacts"), "evidence.reviewed_artifacts")
    screenshots = require_list(evidence.get("screenshots"), "evidence.screenshots")
    blockers = require_list(record.get("blockers"), "blockers")

    if overall == "pass":
        require(automated_status == "pass", "overall pass requires automated_package_qa_status pass")
        require(manual_status == "pass", "overall pass requires manual_qgis_visual_qa_status pass")
        require(qgis_available, "overall pass requires qgis_available true")
        require(reviewed_artifacts, "overall pass requires reviewed_artifacts")
        require(screenshots, "overall pass requires screenshot or exported visual artifact references")
        failing = sorted(check_id for check_id, check in checks.items() if check["status"] != "pass")
        require(not failing, f"overall pass requires all required checks to pass: {failing}")
    elif overall == "blocked":
        require(blockers, "overall blocked requires at least one explicit blocker")
        require(
            manual_status == "blocked" or automated_status == "blocked",
            "overall blocked requires manual or automated QA to be blocked",
        )
    else:
        require(blockers, f"overall {overall} requires at least one explicit blocker or limitation")

    if manual_status == "pass":
        require(qgis_available, "manual QGIS pass requires qgis_available true")
        require(reviewed_artifacts, "manual QGIS pass requires reviewed_artifacts")
    elif manual_status == "not-run":
        raise VisualQaValidationError("manual_qgis_visual_qa_status must be pass, no-go, blocked, or inconclusive for a selected roadmap review")
    elif manual_status == "blocked":
        require(blockers, "manual QGIS blocked status requires explicit blockers")

    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))
    scan_text_for_misleading_claims(record)

    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "package_manifest_path": package_manifest_path,
        "automated_package_qa_status": automated_status,
        "manual_qgis_visual_qa_status": manual_status,
        "overall_acceptance": overall,
        "qgis_available": qgis_available,
        "required_check_count": len(checks),
        "blocker_count": len(blockers),
        "package_summary": package_summary,
    }


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is user-facing.
        raise VisualQaValidationError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise VisualQaValidationError(f"YAML document must be an object: {path}")
    return data


def validate_package_manifest(path_text: str) -> dict[str, Any]:
    validator = load_package_validator()
    try:
        return validator.validate_package(
            resolve_path(path_text),
            require_real_site=True,
            require_existing_files=True,
        )
    except Exception as exc:  # noqa: BLE001 - normalize dependency error type.
        raise VisualQaValidationError(f"referenced pilot GIS package is invalid: {exc}") from exc


def load_package_validator() -> Any:
    spec = importlib.util.spec_from_file_location("validate_pilot_gis_package", PACKAGE_VALIDATOR_PATH)
    require(spec is not None and spec.loader is not None, "failed to load pilot GIS package validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_checks(raw_checks: list[Any]) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_checks):
        check = require_mapping(raw, f"checks[{index}]")
        check_id = require_text(check.get("id"), f"checks[{index}].id")
        require(check_id not in checks, f"duplicate check id: {check_id}")
        status = require_status(check.get("status"), f"checks[{index}].status")
        require(status != "not-run", f"required selected-pilot check must be classified, not not-run: {check_id}")
        require_text(check.get("finding"), f"checks[{index}].finding")
        require_list(check.get("evidence"), f"checks[{index}].evidence")
        checks[check_id] = {"status": status, "finding": check["finding"], "evidence": check["evidence"]}
    missing = sorted(REQUIRED_CHECK_IDS - set(checks))
    require(not missing, f"missing required visual QA checks: {missing}")
    return checks


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    require(boundary.get("operational_status") == "research_diagnostic", "claim_boundary.operational_status must remain research_diagnostic")
    require(boundary.get("annualized") is False, "claim_boundary.annualized must be false")
    require(boundary.get("physical_probability") is False, "claim_boundary.physical_probability must be false")
    require(boundary.get("risk_or_exposure") is False, "claim_boundary.risk_or_exposure must be false")
    allowed = set(require_list(boundary.get("current_allowed_product_labels"), "claim_boundary.current_allowed_product_labels"))
    require("conditional_intensity_exceedance" in allowed, "current labels must include conditional_intensity_exceedance")


def scan_text_for_misleading_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"claim_boundary", "unsupported_claim_boundaries"}:
                continue
            scan_text_for_misleading_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("unsupported", "not ", "no ", "without ", "reject", "defer", "avoid")):
            return
        for pattern in MISLEADING_CLAIM_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VisualQaValidationError(message)


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string")
    return value


def require_bool(value: Any, field: str) -> bool:
    require(isinstance(value, bool), f"{field} must be a boolean")
    return value


def require_status(value: Any, field: str) -> str:
    status = require_text(value, field)
    require(status in QA_STATUSES, f"{field} must be one of {sorted(QA_STATUSES)}")
    return status


def require_final_status(value: Any, field: str) -> str:
    status = require_text(value, field)
    require(status in FINAL_STATUSES, f"{field} must be one of {sorted(FINAL_STATUSES)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
