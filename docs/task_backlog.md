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

### TB-630: Add A Spatial Holdout Metric For Runout Evidence

Goal: Strengthen holdout validation by adding a spatial metric beyond simple presence/intake of observed runout/deposition evidence.

Capability gap reduced: Scientific credibility of validation, especially whether simulated outputs are spatially meaningful against held-out evidence.

Why this outranks alternatives: Holdout evidence is now staged, but credibility needs a quantitative spatial comparison rather than only intake status.

Inspect first:

- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/compare_hazard_map_convergence.py`
- `scripts/generate_aoi_map_qa_review.py`
- `validation/data/processed/observed_runout_deposition_benchmark/observed_runout_deposition.geojson`
- `docs/holdout_runout_deposition_evidence_tb615.md`

Deliverables:

- A small spatial-overlap, distance, or coverage metric computed for held-out runout/deposition evidence and wired into the validation summary path.

Definition of done:

- The metric runs on existing data, distinguishes holdout from calibration inputs, and reports a numeric result or a concrete geometry/data blocker.

### TB-631: Measure GIS/COG Output Packaging At Larger Hazard Size

Goal: Verify that the larger hazard output remains practical to package for GIS review without ballooning file count or conversion time.

Capability gap reduced: Feasibility of user-facing map review after larger Balfrin hazard runs.

Why this outranks alternatives: Runtime evidence is incomplete if the resulting map package cannot be reviewed efficiently.

Inspect first:

- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/large_aoi_gis_cog_stress_tb609.md`
- `docs/hazard_layers.md`

Deliverables:

- A measured GIS/COG packaging result for the largest available hazard output root, including conversion time, raster count, byte count, and parity status.

Definition of done:

- Packaging completes or fails with a concrete output-family blocker, and the result is tied to the scale-readiness interpretation.

### TB-632: Simplify Obsolete Balfrin Evidence Surfaces

Goal: Remove or consolidate old Balfrin documents that are superseded by current scale summaries while preserving measured run facts.

Capability gap reduced: Repository clarity and user-facing navigability after many task-specific Balfrin reports.

Why this outranks alternatives: The repo has grown many narrow reports, and simplifying them makes the actual execution path and current evidence easier to find.

Inspect first:

- `docs/README.md`
- `docs/agent_work_log.md`
- `docs/swiss_scale_feasibility_projection.md`
- `docs/balfrin_scale_demonstration_management_package.md`
- `docs/balfrin_diagnostic_series_tb613.md`
- `scripts/check_repo_consistency.py`

Deliverables:

- A safe documentation prune or consolidation that removes superseded Balfrin report files from the docs index and keeps durable measured facts in summary surfaces.

Definition of done:

- Repo consistency checks pass, no active references point to deleted docs, and the docs front door is shorter or clearer than before.
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
