# Synthetic Scale Performance Benchmark

Status: opt-in local benchmark scaffold. This workflow is intentionally excluded from `cargo run -- validate --all` because it can create many trajectory and impact-event CSV files.

## Purpose

The small smoke benchmark proves that timing metadata is written, but it is too small to identify the first real bottleneck. The synthetic scale benchmark creates larger source-area cases so the project can measure whether current limits come from:

- simulation time;
- deterministic release generation;
- CSV trajectory output;
- CSV impact-event output;
- hazard-layer accumulation;
- PNG/HTML report rendering;
- output file count and byte volume.

It does not change physics, tune parameters, or introduce new data formats.

## Runner

Use:

```bash
python3 scripts/run_performance_benchmark.py
```

By default this generates synthetic terrain and source-area metadata under:

```text
validation/results/performance_synthetic_scale/
```

That directory is ignored. It contains generated ESRI ASCII terrain, metadata sidecars, validation case YAML files, validation outputs, hazard-layer outputs, and summary reports.

The default matrix is:

- release counts: `50`, `100`, `200`;
- contact models: `translational_v0`, `sphere_rotational_v1`;
- output modes:
  - summary/deposition only;
  - full ensemble trajectories;
  - full ensemble impact events;
  - full ensemble trajectories plus impact events;
- hazard layers for trajectory-output cases:
  - with PNG plots;
  - with `--no-plots`.

This is intentionally larger than CI fixtures and should be run locally when investigating performance decisions.

## Useful Commands

Prepare generated cases without running them:

```bash
python3 scripts/run_performance_benchmark.py --dry-run
```

Run a smaller local trial:

```bash
python3 scripts/run_performance_benchmark.py \
  --counts 20 50 \
  --hazard-plots no-plots
```

Run the full default matrix but skip hazard post-processing:

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

The benchmark script has lightweight unit tests for argument-free case generation and report rendering, but the default benchmark matrix is not run in CI and is not part of `cargo run -- validate --all`.
