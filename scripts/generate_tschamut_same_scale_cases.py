#!/usr/bin/env python3
"""Regenerate the same-scale Tschamut private case YAMLs from frozen records.

This helper is intentionally narrow:

- it is read-only unless an output root is supplied without ``--dry-run``;
- it reconstructs the gate and target private case YAMLs from the committed
  frozen run records plus the processed public input metadata;
- it preserves the public provenance, source-zone/scenario paths, release
  selection, thresholds, and non-operational claim boundary used by the
  selected same-scale pilot;
- it emits an explicit blocked state when any required committed input is
  missing.

The command is designed for future worker agents that need to recreate the
ignored private case YAMLs without hand-editing them.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_same_scale_case_regeneration_v1"

DEFAULT_GATE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
DEFAULT_TARGET_RECORD = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_RELEASE_POINTS = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"
DEFAULT_OBSERVED_DEPOSITION = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv"
DEFAULT_TERRAIN_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml"
DEFAULT_TERRAIN_CROP = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc"

GATE_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/gate_v1"
TARGET_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1"

GATE_MAP_PRODUCT_ID = "tschamut_public_conditional_gate_v1"
TARGET_MAP_PRODUCT_ID = "tschamut_public_conditional_gate_v1"
GATE_CASE_ID = "validation_tschamut_public_conditional_gate_v1"
TARGET_CASE_ID = "validation_tschamut_public_target_gate_v1"

SUPPORTED_ROLES = {"gate", "target", "both"}


class CaseGenerationError(ValueError):
    """User-facing regeneration error."""

    def __init__(self, message: str, *, missing_input_paths: list[str] | None = None):
        super().__init__(message)
        self.missing_input_paths = missing_input_paths or []


@dataclass(frozen=True)
class FileCheck:
    path: Path
    exists: bool
    kind: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--dry-run", action="store_true", help="do not write YAML outputs")
    parser.add_argument("--output-root", type=Path, default=ROOT / "validation/private/tschamut_public_pilot")
    parser.add_argument("--role", choices=tuple(sorted(SUPPORTED_ROLES)), default="both")
    parser.add_argument("--gate-record", type=Path, default=DEFAULT_GATE_RECORD)
    parser.add_argument("--target-record", type=Path, default=DEFAULT_TARGET_RECORD)
    parser.add_argument("--source-scenario-policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--source-zone-metadata", type=Path, default=DEFAULT_SOURCE_ZONE_METADATA)
    parser.add_argument("--scenario-table", type=Path, default=DEFAULT_SCENARIO_TABLE)
    parser.add_argument("--release-points", type=Path, default=DEFAULT_RELEASE_POINTS)
    parser.add_argument("--observed-deposition", type=Path, default=DEFAULT_OBSERVED_DEPOSITION)
    parser.add_argument("--terrain-metadata", type=Path, default=DEFAULT_TERRAIN_METADATA)
    parser.add_argument("--terrain-crop", type=Path, default=DEFAULT_TERRAIN_CROP)
    args = parser.parse_args(argv)

    try:
        report = build_report(args)
        generated_cases = report.pop("_generated_cases", {})
        if report["case_regeneration_status"] == "ready" and not args.dry_run:
            write_cases(generated_cases)
    except CaseGenerationError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "case_regeneration_status": "blocked_missing_inputs",
            "readiness_status": "blocked_missing_inputs",
            "generated_case_ids": [],
            "generated_case_paths": [],
            "source_record_paths": [],
            "required_input_paths": [],
            "missing_input_paths": list(getattr(exc, "missing_input_paths", [])),
            "defaults_changed": False,
            "physics_changed": False,
            "thresholds_changed": False,
            "source_zone_semantics_changed": False,
            "scenario_probability_semantics_changed": False,
            "output_path_strategy": "repo_relative_validation_private_paths",
            "deterministic_generation_evidence": {},
            "blocked_reason": str(exc),
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }
        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_text_report(report))
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    required_inputs = [
        args.gate_record,
        args.target_record,
        args.source_scenario_policy,
        args.source_zone_metadata,
        args.scenario_table,
        args.release_points,
        args.observed_deposition,
        args.terrain_metadata,
        args.terrain_crop,
    ]
    missing = [display_path(path) for path in required_inputs if not path.exists()]
    if missing:
        raise CaseGenerationError(
            "required committed inputs are missing: " + ", ".join(missing),
            missing_input_paths=missing,
        )

    gate_record = read_yaml(args.gate_record)
    target_record = read_yaml(args.target_record)
    policy = read_yaml(args.source_scenario_policy)
    source_zone_metadata = read_yaml(args.source_zone_metadata)

    if text_value(source_zone_metadata, "source_zone_id") != "tschamut_public_lps_release_bbox":
        raise CaseGenerationError(
            f"source zone metadata id mismatch: {text_value(source_zone_metadata, 'source_zone_id')!r}"
        )

    release_rows = read_csv_rows(args.release_points)
    deposition_rows = read_csv_rows(args.observed_deposition)
    shared_ids = sorted(
        row["trajectory_id"]
        for row in release_rows
        if row.get("trajectory_id") and any(dep.get("trajectory_id") == row["trajectory_id"] for dep in deposition_rows)
    )
    if not shared_ids:
        raise CaseGenerationError(
            f"no shared release/deposition rows were found in {args.release_points} and {args.observed_deposition}"
        )

    selected_id = shared_ids[0]
    release_row = next(row for row in release_rows if row["trajectory_id"] == selected_id)
    deposition_row = next(row for row in deposition_rows if row["trajectory_id"] == selected_id)
    block_scenario = select_block_scenario(policy, release_row.get("block_id"))

    checked_paths = [
        display_path(path)
        for path in (
            args.gate_record,
            args.target_record,
            args.source_scenario_policy,
            args.source_zone_metadata,
            args.scenario_table,
            args.release_points,
            args.observed_deposition,
            args.terrain_metadata,
            args.terrain_crop,
        )
    ]
    selected_roles = ("gate", "target") if args.role == "both" else (args.role,)
    generated_cases = {
        role: build_case(
            role=role,
            selected_release_row=release_row,
            selected_deposition_row=deposition_row,
            policy=policy,
            source_zone_metadata=source_zone_metadata,
            source_zone_metadata_path=args.source_zone_metadata,
            scenario_table=args.scenario_table,
            terrain_metadata=args.terrain_metadata,
            terrain_crop=args.terrain_crop,
            output_root=args.output_root / ("gate_v1" if role == "gate" else "target_gate_v1"),
        )
        for role in selected_roles
    }

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_regeneration_status": "ready",
        "readiness_status": "ready",
        "generated_case_ids": [generated_cases[role]["case_id"] for role in selected_roles],
        "generated_case_paths": [generated_cases[role]["_yaml_path"] for role in selected_roles],
        "source_record_paths": checked_paths,
        "required_input_paths": checked_paths,
        "missing_input_paths": [],
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "source_zone_semantics_changed": False,
        "scenario_probability_semantics_changed": False,
        "output_path_strategy": "repo_relative_validation_private_paths",
        "deterministic_generation_evidence": {
            "reference_selection_rule": "lexicographically smallest shared trajectory_id between release_points and observed_deposition",
            "selected_reference_trajectory_id": selected_id,
            "shared_reference_row_count": len(shared_ids),
            "selected_release_row": {
                "block_id": release_row.get("block_id"),
                "mass_kg": release_row.get("mass_kg"),
                "radius_m": release_row.get("radius_m"),
                "release_position_m": [release_row.get("x_m"), release_row.get("y_m"), release_row.get("z_m")],
            },
            "selected_block_scenario": {
                "block_scenario_id": block_scenario.get("block_scenario_id"),
                "block_mass_kg": block_scenario.get("block_mass_kg"),
                "block_radius_m": block_scenario.get("block_radius_m"),
            },
            "source_zone_id": text_value(source_zone_metadata, "source_zone_id"),
            "gate_record_id": text_value(gate_record, "run_id"),
            "target_record_id": text_value(target_record, "run_id"),
        },
        "blocked_reason": "none",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "_generated_cases": generated_cases,
        "regeneration_commands": [
            command_for_role(role, args.output_root) for role in selected_roles
        ],
        "required_inputs": {
            "gate_record": display_path(args.gate_record),
            "target_record": display_path(args.target_record),
            "source_scenario_policy": display_path(args.source_scenario_policy),
            "source_zone_metadata": display_path(args.source_zone_metadata),
            "scenario_table": display_path(args.scenario_table),
            "release_points": display_path(args.release_points),
            "observed_deposition": display_path(args.observed_deposition),
            "terrain_metadata": display_path(args.terrain_metadata),
            "terrain_crop": display_path(args.terrain_crop),
        },
    }
    return report


def command_for_role(role: str, output_root: Path) -> str:
    return (
        "PYENV_VERSION=system uv run python scripts/generate_tschamut_same_scale_cases.py "
        f"--role {role} --output-root {shlex.quote(str(output_root))} --format json"
    )


def build_case(
    *,
    role: str,
    selected_release_row: dict[str, str],
    selected_deposition_row: dict[str, str],
    policy: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    source_zone_metadata_path: Path,
    scenario_table: Path,
    terrain_metadata: Path,
    terrain_crop: Path,
    output_root: Path,
) -> dict[str, Any]:
    case_meta = case_role_metadata(role)
    block_scenario = select_block_scenario(policy, selected_release_row.get("block_id"))
    release_position = [float(selected_release_row["x_m"]), float(selected_release_row["y_m"]), float(selected_release_row["z_m"])]
    release_velocity = [float(selected_release_row["vx_mps"]), float(selected_release_row["vy_mps"]), float(selected_release_row["vz_mps"])]
    block = {
        "mass": float(block_scenario["block_mass_kg"]),
        "radius": float(block_scenario["block_radius_m"]),
    }
    case = {
        "case_id": case_meta["case_id"],
        "title": case_meta["title"],
        "level": 5,
        "description": case_meta["description"],
        "terrain": {
            "type": "ascii_dem_clamped",
            "path": str(rel(terrain_crop)),
            "metadata_path": str(rel(terrain_metadata)),
        },
        "block": block,
        "release": {
            "position": release_position,
            "velocity": release_velocity,
        },
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.25,
            "tangential_restitution": 0.85,
            "friction_coefficient": 0.45,
            "contact_model": "translational_v0",
            "roughness_model": "stochastic_contact_v1",
            "roughness_std_normal": 0.08,
            "roughness_std_tangent": 0.06,
            "roughness_std_angle": 0.08,
        },
        "simulation": {"dt": 0.02, "t_max": 18.0, "max_steps": 900, "stop_velocity": 0.1},
        "random": {
            "seed": int(text_value(policy, "source_zone_policy.release_sampling.seed")),
            "ensemble_size": int(case_meta["ensemble_size"]),
        },
        "hazard_layers": {
            "statistics": case_meta["hazard_thresholds"],
        },
        "validation_scope": {
            "type": "public-benchmark-reproduction",
            "note": "Scientific diagnostic only; no tuning, operational validity, or proprietary-model equivalence claim.",
        },
        "observations": {
            "release_points_csv": str(rel(DEFAULT_RELEASE_POINTS)),
            "deposition_points_csv": str(rel(DEFAULT_OBSERVED_DEPOSITION)),
        },
        "expected": {
            "metrics": [
                "validation_release_count",
                "validation_simulated_trajectory_count",
                "observed_mean_runout_m",
                "simulated_mean_runout_m",
                "runout_distance_error_m",
                "deposition_centroid_error_m",
                "deposition_cloud_mean_nearest_error_m",
                "lateral_spread_error_m",
                "deposition_cloud_overlap_fraction",
            ],
            "tolerances": {},
        },
        "outputs": {
            "diagnostics_json": str(rel(case_meta["diagnostics_json"])),
            "manifest_json": str(rel(case_meta["manifest_json"])),
            "trajectory_csv": str(rel(case_meta["trajectory_csv"])),
            "ensemble_deposition_csv": str(rel(case_meta["ensemble_deposition_csv"])),
            "ensemble_trajectories_dir": str(rel(case_meta["ensemble_trajectories_dir"])),
            "ensemble_impact_events_dir": str(rel(case_meta["ensemble_impact_events_dir"])),
            "trajectory_metadata_csv": str(rel(case_meta["trajectory_metadata_csv"])),
        },
        "references": {
            "dataset": "tschamut2014",
            "literature": [
                "Volkwein, A., Gerber, W. (2018). Repetitive trajectory testing in Tschamut 2014. EnviDat. https://doi.org/10.16904/envidat.34.",
                "Volkwein et al. (2018). Repetitive Rockfall Trajectory Testing. Geosciences 8(3), 88. https://doi.org/10.3390/geosciences8030088.",
                "swisstopo swissALTI3D public terrain data, LV95/LN02, 2 m COG tile.",
            ],
            "notes": [
                "Uses scan_surface_fit_v1 coordinate preprocessing by default; bbox_align_v1 and overview_offset_v1 remain fallback/comparison modes.",
                "No restitution, friction, roughness, scarring, or contact-model parameters are tuned to these results.",
            ],
        },
        "schema_version": "benchmark_case_v1",
        "probabilistic_metadata": {
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "scenario_table_path": display_path(scenario_table),
            "map_product_id": case_meta["map_product_id"],
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "scenario_id": "tschamut_public_block_observed_rows",
        },
        "hazard_probability": {
            "probability_model": "sampling_weighted",
            "metadata_path": display_path(case_meta["trajectory_metadata_csv"]),
            "weight_column": "sampling_weight",
            "normalization_convention": "conditioned_on_filter",
            "filters": {
                "source_zone_ids": [text_value(source_zone_metadata, "source_zone_id")],
                "scenario_ids": ["tschamut_public_block_observed_rows"],
                "block_mass_kg_min": None,
                "block_mass_kg_max": None,
            },
        },
        "hazard_map_package": {
            "map_product_id": case_meta["map_product_id"],
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "scenario_table_path": display_path(scenario_table),
            "map_package_manifest_json": display_path(case_meta["map_package_manifest_json"]),
            "limitations": [
                "Research diagnostic only; not operational.",
                "No physical or annual probability model is included.",
            ],
        },
        "_yaml_path": display_path(
            output_root / ("tschamut_public_conditional_gate_case.yaml" if role == "gate" else "tschamut_public_target_gate_case.yaml")
        ),
    }
    return case


def case_role_metadata(role: str) -> dict[str, Any]:
    if role == "gate":
        return {
            "case_id": GATE_CASE_ID,
            "title": "Tschamut public conditional gate v1",
            "description": "Same-scale selected Tschamut conditional gate staged locally from public inputs. No parameters are tuned.",
            "ensemble_size": 6,
            "map_product_id": GATE_MAP_PRODUCT_ID,
            "hazard_thresholds": {
                "kinetic_energy_exceedance_j": [1000.0, 10000.0],
                "jump_height_exceedance_m": [1.0, 2.0],
                "velocity_exceedance_mps": [5.0, 10.0],
            },
            "diagnostics_json": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_metrics.json",
            "manifest_json": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_manifest.json",
            "trajectory_csv": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectory.csv",
            "ensemble_deposition_csv": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_deposition.csv",
            "ensemble_trajectories_dir": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectories",
            "ensemble_impact_events_dir": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_impacts",
            "trajectory_metadata_csv": GATE_OUTPUT_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectory_metadata.csv",
            "map_package_manifest_json": GATE_OUTPUT_ROOT / "tschamut_public_conditional_gate_v1_map_package_manifest.json",
        }
    if role == "target":
        return {
            "case_id": TARGET_CASE_ID,
            "title": "Tschamut public target gate v1",
            "description": "Same-scale selected Tschamut conditional target gate staged locally from public inputs. No parameters are tuned.",
            "ensemble_size": 100,
            "map_product_id": TARGET_MAP_PRODUCT_ID,
            "hazard_thresholds": {
                "kinetic_energy_exceedance_j": [1000.0, 10000.0],
                "jump_height_exceedance_m": [0.5, 1.0, 2.0],
                "velocity_exceedance_mps": [5.0, 10.0],
            },
            "diagnostics_json": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_metrics.json",
            "manifest_json": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_manifest.json",
            "trajectory_csv": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_trajectory.csv",
            "ensemble_deposition_csv": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_deposition.csv",
            "ensemble_trajectories_dir": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_trajectories",
            "ensemble_impact_events_dir": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_impacts",
            "trajectory_metadata_csv": TARGET_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_trajectory_metadata.csv",
            "map_package_manifest_json": TARGET_OUTPUT_ROOT / "tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json",
        }
    raise CaseGenerationError(f"unsupported role: {role}")


def rel(path: Path) -> Path:
    if path.is_absolute():
        try:
            return path.relative_to(ROOT)
        except ValueError:
            return path
    return path


def display_path(path: Path) -> str:
    return str(rel(path))


def select_block_scenario(policy: dict[str, Any], block_id: str | None) -> dict[str, Any]:
    scenarios = policy.get("block_scenario_policy", {}).get("scenarios", [])
    if not isinstance(scenarios, list) or not scenarios:
        raise CaseGenerationError("policy is missing block_scenario_policy.scenarios")
    by_suffix = {
        "1": "tschamut_public_block_medium",
        "2": "tschamut_public_block_large",
        "4": "tschamut_public_block_small",
    }
    preferred_id = by_suffix.get(str(block_id or ""))
    if preferred_id is not None:
        for scenario in scenarios:
            if scenario.get("block_scenario_id") == preferred_id:
                return scenario
    for scenario in scenarios:
        if scenario.get("block_mass_kg") == 69.0 or scenario.get("block_radius_m") == 0.176667:
            return scenario
    return scenarios[0]


def text_value(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise CaseGenerationError(f"missing required field {dotted_path}")
        current = current[part]
    return current


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - keep path context.
        raise CaseGenerationError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CaseGenerationError(f"expected YAML mapping in {path}")
    return data


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_cases(cases: dict[str, dict[str, Any]]) -> None:
    for role, case in cases.items():
        yaml_path = Path(case["_yaml_path"])
        case = {k: v for k, v in case.items() if k != "_yaml_path"}
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"case_regeneration_status: {report['case_regeneration_status']}",
        f"readiness_status: {report['readiness_status']}",
        f"generated_case_ids: {', '.join(report['generated_case_ids']) or 'none'}",
        f"generated_case_paths: {', '.join(report['generated_case_paths']) or 'none'}",
        f"missing_input_paths: {', '.join(report['missing_input_paths']) or 'none'}",
        f"defaults_changed: {report['defaults_changed']}",
        f"physics_changed: {report['physics_changed']}",
        f"thresholds_changed: {report['thresholds_changed']}",
        f"source_zone_semantics_changed: {report['source_zone_semantics_changed']}",
        f"scenario_probability_semantics_changed: {report['scenario_probability_semantics_changed']}",
        f"scale_up_authorized: {report['scale_up_authorized']}",
        f"operational_claims_allowed: {report['operational_claims_allowed']}",
    ]
    for label, command in zip(("gate", "target"), report.get("regeneration_commands", []), strict=False):
        lines.append(f"{label}_command: {command}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
