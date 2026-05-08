# Roadmap Recommendation Matrix

Status: current prioritization matrix after the selected Tschamut public pilot
manifest, source/scenario policy, DEM-sensitivity gate, no-go run-freeze,
automated GIS package review, and pilot scaling review. Scores are planning
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
reconciled local ignored run-freeze, GIS/scaling evidence, and a no-go
ensemble-feasibility gate. The next work should harden execution robustness and
maintainability before larger ensembles or annual/physical semantics.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Reconcile and regenerate selected pilot gate evidence | 4 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 2 | 19 |
| 2 | Manual QGIS visual QA for selected package | 3 | 5 | 5 | 2 | 5 | 5 | 2 | 3 | 1 | 19 |
| 3 | Forest/obstacle omission scoping for Tschamut | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 3 | 2 | 18 |
| 4 | Conditional-curve/raster output-volume bottleneck | 3 | 5 | 5 | 2 | 5 | 5 | 3 | 2 | 1 | 19 |
| 5 | Ensemble-size increase with convergence diagnostics | 4 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 18 |
| 6 | Fallible terrain/integrator API migration | 3 | 5 | 5 | 4 | 5 | 5 | 3 | 2 | 1 | 21 |
| 7 | Split validation and shape internals by concern | 2 | 4 | 4 | 4 | 5 | 5 | 4 | 2 | 1 | 17 |
| 8 | Deterministic local parallel ensemble driver | 3 | 5 | 5 | 3 | 5 | 5 | 4 | 3 | 2 | 17 |
| 9 | Physical/source-frequency semantics design | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 4 | 4 | 18 |
| 10 | Annual/physical intensity-frequency prototype | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 14 |

## Interpretation

Evidence reconciliation ranks first because the repository currently has two
different pilot stories: the authoritative run-freeze remains no-go, while
separate GIS and scaling notes reference local ignored artifacts. Before more
features or larger ensembles, the selected pilot reports must agree on whether
the processed DEM, trajectory outputs, conditional curves, GIS manifests,
checksums, runtime metrics, and output-volume evidence are reproducible,
local-only, or absent.

Manual QGIS visual QA ranks second. Automated manifest and file checks are
useful, but they cannot verify visual alignment, nodata styling, layer labels,
or reviewer interpretation in QGIS. The current package review is explicitly
`inconclusive` until this happens.

Forest and obstacle omission scoping ranks third. Missing vegetation,
buildings, roads, barriers, or nets could dominate selected-corridor
interpretation and must not be silently absorbed into terrain/material or
contact-model assumptions.

Conditional-curve and raster output-volume work ranks fourth because the pilot
scaling review identifies this as the next practical bottleneck before
ensemble-size increases. This should be an additive output-control or gating
package, not a semantics change.

Increasing ensemble size ranks fifth as a scientific gate, but execution is
not authorized yet. The roughly 10,000 trajectories per release-zone design
target is important, but larger runs are only meaningful after the small
selected pilot is reconciled, interpretable, GIS-reviewed, and has convergence
diagnostics.

Fallible terrain/integrator migration ranks next because real DEM batches must
not be able to fail catastrophically through nodata or crop-edge panics. This
is an engineering robustness target rather than a physics change.

Splitting validation and shape internals ranks after the panic/error boundary.
It is a maintainability target: avoid adding more schema, exporter, and
experimental scaffold logic to already monolithic modules.

Deterministic local parallel ensemble execution follows the maintainability and
error-boundary work. It is the practical scaling bridge before CSCS/SLURM
orchestration.

Physical/source-frequency semantics and annual/physical prototypes remain
deferred behind robustness, maintainability, and deterministic local
parallelism. Current products are conditional intensity-exceedance diagnostics,
not annual intensity-frequency, return-period, physical-probability, or risk
products.

## Recommended Work Packages

### Best Immediate Work Package

Reconcile and regenerate the selected Tschamut pilot gate evidence. The output
should be either:

- a completed local ignored gate with processed DEM metadata, DEM-sensitivity
  evidence, conditional curves, hazard/map/GIS/scaling manifests, checksums,
  runtime/output metrics, and reports that all point to the same execution; or
- a clean no-go record that downgrades stale local-only GIS/scaling evidence
  and records what must be regenerated.

### Best Near-Term Scientific Work Package

After reconciliation, scope forest/obstacle omission for the selected Tschamut
corridor before interpreting real-site pilot map patterns. This is scientific
claim hygiene, not obstacle-physics implementation.

### Best Near-Term Engineering Work Package

Complete the fallible terrain/integrator API migration, then split one coherent
`validation.rs` or `shape.rs` concern by module boundary. Keep behavior
unchanged and use tests to prove the split is mechanical before adding local
parallel ensemble execution.

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
- SLURM/CSCS orchestration before deterministic local chunk/reducer contracts
  and measured pilot bottlenecks.
- annual/physical frequency implementation before source-frequency design and
  deterministic larger-ensemble execution are stable.

## Roadmap Corrections

1. Treat `docs/next_development_targets.md` and
   `docs/real_case_intensity_frequency_implementation_roadmap.md` as the
   current near-term roadmap authority.
2. Treat `docs/tschamut_public_pilot_gis_package_review.md` and
   `docs/tschamut_public_pilot_scaling_review.md` as local ignored evidence
   records until they are reconciled with the authoritative run-freeze.
3. Keep `docs/hazard_map_semantics.md`, `docs/pilot_gis_package.md`, and
   `docs/validation_maturity_framework.md` as active interpretation contracts.
4. Keep `docs/agent_work_log.md` as an audit log only. It should not outrank
   `AGENTS.md`, `README.md`, or the current roadmap docs.

## Final Recommendation

Do not start annual or physical probability work yet. The highest-value next
move is to finish hardening real-DEM execution boundaries, then reduce
maintenance risk in the largest V&V/experimental modules, and only then add a
deterministic local parallel ensemble driver for the selected pilot workflow.
