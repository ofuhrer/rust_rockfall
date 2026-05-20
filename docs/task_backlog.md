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

### TB-374: Validate Management AOI Cache Integrity

Goal: Verify acquired/staged AOI public-geodata products for checksum stability, required metadata, CRS/datum consistency, tile coverage, and missing-product classification.

Capability gap reduced: Prevents downstream preprocessing from silently accepting partial or mismatched real public inputs.

Why this outranks alternatives: Cache integrity must be trusted before terrain preprocessing or release-zone generation can be interpreted.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/bootstrap_aoi_manifest.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Deterministic cache-integrity report for the management AOI.
- Focused tests for missing, partial, metadata-mismatched, and ready cache states.

Definition of done:

- The AOI cache reports either ready real products or exact product-level blockers without relying on fixture-backed evidence.

Boundaries: No raw data commits; no terrain mutation beyond read-only inspection; no hazard claim.

### TB-375: Run Real-AOI Terrain Preprocessing Pipeline

Goal: Convert the management AOI terrain products into deterministic prepared terrain artifacts with provenance, extent, resolution, CRS, and vertical-datum metadata.

Capability gap reduced: The terrain preprocessing path needs real-AOI evidence beyond fixture-backed dry runs.

Why this outranks alternatives: Release-zone candidate generation and scenario scaling require a prepared real terrain surface.

Inspect first:

- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/run_aoi_hazard_workflow.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Ignored prepared terrain root for the management AOI, or a blocked report naming the exact terrain-preprocessing failure.
- Runtime/output measurements and provenance manifest.

Definition of done:

- The terrain-preprocessing status advances to ready for release-zone candidate generation or records a precise real-input blocker.

Boundaries: No raw data commits; no hazard execution; no terrain smoothing/tuning beyond existing documented preprocessing policy.

### TB-376: Generate Real-AOI Release-Zone Candidate Sweep

Goal: Run deterministic release-zone candidate generation on the prepared management AOI terrain and produce candidate masks, polygons, statistics, and GIS-ready review outputs.

Capability gap reduced: Release zones remain the largest Swiss-wide manual automation gap.

Why this outranks alternatives: The project cannot scale nationally while release zones are curated manually.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Deterministic candidate-zone outputs for the management AOI in ignored roots.
- Candidate counts, area statistics, heuristic parameters, runtime/output measurements, and review-map pointers.

Definition of done:

- The candidate sweep is reproducible and reviewable, or a concrete terrain/input blocker is recorded.

Boundaries: No operational release-zone claim, no parameter tuning to match desired zones, no hazard execution.

### TB-377: Measure Real-AOI Release-Zone Stability

Goal: Quantify candidate-zone sensitivity for the management AOI under bounded slope, resolution, smoothing, and AOI-boundary perturbations.

Capability gap reduced: Defensibility of terrain-driven release-zone generation on real terrain.

Why this outranks alternatives: Candidate zones must be stable enough to support scenario generation before larger Balfrin runs are meaningful.

Inspect first:

- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `docs/current_maturity_snapshot.md`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Stability classes, persistent/unstable candidate masks, and sensitivity summary for the management AOI.
- Recommendation on whether candidates are ready for scenario generation, need review, or are unstable.

Definition of done:

- Candidate-zone stability is measured and classified without changing physics or tuning thresholds to force acceptance.

Boundaries: No operational release-zone claim, no calibration, no hazard execution.

### TB-378: Generate Large Real-AOI Scenario Table From Candidates

Goal: Generate deterministic block/scenario tables from the real-AOI candidate zones and measure scenario cardinality, manifest pressure, and family composition.

Capability gap reduced: Scenario generation is still a major manual and scaling uncertainty.

Why this outranks alternatives: Multi-zone execution pressure is driven by candidate and scenario cardinality; it must be measured before submitting larger jobs.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/generate_tschamut_block_scenario_tables.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`

Deliverables:

- Deterministic real-AOI scenario table or blocked report.
- Scenario counts by candidate family, output bytes, manifest pressure, and command-plan implications.

Definition of done:

- Scenario-generation pressure is quantified for the management AOI and ready for prepared-pilot compilation or explicit deferral.

Boundaries: No source-frequency semantics, no annual probability, no physics tuning, no hazard execution.

### TB-379: Compile Management AOI Prepared Pilot

Goal: Compile the management AOI terrain, context, candidate zones, and scenario tables into a prepared-pilot command package without running ensembles.

Capability gap reduced: The AOI-to-workflow compiler must operate on real candidate/scenario inputs, not only fixtures.

Why this outranks alternatives: A prepared pilot is the handoff between automation and Balfrin execution.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Deterministic prepared-pilot manifest, command plan, ignored-root layout, expected outputs, and first-blocker/next-command report.
- Tests or fixture updates covering real-input-ready and blocked states.

Definition of done:

- The management AOI can be prepared up to the no-simulation command-plan boundary with real inputs or precise blockers.

Boundaries: No ensemble execution; no operational claim; no raw data commits.

### TB-380: Build Management AOI Multi-Zone Balfrin Handoff

Goal: Convert the prepared management AOI pilot into a bounded Balfrin multi-zone handoff package with reduced-output mode, output budgets, authorization records, and preservation plan.

Capability gap reduced: Real-AOI prepared pilots need an HPC handoff path before execution feasibility can be tested.

Why this outranks alternatives: This is the bridge from local AOI automation to measured Balfrin scale evidence.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Bounded handoff package for the management AOI with exact run root, command list, budget checks, and authorization audit.
- Classification as ready, blocked by budget, blocked by authorization, or blocked by missing prepared-pilot inputs.

Definition of done:

- A GPT-5.5 worker has enough package evidence to decide whether a live management-AOI postproc run can be attempted.

Boundaries: No live submission in this task; `postproc` only for future live work; no distributed execution or scale-up claim.

### TB-381: Execute Bounded Management AOI Multi-Zone Balfrin Run

Goal: Submit and monitor a bounded management-AOI multi-zone hazard run on Balfrin `postproc` if TB-380 reports ready.

Capability gap reduced: Missing measured real-AOI multi-zone Balfrin hazard execution.

Why this outranks alternatives: This is the closest direct evidence for whether a full-scale Balfrin demonstration is feasible or out of reach.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Live management-AOI job id, run root, runtime, memory, validation/hazard output pressure, reducer pressure, and preservation evidence.
- Fail-closed report if readiness or scheduler gates block submission.

Definition of done:

- The management-AOI multi-zone branch is measured or explicitly failed closed with the first persistent blocker named.

Boundaries: GPT-5.5 worker only; `postproc` only; respect the 6-hour full-partition rediscussion rule; no scale-up or operational claim.

### TB-382: Stress Large-AOI GIS And COG Packaging From Real Outputs

Goal: Stress-test GIS package manifest generation, raster package completeness, and COG conversion/scope classification against the largest available real-AOI or measured multi-zone outputs.

Capability gap reduced: Management-facing feasibility needs to know whether GIS packaging breaks before compute does.

Why this outranks alternatives: GIS/COG remains a lower-priority blocker, but it becomes material once real-AOI/multi-zone outputs exist.

Inspect first:

- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Package runtime, file count, raster count, manifest pressure, COG readiness, and scope-delta classification.
- Explicit first GIS/COG blocker and whether it affects demonstration readability or only production packaging.

Definition of done:

- GIS/COG feasibility for the largest current real output is classified without overstating operational readiness.

Boundaries: No generated raster commits; no operational GIS claim; no new hazard run.

### TB-383: Refresh Management Swiss-Scale Feasibility Decision

Goal: Update the Swiss-scale feasibility projection and management package after the two-zone/four-zone/management-AOI evidence sequence completes.

Capability gap reduced: Management needs a current answer on whether Swiss-scale is feasible, conditional, or out of reach based on measured evidence.

Why this outranks alternatives: This synthesis is only useful after the execution and automation evidence above has landed.

Inspect first:

- `docs/swiss_scale_feasibility_projection.md`
- `docs/balfrin_scale_demonstration_management_package.md`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Updated projection table separating measured evidence, extrapolated assumptions, failed-closed branches, no-go thresholds, and unknowns.
- Recommendation for 10-zone, 100-zone, regional, and Swiss-wide classes.

Definition of done:

- Management can read one current feasibility package that reflects the latest measured Balfrin and real-AOI automation evidence.

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
