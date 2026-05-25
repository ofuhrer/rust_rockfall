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

### TB-509: Clear The Eight-Zone Local Scaling Blocker

Goal: Move the local multi-zone scaling ladder past the eight-zone blocker rather than only reducing its manifest pressure.

Capability gap reduced: Advances the local scalability frontier to a larger measured rung without Balfrin access.

Why this outranks alternatives: TB-497 reduced the eight-zone manifest bundle but left the first blocked rung unchanged, so the next scalability task should clear or precisely reclassify that blocker.

Inspect first:

- `scripts/summarize_multi_zone_scaling_ladder.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_multi_zone_reducer_pressure.py`

Deliverables:

- Identify the remaining eight-zone blocker after compact merge manifests and remove one real pressure source or tighten an over-conservative classifier using measured evidence.
- Re-run before/after local ladder metrics and record whether the first blocked rung moves beyond eight zones.

Definition of done:

- Focused multi-zone tests pass, before/after ladder output shows eight-zone status improved or a rigorously justified no-clear result, and no new report surface is added.

Boundaries: Local fixture-backed scaling only; no Balfrin submission, no distributed execution, no Swiss-wide claim, and no operational claim.

### TB-510: Run Candidate Geometry Ablation Locally

Goal: Ablate candidate release placement locally to separate source offset from local stopping behavior in the Tschamut candidate failure.

Capability gap reduced: Turns the TB-494 failure classification into a direct geometry experiment instead of an inferred explanation.

Why this outranks alternatives: The current candidate diagnosis says source placement and early stopping are entangled; a small ablation can decide which effect dominates next.

Inspect first:

- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `validation/pilot_runs/tschamut_candidate_adjacent_prau_mulins_local_comparison_v1.yaml`
- `tests/test_tschamut_closure_gap_deltas.py`

Deliverables:

- Reuse existing local comparison inputs to run or fixture-replay one source-aligned and one candidate-aligned comparison variant.
- Record a measured or fail-closed local result that names whether source offset, terrain/contact stopping, or both dominate.

Definition of done:

- Focused closure/candidate tests pass, the local ablation runs or fails closed with the smallest unblock action, and no candidate acceptance or tuning claim is added.

Boundaries: Local ablation only; no physics tuning, no candidate acceptance upgrade, no annual-frequency semantics, no operational claim, and no Balfrin dependency.

### TB-511: Add Real-Terrain Energy Budget Regression

Goal: Add a focused real-terrain regression that checks energy and speed remain finite and bounded over a committed terrain case.

Capability gap reduced: Strengthens the scientific core by catching nonphysical trajectory behavior before workflow-level tests mask it.

Why this outranks alternatives: Candidate and scale work depend on stable core physics, and one real-terrain invariant can guard many downstream surfaces.

Inspect first:

- `src/simulation.rs`
- `tests/terrain_edge_cases.rs`
- `validation/cases/tschamut_basic.yaml`
- `validation/cases/chant_sura_contact.yaml`

Deliverables:

- Add or tighten one Rust test that runs a small committed real-terrain case and asserts finite positions, speeds, and a bounded energy/jump envelope.
- Keep runtime suitable for local and CI execution.

Definition of done:

- Focused Rust tests pass locally and the regression would fail on NaN, runaway energy, or nondeterministic replay.

Boundaries: Regression only; no physics tuning unless a demonstrated bug requires a minimal fix, no new data fixture, no operational claim, and no Balfrin dependency.

### TB-512: Optimize Real-Terrain Hazard Build Runtime

Goal: Reduce runtime for one repeated real-terrain hazard build path used by local scientific iteration.

Capability gap reduced: Makes local validation and candidate experiments faster without changing output semantics.

Why this outranks alternatives: The backlog increasingly depends on repeated local hazard builds; runtime improvements compound across scientific and scaling tasks.

Inspect first:

- `scripts/hazard_accumulation_benchmark.py`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_accumulation_benchmark.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Run the existing benchmark/profile, identify the current dominant local hotspot, and implement one scoped optimization with before/after metrics.
- Preserve stable hashes or deterministic output signatures.

Definition of done:

- Focused benchmark/hazard tests pass and before/after metrics show a measurable runtime reduction or a clearly bounded no-op with the next hotspot named.

Boundaries: Local performance only; no output contract break, no physics change, no new benchmark framework, and no Balfrin dependency.

### TB-513: Compare Candidate Footprint Against Terrain Support

Goal: Measure whether reviewed candidate footprints occupy terrain cells with enough support for meaningful local trajectory evaluation.

Capability gap reduced: Prevents candidate comparisons from being interpreted when the source footprint sits on weak terrain/support geometry.

Why this outranks alternatives: The failed candidate comparison may be partly geometric; footprint/support quality should be measured before more candidate runs are trusted.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_candidate_source_zone_freezer.py`

Deliverables:

- Add a local check or regression that compares reviewed candidate bbox/cell centers against terrain-grid support and records support status in an existing candidate/freezer artifact.
- Reuse existing candidate review/freezer paths.

Definition of done:

- Focused candidate tests pass and candidate freeze/review artifacts expose whether sampled release cells are terrain-supported.

Boundaries: Geometry/support measurement only; no candidate acceptance upgrade, no tuning, no new review status vocabulary, and no Balfrin dependency.

### TB-514: Make Same-Scale Closure Rebuildable Locally

Goal: Convert one summary-only same-scale closure input into a locally rebuildable reduced artifact.

Capability gap reduced: Reduces the `summary_only_not_rebuildable` blocker that keeps the Tschamut closure gap from becoming a stronger diagnostic.

Why this outranks alternatives: Closure interpretation remains limited by missing rebuildable evidence; one reduced rebuildable path is more valuable than another summary.

Inspect first:

- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/build_hazard_layers.py`
- `tests/test_bounded_validation_output_profile.py`

Deliverables:

- Use existing reduced-output controls to regenerate or fixture-generate one closure-relevant artifact with enough row/grid data to be locally rebuildable.
- Thread that artifact through the existing closure/output-profile check if applicable.

Definition of done:

- Focused output-profile/closure tests pass and at least one previous summary-only blocker is reduced or explicitly narrowed by executable evidence.

Boundaries: Local rebuildability only; no claim upgrade, no new dashboard, no operational semantics, and no Balfrin dependency.

### TB-515: Reduce Scenario Table Memory Footprint

Goal: Reduce memory or materialization pressure when generating large candidate scenario tables.

Capability gap reduced: Lets local scenario-cardinality experiments scale further before requiring cluster execution.

Why this outranks alternatives: Candidate expansion and storage pressure tasks depend on scenario generation not holding redundant row payloads.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_scenario_storage_output_tier_pressure.py`

Deliverables:

- Profile or inspect the candidate scenario generation path and remove one redundant in-memory or on-disk row family while preserving deterministic output.
- Record before/after row count, file count, byte count, or memory proxy in scratch output.

Definition of done:

- Focused candidate/storage tests pass and before/after evidence shows reduced materialization pressure or a bounded no-op with the next pressure source named.

Boundaries: Local scenario generation only; no probability semantics, no annual-frequency claim, no new storage report, and no Balfrin dependency.

### TB-516: Add Cross-Language Fixture Replay Check

Goal: Verify that a small Python-generated hazard input fixture replays consistently through the Rust simulation path.

Capability gap reduced: Catches drift between Python workflow artifacts and Rust execution assumptions.

Why this outranks alternatives: Local and CI drift has already been a concern; a cross-language replay invariant gives higher confidence than isolated Python or Rust tests.

Inspect first:

- `scripts/build_hazard_layers.py`
- `src/simulation.rs`
- `tests/terrain_edge_cases.rs`
- `tests/test_hazard_layers.py`

Deliverables:

- Add a small fixture-backed test or shared expected-output artifact that validates a Python-generated case remains compatible with Rust trajectory execution.
- Keep the check deterministic and cheap enough for CI.

Definition of done:

- Focused Python/Rust checks pass and the replay would fail on schema drift, coordinate drift, or nondeterministic trajectory output.

Boundaries: Compatibility regression only; no new physics, no new external data, no operational claim, and no Balfrin dependency.

### TB-517: Tighten Output Family Budget Accounting

Goal: Make output-family byte and file accounting consistent between hazard manifests, reducer pressure, and scenario storage pressure.

Capability gap reduced: Prevents scale recommendations from changing because different helpers count the same output families differently.

Why this outranks alternatives: Recent manifest compaction work changed pressure surfaces; consistent accounting is now required before further scale decisions.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/build_hazard_layers.py`
- `tests/test_multi_zone_reducer_pressure.py`
- `tests/test_scenario_storage_output_tier_pressure.py`

Deliverables:

- Consolidate or align one duplicated output-family accounting rule using existing helpers or a shared local function.
- Add focused coverage proving two affected surfaces produce compatible counts for the same fixture.

Definition of done:

- Focused reducer/storage/hazard tests pass and duplicated accounting logic is reduced without changing accepted output semantics.

Boundaries: Internal accounting simplification only; no new report, no threshold loosening without measured justification, no scale-up claim, and no Balfrin dependency.

### TB-518: Build A Minimal Second-Site Real-Terrain Smoke

Goal: Run a minimal committed second-site terrain case locally to test portability beyond Tschamut without requiring private geodata.

Capability gap reduced: Moves the project toward multi-site credibility with executable local evidence rather than placeholder portability notes.

Why this outranks alternatives: Scientific generality needs at least one non-Tschamut smoke path that exercises real terrain and current output contracts.

Inspect first:

- `validation/cases/chant_sura_contact.yaml`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_layers.py`
- `scripts/check_second_site_public_geodata_preflight.py`

Deliverables:

- Run or fixture-generate a minimal second-site hazard output using committed inputs and record deterministic output checks in existing tests or artifacts.
- Fail closed if public inputs are insufficient, with the smallest concrete input gap named.

Definition of done:

- Focused hazard/portability tests pass and the second-site smoke either produces local measured output or a precise blocked input gap.

Boundaries: Local smoke only; no new private data, no operational claim, no public-context claim upgrade unless evidence exists, and no Balfrin dependency.

### TB-519: Improve Candidate Endpoint Comparison Metrics

Goal: Add endpoint-shape metrics that compare simulated deposition clouds to observed deposition beyond centroid and mean runout.

Capability gap reduced: Makes candidate comparison scientifically less brittle by measuring spread, nearest-neighbor structure, and endpoint orientation.

Why this outranks alternatives: Candidate decisions based only on centroid/runout can miss shape failures that matter for local hazard interpretation.

Inspect first:

- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `validation/pilot_runs/tschamut_candidate_adjacent_prau_mulins_local_comparison_v1.yaml`
- `tests/test_tschamut_closure_gap_deltas.py`
- `data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv`

Deliverables:

- Extend the existing local candidate diagnostic with one or two deterministic endpoint-cloud metrics using committed or ignored local evidence.
- Add focused tests with small synthetic point clouds.

Definition of done:

- Focused closure-gap tests pass and the diagnostic can distinguish centroid-only improvement from cloud-shape or spread failure.

Boundaries: Diagnostic metrics only; no tuning, no candidate acceptance upgrade, no operational claim, and no Balfrin dependency.

### TB-520: Add Deterministic Reduced-Output Rebuild Test

Goal: Prove that a reduced-output hazard run can be rebuilt from its retained artifacts without hidden local state.

Capability gap reduced: Reduces workflow reproducibility risk for retained reduced-output artifacts.

Why this outranks alternatives: Output reduction is useful only if retained artifacts are enough to replay or inspect the run deterministically.

Inspect first:

- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/build_hazard_layers.py`
- `tests/test_bounded_validation_output_profile.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Add a fixture-backed rebuild test for one reduced-output profile and verify required retained artifacts are sufficient.
- Keep generated data in temporary or ignored roots.

Definition of done:

- Focused rebuild/output-profile tests pass and the test fails if a required retained artifact is removed or renamed.

Boundaries: Rebuildability regression only; no new output mode, no operational claim, and no remote execution.

### TB-521: Vectorize A Hot Grid Reduction Loop

Goal: Replace one measurable Python per-cell grid reduction hotspot with a faster local implementation while preserving exact outputs.

Capability gap reduced: Improves local hazard layer generation throughput for repeated scientific experiments.

Why this outranks alternatives: Profiling has repeatedly found output/reduction loops as local bottlenecks; a focused exact-output optimization can unlock faster iteration.

Inspect first:

- `scripts/build_hazard_layers.py`
- `scripts/hazard_accumulation_benchmark.py`
- `tests/test_hazard_layers.py`
- `tests/test_hazard_accumulation_benchmark.py`

Deliverables:

- Profile the current grid reduction path, optimize one loop or data movement step, and compare before/after benchmark metrics.
- Preserve deterministic layer signatures and manifest hashes where applicable.

Definition of done:

- Focused hazard/benchmark tests pass and before/after metrics show improvement or identify the next nontrivial hotspot if exact-output optimization is not feasible.

Boundaries: Local performance only; no output semantics change, no new dependency unless already used in repo, no physics change, and no Balfrin dependency.

### TB-522: Consolidate Candidate Diagnostic Point Geometry Helpers

Goal: Reduce duplicated point/centroid/geometry parsing across candidate diagnostics and freezer tests.

Capability gap reduced: Lowers risk of subtle coordinate parsing drift in candidate science tasks.

Why this outranks alternatives: Recent candidate diagnostics and freezer geometry checks both parse LV95 point data; duplicated parsing can create inconsistent scientific conclusions.

Inspect first:

- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `tests/test_tschamut_closure_gap_deltas.py`
- `tests/test_candidate_source_zone_freezer.py`

Deliverables:

- Move one shared point parsing or centroid helper into an existing appropriate helper module or reuse an existing helper without adding a new script.
- Update affected tests to prove candidate diagnostics and freezer geometry interpret the same coordinate fields consistently.

Definition of done:

- Focused candidate/freezer tests pass and duplicated coordinate parsing is reduced.

Boundaries: Internal simplification only; no new coordinate semantics, no source-zone claim change, no tuning, and no Balfrin dependency.

### TB-523: Measure Local End-To-End Candidate Loop Runtime

Goal: Measure the local end-to-end candidate loop from review/freezing through reduced hazard comparison for a tiny fixture.

Capability gap reduced: Gives the project a concrete local iteration-time target for scientific candidate work.

Why this outranks alternatives: Scientific progress depends on how quickly candidate hypotheses can be tested locally; individual helper timings do not show full-loop latency.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/build_hazard_layers.py`
- `tests/test_candidate_source_zone_freezer.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Use existing tiny fixtures to run the local candidate loop end to end or build a fixture-backed timing smoke through existing helpers.
- Record phase timings and identify the largest local bottleneck without adding a new dashboard.

Definition of done:

- Focused candidate/hazard tests pass and the measured loop either completes with phase timings or fails closed with the exact missing fixture/input.

Boundaries: Local timing smoke only; no new workflow contract, no operational claim, no Balfrin dependency, and no candidate acceptance upgrade.

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
