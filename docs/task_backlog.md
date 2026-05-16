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
