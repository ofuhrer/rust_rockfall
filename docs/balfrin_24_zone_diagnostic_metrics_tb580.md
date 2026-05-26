# Balfrin 24-Zone Diagnostic Metrics TB-580

Date: 2026-05-26

This note records the promotion boundary for the completed 24-zone diagnostic
`postproc` run. It is measured reducer-pressure evidence only.

## Promoted Run Record

- Run record: `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next/run_record.json`
- Slurm job id: `4368588`
- Terminal state: `COMPLETED`
- Release zones: 24
- Reducer chunks/workers: 2 / 2
- Reducer wall time: 4.03 s
- Elapsed: 0:01.55
- MaxRSS: 33.711 MB
- Diagnostic output: 76 files, 32,904 bytes
- Manifest size: 20,170 bytes
- Run-root footprint: 89 files, 144,378 bytes

## Evidence Surfaces

- `scripts/summarize_balfrin_evidence_bundle.py` now treats the 24-zone run
  record as the latest diagnostic multi-zone evidence when it is present.
- `scripts/summarize_balfrin_scale_readiness_matrix.py` reports
  `diagnostic_24_zone_reducer_pressure` as a measured tier and keeps 16-zone,
  current regional split, and historical regional split rows in the diagnostic
  performance comparison surface.
- `scripts/summarize_multi_zone_reducer_pressure.py` uses the latest diagnostic
  run record as the measured single-node diagnostic batch ceiling when present.

## Boundary

The promoted evidence supports diagnostic single-node `postproc` planning only.
It does not establish operational hazard-map readiness, physical probability,
annual frequency, risk semantics, distributed execution, Swiss-wide execution,
or non-`postproc` partition capability.
