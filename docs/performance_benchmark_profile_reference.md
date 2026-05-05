# Benchmark Profile Reference

Status: canonical post-refactor benchmark reference for the
`scripts/run_performance_benchmark.py` profile system. This is an engineering
measurement record only. It does not change physics, validation semantics, or
hazard-layer interpretation.

## Setup

Date: 2026-05-05

Environment:

- Host OS: Darwin 25.3.0 arm64
- CPU: Apple M1, 8 hardware threads
- Rust: `rustc 1.95.0`
- Python: `Python 3.11.11`
- Benchmark binary: local debug `target/debug/rockfall`
- Hazard plots: disabled for all benchmark profiles
- Generated outputs: ignored under `validation/results/benchmark_reference_*`

Commands:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile smoke \
  --output-root validation/results/benchmark_reference_smoke

python3 scripts/run_performance_benchmark.py \
  --output-root validation/results/benchmark_reference_standard

python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 20 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 \
  --output-root validation/results/benchmark_reference_custom

python3 scripts/run_performance_benchmark.py \
  --profile scale \
  --output-root validation/results/benchmark_reference_scale
```

Wall-clock timings are single-run measurements on a local workstation and are
expected to vary with filesystem cache, thermals, and background activity.
Manifest timings are summed across validation and hazard stages from
`summary.csv`.

## Profile Results

| profile | matrix | shell wall time | manifest stage sum | rows | output size |
|---|---|---:|---:|---:|---:|
| smoke | 5 releases, baseline, trajectories + Parquet impact modes | 2.09 s | 0.62 s | 4 | 524 KB |
| standard | 10 releases, both contact models, trajectories + Parquet impact modes | 4.54 s | 2.60 s | 9 | 4.4 MB |
| custom sample | 20 releases, baseline only, trajectories + Parquet impact modes | 4.04 s | 2.47 s | 5 | 3.9 MB |
| scale | 500/1000 releases, both contact models, summary/trajectory/CSV/Parquet/CSV+Parquet modes | 27m49s | 1657.90 s | 37 | 2.4 GB |

Interpretation:

- `smoke` is suitable for script sanity checks and unit-test style coverage.
- `standard` is genuinely lightweight on this machine and safely below the
  intended routine local threshold. It no longer includes CSV+Parquet or CSV
  impact-event output by default.
- `custom` works as the intended targeted path for small local comparisons.
- `scale` remains meaningfully larger and stress-oriented. It should be run only
  when measuring data-format and output-volume behavior.

## Standard Profile Quality

The standard profile validates the most important routine paths without creating
heavy output pressure:

- both `translational_v0` and `sphere_rotational_v1`;
- full ensemble trajectory output;
- opt-in Parquet impact-event output;
- no-plot hazard layers;
- one representative sampling-weighted hazard stage.

It intentionally omits CSV impact-event output and CSV+Parquet dual output.
Those modes are covered by the scale profile and targeted custom runs.

## Scale Profile Results

The scale profile reproduced the previous large benchmark capability:

- release counts: `500`, `1000`;
- contact models: `translational_v0`, `sphere_rotational_v1`;
- impact modes: none, CSV, Parquet, CSV+Parquet;
- one representative weighted hazard stage;
- no PNG/HTML plotting.

### Validation Timing And Output Volume

| count | model | impact mode | total s | simulation s | output write s | files | total MB | CSV impact files/MB/rows | Parquet impact files/MB/rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | translational | none | 5.64 | 3.94 | 1.62 | 504 | 35.5 | 0/0.0/0 | 0/0.0/0 |
| 500 | translational | csv | 8.94 | 3.63 | 5.27 | 1004 | 120.2 | 500/84.7/114861 | 0/0.0/0 |
| 500 | translational | parquet | 17.56 | 4.93 | 12.57 | 505 | 74.8 | 0/0.0/0 | 1/39.3/114861 |
| 500 | translational | csv+parquet | 47.97 | 10.50 | 37.33 | 1005 | 159.5 | 500/84.7/114861 | 1/39.3/114861 |
| 500 | rotational | none | 15.31 | 9.94 | 5.28 | 504 | 42.9 | 0/0.0/0 | 0/0.0/0 |
| 500 | rotational | csv | 23.53 | 10.26 | 13.15 | 1004 | 132.6 | 500/89.7/114855 | 0/0.0/0 |
| 500 | rotational | parquet | 34.36 | 8.97 | 25.24 | 505 | 86.8 | 0/0.0/0 | 1/43.8/114855 |
| 500 | rotational | csv+parquet | 57.27 | 10.78 | 46.26 | 1005 | 176.5 | 500/89.7/114855 | 1/43.8/114855 |
| 1000 | translational | none | 34.25 | 23.59 | 10.41 | 1004 | 71.1 | 0/0.0/0 | 0/0.0/0 |
| 1000 | translational | csv | 51.90 | 21.17 | 30.54 | 2004 | 240.7 | 1000/169.7/229104 | 0/0.0/0 |
| 1000 | translational | parquet | 65.01 | 20.46 | 44.36 | 1005 | 142.9 | 0/0.0/0 | 1/71.9/229104 |
| 1000 | translational | csv+parquet | 79.44 | 18.17 | 61.10 | 2005 | 312.6 | 1000/169.7/229104 | 1/71.9/229104 |
| 1000 | rotational | none | 34.62 | 22.71 | 11.69 | 1004 | 85.9 | 0/0.0/0 | 0/0.0/0 |
| 1000 | rotational | csv | 64.18 | 24.02 | 39.95 | 2004 | 265.6 | 1000/179.7/229111 | 0/0.0/0 |
| 1000 | rotational | parquet | 76.24 | 25.54 | 50.37 | 1005 | 166.2 | 0/0.0/0 | 1/80.2/229111 |
| 1000 | rotational | csv+parquet | 87.88 | 21.50 | 66.15 | 2005 | 345.9 | 1000/179.7/229111 | 1/80.2/229111 |

### Hazard Timing

| count | model | impact mode | stage | total s | accumulation s | output s | impact events |
|---|---|---|---|---:|---:|---:|---:|
| 500 | translational | none | hazard_no_plots | 6.19 | 2.97 | 0.07 | 0 |
| 500 | translational | csv | hazard_no_plots | 19.12 | 10.52 | 0.09 | 114222 |
| 500 | translational | parquet | hazard_no_plots | 29.54 | 16.51 | 0.34 | 114222 |
| 500 | translational | parquet | hazard_weighted_no_plots | 42.84 | 24.71 | 0.21 | 114222 |
| 500 | translational | csv+parquet | hazard_no_plots | 49.28 | 25.21 | 0.16 | 114222 |
| 500 | rotational | none | hazard_no_plots | 16.16 | 9.46 | 0.14 | 0 |
| 500 | rotational | csv | hazard_no_plots | 35.07 | 19.28 | 0.17 | 114216 |
| 500 | rotational | parquet | hazard_no_plots | 53.22 | 27.14 | 0.16 | 114216 |
| 500 | rotational | csv+parquet | hazard_no_plots | 49.82 | 28.01 | 0.17 | 114216 |
| 1000 | translational | none | hazard_no_plots | 36.62 | 20.12 | 0.19 | 0 |
| 1000 | translational | csv | hazard_no_plots | 82.79 | 43.14 | 0.15 | 228465 |
| 1000 | translational | parquet | hazard_no_plots | 93.93 | 47.01 | 0.13 | 228465 |
| 1000 | translational | csv+parquet | hazard_no_plots | 95.86 | 51.23 | 0.18 | 228465 |
| 1000 | rotational | none | hazard_no_plots | 29.36 | 15.87 | 0.17 | 0 |
| 1000 | rotational | csv | hazard_no_plots | 88.58 | 47.02 | 0.19 | 228472 |
| 1000 | rotational | parquet | hazard_no_plots | 86.61 | 47.68 | 0.23 | 228472 |
| 1000 | rotational | csv+parquet | hazard_no_plots | 84.91 | 41.19 | 0.22 | 228472 |

## Conclusions

- Parquet materially reduces impact-event file count: 500 or 1000 per-trajectory
  impact CSV files become one Parquet table.
- Parquet materially reduces impact-event storage volume: the Parquet impact
  table is roughly 42-49% of the corresponding CSV impact-event bytes.
- Parquet is not yet faster to write in this implementation. Output-write time
  was higher for Parquet-only than CSV-only in this single scale run.
- Hazard accumulation is still dominated by row-wise Python processing of full
  trajectory and impact-event inputs. Current Parquet impact reading does not
  yet provide a consistent accumulation speedup.
- Weighted hazard layers work as an opt-in representative path, but add a
  measurable hazard-stage cost because metadata filtering and extra weighted
  layers are generated.
- CSV+Parquet dual-output mode is practical for parity/debugging only. It has
  the highest write cost and should not be a default benchmark or production
  mode.
- CSV remains acceptable for small validation/debug workflows because it is
  inspectable and remains competitive at small scale.

## Future Optimization Opportunities

1. Optimize the Parquet impact-event reader before adding trajectory Parquet:
   use projected columns and batch/array processing instead of row dictionaries.
2. Add repeated-run support for benchmark stability summaries when making
   performance claims.
3. Separate process startup, validation, and hazard-stage wall time more
   explicitly in the summary report.
4. Keep standard no-plot benchmarks as the routine local check; use scale only
   for explicit storage/I/O decisions.
