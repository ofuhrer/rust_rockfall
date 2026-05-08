# Next Development Targets

Status: prioritized development directions after the selected Tschamut public
pilot manifest, source/scenario policy, reconciled DEM-sensitivity and
conditional gate evidence, automated GIS package review record, and local
scaling review. These are planning recommendations only and do not change
simulator behavior.

The repository now has substantial scaffolding and selected-domain contracts
for the Swiss hazard-map workflow. The selected Tschamut run-freeze, DEM
sensitivity gate, conditional pilot report, GIS package review, scaling review,
and visual-QA review record have been reconciled against regenerated local
ignored artifacts. The current critical gap is no longer evidence consistency,
an unclassified visual-QA gate, unscoped forest/obstacle omission, or missing
local threaded ensemble semantics. Larger ensembles should still proceed only
if convergence, performance, and output-volume evidence justify them. The next
development task should design physical/source-frequency semantics before any
annual or physical prototype is attempted.

## Target 1: Reconcile And Regenerate Selected Pilot Gate Evidence

Objective: Bring the selected Tschamut run-freeze, DEM-sensitivity evidence,
conditional pilot report, GIS package review, and scaling review into one
authoritative, locally reproducible state.

Rationale: The project could not honestly claim a completed conditional pilot
while the checked-in run-freeze said `no-go` and the GIS/scaling reviews
referenced ignored artifacts that are absent in a clean checkout. This was
resolved before ensemble scaling or source-frequency design.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium. Reconciliation must not tune parameters or reinterpret
missing data as model behavior.

Engineering risk: Medium. Local ignored outputs, checksums, reports, and
manifest paths must agree.

Likely affected areas:
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
`docs/tschamut_public_conditional_pilot_gate_report.md`,
`docs/tschamut_public_pilot_gis_package_review.md`,
`docs/tschamut_public_pilot_scaling_review.md`,
`scripts/validate_public_real_site_conditional_pilot_run.py`,
`scripts/run_dem_terrain_sensitivity.py`, `scripts/validate_pilot_gis_package.py`,
ignored `data/processed/`, `validation/private/`, and `hazard/results/` paths.

Evidence needed: regenerated or verified processed DEM and metadata, DEM
sensitivity report, conditional curve table, hazard/map/GIS/scaling manifests,
artifact checksums, runtime and output-budget metrics, and a
pass/no-go/inconclusive classification that is consistent across reports.

Minimal acceptable deliverable: complete. The selected run-freeze
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` now
records `gate_run_completed` with an `inconclusive` report classification. It
references regenerated ignored DEM-sensitivity, validation, hazard, GIS
package, reducer, scaling, runtime, memory, file-count, byte-count, and
checksum evidence, while the reports consistently state that generated
artifacts remain ignored and non-operational.

What not to do: Do not tune physics, change defaults, commit raw geodata,
commit large generated outputs, or claim operational/annual/physical/risk
validity.

Estimated order: 1.

## Target 2: Run Manual QGIS Visual QA For The Selected Package

Objective: Complete the human GIS review step for the selected pilot package
after the package artifacts are regenerated or verified.

Rationale: Automated manifest/file QA can verify inventory and checksums, but
it cannot confirm visual alignment, nodata styling, source-zone overlay
interpretation, or map-label clarity in QGIS.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low to medium. Visual QA can reveal spatial metadata errors
that would mislead interpretation.

Engineering risk: Low to medium.

Likely affected areas: `docs/tschamut_public_pilot_gis_package_review.md`,
`docs/pilot_gis_package.md`,
`validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`, local ignored
package outputs.

Evidence needed: QGIS review notes for CRS alignment, DEM/hillshade or terrain
context alignment, nodata styling, source-zone overlay, layer labels, and
conditional-product language.

Minimal acceptable deliverable: complete at the share-safe checklist level. The
selected visual-QA record
`validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml` classifies manual
GIS/QGIS visual QA as `inconclusive` because QGIS was unavailable in the
non-GUI agent environment, while automated package QA passed and all required
CRS, datum, alignment, nodata, source-zone, label, and claim-boundary checks are
classified. The validator
`scripts/validate_pilot_gis_visual_qa.py --require-existing-package` checks the
record against the ignored local package when artifacts exist.

What not to do: Do not create a production QGZ, GeoPackage, COG, risk map, or
operational map product in this step.

Estimated order: 2.

## Target 3: Scope Forest And Obstacle Omission For Tschamut

Objective: Determine whether forest, buildings, roads, barriers, nets, or
other obstacles are first-order boundary conditions for the selected Tschamut
pilot corridor.

Rationale: A no-forest/no-obstacle conditional pilot may be acceptable,
limiting, or invalidating depending on the corridor. This should be explicit
before terrain/material, contact, or calibration conclusions are drawn.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium if omission is silently absorbed into model parameters.

Engineering risk: Low for scoping.

Likely affected areas: `docs/swisstopo_data_strategy.md`,
`docs/tschamut_public_conditional_pilot_gate_report.md`,
`docs/tschamut_public_obstacle_context_scope.md`,
`validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`, future pilot
report notes.

Evidence needed: share-safe inventory of available public context layers and a
classification of obstacle omission as acceptable, limiting, or invalidating
for the selected gate.

Minimal acceptable deliverable: complete at the share-safe scoping level. The
selected scope record
`validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml` classifies
forest and obstacle omission as `limiting` because public SWISSIMAGE,
swissTLM3D, swissSURFACE3D/swissSURFACE3D Raster, and swissBUILDINGS3D context
layers are documented but not locally reviewed for the selected corridor. The
validator `scripts/validate_pilot_obstacle_scope.py` checks the six required
context categories, future context actions, and claim boundaries. No obstacle
physics is implemented.

What not to do: Do not tune restitution, terrain classes, or stopping behavior
to mimic omitted forest or barriers.

Estimated order: 3.

## Target 4: Address Conditional-Curve/Raster Output-Volume Bottleneck

Objective: Reduce or gate the selected pilot's conditional-curve and raster
output volume before increasing ensemble size.

Rationale: The local scaling review identifies hazard conditional-curve output
volume as the next bottleneck. Larger ensembles should not proceed until the
output contract is manageable and still reviewable.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low if numerical semantics and manifests remain unchanged.

Engineering risk: Medium.

Likely affected areas: `scripts/build_hazard_layers.py`,
`scripts/summarize_pilot_scaling.py`, `docs/performance_benchmarking.md`,
`docs/scalability_and_data_formats_review.md`, hazard-layer tests, and pilot
run-freeze output budgets.

Evidence needed: output-mode comparison, manifest-visible output budgets,
checks that selected summaries remain deterministic, and a no-default-change or
explicit opt-in recommendation before ensemble scaling.

Minimal acceptable deliverable: complete for the curve-table bottleneck.
`scripts/build_hazard_layers.py --conditional-curve-export summary-only`
provides an opt-in no-default-change mode that keeps conditional exceedance
rasters and metadata summaries but skips the large per-cell curve CSV table.
Focused tests verify the full default path remains available and the
summary-only path omits the table from the output manifest.

What not to do: Do not remove existing debug outputs, change current hazard
semantics, add distributed orchestration, or hide denominators/provenance.

Estimated order: 4.

## Target 5: Increase Ensemble Size Toward The Target Count

Objective: Increase trajectory count only after the small pilot gate and local
scaling evidence are reproducible and interpretable.

Rationale: The target of roughly 10,000 trajectories per release zone is useful
only if convergence diagnostics and output handling can show what additional
samples change.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Larger samples can make uncertain source-zone or
block assumptions look falsely precise.

Engineering risk: Medium to high.

Likely affected areas: pilot run-freeze files, performance docs, validation
runner/output modes, hazard reducers, and convergence summaries.

Evidence needed: convergence diagnostics for conditional curves and supporting
layers, trajectory-count sensitivity, output budget compliance, and
worker-count-independent reduced outputs.

Minimal acceptable deliverable: complete as a documented no-go feasibility
gate. `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml` and
`docs/tschamut_public_ensemble_feasibility.md` record that ensemble increase is
not authorized yet because target-scale convergence is not established, manual
GIS/QGIS visual QA remains inconclusive, and forest/obstacle omission remains
limiting. `scripts/validate_pilot_ensemble_feasibility.py` checks the decision,
required preconditions, output-budget controls, and claim boundaries.

What not to do: Do not scale up before source-zone, DEM, small-gate, GIS, and
performance interpretation are stable.

Estimated order: 5.

## Target 6: Complete Fallible Terrain/Integrator API Migration

Objective: remove remaining production footguns around infallible terrain and
integration entry points before larger real-site or parallel runs.

Rationale: Real DEMs can contain nodata, crop-edge gaps, and out-of-domain
queries. The normal validation path now uses structured terrain errors, but the
legacy `height`/`normal` terrain methods and `simulate_fixed_step*` wrappers can
still panic if downstream code uses them with DEM terrain. This is the largest
near-term robustness gap for batch execution semantics.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low if behavior is preserved and errors are only made more
explicit.

Engineering risk: Medium because public Rust callers may still use the
compatibility wrappers.

Likely affected areas: `src/terrain.rs`, `src/integrator.rs`,
`src/simulation.rs`, direct Rust tests, `docs/architecture_boundaries.md`, and
`docs/model_design.md`.

Evidence needed: grep/test coverage showing new DEM-facing code uses
`try_height`/`try_normal` and `try_simulate_fixed_step*`, structured
terrain-error tests for strict DEM nodata/out-of-domain queries, and clear
documentation of compatibility wrapper panic semantics.

Minimal acceptable deliverable: complete. The runtime fixed-step integration
path now uses fallible contact-motion helpers that propagate `TerrainError`
through `IntegrationError` instead of relying on infallible DEM queries inside
contact response, while legacy `simulate_fixed_step*`, `height`, and `normal`
wrappers remain compatibility helpers. `tests/config_io_terrain.rs` covers
strict DEM runtime and contact-response terrain errors, and
`scripts/check_repo_consistency.py` rejects new infallible terrain/contact
calls in `src/integrator.rs`.

What not to do: Do not change DEM interpolation numerics, contact physics,
defaults, validation baselines, or classify terrain failures as physical stops.

Estimated order: 6.

## Target 7: Split Validation And Experimental Shape Internals By Concern

Objective: reduce maintenance and review risk in `src/validation.rs` and
`src/shape.rs` without changing behavior.

Rationale: Both files have grown into multi-thousand-line modules that mix
library logic, V&V harnesses, exporters, manifests, diagnostics, and internal
experimental scaffolds. This slows review, increases compile/check time, and
blurs the boundary between reusable trajectory code and validation tooling.

Expected value for Swiss hazard-map goal: Medium to high. It improves
contributor velocity and makes later pilot, schema, and output work safer.

Scientific risk: Low if the split is mechanical and tests prove behavior is
unchanged.

Engineering risk: Medium because these files touch many tests and workflows.

Likely affected areas: `src/validation.rs`, new validation submodules,
`src/shape.rs`, potential shape submodules, tests, and
`docs/architecture_boundaries.md`.

Evidence needed: behavior-preserving module splits with no output/schema
changes, unchanged public validation and `shape_contact_v0` guard tests, and
unchanged `cargo run -- validate --all` results.

Minimal acceptable deliverable: complete for one narrow concern. The pure
metric-math helpers used by validation metrics now live in
`src/validation/metric_math.rs` with focused unit tests, while
`src/validation.rs` keeps the metric orchestration, case loading, output
writing, manifests, and public behavior unchanged. `scripts/check_repo_consistency.py`
guards the module boundary.

What not to do: Do not use this as a vehicle for new physics, new schemas,
baseline refreshes, or public `shape_contact_v0` execution.

Estimated order: 7.

## Target 8: Add Deterministic Local Parallel Ensemble Driver

Objective: introduce local parallel trajectory execution with deterministic
ordering, chunk/reducer metadata, and identical reduced outputs.

Rationale: Sequential ensemble execution is a scaling bottleneck relative to
the 10,000-trajectory-per-release-zone design target. Parallelism should start
locally and deterministically before CSCS/SLURM orchestration.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Parallel execution must not change seeds, trajectory
ids, reducers, convergence diagnostics, or output interpretation.

Engineering risk: Medium to high.

Likely affected areas: `src/simulation.rs`, validation runner/output modes,
chunk manifests, hazard reducers, performance docs, and HPC-readiness tests.

Evidence needed: order-independent ensemble tests, serial-versus-parallel
bitwise or tolerance-controlled output comparisons, deterministic chunk
manifests, row-count/checksum provenance, and pilot-scale timing evidence.

Minimal acceptable deliverable: complete. `simulate_ensemble_parallel` and
`simulate_ensemble_parallel_with_contact_parameters` provide an opt-in local
threaded ensemble path with serial default preserved. The returned
`LocalParallelEnsembleExecution` records `local_parallel_ensemble_v1`
provenance, requested/effective worker counts, deterministic contiguous chunks,
and merge order `requested_trajectory_index`. Focused HPC-readiness tests prove
serial-vs-parallel equality, worker-count-independent reduced outputs, and
zero-worker rejection.

What not to do: Do not add SLURM, MPI, GPU, distributed frameworks, or changed
default execution order before local chunk/reducer contracts are stable.

Estimated order: 8.

## Target 9: Design Physical Source-Frequency Semantics

Objective: Decide whether and how the project can represent physical or annual
intensity-frequency products.

Rationale: Annual products require source and block occurrence evidence, units,
overlap rules, uncertainty, and validation boundaries. Sampling weights are not
physical probability.

Expected value for Swiss hazard-map goal: High, but only after the conditional
pilot evidence exists.

Scientific risk: High.

Engineering risk: Medium.

Likely affected areas: `docs/hazard_map_semantics.md`,
`docs/probabilistic_scenario_model_design.md`, `docs/validation_plan.md`,
`docs/dataset_strategy.md`, future probability schemas and tests.

Evidence needed: source-frequency units, block-frequency semantics, uncertainty
model, source-zone overlap rules, validation/calibration separation, fixtures,
and rejection tests for incomplete frequency metadata.

Minimal acceptable deliverable: complete as a deferred design gate.
`docs/physical_source_frequency_design_gate.md` and
`validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml` define
required source-rate units, block and release-cell conditional denominators,
source-zone overlap rules, uncertainty components, and validation/calibration
separation. The validator
`scripts/validate_physical_source_frequency_design_gate.py` rejects missing
units, sampling-weight reuse as physical probability, missing overlap policy,
missing uncertainty, and premature prototype authorization.

What not to do: Do not back-fill annual frequencies from sampling weights or
calibrate frequency to match one map pattern.

Estimated order: 9.

## Target 10: Implement An Annual/Physical Intensity-Frequency Prototype

Objective: Implement a clearly experimental annual or physical frequency path
only if Target 9 passes.

Rationale: This is the long-term national hazard-map quantity, but implementing
it before the evidence model exists would create misleading products.

Expected value for Swiss hazard-map goal: Very high eventually.

Scientific risk: High.

Engineering risk: Medium.

Likely affected areas: `src/probabilistic.rs`, scenario metadata, map-package
schemas, `scripts/build_hazard_layers.py`, `tests/probabilistic_phase1.rs`,
`tests/test_hazard_layers.py`, and hazard-map docs.

Evidence needed: complete frequency metadata, analytic frequency-sum fixture,
unit-labelled per-cell curves, manifest provenance, and explicit
non-operational report labels.

Minimal acceptable deliverable: a small fixture proving annual or physical
frequency sums with explicit units and complete provenance.

What not to do: Do not promote annual-frequency defaults or imply regulatory
readiness.

Estimated order: 10.

## Completed Selected-Domain Roadmap Items

- Public Tschamut real-site swisstopo pilot package is complete at the
  share-safe manifest level.
- Domain-specific source-zone and block-scenario policy is complete at the
  share-safe policy level.
- DEM/terrain sensitivity is complete as a selected-domain gate with local
  ignored terrain-variant metrics recorded in the reconciled run-freeze.
- Small frozen conditional pilot gate is complete as a regenerated local
  ignored trajectory/hazard run with `inconclusive` report classification, not
  as an operational or target-scale result.
- Real-pilot GIS package is complete at automated manifest/file QA level for
  local ignored outputs, and the selected manual GIS/QGIS visual-QA gate is
  explicitly classified `inconclusive` by a share-safe checklist because QGIS
  was unavailable and no visual overlay evidence was produced.
- Forest and obstacle omission is scoped at the share-safe interpretation
  level and classified `limiting` for the selected Tschamut corridor because
  public context layers are documented but not locally reviewed.
- Conditional-curve output volume has an opt-in mitigation:
  `--conditional-curve-export summary-only`. The default remains full
  curve-table export for small debug/review runs.
- Ensemble-size increase has a selected-domain no-go feasibility gate. The
  gate records that larger Tschamut runs are not authorized until convergence
  diagnostics, output budgets, manual GIS/QGIS review, and forest/obstacle
  context review are resolved.
- Fallible terrain/integrator API migration is complete at the guardrail
  level. DEM-facing fixed-step runtime code propagates structured terrain
  errors through the fallible integration path, with compatibility wrappers
  retained for older analytic callers.
- One validation-module concern has been split: pure metric-math helpers now
  live in `src/validation/metric_math.rs`, with behavior-preserving unit tests
  and a consistency guard. Larger validation and shape splits remain future
  work.
- Deterministic local parallel ensemble execution is available as an opt-in
  library path. Serial execution remains the default, and no SLURM, MPI, GPU,
  distributed orchestration, validation-runner default change, or larger
  selected-domain run is introduced.
- Local scaling/output-volume summary is complete at the manifest-summary
  level and is reconciled with the authoritative run-freeze. It records
  validation/hazard timings, row/file/byte counts, reducer metadata, memory
  sidecars, and a no-default-change bottleneck decision.
- Physical/source-frequency semantics are complete as a deferred design gate.
  The gate documents the evidence and schema blockers for annual or physical
  products and does not authorize the annual/physical prototype.
- The first source-frequency blocker is partially resolved as an inactive
  evidence contract. `docs/source_frequency_evidence_contract.md`,
  `validation/templates/source_frequency_evidence_v1.yaml`, and
  `scripts/validate_source_frequency_evidence.py` define and validate
  candidate source-rate evidence records while keeping the selected template at
  `no_accepted_frequency_evidence`.
- The block/release probability evidence blocker is partially resolved as an
  inactive evidence contract.
  `docs/block_release_probability_evidence_contract.md`,
  `validation/templates/block_release_probability_evidence_v1.yaml`, and
  `scripts/validate_block_release_probability_evidence.py` define and validate
  candidate conditional block-scenario and release-cell probability evidence
  records while keeping the selected template at
  `no_accepted_block_release_probability_evidence`.
- The overlap-adjusted reducer and uncertainty-propagation blocker is
  partially resolved as an inactive precondition contract.
  `docs/physical_frequency_reducer_preconditions.md`,
  `validation/templates/physical_frequency_reducer_preconditions_v1.yaml`, and
  `scripts/validate_physical_frequency_reducer_preconditions.py` define and
  validate future reducer preconditions while keeping the selected template at
  `preconditions_not_satisfied`.

## Deferred But Important Cross-Cutting Work

- Shape/contact runtime work remains paused until provenance and rebound
  blockers are resolved.
- Terrain/material calibration remains deferred until DEM sensitivity, pilot
  evidence, and holdout policy are available.
- Production COG/tiled packages remain deferred until local GeoTIFF/QGIS
  acceptance and reducer contracts are stable.
- `validation.rs` and `shape.rs` modularization is now an explicit
  maintainability target, not a prerequisite for every feature.
- A deterministic local parallel ensemble driver is a scaling target before
  any CSCS/SLURM orchestration.

## Recommended Sequence

1. Reconcile and regenerate selected pilot gate evidence.
2. Run or classify manual QGIS visual QA for the selected package.
3. Scope forest and obstacle omission for Tschamut.
4. Address conditional-curve/raster output-volume bottleneck.
5. Increase ensemble size only if convergence and performance evidence justify
   it; current selected-domain decision is no-go.
6. Resolve the remaining physical/source-frequency design-gate blockers if
   annual or physical products are still desired: accepted evidence,
   implemented overlap-adjusted reducers, implemented uncertainty propagation,
   and validation/calibration review.
7. Implement an annual/physical prototype only if the design gate passes.
