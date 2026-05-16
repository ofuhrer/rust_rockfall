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
