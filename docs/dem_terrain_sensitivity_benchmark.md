# DEM And Terrain-Representation Sensitivity Benchmark

Status: M014 documentation-only design scaffold. This document defines a future
dry-runnable or real-site benchmark plan; it does not run private data, generate
outputs, tune parameters, select physics, or claim operational validation.

## Purpose

The benchmark should distinguish DEM and terrain-representation effects from
physics or parameter tuning. It should answer whether runout, deposition, and
hazard-layer patterns change because of terrain source, resolution, alignment,
interpolation, nodata, or terrain-class representation while the simulator,
source-zone policy, block/scenario metadata, and seeds remain fixed.

## Compared Terrain Representations

Candidate representations should be predeclared before execution:

| Variant | Input | Purpose | Notes |
| --- | --- | --- | --- |
| Synthetic/control baseline | Analytic terrain or tiny checked-in DEM fixture | Dry-runnable control for command, manifest, and reducer behavior | Must be public and fixture-sized. |
| Public Tschamut proxy | Current public-derived Tschamut proxy terrain | Compare current proxy behavior against alternative representations | No private data; remains diagnostic. |
| Native private swissALTI3D | Private Tschamut/swissALTI3D crop when available | Test real bare-earth terrain representation | Must remain outside git and use LV95/LN02 or recorded transforms. |
| Coarsened resolutions | Same source terrain resampled to declared cell sizes | Isolate resolution effects | Use same extent and source-zone/release cells where possible. |
| Interpolation/resampling methods | Nearest, bilinear, cubic, mean/aggregate, or another predeclared method | Isolate interpolation or aggregation effects | Method must be recorded before execution. |
| Smoothing/no-smoothing | Raw versus declared smoothing kernel/window | Isolate smoothing or micro-topography effects | Smoothing is preprocessing, not tuning to results. |
| Cliff/nodata variants | Declared nodata masks, clipped extents, or cliff-edge handling | Isolate edge and nodata handling effects | Interpolation across nodata is forbidden unless declared separately. |
| Terrain-class/raster alignment | Optional aligned categorical raster variant | Test representation/alignment of class rasters | Active physics parameters and class-to-parameter mapping stay fixed. |

Private swissALTI3D crops, raw swisstopo tiles, and generated private outputs
must remain ignored. Public/proxy and synthetic variants should stay clearly
separated from private real-site evidence.

## Invariants

Each comparison must keep these fixed unless the report explicitly declares a
separate experiment:

- source-zone polygon and deterministic release cells;
- block/scenario metadata labels and active simulated block parameters;
- random seeds, trajectory ids, and release-cell ids;
- simulation configuration and contact model;
- hazard grid, thresholds, and probability/weighting semantics;
- output selection and plot mode where possible;
- no restitution, friction, roughness, scarring, terrain-class, source-zone, or
  release-condition tuning after inspecting results.

Terrain-class variants may vary only as representation/alignment inputs while
the active physics parameters and class-to-parameter mapping remain fixed. If a
class definition or parameter mapping changes, that is a separate
physics/material experiment, not a DEM/terrain-representation sensitivity run.

## Required Metadata

Every terrain representation should record:

- horizontal CRS/EPSG and vertical datum. Private Tschamut/swissALTI3D variants
  require LV95 / EPSG:2056 and LN02, or a recorded transform if source data are
  not already in that frame;
- extent, cell size, dimensions, nodata value, and row order/origin convention;
- affine/geotransform or ESRI ASCII header interpretation. For ESRI ASCII,
  verify `xllcorner`/`yllcorner` as the lower-left outer cell corner, first data
  row as the north/top row, and cell-center sampling;
- resampling or coarsening method, if any;
- source dataset, source path or tile ids where share-safe, license, and
  provenance notes;
- processed checksums where feasible, or a recorded reason if absent;
- terrain-class raster alignment, class metadata, and nodata policy when used;
- private-data exclusion and redaction notes for shareable reports.

swisstopo inputs are operational geodata for terrain representation, not
validation evidence by themselves.

Allowed resampling/coarsening behavior:

- record the method and parameters before running;
- propagate nodata masks through derived terrain products;
- do not interpolate across nodata unless it is explicitly documented as a
  separate preprocessing experiment;
- mark release cells or hazard cells touching nodata as no-go, or explicitly
  exclude/mask them before interpretation.

## Metrics And Observations

Future benchmark reports should compare:

- runout summaries: mean, median, extrema, selected quantiles, and runout error
  against available observations where appropriate;
- deposition summaries: centroid, spread, overlap, nearest-neighbour distance,
  and deposition-density footprint;
- hazard-layer map differences: reach, deposition, maximum kinetic energy,
  maximum jump height, threshold exceedance layers, and significant-impact
  density where impact events exist;
- per-layer deltas and spatial disagreement between terrain representations;
- visual QA: DEM/hillshade, source-zone, release-cell, observed-deposition, and
  hazard-raster alignment review;
- timing and output-volume context: phase timings, row counts, file counts,
  bytes, plot mode, release count, ensemble size, and input/output format.

If observations are included, they are diagnostic context only. They do not
create validation pass/fail evidence, calibrated skill, or operational
acceptance unless a separate validation milestone defines that role and
holdout/tuning boundary.

## Acceptance And Gates

The benchmark can be interpreted only when these gates pass:

- deterministic rerun parity for the same terrain representation and seed;
- manifest completeness for terrain, source-zone, scenario, simulation, hazard
  grid, thresholds, output counts, timings, and checksums/provenance;
- CRS, vertical-datum, grid-alignment, nodata, row-order, and hazard-cell
  alignment checks;
- visual QA shows no unresolved crop-edge, nodata, release-zone, or alignment
  artifact dominating the result;
- no operational validation, annual-frequency, physical-probability, or risk
  claims;
- no physics selection or default recommendation unless the sensitivity
  classification is stable across representations and explicitly reviewed in a
  later milestone.

No-go outcomes should lead to data/provenance/alignment fixes, a documented
rerun, or deferral, not parameter tuning.

Gate statuses:

- `pass`: required evidence is complete and interpretable;
- `no-go`: required data, metadata, alignment, manifest, or QA evidence is
  missing, contradictory, or affected by forbidden tuning;
- `inconclusive`: evidence is present but insufficient to classify sensitivity;
- `not-run`: only for optional variants that were not requested.

## Minimum Dry-Run Or Real-Site Recipe

Expected inputs:

- baseline case or case template;
- terrain representation inventory and metadata sidecars;
- fixed source-zone/release-cell table;
- fixed block/scenario metadata;
- fixed random seed and simulation configuration;
- fixed hazard grid and threshold configuration;
- optional observation tables for diagnostic context only.

Ignored output root:

```text
validation/results/dem_terrain_sensitivity/
hazard/results/dem_terrain_sensitivity/
```

Command/report placeholders:

```text
prepare terrain variants: <future command or documented manual preprocessing>
run validation cases:    <future cargo run -- validate --case ...>
build hazard layers:     <future python3 scripts/build_hazard_layers.py ...>
write report:            <future M015/M016 report path>
```

Paired output modes:

- no-plot batch diagnostic outputs for comparable timings and file counts;
- selected plot/GIS QA outputs for representative variants only;
- CSV/ASCII parity outputs for every hazard raster;
- GeoTIFF outputs where explicitly requested and metadata-complete.

Minimum report gate table:

| Gate | Status | Required note |
| --- | --- | --- |
| Deterministic rerun parity | `pass` / `no-go` / `inconclusive` | Same inputs and seed reproduce manifests and key summaries. |
| Manifest completeness | `pass` / `no-go` / `inconclusive` | Terrain, scenario, output, timing, checksum, and provenance fields reviewed. |
| CRS/grid/nodata alignment | `pass` / `no-go` / `inconclusive` | EPSG/datum, transform, row order, nodata, and hazard-cell alignment reviewed. |
| Variant invariants | `pass` / `no-go` / `inconclusive` | Source, scenario, seed, physics, hazard grid, thresholds, and outputs stayed fixed. |
| Visual QA | `pass` / `no-go` / `inconclusive` | Artifacts or manual/GIS inspection notes reviewed. |
| Interpretation boundary | `pass` / `no-go` | No tuning, operational validation, annual-frequency, physical-probability, or risk claim. |

## Future Report Sections

M015/M016 can turn this scaffold into a report or fixture plan. Expected report
sections:

- terrain representation inventory;
- invariant configuration table;
- command log or dry-run plan;
- manifest and provenance summary;
- alignment and visual QA findings;
- runout/deposition metric comparison;
- hazard-layer difference summary;
- timing and output-volume context;
- sensitivity classification and uncertainty notes;
- gate table and no-go/inconclusive reasons;
- next-step decision and limitations.
