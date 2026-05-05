# Tschamut/swissALTI3D Controlled Pilot Plan

Status: execution plan for Work Package 1 from
`current_state_gap_analysis_next_directions.md`. This document defines a
controlled local/private pilot. It does not implement new physics, tune
parameters, change defaults, add shape models, add GeoTIFF export, or add
trajectory Parquet.

## Purpose

The current checked-in Tschamut validation under-runs observed mean runout by
tens of metres on a public-derived proxy terrain. The controlled pilot asks a
narrow question:

```text
Does the Tschamut under-run persist when the proxy terrain is replaced by a
real, provenance-tracked swissALTI3D-style DEM crop and explicit source-area
metadata?
```

The pilot compares:

- `translational_v0`: current default baseline;
- `sphere_rotational_v1`: recommended opt-in contact model for trajectory and
  contact experiments.

No parameters may be tuned during this pilot. The result is a diagnostic
workflow outcome, not operational validation.

## Required Private Inputs

Prepare these files outside git, preferably under a local path such as:

```text
validation/private/tschamut_swissalti3d/input/
```

That directory is for local/private work only. Do not stage raw DEMs, raw
swisstopo products, or generated pilot outputs.

Required files:

1. `tschamut_swissalti3d_crop.asc`
   - ESRI ASCII DEM crop derived from a manually supplied swissALTI3D or
     swissALTI3D-compatible bare-earth DEM.
   - Horizontal coordinates in metres.
   - Elevations in metres.
   - Header must contain `ncols`, `nrows`, `xllcorner`, `yllcorner`,
     `cellsize`, and `NODATA_value`.
2. `tschamut_swissalti3d_terrain_metadata.yaml`
   - Terrain-source metadata sidecar following the Swiss terrain contract in
     `swiss_terrain_ingestion_pilot.md`.
3. `tschamut_release_zone.yaml`
   - Release-zone/source-area metadata sidecar with a polygon in the same CRS as
     the DEM and deterministic sampling settings.

Optional file:

4. `tschamut_terrain_classes.yaml`
   - Terrain/material-class metadata sidecar referencing an aligned categorical
     ESRI ASCII class grid.
   - Use only if the class map is provenance-tracked. Do not invent calibrated
     terrain classes for this pilot.

## CRS And Height Reference

Required CRS and vertical datum:

- horizontal CRS: LV95 / EPSG:2056;
- vertical datum: LN02;
- coordinate units: metres;
- height units: metres.

The preparation script rejects incompatible CRS/datum metadata. If source data
arrive in another CRS or height reference, preprocess them outside the
repository and record the transformation in the terrain metadata sidecar before
running the pilot.

## DEM Crop Requirements

The DEM crop should be small enough for local iteration but large enough to
contain:

- all release-zone polygon vertices;
- the expected downslope runout corridor;
- observed deposition points used by the current Tschamut validation subset;
- a margin around the expected trajectory envelope so clamped edge behavior does
  not dominate the result.

Recommended first crop:

- use a single connected local slope/runout domain, not an entire valley;
- use the native swissALTI3D crop resolution when feasible, or a documented
  resampling to a fixed cell size such as `2 m` or `5 m`;
- avoid nodata holes inside the release zone and main runout corridor;
- record source tile ids, original filename, preprocessing command or manual
  steps, resolution, extent, nodata value, and checksum where possible.

Do not crop by looking at simulated outputs. Define the crop from observed
release/deposition context and terrain coverage before running the simulator.

## Release-Zone Requirements

The release-zone sidecar must define:

- `schema_version`;
- `source_zone_id`;
- EPSG `2056` and vertical datum `LN02`;
- polygon vertices inside the DEM extent;
- deterministic sampling mode;
- requested release-point count;
- seed;
- source/provenance/license notes.

For the first pilot, use deterministic grid sampling. The release zone should be
defined from public Tschamut release context, field notes, or transparent
manual interpretation. It must not be adjusted after seeing model runout.

## Optional Terrain-Class Requirements

Terrain classes are allowed only as an opt-in comparison if the class raster and
metadata are already available and auditable.

Requirements:

- same EPSG, vertical datum, extent, resolution, dimensions, and nodata policy as
  the DEM crop;
- class IDs and names documented in metadata;
- any parameter overrides explicitly listed;
- clear note that classes are not calibrated to Tschamut observations unless a
  separate calibration experiment is later designed.

The baseline pilot should first run without terrain classes or with clearly
documented global-equivalent classes. A terrain-class variant may be added only
as a separate comparison.

## Pre-Flight Checklist

Before generating runnable cases, confirm:

- DEM header contains `ncols`, `nrows`, `xllcorner`, `yllcorner`, `cellsize`,
  and `NODATA_value`;
- terrain metadata uses EPSG:2056, vertical datum `LN02`, metre coordinate
  units, and metre height units;
- terrain metadata extent, resolution, dimensions, and nodata match the DEM
  header;
- release-zone polygon vertices are inside the DEM extent;
- optional terrain-class raster has the same CRS, extent, resolution,
  dimensions, and nodata policy as the DEM;
- private inputs, generated cases, validation outputs, and hazard outputs are
  all under ignored paths;
- no restitution, friction, roughness, scarring, terrain-class, block,
  release-velocity, or release-zone parameter has been tuned after seeing
  results;
- validation and hazard manifests will be reviewed before interpreting metrics
  or maps.

## Output And Ignored-Data Policy

Generated local cases:

```text
validation/private/tschamut_swissalti3d/cases/
```

Generated validation outputs:

```text
validation/results/tschamut_swissalti3d_private/
```

Generated hazard outputs:

```text
hazard/results/tschamut_swissalti3d_baseline/
hazard/results/tschamut_swissalti3d_rotational/
```

All three locations are local/generated or private-output locations. They must
remain ignored unless a future task explicitly adds tiny synthetic fixtures.
Never commit:

- raw swissALTI3D or other swisstopo products;
- private terrain crops;
- generated private validation cases;
- generated trajectory/impact/hazard outputs;
- derived visual reports containing private geodata.

## Prepare Runnable Cases

Baseline and rotational cases are generated from checked-in templates by:

```bash
python3 scripts/prepare_tschamut_swissalti3d_pilot.py \
  --dem-path validation/private/tschamut_swissalti3d/input/tschamut_swissalti3d_crop.asc \
  --terrain-metadata validation/private/tschamut_swissalti3d/input/tschamut_swissalti3d_terrain_metadata.yaml \
  --release-zone-metadata validation/private/tschamut_swissalti3d/input/tschamut_release_zone.yaml \
  --case-dir validation/private/tschamut_swissalti3d/cases \
  --results-dir validation/results/tschamut_swissalti3d_private \
  --ensemble-size 6 \
  --seed 34014 \
  --force
```

If an optional terrain-class sidecar is used, add:

```bash
  --terrain-classes-metadata validation/private/tschamut_swissalti3d/input/tschamut_terrain_classes.yaml
```

Expected generated cases:

```text
validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml
validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml
```

## Run Validation Cases

Run the baseline:

```bash
cargo run -- validate \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml
```

Run the opt-in rotational comparison:

```bash
cargo run -- validate \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml
```

Run the current proxy controls for context:

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
```

These commands should complete without changing any defaults and without
touching checked-in validation cases.

## Build Hazard Layers With Explicit Grid

Use an explicit grid derived from the private DEM header:

```text
--grid-xmin       = DEM xllcorner or converted lower-left x
--grid-ymin       = DEM yllcorner or converted lower-left y
--grid-ncols      = DEM ncols
--grid-nrows      = DEM nrows
--grid-cell-size  = DEM cellsize
```

Example placeholders:

```bash
GRID_XMIN=<dem_xllcorner>
GRID_YMIN=<dem_yllcorner>
GRID_NCOLS=<dem_ncols>
GRID_NROWS=<dem_nrows>
GRID_CELL_SIZE=<dem_cellsize>
```

Baseline hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_baseline.yaml \
  --output-dir hazard/results/tschamut_swissalti3d_baseline \
  --grid-xmin "$GRID_XMIN" \
  --grid-ymin "$GRID_YMIN" \
  --grid-ncols "$GRID_NCOLS" \
  --grid-nrows "$GRID_NROWS" \
  --grid-cell-size "$GRID_CELL_SIZE" \
  --no-plots
```

Rotational hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/private/tschamut_swissalti3d/cases/tschamut_swissalti3d_rotational.yaml \
  --output-dir hazard/results/tschamut_swissalti3d_rotational \
  --grid-xmin "$GRID_XMIN" \
  --grid-ymin "$GRID_YMIN" \
  --grid-ncols "$GRID_NCOLS" \
  --grid-nrows "$GRID_NROWS" \
  --grid-cell-size "$GRID_CELL_SIZE" \
  --no-plots
```

For a selected QA run only, omit `--no-plots` to generate PNG/HTML diagnostic
reports. Do not use plotted mode for routine benchmark or production-style
runs.

## Manifest And Provenance Checks

After validation, inspect:

```text
validation/results/tschamut_swissalti3d_private/validation_tschamut_swissalti3d_baseline_manifest.json
validation/results/tschamut_swissalti3d_private/validation_tschamut_swissalti3d_rotational_manifest.json
```

Required checks:

- `schema_version` is `run_manifest_v1`;
- `model_version`, git hash, config fingerprint, case id, and seed policy are
  present;
- terrain source records private DEM path, metadata path, EPSG `2056`, vertical
  datum `LN02`, extent, resolution, nodata, source dataset, and provenance;
- optional checksums match metadata when provided;
- release-zone section records metadata path, source-zone id, polygon extent,
  generated point count, sampling mode, seed, and CRS;
- optional terrain-class section records class-grid path, class ids, coverage
  histogram, and provenance;
- output section records trajectory/deposition/impact paths, file counts, row
  counts, and bytes;
- warnings are reviewed and explained.

After hazard-layer generation, inspect each hazard manifest:

```text
hazard/results/tschamut_swissalti3d_baseline/validation_tschamut_swissalti3d_baseline_manifest.json
hazard/results/tschamut_swissalti3d_rotational/validation_tschamut_swissalti3d_rotational_manifest.json
```

Required checks:

- grid source is `explicit`;
- grid extent and cell size match the DEM metadata;
- generated layer names include reach, deposition, max energy, max jump height,
  significant impact density when impacts exist, and configured exceedance
  layers;
- `plots_enabled` is `false` for production-style runs;
- warnings do not indicate missing full ensemble trajectory inputs.

## Metrics To Compare

From validation diagnostics JSON:

- `observed_mean_runout_m`;
- `simulated_mean_runout_m`;
- `runout_distance_error_m`;
- `deposition_centroid_error_m`;
- `deposition_cloud_mean_nearest_error_m`;
- `deposition_cloud_overlap_fraction`;
- `lateral_spread_error_m`;
- `release_zone_mean_runout_m`;
- `release_zone_max_runout_m`;
- `validation_release_count` or `release_zone_point_count`;
- `validation_simulated_trajectory_count` when present.

From hazard layers:

- reach-probability envelope;
- deposition-density footprint;
- maximum kinetic-energy hotspots;
- maximum jump-height hotspots;
- kinetic-energy, jump-height, and velocity exceedance layers;
- significant-impact density if impact events are available.

From manifests:

- contact model;
- terrain metadata/provenance;
- release-zone metadata/provenance;
- terrain-class configuration if present;
- trajectory and impact row counts;
- timing and output-size diagnostics.

## Visual QA

Before interpreting metrics:

1. Plot or inspect the DEM crop and release-zone polygon.
2. Confirm observed deposition points fall inside or near the DEM crop and not
   on nodata.
3. Confirm generated release points are inside the intended source area.
4. Check hillshade or slope visually against SWISSIMAGE or another legitimate
   local QA layer if available.
5. Inspect reach and deposition rasters over the DEM/hillshade.
6. Check whether high-energy and high-jump cells occur in plausible terrain
   locations rather than at crop edges or nodata boundaries.
7. Confirm no trajectory envelope is dominated by clamped DEM edge behavior.

Visual QA is required because CRS, crop, or release-zone mistakes can produce
plausible-looking metrics with invalid spatial interpretation.

## Comparison Criteria

### Runout And Deposition

Compare real-terrain baseline and rotational results against the existing proxy
Tschamut cases:

- Does `simulated_mean_runout_m` move closer to `observed_mean_runout_m`?
- Does `runout_distance_error_m` decrease?
- Does deposition centroid error decrease?
- Does deposition cloud mean-nearest error decrease?
- Does deposition-cloud overlap increase?
- Does lateral spread become more plausible?

### Reach Envelope

Compare reach-probability rasters:

- Is the reach corridor spatially continuous?
- Does it extend into observed deposition regions?
- Are there disconnected high-probability islands caused by sparse sampling or
  grid/crop artifacts?
- Does `sphere_rotational_v1` materially change reach compared with baseline?

### Energy And Jump Height

Compare energy and jump layers:

- Are maximum kinetic-energy hotspots near steep acceleration zones or early
  impacts?
- Are jump-height hotspots physically plausible and away from DEM edge artifacts?
- Do exceedance layers show coherent corridors rather than isolated single-cell
  spikes?
- Does rotational contact redistribute kinetic energy without creating
  unexplained hotspots?

### Contact-Model Sensitivity

Interpret `sphere_rotational_v1` as an opt-in comparison only:

- Improvement in shape/runout/deposition metrics supports using rotational
  contact for future Tschamut-style experiments.
- Degradation or no change does not invalidate the Chant Sura conclusion; it
  may indicate terrain/source/shape/forest limitations dominate Tschamut.
- No result from this pilot changes the default contact model.

## Interpretation Rules

Use these categories:

### Under-run Improves

If real terrain reduces the runout/deposition bias substantially without
tuning, proxy terrain was a major limitation. Next step: prioritize GIS-ready
hazard outputs and better real-site source/terrain-class documentation before
new physics.

### Under-run Persists

If the under-run remains similar, the dominant limitation is likely not just the
proxy DEM. Candidate explanations: release conditions, block shape, forest or
obstacles, terrain/material parameters, or missing contact physics. Next step:
prioritize shape-aware scaffold or broader Chant Sura/contact validation before
terrain-class calibration.

### Under-run Worsens

If real terrain worsens runout/deposition, check data quality first: CRS,
vertical datum, crop extent, nodata, release-zone placement, and DEM edge
clamping. If those are clean, the result is useful evidence that current global
parameters and equivalent-sphere physics are not transferable to this site.

### Rotational Contact Helps

If `sphere_rotational_v1` improves Tschamut real-terrain metrics without
creating worse energy/jump artifacts, it strengthens the recommendation to use
rotational contact in trajectory and real-site experiments. It still does not
justify changing defaults.

### Rotational Contact Does Not Help

If rotational contact does not improve Tschamut, keep it recommended for Chant
Sura trajectory/contact experiments only. Tschamut may be controlled more by
terrain/source/shape/material effects than by spherical rotational coupling.

## Strict Constraints

- Do not tune restitution, friction, roughness, scarring, terrain classes, block
  radius, block mass, release velocity, or release-zone geometry after looking
  at results.
- Do not change project defaults.
- Do not enable `scarring_contact_v1` in the first baseline/rotational pilot
  unless a separate explicit comparison is later designed.
- Do not commit private DEMs, terrain metadata containing restricted paths if
  that is not acceptable, generated private case files, or generated outputs.
- Do not describe outputs as operational hazard maps.
- Do not describe hazard layers as risk maps.
- Do not infer annual probability or physical occurrence probability from this
  pilot.

## Deliverable After Execution

Once private inputs are available and the pilot is run, create a short results
document with:

- input data inventory and checksums;
- command log;
- manifest/provenance summary;
- baseline vs rotational validation metric table;
- proxy vs real-terrain comparison table;
- selected hazard-layer screenshots or statistics;
- visual QA findings;
- conclusion: under-run improves, persists, or worsens;
- recommended next step: shape scaffold, GIS export, terrain-class calibration
  design, or data-quality correction.

That execution report should remain honest about limitations and should not
claim predictive skill.
