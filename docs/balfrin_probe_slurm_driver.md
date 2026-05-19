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
  - The generated package is explicitly marked `deferred_pending_authorization` and carries
    the recomputed frontier recommendation, reduced-output settings, metrics
    collection command, and stop/resume notes.
  - Does not submit a job.

- `--submit`
  - Writes artifacts and calls `sbatch` with `--parsable`.
  - Exercised for the authorized TB-168 target-area probe as job `4329024`.
  - Must not be used for a future live run unless the user has explicitly
    authorized that exact bounded run and a GPT-5.5 Balfrin worker is executing
    the submission after the required preflights pass.

- `--authorized-submit`
  - Writes artifacts and calls `sbatch` only after a reviewed handoff package
    and live-run authorization record are both supplied and validated.
  - This is the fail-closed path for the smallest bounded multi-zone Balfrin
    probe; it returns `blocked_missing_authorization` or
    `blocked_missing_inputs` instead of submitting when either gate is absent.
  - The authorization record is necessary but not sufficient: the user must also
    explicitly instruct the worker to submit the exact run in the current
    orchestration context.

- `--collect`
  - Reads an existing run root and emits a compact summary JSON.

- `--local-command-plan`
  - Regenerates and prints the command plan only.

## Balfrin checkout and scratch boundary

Run submission commands from the Balfrin checkout:

`/users/olifu/work/rust_rockfall`

Do not assume a git checkout exists under `/scratch/mch/olifu/rust_rockfall/main`.
The `/scratch/mch/olifu/rust_rockfall/...` tree is reserved for generated run roots,
the shared Cargo target directory, caches, and other ignored execution artifacts.
Before a live submission, fast-forward the checkout and run readiness checks from
`/users/olifu/work/rust_rockfall`; then write the deterministic run root under
scratch.

## Live-run authorization protocol

This repository does not carry standing authorization for additional live
Balfrin runs. A future live run can proceed only under all of the following
conditions:

- the user explicitly instructs the agent to submit the exact bounded Balfrin
  run, naming the target package, manifest, run root, or probe;
- the orchestrator routes the task to a GPT-5.5 Balfrin worker;
- the worker includes the exact authorization text in its task context and does
  not broaden the scope beyond that single named run;
- the Balfrin checkout is fast-forwarded, the local worktree context is clean,
  and the access preflight, package-specific readiness or authorization
  preflight, reviewed handoff package, reduced-output/output-budget checks, and
  any preservation or post-run evidence gates required by the package all pass;
- the final report records the job id, run root, gates run, and scientific
  boundary note.

The following are not live-run authorization: `--dry-run`, `--generate-only`, a
generated `probe.sbatch`, a ready command plan, a preflight status such as
`ready_for_authorization_review`, a backlog task that asks for package
preparation, a request to inspect or collect existing evidence, or a previous
authorization for a different Balfrin run. Authorization for one run does not
authorize retries, larger ensembles, multi-node or distributed execution,
second-site execution, Swiss-wide scale-up, annual-frequency products, physical
probability claims, risk/exposure/vulnerability products, regulatory use, or
operational claims.

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

For the multi-zone TB-211 path, the later submit command now uses
`--authorized-submit` together with explicit `--reviewed-handoff-package` and
`--authorization-record` arguments. The command will refuse to submit without
both of those inputs.

Before that submit path can call `sbatch`, it now runs the smallest multi-zone
authorization preflight:

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py \
  --reviewed-handoff-package /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml \
  --format json
```

The preflight is deterministic for a supplied package, authorization record,
and Balfrin access report. It records the exact smallest run shape, reducer
budget, reduced-output profile, and preservation checklist, but it does not
grant authorization. The gate reports `ready_for_authorization_review` only
when the reviewed package, live-run authorization record, read-only Balfrin
access preflight, reducer-budget checks, and reduced-output profile are all
ready. Missing authorization returns `blocked_missing_authorization`; expired
SSH, missing remote artifacts, and scheduler-query blockers return
`blocked_access` while preserving the exact consumed Balfrin access status; and
over-budget reducer or compact handoff settings return `blocked_reducer_budget`
before any submission artifacts are written.

TB-248 adds the read-only checklist wrapper for the post-authorization path:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py \
  --authorization-preflight validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml \
  --format json
```

The wrapper does not submit jobs. It binds the exact authorization preflight
output, reviewed handoff package, authorization record, documented
`--authorized-submit` command, deterministic run root, post-run metrics
collector, preservation gate, post-run evidence collector, and closure-package
input path into one machine-readable checklist. If the TB-247 preflight remains
`blocked_reducer_budget`, if the authorization record is absent, or if Balfrin
access is lost, the wrapper emits a blocked report and leaves
`submit_command_executed=false`.

After a future explicitly authorized run completes, pass the preserved run root
back to the same helper:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py \
  --authorization-preflight validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml \
  --run-root /scratch/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 \
  --balfrin-access-json /tmp/balfrin_access_preflight.json \
  --format json
```

The post-run branch can promote evidence only when the collector reports
`measured_complete`, the preservation gate reports
`ready_for_demonstration_evidence`, and the closure-package input compatibility
is `compatible`. Incomplete run roots, fixture-backed roots, missing
authorization, access loss, or unavailable non-git artifacts remain blocked and
cannot be treated as measured evidence.

The frozen target-area demonstration contract is
`validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`.
Its `balfrin_execution_boundary.command_plan_hook.command` is the read-only
hook for inspecting the frozen Balfrin command plan without launching a job.
Its `balfrin_execution_boundary.remote_repo_root` records the canonical Balfrin
checkout path used for live submission.

Before read-only collection or inspection work that depends on live Balfrin
state, run the fail-closed access preflight:

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json
```

The helper uses SSH `BatchMode=yes` and `ConnectTimeout=10` by default. It checks
the `balfrin` SSH target, the expected checkout
`/users/olifu/work/rust_rockfall`, remote checkout hygiene, the preserved
non-git run root
`/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`,
and read-only scheduler reachability through `squeue`. The checkout-hygiene
gate records the remote branch and HEAD, tracked modifications, untracked
generated files, stale submission packages, stale SLURM/log files, and exact
preserve/inspect/clean commands for an operator to run before any future
package generation or submission. It reports `ready_for_read_only_collection`,
`blocked_ssh_unavailable`, `blocked_missing_remote_clone`,
`blocked_dirty_remote_checkout`, `blocked_missing_run_root`, or
`blocked_scheduler_unavailable`; it does not submit jobs, delete files, or write
remote files.

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

The TB-168 authorized target-area probe used:

- `job_id=4329024`
- `run_root=/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`
- `partition=postproc`
- `--cpus-per-task=16`, `--time=00:30:00`
- SLURM state `COMPLETED`, exit `0:0`, elapsed `00:00:43`
- `output_file_count=58`
- `output_bytes=192,350,243`
- `conditional_curve_row_count=729600`

The probe was measured, but the metrics contract still reports missing peak
memory and split validation/hazard output counts and bytes. Those completeness
gaps are intentionally left to the next metrics task rather than backfilled.

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
The collected run must then pass `scripts/summarize_balfrin_probe_preservation_gate.py`
before it is treated as evidence rather than only as an execution attempt.
The preservation gate materializes a deterministic JSON/text report that lists
the required metrics, preserved run-root files, SLURM accounting fields,
output-family summaries, and declared GIS artifact paths for the next
authorized live run.

For the metrics-completion rerun package that closes only the missing
target-area peak-memory and split validation/hazard output metrics, use
`scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`.
It stays read-only, emits the dry-run rerun plan and SBATCH package, and keeps
the comparison against the recorded target-area run separate from any live
submission path.
Its `post_attempt_integration_notes` section classifies the current branch as
`submitted`, `blocked_pre_submit`, `failed_closed`, or `no_authorization`.
Only a submitted run that later passes the preservation gate may promote
measured evidence; blocked, unauthorized, or failed-closed states remain
planning or failure evidence with one exact remaining precondition.

Before requesting that rerun, use
`scripts/recover_balfrin_target_area_metrics_from_run_root.py` with the TB-223
access preflight JSON. The recovery helper targets the existing authorized
target-area run root, runs only read-only collection, and reports whether each
rerun target metric is `recovered`, `still_missing`,
`unavailable_from_preserved_root`, or `blocked_access`. The comparison section
states whether the metrics-completion rerun is still necessary; it does not
authorize or launch a job.

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
