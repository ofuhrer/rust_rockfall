# TB-683 Concurrent Hazard-Throughput Balfrin Blocked Report

Date: 2026-05-31

TB-683 attempted to exercise concurrent bounded hazard-throughput jobs on
Balfrin `postproc`, but stopped before submission because the scheduler
reported `postproc` as down. No jobs were submitted.

## Preflight

- SSH access: ready
- Remote checkout: clean, branch `main`, head
  `4b335c03e02e7d2e65704a3ae74e9662a3f2d42f`
- Existing hazard-throughput run-root visibility check: pass for
  `/scratch/mch/olifu/rust_rockfall/probes/tb680_24_zone_hazard_throughput_preserved_20260527_145422`
- Read-only preflight status: `ready_for_read_only_collection`
- Live submission status: blocked by scheduler state

## Scheduler Snapshot

Read-only scheduler inspection at `2026-05-31T20:20:11Z` reported:

| Partition | Availability | Node state | Nodes | Reason / note |
| --- | --- | --- | ---: | --- |
| `postproc` | `down` | `mix` | 8 | partition unavailable |
| `postproc` | `down` | `alloc` | 5 | partition unavailable |
| `postproc` | `down` | `idle` | 1 | partition unavailable despite idle node |

The queue had `22` pending `postproc` jobs and `0` current-user jobs. The
visible pending jobs were all held with reason `PartitionDown`.

## Filesystem Snapshot

`$SCRATCH` was visible and mounted as Lustre:

- Path: `/scratch/mch`
- Capacity: `800T`
- Used: `740T`
- Available: `61T`
- Use: `93%`

The stop decision was driven by scheduler unavailability, not a failed scratch
visibility check.

## Outcome

- Concurrent hazard-throughput jobs submitted: `0`
- Terminal job count: `0`
- Per-job metrics collected: none
- Run-root isolation verified for new jobs: not applicable, because no jobs
  were submitted
- Contention result: `blocked_scheduler_partition_down`

The intended bounded plan would have used multiple distinct `$SCRATCH` roots
and the existing hazard-throughput profiler, but it was not executed under the
task rule to stop when scheduler behavior indicates stress or unavailability.

## Boundary

This report is a blocked live Balfrin inspection result only. It does not
provide concurrent hazard-throughput evidence, distributed-execution evidence,
Swiss-wide evidence, physical-probability evidence, annual-frequency evidence,
operational evidence, or risk/exposure/vulnerability evidence.
