# TB-677 Conditional Physical-Probability Prototype Preflight

Date: 2026-05-27

## Result

The one-AOI physical-probability prototype remains fail-closed. No prototype
probability output was generated because the physical/annual design gate is
still deferred and the calibration review now explicitly rejects the selected
candidate for validation or physical-probability use.

## Commands

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_physical_credibility_evidence_gaps.py \
  --format json \
  --json-output /tmp/tb677_physical_gaps.json

PYENV_VERSION=system uv run python scripts/validate_physical_frequency_reducer_preconditions.py \
  validation/templates/physical_frequency_reducer_preconditions_v1.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/validate_physical_frequency_reducer_preconditions.py \
  tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/validate_annual_physical_prototype_preflight.py \
  validation/templates/annual_physical_prototype_preflight_v1.yaml \
  --format json
```

## Measured Status

Physical-credibility gap report:

- `balfrin_evidence_gap_status`: `measured_diagnostic_only`
- `physical_credibility_state`: `no_physical_evidence`
- `physical_credibility_status`: `not_established`
- `calibration_status`: `partial`
- `observed_runout_deposition_intake_status`: `ready`

Reducer preconditions:

- Template status: `preconditions_not_satisfied`
- Template prototype authorization: `false`
- Design-review fixture status: `accepted_for_design_review`
- Design-review fixture prototype authorization: `false`
- Design-review fixture selected overlap policy: `documented_overlap_adjustment`

Annual/physical prototype preflight:

- `record_status`: `blocked_by_design_gate`
- `prototype_authorized`: `false`
- `design_gate_decision`: `deferred`
- `design_gate_authorized`: `false`
- Remaining blocker count: `5`

## First Blocking Evidence Item

The immediate blocker for a one-AOI physical-probability prototype is:

`accepted_validation_calibration_review`

The concrete measured failure behind that blocker is:

`holdout_runout_abs_error_max_m`

The selected calibration candidate reports:

- threshold: `<= 30.0 m`
- observed: `55.111764 m`
- decision: `rejected_residual_quality`

Until this calibration review is accepted, a physical-probability prototype
would mix conditional diagnostic layers with rejected calibration evidence.

## Other Remaining Blockers

The preflight also keeps these prototype blockers active:

- `accepted_source_frequency_evidence`
- `accepted_block_release_probability_evidence`
- `implemented_overlap_adjusted_reducers`
- `implemented_uncertainty_propagation`

## Boundary

No physical-probability map, annual-frequency product, return-period label,
operational hazard map, risk/exposure/vulnerability output, distributed claim,
or Swiss-wide claim is made by this preflight.
