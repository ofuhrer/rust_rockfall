# Balfrin 40-Zone Diagnostic Run TB-601

Date: 2026-05-26

This note records the completed 40-zone diagnostic `postproc` run launched
after the measured 32-zone diagnostic completed cheaply. It is single-node
reducer-pressure evidence only; it is not an operational,
physical-probability, Swiss-wide, distributed, or non-`postproc` result.

## Decision

At `2026-05-26T21:08:19+02:00`, `postproc` had 11 idle nodes, 2 mixed nodes,
and 1 reserved node. The queue was busier than the TB-598 snapshot, but the
candidate run used one node, 16 CPUs, `$SCRATCH`, and a `00:45:00` walltime
request, so it did not approach the standing-clearance boundary of filling
`postproc` for more than 6 hours.

## Run

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote commit: `980026004604fb0f8747d76d5e0272a87c6130b8`
- Run id: `diagnostic_40_zone_tb601_20260526`
- Run root: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_40_zone_tb601_20260526`
- Run record: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_40_zone_tb601_20260526/run_record.json`
- Slurm job id: `4372257`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`

Command:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 40 --reducer-chunks 4 --reducer-workers 4 --manifest-mode compact --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_40_zone_tb601_20260526 --partition postproc --time 00:45:00 --poll-seconds 10 --format json
```

## Metrics

| Metric | Value |
| --- | ---: |
| Release zones | 40 |
| Reducer chunks | 4 |
| Reducer workers | 4 |
| Reducer wall time | 6.35 s |
| `/usr/bin/time -v` elapsed | 0:01.40 |
| MaxRSS | 33.902 MB |
| Diagnostic output files | 124 |
| Diagnostic output bytes | 51,493 |
| Manifest size | 28,818 bytes |
| Pressure-root files | 129 |
| Pressure-root bytes | 90,261 |
| Run-root files | 137 |
| Run-root bytes | 212,134 |

## Boundary

This run extends measured single-node diagnostic post-processing evidence from
32 to 40 release zones. The run root stays on `$SCRATCH`; no large data was
stored under `/tmp`. It should be promoted into projection surfaces by a later
promotion task before it is treated as the current default diagnostic ceiling.
