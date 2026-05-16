# Balfrin Restartability Recovery Report

- Status: `fixture_proven`
- Scope: controlled recovery evidence only; this does not claim a live interrupted Balfrin run was exercised on balfrin.
- Provenance: fixture-backed partial-state recovery evidence, not a live Balfrin interruption/recovery measurement.
- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_balfrin_restartability_recovery_v1`

## Partial State

- Run root: `/scratch/rust_rockfall/probes/balfrin-demo/fixture_partial`
- Trajectory chunks:
  - `chunk_000000`: `complete`
  - `chunk_000001`: `partial`
- Reducer chunks:
  - `chunk_000000`: `complete`
  - `chunk_000001`: `partial`
- Staged outputs were limited to run-root scratch artifacts such as `command_plan.json`, `probe.sbatch`, and logs.

## Resume Commands

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml --run-root /scratch/rust_rockfall/probes/balfrin-demo/fixture_partial --run-id tschamut_public_balfrin_restartability_recovery_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --submit
```

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/rust_rockfall/probes/balfrin-demo/fixture_partial
```

## Reused And Executed Chunks

- Reused chunks:
  - `trajectory/chunk_000000`
  - `reducer/chunk_000000`
- Executed chunks:
  - `trajectory/chunk_000001`
  - `reducer/chunk_000001`
- Chunk-count evidence:
  - trajectory reused: `1`
  - reducer reused: `1`
  - trajectory executed: `1`
  - reducer executed: `1`

## Numerical Stability

- Numerical artifact stability classification: `pass_hash_stable`
- Changed artifact count: `0`
- Changed paths: `[]`
- The recovery fixture is intended to show that resuming a partial state does not corrupt outputs or alter numerical artifacts.

## Artifact Hygiene

- Artifact hygiene classification: `pass_clean`
- Generated roots stayed inside the scratch run root.
- Placeholder second-site paths were avoided:
  - `data/processed/swisstopo/placeholder_second_site_v1`
  - `validation/private/placeholder_second_site_v1`
  - `hazard/results/placeholder_second_site_v1`

## Explicit Limits

- Fixture-backed recovery evidence only; no live interruption is claimed here.
- No distributed execution authorization is implied.
- No physics, sampling, or output-profile changes are introduced by this report.

## Live Interruption Status

- Status: `blocked_missing_inputs`
- Reason: no fresh live Balfrin interruption/resume experiment was run for this report.
- Live interruption job id: not recorded
- Live resume job id: not recorded
- This note is separate from the fixture-backed recovery evidence above.
