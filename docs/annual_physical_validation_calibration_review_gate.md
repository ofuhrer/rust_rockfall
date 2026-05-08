# Annual/Physical Validation Calibration Review Gate

Status: inactive review-gate contract for future annual or physical products.
This document does not add annual frequency products, physical probability
products, return-period labels, operational hazard maps, or risk modelling. It
closes one physical/source-frequency design-gate blocker by defining the
validation/calibration review package required before a later gate can consider
prototype authorization.

## Scope

The contract applies only to future review records for annual or physical
frequency products. Current Tschamut and fixture products remain conditional
intensity-exceedance, sampling-weighted conditional, or unweighted diagnostic
products. A valid review record does not by itself authorize annual or physical
map generation.

The checked-in template is
`validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml`,
and the executable validator is
`scripts/validate_annual_physical_validation_calibration_review_gate.py`.

## Required Record States

`record_status` must be one of:

- `review_not_passed`: records that validation/calibration review is not
  complete for prototype use.
- `candidate_not_authorized`: records a complete candidate review package for
  design review only; it is not usable by runtime products.
- `accepted_for_design_review`: records a complete review package that a
  future design gate may review. It still does not authorize map generation.

No state in this contract authorizes annual or physical runtime support.

## Required Review Topics

Candidate records must define:

- calibration objective and dataset ids;
- validation objective and dataset ids;
- holdout or external-review dataset ids;
- validation maturity target and current maturity cap;
- no-tuning rule for frequency products;
- proof that swisstopo terrain and context layers are treated as input geodata,
  not validation evidence by themselves;
- review links to source-frequency, block/release probability, and reducer
  precondition records;
- claim boundaries that keep return-period, operational, risk, exposure, and
  vulnerability semantics out of scope.

## Rejections

The validator rejects:

- prototype authorization;
- missing calibration, validation, or holdout review sections in candidate
  records;
- calibration, validation, and holdout dataset overlap;
- `swisstopo` listed as validation or holdout evidence by itself;
- missing no-tuning rule;
- missing maturity target or maturity cap;
- missing source-frequency, block/release probability, or reducer precondition
  record references;
- operational, risk, exposure, vulnerability, or return-period claims.

## Current Decision

The selected template records `review_not_passed`. This means the
validation/calibration review blocker is closed only at the inactive contract
level. The annual or physical prototype remains blocked by missing accepted
evidence, missing implemented overlap-adjusted reducers, missing implemented
uncertainty propagation, and no accepted validation/calibration review.
