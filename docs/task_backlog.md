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
   same-scale hazard manifest and grid files are restored or regenerated in the
   current checkout.
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

- target-vs-gate spatial convergence on the refreshed same-scale hazard
  outputs;
- corridor-level context relevance from the staged swissTLM3D archive;
- a reusable same-scale uncertainty envelope that composes the measured
  convergence, output budget, context, and execution-sufficiency evidence;
- reusable comparison tooling for future selected-pilot artifact refreshes;
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

### TB-017: Restore The Same-Scale Target Hazard Manifest For Comparison

Capability gap reduced: the convergence diagnostic is ready, but the target
side of the refreshed same-scale hazard comparison is still missing in this
checkout.

Goal: restore or regenerate the target-side same-scale hazard manifest and its
referenced raster/grid files under the ignored local paths so TB-014 can be
rerun as a real target-vs-gate spatial comparison.

Inspect first:

- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `docs/conditional_hazard_convergence_acceptance_protocol.md`;
- `docs/tschamut_public_scalable_conditional_target_gate.md`;
- `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`;
- `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`;
- the ignored target-side paths listed in those records, if present locally.

Required work:

1. Restore or regenerate the target-side same-scale manifest and raster/grid
   files, or produce an exact missing-input checklist if the case inputs are
   unavailable.
2. Do not change physics, thresholds, release assumptions, or ensemble size.
3. Keep the outputs ignored and uncommitted.
4. Preserve the target-vs-gate comparison contract so TB-014 can consume the
   refreshed artifacts directly.

Definition of done:

- the target-side manifest and referenced grids are present locally, or the
  exact missing inputs and regeneration command are recorded;
- TB-014 can be rerun without further ambiguity;
- checks pass.

### TB-016: Build A Reusable Same-Scale Uncertainty Envelope Report

Capability gap reduced: the repository now measures convergence, output
budget, context, and execution sufficiency separately, but there is no single
reusable report that summarizes the remaining same-scale uncertainty in one
place for future pilot reviews.

Goal: compose the existing convergence, bounded-output, context, and
single-job sufficiency diagnostics into a compact uncertainty-envelope report
for the selected Tschamut pilot, without changing physics, thresholds, or
release assumptions.

Inspect first:

- `docs/tschamut_public_conditional_pilot_acceptance_summary.md`;
- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `docs/balfrin_single_job_execution_sufficiency.md`;
- `docs/tschamut_public_obstacle_context_scope.md`;
- `scripts/summarize_conditional_pilot_acceptance.py`;
- `scripts/summarize_bounded_validation_output_profile.py`;
- `scripts/inspect_tschamut_public_context_layers.py`.

Required work:

1. Reuse existing executable diagnostics instead of adding another status-only
   reader.
2. Quantify what uncertainty remains in convergence, output budget, context,
   and execution sufficiency.
3. Emit stable machine-readable fields and a concise markdown summary.
4. Make missing inputs explicit and preserve the non-operational claim
   boundary.

Definition of done:

- a reusable uncertainty-envelope report exists and is backed by measured
  inputs or exact missing-input paths;
- the report improves interpretability without authorizing scale-up;
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
