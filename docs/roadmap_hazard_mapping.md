# Long-Term Roadmap: Probabilistic Alpine Rockfall Hazard Mapping

## End Goal

The long-term goal is an independent, open, research-oriented rockfall simulation tool capable of producing scientifically traceable probabilistic rockfall hazard-map layers for Alpine terrain in Switzerland.

The goal is not to reproduce RAMMS::ROCKFALL internals, clone proprietary workflows, or claim equivalence with any operational tool. RAMMS and related literature are used as scientific context for understanding state-of-the-art modelling concepts, not as implementation targets.

## Current Position

The current `v0.4.0` codebase is still a trajectory-scale research core. It supports analytic terrain, small DEM fixtures, seeded ensembles, impact diagnostics, opt-in rotational sphere contact, opt-in stochastic contact roughness, and opt-in compactable-soil scarring diagnostics.

Recent impact-level work is important because spatial hazard mapping is only credible if the underlying contact, energy, and calibration behaviour can be inspected and challenged. The proxy and Chant Sura single-impact calibration experiments are therefore not a side path; they build the traceability needed before running large ensembles over Alpine terrain.

## Hazard Versus Risk

This project currently targets hazard modelling, not risk modelling.

Hazard modelling estimates where rockfall may travel and how intense it may be. Future hazard layers should include, at minimum:

- runout probability;
- deposition density;
- maximum kinetic energy;
- maximum jump height;
- velocity or momentum summaries where useful;
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
- GeoTIFF and common Swiss geodata support;
- terrain normals, slope/aspect, and terrain-class layers;
- release-zone and source-area representations;
- clear preprocessing provenance for every raster/vector layer.

Current status: small DEM support and a Tschamut proxy terrain exist; production GIS workflows are not implemented.

### 3. Release-Zone and Scenario Definition

Purpose: make ensembles spatially meaningful.

Needed work:

- release-zone polygons or raster masks;
- sampling of release points, initial velocities, block volumes, and shape classes;
- scenario metadata for return-period or event-family assumptions;
- deterministic seeding by scenario, release cell, and trajectory id.

Current status: deterministic seeded release perturbations exist, but no operational release-zone generation exists.

### 4. Ensemble Orchestration

Purpose: run many independent trajectories without changing the physics kernel.

Needed work:

- chunked ensemble execution;
- stable per-trajectory seeds independent of execution order;
- resumable outputs;
- summary reducers for hazard layers;
- later optional parallel, HPC, or cloud orchestration.

Current status: architecture is HPC-ready by design, but MPI, GPU, distributed execution, and production schedulers are deliberately absent.

### 5. Hazard-Layer Generation

Purpose: convert trajectories into reproducible spatial map products.

Future raster/vector outputs should include:

- reach or runout probability rasters;
- deposition density rasters;
- maximum kinetic-energy rasters;
- maximum jump-height rasters;
- velocity/momentum summary rasters where justified;
- uncertainty bands or scenario-comparison layers;
- metadata recording model version, configuration hash, source datasets, calibration state, and random seeds.

Candidate export formats:

- GeoTIFF for raster hazard layers;
- GeoPackage or GeoJSON for release zones, deposits, trajectories, and contours;
- CSV/JSON summaries for reproducibility and audit.

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

## Operational-Use Boundary

This project is experimental research software. It is not validated for operational hazard assessment, emergency planning, engineering design, or regulatory decision-making.

Future map layers should carry explicit metadata and disclaimers:

- model version and configuration;
- calibration dataset and validation status;
- terrain and release-zone data provenance;
- ensemble size and random-seed policy;
- known unsupported physics;
- statement that outputs are research products unless independently reviewed and validated for a specific operational use.

## Near-Term Priorities

The next high-impact work should support the hazard-mapping goal without prematurely building production GIS or HPC infrastructure:

1. Improve impact-level calibration inputs and diagnostics using public measured datasets.
2. Improve DEM/terrain handling with CRS-aware, reproducible preprocessing.
3. Define a minimal release-zone and ensemble-hazard-layer schema.
4. Add lightweight reducers for runout probability, deposition density, maximum kinetic energy, and maximum jump height on small synthetic rasters.
5. Keep all new map-style outputs labelled as research diagnostics until validation improves.
