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

### TB-088: Define Minimal Swiss Public-Geodata Workflow Contract

Goal: Specify the reusable public-geodata contract needed for any Swiss AOI before site-specific preprocessing, release planning, or hazard generation can proceed.

Capability gap reduced: Swiss-wide portability realism.

Why this outranks alternatives: Current second-site work is Chant Sura-specific; a minimal contract prevents new locations from inheriting Tschamut or Chant Sura assumptions.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A reusable contract summary for required AOI metadata, CRS/grid assumptions, swisstopo product classes, cache paths, provenance, and deferred optional context.
- Tests cover at least the existing Chant Sura fixture and a minimal synthetic AOI fixture.
- Docs distinguish public-geodata contract readiness from synthetic fixture readiness.

Definition of done:

- The contract can be emitted as JSON/text, focused tests pass, and TB-088 is removed from this backlog.

Boundaries: Do not download public data, stage fake public-context evidence, or run a second-site hazard build.

### TB-089: Add AOI-To-Prepared-Pilot Dry-Run Orchestrator

Goal: Chain existing AOI acquisition, public-context gate, release-zone dry-run, release-plan dry-run, and command-plan helpers into one dry-run workflow report.

Capability gap reduced: Workflow automation from user AOI toward prepared conditional pilot inputs.

Why this outranks alternatives: It reduces manual orchestration across already-existing helpers without pretending the missing downloads or evidence exist.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/plan_release_plan_dry_run.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A dry-run orchestrator or command-plan group that reports ordered steps, blockers, expected inputs, and generated/ignored output roots for a candidate AOI.
- The report remains blocked/deferred when real public-context products are missing.
- Tests prove the dry run does not download data or run ensembles.

Definition of done:

- One command produces a deterministic AOI-to-prepared-pilot dry-run report for Chant Sura, focused tests pass, and TB-089 is removed from this backlog.

Boundaries: No data downloads, no second-site ensemble, no hazard build, no operational or physical-probability claim.

### TB-090: Generate Second-Site Conditional Case Skeleton

Goal: Produce a blocked, inspectable second-site case skeleton from the current Chant Sura contract without authorizing execution.

Capability gap reduced: Portable multi-site workflow realism and reproducibility.

Why this outranks alternatives: A case skeleton exposes exactly which real public-context and source/scenario fields remain missing before any second-site run can be valid.

Inspect first:

- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A dry-run case skeleton generator or command-plan step that emits a non-executable case draft to a temporary/ignored location.
- The skeleton clearly marks synthetic fixture fields, deferred public-context fields, and execution blockers.
- Tests verify the skeleton cannot be mistaken for an authorized run case.

Definition of done:

- The skeleton is generated and audited in dry-run mode, focused tests pass, and TB-090 is removed from this backlog.

Boundaries: Do not run validation or hazard generation for Chant Sura, do not claim public-context readiness, and do not commit generated private artifacts.

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
- distributed SLURM orchestration unless later evidence shows a measured need.
- shared typed evidence-reader refactors unless at least one more executable
  diagnostic exposes duplicated parsing as the implementation bottleneck.
- larger selected-domain or production ensembles until closure criteria,
  rebuildable reduced outputs, and current same-scale uncertainty blockers are
  addressed.
- helper consolidation beyond the task-context bootstrap until duplicated
  parsing becomes a demonstrated implementation bottleneck.
