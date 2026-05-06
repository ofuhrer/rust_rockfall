# Changelog

## Unreleased

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
