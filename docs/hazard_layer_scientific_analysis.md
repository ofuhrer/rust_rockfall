# Scientific Analysis of Ensemble Hazard Layers

This document interprets the current ensemble-based hazard-layer outputs for
`v0.4.0`. It uses freshly generated, ignored artifacts under
`hazard/results/hazard_analysis_*` from git hash `2a328c2`. No simulation
physics, validation semantics, or calibration settings were changed.

The layers should be read as diagnostic hazard-model outputs, not operational
hazard or risk maps. Reach probability is path occupancy by simulated
trajectory centre lines. Deposition density is final-position density. Maximum
kinetic energy and maximum jump height are cell-wise maxima, so isolated
high values can be caused by one trajectory. Significant impact density is
normalized over impact events with incoming normal speed at least `0.05 m/s`.

## Cases

| Case | Source case | Inputs used | Purpose |
| --- | --- | --- | --- |
| Synthetic roughness ensemble | `verification/stochastic/contact_roughness_ensemble_spread.yaml` | 12 trajectories, 5,538 trajectory samples, 2,842 impact events | Controlled path-spread and layer-consistency check on analytic terrain |
| Tschamut baseline | `validation/cases/validation_tschamut_baseline.yaml` | 60 trajectories, 53,615 trajectory samples, 60 depositions, 26,530 impact events | Proxy-terrain real-data comparison without scarring |
| Tschamut scarring | `validation/cases/validation_tschamut_scarring.yaml` | 60 trajectories, 54,060 trajectory samples, 60 depositions, 23,816 impact events | Same setup with transferred impact-level `scarring_contact_v1` parameters |

The Tschamut cases still use the current proxy DEM workflow. Their outputs are
useful for model diagnosis and comparative experiments, but not for operational
Alpine hazard assessment.

## Layer Statistics

Values below summarize valid raster cells. For sparse layers, the median and
p95 often remain zero because most cells are untouched.

### Synthetic Roughness Ensemble

| Layer | Nonzero cells | Max | Mean | p95 | Sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reach probability | 18 / 65 | 1.000 | 0.119 | 0.900 | 7.750 |
| Deposition density | not generated | | | | |
| Maximum kinetic energy (J) | 18 / 18 | 2,178.98 | 526.19 | 1,552.65 | 9,471.46 |
| Maximum jump height (m) | 18 / 18 | 3.50 | 0.50 | 3.05 | 8.96 |
| Significant impact density | 16 / 65 | 0.325 | 0.015 | 0.074 | 1.000 |

The synthetic case has no ensemble deposition CSV, so no deposition-density
layer is produced. This is acceptable for a verification-style ensemble where
the relevant diagnostic is path spread.

### Tschamut Baseline

| Layer | Nonzero cells | Max | Mean | p95 | Sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reach probability | 44 / 204 | 1.000 | 0.101 | 0.771 | 20.700 |
| Deposition density | 4 / 204 | 0.617 | 0.005 | 0.000 | 1.000 |
| Maximum kinetic energy (J) | 44 / 44 | 7,697.57 | 4,152.14 | 7,490.41 | 182,694.05 |
| Maximum jump height (m) | 44 / 44 | 1.24 | 0.35 | 0.55 | 15.32 |
| Significant impact density | 43 / 204 | 0.387 | 0.005 | 0.007 | 1.000 |

The validation summary reports a simulated mean runout of `71.51 m` versus an
observed mean runout of `102.84 m`, giving a mean runout deficit of `31.33 m`.
Deposition is tightly clustered in four cells and remains upslope of the
observed deposition pattern.

### Tschamut Scarring

| Layer | Nonzero cells | Max | Mean | p95 | Sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reach probability | 41 / 176 | 1.000 | 0.104 | 0.738 | 18.283 |
| Deposition density | 4 / 176 | 0.767 | 0.006 | 0.000 | 1.000 |
| Maximum kinetic energy (J) | 41 / 41 | 4,574.16 | 2,673.55 | 4,407.35 | 109,615.54 |
| Maximum jump height (m) | 41 / 41 | 1.24 | 0.25 | 0.39 | 10.21 |
| Significant impact density | 40 / 176 | 0.592 | 0.006 | 0.012 | 1.000 |

Scarring reduces trajectory extent and kinetic energy, as expected from an
impact-local energy-loss model. It worsens the existing Tschamut under-run:
the simulated mean runout decreases to `64.03 m`, increasing the mean runout
error to `38.81 m`. This is physically understandable because the baseline
already stops too early on the proxy terrain.

## Cross-Layer Consistency

Top-cell overlap uses the upper decile of positive cells for each layer.

| Case | Check | Result | Interpretation |
| --- | --- | --- | --- |
| Synthetic | High reach vs high energy | Jaccard `0.50` | The main corridor is also the acceleration corridor, consistent with a controlled downslope path. |
| Synthetic | High jump/energy vs significant impacts | Jaccard `0.00` | The largest jump occurs early in flight; impact density concentrates farther downslope after repeated contacts. |
| Tschamut baseline | High reach vs deposition | Jaccard `0.00` | Reach is a corridor measure, while deposition is a terminal cluster farther downslope. Divergence is expected. |
| Tschamut baseline | High reach vs high energy | Jaccard `0.11` | High energy occurs along part of the main corridor, not necessarily where path occupancy is highest. |
| Tschamut scarring | High reach vs deposition | Jaccard `0.20` | Shorter runout moves the terminal cluster closer to the high-occupancy corridor. |
| Tschamut scarring | High jump vs impacts | Jaccard `0.13` | Some jump-height maxima coincide with impact concentration, but the layers remain different diagnostics. |

No obvious disconnected high-probability islands were found in these runs.
The main numerical caution is sparsity: deposition density is based on 60
points and occupies four cells, so small shifts can strongly change overlap
fractions.

## Spatial Shifts From Baseline to Scarring

Centroids are value-weighted over positive cells.

| Layer | Baseline centroid `(x, y)` m | Scarring centroid `(x, y)` m | Shift |
| --- | ---: | ---: | ---: |
| Reach probability | `(50.06, 206.47)` | `(47.71, 210.26)` | `4.46 m` upslope/leftward |
| Deposition density | `(67.58, 174.25)` | `(62.67, 181.42)` | `8.69 m` upslope/leftward |
| Maximum kinetic energy | `(51.81, 204.82)` | `(48.48, 210.28)` | `6.40 m` upslope/leftward |
| Maximum jump height | `(48.72, 210.55)` | `(45.16, 216.23)` | `6.70 m` upslope/leftward |
| Significant impact density | `(62.63, 183.47)` | `(56.74, 192.69)` | `10.94 m` upslope/leftward |

The scarring run shifts all major layer centroids upslope and reduces the
number of reached cells (`44` to `41`). Maximum kinetic energy falls by about
`41%` (`7.70 kJ` to `4.57 kJ`). Maximum jump height stays capped by the same
early release/terrain geometry (`1.24 m`) but its mean over positive cells
drops from `0.35 m` to `0.25 m`.

The full scarring impact logs contain about `189 kJ` cumulative capped energy
loss over the 60-member ensemble, or roughly `3.2 kJ` per trajectory. This is
consistent in scale with the case-level scarring diagnostic and explains the
shorter runout and lower energy layers.

## Region Explanations

### Synthetic High-Energy Corridor

Selected cell: centre `(2.5, 0.5) m`, from the maximum-kinetic-energy layer.
All 12 trajectories pass through this cell between `0.67 s` and `1.06 s`.
The cell contains 388 trajectory samples: 375 airborne, 12 impact, and 1
sliding sample. The maximum speed is `9.34 m/s`, giving a maximum kinetic
energy of `2.18 kJ`.

This is the first major acceleration corridor after release. Reach probability
is high because all ensemble members follow the same analytic slope before
roughness-driven divergence becomes large. Energy is high because the block is
still converting release elevation into translational kinetic energy. The
impact count is present but not dominant in the sample mix, so this region is
best interpreted as a ballistic acceleration corridor with one coherent impact
sequence, not an impact-density hotspot.

### Tschamut Baseline Deposition Hotspot

Selected cell: centre `(67.5, 172.5) m`, from the deposition-density layer.
This cell contains the largest terminal cluster: 38 trajectories contribute
samples, and deposition density reaches `0.617`. Samples occur from about
`9.86 s` to the end of the run at `18.0 s`. The contact-state mix is dominated
by impact-labelled samples, with some airborne and sliding states and one
stopped sample. The maximum speed inside the cell is `5.76 m/s`, but terminal
motion is low-energy and repeated-contact dominated.

The layer pattern is physically plausible for the current model: trajectories
accelerate earlier, then accumulate in a low-runout terminal zone where
repeated low-energy contacts consume motion. It is also a model limitation:
the cluster is much too far upslope relative to observed Tschamut runout, so
high deposition density here should be interpreted as simulated stopping bias,
not as validation success.

### Tschamut Baseline High-Energy Zone

Selected cell: centre `(57.5, 197.5) m`, from the maximum-kinetic-energy
layer. Forty-nine trajectories pass through this cell between about `6.8 s`
and `8.6 s`. The sample mix is mostly airborne, with 90 impact events and a
small number of sliding samples. Maximum speed reaches `14.67 m/s`, giving
the baseline maximum kinetic energy of `7.70 kJ`.

This zone links trajectory physics to the energy layer: the proxy terrain
still allows substantial downslope acceleration here, and high energy is
recorded before the terminal repeated-contact zone. It does not coincide with
the deposition hotspot because energy maxima occur during transit, not at
stopping positions. This separation is expected and scientifically useful.

### Tschamut Scarring Impact Concentration

Selected cell: centre `(62.5, 182.5) m`, from the significant-impact-density
layer. All 60 scarring trajectories contribute samples here between about
`10.26 s` and `18.0 s`. The cell contains 14,078 impact events, of which
14,042 exceed the significant-impact threshold. The maximum speed is
`6.68 m/s`; the maximum incoming normal impact speed is `1.80 m/s`.

This is where trajectory physics most directly explains the map change. The
same repeated-contact terminal behaviour that creates deposition also triggers
scarring losses. Within this cell, capped scarring energy loss sums to about
`4.08 kJ`, with maximum scar depth near `0.058 m`. That impact-local energy
loss shortens trajectories and shifts the deposition and impact-density
centroids upslope relative to baseline.

## Key Insights

1. The ensemble hazard layers are internally consistent for the current model:
   reach describes corridors, deposition describes terminal clustering, and
   energy maxima occur upstream of stopping zones.
2. The synthetic roughness case behaves as expected: early path occupancy and
   energy are coherent, while impact density shifts downslope after repeated
   contacts begin.
3. Tschamut scarring changes the maps in the physically expected direction for
   an energy-loss mechanism: lower maximum energy, lower mean jump height,
   fewer reached cells, and upslope-shifted deposition.
4. That same direction is unfavorable for the current Tschamut comparison
   because the baseline already under-runs observations. The experiment
   therefore diagnoses a structural terrain/model gap rather than successful
   trajectory validation.
5. Cell-wise maximum layers are useful but can be dominated by one trajectory.
   Percentile or exceedance layers are needed before these outputs become
   robust map products.

## Likely Model and Data Limitations

- **Proxy terrain remains dominant.** The Tschamut proxy DEM is still too
  simplified to interpret spatial skill. Terrain slope, channelization, local
  roughness, and release geometry probably dominate the runout mismatch.
- **Spherical-block dynamics are limited.** Shape-controlled lateral spread,
  angular momentum exchange, and non-spherical contact are not represented.
- **Sparse ensembles and raster sensitivity matter.** Sixty trajectories and
  5 m cells are adequate for debugging but not enough for stable deposition
  density, exceedance probability, or operational-style maps.

## Swiss-Scale Readiness

The current workflow is scientifically useful for small diagnostic ensembles,
but it is not yet sufficient for Swiss-scale rockfall hazard mapping.

For **pilot-scale single-slope studies**, the next needs are:

1. real DEM patches with explicit CRS and cell alignment;
2. larger opt-in ensemble trajectory output with stable storage conventions;
3. percentile and exceedance layers for energy and jump height;
4. documented release-zone generation and parameter sets.

For **regional-scale studies**, the next needs are:

1. DEM tiling and edge-buffer handling;
2. streaming or chunked hazard accumulation;
3. reproducible ensemble orchestration across many source zones;
4. calibration/validation splits by terrain and event type.

For **Switzerland-wide workflows**, the next needs are:

1. standard geospatial exports such as GeoTIFF with LV95 metadata;
2. job-array or HPC orchestration that preserves trajectory-id reproducibility;
3. scalable storage formats for trajectories and impacts, likely Parquet or
   Zarr rather than CSV;
4. clear separation of hazard layers from later risk layers requiring exposure
   and vulnerability data.

The current layers are best viewed as a traceable bridge from individual
trajectory physics to spatial hazard diagnostics. They are not yet calibrated
or validated map products.
