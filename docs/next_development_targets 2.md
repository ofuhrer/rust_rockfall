# Next Development Targets

Status: proposed development directions from the strategic review in
`docs/repository_scientific_roadmap_review.md`. These targets are planning
recommendations only and do not change simulator behavior.

## Target 1: Controlled Real-Site Tschamut/swissALTI3D Pilot With Performance Gate

Objective: Execute the existing private/local Tschamut swissALTI3D pilot plan
with a real provenance-tracked DEM crop, explicit source-area metadata, baseline
and `sphere_rotational_v1` comparison cases, embedded release-mode performance
readiness measurements, no tuning, and documented visual QA.

Rationale: The repository has a Swiss pilot contract but not a real-site result.
Tschamut under-run remains confounded by proxy terrain. The pilot is primarily
workflow, confounding, and feasibility evidence; it is not decisive physics
validation.

Expected value for Swiss hazard-map goal: Very high. This directly tests
whether the Swiss workflow stack can process real terrain, whether proxy
terrain is a dominant failure source, and whether intended ensemble sizes are
locally feasible without unmanageable outputs.

Scientific risk: Medium. Results may still be poor because shape, vegetation,
source conditions, and terrain/material parameters are missing. Such a result
must be interpreted as pilot evidence, not model validation failure by itself.

Engineering risk: Medium. CRS, datum, DEM extent, nodata, clamping, and private
data hygiene can fail. Throughput, file-count, and hazard-accumulation limits
may also force smaller first-pilot ensembles than the long-term 10,000
trajectories-per-release-zone target.

Likely affected areas:

- `docs/tschamut_swissalti3d_controlled_pilot_plan.md`
- `docs/tschamut_swissalti3d_pilot.md`
- `scripts/prepare_tschamut_swissalti3d_pilot.py`
- `scripts/run_performance_benchmark.py`
- `scripts/build_hazard_layers.py`
- `validation/templates/`
- ignored `validation/private/`, `validation/results/`, and `hazard/results/`

Evidence needed:

- manifest review showing LV95/EPSG:2056, LN02, extent, resolution, tile
  provenance, release-zone metadata, and output identities;
- baseline vs rotational validation metrics;
- proxy vs real-terrain comparison;
- reach/deposition/energy/jump/impact/exceedance layer QA;
- release-mode performance report with trajectories/s, rows/s, output bytes,
  output file counts, hazard-stage timings, explicit-grid/no-plot settings, and
  an ensemble-size feasibility estimate;
- explicit conclusion: under-run improves, persists, or worsens.

Minimal acceptable deliverable: A concise execution report with input inventory,
commands, manifest checks, metric tables, performance-readiness section, visual
QA notes, and next-step decision. Raw DEM and generated large outputs remain out
of git.

What not to do: Do not tune parameters, alter release zones after seeing
results, commit private geodata, claim operational validation, or optimize
physics for speed.

Estimated order: 1.

## Target 2: Pilot GIS/QGIS Package And Raster Semantics

Objective: Turn current hazard outputs into a QGIS-reviewable pilot package:
CRS-bearing GeoTIFF rasters, explicit grid metadata, release-zone vector
sidecars, manifest identities, and a visual QA checklist. Produce correct local
GeoTIFF first; keep verified COG as a later production/tiled-delivery step.

Rationale: The current hazard builder is scientifically traceable but still
partly debug-format oriented. Swiss pilot review requires geospatial products
that align safely with LV95 terrain and QA layers.

Expected value for Swiss hazard-map goal: High. Prevents map interpretation
errors and makes pilot outputs inspectable by GIS users. For the first local
pilot, CRS, affine transform, nodata, grid alignment, and QGIS inspectability
matter more than cloud optimization.

Scientific risk: Low to medium. It does not improve physics, but geospatial
mistakes could create misleading maps.

Engineering risk: Medium. GeoTIFF transforms, nodata, row order, compression,
COG conformance, and dependency boundaries need tests.

Likely affected areas:

- `scripts/build_hazard_layers.py`
- `docs/hazard_layers.md`
- `docs/swisstopo_data_strategy.md`
- `docs/scalability_and_data_formats_review.md`
- `tests/test_hazard_layers.py`
- hazard fixtures under `tests/fixtures/hazard/`

Evidence needed:

- round-trip parity between CSV/ASCII and GeoTIFF values;
- CRS/transform/nodata manifest checks;
- QGIS or raster-library smoke inspection for a small fixture;
- explicit failure for unsupported COG claims until verified.

Minimal acceptable deliverable: A tiny fixture producing GeoTIFF outputs with
manifested CRS/extent/nodata plus documentation explaining debug GeoTIFF vs
future production COG.

What not to do: Do not put GIS dependencies in the trajectory kernel; do not
let COG work delay CRS-correct GeoTIFF/QGIS pilot inspection; do not call
non-COG files COG; do not change hazard layer values.

Estimated order: 2.

## Target 3: Source-Zone And Block-Scenario Semantics V1

Objective: Define and validate a minimal scenario schema for source-zone
identity, release sampling, block-size classes, shape-class placeholders,
sampling weights, and explicit absence of physical/annual probabilities.

Rationale: Hazard maps need scenario semantics before annual probability.
Current `sampling_weighted` maps are useful but still conditional diagnostics.
External expert assessment emphasizes that defensible source-zone derivation
from DEM geomorphometry plus geological/topographic context is an early
national hazard-map need, not a late orchestration detail.

Expected value for Swiss hazard-map goal: High. It prevents ambiguous
probability language and prepares release-zone/block scenario ensembles.

Scientific risk: Medium. Source and block assumptions can look more precise
than evidence supports.

Engineering risk: Low to medium. Mostly schema, parser, manifest, and fixture
work.

Likely affected areas:

- `src/probabilistic.rs`
- `docs/probabilistic_scenario_model_design.md`
- `docs/probabilistic_hazard_framework_priorities.md`
- `validation/cases/probabilistic_phase1_smoke.yaml`
- `tests/probabilistic_phase1.rs`
- `tests/fixtures/probabilistic_phase1/`

Evidence needed:

- parser rejects annual/physical labels when required fields are absent;
- scenario rows join deterministically to trajectory metadata;
- map package manifests clearly label conditional products;
- docs include examples for fixed-block and block-class scenarios.

Minimal acceptable deliverable: Schema and fixture updates for conditional
source-zone/block-class scenario metadata, with no annual-frequency computation.

What not to do: Do not invent annual release rates, physical block
probabilities, or risk semantics.

Estimated order: 3.

## Target 4: Expanded Chant Sura Contact And Shape-Readiness Validation

Objective: Improve Chant Sura contact/trajectory evidence by expanding or
cleaning DEM-backed contact fixtures, documenting proxy-contact uncertainty,
and attaching passive EOTA/shape metadata where provenance is auditable.

Rationale: Shape and contact are the largest physics gaps. External expert
assessment agrees that shape is a dominant driver of lateral spread, runout,
rotational behavior, and energy dissipation, and that Chant Sura shape evidence
should be strengthened before active shape-contact work proceeds.

Expected value for Swiss hazard-map goal: High scientific value. Better
contact evidence reduces the risk of fitting Tschamut deposition with the wrong
physics.

Scientific risk: Medium. Segment-boundary contacts may remain too approximate
for strong conclusions.

Engineering risk: Medium. Raw archive handling, DEM cropping, trajectory
segmentation, and metadata checks are nontrivial.

Likely affected areas:

- `scripts/prepare_chant_sura_public_benchmark.py`
- `scripts/summarize_chant_sura_contact_diagnostics.py`
- `validation/data/processed/chant_sura_2020/`
- `validation/cases/chant_sura_contact*.yaml`
- `docs/chant_sura_contact_validation.md`
- `docs/dataset_strategy.md`
- `docs/shape_aware_block_scaffold_design.md`
- passive shape metadata under `data/processed/` and `validation/data/`

Evidence needed:

- deterministic split records;
- contact timing/rebound/jump/energy metrics for model-selection and held-out
  subsets;
- explicit proxy-contact caveats;
- no tuning or default changes.

Minimal acceptable deliverable: Expanded or audited contact/shape-readiness
fixture/report that improves confidence in what Chant Sura can and cannot
constrain, plus passive shape scenario semantics where provenance is auditable.

What not to do: Do not use proxy contacts as exact truth; do not run
`shape_contact_v0` held-out validation while its gates remain blocked.

Estimated order: 4.

## Target 5: Forest/Obstacle Relevance Scoping For The Swiss Pilot Domain

Objective: Before interpreting the first Swiss valley pilot, assess whether
forest, buildings, roads, barriers, or other obstacles are first-order boundary
conditions in the chosen domain. Document available public/context geodata,
expected effect direction, and whether omission invalidates or only limits the
pilot interpretation.

Rationale: Forest may materially reduce propagation probability and intensity
in Swiss Alpine terrain. External expert assessment notes regional
state-of-practice examples where standing trees are explicitly included. The
repo should scope this early while still deferring implementation.

Expected value for Swiss hazard-map goal: High when the pilot domain contains
forest or obstacles; medium otherwise. It prevents overinterpreting bare-earth,
no-forest hazard layers.

Scientific risk: Medium. Ignoring forest/obstacles can overstate reach or
intensity; silently absorbing them into terrain/material parameters would
confuse physics, calibration, and scenario assumptions.

Engineering risk: Low to medium for scoping; high only if implementation is
started.

Likely affected areas:

- `docs/swisstopo_data_strategy.md`
- `docs/roadmap_hazard_mapping.md`
- `docs/dataset_strategy.md`
- pilot execution report
- future source-zone and terrain-context docs

Evidence needed:

- pilot-domain forest/obstacle inventory from allowed public/context data;
- statement of whether forest/obstacles are absent, minor, or major for the
  chosen source-runout corridor;
- recommendation to defer, mask/exclude, scenario-split, or design explicit
  future physics;
- clear statement that current layers remain no-forest/no-obstacle diagnostics.

Minimal acceptable deliverable: A short scoping memo tied to the selected pilot
domain and cited public/context layers. No simulator changes are required.

What not to do: Do not implement forest/barrier physics in this package; do not
tune restitution or terrain classes to mimic forest; do not call no-forest
outputs operational hazard maps.

Estimated order: 5.

## Target 6: Active Shape-Contact Decision Gate, Not Runtime Feature First

Objective: Convert the paused `shape_contact_v0` status into a formal gate:
required provenance, diagnostics, non-regression metrics, and failure criteria
before any public runtime wiring proceeds.

Rationale: Shape is scientifically crucial, but the first internal result was
uncertain/failed. The next shape step should reduce risk before adding public
behavior.

Expected value for Swiss hazard-map goal: High long-term scientific value.

Scientific risk: High. A simplistic shape model may trade one failure mode for
another or hide terrain/material errors.

Engineering risk: High. Orientation state, support selection, impulse
application, diagnostics, and output compatibility touch core modules.

Likely affected areas:

- `docs/active_shape_contact_design.md`
- `docs/post_shape_contact_v0_pause_next_step.md`
- `docs/shape_contact_v0_experimental_contract.md`
- `src/shape.rs`
- internal validation under `validation/internal/`

Evidence needed:

- frozen diagnostic contract;
- energy non-increase/non-explosion checks;
- baseline parity for existing contact models;
- model-selection results that do not degrade Chant Sura and do not recreate
  Tschamut rotational over-run.

Minimal acceptable deliverable: A gate document and internal-only tests that
define when public shape runtime work is allowed.

What not to do: Do not implement a broad polyhedral solver, tune shape
constants, or present passive shape metadata as active validation.

Estimated order: 6.

## Target 7: Terrain/Material Calibration Design With Holdout Policy

Objective: Design a no-hidden-tuning calibration framework for terrain/material
classes, including parameter bounds, objective functions, training/held-out
datasets, and manifest labels. Implementation of calibrated values should wait
for pilot evidence.

Rationale: Terrain classes are essential for maps but dangerous without
calibration discipline.

Expected value for Swiss hazard-map goal: High, once real-site terrain and
validation splits exist.

Scientific risk: Very high if done prematurely; it could fit structural errors
from shape, source, or terrain mistakes.

Engineering risk: Medium.

Likely affected areas:

- `docs/terrain_material_interaction_protocol.md`
- `docs/terrain_material_diagnostic_gap_report.md`
- `docs/validation_plan.md`
- `docs/dataset_strategy.md`
- `calibration/`
- `validation/cases/*terrain_classes*.yaml`

Evidence needed:

- explicit calibration/validation split;
- objective-function documentation;
- parameter bounds and provenance;
- holdout metrics showing transfer, not only fit.

Minimal acceptable deliverable: Design document and schema additions for
calibration status/provenance, with synthetic fixtures only.

What not to do: Do not tune terrain classes on Tschamut proxy results; do not
promote synthetic class values as calibrated material parameters.

Estimated order: 7.

## Target 8: Trajectory Samples Table And Batched Hazard Reader

Objective: Add an opt-in `trajectory_samples_table_v1` columnar output and
projected/batched reader only if it can match CSV hazard layers and reduce file
count/bytes without unacceptable write cost.

Rationale: Impact-event Parquet exists, but trajectory CSVs still feed most
hazard layers and create one file per trajectory.

Expected value for Swiss hazard-map goal: Medium to high for larger pilots and
future production.

Scientific risk: Low. This is data plumbing if values are parity-tested.

Engineering risk: Medium to high. Parquet writing may be slower and Python
row-wise readers can erase benefits.

Likely affected areas:

- `src/validation.rs`
- `scripts/build_hazard_layers.py`
- `docs/trajectory_parquet_next_step_decision.md`
- `docs/columnar_output_design_decision.md`
- `tests/test_hazard_layers.py`
- performance benchmark scripts

Evidence needed:

- numerical parity for reach, deposition, max energy, max jump, velocity, and
  exceedance layers;
- file-count and byte-volume reduction;
- no slower projected/batched hazard reads at 300/500 scale;
- unchanged CSV defaults.

Minimal acceptable deliverable: Optional prototype with benchmark report and
manifest schema, not default output.

What not to do: Do not remove CSV debug outputs or add probability semantics to
the trajectory table.

Estimated order: 8.

## Target 9: Chunked/Tiled Reducer Contract And Resume Semantics

Objective: Implement a minimal local chunk manifest and deterministic reducer
merge contract for reach counts, deposition counts, maxima, exceedances, and
significant-impact counts.

Rationale: National or valley-scale production requires resumable chunks and
mergeable rasters before SLURM orchestration.

Expected value for Swiss hazard-map goal: High engineering value, especially
after a real-site pilot starts producing large outputs.

Scientific risk: Low to medium. Merge semantics for percentiles/uncertainty
need care.

Engineering risk: High.

Likely affected areas:

- `src/manifest.rs`
- `scripts/build_hazard_layers.py`
- `docs/scalability_and_data_formats_review.md`
- `tests/fixtures/hpc/chunk_manifest_v0.json`
- future orchestration scripts

Evidence needed:

- chunked vs single-run raster parity;
- deterministic checksums independent of chunk order;
- incomplete chunk handling and resume status;
- documented merge rules.

Minimal acceptable deliverable: Local two-chunk fixture whose merged outputs
match an unchunked fixture.

What not to do: Do not add SLURM, MPI, GPU, or distributed frameworks before
local chunk/reducer contracts are stable.

Estimated order: 9.

## Target 10: Fragmentation And Broader Obstacle Implementation Scoping

Objective: Produce a later implementation-oriented scoping review for
fragmentation and broader obstacle modelling requirements after the first
forest/obstacle relevance memo has clarified pilot-domain needs.

Rationale: Fragmentation and engineered mitigation structures can matter for
some sites, but they should not be added generically before the pilot identifies
whether they are blockers and before forest/obstacle relevance is scoped.

Expected value for Swiss hazard-map goal: Medium, domain-dependent.

Scientific risk: Medium if omitted where important; high if implemented without
data.

Engineering risk: Medium to high for future implementation.

Likely affected areas:

- `docs/roadmap_hazard_mapping.md`
- `docs/swisstopo_data_strategy.md`
- `docs/dataset_strategy.md`
- future `terrain_classes` and scenario docs

Evidence needed:

- pilot-domain inventory of fragmentation or engineered-obstacle relevance;
- source paths for public geodata candidates;
- decision whether to defer, model as scenario exclusion, or design explicit
  future physics.

Minimal acceptable deliverable: A gap note that says whether these effects are
material to the first pilot.

What not to do: Do not silently absorb fragmentation, forest, or barriers into
restitution or terrain-class tuning.

Estimated order: 10.

## Recommended Sequence

1. Controlled real-site Tschamut/swissALTI3D pilot.
2. Pilot GIS package and production raster semantics.
3. Source-zone and block-scenario semantics v1.
4. Expanded Chant Sura contact and shape-readiness validation.
5. Forest/obstacle relevance scoping for the chosen Swiss pilot domain.
6. Active shape-contact decision gate.
7. Terrain/material calibration design with holdout policy.
8. Trajectory samples table and batched hazard reader.
9. Chunked/tiled reducer contract and resume semantics.
10. Fragmentation and broader obstacle implementation scoping, timed by
    pilot-domain need.

The sequence is intentionally not "more physics first." It first asks the
existing Swiss stack to produce pilot and feasibility evidence, then
strengthens geospatial, source-zone, shape-readiness, and forest-context
semantics, then reopens active shape and calibration with better guardrails.
