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

### TB-192: Backlog And Command-Plan Reference Integrity Checker

Goal: Add an automated integrity check that fails when active backlog `Inspect first` paths or generated command-plan script references point at files that do not exist.

Capability gap reduced: Worker autonomy and orchestration reliability when docs, backlog entries, and command-plan helpers drift apart.

Why this outranks alternatives: A stale reference can misdirect the next worker before any scientific or engineering task begins, so the repo needs a cheap fail-fast guard before adding more workflow surface.

Inspect first:

- `docs/task_backlog.md`
- `scripts/check_repo_consistency.py`
- `scripts/print_agent_task_context.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A repository-consistency check that verifies every active backlog `Inspect first` file path exists unless it is explicitly marked as an external or generated scratch path.
- A command-plan reference audit that verifies script paths emitted by tracked command-plan and handoff helpers resolve to tracked repository scripts.
- Focused tests covering a valid backlog, a missing inspect-first path, and a stale command-plan script reference.
- A short note in the backlog protocol or agent guidance explaining that new tasks must use resolvable inspect-first paths.

Definition of done:

- `scripts/check_repo_consistency.py` fails on stale active-backlog and command-plan script references, focused tests pass, and the existing active backlog validates cleanly.

Boundaries: No task execution, no command-plan regeneration requirement, no generated artifact commit, and no broad documentation rewrite.

### TB-193: Clean-Checkout Reproducibility Blocked-Report Mode

Goal: Provide a deterministic clean-checkout mode that proves key readiness and evidence helpers fail closed with explicit blocked reports when ignored local artifacts are absent.

Capability gap reduced: Hidden dependence on local ignored roots, mounted Balfrin run roots, and staged swisstopo artifacts.

Why this outranks alternatives: Current maturity claims are disciplined, but reviewers correctly identified that large ignored roots can masquerade as repository readiness unless missing-artifact behavior is tested directly.

Inspect first:

- `scripts/check_same_scale_artifact_readiness.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_target_area_evidence_bundle.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `tests/test_agent_task_context.py`
- `.gitignore`

Deliverables:

- A clean-checkout test or helper mode that runs selected readiness/evidence helpers against an isolated temporary root with ignored artifact directories absent.
- Deterministic blocked-report assertions for missing same-scale artifacts, missing Balfrin run roots, and missing second-site public-context inputs.
- A compact report that lists which maturity evidence is tracked, fixture-backed, ignored-local, or unavailable in a clean checkout.
- Documentation of the command workers should run before treating local readiness as measured evidence.

Definition of done:

- The clean-checkout mode is reproducible without local ignored artifacts, focused tests cover the blocked paths, and no helper reports `ready` solely because a default or empty local path was accepted.

Boundaries: No public-data download, no Balfrin access requirement, no deletion of local ignored artifacts, no new evidence claim, and no generated heavy outputs committed.

### TB-194: Shared Python Workflow Utility Extraction

Goal: Extract duplicated Python workflow utilities for YAML/JSON loading, path normalization, checksums, required-field validation, claim-boundary scanning, and status rendering into one shared module.

Capability gap reduced: Validator and workflow-script drift caused by repeated local implementations of the same safety and parsing rules.

Why this outranks alternatives: Claim-boundary and schema helpers are correctness logic; duplicated copies across validators make future scientific-safety fixes easy to miss.

Inspect first:

- `scripts/validate_source_frequency_evidence.py`
- `scripts/validate_block_release_probability_evidence.py`
- `scripts/validate_scalable_conditional_target_gate.py`
- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/check_repo_consistency.py`
- `tests/test_source_frequency_evidence.py`

Deliverables:

- A small shared Python module under a repository-local package or `scripts/lib/` with stable helpers for common loading, path, checksum, `require_*`, and claim-boundary checks.
- Migration of at least six high-overlap validator scripts to the shared helpers without changing their CLI behavior or output schemas.
- Focused tests for the shared helpers plus regression coverage showing migrated validators still accept and reject the existing fixtures.
- A short migration note naming which helper patterns remain intentionally script-local.

Definition of done:

- Duplicate helper implementations are removed from the migrated validators, all migrated validator tests pass, and scripts remain runnable through `PYENV_VERSION=system uv run python ...`.

Boundaries: Bounded extraction only; no framework rewrite, no schema redesign, no behavior change to claim boundaries, and no mass migration of every script in one task.

### TB-195: Hazard-Layer Writer And Manifest Module Split

Goal: Split the lowest-risk output writer and manifest/report generation responsibilities out of `scripts/build_hazard_layers.py` while preserving CLI behavior and generated artifact schemas.

Capability gap reduced: Hazard-layer maintainability and scaling risk from a single monolithic post-processing script.

Why this outranks alternatives: The hazard builder is now an accidental platform; extracting writers and manifests first creates a stable seam without changing reducer math, probability semantics, or raster values.

Inspect first:

- `scripts/build_hazard_layers.py`
- `tests/test_hazard_layers.py`
- `docs/hazard_layers.md`
- `docs/hazard_output_profile_contract.md`
- `docs/hazard_throughput_bottleneck_report.md`

Deliverables:

- One or more focused modules for CSV/ASCII/GeoTIFF/COG writer helpers, manifest assembly, and text/HTML report rendering.
- Direct module-level tests for writer and manifest helpers, with existing CLI tests still covering end-to-end compatibility.
- A before/after behavior check on representative hazard-layer fixtures confirming raster summaries, manifests, checksums, and report fields are unchanged.
- A follow-up note identifying the next safe split target, if any.

Definition of done:

- `scripts/build_hazard_layers.py` delegates writer/manifest/report responsibilities to focused modules, existing hazard-layer tests pass, and generated schemas remain byte- or field-compatible where deterministic.

Boundaries: No reducer redesign, no probability-semantics change, no output-profile default change, no large fixture regeneration, and no GIS/COG claim upgrade.

### TB-196: Explicit Missing-Data Validity Semantics In Validation Metrics

Goal: Replace silent zero or empty fallback behavior in validation metrics and summary parsing with explicit validity flags, warnings, or structured failures.

Capability gap reduced: Scientific review risk from missing or malformed evidence appearing as valid numeric zeroes.

Why this outranks alternatives: Validation summaries influence scientific conclusions; empty observations, malformed sidecars, and missing count maps must be distinguishable from real zero-valued results.

Inspect first:

- `src/validation/metric_math.rs`
- `src/validation.rs`
- `src/validation/metrics.rs`
- `tests/physics.rs`
- `tests/config_io_terrain.rs`
- `docs/validation_data_schema.md`

Deliverables:

- Metric helpers or call sites that distinguish empty input, malformed JSON sidecars, and missing observed data from valid zero-valued metrics.
- Warning, validity-flag, or blocked-status propagation into affected validation reports and manifests without breaking unrelated valid cases.
- Focused Rust tests covering empty metric inputs, malformed stop-state or terrain/material count maps, and legitimate zero-valued metrics.
- A documentation note describing how consumers should interpret invalid or unavailable metric fields.

Definition of done:

- Empty or malformed validation evidence can no longer silently produce valid-looking `0.0` or empty-count summaries, focused tests pass, and existing standard validation cases retain expected scientific statuses.

Boundaries: No metric retuning, no benchmark reinterpretation, no default physics change, and no broad validation-file refactor beyond the affected paths.

### TB-197: Python Execution Policy Normalization

Goal: Normalize repository Python invocation guidance and PyYAML dependency messages around the project-local `uv` workflow used by agents and local checks.

Capability gap reduced: Environment-specific workflow failures caused by mixed `python`, `python3`, global pip, requirements, and `uv` guidance.

Why this outranks alternatives: Reviewers reproduced the local pyenv failure mode; workers should receive one consistent command pattern when a Python dependency or tool invocation fails.

Inspect first:

- `AGENTS.md`
- `docs/onboarding.md`
- `README.md`
- `.github/workflows/ci.yml`
- `scripts/run_performance_benchmark.py`
- `scripts/run_tschamut_calibration.py`
- `scripts/calibrate_scarring_impact.py`
- `scripts/download_datasets.py`

Deliverables:

- Consistent user-facing error messages in Python scripts that point to `PYENV_VERSION=system uv run python ...` or the documented CI exception.
- Documentation updates that clarify when CI may use installed Python dependencies and when local workers must use `uv`.
- A repository-consistency or focused test that rejects new global `python3 -m pip install PyYAML` guidance in scripts.
- Confirmation that `pyproject.toml` and `requirements-tools.txt` remain intentionally synchronized rather than competing sources of truth.

Definition of done:

- The documented local Python policy is consistent across agent docs, onboarding docs, and script dependency errors, and focused checks catch regressions.

Boundaries: No dependency upgrade, no removal of CI support for `requirements-tools.txt`, no environment installation, and no unrelated script rewrites.

### TB-198: Calibration Script Failure Diagnostics

Goal: Harden calibration scripts so empty inputs, empty parameter grids, missing impact events, and subprocess failures produce explicit diagnostics with focused tests.

Capability gap reduced: Opaque research-workflow failures in calibration paths that are important for future physical credibility work.

Why this outranks alternatives: Calibration remains scientifically deferred, but the existing scripts should fail clearly before any future no-tuning or holdout protocol depends on them.

Inspect first:

- `scripts/run_tschamut_calibration.py`
- `scripts/calibrate_scarring_impact.py`
- `scripts/preprocess_scarring_real_data.py`
- `calibration/README.md`
- `tests/test_validation_calibration_evidence_gaps.py`

Deliverables:

- Explicit precondition checks for empty candidate rows, empty parameter grids, missing split/deposition rows, missing significant impacts, and failed `cargo run` subprocesses.
- Focused unit tests for the failure cases using tiny temporary CSV/YAML fixtures.
- Improved error messages that name the missing or malformed input and the calibration stage that failed.
- A short documentation update clarifying that these scripts are research diagnostics, not accepted calibration evidence.

Definition of done:

- Calibration scripts no longer rely on `rows[0]`-style assumptions for expected failure modes, focused tests pass, and normal fixture-backed calibration paths remain unchanged.

Boundaries: No calibration run, no parameter selection change, no accepted calibration evidence, no model default change, and no annual/physical probability claim.

### TB-199: Runtime-Facing Panic Path Reduction

Goal: Convert the highest-risk runtime-facing terrain and validation panic paths into structured errors or tightly test-only helpers.

Capability gap reduced: Crash-only behavior in DEM-facing and validation-facing paths that should produce actionable diagnostics.

Why this outranks alternatives: The architecture boundary already requires fallible DEM and pilot workflows; remaining public or runtime-adjacent panics undermine clean blocked-state reporting.

Inspect first:

- `docs/architecture_boundaries.md`
- `src/terrain.rs`
- `src/dynamics.rs`
- `src/integrator.rs`
- `src/validation.rs`
- `src/shape.rs`
- `tests/terrain_edge_cases.rs`

Deliverables:

- An audit of panic/`expect` paths classified as test-only, compatibility-only, or runtime-facing.
- Conversion of the highest-risk DEM-facing and validation-facing panic paths to `TerrainError`, `IntegrationError`, `SimulationError`, or `ValidationError` propagation.
- Focused tests proving malformed DEM queries and missing validation sidecars return structured diagnostics instead of panicking.
- Documentation or code comments marking any remaining panic-only wrappers as compatibility or test helpers.

Definition of done:

- New runtime-facing DEM or validation workflows use fallible paths for the audited cases, focused tests pass, and compatibility wrappers remain clearly bounded.

Boundaries: No physics change, no public runtime promotion of `shape_contact_v0`, no sweeping refactor of all `expect` calls, and no change to analytic-test convenience behavior.

### TB-200: GitHub Python Test Clean-Checkout Stabilization

Goal: Make the Python tests that currently fail in GitHub pass from a clean checkout without relying on ignored Tschamut, hazard, validation, swisstopo, or Balfrin scratch artifacts.

Capability gap reduced: CI reproducibility for planning and evidence helpers when local ignored artifacts are absent.

Why this outranks alternatives: The failing tests are active feedback from GitHub CI; until they fail closed or use committed fixtures, local green runs can keep hiding clean-checkout regressions.

Inspect first:

- `tests/test_pilot_command_plan.py`
- `tests/test_swiss_wide_execution_envelope.py`
- `tests/test_balfrin_single_release_zone_case_plan_dry_run.py`
- `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/plan_balfrin_single_release_zone_case_dry_run.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`

Deliverables:

- `generate_pilot_command_plan.py` no longer hard-reads ignored hazard manifests when building command-plan metadata; missing package manifests produce explicit bounded or empty scope metadata.
- `estimate_swiss_wide_execution_envelope.py` and its measured-coefficient loader return a deterministic blocked report or use committed fixture evidence in tests when same-scale manifests are absent.
- `plan_balfrin_single_release_zone_case_dry_run.py` either uses committed fixture inputs for smoke tests or returns a structured blocked report instead of exit-code-only failure when default ignored inputs are missing.
- `generate_chant_sura_fluelapass_dry_run_case_skeleton.py` has deterministic test fixture setup for deferred-public-context and blocked-missing-input states, including the `/tmp` repo-root edge case.
- Focused tests prove the affected Python test modules pass with ignored roots absent.

Definition of done:

- The named Python tests pass in a clean checkout without `hazard/results/tschamut_public_pilot`, `validation/private/tschamut_public_pilot`, `data/processed/swisstopo/tschamut_public_pilot`, or mounted `/scratch` roots, and reports distinguish `ready`, `blocked_missing_inputs`, and `fixture_backed` correctly.

Boundaries: No public-data download, no generated ignored artifact commit, no fabricated measured evidence, no Balfrin access requirement, and no scale-up or operational claim.

### TB-201: Ignored-Artifact Dependency Audit For Python Tests

Goal: Add an automated audit that identifies Python tests and helper smoke paths that read ignored artifact roots without creating committed fixtures, temporary fixtures, or explicit blocked-report expectations.

Capability gap reduced: Hidden test coupling to local-only artifacts that makes CI and clean clones diverge from developer workstations.

Why this outranks alternatives: Copilot found concrete failures, but a broader scan shows many tests reference ignored roots; the suite needs a guard so new hard dependencies do not reappear after the immediate CI fixes.

Inspect first:

- `tests/test_same_scale_artifact_readiness.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_swiss_wide_execution_envelope.py`
- `tests/test_balfrin_probe_metrics_report.py`
- `tests/test_balfrin_tschamut_readiness.py`
- `scripts/check_repo_consistency.py`
- `.gitignore`

Deliverables:

- A repository-consistency or dedicated test-audit helper that scans Python tests for hard dependencies on `hazard/results/**`, `validation/private/**`, `data/processed/swisstopo/*/`, and `/scratch/**`.
- An allowlist format that permits references only when the test creates temporary fixture data, uses tracked `tests/fixtures/**`, or asserts an explicit blocked state.
- Initial audit classifications for the current test files that reference ignored roots, including which are fixture-backed, blocked-state tests, or cleanup candidates.
- Focused tests showing the audit rejects a new hard read from an ignored root and accepts a temporary fixture or tracked fixture path.

Definition of done:

- The audit runs in CI or repository consistency checks, current tests are classified without false failures, and a new hard dependency on ignored local artifacts is caught before merge.

Boundaries: Audit and classification only; no broad rewrite of all tests, no deletion of local artifacts, no new generated fixtures outside `tests/fixtures`, and no scientific evidence reclassification.

### TB-202: CI Git History And Output-Root Portability Guard

Goal: Remove CI-only failures caused by shallow Git history and by output-root allowlists that treat repository paths under `/tmp` as safe scratch paths.

Capability gap reduced: Portability of repository hygiene checks and dry-run output-root validation across GitHub runners, local temporary checkouts, and isolated test roots.

Why this outranks alternatives: These failures are not scientific, but they break CI and can mask more meaningful artifact-dependency failures.

Inspect first:

- `.github/workflows/ci.yml`
- `scripts/check_repo_consistency.py`
- `tests/test_repo_consistency_claim_hygiene.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`

Deliverables:

- CI checkout or consistency-check behavior that keeps work-log commit reachability deterministic, either by fetching full history for the Python job or by explicitly detecting and reporting shallow clones.
- Focused tests for work-log reachability behavior under shallow-history simulation.
- Output-root validation that rejects paths inside the repository unless they are under an allowed ignored output root, even when the repository root itself is located below `/tmp`.
- Focused tests covering allowed `/tmp` scratch roots, allowed ignored repository roots, and forbidden repository-local paths.

Definition of done:

- GitHub Python tests no longer fail because historical work-log commits are unreachable in a shallow checkout, and dry-run skeleton output-root validation behaves consistently for repos under `/tmp`.

Boundaries: No changes to task history, no weakening of work-log hygiene in normal full-history clones, no generated artifact commit, and no expansion of allowed output roots beyond documented ignored/scratch locations.

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
