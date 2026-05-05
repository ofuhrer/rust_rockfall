# Impact Diagnostics

Impact diagnostics are an optional reporting layer for reconstructing individual terrain impacts. They do not change simulation physics and are written only when a case requests `outputs.impact_events_csv` or `outputs.impact_events_json`.

## Purpose

Trajectory samples answer what happened over time. Impact events answer why one contact step changed the velocity and energy state. They are intended for:

- auditing restitution, friction, roughness, and scarring behavior at one impact;
- checking energy accounting before calibration experiments;
- comparing impact-level quantities with laboratory or field observations when those are available.

They are not a validation metric by themselves and do not imply RAMMS equivalence.

## Event Stages

Each event records four state snapshots:

- `pre_contact`: after ballistic motion brings the sphere into terrain contact, before contact response;
- `post_contact`: after restitution/friction impact response;
- `post_scarring`: after optional `scarring_contact_v1` energy removal;
- `post_step`: after same-step sliding/rolling/friction contact motion.

The trajectory CSV row for the same time corresponds to the `post_step` state. The impact-event record is therefore the source of truth for reconstructing the intermediate contact and scarring stages.

## Raw And Significant Impacts

The impact-event log is intentionally raw: one `ImpactEvent` is emitted whenever the contact response reports an impact. During low-energy near-rest motion this can include contact chatter with tiny normal approach speeds.

For interpretation and reporting, the validation metrics distinguish:

- `impact_event_count`: every raw impact-event record;
- `significant_impact_count`: event records with `incoming_normal_speed_mps >= 0.05 m/s`;
- `impact_count`: the older trajectory-sample transition metric, retained for backward compatibility.

Use `impact_event_count` for audit trails and `significant_impact_count` for physically meaningful impact comparisons. Do not assume `impact_event_count == impact_count`.

## Normal And Tangential Components

For each velocity snapshot, the event reports normal and tangential speed relative to the base terrain normal. `impact_angle_deg` is the angle between the incoming travel direction and the terrain normal:

```text
impact_angle = acos((-v_in / |v_in|) . n_terrain)
```

A vertical impact on a horizontal plane has an impact angle of `0 deg`. A shallow grazing impact has a larger angle.

## Scarring Fields

Scarring diagnostics are populated for every impact, but remain zero unless `soil_interaction_model: scarring_contact_v1` is active and the configured parameters produce nonzero depth and drag work.

- `scarring_depth_m`: scar depth used by the energy-loss estimate.
- `scarring_area_m2`: projected sphere-cap area.
- `scarring_drag_force_n`: velocity-squared drag-force diagnostic.
- `scarring_uncapped_energy_loss_j`: `drag_force * depth` before kinetic-energy capping.
- `scarring_capped_energy_loss_j`: energy actually removed from translational kinetic energy.
- `scarring_depth_source`: `none`, `computed`, `computed_capped`, `explicit`, or `explicit_capped`.
- `cumulative_scarring_energy_loss_j`: running sum over impacts.

## Worked Example

For a single oblique impact with scarring enabled:

1. Check `incoming_normal_speed_mps` and `incoming_tangent_speed_mps` to understand whether the event is steep or grazing.
2. Compare `post_contact_translational_j` and `post_scarring_translational_j`.
3. The difference should match `scarring_capped_energy_loss_j` within numerical tolerance.
4. Compare `post_scarring_*` with `post_step_*` to see whether same-step contact motion changed velocity further.
5. Check `scarring_uncapped_energy_loss_j >= scarring_capped_energy_loss_j`; equality means the drag-work estimate was not capped by available kinetic energy.

For example, if `post_contact_translational_j = 500 J`, `post_scarring_translational_j = 460 J`, and `scarring_capped_energy_loss_j = 40 J`, then the scarring layer removed 40 J after contact response and before same-step sliding/rolling updates.

## How To Generate

Add output paths to a benchmark case:

```yaml
outputs:
  diagnostics_json: verification/results/example.json
  trajectory_csv: verification/results/example.csv
  impact_events_csv: verification/results/example_impacts.csv
  impact_events_json: verification/results/example_impacts.json
```

Then run:

```bash
cargo run -- verify --case verification/synthetic/synthetic_scarring_energy_dissipation.yaml
```

The generated impact event files are diagnostic artifacts and should normally remain uncommitted.
