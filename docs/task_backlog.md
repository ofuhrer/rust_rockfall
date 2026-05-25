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

Live Balfrin rule: the user has granted standing clearance for GPT-5.5 workers
to submit and actively monitor jobs on Balfrin's `postproc` partition. Multiple
concurrent `postproc` jobs are allowed, including filling the partition. If the
work would keep the `postproc` partition fully busy for more than 6 hours, stop
and rediscuss. Submission still requires the relevant access, readiness,
authorization-record/audit, output-budget, preservation, and evidence gates to
pass. This clearance does not authorize non-postproc partitions, distributed
execution, scale-up claims, or scientific/operational claim upgrades.

## Active Tasks

### TB-546: Make Rebuildable Reduced Output The Default Local Hazard Smoke Recommendation

Goal: Steer local hazard smoke and replay recommendations toward rebuildable reduced outputs by default.

Capability gap reduced: Reduces local output-volume drift while preserving reproducibility through rebuild instructions.

Why this outranks alternatives: Output pressure is already a scaling bottleneck, and default local recommendations should avoid producing heavy artifacts unnecessarily.

Inspect first:

- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/hazard_output_profile_contract.md`
- `tests/test_hazard_rebuild_output_profile.py`

Deliverables:

- Update existing command-plan or output-profile surfaces so local smoke/replay guidance prefers the rebuildable reduced profile when scientifically sufficient.
- Add focused tests that preserve access to fuller outputs when explicitly requested.

Definition of done:

- Local command guidance names the reduced rebuildable profile, the rebuild command or metadata needed to recover full outputs, and the focused tests pass.

Boundaries: No deletion of existing artifacts, no forced behavior change for heavy runs, no new output contract, and no claim that reduced output is always sufficient.

### TB-547: Add Local GIS/COG Package Roundtrip Smoke On Tiny Fixture

Goal: Prove that a tiny local same-scale package can be converted and audited as GIS/COG-ready without large artifacts.

Capability gap reduced: Moves GIS handoff readiness from static checks toward an executable local roundtrip.

Why this outranks alternatives: GIS package usability is a user-facing validation frontier and can be tested cheaply on tiny fixtures.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/prototype_cog_conversion.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `tests/test_cog_conversion_prototype.py`
- `tests/test_same_scale_cog_package_conversion.py`

Deliverables:

- Add or tighten a tiny fixture-backed conversion-plus-audit path using existing COG helpers.
- Ensure the output reports both conversion success and any missing GIS metadata needed for user-facing use.

Definition of done:

- Focused COG conversion/audit tests pass and the roundtrip can run locally without large rasters or external services.

Boundaries: Tiny fixtures only; no QGIS automation, no publishing, no new GIS package format, and no operational map claim.

### TB-548: Strengthen Multisite Source/Scenario Portability Checks

Goal: Make multisite audits distinguish portable source/scenario semantics from site-specific assumptions.

Capability gap reduced: Reduces the risk that Tschamut-specific scenario assumptions silently contaminate Chant Sura or future sites.

Why this outranks alternatives: Multisite scientific validation depends on knowing which assumptions travel and which must be restated per site.

Inspect first:

- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_multisite_source_scenario_contract.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- Update existing audit or command-plan output to name portable fields, site-specific fields, and the next local fixture/staging action for missing semantics.
- Add focused tests for at least one portable and one site-specific field.

Definition of done:

- The multisite audit gives an actionable local result without requiring Balfrin and focused tests pass.

Boundaries: No new contract file unless consolidation requires it, no new site onboarding, no live data acquisition, and no validation claim upgrade.

### TB-549: Add Observed-Evidence Intake Acceptance Smoke

Goal: Exercise accepted and rejected observed runout/deposition evidence packages locally and explain why accepted intake is not yet validation evidence.

Capability gap reduced: Clarifies the boundary between evidence ingestion and scientific validation.

Why this outranks alternatives: Observed evidence intake is essential for validation, but premature interpretation would create false scientific confidence.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `tests/fixtures/observed_runout_deposition_intake_contract/accepted_fixture.yaml`

Deliverables:

- Add or tighten fixture-backed acceptance and rejection cases in the existing intake summary/tests.
- Ensure accepted intake output explicitly states the remaining validation or calibration evidence gap.

Definition of done:

- Focused intake tests pass and the local intake command reports accepted/rejected evidence packages plus the missing validation step.

Boundaries: No new observed dataset, no calibration, no validation claim, no annual-frequency claim, and no new intake framework.

### TB-550: Consolidate Local Scientific Recommendation Output Into Next Executable Commands

Goal: Make the local scientific backlog recommendation report map each top local follow-up to an exact executable command and expected measurement.

Capability gap reduced: Turns local scientific prioritization into concrete execution guidance for the next autonomous worker.

Why this outranks alternatives: The repo already has many local diagnostics; the highest leverage is making the next command unambiguous without adding more files.

Inspect first:

- `scripts/recommend_local_scientific_backlog.py`
- `scripts/lib/local_scientific_progress.py`
- `tests/test_local_scientific_backlog_recommendation.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Update existing recommendation output so each ranked local scientific follow-up includes one executable command and the measurement or artifact it should produce.
- Add focused tests that guard against recommendations with no next command.

Definition of done:

- The recommendation command passes focused tests and its top local-only entries are directly executable from the repository checkout.

Boundaries: No new roadmap document, no new backlog generator, no Balfrin dependency, no claim upgrade, and no placeholder commands.

### TB-551: Make Balfrin Decision Helpers Clean-Checkout Safe

Goal: Make the Balfrin scale-readiness and next-live-run decision helpers fail closed instead of crashing when scratch reducer-pressure artifacts are absent.

Capability gap reduced: Removes hidden local-state coupling from the main Balfrin decision surface.

Why this outranks alternatives: A review run currently fails on missing `/private/tmp` reducer-pressure roots, so the next live probe cannot be planned reproducibly from a clean checkout.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Convert missing scratch-root reducer artifacts into explicit blocked inputs with the exact regeneration command.
- Add focused tests that simulate absent `/tmp` roots.

Definition of done:

- Both decision helpers emit deterministic blocked JSON from a clean checkout and focused tests pass.

Boundaries: No new live run, no silent fixture substitution, no scale-up claim, no distributed execution.

### TB-552: Regenerate Reducer-Pressure Scratch Roots Deterministically

Goal: Provide a deterministic command path that rematerializes the reducer-pressure scratch roots required by Balfrin scale planning.

Capability gap reduced: Makes reducer-pressure evidence reproducible instead of depending on stale `/tmp` state.

Why this outranks alternatives: TB-551 can make missing roots fail closed, but planning still needs a cheap way to rebuild the scratch evidence.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `tests/test_multi_zone_reducer_pressure.py`
- `tests/test_multi_zone_reducer_pressure_gate.py`

Deliverables:

- Add or document an existing command that materializes the needed compact reducer-pressure roots under a caller-supplied scratch root.
- Report the generated manifest paths and byte/file counts.

Definition of done:

- A focused test proves the scratch roots can be regenerated in `/tmp` and then consumed by the reducer-pressure gate.

Boundaries: Local scratch generation only; no Balfrin submission, no large ensemble, no distributed execution.

### TB-553: Sync The Balfrin Remote Checkout To A Reviewed Commit

Goal: Align the Balfrin remote checkout with the reviewed repository commit before any further package or submission work.

Capability gap reduced: Removes stale remote-head mismatch from Balfrin package readiness.

Why this outranks alternatives: Read-only access is back, but package generation has recently failed closed when the Balfrin remote HEAD lagged behind the local package source.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `docs/orchestration_strategy.md`
- `tests/test_balfrin_regional_split_submission_package.py`

Deliverables:

- Run the remote access preflight, update the remote clone only by a safe fast-forward path if possible, and rerun the preflight.
- Record before/after remote HEAD and any remaining remote hygiene blockers.

Definition of done:

- The Balfrin access preflight reports a clean remote checkout with documented head alignment, or it fails closed with exact operator recovery commands.

Boundaries: Remote git hygiene only; no `sbatch`, no generated artifact deletion beyond documented stale checkout cleanup, no live run.

### TB-554: Recompute Balfrin Decision Gate After Access And Scratch Repair

Goal: Recompute the next-live-run decision gate after clean-checkout and Balfrin remote-head blockers are resolved.

Capability gap reduced: Restores one current downstream decision surface for the next executable Balfrin action.

Why this outranks alternatives: The current decision gate should be rerun only after the helper no longer crashes and the remote checkout is aligned.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`
- `tests/test_balfrin_management_demo_package.py`

Deliverables:

- Updated decision/demo outputs that name the next executable action and exact remaining blockers.
- Focused regression coverage for the current reducer-first ranking.

Definition of done:

- The decision gate and management demo package run from a clean local state and reflect current access, reducer, scenario, replay, and candidate evidence.

Boundaries: Decision refresh only; no live submission, no operational claim, no scale-up authorization beyond existing postproc rules.

### TB-555: Compare Measured Regional Split Against Scenario And Output Projections

Goal: Thread measured regional split evidence into scenario-cardinality and output-tier projection surfaces.

Capability gap reduced: Replaces stale projection-only scale recommendations with measured regional-split comparison evidence.

Why this outranks alternatives: The regional split branch is now measured, but the projection surfaces still need measured deltas before another live recommendation.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_regional_gis_cog_pressure.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Existing scale/projection outputs distinguish measured regional split evidence from projection-only and failed-closed branches.
- A refreshed recommendation names the next measured run candidate or blocker.

Definition of done:

- Focused scale/projection tests pass and no new dashboard/report script is added.

Boundaries: Evidence comparison only; no new live run, no Swiss-wide authorization, no physical-probability or annual-frequency semantics.

### TB-556: Build The Next Reduced-Output Balfrin Probe Handoff

Goal: Generate the next bounded Balfrin probe handoff using reduced-output defaults and current scenario/reducer limits.

Capability gap reduced: Converts decision-surface evidence into a concrete reviewed handoff without immediately submitting.

Why this outranks alternatives: A live run should be launched only from a current reviewed package that already encodes output and reducer pressure constraints.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- A no-submit handoff package with exact command, ignored roots, output mode, reducer limits, and claim boundaries.
- A focused test proving the handoff remains no-submit until the submit gate is explicitly invoked.

Definition of done:

- The package is ready for review or fails closed with one blocker and recovery command.

Boundaries: No `sbatch`, no scale-up claim, no distributed execution, no operational semantics.

### TB-557: Execute The Next Bounded Balfrin Postproc Probe

Goal: Run the next repository-gated bounded Balfrin `postproc` probe if all access, package, output-budget, and preservation gates pass.

Capability gap reduced: Converts readiness into measured execution evidence.

Why this outranks alternatives: Management needs measured feasibility evidence for the next bounded step, but only after the reviewed package and gates are current.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Submit and actively monitor one bounded `postproc` job only if gates are ready.
- Preserve the run root and collect runtime, memory, file-count, byte-count, reducer, and manifest metrics.

Definition of done:

- Either one bounded `postproc` run completes with preserved measured evidence, or the attempt fails closed before submission with a concrete blocker and smallest next unblock action.

Boundaries: `postproc` only under existing clearance; stop if expected partition saturation exceeds 6 hours; no non-postproc partition, distributed execution, operational claim, annual-frequency claim, or physical-probability claim.

### TB-558: Collect And Promote The Next Probe Evidence

Goal: Integrate the latest completed bounded Balfrin probe into the existing evidence bundle and preservation surfaces.

Capability gap reduced: Prevents measured run evidence from remaining only as raw remote artifacts.

Why this outranks alternatives: A successful run is not useful for planning until metrics, output budgets, and preservation status are collected and surfaced.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Updated local reports that classify the new run root as measured, failed-closed, or blocked.
- Runtime/output/reducer metrics are separated from scientific claim boundaries.

Definition of done:

- The evidence bundle and interpretation gate consume the new run-root metrics or fail closed with exact missing artifacts.

Boundaries: Evidence collection only; no rerun, no operational claim, no physical validation claim.

### TB-559: Refresh Swiss-Scale Feasibility Projection From Latest Measured Evidence

Goal: Update the Swiss-scale feasibility projection using the latest measured bounded-run evidence and current output/reducer pressure.

Capability gap reduced: Turns measured Balfrin evidence into a management-useful feasibility answer.

Why this outranks alternatives: Management needs to know whether Swiss-scale remains plausible, conditional, or out of reach under current single-node/postproc constraints.

Inspect first:

- `docs/swiss_scale_feasibility_projection.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Updated projection text and any existing helper output needed to support it.
- Explicit separation of measured, projection-only, failed-closed, and deferred evidence.

Definition of done:

- The projection names the current practical ceiling, first bottleneck, and next measurable step without authorizing Swiss-wide execution.

Boundaries: Projection only; no Swiss-wide run, no operational claim, no distributed execution phase change.

### TB-560: Consolidate Duplicate Balfrin Decision Logic

Goal: Reduce duplication between scale-readiness, next-live-run decision, and management-demo package logic.

Capability gap reduced: Lowers workflow-shell complexity and reduces stale recommendation drift.

Why this outranks alternatives: Recent decision surfaces have drifted and crashed in different ways; consolidation should remove logic, not add another wrapper.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Extract or reuse one shared ranking/evidence function for the overlapping next-action logic.
- Delete or reduce duplicated constants or stale follow-up IDs where possible.

Definition of done:

- Focused tests pass and the diff removes more duplicated decision text or branches than it adds.

Boundaries: No new top-level report, no behavior broadening beyond current evidence, no claim upgrade.

### TB-561: Add A Clean-Checkout AOI Workflow Smoke Regression

Goal: Ensure the user-facing AOI workflow can run its smallest local smoke path without ignored artifacts.

Capability gap reduced: Protects onboarding and user-facing workflow reliability from hidden local-state assumptions.

Why this outranks alternatives: A clean checkout must be able to demonstrate the workflow without private Tschamut/Balfrin roots.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `README.md`

Deliverables:

- A focused clean-checkout-safe smoke test or helper mode using tracked tiny fixtures.
- README command remains accurate and bounded.

Definition of done:

- The smoke path writes reduced local artifacts under `/tmp` and does not require ignored roots.

Boundaries: Tiny fixture only; no real geodata download, no Balfrin, no operational map claim.

### TB-562: Measure Real-AOI Public-Geodata Acquisition Dry Run

Goal: Exercise the public-geodata acquisition/staging dry-run path for a real AOI without downloading or claiming readiness.

Capability gap reduced: Moves Swiss-wide portability from fixture semantics toward real AOI acquisition planning.

Why this outranks alternatives: Public-geodata acquisition and staging remain the largest practical gap before arbitrary target-area preparation.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A deterministic dry-run manifest listing required swisstopo products, expected staging roots, missing inputs, and next acquisition actions for one real AOI.
- Focused tests or fixture assertions for blocked/no-download behavior.

Definition of done:

- The dry-run command produces an actionable blocked/acquisition report without using synthetic fixtures as evidence.

Boundaries: No downloads unless explicitly authorized later, no second-site ensemble, no operational or validation claim.

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

Boundaries: No tuning, operational claims, scale-up authorization, non-postproc
Balfrin submission, distributed execution, or other phase changes unless the
task explicitly allows them. Postproc Balfrin submissions are covered by the
standing live Balfrin rule above and still require GPT-5.5 routing, active
monitoring, and passing repository gates.
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
