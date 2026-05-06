# Post-RAMMS Gap Next Work Packages

Status: staged planning document. This roadmap translates
`ramms_gap_analysis.md` into executable no-tuning work packages. It does not
implement code, change defaults, tune parameters, add physics, optimize
performance, or claim operational hazard validity.

## Purpose

The RAMMS gap analysis identifies four high-value directions:

1. grouped public Tschamut validation;
2. active shape/contact design;
3. terrain/material calibration protocol;
4. GIS-ready hazard products.

The local project should not copy RAMMS internals or product philosophy. The
next phase should close the most consequential public gaps in an open,
testable order, with go/no-go criteria that prevent calibration or new physics
from masking known failure modes.

## Sequencing Logic

The current public Tschamut evidence is strong enough to show a structural
problem, but not yet strong enough to identify one mechanism:

- `translational_v0` under-runs public Tschamut by about 30 m.
- `sphere_rotational_v1` over-runs strongly.
- Passive shape metadata is available for blocks 1, 2, and 4.
- Grouped analysis suggests shape/contact and terrain/material effects remain
  confounded.

Therefore, the next sequence is:

1. make the failure modes harder to misread;
2. design active shape/contact before implementing it;
3. choose between minimal active shape/contact and terrain/material calibration
   based on predefined evidence;
4. add GIS-ready products once the scientific map semantics are stable enough
   to export.

## Work Package 1: All-Usable Public Tschamut Grouped Validation

### Purpose

Expand the registered public Tschamut benchmark from the 10-run and 25-run
subsets to all usable public runs, with stronger grouping and outlier QA. This
is the evidence-control step before new contact physics or calibration.

### Inputs

- Public EnviDat Tschamut LPS trajectories and overview tables.
- Public Tschamut slope scan and `scan_surface_fit_v1` registration workflow.
- Public swissALTI3D 2 m terrain crop workflow.
- Passive Tschamut block sidecars for blocks 1, 2, and 4.
- Existing no-tuning model set:
  - `translational_v0`;
  - `sphere_rotational_v1`;
  - optional predefined roughness/scarring variants only if parameters are
    frozen before execution.

### Outputs

- Updated public Tschamut benchmark report or companion grouped-analysis
  report.
- Per-run and grouped metrics by:
  - block ID;
  - mass and equivalent radius;
  - principal-dimension class where available;
  - observed-runout quantile;
  - impact-count class;
  - trajectory-length class;
  - contact model;
  - valid/invalid observation status.
- QA table for excluded runs with explicit exclusion reasons.
- No-tuning comparison matrix and fixed success metrics for later work
  packages.

### Strict Constraints

- Do not tune restitution, friction, roughness, scarring, terrain classes, or
  release parameters.
- Do not change defaults.
- Do not introduce shape-dependent contact.
- Do not treat passive shape metadata as active dynamics.
- Do not claim operational validity.
- Keep raw/public downloads and generated outputs ignored unless they are
  intentionally tiny processed fixtures.

### Expected Scientific Value

High. This work reduces the risk of adding a new physics model that improves
one aggregate metric while worsening block-level, lateral-spread, energy, or
deposition behaviour.

### Risks

- More runs may expose data-cleaning and registration edge cases.
- Block ID, runout length, release location, and terrain path may remain
  confounded.
- Impact counts are sensitive to diagnostic thresholds and contact chatter.

### Required Tests And Checks

- Existing Rust and Python tests remain unchanged unless a reporting parser is
  modified.
- Preparation script tests, if updated, must cover run filters, block filters,
  selected-run manifest fields, and exclusion reporting.
- Required commands:

```bash
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
```

If scripts or validation parsers change, also run:

```bash
cargo test
python3 -m unittest tests/test_hazard_layers.py tests/test_performance_benchmark.py
cargo run -- validate --all
```

### Go Criteria

- At least 80% of public shared LPS/overview runs are either included or
  explicitly excluded with reproducible QA reasons.
- The same output tables can be regenerated from public inputs and documented
  commands.
- Model comparison metrics are grouped enough to define what a future shape or
  calibration step must improve and must not degrade.
- The 10-run and 25-run conclusions are either confirmed or clearly revised.

### No-Go Criteria

- Coordinate registration uncertainty dominates runout/deposition error for a
  large fraction of runs.
- Too many runs require manual classification that is not reproducible.
- Grouped metrics cannot separate block, path, and observation-quality effects
  well enough to evaluate new physics.

### Deferred

- Active shape/contact implementation.
- Terrain/material parameter calibration.
- GeoTIFF/COG export.
- Annual probability or risk outputs.

## Work Package 2: Active Shape-Contact Design Only

### Purpose

Define an independent, literature-based active shape/contact model design before
any implementation. This is a design gate, not a coding step.

### Inputs

- `ramms_gap_analysis.md`.
- `public_tschamut_failure_mode_analysis.md`.
- `public_tschamut_shape_metadata_milestone.md`.
- `shape_aware_block_scaffold_design.md`.
- Chant Sura contact-validation and held-out generalization reports.
- Public shape/contact literature already listed in `literature_review.md`.

### Outputs

- Design document for a minimal active shape-contact model.
- Explicit list of state variables:
  - orientation;
  - angular velocity;
  - active inertia model;
  - support/contact geometry;
  - contact-point selection;
  - energy accounting;
  - diagnostics.
- Verification plan for rigid-body invariants and simple contact cases.
- No-tuning validation matrix using Chant Sura and public Tschamut grouped
  metrics.
- Versioning decision for the eventual implementation, likely a minor version
  because it would be opt-in physics.

### Strict Constraints

- Do not implement active shape contact in this work package.
- Do not reverse engineer proprietary models.
- Do not copy undocumented RAMMS internals.
- Do not change default `translational_v0`.
- Do not use Tschamut results to tune design constants.
- Preserve current passive shape metadata semantics.

### Expected Scientific Value

Very high. Shape/contact is the largest public capability gap against mature
state-of-practice rockfall tools and the clearest structural limitation exposed
by Tschamut plus Chant Sura.

### Risks

- A too-large design could become an unreviewable physics rewrite.
- A too-small design may not address the observed under-run/over-run
  structure.
- Non-spherical contact can introduce numerical instability and energy
  accounting errors.

### Required Tests And Checks

Design-only work requires:

```bash
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
```

The design must specify future tests before any implementation:

- mass/inertia property tests;
- orientation integration tests;
- energy conservation/dissipation tests;
- contact impulse sign and friction-limit tests;
- deterministic fixed-seed tests;
- passive-shape backward-compatibility tests;
- no-tuning Chant Sura/Tschamut comparison tests.

### Go Criteria

- The design identifies one minimal opt-in implementation slice that can be
  tested independently of calibration.
- The design specifies exact success and non-regression criteria from WP1.
- The design keeps current spherical modes intact and backward compatible.
- Energy and momentum accounting are explicit enough to write tests before
  implementation.

### No-Go Criteria

- The design requires parameter tuning to demonstrate value.
- The design cannot be verified with analytic or synthetic fixtures.
- The design depends on proprietary implementation details.
- The design changes defaults or validation semantics.

### Deferred

- Full polyhedral production contact.
- Terrain/material calibration.
- Protection structures, forest, fragmentation, and GUI work.

## Work Package 3: Conditional Branch

WP3 depends on WP1 and WP2. It should not be chosen before those gates are
resolved.

### Branch 3A: Minimal Active Shape-Contact Prototype

#### Purpose

Implement the smallest opt-in active shape/contact slice that the WP2 design
proves testable and that WP1 metrics can evaluate without tuning.

#### Inputs

- WP1 grouped metrics and go/no-go decision.
- WP2 active shape/contact design.
- Passive `shape_metadata_v1` sidecars.
- Existing Chant Sura and public Tschamut validation cases.

#### Outputs

- New opt-in contact model or shape-dynamics mode.
- Focused analytic/synthetic verification tests.
- No-tuning Chant Sura/Tschamut comparison report.
- Manifest and trajectory-metadata updates that clearly label active shape
  physics.

#### Strict Constraints

- Keep existing defaults unchanged.
- Do not tune to Tschamut.
- Do not silently reinterpret existing `block.radius` semantics.
- Do not remove or weaken current spherical models.

#### Go Criteria

- WP1 confirms grouped metrics are stable enough to judge shape effects.
- WP2 identifies a minimal model that can be verified before field comparison.
- The prototype can be added opt-in without output-breaking changes.

#### No-Go Criteria

- WP1 shows terrain/material grouping dominates the mismatch more clearly than
  block-shape grouping.
- WP2 cannot define a small verifiable implementation.
- The prototype requires a broad solver rewrite before any testable slice
  exists.

### Branch 3B: Terrain/Material Calibration Protocol

#### Purpose

Design the calibration protocol for terrain/material parameters before any
parameter fitting. This branch is preferred if WP1 shows terrain/path grouping
dominates block-shape grouping.

#### Inputs

- WP1 grouped public Tschamut metrics.
- Terrain-class metadata infrastructure.
- Chant Sura trajectory/contact validation.
- Lu/scarring impact-level calibration workflow.
- Existing roughness/scarring parameter docs.

#### Outputs

- Calibration protocol document with training/held-out splits.
- Parameter identifiability table.
- Fixed objective functions:
  - runout/deposition;
  - lateral spread;
  - energy/jump layers;
  - impact diagnostics;
  - contact-event metrics where available.
- Rules preventing calibration from masking missing shape physics.

#### Strict Constraints

- Design protocol only unless explicitly approved later.
- Do not fit parameters in this work package.
- Do not use validation sets as calibration targets.
- Do not change defaults or claim field validity.

#### Go Criteria

- WP1 shows terrain/path or material grouping is the dominant explanatory
  signal.
- A clean training/held-out split exists.
- Objectives and constraints are fixed before any calibration run.

#### No-Go Criteria

- Shape/contact grouping remains too confounded to calibrate terrain safely.
- Available terrain/material labels are too weak or provenance-poor.
- The protocol would require tuning directly against the public benchmark
  target without held-out controls.

### Recommendation For WP3

Default branch: **3A minimal active shape-contact prototype**, but only after
WP1 and WP2 pass their go criteria.

Fallback branch: **3B terrain/material calibration protocol** if WP1 shows
terrain/path dependence is stronger than block/shape dependence or if WP2
cannot define a small safe implementation slice.

## Work Package 4: GIS-Ready GeoTIFF/COG Export

### Purpose

Make hazard outputs easier to inspect in standard GIS workflows once map
semantics and validation metrics are stable.

### Inputs

- Existing hazard layers and manifest metadata.
- Explicit-grid benchmark/pilot support.
- swissALTI3D terrain metadata with CRS, vertical datum, extent, resolution,
  nodata, source, license, and checksum.
- Sampling-weighted conditional hazard-layer semantics.

### Outputs

- Opt-in GeoTIFF export for core hazard rasters.
- CRS/provenance-carrying raster metadata.
- Optional COG conversion path if it can be added without heavy runtime
  coupling.
- Raster parity tests against existing CSV/ASCII outputs.
- GIS QA recipe for public Tschamut and private Swiss pilot outputs.

### Strict Constraints

- Preserve CSV/ASCII debug outputs.
- Do not change hazard numerical semantics.
- Do not introduce operational validity claims.
- Do not conflate hazard maps with risk maps.
- Avoid heavy dependencies unless the implementation decision justifies them.

### Expected Scientific And Engineering Value

High engineering value, medium scientific value. GIS-ready outputs do not solve
the Tschamut physics mismatch, but they are necessary for credible Swiss pilot
review and visual QA.

### Risks

- Dependency creep.
- CRS metadata errors becoming harder to spot than plain ASCII fixtures.
- Premature productization before scientific semantics stabilize.

### Required Tests And Checks

- Raster parity tests against existing CSV/ASCII layers.
- CRS/provenance metadata tests.
- Explicit-grid extent and nodata tests.
- Backward-compatibility tests for existing hazard outputs.

Required command chain after implementation:

```bash
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
cargo test
python3 -m unittest tests/test_hazard_layers.py tests/test_performance_benchmark.py
cargo run -- validate --all
```

### Go Criteria

- WP1 has stable map metrics and grid conventions.
- Export can be implemented opt-in without changing existing hazard outputs.
- CRS/provenance fields are already available from manifests.

### No-Go Criteria

- Export requires changing hazard semantics.
- Dependency cost is disproportionate to pilot needs.
- Existing ASCII/CSV outputs are still sufficient for the next scientific
  comparison.

### Deferred

- Full national tiling.
- Cloud object storage.
- Web GIS services.
- Exposure/vulnerability/risk layers.

## Cross-Package Decision Gates

Before any physics implementation:

- WP1 grouped metrics define what must improve and what must not degrade.
- WP2 design defines verifiable equations and failure modes.
- Defaults remain unchanged.
- No parameter tuning is introduced.

Before any calibration:

- Training and held-out validation splits are fixed.
- Parameter bounds and objectives are documented.
- Calibration cannot use public benchmark conclusions retroactively.

Before any product/GIS expansion:

- Hazard-layer semantics are clear.
- CRS/provenance are manifest-backed.
- Existing debug outputs remain available.

## Immediate Recommendation

Start with **Work Package 1: all-usable public Tschamut grouped validation**.

This is the lowest-risk, highest-leverage next step because it makes future
shape/contact or terrain/material decisions harder to overfit. It also directly
addresses the RAMMS gap-analysis recommendation to improve validation evidence
before adding more physics or product features.

## Deferred For Now

- Changing the default contact model.
- Implementing active shape contact before WP1/WP2 gates pass.
- Calibrating terrain/material parameters before a held-out protocol exists.
- GeoTIFF/COG export before map semantics and grids are stable enough.
- Further low-level performance optimization.
- Forest, barrier, fragmentation, or risk/exposure modules.
- Any claim of operational hazard-map readiness.
