# Changelog

## Unreleased

- Eliminated two redundant `terrain.try_normal` calls per integration step by
  reusing the already-computed normal in the contact-state diagnostics block of
  `try_simulate_fixed_step_with_events_and_contact_parameters`. This reduces
  terrain normal queries from four to two per step, halving DEM bilinear
  interpolation work in the hot loop.
- Unified the `unit_or` helper across `dynamics`, `stochastic`, and `integrator`
  modules: all three now use `try_normalize(EPS)` with a double fallback to
  `Vec3(0,0,1)`. Previously `dynamics` and `stochastic` used a `norm > 0.0`
  guard that would normalize near-zero vectors and amplify floating-point noise;
  the integrator's safer implementation is now canonical.
- Added inline documentation for `percentile` (requires sorted input),
  `stddev_axis_y` (population std dev, not sample), and `DemGrid::xmax_m` /
  `DemGrid::ymax_m` (return cell-center maxima, not footprint extents).
- Added unit tests covering the `unit_or` zero-vector, dual-zero, and
  non-zero-normalization cases.

- Hardened runtime configuration, DEM parsing, hazard-layer input semantics,
  and reducer layer construction by rejecting unknown simulation JSON fields,
  rejecting panic-prone DEM grids, rejecting mixed `trajectory_id` trajectory
  CSVs, and making hazard-layer normalization idempotent.
- Added Python workflow unit tests to the local pre-push gate.
- Updated roadmap, scalability, and performance documentation to distinguish
  implemented local hazard-reducer scaffolding from still-missing parallel
  trajectory execution, resumeable chunks, tiled reducers, and annual/physical
  hazard products.
- Added validation maturity, public real-site geodata preparation, source/block
  scenario policy, and conditional real-site pilot run scaffolds and validators.
- Removed duplicate copy-suffix roadmap documents and added a repository
  consistency guard against reintroducing tracked copy-suffix docs.
- Added a pre-runtime, opt-in `shape_contact_v0` scaffold for analytic
  box-shape metadata validation, support selection, impulse diagnostics, and
  internal dry-run checks. It remains blocked from fixed-step simulation,
  validation, and benchmarks; existing contact models and defaults are
  unchanged.
- Fixed persistent `translational_v0` sliding integration so tangential gravity
  is applied once per step after ballistic stepping. This is targeted as the
  `v0.6.1` patch-candidate physics bug fix and changes default numerical
  results for sliding contact cases.
- Adopted the standard ESRI/GIS DEM convention for ASCII grids:
  `xllcorner`/`yllcorner` are outer lower-left cell corners, raster values are
  cell-center samples, and metadata extents record the full outer footprint.
  This can change DEM-backed validation metrics and the `Chant Sura` contact
  timing tolerance was refreshed accordingly.
- Added an expert-review baseline release-preparation note for the proposed
  `v0.6.0-expert-review-baseline` tag, without creating the tag or changing the
  project version.
- Added opt-in batched Parquet impact-event output via `outputs.ensemble_impact_events_parquet` and `impact_events_table_v1`.
- Added hazard-layer Parquet impact-event reader support with CSV/Parquet significant-impact density parity.
- Added manifest metadata for columnar impact-event outputs, including schema version, row count, compression, and row-group count.
- Added a benchmark harness mode and results document comparing Parquet impact-event output with the existing CSV impact-event workflow.
- Added explicit smoke/standard/scale/custom performance benchmark profiles and made the default standard profile a short no-plot local run.
- Added a canonical post-refactor benchmark profile reference with measured smoke, standard, custom, and scale results.

## v0.6.0

- Added opt-in sampling-weighted conditional hazard layers using `trajectory_metadata_table_v1` and `sampling_weight`.
- Added strict probability-configuration validation for supported `sampling_weighted` maps, metadata joins, filters, nonnegative weights, and positive filtered total weight.
- Added weighted reach, kinetic-energy exceedance, jump-height exceedance, and velocity exceedance raster outputs while preserving existing unweighted hazard layers.
- Added weighted-hazard manifest metadata, illustrative fixtures, focused tests, and probability-semantics documentation.

## v0.5.0

- Added Chant Sura trajectory-validation fixtures and model-improvement evaluation documentation.
- Added real-data single-impact scarring calibration using public Chant Sura / ESurf 2019 tables.
- Added a lightweight hazard-layer post-processing workflow for reach probability, deposition density, maximum kinetic energy, maximum jump height, significant impact density, CSV/ASCII grid exports, deposition GeoJSON, PNG plots, and local HTML reports.
- Added opt-in full ensemble trajectory and impact-event outputs for scientifically meaningful small-to-medium hazard layers.
- Added hazard-layer scientific analysis, scale-review notes, and smoke-test fixtures while keeping simulation physics unchanged.
- Added swisstopo metadata-only dataset registry entries, terrain tile metadata schema, and Swiss pilot geodata strategy without downloading or committing national datasets.
- Consolidated documentation, dataset roles, version metadata, generated-artifact hygiene, and repository consistency checks.

## v0.4.0

- Added opt-in `scarring_contact_v1` soil interaction model for minimal compactable-soil impact energy-loss diagnostics.
- Added scarring configuration fields, trajectory diagnostics, verification metrics, and synthetic scarring verification cases.
- Kept default behavior unchanged with `soil_interaction_model: none`.
- Updated schema, documentation, report generation, and consistency checks for versioned scarring fields.

## v0.3.0

- Added opt-in `stochastic_contact_v1` impact roughness.
- Added roughness parameters for contact-normal angular perturbation, dissipative restitution perturbation, and friction increase.
- Added roughness verification cases for zero-roughness consistency, seeded reproducibility, ensemble spread, and energy stability.
- Added semantic-versioning rules and consistency checks.
- Updated visualization/reporting to expose model version and roughness-enabled cases.

## v0.2.0

- Added opt-in `sphere_rotational_v1` sphere contact with translational-rotational impulse coupling.
- Added rolling diagnostics, rolling contact state, and simple rolling resistance.
- Added HPC-readiness constraints, deterministic ensemble seed derivation, validation/report tooling, and report readability improvements.

## v0.1.0

- Initial independent spherical-block simulator with analytic terrain, free flight, translational impact response, Coulomb contact friction, seeded release perturbations, CSV output, and verification scaffolding.
