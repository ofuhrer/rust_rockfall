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

### TB-162: Verify Target-Area Public-Geodata Readiness

Goal: Check whether the frozen target area has all required public geodata, cache manifests, terrain metadata, and context products staged for execution.

Capability gap reduced: Public-input readiness for the target-area demonstration.

Why this outranks alternatives: A Balfrin run is only meaningful if the input provenance is explicit and missing public geodata is not hidden by synthetic fixtures.

Inspect first:

- `scripts/verify_public_geodata_cache.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Target-area geodata readiness JSON/text report.
- Product-by-product staged/missing/deferred classification.
- Reproduction commands for cache verification and missing-input remediation.

Definition of done:

- The target area is classified as ready for real inputs or blocked with exact missing products and paths.

Boundaries: No downloads unless explicitly already supported by an existing helper, no synthetic evidence upgrade, no ensemble execution, and no operational claim.

### TB-163: Materialize Target-Area AOI Case Handoff

Goal: Emit the ignored case-skeleton, command manifest, expected roots, scenario-generation handoff, and GIS scope summary for the frozen target area.

Capability gap reduced: AOI-to-executable handoff reproducibility.

Why this outranks alternatives: The project needs one target-area handoff bundle before workers can submit, replay, or review a full demonstration path.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_release_plan_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- Ignored target-area handoff bundle or blocked report.
- Case skeleton with scenario-generation and GIS scope sections.
- Focused tests covering the target-area handoff shape.

Definition of done:

- The handoff bundle can be regenerated deterministically and states whether it is runnable or template-only.

Boundaries: No hazard build, no generated raster commit, no second-site ensemble unless explicitly authorized, and no operational GIS claim.

### TB-164: Validate Target-Area Release-Zone Candidate Stability

Goal: Run or extend the deterministic release-zone candidate stability audit for the frozen target area.

Capability gap reduced: Release-zone heuristic uncertainty for the demonstration target.

Why this outranks alternatives: The target run is scientifically weak if the release-zone candidate is not tied to a reproducible stability/sensitivity report.

Inspect first:

- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/prepare_tschamut_public_benchmark.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `docs/swisstopo_data_strategy.md`
- `tests/test_release_zone_heuristic_dry_run.py`

Deliverables:

- Target-area candidate stability summary.
- Stable versus heuristic-sensitive region classification.
- GIS-readable candidate outputs if the existing helper supports them for the staged inputs.

Definition of done:

- The target-area release-zone candidate basis is deterministic and its heuristic sensitivity is explicit.

Boundaries: No tuning, no field validation claim, no operational release-zone claim, and no physical credibility upgrade.

### TB-165: Generate Target-Area Deterministic Scenario Tables

Goal: Generate or block deterministic target-area scenario tables from candidate source-zone metadata and policy inputs.

Capability gap reduced: Handcrafted scenario dependence for the target-area demonstration.

Why this outranks alternatives: A full demonstration needs scenario rows and provenance generated from the same target contract, not manually inferred.

Inspect first:

- `scripts/plan_release_plan_dry_run.py`
- `scripts/generate_tschamut_same_scale_cases.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `tests/test_release_plan_dry_run.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Deterministic scenario table or blocked missing-input report.
- Scenario manifest with source-zone, seed, scenario id, and conditional-weight provenance.
- Regression coverage for target-area or synthetic target-area scenario generation.

Definition of done:

- Scenario generation is reproducible and preserves conditional-only probability semantics.

Boundaries: No block-population fitting, no annual-frequency semantics, no physics changes, and no operational claim.

### TB-166: Build Target-Area Balfrin Submission Package

Goal: Produce an unlaunched Balfrin submission package for the frozen target-area demonstration.

Capability gap reduced: Execution handoff from target contract to Balfrin.

Why this outranks alternatives: Operators need a concrete sbatch script, command plan, expected roots, and metrics collection command before any controlled run.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `tests/test_balfrin_probe_driver.py`

Deliverables:

- Unlaunched submission package under an ignored root.
- Sbatch script, command manifest, expected run root, stop/resume notes, and metrics command.
- Explicit `deferred_pending_authorization` or ready-to-submit status.

Definition of done:

- The package can be generated quickly and inspected without submitting a Balfrin job.

Boundaries: No job submission, no `git push --no-verify`, no scale-up authorization, and no distributed execution.

### TB-167: Execute Authorized Target-Area Balfrin Probe

Goal: If the target-area package is explicitly authorized and runnable, submit one bounded Balfrin probe and record measured execution evidence; otherwise emit a precise blocked report.

Capability gap reduced: Measured target-area Balfrin execution realism.

Why this outranks alternatives: The strongest demonstration evidence is a real measured run; if authorization or inputs are absent, the repo should say exactly why.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_evidence_bundle.py`

Deliverables:

- Measured run id, run root, exit status, runtime, and artifact pointers, or a blocked execution report.
- Updated evidence pointers without committing generated outputs.
- Work-log entry that distinguishes measured execution from blocked/unlaunched status.

Definition of done:

- The target-area probe is either measured and collectable or blocked with the exact unresolved gate.

Boundaries: Execute only if existing repo contract and operator authorization allow it; no large ensemble, no distributed execution, no operational claim, and no scale-up authorization.

### TB-168: Collect Target-Area Balfrin Metrics Completeness

Goal: Collect and classify target-area Balfrin runtime, output, memory, split-output, and remediation metrics from the measured run root.

Capability gap reduced: Demonstration runtime/output evidence completeness.

Why this outranks alternatives: A run without metrics cannot support management or scaling conclusions.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `tests/test_balfrin_probe_driver.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Target-area metrics JSON/text report.
- Mandatory, ancillary, unavailable, and next-run-required metric classification.
- Updated tests or fixtures for the metrics contract.

Definition of done:

- The measured run root has a deterministic metrics completeness report or a blocked missing-run-root report.

Boundaries: No fabricated measured metrics, no new run unless covered by TB-167, no operational claim, and no scale-up authorization.

### TB-169: Build Target-Area Evidence Bundle

Goal: Compose the target-area Balfrin evidence into one deterministic JSON/text bundle with section provenance.

Capability gap reduced: Fragmented demonstration evidence.

Why this outranks alternatives: Management and future workers need one auditable artifact rather than scattered helper outputs.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `docs/current_maturity_snapshot.md`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Target-area evidence bundle.
- Section-level measured, fixture-backed, unavailable, and blocked provenance.
- Text summary suitable for review.

Definition of done:

- One deterministic bundle represents the current target-area demonstration state without overclaiming.

Boundaries: No operational claim, no physical credibility upgrade, no generated output commit, and no annual-frequency semantics.

### TB-170: Produce Target-Area GIS And COG Scope Audit

Goal: Audit the target-area GIS products, COG conversion scope, missing layers, and demonstration usability.

Capability gap reduced: GIS demonstration readiness.

Why this outranks alternatives: GIS output is management-visible, but it must remain bounded and not imply operational hazard products.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/build_hazard_layers.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Target-area GIS/COG audit or blocked missing-products report.
- Explicit full-scope, bounded-scope, or blocked classification.
- Layer parity and missing-layer summary.

Definition of done:

- GIS readiness for the target-area demonstration is machine-readable and visually useful boundaries are explicit.

Boundaries: No operational GIS claim, no QGIS sign-off claim, no generated raster commit, and no risk/exposure/vulnerability semantics.

### TB-171: Summarize Target-Area Spatial Uncertainty And Stability

Goal: Produce uncertainty, stability-zone, persistence, and hotspot summaries for the target-area run or report why they are unavailable.

Capability gap reduced: Scientific interpretability of the target-area demonstration.

Why this outranks alternatives: A Balfrin run is not scientifically convincing unless uncertainty and unstable regions are explicit.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_same_scale_sampling_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `tests/test_spatial_same_scale_uncertainty.py`

Deliverables:

- Target-area spatial uncertainty report or blocked missing-artifacts report.
- Persistent, unstable, support/nodata-sensitive, and magnitude-sensitive region summaries.
- Integration notes for the evidence bundle.

Definition of done:

- Target-area uncertainty is summarized with the same conservative boundary language as Tschamut.

Boundaries: No closure upgrade by assertion, no operational hazard-map claim, and no physical probability claim.

### TB-172: Interpret Target-Area Closure And Scientific Meaning

Goal: Generate a target-area conditional diagnostic interpretation combining execution, uncertainty, GIS, output, and physical-credibility boundaries.

Capability gap reduced: Coherent scientific interpretation for the demonstration.

Why this outranks alternatives: The repo needs one answer to "what did the target-area run mean?" before management review.

Inspect first:

- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Target-area diagnostic interpretation JSON/text report.
- Dominant blockers, satisfied workflow criteria, and claim-boundary summary.
- Explicit comparison to current Tschamut/Balfrin baseline.

Definition of done:

- The target-area interpretation is deterministic, conservative, and sectioned for future demo packaging.

Boundaries: No accepted diagnostic unless criteria are actually met, no operational claim, no physical credibility upgrade, and no annual-frequency semantics.

### TB-173: Demonstrate Target-Area Restartability Or Preserve Blocked Status

Goal: Run or document an interruption/resume proof for the target-area Balfrin package, using measured evidence only when available.

Capability gap reduced: Operational recovery credibility for the target-area demonstration.

Why this outranks alternatives: A full Balfrin demonstration should show recovery behavior or explicitly state why it remains untested.

Inspect first:

- `docs/balfrin_restartability_recovery_report.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `tests/test_balfrin_evidence_bundle.py`

Deliverables:

- Target-area restartability report with measured or blocked provenance.
- Resume timing, chunk reuse/execution counts, and artifact continuity if measured.
- Evidence bundle integration.

Definition of done:

- Restartability is either measured for the target area or explicitly blocked without reusing fixture-backed evidence as measured proof.

Boundaries: No unnecessary rerun, no destructive cancellation of healthy Slurm jobs, no distributed execution, and no operational claim.

### TB-174: Update Target-Area Runtime And Swiss-Wide Scaling Envelope

Goal: Recompute runtime/output and Swiss-wide scaling estimates from the target-area evidence.

Capability gap reduced: Scaling realism after measured target-area execution.

Why this outranks alternatives: Management needs to know what the target-area evidence implies for future larger domains without authorizing scale-up.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `tests/test_swiss_wide_execution_envelope.py`

Deliverables:

- Updated target-area scaling envelope.
- Runtime, output, memory, and uncertainty tradeoff classification.
- Explicit no-go, defer, or allowed-next-probe planning labels.

Definition of done:

- Scaling conclusions are recomputed from current evidence and do not imply Swiss-wide authorization.

Boundaries: No distributed execution, no national-scale run, no scale-up authorization, and no operational claim.

### TB-175: Produce Target-Area Management Demonstration Package

Goal: Assemble a compact management-facing package that explains the target-area Balfrin demonstration, evidence, limits, and next decision.

Capability gap reduced: Demonstration communication and decision readiness.

Why this outranks alternatives: Once evidence exists, management needs a concise artifact that is honest, auditable, and not buried in helper outputs.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `README.md`

Deliverables:

- Compact JSON/text or markdown management package.
- Run status, scientific meaning, GIS preview/scope, scaling implication, and explicit boundaries.
- Recommendation for next authorized step.

Definition of done:

- A reviewer can understand the target-area demonstration state without reading the full repo.

Boundaries: No marketing overclaim, no operational claim, no annual-frequency claim, and no physical credibility upgrade.

### TB-176: Prepare Second-Site Real-Context Acquisition Execution Plan

Goal: Convert the Chant Sura real-context staging checklist into a concrete operator execution plan for acquiring and verifying real public-context products.

Capability gap reduced: Portability realism beyond the target-area demonstration.

Why this outranks alternatives: The next portability bottleneck is real public context, not more synthetic fixture planning.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/verify_public_geodata_cache.py`
- `tests/test_chant_sura_real_context_readiness_gate.py`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- Product-by-product execution checklist with exact roots, expected metadata, verifier commands, and stop conditions.
- Clear stage/defer decision rows based on current evidence.
- No-download fallback report when credentials or local files are absent.

Definition of done:

- An operator can stage real Chant Sura public context without consulting synthetic fixtures as evidence.

Boundaries: No downloads unless explicitly requested and supported, no second-site ensemble, no synthetic evidence upgrade, and no operational claim.

### TB-177: Define Physical Evidence Acquisition Pack For Target Area

Goal: Specify the real observed runout/deposition, release-zone, block-population, and source-frequency evidence needed to move beyond workflow credibility for the target area.

Capability gap reduced: Physical credibility and validation realism.

Why this outranks alternatives: More execution alone will not establish physical credibility; the missing evidence must be concrete and acquirable.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `docs/current_maturity_snapshot.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- Target-area physical evidence acquisition checklist.
- Dataset roles, required geometry/provenance fields, and claim-boundary mapping.
- Blocked status that separates benchmark intake, calibration, and frequency evidence.

Definition of done:

- Physical credibility gaps for the target area are concrete enough for data acquisition without implying validation exists.

Boundaries: No calibration, no tuning, no annual-frequency claim, no risk/exposure/vulnerability workflow, and no operational claim.

### TB-178: Refill Or Close Post-Demonstration Backlog

Goal: After the target-area demonstration sequence, reassess maturity and refill only the next highest-value tasks.

Capability gap reduced: Backlog relevance after new measured or blocked evidence.

Why this outranks alternatives: The sequence above can change priorities substantially; the next queue should be evidence-driven rather than pre-generated too far ahead.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/agent_work_log.md`
- `docs/task_backlog.md`
- `scripts/print_agent_task_context.py`
- `docs/orchestration_strategy.md`

Deliverables:

- Updated maturity snapshot if evidence changed.
- Either a concise new active backlog or a clear backlog-refill-needed state.
- Summary of tasks completed, blocked, deferred, or superseded.

Definition of done:

- The backlog reflects the actual post-demonstration state and does not retain stale completed or impossible tasks.

Boundaries: No implementation of scientific/execution tasks inside the refill itself, no roadmap bloat, and no claim-boundary changes without measured evidence.

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
