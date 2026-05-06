# Tschamut scarring_contact_v1 Comparison

## Purpose

This document records a controlled trajectory-level comparison for the public-derived Tschamut 2014 validation subset. The question is narrow:

```text
Does enabling impact-level calibrated scarring_contact_v1 improve trajectory-level realism?
```

This is a comparative experiment, not a new operational validation claim.

## Cases

Two new validation cases were added without modifying the original `validation/cases/tschamut_basic.yaml` case:

- `validation/cases/validation_tschamut_baseline.yaml`
- `validation/cases/validation_tschamut_scarring.yaml`

The cases use the same:

- public-derived Tschamut release and deposition CSV files;
- IDW residual DEM terrain proxy;
- spherical block approximation;
- restitution and friction parameters;
- synthetic stochastic contact roughness;
- random seed and ensemble size.

The scarring case differs only by enabling:

```yaml
soil_interaction_model: scarring_contact_v1
soil_strength_pa: 500000.0
scarring_drag_coefficient: 1.0
scarring_layer_density_kgpm3: 1200.0
```

These parameters come from the Chant Sura / ESurf 2019 single-impact calibration experiment. They were not tuned to Tschamut trajectory runout or deposition.

## Commands

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
cargo run -- validate --case validation/cases/validation_tschamut_scarring.yaml
```

## Results

| metric | baseline | scarring | change |
| --- | ---: | ---: | ---: |
| observed mean runout (m) | `102.844` | `102.844` | `0.000` |
| simulated mean runout (m) | `71.702` | `64.456` | `-7.246` |
| runout distance error (m) | `31.142` | `38.388` | `+7.246` |
| deposition centroid error (m) | `31.018` | `38.208` | `+7.191` |
| deposition cloud mean-nearest error (m) | `23.882` | `30.295` | `+6.413` |
| deposition cloud overlap fraction | `0.917` | `0.000` | `-0.917` |
| lateral spread error (m) | `16.572` | `16.964` | `+0.392` |

Scarring diagnostics from the representative single trajectory in the scarring case:

| diagnostic | value |
| --- | ---: |
| maximum scarring depth (m) | `0.105` |
| maximum scarring drag force (N) | `3592.368` |
| total scarring energy loss (J) | `3565.376` |

## Interpretation

The baseline already under-runs the observed mean runout by about `31.1 m`. Enabling `scarring_contact_v1` shortens the simulated mean runout by another `7.25 m`, increasing the runout bias to about `38.4 m`.

This direction is physically expected. The current scarring model removes translational energy during impacts, so it should generally shorten trajectories when all other parameters are unchanged. For this Tschamut setup, that direction is not helpful because the dominant mismatch is already insufficient runout.

Deposition metrics also worsen in this experiment. The overlap fraction drops from `0.917` to `0.000`, and centroid and nearest-cloud errors increase. This indicates that the transferred Chant Sura single-impact scarring parameters do not improve trajectory-level realism for the current Tschamut model configuration.

## Answer

For the current v0.6.1 Tschamut setup:

```text
No. scarring_contact_v1 does not improve trajectory-level realism.
```

It moves the simulation in the physically expected direction for added energy loss, but that direction increases the existing under-runout bias.

## Limitations

- The scarring parameters are calibrated at impact level using Chant Sura / ESurf 2019 table data, not Tschamut trajectories.
- The Tschamut terrain is still a proxy IDW residual DEM, not an official field DEM.
- Blocks are spherical; real block shape and rotational shape effects are not represented.
- Forest, fragmentation, terrain-class parameters, and calibrated spatial roughness are absent.
- The scarring model has no drag torque, slip-dependent scarring, or terrain deformation memory.
- This comparison is not evidence against scarring physics in general; it only shows that this minimal opt-in model and transferred parameter set do not improve this trajectory-level case.

## Next Step

The next scientific step should not be hidden trajectory tuning of scarring parameters. More useful options are:

1. improve terrain and release-condition realism for Tschamut;
2. use impact-level Tschamut jump/impact measurements, if available, before trajectory-level scarring calibration;
3. constrain scarring parameters by material or impact tests and keep trajectory validation held out;
4. investigate block-shape and rotational contact effects, which are likely important for runout and deposition spread.
