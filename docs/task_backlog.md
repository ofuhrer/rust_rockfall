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
   manifest summaries, cell-wise fixture grids, and normal hazard-output
   manifests when raster files exist. The same-scale local gate has now been
   regenerated under ignored paths and passes a cell-wise self-check, but
   target-vs-gate spatial convergence still needs the matching target artifacts
   or a fresh same-scale comparison run.
2. Validation-output volume remains a practical blocker for target-scale
   growth, but the local same-scale gate now has measured before/after
   evidence: full debug validation output was `125` files / `34545900` bytes,
   while the opt-in `summary_only` probe was `4` files / `81425` bytes.
3. Forest and obstacle context is limiting and partly unresolved. The
   inspection command now has real local public context evidence for
   swissSURFACE3D Raster, SWISSIMAGE, and swissBUILDINGS3D, with surface-height
   relevance indicators. swissTLM3D road, channel, and barrier categories
   remain unresolved pending a targeted crop or feature-service extraction.
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
- target-vs-gate or split-half convergence using the refreshed same-scale
  hazard-output contract;
- measured validation-debug output reduction on target-scale or repeated
  same-scale pilot paths;
- targeted swisTLM3D extraction for roads, channels, and barrier/protection
  context;
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

### TB-014: Apply Current Diagnostics To A Same-Scale Conditional Pilot Review

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
- refreshed ignored outputs documented in
  `docs/tschamut_public_conditional_pilot_gate_report.md`;
- local context evidence documented in
  `docs/tschamut_public_obstacle_context_scope.md`.

Required work:

1. Prefer composing existing executable diagnostics over writing another
   one-off YAML reader.
2. Do not run larger ensembles or change thresholds.
3. Preserve conditional, non-operational semantics.
4. Make missing diagnostic inputs explicit rather than silently passing.
5. Treat the current same-scale cell-wise self-check as plumbing evidence only;
   do not convert it into target-vs-gate convergence acceptance.
6. Include the measured `summary_only` validation-output reduction and the
   limiting/unresolved context classification in the review.

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
