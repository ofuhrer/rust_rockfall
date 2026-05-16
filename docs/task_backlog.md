# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

## Active Tasks

### TB-058: Stabilize Command-Plan And COG Readiness Drift

Goal: post-TB-057 reviews found red or fragile worker-facing surfaces before any new scientific task starts. Reduces: makes the executable queue reliable in fresh checkouts and prevents workers from following stale COG/export guidance.

Inspect first:

- `tests/test_pilot_command_plan.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `docs/pilot_gis_package.md`
- `docs/model_benchmark_execution_report.md`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`

Deliverables:

- command-plan tests use fixtures or explicit skip/block behavior instead of assuming ignored Tschamut artifacts exist;
- COG docs distinguish standard non-COG roots from the now-valid `--export-cog` path;
- GIS/COG audit exposes an explicit converted-package readiness summary such as `converted_package_readiness_status` or `any_converted_package_ready`;
- diagnostic interpretation distinguishes old `summary_only` blockers from native rebuildable reduced output and standard-root COG blockers from converted-package readiness.

Definition of done:

- focused command-plan, GIS/COG, and diagnostic-interpretation tests pass in a way that does not rely on ignored generated artifacts;
- `print_agent_task_context.py --format json` and the same-scale command plan point workers at current helpers;
- no placeholder artifacts remain after the test run.

Boundaries: no scientific reclassification, no new simulation, no COG package
manual QA, no operational or scale-up claim.

### TB-059: Emit Persistent Spatial Disagreement Stability Zones

Goal: TB-052 and TB-053 decomposed closure-limiting uncertainty, but workers still need a compact spatial product that distinguishes persistent closure-limiting regions from localized deferrable disagreement. Reduces: scientific interpretability and uncertainty understanding.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- JSON/text summary of stability zones for `max_kinetic_energy`, `max_jump_height`, and `velocity_exceedance_5mps`;
- counts, bounding boxes, and fractions for persistent closure-limiting, deferrable localized, shared-support magnitude, and support/nodata-sensitive cells;
- optional scratch-only CSV/GeoJSON products under `/tmp` for review.

Definition of done:

- closure helper consumes or references the stability-zone summary;
- docs state whether the stability zones change the closure status, which is expected to remain conservative unless evidence proves otherwise;
- focused tests cover the classification rules.

Boundaries: no tuning, no physics change, no new ensemble, no accepted/no-go
status change unless directly justified by existing measured evidence.

### TB-060: Trace Uncertainty Hotspots To Source And Scenario Evidence

Goal: the dominant hotspots are known spatially, but the repo does not yet explain whether the high-uncertainty cells align with particular source-zone, release, scenario, or trajectory families. Reduces: scientific interpretability and pilot closure realism.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `data/processed/swisstopo/tschamut_public_pilot/input/`
- `validation/private/tschamut_public_pilot/*`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- read-only hotspot provenance report mapping selected high-uncertainty cells to available source-zone metadata, scenario rows, trajectory/deposition evidence, and artifact roots;
- explicit classification of what can and cannot be attributed from current artifacts;
- prioritized unknowns for any later bounded ensemble.

Definition of done:

- helper emits JSON/text with per-layer hotspot provenance classes;
- tests use small fixtures and do not require ignored full artifacts;
- docs record the interpretation limits.

Boundaries: no new simulation, no source-zone tuning, no physical-probability
claim, no operational interpretation.

### TB-061: Define A Bounded Next-Ensemble Feasibility Probe

Goal: closure remains inconclusive, but any additional ensemble should be justified by expected information gain and bounded output cost. Reduces: uncertainty characterization and scalable execution planning.

Inspect first:

- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- a read-only feasibility report for the smallest additional same-scale probe, including proposed seed/scenario scope, expected artifact families, estimated output size, and expected closure question answered;
- command-plan template using native `rebuildable_reduced_output`, but not executing the run;
- explicit go/no-go criteria for whether the probe would be worth running.

Definition of done:

- JSON/text helper and command-plan entry exist;
- report proves the proposed probe is bounded relative to measured target/full output sizes;
- docs keep execution deferred until explicitly authorized.

Boundaries: do not run the ensemble, do not tune parameters, do not authorize
scale-up or distributed execution.

### TB-062: Generate Chant Sura Dry-Run Case Skeleton

Goal: Chant Sura core synthetic staging is ready and public context is deferred, but there is no concrete second-site case-generation skeleton showing what would run once real public context exists. Reduces: Swiss-wide portability and second-site realism.

Inspect first:

- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- dry-run case-generation helper or command-plan entry that writes only to `/tmp` or ignored paths;
- case skeleton includes terrain/source-zone/scenario/policy references and explicit deferred public-context placeholders;
- preflight remains `deferred_public_context_inputs`.

Definition of done:

- focused tests prove the dry-run skeleton is generated, validates references, and blocks ensemble execution;
- command plan surfaces the dry-run without adding real second-site run commands.

Boundaries: no second-site ensemble, no hazard build, no downloads, no
portability or physical-evidence claim.

### TB-063: Add AOI-To-Swisstopo Acquisition Dry-Run Planner

Goal: the desired future user workflow begins with a geographic region, but the repo still lacks a dry-run step that maps an AOI to required public geodata products and expected staging paths. Reduces: Swiss-wide public-geodata portability and user workflow automation.

Inspect first:

- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `scripts/check_second_site_public_geodata_preflight.py`
- Chant Sura acquisition manifest under `tests/fixtures/second_site_public_geodata_preflight/`

Deliverables:

- helper accepting a small AOI/site config and emitting required swisstopo product categories, expected staging paths, and unresolved acquisition decisions;
- Chant Sura fixture coverage showing the planner matches the current deferred context boundary;
- no downloads or generated public-context artifacts.

Definition of done:

- JSON/text output is deterministic and fixture-backed;
- preflight or command-plan docs point to the dry-run planner as the first step before real staging.

Boundaries: no network fetches, no tile downloading, no claim that products
are locally staged unless files exist.

### TB-064: Verify COG Export Layer Parity And Audit Semantics

Goal: `--export-cog` is proven, but reviews noted possible confusion between standard roots with 22 layers and exported COG roots with a different declared raster count. Reduces: GIS/output usability.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `tests/test_hazard_layers.py`
- `tests/test_gis_cog_package_readiness.py`
- `docs/pilot_gis_package.md`

Deliverables:

- audit summary comparing standard-root layer inventory to exported COG-root layer inventory;
- explicit semantics for omitted/non-exported layers, if any;
- test covering the `gate_v1_cog_export` expected scope without committing rasters.

Definition of done:

- `audit_gis_cog_package_readiness.py --converted-package-root ...` reports both package readiness and layer-parity/scope status;
- docs state which layers are expected in COG exports and why.

Boundaries: no generated rasters committed, no manual QGIS acceptance, no
operational product claim.

### TB-065: Score Physical-Credibility Evidence Acquisition Priorities

Goal: TB-057 mapped missing evidence requirements, but it does not yet rank which concrete evidence acquisitions would most reduce the physical-credibility gap. Reduces: physical credibility boundaries and validation realism.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_chant_sura_holdout_evidence.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- ranked evidence-acquisition matrix for observed runout/deposition, release-zone evidence, block population, source-frequency evidence, calibration objective functions, independent holdout validation, and multi-site transfer evidence;
- current repo evidence separated from future field/reference-data needs;
- no change to claim boundaries.

Definition of done:

- helper emits JSON/text with priority, expected claim unlocked, required data, and current repo gap for each evidence class;
- docs state which evidence class is first actionable and which remains deferred.

Boundaries: no calibration fitting, no annual-frequency model, no operational,
risk, exposure, or vulnerability claim.

### TB-066: Reconcile Canonical Diagnostic Interpretation With Current Product Paths

Goal: the canonical diagnostic interpretation exists, but its blocker language can lag behind product improvements such as native reduced output and COG export. Reduces: pilot closure realism and user-facing interpretation coherence.

Inspect first:

- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- diagnostic interpretation separates scientific blockers from workflow blockers already mitigated by alternate paths;
- reduced output and COG export readiness appear as mitigations, while standard-root and old `summary_only` blockers remain accurately named;
- no change to `inconclusive_conditional_diagnostic` unless supported by measured closure evidence.

Definition of done:

- JSON/text interpretation includes current product-path statuses and mitigations;
- focused tests pin the blocker/mitigation split;
- gate report references the updated interpretation.

Boundaries: no acceptance claim, no no-go reclassification, no new simulation,
no operational semantics.

## Backlog Protocol

Task headings must always be exactly:

```markdown
### TB-XXX: Short Description
```

Do not put priority, status, owner, or tags in the heading. Use this schema for
every active task:

```markdown
### TB-XXX: Short Description

Goal: One sentence describing why the task matters and what gap it reduces.

Inspect first:

- `path/or/script.py`

Deliverables:

- Concrete executable, analysis, test, or measured output.

Definition of done:

- Focused checks pass and the task is removed from this backlog.

Boundaries: No tuning, operational claims, scale-up authorization, or other
phase changes unless the task explicitly allows them.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read only the selected task and its `Inspect first` files unless the task
explicitly requires broader context. Use `--detail full` on the task-context
helper only for orchestrator/review work.

Before commit, run the task-specific checks, `git diff --check`, repository
consistency, `scripts/git-hooks/pre-commit`, and the placeholder-artifact scan.

Do not keep completed tasks here. Use `agent_work_log.md` for chronological TB
execution history and `decision_log.md` for durable decisions.

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
