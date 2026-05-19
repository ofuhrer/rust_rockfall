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

### TB-320: Repair Two-Zone Balfrin Submit Contract

Goal: Repair or regenerate the failed-closed two-zone Balfrin submit package so it uses the executable `public_real_site_conditional_pilot_run_v1` contract instead of the target-area wrapper manifest.

Capability gap reduced: The smallest multi-zone Balfrin path is currently blocked before `sbatch` by a manifest-contract mismatch.

Why this outranks alternatives: No larger Balfrin scale measurement is meaningful until the first multi-zone submit contract can pass the existing access, readiness, output-budget, and preservation gates.

Inspect first:

- `docs/balfrin_two_zone_probe_tb309.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `tests/test_balfrin_authorized_multi_zone_submit.py`

Deliverables:

- A corrected two-zone submit package or package generator path that points at the executable pilot-run manifest contract.
- Focused tests proving the previous TB-309 mismatch fails and the repaired package passes pre-submit contract validation.
- Updated docs naming the repaired command and the remaining live-run gates.

Definition of done:

- The two-zone submit package passes local contract/preflight checks and is ready for a GPT-5.5 Balfrin worker to run through the live `postproc` gates.

Boundaries: Contract repair only; no live Balfrin submission in this task, no scale-up claim, no operational claim, no annual/physical/risk semantics.

### TB-321: Execute Repaired Two-Zone Balfrin Probe

Goal: Run the repaired bounded two-zone Balfrin probe on `postproc` after all access, submit-contract, output-budget, preservation, and evidence gates pass.

Capability gap reduced: The repo lacks any measured multi-zone Balfrin hazard execution beyond single-zone and post-processing-only evidence.

Why this outranks alternatives: A measured two-zone run is the smallest credible step from single-release-zone demonstration toward scale feasibility.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/balfrin_two_zone_probe_tb309.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`

Deliverables:

- One live two-zone `postproc` job submission from the repaired package, or a fail-closed report with the exact gate that blocked submission.
- Preserved run root, job id, scheduler status, command plan, logs, metrics, and preservation/output-budget evidence when submission succeeds.
- Boundary note distinguishing measured multi-zone hazard execution from postproc-only or fixture evidence.

Definition of done:

- Either the two-zone probe completes and measured evidence is preserved, or the task records a new precise pre-submit/live-run blocker that replaces the stale TB-309 blocker.

Boundaries: Bounded `postproc` run only under standing clearance with GPT-5.5 routing; no non-postproc partition, distributed execution, scale-up claim, operational claim, or annual/physical/risk semantics.

### TB-322: Integrate Two-Zone Balfrin Evidence

Goal: Integrate the TB-321 two-zone outcome into the scale dashboard, run-root audits, maturity snapshot, and next-action recommendations.

Capability gap reduced: Measured or fail-closed two-zone results must become machine-readable so later workers do not follow stale scale recommendations.

Why this outranks alternatives: The next Balfrin scale step depends on whether TB-321 produced measured evidence or a new blocker.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Dashboard tier update for the two-zone branch with correct evidence label, runtime/output metrics, and next recommended scaling task.
- Read-only output-budget summary for the preserved run root when available.
- Documentation update that preserves failed-closed history without promoting it to measured evidence.

Definition of done:

- The scale matrix and docs tell one current story about two-zone status and the next scale step.

Boundaries: Synthesis after measured or fail-closed evidence only; no new Balfrin job, no claim upgrade, no annual/physical/risk semantics.

### TB-323: Real AOI Public-Geodata Acquisition Pack

Goal: Prepare an operator-ready acquisition pack for one small real AOI using the explicit swisstopo acquisition driver without committing large products.

Capability gap reduced: The AOI path remains fixture-backed until real public products can be selected, sourced, checksummed, and staged through the cache manifest.

Why this outranks alternatives: A real AOI feasibility demonstration needs staged public geodata before terrain preprocessing, release candidates, or scenarios matter.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/stage_public_geodata_cache.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_public_geodata_cache_stager.py`

Deliverables:

- A deterministic acquisition package for one bounded AOI with required products, source records, expected cache paths, license references, and operator choices.
- Dry-run and local-copy command transcript using ignored roots; download commands remain opt-in and side-effect explicit.
- Verification output showing which products are ready, missing, or blocked.

Definition of done:

- A user can take the acquisition pack and either stage local public data or see the exact missing source records needed for the AOI.

Boundaries: Public geodata acquisition/staging only; no private data, no simulation, no live Balfrin submission, no large swisstopo products committed, no operational claim.

### TB-324: Real AOI Terrain And Context Preprocessing Gate

Goal: Extend the AOI preprocessing path so real staged swissALTI3D terrain and selected context products produce deterministic manifests, QA summaries, and blocked/ready classifications.

Capability gap reduced: The current terrain/context preprocessing surface is strongest on fixtures and needs a real-staged-input gate before arbitrary AOIs are credible.

Why this outranks alternatives: Release-zone candidate generation on real terrain is only meaningful after the terrain/context preprocessing contract is deterministic and auditable.

Inspect first:

- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/verify_public_geodata_cache.py`
- `scripts/run_aoi_hazard_workflow.py`
- `docs/swiss_terrain_ingestion_pilot.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_terrain_preprocessing.py`

Deliverables:

- Preprocessing report fields for real staged terrain/context provenance, CRS, extent, resolution, nodata, source tile ids, and QA blockers.
- Tests for verified real-input-like fixtures, missing context, CRS/extent mismatch, and deterministic output roots.
- Documentation showing how the gate feeds the guided AOI workflow.

Definition of done:

- The AOI front door can distinguish fixture-backed, missing, mismatched, and real-staged preprocessing readiness without generating heavy outputs.

Boundaries: Preprocessing gate only; no release-zone validation claim, no simulation, no Balfrin submission, no operational claim.

### TB-325: Real-Terrain Release-Zone Candidate Sweep

Goal: Run the deterministic terrain-driven release-zone candidate generator across a larger real or real-like staged AOI and measure candidate counts, geometry sizes, runtime, and output pressure.

Capability gap reduced: Release-zone generation remains a core Swiss-scale automation gap and needs measured behavior beyond handcrafted single-zone examples.

Why this outranks alternatives: Multi-zone scenario and Balfrin scaling projections depend directly on how many candidate zones the heuristic produces.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `docs/swisstopo_data_strategy.md`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `tests/test_balfrin_target_area_candidate_stability.py`

Deliverables:

- Candidate sweep summary with slope/topography thresholds, component counts, area distributions, runtime, file counts, and output bytes.
- GIS-ready candidate masks or vector outputs in ignored scratch roots.
- Comparison to existing Tschamut/Balfrin candidate behavior without claiming validation.

Definition of done:

- The repo has measured release-candidate cardinality and output pressure for a larger AOI, with deterministic rerun evidence.

Boundaries: Heuristic candidate generation only; no validated release-zone claim, no tuning to fit outcomes, no simulation, no operational claim.

### TB-326: Release-Zone Stability Ranking For Scale

Goal: Rank automatically generated release-zone candidates by stability under slope threshold, smoothing, terrain resolution, and AOI-boundary perturbations.

Capability gap reduced: Candidate generation needs defensible prioritization before many-zone scenario generation and Balfrin execution.

Why this outranks alternatives: Running every heuristic candidate is likely wasteful; stability ranking gives a reproducible way to choose bounded probe subsets.

Inspect first:

- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `docs/current_maturity_snapshot.md`
- `docs/swisstopo_data_strategy.md`
- `tests/test_balfrin_target_area_candidate_stability.py`

Deliverables:

- Stability-score summary for candidate polygons with stable/unstable/sensitive classifications.
- Deterministic top-N candidate selection for two-zone, four-zone, and eight-zone bounded probes.
- Tests proving ranking is stable and does not depend on filesystem ordering.

Definition of done:

- A later worker can select bounded multi-zone probe candidates from a deterministic stability ranking.

Boundaries: Ranking heuristic only; no physical credibility, calibration, source-frequency, or operational release-zone claim.

### TB-327: Multi-Zone Scenario Table Stress Test

Goal: Generate deterministic scenario tables for the selected stable release-zone candidates and measure scenario cardinality, manifest pressure, and output-root expectations.

Capability gap reduced: Scenario generation for many zones is not yet measured enough to project runtime/output pressure.

Why this outranks alternatives: Balfrin scale feasibility depends on scenario count and scenario-family structure before execution.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/generate_balfrin_target_area_scenario_tables.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `docs/source_zone_block_scenario_policy_v1.md`
- `tests/test_candidate_source_zone_scenario_stress.py`
- `tests/test_aoi_scenario_preview.py`

Deliverables:

- Deterministic scenario tables for 2, 4, 8, and 12 selected zones in ignored scratch roots.
- Cardinality, block-family, seed-policy, manifest-size, and expected-output summaries.
- Tests for deterministic ordering and bounded output sizes.

Definition of done:

- The repo can estimate scenario pressure for selected multi-zone AOIs before any Balfrin submission.

Boundaries: Conditional scenario generation only; no source-frequency semantics, no physics tuning, no simulation, no operational claim.

### TB-328: AOI Scenario Cost Projection Model

Goal: Convert release-zone and scenario-table cardinality into a deterministic runtime, storage, and reducer-pressure projection for bounded AOI sizes.

Capability gap reduced: Management needs Swiss-scale feasibility projections grounded in measured candidate/scenario pressure rather than vague extrapolation.

Why this outranks alternatives: The next Balfrin run sizes should be chosen from projected cost and uncertainty value, not arbitrary zone counts.

Inspect first:

- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/estimate_large_scale_execution.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/hazard_workflow_scale_review.md`
- `docs/performance_benchmark_synthetic_scale.md`
- `tests/test_aoi_scenario_preview.py`

Deliverables:

- Cost projection helper output for 2, 4, 8, 12, 50, and 100-zone AOI shapes.
- Separation of measured, scratch-local, projection-only, and no-go classifications.
- Documentation of assumptions and uncertainty in the projection.

Definition of done:

- The scale dashboard or companion report can state which AOI sizes are plausible, blocked, or out of reach under current single-node/postproc constraints.

Boundaries: Projection only unless using already measured inputs; no Swiss-scale authorization, no operational claim, no annual/physical/risk semantics.

### TB-329: Real-Input AOI Prepared-Pilot Compiler

Goal: Make the AOI-to-prepared-pilot compiler consume verified real-staged input manifests and produce a clean ignored handoff bundle for bounded local or Balfrin review.

Capability gap reduced: The current prepared-pilot path is fixture-backed and must advance to real-staged input readiness before a real AOI demonstration is credible.

Why this outranks alternatives: Prepared-pilot handoff is the bridge between acquisition/preprocessing and executable local or Balfrin workflows.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- Real-input-ready classification path for prepared-pilot bundles with explicit blockers for missing terrain, source zones, scenarios, or context.
- Ignored-root handoff layout and command transcript for local smoke and Balfrin review.
- Tests separating fixture-backed, real-staged-ready, and blocked-missing-input states.

Definition of done:

- A real-staged AOI can produce a deterministic prepared-pilot handoff or one exact blocker.

Boundaries: Handoff generation only; no live Balfrin submission, no second-site ensemble execution, no physical-frequency semantics, no operational claim.

### TB-330: User AOI Local Multi-Zone Smoke Demonstration

Goal: Run a bounded local multi-zone smoke demonstration from AOI bounds or a real-staged handoff through reduced validation output, hazard packaging, and QA review.

Capability gap reduced: The AOI-to-map path is currently fixture-backed and mostly single-smoke; it needs a small multi-zone local proof before Balfrin scale runs.

Why this outranks alternatives: Local multi-zone smoke catches workflow and output-profile issues cheaply before consuming Balfrin time.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `tests/test_run_aoi_hazard_workflow.py`
- `tests/test_aoi_golden_fixture_package.py`

Deliverables:

- Local two-zone or four-zone smoke command/test using reduced outputs and ignored scratch roots.
- Measured local runtime, file count, bytes, package status, and QA-review entrypoint.
- Explicit blockers if real-staged inputs are not available.

Definition of done:

- A user-facing command or regression demonstrates AOI-to-review-map behavior for more than one candidate zone locally.

Boundaries: Local bounded smoke only; no live Balfrin submission, no Swiss-wide claim, no operational claim, no annual/physical/risk semantics.

### TB-331: Four-Zone Balfrin Hazard Probe Package

Goal: Build a reviewed four-zone Balfrin hazard-execution package from the repaired two-zone path and measured cost projections.

Capability gap reduced: The repo has measured four-zone post-processing evidence but not a four-zone hazard execution package that can pass submit gates.

Why this outranks alternatives: A four-zone hazard package is the next credible step after a measured two-zone run and before larger AOI projections.

Inspect first:

- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/balfrin_four_zone_probe_tb312.md`
- `tests/test_balfrin_multi_release_zone_demo_handoff.py`

Deliverables:

- Four-zone hazard-execution package with command plan, authorization/audit record, reduced-output settings, expected output budget, and preservation instructions.
- Pre-submit report classifying the package as ready or blocked with exact reason.
- Tests for package shape and output-budget compliance.

Definition of done:

- A GPT-5.5 Balfrin worker can execute or fail-close the four-zone hazard probe from a reviewed package without inventing missing details.

Boundaries: Package/pre-submit only; no live Balfrin submission, no scale-up claim, no operational claim, no annual/physical/risk semantics.

### TB-332: Execute Four-Zone Balfrin Hazard Probe

Goal: Submit and monitor the reviewed four-zone Balfrin hazard probe on `postproc` if TB-331 and all live gates pass.

Capability gap reduced: The project needs measured multi-zone hazard execution beyond two zones to support scale feasibility projections.

Why this outranks alternatives: Four zones is the smallest next step that can reveal nonlinear runtime, output, reducer, or manifest pressure after two-zone evidence.

Inspect first:

- `docs/orchestration_strategy.md`
- `docs/balfrin_probe_slurm_driver.md`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/audit_balfrin_run_root_output_budget.py`

Deliverables:

- Live four-zone `postproc` job evidence, or a fail-closed report with exact gate failure.
- Preserved run root, scheduler status, logs, metrics, output-budget audit, and replay/preservation summary when successful.
- Boundary note separating measured hazard execution from prior postproc-only evidence.

Definition of done:

- The four-zone branch becomes measured-on-Balfrin hazard evidence or a precise blocked branch in the scale dashboard.

Boundaries: Bounded `postproc` run only under standing clearance with GPT-5.5 routing; no non-postproc partition, distributed execution, scale-up claim, operational claim, or annual/physical/risk semantics.

### TB-333: Integrate Four-Zone Hazard Evidence

Goal: Integrate the four-zone hazard probe outcome into the scale dashboard, maturity snapshot, reducer-pressure docs, and next-run decision surface.

Capability gap reduced: New measured scale evidence must update projections and next-run choices before larger work is proposed.

Why this outranks alternatives: The decision to attempt eight zones or optimize depends on the measured four-zone hazard outcome.

Inspect first:

- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `docs/current_maturity_snapshot.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_balfrin_scale_readiness_matrix.py`

Deliverables:

- Scale dashboard row for the four-zone hazard branch with evidence label, metrics, output pressure, and next recommended action.
- Updated local-vs-Balfrin comparison preserving postproc-only and hazard-execution distinctions.
- Tests for evidence taxonomy and next-action ranking.

Definition of done:

- The repo can state whether four-zone hazard execution supports an eight-zone probe, requires optimization, or should be deferred.

Boundaries: Evidence integration only; no new Balfrin job, no claim upgrade, no annual/physical/risk semantics.

### TB-334: Hazard Accumulation Profiling At Multi-Zone Scale

Goal: Profile hazard accumulation, raster writing, reducer merge, and manifest generation using the largest available measured/local multi-zone artifacts.

Capability gap reduced: TB-313 rejected one accumulator micro-optimization; future performance work needs a new measured bottleneck and acceptance floor.

Why this outranks alternatives: Optimization should follow measured phase costs, not broad speculation.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/build_hazard_layers.py`
- `docs/hazard_throughput_bottleneck_report.md`
- `tests/test_multi_zone_scaling_ladder.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Phase-level profile for available two/four-zone evidence or scratch-local ladder artifacts.
- Identification of the dominant bottleneck and a numeric acceptance threshold for any proposed optimization.
- Explicit no-op recommendation if no bottleneck clears the threshold.

Definition of done:

- The next performance task has a measured target, or performance work is explicitly deferred.

Boundaries: Profiling/analysis only unless a trivial measurement harness fix is required; no physics changes, no new Balfrin job, no operational claim.

### TB-335: Implement Measured Hazard Throughput Improvement

Goal: Implement one narrowly scoped performance improvement only if TB-334 identifies a measured bottleneck with a defensible acceptance threshold.

Capability gap reduced: Multi-zone feasibility may depend on reducing the dominant local or Balfrin hazard-build bottleneck.

Why this outranks alternatives: A targeted measured optimization can improve scale feasibility, but only after profiling prevents churn.

Inspect first:

- `docs/hazard_throughput_bottleneck_report.md`
- `scripts/build_hazard_layers.py`
- `tests/test_hazard_layers.py`
- `tests/test_multi_zone_scaling_ladder.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`

Deliverables:

- One scoped implementation change tied to the measured bottleneck.
- Before/after runtime or phase timing evidence meeting the predeclared threshold, or a reverted/no-op result if it fails.
- Tests proving output equivalence and deterministic manifests.

Definition of done:

- The repo either lands a measured throughput improvement or records a rejected optimization without changing behavior.

Boundaries: No physics changes, no output semantics changes, no tuning, no live Balfrin submission unless a later task authorizes measurement, no operational claim.

### TB-336: Reducer And Manifest Scaling Hardening

Goal: Reduce or bound reducer sidecar, manifest, and merge pressure for multi-zone AOI runs without losing rebuildability.

Capability gap reduced: Multi-zone scale can fail on manifest/sidecar pressure even when trajectory execution is acceptable.

Why this outranks alternatives: TB-309/TB-314 evidence shows manifest and reducer artifacts are central scale gates.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `docs/output_budget_reducer_scaling_gate.md`
- `tests/test_multi_zone_reducer_pressure.py`
- `tests/test_output_budget_reducer_gate.py`

Deliverables:

- Hardening change or stricter bounded policy for reducer manifests/sidecars across 2/4/8/12-zone projections.
- Tests showing rebuild-critical files remain present while debug fanout is bounded.
- Updated reducer-pressure docs and scale-dashboard inputs if policy changes.

Definition of done:

- Multi-zone reducer pressure is lower or more explicitly bounded without breaking hazard rebuild compatibility.

Boundaries: Output/reducer policy only; no trajectory physics changes, no live Balfrin job, no operational or scale-up claim.

### TB-337: Large-AOI GIS And COG Packaging Stress Test

Goal: Stress-test GIS package generation, QA-review HTML, manifest size, and COG conversion behavior on a realistically large AOI package shape.

Capability gap reduced: A Balfrin feasibility demonstration must show that hazard outputs can become usable diagnostic map packages at larger AOI sizes.

Why this outranks alternatives: GIS packaging is secondary to execution, but it can still become the first user-facing bottleneck once multi-zone runs succeed.

Inspect first:

- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/pilot_gis_package.md`
- `tests/test_large_aoi_gis_cog_stress_test.py`
- `tests/test_aoi_hazard_map_packager.py`

Deliverables:

- Large-AOI package stress report with raster/vector counts, COG timing, manifest bytes, QA HTML size, file count, and first blocker.
- Explicit classification of ready, COG-blocked, or no-go package sizes.
- Tests for deterministic stress outputs and claim-boundary labels.

Definition of done:

- The repo can project GIS/COG package practicality for the next multi-zone Balfrin demonstration size.

Boundaries: Packaging stress only; no hazard-value changes, no live Balfrin submission, no operational claim, no annual/physical/risk semantics.

### TB-338: Swiss-Scale Feasibility Projection From Measured Evidence

Goal: Produce a measured-evidence-based projection for 10, 100, regional, and Swiss-scale AOI workflows using current release-zone, scenario, runtime, reducer, and GIS evidence.

Capability gap reduced: Management needs a defensible answer on whether Swiss-scale execution is feasible or out of reach under current architecture.

Why this outranks alternatives: This projection should come after two/four-zone, release/scenario, and packaging evidence are integrated.

Inspect first:

- `scripts/estimate_large_scale_execution.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `docs/current_maturity_snapshot.md`
- `docs/hazard_workflow_scale_review.md`

Deliverables:

- Swiss-scale projection report separating measured evidence, extrapolated assumptions, no-go thresholds, and unknowns.
- Runtime, storage, reducer, manifest, GIS/COG, and operator-effort estimates for defined AOI sizes.
- Recommendation of feasible, conditionally feasible, or out-of-reach under current single-node/postproc constraints.

Definition of done:

- The repo can give management a bounded, evidence-labeled Swiss-scale feasibility projection without overclaiming.

Boundaries: Projection and synthesis only; no new run, no Swiss-scale authorization, no operational claim, no annual/physical/risk semantics.

### TB-339: Balfrin Scale Demonstration Management Package

Goal: Produce a concise management-facing package that explains current Balfrin feasibility, measured scale evidence, failed-closed branches, next run choice, and Swiss-scale projection.

Capability gap reduced: Technical evidence is now distributed across many helpers and needs one bounded demonstration narrative for decision makers.

Why this outranks alternatives: Management needs a clear projection and next decision after the measured multi-zone and Swiss-scale projection tasks, not another raw technical report.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `tests/test_balfrin_management_demo_package.py`

Deliverables:

- Management package summarizing measured Balfrin evidence, AOI automation maturity, Swiss-scale feasibility classification, top blockers, and recommended next run.
- Clear separation of measured, projection-only, failed-closed, and deferred evidence.
- Explicit non-operational and no-physical-frequency boundaries.

Definition of done:

- A non-technical reader can understand whether the current architecture plausibly scales, what evidence supports that answer, and what must be done next.

Boundaries: Management synthesis only after evidence/projection tasks; no claim upgrade, no new Balfrin job, no operational claim, no annual/physical/risk semantics.

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
