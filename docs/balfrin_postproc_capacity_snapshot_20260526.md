# Balfrin Postproc Capacity Snapshot - 2026-05-26

Status: live read-only scheduler snapshot for TB-598. This is a capacity
planning note for the next bounded diagnostic submission, not a performance
measurement.

Captured from `balfrin-ln003` at `2026-05-26T20:26:27+02:00`.

## Access And Hygiene

- SSH target: `balfrin`
- Remote user: `olifu`
- Remote repo checkout: `/users/olifu/work/rust_rockfall`
- Remote checkout status from preflight: clean
- Remote checkout head at capture: `6ecc0aaa1abdd0f2c8280279980833d25019f05a`
- `$SCRATCH`: `/scratch/mch/olifu`

The read-only access preflight completed with
`status=ready_for_read_only_collection` and `ready_for_pre_submit=true`.

## Postproc Nodes

`sinfo -p postproc` reported 14 CPU post-processing nodes:

| State | Nodes | Node list |
| --- | ---: | --- |
| reserved | 1 | `nid001232` |
| mixed | 1 | `nid001225` |
| idle | 12 | `nid[001226-001227,001229-001231,001233-001239]` |

Each listed `postproc` node reported 256 CPUs, 456704 MB memory, and a
partition time limit of `1-00:00:00`.

## Queue State

`squeue -p postproc` reported three running jobs and no pending jobs in the
preflight summary:

| Job ID | User | Name | State | Elapsed | Nodes | Node |
| --- | --- | --- | --- | ---: | ---: | --- |
| `4371509` | `olifu` | `tp-analysis-report` | `R` | `02:24:41` | 1 | `nid001225` |
| `4371858` | `sideris` | `interactive` | `R` | `01:47:03` | 1 | `nid001225` |
| `4371965` | `sideris` | `1` | `R` | `00:35:54` | 1 | `nid001225` |

No `postproc` jobs were pending at capture time. Current-user `postproc` count
was one.

## Running Olifu Job Root

`scontrol show job 4371509 -o` identified the running `olifu` job as outside
this repository:

- Job: `4371509`
- Name: `tp-analysis-report`
- Partition: `postproc`
- Runtime at inspection: `02:24:54`
- Time limit: `12:00:00`
- Requested resources: 1 node, 32 CPUs, 446 GB memory
- WorkDir: `/users/olifu/work/cra5_vs_era5`
- Command: `/users/olifu/work/cra5_vs_era5/slurm/balfrin_postproc_tp_analysis_report.sbatch`
- Stdout: `/scratch/mch/olifu/cra5_vs_era5/logs/tp-analysis-report-4371509.out`
- Stderr: `/scratch/mch/olifu/cra5_vs_era5/logs/tp-analysis-report-4371509.err`

This job should not block collection of `rust_rockfall` diagnostic roots. If
it is still running when a new diagnostic is submitted, avoid unnecessary
contention on `nid001225`; otherwise no `rust_rockfall` run root needs
collection before the next diagnostic.

## Next Executable Submission Size

The largest bounded diagnostic that should be submitted next is the explicit
32-zone single-node `postproc` diagnostic:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 32 \
  --reducer-chunks 4 \
  --reducer-workers 4 \
  --manifest-mode compact \
  --partition postproc \
  --time 00:45:00 \
  --format text
```

The corresponding dry plan keeps the run root under
`/scratch/mch/olifu/rust_rockfall/diagnostics/`, uses one node and 16 CPUs per
task, and materializes one `run_record.json` plus reducer-pressure outputs and
SLURM logs.

With 12 idle `postproc` nodes and no pending jobs, this run does not approach
the standing-clearance boundary of filling `postproc` for more than 6 hours.
Do not escalate to 40-zone, 48-zone, or 100-zone diagnostics until the 32-zone
run reaches a terminal state and its measured runtime, memory, output bytes,
file counts, manifest bytes, and scheduler metadata are collected.
