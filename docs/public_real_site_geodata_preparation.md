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
- Validator:
  `scripts/validate_public_real_site_geodata_manifest.py`

The checked-in template is intentionally `template_not_run`. A real local pilot
should copy it to an ignored working directory, fill in the selected domain and
tile inventory, and run the validator before deriving source zones or
simulation cases.

## Ignored Local Layout

Recommended local paths:

```text
data/raw/swisstopo/<pilot_id>/
data/processed/swisstopo/<pilot_id>/
validation/private/<pilot_id>/
hazard/results/<pilot_id>/
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

The validator checks the share-safe contract only. It verifies CRS/datum,
dataset roles, required boundaries, local path conventions, and that template
manifests do not pretend raw or processed geodata are present.

For a local real pilot, use the same validator after the manifest records real
tile ids, raw checksums, processed DEM metadata, and QA statuses. The validator
does not prove scientific skill; it only gates provenance and claim hygiene.

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
