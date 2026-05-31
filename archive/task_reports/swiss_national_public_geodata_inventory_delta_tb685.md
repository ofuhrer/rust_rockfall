# Swiss National Public-Geodata Inventory Delta TB-685

Date: 2026-05-31

Command:

```bash
PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py \
  --national-data-inventory-smoke \
  --format json --json-output /tmp/tb685_inventory_delta.json
```

## Result

- Delta status: `measured_local_filesystem_inventory_delta_missing_national_cache`
- Smoke status: `planning_inventory_ready_missing_cache`
- Present cache products: `5`
- Missing national products: `5`
- Estimated national bytes reference total: `2,789,100,000,000`
- Next acquisition command: `BLOCKED` because no national staging helper exists yet

## Product Delta

### swissALTI3D

- Present caches:
  - `data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1/swissalti3d_2019_2793-1180_2_2056_5728.tif` (`1,096,566` bytes)
  - `data/raw/swisstopo/swissalti3d_2019_2696-1167_2_2056_5728.tif` (`1,201,215` bytes)
- Present cache bytes: `2,297,781`
- National estimate: `43,500,000,000` bytes for the `2 m` delivery
- National stage status: missing
- First acquisition action: promote the local 2 m swissALTI3D cache into the deterministic national staging template and add version/date, source URL, and raw/processed checksums

### SWISSIMAGE

- Present caches:
  - `data/raw/swisstopo/swissimage/swissimage-dop10_2019_2696-1167_2_2056.tif` (`164,008` bytes)
- Present cache bytes: `164,008`
- National estimate: `2,049,600,000,000` bytes for `25 cm`; `12,810,000,000,000` bytes for `10 cm`
- National stage status: missing
- First acquisition action: choose the national SWISSIMAGE resolution, then stage the delivery into the matching raw cache template and add version/date, source URL, and checksums

### swissTLM3D

- Present caches:
  - `data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip` (`3,136,564,656` bytes)
- Present cache bytes: `3,136,564,656`
- National estimate: unavailable until a national package/version is selected
- National stage status: missing
- First acquisition action: choose the national swissTLM3D package/version, then stage the delivery into the versioned raw cache template and add checksums plus coverage metadata

### swissSURFACE3D Raster

- Present caches:
  - `data/raw/swisstopo/swisssurface3d_raster/swisssurface3d-raster_2020_2696-1167_0.5_2056_5728.tif` (`16,234,230` bytes)
- Present cache bytes: `16,234,230`
- National estimate: `696,000,000,000` bytes for the `0.5 m` delivery
- National stage status: missing
- First acquisition action: promote the local 0.5 m swissSURFACE3D Raster cache into the national staging template and add version/date, source URL, and checksums

### swissBUILDINGS3D

- Present caches:
  - `data/raw/swisstopo/swissbuildings3d/swissbuildings3d_3_0_2021_1232-12_2056_5728.gdb.zip` (`1,005,273` bytes)
- Present cache bytes: `1,005,273`
- National estimate: unavailable until a national package/version is selected
- National stage status: missing
- First acquisition action: choose the national swissBUILDINGS3D package/version, then stage the delivery into the raw cache template and add checksums plus coverage metadata

## Boundary

This is a filesystem-backed inventory delta only. It shows that local raw caches are already visible for the five requested product families, but no national cache promotion, coverage join, or checksum/version manifest exists yet. It does not download swisstopo products, authorize Swiss-wide execution, or introduce operational, annual-frequency, physical-probability, risk, exposure, or vulnerability claims.
