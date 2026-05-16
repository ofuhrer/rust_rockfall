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
evidence. Second-site pilots remain non-executed, but Chant Sura / Flüelapass
now has a concrete candidate manifest, a concrete acquisition manifest, a tiny
synthetic core-input staging helper, and an explicit
`deferred_public_context_inputs` boundary for the missing public context
products.

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
   `max_jump_height` remain support/nodata sensitive enough that the closure
   matrix treats both dominant layers as closure-limiting.
3. Output volume is measured and partly controlled but not yet a standard
   execution path.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. TB-042 implemented a Python-side
   `rebuildable_reduced_output` proof that retains the builder-facing
   trajectory, deposition, impact-event, and diagnostics artifacts in a compact
   ignored root and successfully rebuilds hazard layers from that reduced
   profile. The remaining workflow gap is canonical use of that profile in
   command plans or generation paths, not proof that the contract works.
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
6. Swiss-wide portability has a concrete Chant Sura / Flüelapass candidate, a
   multisite source/scenario contract audit, and a tiny synthetic core-input
   staging path. The candidate now has the ignored terrain, source-zone,
   scenario, processed-input, validation-root, and hazard-root inputs needed to
   separate core readiness from `deferred_public_context_inputs`. No second-site
   ensemble or hazard build is authorized, and the synthetic inputs must not be
   represented as real swisstopo evidence.
7. Scaling direction is measured for the current same-scale set. The
   single-job Balfrin path remains sufficient for the next same-scale step,
   distributed execution stays deferred, and the dominant bottleneck is
   validation output size rather than hazard-reducer parallelism.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked for the committed
   standard roots by the current strip-organized raster layout, missing
   overviews, and `cloud_optimized: false` metadata, not by missing package
   manifests. The ignored `gate_v1_cog_poc` package now audits as
   COG-ready, proving the package-level path without changing the committed
   roots. The remaining GIS workflow gap is turning that proof into a normal
   export option when the standard package path is ready to change.
9. Physical/annual frequency semantics, risk, exposure, vulnerability, and
   operational claims remain out of scope until conditional diagnostic
   convergence, source-frequency semantics, and validation/calibration
   evidence mature. The validation/calibration gap assessment reports
   `physical_credibility_status=not_established`, `calibration_status=missing`,
   and `validation_status=partial`.
10. The fully automated "user supplies an AOI and receives an
    intensity-frequency hazard map" workflow is still a future product shape,
    not the current user workflow. The missing pieces are AOI-to-swisstopo tile
    discovery and download/cache management; generic terrain and context
    preprocessing; heuristic release-zone identification; pragmatic release
    and block-scenario plan generation; automatic ensemble-size/convergence
    control; native rebuildable reduced output; default COG-ready GIS export;
    a site-level orchestrator that chains those steps; and, most importantly,
    physical frequency semantics from source occurrence rates, block-population
    frequencies, uncertainty propagation, and validation/calibration evidence.
    The near-term achievable product remains an automated conditional
    diagnostic hazard-map workflow; true intensity-frequency curves remain
    deferred until the physical-probability layer exists.

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

- decomposing the support/nodata component of the closure-limiting
  `max_kinetic_energy` and `max_jump_height` uncertainty instead of only
  reporting that it exists;
- translating spatial uncertainty masks into closure-gap deltas that identify
  what evidence would move the pilot toward deferred, no-go, or accepted
  diagnostic status;
- turning the rebuildable reduced-output proof from a derivation command into
  a normal generation/output mode before any larger validation-output run is
  attempted;
- moving Chant Sura / Flüelapass from synthetic core staging toward a concrete
  public-context acquisition decision without pretending that context products
  are already real validation evidence;
- turning the package-level COG proof into an export option that can produce
  COG-ready packages directly, while keeping manual QGIS acceptance deferred;
- mapping the missing physical-credibility evidence into concrete field or
  reference data requirements rather than broad calibration language.

Current priority order:

P0. TB-054 makes rebuildable reduced output a standard generation path because
    validation output size remains the measured scalability bottleneck.
P1. TB-055 advances Chant Sura public-context realism without starting a
    second-site ensemble.
P2. TB-056 promotes COG export from package-copy proof to a reusable export
    option for GIS-ready products.
P3. TB-057 makes physical-credibility evidence requirements executable and
    site-aware without adding calibration or operational claims.

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

If bootstrap, command-plan, or generated-artifact hygiene tests fail after a
task has been removed from this backlog, fix that engineering drift before
starting the next scientific or portability task. This does not replace the
active task queue; it keeps the queue executable.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history and `decision_log.md` for durable decisions.

### TB-054: Add A Standard Rebuildable Reduced Validation Output Mode

Priority: P2.

Why now: TB-042 and TB-049 proved and command-plan-addressed the
`rebuildable_reduced_output` contract, but it is still derived after the fact
from a full output root. The scalable path needs the validation workflow to
write this profile directly.

Capability gap reduced: rebuild-compatible scalable execution and output
volume control.

Why higher priority than alternatives: validation output size is the measured
runtime/scaling bottleneck, and a direct reduced-output mode is prerequisite
for any responsibly larger same-scale run.

Inspect first:

- Rust validation output writer and output-mode handling under `src/`
- `scripts/derive_hazard_rebuild_reduced_profile.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_hazard_rebuild_output_profile.py`
- `tests/test_hazard_rebuild_reduced_profile.py`
- `docs/tschamut_public_bounded_validation_output_profile.md`

Expected measurable outputs:

- a standard `rebuildable_reduced_output` validation output mode, or the
  narrowest equivalent workflow path, that writes the trajectory, deposition,
  impact-event, metadata, and diagnostics artifacts required by
  `build_hazard_layers.py`;
- manifest fields that classify the output mode distinctly from
  non-rebuildable `summary_only`;
- tests proving the generated reduced output is classified as rebuildable
  without relying on a full-output source root.

Definition of done:

- a fixture or bounded local run produces a reduced output root that
  `scripts/check_hazard_rebuild_output_profile.py` classifies as
  `rebuildable_reduced_output`;
- no large generated outputs are committed;
- no larger ensemble, physics tuning, distributed execution, scale-up, or
  operational claim is introduced.

### TB-055: Decide And Stage Chant Sura Public-Context Acquisition Boundaries

Priority: P3.

Why now: Chant Sura / Flüelapass has concrete candidate, acquisition, and
synthetic core-input fixtures, but public context remains deferred. The next
portability step is to decide exactly which real swisstopo context products
would move the preflight forward and how they would be recognized locally.

Capability gap reduced: Swiss-wide public-geodata portability realism.

Why higher priority than alternatives: second-site ensembles are not useful
until the repo can distinguish missing real public context from synthetic core
fixtures with product-level precision.

Inspect first:

- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Expected measurable outputs:

- a read-only acquisition-boundary report or preflight extension that lists the
  exact public-context product families, expected local paths, CRS/date
  metadata expectations, and which missing item keeps the site at
  `deferred_public_context_inputs`;
- tests proving synthetic core fixtures remain separate from real public
  context readiness;
- command-plan or docs updates that keep second-site ensemble commands blocked.

Definition of done:

- the Chant Sura preflight reports product-level public-context blockers with
  concrete local path expectations;
- no downloads, second-site ensemble, hazard build, calibration, portability
  acceptance, scale-up, or operational claim is introduced.

### TB-056: Add A COG-Ready Export Option For Same-Scale GIS Packages

Priority: P4.

Why now: the package-level COG conversion command works on an ignored copy, but
the normal GIS export path still writes standard roots that audit
`gis_package_ready_cog_blocked`.

Capability gap reduced: GIS/output usability and reproducible package
delivery.

Why higher priority than alternatives: GIS-ready products are a first-pilot
milestone, but this can wait behind the scientific and output-profile blockers
because the package-copy proof already exists.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_same_scale_cog_package_conversion.py`
- `tests/test_gis_cog_package_readiness.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Expected measurable outputs:

- a bounded COG-ready export flag, command-plan option, or post-export package
  step that produces a GIS package whose manifests and declared rasters audit
  as COG-ready without mutating the source standard roots;
- tests using small fixtures or mocked GDAL where appropriate;
- an ignored proof run only if local raster artifacts are available.

Definition of done:

- the export path can produce or declare a COG-ready ignored same-scale package
  through a standard command;
- standard roots remain honestly reported if not regenerated;
- no generated rasters are committed and no manual QGIS, operational, scale-up,
  annual-frequency, risk, exposure, or vulnerability claim is introduced.

### TB-057: Map Physical Credibility Data Requirements To Concrete Evidence Sources

Priority: P5.

Why now: the physical-credibility gap assessment correctly reports
`not_established`, `calibration_status=missing`, and `validation_status=partial`,
but it does not yet map those gaps to concrete field/reference data products
that future acquisition or collaborations could target.

Capability gap reduced: validation realism and physical-credibility boundary
clarity.

Why higher priority than deferred calibration work: it defines required
evidence sources without fitting parameters, expanding claims, or starting a
calibration workflow prematurely.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_chant_sura_holdout_evidence.py`
- `validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json`
- `data/datasets.yaml`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Expected measurable outputs:

- a read-only evidence-requirements matrix, preferably JSON/text, that maps
  observed runout/deposition, release-zone evidence, block-size or
  block-population evidence, terrain/context evidence, calibration splits, and
  holdout validation needs to concrete candidate data sources or missing
  acquisition classes;
- tests proving the matrix keeps calibration, physical probability, and
  operational claims blocked;
- docs updated to separate "data required for future credibility" from current
  diagnostic evidence.

Definition of done:

- the repo has a concrete, machine-readable list of physical-credibility data
  requirements and current evidence gaps;
- it does not tune parameters, create annual frequency semantics, validate
  operational skill, or change the current `not_established` physical
  credibility status.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- real Chant Sura public-context product downloads until a specific
  acquisition decision authorizes them;
- physical credibility boundary expansion beyond the existing evidence-gap
  matrix until new field/reference data is identified;
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
