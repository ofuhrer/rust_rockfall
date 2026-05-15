# Public Real-Site Geodata Preparation

Status: Phase 1 preparation contract for a future public Swiss real-site pilot.
This document does not download swisstopo products, commit raw geodata, run
simulations, change physics, or create annual/physical probability products.

## Purpose

The real-case pilot needs a reproducible geodata package before source-zone,
block-scenario, ensemble, or hazard-layer work can be interpreted. The package
must make a small public Swiss pilot domain auditable from public inputs while
keeping raw swisstopo tiles and large processed crops out of git.

The preparation artifact is a manifest, not a hazard result. It records the
selected domain, required public datasets, source-tile inventory, local ignored
directory layout, preprocessing plan, checksums, CRS/vertical-datum assumptions,
and claim boundaries.

## Files

- Template manifest:
  `data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml`
- Selected-domain manifest:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
- Validator:
  `scripts/validate_public_real_site_geodata_manifest.py`
- Conditional pilot run-freeze template:
  `validation/templates/public_real_site_conditional_pilot_run_v1.yaml`
- Conditional pilot run-freeze validator:
  `scripts/validate_public_real_site_conditional_pilot_run.py`
- Report scaffold:
  `docs/public_real_site_conditional_pilot_report_template.md`

The checked-in template is intentionally `template_not_run`. A real local pilot
should copy it to an ignored working directory, fill in the selected domain and
tile inventory, and run the validator before deriving source zones or
simulation cases.

The first selected public pilot domain is the Tschamut 2014 public
release/deposition corridor. Its share-safe manifest is
`data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`. That manifest
binds the domain to public swissALTI3D tile `2696-1167`, EPSG:2056/LN02,
the expected 2 m ESRI ASCII crop extent, source and processed SHA-256 digests,
the deterministic preparation command, and the selected source-scenario policy
`validation/policies/tschamut_public_source_scenario_policy_v1.yaml`. It does
not commit the raw tile, processed DEM, generated cases, validation outputs, or
hazard outputs.

The Phase 6 run-freeze template is also intentionally not run. It records the
geodata manifest, source-zone/block-scenario policy, benchmark case, terrain
metadata, source-zone sidecar, scenario table, random seed, gate scale, target
scale, thresholds, explicit grid, output budget, and report classification
before any local pilot execution. Completed gate or target runs must also fill
the `run_evidence` block with share-safe paths, checksums, runtime, output
counts, and convergence-diagnostic status for the generated private artifacts.
It is the gate that prevents tuning or claim-language drift after outputs are
inspected.

## Ignored Local Layout

Recommended local paths:

```text
data/raw/swisstopo/<pilot_id>/
data/processed/swisstopo/<pilot_id>/
validation/private/<pilot_id>/
hazard/results/<pilot_id>/
```

For the selected Tschamut public pilot, the preparation command writes ignored
processed terrain artifacts under:

```text
data/processed/swisstopo/tschamut_public_pilot/
```

and uses the shared ignored public raw-data cache:

```text
data/raw/swisstopo/
data/raw/tschamut2014/
```

Raw swissALTI3D, SWISSIMAGE, swissSURFACE3D, swissTLM3D, GeoCover, Geological
Atlas, GeoMaps, and swissBUILDINGS3D products must remain ignored unless a
future commit explicitly adds a tiny license-compatible fixture.

## Minimum Manifest Content

The manifest must record:

- `pilot_id`, `pilot_status`, and `operational_status`;
- selected domain name, purpose, LV95 extent, CRS `EPSG:2056`, and vertical
  datum `LN02`;
- required swissALTI3D source tiles and optional context datasets;
- source URL, product version/date where known, license notes, and tile ids;
- raw and processed local paths, with raw files excluded from git;
- processed DEM path, format, resolution, dimensions, nodata policy, and
  checksum when a processed crop exists;
- preprocessing steps for tile selection, crop, CRS/datum checks, checksum
  calculation, DEM export, and metadata emission;
- DEM/terrain sensitivity status and visual QA status;
- claim boundaries that identify current products as diagnostic or conditional
  intensity-exceedance only.

`swisstopo_swissalti3d` is required for the first real-site pilot. Context
layers such as SWISSIMAGE, swissTLM3D, GeoCover, or swissSURFACE3D are optional
until a specific QA or source-zone policy needs them.

## Validation

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_geodata_manifest.py \
  data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml
```

Validate the selected Tschamut public pilot manifest:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_geodata_manifest.py \
  data/processed/swisstopo/tschamut_public_pilot_manifest.yaml
```

The validator checks the share-safe contract only. It verifies CRS/datum,
dataset roles, required boundaries, local path conventions, source-tile
identity, product version/date, source and processed SHA-256 digests, processed
DEM dimensions, nodata, crop extent, and that template manifests do not pretend
raw or processed geodata are present.

For a local real pilot, use the same validator after the manifest records real
tile ids, raw checksums, processed DEM metadata, and QA statuses. The validator
does not prove scientific skill; it only gates provenance and claim hygiene.

## Selected Tschamut Public Pilot Preparation

The selected-domain manifest can be reproduced from a clean checkout plus
public downloads with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/prepare_tschamut_public_benchmark.py \
  --output-root data/processed/swisstopo/tschamut_public_pilot \
  --padding-m 250 \
  --force
```

The script downloads public Tschamut 2014 EnviDat resources and the public
swissALTI3D tile into ignored raw caches when absent, transforms the selected
Tschamut release/deposition rows to LV95, crops the 2 m swissALTI3D tile to the
manifested extent, writes the ESRI ASCII DEM and terrain metadata sidecar, and
records checksums. If network access is unavailable, place the files listed in
the manifest at the ignored raw paths and rerun the same command. A missing or
checksum-mismatched download is an explicit no-go for Priority 1 reproduction.

Only the selected-domain manifest is committed. The raw public downloads,
processed crop, generated cases, validation outputs, and later hazard outputs
remain ignored. The Tschamut terrain package is input geodata for workflow
development; it is not validation evidence by itself.

## Second-Site Portability Preflight

`scripts/check_second_site_public_geodata_preflight.py` is a metadata-only
helper for a future Swiss site. It does not download geodata or run an
ensemble. Instead, it reports which public geodata products, terrain metadata,
source-zone/scenario records, extent definitions, and ignored output roots must
exist before the Tschamut workflow can be ported to a second site.

The preflight also distinguishes what is reusable from the current Tschamut
workflow, including readiness checks, case regeneration, convergence, output
profiling, context inspection, overlap diagnostics, and the uncertainty
envelope summary. It is a portability helper, not a gate or an acceptance
decision.

A staged placeholder candidate manifest lives at
`tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml`.
Running the preflight against that manifest is expected to remain blocked until
actual second-site terrain, context, source-zone, and scenario inputs are
staged under the candidate roots.

Before the first conditional pilot run, also run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/templates/public_real_site_conditional_pilot_run_v1.yaml
```

For a real local run, copy the template to an ignored pilot directory and use
the same validator after all freeze fields are populated. The validator requires
frozen inputs, nonnegative thresholds, explicit grid metadata, local output
budgets, and pass/no-go/inconclusive gate statuses. When a run is marked
`gate_run_completed` or `target_run_completed`, it also requires `run_evidence`
paths under the ignored validation/hazard output roots, recorded runtime and
output-volume metrics, convergence notes, and SHA-256 digests for the generated
manifests/tables. It does not run the simulator or hazard builder and does not
create or commit generated products.

After a non-template freeze file validates, print the dry-run command plan:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/private/<pilot_id>/<run_id>.yaml \
  --print-command-plan
```

The command plan validates the geodata manifest and source-scenario policy,
runs the frozen validation case, and builds conditional hazard layers with the
predeclared explicit grid, thresholds, map-package metadata, GeoTIFF export,
pilot GIS package manifest, and deterministic local reducer options. It is a
dry-run plan only; the user still executes the listed commands intentionally,
and generated outputs remain under ignored validation and hazard result roots.

## Claim Boundary

Phase 1 artifacts may claim:

- public geodata inventory is predeclared;
- CRS, vertical datum, extent, resolution, and provenance are recorded;
- raw and processed local paths are ignored or share-safe;
- future conditional pilot inputs are ready for review when all gates pass.

Phase 1 artifacts must not claim:

- annual frequency, return-period, or physical probability semantics;
- operational hazard-map validation;
- risk-map meaning;
- calibrated source frequency or block-population probability;
- validation evidence from swisstopo terrain by itself.
