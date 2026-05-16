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
later prompts.

## Active Tasks

_Active TB tasks remain below._

### TB-108: Audit Post-Balfrin Output Tier Sufficiency

Goal: Determine whether the measured `rebuildable_reduced_output` tier is sufficient for the Balfrin demo and future bounded runs.

Capability gap reduced: Scalable execution realism and artifact sufficiency.

Why this outranks alternatives: Output pressure is the dominant known bottleneck, and Balfrin evidence should decide whether current output tiers are enough.

Inspect first:

- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `docs/hazard_output_profile_contract.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/tschamut_public_bounded_validation_output_profile.md`

Deliverables:

- A post-run output-tier audit that reports rebuildability, required family counts, bytes, file counts, curve availability, and omitted-output implications.
- Tests for sufficient, insufficient, and missing-measured-output states.

Definition of done:

- Output-tier sufficiency is classified with measured or blocked evidence, focused checks pass, and TB-108 is removed from this backlog.

Boundaries: Do not add new output modes unless measured evidence proves the current tier is insufficient; do not call `summary_only` rebuildable.

### TB-109: Check Balfrin GIS/COG Demonstration Parity

Goal: Verify that the Balfrin demonstration GIS package is usable, COG-ready where expected, and explicit about any layer-scope delta.

Capability gap reduced: Demonstration-grade GIS/product usability.

Why this outranks alternatives: Management-facing demos need visual and package coherence, but this should stay machine-auditable rather than manual polish.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `docs/pilot_gis_package.md`
- `docs/balfrin_post_run_interpretation_gate.md`

Deliverables:

- A GIS/COG parity report for the Balfrin demo package covering layer counts, COG metadata, curve linkage, manifest consistency, and scope delta.
- Tests for ready, blocked, and bounded-scope package states.

Definition of done:

- The GIS/COG parity report is emitted from measured or fixture evidence, focused checks pass, and TB-109 is removed from this backlog.

Boundaries: Do not commit generated rasters, do not require manual QGIS QA unless artifacts and QGIS are actually available, and do not make operational GIS claims.

### TB-110: Audit Demo Claim Boundaries

Goal: Machine-check that all Balfrin demo outputs preserve non-operational, non-annual, non-risk, non-exposure, non-vulnerability, and non-physical-probability boundaries.

Capability gap reduced: Scientific integrity and external-facing interpretation safety.

Why this outranks alternatives: As artifacts become demo-ready, accidental overclaiming becomes a higher risk than missing labels.

Inspect first:

- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/check_repo_consistency.py`
- `docs/hazard_map_semantics.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- A claim-boundary audit for demo reports/manifests/docs or an extension to existing consistency checks.
- Tests proving forbidden claim language or flags are rejected in demo-facing artifacts.

Definition of done:

- Demo claim-boundary audit passes on current artifacts, focused negative tests pass, and TB-110 is removed from this backlog.

Boundaries: Do not change claim boundaries to make checks pass; fix or flag artifacts that drift.

### TB-111: Compare Balfrin Results Against Same-Scale Uncertainty

Goal: Explain what the measured Balfrin run changes, confirms, or fails to address relative to existing same-scale uncertainty, closure, stability, and hotspot evidence.

Capability gap reduced: Scientific interpretability.

Why this outranks alternatives: A Balfrin run is scientifically useful only if it is interpreted against the known closure-limiting uncertainty structure.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`

Deliverables:

- A scientific delta report that compares Balfrin measured outputs to same-scale uncertainty, stability zones, closure-gap deltas, and hotspot provenance.
- Tests for measured, inconclusive, and missing Balfrin evidence states.

Definition of done:

- The delta report emits JSON/text, focused tests pass, and TB-111 is removed from this backlog.

Boundaries: Do not reclassify Tschamut closure without new measured evidence, do not tune physics, and do not claim physical validation.

### TB-112: Define Balfrin Operational Failure Taxonomy

Goal: Formalize Balfrin run failure classes and recovery semantics for readiness, scheduler, runtime, partial-output, metrics, GIS/export, and scientific-state failures.

Capability gap reduced: Operational robustness and maintainability.

Why this outranks alternatives: Failure classification prevents infrastructure or orchestration problems from being misread as scientific no-go outcomes.

Inspect first:

- `scripts/check_balfrin_tschamut_readiness.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/balfrin_tschamut_pilot_runbook.md`

Deliverables:

- A machine-readable failure taxonomy or helper output used by the runbook and post-run bundle.
- Tests for representative failure classes and escalation boundaries.

Definition of done:

- Failure classes are actionable and wired to at least one helper or report, focused checks pass, and TB-112 is removed from this backlog.

Boundaries: Do not create labels without command/action mappings, and do not let failure taxonomy change scientific interpretation criteria.

### TB-113: Update Balfrin Runtime And Scaling Frontier

Goal: Use measured Balfrin evidence to refine runtime, storage, file-count, memory, and job-count projections for bounded next-step planning.

Capability gap reduced: Future scalability realism.

Why this outranks alternatives: After the demo run, scaling guidance must be based on measured evidence rather than stale coefficients or wishful extrapolation.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_single_job_execution.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- Updated runtime/storage frontier using measured Balfrin metrics or a blocked report if measured metrics are absent.
- Tests for measured, extrapolated no-go, and missing-evidence paths.

Definition of done:

- The frontier report reflects current measured support and explicit no-go labels, focused checks pass, and TB-113 is removed from this backlog.

Boundaries: Do not authorize Swiss-wide execution or distributed execution; keep projections conservative and labeled.

### TB-114: Prepare Second-Site Real-Context Acquisition Decision

Goal: Decide whether to stage real Chant Sura / Fluelapass public-context products next, or explicitly defer them with measured rationale after the Balfrin demo path is assessed.

Capability gap reduced: Swiss-wide portability realism.

Why this outranks alternatives: Portability cannot advance beyond synthetic boundaries until real public context is either staged or consciously deferred.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A decision pack that lists required real public-context products, expected data volume, cache/output roots, readiness impact, and proceed/defer recommendation.
- Tests for proceed, defer, and blocked decision states if helper code changes.

Definition of done:

- The acquisition decision is explicit and machine-readable or documented with exact commands, focused checks pass, and TB-114 is removed from this backlog.

Boundaries: Do not download real public context unless explicitly authorized, do not run a second-site ensemble, and do not treat synthetic fixtures as evidence.

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

- Focused checks pass and the task is removed from this backlog.

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

Before commit, run the task-specific checks, `git diff --check`, repository
consistency, `scripts/git-hooks/pre-commit`, and the placeholder-artifact scan.

Do not keep completed tasks here. Use `agent_work_log.md` for chronological TB
execution history and `decision_log.md` for durable decisions.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- real Chant Sura public-context product downloads until a specific
  acquisition decision authorizes them;
- physical credibility boundary expansion beyond the existing evidence-gap
  matrix until new field/reference data is identified;
- production COG or QGIS packaging work beyond secondary QA;
- manual GIS/QGIS visual QA unless the local package artifacts and QGIS are
  actually available and the main acceptance evidence is not blocked elsewhere;
- distributed/MPI execution unless the Balfrin single-release-zone pilot shows
  a measured need beyond the current single-job path.
- shared typed evidence-reader refactors unless at least one more executable
  diagnostic exposes duplicated parsing as the implementation bottleneck.
- production Swiss-wide ensembles until the Balfrin single-release-zone pilot
  has measured execution evidence, a complete metrics bundle, and post-run
  interpretation.
- helper consolidation beyond the task-context bootstrap until duplicated
  parsing becomes a demonstrated implementation bottleneck.
