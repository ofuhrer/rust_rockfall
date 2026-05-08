# Tschamut Public Scalable Conditional Target Gate

Status: blocked missing ignored inputs (`blocked_missing_inputs`).

Validated record:
`validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py \
  validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml
```

## Result

The selected target-scale conditional workflow was not executed in this
checkout. The command plan for
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` is valid,
but the local ignored inputs and generated gate artifacts needed to run or
compare the target-scale case are absent.

Missing local paths recorded by the gate:

- `validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`
- `validation/private/tschamut_public_pilot/gate_v1/trajectories`
- `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`

These paths are intentionally local/ignored artifacts. They must be regenerated
or restored from documented public inputs and local private outputs, not
committed as substitutes.

## Required Rerun Conditions

Before the selected ensemble-size gate can be reassessed, a future local run must
record:

- validation-runner `ensemble_execution` provenance from `random.ensemble_workers`;
- `conditional_hazard_execution_diagnostics_v1` in the hazard manifest;
- `hazard_reducer_chunk_manifest_v1` chunk manifests;
- summary-only conditional-curve export;
- output file count and bytes;
- wall time and memory sidecars where available;
- worker-count parity for the selected run;
- convergence diagnostics comparing target and small-gate trajectory counts.

## Claim Boundary

This blocker record does not change physics, defaults, sampling weights, hazard
semantics, or validation status. It does not add annual frequency, physical
probability, return-period, risk, exposure, vulnerability, or operational
hazard-map semantics.
