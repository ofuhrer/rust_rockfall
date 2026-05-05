#!/usr/bin/env python3
"""Lightweight repository consistency checks for agent-driven changes."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_PREFIXES = (
    "verification/results/",
    "validation/results/",
    "calibration/results/",
    "visualization/output/",
    "visualization/reports/standard_v0/",
)
ALLOWED_GENERATED = {
    "verification/results/.gitkeep",
    "validation/results/.gitkeep",
    "calibration/results/.gitkeep",
}
KNOWN_CONTACT_MODELS = {"translational_v0", "sphere_rotational_v1"}
KNOWN_ROUGHNESS_MODELS = {"none", "stochastic_contact_v1"}
KNOWN_SOIL_INTERACTION_MODELS = {"none", "scarring_contact_v1"}
KNOWN_CONTACT_STATES = {"airborne", "impact", "sliding", "rolling", "stopped"}
KNOWN_TERRAIN_TYPES = {
    "plane",
    "inclined_plane",
    "paraboloid",
    "step",
    "step_terrain",
    "v_shaped_valley",
    "terraced_slope",
    "sinusoidal_rough_slope",
    "gaussian_bump",
    "channelized_gully",
    "esri_ascii_grid",
    "ascii_dem",
    "esri_ascii_grid_clamped",
    "ascii_dem_clamped",
}
KNOWN_OUTPUT_KEYS = {"trajectory_csv", "diagnostics_json", "ensemble_deposition_csv"}
KNOWN_METRICS = {
    "position_error_m",
    "velocity_error_mps",
    "rebound_height_error_m",
    "stopping_distance_error_m",
    "impact_time_error_s",
    "impact_count",
    "runout_m",
    "max_speed_mps",
    "max_bounce_height_m",
    "rebound_height_m",
    "total_energy_initial_j",
    "total_energy_final_j",
    "energy_error_j",
    "energy_conservation_error_j",
    "energy_monotonicity_violation_j",
    "seed_repeat_max_position_delta_m",
    "roughness_zero_baseline_max_position_delta_m",
    "scarring_zero_baseline_max_position_delta_m",
    "different_seed_ensemble_runout_delta_m",
    "ensemble_mean_runout_m",
    "ensemble_median_runout_m",
    "ensemble_p05_runout_m",
    "ensemble_p95_runout_m",
    "ensemble_runout_spread_m",
    "ensemble_p95_max_kinetic_energy_j",
    "deposition_point_error_m",
    "runout_distance_error_m",
    "lateral_deviation_m",
    "validation_release_count",
    "validation_simulated_trajectory_count",
    "observed_mean_runout_m",
    "simulated_mean_runout_m",
    "deposition_centroid_error_m",
    "deposition_cloud_mean_nearest_error_m",
    "deposition_cloud_overlap_fraction",
    "lateral_spread_error_m",
    "final_speed_mps",
    "max_kinetic_energy_j",
    "max_rolling_residual_mps",
    "final_rolling_residual_mps",
    "final_contact_tangent_speed_mps",
    "final_angular_speed_radps",
    "max_scarring_depth_m",
    "max_scarring_drag_force_n",
    "total_scarring_energy_loss_j",
}


def main() -> int:
    errors: list[str] = []
    errors.extend(check_staged_generated_outputs())
    errors.extend(check_yaml_cases())
    errors.extend(check_schema_docs())
    errors.extend(check_documented_paths())
    errors.extend(check_contact_model_docs())
    errors.extend(check_version_consistency())
    errors.extend(check_tschamut_validation_metadata())
    errors.extend(check_calibration_metadata())

    if errors:
        for error in errors:
            print(f"consistency error: {error}", file=sys.stderr)
        return 1
    print("repository consistency checks passed")
    return 0


def check_staged_generated_outputs() -> list[str]:
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    ).stdout.splitlines()
    errors = []
    for path in staged:
        if path in ALLOWED_GENERATED:
            continue
        if any(path.startswith(prefix) for prefix in GENERATED_PREFIXES):
            errors.append(f"generated output is staged: {path}")
    return errors


def check_yaml_cases() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return ["PyYAML is required; install with `python3 -m pip install PyYAML`"]

    errors = []
    case_paths = sorted(ROOT.glob("verification/**/*.yaml")) + sorted(
        (ROOT / "validation/cases").glob("*.yaml")
    )
    for path in case_paths:
        data = yaml.safe_load(path.read_text()) or {}
        rel = path.relative_to(ROOT)
        terrain = data.get("terrain", {}) or {}
        terrain_type = terrain.get("type", terrain.get("kind"))
        if terrain_type not in KNOWN_TERRAIN_TYPES:
            errors.append(f"{rel}: unknown terrain type {terrain_type!r}")

        parameters = data.get("parameters", {}) or {}
        contact_model = parameters.get("contact_model", "translational_v0")
        if contact_model not in KNOWN_CONTACT_MODELS:
            errors.append(f"{rel}: unknown contact_model {contact_model!r}")

        roughness_model = parameters.get("roughness_model", "none")
        if roughness_model not in KNOWN_ROUGHNESS_MODELS:
            errors.append(f"{rel}: unknown roughness_model {roughness_model!r}")

        soil_interaction_model = parameters.get("soil_interaction_model", "none")
        if soil_interaction_model not in KNOWN_SOIL_INTERACTION_MODELS:
            errors.append(
                f"{rel}: unknown soil_interaction_model {soil_interaction_model!r}"
            )

        expected = data.get("expected", {}) or {}
        contact_state = expected.get("contact_state")
        if contact_state is not None and contact_state not in KNOWN_CONTACT_STATES:
            errors.append(f"{rel}: unknown expected.contact_state {contact_state!r}")

        outputs = data.get("outputs", {}) or {}
        for key in outputs:
            if key not in KNOWN_OUTPUT_KEYS:
                errors.append(f"{rel}: unknown outputs.{key}")

        metric_names = set(expected.get("metrics", []) or [])
        for section in ("values", "minimums", "maximums", "tolerances"):
            metric_names.update((expected.get(section, {}) or {}).keys())
        for metric in metric_names:
            base_metric = metric.removesuffix("_error")
            if metric not in KNOWN_METRICS and base_metric not in KNOWN_METRICS:
                errors.append(f"{rel}: unknown metric {metric!r}")
    return errors


def check_schema_docs() -> list[str]:
    schema = (ROOT / "docs/validation_data_schema.md").read_text()
    benchmark = (ROOT / "docs/benchmark_case_schema.yaml").read_text()
    required_schema_terms = [
        "contact_model",
        "translational_v0",
        "sphere_rotational_v1",
        "rolling_resistance_coefficient",
        "roughness_model",
        "stochastic_contact_v1",
        "roughness_std_normal",
        "roughness_std_tangent",
        "roughness_std_angle",
        "soil_interaction_model",
        "scarring_contact_v1",
        "soil_strength_pa",
        "scarring_drag_coefficient",
        "scarring_layer_density_kgpm3",
        "scarring_max_depth_m",
        "scarring_depth_m",
        "scarring_drag_force_n",
        "scarring_energy_loss_j",
        "max_scarring_depth_m",
        "max_scarring_drag_force_n",
        "total_scarring_energy_loss_j",
        "scarring_zero_baseline_max_position_delta_m",
        "final_rolling_residual_mps",
        "final_contact_tangent_speed_mps",
        "final_angular_speed_radps",
        "roughness_zero_baseline_max_position_delta_m",
        "different_seed_ensemble_runout_delta_m",
        "ascii_dem_clamped",
        "esri_ascii_grid_clamped",
    ]
    errors = []
    for term in required_schema_terms:
        if term not in schema:
            errors.append(f"docs/validation_data_schema.md omits {term}")
        if term in {
            "contact_model",
            "rolling_resistance_coefficient",
            "roughness_model",
            "roughness_std_normal",
            "roughness_std_tangent",
            "roughness_std_angle",
            "soil_interaction_model",
            "soil_strength_pa",
            "scarring_drag_coefficient",
            "scarring_layer_density_kgpm3",
            "scarring_max_depth_m",
        } and term not in benchmark:
            errors.append(f"docs/benchmark_case_schema.yaml omits {term}")
    return errors


def check_documented_paths() -> list[str]:
    errors = []
    docs = [
        ROOT / "README.md",
        ROOT / "visualization/README.md",
        ROOT / "AGENTS.md",
    ]
    pattern = re.compile(r"(?:python3|bash)\s+([A-Za-z0-9_./-]+)")
    for doc in docs:
        text = doc.read_text()
        for match in pattern.finditer(text):
            token = match.group(1)
            if token.startswith("-") or token in {"cargo", "git"}:
                continue
            path = ROOT / token
            if "/" in token and not path.exists():
                errors.append(f"{doc.relative_to(ROOT)} references missing path {token}")
    return errors


def check_contact_model_docs() -> list[str]:
    errors = []
    paths = [
        ROOT / "docs/model_review_v0.md",
        ROOT / "docs/model_design.md",
        ROOT / "docs/validation_data_schema.md",
    ]
    for path in paths:
        text = path.read_text()
        for model in KNOWN_CONTACT_MODELS:
            if model not in text:
                errors.append(f"{path.relative_to(ROOT)} omits contact model {model}")
        for model in KNOWN_SOIL_INTERACTION_MODELS:
            if model not in text:
                errors.append(
                    f"{path.relative_to(ROOT)} omits soil interaction model {model}"
                )
    terrain_model = ROOT / "docs/terrain_model.md"
    if not terrain_model.exists():
        errors.append("docs/terrain_model.md is missing")
    else:
        terrain_text = terrain_model.read_text()
        for term in ("ascii_dem_clamped", "idw_residual_dem_from_lps"):
            if term not in terrain_text:
                errors.append(f"docs/terrain_model.md omits {term}")
    return errors


def check_version_consistency() -> list[str]:
    cargo = (ROOT / "Cargo.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', cargo, re.MULTILINE)
    if not match:
        return ["Cargo.toml omits package version"]
    version = match.group(1)
    tagged = f"v{version}"
    errors = []
    required_paths = [
        ROOT / "README.md",
        ROOT / "docs/README.md",
        ROOT / "CHANGELOG.md",
    ]
    for path in required_paths:
        if tagged not in path.read_text():
            errors.append(f"{path.relative_to(ROOT)} omits {tagged}")

    report_generator = (ROOT / "visualization/build_report.py").read_text()
    if f'FALLBACK_MODEL_VERSION = "{version}"' not in report_generator:
        errors.append("visualization/build_report.py fallback version disagrees with Cargo.toml")
    if "model_version" not in report_generator:
        errors.append("visualization/build_report.py does not render model_version")
    return errors


def check_tschamut_validation_metadata() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return []
    errors = []
    registry = yaml.safe_load((ROOT / "data/datasets.yaml").read_text()) or {}
    datasets = {dataset.get("id"): dataset for dataset in registry.get("datasets", [])}
    dataset = datasets.get("tschamut2014")
    if not dataset:
        errors.append("data/datasets.yaml omits tschamut2014 metadata")
    else:
        for key in ("source_url", "doi", "license", "citation", "local_path", "processed_path"):
            if not dataset.get(key):
                errors.append(f"tschamut2014 dataset metadata omits {key}")

    case = yaml.safe_load((ROOT / "validation/cases/tschamut_basic.yaml").read_text()) or {}
    if (case.get("references") or {}).get("dataset") != "tschamut2014":
        errors.append("validation/cases/tschamut_basic.yaml does not reference dataset tschamut2014")
    observations = case.get("observations") or {}
    for key in ("release_points_csv", "deposition_points_csv"):
        path = observations.get(key)
        if not path:
            errors.append(f"tschamut_basic omits observations.{key}")
        elif not (ROOT / path).exists():
            errors.append(f"tschamut_basic references missing observations.{key}: {path}")
    if "validation_scope" not in case:
        errors.append("tschamut_basic omits validation_scope")

    report = ROOT / "visualization" / "build_report.py"
    report_text = report.read_text()
    if "Real-world validation" not in report_text:
        errors.append("visualization/build_report.py omits real-world validation wording")
    return errors


def check_calibration_metadata() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return []
    errors = []
    required_paths = [
        ROOT / "calibration/experiments/tschamut_v0_3/config.yaml",
        ROOT / "calibration/data/tschamut/split.yaml",
        ROOT / "calibration/experiments/tschamut_v0_3/candidate_results.csv",
        ROOT / "calibration/experiments/tschamut_v0_3/selected_parameters.yaml",
        ROOT / "calibration/experiments/tschamut_v0_3/summary.json",
        ROOT / "docs/tschamut_calibration.md",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing calibration artifact {path.relative_to(ROOT)}")

    split_path = ROOT / "calibration/data/tschamut/split.yaml"
    if split_path.exists():
        split = yaml.safe_load(split_path.read_text()) or {}
        calibration_ids = set(split.get("calibration_ids", []))
        holdout_ids = set(split.get("holdout_ids", []))
        intersection = calibration_ids & holdout_ids
        if intersection:
            errors.append(f"calibration split leaks ids across partitions: {sorted(intersection)}")
        if (split.get("leakage_check") or {}).get("intersection_size") != 0:
            errors.append("calibration split leakage_check.intersection_size is not zero")

    selected_path = ROOT / "calibration/experiments/tschamut_v0_3/selected_parameters.yaml"
    if selected_path.exists():
        selected = yaml.safe_load(selected_path.read_text()) or {}
        if selected.get("dataset_id") != "tschamut2014":
            errors.append("selected calibration parameters do not reference tschamut2014")
        if not selected.get("parameters"):
            errors.append("selected calibration parameters omit parameter values")

    docs = (ROOT / "docs/validation_plan.md").read_text() + "\n" + (
        ROOT / "docs/tschamut_calibration.md"
    ).read_text()
    for term in ("calibration", "holdout", "objective", "not operational"):
        if term not in docs:
            errors.append(f"calibration docs omit {term!r}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
