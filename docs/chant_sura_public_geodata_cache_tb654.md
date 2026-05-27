# TB-654 Chant Sura Public-Geodata Cache Check

Date: 2026-05-27

## Result

The Chant Sura / Fluelapass second-site path is still blocked on real public
geodata, but the blocker is now product-by-product instead of an empty cache
verification result.

The preflight remains:

- `portability_preflight_status`: `deferred_public_context_inputs`
- `readiness_status`: `deferred_public_context_inputs`
- Blocker: public-context products are intentionally deferred until staged.

The cache verifier now reads the acquisition manifest's `expected_products`
rows and reports:

- `cache_integrity_status`: `partial`
- `cache_audit_status`: `partial`
- Product count: `14`
- Required products: `12`
- Ready required products: `1`
- Missing required products: `11`
- Optional products: `2`
- Fixture-backed required products: `0`
- Unsupported products: `0`

## Commands

```bash
PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json \
  --json-output /tmp/tb654_chant_sura_preflight.json

PYENV_VERSION=system uv run python scripts/stage_public_geodata_cache.py \
  --cache-manifest tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml \
  --mode dry-run \
  --proposal-output /tmp/tb654_chant_sura_stage_proposal.json \
  --format json \
  --json-output /tmp/tb654_chant_sura_stage_dry_run.json

PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py \
  --cache-manifest tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml \
  --format json \
  --json-output /tmp/tb654_chant_sura_verify.json
```

## Product Status

| Product | Required | Status | Provenance | Main blocker |
| --- | --- | --- | --- | --- |
| `terrain_crop` | yes | `checksum_mismatch` | `real_staged` | metadata fields do not match the cache contract |
| `terrain_metadata` | yes | `missing` | `missing` | metadata sidecar missing |
| `aoi_tile_catalog` | yes | `missing` | `missing` | metadata sidecar missing |
| `swissimage_context` | yes | `missing` | `missing` | staged directory and metadata missing |
| `swisstlm3d_context` | yes | `missing` | `missing` | staged directory and metadata missing |
| `swisstlm3d_metadata` | yes | `missing` | `missing` | staged file and metadata missing |
| `swisssurface3d_context` | yes | `missing` | `missing` | staged directory and metadata missing |
| `swisssurface3d_raster_context` | yes | `missing` | `missing` | staged directory and metadata missing |
| `swissbuildings3d_context` | yes | `missing` | `missing` | staged directory and metadata missing |
| `source_zone_metadata` | yes | `missing` | `missing` | metadata sidecar missing |
| `scenario_table` | yes | `missing` | `missing` | metadata sidecar missing |
| `source_scenario_policy` | yes | `missing` | `missing` | metadata sidecar missing |
| `barrier_inventory` | no | `optional_missing` | `missing` | staged directory and metadata missing |
| `release_observation_evidence` | no | `optional_missing` | `missing` | staged directory and metadata missing |

The next acquisition command remains the dry-run staging front door:

```bash
PYENV_VERSION=system uv run python scripts/stage_public_geodata_cache.py \
  --cache-manifest tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml \
  --mode dry-run \
  --format json
```

## Interpretation

This is a concrete acquisition blocker, not a second-site validation result.
The existing local files are enough for a metadata/preflight path, but not
enough for a real second-site prepared pilot. The next useful step is to stage
real swissALTI3D metadata consistency, AOI tile catalog metadata, SWISSIMAGE,
swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, swissBUILDINGS3D, and the
site-specific source/scenario records.

No operational, physical-probability, annual-frequency, risk, exposure,
vulnerability, Swiss-wide, distributed, or non-`postproc` claim is made by this
cache check.
