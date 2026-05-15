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

## DT-01 Provenance And Output-Profile Closure

The selected record now contains two explicit policy sections:

- `target_run_provenance_policy` separates the 1,000-trajectory
  observed-release target run from the auxiliary `local_parallel_ensemble_v1`
  `ensemble_execution` sidecar. The auxiliary sidecar covers the 100-trajectory
  single-release ensemble path only and must not be interpreted as full
  observed-release target-run provenance.
- `output_profile_policy` records that the current target gate is a
  `custom_or_mixed_legacy_summary_only` run: summary-only conditional curves
  and no plots are recorded, but available command evidence does not prove
  `--grid-csv-export none`. Future selected balfrin/reproduction runs should
  use the `scalable_conditional` profile unless an explicit `provenance_audit`
  profile is needed.

This closes the target-run provenance/output-profile ambiguity for the current
gate. It does not make the gate a convergence pass and does not authorize
ensemble-size increase. The validation-side debug output budget remains a
blocker for any larger selected-domain run: the current target validation run
produced 2,004 files and 571,131,205 bytes of ignored debug artifacts.

Recorded target evidence:

- validation wall time: 77.024 s; validation output: 2,004 files and 571,131,205 bytes;
- hazard wall time: 57.859 s; hazard output: 54 files and 75,423,367 bytes;
- memory sidecars on Darwin: validation 367,017,984 bytes, hazard 411,058,176 bytes;
- 1-worker vs 2-worker hazard reducer parity matched compared `hazard_layer` and `deposition_points` checksums;
- summary-only conditional curves were enabled and no full curve table was written.

## DT-04 Balfrin Reproduction

The selected target gate was reproduced on `balfrin.cscs.ch` as SLURM job
`4318941` from `/users/olifu/work/rust_rockfall` at commit
`61ab9c6542ba1d2274139940777ff0238f1983cf`.

Validated record:
`validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_balfrin_target_gate_reproduction.py \
  validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml
```

The run used the same selected target-gate inputs and unchanged
`translational_v0` physics/defaults, with 10 observed release cells and 100
trajectories per release cell (`1000` simulated trajectories total). The hazard
run used the scalable output profile: `summary-only` conditional curves, no
full conditional curve CSV, no grid CSV, GeoTIFF export enabled, plots disabled,
and deterministic two-worker chunk/reducer metadata.

Recorded evidence includes validation and hazard manifests, map-package and
pilot-GIS-package manifests, a scaling summary, SHA-256 checksums, positive
runtime/output-size measurements, and a clean log audit. The result is
classified `inconclusive`, not operational validation and not a convergence
pass. The record exists to prove that the selected conditional hazard-map
workflow can run in the intended balfrin environment at the current same-scale
target gate.

## DT-05 Convergence Acceptance Assessment

Validated record:
`validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_conditional_convergence_protocol.py \
  validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml \
  --format json
```

The DT-05 protocol records the required evidence categories for conditional
hazard-map convergence and applies them to the completed DT-04 Balfrin
reproduction. The result remains `inconclusive`: target-run provenance,
frozen inputs, deterministic order metadata, reducer parity, output profile,
checksums, and log audit are present, but convergence has not been accepted,
forest/obstacle context remains limiting, manual GIS/QGIS QA is secondary and
not run here, and the validation debug-output budget remains a retained
blocker. Scale-up authorization stays false.

## Required Rerun Conditions

Before the selected ensemble-size gate can be reassessed, follow-up review must
resolve:

- target-vs-small-gate convergence interpretation;
- manual GIS/QGIS visual QA, which is currently blocked by missing QGIS and
  absent ignored target package artifacts in this checkout;
- forest/obstacle context limits, currently classified `limiting` because no
  public context layer crop is available in this checkout;
- validation debug output volume, which remains too large for another
  selected-domain increase without reduction or explicit justification.

## Claim Boundary

This blocker record does not change physics, defaults, sampling weights, hazard
semantics, or validation status. It does not add annual frequency, physical
probability, return-period, risk, exposure, vulnerability, or operational
hazard-map semantics.
