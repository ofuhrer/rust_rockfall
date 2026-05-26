# Balfrin 32-Zone Diagnostic Run TB-599

Date: 2026-05-26

This note records the completed 32-zone diagnostic `postproc` run. It is
single-node reducer-pressure evidence only; it is not an operational,
physical-probability, Swiss-wide, distributed, or non-`postproc` result.

## Run

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote commit: `ac1aed47a374572ef200b2752cf5aeb06c62ee13`
- Run id: `diagnostic_32_zone_tb599_20260526`
- Run root: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_32_zone_tb599_20260526`
- Run record: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_32_zone_tb599_20260526/run_record.json`
- Slurm job id: `4372124`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`

Command:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 32 --reducer-chunks 4 --reducer-workers 4 --manifest-mode compact --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_32_zone_tb599_20260526 --partition postproc --time 00:45:00 --poll-seconds 10 --format json
```

## Metrics

| Metric | Value |
| --- | ---: |
| Release zones | 32 |
| Reducer chunks | 4 |
| Reducer workers | 4 |
| Reducer wall time | 5.39 s |
| `/usr/bin/time -v` elapsed | 0:00.75 |
| MaxRSS | 34.168 MB |
| Diagnostic output files | 100 |
| Diagnostic output bytes | 42,221 |
| Manifest size | 24,514 bytes |
| Pressure-root files | 105 |
| Pressure-root bytes | 73,933 |
| Run-root files | 113 |
| Run-root bytes | 181,433 |

## Scheduler Accounting

| Job ID | State | Elapsed | MaxRSS | ReqCPUS | AllocCPUS |
| --- | --- | ---: | ---: | ---: | ---: |
| `4372124` | `COMPLETED` | `00:00:01` |  | 16 | 16 |
| `4372124.batch` | `COMPLETED` | `00:00:01` | `5416K` | 16 | 16 |
| `4372124.extern` | `COMPLETED` | `00:00:01` | `716K` | 16 | 16 |

## Boundary

This run extends measured single-node diagnostic post-processing evidence from
24 to 32 release zones. The run root stays on `$SCRATCH`; no large data was
stored under `/tmp`. TB-600 is responsible for promoting this measured run into
the scale evidence surfaces so future projections read the 32-zone result as
measured evidence.
