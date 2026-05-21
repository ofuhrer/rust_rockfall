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

### TB-431: Compact Regional Split Submission Package

Goal: Reduce the regional split Balfrin submission package below the reviewed manifest-size budget so the next live probe can pass pre-submit gates.

Capability gap reduced: Regional multi-zone Balfrin execution blocked by package/manifest pressure.

Why this outranks alternatives: TB-428 identified an exact blocker (`14550` bytes versus `14000` allowed), so a small compaction task directly unblocks the next measured run.

Inspect first:

- `docs/balfrin_regional_split_probe_gate_tb428.md`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_balfrin_regional_split_submission_package.py`

Deliverables:

- A compacted package/manifest representation or redundant-field removal that preserves all required submission, preservation, and split/merge evidence.
- Focused regression coverage proving the package remains readable and falls within the reviewed `next_larger_four_zone_review_only_probe` manifest-size budget.
- A regenerated no-submit package smoke result under `/tmp` showing `ready_for_bounded_postproc_submission=true` or the next exact blocker.

Definition of done:

- The regional split submission package no longer fails on the TB-428 manifest-size budget, or the task records the smallest remaining package-size blocker with a concrete next-byte target.

Boundaries: No Balfrin submission, no loss of required provenance, no scale-up or operational claim, and no budget loosening without measured justification.

### TB-432: Execute Regional Split Balfrin Probe After Package Compaction

Goal: Submit and actively monitor one bounded regional split `postproc` probe after TB-431 makes the reviewed package pass all gates.

Capability gap reduced: Lack of measured regional split execution evidence.

Why this outranks alternatives: Management needs measured evidence beyond the smallest multi-zone branch; this is the next live step once the exact TB-428 package blocker is removed.

Inspect first:

- `docs/orchestration_strategy.md`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/collect_balfrin_probe_metrics.py`

Deliverables:

- One measured Balfrin `postproc` run, or a failed-closed pre-submit/submit record with the exact first blocker.
- Runtime, memory when available, validation/hazard file counts and bytes, reducer metrics, preservation gate status, and run-root pointers.
- Updated evidence surface only where needed to separate measured regional split execution from failed-closed or fixture-backed evidence.

Definition of done:

- The regional split branch either has measured run-root evidence or a durable failed-closed record with no ambiguous half-state.

Boundaries: GPT-5.5 worker required, one bounded `postproc` probe only, no non-postproc partition, no distributed execution, no scale-up, operational, annual-frequency, physical-probability, risk, exposure, or vulnerability claim.

### TB-433: Integrate Regional Split Run Outcome Into Scale Dashboard

Goal: Thread the TB-432 measured or failed-closed outcome into the scale readiness dashboard and Swiss-scale feasibility surfaces.

Capability gap reduced: Stale scale interpretation after the regional split probe branch changes state.

Why this outranks alternatives: Scale decisions should be based on the latest measured or failed-closed regional evidence, not the older TB-407/TB-428 state.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_regional_split_probe_gate_tb428.md`

Deliverables:

- Updated scale dashboard classification for the regional split branch.
- Updated concise documentation stating whether the next blocker is execution, output pressure, reducer pressure, or evidence collection.
- Regression coverage for the new classification path.

Definition of done:

- The scale dashboard and maturity snapshot agree on the current regional split status and next executable action.

Boundaries: Evidence integration only; do not promote failed-closed, fixture-backed, or projection-only evidence into measured scale capability.

### TB-434: Build Real-AOI Public-Geodata Acquisition Command Set

Goal: Turn the current AOI acquisition planning surfaces into concrete copy/paste commands for acquiring and staging the required public geodata products for one arbitrary AOI.

Capability gap reduced: Manual public-geodata acquisition remains the largest user workflow gap.

Why this outranks alternatives: Swiss-wide workflow automation cannot progress while AOI input acquisition is mostly planning and local-state dependent.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/stage_public_geodata_cache.py`

Deliverables:

- Deterministic dry-run command output listing product IDs, expected local roots, cache verification commands, and staging commands for a supplied AOI.
- A fixture-backed test proving the commands remain stable and do not perform downloads unless explicitly requested.
- Documentation update pointing users to the acquisition command path from the AOI manual.

Definition of done:

- A user can go from AOI bounds to a concrete public-geodata acquisition/staging command sequence without reading multiple planning reports.

Boundaries: No automatic network download by default, no generated artifact commits, no second-site ensemble, no operational claim.

### TB-435: Rehearse Real-AOI Cache Verification With Missing And Partial Inputs

Goal: Make public-geodata cache verification produce actionable missing/partial/input-mismatch reports for arbitrary AOI staging roots.

Capability gap reduced: Hidden local-state coupling in real-AOI preprocessing.

Why this outranks alternatives: Robust failure messages for missing or partial public inputs are required before broad AOI automation or Balfrin execution can be trusted.

Inspect first:

- `scripts/verify_public_geodata_cache.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `tests/test_second_site_public_geodata_preflight.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Fixture-backed cache-verification cases for missing, partial, metadata-mismatched, and ready public inputs.
- Machine-readable next-command or next-file hints for each blocked state.
- Updated AOI manual or geodata prep doc with the concise recovery path.

Definition of done:

- Cache verification distinguishes ready, partial, missing, and metadata-mismatched inputs with actionable recovery hints and focused tests.

Boundaries: No downloads, no fabricated real geodata, no physical-evidence claim.

### TB-436: Exercise AOI Terrain Preprocessing On A Real Staged Crop

Goal: Run the terrain preprocessing path against a real staged AOI crop when available, otherwise fail closed with the exact missing input and command needed.

Capability gap reduced: Terrain preprocessing is still too fixture-dependent for arbitrary AOIs.

Why this outranks alternatives: Release-zone generation and scenario automation depend on trustworthy terrain crops and metadata.

Inspect first:

- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/stage_management_aoi_restaged_terrain.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- One real-staged or failed-closed terrain preprocessing report with terrain bounds, resolution, nodata, slope-domain, and provenance summaries.
- Focused test coverage for the report schema and blocked-state messaging.
- No generated terrain committed.

Definition of done:

- The AOI terrain preprocessing path either produces a measured real-crop QA report or a precise missing-input blocker that can be acted on.

Boundaries: No synthetic evidence promotion, no simulation, no source-zone acceptance claim.

### TB-437: Make Release-Zone Candidate Heuristic Explainable Per Candidate

Goal: Add per-candidate feature summaries explaining why each release-zone candidate was selected or rejected.

Capability gap reduced: Release-zone automation remains difficult to review scientifically and visually.

Why this outranks alternatives: The next Balfrin demonstration needs defensible automated candidates, not opaque slope masks or hand-picked polygons.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `docs/aoi_user_manual.md`
- `qgis/styles/aoi_qgis_style_bundle.json`
- `tests/test_plan_terrain_release_zone_candidates.py`

Deliverables:

- Candidate-level summaries for slope band, local relief/roughness when available, size, separation, context exclusions, and review status.
- GeoJSON properties suitable for QGIS inspection.
- Focused tests using fixture terrain/candidate data.

Definition of done:

- Candidate overlays carry enough deterministic feature evidence for a reviewer to understand why the heuristic selected or rejected each zone.

Boundaries: No tuning to match a desired result, no operational source-zone claim, no physical release probability semantics.

### TB-438: Add Release-Zone Candidate Search-Area Expansion Modes

Goal: Make source-zone candidate generation support explicit local, expanded, and full-AOI search domains with stable metadata.

Capability gap reduced: Candidate generation can miss plausible terrain when search extent is too narrow.

Why this outranks alternatives: Recent review showed the search domain itself can dominate candidate discovery, so the domain choice must be explicit and reproducible.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/aoi_user_manual.md`
- `tests/test_plan_terrain_release_zone_candidates.py`

Deliverables:

- Search-domain modes with deterministic bounds metadata, candidate counts, and output paths.
- GPX or GeoJSON extent output suitable for map review.
- Tests proving each mode is stable and reported in the candidate manifest.

Definition of done:

- A candidate sweep records exactly which search area was used and can widen beyond the original local footprint without ad hoc edits.

Boundaries: No candidate acceptance claim, no operational hazard semantics, no unbounded national sweep.

### TB-439: Stress Scenario Generation From Expanded Candidate Sets

Goal: Measure scenario-table cardinality, file size, and family distribution from expanded release-zone candidate sets.

Capability gap reduced: Scenario cardinality and storage pressure remain uncertain when candidate counts grow.

Why this outranks alternatives: Larger Balfrin probes will fail on scenario/output pressure if expanded candidate sets explode before execution.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Fixture-backed or current-AOI scenario stress output for at least two candidate-count levels.
- Scenario family counts, bytes, row counts, and expected output-tier pressure estimates.
- Recommended cap or batching criterion for the next Balfrin package.

Definition of done:

- Scenario generation has measured cardinality and storage behavior for expanded candidate sets and a clear next batching rule.

Boundaries: No source-frequency semantics, no physical probability, no large production ensemble.

### TB-440: Define Scenario Batching Contract For Multi-Zone Runs

Goal: Split expanded release-zone scenario tables into deterministic batches that respect output-budget and reducer-pressure constraints.

Capability gap reduced: Multi-zone runs need bounded execution units rather than one monolithic scenario table.

Why this outranks alternatives: TB-428 showed package size and reducer budgets are first-order blockers; batching is the pragmatic path to larger measured runs.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/generate_balfrin_regional_split_submission_package.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- Deterministic batching metadata keyed by release zone, scenario family, and budget profile.
- Tests for stable ordering, non-overlap, and budget summaries.
- A no-submit package smoke path using batched scenarios.

Definition of done:

- Multi-zone scenario tables can be partitioned into reproducible budget-aware batches without changing simulation physics.

Boundaries: No Balfrin submission, no distributed execution, no probability/frequency semantics.

### TB-441: Measure Reducer Pressure On Batched Scenario Outputs

Goal: Run a fixture-backed reducer/merge pressure probe over the TB-440 batching contract.

Capability gap reduced: Unknown reducer pressure after scenario batching.

Why this outranks alternatives: Batching only helps if reducer and merge pressure stay bounded and rebuild-compatible.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_multi_zone_reducer_pressure.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `scripts/generate_candidate_source_zone_scenarios.py`

Deliverables:

- Measured file counts, byte counts, merge ordering, sample support, and output-family summaries for batched fixture outputs.
- Regression tests proving deterministic merge behavior across batch order changes.
- Updated reducer pressure doc with the new bottleneck or green path.

Definition of done:

- The batched reducer path has measured pressure evidence and either passes the budget profile or names the next specific bottleneck.

Boundaries: Fixture/scratch only unless a task explicitly authorizes live Balfrin; no generated artifacts committed.

### TB-442: Add Clean-Checkout AOI Workflow Smoke Test

Goal: Prove the documented AOI front-door commands fail closed or pass using only tracked fixtures and no ignored local artifacts.

Capability gap reduced: Hidden local-state dependence in the user-facing AOI workflow.

Why this outranks alternatives: User-facing documentation is only useful if its core commands behave predictably on a clean checkout.

Inspect first:

- `docs/aoi_user_manual.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/package_aoi_hazard_map.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- Focused tests for `describe-config`, `prepare`, `candidate-review`, `package-map`, and `workflow` using tracked fixtures or explicit blocked states.
- Assertions that ignored Tschamut/Balfrin artifacts are not required for the smoke path.
- Documentation correction if any command in the AOI manual is not clean-checkout safe.

Definition of done:

- The compact AOI user path has clean-checkout regression coverage or explicit fail-closed behavior for missing artifacts.

Boundaries: No broad full-suite rewrite, no generated artifact commits, no reliance on local ignored roots.

### TB-443: Connect QGIS Connector Manifest To AOI Smoke Coverage

Goal: Ensure the QGIS Processing connector manifest remains synchronized with the AOI front-door commands and style bundle as they evolve.

Capability gap reduced: Prototype UI contract drift.

Why this outranks alternatives: TB-430 introduced the bridge specification; a small sync test prevents it from becoming stale while avoiding a full plugin.

Inspect first:

- `tests/fixtures/qgis_processing_connector_manifest_v1.json`
- `tests/test_qgis_processing_connector_manifest.py`
- `docs/aoi_user_manual.md`
- `qgis/styles/aoi_qgis_style_bundle.json`

Deliverables:

- Extended static or smoke test coverage comparing manifest actions to AOI manual command names and available CLI subcommands.
- Clear failure messages when a command or style asset is renamed without updating the manifest.
- Optional concise note in `docs/aoi_user_manual.md` if the synchronization contract changes.

Definition of done:

- The QGIS connector manifest cannot silently drift from the documented AOI command path or tracked style assets.

Boundaries: No plugin, no GUI, no new execution layer, no operational map claim.

### TB-444: Rank Next Balfrin Probe Candidates From Measured Bottlenecks

Goal: Generate a compact, deterministic next-probe ranking from the latest measured and failed-closed Balfrin evidence.

Capability gap reduced: Ambiguity about whether to retry regional split, batch scenarios, optimize reducer pressure, or collect more local evidence next.

Why this outranks alternatives: The backlog should follow measured blockers rather than accumulating unrelated wrappers.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_regional_split_probe_gate_tb428.md`
- `docs/balfrin_multi_zone_hazard_run_tb407.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A deterministic ranking of the next bounded Balfrin probe candidates with blocker, expected evidence gain, and required pre-submit gates.
- Tests or fixture assertions for the ranking logic.
- Documentation update only if it replaces stale next-action wording.

Definition of done:

- The next live Balfrin action is ranked from current evidence and points to one concrete executable task, not a generic scale-up request.

Boundaries: Ranking only unless another task authorizes submission; no scale-up, distributed execution, or operational claim.

### TB-445: Refresh Management Feasibility Summary After Regional And AOI Updates

Goal: Update the management-facing feasibility summary after TB-431 through TB-444 clarify regional split, AOI, candidate, scenario, and QGIS readiness.

Capability gap reduced: Management-facing status drift after executable changes.

Why this outranks alternatives: This should happen after the execution and automation blockers are updated, not before, so it synthesizes measured progress instead of creating another projection-only report.

Inspect first:

- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- Concise updated management status explaining what is measured, what is blocked, and what remains projected.
- Explicit answer to whether 10-zone, 100-zone, regional, and Swiss-wide workflows are feasible under current constraints.
- No duplicate evidence package if existing surfaces can be updated.

Definition of done:

- Management-facing docs agree with the latest measured evidence and failed-closed blockers, and the next recommended executable milestone is explicit.

Boundaries: Synthesis only after upstream evidence tasks; do not upgrade failed-closed or projection-only evidence into measured capability.

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
