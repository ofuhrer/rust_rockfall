# Public Tschamut All-Runs Grouped Validation

Status: no-tuning Work Package 1 report. This document analyzes the registered
public Tschamut benchmark across all usable public processed runs. It changes
no physics, parameters, defaults, validation semantics, hazard semantics, or
output schemas, and it does not claim operational validity.

## Scope

This report expands the public Tschamut benchmark from the 10-run and 25-run
subsets to all 80 processed shared LPS/overview runs. The goal is to make the
current failure modes harder to misread before active shape-contact physics or
terrain/material calibration are attempted.

Models compared:

- `translational_v0`
- `sphere_rotational_v1`

Both runs use public EnviDat Tschamut observations, public swissALTI3D 2 m
terrain, `scan_surface_fit_v1` registration, deterministic seed `34014`,
ensemble size `6`, and explicit-grid hazard generation with plots disabled.
No restitution, friction, roughness, scarring, terrain-class, release, or
contact-model parameters were tuned. Passive Tschamut shape sidecars remain
passive; mixed-block all-runs cases do not attach a single
`block_shape.metadata_path`.

## Commands

Preparation:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py \
  --output-root validation/results/tschamut_public_benchmark_all \
  --run-limit 80 \
  --padding-m 250 \
  --force
```

Validation:

```bash
cargo run -- validate --case validation/results/tschamut_public_benchmark_all/cases/tschamut_public_benchmark_baseline.yaml
cargo run -- validate --case validation/results/tschamut_public_benchmark_all/cases/tschamut_public_benchmark_rotational.yaml
```

Hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark_all/cases/tschamut_public_benchmark_baseline.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_all_baseline \
  --grid-xmin 2696360 \
  --grid-ymin 1167382 \
  --grid-ncols 308 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots

python3 scripts/build_hazard_layers.py \
  --case validation/results/tschamut_public_benchmark_all/cases/tschamut_public_benchmark_rotational.yaml \
  --output-dir hazard/results/tschamut_public_benchmark_all_rotational \
  --grid-xmin 2696360 \
  --grid-ymin 1167382 \
  --grid-ncols 308 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots
```

Generated validation and hazard outputs are ignored result artifacts.

## Inclusion And Exclusion QA

| Source set | Count | Notes |
| --- | ---: | --- |
| `OverviewAllTests` campaign rows | 111 | Public overview rows parsed from the raw EnviDat ZIP |
| Processed shared LPS/overview rows | 80 | Rows with overview block metadata and usable LPS first/last samples |
| Included in all-runs benchmark | 80 | All processed shared rows |
| Excluded from all-runs benchmark | 31 | Overview rows without usable processed LPS trajectory rows |

Excluded overview IDs:

```text
v001, v002, v003, v008, v009, v010, v012, v013, v016, v054,
v056, v059, v060, v061, v062, v071, v082, v084, v085, v087,
v089, v091, v094, v096, v098, v100, v102, v103, v106, v108,
v110
```

These exclusions are not model-result filters. They are reproducible data
availability exclusions inherited from the processed public LPS/overview
intersection. All 80 processed shared rows are included.

## Registration, Crop, And Provenance QA

| Check | Value |
| --- | --- |
| Transform | `scan_surface_fit_v1` |
| Registration horizontal mean / p95 / max | 0.485 / 1.507 / 5.149 m |
| Registration vertical RMSE / abs p95 | 0.517 / 1.117 m |
| DEM grid | 308 x 309 at 2 m |
| DEM extent LV95 | x 2696360-2696976, y 1167382-1168000 |
| NODATA cells | 0 |
| Release/deposition points inside crop | 80/80 releases, 80/80 depositions |
| Block counts | block 1: 29, block 2: 25, block 4: 26 |

Registration is still an approximate terrain-scan fit, not a surveyed
control-point adjustment, but it is not the dominant explanation for the
all-runs mismatch.

## Overall Results

| Model | Runs | Observed runout (m) | Simulated runout (m) | Mean signed error (m) | P05 (m) | P50 (m) | P95 (m) | Lateral error (m) | Reach width (m) | Significant impacts / traj | Path length (m) | Max sample energy (J) | Under / near / over |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `translational_v0` | 80 | 98.401 | 63.398 | -35.003 | -93.453 | -34.706 | 26.590 | 7.949 | 9.390 | 501.367 | 77.967 | 10699 | 71 / 4 / 5 |
| `sphere_rotational_v1` | 80 | 98.401 | 202.953 | 104.552 | 79.763 | 102.815 | 154.229 | 23.226 | 34.353 | 143.669 | 239.035 | 30659 | 1 / 0 / 79 |

`Under / near / over` uses signed runout error thresholds of less than -10 m,
within +/-10 m, and greater than 10 m.

The 10-run and 25-run conclusions are stable:

- `translational_v0` remains a systematic under-run model, and the all-runs
  mean under-run is slightly larger than the earlier approximately 30 m result.
- `sphere_rotational_v1` remains a systematic over-run model.
- The rotational model is not a candidate default change from this evidence.

## Block And Shape-Class Grouping

| Model | Block shape class | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Reach width (m) | Significant impacts / traj | Path length (m) | Max sample energy (J) | Under / near / over |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `translational_v0` | blocky / St. Leonard | 29 | 106.219 | 64.362 | -41.857 | 6.830 | 8.429 | 486.155 | 79.201 | 9535 | 28 / 0 / 1 |
| `translational_v0` | elongate-heavy / Most heavy | 25 | 100.682 | 59.319 | -41.364 | 6.859 | 8.125 | 533.340 | 72.939 | 10699 | 24 / 0 / 1 |
| `translational_v0` | plate-like / Plate | 26 | 87.487 | 66.246 | -21.241 | 10.245 | 11.679 | 487.590 | 81.426 | 5269 | 19 / 4 / 3 |
| `sphere_rotational_v1` | blocky / St. Leonard | 29 | 106.219 | 204.923 | 98.704 | 17.501 | 29.319 | 141.259 | 240.598 | 26916 | 0 / 0 / 29 |
| `sphere_rotational_v1` | elongate-heavy / Most heavy | 25 | 100.682 | 199.206 | 98.523 | 22.175 | 32.557 | 152.640 | 233.657 | 30659 | 1 / 0 / 24 |
| `sphere_rotational_v1` | plate-like / Plate | 26 | 87.487 | 204.360 | 116.873 | 30.621 | 41.695 | 137.731 | 242.461 | 15683 | 0 / 0 / 26 |

Block shape is correlated with error, but not cleanly identifiable. The
baseline under-run is weaker for the plate-like block 4, while rotational
over-run is strongest for the same block. That is compatible with a
shape/contact hypothesis, but block ID is also coupled to release location,
observed runout, and terrain path.

## Observed-Runout Grouping

| Model | Observed runout group | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Reach width (m) | Significant impacts / traj | Path length (m) | Max sample energy (J) | Under / near / over |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `translational_v0` | short observed | 27 | 78.336 | 66.618 | -11.718 | 8.205 | 9.799 | 481.926 | 82.024 | 9732 | 18 / 4 / 5 |
| `translational_v0` | mid observed | 27 | 102.431 | 56.908 | -45.523 | 7.246 | 8.640 | 531.932 | 70.067 | 9501 | 27 / 0 / 0 |
| `translational_v0` | long observed | 26 | 115.052 | 66.794 | -48.258 | 8.414 | 9.745 | 489.814 | 81.959 | 10699 | 26 / 0 / 0 |
| `sphere_rotational_v1` | short observed | 27 | 78.336 | 200.071 | 121.734 | 26.970 | 37.595 | 147.154 | 236.911 | 30659 | 1 / 0 / 26 |
| `sphere_rotational_v1` | mid observed | 27 | 102.431 | 205.090 | 102.659 | 24.369 | 36.152 | 146.586 | 238.761 | 30611 | 0 / 0 / 27 |
| `sphere_rotational_v1` | long observed | 26 | 115.052 | 203.728 | 88.676 | 18.151 | 29.118 | 137.019 | 241.525 | 30503 | 0 / 0 / 26 |

Observed-runout length is one of the strongest grouping signals. Baseline
short-runout cases include the few near/over outcomes; baseline mid and long
observed trajectories under-run uniformly. Rotational trajectories cluster near
200 m regardless of observed runout, which makes short observed trajectories
the largest over-runs.

## Impact-Count And Trajectory-Length Grouping

| Model | Impact-count group | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Significant impacts / traj | Path length (m) | Under / near / over |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `translational_v0` | low impacts | 27 | 93.847 | 72.187 | -21.661 | 445.907 | 88.464 | 21 / 2 / 4 |
| `translational_v0` | mid impacts | 26 | 98.405 | 72.315 | -26.090 | 462.538 | 89.147 | 23 / 2 / 1 |
| `translational_v0` | high impacts | 27 | 102.951 | 46.023 | -56.927 | 594.216 | 56.705 | 27 / 0 / 0 |
| `sphere_rotational_v1` | low impacts | 28 | 94.373 | 201.579 | 107.206 | 126.774 | 243.413 | 0 / 0 / 28 |
| `sphere_rotational_v1` | mid impacts | 25 | 101.273 | 207.382 | 106.109 | 137.673 | 244.896 | 0 / 0 / 25 |
| `sphere_rotational_v1` | high impacts | 27 | 99.919 | 200.278 | 100.359 | 166.741 | 229.066 | 1 / 0 / 26 |

| Model | Trajectory-length group | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Significant impacts / traj | Path length (m) | Under / near / over |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `translational_v0` | short simulated path | 27 | 101.366 | 45.745 | -55.621 | 585.988 | 55.949 | 25 / 1 / 1 |
| `translational_v0` | mid simulated path | 26 | 93.580 | 71.887 | -21.694 | 455.929 | 88.356 | 21 / 1 / 4 |
| `translational_v0` | long simulated path | 27 | 100.078 | 72.877 | -27.201 | 460.500 | 89.983 | 25 / 2 / 0 |
| `sphere_rotational_v1` | short simulated path | 27 | 102.597 | 194.044 | 91.447 | 160.290 | 225.709 | 1 / 0 / 26 |
| `sphere_rotational_v1` | mid simulated path | 26 | 94.993 | 203.559 | 108.566 | 134.404 | 243.342 | 0 / 0 / 26 |
| `sphere_rotational_v1` | long simulated path | 27 | 97.487 | 211.280 | 113.793 | 135.969 | 248.213 | 0 / 0 / 27 |

Impact-rich baseline trajectories systematically under-run. The correlation
between significant impacts per trajectory and signed runout error is about
`r = -0.732` for `translational_v0`. This supports a contact/terrain stopping
failure mode: many small impacts and short simulated paths are associated with
large negative runout errors.

The rotational model has fewer significant impacts per trajectory and much
longer paths, but remains over-run in essentially every group. That supports
the interpretation that rotational energy transport is too persistent without
shape-dependent contact losses or calibrated terrain/material dissipation.

## Hazard-Layer Structure

| Model | Layer | Nonzero cells | Maximum | Sum | Valid cells |
| --- | --- | ---: | ---: | ---: | ---: |
| `translational_v0` | reach_probability | 740 | 0.291667 | 43.221 | 95172 |
| `translational_v0` | deposition_density | 82 | 0.133333 | 1.000 | 95172 |
| `translational_v0` | significant_impact_density | 696 | 0.082483 | 1.000 | 95172 |
| `translational_v0` | max_kinetic_energy | 740 | 10699.457 | 3193839.031 | 740 |
| `translational_v0` | max_jump_height | 734 | 1.722 | 242.433 | 740 |
| `translational_v0` | kinetic_energy_exceedance_10000j | 3 | 0.002083 | 0.006 | 95172 |
| `translational_v0` | jump_height_exceedance_2m | 0 | 0.000000 | 0.000 | 95172 |
| `sphere_rotational_v1` | reach_probability | 5125 | 0.277083 | 140.806 | 95172 |
| `sphere_rotational_v1` | deposition_density | 282 | 0.014583 | 1.000 | 95172 |
| `sphere_rotational_v1` | significant_impact_density | 3616 | 0.040472 | 1.000 | 95172 |
| `sphere_rotational_v1` | max_kinetic_energy | 5125 | 26152.569 | 70616488.756 | 5125 |
| `sphere_rotational_v1` | max_jump_height | 5115 | 7.229 | 5399.302 | 5125 |
| `sphere_rotational_v1` | kinetic_energy_exceedance_10000j | 3588 | 0.145833 | 76.065 | 95172 |
| `sphere_rotational_v1` | jump_height_exceedance_2m | 717 | 0.045833 | 3.727 | 95172 |

The hazard layers show the same split as the deposition metrics:

- baseline is compact, impact-rich, and low jump-height;
- rotational output spreads much farther laterally and downslope;
- rotational output has broad 10 kJ kinetic-energy exceedance and nonzero 2 m
  jump-height exceedance.

## Largest Release-Level Failures

| Model | Release | Block | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Significant impacts / traj | Path length (m) | Max sample energy (J) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | `v090` | 2 | 114.616 | 1.897 | -112.720 | 1.280 | 883.667 | 2.413 | 181 |
| `translational_v0` | `v099` | 4 | 110.092 | 1.461 | -108.631 | 1.363 | 889.167 | 1.653 | 49 |
| `translational_v0` | `v083` | 2 | 103.405 | 1.410 | -101.995 | 1.130 | 883.500 | 1.948 | 223 |
| `translational_v0` | `v093` | 2 | 101.561 | 1.138 | -100.424 | 1.126 | 882.667 | 1.712 | 250 |
| `translational_v0` | `v086` | 2 | 94.447 | 1.361 | -93.086 | 0.976 | 879.000 | 1.852 | 298 |
| `sphere_rotational_v1` | `v026` | 4 | 27.490 | 203.004 | 175.514 | 9.319 | 139.500 | 243.722 | 14858 |
| `sphere_rotational_v1` | `v022` | 2 | 36.844 | 199.386 | 162.542 | 38.398 | 123.833 | 238.408 | 27937 |
| `sphere_rotational_v1` | `v107` | 4 | 30.640 | 191.775 | 161.136 | 25.803 | 125.000 | 243.539 | 15426 |
| `sphere_rotational_v1` | `v023` | 1 | 46.087 | 201.608 | 155.522 | 9.951 | 131.333 | 242.809 | 25859 |
| `sphere_rotational_v1` | `v017` | 4 | 42.904 | 197.065 | 154.161 | 15.787 | 127.333 | 239.220 | 14422 |

The all-runs subset exposes severe baseline near-start stopping for several
later runs. These are not registration exclusions; they are valid processed
runs where the current baseline model repeatedly contacts and stalls almost
immediately.

## Correlations With Signed Runout Error

| Model | Variable | Pearson r vs signed error |
| --- | --- | ---: |
| `translational_v0` | observed runout | -0.728 |
| `translational_v0` | significant impacts/traj | -0.732 |
| `translational_v0` | simulated path length | 0.746 |
| `translational_v0` | lateral error | 0.257 |
| `translational_v0` | mass | -0.308 |
| `sphere_rotational_v1` | observed runout | -0.715 |
| `sphere_rotational_v1` | significant impacts/traj | -0.599 |
| `sphere_rotational_v1` | simulated path length | 0.678 |
| `sphere_rotational_v1` | lateral error | -0.037 |
| `sphere_rotational_v1` | mass | -0.312 |

These correlations are descriptive, not causal. They are useful for designing
the next model-comparison objectives.

## Answers To The WP1 Questions

### Are the 10-run and 25-run conclusions stable?

Yes. The all-runs result strengthens the previous conclusion: baseline
under-run persists and becomes -35.0 m on average, while rotational over-run
persists at +104.6 m on average.

### Does block shape appear correlated with under-run or over-run?

Yes, but not cleanly enough for a causal conclusion. The plate-like block 4
under-runs less in the baseline model but over-runs more in the rotational
model. That pattern is compatible with missing shape/contact physics, but block
shape is confounded with release path, observed runout, and terrain location.

### Are impact-rich trajectories systematically under-running?

Yes for `translational_v0`. High-impact baseline runs under-run by -56.9 m on
average and are all under-runs. Several largest failures stop within about
1-2 m of simulated runout while accumulating nearly 880 significant impacts per
trajectory. This is a concrete failure mode for future model comparisons.

### Are rotational trajectories systematically over-energetic?

Yes. `sphere_rotational_v1` produces wider reach, longer paths, higher kinetic
energy, and nonzero 2 m jump-height exceedance. It over-runs 79 of 80 releases
by more than 10 m. This does not invalidate its Chant Sura trajectory/contact
value, but it shows that spherical rotation alone transfers poorly to Tschamut
deposition/runout.

### Is there evidence for terrain/material dependence that could justify calibration before shape-contact?

There is evidence for terrain/path dependence, especially in impact-rich
baseline early-stopping runs. That justifies designing a terrain/material
calibration protocol, but not running calibration before shape/contact design.
The current evidence still cannot separate terrain/material dissipation from
missing shape-dependent contact and orientation effects.

## Scientific Interpretation

The all-runs benchmark sharpens the failure-mode split:

- baseline failure mode: excessive contact-rich stopping, with repeated
  significant impacts and short simulated paths associated with large negative
  runout errors;
- rotational failure mode: persistent high-energy transport, broad reach,
  larger lateral spread, and high energy/jump exceedance;
- block grouping: block shape is relevant enough to keep as a primary grouping
  variable, but not sufficient to select a model mechanism alone;
- terrain/material grouping: impact-rich stopping suggests terrain/contact
  interaction is important, but calibration could hide missing shape physics if
  started too early.

## Go / No-Go Assessment

WP1 go criteria are met:

- 111 public overview rows are accounted for: 80 included and 31 excluded for
  reproducible data-availability reasons.
- All 80 processed shared LPS/overview rows are included.
- Registration and crop QA remain acceptable for diagnostic comparison.
- Grouped metrics define clear future non-regression criteria.
- The 10-run and 25-run conclusions are confirmed.

No-go conditions are not triggered for grouped diagnostic reporting:

- coordinate registration uncertainty is reduced, but a registration
  sensitivity table across `scan_surface_fit_v1`, `bbox_align_v1`, and
  `overview_offset_v1` was subsequently executed. It confirmed stable runout
  sign (`translational_v0` under-runs; `sphere_rotational_v1` over-runs), but
  runout magnitude and deposition-overlap class vary materially by transform.
  Public Tschamut therefore remains diagnostic failure-mode evidence rather
  than physics-selection evidence, and `physics_selection_allowed` remains
  `false`;
- exclusions are reproducible rather than manual model-result filtering;
- grouped metrics are informative enough to guide the next design step.

## Recommended Next Step

Proceed to **active shape-contact design only** before implementation. The
design should use this all-runs report to define non-regression criteria:

- do not worsen the rotational over-run pattern;
- reduce baseline contact-rich early stopping without simply making every run
  over-energetic;
- preserve or improve lateral-spread realism;
- report block-specific effects for blocks 1, 2, and 4;
- keep Chant Sura trajectory/contact metrics in the comparison matrix.

Terrain/material calibration remains a necessary later work package, but this
all-runs evidence does not justify calibrating before shape/contact design.
