#!/usr/bin/env python3
"""Check that calibration artifacts are not treated as validation evidence.

The helper is read-only. It inventories committed calibration selected-parameter
records and scans validation cases for prohibited references to calibration
artifacts. It does not tune parameters, promote defaults, or upgrade validation,
physical-probability, annual-frequency, operational, risk, or scale-up claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `.venv/bin/python ...` or `uv run python ...`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "calibration_separation_preflight_v1"
DEFAULT_CALIBRATION_ROOT = ROOT / "calibration"
DEFAULT_VALIDATION_CASE_ROOT = ROOT / "validation/cases"

PROHIBITED_REFERENCE_KEYS = {
    "calibration_artifact",
    "calibration_artifacts",
    "calibration_parameters",
    "selected_parameter_path",
    "selected_parameters",
    "selected_parameters_path",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-root", type=Path, default=DEFAULT_CALIBRATION_ROOT)
    parser.add_argument("--validation-case-root", type=Path, default=DEFAULT_VALIDATION_CASE_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(calibration_root=args.calibration_root, validation_case_root=args.validation_case_root)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["preflight_status"] == "passed" else 2


def build_report(
    *,
    calibration_root: Path = DEFAULT_CALIBRATION_ROOT,
    validation_case_root: Path = DEFAULT_VALIDATION_CASE_ROOT,
) -> dict[str, Any]:
    calibration_records = collect_calibration_records(calibration_root)
    validation_cases = collect_validation_cases(validation_case_root)
    prohibited_crossings = []
    for case in validation_cases:
        prohibited_crossings.extend(scan_case_for_prohibited_crossings(case))

    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_status": "passed" if not prohibited_crossings else "blocked_forbidden_validation_reference",
        "calibration_root": relative(calibration_root),
        "validation_case_root": relative(validation_case_root),
        "calibration_artifact_count": len(calibration_records),
        "validation_case_count": len(validation_cases),
        "calibration_artifacts": calibration_records,
        "validation_cases": [
            {
                "case_path": case["case_path"],
                "case_id": case["case_id"],
                "status": "checked",
            }
            for case in validation_cases
        ],
        "prohibited_crossings": prohibited_crossings,
        "separation_summary": {
            "calibration_records_are_diagnostic": True,
            "selected_parameters_promoted_to_validation": bool(prohibited_crossings),
            "validation_acceptance_contaminated": bool(prohibited_crossings),
            "current_calibration_claim_status": "diagnostic_non_default",
        },
        "claim_boundaries": {
            "calibration_performed_by_preflight": False,
            "selected_parameters_promoted": False,
            "validation_acceptance_claimed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "operational_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "balfrin_required": False,
        },
    }


def collect_calibration_records(calibration_root: Path) -> list[dict[str, Any]]:
    records = []
    experiments_root = calibration_root / "experiments"
    for path in sorted(experiments_root.glob("*/selected_parameters.yaml")):
        data = load_yaml(path)
        limitations = data.get("limitations") if isinstance(data.get("limitations"), list) else []
        records.append(
            {
                "path": relative(path),
                "experiment_id": str(data.get("experiment_id") or path.parent.name),
                "dataset_id": str(data.get("dataset_id") or ""),
                "model_version": str(data.get("model_version") or ""),
                "objective": data.get("objective") if data.get("objective") is not None else data.get("calibration_objective"),
                "status": "diagnostic_non_default",
                "promotion_status": "not_promoted_to_validation",
                "limitations": [str(item) for item in limitations],
            }
        )
    return records


def collect_validation_cases(validation_case_root: Path) -> list[dict[str, Any]]:
    cases = []
    for path in sorted(validation_case_root.glob("*.yaml")):
        data = load_yaml(path)
        cases.append(
            {
                "case_path": relative(path),
                "case_id": str(data.get("case_id") or path.stem),
                "document": data,
            }
        )
    return cases


def scan_case_for_prohibited_crossings(case: dict[str, Any]) -> list[dict[str, Any]]:
    crossings = []
    for location, key, value in walk_mapping(case["document"]):
        key_text = str(key)
        value_text = str(value)
        if key_text in PROHIBITED_REFERENCE_KEYS:
            crossings.append(
                {
                    "case_path": case["case_path"],
                    "case_id": case["case_id"],
                    "location": location,
                    "key": key_text,
                    "value": value_text,
                    "reason": "validation case declares a calibration or selected-parameter field",
                }
            )
        elif is_forbidden_calibration_reference(value_text):
            crossings.append(
                {
                    "case_path": case["case_path"],
                    "case_id": case["case_id"],
                    "location": location,
                    "key": key_text,
                    "value": value_text,
                    "reason": "validation case references a calibration selected-parameter artifact",
                }
            )
    return crossings


def walk_mapping(value: Any, location: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            rows.append((child_location, str(key), child))
            rows.extend(walk_mapping(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(walk_mapping(child, f"{location}[{index}]"))
    return rows


def is_forbidden_calibration_reference(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return "calibration/experiments/" in normalized and "selected_parameters" in normalized


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"preflight_status: {report['preflight_status']}",
        f"calibration_artifact_count: {report['calibration_artifact_count']}",
        f"validation_case_count: {report['validation_case_count']}",
        "calibration_artifacts:",
    ]
    for record in report["calibration_artifacts"]:
        lines.append(f"  - {record['experiment_id']}: {record['status']} ({record['path']})")
    lines.append("prohibited_crossings:")
    if report["prohibited_crossings"]:
        for crossing in report["prohibited_crossings"]:
            lines.append(f"  - {crossing['case_path']} {crossing['location']}: {crossing['reason']}")
    else:
        lines.append("  none")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
