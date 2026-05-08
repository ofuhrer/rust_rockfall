#!/usr/bin/env python3
"""Lightweight repository consistency checks for agent-driven changes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_PREFIXES = (
    "verification/results/",
    "validation/results/",
    "calibration/results/",
    "hazard/results/",
    "visualization/output/",
    "visualization/reports/standard_v0/",
)
ALLOWED_GENERATED = {
    "verification/results/.gitkeep",
    "validation/results/.gitkeep",
    "calibration/results/.gitkeep",
    "hazard/results/.gitkeep",
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
KNOWN_OUTPUT_KEYS = {
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
}
KNOWN_METRICS = {
    "position_error_m",
    "velocity_error_mps",
    "rebound_height_error_m",
    "stopping_distance_error_m",
    "impact_time_error_s",
    "impact_count",
    "impact_event_count",
    "significant_impact_count",
    "significant_impact_min_normal_speed_mps",
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
    "validation_trajectory_count",
    "observed_trajectory_sample_count",
    "trajectory_shape_mean_error_m",
    "trajectory_shape_p95_error_m",
    "trajectory_shape_max_error_m",
    "trajectory_final_position_mean_error_m",
    "trajectory_energy_mean_relative_error",
    "trajectory_max_jump_height_mean_error_m",
    "trajectory_jump_height_envelope_error_m",
    "observed_contact_event_count",
    "contact_event_compared_count",
    "impact_timing_mean_error_s",
    "impact_timing_p95_error_s",
    "rebound_velocity_mean_error_mps",
    "rebound_velocity_p95_error_mps",
    "post_impact_energy_change_mean_error_j",
    "post_impact_energy_change_p95_error_j",
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
    "release_zone_point_count",
    "release_zone_extent_area_m2",
    "release_zone_mean_runout_m",
    "release_zone_max_runout_m",
}


def main() -> int:
    errors: list[str] = []
    errors.extend(check_staged_generated_outputs())
    errors.extend(check_tracked_copy_suffix_docs())
    errors.extend(check_strict_case_schema_audit())
    errors.extend(check_yaml_cases())
    errors.extend(check_schema_docs())
    errors.extend(check_documented_paths())
    errors.extend(check_contact_model_docs())
    errors.extend(check_version_consistency())
    errors.extend(check_chant_sura_validation_metadata())
    errors.extend(check_tschamut_validation_metadata())
    errors.extend(check_public_benchmark_framework())
    errors.extend(check_calibration_metadata())
    errors.extend(check_scarring_not_in_tschamut_workflows())
    errors.extend(check_hazard_layer_metadata())
    errors.extend(check_swisstopo_geodata_metadata())
    errors.extend(check_hazard_claim_hygiene())

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
        if path.startswith("data/private/") or path.startswith("validation/private/"):
            errors.append(f"private local data or generated private case is staged: {path}")
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    ).stdout.splitlines()
    for path in tracked:
        if path in ALLOWED_GENERATED:
            continue
        if any(path.startswith(prefix) for prefix in GENERATED_PREFIXES):
            errors.append(f"generated output is tracked: {path}")
        if path.startswith("data/raw/") and path != "data/raw/.gitkeep":
            errors.append(f"raw external data is tracked: {path}")
        if path.startswith("data/private/") or path.startswith("validation/private/"):
            errors.append(f"private local data or generated private case is tracked: {path}")
    return errors


def check_tracked_copy_suffix_docs() -> list[str]:
    tracked = subprocess.run(
        ["git", "ls-files", "docs"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    ).stdout.splitlines()
    return [
        f"tracked duplicate/copy-suffix documentation file: {path}"
        for path in find_copy_suffix_doc_paths(tracked)
        if (ROOT / path).exists()
    ]


def find_copy_suffix_doc_paths(tracked_paths: list[str]) -> list[str]:
    copy_suffix = re.compile(r"(?:^|/)[^/]+(?: copy| [0-9]+)\.md$")
    return [
        path
        for path in tracked_paths
        if copy_suffix.search(path)
    ]


def check_strict_case_schema_audit() -> list[str]:
    audit = subprocess.run(
        [sys.executable, "scripts/audit_case_schema.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode == 0:
        return []
    output = "\n".join(part for part in (audit.stdout, audit.stderr) if part).strip()
    return [f"strict YAML case schema audit failed:\n{output}"]


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
        "scarring_area_m2",
        "scarring_drag_force_n",
        "scarring_uncapped_energy_loss_j",
        "scarring_capped_energy_loss_j",
        "scarring_energy_loss_j",
        "scarring_depth_source",
        "impact_events_csv",
        "impact_events_json",
        "ensemble_trajectories_dir",
        "ensemble_impact_events_dir",
        "ensemble_impact_events_parquet",
        "contact_events_csv",
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
        "metadata_path",
        "release_zone",
        "generated_release_points_csv",
        "deterministic_grid",
        "terrain_classes",
        "class_grid_path",
        "restitution_n",
        "restitution_t",
        "friction_mu",
        "rolling_resistance",
        "hazard_layers",
        "hazard_probability",
        "sampling_weighted",
        "sampling_weight",
        "conditional_intensity_exceedance_curves",
        "pilot_gis_package",
        "pilot_gis_package_manifest_v1",
        "deterministic_local_reducer_v1",
        "hazard_reducer_chunk_manifest_v1",
        "normalization_convention",
        "conditioned_on_filter",
        "kinetic_energy_exceedance_j",
        "jump_height_exceedance_m",
        "velocity_exceedance_mps",
        "EPSG:2056",
        "LN02",
        "raw_sha256",
        "processed_sha256",
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
        ROOT / "hazard/README.md",
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


def check_hazard_layer_metadata() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "scripts/build_hazard_layers.py",
        ROOT / "hazard/README.md",
        ROOT / "hazard/results/.gitkeep",
        ROOT / "docs/hazard_layers.md",
        ROOT / "docs/performance_benchmarking.md",
        ROOT / "docs/hazard_workflow_scale_review.md",
        ROOT / "tests/test_hazard_layers.py",
        ROOT / "tests/fixtures/hazard/plane_case.yaml",
        ROOT / "tests/fixtures/hazard/ensemble_case.yaml",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing hazard-layer artifact {path.relative_to(ROOT)}")

    docs = "\n".join(
        path.read_text()
        for path in (ROOT / "README.md", ROOT / "docs/hazard_layers.md", ROOT / "hazard/README.md")
        if path.exists()
    )
    for term in (
        "reach probability",
        "deposition density",
        "maximum kinetic energy",
        "maximum jump height",
        "significant impact density",
        "risk",
        "not operational",
    ):
        if term not in docs:
            errors.append(f"hazard-layer docs omit {term!r}")
    return errors


def check_swisstopo_geodata_metadata() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return []

    errors = []
    required_paths = [
        ROOT / "docs/swisstopo_data_strategy.md",
        ROOT / "docs/swiss_terrain_ingestion_pilot.md",
        ROOT / "docs/public_real_site_geodata_preparation.md",
        ROOT / "docs/source_zone_block_scenario_policy_v1.md",
        ROOT / "docs/tschamut_swissalti3d_pilot.md",
        ROOT / "docs/swisstopo_terrain_tile_schema.yaml",
        ROOT / "data/processed/swisstopo/README.md",
        ROOT / "data/processed/swisstopo/sample_swissalti3d_tile_metadata.yaml",
        ROOT / "data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml",
        ROOT / "scripts/validate_public_real_site_geodata_manifest.py",
        ROOT / "scripts/validate_source_scenario_policy.py",
        ROOT / "scripts/prepare_tschamut_swissalti3d_pilot.py",
        ROOT / "validation/templates/public_real_site_source_scenario_policy_v1.yaml",
        ROOT / "validation/templates/tschamut_swissalti3d_baseline.yaml",
        ROOT / "validation/templates/tschamut_swissalti3d_rotational.yaml",
        ROOT / "validation/cases/swissalti3d_pilot.yaml",
        ROOT / "validation/cases/swissalti3d_release_zone_pilot.yaml",
        ROOT / "validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml",
        ROOT / "validation/cases/swissalti3d_hazard_statistics_pilot.yaml",
        ROOT / "validation/cases/performance_smoke.yaml",
        ROOT / "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc",
        ROOT / "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml",
        ROOT / "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml",
        ROOT / "validation/data/processed/swisstopo_pilot/terrain_classes.asc",
        ROOT / "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing swisstopo geodata artifact {path.relative_to(ROOT)}")

    registry = yaml.safe_load((ROOT / "data/datasets.yaml").read_text()) or {}
    datasets = {dataset.get("id"): dataset for dataset in registry.get("datasets", [])}
    required_dataset_ids = {
        "swisstopo_swissalti3d",
        "swisstopo_swisssurface3d",
        "swisstopo_swisssurface3d_raster",
        "swisstopo_swisstlm3d",
        "swisstopo_swissbuildings3d",
        "swisstopo_geocover",
        "swisstopo_geological_atlas_25k",
        "swisstopo_geomaps_500",
        "swisstopo_swissimage",
    }
    for dataset_id in sorted(required_dataset_ids):
        dataset = datasets.get(dataset_id)
        if not dataset:
            errors.append(f"data/datasets.yaml omits {dataset_id}")
            continue
        for key in ("source_url", "license", "citation", "local_path", "processed_path"):
            if not dataset.get(key):
                errors.append(f"{dataset_id} dataset metadata omits {key}")
        if dataset.get("download_status") != "metadata_only":
            errors.append(f"{dataset_id} must remain metadata_only until explicit download support exists")

    if (ROOT / "docs/swisstopo_data_strategy.md").exists():
        strategy = (ROOT / "docs/swisstopo_data_strategy.md").read_text()
        for term in (
            "swissALTI3D",
            "swissSURFACE3D",
            "swissTLM3D",
            "swissBUILDINGS3D",
            "GeoCover",
            "Geological Atlas",
            "GeoMaps 500",
            "SWISSIMAGE",
            "EPSG:2056",
            "LN02",
            "provenance",
            "hazard",
            "risk",
        ):
            if term not in strategy:
                errors.append(f"docs/swisstopo_data_strategy.md omits {term!r}")

    manifest_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_public_real_site_geodata_manifest.py",
            "data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if manifest_check.returncode != 0:
        output = "\n".join(
            part for part in (manifest_check.stdout, manifest_check.stderr) if part
        ).strip()
        errors.append(f"public real-site geodata manifest template validation failed:\n{output}")

    policy_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_source_scenario_policy.py",
            "validation/templates/public_real_site_source_scenario_policy_v1.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if policy_check.returncode != 0:
        output = "\n".join(
            part for part in (policy_check.stdout, policy_check.stderr) if part
        ).strip()
        errors.append(f"source-zone/block-scenario policy template validation failed:\n{output}")

    hazard_docs = "\n".join(
        path.read_text()
        for path in (
            ROOT / "docs/hazard_layers.md",
            ROOT / "docs/hazard_workflow_scale_review.md",
        )
        if path.exists()
    )
    for term in ("swissALTI3D", "EPSG:2056", "LN02", "provenance", "GeoTIFF", "COG"):
        if term not in hazard_docs:
            errors.append(f"hazard geodata docs omit {term!r}")

    gitignore = (ROOT / ".gitignore").read_text()
    if "data/raw/**" not in gitignore:
        errors.append(".gitignore must keep raw dataset directories ignored")
    for raw_path in (
        "data/raw/swisstopo/swissalti3d/example.tif",
        "data/raw/swisstopo/swissimage/example.tif",
    ):
        check = subprocess.run(
            ["git", "check-ignore", "-q", raw_path],
            cwd=ROOT,
            check=False,
        )
        if check.returncode != 0:
            errors.append(f"{raw_path} is not ignored by git")

    sample_path = ROOT / "data/processed/swisstopo/sample_swissalti3d_tile_metadata.yaml"
    if sample_path.exists():
        sample = yaml.safe_load(sample_path.read_text()) or {}
        crs = sample.get("coordinate_reference_system", {}) or {}
        if crs.get("epsg") != 2056:
            errors.append("sample swissALTI3D tile metadata must use EPSG:2056")
        if crs.get("vertical_datum") != "LN02":
            errors.append("sample swissALTI3D tile metadata must use LN02")
        if sample.get("source_dataset") != "swisstopo_swissalti3d":
            errors.append("sample swissALTI3D tile metadata references wrong source_dataset")
        if sample.get("source_file_present") is not False:
            errors.append("sample swissALTI3D tile metadata must remain metadata-only")
    pilot_case_path = ROOT / "validation/cases/swissalti3d_pilot.yaml"
    if pilot_case_path.exists():
        pilot_case = yaml.safe_load(pilot_case_path.read_text()) or {}
        terrain = pilot_case.get("terrain", {}) or {}
        if terrain.get("metadata_path") != "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml":
            errors.append("swissalti3d_pilot case must reference the checked-in terrain metadata sidecar")
        if terrain.get("type") not in {"ascii_dem_clamped", "esri_ascii_grid_clamped"}:
            errors.append("swissalti3d_pilot case should use clamped small DEM terrain")

    pilot_metadata_path = ROOT / "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml"
    if pilot_metadata_path.exists():
        pilot = yaml.safe_load(pilot_metadata_path.read_text()) or {}
        crs = pilot.get("coordinate_reference_system", {}) or {}
        raster = pilot.get("raster", {}) or {}
        extent = pilot.get("extent_lv95_m", {}) or {}
        if pilot.get("source_dataset") != "swisstopo_swissalti3d":
            errors.append("pilot terrain metadata references wrong source_dataset")
        if crs.get("epsg") != 2056 or crs.get("vertical_datum") != "LN02":
            errors.append("pilot terrain metadata must use EPSG:2056 and LN02")
        if raster.get("resolution_m", 0) <= 0:
            errors.append("pilot terrain metadata must have positive raster.resolution_m")
        if extent.get("xmax", 0) <= extent.get("xmin", 0) or extent.get("ymax", 0) <= extent.get("ymin", 0):
            errors.append("pilot terrain metadata must have a finite positive extent")

    release_zone_case_path = ROOT / "validation/cases/swissalti3d_release_zone_pilot.yaml"
    if release_zone_case_path.exists():
        release_case = yaml.safe_load(release_zone_case_path.read_text()) or {}
        release_zone = release_case.get("release_zone", {}) or {}
        if release_zone.get("metadata_path") != "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml":
            errors.append("swissalti3d_release_zone_pilot case must reference the checked-in release-zone metadata sidecar")
        if not release_zone.get("generated_release_points_csv"):
            errors.append("swissalti3d_release_zone_pilot should write generated release-point audit CSV")
        if release_case.get("terrain", {}).get("metadata_path") != "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml":
            errors.append("swissalti3d_release_zone_pilot must share the checked-in terrain metadata sidecar")

    release_zone_path = ROOT / "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml"
    if release_zone_path.exists():
        release_zone = yaml.safe_load(release_zone_path.read_text()) or {}
        crs = release_zone.get("coordinate_reference_system", {}) or {}
        sampling = release_zone.get("sampling", {}) or {}
        geometry = release_zone.get("geometry", {}) or {}
        if crs.get("epsg") != 2056 or crs.get("vertical_datum") != "LN02":
            errors.append("pilot release-zone metadata must use EPSG:2056 and LN02")
        if geometry.get("type") != "polygon":
            errors.append("pilot release-zone metadata must use polygon geometry")
        if sampling.get("mode") != "deterministic_grid":
            errors.append("pilot release-zone metadata must use deterministic_grid sampling")
        if sampling.get("count", 0) <= 0:
            errors.append("pilot release-zone metadata must request at least one release point")

    terrain_class_case_path = ROOT / "validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml"
    if terrain_class_case_path.exists():
        class_case = yaml.safe_load(terrain_class_case_path.read_text()) or {}
        terrain_classes = class_case.get("terrain_classes", {}) or {}
        if terrain_classes.get("metadata_path") != "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml":
            errors.append("swissalti3d terrain-class pilot must reference the checked-in terrain-class metadata sidecar")
        if class_case.get("release_zone", {}).get("metadata_path") != "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml":
            errors.append("swissalti3d terrain-class pilot must share the checked-in release-zone sidecar")

    terrain_class_metadata_path = ROOT / "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml"
    if terrain_class_metadata_path.exists():
        class_metadata = yaml.safe_load(terrain_class_metadata_path.read_text()) or {}
        crs = class_metadata.get("coordinate_reference_system", {}) or {}
        raster = class_metadata.get("raster", {}) or {}
        classes = class_metadata.get("classes", []) or []
        if crs.get("epsg") != 2056 or crs.get("vertical_datum") != "LN02":
            errors.append("pilot terrain-class metadata must use EPSG:2056 and LN02")
        if class_metadata.get("class_grid_path") != "terrain_classes.asc":
            errors.append("pilot terrain-class metadata must reference terrain_classes.asc")
        if raster.get("resolution_m", 0) <= 0:
            errors.append("pilot terrain-class metadata must have positive raster.resolution_m")
        if len(classes) < 2:
            errors.append("pilot terrain-class metadata should declare at least two classes")
        for class_entry in classes:
            if not class_entry.get("name"):
                errors.append("pilot terrain-class metadata has unnamed class")

    hazard_statistics_case_path = ROOT / "validation/cases/swissalti3d_hazard_statistics_pilot.yaml"
    if hazard_statistics_case_path.exists():
        hazard_case = yaml.safe_load(hazard_statistics_case_path.read_text()) or {}
        statistics = ((hazard_case.get("hazard_layers") or {}).get("statistics") or {})
        for key in (
            "kinetic_energy_exceedance_j",
            "jump_height_exceedance_m",
            "velocity_exceedance_mps",
        ):
            values = statistics.get(key) or []
            if not values:
                errors.append(f"swissalti3d hazard-statistics pilot omits {key}")
            elif any(value < 0 for value in values):
                errors.append(f"swissalti3d hazard-statistics pilot has negative {key}")
        outputs = hazard_case.get("outputs") or {}
        if not outputs.get("ensemble_trajectories_dir"):
            errors.append("swissalti3d hazard-statistics pilot must write ensemble_trajectories_dir")
    return errors


MISLEADING_HAZARD_CLAIM_PATTERNS: tuple[tuple[str, str], ...] = (
    ("annual frequency claim", r"\bannual(?:ized)?\s+(?:exceedance\s+)?frequenc(?:y|ies)\b"),
    ("annual probability claim", r"\bannual\s+probabilit(?:y|ies)\b"),
    ("annual unit claim", r"\b1\s*/\s*year\b|\bper\s+year\b"),
    ("return-period claim", r"\breturn[- ]period\b|\b(?:10|30|100)[- ]year\b"),
    ("risk-map claim", r"\brisk[- ]map(?:s)?\b"),
    (
        "operational hazard-map claim",
        r"\boperational(?:ly)?\s+(?:validated\s+)?hazard[- ]map(?:s)?\b",
    ),
    ("official hazard-map claim", r"\bofficial\s+hazard[- ]map(?:s)?\b"),
    ("validated hazard-map claim", r"\bvalidated\s+hazard[- ]map(?:s)?\b"),
)

INTENSITY_FREQUENCY_PATTERN = re.compile(r"\bintensity[- ]frequency\b", re.IGNORECASE)

CLAIM_HYGIENE_ALLOWLIST_TERMS = (
    "future",
    "unsupported",
    "disallowed",
    "not ",
    "no ",
    "do not",
    "does not",
    "must not",
    "without",
    "requires",
    "require ",
    "reserved",
    "later",
    "deferred",
    "schema-visible",
    "inactive",
    "excluded",
    "out of scope",
    "before",
    "only when",
    "once ",
    "explicit",
    "reject",
    "rejection",
    "deferral",
    "target",
    "until",
    "design",
    "fields",
    "physical probability",
    "documentation-only",
)

INTENSITY_FREQUENCY_ALLOWLIST_TERMS = CLAIM_HYGIENE_ALLOWLIST_TERMS + (
    "annual",
    "physical",
    "source-frequency",
    "reserve",
    "prototype",
)


def check_hazard_claim_hygiene() -> list[str]:
    """Reject unsupported hazard-product claims in user-facing text.

    The check is intentionally narrow: it allows future, unsupported, disallowed,
    and explicit boundary language, while flagging bare labels that could make a
    current product look annualized, return-period based, operational, or risk
    oriented.
    """

    paths = [
        ROOT / "README.md",
        ROOT / "hazard/README.md",
        ROOT / "docs/hazard_layers.md",
        ROOT / "docs/hazard_map_semantics.md",
        ROOT / "docs/roadmap_hazard_mapping.md",
        ROOT / "docs/validation_plan.md",
        ROOT / "docs/dataset_strategy.md",
        ROOT / "docs/real_case_intensity_frequency_implementation_roadmap.md",
        ROOT / "docs/probabilistic_scenario_model_design.md",
        ROOT / "docs/validation_maturity_framework.md",
        ROOT / "docs/pilot_gis_package.md",
    ]
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"claim-hygiene path is missing: {path.relative_to(ROOT)}")
            continue
        errors.extend(
            find_hazard_claim_hygiene_errors(
                path.read_text(),
                path.relative_to(ROOT).as_posix(),
            )
        )
    return errors


def find_hazard_claim_hygiene_errors(text: str, label: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        window = _claim_hygiene_window(lines, index)
        for claim_label, pattern in MISLEADING_HAZARD_CLAIM_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE) and not _has_claim_hygiene_allowance(
                window,
                CLAIM_HYGIENE_ALLOWLIST_TERMS,
            ):
                errors.append(
                    f"{label}:{index}: unsupported bare {claim_label}: {line.strip()}"
                )
        if INTENSITY_FREQUENCY_PATTERN.search(line) and not _has_claim_hygiene_allowance(
            window,
            INTENSITY_FREQUENCY_ALLOWLIST_TERMS,
        ):
            errors.append(
                f"{label}:{index}: intensity-frequency must be reserved for future physical/annual products: {line.strip()}"
            )
    return errors


def _claim_hygiene_window(lines: list[str], one_based_index: int) -> str:
    start = max(0, one_based_index - 6)
    end = min(len(lines), one_based_index + 4)
    return "\n".join(lines[start:end]).lower()


def _has_claim_hygiene_allowance(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


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
    if f"Rockfall v{version} Verification and Validation Report" not in report_generator:
        errors.append("visualization/build_report.py report title/header disagrees with Cargo.toml")
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
    if (case.get("parameters") or {}).get("soil_interaction_model", "none") != "none":
        errors.append("validation/cases/tschamut_basic.yaml must keep soil_interaction_model none")
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


def check_chant_sura_validation_metadata() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return []
    errors = []
    registry = yaml.safe_load((ROOT / "data/datasets.yaml").read_text()) or {}
    datasets = {dataset.get("id"): dataset for dataset in registry.get("datasets", [])}
    dataset = datasets.get("chant_sura_2020")
    if not dataset:
        errors.append("data/datasets.yaml omits chant_sura_2020 metadata")
    else:
        for key in ("source_url", "doi", "license", "citation", "local_path", "processed_path"):
            if not dataset.get(key):
                errors.append(f"chant_sura_2020 dataset metadata omits {key}")

    case_path = ROOT / "validation/cases/chant_sura_trajectory_subset.yaml"
    if not case_path.exists():
        errors.append("validation/cases/chant_sura_trajectory_subset.yaml is missing")
    else:
        case = yaml.safe_load(case_path.read_text()) or {}
        if (case.get("references") or {}).get("dataset") != "chant_sura_2020":
            errors.append("chant_sura_trajectory_subset does not reference dataset chant_sura_2020")
        observations = case.get("observations") or {}
        for key in ("release_points_csv", "trajectory_csv"):
            path = observations.get(key)
            if not path:
                errors.append(f"chant_sura_trajectory_subset omits observations.{key}")
            elif not (ROOT / path).exists():
                errors.append(
                    f"chant_sura_trajectory_subset references missing observations.{key}: {path}"
                )
        if "validation_scope" not in case:
            errors.append("chant_sura_trajectory_subset omits validation_scope")

    contact_case_path = ROOT / "validation/cases/chant_sura_contact.yaml"
    if not contact_case_path.exists():
        errors.append("validation/cases/chant_sura_contact.yaml is missing")
    else:
        case = yaml.safe_load(contact_case_path.read_text()) or {}
        if (case.get("references") or {}).get("dataset") != "chant_sura_2020":
            errors.append("chant_sura_contact does not reference dataset chant_sura_2020")
        terrain = case.get("terrain") or {}
        terrain_path = terrain.get("path")
        if not terrain_path or not (ROOT / terrain_path).exists():
            errors.append("chant_sura_contact references missing DEM fixture")
        observations = case.get("observations") or {}
        for key in ("release_points_csv", "trajectory_csv", "contact_events_csv"):
            path = observations.get(key)
            if not path:
                errors.append(f"chant_sura_contact omits observations.{key}")
            elif not (ROOT / path).exists():
                errors.append(f"chant_sura_contact references missing observations.{key}: {path}")
        metrics = (case.get("expected") or {}).get("metrics", []) or []
        for metric in (
            "impact_timing_mean_error_s",
            "rebound_velocity_mean_error_mps",
            "post_impact_energy_change_mean_error_j",
        ):
            if metric not in metrics:
                errors.append(f"chant_sura_contact omits contact metric {metric}")

    extended_case_path = ROOT / "validation/cases/chant_sura_contact_extended.yaml"
    if not extended_case_path.exists():
        errors.append("validation/cases/chant_sura_contact_extended.yaml is missing")
    else:
        case = yaml.safe_load(extended_case_path.read_text()) or {}
        if (case.get("references") or {}).get("dataset") != "chant_sura_2020":
            errors.append("chant_sura_contact_extended does not reference dataset chant_sura_2020")
        terrain = case.get("terrain") or {}
        terrain_path = terrain.get("path")
        if not terrain_path or not (ROOT / terrain_path).exists():
            errors.append("chant_sura_contact_extended references missing DEM fixture")
        observations = case.get("observations") or {}
        for key in ("release_points_csv", "trajectory_csv", "contact_events_csv"):
            path = observations.get(key)
            if not path:
                errors.append(f"chant_sura_contact_extended omits observations.{key}")
            elif not (ROOT / path).exists():
                errors.append(
                    f"chant_sura_contact_extended references missing observations.{key}: {path}"
                )
        metrics = (case.get("expected") or {}).get("metrics", []) or []
        for metric in (
            "impact_timing_mean_error_s",
            "rebound_velocity_mean_error_mps",
            "post_impact_energy_change_mean_error_j",
        ):
            if metric not in metrics:
                errors.append(f"chant_sura_contact_extended omits contact metric {metric}")
        values = (case.get("expected") or {}).get("values", {}) or {}
        if values.get("observed_contact_event_count") != 11.0:
            errors.append("chant_sura_contact_extended should declare 11 observed contact events")

    heldout_case_path = ROOT / "validation/cases/chant_sura_contact_heldout.yaml"
    if not heldout_case_path.exists():
        errors.append("validation/cases/chant_sura_contact_heldout.yaml is missing")
    else:
        case = yaml.safe_load(heldout_case_path.read_text()) or {}
        if (case.get("references") or {}).get("dataset") != "chant_sura_2020":
            errors.append("chant_sura_contact_heldout does not reference dataset chant_sura_2020")
        terrain = case.get("terrain") or {}
        terrain_path = terrain.get("path")
        if not terrain_path or not (ROOT / terrain_path).exists():
            errors.append("chant_sura_contact_heldout references missing DEM fixture")
        observations = case.get("observations") or {}
        for key in ("release_points_csv", "trajectory_csv", "contact_events_csv"):
            path = observations.get(key)
            if not path:
                errors.append(f"chant_sura_contact_heldout omits observations.{key}")
            elif not (ROOT / path).exists():
                errors.append(
                    f"chant_sura_contact_heldout references missing observations.{key}: {path}"
                )
        values = (case.get("expected") or {}).get("values", {}) or {}
        if values.get("observed_contact_event_count") != 9.0:
            errors.append("chant_sura_contact_heldout should declare 9 observed contact events")
    split_path = ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json"
    if not split_path.exists():
        errors.append("Chant Sura contact split metadata is missing")
    else:
        split = json.loads(split_path.read_text())
        selection_ids = set(split.get("model_selection_subset", {}).get("trajectory_ids", []))
        heldout_ids = set(split.get("held_out_evaluation_subset", {}).get("trajectory_ids", []))
        if not selection_ids or not heldout_ids:
            errors.append("Chant Sura contact split metadata omits selection or held-out ids")
        if selection_ids.intersection(heldout_ids):
            errors.append("Chant Sura contact split has overlapping trajectory ids")

    strategy = ROOT / "docs/dataset_strategy.md"
    if not strategy.exists():
        errors.append("docs/dataset_strategy.md is missing")
    else:
        text = strategy.read_text()
        for term in ("Chant Sura", "trajectory", "calibration", "Tschamut", "hazard"):
            if term not in text:
                errors.append(f"docs/dataset_strategy.md omits {term!r}")
    contact_doc = ROOT / "docs/chant_sura_contact_validation.md"
    if not contact_doc.exists():
        errors.append("docs/chant_sura_contact_validation.md is missing")
    else:
        text = contact_doc.read_text()
        for term in (
            "DEM-backed",
            "segment",
            "impact timing",
            "rebound velocity",
            "extended fixture",
            "held-out fixture",
        ):
            if term not in text:
                errors.append(f"docs/chant_sura_contact_validation.md omits {term!r}")
    generalization_doc = ROOT / "docs/chant_sura_contact_generalization.md"
    if not generalization_doc.exists():
        errors.append("docs/chant_sura_contact_generalization.md is missing")
    else:
        text = generalization_doc.read_text()
        for term in ("held-out", "model-selection", "sphere_rotational_v1", "translational_v0"):
            if term not in text:
                errors.append(f"docs/chant_sura_contact_generalization.md omits {term!r}")
    return errors


def check_public_benchmark_framework() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return ["PyYAML is required; install with `python3 -m pip install PyYAML`"]

    errors = []
    framework = ROOT / "docs/public_benchmark_framework.md"
    if not framework.exists():
        return ["docs/public_benchmark_framework.md is missing"]
    text = framework.read_text()
    for term in (
        "Tschamut",
        "Chant Sura",
        "EOTA221",
        "Mel de la Niva",
        "no-tuning",
        "provenance",
        "grouped",
    ):
        if term not in text:
            errors.append(f"docs/public_benchmark_framework.md omits {term!r}")

    registry = yaml.safe_load((ROOT / "data/datasets.yaml").read_text()) or {}
    dataset_ids = {dataset.get("id") for dataset in registry.get("datasets", [])}
    for dataset_id in ("tschamut2014", "chant_sura_2020", "mel_de_la_niva_2015"):
        if dataset_id not in dataset_ids:
            errors.append(f"data/datasets.yaml omits public benchmark dataset {dataset_id}")

    benchmark_dirs = (
        "tschamut",
        "chant_sura",
        "chant_sura_eota221",
        "mel_de_la_niva",
    )
    for benchmark_id in benchmark_dirs:
        readme = ROOT / "validation/benchmarks" / benchmark_id / "README.md"
        if not readme.exists():
            errors.append(f"validation/benchmarks/{benchmark_id}/README.md is missing")

    for script in (
        "scripts/prepare_tschamut_public_benchmark.py",
        "scripts/collect_tschamut_registration_sensitivity.py",
        "scripts/prepare_chant_sura_public_benchmark.py",
        "scripts/summarize_chant_sura_contact_diagnostics.py",
        "scripts/prepare_chant_sura_eota221_benchmark.py",
        "scripts/prepare_mel_de_la_niva_benchmark.py",
        "scripts/validate_public_benchmark_manifest.py",
    ):
        if not (ROOT / script).exists():
            errors.append(f"{script} is missing")

    readme = ROOT / "docs/README.md"
    if readme.exists() and "public_benchmark_framework.md" not in readme.read_text():
        errors.append("docs/README.md omits public_benchmark_framework.md")
    return errors


def check_scarring_not_in_tschamut_workflows() -> list[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return []
    errors = []
    allowed_scarring_cases = {
        "validation/cases/validation_tschamut_scarring.yaml",
    }
    for path in sorted((ROOT / "validation/cases").glob("*.yaml")):
        relative = path.relative_to(ROOT).as_posix()
        if "tschamut" not in path.name:
            continue
        data = yaml.safe_load(path.read_text()) or {}
        model = (data.get("parameters") or {}).get("soil_interaction_model", "none")
        if model != "none" and relative not in allowed_scarring_cases:
            errors.append(
                f"{path.relative_to(ROOT)} must not enable scarring without an explicit calibration/validation decision"
            )
        if relative in allowed_scarring_cases:
            scope_note = ((data.get("validation_scope") or {}).get("note") or "").lower()
            if model != "scarring_contact_v1":
                errors.append(f"{relative} must enable scarring_contact_v1")
            for term in ("exploratory", "impact-level", "not tschamut trajectory calibration"):
                if term not in scope_note:
                    errors.append(f"{relative} validation_scope.note omits {term!r}")
    for path in sorted((ROOT / "calibration/experiments").glob("tschamut_v0_3/*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        if "scarring_contact_v1" in path.read_text() or data.get("soil_interaction_model"):
            errors.append(
                f"{path.relative_to(ROOT)} must remain a v0.3.0 calibration artifact without scarring"
            )
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
        ROOT / "calibration/data/scarring_single_impact/reference_impacts.csv",
        ROOT / "calibration/experiments/scarring_single_impact_v0_4/config.yaml",
        ROOT / "calibration/experiments/scarring_single_impact_v0_4/candidate_results.csv",
        ROOT / "calibration/experiments/scarring_single_impact_v0_4/selected_parameters.yaml",
        ROOT / "calibration/experiments/scarring_single_impact_v0_4/summary.json",
        ROOT / "docs/scarring_single_impact_calibration.md",
        ROOT / "scripts/calibrate_scarring_impact.py",
        ROOT / "calibration/data/scarring_single_impact/chant_sura_esurf_2019_impacts.csv",
        ROOT / "calibration/data/scarring_single_impact/chant_sura_esurf_2019_metadata.yaml",
        ROOT / "calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/config.yaml",
        ROOT / "calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/candidate_results.csv",
        ROOT / "calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/selected_parameters.yaml",
        ROOT / "calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/summary.json",
        ROOT / "docs/scarring_real_data_calibration.md",
        ROOT / "scripts/preprocess_scarring_real_data.py",
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

    scarring_selected_path = (
        ROOT / "calibration/experiments/scarring_single_impact_v0_4/selected_parameters.yaml"
    )
    if scarring_selected_path.exists():
        selected = yaml.safe_load(scarring_selected_path.read_text()) or {}
        if selected.get("dataset_id") != "scarring_single_impact_proxy_v0_4":
            errors.append("single-impact scarring calibration selected parameters reference wrong dataset")
        if not selected.get("parameters"):
            errors.append("single-impact scarring calibration omits parameter values")

    scarring_docs = (
        ROOT / "docs/scarring_single_impact_calibration.md"
    ).read_text()
    for term in ("single-impact", "proxy", "not validation", "not operational"):
        if term not in scarring_docs:
            errors.append(f"single-impact scarring calibration docs omit {term!r}")

    real_selected_path = (
        ROOT
        / "calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/selected_parameters.yaml"
    )
    if real_selected_path.exists():
        selected = yaml.safe_load(real_selected_path.read_text()) or {}
        if selected.get("dataset_id") != "chant_sura_esurf_2019_impacts":
            errors.append("real-data scarring calibration selected parameters reference wrong dataset")
        if not selected.get("parameters"):
            errors.append("real-data scarring calibration omits parameter values")

    real_docs = (ROOT / "docs/scarring_real_data_calibration.md").read_text()
    for term in ("Chant Sura", "not validation", "inferred", "not operational"):
        if term not in real_docs:
            errors.append(f"real-data scarring calibration docs omit {term!r}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
