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
