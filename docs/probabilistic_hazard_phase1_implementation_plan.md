# Probabilistic Hazard Phase 1 Implementation Plan

Status: implementation plan for Level 1-2 hazard-map semantics and scenario
modelling. Slice B is implemented as metadata parsers and validators in
`src/probabilistic.rs`; Slice C is implemented as opt-in validation-case
propagation into `trajectory_metadata_table_v1` and run manifests. Slice D is
implemented as opt-in hazard-manifest labelling and `map_package_manifest_v1`
writing. Slice E is implemented as a tiny end-to-end smoke example. Phase 1 is
closed for Level 1 conditional and Level 2 sampling-weighted map semantics. This
document does not tune parameters, change defaults, add physics, add active
shape-contact, add regional tiling, or claim annualized/operational hazard
validity.

## Objective

Phase 1 turns the probabilistic hazard-map roadmap into a concrete
implementation package for:

- map-product identity;
- source-zone identity and release-cell provenance;
- scenario tables;
- probability labels;
- sampling-weight normalization rules;
- manifest fields that make conditional and sampling-weighted maps auditable.

The immediate target is **Level 1 conditional source-zone maps** and **Level 2
sampling-weighted scenario maps**. Annualized hazard mapping remains explicitly
out of scope until temporal source-frequency fields and validation evidence
exist.

## Current Starting Point

Already implemented:

- `trajectory_metadata_table_v1` with `trajectory_id`, release metadata,
  `source_zone_id`, `scenario_id`, block radius/mass, shape class, and
  `sampling_weight = 1.0`;
- opt-in `hazard_probability.probability_model: sampling_weighted` for weighted
  reach and trajectory-level exceedance layers;
- `run_manifest_v1` hazard manifests with probability metadata for weighted
  runs;
- release-zone metadata for small source-area fixtures;
- public benchmark evidence showing that map semantics should not wait for new
  physics.

Phase 1 now covers the metadata and labelling path needed to distinguish
diagnostic outputs from conditional and sampling-weighted map packages. Physical
probability and annual-frequency labels remain schema-visible only; generated
Phase 1 maps reject them rather than producing ambiguous products.

Implemented in Slice B:

- `source_zone_metadata_v1` YAML parser and validator;
- `scenario_table_v1` CSV parser and validator;
- `map_package_manifest_v1` JSON/YAML parser and cross-validator;
- strict validation for supported probability modes, normalization scopes,
  negative weights/probabilities, source-zone mismatches, and unsupported
  annual-frequency labels;
- tiny parser/validator fixtures under `tests/fixtures/probabilistic_phase1/`.

Implemented in Slice C:

- optional validation-case `probabilistic_metadata` block;
- pre-run validation of referenced source-zone and scenario sidecars;
- deterministic scenario-row selection, requiring explicit `scenario_id` when
  a scenario table has multiple rows;
- additive source-zone, scenario, map-product, block-class, model-configuration,
  sampling-weight, probability-mode, and normalization-scope fields in
  `trajectory_metadata_table_v1` and its run-manifest summary;
- annual-frequency propagation remains null/empty in Phase 1.

Implemented in Slice D:

- optional hazard-builder `hazard_map_package` case block and matching CLI
  flags for `map_product_id`, `probability_mode`, `normalization_scope`,
  `source_zone_metadata_path`, `scenario_table_path`, and package-manifest
  output path;
- pre-output validation of source-zone/scenario joins for labelled hazard-map
  packages;
- additive `hazard_map_package` and `layer_semantics` sections in hazard
  metadata and `run_manifest_v1`;
- `map_package_manifest_v1` JSON writer for hazard outputs;
- existing internal `hazard_probability.probability_model: sampling_weighted`
  remains the numerical weighted-layer switch, while labelled map packages use
  the external `sampling_weighted_conditional` probability-mode label;
- `annual_frequency` and `physical_probability` remain rejected by the hazard
  builder in Phase 1.

Implemented in Slice E:

- checked-in tiny smoke source-zone and scenario sidecars under
  `validation/data/processed/probabilistic_phase1/`;
- checked-in validation case
  `validation/cases/probabilistic_phase1_smoke.yaml`;
- end-to-end tests that run validation, inspect `trajectory_metadata_table_v1`,
  build weighted hazard layers, write labelled hazard and map-package manifests,
  and verify labelled/unlabelled raster parity;
- all generated validation and hazard products remain under ignored result
  directories or temporary test directories.

## Phase 1 Schema Additions

### Map Package Identity

Add a lightweight `map_package_v1` metadata contract for generated hazard-map
packages.

| Field | Required | Meaning |
| --- | ---: | --- |
| `map_product_id` | yes | Stable id for the map package, independent of one validation case id. |
| `map_product_version` | yes | Schema/product version, initially `map_package_v1`. |
| `probability_mode` | yes | One of the allowed probability modes below. |
| `normalization_scope` | yes for weighted/probability modes | Denominator convention used by probability-like layers. |
| `source_zone_metadata_path` | yes for Level 1+ | Source-zone sidecar used to define the map conditioning. |
| `scenario_table_path` | yes for Level 2+ | Scenario rows used for block/source/model combinations and weights. |
| `hazard_manifest_paths` | yes | Paths to hazard `run_manifest_v1` files included in the package. |
| `validation_evidence` | yes | Public benchmark docs/manifests used as model-performance context. |
| `operational_status` | yes | Must be `research_diagnostic`, `review_candidate`, or a later explicit status; Phase 1 uses `research_diagnostic`. |

### Source-Zone Metadata

Extend the existing release-zone/source-zone contract with explicit Level 1
fields.

| Field | Required | Meaning |
| --- | ---: | --- |
| `source_zone_id` | yes | Stable source-zone identifier. |
| `source_zone_metadata_path` | manifest field | Path to the source-zone sidecar. |
| `crs_epsg` | yes | Horizontal CRS; Swiss pilots should use `2056`. |
| `vertical_datum` | yes when z is spatial | Vertical datum, for Swiss pilots usually `LN02`. |
| `geometry` | yes | Polygon, multipolygon, or raster-mask reference. |
| `release_sampling_policy` | yes | Sampling mode and determinism rules. |
| `release_cell_id` | yes for generated releases | Stable id for the sampled cell or release point. |
| `source_provenance` | yes | Data source, preprocessing, license, and author notes. |
| `annual_release_frequency_per_year` | null in Phase 1 | Reserved for Level 3; must be absent or null unless `annual_frequency` is supported. |

### Scenario Table

Define `scenario_table_v1` as a CSV or YAML table whose rows describe one
source/block/model scenario contribution.

Required Level 1 fields:

| Field | Meaning |
| --- | --- |
| `scenario_id` | Stable row/scenario identifier. |
| `source_zone_id` | Join to source-zone metadata. |
| `release_sampling_policy` | Policy id or label used for release-cell generation. |
| `model_configuration_id` | Contact model and optional model-feature configuration id. |
| `terrain_material_assumption_id` | Terrain/material assumption label, even if `uniform_global_parameters`. |
| `sampling_weight` | Defaults to `1.0` for unweighted/conditional scenarios. |

Recommended Level 1/2 block fields:

| Field | Meaning |
| --- | --- |
| `block_scenario_id` | Stable id for the block scenario. |
| `block_size_class` | Size/volume/mass class label. |
| `block_shape_class` | Shape class label, for example `sphere`, `blocky`, `plate`, or passive dataset class. |
| `block_radius_m` | Spherical or equivalent radius used by current dynamics. |
| `block_mass_kg` | Block mass. |
| `block_density_kgpm3` | Optional density. |

Reserved probability fields:

| Field | Phase 1 rule |
| --- | --- |
| `release_probability` | Null unless `physical_probability` is supported. |
| `scenario_probability` | Null unless `physical_probability` is supported. |
| `annual_frequency_per_year` | Null unless `annual_frequency` is supported. |
| `time_horizon_years` | Null unless annual or finite-time products are supported. |

### Trajectory Metadata Additions

Additive fields for `trajectory_metadata_table_v1` once Slice C is implemented:

| Field | Required for new map products | Meaning |
| --- | ---: | --- |
| `map_product_id` | yes | Joins trajectory to a map package. |
| `scenario_id` | yes | Already present; must be deterministic and stable. |
| `source_zone_id` | yes | Already present; must match source-zone metadata. |
| `release_cell_id` | yes for source-zone maps | Stable release-cell/source sample id. |
| `block_scenario_id` | yes for scenario maps | Block scenario identifier. |
| `block_size_class` | optional initially | Block-size class for filtering/grouping. |
| `block_shape_class` | optional initially | Shape class for filtering/grouping. |
| `terrain_material_assumption_id` | yes for map products | Records the terrain/material assumption used. |
| `model_configuration_id` | yes for map products | Contact/model configuration label. |
| `sampling_weight` | yes | Nonnegative finite estimator weight. |
| `probability_mode` | yes | Matches the map or scenario probability mode. |
| `normalization_scope` | yes for weighted modes | Denominator convention. |
| `annual_frequency_per_year` | null in Phase 1 | Reserved; must remain null unless Level 3 is implemented. |

Existing validation cases without these fields remain valid. The writer should
emit the new fields only when the corresponding scenario/source metadata is
provided, or emit null/default values where backward compatibility is clearer.

## Allowed Probability Modes

| Mode | Phase 1 status | Meaning |
| --- | --- | --- |
| `unweighted_diagnostic` | supported label | Trajectory-count diagnostic with no probability claim. |
| `sampling_weighted_conditional` | implementation target | Conditional weighted map normalized over the filtered/scenario set. |
| `physical_probability` | schema-only in Phase 1 | Conditional physical probability without temporal frequency. |
| `annual_frequency` | rejected unless Level 3 fields exist | Annualized frequency or probability requiring temporal/source-frequency inputs. |

Compatibility note: the existing hazard-layer prototype uses
`hazard_probability.probability_model: sampling_weighted`. Phase 1 should keep
that accepted as a builder-internal alias only when the map manifest labels the
map package as `sampling_weighted_conditional`.

## Normalization Rules

Allowed `normalization_scope` values:

| Scope | Meaning | Phase 1 status |
| --- | --- | --- |
| `conditioned_on_filter` | Denominator is the total weight/probability after filters. | implemented in current weighted prototype; keep as default for Level 2. |
| `conditioned_on_scenario` | Denominator is the selected scenario row or scenario set. | define in schema; implementation may alias to `conditioned_on_filter` when filters equal scenario selection. |
| `absolute_probability_mass` | Values retain absolute physical probability mass. | schema-only until `physical_probability`. |
| `annual_frequency_sum` | Values are annual frequency sums, not probabilities. | Level 3 only; reject in Phase 1 code paths. |

Phase 1 must ensure that output layer names, manifest fields, and documentation
state whether a map is a diagnostic fraction, a conditional weighted
probability, a physical probability, or an annual frequency.

## Strict Validation Rules

General map-package validation:

- `map_product_id` must be nonempty and stable.
- `probability_mode` must be one of the allowed modes.
- Level 1+ products must provide `source_zone_metadata_path`.
- Scenario ids, source-zone ids, model-configuration ids, and release-cell ids
  must be deterministic strings.
- Existing unweighted diagnostic hazard layers remain valid without a map
  package.

Mode-specific validation:

- `unweighted_diagnostic`
  - must not be labelled probabilistic;
  - must not contain physical probability or annual-frequency layer names;
  - may omit source-zone metadata for Level 0 diagnostics.
- `sampling_weighted_conditional`
  - requires `scenario_table_path` or trajectory metadata with `scenario_id`;
  - requires nonnegative finite `sampling_weight`;
  - requires positive total filtered weight;
  - requires `normalization_scope` of `conditioned_on_filter` or
    `conditioned_on_scenario`;
  - must not read `release_probability`, `scenario_probability`, or
    `annual_frequency_per_year` as weights unless a later mode explicitly says
    so.
- `physical_probability`
  - requires explicit `scenario_probability` or `release_probability` fields;
  - requires a normalization rule;
  - must not use annual language or units;
  - should remain schema-only until tests and manifest semantics are reviewed.
- `annual_frequency`
  - requires temporal/source-frequency fields such as
    `annual_release_frequency_per_year`, `annual_frequency_per_year`, or a
    named frequency model;
  - requires units such as `1/year` in layer metadata;
  - must fail in Phase 1 implementation if those fields are missing;
  - should not be exposed in generated maps until Level 3.

Ambiguity checks:

- reject configurations with multiple active probability columns and no
  explicit `probability_mode`;
- reject negative weights or probabilities;
- reject missing metadata joins for any trajectory id used in weighted layers;
- reject Level 1+ packages whose source-zone id in trajectory metadata does not
  match the source-zone sidecar or scenario table;
- reject annualized labels when all frequency fields are null.

## Output And Manifest Additions

### Map Package Manifest

`map_package_manifest_v1` should be a small JSON sidecar that references
existing `run_manifest_v1` files rather than duplicating all run details.

Minimal structure:

```json
{
  "schema_version": "map_package_manifest_v1",
  "map_product_id": "swiss_pilot_demo_conditioned_on_zone_a",
  "probability_mode": "sampling_weighted_conditional",
  "normalization_scope": "conditioned_on_filter",
  "source_zone_metadata_path": "validation/results/.../source_zone.yaml",
  "scenario_table_path": "validation/results/.../scenario_table.csv",
  "hazard_manifest_paths": ["hazard/results/.../manifest.json"],
  "layer_semantics": [
    {
      "layer_name": "weighted_reach_probability",
      "units": "dimensionless",
      "conditioned_on": ["source_zone_id=zone_a"],
      "is_annualized": false
    }
  ],
  "validation_context": [
    "docs/public_benchmark_results_baseline.md"
  ],
  "limitations": [
    "Research diagnostic; not operational hazard validation.",
    "No annual frequency model."
  ]
}
```

### Hazard Manifest Additions

Extend `run_manifest_v1` hazard sections additively:

- `map_product_id`;
- `probability_mode`;
- `normalization_scope`;
- `source_zone_id`;
- `source_zone_metadata_path`;
- `scenario_table_path`;
- `scenario_ids`;
- `total_sampling_weight`;
- `total_filtered_weight`;
- `annual_frequency_fields_present: false` in Phase 1 unless Level 3 is added;
- `layer_semantics` entries with units and conditioning.

### Source-Zone Metadata Format

Keep YAML for small fixtures:

```yaml
schema_version: source_zone_metadata_v1
source_zone_id: zone_a
crs_epsg: 2056
vertical_datum: LN02
geometry:
  type: polygon
  vertices:
    - [2696000.0, 1167000.0]
release_sampling_policy:
  mode: deterministic_grid
  seed: 34014
  release_count: 100
provenance:
  source: documented slope/geology workflow
  license: project fixture
annual_release_frequency_per_year: null
```

### Scenario Table Format

Use CSV first, because it is easy to inspect and join:

```csv
scenario_id,source_zone_id,block_scenario_id,block_size_class,block_shape_class,terrain_material_assumption_id,model_configuration_id,sampling_weight,release_probability,scenario_probability,annual_frequency_per_year
scenario_a,zone_a,block_small,s10_30cm,sphere,uniform_global_parameters,translational_v0,1.0,,,
```

Future Parquet/Arrow can mirror this schema after semantics stabilize.

## Example Packages

### Minimal Level 1 Conditional Package

Use case:

- one source zone;
- deterministic release grid;
- one block scenario;
- one model configuration;
- all trajectories equally weighted.

Expected labels:

- `probability_mode: unweighted_diagnostic` for existing diagnostic output, or
  `probability_mode: sampling_weighted_conditional` with all weights `1.0` when
  the map package is explicitly conditional;
- `normalization_scope: conditioned_on_scenario`;
- no physical probability fields;
- no annual-frequency fields.

Success condition:

- reviewer can identify source zone, release-cell ids, block scenario, model
  configuration, seed policy, and output grid from manifests.

### Minimal Level 2 Sampling-Weighted Package

Use case:

- one or more source zones;
- multiple block-size classes or model configurations;
- sampling weights correct stratified sampling or express a documented scenario
  design;
- no annual frequency.

Expected labels:

- `probability_mode: sampling_weighted_conditional`;
- `normalization_scope: conditioned_on_filter`;
- `total_sampling_weight` and `total_filtered_weight` recorded;
- weighted and unweighted layers written side by side.

Success condition:

- weighted layers match unweighted layers when all `sampling_weight = 1.0`;
- nonuniform weights change only weighted layers;
- annual-frequency labels are absent.

## Implementation Slices

### Slice A: Documentation And Schema Only

Deliverables:

- this plan;
- schema examples for source-zone metadata, scenario table, and map-package
  manifest;
- doc updates linking Phase 1 from `docs/README.md`.

No Rust/Python behavior changes.

### Slice B: Parser And Validation

Deliverables:

- parser for `source_zone_metadata_v1`;
- parser for `scenario_table_v1`;
- parser or validator for `map_package_manifest_v1`;
- clear errors for missing Level 1+ source-zone metadata, unsupported probability
  modes, invalid annual-frequency labels, negative weights, and inconsistent
  source-zone/scenario ids.

Implementation status: complete in `src/probabilistic.rs` with focused Rust
tests in `tests/probabilistic_phase1.rs`. This slice is deliberately isolated;
no validation runner, simulation, or hazard-layer numerical behavior uses the
new metadata unless later slices explicitly opt in.

### Slice C: Scenario Propagation

Deliverables:

- additive trajectory metadata fields for `map_product_id`, `release_cell_id`,
  `block_scenario_id`, block class fields, terrain/material assumption id, and
  model configuration id;
- deterministic id propagation from release-zone/scenario metadata;
- manifest summaries of scenario ids and source-zone ids.

Existing validation cases remain unchanged unless they opt in.

Implementation status: complete. Validation cases can opt in with a
`probabilistic_metadata` block that references `source_zone_metadata_v1`,
`scenario_table_v1`, `map_product_id`, `probability_mode`,
`normalization_scope`, and optionally `scenario_id`. The runner validates those
sidecars through the Slice B parsers before simulation output is written. If the
scenario table has multiple rows, `scenario_id` is required; no row is selected
by guessing. The selected scenario row is propagated only into
`trajectory_metadata_table_v1` and its run-manifest summary. Simulation physics,
contact models, default behavior, and hazard-layer numerical outputs are
unchanged.

### Slice D: Hazard Normalization And Manifest Labelling

Deliverables:

- map package writer for hazard outputs;
- hazard manifest additions for probability mode, normalization scope, source
  zone, scenario ids, weights, layer semantics, and annual-frequency absence;
- builder compatibility from existing `sampling_weighted` config to the
  external `sampling_weighted_conditional` map label.

Existing unweighted layers remain unchanged.

Implementation status: complete. Hazard runs can opt in through
`hazard_map_package` in the case YAML or through CLI flags. When map-package
metadata is absent, default unweighted diagnostic hazard outputs and manifests
remain backward-compatible and are not relabelled probabilistic. When present,
the builder validates the source-zone sidecar, scenario table, scenario/source
joins, and Phase 1 probability labels before writing hazard products. Only
manifest/package metadata changes; raster values are unchanged.

### Slice E: Tests And Smoke Example

Deliverables:

- tiny Level 1 conditional source-zone fixture;
- tiny Level 2 sampling-weighted scenario fixture;
- expected map package manifests;
- focused tests for parser, joins, labels, validation failures, and backward
  compatibility.

No large raw data or generated outputs are committed.

Implementation status: complete. The smoke fixture demonstrates the full Phase
1 path from validated source-zone/scenario metadata through trajectory metadata
propagation and labelled hazard package writing. It is explicitly a CI-safe
semantics fixture, not a benchmark, calibration case, scientific validation
result, or operational hazard product.

## Required Tests

Parser and validation tests:

- valid `source_zone_metadata_v1` with EPSG:2056/LN02 and deterministic release
  policy;
- valid `scenario_table_v1` for a Level 1 conditional package;
- valid `scenario_table_v1` for a Level 2 sampling-weighted package;
- invalid `annual_frequency` without `annual_release_frequency_per_year` or
  equivalent temporal/source-frequency fields;
- invalid `physical_probability` without explicit probability columns;
- invalid negative `sampling_weight`;
- invalid missing source-zone metadata for Level 1+ products;
- invalid mismatch between scenario-table `source_zone_id` and source-zone
  sidecar id.

Propagation tests:

- deterministic `scenario_id`, `source_zone_id`, and `release_cell_id`
  propagation into trajectory metadata;
- backward compatibility for existing validation cases without scenario tables;
- old unweighted diagnostic hazard layers unchanged.

Hazard-layer tests:

- weighted equals unweighted when all weights are `1.0`;
- nonuniform weights affect only weighted layers;
- weighted layers are labelled `sampling_weighted_conditional` in the map
  package manifest;
- unweighted diagnostic layers are not labelled annual or physical probability;
- annual-frequency mode fails until Level 3 fields are supported.

## Acceptance Criteria For Phase 1

Phase 1 is complete when:

- a reviewer can identify what every Level 1/2 map layer is conditioned on;
- source-zone, release-cell, scenario, block, terrain/material, and model
  configuration ids are stable and manifest-backed;
- sampling weights are auditable and cannot be confused with annual frequency;
- existing validation and diagnostic hazard workflows remain unchanged by
  default;
- annual-frequency labels fail unless temporal/source-frequency fields are
  present and explicitly supported by a later phase.

## Out Of Scope

- annualized hazard layers;
- source-frequency calibration;
- block-size probability distribution sampling;
- active shape-contact physics;
- terrain/material calibration;
- regional tiling and reducer orchestration;
- GeoTIFF/COG productization beyond schema references;
- exposure, vulnerability, and risk mapping;
- operational hazard-map validity claims.

## Phase 1 Closure And Next Action

Phase 1 Slices B-E are complete. The implemented path validates source-zone,
scenario-table, and map-package metadata, propagates scenario/source-zone labels
into trajectory metadata, labels hazard manifests and package manifests, and
exercises the full flow with a CI-safe smoke case. Existing diagnostic and
unweighted workflows remain unchanged by default.

The recommended next implementation slice after Phase 1 was **Phase 2A:
GIS-ready GeoTIFF export for existing labelled hazard rasters**. The first
Phase 2A slice adds value-preserving GeoTIFF output while leaving COG-specific
compression, tiling, and overview guarantees deferred until a verified COG
writer is selected.
