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

### TB-307: Target-Area Metrics Completion Postproc Rerun

Goal: Execute the bounded target-area metrics-completion postproc rerun now that standing `postproc` clearance exists, if all current preflight and preservation gates pass.

Capability gap reduced: The target-area Balfrin evidence still needs a clean live branch for peak memory and split validation/hazard output metrics.

Why this outranks alternatives: Metrics completion is still the top ranked Balfrin decision-gate action and directly improves the measured target-area demonstration record.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A GPT-5.5-routed `postproc` submission for the exact target-area metrics-completion rerun package if access, remote hygiene, package readiness, output-budget, and preservation gates pass.
- Preserved metrics for peak memory, split validation/hazard file counts and bytes, run-root paths, scheduler fields, logs, checksums, and preservation status.
- A fail-closed report with one exact blocker if any gate fails before `sbatch`.

Definition of done:

- The target-area metrics-completion branch is either measured and preserved or blocked at one current pre-submit gate with no ambiguous authorization state.

Boundaries: Exact target-area metrics-completion postproc rerun only; standing clearance applies only to `postproc`; no multi-zone run, no retry loop without diagnosis, no physical credibility upgrade, no annual-frequency claim, no risk/exposure/vulnerability claim, and no operational claim.

### TB-308: Target-Area Metrics Evidence Integration

Goal: Propagate the TB-307 target-area metrics outcome through the evidence bundle, closure package, decision gate, scale dashboard, and maturity snapshot.

Capability gap reduced: Balfrin evidence summaries must agree on whether target-area metrics are recovered, newly measured, blocked pre-submit, or still missing.

Why this outranks alternatives: Stale or conflicting metrics labels would mislead the next live-run decision.

Inspect first:

- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/current_maturity_snapshot.md`
- `tests/test_balfrin_evidence_bundle.py`
- `tests/test_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Unified metric-state propagation for `new_metrics_completion_rerun`, `recovered_existing_run_root`, `blocked_pre_submit`, `failed_closed`, and `blocked_missing_metrics`.
- Tests proving peak memory, split output counts/bytes, SLURM fields, run-root hashes, and preservation status are shown consistently when present.
- Updated next-action ranking after the metrics branch is integrated.

Definition of done:

- All authoritative Balfrin decision and evidence surfaces agree on the target-area metrics state and the next recommended measured action.

Boundaries: Evidence integration only; no live Balfrin submission, no new metrics fabrication, no claim upgrade beyond execution-metric completeness, no annual/physical/risk semantics, and no operational claim.

### TB-309: Smallest Two-Zone Balfrin Postproc Probe

Goal: Submit the smallest bounded two-zone Balfrin `postproc` probe under standing clearance once the current access, remote-hygiene, authorization-audit, reducer-budget, output-profile, and preservation gates pass.

Capability gap reduced: The project still lacks measured live Balfrin evidence beyond single-zone/target-area comfort; multi-zone remains blocked/pre-submit only.

Why this outranks alternatives: The compact manifest and output-budget work has made the two-zone package technically ready except for the current dirty remote checkout blocker.

Inspect first:

- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/balfrin_probe_slurm_driver.md`

Deliverables:

- A GPT-5.5-routed `postproc` submission for the exact two-zone package if all gates pass, using the reviewed/authorized audit record as a reproducibility artifact.
- Preserved job id, run root, runtime, memory, reducer timing, output counts/bytes, manifest bytes, sidecar counts, hashes, replay metadata, and run-root output-budget audit.
- A fail-closed pre-submit report if any gate remains blocked.

Definition of done:

- The smallest multi-zone branch is either measured on Balfrin and preserved or blocked at one exact current technical gate.

Boundaries: Exact smallest two-zone postproc probe only; no larger ensemble, no non-postproc partition, no distributed execution, no scale-up claim, no annual-frequency or physical-probability claim, no risk/exposure/vulnerability claim, and no operational claim.

### TB-310: Two-Zone Balfrin Evidence Integration And Scale Decision

Goal: Integrate the TB-309 outcome into reducer-pressure docs, evidence bundles, scale dashboard, Swiss-wide envelope, and the next scale decision without treating it as Swiss-wide proof.

Capability gap reduced: A measured or blocked two-zone branch must update the scaling frontier and determine whether the next action is four-zone review, hazard optimization, or deferral.

Why this outranks alternatives: Multi-zone evidence changes the ordering of every later Balfrin scale task.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/current_maturity_snapshot.md`
- `tests/test_balfrin_scale_readiness_matrix.py`
- `tests/test_swiss_wide_execution_envelope.py`

Deliverables:

- Updated classifiers for `measured_two_zone_balfrin`, `blocked_pre_submit`, `failed_closed`, or `budget_no_go`.
- Scale-dashboard and Swiss-wide envelope updates that keep `scale_up_authorized=false` unless a later task explicitly scopes the next probe.
- A concrete next recommendation: four-zone review package, hazard accumulation optimization, remote cleanup rerun, or no live scale action.

Definition of done:

- The repository's scaling frontier reflects the two-zone result and names the next safe scaling action.

Boundaries: Evidence integration and decision support only; no live Balfrin submission, no larger run, no Swiss-wide claim, no distributed execution, no annual/physical/risk semantics, and no operational claim.

### TB-311: Four-Zone Balfrin Review Package

Goal: Generate a review-only four-zone Balfrin package using the post-TB-309 evidence and current output-budget thresholds.

Capability gap reduced: The project needs a measured path from two-zone evidence to the next bounded scale step without jumping directly to Swiss-wide or distributed execution.

Why this outranks alternatives: A four-zone review package is the smallest logical follow-on once two-zone evidence is integrated and local 4-zone rungs are fixture-ready.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/summarize_multi_zone_scaling_ladder.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- A four-zone review-only package with compact manifests, reduced-output defaults, objective budget-threshold validation, expected runtime/output projection, and explicit replay-critical families.
- A readiness classification that distinguishes `ready_for_review`, `blocked_by_two_zone_evidence`, `blocked_output_budget`, and `blocked_efficiency`.
- Tests proving the package cannot be promoted to live submission without a later task and current gate evidence.

Definition of done:

- The next-larger Balfrin scale step is reviewable and budget-classified without authorizing or submitting it.

Boundaries: Review package only; no live Balfrin submission, no scale-up authorization, no distributed execution, no Swiss-wide claim, no annual/physical/risk semantics, and no operational claim.

### TB-312: Four-Zone Balfrin Postproc Probe

Goal: Execute the four-zone `postproc` probe only if TB-311 and the latest scale dashboard show the package is ready and the run will not keep `postproc` fully busy for more than 6 hours.

Capability gap reduced: The project needs the next measured multi-zone point after two-zone before larger Balfrin or Swiss-scale planning can be credible.

Why this outranks alternatives: Four zones is the first local-ladder scale tier above the two-zone live probe and below the first local blocked 8-zone rung.

Inspect first:

- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/multi_zone_reducer_pressure_probe.md`

Deliverables:

- A GPT-5.5-routed four-zone `postproc` submission only if access, remote hygiene, budget, readiness, audit, and preservation gates pass.
- Preserved job id, run root, runtime, memory, reducer timing, output budget audit, manifest bytes, sidecar counts, hashes, and replay metadata.
- A fail-closed report if any gate blocks the run.

Definition of done:

- The four-zone branch is either measured on Balfrin and preserved or has one exact current blocker.

Boundaries: Exact four-zone `postproc` probe only; stop and rediscuss if estimated full-partition occupancy exceeds 6 hours; no non-postproc partition, no distributed execution, no Swiss-wide scale-up claim, no annual/physical/risk semantics, and no operational claim.

### TB-313: Hazard Accumulation Optimization From Measured Bottleneck

Goal: Implement one targeted hazard-accumulation optimization only if the benchmark harness shows it improves the `accumulation_seconds` bottleneck without changing hazard outputs.

Capability gap reduced: The local ladder identifies accumulation timing as the first 8-zone bottleneck, but no accepted optimization has reduced it yet.

Why this outranks alternatives: Execution efficiency must improve at the measured bottleneck before larger local or Balfrin scale steps are credible.

Inspect first:

- `scripts/hazard_accumulation_benchmark.py`
- `scripts/build_hazard_layers.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_hazard_accumulation_benchmark.py`
- `tests/test_hazard_layers.py`
- `tests/test_multi_zone_scaling_ladder.py`

Deliverables:

- One bounded optimization to trajectory accumulation or grid update logic, selected from benchmark evidence and guarded by before/after measurements.
- Output parity checks for hazard layers, manifests, checksums, and claim boundaries.
- Updated benchmark report showing speedup, memory impact, and whether the 8-zone local rung remains blocked.

Definition of done:

- The accepted optimization improves the measured accumulation bottleneck under the existing acceptance thresholds without changing numerical outputs or public CLI semantics.

Boundaries: One targeted optimization only; no physics changes, no output schema break, no live Balfrin submission, no distributed execution, no tuning, no annual/physical/risk semantics, and no operational claim.

### TB-314: Post-Optimization Local Scaling Ladder Refresh

Goal: Rerun the 1/2/4/8/12-zone local scaling ladder after any accepted accumulation optimization and update the first-blocked breakpoint.

Capability gap reduced: Efficiency improvements need to translate into changed scale evidence, not just isolated benchmark wins.

Why this outranks alternatives: The scale dashboard should guide live Balfrin actions from current measurements, not stale pre-optimization ladder data.

Inspect first:

- `scripts/summarize_multi_zone_scaling_ladder.py`
- `scripts/hazard_accumulation_benchmark.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Refreshed ladder measurements for 1, 2, 4, 8, and 12 zones with phase timing, manifest bytes, sidecars, output files, first bottleneck, and status changes.
- Scale-dashboard updates that separate pre-optimization and post-optimization evidence.
- A next-action recommendation for larger local ladder, four-zone live probe, or further optimization.

Definition of done:

- The local scaling frontier reflects the latest implementation and names the next safe scale action.

Boundaries: Local/fixture measurement only; no live Balfrin submission, no Swiss-wide claim, no distributed execution, no physical credibility claim, and no operational claim.

### TB-315: User AOI Guided Pipeline Command

Goal: Add a single guided command that takes AOI bounds or a bootstrapped AOI manifest and walks the user through status, prepare, local smoke, package-map, and QA-review steps.

Capability gap reduced: The repo has many AOI pieces, but a user still needs to know which commands to run and when to stop.

Why this outranks alternatives: A clear front door is required before arbitrary user-defined regions become practical.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/stage_public_geodata_cache.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- A guided front-door mode, for example `workflow`, that accepts bounds or a site config and emits the next command sequence, executing safe local steps when requested.
- Unified text and JSON output with current stage, first blocker, next command, generated artifact paths, and claim boundaries.
- Tests for blocked missing geodata, ready fixture, local smoke/package-map path, and invalid AOI input.

Definition of done:

- A user can start from AOI bounds or a site config and get a deterministic guided path to a local diagnostic review map or one exact blocker.

Boundaries: User-facing local workflow only; no network download unless a later task enables it, no live Balfrin submission, no operational claim, no annual/physical/risk semantics, and no heavy generated outputs committed.

### TB-316: Swisstopo Public Data Acquisition Driver

Goal: Add an explicit opt-in public-data acquisition driver that can fetch or stage required swisstopo products for a user-defined AOI while preserving license, source, checksum, CRS, and provenance records.

Capability gap reduced: User-defined AOI workflows still depend on manually downloaded or pre-staged public geodata.

Why this outranks alternatives: The biggest user friction after AOI definition is getting required terrain/context inputs into the verified cache manifest.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/stage_public_geodata_cache.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_swisstopo_aoi_acquisition_planner.py`
- `tests/test_public_geodata_cache_stager.py`

Deliverables:

- An opt-in acquisition driver with dry-run, local-copy, and download-enabled modes, defaulting to no network mutation unless the user explicitly passes a download/apply flag.
- Cache-manifest updates with source URL or delivery record, product version/date, tile id, raw checksum, processed checksum, CRS, resolution, extent, license reference, and preprocessing timestamp.
- Tests for dry-run, local-copy, blocked missing URL, checksum mismatch, and no-hidden-download behavior.

Definition of done:

- A user-defined AOI can move from resolved product rows to verified local cache inputs through a documented, auditable acquisition command.

Boundaries: Public geodata acquisition/staging only; no private data, no simulation, no live Balfrin submission, no operational claim, no physical validation claim, and no large swisstopo products committed.

### TB-317: User-Defined AOI End-To-End Local Demonstration

Goal: Demonstrate a new small user-defined AOI path from bounds through verified inputs, prepared pilot, local execution, map package, and QA review using the guided frontend.

Capability gap reduced: The AOI path is currently strongest on fixtures and known sites; the project needs a user-defined region demonstration that exercises the frontend.

Why this outranks alternatives: A project goal demonstration should show the workflow from user AOI definition to hazard map, not only internal helper interoperability.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_golden_fixture_package.py`

Deliverables:

- A bounded local demonstration for one small user-defined AOI using verified fixture or staged public inputs, reduced-output local execution, map packaging, and static QA review.
- A reproducible command transcript or test that proves the same path works from a clean checkout plus allowed fixture/staged inputs.
- Explicit non-operational, conditional-only, and no-annual-frequency labels in the generated package and docs.

Definition of done:

- The repo can show a user-facing AOI-to-review-map demonstration that starts from AOI definition and ends with an openable diagnostic hazard-map package.

Boundaries: Local bounded demonstration only; no live Balfrin submission, no Swiss-wide claim, no physical-probability semantics, no annual-frequency product, no risk/exposure/vulnerability claim, and no operational claim.

### TB-318: AOI Frontend Review Surface Polish

Goal: Improve the generated AOI review surface so users can inspect layers, warnings, provenance, and next actions without reading raw JSON manifests.

Capability gap reduced: The map package is reviewable, but the user-facing frontend is still mainly a static diagnostic bundle rather than a clear map workflow surface.

Why this outranks alternatives: The project goal includes producing a hazard map for a region; the review surface is the user's primary artifact.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/hazard_map_semantics.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_hazard_map_packager.py`
- `tests/test_aoi_map_qa_review.py`

Deliverables:

- A clearer static review page with layer inventory, legend, conditional semantics, warnings, provenance, observed-overlay status, first blocker, and next recommended command.
- Tests for missing layers, COG-blocked outputs, observed-evidence overlays, conditional-only labels, and non-operational warnings.
- Documentation update that points users to the generated review surface as the primary local output.

Definition of done:

- A user can open the generated review surface and understand what was produced, what is missing, and what the map is allowed to mean.

Boundaries: Frontend/review surface only; no hazard-value changes, no live Balfrin submission, no operational claim, no annual/physical/risk semantics, and no heavy outputs committed.

### TB-319: Post-Demonstration Capability And Gap Refresh

Goal: Refresh the maturity snapshot, README, scale dashboard, and backlog recommendations after the next Balfrin and user-AOI demonstration tasks complete.

Capability gap reduced: Once measured scale and frontend evidence changes, the repository needs one authoritative synthesis that prevents workers from following stale blocked paths.

Why this outranks alternatives: This should come after new measurements and user-facing demonstrations, not before them.

Inspect first:

- `README.md`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/print_agent_task_context.py`

Deliverables:

- Updated status docs and task-context summaries reflecting measured Balfrin runs, output/efficiency status, user-AOI frontend capability, and remaining scientific boundaries.
- Removal or correction of stale blockers that have been superseded by measured evidence, while preserving failed-closed branches as history.
- A short next-backlog recommendation list that favors execution, acquisition, optimization, or explicit deferral over further synthesis.

Definition of done:

- The repository tells one current story about scale, Balfrin readiness, user-defined AOI workflow, and remaining gaps after the new evidence lands.

Boundaries: Synthesis after evidence changes only; no live Balfrin submission, no new run, no claim upgrade beyond measured capability, no annual/physical/risk semantics, and no operational claim.

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
