# Shape-Aware Block Scaffold Design

Status: design-only implementation plan. This document does not change
simulation physics, defaults, validation semantics, or calibration policy.

## Purpose

The registered public Tschamut benchmark and Chant Sura contact-validation
results now point to a structural limitation in the current equivalent-sphere
model:

- public Tschamut 10-run and 25-run subsets show `translational_v0` under-runs
  by about 30 m, while `sphere_rotational_v1` over-runs strongly;
- Chant Sura supports `sphere_rotational_v1` for trajectory-shape and
  kinetic-energy diagnostics, but not for all rebound, jump-height, or timing
  metrics;
- no tuning has been performed, and registration is no longer the dominant
  explanation for the public Tschamut mismatch.

The next safe scientific step is not full polyhedral contact. It is a minimal
opt-in scaffold that carries block shape, orientation, and inertia metadata
through validation and reporting while preserving the current spherical contact
laws. This gives future shape-dependent contact work a tested, auditable state
and provenance contract.

## Current Implementation Boundary

Current runtime assumptions:

- `SimulationConfig.block` is a `SphereBlock` with `radius_m` and `mass_kg`.
- `BodyState` carries position, velocity, and angular velocity, but no
  orientation.
- Contact geometry uses the sphere radius for terrain clearance and impact
  response.
- Rotational energy uses the solid-sphere moment of inertia.
- Validation YAML exposes `block.mass` and `block.radius`.
- `trajectory_metadata_table_v1` already records `shape_class = "sphere"`,
  `block_radius_m`, `block_mass_kg`, `scenario_id`, and `sampling_weight`.

The scaffold must not silently reinterpret any of those fields. Until a future
version introduces an explicit shape-dependent contact model, `block.radius`
remains the active contact radius and the current sphere inertia remains the
active rotational inertia used by existing dynamics.

## Scaffold Scope

In scope for the first implementation slice:

- optional shape metadata parsing;
- analytic mass-property calculations for simple shapes;
- deterministic initial orientation metadata;
- passive orientation state or diagnostics if implemented additively;
- manifest and trajectory-metadata provenance;
- validation fixtures proving the default sphere path is unchanged.

Out of scope:

- non-spherical contact points;
- tumbling, edge, corner, or face contact;
- shape-dependent restitution, friction, or rolling resistance;
- using shape inertia in current contact dynamics;
- calibration, tuning, or default changes;
- claims of improved predictive skill.

## Proposed Metadata Contract

Prefer a sidecar metadata file for real datasets and allow inline metadata only
for tiny fixtures. Existing cases without this block remain valid.

```yaml
block:
  mass: 69.0
  radius: 0.176667

block_shape:
  metadata_path: validation/data/example/block_shape.yaml
```

Example sidecar:

```yaml
schema_version: shape_metadata_v1
shape_id: tschamut_block_001
shape_type: principal_dimensions
shape_class: blocky

dimensions_m:
  equivalent_radius_m: 0.176667
  principal_lengths_m: [0.42, 0.31, 0.24]

mass_properties:
  mass_kg: 69.0
  density_kgpm3: 2550.0
  mass_property_model: box_principal_dimensions
  principal_moments_kg_m2: [1.39, 1.82, 2.42]
  center_of_mass_offset_m: [0.0, 0.0, 0.0]

orientation:
  representation: quaternion_wxyz
  initialization_mode: identity
  initial_quaternion_wxyz: [1.0, 0.0, 0.0, 0.0]

provenance:
  source_dataset: public_tschamut
  source_record_id: run_or_block_id
  source_url_or_doi: documented_elsewhere
  license: documented_elsewhere
  notes: "Shape metadata only; current contact remains spherical."
```

Required validation:

- `schema_version` must be `shape_metadata_v1`.
- `shape_type` must be one of the supported scaffold types.
- dimensions, mass, density, and inertia values must be finite and positive
  where present.
- `mass_properties.mass_kg` must match `block.mass` within a documented
  tolerance unless an explicit `mass_source` field says the sidecar is
  descriptive only.
- `dimensions_m.equivalent_radius_m` must match `block.radius` within a
  documented tolerance when the shape is intended to describe the active
  equivalent sphere.
- orientation quaternions must be finite and unit length within tolerance.
- raw scans or large point clouds must not be committed; use derived summaries
  and provenance records.

## Initial Shape Types

| Shape type | Required dimensions | Mass-property model | Runtime effect in scaffold |
| --- | --- | --- | --- |
| `sphere` | `radius_m` | solid sphere, `I = 2/5 m r^2` | Equivalent to current metadata. No behavior change. |
| `ellipsoid` | semi-axes `[a, b, c]` | `Ixx = 1/5 m (b^2 + c^2)`, cyclic permutations | Metadata and diagnostics only. |
| `box` | side lengths `[lx, ly, lz]` | `Ixx = 1/12 m (ly^2 + lz^2)`, cyclic permutations | Metadata and diagnostics only. |
| `principal_dimensions` | length, width, height plus chosen mass-property model | Box or ellipsoid approximation, recorded explicitly | Metadata and diagnostics only. |
| `custom_principal_moments` | principal moments and provenance | User-provided, validated positive | Metadata and diagnostics only. |

`point_cloud_summary` may be added later as a metadata-only type if public
datasets provide derived bounding boxes, principal axes, or convex-hull
summaries. Raw point clouds should remain external unless a tiny fixture is
explicitly licensed and documented.

## Orientation Representation

Use unit quaternions in `[w, x, y, z]` order. This avoids Euler-angle singularity
and is compatible with future rigid-body contact work.

Initial supported modes:

- `identity`: deterministic default for shape metadata.
- `fixed_quaternion`: use the provided unit quaternion.
- `align_long_axis_to_velocity`: future deterministic mode; acceptable only
  after a focused test defines zero-velocity behavior.

Randomized orientation sampling is deferred. When added, it must derive seeds
from the global seed, case id, and trajectory id so ensemble results are
independent of execution order.

## Manifest And Output Fields

`run_manifest_v1` should gain an optional `shape_metadata` section when a case
provides `block_shape.metadata_path`:

```json
{
  "shape_metadata": {
    "schema_version": "shape_metadata_v1",
    "shape_id": "tschamut_block_001",
    "shape_type": "principal_dimensions",
    "shape_class": "blocky",
    "metadata_path": "...",
    "active_contact_shape": "sphere",
    "active_contact_radius_m": 0.176667,
    "principal_moments_kg_m2": [1.39, 1.82, 2.42],
    "orientation_initialization_mode": "identity",
    "warnings": [
      "Shape metadata is passive; current contact physics remains spherical."
    ]
  }
}
```

`trajectory_metadata_table_v1` can be extended additively with:

- `shape_id`
- `shape_type`
- `shape_class`
- `equivalent_radius_m`
- `principal_length_m`
- `principal_width_m`
- `principal_height_m`
- `Ixx_kg_m2`, `Iyy_kg_m2`, `Izz_kg_m2`
- `initial_orientation_w`, `initial_orientation_x`, `initial_orientation_y`,
  `initial_orientation_z`

Existing consumers must continue to work when these columns are absent.

## Validation Diagnostics

Add diagnostics only after the metadata parser exists:

- shape metadata present / absent;
- active contact shape (`sphere`);
- equivalent radius consistency;
- mass consistency;
- principal-moment positivity;
- orientation norm error;
- metadata provenance path and checksum when available.

Do not use shape inertia in current rotational-energy diagnostics unless the
case explicitly opts into a future shape-aware dynamics model. Reporting both
the active sphere inertia and passive shape principal moments is acceptable if
the labels are unambiguous.

## Staged Implementation Plan

### Stage 1: Parser And Metadata Validation

- Add Rust structs for `BlockShapeMetadata`.
- Add YAML parsing through validation/case configuration.
- Support `sphere`, `ellipsoid`, `box`, `principal_dimensions`, and
  `custom_principal_moments`.
- Add analytic mass-property functions with unit tests.
- Reject invalid dimensions, non-positive inertia, invalid quaternions, and
  unsupported shape types.
- Prove cases without `block_shape` produce byte-for-byte compatible numerical
  trajectory outputs where tests can reasonably compare them.

### Stage 2: Manifest And Trajectory Metadata Propagation

- Record passive shape metadata in `run_manifest_v1`.
- Extend `trajectory_metadata_table_v1` additively.
- Add one tiny synthetic shape fixture and one public-data-derived metadata
  fixture if license-compatible.
- Keep `shape_class = "sphere"` as the default when no shape metadata exists.

### Stage 3: Passive Orientation State

- If needed for future model work, add optional orientation state to trajectory
  samples behind an opt-in output flag.
- Preserve existing trajectory CSV columns by default.
- Verify deterministic initialization and orientation normalization.
- Do not feed orientation into contact response in this stage.

### Stage 4: No-Tuning Validation Readiness

- Attach shape metadata to selected Chant Sura and public Tschamut cases.
- Group validation summaries by shape type, dimensions, and mass class.
- Confirm that adding metadata alone does not change simulated runout,
  deposition, or hazard layers.

### Stage 5: Separate Shape-Contact Design

- Only after the scaffold is validated, create a separate design for
  shape-dependent contact.
- That later design must define contact points, inertia usage, restitution and
  friction semantics, verification tests, and no-tuning comparison cases before
  any default change is considered.

## Required Tests

- Shape metadata parse success and failure cases.
- Analytic inertia tests for sphere, ellipsoid, and box.
- Positive-definite principal-moment validation.
- Unit-quaternion validation and rejection of zero or non-finite quaternions.
- Backward compatibility for cases without `block_shape`.
- Manifest inclusion when `block_shape.metadata_path` is present.
- Trajectory metadata row count and shape-field propagation.
- Deterministic orientation initialization.
- A regression test confirming current contact results are unchanged when
  passive shape metadata is supplied.

## Success Criteria

The scaffold is ready if:

- default behavior and existing validation results are unchanged;
- shape metadata is opt-in and clearly marked passive;
- mass, dimensions, inertia, and orientation are validated and provenance
  tracked;
- manifests and trajectory metadata can carry shape information;
- future shape-contact work has a tested state/schema boundary;
- documentation prevents users from interpreting the scaffold as a
  non-spherical contact model.

## Risks

- Users may assume shape metadata changes the physical trajectory. Mitigation:
  manifest warnings, docs, and field names such as `active_contact_shape`.
- Shape inertia may be accidentally mixed into current sphere dynamics.
  Mitigation: keep active inertia and passive shape moments separately labelled
  until a future model explicitly opts in.
- Tschamut and Chant Sura shape records may not use identical measurement
  definitions. Mitigation: carry provenance and source-record ids; avoid
  calibration until data roles are clear.
- A broad schema can become a hidden physics model. Mitigation: keep the first
  slice to simple analytic shapes and documented custom principal moments.

## Relation To State Of Practice

Mature 3D rockfall tools and operational workflows commonly account for block
shape, orientation, and shape-dependent energy partitioning more explicitly than
an equivalent sphere. This scaffold addresses only the representation and
provenance gap. It does not copy proprietary implementation details, does not
claim equivalence to any proprietary model, and does not yet implement full
polyhedral contact.

## Dataset Use

Chant Sura should remain the primary trajectory/contact validation dataset. The
shape scaffold can carry EOTA or block-shape summaries through trajectory
comparisons and help test whether equivalent-sphere assumptions correlate with
specific rebound or jump-height errors.

Public Tschamut should remain the deposition/runout validation dataset. Shape
metadata can be attached to its public block records so future no-tuning model
comparisons can ask whether under-run or over-run behaviour varies by block
dimensions, mass, or shape class.

Scarring calibration datasets should not be used to tune shape dynamics unless
a later document defines an impact-level shape calibration target and held-out
validation policy.

## Recommended Next Action

Implement Stage 1 and Stage 2 only:

1. add the metadata parser and analytic mass-property validation;
2. propagate passive shape metadata into manifests and trajectory metadata;
3. add backward-compatibility tests proving current physics is unchanged.

Stop before passive orientation output or shape-dependent contact unless a
separate implementation plan and tests are approved.
