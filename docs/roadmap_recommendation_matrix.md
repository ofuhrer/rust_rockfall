# Roadmap Recommendation Matrix

Status: scoring matrix and ranked recommendation from the strategic review in
`docs/repository_scientific_roadmap_review.md`. Scores are planning guidance,
not implementation commitments.

## Scoring Method

Each direction is scored from 1 to 5 for positive criteria:

- scientific credibility gain;
- Swiss pilot relevance;
- hazard-map workflow value;
- validation value;
- reproducibility value;
- alignment with `AGENTS.md` boundaries.

Risk criteria are scored from 1 to 5 where higher is worse:

- implementation risk;
- dependency risk;
- risk of confusing calibration with validation.

Composite score:

```text
 scientific credibility
+ Swiss pilot relevance
+ hazard workflow value
+ validation value
+ reproducibility value
+ alignment
- implementation risk
- dependency risk
- calibration/validation confusion risk
```

The composite is intentionally simple and transparent. The rank order is not a
pure sort by composite score; it also reflects dependency order and the
requirement to keep performance measurement tied to scientific workflows.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Controlled real-site Tschamut/swissALTI3D pilot with embedded performance and terrain observations | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 2 | 18 |
| 2 | Hazard-map semantics and interpretation guide | 5 | 5 | 5 | 3 | 5 | 5 | 2 | 2 | 2 | 22 |
| 3 | Pilot GIS/QGIS package and raster semantics | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 2 | 1 | 20 |
| 4 | Source-zone and block-scenario semantics v1 | 4 | 5 | 5 | 3 | 5 | 5 | 2 | 3 | 3 | 19 |
| 5 | DEM and terrain-representation sensitivity benchmark | 5 | 5 | 4 | 4 | 5 | 5 | 3 | 3 | 3 | 19 |
| 6 | Expanded Chant Sura contact and shape-readiness validation | 5 | 4 | 4 | 5 | 4 | 5 | 3 | 3 | 2 | 19 |
| 7 | Forest/obstacle relevance scoping for Swiss pilot domain | 4 | 4 | 4 | 2 | 4 | 5 | 2 | 3 | 2 | 16 |
| 8 | Validation maturity framework | 4 | 4 | 4 | 5 | 5 | 5 | 1 | 1 | 1 | 28 |
| 9 | Deterministic local parallel execution prototype | 2 | 5 | 5 | 2 | 5 | 5 | 4 | 2 | 1 | 17 |
| 10 | Active shape-contact decision gate | 5 | 3 | 3 | 4 | 4 | 5 | 5 | 3 | 2 | 14 |
| 11 | Terrain/material calibration design with holdout policy | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 3 | 5 | 13 |
| 12 | Trajectory samples table and batched hazard reader | 2 | 4 | 5 | 2 | 5 | 5 | 4 | 2 | 1 | 16 |
| 13 | Chunked/tiled reducer contract and resume semantics | 2 | 4 | 5 | 2 | 5 | 5 | 5 | 2 | 1 | 15 |
| 14 | Fragmentation and broader obstacle implementation scoping | 3 | 3 | 3 | 2 | 4 | 5 | 2 | 3 | 2 | 13 |

## Interpretation

The real-site Tschamut/swissALTI3D pilot remains rank 1 even with only a
medium scientific score. It is the gateway experiment: it tests the Swiss
workflow, exposes confounders, and embeds performance and terrain-
representation observations. It should be described as pilot evidence, not
decisive physics validation.

Hazard-map semantics moves to rank 2 despite low implementation complexity
because conditional map ambiguity is a scientific risk, not just a
documentation problem. Weighting, source-zone normalization, block weighting,
overlapping source zones, release density, terrain-class conditionality, and
conditional-vs-physical probability must be formal before map products are
interpreted or compared.

GIS/QGIS packaging remains immediate. The first pilot needs CRS-bearing,
QGIS-inspectable GeoTIFF outputs with correct transform, nodata, grid
alignment, and semantic labels. Verified COG remains valuable later, but should
not dominate the first local pilot.

Source-zone and block-scenario semantics remain early because source-area
policy and block-population assumptions are central to national hazard mapping.
They should be linked to the hazard-map semantics guide rather than treated as
annual-frequency machinery.

DEM and terrain-representation sensitivity is elevated. Terrain resolution,
smoothing, interpolation, cliff-edge treatment, micro-topography, and vegetation
representation can dominate map patterns and should be studied before
calibration. This is a scientific benchmark, not an optimization exercise.

Shape-readiness validation remains a high scientific priority. Shape is likely
a dominant driver of lateral spread, runout, rotational behavior, and energy
dissipation, but active runtime shape contact remains gated. The immediate
shape work is better Chant Sura evidence and passive shape provenance.

Forest/obstacle relevance scoping stays early because no-forest/no-obstacle
pilot layers may be invalidating or merely limiting depending on the chosen
domain. Implementation remains deferred.

The validation maturity framework has the highest composite score because it
is cheap and reduces overclaim risk. It ranks eighth because it can be done in
parallel with the pilot/reporting stream, but it should be completed before
new public validation claims or publications.

Deterministic local parallel execution is elevated above trajectory Parquet and
SLURM. Local multithreading, order-independent reducers, memory scaling, and
I/O concurrency are the next scaling prototype if the pilot gate shows ensemble
size or output volume pressure. It should remain measurement-driven and
pilot-coupled.

Terrain/material calibration remains deferred. DEM representation, source
zones, shape, forest, and validation maturity must be clearer first; otherwise
calibration would likely fit structural errors.

## Recommended Work Packages

### Best Immediate Work Package

Run the controlled real-site Tschamut/swissALTI3D pilot and write a concise
execution report with embedded performance-readiness and terrain-
representation observations.

Required constraints:

- no tuning;
- no default changes;
- no raw geodata commits;
- no operational hazard or risk claims;
- explicit manifest and visual QA review;
- release-mode throughput, output file/byte counts, no-plot hazard timings,
  memory/file-count observations, and ensemble-size feasibility estimates;
- notes on DEM resolution, interpolation, smoothing, cliff/nodata handling,
  and visible terrain/vegetation representation confounders.

### Best Immediate Documentation/Semantics Work Package

Create the hazard-map semantics and interpretation guide, then align the pilot
GIS package and source-zone/block scenario schemas to it.

Why: Conditional hazard maps can be scientifically misleading if weighting and
normalization are ambiguous. This work is small, high-leverage, and directly
protects the first pilot from overinterpretation.

### Best Medium-Term Scientific Work Package

Build the DEM and terrain-representation sensitivity benchmark, expand Chant
Sura contact/shape-readiness validation, and complete the forest/obstacle
relevance scoping for the selected pilot domain.

Why: These three work packages address the most likely non-parameter drivers of
trajectory realism: terrain representation, block shape/contact evidence, and
domain boundary conditions.

### Best Medium-Term Engineering Work Package

Prototype deterministic local parallel execution only after pilot measurements
show where the bottleneck is. The prototype should include serial/parallel
parity, thread-safe reducers, reproducibility independent of execution order,
and scaling benchmarks versus trajectory count and output volume.

Why: Local parallel scaling is likely a more immediate feasibility issue than
distributed orchestration. It should precede trajectory Parquet and SLURM when
the pilot shows throughput or output pressure.

## What Should Be Paused Or Deferred

Pause or defer:

- public `shape_contact_v0` runtime validation until provenance, diagnostics,
  and non-regression gates are satisfied;
- default change to `sphere_rotational_v1`;
- terrain/material calibration or calibrated class libraries until real-site
  pilot evidence, DEM sensitivity, and holdout policy exist;
- annual-frequency or physical-probability hazard maps until source frequency
  and block-population probability are explicit;
- standalone generic kernel optimization disconnected from pilot workloads;
- trajectory Parquet as a writer-only feature without projected/batched hazard
  reader support and parity/performance evidence;
- SLURM/CSCS orchestration until deterministic local parallelism and local
  chunk/reducer/resume contracts are stable;
- forest/barrier implementation and risk modelling unless the pilot domain
  makes them unavoidable and a separate design is written.

## Roadmap Corrections

1. Reword stale statements that say GeoTIFF export is entirely missing. The
   current gap is verified production raster packaging and COG/tiled output,
   not the absence of any GeoTIFF writer.

2. Treat terrain classes as configured assumptions until calibration evidence
   exists. Do not let terrain-class sidecars become implicit material truth.

3. Keep Tschamut diagnostic evidence separate from physics-selection evidence
   until real terrain, release assumptions, DEM representation, and validation
   splits are cleaner.

4. Keep weighted conditional maps clearly separated from annual-frequency maps.
   Formalize normalization, weighting, source-zone overlap, block weighting,
   and release-density conventions before expanding map interpretation.

5. Add a validation maturity hierarchy and use it in pilot reports so V0
   analytic verification, V1 synthetic realism, V2 impact-level validation, V3
   site-scale hazard-pattern evidence, V4 cross-site generalization, and V5
   operational reproducibility are not conflated.

6. Merge performance-readiness into the pilot workflow. Use release-mode
   builds, explicit grids, no-plot hazard layers, manifest row counts, output
   bytes/file counts, memory observations, and a decision gate before choosing
   local parallelism, trajectory Parquet, Python accumulator work, or tiled
   reducers.

7. Elevate deterministic local parallel execution above trajectory Parquet and
   SLURM if the pilot shows throughput or output-volume pressure.

8. Add DEM/terrain sensitivity before calibration. Multi-resolution,
   smoothing, interpolation, cliff-edge, micro-topography, and vegetation-in-DEM
   effects should be measured rather than silently absorbed into parameters.

9. Add forest/obstacle relevance scoping to the first pilot interpretation.
   Implementation can wait, but the report should say whether no-forest and
   no-obstacle assumptions are acceptable, limiting, or invalidating.

## Final Recommendation

The repository should next use the capabilities it already built, but with
sharper semantics and stronger confounder discipline. The immediate package is
a controlled real-site Tschamut/swissALTI3D pilot with no tuning, embedded
performance and terrain-representation observations, and a hard-nosed results
report. In parallel or immediately after, formalize hazard-map semantics and
prepare the QGIS package. The next scientific axis should be DEM sensitivity,
Chant Sura/shape-readiness evidence, and forest/obstacle scoping before
calibration or public shape runtime work. The next engineering axis should be
deterministic local parallel execution only when pilot measurements justify it.
