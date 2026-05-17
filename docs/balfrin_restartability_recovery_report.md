# Balfrin Restartability Recovery Report

- Status: `measured`
- Scope: live interrupted and resumed Balfrin recovery evidence only; this does not authorize distributed execution, scale-up, or operational hazard claims.
- Provenance: live Balfrin interruption on `tschamut_public_balfrin_single_release_zone_v1` followed by a resumed run at `tschamut_public_balfrin_single_release_zone_v3`.
- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_balfrin_restartability_recovery_v1`

## Partial State

- Interrupted run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1`
- Resumed run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`
- Interrupted job id: `4325958`
- Resumed job id: `4326021`
- Interrupted job state: `CANCELLED by 21028`
- Resumed job state: `COMPLETED`
- The interrupted job reached the compile stage, then stopped before a usable output tree was produced in the run root.

## Resume Commands

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_conditional_gate_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --submit
```

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 --run-id tschamut_public_conditional_gate_v1 --partition postproc --time 01:00:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --submit
```

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 --output-json /tmp/balfrin_probe_metrics_v3.json
```

## Recovery Timing

- Interrupted job start: `2026-05-17T00:59:56`
- Interrupted job cancel: `2026-05-17T01:08:36`
- Resumed job start: `2026-05-17T01:17:26`
- Resumed job end: `2026-05-17T01:17:40`
- Resume gap: `530` seconds
- Interrupted job wall time before cancel: `00:08:40`
- Resumed job wall time: `00:00:14`

## Reused And Executed Chunks

- Trajectory decision counts: `{"executed": 4}`
- Reducer decision counts: `{"reused_completed_state": 2, "executed": 2}`
- Reused chunk counts:
  - reducer: `2`
- Executed chunk counts:
  - trajectory: `4`
  - reducer: `2`
- The live recovery reused completed reducer state and reran the trajectory side of the probe before finishing the remaining reducer work.

## Artifact Continuity

- `validation_tschamut_public_conditional_gate_v1_trajectory_merge_state_v1.json`: `ready`
- `validation_tschamut_public_conditional_gate_v1_reducer_merge_state_v1.json`: `ready`
- `validation_tschamut_public_conditional_gate_v1_trajectory_execution_index_v1.json`: `completed_chunk_count=4`, `failed_chunk_count=0`, `rerun_count=4`
- `validation_tschamut_public_conditional_gate_v1_reducer_execution_index_v1.json`: `completed_chunk_count=2`, `failed_chunk_count=0`, `rerun_count=0`
- `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`: present in the live checkout and consistent with the resumed run output tree
- `validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json`: present in the live checkout and tied to the same command plan

## Source Paths

- Interrupted run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1`
- Resumed run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`
- Interrupted SLURM stderr: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1/logs/slurm-4325958.err`
- Resumed SLURM stdout: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/logs/slurm-4326021.out`
- Live collector summary: `/tmp/balfrin_probe_metrics_v3.json`

## Numerical Stability

- Numerical artifact stability: `not_separately_assessed`
- Changed artifact count: `null`
- Changed paths: `[]`
- This report does not overclaim hash parity for the live recovery; the proof here is restartability and artifact continuity.

## Artifact Hygiene

- Artifact hygiene classification: `pass_clean`
- Generated roots stayed inside the two live run roots and the live repo checkout.
- Placeholder second-site paths were avoided:
  - `data/processed/swisstopo/placeholder_second_site_v1`
  - `validation/private/placeholder_second_site_v1`
  - `hazard/results/placeholder_second_site_v1`

## Explicit Limits

- Live interruption/resume evidence only; no distributed execution, scale-up authorization, physics, annual-frequency, risk, exposure, vulnerability, or operational claim is introduced.
- The collector still reports `blocked_missing_inputs` for output-family fields, so this report is a restartability proof, not a full metrics-closure claim.
- No fixture-backed proof is presented here as a live recovery.
