#!/usr/bin/env python3
"""Generate a deterministic Balfrin block-scenario sensitivity plan.

This helper stays read-only. It turns the frozen Balfrin/Tschamut source-policy
record and the committed scenario table into a deterministic report that makes
block-size bins, conditional weighting semantics, and non-frequency labels
explicit. It does not fit block-size distributions, infer annual frequencies,
run ensembles, or authorize scale-up.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_block_scenario_sensitivity_plan_v1"
PLAN_TITLE = "Balfrin block-scenario sensitivity plan"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_SAME_SCALE_REFERENCE = ROOT / "docs/tschamut_public_same_scale_uncertainty_envelope.md"
EXPLICIT_NON_FREQUENCY_LABELS = [
    "conditional_sampling_only",
    "not_annual_frequency",
    "not_physical_probability",
    "not_return_period",
    "not_operational_hazard_map",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--scenario-table", type=Path, default=DEFAULT_SCENARIO_TABLE)
    parser.add_argument("--same-scale-reference", type=Path, default=DEFAULT_SAME_SCALE_REFERENCE)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        policy_path=args.policy,
        scenario_table_path=args.scenario_table,
        same_scale_reference_path=args.same_scale_reference,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["scenario_plan_status"] == "ready" else 2


def build_report(
    *,
    policy_path: Path = DEFAULT_POLICY,
    scenario_table_path: Path = DEFAULT_SCENARIO_TABLE,
    same_scale_reference_path: Path = DEFAULT_SAME_SCALE_REFERENCE,
) -> dict[str, Any]:
    missing_inputs = [
        display_path(path)
        for path in (policy_path, scenario_table_path)
        if not path.exists()
    ]
    if missing_inputs:
        return blocked_report(
            missing_inputs,
            policy_path=policy_path,
            scenario_table_path=scenario_table_path,
            same_scale_reference_path=same_scale_reference_path,
        )

    policy = load_yaml(policy_path)
    scenario_rows = load_csv_rows(scenario_table_path)

    block_size_bins = build_block_size_bins(policy)
    weighting_semantics = build_weighting_semantics(policy, block_size_bins)
    reference_rows = build_reference_rows(scenario_rows)
    source_policy_provenance = build_source_policy_provenance(policy, policy_path)

    report = {
        "schema_version": SCHEMA_VERSION,
        "plan_title": PLAN_TITLE,
        "scenario_plan_status": "ready",
        "blocked_reason": None,
        "missing_inputs": [],
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "source_policy_provenance": source_policy_provenance,
        "block_size_bins": block_size_bins,
        "weighting_semantics": weighting_semantics,
        "reference_scenario_table": {
            "path": display_path(scenario_table_path),
            "row_count": len(reference_rows),
            "row_ids": [text_value(row.get("scenario_id")) for row in reference_rows],
            "block_scenario_ids": [text_value(row.get("block_scenario_id")) for row in reference_rows],
            "role": "frozen_reference_record",
            "non_frequency_columns": [
                "release_probability",
                "scenario_probability",
                "annual_frequency_per_year",
                "time_horizon_years",
            ],
            "rows": reference_rows,
        },
        "scenario_plan_summary": {
            "block_size_bin_count": len(block_size_bins),
            "reference_row_count": len(reference_rows),
            "policy_sampling_weight_total": round(sum(float(bin_row["sampling_weight"]) for bin_row in block_size_bins), 6),
            "normalized_sampling_share_total": round(sum(float(bin_row["normalized_sampling_share"]) for bin_row in block_size_bins), 6),
        },
        "explicit_non_frequency_labels": list(EXPLICIT_NON_FREQUENCY_LABELS),
        "same_scale_reference": build_same_scale_reference(same_scale_reference_path),
        "claim_boundary": build_claim_boundary(policy),
        "pragmatic_coverage_boundary": {
            "coverage_type": "policy_declared_sensitivity_bins",
            "coverage_is_not_physical_frequency": True,
            "coverage_is_not_annual_frequency": True,
            "sampling_weights_are_not_occurrence_rates": True,
            "coverage_note": "block-size bins are coverage bins for conditional sampling, not a physical occurrence model",
        },
        "source_inputs": {
            "source_scenario_policy_path": display_path(policy_path),
            "scenario_table_path": display_path(scenario_table_path),
            "same_scale_reference_path": display_path(same_scale_reference_path),
        },
    }
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    policy_path: Path,
    scenario_table_path: Path,
    same_scale_reference_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_title": PLAN_TITLE,
        "scenario_plan_status": "blocked_missing_inputs",
        "blocked_reason": "required frozen inputs are missing",
        "missing_inputs": sorted(set(missing_inputs)),
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "source_policy_provenance": {
            "policy_path": display_path(policy_path),
            "policy_status": "missing",
        },
        "block_size_bins": [],
        "weighting_semantics": {
            "sampling_weight_semantics": "conditional_sampling_only",
            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
            "sampling_weights_are_not_physical_probabilities": True,
        },
        "reference_scenario_table": {
            "path": display_path(scenario_table_path),
            "row_count": 0,
            "row_ids": [],
            "block_scenario_ids": [],
            "role": "frozen_reference_record",
            "non_frequency_columns": [
                "release_probability",
                "scenario_probability",
                "annual_frequency_per_year",
                "time_horizon_years",
            ],
            "rows": [],
        },
        "scenario_plan_summary": {
            "block_size_bin_count": 0,
            "reference_row_count": 0,
            "policy_sampling_weight_total": 0.0,
            "normalized_sampling_share_total": 0.0,
        },
        "explicit_non_frequency_labels": list(EXPLICIT_NON_FREQUENCY_LABELS),
        "same_scale_reference": build_same_scale_reference(same_scale_reference_path),
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "return_period_supported": False,
            "operational_hazard_map_supported": False,
            "risk_or_exposure_supported": False,
            "current_allowed_products": [
                "conditional_sampling_only",
                "diagnostic_planning",
                "coverage_review_only",
            ],
            "unsupported_current_claims": [
                "annual_frequency",
                "physical_probability",
                "return_period",
                "risk",
                "exposure",
                "vulnerability",
                "operational_hazard_map",
            ],
            "notes": [
                "plan generation is blocked until the frozen policy and scenario table are available",
            ],
        },
        "pragmatic_coverage_boundary": {
            "coverage_type": "policy_declared_sensitivity_bins",
            "coverage_is_not_physical_frequency": True,
            "coverage_is_not_annual_frequency": True,
            "sampling_weights_are_not_occurrence_rates": True,
            "coverage_note": "coverage bins remain unavailable until required frozen inputs are present",
        },
        "source_inputs": {
            "source_scenario_policy_path": display_path(policy_path),
            "scenario_table_path": display_path(scenario_table_path),
            "same_scale_reference_path": display_path(same_scale_reference_path),
        },
    }


def build_block_size_bins(policy: dict[str, Any]) -> list[dict[str, Any]]:
    block_policy = policy.get("block_scenario_policy", {}) if isinstance(policy.get("block_scenario_policy"), dict) else {}
    scenarios = block_policy.get("scenarios", []) if isinstance(block_policy.get("scenarios"), list) else []
    total_weight = sum(float(scenario.get("sampling_weight") or 0.0) for scenario in scenarios if isinstance(scenario, dict))
    bins: list[dict[str, Any]] = []
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            continue
        sampling_weight = float(scenario.get("sampling_weight") or 0.0)
        bins.append(
            {
                "bin_index": index,
                "bin_label": build_bin_label(text_value(scenario.get("block_size_class")), text_value(scenario.get("block_scenario_id"))),
                "block_scenario_id": text_value(scenario.get("block_scenario_id")),
                "block_size_class": text_value(scenario.get("block_size_class")),
                "block_shape_class": text_value(scenario.get("block_shape_class")),
                "block_radius_m": scenario.get("block_radius_m"),
                "block_mass_kg": scenario.get("block_mass_kg"),
                "sampling_weight": sampling_weight,
                "normalized_sampling_share": round(sampling_weight / total_weight, 6) if total_weight else None,
                "plan_label": "pragmatic_sensitivity_bin",
                "non_frequency_labels": [
                    "conditional_sampling_only",
                    "not_annual_frequency",
                    "not_physical_probability",
                ],
                "derivation_basis": text_value(scenario.get("derivation_basis")),
            }
        )
    return bins


def build_weighting_semantics(policy: dict[str, Any], block_size_bins: list[dict[str, Any]]) -> dict[str, Any]:
    source_zone_policy = policy.get("source_zone_policy", {}) if isinstance(policy.get("source_zone_policy"), dict) else {}
    release_sampling = source_zone_policy.get("release_sampling", {}) if isinstance(source_zone_policy.get("release_sampling"), dict) else {}
    block_policy = policy.get("block_scenario_policy", {}) if isinstance(policy.get("block_scenario_policy"), dict) else {}
    total_weight = round(sum(float(bin_row["sampling_weight"]) for bin_row in block_size_bins), 6)
    return {
        "sampling_weight_semantics": text_value(release_sampling.get("sampling_weight_semantics")) or "conditional_sampling_only",
        "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
        "sampling_weight_total": total_weight,
        "normalized_share_total": round(sum(float(bin_row["normalized_sampling_share"]) for bin_row in block_size_bins), 6)
        if block_size_bins
        else 0.0,
        "sampling_weight_is_not_physical_probability": True,
        "sampling_weight_is_not_annual_frequency": True,
        "weighting_note": "weights are conditional coverage weights for the sensitivity plan, not observed occurrence frequencies",
    }


def build_reference_rows(scenario_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(scenario_rows, start=1):
        rows.append(
            {
                "row_index": index,
                "scenario_id": text_value(row.get("scenario_id")),
                "source_zone_id": text_value(row.get("source_zone_id")),
                "release_sampling_policy": text_value(row.get("release_sampling_policy")),
                "model_configuration_id": text_value(row.get("model_configuration_id")),
                "terrain_material_assumption_id": text_value(row.get("terrain_material_assumption_id")),
                "sampling_weight": text_value(row.get("sampling_weight")),
                "block_scenario_id": text_value(row.get("block_scenario_id")),
                "block_size_class": text_value(row.get("block_size_class")),
                "block_shape_class": text_value(row.get("block_shape_class")),
                "block_radius_m": text_value(row.get("block_radius_m")),
                "block_mass_kg": text_value(row.get("block_mass_kg")),
                "block_density_kgpm3": text_value(row.get("block_density_kgpm3")),
                "release_probability": text_value(row.get("release_probability")),
                "scenario_probability": text_value(row.get("scenario_probability")),
                "annual_frequency_per_year": text_value(row.get("annual_frequency_per_year")),
                "time_horizon_years": text_value(row.get("time_horizon_years")),
                "non_frequency_labels": [
                    "conditional_sampling_only",
                    "not_annual_frequency",
                    "not_physical_probability",
                ],
            }
        )
    return rows


def build_source_policy_provenance(policy: dict[str, Any], policy_path: Path) -> dict[str, Any]:
    source_zone_policy = policy.get("source_zone_policy", {}) if isinstance(policy.get("source_zone_policy"), dict) else {}
    block_policy = policy.get("block_scenario_policy", {}) if isinstance(policy.get("block_scenario_policy"), dict) else {}
    release_sampling = source_zone_policy.get("release_sampling", {}) if isinstance(source_zone_policy.get("release_sampling"), dict) else {}
    claim_boundary = policy.get("claim_boundary", {}) if isinstance(policy.get("claim_boundary"), dict) else {}
    return {
        "policy_path": display_path(policy_path),
        "schema_version": text_value(policy.get("schema_version")),
        "policy_id": text_value(policy.get("policy_id")),
        "pilot_id": text_value(policy.get("pilot_id")),
        "operational_status": text_value(policy.get("operational_status")),
        "validation_maturity_target": text_value(policy.get("validation_maturity_target")),
        "source_zone_id": text_value(source_zone_policy.get("source_zone_id")),
        "source_zone_geometry_type": text_value(source_zone_policy.get("geometry", {}).get("type"))
        if isinstance(source_zone_policy.get("geometry"), dict)
        else "",
        "release_sampling_mode": text_value(release_sampling.get("mode")),
        "release_sampling_seed": release_sampling.get("seed"),
        "block_population_status": text_value(block_policy.get("block_population_status")),
        "source_policy_claim_boundary": {
            "current_allowed_products": list(claim_boundary.get("current_allowed_products", [])),
            "unsupported_current_claims": list(claim_boundary.get("unsupported_current_claims", [])),
        },
    }


def build_same_scale_reference(reference_path: Path) -> dict[str, Any]:
    return {
        "document_path": display_path(reference_path),
        "document_status": "available" if reference_path.exists() else "missing",
        "interpretation_role": "non_operational_reference_only",
    }


def build_claim_boundary(policy: dict[str, Any]) -> dict[str, Any]:
    claim_boundary = policy.get("claim_boundary", {}) if isinstance(policy.get("claim_boundary"), dict) else {}
    return {
        "annual_frequency_supported": False,
        "physical_probability_supported": False,
        "return_period_supported": False,
        "operational_hazard_map_supported": False,
        "risk_or_exposure_supported": False,
        "current_allowed_products": list(claim_boundary.get("current_allowed_products", [])),
        "unsupported_current_claims": list(claim_boundary.get("unsupported_current_claims", [])),
        "notes": list(claim_boundary.get("notes", [])),
    }


def build_bin_label(block_size_class: str, block_scenario_id: str) -> str:
    for suffix in ("small", "medium", "large", "observed"):
        if block_size_class.endswith(f"_{suffix}") or block_scenario_id.endswith(f"_{suffix}"):
            return suffix
    return block_scenario_id or block_size_class or "bin"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Block-Scenario Sensitivity Plan",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Plan title: `{report['plan_title']}`",
        f"- Scenario plan status: `{report['scenario_plan_status']}`",
        f"- Read only: `{report['read_only']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
    ]
    if report.get("blocked_reason"):
        lines.append(f"- Blocked reason: {report['blocked_reason']}")
    if report.get("missing_inputs"):
        lines.extend(["", "Missing Inputs"])
        for item in report["missing_inputs"]:
            lines.append(f"- `{item}`")
    lines.extend(["", "Source Policy Provenance"])
    provenance = report.get("source_policy_provenance", {})
    for key in (
        "policy_path",
        "schema_version",
        "policy_id",
        "pilot_id",
        "operational_status",
        "validation_maturity_target",
        "source_zone_id",
        "source_zone_geometry_type",
        "release_sampling_mode",
        "release_sampling_seed",
        "block_population_status",
    ):
        lines.append(f"- {key}: `{provenance.get(key, '')}`")
    lines.extend(["", "Weighting Semantics"])
    for key, value in report.get("weighting_semantics", {}).items():
        if isinstance(value, list):
            lines.append(f"- {key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {key}: `{value}`")
    lines.extend(["", "Block-Size Bins"])
    for bin_row in report.get("block_size_bins", []):
        lines.append(
            "- {bin_label}: `{block_scenario_id}` mass `{block_mass_kg}` kg, radius `{block_radius_m}` m, weight `{sampling_weight}`".format(
                bin_label=bin_row.get("bin_label", ""),
                block_scenario_id=bin_row.get("block_scenario_id", ""),
                block_mass_kg=bin_row.get("block_mass_kg", ""),
                block_radius_m=bin_row.get("block_radius_m", ""),
                sampling_weight=bin_row.get("sampling_weight", ""),
            )
        )
        lines.append(f"  - normalized_share: `{bin_row.get('normalized_sampling_share')}`")
        lines.append(f"  - plan_label: `{bin_row.get('plan_label', '')}`")
        lines.append("  - non_frequency_labels:")
        for label in bin_row.get("non_frequency_labels", []):
            lines.append(f"    - {label}")
    lines.extend(["", "Reference Scenario Table"])
    reference = report.get("reference_scenario_table", {})
    lines.append(f"- path: `{reference.get('path', '')}`")
    lines.append(f"- row_count: `{reference.get('row_count', 0)}`")
    lines.append(f"- role: `{reference.get('role', '')}`")
    lines.append("- non_frequency_columns:")
    for column in reference.get("non_frequency_columns", []):
        lines.append(f"  - {column}")
    lines.append("- rows:")
    for row in reference.get("rows", []):
        lines.append(
            f"  - `{row.get('scenario_id', '')}` -> block `{row.get('block_scenario_id', '')}`, sampling_weight `{row.get('sampling_weight', '')}`"
        )
    lines.extend(["", "Non-Frequency Boundary"])
    for label in report.get("explicit_non_frequency_labels", []):
        lines.append(f"- {label}")
    lines.extend(["", "Pragmatic Coverage Boundary"])
    boundary = report.get("pragmatic_coverage_boundary", {})
    lines.append(f"- coverage_type: `{boundary.get('coverage_type', '')}`")
    lines.append(f"- coverage_is_not_physical_frequency: `{boundary.get('coverage_is_not_physical_frequency', False)}`")
    lines.append(f"- coverage_is_not_annual_frequency: `{boundary.get('coverage_is_not_annual_frequency', False)}`")
    lines.append(f"- sampling_weights_are_not_occurrence_rates: `{boundary.get('sampling_weights_are_not_occurrence_rates', False)}`")
    lines.extend(["", "Same-Scale Reference"])
    same_scale = report.get("same_scale_reference", {})
    lines.append(f"- document_path: `{same_scale.get('document_path', '')}`")
    lines.append(f"- document_status: `{same_scale.get('document_status', '')}`")
    lines.append(f"- interpretation_role: `{same_scale.get('interpretation_role', '')}`")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
