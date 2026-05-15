#!/usr/bin/env python3
"""Lightweight repository consistency checks for agent-driven changes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
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
    errors.extend(check_python_tool_dependency_metadata())
    errors.extend(check_roadmap_target_authority())
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
    errors.extend(check_fallible_terrain_boundaries())
    errors.extend(check_validation_module_boundaries())
    errors.extend(check_local_parallel_ensemble_contract())
    errors.extend(check_physical_source_frequency_design_gate())
    errors.extend(check_source_frequency_evidence_contract())
    errors.extend(check_block_release_probability_evidence_contract())
    errors.extend(check_physical_frequency_reducer_preconditions())
    errors.extend(check_annual_physical_validation_calibration_review_gate())
    errors.extend(check_annual_physical_prototype_preflight())
    errors.extend(check_scalable_conditional_execution())
    errors.extend(check_scalable_conditional_target_gate())
    errors.extend(check_conditional_hazard_convergence_protocol())
    errors.extend(check_stochastic_sampling_audit())
    errors.extend(check_dem_input_conditioning_qa())
    errors.extend(check_output_budget_reducer_scaling_gate())
    errors.extend(check_balfrin_tschamut_readiness_record())
    errors.extend(check_balfrin_slurm_probe_repeatability())
    errors.extend(check_balfrin_target_gate_reproduction())
    errors.extend(check_pilot_obstacle_scope_contract())

    if errors:
        for error in errors:
            print(f"consistency error: {error}", file=sys.stderr)
        return 1
    print("repository consistency checks passed")
    return 0


def check_fallible_terrain_boundaries() -> list[str]:
    errors = []
    integrator = (ROOT / "src/integrator.rs").read_text()
    forbidden_integrator_patterns = {
        r"\.height\(": ".height(",
        r"\.normal\(": ".normal(",
        r"\.signed_distance_sphere\(": ".signed_distance_sphere(",
        r"(?<!try_)resolve_sphere_contact_with_normal\(": "resolve_sphere_contact_with_normal(",
        r"(?<!try_)resolve_rotational_sphere_contact_with_normal\(": "resolve_rotational_sphere_contact_with_normal(",
        r"(?<!try_)apply_contact_friction_after_ballistic_step\(": "apply_contact_friction_after_ballistic_step(",
        r"(?<!try_)apply_rotational_contact_motion\(": "apply_rotational_contact_motion(",
    }
    for pattern, label in forbidden_integrator_patterns.items():
        if re.search(pattern, integrator):
            errors.append(
                f"src/integrator.rs should use fallible terrain/contact APIs, found {label!r}"
            )

    dynamics = (ROOT / "src/dynamics.rs").read_text()
    required_dynamics_symbols = (
        "try_resolve_sphere_contact_with_normal",
        "try_resolve_rotational_sphere_contact_with_normal",
        "try_apply_contact_friction_after_ballistic_step",
        "try_apply_rotational_contact_motion",
    )
    for symbol in required_dynamics_symbols:
        if symbol not in dynamics:
            errors.append(f"src/dynamics.rs omits fallible contact helper {symbol}")

    tests = (ROOT / "tests/config_io_terrain.rs").read_text()
    for test_name in (
        "strict_dem_terrain_query_errors_return_simulation_errors_instead_of_panicking",
        "strict_dem_contact_response_propagates_terrain_errors_without_panicking",
    ):
        if test_name not in tests:
            errors.append(f"tests/config_io_terrain.rs omits {test_name}")
    return errors


def check_validation_module_boundaries() -> list[str]:
    errors = []
    validation = (ROOT / "src/validation.rs").read_text()
    metric_math = ROOT / "src/validation/metric_math.rs"
    metrics = ROOT / "src/validation/metrics.rs"
    probabilistic = ROOT / "src/validation/probabilistic.rs"
    validation_io = ROOT / "src/validation/validation_io.rs"
    runner = ROOT / "src/validation/runner.rs"
    types = ROOT / "src/validation/types.rs"
    if "mod metric_math;" not in validation:
        errors.append("src/validation.rs should declare the metric_math submodule")
    for submodule in (
        "mod metrics;",
        "mod probabilistic;",
        "mod validation_io;",
        "mod runner;",
        "mod types;",
    ):
        if submodule not in validation:
            errors.append(f"src/validation.rs should declare the {submodule.split()[1][:-1]} submodule")
    if not metric_math.exists():
        errors.append("src/validation/metric_math.rs is missing")
    if not metrics.exists():
        errors.append("src/validation/metrics.rs is missing")
    if not probabilistic.exists():
        errors.append("src/validation/probabilistic.rs is missing")
    if not validation_io.exists():
        errors.append("src/validation/validation_io.rs is missing")
    if not runner.exists():
        errors.append("src/validation/runner.rs is missing")
    if not types.exists():
        errors.append("src/validation/types.rs is missing")
    if errors:
        return errors

    for helper in (
        "mean",
        "percentile",
        "distance3",
        "centroid2",
        "cloud_overlap_fraction",
    ):
        if re.search(rf"\nfn {helper}\(", validation):
            errors.append(
                f"validation metric helper {helper} should live in src/validation/metric_math.rs"
            )

    required_delegations = {
        r"metrics::compute_deposition_cloud_metrics\(": "metrics delegation for deposition metrics",
        r"metrics::compute_roughness_comparison_metrics\(": "metrics delegation for roughness comparison",
        r"metrics::compute_scarring_comparison_metrics\(": "metrics delegation for scarring comparison",
        r"metrics::evaluate_failures\(": "metrics delegation for failure evaluation",
        r"probabilistic::load_probabilistic_metadata_context\(": "probabilistic metadata delegation",
        r"validation_io::load_observations\(": "validation observation I/O delegation",
        r"runner::run_case_file\(": "runner delegation for run_case_file",
        r"runner::run_case\(": "runner delegation for run_case",
        r"runner::write_report\(": "runner delegation for write_report",
    }
    for pattern, label in required_delegations.items():
        if not re.search(pattern, validation):
            errors.append(
                f"src/validation.rs should keep {label} through dedicated submodules"
            )
    return errors


def check_local_parallel_ensemble_contract() -> list[str]:
    errors = []
    simulation = (ROOT / "src/simulation.rs").read_text()
    validation = (ROOT / "src/validation.rs").read_text()
    manifest = (ROOT / "src/manifest.rs").read_text()
    lib = (ROOT / "src/lib.rs").read_text()
    tests = (ROOT / "tests/hpc_readiness.rs").read_text()
    config_tests = (ROOT / "tests/config_io_terrain.rs").read_text()
    docs = "\n".join(
        path.read_text()
        for path in (
            ROOT / "docs/model_design.md",
            ROOT / "docs/validation_data_schema.md",
            ROOT / "docs/scalability_and_data_formats_review.md",
            ROOT / "docs/task_backlog.md",
        )
    )

    for symbol in (
        "LOCAL_PARALLEL_ENSEMBLE_SCHEMA_VERSION",
        "LocalParallelEnsembleExecution",
        "simulate_ensemble_parallel",
        "simulate_ensemble_parallel_with_contact_parameters",
    ):
        if symbol not in simulation:
            errors.append(f"src/simulation.rs omits local parallel ensemble symbol {symbol}")
        if symbol not in lib:
            errors.append(f"src/lib.rs does not re-export local parallel ensemble symbol {symbol}")

    for test_name in (
        "local_parallel_ensemble_matches_serial_order_and_samples",
        "local_parallel_ensemble_is_independent_of_worker_count",
        "local_parallel_ensemble_rejects_zero_workers",
    ):
        if test_name not in tests:
            errors.append(f"tests/hpc_readiness.rs omits {test_name}")

    if '"local_threads"' not in simulation:
        errors.append("local parallel ensemble execution should record mode 'local_threads'")
    if '"requested_trajectory_index"' not in simulation:
        errors.append(
            "local parallel ensemble execution should record merge_order 'requested_trajectory_index'"
        )
    for term in (
        "ensemble_workers",
        "simulate_ensemble_parallel_with_contact_parameters",
        "ensemble_execution",
    ):
        if term not in validation:
            errors.append(f"src/validation.rs omits validation ensemble execution term {term!r}")
    if "pub ensemble_execution: Option<LocalParallelEnsembleExecution>" not in manifest:
        errors.append("run manifests should serialize optional LocalParallelEnsembleExecution")
    for term in (
        "ensemble_workers: 2",
        "local_parallel_ensemble_v1",
        "requested_trajectory_index",
    ):
        if term not in config_tests:
            errors.append(f"tests/config_io_terrain.rs omits ensemble execution assertion {term!r}")
    for term in (
        "random.ensemble_workers",
        "ensemble_execution",
        "run_manifest_v1",
        "local_parallel_ensemble_v1",
    ):
        if term not in docs:
            errors.append(f"local parallel ensemble docs omit {term!r}")
    return errors


def check_physical_source_frequency_design_gate() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/physical_source_frequency_design_gate.md",
        ROOT / "validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml",
        ROOT / "scripts/validate_physical_source_frequency_design_gate.py",
        ROOT / "tests/test_physical_source_frequency_design_gate.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                f"physical/source-frequency design gate path is missing: {path.relative_to(ROOT)}"
            )
    if errors:
        return errors

    doc = (ROOT / "docs/physical_source_frequency_design_gate.md").read_text()
    record = (ROOT / "validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_physical_source_frequency_design_gate.py").read_text()
    tests = (ROOT / "tests/test_physical_source_frequency_design_gate.py").read_text()

    for term in (
        "Decision: deferred",
        "Prototype authorization: false",
        "sampling weights",
        "overlap",
        "uncertainty",
        "calibration",
        "validation",
    ):
        if term not in doc:
            errors.append(f"docs/physical_source_frequency_design_gate.md omits {term!r}")

    for term in (
        "decision: deferred",
        "annual_physical_prototype_authorized: false",
        "source_event_rate: events_per_source_zone_per_year",
        "sampling_weight_reused_as_physical_probability",
        "missing_source_zone_overlap_policy",
        "missing_rate_uncertainty",
        "missing_calibration_validation_separation",
        "gate_reassessment:",
        "blocker_contracts:",
        "validation/templates/source_frequency_evidence_v1.yaml",
        "validation/templates/block_release_probability_evidence_v1.yaml",
        "validation/templates/physical_frequency_reducer_preconditions_v1.yaml",
        "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml",
        "design_review_fixture_reassessment:",
        "synthetic_fixtures_valid_but_not_gate_inputs",
        "design_review_fixtures:",
        "source_frequency_evidence_design_review_fixture_v1.yaml",
        "block_release_probability_evidence_design_review_fixture_v1.yaml",
        "physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml",
        "annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml",
        "runtime_authorization: not_authorized",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_design_gate_record",
        "REQUIRED_UNITS",
        "REQUIRED_REJECTION_TESTS",
        "REQUIRED_BLOCKER_CONTRACTS",
        "REQUIRED_DESIGN_REVIEW_FIXTURES",
        "validate_gate_reassessment",
        "validate_design_review_fixture_reassessment",
        "authorize_prototype is intentionally unsupported",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_physical_source_frequency_design_gate.py omits {symbol!r}")

    for test_name in (
        "test_selected_gate_record_is_valid_and_deferred",
        "test_rejects_authorized_prototype_in_current_gate",
        "test_rejects_missing_source_rate_unit",
        "test_rejects_sampling_weight_reused_as_physical_probability",
        "test_rejects_missing_overlap_policy",
        "test_rejects_missing_blocker_contract",
        "test_rejects_blocker_status_that_does_not_match_template",
        "test_rejects_design_review_fixture_status_that_does_not_match_fixture",
        "test_rejects_design_review_fixture_as_runtime_authorized",
        "test_rejects_nonblocking_inactive_contract",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_physical_source_frequency_design_gate.py omits {test_name}")
    return errors


def check_source_frequency_evidence_contract() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/source_frequency_evidence_contract.md",
        ROOT / "validation/templates/source_frequency_evidence_v1.yaml",
        ROOT / "tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml",
        ROOT / "scripts/validate_source_frequency_evidence.py",
        ROOT / "tests/test_source_frequency_evidence.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"source-frequency evidence contract path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/source_frequency_evidence_contract.md").read_text()
    template = (ROOT / "validation/templates/source_frequency_evidence_v1.yaml").read_text()
    fixture = (
        ROOT / "tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_source_frequency_evidence.py").read_text()
    tests = (ROOT / "tests/test_source_frequency_evidence.py").read_text()

    for term in (
        "Status: inactive evidence-schema contract",
        "annual frequency products",
        "no_accepted_frequency_evidence",
        "source_event_rate_per_year",
        "calibration and validation dataset overlap",
        "swisstopo",
        "source_frequency_evidence_design_review_fixture_v1.yaml",
        "not accepted evidence for Tschamut",
    ):
        if term not in doc:
            errors.append(f"docs/source_frequency_evidence_contract.md omits {term!r}")

    for term in (
        "schema_version: source_frequency_evidence_v1",
        "record_status: no_accepted_frequency_evidence",
        "prototype_authorized: false",
        "frequency_unit: events_per_source_zone_per_year",
        "source_event_rate_per_year: null",
        "annual_frequency_supported: false",
        "physical_probability_supported: false",
    ):
        if term not in template:
            errors.append(f"validation/templates/source_frequency_evidence_v1.yaml omits {term!r}")

    for term in (
        "schema_version: source_frequency_evidence_v1",
        "record_status: accepted_for_design_review",
        "prototype_authorized: false",
        "frequency_unit: events_per_source_zone_per_year",
        "source_event_rate_per_year: 0.02",
        "not accepted evidence for Tschamut",
        "annual and physical products remain deferred",
    ):
        if term not in fixture:
            errors.append(
                "tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_source_frequency_evidence",
        "source_event_rate_per_year",
        "validate_dataset_separation",
        "swisstopo geodata must not be listed as validation evidence",
        "prototype_authorized must be false",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_source_frequency_evidence.py omits {symbol!r}")

    for test_name in (
        "test_selected_template_records_no_accepted_frequency_evidence",
        "test_accepts_complete_candidate_for_design_review_only",
        "test_design_review_fixture_is_valid_but_not_runtime_authorized",
        "test_rejects_candidate_missing_source_rate",
        "test_rejects_uncertainty_that_excludes_rate",
        "test_rejects_swisstopo_as_validation_evidence",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_source_frequency_evidence.py omits {test_name}")
    return errors


def check_block_release_probability_evidence_contract() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/block_release_probability_evidence_contract.md",
        ROOT / "validation/templates/block_release_probability_evidence_v1.yaml",
        ROOT / "tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml",
        ROOT / "scripts/validate_block_release_probability_evidence.py",
        ROOT / "tests/test_block_release_probability_evidence.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                f"block/release probability evidence contract path is missing: {path.relative_to(ROOT)}"
            )
    if errors:
        return errors

    doc = (ROOT / "docs/block_release_probability_evidence_contract.md").read_text()
    template = (ROOT / "validation/templates/block_release_probability_evidence_v1.yaml").read_text()
    fixture = (
        ROOT / "tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_block_release_probability_evidence.py").read_text()
    tests = (ROOT / "tests/test_block_release_probability_evidence.py").read_text()

    for term in (
        "Status: inactive evidence-schema contract",
        "block-scenario and release-cell physical probability evidence",
        "no_accepted_block_release_probability_evidence",
        "conditional_probability_given_source_event",
        "conditional_probability_given_source_event_and_block_scenario",
        "reuse of `sampling_weight` as physical probability",
        "swisstopo",
        "block_release_probability_evidence_design_review_fixture_v1.yaml",
        "not accepted evidence for Tschamut",
    ):
        if term not in doc:
            errors.append(f"docs/block_release_probability_evidence_contract.md omits {term!r}")

    for term in (
        "schema_version: block_release_probability_evidence_v1",
        "record_status: no_accepted_block_release_probability_evidence",
        "prototype_authorized: false",
        "probability_mode: block_release_probability_evidence_only",
        "sampling_weights_are_physical_probability: false",
        "sampling_weight_column_allowed_as_probability: false",
        "physical_probability_supported: false",
    ):
        if term not in template:
            errors.append(
                f"validation/templates/block_release_probability_evidence_v1.yaml omits {term!r}"
            )

    for term in (
        "schema_version: block_release_probability_evidence_v1",
        "record_status: accepted_for_design_review",
        "prototype_authorized: false",
        "conditional_probability_given_source_event",
        "conditional_probability_given_source_event_and_block_scenario",
        "sampling_weights_are_physical_probability: false",
        "not accepted evidence for Tschamut",
        "annual and physical products remain deferred",
    ):
        if term not in fixture:
            errors.append(
                "tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_block_release_probability_evidence",
        "conditional_probability_given_source_event",
        "conditional_probability_given_source_event_and_block_scenario",
        "validate_sampling_weight_boundary",
        "swisstopo geodata must not be listed as validation evidence",
        "prototype_authorized must be false",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_block_release_probability_evidence.py omits {symbol!r}")

    for test_name in (
        "test_selected_template_records_no_accepted_block_release_probability_evidence",
        "test_accepts_complete_candidate_for_design_review_only",
        "test_design_review_fixture_is_valid_but_not_runtime_authorized",
        "test_rejects_block_probabilities_that_do_not_sum_to_one",
        "test_rejects_release_probabilities_that_do_not_sum_by_block_scenario",
        "test_rejects_sampling_weight_reuse_as_physical_probability",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_block_release_probability_evidence.py omits {test_name}")
    return errors


def check_physical_frequency_reducer_preconditions() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/physical_frequency_reducer_preconditions.md",
        ROOT / "validation/templates/physical_frequency_reducer_preconditions_v1.yaml",
        ROOT / "tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml",
        ROOT / "scripts/validate_physical_frequency_reducer_preconditions.py",
        ROOT / "tests/test_physical_frequency_reducer_preconditions.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                f"physical frequency reducer precondition path is missing: {path.relative_to(ROOT)}"
            )
    if errors:
        return errors

    doc = (ROOT / "docs/physical_frequency_reducer_preconditions.md").read_text()
    template = (ROOT / "validation/templates/physical_frequency_reducer_preconditions_v1.yaml").read_text()
    fixture = (
        ROOT / "tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_physical_frequency_reducer_preconditions.py").read_text()
    tests = (ROOT / "tests/test_physical_frequency_reducer_preconditions.py").read_text()

    for term in (
        "Status: inactive precondition contract",
        "overlap-adjusted reducer and uncertainty-propagation conditions",
        "preconditions_not_satisfied",
        "mutually_exclusive_partition",
        "documented_overlap_adjustment",
        "swisstopo",
        "physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml",
        "not an implemented reducer",
    ):
        if term not in doc:
            errors.append(f"docs/physical_frequency_reducer_preconditions.md omits {term!r}")

    for term in (
        "schema_version: physical_frequency_reducer_preconditions_v1",
        "record_status: preconditions_not_satisfied",
        "prototype_authorized: false",
        "precondition_mode: physical_frequency_reducer_preconditions_only",
        "annual_or_physical_output_supported: false",
        "source_frequency_evidence_v1",
        "block_release_probability_evidence_v1",
    ):
        if term not in template:
            errors.append(
                "validation/templates/physical_frequency_reducer_preconditions_v1.yaml "
                f"omits {term!r}"
            )

    for term in (
        "schema_version: physical_frequency_reducer_preconditions_v1",
        "record_status: accepted_for_design_review",
        "prototype_authorized: false",
        "documented_overlap_adjustment",
        "annual_or_physical_output_supported: false",
        "nested_monte_carlo_design_review_only",
        "terrain_model_form_uncertainty",
        "not an implemented overlap-adjusted reducer",
        "annual and physical products remain deferred",
    ):
        if term not in fixture:
            errors.append(
                "tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_physical_frequency_reducer_preconditions",
        "REQUIRED_UNCERTAINTY_COMPONENTS",
        "validate_overlap_policy",
        "validate_reducer_contract",
        "swisstopo geodata must not be listed as validation evidence",
        "prototype_authorized must be false",
    ):
        if symbol not in validator:
            errors.append(
                f"scripts/validate_physical_frequency_reducer_preconditions.py omits {symbol!r}"
            )

    for test_name in (
        "test_selected_template_records_unsatisfied_preconditions",
        "test_accepts_complete_candidate_for_design_review_only",
        "test_design_review_fixture_is_valid_but_not_runtime_authorized",
        "test_rejects_missing_overlap_policy",
        "test_rejects_nondeterministic_reducer_merge",
        "test_rejects_missing_uncertainty_component",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_physical_frequency_reducer_preconditions.py omits {test_name}")
    return errors


def check_annual_physical_validation_calibration_review_gate() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/annual_physical_validation_calibration_review_gate.md",
        ROOT / "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml",
        ROOT / "tests/fixtures/frequency/annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml",
        ROOT / "scripts/validate_annual_physical_validation_calibration_review_gate.py",
        ROOT / "tests/test_annual_physical_validation_calibration_review_gate.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                f"annual/physical validation-calibration review gate path is missing: {path.relative_to(ROOT)}"
            )
    if errors:
        return errors

    doc = (ROOT / "docs/annual_physical_validation_calibration_review_gate.md").read_text()
    template = (
        ROOT / "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml"
    ).read_text()
    fixture = (
        ROOT / "tests/fixtures/frequency/annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml"
    ).read_text()
    validator = (
        ROOT / "scripts/validate_annual_physical_validation_calibration_review_gate.py"
    ).read_text()
    tests = (ROOT / "tests/test_annual_physical_validation_calibration_review_gate.py").read_text()

    for term in (
        "Status: inactive review-gate contract",
        "validation/calibration review package",
        "review_not_passed",
        "no-tuning rule",
        "swisstopo terrain and context layers are treated as input geodata",
        "return-period claims",
        "annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml",
        "not accepted validation evidence",
    ):
        if term not in doc:
            errors.append(f"docs/annual_physical_validation_calibration_review_gate.md omits {term!r}")

    for term in (
        "schema_version: annual_physical_validation_calibration_review_gate_v1",
        "record_status: review_not_passed",
        "prototype_authorized: false",
        "review_mode: annual_physical_validation_calibration_review_only",
        "runtime_support_added: false",
        "swisstopo_input_geodata_is_validation_evidence: false",
        "annual_frequency_supported: false",
    ):
        if term not in template:
            errors.append(
                "validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml "
                f"omits {term!r}"
            )

    for term in (
        "schema_version: annual_physical_validation_calibration_review_gate_v1",
        "record_status: accepted_for_design_review",
        "prototype_authorized: false",
        "runtime_support_added: false",
        "source_frequency_evidence_design_review_fixture_v1.yaml",
        "block_release_probability_evidence_design_review_fixture_v1.yaml",
        "physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml",
        "maturity_target: V3",
        "current_maturity_cap: V2",
        "swisstopo_input_geodata_is_validation_evidence: false",
        "not accepted validation or calibration evidence",
    ):
        if term not in fixture:
            errors.append(
                "tests/fixtures/frequency/annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_annual_physical_validation_calibration_review_gate",
        "REQUIRED_REFERENCE_FIELDS",
        "validate_dataset_separation",
        "swisstopo geodata must not be listed as validation or holdout evidence",
        "prototype_authorized must be false",
    ):
        if symbol not in validator:
            errors.append(
                "scripts/validate_annual_physical_validation_calibration_review_gate.py "
                f"omits {symbol!r}"
            )

    for test_name in (
        "test_selected_template_records_review_not_passed",
        "test_accepts_complete_candidate_for_design_review_only",
        "test_design_review_fixture_is_valid_but_not_runtime_authorized",
        "test_rejects_missing_record_reference",
        "test_rejects_missing_no_tuning_rule",
        "test_rejects_calibration_validation_overlap",
        "test_rejects_swisstopo_as_validation_evidence",
    ):
        if test_name not in tests:
            errors.append(
                f"tests/test_annual_physical_validation_calibration_review_gate.py omits {test_name}"
            )
    return errors


def check_annual_physical_prototype_preflight() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/annual_physical_prototype_preflight.md",
        ROOT / "validation/templates/annual_physical_prototype_preflight_v1.yaml",
        ROOT / "scripts/validate_annual_physical_prototype_preflight.py",
        ROOT / "tests/test_annual_physical_prototype_preflight.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"annual/physical prototype preflight path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/annual_physical_prototype_preflight.md").read_text()
    template = (ROOT / "validation/templates/annual_physical_prototype_preflight_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_annual_physical_prototype_preflight.py").read_text()
    tests = (ROOT / "tests/test_annual_physical_prototype_preflight.py").read_text()

    for term in (
        "Status: inactive preflight contract",
        "Target 10",
        "blocked_by_design_gate",
        "runtime_support_added: false",
        "accepted source-frequency evidence",
        "accepted validation/calibration review",
        "synthetic design-review fixtures",
    ):
        if term not in doc:
            errors.append(f"docs/annual_physical_prototype_preflight.md omits {term!r}")

    for term in (
        "schema_version: annual_physical_prototype_preflight_v1",
        "record_status: blocked_by_design_gate",
        "prototype_authorized: false",
        "design_gate_record: validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml",
        "observed_design_gate_decision: deferred",
        "runtime_support_added: false",
        "implemented_uncertainty_propagation",
        "annual_frequency_supported: false",
    ):
        if term not in template:
            errors.append(f"validation/templates/annual_physical_prototype_preflight_v1.yaml omits {term!r}")

    for symbol in (
        "validate_prototype_preflight",
        "REQUIRED_REMAINING_BLOCKERS",
        "validate_design_gate_reference",
        "current preflight expects the design gate to remain deferred",
        "prototype_authorized must be false",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_annual_physical_prototype_preflight.py omits {symbol!r}")

    for test_name in (
        "test_selected_preflight_is_valid_and_blocked",
        "test_rejects_prototype_authorization",
        "test_rejects_runtime_support",
        "test_rejects_missing_remaining_blocker",
        "test_rejects_observed_gate_decision_drift",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_annual_physical_prototype_preflight.py omits {test_name}")
    return errors


def check_scalable_conditional_execution() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/tschamut_public_scalable_conditional_execution.md",
        ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml",
        ROOT / "scripts/validate_scalable_conditional_execution.py",
        ROOT / "tests/test_scalable_conditional_execution.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"scalable conditional execution path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/tschamut_public_scalable_conditional_execution.md").read_text()
    record = (
        ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_scalable_conditional_execution.py").read_text()
    tests = (ROOT / "tests/test_scalable_conditional_execution.py").read_text()
    runner = (ROOT / "scripts/build_hazard_layers.py").read_text()
    hazard_tests = (ROOT / "tests/test_hazard_layers.py").read_text()

    for term in (
        "scalable conditional execution",
        "summary-only",
        "sorted_chunk_id",
        "conditional_hazard_execution_diagnostics_v1",
        "target-scale convergence",
        "not operational",
    ):
        if term not in doc:
            errors.append(f"docs/tschamut_public_scalable_conditional_execution.md omits {term!r}")

    for term in (
        "schema_version: scalable_conditional_execution_v1",
        "decision: design_ready_not_authorized_for_scale_up",
        "runtime_support_added: true",
        "merge_order: sorted_chunk_id",
        "required_mode_for_scale_up: summary-only",
        "conditional_hazard_execution_diagnostics_v1",
        "worker_count_reducer_parity",
        "annualized: false",
        "physical_probability: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_scalable_conditional_execution",
        "REQUIRED_DIAGNOSTICS",
        "REQUIRED_OUTPUT_BUDGET_FIELDS",
        "full curve table must not be allowed for scale-up",
        "merge_order must be sorted_chunk_id",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_scalable_conditional_execution.py omits {symbol!r}")

    for term in (
        "conditional_hazard_execution_diagnostics_v1",
        "update_conditional_execution_manifest",
        "summary_only_curve_export_required_for_scale_up",
        "requires_worker_count_reducer_parity_before_scale_up",
    ):
        if term not in runner:
            errors.append(f"scripts/build_hazard_layers.py omits {term!r}")

    for test_name in (
        "test_selected_tschamut_record_is_valid_and_not_authorized_for_scale_up",
        "test_rejects_full_curve_table_for_scale_up",
        "test_rejects_nondeterministic_merge_order",
        "test_rejects_missing_convergence_diagnostic",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_scalable_conditional_execution.py omits {test_name}")

    for test_name in (
        "test_conditional_curve_summary_only_suppresses_large_curve_table",
        "test_chunked_reducer_matches_serial_outputs_and_writes_chunk_manifests",
    ):
        if test_name not in hazard_tests:
            errors.append(f"tests/test_hazard_layers.py omits {test_name}")
    return errors


def check_scalable_conditional_target_gate() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/tschamut_public_scalable_conditional_target_gate.md",
        ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        ROOT / "scripts/validate_scalable_conditional_target_gate.py",
        ROOT / "tests/test_scalable_conditional_target_gate.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"scalable conditional target gate path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/tschamut_public_scalable_conditional_target_gate.md").read_text()
    record = (
        ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_scalable_conditional_target_gate.py").read_text()
    tests = (ROOT / "tests/test_scalable_conditional_target_gate.py").read_text()

    for term in (
        "Status: executed but inconclusive",
        "`inconclusive`",
        "1,000 simulated trajectories",
        "conditional_hazard_execution_diagnostics_v1",
        "hazard_reducer_chunk_manifest_v1",
        "DT-01 Provenance And Output-Profile Closure",
        "custom_or_mixed_legacy_summary_only",
        "validation-side debug output budget",
        "1-worker vs 2-worker",
        "not change physics",
    ):
        if term not in doc:
            errors.append(f"docs/tschamut_public_scalable_conditional_target_gate.md omits {term!r}")

    for term in (
        "schema_version: scalable_conditional_target_gate_v1",
        "gate_status: inconclusive",
        "validation_runner_ensemble_workers_required: true",
        "conditional_curve_export_mode: summary-only",
        "check_status: restored_or_regenerated",
        "target_scale_executed: true",
        "convergence_diagnostics_status: inconclusive",
        "output_budget_status: recorded",
        "target_run_provenance_policy:",
        "output_profile_policy:",
        "policy_status: closed_for_current_gate",
        "may_be_interpreted_as_full_observed_release_target_provenance: false",
        "profile: custom_or_mixed_legacy_summary_only",
        "profile: scalable_conditional",
        "reduce_or_justify_validation_debug_output_volume",
        "all_compared_outputs_match: true",
        "physical_probability: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_target_gate_record",
        "REQUIRED_MISSING_ROLES",
        "REQUIRED_INCONCLUSIVE_REMAINING_STEPS",
        "validate_target_run_provenance_policy",
        "validate_output_profile_policy",
        "validate_execution_evidence",
        "conditional_curve_export_mode must be summary-only",
        "executed or inconclusive records must start target execution",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_scalable_conditional_target_gate.py omits {symbol!r}")

    for test_name in (
        "test_selected_inconclusive_executed_record_is_valid",
        "test_rejects_full_curve_export_for_target_gate",
        "test_rejects_missing_validation_runner_workers",
        "test_rejects_inconclusive_record_that_did_not_start_execution",
        "test_rejects_missing_required_path_role",
        "test_rejects_unrecorded_output_budget_after_execution",
        "test_rejects_auxiliary_ensemble_as_full_target_provenance",
        "test_rejects_missing_selected_followup_output_profile",
        "test_rejects_scale_increase_without_debug_output_budget_policy",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_scalable_conditional_target_gate.py omits {test_name}")
    return errors


def check_balfrin_tschamut_readiness_record() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/balfrin_tschamut_readiness.md",
        ROOT / "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml",
        ROOT / "scripts/validate_balfrin_tschamut_readiness_record.py",
        ROOT / "tests/test_balfrin_tschamut_readiness_record.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"balfrin readiness record path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/balfrin_tschamut_readiness.md").read_text()
    record = (ROOT / "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_balfrin_tschamut_readiness_record.py").read_text()
    tests = (ROOT / "tests/test_balfrin_tschamut_readiness_record.py").read_text()

    for term in (
        "readiness record",
        "ready_for_balfrin_target_gate",
        "does not run simulation commands",
        "does not assess annual-frequency semantics",
    ):
        if term not in doc:
            errors.append(f"docs/balfrin_tschamut_readiness.md omits {term!r}")

    for term in (
        "schema_version: balfrin_tschamut_readiness_record_v1",
        "roadmap_item: DT-02",
        "readiness_status: ready_for_balfrin_target_gate",
        "repo_root: /users/olifu/work/rust_rockfall",
        "raw_json_committed: false",
        "missing_required_count: 0",
        "processed_public_dem",
        "generated_outputs_committed: false",
        "raw_geodata_committed: false",
        "annualized: false",
        "operational_hazard_map: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_balfrin_readiness_record",
        "READY_STATUS",
        "REQUIRED_INPUT_ROLES",
        "REQUIRED_PROCESSED_ROLES",
        "REQUIRED_COMMANDS",
        "ready records must have zero blocking checks",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_balfrin_tschamut_readiness_record.py omits {symbol!r}")

    for test_name in (
        "test_selected_balfrin_readiness_record_is_valid",
        "test_rejects_ready_record_with_missing_required_input",
        "test_rejects_record_without_processed_dem_artifact",
        "test_rejects_missing_command_plan_precondition",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_balfrin_tschamut_readiness_record.py omits {test_name}")
    return errors


def check_balfrin_slurm_probe_repeatability() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml",
        ROOT / "scripts/validate_balfrin_slurm_probe_repeatability.py",
        ROOT / "tests/test_balfrin_slurm_probe_repeatability.py",
        ROOT / "docs/tschamut_public_pilot_scaling_review.md",
        ROOT / "docs/balfrin_probe_slurm_driver.md",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"balfrin SLURM probe repeatability path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    record = (ROOT / "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_balfrin_slurm_probe_repeatability.py").read_text()
    tests = (ROOT / "tests/test_balfrin_slurm_probe_repeatability.py").read_text()
    scaling_doc = (ROOT / "docs/tschamut_public_pilot_scaling_review.md").read_text()
    driver_doc = (ROOT / "docs/balfrin_probe_slurm_driver.md").read_text()

    for term in (
        "schema_version: balfrin_slurm_probe_repeatability_v1",
        "roadmap_item: DT-03",
        "classification: pass_with_scope_limits",
        "driver_decision: ready_for_same_scale_selected_gate_reproduction",
        "job_id: \"4318872\"",
        "job_id: \"4318896\"",
        "pass_hash_stable",
        "changed_artifact_count: 0",
        "slurm_arrays",
        "operational_hazard_map: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_probe_repeatability_record",
        "REQUIRED_CONTROLS",
        "REQUIRED_NOT_AUTHORIZED",
        "pass_hash_stable",
        "repeat trajectory plan ids must be stable",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_balfrin_slurm_probe_repeatability.py omits {symbol!r}")

    for test_name in (
        "test_selected_slurm_probe_repeatability_record_is_valid",
        "test_rejects_repeat_without_reused_trajectory_chunks",
        "test_rejects_plan_id_drift_between_repeat_runs",
        "test_rejects_changed_numeric_artifacts",
        "test_rejects_scale_up_authorization",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_balfrin_slurm_probe_repeatability.py omits {test_name}")

    for term in (
        "DT-03 repeat/reuse closure",
        "4318872",
        "4318896",
        "33/33 numeric hazard artifacts",
        "ready_for_same_scale_selected_gate_reproduction",
    ):
        if term not in scaling_doc:
            errors.append(f"docs/tschamut_public_pilot_scaling_review.md omits {term!r}")

    for term in (
        "DT-03 repeat/reuse closure",
        "pass_with_scope_limits",
        "single-job SLURM driver",
        "same-scale selected-gate reproduction",
    ):
        if term not in driver_doc:
            errors.append(f"docs/balfrin_probe_slurm_driver.md omits {term!r}")
    return errors


def check_balfrin_target_gate_reproduction() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        ROOT / "scripts/validate_balfrin_target_gate_reproduction.py",
        ROOT / "tests/test_balfrin_target_gate_reproduction.py",
        ROOT / "docs/tschamut_public_scalable_conditional_target_gate.md",
        ROOT / "docs/task_backlog.md",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"balfrin target-gate reproduction path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    record = (ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_balfrin_target_gate_reproduction.py").read_text()
    tests = (ROOT / "tests/test_balfrin_target_gate_reproduction.py").read_text()
    target_doc = (ROOT / "docs/tschamut_public_scalable_conditional_target_gate.md").read_text()
    backlog = (ROOT / "docs/task_backlog.md").read_text()

    for term in (
        "schema_version: balfrin_target_gate_reproduction_v1",
        "roadmap_item: DT-04",
        "execution_status: completed",
        "reproducibility_classification: inconclusive",
        "job_id: \"4318941\"",
        "validation_simulated_trajectory_count: 1000.0",
        "conditional_curve_export: summary-only",
        "conditional_curve_csv_written: false",
        "grid_csv_export: none",
        "grid_csv_written: false",
        "pass_clean",
        "operational_hazard_map: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_target_gate_reproduction_record",
        "REQUIRED_CHECKSUMS",
        "current DT-04 record must remain inconclusive",
        "conditional_curve_export must be summary-only",
        "simulated_trajectory_count must be 1000",
        "log audit warning count must be zero",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_balfrin_target_gate_reproduction.py omits {symbol!r}")

    for test_name in (
        "test_selected_balfrin_target_gate_reproduction_record_is_valid",
        "test_rejects_non_target_trajectory_count",
        "test_rejects_full_conditional_curve_csv",
        "test_rejects_missing_checksum",
        "test_rejects_dirty_log_audit",
        "test_rejects_scale_up_classification",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_balfrin_target_gate_reproduction.py omits {test_name}")

    for term in (
        "DT-04 Balfrin Reproduction",
        "4318941",
        "1000",
        "inconclusive",
        "summary-only",
        "not operational validation",
        "DT-05 Convergence Acceptance Assessment",
        "conditional_convergence_protocol_v1",
    ):
        if term not in target_doc:
            errors.append(f"docs/tschamut_public_scalable_conditional_target_gate.md omits {term!r}")

    for term in (
        "Status: authoritative executable task backlog.",
        "Balfrin target-gate reproduction",
        "The selected Tschamut target-scale evidence remains `inconclusive`.",
        "selected-domain runs remain blocked",
    ):
        if term not in backlog:
            errors.append(f"docs/task_backlog.md omits {term!r}")
    return errors


def check_conditional_hazard_convergence_protocol() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/conditional_hazard_convergence_acceptance_protocol.md",
        ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
        ROOT / "scripts/validate_conditional_convergence_protocol.py",
        ROOT / "tests/test_conditional_convergence_protocol.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                f"conditional hazard convergence protocol path is missing: {path.relative_to(ROOT)}"
            )
    if errors:
        return errors

    doc = (ROOT / "docs/conditional_hazard_convergence_acceptance_protocol.md").read_text()
    record = (
        ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
    ).read_text()
    validator = (ROOT / "scripts/validate_conditional_convergence_protocol.py").read_text()
    tests = (ROOT / "tests/test_conditional_convergence_protocol.py").read_text()

    for term in (
        "conditional hazard-map products only",
        "pass",
        "inconclusive",
        "no_go",
        "no annual/physical frequency",
        "no return periods",
        "secondary interoperability evidence",
        "current DT-04 Balfrin evidence is assessed as `inconclusive`",
    ):
        if term not in doc:
            errors.append(f"docs/conditional_hazard_convergence_acceptance_protocol.md omits {term!r}")

    for term in (
        "schema_version: conditional_hazard_convergence_protocol_v1",
        "roadmap_item: DT-05",
        "protocol_status: applied_to_dt04_evidence",
        "current_classification: inconclusive",
        "scale_up_authorized: false",
        "dt04_balfrin_reproduction_record: validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        "dt04_target_gate_record: validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        "target_run_provenance:",
        "input_freeze:",
        "trajectory_and_release_counts:",
        "deterministic_seed_order_chunk_metadata:",
        "reducer_parity_or_repeatability:",
        "output_profile:",
        "output_budget:",
        "checksum_provenance:",
        "log_audit:",
        "convergence_indicators:",
        "known_interpretation_blockers:",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_protocol_record",
        "REQUIRED_EVIDENCE_CATEGORIES",
        "PROHIBITED_CLAIM_PATTERNS",
        "current_classification is invalid",
        "scale_up_authorized must be boolean",
        "pass records require every gate to pass",
        "conditional convergence protocol record is valid",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_conditional_convergence_protocol.py omits {symbol!r}")

    for test_name in (
        "test_selected_protocol_record_is_valid",
        "test_rejects_missing_dt04_evidence",
        "test_rejects_missing_convergence_evidence",
        "test_rejects_operational_annual_and_risk_claims",
        "test_rejects_scale_up_authorization_without_passed_gates",
        "test_rejects_unsupported_classification_values",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_conditional_convergence_protocol.py omits {test_name}")
    return errors


def check_stochastic_sampling_audit() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/stochastic_sampling_rng_stream_audit.md",
        ROOT / "validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml",
        ROOT / "scripts/validate_stochastic_sampling_audit.py",
        ROOT / "tests/test_stochastic_sampling_audit.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"stochastic sampling audit path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/stochastic_sampling_rng_stream_audit.md").read_text()
    record = (ROOT / "validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_stochastic_sampling_audit.py").read_text()
    tests = (ROOT / "tests/test_stochastic_sampling_audit.py").read_text()

    for term in (
        "Status: DT-06 audit package",
        "no-behavior-change boundary",
        "stream-separation",
        "release perturbation",
        "roughness/contact",
        "sampling_weighted_conditional",
        "not statistically validated",
        "Tschamut pilot",
    ):
        if term not in doc:
            errors.append(f"docs/stochastic_sampling_rng_stream_audit.md omits {term!r}")

    for term in (
        "schema_version: stochastic_sampling_audit_v1",
        "roadmap_item: DT-06",
        "current_classification: diagnostic_incomplete",
        "stochastic_validity_accepted: false",
        "scale_up_authorized: false",
        "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
        "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        "stream_separation_assessment",
        "distribution_truncation_support",
        "weighted_uncertainty_assessment",
        "physics_changes_claimed: false",
        "rng_changes_claimed: false",
        "stochastic_default_changes_claimed: false",
        "annual_or_physical_probability_claimed: false",
        "risk_exposure_or_operational_claimed: false",
        "accepted_stochastic_validity_claimed: false",
        "scale_up_authorized: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_stochastic_sampling_audit",
        "REQUIRED_CODE_PATHS",
        "REQUIRED_DOC_PATHS",
        "REQUIRED_RECORD_PATHS",
        "REQUIRED_STREAM_AXES",
        "REQUIRED_FAMILIES",
        "REQUIRED_BLOCKERS",
        "REQUIRED_NON_BLOCKERS",
        "validate_stream_separation_assessment",
        "validate_distribution_truncation_support",
        "validate_claim_boundary",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_stochastic_sampling_audit.py omits {symbol!r}")

    for test_name in (
        "test_current_record_is_valid",
        "test_rejects_missing_stream_separation_assessment",
        "test_rejects_missing_distribution_truncation_assessment",
        "test_rejects_stochastic_validity_acceptance",
        "test_rejects_rng_default_or_physics_change_claims",
        "test_rejects_annual_physical_risk_operational_claims",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_stochastic_sampling_audit.py omits {test_name}")
    return errors


def check_dem_input_conditioning_qa() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/real_site_dem_input_conditioning_qa_gate.md",
        ROOT / "validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml",
        ROOT / "scripts/validate_dem_input_conditioning_qa.py",
        ROOT / "tests/test_dem_input_conditioning_qa.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"dem input conditioning QA path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/real_site_dem_input_conditioning_qa_gate.md").read_text()
    record = (ROOT / "validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_dem_input_conditioning_qa.py").read_text()
    tests = (ROOT / "tests/test_dem_input_conditioning_qa.py").read_text()

    for term in (
        "fail-closed QA gate",
        "raw public inputs",
        "atomic ingest",
        "CRS/registration",
        "nodata",
        "strict versus clamped DEM interpretation",
        "domain-exit / terrain-error interpretation",
        "no-tuning/no-operational/no-annual boundary",
    ):
        if term not in doc:
            errors.append(f"docs/real_site_dem_input_conditioning_qa_gate.md omits {term!r}")

    for term in (
        "schema_version: dem_input_conditioning_qa_v1",
        "roadmap_item: DT-07",
        "pilot_id: tschamut_public_pilot",
        "current_classification: blocked_pending_local_evidence",
        "qa_status: diagnostic_incomplete",
        "raw_input_evidence:",
        "atomic_ingest_and_checksum:",
        "crs_and_registration_evidence:",
        "nodata_policy:",
        "terrain_sanity_checks:",
        "boundary_and_terrain_error_semantics:",
        "claim_boundary:",
        "stochastic_or_physics_change_claimed: false",
        "dem_behavior_change_claimed: false",
        "tuning_claimed: false",
        "operational_or_annual_claimed: false",
        "physics_changes_claimed: false",
        "dem_behavior_changes_claimed: false",
        "annual_or_physical_probability_claimed: false",
        "risk_exposure_or_operational_claimed: false",
        "validated_hazard_map_claimed: false",
        "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
        "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        "docs/public_real_site_geodata_preparation.md",
        "docs/swiss_terrain_ingestion_pilot.md",
        "docs/dem_terrain_sensitivity_benchmark.md",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_dem_input_conditioning_qa",
        "ALLOWED_CLASSIFICATIONS",
        "REQUIRED_REFERENCES",
        "REQUIRED_BLOCKERS",
        "PROHIBITED_PATTERNS",
        "validate_claim_boundary",
        "scan_text_for_prohibited_claims",
        "DEM/input QA record is valid",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_dem_input_conditioning_qa.py omits {symbol!r}")

    for test_name in (
        "test_current_record_is_valid",
        "test_rejects_missing_raw_input_evidence",
        "test_rejects_missing_crs_registration_evidence",
        "test_rejects_passed_while_blockers_remain",
        "test_rejects_dem_behavior_or_physics_claims",
        "test_rejects_annual_physical_risk_operational_claims",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_dem_input_conditioning_qa.py omits {test_name}")
    return errors


def check_output_budget_reducer_scaling_gate() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/output_budget_reducer_scaling_gate.md",
        ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml",
        ROOT / "scripts/validate_output_budget_reducer_gate.py",
        ROOT / "tests/test_output_budget_reducer_gate.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"output/reducer scaling gate path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/output_budget_reducer_scaling_gate.md").read_text()
    record = (ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_output_budget_reducer_gate.py").read_text()
    tests = (ROOT / "tests/test_output_budget_reducer_gate.py").read_text()

    for term in (
        "fail-closed gate",
        "output file-count budget",
        "byte-count budget",
        "inode/file-family budget",
        "summary-only conditional curves",
        "grid CSV suppression",
        "reducer state-size and dense-grid accumulator risk classification",
        "reducer chunk/restart manifest requirements",
        "checksum and hash requirements",
        "local single-job",
        "future distributed execution",
        "no-tuning/no-physics/no-output-default-change/no-operational boundary",
    ):
        if term not in doc:
            errors.append(f"docs/output_budget_reducer_scaling_gate.md omits {term!r}")

    for term in (
        "schema_version: output_budget_reducer_gate_v1",
        "roadmap_item: DT-08",
        "current_classification: blocked_before_scale_up",
        "qa_status: diagnostic_incomplete",
        "scale_up_authorized: false",
        "selected_dt04_output_evidence:",
        "referenced_records:",
        "validation_output_budget:",
        "hazard_output_budget:",
        "inode_and_file_family_budget:",
        "reducer_scaling:",
        "dense_grid_risk:",
        "checksum_evidence:",
        "claim_boundary:",
        "physics_changes_claimed: false",
        "reducer_behavior_changes_claimed: false",
        "output_default_changes_claimed: false",
        "ensemble_size_increase_claimed: false",
        "distributed_execution_claimed: false",
        "annual_or_physical_claimed: false",
        "risk_exposure_or_operational_claimed: false",
        "full_curve_csv_default_claimed: false",
        "grid_csv_default_claimed: false",
        "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
        "docs/tschamut_public_pilot_scaling_review.md",
        "docs/conditional_hazard_convergence_acceptance_protocol.md",
        "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
        "required_future_evidence:",
        "limitations:",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "validate_output_budget_reducer_gate",
        "ALLOWED_CLASSIFICATIONS",
        "REQUIRED_REFERENCES",
        "REQUIRED_BLOCKERS",
        "REQUIRED_FOLLOWUP_CONTROLS",
        "validate_budget_block",
        "validate_claim_boundary",
        "scan_text_for_prohibited_claims",
        "output/reducer gate record is valid",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_output_budget_reducer_gate.py omits {symbol!r}")

    for test_name in (
        "test_current_record_is_valid",
        "test_rejects_missing_validation_output_budget",
        "test_rejects_missing_hazard_output_budget",
        "test_rejects_missing_reducer_evidence",
        "test_rejects_passed_while_blockers_remain",
        "test_rejects_scale_up_authorization_while_blockers_remain",
        "test_rejects_scalable_output_default_claims",
        "test_rejects_physics_reducer_behavior_and_output_default_change_claims",
        "test_rejects_annual_physical_risk_operational_claims",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_output_budget_reducer_gate.py omits {test_name}")
    return errors


def check_pilot_obstacle_scope_contract() -> list[str]:
    errors = []
    required_paths = [
        ROOT / "docs/tschamut_public_obstacle_context_scope.md",
        ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
        ROOT / "scripts/validate_pilot_obstacle_scope.py",
        ROOT / "tests/test_pilot_obstacle_scope.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"pilot obstacle-scope path is missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    doc = (ROOT / "docs/tschamut_public_obstacle_context_scope.md").read_text()
    record = (ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml").read_text()
    validator = (ROOT / "scripts/validate_pilot_obstacle_scope.py").read_text()
    tests = (ROOT / "tests/test_pilot_obstacle_scope.py").read_text()

    for term in (
        "target-scale interpretation review",
        "blocked_missing_context_layers",
        "blocked_pending_local_evidence",
        "does not add obstacle physics",
        "research_diagnostic",
        "inspect_tschamut_public_context_layers.py",
    ):
        if term not in doc:
            errors.append(f"docs/tschamut_public_obstacle_context_scope.md omits {term!r}")

    for term in (
        "run_id: tschamut_public_scalable_conditional_target_gate_v1",
        "classification: blocked_pending_local_evidence",
        "target_scale_review:",
        "target_gate_status: inconclusive",
        "target_package_visual_qa_status: blocked",
        "local_context_review_status: blocked_missing_context_layers",
        "context_artifacts_committed: false",
        "context_downloads_or_crops_present_in_checkout: false",
        "forest_or_canopy",
        "buildings_or_structures",
        "roads_or_transport",
        "barriers_or_protection",
        "water_or_channel",
        "orthophoto_visual_context",
        "swissimage",
        "swisstlm3d",
        "swisssurface3d_raster",
        "swissbuildings3d",
        "obstacle_physics_implemented: false",
        "annualized: false",
        "physical_probability: false",
    ):
        if term not in record:
            errors.append(
                "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml "
                f"omits {term!r}"
            )

    for symbol in (
        "TARGET_REVIEW_STATUSES",
        "validate_target_scale_review",
        "validate_local_artifact_probe",
        "target_scale_context_review_status",
        "missing_context_artifact_count",
    ):
        if symbol not in validator:
            errors.append(f"scripts/validate_pilot_obstacle_scope.py omits {symbol!r}")

    for test_name in (
        "test_selected_target_scope_is_blocked_pending_local_evidence_with_blocked_context_review",
        "test_rejects_blocked_context_review_with_reviewed_artifacts",
        "test_accepts_blocked_scope_with_future_context_actions",
        "test_rejects_blocked_scope_without_future_actions",
        "test_rejects_acceptable_classification_without_reviewed_target_context",
    ):
        if test_name not in tests:
            errors.append(f"tests/test_pilot_obstacle_scope.py omits {test_name}")

    for path in (
        ROOT / "scripts/inspect_tschamut_public_context_layers.py",
        ROOT / "tests/test_tschamut_public_context_layers.py",
    ):
        if not path.exists():
            errors.append(f"pilot obstacle-scope inspection path is missing: {path.relative_to(ROOT)}")
    return errors


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


def check_python_tool_dependency_metadata() -> list[str]:
    errors: list[str] = []
    pyproject_path = ROOT / "pyproject.toml"
    requirements_path = ROOT / "requirements-tools.txt"
    if not pyproject_path.exists():
        return ["missing pyproject.toml for uv-run Python tool dependencies"]
    if not requirements_path.exists():
        return ["missing requirements-tools.txt for CI Python tool dependencies"]

    pyproject = tomllib.loads(pyproject_path.read_text())
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        errors.append("pyproject.toml project.dependencies must be a list")
        dependencies = []
    pyproject_packages = {_requirement_name(str(value)) for value in dependencies}
    requirement_packages = {
        _requirement_name(line)
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    if pyproject_packages != requirement_packages:
        errors.append(
            "pyproject.toml dependencies must match requirements-tools.txt "
            f"(pyproject={sorted(pyproject_packages)}, requirements={sorted(requirement_packages)})"
        )
    if pyproject.get("tool", {}).get("uv", {}).get("package") is not False:
        errors.append("pyproject.toml should set tool.uv.package = false for repository tools")
    return errors


def _requirement_name(requirement: str) -> str:
    name = re.split(r"[<>=!~;\\[]", requirement.strip(), maxsplit=1)[0].strip()
    return name.lower().replace("_", "-")


def check_roadmap_target_authority() -> list[str]:
    errors: list[str] = []
    backlog = ROOT / "docs/task_backlog.md"
    legacy_targets = ROOT / "docs/next_development_targets.md"
    matrix = ROOT / "docs/roadmap_recommendation_matrix.md"
    long_term = ROOT / "docs/real_case_intensity_frequency_implementation_roadmap.md"

    expected_marker = "Status: authoritative executable task backlog."
    backlog_text = backlog.read_text()
    if expected_marker not in backlog_text:
        errors.append("docs/task_backlog.md must contain the authoritative executable task backlog marker")
    for term in (
        "Worker rule:",
        "Project Objective",
        "Capability Gap Analysis",
        "Backlog Quality Assessment",
        "decision_log.md",
        "agent_work_log.md",
    ):
        if term not in backlog_text:
            errors.append(f"docs/task_backlog.md omits {term!r}")

    legacy_text = legacy_targets.read_text()
    if "Status: legacy pointer." not in legacy_text or "Current executable tasks have moved to `task_backlog.md`." not in legacy_text:
        errors.append("docs/next_development_targets.md must remain a legacy pointer to task_backlog.md")

    support_marker = "not authoritative for current target selection"
    for path in (matrix, long_term):
        if support_marker not in path.read_text():
            errors.append(
                f"{path.relative_to(ROOT)} must state it is not authoritative for current target selection"
            )

    docs_to_scan = [
        path
        for path in sorted((ROOT / "docs").glob("*.md"))
        if path.name
        in {
            "task_backlog.md",
            "next_development_targets.md",
            "roadmap_recommendation_matrix.md",
            "real_case_intensity_frequency_implementation_roadmap.md",
        }
    ]
    for path in docs_to_scan:
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if re.match(r"^## Target \d+:", line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number} uses active-looking '## Target N:' heading; use TB-xxx in task_backlog.md"
                )
    return errors


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
        ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
        ROOT / "scripts/validate_public_real_site_geodata_manifest.py",
        ROOT / "scripts/validate_source_scenario_policy.py",
        ROOT / "scripts/prepare_tschamut_public_benchmark.py",
        ROOT / "scripts/prepare_tschamut_swissalti3d_pilot.py",
        ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
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

    selected_manifest_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_public_real_site_geodata_manifest.py",
            "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if selected_manifest_check.returncode != 0:
        output = "\n".join(
            part
            for part in (selected_manifest_check.stdout, selected_manifest_check.stderr)
            if part
        ).strip()
        errors.append(f"selected public real-site geodata manifest validation failed:\n{output}")

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

    selected_policy_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_source_scenario_policy.py",
            "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if selected_policy_check.returncode != 0:
        output = "\n".join(
            part
            for part in (selected_policy_check.stdout, selected_policy_check.stderr)
            if part
        ).strip()
        errors.append(f"selected source-zone/block-scenario policy validation failed:\n{output}")

    pilot_run_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_public_real_site_conditional_pilot_run.py",
            "validation/templates/public_real_site_conditional_pilot_run_v1.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if pilot_run_check.returncode != 0:
        output = "\n".join(
            part for part in (pilot_run_check.stdout, pilot_run_check.stderr) if part
        ).strip()
        errors.append(f"public real-site conditional pilot run template validation failed:\n{output}")

    selected_pilot_run_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_public_real_site_conditional_pilot_run.py",
            "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if selected_pilot_run_check.returncode != 0:
        output = "\n".join(
            part
            for part in (selected_pilot_run_check.stdout, selected_pilot_run_check.stderr)
            if part
        ).strip()
        errors.append(f"selected public real-site conditional pilot run validation failed:\n{output}")

    selected_ensemble_feasibility_check = subprocess.run(
        [
            sys.executable,
            "scripts/validate_pilot_ensemble_feasibility.py",
            "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if selected_ensemble_feasibility_check.returncode != 0:
        output = "\n".join(
            part
            for part in (
                selected_ensemble_feasibility_check.stdout,
                selected_ensemble_feasibility_check.stderr,
            )
            if part
        ).strip()
        errors.append(f"selected pilot ensemble feasibility validation failed:\n{output}")

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
        ROOT / "docs/stochastic_sampling_rng_stream_audit.md",
        ROOT / "docs/conditional_hazard_convergence_acceptance_protocol.md",
        ROOT / "docs/roadmap_hazard_mapping.md",
        ROOT / "docs/validation_plan.md",
        ROOT / "docs/dataset_strategy.md",
        ROOT / "docs/real_case_intensity_frequency_implementation_roadmap.md",
        ROOT / "docs/probabilistic_scenario_model_design.md",
        ROOT / "docs/physical_source_frequency_design_gate.md",
        ROOT / "docs/source_frequency_evidence_contract.md",
        ROOT / "docs/block_release_probability_evidence_contract.md",
        ROOT / "docs/physical_frequency_reducer_preconditions.md",
        ROOT / "docs/annual_physical_validation_calibration_review_gate.md",
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
