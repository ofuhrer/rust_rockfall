# Balfrin 24-Zone Repeatability Metrics TB-582

Date: 2026-05-26

This note records the repeatability bounds computed from the two TB-581
24-zone diagnostic `postproc` runs.

## Inputs

- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_a_tb581/run_record.json`
- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_b_tb581/run_record.json`

## Bounds

| Metric | Min | Median | Max | Spread |
| --- | ---: | ---: | ---: | ---: |
| Reducer wall time, s | 4.03 | 4.03 | 4.03 | 0.00 |
| MaxRSS, MB | 34.242 | 37.0605 | 39.879 | 5.637 |
| Output files | 76 | 76 | 76 | 0 |
| Output bytes | 32,922 | 32,922 | 32,922 | 0 |
| Manifest bytes | 20,218 | 20,218 | 20,218 | 0 |

## Promoted Surface

`scripts/summarize_balfrin_scale_readiness_matrix.py` now exposes
`diagnostic_repeatability_summary` with the same-size rows and bounded summary
statistics.

## Boundary

This is measurement-stability evidence for single-node 24-zone diagnostic
`postproc` reducer pressure only. It does not establish operational hazard-map
readiness, physical probability, annual frequency, risk semantics, Swiss-wide
execution, distributed execution, or non-`postproc` partition capability.
