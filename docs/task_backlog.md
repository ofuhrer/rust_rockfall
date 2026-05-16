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

### TB-095: Define Conditional Gridpoint Curve Pilot Product

Goal: Make the single-release-zone pilot's gridpoint conditional intensity-exceedance curve product explicit, auditable, and tied to GIS output layers.

Capability gap reduced: Hazard-map product interpretability.

Why this outranks alternatives: The user-facing goal is a hazard map with per-gridpoint intensity-frequency-like curves, but the current safe product is conditional exceedance curves without annual frequency.

Inspect first:

- `scripts/build_hazard_layers.py`
- `docs/hazard_layers.md`
- `docs/hazard_map_semantics.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `tests/test_hazard_layers.py`

Deliverables:

- A product summary or audit that identifies the per-gridpoint conditional curve schema, thresholds, units, denominator semantics, and corresponding GIS layers.
- Tests proving annual/physical-frequency fields remain absent or explicitly unsupported.
- Command-plan or diagnostic integration if needed to make the product discoverable for the Balfrin pilot.

Definition of done:

- The conditional curve product can be audited from existing outputs or fixtures, focused tests pass, and TB-095 is removed from this backlog.

Boundaries: Do not create annual frequency, return-period, risk, exposure, vulnerability, or operational semantics.

### TB-096: Plan Terrain-Driven Release-Zone Candidate Generation

Goal: Produce a deterministic dry-run release-zone candidate generator contract from public terrain and context inputs.

Capability gap reduced: Automated release-zone identification from public geodata.

Why this outranks alternatives: Swiss-wide automation cannot rely on hand-written release polygons; it needs a pragmatic reproducible heuristic before large ensembles can scale beyond Tschamut.

Inspect first:

- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A dry-run heuristic contract naming terrain derivatives, slope/roughness/corridor inputs, context exclusions, output geometry schema, and required provenance.
- Tests covering a blocked Chant Sura public-context path and a tiny synthetic AOI fixture.
- Clear labels separating candidate generation from validated release-zone evidence.

Definition of done:

- The heuristic contract emits JSON/text, focused tests pass, and TB-096 is removed from this backlog.

Boundaries: Do not generate production release zones, do not tune thresholds against Tschamut outcomes, and do not treat heuristic candidates as physical evidence.

### TB-097: Plan Pragmatic Block-Scenario Generation

Goal: Define a deterministic block-scenario generation dry run that maps release-zone candidates to a small, pragmatic scenario table.

Capability gap reduced: Automated scenario generation for reproducible conditional ensembles.

Why this outranks alternatives: Release zones alone do not produce a hazard map; the workflow needs a repeatable block/scenario plan whose uncertainty is explicit and bounded.

Inspect first:

- `scripts/plan_release_plan_dry_run.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A dry-run scenario-generation contract that names block-size bins, conditional sampling weights, release-cell linkage, required metadata, and unsupported physical-frequency fields.
- Tests proving Tschamut-specific heuristics are labelled separately from portable scenario semantics.
- A blocked path for missing source-zone or terrain evidence.

Definition of done:

- The scenario dry run emits JSON/text, focused tests pass, and TB-097 is removed from this backlog.

Boundaries: Do not estimate annual source frequencies, do not calibrate block distributions, and do not change current physics parameters.

### TB-098: Estimate Swiss-Wide Runtime And Storage Envelope

Goal: Convert the measured Tschamut/Balfrin pilot evidence into a conservative runtime and storage envelope for scaling to many Swiss AOIs.

Capability gap reduced: Swiss-wide execution feasibility planning.

Why this outranks alternatives: Before launching broader pilots, the repository needs a quantitative scaling estimate based on measured single-zone outputs and reduced-output mode.

Inspect first:

- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/run_performance_benchmark.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- A read-only projection helper that estimates runtime, storage, file counts, and job counts for configurable AOI/release-zone counts using measured coefficients.
- Tests for small, valley-scale, and Swiss-wide projection inputs.
- Explicit uncertainty bands and no-go labels when extrapolation exceeds measured evidence.

Definition of done:

- The projection helper emits JSON/text from measured inputs, focused tests pass, and TB-098 is removed from this backlog.

Boundaries: Do not claim Swiss-wide execution is authorized, do not submit jobs, and do not hide extrapolation uncertainty.

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
