# Task Backlog

Status: authoritative executable task backlog.

This file is the only maintained queue of implementation tasks. It is written
for worker agents, including smaller GPT-5.4-Mini-style agents, so each task
should be narrowly scoped, have a concrete definition of done, and avoid
requiring broad roadmap rereads.

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

Worker rule: when a task is completed successfully and committed, remove that
task from this backlog. Add at most one follow-up task if the completed work
uncovers a concrete next blocker. Record durable choices in `decision_log.md`
and completed work in `agent_work_log.md`.

Supporting documents such as
`real_case_intensity_frequency_implementation_roadmap.md` and
`roadmap_recommendation_matrix.md` explain long-term context and rationale.
They do not define the executable queue.

## Current Pilot State

The closest achievable milestone is a conditional Tschamut hazard map with
documented uncertainty, provenance, resource bounds, and non-operational
framing. The repository is not close to a true physical or annual
intensity-frequency map. Source occurrence rates, block-population frequency,
annualization semantics, uncertainty propagation, physical-frequency reducer
semantics, and validation/calibration gates remain deferred.

Completed prerequisites include:

- DT-05 conditional convergence and acceptance protocol;
- DT-06 stochastic sampling and RNG stream audit;
- DT-07 real-site DEM/input conditioning QA gate;
- DT-08 output budget and reducer scaling gate;
- Balfrin same-scale target-gate reproduction;
- DT-10 forest/obstacle context review classified
  `blocked_pending_local_evidence`.

The selected Tschamut target-scale evidence remains `inconclusive`. Larger
ensembles remain blocked unless convergence, output budgets, stochastic audit,
DEM/input QA, forest/obstacle context, and claim-state evidence justify the
increase. QGIS/GIS visual QA is secondary to the hazard-map evidence chain.

## Backlog Protocol

Each active task should include:

- scope small enough for one focused worker turn;
- explicit files or evidence records to inspect first;
- the concrete implementation or validation outcome it enables;
- no-physics/no-tuning/no-operational-claim boundaries when relevant;
- exact outputs expected;
- focused checks to run.

Do not keep completed tasks here. Use `agent_work_log.md` for execution
history.

## Active Tasks

### TB-001: Reassess Conditional Pilot Classification Using Existing Gates

Goal: apply the completed DT-05 convergence protocol and DT-08 output-budget
gate to the current 1,000-trajectory Balfrin target evidence and record whether
the selected Tschamut pilot remains `inconclusive`, becomes `no_go`, or can be
classified as an accepted conditional diagnostic pilot.

Inspect first:

- `docs/conditional_hazard_convergence_acceptance_protocol.md`;
- `docs/output_budget_reducer_scaling_gate.md`;
- `validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`;
- `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`;
- `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`;
- `docs/tschamut_public_scalable_conditional_target_gate.md`.

Required work:

1. Update only the relevant assessment record or report.
2. Keep all physics, defaults, thresholds, release assumptions, and baselines
   unchanged.
3. Do not run larger ensembles or public benchmarks.
4. Preserve no annual/physical/risk/operational claims.
5. If evidence is insufficient, keep the classification conservative and state
   the exact missing evidence.

Definition of done:

- classification is explicit;
- scale-up authorization is explicit;
- output-budget and convergence blockers are listed;
- focused validator/tests and `scripts/check_repo_consistency.py` pass.

### TB-002: Reduce Or Justify Validation Debug-Output Budget Blocker

Goal: decide whether validation debug-output volume is a real blocker for the
selected Tschamut pilot or can be bounded by a documented output profile
without changing defaults silently.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`;
- `docs/tschamut_public_pilot_scaling_review.md`;
- `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`;
- `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`;
- `scripts/validate_pilot_ensemble_feasibility.py`.

Required work:

1. Record the current validation output file/byte/inode pressure.
2. Decide whether the blocker is `accepted_with_limits`, `blocked`, or
   `requires_output_profile_change`.
3. If proposing a future profile change, document it only; do not change
   runtime defaults unless a separate task authorizes it.
4. Keep generated outputs ignored.

Definition of done:

- machine-readable record and docs agree;
- no scale-up is authorized unless output limits are explicitly accepted;
- focused tests and consistency checks pass.

### TB-003: Prepare Local Public Context-Layer Acquisition Checklist For Tschamut

Goal: unblock the forest/obstacle context review by defining the exact public
context layers, local cache paths, checksums, and review steps needed to move
DT-10 from `blocked_pending_local_evidence` to an interpretation
classification.

Inspect first:

- `docs/tschamut_public_obstacle_context_scope.md`;
- `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`;
- `docs/swisstopo_data_strategy.md`;
- `docs/public_real_site_geodata_preparation.md`.

Required work:

1. Do not infer obstacle absence from missing data.
2. Do not implement obstacle physics.
3. Do not tune terrain, restitution, friction, or stopping behavior.
4. Produce a small acquisition/review checklist or update the existing obstacle
   scope doc.
5. Keep raw geodata out of git.

Definition of done:

- required public context products are named;
- expected local ignored paths and checksum/provenance requirements are clear;
- the current gate remains blocked unless evidence is actually reviewed;
- focused checks pass.

### TB-004: Decide Whether Single-Job Balfrin Execution Is Still Enough

Goal: use existing DT-08 and Balfrin evidence to decide whether DT-09
distributed execution design is needed now or should remain deferred.

Inspect first:

- `docs/output_budget_reducer_scaling_gate.md`;
- `docs/balfrin_probe_slurm_driver.md`;
- `docs/balfrin_tschamut_readiness.md`;
- `validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`;
- `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`.

Required work:

1. Do not add SLURM arrays, MPI, GPU, or distributed reducers.
2. Summarize measured wall time, memory, output size, restartability, and
   reducer-state evidence.
3. Classify DT-09 as `defer`, `design_needed`, or `blocked_pending_evidence`.

Definition of done:

- decision is recorded in `decision_log.md` if durable;
- no runtime behavior changes;
- consistency checks pass.

### TB-005: Secondary Manual GIS/QGIS Visual QA Record

Goal: keep the visual-QA state explicit without letting it outrank the
hazard-map evidence chain.

Inspect first:

- `docs/pilot_gis_package.md`;
- `validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`;
- `docs/tschamut_public_pilot_gis_package_review.md`.

Required work:

1. If QGIS and local ignored package artifacts are unavailable, keep the record
   `blocked`.
2. If they are available, record CRS alignment, nodata styling, source-zone
   overlay, layer labels, and interpretation notes.
3. Do not claim operational validity.

Definition of done:

- visual QA is `passed`, `failed`, or `blocked`;
- docs state it is secondary interoperability evidence;
- checks pass.

## Deferred Backlog

These are intentionally not current worker tasks:

- annual or physical intensity-frequency runtime implementation;
- risk, exposure, vulnerability, return-period, or operational products;
- shape-contact runtime progression;
- terrain/material calibration libraries;
- production COG or QGIS packaging work beyond secondary QA;
- distributed SLURM orchestration unless TB-004 or later evidence shows a
  measured need.
