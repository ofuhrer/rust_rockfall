# Columnar Output Design Decision

Status: design decision only. This document does not implement a new output
format, remove CSV outputs, change validation semantics, or change simulation
physics.

## Context

The 500/1000 release synthetic benchmark showed that the next scaling pressure
is no longer just simulation time:

- impact-event CSV output dominates or competes with simulation time;
- full trajectory plus impact mode creates thousands of files;
- hazard accumulation becomes expensive when it reads many impact-event CSVs;
- core hazard raster writing is not the bottleneck;
- plotting/report rendering has already been separated from production
  no-plot hazard generation.

The largest measured 1000-release cases produced:

| Case | Total wall s | Simulation s | Output write s | Files | Output bytes |
|---|---:|---:|---:|---:|---:|
| baseline, impacts only | 10.29 | 4.15 | 6.10 | 1003 | 171.0 MB |
| baseline, trajectories + impacts | 13.82 | 4.84 | 8.92 | 2003 | 241.5 MB |
| rotational, impacts only | 13.64 | 6.96 | 6.64 | 1003 | 179.2 MB |
| rotational, trajectories + impacts | 15.11 | 6.03 | 9.04 | 2003 | 262.7 MB |

The immediate problem is therefore output volume and file-count pressure,
especially for impact events. Hazard accumulation is also slowed by reading many
small impact files.

## Requirements

Any new output path must:

- be opt-in and preserve existing CSV outputs;
- keep tiny fixtures and `cargo run -- validate --all` behavior unchanged;
- support deterministic trajectory ids and reproducible manifests;
- focus first on impact events, then trajectories;
- support Python hazard-layer post-processing without loading everything into
  memory;
- support schema evolution as diagnostics grow;
- avoid changing simulation physics or validation pass/fail semantics.

## Options

### A. Parquet/Arrow

Description: write one batched Parquet file per case for impact events and later
one batched Parquet file per case for trajectory samples, using Arrow-compatible
column schemas.

Write/read performance:

- Strong for large tabular event/sample data.
- Compression and columnar layout should reduce impact-event output bytes and
  read only columns needed for hazard accumulation.
- Row groups can be organized by trajectory id or chunks of trajectory ids.

File-count reduction:

- Excellent. A case can move from one CSV per trajectory plus one CSV per
  impact-event trajectory to one impact-event Parquet file and one trajectory
  Parquet file.

Suitability for HPC:

- Strong. Row groups and partitioning can later support chunked writers,
  process-local shards, and post-run compaction.
- Deterministic shard naming can preserve order-independent execution.

Python/Rust ecosystem maturity:

- Strong. Rust has Arrow/Parquet ecosystem support; Python has mature Parquet
  readers and column filtering.
- Adds dependencies, so the first implementation should be opt-in and isolated.

Ease of streaming hazard accumulation:

- Strong. The hazard builder can read only `x`, `y`, energy/jump/velocity, and
  impact significance columns, either row group by row group or via batches.

Schema evolution:

- Good. Additive columns can preserve backward compatibility if schemas are
  versioned and manifests record schema version and optional-column presence.

Interoperability:

- Strong for data science and HPC workflows.
- Not a GIS raster format, but appropriate for trajectory and event tables.

Implementation complexity:

- Medium. Requires introducing Arrow schema definitions, optional writers, and
  Python readers. The schema work is real but aligned with the benchmark
  bottleneck.

Assessment:

- Best fit for the measured impact/trajectory table bottleneck.

### B. Single Batched CSV Per Case

Description: write one impact-event CSV per case and one trajectory CSV per
case, each with a `trajectory_id` column.

Write/read performance:

- Better than thousands of small files due to fewer open/close operations.
- Still text-heavy and larger than columnar compressed formats.

File-count reduction:

- Excellent. Reduces thousands of files to one or two tabular files.

Suitability for HPC:

- Moderate. Appending from many workers is awkward; safer designs require one
  CSV shard per worker plus merge.

Python/Rust ecosystem maturity:

- Excellent and already used.

Ease of streaming hazard accumulation:

- Good. Python can stream rows from one file.

Schema evolution:

- Weak to moderate. Additive columns are easy, but type metadata and optional
  fields remain informal.

Interoperability:

- High for inspection, low for larger analytical workflows.

Implementation complexity:

- Low. This is the simplest near-term fallback.

Assessment:

- Good intermediate step if dependency risk blocks Parquet/Arrow, but likely
  insufficient for larger Swiss-scale ensembles because it keeps the largest
  byte-volume issue.

### C. SQLite

Description: write impact events and trajectory samples into one SQLite
database per case.

Write/read performance:

- Good for indexed queries and moderate data sizes.
- Bulk insert performance can be acceptable, but row-oriented storage is not
  ideal for scanning millions of events into raster accumulators.

File-count reduction:

- Excellent: one database file per case.

Suitability for HPC:

- Weak to moderate. Concurrent writes from many processes are possible only with
  care and are not a natural fit for distributed ensemble shards.

Python/Rust ecosystem maturity:

- Excellent. Available everywhere.

Ease of streaming hazard accumulation:

- Good for simple SQL cursors; less efficient than columnar scans.

Schema evolution:

- Good with migrations, but migration discipline must be added.

Interoperability:

- Good for general tooling, less standard for numerical trajectory archives.

Implementation complexity:

- Medium. Requires schema migrations and bulk insert handling.

Assessment:

- Useful for local metadata/catalog workflows, not the best primary archive for
  high-volume sample/event arrays.

### D. HDF5

Description: store arrays for trajectories and impact events in HDF5 datasets.

Write/read performance:

- Strong for large arrays when chunked well.

File-count reduction:

- Excellent.

Suitability for HPC:

- Strong in some HPC environments, especially where HDF5 is standard.
- Parallel HDF5 adds operational complexity.

Python/Rust ecosystem maturity:

- Python support is mature. Rust support exists but tends to involve native
  library concerns and more platform-specific setup.

Ease of streaming hazard accumulation:

- Good with chunked datasets.

Schema evolution:

- Moderate. Requires careful group/dataset conventions and metadata attrs.

Interoperability:

- Strong in scientific computing, weaker in cloud-native and data-frame
  workflows than Parquet.

Implementation complexity:

- Medium to high due to native dependency and packaging concerns.

Assessment:

- Technically viable, but heavier than needed for the current table-shaped
  impact/trajectory outputs.

### E. Zarr/Icechunk

Description: store chunked arrays or cloud-native array stores for trajectories
and impact events.

Write/read performance:

- Strong for chunked array workloads and object-storage-oriented workflows.

File-count reduction:

- Mixed. Zarr can create many chunk objects; Icechunk-style manifests can help,
  but this is not a simple local-file reduction story.

Suitability for HPC:

- Potentially strong for future tiled or cloud workflows.

Python/Rust ecosystem maturity:

- Python ecosystem is stronger than Rust for this use case. Rust integration
  would require more investigation.

Ease of streaming hazard accumulation:

- Good if chunking is designed around spatial or trajectory batches.

Schema evolution:

- Good for array metadata, but table-like variable-width records and additive
  columns are less direct than Arrow schemas.

Interoperability:

- Strong in cloud-native scientific array workflows, less common for event
  tables than Parquet.

Implementation complexity:

- High relative to the current need.

Assessment:

- Promising for future raster/tiled state, not the immediate answer for
  impact-event tables.

### F. Keep Current Per-Trajectory CSVs

Description: keep one trajectory CSV and one impact-event CSV per trajectory.

Write/read performance:

- Acceptable for small validation and debugging cases.
- Poor at the benchmark scale due to file-count pressure and repeated open/read
  overhead.

File-count reduction:

- None. The 1000-release trajectory+impact case produced `2003` files.

Suitability for HPC:

- Weak beyond debugging. Many small files are unfriendly to shared filesystems
  and later job-array workflows.

Python/Rust ecosystem maturity:

- Excellent.

Ease of streaming hazard accumulation:

- Simple but inefficient for many files.

Schema evolution:

- Informal and easy for humans, but weak for larger automated workflows.

Interoperability:

- Good for inspection, weak for production data pipelines.

Implementation complexity:

- None.

Assessment:

- Keep as the default inspectable/debug path, but do not rely on it for larger
  benchmark or pilot ensembles.

## Decision

Recommended immediate implementation target: **Parquet files using Arrow-style
schemas, impact events first, trajectories second.**

The first implementation should be opt-in and should not remove or alter current
CSV outputs.

Recommended first target:

```yaml
outputs:
  ensemble_impact_events_parquet: validation/results/<case>_impact_events.parquet
```

Recommended second target:

```yaml
outputs:
  ensemble_trajectories_parquet: validation/results/<case>_trajectories.parquet
```

Rationale:

- The benchmark’s most obvious output bottleneck is impact-event volume and
  impact-event file count.
- Hazard accumulation needs a small subset of columns, which maps well to
  Parquet column reads.
- A single case-level Parquet file directly addresses thousands of small files.
- Keeping CSV outputs preserves debugging, fixtures, and current validation
  behavior.

## Migration Strategy

Phase 1: schema design only

- Define `impact_events_table_v1` and `trajectory_samples_table_v1` schemas in
  docs and code comments.
- Keep existing CSV schemas unchanged.
- Add manifest vocabulary for optional columnar outputs.

Phase 2: impact-event Parquet writer (implemented)

- Add opt-in `outputs.ensemble_impact_events_parquet`.
- Write one row per impact event with `trajectory_id`, `seed`, and all existing
  `ImpactEvent` fields.
- Preserve `outputs.ensemble_impact_events_dir` exactly as-is.
- Allow cases to write CSV, Parquet, both, or neither.

Phase 3: hazard reader (implemented for impact events)

- Teach `scripts/build_hazard_layers.py` to read
  `ensemble_impact_events_parquet` when present or when explicitly passed.
- Keep CSV impact-event directory support.
- Compare hazard layers from CSV and Parquet inputs for numerical identity.
- Use projected Parquet column reads for impact-density post-processing instead
  of converting complete impact-event rows into Python dictionaries.

Phase 4: trajectory Parquet writer

- Add opt-in `outputs.ensemble_trajectories_parquet`.
- Write one row per trajectory sample with `trajectory_id`, `seed`, sample
  fields, and contact/scarring/rolling diagnostics.
- Preserve `outputs.ensemble_trajectories_dir`.

Phase 5: benchmark comparison

- Re-run the 500/1000 synthetic benchmark with:
  - CSV impact events only;
  - Parquet impact events only;
  - CSV trajectories plus CSV impacts;
  - Parquet trajectories plus Parquet impacts;
  - both CSV and Parquet enabled for debugging overhead measurement.

Writer-side profiling after the first impact-event Parquet implementation found
that projected Parquet reads are performance-positive for hazard accumulation,
but Parquet writing remains slower than CSV at 300/500-release scale. A
schema-neutral column-buffer preallocation was retained; compression and page
statistics changes did not consistently improve write time. This keeps the
design priority unchanged: optimize or understand the existing impact-event
table before adding `trajectory_samples_table_v1`.

## Manifest and Schema Changes

Add optional output fields:

```yaml
outputs:
  ensemble_impact_events_parquet: path
  ensemble_trajectories_parquet: path
```

Add manifest output entries:

- `kind: ensemble_impact_events`
- `format: parquet`
- `schema_version: impact_events_table_v1`
- `path`
- `file_count`
- `row_count`
- `total_bytes`
- optional `row_group_count`
- optional `compression`

and:

- `kind: ensemble_trajectories`
- `format: parquet`
- `schema_version: trajectory_samples_table_v1`
- `path`
- `file_count`
- `row_count`
- `total_bytes`
- optional `row_group_count`
- optional `compression`

Add performance fields only if they can be recorded cleanly:

- `columnar_output_write_seconds`
- `csv_output_write_seconds`

If this split makes timing code noisy, keep the existing
`output_write_seconds` and compare output entries by format in post-processing.

## Benchmark Metrics Before/After

Compare at least:

- total wall time;
- simulation time;
- output write time;
- hazard accumulation time;
- core hazard output write time;
- output bytes;
- file count;
- impact-event row count;
- trajectory sample row count;
- trajectories/s;
- impacts/s;
- hazard input rows/s;
- numerical equality of hazard layers between CSV and columnar inputs.

Primary success criteria for impact-event Parquet:

- large reduction in file count;
- reduced impact-event output bytes;
- reduced output write time or at least no major regression;
- reduced hazard accumulation time for impact-density layers;
- identical significant-impact-density raster relative to CSV input.

Secondary success criteria for trajectory Parquet:

- reduced trajectory output bytes;
- reduced hazard accumulation time for reach, energy, jump-height, and
  exceedance layers;
- identical hazard rasters relative to CSV input.

## Risks

- Dependency footprint increases in Rust and Python.
- Arrow/Parquet schema definitions must be kept stable and documented.
- Parquet is less inspectable than CSV; CSV must remain available for debugging
  and small fixtures.
- Per-case single-file output may be too coarse for future distributed jobs.
  Later phases may need deterministic shard files plus a manifest-level logical
  dataset view.
- Compression choices can trade CPU for bytes; benchmarks must record
  compression settings.

## Deferred Decisions

- GeoTIFF/COG remains a GIS-interoperability target for hazard rasters, not a
  solution to the measured trajectory/impact table bottleneck.
- Parallel ensemble execution should wait until output paths can absorb
  parallel throughput.
- Zarr/Icechunk should be revisited when tiled raster/state workflows or
  cloud-native stores become the primary bottleneck.
- SQLite can be reconsidered for run catalogs and metadata, not high-volume
  impact or trajectory samples.
