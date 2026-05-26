# Balfrin 24-Zone Diagnostic Run TB-579

Date: 2026-05-26

This note records the completed 24-zone diagnostic `postproc` run. It is
single-node reducer-pressure evidence only; it is not an operational,
physical-probability, Swiss-wide, distributed, or non-`postproc` result.

## Run

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote commit: `d6863e299a590f97d93cc16ba0018745b2bf6506`
- Run id: `diagnostic_24_zone_simplified_next`
- Run root: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next`
- Run record: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next/run_record.json`
- Slurm job id: `4368588`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`

Command:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run --release-zones 24 --reducer-chunks 2 --reducer-workers 2 --manifest-mode compact --run-id diagnostic_24_zone_simplified_next --partition postproc --time 00:30:00 --format json
```

## Metrics

| Metric | Value |
| --- | ---: |
| Release zones | 24 |
| Reducer chunks | 2 |
| Reducer workers | 2 |
| Reducer wall time | 4.03 s |
| `/usr/bin/time -v` elapsed | 0:01.55 |
| MaxRSS | 33.711 MB |
| Diagnostic output files | 76 |
| Diagnostic output bytes | 32,904 |
| Manifest size | 20,170 bytes |
| Pressure-root files | 81 |
| Pressure-root bytes | 57,543 |
| Run-root files | 89 |
| Run-root bytes | 144,378 |

## Boundary

This run extends measured single-node diagnostic post-processing evidence from
16 to 24 release zones. It does not promote operational hazard-map readiness,
annual frequency, physical probability, risk semantics, distributed execution,
Swiss-wide execution, or any non-`postproc` partition capability.
