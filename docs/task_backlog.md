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

### TB-489: Execute The Next Bounded Balfrin Postproc Probe

Goal: Run the next repository-gated bounded Balfrin `postproc` probe that is ready after local candidate/scenario and output-pressure checks.

Capability gap reduced: Converts scale readiness into measured execution evidence instead of projection-only status.

Why this outranks alternatives: The current scale frontier needs measured larger multi-zone hazard execution, not another local-only summary.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `scripts/submit_balfrin_probe.py`
- `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`

Deliverables:

- Run the existing readiness/access/output-budget gates and submit only if they are ready under the standing `postproc` clearance.
- Preserve the run root and collect runtime, memory, output-file, output-byte, reducer, and manifest metrics using existing collectors.

Definition of done:

- Either one bounded `postproc` run completes with preserved measured evidence, or the attempt fails closed before submission with a concrete blocker and the smallest next unblock action.

Boundaries: `postproc` only under existing clearance; no non-postproc partition, distributed execution, Swiss-wide scale-up claim, operational claim, annual-frequency claim, or physical-probability claim.

### TB-490: Compare Measured Regional Split Against Projections

Goal: Thread the measured regional split evidence into the existing scenario-cardinality and output-tier projection surfaces so the next scale recommendation is based on measured deltas.

Capability gap reduced: Replaces stale projection-only scale recommendations with measured regional-split comparison evidence.

Why this outranks alternatives: The maturity snapshot says the regional split branch is now measured and the next blocker is comparison work before further live recommendation.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_regional_gis_cog_pressure.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Update existing scale/projection surfaces to consume the measured regional split metrics where they currently rely on older projection-only or failed-closed branches.
- Produce one refreshed recommendation that names the next executable measured run or blocker.

Definition of done:

- Focused scale/projection tests pass, the refreshed output differentiates measured regional split evidence from projections, and no new dashboard/report script is added.

Boundaries: Evidence comparison only; no new live run, no operational claim, no Swiss-wide authorization, and no physical-probability or annual-frequency semantics.

### TB-538: Separate Extreme-Layer Support From Magnitude Sensitivity

Goal: Make the local extreme-layer smoke explain whether changes come from support/nodata differences or from magnitude changes on shared support.

Capability gap reduced: Reduces scientific ambiguity in max kinetic-energy and jump-height comparisons.

Why this outranks alternatives: Extreme-layer sensitivity can otherwise look like physics variation when it is actually raster support or nodata behavior.

Inspect first:

- `scripts/summarize_extreme_layer_sensitivity_smoke.py`
- `scripts/rank_local_hazard_layer_fragility.py`
- `tests/test_extreme_layer_sensitivity_smoke.py`
- `tests/test_local_hazard_layer_fragility.py`

Deliverables:

- Update existing sensitivity output to report shared-support magnitude deltas separately from support/nodata deltas.
- Add focused tests that exercise both support drift and same-support magnitude drift.

Definition of done:

- Local sensitivity tests pass and the report names which differences are interpretation-relevant versus support diagnostics.

Boundaries: Existing tiny fixtures only; no new hazard model, no tuning, no operational threshold, and no physical-probability claim.

### TB-539: Promote Denominator And Deposition Audits Into A Single Interpretation Gate

Goal: Make map interpretation fail closed unless conditional denominator provenance and trajectory-to-deposition traceability are both explicit.

Capability gap reduced: Prevents local scientific summaries from treating deposition outputs as interpretable when the denominator or traceability semantics are ambiguous.

Why this outranks alternatives: A combined interpretation gate removes a recurring source of false confidence without adding a new workflow surface.

Inspect first:

- `scripts/audit_conditional_denominator_provenance.py`
- `scripts/audit_trajectory_deposition_traceability.py`
- `scripts/recommend_local_scientific_backlog.py`
- `tests/test_conditional_denominator_provenance.py`
- `tests/test_trajectory_deposition_traceability.py`

Deliverables:

- Thread the two existing audits into one existing recommendation or audit output that clearly passes or fails map interpretation readiness.
- Add focused tests for the combined fail-closed and pass cases.

Definition of done:

- The local recommendation or audit command reports one interpretation gate result with exact failing evidence and the next executable local recovery command.

Boundaries: Consolidate existing audits only; no new standalone dashboard, no claim upgrade, no annual-frequency semantics, and no tuning.

### TB-540: Wire Holdout And Calibration Separation Into Validation Guardrails

Goal: Ensure validation evidence summaries warn or fail closed when holdout overlap or selected-parameter leakage is detected.

Capability gap reduced: Protects scientific validation from accidental calibration/validation leakage.

Why this outranks alternatives: The existing holdout and calibration separation checks need to govern validation evidence, not remain disconnected diagnostics.

Inspect first:

- `scripts/audit_chant_sura_holdout_split.py`
- `scripts/check_calibration_separation_preflight.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `tests/test_chant_sura_holdout_split_audit.py`
- `tests/test_calibration_separation_preflight.py`

Deliverables:

- Update an existing validation evidence or preflight surface to consume holdout and calibration separation results.
- Add focused tests covering a clean separation case and a leakage/overlap warning case.

Definition of done:

- Focused guardrail tests pass and the validation evidence command names the exact dataset or parameter source that blocks interpretation when separation fails.

Boundaries: Fixture-backed guardrails only; no recalibration, no new validation claim, no parameter tuning, and no Balfrin dependency.

### TB-541: Create A Local Tschamut Micro-Validation Smoke From Existing Fixtures

Goal: Provide one tiny local command path that produces a trajectory sample and one hazard layer from existing Tschamut-compatible fixtures.

Capability gap reduced: Gives contributors a reproducible local scientific smoke that exercises simulation-to-layer plumbing without large data or Balfrin.

Why this outranks alternatives: A small executable proof is more useful than another overview when validating local changes to scientific plumbing.

Inspect first:

- `validation/cases/probabilistic_phase1_smoke.yaml`
- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_hazard_layers.py`
- `README.md`

Deliverables:

- Document or wire an existing tiny local command that writes outputs under an ignored scratch root and verifies one trajectory artifact plus one hazard layer.
- Add a focused test or fixture-backed command proof that keeps runtime small.

Definition of done:

- The micro-smoke command is discoverable from existing repo surfaces, runs locally without Balfrin, and its focused test passes.

Boundaries: No large AOI run, no live data acquisition, no new workflow framework, no operational claim, and no statistical validation claim.

### TB-542: Add Deterministic Energy-Budget Checks To Minimal Smoke

Goal: Verify that the minimal trajectory smoke preserves deterministic sample count and bounded energy fields.

Capability gap reduced: Adds a physics-adjacent regression check to the local smoke path instead of validating only file existence.

Why this outranks alternatives: Energy and sample-count regressions would undermine every downstream hazard layer, and they are cheap to catch locally.

Inspect first:

- `examples/inclined_plane.json`
- `tests/terrain_edge_cases.rs`
- `src/main.rs`
- `src/io.rs`

Deliverables:

- Add or tighten a Rust test around the existing inclined-plane example that checks deterministic sample count and finite, bounded energy outputs.
- Keep the test small enough for normal local and GitHub Actions runs.

Definition of done:

- `cargo test` for the focused Rust test passes and would fail on non-finite or unexpectedly unbounded energy output.

Boundaries: No physics model rewrite, no parameter tuning, no new example family, and no performance-heavy ensemble.

### TB-543: Tighten Same-Scale Uncertainty Summary Around Scientific Decision Thresholds

Goal: Make same-scale uncertainty summaries identify which layer differences affect interpretation and which are diagnostic-only.

Capability gap reduced: Converts same-scale comparison output into a clearer scientific decision aid.

Why this outranks alternatives: Same-scale uncertainty is already measured locally; the next leverage is making its interpretation boundary explicit.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_same_scale_uncertainty_envelope.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `tests/test_spatial_same_scale_uncertainty.py`

Deliverables:

- Update existing uncertainty output to classify differences as interpretation-relevant or diagnostic-only using existing thresholds or explicit conservative defaults.
- Add focused tests for both classifications.

Definition of done:

- Focused same-scale uncertainty tests pass and the summary makes no claim upgrade while naming the relevant layer and threshold basis.

Boundaries: No new uncertainty theory, no threshold tuning from outcomes, no operational decision threshold, and no new report script.

### TB-544: Make Source-Zone Candidate Review Produce A Rejection-Reasons Summary

Goal: Show why source-zone candidates are accepted or rejected so local scientific review can fix the highest-impact candidate defects first.

Capability gap reduced: Improves source-zone reproducibility and reviewability before any larger scenario run.

Why this outranks alternatives: Candidate quality controls the scientific meaning of every simulated scenario and is inspectable locally.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/run_aoi_hazard_workflow.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- Extend an existing candidate review or workflow output to summarize accepted candidates and rejected candidates by reason.
- Add focused tests using current candidate fixtures.

Definition of done:

- Local candidate review reports counts by rejection reason and points to the smallest candidate fixture or metadata correction needed next.

Boundaries: No new source-zone algorithm, no manual digitizing, no new GIS dependency, no claim that candidate selection is validated.

### TB-545: Measure Local Candidate Scenario Cardinality Pressure

Goal: Quantify how local source-zone and scenario choices expand trajectory count before any larger execution.

Capability gap reduced: Connects scientific scenario design to scalability pressure using local fixtures.

Why this outranks alternatives: Scenario cardinality is a shared scientific and performance bottleneck, and it can be measured entirely from local fixtures.

Inspect first:

- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `tests/test_aoi_scenario_preview.py`
- `tests/test_management_aoi_scenario_pressure.py`

Deliverables:

- Update existing preview or pressure summaries to report scenario count, expected trajectory count, and the first driver of cardinality growth.
- Add focused tests using existing review package fixtures.

Definition of done:

- The local preview command reports the first scaling pressure in a way that can guide either scenario reduction or measured execution planning.

Boundaries: Local estimation only; no execution on external compute, no cluster submission, no distributed execution, and no scientific claim upgrade.

### TB-546: Make Rebuildable Reduced Output The Default Local Hazard Smoke Recommendation

Goal: Steer local hazard smoke and replay recommendations toward rebuildable reduced outputs by default.

Capability gap reduced: Reduces local output-volume drift while preserving reproducibility through rebuild instructions.

Why this outranks alternatives: Output pressure is already a scaling bottleneck, and default local recommendations should avoid producing heavy artifacts unnecessarily.

Inspect first:

- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/hazard_output_profile_contract.md`
- `tests/test_hazard_rebuild_output_profile.py`

Deliverables:

- Update existing command-plan or output-profile surfaces so local smoke/replay guidance prefers the rebuildable reduced profile when scientifically sufficient.
- Add focused tests that preserve access to fuller outputs when explicitly requested.

Definition of done:

- Local command guidance names the reduced rebuildable profile, the rebuild command or metadata needed to recover full outputs, and the focused tests pass.

Boundaries: No deletion of existing artifacts, no forced behavior change for heavy runs, no new output contract, and no claim that reduced output is always sufficient.

### TB-547: Add Local GIS/COG Package Roundtrip Smoke On Tiny Fixture

Goal: Prove that a tiny local same-scale package can be converted and audited as GIS/COG-ready without large artifacts.

Capability gap reduced: Moves GIS handoff readiness from static checks toward an executable local roundtrip.

Why this outranks alternatives: GIS package usability is a user-facing validation frontier and can be tested cheaply on tiny fixtures.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/prototype_cog_conversion.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `tests/test_cog_conversion_prototype.py`
- `tests/test_same_scale_cog_package_conversion.py`

Deliverables:

- Add or tighten a tiny fixture-backed conversion-plus-audit path using existing COG helpers.
- Ensure the output reports both conversion success and any missing GIS metadata needed for user-facing use.

Definition of done:

- Focused COG conversion/audit tests pass and the roundtrip can run locally without large rasters or external services.

Boundaries: Tiny fixtures only; no QGIS automation, no publishing, no new GIS package format, and no operational map claim.

### TB-548: Strengthen Multisite Source/Scenario Portability Checks

Goal: Make multisite audits distinguish portable source/scenario semantics from site-specific assumptions.

Capability gap reduced: Reduces the risk that Tschamut-specific scenario assumptions silently contaminate Chant Sura or future sites.

Why this outranks alternatives: Multisite scientific validation depends on knowing which assumptions travel and which must be restated per site.

Inspect first:

- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/test_multisite_source_scenario_contract.py`
- `tests/test_pilot_command_plan.py`

Deliverables:

- Update existing audit or command-plan output to name portable fields, site-specific fields, and the next local fixture/staging action for missing semantics.
- Add focused tests for at least one portable and one site-specific field.

Definition of done:

- The multisite audit gives an actionable local result without requiring Balfrin and focused tests pass.

Boundaries: No new contract file unless consolidation requires it, no new site onboarding, no live data acquisition, and no validation claim upgrade.

### TB-549: Add Observed-Evidence Intake Acceptance Smoke

Goal: Exercise accepted and rejected observed runout/deposition evidence packages locally and explain why accepted intake is not yet validation evidence.

Capability gap reduced: Clarifies the boundary between evidence ingestion and scientific validation.

Why this outranks alternatives: Observed evidence intake is essential for validation, but premature interpretation would create false scientific confidence.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `tests/test_observed_runout_deposition_intake_contract.py`
- `tests/fixtures/observed_runout_deposition_intake_contract/accepted_fixture.yaml`

Deliverables:

- Add or tighten fixture-backed acceptance and rejection cases in the existing intake summary/tests.
- Ensure accepted intake output explicitly states the remaining validation or calibration evidence gap.

Definition of done:

- Focused intake tests pass and the local intake command reports accepted/rejected evidence packages plus the missing validation step.

Boundaries: No new observed dataset, no calibration, no validation claim, no annual-frequency claim, and no new intake framework.

### TB-550: Consolidate Local Scientific Recommendation Output Into Next Executable Commands

Goal: Make the local scientific backlog recommendation report map each top local follow-up to an exact executable command and expected measurement.

Capability gap reduced: Turns local scientific prioritization into concrete execution guidance for the next autonomous worker.

Why this outranks alternatives: The repo already has many local diagnostics; the highest leverage is making the next command unambiguous without adding more files.

Inspect first:

- `scripts/recommend_local_scientific_backlog.py`
- `scripts/lib/local_scientific_progress.py`
- `tests/test_local_scientific_backlog_recommendation.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Update existing recommendation output so each ranked local scientific follow-up includes one executable command and the measurement or artifact it should produce.
- Add focused tests that guard against recommendations with no next command.

Definition of done:

- The recommendation command passes focused tests and its top local-only entries are directly executable from the repository checkout.

Boundaries: No new roadmap document, no new backlog generator, no Balfrin dependency, no claim upgrade, and no placeholder commands.

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
