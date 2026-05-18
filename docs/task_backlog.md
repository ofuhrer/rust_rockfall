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

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

## Active Tasks

### TB-204: Enforce Multi-Zone Output And Reducer Constraints In Handoff

Goal: Thread measured multi-zone reducer-pressure constraints into the Balfrin multi-release-zone handoff generator so oversized or unsafe dry-run packages fail closed.

Capability gap reduced: Multi-zone handoff packages can currently describe reducer pressure without necessarily enforcing measured output, chunk, and merge constraints.

Why this outranks alternatives: The scratch multi-zone probe already showed manifest, file-family, and reducer-runtime pressure; the next package should enforce those constraints before any authorization decision.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- Handoff-package constraints for maximum simultaneous release-zone batch size, reducer chunk count, reducer worker count, manifest bytes, file count, and output-family bytes.
- Fail-closed package classification when requested multi-zone settings exceed measured reducer constraints.
- Command-plan or SBATCH notes that preserve deterministic merge order and restart/replay checkpoints.
- Focused tests for acceptable, warning, and blocked oversized-package cases.

Definition of done:

- The multi-zone handoff generator enforces measured reducer constraints deterministically, records the constraint source, and rejects unsafe dry-run packages without submitting any job.

Boundaries: No live Balfrin job, no distributed reducer, no MPI/GPU, no physics change, no generated heavy outputs committed, and no operational claim.

### TB-205: Smallest Bounded Multi-Zone Balfrin Probe Package

Goal: Produce the smallest reviewable multi-zone Balfrin probe package that would be worth explicitly authorizing after the decision gate.

Capability gap reduced: Missing execution-ready package for the first measured multi-release-zone Balfrin evidence step.

Why this outranks alternatives: Full-scale Balfrin demonstration credibility depends on at least one measured multi-zone run, but the first candidate must be bounded by reducer and preservation constraints.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A scratch/ignored handoff package with exact release-zone count, scenario count, trajectory count, seed policy, command plan, SBATCH script, and output roots.
- Estimated runtime, storage, file count, manifest pressure, reducer pressure, and preservation-gate checklist for that smallest run.
- A blocked-pending-authorization classification that states the exact command to review if authorization is granted later.
- Focused tests for package determinism, command-plan shape, and blocked-missing-input behavior.

Definition of done:

- The package is deterministic, reviewable from tracked inputs plus ignored scratch outputs, passes the preservation checklist in dry-run form, and remains unsubmitted unless the conversation explicitly authorizes execution.

Boundaries: Package only by default; no live Balfrin job, no scale-up authorization, no distributed execution, no operational claim, and no generated heavy outputs committed.

### TB-206: Target-Area Metrics Completion Rerun Package

Goal: Prepare a bounded Balfrin rerun package whose only purpose is closing missing target-area peak-memory and split validation/hazard output metrics.

Capability gap reduced: Incomplete measured target-area evidence caused by missing memory and split-output provenance.

Why this outranks alternatives: If the next live action is not multi-zone, the most valuable single-zone/target-area rerun is one that closes known evidence gaps rather than producing another broad package.

Inspect first:

- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/submit_balfrin_probe.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A dry-run rerun command plan and SBATCH package focused on peak memory, split validation/hazard output bytes and counts, hashes, run-root paths, reducer state, and replay metadata.
- A preservation checklist that fails closed unless all required metrics and run-root files are declared.
- A comparison against the existing target-area run identifying exactly which fields the rerun is meant to close.
- Focused tests for complete, partial, and missing-rerun-package classifications.

Definition of done:

- The rerun package is reproducible and explicitly scoped to metrics completion, with no live submission and no claim that the existing measured target-area evidence has been upgraded before a real rerun occurs.

Boundaries: No live Balfrin submission, no new scientific interpretation, no scale-up authorization, no operational claim, and no fabricated metrics.

### TB-207: Real Chant Sura Public-Context Staging Verification

Goal: Verify real staged Chant Sura / Fluelapass public-context inputs when present, while preserving deterministic blocked reports when the clean checkout lacks those inputs.

Capability gap reduced: Second-site portability remains fixture-backed and blocked on real public-context staging.

Why this outranks alternatives: Tschamut coupling is still a major portability risk; a real-context verifier is the next useful step before any second-site ensemble or hazard build.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A verifier or verifier mode that checks staged AOI catalog, terrain crop, terrain metadata, source-zone metadata, scenario table, source-scenario policy, and public context product metadata.
- Product-by-product `ready`, `missing`, `deferred`, or `metadata_mismatch` classifications with exact paths and required fields.
- Integration with the Chant Sura dry-run report so real staged context changes the classification without representing synthetic fixtures as public evidence.
- Focused tests for clean-checkout blocked, fixture-backed, and staged-real-like metadata paths.

Definition of done:

- The verifier distinguishes real staged public-context readiness from synthetic fixtures and clean-checkout absence, and no second-site ensemble or hazard run is triggered.

Boundaries: No downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, and no physical validation claim.

### TB-208: Independent Physical Evidence Intake Pilot

Goal: Populate one independent observed runout/deposition evidence intake package if data are available, or emit an exact blocked acquisition report if they are not.

Capability gap reduced: Physical credibility remains not established because observed benchmark evidence, release-zone provenance, block-population evidence, and calibration separation are not populated.

Why this outranks alternatives: Execution success no longer resolves the largest scientific gap; the project needs independent physical evidence rather than more packaging around conditional diagnostics.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/validation_data_schema.md`
- `validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml`

Deliverables:

- A benchmark intake artifact or blocked report with manifest, observed geometry/provenance fields, uncertainty fields, objective-function readiness, and calibration/validation separation.
- Dataset-role classification for observed runout/deposition, release-zone provenance, block-population evidence, calibration inputs, validation inputs, and holdout data.
- A physical-credibility gap update that remains `not_established` unless real accepted evidence is present.
- Focused tests for accepted fixture shape, missing-evidence blocked report, and claim-boundary hygiene.

Definition of done:

- The intake path is executable and fail-closed, and the report clearly distinguishes real evidence, fixture shape, missing data, and future calibration requirements.

Boundaries: No calibration, no parameter fitting, no validation-status upgrade without real evidence, no annual-frequency or physical-probability claim, and no operational claim.

### TB-209: Multi-Zone Hazard Builder Throughput Profile

Goal: Profile hazard-layer post-processing on the multi-zone scratch fixture and identify the first concrete throughput or output-pressure bottleneck.

Capability gap reduced: Unknown hazard-builder pressure for multi-zone products after the reducer probe and writer-module split.

Why this outranks alternatives: The next measured Balfrin step may be limited by post-processing and output fan-out before the Rust trajectory kernel.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/hazard_output_writers.py`
- `scripts/hazard_output_manifests.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/hazard_output_profile_contract.md`

Deliverables:

- A deterministic profiling helper or mode that uses a multi-zone scratch fixture and reports read time, accumulation time, reducer merge time, manifest time, raster write time, COG/export time where applicable, and report-rendering time.
- Output-pressure measurements by layer family, file family, manifest family, and optional COG/GIS family.
- One bounded optimization recommendation with evidence, plus a no-change label if the profile is too small to justify optimization.
- Focused tests for profile schema, deterministic fixture generation, and blocked-missing-input behavior.

Definition of done:

- The profile is reproducible without live Balfrin artifacts, identifies the first bottleneck or declares insufficient scale, and does not change hazard values or output semantics.

Boundaries: Profiling only; no broad hazard-builder rewrite, no probability-semantics change, no GIS/COG claim upgrade, and no generated heavy outputs committed.

### TB-210: Full-Scale Balfrin Demonstration Readiness Matrix

Goal: Define the evidence and execution gates that must be satisfied before the project can call a Balfrin run a full-scale demonstration.

Capability gap reduced: Ambiguous use of "full-scale Balfrin demonstration" after multiple single-zone, target-area, dry-run, and fixture-backed evidence packages.

Why this outranks alternatives: The phrase "full-scale" needs a concrete gate before management, execution, or scientific reports start using it as a maturity label.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- A readiness matrix covering measured multi-zone execution, preservation gate, reducer constraints, output budget, restart/replay, GIS package scope, command-plan reproducibility, clean-checkout behavior, and scientific claim boundaries.
- Gate statuses that distinguish measured, fixture-backed, dry-run, blocked, unavailable, and unauthorized evidence.
- A recommendation on whether the next milestone should be metrics completion, smallest multi-zone measurement, real second-site staging, or physical-evidence intake.
- Focused tests or consistency checks for required matrix sections and disallowed claim language.

Definition of done:

- The readiness matrix is deterministic, cites the relevant evidence helpers, and keeps full-scale demonstration readiness separate from operational, annual-frequency, physical-probability, and risk claims.

Boundaries: Gate definition only; no live execution, no claim upgrade, no new management package replacing existing evidence, and no operational or annual-frequency semantics.

### TB-211: Authorization-Gated Multi-Zone Balfrin Execution

Goal: Execute, or explicitly block, the smallest bounded multi-zone Balfrin probe only after the current decision gate and package task select it and the user gives explicit live-run authorization.

Capability gap reduced: Missing measured many-release-zone Balfrin evidence beyond fixture-backed and dry-run handoff packages.

Why this outranks alternatives: The external review recommendation for a true multi-zone Balfrin demonstration is scientifically important, but it should only follow the preservation, reducer-constraint, and smallest-package gates already active in `TB-203` through `TB-205`.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- An authorization-aware execution helper or mode that refuses to submit without an explicit reviewed handoff package and live-run authorization record.
- A measured run-root report when execution is authorized, including runtime, peak memory, validation/hazard split output counts and bytes, reducer pressure, manifest pressure, restart/replay metadata, checksums, and failure behavior.
- A deterministic `blocked_missing_authorization` or `blocked_missing_inputs` report when live execution is not authorized or required staged inputs are absent.
- Focused tests for authorized fixture execution metadata, blocked-missing-authorization, blocked-missing-input, and incomplete-run-root classifications.

Definition of done:

- The first multi-zone Balfrin execution path is gated by explicit authorization, produces a preservation-checked measured run root when run, and cannot silently promote incomplete multi-zone evidence.

Boundaries: No live execution without explicit authorization, no larger-than-reviewed package, no distributed execution, no operational claim, no annual-frequency or physical-probability semantics, and no fabricated metrics.

### TB-212: Real Second-Site Prepared-Pilot Dry Run

Goal: Compose a real Chant Sura / Fluelapass prepared-pilot dry run from staged public-context inputs when they exist, while emitting a deterministic blocked report when they do not.

Capability gap reduced: Tschamut-specific coupling remains unresolved until a real second-site path can run beyond synthetic fixtures and metadata-only readiness.

Why this outranks alternatives: `TB-207` verifies whether real second-site inputs are staged; this task uses those verified inputs to exercise the AOI preparation, release-candidate, scenario, command-plan, and optional tiny handoff path without claiming operational readiness.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`

Deliverables:

- A deterministic second-site prepared-pilot report using real staged terrain/context/source/scenario metadata when available.
- Release-candidate, scenario-table, command-plan, ignored-root layout, and blocked-input summaries that preserve real-versus-fixture provenance.
- A permission-gated tiny execution handoff only if all required staged inputs are real and the user explicitly authorizes it.
- Focused tests for clean-checkout blocked, fixture-backed blocked, staged-real-like dry run, and forbidden output-root behavior.

Definition of done:

- Chant Sura / Fluelapass can be classified as real-staged dry-run ready or explicitly blocked using the same workflow shape as the Balfrin/Tschamut path, without treating synthetic fixtures as public evidence.

Boundaries: No downloads, no ensemble execution without explicit authorization, no synthetic public-context evidence, no physical-validation claim, no operational claim, and no claim that Chant Sura is ready when required real inputs are absent.

### TB-213: Evidence-Gated Balfrin Demonstration Closure Package

Goal: Produce one coherent Balfrin demonstration closure package only after new measured evidence from a metrics-completion rerun or authorized multi-zone probe exists.

Capability gap reduced: Reviewers currently have to reconcile many reports to decide whether Balfrin is plausibly extensible toward larger Swiss workflows.

Why this outranks alternatives: A closure package is useful after new measured evidence, but premature synthesis would add process without reducing the current evidence gaps.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- A reproducible closure report or package that consolidates runtime evidence, preservation status, restartability, reducer/output scaling, AOI/release/scenario automation, GIS readiness, second-site portability, and scientific claim boundaries.
- Strict provenance labels distinguishing measured, fixture-backed, dry-run, blocked, unavailable, unauthorized, and historical evidence.
- A direct reviewer-facing answer to whether the current Balfrin evidence is plausibly extensible toward larger Swiss workflows.
- A fail-closed `blocked_no_new_measured_evidence` classification if neither a metrics-completion rerun nor an authorized multi-zone run has produced new preservation-checked evidence.
- Focused tests for complete measured evidence, mixed-provenance warning, and blocked-no-new-evidence classifications.

Definition of done:

- The closure package can be regenerated deterministically, answers the demonstration-readiness question without requiring a repository reread, and refuses to upgrade maturity labels without new measured evidence.

Boundaries: No new live execution, no operational claim, no annual-frequency or risk semantics, no physical-credibility upgrade without independent evidence, and no replacement of the authoritative backlog or work log.

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
