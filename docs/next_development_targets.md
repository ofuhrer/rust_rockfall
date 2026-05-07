# Next Development Targets

Status: proposed development directions from the strategic review in
`docs/repository_scientific_roadmap_review.md`. These targets are planning
recommendations only and do not change simulator behavior.

## Target 1: Controlled Real-Site Tschamut/swissALTI3D Pilot With Embedded Gates

Objective: Execute the existing private/local Tschamut swissALTI3D pilot plan
with a real provenance-tracked DEM crop, explicit source-area metadata,
baseline and `sphere_rotational_v1` comparison cases, no tuning, visual QA,
and embedded performance and terrain-representation observations.

Rationale: The repository has a Swiss pilot contract but not a real-site
result. Tschamut under-run remains confounded by proxy terrain. The pilot is
primarily workflow, confounding, and feasibility evidence; it is not decisive
physics validation.

Expected value for Swiss hazard-map goal: Very high. It tests the Swiss
workflow stack, exposes whether proxy terrain was a dominant failure source,
and produces the measurements needed to prioritize GIS, semantics, terrain,
shape, forest, or performance work.

Scientific risk: Medium. Results may still be poor because shape, vegetation,
source conditions, DEM representation, and terrain/material parameters are
missing. Such a result must be interpreted as pilot evidence, not model
validation failure by itself.

Engineering risk: Medium. CRS, datum, DEM extent, nodata, clamping, private
data hygiene, output volume, file count, and hazard-stage performance can fail.

Likely affected areas: `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
`docs/tschamut_swissalti3d_pilot.md`,
`scripts/prepare_tschamut_swissalti3d_pilot.py`,
`scripts/run_performance_benchmark.py`, `scripts/build_hazard_layers.py`,
`validation/templates/`, ignored `validation/private/`,
`validation/results/`, and `hazard/results/`.

Evidence needed: manifest review for EPSG:2056/LN02, extent, resolution,
source-zone metadata, and tile provenance; baseline vs rotational metrics;
proxy vs real-terrain comparison; reach/deposition/energy/jump/impact QA;
release-mode trajectories/s, rows/s, bytes, file counts, hazard-stage timings,
and ensemble-size feasibility estimates; notes on whether cliff edges,
smoothing, interpolation, forest in DEMs, or micro-topography appear to control
results.

Minimal acceptable deliverable: A concise execution report with commands,
manifest checks, metric tables, visual QA, performance-readiness section,
terrain-representation observations, and a next-step decision. Raw DEM and
large generated outputs remain out of git.

What not to do: Do not tune parameters, alter release zones after seeing
results, commit private geodata, claim operational validation, or optimize
physics speculatively.

Estimated order: 1.

## Target 2: Hazard-Map Semantics And Interpretation Guide

Objective: Formalize conditional hazard-map semantics before expanding map
products: normalization conventions, weighting assumptions, release-density
interpretation, source-zone normalization, block weighting, overlapping source
zones, terrain-class conditionality, and interpretation limits.

Rationale: Ambiguous map semantics can invalidate interpretation even when
trajectory simulation is technically correct. The repository correctly avoids
annual-frequency claims, but conditional maps still need stronger language
around what their weights and denominators mean.

Expected value for Swiss hazard-map goal: Very high. It reduces misuse risk,
stabilizes GIS package manifests, and gives future source-zone, block-scenario,
and uncertainty work a common vocabulary.

Scientific risk: Medium. Semantics may look more authoritative than the
underlying source-frequency evidence supports.

Engineering risk: Low. Mostly documentation, schema labels, fixture manifests,
and consistency checks.

Likely affected areas: `docs/hazard_layers.md`,
`docs/probabilistic_scenario_model_design.md`,
`docs/probabilistic_hazard_framework_priorities.md`,
`docs/roadmap_hazard_mapping.md`, `src/probabilistic.rs`,
`tests/probabilistic_phase1.rs`, and map package fixtures.

Evidence needed: examples showing equal sampling weights, conditional weights,
unsupported physical probability, unsupported annual frequency, overlapping
source-zone handling, and recommended/non-recommended user language.

Minimal acceptable deliverable: A formal semantics guide referenced by hazard
docs and enforced by small manifest/schema tests where possible.

Sequencing note: M005 created the guide outline, M006 adds language examples
only, and M007 owns manifest/schema enforcement. These incremental
micro-milestones should complete the deliverable rather than weaken it.

What not to do: Do not invent annual rates, physical source probabilities,
exposure, vulnerability, or risk semantics.

Estimated order: 2.

## Target 3: Pilot GIS/QGIS Package And Raster Semantics

Objective: Turn current hazard outputs into a QGIS-reviewable pilot package:
CRS-bearing GeoTIFF rasters, explicit grid metadata, release-zone vector
sidecars, manifest identities, semantic labels, and a visual QA checklist.
Produce correct local GeoTIFF first; keep verified COG as a later
production/tiled-delivery step.

Rationale: Swiss pilot review requires geospatial products that align safely
with LV95 terrain and can be inspected by GIS users. For the first local pilot,
CRS, affine transform, nodata, grid alignment, and QGIS inspectability matter
more than cloud optimization.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low to medium. It does not improve physics, but geospatial or
semantic mistakes could create misleading maps.

Engineering risk: Medium. GeoTIFF transforms, nodata, row order, compression,
COG conformance, and dependency boundaries need tests.

Likely affected areas: `scripts/build_hazard_layers.py`,
`docs/hazard_layers.md`, `docs/swisstopo_data_strategy.md`,
`docs/scalability_and_data_formats_review.md`, `tests/test_hazard_layers.py`,
and hazard fixtures.

Evidence needed: round-trip parity between CSV/ASCII and GeoTIFF values;
CRS/transform/nodata manifest checks; QGIS or raster-library smoke inspection;
explicit failure for unsupported COG claims until verified.

Minimal acceptable deliverable: A tiny fixture producing GeoTIFF outputs with
manifested CRS/extent/nodata and conditional-map semantic labels.

What not to do: Do not put GIS dependencies in the trajectory kernel; do not
let COG work delay CRS-correct GeoTIFF/QGIS inspection; do not call non-COG
files COG.

Estimated order: 3.

## Target 4: Source-Zone And Block-Scenario Semantics V1

Objective: Define and validate a minimal scenario schema for source-zone
identity, release sampling, source-zone derivation policy, block-size classes,
shape-class placeholders, sampling weights, and explicit absence of physical or
annual probabilities.

Rationale: Source-zone derivation is an early national hazard-map need, not a
late orchestration detail. Deterministic polygon sampling is useful, but Swiss
automation will need a defensible policy based on slope, geology, inventories,
or field interpretation.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Source and block assumptions can look more precise
than evidence supports.

Engineering risk: Low to medium.

Likely affected areas: `src/probabilistic.rs`,
`docs/probabilistic_scenario_model_design.md`,
`docs/probabilistic_hazard_framework_priorities.md`,
`docs/dataset_strategy.md`, `validation/cases/probabilistic_phase1_smoke.yaml`,
`tests/probabilistic_phase1.rs`, and probabilistic fixtures.

Evidence needed: parser rejection of annual/physical labels when evidence is
absent; deterministic joins between scenario rows and trajectory metadata;
conditional map package labels; fixed-block and block-class examples; explicit
notes on source-zone derivation evidence levels.

Minimal acceptable deliverable: Schema and fixture updates for conditional
source-zone/block-class scenario metadata, with no annual-frequency
computation.

What not to do: Do not invent annual release rates, physical block
probabilities, or risk semantics.

Estimated order: 4.

## Target 5: DEM And Terrain-Representation Sensitivity Benchmark

Objective: Build a reproducible benchmark framework for DEM resolution,
terrain smoothing, interpolation artifacts, cliff-edge representation,
micro-topography/subgrid roughness, vegetation representation in DEMs, and
hazard-layer stability under terrain perturbations.

Rationale: Terrain representation uncertainty may dominate trajectory realism
and hazard-map structure as much as contact physics or shape. Multi-resolution
and interpolation sensitivity should precede calibration claims.

Expected value for Swiss hazard-map goal: Very high. It directly tests whether
map patterns are stable under public-terrain representation choices and helps
separate DEM artifacts from physics failures.

Scientific risk: Medium. Perturbations can be arbitrary if not tied to real
DEM products and terrain-processing assumptions.

Engineering risk: Medium. Requires careful fixture design, raster alignment,
map-difference metrics, and reproducible terrain variants.

Likely affected areas: `docs/model_design.md`,
`docs/swisstopo_data_strategy.md`, `docs/validation_plan.md`,
`docs/hazard_layers.md`, `src/terrain.rs`, `scripts/build_hazard_layers.py`,
`validation/cases/`, `verification/`, and terrain fixtures.

Evidence needed: multi-resolution terrain runs; strict vs clamped/interpolated
comparisons; smoothing/no-smoothing comparisons; cliff-edge and nodata edge
fixtures; reach/deposition/energy/jump map-difference diagnostics; stability
summary for at least one Swiss-style terrain fixture.

Minimal acceptable deliverable: A small deterministic DEM sensitivity
benchmark with map-difference metrics and a report template. It may use
fixtures before private real-site data are available.

What not to do: Do not calibrate contact parameters to compensate for DEM
resolution, smooth terrain silently, or treat swisstopo data as validation
evidence by itself.

Estimated order: 5.

## Target 6: Expanded Chant Sura Contact And Shape-Readiness Validation

Objective: Improve Chant Sura contact/trajectory evidence by expanding or
cleaning DEM-backed contact fixtures, documenting proxy-contact uncertainty,
and attaching passive EOTA/shape metadata where provenance is auditable.

Rationale: Shape and contact are among the largest physics gaps. External
review reinforces that shape is a dominant driver of lateral spread, runout,
rotational behavior, and energy dissipation, and that Chant Sura shape evidence
should be strengthened before active shape-contact work proceeds.

Expected value for Swiss hazard-map goal: High scientific value.

Scientific risk: Medium. Segment-boundary contacts may remain too approximate
for strong conclusions.

Engineering risk: Medium.

Likely affected areas: `scripts/prepare_chant_sura_public_benchmark.py`,
`scripts/summarize_chant_sura_contact_diagnostics.py`,
`validation/data/processed/chant_sura_2020/`,
`validation/cases/chant_sura_contact*.yaml`,
`docs/chant_sura_contact_validation.md`, `docs/dataset_strategy.md`,
`docs/shape_aware_block_scaffold_design.md`, and passive shape metadata.

Evidence needed: deterministic split records; contact timing/rebound/jump/
energy metrics for model-selection and held-out subsets; explicit proxy-contact
caveats; no tuning or default changes.

Minimal acceptable deliverable: Expanded or audited contact/shape-readiness
fixture/report plus passive shape scenario semantics where provenance is
auditable.

What not to do: Do not use proxy contacts as exact truth; do not run
`shape_contact_v0` held-out validation while its gates remain blocked.

Estimated order: 6.

## Target 7: Forest/Obstacle Relevance Scoping For The Swiss Pilot Domain

Objective: Before interpreting the first Swiss valley pilot, assess whether
forest, buildings, roads, barriers, or other obstacles are first-order boundary
conditions in the chosen domain.

Rationale: Forest may materially reduce propagation probability and intensity
in Swiss Alpine terrain. The repo should scope this early while still deferring
implementation.

Expected value for Swiss hazard-map goal: High when the pilot domain contains
forest or obstacles; medium otherwise.

Scientific risk: Medium. Ignoring forest/obstacles can overstate reach or
intensity; silently absorbing them into terrain/material parameters would
confuse physics, calibration, and scenario assumptions.

Engineering risk: Low to medium for scoping; high only if implementation is
started.

Likely affected areas: `docs/swisstopo_data_strategy.md`,
`docs/roadmap_hazard_mapping.md`, `docs/dataset_strategy.md`, the pilot report,
and future terrain-context docs.

Evidence needed: pilot-domain forest/obstacle inventory from allowed public or
context data; statement of whether no-forest/no-obstacle assumptions are
acceptable, limiting, or invalidating; recommendation to defer, mask/exclude,
scenario-split, or design explicit future physics.

Minimal acceptable deliverable: A short scoping memo tied to the selected pilot
domain and cited public/context layers.

What not to do: Do not implement forest/barrier physics in this package; do not
tune restitution or terrain classes to mimic forest; do not call no-forest
outputs operational hazard maps.

Estimated order: 7.

## Target 8: Validation Maturity Framework

Objective: Formalize a validation maturity hierarchy for repository claims:
V0 analytic verification, V1 synthetic trajectory realism, V2 impact-level
field validation, V3 site-scale hazard-pattern validation, V4 cross-site
generalization, and V5 operational reproducibility.

Rationale: The repository already distinguishes verification, calibration,
validation, pilot evidence, shape-readiness, and performance gates. A named
maturity framework will reduce overclaim risk and make reports, README text,
and future papers more consistent.

Expected value for Swiss hazard-map goal: High. It clarifies what evidence each
result supports and prevents pilot evidence from being mistaken for operational
validation.

Scientific risk: Low to medium. The main risk is creating labels without
enforcing them in reports.

Engineering risk: Low.

Likely affected areas: new `docs/validation_maturity_framework.md`,
`README.md`, `AGENTS.md`, `docs/validation_plan.md`, `docs/dataset_strategy.md`,
validation report templates, and consistency checks.

Evidence needed: mapping from existing verification/validation cases to
maturity levels; examples of allowed and forbidden claims for each level;
report-template language.

Minimal acceptable deliverable: A concise framework document referenced by
validation docs and future pilot reports. Updating `AGENTS.md` can follow in a
separate procedural docs change.

What not to do: Do not relabel current evidence upward; do not imply
operational readiness before cross-site and reproducibility evidence exist.

Estimated order: 8.

## Target 9: Deterministic Local Parallel Execution Prototype

Objective: Prototype deterministic local multithreaded execution and
thread-safe hazard accumulation before trajectory Parquet or SLURM
orchestration work: reproducible seeds, order-independent reducers, memory
scaling, I/O concurrency checks, and scaling benchmarks.

Rationale: The long-term target of roughly 10,000 trajectories per release zone
makes local parallel scaling a core feasibility issue. A measured multithreaded
CSV/reducer workflow may outperform premature distributed or Parquet-heavy
designs.

Expected value for Swiss hazard-map goal: High engineering value after the
pilot has identified real output and reducer pressure.

Scientific risk: Low, provided outputs are parity-tested and deterministic.

Engineering risk: Medium to high. Requires careful ownership of RNG,
execution-order independence, reducer merges, memory use, and file layout.

Likely affected areas: `src/stochastic.rs`, `src/simulation.rs`,
`src/validation.rs`, `src/manifest.rs`, `scripts/build_hazard_layers.py`,
`tests/hpc_readiness.rs`, performance benchmark scripts, and
`docs/scalability_and_data_formats_review.md`.

Evidence needed: serial vs parallel parity; deterministic outputs independent
of worker count and execution order; scaling benchmarks versus trajectory
count and output volume; memory/file-count report; thread-safe reducer contract.

Minimal acceptable deliverable: An opt-in local parallel runner or prototype
fixture with deterministic parity tests and a benchmark report. It should be
selected after pilot measurements confirm parallel execution or reduction is
the next bottleneck.

What not to do: Do not add MPI, GPU, or SLURM first; do not make parallelism
change default numerical behavior; do not optimize the kernel without evidence
that it is the limiting path.

Estimated order: 9.

## Target 10: Active Shape-Contact Decision Gate, Not Runtime Feature First

Objective: Convert the paused `shape_contact_v0` status into a formal gate:
required provenance, diagnostics, non-regression metrics, and failure criteria
before any public runtime wiring proceeds.

Rationale: Shape is scientifically crucial, but the first internal result was
uncertain/failed. The next shape-runtime step should reduce risk before adding
public behavior.

Expected value for Swiss hazard-map goal: High long-term scientific value.

Scientific risk: High. A simplistic shape model may trade one failure mode for
another or hide terrain/material errors.

Engineering risk: High.

Likely affected areas: `docs/active_shape_contact_design.md`,
`docs/post_shape_contact_v0_pause_next_step.md`,
`docs/shape_contact_v0_experimental_contract.md`, `src/shape.rs`, and internal
validation under `validation/internal/`.

Evidence needed: frozen diagnostic contract; energy non-increase checks;
baseline parity; model-selection results that do not degrade Chant Sura or
recreate Tschamut rotational over-run.

Minimal acceptable deliverable: A gate document and internal-only tests that
define when public shape runtime work is allowed.

What not to do: Do not implement a broad polyhedral solver, tune shape
constants, or present passive shape metadata as active validation.

Estimated order: 10.

## Target 11: Terrain/Material Calibration Design With Holdout Policy

Objective: Design a no-hidden-tuning calibration framework for terrain/material
classes, including parameter bounds, objective functions, training/held-out
datasets, and manifest labels. Implementation of calibrated values should wait
for pilot evidence, DEM sensitivity results, and validation maturity labels.

Rationale: Terrain classes are essential for maps but dangerous without
calibration discipline. DEM representation, source zones, shape, and forest can
all masquerade as material-parameter effects.

Expected value for Swiss hazard-map goal: High, once real-site terrain,
sensitivity benchmarks, and validation splits exist.

Scientific risk: Very high if done prematurely.

Engineering risk: Medium.

Likely affected areas: `docs/terrain_material_interaction_protocol.md`,
`docs/terrain_material_diagnostic_gap_report.md`, `docs/validation_plan.md`,
`docs/dataset_strategy.md`, `calibration/`, and terrain-class validation cases.

Evidence needed: explicit calibration/validation split; objective-function
documentation; parameter bounds and provenance; holdout metrics showing
transfer, not only fit.

Minimal acceptable deliverable: Design document and schema additions for
calibration status/provenance, with synthetic fixtures only.

What not to do: Do not tune terrain classes on Tschamut proxy results; do not
promote synthetic class values as calibrated material parameters; do not use
terrain classes to absorb forest, DEM, or shape errors.

Estimated order: 11.

## Target 12: Trajectory Samples Table And Batched Hazard Reader

Objective: Add an opt-in `trajectory_samples_table_v1` columnar output and
projected/batched reader only if pilot and local-parallel measurements show
trajectory CSV file count or Python row processing is the limiting path.

Rationale: Impact-event Parquet exists, but trajectory CSVs still feed most
hazard layers. Columnar output is useful only if reader parity and throughput
improve the measured workflow.

Expected value for Swiss hazard-map goal: Medium to high for larger pilots and
future production.

Scientific risk: Low.

Engineering risk: Medium to high.

Likely affected areas: `src/validation.rs`, `scripts/build_hazard_layers.py`,
`docs/trajectory_parquet_next_step_decision.md`,
`docs/columnar_output_design_decision.md`, `tests/test_hazard_layers.py`, and
performance benchmark scripts.

Evidence needed: numerical parity for reach, deposition, max energy, max jump,
velocity, and exceedance layers; file-count and byte-volume reduction; no
slower projected/batched hazard reads at representative scale; unchanged CSV
defaults.

Minimal acceptable deliverable: Optional prototype with benchmark report and
manifest schema, not default output.

What not to do: Do not remove CSV debug outputs, add a writer-only Parquet
feature, or add probability semantics to the trajectory table.

Estimated order: 12.

## Target 13: Chunked/Tiled Reducer Contract And Resume Semantics

Objective: Implement a minimal local chunk manifest and deterministic reducer
merge contract for reach counts, deposition counts, maxima, exceedances, and
significant-impact counts.

Rationale: National or valley-scale production requires resumable chunks and
mergeable rasters before SLURM orchestration. This should follow the local
parallel and reducer contracts, not precede them.

Expected value for Swiss hazard-map goal: High engineering value.

Scientific risk: Low to medium. Merge semantics for percentiles and uncertainty
need care.

Engineering risk: High.

Likely affected areas: `src/manifest.rs`, `scripts/build_hazard_layers.py`,
`docs/scalability_and_data_formats_review.md`,
`tests/fixtures/hpc/chunk_manifest_v0.json`, and future orchestration scripts.

Evidence needed: chunked vs single-run raster parity; deterministic checksums
independent of chunk order; incomplete chunk handling and resume status;
documented merge rules.

Minimal acceptable deliverable: Local two-chunk fixture whose merged outputs
match an unchunked fixture.

What not to do: Do not add SLURM, MPI, GPU, or distributed frameworks before
local chunk/reducer contracts are stable.

Estimated order: 13.

## Target 14: Fragmentation And Broader Obstacle Implementation Scoping

Objective: Produce a later implementation-oriented scoping review for
fragmentation and broader obstacle modelling requirements after the first
forest/obstacle relevance memo has clarified pilot-domain needs.

Rationale: Fragmentation and engineered mitigation structures can matter for
some sites, but they should not be added generically before the pilot
identifies whether they are blockers.

Expected value for Swiss hazard-map goal: Medium, domain-dependent.

Scientific risk: Medium if omitted where important; high if implemented
without data.

Engineering risk: Medium to high for future implementation.

Likely affected areas: `docs/roadmap_hazard_mapping.md`,
`docs/swisstopo_data_strategy.md`, `docs/dataset_strategy.md`, and future
terrain-context and scenario docs.

Evidence needed: pilot-domain inventory of fragmentation or
engineered-obstacle relevance; public geodata candidates; decision whether to
defer, model as scenario exclusion, or design explicit future physics.

Minimal acceptable deliverable: A gap note that says whether these effects are
material to the first pilot.

What not to do: Do not silently absorb fragmentation, forest, or barriers into
restitution or terrain-class tuning.

Estimated order: 14.

## Recommended Sequence

1. Controlled real-site Tschamut/swissALTI3D pilot with embedded performance
   and terrain-representation observations.
2. Hazard-map semantics and interpretation guide.
3. Pilot GIS/QGIS package and raster semantics.
4. Source-zone and block-scenario semantics v1.
5. DEM and terrain-representation sensitivity benchmark.
6. Expanded Chant Sura contact and shape-readiness validation.
7. Forest/obstacle relevance scoping for the chosen Swiss pilot domain.
8. Validation maturity framework.
9. Deterministic local parallel execution prototype, if pilot measurements
   justify it.
10. Active shape-contact decision gate.
11. Terrain/material calibration design with holdout policy.
12. Trajectory samples table and batched hazard reader, only after measured
    output-reader pressure.
13. Chunked/tiled reducer contract and resume semantics.
14. Fragmentation and broader obstacle implementation scoping, timed by
    pilot-domain need.

The sequence is intentionally not "more physics first." It first asks the
existing Swiss stack to produce pilot and feasibility evidence, then formalizes
map semantics, GIS products, source-zone assumptions, terrain sensitivity,
shape-readiness evidence, and forest context before calibration or public shape
runtime work. Performance remains coupled to realistic scientific workflows:
measure in the pilot, prototype deterministic local parallelism when warranted,
and defer columnar/distributed work until the measured bottleneck is clear.
