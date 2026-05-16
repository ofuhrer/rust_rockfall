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

## Active Tasks

_Active TB tasks remain below._

### TB-099: Add Balfrin Pilot Post-Run Interpretation Gate

Goal: Define the post-run gate that decides whether the Balfrin single-release-zone pilot is usable as a conditional diagnostic artifact.

Capability gap reduced: Pilot closure readiness and scientific interpretation.

Why this outranks alternatives: A large run is only useful if the repository already knows how to interpret success, instability, output pressure, and GIS product readiness.

Inspect first:

- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/audit_gis_cog_package_readiness.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- A post-run gate summary for the Balfrin pilot that names required readiness, convergence/stability, output, GIS/COG, and physical-credibility checks.
- Tests for measured, blocked, and inconclusive post-run states.
- Documentation that the gate can accept a conditional diagnostic artifact without operational or physical-probability claims.

Definition of done:

- The post-run gate emits JSON/text, focused tests pass, and TB-099 is removed from this backlog.

Boundaries: Do not change current closure criteria, do not reclassify existing Tschamut evidence without new artifacts, and do not authorize operational use.

### TB-100: Refill Maturity Snapshot For The Balfrin Pilot Track

Goal: Update the compact maturity snapshot and command-context guidance so future workers see the Balfrin single-release-zone pilot track as the current execution focus.

Capability gap reduced: Worker orientation for the next execution phase.

Why this outranks alternatives: After the pilot contract, case plan, submission package, metrics contract, and post-run gate exist, the repo needs a concise source of truth to prevent workers from reverting to earlier same-scale-only assumptions.

Inspect first:

- `docs/current_maturity_snapshot.md`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/task_backlog.md`
- `scripts/print_agent_task_context.py`
- `docs/agent_work_log.md`

Deliverables:

- A compact maturity update that distinguishes completed dry-run automation from the remaining Balfrin execution gap.
- Task-context helper adjustments only if future active tasks are not discoverable from compact context.
- No new roadmap beyond the next measurable execution phase.

Definition of done:

- The snapshot reflects the new Balfrin pilot track, focused checks pass, and TB-100 is removed from this backlog.

Boundaries: Documentation/helper context only; do not add new scientific claims, run simulations, or alter backlog protocol.

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

- Focused checks pass and the task is removed from this backlog.

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
  contract, submission package, metrics contract, and post-run interpretation
  gate are in place.
- helper consolidation beyond the task-context bootstrap until duplicated
  parsing becomes a demonstrated implementation bottleneck.
