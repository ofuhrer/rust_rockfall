# Parquet Impact-Event Benchmark Results

This document records the first benchmark of opt-in batched Parquet impact-event
output against the existing per-trajectory CSV impact-event directory workflow.
The benchmark is an engineering diagnostic only. It does not change simulation
physics, validation semantics, or hazard-layer interpretation.

## Setup

Command:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile scale \
  --output-root validation/results/parquet_impact_benchmark
```

Generated outputs were written under ignored
`validation/results/parquet_impact_benchmark/`.

Environment:

- Date: 2026-05-05
- Host OS: Darwin 25.3.0 arm64
- CPU: Apple M1, 8 hardware threads
- Memory: 16 GB
- Rust: `rustc 1.95.0`
- Python: `Python 3.11.11`

Benchmark matrix:

- release counts: 500 and 1000;
- contact models: `translational_v0` and `sphere_rotational_v1`;
- hazard plots: disabled (`--no-plots`);
- impact output modes: none, CSV directory, Parquet table, CSV+Parquet;
- weighted hazard: one representative Parquet case using
  `sampling_weight = 1.0` for all supplied trajectories.

After this benchmark, the runner default was changed to the smaller
`standard` profile for routine local use. The command above remains the
reproducible way to run this larger scale comparison.

The timings are single-run wall-clock measurements on a local workstation.
Absolute times are noisy; file counts, row counts, byte counts, and layer parity
are more stable than small timing differences.

## Validation Timing And Output Volume

| count | model | impact mode | total s | simulation s | output write s | files | total MB | CSV impact files/MB/rows | Parquet impact files/MB/rows |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 500 | translational | none | 11.86 | 6.99 | 4.77 | 504 | 35.5 | 0/0.0/0 | 0/0.0/0 |
| 500 | translational | csv | 20.56 | 7.06 | 13.40 | 1004 | 120.2 | 500/84.7/114222 | 0/0.0/0 |
| 500 | translational | parquet | 29.98 | 8.86 | 20.94 | 505 | 74.8 | 0/0.0/0 | 1/39.3/114222 |
| 500 | translational | csv+parquet | 40.81 | 9.36 | 31.35 | 1005 | 159.5 | 500/84.7/114222 | 1/39.3/114222 |
| 500 | rotational | none | 13.79 | 9.07 | 4.63 | 504 | 42.9 | 0/0.0/0 | 0/0.0/0 |
| 500 | rotational | csv | 20.59 | 7.91 | 12.58 | 1004 | 132.6 | 500/89.7/114216 | 0/0.0/0 |
| 500 | rotational | parquet | 29.37 | 7.82 | 21.40 | 505 | 86.8 | 0/0.0/0 | 1/43.8/114216 |
| 500 | rotational | csv+parquet | 42.84 | 9.14 | 33.61 | 1005 | 176.5 | 500/89.7/114216 | 1/43.8/114216 |
| 1000 | translational | none | 7.08 | 4.77 | 2.28 | 1004 | 71.1 | 0/0.0/0 | 0/0.0/0 |
| 1000 | translational | csv | 12.97 | 4.55 | 8.38 | 2004 | 240.7 | 1000/169.7/228465 | 0/0.0/0 |
| 1000 | translational | parquet | 17.19 | 5.04 | 12.08 | 1005 | 142.9 | 0/0.0/0 | 1/71.9/228465 |
| 1000 | translational | csv+parquet | 30.51 | 8.72 | 21.72 | 2005 | 312.6 | 1000/169.7/228465 | 1/71.9/228465 |
| 1000 | rotational | none | 54.44 | 42.65 | 11.59 | 1004 | 85.9 | 0/0.0/0 | 0/0.0/0 |
| 1000 | rotational | csv | 71.91 | 37.07 | 34.53 | 2004 | 265.6 | 1000/179.7/228472 | 0/0.0/0 |
| 1000 | rotational | parquet | 63.08 | 19.04 | 43.88 | 1005 | 166.2 | 0/0.0/0 | 1/80.2/228472 |
| 1000 | rotational | csv+parquet | 122.80 | 44.76 | 77.87 | 2005 | 345.9 | 1000/179.7/228472 | 1/80.2/228472 |

Observed reductions for Parquet-only versus CSV-only impact-event output:

| count | model | file-count reduction | total output byte ratio | impact byte ratio | output-write time ratio |
|---|---|---:|---:|---:|---:|
| 500 | translational | 499 fewer files | 0.62 | 0.46 | 1.56 |
| 500 | rotational | 499 fewer files | 0.65 | 0.49 | 1.70 |
| 1000 | translational | 999 fewer files | 0.59 | 0.42 | 1.44 |
| 1000 | rotational | 999 fewer files | 0.63 | 0.45 | 1.27 |

Interpretation:

- Parquet materially reduces impact-event file-count pressure: 500 or 1000
  small CSV files become one Parquet table.
- Parquet materially reduces impact-event byte volume: impact-event bytes are
  roughly 42-49% of the CSV impact-event bytes in this benchmark.
- The current Parquet writer is not yet faster. Output-write time was 1.27-1.70x
  the CSV-only impact output time in these single-run measurements.
- CSV+Parquet is useful only for debugging/parity; it predictably has the worst
  output write cost.

## Hazard Accumulation

| count | model | impact mode | stage | total s | accumulation s | impact events | events/s total |
|---|---|---|---|---:|---:|---:|---:|
| 500 | translational | none | hazard_no_plots | 15.54 | 9.54 | 0 | 0 |
| 500 | translational | csv | hazard_no_plots | 44.55 | 21.66 | 114222 | 2564 |
| 500 | translational | parquet | hazard_no_plots | 42.46 | 19.65 | 114222 | 2690 |
| 500 | translational | parquet | hazard_weighted_no_plots | 40.53 | 21.15 | 114222 | 2818 |
| 500 | translational | csv+parquet | hazard_no_plots | 51.14 | 25.00 | 114222 | 2233 |
| 500 | rotational | none | hazard_no_plots | 13.77 | 8.10 | 0 | 0 |
| 500 | rotational | csv | hazard_no_plots | 35.51 | 18.78 | 114216 | 3216 |
| 500 | rotational | parquet | hazard_no_plots | 37.87 | 20.19 | 114216 | 3016 |
| 500 | rotational | csv+parquet | hazard_no_plots | 39.91 | 22.43 | 114216 | 2862 |
| 1000 | translational | none | hazard_no_plots | 7.46 | 4.20 | 0 | 0 |
| 1000 | translational | csv | hazard_no_plots | 22.26 | 10.77 | 228465 | 10263 |
| 1000 | translational | parquet | hazard_no_plots | 31.01 | 18.40 | 228465 | 7368 |
| 1000 | translational | csv+parquet | hazard_no_plots | 67.24 | 50.20 | 228465 | 3398 |
| 1000 | rotational | none | hazard_no_plots | 56.34 | 26.89 | 0 | 0 |
| 1000 | rotational | csv | hazard_no_plots | 94.48 | 54.65 | 228472 | 2418 |
| 1000 | rotational | parquet | hazard_no_plots | 104.29 | 62.90 | 228472 | 2191 |
| 1000 | rotational | csv+parquet | hazard_no_plots | 88.72 | 42.28 | 228472 | 2575 |

Interpretation:

- Hazard accumulation remains a real bottleneck when full trajectory CSVs and
  impact events are present.
- Current Parquet impact reading does not consistently improve hazard
  accumulation. The reader uses PyArrow but converts record batches through
  Python row dictionaries, so it does not yet benefit from columnar/vectorized
  processing.
- The CSV+Parquet hazard stage defaults to the Parquet impact table to avoid
  double-counting; it exists to measure output mode overhead, not to improve
  hazard accumulation.
- Plotting was disabled, so these timings isolate core no-plot hazard
  generation.

## Numerical Parity

CSV impact-event layers, Parquet impact-event layers, and CSV+Parquet case-file
layers were compared for:

- reach probability;
- deposition density;
- maximum kinetic energy;
- maximum jump height;
- significant impact density;
- kinetic-energy exceedance layers;
- jump-height exceedance layers;
- velocity exceedance layers.

Maximum absolute CSV-vs-Parquet layer difference: `0.0`.

The representative weighted Parquet case used a filtered benchmark metadata
sidecar with `sampling_weight = 1.0` for each supplied trajectory. Weighted reach
and weighted exceedance layers matched their unweighted counterparts exactly in
that representative run. This verifies that weighted semantics were not changed
by the Parquet impact-event path.

## Bottleneck Diagnosis

At 500/1000 release scale:

- Simulation is still important, especially for `sphere_rotational_v1`.
- Full trajectory CSV output remains a large file-count source because this
  benchmark still writes one trajectory CSV per release.
- Impact-event CSV output creates the most obvious small-file pressure.
- Parquet solves the impact-event small-file problem and reduces impact-event
  byte volume, but it does not yet solve output-write time or hazard-read time.
- Core raster writing is not the bottleneck. Plotting was disabled and therefore
  did not contribute.

## Answers

### Is Parquet impact-event output clearly superior at 500/1000 scale?

It is clearly superior for impact-event file count and byte volume. It is not
yet clearly superior for output-write time or hazard accumulation time.

### Is output writing or hazard accumulation the dominant bottleneck?

Both matter. Validation output writing dominates the incremental cost of impact
debug output, while hazard accumulation dominates no-plot hazard post-processing
when full trajectories and impact events are read. Core raster writing remains
small.

### Does Parquet materially reduce file-count pressure?

Yes. It replaces 500 or 1000 impact-event CSV files with one Parquet file. Total
file count is still high when full trajectory CSV output is enabled because
trajectory samples remain one CSV per trajectory.

### Is trajectory Parquet now justified?

Trajectory Parquet is justified as a design direction for file-count pressure,
but not as the immediate implementation step. The impact-event Parquet path
should first be made performance-positive; otherwise trajectory Parquet risks
moving the same row-wise Python conversion bottleneck to a larger table.

### Should hazard accumulation be optimized before trajectory Parquet?

Yes. The next engineering step should optimize the columnar hazard reader and
accumulator before adding trajectory Parquet. The current Parquet reader should
use projected columns and Arrow/NumPy-style batch processing instead of
`to_pylist()` row dictionaries.

### Should CSV remain default for small validation/debug workflows?

Yes. CSV remains easier to inspect, has no PyArrow dependency for hazard
post-processing, and is still competitive or faster at this scale. Parquet
should remain opt-in for larger impact-event runs and file-count reduction.

## Recommendation

Immediate next engineering step:

- Optimize the Parquet impact-event reader/writer path before implementing
  `trajectory_samples_table_v1`. Specifically, benchmark projected-column
  PyArrow batch reads, avoid `to_pylist()` in hazard accumulation, and evaluate
  compression settings separately from schema correctness.

Deferred step:

- Defer trajectory Parquet until impact-event Parquet is performance-positive
  or until a separate benchmark shows trajectory CSV file count is the dominant
  operational constraint.

`trajectory_samples_table_v1` should not be implemented immediately. It remains
the right medium-term direction, but the safer next step is to make the existing
impact-event Parquet path efficient and repeat the benchmark with multiple runs
or larger ensembles once the reader is vectorized.
