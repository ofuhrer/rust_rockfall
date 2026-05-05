# Hazard Throughput Bottleneck Report

Status: measured post-processing benchmark. This report does not change
simulation physics, hazard semantics, output schemas, validation behavior, or
benchmark defaults.

## Benchmark

Command:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none \
  --output-root validation/results/hazard_throughput_300_500
```

The output directory is ignored and was not committed. The run produced eight
hazard-stage rows: 300 and 500 releases, two contact models, and trajectory-only
versus trajectory-plus-Parquet-impact inputs.

## Timing Summary

| Case family | Hazard wall time | Bounds discovery | Trajectory accumulation | Impact accumulation | Normalization |
| --- | ---: | ---: | ---: | ---: | ---: |
| 300 releases, trajectories only | 6.02-7.15 s | 2.44-3.77 s | 2.93-3.25 s | ~0.00 s | 0.004-0.005 s |
| 300 releases, Parquet impacts | 5.72-7.98 s | 2.49-3.85 s | 2.78-3.16 s | 0.20-0.31 s | 0.004-0.009 s |
| 500 releases, trajectories only | 10.44-10.53 s | 4.39-5.56 s | 4.55-5.80 s | ~0.00 s | 0.004-0.006 s |
| 500 releases, Parquet impacts | 9.53-10.07 s | 3.72-4.06 s | 4.85-5.65 s | 0.36-0.38 s | 0.005-0.006 s |

Rows processed:

- 300-release trajectory runs read 45,300 trajectory samples and 300 deposition
  rows. Parquet-impact variants also read about 38,550 impact rows.
- 500-release trajectory runs read 75,500 trajectory samples and 500 deposition
  rows. Parquet-impact variants also read about 64,220 impact rows.

Observed diagnostic throughput:

- Trajectory accumulation: about 13k-16k trajectory rows/s.
- Projected Parquet impact accumulation: about 126k-189k impact rows/s.
- Total hazard input throughput is higher when impact rows are present because
  projected impact rows are much cheaper than trajectory rows.

## Bottleneck Diagnosis

The dominant post-processing cost is split between auto-grid bounds discovery
and trajectory accumulation. Bounds discovery alone accounts for roughly
37-53% of hazard-stage wall time in this run. Trajectory accumulation accounts
for roughly 40-56% of hazard-stage wall time and almost all of the measured
`accumulation_seconds` when impact inputs are absent.

Projected Parquet impact accumulation is not the current bottleneck. Even with
64k impact rows, impact accumulation stayed below 0.39 s and below about 4% of
hazard-stage wall time. Normalization is negligible. Core raster writing is
also small compared with bounds discovery and trajectory accumulation.

The repeated auto-grid scan matters. In auto-grid mode the builder scans
trajectory files once to determine bounds and again to accumulate layers. For
these small synthetic cases, the bounds scan is already comparable to the full
trajectory accumulation pass. That makes explicit-grid mode the right default
for benchmark and pilot scenarios where the terrain/grid extent is already
known from metadata.

## Recommendation

Immediate engineering target:

1. Make explicit-grid benchmark/pilot runs first-class in the benchmark
   recipes and any future Swiss pilot orchestration. This removes the repeated
   bounds scan from controlled comparisons without changing outputs for
   convenience auto-grid runs.
2. Then target trajectory accumulation, not impact accumulation. The next code
   optimization should reduce Python-level trajectory sample work or prepare a
   projected trajectory reader that feeds the existing batch interface.

Deferred:

- Do not optimize projected Parquet impact accumulation next; it is already
  substantially cheaper per row than trajectory accumulation.
- Do not implement trajectory Parquet as a writer-only feature. It should be
  paired with projected/batched hazard-reader support and measured against the
  trajectory accumulation bottleneck.
- Do not start tiled reducers before explicit-grid benchmark semantics are
  consistently used. Tiling remains important for large domains, but this
  benchmark shows a simpler repeated-scan issue first.

The safest next implementation slice is therefore an explicit-grid benchmark
mode/update for the synthetic benchmark runner, followed by a focused
trajectory-accumulation optimization pass.

## Explicit-Grid Follow-Up

The benchmark runner now supports `--hazard-grid explicit`, `auto`, and `both`.
The smoke, standard, and scale profiles use `explicit` by default. Explicit
mode derives the hazard grid from the generated synthetic DEM extent:

- `xmin = 2601000 m`, `ymin = 1201000 m`;
- `ncols = terrain_size`, `nrows = terrain_size`;
- `cell_size = synthetic DEM cell_size`.

Follow-up command:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none \
  --hazard-grid both \
  --output-root validation/results/hazard_explicit_grid_300_500
```

Measured result:

- Auto-grid hazard-stage wall time averaged about `10.0 s` across the eight
  hazard rows.
- Explicit-grid hazard-stage wall time averaged about `6.8 s`.
- Bounds discovery dropped to `0.0 s` in explicit mode by construction.
- Total hazard wall time improved in seven of eight paired rows. The remaining
  pair was essentially flat because explicit mode used the full synthetic DEM
  extent, while auto-grid used a smaller padded trajectory extent.

Interpretation:

- Explicit-grid mode removes the avoidable pre-scan and is the right default
  for controlled synthetic benchmarks and pilot-style runs.
- Explicit and auto grids can have different extents. The benchmark should use
  explicit mode for timing comparisons, while auto mode remains available for
  quick inspection and convenience.
- With bounds discovery removed, trajectory accumulation remains the dominant
  hazard-stage code path. The next optimization should target trajectory sample
  accumulation or a projected trajectory-reader interface, not impact
  accumulation.
