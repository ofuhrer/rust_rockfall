# Balfrin Chunk Restartability Recovery TB-606

Date: 2026-05-26

Status: measured bounded chunk-recovery run on Balfrin `postproc`.

Run root:
`/scratch/mch/olifu/rust_rockfall/restartability/tb606_20260526_v2`

Source run root:
`/scratch/mch/olifu/rust_rockfall/distributed_dry_runs/tb605_20260526`

Remote checkout:
`4514485ca382dc67abed6eec41cb6d3e3fdbfff7`

## Recovery Setup

The recovery run copied the completed TB-605 output tree into a fresh `$SCRATCH`
root, rewrote preserved absolute manifest paths from the TB-605 source root to
the new TB-606 root, and then removed one reducer partial state:

`output/chunks/tb605_scheduler_dry_run__chunk_0001_state.json`

Removed state size: `6,945,504` bytes.

The path rewrite matters: the chunk manifests store absolute partial-state
paths, so a copied recovery root must point those paths at the copied root
before a missing-state intervention is meaningful.

## Scheduler Evidence

| Role | Job ID | SLURM name | State | Elapsed | Batch MaxRSS |
| --- | --- | --- | --- | --- | --- |
| recover chunk 1 | `4372418` | `tb606v2-c1` | `COMPLETED` | `00:00:06` | `3064K` |
| merge | `4372419` | `tb606v2-merge` | `COMPLETED` | `00:01:01` | `387104K` |

Accounting is preserved at:
`/scratch/mch/olifu/rust_rockfall/restartability/tb606_20260526_v2/slurm_accounting.psv`

## Recovery Result

The after-recovery execution plan recorded:

- target chunk: `tb605_scheduler_dry_run__chunk_0001`
- target chunk decision: `completed_state_reset_for_rerun`
- target chunk attempt count: `2`
- non-target chunks: `not_scheduled`

The final merge recorded:

- final execution-plan status: `completed`
- completed chunks: `3`
- failed chunks: `0`
- reducer merge state: `ready`
- merge order: `sorted_chunk_id`
- merge group id: `eba46edcb927ace9b25ff7bd`

Hash comparison for stable hazard products:

- baseline files: `37`
- recovered files: `37`
- changed artifact count: `0`
- classification: `pass_hash_stable`

Measured footprint:

- final output directory: `49` files / `91,981,158` bytes
- recovery run root: `66` files / `92,065,087` bytes
- stderr logs: empty for recovery and merge jobs

Summary artifacts:

- `tb606_restartability_recovery_summary.json`
- `tb606_restartability_evidence.json`
- `tb606_restartability_report.json`
- `tb606_restartability_report.md`
- `after_recover_execution_plan_v1.json`
- `after_recover_reducer_execution_index_v1.json`

## Boundary

This is measured bounded `postproc` restartability evidence for one copied
TB-605 run root and one removed reducer partial state. It does not establish
Swiss-wide readiness, operational hazard-map readiness, physical-probability
semantics, non-`postproc` behavior, multi-node behavior, or concurrent
shared-plan write safety.
