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

### TB-414: Freeze The AOI Conditional Map Workflow Contract

Goal: Define the canonical AOI-to-conditional-map workflow as an executable contract rather than another scattered set of helper commands.

Capability gap reduced: User-facing workflow coherence and reproducible AOI execution.

Why this outranks alternatives: OpenNHM-style workflow design and RAMMS scenario practice both point to one named project/scenario workflow before adding more science surfaces or wrappers.

Inspect first:

- `docs/opennhm_learnings_report.md`
- `background/RAMMS_ROCK2_Manual.pdf`
- `scripts/run_aoi_hazard_workflow.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- One compact AOI workflow contract covering prepare, review, scenario generation, bounded execution, post-processing, GIS packaging, and interpretation.
- `scripts/run_aoi_hazard_workflow.py` help/status output aligned with that contract, or a documented reason if the CLI already exposes the needed phases.
- Regression coverage or a focused smoke check proving the contract remains discoverable from the front door.

Definition of done:

- A new worker can discover the canonical AOI workflow without reading long maturity or backlog history, and the task removes any stale competing AOI workflow wording it touches.

Boundaries: No new simulation, no operational claims, no scale-up authorization, no physical-probability or annual-frequency semantics.

### TB-415: Add AOI Config Describe And Precedence Mode

Goal: Make AOI workflow configuration inspectable before execution, including defaults, site config, source/scenario policy, generated manifests, and CLI overrides.

Capability gap reduced: Hidden configuration coupling and reproducibility risk.

Why this outranks alternatives: Both OpenNHM-style workflows and RAMMS scenario reproducibility depend on transparent configuration state before running expensive trajectories.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- A compact `describe-config` or equivalent dry-run mode for the AOI front door.
- Machine-readable output that identifies config layers, effective values, unknown fields, and generated-root locations without running simulations.
- Focused tests for precedence and missing-field behavior.

Definition of done:

- A worker can run one command to see the effective AOI workflow configuration and verify it does not depend on untracked local state.

Boundaries: No new config framework, no downloads, no simulations, no operational semantics.

### TB-416: Add Terrain Resolution And Domain QA To AOI Preparation

Goal: Add deterministic terrain QA to AOI preparation so DEM resolution, CRS, nodata, crop extent, and domain margins are reported before release-zone or hazard generation.

Capability gap reduced: Real-terrain preprocessing robustness.

Why this outranks alternatives: RAMMS guidance makes DEM quality and resolution a first-order setup check; a bad terrain crop invalidates every downstream candidate and scenario table.

Inspect first:

- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_aoi_terrain_preprocessing.py`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Terrain QA fields for CRS, grid spacing, nodata coverage, AOI containment, and result-grid resolution class.
- A warning or blocked status for obviously unsuitable terrain domains.
- Fixture-backed tests covering valid terrain, missing nodata metadata, and resolution/domain warnings.

Definition of done:

- AOI preparation emits deterministic terrain QA before source-zone candidate generation and explains the next unblock action when QA fails.

Boundaries: No terrain resampling implementation unless already supported locally, no claim that one resolution is physically validated, no operational claims.

### TB-417: Derive Public-Context Ground Material Prior Layers

Goal: Generate deterministic, provenance-tagged ground material prior layers from available public context products for use in scenario metadata and GIS review.

Capability gap reduced: Terrain/context semantics between raw swisstopo inputs and model scenario assumptions.

Why this outranks alternatives: RAMMS highlights terrain category selection as a dominant modeling choice, while the current workflow still treats many context inputs as staging evidence rather than scenario-relevant priors.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/stage_public_geodata_cache.py`
- `scripts/plan_aoi_terrain_preprocessing.py`

Deliverables:

- A deterministic material-prior manifest or raster/vector layer for categories such as road, water/swamp, forest, talus/rock, and unknown.
- Provenance fields linking each category to source public products and fallback rules.
- Tests or fixture smoke checks proving unknown/missing context remains explicit rather than silently inferred.

Definition of done:

- The AOI workflow can carry a material-prior layer into review/scenario metadata without calibrated friction, restitution, or operational terrain-parameter claims.

Boundaries: No calibration, no physics changes, no RAMMS parameter transfer, no operational terrain-material claim.

### TB-418: Add Forest Context Intake And Realization Planning

Goal: Add an optional forest-context intake and deterministic realization plan so forest presence, missing DBH/density evidence, and scenario variants are explicit.

Capability gap reduced: Missing vegetation/context treatment for real AOIs.

Why this outranks alternatives: RAMMS treats forest as a major runout-control input; even if the Rust workflow does not yet model tree impacts, the uncertainty must be explicit before Balfrin-scale demonstration claims.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/generate_candidate_source_zone_scenarios.py`

Deliverables:

- Optional forest-context fields in AOI/prepared-pilot manifests.
- A deterministic forest-on/forest-deferred scenario planning record that separates mapped forest presence from missing stem-density/DBH evidence.
- Focused tests proving forest data absence remains a bounded deferral, not a silent omission.

Definition of done:

- Real AOI scenario plans can state whether forest context is staged, deferred, or intentionally excluded, with no change to physical model behavior.

Boundaries: No tree-impact physics, no calibrated forest parameters, no operational forest-protection claim.

### TB-419: Add Rock Shape And Block-Volume Scenario Families

Goal: Make deterministic block-volume and rock-shape scenario families first-class inputs to scenario-table generation.

Capability gap reduced: Handcrafted scenario semantics and weak shape/volume uncertainty representation.

Why this outranks alternatives: RAMMS guidance shows that block volume and shape variation are core scenario dimensions; scaling release zones without structured scenario families would multiply poorly documented assumptions.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/generate_tschamut_block_scenario_tables.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `docs/probabilistic_scenario_model_design.md`

Deliverables:

- Deterministic scenario-family templates for small/medium/large block volumes and at least equant/platy/elongated shape classes where supported by the current Rust inputs.
- Scenario-table provenance fields that identify release geometry, block family, shape family, and deterministic orientation/repetition policy.
- Tests proving stable scenario IDs and cardinality for a fixture candidate set.

Definition of done:

- A multi-zone candidate set can produce reproducible scenario tables with explicit block/shape families and no hidden physical-frequency semantics.

Boundaries: No new physics, no calibrated block population, no annual-frequency or physical-probability claims.

### TB-420: Add Deterministic Release Geometry Sampling Modes

Goal: Support deterministic point, line, and area release sampling from candidate source geometries with stable release IDs and reproducible start distributions.

Capability gap reduced: Release-zone automation realism.

Why this outranks alternatives: RAMMS distinguishes point, line, and area releases as materially different representations; current Swiss-wide automation needs this before larger multi-zone demonstrations are meaningful.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/plan_pragmatic_release_plan.py`
- `tests/test_plan_pragmatic_release_plan.py`

Deliverables:

- Deterministic sampling modes for point, line, and area candidate geometries.
- Release-plan manifests with sampling density, seed/provenance, geometry type, and release-count summaries.
- Fixture tests covering stable IDs, boundary behavior, and empty/small candidate handling.

Definition of done:

- Candidate source polygons or lines can be converted into reproducible release-point plans without manual point editing.

Boundaries: No claim that generated candidates are validated source zones, no tuning to fit Tschamut, no new simulations.

### TB-421: Add Candidate And Hazard QGIS Style Bundle

Goal: Provide reusable QGIS style files for source candidates, accepted/rejected review zones, release points, scenario families, and conditional hazard rasters.

Capability gap reduced: GIS review usability for AOI and Balfrin demonstrations.

Why this outranks alternatives: OpenNHM learnings favor QGIS-compatible map review before heavier plugin work; styles make current outputs inspectable without changing science.

Inspect first:

- `scripts/generate_aoi_map_qa_review.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/hazard_layers.md`
- `docs/opennhm_learnings_report.md`

Deliverables:

- Tracked QGIS style assets or templates for candidate overlays, release points, scenario families, and key hazard rasters.
- Map-package manifest references to the style assets.
- A fixture-backed package or test proving styles are discoverable without generated artifacts.

Definition of done:

- A reviewer can open an AOI package in QGIS and apply consistent visual styling without relying on screenshots or ad hoc layer naming.

Boundaries: No QGIS plugin yet, no operational map symbology claim, no generated raster commits.

### TB-422: Build Conditional Statistics Surfaces From Trajectory Samples

Goal: Add reusable per-cell conditional statistics surfaces for count, reach fraction, Q90/Q95/Q99, median, and maximum where the underlying samples support them.

Capability gap reduced: Scientific interpretation and hazard-product comparability.

Why this outranks alternatives: RAMMS statistics mode makes cellwise count/quantile surfaces central; the Rust workflow should expose equivalent conditional diagnostic products before larger demonstrations.

Inspect first:

- `scripts/build_hazard_layers.py`
- `docs/hazard_layers.md`
- `tests/test_hazard_layers.py`
- `scripts/summarize_spatial_same_scale_uncertainty.py`

Deliverables:

- Deterministic statistics layer definitions and manifest entries for supported variables.
- Explicit sample-count and insufficient-sample flags so high quantiles are not overinterpreted.
- Focused tests using fixture trajectories.

Definition of done:

- Hazard packages can include conditional statistics surfaces and sample-support metadata without changing closure or physical-credibility status.

Boundaries: No annual probability, no risk/exposure/vulnerability semantics, no operational design quantile claim.

### TB-423: Add Target-Line Conditional Impact Diagnostics

Goal: Compute conditional target-line diagnostics for roads or protection lines from existing trajectory/hazard outputs.

Capability gap reduced: Management and engineering interpretability for Balfrin map outputs.

Why this outranks alternatives: RAMMS target-line analysis is highly useful for linear infrastructure, and a conditional diagnostic variant can be implemented without source-frequency or risk semantics.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/package_aoi_hazard_map.py`
- `tests/test_hazard_layers.py`
- `docs/hazard_layers.md`

Deliverables:

- A target-line input mode or helper that counts trajectory intersections and summarizes conditional kinetic energy and jump height along line segments.
- Output CSV/GeoJSON plus manifest entries with sample counts and insufficient-sample warnings.
- Tests for a tiny synthetic target line.

Definition of done:

- A road or review line can be evaluated as a conditional diagnostic target, with clear separation from risk, exposure, or annual-frequency claims.

Boundaries: No risk model, no object vulnerability, no physical occurrence probability, no operational protection design claim.

### TB-424: Define Regional Split Execution Contract

Goal: Define a compact regional split contract that maps AOI candidates into source groups, scenario IDs, execution chunks, and reducer merge keys.

Capability gap reduced: Multi-zone execution scalability and orchestration simplicity.

Why this outranks alternatives: OpenNHM’s regional splitting pattern directly addresses the next scaling bottleneck without requiring distributed execution or a framework rewrite.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/run_aoi_hazard_workflow.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A deterministic split-plan schema or manifest emitted by existing front-door commands.
- Required fields for `group`, `zone_id`, `scenario_id`, optional sampling weight, chunk ID, expected output root, and merge key.
- Fixture tests proving stable ordering and no duplicate execution keys.

Definition of done:

- A multi-zone AOI can be partitioned into reproducible execution chunks and later merged without relying on implicit file naming.

Boundaries: No distributed execution, no Balfrin submission, no scale-up claim.

### TB-425: Run Fixture Regional Split And Merge Dry Run

Goal: Exercise the regional split contract on a small fixture AOI with multiple source groups and merge the resulting reduced outputs.

Capability gap reduced: Rebuildable multi-zone workflow realism.

Why this outranks alternatives: A split contract is only useful if a small end-to-end split/merge path proves output and reducer assumptions before Balfrin jobs.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/build_hazard_layers.py`
- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- Fixture-backed split/merge run producing reduced outputs, merge manifest, file/byte counts, and sample-support summaries.
- Focused tests for deterministic merge ordering and rebuild-compatible output families.
- Updated command-plan/front-door references if the dry run becomes the canonical pre-Balfrin check.

Definition of done:

- The repo can demonstrate a complete local multi-group split/merge workflow without generated artifact commits.

Boundaries: No live Balfrin submission, no large ensemble, no operational or scale-up claim.

### TB-426: Measure Scenario Storage And Output Tier Pressure

Goal: Quantify scenario-table, release-plan, trajectory, statistics, GIS, and reduced-output storage pressure for candidate expansion.

Capability gap reduced: Output/runtime sustainability at larger AOIs.

Why this outranks alternatives: RAMMS explicitly optimizes scenario/trajectory storage; the Rust workflow needs measured tier pressure before management can trust Swiss-scale feasibility projections.

Inspect first:

- `scripts/summarize_management_aoi_scenario_pressure.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/derive_hazard_rebuild_reduced_profile.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- Measured file/byte/cardinality summary for at least one fixture and one current real-AOI candidate bundle when available.
- Comparison of minimal, rebuildable-reduced, GIS, and research-full output tiers.
- A deterministic recommendation for the smallest tier suitable for Balfrin demonstration replay.

Definition of done:

- Scenario and output tier pressure is measured in a reusable helper and the next scale bottleneck is explicit.

Boundaries: No large production ensemble, no deletion of existing outputs, no scale-up authorization.

### TB-427: Build Balfrin Regional Split Submission Package

Goal: Generate a no-submit Balfrin `postproc` submission package from the regional split/merge contract and current accepted source candidates.

Capability gap reduced: Balfrin multi-zone demonstration readiness.

Why this outranks alternatives: After local split/merge evidence, the next management-relevant step is a runnable, budgeted Balfrin package rather than another projection report.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `docs/orchestration_strategy.md`

Deliverables:

- A no-submit package with exact command, writable remote roots, output budgets, preservation plan, and authorization/preflight status.
- Failure-closed behavior if access, budget, output profile, or package contracts are not ready.
- Tests or smoke checks proving no `sbatch` is attempted during package generation.

Definition of done:

- A GPT-5.5 worker can inspect one package and know whether a bounded `postproc` submission is authorized and runnable.

Boundaries: No submission in this task, no non-postproc partition, no distributed execution, no scale-up or operational claim.

### TB-428: Execute Bounded Regional Split Balfrin Probe

Goal: Submit and actively monitor one bounded `postproc` Balfrin probe from the approved regional split package when all repository gates pass.

Capability gap reduced: Measured multi-zone execution realism.

Why this outranks alternatives: Management needs measured evidence for whether multi-zone execution is feasible; this is the smallest live step after the no-submit package is ready.

Inspect first:

- `docs/orchestration_strategy.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/collect_balfrin_probe_metrics.py`

Deliverables:

- One measured Balfrin `postproc` run or a failed-closed no-submit/submit record with the first blocker identified.
- Runtime, memory when available, validation/hazard file counts and bytes, reducer metrics, and preserved run-root pointers.
- Updated evidence surfaces only to the extent needed to distinguish measured execution from blocked/fixture-backed/projection-only evidence.

Definition of done:

- The run either completes with measured evidence or fails closed with the exact persistent blocker and next unblock action; no ambiguous half-state remains.

Boundaries: GPT-5.5 worker required, one bounded probe only, postproc partition only, no distributed execution, no operational, scale-up, annual-frequency, physical-probability, risk, exposure, or vulnerability claims.

### TB-429: Consolidate AOI User Manual And QGIS Review Entry Point

Goal: Provide a short user-facing manual entry point for AOI preparation, candidate review, bounded execution, and QGIS map inspection.

Capability gap reduced: Usability for non-author workers and management-facing demonstrations.

Why this outranks alternatives: OpenNHM succeeds partly because users have a clear manual and GUI/GIS review path; the Rust workflow needs a concise equivalent without expanding long root docs.

Inspect first:

- `README.md`
- `AGENTS.md`
- `docs/opennhm_learnings_report.md`
- `scripts/run_aoi_hazard_workflow.py`

Deliverables:

- A concise AOI quickstart or manual page linked from README/AGENTS without duplicating maturity history.
- Exact commands for AOI config description, preparation, candidate review, package generation, and QGIS style application.
- Explicit non-operational and conditional-only interpretation boundaries.

Definition of done:

- A new user can find the AOI front door and QGIS review path from README in under one minute, with links to detailed docs only where needed.

Boundaries: Documentation must stay compact; no new claims, no new wrappers, no broad README expansion.

### TB-430: Prototype Minimal QGIS Processing Connector Manifest

Goal: Define a minimal QGIS Processing connector manifest for the AOI front-door commands without building a full plugin.

Capability gap reduced: Future user-interface integration path.

Why this outranks alternatives: The OpenNHM comparison suggests QGIS integration is valuable, but a manifest/prototype avoids premature plugin complexity while validating command boundaries.

Inspect first:

- `docs/opennhm_learnings_report.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/script_inventory.md`

Deliverables:

- A small tracked prototype manifest or design fixture mapping QGIS actions to existing CLI commands and expected inputs/outputs.
- A smoke test or static check that the named commands and style assets exist.
- A clear deferral note for full plugin implementation.

Definition of done:

- The repo has a concrete, testable bridge specification for QGIS integration that reuses existing front doors and does not add a second workflow layer.

Boundaries: No full QGIS plugin, no GUI development, no new execution framework, no operational map claim.

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
