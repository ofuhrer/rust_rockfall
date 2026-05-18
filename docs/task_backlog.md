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

Definition of done:

- A complete fixture can pass the schema while the report still says physical credibility is not established unless the input is real accepted evidence.

Boundaries: Fixture-backed schema smoke only, no real evidence claim, no calibration, no parameter fitting, no validation upgrade, and no operational claim.

### TB-238: Command-Plan Manifest Contract Consolidation

Goal: Consolidate repeated command-plan manifest, expected-input/output, ignored-root, and read-only/write semantics across the pilot and Balfrin handoff generators.

Capability gap reduced: Command-plan strings are a high-coupling surface where stale script references, hidden local-state assumptions, and output-root drift can break reproducibility.

Why this outranks alternatives: The command plan is now the practical workflow contract for both local pilots and Balfrin handoffs, so reducing duplication here directly protects execution.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/lib/output_profile_policy.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/check_repo_consistency.py`
- `docs/hazard_output_profile_contract.md`

Deliverables:

- A small shared command-plan helper or dataclass for command id, command text, read-only/write behavior, expected inputs/outputs, ignored output roots, and output-profile policy.
- Tests proving the Tschamut and Balfrin command-plan shapes remain stable except for intentional shared-field normalization.
- Consistency-check updates only if needed to preserve stale-reference protection.

Definition of done:

- The two main command-plan generators share mechanics for manifest semantics while preserving their domain-specific command content.

Boundaries: No broad workflow framework, no command behavior change unless explicitly tested, no generated output commit, no live execution, and no claim upgrade.

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
