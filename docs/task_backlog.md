# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

## Active Tasks

_Active TB tasks remain below._

### TB-139: Build Balfrin Demonstration Replay Smoke Test

Goal: Verify that the canonical Balfrin evidence bundle and interpretation can
be regenerated from the measured run root or fail closed when the run root is
absent.

Capability gap reduced: demonstration reproducibility and handoff robustness.

Why this outranks alternatives: evidence exists but management-facing replay
should not depend on implicit local state or scattered manual commands.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Replay/smoke helper or command-plan path that checks run-root availability,
  regenerates the bundle/interpreter outputs, and records blocked status when
  remote artifacts are unavailable.
- Focused tests for present-run-root and missing-run-root behavior.

Definition of done:

- A fresh operator can run one deterministic smoke command to verify whether
  the current Balfrin demonstration evidence is replayable from available
  artifacts.

Boundaries: No new Slurm execution, no generated artifact commits, and no
claim-boundary changes.

### TB-140: Compose Site-Level AOI-To-Command-Plan Dry Run

Goal: Chain AOI product discovery, release-zone candidate generation,
scenario-table generation, output-root planning, and command-plan hooks into
one dry-run site orchestration report.

Capability gap reduced: missing composition layer between individual
automation helpers and an AOI-to-workflow user path.

Why this outranks alternatives: individual dry-run helpers now exist, but
Swiss-wide workflow realism requires proving they compose into one deterministic
site-level preparation plan.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_pragmatic_release_plan.py`
- `scripts/generate_pilot_command_plan.py`

Deliverables:

- End-to-end AOI/release-polygon dry-run report with product discovery,
  candidate source zones, scenario-generation inputs, ignored output roots,
  and runnable or blocked command-plan references.
- Tests covering deterministic fixture output and blocked missing-input states.

Definition of done:

- The repository has one compact dry-run command that shows how an AOI would be
  prepared up to, but not including, ensemble execution.

Boundaries: No downloads, no ensembles, no second-site hazard build, no
physical-probability semantics, and no operational claim.

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
