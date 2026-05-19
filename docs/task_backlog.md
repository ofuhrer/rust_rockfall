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

Live Balfrin rule: a task may prepare, review, or preflight a Balfrin submission
package, but it may not submit a new live run unless the user gives an explicit
instruction for that exact run. The orchestrator must route any authorized live
run to a GPT-5.5 Balfrin worker and require the existing Balfrin access,
readiness, authorization, output-budget, preservation, and evidence gates. A
ready preflight, generated package, or backlog task is not authorization.

## Active Tasks

### TB-300: Validation Output Budget Reduction Plan

Goal: Measure and reduce validation-output file fanout for target-area and multi-zone workflows while preserving replayability and required scientific diagnostics.

Capability gap reduced: Validation output has historically dominated file count and bytes, and can overwhelm useful hazard artifacts before Swiss-scale execution.

Why this outranks alternatives: Output size control is not complete until validation debug outputs are budgeted as strictly as hazard outputs.

Inspect first:

- `src/validation.rs`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_hazard_output_profile.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_pilot_command_plan.py`
- `tests/test_bounded_validation_output_profile.py`

Deliverables:

- A validation-output inventory for target-area and multi-zone plans, separating replay-critical files from diagnostic/debug files.
- A reduced validation-output mode or plan-level defaults that preserve manifests, hashes, summaries, and required trajectories while suppressing nonessential debug fanout.
- Tests proving reduced validation outputs remain replayable and evidence-preserving.

Definition of done:

- The largest validation-output families have explicit budgets and a reduced mode suitable for scalable AOI/Balfrin plans.

Boundaries: Validation output budgeting only; no physics change, no metric suppression without replacement summary evidence, no live Balfrin submission, no claim upgrade, and no operational claim.

### TB-301: Multi-Zone Local Scaling Ladder

Goal: Run a deterministic local scaling ladder over increasing zone/scenario counts to measure output, reducer, manifest, and hazard-builder timing before another live Balfrin scale step.

Capability gap reduced: Multi-zone pressure is currently scratch/fixture-backed at limited points, with no systematic ladder showing where bottlenecks appear.

Why this outranks alternatives: A local ladder can cheaply identify the next measured breakpoint and prevent premature live Balfrin submission.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/check_hazard_output_profile.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- A local scaling-ladder helper or report for 1, 2, 4, 8, and 12 zone-equivalent fixture workloads using reduced-output profiles.
- Measurements for runtime, phase timing if TB-297 exists, file counts, bytes, manifest bytes, reducer sidecars, and first bottleneck.
- Tests for deterministic ladder fixture generation and blocked budget classifications.

Definition of done:

- The repo has systematic local evidence for how output and reducer pressure grows before requiring live Balfrin execution.

Boundaries: Local/fixture scaling only; no live Balfrin submission, no distributed execution, no physical credibility claim, no Swiss-wide claim, and no operational claim.

### TB-302: Balfrin Run-Root Output Budget Auditor

Goal: Add a run-root auditor that can inspect preserved Balfrin roots and classify output budget compliance after execution.

Capability gap reduced: Post-run evidence preservation exists, but output-budget compliance needs to be measured directly from run roots, not only predicted from handoff packages.

Why this outranks alternatives: Scale claims require proving the actual run root stayed within file, byte, manifest, sidecar, and replayability budgets.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_probe_preservation_gate.py`

Deliverables:

- A read-only auditor for Balfrin run roots that reports per-family files/bytes, manifest bytes, sidecar counts, reducer chunks, hashes, missing replay-critical artifacts, and budget status.
- Integration into post-run collector or preservation-gate summaries.
- Fixture tests for compliant, oversized, incomplete, and missing-run-root cases.

Definition of done:

- Any future Balfrin run root can be classified against the output/reducer budget from preserved artifacts.

Boundaries: Read-only auditing only; no remote mutation, no live Balfrin submission, no new run, no claim upgrade, and no operational claim.

### TB-303: Scale Evidence Dashboard For Workers

Goal: Produce a compact worker-facing scale dashboard that summarizes the latest measured and blocked evidence for Balfrin execution efficiency, output size, reducer pressure, and next safe action.

Capability gap reduced: Scale evidence is fragmented across maturity snapshots, reducer docs, decision gates, and run-root reports.

Why this outranks alternatives: Workers need one short status surface to avoid re-running stale paths or treating projections as measured scale evidence.

Inspect first:

- `scripts/print_agent_task_context.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A scale dashboard command or extension to task context with latest measured tiers, blocked tiers, output-budget status, efficiency measurements, live-run authorization status, and next recommended scaling task.
- Clear labels for `measured_on_balfrin`, `fixture_backed`, `scratch_local`, `projection_only`, and `blocked_pre_submit`.
- Tests that prevent blocked multi-zone evidence from appearing as measured scale capability.

Definition of done:

- A worker can quickly answer whether output size and execution efficiency are under control for each scale tier without reading the whole repository.

Boundaries: Status/dashboard only; no live Balfrin submission, no new run, no claim upgrade, no scale-up authorization, and no operational claim.

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

Boundaries: No live Balfrin submission, tuning, operational claims, scale-up
authorization, or other phase changes unless the task explicitly allows them
and, for live Balfrin submission, the user has separately authorized the exact
run.
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
