# Scarring Contact v1 Review

## Decision

`scarring_contact_v1` is not ready for scientific calibration yet.

The current implementation is qualitatively plausible as an opt-in, dissipative compactable-soil diagnostic, and it is useful for synthetic verification. However, calibration would be premature because the available diagnostics do not yet let a reviewer reconstruct and explain a single impact cleanly. The next step should be impact-level diagnostic instrumentation, not parameter fitting.

## Current Implementation

The model is configured through `SoilInteractionModel` and `ScarringSettings`:

- `soil_interaction_model`: `none` by default, or `scarring_contact_v1`
- `soil_strength_pa`
- `scarring_drag_coefficient`
- `scarring_layer_density_kgpm3`
- `scarring_max_depth_m`

All defaults are inert. Negative soil/scarring parameters are rejected.

Scarring is triggered in `simulate_fixed_step` after the ballistic step, when the sphere is penetrating or touching terrain and the center velocity is incoming relative to the base terrain normal:

```text
signed_distance_sphere <= 0
v . n_terrain < 0
```

The contact response is resolved first using either `translational_v0` or `sphere_rotational_v1`. Scarring energy loss is then applied to the post-contact translational velocity before same-step contact friction/rolling motion is applied.

Depth is computed as follows:

- if `scarring_max_depth_m` is supplied, that value is used as the scar depth and capped at one sphere radius;
- otherwise depth follows a Lu/RAMMS-style scaling:

```text
d = 0.16 m^(1/4) ME^(-0.4) |v_n^-|^(0.8)
```

where `ME` is converted from `soil_strength_pa` to kPa. The one-radius cap is a numerical guard for the simple sphere-cap area model, not a calibrated law.

The effective projected sphere-cap area is:

```text
A = pi (2 R d - d^2)
```

The drag-force diagnostic and energy loss are:

```text
F_d = 0.5 C_d rho A |v^-|^2
E_loss = min(F_d d, post_contact_translational_kinetic_energy)
```

The implementation removes `E_loss` by scaling the post-contact translational velocity magnitude. It does not change direction, angular velocity, terrain geometry, or any persistent soil state.

Current trajectory-sample diagnostics are:

- `scarring_depth_m`
- `scarring_drag_force_n`
- `scarring_energy_loss_j`

These are per time step, not per impact event.

## Theory Comparison

The implementation captures several intended qualitative trends:

- scar depth increases with normal impact speed;
- scar depth increases with mass;
- scar depth decreases with soil strength;
- drag-force diagnostic increases with impact speed, scar area, layer density, and drag coefficient;
- energy loss is nonnegative and capped by available post-contact translational kinetic energy;
- scarring is impact-local and opt-in.

This aligns at a high level with Lu et al. 2019 and RAMMS-style scarring concepts: compactable soil can create penetration/scar depth, velocity-squared drag, and additional energy dissipation that should not be hidden inside global restitution/friction coefficients.

Important mismatches remain:

- Lu-style scarring separates penetration/scarring, sliding along a rebound plane, and rebound. The current model applies a single scalar energy removal after a standard contact response.
- RAMMS/Leine-style rigid-body contact couples forces, torques, contact points, shape, and rotation. The current model only scales translational velocity.
- The scarring force is not integrated over a penetration path or contact duration; it is converted to bounded work over an inferred depth.
- `scarring_max_depth_m` currently acts as a prescribed depth when present, not merely as an upper bound on an inferred depth.
- Scarring uses the base terrain normal, while stochastic roughness may use a perturbed effective contact normal for rebound.
- Same-step sliding or rolling updates can further change the sample velocity after scarring, making the sample row insufficient to isolate the impact.

## Diagnostic Sufficiency

Current diagnostics are enough to answer broad trajectory questions:

- Did scarring activate?
- What was the maximum inferred scar depth?
- What was the maximum drag-force diagnostic?
- How much scarring energy was removed over the trajectory?

They are not enough to explain an individual impact. Missing impact-level information includes:

- impact index and exact time-step context;
- position/contact point at impact;
- terrain normal and effective roughened contact normal;
- signed distance before projection;
- incoming velocity before contact response;
- outgoing velocity after contact response and before scarring;
- outgoing velocity after scarring;
- velocity after same-step sliding/rolling update;
- normal and tangential incoming speeds;
- impact angle;
- effective restitution and friction values used for that impact;
- inferred scar depth source: explicit depth vs empirical relation;
- whether depth was capped;
- scar area;
- uncapped drag work and capped energy loss;
- translational and rotational energy before contact, after contact, after scarring, and after same-step contact motion;
- cumulative scarring energy loss.

Without these fields, calibration would be hard to audit. A parameter set could appear to improve runout while individual impacts are losing energy for the wrong reason, at the wrong contact angle, or after the wrong contact response.

## Calibration Readiness

Final decision: **B) Not ready: diagnostics are insufficient.**

The physics is intentionally simple, but it is not the immediate blocker. The model is plausible enough for controlled synthetic experiments. The blocker is traceability: the current outputs do not provide an impact ledger. Calibration should wait until every scarring event can be inspected as a standalone physical event.

Tschamut should not be the first scarring calibration target. It is useful as a held-out plausibility case, but it does not currently provide the scar-depth and high-frequency impact measurements needed to constrain scarring parameters. A Lu/Chant Sura-style impact dataset is scientifically better for first calibration if public, license-compatible impact/scar observations are available.

## Minimal Next Step

Add diagnostic instrumentation only, with no physics change:

1. Add an `ImpactEvent` or `ScarringImpactEvent` struct in the simulation/diagnostic layer.
2. Populate one event per incoming terrain impact, whether or not scarring is active.
3. Include pre-contact, post-contact, post-scarring, and post-step velocities and energies.
4. Include terrain/effective normals, impact angle, scarring depth/area/force/work, cap flags, and cumulative scarring energy.
5. Add optional output paths such as `outputs.impact_events_csv` and/or `outputs.impact_events_json`.
6. Keep the trajectory CSV unchanged except for existing fields.
7. Add verification tests that reconstruct one horizontal and one oblique scarring impact from the event output.

Only after that instrumentation exists should calibration be considered. A first calibration should target measured scar depth and impact energy loss before using runout or deposition-cloud metrics.

## Bottom Line

`scarring_contact_v1` is a reasonable v0.4 research scaffold, but it is not field-calibration-ready. The next scientifically useful increment is an auditable impact-event log. If a single impact cannot be explained from the output, fitting scarring parameters would not be defensible.

## Implementation Follow-Up

The recommended impact-event log has been added as optional diagnostics through `outputs.impact_events_csv` and `outputs.impact_events_json`. A first single-impact proxy calibration workflow is documented in `scarring_single_impact_calibration.md`, and the first public-data Chant Sura table experiment is documented in `scarring_real_data_calibration.md`. This improves traceability and workflow reproducibility, but it does not by itself make `scarring_contact_v1` field-calibrated or field-valid. Real calibration still depends on inferred impact components and explicit objective functions, not hidden tuning against runout.
