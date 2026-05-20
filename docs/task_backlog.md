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

### TB-351: Multi-Zone Submit Contract Regeneration

Goal: Regenerate the smallest live multi-zone Balfrin hazard submit package so reviewed commands, authorization records, writable run roots, and executable manifest schema match exactly.

Capability gap reduced: Previous two-zone and four-zone live submit attempts failed closed before `sbatch` because package and executable contracts diverged.

Why this outranks alternatives: A measured multi-zone Balfrin hazard result cannot happen until the submit-contract mismatch is removed.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `docs/balfrin_two_zone_probe_tb309.md`

Deliverables:

- A regenerated two-zone live package with reviewed command, authorization/audit record, writable run root, executable manifest schema, and output-budget summary.
- Tests proving stale checksum, wrong schema, and unwritable root cases fail closed.

Definition of done:

- The authorization preflight reaches ready-for-submit for the smallest live multi-zone hazard package, without submitting the job.

Boundaries: No live Balfrin job in this task, no scale-up claim, no distributed execution.

### TB-352: Execute Smallest Multi-Zone Balfrin Hazard Run

Goal: Submit and monitor the regenerated smallest live multi-zone Balfrin hazard package under the existing `postproc` clearance.

Capability gap reduced: The repo lacks measured multi-zone Balfrin hazard execution evidence; current multi-zone evidence is dry-run, scratch-local, postproc-only, projection-only, or failed-closed.

Why this outranks alternatives: This is the key evidence needed to tell management whether scale is plausible beyond single-zone comfort.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`

Deliverables:

- Live job id, run root, exit status, wall time, memory, validation/hazard output counts and bytes, preservation evidence, and post-run collector output.
- A fail-closed report if access, authorization, output-budget, or preservation gates block submission.

Definition of done:

- The run either completes with measured multi-zone hazard evidence or fails before submission with a precise blocker and no ambiguous partial state.

Boundaries: GPT-5.5 worker required; `postproc` only; stop and rediscuss if fully occupying `postproc` for more than 6 hours; no operational or scale-up claim.

### TB-353: Integrate Measured Multi-Zone Hazard Evidence

Goal: Thread the TB-352 measured or fail-closed result through the scale readiness matrix, evidence bundle, management package, and Swiss-scale projection surfaces.

Capability gap reduced: Measured multi-zone evidence must become canonical and not remain an isolated run log.

Why this outranks alternatives: Without integration, future workers and management summaries can misclassify the current scale state.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Updated evidence labels, next-action ranking, management summary, and projection assumptions based on TB-352.
- Tests preventing failed-closed, measured, and partial states from being conflated.

Definition of done:

- The canonical helper outputs reflect the TB-352 outcome and identify the next measured action or deferral.

Boundaries: Synthesis/integration only; no new Balfrin job, no claim upgrade.

### TB-354: Four-Zone Hazard Package From Measured Two-Zone Evidence

Goal: Generate a four-zone hazard package only if TB-352 produced measured two-zone evidence and TB-353 integrated it successfully.

Capability gap reduced: The next scale rung needs to be derived from measured evidence rather than review-only or stale package assumptions.

Why this outranks alternatives: Four-zone hazard execution is the smallest meaningful step toward the existing 10-zone feasibility projection after two-zone evidence exists.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- Four-zone live hazard package with reduced outputs, output-budget gate, reducer/manifest budget, reviewed command, authorization/audit record, and expected artifact roots.
- Explicit defer/no-go classification if two-zone evidence is missing or budgets are exceeded.

Definition of done:

- The four-zone package is ready-for-submit or deferred with a specific measured blocker.

Boundaries: No live submission in this task, no distributed execution, no operational or scale-up claim.

### TB-355: Execute Four-Zone Balfrin Hazard Run

Goal: Submit and monitor the four-zone Balfrin hazard package if TB-354 reaches ready-for-submit.

Capability gap reduced: The 10-zone feasibility projection needs measured evidence at an intermediate hazard-execution rung.

Why this outranks alternatives: Four-zone measured execution reveals whether runtime/output pressure and reducer/manifest behavior stay inside the projected envelope.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`

Deliverables:

- Live job id, run root, exit status, wall time, memory, validation/hazard output counts and bytes, preservation evidence, and post-run collector output.
- Fail-closed report if readiness gates block submission.

Definition of done:

- The four-zone run is measured and preserved, or the task stops before submission with a precise blocker.

Boundaries: GPT-5.5 worker required; `postproc` only; stop and rediscuss if fully occupying `postproc` for more than 6 hours; no operational or scale-up claim.

### TB-356: Multi-Zone Reducer Merge Profile From Measured Runs

Goal: Profile reducer merge ordering, manifest fanout, sidecar counts, and replay-critical outputs using the measured multi-zone hazard run roots.

Capability gap reduced: Reducer pressure is currently partly scratch-local; measured run roots are needed to validate or revise the scaling assumptions.

Why this outranks alternatives: Reducer/manifest pressure is a primary blocker in Swiss-scale projection and must be measured before larger AOI claims.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `scripts/summarize_multi_zone_scaling_ladder.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- Measured reducer/manifest profile from two-zone and, if available, four-zone run roots.
- Updated thresholds or explicit deferral where measured roots lack required artifacts.

Definition of done:

- The reducer-pressure report distinguishes measured run-root evidence from scratch-local projections and updates the first bottleneck if needed.

Boundaries: Read-only analysis; no new Balfrin job, no distributed execution, no output semantics change.

### TB-357: Measured Hazard Accumulation Throughput Profile

Goal: Profile hazard accumulation throughput on the latest measured multi-zone hazard outputs and identify the dominant runtime phase.

Capability gap reduced: Previous optimization attempts were rejected or fixture-backed; any new optimization must start from a measured multi-zone bottleneck.

Why this outranks alternatives: Performance work is only worthwhile if tied to the measured scale path that management cares about.

Inspect first:

- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/hazard_accumulation_benchmark.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_multi_zone_hazard_throughput_profile.py`

Deliverables:

- Measured throughput profile from current multi-zone hazard artifacts, including dominant phase, wall time, input sizes, and acceptance threshold for any optimization.
- No-op/defer recommendation if no measured optimization target exists.

Definition of done:

- The repo has a measured, current hazard-accumulation bottleneck report or explicitly defers optimization due to missing measured input.

Boundaries: Profiling only; no physics or hazard-output changes, no new Balfrin job.

### TB-358: Bounded Hazard Accumulation Optimization From Measured Bottleneck

Goal: Implement one narrowly scoped hazard-accumulation optimization only if TB-357 identifies a measured bottleneck and a predeclared acceptance threshold.

Capability gap reduced: Scale feasibility depends on improving measured bottlenecks, not speculative refactors.

Why this outranks alternatives: This is the only justified optimization path after a measured bottleneck exists; otherwise it should record a no-retain decision.

Inspect first:

- `scripts/hazard_accumulation_benchmark.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_layers.py`

Deliverables:

- A retained optimization with before/after benchmark evidence, output equivalence checks, and acceptance-threshold result, or a no-retain report.

Definition of done:

- The optimization is either merged because it clears the measured acceptance floor without output changes, or explicitly rejected with evidence.

Boundaries: No physics changes, no tuning, no output semantic changes, no live Balfrin job.

### TB-359: Refresh Swiss-Scale Projection After Multi-Zone Evidence

Goal: Recompute the Swiss-scale feasibility projection and management package after the new acquisition, preprocessing, multi-zone execution, reducer, GIS, and performance evidence lands.

Capability gap reduced: Management needs the feasibility answer to track measured evidence rather than stale projections.

Why this outranks alternatives: This synthesis should happen only after the executable evidence tasks above, not before them.

Inspect first:

- `docs/swiss_scale_feasibility_projection.md`
- `docs/balfrin_scale_demonstration_management_package.md`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Updated projection table and management package that separate measured evidence, extrapolated assumptions, failed-closed branches, no-go thresholds, and unknowns.
- A recommendation for whether the 10-zone and 100-zone classes remain feasible, conditional, or out of reach.

Definition of done:

- Management can read one current projection and one current management package that reflect the latest measured multi-zone and AOI automation evidence.

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
