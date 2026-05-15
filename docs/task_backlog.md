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
same-scale artifact chain is reproducible and measured, and the repository now
has multi-seed uncertainty, spatial uncertainty interpretation, closure
criteria, GIS/package, command-plan, COG proof-of-concept, and bounded
runtime/output evidence. Larger selected-domain runs remain blocked until the
dominant uncertainty and output-profile gaps below are reduced with measured
evidence. Second-site pilots remain metadata-only even though Chant Sura /
Flüelapass is staged as the concrete candidate manifest with a concrete
acquisition manifest.

Non-goals for current backlog work: operational warning systems, regulatory
approval, risk/exposure/vulnerability modelling, annual return-period claims,
parameter tuning to fit the pilot, and new contact/terrain physics unless a
separate falsifiable implementation task is explicitly authorized.

## Capability Gap Analysis

The most important gaps between the current repository and the project
objective are:

1. Conditional pilot evidence is still inconclusive, but the same-scale
   Tschamut workflow is no longer blocked on missing local artifacts. The
   readiness preflight, deterministic case regeneration, restored gate/target
   manifests, target-side `summary_only` output profile, portable command
   plan, measured convergence diagnostics, closure criteria, spatial
   uncertainty summary, and bounded runtime/output summaries now form an
   executable evidence chain. The earlier
   `Balfrin target-gate reproduction` remains useful single-job execution
   evidence.
2. Target-vs-gate convergence remains the dominant scientific uncertainty. The
   restored Tschamut gate and target hazard manifests expose 22 shared
   cell-wise layers. TB-024 ruled out grid/CRS and scenario/source path
   mismatch as dominant drivers. TB-031 expanded the evidence into six
   pairwise comparisons across gate, target, and two bounded 12-trajectory
   probes. `max_kinetic_energy` remains dominant with pairwise
   `l1_abs_diff` from `92903.17436309032` to `190718.90391041967`,
   `linf_abs_diff` from `1797.8665432400003` to `4484.5620665999995`, and
   nonzero Jaccard fixed at `1.0`. `max_jump_height` remains limited by
   support/nodata sensitivity with nonzero Jaccard from
   `0.7598039215686274` to `0.8579234972677595`.
   Spatial uncertainty is now measured from the same artifacts: the dominant
   uncertainty is localized rather than diffuse, but `max_kinetic_energy` and
   `max_jump_height` remain support/nodata sensitive enough that closure logic
   still needs to consume the spatial classifications explicitly.
3. Output volume is measured and partly controlled but not yet scale-ready.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially,
   but TB-025 showed that `summary_only` validation artifacts cannot currently
   rebuild hazard layers because the hazard builder still needs trajectory,
   deposition, impact-event, and diagnostics artifacts that the reduced profile
   omits. The minimum builder-facing contract is specified but not yet
   implemented as a real reduced-output mode.
4. Forest and obstacle context is no longer an absent-cache problem; it is a
   limiting interpretation problem. Public context is staged and measured at
   corridor level, and hazard-context overlap has been measured for a narrow
   broader envelope. The overlap remains unresolved and does not imply
   obstacle absence or obstacle physics.
5. Tschamut source-zone and block-scenario case regeneration is now
   deterministic from committed records and processed public inputs. The same
   pattern has only been audited, not implemented, for a non-Tschamut site with
   its own extent, terrain crop, source-zone metadata, scenario table, and
   context products.
6. Swiss-wide portability has a concrete metadata-only candidate in Chant Sura /
   Flüelapass, plus a multisite source/scenario contract audit. The candidate
   remains blocked on missing terrain, source-zone, scenario, public-context,
   validation-root, and hazard-root artifacts. No second-site ensemble or hazard
   build is authorized.
7. Scaling direction is measured for the current same-scale set. The
   single-job Balfrin path remains sufficient for the next same-scale step,
   distributed execution stays deferred, and the dominant bottleneck is
   validation output size rather than hazard-reducer parallelism.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked by the current
   strip-organized raster layout, missing overviews, and
   `cloud_optimized: false` metadata, not by missing package manifests. A
   scratch COG conversion proof has shown this is technically fixable, but no
   ignored same-scale package has yet been regenerated and audited as
   COG-ready.
9. Physical/annual frequency semantics, risk, exposure, vulnerability, and
   operational claims remain out of scope until conditional diagnostic
   convergence, source-frequency semantics, and validation/calibration
   evidence mature. The validation/calibration gap assessment reports
   `physical_credibility_status=not_established`, `calibration_status=missing`,
   and `validation_status=partial`.

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

- implementation of the hazard-rebuild-compatible reduced-output contract so a
  smaller retained-output profile actually rebuilds hazard layers, rather than
  only being specified;
- integration of spatial uncertainty summaries into closure logic so localized
  versus closure-limiting disagreement affects `accepted_diagnostic`, `no_go`,
  or `deferred` interpretation explicitly;
- regeneration of a same-scale GIS package into ignored COG-ready outputs so
  the scratch COG proof becomes normal package evidence;
- staging of minimal Chant Sura / Flüelapass public inputs so the second-site
  preflight moves from acquisition-manifest-ready to a more specific
  blocked-or-ready state;
- durable holdout evidence for Chant Sura so diagnostic selection evidence and
  independent validation evidence remain separated.

Current priority order:

1. TB-043 turns measured spatial uncertainty into closure evidence rather than
   another standalone summary.
2. TB-044 converts the proven COG path into an ignored package-level result.
3. TB-045 advances Swiss-wide portability only after the diagnostic evidence
   and output/product blockers are better controlled.

## Backlog Protocol

Each active task must include:

- scope small enough for one focused worker turn;
- explicit files, data records, or commands to inspect first;
- the concrete implementation, run, analysis, or validation outcome it enables;
- no-physics/no-tuning/no-operational-claim boundaries when relevant;
- exact outputs expected;
- focused checks to run.

For Tschamut same-scale tasks, prompts should normally tell workers to run the
agent task-context helper and then the readiness preflight before broad
inspection:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
```

```bash
PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json
```

Workers should use the bootstrap report for canonical helper commands, known
environment issues, ignored/generated roots, and task-specific inspect-first
files. They should use the readiness command's readiness flags,
`missing_paths`, and `regeneration_commands` as the current local artifact
state unless a task-specific diagnostic proves otherwise. Do not make workers
rediscover gate/target/context/output-profile paths manually when these helpers
can answer the question directly.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history and `decision_log.md` for durable decisions.

## Active Tasks

### TB-043: Use Spatial Uncertainty In Conditional Closure Logic

Goal: connect the measured spatial uncertainty diagnostics to the conditional
pilot closure helper so localized uncertainty and support/nodata-driven
uncertainty are interpreted consistently.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Expected work:

- extend the closure helper or its evidence mapping to consume the spatial
  uncertainty summary;
- distinguish localized shared-support magnitude variation from
  support/nodata-dominated disagreement in the closure matrix;
- report whether each dominant layer is closure-limiting, deferrable, or
  compatible with a future accepted diagnostic threshold.

Definition of done:

- the closure report no longer treats all spatial uncertainty as a scalar
  envelope; it names the layer-specific spatial concentration class;
- current closure remains conservative unless measured evidence supports a
  stricter status;
- tests cover localized shared-support uncertainty versus nodata/support
  dominated uncertainty.

Boundaries:

- no larger ensembles until the reduced-output blocker is resolved;
- no physics changes, tuning, scale-up, annual-frequency claims, risk, exposure,
  vulnerability, or operational use.

### TB-044: Regenerate One Ignored Same-Scale GIS Package As COG-Ready

Goal: move from the scratch COG proof of concept to an ignored same-scale GIS
package whose audit reports COG-ready rasters and `cloud_optimized: true`
metadata.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/prototype_cog_conversion.py`
- `scripts/build_hazard_layers.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `hazard/results/tschamut_public_pilot/gate_v1/`

Expected work:

- regenerate or convert one bounded same-scale package under an ignored output
  root;
- ensure rasters are tiled, compressed, and carry overviews;
- update package manifests for the regenerated package only so the audit can
  report COG readiness.

Definition of done:

- the GIS/COG audit reports the regenerated ignored package as COG-ready;
- the current committed/standard package state remains truthfully reported;
- no generated rasters or large package outputs are committed.

Boundaries:

- no manual QGIS acceptance unless actually performed;
- no scientific acceptance, scale-up, operational, annual-frequency, risk,
  exposure, or vulnerability claims.

### TB-045: Stage Minimal Chant Sura Inputs For Preflight Progress

Goal: move the Chant Sura / Flüelapass candidate beyond metadata-only
acquisition readiness by staging the smallest ignored input set needed to
reduce core `blocked_missing_inputs` categories.

Inspect first:

- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Expected work:

- stage or fixture a minimal terrain metadata, source-zone metadata, and
  scenario-table input set under ignored Chant Sura paths, using only public or
  tiny intentional fixture data;
- keep missing context or validation artifacts explicit if they remain
  intentionally deferred;
- rerun the second-site preflight and report which blockers were reduced.

Definition of done:

- the preflight no longer fails on the staged core input categories, or it
  reports exact remaining blockers after a bounded attempt;
- no raw or large geodata is downloaded or committed;
- no second-site validation ensemble or hazard build is run.

Boundaries:

- no Tschamut evidence reused as Chant Sura validation evidence;
- no tuning, source-frequency, annual probability, risk, exposure,
  vulnerability, scale-up, or operational claims.

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
- larger selected-domain or production ensembles until closure criteria,
  rebuildable reduced outputs, and current same-scale uncertainty blockers are
  addressed.
- helper consolidation beyond the task-context bootstrap until duplicated
  parsing becomes a demonstrated implementation bottleneck.
