# TB-304 Balfrin Remote Checkout Hygiene Report

Schema: `tb304_balfrin_remote_checkout_hygiene_v1`

Remote checkout: `/users/olifu/work/rust_rockfall`
SSH target: `balfrin`
Run root preservation boundary:
`/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`

This record preserves the before/after state for TB-304 remote-checkout
cleanup. It is limited to checkout hygiene. No `sbatch` command, live run,
non-`postproc` work, distributed execution, or scratch/evidence-root deletion is
authorized or recorded here.

## Before Cleanup

Collected: `2026-05-19T18:57:45Z`
Command:
`PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`

- Preflight status: `blocked_dirty_remote_checkout`
- Remote branch: `main`
- Remote HEAD: `a2c4831b52e34e5b772c560ad6cc4faa65886853`
- Tracked modifications: none
- Dirty path count: 18

Tracked modifications:

- none

Untracked generated files:

- `balfrin_submission_package.json`
- `balfrin_submission_package.md`
- `command_plan.json`
- `probe.sbatch`

Untracked generated/checkout-clutter files:

- `balfrin_hazard_stage_time.txt`
- `balfrin_probe_context.txt`
- `balfrin_probe_full_time.txt`
- `balfrin_probe_summary.json`
- `compare_baseline_12_vs6.py`
- `extract_20_12traj_metrics.py`
- `extract_20_12traj_metrics2.py`
- `extract_metadata_keys.py`
- `extract_metrics_runtime.py`
- `tmp_run_20cell12traj_balfrin.py`

Stale submission packages:

- `balfrin_submission_package.json`
- `balfrin_submission_package.md`
- `command_plan.json`
- `probe.sbatch`

Stale SLURM/log files:

- `logs/slurm-4326016.err`
- `logs/slurm-4326016.out`
- `slurm-4289608.out`
- `slurm-4289610.out`

Cleanup plan before any remote deletion:

- Preserve remote file metadata and content for all 18 paths in a compressed
  archive outside the checkout at
  `/users/olifu/work/tb304_remote_checkout_cleanup_20260519T185745Z.tgz`.
- Remove only the 18 listed untracked files from
  `/users/olifu/work/rust_rockfall`.
- Do not touch tracked files, `/scratch`, preserved run roots, evidence roots,
  or any scheduler state.

## Cleanup Actions

- Created preservation manifest:
  `/users/olifu/work/tb304_remote_checkout_cleanup_20260519T185745Z_manifest.txt`
- Created preservation archive:
  `/users/olifu/work/tb304_remote_checkout_cleanup_20260519T185745Z.tgz`
- Removed only the 18 listed untracked checkout paths from
  `/users/olifu/work/rust_rockfall`.
- Deferred tracked-file cleanup because there were no tracked modifications.
- Deferred scratch/evidence cleanup by policy; no `/scratch` path or preserved
  run root was touched.

## After Cleanup

Collected: `2026-05-19T19:01:09Z`
Command:
`PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`

- Preflight status: `ready_for_read_only_collection`
- Remote branch: `main`
- Remote HEAD: `a2c4831b52e34e5b772c560ad6cc4faa65886853`
- Tracked modifications: none
- Dirty path count: 0
- Untracked generated files: none
- Untracked other files: none
- Stale submission packages: none
- Stale SLURM/log files: none

Remaining non-clean state accepted or blocked for next task: none from the
remote checkout hygiene gate. The remote checkout may still need to be
fast-forwarded by the next live-run worker before package-specific gates, but
TB-304 cleared the stale generated-file blocker without submitting work.
