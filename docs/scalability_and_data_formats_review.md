# Scalability And Data Formats Review

Status: planning review for the v0.5.x workflow. This document proposes
architecture and data-format changes only. It does not define new physics,
change validation semantics, or make current outputs operational hazard products.

## Purpose

The current workflow is intentionally transparent and development-oriented:
small YAML cases, Rust simulation, CSV trajectory and impact diagnostics, Python
hazard-layer post-processing, CSV/ASCII/GeoJSON outputs, and local reports. That
is appropriate for verification, validation fixtures, calibration experiments,
and scientific debugging.

Swiss-scale probabilistic hazard mapping has different constraints. It requires
many release zones, large DEM tiles, large ensembles, resumable execution,
tile-wise reductions, CRS-aware outputs, and provenance that survives job-array
or distributed execution. The main scaling question is therefore not whether the
single trajectory kernel can run one more trajectory. It is whether the workflow
can avoid producing, parsing, and managing a huge number of debug artifacts when
only reduced hazard layers are needed.

## Current Workflow Inventory

### Input Data

| Input | Current representation | Scale posture |
| --- | --- | --- |
| Analytic terrain | YAML case fields mapped to `TerrainConfig` | Development and verification |
| DEM terrain | Small ESRI ASCII grids, strict or clamped | Small fixtures and validation patches |
| swisstopo terrain | Metadata strategy and sample metadata only | Future operational geodata input |
| Release points | CSV observations or YAML single release | Validation/debug; not release-zone scale |
| Release zones | Not implemented | Required for hazard mapping |
| Block parameters | YAML `block` and optional release CSV mass/radius | Small scenario inputs |
| Contact/scarring/roughness parameters | YAML case parameters | Explicit and reproducible, but not spatial fields |
| Calibration parameters | Committed experiment summaries, not defaults | Research diagnostics only |
| Scenario metadata | Case YAML plus diagnostics JSON | Partial; no standard run manifest yet |

### Simulation Execution

The Rust core has good separation between computation and I/O. `simulate_fixed_step`
and `simulate_fixed_step_with_events` are deterministic for explicit inputs and do
not perform file I/O. `SimulationConfig::run_with_terrain` reuses a constructed
terrain object, and `simulate_ensemble` derives stable trajectory seeds from
global seed, case ID, and trajectory ID.

Current execution modes:

- single JSON simulation through `rockfall run`;
- verification and validation YAML cases through the CLI;
- validation ensembles over release-point CSVs;
- opt-in full ensemble trajectory output through
  `outputs.ensemble_trajectories_dir`;
- opt-in full ensemble impact-event output through
  `outputs.ensemble_impact_events_dir`;
- diagnostics JSON reports for cases;
- calibration scripts that generate temporary cases and collect metrics.

This is designed for correctness, reproducibility, and inspection. It is not yet
designed for national job arrays or for streaming samples directly into reducers.

### Post-Processing

`scripts/build_hazard_layers.py` consumes existing outputs and builds:

- `reach_probability` from supplied trajectory CSVs;
- `deposition_density` from ensemble deposition CSV;
- `max_kinetic_energy` from trajectory CSVs;
- `max_jump_height` from trajectory CSVs plus terrain evaluation;
- `significant_impact_density` from impact-event CSVs.

The builder currently reads CSV rows into Python memory, allocates complete
in-memory raster arrays, then writes development products. It can prefer
`ensemble_trajectories_dir` and `ensemble_impact_events_dir` when those exist,
which makes small-to-medium ensemble layers scientifically more meaningful than
representative-trajectory layers.

### Outputs

| Output | Current format | Intended current use |
| --- | --- | --- |
| Representative trajectory | CSV | Debug, verification, examples |
| Per-ensemble trajectory | One CSV per trajectory | Small-to-medium inspection only |
| Impact events | CSV and optional JSON | Impact audit and calibration diagnostics |
| Diagnostics report | JSON | Case metrics, model version, warnings |
| Ensemble deposition | CSV | Validation and deposition-density input |
| Hazard grids | CSV grid and ESRI ASCII grid | Development, tests, local inspection |
| Deposition points | GeoJSON | Small point-cloud visualization |
| Plots/reports | PNG and HTML | Local review, not authoritative data |

The current output set is excellent for traceability and review. It is explicitly
not a production-scale data layout.

## Bottleneck Analysis

| Bottleneck | Where it occurs | Why it matters | Likely limiting scale | Severity | Timing |
| --- | --- | --- | --- | --- | --- |
| Many small trajectory files | `ensemble_trajectories_dir`, one CSV per trajectory | Creates high metadata overhead, slow directory scans, poor HPC filesystem behavior, and expensive post-processing discovery | Tens of thousands to millions of trajectories | High | Urgent before large ensembles |
| Many small impact-event files | `ensemble_impact_events_dir`, one CSV per trajectory with impacts | Contact-rich trajectories can produce large event logs and many files; empty files are skipped, complicating completeness checks | Large contact-rich ensembles | High | Urgent before impact-density production |
| Text CSV parse/write cost | Rust/validation output and Python hazard input | CPU and I/O cost scale with text formatting, repeated headers, and string parsing | Millions of samples or repeated runs | High | Near-term |
| In-memory hazard rasterization | `build_hazard_layers.py` | All rows and full raster arrays are held in memory; no streaming or tile merge | Large rasters, many trajectories, high-resolution Swiss tiles | High | Near-term for pilot scaling |
| Representative trajectory defaults | Validation writes one full trajectory plus ensemble deposition by default | Reach, energy, jump-height layers can silently represent only one path unless full ensemble outputs are enabled | Any scientific ensemble interpretation | Medium | Already documented; keep warnings visible |
| Full trajectory storage volume | Per-sample outputs for every ensemble member | Full trajectories are often unnecessary once reduced hazard layers are available | Large ensembles or long run durations | High | Near-term design issue |
| Impact-event storage volume | Raw event ledger includes low-energy chatter | Raw logs are valuable for audit but too large for routine map production | Rough/contact-rich slopes, small time steps | Medium to high | Future for national scale; near-term for dense diagnostics |
| Repeated DEM loading | Current APIs can reuse terrain within local loops, but workflows rebuild by case/script boundary | Large DEMs will be expensive to parse repeatedly; ASCII DEM is not tiled or indexed | Large DEM tiles or many worker processes | Medium | Future after real terrain ingestion |
| ESRI ASCII terrain format | DEM fixtures and hazard grids | No CRS, inefficient text format, no tiling/compression | Pilot geodata exchange and large rasters | High | Near-term for Swiss pilot outputs |
| Lack of CRS/reference-grid metadata | Hazard outputs and some case metadata | Products cannot be safely aligned or exchanged as Swiss geodata | Any LV95/LN02 pilot product | High | Urgent before Swiss pilot |
| No output manifest | Verification, validation, hazard, calibration outputs | Hard to track completeness, config hash, terrain source, chunk IDs, seed ranges, file sizes, and calibration state | Multiple chunks/jobs/scenarios | High | Immediate low-risk task |
| No restart/resume model | Validation and hazard scripts | Failed large jobs require manual inspection and rerun; partial outputs lack a formal completion record | Long ensembles and job arrays | High | Near-term |
| Serial local ensemble orchestration | `simulate_ensemble` and validation loops | Deterministic but local; no chunk IDs, job partitions, or merge contracts | Many release zones or national domains | Medium to high | Future after manifest/chunk schema |
| Python row-oriented processing | Hazard builder | Simple and flexible, but pure-Python loops and dict rows are slow for very large tables | Millions to billions of rows | Medium to high | Future after streaming design |
| JSON diagnostics growth | Case reports and impact-event JSON | JSON is readable but inefficient for large nested records; impact-event JSON can become huge | Full event logs or many case reports | Medium | Future; keep JSON for summaries |
| PNG/HTML report generation | Visualization and hazard reports | Useful for local review but expensive and unnecessary for production batches | Many tiles/scenarios | Low to medium | Future; disable by default for batch production |
| Filesystem cleanup and staging risk | Ignored result directories | Many generated products increase clutter and accidental staging risk | Regular large experiments | Medium | Near-term guardrails |
| Deterministic reduction of maxima/percentiles | Future hazard layers | Merging maxima is easy; percentiles/exceedances need defined sketches or histograms | Scenario uncertainty and production intensity layers | Medium | Future, before percentile products |

## Data-Format Assessment

### Current Formats

| Format | Strengths | Scaling limits | Keep for |
| --- | --- | --- | --- |
| CSV trajectories | Transparent, easy diffing, language-neutral, simple tests | Large, slow to parse/write, row-oriented, many-small-file pattern | Tests, examples, representative debug traces |
| CSV impact events | Auditable, directly usable by calibration scripts | Large for contact-rich cases, many files, repeated headers | Focused impact diagnostics and small calibration fixtures |
| JSON diagnostics | Human-readable structured metadata and metrics | Inefficient for large arrays/events; weak chunk manifest semantics | Case reports and run manifests |
| ESRI ASCII grids | Simple, inspectable, supported by basic GIS tools | Text, no CRS, inefficient, no tiling/compression | Tiny fixtures and local smoke tests |
| GeoJSON deposition points | Easy browser/GIS inspection | Verbose, poor for large point clouds | Small reports and examples |
| PNG/HTML reports | Excellent review layer | Not machine-efficient, not authoritative data | Local QA and publication-style summaries |

### Candidate Formats

| Format | Trajectories | Impact events | Hazard rasters | Metadata/geospatial support | Streaming/chunking | Ecosystem and interoperability | HPC friendliness | Assessment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parquet | Strong for columnar trajectory samples with `trajectory_id`, `sample_index`, and numeric columns | Strong for impact-event tables | Not a raster format | Good table metadata; geospatial via GeoParquet conventions for points/lines | Row groups support chunked reads/writes | Mature in Python; Rust support exists through Arrow/Parquet crates but adds dependencies | Good if written in moderately large row groups | Best next tabular format for trajectories/events when full storage is needed |
| Arrow IPC | Good for fast local interchange | Good for event batches | Not a raster format | Schema-rich but less archival than Parquet | Record batches are streaming-friendly | Strong Python/Rust ecosystem | Good for pipelines; less ideal as long-term artifact | Useful internal interchange or feature-gated streaming bridge |
| Zarr | Poor fit for raw variable-length trajectories | Possible for gridded event cubes, awkward for sparse events | Strong for chunked multidimensional rasters and scenario stacks | Metadata model is flexible, geospatial conventions less universal than GeoTIFF | Excellent chunking | Strong Python/xarray ecosystem; Rust ecosystem less central | Good for object stores and chunked HPC if chunk sizes are chosen carefully | Consider later for scenario cubes or percentile/exceedance stacks, not first |
| GeoTIFF / COG | Not suitable for raw trajectories | Not suitable for event tables | Strong primary raster output | Excellent CRS, nodata, transform, compression, overviews, tiling | COG supports tiled reads; writing can be tile/chunk aware | Very mature GIS ecosystem; Rust/Python via GDAL or raster libraries | Good when tiled and compressed; one file per layer/tile | Primary future exchange format for hazard rasters |
| FlatGeobuf | Not for dense sample tables unless geometrized | Good for spatial point/event vectors | Not raster | CRS and spatial index support | Streamable vector format | Mature enough in GIS; simpler than GeoPackage for web/file streaming | Better than GeoJSON for large vectors | Good candidate for large deposition/impact points if vector output is needed |
| GeoParquet | Good for trajectory points or line summaries with geometry | Good for spatial impact/deposition points | Not raster | Strong emerging geospatial columnar metadata | Row groups and partitioned datasets | Growing GIS/Python support; less universal than GeoTIFF/GeoPackage | Good for analytics workloads | Good for analysis stores; less universal for final map rasters |
| NetCDF / HDF5 | Possible but awkward for variable-length trajectories | Possible but schema-heavy | Good for multidimensional gridded arrays | Mature scientific metadata, GIS interop varies | Chunking supported | Mature, but Rust integration and deployment can be heavier | HDF5 can suffer on parallel filesystems without careful setup | Better for scientific arrays than sparse trajectory/event logs; not first choice |
| SQLite / GeoPackage | Reasonable for moderate trajectory/event tables | Reasonable for events and vectors | GeoPackage can store raster tiles but less common for hazard grids | Good single-file metadata and vector CRS | Transactional, not ideal for massive parallel writes | Very mature; easy inspection | Single-writer constraints limit job arrays | Good for pilot vector packages and manifests; not primary high-throughput store |
| Custom binary | Can be compact and fast | Can be compact and fast | Possible | Must build all metadata and readers | Depends on implementation | Poor interoperability unless wrappers are maintained | Potentially excellent but high maintenance | Avoid unless measured needs exceed standard formats |
| Compressed CSV | Same schema as current, smaller files | Same parse cost after decompression; still row-oriented | Not a raster solution | Sidecars still needed | Streamable gzip/zstd | Very mature | Fewer bytes, same file-count issue | Good low-risk bridge, not final production design |

## Architecture Assessment

### What Works Well Now

- The trajectory kernel is deterministic and mostly isolated from file I/O.
- Randomness is explicit and seeded per trajectory identity.
- Terrain construction can be reused within local ensemble loops.
- Validation, calibration, and hazard post-processing are separate from core
  physics.
- Debug outputs are easy to inspect and compare.
- Consistency checks already encode many documentation and artifact hygiene
  rules.

### What Does Not Scale Yet

- The validation runner stores ensemble runs in memory before writing optional
  trajectory/event directories.
- Full ensemble storage is represented as one CSV per trajectory, not as a
  chunked dataset.
- The hazard builder expects existing files, then rereads them into memory
  rather than receiving samples/events as a stream.
- There is no formal run manifest describing chunk status, file sizes, row
  counts, trajectory ID ranges, config hashes, terrain provenance, CRS, or
  calibration state.
- There is no deterministic partial-reducer contract for merging hazard rasters
  from many jobs.
- Debug/report artifacts and production artifacts are not yet separated by
  schema or layout.
- Output rasters are not aligned to a reference grid and do not carry CRS or
  vertical-datum metadata.

### Production Capabilities Needed

To support Swiss pilot and later Swiss-wide workflows, the architecture should
evolve toward:

- streaming trajectory samples directly into hazard accumulators when full
  trajectories are not required;
- chunked tabular output when full samples/events are required;
- one manifest per run and one manifest per chunk;
- deterministic chunk IDs derived from scenario, release cell, trajectory range,
  and global seed;
- mergeable reducer states for counts, maxima, exceedances, and future
  percentile approximations;
- explicit distinction between audit/debug traces and production reduced layers;
- CRS-aware reference grids and tile extents for all spatial products.

## Production-Oriented Design Options

### Option A: Keep CSV Debug Workflow, Add Streaming Hazard Accumulator

Description: Preserve current CSV/JSON behavior for tests and small cases, but
add a path that feeds trajectory samples and impact events into a reducer during
simulation. The reducer writes partial hazard grids and a manifest without
writing full trajectories by default.

Benefits:

- Smallest conceptual change to current architecture.
- Immediately reduces trajectory/event storage when hazard layers are the goal.
- Preserves current debug outputs and validation fixtures.
- Can be implemented first in Python around existing outputs, then moved closer
  to Rust if needed.

Risks:

- Limited interoperability if partial reducer states remain custom CSV/JSON.
- Does not solve full trajectory archival when full samples are required.
- Percentile/exceedance reducers need careful deterministic merge definitions.

Complexity: medium.

Migration path: add manifest and streaming accumulator while leaving current case
outputs unchanged. Make full ensemble CSV an explicit debug/audit mode.

Swiss-scale compatibility: useful for pilot scaling, insufficient alone for
long-term national archival and GIS exchange.

### Option B: Parquet / GeoParquet Trajectory And Event Store

Description: Store trajectories, impact events, and deposition points in
partitioned Parquet datasets. Partition by scenario, release tile/cell, chunk ID,
and trajectory ID range. Use GeoParquet for spatial point/event products when
geometry is useful.

Benefits:

- Columnar compression reduces storage and parse cost.
- Row groups support selective reads for energy, position, impact speed, etc.
- Better for analytics, calibration, and reprocessing than many CSVs.
- Can retain full-fidelity trajectory/event data when needed.

Risks:

- Adds Arrow/Parquet dependencies or requires a Python conversion layer.
- Schema evolution must be explicit.
- Parquet is not a final raster hazard-map format.
- Some GIS users still expect GeoTIFF/GeoPackage rather than GeoParquet.

Complexity: medium to high.

Migration path: first add a separate converter or optional writer that combines
existing CSVs into Parquet; later write Parquet directly from chunked execution.

Swiss-scale compatibility: strong for trajectory/event analytics and archive,
but must be paired with geospatial raster outputs.

### Option C: Tiled Raster Workflow With GeoTIFF/COG And Optional Zarr

Description: Make hazard production tile-first. Each job accumulates partial
rasters on a reference grid and writes GeoTIFF/COG tiles or mergeable tile
states. Zarr is considered later for multidimensional scenario stacks or
percentile/exceedance cubes.

Benefits:

- Directly addresses Swiss-scale geospatial products.
- Carries CRS, transform, nodata, compression, and tiling metadata.
- Works with standard GIS tools and swisstopo LV95 workflows.
- Supports tile-by-tile production and review.

Risks:

- Requires geospatial dependencies or a careful external preprocessing/export
  boundary.
- Does not store raw trajectories/events.
- Merge semantics for percentile layers require additional design.

Complexity: high if done fully; medium for first GeoTIFF export sidecar.

Migration path: add CRS/reference-grid metadata first, then GeoTIFF export for
current in-memory layers, then chunked/tiled reducers.

Swiss-scale compatibility: essential for final hazard raster products.

### Option D: Hybrid Recommended Architecture

Description: Keep CSV/JSON debug outputs, add standard manifests, stream hazard
reducers for production runs, use Parquet/GeoParquet for optional full
trajectory/event archives, and use GeoTIFF/COG for hazard rasters.

Benefits:

- Matches each data type to an appropriate format.
- Preserves current inspectable research workflow.
- Avoids forcing every run to store full trajectories.
- Provides an incremental path from pilot to national scale.

Risks:

- More moving parts than a single-format solution.
- Requires disciplined schema/version management.
- Needs clear documentation so users do not confuse debug and production
  outputs.

Complexity: medium staged over several releases.

Migration path: manifest, streaming reducers, optional Parquet, GeoTIFF/COG,
then chunked orchestration.

Swiss-scale compatibility: strongest overall path.

## Recommended Roadmap

### Stage 0: Preserve Current Debug Outputs

Keep CSV trajectories, impact CSV/JSON, diagnostics JSON, ASCII grids, GeoJSON,
PNG, and HTML for verification, validation, examples, calibration inspection,
and small reports. They remain the easiest way to audit one trajectory or one
impact. Document them explicitly as debug/development formats.

### Stage 1: Add Run And Chunk Manifests

Define a small JSON or YAML manifest before changing storage formats. It should
record:

- model version and git hash;
- config fingerprint and case ID;
- terrain source, CRS, vertical datum, resolution, extent, tile IDs, checksums,
  and preprocessing method;
- scenario ID, calibration state, and validation status;
- global seed, seed-derivation policy, release IDs, trajectory ID range, and
  chunk ID;
- output files, formats, row counts, raster dimensions, file sizes, checksums,
  and completion status;
- whether each hazard layer came from full trajectories, representative
  trajectories, deposition summaries, or impact-event logs.

This is the lowest-risk foundation for restartability and reproducibility.

### Stage 2: Add Streaming Hazard Accumulation

Add a reducer path that can consume samples/events as they are produced and write
partial layer states. The first reducers should cover:

- trajectory reach counts;
- deposition counts;
- maximum kinetic energy;
- maximum jump height;
- significant impact counts.

The merge contract should be deterministic: counts add, maxima take max, and
metadata records exactly which chunks contributed. Percentiles and exceedances
can be added later with fixed bins or documented sketches.

### Stage 3: Add Columnar Trajectory/Event Outputs

Introduce Parquet or Arrow-backed output as optional tooling, not as a replacement
for debug CSV. A practical first step is a converter that combines existing
ensemble trajectory/event CSV directories into partitioned Parquet and records
the result in the manifest. Direct Rust output can follow after schemas stabilize.

Suggested tables:

- `trajectory_samples`: scenario, release ID, trajectory ID, seed, sample index,
  time, position, velocity, energy, contact state, diagnostics;
- `impact_events`: scenario, release ID, trajectory ID, impact index, time,
  position, normals, velocity stages, energy stages, scarring fields;
- `depositions`: scenario, release ID, trajectory ID, seed, final position,
  runout, final speed, summary diagnostics.

### Stage 4: Add CRS-Aware Raster Outputs

Add GeoTIFF/COG export for hazard layers once reference-grid metadata is present.
Keep CSV/ASCII grid exports for tests and local inspection. For Swiss workflows,
GeoTIFF/COG should be the primary raster exchange format because it carries CRS,
transform, nodata, compression, and tiling conventions understood by GIS tools.

### Stage 5: Add Tiled / Distributed Orchestration

Design job-array execution around chunk manifests:

- partition by scenario, terrain tile, release-zone tile, and trajectory range;
- use deterministic seeds independent of execution order;
- write partial reducer states and optional Parquet row groups;
- resume incomplete chunks by manifest status;
- merge partial rasters deterministically;
- generate final metadata and reports after data products are complete.

MPI, GPU, and distributed frameworks should remain out of scope until this
manifest/chunk/reducer contract exists.

## Immediate Low-Risk Improvements

Priority 1: define a manifest schema and write manifests for verification,
validation, calibration, and hazard outputs. This does not require changing
physics or output defaults and immediately improves reproducibility.

Priority 2: add output-size and file-count summaries plus warnings when
`ensemble_trajectories_dir` or `ensemble_impact_events_dir` would create many
small files. This helps users avoid accidentally turning debug output into a
large-scale storage pattern.

Priority 3: add a single combined ensemble CSV or compressed CSV option as a
bridge format. It would reduce file-count overhead without committing to Parquet
yet. It should be labelled a transitional/debug format.

Priority 4: refactor the hazard builder around streaming row iterators and
incremental accumulators before changing file formats. This reduces peak memory
and prepares deterministic partial reducers.

Priority 5: add CRS/reference-grid metadata sidecars to hazard outputs and case
schemas. This is required before any Swiss pilot product can be interpreted as a
geospatial hazard layer.

## Decision Answers

1. **Where will the current workflow break first?** The first breaking point is
   file-heavy full ensemble output: one CSV per trajectory and one CSV per
   impact-event trajectory, followed by Python rereading all rows into memory.
   At larger map scales, missing manifests and missing tiled reducers become
   equally limiting because failed jobs cannot be resumed or merged
   systematically.

2. **Which outputs are debug/development formats versus scalable formats?** CSV
   trajectories, impact CSV/JSON, diagnostics JSON, ASCII grids, GeoJSON, PNG,
   and HTML are development/debug/review formats. They should remain available
   for small cases. Scalable production formats should be Parquet/GeoParquet for
   optional tabular trajectory/event archives and GeoTIFF/COG for final hazard
   rasters, with manifests tying everything together.

3. **What data formats should be introduced next, and why?** Introduce manifests
   first because they support every later format. Then add streaming reducers.
   For storage formats, Parquet is the best next tabular format for
   trajectories/events, while GeoTIFF/COG is the right next geospatial raster
   output. Zarr is promising for later multidimensional scenario stacks but is
   not the first migration target.

4. **What is the lowest-risk migration path?** Keep existing debug outputs,
   standardize manifests, add streaming hazard accumulation, add optional
   combined/columnar outputs, then add CRS-aware GeoTIFF/COG export and
   chunked orchestration. This path avoids a disruptive rewrite and keeps the
   verified trajectory kernel stable.

5. **Which changes should be implemented first?** Implement manifest schema and
   file-count/size warnings first, then refactor the hazard builder around
   streaming accumulators, then add CRS/reference-grid sidecars. Columnar output
   and GeoTIFF/COG export should follow once the metadata contract is stable.
