# Sampling-Weighted Hazard-Layer Review

Status: review of `v0.6.0` sampling-weighted hazard-layer prototype. This
document does not introduce new physics, new probability models, or new output
formats.

## Current Behavior Summary

The hazard-layer builder remains a post-processing tool. It consumes existing
trajectory, deposition, and impact-event CSV outputs and never calls or changes
the simulation kernel.

Default behavior is unchanged:

- cases without `hazard_probability` produce only the existing unweighted
  reach, deposition, maximum-energy, jump-height, impact-density, and optional
  unweighted exceedance layers;
- no metadata CSV is required for unweighted hazard-layer generation;
- unweighted layers retain their previous names and normalization;
- validation and verification pass/fail semantics remain unweighted.

Weighted outputs appear only when a case explicitly configures:

```yaml
hazard_probability:
  probability_model: sampling_weighted
  metadata_path: path/to/trajectory_metadata.csv
  weight_column: sampling_weight
  normalization_convention: conditioned_on_filter
  filters:
    source_zone_ids: []
    scenario_ids: []
    block_mass_kg_min: null
    block_mass_kg_max: null
```

When enabled, the builder writes these additional trajectory-derived layers:

- `weighted_reach_probability`;
- `weighted_kinetic_energy_exceedance_<threshold>j`;
- `weighted_jump_height_exceedance_<threshold>m`;
- `weighted_velocity_exceedance_<threshold>mps`.

The existing unweighted layers are still written alongside the weighted layers.

## Probability Semantics

The current prototype is a conditional sampling-weighted estimator, not a full
physical hazard-probability model.

For a filtered trajectory set with weights `w_i`, weighted reach is:

```text
sum(w_i for trajectories reaching the cell) / sum(w_i for filtered trajectories)
```

Weighted exceedance layers use the same denominator. A trajectory contributes at
most once per cell and threshold, matching the unweighted exceedance semantics.

The only supported probability mode is `sampling_weighted`. The only supported
normalization convention is `conditioned_on_filter`. The only supported weight
column is `sampling_weight`.

The layer names are intentionally probability-like, not frequency-like:

- `weighted_*_probability` means a dimensionless conditional fraction;
- no layer name uses `annual`, `frequency`, `return_period`, or `per_year`;
- manifest metadata records `probability_model`, `weight_column`,
  `normalization_convention`, filters, total input weight, total filtered
  weight, and generated weighted layer names.

## Validation Coverage

The focused hazard-layer tests cover the key semantic contracts:

- weighted layers equal unweighted layers when all `sampling_weight` values are
  `1.0`;
- non-uniform weights change weighted reach and exceedance layers as expected;
- negative weights are rejected;
- missing trajectory metadata is rejected;
- filters by `source_zone_id` and block-mass range are applied deterministically;
- unweighted mode emits no weighted layers;
- plotted and no-plot modes preserve identical numerical core layers;
- hazard manifests include probability metadata when weighted layers are active.

The fixture `tests/fixtures/hazard/weighted_metadata.csv` is intentionally
small and illustrative. Its weights are not calibrated physical probabilities.

## Known Limitations

This is not yet a true probabilistic hazard map in the physical or annualized
sense. It is a conditional sampling-weighted map over the supplied trajectory
set.

Still missing for physical or annual probability:

- documented source-zone probability or annual release-frequency inputs;
- block-size or block-mass population probabilities;
- a scenario model that combines source, block, parameter-set, and model-form
  probabilities without double counting;
- calibrated or otherwise defensible occurrence rates;
- annual-frequency layer names, units, and manifest semantics;
- validation methods for probabilistic inputs, not only trajectory outputs;
- geospatial production metadata and standard raster outputs for operational
  GIS workflows.

Current weighted layers are trajectory-derived only. Weighted deposition density
and weighted significant-impact density are not implemented. That is acceptable
for the first prototype because deposition and impact weighting need careful
join and denominator semantics, especially before batched impact-event output is
introduced.

The metadata CSV may contain physical-probability fields, but this prototype
does not read or combine them. This avoids hidden probability multiplication.

## Risks Of Misuse

The main misuse risk is interpreting `sampling_weight` as a physical occurrence
probability. The current documentation and manifest fields reduce this risk by
requiring `sampling_weighted` and `conditioned_on_filter`, but users still need
to understand that these layers are conditional diagnostics unless a physical
scenario model is supplied later.

Other risks:

- using illustrative fixture weights as calibrated probabilities;
- comparing filtered weighted maps without checking the filtered denominator;
- mixing validation outputs and hazard-pilot outputs without verifying
  `trajectory_id` metadata joins;
- assuming weighted reach is annual reach probability;
- extending weighted maps to deposition or impact density before the output
  model can carry metadata efficiently and audibly.

## Answers To Key Questions

### Is This Now A True Probabilistic Hazard Map?

No. It is a first probabilistic post-processing prototype: a
sampling-weighted conditional map over a specified trajectory ensemble. It is
useful for testing denominator, metadata, filtering, and manifest semantics. It
does not encode physical occurrence probability or annual frequency.

### What Is Still Missing For Physical Or Annual Probability?

Physical or annual probability requires source-zone release probability or
annual frequency, block-population probabilities, scenario composition rules,
time-horizon semantics, calibrated or documented probability inputs, and layer
names/units that distinguish conditional probability from annual frequency.
Those inputs should be validated before any `annual_*` or `*_frequency` layers
are added.

### Should The Next Engineering Step Be Parquet Impact-Event Output?

This has now been implemented as an opt-in `outputs.ensemble_impact_events_parquet`
sidecar while preserving existing CSV impact-event outputs. The columnar table
uses `impact_events_table_v1`, carries stable `trajectory_id`, and is readable by
the hazard-layer builder for unweighted significant-impact density parity with
the CSV path.

### Should Weighted Maps Be Extended Before Parquet?

Only minimally. It is reasonable to add small validation safeguards or manifest
fields if a clear ambiguity is found. Weighted deposition, weighted impact
density, physical probabilities, and annual frequencies should wait until the
columnar output and scenario contracts are stable enough to avoid expensive CSV
joins and ambiguous denominators.

### What Should Remain Deferred?

Defer:

- annual-frequency maps;
- physical source or trajectory probability maps;
- block-size probability sampling;
- weighted deposition and weighted significant-impact density;
- model-form uncertainty weighting;
- exposure, vulnerability, and risk layers;
- operational GIS outputs and claims of operational validity.

## Recommended Next Step

Keep weighted reach and exceedance semantics unchanged while gathering
benchmark evidence for the new Parquet impact-event path. After parity and
throughput are demonstrated, design weighted significant-impact density and
weighted deposition layers explicitly rather than inferring them from current
unweighted density denominators.
