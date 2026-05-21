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

### TB-442: Add Clean-Checkout AOI Workflow Smoke Test

Goal: Prove the documented AOI front-door commands fail closed or pass using only tracked fixtures and no ignored local artifacts.

Capability gap reduced: Hidden local-state dependence in the user-facing AOI workflow.

Why this outranks alternatives: User-facing documentation is only useful if its core commands behave predictably on a clean checkout.

Inspect first:

- `docs/aoi_user_manual.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/package_aoi_hazard_map.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- Focused tests for `describe-config`, `prepare`, `candidate-review`, `package-map`, and `workflow` using tracked fixtures or explicit blocked states.
- Assertions that ignored Tschamut/Balfrin artifacts are not required for the smoke path.
- Documentation correction if any command in the AOI manual is not clean-checkout safe.

Definition of done:

- The compact AOI user path has clean-checkout regression coverage or explicit fail-closed behavior for missing artifacts.

Boundaries: No broad full-suite rewrite, no generated artifact commits, no reliance on local ignored roots.

### TB-443: Connect QGIS Connector Manifest To AOI Smoke Coverage

Goal: Ensure the QGIS Processing connector manifest remains synchronized with the AOI front-door commands and style bundle as they evolve.

Capability gap reduced: Prototype UI contract drift.

Why this outranks alternatives: TB-430 introduced the bridge specification; a small sync test prevents it from becoming stale while avoiding a full plugin.

Inspect first:

- `tests/fixtures/qgis_processing_connector_manifest_v1.json`
- `tests/test_qgis_processing_connector_manifest.py`
- `docs/aoi_user_manual.md`
- `qgis/styles/aoi_qgis_style_bundle.json`

Deliverables:

- Extended static or smoke test coverage comparing manifest actions to AOI manual command names and available CLI subcommands.
- Clear failure messages when a command or style asset is renamed without updating the manifest.
- Optional concise note in `docs/aoi_user_manual.md` if the synchronization contract changes.

Definition of done:

- The QGIS connector manifest cannot silently drift from the documented AOI command path or tracked style assets.

Boundaries: No plugin, no GUI, no new execution layer, no operational map claim.

### TB-444: Rank Next Balfrin Probe Candidates From Measured Bottlenecks

Goal: Generate a compact, deterministic next-probe ranking from the latest measured and failed-closed Balfrin evidence.

Capability gap reduced: Ambiguity about whether to retry regional split, batch scenarios, optimize reducer pressure, or collect more local evidence next.

Why this outranks alternatives: The backlog should follow measured blockers rather than accumulating unrelated wrappers.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_regional_split_probe_gate_tb428.md`
- `docs/balfrin_multi_zone_hazard_run_tb407.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A deterministic ranking of the next bounded Balfrin probe candidates with blocker, expected evidence gain, and required pre-submit gates.
- Tests or fixture assertions for the ranking logic.
- Documentation update only if it replaces stale next-action wording.

Definition of done:

- The next live Balfrin action is ranked from current evidence and points to one concrete executable task, not a generic scale-up request.

Boundaries: Ranking only unless another task authorizes submission; no scale-up, distributed execution, or operational claim.

### TB-445: Refresh Management Feasibility Summary After Regional And AOI Updates

Goal: Update the management-facing feasibility summary after TB-431 through TB-444 clarify regional split, AOI, candidate, scenario, and QGIS readiness.

Capability gap reduced: Management-facing status drift after executable changes.

Why this outranks alternatives: This should happen after the execution and automation blockers are updated, not before, so it synthesizes measured progress instead of creating another projection-only report.

Inspect first:

- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Concise updated management status explaining what is measured, what is blocked, and what remains projected.
- Explicit answer to whether 10-zone, 100-zone, regional, and Swiss-wide workflows are feasible under current constraints.
- No duplicate evidence package if existing surfaces can be updated.

Definition of done:

- Management-facing docs agree with the latest measured evidence and failed-closed blockers, and the next recommended executable milestone is explicit.

Boundaries: Synthesis only after upstream evidence tasks; do not upgrade failed-closed or projection-only evidence into measured capability.

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
