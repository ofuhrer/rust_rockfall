# Probabilistic Trajectory Metadata Design

Status: partially implemented. `trajectory_metadata_table_v1` is implemented as
an opt-in CSV sidecar for validation/verification cases via
`outputs.trajectory_metadata_csv`, and validation-written trajectory and
impact-event CSVs carry `trajectory_id`. The metadata sidecar includes
unweighted probability semantics, `sampling_weight = 1.0`, and reserved null
physical-probability fields. The hazard-layer builder now supports opt-in
sampling-weighted conditional reach and exceedance maps using
`hazard_probability.probability_model: sampling_weighted`. Physical probability
models, annual frequencies, block-size sampling, Parquet/Arrow output, new
physics, and validation semantic changes are not implemented.

## Purpose

The current hazard-layer workflow treats all simulated trajectories equally.
That is appropriate for deterministic verification, small validation subsets,
and early diagnostic hazard maps. Future probabilistic hazard maps need an
explicit way to carry release metadata, block metadata, scenario identity, and
probability or sampling-weight information from simulation outputs into
hazard-layer post-processing.

This design defines the metadata contract that should be established before
implementing batched Parquet/Arrow trajectory and impact-event outputs. The
goal is to avoid retrofitting probability semantics after large output tables
already exist.

## Design Principles

- Preserve the current unweighted behavior by default.
- Treat metadata and weights as orchestration/output concerns, not simulation
  physics.
- Keep sampling weights separate from physical occurrence probabilities.
- Make the denominator and normalization convention explicit for every
  weighted hazard layer.
- Keep validation cases valid even when they do not provide probabilities.
- Prefer one source-of-truth metadata table, with selected denormalized fields
  in high-volume tables only when needed for efficient hazard accumulation.

## Per-Trajectory Metadata Schema

The proposed schema version is `trajectory_metadata_table_v1`. One row
describes one simulated trajectory.

Required identity fields:

| Field | Type | Meaning |
|---|---|---|
| `trajectory_id` | integer or string | Stable trajectory identifier used by trajectory samples, impact events, and deposition outputs. |
| `release_id` | string | Identifier for the sampled release point or release draw. |
| `source_zone_id` | string | Identifier for the source area or release-zone polygon. |
| `scenario_id` | string | Scenario or case identifier, for example a validation case or hazard-map scenario. |

Required release fields:

| Field | Type | Meaning |
|---|---|---|
| `release_x_m` | float | Release x coordinate in the case coordinate reference system. |
| `release_y_m` | float | Release y coordinate in the case coordinate reference system. |
| `release_z_m` | float | Release elevation in metres. |
| `release_crs_epsg` | integer or null | EPSG code when coordinates are geospatial. |
| `release_vertical_datum` | string or null | Vertical datum, if known. |

Optional initial-condition fields:

| Field | Type | Meaning |
|---|---|---|
| `release_vx_mps` | float | Initial x velocity. |
| `release_vy_mps` | float | Initial y velocity. |
| `release_vz_mps` | float | Initial z velocity. |

Probability and weighting fields:

| Field | Type | Meaning |
|---|---|---|
| `release_probability` | float or null | Physical probability mass assigned to the release draw or source-zone sample, if known. |
| `sampling_weight` | float | Monte Carlo estimator weight. Defaults to `1.0`. |
| `trajectory_probability` | float or null | Physical probability assigned to this trajectory after combining release, scenario, and block probabilities, if explicitly defined. |
| `event_frequency_per_year` | float or null | Annualized event frequency contribution, if the scenario has a frequency model. |
| `return_period_years` | float or null | Return period associated with the scenario, if applicable. |
| `probability_model` | string | Semantics of probability fields, such as `unweighted`, `sampling_weighted`, `physical_probability`, or `annual_frequency`. |

Block fields:

| Field | Type | Meaning |
|---|---|---|
| `block_diameter_m` | float or null | Block diameter when a spherical equivalent is used. |
| `block_radius_m` | float or null | Block radius used by the current model. |
| `block_mass_kg` | float or null | Block mass. |
| `block_density_kgpm3` | float or null | Block density. |
| `shape_class` | string | Placeholder for future shape categories. Use `sphere` for current spherical runs. |

Run provenance fields:

| Field | Type | Meaning |
|---|---|---|
| `case_id` | string | Verification, validation, calibration, or hazard case id. |
| `run_id` | string | Manifest/run identifier. |
| `parameter_set_id` | string or null | Parameter set identifier if multiple model configurations are compared. |
| `random_seed` | integer or null | Trajectory-specific seed, if available. |
| `trajectory_index` | integer | Stable zero-based or one-based index within the run, as documented by the writer. |
| `metadata_notes` | string or null | Human-readable notes for fixtures or unusual assumptions. |

Default unweighted rows should use:

- `sampling_weight = 1.0`
- `release_probability = null`
- `trajectory_probability = null`
- `event_frequency_per_year = null`
- `probability_model = "unweighted"`

## Output Propagation

### Current CSV Outputs

Current per-trajectory CSV files can remain unchanged except for preserving or
adding a stable `trajectory_id` where the existing output mode already carries
one. The metadata should be written as a separate table, for example
`outputs.trajectory_metadata_csv`, so high-frequency trajectory samples do not
duplicate release and block metadata on every row.

Trajectory sample rows link to metadata by `trajectory_id`.

Impact-event rows link to metadata by `trajectory_id`. Impact CSV files already
represent per-event diagnostics; they should not become the source of truth for
release probability or block properties.

Deposition outputs link to metadata by `trajectory_id`. If a deposition summary
contains one row per trajectory, weighted deposition density can be computed by
joining the deposition row to the metadata row and summing the selected weight.

### Future Parquet/Arrow Outputs

The recommended columnar layout is:

- `trajectory_metadata_table_v1`: one row per trajectory, source of truth for
  release, block, scenario, and probability metadata.
- `trajectory_samples_table_v1`: one row per trajectory sample, including
  `trajectory_id` and sample-state columns.
- `impact_events_table_v1`: one row per impact event, including
  `trajectory_id` and impact diagnostics.
- `deposition_table_v1`: one row per final trajectory deposition state, including
  `trajectory_id`.

The metadata table should be stored separately. For efficient hazard-layer
scans, selected numeric fields may also be denormalized into high-volume tables:

- `sampling_weight`
- `trajectory_probability`
- `event_frequency_per_year`
- `source_zone_id`
- `scenario_id`
- `block_mass_kg`
- `block_diameter_m`

Denormalized fields must be declared in the manifest as copies from
`trajectory_metadata_table_v1`, not as independent probability definitions.

## Hazard-Map Semantics

### Unweighted Reach Probability

This is the current default interpretation. For a cell:

```text
unweighted_reach_probability =
  number of considered trajectories that reached the cell
  / number of considered trajectories
```

This is a sample occupancy fraction. It is useful for diagnostics and ensemble
comparison, but it is not a physical occurrence probability unless the ensemble
sampling design makes every trajectory equiprobable.

### Weighted Reach Probability

For a chosen weight column `w`:

```text
weighted_reach_probability =
  sum(w_i for trajectories that reached the cell)
  / sum(w_i for considered trajectories)
```

The denominator must use the same filters as the numerator. By default,
normalization should be conditioned on the filtered set, not on the full
unfiltered scenario set.

### Weighted Exceedance Probability

For a threshold such as kinetic energy or jump height:

```text
weighted_exceedance_probability =
  sum(w_i for trajectories exceeding the threshold in the cell)
  / sum(w_i for considered trajectories)
```

If the weight column is an annual frequency rather than a dimensionless weight,
the output should be named and documented as an exceedance frequency layer, not
as a probability layer.

### Conditional Hazard Maps

Hazard maps may be filtered by:

- `source_zone_id`
- `scenario_id`
- block mass range
- block diameter range
- `shape_class`
- parameter set

The manifest must record whether each output layer is normalized:

- after filtering, so values are conditional on the selected subset; or
- before filtering, so values retain absolute probability mass from the full
  scenario definition.

The default for diagnostic filtering should be `conditioned_on_filter`.

### Sampling Weights vs Physical Probabilities

`sampling_weight` is an estimator correction for how trajectories were sampled.
It does not by itself assert how often rockfall occurs.

`release_probability`, `trajectory_probability`, and
`event_frequency_per_year` are physical occurrence quantities only when they are
derived from a documented scenario model or calibration workflow.

Hazard-layer code must not multiply `sampling_weight` by physical probability
fields unless the selected probability mode explicitly defines that operation.

## Manifest and Schema Additions

Future manifests should add a metadata/probability section without changing
existing diagnostics:

```yaml
trajectory_metadata:
  schema_version: trajectory_metadata_table_v1
  path: path/to/trajectory_metadata.csv
  row_count: 1000
  trajectory_id_column: trajectory_id
  probability_model: unweighted
  total_sampling_weight: 1000.0
  total_release_probability: null
  total_trajectory_probability: null
  total_event_frequency_per_year: null
```

Hazard-layer manifests record probability semantics when weighted maps are
enabled:

```yaml
hazard_probability:
  probability_model: sampling_weighted
  weight_column: sampling_weight
  normalization_convention: conditioned_on_filter
  filters:
    source_zone_ids: []
    scenario_ids: []
    block_mass_kg_min: null
    block_mass_kg_max: null
  total_input_weight: 1000.0
  total_filtered_weight: 1000.0
  generated_weighted_layer_names:
    - weighted_reach_probability
```

Each output layer should record:

```yaml
layer_probability_semantics:
  layer_name: reach_probability
  numerator: trajectories_reaching_cell
  denominator: considered_trajectories
  weighted: false
  units: fraction
```

## Compatibility

Existing validation, verification, and synthetic benchmark cases do not need
probability fields. If no metadata table is provided, hazard-layer generation
must behave exactly as it does today:

- each trajectory has implicit `sampling_weight = 1.0`;
- reach probability is an unweighted occupancy fraction;
- deposition density is an unweighted count or normalized count;
- exceedance layers are unweighted;
- no simulation physics or trajectory integration changes.

Probability-aware outputs should be opt-in. Missing probability metadata should
not cause existing validation cases to fail.

## Interaction With Columnar Output

The columnar-output design should reserve probability-aware identifiers and
weight columns before implementation:

`impact_events_table_v1` should include:

- `trajectory_id`
- `impact_index`
- event position and timing fields
- impact diagnostics
- optionally denormalized `sampling_weight`
- optionally denormalized `trajectory_probability`
- optionally denormalized `event_frequency_per_year`

`trajectory_samples_table_v1` should include:

- `trajectory_id`
- sample time and state fields
- optionally denormalized `sampling_weight`
- optionally denormalized `trajectory_probability`
- optionally denormalized `event_frequency_per_year`

`trajectory_metadata_table_v1` should remain the source of truth for all release,
block, scenario, and probability metadata. Hazard-layer post-processing can then
choose between:

- joining event/sample batches to metadata by `trajectory_id`; or
- reading denormalized weight columns when the manifest confirms they were
  copied from the metadata table.

For early Parquet/Arrow implementation, denormalizing the selected weight fields
is acceptable because it avoids repeated joins during streaming raster
accumulation. The manifest must still identify the metadata table and probability
mode used to create those columns.

## Risks

Double-counting probabilities:

If `sampling_weight`, `release_probability`, and `trajectory_probability` are
all present, downstream code may multiply fields incorrectly. Mitigation:
require an explicit `probability_mode` and a single selected weight/probability
column per hazard run.

Confusing sampling weights with physical probability:

Equal Monte Carlo weights produce ensemble statistics, not event probabilities.
Mitigation: default to `unweighted` and require docs/manifests to label physical
probability layers explicitly.

Filtering before versus after normalization:

A source-zone-filtered map can mean either “probability conditional on this
source zone” or “absolute contribution from this source zone.” Mitigation:
record `normalization_convention` on every hazard run and layer.

Illustrative fixture probabilities:

Small checked-in fixtures may use artificial probabilities for tests. Mitigation:
mark fixture probabilities as illustrative and never reuse them as calibrated
hazard probabilities.

Probability leakage into validation:

Validation metrics should not silently become weighted unless the validation
case explicitly requests that interpretation. Mitigation: preserve unweighted
validation behavior by default.

## Recommended Implementation Path

### Implemented Minimal First Step

Before implementing Parquet/Arrow, the repository now supports an opt-in
metadata sidecar for current CSV workflows:

```yaml
outputs:
  trajectory_metadata_csv: validation/results/example/trajectory_metadata.csv
```

The current writer produces one row per trajectory with:

- `trajectory_id`
- `release_id`
- `source_zone_id`
- release coordinates
- null `release_probability`
- `block_radius_m`
- `block_mass_kg`
- optional `block_density_kgpm3`
- `shape_class = "sphere"`
- `scenario_id`
- `sampling_weight = 1.0`
- `probability_model = "unweighted"`

The manifest records the metadata schema version, row count, total sampling
weight, probability model, probability semantics, normalization convention, and
path. Hazard-layer code continues using unweighted behavior unless a case
explicitly configures `hazard_probability.probability_model:
sampling_weighted`.

### Changes Needed Before Parquet/Arrow

- Reserve `trajectory_id`, `release_id`, `source_zone_id`, `scenario_id`, and
  probability/weight fields in the columnar schema.
- Decide which probability fields may be denormalized into
  `impact_events_table_v1` and `trajectory_samples_table_v1`.
- Add manifest fields for metadata schema version and probability semantics.
- Add tests that confirm existing cases without metadata remain unweighted.
- Add tests that reject ambiguous probability modes, for example selecting both
  `sampling_weight` and `trajectory_probability` without an explicit rule.

### Implemented Sampling-Weighted Hazard-Layer Prototype

The implemented opt-in hazard configuration is:

```yaml
hazard_probability:
  probability_model: sampling_weighted
  metadata_path: validation/results/example/trajectory_metadata.csv
  weight_column: sampling_weight
  normalization_convention: conditioned_on_filter
  filters:
    source_zone_ids: ["zone_a"]
    scenario_ids: []
    block_mass_kg_min: 100.0
    block_mass_kg_max: 1000.0
```

The current prototype writes weighted versions of trajectory-derived
conditional layers:

- weighted reach probability
- weighted kinetic-energy exceedance probability
- weighted jump-height exceedance probability
- weighted velocity exceedance probability

Weighted deposition density, annualized frequency layers, and physical
occurrence-probability layers remain future work. They should be added only
after the denominator, source-frequency inputs, and validation interpretation
are scientifically defined and documented.
