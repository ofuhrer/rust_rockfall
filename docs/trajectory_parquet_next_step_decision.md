# Trajectory Parquet Next-Step Decision

Status: decision record only. This document does not implement trajectory
Parquet, change simulation physics, change validation semantics, or change
hazard-layer semantics.

## Question

Impact-event Parquet now reduces impact-event file count and byte volume, and
the projected Parquet reader speeds significant-impact hazard accumulation.
The remaining question is whether full trajectory CSV output has become the
dominant scaling bottleneck and therefore whether
`trajectory_samples_table_v1` should be implemented next.

## Evidence Reviewed

Inputs reviewed:

- `docs/columnar_output_design_decision.md`
- `docs/parquet_impact_benchmark_results.md`
- `docs/performance_benchmark_profile_reference.md`
- `scripts/run_performance_benchmark.py`
- `scripts/build_hazard_layers.py`
- `src/validation.rs`

Existing benchmark evidence already showed:

- per-trajectory impact CSVs caused clear small-file pressure;
- Parquet impact output reduced impact-event bytes to roughly 42-49% of CSV;
- projected Parquet impact reads made impact-density accumulation faster;
- Parquet impact writing remained slower than CSV impact writing;
- hazard accumulation still uses trajectory CSV samples for reach,
  energy, jump-height, velocity-exceedance, and deposition layers.

## Targeted Benchmark

To isolate trajectory output, a targeted no-plot benchmark was run with
`summary_only`, `trajectories`, and `parquet` modes:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes summary_only trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none \
  --output-root validation/results/trajectory_bottleneck_300_500
```

Generated outputs are ignored under `validation/results/`.

### Trajectory CSV Output Cost

`summary_only` writes no full trajectory CSVs. `trajectories` writes one
trajectory CSV per release and no impact-event outputs. The table below reports
the incremental trajectory-write cost over `summary_only`.

| releases | model | trajectory files | trajectory rows | trajectory MB | incremental trajectory write s | simulation s |
|---:|---|---:|---:|---:|---:|---:|
| 300 | `translational_v0` | 300 | 45,300 | 12.52 | 2.60 | 2.62 |
| 300 | `sphere_rotational_v1` | 300 | 45,300 | 15.19 | 1.98 | 5.27 |
| 500 | `translational_v0` | 500 | 75,500 | 20.87 | 4.07 | 6.74 |
| 500 | `sphere_rotational_v1` | 500 | 75,500 | 25.32 | 2.81 | 4.87 |

Interpretation:

- trajectory CSV output is a real cost and creates one file per trajectory;
- trajectory bytes are smaller than impact-event bytes in the same benchmark;
- at 300/500 releases, trajectory CSV writing is not consistently larger than
  simulation time;
- trajectory CSV writing is materially smaller than current Parquet
  impact-event writing when impact Parquet is enabled.

### Hazard Accumulation From Trajectory CSVs

The `trajectories` mode builds all non-impact hazard layers from trajectory CSV
samples. The `parquet` mode adds impact-event Parquet for significant-impact
density while preserving the same trajectory CSV path for reach, energy,
jump-height, velocity, and deposition layers.

| releases | model | impact mode | hazard accumulation s | impact events read |
|---:|---|---|---:|---:|
| 300 | `translational_v0` | none | 2.54 | 0 |
| 300 | `translational_v0` | parquet | 3.83 | 38,547 |
| 300 | `sphere_rotational_v1` | none | 4.05 | 0 |
| 300 | `sphere_rotational_v1` | parquet | 3.42 | 38,553 |
| 500 | `translational_v0` | none | 5.76 | 0 |
| 500 | `translational_v0` | parquet | 5.91 | 64,222 |
| 500 | `sphere_rotational_v1` | none | 4.41 | 0 |
| 500 | `sphere_rotational_v1` | parquet | 5.02 | 64,216 |

Interpretation:

- trajectory CSV rasterization alone is now a measurable hazard-stage cost;
- projected Parquet impact reads add little cost in these runs, and sometimes
  timing noise makes the Parquet-impact run appear faster;
- the hazard stage still performs row-wise Python raster accumulation, so a
  trajectory Parquet table would not automatically remove all accumulation
  cost unless the reader also uses projected, batched access.

## Bottleneck Diagnosis

### Simulation Kernel

Simulation remains important but is not the only bottleneck. In the targeted
benchmark, simulation time was comparable to or larger than trajectory CSV
write time for most cases. No simulation optimization is justified by this
evidence alone because output and hazard post-processing remain substantial and
more isolated from physics risk.

### Trajectory CSV Output

Trajectory CSV output is a meaningful scaling pressure:

- one file per trajectory;
- tens of MB at 300/500 releases;
- expected to scale linearly with release count and sample count;
- required by current reach, energy, jump-height, velocity, and deposition
  hazard layers.

It is not yet the dominant remaining output-write bottleneck. Current
impact-event Parquet writing is larger than the incremental trajectory CSV
write cost in the same 300/500 benchmark.

### Impact-Event Writer

The Parquet impact-event writer remains the clearest writer-side problem after
the projected reader improvement. It reduces files and bytes, but its write
time remains higher than CSV for these benchmark sizes.

### Hazard Accumulation

Hazard accumulation from trajectory samples is now a strong candidate for the
next engineering focus. The current Python path still rasterizes row by row.
Trajectory Parquet could help by reducing file opens, bytes, and projected
column reads, but it would need to be paired with a projected/batched reader
path to be performance-positive.

### Filesystem Small-File Pressure

Trajectory CSVs create one file per trajectory. At 500 releases this is already
500 files; at larger ensembles or source-zone grids this will become
operationally awkward even if write time is not yet the largest measured cost.

## Decision

Trajectory Parquet is justified as the next columnar design target, but not as
an urgent replacement for CSV or as the only next engineering step.

Rationale:

- the trajectory CSV path is now the main remaining per-trajectory small-file
  source after impact events can be batched;
- trajectory samples feed most hazard layers, so columnar trajectory access has
  broader hazard-stage value than further impact-only work;
- the measured 300/500 trajectory write and hazard-read costs are large enough
  to justify a minimal opt-in prototype;
- however, impact Parquet writing is still slower than CSV, so trajectory
  Parquet must be introduced carefully and benchmarked against explicit success
  criteria before it becomes a recommended larger-workflow path.

CSV trajectory outputs should remain the default small-case/debug format.

## Minimum `trajectory_samples_table_v1` Requirements

A future opt-in table should include only fields needed to replace current
trajectory CSV consumption:

- `trajectory_id`
- `sample_index`
- `time_s`
- `x_m`, `y_m`, `z_m`
- `vx_mps`, `vy_mps`, `vz_mps`
- `speed_mps`
- `kinetic_energy_j`
- `jump_height_m`
- `contact_state`
- optional rotational diagnostics already present in CSV:
  `omega_x_radps`, `omega_y_radps`, `omega_z_radps`
- optional rolling/contact diagnostics already present in CSV:
  `contact_tangent_speed_mps`, `rolling_residual_mps`

The table must join cleanly to `trajectory_metadata_table_v1` by
`trajectory_id`. It should not introduce probabilities, annual frequencies, or
new hazard semantics.

Manifest entries should record:

- `kind: ensemble_trajectories`
- `format: parquet`
- `schema_version: trajectory_samples_table_v1`
- `path`
- `file_count`
- `row_count`
- `total_bytes`
- `compression`
- `row_group_count`
- the trajectory id count represented in the table

## Success Criteria For A Prototype

Implementing trajectory Parquet is justified only if a prototype can show:

1. CSV and Parquet trajectory hazard layers are numerically identical for reach,
   deposition, max energy, max jump height, velocity exceedance, and configured
   exceedance layers.
2. Trajectory Parquet reduces trajectory file count from one file per
   trajectory to one table or deterministic shards.
3. Trajectory Parquet reduces trajectory byte volume materially at 300/500
   scale.
4. Projected Parquet trajectory reads are no slower than trajectory CSV
   accumulation in no-plot hazard benchmarks.
5. Parquet trajectory writing is not dramatically slower than CSV trajectory
   writing; if it is slower, the file-count and hazard-read gains must be large
   enough to justify opt-in use.
6. Existing CSV outputs remain unchanged and can be written alone, with
   Parquet, or not at all.

## Risks Of Adding It Too Early

- A wide trajectory table may repeat the impact-event writer problem: fewer
  files and bytes but slower writing.
- If the hazard builder still converts Parquet rows into Python dictionaries,
  the expected read benefit may disappear.
- Adding another columnar schema increases maintenance surface before the
  impact-event writer is fully understood.
- Users may assume Parquet is the recommended path for all cases even though
  CSV is still better for small inspection workflows.

## Alternatives If Deferred

If trajectory Parquet is deferred, the next safer engineering steps are:

1. Optimize trajectory CSV hazard accumulation by reducing row-dictionary
   overhead and reading only columns needed for each layer.
2. Add a single batched trajectory CSV per case as a lower-risk file-count
   reduction, preserving text inspection but reducing open/close pressure.
3. Continue profiling the Parquet writer path before adding a second Parquet
   table.
4. Add repeated-run benchmark statistics to separate timing noise from real
   effects.

## Recommendation

Immediate next step:

- implement a minimal opt-in `outputs.ensemble_trajectories_parquet` prototype
  only if it includes projected/batched hazard-reader support and the success
  criteria above are measured in the same change.

Deferred:

- do not remove or de-emphasize trajectory CSV outputs;
- do not implement weighted trajectory semantics as part of the table;
- do not add physical probability or annual-frequency logic;
- do not change default validation or hazard-layer behavior.

