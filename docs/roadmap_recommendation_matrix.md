# Roadmap Recommendation Matrix

Status: current prioritization matrix after the selected Tschamut public pilot
manifest, source/scenario policy, DEM-sensitivity gate, reconciled no-go
run-freeze, automated GIS package review, pilot scaling review, fallible
DEM-facing integration guardrails, opt-in local parallel ensemble execution,
and scalable conditional execution contract. Scores are planning guidance, not
implementation commitments.

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

Rank is not a pure sort by composite score. It also reflects dependency order
and the current evidence state. In particular, the selected Tschamut pilot now
has share-safe manifests, source/scenario policy, a DEM-sensitivity gate, a
reconciled local ignored run-freeze, GIS/scaling evidence, fallible DEM-facing
execution guardrails, opt-in local parallel ensemble provenance, target-scale
conditional evidence, and a reassessed no-go ensemble-feasibility gate. The next
work should resolve interpretation/QA blockers before any ensemble-size gate is
relaxed or annual/physical semantics are attempted.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Manual QGIS visual QA for selected package | 3 | 5 | 5 | 2 | 5 | 5 | 2 | 3 | 1 | 19 |
| 2 | Forest/obstacle context review for Tschamut | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 3 | 2 | 18 |
| 3 | Clarify validation-runner target provenance and debug output budget | 3 | 5 | 5 | 4 | 5 | 5 | 3 | 3 | 2 | 18 |
| 4 | Resumable cross-process trajectory chunk manifests | 3 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 17 |
| 5 | Continue focused validation/shape module splits | 2 | 4 | 4 | 4 | 5 | 5 | 3 | 2 | 1 | 18 |
| 6 | Source-frequency evidence acquisition or acceptance review | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 4 | 17 |
| 7 | Physical-frequency reducer implementation design | 5 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 16 |
| 8 | Annual/physical prototype preflight reassessment | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 5 | 16 |
| 9 | Annual/physical intensity-frequency prototype | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 14 |

## Interpretation

The active bottleneck is no longer missing execution contracts or target-scale
execution evidence. The repository has a selected scalable conditional
execution record, deterministic local hazard reducer chunks, summary-only
conditional curves, validation-runner ensemble chunk provenance, and an
executed but inconclusive selected Tschamut target-scale gate.

The target-scale gate produced 1,000 observed-release trajectories, summary-only
conditional hazard layers, output-budget/runtime/memory/checksum evidence, and
1-vs-2 worker reducer parity. It remains `inconclusive` because convergence has
not been accepted, manual GIS/QGIS visual QA is not complete, forest/obstacle
context remains limiting, and validation-runner `ensemble_execution` provenance
covers only the auxiliary single-release ensemble path.

The ensemble-size gate has now been reassessed and remains `no_go`. A
successful technical run was not enough by itself: convergence, output budget,
manual GIS/QGIS visual QA, forest/obstacle context, and validation-runner
provenance still block a larger diagnostic ensemble.

Manual QGIS visual QA and forest/obstacle context review remain high-priority
scientific interpretation blockers. Automated manifest checks prove file and
metadata consistency, but they cannot replace visual alignment review or
terrain/forest/obstacle context assessment for a real Alpine corridor.

Resumable cross-process trajectory chunk manifests rank after the selected
target-scale evidence because the repository should not add scheduler-style
complexity until the local evidence identifies the actual bottlenecks in
runtime, file count, byte count, memory, or restartability.

Focused `validation.rs` and `shape.rs` splits remain useful maintenance work,
but they should be scoped to behavior-preserving module boundaries. They should
not displace the selected pilot evidence step unless a change already touches
those modules.

Physical/source-frequency work remains behind evidence gates. The repository
now contains inactive contracts for source-rate evidence, block/release
probabilities, reducer preconditions, and validation-calibration review. Those
contracts are useful, but they do not authorize annual intensity-frequency,
return-period, physical-probability, or risk products.

## Recommended Work Packages

### Best Immediate Work Package

Complete or explicitly classify manual GIS/QGIS visual QA with the new
target-scale package still treated as a research diagnostic. Automated manifest
checks and reducer parity are not a substitute for visual alignment review.

### Best Near-Term Scientific Work Package

Review forest/obstacle context against the target-scale package. This is
scientific claim hygiene, not obstacle-physics implementation.

### Best Near-Term Engineering Work Package

Clarify validation-runner provenance for observed-release target runs and reduce
or justify validation-side debug output volume before considering another
selected-domain increase. Add resumable cross-process trajectory chunk manifests
only if that review shows restartability, output size, or wall-time bottlenecks
that justify the complexity.

## What Should Be Paused Or Deferred

Pause or defer:

- public `shape_contact_v0` runtime validation;
- any default change to `sphere_rotational_v1`;
- terrain/material calibration or calibrated parameter libraries;
- annual-frequency or physical-probability hazard maps;
- risk maps, expected loss, vulnerability, exposure, or operational approval
  language;
- forest/barrier/fragmentation implementation before pilot-domain scoping;
- production COG/tiled package work before local GeoTIFF/QGIS acceptance;
- SLURM/CSCS orchestration before measured target-scale pilot bottlenecks and
  resumable local chunk/reducer contracts justify it.
- annual/physical frequency implementation before source-frequency design and
  deterministic larger-ensemble execution are stable.

## Roadmap Corrections

1. Treat `docs/next_development_targets.md` and
   `docs/real_case_intensity_frequency_implementation_roadmap.md` as the
   current near-term roadmap authority.
2. Treat `docs/tschamut_public_scalable_conditional_execution.md`,
   `docs/tschamut_public_pilot_gis_package_review.md`, and
   `docs/tschamut_public_pilot_scaling_review.md` as selected-pilot evidence
   records with explicit local/ignored artifact boundaries.
3. Keep `docs/hazard_map_semantics.md`, `docs/pilot_gis_package.md`, and
   `docs/validation_maturity_framework.md` as active interpretation contracts.
4. Keep `docs/agent_work_log.md` as an audit log only. It should not outrank
   `AGENTS.md`, `README.md`, or the current roadmap docs.

## Final Recommendation

Do not start annual or physical probability work yet. The highest-value next
move is manual GIS/QGIS visual QA and forest/obstacle interpretation against
the executed target-scale package. Larger diagnostic execution remains blocked
by the reassessed no-go ensemble-size gate.
