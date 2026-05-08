# Validation Data and Case Schema

This repository uses one YAML case schema for verification and validation. The schema is intentionally small and maps directly onto the current model: spherical block, analytic plane/paraboloid/step terrain, small ESRI ASCII DEMs including opt-in `ascii_dem_clamped` terrain patches, fixed-step integration, impact restitution, Coulomb friction, optional rotational sphere contact, opt-in stochastic contact roughness, opt-in compactable-soil scarring diagnostics, seeded release perturbations, and CSV trajectory output.

## Case YAML

Required case fields:

- `schema_version: benchmark_case_v1`
- `case_id`, `title`, `level`, `description`
- `terrain.type`, `terrain.parameters`, and optionally `terrain.path`
- optional `terrain.metadata_path` for Swiss/swisstopo-style terrain-source metadata sidecars
- optional `terrain_classes.metadata_path` for an aligned LV95/LN02 categorical raster metadata sidecar
- `block.mass`, `block.radius`
- optional `block_shape.metadata_path` for passive `shape_metadata_v1` block-shape sidecars
- `release.position`, `release.velocity`, optional `release.perturbation`
- optional `release_zone.metadata_path` for a small LV95/LN02 source-area polygon metadata sidecar
- optional `release_zone.generated_release_points_csv` for the deterministic generated release-point audit table
- `parameters.gravity`, `normal_restitution`, `tangential_restitution`, `friction_coefficient`
- optional `parameters.contact_model`: `translational_v0` by default,
  `sphere_rotational_v1`, or the experimental verification scaffold
  `shape_contact_v0`
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
- `outputs.trajectory_csv`, `outputs.diagnostics_json`, optional `outputs.manifest_json`, optional `outputs.trajectory_metadata_csv`, optional `outputs.ensemble_deposition_csv`
- optional `outputs.ensemble_trajectories_dir` for one full trajectory CSV per ensemble member; this is opt-in because it can be large
- optional `outputs.ensemble_impact_events_dir` for one impact-event CSV per ensemble member when impacts occur; this is opt-in because it can be large
- optional `outputs.ensemble_impact_events_parquet` for one batched `impact_events_table_v1` Parquet file containing all ensemble impact events; this is opt-in and can be written alongside or instead of the CSV directory
- optional `outputs.impact_events_csv` and `outputs.impact_events_json` for one row/object per terrain impact
- optional `hazard_layers.statistics.kinetic_energy_exceedance_j`, `jump_height_exceedance_m`, and `velocity_exceedance_mps` for additive hazard post-processing thresholds
- optional top-level `hazard_probability` block for opt-in sampling-weighted conditional hazard-layer post-processing
- optional top-level `hazard_map_package` block for labelled Phase 1 map-package metadata

The machine-readable example is in `docs/benchmark_case_schema.yaml`.

`scripts/audit_case_schema.py` provides the strict migration audit path. It
requires `schema_version: benchmark_case_v1` for checked-in validation and
verification cases and reports unknown keys, but runtime case loading remains
legacy-compatible for now.

`cargo run -- validate` keeps the legacy tab-separated output by default. Use
`--json-lines` with `verify`, `validate`, or `benchmark` for opt-in detailed
case-status records containing `completion_status`, `execution_status`,
`scientific_status`, warnings, failures, and metrics.

Restitution coefficients must be finite values in `[0, 1]`. Values above
`1.0` are rejected instead of being silently clamped by the contact solver,
so reported case parameters match the active physics. Friction and the
optional rolling-resistance coefficient must be finite and nonnegative.

ESRI ASCII DEMs use the standard GIS convention: `xllcorner` and `yllcorner`
are the outer lower-left cell corner, raster values are samples at cell
centers, and `extent_lv95_m` describes the full outer raster footprint. Strict
`ascii_dem` interpolation accepts cell-center-domain queries; the opt-in
`ascii_dem_clamped` variant clamps out-of-domain queries to the nearest cell
center before interpolating.

If `t_max` and `max_steps` are both supplied, the runner uses the shorter
horizon: `min(t_max, max_steps * dt)`. YAML case defaults are intentionally
small for smoke tests (`dt = 0.01 s`, `t_max = 1.0 s`, and
`stop_velocity = 0.10 m/s`, matching the JSON `SimulationConfig` stop-speed
default), but versioned verification and validation cases should continue to
set these fields explicitly.

## Stop-State Terrain/Material Diagnostics

`run_manifest_v1` and ensemble `*_stop_state.csv` sidecars can carry additive
terrain/material stopping context when a case configures
`terrain_classes.metadata_path`.

The fields are diagnostic only:

- `terrain_material_context_available`;
- `final_terrain_class_id`, `final_terrain_class_name`, and
  `final_terrain_class_source`;
- `last_significant_impact_terrain_class_id`,
  `last_significant_impact_terrain_class_name`, and
  `last_significant_impact_terrain_class_source`;
- `significant_impact_terrain_class_counts`;
- `significant_impact_terrain_class_sequence_head`;
- `significant_impact_terrain_class_sequence_tail`;
- `significant_impact_terrain_class_sequence_truncated`;
- `significant_impact_terrain_class_unavailable_count`;
- `terrain_material_instrumentation_gaps`;
- aggregate `stop_state_summary_v3` counts for final, last-impact, and
  significant-impact classes.

Class labels are looked up from the configured aligned class raster at the
final position, last significant-impact location, and significant-impact event
locations. They are not inferred from paths, outcomes, runout, or terrain
slope. Missing metadata, out-of-grid points, nodata cells, and absent
significant impacts are reported as instrumentation gaps. These fields do not
change contact laws, parameters, stopping thresholds, validation metrics, or
pass/fail criteria. Significant-impact class sequences are bounded head/tail
diagnostics; per-event class tables are emitted only as opt-in companion
sidecars for ensemble impact-event CSV outputs with configured terrain classes.

When a generated ensemble/deposition output also has configured
`terrain_classes`, the runner writes an additive
`*_terrain_material_exposure.csv` sidecar with
`terrain_material_exposure_table_v1` schema. This sidecar is not configured as a
separate case output; it is a diagnostic companion to the generated deposition
output. It groups saved trajectory samples by terrain/material class and records
sample counts, segment counts, duration, horizontal path length, contact sample
counts, contact duration, contact path length, contact-state sample counts, and
explicit lookup gaps for unavailable class context. The run manifest records a
`terrain_material_exposure_summary_v1` object with per-class aggregate exposure
summaries. Exposure summaries are descriptive sample/path provenance and do not
change trajectories, contact laws, validation metrics, or pass/fail criteria.

When `terrain_classes` and `outputs.ensemble_impact_events_dir` are both
configured, validation also writes a sibling `*_terrain_material/` directory
with `impact_terrain_material_table_v1` CSV files. The same sidecar is written
beside `outputs.ensemble_impact_events_parquet` when terrain classes are
configured and no impact-event CSV directory is configured. Each row is keyed
by trajectory id, impact index, and impact time/location, reports whether the
impact meets the fixed significant-impact threshold, classifies the configured
terrain/material class at the impact point when available, lists configured
override field names and explicit override values for that class, and records
explicit lookup gaps for outside-grid or nodata impacts. Override values are
configured class metadata assumptions only and do not include global defaults.
This sidecar does not alter the existing impact-event CSV/Parquet schemas.

`terrain_classes` manifest records carry `terrain_class_manifest_v1`,
the source metadata schema version, and SHA-256 hashes for the metadata sidecar
and class raster when those files are available through the configured metadata
path. Each class-coverage entry also lists the configured terrain/material
override field names and count for that class, if any. These names expose active
configured assumptions only; they are not calibrated material evidence.

## Hazard-Layer Statistics

`hazard_layers.statistics` is consumed by `scripts/build_hazard_layers.py`, not by the simulation kernel. Threshold lists are optional, finite, nonnegative values. When configured, the hazard builder writes trajectory-level exceedance probability rasters in addition to the existing reach, deposition, maximum-energy, jump-height, and impact-density layers. It also writes `conditional_intensity_exceedance_curves_v1` as `<prefix>_conditional_intensity_exceedance_curves.csv`, a tidy table over grid cell, intensity measure, threshold, numerator, denominator, conditional fraction, optional standard error, probability mode, and normalization scope. Existing validation pass/fail semantics are unchanged.

## Hazard Probability Block

`hazard_probability` is also consumed only by
`scripts/build_hazard_layers.py`. It is optional and disabled by default. The
current implementation supports only sampling-weighted conditional maps:

```yaml
hazard_probability:
  probability_model: sampling_weighted
  metadata_path: validation/results/example_trajectory_metadata.csv
  weight_column: sampling_weight
  normalization_convention: conditioned_on_filter
  filters:
    source_zone_ids: []
    scenario_ids: []
    block_mass_kg_min: null
    block_mass_kg_max: null
```

Validation rules:

- `probability_model` must be `sampling_weighted`;
- `normalization_convention` must be `conditioned_on_filter`;
- `weight_column` must be `sampling_weight`;
- `metadata_path` must point to a `trajectory_metadata_table_v1` CSV with
  `trajectory_id` and `sampling_weight`;
- sampling weights must be finite and nonnegative;
- filters may restrict `source_zone_id`, `scenario_id`, and block-mass range;
- the filtered total weight must be positive;
- every trajectory CSV supplied to the hazard builder must resolve to a
  metadata row that passes the active filters.

When enabled, the hazard builder writes weighted reach and weighted
deposition-density rasters, weighted significant-impact event-density rasters,
plus weighted trajectory-level exceedance probability rasters, alongside the
existing unweighted rasters. Weighted deposition density requires
`trajectory_id` in the ensemble deposition CSV so rows can be joined to the
active metadata filter. Its denominator is the filtered sampling-weight sum, so
the layer can sum below `1.0` when the supplied deposition CSV covers only part
of the filtered trajectory input set. Weighted significant-impact density
requires resolvable `trajectory_id` values in CSV or Parquet impact-event inputs
and is normalized by the filtered significant-impact event sampling-weight sum.
These are conditional sampling-weighted diagnostics only; they are not
annual-frequency, physical source-probability, exposure, or risk layers.

Cases can also opt into unweighted trajectory-level probability standard-error
rasters:

```yaml
hazard_layers:
  statistics:
    probability_standard_error: true
```

The hazard builder then writes `reach_probability_standard_error` and
`<exceedance_layer>_standard_error` rasters for configured unweighted
trajectory-level probability layers. The formula is `sqrt(p(1-p)/n)`, using the
supplied trajectory count. These rasters are convergence diagnostics only; they
are not weighted uncertainty estimates, confidence intervals, physical
probability validation, annual frequency, exposure, vulnerability, or risk.

## Release-Zone Metadata

Swiss pilot source-area cases can opt into `release_zone.metadata_path`. This is an orchestration feature, not new physics: the simulator still runs independent spherical-block trajectories from generated starting points.

The current `schema_version: 1` release-zone metadata contract supports only small fixtures:

- `coordinate_reference_system.epsg: 2056` (`EPSG:2056`) and `vertical_datum: LN02`
- `geometry.type: polygon` with LV95 metre coordinates
- `sampling.mode: deterministic_grid`
- `sampling.count`, `sampling.seed`, `sampling.initial_velocity_mps`, optional `sampling.z_offset_m`, and `sampling.point_id_prefix`
- `source_dataset`, optional `source_url`, `license`, and `provenance.notes`

When both `terrain.metadata_path` and `release_zone.metadata_path` are present, validation checks that CRS/vertical datum match and that the release polygon lies inside the small pilot DEM footprint. Generated release points are recorded in `run_manifest_v1` and can optionally be written to `release_zone.generated_release_points_csv`.

Source-zone semantics are defined in
`docs/probabilistic_scenario_model_design.md`. In this validation schema,
`release_zone.metadata_path` is a separate schema-version-1 deterministic
release-generation sidecar. `source_zone_metadata_v1` belongs to the
probabilistic metadata contract for source-zone/scenario joins and
`trajectory_metadata_table_v1` production. Both sidecar families must preserve
stable source/release identity, CRS/vertical datum, sampling policy,
provenance, source, and license notes, but they are not the same schema. Neither
sidecar implies physical source probability, annual source frequency, national
release-zone derivation, validation evidence from swisstopo inputs alone, or
operational source-zone approval.

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

## Passive Block-Shape Metadata

Validation cases can opt into passive shape metadata:

```yaml
block_shape:
  metadata_path: validation/data/example/block_shape.yaml
```

The sidecar must use `schema_version: shape_metadata_v1`. Supported
`shape_type` values are `sphere`, `ellipsoid`, `box`, `principal_dimensions`,
and `custom_principal_moments`. The validator checks finite positive dimensions,
mass, density, and principal moments where present, and requires
`orientation.representation: quaternion_wxyz` with a unit
`initial_quaternion_wxyz`. For `principal_dimensions`,
`mass_properties.mass_property_model` must be either
`box_principal_dimensions` or `ellipsoid_principal_dimensions`. Shape metadata
must match the active `block.mass` and the descriptive equivalent radius when
that radius is supplied.

This metadata is passive for `translational_v0` and `sphere_rotational_v1`.
The experimental `shape_contact_v0` scaffold recognizes the metadata only when
explicitly selected, requires compatible `principal_dimensions` sidecars using
`mass_property_model: box_principal_dimensions`, and exposes scaffold-owned
analytic contact preparation only through internal verification paths. It still
stops before fixed-step simulation and public validation runs. The raw low-level impulse kernel is
crate-internal test support rather than a public validation API. The
crate-internal preparation layer keeps terrain/contact context, support
selection, mass, inertia, contact-regime classification, and diagnostics tied to
the validated sidecar; a test-only single-contact wrapper exercises this path
before runtime wiring. An internal contact-adjacent dry run can combine a
terrain contact point, terrain normal, support gap diagnostic, and one
scaffold-owned impulse update for touching or penetrating contact without
producing validation or benchmark outputs. An internal synthetic harness can
query simple analytic terrain height and normal before calling the same
preparation layer, but it is not a public validation path. The internal
integrator-smoke scaffold can advance one synthetic ballistic prediction
through an integrator-owned fixed-step prediction helper, collect an in-memory
`shape_contact_runtime_diagnostic_v1` row, and build a manifest-shaped
diagnostic sidecar record. Tests can use file-backed shape metadata so
`shape_metadata_path` and `shape_metadata_sha256` are real. Internal tests can
write a temporary JSON Lines sidecar and manifest checksum, but those files are
not public validation outputs and are not committed. Persistent contact
handling, projection, orientation evolution, and public runtime diagnostic
emission remain deferred. Separated dry-run states remain non-impulsive, even
when moving toward future contact.
The contact-gap tolerance is fixed at `1.0e-9 m` as a deterministic
pre-runtime scaffold convention, not a
calibrated contact parameter. The runtime diagnostic implementation is still
incomplete before public `shape_contact_v0` use.
Support-corner tie breaks are deterministic: exact zero components in the
body-frame support direction choose the positive corner sign. That policy is
reproducibility scaffolding, not a validated face-contact law.
Current default contact, inertia, trajectory integration, and validation
semantics remain spherical and continue to use `block.radius` and the current
spherical moment of inertia.

Before `shape_contact_v0` can be used by public validation or benchmark cases,
runtime contact rows must implement the frozen
`shape_contact_runtime_diagnostic_v1` contract from
`docs/shape_contact_v0_experimental_contract.md`. Required row fields include
row identity fields (`case_id`, `trajectory_id`, `step_index`, `time_s`, and
`shape_contact_row_id`), optional impact-event alignment fields,
`contact_regime`, `shape_contact_regime_label`, `support_signed_gap_m`,
`contact_gap_tolerance_m`, `terrain_contact_point_*_m`, `terrain_normal_*`,
`support_point_*_m`, `support_corner_sign_*`, pre/post contact-point normal and
tangential speeds, normal and tangential impulse fields, active restitution,
friction, and gravity fields, `coulomb_cap_ratio`, pre/post
translational, rotational, potential, and total mechanical energy fields,
`contact_energy_delta_j`, `projection_energy_delta_j`, `total_energy_delta_j`,
orientation quaternion fields, `orientation_norm_error`, active model/shape
metadata, and explicit `impulse_applied` / `projection_applied` flags. While
projection correction is deferred, `projection_energy_delta_j` must be null and
`projection_applied` must be false; `total_energy_delta_j` must equal
`post_total_mechanical_energy_j - pre_total_mechanical_energy_j` and, while
projection is absent, `contact_energy_delta_j`.

Future `run_manifest_v1` output for `shape_contact_v0` must include an additive
`shape_contact_v0` object recording `active_contact_model`, `active_shape_type`,
`shape_metadata_path`, `shape_metadata_sha256`, `shape_id`, active mass,
principal dimensions, orientation initialization/representation, `inertia_model`,
`principal_moments_kg_m2`, support-selection and tie-break policy,
`contact_gap_tolerance_m`, `multi_contact: false`,
`new_tuned_parameters: false`, `defaults_changed: false`, projection,
persistent-contact, and
orientation-evolution flags, runtime diagnostic schema version, experimental
status, warnings, and limitations. These fields are a future diagnostic contract
only; current validation loading still rejects public `shape_contact_v0`
execution.

The only tracked validation-style `shape_contact_v0` case is
`validation/internal/shape_contact_v0_internal_smoke.yaml`. It is internal-only
and outside public `validate --all` discovery. It may be loaded only by focused
Rust smoke tests that assert diagnostic rows, sidecar manifests, and public
runner rejection; it is not public validation or benchmark evidence.

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
`outputs.trajectory_csv` remains a representative trajectory output and now
includes an additive leading `trajectory_id` column when written by validation.
The run manifest records a deterministic aggregate `sha256` for the CSV
directory, computed from sorted member file names, byte sizes, and file
checksums.
Hazard-layer reach probability, maximum kinetic energy, and maximum jump height should use
`outputs.ensemble_trajectories_dir` when the full ensemble is needed.

When `outputs.ensemble_impact_events_dir` is set, validation writes deterministic
per-trajectory impact-event CSV files for ensemble members that produced impact
events. Validation-written impact-event CSVs include an additive leading
`trajectory_id` column. When at least one impact-event CSV is written, the run
manifest records the same deterministic aggregate directory `sha256` policy used
for ensemble trajectory CSV directories. Hazard-layer significant-impact density
should use this directory when full-ensemble impact density is needed.

When `outputs.ensemble_impact_events_parquet` is set, validation writes one
batched Parquet file with schema version `impact_events_table_v1`. The table
contains `trajectory_id`, `impact_index`, optional `seed`, a
`significant_impact` flag, `scarring_depth_source`, and the same numeric
velocity, energy, geometry, and scarring diagnostics exposed by impact-event
CSV/JSON output. Cases may write CSV impact directories, Parquet, both, or
neither. This columnar output is intended for file-count reduction and efficient
trajectory-id joins in post-processing; it does not change validation semantics
or simulation physics.

When `outputs.trajectory_metadata_csv` is set, validation writes one
`trajectory_metadata_table_v1` row per simulated output trajectory. Current rows
contain `trajectory_id`, `release_id`, `source_zone_id`, release coordinates,
null `release_probability`, `block_radius_m`, `block_mass_kg`, optional
`block_density_kgpm3`, `shape_class`, optional passive shape fields
(`shape_id`, `shape_type`, `equivalent_radius_m`, principal dimensions,
principal moments, and initial quaternion components), `scenario_id`,
`sampling_weight = 1.0`, and `probability_model = "unweighted"`. This sidecar
can be used by opt-in sampling-weighted hazard-layer post-processing. It does
not change default unweighted hazard or validation semantics.

Validation cases may also opt in to Phase 1 probabilistic map metadata with a
top-level `probabilistic_metadata` block:

```yaml
probabilistic_metadata:
  source_zone_metadata_path: tests/fixtures/probabilistic_phase1/source_zone_valid.yaml
  scenario_table_path: tests/fixtures/probabilistic_phase1/scenario_level1.csv
  map_product_id: phase1_demo_map
  probability_mode: sampling_weighted_conditional
  normalization_scope: conditioned_on_scenario
  scenario_id: scenario_a  # required when the scenario table has multiple rows
```

When this block is present, the runner validates the referenced
`source_zone_metadata_v1` and `scenario_table_v1` sidecars before writing
outputs. The selected scenario row is propagated additively into
`trajectory_metadata_table_v1`: `map_product_id`, `scenario_id`,
`source_zone_id`, deterministic `release_cell_id`, `block_scenario_id`,
`block_size_class`, `block_shape_class`, `terrain_material_assumption_id`,
`model_configuration_id`, `sampling_weight`, `probability_mode`, and
`normalization_scope`. `annual_frequency_per_year` remains null/empty in Phase
1. If multiple scenario rows are present, `scenario_id` is required; the runner
does not infer a scenario. Existing cases without `probabilistic_metadata`
remain diagnostic/unweighted and are not relabelled probabilistic.

Block-scenario fields propagated from `scenario_table_v1` are additive labels
and weights for Phase 1 metadata. `block_scenario_id`, `block_size_class`,
`block_shape_class`, and `sampling_weight` do not change default simulation
physics, do not create shape-dependent contact, and do not define physical
block-population probability unless a future schema and runner explicitly add
that contract. Representative radius/mass/density fields in `scenario_table_v1`
are parsed and validated scenario-table fields, but current
`trajectory_metadata_table_v1` numeric block columns report active simulated
case block and passive shape values, not scenario-row numeric overrides.

Scenario consistency expectations are summarized in
`docs/probabilistic_scenario_model_design.md`. Current parser/tests enforce
some Phase 1 checks, including source-zone/scenario joins, sampling-weight
constraints, and annual-frequency rejection. Calibration/validation separation,
swisstopo-as-input-not-validation interpretation, deterministic seed review,
and reducer-order independence remain documented review gates unless a future
milestone adds executable enforcement.

When `outputs.manifest_json` is set, verification or validation writes an
additive `run_manifest_v1` sidecar. The manifest records the case id, model
version, git hash, config fingerprint, seed policy, terrain source, output file
summaries, warnings, completion status, execution status, and scientific status.
It does not replace diagnostics JSON or change pass/fail semantics. If
`terrain.metadata_path` is present, the
manifest terrain section includes CRS/EPSG, vertical datum, LV95 extent,
resolution, nodata, source dataset/product, source filename/URL, license,
download/preprocessing status, optional `raw_sha256` and `processed_sha256`
checksums from the metadata sidecar, and provenance notes. If `release_zone` is
present, the manifest includes release-zone id, metadata path, CRS/EPSG,
vertical datum, deterministic sampling mode and seed, requested/generated
release-point counts, polygon extent/area, source/license fields, and
provenance notes. If `terrain_classes` is present, the manifest includes
terrain-class layer id, metadata path, class-grid path, CRS/EPSG, vertical datum,
resolution, extent, nodata, source/license fields, class coverage histogram,
configured override field names per class, and provenance notes. If
`block_shape.metadata_path` is present, the manifest
includes a `shape_metadata` section with schema version, metadata path, shape id
and type, active contact shape, active contact radius, passive mass properties,
initial orientation, provenance, and a warning that current contact remains
spherical. If `outputs.trajectory_metadata_csv` is present, the manifest
includes a `trajectory_metadata` section with schema version, path, row count,
probability model, probability semantics, normalization convention, and total
sampling weight. Single-file output entries include additive SHA-256 checksums
where feasible; directory outputs keep file-count and byte summaries without
per-file hashes.

Diagnostics and manifests split status interpretation:

- `execution_status`: whether the case completed, failed, or skipped;
- `scientific_status`: whether configured acceptance thresholds were met,
  failed, absent, or not evaluated.

Real-world validation cases with observations but no configured acceptance
thresholds use `scientific_status:
reported_without_acceptance_thresholds`. Their legacy `status: passed` still
means the workflow completed and reported metrics, not that scientific skill was
accepted against thresholds.

Phase 1 probabilistic hazard-map metadata is available through Rust parsers for:

- `source_zone_metadata_v1` YAML source-zone sidecars;
- `scenario_table_v1` CSV scenario tables;
- `map_package_manifest_v1` JSON/YAML map-package manifests.

Source-zone/block-scenario v1 semantics, source-zone derivation evidence
levels, current examples, and executable check boundaries are defined in
`docs/probabilistic_scenario_model_design.md`. This schema document records
where the metadata appears; it does not duplicate the interpretation contract.

These contracts add Level 1-2 map semantics (`map_product_id`,
`source_zone_id`, `source_zone_metadata_path`, scenario ids, block/scenario
classes, `sampling_weight`, `probability_mode`, and `normalization_scope`)
without changing existing validation cases. The validation runner uses these
parsers only when `probabilistic_metadata` is configured. The validator accepts
`unweighted_diagnostic` and `sampling_weighted_conditional` labels, recognizes
`physical_probability` only when explicit physical probability columns are
present, and rejects `annual_frequency` in Phase 1 with a Level 3 error. Tiny
schema fixtures live under `tests/fixtures/probabilistic_phase1/`.

Hazard-layer builds can opt in to map-package labelling with a
`hazard_map_package` block or equivalent CLI flags. This adds
`hazard_map_package` and `layer_semantics` sections to the hazard
`run_manifest_v1` and writes a `map_package_manifest_v1` JSON sidecar. The
builder validates source-zone/scenario joins before writing labelled products,
keeps `annual_frequency_fields_present: false` in Phase 1, and rejects
`physical_probability` or `annual_frequency` package generation. Unlabelled
hazard builds remain diagnostic and backward-compatible.

Hazard-layer builds can also opt in to GIS raster export without changing
existing CSV/ASCII outputs:

```yaml
hazard_exports:
  geotiff: true
  cog: false
```

`geotiff: true` writes one float64 GeoTIFF per generated hazard raster. The
hazard manifest records `format: geotiff`, SHA-256 checksum, affine transform,
nodata value, grid dimensions, extent, EPSG/vertical datum when available from
`terrain.metadata_path`, and probability semantics with `annualized: false`.
`cog: true` is schema-reserved but rejected by the Phase 2A hazard builder until
a verified COG writer is added. Existing cases that omit `hazard_exports`
continue to write only CSV/ASCII/GeoJSON/JSON outputs.

Local diagnostic GIS/QGIS review packages can opt in to a package inventory:

```yaml
pilot_gis_package:
  enabled: true
  visual_qa_status: not-run
  visual_qa_note: "Manual GIS/QGIS inspection has not been run."
  reviewed_artifacts: []
  source_zone_context_paths: []
```

When enabled with GeoTIFF export, the hazard builder writes
`pilot_gis_package_manifest_v1` as
`<prefix>_pilot_gis_package_manifest.json`. The manifest inventories GeoTIFF
rasters, CSV/ASCII parity grids, hazard metadata, optional map-package
manifests, optional source-zone context sidecars, terrain metadata identity,
grid/terrain provenance, visual QA status, and unsupported claim boundaries.
It is a research-diagnostic review manifest only; it is not a QGZ, GeoPackage,
COG, annual intensity-frequency product, return-period product, risk map, or
operational hazard-map approval artifact.

Hazard-layer builds can opt in to local chunked reducer execution with
`--reducer-workers N` for `N > 1`. The hazard `run_manifest_v1` then records a
`reducer_execution` section with schema version
`deterministic_local_reducer_v1`, sorted chunk-id merge order, worker count,
chunk ids, and reducer contract. Each chunk writes
`hazard_reducer_chunk_manifest_v1` JSON under the output `chunks/` directory
with input artifact identities, row counts, reducer counts, timings, completion
status, and local in-memory partial-state limitations. The chunked reducer is
required to preserve serial output values for current conditional diagnostic
layers; it does not introduce annual frequency, physical probability, or
distributed execution semantics.

Phase 6 public real-site conditional pilots must be predeclared with
`public_real_site_conditional_pilot_run_v1` before execution. The run-freeze
YAML records validated geodata and source-scenario policy paths, frozen case
and terrain/source-zone/scenario sidecars, physics defaults, random seed,
gate-run scale, target scale, reducer mode, conditional thresholds, explicit
grid, output roots, output budget, workflow gate statuses, and report
classification. The committed template remains `template_not_run`; populated
local copies belong in ignored pilot directories and generated outputs remain
outside git.

For populated non-template run-freeze files,
`scripts/validate_public_real_site_conditional_pilot_run.py
--print-command-plan` emits
`public_real_site_conditional_pilot_command_plan_v1`. The plan is dry-run
orchestration metadata: it lists validators, the frozen `cargo run -- validate`
case, and the hazard-layer command with explicit grid, conditional thresholds,
map-package metadata, GeoTIFF export, pilot GIS package manifest, and local
reducer worker count. It does not execute commands or alter output semantics.

If `outputs.ensemble_impact_events_parquet` is present, the manifest `outputs`
array includes `kind: ensemble_impact_events`, `format: parquet`,
`schema_version: impact_events_table_v1`, path, row count, file count, total
bytes, SHA-256 checksum, compression, and row-group count when available.

Current manifests also include an optional `performance` object with lightweight
wall-clock and output-volume diagnostics: `total_wall_seconds`,
`terrain_load_seconds`, `release_generation_seconds`, `simulation_seconds`,
`output_write_seconds`, optional `hazard_layer_seconds`, `trajectory_count`,
`impact_event_count`, `output_file_count`, and `output_bytes`. Hazard-layer
manifests additionally split post-processing into `accumulation_seconds`,
`core_output_write_seconds`, `plot_render_seconds`, and `plots_enabled`.
`hazard_layer_seconds` is retained as a backward-compatible alias for
`accumulation_seconds`; `output_write_seconds` is the sum of core output writing
and optional plot/report rendering. These values are diagnostic metadata, not
validation thresholds. Older manifests without this section remain valid.

When `outputs.ensemble_trajectories_dir` or
`outputs.ensemble_impact_events_dir` is set, validation treats the configured
directory as run-exclusive for generated CSVs. Existing `*.csv` files in that
directory are removed before the current run writes its ensemble files so later
hazard-layer builds cannot accidentally consume stale trajectories or impact
events from an earlier, larger run. Non-CSV files are left untouched.

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
- `significant_impact_count`: impact-event count filtered by incoming normal speed. Since v0.5.0, an impact is significant when `incoming_normal_speed_mps >= 0.05 m/s`. This threshold is tied to the current stop-speed scale and is intended to separate physically interpretable rebound/contact events from near-rest chatter while preserving the raw event log.

Use `impact_event_count` when auditing all contact responses, `significant_impact_count` when comparing impact-level behavior, and `impact_count` only for legacy trajectory-state tests.

## Local Tschamut/swissALTI3D Pilot Templates

Runnable private Tschamut/swissALTI3D pilot cases should be generated under
ignored `validation/private/` paths with:

```bash
python3 scripts/prepare_tschamut_swissalti3d_pilot.py \
  --dem-path /path/to/private/tschamut_swissalti3d_crop.asc \
  --terrain-metadata /path/to/private/tschamut_swissalti3d_metadata.yaml \
  --release-zone-metadata /path/to/private/tschamut_release_zone.yaml
```

The checked-in templates live under `validation/templates/` and contain
placeholders only. They are not scanned by `cargo run -- validate --all`.
Generated private cases use the same schema as validation cases, including
`terrain.metadata_path`, `release_zone.metadata_path`,
optional `terrain_classes.metadata_path`, full ensemble trajectory/impact
outputs, and `hazard_layers.statistics` thresholds.

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
