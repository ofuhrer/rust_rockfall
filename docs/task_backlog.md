# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is done, remove it from this file and add a short
entry to `docs/agent_work_log.md`. Record only durable technical decisions in
`docs/decision_log.md`.

Progress rule: prefer runs, measurements, code, data, and simplification over
new process artifacts.

Reports, checks, validators, YAML records, checklists, and evidence packages are
useful only when they directly enable a run, measurement, acquisition,
reproducibility step, or simplification.

Orchestrator rule: work the active tasks in numeric order and keep `main`
usable. Full sequential-loop guidance lives in `docs/orchestration_strategy.md`.

Live Balfrin rule: the user has granted standing clearance for GPT-5.5 workers
to submit and actively monitor jobs on Balfrin's `postproc` partition. Multiple
concurrent `postproc` jobs are allowed, including filling the partition. If a
run plan would keep `postproc` fully busy for more than 6 hours, stop and
rediscuss. Keep run roots on `$SCRATCH` and preserve enough metadata to replay
and compare the result.

## Active Tasks

### TB-687: Execute The First Real Chant Sura Prepared-Pilot Slice

Goal: Run the smallest scientifically useful Chant Sura prepared-pilot slice once required public inputs are present.

Capability gap reduced: Multi-site feasibility and validation evidence beyond Tschamut.

Why this outranks alternatives: Scientific credibility needs a second real terrain/context site, not another Tschamut-only report.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/aoi_user_manual.md`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`

Deliverables:

- A real or explicitly blocked Chant Sura prepared-pilot slice with run root, input provenance, output footprint, and residual/scientific interpretation hooks.

Definition of done:

- The run executes or fails at the first concrete missing input, focused tests pass, and the next input or command is explicit.

Scope: Do not label the result operational or physical-probability evidence unless the validation criteria explicitly support it.

### TB-688: Rework Calibration Candidate Selection Against Holdout Residuals

Goal: Move from a rejected selected calibration candidate to an accepted candidate or a clearer model/data limitation.

Capability gap reduced: Accepted validation/calibration evidence, currently blocked by holdout residual quality.

Why this outranks alternatives: The scale surfaces rank accepted scientific validation as the first blocker for physical and operational claims.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `calibration/experiments/tschamut_v0_3/summary.json`
- `archive/task_reports/calibration_acceptance_review_tb676.md`
- `docs/tschamut_calibration.md`

Deliverables:

- A recalculated calibration review that evaluates available candidates against holdout max/mean residuals and either selects an accepted candidate or records the first physical/model limitation.

Definition of done:

- Focused calibration tests pass, the selected candidate status is explicit, and any failure is tied to a measured residual threshold rather than a missing review.

Scope: Do not tune on holdout labels; preserve calibration/validation separation.

### TB-689: Run A Cross-Site Conditional Validation Smoke

Goal: Test whether the current calibrated or best available parameters transfer to a second site under conditional-use semantics.

Capability gap reduced: Multi-site holdout validation evidence for scientific credibility.

Why this outranks alternatives: A Swiss-scale claim cannot rest on one AOI even if Balfrin scaling looks good.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/public_benchmark_framework.md`
- `docs/validation_plan.md`
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`

Deliverables:

- A conditional validation smoke result for Chant Sura or a concrete blocked input report, including residual metrics comparable to the Tschamut holdout thresholds.

Definition of done:

- Focused validation tests pass, metrics are computed or the first missing observed/input artifact is named, and no operational or annual-frequency claim is introduced.

Scope: Treat this as scientific validation evidence only, not a calibrated operational product.

### TB-690: Promote Physical-Evidence Intake From Design Review To Measured Records

Goal: Replace remaining design-review-only physical-probability blockers with measured or explicitly absent source, release, and block-population records.

Capability gap reduced: Physical-probability evidence readiness.

Why this outranks alternatives: The phase-change matrix ranks physical-probability evidence as the first scientifically useful next action.

Inspect first:

- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/source_frequency_evidence_contract.md`
- `docs/block_release_probability_evidence_contract.md`

Deliverables:

- Measured intake records or fail-closed absence records for release probability and block population, plus refreshed physical-credibility and calibration-gap outputs.

Definition of done:

- Focused physical-credibility tests pass and the first remaining physical-probability blocker moves to a measured data gap rather than a process gap.

Scope: Do not synthesize physical probabilities from placeholders; absence is an acceptable measured result.

### TB-691: Exercise A Minimal Distributed Chunk Submission Smoke On Balfrin

Goal: Prove the mechanics for multiple chunk jobs, shared filesystem roots, leases, and deterministic collection without claiming Swiss-wide execution.

Capability gap reduced: Distributed execution mechanics, currently a first compute blocker for Swiss-scale readiness.

Why this outranks alternatives: The Swiss-wide envelope marks distributed authorization/execution as a compute blocker independent of hazard physics.

Inspect first:

- `archive/task_reports/balfrin_distributed_chunk_dry_run_tb605.md`
- `archive/task_reports/balfrin_national_chunk_execution_smoke_tb673.md`
- `scripts/generate_pilot_command_plan.py`
- `docs/balfrin_skills.md`

Deliverables:

- A minimal live Balfrin chunk submission/collection smoke with at least two chunk jobs, lease/state files, deterministic merge order, and restart-cost metrics.

Definition of done:

- Jobs reach terminal state, merged outputs are deterministic, focused tests pass, and the result is classified as distributed-mechanics evidence only.

Scope: Keep chunk payload small; do not promote to Swiss-wide execution.

### TB-692: Saturate The Empty Postproc Partition With Bounded Work

Goal: Measure how far bounded hazard or chunk jobs can fill `postproc` before queue, memory, I/O, or filesystem limits appear.

Capability gap reduced: Scheduler and throughput evidence for a future larger demonstration.

Why this outranks alternatives: Balfrin is currently exceptionally empty, so this is the right time to capture concurrency and saturation evidence.

Inspect first:

- `docs/balfrin_skills.md`
- `archive/task_reports/balfrin_concurrent_postproc_diagnostics_tb671.md`
- `docs/swiss_scale_feasibility_projection.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

Deliverables:

- A monitored saturation run using bounded jobs, with concurrency, queue latency, runtime, memory, I/O, failure modes, and cleanup/replay notes.

Definition of done:

- The run stays under the six-hour standing clearance, focused checks pass, and the measured limiting factor is explicit.

Scope: Stop before creating uncontrolled filesystem pressure; use `$SCRATCH` and clean ephemeral probes.

### TB-693: Collapse Readiness Surfaces Into One Worker Command

Goal: Reduce duplicated readiness scripts and docs by routing workers through one concise command for scale, science, and operational state.

Capability gap reduced: Procedural drag from multiple overlapping dashboards and decision surfaces.

Why this outranks alternatives: Workers need a fast current-state command before choosing the next run, not a growing set of reports.

Inspect first:

- `scripts/print_agent_task_context.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`

Deliverables:

- One worker-facing command or mode that emits the current next action, measured support points, scientific blockers, and Balfrin run recommendation while preserving existing lower-level helpers for tests.

Definition of done:

- Focused tests pass, the command returns compact JSON/text, and docs/onboarding point workers to the single command.

Scope: Prefer consolidation over adding another standalone report; remove or archive redundant prose if it is no longer referenced.

### TB-694: Prune Or Merge The Next Layer Of Low-Value Docs

Goal: Continue reducing top-level `docs/` so it stays a current interface rather than a document warehouse.

Capability gap reduced: Repository complexity and worker navigation overhead.

Why this outranks alternatives: The first simplification cut removed TB reports, but `docs/` still has many low-reference notes that slow onboarding.

Inspect first:

- `docs/README.md`
- `docs/script_inventory.md`
- `scripts/check_repo_consistency.py`
- `archive/reference_notes/README.md`

Deliverables:

- A second safe pruning pass that archives, merges, or deletes low-value docs and updates references without weakening active safety checks.

Definition of done:

- Focused docs/reference scans pass, default consistency remains fast, top-level `docs/` is smaller, and current worker entry points are clearer.

Scope: Do not remove scientific or execution evidence still consumed by scripts, tests, or current docs.

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
  mainly a report, check, validator, checklist, or package, state the exact run,
  recovery, acquisition, reproducibility, or consolidation action it enables.

Definition of done:

- Focused checks pass, the result is explicit, and the task actually moved
  execution, measurement, acquisition, or simplification forward.

Scope: Keep work focused. If a task changes physics defaults, execution
architecture, partition choice, or public output semantics, record that choice
plainly in the work log.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read the selected task and its `Inspect first` files first. Pull broader
context only when it is needed.

Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.

Keep worker prompts compact. Redirect large JSON, diffs, and logs to `/tmp` and
summarize the important result; finish with the compact structured report schema:
`TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
`PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.

Before commit, run the focused checks, `git diff --check`, and the pre-commit
hook. Add broader consistency checks when the change touches shared contracts or
public docs.

Do not keep completed tasks here. Append completed TB work to the bottom of `docs/agent_work_log.md`
and use `decision_log.md` for durable decisions.
