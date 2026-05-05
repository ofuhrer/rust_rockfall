# Current-State Gap Analysis And Next Directions

Status: strategic decision record after the recent benchmarking, Parquet
impact-event output, explicit-grid hazard benchmark, probabilistic metadata, and
Swiss pilot-stack work. This document does not change simulation physics,
validation semantics, hazard semantics, output schemas, or defaults.

## Purpose

Recent work made the engineering bottlenecks measurable: impact-event Parquet
reduces file count and byte volume, projected Parquet reads help impact-density
accumulation, explicit grids remove repeated bounds scans, and further local
Python loop optimization has diminishing returns. The next phase should now be
chosen by scientific and workflow value, not by another low-level optimization
pass.

This review asks which next direction best advances an open, research-oriented
probabilistic rockfall hazard-mapping framework for Alpine terrain in
Switzerland while remaining clearly separate from operational hazard assessment.

## Current State

### Simulation Physics

Implemented and verified:

- `translational_v0`: default equivalent-sphere contact with restitution and
  Coulomb friction.
- `sphere_rotational_v1`: opt-in spherical rotational contact with tangential
  impulse coupling, angular velocity, rolling diagnostics, and rolling
  resistance.
- `stochastic_contact_v1`: opt-in impact-local roughness/contact perturbations
  with deterministic seeded randomness.
- `scarring_contact_v1`: opt-in compactable-soil energy-loss layer with
  per-impact scar depth, drag, and energy diagnostics.
- Terrain support: analytic terrain, strict/clamped ESRI ASCII DEMs, proxy
  Tschamut terrain, Chant Sura DEM crops, and swissALTI3D-style metadata
  fixtures.
- Opt-in spatial terrain/material-class lookup for existing contact and
  scarring parameters.

Not implemented:

- non-spherical shape, orientation state, or shape-dependent contact points;
- polyhedral, edge/corner, or multi-contact mechanics;
- calibrated forest, barrier, fragmentation, or vegetation interaction;
- calibrated terrain-class parameter library;
- annual source-frequency or physical probability model.

### Scientific Workflows

The repository now separates verification, calibration, validation, and
hazard-map post-processing:

- analytic and synthetic verification for free flight, restitution, friction,
  rotation, roughness, scarring, DEM interpolation, terrain classes, metadata,
  manifests, and hazard layers;
- Chant Sura trajectory/contact validation with model-selection, extended, and
  held-out subsets;
- Tschamut deposition/runout validation plus a controlled scarring comparison;
- single-impact scarring calibration using proxy and public real-data-derived
  observations;
- impact-event diagnostics sufficient to reconstruct individual terrain impacts;
- documentation separating calibration, validation, and hazard mapping.

The strongest current field-data result is that `sphere_rotational_v1`
consistently improves Chant Sura trajectory-shape and kinetic-energy metrics on
model-selection, extended, and held-out subsets. The improvement is not uniform:
jump-height envelope and rebound-velocity metrics are slightly worse. This
supports `sphere_rotational_v1` as the recommended opt-in trajectory/contact
model, not as a new default.

The weakest current field-data result remains Tschamut. The model under-runs
observed deposition/runout by tens of metres on current proxy terrain, and
impact-level scarring makes the under-run worse by adding energy loss. That is
physically interpretable, but it shows that scarring is not the missing
trajectory-level mechanism for the current Tschamut mismatch.

### Hazard And Probabilistic Workflow

Implemented:

- full-ensemble trajectory output is opt-in;
- trajectory metadata sidecar `trajectory_metadata_table_v1` carries stable
  `trajectory_id`, release/source metadata, block metadata, scenario id, and
  `sampling_weight = 1.0`;
- unweighted reach, deposition, maximum kinetic energy, maximum jump height,
  significant-impact density, and threshold-exceedance layers;
- opt-in `sampling_weighted` conditional reach and trajectory-level exceedance
  layers;
- explicit probability terminology and manifest fields for the current
  sampling-weighted prototype;
- strict rejection of ambiguous weighted configurations.

Not implemented:

- source-zone physical probability or annual release frequency;
- block-size population probabilities;
- weighted deposition density or weighted significant-impact density;
- annual-frequency layers;
- convergence/uncertainty diagnostics for probabilistic maps;
- exposure/vulnerability/risk layers.

The current weighted layers are conditional sampling-weighted diagnostics, not
annual or physical hazard probabilities.

### Swiss Pilot And Geodata Readiness

Implemented:

- swissALTI3D-style terrain metadata with LV95/EPSG:2056 and LN02 provenance;
- deterministic release-zone/source-area metadata and sampling;
- optional terrain-class raster metadata with DEM/class compatibility checks;
- a Tschamut/swissALTI3D real-site pilot template that keeps private DEM crops
  out of git;
- hazard exceedance layers and explicit-grid benchmark/pilot support;
- `run_manifest_v1` records terrain, release-zone, terrain-class, output,
  row-count, timing, and provenance summaries.

Still missing:

- a real manually supplied Tschamut swissALTI3D rerun with documented outcomes;
- CRS-bearing GeoTIFF/COG export for hazard rasters;
- release-zone derivation from slope/geology/inventory data;
- calibrated terrain/material classes;
- GIS-quality visual QA workflow against hillshade/orthophoto layers.

### Performance And Scalability

Implemented:

- manifest-backed timing and throughput counters;
- opt-in Parquet impact-event table `impact_events_table_v1`;
- projected Parquet reads for significant-impact accumulation;
- benchmark profiles (`smoke`, `standard`, `scale`, `custom`);
- explicit hazard grids for controlled benchmarks and pilot-style runs;
- batch/reducer boundary inside the Python hazard builder.

Measured conclusions:

- plotting/report rendering should remain optional and off for production-style
  runs;
- auto-grid bounds discovery was a large avoidable cost and is now removed from
  controlled explicit-grid benchmarks;
- projected Parquet impact accumulation is no longer the main bottleneck;
- trajectory accumulation is still Python-row dominated;
- local helper inlining did not yield stable improvement;
- trajectory Parquet should wait until a projected/batched trajectory reader can
  feed the reducer without converting back to row-wise Python objects.

## State-Of-Practice Gap

Public RAMMS::ROCKFALL material describes a mature operational reference for
rigid-body rockfall simulation: real rock shapes, 3D terrain interaction,
jump/rolling/sliding motion regimes, rotational motion, kinetic energy, terrain
material classes, and statistical trajectory analysis. The comparison below uses
that public description only as a capability benchmark; this project does not
copy proprietary internals or claim equivalence.

| Dimension | Current repository | Gap relative to state of practice | Impact |
| --- | --- | --- | --- |
| Block representation | Equivalent spheres only. | No real/polyhedral shapes, no orientation-dependent contact points. | Major scientific gap for trajectory realism, lateral spread, rolling/tumbling, and energy partitioning. |
| Rotation | Spherical angular velocity and rolling diagnostics. | No full rigid-body orientation or principal-axis behavior for non-spherical blocks. | Important for Chant Sura trajectory/contact realism. |
| Contact regimes | Restitution/friction, optional sphere rotation, roughness, simple scarring. | No multi-contact shape-aware contact, no calibrated terrain interaction law, no forest/barrier/fragmentation. | Limits field realism and model transferability. |
| Terrain/geodata | Small DEMs, metadata fixtures, private-pilot template. | No production GeoTIFF/COG ingestion/export, tile workflow, or real-site pilot result. | Blocking for credible Swiss pilot maps. |
| Terrain classes | Opt-in class raster can override existing parameters. | No calibrated terrain-class parameter sets or field-derived class maps. | Blocking for credible material-dependent hazard products. |
| Release/source model | Manual points and deterministic release-zone sampling. | No source-zone derivation, release-density model, or occurrence-frequency model. | Blocking for probabilistic hazard interpretation. |
| Hazard outputs | Reach, deposition, maxima, impact density, threshold exceedance, sampling-weighted conditional maps. | No CRS-bearing rasters, percentile/uncertainty products, annual-frequency products, or GIS-ready map package. | Major engineering/workflow gap. |
| Validation | Chant Sura trajectory/contact, Tschamut deposition, scarring calibration. | Limited contact labels, small DEM crops, no broad real-site terrain rerun, no calibrated terrain classes. | Scientific conclusions remain research-grade and local. |
| Scalability | Deterministic manifests, explicit grids, Parquet impacts, benchmarks. | No tiled reducers, no trajectory columnar reader, no chunk/resume orchestration. | Not ready for regional or Swiss-wide production runs. |

## Strategic Gap Analysis

### Scientific Model Credibility

Credibility is strongest at the level of transparent equations, analytic tests,
impact traceability, and controlled model comparisons. It is weakest at the
level of field transferability because the model is still equivalent-sphere
based and terrain/material classes are not calibrated.

Main gap: shape-aware rigid-body representation and broader contact validation.

### Trajectory Validation

Chant Sura now provides the most useful validation signal. It shows that
rotational contact matters, but the proxy contact segmentation, small DEM crop,
and equivalent-sphere assumption limit the strength of conclusions.

Main gap: either expand/clean Chant Sura contact labels further or introduce a
shape scaffold that can be tested against existing shape-aware field data.

### Deposition And Runout Validation

Tschamut remains scientifically important because it exposes a persistent
runout/deposition mismatch. It is also currently ambiguous because proxy terrain,
manual release assumptions, shape, forest/vegetation, terrain classes, and
contact parameters are confounded.

Main gap: run the controlled Tschamut/swissALTI3D pilot with real terrain and
document whether the under-run persists.

### Calibration Strategy

The project has good calibration discipline: impact-level scarring calibration
is separated from trajectory/deposition validation, and terrain-class parameters
are not silently tuned. The next calibration step should not be another
parameter search until a real-site pilot clarifies structural bias.

Main gap: a terrain-class calibration design with training/held-out splits,
only after real terrain/source workflows are exercised.

### Probability And Uncertainty

The terminology is now much better than the outputs. `sampling_weighted`
conditional maps are useful, but they are not physical probability or annual
frequency. The framework still needs source-zone frequency, block-population
probabilities, normalization modes, and convergence diagnostics.

Main gap: scenario probability model implementation should remain minimal until
a real-site pilot defines practical source-zone and block scenario needs.

### Real-Site Swiss Workflow

The schema stack exists. The missing evidence is a real local/private
swissALTI3D crop run through the stack. Without that, GeoTIFF export,
terrain-class calibration, and source-zone probability models remain somewhat
abstract.

Main gap: controlled Tschamut/swissALTI3D pilot execution and review.

### Hazard-Map Production

The hazard builder is scientifically traceable and now better instrumented.
However, production map interpretation needs CRS-bearing rasters, reference-grid
discipline, and convergence/uncertainty summaries.

Main gap: GeoTIFF/COG export and a GIS review workflow after the real-site pilot
establishes reference-grid metadata.

### Performance And Scalability

Performance work has reached a useful plateau. The known bottlenecks are clear,
but current small-to-medium workflows are not blocked by them. Further low-level
optimization is lower value than scientific and workflow validation.

Main gap: pause low-level optimization; resume only when a real-site pilot or
larger benchmark shows a blocking failure.

### Usability And Reproducibility

Documentation and manifests are strong. The remaining usability gap is that the
project has many advanced pieces but no single recommended "next scientific
experiment" path for a new contributor.

Main gap: package the next pilot as a clear, reproducible workflow with expected
outputs, caveats, and interpretation.

## Ranked Development Directions

| Rank | Direction | Expected value | Urgency | Risk | Dependencies | Swiss prototype relevance |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Controlled Tschamut/swissALTI3D real-site pilot | Very high: tests whether the Swiss stack resolves the largest current field mismatch ambiguity. | High | Medium | Requires local/private DEM crop and careful provenance. | Directly required. |
| 2 | Shape-aware block-model scaffold | Very high scientific value: addresses the largest physics gap and Chant Sura evidence. | Medium-high | High | Better if informed by real-site pilot and Chant Sura shape data. | Important for credible trajectories. |
| 3 | GeoTIFF/COG hazard raster export | High engineering value: makes pilot outputs GIS-reviewable. | Medium-high | Medium | Needs stable reference grid/provenance from pilot. | Required for practical Swiss map review. |
| 4 | Probabilistic source-zone/block scenario semantics implementation | High long-term value: turns conditional maps into scientifically interpretable probabilistic products. | Medium | Medium-high | Needs real source-zone use case and metadata. | Required before physical/annual maps. |
| 5 | Expanded Chant Sura validation/contact labels | High scientific value: strengthens model ranking and shape validation. | Medium | Medium | Needs more preprocessing and clear contact labels. | Indirect but important. |
| 6 | Terrain-class calibration framework | High, but only after real terrain/source setup. | Medium | High | Requires pilot and held-out validation design. | Required for credible field maps. |
| 7 | Tiled reducers and trajectory columnar input | Medium-high engineering value for larger runs. | Low-medium now | Medium | Needs larger pilot-driven pressure and reader design. | Required for regional scaling, not the next blocker. |
| 8 | CLI/productization | Medium: improves usability and repeatability. | Low-medium | Low | Should follow the pilot workflow shape. | Useful but not decisive scientifically. |

## Recommended Work Packages

### Work Package 1: Real-Site Tschamut/swissALTI3D Pilot Review

Objective:

Run and document the controlled Tschamut/swissALTI3D pilot using a manually
supplied real DEM crop, release-zone metadata, optional terrain classes, and the
existing hazard layers. Compare baseline and `sphere_rotational_v1` without
tuning.

Why this comes first:

- It directly attacks the current Tschamut under-run ambiguity.
- It exercises the Swiss terrain, release-zone, terrain-class, manifest, and
  hazard-layer stack end to end.
- It provides the evidence needed to choose between shape, calibration, or GIS
  export as the next priority.

Deliverables:

- local/private-data run instructions and manifest review;
- baseline vs rotational metrics and hazard-layer comparison;
- explicit statement whether runout/deposition mismatch improves, persists, or
  worsens under real terrain;
- list of data-quality issues: CRS, nodata, release-zone extent, terrain-class
  assumptions, and visual QA gaps.

### Work Package 2: Shape-Aware Block Scaffold Design And Minimal Prototype

Objective:

Introduce an opt-in shape scaffold without changing default sphere behavior:
shape metadata, inertia/orientation state, mass-property diagnostics, and
verification tests before adding complex contact.

Why this is the medium-term scientific step:

- Shape is the largest physics gap relative to modern 3D rockfall practice.
- Chant Sura evidence already shows that adding rotational coupling improves
  trajectory shape/energy even before non-spherical geometry.
- A staged scaffold reduces risk compared with jumping directly to a full
  polyhedral contact solver.

Out of scope initially:

- changing defaults;
- replacing the sphere contact model;
- claiming operational equivalence;
- tuning shape parameters to Tschamut.

### Work Package 3: GIS-Ready Hazard Raster Export

Objective:

Add CRS-bearing GeoTIFF/COG export for hazard layers after the real-site pilot
confirms reference-grid needs. Preserve CSV/ASCII debug outputs.

Why this is the medium-term engineering step:

- The current hazard layers are traceable but not GIS-ready.
- Swiss pilot review needs CRS, transform, extent, nodata, provenance, and
  standard raster formats.
- This is higher value than more Python loop optimization because it makes the
  existing science inspectable in real geospatial tools.

Out of scope initially:

- national tiling;
- cloud/object-store layout;
- risk/exposure layers;
- replacing current debug outputs.

## What To Pause Or Defer

Pause:

- further low-level Python micro-optimization unless a benchmark demonstrates a
  blocking pilot failure;
- writer-only trajectory Parquet without a projected/batched hazard reader;
- broader benchmark matrix expansion unless tied to a concrete workflow
  decision.

Defer:

- making `sphere_rotational_v1` the default;
- annual-frequency hazard maps;
- physical source-probability calibration;
- weighted deposition and weighted impact-density layers;
- terrain-class calibration before a real-site pilot;
- full polyhedral hard-contact dynamics before a shape scaffold;
- Swiss-wide orchestration/HPC until GIS outputs and pilot workflow semantics
  are stable;
- risk mapping until exposure and vulnerability data are explicitly introduced.

## Decision

The next phase should focus on **scientific and workflow credibility**, not
further local performance tuning.

Immediate next work package:

> Run and document a controlled Tschamut/swissALTI3D real-site pilot with
> baseline and `sphere_rotational_v1`, no tuning, full provenance, and hazard
> layer interpretation.

Medium-term scientific work package:

> Design and implement a minimal opt-in shape-aware block scaffold after the
> real-site pilot clarifies terrain/source sensitivity.

Medium-term engineering work package:

> Add CRS-bearing GeoTIFF/COG hazard raster export once the pilot reference-grid
> and provenance requirements are confirmed.

This sequence best balances scientific credibility, Swiss hazard-map readiness,
probabilistic workflow maturity, and implementation risk.

## Sources For State-Of-Practice Context

Public, high-level context only:

- RAMMS::Rockfall project page, WSL/SLF, accessed 2026-05-06:
  <https://ramms.ch/ramms-rockfall/>
- RAMMS::Rockfall user manual download page, WSL/SLF, accessed 2026-05-06:
  <https://ramms.ch/ramms-rockfall/>
- WSL/SLF RAMMS overview, accessed 2026-05-06:
  <https://www.slf.ch/en/services-and-products/ramms-rapid-mass-movement-simulation/>

