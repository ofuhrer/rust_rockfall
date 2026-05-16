# Pilot GIS/QGIS Package

Status: current contract for local pilot QGIS review package contents, raster
semantics, and visual QA acceptance gate. This document defines diagnostic
review expectations only. It does not claim operational map status,
Cloud-Optimized GeoTIFF conformance, production tiling, or risk modelling.

## Scope

The pilot package is a review bundle for local diagnostic inspection of hazard
post-processing outputs. It should make raster alignment, CRS metadata,
vertical-datum provenance, source-zone context, and visual QA traceable enough
for a reviewer to inspect the pilot in QGIS or another GIS tool.

The current executable artifact is a package inventory, not a packaged QGIS
project. `scripts/build_hazard_layers.py --pilot-gis-package --export-geotiff`
or `pilot_gis_package.enabled: true` writes
`<prefix>_pilot_gis_package_manifest.json` with schema version
`pilot_gis_package_manifest_v1`.

## Package Classes

Current and future GIS products must be distinguished explicitly:

- Debug/review GeoTIFF: the current opt-in `--export-geotiff` or
  `hazard_exports.geotiff: true` output. It writes uncompressed float64
  GeoTIFF rasters with manifest metadata, SHA-256 identity, nodata, affine
  transform, EPSG metadata when available, and value parity with the CSV/ESRI
  ASCII review grids. It is a debug/review raster export, not a COG, styled map
  product, or publication package.
- Local QGIS pilot package: a review bundle containing selected rasters,
  CSV/ASCII parity files, manifests, metadata sidecars, source-zone/context
  sidecars where available, and visual QA notes. It is meant to be loadable and
  auditable in QGIS, but it is not required to be a `.qgz`, GeoPackage bundle,
  tiled product, or production delivery package.
- Future production COG/package: deferred work for a verified COG writer,
  tiling/overview/compression policy, standardized styles, optional QGZ or
  GeoPackage bundles, publication manifests, and an approval workflow.
  Standard same-scale roots may remain COG-blocked; `hazard_exports.cog: true`
  and `--export-cog` now describe a valid package-level export path that writes
  to an ignored converted root unless explicitly staged.

The package-level COG path follows the requested export scope, not an
implicit "all layers ever used by the same-scale root" rule. When a COG export
is built from a command that only requests a subset of threshold families, the
audit must report the omitted layers explicitly. The current same-scale COG
proof therefore has two acceptable forms:

- full-scope COG export parity, where the converted root matches the standard
  same-scale layer inventory;
- bounded proof export with a machine-readable `scope_delta` that lists any
  intentionally omitted layers and keeps the standard-root
  `gis_package_ready_cog_blocked` state visible.

## Required Diagnostic Review Contents

A pilot GIS package should include:

- GeoTIFF rasters where `--export-geotiff` or case configuration requests them;
- CSV and ESRI ASCII parity files for each exported raster layer;
- hazard-layer manifests and metadata JSON sidecars;
- source-zone metadata and a vector sidecar where available, such as GeoJSON,
  GeoPackage, or another documented review format;
- terrain metadata sidecar documenting CRS, vertical datum, extent, resolution,
  nodata, source dataset, preprocessing, and provenance;
- visual QA note describing reviewed PNG, HTML, GIS, or QGIS artifacts, or an
  explicit no-artifact manual/GIS inspection statement;
- checksums or manifest identities for generated rasters and provenance files
  where available.

Private raw terrain crops, raw swisstopo products, and generated private outputs
remain ignored unless a future task explicitly adds tiny synthetic fixtures.

The package manifest records:

- GeoTIFF raster outputs with checksums and non-COG/non-annual semantics;
- CSV and ESRI ASCII parity outputs for the same generated layers;
- hazard metadata and any map-package manifest outputs already generated;
- optional source-zone context sidecars from
  `pilot_gis_package.source_zone_context_paths`;
- terrain metadata sidecar identity where `terrain.metadata_path` is available;
- visual QA status, note, and reviewed artifact labels;
- explicit unsupported-product labels for physical probability, annual
  intensity-frequency, return-period, risk-map, and operational hazard-map
  claims.

## CRS And Geodata Requirements

Swiss real-site pilots must record:

- horizontal CRS: LV95 / EPSG:2056;
- vertical datum: LN02;
- affine transform or geotransform;
- cell size;
- raster extent;
- nodata value;
- raster origin convention, including lower-left grid origin where inputs use
  ESRI ASCII headers;
- row order and north-up interpretation;
- hazard-cell alignment with the terrain grid;
- source DEM, source-zone, and processing provenance;
- output checksums or manifest identities.

The vertical datum may be carried in manifests and sidecars rather than fully
encoded in lightweight GeoTIFF tags. Review notes must make this explicit so the
GeoTIFF is not treated as self-sufficient vertical-datum evidence.

Current GeoTIFF transform semantics use north-up raster georeferencing. The
manifest `affine_transform` is ordered as `[pixel_width, 0, x_min, 0,
-pixel_height, y_max]`. GeoTIFF pixel scale records positive x/y cell sizes,
while the tiepoint anchors the upper-left raster corner. ESRI ASCII parity files
continue to expose `xllcorner`, `yllcorner`, `cellsize`, `ncols`, `nrows`, and
`NODATA_value`; values are written in north-to-south row order for GIS-style
inspection. Grid alignment means the GeoTIFF, ESRI ASCII grid, CSV cell
centres, manifest extent, and source terrain metadata describe the same cell
edges and dimensions. Nodata is the manifest nodata value and is distinct from a
valid zero cell.

## Explicit Grid Requirement For Real Pilots

Real pilot hazard-layer builds must use explicit DEM-derived grid arguments
instead of relying only on `--cell-size` convenience grid construction:

```text
--grid-xmin
--grid-ymin
--grid-ncols
--grid-nrows
--grid-cell-size
```

The explicit grid should match the private DEM crop extent, dimensions, cell
size, and alignment. Any resampling or intentional mismatch must be recorded in
the manifest and visual QA note.

## Raster Layer Semantics For Review

Layer interpretation must follow `docs/hazard_map_semantics.md`. The pilot GIS
package should make each raster's source table, units, denominator, and
probability mode visible in the manifest or review note.

Review semantics:

- `reach_probability`: fraction of supplied trajectories that touch each valid
  cell, counted at most once per trajectory, with denominator equal to the
  supplied trajectory count. Source input: trajectory CSVs. For current
  unweighted diagnostic maps this is a reach fraction, not annual probability.
- `deposition_density`: dimensionless fraction of supplied deposition rows or
  points in each valid cell, derived from the ensemble deposition CSV. It is not
  area-normalized points per square metre unless a future product explicitly
  adds that unit and denominator.
- `max_kinetic_energy`: maximum sampled kinetic energy in joules (`J`) from
  trajectory CSV rows with `kinetic_j` that fall in each valid cell.
- `max_jump_height`: maximum sampled jump height in metres (`m`) above the
  referenced terrain surface for each valid cell, derived from trajectory CSVs.
- `significant_impact_density`: event-location distribution over supplied
  impact-event CSV or Parquet records that meet the significant-impact
  threshold. It is not a structure-impact probability or risk layer.
- threshold exceedance layers: trajectory-level or weighted conditional
  fractions from trajectory CSVs exceeding configured kinetic-energy (`J`),
  jump-height (`m`), or velocity (`m/s`) thresholds. Thresholds must be listed
  in the manifest.
- probability standard-error or convergence layers, where present: Monte Carlo
  convergence diagnostics derived from trajectory CSVs for the supplied sample
  set. They are not validation uncertainty, physical-probability uncertainty,
  annual-frequency uncertainty, or risk.
- weighted conditional layers: layers using metadata sampling weights from
  `trajectory_metadata_table_v1` and the documented filter denominator. They
  remain conditional on the supplied source-zone, scenario, block, and metadata
  filters and must not be described as physical or annual probabilities.

Nodata means outside the valid review grid, missing terrain support, or
explicitly masked output. Valid zero means the cell is inside the review grid
and the layer value is zero under the supplied inputs. Reviewers must not treat
nodata and valid zero as equivalent.

Annualized layers, return-period labels, operational hazard-map labels, exposure
or vulnerability overlays, expected-loss language, and risk maps are excluded
from the local pilot GIS package unless a future phase adds the required
source-frequency, validation, exposure/vulnerability, and approval contracts.

## QGIS Visual QA And Acceptance Gate

M010 defines the visual QA checklist and acceptance gate for a local diagnostic
review package only. It does not create a QGIS project file, COG product, tiled
delivery package, production map, or operational approval.

Visual QA should load or inspect, where available:

- DEM or hillshade background;
- release-zone sidecar;
- observed deposition points where share-safe;
- generated hazard rasters and parity CSV/ASCII outputs;
- manifests and metadata sidecars needed to verify CRS, vertical datum, grid,
  nodata, source-zone, and provenance claims.

Review checklist:

- confirm project CRS and raster CRS are LV95 / EPSG:2056;
- confirm LN02 vertical datum is recorded in terrain metadata, manifests, or
  sidecars, even if not fully encoded in lightweight GeoTIFF tags;
- confirm hazard rasters align with the DEM grid, release-zone sidecar, and
  deposition context;
- confirm raster origin, row order, north-up interpretation, cell size, extent,
  and nodata value match the manifests;
- inspect nodata versus valid zero styling so masked cells are not confused with
  zero-valued hazard cells;
- confirm layer names, legends, and notes match the raster semantics above and
  `docs/hazard_map_semantics.md`;
- confirm styling and labels do not imply annual frequency, return period,
  risk, official status, or operational validation;
- record reviewed artifacts, such as PNG, HTML, GIS project screenshots, QGIS
  layer lists, raster metadata dialogs, or explicit manual/GIS inspection notes.

Use these QA statuses:

- `pass`: required artifacts and metadata are present and visually consistent;
- `no-go`: required raster, manifest, CRS/grid, semantic-label, or visual QA
  evidence is missing or contradictory;
- `inconclusive`: evidence exists but does not support a confident spatial or
  semantic interpretation;
- `not-run`: only for explicitly optional artifacts, such as plots, GeoTIFFs, or
  GIS project files that were not requested.

The local diagnostic package is accepted only when core CRS/grid metadata,
semantic labels, nodata handling, provenance, and required visual QA evidence
are `pass`. Optional or non-core artifacts may be `inconclusive` without
blocking acceptance only when the report explains why they do not affect the
stated diagnostic question. Acceptance does not imply QGZ packaging, COG
compliance, production readiness, operational validation, or risk-map validity.

## Executable Checks

Current executable coverage is intentionally small but checks the core raster
contract:

- `scripts/validate_pilot_gis_package.py` validates a
  `pilot_gis_package_manifest_v1` inventory. With `--require-real-site` and
  `--require-existing-files`, it checks local generated file checksums,
  GeoTIFF/CSV/ESRI ASCII parity inventory, TIFF-family signatures for local
  GeoTIFF artifacts, EPSG:2056/LN02/nodata/grid metadata in the hazard
  manifest, source-zone sidecar references through either package context
  artifacts or the map-package manifest, and unsupported
  annual/return-period/risk/operational claim boundaries. The TIFF signature
  check catches placeholder or wrong-file artifacts; it is not full raster
  readability or QGIS QA.
- `scripts/validate_pilot_gis_visual_qa.py` validates a
  `pilot_gis_visual_qa_record_v1` checklist for the selected manual GIS/QGIS
  review step. It requires the core CRS, vertical-datum, raster-alignment,
  nodata-styling, source-zone-overlay, conditional-label, and unsupported-claim
  checks to be classified as `pass`, `no-go`, or `inconclusive`; rejects
  selected-pilot `not-run` visual-QA records; and only allows an overall `pass`
  when QGIS availability plus reviewed visual artifacts are recorded. With
  `--require-existing-package`, it also validates the referenced local package
  manifest and generated files through `scripts/validate_pilot_gis_package.py`.
- `tests/test_hazard_layers.py::HazardLayerTests.test_geotiff_export_preserves_values_grid_and_crs_metadata`
  builds a tiny GeoTIFF fixture, verifies GeoTIFF values match the CSV grid, and
  checks pixel scale, tiepoint, nodata, EPSG metadata, manifest affine
  transform, vertical datum, non-COG status, diagnostic non-annualized
  semantics, and SHA-256 checksum recording.
- `tests/test_hazard_layers.py` coverage for the package-level export path now
  distinguishes standard COG-blocked roots from ignored converted-package
  exports and now reports layer parity versus intentional scope reduction,
  rather than treating `--export-cog` as universally deferred.
- `tests/test_hazard_layers.py::HazardLayerTests.test_pilot_gis_package_manifest_records_review_artifacts_and_boundaries`
  verifies the pilot package manifest records GeoTIFF outputs, CSV/ASCII parity
  files, source-zone and terrain metadata sidecars, visual QA status, and
  unsupported annual, return-period, risk, and operational claim boundaries.
- `tests/test_hazard_layers.py::HazardLayerTests.test_pilot_gis_package_requires_geotiff_export`
  verifies package manifest generation is gated on explicit GeoTIFF export.
- `tests/test_pilot_gis_package_validator.py` covers the standalone package
  validator success path and rejection of missing ASCII parity, annualized
  GeoTIFF claims, missing unsupported-claim boundaries, checksum mismatch, and
  non-TIFF placeholder artifacts when local files are required.
- `tests/test_pilot_gis_visual_qa.py` covers the visual-QA review-record
  validator success path for an explicit `inconclusive` selected-pilot record
  and rejection of pass records without QGIS evidence, missing required checks,
  selected-pilot `not-run` status, and unqualified misleading current-product
  claims.

These checks prove value/metadata parity for the tiny fixture path and enforce
the current package boundary. Standard same-scale roots can remain COG-blocked
while the package-level export path writes a separate ignored converted root.
The standalone validator can also check local real-pilot generated package
inventories when ignored outputs exist, and the visual-QA validator can record
an explicit `pass`, `no-go`, or `inconclusive` manual-review classification.
These checks do not themselves prove QGIS styling quality, QGZ packaging,
Cloud-Optimized GeoTIFF conformance, production tiling, Swiss pilot scientific
validity, operational approval, or risk-map validity.

## Deferred Production Work

The local pilot package does not yet define:

- QGIS project (`.qgz`) packaging;
- GeoPackage delivery bundles;
- standardized QGIS styles or symbology;
- verified Cloud-Optimized GeoTIFF output;
- tiled raster products;
- production-scale package manifests;
- publication or operational approval workflow.

The current `--export-cog` path is package-level and ignored by default. It is
valid for generated proof/export roots, but those converted roots remain
generated and ignored unless a future task explicitly stages them. The same
command-plan path may be used for full-scope parity proof or a bounded proof
with explicit scope delta metadata.
