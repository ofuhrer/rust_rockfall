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

### TB-392: Repair Multi-Zone Reduced Output Profile Gate

Goal: Remove the current `blocked_output_profile` obstacle for the smallest multi-zone hazard branch by making the handoff use the canonical rebuildable reduced-output mode and bounded GIS settings.

Capability gap reduced: Previous two-zone and four-zone hazard branches failed closed before `sbatch` because the submit package and output-profile expectations diverged from executable reduced-output contracts.

Why this outranks alternatives: Submitting another Balfrin job before the output-profile gate is executable would repeat the same fail-closed branch.

Inspect first:

- `scripts/build_management_aoi_balfrin_handoff.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `scripts/check_hazard_rebuild_output_profile.py`

Deliverables:

- A smallest multi-zone handoff package whose output-profile gate passes with rebuildable reduced outputs and bounded GIS/COG settings.
- Regression coverage showing full grid CSV, full conditional curves, excessive sidecars, and manifest mismatch still fail closed.
- Updated command-plan or handoff text only where needed to remove stale review-only profile references.

Definition of done:

- The relevant pre-submit output-profile check returns ready/accepted for the smallest executable multi-zone branch without weakening output-budget guardrails.

Boundaries: No live submission in this task, no summary-only rebuildability claim, no scale-up or operational claim.

### TB-393: Execute Smallest Real-AOI Multi-Zone Balfrin Probe

Goal: Submit and monitor the smallest real-AOI multi-zone Balfrin `postproc` hazard probe only after the prepared-pilot and reduced-output gates are ready.

Capability gap reduced: The repository still lacks measured multi-zone Balfrin hazard execution; projections and postproc microbenchmarks are not enough.

Why this outranks alternatives: This is the decisive evidence gap for management’s Swiss-scale feasibility question.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/collect_balfrin_probe_metrics.py`

Deliverables:

- If gates pass: measured job id, run root, runtime, memory, validation/hazard bytes, file counts, reducer metrics, preservation status, and failure/recovery notes.
- If gates fail: a fail-closed no-submit record naming the first persistent blocker and preserving exact next unblock action.
- Updated scale-readiness matrix row distinguishing measured execution from blocked or fixture-backed evidence.

Definition of done:

- The smallest real-AOI multi-zone branch is either measured on Balfrin `postproc` or blocked before `sbatch` by one current, non-stale gate with no ambiguous status.

Boundaries: GPT-5.5 worker required; `postproc` only; no non-postproc, MPI, GPU, distributed execution, scale-up authorization, operational claim, or physical-probability semantics.

### TB-394: Measure Compact Multi-Zone Reducer And Manifest Pressure

Goal: Measure how compact replay-preserving manifests and reduced output families change multi-zone reducer pressure relative to the current full scratch probe.

Capability gap reduced: Manifest size and reducer sidecars are repeatedly the first bottleneck in scale projections and failed pre-submit gates.

Why this outranks alternatives: Reducing manifest/output pressure improves every later Balfrin and Swiss-wide path without adding another orchestration layer.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/hazard_output_manifests.py`

Deliverables:

- Measured full-vs-compact reducer pressure for at least 2, 4, 8, and 12 release-zone scratch probes.
- Byte/file-count deltas by output family and manifest mode.
- A concrete recommendation for the default multi-zone manifest mode.

Definition of done:

- The reducer-pressure helper produces deterministic compact-mode measurements and the Swiss-scale projection can cite measured pressure reduction rather than only thresholds.

Boundaries: Scratch/local probe only unless explicitly authorized; no live Balfrin submission, no deletion of replay-critical metadata, no operational claim.

### TB-395: Consolidate AOI Prepared-Pilot State Assembly

Goal: Extract duplicated AOI prepared-pilot status, blocker, expected-output, and command-manifest assembly from the large AOI workflow scripts into a small shared helper.

Capability gap reduced: Workflow-shell complexity is growing faster than executable capability, especially around `plan_aoi_to_prepared_pilot_dry_run.py` and `run_aoi_hazard_workflow.py`.

Why this outranks alternatives: Consolidating repeated mechanics reduces future blocker drift without adding another wrapper or status vocabulary.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/build_management_aoi_balfrin_handoff.py`
- `scripts/lib/workflow_validation.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- Shared helper functions for prepared-pilot state assembly reused by at least two existing CLIs.
- No CLI output schema changes except removal of stale duplicated wording.
- Regression coverage proving current ready and blocked branches stay compatible.

Definition of done:

- Lines of duplicated blocker/status assembly are reduced, tests pass, and no new wrapper/report/gate is introduced.

Boundaries: Bounded refactor only; do not rewrite the AOI workflow, rename public statuses, or change scientific semantics.

### TB-396: Split Hazard Layer Packaging Primitives From Giant Builder

Goal: Move a narrow, tested slice of hazard-layer packaging or manifest-writing logic out of `scripts/build_hazard_layers.py` into an existing or new support module.

Capability gap reduced: `build_hazard_layers.py` is a high-risk 7000-line workflow surface that makes GIS/output changes fragile and expensive.

Why this outranks alternatives: A small extraction improves maintainability around the output surface that will be stressed by every larger AOI and multi-zone run.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_output_manifests.py`
- `scripts/hazard_output_reports.py`
- `scripts/hazard_output_writers.py`
- `tests/test_hazard_layers.py`

Deliverables:

- One cohesive packaging/manifest-writing primitive moved out of the giant builder with focused tests.
- Existing CLI behavior and output schemas preserved.
- A short inventory note identifying the next safe extraction seam, if one is obvious from the touched code.

Definition of done:

- The extracted primitive is imported by `build_hazard_layers.py`, relevant hazard-layer tests pass, and no broad rewrite or behavior drift occurs.

Boundaries: No hazard physics change, no output schema break, no new workflow wrapper, no large refactor beyond the selected primitive.

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
