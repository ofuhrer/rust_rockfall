# TB-671 Concurrent Postproc Diagnostics

Date: 2026-05-27

TB-671 submitted a bounded concurrent diagnostic set on Balfrin `postproc` to
check scheduler behavior and `$SCRATCH` run-root isolation.

## Run Set

- Base root:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb671_concurrent_20260527_131408`
- Aggregate report:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb671_concurrent_20260527_131408/tb671_concurrent_summary.json`
- Job count: `3`
- Diagnostic shape per job: `16` release zones, `2` reducer chunks, `2` reducer workers, compact manifest mode
- Run roots isolated: `true`
- All jobs terminal completed: `true`
- Maximum observed concurrent top-level jobs: `2`

## Per-Job Metrics

| Job | Run root | State | SLURM elapsed | `/usr/bin/time` elapsed | Peak RSS MB | Output files | Output bytes | Run-root files | Run-root bytes |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `4378322` | `job_1` | `COMPLETED` | `00:00:01` | `0:00.39` | `33.801` | `52` | `23,661` | `65` | `118,173` |
| `4378358` | `job_2` | `COMPLETED` | `00:00:01` | `0:00.35` | `34.336` | `52` | `23,661` | `65` | `118,171` |
| `4378359` | `job_3` | `COMPLETED` | `00:00:01` | `0:00.36` | `34.297` | `52` | `23,661` | `65` | `118,170` |

## Aggregate

- Aggregate output files: `156`
- Aggregate output bytes: `70,983`
- Aggregate run-root files: `195`
- Aggregate run-root bytes: `354,514`
- Reducer wall-time range: `3.07` to `3.07` seconds
- Output-byte range: `23,661` to `23,661`
- Contention status: `no_contention_detected`

## Boundary

This is measured concurrent single-node `postproc` diagnostic reducer-pressure
evidence with isolated run roots. It is not hazard-throughput evidence,
distributed execution evidence, non-`postproc` evidence, physical-probability
evidence, operational evidence, or Swiss-wide execution evidence.
