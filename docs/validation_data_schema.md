# Validation Data and Case Schema

This repository uses one YAML case schema for verification and validation. The schema is intentionally small and maps directly onto the current model: spherical block, analytic plane/paraboloid/step terrain, small ESRI ASCII DEMs including opt-in `ascii_dem_clamped` terrain patches, fixed-step integration, impact restitution, Coulomb friction, optional rotational sphere contact, opt-in stochastic contact roughness, opt-in compactable-soil scarring diagnostics, seeded release perturbations, and CSV trajectory output.

## Case YAML

Required case fields:

- `case_id`, `title`, `level`, `description`
- `terrain.type`, `terrain.parameters`, and optionally `terrain.path`
- `block.mass`, `block.radius`
- `release.position`, `release.velocity`, optional `release.perturbation`
- `parameters.gravity`, `normal_restitution`, `tangential_restitution`, `friction_coefficient`
- optional `parameters.contact_model`: `translational_v0` by default, or `sphere_rotational_v1`
- optional `parameters.rolling_resistance_coefficient`: dimensionless, default `0.0`, used by `sphere_rotational_v1`
- optional `parameters.roughness_model`: `none` by default, or `stochastic_contact_v1`
- optional `parameters.roughness_std_normal`: dimensionless dissipative normal-restitution perturbation scale, default `0.0`
- optional `parameters.roughness_std_tangent`: dimensionless dissipative tangential-restitution/friction perturbation scale, default `0.0`
- optional `parameters.roughness_std_angle`: contact-normal angular perturbation scale in radians, default `0.0`
- optional `parameters.soil_interaction_model`: `none` by default, or `scarring_contact_v1`
- optional `parameters.soil_strength_pa`: nonnegative soil-strength proxy in Pa for inferred scarring depth, default `0.0`
- optional `parameters.scarring_drag_coefficient`: nonnegative dimensionless drag coefficient, default `0.0`
- optional `parameters.scarring_layer_density_kgpm3`: nonnegative compacted-layer density in kg/m3, default `0.0`
- optional `parameters.scarring_max_depth_m`: nonnegative explicit scar-depth cap/input in m, default omitted
- `simulation.dt`, `t_max`, `max_steps`, `stop_velocity`
- `random.seed`, `ensemble_size`
- optional `validation_scope.type` and `validation_scope.note` for real-world cases
- optional `observations.release_points_csv`, `observations.deposition_points_csv`
- `expected.metrics`, `expected.tolerances`
- `outputs.trajectory_csv`, `outputs.diagnostics_json`, optional `outputs.ensemble_deposition_csv`

The machine-readable example is in `docs/benchmark_case_schema.yaml`.

## Implemented Terrain Types

- `plane`: `z0_m`, `slope_x`, `slope_y`
- `paraboloid`: `z0_m`, `ax`, `ay`
- `step`: `step_x_m`, `high_z_m`, `low_z_m`
- `v_shaped_valley`: `z0_m`, `slope_x`, `side_slope_abs_y`
- `terraced_slope`: `z0_m`, `slope_x`, `terrace_width_m`, `terrace_height_m`
- `sinusoidal_rough_slope`: `z0_m`, `slope_x`, `amplitude_m`, `wavelength_m`
- `gaussian_bump`: `z0_m`, `slope_x`, `center_x_m`, `center_y_m`, `height_m`, `sigma_m`
- `channelized_gully`: `z0_m`, `slope_x`, `depth_m`, `width_m`
- `esri_ascii_grid`: `path`
- `ascii_dem_clamped` / `esri_ascii_grid_clamped`: `path`; bilinear ESRI ASCII grid with boundary-clamped queries for limited validation patches

## Report Metrics

The CLI can report:

- `position_error_m`
- `velocity_error_mps`
- `rebound_height_error_m`
- `stopping_distance_error_m`
- `impact_time_error_s`
- `impact_count`
- `runout_m`
- `max_speed_mps`
- `max_bounce_height_m`
- `rebound_height_m`
- `total_energy_initial_j`
- `total_energy_final_j`
- `energy_error_j`
- `energy_conservation_error_j`
- `energy_monotonicity_violation_j`
- `seed_repeat_max_position_delta_m`
- `roughness_zero_baseline_max_position_delta_m`
- `different_seed_ensemble_runout_delta_m`
- `ensemble_mean_runout_m`
- `ensemble_median_runout_m`
- `ensemble_p05_runout_m`
- `ensemble_p95_runout_m`
- `ensemble_runout_spread_m`
- `ensemble_p95_max_kinetic_energy_j`
- `deposition_point_error_m`
- `runout_distance_error_m`
- `lateral_deviation_m`
- `validation_release_count`
- `validation_simulated_trajectory_count`
- `observed_mean_runout_m`
- `simulated_mean_runout_m`
- `deposition_centroid_error_m`
- `deposition_cloud_mean_nearest_error_m`
- `deposition_cloud_overlap_fraction`
- `lateral_spread_error_m`
- `max_rolling_residual_mps`
- `final_rolling_residual_mps`
- `final_contact_tangent_speed_mps`
- `final_angular_speed_radps`
- `max_scarring_depth_m`
- `max_scarring_drag_force_n`
- `total_scarring_energy_loss_j`
- `scarring_zero_baseline_max_position_delta_m`

Trajectory CSV diagnostics include `scarring_depth_m`, `scarring_drag_force_n`, and `scarring_energy_loss_j`. They are zero unless `soil_interaction_model: scarring_contact_v1` is active and an incoming impact produces a nonzero scar-depth diagnostic.

`expected.tolerances` compare error-style metrics against maximum allowed values. `expected.minimums` and `expected.maximums` bound direct metrics such as runout, max speed, or ensemble spread.

## Validation-Ready Data

Use plain CSV or GeoJSON with explicit units and coordinate metadata. Do not overwrite raw public data.

Release-point CSV required fields:

- `trajectory_id`
- `experiment_id`
- `x_m`
- `y_m`
- `z_m`

Optional release fields include `vx_mps`, `vy_mps`, `vz_mps`, `mass_kg`, and `radius_m`.
For v0 validation, `x_m`, `y_m`, and `z_m` are interpreted as block-center coordinates in meters.

Deposition-point CSV required fields:

- `trajectory_id`
- `experiment_id`
- `x_m`
- `y_m`
- `z_m`

Optional deposition fields include `release_x_m`, `release_y_m`, `release_z_m`, and `observed_runout_m`.
When these are present, validation can compare distribution-level runout and deposition-cloud metrics instead of exact trajectories.

Observed trajectory CSV required fields:

- `trajectory_id`
- `experiment_id`
- `time_s`
- `x_m`
- `y_m`
- `z_m`

Optional fields include velocity components, angular velocity, contact-point tangential speed, rolling residual, speed, bounce height, contact state, block mass, shape class, terrain class, forest/obstacle metadata, CRS, and preprocessing notes.
