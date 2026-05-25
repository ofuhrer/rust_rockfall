# Orchestration Strategy

This document records the lightweight way to work through TB tasks without
letting context or generated artifacts get out of hand. It is guidance, not a
roadmap.

## Execution Model

- Work directly on `main`; do not create branches or worktrees for normal TB
  execution.
- Execute exactly one active task at a time, always the lowest-numbered
  `### TB-XXX:` heading in `docs/task_backlog.md`.
- Keep `main` usable: pull before substantial work, make focused commits, and
  verify the task is removed when done.
- Pause only for failures that make the next action unsafe or ambiguous.

## Worker Prompt Shape

Worker prompts should stay small:

- the selected task title and body;
- `print_agent_task_context.py --task TB-XXX --format json`;
- `rg -n "^### TB-XXX:" docs/task_backlog.md`;
- the task's `Inspect first` files;
- the focused checks that matter for the task.

Avoid broad reference dumps unless the task needs them.

When Balfrin access is unavailable, use:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --local-only --format json --no-live-checks
```

This preserves the full active-task order in the report while surfacing
`next_local_task`, `local_active_tasks`, and `balfrin_required_tasks` so the
worker can select the first executable non-Balfrin task without changing
backlog headings or task-status vocabulary.

## Output Monitoring

Use file-backed worker logs by default:

```bash
OD_CODEX_DISABLE_PLUGINS=1 RUST_LOG=error codex exec \
  -m gpt-5.4-mini \
  -C /Users/fuhrer/Desktop/rust_rockfall/main \
  --dangerously-bypass-approvals-and-sandbox \
  "$PROMPT" >/tmp/codex-worker-TB-XXX.log 2>&1
```

Monitor compact health rather than streaming everything:

```bash
stat -f 'TB-XXX log bytes=%z modified=%Sm' /tmp/codex-worker-TB-XXX.log
tail -n 20 /tmp/codex-worker-TB-XXX.log
```

After exit, extract only the final structured block beginning at `TASK:`. If a
worker fails, preserve the final relevant error block and stop.

If a worker prints a complete final structured report, the reported commit is
pushed, the worker log stops changing, and post-worker verification passes, but
the `codex exec` wrapper process remains alive, treat that as a stuck wrapper
after completion. Record the condition, terminate only the stale wrapper
process, run the full post-worker verification, and continue only if the
worktree is clean and the completed task is absent from the backlog.

## Balfrin Access

Workers may access Balfrin over SSH when the selected task explicitly requires
Balfrin inspection, evidence collection, or a user-authorized Balfrin run.
Use a stronger worker for live Balfrin submissions and for read-only work that
mixes remote state, scheduler state, and preserved run roots.

Balfrin SSH access can expire. If access or expected run roots are unavailable,
record the missing piece and move to the next useful local action. Keep fixture
results and measured Balfrin results clearly labeled.

## Live Balfrin Run Authorization

The user has granted standing clearance for GPT-5.5 workers to submit and
actively monitor Balfrin jobs on the `postproc` partition. This includes
permission to submit multiple concurrent `postproc` jobs and to fill the
partition. If a task would keep the `postproc` partition fully busy for more
than 6 hours, the worker must stop and rediscuss before continuing.

For `postproc` jobs covered by the standing clearance, authorization/audit
records are reproducibility artifacts. Use reviewed packages, active
monitoring, `$SCRATCH` run roots, and post-run collection so results can be
replayed and compared. Non-`postproc`, multi-node, GPU/MPI, and Swiss-wide work
should be introduced as explicit phase changes.

## Outcome Taxonomy

Final worker reports should say plainly what happened. Use these labels when
they help:

- `implemented_measured`: the task's measured capability was actually achieved.
- `implemented_fixture_backed`: helper/report behavior is proven only by
  fixtures or synthetic roots.
- `implemented_waiting_report`: the task produced a useful waiting-state report
  but did not achieve the intended execution or measurement.
- `waiting_unresolved`: the worker could not make the requested capability
  executable.
- `partial_needs_followup`: useful work landed, but the original capability
  still needs a follow-up task.

For execution tasks, do not treat a report as a measurement. If a run did not
happen, choose the next action that makes a run more likely.

## Post-Worker Verification

After every successful worker:

```bash
git pull --ff-only origin main
git status --short --branch
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --format json
rg -n "^### TB-XXX:" docs/task_backlog.md || true
```

Verify:

- `main` fast-forwards cleanly from `origin/main`;
- the worktree is clean;
- the completed task is removed;
- the worker's outcome taxonomy matches the task definition of done;
- no generated placeholder artifacts remain.

If a task produced only fixture-backed or partial evidence, prefer the next
measurement or simplification task over synthesis.

## Known Pitfalls

- Do not use plain `python`; use `PYENV_VERSION=system uv run python`.
- Do not use `git push --no-verify`.
- Do not add priority markers or `Priority:` fields to `docs/task_backlog.md`.
- Do not rely on ignored local Tschamut/Balfrin artifacts in clean-checkout
  tests unless the task explicitly concerns live local artifacts.
- Do not silently convert an execution task into a documentation-only success.
- Remove generated `placeholder_second_site_v1` artifacts before committing.
