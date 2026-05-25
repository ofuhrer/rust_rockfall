# Balfrin Capacity Window TB-563

Date: 2026-05-25

This note records the Balfrin checkout sync and queue snapshot captured for
TB-563. It is a run-window note only; it does not authorize a claim upgrade,
non-`postproc` work, or Swiss-wide execution.

## Checkout Sync

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Previous remote HEAD: `24bdc5d8ae61aa79b654151265613c5cf869c2dd`
- Synced remote HEAD: `c4f5e202e30d9a1bb1cc1b398e0a87290e4065f9`
- Branch: `main`
- Sync mode: `git fetch origin main` followed by `git merge --ff-only origin/main`
- Remote status after sync: clean
- Sync transcript: `/tmp/tb563_balfrin_sync.txt`

The fresh Balfrin preflight report is preserved at
`/tmp/tb563_balfrin_preflight.json`. It reported:

- `status`: `ready_for_read_only_collection`
- `ready_for_pre_submit`: `true`
- `remote_checkout_hygiene.status`: `pass`
- `remote_head`: `c4f5e202e30d9a1bb1cc1b398e0a87290e4065f9`
- `dirty_path_count`: `0`
- stale regional split artifacts: `0`

## Queue Snapshot

- Snapshot file: `/tmp/tb563_postproc_capacity_snapshot.txt`
- Captured at: `2026-05-25T19:07:05Z`
- Host: `balfrin-ln002`
- User: `olifu`
- Partition: `postproc`
- Time limit: `1-00:00:00`

Observed node state:

| State | Nodes |
| --- | ---: |
| `idle` | 11 |
| `alloc` | 1 |
| `mix` | 1 |
| `resv` | 1 |

Queue state:

- Running jobs in `postproc`: 141
- Pending jobs in `postproc`: 0 observed in the captured queue snapshot
- Current `olifu` jobs in `postproc`: 0
- Other-user running jobs were concentrated on `nid001225` and `nid001226`.

## Run-Window Classification

Classification: `run_now`

Rationale: the remote checkout is aligned with `origin/main`, remote hygiene is
clean, scheduler queries work, no `olifu` jobs are occupying `postproc`, and
11 `postproc` nodes were idle at the absolute timestamp above. Bounded
single-node or otherwise reviewed `postproc` submissions can proceed through
the existing readiness, authorization-record, output-budget, and preservation
gates. This classification does not justify filling the partition for more
than 6 hours or using any non-`postproc` partition.
