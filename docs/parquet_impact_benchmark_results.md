# Parquet Impact-Event Benchmark Results

This document records the canonical post-refactor benchmark of opt-in batched
Parquet impact-event output against the existing per-trajectory CSV
impact-event directory workflow. The benchmark is an engineering diagnostic
only. It does not change simulation physics, validation semantics, or
hazard-layer interpretation.

For the full smoke/standard/custom/scale profile reference, see
`performance_benchmark_profile_reference.md`.

## Setup

Command:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile scale \
  --output-root validation/results/benchmark_reference_scale
```

Generated outputs were written under ignored
`validation/results/benchmark_reference_scale/`.

Environment:

- Date: 2026-05-05
- Host OS: Darwin 25.3.0 arm64
- CPU: Apple M1, 8 hardware threads
- Rust: `rustc 1.95.0`
- Python: `Python 3.11.11`

Benchmark matrix:

- release counts: 500 and 1000;
- contact models: `translational_v0` and `sphere_rotational_v1`;
- hazard plots: disabled (`--no-plots`);
- impact output modes: none, CSV directory, Parquet table, CSV+Parquet;
- weighted hazard: one representative Parquet case using
  `sampling_weight = 1.0` for all supplied trajectories.

The full command completed in `27m49s` and generated `2.4 GB` of ignored
artifacts on the reference machine.

The timings are single-run wall-clock measurements. Absolute times are noisy;
file counts, row counts, byte counts, and layer parity are more stable than
small timing differences.

## Validation Timing And Output Volume

| count | model | impact mode | total s | simulation s | output write s | files | total MB | CSV impact files/MB/rows | Parquet impact files/MB/rows |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 500 | translational | csv | 8.94 | 3.63 | 5.27 | 1004 | 120.2 | 500/84.7/114861 | 0/0.0/0 |
| 500 | translational | parquet | 17.56 | 4.93 | 12.57 | 505 | 74.8 | 0/0.0/0 | 1/39.3/114861 |
| 500 | translational | csv+parquet | 47.97 | 10.50 | 37.33 | 1005 | 159.5 | 500/84.7/114861 | 1/39.3/114861 |
| 500 | rotational | csv | 23.53 | 10.26 | 13.15 | 1004 | 132.6 | 500/89.7/114855 | 0/0.0/0 |
| 500 | rotational | parquet | 34.36 | 8.97 | 25.24 | 505 | 86.8 | 0/0.0/0 | 1/43.8/114855 |
| 500 | rotational | csv+parquet | 57.27 | 10.78 | 46.26 | 1005 | 176.5 | 500/89.7/114855 | 1/43.8/114855 |
| 1000 | translational | csv | 51.90 | 21.17 | 30.54 | 2004 | 240.7 | 1000/169.7/229104 | 0/0.0/0 |
| 1000 | translational | parquet | 65.01 | 20.46 | 44.36 | 1005 | 142.9 | 0/0.0/0 | 1/71.9/229104 |
| 1000 | translational | csv+parquet | 79.44 | 18.17 | 61.10 | 2005 | 312.6 | 1000/169.7/229104 | 1/71.9/229104 |
| 1000 | rotational | csv | 64.18 | 24.02 | 39.95 | 2004 | 265.6 | 1000/179.7/229111 | 0/0.0/0 |
| 1000 | rotational | parquet | 76.24 | 25.54 | 50.37 | 1005 | 166.2 | 0/0.0/0 | 1/80.2/229111 |
| 1000 | rotational | csv+parquet | 87.88 | 21.50 | 66.15 | 2005 | 345.9 | 1000/179.7/229111 | 1/80.2/229111 |

Observed reductions for Parquet-only versus CSV-only impact-event output:

| count | model | file-count reduction | total output byte ratio | impact byte ratio | output-write time ratio |
|---|---|---:|---:|---:|---:|
| 500 | translational | 499 fewer files | 0.62 | 0.46 | 2.39 |
| 500 | rotational | 499 fewer files | 0.65 | 0.49 | 1.92 |
| 1000 | translational | 999 fewer files | 0.59 | 0.42 | 1.45 |
| 1000 | rotational | 999 fewer files | 0.63 | 0.45 | 1.26 |

Interpretation:

- Parquet materially reduces impact-event file-count pressure: 500 or 1000
  small CSV files become one Parquet table.
- Parquet materially reduces impact-event byte volume: impact-event bytes are
  roughly 42-49% of the CSV impact-event bytes in this benchmark.
- The current Parquet writer is not faster in this implementation. Output-write
  time was 1.26-2.39x the CSV-only impact output time in this single run.
- CSV+Parquet is useful only for debugging/parity; it predictably has the worst
  output write cost.

## Hazard Accumulation

| count | model | impact mode | stage | total s | accumulation s | impact events |
|---|---|---|---|---:|---:|---:|
| 500 | translational | csv | hazard_no_plots | 19.12 | 10.52 | 114222 |
| 500 | translational | parquet | hazard_no_plots | 29.54 | 16.51 | 114222 |
| 500 | translational | parquet | hazard_weighted_no_plots | 42.84 | 24.71 | 114222 |
| 500 | translational | csv+parquet | hazard_no_plots | 49.28 | 25.21 | 114222 |
| 500 | rotational | csv | hazard_no_plots | 35.07 | 19.28 | 114216 |
| 500 | rotational | parquet | hazard_no_plots | 53.22 | 27.14 | 114216 |
| 500 | rotational | csv+parquet | hazard_no_plots | 49.82 | 28.01 | 114216 |
| 1000 | translational | csv | hazard_no_plots | 82.79 | 43.14 | 228465 |
| 1000 | translational | parquet | hazard_no_plots | 93.93 | 47.01 | 228465 |
| 1000 | translational | csv+parquet | hazard_no_plots | 95.86 | 51.23 | 228465 |
| 1000 | rotational | csv | hazard_no_plots | 88.58 | 47.02 | 228472 |
| 1000 | rotational | parquet | hazard_no_plots | 86.61 | 47.68 | 228472 |
| 1000 | rotational | csv+parquet | hazard_no_plots | 84.91 | 41.19 | 228472 |

Interpretation:

- Hazard accumulation remains a major bottleneck when full trajectory CSVs and
  impact events are present.
- Current Parquet impact reading does not consistently improve hazard
  accumulation. The reader can consume Parquet, but the current path still
  performs row-wise Python processing during accumulation.
- Plotting was disabled, so these timings isolate core no-plot hazard
  generation.

## Numerical Parity

CSV impact-event layers, Parquet impact-event layers, and CSV+Parquet case-file
layers are covered by the hazard-layer parity tests for:

- reach probability;
- deposition density;
- maximum kinetic energy;
- maximum jump height;
- significant impact density;
- kinetic-energy exceedance layers;
- jump-height exceedance layers;
- velocity exceedance layers.

Maximum absolute CSV-vs-Parquet layer difference in the fixture parity test:
`0.0`.

The representative weighted Parquet scale case used a filtered benchmark
metadata sidecar with `sampling_weight = 1.0` for each supplied trajectory. This
exercises the opt-in weighted path but does not claim calibrated probability.

## Bottleneck Diagnosis

At 500/1000 release scale:

- Simulation is still important, especially for `sphere_rotational_v1`.
- Full trajectory CSV output remains a large file-count source because this
  benchmark still writes one trajectory CSV per release.
- Impact-event CSV output creates obvious small-file pressure.
- Parquet solves the impact-event small-file problem and reduces impact-event
  byte volume, but it does not yet solve output-write time or hazard-read time.
- Core raster writing is not the bottleneck. Plotting was disabled and therefore
  did not contribute.

## Post-Refactor Optimization Update

After the canonical scale run, the Parquet impact-event hazard reader was
optimized conservatively:

- bounds discovery now reads only `x_m` and `y_m` from Parquet impact tables;
- significant-impact accumulation now reads only `x_m`, `y_m`, and
  `significant_impact` when that flag is present;
- the impact-density path no longer converts full Parquet rows into Python
  dictionaries;
- the writer schema and CSV/Parquet hazard semantics remain unchanged.

A targeted 100/200-release custom run was used to check the change:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 100 200 \
  --output-modes csv parquet \
  --contact-models translational_v0
```

Matched post-optimization hazard accumulation timings:

| count | impact mode | hazard accumulation s |
|---:|---|---:|
| 100 | csv | 2.49 |
| 100 | parquet | 1.77 |
| 200 | csv | 4.48 |
| 200 | parquet | 1.74 |

The machine was noisy during this run, so the numbers should not be treated as
absolute speed claims. The useful engineering signal is that the projected
Parquet reader removes the earlier full-row conversion penalty and makes the
Parquet hazard path competitive or faster in this intermediate benchmark.

A focused 300/500-release validation then checked both contact models:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes csv parquet \
  --contact-models translational_v0 sphere_rotational_v1
```

| count | model | CSV accum s | Parquet accum s | Parquet/CSV accum | CSV total s | Parquet total s | row parity |
|---:|---|---:|---:|---:|---:|---:|---|
| 300 | translational | 5.35 | 2.35 | 0.44 | 9.42 | 5.14 | yes |
| 300 | rotational | 6.68 | 2.64 | 0.39 | 12.71 | 6.25 | yes |
| 500 | translational | 12.14 | 4.66 | 0.38 | 23.43 | 9.19 | yes |
| 500 | rotational | 12.91 | 6.34 | 0.49 | 24.87 | 12.39 | yes |

This intermediate run produced no missing-column failures and preserved
CSV/Parquet impact row parity. It strengthens the conclusion that projected
Parquet reads are performance-positive for significant-impact hazard
accumulation. Parquet validation output writing remains slower than CSV in the
same run, with Parquet write-time ratios from 1.32x to 2.80x of CSV write time.

The writer remains mixed. A Snappy compression trial only reduced bytes
slightly and did not make writing faster, so the Parquet writer remains
uncompressed for now. The remaining write-time bottleneck is likely ArrowWriter
encoding many impact-event diagnostic columns, not just raw byte volume.

## Writer-Side Profiling Update

The writer path was profiled with hazard generation disabled so the measured
`output_write_seconds` isolates validation output writing:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes csv parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --skip-hazard \
  --output-root validation/results/parquet_writer_baseline_300_500
```

Baseline output-write timings were:

| count | model | impact mode | output write s | files | bytes | impact rows |
|---:|---|---|---:|---:|---:|---:|
| 300 | translational | csv | 5.48 | 604 | 41,269,873 | 38,886 |
| 300 | translational | parquet | 9.16 | 305 | 25,803,041 | 38,886 |
| 300 | rotational | csv | 5.42 | 604 | 45,831,793 | 38,892 |
| 300 | rotational | parquet | 11.16 | 305 | 30,005,783 | 38,892 |
| 500 | translational | csv | 7.95 | 1,004 | 68,765,502 | 64,561 |
| 500 | translational | parquet | 15.46 | 505 | 43,048,104 | 64,561 |
| 500 | rotational | csv | 8.95 | 1,004 | 76,350,716 | 64,555 |
| 500 | rotational | parquet | 17.95 | 505 | 50,050,942 | 64,555 |

Two conservative writer-side changes were tested:

- pre-sizing all impact-event column buffers from the known row count;
- disabling Parquet page statistics metadata.

Pre-sizing was retained because it removes repeated vector growth without
changing the schema, file format, compression, or hazard semantics. The timing
effect was noisy: it improved some Parquet cases but did not consistently make
Parquet writing faster than CSV. Disabling page statistics reduced Parquet file
size slightly but did not improve write time consistently, so it was rejected.

The current conclusion is unchanged: Parquet impact events are already useful
for reducing file count, reducing byte volume, and speeding projected hazard
reads, but the Rust writer remains slower than the per-trajectory CSV writer for
these small-to-intermediate synthetic runs. The bottleneck appears to be the
wide Arrow/Parquet column encoding and metadata path rather than filesystem
byte volume alone.

## Recommendation

Immediate next engineering step:

- Keep trajectory Parquet deferred and make the next columnar step either
  repeated scale benchmarking of the projected Parquet reader or focused
  writer-side profiling of ArrowWriter column encoding. Do not add a larger
  trajectory table until the existing impact-event table is consistently
  performance-positive at scale.

Deferred step:

- Defer trajectory Parquet until impact-event Parquet is performance-positive or
  until a separate benchmark shows trajectory CSV file count is the dominant
  operational constraint.

CSV should remain the default for small validation/debug workflows. Parquet
should remain opt-in for larger impact-event runs where file-count and byte
volume matter more than immediate write speed.
