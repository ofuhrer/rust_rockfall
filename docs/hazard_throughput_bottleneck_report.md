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

## Phase Timing Contract

`scripts/build_hazard_layers.py` now emits a stable sidecar timing file next to
each hazard manifest: `<prefix>_phase_timing.json`. The file is fixture-friendly
JSON with `schema_version: hazard_builder_phase_timing_v1` and records:

- `grid`: output grid dimensions and source.
- `output_profile`: the writer and profile settings that affect comparable runs.
- `input`: file counts, bytes, and hazard-input row counts.
- `output`: total output counts/bytes plus raster, report, and manifest groups.
- `phase_seconds`: input reading, accumulation, reducer merge, raster write,
  report write, manifest generation, COG export, and total wall time.
- `memory.peak_rss_kb`: optional peak RSS when the platform exposes it.

`input_read_seconds` includes direct file reads and bounds discovery. The timing
file is a sidecar artifact and does not change hazard-layer values or manifest
semantics.

## Multi-Zone Scratch Profile

TB-209 added a deterministic multi-zone scratch-root profiler at
`scripts/summarize_multi_zone_hazard_throughput_profile.py`. The helper
materializes a 12-zone synthetic hazard corpus, runs the hazard-layer builder
with explicit-grid and reduced-output controls, and captures the builder's own
timing fields together with read and reducer-merge instrumentation.

Measured on the scratch fixture:

- read time: `0.004` s
- accumulation time: `0.071` s
- reducer merge time: `0.005` s
- manifest time: `0.000` s
- raster write time: `0.027` s
- report-rendering time: `0.000` s
- output file count: `26`
- output bytes: `968042`

Observed output pressure:

- layer family leader: `max_kinetic_energy` at `2` files / `129276` bytes
- file family leader: `geotiff` at `9` files / `665910` bytes
- manifest family leader: `reducer_execution_plan` at `1` file / `14133` bytes
- COG/GIS family: not applicable in the default fixture

The first concrete bottleneck is accumulation time, not output fan-out. The
bounded recommendation is to focus the next optimization slice on accumulator
batching or merge handling rather than touching hazard semantics or output
formats.

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

## Trajectory Accumulation Profiling Follow-Up

A conservative local-loop optimization was tested after explicit-grid support:
the trajectory accumulator cached grid constants and inlined per-sample cell,
maxima, exceedance, and jump-height work while preserving the existing batch
interface. The benchmark command was:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none \
  --hazard-grid explicit \
  --output-root validation/results/trajectory_accumulation_optimization_300_500
```

The result was mixed and the change was not retained:

- Average explicit-grid trajectory accumulation changed only from about
  `5.52 s` to `5.40 s` across the eight rows.
- Average explicit-grid hazard-stage time was effectively unchanged
  (`6.00 s` before, `6.02 s` after).
- Several paired Parquet-impact rows became slower, while one large apparent
  improvement was dominated by a noisy previous outlier.

Interpretation:

- Simple helper inlining and attribute caching are not a stable optimization
  target for the current Python accumulator.
- The remaining bottleneck is still Python-level per-sample raster updates, but
  it likely needs a more structural change: vectorized/batched trajectory cell
  indexing, per-trajectory occupied-cell reduction, or a projected trajectory
  input path that feeds the reducer in larger arrays.
- Trajectory Parquet should still wait until the hazard builder has a reader
  path that can use projected/batched trajectory columns rather than converting
  back to row-wise Python objects.

## TB-219 Microprofile Update

The current microprofile helper now separates the remaining hazard-stage
phases on a fixture-backed scratch root:

- smoke profile: 2 release zones, explicit-only routine check, 18 output files
  / 824030 bytes, bounded by `raster_write_seconds`.
- representative profile: 12 release zones, auto-grid bounds pass plus
  explicit-grid accumulation pass, 25 output files / 957998 bytes.

Representative measured phases:

- trajectory reading: `0.002586` s
- bounds discovery: `0.001153` s
- accumulation: `0.07079` s
- reducer merge: `0.004829` s
- raster write: `0.026177` s
- manifest write: `0.000317` s
- report rendering: `0.0` s

Representative output pressure:

- largest phase: `accumulation_seconds`
- largest layer family: `max_kinetic_energy` at `2` files / `129276` bytes
- largest file family: `geotiff` at `9` files / `665910` bytes

Bounded next target:

- batch or vectorize trajectory-cell updates inside the existing accumulator.
- expected impact: reduce the dominant explicit-grid trajectory accumulation
  phase by lowering Python row-wise update overhead.
- risk: batching must preserve per-cell maxima, reach counts, exceedance
  semantics, and reducer merge determinism.
- required tests: smoke-profile semantic guardrail, representative phase
  breakdown, and the existing trajectory-layer / reducer-merge regressions in
  `tests/test_hazard_layers.py`.

Interpretation:

- Auto-grid bounds discovery is now measurable but small on the representative
  fixture, so explicit-grid remains the right control for accumulation work.
- The smoke profile stays intentionally smaller and routine; it is useful for
  semantic guardrails, but not for selecting the next optimization target.

## TB-229 Bounded Accumulator Spike

A narrow trajectory-accumulation rewrite was tested against the same
fixture-backed multi-zone scratch profile used by the profiler. The attempted
change buffered per-trajectory cell maxima before committing them back to the
existing grids, while leaving reach counts, threshold exceedance counts, merge
contracts, and manifest semantics unchanged.

Measured results on `/tmp/rust_rockfall/tb229_baseline` versus
`/tmp/rust_rockfall/tb229_after`:

- explicit-grid accumulation: `0.068822` s before, `0.070471` s after
- explicit-grid hazard-stage wall time: effectively unchanged within noise
- hazard-layer signatures: unchanged in the smoke guardrail
- path-free manifest semantics: unchanged in the smoke guardrail

Decision:

- reject the buffering rewrite as a retained optimization
- keep the current accumulator implementation unchanged
- leave the bounded next target as trajectory batching or vectorization only if
  a future measured slice can beat this baseline without changing semantics

Before/after profile artifacts were written only to `/tmp` and were not
committed.

## TB-230 Post-Optimization Reprofile

TB-229 left the accumulator unchanged, so this follow-up reprofile checked the
current profiler output against the rejected baseline slice rather than
introducing new hazard behavior.

Smoke profile current state:

- 2 release zones, explicit-only run
- 18 output files / 824030 bytes
- `raster_write_seconds`: `0.024798` s
- `accumulation_seconds`: `0.007730` s
- bottleneck: `raster_write_seconds`

Representative profile current state:

- 12 release zones, auto + explicit runs
- 25 output files / 957723 bytes
- `bounds_discovery_seconds`: `0.000990` s
- `accumulation_seconds`: `0.073202` s
- `raster_write_seconds`: `0.026340` s
- bottleneck: `accumulation_seconds`

Baseline comparison against TB-229:

- TB-229 baseline accumulation: `0.068822` s
- TB-229 rejected after-state accumulation: `0.070471` s
- TB-230 current accumulation: `0.073202` s
- current minus baseline: `+0.004380` s
- current minus rejected after-state: `+0.002731` s

Interpretation:

- The smoke profile is a guardrail, not an optimization target. Its smaller
  scale pushes the bottleneck to raster writes, so it does not overturn the
  representative result.
- The representative profile still reports trajectory accumulation as the
  dominant explicit-grid phase.
- The TB-229 buffering slice is therefore rejected as a retained optimization.
  The current run is slower than both the baseline and the rejected
  after-state, so the evidence supports noise or regression, not improvement.
- The next bounded target remains trajectory batching or vectorization only if
  a later measured slice can beat this baseline without changing hazard
  semantics.
