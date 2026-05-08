# Probabilistic Scenario Model Design

Status: scenario design with a first post-processing prototype. The hazard-layer
builder now supports opt-in `sampling_weighted` conditional reach and
exceedance maps using `trajectory_metadata_table_v1`. This document does not
implement release-frequency calibration, block-size sampling, Parquet/Arrow
output, annual-frequency maps, physical source probabilities, or
simulation-physics changes.

## Purpose

Future probabilistic hazard maps need scenario-level semantics before physical
probability or annual-frequency post-processing is implemented. The current
simulator can already run deterministic ensembles, write
`trajectory_metadata_table_v1`, and build unweighted diagnostic hazard layers,
plus opt-in sampling-weighted conditional layers. The remaining future contract
is physical probability or annual frequency; those claims are inactive until a
future phase defines source-frequency evidence, probability inputs, validation,
and manifest support.

This document defines the scenario metadata contract. Current hazard-map
denominator, conditioning, language, and unsupported physical/annual claim
semantics are defined in `docs/hazard_map_semantics.md`.
The real-site pilot policy layer that freezes source-zone evidence,
deterministic release sampling, and representative block scenarios before
simulation is defined in `docs/source_zone_block_scenario_policy_v1.md`.
The future annual/physical source-frequency contract is controlled by
`docs/physical_source_frequency_design_gate.md`; that gate currently keeps the
prototype deferred and does not add runtime support.

## Scenario Identity

A probabilistic scenario should be identified independently from a validation
case file. A case may run one scenario, or a later orchestration layer may run
many scenarios.

Recommended fields:

| Field | Required | Meaning |
|---|---:|---|
| `scenario_id` | yes | Stable identifier for the hazard scenario being simulated. |
| `source_zone_id` | yes | Source-zone polygon or source-area identifier. |
| `parameter_set_id` | optional | Contact, terrain-class, roughness, scarring, or calibration parameter set. |
| `model_configuration_id` | optional | Model-form identifier, for example contact model and enabled optional physics. |
| `time_horizon_years` | optional | Time horizon for annual-frequency or exceedance-frequency products. |

For current unweighted validation and pilot runs, `scenario_id` may equal
`case_id`, `source_zone_id` may be `manual_release` or the release-zone metadata
id, and `time_horizon_years` should be omitted.

## Source-Zone Model

### Geometry

The source-zone model starts with geometry:

- polygon in the case CRS for current `source_zone_metadata_v1` and
  release-zone parser support;
- EPSG code and vertical datum;
- source-zone id;
- provenance, source, and license metadata;
- optional slope, elevation, or terrain-class filters when those are explicitly
  documented.

The current release-zone pilot already provides deterministic polygon sampling
for small fixtures. That is sufficient for conditional source-zone experiments.
Multipolygon source areas remain future design intent and are not parsed by the
current source-zone/release-zone fixture path.

### Source-Zone Semantics V1

Current source-zone semantics are intentionally narrow and metadata-driven.

- Geometry intent: current source zones are polygon source areas in the case
  CRS. Current checked-in fixtures and parser paths use small polygon sidecars
  only; multipolygon remains future design intent and must not be assumed
  parsed or supported by `source_zone_metadata_v1` or `release_zone.metadata_path`
  until an explicit schema/parser change adds it.
- Identity: `source_zone_id` must be stable across manifests, source-zone
  sidecars, scenario tables, and `trajectory_metadata_table_v1`. Generated
  release cells or release points should have deterministic `release_cell_id`
  values so reruns and reducers can join outputs without depending on execution
  order.
- Sampling semantics: release sampling is a numerical design for representing
  a source area. Equal grid samples, stratified samples, and sampling weights do
  not by themselves define physical release probability.
- Required provenance: source-zone sidecars should record CRS, vertical datum,
  source geometry provenance, source dataset or interpretation basis, license
  notes, preprocessing notes where applicable, and any manual interpretation
  caveats.
- Exclusions: current source-zone metadata does not implement national source
  derivation, a slope/geology/inventory release algorithm, annual source
  frequency, or physical source probability. Those may appear only in a future
  phase with explicit evidence and schema support. swisstopo terrain or context
  data are operational input geodata, not validation evidence by themselves.
  Source zones are diagnostic research inputs and must not be presented as
  operationally approved source areas.

### Source-Zone Derivation Evidence Levels V1

Source-zone evidence level describes how a source area was derived. It is a
metadata and interpretation label, not a validation result.

| Level | Meaning | Allowed claims | Disallowed claims |
|---|---|---|---|
| Level 0 | Manual or synthetic fixture source area for dry runs, schema tests, and debug workflows. | "synthetic fixture source area"; "manual debug source polygon"; "schema/provenance example" | "field-derived source zone"; "validated source area"; "annual source model"; "physical release probability" |
| Level 1 | Operational-input source area backed by CRS/provenance metadata, terrain context, or manual real-site interpretation. | "diagnostic real-site source area"; "CRS/provenance-backed input geometry"; "suitable for local review only" | "validation evidence"; "inventory-supported derivation"; "operationally approved source area"; "frequency-supported source model" |
| Level 2 | Documented geomorphic or inventory-supported source-zone derivation using stated slope, geology, inventory, or expert-review criteria. Future/conditional until criteria and review records are implemented. | "documented candidate source-zone derivation" when criteria, data, and review are attached | "annual frequency"; "physical source probability"; "validated hazard source model" without a separate validation policy |
| Level 3 | Frequency/probability-supported source model. Future only; requires source-frequency or physical-probability evidence, temporal assumptions, and validation policy. | "frequency-supported source model" only after future schema, evidence, and validation gates exist | Any current claim that sampling weights, swisstopo terrain, or source polygons define physical or annual probability |

swisstopo terrain, imagery, buildings, or context layers are operational input
geodata. They can support provenance and interpretation at Level 1, but by
themselves they are not validation evidence, inventory evidence, source
frequency evidence, or physical-probability evidence.

### Release Density and Sampling Policy

Release sampling must distinguish the numerical sampling design from physical
release probability.

Examples:

- uniform samples over a polygon;
- grid samples over a polygon;
- deterministic stratified samples by terrain class or elevation band;
- future weighted samples where each release point represents a different area
  or source probability.

The sampling policy should record:

- sampling mode;
- requested and generated release count;
- seed;
- whether samples are equal-weight by construction;
- whether `sampling_weight` corrects nonuniform sampling.

### Probability and Frequency Placeholders

The source-zone schema should reserve, but not require, these fields:

| Field | Meaning |
|---|---|
| `source_zone_probability` | Physical probability mass for the source zone within a scenario, if defined. |
| `release_probability` | Physical probability for a sampled release point or release cell, if defined. |
| `annual_release_frequency_per_year` | Annualized release frequency for the source zone or release sample, if defined. |
| `probability_model` | Declares whether the fields are absent, sampling weights, physical probability, or annual frequency. |

Current checked-in fixtures should leave physical probability and annual
frequency fields empty. Artificial values should be marked illustrative and
excluded from validation semantics.

### Conditional-on-Release vs Annual-Frequency Maps

Conditional-on-release maps answer:

```text
Given this source zone, block scenario, and model configuration,
where do simulated trajectories reach or exceed a threshold?
```

Annual-frequency maps answer:

```text
Given an annual source frequency and probability model,
what is the annual frequency of reach or exceedance in each cell?
```

These products must not share the same layer name. A conditional map can use
fractions or probabilities conditioned on the scenario. An annual-frequency map
should use frequency units, for example `1/year`.

## Block Population Model

### Block-Scenario Semantics V1

Block-scenario metadata is an additive scenario contract, not physics behavior
by itself.

- Identity: `block_scenario_id` is the stable identifier for the block scenario
  represented by a scenario row and propagated trajectory metadata. It does not
  select contact physics or shape behavior by itself.
- Metadata fields: `block_scenario_id`, `block_size_class`,
  `block_shape_class`, and `sampling_weight` are current additive propagated
  scenario labels or weights. Representative scenario numeric fields such as
  `block_radius_m`, `block_mass_kg`, and optional `block_density_kgpm3` are
  schema-visible design and consistency fields; they must match or be
  reconciled with active case block values before they can be interpreted as
  simulated values. Current `trajectory_metadata_table_v1` numeric block
  radius, mass, and density columns reflect the active simulated case block or
  passive shape metadata, not scenario-row numeric overrides.
- Current physics boundary: the simulator still uses the active case spherical
  block unless a validation or probabilistic runner explicitly selects and
  propagates a scenario row into the case/run metadata. Passive shape labels do
  not imply active shape-dependent contact.
- Sampling weights: `sampling_weight` may weight scenario rows for conditional
  sampling-weighted hazard products. It is not physical block-population
  probability by itself.
- Inactive probability fields: release/source probability fields and annual
  frequency remain inactive for current Phase 1 unless future evidence and
  schema support are added.
- Exclusions: v1 does not define calibrated block-population distributions,
  fragmentation, shape-dependent contact, mid-trajectory block-size changes, or
  operational block-scenario approval.

### Fixed Block Scenario

The current simulator uses a spherical block with fixed radius and mass. A
probabilistic scenario may still be a fixed-block scenario. In that case every
trajectory metadata row should record:

- `block_radius_m`;
- `block_mass_kg`;
- optional `block_density_kgpm3`;
- `shape_class = "sphere"`;
- `sampling_weight = 1.0` unless the release sampling design says otherwise.

### Block-Size Classes

The next lightweight extension should be block-size classes, not continuous
block-size distributions. A block class can define:

- `block_class_id`;
- radius or diameter range;
- representative radius;
- mass or density;
- shape class placeholder;
- optional class probability, only when a documented block-population model
  exists.

### Future Block-Size Probability Distribution

A future distribution model may assign probabilities to block classes or sample
continuous block sizes. That should be treated as a scenario-model layer, not as
core physics. It must define whether probabilities are conditional on a release
event, source zone, event magnitude, or annual frequency.

### Shape Class Placeholder

`shape_class` is currently `sphere`. Future values may describe calibrated
shape categories or polyhedral models. Until shape physics exists, shape class
is metadata and filter context only.

## Probability Semantics

Allowed scenario probability modes should be explicit:

| Mode | Meaning | Current support |
|---|---|---|
| `unweighted` | Every trajectory contributes equally; current default. | implemented |
| `sampling_weighted` | Trajectories use Monte Carlo sampling weights; not physical occurrence probability by itself. | implemented for opt-in reach and trajectory-level exceedance maps |
| `conditional_probability` | Layer values are probabilities conditioned on the selected scenario/filter. | design only |
| `physical_probability` | Layer values use documented physical occurrence probabilities but are not annualized. | design only |
| `annual_frequency` | Layer values are annualized frequency contributions, usually in `1/year`. | design only |

`sampling_weighted` can be used to estimate a conditional probability if the
scenario defines the denominator. It should not be described as physical
probability unless the probability model states that interpretation explicitly.

### Scenario Consistency Checks V1

Current Phase 1 scenario consistency checks should keep joins, weights,
evidence roles, and deterministic identity explicit. Some checks are already
parser/test-enforced; others are documented review gates until future executors
or reducers add explicit enforcement.

Parser/test-enforced checks:

- Stable joins: `source_zone_id`, `scenario_id`, deterministic
  `release_cell_id`, and `block_scenario_id` where present must join
  consistently across source-zone metadata, scenario tables, selected
  `trajectory_metadata_table_v1` fields, and map-package manifests.
- Sampling weights: weighted scenario rows must use finite nonnegative
  `sampling_weight` values; sampling-weighted conditional products require a
  positive filtered total weight and must record the denominator and
  normalization scope where current map-package metadata supports it.
- Deferred probability failures: physical probability and annual frequency
  require explicit future evidence and schema support; current Phase 1 metadata
  must not infer them from sampling weights.

Documented review gates and future enforcement targets:

- Calibration/validation separation: scenario weights and source-zone choices
  used for hazard-map conditioning are not validation evidence and must not be
  treated as tuning results. swisstopo terrain or context inputs are
  operational geodata, not validation evidence by themselves.
- Deterministic seeding and reducer order: release sampling seeds, trajectory
  ids, release-cell ids, and reducer joins should make reruns and aggregated
  summaries independent of trajectory execution order. This is a documented
  design/review expectation for future executors and reducers, not current
  parser/test enforcement.
- Physics-boundary failures: representative block numeric scenario fields must
  not silently override the active case block, and shape labels must not imply
  shape-dependent contact.

### Executable Checks And Examples V1

Current executable coverage for source-zone and block-scenario v1 semantics is:

- `tests/probabilistic_phase1.rs` parses and validates
  `source_zone_metadata_v1`, `scenario_table_v1`, and
  `map_package_manifest_v1` fixtures under
  `tests/fixtures/probabilistic_phase1/`. It checks source-zone metadata,
  the fixture scenario-table rows named `scenario_level1.csv` and
  `scenario_level2_weighted.csv`, source-zone mismatch rejection, negative
  sampling-weight rejection, Phase 1 annual-frequency rejection, and incomplete
  `physical_probability` rejection.
- `tests/config_io_terrain.rs::probabilistic_scenario_metadata_propagates_to_trajectory_metadata`
  verifies deterministic propagation from source-zone/scenario metadata into
  `trajectory_metadata_table_v1`, including `map_product_id`,
  `source_zone_id`, `release_cell_id`, `scenario_id`, `block_scenario_id`,
  block size/shape labels, model labels, `sampling_weight`,
  `probability_mode`, `normalization_scope`, and empty
  `annual_frequency_per_year`.
- `tests/config_io_terrain.rs::probabilistic_phase1_smoke_case_propagates_scenario_metadata`
  verifies the smoke-case metadata path using
  `validation/cases/probabilistic_phase1_smoke.yaml` and examples under
  `validation/data/processed/probabilistic_phase1/`.

Current metadata examples are:

- `tests/fixtures/probabilistic_phase1/source_zone_valid.yaml`;
- `tests/fixtures/probabilistic_phase1/scenario_level1.csv`;
- `tests/fixtures/probabilistic_phase1/scenario_level2_weighted.csv`;
- `validation/data/processed/probabilistic_phase1/source_zone_smoke.yaml`;
- `validation/data/processed/probabilistic_phase1/scenario_table_smoke.csv`.

Executable tests currently enforce parser validity, deterministic metadata
joins, unsupported annual/physical probability boundaries, and selected
manifest/schema labels. Evidence-level assignment, geomorphic/inventory
derivation review, swisstopo-as-input-not-validation interpretation,
operational approval exclusion, and future Level 2/3 evidence quality remain
documented review gates until a later milestone adds explicit schemas and
checks.

## Normalization

The normalization convention must be recorded for every weighted or filtered
hazard run.

### `conditioned_on_filter`

The denominator is the total weight or probability mass after applying filters.
This is appropriate for maps such as:

```text
reach probability conditioned on source_zone_id = A and block_class_id = B
```

### `absolute_probability_mass`

The denominator or units preserve the full scenario probability mass. This is
appropriate when comparing the absolute contribution of one source zone or block
class to a larger scenario.

### `annual_frequency_sum`

The output value is a summed annual frequency contribution, not a normalized
probability. This is appropriate only when annual source-frequency inputs are
available and documented.

## Compatibility

### `trajectory_metadata_table_v1`

Compatible. It already carries:

- `trajectory_id`;
- `release_id`;
- `source_zone_id`;
- release coordinates;
- null `release_probability`;
- block radius, mass, and optional density;
- `shape_class`;
- `scenario_id`;
- `sampling_weight = 1.0`;
- `probability_model = "unweighted"`.

Before weighted maps, it should also support optional scenario/model fields when
needed:

- `parameter_set_id`;
- `model_configuration_id`;
- `time_horizon_years`;
- optional physical probability or annual frequency fields.

These should remain optional so existing validation cases continue to work.

### Future `impact_events_table_v1`

Compatible if every impact event includes `trajectory_id`. Future table writers
may denormalize selected probability fields such as `sampling_weight` or
`event_frequency_per_year`, but `trajectory_metadata_table_v1` should remain the
source of truth.

### Future Weighted Hazard Layers

Weighted hazard layers should require:

- a metadata table;
- a selected probability mode;
- a selected weight or probability column;
- a normalization convention;
- a clear filter set;
- manifest output recording all of the above.

The first weighted implementation supports conditional `sampling_weighted`
reach and trajectory-level exceedance layers before physical or
annual-frequency layers. The next probabilistic step should define source-zone
or scenario probability inputs before adding physical-probability or
annual-frequency rasters.
`validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml` records
the first design decision for those future inputs: source event rates, block
scenario probabilities, release-cell probabilities, source-zone overlap rules,
and uncertainty metadata are required before any annual or physical prototype
can proceed. Sampling weights remain conditional design weights unless replaced
by evidence-backed physical probabilities in a future schema.

### Current Unweighted Validation Behavior

Current validation remains unweighted. Missing probability fields must not cause
validation failures. Validation metrics should not silently become weighted
unless a case explicitly opts into a future weighted metric mode.

## Minimal Implementation Recommendation

### Add Next, If Any

The only low-complexity fields worth adding before weighted maps are optional
scenario identifiers:

- `parameter_set_id`;
- `model_configuration_id`;
- `time_horizon_years`.

These should be added only when a concrete writer or manifest consumer needs
them. The current metadata sidecar already has enough information for unweighted
joins and future filtering by source zone, mass, block size, and scenario.

### Keep Documentation-Only

Keep these concepts documentation-only for now:

- source-zone probability;
- annual release frequency;
- block-size probability distributions;
- annual frequency layers;
- physical occurrence probability layers;
- model-form uncertainty weighting.

### Implemented Checks for Sampling-Weighted Maps

The current sampling-weighted prototype rejects:

- any probability model other than `sampling_weighted`;
- any normalization convention other than `conditioned_on_filter`;
- any weight column other than `sampling_weight`;
- missing `trajectory_id` or `sampling_weight` metadata columns;
- duplicate trajectory IDs;
- negative or non-finite sampling weights;
- filters that remove all sampling weight;
- trajectory CSV inputs whose IDs do not resolve to metadata rows;
- trajectory CSV inputs excluded by active filters.

Additional checks are still needed before physical-probability or
annual-frequency layers, including units, denominator semantics, and explicit
source-frequency metadata.

## First Weighted Prototype

The implemented prototype uses:

- `probability_model: sampling_weighted`;
- `normalization_convention: conditioned_on_filter`;
- metadata source: `trajectory_metadata_table_v1`;
- output layers: weighted reach probability and weighted kinetic-energy,
  jump-height, and velocity exceedance probability;
- no annual frequency;
- no block-size sampling;
- no physical source-frequency interpretation.

This keeps the first probabilistic layer auditable while preserving default
unweighted validation and diagnostic workflows.
