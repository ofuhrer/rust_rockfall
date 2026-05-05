# Validation Data and Case Schema

This repository uses one YAML case schema for verification and validation. The schema is intentionally small and maps directly onto the current model: spherical block, analytic plane/paraboloid/step terrain, small ESRI ASCII DEMs, fixed-step integration, impact restitution, Coulomb friction, optional rotational sphere contact, seeded release perturbations, and CSV trajectory output.

## Case YAML

Required case fields:

- `case_id`, `title`, `level`, `description`
- `terrain.type`, `terrain.parameters`, and optionally `terrain.path`
- `block.mass`, `block.radius`
- `release.position`, `release.velocity`, optional `release.perturbation`
- `parameters.gravity`, `normal_restitution`, `tangential_restitution`, `friction_coefficient`
- optional `parameters.contact_model`: `translational_v0` by default, or `sphere_rotational_v1`
- optional `parameters.rolling_resistance_coefficient`: dimensionless, default `0.0`, used by `sphere_rotational_v1`
- `simulation.dt`, `t_max`, `max_steps`, `stop_velocity`
- `random.seed`, `ensemble_size`
- `expected.metrics`, `expected.tolerances`
- `outputs.trajectory_csv`, `outputs.diagnostics_json`

The machine-readable example is in `docs/benchmark_case_schema.yaml`.

## Implemented Terrain Types

- `plane`: `z0_m`, `slope_x`, `slope_y`
- `paraboloid`: `z0_m`, `ax`, `ay`
- `step`: `step_x_m`, `high_z_m`, `low_z_m`
- `esri_ascii_grid`: `path`

Other procedural terrains may exist in the codebase, but v0 verification cases focus on the model scope above.

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
- `ensemble_mean_runout_m`
- `ensemble_median_runout_m`
- `ensemble_p05_runout_m`
- `ensemble_p95_runout_m`
- `ensemble_runout_spread_m`
- `ensemble_p95_max_kinetic_energy_j`
- `deposition_point_error_m`
- `runout_distance_error_m`
- `lateral_deviation_m`
- `max_rolling_residual_mps`
- `final_rolling_residual_mps`
- `final_contact_tangent_speed_mps`
- `final_angular_speed_radps`

`expected.tolerances` compare error-style metrics against maximum allowed values. `expected.minimums` and `expected.maximums` bound direct metrics such as runout, max speed, or ensemble spread.

## Validation-Ready Data

Use plain CSV or GeoJSON with explicit units and coordinate metadata. Do not overwrite raw public data.

Deposition-point CSV required fields:

- `trajectory_id`
- `experiment_id`
- `x_m`
- `y_m`
- `z_m`

Observed trajectory CSV required fields:

- `trajectory_id`
- `experiment_id`
- `time_s`
- `x_m`
- `y_m`
- `z_m`

Optional fields include velocity components, angular velocity, contact-point tangential speed, rolling residual, speed, bounce height, contact state, block mass, shape class, terrain class, forest/obstacle metadata, CRS, and preprocessing notes.
