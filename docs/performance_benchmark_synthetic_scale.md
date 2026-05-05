# Synthetic Scale Performance Benchmark

Status: opt-in local benchmark scaffold. This workflow is intentionally
excluded from `cargo run -- validate --all` because it can create many
trajectory and impact-event files.

## Purpose

The small smoke benchmark proves that timing metadata is written, but it is too
small to identify the first real bottleneck. The standard synthetic benchmark is
short enough for routine local iteration, while the scale profile preserves the
larger exploratory matrix used for data-format decisions. These benchmarks
measure whether current limits come from:

- simulation time;
- deterministic release generation;
- CSV trajectory output;
- CSV or Parquet impact-event output;
- hazard-layer accumulation;
- PNG/HTML report rendering;
- output file count and byte volume.

It does not change physics, tune parameters, or introduce new data formats.

## Runner

Use the default standard profile:

```bash
python3 scripts/run_performance_benchmark.py
```

By default this generates synthetic terrain and source-area metadata under:

```text
validation/results/performance_synthetic_scale/
```

That directory is ignored. It contains generated ESRI ASCII terrain, metadata sidecars, validation case YAML files, validation outputs, hazard-layer outputs, and summary reports.

The runner builds the local debug `rockfall` binary once when needed and reuses
it for generated validation cases. This keeps routine benchmark timing focused
on validation, output, and hazard-layer stages rather than repeated Cargo
startup overhead.

The default `standard` profile is intended to complete comfortably within a
routine local iteration window. On the 2026-05-05 Apple M1 reference run it
completed in about 4.5 seconds after the local debug binary was already built.
Cold builds or slower filesystems may take longer, but the benchmark matrix is
designed to stay below the earlier 20-30 second target on a typical development
machine. It uses:

- release count: `10`;
- contact models: `translational_v0`, `sphere_rotational_v1`;
- shorter synthetic horizon: `t_max = 3.0 s`;
- output modes:
  - full ensemble trajectories without impact-event output;
  - full ensemble trajectories plus Parquet impact-event output;
- hazard layers for trajectory-output cases:
  - `--no-plots` only;
- one representative sampling-weighted hazard stage.

This standard run is intentionally smaller than the exploratory scale matrix and
avoids CSV and CSV+Parquet impact-event output by default. Use `scale` or
`custom` when comparing CSV and Parquet impact-event modes.

## Profiles

The runner supports explicit profiles:

- `smoke`: tiny local/test profile with one release count, one contact model,
  and a minimal no-plot matrix. Use it for script sanity checks.
- `standard`: default routine profile, targeting short local iteration.
- `scale`: larger exploratory profile with counts `500` and `1000`, both contact
  models, CSV, Parquet, CSV+Parquet impact modes, no-plot hazard layers, and one
  representative weighted hazard stage. This can take many minutes and produce
  gigabytes of ignored artifacts.
- `custom`: requires user-provided `--counts` and `--output-modes`.

`--weighted-hazard representative` requires an output mode that writes Parquet
impact events (`parquet` or `csv_parquet`) so the representative run exercises
the columnar impact-event path explicitly.

The canonical post-refactor profile validation is recorded in
`docs/performance_benchmark_profile_reference.md`.

## Useful Commands

Prepare generated cases without running them:

```bash
python3 scripts/run_performance_benchmark.py --dry-run
```

Run the very small smoke profile:

```bash
python3 scripts/run_performance_benchmark.py --profile smoke
```

Run the larger Parquet impact-event scale benchmark used for columnar-output
decisions:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile scale \
  --output-root validation/results/benchmark_reference_scale
```

Run a custom local trial:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 20 50 \
  --output-modes trajectories parquet \
  --contact-models translational_v0
```

Run the selected profile but skip hazard post-processing:

```bash
python3 scripts/run_performance_benchmark.py --skip-hazard
```

Change synthetic terrain size or simulation horizon:

```bash
python3 scripts/run_performance_benchmark.py \
  --terrain-size 120 \
  --cell-size 2 \
  --t-max 8 \
  --dt 0.02
```

## Outputs

The runner writes:

- generated synthetic input fixtures under `validation/results/performance_synthetic_scale/inputs/`;
- generated validation cases under `validation/results/performance_synthetic_scale/cases/`;
- validation manifests and diagnostics under `validation/results/performance_synthetic_scale/validation/`;
- optional hazard-layer outputs under `validation/results/performance_synthetic_scale/hazard/`;
- `summary.csv`;
- `summary.md`.

The summary files collect:

- total wall time;
- terrain load time;
- release generation time;
- simulation time;
- output writing time;
- hazard-layer time;
- trajectory count;
- impact-event count;
- output file count;
- output bytes;
- per-format impact-event file count, byte count, and row count;
- trajectories per second;
- impacts per second.

## Interpretation

Use the summary to decide what should be measured or changed next:

- If simulation time dominates, investigate kernel profiling and parallel ensemble execution.
- If output writing dominates and bytes/file count scale rapidly, investigate binary or columnar trajectory/impact outputs.
- If hazard accumulation dominates, investigate tiled or streaming spatial reducers.
- If plotting dominates, separate diagnostic rendering from production hazard-layer export.
- If all measurements remain small, increase release count, terrain size, or simulation horizon before optimizing.

Do not infer scientific validity from this benchmark. It uses synthetic terrain and source areas only.

## CI Policy

The benchmark script has lightweight unit tests for profile parsing, generated
case shape, and report rendering, but none of the benchmark profiles are run in
CI and they are not part of `cargo run -- validate --all`.
