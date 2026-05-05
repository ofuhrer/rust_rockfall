# v0.5.0 Next-Steps Review

Status: current-state planning review for `v0.5.0`. This document does not define new model behavior and does not change validation or calibration semantics.

## Purpose

The project has moved from a minimal spherical rockfall kernel to a broader research workflow with verification, public-data validation, impact diagnostics, calibration experiments, hazard-layer post-processing, and Swiss geodata planning. This review summarizes what is implemented, what has been learned scientifically, and which next steps would add the most value.

The goal remains an independent, open, research-oriented simulator for probabilistic rockfall hazard-map layers in Alpine terrain. The goal is not to reproduce RAMMS internals or to claim operational validity.

## Current Repository State

### Simulation Physics

Implemented:

- Spherical block model with mass, radius, translational state, and rotational diagnostics.
- Analytic terrain: plane, paraboloid, and step terrain.
- Small ESRI ASCII DEM support, including strict and clamped variants for development fixtures.
- Exact constant-gravity free-flight integration.
- Default `translational_v0` impact response with normal/tangential restitution and Coulomb friction.
- Opt-in `sphere_rotational_v1` contact model with sphere rotational coupling and rolling diagnostics.
- Opt-in `stochastic_contact_v1` roughness/contact perturbation model with deterministic seeding.
- Opt-in `scarring_contact_v1` compactable-soil impact energy-loss model with impact-level diagnostics.
- Deterministic release perturbations and ensemble execution with explicit trajectory IDs.

Not implemented:

- Polyhedral or non-spherical contact.
- Nonsmooth hard-contact complementarity.
- Calibrated terrain classes, forest interaction, deadwood, fragmentation, or barrier interaction.
- Production GIS workflows, GeoTIFF/COG output, MPI, GPU, distributed execution, or streaming large-scale orchestration.

### Verification Suite

The repository now has a layered verification suite covering:

- Analytic mechanics: free flight, projectile motion, rebound, frictional stopping, and energy consistency.
- Synthetic terrain/contact cases: flat and inclined planes, step terrain, paraboloid basin, small DEM fixtures, and motion-regime transitions.
- Stochastic behavior: fixed-seed reproducibility, seed-dependent spread, roughness ensembles, and order independence.
- Rotational contact and rolling diagnostics.
- Scarring zero-effect baselines, scaling checks, energy dissipation checks, and impact-event accounting.
- Hazard-layer post-processing unit tests.

The suite is strongest for isolated mechanics and deterministic behavior. It is weaker for terrain realism, shape effects, and field-scale contact sequences because those require better terrain and experimental trajectory segmentation.

### Validation Datasets

Current public-data roles are intentionally separated:

- Chant Sura: primary trajectory/physics reference. The current subset tests reconstructed first-flight trajectory segments, energy evolution, and proxy jump height.
- Lu / ESurf 2019 tables: impact-level scarring calibration reference. These constrain scar-depth and post-impact energy behavior in a limited, public-data workflow.
- Tschamut: deposition/runout distribution validation and comparative baseline/scarring experiments using proxy terrain products.
- swisstopo datasets: future operational geodata inputs for Swiss hazard mapping, not validation datasets.

This separation is scientifically useful: no single dataset currently constrains release generation, full trajectory physics, scarring, terrain effects, and deposition distributions at once.

### Calibration Workflows

Implemented calibration workflows are explicitly separate from validation:

- Historical Tschamut trajectory-level calibration artifacts for v0.3.x behavior.
- Proxy single-impact scarring calibration for controlled sensitivity analysis.
- Real-data single-impact scarring calibration using public Chant Sura / ESurf 2019 tabular observations.

The real-data scarring calibration currently estimates plausible parameter combinations, not validated trajectory-prediction settings. The strongest lesson is identifiability: `scarring_drag_coefficient` and `scarring_layer_density_kgpm3` are structurally confounded because the drag work depends primarily on their product.

### Impact Diagnostics

Optional per-impact CSV/JSON outputs make individual impacts reconstructable. Events include incoming and outgoing velocities, terrain/effective normals, contact/scarring energy stages, scarring depth, area, drag force, uncapped/capped energy loss, and cumulative scarring energy.

The distinction between raw contact events and significant impacts has been clarified. Raw event counts can include low-energy contact chatter; significant-impact counts are better suited for interpretation, calibration, and hazard-layer impact density.

### Hazard-Layer Outputs

The hazard workflow converts trajectory ensembles into diagnostic spatial layers:

- reach probability
- deposition density
- maximum kinetic energy
- maximum jump height
- significant impact density when impact-event files are available

It can consume full ensemble trajectories when cases opt into `ensemble_trajectories_dir` and `ensemble_impact_events_dir`. Outputs are development-oriented CSV/ASCII grids, GeoJSON deposition points, PNG plots, and lightweight HTML summaries.

These are hazard layers only. They are not risk maps because exposure and vulnerability are not included.

### swisstopo / Geodata Readiness

The project is geodata-aware but not yet production GIS-capable:

- `swisstopo_data_strategy.md` identifies swissALTI3D as the primary future bare-earth terrain source.
- swisstopo surface, vector, building, geology, and imagery products are documented by role.
- A terrain-tile metadata schema records CRS, extent, resolution, source, and provenance expectations.
- No large swisstopo datasets are downloaded or committed.

The key engineering gap is turning this metadata strategy into a small, reproducible LV95/LN02 terrain-ingestion pilot.

## Scientific Findings So Far

### Tschamut

Tschamut has been useful for deposition/runout-level behavior, not detailed trajectory physics. Earlier fitted-plane terrain under-ran the observed mean runout by roughly 60 m. The later proxy DEM reduced the mismatch to roughly 31 m in the current basic validation, with observed mean runout near 103 m and simulated mean runout near 72 m.

This shows that terrain representation is a structural source of error, but it does not fully explain the mismatch. The proxy DEM remains an approximate reconstruction, not a measured high-resolution field terrain model.

The Tschamut scarring comparison is scientifically important because it moves in the expected physical direction: scarring dissipates energy and shortens trajectories. Because the baseline already under-runs, transferred impact-level scarring parameters worsen the mean runout mismatch. That does not invalidate scarring as impact physics; it shows that Tschamut trajectory-level behavior is not ready to be improved by adding dissipation without better terrain, release, shape, and contact constraints.

### Chant Sura

The Chant Sura trajectory subset currently validates free-flight reconstruction very well. Reported trajectory errors are near numerical/preprocessing precision, and energy evolution is consistent with ballistic motion.

The limitation is that the selected subset is mostly first-flight behavior. It does not strongly test rebound, rolling, sliding, scarring, or shape-sensitive contact. Candidate model options that affect contact therefore do not materially improve these metrics. This is a dataset-processing limitation, not evidence that contact physics is unimportant.

The next scientific value from Chant Sura requires DEM-backed trajectory segmentation with observed contact/rebound windows.

### Lu / ESurf Scarring Calibration

The real-data scarring calibration demonstrates that public impact-level data can be integrated into the workflow. It also shows that the minimal scarring model is interpretable but underdetermined.

The current best grid-search set is useful as a diagnostic parameter set, not as a field-calibrated terrain model. The model tends to overpredict scar depth while giving a more moderate post-impact energy match. This suggests that the simplified spherical cap geometry, inferred impact normal, and compactable-soil work law are not independently constrained by the available table data.

The most important scarring lesson is that impact-level calibration should stay at the impact level until terrain and trajectory contacts are more observable.

### Hazard-Layer Analysis

Current hazard layers are internally coherent at diagnostic scale:

- Reach probability follows repeated trajectory corridors.
- Deposition density concentrates where trajectories stop.
- Maximum energy tends to occur in acceleration/transit zones rather than final deposition zones.
- Jump-height and significant-impact hotspots can highlight bounce/contact zones.

Scarring reduces energy and reach in the Tschamut comparison, consistent with its dissipative role. The same behavior worsens the already-short baseline runout, so it should not be treated as a validated trajectory-level improvement.

The current max layers are vulnerable to single-trajectory spikes. Future hazard products should include percentile and exceedance layers, not only cell-wise maxima.

### Impact Diagnostics

The synthetic scarring impacts can be reconstructed from logged velocity, normal, energy, and scarring fields. This is a major interpretability improvement. It makes it possible to audit one impact before trusting trajectory-level effects.

The remaining gap is not traceability; it is whether the simplified scarring physics is sufficiently constrained by real impact observations and real terrain normals.

## Gap Analysis

### Physics Gaps

- Shape is still the largest missing physical mechanism after terrain. Spherical blocks cannot reproduce shape-dependent rebound, lateral spreading, tumbling, or angular-momentum effects seen in field experiments.
- Contact remains restitution/friction based, with optional rotational coupling and scarring. It is not a nonsmooth multi-contact solver.
- Scarring lacks shape dependence, torque, slip-dependent drag, terrain-class calibration, and full penetration/rebound interpretation.
- Roughness is contact-stochastic, not yet a spatial terrain roughness or material field.
- Rolling/sliding modes are useful diagnostics but still simplified.

### Dataset Gaps

- Chant Sura is not yet used in a DEM-backed, multi-contact trajectory-validation form.
- Tschamut terrain is still proxy terrain, not a measured high-resolution validation terrain.
- Real impact calibration data constrain only limited impact summaries and may not separate all scarring parameters.
- swisstopo datasets are documented but not yet used in a pilot terrain pipeline.

### Calibration / Validation Gaps

- Contact/scarring/roughness parameters are not validated at trajectory scale.
- Calibration and validation are separated, but model-comparison experiments need stronger observed contact and terrain information.
- Current validation does not yet quantify shape effects or terrain-resolution sensitivity from measured DEMs.
- Hazard-layer outputs are diagnostic and qualitative; they are not yet benchmarked against independent hazard inventories.

### Hazard-Map Generation Gaps

- No release-zone generation from slope/geology/source-area rules.
- No percentile or exceedance hazard layers.
- No CRS-bearing GeoTIFF/COG outputs.
- No provenance manifest tying layers to code version, config hash, seed, terrain source, and calibration status.
- Current rasterization is suitable for small-to-medium artifacts, not Swiss-scale tiled processing.

### Geospatial Integration Gaps

- No production GeoTIFF/COG ingestion in Rust or Python.
- No LV95/LN02 coordinate pipeline beyond metadata design.
- No Swiss terrain tiling/chunking or edge-overlap strategy.
- No alignment with SWISSIMAGE/hillshade QA workflows.

### HPC / Scaling Gaps

- The single-trajectory kernel is designed for deterministic ensembles, but orchestration is still local and serial.
- Ensemble trajectory outputs can become large quickly.
- Hazard-layer accumulation is not streaming/tiled.
- No job-array, restart, chunk manifest, or distributed reduction strategy exists yet.

### Documentation / Tooling Gaps

- The documentation is broad and largely consistent, but the next contributor needs a clearer immediate target.
- Historical review documents are useful, but readers must understand that several are intentionally historical.
- Consistency checks are strong for drift but cannot replace scientific review of dataset assumptions.

## Prioritized Next Steps

### 1. DEM-Backed Chant Sura Contact/Trajectory Validation

Objective: Process a small Chant Sura terrain/trajectory subset so validation includes terrain contact, rebound timing, jump height, and energy evolution across impacts.

Why it matters: Current Chant Sura validation mostly confirms ballistic kinematics. It cannot rank contact, roughness, rotation, scarring, or shape improvements.

Value: Very high scientific value. It turns the primary trajectory dataset into a contact-physics reference.

Complexity: Medium to high.

Risks: DEM alignment, CRS handling, trajectory segmentation ambiguity, and measured-contact uncertainty.

Dependencies: Public Chant Sura archive structure, small DEM fixture, documented coordinate transforms, validation metrics.

Needed for: scientific validation and Swiss pilot mapping. It is not directly sufficient for Switzerland-wide scaling.

### 2. swissALTI3D Pilot Terrain Ingestion

Objective: Implement a small, reproducible LV95/LN02 terrain-ingestion pilot using manually supplied swissALTI3D or equivalent cropped sample terrain, with provenance metadata.

Why it matters: Terrain simplification has already dominated Tschamut interpretation. Swiss hazard mapping needs authoritative terrain inputs.

Value: High engineering and mapping value.

Complexity: Medium.

Risks: Dependency boundary for GDAL/GeoTIFF, tile-size handling, CRS/provenance mistakes, and avoiding large data commits.

Dependencies: swisstopo metadata strategy, internal DEM representation, small sample tile policy.

Needed for: Swiss pilot mapping and Switzerland-wide scaling.

### 3. Release-Zone Schema and Deterministic Source Sampling

Objective: Define release-zone inputs and deterministic sampling from polygons or raster masks, including trajectory IDs tied to release cells and scenarios.

Why it matters: Hazard maps require source zones and ensembles, not one-off release points.

Value: High for hazard-map usefulness.

Complexity: Medium.

Risks: Geology/slope assumptions can become hidden calibration if not documented. Sampling choices can bias reach probability.

Dependencies: terrain metadata, future geology/source-zone inputs, seeded ensemble design.

Needed for: Swiss pilot mapping and Switzerland-wide scaling.

### 4. Streaming / Tiled Hazard Accumulator with Percentile Layers

Objective: Extend hazard-layer post-processing so it can reduce large ensembles in chunks and produce percentile/exceedance layers for energy and jump height.

Why it matters: Cell-wise maxima are sensitive to outliers, and CSV-based in-memory accumulation will not scale.

Value: High engineering value and medium scientific value.

Complexity: Medium to high.

Risks: Merge correctness, deterministic reductions, storage format decisions, and metadata consistency.

Dependencies: ensemble output manifests, hazard-layer schema, CRS-aware grids.

Needed for: Swiss pilot mapping and Switzerland-wide scaling.

### 5. Shape-Aware Block Representation Scaffold

Objective: Add a carefully scoped non-spherical block path, starting with a testable ellipsoid or convex-shape API before full polyhedral contact.

Why it matters: Field experiments show that shape strongly affects runout, lateral spread, rotation, and contact behavior.

Value: Very high scientific value.

Complexity: High.

Risks: Large physics expansion, difficult verification, and potential confusion if introduced before terrain/contact validation can measure the effect.

Dependencies: DEM-backed Chant Sura validation and shape metadata.

Needed for: scientific validation. It is useful but not the first dependency for Swiss pilot mapping.

### 6. Scarring Model Identifiability Refinement

Objective: Improve impact-level scarring experiments by fixing or independently constraining one of `Cd` or layer density, using better impact normals where available.

Why it matters: Current scarring calibration exposes a parameter-identifiability problem.

Value: Medium scientific value.

Complexity: Medium.

Risks: More calibration may not improve trajectory realism without better terrain and shape.

Dependencies: impact diagnostics and real-data table interpretation.

Needed for: scientific validation, not immediate Swiss pilot mapping.

### 7. Spatial Roughness / Terrain-Class Parameter Fields

Objective: Move from stochastic contact roughness to spatially documented roughness/material fields tied to terrain, geology, or land-cover classes.

Why it matters: Real hazard mapping needs spatially varying terrain response.

Value: High eventual value.

Complexity: High.

Risks: Easy to overfit or hide calibration choices. Requires better datasets and source metadata.

Dependencies: geodata ingestion, calibration policy, validation cases.

Needed for: Swiss pilot mapping and Switzerland-wide scaling, but not before terrain ingestion and release-zone design.

### 8. Run Provenance and Configuration Manifests

Objective: Add a standard manifest for verification, validation, calibration, and hazard outputs containing model version, git hash, config hash, seed policy, dataset sources, CRS, and calibration status.

Why it matters: Scientific reproducibility and map-layer traceability depend on knowing exactly how outputs were produced.

Value: High engineering value with low scientific risk.

Complexity: Low to medium.

Risks: Schema churn if overdesigned.

Dependencies: existing diagnostics and consistency checks.

Needed for: scientific validation, Swiss pilot mapping, and Switzerland-wide scaling.

## Recommended Path

### Immediate Next Step

Implement DEM-backed Chant Sura contact/trajectory validation.

This is the highest-leverage next step because the current primary trajectory dataset only verifies free-flight behavior. Without observed terrain/contact windows, the project cannot fairly decide whether rotational contact, roughness, scarring, or future shape models improve trajectory realism. A small, well-documented Chant Sura subset would make model-improvement decisions evidence-based instead of speculative.

Minimum useful scope:

- Select a small public Chant Sura subset with DEM and trajectory data.
- Preserve raw data and create a reproducible processed fixture.
- Define segment-level validation metrics for contact timing, rebound height, trajectory shape, and energy evolution.
- Keep the case optional or small enough for normal checks.
- Do not recalibrate during this step.

### Medium-Term Scientific Step

Add a shape-aware block/contact scaffold after DEM-backed Chant Sura validation exists.

Shape is likely the most important missing physics after terrain/contact observability. However, implementing shape before the validation dataset can see contact behavior would make it hard to judge whether the added complexity helps. The scientific order should be: first make contact validation observable, then add the simplest shape representation that can be verified.

### Medium-Term Engineering Step

Build a swissALTI3D pilot terrain-ingestion workflow with CRS/provenance metadata.

This unlocks the future Swiss pilot mapping path while staying outside core physics. It should start with a small manually supplied or documented sample tile, not a national workflow. The goal should be a reproducible path from authoritative terrain metadata to an internal DEM representation and hazard-layer grid metadata.

## Open Scientific Questions

- How much of the Tschamut runout underestimation is caused by proxy terrain rather than contact, friction, shape, or release assumptions?
- Can Chant Sura contact segments constrain rebound timing, energy loss, and jump height well enough to rank contact-model improvements?
- What is the simplest shape representation that captures the first-order runout and lateral-spread effects seen in experiments?
- Are current scarring depth and energy mismatches caused primarily by impact-normal inference, spherical scar geometry, parameter identifiability, or missing soil mechanics?
- How should terrain roughness and material classes be parameterized without hiding calibration choices?
- Which dataset split can support calibration and validation without leakage across impact-level, trajectory-level, and deposition-level workflows?

## Open Engineering Questions

- Should GeoTIFF/COG ingestion live in a Python preprocessing layer first, or become an optional Rust feature later?
- What is the minimal run-manifest schema that supports reproducibility without over-constraining future workflows?
- When should hazard-layer outputs move from CSV/ASCII grids to GeoTIFF, Parquet, Zarr, or another tiled format?
- How should streaming reductions handle deterministic merging of percentile and exceedance layers?
- What small CI fixtures are sufficient to test CRS, terrain ingestion, hazard-layer metadata, and report generation without downloading large data?
- How should optional large public datasets be discovered, downloaded, cached, and skipped cleanly in local and CI workflows?

## Decision Summary

The repository is now ready for a targeted transition from verification-rich model development to dataset-constrained model selection. The most important next decision is not which new physics to add; it is to make the Chant Sura trajectory validation sensitive to contact and terrain. That will provide the evidence needed to choose between shape, roughness, scarring refinement, and contact-model improvements.

For Swiss hazard-map readiness, the parallel engineering track should focus on authoritative terrain ingestion and provenance. Hazard-layer scaling and release-zone generation should follow once the terrain pipeline is concrete.
