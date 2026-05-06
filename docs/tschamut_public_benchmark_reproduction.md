# Tschamut Public Benchmark Reproduction

Status: registration-reviewed public-data reproduction workflow. This document
records a transparent benchmark reproduction using public Tschamut 2014
observations, public swissALTI3D terrain, and the current simulator/hazard
workflow. It is not an operational hazard assessment, not a calibration
exercise, and not a claim of equivalence to any proprietary rockfall model.

## Scope

The workflow answers a narrow question:

> Does the existing uncalibrated spherical-block model behave differently when
> the Tschamut validation subset is run on a public swissALTI3D terrain crop
> instead of the repository's LPS-derived terrain proxy?

It does not tune restitution, friction, roughness, scarring, terrain classes, or
release parameters after seeing results. It compares:

- `translational_v0` baseline;
- `sphere_rotational_v1`;
- existing proxy-terrain Tschamut controls.

The first executed run uses the same first 10 public LPS trajectories as the
checked-in Tschamut validation subset so the real-terrain and proxy-terrain
comparisons are directly comparable. This report also includes an expanded
25-run public subset to check whether the 10-run conclusion is stable.

## Public Inputs

| Input | Source | Use | License/provenance |
| --- | --- | --- | --- |
| Tschamut 2014 observations | EnviDat `tschamut2014`, DOI <https://doi.org/10.16904/envidat.34> | release points, deposition points, slope scan bridge | ODbL with DbCL, as recorded in `data/datasets.yaml` |
| Tschamut slope scan | EnviDat resource `Tschamut2014_Slope+BlockScans`, file `DEM_Tschamut.xyz` | bridge from local LPS coordinates to Swiss projected coordinates | same EnviDat record |
| Tschamut LPS trajectories | EnviDat resource `trajectoriesfromlps.zip` | public release/deposition rows and runout metrics | same EnviDat record |
| swissALTI3D tile | swisstopo public tile `swissalti3d_2019_2696-1167_2_2056_5728.tif` | public 2 m bare-earth DEM crop | swisstopo open data terms |

The EnviDat metadata page states that the 2014 campaign threw six 20-80 kg
blocks 111 times near Tschamut/Oberalppass and provides slope/block scans,
overview tables, LPS trajectories, and jump/impact resources. The linked
publication is Volkwein et al. 2018, *Repetitive Rockfall Trajectory Testing*,
Geosciences 8(3), 88, DOI <https://doi.org/10.3390/geosciences8030088>.

swissALTI3D is distributed in LV95/LN02, with 1 km by 1 km tiles and 2 m COG
files suitable for this small benchmark crop.

## Preprocessing Workflow

Script:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py --padding-m 250 --force
```

The same script supports larger controlled subsets:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py \
  --output-root validation/results/tschamut_public_benchmark_25 \
  --run-limit 25 \
  --padding-m 250 \
  --force
```

It also supports explicit deterministic run filters with `--run-ids`, for
example `--run-ids v004,v005,v006`. The preparation manifest records the
selection mode, selected trajectory IDs, available shared run count, block-ID
counts, and mass/radius summary.

For passive block-shape provenance checks, generate a single-block package and
attach the matching public `shape_metadata_v1` sidecar:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py \
  --output-root validation/results/tschamut_public_block1_shape \
  --block-id 1 \
  --run-limit 3 \
  --block-shape-metadata data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml \
  --force
```

The sidecar is passive. It records Tschamut block mass/dimension provenance in
manifests and trajectory metadata, but it does not change contact physics,
parameters, or validation semantics. Mixed-block benchmark packages should not
receive a single block-shape sidecar.

The preparation script uses `numpy`, `Pillow`, `pyproj`, `PyYAML`, and
`scipy.spatial.cKDTree` for GeoTIFF cropping, LV03-to-LV95 projection, YAML
metadata, and registration QA.

Generated ignored package:

```text
validation/results/tschamut_public_benchmark/
  input/
    release_points_lv95.csv
    observed_deposition_lv95.csv
    tschamut_public_swissalti3d_crop.asc
    tschamut_public_swissalti3d_metadata.yaml
    tschamut_public_release_zone.yaml
    registration_qa.json
    registration_lps_scan_overlay.svg
    release_deposition_crop_overlay.svg
  cases/
    tschamut_public_benchmark_baseline.yaml
    tschamut_public_benchmark_rotational.yaml
  validation/
    validation_tschamut_public_benchmark_* outputs
  preparation_manifest.json
```

The script downloads public raw resources into ignored caches if absent:

- `data/raw/tschamut2014/geosciences-08-00088-s001.zip`
- `data/raw/tschamut2014/trajectoriesfromlps.zip`
- `data/raw/swisstopo/swissalti3d_2019_2696-1167_2_2056_5728.tif`

The terrain crop is a 2 m ESRI ASCII grid derived by integer-window cropping
from the swissALTI3D COG. For this run:

| Field | Value |
| --- | ---: |
| `ncols` | 300 |
| `nrows` | 304 |
| `xllcorner` | 2696376 |
| `yllcorner` | 1167384 |
| `cellsize` | 2 |
| `NODATA_value` | -9999 |
| processed crop SHA-256 | `36f3156bbc57a01536784807a09db214a46911b4df95c04af8182e420973ea8f` |

For the 25-run expanded subset:

| Field | Value |
| --- | ---: |
| `ncols` | 304 |
| `nrows` | 309 |
| `xllcorner` | 2696368 |
| `yllcorner` | 1167382 |
| `cellsize` | 2 |
| `NODATA_value` | -9999 |

Coordinate transform:

```text
scan_surface_fit_v1
LV03 E offset = 696598.753 m
LV03 N offset = 167499.232 m
vertical offset for processed local z = 1600.000 m
```

The default transform is intentionally transparent and auditable. It fits a 2D
translation between the public LPS-splined terrain-height samples (`xs`, `ys`,
`zs`) and the public CH1903 slope scan by minimizing vertical residuals to the
nearest scan point. It then uses `pyproj` to transform LV03 coordinates to LV95.
No simulated trajectory outputs or model metrics are used in the registration.

Two fallback/comparison transforms remain available in the preparation script:

- `bbox_align_v1`: the first-pass lower-left bounding-box alignment;
- `overview_offset_v1`: the public `OverviewAllTests.txt` tachymeter offset
  (`696608/167635/1600`), which applies to overview tachymeter coordinates and
  does not align the LPS-splined rows well.

Registration QA against the public slope scan:

| Transform | Mean nearest horizontal residual (m) | P95 horizontal residual (m) | Vertical RMSE (m) | P95 absolute vertical residual (m) |
| --- | ---: | ---: | ---: | ---: |
| `scan_surface_fit_v1` | 0.485 | 1.507 | 0.517 | 1.117 |
| `bbox_align_v1` | 2.603 | 13.532 | 11.401 | 19.380 |
| `overview_offset_v1` | 76.716 | 129.924 | 26.933 | 42.946 |

This is a substantial improvement over the first-pass bbox transform. It is
still a terrain-scan registration, not a surveyed control-point adjustment.

## Commands Run

Validation:

```bash
cargo run -- validate --case validation/results/tschamut_public_benchmark/cases/tschamut_public_benchmark_baseline.yaml
cargo run -- validate --case validation/results/tschamut_public_benchmark/cases/tschamut_public_benchmark_rotational.yaml
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
```

Hazard layers, explicit grid, plots disabled:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark/cases/tschamut_public_benchmark_baseline.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_baseline \
  --grid-xmin 2696376 \
  --grid-ymin 1167384 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2 \
  --no-plots

python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark/cases/tschamut_public_benchmark_rotational.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_rotational \
  --grid-xmin 2696376 \
  --grid-ymin 1167384 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2 \
  --no-plots
```

Expanded 25-run validation and hazard commands:

```bash
cargo run -- validate --case validation/results/tschamut_public_benchmark_25/cases/tschamut_public_benchmark_baseline.yaml
cargo run -- validate --case validation/results/tschamut_public_benchmark_25/cases/tschamut_public_benchmark_rotational.yaml

python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark_25/cases/tschamut_public_benchmark_baseline.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_25_baseline \
  --grid-xmin 2696368 \
  --grid-ymin 1167382 \
  --grid-ncols 304 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots

python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark_25/cases/tschamut_public_benchmark_rotational.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_25_rotational \
  --grid-xmin 2696368 \
  --grid-ymin 1167382 \
  --grid-ncols 304 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots
```

QA plot generated locally under ignored outputs:

```text
hazard/results/tschamut_public_benchmark_qa/terrain_release_deposition_qa.png
validation/results/tschamut_public_benchmark/input/registration_lps_scan_overlay.svg
validation/results/tschamut_public_benchmark/input/release_deposition_crop_overlay.svg
```

## Manifest Review

Validation and hazard manifests record:

- `schema_version: run_manifest_v1`;
- model version `0.6.0`;
- EPSG `2056`, CRS `CH1903+ / LV95`, vertical datum `LN02`;
- terrain source `swisstopo_swissalti3d`;
- crop extent, 2 m resolution, nodata value, source URL, license note, raw and
  processed checksums;
- preparation manifest transform method, offsets, and registration QA residuals;
- deterministic seed `34014` and ensemble size `6`;
- no-plot hazard generation with explicit grid source.

The hazard manifests now carry the same terrain provenance as validation
manifests when `terrain.metadata_path` is present.

## Validation Metrics

### Ten-Run Subset

| Case | Terrain | Contact model | Simulated mean runout (m) | Observed mean runout (m) | Runout error (m) | Deposition centroid error (m) | Cloud nearest error (m) | Overlap fraction |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Public real-terrain baseline | swissALTI3D 2 m crop | `translational_v0` | 72.447 | 102.844 | 30.396 | 29.973 | 23.443 | 0.867 |
| Public real-terrain rotational | swissALTI3D 2 m crop | `sphere_rotational_v1` | 200.375 | 102.844 | 97.532 | 98.261 | 76.186 | 0.000 |
| Proxy baseline control | LPS-derived terrain proxy | `translational_v0` | 71.702 | 102.844 | 31.142 | 31.018 | 23.882 | 0.917 |
| Proxy basic control | LPS-derived terrain proxy | `translational_v0` | 71.773 | 102.844 | 31.070 | 30.963 | 23.751 | 0.950 |

### Twenty-Five-Run Subset

The expanded subset uses the first 25 shared processed public LPS runs:
`v004`, `v005`, `v006`, `v007`, `v011`, `v014`, `v015`, `v017`, `v018`,
`v019`, `v020`, `v021`, `v022`, `v023`, `v024`, `v025`, `v026`, `v027`,
`v028`, `v029`, `v030`, `v031`, `v032`, `v033`, and `v034`.

Block coverage:

| Block ID | Count | Mass (kg) |
| --- | ---: | ---: |
| 1 | 11 | 69 |
| 2 | 7 | 79 |
| 4 | 7 | 40 |

| Case | Contact model | Simulated mean runout (m) | Observed mean runout (m) | Runout error (m) | Deposition centroid error (m) | Cloud nearest error (m) | Overlap fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Public real-terrain baseline, 25 runs | `translational_v0` | 67.532 | 97.375 | 29.843 | 29.337 | 23.945 | 0.813 |
| Public real-terrain rotational, 25 runs | `sphere_rotational_v1` | 200.632 | 97.375 | 103.257 | 103.830 | 78.276 | 0.000 |

Per-block mean runout comparison for the 25-run subset:

| Contact model | Block ID | Runs | Observed mean (m) | Simulated mean (m) | Signed error (m) |
| --- | --- | ---: | ---: | ---: | ---: |
| `translational_v0` | 1 | 11 | 103.878 | 65.251 | -38.627 |
| `translational_v0` | 2 | 7 | 95.014 | 66.442 | -28.572 |
| `translational_v0` | 4 | 7 | 89.517 | 72.207 | -17.310 |
| `sphere_rotational_v1` | 1 | 11 | 103.878 | 200.799 | 96.921 |
| `sphere_rotational_v1` | 2 | 7 | 95.014 | 200.041 | 105.028 |
| `sphere_rotational_v1` | 4 | 7 | 89.517 | 200.960 | 111.443 |

Classification for this 10-run subset:

- baseline under-run **persists** on the public swissALTI3D crop, but no longer
  worsens relative to the LPS-derived proxy terrain after registration
  improvement;
- `sphere_rotational_v1` changes trajectory physics strongly but over-runs this
  subset;
- the result is not a contact-model selection decision because the dataset is
  small and the remaining uncertainty is terrain/material/shape-model dominated.

Classification for the 25-run subset:

- baseline under-run remains stable at about 30 m mean runout error;
- rotational over-run also persists and becomes slightly larger in mean-runout
  error;
- block-level grouping shows the baseline under-run is strongest for block 1
  and weakest for block 4, while rotational over-run appears across all three
  represented block IDs;
- the larger subset strengthens the conclusion that the current evidence does
  not support changing the recommended/default contact model from this
  benchmark alone.

## Hazard-Layer Summaries

### Ten-Run Subset

| Case | Reach nonzero cells | Deposition nonzero cells | Max kinetic energy (J) | Max jump height (m) | Significant-impact nonzero cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public baseline | 295 | 17 | 9,401 | 1.291 | 273 |
| Public rotational | 1,399 | 45 | 25,005 | 3.748 | 875 |

Selected exceedance layers:

| Case | KE >= 10 kJ nonzero cells | Jump >= 2 m nonzero cells |
| --- | ---: | ---: |
| Public baseline | 0 | 0 |
| Public rotational | 1,029 | 135 |

### Twenty-Five-Run Subset

| Case | Reach nonzero cells | Deposition nonzero cells | Max kinetic energy (J) | Max jump height (m) | Significant-impact nonzero cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public baseline, 25 runs | 524 | 33 | 9,401 | 1.722 | 478 |
| Public rotational, 25 runs | 2,696 | 88 | 25,025 | 6.067 | 1,656 |

Selected exceedance layers:

| Case | KE >= 10 kJ nonzero cells | Jump >= 2 m nonzero cells |
| --- | ---: | ---: |
| Public baseline, 25 runs | 0 | 0 |
| Public rotational, 25 runs | 1,902 | 313 |

The larger rotational reach and energy footprint is consistent with the
runout-metric over-run in both subsets. No operational hazard interpretation is
made from these diagnostic layers.

## Visual QA

The generated QA plot shows:

- release points and observed deposition points lie inside the 2 m crop;
- the release cluster is upslope of the deposition cluster in the expected
  direction;
- the 250 m crop avoids the tight-grid clipping issue seen with the initial 40 m
  crop;
- no nodata edge artifact was visible in the release/deposition region;
- the 25-run crop contains all observed and simulated deposition rows for both
  contact modes;
- transformed LPS samples overlay the public slope scan closely under
  `scan_surface_fit_v1`, with sub-metre vertical RMSE against nearest scan
  points.

Open issue: the LPS-to-LV95 transform is still a terrain-scan fit, not a
surveyed control transform. It is now bounded well enough for a controlled
workflow comparison on this subset, but final scientific conclusions still need
additional trajectory coverage and independent coordinate QA.

## Interpretation

This reproduction improves workflow credibility and removes the first-pass
registration as the dominant explanation for the public-terrain mismatch. The
current uncalibrated spherical model still does not match deposition/runout
robustly:

- on proxy terrain it under-runs by about 31 m for the 10-run subset;
- on the public swissALTI3D crop it under-runs by about 30 m in baseline mode;
- with `sphere_rotational_v1` it over-runs by about 98 m on the same crop.
- on the 25-run public subset, baseline under-run remains about 30 m and
  `sphere_rotational_v1` over-runs by about 103 m.

The registration change materially changes the earlier first-pass conclusion:
the public real-terrain baseline no longer worsens the under-run relative to the
proxy controls. The remaining likely explanations are not separable yet:

- terrain differences between the published slope scan/LPS proxy and the
  swissALTI3D 2019 tile;
- equivalent-sphere limitations for irregular field blocks;
- globally uniform contact/roughness parameters;
- missing terrain/material classes, vegetation, and shape-dependent energy
  partitioning.

Because the real-terrain baseline now reproduces the proxy-scale under-run and
the 25-run subset gives the same broad conclusion, the next scientific step
should focus on whether the missing trajectory realism is mainly due to
equivalent-sphere physics or terrain/material parameterization. Shape-aware
scaffolding remains the strongest physics candidate, but it should be evaluated
against an even broader registered subset and not tuned to these deposition
metrics.

## Remaining Gaps Relative To State-Of-Practice Tools

- non-spherical block geometry, inertia, orientation, and contact-point
  switching;
- terrain/material-class dependent contact and roughness parameters;
- calibrated treatment of rolling, sliding, bouncing, and stopping transitions;
- GIS-ready raster outputs with CRS-bearing GeoTIFF/COG;
- larger public benchmark coverage beyond the first 25 LPS runs;
- independent survey/control-point confirmation of the LPS-to-LV95 registration.

## Recommended Next Step

Immediate next step: **prepare a shape-aware scaffold or terrain/material
calibration design, but only as a no-tuning model-comparison experiment**.

Concrete work:

1. expand the registered public subset further only if the next model-comparison
   question requires additional block/run coverage;
2. define a shape-aware scaffold or terrain/material calibration experiment that
   is evaluated against the already-registered public workflow without tuning
   after seeing results;
3. compare `translational_v0`, `sphere_rotational_v1`, roughness variants, and
   any future candidate model as predefined configurations;
4. inspect whether under-run persists consistently across block sizes, impact
   counts, and release/deposition regions.

Deferred:

- no parameter tuning against these diagnostic results;
- no parameter tuning or terrain/material calibration against these subset
  results before defining the calibration protocol;
- no operational hazard claims;
- no performance/data-format work based on this small scientific benchmark.
