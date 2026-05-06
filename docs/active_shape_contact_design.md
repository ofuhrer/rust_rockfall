# Active Shape-Contact Design

Status: design-only Work Package 2 document. This document defines a minimal
opt-in active shape-contact plan named `shape_contact_v0_design_only`. It does
not implement physics, change defaults, tune parameters, calibrate terrain or
materials, copy proprietary RAMMS internals, or claim operational validity.

## Scientific Objective

The objective is to define the smallest independently specified active
shape-contact model that can be tested against the current public failure modes
without tuning. The model should use existing passive `shape_metadata_v1`
records as active geometry and inertia inputs only when a case explicitly opts
in.

The design target is not RAMMS equivalence. Public RAMMS documentation and the
Leine et al. rigid-body literature motivate the need for shape, orientation,
support points, inertia, and contact regimes, but this design must remain an
open, auditable approximation with its own equations, diagnostics, and failure
criteria.

The immediate scientific question is:

> Can one minimal active shape slice reduce the public Tschamut contact-rich
> early-stopping failure of `translational_v0` without reproducing the broad,
> high-energy, systematic over-run failure of `sphere_rotational_v1`, while
> preserving or improving Chant Sura trajectory/contact diagnostics?

## Evidence Baseline

Work Package 1 uses all 80 usable public Tschamut LPS/overview runs and excludes
31 overview rows for reproducible data-availability reasons. It reports:

- `translational_v0` under-runs by about 35 m on average;
- `sphere_rotational_v1` over-runs by about 105 m on average;
- baseline high-impact/contact-rich trajectories systematically under-run;
- several baseline outliers stop within about 1-2 m while accumulating hundreds
  of significant contacts;
- rotational output is broad, high-energy, and over-runs 79 of 80 releases;
- block and shape effects are relevant, but remain confounded with terrain path,
  observed runout, and release location.

Chant Sura contact-validation evidence remains complementary:

- `sphere_rotational_v1` improves trajectory-shape and kinetic-energy metrics
  over `translational_v0` in model-selection and held-out fixtures;
- rebound velocity, jump-height envelope, and impact timing do not improve;
- segment-boundary contacts are proxies, not instrumented impact truth;
- the current equivalent sphere cannot use EOTA or Tschamut shape observations
  dynamically.

This design must be judged against both datasets. Tschamut constrains
deposition/runout and hazard-layer failure modes; Chant Sura constrains
trajectory and contact behavior.

## Failure Modes To Address

The first active shape-contact slice aims to address:

- contact-rich early stopping in `translational_v0`, especially Tschamut cases
  with high significant-impact counts, very short simulated paths, and large
  negative runout errors;
- missing orientation-dependent energy partitioning between translation and
  rotation;
- missing shape-dependent support geometry that can alternate between sliding,
  rolling, rocking, and tumbling instead of treating every block as a sphere;
- missing block-specific behavior for public Tschamut blocks 1, 2, and 4;
- equivalent-sphere limitations in Chant Sura rebound and jump diagnostics.

## Failure Modes Not To Worsen

The first active shape-contact slice must not:

- create a `sphere_rotational_v1`-style systematic Tschamut over-run;
- increase broad high-energy reach or 10 kJ exceedance footprint without
  independent evidence;
- increase lateral spread simply by injecting extra rotational transport;
- degrade Chant Sura trajectory-shape or kinetic-energy diagnostics relative to
  the current rotational sphere recommendation;
- hide terrain/material deficiencies behind uncalibrated shape constants;
- change results for existing `translational_v0` or `sphere_rotational_v1`
  cases;
- reinterpret passive shape sidecars as active dynamics unless the case opts in.

## Minimal Implementation Slice

The first implementation slice should be one shape family only:
`principal_dimensions_box_v0`.

Rationale:

- Tschamut public sidecars for blocks 1, 2, and 4 are already represented as
  principal dimensions.
- Box inertia and support functions are analytic, testable, and deterministic.
- A box support point is the simplest non-spherical approximation that can
  represent blocky, elongate, and plate-like behavior without full polyhedral
  mesh contact.
- It keeps the model smaller than a general convex-hull contact solver.

The model name for a later implementation should be explicit and opt-in, for
example:

```yaml
parameters:
  contact_model: shape_contact_v0
block_shape:
  metadata_path: data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml
```

Until implementation is approved, this document uses
`shape_contact_v0_design_only`.

Fallback behavior:

- if `contact_model` is not `shape_contact_v0`, current sphere behavior is
  unchanged;
- if `shape_contact_v0` is requested without compatible shape metadata, the
  future parser should fail clearly rather than silently falling back;
- compatibility cases may explicitly choose `shape_contact_v0` with
  `shape_type: sphere` only as a verification bridge, not as the main model.

## Active State Variables

The active state for `shape_contact_v0` should extend the current body state
only in the opt-in path:

- center-of-mass position `x_m`;
- center-of-mass velocity `v_mps`;
- angular velocity `omega_radps` in world coordinates;
- orientation quaternion `q_wxyz`;
- constant body-frame principal inertia tensor `I_body_kg_m2`;
- world-frame inertia tensor `I_world = R(q) I_body R(q)^T`;
- active shape dimensions and support-function metadata;
- contact/regime diagnostics for the current step.

Existing `BodyState` and trajectory outputs should not be changed for existing
models unless an additive, backward-compatible field path is explicitly
approved.

## Orientation Representation

Use unit quaternions in `[w, x, y, z]` order, matching the passive shape scaffold.

Initialization:

- first slice: deterministic `identity` or `fixed_quaternion` only;
- public Tschamut block sidecars should use deterministic orientation
  initialization recorded in the case or sidecar;
- randomized orientation sampling is deferred until there is a documented seed
  policy and a no-tuning evaluation design.

Integration concept:

- free flight integrates orientation from angular velocity with a stable
  quaternion update;
- the quaternion is normalized after each update and the normalization error is
  reported as a diagnostic;
- no Euler-angle state is introduced.

## Active Inertia Usage

For `principal_dimensions_box_v0`, use analytic box principal moments:

```text
Ixx = (1/12) m (ly^2 + lz^2)
Iyy = (1/12) m (lx^2 + lz^2)
Izz = (1/12) m (lx^2 + ly^2)
```

The inertia tensor is active only in `shape_contact_v0`. Existing
`sphere_rotational_v1` keeps the solid-sphere inertia. Diagnostics should label:

- active inertia model;
- body-frame principal moments;
- world-frame rotational kinetic energy;
- passive sidecar moments, if different from the active model.

No empirical inertia scaling should be introduced in the first slice.

## Contact Geometry Abstraction

Define a minimal support-function trait for convex body approximations:

```text
support_body(d_body) -> r_body
support_world(d_world, q) = R(q) support_body(R(q)^T d_world)
```

For a box, `support_body(d)` returns the corner with signs chosen from the
direction vector. For terrain contact with normal `n`, the support point below
the center of mass is:

```text
r = support_world(-n, q)
p_contact = x + r
```

Clearance concept:

```text
gap = (p_contact - terrain_point_at(p_contact.x, p_contact.y)) . n
```

The first slice should keep the existing heightfield terrain assumption. It
should not attempt general overhangs, multi-contact terrain facets, or exact
closest-point distance to a triangulated surface.

## Contact Point And Support Selection

First slice:

- choose a single active support point against the local terrain normal;
- evaluate terrain height and normal at the support point horizontal position;
- recompute support point using that terrain normal;
- project only enough to remove penetration along the terrain normal;
- record selected support vertex/corner signs in diagnostics.

This is intentionally not full polyhedral contact. It may miss edge/face
multi-contact states, but it is testable and can expose whether even a single
orientation-dependent support point changes the WP1 failure modes.

Deferred support features:

- multiple simultaneous support points;
- edge and face contact patches;
- complementarity/contact-set solvers;
- contact persistence and stick/slip history;
- shape-specific terrain roughness sampling.

## Normal Impulse Concept

At the selected support point, compute contact-point velocity:

```text
v_c = v + omega x r
v_n = v_c . n
```

For incoming contact (`v_n < 0`), apply a normal impulse:

```text
J_n = -(1 + e_n) v_n / (1/m + n . ((I_world^-1 (r x n)) x r))
```

Then update:

```text
v+ = v + (J_n / m) n
omega+ = omega + I_world^-1 (r x (J_n n))
```

For resting/sliding contact, enforce non-penetration without adding rebound
energy. The exact low-speed threshold should reuse existing stop/contact
settings rather than introduce a hidden new parameter.

## Tangential And Friction Impulse Concept

Compute tangential contact velocity:

```text
v_t = v_c - (v_c . n) n
```

If `|v_t|` is nonzero, choose tangential direction `t = -normalize(v_t)`.
Compute the uncapped impulse needed to reduce tangential slip:

```text
J_t_free = -v_t / effective_mass_t
```

Cap it by Coulomb friction:

```text
|J_t| <= mu J_n
```

Use the capped tangential impulse to update linear and angular velocity:

```text
v+ = v+ + J_t / m
omega+ = omega+ + I_world^-1 (r x J_t)
```

The first slice should use the existing global or terrain-class values for
`e_n`, `e_t`, and `mu`. It should not add new tuned shape/friction parameters.
Tangential restitution can be represented as a bounded slip-reduction target,
but must remain dissipative by construction.

## Rolling, Sliding, And Tumbling Regimes

Regime labels should be diagnostic, not separate hidden solvers in the first
slice:

- `impact`: incoming support-point normal speed above the significant-contact
  threshold;
- `sliding`: support point remains near terrain and tangential slip is above the
  stop threshold;
- `rolling`: support point remains near terrain and tangential slip is small,
  with angular motion consistent with support-point transport;
- `tumbling`: angular kinetic energy and changing support corners dominate while
  the center of mass remains intermittently airborne or impact-dominated;
- `stopped`: center-of-mass and support-point velocities are below existing stop
  criteria and downslope gravity cannot overcome friction.

The first implementation should avoid a broad tumbling heuristic that changes
forces. It should record tumbling indicators, such as support-corner changes per
second and rotational-to-translational energy ratio, then use validation
evidence before making tumbling a separate dynamics branch.

## Energy Accounting

Energy accounting must be explicit before implementation:

- translational kinetic energy: `0.5 m |v|^2`;
- rotational kinetic energy: `0.5 omega . I_world omega`;
- potential energy: `m g z_com`;
- contact normal impulse work proxy;
- tangential/friction impulse work proxy;
- numerical projection energy change;
- total energy before and after each contact event.

Required invariant:

- with `e_n <= 1`, dissipative tangential impulse, no scarring, and no external
  energy source, a contact event must not create positive total mechanical
  energy beyond a documented numerical tolerance.

Any positive energy jump must be recorded as a failure in verification or as an
explicit diagnostic warning in validation.

## Diagnostics And Manifest Fields

Trajectory diagnostics should be additive and opt-in. Candidate per-sample
fields:

- `orientation_wxyz`;
- `active_shape_type`;
- `support_point_x_m`, `support_point_y_m`, `support_point_z_m`;
- `support_corner_signs`;
- `contact_point_speed_mps`;
- `contact_point_normal_speed_mps`;
- `contact_point_tangent_speed_mps`;
- `shape_regime`;
- `orientation_norm_error`;
- `rotational_to_translational_energy_ratio`.

Impact-event diagnostics should include:

- selected support point before and after contact;
- terrain normal at support point;
- normal impulse `J_n`;
- tangential impulse magnitude and Coulomb cap;
- pre/post translational and rotational energy;
- projection energy change;
- support-corner change flag.

Manifest fields should include:

- `active_contact_model: shape_contact_v0`;
- `active_contact_shape: principal_dimensions_box_v0`;
- `shape_metadata_path`;
- `orientation_initialization_mode`;
- `active_inertia_model`;
- `principal_moments_kg_m2`;
- `support_selection: single_support_point_from_terrain_normal`;
- `multi_contact: false`;
- `defaults_changed: false`;
- warnings that the model is experimental, opt-in, uncalibrated, and not
  operational.

## Opt-In And Default Policy

Defaults remain unchanged:

- `translational_v0` remains the default contact model;
- `sphere_rotational_v1` remains opt-in and recommended only for current
  trajectory/contact experiments;
- passive `block_shape.metadata_path` remains passive unless
  `contact_model: shape_contact_v0` is explicitly selected;
- existing validation cases and examples must produce unchanged results unless
  they opt in.

An eventual implementation is new opt-in physics and therefore requires a minor
version bump. A default change would require a separate major-version decision
and is explicitly out of scope.

## Verification Tests Before Implementation

The implementation should not start until these tests are written as expected
contracts:

- mass and inertia consistency for `principal_dimensions_box_v0`;
- rejection of non-positive dimensions, mass, and inertia;
- quaternion normalization and finite-value validation;
- deterministic orientation initialization;
- free-flight conservation of translational, rotational, and total energy with
  no contact;
- flat-plane resting/contact sanity for a box with identity orientation;
- no positive energy creation under dissipative normal/tangential impacts;
- Coulomb cap enforcement for tangential impulse;
- deterministic fixed-seed behavior for identical case and trajectory IDs;
- backward compatibility proving `translational_v0` and `sphere_rotational_v1`
  outputs are unchanged when shape contact is absent;
- failure when `shape_contact_v0` is requested without compatible shape
  metadata;
- no-tuning public Tschamut comparison case generation;
- Chant Sura trajectory/contact comparison cases for model-selection and
  held-out splits.

## No-Tuning Evaluation Criteria From WP1

The first no-tuning evaluation must compare `translational_v0`,
`sphere_rotational_v1`, and `shape_contact_v0` with frozen parameters.

Required Tschamut criteria:

- reduce baseline contact-rich early stopping, especially high-impact and
  short simulated-path groups;
- avoid rotational-style systematic over-run across the 80-run all-usable set;
- do not increase broad high-energy reach, 10 kJ exceedance, or 2 m jump-height
  footprint without evidence;
- compare block-specific behavior for blocks 1, 2, and 4;
- report observed-runout, impact-count, path-length, and block-group metrics;
- report failures even if the new model is worse than both sphere models.

Required Chant Sura criteria:

- preserve or improve trajectory-shape mean error;
- preserve or improve kinetic-energy relative error;
- avoid worsening jump-height envelope, rebound velocity, and impact timing
  without a clear explanation;
- evaluate both model-selection and held-out segmented-contact splits.

No aggregate pass is allowed to hide subgroup failures. The report must include
under/near/over counts, lateral spread, energy footprint, and significant-impact
density.

## Explicit Deferrals

This design defers:

- full polyhedral contact;
- multi-contact complementarity solvers;
- terrain/material calibration;
- parameter search or optimization;
- roughness, scarring, or terrain-class tuning;
- forest, barrier, protection-structure, and fragmentation physics;
- GeoTIFF/COG productization;
- default model changes;
- operational hazard claims;
- risk modelling with exposure or vulnerability.

## Go / No-Go Before Implementation

Implementation should proceed only if the following are clear enough:

- the first slice is limited to `principal_dimensions_box_v0`;
- active state, inertia, support point, and impulse equations are agreed;
- diagnostics and manifest labels are sufficient to audit energy and support
  selection;
- verification tests can be written before or alongside code;
- WP1 no-tuning evaluation tables are fixed and reusable;
- Chant Sura model-selection and held-out comparisons are part of the gate;
- current defaults and current models remain backward compatible.

Assumptions still uncertain:

- whether single-support-point box contact is sufficient to change Tschamut
  early stopping without over-transporting energy;
- whether Tschamut block grouping is causal or mostly terrain/path confounding;
- whether public shape dimensions represent contact-relevant support geometry
  well enough for active dynamics;
- whether equivalent centre-of-mass alignment in Chant Sura is adequate for
  shape contact;
- how sensitive the first slice will be to DEM resolution and terrain normals.

Terrain/material calibration should become preferable before coding if:

- WP1 follow-up grouping shows terrain path or material class explains the
  mismatch more strongly than block shape;
- single-support-point shape contact cannot define testable non-tuned equations;
- energy accounting requires hidden damping parameters to avoid over-run;
- the model can only improve Tschamut by adjusting friction/restitution values;
- Chant Sura diagnostics would be degraded by the shape slice without a
  physically interpretable reason.

## Design Decision

Proceed to implementation only after this design is reviewed and accepted as a
small, opt-in, testable physics extension. The recommended next coding slice,
if approved later, is not full rigid-body contact. It is a deterministic
`principal_dimensions_box_v0` support-point model with active quaternion
orientation, active box inertia, explicit contact impulses, additive
diagnostics, and no parameter tuning.
