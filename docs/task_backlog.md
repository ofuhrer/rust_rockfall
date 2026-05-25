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

### TB-488: Extend The Local Multi-Zone Scaling Ladder

Goal: Run the existing local multi-zone scaling ladder after recent reducer/writer changes and advance the first blocker by reducing one measured bottleneck if feasible.

Capability gap reduced: Keeps scale decisions tied to current measured reducer/output behavior rather than stale ladder results.

Why this outranks alternatives: Larger Balfrin runs should be informed by the latest local reducer and output-pressure evidence.

Inspect first:

- `scripts/summarize_multi_zone_scaling_ladder.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_bounded_reducer_runtime_scaling.py`

Deliverables:

- Re-run the existing local scaling ladder and record the current first blocker.
- If the first blocker is a bounded local output/runtime issue, implement one targeted existing-path reduction and re-measure.

Definition of done:

- Scaling-ladder tests pass, before/after ladder metrics are recorded, and the next blocker is smaller, later, or explicitly unchanged with evidence.

Boundaries: Local bounded scaling evidence only; no Swiss-wide claim, no distributed execution, no operational claim, and no new scale dashboard.

### TB-489: Execute The Next Bounded Balfrin Postproc Probe

Goal: Run the next repository-gated bounded Balfrin `postproc` probe that is ready after local candidate/scenario and output-pressure checks.

Capability gap reduced: Converts scale readiness into measured execution evidence instead of projection-only status.

Why this outranks alternatives: The current scale frontier needs measured larger multi-zone hazard execution, not another local-only summary.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `scripts/submit_balfrin_probe.py`
- `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`

Deliverables:

- Run the existing readiness/access/output-budget gates and submit only if they are ready under the standing `postproc` clearance.
- Preserve the run root and collect runtime, memory, output-file, output-byte, reducer, and manifest metrics using existing collectors.

Definition of done:

- Either one bounded `postproc` run completes with preserved measured evidence, or the attempt fails closed before submission with a concrete blocker and the smallest next unblock action.

Boundaries: `postproc` only under existing clearance; no non-postproc partition, distributed execution, Swiss-wide scale-up claim, operational claim, annual-frequency claim, or physical-probability claim.

### TB-490: Compare Measured Regional Split Against Projections

Goal: Thread the measured regional split evidence into the existing scenario-cardinality and output-tier projection surfaces so the next scale recommendation is based on measured deltas.

Capability gap reduced: Replaces stale projection-only scale recommendations with measured regional-split comparison evidence.

Why this outranks alternatives: The maturity snapshot says the regional split branch is now measured and the next blocker is comparison work before further live recommendation.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_regional_gis_cog_pressure.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Update existing scale/projection surfaces to consume the measured regional split metrics where they currently rely on older projection-only or failed-closed branches.
- Produce one refreshed recommendation that names the next executable measured run or blocker.

Definition of done:

- Focused scale/projection tests pass, the refreshed output differentiates measured regional split evidence from projections, and no new dashboard/report script is added.

Boundaries: Evidence comparison only; no new live run, no operational claim, no Swiss-wide authorization, and no physical-probability or annual-frequency semantics.

### TB-491: Consolidate Scenario Pressure Helpers

Goal: Reduce duplicated scenario/output-pressure logic by consolidating overlapping calculations into one existing helper path.

Capability gap reduced: Simplifies the repo so scenario scale estimates remain maintainable as candidate/scenario workflows grow.

Why this outranks alternatives: The repo has several scenario-pressure surfaces; reducing duplicated logic lowers drift while still supporting executable scale decisions.

Inspect first:

- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `tests/test_aoi_scenario_preview.py`
- `tests/test_management_aoi_scenario_pressure.py`
- `tests/test_scenario_storage_output_tier_pressure.py`

Deliverables:

- Move duplicated scenario-count/output-pressure calculations into one existing module or helper function.
- Remove at least one redundant code path or reduce duplicated logic while preserving existing CLI outputs consumed by tests.

Definition of done:

- The focused scenario-pressure tests pass, repository consistency passes, and the diff shows simplification rather than another wrapper or report layer.

Boundaries: Simplification only; no new script, no new contract, no status-vocabulary change unless tests prove compatibility.

### TB-492: Consolidate Release-Candidate Review Logic

Goal: Simplify the release-zone candidate generation/review path by consolidating duplicated candidate metrics, review CSV, and GeoJSON/mask emission logic.

Capability gap reduced: Makes source-zone candidate review easier to maintain before adding more sites or candidate classes.

Why this outranks alternatives: Candidate generation is now on the critical path; duplicated output logic will create drift as reviewed candidates feed scenarios.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_release_candidate_zero_result_diagnostic.py`

Deliverables:

- Consolidate duplicated candidate-review output or metric-building logic inside existing candidate scripts.
- Preserve existing manifest fields and outputs while reducing local duplication or deleting dead code.

Definition of done:

- Focused candidate tests pass, generated candidate artifacts remain loadable, and the change removes or consolidates code rather than adding a new workflow surface.

Boundaries: Internal simplification only; no new source-zone semantics, no tuning, no operational claim, and no new script.

### TB-493: Shrink Generated-Result Clutter

Goal: Reduce generated-result clutter by tightening one existing output path, fixture path, or cleanup rule that currently leaves stale artifacts around local runs.

Capability gap reduced: Keeps the repo easier to inspect and faster to test as more measured outputs are produced.

Why this outranks alternatives: Scientific and scale work will keep generating artifacts; the repo needs active simplification to avoid accumulating stale ignored outputs and accidental fixtures.

Inspect first:

- `.gitignore`
- `tests/test_hazard_layers.py`
- `tests/test_bounded_validation_output_profile.py`
- `scripts/check_repo_consistency.py`

Deliverables:

- Identify one duplicated or stale generated-result family under an ignored output root that is produced by existing tests or local workflows.
- Tighten the existing writer, fixture setup, cleanup, or ignore/consistency rule so that family is no longer left behind unnecessarily.

Definition of done:

- Relevant tests and repository consistency pass, local generated clutter is measurably reduced or better contained, and no ignored generated outputs are accidentally committed.

Boundaries: Repository simplification only; do not delete unique observed evidence, real-terrain inputs, provenance records, or current benchmark fixtures.

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
