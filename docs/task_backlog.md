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

### TB-527: Route One AOI Workflow Through A Single Existing Front Door

Goal: Make one documented AOI path runnable through `scripts/run_aoi_hazard_workflow.py` or another existing front-door command instead of a chain of individually invoked helper scripts.

Capability gap reduced: Converts a multi-script user workflow into a simpler command path while preserving existing helper internals.

Why this outranks alternatives: Users should not need to learn low-level helper names before they can produce or inspect a local AOI package.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `docs/aoi_user_manual.md`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- Add or tighten one front-door mode, option, or documented invocation that delegates to existing helpers for a bounded local AOI workflow.
- Update focused tests or fixtures so the front-door command remains the documented path.

Definition of done:

- The focused AOI/front-door tests pass and the user manual no longer requires direct invocation of at least one lower-level helper for that path.

Boundaries: Existing front-door routing only; no new script, no new data source, no operational claim, and no Balfrin dependency.

### TB-528: Merge One Redundant Status Summary Into Maturity Snapshot

Goal: Remove or demote one redundant status/report document by preserving its still-useful content in `docs/current_maturity_snapshot.md` or an existing archive.

Capability gap reduced: Reduces the number of active docs a reader must scan to understand current project state.

Why this outranks alternatives: Many docs are historical reports or narrowly scoped summaries; active status should converge on one maintained snapshot.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/next_development_targets.md`
- `docs/roadmap_recommendation_matrix.md`
- `docs/hazard_workflow_scale_review.md`
- `docs/archive/README.md`

Deliverables:

- Pick one stale or overlapping active doc, preserve any current actionable point in an existing active doc, then move the stale file to `docs/archive/` or replace it with a short pointer if links require it.
- Update references that pointed users at the stale active doc.

Definition of done:

- Link/reference checks pass, the active docs list is smaller or clearer, and no current scientific evidence is lost.

Boundaries: Documentation consolidation only; no new doc file, no claim upgrade, no deletion of unique evidence, and no Balfrin dependency.

### TB-529: Convert One Summarizer Script Into A Library Helper Or Existing Command Option

Goal: Eliminate one narrow `summarize_*` script from the direct command surface by moving reusable logic behind an existing command or library helper.

Capability gap reduced: Reduces script sprawl while preserving the measured output or summary behavior users still need.

Why this outranks alternatives: There are 52 `summarize_*` scripts; retiring one representative narrow script establishes the pattern for shrinking the command surface.

Inspect first:

- `scripts/summarize_local_scientific_progress.py`
- `scripts/recommend_local_scientific_backlog.py`
- `scripts/run_ci_local.py`
- `tests/test_local_scientific_progress.py`
- `tests/test_local_scientific_backlog_recommendation.py`

Deliverables:

- Move one selected summarizer's reusable logic into an existing module or expose it through an existing command path, then mark or remove the redundant direct script if tests allow.
- Preserve existing JSON fields consumed by tests or docs.

Definition of done:

- Focused tests pass, direct script count is reduced or the script is clearly marked internal/deprecated through existing inventory, and no summary capability is lost.

Boundaries: One-script consolidation only; no new command, no new report surface, no scientific claim change, and no Balfrin dependency.

### TB-530: Simplify Local CI Entry Points

Goal: Make `scripts/run_ci_local.py` the obvious local verification entry point and hide duplicate test incantations from first-line docs.

Capability gap reduced: Reduces local-vs-CI drift and lowers onboarding friction.

Why this outranks alternatives: A clean user interface needs one verification command before it needs more workflow features.

Inspect first:

- `scripts/run_ci_local.py`
- `README.md`
- `docs/onboarding.md`
- `tests/python_test_tiers.toml`
- `.github/workflows`

Deliverables:

- Update README/onboarding so the default local verification path starts with one `run_ci_local.py` command and secondary direct commands are clearly optional.
- Add or update a focused test/check if the CI-suite command mapping is not already covered.

Definition of done:

- Local CI runner help or focused tests pass, README/onboarding references are consistent, and direct command duplication in front-door docs is reduced.

Boundaries: Verification interface simplification only; no CI workflow expansion, no new script, and no Balfrin dependency.

### TB-531: Move Balfrin-Specific User Noise Out Of The Main Front Door

Goal: Keep Balfrin/HPC details available but prevent them from dominating the initial user-facing path.

Capability gap reduced: Separates ordinary local users from advanced scale/HPC operators.

Why this outranks alternatives: Many active docs and scripts are Balfrin-specific; the public front door should emphasize local reproducible workflows first.

Inspect first:

- `README.md`
- `docs/aoi_user_manual.md`
- `docs/balfrin_skills.md`
- `docs/balfrin_tschamut_pilot_runbook.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Update front-door docs so Balfrin is linked as an advanced scaling topic, not part of the first local path.
- Preserve the explicit Balfrin runbooks and orchestration guidance for agents/operators.

Definition of done:

- README/AOI manual remain link-valid and local-first, while Balfrin docs remain reachable through one advanced/scaling link.

Boundaries: Documentation navigation only; no Balfrin workflow change, no access/preflight change, no operational claim, and no remote execution.

### TB-532: Consolidate AOI Manual Command Blocks

Goal: Reduce duplicated or low-level command blocks in the AOI user manual so a user can follow one minimal local path.

Capability gap reduced: Makes the main AOI workflow easier to execute and less brittle as helper internals change.

Why this outranks alternatives: The AOI manual is the practical front door; simplification there directly improves user experience.

Inspect first:

- `docs/aoi_user_manual.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_second_site_public_geodata_preflight.py`

Deliverables:

- Replace one cluster of low-level AOI helper commands with a shorter front-door invocation or a generated command-plan reference.
- Keep expert commands available in a clearly labeled advanced section.

Definition of done:

- AOI manual remains accurate, referenced commands exist, and the main path has fewer required direct script calls.

Boundaries: User manual simplification only; no new workflow semantics, no new data acquisition, no operational claim, and no Balfrin dependency.

### TB-533: Add A Deprecated-Internal Script Warning For One Legacy Helper Family

Goal: Prevent new users from invoking legacy/internal helper scripts directly when a better front-door path exists.

Capability gap reduced: Shrinks the practical command surface without risky file deletion.

Why this outranks alternatives: Some scripts may still be used by tests or agents; warnings are a safer first step than broad deletion.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/plan_release_plan_dry_run.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- Add one consistent warning, help text, or inventory classification for a small legacy helper family that points users to the supported front-door command.
- Preserve existing behavior for tests and internal automation.

Definition of done:

- Focused command/help tests pass and the deprecated/internal helper family points to the supported path without breaking existing callers.

Boundaries: Warning/classification only; no script deletion, no new wrapper, no workflow claim change, and no Balfrin dependency.

### TB-534: Create A Minimal User-Facing Smoke Path

Goal: Provide one small local smoke path that exercises the Rust core and one reviewable output without requiring users to understand the full research workflow.

Capability gap reduced: Gives users a fast confidence-building path from checkout to visible result.

Why this outranks alternatives: A clean interface needs a tiny end-to-end experience, not only tests and specialist AOI commands.

Inspect first:

- `README.md`
- `examples/inclined_plane.json`
- `scripts/run_ci_local.py`
- `docs/aoi_user_manual.md`
- `tests/terrain_edge_cases.rs`

Deliverables:

- Document and, if necessary, lightly adjust one existing example or command so it produces a small deterministic output and names where to inspect it.
- Reuse existing examples and commands; do not add a new app, dashboard, or dataset.

Definition of done:

- The documented smoke command runs locally or has focused test coverage, produces a deterministic small output, and appears in the README quick start.

Boundaries: Minimal local smoke only; no new physics, no new dataset, no operational claim, and no Balfrin dependency.

### TB-535: Prune One Generated-Or-Archived Reference From Active Navigation

Goal: Remove one obsolete generated-output or archive-style reference from active navigation so active docs only point to maintained surfaces.

Capability gap reduced: Reduces reader confusion between current user guidance and historical agent/research artifacts.

Why this outranks alternatives: The docs tree contains many run reports and archive files; active navigation should not invite users into stale state unless explicitly historical.

Inspect first:

- `README.md`
- `docs/archive/README.md`
- `docs/current_maturity_snapshot.md`
- `docs/agent_reference.md`
- `docs/agent_work_log.md`

Deliverables:

- Find one active navigation link or reference that points to historical/generated detail, replace it with a maintained high-level link, and keep the historical target reachable from `docs/archive/README.md` or agent-specific docs.

Definition of done:

- Link checks pass, active navigation is cleaner, and no unique historical record is deleted.

Boundaries: Navigation pruning only; no content deletion unless it is a duplicate pointer, no claim change, and no Balfrin dependency.

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
