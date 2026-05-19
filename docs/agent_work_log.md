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
  `docs/archive/agent_work_log_archive.md`. If a user explicitly requests a
  non-TB guidance-cleanup work-log note, keep it in the compact guidance-notes
  section and do not format it as a `TB-XXX` entry.
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
- TB-181 through TB-238: retained below as the active recent execution history.

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

### TB-214: Workflow-Shell Coupling Inventory

- Date: 2026-05-18
- Commit: `d7915d1`
- Objective: build an executable inventory that classifies implicit workflow-shell coupling across tracked scripts, command-plan strings, ignored-root assumptions, generated report dependencies, and duplicated status vocabularies.
- Files changed: `scripts/inventory_workflow_shell_coupling.py`, `tests/test_workflow_shell_coupling_inventory.py`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a deterministic `scripts/inventory_workflow_shell_coupling.py` helper that scans tracked text files, surfaces dynamic import-by-path usage, command-plan script references, ignored-root assumptions, generated report dependencies, and duplicated status values, and ranks the resulting coupling families by severity.
  - Encoded a prioritized extraction shortlist that keeps follow-up work bounded to shared loader, ignored-root, and status-vocabulary helpers rather than a broad rewrite.
  - Added a fixture-backed regression that proves the inventory catches both a stale script reference and an ignored-root-only dependency without touching real ignored artifacts.
  - Registered the new helper in `docs/script_inventory.md` and removed TB-214 from the active backlog before the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/inventory_workflow_shell_coupling.py tests/test_workflow_shell_coupling_inventory.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_workflow_shell_coupling_inventory tests.test_repo_consistency_claim_hygiene -v`
  - `PYENV_VERSION=system uv run python scripts/inventory_workflow_shell_coupling.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: inventory and prioritization only, no broad script moves, no deletion campaign, no new evidence package, and no live command behavior changes.
- Next task: `TB-215`

### TB-215: Workflow Utility Migration Batch For Status And Provenance

- Date: 2026-05-18
- Commit: `d742f64`
- Objective: migrate a bounded set of high-churn validators and summarizers onto shared status, checksum, manifest, blocked-report, and claim-boundary helpers.
- Files changed: `scripts/lib/workflow_validation.py`, `scripts/validate_output_budget_reducer_gate.py`, `scripts/validate_public_real_site_conditional_pilot_run.py`, `scripts/map_physical_credibility_evidence_requirements.py`, `scripts/summarize_observed_runout_deposition_intake_contract.py`, `scripts/assess_validation_calibration_evidence_gaps.py`, `tests/test_workflow_validation_helpers.py`, `docs/decision_log.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added shared helpers for required-path validation, checksum-field validation, and blocked-report construction, and widened the claim-scan helper to ignore explicit negation blocks such as `does_not_verify`.
  - Migrated the output-budget reducer gate and public real-site pilot validator to shared status rendering, false-field checks, checksum validation, and claim-boundary scanning while keeping their public outputs and selected status vocabulary stable.
  - Migrated the physical-credibility mapper, observed-runout intake summarizer, and validation-gap report builder to the shared blocked-report, false-field, path-check, and scan helpers, preserving their JSON/text schemas and blocked-state semantics.
  - Added focused helper tests plus downstream regressions that cover checksum handling, required-path checks, blocked-report construction, and the preserved public status vocabulary.
  - Removed TB-215 from the active backlog and added a compatibility note in the decision log so downstream report labels stay stable while mechanics move into the shared helper layer.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/lib/workflow_validation.py scripts/validate_output_budget_reducer_gate.py scripts/validate_public_real_site_conditional_pilot_run.py scripts/map_physical_credibility_evidence_requirements.py scripts/summarize_observed_runout_deposition_intake_contract.py scripts/assess_validation_calibration_evidence_gaps.py tests/test_workflow_validation_helpers.py tests/test_output_budget_reducer_gate.py tests/test_public_real_site_conditional_pilot_run.py tests/test_physical_credibility_evidence_requirements.py tests/test_observed_runout_deposition_intake_contract.py tests/test_validation_calibration_evidence_gaps.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_workflow_validation_helpers tests.test_output_budget_reducer_gate tests.test_public_real_site_conditional_pilot_run tests.test_physical_credibility_evidence_requirements tests.test_observed_runout_deposition_intake_contract tests.test_validation_calibration_evidence_gaps`
  - `git diff --check`
- Result/status: implemented_fixture_backed
- Boundaries: bounded helper migration only, no domain-schema collapse, no broad packaging rewrite, no claim upgrade, and no unrelated validator churn.
- Next task: `TB-216`

### TB-216: Repository Consistency Checker Responsibility Split

- Date: 2026-05-18
- Commit: `673ae32`
- Objective: split the backlog/work-log and claim hygiene responsibilities out of `scripts/check_repo_consistency.py` into importable modules while preserving the CLI contract.
- Files changed: `scripts/check_repo_consistency.py`, `scripts/lib/repo_consistency_backlog.py`, `scripts/lib/repo_consistency_claims.py`, `tests/test_repo_consistency_claim_hygiene.py`, `tests/test_repo_consistency_module_split.py`, `docs/task_backlog.md`
- Implementation summary:
  - Moved the backlog/work-log hygiene family into `scripts/lib/repo_consistency_backlog.py`, including the inspect-first resolver, TB heading parsing, work-log commit checks, and shallow-history guard, then re-exported those helpers through the entrypoint.
  - Moved the hazard claim/status hygiene family into `scripts/lib/repo_consistency_claims.py` so the CLI keeps the same pass/fail behavior while the claim-family scanner is importable and testable on its own.
  - Added focused clean-failure fixture tests for both extracted families plus CLI-level exit-code smoke tests that patch the split checks through `main()`, and updated the existing shallow-history test to patch the extracted backlog module.
  - Removed TB-216 from the active backlog before the implementation commit and kept the entrypoint focused on orchestration plus the remaining cross-document guards.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_repo_consistency.py scripts/lib/repo_consistency_backlog.py scripts/lib/repo_consistency_claims.py tests/test_repo_consistency_module_split.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene tests.test_repo_consistency_module_split -v`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `git diff --check`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: refactor only, no new broad policy checks, no backlog edits beyond task completion, no generated evidence claims, and no unrelated script cleanup.
- Next task: `TB-217`

### TB-217: Scalable Command-Plan Output Profile Enforcement

- Date: 2026-05-18
- Commit: `35bfeeb`
- Objective: enforce scalable output defaults in the pilot and Balfrin command-plan helpers so summary-only conditional curves and `--grid-csv-export none` are the recorded default unless an explicit heavy-debug override is present.
- Files changed: `scripts/lib/output_profile_policy.py`, `scripts/generate_pilot_command_plan.py`, `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_pilot_command_plan.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/hazard_output_profile_contract.md`, `docs/output_budget_reducer_scaling_gate.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a shared three-state output-profile policy helper that classifies command plans as `scalable_default`, `explicit_heavy_debug`, or `blocked_unscalable_default` from the control triple only.
  - Threaded the policy into the pilot command plan and Balfrin handoff generators so hazard-build and follow-up outputs record scalable defaults explicitly, while the Balfrin package surfaces the current target-gate profile as blocked until the recorded grid CSV mode is suppressed.
  - Added focused tests for scalable defaults, explicit heavy-debug override, and the blocked multi-zone/Balfrin plan path, then documented the command-plan contract in the hazard output profile and output-budget gate notes.
  - Removed TB-217 from the active backlog before the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/lib/output_profile_policy.py scripts/generate_pilot_command_plan.py scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_pilot_command_plan.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_pilot_command_plan tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: output-profile policy only, no live execution, no distributed reducer, no hazard-value changes, no COG/GIS claim upgrade, and no generated heavy outputs committed.
- Next task: `TB-218`

### TB-218: Reducer Manifest And File-Family Budget Regression Gate

- Date: 2026-05-18
- Commit: `a824264`
- Objective: add a fixture-backed regression gate that measures reducer manifest bytes, output-family counts, output bytes, sidecar counts, and deterministic merge order for realistic multi-zone scratch roots.
- Files changed: `scripts/summarize_multi_zone_reducer_pressure.py`, `scripts/validate_multi_zone_reducer_pressure_gate.py`, `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_multi_zone_reducer_pressure.py`, `tests/test_multi_zone_reducer_pressure_gate.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/output_budget_reducer_scaling_gate.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the deterministic multi-zone reducer probe to accept a configurable output-family mix, record reducer-manifest bytes plus sidecar and primary-output budgets, and keep the measured merge-order data explicit in both the report and the command-plan provenance.
  - Added a new fixture-backed regression gate that materializes ready, warning, and blocked scratch fixtures, derives its thresholds from deterministic 9-zone and 11-zone profiles, and fails closed on manifest, file-family, byte, sidecar, wall-time, or merge-order regressions.
  - Surfaced the new pressure fields through the Balfrin multi-zone handoff summary, refreshed the reducer-pressure notes, and registered the new validator in the script inventory.
  - Added focused regressions for configurable family mixes, gate-ready and gate-warning profiles, and merge-order corruption so the gate does not rely on live Balfrin artifacts.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_reducer_pressure.py scripts/validate_multi_zone_reducer_pressure_gate.py scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_multi_zone_reducer_pressure.py tests/test_multi_zone_reducer_pressure_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_reducer_pressure tests.test_multi_zone_reducer_pressure_gate -v`
- Result/status: implemented_fixture_backed
- Boundaries: fixture-backed regression gate only, no live Balfrin job, no distributed reducer, no Swiss-wide projection claim, and no generated heavy outputs committed.
- Next task: `TB-219`

### TB-219: Hazard Accumulation Throughput Hotspot Isolation

- Date: 2026-05-18
- Commit: `0007b37`
- Objective: isolate the remaining Python hazard-accumulation hotspot after explicit-grid improvements and define one bounded optimization target.
- Files changed: `scripts/summarize_multi_zone_hazard_throughput_profile.py`, `tests/test_multi_zone_hazard_throughput_profile.py`, `docs/hazard_throughput_bottleneck_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the fixture-backed throughput profiler with smoke and representative presets, explicit-grid and auto-grid runs, and phase timing fields that separate trajectory reading, bounds discovery, accumulation, reducer merge, raster write, manifest write, and report rendering.
  - Added a smoke semantic guardrail that compares profiled and control hazard-layer signatures plus path-free manifest semantics, so the profiling path does not change hazard values or output meaning.
  - Confirmed the representative multi-zone fixture still points to trajectory accumulation as the dominant explicit-grid phase and recorded a bounded next target: batch or vectorize trajectory-cell updates inside the existing accumulator.
  - Updated the throughput report with the measured representative profile and removed TB-219 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_hazard_throughput_profile.py tests/test_multi_zone_hazard_throughput_profile.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_hazard_throughput_profile -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb219_multi_zone_profile --profile multi_zone --format json > /tmp/tb219_multi_zone_profile.json`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb219_smoke_profile --profile smoke --format json > /tmp/tb219_smoke_profile.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: profiling and target selection only, no hazard semantics or physics change, no heavy outputs committed, and no distributed or operational claims introduced.
- Next task: `TB-220`

### TB-220: Release-Zone And Scenario Physical-Meaning Firewall

- Date: 2026-05-18
- Commit: `1204948`
- Objective: add an explicit interpretation firewall that prevents workflow-generated release candidates, scenario tables, and sampling weights from being represented as field-supported source probabilities.
- Files changed: `docs/current_maturity_snapshot.md`, `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/task_backlog.md`, `scripts/assess_validation_calibration_evidence_gaps.py`, `scripts/generate_candidate_source_zone_scenarios.py`, `scripts/lib/workflow_validation.py`, `scripts/map_physical_credibility_evidence_requirements.py`, `tests/test_candidate_source_zone_scenario_stress.py`, `tests/test_physical_credibility_evidence_requirements.py`, `tests/test_validation_calibration_evidence_gaps.py`
- Implementation summary:
  - Added a shared release-candidate physical-meaning firewall helper that classifies candidate rows as `workflow_generated`, `field_supported`, `mixed_provenance`, or `blocked_missing_provenance` and rejects occurrence-probability, annual-frequency, return-period, and risk language.
  - Threaded the firewall through the candidate scenario generator, the physical-credibility evidence map, and the validation/calibration gap report so release-zone and scenario automation summaries surface the boundary explicitly.
  - Added focused tests for all supported provenance labels, blocked overclaim examples, and report-shape regressions, then updated the maturity snapshot and gate report to mention the new firewall.
  - Removed TB-220 from the active backlog before committing the implementation.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_scenario_stress tests.test_physical_credibility_evidence_requirements tests.test_validation_calibration_evidence_gaps`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: claim-boundary hardening only; no calibration, no annual-frequency semantics, no operational claim, no new physical evidence, and no source-zone heuristic change.
- Next task: `TB-221`

### TB-221: Observed Runout And Deposition Acquisition Blocker Matrix

- Date: 2026-05-18
- Commit: `98fa351`
- Objective: convert the observed runout/deposition intake gap into a machine-readable blocker matrix that separates acquisition, schema repair, and scientific deferral without upgrading the physical-credibility boundary.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a six-row acquisition blocker matrix that records required geometry, provenance, uncertainty, licensing/readiness notes, calibration-versus-validation role, holdout eligibility, and current repository status for observed runout/deposition, release-zone provenance, block-population evidence, calibration inputs, validation inputs, and holdout data.
  - Added a deterministic next-action recommendation plus a blocked no-evidence report that keeps data acquisition distinct from schema repair and scientific deferral when no real observed benchmark package is staged.
  - Added a fixture classifier and focused acceptance tests for complete shape, missing geometry, missing uncertainty, unclear calibration role, and blocked-status overclaiming, then kept the existing non-operational claim boundaries intact.
  - Removed TB-221 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_observed_runout_deposition_intake_contract.py tests/test_observed_runout_deposition_intake_contract.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_physical_credibility_evidence_gaps -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: acquisition planning and acceptance gate only; no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or risk semantics, and no operational claim.
- Next task: backlog refill needed

### TB-222: Balfrin Next Measured Action Decision Refresh

- Date: 2026-05-18
- Commit: `a1f5974`
- Objective: refresh the Balfrin next-action decision matrix using post-TB-221 evidence before any live-run request or optimization task is prepared.
- Files changed: `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `tests/test_balfrin_next_live_run_decision_gate.py`, `tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json`, `tests/fixtures/balfrin_next_live_run_decision_gate/defer_bundle.json`, `docs/task_backlog.md`
- Implementation summary:
  - Extended the deterministic decision helper from the prior three-way gate into a ranked five-action matrix covering metrics completion, smallest multi-zone measurement, second-site progress, physical-evidence acquisition, and hazard-builder optimization.
  - Added explicit path states for measured, fixture-backed, blocked, unavailable, unauthorized, and SSH-access-expired cases, plus per-action claim-upgrade boundaries and exact evidence blockers.
  - Refreshed the default and defer fixtures with TB-217 through TB-221 evidence rows, Balfrin access provenance, second-site blockers, physical-evidence blockers, and hazard optimization fixture-backed status.
  - Added focused tests for the metrics-completion recommendation, multi-zone blockers, SSH-expired fail-closed behavior, and defer-to-portability/physical-evidence branch.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_next_live_run_decision_gate.py tests/test_balfrin_next_live_run_decision_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_next_live_run_decision_gate -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_next_live_run_decision_gate.py --evidence-json tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json --format json > /tmp/tb222_decision_gate.json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_next_live_run_decision_gate tests.test_balfrin_management_demo_package -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: deterministic decision refresh only; no live Balfrin submission, no SSH access claim, no authorization grant, no new maturity label, no fabricated metrics, no scale-up, no distributed-execution claim, no annual-frequency or physical-probability claim, and no operational hazard-map claim.
- Next task: `TB-223`

### TB-223: Balfrin SSH And Remote Artifact Access Preflight

- Date: 2026-05-18
- Commit: `54a9813`
- Objective: add a fail-closed read-only Balfrin preflight that distinguishes SSH expiry, missing remote checkout, missing non-git run root, and scheduler-query blockers before collection work.
- Files changed: `scripts/check_balfrin_remote_access_preflight.py`, `tests/test_balfrin_probe_driver.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `scripts/check_balfrin_remote_access_preflight.py`, a one-command JSON/text helper that checks SSH `BatchMode=yes`, the canonical Balfrin checkout `/users/olifu/work/rust_rockfall`, the preserved target-area run root under `/scratch/mch/olifu/rust_rockfall/probes/.../authorized_tb168_20260517`, and read-only `squeue` reachability.
  - The helper reports `ready_for_read_only_collection`, `blocked_ssh_unavailable`, `blocked_missing_remote_clone`, `blocked_missing_run_root`, or `blocked_scheduler_unavailable`, with exact command arrays and remote commands included in the report.
  - Added mock-backed tests for ready, expired SSH, missing remote clone, missing run-root, and scheduler-unavailable paths, and documented the new preflight command in the Balfrin SLURM driver runbook.
  - Removed TB-223 from the active backlog after implementation.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_balfrin_remote_access_preflight.py tests/test_balfrin_probe_driver.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/balfrin_remote_access_preflight_tb223.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: read-only SSH and remote artifact preflight only; no Balfrin job launch, no remote mutation, no generated remote artifact claim, no operational claim, no scale-up or distributed-execution claim, and no annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-224`

### TB-224: Balfrin Worker Routing In Task Context

- Date: 2026-05-18
- Commit: `09a3e7c`
- Objective: teach the task-context helper to mark Balfrin SSH/live-evidence tasks as requiring a stronger Balfrin-capable worker and the access preflight from TB-223.
- Files changed: `scripts/print_agent_task_context.py`, `tests/test_agent_task_context.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added Balfrin-aware routing metadata to compact task summaries, including `balfrin_access_required`, `recommended_worker_model`, `balfrin_access_preflight_command`, and a short access-expiry note.
  - Added a Balfrin access preflight helper entry and routing keyword detection so compact task context surfaces the stronger-worker recommendation when a task mentions Balfrin SSH, live run, remote run root, or evidence collection.
  - Preserved full-detail helper output while extending the report text renderer to print the routing fields inline for Balfrin tasks.
  - Added focused tests for Balfrin and non-Balfrin tasks, then removed TB-224 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/print_agent_task_context.py tests/test_agent_task_context.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_agent_task_context -v`
- Result/status: implemented_fixture_backed
- Boundaries: helper/context routing only; no live SSH call, no worker launch automation change, no task-priority fields, and no claim upgrade.
- Next task: `TB-225`

### TB-225: Target-Area Metrics Completion Rerun Preflight

- Date: 2026-05-18
- Commit: `fa8d9b2`
- Objective: convert the target-area metrics-completion rerun package into a strict authorization-request preflight that consumes the TB-223 Balfrin access status before any authorization review.
- Files changed: `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`, `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `preflight_status` / `authorization_request_preflight_status` classifications, including `ready_for_authorization_request`, `blocked_missing_run_root`, exact Balfrin access blocker statuses, and `blocked_incomplete_package`.
  - Added a TB-223 access-preflight requirement section, pre-authorization input checks, exact expected metrics, preservation files, comparison basis, and post-run collection commands while keeping authorization and live submission false.
  - Updated the CLI to consume a supplied Balfrin access JSON or run the read-only TB-223 helper, and added focused fixture-backed tests for ready, partial, missing-run-root, and Balfrin-access-blocked paths.
  - Removed TB-225 from the active backlog after implementation.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py tests/test_balfrin_target_area_metrics_completion_rerun_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_completion_rerun_package -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/balfrin_remote_access_preflight_tb225.json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py --artifact-dir /tmp/tb225_metrics_completion_preflight --format json > /tmp/tb225_metrics_completion_preflight.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: authorization-request preflight only; no live Balfrin submission, no authorization grant, no new scientific interpretation, no fabricated metrics, no scale-up or distributed-execution claim, and no operational, annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-226`

### TB-226: Smallest Multi-Zone Probe Authorization Preflight

- Date: 2026-05-18
- Commit: `c26dd4d`
- Objective: turn the smallest bounded multi-zone handoff into a fail-closed authorization preflight that ties reviewed package state, authorization record, Balfrin read-only access, reducer budget, and the submit gate to one exact minimal run shape.
- Files changed: `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `scripts/submit_balfrin_probe.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `tests/test_balfrin_authorized_multi_zone_submit.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a deterministic smallest multi-zone authorization preflight report that records release-zone count, scenario count, trajectory/reducer workers, reducer chunks, reduced-output profile, estimates, preservation checklist, package hashes, authorization-record state, and Balfrin access status.
  - Integrated the preflight into `scripts/submit_balfrin_probe.py --authorized-submit` so missing authorization, invalid package state, expired or unavailable Balfrin access, and reducer-budget blockers return a blocked report before submission artifacts are written or `sbatch` is called.
  - Allowed the authorization record to target the TB-226 preflight path while preserving the older TB-211 authorized-submit compatibility, and documented the new preflight command in the Balfrin SLURM and reducer-pressure docs.
  - Added focused tests for ready package, missing authorization, expired access, and reducer-budget-blocked paths, plus submit-driver coverage using a supplied read-only access preflight JSON.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py scripts/submit_balfrin_probe.py tests/test_balfrin_smallest_multi_zone_authorization_preflight.py tests/test_balfrin_authorized_multi_zone_submit.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_authorized_multi_zone_submit -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/balfrin_remote_access_preflight_tb226.json`
  - `PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --artifact-dir /tmp/rust_rockfall/tb226_smallest_multi_zone_handoff --format json > /tmp/tb226_smallest_multi_zone_handoff.json`
  - `PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --reviewed-handoff-package /tmp/rust_rockfall/tb226_smallest_multi_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /tmp/rust_rockfall/tb226_smallest_multi_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml --balfrin-access-preflight-json /tmp/balfrin_remote_access_preflight_tb226.json --format json > /tmp/tb226_smallest_multi_zone_authorization_preflight.json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_reducer_pressure_gate -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: authorization preflight and submit gate only; no live Balfrin job, no remote mutation, no authorization grant, no scale-up or distributed execution, no operational claim, and no annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-227`

### TB-227: Balfrin Post-Run Evidence Collector Rehearsal

- Date: 2026-05-18
- Commit: `2b78d4b`
- Objective: rehearse Balfrin post-run evidence collection across complete, incomplete, missing-root, SSH-unavailable, and non-git-artifact-unavailable fixture states before any future live run is treated as evidence.
- Files changed: `scripts/rehearse_balfrin_post_run_evidence_collector.py`, `scripts/summarize_balfrin_demonstration_closure_package.py`, `tests/test_balfrin_post_run_evidence_collector_rehearsal.py`, `tests/test_balfrin_demonstration_closure_package.py`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only post-run evidence collector rehearsal helper that runs the existing metrics report and preservation gate over fixture roots and classifies `fixture_backed_complete`, `blocked_incomplete_run_root`, `blocked_missing_run_root`, `blocked_ssh_unavailable`, and `blocked_non_git_artifact_unavailable`.
  - Covered both closure source families, `metrics_completion_rerun` and `authorized_multi_zone_probe`, while keeping fixture-backed complete roots distinct from measured evidence and refusing promotion to closure evidence.
  - Added closure-package input compatibility checks for new measured evidence, including source family, measured provenance, preservation-gate readiness, and authorization status.
  - Added focused tests proving incomplete roots remain blocked and access/artifact blockers preserve exact statuses.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_post_run_evidence_collector_rehearsal tests.test_balfrin_demonstration_closure_package tests.test_balfrin_probe_metrics_report tests.test_balfrin_probe_preservation_gate tests.test_balfrin_authorized_multi_zone_submit`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_post_run_evidence_collector_rehearsal tests.test_balfrin_demonstration_closure_package`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb227_balfrin_preflight.json`
- Result/status: implemented_fixture_backed
- Boundaries: fixture-backed rehearsal and read-only access preflight only; no live Balfrin job, no remote mutation, no generated heavy output, no claim upgrade, no maturity upgrade, no scale-up or distributed execution, and no operational, annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-228`

### TB-228: Multi-Zone Handoff Output Budget Projection

- Date: 2026-05-18
- Commit: `d0c91fc`
- Objective: project reducer manifest, file-family, and output-byte pressure from the actual multi-zone Balfrin handoff command plan instead of relying only on the standalone scratch probe.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a handoff-derived output-budget projection that parses the `multi_zone_reducer_pressure_summary` command, runs the fixture-backed reducer-pressure gate against that command-plan shape, and writes projection JSON/text artifacts under the ignored handoff scratch directory.
  - Exposed the reducer gate vocabulary in the handoff package, including budget checks, family count/byte checks, primary output totals, sidecar totals, reducer-manifest totals, manifest bytes, and first bottleneck labels.
  - Made package constraint status fail closed when the handoff command-plan projection exceeds the current gate, while preserving the separate requested reducer max checks for the smallest submit shape.
  - Documented the distinction between scratch measurement and handoff-derived projection, then removed TB-228 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb228_balfrin_preflight.json`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py scripts/summarize_multi_zone_reducer_pressure.py scripts/validate_multi_zone_reducer_pressure_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_multi_zone_reducer_pressure tests.test_multi_zone_reducer_pressure_gate -v`
  - `PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --artifact-dir /tmp/rust_rockfall/tb228_probe_report --format json > /tmp/tb228_handoff_report.json` (expected fail-closed exit `2`)
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: fixture-backed handoff budget projection only; no live Balfrin job, no remote mutation, no output-default change, no scale-up or distributed-execution authorization, and no operational, annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-229`

### TB-229: Bounded Hazard Accumulator Optimization Spike

- Date: 2026-05-18
- Commit: `2eaa49e`
- Objective: test one bounded trajectory-accumulation optimization slice against the TB-219 hotspot evidence and report whether it should be retained.
- Files changed: `docs/hazard_throughput_bottleneck_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Measured a narrow accumulator experiment that buffered per-trajectory cell maxima before committing them back to the existing grids.
  - Re-ran the representative multi-zone scratch profile and found the patched path slower (`0.070471` s accumulation) than baseline (`0.068822` s accumulation), so the optimization was reverted.
  - Added a no-retain note to the throughput report and removed TB-229 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb229_baseline --format json > /tmp/rust_rockfall/tb229_baseline_profile.json`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb229_after --format json > /tmp/rust_rockfall/tb229_after_profile.json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_hazard_throughput_profile -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: implemented_blocked_report
- Boundaries: no physics change, no hazard semantics change, no output-schema change, no operational claim, and no scale-up or distributed-execution claim.
- Next task: `TB-230`

### TB-230: Post-Optimization Multi-Zone Throughput Reprofile

- Date: 2026-05-18
- Commit: `7cf9f76`
- Objective: reprofile the representative multi-zone hazard-builder fixture after TB-229, compare it with the rejected accumulator spike, and tighten schema-stability coverage for the profiler report.
- Files changed: `docs/hazard_throughput_bottleneck_report.md`, `tests/test_multi_zone_hazard_throughput_profile.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Reprofiled the smoke and representative multi-zone scratch fixtures and recorded the current-vs-baseline evidence in the throughput report.
  - Confirmed that smoke remains a routine guardrail while the representative profile still reports trajectory accumulation as the dominant explicit-grid phase.
  - Added regression coverage that locks the profiler report schema across smoke and representative modes, including the stable top-level keys, phase timing keys, and run-summary keys.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --profile smoke --materialize-root /tmp/rust_rockfall/tb230_smoke --format json --json-output /tmp/rust_rockfall/tb230_smoke_report.json --markdown-output /tmp/rust_rockfall/tb230_smoke_report.md`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/tb230_representative --format json --json-output /tmp/rust_rockfall/tb230_representative_report.json --markdown-output /tmp/rust_rockfall/tb230_representative_report.md`
- Result/status: implemented_measured
- Boundaries: profiling and report updating only; no new physics, no distributed execution, no operational claim, no scale-up claim, and no annual-frequency, physical-probability, risk, exposure, or vulnerability claim.
- Next task: `TB-231`

### TB-231: Chant Sura Public-Context Acquisition Package Freeze

- Date: 2026-05-18
- Commit: `5f2a2b8`
- Objective: freeze the Chant Sura / Fluelapass acquisition package so required real inputs, expected local roots, and fixture-only paths stay separated and fail closed.
- Files changed: `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`, `docs/task_backlog.md`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a frozen machine-readable acquisition package that enumerates required real inputs, expected local roots, fixture-only paths, metadata fields, and the current blocked state.
  - Linked the package from the Chant Sura decision doc so the freeze artifact is easy to find alongside the human-readable decision record.
  - Added a focused regression that checks the package taxonomy stays `real_staged`/`fixture_backed`/`missing`/`deferred` and keeps fixture-only paths separate from required acquisition rows.
  - Removed TB-231 from the active backlog after the package and test coverage were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: no downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, and no physical-validation claim.
- Next task: `TB-232`

### TB-232: Real-Input Prepared-Pilot Gate For Chant Sura

- Date: 2026-05-18
- Commit: `bc0cbbd`
- Objective: make the Chant Sura prepared-pilot dry run consume the real-context acquisition package, surface the first missing real input category, and fail closed until required real inputs are staged.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a real-input acquisition-package classifier to the Chant Sura readiness gate so the report now distinguishes `missing`, `fixture_backed`, `partial_real`, and `ready_real` package states and exposes `first_missing_real_input_category`.
  - Threaded the new classification into the prepared-pilot dry-run summary so second-site readiness is only advertised when the acquisition package is fully real staged, with explicit blocked states for fixture-backed and partial-real packages.
  - Reworked the Chant Sura gate and workflow tests around temporary acquisition-package variants so the missing, fixture-backed, partial-real, and ready-real states are all exercised deterministically.
  - Updated the public real-site geodata guidance to note the new machine-readable prepared-pilot classification fields.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_chant_sura_real_context_readiness_gate.py scripts/summarize_chant_sura_fluelapass_dry_run_report.py tests/test_chant_sura_real_context_readiness_gate.py tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_chant_sura_real_context_readiness_gate tests.test_chant_sura_fluelapass_workflow_dry_run_report`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no downloads, no ensemble execution, no synthetic evidence claim, no physical-validation claim, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-233`

### TB-233: Observed Runout Acquisition Operator Package
- Date: 2026-05-18
- Commit: `c2cdad8`
- Objective: materialize an operator-facing observed runout/deposition acquisition package that follows the blocker matrix while staying explicitly template/non-evidence.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit `first_acquisition_action` to the next-action recommendation and threaded it through the rendered text report, acquisition checklist, and blocked no-evidence report.
  - Kept the generated scratch-root package classified as `template_non_evidence` while preserving the required inventory, geometry template, provenance template, uncertainty fields, licensing/readiness notes, and validation summary.
  - Extended the contract tests to assert the first acquisition action appears in the plain-text output and in the generated package artifacts.
  - Removed TB-233 from the active backlog after the operator package path was verified.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --output-root /tmp/tb233_observed_runout_pack --format text`
- Result/status: implemented_measured
- Boundaries: no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency claim, no physical-probability claim, no operational claim, and no generated acquisition files committed.
- Next task: `TB-234`

### TB-234: Observed Benchmark Intake Acceptance Smoke

- Date: 2026-05-18
- Commit: `913dd9b`
- Objective: add a fixture-backed acceptance smoke path for a complete observed runout/deposition benchmark intake and explicit schema rejections for common failure modes.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `tests/fixtures/observed_runout_deposition_intake_contract/accepted_fixture.yaml`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a committed acceptance-smoke fixture and threaded it into the observed intake report as a separate `fixture_acceptance_smoke` section so the accepted schema shape is reported independently from real physical evidence.
  - Kept the report blocked on missing benchmark inputs while still proving that the fixture-backed intake shape is accepted with geometry, provenance, uncertainty, calibration-role, validation-role, and holdout-eligibility checks.
  - Expanded the contract tests to load the fixture from disk, assert the accepted path, and cover missing geometry, missing provenance, missing uncertainty, ambiguous calibration role, and overclaim rejection cases.
  - Removed TB-234 from the active backlog after the smoke path and rejection cases were verified.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -v`
- Result/status: implemented_fixture_backed
- Boundaries: no real evidence claim, no calibration, no parameter fitting, no validation upgrade, no annual-frequency claim, no physical-probability claim, no operational claim, and no generated acquisition files committed.
- Next task: `TB-235`

### TB-235: Release-Zone Provenance Intake Bridge
- Date: 2026-05-18
- Commit: `5c1ad39`
- Objective: define a small intake path for field-supported release-zone provenance that stays separate from workflow-generated release candidates.
- Files changed: `scripts/lib/workflow_validation.py`, `scripts/plan_terrain_release_zone_candidates.py`, `scripts/generate_candidate_source_zone_scenarios.py`, `scripts/assess_validation_calibration_evidence_gaps.py`, `scripts/map_physical_credibility_evidence_requirements.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_candidate_source_zone_scenario_stress.py`, `tests/test_physical_credibility_evidence_requirements.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a shared release-zone provenance intake helper that canonicalizes `workflow_generated`, `field_supported`, `mixed_provenance`, and `blocked_missing_provenance` labels and reuses the same normalization path in the release-candidate firewall.
  - Threaded the intake bridge into the terrain candidate planner so source-zone provenance is reported separately from workflow-generated candidate rows.
  - Extended scenario generation to carry a nested provenance intake record and verified that field-supported provenance still keeps sampling weights conditional-only instead of turning them into occurrence probabilities.
  - Updated the physical-credibility evidence map and gap report to recognize the intake bridge as workflow evidence while keeping the release-zone evidence gap open.
  - Removed TB-235 from the active backlog after the new intake bridge and tests were verified.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_scenario_stress -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_physical_credibility_evidence_requirements -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: no release-zone validation claim, no threshold tuning, no source-frequency semantics, no annual-frequency claim, no operational claim, and no probability conversion for sampling weights.
- Next task: `TB-236`

### TB-236: Block-Population And Source-Frequency Acquisition Deferral Map
- Date: 2026-05-18
- Commit: `1219872`
- Objective: split the block-population and source-frequency rows in the physical-evidence matrix into explicit acquisition blockers and future-gate prerequisites, while keeping conditional scenario weights out of frequency language.
- Files changed: `scripts/assess_validation_calibration_evidence_gaps.py`, `scripts/map_physical_credibility_evidence_requirements.py`, `tests/test_validation_calibration_evidence_gaps.py`, `tests/test_physical_credibility_evidence_requirements.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added explicit machine-readable blocker records for block-population evidence and source-frequency evidence in the validation/calibration gap helper, including `first_missing_input` fields and future-gate prerequisite records.
  - Threaded those blocker records into the physical-credibility matrix so the top-level report now exposes separate block-population and source-frequency blocker lists, first-missing inputs, and the conditional-only sampling-weight boundary.
  - Reworked the block-population and source-frequency evidence categories so the first missing inputs are named directly and conditional sampling weights are not reported as frequency evidence.
  - Updated the regression tests to assert the new blocker fields, the first missing inputs, and the frequency/evidence boundary, then removed TB-236 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps tests.test_physical_credibility_evidence_requirements`
  - `PYENV_VERSION=system uv run python scripts/map_physical_credibility_evidence_requirements.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no source-frequency implementation, no annual-frequency product, no calibration, no risk/exposure semantics, no operational claim, and no probability claim for conditional sampling weights.
- Next task: `TB-237`

### TB-237: Workflow-Shell Coupling Extraction Batch
- Date: 2026-05-18
- Commit: `2d8430d`
- Objective: extract one bounded batch of duplicated workflow-shell mechanics into shared helpers while preserving public CLI output contracts.
- Files changed: `scripts/lib/workflow_validation.py`, `scripts/generate_pilot_command_plan.py`, `scripts/check_same_scale_artifact_readiness.py`, `scripts/inventory_workflow_shell_coupling.py`, `tests/test_workflow_shell_coupling_inventory.py`, `tests/test_pilot_command_plan.py`, `tests/test_same_scale_artifact_readiness.py`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a shared `load_repo_script_module` helper for repo-local dynamic script loading and replaced the duplicated loader implementations in the pilot command plan and same-scale readiness CLIs.
  - Preserved inventory visibility for shared-helper dynamic imports so the coupling report still lists script dependencies after the extraction.
  - Added focused compatibility coverage for affected JSON/text CLI surfaces, including schema keys and existing status labels.
  - Updated the script inventory to record the shared workflow helper and removed TB-237 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_workflow_shell_coupling_inventory tests.test_pilot_command_plan tests.test_same_scale_artifact_readiness`
  - `PYENV_VERSION=system uv run python scripts/inventory_workflow_shell_coupling.py --format json --json-output /tmp/tb237_workflow_shell_inventory.json > /tmp/tb237_workflow_shell_inventory.stdout`
  - `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json > /tmp/tb237_command_plan.json`
  - `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json > /tmp/tb237_readiness.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no script deletion, no broad rewrite, no public status-label rename, no scientific claim change, no operational claim, and no unrelated validator churn.
- Next task: `TB-238`

### TB-238: Command-Plan Manifest Contract Consolidation
- Date: 2026-05-18
- Commit: `a4bfbbe`
- Objective: consolidate command-plan manifest semantics across the portable pilot and Balfrin multi-release-zone handoff generators.
- Files changed: `scripts/lib/command_plan_contract.py`, `scripts/generate_pilot_command_plan.py`, `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_pilot_command_plan.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a shared command-plan contract helper that owns command id, command text, expected-input/output lists, read-only/write flags, ignored output roots, blocked-template ids, command descriptions, repo-relative display paths, and output-profile policy passthrough.
  - Routed the Tschamut/Chant Sura pilot plan and Balfrin handoff plan through the helper while preserving their domain-specific command strings and existing group-shape contracts.
  - Added focused regression assertions that command ids, command descriptions, blocked-template ids, read/write fields, expected inputs/outputs, ignored roots, and Balfrin group shape remain stable under the shared contract.
  - Removed TB-238 from the active backlog after the shared manifest semantics were verified.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/lib/command_plan_contract.py scripts/generate_pilot_command_plan.py scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_pilot_command_plan.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_pilot_command_plan tests.test_balfrin_multi_release_zone_demo_handoff`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no live execution, no Balfrin job submission, no generated output commit, no command behavior change, no scale-up claim, no operational claim, and no physical-probability/risk/exposure/vulnerability claim.
- Next task: backlog refill needed

### TB-239: Backlog, Maturity Snapshot, And Worker-Context Alignment

- Date: 2026-05-18
- Commit: `9333ad7`
- Objective: align the active backlog, maturity snapshot, and worker-context routing so the current queue stays synchronized with worker guidance.
- Files changed: `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `scripts/print_agent_task_context.py`, `tests/test_agent_task_context.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Updated the maturity snapshot to state that TB-239+ tasks are active, replacing the stale empty-backlog language without changing any scientific claims.
  - Narrowed Balfrin routing so it requires explicit Balfrin plus access/action terms, which keeps Chant Sura-only tasks from inheriting remote-cluster access just because their text mentions remote evidence.
  - Added regression coverage for the live active-queue report and for Chant Sura text that mentions remote-cluster evidence but still stays local-only.
  - Removed TB-239 from the active backlog after the alignment change was verified.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_agent_task_context -v`
  - `git diff --check`
  - `scripts/git-hooks/pre-commit`
- Result/status: implemented_measured
- Boundaries: documentation/context hygiene only; no remote-cluster access attempt, no scientific claim upgrade, and no operational claim.
- Next task: `TB-240`

### TB-240: Read-Only Target-Area Metrics Recovery From Balfrin Run Root

- Date: 2026-05-18
- Commit: local
- Objective: add a read-only recovery path that checks whether the preserved authorized Balfrin target-area run root can close the missing peak-memory and split validation/hazard metrics before requesting a rerun.
- Files changed: `scripts/recover_balfrin_target_area_metrics_from_run_root.py`, `tests/test_balfrin_target_area_metrics_recovery.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/balfrin_probe_slurm_driver.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a recovery CLI that consumes the Balfrin access preflight, targets the existing authorized target-area run root, and classifies each required metrics-completion field as `recovered`, `still_missing`, `unavailable_from_preserved_root`, or `blocked_access`.
  - Added a rerun-package comparison section that reports recovered and unrecovered metrics and states whether the existing metrics-completion rerun remains necessary.
  - Exercised the live read-only preflight and remote recovery path against the preserved Balfrin root; access was ready, collection completed, and all five required target metrics were recovered from preserved/read-only sources, so the metrics-completion rerun is not necessary for those fields.
  - Recovered `memory_peak_mb` from read-only `sacct` MaxRSS for job `4329024`, validation output file count/bytes from command-plan validation paths, and hazard output file count/bytes from the command-plan hazard output directory.
  - Added fixture-backed tests for recovered, still-missing, access-blocked, and artifact-writing cases, then removed TB-240 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/recover_balfrin_target_area_metrics_from_run_root.py tests/test_balfrin_target_area_metrics_recovery.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_recovery -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb240_balfrin_access_preflight.json`
  - `PYENV_VERSION=system uv run python scripts/recover_balfrin_target_area_metrics_from_run_root.py --balfrin-access-json /tmp/tb240_balfrin_access_preflight.json --format json --json-output /tmp/tb240_balfrin_target_area_metrics_recovery.json --text-output /tmp/tb240_balfrin_target_area_metrics_recovery.txt > /tmp/tb240_balfrin_target_area_metrics_recovery.stdout`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_recovery tests.test_balfrin_target_area_metrics_completion_rerun_package tests.test_balfrin_probe_metrics_report -v`
- Result/status: implemented_measured
- Boundaries: read-only recovery only; no live Balfrin submission, no remote mutation, no authorization grant, no fabricated metrics, no claim upgrade, no scale-up claim, no physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-241`

### TB-241: Target-Area Metrics Completion Authorization Handoff

- Date: 2026-05-18
- Commit: local
- Objective: produce a minimal authorization-ready handoff for the Balfrin target-area metrics-completion rerun while keeping live execution explicitly authorization-gated.
- Files changed: `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`, `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit `authorization_handoff_package` to the metrics-completion rerun helper with the exact rerun root, SBATCH command, dry-run/generate-only commands, collection command, preservation gate command, preservation checklist, access-preflight status, and TB-240 unrecovered-metric list.
  - Added fail-closed classifications for missing Balfrin access, missing package inputs, stale comparison basis, no unrecovered metrics, and missing explicit authorization; the handoff can be ready for review while still reporting live submission as unauthorized.
  - Materialized a read-only `/tmp` handoff using the current Balfrin preflight; access status was `ready_for_read_only_collection`, and the handoff status was `ready_for_authorization_review` for the five TB-240 unrecovered metrics.
  - Added focused fixture-backed tests for ready-for-authorization-review, blocked-missing-access, blocked-no-unrecovered-metrics, and blocked-missing-package cases, then removed TB-241 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py tests/test_balfrin_target_area_metrics_completion_rerun_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_completion_rerun_package`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb241_balfrin_access_preflight.json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py --balfrin-access-json /tmp/tb241_balfrin_access_preflight.json --format json --json-output /tmp/tb241_balfrin_target_area_metrics_completion_authorization_handoff.json --text-output /tmp/tb241_balfrin_target_area_metrics_completion_authorization_handoff.txt > /tmp/tb241_balfrin_target_area_metrics_completion_authorization_handoff.stdout`
  - `git diff --check`
- `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
- `scripts/git-hooks/pre-commit`
- `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: authorization handoff only; no live submission, no remote mutation beyond read-only preflight, no scientific interpretation, no fabricated metrics, no scale-up authorization, no operational claim, and no physical-probability/risk/exposure/vulnerability claim.
- Next task: `TB-242`

### TB-242: Preservation-Checked Metrics Completion Evidence Integration

- Date: 2026-05-18
- Commit: local
- Objective: propagate a canonical metrics-completion source label through the Balfrin metrics report, preservation gate, evidence bundle, and next-action decision helper without collapsing recovered, rerun, and blocked branches.
- Files changed: `scripts/summarize_balfrin_probe_metrics_report.py`, `scripts/summarize_balfrin_probe_preservation_gate.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json`, `tests/fixtures/balfrin_next_live_run_decision_gate/defer_bundle.json`, `tests/test_balfrin_probe_metrics_report.py`, `tests/test_balfrin_probe_preservation_gate.py`, `tests/test_balfrin_evidence_bundle.py`, `tests/test_balfrin_next_live_run_decision_gate.py`
- Implementation summary:
  - Added `metrics_completion_source` handling so the canonical metrics report, preservation gate, and evidence bundle can label `recovered_existing_run_root`, `new_metrics_completion_rerun`, or `blocked_missing_metrics` explicitly.
  - Updated the next-action decision helper so completed target-area metrics are treated as closed evidence rather than the top-ranked next action, and the blocked branch remains explicit when no recovered or rerun metrics exist.
  - Refreshed the decision fixtures and focused tests to prove the blocked branch stays blocked, the recovered branch stays recovered, and no claim-boundary upgrade is implied by the new source label.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_metrics_report tests.test_balfrin_probe_preservation_gate tests.test_balfrin_evidence_bundle tests.test_balfrin_next_live_run_decision_gate`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: evidence integration only; no live submission, no physical-credibility upgrade, no annual-frequency or risk semantics, and no operational claim.
- Next task: `TB-243`

### TB-243: Target-Area Spatial Artifact Recovery Or Deferral

- Date: 2026-05-18
- Commit: local
- Objective: determine whether target-area spatial-uncertainty artifacts can be recovered from the preserved Balfrin run root or must remain explicit deferrals separate from execution metrics.
- Files changed: `scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py`, `tests/test_balfrin_target_area_spatial_artifact_recovery.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only spatial artifact recovery CLI that consumes the Balfrin access preflight, supports local fixtures or precollected inventory JSON, and inspects the existing authorized target-area run root without remote mutation.
  - Classified required spatial artifacts as `recovered`, `unavailable_from_preserved_root`, or `blocked_access`, while recording `not_required_for_execution_metrics_closure` for the execution-metrics separation path.
  - Exercised the live read-only Balfrin path; access was ready, collection completed, the run-root-referenced hazard manifest plus standard and pilot GIS package manifests were recovered, and the cellwise spatial layers plus derived spatial uncertainty products remained `unavailable_from_preserved_root`.
  - Added fixture-backed tests proving unavailable spatial artifacts remain explicit deferrals and are not treated as physical validation evidence, then removed TB-243 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py tests/test_balfrin_target_area_spatial_artifact_recovery.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_spatial_artifact_recovery -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb243_balfrin_access_preflight.json`
  - `PYENV_VERSION=system uv run python scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py --balfrin-access-json /tmp/tb243_balfrin_access_preflight.json --format json --json-output /tmp/tb243_balfrin_target_area_spatial_artifact_recovery.json --text-output /tmp/tb243_balfrin_target_area_spatial_artifact_recovery.txt > /tmp/tb243_balfrin_target_area_spatial_artifact_recovery.stdout`
- Result/status: implemented_measured
- Boundaries: read-only artifact inspection only; no live Balfrin submission, no remote mutation, no generated artifact commit, no new spatial interpretation claim, no physical-credibility upgrade, no scale-up claim, no physical-probability/risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-244`

### TB-244: Post-Metrics Balfrin Demonstration Closure Refresh

- Date: 2026-05-18
- Commit: local
- Objective: refresh the Balfrin closure synthesis so execution-metrics closure states, spatial-artifact separation, and post-metrics next-action ranking stay explicit.
- Files changed: `scripts/summarize_balfrin_demonstration_closure_package.py`, `tests/test_balfrin_demonstration_closure_package.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Refreshed the closure helper to expose `metrics_complete`, `metrics_unrecoverable_deferred`, and `blocked_no_new_measured_evidence` as explicit states instead of only the old mixed-provenance/new-evidence gate.
  - Added a separate target-area spatial-artifact classification section using the TB-243 separation vocabulary so spatial deferrals remain distinct from execution-metrics closure.
  - Added a post-metrics next-action section that ranks smallest multi-zone measurement, physical-evidence acquisition, second-site staging, and deferral after the metrics gate is resolved.
  - Updated the focused closure tests to prove the default path remains blocked when no new measured or recovered metrics are supplied and to exercise the complete and explicitly deferred branches.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_demonstration_closure_package.py tests/test_balfrin_demonstration_closure_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_demonstration_closure_package -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_closure_package.py --format json > /tmp/balfrin_demonstration_closure_package.stdout`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: synthesis only; no live execution, no physical-credibility upgrade, no annual-frequency semantics, no operational claim, and no replacement of source evidence reports.
- Next task: `TB-245`

### TB-245: Current Multi-Zone Handoff Budget Recheck

- Date: 2026-05-18
- Commit: `d92f4e2`
- Objective: remeasure the current multi-zone handoff projection after command-plan contract consolidation and record whether the budget still requires manifest reduction before any pruning work.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/output_budget_reducer_scaling_gate.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit budget-recheck classification to the handoff projection so the current command-plan shape reports `budget_passes_no_reduction_needed`, `blocked_budget_reduction_needed`, or `blocked_replay_contract_ambiguity` deterministically.
  - Surfaced the replay-critical field inventory for the projection, constraint thresholds, and smallest-run replay fields so the report can say exactly which fields must stay stable for the recheck.
  - Added a contract-spy regression that proves the handoff consumes the shared command-plan helper, plus a no-mutation regression that keeps the command plan and projection semantics stable across rechecks.
  - Refreshed the reducer-pressure and output-budget docs with the current blocked handoff projection and removed TB-245 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_multi_zone_reducer_pressure_gate tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: measurement/recheck only; no pruning, no live Balfrin job, no output-schema change, no distributed reducer, no scale-up claim, and no operational claim.
- Next task: `TB-246`

### TB-246: Multi-Zone Handoff Manifest Budget Reduction

- Date: 2026-05-18
- Commit: `0eb6729`
- Objective: reduce the smallest multi-zone handoff's projected manifest and sidecar pressure with a compact replay-safe projection while keeping replay-critical fields, hashes, merge order, and provenance explicit.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/output_budget_reducer_scaling_gate.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a compact manifest-pruning path to the handoff projection that strips non-replay sidecars while keeping the replay-safe primary outputs, merge-state files, and projection hashes explicit.
  - Recorded before/after fixture-backed comparisons for the baseline and compact projections, including manifest bytes, output bytes, output file counts, sidecar bytes, sidecar counts, and reducer-manifest counts.
  - Kept the budget recheck fail-closed: the compact projection reduces the handoff from 62 files / 21 sidecars / 26057 manifest bytes to 39 files / 2 sidecars / 17788 manifest bytes, but it still remains blocked on `manifest_size_bytes`, so the report now names the exact remaining replay-safe fields.
  - Added regressions for the compact-vs-baseline comparison, the no-reduction-needed branch, and the fail-closed refusal to prune replay-critical fields.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: projection and manifest-pruning only; no live Balfrin job, no output schema change, no distributed reducer, no scale-up claim, no physical-probability/risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-247`

### TB-247: Smallest Multi-Zone Authorization Preflight Recheck

- Date: 2026-05-18
- Commit: local
- Objective: refresh the smallest multi-zone Balfrin authorization preflight after the compact handoff budget recheck and keep the go/no-go branch machine-readable.
- Files changed: `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/balfrin_probe_slurm_driver.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Refreshed the preflight decision branch to report `ready_for_authorization_review`, `blocked_missing_authorization`, `blocked_reducer_budget`, or `blocked_access`, while preserving the exact consumed Balfrin access status separately.
  - Made reducer-budget and compact handoff-budget blockers take precedence over missing authorization, so the current `blocked_budget_reduction_needed` manifest-size blocker remains fail-closed as `blocked_reducer_budget`.
  - Added explicit output-profile status, reviewed-package hash, authorization-record status, reducer-budget status, and smallest-run shape fields to the machine-readable preflight report.
  - Materialized the current compact answer in `validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml`: access was `ready_for_read_only_collection`, the reviewed package hash was `6f2b5288e4c87369c847b566a1cce31685a91146536207d2cdc3c0d182028f64`, the authorization record was missing, output profile was ready, and status remained `blocked_reducer_budget`.
  - Added fixture-backed tests for the ready-for-review, missing-authorization, reducer-budget, compact handoff-budget, and blocked-access branches, then removed TB-247 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_authorized_multi_zone_submit tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb247_balfrin_access_preflight.json`
  - `PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --format json > /tmp/tb247_default_smallest_multi_zone_handoff.json` (expected exit 2 because the compact handoff budget remains blocked)
  - `PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --balfrin-access-preflight-json /tmp/tb247_balfrin_access_preflight.json --json-output /tmp/tb247_default_smallest_multi_zone_authorization_preflight.json --text-output /tmp/tb247_default_smallest_multi_zone_authorization_preflight.txt --format json > /tmp/tb247_default_smallest_multi_zone_authorization_preflight.stdout` (expected exit 2 with `blocked_reducer_budget`)
- Result/status: implemented_measured
- Boundaries: preflight only; no live Balfrin submission, no remote mutation beyond read-only access checks, no authorization grant, no scale-up claim, no distributed-execution claim, no annual-frequency or physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-248`

### TB-248: Authorization-Gated Smallest Multi-Zone Measurement Evidence Path

- Date: 2026-05-18
- Commit: local
- Objective: prepare a deterministic, authorization-gated path from the smallest multi-zone Balfrin preflight through post-run collection and closure-package input while preserving the current blocked branch.
- Files changed: `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`, `tests/test_balfrin_authorization_gated_multi_zone_measurement_path.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only checklist helper that consumes the TB-247 authorization preflight record and binds the exact preflight output, reviewed handoff package, authorization record, documented `--authorized-submit` command, deterministic run root, collector commands, preservation gate, post-run evidence collector, and closure-package input path.
  - Preserved the current blocked branch from TB-247: the default helper run over `validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml` reports `blocked_pre_authorization` with TB-247 status `blocked_reducer_budget`, the missing authorization record, and `submit_command_executed=false`.
  - Added fixture-backed tests proving missing authorization, access loss, and incomplete run roots cannot be promoted to measured closure evidence.
  - Documented the post-authorization checklist and post-run promotion conditions in the Balfrin SLURM driver, then removed TB-248 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py tests/test_balfrin_authorization_gated_multi_zone_measurement_path.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_authorization_gated_multi_zone_measurement_path -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py --format json --json-output /tmp/tb248_authorization_gated_multi_zone_path.json --text-output /tmp/tb248_authorization_gated_multi_zone_path.txt > /tmp/tb248_authorization_gated_multi_zone_path.stdout` (expected exit 2 with `blocked_reducer_budget`)
- Result/status: implemented_blocked_report
- Boundaries: read-only checklist and fixture-backed evidence gates only; no live Balfrin submission, no remote mutation, no authorization grant, no generated heavy output commit, no scale-up or distributed-execution claim, no annual-frequency or physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-249`

### TB-249: Chant Sura Real Core-Input Staging Verification

- Date: 2026-05-18
- Commit: local
- Objective: tighten the Chant Sura gate so it distinguishes real-staged core inputs, fixture-backed scaffolding, metadata mismatches, missing rows/files, and deferred public-context products before any prepared-pilot dry run.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit real-core input classifier with ordered row definitions, file validation, synthetic-marker detection, and separate handling for real-staged, fixture-backed, metadata-mismatch, missing-row, and deferred rows.
  - Split the no-download verifier output into first missing real input details, first fixture-backed input details, exact missing-field lists, and separate missing-row versus missing-file counts.
  - Tightened the gate/status logic so metadata mismatches report a dedicated blocked state instead of collapsing into generic missing-input output.
  - Added focused tests for clean missing-input, fixture-backed blocked, partial-real, metadata-mismatch, missing-row, ready-real-core, and render-text cases, then removed TB-249 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_chant_sura_real_context_readiness_gate.py tests/test_chant_sura_real_context_readiness_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate -v`
- Result/status: implemented_measured
- Boundaries: no downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, no physical-validation claim, no scale-up claim, and no generated heavy outputs committed.
- Next task: `TB-250`

### TB-250: Chant Sura Missing-Input Acquisition Handoff

- Date: 2026-05-18
- Commit: local
- Objective: add a no-download Chant Sura handoff that names the first missing real core input, the expected local path, the metadata contract, and the deterministic next action before a real-input dry run.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a deterministic `real_input_acquisition_handoff` block to the Chant Sura readiness gate so operators can read the next action directly from the report instead of inferring it from blocker state.
  - Classified the handoff as `ready_no_handoff_needed`, `stage_local_existing_input`, `request_download_authorization`, or `defer_second_site` using the first missing real core input and its metadata contract.
  - Added focused tests covering ready-real-core, missing terrain metadata, missing AOI tile catalog, and missing source-zone / scenario / policy records, then verified the gate text output includes the new handoff section.
  - Documented the current no-download handoff snapshot in the Chant Sura real-context acquisition decision pack and removed TB-250 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: handoff only; no downloads, no second-site ensemble, no generated heavy outputs committed, no physical-validation claim, no operational claim, and no scale-up / annual-frequency / risk / exposure / vulnerability / distributed-execution claim.
- Next task: `TB-251`

### TB-251: Real-Input Chant Sura Prepared-Pilot Dry Run

- Date: 2026-05-18
- Commit: local
- Objective: make the Chant Sura AOI-to-prepared-pilot dry run follow the acquisition-package core-input status, stay ready only for real staged core inputs, and emit a deterministic blocked handoff for missing real core inputs.
- Files changed: `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Reworked the Chant Sura dry-run summarizer to classify readiness from the acquisition package core-input status instead of file presence, which keeps fixture-backed or partial packages from looking ready and preserves a ready path for genuine real-staged core inputs.
  - Added a deterministic `blocked_missing_real_core_inputs` path with a TB-250 acquisition-handoff pointer, while keeping fixture-backed and partial-real packages in their own blocked states.
  - Mirrored the acquisition-package-derived core classification back into the nested readiness section so the JSON and text report stay internally consistent.
  - Updated the Chant Sura dry-run regression to cover a real-core ready path, fixture-backed fail-closed behavior, partial-real fail-closed behavior, and the blocked-missing-real-core-inputs handoff.
  - Removed TB-251 from the active backlog after the dry-run report behavior and tests were aligned.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_fluelapass_workflow_dry_run_report`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: dry run only; no downloads, no ensemble execution, no synthetic evidence claim, no physical-validation claim, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-252`

### TB-252: Observed Benchmark Candidate Acquisition Triage

- Date: 2026-05-18
- Commit: local
- Objective: identify one concrete local observed runout/deposition candidate path or return a precise blocked acquisition report, while keeping the intake boundary non-operational and non-calibration.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated `candidate_acquisition_report` to the observed intake contract helper so the report now names the local candidate paths, the selected candidate path, the required external acquisition actions, the licensing/provenance blockers, and the first missing geometry/provenance/uncertainty fields.
  - Wired the report to the local observed-deposition diagnostic CSVs under `data/processed/tschamut2014` and `validation/data/processed/tschamut`, while keeping the acceptance-smoke fixture separate as schema-only evidence.
  - Kept the recommendation logic explicit with the task-specified `stage_candidate`, `blocked_no_candidate`, `blocked_license_or_provenance`, and `defer_scientific_claim` vocabulary.
  - Added focused tests for the local-candidate-present branch, the no-candidate branch, and the existing missing provenance / missing uncertainty classifier cases, then verified the text report surfaces the candidate-acquisition section.
  - Removed TB-252 from the active backlog after the triage report and tests were aligned.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -q`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: acquisition triage only; no downloads, no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or risk semantics, and no operational claim.
- Next task: `TB-253`

### TB-253: First Real Observed Benchmark Intake Integration

- Date: 2026-05-18
- Commit: local
- Objective: integrate deterministic real-input observed benchmark intake classification while keeping calibration, holdout, and claim boundaries explicit.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a first-class `real_input_intake_report` to the observed intake helper so the report now separates package availability from acceptance and reports geometry, provenance, uncertainty, calibration-role, validation-role, holdout-eligibility, and license classifications.
  - Implemented deterministic blocked states for `blocked_missing_inputs`, `blocked_schema_gap`, `blocked_role_unclear`, `blocked_claim_overclaim`, and `blocked_fixture_only_inputs`, while keeping the physical-credibility gap update at `not_established`.
  - Wired the real-input classification into the top-level report, the blocker summary, the readiness-pack manifest, and the CLI exit path so non-ready intake stays explicit without upgrading claims.
  - Updated the regression coverage to prove a contract-compliant staged package is accepted, missing-field and role-gap cases are rejected, fixture-only inputs fail closed, and the default repo state remains blocked until a real package is staged.
  - Removed TB-253 from the active backlog after the intake contract and tests were aligned.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json >/tmp/tb253_default_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: intake only; no calibration, no parameter fitting, no source-frequency semantics, no annual-frequency or risk semantics, no operational claim, and no claim upgrade beyond what accepted evidence supports.
- Next task: `TB-254`

### TB-254: Release-Zone, Block-Population, And Source-Frequency Evidence Triage

- Date: 2026-05-18
- Commit: `8c44f4a`
- Objective: triage the next real-evidence acquisition blockers for field-supported release zones, block-population evidence, and source-frequency records without changing the scientific claim level.
- Files changed: `scripts/assess_validation_calibration_evidence_gaps.py`, `scripts/map_physical_credibility_evidence_requirements.py`, `docs/target_area_physical_evidence_acquisition_pack.md`, `docs/current_maturity_snapshot.md`, `tests/test_validation_calibration_evidence_gaps.py`, `tests/test_physical_credibility_evidence_requirements.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added an explicit release-zone first-missing-input and acquisition blocker path in the gap helper so the release-zone evidence gap now names a concrete field-supported geometry/provenance package instead of collapsing into the conditional contract.
  - Added a physical-evidence triage section to the requirements helper that classifies release-zone provenance and block-population evidence as acquisition candidates while deferring source-frequency records until a later frequency-semantics phase change.
  - Preserved the distinction between conditional sampling weights and source-frequency evidence in both the report data and the text renderers, and kept the fixture-backed second-site provenance boundary out of field-supported evidence.
  - Updated the roadmap docs and focused tests so the next acquisition/defer actions, first-missing-input fields, and non-promotion of workflow fixtures are explicit.
  - Removed TB-254 from the active backlog after the implementation state was aligned.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps tests.test_physical_credibility_evidence_requirements`
  - `git diff --check`
- Result/status: implemented_measured
- Boundaries: acquisition triage only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no physical-probability claim, no risk/exposure semantics, no distributed-execution change, and no operational claim.
- Next task: backlog refill needed

## Guidance Notes

### 2026-05-18: Procedural Drift Reduction

- Scope: repository guidance, backlog semantics, and worker-facing incentives.
- Procedural patterns reduced: tasks whose primary output is another gate,
  checklist, YAML record, blocked/deferred report, closure package, or
  management summary without a named execution, measurement, acquisition,
  reproducibility, or consolidation payoff.
- Desired worker behavior: prefer bounded runs or recovery, real-input staging,
  release/scenario/AOI automation, restartability proof, runtime/output scaling
  measurements, uncertainty-localization evidence, and simplification of
  duplicated orchestration surfaces.
- Boundary retained: scientific honesty, claim boundaries, fail-closed evidence
  discipline, and Balfrin authorization requirements remain intact.

### TB-255: AOI-To-Hazard-Map Front Door CLI

- Date: 2026-05-19
- Commit: `70f7599`
- Objective: add one user-facing entrypoint that exposes the existing AOI preparation, staging, planning, execution, collection, and map-package steps behind a coherent command surface.
- Files changed: `scripts/run_aoi_hazard_workflow.py`, `tests/test_run_aoi_hazard_workflow.py`, `docs/task_backlog.md`, `docs/script_inventory.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only front-door helper with `status`, `prepare`, `plan`, `run-local-smoke`, `submit-balfrin`, `collect`, and `package-map` views that normalize the existing AOI dry-run, portable command-plan, and GIS/COG audit helpers into one compact JSON status object.
  - Kept the status object fail-closed with explicit next-action, first-blocker, expected-path, and claim-boundary fields, while trimming the payload to path-level summaries instead of full command-plan inventories.
  - Added focused tests for command dispatch, clean-checkout blocking, and fixture-backed status aggregation, then classified the new script in the repository inventory and removed TB-255 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow -v`
  - `PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py status --format json >/tmp/tb255_front_door_status.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: front-door orchestration only; no live Balfrin submission, no downloads, no physical-probability semantics, no operational claim, and no generated heavy outputs committed.
- Next task: backlog refill needed

### TB-256: AOI Manifest Bootstrap And Schema Contract

- Date: 2026-05-19
- Commit: local
- Objective: add a compact AOI manifest/bootstrap contract that turns user-supplied LV95 bounds or a GeoJSON polygon into a deterministic site config package for the existing second-site preparation helpers.
- Files changed: `scripts/bootstrap_aoi_manifest.py`, `scripts/check_second_site_public_geodata_preflight.py`, `scripts/plan_swisstopo_aoi_acquisition.py`, `tests/test_bootstrap_aoi_manifest.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a metadata-only bootstrap helper that validates EPSG:2056/LN02 AOI input, computes a deterministic manifest id from canonicalized geometry, and writes a compact self-contained site package under the caller-provided ignored root.
  - Generated the AOI tile catalog, acquisition manifest, and template source-scenario policy alongside the site config so the existing preflight and AOI acquisition planner can consume the bootstrap output without hand-editing fixture files.
  - Updated shared preflight path resolution to respect the bootstrap package’s root-relative layout while preserving the older fixture-backed repo-relative behavior, then added focused tests for valid bounds, invalid CRS, missing geometry, deterministic ids, and downstream helper consumption.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_bootstrap_aoi_manifest`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner`
- Result/status: implemented_fixture_backed
- Boundaries: manifest/bootstrap only; no geodata download, no simulation, no hazard-map claim, no annual-frequency semantics, and no committed generated AOI roots.
- Next task: backlog refill needed

### TB-257: AOI Swisstopo Product Resolver And Cache Manifest

- Date: 2026-05-19
- Commit: local
- Objective: resolve the bootstrapped AOI into deterministic swisstopo product rows and a resumable cache-manifest template without introducing any download path.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`, `scripts/plan_swisstopo_aoi_acquisition.py`, `docs/swisstopo_data_strategy.md`, `docs/public_real_site_geodata_preparation.md`, `tests/test_swisstopo_aoi_acquisition_planner.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a resolver layer that emits one AOI product row each for swissALTI3D, SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D, with swissALTI3D resolving to the AOI catalog tile id and the remaining public-context rows carrying explicit unresolved-tile blockers.
  - Added a cache-manifest template surface to the public-geodata contract with checksum, version/date, license, raw path, processed path, and retry/resume placeholders so the no-download planner can describe the future staging contract deterministically.
  - Updated the planner text/JSON output and focused tests so the resolved terrain tile, unresolved context rows, and no-download behavior are all asserted from the same fixture-backed path.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swisstopo_aoi_acquisition_planner tests.test_second_site_public_geodata_preflight tests.test_public_geodata_cache_verifier`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: resolver and manifest generation only; no download, no simulation, no operational claim, and no generated public data committed.
- Next task: `TB-258`

### TB-258: Local Public-Geodata Staging And Verification Command

- Date: 2026-05-19
- Commit: local
- Objective: add a user-facing staging command that validates locally supplied swisstopo files against the AOI cache manifest and records verified staged inputs.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`, `scripts/stage_public_geodata_cache.py`, `docs/swisstopo_data_strategy.md`, `docs/public_real_site_geodata_preparation.md`, `docs/script_inventory.md`, `tests/test_public_geodata_cache_stager.py`, `tests/test_second_site_public_geodata_preflight.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a new `scripts/stage_public_geodata_cache.py` front door that rewrites the cache manifest in place after validating repo-relative or absolute staged paths, checksums, CRS, resolution, provenance, and optional rows without requiring manual cache-manifest edits.
  - Extended the shared cache verifier to support directory checksums with metadata-sidecar exclusion, optional-missing rows, and provenance field checks so staged inputs can round-trip through the same manifest contract the readiness gate consumes.
  - Surfaced the staging command in the second-site cache contract, updated the repo documentation and script inventory, and added focused fixture-backed tests for verified, missing, checksum-mismatch, metadata-mismatch, unsupported-product, and optional-missing paths.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_stager`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_verifier tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner`
- Result/status: implemented_fixture_backed
- Boundaries: local staging and verification only; no network download, no simulation, no physical validation claim, no operational claim, and no heavy geodata committed.
- Next task: backlog refill needed

### TB-259: Prepared Terrain And Context Builder For AOI

- Date: 2026-05-19
- Commit: `d948d3e`
- Objective: build the prepared terrain crop and context QA products from verified AOI cache inputs into a deterministic prepared-input root.
- Files changed: `scripts/plan_aoi_terrain_preprocessing.py`, `tests/test_aoi_terrain_preprocessing.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a prepared-input builder front door to the AOI terrain planner that stages terrain crops, terrain metadata, an AOI tile catalog copy, a terrain QA summary, and a context availability summary under an ignored prepared-input root.
  - Added explicit `ready`, `partial_context`, `blocked_missing_terrain`, and `blocked_metadata_mismatch` classifications, with deterministic slope/aspect/hillshade QA metrics derived from the staged ESRI ASCII grid.
  - Added fixture-backed tests for the ready, partial-context, missing-terrain, and metadata-mismatch paths, plus regression coverage for the existing terrain-preprocessing helper.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_terrain_preprocessing -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_context_overlap -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_fixture_backed
- Boundaries: preparation only; no release-zone validation, no ensemble execution, no operational claim, and no heavy public geodata committed.
- Next task: `TB-260`

### TB-260: Release-Zone Candidate Review Package

- Date: 2026-05-19
- Commit: local
- Objective: generate a reviewable release-zone candidate package from prepared AOI terrain with stable candidate IDs, GIS outputs, sensitivity labels, and editable acceptance fields.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/lib/workflow_validation.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_candidate_source_zone_scenario_stress.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated candidate review package surface to the terrain planner with deterministic release-cell IDs, review-decision defaults, provenance-label legends, slope summaries, and GIS-readable GeoJSON, CSV, and mask outputs.
  - Kept the candidate polygon bundle reviewable by threading `accepted`, `rejected`, and `needs_field_review` fields into the emitted feature properties while preserving the existing heuristic candidate generation contract.
  - Extended the shared provenance intake so non-accepted review states cannot be upgraded to `field_supported`, and added regression coverage showing unreviewed or overclaimed candidates stay out of the field-supported scenario path.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates tests.test_candidate_source_zone_scenario_stress`
- Result/status: implemented_fixture_backed
- Boundaries: candidate generation and review packaging only; no release-zone validation claim, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-261`

### TB-261: Reviewed Source-Zone And Scenario Plan Freezer

- Date: 2026-05-19
- Commit: `8130a82`
- Objective: convert reviewed release-zone candidates into frozen source-zone metadata, conditional scenario tables, and a source/scenario policy record for the AOI.
- Files changed: `scripts/generate_candidate_source_zone_scenarios.py`, `tests/test_candidate_source_zone_freezer.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a freezer mode to the candidate scenario generator that consumes a review package plus accepted candidate IDs and emits frozen source-zone metadata, release rows, a conditional scenario table, and a source/scenario policy record under an ignored output root.
  - Kept the conditional-only boundary explicit by carrying trajectory-count, seed-policy, block-family, and conditional-weight controls into the freezer outputs while leaving annual-frequency and probability fields empty.
  - Added focused tests for deterministic freezer IDs, rejected-candidate exclusion, invalid conditional weights, and policy-boundary validation through the existing source-scenario policy validator.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_candidate_source_zone_scenarios.py tests/test_candidate_source_zone_freezer.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_freezer tests.test_source_scenario_policy`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_scenario_stress.CandidateSourceZoneScenarioStressTests.test_deterministic_release_candidates_generate_a_large_manifest_rich_table tests.test_candidate_source_zone_scenario_stress.CandidateSourceZoneScenarioStressTests.test_missing_inputs_fail_closed`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_candidate_source_zone_scenarios.py`
  - Freeze-mode CLI smoke against a tiny synthetic review package
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: conditional scenario planning only; no physical probability, no source-frequency evidence, no calibration, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-262`

### TB-262: Prepared-Pilot Compiler From AOI Manifest

- Date: 2026-05-19
- Commit: local
- Objective: compile the AOI manifest, prepared inputs, reviewed source zones, and frozen scenario plan into one runnable prepared-pilot command plan with deterministic compiler output.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a prepared-pilot compiler mode that emits a run manifest, command plan, expected input/output inventory, output profile, Balfrin/local execution hints, and first blocker.
  - Threaded a compiler classification through the report surface so ready fixtures classify as `ready_for_local_smoke` or `ready_for_balfrin_postproc`, while missing terrain, reviewed source zones, or scenario plans classify as `blocked_missing_inputs`.
  - Added focused fixture-backed tests for the ready fixture, missing terrain, missing reviewed source zones, missing scenario plan, and deterministic command-plan shape, and documented the compiler handoff contract.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run -v`
- Result/status: implemented_fixture_backed
- Boundaries: compilation only; no live Balfrin submission, no ensemble execution, no annual-frequency semantics, no operational claim, and no heavy outputs committed.
- Next task: `TB-263`

### TB-263: Local Tiny AOI Hazard-Map Smoke Run

- Date: 2026-05-19
- Commit: local
- Objective: execute a tiny local fixture-backed AOI prepared-pilot smoke run through validation trajectory generation and hazard-layer building so the front-door workflow proves it can produce map artifacts under a temporary output root.
- Files changed: `scripts/run_aoi_hazard_workflow.py`, `tests/test_run_aoi_hazard_workflow.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a `run-local-smoke` execution path to the AOI front-door helper that rewrites the existing `probabilistic_phase1_smoke` case into a `/tmp` output root, runs `cargo run -- validate`, then rebuilds hazard layers with reduced-output controls and GIS packaging enabled.
  - Kept the smoke path clean-checkout safe by directing validation and hazard outputs into a temporary root, and by hashing only the stable reduced artifacts for the determinism check.
  - Added a regression test that runs the smoke path twice against the same temporary root and asserts required reduced trajectory outputs, hazard rasters, manifests, claim-boundary metadata, and no-heavy-debug defaults.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_local_tiny_aoi_smoke_run_writes_reduced_outputs_and_hazard_layers`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: tiny local fixture execution only; no live Balfrin submission, no operational claim, no physical-probability claim, no annual-frequency claim, no risk/exposure/vulnerability claim, and no generated heavy outputs committed.
- Next task: `TB-264`

### TB-264: Balfrin Target-Area Metrics Completion Postproc Run

- Date: 2026-05-19
- Commit: local
- Objective: submit the exact bounded target-area metrics-completion rerun on Balfrin postprocessing nodes, or record the exact fail-closed preflight blocker.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Ran the Balfrin access preflight successfully: SSH, remote checkout visibility, existing target-area run-root visibility, and scheduler query all passed; the JSON output was preserved at `/tmp/tb264_balfrin_access_preflight.json`.
  - Built the metrics-completion rerun package preflight for the exact run root `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v2`; it reported `preflight_status=ready_for_authorization_request`, `authorization_handoff_status=ready_for_authorization_review`, and `package_status=complete_rerun_package`, with JSON preserved at `/tmp/tb264_metrics_completion_package.json`.
  - Fast-forwarded the Balfrin checkout to local `main` commit `a2c4831b52e34e5b772c560ad6cc4faa65886853`, then stopped before submission because the remote checkout was not clean: untracked generated files were present in the repository root, including `command_plan.json`, `probe.sbatch`, `balfrin_submission_package.json`, timing/context sidecars, `logs/`, SLURM outputs, and scratch helper scripts.
  - No SLURM job was submitted, no job id was produced, and no run-root metrics, `sacct` fields, or preservation-gate output were promoted as evidence.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-264 --format json`
  - `rg -n "^### TB-264:" docs/task_backlog.md`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v2 --balfrin-access-json /tmp/tb264_balfrin_access_preflight.json --format json --artifact-dir /tmp/tb264_metrics_completion_package`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && git pull --ff-only origin main && git status --short --branch && git rev-parse HEAD'`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_completion_rerun_package -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: blocked_unresolved
- Boundaries: fail-closed checkout blocker only; no live Balfrin submission, no retry, no multi-zone run, no distributed execution, no scale-up, no physical-probability claim, no annual-frequency claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-265`

### TB-265: Metrics Completion Evidence Integration And Decision Refresh

- Date: 2026-05-19
- Commit: local
- Objective: integrate the TB-264 Balfrin metrics-completion result into canonical evidence reports and downstream next-action decisions without fabricating measured evidence.
- Files changed: `scripts/summarize_balfrin_probe_metrics_report.py`, `scripts/summarize_balfrin_probe_preservation_gate.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/summarize_balfrin_demonstration_closure_package.py`, `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `tests/test_balfrin_probe_metrics_report.py`, `tests/test_balfrin_probe_preservation_gate.py`, `tests/test_balfrin_demonstration_closure_package.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a canonical `metrics_completion_outcome` classification that separates `measured`, `recovered`, `blocked`, and `incomplete` from the existing source label.
  - Classified the TB-264 no-submission path as `incomplete` when a metrics-completion attempt stopped before a live SLURM job, run-root metrics, `sacct` fields, or preservation-gate output existed.
  - Propagated the outcome through the metrics report, preservation gate, evidence bundle probe-metrics section, closure package, and next live-run decision criteria.
  - Kept complete evidence ranked past the metrics-completion rerun while incomplete TB-264-style evidence remains blocked and does not promote a next measured action.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_probe_metrics_report.py scripts/summarize_balfrin_probe_preservation_gate.py scripts/summarize_balfrin_evidence_bundle.py scripts/summarize_balfrin_demonstration_closure_package.py scripts/summarize_balfrin_next_live_run_decision_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_metrics_report tests.test_balfrin_probe_preservation_gate tests.test_balfrin_demonstration_closure_package -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_next_live_run_decision_gate -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_fixture_backed
- Boundaries: evidence integration only; no live Balfrin submission, no retry, no generated heavy outputs, no physical credibility upgrade, no annual-frequency claim, no risk/exposure/vulnerability claim, no distributed-execution or scale-up claim, and no operational claim.
- Next task: `TB-266`

### TB-266: Smallest Multi-Zone Handoff Budget Repair

- Date: 2026-05-19
- Commit: `c18afd1`
- Objective: tighten the smallest multi-zone handoff so the compact projection, reducer budget, and smallest-review preflight either pass or report the exact replay-critical blocker with before/after budget evidence.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/output_budget_reducer_scaling_gate.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Kept the compact handoff projection fail-closed while threading the retained replay-critical families into the budget recheck reason so the blocker names the exact manifest-size limit and the preserved replay set.
  - Added `replay_critical_field_paths` / retained-family reporting to the compact manifest-pruning report and surfaced the before/after manifest, output-file, sidecar, and reducer-manifest counts in the smallest multi-zone preflight text report.
  - Updated the reducer-pressure and output-budget docs with the reviewed two-release-zone before/after budget envelope, then tightened the regressions so replay-critical metadata, merge order, hashes, and output-profile semantics remain required.
  - Removed TB-266 from the active backlog before recording this work-log entry.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_smallest_multi_zone_authorization_preflight`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_blocked_report
- Boundaries: handoff budget repair only; no live Balfrin submission, no loss of replayability, no distributed reducer, no physics change, and no operational claim.
- Next task: `TB-267`

### TB-267: Smallest Multi-Zone Balfrin Postproc Probe

- Date: 2026-05-19
- Commit: local
- Objective: submit the exact smallest bounded two-zone Balfrin postproc probe only if access, reviewed handoff, authorization, reducer-budget, output-profile, and preservation gates were ready; otherwise record the exact pre-submit blocker.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Ran the Balfrin access preflight successfully and preserved the JSON at `/tmp/tb267_balfrin_access_preflight.json`; SSH, remote checkout visibility, preserved target-area run-root visibility, and scheduler query all passed read-only.
  - Ran the smallest multi-zone authorization preflight with that access report and preserved JSON/text outputs at `/tmp/tb267_authorization_preflight.json` and `/tmp/tb267_authorization_preflight.txt`.
  - Stopped before submission because the preflight reported `blocked_reducer_budget`: the reviewed package hash was `0a3802882b1fefb3ee35b63962fca2befb24e4003d213bacb53fdf085a61d5e1`, Balfrin access was `ready_for_read_only_collection`, the output profile was `ready`, but the reducer budget remained blocked at first bottleneck `manifest_size_bytes`; the authorization record was also missing.
  - Recorded the exact blocker: `blocked: requested reducer_worker_count=2 reaches measured max 2; handoff output-budget projection blocked: first bottleneck manifest_size_bytes; current handoff projection remains blocked_fixture_backed at first bottleneck manifest_size_bytes; replay-critical families retained: trajectory_csv, deposition_csv, impact_events_csv, trajectory_merge_state, reducer_merge_state`.
  - No SLURM job was submitted, no job id was produced, and no metrics JSON, preservation gate, or post-run collector output was promoted as measured evidence.
  - Removed TB-267 from the active backlog before recording this work-log entry.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-267 --format json`
  - `rg -n "^### TB-267:" docs/task_backlog.md`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`
  - `PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --balfrin-access-preflight-json /tmp/tb267_balfrin_access_preflight.json --json-output /tmp/tb267_authorization_preflight.json --text-output /tmp/tb267_authorization_preflight.txt --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py --authorization-preflight /tmp/tb267_authorization_preflight.json --balfrin-access-json /tmp/tb267_balfrin_access_preflight.json --json-output /tmp/tb267_measurement_path.json --text-output /tmp/tb267_measurement_path.txt --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_authorization_gated_multi_zone_measurement_path tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: blocked_unresolved
- Boundaries: fail-closed pre-submit blocker only; no live Balfrin submission, no retry, no larger ensemble, no distributed execution, no scale-up, no annual-frequency claim, no physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-268`

### TB-268: Multi-Zone Evidence Integration And Reducer Scaling Update

- Date: 2026-05-19
- Commit: local
- Objective: integrate the TB-267 multi-zone outcome into reducer-pressure, evidence-bundle, closure, next-action, and Swiss-wide envelope helpers without promoting blocked pre-submit evidence as measured.
- Files changed: `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/summarize_balfrin_demonstration_closure_package.py`, `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `scripts/estimate_swiss_wide_execution_envelope.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`, `tests/test_balfrin_evidence_bundle.py`, `tests/test_balfrin_demonstration_closure_package.py`, `tests/test_balfrin_next_live_run_decision_gate.py`, `tests/test_swiss_wide_execution_envelope.py`
- Implementation summary:
  - Added a multi-zone Balfrin evidence classifier that distinguishes scratch reducer probes, fixture-backed roots, measured preservation-checked Balfrin roots, and blocked incomplete TB-267 pre-submit evidence.
  - Recorded the current TB-267 state as `blocked_incomplete`: no SLURM job id, no promoted metrics JSON, no preservation gate, no post-run collector output, missing authorization record, and first bottleneck `manifest_size_bytes`.
  - Wired the classifier into the evidence bundle, closure package, next live-run decision gate, and Swiss-wide envelope so the scaling frontier stays fail-closed until the reducer-budget blocker and authorization record are resolved.
  - Added tests proving a future measured two-zone root changes the scaling branch to review-only next-larger package planning while keeping `scale_up_authorized=false` and not authorizing larger runs.
  - Removed TB-268 from the active backlog before recording this work-log entry.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-268 --format json`
  - `rg -n "^### TB-268:" docs/task_backlog.md`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle tests.test_balfrin_next_live_run_decision_gate tests.test_balfrin_demonstration_closure_package tests.test_swiss_wide_execution_envelope -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `rg -n "^### TB-268:" docs/task_backlog.md` (exit 1, confirming removal)
  - `git status --short --branch`
- Result/status: implemented_blocked_report
- Boundaries: evidence integration only; no live Balfrin submission, no Swiss-wide authorization, no distributed execution, no scale-up authorization, no annual-frequency claim, no physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-269`

### TB-269: AOI Hazard Map Product Packager

- Date: 2026-05-19
- Commit: `1283656`
- Objective: package AOI hazard-layer outputs into a compact review bundle with COG rasters where available, vector overlays, checksums, a manifest, and an explicit claim boundary.
- Files changed: `scripts/package_aoi_hazard_map.py`, `tests/test_aoi_hazard_map_packager.py`, `docs/task_backlog.md`, `docs/script_inventory.md`
- Implementation summary:
  - Added a new AOI hazard-map packager CLI that consumes an existing hazard output root, converts declared GeoTIFFs to COG when possible, and falls back cleanly to a reviewable GeoTIFF package when conversion is blocked.
  - Emitted compact release-zone and scenario-table GeoJSON overlays from the committed source-zone metadata and scenario table, plus a manifest, summary text, and inventory/checksum metadata.
  - Classified package runs as `map_package_ready`, `cog_blocked`, or `blocked_missing_hazard_outputs`, and preserved claim-boundary metadata that explicitly excludes annual-frequency, physical-probability, risk, exposure, and operational claims.
  - Added focused regressions for the real fixture hazard package, missing-layer blocking, COG conversion failure fallback, and manifest/inventory consistency.
  - Removed TB-269 from the active backlog and registered the new command in the script inventory.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion tests.test_aoi_hazard_map_packager -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: packaging only; no hazard-value change, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability product, and no heavy outputs committed.
- Next task: `TB-270`

### TB-270: AOI Map QA Project And Static Review Surface

- Date: 2026-05-19
- Commit: `8823720`
- Objective: generate a lightweight AOI map QA review surface that exposes terrain, release-zone, scenario, hazard-layer, and context availability evidence without changing hazard outputs.
- Files changed: `scripts/generate_aoi_map_qa_review.py`, `tests/test_aoi_map_qa_review.py`, `docs/script_inventory.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a manifest-driven static AOI map QA review generator that writes an ignored review root with `index.html` and a JSON manifest, and keeps the review surface diagnostic rather than operational.
  - Surfaced layer-presence, claim-boundary, and warning details for missing context layers, COG-blocked rasters, fixture-backed inputs, conditional-only weights, and non-operational status.
  - Added focused regressions for layer presence, warning propagation, and blocked missing-map-package behavior, then removed TB-270 from the active backlog and registered the new generator in the script inventory.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_map_qa_review -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_map_qa_review tests.test_pilot_gis_visual_qa tests.test_balfrin_target_area_gis_cog_scope -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: QA/review surface only; no hazard-value changes, no operational claim, no physical-probability semantics, no annual-frequency semantics, no risk/exposure/vulnerability claim, and no heavy outputs committed.
- Next task: `TB-271`

### TB-271: Adaptive AOI Ensemble Convergence Controller

- Date: 2026-05-19
- Commit: `72e480d`
- Objective: add a bounded adaptive AOI convergence controller that recommends the next trajectory-count step from measured convergence and output-budget evidence instead of fixed guesses.
- Files changed: `scripts/summarize_adaptive_aoi_ensemble_convergence_controller.py`, `tests/test_adaptive_aoi_ensemble_convergence_controller.py`, `docs/task_backlog.md`, `docs/script_inventory.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only adaptive convergence controller that composes hazard-map convergence comparisons, the output-budget gate, the Balfrin ensemble frontier, and the bounded next-probe feasibility report into one controller summary.
  - The controller now classifies converged, budget-stopped, and inconclusive branches, proposes bounded trajectory-count increments with projected output budgets, and exposes a Balfrin-ready command plan only when the preflight evidence is favorable.
  - Added focused regressions for converged, budget-stopped, and inconclusive branches using fixture-backed comparisons plus a machine-readable JSON smoke path, and registered the new controller in the script inventory.
  - Removed TB-271 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_adaptive_aoi_ensemble_convergence_controller -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_map_convergence tests.test_balfrin_ensemble_frontier -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: conditional convergence only; no live Balfrin submission, no annual-frequency semantics, no physical validation claim, no operational claim, no scale-up authorization, and no distributed-execution claim.
- Next task: `TB-272`

### TB-272: End-To-End AOI-To-Map Regression Fixture

- Date: 2026-05-19
- Commit: `40dbb60`
- Objective: add a compact clean-checkout-safe regression proof for the user-facing AOI-to-map workflow.
- Files changed: `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a fixture-backed regression inside the AOI prepared-pilot dry-run tests that runs under `/tmp` and composes the AOI dry-run planner, prepared-input contract, tiny hazard-layer smoke build, map-package manifest, pilot GIS manifest, and GIS/COG readiness audit.
  - Asserted expected command states, claim-boundary fields, generated hazard outputs, map package metadata, pilot GIS QA status, and the maintained `gis_package_ready_cog_blocked` classification for non-COG fixture rasters.
  - Added a compact first-failure summary tied to the current prepared-pilot command-plan blocker so users and agents see the first broken workflow step instead of scattered helper failures.
  - Removed TB-272 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run.AoiToPreparedPilotDryRunTests.test_aoi_to_map_regression_fixture_produces_smoke_map_package_and_qa_summary`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_pilot_gis_package_manifest_records_review_artifacts_and_boundaries tests.test_hazard_layers.HazardLayerTests.test_fixture_layers_are_reproducible_and_interpretable`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: fixture-backed regression only; generated outputs were written under `/tmp`; no live Balfrin submission, no real public-geodata download, no operational claim, and no heavy outputs committed.
- Next task: `TB-273`

### TB-273: Optional Observed-Evidence Overlay Hook For AOI Maps

- Date: 2026-05-19
- Commit: `0fea046`
- Objective: allow AOI map packages to carry optional observed-evidence overlays while keeping calibration, annual-frequency, risk, and operational claims out of scope.
- Files changed: `scripts/package_aoi_hazard_map.py`, `tests/test_aoi_hazard_map_packager.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an optional overlay hook to the AOI packager that accepts either a real staged observed runout/deposition benchmark or a field-supported release-zone provenance record and emits explicit blocked statuses for missing, fixture-only, or schema-gap inputs.
  - Extended the AOI package manifest with role-separated sections for diagnostic hazard outputs, observed evidence overlays, calibration inputs, holdout evidence, and deferred source-frequency records, plus summary lines that expose the overlay hook state.
  - Added regressions covering accepted real evidence, fixture-only observed evidence, and ambiguous mixed-provenance release-zone evidence so the new package path cannot silently upgrade non-accepted inputs into physical validation.
  - Removed TB-273 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_hazard_map_packager -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_physical_credibility_evidence_requirements -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: optional overlay integration only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no operational claim, and no claim upgrade beyond accepted evidence.
- Next task: backlog refill needed

### TB-274: AOI Workflow Guided Prepare Mode

- Date: 2026-05-19
- Commit: `5465dcf`
- Objective: add a guided front-door prepare mode that walks the AOI bootstrap, product resolution, cache verification, terrain preparation, release-candidate planning, and scenario-freeze readiness steps in dependency order without changing scientific claims or introducing live compute.
- Files changed: `scripts/run_aoi_hazard_workflow.py`, `tests/test_run_aoi_hazard_workflow.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a dedicated `prepare` report path to the AOI front door that composes the existing bootstrap, acquisition, cache verification, terrain-preparation, release-candidate planning, and scenario-freeze readiness helpers into one ordered dependency chain.
  - Surfaced a compact JSON/text summary with ordered step statuses, the next exact command, the expected input path, the first actionable blocker, and claim-boundary notes so users can stop at the right helper instead of inferring the workflow.
  - Reworked the test fixture config to point at the temporary repo roots used by the tests, then added fixture-backed regressions for the clean-checkout blocker, a partially prepared path, and a ready-for-planning path.
  - Removed TB-274 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow -v`
- Result/status: completed
- Boundaries: guided preparation only; no network download, no simulation, no live Balfrin submission, no physical-probability semantics, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.
- Next task: `TB-275`

### TB-275: Public Geodata Local Staging Wizard

- Date: 2026-05-19
- Commit: `cd10985`
- Objective: add a local staging wizard that matches caller-supplied swisstopo files or directories to the AOI cache manifest, writes a dry-run proposal first, and only applies manifest updates after the proposal is clean.
- Files changed: `scripts/stage_public_geodata_cache.py`, `tests/test_public_geodata_cache_stager.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a wizard mode to the public-geodata staging helper with explicit local-path and scan-root inputs, proposal output writing, and an optional apply step that only mutates the manifest after the proposal is ready.
  - Added deterministic candidate matching for file and directory inputs, including sibling metadata discovery, fail-closed ambiguous-match handling, missing-metadata detection, and optional-deferred classification.
  - Extended the stager tests with fixture-backed dry-run/apply coverage, missing-metadata failure coverage, and ambiguous directory-match coverage while keeping the verifier regressions intact.
  - Removed TB-275 from the active backlog after the implementation commit landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_stager tests.test_public_geodata_cache_verifier -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/stage_public_geodata_cache.py scripts/verify_public_geodata_cache.py tests/test_public_geodata_cache_stager.py tests/test_public_geodata_cache_verifier.py`
  - `git diff --check`
- Result/status: completed
- Boundaries: local file staging only; no network download, no simulation, no source-frequency semantics, no physical validation claim, no operational claim, and no heavy public geodata committed.
- Next task: `TB-276`

### TB-276: Real AOI Golden Fixture Package

- Date: 2026-05-19
- Commit: to be recorded
- Objective: add a compact clean-checkout-safe AOI regression fixture package with minimized public-data-like metadata and explicit regression-only labeling.
- Files changed: `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/README.md`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/aoi_manifest.yaml`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml`, `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv`, `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`, `tests/test_aoi_golden_fixture_package.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a committed AOI regression fixture package under `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/` with an AOI manifest, cache manifest, tiny terrain crop, terrain metadata, AOI tile catalog, source-zone metadata, scenario table, and regression-only policy labels.
  - Added a dedicated integration test that copies the fixture package into a temporary clean checkout and exercises bootstrap, cache verification, prepared-input building, command planning, tiny smoke hazard packaging, and QA review without ignored local state.
  - Updated the preparation docs to point at the new regression fixture package and removed TB-276 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_golden_fixture_package tests.test_aoi_terrain_preprocessing`
- Result/status: completed
- Boundaries: fixture/regression only; no heavy data, no live Balfrin submission, no physical credibility claim, no annual-frequency semantics, no operational claim, and no real-world hazard product.
- Next task: `TB-277`

### TB-277: AOI Front-Door Status UX Tightening

- Date: 2026-05-19
- Commit: to be recorded
- Objective: normalize the AOI front-door `status` output so text and JSON modes surface stable, directly actionable fields without helper-vocabulary noise.
- Files changed: `scripts/run_aoi_hazard_workflow.py`, `tests/test_run_aoi_hazard_workflow.py`, `README.md`, `docs/onboarding.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a normalized `status`-mode front-door report with explicit `workflow_status`, `next_action`, `first_blocker`, `next_command`, `expected_inputs`, `expected_outputs`, and `claim_boundaries` fields.
  - Classified malformed site config and unsupported-command state as invalid input, and reserved a separate internal-error exit path for unexpected failures.
  - Kept the detailed helper reports available for existing callers while tightening the user-facing text and JSON output to the concise status surface.
  - Updated onboarding and README guidance, removed TB-277 from the active backlog, and added focused tests for ready, blocked, invalid-input, and unsupported-command status paths.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_status_main_renders_concise_text_and_json_for_ready_report tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_status_main_reports_blocked_missing_inputs_in_text_and_json tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_status_main_rejects_invalid_site_config_with_exit_code_64 tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_status_build_report_marks_unsupported_command_state_as_invalid_input tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_clean_checkout_status_reports_the_first_blocker_and_prepare_next_step`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow`
- `git diff --check`
- `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
- `scripts/git-hooks/pre-commit`
- `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- `git status --short`
- Result/status: completed
- Boundaries: UX/status normalization only; no simulation, no live Balfrin submission, no claim upgrade, and no heavy outputs committed.
- Next task: `TB-278`

### TB-278: AOI Release Candidate Review Editing Loop

- Date: 2026-05-19
- Commit: local
- Objective: add a deterministic review-apply command for release-zone candidate packages and validate the edited review state before freezing.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/generate_candidate_source_zone_scenarios.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_candidate_source_zone_freezer.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a review-apply mode to the terrain candidate planner that applies explicit candidate decisions, rewrites the reviewed package outputs, and validates unknown IDs, unreviewed accepted candidates, mixed-provenance overclaims, empty accepted sets, and allowed provenance labels.
  - Required the freezer mode to consume only review-applied packages whose review application is validated, then freeze only the validated accepted candidates.
  - Added focused regression coverage for successful review application, each blocking diagnostic, and the freezer path that consumes the validated accepted review package.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/generate_candidate_source_zone_scenarios.py tests/test_plan_terrain_release_zone_candidates.py tests/test_candidate_source_zone_freezer.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates tests.test_candidate_source_zone_freezer`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: review editing and validation only; no physical source validation claim, no calibration, no annual-frequency semantics, no operational claim, and no heavy outputs committed.
- Next task: `TB-279`

### TB-279: AOI Scenario Preview And Cost Estimate

- Date: 2026-05-19
- Commit: local
- Objective: add a pre-execution AOI scenario preview that reports source-zone / block-family / scenario-family rows, projected runtime and storage pressure, and the local-vs-Balfrin execution target.
- Files changed: `scripts/preview_aoi_scenario_cost_estimate.py`, `tests/test_aoi_scenario_preview.py`, `tests/fixtures/aoi_scenario_preview/tiny_review_package.yaml`, `tests/fixtures/aoi_scenario_preview/multi_zone_review_package_a.yaml`, `tests/fixtures/aoi_scenario_preview/multi_zone_review_package_b.yaml`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated AOI preview helper that consumes reviewed candidate packages, freezes them through the existing candidate-source-zone workflow, classifies the output profile, and projects per-row and aggregate runtime/storage pressure with measured-envelope helpers.
  - Fail-closed paths now explicitly label missing reviewed candidates, unknown trajectory budget, unsupported output profile, and projected output-budget overflow.
  - Added tiny and multi-zone preview fixtures plus regression coverage for local-smoke readiness, multi-zone aggregation, and the blocked edge cases.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_scenario_preview`
  - `PYENV_VERSION=system uv run python scripts/preview_aoi_scenario_cost_estimate.py --review-package tests/fixtures/aoi_scenario_preview/tiny_review_package.yaml --format text`
- Result/status: completed
- Boundaries: preview and estimation only; no live Balfrin submission, no simulation, no distributed execution, no scale-up authorization, and no physical-probability semantics.
- Next task: `TB-280`

### TB-280: Prepared-Pilot Local Execution Wrapper

- Date: 2026-05-19
- Commit: local
- Objective: add one local bounded execution command that consumes a ready prepared-pilot report, runs the bounded validation case, packages the hazard layers, and emits the static QA review under a caller-provided output root.
- Files changed: `scripts/run_aoi_hazard_workflow.py`, `tests/test_run_aoi_hazard_workflow.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a `run-prepared-pilot-local` front-door command that validates a prepared-pilot report, enforces an allowed output-root policy, runs the bounded smoke validation, packages the hazard outputs, and generates the QA review surface.
  - Kept the local execution bounded by reusing the existing tiny smoke case defaults and recorded manifest checksums plus first-failure details for each stage.
  - Added regression coverage for the successful prepared-pilot path, the overwrite/output-root guard, and the existing tiny smoke execution path.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/run_aoi_hazard_workflow.py tests/test_run_aoi_hazard_workflow.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run.AoiToPreparedPilotDryRunTests.test_ready_compiler_fixture_emits_manifest_plan_and_hints`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_local_tiny_aoi_smoke_run_writes_reduced_outputs_and_hazard_layers tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_prepared_pilot_local_execution_writes_validation_hazard_package_and_review tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_prepared_pilot_local_execution_blocks_overwrite_and_reports_first_failure`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: completed
- Boundaries: local bounded execution only; no live Balfrin submission, no large AOI execution, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability product, and no heavy outputs committed.
- Next task: `TB-281`

### TB-281: AOI Map Package Openable Review Bundle

- Date: 2026-05-19
- Commit: local
- Objective: turn the AOI map package into a single openable static review bundle with layer toggles, legends, warnings, provenance, and claim-boundary text.
- Files changed: `scripts/generate_aoi_map_qa_review.py`, `scripts/package_aoi_hazard_map.py`, `tests/test_aoi_hazard_map_packager.py`, `tests/test_aoi_map_qa_review.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the AOI QA review renderer into a richer static bundle with toggled sections for diagnostic hazard layers, release/scenario overlays, optional observed evidence, missing context, provenance, and non-operational claim boundaries.
  - Wired the AOI packager to emit the review surface into the package root so `index.html` is the direct entrypoint for package inspection.
  - Added regression coverage for the package entrypoint, generated file inventory, overlay state, warning text, and claim-boundary wording.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_hazard_map_packager tests.test_aoi_map_qa_review -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: review artifact only; no hazard-value changes, no physical validation claim, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability semantics, and no heavy outputs committed.
- Next task: `TB-282`

### TB-282: Balfrin Remote Checkout Hygiene Gate

- Date: 2026-05-19
- Commit: local
- Objective: add a read-only Balfrin pre-submit hygiene gate that detects dirty remote checkout state before any future SLURM attempt.
- Files changed: `scripts/check_balfrin_remote_access_preflight.py`, `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`, `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `tests/test_balfrin_probe_driver.py`, `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Balfrin access preflight with a read-only remote checkout hygiene check that records remote branch/HEAD, tracked modifications, untracked generated files, stale submission packages, stale logs, and exact preserve/inspect/clean commands.
  - Kept the gate fail-closed as `blocked_dirty_remote_checkout` and propagated the hygiene payload into the target-area metrics-completion and smallest multi-zone authorization preflight requirements.
  - Added synthetic remote-status regression coverage for clean, dirty, metrics-completion blocked, and multi-zone blocked pre-submit paths.
- Checks run:
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-282 --format json`
  - `rg -n "^### TB-282:" docs/task_backlog.md`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_balfrin_remote_access_preflight.py scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_target_area_metrics_completion_rerun_package tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: completed
- Boundaries: read-only hygiene/preflight only; no remote deletion, no live Balfrin submission, no SLURM job, no scale-up authorization, no operational claim, no annual-frequency semantics, no physical-probability claim, and no risk/exposure/vulnerability product.
- Next task: `TB-283`

### TB-283: Balfrin Metrics-Completion Rerun Reattempt Package

- Date: 2026-05-19
- Commit: local
- Objective: refresh the exact target-area metrics-completion rerun package and preserve either the authorized submission result or the exact fail-closed blocker.
- Files changed: `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`, `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `post_attempt_integration_notes` to the metrics-completion rerun package so downstream integration can distinguish `submitted`, `blocked_pre_submit`, `failed_closed`, and `no_authorization` without promoting incomplete evidence.
  - Refreshed the read-only Balfrin access preflight and package under `/tmp/tb283_metrics_completion_package`; the measured state is `preflight_status=blocked_dirty_remote_checkout`, `post_attempt_status=blocked_pre_submit`, and exact remaining precondition `blocked_dirty_remote_checkout`.
  - Preserved the package hashes in the `/tmp` report: command plan `0d564cf7bc2ffab4d31b8b1f3fc78b8e9424c53700d1367c3ed33710ec3e68f8`, SBATCH script `0dcd75fe7fbbed17e5dce3e0180a55cbe395ff3ffd345660cecd3c4032cc5d1f`.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-283 --format json`
  - `rg -n "^### TB-283:" docs/task_backlog.md`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py tests/test_balfrin_target_area_metrics_completion_rerun_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_metrics_completion_rerun_package -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb283_balfrin_access_preflight.json` (exit 2, expected fail-closed blocker)
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py --balfrin-access-json /tmp/tb283_balfrin_access_preflight.json --format json --artifact-dir /tmp/tb283_metrics_completion_package` (exit 2, expected fail-closed package)
- Result/status: implemented_blocked_report
- Boundaries: read-only package refresh only; no `sbatch`, no live Balfrin submission, no remote cleanup, no retry, no multi-zone or distributed execution, no operational claim, no annual-frequency semantics, no physical-probability claim, and no risk/exposure/vulnerability product.
- Next task: `TB-284`

### TB-284: Metrics Recovery Integration Refresh

- Date: 2026-05-19
- Commit: local
- Objective: integrate recovered, rerun, missing, and pre-submit-blocked target-area metrics states consistently across the Balfrin evidence bundle, closure package, decision gate, and maturity snapshot.
- Files changed: `scripts/summarize_balfrin_probe_metrics_report.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/summarize_balfrin_demonstration_closure_package.py`, `scripts/summarize_balfrin_next_live_run_decision_gate.py`, `tests/test_balfrin_evidence_bundle.py`, `tests/test_balfrin_demonstration_closure_package.py`, `tests/test_balfrin_next_live_run_decision_gate.py`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `blocked_pre_submit` to the target-area metrics completion classifier path and carried a normalized metrics evidence state through the evidence bundle and closure section.
  - Propagated peak memory, split validation/hazard file counts and bytes, run-root hashes, SLURM fields, and preservation status when supplied.
  - Updated the next live-run decision gate so pre-submit-blocked metrics fail closed with exact blockers instead of being treated as recovered evidence or a ready rerun gap.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-284 --format json`
  - `rg -n "^### TB-284:" docs/task_backlog.md`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json` (exit 2, expected fail-closed dirty remote checkout)
  - `PYENV_VERSION=system uv run python tests/test_balfrin_evidence_bundle.py`
  - `PYENV_VERSION=system uv run python tests/test_balfrin_next_live_run_decision_gate.py`
  - `PYENV_VERSION=system uv run python tests/test_balfrin_demonstration_closure_package.py`
- Result/status: implemented_measured
- Boundaries: evidence integration only; no `sbatch`, no live Balfrin submission, no new run, no remote cleanup, no claim upgrade beyond execution-metric completeness, no annual-frequency semantics, and no operational, risk, exposure, vulnerability, distributed-execution, scale-up, or physical-probability claim.
- Next task: `TB-285`

### TB-285: Reducer Manifest Budget Compression

- Date: 2026-05-19
- Commit: local
- Objective: compress the smallest multi-zone handoff report so it keeps replay-critical metadata, hashes, merge-order proof, and output-profile semantics while reporting the exact remaining blocker.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Collapsed the multi-zone manifest-pruning report into a compact contract with prefix-based replay-critical field inventories, retained family lists, merge-order proof, output-profile semantics, and before/after evidence for manifest bytes, sidecar counts, reducer-manifest counts, and output file counts.
  - Removed redundant top-level projection copies from the package report and kept the smallest-run summary on the canonical follow-up path, cutting the package JSON size while preserving the replay-critical blocker evidence.
  - Expanded the smallest-multi-zone preflight to surface the compact replay-critical contract and the reducer-manifest file-count evidence while continuing to fail closed on the manifest-size blocker.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-285 --format json`
  - `rg -n "^### TB-285:" docs/task_backlog.md`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_smallest_multi_zone_authorization_preflight`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: implemented_blocked_report
- Boundaries: handoff and budget compression only; no live Balfrin submission, no `sbatch`, no dropped replayability, no distributed reducer, no physics change, no scale-up authorization, and no operational claim.
- Next task: `TB-286`

### TB-286: Smallest Multi-Zone Authorization Package Refresh

- Date: 2026-05-19
- Commit: local
- Objective: refresh the smallest two-zone Balfrin authorization package after reducer-budget compression and preserve a clean user-review record before any live job.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Rebound the handoff command-plan budget projection to the requested two-zone authorization shape instead of the older 12-zone pressure command, while keeping the measured 12-zone scratch probe as the reducer constraint source.
  - Refreshed the package under `/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1`; reviewed package hash is `9662e86553962284bfeedf27d9d8f40f57837da5c51a8ff26d08d165aedef2a1`, reducer budget is `ready`, output profile is `ready`, and the two-zone projection reports `budget_passes_no_reduction_needed`.
  - Updated `validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml` with exact run shape, output profile, reducer budget, package hash, authorization-record path, remote hygiene state, and `/tmp` JSON/text summary paths.
  - Preserved fail-closed blockers distinctly: Balfrin access is currently `blocked_dirty_remote_checkout`, the authorization record is missing, and no submit command was executed.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-286 --format json`
  - `rg -n "^### TB-286:" docs/task_backlog.md`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py scripts/check_balfrin_remote_access_preflight.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_smallest_multi_zone_authorization_preflight tests.test_balfrin_authorization_gated_multi_zone_measurement_path -v`
  - `PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --format json --json-output /tmp/tb286_handoff_package.json --text-output /tmp/tb286_handoff_package.txt`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb286_balfrin_access_preflight.json` (exit 2, expected dirty-remote blocker)
  - `PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --balfrin-access-preflight-json /tmp/tb286_balfrin_access_preflight.json --json-output /tmp/tb286_authorization_preflight.json --text-output /tmp/tb286_authorization_preflight.txt --format json` (exit 2, expected access blocker)
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py --authorization-preflight /tmp/tb286_authorization_preflight.json --balfrin-access-json /tmp/tb286_balfrin_access_preflight.json --json-output /tmp/tb286_measurement_path.json --text-output /tmp/tb286_measurement_path.txt --format json` (exit 2, expected pre-authorization blocker)
- Result/status: implemented_blocked_report
- Boundaries: authorization package only; no `sbatch`, no live Balfrin submission, no remote cleanup, no scale-up, no distributed execution, no annual-frequency semantics, no physical-probability claim, no operational claim, and no risk/exposure/vulnerability product.
- Next task: `TB-287`

### TB-287: Smallest Multi-Zone Balfrin Probe

- Date: 2026-05-19
- Commit: local
- Objective: execute or fail closed on the exact smallest bounded two-zone Balfrin postproc probe after authorization, access, budget, and preservation gates.
- Files changed: `docs/balfrin_probe_slurm_driver.md`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Did not run `--authorized-submit`, `sbatch`, or any live Balfrin submission because the current prompt did not contain separate exact user authorization for the two-zone submit.
  - Ran only read-only/preflight checks and recorded the helper's exact current pre-submit blocker: Balfrin access is `blocked_dirty_remote_checkout`, with no tracked remote modifications but untracked generated run files, SLURM logs, and scratch helper scripts in the Balfrin checkout.
  - Confirmed the smallest authorization preflight remains fail-closed with `preflight_status=blocked_access`; reducer budget and output profile are `ready`, the authorization record is `missing`, `submit_command_executed=false`, and no measured multi-zone result was promoted.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-287 --format json`
  - `rg -n "^### TB-287:" docs/task_backlog.md`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb287_balfrin_access_preflight.json` (exit 2, expected dirty-remote blocker)
  - `PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --balfrin-access-preflight-json /tmp/tb287_balfrin_access_preflight.json --json-output /tmp/tb287_authorization_preflight.json --text-output /tmp/tb287_authorization_preflight.txt --format json > /tmp/tb287_authorization_preflight.stdout` (exit 2, expected access blocker)
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py --authorization-preflight validation/pilot_runs/balfrin_smallest_multi_zone_authorization_preflight_v1.yaml --format json > /tmp/tb287_authorization_gated_path.json` (exit 2, expected pre-authorization blocker)
  - `PYENV_VERSION=system uv run python -m py_compile scripts/submit_balfrin_probe.py scripts/collect_balfrin_probe_metrics.py scripts/summarize_balfrin_probe_preservation_gate.py scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_smallest_multi_zone_authorization_preflight tests.test_balfrin_authorization_gated_multi_zone_measurement_path -v`
  - `rg -n "^### TB-287:" docs/task_backlog.md` (exit 1, expected absent after completion)
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: implemented_blocked_report
- Boundaries: exact smallest two-zone probe gate only; no `sbatch`, no live Balfrin submission, no retry, no larger ensemble, no remote cleanup, no scale-up, no distributed execution, no annual-frequency semantics, no physical-probability claim, no operational claim, and no risk/exposure/vulnerability product.
- Next task: `TB-288`

### TB-288: Real Chant Sura Core Input Staging Pass

- Date: 2026-05-19
- Commit: local
- Objective: preserve the first unresolved real Chant Sura core-input blocker in the readiness gate, starting from the live terrain metadata / AOI catalog row order, and keep the acquisition handoff fail-closed without inventing staged evidence.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Updated the Chant Sura readiness gate so partial-real core-input states preserve the first unresolved local row instead of collapsing to a vague `defer_second_site` handoff.
  - The live repo-root report now names `terrain_metadata.yaml` as the first unresolved real core input, marks it `fixture_backed`, and keeps the next action as `stage_local_existing_input` with the expected metadata contract.
  - Aligned the focused gate test fixture with the live partial-real shape by staging only the terrain crop and leaving terrain metadata and the AOI catalog fixture-backed, which keeps the blocker order deterministic.
  - Recorded the blocker explicitly in the Chant Sura acquisition decision note and removed TB-288 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-288 --format json`
  - `rg -n "^### TB-288:" docs/task_backlog.md`
  - `git pull --ff-only origin main`
  - `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate.ChantSuraRealContextReadinessGateTests.test_partial_real_inputs_block_second_site_readiness tests.test_chant_sura_real_context_readiness_gate.ChantSuraRealContextReadinessGateTests.test_fixture_backed_minimal_inputs_block_second_site_readiness`
- Result/status: implemented_blocked_report
- Boundaries: real-input staging/rejection only; no synthetic upgrade to real readiness, no second-site ensemble execution, no live Balfrin submission, no physical validation claim, and no operational claim.
- Next task: `TB-289`

### TB-289: Physical Evidence Overlay Acquisition Pass

- Date: 2026-05-19
- Commit: `ea4c7a7`
- Objective: add an explicit observed-runout/deposition acquisition review surface and keep the AOI overlay intake fail-closed unless real benchmark evidence is staged.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an `acquisition_review_report` that packages the observed intake's geometry, provenance, licensing, uncertainty, role, and claim-boundary fields into one explicit rejection/acceptance surface.
  - Kept the AOI map packager gate unchanged in behavior and verified the existing overlay path still accepts real intake evidence while blocking fixture-only and ambiguous-role packages.
  - Extended the focused intake tests to assert the blocked and ready shapes of the new acquisition review report, then removed TB-289 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_aoi_hazard_map_packager -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_observed_runout_deposition_intake_contract.py tests/test_observed_runout_deposition_intake_contract.py scripts/package_aoi_hazard_map.py tests/test_aoi_hazard_map_packager.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_blocked_report
- Boundaries: acquisition/rejection only; no calibration, no parameter fitting, no physical-probability product, no annual-frequency semantics, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-290`

### TB-290: AOI End-To-End User Documentation Smoke

- Date: 2026-05-19
- Commit: local
- Objective: write a short user-facing AOI walkthrough from bounds to a local diagnostic review bundle, and verify the documented command chain stays aligned with the supported CLI and blocked states.
- Files changed: `README.md`, `docs/onboarding.md`, `docs/public_real_site_geodata_preparation.md`, `tests/test_run_aoi_hazard_workflow.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Rewrote the AOI-to-map review path in the public geodata preparation guide as a concise command sequence from `bootstrap_aoi_manifest.py` through `run_aoi_hazard_workflow.py status`, `prepare`, and `run-local-smoke`, then into `package_aoi_hazard_map.py` for the local review bundle.
  - Added the direct-script import-prefix note to onboarding so the documented commands are runnable from the repository root without guessing why sibling imports fail.
  - Added a focused command-chain smoke test that bootstraps a temp AOI manifest from bounds, checks the documented blocked states, runs the local smoke path, and packages the smoke hazard root into the review surface with `cog_blocked` / `review_ready_with_warnings`.
  - Removed TB-290 from the active backlog after the walkthrough and smoke coverage were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_run_aoi_hazard_workflow.RunAoiHazardWorkflowTests.test_documented_aoi_bounds_to_review_map_command_chain_smoke -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: documentation and command smoke only; no new scientific claims, no live Balfrin submission, no network download, no heavy generated outputs committed, no annual-frequency semantics, no physical-probability claim, and no operational claim.
- Next task: `TB-291`

### TB-291: Workflow Surface Consolidation Review

- Date: 2026-05-19
- Commit: local
- Objective: consolidate duplicated AOI/Balfrin path handling and blocked-report assembly without changing public CLI schemas.
- Files changed: `scripts/lib/workflow_validation.py`, `scripts/package_aoi_hazard_map.py`, `scripts/check_chant_sura_real_context_readiness_gate.py`, `tests/test_workflow_validation_helpers.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `resolve_optional_repo_path` to the shared workflow-validation helpers and used it in the AOI packager and Chant Sura readiness gate instead of keeping separate optional-path resolvers.
  - Routed the AOI packager's blocked-hazard-output report through the shared `build_blocked_report` helper so its blocked shape stays aligned with the rest of the workflow surface.
  - Added focused helper coverage for the new optional-path resolver and verified the touched scripts still compile and pass their unit slice.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_workflow_validation_helpers tests.test_aoi_hazard_map_packager tests.test_chant_sura_real_context_readiness_gate`
  - `PYENV_VERSION=system uv run python -m compileall scripts/lib/workflow_validation.py scripts/package_aoi_hazard_map.py scripts/check_chant_sura_real_context_readiness_gate.py tests/test_workflow_validation_helpers.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: path and blocked-report consolidation only; no CLI schema change, no broader workflow rewrite, no live Balfrin submission, no claim upgrade, no operational claim, and no annual-frequency or physical-probability claim.
- Next task: `TB-292`

### TB-292: Balfrin Scale Readiness Baseline Matrix

- Date: 2026-05-19
- Commit: `9cc8f8d`; never leave `pending` in a pushed commit.
- Objective: establish one authoritative Balfrin scale-readiness baseline matrix that names the current measured, blocked, and projection-only tier state in one read-only report.
- Files changed: `scripts/summarize_balfrin_scale_readiness_matrix.py`, `tests/test_balfrin_scale_readiness_matrix.py`, `docs/task_backlog.md`, `docs/script_inventory.md`
- Implementation summary:
  - Added a read-only scale-readiness matrix helper that composes the current single-job evidence, the exact target-area authorization package, the smallest multi-zone blocked preflight, and the Swiss-wide projection into one four-tier report.
  - Exposed explicit columns for file count, bytes, manifest bytes, reducer sidecars, runtime, memory, run-root preservation, replayability, and authorization status, plus top-level measured, blocked, projection, and no-go tier summaries.
  - Added a focused regression that checks the single-zone, target-area, smallest multi-zone, and larger-AOI rows stay aligned with the existing fixture-backed and blocked-preflight evidence.
  - Removed TB-292 from the active backlog and registered the new helper in the script inventory so consistency checks stay green.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_scale_readiness_matrix -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_scale_readiness_matrix.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: read-only synthesis only; no live Balfrin submission, no new run, no scale-up authorization, no distributed execution, no physical-probability semantics, and no operational claim.
- Next task: `TB-293`

### TB-293: Multi-Zone Output Budget Acceptance Thresholds

- Date: 2026-05-19
- Commit: local
- Objective: convert multi-zone output-budget blockers into explicit acceptance thresholds for the smallest live Balfrin probe and the next larger review-only probe.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`, `docs/output_budget_reducer_scaling_gate.md`, `docs/hazard_output_profile_contract.md`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `balfrin_multi_zone_output_budget_acceptance_v1` thresholds to the handoff package for the two-zone live-review profile and the four-zone review-only profile, including manifest bytes, total files, sidecars, reducer manifests, reducer chunks, per-family file counts, replay-critical families, and package hashes.
  - Added output-budget acceptance validation that reports each exceeded threshold with measured value, limit, excess, and `compressible` or `replay_critical` classification.
  - Surfaced the validation in the smallest multi-zone authorization preflight and added `--validation-mode budget-thresholds` for budget-only review that stays distinct from authorization and Balfrin access blockers.
  - Removed TB-293 from the active backlog and documented the acceptance profiles in the output-budget and multi-zone contracts.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py tests/test_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff tests.test_balfrin_smallest_multi_zone_authorization_preflight -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_fixture_backed
- Boundaries: budget contract only; no compression implementation, no live Balfrin submission, no scale-up authorization, no dropped replayability, no distributed execution, no annual-frequency or physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.
- Next task: `TB-294`
