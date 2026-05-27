# Balfrin Diagnostic Series TB-613

Date: 2026-05-26

Status: measured diagnostic reducer-pressure series promoted through the
100-zone run.

Scope: single-node `postproc` diagnostic reducer-pressure evidence only. These
runs measure scheduler execution, reducer/runtime pressure, memory, output
files, output bytes, and manifest bytes for synthetic diagnostic pressure
roots. They do not measure hazard-throughput scaling, physical probability,
operational readiness, distributed execution, non-`postproc` execution, or
Swiss-wide execution.

## Measured Series

| Zones | Job | Reducer s | Max RSS MB | Time elapsed | Output files | Output bytes | Manifest bytes | Run-root bytes |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `16` | `4367731` | `3.07` | `34.066` | `0:01.24` | `52` | `23,661` | `15,898` | `110,129` |
| `24` | `4368588` | `4.03` | `33.711` | `0:01.55` | `76` | `32,904` | `20,170` | `144,378` |
| `24` repeat A | `4368592` | `4.03` | `34.242` | `0:00.34` | `76` | `32,922` | `20,218` | `145,200` |
| `24` repeat B | `4368593` | `4.03` | `39.879` | `0:00.34` | `76` | `32,922` | `20,218` | `145,203` |
| `32` | `4372124` | `5.39` | `34.168` | `0:00.75` | `100` | `42,221` | `24,514` | `181,433` |
| `40` | `4372257` | `6.35` | `33.902` | `0:01.40` | `124` | `51,493` | `28,818` | `212,134` |
| `100` | `4372447` | `13.55` | `34.16` | `0:01.26` | `304` | `121,172` | `61,119` | `448,376` |

The series is monotonic in output files, output bytes, and manifest bytes. Peak
memory stays around `34 MB` in the diagnostic pressure workload, with the
24-zone repeatability high point at `39.879 MB`.

## Per-Zone Shape

Using the 100-zone run as the current diagnostic ceiling:

| Measure | Per-zone value |
| --- | ---: |
| Reducer wall seconds | `0.1355` |
| Output files | `3.04` |
| Output bytes | `1,211.72` |
| Manifest bytes | `611.19` |

These per-zone values are valid only for the diagnostic reducer-pressure
workload and output-family mix used by `scripts/run_balfrin_diagnostic.py`.

## Remaining Blocker

The computational diagnostic question is no longer blocked on the 100-zone
single-node `postproc` reducer-pressure run. The next blocker is evidence type:

- hazard-throughput scaling beyond the bounded TB-603 support point;
- physical-probability and validation evidence for any scientific claim;
- distributed, non-`postproc`, regional, and Swiss-wide execution as explicit
  phase changes.

## Boundary

This series does not authorize larger live runs by itself. It supports a
clearer feasibility statement: 100-zone diagnostic reducer pressure is measured
and small on Balfrin `postproc`, while Swiss-scale feasibility still depends on
data readiness, hazard-throughput scaling, scientific validation, and the
execution model used for regional or national workloads.
