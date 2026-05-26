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

### TB-595: Prototype Local Distributed-Orchestration Semantics

Goal: Exercise the distributed execution contract locally with deterministic fixture chunks and reducer replay.

Capability gap reduced: Provides a low-risk proof of orchestration semantics before any cluster distributed phase change.

Why this outranks alternatives: Local replay can catch split/merge/retry bugs before consuming scarce cluster resources.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/run_aoi_hazard_workflow.py`
- `scripts/build_hazard_layers.py`
- `tests/test_pilot_command_plan.py`
- `tests/test_hazard_layers.py`

Deliverables:

- Add a local fixture-backed distributed dry run that simulates multiple chunks, one retry, deterministic merge, and preservation of replay-critical outputs.
- Compare the merged output against the equivalent single-process fixture output.
- Record limitations that still block real distributed execution.

Definition of done:

- Focused local orchestration tests pass and the output names the remaining cluster-side blockers.


### TB-596: Quantify Swiss-Wide Data And Execution Inputs Needed For A Phase Change

Goal: Replace the Swiss-wide target with a quantified input, compute, storage, validation, and review readiness matrix.

Capability gap reduced: Makes Swiss-wide feasibility depend on explicit measured requirements rather than a broad “out of reach” label.

Why this outranks alternatives: Swiss-wide work requires both scale evidence and national data readiness; this task defines the actual gap.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_large_scale_execution_probe.py`

Deliverables:

- Extend the feasibility projection with national DEM/context data volume, tiling, chunk count, output footprint, validation evidence, and review checks.
- Distinguish compute-feasible, data-ready, validation-ready, and operational-ready classes.
- Add tests proving Swiss-wide remains currently deferred unless all classes are satisfied.

Definition of done:

- Focused projection tests pass and the Swiss-wide blocker is decomposed into measurable next steps.


### TB-597: Create A Readiness Roadmap And Decision Check

Goal: Combine operational, physical-probability, Swiss-wide, non-postproc, and distributed readiness into one phase-change decision check.

Capability gap reduced: Replaces scattered prose with one ranked roadmap for future evidence work.

Why this outranks alternatives: After individual readiness checks exist, the project needs one decision surface that says which evidence gap is most useful to close next.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/decision_log.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`

Deliverables:

- Add a phase-change decision report that evaluates each readiness class independently.
- Produce a ranked next-action list for the first scientifically useful evidence upgrade.
- Link the decision surface from the maturity snapshot without changing current output labels.

Definition of done:

- Focused decision/gap tests pass and each readiness class has a concrete next task or an explicit deferral reason.


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
