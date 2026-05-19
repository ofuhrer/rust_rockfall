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

### TB-276: Real AOI Golden Fixture Package

Goal: Add one compact clean-checkout-safe AOI fixture package that exercises the AOI workflow with minimized real-like public-data metadata instead of only synthetic terrain assumptions.

Capability gap reduced: The current end-to-end AOI proof is useful, but it remains too fixture/synthetic-heavy to protect the real-user path from schema and provenance drift.

Why this outranks alternatives: A small golden fixture gives every later UX and workflow task a stable regression target without requiring large ignored geodata roots.

Inspect first:

- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/fixtures/second_site_public_geodata_preflight/minimal_synthetic_aoi.yaml`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/plan_aoi_terrain_preprocessing.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A minimized committed fixture package with AOI manifest, terrain/cache metadata, tiny terrain crop, source/scenario records, and provenance fields sufficient for clean-checkout regression.
- Tests proving the fixture can pass bootstrap, staging verification, prepared-input building, command planning, tiny smoke, packaging, and QA review without ignored local state.
- Explicit labels that the fixture is a regression fixture, not physical validation evidence.

Definition of done:

- The repo has one stable AOI-to-map regression fixture that catches user-workflow breakage without needing private or ignored artifacts.

Boundaries: Fixture/regression only; no heavy data, no live Balfrin submission, no physical credibility claim, no annual-frequency semantics, no operational claim, and no real-world hazard product.

### TB-277: AOI Front-Door Status UX Tightening

Goal: Normalize the AOI front-door status output so the text and JSON modes are concise, stable, and directly actionable for a new user.

Capability gap reduced: The front door exists, but user-visible status still exposes internal helper vocabulary and can be noisy or uneven across blocked states.

Why this outranks alternatives: Better status semantics reduce wasted worker/user time before adding more execution paths.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `docs/onboarding.md`
- `README.md`

Deliverables:

- Stable status fields for `workflow_status`, `next_action`, `first_blocker`, `next_command`, `expected_inputs`, `expected_outputs`, and `claim_boundaries`.
- Consistent exit-code policy for ready, blocked, invalid input, and internal error states.
- Tests for text and JSON output on ready fixture, blocked missing inputs, invalid site config, and unsupported command state.

Definition of done:

- A new user can run the front-door status command and understand the first blocker and next command without inspecting nested delegate reports.

Boundaries: UX/status normalization only; no simulation, no live Balfrin submission, no claim upgrade, and no heavy outputs committed.

### TB-278: AOI Release Candidate Review Editing Loop

Goal: Provide a deterministic command for applying user review decisions to release-zone candidate packages and validating the edited review state.

Capability gap reduced: Release-zone review packages exist, but the edit/apply loop is still too manual and schema-sensitive for users.

Why this outranks alternatives: Release-zone acceptance is the first unavoidable expert/user decision before scenario generation, so it needs a robust interface.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_candidate_source_zone_freezer.py`
- `docs/source_zone_block_scenario_policy_v1.md`

Deliverables:

- A review-apply command that accepts candidate IDs and decisions, rewrites or emits a reviewed package, and validates allowed provenance labels.
- Blocking diagnostics for unknown candidate IDs, unreviewed accepted candidates, mixed-provenance overclaims, and empty accepted sets.
- Tests proving the scenario freezer consumes only validated accepted candidates.

Definition of done:

- A user can review, accept, reject, and freeze release candidates without hand-editing low-level JSON/GeoJSON fields.

Boundaries: Review editing and validation only; no physical source validation claim, no calibration, no annual-frequency semantics, no operational claim, and no generated heavy outputs committed.

### TB-279: AOI Scenario Preview And Cost Estimate

Goal: Add a pre-execution preview that reports scenario cardinality, trajectory count, expected output profile, estimated runtime/storage, and local-vs-Balfrin suitability.

Capability gap reduced: Users can freeze scenarios, but they do not yet get a clear cost and output-pressure estimate before running or submitting work.

Why this outranks alternatives: Scenario growth and output pressure are known scaling risks, and users need this feedback before expensive execution.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_hazard_output_profile.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A scenario-preview report with rows by source zone, block family, scenario family, trajectory count, output-profile choice, projected files/bytes, and recommended execution target.
- Fail-closed labels for unsupported profile, missing reviewed candidates, unknown trajectory budget, and output-budget exceeded.
- Tests for tiny fixture, multi-zone fixture, and budget-exceeded paths.

Definition of done:

- Before executing, a user can see whether an AOI plan is safe for local smoke, Balfrin postproc, or blocked by output/runtime pressure.

Boundaries: Preview/estimation only; no live Balfrin submission, no simulation, no distributed execution, no scale-up authorization, and no physical-probability semantics.

### TB-280: Prepared-Pilot Local Execution Wrapper

Goal: Turn a ready prepared-pilot command plan into one local bounded execution command that writes validation outputs, hazard layers, map package, and QA review under a caller-provided output root.

Capability gap reduced: The repo can run a tiny smoke and can package maps, but a user still lacks one local command for a ready prepared pilot.

Why this outranks alternatives: This creates the first practical local end-to-end execution path after preparation and planning, while staying bounded and non-operational.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/build_hazard_layers.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A local execution wrapper that consumes a ready prepared-pilot report, runs the bounded validation case, builds reduced hazard layers, packages the map, and generates the static QA review.
- Output-root safety checks, overwrite policy, reduced-output defaults, manifest checksums, and first-failure reporting.
- Tests against the golden fixture or existing tiny smoke fixture.

Definition of done:

- A prepared AOI fixture can produce a complete local diagnostic map package through one command.

Boundaries: Local bounded execution only; no live Balfrin submission, no large AOI execution, no operational claim, no annual-frequency semantics, no risk/exposure/vulnerability product, and no heavy outputs committed.

### TB-281: AOI Map Package Openable Review Bundle

Goal: Make the AOI map package directly reviewable as a single openable static bundle with layer toggles, legends, warnings, provenance, and claim boundaries.

Capability gap reduced: Map packaging and QA review exist, but the user-facing artifact is still more manifest-oriented than map-review oriented.

Why this outranks alternatives: The project goal ends in a hazard map; users need an inspectable product, not only machine-readable manifests.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `docs/hazard_map_semantics.md`
- `tests/test_aoi_hazard_map_packager.py`
- `tests/test_aoi_map_qa_review.py`

Deliverables:

- A static review bundle entrypoint, such as `index.html`, that links or embeds map layers, overlays, legends, warnings, provenance, and package manifest details.
- Clear visual/text separation between diagnostic hazard layers, release/scenario overlays, optional observed evidence, missing context, and claim boundaries.
- Tests for generated file inventory, missing-layer warnings, overlay state, and non-operational boundary text.

Definition of done:

- A user can open one generated review surface and inspect the AOI diagnostic hazard map package without reading raw manifests first.

Boundaries: Review artifact only; no hazard-value changes, no physical validation claim, no operational claim, no annual-frequency semantics, and no heavy outputs committed.

### TB-282: Balfrin Remote Checkout Hygiene Gate

Goal: Add a Balfrin pre-submit hygiene gate that detects dirty remote checkout state and reports exact safe cleanup actions before any future SLURM attempt.

Capability gap reduced: TB-264 failed before submission because the remote checkout had untracked generated files; this should be caught and explained before packaging or submission.

Why this outranks alternatives: The next ranked Balfrin action is metrics completion, but it should not be retried until remote cleanliness is executable and auditable.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_balfrin_target_area_metrics_completion_rerun_package.py`

Deliverables:

- A read-only remote hygiene gate that reports tracked modifications, untracked generated files, stale submission packages, stale logs, remote HEAD, and expected safe cleanup commands.
- Integration into the metrics-completion and multi-zone preflight reports as a required pre-submit condition.
- Tests using synthetic remote-status fixtures.

Definition of done:

- Future Balfrin pre-submit reports fail closed on dirty remote state and tell the operator exactly what must be cleaned or preserved before continuing.

Boundaries: Read-only hygiene/preflight only; no remote deletion, no live Balfrin submission, no SLURM job, no scale-up authorization, and no claim upgrade.

### TB-283: Balfrin Metrics-Completion Rerun Reattempt Package

Goal: Rebuild the exact target-area metrics-completion rerun package after remote hygiene is ready and preserve either the authorized submission result or the exact fail-closed blocker.

Capability gap reduced: The target-area evidence path still needs a clean, auditable branch for recovering or rerunning missing execution metrics.

Why this outranks alternatives: The decision gate ranks metrics completion first, but the previous attempt stopped on remote checkout hygiene before submission.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A refreshed metrics-completion rerun package for the exact target-area metrics-completion run root, including remote hygiene state, access preflight, package hash, expected outputs, and preservation contract.
- If separate exact user authorization is present at execution time, one bounded postproc submission may be attempted; otherwise the task must stop at `ready_for_authorization` or the exact blocker.
- Post-attempt integration notes that distinguish submitted, blocked_pre_submit, failed_closed, and no_authorization states without promoting incomplete evidence.

Definition of done:

- The metrics-completion branch is either submitted and preserved under the existing evidence gates, or blocked with one exact remaining precondition.

Boundaries: Exact target-area metrics-completion rerun only; live Balfrin submission requires separate explicit authorization at execution time; no retries without a new diagnosis, no multi-zone run, no distributed execution, no physical credibility upgrade, no annual-frequency claim, no risk/exposure/vulnerability claim, and no operational claim.

### TB-284: Metrics Recovery Integration Refresh

Goal: Integrate any newly recovered or rerun target-area metrics into the Balfrin evidence bundle, closure package, decision gate, and maturity snapshot without overclaiming.

Capability gap reduced: Metrics evidence can be recovered or rerun, but it must be propagated consistently across the repository's authoritative decision surfaces.

Why this outranks alternatives: Evidence drift across Balfrin summaries is a known risk and would directly affect the next live-run decision.

Inspect first:

- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/current_maturity_snapshot.md`
- `tests/test_balfrin_evidence_bundle.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Updated evidence classifiers for `recovered_existing_run_root`, `new_metrics_completion_rerun`, `blocked_missing_metrics`, and `blocked_pre_submit`.
- Tests proving peak memory, split validation/hazard counts/bytes, run-root hashes, SLURM fields, and preservation status propagate consistently when available.
- Documentation updates only where the evidence state materially changes.

Definition of done:

- Balfrin evidence summaries agree on the target-area metrics state and the next decision gate no longer relies on stale or contradictory metric labels.

Boundaries: Evidence integration only; no live Balfrin submission, no new run, no claim upgrade beyond execution-metric completeness, no annual-frequency semantics, and no operational claim.

### TB-285: Reducer Manifest Budget Compression

Goal: Reduce smallest multi-zone manifest pressure while retaining replay-critical metadata, hashes, merge order, and output-profile semantics.

Capability gap reduced: The smallest multi-zone Balfrin path is blocked by manifest-size pressure before execution.

Why this outranks alternatives: Multi-zone execution is the next architectural scaling milestone, but it should not proceed until the handoff package fits the reducer/output budget.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- A compact manifest representation or pruning mode that removes redundant data while preserving replay-critical families and deterministic merge proof.
- Before/after budget evidence for manifest bytes, file counts, sidecars, reducer manifests, and replay-critical retained fields.
- Regression tests proving the smallest two-zone package is either under budget or reports the exact irreducible blocker.

Definition of done:

- The smallest multi-zone handoff no longer blocks on avoidable manifest-size pressure, or the remaining blocker is proven replay-critical and explicitly named.

Boundaries: Handoff/budget compression only; no live Balfrin submission, no dropped replayability, no distributed reducer, no physics change, no scale-up authorization, and no operational claim.

### TB-286: Smallest Multi-Zone Authorization Package Refresh

Goal: Rebuild the smallest two-zone Balfrin authorization package after reducer-budget compression and produce a clean authorization-ready record.

Capability gap reduced: The previous multi-zone path had both reducer-budget and authorization-record blockers.

Why this outranks alternatives: A live multi-zone probe should only be considered after the package, output profile, access, authorization record, and preservation gates agree.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`
- `tests/test_balfrin_authorization_gated_multi_zone_measurement_path.py`

Deliverables:

- A refreshed two-zone authorization preflight with reviewed package hash, exact run shape, output profile, reducer budget, remote hygiene, access state, preservation contract, and authorization-record path.
- Text and JSON summaries suitable for user review before any live job.
- Tests proving missing authorization, blocked budget, dirty remote hygiene, and ready-for-review states are distinct.

Definition of done:

- The smallest multi-zone path has one authoritative authorization package with no stale budget or package-hash ambiguity.

Boundaries: Authorization package only; no live Balfrin submission, no scale-up, no distributed execution, no claim upgrade, and no operational claim.

### TB-287: Smallest Multi-Zone Balfrin Probe

Goal: Execute or fail closed on the exact smallest bounded two-zone Balfrin postproc probe after all authorization and budget gates are ready.

Capability gap reduced: Reducer and manifest behavior remain unmeasured beyond scratch/fixture-backed multi-zone probes.

Why this outranks alternatives: Once package and authorization gates are ready, a two-zone probe is the smallest measured step toward the full-scale Balfrin demonstration.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- If separate exact user authorization is present at execution time, submit exactly the bounded two-zone postproc probe described by the refreshed authorization package.
- Preserve SLURM id, runtime, memory, output counts/bytes, reducer manifests, hashes, replay metadata, and preservation-gate output.
- If any gate fails, stop before submission and record the exact blocker.

Definition of done:

- The smallest multi-zone branch is either measured and preserved under the run-root contract or has one exact pre-submit blocker.

Boundaries: Exact smallest two-zone probe only; live Balfrin submission requires separate explicit authorization at execution time; no retry without blocker analysis, no larger ensemble, no distributed execution, no scale-up, no annual-frequency claim, no physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.

### TB-288: Real Chant Sura Core Input Staging Pass

Goal: Stage or reject the first missing real Chant Sura / Fluelapass core inputs named by the readiness gate, beginning with terrain metadata and AOI tile catalog.

Capability gap reduced: Second-site portability remains blocked because real staged inputs and metadata are missing or incomplete.

Why this outranks alternatives: The fastest way to reduce Tschamut coupling is to advance one real second-site input row at a time through the existing fail-closed gate.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/stage_public_geodata_cache.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `tests/test_chant_sura_real_context_readiness_gate.py`

Deliverables:

- A staging pass for the first unresolved real core input named by the gate, with checksum/provenance metadata where available.
- If the local input is unavailable or ambiguous, a blocked acquisition record naming the exact missing file, metadata fields, and next action.
- Focused tests or fixture updates only if schema behavior changes.

Definition of done:

- The Chant Sura readiness gate advances past at least one real-input blocker or preserves an exact acquisition blocker that removes ambiguity.

Boundaries: Real-input staging/rejection only; no synthetic upgrade to real readiness, no second-site ensemble execution, no live Balfrin submission, no physical validation claim, and no operational claim.

### TB-289: Physical Evidence Overlay Acquisition Pass

Goal: Acquire, stage, or reject one real observed runout/deposition or field-supported release-zone provenance package for use as an AOI map overlay.

Capability gap reduced: AOI maps can carry optional evidence overlays, but the repository still lacks an accepted real overlay package that changes review usefulness.

Why this outranks alternatives: Physical credibility is the largest scientific gap, and one accepted overlay package is a concrete step that does not overclaim calibration.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `tests/test_aoi_hazard_map_packager.py`

Deliverables:

- A staged real evidence candidate or explicit rejection report with geometry, provenance, licensing, uncertainty, role, and claim-boundary fields.
- Integration smoke showing the AOI map packager accepts only `real_input_ready` evidence and blocks fixture-only or ambiguous-role packages.
- Documentation update only if a real accepted package is added.

Definition of done:

- The optional overlay path is exercised with either accepted real evidence or a precise acquisition blocker, without implying calibration or operational validity.

Boundaries: Evidence overlay acquisition/intake only; no calibration, no parameter fitting, no physical-probability product, no annual-frequency semantics, no risk/exposure/vulnerability claim, and no operational claim.

### TB-290: AOI End-To-End User Documentation Smoke

Goal: Write and test a short user-facing walkthrough from AOI bounds to review map using only supported commands and documented blocked states.

Capability gap reduced: The workflow has grown many commands, but a user still lacks a concise verified path through them.

Why this outranks alternatives: Documentation should now capture the newly implemented AOI workflow before more interfaces are added.

Inspect first:

- `README.md`
- `docs/onboarding.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/package_aoi_hazard_map.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- A concise AOI-to-map walkthrough that names commands, expected outputs, blocked states, ignored roots, and claim boundaries.
- A smoke test or doc-command checker that verifies the documented fixture commands still run or fail with the documented status.
- Updates to README or onboarding only where they reduce user confusion.

Definition of done:

- A new user can follow one documented path from AOI definition to a local diagnostic review map or an exact blocked state.

Boundaries: Documentation and command smoke only; no new scientific claims, no live Balfrin submission, no network download, and no heavy generated outputs committed.

### TB-291: Workflow Surface Consolidation Review

Goal: Identify and consolidate duplicated AOI/Balfrin status rendering, path handling, blocker vocabulary, and claim-boundary helpers that now affect user-facing workflow consistency.

Capability gap reduced: The helper surface is becoming broad again, and duplicated status mechanics can make equivalent blockers look different to users and workers.

Why this outranks alternatives: Consolidation should happen after the AOI front-door and map-package path exists, but before another large wrapper layer is added.

Inspect first:

- `scripts/lib/workflow_validation.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `docs/script_inventory.md`

Deliverables:

- A bounded review identifying duplicated helper mechanics and one small extraction or consolidation with tests.
- No public CLI schema changes unless the task documents compatibility and updates all affected tests.
- A follow-up recommendation for any larger refactor that should not be attempted opportunistically.

Definition of done:

- At least one concrete duplicated status/path/claim-boundary mechanic is consolidated or a precise no-change rationale is recorded with the next safe refactor boundary.

Boundaries: Bounded consolidation only; no broad framework rewrite, no behavior-changing refactor without tests, no live Balfrin submission, no claim upgrade, and no operational claim.

### TB-292: Balfrin Scale Readiness Baseline Matrix

Goal: Establish one authoritative baseline matrix for Balfrin scale readiness across single-zone, target-area, smallest multi-zone, and projected larger AOI runs.

Capability gap reduced: The project has many scale-related reports, but workers still have to reconcile output budget, reducer pressure, metrics completeness, access, and authorization state manually.

Why this outranks alternatives: Before changing execution or output behavior, the repo needs a single measured/blocked/projection matrix that names the exact blockers for each scale tier.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `docs/current_maturity_snapshot.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A compact scale-readiness report that classifies each tier as `measured`, `ready_for_exact_authorization`, `blocked_pre_submit`, `blocked_reducer_budget`, `projection_only`, or `no_go`.
- Explicit columns for file count, bytes, manifest bytes, reducer sidecars, runtime, memory, run-root preservation, replayability, and authorization status.
- Tests using existing fixture and blocked-preflight evidence.

Definition of done:

- A worker can answer, from one report, which Balfrin scale tier is currently measured, which is blocked, and which evidence field must change next.

Boundaries: Read-only synthesis only; no live Balfrin submission, no new run, no scale-up authorization, no distributed execution, no physical-probability semantics, and no operational claim.

### TB-293: Multi-Zone Output Budget Acceptance Thresholds

Goal: Convert the current multi-zone output-budget blockers into explicit acceptance thresholds for the smallest live Balfrin probe and the next larger review-only probe.

Capability gap reduced: The smallest multi-zone path blocks on `manifest_size_bytes`, but the acceptance thresholds and replay-critical exceptions are still spread across docs and tests.

Why this outranks alternatives: Reducer/manifest compression cannot be judged unless the target budget and non-negotiable replay fields are formalized first.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`
- `docs/hazard_output_profile_contract.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- Machine-readable budget thresholds for manifest bytes, total files, per-family files, sidecar counts, reducer chunks, retained replay-critical families, and package hashes.
- A validator mode that explains exactly which threshold is exceeded and whether the excess is replay-critical or compressible.
- Tests proving threshold failures remain distinct from missing authorization and dirty remote-state failures.

Definition of done:

- The multi-zone handoff has objective pass/fail budget criteria that can drive compression and later live-run authorization.

Boundaries: Budget contract only; no compression implementation, no live Balfrin submission, no scale-up authorization, no dropped replayability, and no operational claim.

### TB-294: Replay-Preserving Manifest Slimming Prototype

Goal: Prototype a replay-preserving compact manifest representation for the smallest multi-zone handoff that reduces manifest bytes without losing deterministic replay, hashes, merge order, or provenance.

Capability gap reduced: Multi-zone Balfrin execution is blocked by manifest-size pressure before the smallest live probe can run.

Why this outranks alternatives: Output size control must be proven on the current blocking artifact before adding more zones or workers.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/hazard_output_profile_contract.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `tests/test_balfrin_smallest_multi_zone_authorization_preflight.py`

Deliverables:

- A compact manifest mode that deduplicates repeated path prefixes, shared output-family metadata, and repeated command-plan fields while preserving replay-critical hashes and merge order.
- Before/after report with manifest bytes, sidecar counts, replay-critical retained fields, deterministic package hash, and threshold status from TB-293.
- Regression tests showing replay metadata is still complete and the previous `manifest_size_bytes` blocker is reduced or explicitly proven irreducible.

Definition of done:

- The smallest multi-zone package either passes the manifest threshold or reports a smaller, replay-critical residual blocker with evidence.

Boundaries: Manifest/package representation only; no live Balfrin submission, no reducer math change, no output data deletion, no scale-up authorization, and no operational claim.

### TB-295: Balfrin Postproc Microbenchmark Harness

Goal: Add a bounded Balfrin postprocessing microbenchmark harness that measures filesystem, manifest scanning, reducer merge, and hazard packaging overhead independently from full simulation scale.

Capability gap reduced: Execution efficiency is not under control because the repo lacks measured Balfrin postproc overhead curves for the workflow shell.

Why this outranks alternatives: The likely scaling wall is Python/output/reducer/filesystem pressure, so microbenchmarks should isolate those costs before larger live probes.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A microbenchmark package generator for synthetic file-family roots with configurable file count, manifest size, sidecar count, and reducer chunk count.
- A postproc-node measurement plan that records wall time, CPU time where available, peak RSS, file scan time, merge time, package time, and bytes/files touched.
- Local fixture tests for package generation and parser behavior.

Definition of done:

- The repo can prepare an exact bounded Balfrin postproc microbenchmark package that measures workflow-shell overhead separately from physics execution.

Boundaries: Package/harness generation only unless separately authorized for live execution; no live Balfrin submission by default, no simulation, no physical claims, no operational claim, and no heavy generated files committed.

### TB-296: Authorized Balfrin Postproc Microbenchmark Run

Goal: Execute one exact bounded Balfrin postproc microbenchmark run if separately authorized, or record the exact pre-submit blocker.

Capability gap reduced: Output and reducer efficiency remain projection-heavy without direct postproc-node measurements.

Why this outranks alternatives: A tiny synthetic postproc benchmark is lower risk than a larger multi-zone simulation and directly measures the suspected scaling wall.

Inspect first:

- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- If separate exact user authorization is present at execution time, one bounded SLURM postproc microbenchmark submission with fixed file-count/manifest-size parameters and deterministic run root.
- Preserved metrics for wall time, peak memory, file scan time, reducer merge time, package time, file counts, bytes, checksums, and SLURM accounting fields.
- If any preflight fails, a fail-closed blocker report with no submission.

Definition of done:

- The repo has either measured Balfrin postproc overhead evidence for a bounded synthetic scale point or one exact remaining pre-submit blocker.

Boundaries: Exact postproc microbenchmark only; live Balfrin submission requires separate explicit authorization at execution time; no simulation, no multi-zone hazard claim, no scale-up authorization, no retries without diagnosis, and no operational claim.

### TB-297: Hazard Builder Phase Timing Instrumentation

Goal: Add structured phase timing and memory telemetry to `build_hazard_layers.py` and its output-writer modules for input reading, accumulation, reducer merge, raster writing, COG/report writing, and manifest generation.

Capability gap reduced: Hazard-building efficiency cannot be controlled without phase-level measurements from real and fixture runs.

Why this outranks alternatives: Previous throughput evidence points at Python accumulation and output writing, but future optimization needs stable per-phase telemetry.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `scripts/hazard_output_reports.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_hazard_layers.py`

Deliverables:

- A stable timing JSON emitted by hazard-layer builds with per-phase wall time, input/output counts, bytes, grid dimensions, output-profile settings, and optional peak memory where available.
- Tests proving telemetry exists for fixture builds and does not change hazard outputs or manifest semantics.
- Documentation of timing fields in the throughput report or output-profile contract.

Definition of done:

- Every relevant hazard-layer build can produce comparable phase timing evidence without changing numerical outputs.

Boundaries: Instrumentation only; no performance optimization, no behavior change, no live Balfrin submission, no hazard-value changes, and no operational claim.

### TB-298: Hazard Accumulation Optimization Hypothesis Bench

Goal: Build a benchmark harness for candidate hazard-accumulation optimizations and require before/after evidence before any implementation is accepted.

Capability gap reduced: The repo has rejected broad performance churn once, but still lacks a safe way to evaluate targeted accumulation improvements.

Why this outranks alternatives: Execution efficiency must improve through measured hypotheses, not speculative rewrites of a fragile hazard builder.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_hazard_layers.py`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- A benchmark harness with representative fixture profiles for single-zone, smallest multi-zone, and output-heavy cases.
- Acceptance criteria for speedup, memory, output parity, deterministic manifests, and claim-boundary preservation.
- At least one no-op/baseline benchmark result that future optimization tasks must beat.

Definition of done:

- Future hazard-accumulation optimization work has a reproducible benchmark and objective acceptance thresholds.

Boundaries: Benchmark harness only; no optimization implementation unless trivially required for instrumentation, no live Balfrin submission, no hazard-value change, and no operational claim.

### TB-299: Reduced-Output Profile Enforcement In AOI Command Plans

Goal: Ensure every AOI and Balfrin command plan that can scale beyond tiny smoke defaults to the scalable reduced-output profile and fails closed on full grid CSV or full conditional-curve output.

Capability gap reduced: Output size is only partly controlled; command-plan drift can still reintroduce non-scalable output families.

Why this outranks alternatives: Preventing accidental high-output plans is cheaper and safer than cleaning up oversized run roots after execution.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/check_hazard_output_profile.py`
- `docs/hazard_output_profile_contract.md`
- `tests/test_pilot_command_plan.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A shared command-plan output-profile validator used by AOI and Balfrin planning paths.
- Fail-closed diagnostics for full grid CSV, full conditional curves, excessive worker/chunk sidecars, missing reduced-output flags, and missing rebuildability artifacts.
- Tests proving tiny smoke can opt into fixture-safe outputs while scalable plans require reduced-output defaults.

Definition of done:

- Scalable command plans cannot silently select output families known to be non-scalable.

Boundaries: Planning/profile enforcement only; no live Balfrin submission, no simulation, no output data deletion, no physical-probability semantics, and no operational claim.

### TB-300: Validation Output Budget Reduction Plan

Goal: Measure and reduce validation-output file fanout for target-area and multi-zone workflows while preserving replayability and required scientific diagnostics.

Capability gap reduced: Validation output has historically dominated file count and bytes, and can overwhelm useful hazard artifacts before Swiss-scale execution.

Why this outranks alternatives: Output size control is not complete until validation debug outputs are budgeted as strictly as hazard outputs.

Inspect first:

- `src/validation.rs`
- `scripts/generate_pilot_command_plan.py`
- `scripts/check_hazard_output_profile.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_pilot_command_plan.py`
- `tests/test_bounded_validation_output_profile.py`

Deliverables:

- A validation-output inventory for target-area and multi-zone plans, separating replay-critical files from diagnostic/debug files.
- A reduced validation-output mode or plan-level defaults that preserve manifests, hashes, summaries, and required trajectories while suppressing nonessential debug fanout.
- Tests proving reduced validation outputs remain replayable and evidence-preserving.

Definition of done:

- The largest validation-output families have explicit budgets and a reduced mode suitable for scalable AOI/Balfrin plans.

Boundaries: Validation output budgeting only; no physics change, no metric suppression without replacement summary evidence, no live Balfrin submission, no claim upgrade, and no operational claim.

### TB-301: Multi-Zone Local Scaling Ladder

Goal: Run a deterministic local scaling ladder over increasing zone/scenario counts to measure output, reducer, manifest, and hazard-builder timing before another live Balfrin scale step.

Capability gap reduced: Multi-zone pressure is currently scratch/fixture-backed at limited points, with no systematic ladder showing where bottlenecks appear.

Why this outranks alternatives: A local ladder can cheaply identify the next measured breakpoint and prevent premature live Balfrin submission.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/check_hazard_output_profile.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- A local scaling-ladder helper or report for 1, 2, 4, 8, and 12 zone-equivalent fixture workloads using reduced-output profiles.
- Measurements for runtime, phase timing if TB-297 exists, file counts, bytes, manifest bytes, reducer sidecars, and first bottleneck.
- Tests for deterministic ladder fixture generation and blocked budget classifications.

Definition of done:

- The repo has systematic local evidence for how output and reducer pressure grows before requiring live Balfrin execution.

Boundaries: Local/fixture scaling only; no live Balfrin submission, no distributed execution, no physical credibility claim, no Swiss-wide claim, and no operational claim.

### TB-302: Balfrin Run-Root Output Budget Auditor

Goal: Add a run-root auditor that can inspect preserved Balfrin roots and classify output budget compliance after execution.

Capability gap reduced: Post-run evidence preservation exists, but output-budget compliance needs to be measured directly from run roots, not only predicted from handoff packages.

Why this outranks alternatives: Scale claims require proving the actual run root stayed within file, byte, manifest, sidecar, and replayability budgets.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/balfrin_probe_slurm_driver.md`
- `tests/test_balfrin_probe_preservation_gate.py`

Deliverables:

- A read-only auditor for Balfrin run roots that reports per-family files/bytes, manifest bytes, sidecar counts, reducer chunks, hashes, missing replay-critical artifacts, and budget status.
- Integration into post-run collector or preservation-gate summaries.
- Fixture tests for compliant, oversized, incomplete, and missing-run-root cases.

Definition of done:

- Any future Balfrin run root can be classified against the output/reducer budget from preserved artifacts.

Boundaries: Read-only auditing only; no remote mutation, no live Balfrin submission, no new run, no claim upgrade, and no operational claim.

### TB-303: Scale Evidence Dashboard For Workers

Goal: Produce a compact worker-facing scale dashboard that summarizes the latest measured and blocked evidence for Balfrin execution efficiency, output size, reducer pressure, and next safe action.

Capability gap reduced: Scale evidence is fragmented across maturity snapshots, reducer docs, decision gates, and run-root reports.

Why this outranks alternatives: Workers need one short status surface to avoid re-running stale paths or treating projections as measured scale evidence.

Inspect first:

- `scripts/print_agent_task_context.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`

Deliverables:

- A scale dashboard command or extension to task context with latest measured tiers, blocked tiers, output-budget status, efficiency measurements, live-run authorization status, and next recommended scaling task.
- Clear labels for `measured_on_balfrin`, `fixture_backed`, `scratch_local`, `projection_only`, and `blocked_pre_submit`.
- Tests that prevent blocked multi-zone evidence from appearing as measured scale capability.

Definition of done:

- A worker can quickly answer whether output size and execution efficiency are under control for each scale tier without reading the whole repository.

Boundaries: Status/dashboard only; no live Balfrin submission, no new run, no claim upgrade, no scale-up authorization, and no operational claim.

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
