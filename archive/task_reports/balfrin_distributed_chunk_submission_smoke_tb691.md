# TB-691 Balfrin Distributed Chunk Submission Smoke

Date: 2026-05-31

## Result

Status: blocked fail-closed before execution.

The minimal distributed chunk submission smoke was submitted to Balfrin
`postproc`, but the authorized partition was unavailable before any chunk
payload ran. The first missing piece was the scheduler partition state:
`postproc` reported `State=DOWN`, and all submitted jobs remained pending with
`Reason=PartitionDown`.

Run root:

`/scratch/mch/olifu/rust_rockfall/distributed_chunk_submission_smokes/tb691_20260531_214135`

## Submission Shape

The attempted smoke prepared a scratch-only two-chunk workflow:

- chunk job `4408922`, SLURM name `tb691-c0`
- chunk job `4408923`, SLURM name `tb691-c1`
- dependent collector job `4408924`, SLURM name `tb691-collect`
- target partition: `postproc`
- requested resources per job: 1 node, 1 task, 1 CPU, 256 MB, 3 minutes

The scratch run root contains the generated worker and collector scripts plus a
fail-closed summary record:

`/scratch/mch/olifu/rust_rockfall/distributed_chunk_submission_smokes/tb691_20260531_214135/fail_closed_summary.json`

## Scheduler Evidence

The jobs reached terminal state only after cancellation of the blocked pending
submission:

| Job ID | Name | Partition | State | Exit code | Elapsed |
| --- | --- | --- | --- | --- | --- |
| `4408922` | `tb691-c0` | `postproc` | `CANCELLED by 21028` | `0:0` | `00:00:00` |
| `4408923` | `tb691-c1` | `postproc` | `CANCELLED by 21028` | `0:0` | `00:00:00` |
| `4408924` | `tb691-collect` | `postproc` | `CANCELLED by 21028` | `0:0` | `00:00:00` |

The job detail for `4408922` reported:

- `JobState=PENDING`
- `Reason=PartitionDown`
- `Partition=postproc`
- `ReqTRES=cpu=1,mem=256M,node=1,billing=1`

The partition detail reported:

- `PartitionName=postproc`
- `State=DOWN`
- `TotalNodes=14`
- `TotalCPUs=3584`

## Boundary

This is a submission-attempt and scheduler-availability report only. It does
not establish completed distributed chunk execution, deterministic merge output,
Swiss-wide execution, operational hazard assessment, annual frequency, physical
probability, risk, exposure, vulnerability, non-`postproc` behavior, MPI/GPU
behavior, or scale-up readiness.
