# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is done, remove it from this file and add a short
entry to `docs/agent_work_log.md`. Record only durable technical decisions in
`docs/decision_log.md`.

Progress rule: prefer runs, measurements, code, data, and simplification over
new process artifacts.

Reports, checks, validators, YAML records, checklists, and evidence packages are
useful only when they directly enable a run, measurement, acquisition,
reproducibility step, or simplification.

Orchestrator rule: work the active tasks in numeric order and keep `main`
usable. Full sequential-loop guidance lives in `docs/orchestration_strategy.md`.

Live Balfrin rule: the user has granted standing clearance for GPT-5.5 workers
to submit and actively monitor jobs on Balfrin's `postproc` partition. Multiple
concurrent `postproc` jobs are allowed, including filling the partition. If a
run plan would keep `postproc` fully busy for more than 6 hours, stop and
rediscuss. Keep run roots on `$SCRATCH` and preserve enough metadata to replay
and compare the result.

## Active Tasks

### TB-574: Execute One 16-Zone Diagnostic Postproc Probe If Checks Pass

Goal: Submit and monitor one 16-zone diagnostic reduced-output Balfrin `postproc` job from the reviewed diagnostic package if TB-573 passes.

Capability gap reduced: Provides the first current single-node measured evidence beyond the 12-split/regional boundary under the softened diagnostic profile.

Why this outranks alternatives: Balfrin is currently underutilized, and this is the most direct measurement waiting by the old review budget.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `docs/orchestration_strategy.md`
- `docs/balfrin_skills.md`

Deliverables:

- Submit exactly one reviewed 16-zone diagnostic `postproc` job from the Balfrin checkout when checks pass.
- Monitor to terminal state.
- Record scheduler state, job id, exit code, elapsed time, MaxRSS, run root, queue state, package hashes, and scratch/persistence paths.

Definition of done:

- The job completes successfully, or the exact package, queue, scheduler, and run-root reason for not completing is recorded.


### TB-575: Collect And Promote 16-Zone Diagnostic Metrics

Goal: Preserve and promote the TB-574 run-root evidence into the Balfrin evidence and scale-readiness surfaces.

Capability gap reduced: Turns the larger diagnostic scheduler run into measured scale evidence with explicit runtime, memory, output, preservation, and evidence status.

Why this outranks alternatives: A Balfrin run is not useful unless its outputs are collected, compared, and bounded immediately while the run root is fresh.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Collect metrics, run preservation and output-budget audits, and write a share-safe 16-zone diagnostic run report.
- Promote the 16-zone diagnostic evidence into the evidence bundle and scale matrix with tests.
- Keep older measured runs available as historical comparisons instead of replacing them.

Definition of done:

- Metrics are complete enough to compare the run, preservation status is clear, and focused tests pass.


### TB-576: Update The Measured Batch Ceiling From Diagnostic Evidence

Goal: If TB-575 measured evidence is complete, update the measured single-node batch ceiling and next-step recommendation from the 16-zone diagnostic run.

Capability gap reduced: Prevents the repo from continuing to block at the stale `simultaneous_release_zone_batch_max=8` ceiling after a larger run has been measured.

Why this outranks alternatives: Without this update, follow-on packages will keep failing currently deferred against obsolete local scratch constraints.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_multi_zone_reducer_pressure.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Thread the measured 16-zone ceiling into reducer-pressure constraints and next-run decision surfaces.
- Keep a separate `diagnostic_single_node_postproc` provenance label so the ceiling is not mistaken for operational scale capability.
- Add tests showing 16-zone is measured, the next proposed diagnostic step is explicit, and evidence labels stay diagnostic.

Definition of done:

- Focused reducer/scale/decision tests pass and the next blocker is no longer the stale 8-zone ceiling when 16-zone evidence is present.


### TB-577: Add A Queue-Aware Diagnostic Run Planner

Goal: Make diagnostic Balfrin run decisions aware of live `postproc` capacity, package freshness, expected wall time, and the six-hour partition-fill limit.

Capability gap reduced: Lets the repo exploit low Balfrin utilization without ad hoc manual judgment or stale package submissions.

Why this outranks alternatives: The standing clearance already allows multiple `postproc` jobs, but the repo lacks a compact planner that turns queue state into bounded diagnostic run choices.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/balfrin_capacity_window_tb563.md`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Add a queue snapshot parser/classifier for single and small batches of diagnostic `postproc` jobs.
- Classify capacity as `run_now`, `run_batch_now`, `run_soon`, `defer_due_to_capacity`, or `unknown`.
- Include stale-preflight, remote-head mismatch, expected-walltime, and six-hour partition-fill checks.

Definition of done:

- Focused tests pass and the next-run decision report can explain whether the current live queue supports one or several bounded diagnostic `postproc` submissions.


### TB-578: Build A 24-Zone Diagnostic Handoff From The Updated Ceiling

Goal: Generate a no-submit 24-zone compact reduced-output diagnostic package after the 16-zone ceiling update.

Capability gap reduced: Prepares the next single-node scale measurement while preserving the same readiness check discipline.

Why this outranks alternatives: A 24-zone package is a tangible next step that can still fit within single-node `postproc` measurement rather than jumping to regional or Swiss-wide runs.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- Generate a 24-zone diagnostic handoff on a clean Balfrin-aligned checkout without submitting.
- Run access, authorization, output-budget, diagnostic-profile, submit-contract, remote-head, and scratch/preservation checks.
- Record exact ready/waiting status and later submit command.

Definition of done:

- The package is diagnostic-measurement ready or does not pass with one concrete blocker and a smaller recovery command.


### TB-579: Execute One 24-Zone Diagnostic Postproc Probe If Checks Pass

Goal: Submit and monitor one 24-zone diagnostic reduced-output `postproc` job if TB-578 passes and the queue planner permits it.

Capability gap reduced: Extends measured single-node evidence beyond 16 zones without changing execution architecture.

Why this outranks alternatives: If Balfrin remains empty, this is the next measurement that can materially sharpen runtime, memory, and output scaling.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/orchestration_strategy.md`
- `docs/balfrin_skills.md`

Deliverables:

- Submit exactly one reviewed 24-zone diagnostic `postproc` job when checks pass.
- Monitor to terminal state.
- Record scheduler state, job id, elapsed time, MaxRSS, output footprint, queue state, run root, and package hashes.

Definition of done:

- The job completes successfully or fails with exact scheduler/package/run-root diagnostics; no partial result is promoted.


### TB-580: Collect And Promote 24-Zone Diagnostic Metrics

Goal: Preserve and promote TB-579 run-root evidence into scale, performance, preservation, and feasibility surfaces.

Capability gap reduced: Converts the 24-zone diagnostic run into durable measured evidence and comparison data.

Why this outranks alternatives: Larger runs only help the project if their evidence is immediately captured and bounded.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Collect metrics and preservation status from the 24-zone run root.
- Promote the evidence into the evidence bundle, scale matrix, and performance comparison surfaces.
- Compare 16-zone, 24-zone, regional split, and historical runs with clear evidence labels.

Definition of done:

- Metrics contract is complete or explicitly waiting with recovery, focused tests pass, and the evidence is visible in current scale surfaces.


### TB-581: Execute A Small Repeatability Pair At The Best Measured Diagnostic Size

Goal: Run two additional diagnostic `postproc` jobs at the largest size that has passed checks to measure runtime/output variability.

Capability gap reduced: Adds repeatability evidence instead of relying on one lucky or unlucky scheduler observation.

Why this outranks alternatives: Scientific feasibility needs variance and repeatability, not only larger maxima.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Submit at most two reviewed diagnostic `postproc` jobs when the queue planner says the combined expected occupancy stays under the six-hour bound.
- Use distinct run roots under `$SCRATCH` and preserve package hashes for each run.
- Monitor both jobs to terminal state and record scheduler/output metrics.

Definition of done:

- Two terminal results are captured, or the batch does not pass before submission with exact queue/package/check diagnostics.


### TB-582: Collect Repeatability Metrics And Variance Bounds

Goal: Collect the TB-581 run roots and compute simple variance bounds for elapsed time, MaxRSS, output bytes, and file counts.

Capability gap reduced: Turns opportunistic repeated Balfrin runs into quantified performance stability evidence.

Why this outranks alternatives: Variance bounds make the feasibility assessment more useful than a single best-run comparison.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/performance_ci_tracking.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_performance_ci_tracking.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Add a compact repeatability comparison surface for same-size diagnostic runs.
- Report min/median/max or equivalent bounded summaries for runtime, memory, and output footprint.
- Promote measurement stability only.

Definition of done:

- Focused tests pass and the repeatability evidence is visible in performance/scale reports.


### TB-583: Recompute Swiss-Scale Feasibility From The New Diagnostic Evidence

Goal: Recompute the Swiss-scale feasibility projection using the latest 16/24-zone and repeatability evidence when available.

Capability gap reduced: Replaces stale projection coefficients with current measured Balfrin runtime, memory, reducer, and output-footprint data.

Why this outranks alternatives: The project needs an honest feasibility statement before considering regional, multi-node, or Swiss-wide phase changes.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_large_scale_execution_probe.py`

Deliverables:

- Update projection inputs and outputs from the latest measured diagnostic evidence.
- Distinguish 10-zone, 16-zone, 24-zone, 100-zone, regional, and Swiss-wide feasibility classes.
- Name the next blocker as runtime, memory, output bytes, reducer pressure, queue policy, or missing scientific evidence.

Definition of done:

- Focused projection tests pass and the projection clearly separates measured evidence, extrapolation, and deferred classes.


### TB-584: Build A Reviewer-Facing Balfrin Diagnostic Evidence Package

Goal: Package the latest measured Balfrin efficiency, performance, output, preservation, repeatability, and feasibility evidence into one reviewer-facing demonstration surface.

Capability gap reduced: Converts scattered run reports and helper outputs into a coherent demonstration of what has been achieved and what remains next.

Why this outranks alternatives: A full demonstration needs one reproducible entry point, not a chain of historical TB reports.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/project_overview.md`
- `docs/current_maturity_snapshot.md`
- `README.md`

Deliverables:

- Refresh the management demo package from the latest measured evidence.
- Ensure README/project overview point to current performance and Balfrin demonstration surfaces without overselling the result.
- Include exact reproduction commands, run-root hashes, and live evidence boundaries.

Definition of done:

- Focused management package tests pass and the package clearly reports measured efficiency/performance/feasibility evidence plus remaining scientific and scale blockers.


### TB-585: Publish Current Balfrin Diagnostic Performance On GitHub Pages

Goal: Extend the public performance dashboard with a clearly separated Balfrin diagnostic-performance section.

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
- Link the new section from README only with bounded diagnostic-evidence language.

Definition of done:

- Focused performance tracking tests pass, local site generation includes the Balfrin section, and Pages paths remain stable for `/performance/latest.json` and `/performance/main_performance.svg`.


### TB-586: Reassess Scientific Validation Gaps After The Diagnostic Scale Push

Goal: Identify which scientific-validation gaps remain after the larger Balfrin diagnostic evidence is collected.

Capability gap reduced: Prevents performance progress from being mistaken for physical validation progress.

Why this outranks alternatives: Once larger runs are feasible, the main project risk shifts back toward calibration, holdout evidence, source frequency, and terrain/context validation.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/audit_conditional_denominator_provenance.py`
- `scripts/audit_trajectory_deposition_traceability.py`
- `docs/current_maturity_snapshot.md`
- `docs/validation_data_schema.md`

Deliverables:

- Run and refresh the local scientific-gap assessment using current evidence.
- Rank the next field/data/acquisition tasks that would convert diagnostic hazard maps into scientifically stronger validation evidence.
- Keep performance feasibility and scientific validity explicitly separated.

Definition of done:

- Focused scientific-gap checks pass and the output names the next concrete validation-data acquisition or calibration task.


### TB-587: Simplify The Large-Run Interface Around One Command Path

Goal: Consolidate the diagnostic handoff, preflight, submit, collect, and promote path into one simple user-facing command sequence .

Capability gap reduced: Reduces repo complexity and makes the successful large-run workflow approachable after the diagnostic scale push.

Why this outranks alternatives: The repo has accumulated many reports and scripts; after the measurement sprint, users need one clean path for reproducing the demonstrated workflow.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `README.md`

Deliverables:

- Identify duplicate or stale large-run entry points and replace them with one documented command sequence.
- Keep detailed helper scripts available internally but expose one primary path from README/project overview.
- Add smoke tests or command-plan checks proving the path still materializes the required files.

Definition of done:

- Focused smoke checks pass and the front-door docs present one clean large-run diagnostic workflow .


### TB-588: Define The Evidence Check For Physical-Probability Products

Goal: Convert the physical-probability target into an explicit evidence check with data requirements, acceptance criteria, and failure modes.

Capability gap reduced: Names the missing source-frequency, release-probability, block-population, calibration, and holdout evidence required before conditional outputs can become physical-probability products.

Why this outranks alternatives: Performance progress cannot open physical-probability products unless the repo first defines a scientifically defensible check.

Inspect first:

- `docs/validation_data_schema.md`
- `docs/real_case_intensity_frequency_implementation_roadmap.md`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/audit_conditional_denominator_provenance.py`
- `scripts/audit_trajectory_deposition_traceability.py`

Deliverables:

- Add or update one machine-readable/reportable physical-probability readiness check that lists required evidence classes and exact pass/fail criteria.
- Wire the check into the scientific-gap assessment so it reports missing evidence instead of relying on prose boundaries.
- Add tests or fixture checks covering conditional-only, partially calibrated, and fully evidence-ready states.

Definition of done:

- Focused validation/calibration checks pass and the repo can explain what evidence is still needed for physical-probability products.


### TB-589: Build A Source-Frequency Evidence Intake Path

Goal: Add a concrete local intake workflow for source-frequency and release-rate evidence needed by physical-probability and annual-frequency products.

Capability gap reduced: Turns one of the largest physical-probability blockers from an abstract missing-data class into a testable data-ingestion contract.

Why this outranks alternatives: Without source-frequency evidence, larger Balfrin runs can only remain conditional diagnostics.

Inspect first:

- `docs/validation_data_schema.md`
- `docs/real_case_intensity_frequency_implementation_roadmap.md`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `tests/test_public_real_site_conditional_pilot_run.py`

Deliverables:

- Define the source-frequency intake schema and a fixture-backed acceptance/rejection path.
- Add a small example fixture or contract stub that records provenance, temporal support, uncertainty, and explicit non-production status.
- Make the scientific-gap report distinguish missing, partial, and accepted source-frequency evidence.

Definition of done:

- Focused intake/gap tests pass and accepted fixture evidence moves the physical-probability assessment to the next missing evidence class.


### TB-590: Add Calibration And Holdout Separation Checks

Goal: Require explicit separation between calibration evidence and holdout validation evidence before stronger scientific conclusions can pass.

Capability gap reduced: Prevents overfitting and makes validation maturity auditable rather than narrative.

Why this outranks alternatives: Physical-probability and operational products need independent validation evidence, not just tuned parameters or successful runs.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/validation_data_schema.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_public_real_site_conditional_pilot_run.py`

Deliverables:

- Add a check that rejects stronger scientific conclusions when calibration and validation evidence share the same event/site/sample without an explicit holdout label.
- Add tests for missing holdout, overlapping holdout, and separated holdout evidence.
- Report the next required acquisition step when holdout evidence is absent.

Definition of done:

- Focused tests pass and the scientific-gap assessment can classify calibration/holdout status without manual interpretation.


### TB-591: Define Operational Readiness Acceptance Criteria

Goal: Convert the operational-readiness target into a concrete readiness checklist and readiness check.

Capability gap reduced: Names the reproducibility, QA, monitoring, provenance, versioning, review, and user-warning requirements needed for an operational candidate workflow.

Why this outranks alternatives: Operational readiness is not a performance problem alone; it requires process and product controls that are currently absent.

Inspect first:

- `docs/project_overview.md`
- `docs/roadmap_hazard_mapping.md`
- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Add an operational-readiness check or report that aggregates scientific validation, reproducibility, GIS/package QA, provenance, and support-status inputs.
- Ensure current outputs do not pass with concrete missing criteria.
- Add tests or smoke checks for diagnostic-only, review-ready, and operational-candidate states.

Definition of done:

- Focused readiness checks pass and the repo can state exactly which operational-readiness criteria remain unmet.


### TB-592: Build A Second-Site Validation Acquisition Plan

Goal: Create an executable acquisition and validation plan for a second real site that can support portability and holdout evidence.

Capability gap reduced: Moves beyond single-AOI demonstration toward the multi-site evidence needed for operational and physical-probability confidence.

Why this outranks alternatives: A Swiss workflow cannot be credible from one Tschamut/Balfrin site alone.

Inspect first:

- `scripts/audit_multisite_source_scenario_contract.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/validation_data_schema.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Define the second-site acquisition checklist for terrain, context, release-zone provenance, observed runout/deposition, source-frequency, and holdout labels.
- Add a machine-readable blocker report that distinguishes public-geodata blockers from field/observational evidence blockers.
- Identify the first executable local or external data task needed for the second site.

Definition of done:

- Focused multisite/scientific checks pass and the backlog can route from generic “second site missing” to a concrete acquisition task.


### TB-593: Assess Non-Postproc Partition Requirements And Risks

Goal: Determine what evidence and safeguards are needed before any non-`postproc` Balfrin partition could be responsibly requested.

Capability gap reduced: Turns the non-postproc path into a concrete resource, policy, and reproducibility assessment.

Why this outranks alternatives: Non-postproc access should be driven by measured bottlenecks and scheduler policy, not convenience.

Inspect first:

- `docs/balfrin_skills.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Add a non-postproc readiness report that compares measured CPU, memory, runtime, IO, walltime, and partition-policy needs.
- Identify whether the next blocker is walltime, memory, queue policy, CPU count, IO, or unsupported execution model.
- Keep the report as an assessment unless a future task explicitly authorizes a non-postproc phase change.

Definition of done:

- Focused decision/readiness checks pass and the repo can justify why non-postproc remains currently deferred or what exact evidence would support a request.


### TB-594: Design A Distributed Execution Contract Without Running It

Goal: Specify the chunking, merge, idempotency, restartability, and provenance contract required for distributed execution.

Capability gap reduced: Converts distributed execution from a currently deferred boundary into an implementable architecture contract.

Why this outranks alternatives: Distributed execution should not be attempted until merge determinism, replay, and failure recovery are explicit.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/build_hazard_layers.py`
- `docs/tschamut_public_scalable_conditional_execution.md`
- `tests/test_pilot_command_plan.py`

Deliverables:

- Define the distributed execution manifest shape for split tasks, chunk keys, reducer inputs, merge order, retry semantics, and output provenance.
- Add fixture-backed command-plan tests proving deterministic split/merge ordering and restartable chunk identity.
- Identify the smallest future distributed dry-run implementation task.

Definition of done:

- Focused command-plan tests pass and the contract can be validated locally without launching distributed jobs.


### TB-595: Prototype Local Distributed-Orchestration Semantics

Goal: Exercise the distributed execution contract locally with deterministic fixture chunks and reducer replay.

Capability gap reduced: Provides a low-risk proof of orchestration semantics before any cluster distributed phase change.

Why this outranks alternatives: Local replay can catch split/merge/retry bugs before consuming scarce cluster resources.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/build_hazard_layers.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Add a local fixture-backed distributed dry run that simulates multiple chunks, one retry, deterministic merge, and preservation of replay-critical outputs.
- Compare the merged output against the equivalent single-process fixture output.
- Record limitations that still block real distributed execution.

Definition of done:

- Focused local orchestration tests pass and the output names the remaining cluster-side blockers.


### TB-596: Quantify Swiss-Wide Data And Execution Inputs Needed For A Phase Change

Goal: Replace the Swiss-wide target with a quantified input, compute, storage, validation, and review readiness matrix.

Capability gap reduced: Makes Swiss-wide feasibility depend on explicit measured requirements rather than a broad “out of reach” label.

Why this outranks alternatives: Swiss-wide work requires both scale evidence and national data readiness; this task defines the actual gap.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_large_scale_execution_probe.py`

Deliverables:

- Extend the feasibility projection with national DEM/context data volume, tiling, chunk count, output footprint, validation evidence, and review checks.
- Distinguish compute-feasible, data-ready, validation-ready, and operational-ready classes.
- Add tests proving Swiss-wide remains currently deferred unless all classes are satisfied.

Definition of done:

- Focused projection tests pass and the Swiss-wide blocker is decomposed into measurable next steps.


### TB-597: Create A Readiness Roadmap And Decision Check

Goal: Combine operational, physical-probability, Swiss-wide, non-postproc, and distributed readiness into one phase-change decision check.

Capability gap reduced: Replaces scattered prose with one ranked roadmap for future evidence work.

Why this outranks alternatives: After individual readiness checks exist, the project needs one decision surface that says which evidence gap is most useful to close next.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/decision_log.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Add a phase-change decision report that evaluates each readiness class independently.
- Produce a ranked next-action list for the first scientifically useful evidence upgrade.
- Link the decision surface from the maturity snapshot without changing current output labels.

Definition of done:

- Focused decision/gap tests pass and each readiness class has a concrete next task or an explicit deferral reason.


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
  mainly a report, check, validator, checklist, or package, state the exact run,
  recovery, acquisition, reproducibility, or consolidation action it enables.

Definition of done:

- Focused checks pass, the result is explicit, and the task actually moved
  execution, measurement, acquisition, or simplification forward.

Scope: Keep work focused. If a task changes physics defaults, execution
architecture, partition choice, or public output semantics, record that choice
plainly in the work log.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read the selected task and its `Inspect first` files first. Pull broader
context only when it is needed.

Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.

Keep worker prompts compact. Redirect large JSON, diffs, and logs to `/tmp` and
summarize the important result; finish with the compact structured report schema:
`TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
`PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.

Before commit, run the focused checks, `git diff --check`, and the pre-commit
hook. Add broader consistency checks when the change touches shared contracts or
public docs.

Do not keep completed tasks here. Append completed TB work to the bottom of `docs/agent_work_log.md`
and use `decision_log.md` for durable decisions.
