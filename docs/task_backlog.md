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

### TB-557: Execute The Next Bounded Balfrin Postproc Probe

Goal: Run the next repository-gated bounded Balfrin `postproc` probe if all access, package, output-budget, and preservation gates pass.

Capability gap reduced: Converts readiness into measured execution evidence.

Why this outranks alternatives: Management needs measured feasibility evidence for the next bounded step, but only after the reviewed package and gates are current.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Submit and actively monitor one bounded `postproc` job only if gates are ready.
- Preserve the run root and collect runtime, memory, file-count, byte-count, reducer, and manifest metrics.

Definition of done:

- Either one bounded `postproc` run completes with preserved measured evidence, or the attempt fails closed before submission with a concrete blocker and smallest next unblock action.

Boundaries: `postproc` only under existing clearance; stop if expected partition saturation exceeds 6 hours; no non-postproc partition, distributed execution, operational claim, annual-frequency claim, or physical-probability claim.

### TB-558: Collect And Promote The Next Probe Evidence

Goal: Integrate the latest completed bounded Balfrin probe into the existing evidence bundle and preservation surfaces.

Capability gap reduced: Prevents measured run evidence from remaining only as raw remote artifacts.

Why this outranks alternatives: A successful run is not useful for planning until metrics, output budgets, and preservation status are collected and surfaced.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Updated local reports that classify the new run root as measured, failed-closed, or blocked.
- Runtime/output/reducer metrics are separated from scientific claim boundaries.

Definition of done:

- The evidence bundle and interpretation gate consume the new run-root metrics or fail closed with exact missing artifacts.

Boundaries: Evidence collection only; no rerun, no operational claim, no physical validation claim.

### TB-560: Consolidate Duplicate Balfrin Decision Logic

Goal: Reduce duplication between scale-readiness, next-live-run decision, and management-demo package logic.

Capability gap reduced: Lowers workflow-shell complexity and reduces stale recommendation drift.

Why this outranks alternatives: Recent decision surfaces have drifted and crashed in different ways; consolidation should remove logic, not add another wrapper.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Extract or reuse one shared ranking/evidence function for the overlapping next-action logic.
- Delete or reduce duplicated constants or stale follow-up IDs where possible.

Definition of done:

- Focused tests pass and the diff removes more duplicated decision text or branches than it adds.

Boundaries: No new top-level report, no behavior broadening beyond current evidence, no claim upgrade.

### TB-561: Add A Clean-Checkout AOI Workflow Smoke Regression

Goal: Ensure the user-facing AOI workflow can run its smallest local smoke path without ignored artifacts.

Capability gap reduced: Protects onboarding and user-facing workflow reliability from hidden local-state assumptions.

Why this outranks alternatives: A clean checkout must be able to demonstrate the workflow without private Tschamut/Balfrin roots.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `README.md`

Deliverables:

- A focused clean-checkout-safe smoke test or helper mode using tracked tiny fixtures.
- README command remains accurate and bounded.

Definition of done:

- The smoke path writes reduced local artifacts under `/tmp` and does not require ignored roots.

Boundaries: Tiny fixture only; no real geodata download, no Balfrin, no operational map claim.

### TB-562: Measure Real-AOI Public-Geodata Acquisition Dry Run

Goal: Exercise the public-geodata acquisition/staging dry-run path for a real AOI without downloading or claiming readiness.

Capability gap reduced: Moves Swiss-wide portability from fixture semantics toward real AOI acquisition planning.

Why this outranks alternatives: Public-geodata acquisition and staging remain the largest practical gap before arbitrary target-area preparation.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A deterministic dry-run manifest listing required swisstopo products, expected staging roots, missing inputs, and next acquisition actions for one real AOI.
- Focused tests or fixture assertions for blocked/no-download behavior.

Definition of done:

- The dry-run command produces an actionable blocked/acquisition report without using synthetic fixtures as evidence.

Boundaries: No downloads unless explicitly authorized later, no second-site ensemble, no operational or validation claim.

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
