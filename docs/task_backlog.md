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

### TB-645: Add A Swiss National Data Inventory Smoke

Goal: Check whether the existing national tiling and data-inventory surfaces can produce a current, small, share-safe planning summary.

Capability gap reduced: Swiss-wide data readiness.

Why this outranks alternatives: Swiss-wide execution is deferred partly because national public-geodata inventory and tiling readiness are not current run evidence.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/swiss_national_tiling_inventory_tb607.md`
- `docs/swiss_national_tile_chunk_mapping_tb608.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A refreshed local national data/tiling inventory summary or exact missing-input blocker.

Definition of done:

- The result reports tile count, estimated bytes, chunk count, missing products, and whether the current inventory is sufficient for planning only.

### TB-646: Exercise A Small Chunked AOI Processing Prototype

Goal: Test whether the current AOI workflow can process multiple chunks and merge reviewable outputs without introducing distributed execution claims.

Capability gap reduced: Path toward regional/Swiss-scale chunking.

Why this outranks alternatives: Distributed execution is deferred, but a local chunk-and-merge prototype can expose merge and packaging issues before scheduler work.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A local scratch chunked AOI smoke or a concrete blocker for chunked hazard-layer merge/package behavior.

Definition of done:

- The prototype writes scratch outputs only, reports per-chunk and merged file/byte counts, and explicitly remains local non-distributed evidence.

### TB-647: Add Operational QA Checklist To Existing Map Package Output

Goal: Make GIS package review more actionable by surfacing visual QA items and provenance fields inside the existing package output.

Capability gap reduced: Operational-readiness preparation without claiming operational use.

Why this outranks alternatives: Packaging is now technically ready, so the next review gap is whether a human can systematically inspect the result.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/pilot_gis_package.md`
- `docs/hazard_map_semantics.md`

Deliverables:

- A concise QA section in the generated AOI package/review output covering layer presence, CRS, nodata, style availability, and evidence/claim boundaries.

Definition of done:

- Existing package tests pass, generated package output includes the QA checklist, and accepted-for-operational-use remains false by default.

### TB-648: Remove Or Merge Remaining Superseded Docs From The Docs Index

Goal: Continue reducing repository documentation weight after the Balfrin diagnostic-doc consolidation.

Capability gap reduced: Repository navigability and lower maintenance drag.

Why this outranks alternatives: Simplification remains valuable only if it removes stale surfaces while preserving current measured facts.

Inspect first:

- `docs/README.md`
- `docs/project_overview.md`
- `docs/current_maturity_snapshot.md`
- `scripts/check_repo_consistency.py`

Deliverables:

- A safe prune or merge of additional superseded top-level docs, with active references updated to current summary surfaces.

Definition of done:

- `docs/README.md` is shorter or clearer, no active references point at deleted docs, and repository consistency checks pass.

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
