# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

## Active Tasks

### TB-183: Multi-Release-Zone Balfrin Dry-Run Demonstration

Goal: Build a bounded multi-release-zone Balfrin demonstration package from
automatic release candidates, deterministic scenarios, reduced-output settings,
and uncertainty-aware post-processing commands.

Capability gap reduced: The architecture is only measured for single-release-
zone Balfrin execution; multi-zone orchestration, output pressure, reducer
pressure, and restartability remain untested.

Why this outranks alternatives: This is the highest-leverage next
demonstration milestone because it tests whether the current workflow shape can
survive beyond the single-zone comfort zone.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/generate_balfrin_target_area_demo_handoff.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/orchestration_strategy.md`

Deliverables:

- A multi-zone command-plan and SBATCH handoff package in an ignored/scratch
  root.
- Estimated runtime, output pressure, reducer/chunk pressure, and restartability
  checkpoints for the package.
- A blocked-or-ready submission classification that explicitly states whether
  live execution requires new human authorization.
- A follow-up recommendation for the smallest measured multi-zone Balfrin run.

Definition of done:

- The dry-run package is reproducible and reviewable, package generation is
  covered by focused tests, and no live Balfrin submission occurs unless the
  task is explicitly re-authorized in the conversation before execution.

Boundaries: Dry-run/package by default; no live Balfrin job, no scale-up
authorization, no distributed execution, no operational claim, and no generated
artifacts committed.

### TB-184: AOI-To-Prepared-Pilot End-To-End Automation

Goal: Given AOI extents or a bounding polygon, automatically derive the
prepared-pilot scaffolding: tile manifests, terrain/context manifests, release
candidates, scenario tables, command plans, and ignored-root layouts.

Capability gap reduced: Missing "AOI to workflow compiler" path for future
Swiss-wide reproducibility.

Why this outranks alternatives: It collapses several existing dry-run helpers
into one deterministic operator-facing preparation path without requiring a
simulation run.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- One AOI preparation helper or orchestration mode that composes existing
  product discovery, cache verification, terrain preprocessing, release
  candidate generation, scenario generation, and command-plan output.
- Deterministic manifests and ignored-root layout records.
- Blocked-missing-input output that names the exact products or metadata
  missing for clean checkouts.

Definition of done:

- The helper produces a deterministic prepared-pilot report for a fixture AOI,
  reports blocked states cleanly when staged products are absent, and focused
  tests cover both paths.

Boundaries: No public-data download, no simulation, no second-site ensemble,
no operational claim, and no synthetic fixture represented as public evidence.

### TB-185: Switzerland-Scale Runtime And Storage Projection

Goal: Project runtime, output pressure, storage growth, reducer scaling, and
rebuildability cost for 10 release zones, 100 release zones, regional workflows,
and a Switzerland-scale planning envelope.

Capability gap reduced: National feasibility is currently extrapolated from
single-zone and target-area evidence without a multi-zone planning model.

Why this outranks alternatives: It turns measured Balfrin output pressure and
candidate/scenario cardinality into explicit no-go/defer/next-probe planning
labels before larger runs are attempted.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Runtime/storage/file-count/rebuildability projections for 10-zone, 100-zone,
  regional, and Swiss-wide planning cases.
- Sensitivity bands using measured single-zone, target-area, and generated
  scenario-table evidence where available.
- Explicit bottleneck labels for validation output, hazard output, reducer
  merge, manifest count, memory, and scheduler practicality.

Definition of done:

- The projection helper/report is deterministic, fails closed when measured
  inputs are absent, and states which scale levels are no-go, deferred, or
  eligible only for an explicitly authorized next probe.

Boundaries: Projection only; no scale-up authorization, no distributed
execution, no Swiss-wide run, and no annual-frequency or operational claim.

### TB-186: Large-AOI GIS Packaging Stress Test

Goal: Stress-test GIS package generation, manifest generation, COG conversion,
and raster packaging for a realistically large AOI or synthetic large-AOI
fixture derived from current target-area outputs.

Capability gap reduced: Unknown GIS/COG packaging pressure for larger AOIs and
multi-zone products.

Why this outranks alternatives: GIS product usability is secondary to
scientific evidence, but large-AOI packaging can become the first practical
demonstration bottleneck once multi-zone outputs exist.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/summarize_balfrin_target_area_gis_cog_scope.py`
- `docs/pilot_gis_package.md`

Deliverables:

- A bounded GIS/COG stress-test helper or mode using scratch/ignored outputs.
- Package runtime, COG conversion timing, raster count, manifest size, layer
  parity, and missing-layer summaries.
- A report that distinguishes standard-root COG-blocked status from converted
  scratch package readiness.

Definition of done:

- Focused tests cover the stress-test summary and blocked-missing-input path,
  and the report identifies the first GIS packaging bottleneck without
  committing generated rasters.

Boundaries: No operational GIS product claim, no manual QGIS acceptance claim,
no generated raster commit, and no claim that scratch COG readiness upgrades
standard roots.

### TB-187: Multi-Zone Reducer And Merge Scaling Probe

Goal: Measure reducer pressure, chunk scaling, deterministic merge ordering,
manifest scaling, and output pressure for many simultaneous release zones using
fixture-backed or scratch multi-zone inputs.

Capability gap reduced: Reducer/runtime evidence remains mostly single-zone
and may not represent aggregation costs for multi-zone workflows.

Why this outranks alternatives: Before live multi-zone Balfrin execution, the
repo needs a local or fixture-backed reducer stress path that exposes manifest
and merge-order bottlenecks.

Inspect first:

- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/build_hazard_layers.py`
- `scripts/summarize_balfrin_output_tier_audit.py`
- `src/validation/runner.rs`
- `docs/tschamut_public_bounded_validation_output_profile.md`

Deliverables:

- Deterministic multi-zone reducer stress fixture or scratch input generator.
- Measurements for chunk count, merge order, reducer wall time, manifest size,
  file count, and bytes by output family.
- A scaling report with bottleneck labels and recommended reducer constraints
  for TB-183.

Definition of done:

- The probe is reproducible without relying on ignored live artifacts, focused
  tests cover deterministic merge ordering and summary fields, and the report
  states whether reducer pressure blocks a multi-zone Balfrin dry run.

Boundaries: No distributed reducer, no MPI/GPU, no live Balfrin job, no physics
change, and no generated heavy outputs committed.

### TB-188: Real Chant Sura Workflow Dry Run

Goal: Run a non-Tschamut workflow dry run for Chant Sura / Flüelapass covering
AOI preparation, terrain staging checks, release-candidate generation,
scenario generation, command planning, and an optional tiny bounded ensemble
only if all real-context gates are satisfied and explicitly permitted.

Capability gap reduced: Portability remains mostly metadata-level and
fixture-backed; the repo needs a real second-site workflow reality check.

Why this outranks alternatives: A non-Tschamut dry run is the fastest way to
separate reusable workflow assumptions from Tschamut-specific heuristics.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`

Deliverables:

- A Chant Sura dry-run report that composes public-context readiness, AOI
  preparation, release-candidate generation, scenario generation, and command
  planning.
- Exact blocked-missing-input or ready-for-next-step classification.
- Optional tiny ensemble handoff only if real staged inputs exist and the task
  records explicit permission; otherwise report the blocked state.

Definition of done:

- The dry run is deterministic, distinguishes real public context from
  synthetic fixtures, and focused tests cover ready and blocked fixture paths.

Boundaries: No downloads, no second-site ensemble by default, no synthetic
public-context evidence, no operational claim, and no physical validation
claim.

### TB-189: Release-Zone Candidate Stability And Sensitivity

Goal: Measure how stable automatically generated release-zone candidates are
under slope thresholds, terrain resolution, smoothing, and AOI boundary
changes.

Capability gap reduced: Unknown reproducibility and uncertainty of automated
release-zone generation.

Why this outranks alternatives: Candidate generation is only useful for
Swiss-wide workflows if the sensitivity of the heuristic is measured and
reported instead of hidden.

Inspect first:

- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `docs/swisstopo_data_strategy.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A sensitivity matrix across slope threshold, smoothing, terrain resolution,
  and AOI boundary perturbations.
- Stable, unstable, and heuristic-sensitive candidate-region classifications.
- Candidate persistence metrics and GIS-readable scratch outputs where
  supported.

Definition of done:

- The stability report is deterministic, includes measurable sensitivity
  metrics, and focused tests cover perturbation summaries and fail-closed
  missing-input behavior.

Boundaries: No release-zone validation, no threshold tuning for acceptance, no
operational source-zone claim, and no generated GIS outputs committed.

### TB-190: Full Balfrin Demonstration Evidence Package

Goal: Produce one coherent technical evidence package for the full
demonstration workflow, including runtime, uncertainty, GIS/COG, restartability,
scaling, AOI automation, release/scenario automation, and claim boundaries.

Capability gap reduced: Demonstration evidence is spread across many helpers
and reports, making it harder to answer whether the workflow plausibly scales
toward Swiss-wide automation.

Why this outranks alternatives: After the automation and stress-test tasks, a
single package is needed to show what is measured, what is fixture-backed, what
is blocked, and what remains scientifically unresolved.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_target_area_evidence_bundle.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/target_area_physical_evidence_acquisition_pack.md`

Deliverables:

- Canonical JSON/text package summarizing the current full demonstration
  workflow and evidence provenance.
- Section-level provenance for measured, fixture-backed, blocked, and
  unavailable evidence.
- Explicit management-facing answer to whether the current architecture is
  plausibly extensible toward Swiss-wide workflows, with blockers named.

Definition of done:

- The package can be regenerated deterministically, focused tests cover its
  required sections and claim boundaries, and the report does not collapse
  blocked or fixture-backed evidence into measured completion.

Boundaries: No marketing overclaim, no operational acceptance, no physical
credibility upgrade, no scale-up authorization, no annual-frequency semantics,
and no generated heavy artifacts committed.

### TB-191: Balfrin Metrics And Run-Root Preservation Gate

Goal: Define and test the metrics/run-root preservation gate that must pass
before any future authorized live Balfrin multi-zone or metrics-completion run
is treated as demonstration evidence.

Capability gap reduced: Previous measured Balfrin probes left peak-memory,
split validation/hazard output, and mounted-run-root availability incomplete or
fragile.

Why this outranks alternatives: A future multi-zone run will be expensive and
hard to repeat; it should not reproduce the same evidence gaps already exposed
by the target-area probe.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/submit_balfrin_probe.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/balfrin_target_area_spatial_uncertainty_stability_report.md`

Deliverables:

- A deterministic preflight or report that lists required metrics, preserved
  run-root files, SLURM accounting fields, output-family summaries, and
  spatial/GIS artifact paths for the next authorized live run.
- A fail-closed classification for missing peak memory, split validation/hazard
  output bytes/counts, conditional-curve rows, reducer state, COG/GIS scope
  paths, or unavailable mounted run roots.
- Updated operator guidance for what must be collected before a live run is
  considered evidence rather than only an execution attempt.

Definition of done:

- Focused tests cover complete, partial, and missing-run-root cases; the gate
  can be run without submitting a job; and the report clearly states whether a
  future live run would satisfy the evidence-preservation contract.

Boundaries: No live Balfrin submission, no scale-up authorization, no
distributed execution, no operational claim, and no fabricated metrics.

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
leverage now.

Inspect first:

- `path/or/script.py`

Deliverables:

- Concrete executable, analysis, test, or measured output.

Definition of done:

- Focused checks pass, the capability outcome is explicit, and the task is
  removed from this backlog only when the definition of done is genuinely met.

Boundaries: No tuning, operational claims, scale-up authorization, or other
phase changes unless the task explicitly allows them.
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
