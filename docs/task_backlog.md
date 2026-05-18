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

### TB-256: AOI Manifest Bootstrap And Schema Contract

Goal: Create a compact AOI manifest format and bootstrap command that turns a user-supplied polygon or LV95 bounds into a deterministic site configuration.

Capability gap reduced: Users need a stable first artifact that names the AOI, CRS, datum, expected roots, target outputs, and public-geodata acquisition intent.

Why this outranks alternatives: Every later workflow step depends on consistent AOI metadata; without a bootstrap contract, each helper continues to infer site rules from fixture-specific configs.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `tests/test_swisstopo_aoi_acquisition_planner.py`
- `tests/fixtures/second_site_public_geodata_preflight/minimal_synthetic_aoi.yaml`

Deliverables:

- An AOI manifest schema and bootstrap helper or front-door subcommand that accepts LV95 bounds or a GeoJSON polygon and writes a site config under a caller-provided ignored root.
- Validation for CRS, vertical datum, AOI extent, site id, product policy, and output-root layout.
- Fixture-backed tests for valid bounds, invalid CRS, missing AOI geometry, and deterministic manifest IDs.

Definition of done:

- A new user can create a valid AOI manifest that all existing preparation helpers can consume without hand-editing fixture files.

Boundaries: Manifest/bootstrap only; no geodata download, no simulation, no hazard-map claim, no annual-frequency semantics, and no committed generated AOI roots.

### TB-257: AOI Swisstopo Product Resolver And Cache Manifest

Goal: Resolve the required swisstopo products and tile ids for a bootstrapped AOI into a deterministic acquisition/cache manifest.

Capability gap reduced: The workflow still lacks a concrete user path from AOI geometry to exact public-data products, tile ids, checksums, versions, and staging paths.

Why this outranks alternatives: Users cannot move quickly to a hazard map until the data acquisition step is machine-readable and resumable rather than prose-driven.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_swisstopo_aoi_acquisition_planner.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`

Deliverables:

- A resolver mode that consumes the AOI manifest and emits product rows for swissALTI3D, SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D with expected tile ids or explicit unresolved-tile blockers.
- A cache manifest template with checksum, version/date, license, raw path, processed path, and retry/resume metadata fields.
- Tests for resolved fixture tiles, unresolved product rows, and deterministic no-download behavior.

Definition of done:

- The user-facing workflow can tell exactly which public products must be staged for an AOI and which rows remain unresolved before any download or copy is attempted.

Boundaries: Resolver and manifest generation only; no download unless a later task explicitly adds and tests it, no simulation, no operational claim, and no generated public data committed.

### TB-258: Local Public-Geodata Staging And Verification Command

Goal: Add a user-facing staging command that validates locally supplied swisstopo files against the AOI cache manifest and records verified staged inputs.

Capability gap reduced: Users need a concrete bridge from downloaded or manually supplied public geodata files into the repository's ignored processed/raw roots.

Why this outranks alternatives: The current workflow has strong verification contracts but no ergonomic staging interface for a user who already has the required local tiles.

Inspect first:

- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_swisstopo_aoi_acquisition_planner.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`

Deliverables:

- A staging helper or front-door subcommand that accepts local input paths, verifies product ids, checksums, CRS, resolution, license/provenance fields, and writes or updates the cache manifest.
- Fail-closed statuses for missing local files, checksum mismatch, metadata mismatch, unsupported product, and verified staged input.
- Focused tests using small fixture files only.

Definition of done:

- A user with local swisstopo inputs can stage and verify them deterministically without editing cache manifests by hand.

Boundaries: Local staging only; no network download, no simulation, no physical validation claim, no operational claim, and no heavy geodata committed.

### TB-259: Prepared Terrain And Context Builder For AOI

Goal: Build the prepared terrain crop and context QA products from verified AOI cache inputs into a deterministic prepared-input root.

Capability gap reduced: The region-to-map workflow still lacks an executable user-facing step that turns staged public geodata into simulator-ready terrain and context artifacts.

Why this outranks alternatives: Hazard-map execution cannot start until terrain, metadata, hillshade/slope QA, and optional context layers are prepared from the verified AOI cache.

Inspect first:

- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/measure_hazard_context_overlap.py`
- `scripts/build_terrain_material_diagnostic_matrix.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `tests/test_aoi_terrain_preprocessing.py`
- `tests/test_hazard_context_overlap.py`

Deliverables:

- A prepared-input builder mode that writes terrain, terrain metadata, slope/aspect/hillshade QA summaries, and context availability summaries under an ignored AOI root.
- Explicit `ready`, `partial_context`, `blocked_missing_terrain`, and `blocked_metadata_mismatch` classifications.
- Tests using fixture terrain and context manifests.

Definition of done:

- A verified AOI cache can be converted into simulator-ready terrain/context inputs or an exact blocker report with no manual path inference.

Boundaries: Preparation only; no release-zone validation, no ensemble execution, no operational claim, and no heavy public geodata committed.

### TB-260: Release-Zone Candidate Review Package

Goal: Generate a reviewable release-zone candidate package from prepared AOI terrain with stable candidate IDs, GIS outputs, sensitivity labels, and editable acceptance fields.

Capability gap reduced: Users need to move from terrain to candidate release zones quickly while preserving the distinction between workflow-generated candidates and field-supported source evidence.

Why this outranks alternatives: Release-zone selection is the first domain-specific user decision in an AOI-to-map workflow and must be reviewable before scenario generation or execution.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `docs/source_zone_block_scenario_policy_v1.md`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_release_zone_heuristic_dry_run.py`

Deliverables:

- A candidate review package with candidate polygons, release-cell IDs, slope/sensitivity summaries, GIS-readable outputs, and user-editable `accepted`, `rejected`, or `needs_field_review` decisions.
- Machine-readable provenance labels for `workflow_generated`, `field_supported`, `mixed_provenance`, and `blocked_missing_provenance`.
- Tests proving scenario generation cannot consume unreviewed or overclaimed candidates as field-supported evidence.

Definition of done:

- A user can review AOI release candidates as a first-class artifact before freezing source-zone metadata.

Boundaries: Candidate generation and review packaging only; no release-zone validation claim, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.

### TB-261: Reviewed Source-Zone And Scenario Plan Freezer

Goal: Convert reviewed release-zone candidates into frozen source-zone metadata, conditional scenario tables, and a source/scenario policy record for the AOI.

Capability gap reduced: The workflow needs a deterministic handoff from user-reviewed candidates to runnable conditional scenarios.

Why this outranks alternatives: Execution plans should consume frozen, reviewed source/scenario records rather than raw heuristic candidate outputs.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/generate_tschamut_block_scenario_tables.py`
- `scripts/validate_source_scenario_policy.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `docs/source_zone_block_scenario_policy_v1.md`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_source_scenario_policy.py`

Deliverables:

- A freezer mode that consumes accepted candidate IDs and emits source-zone metadata, release rows, conditional scenario table, and policy YAML under the AOI ignored root.
- Explicit block-family, trajectory-count, seed-policy, and conditional-weight controls with annual/frequency fields left empty.
- Tests for deterministic IDs, rejected-candidate exclusion, invalid weights, and conditional-only claim boundaries.

Definition of done:

- A reviewed AOI candidate package can become a reproducible conditional scenario plan ready for command-plan generation.

Boundaries: Conditional scenario planning only; no physical probability, no source-frequency evidence, no calibration, no operational claim, and no generated heavy outputs committed.

### TB-262: Prepared-Pilot Compiler From AOI Manifest

Goal: Compile the AOI manifest, prepared inputs, reviewed source zones, and frozen scenario plan into one runnable prepared-pilot command plan.

Capability gap reduced: The current dry-run pieces are broad but still require users to stitch together acquisition, terrain, release, scenario, output-root, and command-plan artifacts manually.

Why this outranks alternatives: A user cannot rapidly move from AOI definition to execution until there is a deterministic compiler that says which commands will run and where outputs will land.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/lib/command_plan_contract.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- A prepared-pilot compiler mode that emits a run manifest, command plan, expected input/output inventory, output profile, Balfrin/local execution hints, and first blocker.
- A `ready_for_local_smoke`, `ready_for_balfrin_postproc`, or `blocked_missing_inputs` classification.
- Tests for ready fixture, missing terrain, missing reviewed source zones, missing scenario plan, and deterministic command-plan shape.

Definition of done:

- A user can compile all AOI preparation artifacts into one execution-ready or blocked pilot package.

Boundaries: Compilation only; no live Balfrin submission in this task, no ensemble execution, no annual-frequency semantics, no operational claim, and no heavy outputs committed.

### TB-263: Local Tiny AOI Hazard-Map Smoke Run

Goal: Execute a tiny local fixture-backed AOI prepared-pilot run through trajectory generation and hazard-layer building to prove the front-door workflow produces actual map artifacts.

Capability gap reduced: The AOI workflow needs an end-to-end executable smoke proof from prepared pilot to hazard rasters before larger Balfrin jobs are trusted.

Why this outranks alternatives: User experience depends on seeing a complete tiny map pipeline, not only a sequence of ready/blocked preparation reports.

Inspect first:

- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/check_hazard_output_profile.py`
- `tests/test_public_real_site_conditional_pilot_run.py`
- `tests/test_hazard_layers.py`
- `tests/fixtures/hazard/ensemble_case.yaml`

Deliverables:

- A local smoke mode or fixture that executes a tiny AOI command plan into an ignored or `/tmp` output root and produces reduced trajectory outputs plus hazard layers.
- Output assertions for required rasters, manifests, claim-boundary metadata, and no-heavy-debug defaults.
- Tests proving the smoke run is deterministic and clean-checkout safe.

Definition of done:

- The repository has a CI-scale end-to-end proof that an AOI prepared-pilot package can produce hazard-map artifacts.

Boundaries: Tiny local fixture execution only; no live Balfrin submission, no physical validation claim, no operational claim, and no generated heavy outputs committed.

### TB-264: Balfrin Target-Area Metrics Completion Postproc Run

Goal: Submit the exact bounded target-area metrics-completion rerun on Balfrin postprocessing nodes to close the missing execution-metrics gap.

Capability gap reduced: The current target-area demonstration still lacks peak memory and split validation/hazard output metrics in the preserved evidence chain.

Why this outranks alternatives: The decision helper ranks metrics completion first, and the user has authorized workers to execute on Balfrin postprocessing nodes for bounded tasks in this queue.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`

Deliverables:

- A live Balfrin postproc submission for the exact metrics-completion run root `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v2`, using the frozen target-area manifest and reduced-output preservation contract.
- Recorded SLURM job id, run root, command plan, logs, sacct fields, metrics JSON, and preservation-gate output.
- A blocked report instead of submission if access, checkout, package, or preservation preflight fails.

Definition of done:

- The metrics-completion run is either submitted and collected as measured evidence, or the exact preflight blocker is recorded without partial evidence promotion.

Boundaries: This task explicitly allows one bounded Balfrin `postproc` submission for the named metrics-completion run only; no retries without diagnosing the failed state, no multi-zone run, no distributed execution, no scale-up, no physical-probability semantics, and no operational claim.

### TB-265: Metrics Completion Evidence Integration And Decision Refresh

Goal: Integrate the TB-264 Balfrin run result into the canonical metrics report, preservation gate, evidence bundle, closure package, and next-action decision.

Capability gap reduced: A measured run only moves the project forward if the repository consumes it consistently and stops ranking metrics completion as the top unresolved action.

Why this outranks alternatives: This turns live execution into durable evidence rather than another unconnected run root.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `tests/test_balfrin_probe_metrics_report.py`
- `tests/test_balfrin_demonstration_closure_package.py`

Deliverables:

- Updated canonical reports or fixtures that classify the TB-264 result as measured, recovered, blocked, or incomplete.
- A refreshed next-action decision that ranks the smallest multi-zone measurement, AOI workflow work, physical evidence, or second-site staging after metrics completion.
- Tests proving incomplete TB-264 evidence remains blocked and complete evidence updates downstream decisions without claim upgrades.

Definition of done:

- The canonical Balfrin evidence state reflects the measured metrics-completion outcome and preserves all non-operational claim boundaries.

Boundaries: Evidence integration only; no additional live submission, no physical credibility upgrade, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.

### TB-266: Smallest Multi-Zone Handoff Budget Repair

Goal: Repair or tighten the smallest multi-zone handoff so its projected manifest, sidecar, and reducer budget can pass or fail with an actionable reason.

Capability gap reduced: The multi-zone path remains blocked by handoff-derived manifest/reducer pressure, preventing a measured many-release-zone Balfrin probe.

Why this outranks alternatives: Full Balfrin demonstration progress requires getting beyond single-zone comfort, but only after the smallest multi-zone handoff is inside measured budgets.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- A compact handoff projection or reduced sidecar mode that preserves replay-critical fields while lowering manifest/file-family pressure.
- Before/after budget report for the reviewed two-release-zone probe shape.
- Tests proving replay-critical metadata, sorted merge order, checksums, and output-profile semantics cannot be removed to pass the budget.

Definition of done:

- The smallest multi-zone handoff either reaches `ready_for_authorization_review` on budget grounds or reports the precise replay-critical budget field that remains a blocker.

Boundaries: Handoff budget repair only; no live Balfrin submission in this task, no loss of replayability, no distributed reducer, no physics change, no operational claim.

### TB-267: Smallest Multi-Zone Balfrin Postproc Probe

Goal: Submit the exact smallest bounded multi-zone Balfrin probe on postprocessing nodes once TB-266 and the authorization preflight are ready.

Capability gap reduced: The repository lacks measured many-release-zone Balfrin evidence, which is the next architectural step toward a fuller demonstration.

Why this outranks alternatives: After target-area metrics are closed and the smallest handoff budget is repaired, a measured two-zone probe is more informative than more dry-run packaging.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_authorization_gated_multi_zone_measurement_path.py`

Deliverables:

- A live Balfrin postproc submission for the exact smallest multi-zone run shape: 2 release zones, 2 scenarios, 1000 target trajectories, 2 trajectory workers, 2 reducer workers, 2 reducer chunks, summary-only conditional curves, no grid CSV export, and a deterministic run root under `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`.
- Recorded SLURM job id, command plan, reviewed handoff package hash, authorization record, metrics JSON, preservation gate, and post-run collector output.
- A blocked report if access, budget, authorization preflight, or preservation requirements fail before submission.

Definition of done:

- The project has either measured smallest multi-zone Balfrin evidence or a precise pre-submit blocker, with no partial run promoted as evidence.

Boundaries: This task explicitly allows one bounded Balfrin `postproc` submission for the named two-zone probe only; no retries without blocker analysis, no larger ensemble, no distributed execution, no annual-frequency or physical-probability semantics, no risk/exposure/vulnerability product, and no operational claim.

### TB-268: Multi-Zone Evidence Integration And Reducer Scaling Update

Goal: Integrate the TB-267 multi-zone result into reducer-pressure, evidence-bundle, closure, and Swiss-wide envelope helpers.

Capability gap reduced: Measured multi-zone evidence must update the scaling frontier and next-action decision rather than remain a detached run root.

Why this outranks alternatives: This is the step that converts a two-zone Balfrin run into actionable scaling evidence for larger Balfrin or Swiss AOI workflows.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A measured multi-zone reducer/output summary with file counts, manifest bytes, reducer wall time, merge-order proof, restart/replay metadata, and first bottleneck labels.
- Updated evidence and decision helpers that distinguish scratch, fixture-backed, and measured multi-zone Balfrin roots.
- Tests proving measured multi-zone evidence changes the scaling branch without authorizing larger runs automatically.

Definition of done:

- The scaling frontier reflects measured two-zone Balfrin evidence and names the next safe expansion or explicit no-go blocker.

Boundaries: Evidence integration only; no additional live run, no Swiss-wide authorization, no distributed execution, no operational claim, and no physical-probability semantics.

### TB-269: AOI Hazard Map Product Packager

Goal: Package AOI hazard-layer outputs into user-consumable GeoTIFF/COG, GeoJSON/GeoPackage, manifest, and text-summary artifacts.

Capability gap reduced: Producing hazard rasters is not enough; a user needs a coherent map package with provenance, layer semantics, and claim boundaries.

Why this outranks alternatives: The stated project goal is an actual hazard map workflow, so the output bundle has to be a first-class interface rather than scattered files.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `docs/hazard_map_semantics.md`
- `docs/hazard_output_profile_contract.md`
- `tests/test_gis_cog_package_readiness.py`
- `tests/test_same_scale_cog_package_conversion.py`

Deliverables:

- A map-packaging command or front-door subcommand that converts AOI hazard outputs into a compact package with COG rasters where supported, vector release/scenario overlays, layer inventory, checksums, and claim-boundary metadata.
- A `map_package_ready`, `cog_blocked`, or `blocked_missing_hazard_outputs` classification.
- Tests for fixture hazard outputs, missing layers, COG conversion failure, and manifest consistency.

Definition of done:

- A user can point at an AOI hazard output root and receive a reviewable map package rather than raw intermediate files.

Boundaries: Packaging only; no hazard-value change, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability product, and no heavy outputs committed.

### TB-270: AOI Map QA Project And Static Review Surface

Goal: Generate a lightweight QA surface for an AOI map package that overlays terrain, release zones, scenario metadata, hazard layers, and context availability.

Capability gap reduced: Users need to inspect whether the map is spatially coherent before interpreting or sharing a hazard product.

Why this outranks alternatives: Rapid AOI-to-map iteration needs visual QA; otherwise users must manually assemble layers in GIS tools and may miss provenance or scope warnings.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/measure_hazard_context_overlap.py`
- `scripts/summarize_balfrin_target_area_gis_cog_scope.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/hazard_map_semantics.md`
- `tests/test_pilot_gis_visual_qa.py`
- `tests/test_balfrin_target_area_gis_cog_scope.py`

Deliverables:

- A QA project generator that emits a QGIS project, static HTML index, or equivalent manifest-driven review surface under an ignored output root.
- Visible or machine-readable warnings for missing context layers, COG-blocked rasters, fixture-backed inputs, conditional-only weights, and non-operational status.
- Tests for layer presence, warning propagation, and blocked missing-map-package behavior.

Definition of done:

- A user can inspect the AOI hazard map package with release/scenario/context overlays and understand the current evidence boundaries.

Boundaries: QA/review surface only; no hazard-value changes, no operational claim, no physical-probability semantics, no regulatory-use claim, and no heavy outputs committed.

### TB-271: Adaptive AOI Ensemble Convergence Controller

Goal: Add a controller that escalates AOI trajectory counts in bounded steps until spatial convergence stabilizes or a runtime/output budget stops the run.

Capability gap reduced: Users should not have to choose arbitrary trajectory counts; the workflow needs a measured sufficiency loop for conditional diagnostic maps.

Why this outranks alternatives: A rapid AOI-to-map workflow is only useful if it can say whether the map is stable enough for diagnostic review or blocked by uncertainty/output pressure.

Inspect first:

- `scripts/compare_hazard_map_convergence.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/submit_balfrin_probe.py`
- `docs/hazard_output_profile_contract.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_hazard_map_convergence.py`
- `tests/test_balfrin_ensemble_frontier.py`

Deliverables:

- An adaptive convergence plan that proposes trajectory-count increments, expected output budgets, stop criteria, and local versus Balfrin execution mode.
- A fixture-backed local loop and a Balfrin-ready command plan for bounded postproc escalation when preflights pass.
- Tests for converged, budget-stopped, and inconclusive branches.

Definition of done:

- The workflow can recommend or execute the next bounded trajectory-count step based on measured convergence and output budget rather than fixed guesses.

Boundaries: Conditional convergence only; Balfrin submission may be prepared but not run in this task unless explicitly scoped by a later task, no annual-frequency semantics, no physical validation claim, and no operational claim.

### TB-272: End-To-End AOI-To-Map Regression Fixture

Goal: Add a compact regression fixture that exercises the entire user-facing path from AOI manifest through prepared inputs, reviewed release/scenario plan, local smoke execution, hazard-layer build, map packaging, and QA summary.

Capability gap reduced: The project needs a durable proof that the front-door workflow stays usable as individual helpers evolve.

Why this outranks alternatives: Without an end-to-end regression, improvements to one helper can silently break the user journey from AOI definition to hazard map.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_public_real_site_conditional_pilot_run.py`
- `tests/test_hazard_layers.py`

Deliverables:

- A small fixture-backed end-to-end test or smoke helper that runs under `/tmp` and asserts the expected command states, output manifests, hazard layers, map-package metadata, and claim-boundary fields.
- A single failure summary that names the first broken workflow step for users and agents.
- Documentation or README update only if needed to point users at the regression-backed command path.

Definition of done:

- The repository has one maintained, clean-checkout-safe proof that the AOI-to-map workflow can produce a map package on tiny inputs.

Boundaries: Fixture-backed regression only; no live Balfrin submission, no real public-geodata download, no operational claim, and no heavy outputs committed.

### TB-273: Optional Observed-Evidence Overlay Hook For AOI Maps

Goal: Allow an AOI hazard map package to include optional observed runout/deposition or release-zone provenance overlays when real accepted evidence is staged.

Capability gap reduced: Scientific credibility remains separate from workflow execution, but users need a clean path to attach observed evidence to a map package without turning it into calibration or annual-frequency semantics.

Why this outranks alternatives: This connects the physical-evidence intake machinery to the user-facing map workflow while preserving the project's strict claim boundaries.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/hazard_map_semantics.md`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `tests/test_physical_credibility_evidence_requirements.py`

Deliverables:

- A map-package overlay hook that accepts only real-input-ready observed evidence or field-supported release-zone provenance, and otherwise emits `blocked_missing_evidence`, `blocked_fixture_only_inputs`, or `blocked_schema_gap`.
- Manifest fields that distinguish diagnostic hazard outputs, observed evidence overlays, calibration inputs, holdout evidence, and deferred source-frequency records.
- Tests proving fixture-only or ambiguous-role evidence cannot appear as accepted physical validation in the map package.

Definition of done:

- AOI map packages can carry optional real observed-evidence overlays without implying calibration, physical probability, annual frequency, risk, or operational readiness.

Boundaries: Optional overlay integration only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no operational claim, and no claim upgrade beyond accepted evidence.

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
