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

## Command Path

1. Plan the public-geodata acquisition command set.

   ```bash
   PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py \
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
   missing.

5. Generate the diagnostic package.

   ```bash
   PYTHONPATH=$PWD PYENV_VERSION=system uv run python scripts/package_aoi_hazard_map.py \
     --input-root hazard/results/tschamut_public_pilot/target_gate_v1 \
     --output-root /tmp/aoi_review_package \
     --overwrite \
     --format json
   ```

   This copies the tracked QGIS style bundle into `/tmp/aoi_review_package/styles/`
   and annotates raster/vector inventory entries with the matching `.qml`
   references where one exists.

6. Use the front-door packaging gate when you want the compact readiness
   report for an existing hazard root.

   ```bash
   PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py package-map \
     --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 \
     --format json
   ```

   This stays diagnostic. It reports packaging readiness for an existing hazard
   root; it does not create a QGIS project or claim operational readiness.

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
`tests/test_qgis_processing_connector_manifest.py`.

## Interpretation Boundaries

- Conditional-only, diagnostic outputs are the current scope.
- No annual-frequency, physical-probability, risk, exposure, vulnerability, or
  operational claim is implied by these commands.
- Optional observed-evidence overlays stay separate and remain blocked unless
  explicitly staged.
- The review path is for GIS inspection and communication, not authorization.
