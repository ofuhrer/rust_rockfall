# Hazard-Map Semantics And Interpretation Guide

Status: current interpretation guide for diagnostic and
sampling-weighted-conditional hazard-map products. This guide defines
interpretation semantics for hazard-map products only. It does not add physics,
introduce annual frequencies, change model defaults, validate operational
hazard maps, or add risk modelling.

## Scope

This document defines how to label and interpret hazard layers produced by the
existing post-processing workflow. It is not a calibration plan, source
frequency model, exposure/vulnerability model, or operational acceptance
standard.
Evidence and claim maturity labels are defined separately in
`docs/validation_maturity_framework.md`.

## Product Classes

Product classes are external or map-package `probability_mode` labels. They are
not always identical to builder configuration terms: current unweighted outputs
come from the default builder behavior, while sampling-weighted outputs are
enabled through `hazard_probability.probability_model: sampling_weighted` and
reported externally as `sampling_weighted_conditional`.

### Supported Now

- `unweighted_diagnostic`: trajectory-count or event-count diagnostic layers
  normalized by supplied model outputs. These layers support debugging,
  verification, and controlled review, but they do not carry physical source
  probabilities or annual frequencies.
- `sampling_weighted_conditional`: sampling-weighted layers normalized over a
  documented filtered scenario set. These layers can express the sampling design
  conditional on explicit source-zone, block-scenario, and trajectory filters.

### Unsupported For Current Claims

- `conditional_probability`: probability conditioned on a documented scenario
  denominator and filter set. This is aligned with
  `docs/probabilistic_scenario_model_design.md`, but it is design-only here and
  is not implemented as a distinct current map-product mode.
- `physical_probability`: conditional probability using physical scenario
  probabilities. This requires explicit and documented source, block, release,
  terrain/material, and model-variant probability semantics that are not yet
  implemented or validated.
- `annual_frequency`: annualized reach or exceedance frequency. This requires a
  temporal source-frequency model and propagation into the map denominator; it
  is not available in the current workflow.

## Denominator And Conditioning Rules

Current products have two active denominator families.

`unweighted_diagnostic` products are normalized only by the supplied input
records for the layer being built:

- `reach_probability` and trajectory-level exceedance layers use the supplied
  trajectory count. A trajectory contributes at most once per cell for reach and
  once per cell per configured exceedance threshold.
- `deposition_density` uses the supplied deposition-row count. Each deposition
  row contributes to one grid cell; absent deposition rows reduce the represented
  deposition set rather than implying zero physical deposition probability.
- `significant_impact_density` uses the supplied significant-impact-event count.
  It is an event-density distribution over significant impact records, not a
  trajectory-level impact probability.
- `max_kinetic_energy` and `max_jump_height` do not use probability
  denominators. They record the maximum sampled value in each cell over the
  supplied trajectory samples.
- Optional unweighted standard-error layers use the same trajectory-count
  denominator as their parent trajectory-level probability layer and are Monte
  Carlo convergence diagnostics only.

`sampling_weighted_conditional` products are normalized by `sampling_weight`
over the active metadata filter:

- The numerical input switch is
  `hazard_probability.probability_model: sampling_weighted`; the external
  map-package label is `sampling_weighted_conditional`.
- The current supported normalization convention is
  `conditioned_on_filter` for weighted hazard-layer construction. Labelled
  Phase 1 map packages may also record `conditioned_on_scenario` when the
  generated package is conditioned on the selected scenario metadata.
- Weighted reach and weighted exceedance layers use the total filtered
  trajectory `sampling_weight` as denominator. A trajectory contributes its
  weight at most once per cell for reach and once per cell per threshold.
- Weighted deposition density uses the same total filtered trajectory-weight
  denominator. Deposition rows join to `trajectory_metadata_table_v1` through
  `trajectory_id`; rows without active filtered metadata are excluded. The
  weighted deposition layer may sum below `1.0` when the supplied deposition CSV
  does not contain deposition rows for every filtered trajectory.
- Weighted significant-impact density is normalized by the sum of
  `sampling_weight` over filtered significant impact events, not by trajectory
  weight. It remains an event-density distribution and must not be described as
  a trajectory-level probability or structure-impact probability.
- Filters are the explicit `hazard_probability.filters` values and the metadata
  rows available in `trajectory_metadata_table_v1`. Filters that leave zero
  total weight are invalid.

No current denominator is physical probability mass or annual source frequency.
`physical_probability` and `annual_frequency` are schema-visible future labels
only. They are inactive for current map generation and must not appear as claims
in map names, legends, reports, or review summaries.
Current trajectory-threshold products should be described as conditional
intensity-exceedance products when they are conditioned on the supplied
trajectory set, metadata filter, or sampling-weighted scenario set. Reserve
intensity-frequency wording for future `physical_probability` or
`annual_frequency` products with explicit frequency semantics.
The current design gate for those future semantics is
`docs/physical_source_frequency_design_gate.md`; its decision is deferred, so
annual and physical labels remain unsupported for current products.

## Source-Zone And Block-Scenario Conditioning

Current conditioning is metadata and filter based:

- Source-zone ids, scenario ids, block-scenario labels, release-cell labels,
  model-configuration labels, and `sampling_weight` values are propagated
  metadata used for joins, filtering, and manifest auditability.
- Release sampling and block-scenario sampling describe the numerical sampling
  design. They do not define physical release probability, calibrated
  block-population probability, or annual source frequency.
- A labelled map package must record its `probability_mode`,
  `normalization_scope`, source-zone metadata path, scenario-table path when
  used, scenario ids, layer semantics, limitations, and non-operational status.
- Overlapping source zones, physical source probability, annual occurrence
  frequency, and calibrated block-population distributions remain unsupported
  unless a future phase adds explicit evidence, schemas, validation, and
  manifest contracts.

## Hazard Versus Risk Boundary

Hazard layers describe where modelled rockfall trajectories may travel and the
intensity of simulated motion or impacts. They are not risk maps. Risk requires
exposure, vulnerability, consequence, and occupancy assumptions that are outside
the current simulator and must not be implied by hazard-layer names, legends, or
reports.

## Allowed And Disallowed Language Examples

These examples apply to current products. Disallowed phrases may become allowed
only in future phases when the required contracts exist:

- risk language requires exposure, vulnerability, consequence, and occupancy
  contracts;
- annual or return-period language requires source-frequency and time-convention
  contracts;
- operational language requires operational validation and approval contracts;
- physical-probability language requires physical scenario probability
  semantics plus manifest and product-mode support.

| Topic | Allowed now | Disallowed now |
| --- | --- | --- |
| `unweighted_diagnostic` | "fraction of supplied trajectories reaching each cell"; "diagnostic reach fraction for this run set" | "probability of rockfall at this location"; "validated hazard probability" |
| `sampling_weighted_conditional` | "sampling-weighted conditional reach fraction over the documented filtered scenario set" | "annual probability"; "physical probability"; "sampling weights as physical probability" |
| Conditional intensity exceedance | "conditional kinetic-energy exceedance fraction over supplied trajectories"; "sampling-weighted conditional jump-height exceedance over the documented filter" | "intensity-frequency curve"; "annual exceedance frequency"; "return-period exceedance map" |
| `conditional_probability` design-only | "design-only conditional probability class; not emitted as a distinct current map-product mode" | "this layer is conditional probability" for current outputs; future conditional-probability mode must still not imply physical occurrence probability, annual probability, risk, or operational validation |
| `physical_probability` unsupported | "unsupported physical-probability claim; requires documented physical scenario probabilities" | "probability of occurrence"; "physically calibrated probability" |
| `annual_frequency` unsupported | "annual frequency is not available in the current workflow" | "1/year frequency"; "30-year return period"; "100-year event map" |
| Significant-impact density | "distribution of significant impact events over supplied event records" | "probability of impact at a structure"; "impact risk" |
| Hazard versus risk | "hazard layer"; "modelled reach or intensity layer" | "risk map"; "expected loss"; "building safety map" |
| Operational validation | "diagnostic or research output"; "not operationally validated" | "official hazard map"; "validated for emergency planning"; "design-basis map" |
| Return-period language | "no return-period semantics are defined" | "10-year", "30-year", or "100-year" labels without explicit annual source-frequency contracts |

## Executable Checks

Current executable coverage validates the active labels and the unsupported
annual/physical boundary:

- `tests/probabilistic_phase1.rs` parses
  `tests/fixtures/probabilistic_phase1/` source-zone, scenario, and
  `map_package_manifest_v1` fixtures. It validates
  `sampling_weighted_conditional` packages with `conditioned_on_filter` and
  `conditioned_on_scenario`, accepts non-annual GeoTIFF raster outputs, keeps
  `unweighted_diagnostic` diagnostic layer names from being relabelled as
  annual products, rejects the `annual_frequency` fixture for Phase 1, and
  rejects incomplete `physical_probability` metadata.
- `tests/test_hazard_layers.py` checks the Python hazard-layer builder against
  `tests/fixtures/hazard/` and the smoke case
  `validation/cases/probabilistic_phase1_smoke.yaml`. It verifies
  `hazard_probability.probability_model: sampling_weighted`,
  `normalization_convention: conditioned_on_filter`,
  `hazard_map_package.probability_mode: sampling_weighted_conditional`,
  non-annualized layer/raster semantics,
  `annual_frequency_fields_present` set to `false`, labelled package generation
  without raster-value changes, rejection of `annual_frequency` map-package
  requests, and source-zone mismatch rejection.
- The fixture directories used by those tests are
  `tests/fixtures/probabilistic_phase1/`, `tests/fixtures/hazard/`, and the
  generated-output paths referenced by
  `validation/cases/probabilistic_phase1_smoke.yaml`.

These checks do not validate model skill, physical scenario probability,
annualized hazard frequency, exposure, vulnerability, risk, or operational
approval. Any future `physical_probability` or `annual_frequency` mode requires
new evidence-backed product semantics, schemas, fixtures, and executable
checks before those labels can be used as current claims.
- `tests/test_physical_source_frequency_design_gate.py` and
  `scripts/validate_physical_source_frequency_design_gate.py` check the current
  design-gate record. The selected record requires source-rate units, overlap
  policy, uncertainty, calibration/validation separation, and rejection tests
  before a future prototype can be authorized.

## Later Milestone Placeholders

- Manifest consistency checks for denominator, conditioning, scenario filters,
  probability model, and unsupported claim prevention.
- GIS package alignment for CRS, vertical datum, affine grid, nodata, layer
  naming, map-package labels, and share-safe provenance.
