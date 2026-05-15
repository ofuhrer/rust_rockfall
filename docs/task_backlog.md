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
   Balfrin target-gate reproduction exists and the reusable convergence CLI can
   compare manifest summaries, but there is not yet cell-wise spatial
   convergence evidence for conditional hazard layers.
2. Validation-output volume remains a practical blocker. The bounded-profile
   summary split hazard-side and validation-side output pressure, but it did
   not reduce validation debug artifacts; larger selected-domain runs are not
   credible until that output is reduced or justified by measured evidence.
3. Forest and obstacle context is unresolved. A reusable inspection command now
   exists, but the current checkout still lacks the processed local public
   context cache; without reviewed context layers, the Tschamut map remains
   hard to interpret physically.
4. Scaling direction is underdetermined. Single-job Balfrin execution may be
   enough for the next conditional pilot step, or it may need distributed
   execution; this should be decided after spatial convergence and
   validation-output blockers are better measured.
5. Evidence tooling is becoming useful but remains ad hoc. Current summary
   scripts are valuable guardrails, but more one-off record readers would add
   process weight unless they generate new measurements or reusable analysis.
6. Source-zone and block-scenario evidence is still pragmatic and
   inventory-conditioned. This is acceptable for the first pilot only if the
   interpretation explicitly stays conditional and non-operational.
7. Physical/annual frequency semantics are absent. This is not a near-term
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

- cell-wise convergence/statistics tooling for comparing hazard rasters and
  conditional exceedance summaries across runs;
- measured validation-debug output reduction, not just output-pressure
  summaries;
- obstacle/context evidence acquisition and spatial overlap analysis;
- resource and runtime profiling that decides whether single-job Balfrin
  execution is enough after the current scientific blockers are reduced;
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

### TB-007: Acquire And Inspect Tschamut Public Context Cache

Capability gap reduced: forest and obstacle context is blocked by missing
local public-context evidence.

Goal: use the existing context-layer inspection command to acquire, stage, or
verify the processed public context cache for Tschamut, then classify forest,
building, transport, barrier, channel, and visual context using actual local
evidence where available.

Inspect first:

- `scripts/inspect_tschamut_public_context_layers.py`;
- `docs/tschamut_public_obstacle_context_scope.md`;
- `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`;
- `docs/swisstopo_data_strategy.md`;
- `docs/public_real_site_geodata_preparation.md`.

Required work:

1. Do not infer obstacle absence from missing data.
2. Keep raw geodata out of git.
3. If public products are locally available, record path patterns, checksums,
   CRS/provenance, and spatial relevance to the selected Tschamut extent.
4. If products are unavailable, produce the exact cache/acquisition commands
   needed next and keep the classification blocked.
5. Do not implement obstacle physics or tune terrain/contact/stopping
   parameters.

Definition of done:

- the inspection result is based on actual local context evidence or an exact
  executable acquisition path;
- interpretation is classified conservatively;
- no operational or obstacle-performance claim is added;
- focused checks pass.

### TB-008: Measure Whether Single-Job Balfrin Execution Is Still Enough

Capability gap reduced: scaling direction is underdetermined.

Goal: use existing Balfrin and reducer evidence, or one small non-public probe
if needed, to decide whether distributed execution design is currently needed
or should remain deferred.

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
3. Account for TB-005/TB-006 results before treating distributed execution as
   the next bottleneck.
4. Classify distributed execution as `defer`, `design_needed`, or
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
- distributed SLURM orchestration unless TB-008 or later evidence shows a
  measured need.
- shared typed evidence-reader refactors unless at least one more executable
  diagnostic exposes duplicated parsing as the implementation bottleneck.
