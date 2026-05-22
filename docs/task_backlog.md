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

### TB-448: Collect Regional Split Run-Root Metrics And Preservation Evidence

Goal: Collect validation/hazard output counts, bytes, reducer metrics, preservation status, and manifest pointers from the regional split run root if TB-447 submitted successfully.

Capability gap reduced: Turns a raw regional split run into auditable measured evidence that can be compared against projections and dashboards.

Why this outranks alternatives: A submitted job is not useful scale evidence until runtime/output and preservation evidence are collected and classified.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- Regional split run-root metrics JSON/text or failed-closed collection report.
- Validation and hazard file counts/bytes split by output family where possible.
- Reducer/postproc timing and peak-memory evidence when scheduler data allows it.
- Preservation and replay-critical artifact status.

Definition of done:

- Measured run-root evidence is collected for the regional split branch, or collection fails closed with exact missing artifact/access classes and no fixture-backed promotion.

Boundaries: GPT-5.5 Balfrin-capable worker recommended. Read-only evidence collection only; do not fabricate metrics from fixtures, do not rerun the job, and do not upgrade claim boundaries.

### TB-449: Integrate Regional Split Evidence Into Scale Readiness Surfaces

Goal: Thread the TB-447/TB-448 regional split outcome into the scale readiness matrix, Swiss-scale projection, management package, and maturity snapshot.

Capability gap reduced: Prevents the repo from continuing to describe regional split status from stale TB-432 evidence after a new retry has completed or failed closed.

Why this outranks alternatives: Management-facing feasibility claims depend on correctly separating measured, failed-closed, blocked, and projection-only regional evidence.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Updated helper output and tests for the regional split evidence class.
- Updated docs reflecting the new measured or failed-closed state.
- Explicit next-action recommendation based on the new outcome.

Definition of done:

- The scale dashboard and management docs no longer point at stale TB-432 as the latest regional split state, and the new status is covered by focused tests.

Boundaries: Synthesis only; no new Balfrin submission, no claim promotion beyond measured evidence actually collected, and no operational or physical-probability semantics.

### TB-450: Compare Regional Split Measurement Against Scenario And Output Projections

Goal: Compare measured regional split runtime/output/reducer pressure against existing scenario-cardinality and output-tier projections.

Capability gap reduced: Replaces projection-only regional split assumptions with a measured-versus-expected delta for planning the next larger probe.

Why this outranks alternatives: The next scaling decision should be driven by measured deltas, not another wrapper or status report.

Inspect first:

- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Deterministic measured-versus-projected delta summary for runtime, file count, bytes, manifest size, and reducer pressure.
- Focused tests using fixtures or preserved measured regional split evidence.
- One recommended next probe class or explicit no-go blocker.

Definition of done:

- The repo can answer whether the regional split measurement stayed within expected pressure bands and what bottleneck ranks next.

Boundaries: No new ensemble, no live submission, no scale-up authorization, and no operational or risk/exposure/vulnerability claims.

### TB-451: Harden Regional Split Retry Idempotency And Remote Hygiene

Goal: Prevent future regional split retries from being blocked by stale generated checkout files or reused `/tmp` package state.

Capability gap reduced: Reduces hidden local/remote state coupling in the Balfrin retry workflow.

Why this outranks alternatives: TB-432 failed entirely on remote checkout hygiene, so hardening idempotency directly removes a repeated operational failure mode.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- Preflight/report improvements that identify stale regional split artifacts with exact preserve/clean guidance.
- Package generation that records current remote HEAD, access preflight path, and scratch-package freshness.
- Tests covering stale generated file detection or stale package rejection.

Definition of done:

- A stale remote/package state fails closed before submission with a clear remediation path, and a fresh state is distinguishable in machine-readable output.

Boundaries: No remote deletion unless explicitly encoded as operator guidance or done under an already documented cleanup procedure; no live job submission and no claim upgrade.

### TB-452: Promote Adjacent-Candidate Scenario Path Into Prepared-Pilot Smoke

Goal: Connect the accepted adjacent-candidate source zone and generated scenario table into a tracked prepared-pilot smoke path without running a full ensemble.

Capability gap reduced: Bridges candidate review, scenario generation, and prepared-pilot packaging so the next scale probes do not depend on hand-curated path assumptions.

Why this outranks alternatives: The maturity snapshot says the adjacent-candidate path replaced stale source-zone-overlap repair as the active management-AOI path, but it still needs an executable smoke handoff.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`

Deliverables:

- Fixture-backed or scratch-only prepared-pilot smoke path using adjacent-candidate scenario outputs.
- Stable manifest fields linking source candidate id, scenario table id, and command-plan target.
- Focused tests that avoid ignored artifact dependence.

Definition of done:

- A clean checkout can exercise candidate-to-scenario-to-prepared-pilot smoke coverage and fail closed on missing real inputs without relying on stale Tschamut artifacts.

Boundaries: No live Balfrin job, no physics changes, no source-frequency semantics, no operational release-zone claim, and no generated heavy artifacts committed.

### TB-453: Measure Regional GIS And COG Package Pressure

Goal: Measure GIS package and COG conversion pressure for the regional split or closest available regional-output fixture without promoting it to operational GIS readiness.

Capability gap reduced: Quantifies whether GIS/COG packaging becomes the next bottleneck after regional split execution.

Why this outranks alternatives: GIS/export polish is secondary, but regional-scale packaging pressure is a likely practical blocker once runtime evidence exists.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/build_hazard_layers.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Measured or fixture-backed GIS/COG file-count, byte-count, raster-count, and conversion-status summary.
- Explicit distinction between standard-root blocked status and converted-package readiness.
- Tests or smoke checks for the pressure summary.

Definition of done:

- The scale projection can name whether regional GIS/COG packaging is measured, fixture-backed, or blocked, and what exact next action would unblock it.

Boundaries: No operational GIS claim, no QGIS manual QA claim, no live run unless already measured outputs exist, and no generated raster commits.

### TB-454: Reduce Regional Split Manifest And Replay Metadata Pressure

Goal: Use the latest measured or fixture-backed regional split artifacts to remove avoidable manifest/replay metadata growth without losing reproducibility-critical fields.

Capability gap reduced: Reduces the manifest/replay pressure that blocks 100-zone and regional planning.

Why this outranks alternatives: The Swiss-scale projection ranks scenario cardinality, manifest size, and replay metadata growth ahead of hazard throughput for larger planning cases.

Inspect first:

- `scripts/generate_balfrin_regional_split_submission_package.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- One bounded manifest/replay compaction or deduplication change.
- Before/after byte and field-count comparison.
- Regression coverage proving deterministic reconstruction still works.

Definition of done:

- Manifest/replay metadata pressure is measurably lower or the task documents a tested no-op result with the next bottleneck clearly identified.

Boundaries: No deletion of replay-critical provenance, no loss of deterministic rebuildability, no live submission, and no claim upgrade.

### TB-455: Refill Backlog From Regional Split Outcome

Goal: After the regional split retry and integration tasks, perform a compact gap analysis and refill the backlog with the next executable worker-sized tasks.

Capability gap reduced: Keeps the queue aligned with measured regional evidence rather than stale projection or failed-closed assumptions.

Why this outranks alternatives: Downstream work should depend on whether the regional split retry measured, failed closed, or exposed a new dominant bottleneck.

Inspect first:

- `docs/task_backlog.md`
- `docs/current_maturity_snapshot.md`
- `docs/swiss_scale_feasibility_projection.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- 6-10 prioritized executable tasks based on the latest regional split outcome.
- Removal or deferral of stale tasks whose dependencies did not materialize.
- Updated capability-gap framing only where materially changed.

Definition of done:

- The active backlog is non-empty, ordered by dependency, and contains only worker-sized executable tasks that name concrete outputs or measurements.

Boundaries: Planning/refill only; do not add process-only tasks, claim upgrades, distributed execution, operational semantics, annual-frequency modeling, risk/exposure/vulnerability workflows, or large production ensembles.

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
