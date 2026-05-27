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

### TB-680: Run The Next Bounded Hazard-Throughput Scale-Up On Balfrin

Goal: Move beyond the 12-zone TB-669 hazard-throughput support point with a real measured Balfrin run.

Capability gap reduced: Hazard-throughput scaling evidence between the current bounded 12-zone result and Swiss-scale planning.

Why this outranks alternatives: The 100-zone evidence is diagnostic-only; the next scale proof must exercise the hazard-throughput path itself while Balfrin is empty.

Inspect first:

- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `archive/task_reports/balfrin_12_zone_hazard_throughput_probe_tb669.md`
- `docs/balfrin_scale_demonstration_management_package.md`

Deliverables:

- A submitted and monitored Balfrin `postproc` hazard-throughput run above `12` release zones, using `$SCRATCH`, summary-only/replay-critical output, and preserved metrics.

Definition of done:

- The job reaches a terminal scheduler state, runtime/memory/file/byte metrics are collected, focused scale-readiness tests pass, and the result is classified as measured or failed with a concrete blocker.

Scope: No Swiss-wide, distributed, physical-probability, operational, risk, exposure, vulnerability, or non-`postproc` claim changes.

### TB-681: Repeat The Larger Hazard-Throughput Run For Variability

Goal: Repeat the TB-680 run shape to measure variability and distinguish one-off scheduler noise from stable throughput behavior.

Capability gap reduced: Repeatability evidence for larger hazard-throughput execution on Balfrin.

Why this outranks alternatives: A single larger run improves scale evidence, but repeatability is needed before using it for planning envelopes.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A second Balfrin run with the same release-zone/output profile as TB-680 and a measured comparison of runtime, memory, file count, byte count, and replay-critical artifact coverage.

Definition of done:

- Both runs are represented in the scale surface or a focused metrics artifact, focused tests pass, and the comparison states whether variability is acceptable for the next scale step.

Scope: Keep run roots isolated under `$SCRATCH`; do not overwrite TB-680 artifacts.

### TB-682: Measure Hazard Reducer And Output Pressure At The Largest Safe Single-Node Size

Goal: Find the largest safe single-node hazard-output footprint that still stays below the six-hour Balfrin limit.

Capability gap reduced: Unknown reducer/output pressure for hazard-throughput workloads beyond the TB-669 profile.

Why this outranks alternatives: Swiss-scale feasibility depends on hazard output and replay costs, not only diagnostic reducer pressure.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `docs/hazard_output_profile_contract.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A measured larger hazard-output run or failed-closed pre-submit package with projected and observed output files, bytes, manifest size, reducer time, and replay-critical coverage.

Definition of done:

- The largest attempted size has a concrete measured or blocked status, focused hazard-output tests pass, and the next safe size is explicit.

Scope: Prefer summary-only/rebuildable outputs; do not enable full grid CSV or full conditional-curve fanout.

### TB-683: Exercise Concurrent Hazard-Throughput Jobs On Balfrin

Goal: Use the empty `postproc` partition to test whether multiple bounded hazard-throughput jobs can run concurrently without run-root contention.

Capability gap reduced: Single-job evidence does not prove isolated concurrent throughput or scheduler behavior.

Why this outranks alternatives: Swiss-scale feasibility will require many independent chunks even before distributed execution is promoted.

Inspect first:

- `archive/task_reports/balfrin_concurrent_postproc_diagnostics_tb671.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_skills.md`

Deliverables:

- Two or more concurrent hazard-throughput jobs with distinct `$SCRATCH` roots, collected scheduler states, per-job metrics, and a contention/no-contention result.

Definition of done:

- All jobs are terminal, run-root isolation is verified, focused tests pass, and aggregate runtime/output metrics are recorded.

Scope: Keep the total plan under the six-hour standing clearance; stop if scheduler behavior indicates shared-filesystem stress.

### TB-684: Prove Replay And Recovery For The Largest Hazard Run

Goal: Demonstrate that the largest recent hazard-throughput run can be copied, inspected, and summarized without rerunning simulation.

Capability gap reduced: Restartability and reproducibility for larger hazard outputs.

Why this outranks alternatives: A scale demonstration is not credible if measured run roots cannot be recovered and re-summarized.

Inspect first:

- `scripts/summarize_balfrin_restartability_recovery.py`
- `archive/task_reports/balfrin_larger_run_root_recovery_tb672.md`
- `docs/balfrin_restartability_recovery_report.md`

Deliverables:

- A recovery copy under `$SCRATCH`, checksum or manifest comparison, regenerated metrics, and a statement whether replay-critical artifacts are sufficient.

Definition of done:

- Recovery succeeds or fails with a concrete missing artifact, focused restartability tests pass, and the largest recovered run is named by job id and run root.

Scope: Use `$SCRATCH` for large copies and clean up ephemeral helper files.

### TB-685: Build A National Public-Geodata Inventory Delta

Goal: Turn the Swiss-wide data blocker into a concrete list of present and missing national DEM/context inputs.

Capability gap reduced: `national_public_geodata_inventory` remains a first data blocker for Swiss-scale execution.

Why this outranks alternatives: Compute scaling is less useful if the national payload inventory is unknown.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `archive/task_reports/swiss_national_tiling_inventory_tb607.json`
- `archive/task_reports/swiss_national_tile_chunk_mapping_tb608.json`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A measured inventory delta for swissALTI3D, SWISSIMAGE, swissTLM3D, swissSURFACE3D, and swissBUILDINGS3D that names present caches, missing products, estimated bytes, and first acquisition action.

Definition of done:

- The inventory delta is generated from local or Balfrin-visible filesystem state, focused tests pass, and the next acquisition/staging command is executable or explicitly blocked.

Scope: Do not download or commit large raw swisstopo products unless an existing helper already stages them into ignored data roots.

### TB-686: Stage The Next Chant Sura Public Context Product

Goal: Reduce the second-site blocker by staging one real missing Chant Sura context product into the existing public-geodata cache.

Capability gap reduced: Second-site public context readiness and multi-site scientific validation preparation.

Why this outranks alternatives: Accepted validation needs a second real site; Chant Sura currently blocks first on missing context.

Inspect first:

- `scripts/stage_public_geodata_cache.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/chant_sura_fluelapass_public_context_acquisition_package.yaml`
- `archive/task_reports/chant_sura_prepared_pilot_attempt_tb675.md`

Deliverables:

- One newly staged real Chant Sura context product, an updated cache manifest/preflight result, and the next remaining missing context product.

Definition of done:

- The preflight distinguishes the staged product as real, focused tests pass, and no fixture-backed product is promoted as real.

Scope: Keep large staged data in ignored data roots; commit only manifests or small provenance records.

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
