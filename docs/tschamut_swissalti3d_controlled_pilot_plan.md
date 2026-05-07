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
- `sphere_rotational_v1`: opt-in contact-model comparison for this controlled
  pilot and later Tschamut-style testing if evidence supports it.

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

## Pilot Scope And Evidence Gates

M002 defines the controlled-pilot scope and gate inventory only. It does not
authorize tuning, new scripts, report templates, physics changes, default
changes, or committed private/geodata artifacts.

### Scope

The pilot is limited to a controlled real-site comparison between:

- checked-in public/proxy Tschamut cases used as context;
- a private, provenance-tracked swissALTI3D-style DEM crop and release-zone
  sidecar;
- `translational_v0` and `sphere_rotational_v1` using existing documented
  settings.

The pilot may answer whether the proxy-terrain under-run changes under real
terrain. It may not claim operational validation, annual probability,
physical occurrence probability, risk, or equivalence to any proprietary model.

### No-Tuning And Private-Data Boundaries

The pilot is a freeze-before-run exercise:

- freeze DEM crop, release-zone geometry, release sampling settings, block
  settings, contact settings, roughness, scarring, and optional terrain-class
  choices before inspecting pilot metrics or maps;
- do not adjust any of those choices after seeing runout, deposition, energy,
  jump-height, or reach results;
- keep raw swissALTI3D, private DEM crops, generated cases, generated
  validation outputs, generated hazard outputs, and derived private visual
  products out of git;
- record private input paths, source-tile identifiers, CRS, vertical datum,
  preprocessing notes, and checksums in local manifests or sidecars where
  available;
- keep manifests containing private absolute paths, restricted tile
  identifiers, or share-sensitive provenance ignored locally, and redact those
  fields before sharing derived summaries;
- record a non-null processed DEM checksum for each real private crop, or an
  explicit reason why the checksum could not be recorded, so local reruns can
  verify the exact terrain crop where feasible;
- treat optional terrain classes as auditable metadata only, not as calibrated
  Tschamut classes, unless a separate future calibration experiment is designed.

### Gate Inventory

These gates are evidence-completeness checks. They are not runtime pass/fail
budgets and they do not decide whether the model is valid for operations.

| Gate | Evidence required | Go condition | No-go condition |
| --- | --- | --- | --- |
| G1 private-input completeness | DEM crop, terrain metadata, release-zone metadata, and optional terrain-class metadata if used. | Required files exist locally and metadata can be inspected. | Any required private input is missing or undocumented. |
| G2 provenance and CRS completeness | EPSG:2056, LN02, metre units, extent, resolution, nodata, source dataset, source/license notes, preprocessing notes, and checksums where available. | Metadata are complete enough to audit terrain and release-zone provenance. | CRS/datum/extent/resolution/nodata are missing, conflicting, or unauditable. |
| G3 source-zone independence | Release-zone source, polygon, sampling mode, requested count, and seed. | Source-zone choices were defined before seeing pilot outputs. | Source-zone geometry or sampling was adjusted after inspecting results. |
| G4 no-tuning freeze | Frozen settings for contact, block, release, roughness, scarring, and optional terrain classes. | All compared cases use predeclared settings and unchanged defaults. | Any parameter or default was changed to improve Tschamut agreement. |
| G5 manifest completeness | Validation and hazard manifests for baseline and rotational cases. | Manifests record model version, git hash, config fingerprint, seed policy, terrain provenance, release-zone provenance, output paths, row counts, file counts, and warnings. | Manifests are missing or omit provenance, seed, configuration, or output-count evidence. |
| G6 spatial QA completeness | DEM/release-zone inspection, deposition-point coverage, nodata/crop-edge review, reach/deposition review, and energy/jump artifact review. | Spatial QA uses reviewed plot/GIS artifacts or documented manual/GIS inspection, and shows inputs and outputs are interpretable and not dominated by obvious CRS, nodata, or crop-edge errors. | Spatial QA exposes unresolved CRS, datum, nodata, release-zone, or crop-edge problems, or lacks reviewed artifacts and documented manual/GIS inspection. |
| G7 comparison evidence completeness | Proxy context metrics, real-terrain baseline metrics, real-terrain rotational metrics, and hazard-layer summaries. | Enough evidence exists to classify under-run as improved, persistent, worsened, or inconclusive. | Missing metrics or layer summaries prevent a traceable comparison. |
| G8 performance/bottleneck interpretability | Phase timings plus trajectory/deposition/impact/hazard row counts, file counts, and byte counts. | Evidence is sufficient to identify whether the limiting stage appears to be simulation, output writing, or hazard accumulation. These diagnostics are contextual only, not runtime pass/fail budgets. | Timing or output-volume evidence is missing or too coarse to interpret the likely bottleneck. |
| G9 interpretation boundary | Written notes state non-operational status, no tuning, no risk-map claim, no annual-frequency claim, and no proprietary-model equivalence claim. | Interpretation remains diagnostic and scoped to the controlled pilot question. | Interpretation overclaims validation, probability, risk, or proprietary equivalence. |

If any gate is no-go, stop interpretation and record the reason before reruns or
additional comparisons. Fix data/provenance issues without tuning model or
release parameters to observed results.

### Post-Run Gate Review Criteria

M004 defines how to review G1-G9 after a run. The review is a diagnostic
evidence assessment, not a model-validation decision.

Allowed gate statuses:

- `pass`: required evidence is present and interpretable;
- `no-go`: required evidence is absent, contradictory, unauditable, or shows a
  process violation;
- `inconclusive`: evidence exists but is too weak, ambiguous, or confounded for
  interpretation;
- `not-run`: the gate depends on an explicitly optional branch or artifact that
  was not generated, such as optional terrain classes, optional plots, GeoTIFF
  metadata when GeoTIFF export was not requested, or significant-impact density
  when impact events are absent.

Missing required baseline or rotational validation outputs, hazard manifests,
comparison metrics, or visual QA evidence must be marked `no-go`, not
`not-run`.

Every `no-go` or `inconclusive` status must include a short reason, the affected
files or evidence sources where share-safe, and the allowed next action. Reruns
are allowed only to fix data, provenance, command, manifest, output, or QA
process issues. Reruns must not tune restitution, friction, roughness, scarring,
terrain classes, block settings, release velocity, release geometry, or defaults
to improve agreement with observations.

Classify failure modes with one or more of these labels:

- `private_input_provenance_failure`: missing private DEM, sidecar metadata,
  source/license notes, preprocessing notes, or checksum evidence;
- `crs_grid_alignment_failure`: conflicting or missing EPSG:2056/LN02,
  geotransform or affine grid, extent, resolution, nodata, DEM/header, raster
  origin convention (`xllcorner` versus `xllcenter`), lower-left grid origin,
  row order or north-up interpretation, hazard-cell alignment, or hazard grid
  evidence;
- `source_zone_freeze_violation`: release-zone geometry, sampling, seed, or
  source interpretation changed after inspecting results;
- `manifest_output_completeness_failure`: validation or hazard manifests,
  warnings, output paths, actual-vs-expected generated release count, ensemble
  size, trajectory/deposition/impact row and file counts, hazard input rows
  read, or byte counts are missing or inconsistent;
- `visual_qa_failure`: DEM/release-zone, deposition coverage, nodata/crop-edge,
  reach/deposition, energy/jump, or reviewed artifact evidence exposes an
  unresolved spatial interpretation problem;
- `performance_evidence_incomplete`: phase timings or row/file/byte counts are
  missing or too coarse to identify whether simulation, output writing, or
  hazard accumulation is the likely bottleneck, or run context is missing for
  hardware/CPU or thread count where known, plot mode, release count, ensemble
  size, and input/output format;
- `terrain_representation_confounder`: DEM resolution, interpolation,
  smoothing, cliff/nodata handling, vegetation/obstacle omission, or terrain
  classes plausibly dominate the interpretation;
- `comparison_evidence_inconclusive`: proxy, real-terrain baseline,
  real-terrain rotational, or hazard-layer summaries are insufficient to
  classify the under-run outcome;
- `interpretation_boundary_violation`: notes overclaim operational validation,
  risk, annual frequency, physical occurrence probability, proprietary-model
  equivalence, tuning, or default-change implications.

No-go outcomes lead to data/provenance/process fixes, an explicitly documented
rerun, or deferral. They do not justify parameter tuning or broad validation
claims.

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
reports. Do not use plotted mode for routine benchmark or batch diagnostic
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
- `plots_enabled` is `false` for batch diagnostic runs;
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
tuning, proxy terrain and/or source representation likely contributed to the
under-run. Next step: prioritize GIS-ready hazard outputs and better real-site
source/terrain-class documentation before new physics.

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
creating worse energy/jump artifacts, it supports further Tschamut-style
testing with rotational contact. It still does not justify changing defaults or
making broad contact-model recommendations.

### Rotational Contact Does Not Help

If rotational contact does not improve Tschamut, do not generalize from this
pilot. Tschamut may be controlled more by terrain/source/shape/material effects
than by spherical rotational coupling.

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

Once private inputs are available and the pilot is run, create a short
diagnostic results document. M003 defines the report structure only; do not add
report scripts or template files in this milestone.

Required report sections:

- input/provenance inventory: DEM crop source, CRS, vertical datum, extent,
  resolution, nodata, source-tile identifiers where share-safe, preprocessing
  notes, release-zone source, optional terrain classes, and checksums where
  feasible;
- command log: preparation, validation, proxy-control, and hazard-layer
  commands with enough detail to reproduce the local run;
- gate table: G1-G9 status, evidence links or filenames, unresolved no-go
  items, failure-mode labels for every `no-go` and `inconclusive` gate, and
  any stopped interpretation;
- validation manifest summary: model version, git hash, config fingerprint,
  seed policy, contact model, terrain provenance, release-zone provenance,
  warning summary, trajectory/deposition/impact output paths, row counts, file
  counts, and bytes;
- hazard manifest summary: explicit grid parameters, layer names, thresholds,
  plot mode, warnings, output file counts, output bytes, trajectory-input
  completeness, and confirmation that EPSG:2056/LN02, geotransform or affine
  grid, nodata, extent/resolution, and terrain/source provenance carry through
  to hazard outputs or GeoTIFF metadata where applicable;
- metric table: proxy controls, real-terrain baseline, and real-terrain
  rotational values for the validation metrics listed above;
- visual QA notes: DEM/release-zone inspection, deposition-point coverage,
  nodata and crop-edge review, reach/deposition review, and energy/jump
  artifact review, with references to reviewed PNG, HTML, GIS, or QGIS files
  where present, or an explicit statement that no plot/GIS artifacts were
  generated and how QA was performed;
- performance/bottleneck observations: phase timings and row/file/byte counts
  sufficient to interpret whether the main bottleneck appears to be simulation,
  output writing, or hazard accumulation;
- terrain-representation observations: resolution, interpolation, smoothing,
  cliff or nodata handling, terrain-class use or omission, vegetation/obstacle
  visibility, and any observed terrain/source confounders;
- interpretation category: under-run improves, persists, worsens, or remains
  inconclusive, with the evidence used for that classification;
- next-step decision: data-quality correction, pilot rerun, GIS packaging,
  terrain/source semantics work, terrain-class calibration design, shape/contact
  testing, or pause;
- limitations: no tuning, no private-data release, no operational validation,
  no risk-map claim, no annual-frequency claim, no proprietary-model
  equivalence claim, and no default change.

The report is a diagnostic evidence summary, not a validation certificate.
Shareable versions must omit raw data, private absolute paths, restricted tile
identifiers, and share-sensitive provenance. Keep private manifests and visual
products ignored locally or redact them before sharing.
