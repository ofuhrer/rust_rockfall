# Block And Release Probability Evidence Contract

Status: inactive evidence-schema contract for future review. This document does
not add annual frequency products, physical probability products, return-period
labels, operational hazard maps, or risk modelling. It closes one
physical/source-frequency design-gate blocker by defining how candidate
block-scenario and release-cell physical probability evidence must be recorded
before a later gate can consider prototype authorization.

## Scope

The contract applies only to future evidence records for block-scenario
distributions and release-cell allocation. Current Tschamut and fixture
products remain conditional intensity-exceedance, sampling-weighted
conditional, or unweighted diagnostic products. A valid evidence record does
not by itself authorize annual or physical map generation.

The checked-in template is
`validation/templates/block_release_probability_evidence_v1.yaml`, and the
executable validator is
`scripts/validate_block_release_probability_evidence.py`.

A small synthetic design-review fixture lives at
`tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml`.
It proves the `accepted_for_design_review` record shape and validator behavior,
but it is not accepted evidence for Tschamut or any real Swiss source zone and
does not authorize runtime annual or physical products.

## Required Record States

`record_status` must be one of:

- `no_accepted_block_release_probability_evidence`: records that no accepted
  block-scenario or release-cell probability evidence exists for prototype
  use; probability distributions must remain empty.
- `candidate_not_authorized`: records a complete candidate evidence package for
  design review only; it is not usable by runtime products.
- `accepted_for_design_review`: records a complete evidence package that a
  future design gate may review. It still does not authorize map generation.

No state in this contract authorizes annual or physical runtime support.

## Required Fields

Every record must include:

- stable `source_zone_id`;
- `source_geometry_version`;
- `source_geometry_hash`;
- `crs_epsg`, expected to be `2056`;
- `vertical_datum`, expected to be `LN02`;
- `source_event_class_id`;
- `block_scenario_distribution`;
- `release_cell_distribution`;
- `sampling_weight_boundary`;
- `uncertainty`;
- `evidence_basis`;
- separate `calibration_dataset_ids` and `validation_dataset_ids`;
- `operational_status`, expected to be `research_diagnostic`;
- `prototype_authorized`, expected to be `false`.

Candidate records must include stable `block_scenario_id` values with positive
conditional probabilities that sum to `1.0` under the denominator
`conditional_probability_given_source_event`. They must also include stable
`release_cell_id` values for each block scenario with nonnegative conditional
probabilities that sum to `1.0` under the denominator
`conditional_probability_given_source_event_and_block_scenario`.

## Rejections

The validator rejects:

- missing or invalid conditional denominators;
- candidate records with missing block-scenario probabilities;
- block-scenario probabilities that are negative, zero, or do not sum to
  `1.0`;
- release-cell probabilities that are missing, negative, assigned to unknown
  block scenarios, or do not sum to `1.0` for each block scenario;
- reuse of `sampling_weight` as physical probability;
- missing uncertainty representation for candidate records;
- calibration and validation dataset overlap;
- `swisstopo` listed as validation evidence by itself;
- prototype authorization;
- operational, risk, or return-period claims.

Sampling weights remain outside this evidence contract. They are conditional
scenario weights unless a future schema replaces them with documented physical
probabilities and a later gate authorizes their use.

## Current Decision

The selected template records
`no_accepted_block_release_probability_evidence`. This means the
block/release probability schema blocker is closed at the inactive contract
level, but the annual or physical prototype remains blocked by missing accepted
evidence, missing overlap-adjusted reducers, missing uncertainty propagation,
and missing validation/calibration review for frequency products.
