# Post-ce3959d Next-Step Decision

Status: planning and decision record after commit `ce3959d` (`v0.5.0`). This document does not define new model behavior, does not change validation or calibration semantics, and does not claim equivalence with RAMMS::ROCKFALL.

## Purpose

The project now has a verified spherical rockfall core, public-data validation workflows, impact-level diagnostics and calibration, diagnostic hazard-layer generation, and first large-ensemble provenance/streaming infrastructure. The next step should be chosen by combining:

- what the current evidence says about model behavior;
- what is needed for Swiss probabilistic hazard mapping;
- what still separates the project from RAMMS-level operational capability.

The decision below uses RAMMS only as the Swiss operational reference and as public grey-literature context. It does not attempt to reproduce RAMMS internals.

## Current State

### Simulation Physics

Implemented:

- `translational_v0`: default spherical-block impact model with normal/tangential restitution and Coulomb friction.
- `sphere_rotational_v1`: opt-in sphere contact model with tangential impulse coupling, angular velocity, rolling diagnostics, and rolling resistance.
- `stochastic_contact_v1`: opt-in impact-local roughness/contact perturbation model with deterministic per-trajectory RNG.
- `scarring_contact_v1`: opt-in compactable-soil energy-loss layer with scar-depth, drag, and impact-level energy diagnostics.
- Terrain support: analytic plane/paraboloid/step terrain, strict small ESRI ASCII DEM, clamped ESRI ASCII DEM patches, Tschamut proxy residual DEM, and Chant Sura small DEM-backed fixtures.

Not implemented:

- non-spherical or convex-polyhedral rock geometry;
- orientation-dependent contact points;
- nonsmooth multi-contact complementarity;
- calibrated spatial terrain classes;
- forest, obstacles, barriers, fragmentation, or operational GIS workflows.

### Scientific Workflow

Implemented:

- layered analytic, synthetic, stochastic, rotational, scarring, DEM, and hazard-layer verification cases;
- Chant Sura trajectory and DEM-backed contact validation subsets;
- deterministic held-out Chant Sura contact split with baseline and rotational comparison;
- impact-level scarring calibration using proxy and public Chant Sura / ESurf 2019 derived observations;
- Tschamut deposition/runout validation and baseline-vs-scarring comparison;
- documentation separating calibration, trajectory validation, deposition validation, hazard mapping, and operational geodata.

The strongest current field-data result is that `sphere_rotational_v1` improves Chant Sura trajectory shape and kinetic-energy metrics on both the model-selection and held-out subsets, while slightly worsening jump-height and rebound-velocity metrics. This supports an opt-in recommendation for trajectory/contact experiments, not a default change.

### Engineering Workflow

Implemented:

- deterministic ensemble execution with explicit case/trajectory IDs and seed derivation;
- representative trajectory CSVs, optional full ensemble trajectory directories, and optional ensemble impact-event directories;
- per-impact event diagnostics sufficient to reconstruct velocity and energy stages for individual impacts;
- hazard-layer workflow for reach probability, deposition density, maximum kinetic energy, maximum jump height, and significant-impact density;
- streaming hazard accumulation in Python, including explicit-grid mode for future tile workflows;
- `run_manifest_v1` sidecars with model version, git/config provenance, seed policy, output summaries, warnings, and completion status;
- local hooks and consistency checks that protect generated-output hygiene and schema/documentation drift.

The engineering foundation is now strong enough for small-to-medium pilot experiments. It is not yet a production Swiss-wide workflow.

## Scientific Evidence Reassessment

### What Is Well Verified

- Free-flight kinematics, energy diagnostics, restitution, frictional stopping, deterministic seeding, and basic DEM interpolation are well covered by analytic and synthetic tests.
- `sphere_rotational_v1` has targeted tests for energy behavior, Coulomb caps, rolling diagnostics, and deterministic behavior.
- `scarring_contact_v1` is traceable at the single-impact level: impact events expose incoming/post-contact/post-scarring energies, scar depth, drag force, and capped energy loss.
- Hazard-layer accumulation is internally consistent for diagnostic ensembles and now avoids holding full trajectory/impact row sets in memory.

### What Remains Uncertain

- Field-scale contact timing, rebound velocity, and jump-height realism remain weakly constrained because Chant Sura contact events are segment-boundary proxies and still use equivalent-sphere geometry.
- Tschamut remains deposition/runout-level validation on proxy terrain. It does not yet isolate whether runout error comes from terrain, release conditions, contact parameters, shape, forest/vegetation, or missing terrain classes.
- `scarring_contact_v1` is useful for impact-level analysis, but its real-data calibration is underdetermined. The current drag coefficient and layer-density parameters are confounded, and scar depths are not matched well with an equivalent sphere.
- Hazard layers are diagnostic and traceable, but not yet stable enough for design-style intensity products because percentile/exceedance layers, release-zone generation, CRS-bearing rasters, and terrain provenance workflows are incomplete.

### What Is Clearly Not Working

- Tschamut still under-runs observed mean runout by roughly tens of metres. The proxy DEM reduced earlier preprocessing artifacts but did not eliminate the structural bias.
- Transferring the impact-level scarring parameter set to Tschamut worsens runout, as expected from adding energy loss to a baseline that already stops too early.
- Roughness and scarring do not currently improve Chant Sura trajectory shape/energy metrics relative to baseline; they may affect deposition or uncertainty, but they are not yet the mechanism that explains trajectory realism.

### Current Physics Conclusions

- `sphere_rotational_v1` is sufficiently supported as the recommended opt-in contact model for trajectory/contact experiments. It is not sufficiently supported as a new default.
- Terrain/contact observability remains the main bottleneck for interpreting validation results. Better DEMs and contact segmentation are prerequisites for stronger physics decisions.
- Scarring is useful beyond toy examples as an impact-level diagnostic and calibration workflow, but not yet as a trajectory-level improvement.
- Shape is now the dominant missing physics relative to modern 3D rockfall theory, but adding shape before terrain/release/geodata infrastructure is ready would make validation harder to interpret.

## RAMMS Gap Analysis

### Core Physics

| Aspect | RAMMS::ROCKFALL public description | Current model | Gap |
| --- | --- | --- | --- |
| Degrees of freedom | Six primary velocity states: three translational and three rotational; orientation and rotational speed enter rock-ground interaction. | Translation plus angular velocity; no orientation state for shape, sphere-only rotation. | Partial rotation only. No full rigid-body orientation dynamics for non-spherical blocks. |
| Block representation | Convex hull polyhedra from idealized or laser-scanned point clouds; equant, platy, columnar, and real shapes. | Equivalent spheres only. | Critical physics gap. Shape controls contact points, runout, lateral spread, rebound, and rolling/skipping. |
| Contact model | Hard-contact rigid-body formulation with contact forces at edges/corners, Coulomb friction, slip-dependent coefficients, and scarring. | Restitution/friction contact; opt-in sphere rotational impulse; opt-in simple scarring energy loss. | No multi-contact solve, no edge/corner contact, no shape contact frames, no full slip-dependent scarring law. |
| Motion regimes | Sliding, rolling, skipping, and jumping are explicitly represented; stopping requires transition to rolling/sliding. | Flight, impact/contact, sliding, rolling/stopped diagnostics; simplified fixed-step transitions. | Regime labels are useful but not yet a full state machine with physically complete transitions. |
| Energy dissipation | Terrain/soil categories with soil strength and drag coefficients; forest and barrier interactions; scarring and frictional dissipation. | Global restitution/friction, impact roughness, optional simple scarring, optional rolling resistance. | Missing terrain-class parameter fields, spatial variability, vegetation, obstacles, and calibrated material mapping. |
| Rotation | Full rigid-body rotational behavior tied to rock shape and orientation. | Sphere angular velocity and rolling residual; no principal-axis behavior. | Missing non-spherical angular momentum and shape-dependent torque arms. |

### Terrain And Geodata

| Aspect | RAMMS::ROCKFALL public description | Current model | Gap |
| --- | --- | --- | --- |
| DEM input | High-resolution DEM is central; public manual recommends roughly 0.5-5 m resolution for meaningful complex-terrain results; supports ASC/TIF/XYZ workflows. | Small ASCII DEM fixtures, clamped patches, Tschamut proxy DEM, Chant Sura small crop. | No production GeoTIFF/COG ingestion, no tile-edge workflow, no robust CRS pipeline. |
| Terrain classes | Soil/ground category polygons with material parameters such as soil strength and drag; default categories including surface soil, talus, boulder field, bedrock, snow, forest-related classes. | No spatial terrain-class raster/vector support. Scarring parameters are global per case. | Blocking for terrain-dependent calibration and Swiss pilot realism. |
| Release zones | Points, lines, and polygons; scenario-based release setup with rock shape/size parameters. | Manual release points and deterministic perturbations. | No source-area polygons, release-density logic, slope/geology masks, or scenario release manifests. |
| Swiss geodata | Operational workflows use georeferenced DEMs and maps. | swisstopo data strategy and metadata schema exist; no pilot ingestion yet. | Need first swissALTI3D pilot tile ingestion and provenance-preserving conversion. |

### Output And Hazard Mapping

| Aspect | RAMMS::ROCKFALL public description | Current model | Gap |
| --- | --- | --- | --- |
| Core outputs | Trajectories, jump heights, velocities, kinetic energy, runout, rotational velocity, scar depth, statistical reports. | Trajectory CSV, diagnostics JSON, impact events, hazard rasters for reach, deposition, max energy, max jump height, significant impacts. | Good diagnostic overlap, but no mature percentile/exceedance intensity products. |
| Statistics | Mean, median, Q90/Q95/Q99, maximum, histograms/CDFs, line/barrier reports, reach probability. | Basic grid layers and reports; cell maxima and densities; no Q95/Q99 layer family yet. | Percentile/exceedance hazard layers are needed before design-style map interpretation. |
| GIS exchange | GeoTIFF export and GIS-oriented workflows are described in the RAMMS manual. | CSV grids, ESRI ASCII, GeoJSON, PNG/HTML, metadata/manifests. | Need CRS-bearing GeoTIFF/COG or equivalent geospatial products for Swiss pilots. |

### Calibration And Validation

| Aspect | RAMMS::ROCKFALL public description | Current model | Gap |
| --- | --- | --- | --- |
| Calibration basis | Years of experiments and application testing; terrain/soil parameters based on case studies and real-scale experiments, with cautions. | Analytic verification, Chant Sura trajectory/contact validation, Lu/ESurf scarring calibration, Tschamut deposition validation. | Strong transparency but limited breadth; no calibrated terrain-class parameter library. |
| Scenario interpretation | Engineering workflows compare scenarios, shapes, release configurations, and terrain categories. | Controlled case comparisons exist, but scenario management is early. | Need scenario/release-zone schema and comparative reports tied to provenance manifests. |
| Operational status | Used as an operational engineering tool with professional judgement and validation cautions. | Experimental research software only. | Operational gap is intentional and should remain explicit. |

## Critical Gaps

### Blocking For A Swiss Pilot

1. **Authoritative terrain ingestion and CRS/provenance.** A Swiss pilot cannot rely on proxy DEMs or repository fixtures. It needs swissALTI3D or equivalent cropped DEMs with LV95/LN02 metadata, tile provenance, and deterministic conversion to internal terrain.
2. **Release-zone representation.** Hazard mapping needs source areas and systematic release sampling, not only hand-entered release points.
3. **Spatial terrain/material classes.** Even a pilot needs a transparent way to assign bedrock/talus/soil/forest-like parameters or to state that they are deliberately uniform.
4. **Percentile/exceedance hazard layers.** Cell-wise maxima are diagnostic but too unstable for map-style interpretation.

### Important But Not Blocking

1. **Shape-aware block model.** This is the largest physics gap versus RAMMS and the strongest candidate for improving trajectory realism, but it can be piloted only after terrain/contact data are well enough controlled.
2. **Better Chant Sura contact labels.** Directly measured or more robustly inferred contacts would improve model ranking.
3. **GeoTIFF/COG output.** Required for exchange beyond the repo, but CSV/ASCII plus manifests remain acceptable during algorithm development.
4. **Terrain-class calibration framework.** Needed before field-like hazard maps are credible, but should follow a pilot terrain/release schema.

### Long-Term Research

1. Convex-polyhedral hard-contact dynamics and robust orientation integration.
2. Nonsmooth multi-contact complementarity.
3. Forest/tree interaction, barriers, fragmentation, and protection structures.
4. Distributed/HPC job orchestration and columnar trajectory/event archives.
5. Risk mapping with exposure and vulnerability data.

## Next-Step Options

| Option | Scientific value | Engineering value | RAMMS gap addressed | Complexity | Risk |
| --- | --- | --- | --- | --- | --- |
| A. Swiss terrain-ingestion pilot (`swissALTI3D`) | High: tests terrain realism and removes proxy-terrain ambiguity. | Very high: establishes CRS/provenance/tile contracts. | DEM/geodata foundation, Swiss operational input workflow. | Medium. | Requires careful raw-data policy and CRS discipline; does not directly improve physics. |
| B. Shape-aware block model | Very high: addresses largest physics gap and Chant Sura shape evidence. | Medium: expands state/contact architecture. | Convex shape, orientation, shape-dependent runout/lateral spread. | High to very high. | Easy to destabilize verified sphere model; validation ambiguous without better terrain/contact data. |
| C. Expanded Chant Sura validation | High: improves contact-model evidence and future shape validation. | Medium: improves dataset tooling. | Calibration/validation breadth, observed contact behavior. | Medium. | Limited by segment-boundary proxies and small DEM crops unless more raw data are processed. |
| D. Production data formats (Parquet/GeoTIFF) | Medium: supports larger ensembles and map exchange. | High: improves scaling and GIS interoperability. | Output/statistics/GIS workflow. | Medium. | Premature if schemas, release zones, and terrain ingestion are not stable. |
| E. Terrain-class / calibration framework | High: separates material behavior from global coefficients. | High: needed for scenario workflows. | RAMMS-like terrain categories and soil parameters. | Medium to high. | Parameter tuning can become hidden calibration if release/terrain data are weak. |

## Decision

### Immediate Next Step

**Implement a minimal Swiss terrain-ingestion pilot around swissALTI3D-style DEM metadata and cropped LV95/LN02 terrain patches.**

This is the most valuable immediate step because terrain ambiguity is blocking both scientific interpretation and Swiss hazard-map progress. Tschamut still under-runs on proxy terrain, Chant Sura contact validation is constrained to small fixtures, and RAMMS-level Swiss workflows depend first on high-resolution georeferenced DEMs. A terrain-ingestion pilot closes a foundational gap without changing simulation physics or defaults.

The minimal pilot should:

- accept a manually supplied small swissALTI3D-style DEM crop or metadata fixture;
- validate CRS, vertical datum, extent, resolution, nodata, and provenance metadata;
- convert or reference the crop through the existing terrain abstraction;
- produce a manifest-linked terrain source record;
- run one small deterministic synthetic/pilot case;
- keep large raw swisstopo data ignored and out of CI.

This is not a full GIS system. It is the smallest step that replaces proxy-terrain ambiguity with a reproducible Swiss terrain contract.

### Medium-Term Scientific Step

**Design a shape-aware block-model scaffold after the terrain pilot is stable.**

Shape is the largest physics gap versus RAMMS and the literature. The Chant Sura decision already shows rotational coupling helps shape and energy metrics even for spheres; the next physically meaningful extension is to represent non-spherical geometry, inertia, orientation, and contact-point variability. However, this should follow the terrain pilot so failures can be attributed to shape/contact rather than DEM/provenance ambiguity.

The first shape step should be a scaffold, not a full RAMMS-like polyhedral solver:

- introduce orientation and inertia APIs behind opt-in geometry types;
- start with ellipsoid or simple convex-polyhedron metadata and diagnostic mass properties;
- add verification tests for orientation/inertia without changing default sphere behavior;
- only then add contact detection and validation against Chant Sura shapes.

### Medium-Term Engineering Step

**Add percentile/exceedance hazard layers plus CRS-bearing raster export once terrain metadata are stable.**

The current hazard layers are useful diagnostics. RAMMS-style map interpretation relies heavily on spatial statistics and quantiles rather than only maxima. The next engineering layer should add Q90/Q95/Q99 or exceedance rasters for kinetic energy, jump height, and velocity, then export them with CRS/provenance metadata. GeoTIFF/COG should wait until the terrain pilot proves the metadata contract.

## Why Other Steps Are Deferred

- **Making `sphere_rotational_v1` the default** is deferred because held-out evidence improves shape/energy but worsens jump/rebound metrics and remains small.
- **Trajectory-level scarring calibration** is deferred because Tschamut already under-runs and scarring worsens that bias. Scarring should remain impact-level until normal/contact/shape assumptions improve.
- **Full shape-aware contact** is deferred as the immediate step because it is high-risk without stronger terrain and contact observability.
- **Parquet/GeoTIFF/COG-first engineering** is deferred because formats should follow stable terrain, release-zone, and hazard-layer schemas.
- **Terrain-class calibration** is deferred until there is a pilot terrain/release workflow where spatial material assignments can be audited instead of tuned implicitly.

## Risks And Assumptions

Risks:

- A terrain-ingestion pilot may expose that current DEM normal/interpolation behavior is insufficient for high-resolution Swiss terrain.
- If source-zone sampling is not added soon after terrain ingestion, pilot maps will still be release-point experiments rather than hazard maps.
- Shape effects may remain the dominant physics gap even after terrain improves.
- CRS/provenance mistakes can invalidate map interpretation more quietly than physics errors.

Assumptions:

- swissALTI3D or equivalent small Swiss DEM crops can be obtained manually and kept out of git unless license-compatible and tiny.
- The existing terrain trait and manifest model are adequate for a first pilot without adding GDAL to the Rust core.
- The next development phase should still optimize for transparent research diagnostics, not operational deployment.

## Final Recommendation

The most important next step to close the gap between the current model and RAMMS-level capability for Swiss hazard mapping is:

> Build the first reproducible Swiss terrain-ingestion pilot using authoritative DEM metadata and small cropped LV95/LN02 terrain patches.

This addresses the blocking terrain/geodata gap, supports future release-zone and hazard-layer workflows, and creates a stable foundation for the later high-impact physics step: shape-aware rock representation. It also keeps the project aligned with its purpose: an independent, open, research-oriented hazard-mapping tool, not a RAMMS clone.
