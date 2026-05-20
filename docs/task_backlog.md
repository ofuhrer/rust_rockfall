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

### TB-384: Unblock Management AOI Release-Candidate Screening

Goal: Replace the current zero-screenable-cell management AOI candidate blocker with a bounded, real-staged candidate-generation path or a precise deferral.

Capability gap reduced: Multi-zone scenario generation and Balfrin execution cannot proceed while the real AOI terrain crop/footprint leaves no screenable candidate cells.

Why this outranks alternatives: Downstream Balfrin handoff, execution, and Swiss-scale projection tasks now only restate the same upstream blocker; this task targets the blocker directly.

Inspect first:

- `scripts/diagnose_release_candidate_zero_result.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc`
- `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml`

Deliverables:

- A deterministic diagnostic or preparation update that resolves whether the blocker is AOI extent, terrain crop size, source-zone footprint overlap, slope band, or missing real input.
- Either a non-empty real-staged candidate package ready for review, or an explicit no-go/deferral record naming the required AOI/crop/source-zone replacement.

Definition of done:

- Scenario generation remains blocked only if a concrete upstream data/preparation requirement is named; otherwise a non-empty candidate package exists and downstream scenario-generation work can resume.

Boundaries: No threshold tuning to force candidates, no field-validation claim, no operational release-zone claim, no scenario generation, no hazard run, and no Balfrin submission.

### TB-385: Rebuild Management AOI Scenario And Prepared-Pilot Chain

Goal: Re-run the management-AOI scenario-pressure and prepared-pilot chain after TB-384 resolves or defers the candidate-screening blocker.

Capability gap reduced: The scenario/prepared-pilot state must reflect the current candidate evidence rather than stale zero-candidate propagation.

Why this outranks alternatives: Balfrin handoff cannot be meaningful until the scenario table and prepared-pilot compiler are synchronized with the latest candidate package or explicit deferral.

Inspect first:

- `scripts/summarize_management_aoi_scenario_pressure.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Updated deterministic scenario-pressure and prepared-pilot reports that either consume a non-empty candidate package or preserve TB-384's explicit deferral reason.
- Tests covering the current candidate-evidence branch and the first downstream blocker.

Definition of done:

- The management-AOI prepared-pilot compiler no longer reports a stale zero-screenable-cell diagnosis; it is either ready for handoff or blocked on the current named requirement.

Boundaries: No invented candidates, no source-frequency semantics, no annual probability, no hazard execution, and no Balfrin submission.

### TB-386: Rebuild Management AOI Balfrin Handoff Decision

Goal: Rebuild the management-AOI Balfrin handoff and no-submit/run decision after the scenario/prepared-pilot chain is current.

Capability gap reduced: The Balfrin execution decision must reflect the latest prepared-pilot state instead of stale TB-380/TB-381 blocked artifacts.

Why this outranks alternatives: Live Balfrin work should resume only when the handoff package has current candidate, scenario, budget, and authorization evidence.

Inspect first:

- `scripts/build_management_aoi_balfrin_handoff.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Updated handoff classification and execution decision: ready for a GPT-5.5 `postproc` run, blocked by current inputs/budgets/access, or explicitly deferred.
- If ready, exact next submit package and preservation requirements; if blocked, first persistent blocker and no-submit evidence.

Definition of done:

- The Balfrin decision surface is current and does not rely on stale zero-candidate artifacts.

Boundaries: GPT-5.5 worker for Balfrin-facing inspection; no live submission unless all gates pass under the standing `postproc` authorization rule; no scale-up or operational claim.

### TB-387: Refresh Management Feasibility Projection From Current Branch

Goal: Refresh the management-facing Swiss-scale feasibility projection after the candidate, prepared-pilot, and Balfrin-decision branch has been rebuilt.

Capability gap reduced: Management needs a current feasibility answer that separates measured progress, upstream data blockers, failed-closed branches, and extrapolation assumptions.

Why this outranks alternatives: A feasibility synthesis is useful only after the current execution branch has stopped at the right layer.

Inspect first:

- `docs/swiss_scale_feasibility_projection.md`
- `docs/balfrin_scale_demonstration_management_package.md`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Updated projection table separating measured evidence, extrapolated assumptions, failed-closed branches, no-go thresholds, and unknowns.
- Recommendation for the next 10-zone, 100-zone, regional, and Swiss-wide feasibility steps.

Definition of done:

- Management can read one current feasibility package that reflects the latest candidate-screening and Balfrin-decision evidence.

Boundaries: Synthesis only; no new run, no Swiss-scale authorization, no operational claim, no annual/physical/risk semantics.

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
