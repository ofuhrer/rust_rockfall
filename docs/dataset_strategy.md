# Multi-Dataset Strategy

The project now treats public rockfall datasets as complementary constraints on
different parts of the model. The goal is not to reproduce RAMMS internals; it
is to build an independent simulator whose assumptions can be checked against
public measurements at the right level of evidence.

## Dataset Roles

| Dataset | Repository ID | Primary role | Current use | Not used for |
| --- | --- | --- | --- | --- |
| Chant Sura / Flüelapass campaign | `chant_sura_2020` | Trajectory and physics validation | Short reconstructed first-flight segments compare trajectory shape, translational kinetic energy, and proxy jump height. Small RF16 DEM-backed segmented contact fixtures compare trajectory shape, jump-height envelope, impact timing, rebound velocity, and post-impact energy change across model-selection and held-out subsets. EOTA shapes are recorded for future non-spherical models. | Calibration, operational hazard mapping, full runout/deposition validation, or shape-effect validation in v0.5.0 |
| Lu / Chant Sura scarring tables | `chant_sura_esurf_2019_impacts` | Impact-level scarring calibration | Public scar-depth and jump-energy tables constrain `scarring_contact_v1` at the single-impact level. | Trajectory validation or hazard-map validation |
| Tschamut 2014 | `tschamut2014` | Deposition-level validation | Public release/deposition subset compares ensemble runout and deposition-cloud metrics on a transparent terrain proxy. | Impact-level calibration, shape validation, or operational hazard skill |
| Synthetic analytic fixtures | `synthetic_*` | Verification | Closed-form or controlled checks for mechanics, terrain handling, stochastic reproducibility, scarring diagnostics, and hazard-layer post-processing. | Real-world validation |

## Operational Swiss Geodata

swisstopo products registered under `swisstopo_*` are operational input geodata,
not experimental validation datasets. Their purpose is to support future Swiss
hazard-map workflows after the physics has been constrained by public
experiments:

- `swisstopo_swissalti3d`: mandatory bare-earth terrain foundation for pilot
  domains.
- `swisstopo_swisssurface3d` and `swisstopo_swisssurface3d_raster`: optional
  vegetation, building, surface, and obstacle context.
- `swisstopo_swisstlm3d`: topographic vector context for release masks,
  infrastructure overlays, hydrography, and QA.
- `swisstopo_geocover`, `swisstopo_geological_atlas_25k`, and
  `swisstopo_geomaps_500`: geological/material context at different scales.
- `swisstopo_swissimage`: orthophoto QA and visual review.
- `swisstopo_swissbuildings3d`: future exposure/obstacle context; risk use
  requires explicit exposure and vulnerability modelling.

These datasets must retain CRS, vertical datum, resolution, extent, tile id, and
provenance metadata. Full swisstopo raw products are not committed. The detailed
strategy and first pilot workflow are in `docs/swisstopo_data_strategy.md`.

## Chant Sura as the Primary Reference Dataset

Chant Sura is the main trajectory-level reference because the public EnviDat
resources include reconstructed trajectory files with position, velocity,
translational energy, rotational diagnostics, and total energy columns. The
registry entry is DOI [10.16904/envidat.174](https://doi.org/10.16904/envidat.174).

Public resources currently registered include:

- `Output.7z`: reconstructed trajectory text files under `Output/txt/`.
- `Input.7z`: site input data, including the RF16 UAS DEM used to derive the small contact-validation terrain crop. The full archive remains large and raw-only.
- `ExperimentalRuns.7z`: large sensor/video run archive, not required by the minimal subset.
- `EOTA.7z`: small public rock-shape point files; summarized as metadata for future non-spherical modelling.
- ESurf 2019 tables 1 and 2: scar dimensions and jump-energy summaries used by the scarring calibration workflow.

The checked-in validation subset in
`validation/data/processed/chant_sura_2020/` contains:

- `release_points.csv`: initial state for three first-flight trajectory segments.
- `observed_trajectories.csv`: reconstructed positions, velocities, kinetic energy, rotational energy, and angular velocity for the selected segments.
- `terrain_rf16_contact.asc`: small RF16 UAS DEM crop in LV95 coordinates.
- `release_points_contact.csv`, `observed_trajectories_contact.csv`, and
  `observed_contact_events.csv`: first three RF16W200r1 local-time-reset
  trajectory segments plus two segment-boundary contact/rebound proxies.
- `terrain_rf16_contact_extended.asc`, `release_points_contact_extended.csv`,
  `observed_trajectories_contact_extended.csv`, and
  `observed_contact_events_extended.csv`: five selected trajectories, 16
  local-time-reset segments, and 11 segment-boundary contact/rebound proxies
  whose samples remain inside the RF16 DEM crop.
- `terrain_rf16_contact_heldout.asc`, `release_points_contact_heldout.csv`,
  `observed_trajectories_contact_heldout.csv`, and
  `observed_contact_events_heldout.csv`: six held-out trajectories, 15
  local-time-reset segments, and 9 segment-boundary contact/rebound proxies
  with no trajectory overlap against the model-selection subset.
- `metadata_contact_split.json`: deterministic split record separating
  model-selection and held-out evaluation trajectories.
- `block_metadata.csv`: equivalent-sphere approximations inferred from trajectory mass.
- `rock_shapes.csv`: EOTA shape bounding boxes and point counts, when `eota.7z` has been downloaded.
- `metadata.json`: source files, assumptions, and limitations.

The current validation case is
`validation/cases/chant_sura_trajectory_subset.yaml`. It checks only the first
monotonic time segment of three reconstructed trajectories because the public
trajectory text files concatenate jump segments with local time resets. It uses
a flat clearance-plane proxy, not the full site DEM, so jump-height comparison
is a consistency diagnostic rather than field-terrain validation.

The DEM-backed segmented-contact experiment is
`validation/cases/chant_sura_contact.yaml`, with comparison variants for
`sphere_rotational_v1`, `stochastic_contact_v1`, and `scarring_contact_v1`.
It uses a small crop from
`Input/UAS/2018_06_20_RF16/20180619_Chant_Sura_DEM_0.05m.tif`. The processed
fixture preserves raw observed z in metadata columns but shifts `z_m` by the
equivalent sphere radius so the current simulator's centre-of-mass convention
is compatible with terrain contact. Segment boundaries are treated as
contact/rebound proxies, not exact instrumented impact events.

The extended contact experiment is
`validation/cases/chant_sura_contact_extended.yaml`, with the same three
model-comparison variants. It increases the contact-event count from two to
eleven while preserving the same validation/calibration separation and the same
small RF16 terrain crop.

The held-out contact experiment is
`validation/cases/chant_sura_contact_heldout.yaml`, with a rotational comparison
variant. It tests whether the `sphere_rotational_v1` trajectory-shape and energy
improvement generalizes to disjoint source trajectories before any future
default-model decision.

## What Each Dataset Constrains

- **Trajectory shape:** Chant Sura reconstructed position/time series constrain
  free-flight and short-segment kinematics.
- **Energy evolution:** Chant Sura kinetic-energy columns constrain
  translational energy consistency for selected trajectory segments.
- **Impact energy loss and scar depth:** Lu/ESurf Chant Sura tables constrain
  the minimal scarring model at the single-impact level.
- **Deposition/runout distribution:** Tschamut constrains ensemble-level
  stopping and runout behavior, with current conclusions limited by the terrain
  proxy.
- **Shape effects:** Chant Sura and EOTA shape data can constrain future
  non-spherical models, but v0.5.0 does not yet use those shapes dynamically.
- **Hazard-map layers:** Synthetic and Tschamut cases exercise hazard-layer
  post-processing; real hazard-map validation requires larger ensembles, real
  DEMs, CRS-aware exports, and release-zone workflows.
- **Operational terrain/input geodata:** swissALTI3D and related swisstopo
  layers provide terrain and map context for future production-style workflows,
  but they do not validate model physics by themselves.

## Inconsistencies and Gaps

- The original Chant Sura trajectory subset is short and ballistic; it is useful
  for kinematic traceability but weak for contact validation.
- The segmented-contact fixture improves contact observability but is still a
  small RF16-only subset. It does not replace full-campaign trajectory,
  deposition, or shape validation.
- Scarring calibration uses impact-level quantities, while Tschamut validation
  uses trajectory/deposition quantities. Parameters must not be transferred
  without explicit comparative experiments.
- Tschamut currently under-runs observations; adding scarring increases energy
  loss and worsens that mismatch, suggesting terrain/model structural error
  rather than a simple scarring-parameter issue.
- Only a tiny derived Chant Sura input DEM crop is checked in. The full
  `Input.7z` archive remains ignored raw data and must not be committed.

## Operating Rules

- Keep calibration and validation separate in file paths, reports, and wording.
- Use Chant Sura trajectory data for trajectory/physics validation, not
  parameter tuning.
- Use Lu/ESurf impact tables for scarring calibration only.
- Use Tschamut as deposition-level validation only unless a separate
  trajectory-focused preprocessing pipeline is added.
- Keep swisstopo operational input geodata separate from experimental
  calibration and validation datasets.
- Do not commit large swisstopo raw tiles or imagery; use metadata records and
  small intentional fixtures only.
- Do not claim operational hazard validity from any single dataset.
