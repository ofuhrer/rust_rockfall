#!/usr/bin/env python3
"""Validate public benchmark preparation manifests.

The validator is intentionally schema-light: it checks the fields needed for
reproducible no-tuning benchmark packages without requiring generated outputs
to exist in git.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "public_benchmark_preparation_manifest_v1"
STABLE_ID = re.compile(r"^[A-Za-z0-9_.:/-]+$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="+", type=Path)
    args = parser.parse_args(argv)

    errors: list[str] = []
    for path in args.manifest:
        errors.extend(f"{path}: {error}" for error in validate_manifest_file(path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def validate_manifest_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        return [f"could not parse JSON: {exc}"]
    return validate_manifest(data)


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require_equal(data, "schema_version", SCHEMA_VERSION, errors)
    require_stable_id(data, "benchmark_id", errors)
    require_stable_id(data, "dataset_id", errors)
    require_nonempty(data, "provenance", errors, fallback_key="public_source")
    require_present(data, "generated_cases", errors, fallback_key="case_files")
    require_nonempty(data, "command_provenance", errors)
    require_nonempty(data, "limitations", errors)

    selected_ids = normalized_selected_ids(data)
    if selected_ids is None:
        errors.append("selected_ids or selection.selected_trajectory_ids must be present")
    elif not isinstance(selected_ids, list):
        errors.append("selected IDs must be a list")
    elif any(not isinstance(item, str) or not item.strip() for item in selected_ids):
        errors.append("selected IDs must be nonempty strings")

    exclusions = data.get("excluded_ids_with_reasons")
    if exclusions is None:
        errors.append("excluded_ids_with_reasons must be present, even if empty")
    elif not isinstance(exclusions, list):
        errors.append("excluded_ids_with_reasons must be a list")
    else:
        for index, row in enumerate(exclusions):
            if not isinstance(row, dict):
                errors.append(f"excluded_ids_with_reasons[{index}] must be an object")
                continue
            if not str(row.get("id", "")).strip() or not str(row.get("reason", "")).strip():
                errors.append(f"excluded_ids_with_reasons[{index}] requires id and reason")

    if data.get("benchmark_id") == "tschamut":
        validate_tschamut_registration_sensitivity(data, errors)

    return errors


def validate_tschamut_registration_sensitivity(data: dict[str, Any], errors: list[str]) -> None:
    sensitivity = data.get("registration_sensitivity")
    if not isinstance(sensitivity, dict):
        errors.append("tschamut manifests require registration_sensitivity")
        return
    if sensitivity.get("required_before_physics_selection") is not True:
        errors.append("registration_sensitivity.required_before_physics_selection must be true")
    required_methods = {"scan_surface_fit_v1", "bbox_align_v1", "overview_offset_v1"}
    methods = sensitivity.get("methods_compared")
    if not isinstance(methods, list) or not required_methods.issubset(set(methods)):
        errors.append(
            "registration_sensitivity.methods_compared must include "
            "scan_surface_fit_v1, bbox_align_v1, and overview_offset_v1"
        )
    if sensitivity.get("classification_stability_required") is not True:
        errors.append("registration_sensitivity.classification_stability_required must be true")
    if "decision_gate" not in sensitivity:
        errors.append("registration_sensitivity.decision_gate must be present")


def normalized_selected_ids(data: dict[str, Any]) -> Any:
    if "selected_ids" in data:
        return data["selected_ids"]
    selection = data.get("selection")
    if isinstance(selection, dict):
        return selection.get("selected_trajectory_ids")
    return None


def require_equal(data: dict[str, Any], key: str, expected: str, errors: list[str]) -> None:
    if data.get(key) != expected:
        errors.append(f"{key} must be {expected!r}")


def require_stable_id(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a nonempty string")
    elif not STABLE_ID.fullmatch(value):
        errors.append(f"{key} must be a stable ASCII id")


def require_nonempty(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    fallback_key: str | None = None,
) -> None:
    value = data.get(key)
    if value:
        return
    if fallback_key and data.get(fallback_key):
        return
    errors.append(f"{key} must be present and nonempty")


def require_present(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    fallback_key: str | None = None,
) -> None:
    if key in data:
        return
    if fallback_key and fallback_key in data:
        return
    errors.append(f"{key} must be present")


if __name__ == "__main__":
    raise SystemExit(main())
