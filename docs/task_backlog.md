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
