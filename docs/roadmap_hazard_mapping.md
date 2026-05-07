# Long-Term Roadmap: Swiss Alpine Rockfall Hazard Mapping

## End Goal

The long-term goal is an independent, open, automated workflow for producing scientifically traceable rockfall hazard maps for Switzerland's Alpine terrain from public geodata, primarily swisstopo.

The first concrete milestone is a valley-scale pilot that demonstrates the full chain from pragmatic release-zone and block-scenario generation through large deterministic trajectory ensembles to GIS-ready hazard outputs. Development should prioritize the largest blockers to that milestone and to eventual national-scale mapping: uncertainty-aware scenario modelling, scalable trajectory execution, reproducible geospatial provenance, and defensible hazard-layer semantics.

The main probabilistic target is pixel-scale intensity-frequency information, or the closest defensible national hazard-map quantity while annual source-frequency assumptions remain immature. The workflow should be designed for efficient single-socket execution, local parallelism, reproducible chunking, a later CSCS/SLURM path, and roughly 10,000 trajectories per release zone where appropriate.

The goal is not to reproduce RAMMS::ROCKFALL internals, clone proprietary workflows, or claim equivalence with any operational tool. RAMMS and related literature are used as scientific context for understanding state-of-the-art modelling concepts, not as implementation targets.

## Current Position

The current `v0.6.1` codebase is a trajectory and hazard-postprocessing core with early Swiss workflow scaffolding, not yet a national hazard-map production workflow. It supports analytic terrain, small DEM fixtures, seeded ensembles, impact diagnostics, opt-in rotational sphere contact, opt-in stochastic contact roughness, opt-in compactable-soil scarring diagnostics, hazard-layer post-processing, probabilistic metadata, GeoTIFF export, and Swiss geodata provenance fixtures.

Recent impact-level work is important because spatial hazard mapping is only credible if the underlying contact, energy, and calibration behaviour can be inspected and challenged. The proxy and Chant Sura single-impact calibration experiments are therefore not a side path; they build the traceability needed before running large ensembles over Alpine terrain.

The current CSV/JSON/ASCII/GeoJSON hazard workflow is a development and
diagnostic workflow. The scaling and data-format migration path toward
large-ensemble and Swiss-scale products is reviewed in
`docs/scalability_and_data_formats_review.md`.

## Hazard Versus Risk

This project currently targets hazard modelling, not risk modelling.

Hazard modelling estimates where rockfall may travel and how intense it may be. Future hazard layers should include, at minimum:

- runout probability;
- deposition density;
- maximum kinetic energy;
- maximum jump height;
- velocity or momentum summaries where useful;
- intensity-frequency or threshold-exceedance summaries where source-frequency semantics allow them;
- scenario uncertainty layers across release, terrain, block, roughness, and contact parameters.

Risk modelling requires exposure and vulnerability information that is outside the current simulator:

- buildings, roads, railways, infrastructure, and people-at-risk layers;
- temporal occupancy or traffic assumptions;
- vulnerability or fragility functions;
- consequence models and decision criteria.

The simulator may eventually provide hazard inputs to risk workflows, but it should not present hazard layers as risk maps unless exposure and vulnerability data are explicitly included and documented.

## Scientific Development Path

### 1. Impact and Contact Credibility

Purpose: make individual impacts explainable before scaling to maps.

Needed work:

- improve impact-normal reconstruction against measured datasets;
- clarify which losses are restitution, friction, scarring, roughness, or terrain effects;
- constrain or calibrate scarring/contact parameters with public impact-level observations;
- keep per-impact diagnostics available for audit.

Current status: first proxy and Chant Sura real-data single-impact experiments exist, but they are exploratory and not operational calibration.

### 2. Terrain and GIS Foundation

Purpose: represent Alpine terrain realistically enough for spatial outputs.

Needed work:

- robust DEM ingestion beyond small ESRI ASCII fixtures;
- CRS-aware coordinate handling;
- GeoTIFF, Cloud-Optimized GeoTIFF, and common Swiss geodata support;
- swisstopo-aware metadata for swissALTI3D terrain tiles and future context
  layers such as swissSURFACE3D, swissTLM3D, geology, and SWISSIMAGE;
- terrain normals, slope/aspect, and terrain-class layers;
- release-zone and source-area representations;
- clear preprocessing provenance for every raster/vector layer.

Current status: small DEM support and a Tschamut proxy terrain exist; production GIS workflows are not implemented.

### 3. Release-Zone and Scenario Definition

Purpose: make ensembles spatially meaningful and nationally repeatable.

Needed work:

- pragmatic release-zone polygons or raster masks from public geodata and documented rules;
- literature-informed sampling of release points, initial velocities, block volumes, and shape classes;
- scenario metadata for return-period or event-family assumptions;
- deterministic seeding by scenario, release cell, and trajectory id.

Current status: deterministic seeded release perturbations exist, but no operational release-zone generation exists.

### 4. Ensemble Orchestration

Purpose: run many independent trajectories without changing the physics kernel.

Needed work:

- single-socket trajectory throughput and local parallel execution as first-order requirements;
- chunked ensemble execution;
- stable per-trajectory seeds independent of execution order;
- resumable outputs;
- summary reducers for hazard layers;
- run and chunk manifests that record configuration hashes, terrain provenance,
  seed policy, output completeness, row counts, file sizes, and reducer inputs;
- optional columnar trajectory/event archives for full-fidelity analysis when
  debug CSV output is too file-heavy;
- later CSCS/SLURM orchestration built on the same chunk and reducer contracts.

Current status: architecture is deterministic and ready for local parallelism and later SLURM orchestration, but MPI, GPU, distributed execution, and production schedulers are deliberately absent.

### 5. Hazard-Layer Generation

Purpose: convert trajectories into reproducible spatial map products.

Current status: a first lightweight post-processing workflow exists in
`scripts/build_hazard_layers.py` and is documented in `docs/hazard_layers.md`.
It writes CSV grids, ESRI ASCII grids, deposition GeoJSON, PNG plots, and a
local HTML report for small synthetic and validation cases. It is intentionally
diagnostic and currently limited by the trajectory outputs supplied to it.

Future raster/vector outputs should include:

- reach or runout probability rasters;
- deposition density rasters;
- maximum kinetic-energy rasters;
- maximum jump-height rasters;
- velocity/momentum summary rasters where justified;
- uncertainty bands or scenario-comparison layers;
- metadata recording model version, configuration hash, source datasets, calibration state, and random seeds.

Candidate export formats:

- CSV/JSON/ASCII/GeoJSON for debug, verification, and small review artifacts;
- Parquet or GeoParquet for optional large tabular trajectory, impact, and
  deposition archives;
- GeoTIFF or Cloud-Optimized GeoTIFF for CRS-aware raster hazard layers;
- GeoPackage, FlatGeobuf, or GeoJSON for release zones, deposits, trajectories,
  and contours depending on size and exchange needs;
- JSON/YAML manifests for reproducibility, chunk status, and audit.

### 6. Calibration and Validation

Purpose: prevent hidden tuning and make model limitations visible.

Needed work:

- keep calibration datasets and validation datasets separate;
- record objective functions, parameter bounds, selected values, and held-out tests;
- validate against analytic cases, synthetic DEMs, controlled experiments, and public field datasets;
- report failure modes as scientific information, not just pass/fail status.

Current status: verification is strong for the v0 model; public-data validation and calibration are early and limited.

### 7. Risk-Workflow Interface

Purpose: support future downstream risk studies without conflating hazard with risk.

Needed work:

- define hazard outputs cleanly enough for external exposure/vulnerability workflows;
- document assumptions required to combine hazard with exposure;
- avoid embedding site-specific consequence logic into the core trajectory simulator.

Current status: no risk modelling is implemented.

## Scope Boundary

This project targets transparent, scalable hazard mapping, not operational warning or risk modelling. It is not validated for emergency planning, engineering design, regulatory decision-making, or national operational production.

Future map layers should carry explicit metadata and disclaimers:

- model version and configuration;
- calibration dataset and validation status;
- terrain and release-zone data provenance;
- ensemble size and random-seed policy;
- known unsupported physics;
- statement that outputs are non-operational hazard products unless independently reviewed and validated for a specific operational use.

## Near-Term Priorities

The next high-impact work should support the Swiss hazard-mapping goal and close the largest gaps to the valley-scale pilot:

1. Build a valley-scale pilot workflow from public geodata with explicit release-zone and block-scenario assumptions.
2. Improve single-socket throughput, local parallelism, chunk manifests, and deterministic reducers toward roughly 10,000 trajectories per release zone where appropriate.
3. Strengthen uncertainty and convergence reporting for weighted conditional hazard layers and intensity-frequency-style products.
4. Improve DEM/terrain handling, GeoTIFF/COG packaging, and CRS-aware visual QA for Swiss workflows.
5. Use Chant Sura, Tschamut, Mel de la Niva, and Swiss pilot evidence to decide which physics gaps matter most, without hidden tuning or operational claims.
