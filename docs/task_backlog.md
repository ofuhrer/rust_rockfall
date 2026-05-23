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

### TB-469: Add A Calibration-Separation Preflight

Goal: Verify that calibration experiment outputs are not silently treated as validation acceptance evidence.

Capability gap reduced: Calibration is currently missing for claim purposes, and future work needs a local guardrail that keeps calibration, validation, and selected parameters separate.

Why this outranks alternatives: It prevents scientific claim drift before anyone starts tuning or adding calibration-oriented tasks.

Inspect first:

- `calibration/README.md`
- `calibration/experiments/scarring_single_impact_v0_4/selected_parameters.yaml`
- `validation/cases/`
- `scripts/assess_validation_calibration_evidence_gaps.py`

Deliverables:

- A local calibration-separation preflight and tests that enumerate calibration outputs, validation cases, and prohibited claim crossings.

Definition of done:

- The preflight reports current calibration artifacts as diagnostic/non-default, tests cover a forbidden validation reference shape, focused checks pass, and this task is removed after calibration separation is executable.

Boundaries: No tuning, no selected-parameter promotion, no physical-credibility upgrade, no operational claims, and no Balfrin access.

### TB-470: Package A Local Scientific Backlog Recommendation

Goal: Generate a compact recommendation report for the next local scientific backlog after the first local audits land.

Capability gap reduced: Backlog refill currently depends on manual interpretation of several helper outputs.

Why this outranks alternatives: It consolidates the new local evidence surfaces into the next small worker queue without reopening Balfrin or claim-upgrade work.

Inspect first:

- `scripts/print_agent_task_context.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/task_backlog.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A local recommendation command or extension and tests that ranks the next scientific tasks from denominator, traceability, fragility, second-site, holdout, and calibration-separation outputs.

Definition of done:

- The report ranks at least five local follow-ups with dependencies and claim boundaries, tests pass, and this task is removed only after it can guide another backlog refill.

Boundaries: No live Balfrin access, no scale-up authorization, no operational claims, no physical-probability claims, and no distributed execution.

### TB-471: Refresh Scientific State Docs From Local Evidence

Goal: Refresh the current maturity and local onboarding docs so they point to the new local scientific progress commands.

Capability gap reduced: Once the local evidence commands exist, worker-facing docs need to route future work to them instead of broad manual reading.

Why this outranks alternatives: It prevents the new local scientific workflow from becoming another hidden helper surface.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/onboarding.md`
- `AGENTS.md`
- `docs/task_backlog.md`

Deliverables:

- Focused documentation updates that name the local scientific progress commands, their boundaries, and the next non-Balfrin workflow.

Definition of done:

- Docs point workers to the new commands, consistency checks pass, the completed work is logged, and this task is removed only after the backlog is empty or explicitly refilled with the next smallest local tasks.

Boundaries: Documentation must not claim physical credibility, annual frequency, operational use, scale-up, distributed execution, or Balfrin authorization changes.

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
