# Physical Frequency Reducer Preconditions

Status: inactive precondition contract for future review. This document does
not add annual frequency products, physical probability products, return-period
labels, operational hazard maps, or risk modelling. It closes one
physical/source-frequency design-gate blocker by defining the future
overlap-adjusted reducer and uncertainty-propagation conditions that must be
satisfied before a later gate can consider prototype authorization.

## Scope

The contract applies only to future reducer design records. Current Tschamut
and fixture products remain conditional intensity-exceedance,
sampling-weighted conditional, or unweighted diagnostic products. A valid
precondition record does not by itself authorize annual or physical map
generation.

The checked-in template is
`validation/templates/physical_frequency_reducer_preconditions_v1.yaml`, and
the executable validator is
`scripts/validate_physical_frequency_reducer_preconditions.py`.

## Required Record States

`record_status` must be one of:

- `preconditions_not_satisfied`: records that overlap adjustment and
  uncertainty propagation are not implemented or reviewed for prototype use.
- `candidate_not_authorized`: records a complete candidate reducer and
  uncertainty precondition package for design review only; it is not usable by
  runtime products.
- `accepted_for_design_review`: records a complete precondition package that a
  future design gate may review. It still does not authorize map generation.

No state in this contract authorizes annual or physical runtime support.

## Required Reducer Preconditions

Candidate records must define:

- source-zone overlap policy, either `mutually_exclusive_partition` or
  `documented_overlap_adjustment`;
- geometry version and hash requirements for all source zones;
- shared release-cell handling rules that prevent double counting;
- deterministic reducer merge rules independent of trajectory execution order;
- required source-rate, block-scenario, release-cell, trajectory, and terrain
  uncertainty components;
- uncertainty propagation method, output summary fields, and provenance fields;
- calibration and validation dataset separation.

The precondition contract is intentionally stricter than current conditional
hazard-layer reducers. It defines what a future frequency reducer must prove;
it does not change existing reducer outputs.

## Rejections

The validator rejects:

- prototype authorization;
- missing or inactive overlap policy in candidate records;
- overlap policies outside the approved policy names;
- missing double-counting guard;
- non-deterministic merge semantics;
- output units or annual/physical output support marked active in the template;
- missing required uncertainty components;
- missing propagation method or output summaries in candidate records;
- calibration and validation dataset overlap;
- `swisstopo` listed as validation evidence by itself;
- unsupported operational, risk, or return-period claims.

## Current Decision

The selected template records `preconditions_not_satisfied`. This means the
overlap/reducer and uncertainty-propagation blocker is closed only at the
inactive contract level. The annual or physical prototype remains blocked by
missing accepted evidence, missing implemented overlap-adjusted reducers,
missing implemented uncertainty propagation, and missing validation/calibration
review for frequency products.
