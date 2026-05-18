# Agent Work Log

Append-only current work log for TB tasks.

This file is intentionally short and chronological. The full pre-refactor
history, non-TB planning notes, M-series milestones, backlog refills, and
review triage entries live in `docs/archive/agent_work_log_archive.md`.

## Worker Instructions

- Always append new entries at the bottom of this file. Do not insert work
  logs near related older entries.
- Use one `### TB-XXX: Short Title` heading per completed task.
- Keep the TB entries in ascending order. If the current task is `TB-058`,
  its entry belongs after `TB-057`.
- Do not add backlog-refill notes, review triage, planning notes, or
  non-task narrative here. Put durable planning in `docs/task_backlog.md` or
  `docs/decision_log.md`; archive older non-TB history only in
  `docs/archive/agent_work_log_archive.md`.
- Prefer concise entries. Link to generated helpers, docs, and commits rather
  than pasting long command transcripts.
- Do not leave `Commit: pending` in a committed entry. Use a two-commit
  sequence when recording a completed task: first commit the implementation
  with the backlog removal and no new work-log entry, then append the work-log
  entry with that implementation commit hash and make a small follow-up
  `Record TB-XXX work log` commit. Do not amend repeatedly to chase a
  self-referential hash.

## Entry Template

```markdown
### TB-XXX: Short Title

- Date: YYYY-MM-DD
- Commit: `<implementation-commit-hash>`; never leave `pending` in a pushed commit.
- Objective: one sentence describing the task.
- Files changed: concise comma-separated list or grouped paths.
- Implementation summary: 2-4 bullets focused on what changed.
- Checks run: focused tests plus repo hygiene checks.
- Result/status: completed, blocked, or follow-up needed.
- Boundaries: note no physics/tuning/operational/scale-up changes when relevant.
- Next task: `TB-YYY` or backlog refill needed.
```

## Completed TB Entries

This active log keeps detailed entries for the latest completed TB range only.
Older detailed TB entries were moved to `docs/archive/agent_work_log_archive.md`
during the documentation-surface cleanup so normal onboarding does not have to
scan thousands of lines of completed history.

## Archived Milestone Summary

- TB-001 through TB-060: early hazard-map, public benchmark, same-scale
  Tschamut, and workflow-orchestration foundation work. Full entries are in the
  archive.
- TB-061 through TB-120: same-scale uncertainty, output-profile, Balfrin
  single-release-zone, and post-run interpretation work. Full entries are in
  the archive.
- TB-121 through TB-180: Balfrin evidence-bundle, AOI automation,
  target-area demonstration, second-site dry-run, and physical-evidence
  boundary work. Full entries are in the archive.
- TB-181 through TB-202: retained below as the active recent execution history.

### TB-181: Automated Release-Zone Candidate Sweep On Real Terrain

- Date: 2026-05-17
- Commit: local
- Objective: run deterministic release-zone candidate generation on the staged Tschamut real-terrain crop with scratch-root outputs, measured runtime/output accounting, and an explicit multi-zone stress-test readiness signal.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/summarize_balfrin_target_area_candidate_stability.py`, `tests/test_balfrin_target_area_candidate_stability.py`, `docs/current_maturity_snapshot.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added deterministic component-area distribution statistics to the terrain candidate product bundle so emitted scratch-root polygons carry an explicit area distribution for the candidate components.
  - Wrapped the frozen target-area candidate stability helper with a measured real-terrain sweep summary that records candidate count/area, slope and terrain thresholds, stable-versus-sensitive classes, runtime, output counts, and an explicit multi-zone scenario-generation readiness classification.
  - Added focused regressions for deterministic output shape, blocked-missing-input behavior from a temporary repo root, and the new sweep measurements.
  - Updated the maturity snapshot and swisstopo data strategy to mention the measured real-terrain sweep and its runtime/output evidence, then removed TB-181 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/summarize_balfrin_target_area_candidate_stability.py tests/test_balfrin_target_area_candidate_stability.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_candidate_stability -v`
- Result/status: implemented_measured
- Boundaries: no release-zone validation claim, no threshold tuning, no field-evidence claim, no operational release-zone claim, no Balfrin job submission, and no generated GIS or raster outputs committed.
- Next task: `TB-182`

### TB-182: Large Deterministic Scenario Table Generation Stress Test

- Date: 2026-05-17
- Commit: `6547e90`
- Objective: generate a deterministic stress-test scenario table from candidate release-point rows, measure cardinality/runtime/storage pressure, and report TB-183 planning-input readiness.
- Files changed: `scripts/generate_candidate_source_zone_scenarios.py`, `tests/test_candidate_source_zone_scenario_stress.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a scratch-root-only candidate source-zone stress helper that expands release-point candidates across the frozen Tschamut block-family policy and writes a manifest-rich scenario table plus bounded report.
  - Recorded scenario cardinality summaries by candidate, source-zone family, block family, and scenario-family template, along with runtime and storage measurements and an explicit first-bottleneck report.
  - Added focused regressions for deterministic manifest/row summaries and fail-closed missing-input handling, then removed TB-182 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_scenario_stress -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_candidate_source_zone_scenarios.py tests/test_candidate_source_zone_scenario_stress.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no annual-frequency semantics, no physical probability semantics, no parameter tuning, no ensemble execution, and no generated large tables committed to git.
- Next task: `TB-183`

### TB-183: Multi-Release-Zone Balfrin Dry-Run Demonstration

- Date: 2026-05-17
- Commit: local
- Objective: build a bounded multi-release-zone Balfrin dry-run package that combines automatic release candidates, deterministic scenario planning, reduced-output pressure summaries, restartability checkpoints, and uncertainty-aware post-processing commands without authorizing live Balfrin execution.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a scratch-root-only multi-release-zone handoff generator that composes the candidate sweep summary, a contract-derived deterministic-scenarios snapshot, bounded output and reducer pressure summaries, single-job restartability evidence, and staged uncertainty-aware post-processing commands into one reviewable package.
  - Kept the target-area handoff explicit in the command plan while preventing the package from materializing the target-area bundle, and normalized the volatile candidate sweep runtime so repeated dry-run generation is deterministic.
  - Added focused regressions for the JSON CLI smoke path, the package filesystem outputs, the staged command-plan shape, and the non-materialized target-area bundle boundary.
  - Removed TB-183 from the active backlog once the dry-run package and focused tests were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no live Balfrin job submission, no scale-up authorization, no distributed execution, no operational claim, no generated artifacts committed, and no target-area bundle materialized by the package helper.
- Next task: `TB-184`

### TB-184: AOI-To-Prepared-Pilot End-To-End Automation

- Date: 2026-05-17
- Commit: local
- Objective: compose the AOI acquisition, cache verification, terrain preprocessing, release-candidate, scenario-generation, and portable command-plan helpers into one deterministic prepared-pilot report.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit cache-verification report and workflow step to the AOI-to-prepared-pilot orchestrator so the report now composes product discovery, cache verification, terrain preprocessing, candidate generation, scenario planning, and command-plan output in one deterministic pass.
  - Threaded deterministic ignored-root layout records and blocked-missing-input inventories through the prepared-pilot summary and case-skeleton bundle so clean-checkout failures name the missing manifest, product, and metadata paths.
  - Extended the focused AOI-prepared-pilot tests with a verified synthetic cache-manifest path and a blocked missing-cache path, then updated the preparation documentation to match the new orchestration shape.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_verifier tests.test_aoi_to_prepared_pilot_dry_run -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_to_prepared_pilot_dry_run.py tests/test_aoi_to_prepared_pilot_dry_run.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no public-data download, no simulation run, no second-site ensemble, no operational claim, and no synthetic fixture was represented as public evidence.
- Next task: `TB-185`

### TB-185: Switzerland-Scale Runtime And Storage Projection

- Date: 2026-05-17
- Commit: local
- Objective: extend the Swiss-wide execution envelope helper into a deterministic multi-case planning report that covers 10-zone, 100-zone, regional, and Switzerland-scale envelopes with explicit no-go / defer / next-probe labels, rebuildability ratios, and bottleneck labels.
- Files changed: `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Swiss-wide envelope helper to load canonical single-job, target-area, and generated scenario-table evidence sources, then synthesize a four-case planning table for 10-zone, 100-zone, regional, and Swiss-wide envelopes.
  - Added explicit rebuildability-cost ratios and bottleneck labels for validation output, hazard output, reducer merge, manifest count, memory, and scheduler practicality, while keeping the helper deterministic and read-only with respect to the repository.
  - Added a focused synthetic regression for the canonical planning cases plus the existing measured-path regressions, updated the Balfrin sufficiency note and maturity snapshot, and removed TB-185 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/estimate_swiss_wide_execution_envelope.py tests/test_swiss_wide_execution_envelope.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope -v`
  - `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --format json >/tmp/tb185_envelope.json`
- Result/status: implemented_measured
- Boundaries: projection-only; no scale-up authorization, no distributed execution, no Swiss-wide run, no annual-frequency or operational claim, and target-area evidence is reported as blocked rather than invented when the measured run root is unavailable.
- Next task: `TB-186`

### TB-186: Large-AOI GIS Packaging Stress Test

- Date: 2026-05-17
- Commit: local
- Objective: add a bounded large-AOI GIS/COG stress-test helper that reports standard-root package runtime, scratch conversion timing, raster count, manifest size, layer parity, and missing-layer summaries while keeping the standard-root COG-blocked state visible.
- Files changed: `scripts/summarize_large_aoi_gis_cog_stress_test.py`, `tests/test_large_aoi_gis_cog_stress_test.py`, `docs/pilot_gis_package.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a standalone large-AOI stress-test helper that audits the standard package root, measures an ignored scratch conversion, and separates the standard-root COG-blocked status from the converted scratch package readiness.
  - Reported package runtime, COG conversion timing, raster count, manifest size, layer parity, missing-layer summaries, and a first GIS packaging bottleneck label without claiming operational readiness or writing generated rasters into the repository.
  - Added focused regressions for the standard-root COG-blocked plus scope-delta-ready path and the blocked-missing-input short-circuit, then updated the pilot GIS package documentation and removed TB-186 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_large_aoi_gis_cog_stress_test`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_large_aoi_gis_cog_stress_test tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion tests.test_balfrin_target_area_gis_cog_scope`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: no operational GIS product claim, no manual QGIS acceptance claim, no generated raster commit, and scratch COG readiness does not upgrade the standard root.
- Next task: `TB-187`

### TB-187: Multi-Zone Reducer And Merge Scaling Probe

- Date: 2026-05-17
- Commit: local
- Objective: build a deterministic scratch-root multi-zone reducer probe that measures chunk scaling, merge-order determinism, manifest size, file pressure, reducer wall time, and output-family bytes without relying on ignored live artifacts or a live Balfrin job.
- Files changed: `scripts/summarize_multi_zone_reducer_pressure.py`, `tests/test_multi_zone_reducer_pressure.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a scratch-root probe helper that materializes a 12-zone multi-zone input set, writes manifest-shaped reducer and trajectory outputs, and summarizes chunk count, merge order, reducer wall time, manifest size, file count, and bytes by output family.
  - Classified the probe as `multi_zone_dry_run_blocked` because manifest pressure, output-family pressure, and reducer-runtime pressure are all visible in the scratch-root measurements, and surfaced the corresponding reducer-constraint recommendations for TB-183.
  - Added focused regressions for deterministic repeated materialization and requested release-zone-count propagation, then wrote a small markdown report that preserves the measured blocker/constraint set and removed TB-187 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_reducer_pressure tests.test_bounded_reducer_runtime_scaling -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_reducer_pressure.py tests/test_multi_zone_reducer_pressure.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py --materialize-root /tmp/rust_rockfall/tb187_multi_zone_probe --format json > /tmp/tb187_multi_zone_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin job, no distributed reducer, no MPI/GPU, no physics change, no operational hazard claim, and no generated heavy outputs committed.
- Next task: `TB-188`

### TB-188: Real Chant Sura Workflow Dry Run

- Date: 2026-05-17
- Commit: local
- Objective: build a deterministic Chant Sura / Flüelapass dry-run report that composes the real-context readiness gate, AOI preparation, release-candidate generation, scenario generation, command planning, and a permission-gated tiny bounded ensemble handoff without downloading public data or claiming operational readiness.
- Files changed: `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Chant Sura dry-run reporter that threads together the real-context readiness gate, the Chant Sura dry-run case-skeleton helper, the terrain release-candidate generator, the pragmatic scenario-plan helper, and the portable command-plan helper.
  - Classified the default checkout as `blocked_missing_inputs`, the staged fixture path as `ready_for_next_step`, and the tiny bounded ensemble handoff as permission-gated so the report stays fail-closed unless explicit permission is recorded.
  - Added focused regressions for the blocked path, the ready fixture path, and the permission-gated tiny handoff, then removed TB-188 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_fluelapass_workflow_dry_run_report -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate tests.test_plan_terrain_release_zone_candidates tests.test_plan_pragmatic_release_plan tests.test_pilot_command_plan tests.test_chant_sura_fluelapass_workflow_dry_run_report -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_chant_sura_fluelapass_dry_run_report.py tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_chant_sura_fluelapass_dry_run_report.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no downloads, no second-site ensemble execution, no synthetic public-context evidence, no operational claim, no physical validation claim, and the tiny ensemble handoff remains permission-gated.
- Next task: `TB-189`

### TB-189: Release-Zone Candidate Stability And Sensitivity

- Date: 2026-05-17
- Commit: local
- Objective: measure deterministic stability of automatically generated release-zone candidates across slope-threshold, smoothing, terrain-resolution, and AOI-boundary perturbations, and surface stable, unstable, and heuristic-sensitive classifications with persistence metrics.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/summarize_balfrin_target_area_candidate_stability.py`, `docs/current_maturity_snapshot.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_balfrin_target_area_candidate_stability.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Expanded the terrain-candidate sensitivity helper to sweep six deterministic variants: baseline, bounded slope thresholds, 3x3 smoothing, 2x2 coarsened/reexpanded resolution, and a one-cell AOI-boundary trim proxy.
  - Added an explicit sensitivity matrix, persistence metrics, and stable/unstable/heuristic-sensitive region classifications, then exposed them through the Balfrin target-area stability report and a scratch report JSON under the provided output root.
  - Kept the candidate product bundle GIS-readable, filtered the scratch stability report out of output-count measurements so repeated runs stay deterministic, and updated the maturity/data-strategy prose plus focused regressions to cover the new perturbation summaries and fail-closed missing-input behavior.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates tests.test_balfrin_target_area_candidate_stability -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/summarize_balfrin_target_area_candidate_stability.py tests/test_plan_terrain_release_zone_candidates.py tests/test_balfrin_target_area_candidate_stability.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_candidate_stability.py --output-root /tmp/tb189_candidate_products --format json >/tmp/tb189_candidate_stability_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no release-zone validation, no threshold tuning for acceptance, no operational source-zone claim, no generated GIS outputs committed, and the sensitivity report remains a heuristic stability characterization only.
- Next task: `TB-190`

### TB-190: Full Balfrin Demonstration Evidence Package

- Date: 2026-05-17
- Commit: local
- Objective: build one deterministic Balfrin management package that separates measured, fixture-backed, blocked, and unavailable evidence, and answers whether the current architecture is plausibly extensible toward Swiss-wide workflows without turning that answer into an authorization.
- Files changed: `scripts/summarize_balfrin_management_demo_package.py`, `tests/test_balfrin_management_demo_package.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Expanded the management package to include explicit AOI automation, release/scenario automation, blocked target-area probe metrics, the measured canonical target-area bundle, the measured physical-credibility gap report, and a dedicated Swiss-wide extension answer section.
  - Kept runtime, replay, restartability, GIS scope, uncertainty, scaling, and claim-boundary sections separate while preserving section-level provenance counts for measured, fixture-backed, unavailable, and blocked evidence.
  - Updated the focused regressions to pin the expanded section set, the management-facing no-go answer, and the deterministic regeneration command list, and removed TB-190 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package tests.test_balfrin_target_area_evidence_bundle tests.test_balfrin_physical_credibility_evidence_gaps`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_management_demo_package.py tests/test_balfrin_management_demo_package.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --artifact-dir /tmp/balfrin_management_demo_package_v1 --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_measured
- Boundaries: no marketing overclaim, no operational acceptance, no physical-credibility upgrade, no scale-up authorization, no annual-frequency semantics, and no generated heavy artifacts committed.
- Next task: `TB-191`

### TB-191: Balfrin Metrics And Run-Root Preservation Gate

- Date: 2026-05-17
- Commit: local
- Objective: define and test the Balfrin evidence-preservation gate that must pass before a future authorized live run can be treated as demonstration evidence.
- Files changed: `scripts/summarize_balfrin_probe_preservation_gate.py`, `tests/test_balfrin_probe_preservation_gate.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/balfrin_probe_slurm_driver.md`, `docs/archive/balfrin_target_area_spatial_uncertainty_stability_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated read-only preservation-gate helper that combines the collected probe metrics with run-root file checks, required SLURM accounting fields, output-family summaries, and declared GIS artifact paths.
  - Classified complete, partial, and missing-run-root cases fail closed, with explicit missing-metric and missing-preserved-path reporting so a future live run is only treated as evidence when the contract is satisfied.
  - Updated the operator guidance in the Balfrin sufficiency note, SLURM driver, and target-area stability note so the preservation gate is called out as the evidence-preservation check rather than relying on the metrics report alone.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_preservation_gate tests.test_balfrin_probe_metrics_report`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_probe_preservation_gate.py tests/test_balfrin_probe_preservation_gate.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin submission, no scale-up authorization, no distributed execution, no operational claim, and no fabricated metrics.
- Next task: `TB-192`

### TB-192: Backlog And Command-Plan Reference Integrity Checker

- Date: 2026-05-17
- Commit: local
- Objective: add a fail-fast repository-consistency check that rejects stale active-backlog `Inspect first` paths and stale command-plan or handoff script references before the next worker starts.
- Files changed: `scripts/check_repo_consistency.py`, `docs/task_backlog.md`, `tests/test_repo_consistency_claim_hygiene.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an active-backlog path audit that reads each active task's `Inspect first` list, allows only explicitly marked external or generated-scratch references to bypass repo resolution, and fails when a listed repository path no longer exists.
  - Added a command-plan and handoff reference audit that walks the emitted helper reports, validates real script references against tracked repository files, and skips template-only command entries so the current backlog remains clean.
  - Added focused regressions for the valid backlog case, a missing `Inspect first` path, and a stale script reference, then updated the backlog protocol note so future tasks keep their inspect-first paths resolvable.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_repo_consistency.py tests/test_repo_consistency_claim_hygiene.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene -v`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `git diff --check`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no task execution, no command-plan regeneration, no generated artifact commit, no broad documentation rewrite, and no scale-up or operational-claim change.
- Next task: `TB-193`

### TB-193: Clean-Checkout Reproducibility Blocked-Report Mode

- Date: 2026-05-17
- Commit: local
- Objective: add a deterministic clean-checkout mode that proves the same-scale readiness, Balfrin probe-metrics, Balfrin target-area bundle, and second-site public-geodata helpers fail closed when ignored local artifacts and mounted run roots are absent.
- Files changed: `scripts/summarize_clean_checkout_blocked_reports.py`, `tests/test_clean_checkout_blocked_reports.py`, `docs/balfrin_tschamut_pilot_runbook.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only clean-checkout summary helper that runs the selected readiness and evidence helpers against an isolated temporary root, reuses the existing blocked-report contracts, and emits a compact inventory of tracked, fixture-backed, ignored-local, and unavailable evidence.
  - Kept the same-scale helper on a temporary root with ignored output directories absent, forced the Balfrin probe-metrics helper to use a missing run root, and fed the second-site public-geodata preflight a clean-checkout config whose expected staged inputs all point at the isolated root.
  - Added focused regression coverage for the blocked helper statuses, the inventory categories, and the helper CLI artifact-writing path; documented the command sequence to run before treating local readiness as measured evidence.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_clean_checkout_blocked_reports.py tests/test_clean_checkout_blocked_reports.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_clean_checkout_blocked_reports -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_blocked_report
- Boundaries: no public-data download, no Balfrin access requirement, no deletion of local ignored artifacts, no new evidence claim, and no generated heavy outputs committed.
- Next task: `TB-194`

### TB-194: Shared Python Workflow Utility Extraction

- Date: 2026-05-17
- Commit: local
- Objective: extract duplicated Python workflow helpers into one shared module so validator and workflow-script safety rules stop drifting apart.
- Files changed: `scripts/lib/__init__.py`, `scripts/lib/workflow_validation.py`, `scripts/validate_source_frequency_evidence.py`, `scripts/validate_block_release_probability_evidence.py`, `scripts/validate_scalable_conditional_target_gate.py`, `scripts/validate_scalable_conditional_execution.py`, `scripts/validate_physical_frequency_reducer_preconditions.py`, `scripts/validate_annual_physical_validation_calibration_review_gate.py`, `scripts/validate_public_real_site_conditional_pilot_run.py`, `tests/test_workflow_validation_helpers.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a small shared `scripts/lib/workflow_validation.py` module with YAML/JSON loading, path resolution, text normalization, SHA-256 validation, `require_*` helpers, claim-boundary field checks, misleading-text scanning, and reusable status-message rendering.
  - Migrated six validator scripts plus the pilot-run validator to the shared helpers, keeping their CLI output and schema-specific validation logic intact while binding each script to its own exception type.
  - Added focused helper tests for loader, checksum, normalization, claim-boundary scan, and status rendering behavior; the existing validator regression tests continue to cover the accepted and rejected fixtures.
  - Kept schema-specific claim-boundary rules, target-gate policies, pilot-run command-plan assembly, and report checksum parsing intentionally script-local.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/lib/workflow_validation.py scripts/validate_source_frequency_evidence.py scripts/validate_block_release_probability_evidence.py scripts/validate_scalable_conditional_target_gate.py scripts/validate_scalable_conditional_execution.py scripts/validate_physical_frequency_reducer_preconditions.py scripts/validate_annual_physical_validation_calibration_review_gate.py scripts/validate_public_real_site_conditional_pilot_run.py tests/test_workflow_validation_helpers.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_workflow_validation_helpers tests.test_source_frequency_evidence tests.test_block_release_probability_evidence tests.test_scalable_conditional_target_gate tests.test_scalable_conditional_execution tests.test_physical_frequency_reducer_preconditions tests.test_annual_physical_validation_calibration_review_gate tests.test_public_real_site_conditional_pilot_run`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: bounded extraction only; no schema redesign, no claim-boundary behavior change, no mass migration of unrelated scripts, and no generated artifact commit.
- Next task: `TB-195`

### TB-195: Hazard-Layer Writer And Manifest Module Split

- Date: 2026-05-17
- Commit: local
- Objective: split the lowest-risk hazard-layer writer, manifest-entry, and report-rendering helpers out of `scripts/build_hazard_layers.py` without changing CLI behavior or generated schemas.
- Files changed: `scripts/build_hazard_layers.py`, `scripts/hazard_output_writers.py`, `scripts/hazard_output_manifests.py`, `scripts/hazard_output_reports.py`, `tests/test_hazard_output_helpers.py`, `docs/hazard_output_profile_contract.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added focused helper modules for shared file/checksum accounting, compact manifest-entry helpers, and HTML report rendering.
  - Updated the hazard builder to delegate those responsibilities while leaving reducer math, raster writers, probability normalization, output-profile defaults, and GIS/COG semantics unchanged.
  - Added direct helper tests for writer metadata/checksums, manifest metadata precedence and fallback hashing, and report rendering output accounting.
  - Documented the next safe split target as the remaining raster writer family, explicitly bounded to behavior-preserving extraction only.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/build_hazard_layers.py scripts/hazard_output_writers.py scripts/hazard_output_manifests.py scripts/hazard_output_reports.py tests/test_hazard_output_helpers.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_output_helpers`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_layers.HazardLayerTests.test_fixture_layers_are_reproducible_and_interpretable tests.test_hazard_layers.HazardLayerTests.test_default_grid_csv_export_is_enabled tests.test_hazard_layers.HazardLayerTests.test_hazard_manifest_includes_terrain_metadata_sidecar_provenance tests.test_hazard_layers.HazardLayerTests.test_pilot_gis_package_manifest_records_review_artifacts_and_boundaries`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_layers tests.test_hazard_output_helpers`
- Result/status: implemented_measured
- Boundaries: no reducer redesign, no probability-semantics change, no output-profile default change, no large fixture regeneration, and no GIS/COG claim upgrade.
- Next task: `TB-196`

### TB-196: Explicit Missing-Data Validity Semantics In Validation Metrics

- Date: 2026-05-18
- Commit: local
- Objective: replace silent empty-input and malformed-summary fallbacks in validation metrics with explicit warnings and validity flags so missing evidence is not mistaken for a real zero-valued result.
- Files changed: `src/manifest.rs`, `src/validation.rs`, `src/validation/metric_math.rs`, `src/validation/metrics.rs`, `src/validation/runner.rs`, `tests/config_io_terrain.rs`, `docs/validation_data_schema.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a warning path for missing observed deposition inputs so empty deposition sidecars no longer produce silent metric omissions.
  - Added a validity flag and error note to the stop-state summary manifest, and changed stop-state count-map aggregation to report malformed JSON instead of collapsing it into an empty aggregate.
  - Added focused regression tests for legitimate zero-valued metric handling, empty deposition-observation warnings, malformed stop-state count-map parsing, and existing observed-data validation flows.
  - Documented how consumers should interpret omitted metrics and invalid summary fields.
- Checks run:
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test cloud_metrics_handle_empty_and_symmetric_nearest_cases`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test stop_state_summary_marks_malformed_count_maps_invalid`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain validation_warns_when_deposition_observations_are_missing -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain validation_compares_observed_trajectory_shape_and_energy -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain swissalti3d_terrain_class_pilot_writes_class_manifest -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test validation_reports_raw_and_significant_impact_counts_separately`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no metric retuning, no benchmark reinterpretation, no default physics change, and no broad validation-file refactor beyond the affected paths.
- Next task: `TB-197`

### TB-197: Python Execution Policy Normalization

- Date: 2026-05-18
- Commit: local
- Objective: normalize local Python and PyYAML guidance around the repository `uv` workflow while keeping CI support for `requirements-tools.txt`.
- Files changed: `README.md`, `docs/onboarding.md`, `scripts/check_repo_consistency.py`, PyYAML-dependent scripts under `scripts/`, `tests/test_repo_consistency_claim_hygiene.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Updated PyYAML dependency failures to point users at `PYENV_VERSION=system uv run python ...` and identify the CI `requirements-tools.txt` exception instead of recommending global pip installs.
  - Clarified the local-vs-CI Python policy in README and onboarding docs without changing dependency versions or CI installation behavior.
  - Added a repository-consistency check and focused regression test that reject restored global `python`/`python3 -m pip install PyYAML` guidance in Python scripts.
  - Confirmed `pyproject.toml` and `requirements-tools.txt` remain the synchronized dependency sources checked by repo consistency.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile $(git diff --name-only | rg '\.py$')`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_repo_consistency_claim_hygiene.HazardClaimHygieneTests.test_python_tool_dependency_metadata_is_consistent tests.test_repo_consistency_claim_hygiene.HazardClaimHygieneTests.test_python_execution_policy_guidance_is_clean`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no dependency upgrade, no removal of CI support for `requirements-tools.txt`, no environment installation, and no behavior change beyond dependency guidance and consistency enforcement.
- Next task: `TB-198`

### TB-198: Calibration Script Failure Diagnostics

- Date: 2026-05-18
- Commit: `0940321`
- Objective: harden calibration scripts so expected missing or empty inputs fail with stage-scoped diagnostics instead of index errors or opaque subprocess failures.
- Files changed: `calibration/README.md`, `scripts/run_tschamut_calibration.py`, `scripts/calibrate_scarring_impact.py`, `scripts/preprocess_scarring_real_data.py`, `tests/test_calibration_failure_diagnostics.py`
- Implementation summary:
  - Added explicit checks for empty calibration splits, empty parameter grids, missing split/deposition rows, missing significant impact events, and failed `cargo run` subprocesses.
  - Added temporary-fixture unit tests covering Tschamut calibration, scarring calibration, and scarring real-data preprocessing failure paths.
  - Updated the calibration README to keep these scripts classified as research diagnostics, not accepted calibration or physical-credibility evidence.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_calibration_failure_diagnostics`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/run_tschamut_calibration.py scripts/calibrate_scarring_impact.py scripts/preprocess_scarring_real_data.py tests/test_calibration_failure_diagnostics.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no calibration run, no parameter selection change, no accepted calibration evidence, no model default change, and no annual/physical probability claim.
- Next task: `TB-199`

### TB-199: Runtime-Facing Panic Path Reduction

- Date: 2026-05-18
- Commit: `8a7b2fa`
- Objective: convert the highest-risk runtime-adjacent DEM and validation panic paths into structured errors while leaving compatibility/test wrappers bounded.
- Files changed: `src/terrain.rs`, `src/validation.rs`, `src/validation/runner.rs`
- Implementation summary:
  - Propagated DEM query failures through `ValidationError::Terrain` in observed-trajectory validation metrics instead of relying on panic-prone height access.
  - Changed shape-manifest assembly to return `ValidationError::Case` for missing block radius instead of panicking during run-manifest construction.
  - Added focused Rust tests for structured validation errors on malformed/out-of-bounds DEM queries and shape sidecar radius requirements.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `cargo test --lib observed_trajectory_metrics_propagate_dem_query_errors`
  - `cargo test --lib shape_metadata_manifest_returns_case_error_when_block_radius_missing`
  - `cargo test --test terrain_edge_cases dem_try_height_returns_out_of_bounds_for_query_outside_grid`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no physics change, no public runtime promotion of `shape_contact_v0`, no sweeping refactor of all `expect` calls, and no change to analytic-test convenience behavior.
- Next task: `TB-200`

### TB-200: GitHub Python Test Clean-Checkout Stabilization

- Date: 2026-05-18
- Commit: `89181ac`
- Objective: Make the Python planning and evidence helpers return explicit blocked or fixture-backed metadata when ignored same-scale, Balfrin, or second-site artifacts are absent in clean-checkout runs.
- Files changed: `scripts/check_hazard_rebuild_output_profile.py`, `scripts/plan_balfrin_single_release_zone_case_dry_run.py`, `tests/test_balfrin_single_release_zone_case_plan_dry_run.py`, `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`, `tests/test_hazard_rebuild_output_profile.py`, `tests/test_pilot_command_plan.py`
- Implementation summary:
  - Surfaced `blocked_missing_inputs` at the hazard-rebuild output-profile top level when any default profile manifest/root is missing, so the command plan no longer implies measured scope on a clean checkout.
  - Added a structured blocked report path to the Balfrin dry-run planner and covered it with a JSON CLI test that exercises missing committed inputs.
  - Staged a minimal AOI tile catalog in the Chant Sura test fixture, added a `/tmp` repo-root ready-path test, and added a blocked-missing-input CLI test for the same helper.
  - Extended the output-profile and command-plan tests so missing manifests stay explicit and bounded instead of silently inheriting measured metadata.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_pilot_command_plan tests.test_swiss_wide_execution_envelope tests.test_balfrin_single_release_zone_case_plan_dry_run tests.test_chant_sura_fluelapass_dry_run_case_skeleton tests.test_hazard_rebuild_output_profile`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no public-data download, no generated ignored-artifact commit, no fabricated measured evidence, no Balfrin access requirement, and no scale-up or operational claim.
- Next task: `TB-201`

### TB-201: Ignored-Artifact Dependency Audit For Python Tests

- Date: 2026-05-18
- Commit: `caf3902`
- Objective: add a repository-consistency audit that catches Python tests which hard-read ignored artifact roots without using committed fixtures, temporary fixtures, or explicit blocked-state expectations.
- Files changed: `scripts/check_repo_consistency.py`, `tests/test_repo_consistency_claim_hygiene.py`, `tests/test_balfrin_target_area_scenario_tables.py`, `tests/test_swiss_wide_execution_envelope.py`, `tests/test_tschamut_block_scenario_table_generation.py`, `tests/fixtures/tschamut_public_input/release_points_lv95.csv`, `tests/fixtures/tschamut_public_input/tschamut_public_scenario_table_v1.csv`, `tests/fixtures/tschamut_public_input/tschamut_public_source_zone_metadata_v1.yaml`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added ignored-artifact dependency classification to repository consistency, including violations for new hard reads from `hazard/results`, `validation/private`, `data/processed/swisstopo`, and `/scratch` paths.
  - Added regression coverage for current classifications, hard-read rejection, and accepted temporary/tracked-fixture reads.
  - Moved scenario-table tests away from ignored Tschamut input roots by adding tracked fixture inputs under `tests/fixtures/tschamut_public_input`.
  - Reworked the Swiss-wide execution envelope smoke test to use mocked measured evidence rather than live local ignored artifacts.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene tests.test_balfrin_target_area_scenario_tables tests.test_tschamut_block_scenario_table_generation tests.test_swiss_wide_execution_envelope`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no broad test rewrite, no deletion of local artifacts, no generated fixtures outside `tests/fixtures`, no scientific evidence reclassification, and no scale-up or operational claim.
- Next task: `TB-202`

### TB-202: CI Git History And Output-Root Portability Guard

- Date: 2026-05-18
- Commit: `4806402`
- Objective: Harden the Python CI path so work-log ancestry checks stay deterministic in full-history clones and Chant Sura dry-run output-root validation stays repo-aware when repositories live under `/tmp`.
- Files changed: `.github/workflows/ci.yml`, `docs/task_backlog.md`, `docs/agent_work_log.md`, `scripts/check_repo_consistency.py`, `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`, `tests/test_repo_consistency_claim_hygiene.py`, `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`
- Implementation summary:
  - Set the Python workflow checkout to `fetch-depth: 0` so repository-consistency ancestry checks have full history in CI.
  - Added shallow-clone detection to the work-log hygiene path and a regression test that simulates shallow history.
  - Tightened the Chant Sura dry-run output-root guard to reject repo-local paths even when the repository root itself is under `/tmp`, while still allowing `/tmp` scratch roots and the ignored validation root.
  - Added focused tests for allowed scratch roots, allowed ignored roots, and forbidden repository-local paths.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_repo_consistency_claim_hygiene tests.test_chant_sura_fluelapass_dry_run_case_skeleton`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no work-log history changes, no weakening of full-history hygiene, no generated artifact commit, and no expansion of allowed output roots beyond documented scratch/ignored locations.
- Next task: backlog refill needed

### TB-203: Balfrin Next Live-Run Decision Gate

- Date: 2026-05-18
- Commit: `bd6f284`
- Objective: add a deterministic decision gate that compares the metrics-completion rerun, smallest bounded multi-zone probe, and deferral options for the next authorized live Balfrin action.
- Files changed: `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `tests/test_balfrin_next_live_run_decision_gate.py`, `tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json`, `tests/fixtures/balfrin_next_live_run_decision_gate/blocked_bundle.json`, `tests/fixtures/balfrin_next_live_run_decision_gate/defer_bundle.json`, `docs/script_inventory.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a deterministic Balfrin next-live-run decision helper that synthesizes the target-area metrics report, preservation gate, reducer-pressure probe, and multi-zone handoff evidence into a ready / blocked / defer recommendation.
  - Encoded explicit criteria for missing target-area metrics, preservation-gate readiness, reducer pressure, multi-zone package readiness, expected runtime/output pressure, and scientific value, with exact evidence blockers preserved in the report.
  - Added compact fixture-backed tests for the ready metrics-completion rerun path, a fail-closed missing-inputs path, and a defer-to-portability-or-physical-evidence path.
  - Registered the new helper in the script inventory and removed TB-203 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_next_live_run_decision_gate tests.test_balfrin_probe_metrics_report tests.test_balfrin_probe_preservation_gate tests.test_multi_zone_reducer_pressure tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_next_live_run_decision_gate.py tests/test_balfrin_next_live_run_decision_gate.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin submission, no scale-up authorization, no distributed execution, no operational claim, and no fabricated metrics.
- Next task: `TB-204`

### TB-204: Enforce Multi-Zone Output And Reducer Constraints In Handoff

- Date: 2026-05-18
- Commit: `5b53baf`
- Objective: thread measured multi-zone reducer-pressure constraints into the Balfrin multi-release-zone handoff generator so oversized or unsafe dry-run packages fail closed.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `scripts/summarize_multi_zone_reducer_pressure.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_multi_zone_reducer_pressure.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a measured multi-zone pressure source to the handoff generator so the scratch probe root, probe document, measurement command, manifest size, file counts, and per-family byte totals are recorded as the constraint source.
  - Threaded a deterministic constraint gate through the package report, command plan, and SBATCH notes, with fail-closed `acceptable` / `warning` / `blocked` classifications for requested release-zone batch size, reducer chunk count, and reducer worker count.
  - Added focused regressions for the measured constraint source, the acceptable/warning/blocked classification cases, and the blocked CLI path that exits non-zero for oversized requests without submitting any job.
  - Extended the probe summary with an explicit measured-constraint bundle, then removed TB-204 from the active backlog once the implementation and focused tests were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_reducer_pressure.py scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_multi_zone_reducer_pressure.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_multi_zone_reducer_pressure tests.test_balfrin_multi_release_zone_demo_handoff`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin job, no distributed reducer, no MPI/GPU, no physics change, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-205`

### TB-205: Smallest Bounded Multi-Zone Balfrin Probe Package

- Date: 2026-05-18
- Commit: `68e6cc6`
- Objective: produce the smallest reviewable multi-zone Balfrin probe package that stays bounded by measured reducer and preservation constraints and remains blocked pending later authorization.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added smallest-reviewable multi-zone follow-up metadata to the Balfrin handoff generator, including exact release-zone count, scenario count, trajectory target, deterministic seed policy, command-plan entries, SBATCH details, output roots, and preservation-gate checklist.
  - Wired the package to emit a blocked-pending-authorization classification plus the exact later review command, and made the text renderer show the blocked classification explicitly.
  - Added focused regressions for deterministic package shape, command-plan coverage, blocked missing-input handling, and the later review-command path.
  - Removed TB-205 from the active backlog once the implementation was committed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin submission, no scale-up authorization, no distributed execution, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-206`

### TB-206: Target-Area Metrics Completion Rerun Package

- Date: 2026-05-18
- Commit: `62126c5`
- Objective: prepare a bounded Balfrin rerun package whose only purpose is closing the missing target-area peak-memory and split validation/hazard output metrics.
- Files changed: `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`, `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated dry-run rerun-package helper that emits the rerun command plan, SBATCH package text, preservation checklist, replay metadata, comparison basis, and hashes for the recorded target-area run.
  - Kept the preservation checklist fail-closed around the missing peak-memory and split validation/hazard output metrics, plus the declared run-root files and replay metadata fields needed to preserve the package.
  - Added focused tests for the complete, partial, and missing-package classifications, along with a CLI artifact smoke test.
  - Registered the new helper in the script inventory, documented it in the Balfrin SLURM / single-job notes, and removed TB-206 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py tests/test_balfrin_target_area_metrics_completion_rerun_package.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_balfrin_target_area_metrics_completion_rerun_package tests.test_balfrin_probe_metrics_report tests.test_balfrin_probe_preservation_gate`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin submission, no new scientific interpretation, no scale-up authorization, no operational claim, and no fabricated metrics.
- Next task: `TB-207`

### TB-207: Real Chant Sura Public-Context Staging Verification

- Date: 2026-05-18
- Commit: `fa191b8`
- Objective: verify real staged Chant Sura / Flüelapass public-context inputs when present while keeping clean-checkout and fixture-backed states deterministic and fail-closed.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `scripts/plan_terrain_release_zone_candidates.py`, `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a real-context product-readiness matrix to the Chant Sura gate so AOI catalog, terrain, source-zone, scenario, policy, and public-context rows are classified as `ready`, `missing`, `deferred`, or `metadata_mismatch` with exact paths and required fields.
  - Reworked the Chant Sura staging checklist to derive from the new matrix, tightened the gate so staged checksum or metadata failures fail closed, and preserved deterministic deferred behavior when the cache manifest is absent.
  - Threaded the new readiness summary into the Chant Sura dry-run report and removed the NaN-driven nondeterminism in the candidate-sensitivity summary so repeated dry-runs compare cleanly.
  - Added focused tests for clean-checkout blocked, fixture-backed deferred, staged partial mismatch, and staged-ready paths, then removed TB-207 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate tests.test_chant_sura_fluelapass_workflow_dry_run_report tests.test_public_geodata_cache_verifier`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_aoi_to_prepared_pilot_dry_run`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, and no physical validation claim.
- Next task: `TB-208`

### TB-208: Independent Physical Evidence Intake Pilot

- Date: 2026-05-18
- Commit: `7f6f4c5`
- Objective: populate a fail-closed observed runout/deposition intake contract with explicit manifest, observed-geometry/provenance, uncertainty, dataset-role, and physical-credibility-gap reporting while keeping calibration and validation separate.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added an explicit benchmark intake manifest alongside the existing contract, including observed geometry fields, provenance fields, uncertainty fields, objective-function readiness, and calibration/validation separation.
  - Expanded the dataset-role classification to cover observed runout/deposition, release-zone provenance, block-population evidence, calibration inputs, validation inputs, and holdout data, then threaded that shape into the blocked report and readable text output.
  - Surfaced the physical-credibility gap update from the shared evidence-requirements helper so the intake report stays pinned to `not_established` unless real accepted evidence is staged.
  - Added focused tests for the accepted fixture shape, the blocked acquisition report, and claim-boundary hygiene, then removed TB-208 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract`
  - `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json >/tmp/tb208_observed_contract.json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_physical_credibility_evidence_requirements`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no calibration, no parameter fitting, no validation-status upgrade without real evidence, no annual-frequency or physical-probability claim, and no operational claim.
- Next task: `TB-209`

### TB-209: Multi-Zone Hazard Builder Throughput Profile

- Date: 2026-05-18
- Commit: `5e59c0e`
- Objective: profile hazard-layer post-processing on a deterministic multi-zone scratch fixture and identify the first concrete throughput or output-pressure bottleneck.
- Files changed: `scripts/summarize_multi_zone_hazard_throughput_profile.py`, `tests/test_multi_zone_hazard_throughput_profile.py`, `docs/hazard_throughput_bottleneck_report.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated deterministic profiling helper that materializes a synthetic 12-zone hazard corpus, runs `scripts/build_hazard_layers.py` with explicit-grid and reduced-output controls, and records read, accumulation, reducer-merge, manifest, raster-write, and report-rendering timings.
  - Captured output-pressure summaries by layer family, file family, manifest family, and a default not-applicable COG/GIS family so the profile stays explicit about what is and is not being measured.
  - Added focused tests for fixture determinism, report schema/pressure shape, CLI JSON output, and blocked-missing-input behavior.
  - Updated the hazard throughput report, script inventory, and active backlog to reflect the new helper and the measured accumulation-dominant bottleneck.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_hazard_throughput_profile -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb209_multi_zone_profile --format json >/tmp/tb209_multi_zone_profile.json`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_hazard_throughput_profile.py tests/test_multi_zone_hazard_throughput_profile.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: profiling only; no hazard-value rewrite, no probability-semantics change, no GIS/COG claim upgrade, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-210`

### TB-210: Full-Scale Balfrin Demonstration Readiness Matrix

- Date: 2026-05-18
- Commit: `c540679`
- Objective: define a deterministic Balfrin readiness matrix that separates measured, fixture-backed, dry-run, blocked, unavailable, and unauthorized evidence before anyone treats "full-scale" as a maturity label.
- Files changed: `scripts/summarize_balfrin_management_demo_package.py`, `tests/test_balfrin_management_demo_package.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a `readiness_matrix` section to the Balfrin management package with rows for measured multi-zone execution, preservation gate, reducer constraints, output budget, restart/replay, GIS package scope, command-plan reproducibility, clean-checkout behavior, scientific claim boundaries, and live authorization.
  - Threaded the matrix through the report renderer and recorded a metrics-completion next milestone from the existing next-live-run decision helper, while keeping the package claim boundaries false.
  - Added focused tests that require the matrix rows, the clean-checkout blocked path, the next-milestone recommendation, and the disallowed claim-boundary language to stay explicit.
  - Removed TB-210 from the active backlog after the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_management_demo_package.py tests/test_balfrin_management_demo_package.py`
- Result/status: implemented_measured
- Boundaries: no live execution, no claim upgrade, no operational or annual-frequency semantics, and no fabricated full-scale evidence.
- Next task: `TB-211`

### TB-211: Authorization-Gated Multi-Zone Balfrin Execution

- Date: 2026-05-18
- Commit: `d8a8580`
- Objective: add a fail-closed multi-zone Balfrin execution path that requires a reviewed handoff package and live-run authorization record before submission, and classify measured versus incomplete run-root evidence without silently promoting partial runs.
- Files changed: `scripts/submit_balfrin_probe.py`, `scripts/collect_balfrin_probe_metrics.py`, `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_authorized_multi_zone_submit.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a dedicated `--authorized-submit` mode to `scripts/submit_balfrin_probe.py` that refuses to submit unless a reviewed handoff package and live-run authorization record are both provided and validated, and writes a deterministic blocked report when either gate is missing.
  - Extended the Balfrin collector with `run_root_status`, checksum summaries, manifest/reducer/restart-replay subreports, and failure-behavior classification so complete fixture roots are distinguishable from incomplete roots.
  - Updated the multi-zone handoff generator and driver docs to advertise the explicit reviewed-package and authorization-record submit command, then removed TB-211 from the active backlog.
  - Added focused tests for authorized fixture execution metadata, blocked-missing-authorization, blocked-missing-input, and incomplete-run-root classifications, plus a regression for the updated multi-zone handoff command shape.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_authorized_multi_zone_submit tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_probe_driver -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/submit_balfrin_probe.py scripts/collect_balfrin_probe_metrics.py scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_authorized_multi_zone_submit.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no live execution, no operational claim, no distributed execution, no annual-frequency or physical-probability semantics, and no fabricated metrics.
- Next task: `TB-212`

### TB-212: Real Second-Site Prepared-Pilot Dry Run

- Date: 2026-05-18
- Commit: `dfda69b`
- Objective: compose a deterministic Chant Sura / Fluelapass prepared-pilot dry run that stays fail-closed when required real staged inputs are missing or fixture-backed.
- Files changed: `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added provenance-aware reporting that separates `real_staged` from `fixture_backed` prepared-pilot inputs and classifies the workflow as `blocked_fixture_backed_inputs` when staged paths exist but the public-context contract is still synthetic.
  - Threaded the provenance and blocked-input summaries into the rendered report, ready-for-next-step output, and tiny bounded ensemble handoff so the dry-run path preserves real-versus-fixture boundaries.
  - Added focused regressions for clean-checkout blocked behavior, fixture-backed fail-closed behavior, staged-real-like ready behavior, and forbidden output-root writes.
  - Removed TB-212 from the active backlog after the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_chant_sura_fluelapass_dry_run_report.py tests/test_chant_sura_fluelapass_workflow_dry_run_report.py tests/test_aoi_to_prepared_pilot_dry_run.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_chant_sura_fluelapass_workflow_dry_run_report tests.test_aoi_to_prepared_pilot_dry_run`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no downloads, no ensemble execution without explicit authorization, no synthetic public-context evidence, no physical-validation claim, no operational claim, and no readiness claim when required real inputs are absent.
- Next task: `TB-213`

### TB-213: Evidence-Gated Balfrin Demonstration Closure Package

- Date: 2026-05-18
- Commit: `83fc07e`
- Objective: produce a deterministic Balfrin closure package that answers the demonstration-readiness question while failing closed unless new preservation-checked measured evidence is present.
- Files changed: `scripts/summarize_balfrin_demonstration_closure_package.py`, `tests/test_balfrin_demonstration_closure_package.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated closure-package helper that composes the current management evidence with the metrics-completion rerun package, the multi-zone handoff, and the preservation gate, while classifying provenance across measured, fixture-backed, dry-run, blocked, unavailable, unauthorized, and historical evidence.
  - Implemented a fail-closed `blocked_no_new_measured_evidence` path, a mixed-provenance warning, and a complete-measured path that can upgrade maturity labels only when all sections are explicitly measured.
  - Added focused tests for the blocked-no-new-evidence, mixed-provenance, complete-measured, and CLI artifact-materialization paths, then updated the Balfrin documentation and script inventory to point reviewers at the new helper.
  - Removed TB-213 from the active backlog after the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_demonstration_closure_package.py tests/test_balfrin_demonstration_closure_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_demonstration_closure_package -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: implemented_blocked_report
- Boundaries: no live execution, no operational claim, no annual-frequency or risk semantics, no maturity upgrade without new preservation-checked measured evidence, and no replacement of the authoritative backlog or work log.
- Next task: `TB-214`
