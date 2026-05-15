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
   manifests when raster files exist. In this checkout, the selected Tschamut
   hazard artifacts are still missing, so applied cell-wise pilot evidence is
   blocked on regenerating or restoring ignored outputs.
2. Validation-output volume remains a practical blocker. The bounded-profile
   summary now preserves `no_go` semantics, can audit output families when
   local manifests exist, and an opt-in `summary_only` validation mode reduces
   debug outputs on fixtures. The real selected-pilot reduced-output evidence
   still needs to be generated or restored.
3. Forest and obstacle context is unresolved. The inspection command now
   exposes expected layers, provenance fields, acquisition checklists, selected
   corridor metadata, and fixture spatial-relevance measurements. The current
   checkout still lacks processed local public context crops, so real context
   relevance remains blocked pending local evidence.
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
- selected-pilot artifact refresh using the current cell-wise hazard and
  reduced validation-output modes;
- measured validation-debug output reduction on the real selected-pilot path,
  not just fixtures;
- obstacle/context crop staging and real spatial overlap analysis;
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

### TB-012: Refresh Same-Scale Selected Tschamut Pilot Artifacts

Capability gap reduced: the new diagnostics cannot produce selected-pilot
evidence until the ignored same-scale validation and hazard artifacts are
regenerated or restored with current output contracts.

Goal: run or stage the same-scale selected Tschamut conditional pilot artifacts
needed by the current diagnostics, without increasing ensemble size or
changing physics. The refreshed artifacts should use the current
`summary_only` validation output mode where applicable and hazard manifests
that expose cell-wise layer paths.

Inspect first:

- `docs/balfrin_tschamut_pilot_runbook.md`;
- `docs/balfrin_single_job_execution_sufficiency.md`;
- `docs/tschamut_public_conditional_pilot_acceptance_summary.md`;
- `docs/conditional_hazard_convergence_acceptance_protocol.md`;
- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `scripts/compare_hazard_map_convergence.py`;
- `scripts/summarize_bounded_validation_output_profile.py`;
- selected private/ignored Tschamut case paths if available locally.

Required work:

1. Do not run a larger ensemble, tune thresholds, change release assumptions,
   or refresh public baselines.
2. Keep all generated validation and hazard outputs under ignored paths.
3. If local/Balfrin inputs are present, run the same-scale selected workflow
   and record the commands, artifact paths, checksums, file/byte counts,
   validation output mode, and hazard `cellwise_layers` availability.
4. Run the cell-wise convergence diagnostic on the refreshed hazard artifacts
   when both comparison manifests are present.
5. Run the bounded-output summary against refreshed validation manifests when
   available.
6. If required private/ignored inputs are missing, produce the exact command
   sequence and path checklist needed on Balfrin or the local machine; do not
   silently reclassify missing inputs as success.
7. Preserve conditional, non-operational semantics.

Definition of done:

- selected-pilot artifact availability is converted from vague missing state
  into either refreshed ignored outputs with measured diagnostics or exact
  executable commands and required paths;
- generated outputs are not committed;
- checks pass.

### TB-013: Stage Tschamut Context Crops And Measure Real Spatial Relevance

Capability gap reduced: forest and obstacle context remains blocked by missing
real public context crops.

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
- outputs from TB-012 and TB-013 when available.

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
