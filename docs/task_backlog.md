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

_Active TB tasks remain below._

### TB-153: Add Probabilistic Metadata To Reduced Probe Fixture

Goal: Unblock the bounded next-ensemble feasibility path by adding the optional
probabilistic metadata expected by the reduced-output probe fixture.

Capability gap reduced: Current bounded-probe planning fails closed on missing
optional probabilistic metadata rather than evaluating a runnable smallest
useful probe.

Why this outranks alternatives: The next measured Balfrin/scaling decision
depends on a feasibility helper that can classify a candidate probe from
complete reduced-output metadata.

Inspect first:

- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `tests/test_bounded_next_ensemble_feasibility_probe.py`
- `tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- Complete fixture-side `probabilistic_metadata` and `hazard_probability`
  fields for the reduced-output probe path.
- Updated feasibility-helper tests proving the present-metadata path is
  classified separately from missing-metadata blocked states.
- Documentation that the fixture unblocks planning only and does not authorize
  execution by itself.

Definition of done:

- The bounded next-ensemble feasibility helper reports a non-blocked planning
  classification for the complete reduced-output fixture while retaining
  fail-closed behavior for missing metadata fixtures.

Boundaries: No ensemble execution, no annual frequency, no physical-probability
claim, no tuning, and no scale-up authorization.

### TB-154: Recompute Balfrin Frontier With Complete Probe Metadata

Goal: Thread the unblocked bounded-probe feasibility result into the Balfrin
ensemble-frontier and Swiss-wide execution-envelope helpers.

Capability gap reduced: Current scaling recommendations remain conservative
because the bounded next-probe path is recorded as blocked rather than
evaluated.

Why this outranks alternatives: Once the feasibility metadata blocker is
removed, the next highest-value step is to see whether the recommended next
probe remains deferred, becomes an allowed bounded probe, or exposes another
blocker.

Inspect first:

- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `tests/test_balfrin_ensemble_frontier.py`

Deliverables:

- Updated frontier report logic and tests for complete-metadata feasibility.
- Swiss-wide envelope wording/status that reflects the recomputed bounded
  probe recommendation.
- Documentation update in the Balfrin sufficiency or maturity snapshot only if
  the recommendation changes materially.

Definition of done:

- Balfrin frontier and Swiss-wide envelope helpers consume the complete
  bounded-probe feasibility result without falling back to stale
  `blocked_missing_optional_probabilistic_metadata` assumptions.

Boundaries: No new Balfrin run, no large ensemble, no distributed execution,
no operational claim, and no scale-up authorization.

### TB-155: Define Measured Minimal Balfrin Probe Execution Package

Goal: Convert the recomputed bounded-probe recommendation into one executable
Balfrin submission package without launching it automatically.

Capability gap reduced: The repo lacks a measured-next-probe handoff that
connects feasibility, reduced-output mode, SLURM command, expected outputs, and
claim boundaries.

Why this outranks alternatives: A bounded, reviewable submission package is the
safest bridge from planning evidence to a future measured probe.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/plan_balfrin_single_release_zone_case_dry_run.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A deterministic dry-run package with command script, expected run root,
  reduced-output settings, metrics collection command, and stop/resume notes.
- Tests for package content and blocked/unlaunched status.
- Clear operator instructions for launching later without using branches or
  committing generated run artifacts.

Definition of done:

- A worker can generate and inspect the exact Balfrin probe package for the
  smallest recommended next probe, and the package remains explicitly
  unexecuted.

Boundaries: Do not submit a job, do not run an ensemble, do not authorize
distributed execution, and do not claim scale-up readiness.

### TB-156: Add Balfrin Metrics Completeness Remediation Plan

Goal: Turn remaining unavailable or ancillary Balfrin metrics into an explicit
next-run collection contract.

Capability gap reduced: Measured Balfrin evidence still has gaps around memory
and split-output provenance when summaries are unavailable.

Why this outranks alternatives: Future Balfrin runs should capture missing
metrics by design instead of relying on post-hoc reconstruction.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- A machine-readable metrics-remediation section listing missing, unavailable,
  and next-run-required fields.
- Collector or evidence-bundle tests proving missing metrics remain explicit
  rather than silently passing.
- Updated Balfrin documentation describing what the next measured run must
  preserve.

Definition of done:

- The evidence bundle exposes a deterministic next-run metrics collection
  checklist for every unavailable mandatory or high-value ancillary field.

Boundaries: No new run, no synthetic measured metrics, no scale-up claim, and
no operational claim.

### TB-157: Connect AOI Case Skeleton To Generic Scenario Generation

Goal: Ensure the AOI case-skeleton dry run can reference the generic
candidate-source-zone scenario generator instead of relying on Tschamut-only
scenario assumptions.

Capability gap reduced: The site-level AOI handoff is not yet fully composed
from the generic release-zone and scenario-generation surfaces.

Why this outranks alternatives: A future second-site worker needs one coherent
handoff bundle whose scenario table is produced by the portable generator.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_tschamut_block_scenario_tables.py`
- `scripts/plan_release_plan_dry_run.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- AOI dry-run output that names the generic scenario-generation command,
  expected scenario table, manifest path, and blocked execution status.
- Tests proving deterministic skeleton output includes generic scenario
  provenance for a synthetic non-Tschamut candidate.
- Documentation note preserving conditional-only weighting semantics.

Definition of done:

- The AOI case-skeleton bundle can be inspected as a portable release/scenario
  handoff without Tschamut-only scenario identifiers.

Boundaries: No ensemble execution, no second-site hazard build, no
block-population fitting, no annual frequency, and no operational claim.

### TB-158: Produce Chant Sura Real-Context Staging Checklist

Goal: Convert the Chant Sura real-context acquisition decision into a concrete,
product-by-product staging checklist with cache-verifier inputs.

Capability gap reduced: Second-site realism remains deferred because real
public-context staging is not yet operator-ready.

Why this outranks alternatives: Portability cannot progress beyond synthetic
fixtures until a worker can stage and verify real SWISSIMAGE/swissTLM3D/etc.
products with deterministic cache manifests.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/verify_public_geodata_cache.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`

Deliverables:

- A staging checklist or helper output that maps each deferred public-context
  product to cache-manifest fields, expected roots, verifier command, and
  readiness impact.
- Tests for missing, partially staged, and verifier-ready checklist states.
- Documentation that the checklist is not a download or validation claim.

Definition of done:

- A future operator can see exactly which real public-context files and
  metadata must be staged for Chant Sura before any second-site run is
  considered.

Boundaries: No downloads, no synthetic evidence upgrade, no second-site
ensemble, no operational claim, and no physical validation claim.

### TB-159: Map Physical-Credibility Gaps Onto AOI Automation Outputs

Goal: Show which AOI dry-run outputs remain workflow artifacts versus physical
credibility evidence.

Capability gap reduced: The new AOI automation chain could be mistaken for
validation readiness unless its outputs are mapped to the physical-credibility
evidence matrix.

Why this outranks alternatives: As automation improves, claim-boundary drift
becomes a larger risk than missing documentation.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_physical_credibility_evidence_requirements.py`

Deliverables:

- Updated physical-credibility matrix entries for AOI cache verification,
  terrain preprocessing, release-zone candidates, scenario tables, and case
  skeletons.
- Tests proving those artifacts do not satisfy observed runout, calibration,
  block-population, or source-frequency evidence requirements.
- Concise docs update if needed.

Definition of done:

- Physical-credibility helpers explicitly classify every major AOI automation
  output as workflow/provenance evidence, not physical validation evidence.

Boundaries: No calibration, no tuning, no physical-probability claim, no
annual frequency, and no operational claim.

### TB-160: Add Demonstration GIS Scope Review For AOI Handoff

Goal: Extend GIS/COG scope reporting so AOI case-skeleton handoff bundles
declare which GIS products are planned, template-only, or unavailable.

Capability gap reduced: Demonstration GIS scope is clear for Balfrin evidence
but not yet connected to generic AOI handoff bundles.

Why this outranks alternatives: Management-facing demonstrations need clear
visual-product expectations before operators run or stage second-site inputs.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- AOI handoff report fields for planned raster/vector products, COG export
  expectation, blocked/missing inputs, and non-operational GIS boundaries.
- Tests proving GIS scope is deterministic for ready and missing-input
  skeletons.
- Documentation note distinguishing planned GIS products from generated
  hazard-map outputs.

Definition of done:

- AOI case-skeleton reports expose a machine-readable GIS scope summary without
  implying any hazard layers were generated.

Boundaries: No hazard build, no generated raster commit, no operational GIS
claim, no risk/exposure/vulnerability semantics, and no scale-up claim.

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
