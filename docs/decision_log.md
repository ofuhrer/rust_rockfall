# Decision Log

Status: consolidated historical decision log. This file replaces several
standalone decision fragments and older roadmap snapshots that were useful at
the time but had become competing sources of truth. Executable tasks are owned
only by `task_backlog.md`; the long-term roadmap and recommendation matrix are
supporting context, not current task authority.

This log is intentionally concise. It records why a decision was made, its
current status, and where the detailed evidence now lives. It does not define
new simulator behavior, validation status, hazard-map semantics, or operational
claims.

## Active And Recent Decisions

### Backlog, Decision, And Work-Log Split

Decision: maintain exactly one executable task queue in `task_backlog.md`, keep
durable choices in `decision_log.md`, and keep completed execution history in
`agent_work_log.md`.

Current status: active. `next_development_targets.md` is retained only as a
legacy pointer for older links and must not regain an active target queue.

Rationale: prior target and roadmap documents created duplicated priority
language, forcing agents to read and update too many files for each task. The
backlog is sized for focused worker-agent execution, while the decision and
work logs separate durable rationale from execution history.

Detailed sources: `task_backlog.md`, `agent_work_log.md`.

### Progress Over Process

Decision: future work should prefer executable implementation, measured
validation, scientific analysis, reproducibility improvements, performance
work, and tested bug fixes over creating additional gates, records, validators,
roadmap labels, or consistency hooks.

Current status: active. Procedural artifacts are acceptable only when they
directly enable executable implementation or validation, or when the user
explicitly asks for planning-only work.

Rationale: the repository accumulated useful but costly gate scaffolding. The
next phase needs to reduce scientific and implementation uncertainty through
runs, measurements, scripts, features, and fixes rather than ending tasks with
only another gate recommendation.

Detailed sources: `../AGENTS.md`, `task_backlog.md`,
`real_case_intensity_frequency_implementation_roadmap.md`.

### Project Priority Rule

Decision: prioritize work by importance to automated, reproducible Swiss Alpine
rockfall hazard mapping from public geodata, with a valley-scale pilot as the
first concrete milestone.

Current status: active. This replaces older "research prototype for expert
review" wording as the main prioritization frame.

Rationale: the largest gaps are now source-zone/block-scenario semantics,
real-site conditional hazard products, DEM/terrain sensitivity, GIS packaging,
uncertainty provenance, and scalable ensemble execution.

Detailed sources: `../README.md`, `../AGENTS.md`, `roadmap_hazard_mapping.md`,
`task_backlog.md`,
`real_case_intensity_frequency_implementation_roadmap.md`.

### External Review Roadmap Pressure

Decision: accept the external review findings as roadmap pressure, not as
immediate implementation authorization.

Current status: active. DT-05 is complete as the current conditional
convergence protocol and keeps the DT-04 Balfrin evidence `inconclusive`. The
DT-06 stochastic sampling/RNG stream audit is complete. The external review
risks that exceed that protocol are now assigned to the next targets:
DEM/input conditioning QA, boundary/termination semantics, output budget
gates, and validation/claim states before distributed execution or larger
ensembles.

Rationale: changing RNG derivation, DEM storage, contact mechanics, dense
reducers, or Balfrin orchestration before acceptance gates are defined would
make behavior drift harder to review. The Tschamut pilot remains conditional,
diagnostic, and non-operational until those gates classify it otherwise.

Detailed sources: `task_backlog.md`,
`roadmap_recommendation_matrix.md`,
`real_case_intensity_frequency_implementation_roadmap.md`.

### Real-Site DEM/Input Conditioning Gate

Decision: treat real-site DEM/input conditioning as a fail-closed QA gate
before larger Swiss public-data pilots are trusted.

Current status: active. DT-07 is complete as the selected QA gate and keeps
the Tschamut pilot classified `blocked_pending_local_evidence`. DT-08 is
complete, DT-09 remains conditional on measured need, DT-10 is complete as a
`blocked_pending_local_evidence` gate, and DT-11 is now the next active target.

Rationale: raw public inputs, intermediate processed artifacts, CRS/
registration, nodata, terrain artifacts, and strict-versus-clamped boundary
interpretation can all create plausible but spatially wrong hazard maps even
when the simulation itself is unchanged.

Detailed sources: `task_backlog.md`,
`real_site_dem_input_conditioning_qa_gate.md`,
`roadmap_recommendation_matrix.md`,
`real_case_intensity_frequency_implementation_roadmap.md`.

### Output Budget And Reducer Scaling Gate

Decision: treat output budgets and reducer scaling as a fail-closed QA gate
before larger selected-domain runs or distributed execution are considered.

Current status: active. DT-08 is complete as the selected QA gate and keeps
the Tschamut pilot classified `blocked_before_scale_up`. DT-09 remains
conditional on measured need, DT-10 is complete as a
`blocked_pending_local_evidence` gate, and DT-11 is now the next active target.

Rationale: validation-side debug output, hazard output volume, reducer restart
state, and dense-grid accumulator growth can make a run look finished while
still being too large or too brittle for the next scale step.

Detailed sources: `task_backlog.md`,
`output_budget_reducer_scaling_gate.md`,
`roadmap_recommendation_matrix.md`,
`real_case_intensity_frequency_implementation_roadmap.md`.

### Contact Model Default

Decision: keep `translational_v0` as the default contact model. Treat
`sphere_rotational_v1` as an opt-in candidate for trajectory/contact
experiments, not as a new default.

Current status: active.

Rationale: Chant Sura comparisons support rotational energy exchange as useful
for trajectory-shape and kinetic-energy metrics, but jump-height and rebound
proxy behavior are not uniformly better and the evidence is not broad enough
for a default change.

Detailed sources: `chant_sura_contact_validation.md`,
`chant_sura_contact_generalization.md`, `model_design.md`,
`validation_plan.md`.

### Public Tschamut Evidence Boundary

Decision: public Tschamut remains diagnostic failure-mode and non-regression
evidence, not physics-selection evidence.

Current status: active.

Rationale: registration sensitivity execution found that broad under-run and
over-run directions were stable, but deposition-overlap class and runout
magnitude varied materially by transform. This blocks using Tschamut alone to
select shape/contact physics.

Detailed sources: `tschamut_public_benchmark_reproduction.md`,
`public_tschamut_all_runs_grouped_validation.md`,
`public_tschamut_failure_mode_analysis.md`,
`tschamut_public_conditional_pilot_gate_report.md`.

### `shape_contact_v0` Runtime Progression

Decision: pause `shape_contact_v0` runtime progression after internal smoke and
Chant Sura model-selection diagnostics.

Current status: active pause.

Rationale: internal plumbing gates passed, but the internal Chant Sura
model-selection result remained failed/uncertain, rebound proxy behavior failed
the frozen non-regression gate, and trajectory-to-EOTA shape provenance remains
unresolved. Public validation and benchmarks remain blocked for
`shape_contact_v0`.

Detailed sources: `shape_contact_v0_experimental_contract.md`,
`shape_contact_v0_internal_validation_progression.md`,
`shape_contact_v0_chant_sura_internal_model_selection.md`,
`shape_contact_v0_rebound_diagnostic_audit.md`.

### Post-Shape Next Scientific Package

Decision: after pausing `shape_contact_v0`, focus on no-tuning stopping and
terrain/material diagnostics before adding new terrain/material parameters or
broader contact machinery.

Current status: active.

Rationale: the current uncertainty is not only contact geometry. Existing
models need clearer evidence on how trajectories lose motion, where final
stopping occurs, and how terrain/material labels relate to last-impact and
final-state behavior.

Detailed sources: `stopping_behavior_diagnostic_report.md`,
`terrain_material_interaction_protocol.md`,
`terrain_material_diagnostic_gap_report.md`,
`terrain_material_interaction_diagnostic_protocol.md`,
`terrain_material_diagnostic_matrix.md`.

### Columnar Output And Hazard Accumulation

Decision: keep CSV/debug outputs for compatibility, but use opt-in columnar
impact/trajectory paths and deterministic reducers as the scaling direction for
large ensembles.

Current status: active direction, implemented only where explicitly documented.

Rationale: synthetic benchmarks showed that file count, impact-event output,
and trajectory/hazard accumulation throughput become bottlenecks before raw
simulation alone. The national hazard-map target needs chunkable, mergeable,
checksum-backed outputs.

Update: validation cases can opt in to deterministic local threaded ensemble
execution with `random.ensemble_workers`. Configured runs preserve the serial
default for all other cases, use the existing per-trajectory seed derivation,
and write `local_parallel_ensemble_v1` `ensemble_execution` provenance into
`run_manifest_v1`. This records local chunk ids, trajectory index ranges,
worker counts, and merge order, but it is not a resumable scheduler,
SLURM/MPI/GPU integration, annual-frequency product, physical probability
model, or operational hazard-map claim.

Detailed sources: `scalability_and_data_formats_review.md`,
`performance_benchmarking.md`, `performance_benchmark_profile_reference.md`,
`parquet_impact_benchmark_results.md`,
`hazard_throughput_bottleneck_report.md`.

### Deterministic Chunk Execution Plans

Decision: implement deterministic per-chunk reducer execution contracts that support
local restart/retry, ownership claims, and merge-sidecar bookkeeping so partial
completion and failure states are recoverable without changing physics or defaults.

Current status: active and implemented for hazard-layer runs using
`--reducer-workers N` with `N > 1`; each run now writes `execution_plan_v1`,
`reducer_execution_index_v1`, `reducer_merge_state_v1`, and
`chunk_execution_manifest_v1`/`hazard_reducer_chunk_manifest_v1`-style state
with deterministic chunk ids, input index provenance, retry/attempt counters,
scheduler ownership metadata, and manifest output accounting.

Rationale: large Swiss-scale pre-pilots require stable partial-reducer provenance
before introducing job arrays or scheduler-level restart logic.

Detailed sources: `docs/validation_data_schema.md`,
`docs/scalability_and_data_formats_review.md`,
`docs/real_case_intensity_frequency_implementation_roadmap.md`,
`scripts/build_hazard_layers.py`.

### Expert Review Baseline

Decision: the expert-review baseline was a historical review checkpoint, not an
operational or version-governing release.

Current status: superseded by the current Swiss hazard-map prioritization.

Rationale: the baseline reports remain useful as evidence snapshots, but the
current target is no longer to package a static review state. New work should
optimize for the public-dataset Swiss pilot and later physical/annual
intensity-frequency products.

Detailed sources: `model_benchmark_execution_report.md`,
`model_overall_assessment_report.md`, `expert_review_briefing.md`,
`benchmark_catalog.md`.

## Superseded Standalone Sources

The following standalone files were consolidated or removed because they had
become stale, overly detailed for onboarding, or duplicative with current
roadmaps and evidence reports:

- `contact_model_decision.md`
- `public_tschamut_model_improvement_decision.md`
- `post_shape_contact_v0_pause_next_step.md`
- `columnar_output_design_decision.md`
- `trajectory_parquet_next_step_decision.md`
- `hazard_accumulation_architecture_decision.md`
- `post_ramms_gap_next_work_packages.md`
- `post_ce3959d_next_step_decision.md`
- `post_swiss_pilot_stack_next_step_decision.md`
- `v0_5_next_steps_review.md`
- `expert_review_release_note.md`
- `current_state_gap_analysis_next_directions.md`
- `repository_scientific_roadmap_review.md`
- `deep_code_review.md`
- `deep_repository_review.md`

When a detailed result is needed, regenerate or re-read the current benchmark,
validation, roadmap, and schema documents rather than relying on removed
historical snapshots.
