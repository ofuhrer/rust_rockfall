# Roadmap Recommendation Matrix

Status: ranked recommendation after the current repository review. Scores are
planning guidance, not implementation commitments.

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

Rank is not a pure sort by composite score. It also reflects dependency order,
data availability, and the need to turn current scaffolds into evidence or
executable checks.

## Scoring Matrix

| Rank | Direction | Scientific | Swiss pilot | Hazard workflow | Validation | Reproducibility | Alignment | Impl. risk | Dep. risk | Cal/val confusion risk | Composite |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Controlled real-site Tschamut/swissALTI3D pilot | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 2 | 18 |
| 2 | Hazard-map semantics enforcement | 5 | 5 | 5 | 3 | 5 | 5 | 2 | 1 | 2 | 23 |
| 3 | DEM/terrain sensitivity dry-run fixture | 5 | 5 | 4 | 4 | 5 | 5 | 3 | 2 | 3 | 20 |
| 4 | Pilot GIS/QGIS package fixture | 3 | 5 | 5 | 3 | 5 | 5 | 3 | 2 | 1 | 20 |
| 5 | Source-zone and block-scenario V1 tightening | 4 | 5 | 5 | 3 | 5 | 5 | 3 | 3 | 3 | 18 |
| 6 | Validation maturity framework | 4 | 4 | 4 | 5 | 5 | 5 | 1 | 1 | 1 | 28 |
| 7 | Chant Sura contact and shape-readiness evidence | 5 | 4 | 4 | 5 | 4 | 5 | 3 | 3 | 2 | 19 |
| 8 | Forest/obstacle pilot-domain scoping | 4 | 4 | 4 | 2 | 4 | 5 | 2 | 3 | 2 | 16 |
| 9 | Deterministic local parallel execution and streaming reduction | 2 | 5 | 5 | 2 | 5 | 5 | 4 | 2 | 1 | 17 |
| 10 | Calibration and production data-format decision gates | 3 | 4 | 5 | 3 | 5 | 5 | 3 | 2 | 4 | 16 |

## Interpretation

The controlled Tschamut/swissALTI3D pilot remains first even though its
scientific score is only medium. It is the gateway workflow experiment and
should be reported as pilot/confounder evidence, not decisive validation.

Hazard-map semantics enforcement ranks second because the guide now exists.
The valuable next step is not another semantics narrative; it is executable
manifest/schema protection against unsupported probability, annual-frequency,
operational, or risk claims.

DEM/terrain sensitivity moves above several physics tasks. Terrain resolution,
smoothing, interpolation, cliff/nodata handling, and vegetation representation
can change map patterns before calibration or active shape decisions are
meaningful.

The GIS/QGIS package fixture remains immediate. Lightweight GeoTIFF exists, but
the project still needs an inspectable package boundary with CRS, transform,
nodata, semantic labels, parity, and QA evidence. Verified COG is deferred.

Source-zone/block scenario V1 tightening remains early because national hazard
mapping depends on stable source and block denominators. Current polygon-only
support and additive block labels should be enforced and documented honestly.

Validation maturity has the highest composite score because it is cheap and
reduces overclaim risk. It can be done in parallel with other work, but it
should be in place before any new public validation claim or publication.

Chant Sura/shape-readiness remains the main medium-term scientific work. Active
public shape-contact runtime should stay gated until the evidence base and
diagnostic contract are stronger.

Forest/obstacle scoping is earlier than implementation. The first Swiss pilot
must state whether no-forest/no-obstacle assumptions are acceptable, limiting,
or invalidating for the chosen corridor.

Deterministic local parallel execution is the next engineering scaling
prototype once measurements justify it. It should precede SLURM and should not
be displaced by writer-only trajectory Parquet.

Calibration and production data-format gates rank tenth because they protect
against premature tuning and premature format work. Actual terrain/material
calibration, trajectory sample tables, tiled reducers, and COG production
should follow evidence, not convenience.

## Recommended Work Packages

### Best Immediate Work Package

Run the controlled real-site Tschamut/swissALTI3D pilot if the private DEM and
source-zone inputs are available. The required output is a share-safe
diagnostic report with no tuning, no default changes, no operational claims,
G1-G9 gate status, manifest review, visual QA, performance observations,
terrain-representation observations, and a clear under-run classification.

If private data are not available, the best immediate public work package is
hazard-map semantics enforcement plus a dry-runnable DEM sensitivity fixture.

### Best Medium-Term Scientific Work Package

Build DEM/terrain sensitivity evidence, expand Chant Sura contact and
shape-readiness validation, and scope forest/obstacle relevance for the chosen
Swiss pilot domain. This addresses the most likely non-parameter confounders:
terrain representation, block/contact realism, and domain boundary conditions.

### Best Medium-Term Engineering Work Package

Prototype deterministic local parallel execution and streaming reduction after
pilot or benchmark measurements identify throughput, memory, file count, or
hazard accumulation as the limiting path. Required evidence is serial/parallel
parity, order independence, worker-count independence, memory/file-count
reporting, and scaling curves.

## What Should Be Paused Or Deferred

Pause or defer:

- public `shape_contact_v0` runtime validation;
- any default change to `sphere_rotational_v1`;
- terrain/material calibration or calibrated parameter libraries;
- annual-frequency or physical-probability hazard maps;
- risk maps, expected loss, vulnerability, exposure, or operational approval
  language;
- forest/barrier/fragmentation implementation before pilot-domain scoping;
- trajectory sample Parquet as writer-only output;
- COG/tiled production before local GeoTIFF/QGIS fixture and reducer contracts;
- SLURM/CSCS orchestration before deterministic local parallel and chunk/reducer
  contracts;
- generic kernel optimization disconnected from pilot workloads.

## Roadmap Corrections

1. Treat `docs/hazard_map_semantics.md`, `docs/pilot_gis_package.md`, and
   `docs/dem_terrain_sensitivity_benchmark.md` as scaffolds now present, not as
   missing deliverables. The next gap is executable evidence.
2. Remove or reword stale references to older roadmap files such as
   `current_state_gap_analysis_next_directions.md` where they imply current
   authority.
3. Keep `docs/agent_work_log.md` as an audit log only. It should not outrank
   `AGENTS.md`, `README.md`, `docs/next_development_targets.md`, or this
   matrix.
4. Keep performance measurement coupled to pilot/benchmark workflows.
5. Make validation maturity labels visible before new validation claims.

## Final Recommendation

The repository should now stop accumulating roadmap prose and start producing
evidence from the highest-leverage scaffolds. The best next move is the
controlled Tschamut/swissALTI3D pilot when data are available. Without private
data, the best public next move is to enforce hazard-map semantics and create a
small DEM sensitivity fixture. Medium-term scientific progress should focus on
DEM sensitivity, Chant Sura/shape-readiness, and forest/obstacle scoping.
Medium-term engineering should focus on deterministic local parallel execution
and streaming reducers only after measured bottlenecks justify them.
