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

### TB-249: Chant Sura Real Core-Input Staging Verification

Goal: Convert the Chant Sura / Fluelapass real-context gate from fixture-ready scaffolding toward real-input readiness by verifying whether locally staged terrain metadata, AOI tile catalog, source-zone metadata, scenario table, and policy records exist and are non-synthetic.

Capability gap reduced: Second-site portability remains blocked because the current candidate has fixture-backed core readiness but missing or deferred real public-context products and metadata.

Why this outranks alternatives: A second-site prepared pilot is the next portability milestone, but it must start with real staged core inputs rather than synthetic fixtures or downloads.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `tests/test_chant_sura_real_context_readiness_gate.py`

Deliverables:

- A stricter real-core-input classification that separates real staged files, fixture-backed files, metadata mismatches, missing rows, and deferred public-context products.
- A no-download verifier report naming the first non-synthetic missing input and the exact path or metadata field needed.
- Focused tests for fixture-backed blocked, partial-real, metadata-mismatch, and ready-real-core classifications.

Definition of done:

- The Chant Sura gate can tell whether real core inputs, not just fixture scaffolding, are ready for a prepared-pilot dry run.

Boundaries: No downloads, no second-site ensemble, no synthetic public-context evidence, no operational claim, no physical-validation claim, and no generated heavy outputs committed.

### TB-250: Chant Sura Missing-Input Acquisition Handoff

Goal: If TB-249 reports missing real core inputs, produce one no-download acquisition/staging handoff that names the exact files, metadata fields, and authorization decisions needed before a real-input dry run.

Capability gap reduced: Second-site portability can otherwise stall after a verifier report without a concrete next operator action.

Why this outranks alternatives: A blocked verifier is useful only if it points to a bounded acquisition path rather than another fixture-backed dry run.

Inspect first:

- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A no-download handoff report for the first missing real core-input category, with expected source product, local path, metadata contract, and authorization/defer status.
- A deterministic recommendation of `ready_no_handoff_needed`, `stage_local_existing_input`, `request_download_authorization`, or `defer_second_site`.
- Tests for ready-real-core, missing terrain metadata, missing AOI tile catalog, and missing source/scenario/policy records.

Definition of done:

- A worker or operator can see the next concrete Chant Sura acquisition/staging action without treating fixtures as public evidence.

Boundaries: Handoff only; no downloads, no second-site ensemble, no generated heavy outputs committed, no physical-validation claim, and no operational claim.

### TB-251: Real-Input Chant Sura Prepared-Pilot Dry Run

Goal: Run the AOI-to-prepared-pilot dry-run path for Chant Sura only when TB-249 reports real staged core inputs, otherwise emit a deterministic blocked report.

Capability gap reduced: The repo needs a real-input second-site workflow proof before it can claim portability beyond the current primary demonstration site.

Why this outranks alternatives: This moves second-site work from acquisition planning into executable workflow evidence while preserving fail-closed boundaries.

Inspect first:

- `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`

Deliverables:

- A real-input prepared-pilot dry-run report with terrain, source-zone, scenario, command-plan, ignored-root, and blocked public-context classifications.
- A `blocked_missing_real_core_inputs` report when TB-249 is not ready, with a pointer to the TB-250 acquisition handoff when applicable.
- Tests proving fixture-backed inputs cannot produce a ready second-site classification.

Definition of done:

- Chant Sura can either produce a real-input prepared-pilot dry-run package or state exactly why it remains blocked, without representing fixtures as public evidence.

Boundaries: Dry run only; no downloads, no ensemble execution, no synthetic evidence claim, no physical-validation claim, no operational claim, and no generated heavy outputs committed.

### TB-252: Observed Benchmark Candidate Acquisition Triage

Goal: Identify one concrete candidate path for real observed runout/deposition benchmark evidence, or produce a precise blocked acquisition report if no candidate can be staged.

Capability gap reduced: The largest scientific gap remains physical credibility, and the current observed-intake machinery is schema-ready but lacks real benchmark inputs.

Why this outranks alternatives: Execution metrics and multi-zone scaling do not establish scientific credibility; the next scientific step is acquiring or explicitly failing to acquire independent observed evidence.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/validation_data_schema.md`
- `docs/public_benchmark_framework.md`
- `tests/test_observed_runout_deposition_intake_contract.py`

Deliverables:

- A candidate-acquisition report listing available local candidates, required external acquisition actions, licensing/provenance blockers, and first missing geometry/provenance/uncertainty fields.
- A recommendation of `stage_candidate`, `blocked_no_candidate`, `blocked_license_or_provenance`, or `defer_scientific_claim`.
- Tests for local candidate present, no candidate, and candidate missing uncertainty/provenance cases.

Definition of done:

- A worker can act on one real observed-evidence candidate or see exactly why the physical-evidence path remains blocked.

Boundaries: Acquisition triage only; no downloads unless separately authorized, no calibration, no parameter fitting, no validation-status upgrade, no annual-frequency or risk semantics, and no operational claim.

### TB-253: First Real Observed Benchmark Intake Integration

Goal: If TB-252 identifies and stages a real observed benchmark candidate, integrate it through the observed runout/deposition intake contract while keeping calibration and claim boundaries explicit.

Capability gap reduced: Physical credibility cannot improve until a real observed benchmark package passes the intake contract and is separated from calibration and holdout roles.

Why this outranks alternatives: A successful real intake would move the scientific evidence base more than another workflow report; a failed intake would still clarify the exact evidence blocker.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_observed_runout_deposition_intake_contract.py`

Deliverables:

- A real-input intake report with geometry, provenance, uncertainty, calibration-role, validation-role, and holdout-eligibility classifications.
- A physical-credibility gap update that remains `not_established` unless the evidence genuinely satisfies the required intake boundary.
- Rejection tests for missing geometry, missing provenance, missing uncertainty, ambiguous calibration role, and fixture-only inputs.

Definition of done:

- The repo can accept or reject one real observed benchmark package deterministically, and any accepted intake is not confused with calibration, annual-frequency, or operational validation.

Boundaries: Intake only; no calibration, no parameter fitting, no source-frequency semantics, no annual-frequency or risk semantics, no operational claim, and no claim upgrade beyond what the accepted evidence supports.

### TB-254: Release-Zone, Block-Population, And Source-Frequency Evidence Triage

Goal: Triage the next real-evidence acquisition blockers for field-supported release zones, block-population evidence, and source-frequency records without implementing physical probability semantics.

Capability gap reduced: Observed runout intake alone does not close the physical-credibility gap; release provenance, block-population, and source-frequency evidence remain separate missing inputs.

Why this outranks alternatives: The repository has already built blocker fields for these categories, but it still lacks a concrete candidate acquisition path or defer decision for each.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `docs/target_area_physical_evidence_acquisition_pack.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_validation_calibration_evidence_gaps.py`
- `tests/test_physical_credibility_evidence_requirements.py`

Deliverables:

- A triage report with separate candidate/defer classifications for field-supported release-zone provenance, block-population evidence, and source-frequency records.
- Explicit first-missing-input fields for each category, preserving the distinction from conditional scenario weights.
- Tests proving conditional sampling weights are not reported as source-frequency evidence and fixture-backed provenance is not promoted to field-supported evidence.

Definition of done:

- The physical-evidence roadmap has concrete next acquisition or deferral actions for release-zone, block-population, and source-frequency evidence without changing the scientific claim level.

Boundaries: Acquisition triage only; no calibration, no parameter fitting, no source-frequency model, no annual-frequency product, no physical-probability claim, no risk/exposure semantics, and no operational claim.

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
