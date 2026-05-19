# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.
Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

Capability filter: a task whose main deliverable is a report, gate, validator,
YAML record, checklist, or evidence package is acceptable only when it names the
specific command it unblocks, measurement it produces, workflow coupling it
removes, or stale surface it replaces. Otherwise the task should be rewritten as
bounded execution, recovery, automation, scaling measurement, real-evidence
acquisition, or consolidation of an existing helper.

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

Live Balfrin rule: a task may prepare, review, or preflight a Balfrin submission
package, but it may not submit a new live run unless the user gives an explicit
instruction for that exact run. The orchestrator must route any authorized live
run to a GPT-5.5 Balfrin worker and require the existing Balfrin access,
readiness, authorization, output-budget, preservation, and evidence gates. A
ready preflight, generated package, or backlog task is not authorization.

## Active Tasks

### TB-269: AOI Hazard Map Product Packager

Goal: Package AOI hazard-layer outputs into user-consumable GeoTIFF/COG, GeoJSON/GeoPackage, manifest, and text-summary artifacts.

Capability gap reduced: Producing hazard rasters is not enough; a user needs a coherent map package with provenance, layer semantics, and claim boundaries.

Why this outranks alternatives: The stated project goal is an actual hazard map workflow, so the output bundle has to be a first-class interface rather than scattered files.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `docs/hazard_map_semantics.md`
- `docs/hazard_output_profile_contract.md`
- `tests/test_gis_cog_package_readiness.py`
- `tests/test_same_scale_cog_package_conversion.py`

Deliverables:

- A map-packaging command or front-door subcommand that converts AOI hazard outputs into a compact package with COG rasters where supported, vector release/scenario overlays, layer inventory, checksums, and claim-boundary metadata.
- A `map_package_ready`, `cog_blocked`, or `blocked_missing_hazard_outputs` classification.
- Tests for fixture hazard outputs, missing layers, COG conversion failure, and manifest consistency.

Definition of done:

- A user can point at an AOI hazard output root and receive a reviewable map package rather than raw intermediate files.

Boundaries: Packaging only; no hazard-value change, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability product, and no heavy outputs committed.

### TB-270: AOI Map QA Project And Static Review Surface

Goal: Generate a lightweight QA surface for an AOI map package that overlays terrain, release zones, scenario metadata, hazard layers, and context availability.

Capability gap reduced: Users need to inspect whether the map is spatially coherent before interpreting or sharing a hazard product.

Why this outranks alternatives: Rapid AOI-to-map iteration needs visual QA; otherwise users must manually assemble layers in GIS tools and may miss provenance or scope warnings.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/measure_hazard_context_overlap.py`
- `scripts/summarize_balfrin_target_area_gis_cog_scope.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/hazard_map_semantics.md`
- `tests/test_pilot_gis_visual_qa.py`
- `tests/test_balfrin_target_area_gis_cog_scope.py`

Deliverables:

- A QA project generator that emits a QGIS project, static HTML index, or equivalent manifest-driven review surface under an ignored output root.
- Visible or machine-readable warnings for missing context layers, COG-blocked rasters, fixture-backed inputs, conditional-only weights, and non-operational status.
- Tests for layer presence, warning propagation, and blocked missing-map-package behavior.

Definition of done:

- A user can inspect the AOI hazard map package with release/scenario/context overlays and understand the current evidence boundaries.

Boundaries: QA/review surface only; no hazard-value changes, no operational claim, no physical-probability semantics, no regulatory-use claim, and no heavy outputs committed.

### TB-271: Adaptive AOI Ensemble Convergence Controller

Goal: Add a controller that escalates AOI trajectory counts in bounded steps until spatial convergence stabilizes or a runtime/output budget stops the run.

Capability gap reduced: Users should not have to choose arbitrary trajectory counts; the workflow needs a measured sufficiency loop for conditional diagnostic maps.

Why this outranks alternatives: A rapid AOI-to-map workflow is only useful if it can say whether the map is stable enough for diagnostic review or blocked by uncertainty/output pressure.

Inspect first:

- `scripts/compare_hazard_map_convergence.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/submit_balfrin_probe.py`
- `docs/hazard_output_profile_contract.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_hazard_map_convergence.py`
- `tests/test_balfrin_ensemble_frontier.py`

Deliverables:

- An adaptive convergence plan that proposes trajectory-count increments, expected output budgets, stop criteria, and local versus Balfrin execution mode.
- A fixture-backed local loop and a Balfrin-ready command plan for bounded postproc escalation when preflights pass.
- Tests for converged, budget-stopped, and inconclusive branches.

Definition of done:

- The workflow can recommend or execute the next bounded trajectory-count step based on measured convergence and output budget rather than fixed guesses.

Boundaries: Conditional convergence only; Balfrin submission may be prepared but not run in this task unless explicitly scoped by a later task, no annual-frequency semantics, no physical validation claim, and no operational claim.

### TB-272: End-To-End AOI-To-Map Regression Fixture

Goal: Add a compact regression fixture that exercises the entire user-facing path from AOI manifest through prepared inputs, reviewed release/scenario plan, local smoke execution, hazard-layer build, map packaging, and QA summary.

Capability gap reduced: The project needs a durable proof that the front-door workflow stays usable as individual helpers evolve.

Why this outranks alternatives: Without an end-to-end regression, improvements to one helper can silently break the user journey from AOI definition to hazard map.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_public_real_site_conditional_pilot_run.py`
- `tests/test_hazard_layers.py`

Deliverables:

- A small fixture-backed end-to-end test or smoke helper that runs under `/tmp` and asserts the expected command states, output manifests, hazard layers, map-package metadata, and claim-boundary fields.
- A single failure summary that names the first broken workflow step for users and agents.
- Documentation or README update only if needed to point users at the regression-backed command path.

Definition of done:

- The repository has one maintained, clean-checkout-safe proof that the AOI-to-map workflow can produce a map package on tiny inputs.

Boundaries: Fixture-backed regression only; no live Balfrin submission, no real public-geodata download, no operational claim, and no heavy outputs committed.

### TB-273: Optional Observed-Evidence Overlay Hook For AOI Maps

Goal: Allow an AOI hazard map package to include optional observed runout/deposition or release-zone provenance overlays when real accepted evidence is staged.

Capability gap reduced: Scientific credibility remains separate from workflow execution, but users need a clean path to attach observed evidence to a map package without turning it into calibration or annual-frequency semantics.

Why this outranks alternatives: This connects the physical-evidence intake machinery to the user-facing map workflow while preserving the project's strict claim boundaries.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/hazard_map_semantics.md`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `tests/test_physical_credibility_evidence_requirements.py`

Deliverables:

- A map-package overlay hook that accepts only real-input-ready observed evidence or field-supported release-zone provenance, and otherwise emits `blocked_missing_evidence`, `blocked_fixture_only_inputs`, or `blocked_schema_gap`.
- Manifest fields that distinguish diagnostic hazard outputs, observed evidence overlays, calibration inputs, holdout evidence, and deferred source-frequency records.
- Tests proving fixture-only or ambiguous-role evidence cannot appear as accepted physical validation in the map package.

Definition of done:

- AOI map packages can carry optional real observed-evidence overlays without implying calibration, physical probability, annual frequency, risk, or operational readiness.

Boundaries: Optional overlay integration only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no operational claim, and no claim upgrade beyond accepted evidence.

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
leverage now, preferably tied to a measured blocker, an executable workflow
boundary, real evidence acquisition, output/runtime scaling, or simplification
of duplicated orchestration.

Inspect first:

- `path/or/script.py`

Deliverables:

- Concrete executable, analysis, test, or measured output. If the deliverable is
  mainly a report, gate, validator, checklist, or package, state the exact run,
  recovery, acquisition, reproducibility, or consolidation action it enables.

Definition of done:

- Focused checks pass, the capability outcome is explicit, and the task is
  removed from this backlog only when the definition of done is genuinely met.
  A new blocked/deferred classification is not enough unless it eliminates a
  real ambiguity and names the next unblock action or explicit deferral.

Boundaries: No live Balfrin submission, tuning, operational claims, scale-up
authorization, or other phase changes unless the task explicitly allows them
and, for live Balfrin submission, the user has separately authorized the exact
run.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read only the selected task and its `Inspect first` files unless the task
explicitly requires broader context. Use `--detail full` on the task-context
helper only for orchestrator/review work.

Keep worker prompts compact: include the selected task body and essential
pitfalls only. Redirect large JSON, diffs, and logs to `/tmp`, summarize the
result, preserve the final relevant error block when a command fails, and
finish with the compact structured report schema:
`TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
`PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.

For `STATUS`, distinguish `implemented_measured`,
`implemented_fixture_backed`, `implemented_blocked_report`,
`blocked_unresolved`, and `partial_needs_followup` when relevant. A blocked
report or fixture-backed proof is not the same as measured execution; leave or
add the smallest unblock task before dependent synthesis work.

Before commit, run the task-specific checks, `git diff --check`, repository
consistency, `scripts/git-hooks/pre-commit`, and the placeholder-artifact scan.

Do not keep completed tasks here. Use `agent_work_log.md` for chronological TB
execution history and `decision_log.md` for durable decisions.
