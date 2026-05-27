# Swiss National Inventory Chunk Smoke TB-661

Date: 2026-05-27

Command:

```bash
PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py \
  --national-data-inventory-smoke \
  --format json --json-output /tmp/tb661_inventory_smoke.json
```

## Result

- `status`: `planning_inventory_ready_missing_cache`
- `inventory_status`: `share_safe_no_download_inventory`
- `tile_count`: `43,500`
- `chunk_count`: `85`
- `merge_group_count`: `11`
- `chunk_size_tiles`: `512`
- `last_chunk_tile_count`: `492`
- `estimated_required_input_bytes`: `2,093,100,000,000`
- `mapping_validation_ready`: `true`
- `data_cache_ready`: `false`
- `execution_ready`: `false`

## Current Data-Cache Blocker

The chunk mapping is ready for planning only. Swiss-wide execution remains
blocked by missing staged cache, version, checksum, and coverage records for
these product families:

- `swissalti3d_2m`
- `swissalti3d_0_5m`
- `swissimage_10cm_or_25cm`
- `swisssurface3d_raster_0_5m`
- `swisstlm3d`
- `geocover_or_geology_context`
- `swissbuildings3d`

## Boundary

This is a share-safe inventory/chunk smoke. It does not download national data,
stage a cache, authorize Swiss-wide execution, enable distributed execution, or
change operational, annual-frequency, physical-probability, risk, exposure, or
vulnerability claims.
