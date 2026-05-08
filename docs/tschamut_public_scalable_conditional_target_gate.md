# Tschamut Public Scalable Conditional Target Gate

Status: executed but inconclusive (`inconclusive`).

Validated record:
`validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py \
  validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml
```

## Result

The selected target-scale conditional workflow was regenerated and executed
locally after restoring ignored public/processed inputs. The result remains
inconclusive; it is evidence for workflow execution and output budget, not an
authorization to increase ensemble size or make operational claims.

Regenerated or generated local paths recorded by the gate:

- `validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml`
- `validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`

These paths are intentionally local/ignored artifacts. They must be regenerated
or restored from documented public inputs and local private outputs, not
committed as substitutes.

The target validation run completed with ten observed release rows and 1,000
simulated trajectories. The hazard run used `--conditional-curve-export
summary-only` and `--reducer-workers 2`, suppressed a 729,600-row curve table,
and wrote `conditional_hazard_execution_diagnostics_v1` plus
`hazard_reducer_chunk_manifest_v1` chunk manifests.

In short: the run produced 1,000 simulated trajectories for the target gate.

Recorded target evidence:

- validation wall time: 77.024 s; validation output: 2,004 files and 571,131,205 bytes;
- hazard wall time: 57.859 s; hazard output: 54 files and 75,423,367 bytes;
- memory sidecars on Darwin: validation 367,017,984 bytes, hazard 411,058,176 bytes;
- 1-worker vs 2-worker hazard reducer parity matched compared `hazard_layer` and `deposition_points` checksums;
- summary-only conditional curves were enabled and no full curve table was written.

## Required Rerun Conditions

Before the selected ensemble-size gate can be reassessed, follow-up review must
resolve:

- target-vs-small-gate convergence interpretation;
- manual GIS/QGIS visual QA;
- forest/obstacle context limits;
- the validation-runner provenance caveat that `ensemble_execution` records the
  auxiliary single-release 100-trajectory ensemble path, while the observed
  Tschamut validation outputs contain 1,000 trajectories.

## Claim Boundary

This blocker record does not change physics, defaults, sampling weights, hazard
semantics, or validation status. It does not add annual frequency, physical
probability, return-period, risk, exposure, vulnerability, or operational
hazard-map semantics.
