# Swiss-Scale Execution Bottleneck Review (Conditional Hazard Focus)

Status: engineering analysis for future Swiss-scale execution on balfrin-class nodes.
Scope is conditional Tschamut-style hazard workflow only.
Out of scope remains: annual/physical semantics, physics changes, defaults,
or operational claim-making.

## Evidence Baseline

Recent conditional balfrin evidence used:

- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- local-thread reducers and trajectory reducers via deterministic chunk manifests.

Measured baselines (clean balfrin main):

- 2×2 workers: `wall time 9.05s`, `total_wall_seconds 8.2485`,
  `output_write_seconds 2.8636`, `output_bytes 15,579,398`, `output_file_count 46`.
- 4×4 workers: `wall time 9.77s`, `total_wall_seconds 9.2953`,
  `output_write_seconds 3.1814`, `output_bytes 15,614,702`, `output_file_count 50`.

Observed from these runs:

- deterministic IDs and trajectory/reducer lineage are coherent,
- all chunks in fresh runs are executed,
- 4×4 is slower than 2×2 for this small gate workload,
- moderate chunk-count scaling currently adds orchestration overhead before speedup.

This implies current bottlenecks are likely to shift under larger scale factors
before parallelism tuning becomes the primary lever.

## Scaling Estimates by Dimension

Let:

- `Z` = release-zone count,
- `N` = trajectories per zone,
- `C` = grid-cell count at output resolution,
- `P` = output products requested (layers + tables + vectors),
- `S` = trajectory sample count per trajectory (time-step rows),
- `W_t`, `W_r` = trajectory/reducer worker counts.

Expected pressure patterns:

- trajectory generation cost grows with `Z × N`,
- reduction and accumulation grow with `N × C` per layer,
- output/write cost grows with `Z × P × C` for raster tables plus event/trajectory
  file counts,
- metadata and manifest cost grows with artifact count (`trajectories/events/chunks/manifests`).

In current architecture, each additional trajectory largely increases:

- trajectory compute,
- per-trajectory write pressure (if full output policy enabled),
- reducer accumulation updates,
- potential manifest/provenance churn.

## Bottlenecks for Swiss-Scale Conditional Workloads

- trajectory generation throughput: likely dominant once `Z × N` is large and
  local-core parallelism saturates.
- raster accumulation CPU and memory: likely dominant for larger grids where each
  layer touches many more cells.
- output serialization and format overhead: likely dominant for large `P` and
  especially for per-cell tables or verbose grids.
- manifest/provenance and bookkeeping overhead: likely dominant once hundreds to
  thousands of chunks are emitted and every retry/reuse creates additional
  JSON sidecar I/O.
- file-count explosion: likely dominant before raw compute because many small
  trajectory/event files stress directory scans and metadata ops.
- GeoTIFF writing and raster metadata: likely dominant for full raster mode when
  raster bytes rise significantly despite chunking.
- file system metadata pressure: likely dominant with high process/thread counts
  due to open/close and directory churn.
- chunk-state storage: likely dominant for resume-heavy runs with frequent
  partial progress and retries.
- replay bookkeeping consistency: likely dominant once stale/recovered and
  partial reuse logic must be validated for large, long-running jobs.
- hazard-layer reduction merge ordering: likely dominant when many partial states are
  produced and merge ordering must remain deterministic across reruns.

## Chunking Granularity Assessment

- fixed-size trajectory chunk counts derived from worker count are useful for
  local-core utilization but not sufficient for scale.
- for Swiss-scale, chunk policy should be workload-aware (trajectory volume,
  zone density, output-policy breadth), not worker-count-first.
- too many chunks can increase overhead even before core count stops helping.
- chunk sizing should be tuned so that chunk runtime is significantly above I/O
  sidecar overhead and manifest churn for each run phase.

## Output-Policy and Format Direction

- immediate next step is not format conversion but output minimization:
  keep current opt-in scalable controls and avoid high-volume tables unless they
  are explicitly needed.
- trajectory/event artifacts should be separated into:
  - required production-reduced products and
  - optional debug/audit products.
- for tabular trajectory/event products, Parquet remains the strongest next-architecture
  option because it supports compression, columnar scan performance, and better
  chunking than per-file CSV.
- for raster hazard products, GeoTIFF/COG remains the primary exchange format once
  CRS and metadata discipline is enforced.
- Zarr/NetCDF become more attractive only after:
  - stable chunk-indexed raster staging exists,
  - CRS-aware tiling and access semantics are defined,
  - and a storage backend strategy is committed.

## Recommended Near-Term Architecture Work Sequence

1. add explicit production vs debug output profiles and measure file-count reduction
   before increasing compute scale;
2. introduce a deterministic chunk cost model and adaptive chunk-size policy tied to
   trajectory counts and grid footprint;
3. move more trajectory-to-reducer streaming for reduced products where full
   trajectories are not required;
4. consolidate output manifests into explicit per-stage summaries with bounded sidecar
   fan-out.
5. only after the above, evaluate Parquet defaulting paths for trajectory/event
   artifacts and tile-oriented raster merge planning.

## Premature Optimization Warnings

- increasing worker/chunk counts without reducing output volume usually improves
  only orchestration overhead and does not guarantee wall-time reduction.
- re-platforming into Zarr/NetCDF before stable chunk semantics and evidence-driven
  I/O contracts are in place risks format lock-in and reproducibility regressions.
- GIS packaging and visualization changes should follow, not lead, Swiss-scale
  compute/IO bottleneck work.

## Immediate Scaling Frontier for Next Work

- first bottleneck to attack: output volume and file-count minimization under fixed
  scientific outputs.
- second bottleneck: chunk-level cost balancing and deterministic merge planning
  for larger `Z`, `N`, and `C`.
- third bottleneck: scalable raster staging path that reduces repeated
  read-write cycles while preserving deterministic replay semantics.

The current evidence supports treating this as a Swiss-scale execution planning
step rather than an immediate distributed-orchestration feature project.
