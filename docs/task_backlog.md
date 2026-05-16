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

_Active TB tasks remain below._

### TB-083: Add Observed Runout Intake Readiness Pack Generator

Goal: Make the TB-080 observed runout/deposition contract actionable by generating a dry-run readiness pack for future real benchmark data.

Capability gap reduced: Validation-data acquisition reproducibility.

Why this outranks alternatives: The contract is useful but still manual; a dry-run pack tells a future data provider exactly what files, fields, and provenance must exist.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A CLI option or helper emits a template manifest, required geometry inventory, provenance checklist, and validation summary into a caller-provided temporary directory.
- The generated pack is explicitly marked as a template/non-evidence artifact.
- Tests verify the pack structure without committing generated benchmark files.

Definition of done:

- The readiness pack can be generated and validated in a temporary directory, focused tests pass, and TB-083 is removed from this backlog.

Boundaries: No real benchmark data, calibration, parameter fitting, operational claims, or committed generated artifact roots.

### TB-084: Resolve COG Export Layer-Scope Delta

Goal: Make the COG export proof either full-scope with the standard same-scale GIS package or explicitly bounded in machine-readable audit output.

Capability gap reduced: GIS product usability and reproducible export semantics.

Why this outranks alternatives: The export path works, but the converted proof currently differs from the standard 22-layer scope, which can mislead downstream GIS users.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_hazard_layers.py`
- `tests/test_gis_cog_package_readiness.py`

Deliverables:

- Either a full-scope COG export command/audit path that includes the missing 0.5 m jump-height layers, or an explicit bounded-scope COG classification with the omitted layer list.
- Command-plan metadata exposes the intended COG scope.
- Tests cover the selected full-scope or bounded-scope behavior.

Definition of done:

- COG audit output no longer leaves the layer-scope delta ambiguous, focused tests pass, and TB-084 is removed from this backlog.

Boundaries: Do not commit generated rasters, perform manual QGIS acceptance, or introduce operational GIS claims.

### TB-085: Attribute Closure-Limiting Hotspots To Source And Scenario Evidence

Goal: Trace dominant uncertainty hotspots back to available source-zone, release, scenario, and support/nodata evidence without running new simulations.

Capability gap reduced: Scientific interpretability of closure-limiting uncertainty.

Why this outranks alternatives: The repo knows where hotspots are; the next scientific value is explaining whether they align with source/scenario structure or data-support limits.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- JSON/text hotspot attribution for `max_kinetic_energy` and `max_jump_height`.
- Counts or fractions for hotspots associated with shared-support magnitude, support/nodata sensitivity, source-zone proximity, release/scenario identifiers when available, and unknown attribution.
- Closure output references the attribution without changing closure status.

Definition of done:

- Focused tests pin the attribution schema and conservative interpretation, helper outputs are stable, and TB-085 is removed from this backlog.

Boundaries: Do not change physics, tune parameters, run new validation, or convert attribution into acceptance/no-go status.

### TB-086: Summarize Same-Scale Ensemble Stability Frontier

Goal: Combine existing uncertainty, runtime, and output-size measurements into a bounded stability frontier for deciding whether another small probe would be informative.

Capability gap reduced: Uncertainty characterization and scalable execution planning.

Why this outranks alternatives: It uses existing artifacts to estimate marginal scientific value before spending runtime on another ensemble.

Inspect first:

- `scripts/summarize_same_scale_sampling_uncertainty.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- A JSON/text frontier summary relating compared trajectory counts, runtime/output footprint, and measured uncertainty deltas.
- A conservative recommendation class such as `additional_probe_informative`, `additional_probe_low_value`, or `blocked_pending_helper_contract`.
- Tests use fixtures or mocked summaries and do not require a new ensemble.

Definition of done:

- Frontier helper output is deterministic, command-plan or docs reference it where appropriate, focused tests pass, and TB-086 is removed from this backlog.

Boundaries: Do not run a new ensemble, authorize production scale-up, or change scientific closure criteria.

### TB-087: Extract Persistent Conditional Hazard Confidence Regions

Goal: Derive stable and unstable conditional-hazard interpretation regions from existing same-scale uncertainty and hazard-layer evidence.

Capability gap reduced: Scientific interpretability and uncertainty-aware product reading.

Why this outranks alternatives: It turns measured spatial uncertainty into user-facing confidence regions instead of another scalar status summary.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/build_hazard_layers.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- JSON/text summaries for persistent agreement, stable low-disagreement, shared-support magnitude-sensitive, and support/nodata-sensitive conditional hazard regions.
- Optional small GeoJSON/vector-style summary artifacts only in temporary or ignored output locations.
- Diagnostic interpretation names the regions as interpretive aids, not acceptance evidence.

Definition of done:

- Region extraction is deterministic on current artifacts or fixtures, focused tests pass, and TB-087 is removed from this backlog.

Boundaries: Do not create operational hazard zones, regulatory classes, risk/exposure products, or new simulation outputs.

### TB-088: Define Minimal Swiss Public-Geodata Workflow Contract

Goal: Specify the reusable public-geodata contract needed for any Swiss AOI before site-specific preprocessing, release planning, or hazard generation can proceed.

Capability gap reduced: Swiss-wide portability realism.

Why this outranks alternatives: Current second-site work is Chant Sura-specific; a minimal contract prevents new locations from inheriting Tschamut or Chant Sura assumptions.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A reusable contract summary for required AOI metadata, CRS/grid assumptions, swisstopo product classes, cache paths, provenance, and deferred optional context.
- Tests cover at least the existing Chant Sura fixture and a minimal synthetic AOI fixture.
- Docs distinguish public-geodata contract readiness from synthetic fixture readiness.

Definition of done:

- The contract can be emitted as JSON/text, focused tests pass, and TB-088 is removed from this backlog.

Boundaries: Do not download public data, stage fake public-context evidence, or run a second-site hazard build.

### TB-089: Add AOI-To-Prepared-Pilot Dry-Run Orchestrator

Goal: Chain existing AOI acquisition, public-context gate, release-zone dry-run, release-plan dry-run, and command-plan helpers into one dry-run workflow report.

Capability gap reduced: Workflow automation from user AOI toward prepared conditional pilot inputs.

Why this outranks alternatives: It reduces manual orchestration across already-existing helpers without pretending the missing downloads or evidence exist.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/plan_release_plan_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A dry-run orchestrator or command-plan group that reports ordered steps, blockers, expected inputs, and generated/ignored output roots for a candidate AOI.
- The report remains blocked/deferred when real public-context products are missing.
- Tests prove the dry run does not download data or run ensembles.

Definition of done:

- One command produces a deterministic AOI-to-prepared-pilot dry-run report for Chant Sura, focused tests pass, and TB-089 is removed from this backlog.

Boundaries: No data downloads, no second-site ensemble, no hazard build, no operational or physical-probability claim.

### TB-090: Generate Second-Site Conditional Case Skeleton

Goal: Produce a blocked, inspectable second-site case skeleton from the current Chant Sura contract without authorizing execution.

Capability gap reduced: Portable multi-site workflow realism and reproducibility.

Why this outranks alternatives: A case skeleton exposes exactly which real public-context and source/scenario fields remain missing before any second-site run can be valid.

Inspect first:

- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A dry-run case skeleton generator or command-plan step that emits a non-executable case draft to a temporary/ignored location.
- The skeleton clearly marks synthetic fixture fields, deferred public-context fields, and execution blockers.
- Tests verify the skeleton cannot be mistaken for an authorized run case.

Definition of done:

- The skeleton is generated and audited in dry-run mode, focused tests pass, and TB-090 is removed from this backlog.

Boundaries: Do not run validation or hazard generation for Chant Sura, do not claim public-context readiness, and do not commit generated private artifacts.

## Backlog Protocol

Task headings must always be exactly:

```markdown
### TB-XXX: Short Description
```

Do not put priority, status, owner, or tags in the heading. Use this schema for
every active task:

```markdown
### TB-XXX: Short Description

Goal: One sentence describing why the task matters now.

Capability gap reduced: The concrete capability gap this task reduces.

Why this outranks alternatives: One sentence explaining why this is high
leverage now.

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
