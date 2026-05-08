# Source-Frequency Evidence Contract

Status: inactive evidence-schema contract for future review. This document does
not add annual frequency products, physical probability products, return-period
labels, operational hazard maps, or risk modelling. It closes one
source-frequency design-gate blocker by defining how candidate source-rate
evidence must be recorded before a later gate can consider prototype
authorization.

## Scope

The contract applies only to future source-frequency evidence records. Current
Tschamut and fixture products remain conditional intensity-exceedance,
sampling-weighted conditional, or unweighted diagnostic products. A valid
source-frequency evidence record does not by itself authorize annual or
physical map generation.

The checked-in template is
`validation/templates/source_frequency_evidence_v1.yaml`, and the executable
validator is `scripts/validate_source_frequency_evidence.py`.

## Required Record States

`record_status` must be one of:

- `no_accepted_frequency_evidence`: records that a source zone has no accepted
  source-rate evidence for prototype use; rate values must remain empty.
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
- `source_event_class`;
- `frequency_model_id`;
- `frequency_unit`, expected to be `events_per_source_zone_per_year`;
- `rate_time_window_years`;
- `rate_observation_period`;
- `rate_evidence_type`;
- `rate_provenance`;
- `rate_uncertainty`;
- `source_zone_overlap_policy`;
- separate `calibration_dataset_ids` and `validation_dataset_ids`;
- `operational_status`, expected to be `research_diagnostic`;
- `prototype_authorized`, expected to be `false`.

Candidate records with a numeric `source_event_rate_per_year` must also include
positive lower and upper uncertainty bounds, provenance URL or citation text,
and non-empty limitation notes.

## Rejections

The validator rejects:

- missing or invalid source-rate units;
- accepted or candidate records with missing source rates;
- uncertainty intervals that are missing, negative, inverted, or do not contain
  the point estimate;
- missing source-zone overlap policy;
- calibration and validation dataset overlap;
- `swisstopo` listed as validation evidence by itself;
- prototype authorization;
- operational, risk, or return-period claims.

Sampling weights remain outside this evidence contract. They are conditional
scenario weights unless a future schema replaces them with documented physical
probabilities and a later gate authorizes their use.

## Current Decision

The selected template records `no_accepted_frequency_evidence`. This means the
source-frequency evidence schema blocker is partially closed, but the annual or
physical prototype remains blocked by missing accepted evidence, missing
overlap-adjusted reducers, missing uncertainty propagation, and missing
validation/calibration review for frequency products.
