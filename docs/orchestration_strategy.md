# Orchestration Strategy

This document records the current strategy for executing TB tasks with small
Codex workers while keeping the lead/orchestrator context small. It is a
process contract, not a project roadmap.

## Execution Model

- Work directly on `main`; do not create branches or worktrees for normal TB
  execution.
- Execute exactly one active task at a time, always the lowest-numbered
  `### TB-XXX:` heading in `docs/task_backlog.md`.
- Treat each task as one transaction: clean pull, one worker, verification,
  then continue or stop.
- Stop on worker failure, dirty worktree, failed fast-forward pull, stale
  completed task in the backlog, or `backlog_refill_needed=true`.

## Worker Prompt Shape

Worker prompts should include only:

- the selected task title and body;
- `print_agent_task_context.py --task TB-XXX --format json`;
- `rg -n "^### TB-XXX:" docs/task_backlog.md`;
- the task's `Inspect first` files;
- hard boundaries and known pitfalls;
- required focused checks and final report schema.

Do not paste unrelated backlog tasks or broad reference docs. Use
`--detail full` only for orchestrator/review work.

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

## Outcome Taxonomy

Final worker reports must distinguish implementation status from capability
status. Use these labels in `STATUS` or `SUMMARY` when relevant:

- `implemented_measured`: the task's measured capability was actually achieved.
- `implemented_fixture_backed`: helper/report behavior is proven only by
  fixtures or synthetic roots.
- `implemented_blocked_report`: the task produced a useful blocked-state report
  but did not achieve the intended execution or measurement.
- `blocked_unresolved`: the worker could not make the requested capability
  executable.
- `partial_needs_followup`: useful work landed, but the original capability
  still needs a follow-up task.

For execution tasks, a blocked report is not equivalent to measured execution.
The orchestrator must add or request an unblock task before continuing into
tasks that depend on the missing measurement.

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

If the task outcome is fixture-backed, blocked, or partial, the next backlog
refill should capture the smallest unblock or measurement task before adding
dependent synthesis work.

## Known Pitfalls

- Do not use plain `python`; use `PYENV_VERSION=system uv run python`.
- Do not use `git push --no-verify`.
- Do not add priority markers or `Priority:` fields to `docs/task_backlog.md`.
- Do not rely on ignored local Tschamut/Balfrin artifacts in clean-checkout
  tests unless the task explicitly concerns live local artifacts.
- Do not silently convert an execution task into a documentation-only success.
- Remove generated `placeholder_second_site_v1` artifacts before committing.

