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
    physics_selection_allowed = sensitivity.get("physics_selection_allowed")
    if not isinstance(physics_selection_allowed, bool):
        errors.append("registration_sensitivity.physics_selection_allowed must be a boolean")
    if physics_selection_allowed is True:
        validate_tschamut_physics_selection_table(sensitivity, required_methods, errors)


def validate_tschamut_physics_selection_table(
    sensitivity: dict[str, Any],
    required_methods: set[str],
    errors: list[str],
) -> None:
    if sensitivity.get("classification_stability_reported") is not True:
        errors.append(
            "registration_sensitivity.classification_stability_reported must be true "
            "when physics_selection_allowed is true"
        )
    table = sensitivity.get("classification_sensitivity")
    if not isinstance(table, list) or not table:
        errors.append(
            "registration_sensitivity.classification_sensitivity must be a nonempty list "
            "when physics_selection_allowed is true"
        )
        return

    grouped: dict[tuple[str, str], dict[str, set[str]]] = {}
    required_contact_models = {"translational_v0", "sphere_rotational_v1"}
    required_row_keys = {
        "transform_method",
        "run_subset",
        "contact_model",
        "classification",
        "summary_metric_provenance",
    }
    for index, row in enumerate(table):
        if not isinstance(row, dict):
            errors.append(
                f"registration_sensitivity.classification_sensitivity[{index}] must be an object"
            )
            continue
        for key in required_row_keys:
            if not str(row.get(key, "")).strip():
                errors.append(
                    f"registration_sensitivity.classification_sensitivity[{index}].{key} "
                    "must be present and nonempty"
                )
        grouped_metrics = row.get("grouped_metrics")
        if not isinstance(grouped_metrics, dict) or not grouped_metrics:
            errors.append(
                f"registration_sensitivity.classification_sensitivity[{index}].grouped_metrics "
                "must be a nonempty object"
            )
        method = row.get("transform_method")
        if method not in required_methods:
            errors.append(
                f"registration_sensitivity.classification_sensitivity[{index}].transform_method "
                "must be one of scan_surface_fit_v1, bbox_align_v1, overview_offset_v1"
            )
            continue
        run_subset = str(row.get("run_subset", "")).strip()
        contact_model = str(row.get("contact_model", "")).strip()
        classification = str(row.get("classification", "")).strip()
        if run_subset and contact_model and classification:
            group = grouped.setdefault((run_subset, contact_model), {})
            group.setdefault(method, set()).add(classification)

    run_subsets = {run_subset for run_subset, _ in grouped}
    for run_subset in run_subsets:
        missing_contact_models = required_contact_models.difference(
            contact_model for subset, contact_model in grouped if subset == run_subset
        )
        if missing_contact_models:
            errors.append(
                "registration_sensitivity.classification_sensitivity missing contact models "
                f"{sorted(missing_contact_models)} for run_subset={run_subset!r}"
            )

    for (run_subset, contact_model), by_method in grouped.items():
        for method, classifications_for_method in by_method.items():
            if len(classifications_for_method) > 1:
                errors.append(
                    "registration_sensitivity.classification_sensitivity has conflicting "
                    f"classifications for method={method!r}, run_subset={run_subset!r}, "
                    f"contact_model={contact_model!r}"
                )
        missing = required_methods.difference(by_method)
        if missing:
            errors.append(
                "registration_sensitivity.classification_sensitivity missing methods "
                f"{sorted(missing)} for run_subset={run_subset!r}, contact_model={contact_model!r}"
            )
            continue
        classifications = {next(iter(values)) for values in by_method.values() if values}
        if len(classifications) > 1:
            errors.append(
                "registration_sensitivity.classification_sensitivity classifications are not stable "
                f"for run_subset={run_subset!r}, contact_model={contact_model!r}"
            )


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
