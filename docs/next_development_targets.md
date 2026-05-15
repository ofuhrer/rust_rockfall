# Next Development Targets

Status: authoritative current development targets.

This file is the single source of truth for current implementation priority.
When an agent or user refers to "Target 1" or "the next target", interpret that
as `DT-01` in this file, not as a historical target number in an older roadmap,
matrix, work log, or decision record. Supporting roadmap documents may explain
why these targets are ordered this way, but they do not define current target
selection.

These targets are planning recommendations only. They do not change simulator
physics, defaults, validation cases, sampling weights, public benchmark status,
annual/physical probability semantics, or operational claims.

## Current State

The repository now has substantial scaffolding and selected-domain contracts
for the Swiss public-data hazard-map workflow:

- selected Tschamut public conditional pilot manifests and source/scenario
  policy;
- reconciled DEM-sensitivity, conditional gate, GIS package, scaling, runtime,
  memory, file-count, byte-count, and checksum evidence in ignored local
  artifacts;
- summary-only conditional intensity-exceedance curve export;
- fallible DEM-facing runtime guardrails;
- deterministic local parallel ensemble execution and reducer parity tests;
- target-scale conditional evidence with 1,000 observed-release trajectories;
- reassessed `no_go` ensemble-size gate;
- blocked secondary QGIS/visual-QA record;
- limiting forest/obstacle context record;
- balfrin readiness checker, pilot runbook, output-profile contract,
  SLURM-first probe driver, probe metrics/log-audit collection, and clean
  420x450 SLURM baseline evidence;
- initial conditional hazard-map convergence acceptance protocol applied to the
  completed DT-04 Balfrin reproduction, with the current classification still
  `inconclusive`;
- completed balfrin same-scale reproduction of the selected conditional
  hazard-map target gate.

The pilot is still not complete. The selected target-scale gate remains
`inconclusive` because convergence has not been accepted, forest/obstacle
context remains limiting, validation debug-output volume still needs reduction
or explicit justification before a larger run, and the completed balfrin
target-gate reproduction is not yet a convergence pass. DT-05 now records the
conditional convergence protocol and keeps the DT-04 evidence
`inconclusive`; external review risks are carried forward as DT-08 through
DT-10 before the pilot can be accepted. The DT-06 stochastic sampling and RNG
stream audit package is complete, DT-07 is complete, and DT-08 is now the next
active target.
DT-08 is now the next active target.
Target-run provenance is now explicitly classified: the
1,000-trajectory observed-release target run is separated from the auxiliary
single-release `ensemble_execution` sidecar.

## Active Development Targets

### DT-01: Close Target-Run Provenance And Selected Output-Profile Policy

Status: complete for the current selected target gate.

Objective: prevent future agents from confusing auxiliary `ensemble_execution`
provenance with full observed-release target-run provenance, and tie selected
runs to the documented output profiles.

Why this comes first: further selected-domain scaling should not proceed while
the target-scale report can be interpreted as having complete validation-runner
parallel provenance when that provenance currently applies only to an auxiliary
single-release ensemble path. The output-profile contract exists, but selected
target reports still need a clear policy link.

Done: `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`
now has `target_run_provenance_policy` and `output_profile_policy` sections.
They separate the 1,000 observed-release target run from the auxiliary
single-release `local_parallel_ensemble_v1` sidecar, classify the current run
as `custom_or_mixed_legacy_summary_only`, select `scalable_conditional` for
future follow-up runs unless `provenance_audit` is explicitly needed, and keep
the validation debug-output budget blocker visible.

Do not: increase ensemble size, change debug-output defaults silently, rewrite
hazard semantics, or present this as a convergence pass.

### DT-02: Record Balfrin Artifact And Environment Readiness

Status: complete for the current balfrin readiness gate.

Objective: create a share-safe readiness record for
`/users/olifu/work/rust_rockfall` on `balfrin.cscs.ch`.

Why this comes next: the readiness checker and runbook exist, but the intended
execution checkout still needs an auditable ready/blocked result before the
selected target-scale gate is rerun there.

Done: `validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml`
records the `/users/olifu/work/rust_rockfall` checkout on balfrin at commit
`61ab9c6542ba1d2274139940777ff0238f1983cf`, Rust/Python toolchain status,
writable validation and hazard output roots, required ignored input status,
processed DEM artifact status, command-plan preconditions, and
`ready_for_balfrin_target_gate` with zero blocking checks.

Do not: commit raw/public geodata tiles, regenerate baselines, or run the
selected target-scale gate as part of this readiness record unless explicitly
requested.

### DT-03: Close Current SLURM Probe Repeatability And Log-Audit Loop

Status: complete for the current 420x450 SLURM probe.

Objective: classify the current 420x450 SLURM probe evidence before using the
driver for selected-gate reproduction.

Why this comes next: the SLURM-first driver and clean 420x450 baseline are
useful only if repeat/reuse behavior, numerical artifact stability, and
warning/error-like log summaries are reviewed.

Done: `validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`
records the fresh baseline, two repeat/reuse SLURM jobs, clean log audits,
stable trajectory/reducer plan IDs, and a before/after hash check showing
`33/33` numeric hazard artifacts unchanged. The single-job driver is classified
as `ready_for_same_scale_selected_gate_reproduction` with scope limits.

Do not: add SLURM arrays, distributed reducers, MPI, GPU execution, or new
scheduler orchestration before the single-job probe loop is classified.

### DT-04: Reproduce Selected Tschamut Conditional Hazard-Map Gate On Balfrin

Status: complete; classification `inconclusive`.

Objective: rerun the existing selected Tschamut conditional hazard-map target
gate on balfrin at the same scale with unchanged inputs/defaults.

Why this comes next: the main pilot outcome is a reproducible conditional
hazard map, not a GIS package. The current target-scale evidence is local and
ignored; the intended CSCS environment needs its own share-safe reproduction
record.

Done: `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`
records the selected 1,000-trajectory Tschamut conditional hazard-map target
gate on balfrin at commit `61ab9c6542ba1d2274139940777ff0238f1983cf`, with
unchanged physics/defaults, summary-only conditional curves, grid CSV
suppression, GeoTIFF export, deterministic chunk metadata, checksums,
performance evidence, and a clean log audit. The result is classified
`inconclusive`, not `passed`, because convergence acceptance, forest/obstacle
context, and secondary manual GIS/QGIS QA remain unresolved.

Do not: increase ensemble size, tune parameters, change release assumptions,
change output thresholds, or claim operational validity.

### DT-05: Define Conditional Hazard-Map Convergence And Acceptance Protocol

Status: complete for the current selected target gate; classification
`inconclusive`.

Objective: predeclare how conditional hazard rasters, target-gate summaries,
and pilot evidence are classified as `pass`, `inconclusive`, or `no_go`.

Why this was needed: the selected target-scale gate remains inconclusive
because technical completion is not enough. Acceptance needs predeclared
conditional-only rules that are independent of annual/physical probability
claims.

Done: `validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`
records the conservative DT-05 protocol, required evidence categories, and the
current DT-04 Balfrin assessment. The protocol classifies that evidence as
`inconclusive`, keeps scale-up authorization false, and preserves the
no-annual/no-physical/no-risk boundary. External review issues that exceed the
current protocol are now carried forward as DT-07 DEM/input QA, DT-08
output-budget/reducer gates, and DT-09 distributed execution; DT-06 stochastic
sampling and RNG stream audit is complete.

Do not: use the protocol to justify physical source frequency, return periods,
risk products, regulatory acceptance, or a larger ensemble-size run.

### DT-06: Audit Stochastic Sampling And RNG Stream Semantics

Status: complete; classification `diagnostic_incomplete`.

Objective: turn stochastic validity concerns into an auditable contract before
the selected pilot is used as accepted hazard-map evidence.

Why this came before execution scaling: the pilot can run and still be
statistically weak if deterministic stream derivation, stochastic variable
families, release perturbations, roughness draws, scenario weights, or weighted
uncertainty semantics are not auditable.

Done: `docs/stochastic_sampling_rng_stream_audit.md` records the current RNG
and seed derivation summary, stochastic variable families, release
perturbation semantics, roughness/contact semantics, scenario/block sampling
and weighting semantics, known limitations, and the no-behavior-change
boundary. `validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml`
captures the machine-readable audit record, and the focused validator/test
pair enforces the current claim boundary.

Do not: change stochastic defaults, tune distributions, or reinterpret current
conditional layers as physical probabilities.

### DT-07: Define Real-Site DEM/Input Conditioning QA Gate

Status: complete; classification `blocked_pending_local_evidence`.

Objective: require a fail-closed QA gate for raw public inputs, DEM
conditioning, CRS/registration, nodata, slope artifacts, and DEM boundary
semantics before larger Tschamut or Swiss-wide pilot runs are trusted.

Why this comes before more scale: external review identified ingestion,
registration, nodata, DEM artifacts, and boundary/clamping behavior as failure
points that can create plausible but spatially wrong hazard maps.

Done: `docs/real_site_dem_input_conditioning_qa_gate.md` defines the QA gate
scope, evidence categories, nodata policy, strict versus clamped DEM
interpretation, terrain-error handling, and conservative classification
states. `validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml`
records the selected Tschamut pilot assessment, and the focused
validator/test pair enforces the claim boundary and blocked status.

Do not: patch DEM defects through contact-parameter tuning or treat clamped
edge behavior as physical terrain continuation.

### DT-08: Define Output Budget And Reducer Scaling Gate

Status: next active target.

Objective: convert output file count, byte count, inode use, dense-grid
accumulator behavior, reducer restart files, and summary-only output policy
into explicit pass/fail gates before any ensemble-size increase.

Why this comes before more trajectories: the DT-04 run completed, but output
volume and dense-grid reduction remain plausible bottlenecks. Scaling should be
authorized only after budgets and reducer behavior are enforced rather than
described after the fact.

Done when: the selected pilot has explicit byte/file/inode budgets, summary-only
export requirements, reducer state-size limits, dense-vs-sparse risk
classification, and no-go rules for budget overruns.

Do not: increase ensemble size, add full curve/grid CSV outputs at scale, or
replace acceptance criteria with ad hoc output cleanup.

### DT-09: Design Balfrin Distributed Execution Only If Needed

Objective: define restartable cross-process trajectory/hazard chunks, SLURM
arrays, work balancing, and reducer dependencies only if DT-05 through DT-08
show the current single-job driver is the limiting blocker.

Why this is later: scheduler complexity should follow measured bottlenecks and
accepted scientific/output gates, not precede them.

Done when: a design or prototype proves deterministic chunk ids, immutable
content-addressed run identity, restart behavior, checksums, reducer merge
semantics, failure classification, and Balfrin quota/I/O preflight without
changing model results.

Do not: add SLURM arrays, distributed reducers, MPI, GPU execution, or
production orchestration while scientific acceptance and output gates are still
undefined.

### DT-10: Review Target-Scale Forest And Obstacle Context

Objective: decide whether omitted forest, buildings, roads, barriers, nets, or
other obstacles are acceptable, limiting, or invalidating for interpreting the
selected Tschamut outputs.

Why this remains important: the context-layer inventory exists, but local
public context layers have not been reviewed for the selected corridor.
Obstacle omission can invalidate interpretation even if convergence and
execution gates pass.

Done when: the obstacle-context record is updated with locally reviewed public
context layers and a share-safe interpretation classification.

Do not: tune restitution, terrain classes, stopping behavior, or contact
parameters to absorb omitted obstacles.

### DT-11: Complete Secondary Target-Scale Manual GIS/QGIS Visual QA

Objective: review target-scale package alignment and labels in QGIS when local
package artifacts and QGIS are available.

Why this is secondary: visual GIS QA supports interoperability and spatial
sanity, but the main pilot outcome is the reproducible conditional hazard map
and its convergence/provenance evidence.

Done when: a share-safe visual-QA record is `passed`, `failed`, or explicitly
`blocked` for CRS alignment, nodata styling, source-zone overlay, layer labels,
and interpretation notes.

Do not: treat QGIS packaging as a substitute for convergence, stochastic
validity, DEM/input QA, output-budget gates, forest/obstacle context, or
balfrin reproduction.

### DT-12: Continue Focused Module Splits When They Support Roadmap Work

Objective: keep reducing maintenance risk in large validation and experimental
shape-contact areas when a focused behavior-preserving split directly supports
active pilot or provenance work.

Why this is supporting work: validation has already been split into several
submodules. Further cleanup should reduce real review risk, not distract from
the pilot evidence chain.

Done when: a narrow module split keeps behavior unchanged, preserves tests, and
removes a concrete maintenance or review blocker.

Do not: refactor broadly without a behavior-preserving test boundary.

### DT-13: Revisit Physical/Annual Intensity-Frequency Only After Evidence Gates

Objective: keep annual frequency, physical probability, return-period, and risk
products deferred until the source-frequency design gate has accepted evidence
and runtime preconditions.

Why this is deferred: the current products are conditional
intensity-exceedance diagnostics. Physical or annual products require source
and block occurrence evidence, overlap-adjusted reducers, uncertainty
propagation, and accepted validation/calibration review.

Done when: the inactive design-gate records are accepted with real evidence and
a separate implementation plan authorizes a small physical/annual prototype.

Do not: implement annual or physical runtime semantics while the design gate
remains deferred.

## Completed Or Blocked Historical Gates

These items are retained as history so agents understand why the active targets
start at DT-01. They are no longer current target numbers.

| Former item | Current status |
| --- | --- |
| Reconcile and regenerate selected pilot gate evidence | Complete. The selected run-freeze and reports reference regenerated or verified ignored DEM-sensitivity, validation, hazard, GIS, reducer, scaling, runtime, memory, file-count, byte-count, and checksum evidence with an `inconclusive` non-operational classification. |
| Manual QGIS visual QA for the selected package | Complete at the share-safe checklist level as `blocked`; QGIS and ignored target package artifacts are unavailable in this checkout. |
| Forest and obstacle omission scoping | Complete at the share-safe scoping level as `limiting`; local public context-layer review remains DT-10. |
| Conditional-curve output-volume bottleneck | Complete for the largest curve-table output through opt-in `--conditional-curve-export summary-only`; raster-output optimization remains future work. |
| Ensemble-size increase gate | Complete as `no_go`; further diagnostic scale-up is not authorized until convergence, output budget, obstacle context, balfrin reproducibility, and provenance blockers are resolved. |
| Fallible terrain/integrator API guardrails | Complete at the guardrail level; DEM-facing fixed-step runtime code propagates terrain errors through fallible helpers, with infallible wrappers retained as compatibility helpers. |
| Validation module split | Substantially complete for validation; remaining shape/validation splits are maintenance work under DT-12. |
| Deterministic local parallel ensemble execution | Complete at the library-contract level with opt-in `simulate_ensemble_parallel`, `random.ensemble_workers`, `ensemble_execution`, `local_parallel_ensemble_v1`, and deterministic `requested_trajectory_index` merge semantics. |
| Selected scalable conditional target-scale gate | Complete as executed but inconclusive evidence; 1,000 observed-release trajectories, summary-only hazard layers, output budgets, checksums, and reducer parity exist, but scale-up remains unauthorized. |
| Physical/source-frequency semantics and annual prototype | Deferred behind inactive design-gate and preflight records. |

## Recommended Sequence

1. Keep DT-05 as the classification reference for the completed DT-04 balfrin
   evidence.
2. Complete DT-06 and DT-07 before treating the pilot as accepted evidence.
3. Complete DT-08 before any ensemble-size increase.
4. Consider DT-09 only if accepted gates show restartability, load-balancing,
   output-size, or memory bottlenecks that justify distributed execution.
5. Treat DT-10 and DT-11 as interpretation/interoperability blockers that
   should be closed when their local data/tool dependencies are available.

## Boundaries

- Do not change physics, defaults, validation cases, thresholds, release
  assumptions, sampling weights, or baselines as part of target documentation.
- Do not commit raw swisstopo or other large public/private geodata products.
- Do not present conditional hazard maps as annual, physical-probability,
  return-period, risk, regulatory, or operational products.
- Do not use Tschamut/Mel diagnostic evidence as physics-selection evidence.
- Do not continue public `shape_contact_v0` runtime validation while its pause
  decision remains active.
