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
