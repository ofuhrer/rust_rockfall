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

### TB-475: Add A Rust Real-Terrain Golden Trajectory Test

Goal: Add a small Rust-level regression test that exercises terrain-driven trajectory behavior on a committed real-terrain fixture.

Capability gap reduced: Gives the simulation core a meaningful terrain regression that can catch physical or numerical regressions without Python workflow indirection.

Why this outranks alternatives: Core model regressions should be caught in Rust close to the dynamics and terrain code, especially before expanding AOI workflows.

Inspect first:

- `src/simulation.rs`
- `src/terrain.rs`
- `tests/terrain_edge_cases.rs`
- `data/processed/tschamut2014/terrain.asc`

Deliverables:

- Add a Rust test using a small existing terrain fixture and deterministic release state.
- Assert physically meaningful invariants such as finite samples, nonnegative energy, bounded jump height, plausible stop behavior, and no terrain lookup failure.

Definition of done:

- `cargo test` or the focused Rust test target passes, the test fails on obvious invalid terrain/trajectory behavior, and no Python script, contract, or administrative document is added.

Boundaries: No tuning, no validation claim upgrade, no operational claim, no Balfrin submission, and no broad model rewrite unless required by the failing test.

### TB-476: Reduce Extreme-Layer Instability In The Rust Model

Goal: Investigate and reduce the instability behind `max_kinetic_energy` and `max_jump_height` using model or numerical changes rather than additional reporting.

Capability gap reduced: Improves the most fragile current hazard-layer families.

Why this outranks alternatives: Recent local evidence ranks these layers as the least stable scientific surfaces, and they directly affect hazard-map interpretability.

Inspect first:

- `src/dynamics.rs`
- `src/integrator.rs`
- `src/simulation.rs`
- `scripts/summarize_extreme_layer_sensitivity_smoke.py`

Deliverables:

- Identify one concrete model/numerical cause of avoidable extreme-layer sensitivity.
- Implement the smallest Rust change that improves boundedness, interpolation, contact handling, energy accounting, or sampling stability.
- Re-run the existing extreme-layer sensitivity smoke and relevant Rust tests to compare before/after behavior.

Definition of done:

- Focused checks pass, the measured extreme-layer sensitivity is no worse and at least one instability metric improves or the attempted model change is reverted with a smaller executable follow-up left in the backlog.

Boundaries: No parameter tuning to fit outputs, no new audit/report script, no physical-credibility upgrade claim, no operational claim, no Balfrin submission, and no annual-frequency semantics.

### TB-477: Run Multi-Release-Zone Hazard Accumulation Locally

Goal: Execute a small multi-release-zone local hazard accumulation run and aggregate outputs into combined conditional layers.

Capability gap reduced: Moves from single-zone demonstrations toward practical AOI hazard-map generation.

Why this outranks alternatives: Real hazard products need multiple source areas; local multi-zone execution finds aggregation and output issues before larger HPC work.

Inspect first:

- `scripts/hazard_accumulation_benchmark.py`
- `scripts/build_hazard_layers.py`
- `tests/fixtures/aoi_scenario_preview/multi_zone_review_package_a.yaml`
- `tests/fixtures/hazard/ensemble_case.yaml`

Deliverables:

- Run or adapt existing multi-zone fixture/input paths to produce combined conditional hazard layers locally.
- Measure runtime, trajectory count, layer count, and output size from the run.

Definition of done:

- The multi-zone local run produces combined hazard layers, focused hazard accumulation tests pass, and the task is removed only after the measured output summary is recorded in the work log.

Boundaries: No new orchestration scripts, no Balfrin submission, no scale-up authorization, no annualized probability, no operational claim, and no risk/exposure/vulnerability output.

### TB-478: Compare Simulated Runout Against One Observed Fixture

Goal: Compare one existing simulated runout/deposition output against an observed runout or deposition fixture using existing validation machinery.

Capability gap reduced: Connects model output to observed evidence instead of only internal consistency.

Why this outranks alternatives: A direct observed-vs-simulated comparison is the shortest path from technical workflow progress toward scientific credibility.

Inspect first:

- `validation/data/processed/tschamut/observed_deposition.csv`
- `validation/data/processed/chant_sura_2020/observed_trajectories_contact.csv`
- `src/validation.rs`
- `validation/cases/validation_tschamut_baseline.yaml`

Deliverables:

- Run an existing validation case or make the smallest code/test adjustment needed to compute a clear observed-vs-simulated runout/deposition comparison.
- Record the measured agreement metric and the main model discrepancy exposed by the comparison.

Definition of done:

- The comparison is executable locally, focused validation tests pass, the result is documented in the work log, and no new standalone report/checker script is added.

Boundaries: No calibration, no parameter tuning, no external validation claim upgrade, no operational claim, no annual-frequency or physical-probability semantics, and no Balfrin submission.

### TB-479: Improve Release-Zone Generation On Real Terrain

Goal: Make existing terrain-based release-zone generation produce reviewable candidate zones on a real local AOI.

Capability gap reduced: Reduces dependence on hand-authored or synthetic source-zone fixtures.

Why this outranks alternatives: Real AOI hazard mapping cannot scale until candidate release zones are useful enough for human review.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `src/geodata.rs`
- `qgis/styles/candidate_source_zone.qml`

Deliverables:

- Use existing release-zone candidate code on a real local terrain input and improve the underlying selection or output shape if the candidates are empty, implausible, or hard to review.
- Produce a candidate release-zone layer that loads with the existing QGIS style.

Definition of done:

- The candidate generation command produces non-empty, spatially plausible candidates for the selected AOI, focused release-zone tests pass, and no new planning/admin script is added.

Boundaries: Human-review candidates only; no final source-zone interpretation, no tuning against outcomes, no operational claim, no Balfrin submission, and no scale-up claim.

### TB-480: Make QGIS Hazard Outputs Immediately Reviewable

Goal: Improve the generated hazard package contents so a reviewer can open the layers in QGIS with clear names, CRS, styles, and legends.

Capability gap reduced: Turns hazard outputs into practical review products instead of raw files that require internal knowledge.

Why this outranks alternatives: Scientific outputs need fast visual inspection; poor GIS packaging slows every real AOI iteration.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/hazard_output_writers.py`
- `qgis/styles/aoi_qgis_style_bundle.json`
- `tests/test_aoi_hazard_map_packager.py`

Deliverables:

- Improve existing package-writing code or style references so generated AOI packages include clear layer names, CRS metadata, style links, and review-ready ordering.
- Verify the improvement against an existing package fixture or a freshly generated local AOI package.

Definition of done:

- Focused package tests pass, one generated package contains review-ready metadata/style references, and the work does not add a new connector, contract, or administrative layer.

Boundaries: Packaging and usability only; no operational-map claim, no new QGIS plugin, no risk/exposure/vulnerability content, no Balfrin submission, and no annualized semantics.

### TB-481: Profile And Optimize One Local Ensemble Hotspot

Goal: Reduce runtime or memory for one actual local ensemble or hazard-layer run by profiling and optimizing the dominant hotspot.

Capability gap reduced: Improves the practical path from local development to larger AOI ensembles.

Why this outranks alternatives: Scaling progress should come from measured runtime or memory bottlenecks, not from more orchestration.

Inspect first:

- `src/simulation.rs`
- `src/terrain.rs`
- `scripts/hazard_accumulation_benchmark.py`
- `validation/cases/performance_smoke.yaml`

Deliverables:

- Profile an existing local ensemble or performance smoke run.
- Implement one targeted Rust or existing workflow-code optimization.
- Record before/after runtime or memory on the same input.

Definition of done:

- The optimized path preserves test results, shows a measured runtime or memory improvement on the selected local case, and avoids adding new benchmark/admin scripts unless an existing benchmark entry is extended.

Boundaries: No scale-up claim beyond the measured local case, no Balfrin submission, no distributed execution, no output semantics change, and no broad refactor without measured need.

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
