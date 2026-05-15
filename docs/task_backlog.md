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
has multi-seed uncertainty, GIS/package, command-plan, and bounded
runtime/output evidence. Larger selected-domain runs remain blocked until the
dominant uncertainty and output-profile gaps below are reduced with measured
evidence. Second-site pilots remain metadata-only even though Chant Sura /
Flüelapass is staged as the concrete candidate manifest.

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
   plan, measured convergence diagnostics, and bounded runtime/output summaries
   now form an executable evidence chain. The earlier
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
   Current tooling interprets this mostly through scalar pairwise metrics,
   layer summaries, and envelope ranges. The next scientific maturation step is
   spatial uncertainty interpretation: where uncertainty concentrates, which
   cells are stable across seeds, and which layers produce persistent spatial
   disagreement.
3. Output volume is measured and partly controlled but not yet scale-ready.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially,
   but TB-025 showed that `summary_only` validation artifacts cannot currently
   rebuild hazard layers because the hazard builder still needs trajectory CSV
   artifacts that the reduced profile omits.
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
   `cloud_optimized: false` metadata, not by missing package manifests.
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

- a closure assessment that turns the measured uncertainty, context, output,
  GIS, and runtime evidence into explicit non-operational diagnostic
  `accepted`, `no_go`, or `deferred` criteria without changing the current
  classification by assertion;
- a hazard-rebuild-compatible reduced-output profile that preserves the
  trajectory metadata needed by `scripts/build_hazard_layers.py` while keeping
  validation output closer to `summary_only`;
- spatial uncertainty interpretation tooling that turns the existing same-scale
  gate/target/probe artifacts into per-layer stability maps, agreement masks,
  uncertainty surfaces, or cell-wise variance summaries;
- a bounded COG conversion proof of concept that fixes the measured raster
  layout blocker without committing generated raster products;
- a concrete Chant Sura / Flüelapass public-geodata acquisition/staging plan
  that turns the current metadata fixture into exact public input requirements;
- validation/calibration evidence-gap analysis that names the field or
  reference data needed for physical credibility without tuning the model.

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

### TB-039: Stage A Concrete Chant Sura Public-Geodata Acquisition Manifest

Goal: move the Chant Sura / Flüelapass candidate from a blocked metadata
fixture toward exact public-geodata staging requirements.

Inspect first:

- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `data/datasets.yaml`

Expected work:

- add or update a small committed manifest that names the exact expected
  terrain, source-zone, scenario, and context inputs for the candidate site;
- include acquisition/staging commands or placeholders that are specific enough
  for a future worker to execute once data access is available;
- keep the second-site preflight metadata-only and blocked until the artifacts
  actually exist.

Definition of done:

- the candidate preflight reports concrete missing paths and product categories
  rather than generic template gaps;
- no raw or large geodata is downloaded or committed;
- no second-site ensemble or hazard build is run.

Boundaries:

- no Tschamut evidence is reused as Chant Sura validation evidence;
- no source-frequency, annual probability, risk, exposure, or operational
  claims.

### TB-040: Assess Validation And Calibration Evidence Gaps For Physical Credibility

Goal: identify the field, reference, or benchmark evidence required to move
from workflow credibility toward physical credibility.

Inspect first:

- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `data/datasets.yaml`
- any existing validation fixture references for Tschamut, Chant Sura,
  Schiers, or Balfrin discovered from those files only.

Expected work:

- produce a concise evidence-gap matrix separating observed deposition,
  release-zone evidence, block-size distribution evidence, terrain/context
  evidence, and calibration/holdout needs;
- identify which gaps block physical probability claims versus which only
  limit diagnostic interpretation;
- update docs/backlog with executable next data-staging tasks only if the
  evidence gap is concrete.

Definition of done:

- the report names the minimum evidence needed for physical credibility without
  tuning the current model;
- it does not relabel current same-scale evidence as physically validated;
- it preserves all non-operational boundaries.

Boundaries:

- no calibration, parameter fitting, physics changes, annual-frequency claims,
  risk, exposure, vulnerability, or operational use.

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
