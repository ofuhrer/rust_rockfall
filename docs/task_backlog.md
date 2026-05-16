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

### TB-076: Define Conditional Gridpoint Curve Product Contract

Goal: Specify and exercise the conditional gridpoint intensity-exceedance curve
contract that current hazard maps can support without annual frequency claims.

Inspect first:

- `scripts/build_hazard_layers.py`
- `docs/hazard_layers.md`
- `docs/hazard_map_semantics.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `tests/test_hazard_layers.py`

Deliverables:

- A small machine-readable contract or helper report describing per-gridpoint
  conditional exceedance curves, their threshold units, normalization scope,
  and unsupported physical-frequency fields.
- A tiny fixture or existing-output summary proving the curve schema can be
  emitted or audited without new simulations.
- Documentation that cleanly separates conditional exceedance curves from
  physical intensity-frequency curves.

Definition of done:

- A focused test validates the conditional curve contract shape.
- The report/docs state that annual or physical frequency remains unsupported.

Boundaries: Do not implement annual-frequency modelling, return periods,
  source occurrence rates, risk, exposure, vulnerability, or operational use.

### TB-077: Prototype AOI-To-Release-Zone Heuristic Dry Run

Goal: Start closing the automation gap between "user provides a region" and a
candidate release-zone set by defining a deterministic, fixture-backed heuristic
dry run.

Inspect first:

- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A dry-run helper or report that accepts an AOI/site config and emits candidate
  release-zone heuristic requirements, inputs, and blocked/missing products.
- A tiny fixture-backed example that does not claim the synthetic candidate is a
  real public-geodata release-zone interpretation.
- Documentation of heuristic assumptions and missing terrain/context
  prerequisites for a real site.

Definition of done:

- The dry run produces deterministic JSON/text output for the Chant Sura fixture
  and reports `deferred_public_context_inputs` where real context is absent.

Boundaries: Do not download public data, run a second-site ensemble, tune
  release-zone physics, or treat synthetic fixtures as field evidence.

### TB-078: Generate Pragmatic Release-Plan Dry Run

Goal: Define how a portable source-zone candidate becomes deterministic release
and block-scenario rows before any new ensemble is run.

Inspect first:

- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/generate_pilot_command_plan.py`
- `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A fixture-backed release-plan dry run that emits deterministic release counts,
  seed policy, block-scenario classes, and site-specific fields for a candidate
  source-zone record.
- A machine-readable distinction between reusable semantics, site-specific
  inputs, and Tschamut-only heuristics.
- A command-plan entry that remains blocked/template-only for real second-site
  execution until public context is present.

Definition of done:

- Focused tests verify deterministic dry-run output and that no second-site
  simulation command is authorized.

Boundaries: Do not create a production release plan, tune parameters, run
  ensembles, or authorize scale-up.

### TB-079: Add Chant Sura Real-Context Readiness Gate Artifact

Goal: Move Chant Sura from synthetic core-input staging toward real
public-context readiness by adding an explicit gate artifact for acquisition
decisions.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- A readiness-gate report that compares the deterministic acquisition plan,
  local staged files, and deferred public-context products for Chant Sura.
- Concrete next acquisition decisions for SWISSIMAGE, swissTLM3D,
  swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D without
  downloading them.
- A clear indication that synthetic core inputs are not public-context evidence.

Definition of done:

- The gate report has JSON/text output and tests covering ready core inputs plus
  deferred real-context products.

Boundaries: Do not perform downloads, run second-site hazard maps, or claim
  second-site validation/calibration readiness.

### TB-080: Define Observed Runout And Deposition Validation Intake Contract

Goal: Turn the physical-credibility evidence map into a concrete future data
intake contract for observed runout/deposition evidence.

Inspect first:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/summarize_chant_sura_holdout_evidence.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A minimal schema/report for observed runout/deposition benchmark intake,
  including geometry, event/source metadata, uncertainty fields, and objective
  function placeholders.
- Explicit mapping from each field to the physical-credibility requirement it
  would satisfy.
- A blocked/current-state report showing that no such calibration dataset is
  currently available in the repo.

Definition of done:

- Focused tests validate the intake contract and current blocked status.
- Documentation states that calibration, physical probability, and operational
  claims remain unsupported until real evidence is acquired.

Boundaries: Do not fabricate validation data, fit parameters, change closure
  status, or introduce annual-frequency/risk/exposure/vulnerability semantics.

## Backlog Protocol

Task headings must always be exactly:

```markdown
### TB-XXX: Short Description
```

Do not put priority, status, owner, or tags in the heading. Use this schema for
every active task:

```markdown
### TB-XXX: Short Description

Goal: One sentence describing why the task matters and what gap it reduces.

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
