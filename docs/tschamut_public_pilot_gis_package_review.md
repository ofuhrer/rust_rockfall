# Tschamut Public Pilot GIS Package Review

Status: share-safe diagnostic review record for the local Tschamut public
conditional pilot GIS package. This review records automated package-manifest
and file-integrity checks only. It is not a QGIS project, production COG
package, operational hazard map, physical-probability product, annual-frequency
product, return-period product, or risk map.

This is local-only evidence. The generated rasters, manifests, and parity files
listed below are ignored outputs and are not present in a clean checkout. The
selected pilot run-freeze has now been reconciled against regenerated local
artifacts and records the package manifest checksum, but reproduction still
requires the documented public Tschamut preparation and ignored local output
paths.

## Scope

- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_conditional_gate_v1`
- Package manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json`
- Hazard manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`
- Map package manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json`
- Terrain metadata:
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`

All listed artifacts are ignored local outputs except for this review record.
No raw swisstopo data, processed DEM crop, GeoTIFF, CSV, ESRI ASCII grid,
conditional curve table, or generated package manifest is committed. The
authoritative run-freeze now classifies the small local gate as
`gate_run_completed` with an `inconclusive` report classification because
manual QGIS visual QA and target-scale convergence remain incomplete.

## Automated Package QA

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_pilot_gis_package.py \
  hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json \
  --require-real-site \
  --require-existing-files \
  --format json
```

Result: pass.

Observed summary:

- GeoTIFF rasters: 16
- CSV parity grids: 16
- ESRI ASCII parity grids: 16
- Grid: explicit, 300 by 304 cells, 2 m cell size,
  `xmin=2696376.0`, `ymin=1167384.0`
- CRS/datum: EPSG:2056 / LV95, LN02
- Nodata: `-9999.0`
- Source-zone context: referenced through the map-package
  `source_zone_metadata_path`
- Visual QA status in package manifest: `not-run`
- Operational status: `research_diagnostic`
- Package manifest SHA-256 in the reconciled run-freeze:
  `ab9bc43b1d4ae8a61724f3f951e1127064d1b841b1d74b391516016efd0b9f92`

The validator checked:

- package schema and diagnostic raster contract;
- GeoTIFF inventory and `cloud_optimized: false` / non-annualized flags;
- CSV and ESRI ASCII parity inventory for every GeoTIFF layer;
- recorded SHA-256 and byte counts against local ignored files;
- hazard-manifest raster CRS, affine transform, grid size, nodata, and
  EPSG:2056/LN02 metadata;
- source-zone metadata reference via the map-package manifest;
- unsupported-product labels for physical probability, annual
  intensity-frequency, return period, risk-map, and operational hazard-map
  claims.

## Visual QA Result

Manual QGIS inspection was not run. The package therefore has this gate status:

- Automated manifest/file QA: `pass`
- Manual QGIS visual QA: `not-run`
- Overall local diagnostic package acceptance: `inconclusive`

The package is suitable for the next manual GIS review step because the rasters,
parity grids, manifests, CRS/datum metadata, nodata metadata, and source-zone
sidecar references are present and internally consistent at the manifest level.
It is not yet accepted as a visually reviewed QGIS package.

## Claim Boundary

Allowed current interpretation:

- local diagnostic GeoTIFF review rasters;
- CSV/ESRI ASCII parity grids for the same generated layers;
- conditional intensity-exceedance and sampling-weighted conditional products;
- research diagnostic source-zone and scenario conditioning.

Unsupported current interpretation:

- annual frequency;
- return period;
- physical probability;
- exposure, vulnerability, consequence, expected loss, or risk;
- operational or validated hazard-map status;
- Cloud-Optimized GeoTIFF or production tiled package status.

## Next GIS Action

The next reviewer should load the ignored local package in QGIS with the
terrain DEM or hillshade, source-zone sidecar, and selected rasters; verify
spatial alignment, nodata versus valid zero styling, layer labels, and
conditional-product wording; then update the package visual QA status only if
the manual GIS findings support it.
