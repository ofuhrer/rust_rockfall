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

### TB-222: Balfrin Next Measured Action Decision Refresh

Goal: Refresh the Balfrin next-action decision matrix using post-TB-221 evidence before any worker prepares a live-run request or optimization task.

Capability gap reduced: The project needs a current, evidence-ranked choice among target-area metrics completion, smallest multi-zone measurement, second-site progress, physical-evidence acquisition, and hazard-builder optimization.

Why this outranks alternatives: A stale decision gate would let execution momentum choose the next Balfrin step instead of measured blockers, SSH availability, and scientific value.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Updated deterministic decision helper or fixture data that includes TB-217 through TB-221 evidence.
- A ranked recommendation that explicitly distinguishes measured, fixture-backed, blocked, unavailable, unauthorized, and SSH-access-expired paths.
- Focused tests for metrics-completion, multi-zone, Balfrin-access-blocked, and defer-to-physical-or-portability branches.

Definition of done:

- The decision output names the recommended next measured action, the exact blocker for each non-selected action, and the boundary that prevents claim upgrades.
- Focused tests pass and the task is removed only after the updated recommendation is reproducible.

Boundaries: No live Balfrin submission, no authorization grant, no new maturity label, no operational claim, and no fabricated metrics.

### TB-223: Balfrin SSH And Remote Artifact Access Preflight

Goal: Add a read-only Balfrin access preflight that checks SSH availability, expected clone path, non-git run-root visibility, and scheduler query reachability without launching jobs.

Capability gap reduced: Balfrin-capable workers need a fail-closed way to distinguish expired SSH access, missing remote artifacts, missing non-git data, and actual execution blockers.

Why this outranks alternatives: Remote evidence and live-run tasks should not start until access and artifact availability are machine-readable.

Inspect first:

- `docs/balfrin_probe_slurm_driver.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/orchestration_strategy.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `tests/test_balfrin_probe_driver.py`

Deliverables:

- A read-only helper or preflight mode that reports `ready_for_read_only_collection`, `blocked_ssh_unavailable`, `blocked_missing_remote_clone`, `blocked_missing_run_root`, or `blocked_scheduler_unavailable`.
- Exact remote paths and commands checked, with no secrets or private SSH material committed.
- Tests using mocks/fixtures for available, expired-access, missing-run-root, and scheduler-unavailable paths.

Definition of done:

- A Balfrin-capable worker can run one command to decide whether read-only collection is possible, and expired access fails closed without modifying local evidence.

Boundaries: Read-only SSH/preflight only, no live submission, no remote mutation, no generated remote artifact claim, no operational claim.

### TB-224: Balfrin Worker Routing In Task Context

Goal: Teach the task-context helper to mark Balfrin SSH/live-evidence tasks as requiring a stronger Balfrin-capable worker and the access preflight from TB-223.

Capability gap reduced: Orchestrators currently have to remember when to switch from the default small worker to a stronger worker for remote Balfrin tasks.

Why this outranks alternatives: The worker-routing rule should be machine-visible before live or read-only Balfrin tasks are delegated.

Inspect first:

- `scripts/print_agent_task_context.py`
- `tests/test_agent_task_context.py`
- `docs/orchestration_strategy.md`
- `docs/task_backlog.md`

Deliverables:

- Compact task-context fields such as `balfrin_access_required`, `recommended_worker_model`, and `balfrin_access_preflight_command` for tasks that mention Balfrin SSH, live run, remote run root, or evidence collection.
- Full-detail mode preserving existing broader helper output.
- Tests for a Balfrin task and a non-Balfrin task.

Definition of done:

- The default compact task context clearly tells the orchestrator when to use a stronger worker and when Balfrin access may have expired.

Boundaries: Helper/context routing only, no live SSH call, no worker launch automation change, no task-priority fields, and no claim upgrade.

### TB-225: Target-Area Metrics Completion Rerun Preflight

Goal: Convert the existing target-area metrics-completion rerun package into a strict authorization-request preflight that first consumes the Balfrin access status from TB-223.

Capability gap reduced: Peak-memory and split validation/hazard output metrics remain incomplete for the preserved target-area run, which weakens the Balfrin demo evidence package.

Why this outranks alternatives: Closing missing mandatory evidence is a smaller and more interpretable step than launching a multi-zone probe.

Inspect first:

- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/orchestration_strategy.md`

Deliverables:

- A preflight classification such as `ready_for_authorization_request`, `blocked_missing_run_root`, or `blocked_incomplete_package`.
- Exact expected metrics, preservation files, comparison basis, access-preflight requirement, and post-run collection commands.
- Focused tests for ready, partial, missing-run-root, and Balfrin-access-blocked paths.

Definition of done:

- The rerun package can be reviewed without reading the whole Balfrin doc stack, and it fails closed unless every pre-authorization input is present.
- No live submission command is presented as authorized.

Boundaries: No live Balfrin submission, no authorization grant, no new scientific interpretation, no scale-up authorization, no operational claim, and no fabricated metrics.

### TB-226: Smallest Multi-Zone Probe Authorization Preflight

Goal: Turn the smallest bounded multi-zone handoff into an authorization preflight that proves the reviewed package, reducer budget, Balfrin access state, and submission gate are mutually consistent.

Capability gap reduced: Multi-zone execution remains dry-run or fixture-backed until the package, reducer constraints, and authorization-gated submit path agree on the exact minimal run shape.

Why this outranks alternatives: Multi-zone measurement is valuable only if the first attempt is small, reproducible, preservation-safe, and delegated to a stronger Balfrin-capable worker.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_authorized_multi_zone_submit.py`
- `tests/test_multi_zone_reducer_pressure_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/orchestration_strategy.md`

Deliverables:

- A deterministic preflight report for the smallest multi-zone package with release-zone count, scenario count, worker counts, reducer chunks, output profile, and preservation checklist.
- Fail-closed validation that the reviewed handoff package, authorization record, and Balfrin access preflight are all required before submission.
- Focused tests covering ready-package, missing-authorization, expired-access, and reducer-budget-blocked paths.

Definition of done:

- The package can be reviewed for possible authorization without implying that authorization has been granted.
- The reported run shape stays within measured reducer and file-family constraints.

Boundaries: No live Balfrin job, no distributed execution, no scale-up authorization, no operational claim, and no generated heavy outputs committed.

### TB-227: Balfrin Post-Run Evidence Collector Rehearsal

Goal: Rehearse post-run evidence collection on complete, incomplete, missing, and access-blocked fixture roots for both metrics-completion and multi-zone paths so partial runs cannot be promoted.

Capability gap reduced: The demo needs a reliable post-run classification before another live run can be treated as evidence rather than only execution.

Why this outranks alternatives: A live run without a preservation-safe collector and access-aware failure mode would increase ambiguity instead of reducing it.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `tests/test_balfrin_authorized_multi_zone_submit.py`
- `tests/test_balfrin_probe_metrics_report.py`
- `tests/test_balfrin_probe_preservation_gate.py`
- `tests/test_balfrin_demonstration_closure_package.py`
- `tests/fixtures/balfrin_probe_metrics_contract/complete_run_root/command_plan.json`
- `docs/orchestration_strategy.md`

Deliverables:

- Fixture-backed collector rehearsal covering complete, incomplete, missing-root, SSH-unavailable, and non-git-artifact-unavailable classifications.
- Closure-package input compatibility checks for the two plausible next live-run families.
- Focused tests proving incomplete roots remain blocked.

Definition of done:

- The collector and closure package agree on provenance and missing-field semantics for fixture roots.
- The result preserves measured versus fixture-backed distinction.

Boundaries: Fixture-backed rehearsal only, no live run, no claim upgrade, no maturity upgrade, and no generated heavy outputs committed.

### TB-228: Multi-Zone Handoff Output Budget Projection

Goal: Project reducer manifest, file-family, and output-byte pressure from the actual multi-zone handoff command plan rather than from a standalone scratch probe alone.

Capability gap reduced: Current multi-zone pressure evidence is useful but still partly detached from the concrete Balfrin handoff package that would be reviewed.

Why this outranks alternatives: The first multi-zone measurement should be constrained by the package it would actually execute, not by a generic scratch shape.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_multi_zone_reducer_pressure.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A handoff-derived output-budget summary with primary outputs, sidecars, reducer manifests, manifest bytes, and first bottleneck labels.
- Tests proving the handoff fails closed when projected budgets exceed the current gate.
- Documentation update only if needed to clarify the handoff-versus-scratch distinction.

Definition of done:

- The multi-zone handoff exposes the same budget vocabulary as the reducer gate.
- The task produces measured or fixture-backed budget evidence, not a new roadmap label.

Boundaries: No live Balfrin job, no distributed reducer, no output-default change, no scale-up authorization, and no operational claim.

### TB-229: Bounded Hazard Accumulator Optimization Spike

Goal: Implement or reject one bounded trajectory-accumulation optimization inside the existing hazard builder based on the TB-219 hotspot evidence.

Capability gap reduced: Multi-zone hazard throughput is likely to hit Python trajectory accumulation before Rust simulation limits, but unmeasured rewrites would be risky.

Why this outranks alternatives: The profiler has already isolated a concrete bottleneck; the next engineering step should be one small measured slice, not a broad hazard-builder rewrite.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `tests/test_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `scripts/hazard_output_manifests.py`
- `scripts/hazard_output_reports.py`
- `scripts/hazard_output_writers.py`

Deliverables:

- One narrowly scoped accumulator change, or a measured no-retain report if the attempted optimization is not stable.
- Semantic guardrail tests showing hazard-layer signatures and path-free manifest semantics are unchanged.
- Before/after profile artifacts written only to `/tmp`.

Definition of done:

- The task reports whether the optimization is retained, reverted, or explicitly rejected based on measured throughput and unchanged semantics.
- Existing output-profile and claim-boundary behavior remains unchanged.

Boundaries: No physics change, no hazard semantics change, no output-schema change unless explicitly backward-compatible, no generated heavy outputs committed, and no operational claim.

### TB-230: Post-Optimization Multi-Zone Throughput Reprofile

Goal: Reprofile the representative multi-zone hazard-builder fixture after TB-229 and update the throughput report with retained or rejected optimization evidence.

Capability gap reduced: A code optimization without a follow-up profile can hide noise, regress output pressure, or overstate scaling improvement.

Why this outranks alternatives: Throughput work should remain evidence-driven and should not become speculative performance churn.

Inspect first:

- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `tests/test_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `scripts/build_hazard_layers.py`

Deliverables:

- A before/after or current-versus-baseline report for smoke and representative profiles.
- Updated bottleneck classification that says whether trajectory accumulation is still dominant.
- Focused regression coverage for profile schema stability.

Definition of done:

- The report distinguishes real improvement, noise, and regressions, and records the next bounded target only if evidence supports one.

Boundaries: Profiling only unless TB-229 retained code changes; no new physics, no distributed execution, no operational claim, and no heavy outputs committed.

### TB-231: Chant Sura Public-Context Acquisition Package Freeze

Goal: Freeze a concrete real-input acquisition package for Chant Sura / Fluelapass that separates required swisstopo products, expected local roots, and fixture-only paths.

Capability gap reduced: Second-site realism remains blocked because real public-context products are not staged and fixture-backed dry runs can be mistaken for portability evidence.

Why this outranks alternatives: A second-site hazard build is premature until the real-input acquisition boundary is exact and fail-closed.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/verify_public_geodata_cache.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`

Deliverables:

- A deterministic acquisition package or report that lists every required real product, path, metadata field, and current status.
- Explicit `real_staged`, `fixture_backed`, `missing`, and `deferred` classifications.
- Focused tests for clean-checkout blocked and fixture-backed fail-closed behavior.

Definition of done:

- A worker can tell exactly what must be acquired before any second-site prepared-pilot or hazard build can be called real.

Boundaries: No downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, and no physical-validation claim.

### TB-232: Real-Input Prepared-Pilot Gate For Chant Sura

Goal: Make the Chant Sura prepared-pilot dry run consume the real-context acquisition package and fail closed until required real inputs are staged.

Capability gap reduced: The AOI-to-prepared-pilot path is useful, but portability remains partial while it can advance on fixture-backed roots.

Why this outranks alternatives: This is the practical bridge from acquisition planning to a real second-site workflow without pretending fixtures are evidence.

Inspect first:

- `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Prepared-pilot gate output that requires real acquisition status before reporting second-site readiness.
- Tests for missing, fixture-backed, partial-real, and ready-real input classifications.
- A compact report field naming the first missing real input category.

Definition of done:

- The dry-run path cannot advertise second-site readiness from fixture-backed inputs, and the first real blocker is machine-readable.

Boundaries: No downloads, no ensemble execution, no synthetic evidence claim, no physical-validation claim, no operational claim, and no generated heavy outputs committed.

### TB-233: Observed Runout Acquisition Operator Package

Goal: Materialize an operator-facing observed runout/deposition acquisition package that follows the blocker matrix without treating the package as evidence.

Capability gap reduced: Physical credibility remains weak because no independent observed benchmark package is staged, and the next acquisition action must be concrete.

Why this outranks alternatives: More interpretation of existing conditional runs will not reduce the physical-evidence gap; workers should be able to prepare the package while preserving the non-evidence boundary.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`

Deliverables:

- A generated acquisition package in a caller-provided scratch root with required inventory, geometry/provenance templates, uncertainty fields, licensing/readiness notes, and blocked no-evidence report.
- Tests proving the generated package is classified as template/non-evidence.
- Text output that names the first acquisition action.

Definition of done:

- The package is executable as a dry run and cannot be confused with an accepted observed benchmark dataset.

Boundaries: Worker may generate templates in a caller-provided scratch root only; no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or physical-probability claim, no operational claim, and no generated acquisition files committed.

### TB-234: Observed Benchmark Intake Acceptance Smoke

Goal: Add a fixture-backed acceptance smoke path for a complete observed runout/deposition benchmark intake and explicit rejection paths for common schema failures.

Capability gap reduced: The repository has a blocker matrix but still needs a compact proof that a future real dataset can be accepted or rejected deterministically.

Why this outranks alternatives: Schema repair should be proven on fixtures before any real observed dataset is acquired or reviewed.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `scripts/assess_validation_calibration_evidence_gaps.py`

Deliverables:

- A fixture-backed accepted-intake path with geometry, provenance, uncertainty, calibration-role, validation-role, and holdout-eligibility checks.
- Rejection tests for missing geometry, missing provenance, missing uncertainty, ambiguous calibration role, and overclaiming.
- Report output that keeps accepted schema shape separate from real physical evidence.

Definition of done:

- A complete fixture can pass the schema while the report still says physical credibility is not established unless the input is real accepted evidence.

Boundaries: Fixture-backed schema smoke only, no real evidence claim, no calibration, no parameter fitting, no validation upgrade, and no operational claim.

### TB-235: Release-Zone Provenance Intake Bridge

Goal: Define a small intake path for field-supported release-zone provenance that remains separate from workflow-generated release candidates.

Capability gap reduced: Release-zone automation is improving, but physical meaning remains weak until field-supported provenance can be ingested and kept distinct.

Why this outranks alternatives: Without this bridge, automated candidates can continue to look more physically credible than their evidence supports.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/lib/workflow_validation.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_physical_credibility_evidence_requirements.py`
- `docs/source_zone_block_scenario_policy_v1.md`

Deliverables:

- A minimal release-zone provenance intake schema or helper path that labels `field_supported`, `workflow_generated`, `mixed_provenance`, and `blocked_missing_provenance` consistently.
- Tests showing scenario generation preserves conditional sampling semantics even when field-supported provenance is present.
- A physical-credibility evidence-map update if the intake changes the gap report.

Definition of done:

- Field-supported release-zone provenance can be represented without converting sampling weights into occurrence probabilities.

Boundaries: No release-zone validation claim, no threshold tuning, no source-frequency semantics, no annual-frequency claim, and no operational claim.

### TB-236: Block-Population And Source-Frequency Acquisition Deferral Map

Goal: Convert block-population and source-frequency rows in the physical-evidence matrix into exact acquisition blockers and future-gate prerequisites.

Capability gap reduced: The future physical-probability layer remains vague unless block-population and source-frequency evidence are explicitly separated from current conditional scenario weights.

Why this outranks alternatives: This keeps the project scientifically honest while avoiding premature annual-frequency implementation.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/physical_source_frequency_design_gate.md`
- `docs/source_frequency_evidence_contract.md`
- `docs/physical_frequency_reducer_preconditions.md`

Deliverables:

- Machine-readable blockers for block-population evidence and source-frequency evidence.
- Tests proving conditional scenario weights are not reported as frequency evidence.
- A short current-doc update only if needed to point to the new blocker fields.

Definition of done:

- The gap report names the first missing block-population and source-frequency inputs and leaves annual/physical probability unsupported.

Boundaries: No source-frequency implementation, no annual-frequency product, no calibration, no risk/exposure semantics, and no operational claim.

### TB-237: Workflow-Shell Coupling Extraction Batch

Goal: Extract one bounded batch of duplicated workflow-shell mechanics identified by the coupling inventory into shared helpers without changing public CLI outputs.

Capability gap reduced: Python orchestration drift is now a dominant maintainability risk, especially around dynamic imports, ignored-root assumptions, and repeated status vocabulary.

Why this outranks alternatives: Small consolidation lowers future workflow risk without adding another broad framework or validator family.

Inspect first:

- `scripts/inventory_workflow_shell_coupling.py`
- `tests/test_workflow_shell_coupling_inventory.py`
- `scripts/lib/workflow_validation.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_same_scale_artifact_readiness.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/script_inventory.md`

Deliverables:

- One focused helper extraction for dynamic script loading, ignored-root classification, or shared blocked/status rendering.
- Compatibility tests proving affected CLI JSON/text outputs keep their existing schema and status labels.
- Updated script inventory only if a helper or classification changes.

Definition of done:

- The extraction removes real duplication in at least two call sites and does not create a new orchestration framework.

Boundaries: No script deletion, no broad rewrite, no public status-label rename, no scientific claim change, and no unrelated validator churn.

### TB-238: Command-Plan Manifest Contract Consolidation

Goal: Consolidate repeated command-plan manifest, expected-input/output, ignored-root, and read-only/write semantics across the pilot and Balfrin handoff generators.

Capability gap reduced: Command-plan strings are a high-coupling surface where stale script references, hidden local-state assumptions, and output-root drift can break reproducibility.

Why this outranks alternatives: The command plan is now the practical workflow contract for both local pilots and Balfrin handoffs, so reducing duplication here directly protects execution.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/lib/output_profile_policy.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/check_repo_consistency.py`
- `docs/hazard_output_profile_contract.md`

Deliverables:

- A small shared command-plan helper or dataclass for command id, command text, read-only/write behavior, expected inputs/outputs, ignored output roots, and output-profile policy.
- Tests proving the Tschamut and Balfrin command-plan shapes remain stable except for intentional shared-field normalization.
- Consistency-check updates only if needed to preserve stale-reference protection.

Definition of done:

- The two main command-plan generators share mechanics for manifest semantics while preserving their domain-specific command content.

Boundaries: No broad workflow framework, no command behavior change unless explicitly tested, no generated output commit, no live execution, and no claim upgrade.

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
