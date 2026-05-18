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

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

## Active Tasks

### TB-244: Post-Metrics Balfrin Demonstration Closure Refresh

Goal: Recompute the Balfrin demonstration closure package after target-area metrics are complete or explicitly unrecoverable, and produce the next measured-action recommendation from that updated state.

Capability gap reduced: The current closure package is blocked by no new measured evidence and cannot yet answer whether the target-area demonstration evidence is complete enough to move on.

Why this outranks alternatives: A closure refresh should happen only after the metrics gap is resolved or formally deferred; otherwise it repeats known blocked synthesis.

Inspect first:

- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_target_area_interpretation.py`
- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- A refreshed closure report that distinguishes `metrics_complete`, `metrics_unrecoverable_deferred`, and `blocked_no_new_measured_evidence`.
- A separate target-area spatial-artifact classification from TB-243 so missing spatial products do not masquerade as missing execution metrics.
- A ranked next-action recommendation after metrics completion: smallest multi-zone measurement, physical-evidence acquisition, second-site staging, or deferral.
- Tests proving closure remains blocked when no new measured or recovered metrics are supplied.

Definition of done:

- Reviewers can see whether the Balfrin target-area demonstration is evidence-complete at the execution-metrics level and which next action is justified.

Boundaries: Synthesis only; no live execution, no physical-credibility upgrade, no annual-frequency semantics, no operational claim, and no replacement of source evidence reports.

### TB-245: Current Multi-Zone Handoff Budget Recheck

Goal: Recompute the smallest multi-zone handoff budget after command-plan contract consolidation before attempting manifest pruning.

Capability gap reduced: The current multi-zone budget blocker may be stale after recent command-plan consolidation, and reducing manifests before remeasurement risks optimizing against outdated evidence.

Why this outranks alternatives: A no-change recheck is cheaper and more scientifically honest than assuming reduction work is necessary.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/lib/command_plan_contract.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- A refreshed fixture-backed budget report for the current handoff projection, including manifest bytes, sidecar bytes, file counts, reducer constraints, and replay-critical field inventory.
- A deterministic recommendation of `budget_passes_no_reduction_needed`, `blocked_budget_reduction_needed`, or `blocked_replay_contract_ambiguity`.
- Tests proving the recheck consumes the shared command-plan contract and does not mutate handoff semantics.

Definition of done:

- The repo can say whether manifest reduction is still needed using current handoff semantics and current budget thresholds.

Boundaries: Measurement/recheck only; no pruning, no live Balfrin job, no output-schema change, no distributed reducer, no scale-up claim, and no operational claim.

### TB-246: Multi-Zone Handoff Manifest Budget Reduction

Goal: If TB-245 still reports budget pressure, reduce the smallest multi-zone handoff's projected manifest and sidecar pressure without losing replay-critical fields.

Capability gap reduced: The smallest multi-zone path is blocked not only by authorization but also by reducer/manifest pressure in the reviewed handoff projection.

Why this outranks alternatives: A full-scale Balfrin demonstration cannot advance beyond single-zone comfort until the smallest many-zone handoff stays inside measured reducer and file-family budgets, but pruning is only justified after current-budget remeasurement.

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

- A blocked `budget_passes_no_reduction_needed` branch when TB-245 shows the current handoff already fits the budget.
- A bounded compact-manifest or manifest-pruning mode for the handoff projection that preserves replay-critical fields, hashes, merge order, and provenance.
- Before/after fixture-backed budget measurements for manifest bytes, sidecar bytes, file counts, and reducer constraints.
- Fail-closed tests proving replay-critical fields cannot be removed to satisfy the budget.

Definition of done:

- The smallest multi-zone handoff either passes the current budget gate with preserved replayability or reports the exact manifest fields that make it impossible.

Boundaries: Handoff/projection mechanics only; no live Balfrin job, no loss of replay metadata, no distributed reducer, no physics change, no generated heavy outputs committed, and no operational claim.

### TB-247: Smallest Multi-Zone Authorization Preflight Recheck

Goal: Re-run and refresh the smallest multi-zone authorization preflight after the current budget is rechecked and any needed manifest-budget reduction work is complete.

Capability gap reduced: The multi-zone route needs a current go/no-go classification after budget changes before anyone considers a live authorization request.

Why this outranks alternatives: A stale blocked preflight could hide that the smallest multi-zone measurement is now reviewable, or could let a still-blocked package proceed toward authorization.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/rehearse_balfrin_post_run_evidence_collector.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A refreshed preflight report with access status, reviewed package hash, authorization-record status, reducer-budget status, output-profile status, and exact smallest run shape.
- A deterministic branch for `ready_for_authorization_review`, `blocked_missing_authorization`, `blocked_reducer_budget`, and `blocked_access`.
- Tests proving the preflight consumes the current or compacted handoff budget and remains explicit that it does not grant authorization.

Definition of done:

- The repo has a current, machine-readable preflight answer for the smallest multi-zone Balfrin measurement.

Boundaries: Preflight only; no live submission, no authorization grant, no scale-up claim, no distributed execution, and no operational claim.

### TB-248: Authorization-Gated Smallest Multi-Zone Measurement Evidence Path

Goal: Prepare the post-authorization execution and evidence-collection path for the smallest multi-zone Balfrin measurement if TB-247 reaches `ready_for_authorization_review`.

Capability gap reduced: The project has dry-run multi-zone scaffolding but still lacks a measured many-release-zone Balfrin evidence record.

Why this outranks alternatives: Once metrics completion and preflight blockers are addressed, the smallest measured multi-zone run is the next architectural step toward the full Balfrin demonstration.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/rehearse_balfrin_post_run_evidence_collector.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- An authorization-gated execution checklist that binds the exact preflight output, reviewed handoff package, authorization record, submit command, run root, collector command, and closure-package input.
- Fixture-backed tests proving incomplete run roots, missing authorization, and access loss cannot be promoted to measured evidence.
- A blocked report when TB-247 is not ready or when explicit live-run authorization is absent.

Definition of done:

- A future authorized multi-zone measurement has a deterministic path from authorization through collection and closure input, without allowing accidental submission or evidence promotion.

Boundaries: No live execution unless explicitly authorized by the user, no distributed execution, no scale-up authorization, no physical-probability claim, no operational claim, and no generated heavy outputs committed.

### TB-249: Chant Sura Real Core-Input Staging Verification

Goal: Convert the Chant Sura / Fluelapass real-context gate from fixture-ready scaffolding toward real-input readiness by verifying whether locally staged terrain metadata, AOI tile catalog, source-zone metadata, scenario table, and policy records exist and are non-synthetic.

Capability gap reduced: Second-site portability remains blocked because the current candidate has fixture-backed core readiness but missing or deferred real public-context products and metadata.

Why this outranks alternatives: A second-site prepared pilot is the next portability milestone, but it must start with real staged core inputs rather than synthetic fixtures or downloads.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `tests/test_chant_sura_real_context_readiness_gate.py`

Deliverables:

- A stricter real-core-input classification that separates real staged files, fixture-backed files, metadata mismatches, missing rows, and deferred public-context products.
- A no-download verifier report naming the first non-synthetic missing input and the exact path or metadata field needed.
- Focused tests for fixture-backed blocked, partial-real, metadata-mismatch, and ready-real-core classifications.

Definition of done:

- The Chant Sura gate can tell whether real core inputs, not just fixture scaffolding, are ready for a prepared-pilot dry run.

Boundaries: No downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, no physical-validation claim, and no generated heavy outputs committed.

### TB-250: Chant Sura Missing-Input Acquisition Handoff

Goal: If TB-249 reports missing real core inputs, produce one no-download acquisition/staging handoff that names the exact files, metadata fields, and authorization decisions needed before a real-input dry run.

Capability gap reduced: Second-site portability can otherwise stall after a verifier report without a concrete next operator action.

Why this outranks alternatives: A blocked verifier is useful only if it points to a bounded acquisition path rather than another fixture-backed dry run.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A no-download handoff report for the first missing real core-input category, with expected source product, local path, metadata contract, and authorization/defer status.
- A deterministic recommendation of `ready_no_handoff_needed`, `stage_local_existing_input`, `request_download_authorization`, or `defer_second_site`.
- Tests for ready-real-core, missing terrain metadata, missing AOI tile catalog, and missing source/scenario/policy records.

Definition of done:

- A worker or operator can see the next concrete Chant Sura acquisition/staging action without treating fixtures as public evidence.

Boundaries: Handoff only; no downloads, no second-site ensemble, no generated heavy outputs committed, no physical-validation claim, and no operational claim.

### TB-251: Real-Input Chant Sura Prepared-Pilot Dry Run

Goal: Run the AOI-to-prepared-pilot dry-run path for Chant Sura only when TB-249 reports real staged core inputs, otherwise emit a deterministic blocked report.

Capability gap reduced: The repo needs a real-input second-site workflow proof before it can claim portability beyond the current primary demonstration site.

Why this outranks alternatives: This moves second-site work from acquisition planning into executable workflow evidence while preserving fail-closed boundaries.

Inspect first:

- `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`

Deliverables:

- A real-input prepared-pilot dry-run report with terrain, source-zone, scenario, command-plan, ignored-root, and blocked public-context classifications.
- A `blocked_missing_real_core_inputs` report when TB-249 is not ready, with a pointer to the TB-250 acquisition handoff when applicable.
- Tests proving fixture-backed inputs cannot produce a ready second-site classification.

Definition of done:

- Chant Sura can either produce a real-input prepared-pilot dry-run package or state exactly why it remains blocked, without representing fixtures as public evidence.

Boundaries: Dry run only; no downloads, no ensemble execution, no synthetic evidence claim, no physical-validation claim, no operational claim, and no generated heavy outputs committed.

### TB-252: Observed Benchmark Candidate Acquisition Triage

Goal: Identify one concrete candidate path for real observed runout/deposition benchmark evidence, or produce a precise blocked acquisition report if no candidate can be staged.

Capability gap reduced: The largest scientific gap remains physical credibility, and the current observed-intake machinery is schema-ready but lacks real benchmark inputs.

Why this outranks alternatives: Execution metrics and multi-zone scaling do not establish scientific credibility; the next scientific step is acquiring or explicitly failing to acquire independent observed evidence.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/validation_data_schema.md`
- `docs/public_benchmark_framework.md`
- `tests/test_observed_runout_deposition_intake_contract.py`

Deliverables:

- A candidate-acquisition report listing available local candidates, required external acquisition actions, licensing/provenance blockers, and first missing geometry/provenance/uncertainty fields.
- A recommendation of `stage_candidate`, `blocked_no_candidate`, `blocked_license_or_provenance`, or `defer_scientific_claim`.
- Tests for local candidate present, no candidate, and candidate missing uncertainty/provenance cases.

Definition of done:

- A worker can act on one real observed-evidence candidate or see exactly why the physical-evidence path remains blocked.

Boundaries: Acquisition triage only; no downloads unless separately authorized, no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or risk semantics, and no operational claim.

### TB-253: First Real Observed Benchmark Intake Integration

Goal: If TB-252 identifies and stages a real observed benchmark candidate, integrate it through the observed runout/deposition intake contract while keeping calibration and claim boundaries explicit.

Capability gap reduced: Physical credibility cannot improve until a real observed benchmark package passes the intake contract and is separated from calibration and holdout roles.

Why this outranks alternatives: A successful real intake would move the scientific evidence base more than another workflow report; a failed intake would still clarify the exact evidence blocker.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_observed_runout_deposition_intake_contract.py`

Deliverables:

- A real-input intake report with geometry, provenance, uncertainty, calibration-role, validation-role, and holdout-eligibility classifications.
- A physical-credibility gap update that remains `not_established` unless the evidence genuinely satisfies the required intake boundary.
- Rejection tests for missing geometry, missing provenance, missing uncertainty, ambiguous calibration role, and fixture-only inputs.

Definition of done:

- The repo can accept or reject one real observed benchmark package deterministically, and any accepted intake is not confused with calibration, annual-frequency, or operational validation.

Boundaries: Intake only; no calibration, no parameter fitting, no source-frequency semantics, no annual-frequency or risk semantics, no operational claim, and no claim upgrade beyond what the accepted evidence supports.

### TB-254: Release-Zone, Block-Population, And Source-Frequency Evidence Triage

Goal: Triage the next real-evidence acquisition blockers for field-supported release zones, block-population evidence, and source-frequency records without implementing physical probability semantics.

Capability gap reduced: Observed runout intake alone does not close the physical-credibility gap; release provenance, block-population, and source-frequency evidence remain separate missing inputs.

Why this outranks alternatives: The repository has already built blocker fields for these categories, but it still lacks a concrete candidate acquisition path or defer decision for each.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_validation_calibration_evidence_gaps.py`
- `tests/test_physical_credibility_evidence_requirements.py`

Deliverables:

- A triage report with separate candidate/defer classifications for field-supported release-zone provenance, block-population evidence, and source-frequency records.
- Explicit first-missing-input fields for each category, preserving the distinction from conditional scenario weights.
- Tests proving conditional sampling weights are not reported as source-frequency evidence and fixture-backed provenance is not promoted to field-supported evidence.

Definition of done:

- The physical-evidence roadmap has concrete next acquisition or deferral actions for release-zone, block-population, and source-frequency evidence without changing the scientific claim level.

Boundaries: Acquisition triage only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no physical-probability claim, no risk/exposure semantics, and no operational claim.

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

- Focused checks pass, the capability outcome is explicit, and the task is
  removed from this backlog only when the definition of done is genuinely met.

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
