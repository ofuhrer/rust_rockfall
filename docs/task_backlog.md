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
3. Output volume is measured and now has a native rebuildable reduced
   execution mode.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. The native `rebuildable_reduced_output` mode now
   writes the builder-facing trajectory, deposition, impact-event, diagnostics,
   trajectory-metadata, and stop-state artifacts directly and is exposed in the
   same-scale command plan. The remaining workflow gap is making downstream
   synthesis and tests consistently distinguish the old non-rebuildable
   `summary_only` profile from the valid native reduced mode.
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
   manifests. The first-class `--export-cog` path now writes an ignored
   `gate_v1_cog_export` package that audits as COG-ready, proving the
   package-level export path without changing the committed roots. The
   remaining GIS workflow gaps are parity/semantics checks for the exported
   layer set and making reports expose both the standard-root status and the
   converted-package status without ambiguity.
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

- fixing post-TB-057 engineering drift that can mislead workers before the next
  scientific task, especially live-artifact-dependent command-plan tests, stale
  COG documentation, and ambiguous converted-package COG readiness summaries;
- decomposing the support/nodata component of the closure-limiting
  `max_kinetic_energy` and `max_jump_height` uncertainty instead of only
  reporting that it exists;
- translating spatial uncertainty masks into closure-gap deltas that identify
  what evidence would move the pilot toward deferred, no-go, or accepted
  diagnostic status;
- turning the rebuildable reduced-output proof into a normal generation/output
  mode before any larger validation-output run is attempted;
- moving Chant Sura / Flüelapass from synthetic core staging toward a concrete
  public-context acquisition decision without pretending that context products
  are already real validation evidence;
- keeping the package-level COG export path reproducible on regenerated
  packages while keeping manual QGIS acceptance deferred;
- mapping the missing physical-credibility evidence into concrete field or
  reference data requirements rather than broad calibration language.

## Active Tasks

### TB-058 (P0): Stabilize Command-Plan And COG Readiness Drift

Why it matters now: post-TB-057 reviews found red or fragile worker-facing
surfaces before any new scientific task starts. The command-plan tests still
depend on ignored local Tschamut artifacts, COG docs still describe
`--export-cog` as deferred in some places, and the GIS/COG audit can be
misread if automation only looks at the top-level standard-root status.

Capability gap reduced: makes the executable queue reliable in fresh checkouts
and prevents workers from following stale COG/export guidance.

Why this outranks alternatives: it is the highest-leverage cleanup because it
protects every later task from false failures and stale helper output.

Inspect first:

- `tests/test_pilot_command_plan.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `docs/pilot_gis_package.md`
- `docs/model_benchmark_execution_report.md`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`

Expected measurable outputs:

- command-plan tests use fixtures or explicit skip/block behavior instead of
  assuming ignored Tschamut artifacts exist;
- COG docs distinguish standard non-COG roots from the now-valid
  `--export-cog` path;
- GIS/COG audit exposes an explicit converted-package readiness summary such
  as `converted_package_readiness_status` or `any_converted_package_ready`;
- diagnostic interpretation distinguishes old `summary_only` blockers from
  native rebuildable reduced output and standard-root COG blockers from
  converted-package readiness.

Definition of done:

- focused command-plan, GIS/COG, and diagnostic-interpretation tests pass in a
  way that does not rely on ignored generated artifacts;
- `print_agent_task_context.py --format json` and the same-scale command plan
  point workers at current helpers;
- no placeholder artifacts remain after the test run.

Boundaries: no scientific reclassification, no new simulation, no COG package
manual QA, no operational or scale-up claim.

### TB-059 (P1): Emit Persistent Spatial Disagreement Stability Zones

Why it matters now: TB-052 and TB-053 decomposed closure-limiting uncertainty,
but workers still need a compact spatial product that distinguishes persistent
closure-limiting regions from localized deferrable disagreement.

Capability gap reduced: scientific interpretability and uncertainty
understanding.

Why this outranks alternatives: it turns the existing measured uncertainty into
actionable closure evidence without running another ensemble or changing
physics.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Expected measurable outputs:

- JSON/text summary of stability zones for `max_kinetic_energy`,
  `max_jump_height`, and `velocity_exceedance_5mps`;
- counts, bounding boxes, and fractions for persistent closure-limiting,
  deferrable localized, shared-support magnitude, and support/nodata-sensitive
  cells;
- optional scratch-only CSV/GeoJSON products under `/tmp` for review.

Definition of done:

- closure helper consumes or references the stability-zone summary;
- docs state whether the stability zones change the closure status, which is
  expected to remain conservative unless evidence proves otherwise;
- focused tests cover the classification rules.

Boundaries: no tuning, no physics change, no new ensemble, no accepted/no-go
status change unless directly justified by existing measured evidence.

### TB-060 (P2): Trace Uncertainty Hotspots To Source And Scenario Evidence

Why it matters now: the dominant hotspots are known spatially, but the repo
does not yet explain whether the high-uncertainty cells align with particular
source-zone, release, scenario, or trajectory families.

Capability gap reduced: scientific interpretability and pilot closure realism.

Why this outranks larger ensembles: attribution of current hotspots is needed
before deciding whether another bounded ensemble would actually reduce the
closure blocker.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `data/processed/swisstopo/tschamut_public_pilot/input/`
- `validation/private/tschamut_public_pilot/*`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Expected measurable outputs:

- read-only hotspot provenance report mapping selected high-uncertainty cells
  to available source-zone metadata, scenario rows, trajectory/deposition
  evidence, and artifact roots;
- explicit classification of what can and cannot be attributed from current
  artifacts;
- prioritized unknowns for any later bounded ensemble.

Definition of done:

- helper emits JSON/text with per-layer hotspot provenance classes;
- tests use small fixtures and do not require ignored full artifacts;
- docs record the interpretation limits.

Boundaries: no new simulation, no source-zone tuning, no physical-probability
claim, no operational interpretation.

### TB-061 (P3): Define A Bounded Next-Ensemble Feasibility Probe

Why it matters now: closure remains inconclusive, but any additional ensemble
should be justified by expected information gain and bounded output cost.

Capability gap reduced: uncertainty characterization and scalable execution
planning.

Why this outranks running a larger ensemble now: it prevents spending compute
on a run that cannot materially reduce the measured closure gap or that would
recreate the validation-output bottleneck.

Inspect first:

- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Expected measurable outputs:

- a read-only feasibility report for the smallest additional same-scale probe,
  including proposed seed/scenario scope, expected artifact families,
  estimated output size, and expected closure question answered;
- command-plan template using native `rebuildable_reduced_output`, but not
  executing the run;
- explicit go/no-go criteria for whether the probe would be worth running.

Definition of done:

- JSON/text helper and command-plan entry exist;
- report proves the proposed probe is bounded relative to measured target/full
  output sizes;
- docs keep execution deferred until explicitly authorized.

Boundaries: do not run the ensemble, do not tune parameters, do not authorize
scale-up or distributed execution.

### TB-062 (P4): Generate Chant Sura Dry-Run Case Skeleton

Why it matters now: Chant Sura core synthetic staging is ready and public
context is deferred, but there is no concrete second-site case-generation
skeleton showing what would run once real public context exists.

Capability gap reduced: Swiss-wide portability and second-site realism.

Why this outranks real downloads: it tests the reusable source/scenario/case
plumbing without pretending the synthetic fixtures are real swisstopo evidence.

Inspect first:

- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Expected measurable outputs:

- dry-run case-generation helper or command-plan entry that writes only to
  `/tmp` or ignored paths;
- case skeleton includes terrain/source-zone/scenario/policy references and
  explicit deferred public-context placeholders;
- preflight remains `deferred_public_context_inputs`.

Definition of done:

- focused tests prove the dry-run skeleton is generated, validates references,
  and blocks ensemble execution;
- command plan surfaces the dry-run without adding real second-site run
  commands.

Boundaries: no second-site ensemble, no hazard build, no downloads, no
portability or physical-evidence claim.

### TB-063 (P5): Add AOI-To-Swisstopo Acquisition Dry-Run Planner

Why it matters now: the desired future user workflow begins with a geographic
region, but the repo still lacks a dry-run step that maps an AOI to required
public geodata products and expected staging paths.

Capability gap reduced: Swiss-wide public-geodata portability and user
workflow automation.

Why this outranks real acquisition: dry-run planning can be implemented and
tested without network downloads, licensing ambiguity, or large artifacts.

Inspect first:

- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `scripts/check_second_site_public_geodata_preflight.py`
- Chant Sura acquisition manifest under
  `tests/fixtures/second_site_public_geodata_preflight/`

Expected measurable outputs:

- helper accepting a small AOI/site config and emitting required swisstopo
  product categories, expected staging paths, and unresolved acquisition
  decisions;
- Chant Sura fixture coverage showing the planner matches the current deferred
  context boundary;
- no downloads or generated public-context artifacts.

Definition of done:

- JSON/text output is deterministic and fixture-backed;
- preflight or command-plan docs point to the dry-run planner as the first
  step before real staging.

Boundaries: no network fetches, no tile downloading, no claim that products
are locally staged unless files exist.

### TB-064 (P6): Verify COG Export Layer Parity And Audit Semantics

Why it matters now: `--export-cog` is proven, but reviews noted possible
confusion between standard roots with 22 layers and exported COG roots with a
different declared raster count.

Capability gap reduced: GIS/output usability.

Why this outranks manual QGIS QA: automated parity and scope checks are needed
before a manual review can be meaningful.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `tests/test_hazard_layers.py`
- `tests/test_gis_cog_package_readiness.py`
- `docs/pilot_gis_package.md`

Expected measurable outputs:

- audit summary comparing standard-root layer inventory to exported COG-root
  layer inventory;
- explicit semantics for omitted/non-exported layers, if any;
- test covering the `gate_v1_cog_export` expected scope without committing
  rasters.

Definition of done:

- `audit_gis_cog_package_readiness.py --converted-package-root ...` reports
  both package readiness and layer-parity/scope status;
- docs state which layers are expected in COG exports and why.

Boundaries: no generated rasters committed, no manual QGIS acceptance, no
operational product claim.

### TB-065 (P7): Score Physical-Credibility Evidence Acquisition Priorities

Why it matters now: TB-057 mapped missing evidence requirements, but it does
not yet rank which concrete evidence acquisitions would most reduce the
physical-credibility gap.

Capability gap reduced: physical credibility boundaries and validation realism.

Why this outranks broad calibration work: it keeps the next physical-evidence
step concrete and prevents premature parameter fitting without data.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_chant_sura_holdout_evidence.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/swisstopo_data_strategy.md`

Expected measurable outputs:

- ranked evidence-acquisition matrix for observed runout/deposition,
  release-zone evidence, block population, source-frequency evidence,
  calibration objective functions, independent holdout validation, and
  multi-site transfer evidence;
- current repo evidence separated from future field/reference-data needs;
- no change to claim boundaries.

Definition of done:

- helper emits JSON/text with priority, expected claim unlocked, required data,
  and current repo gap for each evidence class;
- docs state which evidence class is first actionable and which remains
  deferred.

Boundaries: no calibration fitting, no annual-frequency model, no operational,
risk, exposure, or vulnerability claim.

### TB-066 (P8): Reconcile Canonical Diagnostic Interpretation With Current Product Paths

Why it matters now: the canonical diagnostic interpretation exists, but its
blocker language can lag behind product improvements such as native reduced
output and COG export.

Capability gap reduced: pilot closure realism and user-facing interpretation
coherence.

Why this follows the drift fix: TB-058 should make the helpers/docs reliable;
this task then updates the high-level interpretation artifact so users see a
single current story.

Inspect first:

- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Expected measurable outputs:

- diagnostic interpretation separates scientific blockers from workflow
  blockers already mitigated by alternate paths;
- reduced output and COG export readiness appear as mitigations, while
  standard-root and old `summary_only` blockers remain accurately named;
- no change to `inconclusive_conditional_diagnostic` unless supported by
  measured closure evidence.

Definition of done:

- JSON/text interpretation includes current product-path statuses and
  mitigations;
- focused tests pin the blocker/mitigation split;
- gate report references the updated interpretation.

Boundaries: no acceptance claim, no no-go reclassification, no new simulation,
no operational semantics.

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
