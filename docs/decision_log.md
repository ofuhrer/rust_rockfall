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

### Backlog Tied To Capability Gaps

Decision: backlog changes must be justified by concrete capability-gap
reduction, not by procedural completeness.

Current status: active. The backlog should name the project objective,
important unresolved gaps, and the capability or evidence each active task
improves. Procedural tasks are proportional only when they enable executable
analysis, validation, implementation, reproducibility, or scaling work.

Rationale: the project objective is a reproducible Swiss public-data hazard-map
workflow. Backlog drift toward policy-only gate completion slows progress
unless each task is anchored to a missing capability, missing evidence, or
measured blocker.

Detailed sources: `task_backlog.md`, `../AGENTS.md`.

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

### Balfrin Single-Job Sufficiency

Decision: keep distributed Balfrin execution deferred. The current single-job SLURM path remains sufficient.

Current status: active. The measured single-job evidence is enough for the
next conditional pilot step, but not enough to authorize distributed
execution design or scaling on its own, so distributed execution deferred
remains the current stance.

Rationale: the tracked repeatability record shows stable plan IDs, stable
reused completed state, and hash-stable hazard artifacts; the target-gate
reproduction completed within the single-job boundary with deterministic
chunking; and the output-budget/reducer gate still keeps distributed execution
unauthorized while validation debug output and convergence blockers remain the
dominant concerns.

Detailed sources: `docs/balfrin_probe_slurm_driver.md`,
`validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`,
`validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`,
`validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`,
`validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`,
`docs/balfrin_single_job_execution_sufficiency.md`.

### Post-TB-013 Backlog Reprioritization

Decision: after the same-scale gate regeneration, bounded-output measurement,
and staged public-context evidence became available, prioritize measured
target-vs-gate spatial convergence first, corridor-level context relevance
second, and reusable uncertainty-envelope synthesis after those measurements.

Current status: active.

Rationale: the primary remaining scientific uncertainty is whether the actual
target and gate hazard cells remain spatially stable on the refreshed
same-scale artifacts. The context cache is no longer absent; it is a limiting
interpretation input that now needs corridor-level quantification for roads,
barriers, and water. The next highest-value work is measured comparison,
context relevance measurement, and then reusable uncertainty synthesis, not
more status reclassification.

Detailed sources: `task_backlog.md`,
`tschamut_public_conditional_pilot_gate_report.md`,
`tschamut_public_bounded_validation_output_profile.md`,
`tschamut_public_obstacle_context_scope.md`,
`balfrin_single_job_execution_sufficiency.md`.

### Same-Scale Target-Vs-Gate Convergence Measured Inconclusive

Decision: treat the same-scale target-vs-gate comparison as restored and
measured, but not accepted. The next backlog work should diagnose the measured
disagreement, broaden context-overlap and uncertainty evidence, and harden
reproducible case regeneration instead of continuing to treat missing target
artifacts as the dominant blocker.

Current status: active.

Rationale: the target-side same-scale artifact chain has been regenerated
locally under ignored paths, and the comparison command now completes with
`status: ok` across 22 shared cell-wise layers. The measured differences are
still too large for acceptance, including `cellwise_linf_abs_diff_max =
3028.22579673`, `cellwise_l1_abs_diff_sum = 190790.42488112117`, and
`cellwise_nonzero_jaccard_min = 0.1`. The result is useful scientific
evidence, not operational convergence or scale-up authorization.

Detailed sources: `task_backlog.md`,
`tschamut_public_conditional_pilot_gate_report.md`,
`tschamut_public_same_scale_uncertainty_envelope.md`,
`tschamut_public_bounded_validation_output_profile.md`,
`tschamut_public_obstacle_context_scope.md`,
`conditional_hazard_convergence_acceptance_protocol.md`,
`balfrin_single_job_execution_sufficiency.md`.

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

### Post TB-001 Through TB-004 Backlog Direction

Decision: prioritize cell-wise hazard-map convergence diagnostics and measured
validation-output reduction before distributed Balfrin execution design.

Current status: active backlog direction.

Rationale: TB-001 through TB-004 improved auditability, reusable comparison
tooling, output-pressure measurement, and public-context inspection, but the
selected Tschamut pilot remains inconclusive. The strongest remaining
scientific uncertainty is spatial hazard-map stability; the strongest measured
execution blocker is validation debug-output volume. A distributed SLURM design
would be premature until those blockers are reduced or shown to be secondary.

Detailed sources: `docs/task_backlog.md`,
`docs/tschamut_public_conditional_pilot_acceptance_summary.md`,
`docs/conditional_hazard_convergence_acceptance_protocol.md`,
`docs/tschamut_public_bounded_validation_output_profile.md`,
`docs/tschamut_public_obstacle_context_scope.md`.

### Post TB-008 Backlog Direction

Decision: keep single-job Balfrin execution as the current execution boundary
and prioritize applied pilot evidence: wire cell-wise convergence to emitted
hazard outputs, reduce validation debug output, and stage context crops before
any distributed execution design.

Current status: active backlog direction.

Rationale: TB-005 through TB-008 added real diagnostic capabilities and bounded
the execution architecture question. The remaining blockers are not primarily
SLURM orchestration; they are whether selected-pilot hazard rasters are
spatially stable, whether validation debug output can be reduced, and whether
public forest/obstacle context materially limits interpretation.

Detailed sources: `docs/task_backlog.md`,
`scripts/compare_hazard_map_convergence.py`,
`docs/tschamut_public_bounded_validation_output_profile.md`,
`docs/tschamut_public_obstacle_context_scope.md`,
`docs/balfrin_single_job_execution_sufficiency.md`.

### Post TB-011 Backlog Direction

Decision: prioritize refreshing the same-scale selected Tschamut artifacts
under the current diagnostic contracts before running another integrated
acceptance review.

Current status: active backlog direction.

Rationale: TB-009 through TB-011 added the right executable plumbing: hazard
manifests can expose cell-wise layer paths, validation can opt into
`summary_only` output, and context inspection can report selected-corridor
spatial relevance. The current checkout still lacks the ignored selected-pilot
hazard/validation artifacts and real processed context crops, so the next
capability gain is to regenerate or restore those artifacts and run the
diagnostics on them, not to add another synthesis over missing inputs.

Detailed sources: `docs/task_backlog.md`,
`docs/conditional_hazard_convergence_acceptance_protocol.md`,
`docs/tschamut_public_bounded_validation_output_profile.md`,
`docs/tschamut_public_obstacle_context_scope.md`.

### Post TB-015 Corridor Context Measurement

Decision: treat the staged swissTLM3D archive as measured corridor-level
context evidence, not as missing-cache evidence, and keep the interpretation
boundary conditional and non-operational.

Current status: active backlog direction.

Rationale: TB-015 converted the archive from "staged" to a measurable
corridor-level context signal. Roads, barriers, and water are now quantified
against the selected Tschamut extent, and the result remains limiting rather
than acceptable. The next highest-value work is still the target-vs-gate
spatial comparison on the refreshed same-scale hazard artifacts, because that
gap remains the dominant scientific uncertainty.

Detailed sources: `docs/task_backlog.md`,
`scripts/inspect_tschamut_public_context_layers.py`,
`docs/tschamut_public_obstacle_context_scope.md`,
`docs/tschamut_public_conditional_pilot_gate_report.md`.

### Post TB-027 Backlog Direction

Decision: refill the active backlog around concrete second-site portability,
bounded same-scale uncertainty reduction, command-plan consolidation, GIS
package readiness, and reducer/runtime measurements.

Current status: active backlog direction.

Rationale: TB-018 through TB-027 changed the dominant blockers. The same-scale
Tschamut artifact chain is ready and reproducible, target-vs-gate convergence
is measured but still inconclusive, output reduction is measured, public
context is limiting rather than absent, hazard-context overlap is measured but
unresolved, case regeneration is deterministic, and second-site portability is
now represented by a metadata-only preflight. The next capability gains should
turn that generic portability preflight into a concrete candidate-site
manifest, quantify sampling uncertainty with bounded replicates, consolidate
local command plans, and measure GIS/scaling readiness before any larger or
second-site run.

Detailed sources: `docs/task_backlog.md`,
`docs/tschamut_public_conditional_pilot_gate_report.md`,
`docs/tschamut_public_same_scale_uncertainty_envelope.md`,
`docs/tschamut_public_bounded_validation_output_profile.md`,
`docs/tschamut_public_obstacle_context_scope.md`,
`scripts/check_second_site_public_geodata_preflight.py`,
`scripts/generate_tschamut_same_scale_cases.py`,
`scripts/check_same_scale_artifact_readiness.py`.

### Post TB-028/TB-029 External Backlog Reassessment

Decision: prioritize the multi-site source-zone and scenario contract audit
before additional Tschamut sampling probes, then proceed to a multi-seed
same-scale uncertainty envelope, portable command plans, GIS/COG readiness,
and bounded reducer/runtime measurements.

Current status: active backlog direction.

Rationale: the external assessment correctly identified that the dominant
remaining work has shifted from raw Tschamut execution toward scientific
uncertainty characterization and Swiss-wide portability. The concrete
second-site manifest direction has already been advanced by the staged Chant
Sura / Flüelapass candidate, so the next bottleneck is not another generic
manifest but the portable source-zone/block-scenario contract needed to make
that candidate actionable. Multi-seed uncertainty remains high priority, but
it should follow the source/scenario contract audit so the Swiss-wide path is
not delayed by more Tschamut-specific stabilization.

Detailed sources: `docs/task_backlog.md`,
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`,
`scripts/check_second_site_public_geodata_preflight.py`,
`scripts/generate_tschamut_same_scale_cases.py`,
`docs/tschamut_public_same_scale_uncertainty_envelope.md`,
`docs/public_real_site_geodata_preparation.md`,
`docs/swisstopo_data_strategy.md`.

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
