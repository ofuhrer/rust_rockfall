# Balfrin Distributed Chunk Dry Run TB-605

Date: 2026-05-26

Status: completed bounded scheduler-observed chunk dry run on Balfrin
`postproc`.

Run root:
`/scratch/mch/olifu/rust_rockfall/distributed_dry_runs/tb605_20260526`

Remote checkout:
`15a4e63ee2f083bfd5be68a41f58ed0f8e8b51fd`

## Run Shape

The dry run used the Tschamut public conditional gate inputs and the existing
`scripts/build_hazard_layers.py` reducer scheduler controls:

- reducer worker/chunk count: `3`
- scheduler model: split `postproc` jobs with `afterok` dependencies
- chunk assignment: `chunk_index % scheduler_count == scheduler_index`
- final merge: one dependent `postproc` job reusing completed partial states
- output directory:
  `/scratch/mch/olifu/rust_rockfall/distributed_dry_runs/tb605_20260526/output`

The split jobs were chained rather than submitted concurrently so the current
single shared execution-plan file stayed deterministic. This still exercised
SLURM submission, `$SCRATCH` shared-state preservation, chunk partial-state
reuse, and final sorted merge on Balfrin.

## Scheduler Mapping

| Role | Job ID | SLURM name | State | Elapsed | Batch MaxRSS | Chunk ID |
| --- | --- | --- | --- | --- | --- | --- |
| chunk 0 | `4372410` | `tb605-c0` | `COMPLETED` | `00:00:09` | `5480K` | `tb605_scheduler_dry_run__chunk_0000` |
| chunk 1 | `4372411` | `tb605-c1` | `COMPLETED` | `00:00:05` | `5444K` | `tb605_scheduler_dry_run__chunk_0001` |
| chunk 2 | `4372412` | `tb605-c2` | `COMPLETED` | `00:00:05` | `5448K` | `tb605_scheduler_dry_run__chunk_0002` |
| merge | `4372413` | `tb605-merge` | `COMPLETED` | `00:00:05` | `5512K` | all chunks |

Accounting is preserved at:
`/scratch/mch/olifu/rust_rockfall/distributed_dry_runs/tb605_20260526/slurm_accounting.psv`

## Filesystem Evidence

Summary record:
`/scratch/mch/olifu/rust_rockfall/distributed_dry_runs/tb605_20260526/tb605_scheduler_chunk_dry_run_summary.json`

Final reducer manifests:

- `output/tb605_scheduler_dry_run_execution_plan_v1.json`
- `output/tb605_scheduler_dry_run_reducer_execution_index_v1.json`
- `output/tb605_scheduler_dry_run_reducer_merge_state_v1.json`

Partial states:

| Chunk ID | Partial state path | Bytes |
| --- | --- | ---: |
| `tb605_scheduler_dry_run__chunk_0000` | `output/chunks/tb605_scheduler_dry_run__chunk_0000_state.json` | `6,962,608` |
| `tb605_scheduler_dry_run__chunk_0001` | `output/chunks/tb605_scheduler_dry_run__chunk_0001_state.json` | `6,945,504` |
| `tb605_scheduler_dry_run__chunk_0002` | `output/chunks/tb605_scheduler_dry_run__chunk_0002_state.json` | `6,945,345` |

Measured footprint:

- run root: `68` files / `91,998,937` bytes
- final output directory: `49` files / `91,981,415` bytes
- stderr logs: empty for all chunk and merge jobs

## Result

The final execution plan reports:

- `plan_status`: `completed`
- `completed_chunk_count`: `3`
- `failed_chunk_count`: `0`
- `merge_order`: `sorted_chunk_id`
- `merge_group_id`: `eba46edcb927ace9b25ff7bd`

The final merge state reports `status: ready`.

This closes the local-only gap for scheduler-observed chunk splitting and
shared-filesystem partial-state reuse on Balfrin. It does not establish
Swiss-wide readiness, operational hazard-map readiness, physical-probability
semantics, non-`postproc` behavior, multi-node behavior, or concurrent
shared-plan write safety.
