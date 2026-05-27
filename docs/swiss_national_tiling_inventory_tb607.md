# Swiss National Tiling Inventory TB-607

Date: 2026-05-26

Status: share-safe national public-geodata inventory. No download or staging was
performed.

Machine-readable inventory:
`docs/swiss_national_tiling_inventory_tb607.json`

## Purpose

Swiss-wide feasibility needs a concrete inventory before compute planning is
meaningful. This note decomposes the `data_ready` blocker into terrain,
visual/vector context, and obstacle/geology context classes with deterministic
tile IDs, expected cache paths, version/checksum fields, and byte estimates.

## National Tiling Grid

- CRS: `EPSG:2056`
- Vertical datum for terrain/surface products: `LN02`
- Tile size: `1 km x 1 km`
- Tile ID policy: `lv95_1km_{easting_km}_{northing_km}`
- Sample Tschamut tile ID: `lv95_1km_2696_1167`
- National 1 km tile-count estimate: `43,500`

This matches the current swisstopo strategy note that swissALTI3D uses about
`43,500` one-kilometre tiles nationally.

## Product Inventory

| Product ID | Role | Tile count | Resolution | Estimated national raw bytes | Cache status |
| --- | --- | ---: | ---: | ---: | --- |
| `swissalti3d_2m` | mandatory terrain foundation | `43,500` | `2 m` | `43.5 GB` float32 raw | missing |
| `swissalti3d_0_5m` | optional high-resolution terrain | `43,500` | `0.5 m` | `696 GB` float32 raw | missing |
| `swissimage_10cm_or_25cm` | visual QA and source-zone review context | `42,700` | `10 cm / 25 cm` | `12.81 TB / 2.05 TB` RGB raw | missing |
| `swisssurface3d_raster_0_5m` | canopy/building/obstacle context | `43,500` | `0.5 m` | `696 GB` float32 raw | missing |
| `swisstlm3d` | roads, hydrography, land-cover, QA masks | national vector product | n/a | unknown until package selected | missing |
| `geocover_or_geology_context` | geology/material screening context | product dependent | n/a | unknown until package selected | missing |
| `swissbuildings3d` | building obstacle/exposure context for later risk workflows | product dependent | n/a | unknown until package selected | missing |

Byte estimates are uncompressed planning estimates. Actual COG/package sizes
depend on source format, compression, selected resolution, and product version.

## Cache Path Contract

The inventory uses deterministic path templates so later staging can be checked
without guessing:

- raw 2 m swissALTI3D:
  `data/raw/swisstopo/swissalti3d/2m/{tile_id}/source.tif`
- processed 2 m swissALTI3D:
  `data/processed/swisstopo/national/swissalti3d/2m/{tile_id}/dem.tif`
- raw SWISSIMAGE:
  `data/raw/swisstopo/swissimage/{resolution}/{tile_id}/source.tif`
- processed SWISSIMAGE overview:
  `data/processed/swisstopo/national/swissimage/{resolution}/{tile_id}/overview.tif`
- national swissTLM3D:
  `data/raw/swisstopo/swisstlm3d/{version}/source.gpkg`
- processed swissTLM3D:
  `data/processed/swisstopo/national/swisstlm3d/{version}/context.gpkg`

Every tile or national package needs these fields before it can be counted as
ready:

- product id and product version or delivery date
- source URL or download record
- license or terms reference
- tile id or package id
- source filename
- raw and processed SHA-256 checksums
- CRS, vertical datum where applicable, resolution, and LV95 extent
- cache status

## Data-Ready Breakdown

`terrain_tiles`: blocked on a national swissALTI3D 2 m tile manifest with
version/date, checksums, and local cache paths.

`visual_and_vector_context`: blocked on SWISSIMAGE and swissTLM3D coverage,
checksums, versions, and AOI coverage joins.

`obstacle_and_geology_context`: blocked before operational interpretation by
surface, buildings, and geology product selection, coverage, checksums, and
policy decisions.

## TB-645 Local Inventory Smoke

Command:

```bash
PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py \
  --national-data-inventory-smoke \
  --format json
```

Result:

- status: `planning_inventory_ready_missing_cache`
- tile count: `43,500`
- chunk count: `85`
- merge group count: `11`
- chunk size: `512` tiles
- last chunk tile count: `492`
- estimated required input bytes for mandatory terrain plus first visual/vector
  context: `2,093,100,000,000`
- missing products: `7`
- missing product IDs: `swissalti3d_2m`, `swissalti3d_0_5m`,
  `swissimage_10cm_or_25cm`, `swisssurface3d_raster_0_5m`, `swisstlm3d`,
  `geocover_or_geology_context`, `swissbuildings3d`
- mapping validation: ready
- sufficient for planning only: `true`
- data cache ready: `false`
- execution ready: `false`

Interpretation: the inventory and chunk mapping are current enough for
share-safe planning, sizing, and command-shape work. They are not sufficient for
Swiss-wide execution because no national product cache, checksums, versions, or
coverage joins are staged.

## Boundary

This is an inventory only. It does not download data, stage a national cache,
authorize Swiss-wide execution, or create operational hazard, annual-probability,
risk, exposure, or vulnerability claims.
