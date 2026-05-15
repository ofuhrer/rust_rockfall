# Same-Scale Uncertainty Envelope

- Pilot id: `tschamut_public_pilot`
- Final classification: `inconclusive`
- Envelope status: `measured_with_remaining_scale_constraints`
- Scale-up authorized: `false`
- Operational claims allowed: `false`
- Convergence status: `measured`
- Target artifact restore status: `ready`

## Convergence
- Artifact readiness: `ready`
- Measured per-layer convergence metrics are available.
- The strongest disagreement layers are `max_kinetic_energy`,
  `max_jump_height`, and the velocity exceedance layers; the cell-wise
  comparison is `ok` but remains conservative rather than accepted.

## Validation Output
- Status: `blocker_retained`
- Validation output mode context: `summary_only`
- Validation output reduced: `True`
- Validation output comparison status: `available`
- Baseline validation output files: `125`
- Baseline validation output bytes: `34545900`
- Summary-only validation output files: `4`
- Summary-only validation output bytes: `81425`
- Reduction file count delta: `121`
- Reduction byte delta: `34464475`
- Target-side summary-only validation output pressure is now measured separately as `summary_only` with `4` files / `1271721` bytes versus `2005` files / `571368823` bytes baseline.

## Context
- Status: `limiting`
- swissTLM3D corridor status: `measured_corridor_relevance`
- Roads/transport relevance: `limiting`
- Water/channel relevance: `limiting`
- Barriers/protection relevance: `limiting`

## Execution Sufficiency
- Status: `defer`
- Decision: `defer`

## Limiting Factors
- `validation_output_pressure_retained`
- `context_is_limiting`
- `single_job_path_deferred`

## Remaining Uncertainty
- validation debug-output pressure is still a scale-up blocker
- target-side summary-only validation output pressure is measured, but the target-vs-gate interpretation remains inconclusive
- corridor-level context remains interpretive evidence, not obstacle physics
- the measured broader hazard-context overlap envelope remained unresolved
  within 20 m for roads, barriers, and water; a three-layer probe was runtime
  limited, and the corridor interpretation still does not reach accepted
  obstacle interaction evidence
- the target-vs-gate disagreement is dominated by sampled-output differences
  on the shared grid, with identical CRS/grid geometry but different ensemble
  size and jump-height statistic coverage in the restored case metadata
- distributed execution remains deferred on measured evidence

## Target-Artifact Readiness
- Gate manifest available: `true`
- Target validation manifest available: `true`
- Target hazard manifest available: `true`
- Target cell-wise layers available: `true`
- TB-014 ready: `true`
- Target artifact restore status: `ready`
