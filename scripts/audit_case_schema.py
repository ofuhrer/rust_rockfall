#!/usr/bin/env python3
"""Audit checked-in verification/validation YAML case schemas.

This is a strict-audit migration helper. Runtime case loading remains
backward compatible; this script reports unknown keys and missing/unsupported
schema versions before strict parsing becomes a default behavior.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised by caller environment
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SCHEMA_VERSION = "benchmark_case_v1"

TOP_LEVEL_KEYS = {
    "schema_version",
    "case_id",
    "title",
    "level",
    "description",
    "terrain",
    "terrain_classes",
    "block",
    "block_shape",
    "release",
    "release_zone",
    "parameters",
    "simulation",
    "random",
    "probabilistic_metadata",
    "hazard_layers",
    "hazard_probability",
    "hazard_map_package",
    "validation_scope",
    "observations",
    "expected",
    "outputs",
    "references",
    "report",
}

NESTED_KEYS = {
    "terrain": {"type", "kind", "parameters", "path", "metadata_path"},
    "terrain.parameters": {
        "z0_m",
        "slope_x",
        "slope_y",
        "ax",
        "ay",
        "step_x_m",
        "high_z_m",
        "low_z_m",
    },
    "terrain_classes": {"metadata_path"},
    "block": {"mass", "radius"},
    "block_shape": {"metadata_path"},
    "release": {"position", "velocity", "angular_velocity", "perturbation"},
    "release.perturbation": {"position_uniform_m", "velocity_uniform_mps"},
    "release_zone": {"metadata_path", "generated_release_points_csv"},
    "parameters": {
        "gravity",
        "normal_restitution",
        "tangential_restitution",
        "friction_coefficient",
        "rolling_resistance_coefficient",
        "contact_model",
        "soil_interaction_model",
        "soil_strength_pa",
        "scarring_drag_coefficient",
        "scarring_layer_density_kgpm3",
        "scarring_max_depth_m",
        "roughness_model",
        "roughness_std_normal",
        "roughness_std_tangent",
        "roughness_std_angle",
    },
    "simulation": {"dt", "t_max", "max_steps", "stop_velocity"},
    "random": {"seed", "ensemble_size"},
    "probabilistic_metadata": {
        "source_zone_metadata_path",
        "scenario_table_path",
        "map_product_id",
        "probability_mode",
        "normalization_scope",
        "scenario_id",
    },
    "hazard_layers": {"statistics"},
    "hazard_layers.statistics": {
        "kinetic_energy_exceedance_j",
        "jump_height_exceedance_m",
        "velocity_exceedance_mps",
    },
    "hazard_probability": {
        "probability_model",
        "metadata_path",
        "weight_column",
        "normalization_convention",
        "filters",
    },
    "hazard_probability.filters": {
        "source_zone_ids",
        "scenario_ids",
        "block_mass_kg_min",
        "block_mass_kg_max",
    },
    "hazard_map_package": {
        "map_product_id",
        "probability_mode",
        "normalization_scope",
        "source_zone_metadata_path",
        "scenario_table_path",
        "map_package_manifest_json",
        "limitations",
    },
    "validation_scope": {"type", "note"},
    "observations": {
        "release_points_csv",
        "deposition_points_csv",
        "trajectory_csv",
        "contact_events_csv",
    },
    "expected": {
        "metrics",
        "final_position_m",
        "final_velocity_mps",
        "rebound_height_m",
        "stopping_distance_m",
        "impact_time_s",
        "min_runout_m",
        "max_runout_m",
        "min_impact_count",
        "max_impact_count",
        "contact_state",
        "values",
        "minimums",
        "maximums",
        "tolerances",
    },
    "outputs": {
        "trajectory_csv",
        "trajectory_metadata_csv",
        "diagnostics_json",
        "manifest_json",
        "ensemble_deposition_csv",
        "ensemble_trajectories_dir",
        "ensemble_impact_events_dir",
        "ensemble_impact_events_parquet",
        "impact_events_csv",
        "impact_events_json",
    },
    "references": {"literature", "dataset", "notes"},
    "report": {"verifies", "does_not_verify"},
}

ARBITRARY_METRIC_MAPS = {
    "expected.values",
    "expected.minimums",
    "expected.maximums",
    "expected.tolerances",
}

DEFAULT_CASE_GLOBS = ("verification/**/*.yaml", "validation/cases/*.yaml")


def default_case_paths(root: Path = ROOT) -> list[Path]:
    paths: list[Path] = []
    for pattern in DEFAULT_CASE_GLOBS:
        paths.extend(root.glob(pattern))
    return sorted(path for path in paths if path.is_file())


def audit_mapping(data: dict[str, Any], rel_path: str, path: str = "") -> list[str]:
    errors: list[str] = []
    if path in ARBITRARY_METRIC_MAPS:
        return errors

    allowed = TOP_LEVEL_KEYS if path == "" else NESTED_KEYS.get(path)
    if allowed is not None:
        for key, value in data.items():
            if key not in allowed:
                dotted = key if path == "" else f"{path}.{key}"
                if path == "":
                    errors.append(f"{rel_path}: unknown top-level key {key!r}")
                else:
                    errors.append(f"{rel_path}: unknown {dotted}")
                continue
            if isinstance(value, dict):
                child_path = key if path == "" else f"{path}.{key}"
                errors.extend(audit_mapping(value, rel_path, child_path))
        return errors

    for key, value in data.items():
        if isinstance(value, dict):
            child_path = key if path == "" else f"{path}.{key}"
            errors.extend(audit_mapping(value, rel_path, child_path))
    return errors


def audit_case_data(data: dict[str, Any], rel_path: str) -> list[str]:
    errors: list[str] = []
    schema_version = data.get("schema_version")
    if schema_version is None:
        errors.append(f"{rel_path}: missing schema_version")
    elif schema_version != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            f"{rel_path}: unsupported schema_version {schema_version!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION!r}"
        )

    errors.extend(audit_mapping(data, rel_path))
    return errors


def audit_case_file(path: Path, root: Path = ROOT) -> list[str]:
    if yaml is None:
        return ["PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`"]
    rel_path = str(path.relative_to(root))
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        return [f"{rel_path}: expected YAML mapping at document root"]
    return audit_case_data(data, rel_path)


def audit_paths(paths: list[Path], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in paths:
        errors.extend(audit_case_file(path, root=root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="YAML case paths to audit; defaults to verification/**/*.yaml and validation/cases/*.yaml",
    )
    args = parser.parse_args(argv)
    paths = args.paths or default_case_paths()
    errors = audit_paths(paths)
    if errors:
        for error in errors:
            print(f"schema audit error: {error}", file=sys.stderr)
        return 1
    print(f"case schema audit passed for {len(paths)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
