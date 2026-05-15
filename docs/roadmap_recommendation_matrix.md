# Roadmap Recommendation Matrix

Status: supporting scoring appendix, not authoritative for current target selection.

Current implementation target selection is authoritative only in
`docs/next_development_targets.md`. This matrix records the scoring rationale
behind that target order; it must not introduce independent numbered target or
rank semantics.

Context: current prioritization matrix after the selected Tschamut public pilot
manifest, source/scenario policy, DEM-sensitivity gate, reconciled no-go
run-freeze, automated GIS package review, pilot scaling review, fallible
DEM-facing integration guardrails, opt-in local parallel ensemble execution,
target-scale conditional evidence, blocked visual-QA record, limiting obstacle
context record, and expanded validation/CI refactors. Scores are planning
guidance, not implementation commitments. The latest balfrin work adds a
readiness checker, output-profile contract, SLURM-first probe driver, probe
metrics/log-audit collector, tracked 20-release-cell and 420x450 probe
definitions, and clean 420x450 SLURM baseline evidence.

## Scoring Method

Positive criteria are scored 1-5:

- scientific credibility gain;
- Swiss pilot relevance;
- hazard-map workflow value;
- validation value;
- reproducibility value;
- alignment with `AGENTS.md` boundaries.

Risk criteria are scored 1-5 where higher is worse:

- implementation risk;
- dependency risk;
- calibration/validation confusion risk.

Composite:

```text
scientific + Swiss pilot + hazard workflow + validation + reproducibility + alignment
- implementation risk - dependency risk - calibration/validation confusion risk
```

Order is not a pure sort by composite score. It also reflects dependency order
and the current evidence state. In particular, the selected Tschamut pilot now
has share-safe manifests, source/scenario policy, a DEM-sensitivity gate, a
reconciled local ignored run-freeze, GIS/scaling evidence, fallible DEM-facing
execution guardrails, opt-in local parallel ensemble provenance, target-scale
conditional evidence, explicit blocked/limiting interpretation records, and a
reassessed no-go ensemble-feasibility gate. Target-run provenance and selected
output-profile policy are now explicit for the current gate. Balfrin readiness
is now recorded as ready for the current gate. The 420x450 SLURM probe
repeat/log-audit loop is also closed. The selected target-scale conditional
hazard-map gate has now been reproduced on balfrin and remains
`inconclusive`, not accepted. External review showed that the existing DT-05
convergence protocol is too narrow for scientific acceptance because it does
not yet cover stochastic validity, DEM/input conditioning, boundary/termination
semantics, and output-budget gates. The next implementable work should broaden
DT-05 before any ensemble-size gate is relaxed or annual/physical semantics are
attempted. GIS/QGIS work is treated as secondary interoperability QA rather
than the main pilot outcome.

## External Review Synthesis

The hostile review findings are roadmap pressure, not immediate authorization
to change physics, defaults, RNG behavior, DEM storage, contact mechanics, or
Balfrin execution architecture. They reprioritize the next gates as follows:

1. Scientific acceptance/convergence and claim-state gates.
2. Stochastic validity and sampling semantics.
3. DEM/input conditioning and boundary/termination semantics.
4. Output/reducer scaling and I/O budget enforcement.
5. Distributed SLURM orchestration, only after measured need.
6. Shape/contact and annual/physical frequency, still deferred.

## Scoring Matrix

| Target ID | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DT-01 (complete) | Close target-run provenance and selected output-profile policy | 3 | 5 | 5 | 4 | 5 | 5 | 3 | 3 | 2 | 19 |
| DT-02 (complete) | Record balfrin artifact/environment readiness result | 3 | 5 | 5 | 3 | 5 | 5 | 2 | 4 | 1 | 19 |
| DT-03 (complete) | Close current SLURM probe repeat/log-audit loop | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 1 | 19 |
| DT-04 (complete) | Reproduce selected Tschamut conditional hazard-map gate on balfrin | 4 | 5 | 5 | 4 | 5 | 5 | 4 | 4 | 2 | 18 |
| DT-05 | Conditional hazard-map convergence and acceptance protocol | 5 | 5 | 5 | 5 | 5 | 5 | 3 | 3 | 2 | 22 |
| DT-06 | Stochastic sampling and RNG stream audit | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 3 | 3 | 20 |
| DT-07 | Real-site DEM/input conditioning QA gate | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 4 | 2 | 20 |
| DT-08 | Output budget and reducer scaling gate | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 1 | 19 |
| DT-09 | Balfrin distributed execution design only if needed | 3 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 17 |
| DT-10 | Forest/obstacle context review with local public context layers present | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 4 | 2 | 17 |
| DT-11 | Manual QGIS visual QA with local target package and QGIS present | 2 | 4 | 3 | 2 | 5 | 5 | 2 | 4 | 1 | 14 |
| DT-12 | Continue focused shape module split | 2 | 4 | 4 | 4 | 5 | 5 | 3 | 2 | 1 | 18 |
| DT-13 | Source-frequency evidence acquisition or acceptance review | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 4 | 17 |
| Deferred | Physical-frequency reducer implementation design | 5 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 16 |
| Deferred | Annual/physical prototype preflight reassessment | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 5 | 16 |
| Deferred | Annual/physical intensity-frequency prototype | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 14 |

## Interpretation

The active bottleneck is no longer missing execution contracts or target-scale
execution evidence. The repository has a selected scalable conditional
execution record, deterministic local hazard reducer chunks, summary-only
conditional curves, validation-runner ensemble chunk provenance, and an
executed but inconclusive selected Tschamut target-scale gate.

The target-scale gate produced 1,000 observed-release trajectories, summary-only
conditional hazard layers, output-budget/runtime/memory/checksum evidence, and
1-vs-2 worker reducer parity. It has now also been reproduced on balfrin as
job `4318941`, with clean log audit and share-safe checksums recorded in
`validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`.
It remains `inconclusive` because convergence has not been accepted,
forest/obstacle context remains limiting because local context layers are
absent, and manual GIS/QGIS visual QA is still secondary interoperability
evidence rather than the main hazard-map acceptance gate. The existing DT-05
protocol codifies that classification and keeps scale-up unauthorized, but the
external review requires a broader acceptance protocol before the evidence can
be treated as accepted.

Balfrin readiness has moved from scaffolding to recorded readiness for the
current gate. The readiness checker, runbook, output-profile contract,
SLURM-first probe driver, metrics/log collector, and
`validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml` now exist.
Clean 20-release-cell and 420x450 probe evidence shows the conditional workflow
can run under a controlled single-job SLURM pattern. The current 420x450
baseline now has repeat/reuse closure, clean log audits, and a stable numeric
artifact hash check. The selected target-scale gate now has its own balfrin
reproduction record, classified `inconclusive`.

The ensemble-size gate has now been reassessed and remains `no_go`. A
successful technical run was not enough by itself: convergence, output budget,
forest/obstacle context, balfrin reproducibility, and validation-runner
provenance still block a larger diagnostic ensemble. External review adds
stochastic-stream validity, sampling-distribution contracts, DEM/input
conditioning, boundary/termination semantics, dense-grid reducer scaling, and
claim-state controls as explicit acceptance concerns. Manual GIS/QGIS remains a
supporting QA item.

Forest/obstacle context review remains a high-priority scientific
interpretation blocker, but it is currently data blocked in this checkout.
Manual QGIS visual QA remains useful for spatial sanity and interoperability,
but it should not outrank the hazard-map evidence package itself. Automated
manifest checks prove file and metadata consistency, but they cannot replace
terrain/forest/obstacle context assessment for a real Alpine corridor.

Resumable cross-process trajectory chunk manifests and SLURM-array design now
rank after the acceptance, stochastic, DEM/input, and output-budget gates. The
repository should not add scheduler-style complexity until accepted evidence
shows the current single-job driver is the limiting factor.

Focused module splits remain useful maintenance work. The validation harness
has now been split into several submodules, so the next maintenance value is
mostly in shape-contact scaffolding and any remaining validation extraction
that directly supports the selected pilot evidence chain.

Physical/source-frequency work remains behind evidence gates. The repository
now contains inactive contracts for source-rate evidence, block/release
probabilities, reducer preconditions, and validation-calibration review. Those
contracts are useful, but they do not authorize annual intensity-frequency,
return-period, physical-probability, or risk products.

## Recommended Work Packages

### Completed Immediate Work Package

The target-run provenance/output-profile policy gap is closed for the current
selected gate. The target record now separates the 1,000 observed-release run
from the auxiliary `ensemble_execution` sidecar, classifies the current output
profile as legacy/custom summary-only, selects `scalable_conditional` for
future follow-up runs unless `provenance_audit` is explicitly needed, and keeps
the validation debug-output budget blocker visible.

### Best Near-Term Scientific Work Package

Broaden DT-05 into the conditional convergence and scientific acceptance
protocol described in the current target list. It should classify the completed
DT-04 evidence only through predeclared gates covering convergence, stochastic
validity, DEM/input conditioning, boundary semantics, output budgets, and
claim states.

### Best Near-Term Engineering Work Package

Document the DT-06 stochastic audit, DT-07 DEM/input QA gate, and DT-08
output-budget/reducer gate before adding distributed execution. Use the
SLURM-first single-job probe driver until those gates show a concrete need for
arrays or cross-process reducers. Use the multi-trajectory Parquet writer only
behind an explicit selected-pilot output policy decision.

## What Should Be Paused Or Deferred

Pause or defer:

- public `shape_contact_v0` runtime validation;
- any default change to `sphere_rotational_v1`;
- terrain/material calibration or calibrated parameter libraries;
- annual-frequency or physical-probability hazard maps;
- risk maps, expected loss, vulnerability, exposure, or operational approval
  language;
- forest/barrier/fragmentation implementation before pilot-domain scoping;
- production COG/tiled package work before the conditional hazard-map evidence
  and output contracts justify more GIS packaging;
- SLURM/CSCS orchestration before acceptance, stochastic, DEM/input, and
  output-budget gates show measured bottlenecks that justify it.
- annual/physical frequency implementation before source-frequency design and
  deterministic larger-ensemble execution are stable.

## Roadmap Corrections

1. Treat `docs/next_development_targets.md` as the only authoritative source
   for current target selection.
2. Treat `docs/real_case_intensity_frequency_implementation_roadmap.md` as the
   long-term phase roadmap and `docs/roadmap_recommendation_matrix.md` as this
   supporting scoring appendix. Neither document defines current target
   numbering.
3. Treat `docs/tschamut_public_scalable_conditional_execution.md`,
   `docs/tschamut_public_pilot_gis_package_review.md`, and
   `docs/tschamut_public_pilot_scaling_review.md` as selected-pilot evidence
   records with explicit local/ignored artifact boundaries.
4. Keep `docs/hazard_map_semantics.md`, `docs/pilot_gis_package.md`, and
   `docs/validation_maturity_framework.md` as active interpretation contracts.
5. Keep `docs/agent_work_log.md` as an audit log only. It should not outrank
   `AGENTS.md`, `README.md`, or the current roadmap docs.

## Final Recommendation

Do not start annual or physical probability work yet. The highest-value
implementable next move is the broadened DT-05 acceptance protocol. Manual
GIS/QGIS remains useful but secondary; forest/obstacle review remains
scientifically important but should not outrank convergence, stochastic,
DEM/input, and output-budget gates. Larger diagnostic execution remains blocked
by the reassessed no-go ensemble-size gate.
