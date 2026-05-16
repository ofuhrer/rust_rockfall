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

### TB-118: Execute And Collect Balfrin Single-Release-Zone Demo

Goal: Run the canonical Balfrin demonstration workflow end-to-end for one
release zone, one bounded deterministic ensemble, one native reduced-output
workflow, and one GIS package path.

Capability gap reduced: Balfrin demonstration realism and measured execution
evidence.

Why this outranks alternatives: The repository now has substantial Balfrin
scaffolding, but the demonstration remains unmeasured. A real run is the next
highest-value evidence-producing step after the readiness mismatch is fixed.

Inspect first:

- `docs/balfrin_tschamut_pilot_runbook.md`
- `docs/balfrin_failure_recovery_playbook.md`
- `scripts/check_balfrin_tschamut_readiness.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml`

Deliverables:

- A measured Balfrin run root or a clearly classified blocked execution report
  using the outcome taxonomy in `docs/orchestration_strategy.md`.
- Collected metrics JSON/manifest evidence for wall time, memory, output bytes,
  file counts, reduced-output families, conditional curves, uncertainty
  products, GIS package outputs, closure interpretation summary, and
  restartability evidence.

Definition of done:

- The task status is `implemented_measured` only if a real Balfrin run root and
  collected metrics exist; otherwise it must leave or add the smallest unblock
  task before dependent synthesis work.

Boundaries: Use bounded deterministic ensembles and native rebuildable reduced
output only; do not run distributed/MPI/GPU jobs, large production ensembles, or
operational/physical-frequency products.

### TB-119: Build Canonical Balfrin Demonstration Evidence Bundle

Goal: Convert the measured Balfrin run root into one canonical evidence bundle
for readiness, metrics, outputs, GIS/COG status, restartability, failure
taxonomy, uncertainty summary, runtime summary, GIS-ready outputs, and
post-run interpretation.

Capability gap reduced: Reproducible demonstration evidence and auditability.

Why this outranks alternatives: Management-facing and scientific review should
consume one coherent measured bundle, not scattered helper outputs or
fixture-backed reports.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `scripts/summarize_balfrin_failure_taxonomy.py`
- `docs/balfrin_post_run_interpretation_gate.md`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- A canonical measured evidence-bundle JSON/text path or an explicit
  `blocked_missing_measured_run` report if TB-116 did not produce a run root.
- Tests or smoke checks showing the bundle distinguishes measured, fixture, and
  blocked sections.

Definition of done:

- The bundle helper reports a measured bundle from the Balfrin run evidence, or
  the task records a blocked outcome without pretending the fixture-backed
  bundle is measured.

Boundaries: Do not fabricate missing metrics, do not commit large generated
outputs, and do not broaden claim boundaries.

### TB-120: Demonstrate Measured Balfrin Restartability And Recovery

Goal: Interrupt and recover the canonical Balfrin demonstration or classify why
a live interruption/recovery proof remains blocked, using measured run evidence
where available.

Capability gap reduced: Rebuild-compatible execution realism and recovery
confidence.

Why this outranks alternatives: TB-106 and TB-108 are useful fixture-backed
proofs, but they are not live Balfrin interruption/output evidence. The
demonstration needs this distinction closed or explicitly preserved.

Inspect first:

- `scripts/summarize_balfrin_output_tier_audit.py`
- `scripts/summarize_balfrin_restartability_recovery.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `tests/fixtures/balfrin_probe_metrics_contract/complete_run_root`
- `docs/balfrin_restartability_recovery_report.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Interrupted-run and resumed-run evidence when feasible, including manifest
  continuity, output continuity, restartability timing, and deterministic
  recovery checks.
- Measured output-tier sufficiency and restartability/recovery reports from the
  real run root, or explicit blocked reports if live interruption/recovery is
  not available.
- Updated tests that preserve fixture-backed behavior while proving measured
  evidence is classified separately.

Definition of done:

- The reports no longer imply fixture-backed evidence is a live Balfrin
  measurement; focused checks pass and TB-120 is removed.

Boundaries: Do not create artificial interruption evidence, do not rerun large
ensembles unless explicitly required by the runbook, and do not classify
`summary_only` as rebuildable.

### TB-121: Generate Canonical Balfrin Conditional Diagnostic Interpretation

Goal: Produce one coherent measured Balfrin interpretation that combines
uncertainty, convergence, scaling, GIS readiness, portability, closure
semantics, and physical-credibility boundaries.

Capability gap reduced: Scientific interpretability and uncertainty-aware
demonstration meaning.

Why this outranks alternatives: A successful run is not automatically a
credible diagnostic result; it must be interpreted against the known
closure-limiting uncertainty evidence.

Inspect first:

- `scripts/summarize_balfrin_scientific_delta_report.py`
- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- A canonical measured interpretation artifact that states whether the run
  supports, weakens, or leaves unchanged the current inconclusive diagnostic
  interpretation.
- Machine-readable blocker and boundary fields for closure-limiting layers,
  GIS/product scope, runtime/output sufficiency, portability status, and
  physical-credibility limits.

Definition of done:

- The scientific delta helper consumes measured Balfrin evidence and reports a
  bounded interpretation without changing closure criteria by assertion.

Boundaries: Do not tune physics, change acceptance thresholds, or claim physical
validation from conditional diagnostic agreement.

### TB-122: Resolve Balfrin GIS/COG Demonstration Scope Delta

Goal: Make the Balfrin demonstration GIS package either full-scope COG-ready or
explicitly encode the intended scope delta in the measured evidence bundle.

Capability gap reduced: GIS-readable product usability for the demonstration.

Why this outranks alternatives: GIS polish is secondary to execution, but a
management-facing Balfrin demonstration needs package scope and missing layers
to be unambiguous.

Inspect first:

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/build_hazard_layers.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/pilot_gis_package.md`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A full-scope COG export command for the measured Balfrin package or a
  machine-readable scope-delta classification that the evidence bundle exposes.
- Focused tests for full-scope, scope-delta, and blocked-missing-package cases.

Definition of done:

- Demonstration GIS/COG status is not ambiguous: the package is full-scope ready
  or intentionally scope-limited with exact missing layer semantics.

Boundaries: Do not commit generated rasters, do not require manual QGIS QA, and
do not convert GIS readiness into operational approval.

### TB-123: Generate Balfrin Terrain-Driven Release-Zone Candidate Metrics

Goal: Produce deterministic terrain-driven release-zone candidate metrics for
the Balfrin/Tschamut AOI without using them as field-validated release zones.

Capability gap reduced: Workflow automation and release-zone generation
reproducibility.

Why this outranks alternatives: Swiss-wide automation needs reproducible
terrain-derived candidates; the current workflow still depends on preselected
release-zone records for real execution.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `data/processed/swisstopo/tschamut_public_pilot/input/`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A deterministic dry-run candidate report for the Balfrin/Tschamut AOI with
  slope/terrain criteria, candidate counts, excluded areas, and provenance.
- Tests proving deterministic output and blocked behavior when public inputs
  are absent.

Definition of done:

- The helper emits reproducible candidate metrics and explicitly states that
  candidates are heuristic workflow inputs, not validated release zones.

Boundaries: Do not replace the frozen pilot release zone, tune thresholds to
match outcomes, or claim physical release probability.

### TB-124: Generate Deterministic Balfrin Block-Scenario Sensitivity Plan

Goal: Produce a deterministic block-scenario sensitivity plan for the Balfrin
demo that separates pragmatic scenario coverage from physical frequency claims.

Capability gap reduced: Scenario generation reproducibility and uncertainty
interpretation.

Why this outranks alternatives: Block mass/radius and scenario weighting remain
major uncertainty drivers; the next demo should expose scenario coverage
explicitly instead of hiding it inside a frozen table.

Inspect first:

- `scripts/plan_pragmatic_release_plan.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`
- `validation/policies/`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- A deterministic scenario-plan report with block-size bins, weighting
  semantics, source-policy provenance, and explicit non-frequency labels.
- Tests for deterministic generation and blocked/missing-input behavior.

Definition of done:

- The scenario plan can be regenerated from public/frozen inputs and clearly
  distinguishes sampling weights from physical occurrence frequencies.

Boundaries: Do not fit block-size distributions, infer annual frequencies, or
change the already measured Balfrin demo unless a later task authorizes it.

### TB-125: Prototype AOI-To-Demonstration Preparation Path

Goal: Given AOI extents or a release polygon, prepare the deterministic inputs
needed for a demonstration workflow without running an ensemble.

Capability gap reduced: AOI-to-workflow automation and Swiss-wide portability.

Why this outranks alternatives: The current workflow still assumes substantial
Tschamut-specific preparation. A minimal AOI-to-demonstration path is the first
real generalization step toward Swiss-wide automation.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_pragmatic_release_plan.py`
- `scripts/generate_pilot_command_plan.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A dry-run preparation report that emits terrain manifests, context manifests,
  release/scenario placeholders, command-plan hooks, and ignored output roots
  from an AOI or release polygon input.
- Tests for deterministic output and blocked/missing-input behavior.

Definition of done:

- The prototype can prepare a bounded demonstration scaffold without executing
  trajectories, downloading real data, or treating placeholders as evidence.

Boundaries: Do not run ensembles, download public context, or claim release-zone
validity from the dry-run scaffold.

### TB-126: Define Second-Site Real-Context Trigger From Balfrin Evidence

Goal: Convert the Chant Sura / Fluelapass defer decision into a concrete
measured trigger for when real public-context staging should proceed.

Capability gap reduced: Swiss-wide portability realism and second-site
planning discipline.

Why this outranks alternatives: Portability work should not jump to downloads
or second-site execution before the Balfrin demonstration shows which evidence
classes and product scopes matter.

Inspect first:

- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A machine-readable or documented trigger matrix linking Balfrin outcomes to
  proceed/defer decisions for SWISSIMAGE, swissTLM3D, swissSURFACE3D,
  swissSURFACE3D Raster, and swissBUILDINGS3D staging.
- Tests or smoke checks for proceed, defer, and blocked trigger states if
  helper code changes.

Definition of done:

- The next second-site acquisition decision can be made from measured Balfrin
  evidence without treating synthetic fixtures as public-context evidence.

Boundaries: Do not download real public context, do not run a second-site
ensemble, and do not override the existing defer decision without measured
Balfrin evidence.

### TB-127: Measure Practical Balfrin Ensemble Frontier

Goal: Estimate the smallest useful next Balfrin ensemble by comparing runtime,
output growth, rebuildability cost, and uncertainty/stability changes across
measured or bounded ensemble evidence.

Capability gap reduced: Ensemble-size practicality and uncertainty
characterization.

Why this outranks alternatives: After a measured demonstration exists, the next
question is not Swiss-wide production; it is the smallest additional bounded
ensemble that would materially improve uncertainty interpretation.

Inspect first:

- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_balfrin_scientific_delta_report.py`
- `scripts/summarize_balfrin_single_job_execution.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- A practical ensemble-frontier report with uncertainty reduction, runtime
  growth, output growth, rebuildability cost, and a minimum-useful-ensemble
  recommendation or explicit defer/no-go label.
- Tests preserving blocked behavior when measured Balfrin evidence is absent.

Definition of done:

- The report identifies whether a next bounded ensemble is scientifically
  justified and operationally practical without authorizing production scale-up.

Boundaries: Do not run a large production ensemble, tune physics, or authorize
Swiss-wide execution.

### TB-128: Update Swiss-Wide Envelope From Measured Balfrin Demo

Goal: Recompute the Swiss-wide runtime, storage, file-count, memory, and
job-count planning envelope from measured Balfrin demo evidence.

Capability gap reduced: Swiss-wide scaling realism and bounded execution
planning.

Why this outranks alternatives: The current envelope has conservative blocked
and no-go paths, but real Balfrin evidence is needed before future scaling
claims or larger bounded probes are meaningful.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_single_job_execution.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A measured-envelope report anchored to the Balfrin run with clear no-go,
  defer, and allowed-next-probe labels.
- Tests preserving blocked behavior when measured Balfrin evidence is absent.

Definition of done:

- The envelope helper consumes measured Balfrin evidence and still keeps
  `scale_up_authorized=false` unless a later explicit phase change exists.

Boundaries: Do not authorize Swiss-wide execution, distributed execution, or
production ensembles; this is a planning envelope only.

### TB-129: Map Balfrin Demo Evidence To Physical-Credibility Gaps

Goal: Map the measured Balfrin demo outputs to the existing physical
credibility, validation, and calibration evidence requirements.

Capability gap reduced: Physical-credibility boundary clarity and validation
realism.

Why this outranks alternatives: A successful conditional demo could be
misread as physical validation unless the missing field evidence and calibration
requirements remain explicit.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A Balfrin-specific evidence-gap report showing which physical-credibility
  requirements remain missing after the demo and which, if any, are only
  diagnostic/reproducibility evidence.
- Tests or smoke checks for measured, blocked, and no-physical-evidence states.

Definition of done:

- The report prevents a measured Balfrin run from being confused with
  calibration, validation, annual-frequency, or operational evidence.

Boundaries: Do not introduce calibration, fitting, return periods, risk,
exposure, vulnerability, or physical-probability claims.
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
