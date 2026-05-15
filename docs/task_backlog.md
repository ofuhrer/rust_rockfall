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

The selected Tschamut target-scale evidence remains `inconclusive`. The
same-scale artifact chain is now reproducible and measured, but larger
selected-domain runs remain blocked until the capability gaps below are reduced
with measured evidence. Second-site pilots remain at metadata-preflight status
until a concrete candidate manifest and public-geodata staging path exist.

Non-goals for current backlog work: operational warning systems, regulatory
approval, risk/exposure/vulnerability modelling, annual return-period claims,
parameter tuning to fit the pilot, and new contact/terrain physics unless a
separate falsifiable implementation task is explicitly authorized.

## Capability Gap Analysis

The most important gaps between the current repository and the project
objective are:

1. Conditional pilot evidence is still inconclusive, but the same-scale
   Tschamut workflow is no longer blocked on missing local artifacts. The
   earlier Balfrin target-gate reproduction remains useful execution evidence.
   The readiness preflight, deterministic case regeneration, restored
   gate/target manifests, target-side `summary_only` output profile, and
   measured convergence diagnostics now form an executable evidence chain.
2. Target-vs-gate convergence remains the dominant scientific uncertainty. The
   restored Tschamut gate and target hazard manifests expose 22 shared
   cell-wise layers, but the comparison remains inconclusive with
   `cellwise_linf_abs_diff_max = 3028.22579673`,
   `cellwise_l1_abs_diff_sum = 190790.42488112117`, and
   `cellwise_nonzero_jaccard_min = 0.1`. TB-024 ruled out grid/CRS and
   scenario/source path mismatch as dominant drivers. TB-025 showed a bounded
   12-trajectory sampling probe reduced but did not eliminate the dominant
   `max_kinetic_energy`, `max_jump_height`, and velocity-exceedance
   disagreements.
3. Output volume is measured and partly controlled but not yet scale-ready.
   Gate-side `summary_only` output reduced from `125` files / `34545900` bytes
   to `4` files / `81425` bytes; target-side `summary_only` output reduced
   from `2005` files / `571368823` bytes to `4` files / `1271721` bytes. The
   bounded full-output sampling probe still produced `247` validation files /
   `68221148` bytes, showing hazard rebuilding currently needs trajectory
   artifacts that `summary_only` omits.
4. Forest and obstacle context is no longer an absent-cache problem; it is a
   limiting interpretation problem. Public context is staged and measured at
   corridor level, and hazard-context overlap has been measured for a narrow
   broader envelope. The overlap remains unresolved and does not imply
   obstacle absence or obstacle physics.
5. Tschamut source-zone and block-scenario case regeneration is now
   deterministic from committed records and processed public inputs. The same
   pattern is not yet generalized to a non-Tschamut site with its own extent,
   terrain crop, source-zone metadata, scenario table, and context products.
6. Swiss-wide portability has a metadata-only preflight, but it is still
   abstract. A concrete second-site manifest/config is needed to turn the
   portability checklist into actionable public-geodata staging work.
7. Scaling direction is bounded but undermeasured. The single-job Balfrin path
   remains sufficient for the next same-scale step and distributed execution
   stays deferred, but reducer/runtime behavior for repeated bounded probes or
   larger deterministic ensembles still needs measurement before scale-up.
8. GIS-ready outputs exist in the workflow, but COG/package interoperability
   remains secondary and under-audited. It should be checked with existing
   artifacts before any larger or second-site run depends on those products.
9. Physical/annual frequency semantics, risk, exposure, vulnerability, and
   operational claims remain out of scope until conditional diagnostic
   convergence, source-frequency semantics, and validation/calibration
   evidence mature.

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

- comparing the Tschamut source-zone/block-scenario assumptions with the
  staged Chant Sura / Flüelapass second-site manifest so portable contract
  fields are separated from Tschamut-specific heuristics;
- multi-seed same-scale uncertainty characterization that separates seed
  sensitivity from structural sampled-output divergence;
- reusable sampling-uncertainty summaries across the original gate/target and
  bounded probe artifacts;
- command-plan consolidation for local pilot execution so workers do not copy
  long validation/hazard commands from work-log prose;
- GIS/COG/package readiness checks on existing same-scale artifacts;
- reducer/runtime/output scaling measurements on bounded, non-production
  ensembles;
- concrete public-geodata staging plans for the Chant Sura / Flüelapass
  candidate after its source/scenario portability contract is understood.

## Backlog Protocol

Each active task must include:

- scope small enough for one focused worker turn;
- explicit files, data records, or commands to inspect first;
- the concrete implementation, run, analysis, or validation outcome it enables;
- no-physics/no-tuning/no-operational-claim boundaries when relevant;
- exact outputs expected;
- focused checks to run.

For Tschamut same-scale tasks, prompts should normally tell workers to run the
readiness preflight before broad inspection:

```bash
PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json
```

Workers should use that command's readiness flags, `missing_paths`, and
`regeneration_commands` as the current local artifact state unless a
task-specific diagnostic proves otherwise. Do not make workers rediscover
gate/target/context/output-profile paths manually when the preflight can answer
the question directly.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history and `decision_log.md` for durable decisions.

## Active Tasks

### TB-034: Measure Bounded Reducer Runtime And Output Scaling

Capability gap reduced: distributed execution is deferred, but larger
deterministic ensemble readiness still depends on reducer/runtime/output
behavior beyond the current same-scale probes.

Goal: run a bounded reducer/runtime/output scaling measurement using existing
small artifacts or a tiny controlled probe, then report whether local
single-job execution still appears sufficient for the next measurement step.

Inspect first:

- `docs/balfrin_single_job_execution_sufficiency.md`;
- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `scripts/build_hazard_layers.py`;
- existing validation/hazard manifests for gate, target, and sampling probes;
- reducer/chunking code paths referenced by the hazard builder.

Required work:

1. Keep the measurement bounded; do not run a large production ensemble.
2. Preserve physics, thresholds, source/scenario inputs, and baselines.
3. Record runtime, reducer workers, file counts, bytes, and bottleneck class.
4. Do not authorize distributed execution unless a measured need is shown.

Definition of done:

- bounded reducer/runtime/output evidence is recorded;
- the next scaling decision is supported by measurements rather than
  assumption;
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
