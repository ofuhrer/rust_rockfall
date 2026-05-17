# Chant Sura / Flüelapass Real-Context Acquisition Decision

Status: deferred real public-context staging.

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
  forbids any real swisstopo downloads until an explicit acquisition
  authorization exists after the Balfrin demo path is assessed.
readiness_impact:
  planner_boundary: blocked_missing_inputs
  public_context_boundary: deferred_public_context_inputs
  real_context_readiness_gate: ready_for_real_context_acquisition
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

The current decision stays `defer` until measured Balfrin evidence is
available. The trigger is concrete:

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
  real-context acquisition review, but the AOI planner still reports
  `blocked_missing_inputs` in a clean checkout and the public-context bundle
  remains intentionally deferred until it is explicitly authorized.
- The decision remains `defer` because the task boundary forbids real downloads
  and the repo should not treat metadata-only fixtures as evidence for a second
  site.
- The immediate effect is that the next actionable step is documentation or
  authorization review, not a download or ensemble run.

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

Observed current statuses:

- `plan_swisstopo_aoi_acquisition.py` -> `blocked_missing_inputs`
- `check_second_site_public_geodata_preflight.py` -> `deferred_public_context_inputs`
- `check_chant_sura_real_context_readiness_gate.py` -> `ready_for_real_context_acquisition`
- `plan_aoi_to_prepared_pilot_dry_run.py` -> `blocked_missing_inputs`
