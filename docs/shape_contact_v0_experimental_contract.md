# `shape_contact_v0` Experimental Contract

Status: implementation contract with verification-first scaffold started. This
document freezes the first active shape-contact prototype boundary,
diagnostics, evaluation plan, and falsification criteria. The current scaffold
recognizes `shape_contact_v0`, validates compatible metadata, and exposes pure
box-inertia/support/energy diagnostic helpers plus an internal
contact-preparation layer for analytic tests. The scaffold owns terrain/contact context,
support-gap classification, support geometry, mass, inertia, impulse
application, and available diagnostics so those quantities come from the same
validated shape metadata. A test-only single-contact state-transition wrapper
exercises the same path before runtime wiring. The helper is still not wired
into fixed-step simulation, and the patch does not change defaults, validation
baselines, terrain/material assumptions, or existing model behavior.

## Purpose

The first `shape_contact_v0` slice is a falsifiable no-tuning experiment:

> Can a deterministic non-spherical support-point model using public/passive
> principal-dimension shape metadata improve contact-rich trajectory behavior
> without creating the broad high-energy over-run failure of spherical rotation?

The prototype is justified only as an opt-in scientific feasibility test. It is
not a candidate default model, not a calibration mechanism, and not operational
hazard modelling.

## Evidence Baseline

The contract is based on the current benchmark evidence:

- Chant Sura model-selection, extended, and held-out contact fixtures show that
  `sphere_rotational_v1` improves trajectory-shape and kinetic-energy metrics
  relative to `translational_v0`, but does not improve rebound velocity,
  jump-height envelope, or impact timing.
- Public Tschamut all-runs grouped validation shows `translational_v0`
  under-runs by about 35 m on average and `sphere_rotational_v1` over-runs by
  about 105 m on average. High-impact baseline runs under-run most strongly.
- Tschamut registration sensitivity keeps `physics_selection_allowed=false`:
  runout sign is stable across transforms, but runout magnitude and
  deposition-overlap class vary materially.
- Mel de la Niva is currently an opt-in path-endpoint/deposition smoke
  workflow with timing and deposition-matching limitations. It is useful as a
  non-explosion/generalization smoke gate only.
- Passive Tschamut and Chant Sura shape metadata can carry dimensions, mass,
  inertia, orientation, and provenance, but they remain passive unless an
  explicit active model opts in.

## Implementation Boundary

The first implementation is allowed to do only the following:

- add a new opt-in contact model name: `shape_contact_v0`;
- support one active shape family: `principal_dimensions_box_v0`;
- use active quaternion orientation in `[w, x, y, z]` order;
- use analytic box principal inertia from mass and principal dimensions;
- select one terrain-normal support point per contact step;
- use existing restitution and friction parameters only;
- use existing terrain and heightfield assumptions;
- emit additive diagnostics and manifest fields;
- fail clearly when required shape metadata is missing, invalid, or
  incompatible.

The implementation must not:

- add new damping, calibration, terrain/material, roughness, restitution,
  friction, or shape-tuning parameters;
- add randomized orientation sampling;
- add a multi-contact solver;
- add full polyhedral mesh contact;
- add a separate tumbling force law;
- change `translational_v0`, `sphere_rotational_v1`, or default behavior;
- reinterpret passive shape metadata as active unless `shape_contact_v0` is
  explicitly selected;
- claim field validity, RAMMS equivalence, or operational readiness.

## Required Invariants

Hard invariants:

- all existing non-`shape_contact_v0` verification and validation cases remain
  numerically unchanged within their current tolerances;
- `translational_v0` continues to use its current contact geometry, inertia,
  diagnostics, and defaults;
- `sphere_rotational_v1` continues to use solid-sphere inertia and current
  contact behavior;
- passive `block_shape.metadata_path` remains passive for all existing contact
  models;
- invalid or missing active shape metadata fails before simulation;
- generated trajectory, impact, hazard, and manifest outputs are
  backward-compatible unless the case explicitly opts into additive
  `shape_contact_v0` diagnostics.

Any change that violates these invariants is out of scope for the first slice.

## Frozen Runtime Diagnostic Contract

Before `shape_contact_v0` may be wired into the fixed-step integrator, runtime
outputs must expose the exact per-contact row fields below. The output location
may be impact-event rows, trajectory metadata, or a dedicated diagnostic sidecar,
but the field names, units, nullability, and interpretation must remain stable.
This contract is not validation evidence; it is the audit surface required
before public benchmark execution.

Per-contact or impact-event row fields:

| Field | Unit / type | Required value and meaning |
| --- | --- | --- |
| `shape_contact_runtime_schema_version` | string | `shape_contact_runtime_diagnostic_v1`. |
| `case_id` | string | Validation, verification, or synthetic case identifier that produced the row. |
| `trajectory_id` | string | Stable trajectory identifier; deterministic for ensembles. |
| `step_index` | integer | Zero-based fixed-step index after which the row was emitted. |
| `time_s` | s | Simulation time associated with the post-contact state for the row. |
| `shape_contact_row_id` | string | Stable row identifier unique within a run, recommended format `{trajectory_id}:shape_contact:{step_index}` unless a future writer documents a stricter format. |
| `contact_event_id` | string/null | Existing impact-event identifier when the row is aligned with an impact-event output; null otherwise. |
| `impact_index` | integer/null | Existing impact-event index when aligned with impact-event outputs; null otherwise. |
| `active_contact_model` | string | Must be `shape_contact_v0`. |
| `active_shape_type` | string | Must be `principal_dimensions_box_v0` for the first runtime slice. |
| `shape_id` | string | Shape sidecar identifier used to build the active scaffold. |
| `contact_regime` | enum | One of `separated_moving_away`, `separated_moving_toward`, `touching`, or `penetrating` from the support-gap gate. |
| `shape_contact_regime_label` | enum | Non-null fixed v1 label serialized exactly as one of `non_impulsive_separated`, `non_impulsive_touching`, `non_impulsive_penetrating`, `impulsive_touching`, or `impulsive_penetrating`. |
| `support_signed_gap_m` | m | Signed gap from selected support point to the terrain contact plane along the terrain normal. Positive values are separated. |
| `contact_gap_tolerance_m` | m | Must record the active deterministic tolerance, initially `1.0e-9`. |
| `terrain_contact_point_x_m`, `terrain_contact_point_y_m`, `terrain_contact_point_z_m` | m | Explicit terrain point used for support-gap calculation. |
| `terrain_normal_x`, `terrain_normal_y`, `terrain_normal_z` | unit vector | Terrain normal used for support selection and impulse preparation after normalization. |
| `support_point_x_m`, `support_point_y_m`, `support_point_z_m` | m | Selected world support point from the validated box scaffold. |
| `support_corner_sign_x`, `support_corner_sign_y`, `support_corner_sign_z` | -1 or 1 | Selected box corner signs in body axes. Exact-zero tie breaks use positive signs. |
| `support_corner_changed` | bool/null | Whether the selected support corner changed from the previous emitted contact row. Null until previous-corner tracking exists. |
| `contact_point_normal_velocity_pre_mps` | m/s | Pre-impulse contact-point velocity projected onto the terrain normal. Incoming contact is negative. |
| `contact_point_normal_velocity_post_mps` | m/s | Post-impulse contact-point velocity projected onto the terrain normal. |
| `contact_point_tangential_speed_pre_mps` | m/s | Pre-impulse tangential contact-point speed magnitude. |
| `contact_point_tangential_speed_post_mps` | m/s | Post-impulse tangential contact-point speed magnitude. |
| `normal_impulse_n_s` | N s | Applied normal impulse; zero for non-impulsive rows. |
| `tangential_impulse_x_n_s`, `tangential_impulse_y_n_s`, `tangential_impulse_z_n_s` | N s | Applied tangential impulse vector in world coordinates. |
| `tangential_impulse_norm_n_s` | N s | Magnitude of applied tangential impulse. |
| `coulomb_friction_cap_n_s` | N s | `mu * normal_impulse_n_s`, or zero when no normal impulse exists. |
| `coulomb_cap_ratio` | dimensionless/null | `tangential_impulse_norm_n_s / coulomb_friction_cap_n_s`; null when the cap is zero. |
| `normal_restitution` | dimensionless | Active normal restitution used for this row. |
| `tangential_restitution` | dimensionless | Active tangential restitution used for this row. |
| `friction_coefficient` | dimensionless | Active Coulomb friction coefficient used for this row. |
| `gravity_mps2` | m/s^2 | Active gravitational acceleration used for ballistic prediction and energy accounting. |
| `pre_translational_kinetic_j` | J | Translational kinetic energy before contact update. |
| `post_translational_kinetic_j` | J | Translational kinetic energy after contact update. |
| `pre_rotational_kinetic_j` | J | Rotational kinetic energy before contact update. |
| `post_rotational_kinetic_j` | J | Rotational kinetic energy after contact update. |
| `pre_potential_energy_j` | J | Potential energy before contact update, using the same gravity as the step. |
| `post_potential_energy_j` | J | Potential energy after contact update, using the same gravity as the step. |
| `pre_total_mechanical_energy_j` | J | Pre-contact translational + rotational + potential energy. |
| `post_total_mechanical_energy_j` | J | Post-contact translational + rotational + potential energy. |
| `contact_energy_delta_j` | J | Energy delta from the impulse update only. This must be non-positive for dissipative analytic contacts within tolerance. |
| `projection_energy_delta_j` | J/null | Energy attributed to penetration correction/projection. Must be null while projection correction is deferred. |
| `total_energy_delta_j` | J | Must equal `post_total_mechanical_energy_j - pre_total_mechanical_energy_j`. While projection is deferred, it must also equal `contact_energy_delta_j`; when projection exists, it must equal `contact_energy_delta_j + projection_energy_delta_j`. |
| `rotational_to_translational_energy_ratio_pre` | dimensionless/null | Pre-contact rotational/translational kinetic energy ratio; null if translational kinetic energy is zero. |
| `rotational_to_translational_energy_ratio_post` | dimensionless/null | Post-contact rotational/translational kinetic energy ratio; null if translational kinetic energy is zero. |
| `orientation_w`, `orientation_x`, `orientation_y`, `orientation_z` | unit quaternion | Active orientation before contact update in `[w, x, y, z]` order. |
| `orientation_norm_error` | dimensionless | `abs(norm(q) - 1)`. |
| `orientation_initialization_mode` | string | Initially `identity`; any future value requires a new reviewed slice. |
| `impulse_applied` | bool | True only when the scaffold-owned impulse path changed the state. |
| `projection_applied` | bool | Must be false while projection correction is deferred. |

The field names above supersede earlier informal names such as
`active_contact_shape`, `contact_point_normal_speed_mps`, and
`shape_contact_regime` when runtime rows are implemented. Existing analytic test
struct field names may differ internally, but runtime exports must map to this
contract before any public `shape_contact_v0` run.

## Frozen Run-Manifest Contract

Any run manifest for a future public or validation `shape_contact_v0` run must
include an additive `shape_contact_v0` object with these exact fields:

| Field | Type | Required value and meaning |
| --- | --- | --- |
| `active_contact_model` | string | `shape_contact_v0`. |
| `active_shape_type` | string | `principal_dimensions_box_v0`. |
| `shape_metadata_path` | string | Path to the validated `shape_metadata_v1` sidecar. |
| `shape_metadata_sha256` | string/null | SHA-256 checksum for the shape sidecar when file-backed; null only for in-memory tests that cannot compute a checksum. |
| `shape_id` | string | Sidecar shape identifier. |
| `mass_kg` | number | Active mass copied from the validated shape sidecar and checked against the block mass. |
| `principal_dimensions_m` | array[3] | Active box principal dimensions used for support selection. |
| `orientation_initialization_mode` | string | Initially `identity`. |
| `orientation_representation` | string | `quaternion_wxyz`. |
| `inertia_model` | string | `analytic_box_principal_moments`. |
| `principal_moments_kg_m2` | array[3] | Principal moments used by the active scaffold. |
| `support_selection_policy` | string | `single_support_point_from_terrain_normal_positive_zero_tiebreak`. |
| `support_corner_tie_break` | string | `zero_components_choose_positive_sign`; near-zero signs are not snapped. |
| `contact_gap_tolerance_m` | number | `1.0e-9` unless a future reviewed slice changes it. |
| `multi_contact` | bool | `false`. |
| `new_tuned_parameters` | bool | `false`. |
| `defaults_changed` | bool | `false`. |
| `projection_correction_enabled` | bool | `false` for the first runtime wiring slice. |
| `persistent_contact_enabled` | bool | `false` for the first runtime wiring slice. |
| `orientation_evolution_enabled` | bool | `false` until reviewed separately. |
| `runtime_diagnostic_schema_version` | string | `shape_contact_runtime_diagnostic_v1`. |
| `experimental_status` | string | `pre_runtime` until integrator wiring, then `research_diagnostic` for opt-in runs only. |
| `warnings` | list[string] | Must state opt-in, uncalibrated, non-operational, not RAMMS-equivalent, and not benchmark-validated unless a later report proves otherwise. |
| `limitations` | list[string] | Must list missing projection, persistent contact, orientation evolution, multi-contact, and public benchmark evidence while those are absent. |

## Runtime Diagnostic Deferrals

The diagnostic contract above freezes what must be emitted before public
runtime use. It does not implement, validate, or approve the following:

- projection correction or penetration-position repair;
- persistent contact or resting-contact constraint handling;
- orientation evolution through time;
- support-corner change tracking through time, beyond nullable row fields;
- full runtime diagnostic output writers;
- public validation cases or public benchmark execution;
- shape-dependent restitution, friction, damping, terrain/material classes, or
  calibration;
- any change to `translational_v0`, `sphere_rotational_v1`, or default model
  behavior.

## No-Tuning Evaluation Plan

The first evaluation must compare frozen configurations:

- `translational_v0`;
- `sphere_rotational_v1`;
- `shape_contact_v0`;
- optional existing roughness/scarring variants only as already implemented
  no-tuning context, not as calibration candidates.

No parameter may be changed after viewing `shape_contact_v0` results. Initial
orientation must be deterministic and declared before running public
benchmarks. Random orientation sampling is deferred.

### Analytic Verification Gates

The prototype must pass analytic tests before public benchmark interpretation:

- box mass and principal-moment formulas match analytic values;
- quaternion initialization is unit length and deterministic;
- free flight conserves translational + rotational + potential energy when no
  contact occurs;
- flat-plane resting contact does not create motion or energy;
- dissipative normal/tangential contact with restitution in `[0, 1]` does not
  create positive total mechanical energy beyond a documented numerical
  tolerance;
- Coulomb cap is enforced;
- support-point selection is deterministic for fixed terrain normal and
  orientation;
- requesting `shape_contact_v0` without compatible shape metadata fails
  clearly.

### Backward-Compatibility Gates

The implementation must prove:

- `cargo run -- verify --all` remains unchanged for existing cases;
- `cargo run -- validate --all` remains unchanged for existing cases;
- passive shape-metadata inertness tests still pass;
- existing CSV/manifest readers tolerate the additive diagnostics;
- existing public benchmark reports are not relabelled as shape-contact
  evidence unless explicitly rerun with `shape_contact_v0`.

### Chant Sura Gates

Chant Sura is the primary physics-selection evidence because Tschamut remains
registration-sensitive. The prototype must be evaluated on model-selection,
extended, and held-out contact fixtures.

Hard non-regression gates:

- held-out `trajectory_shape_mean_error_m` must not exceed the current
  `sphere_rotational_v1` value by more than 5%;
- held-out `trajectory_energy_mean_relative_error` must not exceed the current
  `sphere_rotational_v1` value by more than 5%;
- model-selection and extended shape/energy metrics must remain better than
  `translational_v0`;
- rebound velocity, jump-height envelope, and impact timing must not degrade by
  more than 10% relative to the better of current `translational_v0` and
  `sphere_rotational_v1`, unless the run is explicitly classified as a failed
  feasibility result;
- segment-boundary events remain proxy diagnostics and must not be described as
  direct impact truth.

Evidence for the prototype:

- shape and energy metrics remain near or better than `sphere_rotational_v1`;
- rebound, jump-height, or timing metrics improve without hidden parameters;
- support-point and energy diagnostics explain the changes physically.

Evidence against:

- shape or energy metrics regress toward or beyond `translational_v0`;
- rebound/jump/timing worsen materially;
- energy diagnostics show contact energy creation;
- results depend mainly on arbitrary orientation choices.

### Tschamut Diagnostic Gates

Tschamut may be used only as failure-mode and non-regression evidence until
registration sensitivity is resolved. `physics_selection_allowed` remains
`false` for public Tschamut physics selection.

Required diagnostic tables:

- all-runs under/near/over counts;
- block 1, 2, and 4 grouping;
- observed-runout grouping;
- impact-count grouping;
- simulated-path-length grouping;
- lateral error and reach width;
- significant impacts per trajectory;
- reach, deposition, significant-impact, energy, and jump-height hazard-layer
  summaries when feasible.

Hard non-regression gates:

- `shape_contact_v0` must not produce a `sphere_rotational_v1`-style systematic
  over-run: over-run count must remain below 40 of 80 public Tschamut runs;
- mean signed runout error must not exceed +50 m on the all-runs Tschamut
  diagnostic set;
- 10 kJ kinetic-energy exceedance cells must remain below half of the current
  `sphere_rotational_v1` count unless independent evidence justifies the
  expansion;
- 2 m jump-height exceedance must not become broadly nonzero on the all-runs
  diagnostic set without a clear Chant Sura-supported explanation;
- high-impact early-stopping cases must be reported even if they worsen.

Evidence for the prototype:

- high-impact `translational_v0` early-stopping groups move toward observed
  runout without becoming broad over-runs;
- block-specific effects are physically interpretable from principal
  dimensions and support-point diagnostics;
- lateral spread and energy footprints stay bounded between the current
  compact baseline and over-broad rotational result.

Evidence against:

- systematic over-run replaces systematic under-run;
- energy/jump/reach footprints approach or exceed `sphere_rotational_v1`;
- improvements appear only in the registration-sensitive deposition-overlap
  class;
- block grouping does not change despite active shape diagnostics, suggesting
  terrain/material effects dominate.

### Mel de la Niva Smoke Gate

Mel de la Niva is not a calibration or physics-selection benchmark yet. The
first `shape_contact_v0` run may use it only as a non-explosion smoke gate:

- generated cases run deterministically;
- no numerical instability or runaway energy occurs;
- output manifests preserve LV03 provenance, archive checksums, match-distance
  QA fields, and no-threshold deposition-matching limitations;
- results are described as workflow/generalization smoke evidence only.

## Go / No-Go Before Coding

Proceed to implementation only if all conditions are satisfied:

- this contract is accepted as the authoritative first-slice boundary;
- no new tuned parameters are introduced;
- deterministic orientation initialization is chosen before public benchmark
  runs;
- diagnostic fields above are either implemented or explicitly mapped to an
  equivalent additive field name before coding;
- analytic verification tests are written with the implementation;
- the no-tuning evaluation report template is prepared before inspecting
  `shape_contact_v0` benchmark results.

Do not implement yet if any of these remain unresolved:

- the prototype needs damping or fitted friction/restitution to be stable;
- single-support-point contact cannot define an auditable energy update;
- initial orientation policy is chosen by looking at benchmark outcomes;
- Tschamut is treated as physics-selection evidence rather than diagnostic
  non-regression evidence;
- terrain/material calibration is mixed into the same implementation package.

## Stop / Pivot Rules

Stop `shape_contact_v0` and pivot toward terrain/material or stopping-behavior
work if:

- analytic energy gates fail without adding new damping;
- Chant Sura held-out shape or energy metrics fail the hard gates;
- Tschamut over-run gates fail in the same direction as `sphere_rotational_v1`;
- the only apparent improvement is achieved by changing global friction,
  restitution, terrain class, stopping threshold, or release assumptions;
- support-point diagnostics are not interpretable enough to explain behavior;
- Mel smoke runs show numerical instability.

If the shape prototype is stable but does not improve Chant Sura or Tschamut
diagnostics, the next scientific slice should be a terrain/material and
stopping-behavior protocol, not a broader polyhedral solver.

## Explicit Deferrals

Deferred from the first slice:

- multi-contact complementarity;
- face/edge contact patches;
- full convex hull or mesh contact;
- shape-specific restitution or friction;
- calibrated terrain/material classes;
- new damping or stopping parameters;
- randomized orientation ensembles;
- fragmentation;
- vegetation, forest, barriers, and protection structures;
- operational hazard products;
- RAMMS equivalence claims;
- default-model changes;
- regional tiling or GIS product expansion.

## Recommended First Coding Slice

The first scaffold slice should remain limited to:

1. parse `shape_contact_v0` as an opt-in model that requires compatible
   `shape_metadata_v1`;
2. implement analytic `principal_dimensions_box_v0` mass/inertia and support
   selection in isolation;
3. initialize and validate deterministic quaternion orientation for the opt-in
   model path;
4. add isolated contact impulse scaffolding with energy accounting;
5. route impulse preparation through the validated scaffold so support point,
   mass, and inertia remain coupled;
6. add a test-only single-contact state-transition wrapper for controlled
   verification before fixed-step integrator wiring;
7. add analytic verification and backward-compatibility tests before running
   public benchmarks.

Public benchmark execution should come only after those verification and
compatibility gates pass.

## Pre-Dry-Run Guardrails

Before any integrator-adjacent dry run, crate-internal shape-contact code must
use the scaffold-owned preparation path as the normal route. Public APIs must
not expose an ungated impulse application path. The raw low-level impulse kernel
is crate-internal analytic/test support so callers cannot mix support geometry,
mass, and inertia from unrelated sources.

The support-corner tie-break policy is frozen for the scaffold: the selected
corner is based on the sign of the body-frame support direction, and exact zero
components choose the positive corner sign. Near-zero values are not snapped by
tolerance; their raw sign is used. This policy makes tests reproducible and is
not a physically validated face-contact model.

`shape_contact_v0` remains blocked from fixed-step simulation, public validation,
and benchmark execution until a later explicitly reviewed wiring slice.

## Internal Contact-Preparation Layer

The first contact-adjacent adapter is an internal preparation layer. It accepts a
validated `ShapeContactV0Scaffold`, pre-contact body state, explicit terrain
contact point, terrain normal, and existing restitution/friction settings. It
owns scaffold support selection, support signed-gap computation relative to the
supplied contact plane, contact-regime classification, contact-point velocity
diagnostics, and, when the support point is touching or penetrating the contact
plane, one scaffold-owned impulse update. The test-only dry-run wrapper calls
this same preparation layer. It does not advance a trajectory, write validation
outputs, enable public benchmark cases, or change existing model behavior.

A test-only mini fixed-step harness may advance one synthetic ballistic
prediction against analytic terrain, query height and normal at the predicted
position, construct the explicit contact point, and then call the same internal
preparation layer. This is not a public runtime path and is not validation
evidence. Persistent contact, projection/correction, orientation evolution,
runtime diagnostic output, and benchmark execution remain deferred.

A test-only synthetic harness may query a simple analytic terrain for height and
normal, construct the explicit terrain contact point, and then call the same
preparation layer. This harness is integrator-adjacent only because it exercises
terrain-query context; it still does not step a trajectory or enable public
runtime execution.

Contact-gap semantics are:

- `separated_moving_away`: support signed gap is positive and contact-point
  normal velocity is nonnegative; no impulse is applied.
- `separated_moving_toward`: support signed gap is positive and contact-point
  normal velocity is negative; no impulse is applied because contact has not
  occurred yet.
- `touching`: support signed gap is within the fixed contact-gap tolerance of
  `1.0e-9 m`; the scaffold-owned impulse path may apply an impulse only if
  contact-point normal velocity is incoming.
- `penetrating`: support signed gap is negative beyond tolerance; the
  scaffold-owned impulse path may apply an impulse only if contact-point normal
  velocity is incoming.

The contact-gap tolerance is a deterministic pre-runtime scaffold convention,
not a calibrated contact parameter.

The preparation-layer diagnostics remain incomplete for public runtime use; full
orientation evolution, support-corner changes through time, projection energy,
and manifest/runtime diagnostic rows are still deferred.
