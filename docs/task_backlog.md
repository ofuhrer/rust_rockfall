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

### TB-610: Regenerate Adjacent-Candidate Scenario Tables For Scale Planning

Goal: Move the active management-AOI path from candidate review into concrete scenario-table evidence.

Capability gap reduced: Reduces the scenario-cardinality and batching uncertainty that blocks larger Balfrin packages.

Why this outranks alternatives: The current task context says to prefer the adjacent-candidate review path over stale source-zone-overlap repair.

Inspect first:

- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/generate_balfrin_target_area_scenario_tables.py`
- `scripts/measure_scenario_storage_output_tier_pressure.py`
- `scripts/summarize_management_aoi_scenario_pressure.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Generate or refresh scenario-table evidence for the adjacent-candidate path and measure row counts, storage, manifest pressure, and batching implications.

Definition of done:

- Scenario-cardinality pressure is measured for the current active path and the next Balfrin package size can use that evidence.


### TB-611: Build A 100-Zone Diagnostic Submission Package Without Submitting It

Goal: Prepare a 100-zone diagnostic package to expose exact package size, commands, output budget, and pre-submit blockers.

Capability gap reduced: Converts the 100-zone case from broad projection into a concrete reviewed package boundary.

Why this outranks alternatives: The 100-zone case is the nearest useful proxy for Swiss-scale single-AOI pressure, but should not be submitted until smaller measured steps justify it.

Inspect first:

- `scripts/run_balfrin_diagnostic.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- external: Balfrin queue and `$SCRATCH` capacity if package paths are materialized remotely

Deliverables:

- Materialize or plan a 100-zone diagnostic package with exact commands, expected runtime/storage/file-count bands, run-root paths on `$SCRATCH`, and pre-submit no-go conditions.

Definition of done:

- The package is ready for review or fails closed with a precise blocker; no 100-zone live submission occurs in this task.


### TB-612: Submit A 100-Zone Diagnostic Only If Prior Evidence Supports It

Goal: Run the 100-zone diagnostic on Balfrin only if the 32-zone and next larger diagnostic evidence show low risk.

Capability gap reduced: Provides a strong measured single-AOI pressure point toward Swiss-scale feasibility.

Why this outranks alternatives: A measured 100-zone diagnostic would materially strengthen or falsify the Swiss-scale performance story.

Inspect first:

- `scripts/run_balfrin_diagnostic.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- generated scratch: 100-zone diagnostic package from TB-611
- external: Balfrin `postproc` scheduler and `$SCRATCH`

Deliverables:

- Submit, monitor, and collect a 100-zone diagnostic only when prior measured diagnostics and current queue state keep expected use within standing clearance; otherwise record the measured no-go.

Definition of done:

- Either 100-zone evidence is measured, or the task records why the run should remain deferred.


### TB-613: Promote The Largest Diagnostic Series Into Swiss-Scale Feasibility

Goal: Update the Swiss-scale projection with the full measured diagnostic series through the largest safe run.

Capability gap reduced: Replaces extrapolated reducer-pressure bands with a measured curve.

Why this outranks alternatives: The final feasibility argument needs a measured series, not isolated diagnostics.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/swiss_scale_feasibility_projection.md`
- generated scratch: collected diagnostic run records from TB-599 through TB-612

Deliverables:

- Integrate the measured diagnostic series into runtime, memory, I/O, output, file-count, manifest, and next-blocker surfaces.

Definition of done:

- The Swiss-scale feasibility projection reports the measured series and a concrete remaining blocker instead of a single diagnostic ceiling.


### TB-614: Stage Source-Frequency Evidence For The Physical-Probability Blocker

Goal: Start closing the first scientific blocker by staging source-frequency evidence or a clearly labeled accepted-design placeholder.

Capability gap reduced: Moves physical-probability readiness beyond the current first blocker.

Why this outranks alternatives: The phase-change decision check ranks physical-probability evidence as the first scientifically useful action.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/validate_source_frequency_evidence.py`
- `validation/templates/source_frequency_evidence_v1.yaml`
- `docs/current_maturity_snapshot.md`
- external: any available public or local historical rockfall/source-frequency evidence for the selected sites

Deliverables:

- Create or validate a source-frequency evidence record with time window, censoring rules, provenance, uncertainty, and explicit non-production status if real evidence is not yet available.

Definition of done:

- The physical-probability readiness report either moves past `source_frequency_evidence` or names the exact external evidence still missing.


### TB-615: Stage Independent Holdout Runout Or Deposition Evidence

Goal: Acquire or stage holdout runout/deposition evidence that is independent of calibration and model selection.

Capability gap reduced: Reduces the validation-ready blocker for both physical probability and future operational claims.

Why this outranks alternatives: A scale demonstration is scientifically weak unless at least one independent holdout path is concrete.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/audit_chant_sura_holdout_split.py`
- `scripts/check_calibration_separation_preflight.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- Stage or validate a holdout evidence record with dataset/event/sample identifiers, split labels, provenance, and explicit calibration-separation status.

Definition of done:

- The validation/calibration evidence gap report identifies the next blocker after holdout evidence, or records the concrete missing field evidence.


### TB-616: Produce A Balfrin Swiss-Scale Demonstration Summary From Measured Runs

Goal: Summarize the measured Balfrin evidence into a concise demonstration of computational efficiency, performance, and feasibility boundaries.

Capability gap reduced: Turns the measured run series into a clear feasibility demonstration without overstating scientific or operational claims.

Why this outranks alternatives: Once the bounded runs and evidence promotion are complete, the repo needs a front-door summary of what was actually demonstrated.

Inspect first:

- `README.md`
- `docs/swiss_scale_feasibility_projection.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Update the user-facing summary with measured Balfrin runtime, memory, output, diagnostic/hazard-throughput, distributed/restart, and Swiss-scale feasibility boundaries.

Definition of done:

- The README or linked front-door doc accurately communicates the measured demonstration, remaining blockers, and claim boundaries in approachable language.

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
