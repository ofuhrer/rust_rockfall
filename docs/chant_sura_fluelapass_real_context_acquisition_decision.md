# Chant Sura / Flüelapass Real-Context Acquisition Decision

Status: deferred real public-context staging; current repo-root readiness is blocked_missing_inputs.

This decision pack is read-only. It does not download swisstopo products, run a
second-site ensemble, or treat synthetic fixtures as evidence.

## Machine-Readable Decision

```yaml
schema_version: chant_sura_fluelapass_real_context_acquisition_decision_v1
candidate_site_id: chant_sura_fluelapass_portability_example_v1
candidate_site_name: Chant Sura / Flüelapass portability example
decision: defer
recommendation: defer_real_context_staging
decision_rationale: >-
  The current helper reports show that the candidate is structurally ready for
  acquisition review, but the clean-checkout acquisition planner still reports
  blocked_missing_inputs until the expected local core files are staged, and
  the public-context bundle remains intentionally deferred. The task boundary
  forbids any real swisstopo downloads until explicit acquisition
  authorization exists. Measured Balfrin evidence now exists, but the current
  interpretation remains conditional, bounded, and non-operational; it does
  not automatically authorize second-site public-context staging.
readiness_impact:
  planner_boundary: blocked_missing_inputs
  public_context_boundary: blocked_missing_inputs
  real_context_readiness_gate: blocked_missing_inputs
  second_site_ensemble: blocked
  operational_claims_allowed: false
  scale_up_authorized: false
expected_cache_roots:
  - data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1
  - data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input
  - data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context
  - validation/private/chant_sura_fluelapass_portability_example_v1
  - hazard/results/chant_sura_fluelapass_portability_example_v1
```

## Readiness Pack

Current repo-root state:

- `proceed`: none. The Balfrin trigger matrix only reaches `proceed` when measured conditional-diagnostic evidence is present.
- `defer`: `SWISSIMAGE`, `swissTLM3D`, `swissSURFACE3D`, `swissSURFACE3D Raster`, `swissBUILDINGS3D`.
- `missing-input`: `terrain_metadata`, `aoi_tile_catalog`, `swisstlm3d_metadata`, `source_zone_metadata`, `scenario_table`, `source_scenario_policy`.
- `locally-stageable`: `terrain_crop`, the core input bundle, and the public-context directory layout can all be staged without unauthorized downloads, but this pack does not execute those commands.

The operator execution plan below is the concrete handoff. It names the exact roots, expected metadata, verifier commands, and stop conditions, while keeping the no-download boundary in force.

The current clean-checkout helpers report:

- `plan_swisstopo_aoi_acquisition.py -> blocked_missing_inputs`
- `check_second_site_public_geodata_preflight.py -> blocked_missing_inputs`
- `check_chant_sura_real_context_readiness_gate.py -> blocked_missing_inputs`
- `plan_aoi_to_prepared_pilot_dry_run.py -> blocked_missing_inputs`

### Product Readiness Matrix

| Product | Decision | Current state | Exact root | Expected metadata | Verifier command | Stop condition |
|---|---|---|---|---|---|---|
| swissALTI3D terrain crop | stage | ready on the product row, but the overall gate still blocks on missing metadata inputs | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc` | `terrain_metadata.yaml` must carry `crs`, `vertical_datum`, `crop_provenance`, and `checksum` | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the AOI catalog, terrain sidecar, source-zone metadata, scenario table, or policy row is still missing; the crop alone is not readiness evidence. |
| swissALTI3D terrain metadata | stage | missing | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml` | `crs`, `vertical_datum`, `crop_provenance`, `checksum` | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the sidecar omits LN02/CRS/checksum provenance or if the gate still reports `blocked_missing_inputs`. |
| AOI tile catalog for deterministic swisstopo discovery | stage | missing | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml` | `tile_id`, `source_product`, `source_url`, `extent_lv95_m` | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the catalog cannot resolve AOI tile `2793-1180` or discovery remains `blocked_missing_inputs`. |
| SWISSIMAGE | defer | deferred_public_context | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage` | Cache verifier fields: `source_product_id`, `source_product_name`, `source_url_or_download_record`, `product_version_or_date`, `tile_id_or_delivery_identifier`, `checksum_sha256`, `crs`, `resolution_m`, `crop_extent_lv95_m`, `license_or_terms_reference`, `raw_checksum`, `processed_checksum`, `preprocessing_command_and_timestamp` | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the verifier returns anything other than `verified`; do not download to "fix" a missing row. |
| swissTLM3D | defer | deferred_public_context | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d` | Same cache verifier fields as above; the row also expects the staged archive contract to remain auditable | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the verifier returns `missing`, `checksum_mismatch`, or `metadata_mismatch`. |
| swissTLM3D metadata | defer | missing | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d/metadata.json` | `metadata.json`, `source_product`, `staged_asset_present`, plus the cache verifier fields above | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the metadata sidecar is absent or if it cannot be reconciled with the cache contract. |
| swissSURFACE3D | defer | deferred_public_context | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d` | Same cache verifier fields as above | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the verifier returns `missing`, `checksum_mismatch`, or `metadata_mismatch`. |
| swissSURFACE3D Raster | defer | deferred_public_context | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d_raster` | Same cache verifier fields as above | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the verifier returns `missing`, `checksum_mismatch`, or `metadata_mismatch`. |
| swissBUILDINGS3D | defer | deferred_public_context | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissbuildings3d` | Same cache verifier fields as above | `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` | Stop if the verifier returns `missing`, `checksum_mismatch`, or `metadata_mismatch`. |
| barrier inventory | optional | optional | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/barriers` | Only if a site-specific workflow explicitly references barriers or nets | No verifier until the workflow names the row explicitly | Stop unless the workflow explicitly asks for barriers or nets. |
| source-zone metadata | stage | missing | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml` | `source_zone_id` or equivalent site-specific release-zone identifier; LV95 polygon geometry; release-point table if present | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the release-zone geometry, identifier, or release-point table is synthetic-only or missing. |
| scenario table | stage | missing | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv` | `scenario_id`, `probability`, and site-specific scenario rows | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the table is missing or the scenario family cannot be normalized without inventing annual-frequency semantics. |
| source-scenario policy | stage | missing | `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml` | `policy_id` or equivalent site-specific policy identifier; site-specific policy content | `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` | Stop if the policy is synthetic-only or if it cannot be tied to the staged source-zone and scenario rows. |
| release observation evidence | optional | optional | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/validation_observations` | Site-specific QA source, if any | No verifier until a site-specific QA source exists | Stop unless an independent site-specific QA source is available. |

The product matrix above is intentionally fail-closed:

- the `stage_*` rows describe the only local command families that would populate the required roots;
- the `defer` rows stay deferred until the Balfrin trigger becomes `proceed`;
- the AOI catalog row stays stage-only until discovery metadata exists;
- the optional rows remain optional and are not evidence by themselves.

The public-context cache rows all share the same deterministic verifier fields:

- `source_product_id`
- `source_product_name`
- `source_url_or_download_record`
- `product_version_or_date`
- `tile_id_or_delivery_identifier`
- `checksum_sha256`
- `crs`
- `resolution_m`
- `crop_extent_lv95_m`
- `license_or_terms_reference`
- `raw_checksum`
- `processed_checksum`
- `preprocessing_command_and_timestamp`

## Staging Checklist

The Chant Sura real-context readiness gate now emits a product-by-product
staging checklist alongside the acquisition plan. The checklist is a dry-run
operator aid only: it points to the cache-manifest fields, expected staging
roots, and the verifier command for each deferred public-context product, but
it does not download data, validate products, or authorize a second-site run.

Use the checklist to see which rows are `missing`, `partially_staged`, or
`verifier_ready` before any real-context handoff is considered.

## No-Download Fallback Report

When credentials are unavailable or a required local file is missing, the
operator response is a no-download fallback, not a retry loop.

- Fallback status: `blocked_missing_inputs`
- Current missing local inputs: AOI tile catalog metadata, terrain metadata,
  source-zone metadata, scenario table, and source-scenario policy
- Current deferred public-context inputs: SWISSIMAGE, swissTLM3D,
  swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D
- Stop condition: do not download any swisstopo product, do not submit a
  second-site ensemble, and do not treat synthetic fixtures as evidence
- Verifier command for the fallback state: `PYENV_VERSION=system uv run python
  scripts/check_chant_sura_real_context_readiness_gate.py --site-config
  tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml
  --format json`
- Report interpretation: the plan is still metadata-only until the required
  local roots exist and the cache verifier can return `verified`

## Required Products

| Product | Required | Expected staged path | Expected data volume | Readiness impact |
|---|---|---|---|---|
| swissALTI3D terrain crop | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc` | one crop plus metadata sidecar; small compared with public context | required terrain foundation |
| swissALTI3D terrain metadata | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml` | tiny metadata record | freezes CRS, LN02, checksum, and crop provenance |
| SWISSIMAGE | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage` | inferred: likely one 1 km tile bundle for this AOI; exact bytes not staged | QA/context only, not hazard evidence |
| swissTLM3D | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d` | inferred: one vector tile bundle plus metadata; exact bytes not staged | context and exclusion masks |
| swissTLM3D metadata | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d/metadata.json` | tiny metadata record | keeps the archive contract auditable |
| swissSURFACE3D | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d` | inferred: one point-cloud tile bundle; exact bytes not staged | optional future surface/obstacle context |
| swissSURFACE3D Raster | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d_raster` | inferred: one raster tile bundle; exact bytes not staged | optional QA/context |
| swissBUILDINGS3D | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissbuildings3d` | inferred: one building tile bundle; exact bytes not staged | optional obstacle/exposure context |
| barrier inventory | no | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/barriers` | site-policy dependent and usually small | only if a site-specific workflow explicitly asks for it |
| source-zone metadata | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml` | tiny metadata record | required contract input |
| scenario table | yes | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv` | tiny metadata table | required contract input |
| source-scenario policy | yes | `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml` | tiny policy record | required contract input |
| release observation evidence | no | `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/validation_observations` | tiny if present | optional QA source, not a requirement |

## Balfrin Trigger Matrix

Measured Balfrin evidence is now available, but the current decision stays
`defer` because the trigger requires accepted conditional-diagnostic evidence
and an explicit acquisition authorization. The trigger is concrete:

- `interpretation_status: measured_conditional_diagnostic`
- `artifact_acceptance_status: accepted_conditional_diagnostic`
- `usable_as_conditional_diagnostic_artifact: true`

If the Balfrin post-run gate is `inconclusive_conditional_diagnostic`, the
same product rows stay deferred. If the evidence bundle is missing, the rows
are blocked rather than guessed. The product order is a staging priority, not
a scientific ranking.

```yaml
schema_version: chant_sura_real_context_trigger_matrix_v1
evidence_sources:
  post_run_interpretation_gate: scripts/summarize_balfrin_post_run_interpretation_gate.py
  balfrin_evidence_bundle: validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/balfrin_evidence_bundle_v1.json
trigger_states:
  proceed:
    interpretation_status: measured_conditional_diagnostic
    artifact_acceptance_status: accepted_conditional_diagnostic
    usable_as_conditional_diagnostic_artifact: true
  defer:
    interpretation_status: inconclusive_conditional_diagnostic
    artifact_acceptance_status: accepted_conditional_diagnostic
    usable_as_conditional_diagnostic_artifact: true
  blocked:
    interpretation_status: blocked_missing_inputs
    artifact_acceptance_status: blocked_missing_inputs
    usable_as_conditional_diagnostic_artifact: false
products:
  - category: swissimage_context
    product: SWISSIMAGE
    staging_priority: 1
    proceed_decision: proceed
    defer_decision: defer
    blocked_decision: blocked_missing_inputs
  - category: swisstlm3d_context
    product: swissTLM3D
    staging_priority: 2
    proceed_decision: proceed
    defer_decision: defer
    blocked_decision: blocked_missing_inputs
  - category: swisssurface3d_context
    product: swissSURFACE3D
    staging_priority: 3
    proceed_decision: proceed
    defer_decision: defer
    blocked_decision: blocked_missing_inputs
  - category: swisssurface3d_raster_context
    product: swissSURFACE3D Raster
    staging_priority: 4
    proceed_decision: proceed
    defer_decision: defer
    blocked_decision: blocked_missing_inputs
  - category: swissbuildings3d_context
    product: swissBUILDINGS3D
    staging_priority: 5
    proceed_decision: proceed
    defer_decision: defer
    blocked_decision: blocked_missing_inputs
```

## Cache And Output Roots

- Raw public-cache root: `data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1`
- Processed input root: `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input`
- Processed context root: `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context`
- Validation root: `validation/private/chant_sura_fluelapass_portability_example_v1`
- Hazard root: `hazard/results/chant_sura_fluelapass_portability_example_v1`

## Readiness Impact

- The helper set is enough to say the candidate is structurally ready for
  real-context acquisition review, but the clean-checkout planner and gate now
  both report `blocked_missing_inputs` because the AOI catalog and site-specific
  metadata records are not fully staged.
- The decision remains `defer` because the task boundary forbids real downloads
  and the repo should not treat metadata-only fixtures as evidence for a second
  site. The public-context rows remain deferred even after the core bundle is
  staged.
- The immediate effect is that the next actionable step is documentation or
  authorization review, not a download or ensemble run.

### Second-Site Readiness Snapshot

This second-site readiness check on the Chant Sura / Flüelapass candidate
classifies the candidate as `blocked_missing_inputs`. It is not the frozen
Tschamut target-area Balfrin demonstration contract; that contract is recorded
separately in
`validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`.

Current helper outputs:

- `PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` -> `blocked_missing_inputs`
- `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json` -> `blocked_missing_inputs`
- `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml --format json` -> `verified` with `product_count: 0`; this is only a manifest-shape check and does not prove that any products are staged.

Exact missing or deferred products and paths:

- missing AOI tile catalog metadata at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml`
- missing terrain crop at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc`
- missing terrain metadata at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml`
- missing source-zone metadata at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml`
- missing scenario table at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv`
- missing source-scenario policy at `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`
- deferred public context at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage`
- deferred public context at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d`
- deferred public context metadata at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d/metadata.json`
- deferred public context at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d`
- deferred public context at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d_raster`
- deferred public context at `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissbuildings3d`

The candidate remains blocked until the required catalog, terrain, source-zone,
scenario, and policy inputs are staged. Public context stays deferred until a
site-specific workflow explicitly needs it.

## Exact Commands

Run these commands to reproduce the current decision surface:

```bash
PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/plan_aoi_to_prepared_pilot_dry_run.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json
```

The first two commands report the acquisition boundary and required product
inventory. The real-context gate keeps the synthetic core fixtures out of the
evidence bucket, and the AOI-to-prepared-pilot dry run keeps the downstream
workflow blocked rather than authorizing a second-site ensemble.

Use these reproduction commands to verify the cache contract and identify the
missing-input remediation surface:

```bash
PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py \
  --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json

PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json
```

If the missing inputs are later staged, the remediation surface is the helper
family already listed in the acquisition plan:

- `stage_public_terrain_crop` for the terrain crop and metadata sidecar
- `stage_public_context_bundle` for the public-context directory layout
- `stage_source_and_scenario_records` for the source-zone metadata, scenario
  table, and source-scenario policy

Observed current statuses:

- `plan_swisstopo_aoi_acquisition.py` -> `blocked_missing_inputs`
- `check_second_site_public_geodata_preflight.py` -> `blocked_missing_inputs`
- `check_chant_sura_real_context_readiness_gate.py` -> `blocked_missing_inputs`
- `plan_aoi_to_prepared_pilot_dry_run.py` -> `blocked_missing_inputs`
