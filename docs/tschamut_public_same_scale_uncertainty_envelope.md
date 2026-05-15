# Same-Scale Uncertainty Envelope

- Pilot id: `tschamut_public_pilot`
- Final classification: `inconclusive`
- Envelope status: `measured_with_pending_target_artifacts`
- Scale-up authorized: `false`
- Operational claims allowed: `false`
- Convergence status: `blocked_missing_target_artifacts`
- Target artifact restore status: `blocked_missing_inputs`

## Convergence
- Artifact readiness: `blocked_missing_target_artifacts`
- Missing or pending inputs:
  - `/Users/fuhrer/Desktop/rust_rockfall/main/validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`: pending target-side same-scale validation manifest at /Users/fuhrer/Desktop/rust_rockfall/main/validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json
  - `/Users/fuhrer/Desktop/rust_rockfall/main/hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`: pending target-side same-scale hazard manifest at /Users/fuhrer/Desktop/rust_rockfall/main/hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json

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
- `target_vs_gate_convergence_pending`
- `validation_output_pressure_retained`
- `context_is_limiting`
- `single_job_path_deferred`
- `target_artifact_readiness_pending`

## Remaining Uncertainty
- target-side same-scale artifacts are pending or blocked, so convergence remains unmeasured
- validation debug-output pressure is still a scale-up blocker
- corridor-level context remains interpretive evidence, not obstacle physics
- distributed execution remains deferred on measured evidence
- target-side same-scale hazard artifacts are still pending or blocked

## Target-Artifact Readiness
- Gate manifest available: `true`
- Target validation manifest available: `false`
- Target hazard manifest available: `false`
- Target cell-wise layers available: `false`
- TB-014 ready: `false`
- Target artifact restore status: `blocked_missing_inputs`
