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

### TB-666: Integrate The Larger Diagnostic Into Scale Surfaces

Goal: Thread the latest Balfrin diagnostic result into the scale readiness matrix, Swiss-wide envelope, and management package.

Capability gap reduced: Current measured evidence for Swiss-scale feasibility planning.

Why this outranks alternatives: Measured runs only help decisions if the planning surfaces use them instead of stale anchors.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_swiss_wide_execution_envelope.py`

Deliverables:

- Updated summaries/tests that surface the new diagnostic run, preserve its diagnostic-only boundary, and revise the next recommended scale step.

Definition of done:

- Focused tests pass and the latest run changes at least one measured metric, ranked next action, or Swiss-scale projection input.

Scope: Do not promote diagnostic reducer-pressure evidence into hazard-throughput, physical-probability, operational, distributed, or non-`postproc` claims.

### TB-667: Build A Real Greater-Than-Four-Zone Hazard-Throughput Profile

Goal: Add an executable hazard-throughput profile that targets more than four release zones rather than rerunning the old four-zone package shape.

Capability gap reduced: Larger measured hazard-throughput capability on Balfrin.

Why this outranks alternatives: TB-642 identified the lack of a true >4-zone hazard-throughput package as the blocker to stronger feasibility evidence.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `docs/balfrin_hazard_throughput_probe_tb642.md`
- `tests/test_multi_zone_hazard_throughput_profile.py`

Deliverables:

- A generated >4-zone hazard-throughput package or profile whose command plan actually targets the larger release-zone count and whose reduced-output profile stays within an explicit replayable budget.

Definition of done:

- The package/profile is executable in dry-run or pre-submit mode, focused tests pass, and the result is not just a resized contract around a four-zone command.

Scope: Prefer reducing duplicated package machinery or reusing the simplified runner where possible.

### TB-668: Prove The Larger Hazard Package Locally Before Submission

Goal: Exercise the >4-zone hazard-throughput package locally enough to catch output-budget, manifest, and replayability failures before Balfrin submission.

Capability gap reduced: Pre-submit confidence for the next real hazard-throughput run.

Why this outranks alternatives: The previous larger hazard-throughput attempt failed before submission on package/output-profile mismatch.

Inspect first:

- `scripts/check_hazard_output_profile.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `tests/test_hazard_output_profile.py`

Deliverables:

- A local smoke or dry-run result for the larger hazard-throughput package, including file-family counts, manifest size, replay-critical output coverage, and the exact first blocker if it is not submit-ready.

Definition of done:

- The result is either `ready_for_submit` with measured local output pressure or a concrete blocker that can be fixed without guessing.

Scope: Do not submit to Balfrin in this task.

### TB-669: Run The First Greater-Than-Four-Zone Hazard-Throughput Probe On Balfrin

Goal: Execute the first true >4-zone hazard-throughput probe on Balfrin `postproc` once the package is locally submit-ready.

Capability gap reduced: Measured hazard-throughput evidence beyond the four-zone TB-619 anchor.

Why this outranks alternatives: Swiss-scale feasibility currently leans too heavily on diagnostic reducer-pressure runs; a larger hazard-throughput support point is the more relevant performance evidence.

Inspect first:

- `scripts/run_balfrin_diagnostic.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `docs/balfrin_hazard_throughput_package_tb618.md`

Deliverables:

- One completed or clearly failed >4-zone Balfrin hazard-throughput probe under `$SCRATCH`, with scheduler state, elapsed time, peak RSS, output footprint, and replay-critical families collected.

Definition of done:

- The run reaches a terminal state and the metrics distinguish hazard-throughput evidence from diagnostic reducer-pressure evidence.

Scope: Keep the run bounded to `postproc`; if the run shape would occupy the partition for more than 6 hours, stop and resize before submission.

### TB-670: Promote The Larger Hazard-Throughput Metrics Into Swiss-Scale Planning

Goal: Replace stale hazard-throughput anchors with the latest measured >4-zone result in the Swiss-scale feasibility projection.

Capability gap reduced: Feasibility estimates based on directly relevant hazard execution evidence.

Why this outranks alternatives: Without updating the envelope, successful Balfrin runs do not move the Swiss-scale decision frontier.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/swiss_scale_feasibility_projection.md`
- `tests/test_swiss_wide_execution_envelope.py`

Deliverables:

- Updated projection inputs and tests showing how the new hazard-throughput result changes runtime, storage, memory, file-count, and next-run recommendations.

Definition of done:

- Focused tests pass and the planning output names the new measured hazard-throughput support point.

Scope: Keep Swiss-wide execution as a projection unless a later task explicitly runs a bounded Swiss-scale sample.

### TB-671: Measure Safe Concurrent Postproc Diagnostics

Goal: Run a small concurrent set of bounded diagnostics on Balfrin to test scheduler behavior and shared `$SCRATCH` output isolation.

Capability gap reduced: Practical scalability evidence for running many independent chunks on an underused `postproc` partition.

Why this outranks alternatives: Swiss-scale feasibility depends on independent chunk throughput, not only a single larger job.

Inspect first:

- `scripts/run_balfrin_diagnostic.py`
- `scripts/summarize_balfrin_restartability_recovery.py`
- `docs/balfrin_tschamut_pilot_runbook.md`
- `docs/balfrin_restartability_recovery_tb606.md`

Deliverables:

- A bounded concurrent run set, with one run root per job under `$SCRATCH`, terminal scheduler states, per-job metrics, and an aggregate contention summary.

Definition of done:

- All submitted jobs are terminal, run roots are isolated, and the aggregate report shows whether concurrent diagnostics scale cleanly or reveal contention.

Scope: Use only as many jobs as current `postproc` capacity makes reasonable and stay below the 6-hour partition-occupation boundary.

### TB-672: Exercise Restartability On A Larger Run Root

Goal: Prove that a larger diagnostic or hazard-throughput run root can be recovered, copied, and summarized without rerunning the simulation.

Capability gap reduced: Restartability and operational feasibility for long Swiss-scale chunk workflows.

Why this outranks alternatives: Swiss-scale work must tolerate partial completion and recovery; output isolation alone is not enough.

Inspect first:

- `scripts/summarize_balfrin_restartability_recovery.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `tests/test_balfrin_restartability_recovery.py`

Deliverables:

- A restartability/recovery measurement for the latest larger run root, including copied-root size, mandatory artifact coverage, and whether metrics can be regenerated from preserved files.

Definition of done:

- The recovery path either reconstructs the measured summary from preserved artifacts or identifies the exact missing artifact family.

Scope: Recovery should use `$SCRATCH` for large copied data and avoid persistent clutter outside the repo clone.

### TB-673: Run A Swiss National Chunk Execution Smoke

Goal: Execute a tiny national-chunk-shaped sample rather than only estimating the national tile/chunk inventory.

Capability gap reduced: First executable bridge from national tiling inventory to chunked processing behavior.

Why this outranks alternatives: TB-661 showed the national inventory shape, but Swiss-scale feasibility needs at least one runnable chunk-shaped sample.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/estimate_large_scale_execution.py`
- `docs/swiss_national_tiling_inventory_tb607.json`
- `docs/swiss_national_tile_chunk_mapping_tb608.json`
- `tests/test_swiss_wide_execution_envelope.py`

Deliverables:

- A local or Balfrin smoke that processes a tiny representative subset of national chunks, records runtime/output footprint, and compares it with the inventory projection.

Definition of done:

- The smoke produces measured chunk-shaped outputs or a concrete missing-data blocker tied to specific inventory products.

Scope: Do not attempt a full Swiss-wide run in this task.

### TB-674: Stage The Minimum Real Public Geodata Cache For A Second Site

Goal: Move the Chant Sura second-site path from missing context inputs toward a runnable real-input prepared pilot.

Capability gap reduced: Scientific validation beyond the Tschamut-only path.

Why this outranks alternatives: Swiss-scale feasibility is weak if the workflow only works for one site with incomplete second-site validation.

Inspect first:

- `scripts/stage_public_geodata_cache.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`
- `docs/chant_sura_public_geodata_cache_tb654.md`

Deliverables:

- A staged or precisely blocked minimum real public-geodata cache for Chant Sura, with required products classified as ready, missing, or intentionally deferred.

Definition of done:

- The second-site preflight moves measurably closer to real-input execution or reports a product-by-product acquisition blocker that can be acted on directly.

Scope: Do not count fixture-backed smoke inputs as real second-site validation.

### TB-675: Run The Second-Site Prepared Pilot When The Cache Is Ready

Goal: Execute the Chant Sura prepared-pilot path with real staged inputs, or fail on the first still-missing real product.

Capability gap reduced: Cross-site scientific portability evidence.

Why this outranks alternatives: The fastest way to improve scientific credibility is to run the existing second-site front door once real inputs are staged.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `docs/chant_sura_prepared_pilot_path_tb655.md`

Deliverables:

- A second-site prepared-pilot result with real input readiness, generated scenario/source artifacts, local run status, and output footprint, or a single first blocker.

Definition of done:

- The task either produces a real-input second-site smoke result or narrows the second-site blocker below the broad public-context category.

Scope: Keep the result as validation/portability evidence, not an operational or physical-probability claim.

### TB-676: Close The Calibration Acceptance Criterion Gap

Goal: Turn the current calibration blocker into an executable acceptance criterion or a measured rejection.

Capability gap reduced: Scientific credibility for physical-probability and validation claims.

Why this outranks alternatives: The physical credibility summary already reports calibration evidence as the first remaining blocker.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/check_calibration_separation_preflight.py`
- `scripts/run_tschamut_calibration.py`
- `docs/calibration_holdout_evidence_tb658.md`
- `tests/test_validation_calibration_evidence_gaps.py`

Deliverables:

- A calibrated residual-quality threshold or review decision encoded in the existing evidence path, with focused tests and an updated physical-credibility summary.

Definition of done:

- Calibration evidence becomes accepted, explicitly rejected, or narrowed to one measured residual-quality failure.

Scope: Do not tune model parameters to pass the criterion unless the task records the before/after residuals and preserves holdout separation.

### TB-677: Run A Conditional Physical-Probability Prototype For One AOI

Goal: Produce a bounded physical-probability prototype for one AOI using accepted source-frequency, release-probability, block-population, and calibration evidence.

Capability gap reduced: Transition from conditional hazard layers toward scientifically interpretable physical probabilities.

Why this outranks alternatives: Swiss-scale feasibility needs a scientifically credible per-AOI probability path before multiplying the workflow across Switzerland.

Inspect first:

- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/validate_physical_frequency_reducer_preconditions.py`
- `scripts/validate_annual_physical_prototype_preflight.py`
- `docs/physical_frequency_reducer_preconditions.md`
- `tests/test_physical_frequency_reducer_preconditions.py`

Deliverables:

- A bounded one-AOI physical-probability prototype or fail-closed preflight, with all required evidence inputs named and the generated probability semantics separated from operational return-period claims.

Definition of done:

- The prototype either runs and produces a reviewable probability output or reports the exact missing evidence item preventing the run.

Scope: Keep operational, return-period, risk, exposure, vulnerability, and Swiss-wide claims out of scope.

### TB-678: Build A Swiss-Scale Demonstration Readiness Package From Measured Runs

Goal: Combine the latest Balfrin diagnostic, hazard-throughput, concurrency, restartability, chunk-smoke, and scientific-readiness results into one demonstration decision surface.

Capability gap reduced: Clear go/no-go basis for a Swiss-scale feasibility demonstration on Balfrin.

Why this outranks alternatives: After the measured pushes, the repo needs one concise surface that says what can be demonstrated now and what remains projection-only.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A refreshed demonstration readiness package that names measured support points, projected Swiss-scale envelope, first missing input for a full Swiss-scale run, and the recommended next Balfrin demonstration command.

Definition of done:

- The package is generated from current measured outputs, focused tests pass, and the recommendation is concrete enough to execute or reject without adding more process artifacts.

Scope: Favor one concise generated/readable surface over new scattered documentation.

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
