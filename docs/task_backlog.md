# Task Backlog

Status: authoritative executable task backlog.

This file is the only maintained queue of implementation tasks. It is written
for worker agents, including smaller GPT-5.4-Mini-style agents, so each task
must be small enough for focused execution and must name the concrete
capability, analysis, run, or validation outcome it enables.

Worker rule: when a task is completed successfully and committed, remove that
task from this backlog. Add at most one follow-up task if the completed work
uncovers a concrete next blocker. Record durable choices in `decision_log.md`
and completed work in `agent_work_log.md`.

Progress rule: backlog tasks must normally produce executable or measured
progress, not only procedural artifacts. Acceptable real progress includes an
implemented simulator or workflow feature, an executable analysis script, a
validation run with measured results, a comparison against reference or field
data, a reproducibility improvement that enables validation, a performance
improvement that enables larger validation, or a tested bug fix.

Non-sufficient outputs by themselves: documentation-only gates, YAML
record-only changes, validator-only changes, roadmap-status transitions,
consistency-hook extensions, or reclassification of existing evidence without
new analysis. These may support a task, but they are not the deliverable unless
the user explicitly asks for a planning-only change.

## Project Objective

The repository is trying to become an automated, reproducible rockfall
hazard-map workflow for Switzerland's Alpine terrain using public geodata,
primarily swisstopo. The first concrete milestone is a valley-scale Tschamut
pilot that produces conditional grid-cell intensity-exceedance hazard-map
products with documented uncertainty, provenance, performance, and
non-operational interpretation limits.

Medium-term objectives are to make the conditional pilot scientifically
interpretable, reproducible on Balfrin/CSCS-style infrastructure, and scalable
toward larger release-zone ensembles. True physical or annual
intensity-frequency products remain deferred until source occurrence rates,
block-population frequencies, uncertainty propagation, and validation or
calibration evidence exist.

The selected Tschamut target-scale evidence remains `inconclusive`. Larger
selected-domain runs remain blocked until the capability gaps below are reduced
with measured evidence.

Non-goals for current backlog work: operational warning systems, regulatory
approval, risk/exposure/vulnerability modelling, annual return-period claims,
parameter tuning to fit the pilot, and new contact/terrain physics unless a
separate falsifiable implementation task is explicitly authorized.

## Capability Gap Analysis

The most important gaps between the current repository and the project
objective are:

1. Conditional pilot evidence is still inconclusive, but the main same-scale
   artifacts are now present and measured. The earlier
   Balfrin target-gate reproduction remains useful execution evidence, while
   the restored Tschamut gate and target hazard manifests expose 22 shared
   cell-wise layers and the target-vs-gate comparison completed with large
   differences, including
   `cellwise_linf_abs_diff_max = 3028.22579673`,
   `cellwise_l1_abs_diff_sum = 190790.42488112117`, and
   `cellwise_nonzero_jaccard_min = 0.1`. The next gap is explaining and
   reducing the uncertainty behind those differences, not restoring inputs.
2. Validation-output volume is now reduced but still operationally relevant.
   Gate-side `summary_only` output reduced from `125` files / `34545900` bytes
   to `4` files / `81425` bytes; target-side `summary_only` output reduced
   from `2005` files / `571368823` bytes to `4` files / `1271721` bytes. The
   remaining question is how these profiles behave for repeated or larger
   deterministic ensembles.
3. Forest and obstacle context is no longer an absent-cache problem; it is a
   corridor-relevance problem. The inspector now has real local public
   context evidence for swissSURFACE3D Raster, SWISSIMAGE, swissBUILDINGS3D,
   and a staged swissTLM3D archive that has now been queried at corridor
   level. Roads, barriers, and water are measured as limiting context rather
   than missing-cache evidence, and the same-scale top-cell overlap envelope
   has now been measured as unresolved within the current 20 m proximity
   check. The same-scale interpretation remains conditional because context
   is still not obstacle physics.
4. Scaling direction is now better bounded. The single-job Balfrin path is
   sufficient for the next same-scale conditional pilot step; distributed
   execution should stay deferred until a new measurement shows a need.
5. Evidence tooling is becoming useful but remains ad hoc. Current summary and
   measurement scripts are valuable because they generate reusable evidence,
   but more one-off record readers would add process weight unless they remove
   a real execution or interpretation blocker.
6. Local ignored-artifact readiness remains fragile. Several tasks found exact
   missing paths after long audits; a reusable preflight now exists so future
   workers can check readiness before expensive diagnostics.
7. The current same-scale hazard-context overlap measurement is too narrow for
   interpretation. The top positive cell in each of three layers had zero
   20 m proximity hits, but that does not quantify overlap across broader
   high-relevance envelopes or percentile masks.
8. Source-zone and block-scenario evidence is still pragmatic and
   inventory-conditioned. This is acceptable for the first pilot only if the
   interpretation explicitly stays conditional and non-operational.
9. Physical/annual frequency semantics are absent. This is not a near-term
   implementation gap unless the conditional pilot first reaches accepted
   diagnostic status.

## Backlog Quality Assessment

The current backlog should be judged by whether it creates new measurements,
analysis capabilities, reproducibility, or execution capacity. The strongest
tasks are those that turn the existing Tschamut/Balfrin artifacts into
actionable scientific evidence or remove a measured execution blocker.

Over-procedural areas to avoid:

- repeated reclassification of the same `inconclusive` evidence without a new
  analysis or run;
- additional YAML records or validators that do not enable execution,
  measurement, or reproducibility;
- roadmap/status maintenance that does not change what a worker can run or
  learn;
- secondary GIS/QGIS bookkeeping when the main conditional hazard-map evidence
  remains unresolved.

Underrepresented high-value work:

- explaining target-vs-gate disagreement drivers across the measured same-scale
  hazard layers;
- broadening hazard-context overlap from a top-cell probe to a small
  high-relevance envelope;
- bounded repeatability or ensemble-sensitivity probes that quantify whether
  same-scale differences shrink with sampling or remain structurally limiting;
- hardening source-zone and block-scenario generation so future Swiss public
  pilots do not depend on hand-restored private case files;
- GIS-ready output usability checks that remain secondary to scientific
  acceptance but make generated products inspectable when artifacts exist;
- portability preflights for applying the workflow to a second Swiss
  public-geodata site.

## Backlog Protocol

Each active task must include:

- scope small enough for one focused worker turn;
- explicit files, data records, or commands to inspect first;
- the concrete implementation, run, analysis, or validation outcome it enables;
- no-physics/no-tuning/no-operational-claim boundaries when relevant;
- exact outputs expected;
- focused checks to run.

For Tschamut same-scale tasks, prompts should normally tell workers to run the
readiness preflight before broad inspection:

```bash
PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json
```

Workers should use that command's readiness flags, `missing_paths`, and
`regeneration_commands` as the current local artifact state unless a
task-specific diagnostic proves otherwise. Do not make workers rediscover
gate/target/context/output-profile paths manually when the preflight can answer
the question directly.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history and `decision_log.md` for durable decisions.

## Active Tasks

### TB-024: Diagnose Target-Vs-Gate Spatial Disagreement Drivers

Capability gap reduced: target-vs-gate convergence is now measured and
inconclusive, but the repo has not separated which differences come from
sample count, scenario composition, layer semantics, threshold choices, or
spatial displacement.

Goal: analyze the existing gate and target manifests, case metadata, scenario
tables, layer metrics, and comparison output to explain the dominant
target-vs-gate disagreement drivers without rerunning larger ensembles.

Inspect first:

- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `docs/conditional_hazard_convergence_acceptance_protocol.md`;
- `scripts/compare_hazard_map_convergence.py`;
- restored gate and target case/manifests under ignored paths;
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`.

Required work:

1. Use existing artifacts and metadata; do not change thresholds or rerun
   larger ensembles.
2. Produce a compact per-layer diagnosis of the strongest disagreements.
3. Distinguish spatial displacement from magnitude-only differences where the
   current rasters allow it.
4. Recommend the next measurement needed to reduce uncertainty, not a status
   reclassification.

Definition of done:

- disagreement drivers are summarized with measured evidence;
- the result informs the next sampling or scenario-sensitivity task;
- checks pass.

### TB-025: Run A Bounded Same-Scale Sampling Sensitivity Probe

Capability gap reduced: same-scale convergence remains inconclusive, and the
repo needs a measured indication of whether differences shrink under controlled
sampling or seed/chunk variation before considering larger ensembles.

Goal: run a small, bounded sampling-sensitivity or split-run probe using the
existing same-scale workflow and summary-only output profile, then compare the
result with the existing target/gate artifacts.

Inspect first:

- `docs/tschamut_public_conditional_pilot_gate_report.md`;
- `docs/tschamut_public_bounded_validation_output_profile.md`;
- `scripts/build_hazard_layers.py`;
- `scripts/compare_hazard_map_convergence.py`;
- same-scale private cases and manifests under ignored paths.

Required work:

1. Keep the probe bounded and local; do not run a larger production ensemble.
2. Preserve physics, thresholds, release assumptions, sampling weights,
   baselines, and non-operational semantics.
3. Use `summary_only` output where possible.
4. Report file/byte/runtime pressure and cell-wise sensitivity metrics.

Definition of done:

- a bounded sensitivity measurement exists or exact blockers are recorded;
- results inform whether larger deterministic ensembles are justified;
- checks pass.

### TB-026: Harden Source-Zone And Block-Scenario Case Regeneration

Capability gap reduced: target-side artifacts were restored locally, but the
workflow still relied on reconstructing private case files from frozen records.
Future Swiss public-data pilots need a clearer reproducible case-generation
path from public processed inputs.

Goal: add or improve a lightweight case-generation command that reconstructs
same-scale Tschamut validation cases from frozen public input metadata,
scenario tables, and source-zone metadata without hand-editing private YAML.

Inspect first:

- `scripts/validate_public_real_site_conditional_pilot_run.py`;
- `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`;
- `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`;
- restored gate and target private cases under ignored paths.

Required work:

1. Generate or validate case YAML from frozen records without changing model
   settings.
2. Keep generated private cases ignored unless tiny fixtures are needed for
   tests.
3. Add focused fixtures/tests for deterministic case generation.
4. Preserve all non-operational and no-annual-frequency boundaries.

Definition of done:

- future workers can regenerate gate/target private cases from committed
  records and processed public inputs;
- focused tests cover deterministic output shape;
- checks pass.

### TB-027: Add A Second-Site Public-Geodata Portability Preflight

Capability gap reduced: the current workflow is still Tschamut-specific. The
national hazard-map goal needs an early, non-running portability check for a
second Swiss public-geodata pilot site.

Goal: define and run a metadata-only preflight for a second Swiss site that
checks required public geodata products, CRS/extents, source-zone/scenario
inputs, and expected command-plan gaps without running ensembles or committing
raw geodata.

Inspect first:

- `docs/swisstopo_data_strategy.md`;
- `docs/public_real_site_geodata_preparation.md`;
- `data/datasets.yaml`;
- current Tschamut input-preparation scripts and records.

Required work:

1. Do not run a second-site ensemble.
2. Do not commit raw or large geodata.
3. Report exact public-data prerequisites and missing workflow assumptions.
4. Identify what is reusable from Tschamut and what remains site-specific.

Definition of done:

- a second-site portability preflight report or script exists;
- it produces actionable missing inputs and reusable workflow gaps;
- checks pass.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- production COG or QGIS packaging work beyond secondary QA;
- manual GIS/QGIS visual QA unless the local package artifacts and QGIS are
  actually available and the main acceptance evidence is not blocked elsewhere;
- distributed SLURM orchestration unless later evidence shows a measured need.
- shared typed evidence-reader refactors unless at least one more executable
  diagnostic exposes duplicated parsing as the implementation bottleneck.
