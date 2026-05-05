# Hazard Workflow Scale Review

## Purpose

This review stress-tests the first hazard-layer workflow in
`scripts/build_hazard_layers.py` and identifies the next changes needed before
Alpine or Switzerland-wide use. The work is restricted to post-processing and
orchestration. No simulation physics, validation semantics, or calibration
semantics were changed.

## Stress-Test Setup

All timings were measured locally on May 5, 2026 using `/usr/bin/time -lp`.
Generated outputs were written under ignored `hazard/results/` directories.

### Tschamut 10x Ensemble

The baseline Tschamut comparison was copied to a temporary ignored case with
`random.ensemble_size = 60`, which is 10 times the checked-in baseline
`ensemble_size = 6`. With 10 release points, this produced 600 simulated final
deposition points.

Validation run:

- command: `cargo run -- validate --case hazard/results/stress_inputs/tschamut_baseline_10x.yaml`
- elapsed time: `8.69 s`
- maximum resident set size: about `213 MB`
- simulated trajectories: `600`
- observed mean runout: `102.84 m`
- simulated mean runout: `71.78 m`
- runout distance error: `31.06 m`

Hazard-layer build:

- command: `python3 scripts/build_hazard_layers.py --case hazard/results/stress_inputs/tschamut_baseline_10x.yaml --output-dir hazard/results/stress_tschamut_baseline_10x/hazard_layers --cell-size 5`
- elapsed time: `1.34 s`
- maximum resident set size: about `122 MB`
- grid: `11 x 16` cells at `5 m`
- deposition points: `600`

Layer summaries:

- `reach_probability`: 20 nonzero cells, sum `20.0`; this is a representative
  trajectory path mask because only one full trajectory CSV was available.
- `deposition_density`: 6 nonzero cells, sum approximately `1.0`; this is the
  only current layer that reflects the 600-member ensemble.
- `max_kinetic_energy`: 20 valid cells, maximum `5618.59 J`; representative
  trajectory only.
- `max_jump_height`: 20 valid cells, maximum `1.01 m`; representative
  trajectory only.

Observation: the current rasterizer handled this small 10x ensemble easily. At
the time of this stress test, the dominant limitation was not runtime at this
scale; it was that validation emitted ensemble deposition points but only one
representative full trajectory by default. The follow-up implementation adds
opt-in `outputs.ensemble_trajectories_dir` and
`outputs.ensemble_impact_events_dir` for small-to-medium full-ensemble hazard
layers.

### Repeated-Trajectory Rasterization Stress

To stress trajectory CSV I/O without changing the simulator, the same synthetic
inclined-plane trajectory CSV was supplied 50 times to the hazard builder.

- command: repeated `--trajectory verification/results/synthetic_inclined_plane_bounce_runout.csv` 50 times
- elapsed time: `0.81 s`
- maximum resident set size: about `79 MB`
- trajectory CSV count: `50`
- trajectory samples: `40,050`
- grid: `7 x 2` cells at `1 m`

Observation: repeated trajectory loading is fast for tens of thousands of
samples. It is still implemented as in-memory CSV loading, so the first serious
bottleneck for large realistic ensembles will be memory and repeated text-CSV
parsing rather than raster math.

## DEM and Terrain Robustness

### Strict ESRI ASCII DEM Fixture

- case: `verification/synthetic/ascii_dem_fixture.yaml`
- hazard command cell size: `0.5 m`
- elapsed time: `0.38 s`
- maximum resident set size: about `23 MB`
- grid: `3 x 2`
- max jump height: `1.0 m`

The strict DEM fixture produced finite reach, energy, and jump-height layers.
No grid-alignment failures were observed.

### Clamped ESRI ASCII DEM Fixture

- case: `verification/synthetic/clamped_dem_terrain_variation.yaml`
- hazard command cell size: `0.5 m`
- elapsed time: `0.37 s`
- maximum resident set size: about `24 MB`
- grid: `4 x 3`
- max jump height: `0.30 m`

The clamped DEM fixture produced finite layers even though the trajectory starts
outside the DEM x-min edge. This is useful for smoke testing explicit edge
policy, but it is not a production GIS boundary treatment.

### Tschamut Proxy DEM

The Tschamut stress case used the current IDW residual DEM proxy through
`ascii_dem_clamped`. The hazard builder successfully evaluated jump height
against this DEM and produced finite layers. The report and documentation keep
the proxy terrain clearly labelled as a proxy, not an official field DEM.

## Robustness Improvements Added

The hazard builder now performs lightweight hardening:

- drops rows with non-finite coordinates and records a warning;
- ignores non-finite numeric values in layer calculations;
- writes layer summary statistics into metadata;
- warns when probability-like layers contain negative values or values above
  one beyond floating-point tolerance;
- includes a "How to Read Hazard Layers" section in the HTML report;
- explains every raster layer directly in the report.

These changes are post-processing only and do not affect simulation behavior.

## Numerical and Normalization Checks

The stress outputs were inspected for NaNs, infinities, and normalization
problems through metadata summaries:

- `deposition_density` summed to approximately `1.0` for the 600-point Tschamut
  ensemble.
- `reach_probability` values stayed within `[0, 1]` up to floating-point
  accumulation noise.
- maximum-value rasters used `NODATA` for cells without samples.
- DEM-derived jump-height rasters remained finite for the tested strict,
  clamped, and proxy DEM cases.

Grid resolution changes currently affect only post-processing aggregation. The
workflow does not yet support grid alignment to an external reference raster.

## Current Bottlenecks

What breaks or degrades first:

1. **Full ensemble trajectory/impact output is now opt-in but still file-heavy.**
   `outputs.ensemble_trajectories_dir` enables meaningful ensemble reach,
   energy, and jump-height rasters, and `outputs.ensemble_impact_events_dir`
   enables ensemble significant-impact density for small-to-medium cases. Both
   write one CSV per trajectory and are not Swiss-scale storage solutions.
2. **Text CSV I/O.** CSV is transparent and adequate for small cases, but large
   ensembles will spend time parsing text and writing large repeated grids.
3. **In-memory rasterization.** The current script loads all supplied CSV rows
   and all raster layers into memory. This is fine for small tests but not for
   Swiss-wide tiles or millions of trajectories.
4. **No streaming or tiling.** There is no tile-by-tile accumulator, no chunked
   partial reduction, and no resumable merge operation.
5. **No CRS or georeferencing metadata.** ASCII grids carry origin and cell size
   but not projection, vertical datum, or Swiss LV95 metadata.

## Geospatial Readiness Gaps

Swiss-scale geospatial operation needs fields and metadata that are not yet
implemented:

- coordinate reference system, likely EPSG:2056 / CH1903+ LV95 for Swiss
  planar workflows;
- vertical datum and elevation-source metadata;
- source DEM resolution, nodata policy, resampling method, and terrain-class
  provenance;
- release-zone geometry and source-cell identifiers;
- output raster alignment to a reference grid;
- model version, config hash, calibration status, seed policy, and ensemble
  identifiers attached to every product;
- export to GeoTIFF or Cloud-Optimized GeoTIFF for rasters and GeoPackage or
  GeoJSON for vector summaries.

## swisstopo Terrain and Context Inputs

Future Swiss pilot domains should use swisstopo operational input geodata, not
experimental validation terrain proxies. The current strategy is:

- **swissALTI3D** is the mandatory bare-earth terrain foundation for pilot
  hazard domains. It is delivered in LV95/LN02 one-kilometre tiles and can be
  obtained as COG GeoTIFF or text formats.
- **swissSURFACE3D Raster** and **swissSURFACE3D** are optional surface,
  vegetation, building, and obstacle context layers. They are not replacements
  for the bare-earth terrain used by the current trajectory kernel.
- **swissTLM3D** provides roads, tracks, hydrography, constructed features, land
  cover, and other vector context for release masks, exclusions, infrastructure
  overlays, and QA.
- **GeoCover**, the **Geological Atlas 1:25,000**, and **GeoMaps 500** provide
  geological/material context at different scales. Any translation from geology
  to model parameters must be explicit and must not become hidden calibration.
- **SWISSIMAGE** is a visual QA layer for terrain preprocessing, release zones,
  hillshade comparison, and map review.

A metadata-only tile fixture is checked in at
`data/processed/swisstopo/sample_swissalti3d_tile_metadata.yaml`. It documents
the fields future ingestion should validate: EPSG:2056 / LV95 coordinates,
LN02 heights, resolution, extent, nodata policy, checksums, preprocessing
method, license/terms reference, and provenance. It is not a real terrain tile.

## Storage Format Assessment

Current formats:

- **CSV grid**: excellent for inspection, tests, and small cases; too verbose for
  large rasters.
- **ESRI ASCII grid**: simple and widely readable; lacks CRS metadata and is
  inefficient for large tiled products.
- **GeoJSON deposition points**: useful for small point clouds; too large for
  dense national-scale ensembles.

Candidate future formats:

- **GeoTIFF / Cloud-Optimized GeoTIFF**: primary candidate for hazard rasters
  because CRS, nodata, compression, and tiling are standard.
- **GeoPackage**: useful for vector release zones, deposits, contours, and
  metadata tables.
- **Parquet**: useful for large tabular trajectory/event summaries and fast
  columnar filtering.
- **Zarr**: possible future format for chunked multidimensional scenario
  products, but likely premature for the next step.

## Swiss-Scale Requirements

Minimum requirements before Switzerland-wide mapping:

- swisstopo-aware terrain ingestion for cropped swissALTI3D pilot domains;
- deterministic release-zone generation from polygons or raster masks;
- full ensemble trajectory/event output, preferably chunked; the current
  `ensemble_trajectories_dir` and `ensemble_impact_events_dir` are the first
  inspectable versions of this;
- tile-based raster accumulators that can merge partial products;
- explicit CRS and reference-grid alignment;
- DEM tiling and edge-overlap policy;
- job-array or HPC orchestration with order-independent seeds;
- storage policy for raw trajectories versus reduced summaries;
- calibration/validation metadata embedded in every layer;
- clear separation between hazard layers and downstream risk workflows.

The first pilot workflow is defined in `docs/swisstopo_data_strategy.md`: select
a small slope or valley, obtain only the needed swissALTI3D tiles, crop with
documented provenance, generate release zones from slope plus geology context,
run deterministic ensembles, and export hazard layers with CRS/provenance
metadata. Full Swiss-scale download and processing remain deliberately out of
scope.

## Prioritized Next Steps

1. Refactor the hazard builder into a streaming/tiled accumulator that can merge
   partial rasters.
2. Evolve `ensemble_trajectories_dir` and `ensemble_impact_events_dir` toward
   chunked full-ensemble trajectory and event outputs while preserving
   deterministic trajectory IDs.
3. Add CRS/reference-grid metadata fields to hazard-layer metadata and case
   schemas without requiring full GIS dependencies.
4. Add GeoTIFF export behind an optional dependency or separate script.
5. Define a minimal release-zone schema and deterministic source-cell sampling
   policy.

The smallest high-impact next change after opt-in ensemble trajectory and impact
output is a streaming reducer. Without streaming and chunked storage, the new
full ensemble layers are scientifically meaningful for small-to-medium cases but
not yet suitable for Swiss-wide production runs.
