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

Live Balfrin rule: a task may prepare, review, or preflight a Balfrin submission
package, but it may not submit a new live run unless the user gives an explicit
instruction for that exact run. The orchestrator must route any authorized live
run to a GPT-5.5 Balfrin worker and require the existing Balfrin access,
readiness, authorization, output-budget, preservation, and evidence gates. A
ready preflight, generated package, or backlog task is not authorization.

## Active Tasks

### TB-292: Balfrin Scale Readiness Baseline Matrix

Goal: Establish one authoritative baseline matrix for Balfrin scale readiness across single-zone, target-area, smallest multi-zone, and projected larger AOI runs.

Capability gap reduced: The project has many scale-related reports, but workers still have to reconcile output budget, reducer pressure, metrics completeness, access, and authorization state manually.

Why this outranks alternatives: Before changing execution or output behavior, the repo needs a single measured/blocked/projection matrix that names the exact blockers for each scale tier.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `docs/current_maturity_snapshot.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A compact scale-readiness report that classifies each tier as `measured`, `ready_for_exact_authorization`, `blocked_pre_submit`, `blocked_reducer_budget`, `projection_only`, or `no_go`.
- Explicit columns for file count, bytes, manifest bytes, reducer sidecars, runtime, memory, run-root preservation, replayability, and authorization status.
- Tests using existing fixture and blocked-preflight evidence.

Definition of done:

- A worker can answer, from one report, which Balfrin scale tier is currently measured, which is blocked, and which evidence field must change next.

Boundaries: Read-only synthesis only; no live Balfrin submission, no new run, no scale-up authorization, no distributed execution, no physical-probability semantics, and no operational claim.

### TB-293: Multi-Zone Output Budget Acceptance Thresholds

Goal: Convert the current multi-zone output-budget blockers into explicit acceptance thresholds for the smallest live Balfrin probe and the next larger review-only probe.

Capability gap reduced: The smallest multi-zone path blocks on `manifest_size_bytes`, but the acceptance thresholds and replay-critical exceptions are still spread across docs and tests.

Why this outranks alternatives: Reducer/manifest compression cannot be judged unless the target budget and non-negotiable replay fields are formalized first.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`
- `docs/hazard_output_profile_contract.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- Machine-readable budget thresholds for manifest bytes, total files, per-family files, sidecar counts, reducer chunks, retained replay-critical families, and package hashes.
- A validator mode that explains exactly which threshold is exceeded and whether the excess is replay-critical or compressible.
- Tests proving threshold failures remain distinct from missing authorization and dirty remote-state failures.

Definition of done:

- The multi-zone handoff has objective pass/fail budget criteria that can drive compression and later live-run authorization.

Boundaries: Budget contract only; no compression implementation, no live Balfrin submission, no scale-up authorization, no dropped replayability, and no operational claim.

### TB-294: Replay-Preserving Manifest Slimming Prototype

Goal: Prototype a replay-preserving compact manifest representation for the smallest multi-zone handoff that reduces manifest bytes without losing deterministic replay, hashes, merge order, or provenance.

Capability gap reduced: Multi-zone Balfrin execution is blocked by manifest-size pressure before the smallest live probe can run.

Why this outranks alternatives: Output size control must be proven on the current blocking artifact before adding more zones or workers.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/hazard_output_profile_contract.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- A compact manifest mode that deduplicates repeated path prefixes, shared output-family metadata, and repeated command-plan fields while preserving replay-critical hashes and merge order.
- Before/after report with manifest bytes, sidecar counts, replay-critical retained fields, deterministic package hash, and threshold status from TB-293.
- Regression tests showing replay metadata is still complete and the previous `manifest_size_bytes` blocker is reduced or explicitly proven irreducible.

Definition of done:

- The smallest multi-zone package either passes the manifest threshold or reports a smaller, replay-critical residual blocker with evidence.

Boundaries: Manifest/package representation only; no live Balfrin submission, no reducer math change, no output data deletion, no scale-up authorization, and no operational claim.

### TB-295: Balfrin Postproc Microbenchmark Harness

Goal: Add a bounded Balfrin postprocessing microbenchmark harness that measures filesystem, manifest scanning, reducer merge, and hazard packaging overhead independently from full simulation scale.

Capability gap reduced: Execution efficiency is not under control because the repo lacks measured Balfrin postproc overhead curves for the workflow shell.

Why this outranks alternatives: The likely scaling wall is Python/output/reducer/filesystem pressure, so microbenchmarks should isolate those costs before larger live probes.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A microbenchmark package generator for synthetic file-family roots with configurable file count, manifest size, sidecar count, and reducer chunk count.
- A postproc-node measurement plan that records wall time, CPU time where available, peak RSS, file scan time, merge time, package time, and bytes/files touched.
- Local fixture tests for package generation and parser behavior.

Definition of done:

- The repo can prepare an exact bounded Balfrin postproc microbenchmark package that measures workflow-shell overhead separately from physics execution.

Boundaries: Package/harness generation only unless separately authorized for live execution; no live Balfrin submission by default, no simulation, no physical claims, no operational claim, and no heavy generated files committed.

### TB-296: Authorized Balfrin Postproc Microbenchmark Run

Goal: Execute one exact bounded Balfrin postproc microbenchmark run if separately authorized, or record the exact pre-submit blocker.

Capability gap reduced: Output and reducer efficiency remain projection-heavy without direct postproc-node measurements.

Why this outranks alternatives: A tiny synthetic postproc benchmark is lower risk than a larger multi-zone simulation and directly measures the suspected scaling wall.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- If separate exact user authorization is present at execution time, one bounded SLURM postproc microbenchmark submission with fixed file-count/manifest-size parameters and deterministic run root.
- Preserved metrics for wall time, peak memory, file scan time, reducer merge time, package time, file counts, bytes, checksums, and SLURM accounting fields.
- If any preflight fails, a fail-closed blocker report with no submission.

Definition of done:

- The repo has either measured Balfrin postproc overhead evidence for a bounded synthetic scale point or one exact remaining pre-submit blocker.

Boundaries: Exact postproc microbenchmark only; live Balfrin submission requires separate explicit authorization at execution time; no simulation, no multi-zone hazard claim, no scale-up authorization, no retries without diagnosis, and no operational claim.

### TB-297: Hazard Builder Phase Timing Instrumentation

Goal: Add structured phase timing and memory telemetry to `build_hazard_layers.py` and its output-writer modules for input reading, accumulation, reducer merge, raster writing, COG/report writing, and manifest generation.

Capability gap reduced: Hazard-building efficiency cannot be controlled without phase-level measurements from real and fixture runs.

Why this outranks alternatives: Previous throughput evidence points at Python accumulation and output writing, but future optimization needs stable per-phase telemetry.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `scripts/hazard_output_reports.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_hazard_layers.py`

Deliverables:

- A stable timing JSON emitted by hazard-layer builds with per-phase wall time, input/output counts, bytes, grid dimensions, output-profile settings, and optional peak memory where available.
- Tests proving telemetry exists for fixture builds and does not change hazard outputs or manifest semantics.
- Documentation of timing fields in the throughput report or output-profile contract.

Definition of done:

- Every relevant hazard-layer build can produce comparable phase timing evidence without changing numerical outputs.

Boundaries: Instrumentation only; no performance optimization, no behavior change, no live Balfrin submission, no hazard-value changes, and no operational claim.

### TB-298: Hazard Accumulation Optimization Hypothesis Bench

Goal: Build a benchmark harness for candidate hazard-accumulation optimizations and require before/after evidence before any implementation is accepted.

Capability gap reduced: The repo has rejected broad performance churn once, but still lacks a safe way to evaluate targeted accumulation improvements.

Why this outranks alternatives: Execution efficiency must improve through measured hypotheses, not speculative rewrites of a fragile hazard builder.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_hazard_layers.py`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- A benchmark harness with representative fixture profiles for single-zone, smallest multi-zone, and output-heavy cases.
- Acceptance criteria for speedup, memory, output parity, deterministic manifests, and claim-boundary preservation.
- At least one no-op/baseline benchmark result that future optimization tasks must beat.

Definition of done:

- Future hazard-accumulation optimization work has a reproducible benchmark and objective acceptance thresholds.

Boundaries: Benchmark harness only; no optimization implementation unless trivially required for instrumentation, no live Balfrin submission, no hazard-value change, and no operational claim.

### TB-299: Reduced-Output Profile Enforcement In AOI Command Plans

Goal: Ensure every AOI and Balfrin command plan that can scale beyond tiny smoke defaults to the scalable reduced-output profile and fails closed on full grid CSV or full conditional-curve output.

Capability gap reduced: Output size is only partly controlled; command-plan drift can still reintroduce non-scalable output families.

Why this outranks alternatives: Preventing accidental high-output plans is cheaper and safer than cleaning up oversized run roots after execution.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/check_hazard_output_profile.py`
- `docs/hazard_output_profile_contract.md`
- `tests/test_pilot_command_plan.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A shared command-plan output-profile validator used by AOI and Balfrin planning paths.
- Fail-closed diagnostics for full grid CSV, full conditional curves, excessive worker/chunk sidecars, missing reduced-output flags, and missing rebuildability artifacts.
- Tests proving tiny smoke can opt into fixture-safe outputs while scalable plans require reduced-output defaults.

Definition of done:

- Scalable command plans cannot silently select output families known to be non-scalable.

Boundaries: Planning/profile enforcement only; no live Balfrin submission, no simulation, no output data deletion, no physical-probability semantics, and no operational claim.

### TB-300: Validation Output Budget Reduction Plan

Goal: Measure and reduce validation-output file fanout for target-area and multi-zone workflows while preserving replayability and required scientific diagnostics.

Capability gap reduced: Validation output has historically dominated file count and bytes, and can overwhelm useful hazard artifacts before Swiss-scale execution.

Why this outranks alternatives: Output size control is not complete until validation debug outputs are budgeted as strictly as hazard outputs.

Inspect first:

- `src/validation.rs`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_hazard_output_profile.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_pilot_command_plan.py`
- `tests/test_bounded_validation_output_profile.py`

Deliverables:

- A validation-output inventory for target-area and multi-zone plans, separating replay-critical files from diagnostic/debug files.
- A reduced validation-output mode or plan-level defaults that preserve manifests, hashes, summaries, and required trajectories while suppressing nonessential debug fanout.
- Tests proving reduced validation outputs remain replayable and evidence-preserving.

Definition of done:

- The largest validation-output families have explicit budgets and a reduced mode suitable for scalable AOI/Balfrin plans.

Boundaries: Validation output budgeting only; no physics change, no metric suppression without replacement summary evidence, no live Balfrin submission, no claim upgrade, and no operational claim.

### TB-301: Multi-Zone Local Scaling Ladder

Goal: Run a deterministic local scaling ladder over increasing zone/scenario counts to measure output, reducer, manifest, and hazard-builder timing before another live Balfrin scale step.

Capability gap reduced: Multi-zone pressure is currently scratch/fixture-backed at limited points, with no systematic ladder showing where bottlenecks appear.

Why this outranks alternatives: A local ladder can cheaply identify the next measured breakpoint and prevent premature live Balfrin submission.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/check_hazard_output_profile.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- A local scaling-ladder helper or report for 1, 2, 4, 8, and 12 zone-equivalent fixture workloads using reduced-output profiles.
- Measurements for runtime, phase timing if TB-297 exists, file counts, bytes, manifest bytes, reducer sidecars, and first bottleneck.
- Tests for deterministic ladder fixture generation and blocked budget classifications.

Definition of done:

- The repo has systematic local evidence for how output and reducer pressure grows before requiring live Balfrin execution.

Boundaries: Local/fixture scaling only; no live Balfrin submission, no distributed execution, no physical credibility claim, no Swiss-wide claim, and no operational claim.

### TB-302: Balfrin Run-Root Output Budget Auditor

Goal: Add a run-root auditor that can inspect preserved Balfrin roots and classify output budget compliance after execution.

Capability gap reduced: Post-run evidence preservation exists, but output-budget compliance needs to be measured directly from run roots, not only predicted from handoff packages.

Why this outranks alternatives: Scale claims require proving the actual run root stayed within file, byte, manifest, sidecar, and replayability budgets.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_probe_preservation_gate.py`

Deliverables:

- A read-only auditor for Balfrin run roots that reports per-family files/bytes, manifest bytes, sidecar counts, reducer chunks, hashes, missing replay-critical artifacts, and budget status.
- Integration into post-run collector or preservation-gate summaries.
- Fixture tests for compliant, oversized, incomplete, and missing-run-root cases.

Definition of done:

- Any future Balfrin run root can be classified against the output/reducer budget from preserved artifacts.

Boundaries: Read-only auditing only; no remote mutation, no live Balfrin submission, no new run, no claim upgrade, and no operational claim.

### TB-303: Scale Evidence Dashboard For Workers

Goal: Produce a compact worker-facing scale dashboard that summarizes the latest measured and blocked evidence for Balfrin execution efficiency, output size, reducer pressure, and next safe action.

Capability gap reduced: Scale evidence is fragmented across maturity snapshots, reducer docs, decision gates, and run-root reports.

Why this outranks alternatives: Workers need one short status surface to avoid re-running stale paths or treating projections as measured scale evidence.

Inspect first:

- `scripts/print_agent_task_context.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A scale dashboard command or extension to task context with latest measured tiers, blocked tiers, output-budget status, efficiency measurements, live-run authorization status, and next recommended scaling task.
- Clear labels for `measured_on_balfrin`, `fixture_backed`, `scratch_local`, `projection_only`, and `blocked_pre_submit`.
- Tests that prevent blocked multi-zone evidence from appearing as measured scale capability.

Definition of done:

- A worker can quickly answer whether output size and execution efficiency are under control for each scale tier without reading the whole repository.

Boundaries: Status/dashboard only; no live Balfrin submission, no new run, no claim upgrade, no scale-up authorization, and no operational claim.

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

Boundaries: No live Balfrin submission, tuning, operational claims, scale-up
authorization, or other phase changes unless the task explicitly allows them
and, for live Balfrin submission, the user has separately authorized the exact
run.
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
