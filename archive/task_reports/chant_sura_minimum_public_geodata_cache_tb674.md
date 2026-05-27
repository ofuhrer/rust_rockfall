# TB-674 Chant Sura Minimum Public-Geodata Cache

Date: 2026-05-27

## Result

The minimum real public-geodata cache for Chant Sura is staged for the terrain
input family and verifies as ready through the dedicated cache manifest:

`data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml`

Verification command:

```bash
PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py \
  --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml \
  --format json \
  --json-output /tmp/tb674_minimum_cache_verify.json
```

Measured status:

- `verification_status`: `verified`
- `cache_integrity_status`: `ready`
- Required products: `1`
- Ready required products: `1`
- Missing required products: `0`
- Fixture-backed required products: `0`
- Product: `terrain_crop`
- Product verification: `verified`
- Provenance classification: `real_staged`

## Staged Real Product

The ready real public-geodata product is:

- Category: `terrain_crop`
- Source product: `swissALTI3D`
- Source tile: `2793-1180`
- Source URL:
  `https://data.geo.admin.ch/ch.swisstopo.swissalti3d/swissalti3d_2019_2793-1180/swissalti3d_2019_2793-1180_2_2056_5728.tif`
- Processed crop:
  `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc`
- Metadata:
  `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml`
- Processed checksum:
  `0a9b252ce639f0706244c1f7cb9204ef8b07dad283dc7471672b89b44ce70a24`

The second-site preflight also reports the core input families as ready:

- `core_input_status`: `ready`
- `terrain_manifest_status`: `ready`
- `source_zone_manifest_status`: `ready`
- `scenario_manifest_status`: `ready`
- `missing_input_categories`: `[]`

## Remaining Product Status

The full second-site portability path remains intentionally incomplete because
context products and scientific source/scenario inputs are not all real
site-specific evidence yet.

Ready real public geodata:

- `terrain_crop`
- `terrain_metadata`
- `aoi_tile_catalog`

Staged but not real validation evidence:

- `source_zone_metadata`
- `scenario_table`
- `source_scenario_policy`

Deferred public context:

- `swissimage_context`
- `swisstlm3d_context`
- `swisstlm3d_metadata`
- `swisssurface3d_context`
- `swisssurface3d_raster_context`
- `swissbuildings3d_context`

Optional or deferred:

- `barrier_inventory`
- `release_observation_evidence`

## Interpretation

TB-674 closes the empty-cache ambiguity for the second site: there is a verified
minimum real terrain cache, and the remaining work is now specifically context
staging plus replacement of regression source/scenario records with real
site-specific scientific evidence.

This does not claim a real second-site validation, physical probability,
operational hazard output, or Swiss-wide execution.
