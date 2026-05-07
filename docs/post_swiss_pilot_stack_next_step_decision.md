# Post-Swiss-Pilot Stack Next-Step Decision

Status: planning and decision record after the minimal Swiss hazard-mapping stack was added. This document does not define new model behavior, does not change validation or calibration semantics, and does not claim equivalence with proprietary or operational hazard tools.

## Purpose

The repository now has the first Swiss pilot workflow layers needed around the simulator:

- swissALTI3D-style terrain-source metadata and a small LV95/LN02 DEM fixture;
- deterministic release-zone/source-area sampling from a provenance-tracked polygon fixture;
- opt-in terrain/material-class raster lookup for existing contact/scarring parameters;
- additive hazard exceedance layers for kinetic energy, jump height, and velocity.

The question is now what should come next to move toward automated Swiss hazard-map production from public geodata while preserving the project boundaries: independent implementation, transparent provenance, no proprietary-tool equivalence claims, no hidden tuning, and no operational risk or warning claims.

## Current Swiss Pilot Workflow Readiness

The pilot stack is now sufficient for **small reproducible source-area hazard-mapping experiments**. A case can reference a terrain metadata sidecar, generate deterministic release points, apply optional terrain-class parameter overrides, emit ensemble trajectories and impact events, and post-process those outputs into reach, deposition, energy, jump-height, impact-density, and exceedance rasters.

What is ready:

- CRS/provenance contract for tiny LV95/LN02 swissALTI3D-style DEM crops.
- Release-zone metadata with deterministic grid sampling and manifest recording.
- Terrain-class metadata with DEM/class-grid compatibility checks and class coverage summaries.
- `run_manifest_v1` records terrain, release-zone, terrain-class, output, warning, and reproducibility metadata.
- Hazard-layer builder supports full ensemble trajectory inputs, streaming accumulation, explicit grids, and threshold exceedance layers.
- The checked-in pilot fixtures are small, deterministic, and safe for CI.

What is not ready:

- No real swissALTI3D Tschamut or Alpine pilot crop is checked in or wired into a case.
- No GeoTIFF/COG export or CRS-bearing production raster output exists.
- No release-zone derivation from slope, geology, inventory, or field mapping exists.
- Terrain classes are illustrative fixtures, not calibrated material classes.
- Hazard layers are non-operational hazard indicators, not risk maps, warning products, or regulatory hazard-zoning products.
- The physics remains equivalent-sphere based, so shape-controlled spreading, tumbling, contact points, and runout are absent.

Conclusion: the Swiss pilot stack is a credible **contract and fixture layer**. It is not yet a real-site Swiss hazard workflow.

## Remaining Operational Gaps

The current project uses public literature, open datasets, and Swiss operational needs as context. It does not attempt to reproduce proprietary internals.

| Area | Current project state | Remaining national hazard-map gap | Priority |
| --- | --- | --- | --- |
| Terrain input | Small ASCII DEM fixtures plus swissALTI3D-style metadata | Real cropped swissALTI3D pilots, tile workflows, GeoTIFF/COG ingestion/export, hillshade/orthophoto QA | Blocking for Swiss pilots |
| Release/source areas | Deterministic polygon sampling fixture | Source-zone derivation from slope/geology/inventory criteria, scenario definitions, release-density policy | Blocking for hazard mapping |
| Terrain/material classes | Opt-in categorical raster with parameter overrides | Calibrated terrain classes from geology/land-cover/field evidence, terrain-dependent parameter sets | Blocking for credible map products |
| Hazard products | Reach, deposition, maxima, impact density, threshold exceedance layers | CRS-bearing intensity rasters, scenario uncertainty layers, percentile products, map exchange formats | Blocking for GIS use |
| Block geometry | Sphere only | Shape-aware geometry, inertia, orientation, contact points, non-spherical dynamics | Major scientific gap |
| Contact mechanics | Restitution/friction, opt-in sphere rotation, roughness, simple scarring | Multi-contact shape-aware contact, terrain interaction, slip/scarring coupling, calibrated roughness | Major scientific gap |
| Validation | Chant Sura contact subsets, held-out comparison, Tschamut deposition, impact calibration | Broader field validation, real-terrain Tschamut rerun, terrain-class calibration/validation splits | Major scientific gap |
| Scaling | Deterministic ensembles, streaming hazard accumulation, manifests | Chunked/tiled jobs, resumable orchestration, large trajectory/event storage, production geospatial exports | Engineering gap |

## Scientific Credibility

The strongest scientific assets are still transparency, deterministic verification, dataset separation, and impact-level traceability.

Strong points:

- The analytic and synthetic verification suite gives confidence in the implemented equations and deterministic behavior.
- Chant Sura contact comparisons consistently show that `sphere_rotational_v1` improves trajectory-shape and energy metrics on model-selection, extended, and held-out subsets, while not yet justifying a default change.
- Scarring diagnostics are interpretable at single-impact level, and real-data impact calibration is explicitly separated from validation.
- Tschamut experiments show a persistent under-run; enabling scarring shortens trajectories further, which is physically expected but not helpful for the current deposition mismatch.
- Hazard-layer products are now traceable from trajectory/impact/deposition outputs to map layers.

Weak points:

- Equivalent spheres remain a strong simplification for field trajectories where rock shape controls rebound, lateral spread, rolling, and energy partitioning.
- Terrain-class parameters are not calibrated, and terrain source realism has only been exercised through synthetic Swiss-style fixtures.
- Tschamut validation remains on proxy terrain. It does not yet answer whether the simulator performs on real Swiss terrain inputs.
- Chant Sura contact events are still segmented/proxy events rather than a full campaign-scale contact reconstruction.

Scientific credibility is therefore good for **diagnostic evidence and model-comparison experiments**, not for operational hazard assessment.

## Engineering Maturity

The engineering foundation is now stronger than the physics validation:

- The Rust kernel remains deterministic and decoupled from file I/O.
- YAML case parsing, manifests, ensemble outputs, and consistency checks now cover terrain, release zones, terrain classes, and hazard-statistic configuration.
- The hazard builder is streaming-oriented and supports explicit grids, which reduces one major scaling bottleneck.
- CI-scale fixtures exercise the Swiss pilot stack without raw geodata.

The main engineering gap is now **GIS interoperability** rather than basic orchestration. CSV/ASCII products are useful for tests, but real Swiss users will need CRS-bearing GeoTIFF/COG rasters and geospatial vector formats with provenance.

## Option Comparison

### A. Shape-Aware Block Model Scaffold

Objective: introduce opt-in non-spherical geometry and orientation scaffolding without changing default sphere behavior.

- Scientific value: very high. Shape is the dominant missing physics for trajectory realism, lateral spread, rolling/tumbling, and full rigid-body block representation.
- Engineering value: medium. It prepares the state, geometry, and contact APIs for future non-spherical dynamics.
- Capability gap addressed: block representation, rotational dynamics, shape-dependent contacts.
- Complexity: high.
- Risk: high. If implemented too early, shape effects may be confounded with uncalibrated terrain classes and still-proxy field terrain.
- Dependency on current Swiss pilot stack: moderate. The stack can already run experiments, but real-site terrain and broader Chant Sura validation would make shape results more interpretable.

### B. GeoTIFF/COG Export And GIS Interoperability

Objective: export hazard layers and metadata in CRS-bearing geospatial formats suitable for QGIS and Swiss pilot review.

- Scientific value: medium. It does not improve physics, but it prevents map interpretation errors from CRS/extent ambiguity.
- Engineering value: very high. It closes the main post-pilot workflow gap between research outputs and real geospatial review.
- Capability gap addressed: GIS exchange, map-product workflow, geospatial provenance.
- Complexity: medium if implemented in Python with optional raster tooling; higher if forced into the Rust core.
- Risk: medium. Dependency selection and nodata/transform semantics must be handled carefully.
- Dependency on current Swiss pilot stack: high. Terrain metadata, explicit grids, and manifests are now ready to support this.

### C. Expanded Chant Sura Validation

Objective: increase trajectory/contact coverage and improve observed contact segmentation for model ranking.

- Scientific value: high. It would test whether rotational, roughness, scarring, and future shape models generalize across more contacts and terrain locations.
- Engineering value: medium. It improves preprocessing and validation metrics rather than production workflows.
- Capability gap addressed: validation breadth and contact-physics evidence.
- Complexity: medium.
- Risk: medium. Segment-boundary contact proxies may remain the limiting factor unless additional raw observations can be processed.
- Dependency on current Swiss pilot stack: low. It mainly depends on Chant Sura data preprocessing.

### D. Terrain-Class Calibration Framework

Objective: define explicit calibration experiments for terrain/material-class parameter sets using held-out validation splits.

- Scientific value: high. Terrain-dependent parameters are essential for realistic hazard mapping.
- Engineering value: high. It would make terrain classes auditable rather than decorative.
- Capability gap addressed: terrain-dependent parameters and calibration workflow.
- Complexity: medium to high.
- Risk: high. Calibration can easily become hidden tuning if real-site terrain and independent validation are weak.
- Dependency on current Swiss pilot stack: high. The schema and class lookup now exist, but real data and held-out splits are not yet strong enough.

### E. Tschamut/swissALTI3D Real-Site Pilot

Objective: run a controlled Tschamut or similar real-site case with a manually supplied real swissALTI3D crop, source-area metadata, optional terrain classes, and hazard layers.

- Scientific value: high. It directly tests whether the new Swiss pilot stack reduces the proxy-terrain ambiguity behind the Tschamut under-run.
- Engineering value: high. It exercises terrain ingestion, release zones, manifests, hazard layers, and GIS-readiness together.
- Capability gap addressed: real terrain workflow, release/source scenario, hazard-map stack, terrain-class provenance.
- Complexity: medium.
- Risk: medium. Results may still be poor because shape, forest, and calibrated terrain parameters are missing; that is scientifically useful if documented.
- Dependency on current Swiss pilot stack: very high. This option is exactly what the stack was built to enable.

## Explicit Answers

### Is shape now the dominant missing physics?

**Yes for trajectory realism, but not as the immediate workflow blocker.** The evidence from Chant Sura and the literature both point to shape as the largest remaining physics gap. However, implementing shape before a real-terrain Swiss pilot risks mixing geometry errors with terrain, source, and parameter uncertainties. Shape should be the next medium-term scientific development, not the immediate post-pilot infrastructure step.

### Is GIS interoperability now the main engineering gap?

**Yes.** The pilot stack can represent terrain metadata, release zones, terrain classes, ensemble outputs, and exceedance layers, but the products are still CSV/ASCII/GeoJSON development artifacts. For Swiss hazard-map review, CRS-bearing GeoTIFF/COG raster export and GIS-compatible vector/provenance packaging are now the main engineering gap.

### Is calibration now more important than new physics?

**Not yet.** Calibration is important, but calibrating terrain classes or scarring before a real-terrain pilot and stronger contact validation would likely fit structural errors. The next calibration work should be designed after a real-site terrain/source workflow exposes what remains biased under transparent inputs.

### Is the current Swiss pilot stack sufficient for a real-site Tschamut rerun?

**It is sufficient for a controlled research rerun, not for an operational validation.** The stack can accept a small manually supplied swissALTI3D-style crop, deterministic source-area metadata, terrain-class fixtures, ensemble outputs, and hazard layers. It is still missing real Tschamut terrain preprocessing, field-derived source areas/classes, GIS export, and shape/forest physics. A Tschamut/swissALTI3D rerun is now feasible as a diagnostic experiment.

## Recommendation

### Immediate Next Step

**Run a controlled Tschamut/swissALTI3D real-site pilot, with GIS-export preparation kept minimal.**

This is the highest-value next step because it uses the completed Swiss pilot stack for its intended purpose: replacing proxy-terrain ambiguity with a real, provenance-tracked terrain input. It can answer whether the persistent Tschamut under-run is still present under a real DEM and explicit source-area assumptions. It will also reveal whether the current terrain-class and hazard-layer schemas are usable before investing in either calibration or shape.

The immediate pilot should:

- use a small manually supplied real swissALTI3D crop or a documented public-compatible equivalent;
- keep raw tiles out of git;
- preserve LV95/LN02 metadata, source tile identifiers, preprocessing notes, and checksums where available;
- define a deterministic source-area fixture and release sampling policy;
- run baseline and recommended `sphere_rotational_v1` comparison cases without retuning parameters;
- generate reach, deposition, energy, jump-height, impact-density, and exceedance layers;
- document whether runout, deposition, and map patterns improve relative to the current Tschamut proxy cases.

This step does not require changing physics. It should be treated as a real-site workflow and data-quality experiment.

### Medium-Term Scientific Step

**Add a shape-aware block model scaffold after the real-site pilot has established terrain/source behavior.**

Shape is the most important missing physics relative to Chant Sura evidence and modern 3D rockfall literature. The first shape step should be deliberately staged:

- add geometry/inertia/orientation metadata without changing defaults;
- expose shape diagnostics and mass properties;
- then add opt-in contact experiments against Chant Sura EOTA shapes;
- preserve the sphere baseline for every comparison.

The goal should be to learn whether shape improves trajectory/contact metrics, not to reproduce a complete polyhedral contact solver immediately.

### Medium-Term Engineering Step

**Add GeoTIFF/COG hazard-layer export and GIS interoperability.**

The current hazard layers are scientifically useful but not GIS-ready. Once the real-site pilot exists, the next engineering priority should be:

- CRS-bearing raster export for reach, deposition, energy, jump height, impact density, and exceedance layers;
- nodata, transform, extent, resolution, and provenance consistency checks;
- optional QGIS-ready vector sidecars for release zones, depositions, and source metadata;
- no heavy dependency in the Rust kernel.

This closes the main engineering gap for Swiss pilot review and eventual tile workflows.

## Deferred Steps

- **Default change to `sphere_rotational_v1`: deferred.** It is recommended for trajectory experiments, but held-out evidence is not broad enough to change global defaults.
- **Terrain-class calibration framework: deferred until after a real-site pilot.** The schema exists, but calibration should not tune around proxy terrain or untested source assumptions.
- **Full production data formats beyond GeoTIFF/COG: deferred.** Parquet/Zarr/large-scale archives should wait until pilot file volumes and reducer semantics are clearer.
- **Full polyhedral hard-contact model: deferred beyond a shape scaffold.** A complete nonsmooth contact solver is a long-term research step.
- **Swiss-wide SLURM orchestration: deferred.** Single-socket throughput, local parallelism, deterministic chunking, manifests, and reducer contracts are active design targets, but national-scale CSCS/SLURM execution needs stable geospatial I/O and pilot semantics first.
- **Risk mapping: deferred.** Exposure, vulnerability, occurrence frequency, and consequence modelling remain outside the current hazard simulator.

## Risks And Assumptions

Risks:

- A real-site Tschamut rerun may still under-run substantially, revealing that shape, forest, release conditions, or terrain-class calibration dominate.
- Real swissALTI3D preprocessing may expose DEM alignment or nodata issues not covered by the synthetic fixture.
- Without GIS export, visual review remains clumsy; without visual review, terrain/source errors may be missed.
- If shape work starts before the real-site pilot, validation conclusions may remain ambiguous.

Assumptions:

- A small real swissALTI3D or swissALTI3D-compatible crop can be obtained manually and kept out of git.
- The current ASCII DEM plus metadata path is adequate for the first real-site rerun.
- The first Tschamut/swissALTI3D pilot should use existing global or explicitly documented terrain-class parameters, not hidden calibration.
- National hazard-map capability means transparent Swiss workflow maturity, not proprietary equivalence, risk modelling, or operational warning readiness.

## Final Decision

After the minimal Swiss hazard-mapping stack, the most valuable next step toward the automated Swiss hazard-map goal is:

> Run a controlled real-site Tschamut/swissALTI3D pilot using the existing terrain metadata, release-zone, terrain-class, ensemble-output, and hazard-exceedance stack, without changing physics or tuning parameters.

This step tests the newly built Swiss workflow under real terrain conditions, directly attacks the current Tschamut terrain/proxy uncertainty, and produces the evidence needed to choose between the next scientific branch (shape-aware blocks) and the next engineering branch (GeoTIFF/COG interoperability).
