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

The composite is intentionally simple and transparent. It favors work that
creates defensible pilot evidence without violating the repository's no-hidden-
tuning and non-operational boundaries.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Controlled real-site Tschamut/swissALTI3D pilot with embedded performance gate | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 2 | 18 |
| 2 | Pilot GIS/QGIS package and raster semantics | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 2 | 1 | 20 |
| 3 | Source-zone and block-scenario semantics v1 | 4 | 5 | 5 | 3 | 5 | 5 | 2 | 3 | 3 | 19 |
| 4 | Expanded Chant Sura contact and shape-readiness validation | 5 | 4 | 4 | 5 | 4 | 5 | 3 | 3 | 2 | 19 |
| 5 | Forest/obstacle relevance scoping for Swiss pilot domain | 4 | 4 | 4 | 2 | 4 | 5 | 2 | 3 | 2 | 16 |
| 6 | Active shape-contact decision gate | 5 | 3 | 3 | 4 | 4 | 5 | 5 | 3 | 2 | 14 |
| 7 | Terrain/material calibration design with holdout policy | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 3 | 5 | 13 |
| 8 | Trajectory samples table and batched hazard reader | 2 | 4 | 5 | 2 | 5 | 5 | 4 | 2 | 1 | 16 |
| 9 | Chunked/tiled reducer contract and resume semantics | 2 | 4 | 5 | 2 | 5 | 5 | 5 | 2 | 1 | 15 |
| 10 | Fragmentation and broader obstacle implementation scoping | 3 | 3 | 3 | 2 | 4 | 5 | 2 | 3 | 2 | 13 |

## Interpretation

The rank order is not a pure sort by composite score. It also reflects
dependency order. The real-site Tschamut/swissALTI3D pilot remains rank 1 even
with a lower scientific score because it is the gateway experiment: it tests the
Swiss workflow, exposes confounders, and embeds the performance gate needed to
know whether planned ensemble sizes are feasible. It should be described as
pilot evidence, not decisive physics validation.

GIS/QGIS packaging ranks second because the repo now has hazard layers and
lightweight GeoTIFF support, but Swiss pilot review still needs a clear,
CRS-bearing, QGIS-ready product boundary. Verified COG remains valuable later;
for the first local pilot, CRS, transform, nodata, grid alignment, and
inspectability matter more than cloud optimization.

Source-zone and block-scenario semantics rank third because probability labels
are already a misuse risk and because source-zone derivation is an early
hazard-map requirement. Conditional sampling-weighted maps are implemented, but
source-zone frequency, source-area policy, and block-population probability are
not.

Shape-readiness validation ranks fourth and is elevated relative to the earlier
review. External expert assessment reinforces that shape is a dominant driver
of lateral spread, runout, rotational behavior, and energy dissipation. This
does not mean public `shape_contact_v0` should proceed immediately; it means
Chant Sura contact evidence, passive shape provenance, and shape scenario
semantics should advance before calibration.

Forest/obstacle relevance scoping moves earlier because it may be a first-order
boundary condition for a Swiss valley pilot. Implementation remains deferred,
but the pilot report should not interpret no-forest/no-obstacle outputs without
scoping whether that omission matters.

Shape ranks lower than its scientific importance because active runtime shape
work is high-risk right now. The right medium-term shape work is a decision gate
and stronger validation, not an immediate public feature.

Terrain/material calibration ranks low despite high scientific value because it
has the highest calibration/validation confusion risk. It should wait for
real-site pilot evidence and a holdout design.

## Recommended Work Packages

### Best Immediate Work Package

Run the controlled real-site Tschamut/swissALTI3D pilot, then write a concise
execution report with an embedded performance-readiness section.

Why: It exercises the current Swiss geodata, release-zone, manifest, ensemble,
hazard-layer, and throughput stack without changing physics. It directly
informs whether the next branch should emphasize GIS packaging, source-zone
semantics, shape, forest/obstacle treatment, or terrain/material calibration.

Required constraints:

- no tuning;
- no default changes;
- no raw geodata commits;
- no operational hazard or risk claims;
- explicit manifest and visual QA review;
- release-mode throughput, output file/byte counts, explicit-grid no-plot
  hazard timings, and ensemble-size feasibility estimates.

### Best Medium-Term Scientific Work Package

Expand Chant Sura contact/shape-readiness validation and source-zone/block
scenario semantics, then reopen active shape contact only through a formal
decision gate.

Why: The literature and state of practice strongly identify shape and contact as
major realism drivers, while national hazard mapping needs defensible source
areas and block scenarios. The current shape runtime scaffold is not ready for
public validation, so more and cleaner contact/shape evidence should precede
active shape behavior.

### Best Medium-Term Engineering Work Package

Build the pilot GIS package and production raster semantics, then run the
embedded performance gate as part of the pilot. Only after that should the
project choose between trajectory accumulation optimization, trajectory
columnar output, local parallelism, or chunked/tiled reducers.

Why: Swiss pilot maps need CRS-bearing outputs and reviewable packages before
national-scale orchestration. The existing benchmark evidence is strong enough
to justify a performance gate, but not strong enough to pick a specific
optimization path independent of real or representative pilot measurements.

### What Should Be Paused Or Deferred

Pause or defer:

- public `shape_contact_v0` runtime validation until provenance, diagnostics,
  and non-regression gates are satisfied;
- default change to `sphere_rotational_v1`;
- terrain/material calibration or calibrated class libraries until a real-site
  pilot and holdout policy exist;
- annual-frequency or physical-probability hazard maps until source frequency
  and block-population probability are explicit;
- standalone generic low-level kernel optimization until release-mode pilot
  measurements show the kernel is the limiting path;
- trajectory Parquet as a writer-only feature without projected/batched hazard
  reader support and parity/performance evidence;
- SLURM/CSCS orchestration until local chunk/reducer/resume contracts are
  implemented;
- forest/barrier implementation and risk modelling unless the first pilot
  domain makes them unavoidable and a separate design is written. Forest and
  obstacle relevance scoping itself should not be deferred.

## Roadmap Corrections

1. Reword stale statements that say GeoTIFF export is entirely missing. The
   current gap is verified production raster packaging and COG/tiled output, not
   the absence of any GeoTIFF writer.

2. Treat terrain classes as configured assumptions until calibration evidence
   exists. Do not let terrain-class sidecars become implicit material truth.

3. Keep Tschamut diagnostic evidence separate from physics-selection evidence
   until real terrain, release assumptions, and validation splits are cleaner.

4. Keep weighted conditional maps clearly separated from annual-frequency maps.
   The current `sampling_weighted` products are useful but not physical
   probability.

5. Consolidate "next step" documents after the pilot report so future agents do
   not have to reconcile too many historical decision records.

6. Merge performance-readiness into the pilot workflow. The report should use
   release-mode builds, explicit grids, no-plot hazard layers, manifest row
   counts, output bytes/file counts, and a decision gate before choosing
   trajectory Parquet, Python accumulator work, local parallelism, or tiled
   reducers.

7. Add forest/obstacle relevance scoping to the first pilot interpretation.
   Implementation can wait, but the report should say whether no-forest and
   no-obstacle assumptions are acceptable, limiting, or invalidating for the
   selected domain.

## Final Recommendation

The repository should next use the capabilities it already built. The most
valuable immediate package is a controlled real-site Tschamut/swissALTI3D pilot
with no tuning, an embedded performance-readiness gate, and a hard-nosed
results report. If the under-run improves, the next branch should emphasize
GIS/QGIS packaging, source-zone semantics, and domain scoping. If it persists,
the next branch should still preserve the performance gate, but scientific
emphasis should move toward Chant Sura contact/shape evidence and
shape-contact decision gates before any calibration.
