# Hazard-Map Semantics And Interpretation Guide

Status: M005 outline plus M006 language examples and M007 consistency-check
expectations. This guide defines interpretation semantics for hazard-map
products only. It does not add physics, introduce annual frequencies, change
model defaults, validate operational hazard maps, or add risk modelling.

## Scope

This document will define how to label and interpret hazard layers produced by
the existing post-processing workflow. It is not a calibration plan, source
frequency model, exposure/vulnerability model, or operational acceptance
standard.

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

## Denominator And Conditioning Outline

Future guide content should specify, for each layer:

- whether the denominator is trajectory count, deposition-row count, impact-event
  count, filtered sampling weight, physical probability mass, or annual source
  frequency;
- which filters define the conditioned set;
- whether normalization is per source zone, per scenario set, per release cell,
  per block scenario, per map package, or per supplied input table;
- how missing trajectories, absent deposition rows, absent impact events, and
  filtered-out metadata rows affect the denominator;
- which denominator must be recorded in manifests and report tables.

## Source-Zone And Block-Scenario Conditioning Outline

Future guide content should define:

- source-zone identifiers, source geometry, release-cell policy, and release
  sampling assumptions;
- block scenario identifiers, block size or mass classes, passive shape class,
  release-condition settings, and sampling weights;
- whether a map is conditioned on one source zone, a group of source zones, one
  block scenario, or a weighted scenario set;
- how overlapping source zones and scenario filters are reported;
- which source-zone and block-scenario metadata must appear in map-package
  manifests.

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
| `conditional_probability` design-only | "design-only conditional probability class; not emitted as a distinct current map-product mode" | "this layer is conditional probability" for current outputs; future conditional-probability mode must still not imply physical occurrence probability, annual probability, risk, or operational validation |
| `physical_probability` unsupported | "unsupported physical-probability claim; requires documented physical scenario probabilities" | "probability of occurrence"; "physically calibrated probability" |
| `annual_frequency` unsupported | "annual frequency is not available in the current workflow" | "1/year frequency"; "30-year return period"; "100-year event map" |
| Significant-impact density | "distribution of significant impact events over supplied event records" | "probability of impact at a structure"; "impact risk" |
| Hazard versus risk | "hazard layer"; "modelled reach or intensity layer" | "risk map"; "expected loss"; "building safety map" |
| Operational validation | "diagnostic or research output"; "not operationally validated" | "official hazard map"; "validated for emergency planning"; "design-basis map" |
| Return-period language | "no return-period semantics are defined" | "10-year", "30-year", or "100-year" labels without explicit annual source-frequency contracts |

## Consistency Checks And Fixtures

M007 documents consistency expectations only. Executable expansion can follow in
later milestones if gaps remain.

Existing relevant coverage includes:

- `tests/probabilistic_phase1.rs`;
- `tests/fixtures/probabilistic_phase1/`;
- selected hazard-layer builder fixtures under `tests/fixtures/hazard/`.

Existing coverage includes parser and fixture checks for current Phase 1 map
package labels, non-annualized raster outputs, weighted conditional package
fixtures, and incomplete physical/annual metadata rejection cases. It does not
mean every semantic expectation below is already executable.

Expected checks for future manifest/check-script expansion:

- `probability_mode`: accepted current labels are `unweighted_diagnostic` and
  `sampling_weighted_conditional`; design-only or unsupported modes must not be
  presented as current products;
- normalization scope: manifests must record whether the map is conditioned on
  the active filter, scenario, source zone, or another documented denominator;
- annualized flag: current products must keep raster outputs non-annualized;
  annualized layers require a future source-frequency and time-convention
  contract;
- numerator and denominator: reports and manifests should identify the counted
  quantity and denominator, such as trajectory count, event count, filtered
  sampling weight, physical probability mass, or annual source frequency. These
  explicit fields are future expectations unless already represented by current
  layer semantics;
- source-zone and scenario conditioning: source-zone ids, scenario ids,
  block-scenario filters, and sampling-weight fields must match the manifest
  label and normalization scope;
- physical and annual rejection: current map products and builders must not
  present physical-probability or annual-frequency layers. Current fixtures
  cover rejection of incomplete physical-probability metadata; any future
  physical-probability mode requires a separate evidence-backed product and
  manifest contract;
- significant-impact event-density wording: event-density layers must be
  described as distributions over supplied impact events, not trajectory-level
  probabilities, structure-impact probabilities, or risk;
- risk and operational exclusion: map packages must not include exposure,
  vulnerability, consequence, expected-loss, operational-risk, or operational
  approval language unless a future workflow explicitly adds those contracts.
  Current executable checks may be incomplete; M007 records the required review
  and future-enforcement expectation.

## Later Milestone Placeholders

- Manifest consistency checks for denominator, conditioning, scenario filters,
  probability model, and unsupported claim prevention.
- GIS package alignment for CRS, vertical datum, affine grid, nodata, layer
  naming, map-package labels, and share-safe provenance.
