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

### TB-201: Ignored-Artifact Dependency Audit For Python Tests

Goal: Add an automated audit that identifies Python tests and helper smoke paths that read ignored artifact roots without creating committed fixtures, temporary fixtures, or explicit blocked-report expectations.

Capability gap reduced: Hidden test coupling to local-only artifacts that makes CI and clean clones diverge from developer workstations.

Why this outranks alternatives: Copilot found concrete failures, but a broader scan shows many tests reference ignored roots; the suite needs a guard so new hard dependencies do not reappear after the immediate CI fixes.

Inspect first:

- `tests/test_same_scale_artifact_readiness.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_swiss_wide_execution_envelope.py`
- `tests/test_balfrin_probe_metrics_report.py`
- `tests/test_balfrin_tschamut_readiness.py`
- `scripts/check_repo_consistency.py`
- `.gitignore`

Deliverables:

- A repository-consistency or dedicated test-audit helper that scans Python tests for hard dependencies on `hazard/results/**`, `validation/private/**`, `data/processed/swisstopo/*/`, and `/scratch/**`.
- An allowlist format that permits references only when the test creates temporary fixture data, uses tracked `tests/fixtures/**`, or asserts an explicit blocked state.
- Initial audit classifications for the current test files that reference ignored roots, including which are fixture-backed, blocked-state tests, or cleanup candidates.
- Focused tests showing the audit rejects a new hard read from an ignored root and accepts a temporary fixture or tracked fixture path.

Definition of done:

- The audit runs in CI or repository consistency checks, current tests are classified without false failures, and a new hard dependency on ignored local artifacts is caught before merge.

Boundaries: Audit and classification only; no broad rewrite of all tests, no deletion of local artifacts, no new generated fixtures outside `tests/fixtures`, and no scientific evidence reclassification.

### TB-202: CI Git History And Output-Root Portability Guard

Goal: Remove CI-only failures caused by shallow Git history and by output-root allowlists that treat repository paths under `/tmp` as safe scratch paths.

Capability gap reduced: Portability of repository hygiene checks and dry-run output-root validation across GitHub runners, local temporary checkouts, and isolated test roots.

Why this outranks alternatives: These failures are not scientific, but they break CI and can mask more meaningful artifact-dependency failures.

Inspect first:

- `.github/workflows/ci.yml`
- `scripts/check_repo_consistency.py`
- `tests/test_repo_consistency_claim_hygiene.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`

Deliverables:

- CI checkout or consistency-check behavior that keeps work-log commit reachability deterministic, either by fetching full history for the Python job or by explicitly detecting and reporting shallow clones.
- Focused tests for work-log reachability behavior under shallow-history simulation.
- Output-root validation that rejects paths inside the repository unless they are under an allowed ignored output root, even when the repository root itself is located below `/tmp`.
- Focused tests covering allowed `/tmp` scratch roots, allowed ignored repository roots, and forbidden repository-local paths.

Definition of done:

- GitHub Python tests no longer fail because historical work-log commits are unreachable in a shallow checkout, and dry-run skeleton output-root validation behaves consistently for repos under `/tmp`.

Boundaries: No changes to task history, no weakening of work-log hygiene in normal full-history clones, no generated artifact commit, and no expansion of allowed output roots beyond documented ignored/scratch locations.

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
