# DEM And Terrain-Representation Sensitivity Benchmark

Status: dry-runnable fixture benchmark plus selected Tschamut public-pilot
gate. The checked-in dry run derives deterministic terrain variants from a
tiny public swissALTI3D-style DEM fixture and writes map-difference diagnostics
to a user-provided output directory. The selected Tschamut mode validates the
fixed geodata manifest and source/scenario policy, then either writes the same
terrain-variant diagnostics when the ignored processed DEM exists locally or a
share-safe `blocked_missing_processed_dem` report when it does not. It does not
run private data, tune parameters, select physics, change defaults, or claim
operational validation.

## Purpose

The benchmark should distinguish DEM and terrain-representation effects from
physics or parameter tuning. It should answer whether runout, deposition, and
hazard-layer patterns change because of terrain source, resolution, alignment,
interpolation, nodata, or terrain-class representation while the simulator,
source-zone policy, block/scenario metadata, and seeds remain fixed.

## Compared Terrain Representations

Candidate representations should be predeclared before execution:

| Variant | Input | Purpose | Notes |
| --- | --- | --- | --- |
| Synthetic/control baseline | Analytic terrain or tiny checked-in DEM fixture | Dry-runnable control for command, manifest, and reducer behavior | Must be public and fixture-sized. |
| Public Tschamut proxy | Current public-derived Tschamut proxy terrain | Compare current proxy behavior against alternative representations | No private data; remains diagnostic. |
| Native private swissALTI3D | Private Tschamut/swissALTI3D crop when available | Test real bare-earth terrain representation | Must remain outside git and use LV95/LN02 or recorded transforms. |
| Coarsened resolutions | Same source terrain resampled to declared cell sizes | Isolate resolution effects | Use same extent and source-zone/release cells where possible. |
| Interpolation/resampling methods | Nearest, bilinear, cubic, mean/aggregate, or another predeclared method | Isolate interpolation or aggregation effects | Method must be recorded before execution. |
| Smoothing/no-smoothing | Raw versus declared smoothing kernel/window | Isolate smoothing or micro-topography effects | Smoothing is preprocessing, not tuning to results. |
| Cliff/nodata variants | Declared nodata masks, clipped extents, or cliff-edge handling | Isolate edge and nodata handling effects | Interpolation across nodata is forbidden unless declared separately. |
| Terrain-class/raster alignment | Optional aligned categorical raster variant | Test representation/alignment of class rasters | Active physics parameters and class-to-parameter mapping stay fixed. |

Private swissALTI3D crops, raw swisstopo tiles, and generated private outputs
must remain ignored. Public/proxy and synthetic variants should stay clearly
separated from private real-site evidence.

The current dry-runnable fixture uses:

- source DEM: `validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc`;
- baseline variant: byte-preserved source DEM copy;
- smoothing variant: 3x3 valid-cell mean with source nodata preserved;
- coarsening variant: 2x2 valid-cell mean, reexpanded to the source grid;
- output contract: same extent, dimensions, cell size, row order, and nodata
  value for all variants.

The selected public Tschamut gate uses:

- geodata manifest:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`;
- fixed source-zone/block-scenario policy:
  `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`;
- expected ignored processed DEM:
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc`;
- fixed source inputs: source zone `tschamut_public_lps_release_bbox`, ten
  deterministic release cells, and three representative block scenarios;
- sampling semantics: conditional sampling only, with annual/source-frequency
  and physical-probability semantics unsupported.

## Invariants

Each comparison must keep these fixed unless the report explicitly declares a
separate experiment:

- source-zone polygon and deterministic release cells;
- block/scenario metadata labels and active simulated block parameters;
- random seeds, trajectory ids, and release-cell ids;
- simulation configuration and contact model;
- hazard grid, thresholds, and probability/weighting semantics;
- output selection and plot mode where possible;
- no restitution, friction, roughness, scarring, terrain-class, source-zone, or
  release-condition tuning after inspecting results.

Terrain-class variants may vary only as representation/alignment inputs while
the active physics parameters and class-to-parameter mapping remain fixed. If a
class definition or parameter mapping changes, that is a separate
physics/material experiment, not a DEM/terrain-representation sensitivity run.

Do not tune contact parameters to compensate for DEM effects. A sensitivity
finding should lead to terrain/provenance/alignment review, uncertainty
reporting, or a separate predeclared experiment, not hidden restitution,
friction, roughness, scarring, or release-condition adjustment.

## Required Metadata

Every terrain representation should record:

- horizontal CRS/EPSG and vertical datum. Private Tschamut/swissALTI3D variants
  require LV95 / EPSG:2056 and LN02, or a recorded transform if source data are
  not already in that frame;
- extent, cell size, dimensions, nodata value, and row order/origin convention;
- affine/geotransform or ESRI ASCII header interpretation. For ESRI ASCII,
  verify `xllcorner`/`yllcorner` as the lower-left outer cell corner, first data
  row as the north/top row, and cell-center sampling;
- resampling or coarsening method, if any;
- source dataset, source path or tile ids where share-safe, license, and
  provenance notes;
- processed checksums where feasible, or a recorded reason if absent;
- terrain-class raster alignment, class metadata, and nodata policy when used;
- private-data exclusion and redaction notes for shareable reports.

swisstopo inputs are operational geodata for terrain representation, not
validation evidence by themselves.

Allowed resampling/coarsening behavior:

- record the method and parameters before running;
- propagate nodata masks through derived terrain products;
- do not interpolate across nodata unless it is explicitly documented as a
  separate preprocessing experiment;
- mark release cells or hazard cells touching nodata as no-go, or explicitly
  exclude/mask them before interpretation.

## Metrics And Observations

The dry-runnable fixture writes
`dem_terrain_sensitivity_summary.json` with:

- schema version, source DEM path/checksum/header, and variant metadata;
- invariant/no-tuning notes;
- baseline-versus-variant metrics: compared cell count, mean elevation delta,
  mean absolute elevation delta, maximum absolute elevation delta, elevation
  RMSE, slope-proxy mean/max/RMSE delta, and nodata mismatch count.

Real-site benchmark reports should additionally compare:

- runout summaries: mean, median, extrema, selected quantiles, and runout error
  against available observations where appropriate;
- deposition summaries: centroid, spread, overlap, nearest-neighbour distance,
  and deposition-density footprint;
- hazard-layer map differences: reach, deposition, maximum kinetic energy,
  maximum jump height, threshold exceedance layers, and significant-impact
  density where impact events exist;
- per-layer deltas and spatial disagreement between terrain representations;
- visual QA: DEM/hillshade, source-zone, release-cell, observed-deposition, and
  hazard-raster alignment review;
- timing and output-volume context: phase timings, row counts, file counts,
  bytes, plot mode, release count, ensemble size, and input/output format.

If observations are included, they are diagnostic context only. They do not
create validation pass/fail evidence, calibrated skill, or operational
acceptance unless a separate validation milestone defines that role and
holdout/tuning boundary.

## Acceptance And Gates

The benchmark can be interpreted only when these gates pass:

- deterministic rerun parity for the same terrain representation and seed;
- manifest completeness for terrain, source-zone, scenario, simulation, hazard
  grid, thresholds, output counts, timings, and checksums/provenance;
- CRS, vertical-datum, grid-alignment, nodata, row-order, and hazard-cell
  alignment checks;
- visual QA shows no unresolved crop-edge, nodata, release-zone, or alignment
  artifact dominating the result;
- no operational validation, annual-frequency, physical-probability, or risk
  claims;
- no physics selection or default recommendation unless the sensitivity
  classification is stable across representations and explicitly reviewed in a
  later milestone.

No-go outcomes should lead to data/provenance/alignment fixes, a documented
rerun, or deferral, not parameter tuning.

Gate statuses:

- `pass`: required evidence is complete and interpretable;
- `no-go`: required data, metadata, alignment, manifest, or QA evidence is
  missing, contradictory, or affected by forbidden tuning;
- `inconclusive`: evidence is present but insufficient to classify sensitivity;
- `not-run`: only for optional variants that were not requested.

## Minimum Dry-Run Or Real-Site Recipe

Dry-runnable public fixture:

```bash
OUT_DIR="$(mktemp -d)"
python3 scripts/run_dem_terrain_sensitivity.py --output-dir "$OUT_DIR"
```

Optional explicit DEM path:

```bash
OUT_DIR="$(mktemp -d)"
python3 scripts/run_dem_terrain_sensitivity.py \
  --source-dem validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc \
  --output-dir "$OUT_DIR"
```

Selected Tschamut public-pilot gate from a clean checkout:

```bash
OUT_DIR="$(mktemp -d)"
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py \
  --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml \
  --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml \
  --allow-missing-source-dem \
  --output-dir "$OUT_DIR"
```

When the ignored processed DEM is absent, this command writes a no-go
`blocked_missing_processed_dem` summary and report. That status is a
reproducibility blocker, not a model result. After running the public geodata
preparation command from the manifest, rerun the same command without
`--allow-missing-source-dem` to generate comparable baseline, smoothing, and
coarsening terrain variants from the selected Tschamut DEM.

Expected dry-run outputs under the user-provided or temp directory:

```text
terrain_variants/baseline.asc
terrain_variants/smooth_3x3_mean.asc
terrain_variants/coarsen_2x2_mean_reexpanded.asc
dem_terrain_sensitivity_summary.json
dem_terrain_sensitivity_report.md
```

The report includes terrain representation inventory, invariant configuration,
command log, metric comparison table, gate table, limitations, and an explicit
warning not to tune contact parameters to compensate for DEM effects.

Real-site expected inputs:

- baseline case or case template;
- terrain representation inventory and metadata sidecars;
- fixed source-zone/release-cell table;
- fixed block/scenario metadata;
- fixed random seed and simulation configuration;
- fixed hazard grid and threshold configuration;
- optional observation tables for diagnostic context only.

Ignored output root:

```text
validation/results/dem_terrain_sensitivity/
hazard/results/dem_terrain_sensitivity/
```

Real-site command/report placeholders:

```text
prepare terrain variants: UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --output-dir <ignored-output-dir>
run validation cases:    deferred to the small frozen conditional pilot gate
build hazard layers:     deferred to the small frozen conditional pilot gate
write report:            <ignored-output-dir>/dem_terrain_sensitivity_report.md
```

Paired output modes:

- no-plot batch diagnostic outputs for comparable timings and file counts;
- selected plot/GIS QA outputs for representative variants only;
- CSV/ASCII parity outputs for every hazard raster;
- GeoTIFF outputs where explicitly requested and metadata-complete.

Minimum report gate table:

| Gate | Status | Required note |
| --- | --- | --- |
| Deterministic rerun parity | `pass` / `no-go` / `inconclusive` | Same inputs and seed reproduce manifests and key summaries. |
| Manifest completeness | `pass` / `no-go` / `inconclusive` | Terrain, scenario, output, timing, checksum, and provenance fields reviewed. |
| CRS/grid/nodata alignment | `pass` / `no-go` / `inconclusive` | EPSG/datum, transform, row order, nodata, and hazard-cell alignment reviewed. |
| Variant invariants | `pass` / `no-go` / `inconclusive` | Source, scenario, seed, physics, hazard grid, thresholds, and outputs stayed fixed. |
| Visual QA | `pass` / `no-go` / `inconclusive` | Artifacts or manual/GIS inspection notes reviewed. |
| Interpretation boundary | `pass` / `no-go` | No tuning, operational validation, annual-frequency, physical-probability, or risk claim. |

## Real-Site Report Sections

The dry-run script already writes a compact report template. A later real-site
extension should add these sections:

- terrain representation inventory;
- invariant configuration table;
- command log or dry-run plan;
- manifest and provenance summary;
- alignment and visual QA findings;
- runout/deposition metric comparison;
- hazard-layer difference summary;
- timing and output-volume context;
- sensitivity classification and uncertainty notes;
- gate table and no-go/inconclusive reasons;
- next-step decision and limitations.
