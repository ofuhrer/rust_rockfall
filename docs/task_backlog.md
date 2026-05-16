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

### TB-069: Generate Canonical Conditional Diagnostic Interpretation Artifact

Goal: TB-051 created an interpretation helper, but the repo still needs a durable generated artifact path suitable for downstream reviews and release notes. Reduces: interpretability fragmentation and pilot closure ambiguity.

Inspect first:

- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`
- `docs/tschamut_public_bounded_validation_output_profile.md`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- one canonical measured pilot interpretation artifact combining uncertainty, convergence, closure status, runtime/output limits, GIS readiness, context limitations, and physical credibility boundaries;
- JSON/text output path suitable for future synthesis tooling, without committing large generated artifacts;
- docs point to the artifact/helper as the primary synthesis entrypoint.

Definition of done:

- canonical interpretation helper emits deterministic synthesis output to an explicit path when requested;
- interpretation clearly distinguishes workflow credibility, physical credibility, and operational non-readiness;
- focused tests cover the artifact-writing path and blocked/missing-input behavior.

Boundaries: no operational semantics, no reclassification unless directly
supported by measured evidence, no physical validation claims.

### TB-070: Quantify Spatial Uncertainty Hotspot Persistence Across Seeds

Goal: uncertainty hotspots are spatially identified, but persistence across the existing gate/target/probe artifacts is not yet quantified directly. Reduces: uncertainty interpretation ambiguity.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_same_scale_sampling_uncertainty.py`
- `validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/`
- `validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full/`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- hotspot persistence summary across gate, target, sampling probe v1, and sampling probe v2;
- persistence metrics for `max_kinetic_energy`, `max_jump_height`, and velocity exceedance layers;
- optional ignored persistence masks or hotspot overlays.

Definition of done:

- helper emits deterministic persistence metrics from existing artifacts;
- docs state whether uncertainty hotspots are spatially stable or transient across seeds/probes;
- tests validate hotspot aggregation logic with small fixtures.

Boundaries: no new ensemble runs, no tuning, no operational claims.

### TB-071: Define Physical-Credibility Claim Boundaries Per Product Layer

Goal: physical credibility is globally not established, but the repo does not yet distinguish credibility limitations per hazard/intensity product layer. Reduces: scientific ambiguity and future overclaim risk.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `docs/validation_maturity_framework.md`
- `docs/hazard_layers.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`

Deliverables:

- per-layer physical-credibility boundary assessment for reach probability, deposition density, max kinetic energy, max jump height, and exceedance layers;
- explicit distinction between diagnostic usefulness, reproducibility, physical credibility, and operational inadmissibility;
- evidence classes needed to strengthen each layer’s claim boundary.

Definition of done:

- helper emits deterministic layer-level credibility summaries;
- docs explain which layers are most scientifically fragile and why;
- no product is reclassified as physically validated.

Boundaries: no calibration, no tuning, no operational claims, no
annual-frequency semantics.

### TB-072: Stage First Real Chant Sura Public-Context Acquisition Plan

Goal: Chant Sura portability remains synthetic/context-deferred, and the next realism step is a concrete dry-run acquisition plan for actual public-context products. Reduces: Swiss-wide portability uncertainty.

Inspect first:

- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `docs/public_real_site_geodata_preparation.md`
- `docs/swisstopo_data_strategy.md`
- `tests/fixtures/second_site_public_geodata_preflight/`

Deliverables:

- explicit acquisition/staging plan for SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D;
- exact expected staging roots and metadata contracts;
- deterministic dry-run acquisition summary without downloads.

Definition of done:

- second-site preflight reports a concrete acquisition path while still marking unstaged public context as deferred;
- no public geodata is downloaded or committed;
- docs distinguish synthetic staging from real-context readiness.

Boundaries: no second-site ensemble, no hazard build, no downloads, no
operational claims.

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
