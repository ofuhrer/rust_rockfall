# TB-664 Balfrin Readiness For Next Scale Run

Date: 2026-05-27

## Result

Balfrin SSH, the remote checkout, the preserved target-area run root, and the
`postproc` scheduler query are reachable from the desktop checkout. The current
read-only preflight reports:

- status: `ready_for_read_only_collection`
- ready for pre-submit: `true`
- remote checkout: `/users/olifu/work/rust_rockfall`
- remote branch: `main`
- remote head: `4b335c03e02e7d2e65704a3ae74e9662a3f2d42f`
- remote checkout hygiene: `pass`
- checked run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`

The local head at the time of the check was:

```text
c11917e207e6f6b36fb1d40449f31ee8cb2d8c8b
```

The remote checkout is clean but does not match the local head. The next
diagnostic can still run because the remote checkout already contains the
simplified diagnostic runner, but the mismatch should be fixed before relying
on newer local-only reporter or surface changes.

## Current Postproc Capacity

The scheduler query captured at `2026-05-27T11:33:19Z` reported:

- partition: `postproc`
- node states: `mixed|4|1-00:00:00`, `idle|9|1-00:00:00`
- running jobs: `180`
- pending jobs: `1`
- current-user jobs: `1`

This is busier than the older TB-598 snapshot, but there are still idle
`postproc` nodes. A single-node diagnostic run with a 45-minute limit remains
within the standing clearance boundary and does not fill the partition for more
than 6 hours.

## Next Executable Run Shape

The next run should use the remote Balfrin checkout and keep all generated data
under `$SCRATCH`:

```bash
cd /users/olifu/work/rust_rockfall
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 32 \
  --reducer-chunks 4 \
  --reducer-workers 4 \
  --manifest-mode compact \
  --partition postproc \
  --time 00:45:00 \
  --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527 \
  --poll-seconds 10 \
  --monitor-timeout-seconds 3600 \
  --format json
```

The Balfrin-side dry plan for this exact shape returned `status=planned` with:

- release zones: `32`
- reducer chunks: `4`
- reducer workers: `4`
- manifest mode: `compact`
- output family mix: `trajectory_csv`, `deposition_csv`,
  `impact_events_csv`, `trajectory_merge_state`, `reducer_merge_state`
- partition: `postproc`
- nodes: `1`
- tasks: `1`
- CPUs per task: `16`
- time limit: `00:45:00`
- run root:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527`

## Boundary

This is a readiness and plan record only. No job was submitted for TB-664. The
planned run is diagnostic reducer-pressure evidence only, not operational,
physical-probability, annual-frequency, hazard-throughput, distributed,
Swiss-wide, or non-`postproc` evidence.
