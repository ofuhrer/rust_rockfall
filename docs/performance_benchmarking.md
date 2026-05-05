# Performance Benchmarking

Status: lightweight instrumentation scaffold. This document describes how to measure runtime and output volume before optimizing the simulator or changing data formats. It does not define performance budgets and does not change physics.

## Purpose

The current simulator and hazard workflow are still research tools. Before adding binary formats, tiled reducers, or parallel orchestration, each run should expose enough timing and output-volume metadata to answer:

- how many trajectories were simulated;
- how many impact events were emitted;
- how much time was spent loading terrain/provenance inputs;
- how much time was spent generating releases;
- how much time was spent in simulation;
- how much time was spent writing outputs;
- how large the produced output set is;
- how long hazard-layer accumulation took.

These measurements are wall-clock diagnostics. They are useful for comparing workflow choices on the same machine, but they are not deterministic validation metrics.

## Manifest Timing Fields

`run_manifest_v1` now includes an additive `performance` object when the current validation or hazard tooling writes a manifest:

- `total_wall_seconds`
- `terrain_load_seconds`
- `release_generation_seconds`
- `simulation_seconds`
- `output_write_seconds`
- `hazard_layer_seconds`
- `accumulation_seconds`
- `core_output_write_seconds`
- `plot_render_seconds`
- `plots_enabled`
- `bounds_discovery_seconds`
- `deposition_accumulation_seconds`
- `trajectory_accumulation_seconds`
- `impact_accumulation_seconds`
- `normalization_seconds`
- `trajectory_count`
- `impact_event_count`
- `trajectory_sample_rows_read`
- `deposition_rows_read`
- `impact_event_rows_read`
- `total_hazard_input_rows_read`
- `trajectory_files_scanned`
- `deposition_files_scanned`
- `impact_csv_files_scanned`
- `impact_parquet_tables_scanned`
- `bounds_input_rows_scanned`
- `trajectory_rows_per_second`
- `deposition_rows_per_second`
- `impact_rows_per_second`
- `hazard_input_rows_per_second`
- `output_file_count`
- `output_bytes`

Validation manifests set hazard-specific timings to `null` or omit them. Hazard-layer manifests set the simulation-specific timings to `0.0` because they consume existing CSV/JSON files rather than running the Rust kernel. For hazard manifests, `hazard_layer_seconds` is retained as a backward-compatible alias for `accumulation_seconds`; `output_write_seconds` is the sum of `core_output_write_seconds` and `plot_render_seconds`.

Older manifests without `performance` remain readable; the field is optional.
Older hazard manifests without the row-throughput counters also remain
readable. The rows-per-second fields are diagnostic timing ratios, not stable
validation metrics.

## CI-Safe Smoke Benchmark

The checked-in smoke case is intentionally tiny:

```bash
cargo run -- validate --case validation/cases/performance_smoke.yaml
```

It uses the synthetic swissALTI3D-style DEM and release-zone fixtures, writes a manifest under `validation/results/performance_smoke_manifest.json`, and verifies that timing instrumentation works without requiring private data or large ensembles.

This case is part of `cargo run -- validate --all`. Its timing values should not be used as pass/fail performance budgets because they depend on local CPU, filesystem cache, and build mode.

## Hazard-Layer Timing

After running a case with ensemble trajectory output, build hazard layers as usual:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml \
  --output-dir hazard/results/swissalti3d_hazard_statistics \
  --cell-size 2 \
  --no-plots
```

The generated hazard manifest records accumulation time, core output writing
time, optional plot/report rendering time, output file count, output bytes,
trajectory count, impact-event count, input row counts, file/table scan counts,
and coarse rows-per-second diagnostics. Use this to compare
representative-trajectory runs against full-ensemble runs, explicit-grid mode
against auto-grid mode, and plotting enabled versus `--no-plots`.

Use `--no-plots` for benchmark and larger workflow runs. Omit it only when a local PNG/HTML diagnostic report is needed for inspection.

## Medium Private Benchmark Recipe

Use this only with local/private data. Do not commit raw geodata or generated large outputs.

Recommended input:

- one manually supplied swissALTI3D-style ESRI ASCII crop;
- `EPSG:2056` horizontal CRS and `LN02` heights;
- 2 m resolution for the first benchmark;
- approximately `250 x 250` to `500 x 500` cells, depending on local storage;
- one source-area polygon with 50 to 200 deterministic release points;
- optional terrain-class raster aligned with the DEM.

Recommended cases:

1. `translational_v0` baseline.
2. `sphere_rotational_v1` comparison.
3. Optional roughness-enabled run only after the deterministic baseline is understood.

Recommended outputs:

- first run: diagnostics JSON, manifest JSON, ensemble deposition CSV only;
- second run: enable `ensemble_trajectories_dir`;
- third run: enable both `ensemble_trajectories_dir` and `ensemble_impact_events_dir`;
- hazard layers: reach probability, deposition density, maximum kinetic energy, maximum jump height, significant impact density, and configured exceedance layers.

Record:

- model version and git hash from manifests;
- config fingerprint;
- release count and trajectory count;
- impact-event count;
- total wall time;
- simulation time;
- output-write time;
- hazard-layer time;
- output file count and output bytes;
- whether plotting was enabled;
- grid cell size and explicit-grid settings.

The point of this benchmark is to locate the first bottleneck, not to optimize. Expected first bottlenecks are full trajectory CSV volume, impact-event CSV volume, and hazard-layer output size.

## Synthetic Scale Benchmark

When private terrain is not available, use the opt-in synthetic scale benchmark:

```bash
python3 scripts/run_performance_benchmark.py
```

This runs the default `standard` profile and generates synthetic terrain,
source-area metadata, validation cases, and benchmark outputs under ignored
`validation/results/performance_synthetic_scale/`. The standard profile is a
short no-plot matrix over 10 releases, both contact models, full trajectory
output, Parquet impact-event output, a shorter synthetic horizon, and one
representative sampling-weighted hazard stage. It is intended for routine local
iteration. The runner builds the local debug `rockfall` binary once when needed
and reuses it for generated cases, so default timing is not dominated by repeated
Cargo startup. Use `scale` or `custom` when CSV impact-event output must be
included.

The post-refactor reference run completed the standard profile in about 4.5 s
on an Apple M1 after the debug binary was available. The same run completed the
scale profile in about 27m49s and generated 2.4 GB of ignored artifacts. See
`performance_benchmark_profile_reference.md` for the canonical numbers and
engineering conclusions.

For larger data-format decisions, use the explicit scale profile:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile scale \
  --output-root validation/results/benchmark_reference_scale
```

The scale profile uses release counts `500` and `1000`, includes CSV+Parquet
impact output, may take many minutes, and can produce gigabytes of ignored
artifacts. Use `--profile smoke` for a very small script sanity check and
`--profile custom --counts ... --output-modes ...` for targeted local trials.

See `docs/performance_benchmark_synthetic_scale.md` for command variants and interpretation guidance. The synthetic benchmark is intentionally not part of `cargo run -- validate --all`.

## Interpretation Rules

- Compare timings only on the same machine and preferably in release mode if the goal is throughput.
- Keep debug and scientific outputs enabled or disabled consistently across comparisons.
- Treat output bytes and file count as first-class performance results.
- Do not change physics to improve benchmark results.
- Do not replace CSV/ASCII outputs until measurements show which data path is actually limiting the workflow.
