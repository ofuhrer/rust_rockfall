# Validation Data and Case Schema

This repository uses one YAML case schema for verification and validation. The schema is intentionally small and maps directly onto the current model: spherical block, analytic plane/paraboloid/step terrain, small ESRI ASCII DEMs including opt-in `ascii_dem_clamped` terrain patches, fixed-step integration, impact restitution, Coulomb friction, optional rotational sphere contact, opt-in stochastic contact roughness, opt-in compactable-soil scarring diagnostics, seeded release perturbations, and CSV trajectory output.

## Case YAML

Required case fields:

- `case_id`, `title`, `level`, `description`
- `terrain.type`, `terrain.parameters`, and optionally `terrain.path`
- optional `terrain.metadata_path` for Swiss/swisstopo-style terrain-source metadata sidecars
- optional `terrain_classes.metadata_path` for an aligned LV95/LN02 categorical raster metadata sidecar
- `block.mass`, `block.radius`
- `release.position`, `release.velocity`, optional `release.perturbation`
- optional `release_zone.metadata_path` for a small LV95/LN02 source-area polygon metadata sidecar
- optional `release_zone.generated_release_points_csv` for the deterministic generated release-point audit table
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
- optional `observations.release_points_csv`, `observations.deposition_points_csv`, `observations.trajectory_csv`, `observations.contact_events_csv`
- `expected.metrics`, `expected.tolerances`
- `outputs.trajectory_csv`, `outputs.diagnostics_json`, optional `outputs.manifest_json`, optional `outputs.ensemble_deposition_csv`
- optional `outputs.ensemble_trajectories_dir` for one full trajectory CSV per ensemble member; this is opt-in because it can be large
- optional `outputs.ensemble_impact_events_dir` for one impact-event CSV per ensemble member when impacts occur; this is opt-in because it can be large
- optional `outputs.impact_events_csv` and `outputs.impact_events_json` for one row/object per terrain impact
- optional `hazard_layers.statistics.kinetic_energy_exceedance_j`, `jump_height_exceedance_m`, and `velocity_exceedance_mps` for additive hazard post-processing thresholds

The machine-readable example is in `docs/benchmark_case_schema.yaml`.

## Hazard-Layer Statistics

`hazard_layers.statistics` is consumed by `scripts/build_hazard_layers.py`, not by the simulation kernel. Threshold lists are optional, finite, nonnegative values. When configured, the hazard builder writes trajectory-level exceedance probability rasters in addition to the existing reach, deposition, maximum-energy, jump-height, and impact-density layers. Existing validation pass/fail semantics are unchanged.

## Release-Zone Metadata

Swiss pilot source-area cases can opt into `release_zone.metadata_path`. This is an orchestration feature, not new physics: the simulator still runs independent spherical-block trajectories from generated starting points.

The current `schema_version: 1` release-zone metadata contract supports only small fixtures:

- `coordinate_reference_system.epsg: 2056` (`EPSG:2056`) and `vertical_datum: LN02`
- `geometry.type: polygon` with LV95 metre coordinates
- `sampling.mode: deterministic_grid`
- `sampling.count`, `sampling.seed`, `sampling.initial_velocity_mps`, optional `sampling.z_offset_m`, and `sampling.point_id_prefix`
- `source_dataset`, optional `source_url`, `license`, and `provenance.notes`

When both `terrain.metadata_path` and `release_zone.metadata_path` are present, validation checks that CRS/vertical datum match and that the release polygon lies inside the small pilot DEM footprint. Generated release points are recorded in `run_manifest_v1` and can optionally be written to `release_zone.generated_release_points_csv`.

## Terrain-Class Metadata

Swiss pilot cases can opt into `terrain_classes.metadata_path` to attach a small aligned terrain/material-class raster. This is not a new contact law. It only selects local values for existing parameters where a class override is explicitly provided; otherwise the global case parameters are used.

The current `schema_version: 1` terrain-class metadata contract supports only small fixtures:

- `coordinate_reference_system.epsg: 2056` (`EPSG:2056`) and `vertical_datum: LN02`
- `class_grid_path` pointing to an ESRI ASCII categorical raster beside the metadata file
- raster dimensions, resolution, nodata, and `extent_lv95_m` aligned with the DEM metadata
- `classes` with integer `id`, human-readable `name`, and optional `parameter_overrides`
- optional overrides: `restitution_n`, `restitution_t`, `friction_mu`, `rolling_resistance`, `soil_strength_pa`, `scarring_drag_coefficient`, `scarring_layer_density_kgpm3`, and `scarring_max_depth_m`
- `source_dataset`, optional `source_url`, `license`, and `provenance.notes`

Scarring parameter overrides only affect runs where the case already opts into `soil_interaction_model: scarring_contact_v1`; terrain classes do not enable scarring by themselves. Validation rejects unknown class IDs in the raster and rejects CRS, resolution, extent, or grid-shape mismatches against `terrain.metadata_path` when both sidecars are present. `run_manifest_v1` records the class layer id, metadata path, grid path, CRS, extent, source/license fields, provenance notes, and per-class coverage histogram.

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

For Swiss terrain-ingestion pilot cases, add `terrain.metadata_path` pointing to a YAML sidecar with CRS/provenance metadata. The current runtime parser validates the small `schema_version: 1` metadata contract:

- `source_dataset: swisstopo_swissalti3d`
- `coordinate_reference_system.epsg: 2056` (`EPSG:2056`)
- `coordinate_reference_system.vertical_datum: LN02`
- coordinate and height units in metres
- `raster.resolution_m`, `width_px`, `height_px`, and optional `nodata`
- `extent_lv95_m` footprint matching raster dimensions and resolution
- source filename, source product, license/data-origin note, preprocessing status, and provenance notes

When the terrain is an ESRI ASCII grid, validation also checks the metadata dimensions, cell size, nodata value, and LV95 footprint against the DEM header. The pilot fixture and documentation are in `validation/cases/swissalti3d_pilot.yaml` and `docs/swiss_terrain_ingestion_pilot.md`.

## Report Metrics

The CLI can report:

- `position_error_m`
- `velocity_error_mps`
- `rebound_height_error_m`
- `stopping_distance_error_m`
- `impact_time_error_s`
- `impact_count`
- `impact_event_count`
- `significant_impact_count`
- `significant_impact_min_normal_speed_mps`
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
- `validation_trajectory_count`
- `observed_trajectory_sample_count`
- `trajectory_shape_mean_error_m`
- `trajectory_shape_p95_error_m`
- `trajectory_shape_max_error_m`
- `trajectory_final_position_mean_error_m`
- `trajectory_energy_mean_relative_error`
- `trajectory_max_jump_height_mean_error_m`
- `trajectory_jump_height_envelope_error_m`
- `observed_contact_event_count`
- `contact_event_compared_count`
- `impact_timing_mean_error_s`
- `impact_timing_p95_error_s`
- `rebound_velocity_mean_error_mps`
- `rebound_velocity_p95_error_mps`
- `post_impact_energy_change_mean_error_j`
- `post_impact_energy_change_p95_error_j`
- `observed_mean_runout_m`
- `simulated_mean_runout_m`
- `deposition_centroid_error_m`
- `deposition_cloud_mean_nearest_error_m`
- `deposition_cloud_overlap_fraction`
- `release_zone_point_count`
- `release_zone_extent_area_m2`
- `release_zone_mean_runout_m`
- `release_zone_max_runout_m`
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

When `outputs.ensemble_trajectories_dir` is set, validation writes deterministic
per-trajectory CSV files named from the trajectory id. Existing representative
`outputs.trajectory_csv` behavior is unchanged. Hazard-layer reach probability,
maximum kinetic energy, and maximum jump height should use
`outputs.ensemble_trajectories_dir` when the full ensemble is needed.

When `outputs.ensemble_impact_events_dir` is set, validation writes deterministic
per-trajectory impact-event CSV files for ensemble members that produced impact
events. Hazard-layer significant-impact density should use this directory when
full-ensemble impact density is needed.

When `outputs.manifest_json` is set, verification or validation writes an
additive `run_manifest_v1` sidecar. The manifest records the case id, model
version, git hash, config fingerprint, seed policy, terrain source, output file
summaries, warnings, and completion status. It does not replace diagnostics JSON
or change pass/fail semantics. If `terrain.metadata_path` is present, the
manifest terrain section includes CRS/EPSG, vertical datum, LV95 extent,
resolution, nodata, source dataset/product, source filename/URL, license,
download/preprocessing status, and provenance notes. If `release_zone` is
present, the manifest includes release-zone id, metadata path, CRS/EPSG,
vertical datum, deterministic sampling mode and seed, requested/generated
release-point counts, polygon extent/area, source/license fields, and
provenance notes. If `terrain_classes` is present, the manifest includes
terrain-class layer id, metadata path, class-grid path, CRS/EPSG, vertical datum,
resolution, extent, nodata, source/license fields, class coverage histogram, and
provenance notes.

Impact-event CSV/JSON outputs are optional and additive. They preserve trajectory CSV compatibility while exposing one event per terrain impact. Each `ImpactEvent` contains:

- impact identity and location: `impact_index`, `time_s`, `x_m`, `y_m`, `z_m`
- terrain and effective contact normals: `terrain_normal_*`, `effective_normal_*`
- velocity snapshots: `incoming_*`, `post_contact_*`, `post_scarring_*`, and `post_step_*`
- impact geometry: `impact_angle_deg`, normal/tangential speed components for each snapshot
- translational and rotational energies before contact, after contact, after scarring, and after same-step contact motion
- scarring diagnostics: `scarring_depth_m`, `scarring_area_m2`, `scarring_drag_force_n`, `scarring_uncapped_energy_loss_j`, `scarring_capped_energy_loss_j`, `scarring_depth_source`, and `cumulative_scarring_energy_loss_j`

`scarring_depth_source` is one of `none`, `computed`, `computed_capped`, `explicit`, or `explicit_capped`.

`expected.tolerances` compare error-style metrics against maximum allowed values. `expected.minimums` and `expected.maximums` bound direct metrics such as runout, max speed, or ensemble spread.

## Impact Count Semantics

The repository deliberately distinguishes three impact-count concepts:

- `impact_event_count`: raw number of impact-event records emitted by the integrator. This is the complete contact ledger and can include very small low-energy contact chatter.
- `impact_count`: legacy trajectory-derived count of transitions from `airborne` to `impact` in trajectory samples. This remains for backward compatibility with existing cases.
- `significant_impact_count`: impact-event count filtered by incoming normal speed. In v0.5.0, an impact is significant when `incoming_normal_speed_mps >= 0.05 m/s`. This threshold is tied to the current stop-speed scale and is intended to separate physically interpretable rebound/contact events from near-rest chatter while preserving the raw event log.

Use `impact_event_count` when auditing all contact responses, `significant_impact_count` when comparing impact-level behavior, and `impact_count` only for legacy trajectory-state tests.

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

Optional fields include `vx_mps`, `vy_mps`, `vz_mps`, `speed_mps`, `kinetic_j`, angular velocity, contact-point tangential speed, rolling residual, bounce height, contact state, block mass, shape class, terrain class, forest/obstacle metadata, CRS, and preprocessing notes.

When `observations.trajectory_csv` is present, validation groups samples by
`trajectory_id`, simulates each matching release from `observations.release_points_csv`
when available, interpolates simulated samples to observed times, and reports
trajectory-shape, kinetic-energy, final-position, and proxy jump-height errors.

Observed contact-event CSV required fields:

- `event_id`
- `trajectory_id`
- `experiment_id`
- `source_segment_id`
- `next_segment_id`
- `impact_index`
- `impact_time_s`
- `x_m`
- `y_m`
- `z_m`
- `incoming_vx_mps`, `incoming_vy_mps`, `incoming_vz_mps`
- `outgoing_vx_mps`, `outgoing_vy_mps`, `outgoing_vz_mps`

Optional contact-event fields include `raw_z_m`, `incoming_speed_mps`,
`outgoing_speed_mps`, `pre_impact_kinetic_j`, `post_impact_kinetic_j`,
`mass_kg`, `radius_m`, `source_trajectory_id`,
`velocity_deflection_angle_deg`, and `event_role`. Optional trajectory/release
metadata fields such as `source_trajectory_id`, `segment_id`, `segment_index`,
`phase_label`, and `inside_dem_fraction` may be used to document segmented
validation fixtures; the current validator ignores these fields except for
human traceability. When `observations.contact_events_csv` is present,
validation simulates each `source_segment_id` from the matching release row,
uses the first significant simulated impact event, and reports impact timing,
rebound-velocity, and post-impact kinetic-energy-change errors. This is a
contact-diagnostic comparison, not a claim that segment boundaries are exact
instrumented contact measurements.
