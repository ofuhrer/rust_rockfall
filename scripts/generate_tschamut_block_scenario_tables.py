#!/usr/bin/env python3
"""Generate deterministic candidate-source-zone block-scenario tables.

This helper stays inside the non-frequency boundary. It can reconstruct the
checked-in Tschamut scenario table from committed policy plus release metadata
and can also emit deterministic block-scenario family tables for a generic
candidate source zone plus a policy template.

The default template reproduces the current single-row summary table by
aggregating the committed release-point metadata. A policy-family template is
also available for deterministic block-scenario expansion from a candidate
source-zone record without introducing annual frequency, physical probability,
or fitted population models.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "candidate_source_zone_block_scenario_generation_v1"
MANIFEST_SCHEMA_VERSION = "candidate_source_zone_block_scenario_generation_manifest_v1"
DEFAULT_POLICY_TEMPLATE = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_CANDIDATE_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_RELEASE_POINTS = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"

DEFAULT_MODEL_CONFIGURATION_ID = "translational_v0_stochastic_contact_v1"
DEFAULT_TERRAIN_MATERIAL_ASSUMPTION_ID = "uniform_global_parameters"
SUMMARY_BLOCK_SIZE_CLASS = "tschamut_selected_rows_observed"
SUMMARY_BLOCK_SHAPE_CLASS = "sphere"
SUMMARY_SCENARIO_SUFFIX = "observed_rows"
SUMMARY_BLOCK_SCENARIO_SUFFIX = "observed_rows"

SCENARIO_TABLE_COLUMNS = [
    "scenario_id",
    "source_zone_id",
    "release_sampling_policy",
    "model_configuration_id",
    "terrain_material_assumption_id",
    "sampling_weight",
    "block_scenario_id",
    "block_size_class",
    "block_shape_class",
    "block_radius_m",
    "block_mass_kg",
    "block_density_kgpm3",
    "release_probability",
    "scenario_probability",
    "annual_frequency_per_year",
    "time_horizon_years",
]

AVAILABLE_TEMPLATES = {
    "observed_rows_summary_v1": "single-row summary from deterministic release metadata aggregation",
    "policy_block_family_v1": "one row per policy block scenario with conditional weights preserved",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", "--policy-template", dest="policy_template", type=Path, default=DEFAULT_POLICY_TEMPLATE)
    parser.add_argument(
        "--source-zone-metadata",
        "--candidate-source-zone-metadata",
        dest="candidate_source_zone_metadata",
        type=Path,
        default=DEFAULT_CANDIDATE_SOURCE_ZONE_METADATA,
    )
    parser.add_argument("--release-points", type=Path, default=DEFAULT_RELEASE_POINTS)
    parser.add_argument("--reference-scenario-table", type=Path, default=DEFAULT_SCENARIO_TABLE)
    parser.add_argument("--template", choices=tuple(AVAILABLE_TEMPLATES.keys()), default="observed_rows_summary_v1")
    parser.add_argument("--csv-output", type=Path, default=None)
    parser.add_argument("--manifest-json", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    report = build_report(
        policy_template_path=args.policy_template,
        candidate_source_zone_metadata_path=args.candidate_source_zone_metadata,
        release_points_path=args.release_points,
        reference_scenario_table_path=args.reference_scenario_table,
        template_id=args.template,
    )

    if report["scenario_table_status"] == "ready":
        if args.csv_output is not None:
            args.csv_output.parent.mkdir(parents=True, exist_ok=True)
            write_csv(args.csv_output, report["generated_scenario_table_rows"])
        if args.manifest_json is not None:
            args.manifest_json.parent.mkdir(parents=True, exist_ok=True)
            args.manifest_json.write_text(
                json.dumps(report["scenario_table_manifest"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["scenario_table_status"] == "ready" else 2


def build_report(
    *,
    policy_path: Path = DEFAULT_POLICY_TEMPLATE,
    source_zone_metadata_path: Path = DEFAULT_CANDIDATE_SOURCE_ZONE_METADATA,
    release_points_path: Path = DEFAULT_RELEASE_POINTS,
    reference_scenario_table_path: Path = DEFAULT_SCENARIO_TABLE,
    template_id: str = "observed_rows_summary_v1",
) -> dict[str, Any]:
    return build_candidate_source_zone_report(
        policy_template_path=policy_path,
        candidate_source_zone_metadata_path=source_zone_metadata_path,
        release_points_path=release_points_path,
        reference_scenario_table_path=reference_scenario_table_path,
        template_id=template_id,
    )


def build_candidate_source_zone_report(
    *,
    policy_template_path: Path = DEFAULT_POLICY_TEMPLATE,
    candidate_source_zone_metadata_path: Path = DEFAULT_CANDIDATE_SOURCE_ZONE_METADATA,
    release_points_path: Path = DEFAULT_RELEASE_POINTS,
    reference_scenario_table_path: Path = DEFAULT_SCENARIO_TABLE,
    template_id: str = "observed_rows_summary_v1",
) -> dict[str, Any]:
    missing_inputs = [
        display_path(path)
        for path in (
            policy_template_path,
            candidate_source_zone_metadata_path,
            *(
                (release_points_path,)
                if template_id == "observed_rows_summary_v1"
                else ()
            ),
        )
        if not path.exists()
    ]
    if missing_inputs:
        return blocked_report(
            missing_inputs,
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
        )

    policy = load_yaml(policy_template_path)
    candidate_source_zone_metadata = load_yaml(candidate_source_zone_metadata_path)
    release_rows = load_csv_rows(release_points_path) if template_id == "observed_rows_summary_v1" and release_points_path.exists() else []

    source_zone_id, policy_source_zone_id, candidate_source_zone_id = resolve_source_zone_ids(
        policy,
        candidate_source_zone_metadata,
    )
    if not source_zone_id:
        return blocked_report(
            ["candidate source-zone metadata must define source_zone_id"],
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
            blocked_reason="missing source zone id",
        )
    if policy_source_zone_id and candidate_source_zone_id and policy_source_zone_id != candidate_source_zone_id:
        return blocked_report(
            [f"source zone mismatch between metadata ({candidate_source_zone_id!r}) and policy ({policy_source_zone_id!r})"],
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
            blocked_reason="source zone metadata and policy disagree",
        )

    release_sampling = get_nested_mapping(policy, ("source_zone_policy", "release_sampling"))
    if text_value(release_sampling.get("sampling_weight_semantics")) not in ("", "conditional_sampling_only"):
        return blocked_report(
            ["policy release sampling semantics must remain conditional_sampling_only"],
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
            blocked_reason="release sampling semantics changed",
        )

    if text_value(get_nested_value(policy, ("block_scenario_policy", "sampling_weight_semantics"))) not in ("", "conditional_sampling_only"):
        return blocked_report(
            ["policy block sampling semantics must remain conditional_sampling_only"],
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
            blocked_reason="block sampling semantics changed",
        )

    expected_release_count = candidate_source_zone_metadata.get("release_sampling_policy", {}).get("release_count")
    if template_id == "observed_rows_summary_v1" and isinstance(expected_release_count, int) and expected_release_count != len(release_rows):
        return blocked_report(
            [
                f"release row count mismatch: metadata expects {expected_release_count}, release_points.csv has {len(release_rows)} rows"
            ],
            policy_template_path=policy_template_path,
            candidate_source_zone_metadata_path=candidate_source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            template_id=template_id,
            blocked_reason="release metadata count mismatch",
        )

    release_stats = summarize_release_rows(release_rows) if template_id == "observed_rows_summary_v1" else {}
    rows = build_rows(
        template_id=template_id,
        policy=policy,
        source_zone_metadata=candidate_source_zone_metadata,
        release_stats=release_stats,
        source_zone_id=source_zone_id,
    )
    scenario_manifest = build_manifest(
        template_id=template_id,
        policy=policy,
        policy_path=policy_template_path,
        source_zone_metadata=candidate_source_zone_metadata,
        source_zone_metadata_path=candidate_source_zone_metadata_path,
        release_points_path=release_points_path,
        release_stats=release_stats,
        rows=rows,
        reference_scenario_table_path=reference_scenario_table_path,
        source_zone_id=source_zone_id,
    )

    scenario_table_status = "ready"
    blocked_reason = None
    if template_id == "observed_rows_summary_v1" and reference_scenario_table_path.exists():
        reference_rows = load_csv_rows(reference_scenario_table_path)
        if normalize_rows_for_compare(reference_rows) != [row_for_csv(row) for row in rows]:
            scenario_table_status = "blocked_reference_mismatch"
            blocked_reason = "generated summary row does not match the committed scenario table"

    report = {
        "schema_version": SCHEMA_VERSION,
        "scenario_table_status": scenario_table_status,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "scenario_family_template_id": template_id,
        "scenario_family_template_description": AVAILABLE_TEMPLATES[template_id],
        "generated_scenario_table_rows": rows,
        "scenario_table_manifest": scenario_manifest,
        "scenario_table_summary": {
            "row_count": len(rows),
            "row_ids": [text_value(row.get("scenario_id")) for row in rows],
            "block_scenario_ids": [text_value(row.get("block_scenario_id")) for row in rows],
            "policy_sampling_weight_total": round(sum(float(row.get("sampling_weight") or 0.0) for row in rows), 6),
            "normalized_sampling_share_total": round(
                sum(float(item.get("normalized_sampling_share") or 0.0) for item in scenario_manifest["rows"]),
                6,
            ),
        },
        "source_inputs": {
            "policy_template_path": display_path(policy_template_path),
            "candidate_source_zone_metadata_path": display_path(candidate_source_zone_metadata_path),
            "release_points_path": display_path(release_points_path),
            "reference_scenario_table_path": display_path(reference_scenario_table_path),
        },
    }
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    policy_template_path: Path,
    candidate_source_zone_metadata_path: Path,
    release_points_path: Path,
    reference_scenario_table_path: Path,
    template_id: str,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scenario_table_status": "blocked_missing_inputs",
        "blocked_reason": blocked_reason or "required committed inputs are missing",
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "scenario_family_template_id": template_id,
        "scenario_family_template_description": AVAILABLE_TEMPLATES.get(template_id, ""),
        "generated_scenario_table_rows": [],
        "scenario_table_manifest": {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "template_id": template_id,
            "template_description": AVAILABLE_TEMPLATES.get(template_id, ""),
            "table_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason or "required committed inputs are missing",
            "missing_inputs": sorted(set(missing_inputs)),
            "row_count": 0,
            "row_ids": [],
            "block_scenario_ids": [],
            "read_only": True,
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "source_inputs": {
                "policy_template_path": display_path(policy_template_path),
                "candidate_source_zone_metadata_path": display_path(candidate_source_zone_metadata_path),
                "release_points_path": display_path(release_points_path),
                "reference_scenario_table_path": display_path(reference_scenario_table_path),
            },
            "supported_templates": template_summary(),
        },
        "scenario_table_summary": {
            "row_count": 0,
            "row_ids": [],
            "block_scenario_ids": [],
            "policy_sampling_weight_total": 0.0,
            "normalized_sampling_share_total": 0.0,
        },
        "source_inputs": {
            "policy_template_path": display_path(policy_template_path),
            "candidate_source_zone_metadata_path": display_path(candidate_source_zone_metadata_path),
            "release_points_path": display_path(release_points_path),
            "reference_scenario_table_path": display_path(reference_scenario_table_path),
        },
    }


def build_rows(
    *,
    template_id: str,
    policy: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    release_stats: dict[str, Any],
    source_zone_id: str,
) -> list[dict[str, Any]]:
    release_sampling = get_nested_mapping(policy, ("source_zone_policy", "release_sampling"))
    block_policy = get_nested_mapping(policy, ("block_scenario_policy",))
    policy_prefix = policy_root_prefix(policy)

    if template_id == "observed_rows_summary_v1":
        return [
            {
                "scenario_id": f"{policy_prefix}_block_{SUMMARY_SCENARIO_SUFFIX}",
                "source_zone_id": source_zone_id,
                "release_sampling_policy": text_value(release_sampling.get("mode")) or "deterministic_grid",
                "model_configuration_id": DEFAULT_MODEL_CONFIGURATION_ID,
                "terrain_material_assumption_id": DEFAULT_TERRAIN_MATERIAL_ASSUMPTION_ID,
                "sampling_weight": 1.0,
                "block_scenario_id": f"{policy_prefix}_{SUMMARY_BLOCK_SCENARIO_SUFFIX}",
                "block_size_class": SUMMARY_BLOCK_SIZE_CLASS,
                "block_shape_class": SUMMARY_BLOCK_SHAPE_CLASS,
                "block_radius_m": release_stats.get("mean_block_radius_m", ""),
                "block_mass_kg": release_stats.get("mean_block_mass_kg", ""),
                "block_density_kgpm3": "",
                "release_probability": "",
                "scenario_probability": "",
                "annual_frequency_per_year": "",
                "time_horizon_years": "",
                "normalized_sampling_share": 1.0,
            }
        ]

    if template_id == "policy_block_family_v1":
        scenarios = get_nested_list(block_policy, ("scenarios",))
        total_weight = sum(float(scenario.get("sampling_weight") or 0.0) for scenario in scenarios if isinstance(scenario, dict))
        rows: list[dict[str, Any]] = []
        for index, scenario in enumerate(scenarios, start=1):
            if not isinstance(scenario, dict):
                continue
            block_scenario_id = text_value(scenario.get("block_scenario_id"))
            scenario_id = f"{source_zone_id}__{block_scenario_id}"
            sampling_weight = float(scenario.get("sampling_weight") or 0.0)
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "source_zone_id": source_zone_id,
                    "release_sampling_policy": text_value(release_sampling.get("mode")) or "deterministic_grid",
                    "model_configuration_id": DEFAULT_MODEL_CONFIGURATION_ID,
                    "terrain_material_assumption_id": DEFAULT_TERRAIN_MATERIAL_ASSUMPTION_ID,
                    "sampling_weight": sampling_weight,
                    "block_scenario_id": block_scenario_id,
                    "block_size_class": text_value(scenario.get("block_size_class")),
                    "block_shape_class": text_value(scenario.get("block_shape_class")),
                    "block_radius_m": scenario.get("block_radius_m"),
                    "block_mass_kg": scenario.get("block_mass_kg"),
                    "block_density_kgpm3": scenario.get("block_density_kgpm3") or "",
                    "release_probability": "",
                    "scenario_probability": "",
                    "annual_frequency_per_year": "",
                    "time_horizon_years": "",
                }
            )
        if total_weight > 0:
            for row in rows:
                row["normalized_sampling_share"] = round(float(row["sampling_weight"]) / total_weight, 6)
        return rows

    raise SystemExit(f"unsupported template_id: {template_id}")


def build_manifest(
    *,
    template_id: str,
    policy: dict[str, Any],
    policy_path: Path,
    source_zone_metadata: dict[str, Any],
    source_zone_metadata_path: Path,
    release_points_path: Path,
    release_stats: dict[str, Any],
    rows: list[dict[str, Any]],
    reference_scenario_table_path: Path,
    source_zone_id: str,
) -> dict[str, Any]:
    source_zone_policy = get_nested_mapping(policy, ("source_zone_policy",))
    release_sampling = get_nested_mapping(source_zone_policy, ("release_sampling",))
    block_policy = get_nested_mapping(policy, ("block_scenario_policy",))
    claim_boundary = get_nested_mapping(policy, ("claim_boundary",))
    normalized_share_total = round(
        sum(float(row.get("normalized_sampling_share") or 0.0) for row in rows),
        6,
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "table_status": "ready",
        "template_id": template_id,
        "template_description": AVAILABLE_TEMPLATES[template_id],
        "supported_templates": template_summary(),
        "scenario_family_id": build_scenario_family_id(template_id, policy, source_zone_id),
        "row_count": len(rows),
        "row_ids": [text_value(row.get("scenario_id")) for row in rows],
        "block_scenario_ids": [text_value(row.get("block_scenario_id")) for row in rows],
        "row_id_strategy": row_id_strategy(template_id, policy),
        "source_zone_provenance": build_source_zone_provenance(
            candidate_source_zone_metadata=source_zone_metadata,
            candidate_source_zone_metadata_path=source_zone_metadata_path,
            policy=policy,
            source_zone_id=source_zone_id,
        ),
        "release_metadata_provenance": {
            "release_sampling_mode": text_value(release_sampling.get("mode")),
            "release_sampling_seed": release_sampling.get("seed"),
            "release_sampling_policy": text_value(release_sampling.get("sampling_weight_semantics")) or "conditional_sampling_only",
            "release_point_count": release_stats.get("release_point_count", 0),
            "release_point_ids": list(release_stats.get("release_point_ids", [])),
            "release_mass_kg_mean": release_stats.get("mean_block_mass_kg", ""),
            "release_radius_m_mean": release_stats.get("mean_block_radius_m", ""),
            "release_mass_kg_total": release_stats.get("sum_block_mass_kg", ""),
            "release_radius_m_total": release_stats.get("sum_block_radius_m", ""),
            "release_point_source_path": display_path(release_points_path),
        },
        "policy_provenance": {
            "policy_path": display_path(policy_path),
            "schema_version": text_value(policy.get("schema_version")),
            "policy_id": text_value(policy.get("policy_id")),
            "pilot_id": text_value(policy.get("pilot_id")),
            "operational_status": text_value(policy.get("operational_status")),
            "validation_maturity_target": text_value(policy.get("validation_maturity_target")),
            "source_zone_id": text_value(source_zone_policy.get("source_zone_id")),
            "source_zone_geometry_type": text_value(get_nested_value(source_zone_policy, ("geometry", "type"))),
            "block_population_status": text_value(block_policy.get("block_population_status")),
            "conditional_only_weighting": True,
            "source_policy_claim_boundary": {
                "current_allowed_products": list(claim_boundary.get("current_allowed_products", [])),
                "unsupported_current_claims": list(claim_boundary.get("unsupported_current_claims", [])),
            },
        },
        "block_scenario_policy_summary": [
            {
                "block_scenario_id": text_value(scenario.get("block_scenario_id")),
                "block_size_class": text_value(scenario.get("block_size_class")),
                "block_shape_class": text_value(scenario.get("block_shape_class")),
                "block_radius_m": scenario.get("block_radius_m"),
                "block_mass_kg": scenario.get("block_mass_kg"),
                "sampling_weight": scenario.get("sampling_weight"),
                "derivation_basis": text_value(scenario.get("derivation_basis")),
            }
            for scenario in get_nested_list(block_policy, ("scenarios",))
            if isinstance(scenario, dict)
        ],
        "conditional_weighting_semantics": {
            "sampling_weight_semantics": text_value(release_sampling.get("sampling_weight_semantics")) or "conditional_sampling_only",
            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
            "sampling_weights_are_not_physical_probability": True,
            "sampling_weights_are_not_annual_frequency": True,
            "conditional_only_weighting": True,
        },
        "row_provenance": [
            {
                "scenario_id": text_value(row.get("scenario_id")),
                "row_kind": template_row_kind(template_id),
                "block_scenario_id": text_value(row.get("block_scenario_id")),
                "sampling_weight": row.get("sampling_weight"),
                "normalized_sampling_share": row.get("normalized_sampling_share"),
                "row_id": text_value(row.get("scenario_id")),
                "scenario_family_id": build_scenario_family_id(template_id, policy, source_zone_id),
                "source_zone_id": source_zone_id,
                "non_frequency_columns": [
                    "release_probability",
                    "scenario_probability",
                    "annual_frequency_per_year",
                    "time_horizon_years",
                ],
            }
            for row in rows
        ],
        "source_inputs": {
            "policy_template_path": display_path(policy_path),
            "candidate_source_zone_metadata_path": display_path(source_zone_metadata_path),
            "release_points_path": display_path(release_points_path),
            "reference_scenario_table_path": display_path(reference_scenario_table_path),
        },
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "return_period_supported": False,
            "operational_hazard_map_supported": False,
            "risk_or_exposure_supported": False,
            "current_allowed_products": list(claim_boundary.get("current_allowed_products", [])),
            "unsupported_current_claims": list(claim_boundary.get("unsupported_current_claims", [])),
            "notes": list(claim_boundary.get("notes", [])),
        },
        "pragmatic_coverage_boundary": {
            "coverage_type": "policy_declared_sensitivity_bins",
            "coverage_is_not_physical_frequency": True,
            "coverage_is_not_annual_frequency": True,
            "sampling_weights_are_not_occurrence_rates": True,
            "coverage_note": "scenario rows are deterministic conditional templates, not a frequency model",
        },
        "normalized_sampling_share_total": normalized_share_total,
        "rows": [
            {
                **row,
                "row_id": text_value(row.get("scenario_id")),
                "row_kind": template_row_kind(template_id),
                "scenario_family_id": build_scenario_family_id(template_id, policy, source_zone_id),
                "non_frequency_columns": [
                    "release_probability",
                    "scenario_probability",
                    "annual_frequency_per_year",
                    "time_horizon_years",
                ],
            }
            for row in rows
        ],
        "reference_scenario_table": {
            "path": display_path(reference_scenario_table_path),
            "available": reference_scenario_table_path.exists(),
        },
        "conditional_only_weighting": True,
    }


def summarize_release_rows(release_rows: list[dict[str, str]]) -> dict[str, Any]:
    release_point_ids = [text_value(row.get("trajectory_id")) for row in release_rows if text_value(row.get("trajectory_id"))]
    mass_values = [parse_float(row.get("mass_kg")) for row in release_rows if parse_float(row.get("mass_kg")) is not None]
    radius_values = [parse_float(row.get("radius_m")) for row in release_rows if parse_float(row.get("radius_m")) is not None]
    if not mass_values or not radius_values:
        raise SystemExit("release metadata must contain non-empty mass_kg and radius_m columns")
    return {
        "release_point_count": len(release_rows),
        "release_point_ids": release_point_ids,
        "sum_block_mass_kg": round(sum(mass_values), 6),
        "sum_block_radius_m": round(sum(radius_values), 6),
        "mean_block_mass_kg": round(sum(mass_values) / len(mass_values), 6),
        "mean_block_radius_m": round(sum(radius_values) / len(radius_values), 6),
    }


def resolve_source_zone_ids(
    policy: dict[str, Any],
    candidate_source_zone_metadata: dict[str, Any],
) -> tuple[str, str, str]:
    policy_source_zone_id = text_value(get_nested_value(policy, ("source_zone_policy", "source_zone_id")))
    candidate_source_zone_id = text_value(candidate_source_zone_metadata.get("source_zone_id"))
    resolved_source_zone_id = policy_source_zone_id or candidate_source_zone_id
    return resolved_source_zone_id, policy_source_zone_id, candidate_source_zone_id


def build_scenario_family_id(template_id: str, policy: dict[str, Any], source_zone_id: str) -> str:
    policy_id = policy_root_prefix(policy) or "scenario"
    resolved_source_zone_id = text_value(source_zone_id) or "source_zone"
    return f"{resolved_source_zone_id}__{policy_id}__{template_id}"


def build_source_zone_provenance(
    *,
    candidate_source_zone_metadata: dict[str, Any],
    candidate_source_zone_metadata_path: Path,
    policy: dict[str, Any],
    source_zone_id: str,
) -> dict[str, Any]:
    policy_source_zone_id = text_value(get_nested_value(policy, ("source_zone_policy", "source_zone_id")))
    candidate_source_zone_id = text_value(candidate_source_zone_metadata.get("source_zone_id"))
    source_zone_id_source = "candidate_source_zone_metadata"
    if policy_source_zone_id and candidate_source_zone_id and policy_source_zone_id == candidate_source_zone_id:
        source_zone_id_source = "policy_and_candidate_match"
    elif policy_source_zone_id:
        source_zone_id_source = "policy_template"

    release_sampling_policy = candidate_source_zone_metadata.get("release_sampling_policy", {})
    geometry = candidate_source_zone_metadata.get("geometry", {})
    return {
        "candidate_source_zone_metadata_path": display_path(candidate_source_zone_metadata_path),
        "candidate_source_zone_id": candidate_source_zone_id,
        "resolved_source_zone_id": text_value(source_zone_id),
        "source_zone_id_source": source_zone_id_source,
        "candidate_source_zone_geometry_type": text_value(geometry.get("type")) if isinstance(geometry, dict) else "",
        "candidate_source_zone_crs_epsg": candidate_source_zone_metadata.get("crs_epsg"),
        "candidate_source_zone_vertical_datum": text_value(candidate_source_zone_metadata.get("vertical_datum")),
        "release_sampling_mode": text_value(release_sampling_policy.get("mode")) if isinstance(release_sampling_policy, dict) else "",
        "release_sampling_seed": release_sampling_policy.get("seed") if isinstance(release_sampling_policy, dict) else None,
        "release_sampling_policy": text_value(release_sampling_policy.get("mode")) if isinstance(release_sampling_policy, dict) else "",
    }


def row_id_strategy(template_id: str, policy: dict[str, Any]) -> str:
    if template_id == "observed_rows_summary_v1":
        return f"{policy_root_prefix(policy)}_block_{SUMMARY_SCENARIO_SUFFIX}"
    return "source_zone_id__block_scenario_id"


def template_row_kind(template_id: str) -> str:
    if template_id == "observed_rows_summary_v1":
        return "single_row_release_summary"
    return "block_scenario_family_row"


def policy_root_prefix(policy: dict[str, Any]) -> str:
    policy_id = text_value(policy.get("policy_id"))
    if policy_id.endswith("_source_scenario_policy_v1"):
        return policy_id[: -len("_source_scenario_policy_v1")]
    return policy_id or "scenario"


def template_summary() -> list[dict[str, str]]:
    return [
        {"template_id": template_id, "description": description}
        for template_id, description in AVAILABLE_TEMPLATES.items()
    ]


def normalize_rows_for_compare(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append({column: csv_value(row.get(column, "")) for column in SCENARIO_TABLE_COLUMNS})
    return normalized


def row_for_csv(row: dict[str, Any]) -> dict[str, str]:
    return {column: csv_value(row.get(column, "")) for column in SCENARIO_TABLE_COLUMNS}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(SCENARIO_TABLE_COLUMNS)
        for row in rows:
            writer.writerow([csv_value(row.get(column)) for column in SCENARIO_TABLE_COLUMNS])


def csv_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.6f}" if value not in (1.0, 2.0, 3.0, 5.0) else f"{value:.1f}"
        return ""
    return str(value)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def get_nested_value(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def get_nested_mapping(mapping: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    value = get_nested_value(mapping, keys)
    return value if isinstance(value, dict) else {}


def get_nested_list(mapping: dict[str, Any], keys: tuple[str, ...]) -> list[Any]:
    value = get_nested_value(mapping, keys)
    return value if isinstance(value, list) else []


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Candidate Source-Zone Block-Scenario Table Generation",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Table status: `{report['scenario_table_status']}`",
        f"- Template: `{report['scenario_family_template_id']}`",
        f"- Template description: `{report['scenario_family_template_description']}`",
    ]
    if report.get("blocked_reason"):
        lines.append(f"- Blocked reason: {report['blocked_reason']}")
    lines.extend(["", "Scenario Family"])
    lines.append(f"- scenario_family_id: `{report.get('scenario_table_manifest', {}).get('scenario_family_id', '')}`")
    lines.extend(["", "Summary"])
    summary = report.get("scenario_table_summary", {})
    for key in ("row_count", "row_ids", "block_scenario_ids", "policy_sampling_weight_total", "normalized_sampling_share_total"):
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "Source Zone Provenance"])
    provenance = report.get("scenario_table_manifest", {}).get("source_zone_provenance", {})
    for key in (
        "candidate_source_zone_metadata_path",
        "candidate_source_zone_id",
        "resolved_source_zone_id",
        "source_zone_id_source",
        "candidate_source_zone_geometry_type",
        "candidate_source_zone_crs_epsg",
        "candidate_source_zone_vertical_datum",
        "release_sampling_mode",
        "release_sampling_seed",
    ):
        lines.append(f"- {key}: `{provenance.get(key, '')}`")
    lines.extend(["", "Source Inputs"])
    for key, value in report.get("source_inputs", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "Available Templates"])
    for entry in template_summary():
        lines.append(f"- `{entry['template_id']}`: {entry['description']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
