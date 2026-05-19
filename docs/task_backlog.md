# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.
Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

Capability filter: a task whose main deliverable is a report, gate, validator,
YAML record, checklist, or evidence package is acceptable only when it names the
specific command it unblocks, measurement it produces, workflow coupling it
removes, or stale surface it replaces. Otherwise the task should be rewritten as
bounded execution, recovery, automation, scaling measurement, real-evidence
acquisition, or consolidation of an existing helper.

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

Live Balfrin rule: the user has granted standing clearance for GPT-5.5 workers
to submit and actively monitor jobs on Balfrin's `postproc` partition. Multiple
concurrent `postproc` jobs are allowed, including filling the partition. If the
work would keep the `postproc` partition fully busy for more than 6 hours, stop
and rediscuss. Submission still requires the relevant access, readiness,
authorization-record/audit, output-budget, preservation, and evidence gates to
pass. This clearance does not authorize non-postproc partitions, distributed
execution, scale-up claims, or scientific/operational claim upgrades.

## Active Tasks

### TB-316: Swisstopo Public Data Acquisition Driver

Goal: Add an explicit opt-in public-data acquisition driver that can fetch or stage required swisstopo products for a user-defined AOI while preserving license, source, checksum, CRS, and provenance records.

Capability gap reduced: User-defined AOI workflows still depend on manually downloaded or pre-staged public geodata.

Why this outranks alternatives: The biggest user friction after AOI definition is getting required terrain/context inputs into the verified cache manifest.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/stage_public_geodata_cache.py`
- `scripts/verify_public_geodata_cache.py`
- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_swisstopo_aoi_acquisition_planner.py`
- `tests/test_public_geodata_cache_stager.py`

Deliverables:

- An opt-in acquisition driver with dry-run, local-copy, and download-enabled modes, defaulting to no network mutation unless the user explicitly passes a download/apply flag.
- Cache-manifest updates with source URL or delivery record, product version/date, tile id, raw checksum, processed checksum, CRS, resolution, extent, license reference, and preprocessing timestamp.
- Tests for dry-run, local-copy, blocked missing URL, checksum mismatch, and no-hidden-download behavior.

Definition of done:

- A user-defined AOI can move from resolved product rows to verified local cache inputs through a documented, auditable acquisition command.

Boundaries: Public geodata acquisition/staging only; no private data, no simulation, no live Balfrin submission, no operational claim, no physical validation claim, and no large swisstopo products committed.

### TB-317: User-Defined AOI End-To-End Local Demonstration

Goal: Demonstrate a new small user-defined AOI path from bounds through verified inputs, prepared pilot, local execution, map package, and QA review using the guided frontend.

Capability gap reduced: The AOI path is currently strongest on fixtures and known sites; the project needs a user-defined region demonstration that exercises the frontend.

Why this outranks alternatives: A project goal demonstration should show the workflow from user AOI definition to hazard map, not only internal helper interoperability.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/bootstrap_aoi_manifest.py`
- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_golden_fixture_package.py`

Deliverables:

- A bounded local demonstration for one small user-defined AOI using verified fixture or staged public inputs, reduced-output local execution, map packaging, and static QA review.
- A reproducible command transcript or test that proves the same path works from a clean checkout plus allowed fixture/staged inputs.
- Explicit non-operational, conditional-only, and no-annual-frequency labels in the generated package and docs.

Definition of done:

- The repo can show a user-facing AOI-to-review-map demonstration that starts from AOI definition and ends with an openable diagnostic hazard-map package.

Boundaries: Local bounded demonstration only; no live Balfrin submission, no Swiss-wide claim, no physical-probability semantics, no annual-frequency product, no risk/exposure/vulnerability claim, and no operational claim.

### TB-318: AOI Frontend Review Surface Polish

Goal: Improve the generated AOI review surface so users can inspect layers, warnings, provenance, and next actions without reading raw JSON manifests.

Capability gap reduced: The map package is reviewable, but the user-facing frontend is still mainly a static diagnostic bundle rather than a clear map workflow surface.

Why this outranks alternatives: The project goal includes producing a hazard map for a region; the review surface is the user's primary artifact.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/hazard_map_semantics.md`
- `docs/public_real_site_geodata_preparation.md`
- `tests/test_aoi_hazard_map_packager.py`
- `tests/test_aoi_map_qa_review.py`

Deliverables:

- A clearer static review page with layer inventory, legend, conditional semantics, warnings, provenance, observed-overlay status, first blocker, and next recommended command.
- Tests for missing layers, COG-blocked outputs, observed-evidence overlays, conditional-only labels, and non-operational warnings.
- Documentation update that points users to the generated review surface as the primary local output.

Definition of done:

- A user can open the generated review surface and understand what was produced, what is missing, and what the map is allowed to mean.

Boundaries: Frontend/review surface only; no hazard-value changes, no live Balfrin submission, no operational claim, no annual/physical/risk semantics, and no heavy outputs committed.

### TB-319: Post-Demonstration Capability And Gap Refresh

Goal: Refresh the maturity snapshot, README, scale dashboard, and backlog recommendations after the next Balfrin and user-AOI demonstration tasks complete.

Capability gap reduced: Once measured scale and frontend evidence changes, the repository needs one authoritative synthesis that prevents workers from following stale blocked paths.

Why this outranks alternatives: This should come after new measurements and user-facing demonstrations, not before them.

Inspect first:

- `README.md`
- `docs/current_maturity_snapshot.md`
- `docs/balfrin_probe_slurm_driver.md`
- `docs/multi_zone_reducer_pressure_probe.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `scripts/print_agent_task_context.py`

Deliverables:

- Updated status docs and task-context summaries reflecting measured Balfrin runs, output/efficiency status, user-AOI frontend capability, and remaining scientific boundaries.
- Removal or correction of stale blockers that have been superseded by measured evidence, while preserving failed-closed branches as history.
- A short next-backlog recommendation list that favors execution, acquisition, optimization, or explicit deferral over further synthesis.

Definition of done:

- The repository tells one current story about scale, Balfrin readiness, user-defined AOI workflow, and remaining gaps after the new evidence lands.

Boundaries: Synthesis after evidence changes only; no live Balfrin submission, no new run, no claim upgrade beyond measured capability, no annual/physical/risk semantics, and no operational claim.

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
  mainly a report, gate, validator, checklist, or package, state the exact run,
  recovery, acquisition, reproducibility, or consolidation action it enables.

Definition of done:

- Focused checks pass, the capability outcome is explicit, and the task is
  removed from this backlog only when the definition of done is genuinely met.
  A new blocked/deferred classification is not enough unless it eliminates a
  real ambiguity and names the next unblock action or explicit deferral.

Boundaries: No tuning, operational claims, scale-up authorization, non-postproc
Balfrin submission, distributed execution, or other phase changes unless the
task explicitly allows them. Postproc Balfrin submissions are covered by the
standing live Balfrin rule above and still require GPT-5.5 routing, active
monitoring, and passing repository gates.
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
