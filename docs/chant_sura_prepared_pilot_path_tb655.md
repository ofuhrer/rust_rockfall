# Chant Sura Prepared-Pilot Path TB-655

Date: 2026-05-27

## Result

The Chant Sura / Fluelapass prepared-pilot path was exercised locally and is
blocked on missing real public-context inputs. It is not counted as a
real-input second-site validation run, and no Tschamut-only evidence is counted
as Chant Sura validation.

## Commands Run

```bash
PYENV_VERSION=system uv run python scripts/inventory_second_site_local_blockers.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json --json-output /tmp/tb655_second_site_blockers.json

PYENV_VERSION=system uv run python scripts/audit_multisite_source_scenario_contract.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json --json-output /tmp/tb655_multisite_audit.json

PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --repo-root . \
  --workflow-output-root /tmp/tb655_chant_sura_prepare \
  --smoke-case-path tests/fixtures/hazard/chant_sura_second_site_smoke_case.yaml \
  --format json --json-output /tmp/tb655_aoi_prepare.json

PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-prepared-pilot-local \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --repo-root . \
  --prepared-pilot-report-path /tmp/tb655_aoi_prepare.json \
  --prepared-pilot-output-root /tmp/tb655_chant_sura_prepared_pilot_local \
  --smoke-case-path tests/fixtures/hazard/chant_sura_second_site_smoke_case.yaml \
  --format json --json-output /tmp/tb655_prepared_pilot_local.json
```

## Observations

- Second-site local inventory status:
  `ready_with_deferred_public_context`.
- First blocking group:
  `public_context_inputs`.
- AOI prepare status:
  `ready_for_planning`.
- Prepared-pilot compiler classification:
  `blocked_missing_inputs`.
- Local prepared-pilot execution status:
  `blocked_local_execution`.

The local runner exits on the same missing-input boundary reported by the
compiler. The missing real input families are:

- `swissimage_context`
- `swisstlm3d_context`
- `swisssurface3d_context`
- `swisssurface3d_raster_context`
- `swissbuildings3d_context`

The first missing path is:

```text
data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage
```

## Boundary

The committed Chant Sura smoke case remains a portability fixture only. The
prepared-pilot path is blocked before local execution because the real
second-site public-context families have not been staged. This result reduces
the blocker to a concrete acquisition/staging boundary; it does not support
operational, physical-probability, Swiss-wide, or second-site validation claims.
