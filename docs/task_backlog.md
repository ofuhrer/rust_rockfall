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

### TB-676: Close The Calibration Acceptance Criterion Gap

Goal: Turn the current calibration blocker into an executable acceptance criterion or a measured rejection.

Capability gap reduced: Scientific credibility for physical-probability and validation claims.

Why this outranks alternatives: The physical credibility summary already reports calibration evidence as the first remaining blocker.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/check_calibration_separation_preflight.py`
- `scripts/run_tschamut_calibration.py`
- `docs/calibration_holdout_evidence_tb658.md`
- `tests/test_validation_calibration_evidence_gaps.py`

Deliverables:

- A calibrated residual-quality threshold or review decision encoded in the existing evidence path, with focused tests and an updated physical-credibility summary.

Definition of done:

- Calibration evidence becomes accepted, explicitly rejected, or narrowed to one measured residual-quality failure.

Scope: Do not tune model parameters to pass the criterion unless the task records the before/after residuals and preserves holdout separation.

### TB-677: Run A Conditional Physical-Probability Prototype For One AOI

Goal: Produce a bounded physical-probability prototype for one AOI using accepted source-frequency, release-probability, block-population, and calibration evidence.

Capability gap reduced: Transition from conditional hazard layers toward scientifically interpretable physical probabilities.

Why this outranks alternatives: Swiss-scale feasibility needs a scientifically credible per-AOI probability path before multiplying the workflow across Switzerland.

Inspect first:

- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/validate_physical_frequency_reducer_preconditions.py`
- `scripts/validate_annual_physical_prototype_preflight.py`
- `docs/physical_frequency_reducer_preconditions.md`
- `tests/test_physical_frequency_reducer_preconditions.py`

Deliverables:

- A bounded one-AOI physical-probability prototype or fail-closed preflight, with all required evidence inputs named and the generated probability semantics separated from operational return-period claims.

Definition of done:

- The prototype either runs and produces a reviewable probability output or reports the exact missing evidence item preventing the run.

Scope: Keep operational, return-period, risk, exposure, vulnerability, and Swiss-wide claims out of scope.

### TB-678: Build A Swiss-Scale Demonstration Readiness Package From Measured Runs

Goal: Combine the latest Balfrin diagnostic, hazard-throughput, concurrency, restartability, chunk-smoke, and scientific-readiness results into one demonstration decision surface.

Capability gap reduced: Clear go/no-go basis for a Swiss-scale feasibility demonstration on Balfrin.

Why this outranks alternatives: After the measured pushes, the repo needs one concise surface that says what can be demonstrated now and what remains projection-only.

Inspect first:

- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A refreshed demonstration readiness package that names measured support points, projected Swiss-scale envelope, first missing input for a full Swiss-scale run, and the recommended next Balfrin demonstration command.

Definition of done:

- The package is generated from current measured outputs, focused tests pass, and the recommendation is concrete enough to execute or reject without adding more process artifacts.

Scope: Favor one concise generated/readable surface over new scattered documentation.

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
