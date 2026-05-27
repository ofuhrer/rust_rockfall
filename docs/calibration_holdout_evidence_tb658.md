# Calibration And Holdout Evidence TB-658

Date: 2026-05-27

## Result

The calibration/holdout separation checks still pass. The first unresolved
physical-probability blocker is now calibration acceptance, not holdout
separation.

## Checks

Calibration separation preflight:

- `preflight_status`: `passed`
- calibration artifacts: `3`
- validation cases checked: `22`
- prohibited calibration-to-validation crossings: `0`

Chant Sura holdout split audit:

- `audit_status`: `passed`
- model-selection trajectories: `5`
- held-out trajectories: `6`
- shared trajectories: `0`
- recorded overlap: `0`

Validation/calibration evidence gap before TB-676:

- `calibration_status`: `partial`
- `holdout_and_validation_evidence`: `present`
- physical-probability readiness: `partial_evidence_missing_critical_inputs`
- passing evidence classes: `6 / 7`
- first blocking evidence class: `calibration_evidence`
- first blocking calibration input:
  `accepted_residual_quality_threshold_or_review_decision`

## Boundary

Measured calibration evidence is present, and holdout scoring is separated, but
the measured residuals have not been accepted by a predeclared threshold or
explicit review decision. No validation acceptance, physical-probability map
label, annual-frequency product, operational map, return-period claim, or risk
product is enabled by this refresh.

## TB-676 Update

The calibration acceptance review now records an explicit rejection rather than
a missing threshold:

- `readiness_status`: `rejected_residual_quality`
- `support_role`: `measured_fit_rejected_by_acceptance_review`
- `first_blocking_input`: `holdout_runout_abs_error_max_m`
- `acceptance_threshold`: `present`
- `residual_quality_review`: `rejected`

The first failed criterion is:

```text
holdout_runout_abs_error_m.max <= 30.0 m
observed: 55.111764 m
```

The selected candidate remains diagnostic only. No validation acceptance,
physical-probability, annual-frequency, operational, return-period, or risk
claim is enabled.
