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
