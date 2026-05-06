# `shape_contact_v0` Runtime Wiring Plan

This document defines the smallest safe future slice for wiring
`shape_contact_v0` into the fixed-step integrator. It is primarily a design
plan. The repository also contains a compiled internal integrator-smoke
scaffold, covered by tests, that exercises one synthetic ballistic-to-contact
step through an integrator-owned fixed-step prediction and diagnostic mapping
without enabling public simulation, validation, benchmarks, or any new physics
behavior.

The implementation must remain opt-in and experimental. Existing
`translational_v0` and `sphere_rotational_v1` behavior, defaults, verification
cases, and validation baselines must remain unchanged.

## Proposed Architecture

The first runtime slice should route every `shape_contact_v0` contact through
the existing scaffold-owned preparation boundary:

1. `SimulationConfig::validate`
   - continue to reject `shape_contact_v0` for normal public runs until the
     diagnostic writer and manifest fields are implemented and tested;
   - later allow only an explicitly named internal/runtime-smoke mode, not
     public validation cases.
2. `simulate_one_trajectory_with_terrain_and_contact_parameters`
   - create the validated `ShapeContactV0Scaffold` once from the already
     validated `shape_metadata_v1` sidecar;
   - pass a mutable diagnostic sink through the trajectory loop only for
     `shape_contact_v0`.
3. `integrate_fixed_step`
   - replace the current `shape_contact_v0_integrator_guard()` only inside the
     opt-in runtime-smoke path;
   - after the ballistic prediction and terrain query, construct:
     - `ShapeContactV0ContactInput`;
     - terrain contact point;
     - terrain normal;
     - current `BodyState`;
     - existing restitution/friction/gravity settings.
4. `shape_contact_v0_prepare_contact`
   - remains the only runtime-facing contact path;
   - owns support selection, support-gap calculation, contact-regime
     classification, impulse eligibility, and impulse application.
5. Diagnostic mapper/writer
   - maps each returned contact result to `shape_contact_runtime_diagnostic_v1`;
   - writes rows to an internal sink before any public runtime output is
     enabled.

No future integrator code should call the low-level impulse kernel directly.

## Files Likely Touched

- `src/integrator.rs`
  - replace the `shape_contact_v0` guard only behind an internal runtime-smoke
    gate;
  - call `shape_contact_v0_prepare_contact`;
  - preserve existing contact-model branches exactly.
- `src/simulation.rs`
  - carry an optional scaffold and diagnostic sink into the integrator;
  - keep default validation rejecting public `shape_contact_v0` runs.
- `src/shape.rs`
  - keep runtime row, writer, sidecar, and smoke-harness shapes internal rather
    than public API;
  - keep field names and enum labels identical to
    `shape_contact_runtime_diagnostic_v1`.
- `src/manifest.rs`
  - add additive `shape_contact_v0` manifest fields only after the writer
    contract is satisfied.
- `src/validation.rs`
  - continue to reject public validation cases until runtime diagnostics and
    manifest fields are available and reviewed.
- `tests/config_io_terrain.rs`, `tests/physics.rs`, or `src/shape.rs` tests
  - add internal smoke tests and backward-compatibility gates.
- `docs/model_design.md`, `docs/validation_data_schema.md`,
  `docs/shape_contact_v0_experimental_contract.md`
  - update only to reflect implemented runtime-smoke status.

## Runtime Guards

The first implementation must keep these guards:

- public validation cases with `contact_model: shape_contact_v0` fail unless a
  later reviewed slice explicitly permits a named internal smoke fixture;
- public benchmark workflows cannot select `shape_contact_v0`;
- missing or incompatible shape metadata fails before any trajectory step;
- `translational_v0` and `sphere_rotational_v1` branches remain byte-for-byte
  equivalent except for unavoidable formatting;
- no new restitution, friction, damping, calibration, terrain/material, or
  orientation parameters are introduced;
- projection correction, persistent contact, multi-contact, and orientation
  evolution remain disabled and reported as such.

## Diagnostics And Writer Plan

Before the first runtime trajectory can complete, the implementation must emit
or collect `shape_contact_runtime_diagnostic_v1` rows with the frozen contract
from `shape_contact_v0_experimental_contract.md`.

The first writer should be internal and sidecar-oriented:

- collect rows in deterministic step order;
- serialize JSON Lines using exact frozen field names;
- use fixed snake_case enum labels;
- keep `projection_energy_delta_j: null` and `projection_applied: false`;
- keep `support_corner_changed: null` until previous-corner tracking is
  implemented;
- include `shape_contact_row_id` as
  `{trajectory_id}:shape_contact:{step_index}`;
- optionally attach `contact_event_id` / `impact_index` only when aligned with
  existing impact-event output.

The first runtime slice should prefer a dedicated diagnostic sidecar over
overloading existing impact-event rows. Impact-event attachment can come later
once row timing and event alignment are stable.

## Manifest Requirements

No public `shape_contact_v0` run may be allowed until the run manifest contains
an additive `shape_contact_v0` object with:

- `active_contact_model: shape_contact_v0`;
- `active_shape_type: principal_dimensions_box_v0`;
- `shape_metadata_path`;
- `shape_metadata_sha256`;
- `shape_id`;
- `mass_kg`;
- `principal_dimensions_m`;
- `orientation_initialization_mode: identity`;
- `orientation_representation: quaternion_wxyz`;
- `inertia_model: analytic_box_principal_moments`;
- `principal_moments_kg_m2`;
- `support_selection_policy`;
- `support_corner_tie_break`;
- `contact_gap_tolerance_m`;
- `multi_contact: false`;
- `new_tuned_parameters: false`;
- `defaults_changed: false`;
- `projection_correction_enabled: false`;
- `persistent_contact_enabled: false`;
- `orientation_evolution_enabled: false`;
- `runtime_diagnostic_schema_version: shape_contact_runtime_diagnostic_v1`;
- `experimental_status`;
- warnings and limitations.

The manifest must state that the run is research-diagnostic, opt-in,
uncalibrated, non-operational, and not benchmark-validated unless a later
report explicitly changes that status.

## Backward Compatibility Checks

The runtime wiring slice must prove:

- existing verification cases produce unchanged metrics for all non-shape
  contact models;
- existing validation cases produce unchanged metrics for all non-shape contact
  models;
- existing trajectory, impact-event, hazard-layer, and manifest output formats
  are unchanged unless a case explicitly opts into `shape_contact_v0`
  diagnostics;
- passive shape metadata remains passive for existing models;
- normal validation loading still rejects `shape_contact_v0` public cases until
  the runtime-smoke gate is explicitly reviewed.

## Analytic Tests Required Before First Runtime Execution

The first runtime wiring PR must include focused tests for:

- a single flat-plane touching incoming contact routed through the integrator
  path;
- a separated state that remains non-impulsive;
- a penetrating but moving-away state that maps to
  `non_impulsive_penetrating`;
- an inclined terrain normal passed unchanged into the preparation layer;
- no positive total mechanical energy creation for dissipative contacts within
  tolerance;
- exact JSON Lines diagnostic row serialization from runtime-collected rows;
- manifest `shape_contact_v0` fields and checksum provenance;
- public validation rejection for ordinary `shape_contact_v0` cases;
- backward compatibility for `translational_v0` and `sphere_rotational_v1`.

These tests should be synthetic and checked-in. They must not use public
benchmarks.

## Stop Conditions

Stop the runtime wiring slice and do not proceed to public benchmark execution
if any of the following occur:

- a non-shape model changes numerical output;
- `shape_contact_v0` can run without compatible shape metadata;
- the integrator can bypass `shape_contact_v0_prepare_contact`;
- diagnostic rows are missing required fields, use unstable labels, or omit
  projection-disabled fields;
- dissipative contact creates positive mechanical energy beyond documented
  tolerance;
- separated states receive impulses;
- penetrating non-incoming states are silently projected or impulsed;
- manifest fields cannot prove opt-in experimental status and active shape
  provenance.

## Risks

- The current single-support-point policy can create brittle behavior on flat or
  near-flat contacts.
- No projection correction means penetrating states can remain geometrically
  inconsistent after an otherwise valid impulse decision.
- No persistent-contact handling means repeated touching states may generate
  noisy diagnostics.
- Identity-only orientation avoids one class of ambiguity but does not test
  realistic tumbling.
- Early runtime success would be a verification result, not public validation
  evidence.

## Recommended First Implementation Slice

Implement an internal runtime-smoke mode that runs one synthetic trajectory step
through the real fixed-step terrain query and `shape_contact_v0_prepare_contact`,
collects `shape_contact_runtime_diagnostic_v1` rows into an in-memory or
temporary test sink, and verifies the manifest object.

This slice should still reject all public validation and benchmark use. Public
benchmark execution should wait until the runtime-smoke path, diagnostic sidecar,
manifest provenance, and backward-compatibility gates have passed review.

## Current Internal Smoke Scaffold

The first internal smoke scaffold is module-internal and exercised by focused
tests. It:

- requires `contact_model = shape_contact_v0`;
- builds a `ShapeContactV0Scaffold` from compatible `shape_metadata_v1`,
  including a file-backed smoke test that records metadata path and SHA-256;
- advances one synthetic ballistic step through an integrator-owned helper that
  uses the same fixed-step ballistic prediction and terrain-query convention;
- queries analytic terrain height and normal at the predicted position through
  that helper;
- calls `shape_contact_v0_prepare_contact`;
- maps one row to `shape_contact_runtime_diagnostic_v1`;
- collects the row in memory and serializes JSON Lines in tests;
- builds an internal diagnostic-sidecar manifest fixture with sidecar kind,
  schema version, row count, optional path, and deterministic in-memory hash;
- builds a manifest-shaped `shape_contact_v0` object with projection,
  persistent-contact, orientation-evolution, multi-contact, tuned-parameter, and
  default-change flags all disabled.

This scaffold is not reachable from normal CLI validation, verification, or
benchmark flows and is not validation evidence. It does not write files, create
validation cases, run public benchmarks, or permit ordinary
`shape_contact_v0` simulation.

The sidecar scaffold is preferred over overloading impact-event output because
shape-contact rows include support geometry, contact-regime labels, projection
status, and active shape provenance that are not part of the existing
spherical-impact event contract.
