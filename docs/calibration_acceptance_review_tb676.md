# TB-676 Calibration Acceptance Review

Date: 2026-05-27

## Result

The Tschamut v0.3 calibration evidence now has an explicit residual-quality
review decision. The selected candidate remains diagnostic and is rejected for
validation or physical-probability use because holdout runout residuals exceed
the recorded threshold.

Record updated:

`calibration/experiments/tschamut_v0_3/summary.json`

## Decision

- Decision: `rejected_residual_quality`
- Selected candidate: `candidate_103`
- Threshold source: `TB-676 residual-quality screen, predeclared before any parameter promotion`
- First failed criterion: `holdout_runout_abs_error_max_m`

Criteria:

| Criterion | Threshold | Observed | Status |
| --- | ---: | ---: | --- |
| `holdout_runout_abs_error_m.max` | `<= 30.0 m` | `55.111764 m` | `fail` |
| `holdout_runout_abs_error_m.mean` | `<= 15.0 m` | `18.217757 m` | `fail` |
| `holdout_deposition_cloud_overlap_fraction` | `>= 0.7` | `0.777778` | `pass` |

## Evidence Report Change

`scripts/assess_validation_calibration_evidence_gaps.py` now reads the
calibration acceptance review and distinguishes:

- missing acceptance criteria,
- accepted residual quality,
- rejected residual quality.

Current calibration readiness:

- `readiness_status`: `rejected_residual_quality`
- `support_role`: `measured_fit_rejected_by_acceptance_review`
- `first_blocking_input`: `holdout_runout_abs_error_max_m`
- `acceptance_threshold`: `present`
- `residual_quality_review`: `rejected`

Calibration/validation separation still passes:

- `preflight_status`: `passed`
- Calibration artifacts: `3`
- Validation cases checked: `22`
- Prohibited calibration-to-validation crossings: `0`

## Interpretation

This closes the missing-acceptance-criterion gap by making the review decision
explicit. It does not accept the selected parameters. The next scientific work
should improve the residual failure with new evidence or model changes before
any physical-probability prototype treats calibration as accepted.

No validation acceptance, physical probability, annual frequency, operational
hazard, return-period, risk/exposure/vulnerability, or default-parameter claim
is enabled.
