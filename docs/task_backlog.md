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
   manifests when raster files exist. Same-scale local gate artifacts and real
   public context evidence now exist, but target-vs-gate spatial convergence on
   the refreshed same-scale outputs is still blocked until the target-side
   same-scale input bundle, validation manifest, hazard manifest, and grid
   files are restored or regenerated in the current checkout.
2. Validation-output volume remains a practical blocker for target-scale
   growth, but the same-scale gate now has measured before/after evidence:
   full debug validation output was `125` files / `34545900` bytes, while the
   opt-in `summary_only` probe was `4` files / `81425` bytes. The blocker is
   now measured rather than speculative.
3. Forest and obstacle context is no longer an absent-cache problem; it is a
   corridor-relevance problem. The inspector now has real local public
   context evidence for swissSURFACE3D Raster, SWISSIMAGE, swissBUILDINGS3D,
   and a staged swissTLM3D archive that has now been queried at corridor
   level. Roads, barriers, and water are measured as limiting context rather
   than missing-cache evidence, but the same-scale interpretation remains
   conditional because context is still not obstacle physics.
4. Scaling direction is now better bounded. The single-job Balfrin path is
   sufficient for the next same-scale conditional pilot step; distributed
   execution should stay deferred until a new measurement shows a need.
5. Evidence tooling is becoming useful but remains ad hoc. Current summary
   scripts are valuable guardrails, but more one-off record readers would add
   process weight unless they generate new measurements or reusable analysis.
6. Local ignored-artifact readiness is now a workflow bottleneck. Several tasks
   have found exact missing paths after long audits; the repo needs a reusable
   preflight once the current target-side restoration blocker is resolved or
   repeated.
7. Source-zone and block-scenario evidence is still pragmatic and
   inventory-conditioned. This is acceptable for the first pilot only if the
   interpretation explicitly stays conditional and non-operational.
8. Physical/annual frequency semantics are absent. This is not a near-term
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

- restoring or regenerating the target-side same-scale input and hazard
  artifact chain;
- target-vs-gate spatial convergence on restored same-scale hazard outputs;
- target-side `summary_only` validation-output measurement;
- overlap between limiting corridor context and high-relevance hazard cells;
- a reusable same-scale uncertainty envelope that composes the measured
  convergence, output budget, context, and execution-sufficiency evidence;
- reusable readiness/preflight tooling for future selected-pilot artifact
  refreshes;
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

### TB-020: Measure Target-Side Summary-Only Validation Output Profile

Capability gap reduced: `summary_only` validation output has been measured on
the same-scale gate path, but target-side output pressure remains unmeasured.

Goal: run or audit the target-side validation path with the opt-in
`outputs.validation_output_mode: summary_only` profile and compare file/byte
counts against the target full-debug or recorded target output profile.

Inspect first:

- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `scripts/summarize_bounded_validation_output_profile.py`;
- target-side validation manifests under ignored paths, if present locally.

Required work:

1. Do not change public defaults or baselines.
2. Preserve required metrics, manifests, checksums, and provenance.
3. Report baseline and reduced file counts, bytes, omitted output classes, and
   retained provenance for the target-side path.
4. If target artifacts remain absent, record exact missing inputs and commands.

Definition of done:

- target-side validation-output reduction is measured or explicitly blocked;
- scale-up remains unauthorized;
- checks pass.

### TB-021: Measure Hazard-Context Overlap For Limiting Corridor Features

Capability gap reduced: TB-015 measured roads, barriers, and water as limiting
context, but the repo has not quantified whether those limiting features
overlap or neighbor the highest-relevance hazard cells.

Goal: combine existing hazard rasters and the measured swissTLM3D corridor
feature summaries to quantify overlap or proximity between high-relevance
conditional hazard cells and roads, barriers/protection features, and water.

Inspect first:

- `docs/tschamut_public_obstacle_context_scope.md`;
- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `scripts/inspect_tschamut_public_context_layers.py`;
- available ignored hazard rasters/manifests.

Required work:

1. Use existing hazard outputs and staged context evidence; do not implement
   obstacle physics.
2. Compute simple, documented overlap/proximity indicators only where artifact
   paths are available.
3. Keep the result as interpretation evidence, not operational acceptance.
4. If hazard or context artifacts are missing, record exact missing inputs.

Definition of done:

- hazard/context overlap is measured or explicitly blocked;
- limiting interpretation is updated with quantitative evidence;
- checks pass.

### TB-022: Add Same-Scale Artifact Readiness Preflight

Capability gap reduced: repeated worker tasks have spent substantial effort
discovering the same missing gate/target/context paths. A reusable preflight
should make the local readiness state explicit before long-running diagnostics.

Goal: add a lightweight command that checks same-scale gate, target, context,
and output-profile artifact readiness and emits exact missing paths and
regeneration commands.

Inspect first:

- `scripts/audit_local_artifacts.py`;
- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `docs/task_backlog.md`;
- existing validation and hazard command-plan generators.

Required work:

1. Reuse existing audit and command-plan logic where possible.
2. Keep the preflight lightweight and read-only.
3. Emit machine-readable JSON and concise human-readable output.
4. Avoid turning this into a new governance gate; it must directly reduce
   repeated missing-artifact discovery work.

Definition of done:

- a reusable readiness command reports gate/target/context readiness and exact
  missing regeneration steps;
- focused tests cover ready and missing-artifact fixtures;
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
