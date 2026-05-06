# Public Tschamut Failure-Mode Analysis

Status: no-tuning scientific analysis based on the registered public Tschamut
25-run benchmark outputs. This document changes no physics, parameters,
defaults, validation semantics, or output schemas.

Update: `public_tschamut_all_runs_grouped_validation.md` extends this analysis
to all 80 processed shared public Tschamut LPS/overview runs. The all-runs
result confirms the 25-run conclusion: `translational_v0` remains a systematic
under-run model and `sphere_rotational_v1` remains a systematic over-run model.

## Inputs

Analyzed ignored generated artifacts from:

- `validation/results/tschamut_public_benchmark_25/`
- `hazard/results/tschamut_public_benchmark_25_baseline/`
- `hazard/results/tschamut_public_benchmark_25_rotational/`

Models:

- `translational_v0`
- `sphere_rotational_v1`

The 25-run subset contains blocks 1, 2, and 4 with public passive shape
sidecars available under `data/processed/tschamut2014/shape_metadata/`. Shape
metadata is used here only for grouping and interpretation; active contact
remains spherical.

## Core Failure Modes

| Contact model | Dominant runout class | Release-level pattern | Hazard-layer pattern |
| --- | --- | --- | --- |
| `translational_v0` | Mostly under-run | 21 of 25 releases under-run by more than 10 m; 4 over-run by more than 10 m | Compact corridor, low energy, no 10 kJ or 2 m jump exceedance cells |
| `sphere_rotational_v1` | Systematic over-run | 25 of 25 releases over-run by more than 10 m | Much wider reach, high kinetic-energy exceedance, nonzero 2 m jump exceedance |

Signed runout error percentiles:

| Contact model | P05 (m) | Median (m) | P95 (m) |
| --- | ---: | ---: | ---: |
| `translational_v0` | -74.189 | -38.128 | 41.943 |
| `sphere_rotational_v1` | 63.405 | 92.986 | 171.622 |

The baseline mismatch is not simply a uniform shift. It combines strong
under-run for long observed trajectories with a few short observed trajectories
that are over-shot. The rotational model is simpler diagnostically: it carries
too far for every release in this subset.

## Block-Level Grouping

| Contact model | Block | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Reach width (m) | Significant impacts / traj | Max jump (m) | Max KE (J) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | 1 | 11 | 103.878 | 65.251 | -38.627 | 5.474 | 8.079 | 469.985 | 2.762 | 8,460 |
| `translational_v0` | 2 | 7 | 95.014 | 66.442 | -28.572 | 9.198 | 10.376 | 475.357 | 2.726 | 9,401 |
| `translational_v0` | 4 | 7 | 89.517 | 72.207 | -17.310 | 10.184 | 12.071 | 456.619 | 2.573 | 4,775 |
| `sphere_rotational_v1` | 1 | 11 | 103.878 | 200.799 | 96.921 | 18.172 | 28.464 | 139.136 | 7.209 | 23,912 |
| `sphere_rotational_v1` | 2 | 7 | 95.014 | 200.041 | 105.028 | 25.790 | 34.162 | 137.762 | 7.052 | 25,025 |
| `sphere_rotational_v1` | 4 | 7 | 89.517 | 200.960 | 111.443 | 25.507 | 35.412 | 132.571 | 4.496 | 12,999 |

Block grouping is scientifically useful but not decisive yet. Baseline
under-run is strongest for block 1 and weakest for block 4, while rotational
over-run appears for all three blocks. That pattern is plausibly shape-related
because block 4 is plate-like and has the smallest mass/equivalent radius, but
terrain path and observed runout length are confounded with block ID in this
subset.

## Runout Quantile Grouping

| Contact model | Observed-runout group | Runs | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Significant impacts / traj | Mean trajectory length (m) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | short observed | 8 | 64.844 | 72.676 | 7.832 | 8.363 | 446.688 | 88.763 |
| `translational_v0` | mid observed | 9 | 106.177 | 58.625 | -47.553 | 5.624 | 499.407 | 71.428 |
| `translational_v0` | long observed | 8 | 120.004 | 72.408 | -47.595 | 9.796 | 453.188 | 88.368 |
| `sphere_rotational_v1` | short observed | 8 | 64.844 | 200.967 | 136.123 | 25.413 | 134.562 | 241.324 |
| `sphere_rotational_v1` | mid observed | 9 | 106.177 | 199.809 | 93.632 | 18.734 | 143.315 | 235.528 |
| `sphere_rotational_v1` | long observed | 8 | 120.004 | 201.222 | 81.218 | 23.383 | 132.062 | 241.006 |

Observed runout length is the strongest grouping signal. Baseline errors are
strongly anticorrelated with observed runout: longer observed trajectories
under-run more. Rotational trajectories cluster near 200 m simulated runout
regardless of observed runout, which creates the largest over-runs for short
observed trajectories.

## Impact And Path-Length Grouping

| Contact model | Impact group | Runs | Signed error (m) | Significant impacts / traj | Mean trajectory length (m) | Max jump (m) | Max KE (J) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | low impacts | 8 | -25.711 | 439.583 | 88.370 | 2.762 | 8,884 |
| `translational_v0` | mid impacts | 9 | -23.076 | 454.759 | 88.033 | 2.431 | 9,401 |
| `translational_v0` | high impacts | 8 | -41.588 | 510.521 | 70.080 | 2.573 | 8,291 |
| `sphere_rotational_v1` | low impacts | 8 | 107.173 | 126.208 | 241.204 | 4.128 | 24,777 |
| `sphere_rotational_v1` | mid impacts | 9 | 99.244 | 133.463 | 241.566 | 4.980 | 25,005 |
| `sphere_rotational_v1` | high impacts | 8 | 103.855 | 151.500 | 234.333 | 7.209 | 25,025 |

High baseline impact counts coincide with shorter simulated path length and
larger under-run. This looks terrain/material/contact-loss related: repeated
small impacts and contact chatter dissipate or stall motion before the observed
deposition zone. In rotational mode, impact counts fall sharply because
trajectories remain more energetic and airborne/fast; over-run is not limited
to a specific impact-count group.

## Hazard-Layer Structure

| Layer summary, 25-run subset | `translational_v0` | `sphere_rotational_v1` |
| --- | ---: | ---: |
| Reach nonzero cells | 524 | 2,696 |
| Deposition nonzero cells | 33 | 88 |
| Significant-impact nonzero cells | 478 | 1,656 |
| Max kinetic energy (J) | 9,401 | 25,025 |
| Max jump height (m) | 1.722 | 6.067 |
| 10 kJ exceedance cells | 0 | 1,902 |
| 2 m jump exceedance cells | 0 | 313 |

The layer structure matches the runout metrics. Baseline deposition is too
compact and low-energy relative to observed runout, while rotational output
creates a broad high-energy reach footprint. Core raster writing and plotting
are not part of this scientific interpretation; these are diagnostic layers
from existing no-tuning runs.

## Largest Release-Level Failures

Baseline under-run outliers:

| Release | Block | Observed runout (m) | Simulated runout (m) | Signed error (m) | Significant impacts / traj | Mean path length (m) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `v034` | 1 | 107.030 | 32.748 | -74.282 | 584.500 | 39.464 |
| `v033` | 1 | 107.030 | 33.059 | -73.972 | 588.500 | 39.812 |
| `v032` | 2 | 100.452 | 31.075 | -69.377 | 615.000 | 37.326 |
| `v014` | 4 | 134.700 | 71.381 | -63.320 | 453.667 | 86.662 |
| `v015` | 1 | 134.701 | 72.341 | -62.360 | 458.833 | 87.887 |

Rotational over-run outliers:

| Release | Block | Observed runout (m) | Simulated runout (m) | Signed error (m) | Lateral error (m) | Max jump (m) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `v026` | 4 | 27.490 | 203.004 | 175.514 | 13.241 | 4.496 |
| `v022` | 2 | 36.844 | 199.386 | 162.542 | 38.398 | 4.128 |
| `v023` | 1 | 46.087 | 201.608 | 155.522 | 12.400 | 3.872 |
| `v017` | 4 | 42.904 | 197.065 | 154.161 | 15.787 | 2.784 |
| `v005` | 2 | 83.944 | 201.331 | 117.387 | 27.785 | 3.811 |

These outliers suggest two different failure regimes: baseline early stopping
after many contacts, and rotational persistent high-energy transport beyond the
observed deposition zone.

## Interpretation By Mechanism

Plausibly shape-related:

- block-level differences in baseline signed error, especially the weaker
  under-run for the plate-like block 4;
- rotational over-run despite improved Chant Sura trajectory metrics, which may
  indicate missing non-spherical energy partitioning, tumbling transitions, or
  orientation-dependent contact losses;
- large lateral-error and reach-width increases in rotational mode, consistent
  with a spherical model that lacks shape-dependent stabilizing contacts.

Plausibly terrain/material-related:

- baseline high-impact groups have the largest under-run and shortest path
  lengths, suggesting excessive stopping or energy loss along particular terrain
  paths;
- baseline has no 10 kJ or 2 m jump exceedance cells, which may be too
  dissipative for the public-terrain corridor;
- globally uniform contact/roughness parameters cannot represent terrain-class
  transitions, vegetation, surface roughness patches, or local stopping zones.

Ambiguous:

- block ID, observed runout length, and terrain path are not independent in this
  25-run subset;
- significant-impact counts are sensitive to the low 0.05 m/s normal-speed
  threshold and include contact chatter, so they should be interpreted as a
  relative diagnostic rather than physical impact counts;
- jump-height and kinetic-energy differences separate the two contact models,
  but do not alone identify whether shape or material is the missing mechanism.

## Recommendation

The next justified step is **improved validation metric grouping**, not
immediate shape-contact implementation or calibration. Specifically:

1. expand this grouped analysis to all usable public Tschamut runs with outlier
   QA;
2. add reportable group metrics by block ID, mass/radius, observed-runout
   quantile, impact-count class, and trajectory-length class;
3. keep shape metadata passive and use it to test whether block-level patterns
   persist;
4. design shape-contact physics only after the grouped metrics define what a
   successful no-tuning model improvement must improve and must not degrade.

Terrain/material calibration remains important, but should wait until grouped
metrics and held-out criteria prevent calibration from hiding missing shape
physics.

The all-runs grouped validation now satisfies this recommendation and should be
used as the evidence baseline for the next active shape-contact design step.
