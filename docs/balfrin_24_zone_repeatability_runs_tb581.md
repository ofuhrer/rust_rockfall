# Balfrin 24-Zone Repeatability Runs TB-581

Date: 2026-05-26

This note records two additional 24-zone diagnostic `postproc` runs launched
after the queue planner classified the batch as `run_batch_now`.

## Queue Gate

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote commit: `5f9c93790cfa89855fdbbb3d30be81a31298bb50`
- Planner classification: `run_batch_now`
- Idle `postproc` nodes: 12
- Planner blockers: none
- Six-hour partition-fill check: passed

## Results

| Run id | Job id | State | Elapsed | MaxRSS MB | Reducer wall s | Files | Bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `diagnostic_24_zone_repeatability_a_tb581` | 4368592 | `COMPLETED` | 0:00.34 | 34.242 | 4.03 | 76 | 32,922 |
| `diagnostic_24_zone_repeatability_b_tb581` | 4368593 | `COMPLETED` | 0:00.34 | 39.879 | 4.03 | 76 | 32,922 |

Run records:

- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_a_tb581/run_record.json`
- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_b_tb581/run_record.json`

## Boundary

These are repeatability diagnostics for single-node `postproc` reducer pressure.
They do not establish operational hazard-map readiness, physical probability,
annual frequency, risk semantics, Swiss-wide execution, distributed execution,
or non-`postproc` partition capability.
