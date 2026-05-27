# TB-675 Chant Sura Prepared-Pilot Attempt

Date: 2026-05-27

## Result

The Chant Sura prepared-pilot path was re-run against the current staged inputs.
It reaches planning, but the prepared-pilot compiler and local execution wrapper
both stop before execution on missing real public-context products.

Prepare command:

```bash
PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --repo-root . \
  --workflow-output-root /tmp/tb675_chant_sura_prepare \
  --smoke-case-path tests/fixtures/hazard/chant_sura_second_site_smoke_case.yaml \
  --format json \
  --json-output /tmp/tb675_aoi_prepare.json
```

Local prepared-pilot command:

```bash
PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-prepared-pilot-local \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --repo-root . \
  --prepared-pilot-report-path /tmp/tb675_aoi_prepare.json \
  --prepared-pilot-output-root /tmp/tb675_chant_sura_prepared_pilot_local \
  --smoke-case-path tests/fixtures/hazard/chant_sura_second_site_smoke_case.yaml \
  --format json \
  --json-output /tmp/tb675_prepared_pilot_local.json
```

## Measured Status

- AOI prepare status: `ready_for_planning`
- Prepared-pilot compiler classification: `blocked_missing_inputs`
- Prepared-pilot compiler input classification: `blocked_missing_inputs`
- Local prepared-pilot status: `blocked_local_execution`
- Local first-blocker status: `blocked_missing_inputs`

The multisite source/scenario audit reports:

- `source_scenario_contract_audit_status`: `measured`
- `second_site_portability_status`: `deferred_public_context_inputs`
- `missing_second_site_fields`: `[]`

## First Concrete Blocker

The first missing input reported by the prepared-pilot compiler is:

`data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage`

The full missing context set is:

- `swissimage`
- `swisstlm3d`
- `swisssurface3d`
- `swisssurface3d_raster`
- `swissbuildings3d`

This narrows the previous broad public-context blocker to a first actionable
product family: stage the Chant Sura `SWISSIMAGE` context directory and
metadata, then rerun the prepared-pilot compiler.

## Boundary

No second-site validation run was executed. The committed smoke case remains a
fixture-backed portability check, and this task does not claim physical
probability, operational readiness, risk/exposure/vulnerability output, or
Swiss-wide execution.
