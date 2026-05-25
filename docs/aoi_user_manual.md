# AOI User Manual

Status: compact user-facing front door for AOI preparation, candidate review,
bounded execution, and QGIS review.

This page is diagnostic and conditional only. It does not authorize
operational, annual-frequency, physical-probability, risk, exposure, or
vulnerability claims.

For a one-screen summary of the current workflow stage, blocker, and next
command, start with:

```bash
PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py workflow \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --workflow-output-root /tmp/aoi_workflow \
  --format text
```

## Supported Local Commands

The AOI user-facing surface is intentionally small:

- `scripts/run_aoi_hazard_workflow.py workflow` shows current AOI status, the
  first blocker, and the next command.
- `scripts/run_aoi_hazard_workflow.py describe-config` explains the effective
  site configuration and paths.
- `scripts/run_aoi_hazard_workflow.py prepare` checks staged public inputs and
  stops before simulation work.
- `scripts/run_aoi_hazard_workflow.py candidate-review` writes the bounded
  candidate-review package and review overlays.
- `scripts/run_aoi_hazard_workflow.py run-local-smoke` and
  `scripts/run_aoi_hazard_workflow.py run-prepared-pilot-local` are the local
  bounded execution paths.
- `scripts/run_aoi_hazard_workflow.py package-map` reports packaging readiness
  for an existing hazard root.
- `scripts/generate_pilot_command_plan.py` emits portable pilot command plans
  without running them.

Other Python files in `scripts/` are developer, diagnostic, or implementation
helpers unless this manual explicitly says otherwise.

Balfrin/HPC execution is outside this local AOI path. Advanced scaling work
starts from the
[`Balfrin Tschamut pilot runbook`](balfrin_tschamut_pilot_runbook.md), after
the local AOI inputs and diagnostics are explicit.

## Command Path

1. Plan the public-geodata acquisition command set.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py plan \
     --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
     --format text
   ```

   This is the copy/paste handoff for AOI public-geodata staging. It lists the
   product IDs, expected local roots, cache verification commands, and staging
   commands for the supplied AOI. The default mode is dry-run, so it stays
   read-only and does not download public data unless you later opt into the
   explicit staging driver.

2. Describe the AOI config.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py describe-config \
     --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
     --repo-root . \
     --format text
   ```

   Use this to inspect the effective site config, generated roots, and current
   local-state dependency note before staging anything.

3. Prepare the AOI.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare \
     --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
     --repo-root . \
     --format json
   ```

   This is the read-only preparation gate. It verifies staged public inputs and
   stops before simulation work.

4. Review candidate release zones.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py candidate-review \
     --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
     --candidate-review-output-root /tmp/aoi_candidate_review \
     --format json
   ```

   This writes the bounded candidate-review package under `/tmp` and records
   the overlay manifest, review paths, and first blocker when inputs are still
   missing. The candidate GeoJSON features carry deterministic slope-band,
   local-relief, size, separation, context-exclusion, and review-status
   attributes so QGIS identify/label tools can explain why each candidate was
   kept in the review set. Use `--search-domain-mode` to switch between the
   explicit `local`, `expanded`, and `full_aoi` sweep domains; the emitted
   search-domain GeoJSON layer records the exact bounds used for the sweep.

5. Generate the diagnostic package.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py package-map \
     --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 \
     --package-output-root /tmp/aoi_review_package \
     --overwrite \
     --format json
   ```

   When `--package-output-root` is supplied, the front door delegates to the
   package builder, copies the tracked QGIS style bundle into
   `/tmp/aoi_review_package/styles/`, and annotates raster/vector inventory
   entries with the matching `.qml` references where one exists.

6. Use the front-door packaging gate when you want the compact readiness
   report for an existing hazard root.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py package-map \
     --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 \
     --format json
   ```

   This stays diagnostic. It reports packaging readiness for an existing hazard
   root; it does not create a QGIS project or claim operational readiness.

## Internal Helper Routing

Prefer the supported local commands above instead of direct user invocation of
these lower-level helpers:

| Helper | Reach it through |
| --- | --- |
| `scripts/plan_swisstopo_aoi_acquisition.py` | `scripts/run_aoi_hazard_workflow.py plan` or `workflow` |
| `scripts/check_second_site_public_geodata_preflight.py` | `scripts/run_aoi_hazard_workflow.py prepare` or `workflow` |
| `scripts/plan_aoi_terrain_preprocessing.py` | `scripts/run_aoi_hazard_workflow.py prepare` |
| `scripts/plan_terrain_release_zone_candidates.py` | `scripts/run_aoi_hazard_workflow.py candidate-review` |
| `scripts/audit_gis_cog_package_readiness.py` | `scripts/run_aoi_hazard_workflow.py package-map` |
| `scripts/generate_tschamut_same_scale_cases.py` | `scripts/generate_pilot_command_plan.py` |
| `scripts/package_aoi_hazard_map.py` | `scripts/run_aoi_hazard_workflow.py package-map --package-output-root ...` |

## QGIS Review Path

The tracked style bundle lives in `qgis/styles/` and is copied into each
package `styles/` directory by `scripts/package_aoi_hazard_map.py`.

Apply the package styles in QGIS by loading the matching `.qml` from the
generated `styles/` directory for each layer or overlay. The matching bundle is
diagnostic symbology only:

- candidate source zones;
- accepted and rejected review zones;
- release points;
- scenario families;
- reach and deposition diagnostics;
- maximum kinetic energy;
- maximum jump height;
- conditional exceedance rasters.

There is no separate plugin or operational QGIS project in this repository.
The package command is the style-application entry point. A manifest-only QGIS
Processing bridge prototype is tracked at
`tests/fixtures/qgis_processing_connector_manifest_v1.json`; it maps future
QGIS actions onto the existing CLI front doors and is covered by
`tests/test_qgis_processing_connector_manifest.py`. The manifest action names
and tracked style asset names are smoke-checked against this manual and the
`scripts/run_aoi_hazard_workflow.py` subcommands, so rename them together.

## Interpretation Boundaries

- Conditional-only, diagnostic outputs are the current scope.
- No annual-frequency, physical-probability, risk, exposure, vulnerability, or
  operational claim is implied by these commands.
- Optional observed-evidence overlays stay separate and remain blocked unless
  explicitly staged.
- The review path is for GIS inspection and communication, not authorization.
