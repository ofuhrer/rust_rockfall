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

### TB-213: Evidence-Gated Balfrin Demonstration Closure Package

Goal: Produce one coherent Balfrin demonstration closure package only after new measured evidence from a metrics-completion rerun or authorized multi-zone probe exists.

Capability gap reduced: Reviewers currently have to reconcile many reports to decide whether Balfrin is plausibly extensible toward larger Swiss workflows.

Why this outranks alternatives: A closure package is useful after new measured evidence, but premature synthesis would add process without reducing the current evidence gaps.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- A reproducible closure report or package that consolidates runtime evidence, preservation status, restartability, reducer/output scaling, AOI/release/scenario automation, GIS readiness, second-site portability, and scientific claim boundaries.
- Strict provenance labels distinguishing measured, fixture-backed, dry-run, blocked, unavailable, unauthorized, and historical evidence.
- A direct reviewer-facing answer to whether the current Balfrin evidence is plausibly extensible toward larger Swiss workflows.
- A fail-closed `blocked_no_new_measured_evidence` classification if neither a metrics-completion rerun nor an authorized multi-zone run has produced new preservation-checked evidence.
- Focused tests for complete measured evidence, mixed-provenance warning, and blocked-no-new-evidence classifications.

Definition of done:

- The closure package can be regenerated deterministically, answers the demonstration-readiness question without requiring a repository reread, and refuses to upgrade maturity labels without new measured evidence.

Boundaries: No new live execution, no operational claim, no annual-frequency or risk semantics, no physical-credibility upgrade without independent evidence, and no replacement of the authoritative backlog or work log.

### TB-214: Workflow-Shell Coupling Inventory

Goal: Build an executable inventory of implicit coupling across Python scripts, command-plan strings, ignored artifact roots, generated reports, and validator-specific status semantics.

Capability gap reduced: Hidden workflow-shell drift where scripts, docs, command plans, and ignored local roots can disagree while broad consistency checks still pass.

Why this outranks alternatives: The reviewer identified workflow-shell complexity as the most underestimated risk; before more refactors, the repo needs a concrete map of the coupling that causes stale references and local-state dependence.

Inspect first:

- `docs/script_inventory.md`
- `scripts/check_repo_consistency.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_same_scale_artifact_readiness.py`
- `scripts/lib/workflow_validation.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- A deterministic coupling-inventory helper or report that lists dynamic import-by-path usage, command-plan script references, ignored-root path assumptions, generated report dependencies, and duplicated status vocabularies.
- A severity classification for each coupling family: `stable_contract`, `needs_shared_helper`, `stale_reference_risk`, or `hidden_local_state_risk`.
- A small fixture-backed test that proves the inventory catches a stale script reference and an ignored-root-only dependency without requiring real ignored artifacts.
- A prioritized extraction shortlist limited to bounded follow-up work, not a broad rewrite.

Definition of done:

- The repo can regenerate a coupling inventory from tracked files and use it to decide which workflow-shell refactors reduce real drift rather than cosmetic script count.

Boundaries: Inventory and prioritization only; no broad script moves, no deletion campaign, no new evidence package, and no changes to live command behavior.

### TB-215: Workflow Utility Migration Batch For Status And Provenance

Goal: Migrate a bounded set of high-churn validators and summarizers onto shared status, checksum, manifest, blocked-report, and claim-boundary helpers.

Capability gap reduced: Repeated workflow mechanics across validators and summarizers that create drift in blocked-state semantics, provenance labels, checksum handling, and report rendering.

Why this outranks alternatives: `scripts/lib/workflow_validation.py` is the right consolidation direction, but the reviewer found the extraction is still partial and future validators should not keep copying bespoke mechanics.

Inspect first:

- `scripts/lib/workflow_validation.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`

Deliverables:

- A migration of at least five high-use scripts to shared helper calls for status rendering, required-path checks, checksum/provenance fields, and claim-boundary scanning.
- A compatibility note documenting any status vocabulary preserved for downstream reports.
- Focused tests proving migrated scripts keep their output schema stable while using the shared helper layer.
- A short remaining-duplication list for the next migration batch.

Definition of done:

- The selected scripts stop duplicating core workflow validation mechanics, their public JSON/text outputs remain stable where expected, and future status changes have one obvious helper location.

Boundaries: Bounded helper migration only; no domain-schema collapse, no broad packaging rewrite, no claim upgrade, and no unrelated validator churn.

### TB-216: Repository Consistency Checker Responsibility Split

Goal: Split the largest responsibility clusters in `scripts/check_repo_consistency.py` into importable checker modules while preserving the CLI contract.

Capability gap reduced: The consistency checker is becoming a second orchestration system whose growth makes every cleanup require risky edits to one large file.

Why this outranks alternatives: The checker protects useful boundaries, but its size and scope now increase maintainability risk; extracting responsibility groups makes future guards easier to reason about.

Inspect first:

- `scripts/check_repo_consistency.py`
- `docs/script_inventory.md`
- `docs/task_backlog.md`
- `docs/agent_work_log.md`
- `docs/current_maturity_snapshot.md`
- `scripts/lib/workflow_validation.py`

Deliverables:

- A proposed module boundary or first extraction for two checker families, such as backlog/work-log hygiene and claim/status hygiene.
- CLI-preserving tests showing `scripts/check_repo_consistency.py` still reports the same pass/fail state for clean fixtures and targeted failure fixtures.
- A no-new-policy guarantee: extracted modules must move existing behavior before adding new checks.
- A short architecture note naming which checker responsibilities remain in the entrypoint.

Definition of done:

- The consistency checker has smaller testable surfaces for at least two responsibility families, with no loss of existing guard coverage.

Boundaries: Refactor only; no new broad policy checks, no backlog edits except task completion, no generated evidence claims, and no unrelated script cleanup.

### TB-217: Scalable Command-Plan Output Profile Enforcement

Goal: Enforce scalable output defaults in multi-zone and Balfrin command plans, including summary-only conditional curves and disabled full-grid CSV exports unless explicitly overridden.

Capability gap reduced: Multi-zone execution can still be blocked by file-family, manifest, and validation-output pressure even when reduced-output modes exist.

Why this outranks alternatives: The reviewer found output/reducer pressure is the most urgent execution risk; enforcing scalable defaults prevents command plans from selecting known non-scalable artifact families by accident.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `docs/hazard_output_profile_contract.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_pilot_command_plan.py`

Deliverables:

- A command-plan policy check that classifies output profiles as `scalable_default`, `explicit_heavy_debug`, or `blocked_unscalable_default`.
- Fail-closed handling for multi-zone or Balfrin plans that request full conditional-curve CSVs, full-grid CSV exports, or unbounded validation debug outputs by default.
- Focused tests for scalable defaults, explicit debug override, and blocked unscalable multi-zone plans.
- Documentation of the exact output-profile contract used by Balfrin handoff helpers.

Definition of done:

- Multi-zone and Balfrin command plans cannot silently choose known non-scalable output families as defaults.

Boundaries: Output-profile policy only; no live execution, no distributed reducer, no hazard-value changes, no COG/GIS claim upgrade, and no generated heavy outputs committed.

### TB-218: Reducer Manifest And File-Family Budget Regression Gate

Goal: Add a fixture-backed regression gate that measures reducer manifest bytes, output family counts, output bytes, sidecar counts, and deterministic merge order for realistic multi-zone scratch roots.

Capability gap reduced: Reducer and filesystem pressure can regress without changing simulator correctness or high-level readiness labels.

Why this outranks alternatives: The 12-zone probe already labels manifest, output-family, and reducer-runtime pressure as blockers; those budgets need a repeatable guard before authorizing larger probes.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_multi_zone_reducer_pressure.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- A deterministic regression fixture or fixture generator for multi-zone reducer roots with configurable zone count, chunk count, and output family mix.
- Budget checks for manifest bytes, total files, per-family files, per-family bytes, reducer wall time, and merge-order determinism.
- Warning and blocked thresholds that are explicitly labeled as fixture-backed until real Balfrin roots are measured.
- Tests proving budget regressions fail closed without requiring live Balfrin artifacts.

Definition of done:

- Reducer and output-pressure regressions become visible in CI-scale fixtures before they can reach a live multi-zone Balfrin package.

Boundaries: Fixture-backed gate only; no live Balfrin job, no Swiss-wide projection claim, no distributed reducer, and no generated heavy outputs committed.

### TB-219: Hazard Accumulation Throughput Hotspot Isolation

Goal: Isolate the remaining Python hazard-accumulation hotspot after explicit-grid improvements and define one bounded optimization target.

Capability gap reduced: Python hazard accumulation may become the next bottleneck after output-profile and reducer constraints are enforced.

Why this outranks alternatives: The reviewer noted trajectory accumulation remains dominant after explicit-grid mode reduced hazard-stage time; optimizing without a focused profile risks adding complexity in the wrong place.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/hazard_output_profile_contract.md`
- `tests/test_hazard_layers.py`

Deliverables:

- A microprofile that separates trajectory reading, bounds discovery, accumulation, reducer merge, raster write, manifest write, and report rendering.
- A representative fixture-backed multi-zone profile and a smaller smoke profile suitable for routine tests.
- One bounded optimization proposal with expected impact, risk, and required tests, or an explicit `insufficient_scale_to_optimize` classification.
- Guardrails proving the profile does not change hazard values or output semantics.

Definition of done:

- The repo has a concrete, measured next optimization target for hazard accumulation, or a defensible reason to defer optimization until larger measured roots exist.

Boundaries: Profiling and target selection only; no broad hazard-builder rewrite, no probability semantics change, no physics change, and no generated heavy outputs committed.

### TB-220: Release-Zone And Scenario Physical-Meaning Firewall

Goal: Add an explicit interpretation firewall that prevents workflow-generated release candidates, scenario tables, and sampling weights from being represented as field-supported source probabilities.

Capability gap reduced: Deterministic workflow maturity can be mistaken for physical credibility, especially around release-zone provenance and scenario sampling semantics.

Why this outranks alternatives: The reviewer ranked the scientific credibility gap as the most dangerous risk; the repo should protect against overreading release/scenario automation before physical evidence exists.

Inspect first:

- `docs/source_zone_block_scenario_policy_v1.md`
- `docs/current_maturity_snapshot.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/generate_candidate_source_zone_scenarios.py`

Deliverables:

- A validator or report section that labels release candidates as `workflow_generated`, `field_supported`, `mixed_provenance`, or `blocked_missing_provenance`.
- Explicit checks that scenario sampling weights are not described as occurrence probabilities, annual frequencies, return periods, or risk.
- Focused tests with allowed workflow-language examples and blocked overclaim examples.
- Updates to relevant generated summaries so the provenance firewall appears wherever release/scenario automation is reported.

Definition of done:

- Future release-zone and scenario outputs carry machine-readable physical-meaning boundaries and fail closed on probability or field-support overclaims.

Boundaries: Claim-boundary hardening only; no calibration, no annual-frequency semantics, no operational claim, no new physical evidence, and no source-zone heuristic change.

### TB-221: Observed Runout And Deposition Acquisition Blocker Matrix

Goal: Convert the physical-evidence intake gap into a concrete acquisition blocker matrix for observed runout/deposition, release-zone provenance, block-population evidence, calibration inputs, validation inputs, and holdout data.

Capability gap reduced: Physical credibility remains `not_established` partly because missing evidence categories are named, but not yet organized into an actionable acquisition and acceptance matrix.

Why this outranks alternatives: The reviewer identified independent physical evidence as the highest scientific priority; a precise blocker matrix prevents more workflow packaging from masquerading as progress.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/validation_data_schema.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A machine-readable acquisition matrix with required fields, acceptable provenance, uncertainty fields, licensing/readiness notes, calibration-versus-validation role, and holdout eligibility for each evidence category.
- A deterministic blocked report when no real observed runout/deposition package is available.
- Acceptance tests for complete fixture shape, missing geometry, missing uncertainty, unclear calibration role, and overclaiming blocked statuses.
- A short next-action recommendation that distinguishes data acquisition, schema repair, and scientific deferral.

Definition of done:

- A worker can tell exactly which physical evidence category is missing, what would make it acceptable, and why workflow reproducibility still does not establish physical credibility.

Boundaries: Acquisition planning and acceptance gate only; no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or risk semantics, and no operational claim.

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
