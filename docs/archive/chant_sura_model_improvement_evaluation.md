# Chant Sura Model-Improvement Evaluation

This evaluation uses the checked-in Chant Sura trajectory subset as the primary
reference for rapid model-development decisions. It does not modify the dataset
or the permanent validation case. Temporary ignored case files and reports were
generated under `validation/results/chant_sura_model_eval/`.

## Reference Setup

Source validation case:
`validation/cases/chant_sura_trajectory_subset.yaml`.

Observed data:

- three public reconstructed first-flight segments: `RF16W200r1`,
  `RF16W800r1`, and `RF18W200r1`;
- 153 observed trajectory samples;
- position, velocity, translational kinetic energy, rotational diagnostics, and
  total energy from the EnviDat `Output.7z` archive;
- equivalent-sphere radii inferred from mass for the current spherical model.

The current subset is intentionally short and deterministic. It primarily tests
free-flight kinematics and translational energy consistency. It does not yet
exercise full terrain contact, deposition, or shape-controlled runout.

## Candidate Runs

All variants used the same observed samples and release states.

| Variant | Change from baseline | Shape mean error (m) | Shape p95 error (m) | Energy relative error | Proxy jump-height error (m) | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Baseline | `translational_v0`, no roughness, no scarring | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | Current exact-gravity free-flight model matches the selected first-flight segments within interpolation/preprocessing precision. |
| `sphere_rotational_v1` | Enables rotational contact model | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | No trajectory-metric change on the observed first-flight segments; the contact model is not the limiting mechanism here. |
| Low roughness | `stochastic_contact_v1`, low perturbation scales | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | No effect on the observed first-flight trajectory metrics because roughness acts at contact. |
| High roughness | `stochastic_contact_v1`, higher perturbation scales | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | Same as low roughness; useful for runout/deposition ensembles, not for this first-flight subset. |
| `scarring_contact_v1` | Impact-local scarring energy loss enabled | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | No trajectory-metric change on observed first-flight segments; scarring is an impact-level mechanism. |
| Rotational + scarring | `sphere_rotational_v1` plus `scarring_contact_v1` | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | No improvement for the current trajectory subset; changes only occur outside the measured first-flight window. |
| Lower clearance plane | Flat proxy plane lowered by 0.5 m | `1.31e-5` | `2.97e-5` | `5.05e-5` | `7.90e-5` | No observed-window change; it only affects later contact timing outside the selected segment. |
| Higher clearance plane | Flat proxy plane raised by 0.5 m | `5.90e-4` | `3.02e-5` | `6.06e-3` | `7.90e-5` | Degrades trajectory/energy metrics by introducing premature contact in the simulated continuation. |

## What Actually Changes Trajectory Physics?

For the current Chant Sura subset, the only mechanism that matters for the
reported trajectory metrics is the free-flight state update with the observed
initial positions and velocities. The baseline already matches the reconstructed
first-flight segments closely because the model uses exact constant-gravity
kinematics.

Contact-related extensions do not improve these metrics because the selected
observed segments end before terrain contact becomes the controlling process.
They can change representative continuation diagnostics such as impact-event
count, angular speed, or scarring energy after the observed segment, but those
changes are not constrained by the current observed trajectory samples.

The higher clearance-plane variant is the only tested change that materially
degrades the trajectory metrics. That is useful: it shows the Chant Sura subset
is sensitive to terrain/contact timing when the proxy terrain is moved into the
flight path. It also confirms that premature contact is harmful for short-flight
trajectory realism.

## Candidate Ranking

1. **DEM-backed Chant Sura trajectory/contact validation.** This recommendation
   has been implemented as both a small RF16W200r1 experiment in
   `validation/cases/chant_sura_contact.yaml` and an extended multi-trajectory
   experiment in `validation/cases/chant_sura_contact_extended.yaml`. Both are
   documented in `docs/chant_sura_contact_validation.md`. A held-out split in
   `docs/chant_sura_contact_generalization.md` now tests whether the rotational
   contact result generalizes to disjoint trajectory IDs. The fixtures expose
   the model to real terrain-contact timing, but remain qualitative subsets
   rather than full-campaign validation.
2. **Observed impact-event alignment beyond segment-boundary proxies.** The
   public trajectory text files concatenate jump segments with local time resets,
   and the current preprocessing preserves segment IDs. The remaining
   observational need is to align those proxy events with direct impact or
   sensor timing where public data support it.
3. **Non-spherical shape representation.** Chant Sura includes rock-shape data
   and is scientifically suited to shape-effect validation, but this should
   follow DEM/contact alignment so shape effects are not confounded with terrain
   errors.
4. **Contact roughness and scarring transfer experiments.** These mechanisms
   matter for runout and deposition after impacts, but the current Chant Sura
   subset does not constrain them. They should remain calibrated/evaluated with
   impact-level or deposition-level datasets until richer Chant Sura contact
   observations are integrated.
5. **`sphere_rotational_v1` as a trajectory improvement.** It is important for
   future rolling/contact behaviour and improves DEM-backed contact-fixture
   shape and energy metrics, but it does not improve all contact metrics and
   should remain opt-in until broader validation supports a default change.

## Recommendation

The next model-development feature should not be another contact-physics option.
The immediate blocker is observational and terrain coupling: add a Chant
Sura-focused DEM and segmented-trajectory validation pipeline so candidate
contact and shape physics are tested where they can actually act.

Concretely, the next feature should be:

1. extract a small Chant Sura DEM patch from the public input archive;
2. preserve trajectory segment IDs instead of only first monotonic segments;
3. add validation metrics for segment-level impact timing, rebound velocity,
   post-impact energy change, and jump-height envelopes;
4. then re-run the same candidate comparison.

Until that exists, the clear answer is:

> For trajectory realism in the current Chant Sura subset, no contact extension
> improves the model because the subset validates first-flight kinematics, not
> contact. Terrain/contact timing is the first mechanism that must be made
> observable before roughness, scarring, rotation, or shape can be ranked
> scientifically.
