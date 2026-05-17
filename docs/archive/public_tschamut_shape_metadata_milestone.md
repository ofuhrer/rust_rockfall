# Public Tschamut Shape-Metadata Milestone

Status: scientific milestone report. This document summarizes current evidence
after the registered public Tschamut benchmark and passive Tschamut shape
metadata work. It does not implement code, tune parameters, change defaults, or
claim operational validity.

## What Has Been Achieved

- The public Tschamut workflow now runs end to end from public EnviDat
  observations and a public swissALTI3D 2 m terrain crop.
- `scan_surface_fit_v1` replaced the first-pass bounding-box registration and
  reduced terrain-scan registration residuals enough that registration is no
  longer the dominant explanation for the benchmark mismatch.
- Ten-run and 25-run public subsets have been run with no parameter tuning.
- `translational_v0` and `sphere_rotational_v1` have been compared against the
  same registered public terrain and observations.
- The passive shape scaffold is implemented and can carry shape, dimensions,
  mass-property diagnostics, orientation metadata, and provenance into
  manifests and trajectory metadata.
- Three public Tschamut per-block sidecars now record block mass, equivalent
  radius, and measured principal dimensions from the public overview table:
  blocks 1, 2, and 4.
- A local single-block inertness check confirmed that adding the block-1
  passive sidecar leaves reported runout/deposition metrics unchanged; the
  only intended differences are additive metadata and passive-shape warnings.

## What The Benchmark Currently Says

The registered public benchmark gives a stable no-tuning result:

| Subset | `translational_v0` result | `sphere_rotational_v1` result |
| --- | --- | --- |
| 10 runs | under-runs by about 30 m mean runout error | over-runs by about 98 m |
| 25 runs | under-runs by about 30 m mean runout error | over-runs by about 103 m |

The 25-run subset also shows block-dependent baseline under-run: strongest for
block 1, intermediate for block 2, and weakest for block 4. The rotational
over-run appears across all represented block IDs. This strengthens the
conclusion that the current spherical modes do not yet provide a robust
deposition/runout model for public Tschamut without tuning.

The result does not justify changing defaults. It also does not prove that one
missing mechanism dominates. Shape, terrain/material classes, roughness/contact
parameterization, release uncertainty, vegetation/context, and observation
limitations remain coupled.

## What Passive Shape Metadata Adds

Passive sidecars add traceability, not physics. They make the public Tschamut
block records explicit in machine-readable form:

- block 1: 69 kg, equivalent radius 0.176667 m, dimensions 0.37/0.32/0.37 m;
- block 2: 79 kg, equivalent radius 0.198333 m, dimensions 0.50/0.30/0.39 m;
- block 4: 40 kg, equivalent radius 0.160000 m, dimensions 0.46/0.30/0.20 m.

This enables:

- manifest-level provenance for block dimensions and mass;
- trajectory-metadata grouping by block ID, mass, radius, and dimensions;
- no-tuning inertness checks proving the scaffold does not alter dynamics;
- future shape-contact design to start from audited public shape records.

Mixed-block benchmark packages must not receive one sidecar. The preparation
workflow only attaches `block_shape.metadata_path` to single-block selections.

## Why This Is Not Shape-Aware Physics

The active simulator still uses the current spherical contact geometry and
current active spherical inertia. `shape_metadata_v1` records passive
diagnostics only. It does not change:

- terrain clearance or contact point selection;
- restitution, friction, rolling resistance, roughness, or scarring;
- rotational dynamics used by existing contact models;
- trajectory integration or stopping logic;
- validation pass/fail semantics.

Therefore, passive shape metadata cannot improve the Tschamut under-run or
rotational over-run by itself. Its scientific role is to make the next
shape-contact experiment auditable.

## Scientifically Unresolved

- Whether the Tschamut mismatch is dominated by equivalent-sphere limitations,
  terrain/material parameterization, missing environment context, or a
  combination of these.
- Whether block-dependent runout differences persist across all public usable
  runs after outlier review.
- Whether `sphere_rotational_v1` improves trajectory/contact realism while
  degrading field deposition/runout because shape-dependent energy partitioning
  is missing.
- Which validation metrics should control future no-tuning comparisons:
  aggregate runout, lateral spread, deposition overlap, energy/jump layers,
  impact counts, or grouped block-level errors.
- How to prevent terrain/material calibration from compensating for missing
  shape physics.

## Next Fork Ranking

| Option | Scientific value | Risk | Rank | Rationale |
| --- | --- | --- | ---: | --- |
| D. Improve validation metric grouping | High | Low | 1 | The project already has block sidecars and 25-run block coverage. Grouped metrics by block ID, mass, shape dimensions, runout quantiles, lateral spread, impact counts, and energy/jump layers are the safest next evidence layer before adding new physics or calibration. |
| A. Shape-contact design | Very high | Medium-high | 2 | Shape is the largest explicit physics gap exposed by the current benchmark, but contact design should follow stronger metric grouping so the next model is evaluated by predefined criteria. |
| C. Expand all 80 public Tschamut runs | Medium-high | Medium | 3 | More runs would improve coverage and outlier detection, especially for block-level trends, but it may mostly scale the same conclusion unless paired with grouping and QA. |
| B. Terrain/material calibration protocol | High | High | 4 | Calibration is necessary eventually, but starting too early risks tuning terrain/contact parameters to absorb missing shape physics. It should wait for grouped validation criteria and a held-out design. |

## Recommendation

Immediate next step: **improve validation metric grouping** for the registered
public Tschamut workflow using the new passive block metadata. This should be a
no-tuning analysis/reporting step that groups existing and newly generated
metrics by block ID, mass, equivalent radius, principal dimensions, contact
model, and subset.

Medium-term scientific step: **shape-contact design**, beginning with a
design-only decision record and verification criteria. It should explicitly
state which active physics would change and how it will be tested without
tuning.

Deferred alternative: **terrain/material calibration protocol**. It should be
designed soon, but actual calibration should wait until grouped metrics,
held-out splits, and shape-vs-material identifiability assumptions are explicit.

The milestone conclusion is: the project has moved from a proxy Tschamut case
to a registered public-data benchmark with passive public block-shape
provenance, but the scientific bottleneck is now interpretation and model
structure, not data plumbing.
