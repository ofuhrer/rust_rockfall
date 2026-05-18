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

### TB-263: Local Tiny AOI Hazard-Map Smoke Run

Goal: Execute a tiny local fixture-backed AOI prepared-pilot run through trajectory generation and hazard-layer building to prove the front-door workflow produces actual map artifacts.

Capability gap reduced: The AOI workflow needs an end-to-end executable smoke proof from prepared pilot to hazard rasters before larger Balfrin jobs are trusted.

Why this outranks alternatives: User experience depends on seeing a complete tiny map pipeline, not only a sequence of ready/blocked preparation reports.

Inspect first:

- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/check_hazard_output_profile.py`
- `tests/test_public_real_site_conditional_pilot_run.py`
- `tests/test_hazard_layers.py`
- `tests/fixtures/hazard/ensemble_case.yaml`

Deliverables:

- A local smoke mode or fixture that executes a tiny AOI command plan into an ignored or `/tmp` output root and produces reduced trajectory outputs plus hazard layers.
- Output assertions for required rasters, manifests, claim-boundary metadata, and no-heavy-debug defaults.
- Tests proving the smoke run is deterministic and clean-checkout safe.

Definition of done:

- The repository has a CI-scale end-to-end proof that an AOI prepared-pilot package can produce hazard-map artifacts.

Boundaries: Tiny local fixture execution only; no live Balfrin submission, no physical validation claim, no operational claim, and no generated heavy outputs committed.

### TB-264: Balfrin Target-Area Metrics Completion Postproc Run

Goal: Submit the exact bounded target-area metrics-completion rerun on Balfrin postprocessing nodes to close the missing execution-metrics gap.

Capability gap reduced: The current target-area demonstration still lacks peak memory and split validation/hazard output metrics in the preserved evidence chain.

Why this outranks alternatives: The decision helper ranks metrics completion first, and the user has authorized workers to execute on Balfrin postprocessing nodes for bounded tasks in this queue.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`

Deliverables:

- A live Balfrin postproc submission for the exact metrics-completion run root `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v2`, using the frozen target-area manifest and reduced-output preservation contract.
- Recorded SLURM job id, run root, command plan, logs, sacct fields, metrics JSON, and preservation-gate output.
- A blocked report instead of submission if access, checkout, package, or preservation preflight fails.

Definition of done:

- The metrics-completion run is either submitted and collected as measured evidence, or the exact preflight blocker is recorded without partial evidence promotion.

Boundaries: This task explicitly allows one bounded Balfrin `postproc` submission for the named metrics-completion run only; no retries without diagnosing the failed state, no multi-zone run, no distributed execution, no scale-up, no physical-probability semantics, and no operational claim.

### TB-265: Metrics Completion Evidence Integration And Decision Refresh

Goal: Integrate the TB-264 Balfrin run result into the canonical metrics report, preservation gate, evidence bundle, closure package, and next-action decision.

Capability gap reduced: A measured run only moves the project forward if the repository consumes it consistently and stops ranking metrics completion as the top unresolved action.

Why this outranks alternatives: This turns live execution into durable evidence rather than another unconnected run root.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `tests/test_balfrin_probe_metrics_report.py`
- `tests/test_balfrin_demonstration_closure_package.py`

Deliverables:

- Updated canonical reports or fixtures that classify the TB-264 result as measured, recovered, blocked, or incomplete.
- A refreshed next-action decision that ranks the smallest multi-zone measurement, AOI workflow work, physical evidence, or second-site staging after metrics completion.
- Tests proving incomplete TB-264 evidence remains blocked and complete evidence updates downstream decisions without claim upgrades.

Definition of done:

- The canonical Balfrin evidence state reflects the measured metrics-completion outcome and preserves all non-operational claim boundaries.

Boundaries: Evidence integration only; no additional live submission, no physical credibility upgrade, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.

### TB-266: Smallest Multi-Zone Handoff Budget Repair

Goal: Repair or tighten the smallest multi-zone handoff so its projected manifest, sidecar, and reducer budget can pass or fail with an actionable reason.

Capability gap reduced: The multi-zone path remains blocked by handoff-derived manifest/reducer pressure, preventing a measured many-release-zone Balfrin probe.

Why this outranks alternatives: Full Balfrin demonstration progress requires getting beyond single-zone comfort, but only after the smallest multi-zone handoff is inside measured budgets.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- A compact handoff projection or reduced sidecar mode that preserves replay-critical fields while lowering manifest/file-family pressure.
- Before/after budget report for the reviewed two-release-zone probe shape.
- Tests proving replay-critical metadata, sorted merge order, checksums, and output-profile semantics cannot be removed to pass the budget.

Definition of done:

- The smallest multi-zone handoff either reaches `ready_for_authorization_review` on budget grounds or reports the precise replay-critical budget field that remains a blocker.

Boundaries: Handoff budget repair only; no live Balfrin submission in this task, no loss of replayability, no distributed reducer, no physics change, no operational claim.

### TB-267: Smallest Multi-Zone Balfrin Postproc Probe

Goal: Submit the exact smallest bounded multi-zone Balfrin probe on postprocessing nodes once TB-266 and the authorization preflight are ready.

Capability gap reduced: The repository lacks measured many-release-zone Balfrin evidence, which is the next architectural step toward a fuller demonstration.

Why this outranks alternatives: After target-area metrics are closed and the smallest handoff budget is repaired, a measured two-zone probe is more informative than more dry-run packaging.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_authorization_gated_multi_zone_measurement_path.py`

Deliverables:

- A live Balfrin postproc submission for the exact smallest multi-zone run shape: 2 release zones, 2 scenarios, 1000 target trajectories, 2 trajectory workers, 2 reducer workers, 2 reducer chunks, summary-only conditional curves, no grid CSV export, and a deterministic run root under `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`.
- Recorded SLURM job id, command plan, reviewed handoff package hash, authorization record, metrics JSON, preservation gate, and post-run collector output.
- A blocked report if access, budget, authorization preflight, or preservation requirements fail before submission.

Definition of done:

- The project has either measured smallest multi-zone Balfrin evidence or a precise pre-submit blocker, with no partial run promoted as evidence.

Boundaries: This task explicitly allows one bounded Balfrin `postproc` submission for the named two-zone probe only; no retries without blocker analysis, no larger ensemble, no distributed execution, no annual-frequency or physical-probability semantics, no risk/exposure/vulnerability product, and no operational claim.

### TB-268: Multi-Zone Evidence Integration And Reducer Scaling Update

Goal: Integrate the TB-267 multi-zone result into reducer-pressure, evidence-bundle, closure, and Swiss-wide envelope helpers.

Capability gap reduced: Measured multi-zone evidence must update the scaling frontier and next-action decision rather than remain a detached run root.

Why this outranks alternatives: This is the step that converts a two-zone Balfrin run into actionable scaling evidence for larger Balfrin or Swiss AOI workflows.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A measured multi-zone reducer/output summary with file counts, manifest bytes, reducer wall time, merge-order proof, restart/replay metadata, and first bottleneck labels.
- Updated evidence and decision helpers that distinguish scratch, fixture-backed, and measured multi-zone Balfrin roots.
- Tests proving measured multi-zone evidence changes the scaling branch without authorizing larger runs automatically.

Definition of done:

- The scaling frontier reflects measured two-zone Balfrin evidence and names the next safe expansion or explicit no-go blocker.

Boundaries: Evidence integration only; no additional live run, no Swiss-wide authorization, no distributed execution, no operational claim, and no physical-probability semantics.

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
