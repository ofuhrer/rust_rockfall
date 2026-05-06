# Swiss Terrain-Ingestion Pilot

Status: minimal `v0.5.x` pilot contract. This document describes the first swissALTI3D-style terrain ingestion path, deterministic source-area fixture, and opt-in terrain/material-class fixture layered on top of them. It does not add GIS production functionality and does not change simulation physics.

## Purpose

The immediate goal is to make Swiss terrain inputs, source areas, and terrain/material classes auditable before adding larger geospatial workflows. The pilot supports small manually supplied or synthetic ESRI ASCII DEM crops with a required terrain-source metadata sidecar. The metadata sidecar records CRS, vertical datum, extent, resolution, nodata handling, source/provenance, license/data-origin notes, and preprocessing status.

The pilot follows the standard ESRI/GIS raster convention: `xllcorner` and
`yllcorner` define the outer lower-left cell corner, elevation values are
cell-center samples, and the LV95 extent records the full outer footprint.

Raw swisstopo products remain out of git. The checked-in pilot fixture is synthetic but uses LV95/LN02-style coordinates so validation and manifests exercise the same metadata contract expected for future swissALTI3D crops.

## Files

Pilot fixture:

- `validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc`
- `validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml`
- `validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml`
- `validation/data/processed/swisstopo_pilot/terrain_classes.asc`
- `validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml`

Pilot validation cases:

- `validation/cases/swissalti3d_pilot.yaml`
- `validation/cases/swissalti3d_release_zone_pilot.yaml`
- `validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml`
- `validation/cases/swissalti3d_hazard_statistics_pilot.yaml`

The case uses `terrain.type: ascii_dem_clamped`, points at the small DEM crop, and adds:

```yaml
terrain:
  metadata_path: validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml
```

When `outputs.manifest_json` is set, the generated `run_manifest_v1` records the validated terrain metadata.

The source-area pilot adds:

```yaml
release_zone:
  metadata_path: validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml
  generated_release_points_csv: validation/results/swissalti3d_release_zone_points.csv
```

This opt-in block generates deterministic release points from a small polygon. It is an orchestration/provenance feature; it does not change the trajectory physics or the default manual `release` behavior.

The terrain-class pilot adds:

```yaml
terrain_classes:
  metadata_path: validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml
```

This opt-in block reads an aligned categorical raster and applies class-specific overrides to existing contact/scarring parameters at contact locations. Global parameters remain in force outside the class grid, on nodata cells, and for any parameter omitted by a class. This is spatial parameter selection, not new physics or calibration.
Scarring-related class overrides only affect cases that already opt into `soil_interaction_model: scarring_contact_v1`; terrain classes do not enable scarring by themselves.

## Metadata Contract

The runtime parser currently validates:

- `schema_version: 1`;
- `source_dataset: swisstopo_swissalti3d`;
- `coordinate_reference_system.epsg: 2056`;
- `coordinate_reference_system.vertical_datum: LN02`;
- coordinate and height units in metres;
- positive resolution and raster dimensions;
- finite LV95 extent whose width/height match raster dimensions and resolution;
- non-empty source product, source filename, license, preprocessing status, resampling method, and intended use;
- if an ESRI ASCII DEM is present, metadata width, height, cell size, nodata value, and footprint must match the DEM header.

The metadata schema remains intentionally small. It is a provenance and guardrail contract, not a replacement for a full geospatial library.

## Release-Zone Contract

The release-zone parser currently validates:

- `schema_version: 1`;
- `coordinate_reference_system.epsg: 2056`;
- `coordinate_reference_system.vertical_datum: LN02`;
- coordinate and height units in metres;
- `geometry.type: polygon` with at least three finite LV95 vertices and positive area;
- `sampling.mode: deterministic_grid`;
- positive `sampling.count`, deterministic `sampling.seed`, initial velocity, optional `z_offset_m`, and release id prefix;
- non-empty source dataset, license, intended use, and provenance notes.

When terrain metadata is present, the release-zone CRS/vertical datum must match the DEM metadata and the polygon extent must lie inside the pilot DEM footprint.

## Terrain-Class Contract

The terrain-class parser currently validates:

- `schema_version: 1`;
- `coordinate_reference_system.epsg: 2056`;
- `coordinate_reference_system.vertical_datum: LN02`;
- coordinate and height units in metres;
- `class_grid_path` pointing to an ESRI ASCII categorical raster;
- raster width, height, resolution, nodata value, and LV95 extent matching the DEM metadata;
- every non-nodata raster value maps to a declared class id;
- optional class overrides for `restitution_n`, `restitution_t`, `friction_mu`, `rolling_resistance`, `soil_strength_pa`, `scarring_drag_coefficient`, `scarring_layer_density_kgpm3`, and `scarring_max_depth_m`;
- non-empty source dataset, license, intended use, and provenance notes.

The generated `run_manifest_v1` records class layer id, metadata path, class-grid path, CRS, extent, source/license fields, class coverage histogram, and provenance notes.

## Run

```bash
cargo run -- validate --case validation/cases/swissalti3d_pilot.yaml
cargo run -- validate --case validation/cases/swissalti3d_release_zone_pilot.yaml
cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml
cargo run -- validate --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml
```

The case writes ignored outputs under `validation/results/`, including:

- `swissalti3d_pilot_metrics.json`
- `swissalti3d_pilot_trajectory.csv`
- `swissalti3d_pilot_manifest.json`
- `swissalti3d_release_zone_points.csv`
- `swissalti3d_release_zone_deposition.csv`
- `swissalti3d_release_zone_pilot_manifest.json`
- `swissalti3d_terrain_class_release_points.csv`
- `swissalti3d_terrain_class_deposition.csv`
- `swissalti3d_release_zone_terrain_classes_pilot_manifest.json`
- `swissalti3d_hazard_stats_trajectories/`
- `swissalti3d_hazard_stats_impacts/`
- `swissalti3d_hazard_statistics_pilot_manifest.json`

The manifest terrain section includes LV95/LN02 metadata, source dataset/product fields, license note, extent, nodata value, metadata path, and DEM path. The release-zone manifest section records the source-area metadata path, CRS, deterministic sampling seed, requested/generated release-point count, polygon extent/area, source/license fields, and provenance notes.
The terrain-class manifest section records class-layer provenance and class coverage. The checked-in class parameters are illustrative fixtures, not calibrated Swiss terrain parameters.

## Hazard-Statistics Pilot

`validation/cases/swissalti3d_hazard_statistics_pilot.yaml` enables full
source-area trajectory output and declares additive hazard-layer thresholds:

```yaml
hazard_layers:
  statistics:
    kinetic_energy_exceedance_j: [5.0, 10.0]
    jump_height_exceedance_m: [0.05, 0.10]
    velocity_exceedance_mps: [0.5, 1.0]
```

After running the validation case, build the hazard products with:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml \
  --output-dir hazard/results/swissalti3d_hazard_statistics \
  --cell-size 2
```

The resulting exceedance rasters are trajectory-level threshold exceedance
probabilities. They are closer to RAMMS-like intensity map interpretation than
max-only diagnostic layers, but they are still research fixtures and not
operational Swiss hazard products.

## Boundaries

This pilot deliberately does not:

- download swisstopo data;
- commit raw swissALTI3D, SWISSIMAGE, or other large geodata products;
- add GDAL or GeoTIFF/COG support to the Rust core;
- implement full source-zone generation from slope, geology, forest, or inventory masks;
- derive terrain/material classes from GeoCover, Geological Atlas, forest, or field calibration products;
- produce operational hazard or risk maps.

The next step after this pilot should be a manually supplied real swissALTI3D crop with the same metadata sidecar, followed by CRS-bearing hazard-layer export and source-zone derivation from documented terrain/geology criteria.
