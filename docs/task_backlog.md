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

### TB-404: Regenerate Scenario Tables From The Accepted Adjacent Candidate

Goal: Generate deterministic conditional scenario rows from the frozen adjacent
Prau Mulins candidate and prove the previous zero-row blocker is removed.

Capability gap reduced: The prepared-pilot and Balfrin handoff paths are
currently blocked because the management-AOI scenario pressure report has zero
current scenario rows.

Why this outranks alternatives: Scenario rows are the immediate dependency for
the prepared-pilot compiler and the smallest multi-zone Balfrin handoff.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `scripts/validate_source_scenario_policy.py`
- `tests/test_candidate_source_zone_freezer.py`
- `tests/test_candidate_source_zone_scenario_stress.py`

Deliverables:

- A deterministic ignored-root scenario table and manifest for the adjacent
  candidate.
- Scenario-pressure metrics covering row count, block-family composition,
  table bytes, and first bottleneck.
- A regression showing the non-overlapping candidate path returns a positive
  scenario count while preserving conditional-only weights.

Definition of done:

- The scenario-pressure helper reports a ready or next-stage status for the
  selected adjacent candidate, not `blocked_source_zone_footprint_overlap` or
  `blocked_empty_candidate_set`.

Boundaries: No source-frequency semantics, no annual probability, no physics
changes, no generated heavy artifact commits, and no operational claim.

### TB-405: Compile Prepared-Pilot Package From Adjacent Candidate

Goal: Rebuild the management-AOI prepared-pilot chain using the adjacent
candidate scenario table so downstream handoff commands consume current
non-overlapping inputs.

Capability gap reduced: The AOI front door and prepared-pilot compiler still
surface the source-zone-footprint blocker from the stale candidate/scenario
state.

Why this outranks alternatives: Balfrin submission should not be reattempted
until the local prepared-pilot package proves that the scenario and output-mode
contracts are coherent.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/build_management_aoi_balfrin_handoff.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- A prepared-pilot report that references the adjacent candidate scenario table.
- Updated first-blocker/next-command output from the AOI front door.
- Regression coverage proving the prepared-pilot path no longer reports the
  stale source-zone-footprint blocker when the adjacent candidate bundle is
  supplied.

Definition of done:

- The prepared-pilot compiler reaches the next genuine blocker or ready handoff
  state using the adjacent candidate inputs, and the command shown to users is
  copy-pasteable.

Boundaries: No live Balfrin job, no generated heavy artifact commit, no
operational claim, no source-frequency semantics, and no scale-up
authorization.

### TB-406: Repair Smallest Multi-Zone Balfrin Handoff From Current Inputs

Goal: Regenerate the smallest multi-zone Balfrin handoff from the current
prepared-pilot state and verify submit-contract, output-budget, run-root, and
preservation gates before any live job is attempted.

Capability gap reduced: Previous two-zone/four-zone branches failed closed on
stale wrapper manifests, wrong run roots, output-profile mismatches, or stale
candidate blockers.

Why this outranks alternatives: A measured multi-zone Balfrin hazard run is the
dominant demonstration gap, but it must be attempted only from a current,
gate-clean handoff.

Inspect first:

- `scripts/build_management_aoi_balfrin_handoff.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `tests/test_management_aoi_balfrin_handoff.py`
- `tests/test_execute_management_aoi_balfrin_run.py`

Deliverables:

- A regenerated smallest multi-zone handoff using the adjacent candidate path.
- Machine-readable gate results for submit contract, writable run root, reduced
  output profile, output budget, preservation plan, and authorization record.
- A no-submit mode that names any remaining first blocker precisely.

Definition of done:

- The handoff is either `ready_for_live_postproc_submission` or fails closed
  with one current actionable blocker; no stale source-zone-footprint, wrapper
  manifest, or unwritable-root blocker remains.

Boundaries: No `sbatch` unless all repository gates pass, no non-postproc
partition, no distributed execution, no scale-up claim, and no operational
claim.

### TB-407: Execute Smallest Measured Multi-Zone Balfrin Probe

Goal: If TB-406 reports a clean handoff, run the smallest bounded multi-zone
Balfrin `postproc` hazard probe and preserve measured runtime/output evidence.

Capability gap reduced: The repository still lacks measured multi-zone Balfrin
hazard execution evidence.

Why this outranks alternatives: Management's feasibility question depends more
on one honest measured multi-zone run than on additional projection-only
reports.

Inspect first:

- `docs/orchestration_strategy.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/execute_management_aoi_balfrin_run.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_execute_management_aoi_balfrin_run.py`

Deliverables:

- A GPT-5.5-routed live Balfrin `postproc` run if all gates pass.
- Job id, run root, exit status, elapsed time, peak memory, validation/hazard
  output file counts and bytes, and preservation metadata.
- A failed-closed record if any live gate blocks before `sbatch`.

Definition of done:

- Either a measured multi-zone Balfrin run is preserved and locally summarized,
  or the first pre-submit blocker is current, actionable, and not a stale
  artifact of earlier handoff state.

Boundaries: Standing Balfrin clearance applies only to GPT-5.5 workers on
`postproc`; no non-postproc partition, no distributed execution, no scale-up
authorization, no operational claim, and no physical-probability claim.

### TB-408: Integrate Multi-Zone Balfrin Evidence Into Scale Surfaces

Goal: Thread the TB-407 measured or failed-closed multi-zone outcome into the
scale-readiness matrix, maturity snapshot, management package, and next-action
ranking without overclaiming.

Capability gap reduced: Balfrin scale evidence remains fragmented unless live
run outcomes are integrated into the canonical status surfaces.

Why this outranks alternatives: After any live attempt, stale dashboards are
more dangerous than missing dashboards because they can mislead the next
orchestrator or management review.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `docs/current_maturity_snapshot.md`
- `docs/swiss_scale_feasibility_projection.md`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Updated scale-readiness classification for the two-zone/adjacent-candidate
  branch.
- Updated next-action ranking based on measured run, failed-closed gate, or
  missing evidence.
- Documentation that separates measured, failed-closed, fixture-backed,
  projection-only, and deferred evidence.

Definition of done:

- The compact task context and scale dashboard identify the correct next action
  after TB-407 and do not promote failed-closed or fixture-backed outcomes as
  measured execution.

Boundaries: No scale-up authorization, no operational claims, no annual
frequency, no risk/exposure/vulnerability semantics, and no invented evidence.

### TB-409: Add Candidate Review Overlays To The AOI Front Door

Goal: Make the AOI workflow front door able to emit map and SWISSIMAGE review
overlays for candidate source zones so users can inspect what the heuristic is
selecting.

Capability gap reduced: Candidate review is currently possible but not
well-integrated into the user-facing AOI workflow.

Why this outranks alternatives: The recent manual review showed that visual
inspection is essential for pragmatic source-zone selection; making it a
front-door action reduces hidden local-state and ad hoc image generation.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/generate_aoi_map_qa_review.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_plan_terrain_release_zone_candidates.py`

Deliverables:

- A bounded AOI front-door command or option that writes candidate-overlay
  images and a small candidate-review manifest.
- Support for topographic-map and orthophoto backgrounds when available, with a
  clear blocked report when backgrounds cannot be fetched.
- Tests that use fixture-backed imagery or mocked fetches rather than live
  network access.

Definition of done:

- A user can run one documented command to produce candidate review overlays and
  understand the first missing input if the overlay cannot be generated.

Boundaries: No mandatory live network access in tests, no operational
release-zone claim, no field validation, no generated image commits, and no
Balfrin submission.

### TB-410: Measure Adjacent-Candidate Stability Against Heuristic Variants

Goal: Test whether the selected Prau Mulins candidate persists under bounded
slope, smoothing, resolution, and AOI-boundary perturbations.

Capability gap reduced: The selected adjacent candidate is currently a visual
review choice; stability evidence is needed before using it as a robust
workflow input.

Why this outranks alternatives: A candidate that disappears under small
heuristic changes is a poor basis for a management-facing multi-zone probe.

Inspect first:

- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `tests/test_balfrin_target_area_candidate_stability.py`
- `tests/test_plan_terrain_release_zone_candidates.py`

Deliverables:

- Persistence metrics for the adjacent candidate under bounded perturbations.
- Stable, sensitive, and rejected classification for the selected component.
- A recommendation for whether the candidate is adequate for a bounded
  engineering probe.

Definition of done:

- The adjacent candidate is classified as stable enough for the next
  engineering step or the workflow fails closed with a replacement-candidate
  recommendation.

Boundaries: No tuning to force stability, no physical validation claim, no
field-supported provenance, no frequency semantics, and no Balfrin execution.

### TB-411: Stress Scenario Cardinality For Candidate Expansion

Goal: Estimate scenario-row, manifest, and output-pressure growth if the
adjacent-candidate path is expanded from one extra candidate to a small
multi-candidate set.

Capability gap reduced: The next scale question is not only whether one
additional candidate runs, but whether candidate-driven scenario growth remains
bounded.

Why this outranks alternatives: Scenario cardinality can become the first
practical bottleneck before trajectory runtime or GIS export does.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_aoi_scenario_preview.py`

Deliverables:

- A 1/2/4/8-candidate scenario-cardinality ladder using deterministic candidate
  rows or fixture-backed equivalents.
- Estimated manifest bytes, scenario-table bytes, and output-pressure labels.
- A hard fail-closed threshold for over-budget candidate expansion.

Definition of done:

- The scenario generator and preview helper report the smallest useful
  candidate expansion that remains within current reduced-output and
  postproc-boundary assumptions.

Boundaries: No large production ensemble, no annual/source-frequency
semantics, no physical-probability claim, no Balfrin submission, and no
operational claim.

### TB-412: Collapse Stale Management-AOI Blocker Surfaces

Goal: Remove or update stale references that still imply the active blocker is
only a zero-candidate 4x4 crop after the adjacent-candidate review path exists.

Capability gap reduced: Stale blocker wording can cause workers to preserve
obsolete failure states instead of using the current candidate/scenario path.

Why this outranks alternatives: This is a small simplification task that
prevents future orchestration loops from re-entering already diagnosed blocked
branches.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/script_inventory.md`
- `scripts/print_agent_task_context.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `tests/test_agent_task_context.py`

Deliverables:

- Updated compact status wording that names the current adjacent-candidate
  unblock path.
- Removal or deprecation of stale no-op blocker branches where they duplicate
  newer candidate-state reports.
- Tests ensuring the compact context points to the current first executable
  task rather than old TB-384/TB-393 state.

Definition of done:

- Worker-facing context and scale surfaces agree on the current first unblock
  action and do not recommend stale source-zone-overlap repairs after TB-402
  through TB-405 land.

Boundaries: No new gate/report unless it replaces stale wording, no scientific
claim upgrade, no Balfrin execution, and no broad documentation rewrite.

### TB-413: Reassess Swiss-Scale Feasibility After Adjacent-Candidate Probe

Goal: Update the Swiss-scale feasibility projection using the newest
candidate/scenario/Balfrin evidence from the adjacent-candidate path.

Capability gap reduced: Management needs a feasibility projection tied to
current measured evidence rather than stale single-zone or failed-closed
branches.

Why this outranks alternatives: Once the adjacent-candidate branch either runs
or fails closed, the projection should immediately say what bottleneck remains:
source-zone automation, scenario cardinality, hazard throughput, reducer
pressure, GIS packaging, or Balfrin access.

Inspect first:

- `docs/swiss_scale_feasibility_projection.md`
- `scripts/estimate_large_scale_execution.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/current_maturity_snapshot.md`
- `tests/test_large_scale_execution_probe.py`

Deliverables:

- Updated feasibility categories for 10-zone, 100-zone, regional, and
  Swiss-wide planning cases.
- Explicit bottleneck ranking after the adjacent-candidate branch.
- Management-facing summary that distinguishes measured, projection-only, and
  out-of-reach tiers.

Definition of done:

- The projection states whether the next evidence supports a larger bounded
  probe, an optimization task, or continued deferral, with no unsupported
  scale-up claim.

Boundaries: Projection-only unless using already measured evidence; no
Swiss-wide run, no distributed execution, no operational claim, no annual
frequency, and no risk/exposure/vulnerability semantics.

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
