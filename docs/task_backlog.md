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

### TB-177: Prepare Second-Site Real-Context Acquisition Execution Plan

Goal: Convert the Chant Sura real-context staging checklist into a concrete operator execution plan for acquiring and verifying real public-context products.

Capability gap reduced: Portability realism beyond the target-area demonstration.

Why this outranks alternatives: The next portability bottleneck is real public context, not more synthetic fixture planning.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/verify_public_geodata_cache.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Product-by-product execution checklist with exact roots, expected metadata, verifier commands, and stop conditions.
- Clear stage/defer decision rows based on current evidence.
- No-download fallback report when credentials or local files are absent.

Definition of done:

- An operator can stage real Chant Sura public context without consulting synthetic fixtures as evidence.

Boundaries: No downloads unless explicitly requested and supported, no second-site ensemble, no synthetic evidence upgrade, and no operational claim.

### TB-178: Define Physical Evidence Acquisition Pack For Target Area

Goal: Specify the real observed runout/deposition, release-zone, block-population, and source-frequency evidence needed to move beyond workflow credibility for the target area.

Capability gap reduced: Physical credibility and validation realism.

Why this outranks alternatives: More execution alone will not establish physical credibility; the missing evidence must be concrete and acquirable.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/current_maturity_snapshot.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- Target-area physical evidence acquisition checklist.
- Dataset roles, required geometry/provenance fields, and claim-boundary mapping.
- Blocked status that separates benchmark intake, calibration, and frequency evidence.

Definition of done:

- Physical credibility gaps for the target area are concrete enough for data acquisition without implying validation exists.

Boundaries: No calibration, no tuning, no annual-frequency claim, no risk/exposure/vulnerability workflow, and no operational claim.

### TB-179: Refill Or Close Post-Demonstration Backlog

Goal: After the target-area demonstration sequence, reassess maturity and refill only the next highest-value tasks.

Capability gap reduced: Backlog relevance after new measured or blocked evidence.

Why this outranks alternatives: The sequence above can change priorities substantially; the next queue should be evidence-driven rather than pre-generated too far ahead.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/agent_work_log.md`
- `docs/task_backlog.md`
- `scripts/print_agent_task_context.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Updated maturity snapshot if evidence changed.
- Either a concise new active backlog or a clear backlog-refill-needed state.
- Summary of tasks completed, blocked, deferred, or superseded.

Definition of done:

- The backlog reflects the actual post-demonstration state and does not retain stale completed or impossible tasks.

Boundaries: No implementation of scientific/execution tasks inside the refill itself, no roadmap bloat, and no claim-boundary changes without measured evidence.

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
