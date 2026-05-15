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
   Balfrin target-gate reproduction exists and the convergence CLI can compare
   both manifest summaries and cell-wise fixture grids, but normal hazard
   manifests do not yet expose the cell-wise layer paths needed for selected
   pilot evidence.
2. Validation-output volume remains a practical blocker. The bounded-profile
   summary now preserves `no_go` semantics and can audit output families when
   local manifests exist, but it did not reduce the retained validation debug
   artifacts.
3. Forest and obstacle context is unresolved. The inspection command now
   exposes expected layers, provenance fields, and acquisition checklists, but
   the current checkout still lacks processed local public context crops and no
   spatial overlap/relevance measurement has been made.
4. Scaling direction is now better bounded. The single-job Balfrin path is
   sufficient for the next same-scale conditional pilot step; distributed
   execution should stay deferred until a new measurement shows a need.
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
  conditional exceedance summaries across actual selected-pilot outputs;
- measured validation-debug output reduction, not just output-family audits;
- obstacle/context cache staging and spatial overlap analysis;
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

### TB-010: Implement A Reduced Validation Debug Output Mode

Capability gap reduced: validation-output pressure remains the measured
scale-up blocker.

Goal: add an opt-in validation output mode that suppresses, samples, or
summarizes nonessential debug artifacts for selected pilot runs, then measure
before/after file count, bytes, and retained provenance on a tiny fixture or
available selected-pilot output.

Inspect first:

- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `scripts/summarize_bounded_validation_output_profile.py`;
- `tests/test_bounded_validation_output_profile.py`;
- validation output-writing code;
- validation manifest/output tests.

Required work:

1. Do not change public validation defaults or baselines.
2. Keep the mode opt-in and explicit in provenance.
3. Preserve required metrics, manifests, checksums, and scientific review
   evidence.
4. Measure file/byte/inode reduction or prove the specific output class cannot
   yet be reduced safely.
5. Do not authorize scale-up from this task alone.

Definition of done:

- a focused command or test demonstrates reduced validation output on a tiny
  fixture or selected-pilot path;
- before/after output accounting is recorded;
- public defaults remain unchanged;
- checks pass.

### TB-011: Stage Tschamut Context Crops And Measure Spatial Relevance

Capability gap reduced: forest and obstacle context is still blocked by
missing local evidence and no overlap/relevance measurement.

Goal: acquire, stage, or verify minimal public context crops for the selected
Tschamut extent and use the existing inspector to measure whether forest,
buildings, roads, channels, barriers, or visual context intersect or materially
limit the interpreted hazard corridor.

Inspect first:

- `scripts/inspect_tschamut_public_context_layers.py`;
- `docs/tschamut_public_obstacle_context_scope.md`;
- `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`;
- `docs/swisstopo_data_strategy.md`;
- `docs/public_real_site_geodata_preparation.md`.

Required work:

1. Do not infer obstacle absence from missing data.
2. Keep raw geodata and large processed crops out of git.
3. Record cache paths, checksums, CRS/provenance, and spatial relevance.
4. If data remain unavailable, produce the exact acquisition command or
   Balfrin/local staging step needed next.
5. Do not implement obstacle physics or tune terrain/contact/stopping
   parameters.

Definition of done:

- the context review is based on actual local context evidence or an exact
  executable acquisition path;
- overlap/relevance is classified conservatively;
- no operational or obstacle-performance claim is added;
- focused checks pass.

### TB-012: Apply Current Diagnostics To A Same-Scale Conditional Pilot Review

Capability gap reduced: the repo has separate diagnostics, but no integrated
same-scale review that uses cell-wise convergence, validation-output, context,
and single-job evidence together.

Goal: run or generate a single reproducible same-scale pilot review that
combines the outputs of TB-009 through TB-011 with existing acceptance records
and states whether the Tschamut conditional pilot is still `no_go`,
`inconclusive`, or accepted as a non-operational diagnostic.

Inspect first:

- `docs/tschamut_public_conditional_pilot_acceptance_summary.md`;
- `scripts/summarize_conditional_pilot_acceptance.py`;
- `docs/balfrin_single_job_execution_sufficiency.md`;
- outputs from TB-009 through TB-011 when available.

Required work:

1. Prefer composing existing executable diagnostics over writing another
   one-off YAML reader.
2. Do not run larger ensembles or change thresholds.
3. Preserve conditional, non-operational semantics.
4. Make missing diagnostic inputs explicit rather than silently passing.

Definition of done:

- the review consumes actual diagnostic outputs or reports exact missing
  inputs;
- final classification and blockers are explicit;
- uncertainty reduced and remaining blockers are stated quantitatively where
  possible;
- checks pass.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- production COG or QGIS packaging work beyond secondary QA;
- manual GIS/QGIS visual QA unless the local package artifacts and QGIS are
  actually available and the main acceptance evidence is not blocked elsewhere;
- distributed SLURM orchestration unless later evidence shows a measured need.
- shared typed evidence-reader refactors unless at least one more executable
  diagnostic exposes duplicated parsing as the implementation bottleneck.
