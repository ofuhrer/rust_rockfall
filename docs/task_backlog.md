# Task Backlog

Status: authoritative executable task backlog.

This file is the only maintained queue of implementation tasks. It is written
for worker agents, including smaller GPT-5.4-Mini-style agents, so each task
must be small enough for focused execution and must name the concrete
capability, analysis, run, or validation outcome it enables.

Worker rule: when a task is completed successfully and committed, remove that
task from this backlog. Add at most one follow-up task if the completed work
uncovers a concrete next blocker. Record durable choices in `decision_log.md`
and completed work in `agent_work_log.md`.

Progress rule: backlog tasks must normally produce executable or measured
progress, not only procedural artifacts. Acceptable real progress includes an
implemented simulator or workflow feature, an executable analysis script, a
validation run with measured results, a comparison against reference or field
data, a reproducibility improvement that enables validation, a performance
improvement that enables larger validation, or a tested bug fix.

Non-sufficient outputs by themselves: documentation-only gates, YAML
record-only changes, validator-only changes, roadmap-status transitions,
consistency-hook extensions, or reclassification of existing evidence without
new analysis. These may support a task, but they are not the deliverable unless
the user explicitly asks for a planning-only change.

## Project Objective

The repository is trying to become an automated, reproducible rockfall
hazard-map workflow for Switzerland's Alpine terrain using public geodata,
primarily swisstopo. The first concrete milestone is a valley-scale Tschamut
pilot that produces conditional grid-cell intensity-exceedance hazard-map
products with documented uncertainty, provenance, performance, and
non-operational interpretation limits.

Medium-term objectives are to make the conditional pilot scientifically
interpretable, reproducible on Balfrin/CSCS-style infrastructure, and scalable
toward larger release-zone ensembles. True physical or annual
intensity-frequency products remain deferred until source occurrence rates,
block-population frequencies, uncertainty propagation, and validation or
calibration evidence exist.

The selected Tschamut target-scale evidence remains `inconclusive`. Larger
selected-domain runs remain blocked until the capability gaps below are reduced
with measured evidence.

Non-goals for current backlog work: operational warning systems, regulatory
approval, risk/exposure/vulnerability modelling, annual return-period claims,
parameter tuning to fit the pilot, and new contact/terrain physics unless a
separate falsifiable implementation task is explicitly authorized.

## Capability Gap Analysis

The most important gaps between the current repository and the project
objective are:

1. Conditional pilot evidence is still inconclusive. The 1,000-trajectory
   Balfrin target-gate reproduction exists, but convergence and output-budget
   evidence have not been converted into an accepted conditional-pilot
   scientific result.
2. Validation-output volume remains a practical blocker. Larger selected-domain
   runs are not credible until debug/validation outputs are bounded or
   justified by a measured output profile.
3. Forest and obstacle context is unresolved. Public context products are
   identified, but local evidence is missing; without it, the Tschamut map can
   remain visually plausible but physically hard to interpret.
4. Scaling direction is underdetermined. Single-job Balfrin execution may be
   enough for the next conditional pilot step, or it may need distributed
   execution; this should be decided from measured wall-time, memory, output,
   and restartability evidence.
5. Source-zone and block-scenario evidence is still pragmatic and
   inventory-conditioned. This is acceptable for the first pilot only if the
   interpretation explicitly stays conditional and non-operational.
6. Physical/annual frequency semantics are absent. This is not a near-term
   implementation gap unless the conditional pilot first reaches accepted
   diagnostic status.

## Backlog Quality Assessment

The current backlog should be judged by whether it creates new measurements,
analysis capabilities, reproducibility, or execution capacity. The strongest
tasks are those that turn the existing Tschamut/Balfrin artifacts into
actionable scientific evidence or remove a measured execution blocker.

Over-procedural areas to avoid:

- repeated reclassification of the same `inconclusive` evidence without a new
  analysis or run;
- additional YAML records or validators that do not enable execution,
  measurement, or reproducibility;
- roadmap/status maintenance that does not change what a worker can run or
  learn;
- secondary GIS/QGIS bookkeeping when the main conditional hazard-map evidence
  remains unresolved.

Underrepresented high-value work:

- reusable convergence/statistics tooling for comparing hazard rasters and
  conditional exceedance summaries across runs;
- measured validation-output profile reduction;
- obstacle/context evidence acquisition and overlap analysis;
- resource and runtime profiling that decides whether single-job Balfrin
  execution is enough;
- uncertainty summaries that quantify what changes with sampling, chunking, or
  output profile choices.

## Backlog Protocol

Each active task must include:

- scope small enough for one focused worker turn;
- explicit files, data records, or commands to inspect first;
- the concrete implementation, run, analysis, or validation outcome it enables;
- no-physics/no-tuning/no-operational-claim boundaries when relevant;
- exact outputs expected;
- focused checks to run.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history and `decision_log.md` for durable decisions.

## Active Tasks

### TB-002: Build Reusable Hazard-Map Convergence Diagnostics

Capability gap reduced: conditional-pilot acceptance lacks quantitative
convergence/statistical tooling.

Goal: implement or extend an executable diagnostic script that compares two or
more hazard-map runs or summaries and reports quantitative convergence
indicators for conditional intensity-exceedance products.

Inspect first:

- `scripts/build_hazard_layers.py`;
- existing hazard manifests under ignored `hazard/results/` when available;
- `docs/conditional_hazard_convergence_acceptance_protocol.md`;
- `docs/hazard_map_semantics.md`;
- existing tests around hazard-layer reducers and conditional curves.

Required work:

1. Prefer a reusable script or test fixture over a one-off manual comparison.
2. Compare stable products such as threshold exceedance summaries, reach,
   deposition density, maximum kinetic energy, maximum jump height, output
   checksums, or selected raster statistics where available.
3. Make missing local ignored outputs an explicit blocked/input state rather
   than a failure to import or a silent pass.
4. Do not tune thresholds, change hazard semantics, or alter baselines.

Definition of done:

- the diagnostic can run on a tiny fixture or existing selected-pilot outputs;
- it reports concrete metrics, not just pass/fail labels;
- tests cover at least one deterministic fixture or dry-run path;
- output is suitable input for TB-001 acceptance summary.

### TB-003: Implement A Bounded Validation Output Profile For Pilot Runs

Capability gap reduced: validation-output volume blocks larger selected-domain
execution.

Goal: add or exercise a concrete validation-output profile that bounds
debug/output volume for selected pilot runs while preserving enough provenance
for scientific review.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`;
- `docs/tschamut_public_pilot_scaling_review.md`;
- `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`;
- `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`;
- validation output-writing code and existing output-profile controls.

Required work:

1. Measure or derive the current validation output file/byte/inode pressure.
2. Implement or dry-run a bounded output profile only if it can be done without
   changing defaults silently.
3. Keep generated outputs ignored.
4. Do not authorize scale-up unless output limits are explicitly accepted.

Definition of done:

- executable code, script, or command path demonstrates the bounded output
  profile or proves why it is still blocked;
- measured file/byte/inode evidence is recorded;
- public defaults and validation baselines are unchanged;
- focused tests/checks pass.

### TB-004: Acquire Or Verify Public Context-Layer Evidence For Tschamut

Capability gap reduced: forest and obstacle context is unresolved.

Goal: use public context products, where locally available, to determine
whether omitted forest, buildings, roads, barriers, nets, or other obstacles
are acceptable, limiting, invalidating, or still blocked for the selected
Tschamut conditional hazard-map interpretation.

Inspect first:

- `docs/tschamut_public_obstacle_context_scope.md`;
- `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`;
- `docs/swisstopo_data_strategy.md`;
- `docs/public_real_site_geodata_preparation.md`.

Required work:

1. If public context layers are locally available, record paths, checksums,
   CRS/provenance, and a concise spatial relevance assessment.
2. If public context layers are missing, produce the exact fetch/cache commands
   or local acquisition checklist needed next.
3. Do not infer obstacle absence from missing data.
4. Do not implement obstacle physics or tune terrain/contact/stopping
   parameters.
5. Keep raw geodata out of git.

Definition of done:

- the obstacle-context status is based on inspected data or an executable
  acquisition path, not only a policy statement;
- interpretation classification is explicit;
- no operational claim is added;
- focused checks pass.

### TB-005: Measure Whether Single-Job Balfrin Execution Is Still Enough

Capability gap reduced: scaling direction is underdetermined.

Goal: use existing Balfrin and reducer evidence, or one small non-public probe
if needed, to decide whether DT-09 distributed execution design is currently
needed or should remain deferred.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`;
- `docs/balfrin_probe_slurm_driver.md`;
- `docs/balfrin_tschamut_readiness.md`;
- `validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`;
- `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`.

Required work:

1. Do not add SLURM arrays, MPI, GPU, or distributed reducers.
2. Summarize measured wall time, memory, output size, restartability, and
   reducer-state evidence.
3. Classify distributed execution as `defer`, `design_needed`, or
   `blocked_pending_evidence`.

Definition of done:

- decision is based on measured execution/resource evidence;
- any durable decision is recorded in `decision_log.md`;
- no runtime behavior changes unless explicitly required for measurement;
- consistency checks pass.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- production COG or QGIS packaging work beyond secondary QA;
- manual GIS/QGIS visual QA unless the local package artifacts and QGIS are
  actually available and the main acceptance evidence is not blocked elsewhere;
- distributed SLURM orchestration unless TB-005 or later evidence shows a
  measured need.
