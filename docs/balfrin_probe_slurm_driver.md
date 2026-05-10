# Balfrin SLURM Probe Driver (SLURM-first)

This document defines a SLURM-first execution flow for conditional Tschamut probe runs.
It is intentionally focused on reliable job submission and reproducible artifact layout.
It does not add distributed-orchestration semantics (job arrays, cross-node reducer
coordination, or scheduler-driven chunk partitioning) in this stage.

## Why SLURM-first now

Recent balfrin probe runs have relied on ad-hoc SSH one-liners.
A SLURM-first driver is introduced to reduce risk from:

- brittle command quoting,
- inline Python/heredoc failures,
- inconsistent timing sidecars,
- `tmp` artifacts outside checked-in manifests,
- manual command replay and command-plan drift.

The driver keeps the current local single-node, chunked execution model but makes
execution reproducible and metadata-friendly on Balfrin.

## Execution modes

`scripts/submit_balfrin_probe.py` provides:

- `--dry-run`
  - Plan-only: prints resolved run root, command-plan path, generated SBATCH script,
    and script text.
  - No files are written.

- `--generate-only`
  - Writes the command-plan JSON and SBATCH script into a deterministic run root.
  - Does not submit a job.

- `--submit`
  - Writes artifacts and calls `sbatch` with `--parsable`.
  - Implemented but not exercised in this task.

- `--collect`
  - Reads an existing run root and emits a compact summary JSON.

- `--local-command-plan`
  - Regenerates and prints the command plan only.

## Run directory and file layout

Run roots are deterministic and isolated:

`$SCRATCH/rust_rockfall/probes/<probe_id>/<run_id>/`

Generated run files:

- `command_plan.json`
- `probe.sbatch`
- `balfrin_probe_full_time.txt`
- `balfrin_hazard_stage_time.txt`
- `balfrin_probe_summary.json`
- `balfrin_probe_context.txt`
- `logs/slurm-<jobid>.out`
- `logs/slurm-<jobid>.err`

`probe_id` defaults to a sanitized `run_id` from the generated command plan and
`run_id` can be supplied explicitly.

## SBATCH defaults and constraints

Default submit behavior:

- `--partition=postproc`
- `--time=00:30:00`
- `--nodes=1`
- `--ntasks=1`
- `--cpus-per-task=16`
- log files under `${RUN_ROOT}/logs/`

Constraints enforced by generation:

- no `--account` argument is emitted,
- no operational-only queue names (for example `s83opr`),
- no explicit GPU partition is selected.

## Generated shell environment

The generated script sets:

- `set -euo pipefail`
- `UV_CACHE_DIR=${SCRATCH}/.cache/uv` (default)
- `CARGO_TARGET_DIR=${SCRATCH}/rust_rockfall/target` (default)
- `OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}`

The script records run context at start:

- hostname
- UTC date
- SLURM identifiers
- run root
- probe manifest path
- command-plan path
- repository root and git hash

## Runtime command flow

The script writes a fresh command plan from the probe manifest,
then executes command-plan entries in order via an embedded Python runner.
By design it captures two timing sidecars:

- full command-sequence wall time,
- hazard-stage-only wall time (the command named `build_conditional_hazard_layers`).

After execution, it runs `collect_balfrin_probe_metrics.py` to produce a summary JSON.

## Metrics summary fields

`balfrin_probe_summary.json` includes (at minimum):

- probe manifest path
- git commit
- run root
- total wall seconds / output bytes / file count
- output write seconds and per-kind timing/bytes if available
- trajectory and reducer plan IDs where available
- trajectory/reducer orchestration decision counts

## Partition choice guidance

Use for CPU-only conditional probe workflows:

- `postproc`: standard default for moderate-to-large runs.
- `pp-short`: short exploratory runs when wall-time is known to be small.
- `pp-long`: long probe runs with expected multi-run overhead.
- `pp-serial`: single-threaded compatibility/profiling where needed.

## Operational notes

- Keep working directories and writable artifacts on `$SCRATCH`.
- Keep `$HOME` clean; avoid large generated output outside scratch or tracked paths.
- This driver is currently a single-job wrapper, not a job-array pipeline.
- Runtime outputs remain untracked and should be kept in ignored probe/output roots.

## Future extension path

Planned next stage (not implemented yet):

1. Single-job current execution (this stage).
2. Job array over trajectory chunks.
3. Reducer/merge dependency jobs.
4. Deterministic restart and stale-state recovery across arrays.

## Commands

Dry-run example:

```bash
python3 scripts/submit_balfrin_probe.py \
  validation/probes/tschamut_mid_scale_grid_probe_420x450_v1/tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_pilot_run.yaml \
  --dry-run
```

Generate-only example:

```bash
python3 scripts/submit_balfrin_probe.py \
  validation/probes/tschamut_mid_scale_grid_probe_420x450_v1/tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_pilot_run.yaml \
  --generate-only
```

Collect metrics example:

```bash
python3 scripts/submit_balfrin_probe.py \
  --collect --run-root /scratch/rust_rockfall/probes/tschamut_mid_scale_grid_probe_420x450_v1/abcd1234
```

`scripts/collect_balfrin_probe_metrics.py` can be run directly for post-hoc parsing:

```bash
python3 scripts/collect_balfrin_probe_metrics.py \
  --run-root /scratch/rust_rockfall/probes/tschamut_mid_scale_grid_probe_420x450_v1/abcd1234
```
