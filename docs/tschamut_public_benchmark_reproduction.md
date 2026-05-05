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

The executed run uses the same first 10 public LPS trajectories as the checked-in
Tschamut validation subset so the real-terrain and proxy-terrain comparisons are
directly comparable. The preparation script can be rerun with a larger
`--run-limit` after this registration method has been reviewed on additional
trajectory resources.

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

| Case | Terrain | Contact model | Simulated mean runout (m) | Observed mean runout (m) | Runout error (m) | Deposition centroid error (m) | Cloud nearest error (m) | Overlap fraction |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Public real-terrain baseline | swissALTI3D 2 m crop | `translational_v0` | 72.447 | 102.844 | 30.396 | 29.973 | 23.443 | 0.867 |
| Public real-terrain rotational | swissALTI3D 2 m crop | `sphere_rotational_v1` | 200.375 | 102.844 | 97.532 | 98.261 | 76.186 | 0.000 |
| Proxy baseline control | LPS-derived terrain proxy | `translational_v0` | 71.702 | 102.844 | 31.142 | 31.018 | 23.882 | 0.917 |
| Proxy basic control | LPS-derived terrain proxy | `translational_v0` | 71.773 | 102.844 | 31.070 | 30.963 | 23.751 | 0.950 |

Classification for this 10-run subset:

- baseline under-run **persists** on the public swissALTI3D crop, but no longer
  worsens relative to the LPS-derived proxy terrain after registration
  improvement;
- `sphere_rotational_v1` changes trajectory physics strongly but over-runs this
  subset;
- the result is not a contact-model selection decision because the dataset is
  small and the remaining uncertainty is terrain/material/shape-model dominated.

## Hazard-Layer Summaries

| Case | Reach nonzero cells | Deposition nonzero cells | Max kinetic energy (J) | Max jump height (m) | Significant-impact nonzero cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public baseline | 295 | 17 | 9,401 | 1.291 | 273 |
| Public rotational | 1,399 | 45 | 25,005 | 3.748 | 875 |

Selected exceedance layers:

| Case | KE >= 10 kJ nonzero cells | Jump >= 2 m nonzero cells |
| --- | ---: | ---: |
| Public baseline | 0 | 0 |
| Public rotational | 1,029 | 135 |

The larger rotational reach and energy footprint is consistent with the
runout-metric over-run. No operational hazard interpretation is made from these
diagnostic layers.

## Visual QA

The generated QA plot shows:

- release points and observed deposition points lie inside the 2 m crop;
- the release cluster is upslope of the deposition cluster in the expected
  direction;
- the 250 m crop avoids the tight-grid clipping issue seen with the initial 40 m
  crop;
- no nodata edge artifact was visible in the release/deposition region;
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

The registration change materially changes the earlier first-pass conclusion:
the public real-terrain baseline no longer worsens the under-run relative to the
proxy controls. The remaining likely explanations are not separable yet:

- terrain differences between the published slope scan/LPS proxy and the
  swissALTI3D 2019 tile;
- equivalent-sphere limitations for irregular field blocks;
- globally uniform contact/roughness parameters;
- missing terrain/material classes, vegetation, and shape-dependent energy
  partitioning.

Because the real-terrain baseline now reproduces the proxy-scale under-run, the
next scientific step should focus on whether the missing trajectory realism is
mainly due to equivalent-sphere physics, terrain/material parameterization, or
the small 10-run subset. Shape-aware scaffolding remains the strongest physics
candidate, but it should be evaluated against a larger registered subset rather
than this small sample alone.

## Remaining Gaps Relative To State-Of-Practice Tools

- non-spherical block geometry, inertia, orientation, and contact-point
  switching;
- terrain/material-class dependent contact and roughness parameters;
- calibrated treatment of rolling, sliding, bouncing, and stopping transitions;
- GIS-ready raster outputs with CRS-bearing GeoTIFF/COG;
- larger public benchmark coverage beyond the first 10 LPS runs;
- independent survey/control-point confirmation of the LPS-to-LV95 registration.

## Recommended Next Step

Immediate next step: **expand the registered public Tschamut subset and compare
physics variants without tuning**.

Concrete work:

1. rerun the same `scan_surface_fit_v1` workflow with a larger public LPS subset;
2. compare `translational_v0`, `sphere_rotational_v1`, roughness variants, and
   scarring only as predefined no-tuning configurations;
3. inspect whether under-run persists consistently across block sizes, impact
   counts, and release/deposition regions;
4. then decide whether the next major step should be shape-aware physics or
   terrain/material calibration.

Deferred:

- no parameter tuning against these diagnostic results;
- no shape-aware model implementation until the larger registered subset confirms
  the same physics gap;
- no operational hazard claims;
- no performance/data-format work based on this small scientific benchmark.
