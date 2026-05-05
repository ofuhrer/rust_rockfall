# Scarring Impact Inspection

This manual inspection uses the v0.4.0 impact-event diagnostics to reconstruct a small number of synthetic `scarring_contact_v1` impacts. It does not change simulation physics, validation cases, or calibration workflows.

## Inspection Setup

Two temporary flat-plane cases were generated under `/tmp/rust_rockfall_scarring_inspection/` with identical block, contact, and soil/scarring parameters:

- block: sphere, `mass = 50 kg`, `radius = 0.5 m`
- terrain: horizontal plane, `z = 0`
- contact: `normal_restitution = 0.4`, `tangential_restitution = 0.85`, `friction_coefficient = 0.4`
- soil interaction: `scarring_contact_v1`
- soil/scarring parameters: `soil_strength_pa = 500000`, `scarring_drag_coefficient = 0.01`, `scarring_layer_density_kgpm3 = 1600`
- scar depth: computed from the empirical scaling, not prescribed by `scarring_max_depth_m`
- timestep: `dt = 0.005 s`
- seed: `777`

The low-energy release was `[position = (0, 0, 1), velocity = (1, 0, -0.2)]`. The higher-energy release was `[position = (0, 0, 4), velocity = (2, 0, -0.5)]`.

Temporary outputs:

- `/tmp/rust_rockfall_scarring_inspection/results/scarring_low_energy_impacts.csv`
- `/tmp/rust_rockfall_scarring_inspection/results/scarring_high_energy_impacts.csv`
- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_low_energy/`
- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_high_energy/`

These are diagnostic artifacts and are intentionally not tracked.

## Reconstructed Impacts

### Low-Energy Case, First Impact

This is the first significant contact in the low-energy trajectory.

| Quantity | Value |
| --- | ---: |
| impact time | `0.300 s` |
| impact angle | `17.65 deg` |
| incoming normal speed | `3.143 m/s` |
| incoming tangential speed | `1.000 m/s` |
| incoming speed | `3.298 m/s` |
| post-contact speed | `1.518 m/s` |
| post-scarring speed | `1.492 m/s` |
| post-step speed | `1.492 m/s` |
| pre-contact kinetic energy | `271.961 J` |
| post-contact kinetic energy | `57.576 J` |
| post-scarring kinetic energy | `55.623 J` |
| post-step kinetic energy | `55.623 J` |
| scarring depth | `0.0885 m` |
| scarring area | `0.2535 m2` |
| scarring drag force | `22.06 N` |
| uncapped scarring work | `1.954 J` |
| capped scarring loss | `1.954 J` |
| depth source | `computed` |

Energy accounting:

- contact response removed `214.385 J`;
- scarring removed `1.954 J`;
- same-step update removed `0.000 J`;
- scarring loss was `0.72%` of pre-contact kinetic energy and `3.39%` of post-contact kinetic energy.

The velocity reduction is consistent with the energy loss: the post-contact speed drops from `1.518 m/s` to `1.492 m/s` without a direction change from the scarring layer.

### Higher-Energy Case, First Impact

This is the first impact after the larger drop.

| Quantity | Value |
| --- | ---: |
| impact time | `0.800 s` |
| impact angle | `13.47 deg` |
| incoming normal speed | `8.348 m/s` |
| incoming tangential speed | `2.000 m/s` |
| incoming speed | `8.584 m/s` |
| post-contact speed | `3.747 m/s` |
| post-scarring speed | `3.436 m/s` |
| post-step speed | `3.436 m/s` |
| pre-contact kinetic energy | `1842.228 J` |
| post-contact kinetic energy | `351.006 J` |
| post-scarring kinetic energy | `295.113 J` |
| post-step kinetic energy | `295.113 J` |
| scarring depth | `0.1934 m` |
| scarring area | `0.4901 m2` |
| scarring drag force | `288.95 N` |
| uncapped scarring work | `55.894 J` |
| capped scarring loss | `55.894 J` |
| depth source | `computed` |

Energy accounting:

- contact response removed `1491.221 J`;
- scarring removed `55.894 J`;
- same-step update removed `0.000 J`;
- scarring loss was `3.03%` of pre-contact kinetic energy and `15.92%` of post-contact kinetic energy.

This event is physically interpretable: higher incoming speed produces a larger computed scar depth, a larger projected scar area, a much larger drag-force diagnostic, and a larger energy loss. The loss is uncapped and exactly matches the difference between post-contact and post-scarring translational kinetic energy within numerical tolerance.

### Higher-Energy Case, Second Impact

This is a later rebound impact with lower normal speed.

| Quantity | Value |
| --- | ---: |
| impact time | `1.425 s` |
| impact angle | `26.92 deg` |
| incoming normal speed | `3.069 m/s` |
| incoming tangential speed | `1.559 m/s` |
| incoming speed | `3.443 m/s` |
| post-contact speed | `1.806 m/s` |
| post-scarring speed | `1.783 m/s` |
| pre-contact kinetic energy | `296.281 J` |
| post-contact kinetic energy | `81.574 J` |
| post-scarring kinetic energy | `79.521 J` |
| scarring depth | `0.0869 m` |
| scarring drag force | `23.63 N` |
| capped scarring loss | `2.053 J` |

The second impact is close to the low-energy first impact in normal speed and scarring response. This is the expected qualitative trend: the scarring model primarily responds to normal impact speed for depth and to total incoming speed through the drag-force diagnostic.

## Visual Cross-Check

The x-z trajectory plots show the expected qualitative behavior:

- the higher-energy case has a deeper first fall, larger first rebound, and larger post-impact runout than the low-energy case;
- impact markers align with the sphere-center terrain offset (`terrain + radius`);
- the energy plots show stepwise total-energy loss at impacts;
- the high-energy first impact has a visibly larger total-energy drop than the low-energy first impact.

The plots used for this inspection are:

- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_low_energy/scarring_low_energy_trajectory_xz.png`
- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_low_energy/scarring_low_energy_energy.png`
- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_high_energy/scarring_high_energy_trajectory_xz.png`
- `/tmp/rust_rockfall_scarring_inspection/plots/scarring_high_energy/scarring_high_energy_energy.png`

## Cross-Impact Trends

The selected impacts support the intended qualitative scaling:

- normal impact speed increases from `3.143 m/s` to `8.348 m/s`;
- computed scar depth increases from `0.0885 m` to `0.1934 m`;
- scar area increases from `0.2535 m2` to `0.4901 m2`;
- drag-force diagnostic increases from `22.06 N` to `288.95 N`;
- scarring energy loss increases from `1.954 J` to `55.894 J`.

No selected event shows energy creation. For each selected event:

```text
post_scarring_translational_energy
= post_contact_translational_energy - scarring_capped_energy_loss
```

within floating-point tolerance.

## Issues Found

The individual impact records are physically reconstructable, but the inspection found one diagnostic consistency issue:

- The low-energy temporary case reported `impact_count = 6` in the standard verification metrics but wrote `59` impact-event rows.

The difference is explainable from the current implementation: impact events are emitted when the contact response reports an impact, while the existing `impact_count` metric is inferred later from trajectory samples whose `contact_state` can be overwritten by same-step sliding/stopping logic. Near the end of the low-energy trajectory, many very small impacts occur close to the terrain at speeds as low as `0.035 m/s`, with scarring losses around `1.8e-7 J`.

This is not necessarily a physics bug, but it is a diagnostic semantics problem. It is now resolved by documenting and reporting separate metrics:

- `impact_event_count`: all raw event-log records;
- `impact_count`: the legacy trajectory-state transition count;
- `significant_impact_count`: event-log records with `incoming_normal_speed_mps >= 0.05 m/s`.

## Conclusion

Conclusion: **individual scarring impacts are physically interpretable, with impact-count semantics now explicitly separated.**

For representative impacts, the event log is sufficient to reconstruct kinematics, normal/tangential geometry, contact energy loss, scarring work, and post-step state. The scarring response scales in the expected direction with impact speed and remains dissipative.

The remaining caution is that raw event totals can include low-energy contact chatter. Calibration objectives should use `significant_impact_count` or impact-energy/scarring-energy summaries when physically meaningful impacts are intended, and should reserve `impact_event_count` for audit trails.
