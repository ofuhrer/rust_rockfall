# Probabilistic Hazard Phase 1 Closure

Status: closed for Level 1 conditional and Level 2 sampling-weighted hazard-map
semantics. Phase 1 is a metadata, validation, labelling, and smoke-example
milestone. It does not change simulation physics, default parameters, validation
semantics, hazard raster values, or operational status.

## Implemented Capabilities

Phase 1 now provides:

- `source_zone_metadata_v1` parsing and validation for source-zone identity,
  CRS, geometry, release sampling policy, and provenance;
- `scenario_table_v1` parsing and validation for scenario identity, source-zone
  joins, block/source/model labels, sampling weights, and probability-mode
  safeguards;
- `map_package_manifest_v1` parsing, validation, and hazard-builder writing for
  labelled map packages;
- opt-in validation-case `probabilistic_metadata` that propagates validated
  `map_product_id`, `scenario_id`, `source_zone_id`, `release_cell_id`,
  block-scenario labels, model-configuration labels, `sampling_weight`,
  `probability_mode`, and `normalization_scope` into
  `trajectory_metadata_table_v1` and run manifests;
- opt-in hazard-map package labelling that adds `hazard_map_package` and
  `layer_semantics` sections to hazard manifests without changing raster values;
- a CI-safe smoke example at
  `validation/cases/probabilistic_phase1_smoke.yaml` covering source-zone
  metadata, scenario table validation, trajectory metadata propagation,
  sampling-weighted hazard layers, labelled hazard manifest output, and
  `map_package_manifest_v1` writing.

## Exact Limits

Phase 1 supports only:

- `unweighted_diagnostic` labels for diagnostic products;
- `sampling_weighted_conditional` labels for maps normalized by an explicit
  filter or scenario scope;
- `conditioned_on_filter` and `conditioned_on_scenario` normalization scopes for
  generated labelled products.

Phase 1 does not generate:

- physical-probability maps;
- annual-frequency maps;
- source-frequency models;
- block-size probability distributions;
- regional/tiled products;
- Cloud-Optimized GeoTIFF products;
- exposure, vulnerability, or risk layers;
- operationally valid hazard products.

`physical_probability` and `annual_frequency` remain schema-visible labels so
future phases can validate them consistently. The Phase 1 hazard builder rejects
those generated package modes with explicit errors rather than writing products
whose semantics could be confused with calibrated physical or annual hazard.

## What The Smoke Example Proves

The smoke example proves that the Phase 1 metadata path is internally connected:

- source-zone and scenario sidecars validate before use;
- selected scenario metadata reaches trajectory metadata deterministically;
- all generated trajectories can be joined to metadata by `trajectory_id`;
- all-unity `sampling_weight` values make weighted trajectory-derived layers
  match the corresponding unweighted layers;
- labelled and unlabelled hazard runs produce identical raster values;
- labelled hazard manifests and map-package manifests expose probability mode,
  normalization scope, source-zone id, scenario ids, total weights,
  layer semantics, and `annualized: false` style metadata.

## What It Does Not Prove

The smoke example does not validate model skill, source-zone probability,
terrain/material assumptions, annual frequency, or operational hazard-map
quality. It uses tiny synthetic fixtures only. It is a reproducibility and
semantics regression test, not a public benchmark, calibration case, Swiss
pilot result, or risk product.

## Compatibility Guarantees

Phase 1 preserves these compatibility boundaries:

- existing validation cases do not require probabilistic metadata;
- existing unweighted hazard outputs remain diagnostic and are not relabelled
  probabilistic;
- weighted hazard raster numerics remain controlled by the existing
  `hazard_probability.probability_model: sampling_weighted` path;
- `hazard_map_package` adds labels and manifests only when explicitly
  configured;
- annual-frequency fields remain null/empty in Phase 1 propagation;
- simulation physics and contact-model defaults are unchanged.

## Remaining Phase 2/3 Candidates

Candidate next phases are:

- **Phase 2A: GIS-ready GeoTIFF export for existing labelled hazard rasters.**
  This addresses the largest product-readiness gap after Phase 1: rasters now
  have explicit semantics, but need CRS-bearing GIS products for reviewable
  Swiss pilot workflows. The first Phase 2A slice writes value-preserving
  GeoTIFFs; Cloud-Optimized GeoTIFF remains deferred until a verified COG writer
  is selected.
- **Phase 2B: map-product packaging polish.** This would improve package
  completeness checks, artifact inventories, and review templates around the
  existing map-package manifest without changing map values.
- **Phase 2C: regional pilot orchestration design.** This should wait until the
  single-domain GIS package path is demonstrably reproducible.
- **Phase 3: physical probability or annual frequency.** This requires explicit
  source-frequency evidence, temporal assumptions, and validation policy before
  code should generate annualized products.

## Recommended Next Implementation Slice

Recommended next slice after Phase 1: **Phase 2A, GIS-ready GeoTIFF export for
existing labelled hazard rasters**.

Rationale:

- Phase 1 has already made conditional and sampling-weighted map semantics
  auditable in manifests.
- Swiss pilot and public benchmark workflows still need CRS-bearing raster
  products for ordinary GIS review.
- GeoTIFF export can be additive and value-preserving: it should export the
  existing raster arrays with CRS, extent, nodata, units, checksums, and
  manifest links. COG-specific compression, tiling, and overview guarantees
  should wait for a dedicated writer.
- This closes a practical product gap without changing physics, tuning
  parameters, probability semantics, or validation datasets.

Deferred:

- annual-frequency and physical-probability map generation, until source
  frequency and probability inputs are scientifically defined;
- regional tiling, until single-domain GIS products are stable;
- active shape-contact physics, which remains a separate scientific work package
  rather than a prerequisite for conditional map semantics;
- exposure/vulnerability/risk layers, which are outside the hazard-modelling
  scope of the current core.
