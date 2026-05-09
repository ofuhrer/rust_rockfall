# Roadmap Recommendation Matrix

Status: current prioritization matrix after the selected Tschamut public pilot
manifest, source/scenario policy, DEM-sensitivity gate, reconciled no-go
run-freeze, automated GIS package review, pilot scaling review, fallible
DEM-facing integration guardrails, opt-in local parallel ensemble execution,
target-scale conditional evidence, blocked visual-QA record, limiting obstacle
context record, and expanded validation/CI refactors. Scores are planning
guidance, not implementation commitments.

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
conditional evidence, explicit blocked/limiting interpretation records, and a
reassessed no-go ensemble-feasibility gate. The next implementable work should
clarify target-run provenance and validation debug output budget, then prepare
and reproduce the target-scale conditional hazard-map gate on balfrin, before
any ensemble-size gate is relaxed or annual/physical semantics are attempted.
GIS/QGIS work is treated as secondary interoperability QA rather than the main
pilot outcome.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Clarify validation-runner target provenance and debug output budget | 3 | 5 | 5 | 4 | 5 | 5 | 3 | 3 | 2 | 19 |
| 2 | Prepare balfrin artifact/environment readiness gate | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 4 | 1 | 18 |
| 3 | Reproduce selected Tschamut conditional hazard-map gate on balfrin | 4 | 5 | 5 | 4 | 5 | 5 | 4 | 4 | 2 | 18 |
| 4 | Define selected-pilot large-output policy using CSV/Parquet explicitly | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 2 | 18 |
| 5 | Resumable cross-process trajectory chunk manifests | 3 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 17 |
| 6 | Forest/obstacle context review with local public context layers present | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 4 | 2 | 17 |
| 7 | Manual QGIS visual QA with local target package and QGIS present | 2 | 4 | 3 | 2 | 5 | 5 | 2 | 4 | 1 | 14 |
| 8 | Continue focused shape module split | 2 | 4 | 4 | 4 | 5 | 5 | 3 | 2 | 1 | 18 |
| 9 | Source-frequency evidence acquisition or acceptance review | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 4 | 17 |
| 10 | Physical-frequency reducer implementation design | 5 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 16 |
| 11 | Annual/physical prototype preflight reassessment | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | 5 | 16 |
| 12 | Annual/physical intensity-frequency prototype | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 14 |

## Interpretation

The active bottleneck is no longer missing execution contracts or target-scale
execution evidence. The repository has a selected scalable conditional
execution record, deterministic local hazard reducer chunks, summary-only
conditional curves, validation-runner ensemble chunk provenance, and an
executed but inconclusive selected Tschamut target-scale gate.

The target-scale gate produced 1,000 observed-release trajectories, summary-only
conditional hazard layers, output-budget/runtime/memory/checksum evidence, and
1-vs-2 worker reducer parity. It remains `inconclusive` because convergence has
not been accepted, forest/obstacle context remains limiting because local
context layers are absent, validation-runner `ensemble_execution` provenance
covers only the auxiliary single-release ensemble path, and the run has not yet
been reproduced on balfrin. Manual GIS/QGIS visual QA is explicitly blocked by
missing local package/QGIS, but it is a secondary interoperability check rather
than the main hazard-map acceptance gate.

The ensemble-size gate has now been reassessed and remains `no_go`. A
successful technical run was not enough by itself: convergence, output budget,
forest/obstacle context, balfrin reproducibility, and validation-runner
provenance still block a larger diagnostic ensemble. Manual GIS/QGIS remains a
supporting QA item.

Forest/obstacle context review remains a high-priority scientific
interpretation blocker, but it is currently data blocked in this checkout.
Manual QGIS visual QA remains useful for spatial sanity and interoperability,
but it should not outrank the hazard-map evidence package itself. Automated
manifest checks prove file and metadata consistency, but they cannot replace
terrain/forest/obstacle context assessment for a real Alpine corridor.

Resumable cross-process trajectory chunk manifests rank after balfrin
readiness/reproduction because the repository should not add scheduler-style
complexity until the intended environment identifies the actual bottlenecks in
runtime, file count, byte count, memory, or restartability.

Focused module splits remain useful maintenance work. The validation harness
has now been split into several submodules, so the next maintenance value is
mostly in shape-contact scaffolding and any remaining validation extraction
that directly supports Target 15.

Physical/source-frequency work remains behind evidence gates. The repository
now contains inactive contracts for source-rate evidence, block/release
probabilities, reducer preconditions, and validation-calibration review. Those
contracts are useful, but they do not authorize annual intensity-frequency,
return-period, physical-probability, or risk products.

## Recommended Work Packages

### Best Immediate Work Package

Clarify validation-runner provenance for observed-release target runs and
reduce or justify validation-side debug output volume. The deliverable should
prevent future agents from confusing auxiliary `ensemble_execution` provenance
with full target-run provenance and should make another selected-domain
increase impossible without a documented output policy.

### Best Near-Term Scientific Work Package

Prepare and run the balfrin reproduction of the selected conditional hazard-map
target gate after Target 15 is complete. In parallel or after that, when local
public context layers are available, review forest/obstacle context against the
target-scale package. Until then, keep the current `limiting` classification
and do not tune parameters to absorb omitted obstacles.

### Best Near-Term Engineering Work Package

Use the new multi-trajectory Parquet writer only behind an explicit selected
pilot output-policy decision. Add resumable cross-process trajectory chunk
manifests only if the provenance/output-budget review and balfrin reproduction
show restartability, output size, or wall-time bottlenecks that justify the
complexity.

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
- SLURM/CSCS orchestration before the selected target-scale gate is reproduced
  on balfrin and measured bottlenecks plus resumable local chunk/reducer
  contracts justify it.
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

Do not start annual or physical probability work yet. The highest-value
implementable next move is Target 15: clarify observed-release target
provenance and validation debug output budget. The next pilot-specific moves
are a balfrin artifact/environment readiness gate for
`/users/olifu/work/rust_rockfall` and same-scale balfrin reproduction of the
selected conditional hazard-map target gate. Manual GIS/QGIS remains useful but
secondary; forest/obstacle review remains scientifically important and data
blocked. Larger diagnostic execution remains blocked by the reassessed no-go
ensemble-size gate.
