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

### TB-496: Regenerate Extreme-Layer Support Fixtures

Goal: Exercise the new extreme-layer support-count metadata on freshly generated local hazard layers instead of only historical manifests.

Capability gap reduced: Makes the support/nodata mitigation testable on current outputs and usable for future layer comparisons.

Why this outranks alternatives: TB-486 added support metadata, but historical smoke output cannot prove the regenerated support layers behave as intended.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/summarize_extreme_layer_sensitivity_smoke.py`
- `tests/test_hazard_layers.py`
- `tests/test_extreme_layer_sensitivity_smoke.py`

Deliverables:

- Regenerate or fixture-generate a small hazard-layer output that includes `max_kinetic_energy_sample_count` and `max_jump_height_sample_count`.
- Update focused tests so extreme-layer comparisons use support counts to distinguish unsupported cells from true value differences.

Definition of done:

- Focused hazard-layer and extreme-layer smoke tests pass, and the regenerated output proves support metadata is present and consumed.

Boundaries: Local fixture/regeneration only; no layer value tuning, no hazard-meaning change, no operational claim, and no Balfrin dependency.

### TB-497: Reduce Eight-Zone Manifest Pressure Locally

Goal: Reduce the remaining local eight-zone manifest-size blocker in the multi-zone scaling ladder.

Capability gap reduced: Advances the local scale frontier beyond the current manifest-pressure limit without live cluster access.

Why this outranks alternatives: TB-488 moved the first blocked rung to eight zones; shrinking that blocker directly improves local scalability.

Inspect first:

- `scripts/summarize_multi_zone_scaling_ladder.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- Profile or inspect the eight-zone manifest payload and remove one redundant field family or long path family using existing manifest structures.
- Re-run the local ladder before/after and record whether the eight-zone rung improves or clears.

Definition of done:

- Focused multi-zone tests pass, before/after local ladder metrics are recorded in scratch output, and manifest size is measurably reduced without adding another report surface.

Boundaries: Local manifest/output simplification only; no distributed execution, no Balfrin submission, no Swiss-wide claim, and no operational claim.

### TB-498: Optimize The Next Local Reducer Hotspot

Goal: Profile the current local hazard/reducer path after the CSV writer optimization and remove the next measurable local hotspot.

Capability gap reduced: Improves local iteration speed for scientific and scaling tasks.

Why this outranks alternatives: Local tasks are now bottlenecked by repeated hazard generation and reducer materialization; measurable runtime reductions compound.

Inspect first:

- `scripts/hazard_accumulation_benchmark.py`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_accumulation_benchmark.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Run the existing benchmark/profile locally, identify the next nontrivial hotspot, and implement one scoped optimization.
- Preserve deterministic output signatures and record before/after benchmark metrics.

Definition of done:

- Focused benchmark/hazard tests pass, before/after metrics show a measurable improvement or a clearly bounded no-op, and no output semantics change.

Boundaries: Local performance only; no physics changes, no output contract break, no new benchmark framework, and no Balfrin dependency.

### TB-499: Add A Second Candidate Local Comparison

Goal: Run one more local comparison using a different reviewed or stable candidate shape to see whether the degraded runout is candidate-specific.

Capability gap reduced: Separates one bad candidate from a broader candidate-generation failure mode.

Why this outranks alternatives: A single degraded candidate run is not enough to decide whether the candidate workflow is scientifically salvageable.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `validation/pilot_runs/tschamut_candidate_adjacent_prau_mulins_local_comparison_v1.yaml`
- `tests/test_plan_terrain_release_zone_candidates.py`

Deliverables:

- Use existing candidate generation/review/freezer paths to select one alternative local candidate and run a bounded local validation comparison.
- Record the comparison beside existing pilot-run records with the same metrics schema.

Definition of done:

- The local comparison completes or fails closed with a concrete blocker, focused checks pass, and the result classifies whether the alternative improves, degrades, or remains inconclusive versus observed-release baselines.

Boundaries: Local comparison only; no tuning, no field validation claim, no candidate acceptance upgrade, no operational claim, and no Balfrin dependency.

### TB-500: Tighten Real-Terrain Rust Regression Coverage

Goal: Add one more Rust-level real-terrain invariant that catches nonphysical behavior on committed real DEM fixtures.

Capability gap reduced: Improves core simulation confidence on real terrain without relying on external runs.

Why this outranks alternatives: Scientific progress depends on core real-terrain behavior staying finite, bounded, and reproducible as Python workflows evolve.

Inspect first:

- `tests/terrain_edge_cases.rs`
- `validation/cases/chant_sura_contact.yaml`
- `validation/cases/tschamut_basic.yaml`
- `src/simulation.rs`

Deliverables:

- Add one focused Rust regression for a committed real-terrain case covering finite motion, bounded energy/jump behavior, or deterministic replay.
- Keep the test runtime small enough for local and CI execution.

Definition of done:

- The focused Rust test and relevant terrain edge-case test target pass locally.

Boundaries: Regression only; no Rust physics tuning unless required to fix a demonstrated bug, no new data fixture, no operational claim, and no Balfrin dependency.

### TB-501: Consolidate Hazard Manifest Output Helpers

Goal: Reduce duplicated hazard-output manifest bookkeeping in the hazard layer builder and manifest helper path.

Capability gap reduced: Makes output-profile and scale-pressure work less brittle as more output families are added.

Why this outranks alternatives: Recent support-count and manifest-pressure work touched multiple output metadata surfaces, increasing drift risk.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_output_manifests.py`
- `tests/test_hazard_layers.py`
- `tests/test_hazard_output_profile.py`

Deliverables:

- Move one duplicated output-entry or file-accounting pattern into an existing helper and update callers.
- Preserve manifest JSON shape consumed by existing tests.

Definition of done:

- Focused hazard manifest/output-profile tests pass and the diff removes duplicated manifest construction rather than adding a wrapper layer.

Boundaries: Internal simplification only; no output semantics change, no new script, no operational claim, and no Balfrin dependency.

### TB-502: Make Candidate Review CSV Round-Trip Tested

Goal: Add a focused round-trip test for candidate review CSV fields used by review-apply and scenario freezing.

Capability gap reduced: Prevents review CSV drift from breaking downstream candidate freezing or human review loops.

Why this outranks alternatives: TB-492 consolidated artifact paths, but review-row content still needs protection as candidate workflows grow.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_candidate_source_zone_freezer.py`

Deliverables:

- Add a test that writes a candidate review CSV, reloads or compares it through existing review/freezer inputs, and verifies key fields survive safely.
- Reuse existing fixtures and helpers.

Definition of done:

- Focused candidate review/freezer tests pass and at least one downstream-critical CSV field set is covered.

Boundaries: Test/serialization hardening only; no new review workflow, no status vocabulary change, no source-zone semantics change, and no Balfrin dependency.

### TB-503: Improve Local QGIS Package Inspectability

Goal: Make one existing local hazard/QGIS package easier to inspect by reducing redundant files or adding a small deterministic index within the existing package.

Capability gap reduced: Speeds human review of local hazard outputs without growing the repo surface.

Why this outranks alternatives: Local science work benefits from fast map/package inspection, but clutter and missing indices slow review.

Inspect first:

- `scripts/generate_aoi_map_qa_review.py`
- `tests/test_aoi_map_qa_review.py`
- `docs/tschamut_public_pilot_gis_package_review.md`
- `scripts/build_hazard_layers.py`

Deliverables:

- Tighten one existing QGIS/map QA output so the primary raster/vector artifacts are discoverable without opening multiple manifests.
- Preserve existing package contents and tests unless a redundant generated file can be removed.

Definition of done:

- Focused map QA/hazard package tests pass and local package inspectability improves through an existing artifact, not a new dashboard.

Boundaries: Local package ergonomics only; no new GIS product claim, no operational claim, no new external dependency, and no Balfrin dependency.

### TB-504: Add Local Calibration-Failure Replay

Goal: Turn one known calibration or validation failure mode into a small deterministic local replay test.

Capability gap reduced: Keeps scientific failure modes reproducible and prevents accidental masking by future workflow changes.

Why this outranks alternatives: The repo has explicit calibration separation and failure diagnostics; one replayable failure is more valuable than another status note.

Inspect first:

- `scripts/check_calibration_separation_preflight.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `tests/test_calibration_separation_preflight.py`
- `tests/test_calibration_failure_diagnostics.py`

Deliverables:

- Add or extend a focused test that reproduces one calibration/validation failure classification from existing fixtures or local synthetic data.
- Ensure the failure remains separated from model tuning or acceptance.

Definition of done:

- Focused calibration/failure-diagnostic tests pass and the replayed failure names the concrete missing evidence or invalid coupling.

Boundaries: Diagnostic replay only; no calibration, no parameter tuning, no acceptance upgrade, no operational claim, and no Balfrin dependency.

### TB-505: Reduce Ignored Result Root Noise Further

Goal: Remove or guard one additional stale ignored result family that is not unique scientific evidence.

Capability gap reduced: Keeps local result roots inspectable as more measured outputs are produced.

Why this outranks alternatives: TB-493 removed copy-suffix clutter; other stale generated families still make local state noisy and harder to audit.

Inspect first:

- `.gitignore`
- `scripts/check_repo_consistency.py`
- `tests/test_repo_consistency_claim_hygiene.py`
- `tests/test_bounded_validation_output_profile.py`

Deliverables:

- Identify one stale ignored generated-result family and either clean it with a narrow local rule or add a consistency guard that prevents reaccumulation.
- Do not delete unique observed evidence, tracked fixtures, or current benchmark roots.

Definition of done:

- Relevant repo-consistency tests pass, the local ignored clutter count for that family is reduced or guarded, and no tracked files are removed.

Boundaries: Repository hygiene only; no scientific data deletion, no workflow claim change, no new admin script, and no Balfrin dependency.

### TB-506: Strengthen Output-Profile Policy Reuse

Goal: Consolidate one duplicated output-profile policy decision across command-plan, AOI preview, and hazard rebuild checks.

Capability gap reduced: Prevents local-vs-CI drift in scalable output defaults and blocked heavy-debug behavior.

Why this outranks alternatives: Output-profile drift has already caused CI/local mismatch risk, and scale tasks depend on consistent reduced-output assumptions.

Inspect first:

- `scripts/lib/output_profile_policy.py`
- `scripts/check_hazard_output_profile.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `tests/test_hazard_output_profile.py`

Deliverables:

- Move one repeated output-profile classification or blocked-default branch into the existing policy helper and update callers.
- Preserve existing command-line JSON fields.

Definition of done:

- Focused output-profile tests pass and the diff reduces duplicated policy logic.

Boundaries: Policy reuse only; no default-output change unless tests prove compatibility, no scale-up authorization, no operational claim, and no Balfrin dependency.

### TB-507: Add Scenario Storage Batch-Cap Regression

Goal: Pin the compact candidate-batch storage cap with a focused regression that catches future manifest-size drift.

Capability gap reduced: Keeps scenario storage growth bounded while candidate pools increase.

Why this outranks alternatives: The next local and Balfrin-adjacent steps depend on compact scenario packages not regressing in size or file count.

Inspect first:

- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `tests/test_scenario_storage_output_tier_pressure.py`
- `tests/test_candidate_source_zone_scenario_stress.py`

Deliverables:

- Add an assertion or focused measurement that fails when the recommended compact batch cap grows past the current measured envelope without an explicit update.
- Keep the test fixture-backed and deterministic.

Definition of done:

- Focused storage/candidate scenario tests pass and batch-cap/file-count/manifest-byte drift is guarded.

Boundaries: Regression guard only; no new storage report, no live execution, no output claim upgrade, and no Balfrin dependency.

### TB-508: Simplify Agent Task Context For Local-Only Work

Goal: Make the existing task-context helper surface local-only tasks cleanly when Balfrin access is unavailable.

Capability gap reduced: Reduces orchestration friction by separating executable local work from Balfrin-required work without changing task order semantics.

Why this outranks alternatives: The current active queue mixes Balfrin-required and local-only tasks, and no-Balfrin sessions need a cleaner way to select eligible tasks.

Inspect first:

- `scripts/print_agent_task_context.py`
- `docs/orchestration_strategy.md`
- `tests/test_repo_consistency_claim_hygiene.py`
- `docs/task_backlog.md`

Deliverables:

- Extend the existing task-context helper or documentation path so a worker can list or select non-Balfrin active tasks without adding a new tool.
- Add focused coverage if the helper behavior changes.

Definition of done:

- Focused tests or helper smoke checks pass, and no-Balfrin task selection is clearer while preserving the existing backlog schema.

Boundaries: Orchestration helper simplification only; no new admin script, no task-status vocabulary change in headings, no Balfrin access attempt, and no execution claim.

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
