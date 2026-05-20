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

### TB-333: Integrate Four-Zone Hazard Evidence

Goal: Integrate the four-zone hazard probe outcome into the scale dashboard, maturity snapshot, reducer-pressure docs, and next-run decision surface.

Capability gap reduced: New measured scale evidence must update projections and next-run choices before larger work is proposed.

Why this outranks alternatives: The decision to attempt eight zones or optimize depends on the measured four-zone hazard outcome.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Scale dashboard row for the four-zone hazard branch with evidence label, metrics, output pressure, and next recommended action.
- Updated local-vs-Balfrin comparison preserving postproc-only and hazard-execution distinctions.
- Tests for evidence taxonomy and next-action ranking.

Definition of done:

- The repo can state whether four-zone hazard execution supports an eight-zone probe, requires optimization, or should be deferred.

Boundaries: Evidence integration only; no new Balfrin job, no claim upgrade, no annual/physical/risk semantics.

### TB-334: Hazard Accumulation Profiling At Multi-Zone Scale

Goal: Profile hazard accumulation, raster writing, reducer merge, and manifest generation using the largest available measured/local multi-zone artifacts.

Capability gap reduced: TB-313 rejected one accumulator micro-optimization; future performance work needs a new measured bottleneck and acceptance floor.

Why this outranks alternatives: Optimization should follow measured phase costs, not broad speculation.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/build_hazard_layers.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Phase-level profile for available two/four-zone evidence or scratch-local ladder artifacts.
- Identification of the dominant bottleneck and a numeric acceptance threshold for any proposed optimization.
- Explicit no-op recommendation if no bottleneck clears the threshold.

Definition of done:

- The next performance task has a measured target, or performance work is explicitly deferred.

Boundaries: Profiling/analysis only unless a trivial measurement harness fix is required; no physics changes, no new Balfrin job, no operational claim.

### TB-335: Implement Measured Hazard Throughput Improvement

Goal: Implement one narrowly scoped performance improvement only if TB-334 identifies a measured bottleneck with a defensible acceptance threshold.

Capability gap reduced: Multi-zone feasibility may depend on reducing the dominant local or Balfrin hazard-build bottleneck.

Why this outranks alternatives: A targeted measured optimization can improve scale feasibility, but only after profiling prevents churn.

Inspect first:

- `docs/hazard_throughput_bottleneck_report.md`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_layers.py`
- `tests/test_multi_zone_scaling_ladder.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`

Deliverables:

- One scoped implementation change tied to the measured bottleneck.
- Before/after runtime or phase timing evidence meeting the predeclared threshold, or a reverted/no-op result if it fails.
- Tests proving output equivalence and deterministic manifests.

Definition of done:

- The repo either lands a measured throughput improvement or records a rejected optimization without changing behavior.

Boundaries: No physics changes, no output semantics changes, no tuning, no live Balfrin submission unless a later task authorizes measurement, no operational claim.

### TB-336: Reducer And Manifest Scaling Hardening

Goal: Reduce or bound reducer sidecar, manifest, and merge pressure for multi-zone AOI runs without losing rebuildability.

Capability gap reduced: Multi-zone scale can fail on manifest/sidecar pressure even when trajectory execution is acceptable.

Why this outranks alternatives: TB-309/TB-314 evidence shows manifest and reducer artifacts are central scale gates.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_multi_zone_reducer_pressure.py`
- `tests/test_output_budget_reducer_gate.py`

Deliverables:

- Hardening change or stricter bounded policy for reducer manifests/sidecars across 2/4/8/12-zone projections.
- Tests showing rebuild-critical files remain present while debug fanout is bounded.
- Updated reducer-pressure docs and scale-dashboard inputs if policy changes.

Definition of done:

- Multi-zone reducer pressure is lower or more explicitly bounded without breaking hazard rebuild compatibility.

Boundaries: Output/reducer policy only; no trajectory physics changes, no live Balfrin job, no operational or scale-up claim.

### TB-337: Large-AOI GIS And COG Packaging Stress Test

Goal: Stress-test GIS package generation, QA-review HTML, manifest size, and COG conversion behavior on a realistically large AOI package shape.

Capability gap reduced: A Balfrin feasibility demonstration must show that hazard outputs can become usable diagnostic map packages at larger AOI sizes.

Why this outranks alternatives: GIS packaging is secondary to execution, but it can still become the first user-facing bottleneck once multi-zone runs succeed.

Inspect first:

- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/pilot_gis_package.md`
- `tests/test_large_aoi_gis_cog_stress_test.py`
- `tests/test_aoi_hazard_map_packager.py`

Deliverables:

- Large-AOI package stress report with raster/vector counts, COG timing, manifest bytes, QA HTML size, file count, and first blocker.
- Explicit classification of ready, COG-blocked, or no-go package sizes.
- Tests for deterministic stress outputs and claim-boundary labels.

Definition of done:

- The repo can project GIS/COG package practicality for the next multi-zone Balfrin demonstration size.

Boundaries: Packaging stress only; no hazard-value changes, no live Balfrin submission, no operational claim, no annual/physical/risk semantics.

### TB-338: Swiss-Scale Feasibility Projection From Measured Evidence

Goal: Produce a measured-evidence-based projection for 10, 100, regional, and Swiss-scale AOI workflows using current release-zone, scenario, runtime, reducer, and GIS evidence.

Capability gap reduced: Management needs a defensible answer on whether Swiss-scale execution is feasible or out of reach under current architecture.

Why this outranks alternatives: This projection should come after two/four-zone, release/scenario, and packaging evidence are integrated.

Inspect first:

- `scripts/estimate_large_scale_execution.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `docs/current_maturity_snapshot.md`
- `docs/hazard_workflow_scale_review.md`

Deliverables:

- Swiss-scale projection report separating measured evidence, extrapolated assumptions, no-go thresholds, and unknowns.
- Runtime, storage, reducer, manifest, GIS/COG, and operator-effort estimates for defined AOI sizes.
- Recommendation of feasible, conditionally feasible, or out-of-reach under current single-node/postproc constraints.

Definition of done:

- The repo can give management a bounded, evidence-labeled Swiss-scale feasibility projection without overclaiming.

Boundaries: Projection and synthesis only; no new run, no Swiss-scale authorization, no operational claim, no annual/physical/risk semantics.

### TB-339: Balfrin Scale Demonstration Management Package

Goal: Produce a concise management-facing package that explains current Balfrin feasibility, measured scale evidence, failed-closed branches, next run choice, and Swiss-scale projection.

Capability gap reduced: Technical evidence is now distributed across many helpers and needs one bounded demonstration narrative for decision makers.

Why this outranks alternatives: Management needs a clear projection and next decision after the measured multi-zone and Swiss-scale projection tasks, not another raw technical report.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_balfrin_management_demo_package.py`

Deliverables:

- Management package summarizing measured Balfrin evidence, AOI automation maturity, Swiss-scale feasibility classification, top blockers, and recommended next run.
- Clear separation of measured, projection-only, failed-closed, and deferred evidence.
- Explicit non-operational and no-physical-frequency boundaries.

Definition of done:

- A non-technical reader can understand whether the current architecture plausibly scales, what evidence supports that answer, and what must be done next.

Boundaries: Management synthesis only after evidence/projection tasks; no claim upgrade, no new Balfrin job, no operational claim, no annual/physical/risk semantics.

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
