# Probabilistic Scenario Model Design

Status: scenario design with a first post-processing prototype. The hazard-layer
builder now supports opt-in `sampling_weighted` conditional reach and
exceedance maps using `trajectory_metadata_table_v1`. This document does not
implement release-frequency calibration, block-size sampling, Parquet/Arrow
output, annual-frequency maps, physical source probabilities, or
simulation-physics changes.

## Purpose

Future probabilistic hazard maps need scenario-level semantics before physical
probability or annual-frequency post-processing is implemented. The current simulator can already run
deterministic ensembles, write `trajectory_metadata_table_v1`, and build
unweighted diagnostic hazard layers, plus opt-in sampling-weighted conditional
layers. The remaining missing contract is how a set of trajectories relates to
a source-zone scenario, a block scenario, a model configuration, and a physical
probability or frequency interpretation.

This document defines that contract so weighted hazard-layer implementation can
follow without ambiguity.

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

- polygon or multipolygon in the case CRS;
- EPSG code and vertical datum;
- source-zone id;
- provenance, source, and license metadata;
- optional slope, elevation, or terrain-class filters when those are explicitly
  documented.

The current release-zone pilot already provides deterministic polygon sampling
for small fixtures. That is sufficient for conditional source-zone experiments.

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
