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
  - Writes the command-plan JSON, SBATCH script, submission package report, and
    collection instructions into a deterministic run root.
  - The generated package is explicitly marked `blocked_unlaunched` and carries
    the recomputed frontier recommendation, reduced-output settings, metrics
    collection command, and stop/resume notes.
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
- `balfrin_submission_package.json`
- `balfrin_submission_package.md`
- `balfrin_probe_full_time.txt`
- `balfrin_hazard_stage_time.txt`
- `balfrin_probe_summary.json`
- `balfrin_probe_context.txt`
- `logs/slurm-<jobid>.out`
- `logs/slurm-<jobid>.err`

`probe_id` defaults to a sanitized `run_id` from the generated command plan and
`run_id` can be supplied explicitly.

The submission package is the dry-run handoff. Inspect
`balfrin_submission_package.json` and `balfrin_submission_package.md` before
any later launch, because they record the exact run root, the bounded
next-probe recommendation, the reduced-output controls, the metrics collection
command, and the stop/resume boundary.

The frozen target-area demonstration contract is
`validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`.
Its `balfrin_execution_boundary.command_plan_hook.command` is the read-only
hook for inspecting the frozen Balfrin command plan without launching a job.

Target-area public-geodata readiness for that frozen contract is currently
`ready_for_frozen_target_area_demo` at the tracked contract level:

- the public real-site manifest
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` validates;
- the frozen source-zone metadata, release/deposition CSVs, scenario table,
  source-scenario policy, and conditional pilot gate record are present in the
  checkout;
- generated raw geodata, private validation outputs, and hazard outputs remain
  ignored and are not committed;
- this readiness classification is only for the selected Tschamut target-area
  demonstration contract. It is separate from the Chant Sura / Fluelapass
  second-site public-context readiness track, which remains blocked or
  deferred until real second-site inputs are staged.

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

## Clean-fresh SLURM baseline evidence (420×450 grid)

A fresh baseline on balfrin used the tracked 420×450 grid probe manifest:

`validation/probes/tschamut_mid_scale_grid_probe_420x450_v1/tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_pilot_run.yaml`

Commit provenance:

- `Fix SLURM probe heredoc quote stripping` (`61ab9c6`)

Submitted run:

- `job_id=4289703`
- `run_root=/scratch/mch/olifu/rust_rockfall/probes/slurm_smoke_420x450/fresh_baseline_ee8c4eb`
- `partition=postproc`
- `--cpus-per-task=16`, `--time=00:30:00`

Observed summary:

- `balfrin_probe_full_time.txt`: `23.446129538002424`
- `balfrin_hazard_stage_time.txt`: `15.635101707070135`
- `total_wall_seconds`: `14.95406103390269`
- `output_bytes`: `32,124,738`
- `output_file_count`: `46`
- `output_write_seconds`: `5.986803226056509`
- `trajectory_decision_counts`: `executed: 2`
- `reducer_decision_counts`: `executed: 2`
- trajectory plan id:
  `validation_tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_probe_v1__trajectory_execution_plan__75b0ef839657fa96a9fed7d6`
- reducer plan id:
  `validation_tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_probe_v1__execution_plan__b26a5e3da0a3cf72f6e550d3`

Command-plan controls validated for this run:

- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--trajectory-workers 2`
- `--reducer-workers 2`
- `--export-geotiff`
- `--no-plots`
- `--pilot-gis-package` enabled

Log/audit findings:

- no repo-path quoting warning
- no fatal git warning
- no `--account`
- no operational / GPU partition usage
- job completed cleanly with exit `0:0`

Collector log-audit summary:

- `collect_balfrin_probe_metrics.py` also records a `log_audit` block for `run_root/logs/` with:
  - `file_count`
  - `matched_line_count`
  - `warning_like_line_count`
  - `error_like_line_count`
  - `affected_log_paths`
  - per-file matched line counts
- Review this summary together with the job exit status, command-plan controls, and decision counts.
- Use the affected paths to inspect the exact `slurm-<jobid>.out` and `slurm-<jobid>.err` files before deciding whether a warning-like or error-like match is expected environment chatter or a real probe issue.
- For conditional probe evidence, treat this as a log-audit smoke check only.
- It does not prove numerical correctness, output completeness, reproducibility, or operational readiness.
- It also does not prove the absence of all failures, because it only scans the log tree with keyword matching.

Important run-history note:

- The earlier first submitted job `4289616` completed successfully but reused previously
  persisted chunk state.
- Fresh baseline semantics therefore used a second run (`4289703`) after removing
  pre-existing `chunks/` and `trajectory_chunks/` for the same output root so the run
  executed `executed` chunks end-to-end.

## DT-03 repeat/reuse closure

The DT-03 repeat/reuse record is
`validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`.
It classifies the tracked 420×450 probe as `pass_with_scope_limits` and the
single-job SLURM driver as ready for same-scale selected-gate reproduction under
the same output controls.

Evidence summary:

- fresh baseline job `4289703` executed both trajectory and reducer chunks;
- repeat jobs `4318872` and `4318896` reused both trajectory and reducer chunks
  through `reused_completed_state`;
- trajectory and reducer plan IDs stayed stable across repeats;
- a before/after hash check around the second repeat found `33/33` numeric
  hazard artifacts unchanged;
- repeat log audits had zero warning-like and zero error-like matches.

Decision:

- continue using the single-job SLURM driver for the next same-scale selected
  Tschamut conditional hazard-map reproduction;
- do not add SLURM arrays, distributed reducers, MPI, GPU execution, or
  production orchestration from this evidence alone.

## Metrics summary fields

`balfrin_probe_summary.json` includes (at minimum):

- probe manifest path
- git commit
- run root
- total wall seconds / output bytes / file count
- output write seconds and per-kind timing/bytes if available
- trajectory and reducer plan IDs where available
- trajectory/reducer orchestration decision counts
- `log_audit` summary for `run_root/logs/`

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
- To launch later, reuse the same checkout, `RUN_ROOT`, and `RUN_ID`; do not
  create a branch or commit generated run artifacts first.

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

The generate-only package report also records:

- the requested SLURM partition, wall-time, node, task, and CPU settings,
- repository branch and commit,
- readiness-check input status and blocking checks,
- the frontier recommendation and reduced-output settings for the smallest
  recommended next probe,
- generated package roots under the run directory,
- ignored Balfrin output roots from the resolved command plan,
- expected package outputs,
- collection commands for the metrics helper and `--collect` mode.
