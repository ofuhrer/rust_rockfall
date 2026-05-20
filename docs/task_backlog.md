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

### TB-397: Audit Clean-Checkout Dependence In Core Workflow Tests

Goal: Identify and fix the highest-risk core workflow tests or helpers that still depend on ignored local artifacts, Balfrin scratch state, or stale `/tmp` roots.

Capability gap reduced: Hidden local-state coupling makes CI and worker execution fragile, and it has repeatedly produced blocked or misleading task outcomes.

Why this outranks alternatives: Clean-checkout reliability is prerequisite infrastructure for safe autonomous workers and credible reproducibility.

Inspect first:

- `scripts/check_repo_consistency.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_hazard_layers.py`
- `scripts/print_agent_task_context.py`

Deliverables:

- A focused clean-checkout audit for core workflow tests, with at least one concrete hidden-state dependency removed or converted to an explicit fixture/skip/block condition.
- Regression coverage for the corrected behavior.
- No broad test-suite rewrite.

Definition of done:

- The targeted tests no longer require ignored local artifacts unless explicitly marked as live-artifact checks, and repo consistency/pre-commit pass.

Boundaries: Do not weaken tests by silently skipping real regressions; no generated artifact commits; no CI-only workaround.

### TB-398: Make AOI Workflow Front Door Self-Explaining

Goal: Improve the existing AOI front-door command so a user can see the current status, first blocker, and next copy-paste command without reading multiple helper reports.

Capability gap reduced: The user-facing AOI path is technically present but still exposes too many underlying scripts and nested reports.

Why this outranks alternatives: This improves usability by simplifying an existing entrypoint instead of adding another wrapper, report, or management surface.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `docs/public_real_site_geodata_preparation.md`
- `README.md`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- A concise text-mode AOI workflow output that includes `workflow_status`, `first_blocker`, `next_command`, required inputs, generated outputs, and claim boundaries.
- A stable `--help` or example path for the simplest bounds-to-review dry run.
- Focused tests proving the user-facing text output stays compact and copy-pasteable.

Definition of done:

- A new user can run one existing front-door command and see the next action without opening nested JSON reports or separate helper docs.

Boundaries: Do not add a new front-door script, do not hide blocked states, do not run Balfrin, and do not introduce operational claims.

### TB-399: Consolidate User-Facing AOI Documentation

Goal: Collapse duplicated AOI workflow instructions into one short user-facing path and point detailed helper material behind links.

Capability gap reduced: README, onboarding, public-geodata docs, and script inventory currently expose overlapping AOI instructions that make the workflow harder to follow.

Why this outranks alternatives: Documentation cleanup is justified here because it removes duplicated command paths and reduces context injection for future workers and users.

Inspect first:

- `README.md`
- `docs/onboarding.md`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `docs/script_inventory.md`

Deliverables:

- One canonical AOI quickstart path linked from README and onboarding.
- Low-level helper commands moved behind references instead of repeated in multiple user-facing docs.
- Script inventory labels that distinguish user-facing front doors from internal workflow helpers.

Definition of done:

- `rg` shows one canonical AOI quickstart section, low-level helpers remain discoverable, and no active command path is removed.

Boundaries: No new workflow semantics, no new report, no generated artifacts, no claim-boundary changes.

### TB-400: Retire Or Deprecate Redundant Workflow Shell Scripts

Goal: Identify redundant or historical top-level workflow scripts and either remove one safely or mark a small set as deprecated with exact replacement commands.

Capability gap reduced: The repository has accumulated many wrappers and status helpers, increasing maintenance cost and user confusion.

Why this outranks alternatives: Reducing script count or clearly marking replacements prevents further workflow-shell growth without a broad rewrite.

Inspect first:

- `docs/script_inventory.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_repo_consistency.py`

Deliverables:

- `rg`-backed inventory of candidate redundant scripts.
- At least one safe removal, or explicit deprecation metadata for the smallest high-confidence set with replacement commands and tests adjusted.
- Updated script inventory reflecting the reduced or deprecated surface.

Definition of done:

- No active doc, test, command plan, backlog task, or reproduction command references a removed script, and deprecated scripts point to a canonical replacement.

Boundaries: No giant framework rewrite, no deletion of high-risk workflow surfaces, no CLI break without a compatibility shim or documented replacement.

### TB-401: Extract Shared Command And Path Rendering Utilities

Goal: Consolidate repeated command-string, path-normalization, and expected-output rendering logic used by AOI workflow, prepared-pilot, and handoff helpers.

Capability gap reduced: Repeated shell-command and path-rendering logic causes drift in user-facing next commands and Balfrin handoff packages.

Why this outranks alternatives: This is a small maintainability improvement that supports both user-facing clarity and safer orchestration without adding a new layer.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/build_management_aoi_balfrin_handoff.py`
- `scripts/lib/workflow_validation.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- Shared utility functions for rendering repo-relative paths, shell commands, and expected-output path blocks.
- At least two existing helpers migrated to the shared functions.
- Regression tests showing user-facing next commands and handoff command manifests remain stable.

Definition of done:

- Duplicate command/path rendering is measurably reduced and existing JSON/text outputs stay compatible.

Boundaries: Bounded refactor only; no new wrapper, no status-vocabulary change, no Balfrin submission, and no scientific semantics change.

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
