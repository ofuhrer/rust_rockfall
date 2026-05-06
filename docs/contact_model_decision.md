# Contact Model Decision

Status: active decision record for `v0.6.0`. This document reviews the DEM-backed Chant Sura contact-validation results and decides whether `sphere_rotational_v1` should become the recommended or default contact model for trajectory experiments. No defaults are changed by this decision.

## Decision

Recommendation: **treat `sphere_rotational_v1` as the current candidate opt-in contact model for trajectory-validation experiments, but keep `translational_v0` as the default for now.**

The rotational sphere model improves the strongest trajectory-level metrics in the Chant Sura model-selection and held-out contact fixtures, and it is physically better aligned with a rolling/bouncing rockfall model than a purely translational contact law. The evidence is now stronger for opt-in trajectory experiments, but still not broad enough to justify changing the repository default.

## Evidence

The initial comparison used the active DEM-backed RF16W200r1 Chant Sura contact fixture:

- `validation/cases/chant_sura_contact.yaml`
- `validation/cases/chant_sura_contact_rotational.yaml`
- `validation/cases/chant_sura_contact_roughness.yaml`
- `validation/cases/chant_sura_contact_scarring.yaml`

The initial fixture contains three segmented trajectory pieces and two segment-boundary contact/rebound proxies. The extended fixture adds five source trajectories, 16 segmented trajectory pieces, and 11 segment-boundary contact/rebound proxies:

- `validation/cases/chant_sura_contact_extended.yaml`
- `validation/cases/chant_sura_contact_extended_rotational.yaml`
- `validation/cases/chant_sura_contact_extended_roughness.yaml`
- `validation/cases/chant_sura_contact_extended_scarring.yaml`

These are diagnostic comparisons, not calibrated validation claims.

The internal held-out evaluation uses trajectory IDs that do not overlap the model-selection subset:

- `validation/cases/chant_sura_contact_heldout.yaml`
- `validation/cases/chant_sura_contact_heldout_rotational.yaml`

It contains 15 segmented trajectory pieces and 9 segment-boundary contact/rebound proxies. It is an internal disjoint holdout from the same RF16 DEM crop and preprocessing workflow, not an external independent validation dataset.

| Case | Model option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | `translational_v0` | 0.418 | 0.394 | 0.731 | 0.628 | 4.899 |
| Rotational | `sphere_rotational_v1` | 0.378 | 0.289 | 0.750 | 0.628 | 4.902 |
| Roughness | `stochastic_contact_v1` with `translational_v0` | 0.437 | 0.429 | 0.748 | 0.660 | 4.917 |
| Scarring | `scarring_contact_v1` with `translational_v0` | 0.431 | 0.426 | 0.707 | 0.628 | 4.892 |

Extended subset results:

| Case | Model option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Extended baseline | `translational_v0` | 0.563 | 0.498 | 0.713 | 0.683 | 4.281 |
| Extended rotational | `sphere_rotational_v1` | 0.529 | 0.427 | 0.742 | 0.683 | 4.355 |
| Extended roughness | `stochastic_contact_v1` with `translational_v0` | 0.564 | 0.502 | 0.700 | 0.690 | 4.241 |
| Extended scarring | `scarring_contact_v1` with `translational_v0` | 0.576 | 0.514 | 0.746 | 0.683 | 4.263 |

Held-out subset results:

| Case | Model option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Held-out baseline | `translational_v0` | 0.505 | 0.440 | 0.713 | 0.474 | 4.099 |
| Held-out rotational | `sphere_rotational_v1` | 0.475 | 0.391 | 0.744 | 0.477 | 4.150 |

## What Improved

For this decision, the primary comparison endpoints are trajectory-shape mean error and relative kinetic-energy error. Secondary endpoints are jump-height envelope, rebound velocity, and impact timing. `sphere_rotational_v1` improves the primary endpoints in the model-selection and internal held-out contact fixtures:

- initial fixture: shape mean error improves from `0.418 m` to `0.378 m`, about a 10% reduction;
- initial fixture: relative kinetic-energy error improves from `0.394` to `0.289`, about a 27% reduction;
- extended fixture: shape mean error improves from `0.563 m` to `0.529 m`, about a 6% reduction;
- extended fixture: relative kinetic-energy error improves from `0.498` to `0.427`, about a 14% reduction.
- held-out fixture: shape mean error improves from `0.505 m` to `0.475 m`, about a 6% reduction;
- held-out fixture: relative kinetic-energy error improves from `0.440` to `0.391`, about an 11% reduction.

This is scientifically plausible because the rotational model couples tangential impulse with angular velocity and rolling/sliding diagnostics. It gives the model a mechanism to exchange translational and rotational motion during contact, which the default `translational_v0` model lacks.

## What Worsened Or Stayed Flat

The improvement is not uniform:

- initial fixture jump-height envelope error worsens slightly from `0.731 m` to `0.750 m`;
- extended fixture jump-height envelope error worsens from `0.713 m` to `0.742 m`;
- held-out fixture jump-height envelope error worsens from `0.713 m` to `0.744 m`;
- initial fixture rebound velocity mean error is essentially unchanged and slightly worse, from `4.899 m/s` to `4.902 m/s`;
- extended fixture rebound velocity mean error worsens from `4.281 m/s` to `4.355 m/s`;
- held-out fixture rebound velocity mean error worsens from `4.099 m/s` to `4.150 m/s`;
- impact timing mean error is unchanged or effectively unchanged in all fixtures;
- the comparison still has large absolute rebound-velocity and timing errors.

The roughness case does not improve trajectory shape or energy in either fixture, though it slightly improves extended jump envelope and rebound velocity. The scarring case improves the original jump-height envelope and slightly improves rebound velocity in both fixtures, but worsens trajectory shape and energy error. This is consistent with adding impact energy loss without resolving the main trajectory discrepancy.

## Sample-Size Assessment

The sample is **stronger than the original two-event fixture and now includes held-out trajectory IDs, but still not sufficient to change defaults**.

Reasons:

- the extended fixture still uses only a small RF16 DEM crop;
- five source trajectories and 11 contact proxies are useful for model comparison but remain small relative to the public campaign;
- the held-out fixture adds six disjoint source trajectories and 9 contact proxies, but remains constrained to the same small DEM crop;
- the observed contact events are inferred from local time resets, not direct instrumented impact labels;
- the current equivalent-sphere height offset and DEM alignment are transparent but still modelling assumptions;

This evidence is enough to retain `sphere_rotational_v1` as a candidate opt-in model for trajectory experiments, but not enough to make a default-model change that would alter numerical behavior for all existing cases.

## Default Policy

Keep `translational_v0` as the default because:

- it preserves backward compatibility and existing verification baselines;
- it is simpler and easier to audit for minimal cases;
- existing validation and calibration workflows were built against that default;
- changing the default would be a semantic versioning event requiring broader evidence and migration notes.

Use `sphere_rotational_v1` as the **candidate opt-in model** when the experiment is specifically about trajectory realism, contact transitions, rolling/sliding behavior, or energy exchange between translation and spin. Report the worsened or unchanged secondary contact metrics alongside any primary-endpoint improvements.

## Future Default Criteria

`sphere_rotational_v1` should be reconsidered as the project default in a future version only after it satisfies all of the following:

- improves or matches `translational_v0` across a larger Chant Sura segmented-contact subset beyond the current RF16 DEM crop;
- improves or matches at least one independent trajectory/contact dataset outside the current Chant Sura split;
- does not degrade analytic verification behavior or deposition-level validation unexpectedly;
- has clear documentation for changed output interpretation, especially angular velocity, rolling residual, and contact state;
- has a versioned migration note explaining that the default contact model changed.

Changing the default would be a behavior change and should be treated as a future versioned decision, not a silent cleanup.

## Practical Recommendation

For current work:

- keep existing cases and examples on `translational_v0` unless they explicitly study contact-model effects;
- use `sphere_rotational_v1` for new Chant Sura trajectory/contact experiments while continuing to report `translational_v0` as a baseline;
- report both `translational_v0` and `sphere_rotational_v1` when comparing candidate physics changes;
- do not interpret roughness or scarring trajectory comparisons without also reporting the contact model used.

The immediate next scientific step is to move beyond equivalent spheres and segment-boundary proxy impacts: either add shape-aware contact for the Chant Sura EOTA rocks or align the split with direct public sensor/impact timing if those data can be processed reproducibly.
