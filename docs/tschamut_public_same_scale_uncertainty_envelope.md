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

## Sampling Sensitivity
- Status: `measured`
- A bounded 12-trajectory full-output probe at seed `34014` was run to test
  whether the target-vs-gate disagreement shrinks under controlled sampling.
- The summary-only probe attempt stayed blocked for hazard rebuilding because
  trajectory CSV output was not available there, so it is recorded only as a
  blocker check.
- Probe output pressure:
  `247` validation files / `68221148` bytes and `49` hazard files /
  `21058710` bytes.
- Probe-vs-gate and probe-vs-target comparisons both completed with `ok`
  status, and the disagreement shrank compared with TB-024 but did not
  disappear.
- `max_kinetic_energy` remains the dominant disagreement layer, while
  `max_jump_height` still carries support and nodata differences.

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

## Case Regeneration
- Status: `ready`
- The gate and target private case YAMLs can now be regenerated
  deterministically from the committed frozen pilot records and processed
  public input metadata via
  `scripts/generate_tschamut_same_scale_cases.py`.
- The helper is a readiness and regeneration aid, not a new acceptance gate.
- It preserves the non-operational claim boundary and does not change
  physics, defaults, thresholds, or source-zone semantics.

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
- the bounded sampling-sensitivity probe reduced the dominant disagreement
  layers but did not collapse them; the remaining uncertainty is therefore
  sampling-size sensitivity versus structural sampled-output divergence, not a
  grid or scenario/source mismatch
- the target-vs-gate disagreement is dominated by sampled-output differences
  on the shared grid, with identical CRS/grid geometry but different ensemble
  size and jump-height statistic coverage in the restored case metadata
- distributed execution remains deferred on measured evidence

A second-site portability preflight is now available for future Swiss sites;
it remains metadata-only and does not alter the current Tschamut same-scale
uncertainty interpretation.

The multi-site source-zone / scenario contract audit
`scripts/audit_multisite_source_scenario_contract.py` separates portable
contract fields from Tschamut-specific heuristics, but it does not reduce the
current convergence or sampling uncertainty on its own.

## Target-Artifact Readiness
- Gate manifest available: `true`
- Target validation manifest available: `true`
- Target hazard manifest available: `true`
- Target cell-wise layers available: `true`
- TB-014 ready: `true`
- Target artifact restore status: `ready`
