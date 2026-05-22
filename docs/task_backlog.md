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

### TB-458: Refresh The Regional-Split Replay Smoke At The Rebuildable-Reduced Tier

Goal: Confirm the measured regional split run root still supports rebuildable-reduced replay smoke without promoting full GIS or research outputs.

Capability gap reduced: Replay-critical recovery evidence for the measured regional split branch.

Why this outranks alternatives: The matrix still recommends `rebuildable_reduced` as the smallest replay tier, so replay-smoke evidence should stay current before any larger probe.

Inspect first:

- `scripts/summarize_balfrin_demonstration_replay_smoke.py`
- `tests/test_balfrin_demonstration_replay_smoke.py`

Deliverables:

- A refreshed replay-smoke report that preserves the current replay-tier recommendation and any missing-output follow-up needed to keep the measured branch reproducible.

Definition of done:

- The replay-smoke recommendation matches the current measured evidence and focused checks pass.

Boundaries: No operational claim upgrade, no live submission, no distributed execution, no risk/exposure/vulnerability workflow.

### TB-459: Regenerate The Reviewed Regional Split Submission Package From Fresh Preflight Inputs

Goal: Regenerate the reviewed regional split submission package from fresh access-preflight inputs and compact manifest mode before any retry is considered.

Capability gap reduced: Stale-package and stale-preflight rejection on the live regional split path.

Why this outranks alternatives: The earlier failed-closed branch was about stale remote hygiene, and the refreshed package must stay aligned with the current measured split shape.

Inspect first:

- `scripts/generate_balfrin_regional_split_submission_package.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `tests/test_balfrin_regional_split_submission_package.py`

Deliverables:

- A regenerated package report that records the current preflight path, remote-head alignment, and compact-manifest freshness.

Definition of done:

- Fresh preflight and package state agree, stale-package rejection remains covered, and focused checks pass.

Boundaries: No live Balfrin submission, no scale-up claim, no distributed execution, no operational semantics.

### TB-460: Measure Restaged Management-AOI Candidate Stability For The Next Live Probe

Goal: Measure restaged management-AOI candidate stability so the next live probe can use the current candidate ordering instead of stale heuristics.

Capability gap reduced: Local candidate-stability evidence for the next live probe.

Why this outranks alternatives: Local evidence is now ranked behind reducer and scenario follow-up, but it still directly refines the next bounded probe once those are current.

Inspect first:

- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `tests/test_balfrin_target_area_candidate_stability.py`

Deliverables:

- A refreshed candidate-stability report that records the restaged terrain candidate ordering, stability deltas, and any batching or exclusion changes it implies.

Definition of done:

- The candidate-stability output is current and focused checks pass.

Boundaries: No live submission, no scale-up claim, no distributed execution, no operational semantics.

### TB-461: Recompute The Balfrin Next-Live-Run Decision Gate And Demo Package

Goal: Recompute the Balfrin next-live-run decision gate and management demo package from the refreshed reducer, scenario, replay, and candidate measurements.

Capability gap reduced: A single current surface for the next ranked executable action.

Why this outranks alternatives: The queue needs one compact downstream decision surface after the measured regional split work, not another stale summary of earlier blockers.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`
- `tests/test_balfrin_management_demo_package.py`

Deliverables:

- Updated decision-gate and management-demo reports that reflect the reducer-first ranking, scenario batching cap, replay-smoke recommendation, and candidate-stability result.

Definition of done:

- The downstream decision surface matches the latest ranked evidence and focused checks pass.

Boundaries: No operational claim upgrade, no annual-frequency or risk/exposure/vulnerability workflow, no distributed execution.

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
