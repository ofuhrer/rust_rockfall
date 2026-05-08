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
execution guardrails, opt-in local parallel ensemble provenance, and a no-go
ensemble-feasibility gate. The next work should produce target-scale evidence
for the already-defined scalable conditional execution contract before any
ensemble-size gate is relaxed or annual/physical semantics are attempted.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Execute selected scalable conditional target-scale gate | 4 | 5 | 5 | 4 | 5 | 5 | 3 | 4 | 2 | 19 |
| 2 | Reassess selected ensemble-size increase gate | 4 | 5 | 5 | 4 | 5 | 5 | 2 | 3 | 2 | 21 |
| 3 | Manual QGIS visual QA for selected package | 3 | 5 | 5 | 2 | 5 | 5 | 2 | 3 | 1 | 19 |
| 4 | Forest/obstacle context review for Tschamut | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 3 | 2 | 18 |
| 5 | Resumable cross-process trajectory chunk manifests | 3 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 17 |
| 6 | Continue focused validation/shape module splits | 2 | 4 | 4 | 4 | 5 | 5 | 3 | 2 | 1 | 18 |
| 7 | Source-frequency evidence acquisition or acceptance review | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 4 | 17 |
| 8 | Physical-frequency reducer implementation design | 5 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 16 |
| 9 | Annual/physical prototype preflight reassessment | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 5 | 16 |
| 10 | Annual/physical intensity-frequency prototype | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 14 |

## Interpretation

The active bottleneck is no longer missing execution contracts. The repository
has a selected scalable conditional execution record, deterministic local
hazard reducer chunks, summary-only conditional curves, and validation-runner
ensemble chunk provenance. What it does not yet have is target-scale evidence
showing that the selected Tschamut conditional run is reproducible, bounded by
output budgets, and scientifically interpretable.

Executing the selected target-scale gate ranks first because it turns the
current design-ready contract into evidence. The first clean-checkout attempt is
now recorded as `blocked_missing_inputs`; the next move is to regenerate or
restore the ignored processed DEM, private frozen case, scenario table, and
prior gate outputs, then rerun with ignored outputs, current conditional
semantics, and a `target_scale_executed` or `inconclusive` record.

Reassessing the ensemble-size gate ranks second. A successful technical run is
not enough by itself: convergence, output budget, manual GIS/QGIS visual QA,
and forest/obstacle context still have to be considered before a larger
diagnostic ensemble is authorized.

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

Unblock and run the selected Tschamut scalable conditional target-scale gate
locally using ignored prepared inputs. The output should be either:

- a share-safe target-scale evidence update with convergence, output budget,
  wall time, memory, worker-count parity, checksums, reducer manifests,
  `ensemble_execution`, and `conditional_hazard_execution_diagnostics_v1`; or
- an updated inconclusive record if regenerated local inputs or review steps
  still prevent target-scale interpretation.

### Best Near-Term Scientific Work Package

After target-scale execution evidence exists, reassess the ensemble-size gate
with manual GIS/QGIS visual QA and forest/obstacle context still visible. This
is scientific claim hygiene, not obstacle-physics implementation.

### Best Near-Term Engineering Work Package

Add resumable cross-process trajectory chunk manifests only if the selected
target-scale evidence shows restartability, output size, or wall-time
bottlenecks that justify that complexity. Otherwise, continue focused
behavior-preserving module splits as maintenance work.

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
move is to regenerate or restore the ignored Tschamut inputs needed by the
selected target-scale command plan, then run the scalable conditional gate
locally and record convergence, output budget, runtime, memory, checksum, and
worker-parity evidence. Only after that evidence exists should the selected
ensemble-size gate be reassessed; larger diagnostic execution should remain
blocked if GIS visual QA or forest/obstacle context is still insufficient.
