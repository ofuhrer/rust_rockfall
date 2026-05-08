#!/usr/bin/env python3
"""Validate the Phase 2 source-zone and block-scenario policy contract."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


SUPPORTED_STATUSES = {"template_not_run", "draft_predeclared", "ready_for_conditional_pilot"}
SUPPORTED_EVIDENCE_LEVELS = {
    "level0_synthetic_fixture",
    "level1_manual_real_site_interpretation",
    "level2_geomorphic_or_inventory_supported",
}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "return_period",
    "physical_probability",
    "risk_map",
    "operational_hazard_map",
    "validated_hazard_map",
}


class PolicyError(ValueError):
    """User-facing policy validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    args = parser.parse_args(argv)
    try:
        policy = read_yaml(args.policy)
        validate_policy(policy)
    except PolicyError as exc:
        print(f"policy validation error: {exc}", file=sys.stderr)
        return 2
    print(f"source-zone/block-scenario policy is valid: {args.policy}")
    return 0


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context matters.
        raise PolicyError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PolicyError(f"policy must contain a YAML mapping: {path}")
    return data


def validate_policy(policy: dict[str, Any]) -> None:
    require(policy.get("schema_version") == "source_zone_block_scenario_policy_v1", "schema_version must be source_zone_block_scenario_policy_v1")
    status = require_text(policy.get("policy_status"), "policy_status")
    require(status in SUPPORTED_STATUSES, f"policy_status must be one of {sorted(SUPPORTED_STATUSES)}")
    require(policy.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")
    require_text(policy.get("policy_id"), "policy_id")
    require_text(policy.get("pilot_id"), "pilot_id")

    validate_source_zone_policy(require_mapping(policy.get("source_zone_policy"), "source_zone_policy"), status)
    validate_block_scenario_policy(require_mapping(policy.get("block_scenario_policy"), "block_scenario_policy"), status)
    validate_claim_boundary(require_mapping(policy.get("claim_boundary"), "claim_boundary"))


def validate_source_zone_policy(source_zone: dict[str, Any], status: str) -> None:
    evidence_level = require_text(source_zone.get("evidence_level"), "source_zone_policy.evidence_level")
    require(evidence_level in SUPPORTED_EVIDENCE_LEVELS, f"unsupported source-zone evidence_level {evidence_level!r}")
    require(source_zone.get("allowed_geometry_type") == "polygon", "current policy supports polygon source zones only")
    crs = require_mapping(source_zone.get("coordinate_reference_system"), "source_zone_policy.coordinate_reference_system")
    require(crs.get("epsg") == 2056, "source-zone policy must use EPSG:2056")
    require(crs.get("vertical_datum") == "LN02", "source-zone policy must use LN02")
    inputs = require_mapping(source_zone.get("derivation_inputs"), "source_zone_policy.derivation_inputs")
    required_inputs = set(require_list(inputs.get("required"), "source_zone_policy.derivation_inputs.required"))
    require("swisstopo_swissalti3d" in required_inputs, "source-zone derivation requires swissALTI3D terrain input")
    criteria = require_mapping(source_zone.get("derivation_criteria"), "source_zone_policy.derivation_criteria")
    criteria_status = require_text(criteria.get("status"), "source_zone_policy.derivation_criteria.status")
    if status != "template_not_run":
        require(criteria_status != "not_defined", "prepared policies must define source-zone derivation criteria")
        require_text(source_zone.get("source_zone_id"), "source_zone_policy.source_zone_id")
    sampling = require_mapping(source_zone.get("release_sampling"), "source_zone_policy.release_sampling")
    require(sampling.get("mode") == "deterministic_grid", "release_sampling.mode must be deterministic_grid")
    require(sampling.get("sampling_weight_semantics") == "conditional_sampling_only", "release sampling weights must remain conditional_sampling_only")
    require(sampling.get("physical_release_probability_supported") is False, "physical release probability must remain unsupported")
    require(sampling.get("annual_source_frequency_supported") is False, "annual source frequency must remain unsupported")


def validate_block_scenario_policy(block_policy: dict[str, Any], status: str) -> None:
    require(block_policy.get("active_shape_physics_supported") is False, "active shape physics must remain unsupported by this policy")
    require(block_policy.get("sampling_weight_semantics") == "conditional_sampling_only", "block sampling weights must remain conditional_sampling_only")
    scenarios = require_list(block_policy.get("scenarios"), "block_scenario_policy.scenarios")
    if status == "template_not_run" and not scenarios:
        return
    require(scenarios, "prepared policies must list at least one block scenario")
    ids: set[str] = set()
    total_weight = 0.0
    for index, raw in enumerate(scenarios):
        scenario = require_mapping(raw, f"block_scenario_policy.scenarios[{index}]")
        scenario_id = require_text(scenario.get("block_scenario_id"), f"block scenario {index} block_scenario_id")
        require(scenario_id not in ids, f"duplicate block_scenario_id {scenario_id!r}")
        ids.add(scenario_id)
        require_text(scenario.get("block_size_class"), f"block scenario {scenario_id}.block_size_class")
        require(scenario.get("block_shape_class") == "sphere", f"block scenario {scenario_id} must use block_shape_class sphere until active shape physics exists")
        weight = require_number(scenario.get("sampling_weight"), f"block scenario {scenario_id}.sampling_weight")
        require(math.isfinite(weight) and weight >= 0.0, f"block scenario {scenario_id} sampling_weight must be finite and nonnegative")
        total_weight += weight
        has_radius = scenario.get("block_radius_m") is not None
        has_mass = scenario.get("block_mass_kg") is not None
        require(has_radius or has_mass, f"block scenario {scenario_id} must record block_radius_m or block_mass_kg")
        for forbidden in ("physical_probability", "annual_frequency_per_year", "return_period_years"):
            require(scenario.get(forbidden) in (None, ""), f"block scenario {scenario_id} must not set {forbidden}")
    require(total_weight > 0.0, "block scenario sampling_weight total must be positive")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    allowed = set(require_list(boundary.get("current_allowed_products"), "claim_boundary.current_allowed_products"))
    require("conditional_intensity_exceedance" in allowed, "claim_boundary must allow conditional_intensity_exceedance")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "claim_boundary.unsupported_current_claims"))
    missing = REQUIRED_UNSUPPORTED_CLAIMS - unsupported
    require(not missing, f"claim_boundary unsupported_current_claims omits {sorted(missing)}")
    notes = "\n".join(str(note).lower() for note in require_list(boundary.get("notes"), "claim_boundary.notes"))
    require("not validation evidence" in notes, "claim_boundary notes must keep source-zone assumptions out of validation evidence")
    require("not physical" in notes, "claim_boundary notes must keep sampling weights out of physical probability")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyError(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PolicyError(f"{label} must be a list")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyError(f"{label} must be a non-empty string")
    return value


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise PolicyError(f"{label} must be numeric")
    return float(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


if __name__ == "__main__":
    raise SystemExit(main())
