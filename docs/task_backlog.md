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

### TB-130: Execute Live Balfrin Restartability And Resume Proof

Goal: Replace fixture-backed recovery evidence with a deliberately interrupted
and resumed Balfrin demonstration run.

Capability gap reduced: live HPC restartability credibility for the measured
Balfrin workflow.

Why this outranks alternatives: the repository now has measured Balfrin
execution, but interruption/recovery remains the largest fixture-backed
operational evidence class.

Inspect first:

- `docs/balfrin_restartability_recovery_report.md`
- `docs/balfrin_failure_recovery_playbook.md`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`

Deliverables:

- Live interrupted and resumed run evidence, or a precise blocked report if the
  scheduler/input state prevents the experiment.
- Measured recovery timing, reused/executed chunk counts, artifact-continuity
  checks, and updated restartability/evidence-bundle reporting.

Definition of done:

- The restartability report clearly classifies the live experiment as measured
  or blocked, and no fixture-backed proof is presented as live recovery.

Boundaries: One bounded single-node Balfrin run only; no tuning, distributed
execution, scale-up authorization, or operational claim.

### TB-131: Complete Balfrin Metrics Contract Coverage

Goal: Fill or explicitly downgrade the remaining missing measured fields in the
Balfrin metrics and evidence bundle.

Capability gap reduced: incomplete runtime/output evidence for demonstration
and scaling interpretation.

Why this outranks alternatives: measured execution exists, but missing or
ambiguous memory and split output fields weaken the evidence used by later
scaling and management-facing summaries.

Inspect first:

- `docs/balfrin_single_job_execution_sufficiency.md`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/`

Deliverables:

- Collector and bundle updates for peak-memory evidence, validation/hazard file
  counts, validation/hazard bytes, and explicit ancillary-unavailable states.
- Focused tests for complete, missing, and unavailable metric fields.

Definition of done:

- The Balfrin metrics contract reports no hidden missing mandatory fields for
  the measured run; unavailable fields are named and classified explicitly.

Boundaries: No new ensemble, no scale-up authorization, and no replacement of
measured evidence with synthetic evidence.

### TB-132: Prototype AOI-To-Swisstopo Product Tile Discovery

Goal: Given a Swiss LV95 AOI, deterministically report required swisstopo
products, tile candidates, staging roots, and blocked download prerequisites.

Capability gap reduced: Swiss-wide public-geodata automation before any
simulation runs.

Why this outranks alternatives: the current workflows still depend on manually
known products and roots; AOI-to-product discovery is the first reusable
Swiss-wide automation step.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_second_site_public_geodata_preflight.py`

Deliverables:

- Deterministic AOI-to-product/tile discovery helper or extension.
- JSON/text dry-run report with product names, candidate tiles or coverage
  descriptors, expected staging roots, missing catalog inputs, and no-download
  boundaries.

Definition of done:

- A fixture-backed AOI emits stable product/tile discovery output and a missing
  catalog/input case fails closed without downloading data.

Boundaries: No public-data download, no ensemble execution, no physical
probability or operational claim.

### TB-133: Emit Terrain Release-Zone Candidate Polygons And Masks

Goal: Convert deterministic terrain candidate metrics into reproducible
candidate polygon or mask products that can feed a dry-run workflow.

Capability gap reduced: manual release-zone dependence in the path from public
terrain to a prepared pilot.

Why this outranks alternatives: release-zone generation remains one of the
largest blockers to Swiss-wide automation, and the current candidate helper
reports metrics but not reusable spatial candidates.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `docs/swisstopo_data_strategy.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Deterministic candidate polygon or mask output mode, stable candidate IDs,
  provenance metadata, and comparison against the frozen Tschamut source-zone
  footprint.
- Fixture-backed tests for deterministic output and blocked missing-input
  behavior.

Definition of done:

- The helper can emit GIS-readable release-zone candidate products for a
  fixture or existing public terrain input without replacing the validated
  Tschamut source zone.

Boundaries: No threshold tuning to outcomes, no production release-zone
approval, and no physical release-probability claim.

### TB-134: Generate Deterministic Block-Scenario Tables From Policy

Goal: Turn the pragmatic block-scenario sensitivity plan into a deterministic
scenario-table generator from release metadata and policy inputs.

Capability gap reduced: handcrafted block-scenario table dependence.

Why this outranks alternatives: scenario generation is the second major manual
component after release-zone identification and is required before AOI-scale
workflow automation is credible.

Inspect first:

- `scripts/plan_pragmatic_release_plan.py`
- `scripts/generate_tschamut_same_scale_cases.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`

Deliverables:

- Deterministic scenario generator, provenance-aware scenario manifest, stable
  row IDs, configurable non-frequency scenario-family templates, and focused
  tests.

Definition of done:

- Scenario tables can be regenerated deterministically from committed policy
  and release metadata while preserving current conditional weighting
  semantics.

Boundaries: No physics changes, no annual frequency, no fitted block-size
population model, and no operational interpretation.

### TB-135: Execute Bounded Next Ensemble Probe

Goal: Run or produce a fail-closed plan for the smallest bounded next ensemble
probe that can materially test uncertainty/runtime tradeoffs.

Capability gap reduced: uncertainty reduction versus runtime/output ambiguity.

Why this outranks alternatives: frontier summaries now exist, but the next
scientific question is whether a small measured probe changes the stability
picture enough to justify further execution.

Inspect first:

- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- Measured bounded probe evidence or a precise blocked report.
- Runtime/output/stability comparison against existing same-scale and Balfrin
  evidence, with a conservative next-step recommendation.

Definition of done:

- The repository records whether the smallest useful next probe was measured or
  why it remains blocked, without changing closure status by assertion.

Boundaries: No large production ensemble, no tuning, no scale-up
authorization, and no operational claim.

### TB-136: Generate Persistent Hazard Confidence Products

Goal: Convert same-scale stability and persistence evidence into deterministic
GIS-readable diagnostic confidence products.

Capability gap reduced: uncertainty interpretation that is currently stronger
in scalar summaries than in reviewable spatial products.

Why this outranks alternatives: persistent hazard and unstable-region masks
make the existing uncertainty evidence more interpretable without requiring a
new model run.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/compare_hazard_map_convergence.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- Persistent-hazard, unstable-region, support/nodata-sensitive, and
  shared-support magnitude diagnostic products or manifests.
- Tests using fixture evidence and explicit GIS/product claim boundaries.

Definition of done:

- The helper emits stable diagnostic confidence products from measured
  same-scale evidence and reports blocked status when required rasters are
  absent.

Boundaries: Diagnostic uncertainty products only; no operational hazard,
annual-frequency, or physical-probability claim.

### TB-137: Prepare Chant Sura Real-Context Acquisition Readiness Pack

Goal: Convert the Chant Sura real-context trigger matrix into a precise
proceed/defer/stage readiness package for public-context products.

Capability gap reduced: second-site realism beyond synthetic core fixtures.

Why this outranks alternatives: portability remains metadata-level until the
project can state exactly which real public-context products should be staged
next and under which measured trigger.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`

Deliverables:

- Product-by-product acquisition decision report, staging commands, expected
  roots, and resulting preflight impact.
- Optional local staging only if required public products already exist and the
  trigger explicitly allows it; otherwise a blocked/deferred report.

Definition of done:

- Chant Sura has a deterministic readiness pack that separates proceed,
  defer, missing-input, and locally-stageable states without treating synthetic
  fixtures as public-context evidence.

Boundaries: No second-site ensemble, no hazard build, no unauthorized
downloads, and no synthetic evidence promotion.

### TB-138: Prepare Observed Runout And Deposition Benchmark Acquisition Pack

Goal: Turn physical-credibility gaps into a concrete benchmark acquisition
package for Balfrin/Tschamut evidence.

Capability gap reduced: missing validation and physical-credibility evidence.

Why this outranks alternatives: measured workflow credibility has improved, so
the dominant scientific credibility gap is now independent runout/deposition
evidence rather than another status matrix.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Acquisition checklist, required dataset inventory, geometry/provenance
  templates, objective-function placeholders, and blocked no-evidence report.
- Tests that keep benchmark-intake readiness separate from calibration
  readiness.

Definition of done:

- A field or data-acquisition worker can see exactly which independent
  benchmark artifacts are required before physical credibility can improve.

Boundaries: No calibration, fitting, parameter tuning, annual frequency, risk,
exposure, vulnerability, or operational claim.

### TB-139: Build Balfrin Demonstration Replay Smoke Test

Goal: Verify that the canonical Balfrin evidence bundle and interpretation can
be regenerated from the measured run root or fail closed when the run root is
absent.

Capability gap reduced: demonstration reproducibility and handoff robustness.

Why this outranks alternatives: evidence exists but management-facing replay
should not depend on implicit local state or scattered manual commands.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/orchestration_strategy.md`

Deliverables:

- Replay/smoke helper or command-plan path that checks run-root availability,
  regenerates the bundle/interpreter outputs, and records blocked status when
  remote artifacts are unavailable.
- Focused tests for present-run-root and missing-run-root behavior.

Definition of done:

- A fresh operator can run one deterministic smoke command to verify whether
  the current Balfrin demonstration evidence is replayable from available
  artifacts.

Boundaries: No new Slurm execution, no generated artifact commits, and no
claim-boundary changes.

### TB-140: Compose Site-Level AOI-To-Command-Plan Dry Run

Goal: Chain AOI product discovery, release-zone candidate generation,
scenario-table generation, output-root planning, and command-plan hooks into
one dry-run site orchestration report.

Capability gap reduced: missing composition layer between individual
automation helpers and an AOI-to-workflow user path.

Why this outranks alternatives: individual dry-run helpers now exist, but
Swiss-wide workflow realism requires proving they compose into one deterministic
site-level preparation plan.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_pragmatic_release_plan.py`
- `scripts/generate_pilot_command_plan.py`

Deliverables:

- End-to-end AOI/release-polygon dry-run report with product discovery,
  candidate source zones, scenario-generation inputs, ignored output roots,
  and runnable or blocked command-plan references.
- Tests covering deterministic fixture output and blocked missing-input states.

Definition of done:

- The repository has one compact dry-run command that shows how an AOI would be
  prepared up to, but not including, ensemble execution.

Boundaries: No downloads, no ensembles, no second-site hazard build, no
physical-probability semantics, and no operational claim.

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
