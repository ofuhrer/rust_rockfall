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

### TB-571: Rebuild The 16-Zone Handoff After Reducer Optimization

Goal: Re-run the 16-zone no-submit handoff after TB-570 to determine whether the package is live-run eligible.

Capability gap reduced: Converts reducer optimization into a concrete pass/fail pre-submit decision for the next Balfrin scale step.

Why this outranks alternatives: A larger live run should be attempted only after the optimized package passes the same review gates as smaller measured runs.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- Generate the optimized 16-zone handoff on a clean Balfrin-aligned checkout.
- Run authorization, output-budget, submit-contract, and remote-head alignment gates without submitting.
- Record exact ready/blocked status and later submit command.

Definition of done:

- The handoff is either `ready_for_bounded_postproc_submission` or fails closed with one concrete blocker that can be addressed before execution.

Boundaries: No `sbatch`, no live run, no non-postproc partition, no distributed execution, and no scientific/operational claim upgrade.

### TB-572: Execute One Optimized 16-Zone Postproc Probe If Gates Pass

Goal: Run one optimized 16-zone reduced-output Balfrin probe when TB-571 and the queue window both permit it.

Capability gap reduced: Provides the first current measured evidence beyond the 12-split/regional boundary under the reduced-output contract.

Why this outranks alternatives: This is the largest practical single-node/postproc measurement that can materially improve the feasibility demonstration without authorizing distributed execution.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Submit exactly one optimized 16-zone `postproc` job from the reviewed handoff if all gates pass.
- Monitor to terminal state.
- Record scheduler state, job id, exit code, elapsed time, MaxRSS, run root, queue state, and package hashes.

Definition of done:

- The job completes successfully or the failed/blocked result is captured with exact package, queue, and scheduler diagnostics; no ambiguous partial result is promoted.

Boundaries: One job only; `postproc` only; do not keep the partition fully busy for more than 6 hours; no distributed execution, no Swiss-wide run, no operational claim, and no physical-probability claim.

### TB-573: Collect And Promote 16-Zone Probe Metrics

Goal: Preserve and promote the TB-572 run-root evidence into the Balfrin evidence and scale-readiness surfaces.

Capability gap reduced: Turns a larger scheduler run into measured scale evidence with explicit output, memory, and preservation status.

Why this outranks alternatives: A large run is not useful for the project goal unless its outputs are collected, preserved, compared, and bounded by claim gates.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Collect metrics, run preservation and output-budget audits, and write a share-safe TB-572/TB-573 run report.
- Promote the 16-zone evidence into the evidence bundle and scale matrix with tests.
- Keep older measured runs available as historical comparisons.

Definition of done:

- Metrics contract is complete, preservation is ready or explicitly blocked with recovery, focused tests pass, and the promoted evidence does not upgrade physical or operational claims.

Boundaries: Evidence collection and promotion only; no rerun, no distributed execution, no annual-frequency claim, no operational claim, and no physical-probability claim.

### TB-574: Recompute Swiss-Scale Feasibility From Current Large-Run Evidence

Goal: Recompute the Swiss-scale feasibility projection using TB-566 and, if available, TB-573 measured evidence.

Capability gap reduced: Replaces stale projection coefficients with the latest measured Balfrin runtime, memory, reducer, and output-footprint data.

Why this outranks alternatives: The project needs an honest feasibility statement before considering any further scale step or demonstration narrative.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_large_scale_execution_probe.py`

Deliverables:

- Update projection inputs and outputs from the latest measured run evidence.
- Distinguish 10-zone, 16-zone, 100-zone, regional, and Swiss-wide feasibility classes.
- Name the next blocker as runtime, memory, output bytes, reducer pressure, queue policy, or missing scientific evidence.

Definition of done:

- Focused projection tests pass and the projection document/report clearly separates measured evidence, extrapolation, no-go classes, and claim boundaries.

Boundaries: Projection only; no Swiss-wide run, no distributed execution authorization, no operational claim, and no physical-probability claim.

### TB-575: Build A Balfrin Demonstration Evidence Package For Review

Goal: Package the latest measured Balfrin efficiency, performance, output, preservation, and feasibility evidence into one reviewer-facing demonstration surface.

Capability gap reduced: Converts scattered run reports and helper outputs into a coherent demonstration of what has been achieved and what remains blocked.

Why this outranks alternatives: A full demonstration needs one reproducible entry point, not a chain of historical TB reports.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/project_overview.md`
- `docs/current_maturity_snapshot.md`
- `README.md`

Deliverables:

- Refresh the management demo package from the latest measured evidence.
- Ensure README/project overview point to the current performance and Balfrin demonstration surfaces without overclaiming.
- Include exact reproduction commands and live evidence boundaries.

Definition of done:

- Focused management package tests pass and the package clearly reports measured efficiency/performance/feasibility evidence plus remaining scientific and scale blockers.

Boundaries: Packaging and documentation only; no new run, no operational claim, no annual-frequency claim, and no physical-probability claim.

### TB-576: Add A Queue-Aware Balfrin Run Gate To Prevent Missed Capacity Windows

Goal: Make the Balfrin run decision gate aware of live queue capacity, age of access preflight, and package freshness.

Capability gap reduced: Avoids manual judgment drift when Balfrin is empty or busy and prevents stale packages from blocking opportunistic execution.

Why this outranks alternatives: The current decision surfaces know package evidence but not whether the partition is currently usable; this caused the “empty Balfrin” opportunity to require manual review.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Add a small queue snapshot parser/classifier that can be fed into the next-run decision gate.
- Classify capacity as `run_now`, `run_soon`, `defer_due_to_capacity`, or `unknown`.
- Add tests for empty queue, busy queue, stale preflight, and remote-head mismatch.

Definition of done:

- Focused tests pass and the next-run decision report can explain whether the current live queue state supports immediate postproc submission.

Boundaries: Decision logic only; no `sbatch`, no queue polling loop, no job cancellation, no non-postproc partition, and no claim upgrade.

### TB-577: Publish Current Balfrin Performance Evidence On The GitHub Pages Dashboard

Goal: Extend the public performance dashboard with a clearly separated Balfrin measured-performance section.

Capability gap reduced: Makes Balfrin efficiency evidence visible outside raw docs and work logs while keeping CI diagnostics separate.

Why this outranks alternatives: The project front door should show both CI performance trend and measured Balfrin feasibility when large-run evidence exists.

Inspect first:

- `scripts/performance_ci_tracking.py`
- `.github/workflows/performance_main.yml`
- `README.md`
- `docs/performance_ci_tracking.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Add a generated Balfrin evidence JSON/SVG/table section to the Pages artifact using promoted measured run data.
- Keep CI runner timings and Balfrin scheduler timings visually and semantically separate.
- Link the new section from README only with bounded claim language.

Definition of done:

- Focused performance tracking tests pass, local site generation includes the Balfrin section, and Pages paths remain stable for `/performance/latest.json` and `/performance/main_performance.svg`.

Boundaries: Publishing/reporting only; no new run, no scientific validation claim, no operational claim, and no benchmark-as-validation claim.

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
