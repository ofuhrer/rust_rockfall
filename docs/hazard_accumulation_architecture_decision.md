# Hazard Accumulation Architecture Decision

Status: decision record only. This document does not implement new output
formats, change simulation physics, change validation semantics, or change
hazard-layer semantics.

## Question

Recent benchmark and design records show that impact-event Parquet reduces
impact-event file count and byte volume, projected Parquet reads improve
significant-impact accumulation, and trajectory CSV output is a meaningful but
not yet dominant writer-side bottleneck. The next question is whether the next
performance/scalability step should target:

- Python hazard accumulation;
- tiled or streaming reducers;
- opt-in trajectory Parquet;
- another storage or raster output format.

## Evidence Reviewed

Inputs reviewed:

- `trajectory_parquet_next_step_decision.md`
- `columnar_output_design_decision.md`
- `parquet_impact_benchmark_results.md`
- `hazard_workflow_scale_review.md`
- `scalability_and_data_formats_review.md`
- `scripts/build_hazard_layers.py`
- `scripts/run_performance_benchmark.py`

The most relevant measured results are:

- 500/1000-release scale runs showed that plotting is no longer part of the
  production path when `--no-plots` is used.
- Projected Parquet impact reads reduced significant-impact hazard accumulation
  to roughly 38-49% of the CSV impact path in the 300/500 intermediate run.
- Parquet impact writing remains slower than CSV writing even though it writes
  far fewer files and fewer bytes.
- A 300/500 trajectory-focused benchmark found that full trajectory CSV output
  writes 300-500 files and about 12.5-25.3 MB, with about 2-4 s incremental
  write time.
- The same 300/500 run found trajectory-driven no-plot hazard accumulation at
  about 2.5-5.8 s before adding impact events.

## Current Hazard Workflow

`scripts/build_hazard_layers.py` is already streaming in the narrow sense that
it does not retain all trajectory or impact rows. The current sequence is:

1. Resolve input paths from the case YAML and optional CLI overrides.
2. If no explicit grid is supplied, scan all trajectory CSVs, deposition CSVs,
   impact CSVs, and impact Parquet tables to discover x/y bounds.
3. Allocate complete in-memory raster arrays for each layer.
4. Stream deposition rows into the deposition-density grid and retain
   deposition points for small GeoJSON output.
5. Stream each trajectory CSV through `csv.DictReader`.
6. For each trajectory, maintain per-trajectory occupied-cell and exceedance
   sets, then update reach and exceedance grids once per cell per trajectory.
7. Stream impact-event CSVs or projected impact-event Parquet batches into
   significant-impact density.
8. Normalize layers and write CSV-grid, ESRI ASCII, GeoJSON, JSON metadata, and
   optional PNG/HTML report outputs.

This is a good small-case architecture. It is not yet a production reducer
architecture because it still has full-raster memory, repeated scans in
auto-grid mode, row-wise Python parsing for trajectory CSVs, and no tile/chunk
merge contract.

## Architectural Limitation Diagnosis

### Many Small Trajectory CSV Files

This is real but not alone decisive. One trajectory CSV per trajectory creates
metadata pressure and scales poorly on shared filesystems. The 300/500
benchmark shows the file count is already visible, but the write cost is not
yet the largest measured bottleneck. A future trajectory Parquet table should
address this, but only with projected hazard-reader support.

### Row-Wise Python Loops

This is the dominant implementation limitation inside the hazard builder today.
Trajectory CSV samples are parsed into dictionaries and processed one row at a
time. Each row may touch several layer families: reach, max kinetic energy,
max jump height, kinetic exceedance, jump exceedance, velocity exceedance, and
weighted variants. Even if trajectory Parquet reduces file count and bytes, a
row-dictionary reader would keep much of this cost.

### Repeated Input Scans

Auto-grid mode scans inputs once for bounds and again for accumulation. This is
acceptable for small cases and useful for convenience, but explicit-grid mode
should become the normal benchmark and pilot path. Production-style runs should
know the reference grid from terrain metadata and scenario configuration.

### Lack Of Tiling And Mergeable Reducers

The builder currently allocates complete grids in memory. This is fine for
current fixtures but will not scale to large high-resolution pilot domains or
many scenario layers. Counts and maxima are naturally mergeable; exceedance
counts are also mergeable once thresholds are fixed. A formal reducer state and
merge contract is therefore a better architectural foundation than adding more
file formats first.

### Lack Of Columnar Trajectory Input

This is a near-term gap, but it should not be implemented as a writer-only
feature. The value of `trajectory_samples_table_v1` depends on projected,
batched readers for `x_m`, `y_m`, `kinetic_energy_j`, `jump_height_m` or
`z_m`, `speed_mps`, and `trajectory_id`. Without that reader path, trajectory
Parquet risks repeating the impact writer pattern: fewer files and bytes but
mixed or slower end-to-end runtime.

### Grid Size And Memory

Memory is not yet the measured bottleneck for the current synthetic benchmark,
but the architecture is grid-size sensitive. Every enabled layer allocates a
full `nrows x ncols` Python list of lists. Weighted layers and exceedance
thresholds multiply this memory footprint. This becomes important for
Swiss-style tiled terrain and many scenario layers.

### Output Raster Writing

Core raster writing is not currently the bottleneck. The benchmarked
`core_output_write_seconds` values are small compared with accumulation time.
GeoTIFF or other raster export remains important for interoperability, but not
as the immediate performance fix.

## Next-Step Options

### Option A: Tiled/Streaming Hazard Reducer Contract

Objective: define and implement reducer states that can accumulate one tile or
chunk at a time and merge deterministically.

Expected value:

- addresses full-raster memory before real pilot grids become large;
- establishes merge rules for counts, maxima, and exceedance counts;
- prepares for job-array or chunked execution without changing physics;
- works with CSV now and future Parquet later.

Risks:

- moderate design complexity;
- easy to overbuild if tile manifests, merge state, and output products are
  introduced all at once;
- tests must prove numerical identity with current whole-grid outputs.

Best use:

- next architecture foundation for Swiss pilot scalability.

### Option B: Projected/Batched Trajectory Reader And Split Accumulation Kernels

Objective: refactor the current whole-grid Python builder so trajectory inputs
can be read as typed batches and processed by layer-specific accumulator
kernels. Start with CSV-compatible batching, then reuse the same interface for
future trajectory Parquet.

Expected value:

- directly targets the measured row-wise Python trajectory bottleneck;
- can reduce repeated parsing and dictionary overhead;
- creates the reader abstraction needed before `trajectory_samples_table_v1`;
- preserves current CSV outputs and current hazard layer semantics.

Risks:

- pure Python batching may still be limited if per-cell updates remain Python
  loops;
- vectorization is constrained by the per-trajectory occupied-cell semantics
  for reach and exceedance probabilities;
- requires careful parity tests against current outputs.

Best use:

- safest immediate implementation step before adding trajectory Parquet.

### Option C: Opt-In Trajectory Parquet With Projected Reader

Objective: add `outputs.ensemble_trajectories_parquet` and teach the hazard
builder to read only required columns in batches.

Expected value:

- reduces trajectory small-file pressure;
- likely reduces trajectory byte volume;
- enables projected reads for reach, energy, jump-height, velocity, and
  exceedance layers;
- aligns with future columnar output design.

Risks:

- writer may be slower than CSV, as seen with impact Parquet;
- adds another schema before the reducer architecture is stable;
- if implemented before reader refactoring, it may not improve hazard runtime.

Best use:

- next columnar feature after the hazard reader/reducer interface is explicit.

## Recommendation

Immediate next implementation step:

- implement a **hazard input batching and reducer-interface refactor** in
  `scripts/build_hazard_layers.py`, while preserving current CSV and Parquet
  inputs and all numerical outputs.

This should be intentionally smaller than a full tiled production reducer. The
first slice should:

- introduce a typed internal batch representation for trajectory samples and
  impact events;
- keep existing CSV trajectory inputs but convert them into batches rather than
  row dictionaries at the accumulator boundary;
- keep projected Parquet impact batches on the same internal interface;
- split accumulation logic by layer family: trajectory occupancy/exceedance,
  maxima, deposition, significant impacts, and weighted layers;
- add manifest or benchmark summary fields for input rows per second if this
  can be done cleanly;
- preserve explicit-grid and auto-grid behavior, while documenting explicit
  grids as the preferred benchmark and pilot mode.

Rationale:

- the measured bottleneck is now hazard-stage row processing, not core raster
  writing;
- trajectory Parquet is only likely to help if the hazard builder can consume
  projected/batched inputs;
- a reducer interface is useful whether the next storage input is CSV, Parquet,
  or direct simulator streaming;
- the change is post-processing only and avoids physics risk.

## Required Tests

The next implementation should include tests that verify:

- current CSV trajectory hazard layers are byte- or value-equivalent before and
  after the refactor;
- CSV and Parquet impact-density layers remain numerically identical;
- weighted hazard layers remain unchanged;
- explicit-grid mode and auto-grid mode still produce expected extents;
- non-finite row handling and warning behavior remain unchanged;
- input row counts and, if added, rows-per-second metrics match fixture inputs;
- benchmark-profile smoke and standard runs still complete successfully.

## Benchmark Success Criteria

Use the existing benchmark profiles plus a focused custom benchmark:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none
```

Success criteria:

- no numerical layer differences relative to the current implementation;
- no regression in CSV impact or Parquet impact parity tests;
- hazard accumulation time for trajectory-only runs is no worse than current
  timings and preferably improves by at least 15-25% at 300/500 releases;
- projected Parquet impact accumulation remains faster than CSV impact
  accumulation;
- output raster writing remains a small fraction of total hazard time.

## Out Of Scope For The Next Step

- no trajectory Parquet writer yet;
- no new hazard-layer semantics;
- no annual-frequency or physical probability modelling;
- no GeoTIFF/COG export;
- no distributed execution framework;
- no removal or deprecation of CSV debug outputs;
- no changes to simulation physics or validation pass/fail criteria.

## Medium-Term Follow-Up

After the input batching and reducer interface exists, the next two steps are:

1. Add a minimal opt-in `trajectory_samples_table_v1` writer and projected
   trajectory Parquet reader, measured against the success criteria in
   `trajectory_parquet_next_step_decision.md`.
2. Extend the reducer interface into tile/chunk states with deterministic merge
   rules for counts, maxima, and fixed-threshold exceedance layers.

## First Slice Implementation Note

The first implementation slice introduced typed internal trajectory and impact
batches inside `scripts/build_hazard_layers.py` while preserving existing CSV,
Parquet, and raster outputs. The slice is an architecture boundary, not a
vectorization or tiling optimization.

Post-change benchmark command:

```bash
python3 scripts/run_performance_benchmark.py \
  --profile custom \
  --counts 300 500 \
  --output-modes trajectories parquet \
  --contact-models translational_v0 sphere_rotational_v1 \
  --hazard-plots no-plots \
  --weighted-hazard none \
  --output-root validation/results/hazard_batch_refactor_300_500
```

The timing signal was mixed, which is expected for a boundary refactor that
still performs Python-level per-sample cell updates. The useful outcome is that
trajectory CSV, impact CSV, and projected impact Parquet inputs now meet an
internal batch interface, so a future trajectory Parquet reader or tiled reducer
can be added without changing hazard semantics.

## Consolidation Review

The post-implementation cleanup tightened the boundary by making deposition
inputs use the same typed-batch pattern as trajectory and impact inputs.
Parsing now ends at `TrajectorySampleBatch`, `DepositionPointBatch`, and
`ImpactEventBatch`; accumulation consumes those batches and no longer depends
on raw CSV row dictionaries except for the shared low-level CSV parser and
grid-bound discovery. Empty trajectory files intentionally preserve the legacy
"one supplied trajectory file" counting behavior in unweighted mode, while
weighted mode still rejects empty trajectory files because there is no
trajectory id to join against metadata.

The consolidation remains a semantic no-op: CSV trajectory input, CSV impact
input, projected Parquet impact input, auto-grid mode, explicit-grid mode,
weighted layers, and output filenames/schemas are unchanged.
