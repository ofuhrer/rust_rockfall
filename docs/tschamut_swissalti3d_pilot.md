# Tschamut/swissALTI3D Real-Site Pilot

Status: local/private workflow template. This document describes how to rerun the Tschamut deposition/runout experiment with a manually supplied real swissALTI3D-style DEM crop and provenance metadata. It does not change simulation physics, default parameters, or validation semantics.

## Purpose

The current checked-in Tschamut validation uses a transparent proxy terrain. The next diagnostic question is whether the Tschamut under-run persists when the same model is run on a real, provenance-tracked Swiss DEM crop and explicit source-area metadata.

This workflow is deliberately controlled:

- no RAMMS data or proprietary inputs;
- no parameter tuning to Tschamut observations;
- no hidden terrain-class calibration;
- raw swissALTI3D data stay outside git;
- generated private case files live under ignored `validation/private/`.

## Inputs

Required local/private inputs:

- ESRI ASCII DEM crop, normally produced from a manually supplied swissALTI3D crop;
- terrain metadata sidecar following the Swiss terrain contract in `docs/swiss_terrain_ingestion_pilot.md`;
- release-zone/source-area metadata sidecar with an LV95/LN02 polygon and deterministic sampling settings.

Optional local/private input:

- terrain/material-class metadata sidecar with an aligned categorical ESRI ASCII class grid.

The terrain metadata must use:

- `source_dataset: swisstopo_swissalti3d`;
- `coordinate_reference_system.epsg: 2056`;
- `coordinate_reference_system.vertical_datum: LN02`;
- metre units for coordinates and heights;
- raster width, height, resolution, nodata, and extent matching the DEM header;
- source filename, license note, preprocessing status, and provenance notes;
- optional `preprocessing.processed_sha256`, which the preparation script checks against the DEM crop when present.

## Templates

Human-readable templates are checked in under:

- `validation/templates/tschamut_swissalti3d_baseline.yaml`
- `validation/templates/tschamut_swissalti3d_rotational.yaml`

These files contain placeholders and are not part of `cargo run -- validate --all`. Use the preparation script to create runnable ignored cases.

## Prepare Local Cases

Example:

```bash
python3 scripts/prepare_tschamut_swissalti3d_pilot.py \
  --dem-path /path/to/private/tschamut_swissalti3d_crop.asc \
  --terrain-metadata /path/to/private/tschamut_swissalti3d_metadata.yaml \
  --release-zone-metadata /path/to/private/tschamut_release_zone.yaml \
  --terrain-classes-metadata /path/to/private/tschamut_terrain_classes.yaml \
  --case-dir validation/private/tschamut_swissalti3d/cases \
  --results-dir validation/results/tschamut_swissalti3d_private \
  --ensemble-size 6 \
  --seed 34014 \
  --force
```

Omit `--terrain-classes-metadata` to run with global parameters only.

The script validates:

- private file existence with explicit missing-data errors;
- DEM header against terrain metadata width, height, resolution, extent, and nodata;
- CRS/vertical-datum consistency (`EPSG:2056`, `LN02`);
- release-zone polygon vertices inside the terrain extent;
- release-zone deterministic sampling settings;
- optional terrain-class grid dimensions, extent, resolution, CRS, and class metadata;
- optional processed DEM checksum.

It writes two ignored cases:

- `validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml`
- `validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml`

## Run The Pilot

Baseline:

```bash
cargo run -- validate \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml
```

Sphere-rotational comparison:

```bash
cargo run -- validate \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml
```

The generated cases write ignored outputs under `validation/results/tschamut_swissalti3d_private/`, including diagnostics JSON, run manifests, generated release points, ensemble deposition CSV, full ensemble trajectories, and full ensemble impact-event directories.

## Build Hazard Layers

The `--cell-size` examples below are convenience commands. Real controlled
pilot acceptance should use the explicit DEM-derived grid arguments documented
in `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`, so the hazard grid
matches the private DEM extent, dimensions, and cell size.

Baseline hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml \
  --output-dir hazard/results/tschamut_swissalti3d_baseline \
  --cell-size 5
```

Rotational hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml \
  --output-dir hazard/results/tschamut_swissalti3d_rotational \
  --cell-size 5
```

The generated cases include default diagnostic exceedance thresholds:

- kinetic energy: `1000 J`, `10000 J`;
- jump height: `0.5 m`, `2.0 m`;
- velocity: `5 m/s`, `10 m/s`.

These thresholds are placeholders for diagnostic comparison. They are not Swiss hazard-zone criteria and are not calibrated to Tschamut.

## Compare Against Existing Proxy Results

Run the existing proxy cases:

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
```

Then compare key metrics from:

- `validation/results/tschamut_baseline_metrics.json`;
- `validation/results/tschamut_basic_metrics.json`;
- `validation/results/tschamut_swissalti3d_private/validation_tschamut_swissalti3d_baseline_metrics.json`;
- `validation/results/tschamut_swissalti3d_private/validation_tschamut_swissalti3d_rotational_metrics.json`.

Use at least:

- `simulated_mean_runout_m`;
- `observed_mean_runout_m`;
- `runout_distance_error_m`;
- `deposition_centroid_error_m`;
- `deposition_cloud_mean_nearest_error_m`;
- `deposition_cloud_overlap_fraction`;
- `release_zone_mean_runout_m`;
- `release_zone_max_runout_m`.

Interpretation rule:

```text
Improved agreement under real terrain is evidence that proxy terrain and/or
source representation likely contributed to the under-run.
Persistent under-run under real terrain points toward release conditions, terrain classes,
shape, forest/obstacles, or contact parameters as remaining limitations.
```

## Manifest Expectations

`run_manifest_v1` records:

- external DEM path and terrain metadata path;
- source dataset/product/file/license/provenance;
- EPSG, vertical datum, extent, resolution, and nodata;
- optional raw and processed SHA-256 checksums from terrain metadata;
- release-zone metadata path, CRS, polygon extent/area, deterministic sampling seed, and generated point count;
- optional terrain-class metadata, class-grid path, class coverage, and source/license notes;
- model version, git hash, config fingerprint, seed policy, contact model, and output summaries.

Hazard-layer manifests record the generated hazard outputs and configured exceedance thresholds.

## Boundaries

This pilot deliberately does not:

- commit real swissALTI3D, SWISSIMAGE, or other raw geodata;
- tune restitution, friction, roughness, scarring, or terrain-class parameters to Tschamut;
- claim predictive skill or operational hazard validity;
- implement Cloud-Optimized GeoTIFF export or a full GIS product package;
- implement source-zone derivation from geology/slope/inventory layers;
- add shape-aware or forest/fragmentation physics.

The pilot answers a narrower question:

```text
Does the current model and source-area workflow behave differently when the
Tschamut proxy terrain is replaced by a real Swiss DEM crop?
```
