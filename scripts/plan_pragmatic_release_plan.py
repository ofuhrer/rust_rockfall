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
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_block_scenario_sensitivity_plan_v1"
RELEASE_GEOMETRY_SAMPLING_SCHEMA_VERSION = "deterministic_release_geometry_sampling_plan_v1"
PLAN_TITLE = "Balfrin block-scenario sensitivity plan"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_SAME_SCALE_REFERENCE = ROOT / "docs/tschamut_public_same_scale_uncertainty_envelope.md"
DEFAULT_RELEASE_GEOMETRY_OUTPUT_ROOT = Path("/tmp/rust_rockfall_tb420_release_geometry_sampling")
EXPLICIT_NON_FREQUENCY_LABELS = [
    "conditional_sampling_only",
    "not_annual_frequency",
    "not_physical_probability",
    "not_return_period",
    "not_operational_hazard_map",
]
RELEASE_POINTS_COLUMNS = [
    "trajectory_id",
    "experiment_id",
    "x_m",
    "y_m",
    "z_m",
    "ground_z_m",
    "vx_mps",
    "vy_mps",
    "vz_mps",
    "block_id",
    "mass_kg",
    "radius_m",
    "source",
    "release_geometry_id",
    "release_geometry_type",
    "candidate_feature_id",
    "sample_index",
    "sampling_mode",
    "sampling_spacing_m",
    "sampling_seed",
]


class PragmaticReleasePlanError(ValueError):
    """User-facing release-plan error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("scenario-plan", "release-geometry-sampling"), default="scenario-plan")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--scenario-table", type=Path, default=DEFAULT_SCENARIO_TABLE)
    parser.add_argument("--same-scale-reference", type=Path, default=DEFAULT_SAME_SCALE_REFERENCE)
    parser.add_argument("--candidate-geometries", type=Path, default=None)
    parser.add_argument("--sampling-spacing-m", type=float, default=10.0)
    parser.add_argument("--sampling-seed", type=int, default=420)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_RELEASE_GEOMETRY_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        if args.mode == "release-geometry-sampling":
            report = build_release_geometry_sampling_report(
                candidate_geometries_path=args.candidate_geometries,
                output_root=args.output_root,
                sampling_spacing_m=args.sampling_spacing_m,
                seed=args.sampling_seed,
                write_outputs=True,
            )
        else:
            report = build_report(
                policy_path=args.policy,
                scenario_table_path=args.scenario_table,
                same_scale_reference_path=args.same_scale_reference,
            )
    except PragmaticReleasePlanError as exc:
        print(f"pragmatic release-plan error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.mode == "release-geometry-sampling":
        print(render_release_geometry_sampling_text_report(report))
    else:
        print(render_text_report(report))
    status_key = "release_plan_status" if args.mode == "release-geometry-sampling" else "scenario_plan_status"
    return 0 if report[status_key] == "ready" else 2


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


def build_release_geometry_sampling_report(
    *,
    candidate_geometries_path: Path | None,
    output_root: Path | None = None,
    sampling_spacing_m: float = 10.0,
    seed: int = 420,
    write_outputs: bool = False,
) -> dict[str, Any]:
    if sampling_spacing_m <= 0:
        raise PragmaticReleasePlanError("sampling-spacing-m must be greater than zero")
    if candidate_geometries_path is None:
        raise PragmaticReleasePlanError("candidate-geometries is required for release-geometry-sampling mode")

    if not candidate_geometries_path.exists():
        return blocked_release_geometry_sampling_report(
            candidate_geometries_path=candidate_geometries_path,
            output_root=output_root,
            sampling_spacing_m=sampling_spacing_m,
            seed=seed,
        )

    payload = load_yaml_or_json(candidate_geometries_path)
    features = normalize_candidate_features(payload)
    release_rows: list[dict[str, Any]] = []
    geometry_summaries: list[dict[str, Any]] = []
    geometry_type_counts: dict[str, int] = {}
    release_count_by_geometry_type: dict[str, int] = {}

    for feature_index, feature in enumerate(features, start=1):
        properties = feature.get("properties", {}) if isinstance(feature.get("properties"), dict) else {}
        geometry = feature.get("geometry", {}) if isinstance(feature.get("geometry"), dict) else {}
        geometry_type = text_value(geometry.get("type")) or "Unknown"
        geometry_type_key = geometry_type.lower()
        feature_id = stable_feature_id(feature=feature, feature_index=feature_index)
        release_geometry_id = text_value(properties.get("release_geometry_id")) or f"{feature_id}__{geometry_type_key}"
        source_zone_id = text_value(properties.get("source_zone_id")) or feature_id
        points = sample_geometry_points(
            geometry=geometry,
            feature_id=feature_id,
            sampling_spacing_m=sampling_spacing_m,
            seed=seed,
        )
        geometry_type_counts[geometry_type_key] = geometry_type_counts.get(geometry_type_key, 0) + 1
        release_count_by_geometry_type[geometry_type_key] = release_count_by_geometry_type.get(geometry_type_key, 0) + len(points)
        geometry_summaries.append(
            {
                "candidate_feature_id": feature_id,
                "release_geometry_id": release_geometry_id,
                "source_zone_id": source_zone_id,
                "geometry_type": geometry_type,
                "release_count": len(points),
                "sampling_mode": sampling_mode_for_geometry(geometry_type),
                "sampling_spacing_m": sampling_spacing_m,
            }
        )
        for sample_index, point in enumerate(points, start=1):
            release_id = f"{release_geometry_id}__release_{sample_index:04d}"
            release_rows.append(
                build_release_point_row(
                    release_id=release_id,
                    point=point,
                    properties=properties,
                    release_geometry_id=release_geometry_id,
                    geometry_type=geometry_type,
                    feature_id=feature_id,
                    sample_index=sample_index,
                    sampling_spacing_m=sampling_spacing_m,
                    seed=seed,
                    source_zone_id=source_zone_id,
                )
            )

    output_paths = release_geometry_output_paths(output_root)
    report = {
        "schema_version": RELEASE_GEOMETRY_SAMPLING_SCHEMA_VERSION,
        "release_plan_status": "ready",
        "blocked_reason": None,
        "read_only": not write_outputs,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_geometries_path": display_path(candidate_geometries_path),
        "sampling_policy": {
            "sampling_modes": ["point", "line_spacing", "area_grid"],
            "sampling_spacing_m": sampling_spacing_m,
            "sampling_seed": seed,
            "seed_role": "deterministic stable ordering and provenance label only; no stochastic physical probability",
            "point_mode": "one release point per point geometry",
            "line_mode": "distance-spaced points with endpoints preserved",
            "area_mode": "axis-aligned grid centers with centroid fallback for sub-spacing polygons",
        },
        "release_count_summary": {
            "candidate_geometry_count": len(features),
            "release_point_count": len(release_rows),
            "geometry_type_counts": geometry_type_counts,
            "release_count_by_geometry_type": release_count_by_geometry_type,
            "empty_candidate_handled": len(features) == 0,
        },
        "geometry_summaries": geometry_summaries,
        "release_points": release_rows,
        "output_paths": output_paths,
        "provenance": {
            "source_path": display_path(candidate_geometries_path),
            "source_sha256": sha256_file(candidate_geometries_path),
            "generated_by": "scripts/plan_pragmatic_release_plan.py --mode release-geometry-sampling",
            "candidate_interpretation": "workflow_candidate_only_not_validated_source_zone",
            "claim_boundary": {
                "validated_release_zone_evidence": False,
                "physical_probability_supported": False,
                "annual_frequency_supported": False,
                "operational_hazard_map_supported": False,
                "risk_or_exposure_supported": False,
            },
        },
    }
    if write_outputs:
        write_release_geometry_sampling_outputs(report)
    return report


def blocked_release_geometry_sampling_report(
    *,
    candidate_geometries_path: Path,
    output_root: Path | None,
    sampling_spacing_m: float,
    seed: int,
) -> dict[str, Any]:
    return {
        "schema_version": RELEASE_GEOMETRY_SAMPLING_SCHEMA_VERSION,
        "release_plan_status": "blocked_missing_inputs",
        "blocked_reason": "candidate geometries file is missing",
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_geometries_path": display_path(candidate_geometries_path),
        "sampling_policy": {
            "sampling_modes": ["point", "line_spacing", "area_grid"],
            "sampling_spacing_m": sampling_spacing_m,
            "sampling_seed": seed,
            "seed_role": "deterministic provenance only",
        },
        "release_count_summary": {
            "candidate_geometry_count": 0,
            "release_point_count": 0,
            "geometry_type_counts": {},
            "release_count_by_geometry_type": {},
            "empty_candidate_handled": False,
        },
        "geometry_summaries": [],
        "release_points": [],
        "output_paths": release_geometry_output_paths(output_root),
        "provenance": {
            "source_path": display_path(candidate_geometries_path),
            "source_sha256": None,
            "generated_by": "scripts/plan_pragmatic_release_plan.py --mode release-geometry-sampling",
            "candidate_interpretation": "workflow_candidate_only_not_validated_source_zone",
            "claim_boundary": {
                "validated_release_zone_evidence": False,
                "physical_probability_supported": False,
                "annual_frequency_supported": False,
                "operational_hazard_map_supported": False,
                "risk_or_exposure_supported": False,
            },
        },
    }


def normalize_candidate_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    payload_type = text_value(payload.get("type")).lower()
    raw_features: list[Any]
    if payload_type == "featurecollection":
        raw_features = payload.get("features", []) if isinstance(payload.get("features"), list) else []
    elif payload_type == "feature":
        raw_features = [payload]
    elif "geometry" in payload:
        raw_features = [{"type": "Feature", "properties": {}, "geometry": payload["geometry"]}]
    elif payload_type in {"point", "linestring", "polygon", "multipoint", "multilinestring", "multipolygon"}:
        raw_features = [{"type": "Feature", "properties": {}, "geometry": payload}]
    else:
        raise PragmaticReleasePlanError("candidate geometries must be GeoJSON FeatureCollection, Feature, or geometry")
    features: list[dict[str, Any]] = []
    for index, raw_feature in enumerate(raw_features, start=1):
        if not isinstance(raw_feature, dict):
            raise PragmaticReleasePlanError(f"candidate feature {index} must be an object")
        geometry = raw_feature.get("geometry")
        if not isinstance(geometry, dict):
            raise PragmaticReleasePlanError(f"candidate feature {index} must include a geometry object")
        features.append(raw_feature)
    return features


def stable_feature_id(*, feature: dict[str, Any], feature_index: int) -> str:
    properties = feature.get("properties", {}) if isinstance(feature.get("properties"), dict) else {}
    for key in ("candidate_release_zone_id", "release_geometry_id", "source_zone_id", "id"):
        value = text_value(properties.get(key))
        if value:
            return sanitize_id(value)
    feature_id = text_value(feature.get("id"))
    if feature_id:
        return sanitize_id(feature_id)
    geometry_text = json.dumps(feature.get("geometry", {}), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(geometry_text.encode("utf-8")).hexdigest()[:10]
    return f"candidate_geometry_{feature_index:03d}_{digest}"


def sanitize_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value.strip())
    return cleaned.strip("_") or "candidate_geometry"


def sample_geometry_points(
    *,
    geometry: dict[str, Any],
    feature_id: str,
    sampling_spacing_m: float,
    seed: int,
) -> list[tuple[float, float]]:
    geometry_type = text_value(geometry.get("type")).lower()
    coordinates = geometry.get("coordinates")
    if geometry_type == "point":
        return [coordinate_pair(coordinates)]
    if geometry_type == "multipoint":
        return sorted({coordinate_pair(point) for point in coordinates if isinstance(point, list)})
    if geometry_type == "linestring":
        return sample_line_string([coordinate_pair(point) for point in coordinates], sampling_spacing_m)
    if geometry_type == "multilinestring":
        points: list[tuple[float, float]] = []
        for line_index, line in enumerate(coordinates if isinstance(coordinates, list) else [], start=1):
            line_points = sample_line_string([coordinate_pair(point) for point in line], sampling_spacing_m)
            points.extend(line_points)
        return unique_points(points)
    if geometry_type == "polygon":
        return sample_polygon(coordinates, feature_id=feature_id, sampling_spacing_m=sampling_spacing_m, seed=seed)
    if geometry_type == "multipolygon":
        points = []
        for polygon in coordinates if isinstance(coordinates, list) else []:
            points.extend(sample_polygon(polygon, feature_id=feature_id, sampling_spacing_m=sampling_spacing_m, seed=seed))
        return unique_points(points)
    raise PragmaticReleasePlanError(f"unsupported candidate geometry type: {geometry.get('type')}")


def coordinate_pair(value: Any) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        raise PragmaticReleasePlanError("coordinates must contain x and y values")
    return (round(float(value[0]), 6), round(float(value[1]), 6))


def sample_line_string(points: list[tuple[float, float]], sampling_spacing_m: float) -> list[tuple[float, float]]:
    if not points:
        return []
    if len(points) == 1:
        return [points[0]]
    segment_lengths = [distance(start, end) for start, end in zip(points[:-1], points[1:])]
    total_length = sum(segment_lengths)
    if total_length == 0:
        return [points[0]]
    distances = [0.0]
    current = sampling_spacing_m
    while current < total_length:
        distances.append(round(current, 6))
        current += sampling_spacing_m
    if not math.isclose(distances[-1], total_length):
        distances.append(total_length)
    return unique_points([interpolate_line_point(points, segment_lengths, target) for target in distances])


def interpolate_line_point(points: list[tuple[float, float]], segment_lengths: list[float], target_distance: float) -> tuple[float, float]:
    walked = 0.0
    for index, segment_length in enumerate(segment_lengths):
        if segment_length == 0:
            continue
        if target_distance <= walked + segment_length or index == len(segment_lengths) - 1:
            ratio = max(0.0, min(1.0, (target_distance - walked) / segment_length))
            start = points[index]
            end = points[index + 1]
            return (round(start[0] + (end[0] - start[0]) * ratio, 6), round(start[1] + (end[1] - start[1]) * ratio, 6))
        walked += segment_length
    return points[-1]


def sample_polygon(
    coordinates: Any,
    *,
    feature_id: str,
    sampling_spacing_m: float,
    seed: int,
) -> list[tuple[float, float]]:
    rings = polygon_rings(coordinates)
    if not rings:
        return []
    outer = rings[0]
    xmin, ymin, xmax, ymax = bbox_for_points(outer)
    offset = deterministic_grid_offset(feature_id=feature_id, seed=seed, sampling_spacing_m=sampling_spacing_m)
    x_values = stepped_values(xmin + offset, xmax, sampling_spacing_m)
    y_values = stepped_values(ymin + offset, ymax, sampling_spacing_m)
    points: list[tuple[float, float]] = []
    for y_value in y_values:
        for x_value in x_values:
            point = (round(x_value, 6), round(y_value, 6))
            if point_in_polygon_with_holes(point, rings):
                points.append(point)
    if not points:
        centroid = polygon_centroid(outer)
        if point_in_polygon_with_holes(centroid, rings):
            points.append(centroid)
    return unique_points(points)


def polygon_rings(coordinates: Any) -> list[list[tuple[float, float]]]:
    if not isinstance(coordinates, list):
        return []
    rings: list[list[tuple[float, float]]] = []
    for ring in coordinates:
        if not isinstance(ring, list):
            continue
        ring_points = [coordinate_pair(point) for point in ring]
        if len(ring_points) >= 3:
            rings.append(ring_points)
    return rings


def deterministic_grid_offset(*, feature_id: str, seed: int, sampling_spacing_m: float) -> float:
    digest = hashlib.sha256(f"{seed}:{feature_id}".encode("utf-8")).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF
    return round((0.25 + 0.5 * fraction) * sampling_spacing_m, 6)


def stepped_values(start: float, stop: float, step: float) -> list[float]:
    if start > stop:
        return []
    values: list[float] = []
    current = start
    while current <= stop + 1e-9:
        values.append(current)
        current += step
    return values


def point_in_polygon_with_holes(point: tuple[float, float], rings: list[list[tuple[float, float]]]) -> bool:
    if not rings or not point_in_ring(point, rings[0], include_boundary=True):
        return False
    return not any(point_in_ring(point, hole, include_boundary=True) for hole in rings[1:])


def point_in_ring(point: tuple[float, float], ring: list[tuple[float, float]], *, include_boundary: bool) -> bool:
    x, y = point
    inside = False
    for first, second in zip(ring, ring[1:] + ring[:1]):
        x1, y1 = first
        x2, y2 = second
        if include_boundary and point_on_segment(point, first, second):
            return True
        crosses = (y1 > y) != (y2 > y)
        if crosses:
            slope_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < slope_x:
                inside = not inside
    return inside


def point_on_segment(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> bool:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    cross = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross) > 1e-9:
        return False
    return min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9 and min(y1, y2) - 1e-9 <= py <= max(y1, y2) + 1e-9


def polygon_centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    if len(points) < 3:
        return points[0] if points else (0.0, 0.0)
    area_twice = 0.0
    cx = 0.0
    cy = 0.0
    for first, second in zip(points, points[1:] + points[:1]):
        cross = first[0] * second[1] - second[0] * first[1]
        area_twice += cross
        cx += (first[0] + second[0]) * cross
        cy += (first[1] + second[1]) * cross
    if abs(area_twice) < 1e-9:
        return (round(sum(point[0] for point in points) / len(points), 6), round(sum(point[1] for point in points) / len(points), 6))
    return (round(cx / (3.0 * area_twice), 6), round(cy / (3.0 * area_twice), 6))


def bbox_for_points(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    return (min(point[0] for point in points), min(point[1] for point in points), max(point[0] for point in points), max(point[1] for point in points))


def distance(start: tuple[float, float], end: tuple[float, float]) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def unique_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    seen: set[tuple[float, float]] = set()
    unique: list[tuple[float, float]] = []
    for point in points:
        if point not in seen:
            seen.add(point)
            unique.append(point)
    return unique


def sampling_mode_for_geometry(geometry_type: str) -> str:
    key = geometry_type.lower()
    if key in {"point", "multipoint"}:
        return "point"
    if key in {"linestring", "multilinestring"}:
        return "line_spacing"
    if key in {"polygon", "multipolygon"}:
        return "area_grid"
    return "unsupported"


def build_release_point_row(
    *,
    release_id: str,
    point: tuple[float, float],
    properties: dict[str, Any],
    release_geometry_id: str,
    geometry_type: str,
    feature_id: str,
    sample_index: int,
    sampling_spacing_m: float,
    seed: int,
    source_zone_id: str,
) -> dict[str, Any]:
    return {
        "trajectory_id": release_id,
        "experiment_id": text_value(properties.get("experiment_id")) or "deterministic_release_geometry_sampling_v1",
        "x_m": point[0],
        "y_m": point[1],
        "z_m": properties.get("z_m", ""),
        "ground_z_m": properties.get("ground_z_m", ""),
        "vx_mps": properties.get("vx_mps", 0.0),
        "vy_mps": properties.get("vy_mps", 0.0),
        "vz_mps": properties.get("vz_mps", 0.0),
        "block_id": text_value(properties.get("block_id")) or f"{sample_index:03d}",
        "mass_kg": properties.get("mass_kg", ""),
        "radius_m": properties.get("radius_m", ""),
        "source": (
            f"deterministic {sampling_mode_for_geometry(geometry_type)} candidate release sampling; "
            f"source_zone_id={source_zone_id}; not validated source-zone evidence"
        ),
        "release_geometry_id": release_geometry_id,
        "release_geometry_type": geometry_type,
        "candidate_feature_id": feature_id,
        "sample_index": sample_index,
        "sampling_mode": sampling_mode_for_geometry(geometry_type),
        "sampling_spacing_m": sampling_spacing_m,
        "sampling_seed": seed,
    }


def release_geometry_output_paths(output_root: Path | None) -> dict[str, str | None]:
    if output_root is None:
        return {"release_points_csv": None, "manifest_json": None}
    return {
        "release_points_csv": display_path(output_root / "release_points_lv95.csv"),
        "manifest_json": display_path(output_root / "release_geometry_sampling_manifest.json"),
    }


def write_release_geometry_sampling_outputs(report: dict[str, Any]) -> None:
    output_paths = report.get("output_paths", {})
    release_points_path = repo_path(output_paths.get("release_points_csv"))
    manifest_path = repo_path(output_paths.get("manifest_json"))
    if not is_allowed_output_root(release_points_path.parent) or not is_allowed_output_root(manifest_path.parent):
        raise PragmaticReleasePlanError("output-root must stay under /tmp or an ignored repo output root")
    release_points_path.parent.mkdir(parents=True, exist_ok=True)
    with release_points_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RELEASE_POINTS_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in report.get("release_points", []):
            writer.writerow({column: csv_value(row.get(column)) for column in RELEASE_POINTS_COLUMNS})
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_allowed_output_root(output_root: Path) -> bool:
    resolved = output_root.resolve(strict=False)
    allowed_roots = [
        Path("/tmp").resolve(strict=False),
        (ROOT / "validation/private").resolve(strict=False),
        (ROOT / "hazard/results").resolve(strict=False),
    ]
    return any(resolved == root or root in resolved.parents for root in allowed_roots)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_yaml_or_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
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


def repo_path(value: Any) -> Path:
    path = Path(text_value(value))
    return path if path.is_absolute() else ROOT / path


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def render_release_geometry_sampling_text_report(report: dict[str, Any]) -> str:
    summary = report.get("release_count_summary", {})
    lines = [
        "Deterministic Release Geometry Sampling Plan",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Release plan status: `{report['release_plan_status']}`",
        f"- Candidate geometries: `{summary.get('candidate_geometry_count', 0)}`",
        f"- Release points: `{summary.get('release_point_count', 0)}`",
        f"- Sampling spacing m: `{report.get('sampling_policy', {}).get('sampling_spacing_m', '')}`",
        f"- Sampling seed: `{report.get('sampling_policy', {}).get('sampling_seed', '')}`",
    ]
    if report.get("blocked_reason"):
        lines.append(f"- Blocked reason: {report['blocked_reason']}")
    lines.append("- release_count_by_geometry_type:")
    for key, value in summary.get("release_count_by_geometry_type", {}).items():
        lines.append(f"  - {key}: `{value}`")
    lines.append("- outputs:")
    for key, value in report.get("output_paths", {}).items():
        lines.append(f"  - {key}: `{value}`")
    lines.append("- candidate_interpretation: `workflow_candidate_only_not_validated_source_zone`")
    return "\n".join(lines)


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
