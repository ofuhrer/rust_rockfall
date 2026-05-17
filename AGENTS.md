# AGENTS.md

Compact operating guide for automated agents. Detailed background and broad
policy live in `docs/agent_reference.md`; read that file only for broad model,
physics, output, versioning, HPC, or review-policy changes.

## Source Of Truth

- Active task queue: `docs/task_backlog.md`.
- Compact task context: `scripts/print_agent_task_context.py`.
- Durable decisions: `docs/decision_log.md`.
- Completed TB history: `docs/agent_work_log.md`.
- Current maturity snapshot: `docs/current_maturity_snapshot.md`.
- Sequential orchestration strategy: `docs/orchestration_strategy.md`.
- Detailed project background: `docs/project_overview.md`.

When files conflict, preserve hard safety/claim boundaries first, then update
docs so the repository tells one consistent story.

## TB Worker Fast Path

Start every TB implementation from the repo root:

```bash
cd /Users/fuhrer/Desktop/rust_rockfall/main
git pull --ff-only origin main
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

If the context helper reports `backlog_refill_needed=true`, do not invent an
implementation task. Run a scoped backlog-refill or gap-analysis task first.

Read only the selected backlog task and its `Inspect first` files unless the
task explicitly asks for broader context. Use `--detail full` on the context
helper only for orchestrator/review work.

Use `PYENV_VERSION=system uv run python ...`; avoid plain `python` or `python3`
because local pyenv shims can point at unavailable interpreters.

## Sequential Orchestration

When looping over backlog tasks, treat each task as one transaction:

1. Pull `origin/main` and require a clean worktree.
2. Select only the lowest-numbered active `TB-xxx` task.
3. Launch exactly one worker for that task; do not pre-generate later prompts.
4. After the worker exits, verify that `main` fast-forwards, the worktree is
   clean, and the completed task was removed from `docs/task_backlog.md`.
5. Stop on any worker failure, dirty worktree, failed pull, or stale completed
   task.

Run workers directly on `main`; do not create branches or worktrees for normal
TB execution. Keep worker output visible enough to diagnose failures, but route
large JSON, diffs, and logs to `/tmp` and summarize the result. Preserve the
final relevant error block on failure. Use `docs/orchestration_strategy.md` for
the full file-backed monitoring pattern.

## Work Rules

- Prefer executable progress over process artifacts: implemented behavior,
  measured analysis, reproducibility improvements, focused bug fixes, or tests.
- Distinguish measured completion from fixture-backed proofs and blocked-state
  reports. A blocked report is useful evidence, but it is not the same as
  achieving the task's measured capability.
- Keep edits scoped to the task and existing module boundaries.
- Add or update focused tests for behavior, parser, CLI, output, and bug-fix
  changes.
- Keep seeded/stochastic runs deterministic.
- Keep scratch outputs in `/tmp`; do not commit generated trajectory or hazard
  outputs unless they are intentional tiny fixtures.
- Keep visible worker progress compact: use 1-2 sentence updates, redirect
  large JSON/logs/diffs to `/tmp`, never paste full diffs, and preserve the
  final relevant error block when a command fails.
- Finish with the compact structured report schema:
  `TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
  `PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.
  Use statuses such as `implemented_measured`, `implemented_fixture_backed`,
  `implemented_blocked_report`, `blocked_unresolved`, or
  `partial_needs_followup` when that distinction matters.
- For dataset or validation-case changes, keep calibration, validation, and
  operational input data separate.
- For Swiss geodata changes, preserve CRS, vertical datum, resolution, extent,
  source-tile ids, and provenance; never commit large swisstopo raw products.
- Append completed TB entries to the bottom of `docs/agent_work_log.md` using
  its template; do not insert entries near older related work.
- Remove the completed task from `docs/task_backlog.md`; never leave stale
  active tasks for the next worker.

## Required Checks

Run the focused checks named by the task. Before commit also run:

```bash
git diff --check
PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
find data/processed/swisstopo validation/private hazard/results validation/policies \
  \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print
```

There is no repository pre-push hook. Before pushing, confirm task-specific
checks passed and inspect `git status --short --branch` plus the committed diff.

## Hard Boundaries

- Do not introduce hidden physics, tuning, or undocumented parameter choices.
- Do not claim equivalence with proprietary or operational hazard tools.
- Do not present current products as operational hazard assessment.
- Do not describe hazard-map layers as risk maps unless exposure and
  vulnerability are explicitly in scope.
- Do not introduce annual-frequency, physical-probability, risk, exposure,
  vulnerability, scale-up, or distributed-execution claims unless a task
  explicitly authorizes that phase change.
