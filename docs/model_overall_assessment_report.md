# Overall Model Assessment Report

Status: research prototype assessment for expert review.

This report summarizes the current scientific and engineering maturity of the simulator and hazard-map workflow. It is written for fast-cycle review: the project is not operationally validated, does not claim parity with state-of-practice tools, and does not present current hazard layers as risk products.

## Current Capabilities

The project currently provides:

- a deterministic Rust rockfall trajectory simulator with analytic and synthetic verification cases;
- default `translational_v0` contact dynamics and opt-in `sphere_rotational_v1` experiments;
- public Chant Sura trajectory/contact validation fixtures;
- public Tschamut all-usable grouped deposition/runout validation;
- passive block-shape metadata parsing, validation, inertia diagnostics, and manifest propagation;
- diagnostic and labelled Level 1/2 hazard layers for reach, deposition density, kinetic energy, jump height, velocity, and significant-impact density;
- opt-in sampling-weighted conditional hazard layers;
- Phase 1 probabilistic map semantics with source-zone, scenario-table, trajectory-metadata, hazard-manifest, and map-package manifest support;
- additive GeoTIFF export for GIS-ready raster review, while Cloud-Optimized GeoTIFF remains explicitly deferred;
- provenance manifests, artifact checksums, execution/scientific status separation, and benchmark documentation.

## Maturity Matrix

| Category | Current maturity | Evidence | Main limitation |
| --- | --- | --- | --- |
| Trajectory realism | Benchmark-ready for small contact fixtures | Chant Sura first-flight/contact/held-out metrics | Small fixture set; rebound, jump, and timing errors remain |
| Deposition realism | Research prototype | Public Tschamut all-runs grouped validation | Default under-runs; rotational sphere over-runs |
| Contact modelling | Research prototype | `translational_v0`, opt-in `sphere_rotational_v1`, roughness/scarring experiments | No active non-spherical contact, fragmentation, forest, barriers, or calibrated material model |
| Shape handling | Experimental metadata scaffold | Passive Tschamut and EOTA221 sidecars; inertness tests | Shape does not affect dynamics |
| Probabilistic semantics | Benchmark-ready for Level 1/2 semantics | Phase 1 validators, trajectory propagation, weighted layers, map package manifests | No physical probability or annual frequency support |
| Hazard-map semantics | Pilot-ready for conditional research maps | Reach, deposition, exceedance, weighted conditional layers, explicit labels | Not annualized; no exposure/vulnerability; not risk |
| GIS interoperability | Research prototype to pilot-ready | Additive uncompressed float64 GeoTIFF export with CRS/nodata/transform metadata | COG polish, compression, regional tiling, and GIS package QA remain |
| Reproducibility/provenance | Benchmark-ready | Manifests, checksums, command provenance, ignored generated outputs | Public raw-data acquisition still external for large datasets |
| Calibration readiness | Research prototype | Grouped metrics and no-tuning failure-mode analysis | No formal calibration protocol or parameter priors |
| Operational readiness | Experimental / not operationally reviewable | Explicit non-operational framing | Missing calibrated physics, annual frequencies, regulatory review workflow, uncertainty, exposure/risk |

## Strengths

- The project is open, deterministic, and reproducibility-oriented.
- The validation workflow separates execution success from scientific pass/fail status.
- Public Tschamut and Chant Sura evidence exposes systematic model behavior instead of hiding it behind tuning.
- Probabilistic map semantics distinguish unweighted diagnostics, sampling-weighted conditional maps, physical probabilities, and annual frequencies.
- Hazard layers are manifest-backed and now export to GIS-readable GeoTIFFs without changing raster values.
- Passive shape metadata creates a clean bridge toward future shape-contact work while proving current physics remains unchanged.

## Weaknesses

- Public Tschamut all-runs validation shows a persistent default under-run of about 35 m mean signed runout error.
- `sphere_rotational_v1` improves some Chant Sura trajectory/contact metrics but strongly over-runs Tschamut.
- Current spherical contact modes do not resolve both contact-level and deposition/runout evidence.
- Terrain/material uncertainty remains confounded with shape/contact effects.
- Passive shape metadata is not active physics.
- Annualized probabilistic hazard maps are not implemented.
- Mel de la Niva is not yet a runnable external validation benchmark.
- GIS interoperability has started with GeoTIFF export but is not yet a complete regional product workflow.

## Systematic Failure Modes

### Tschamut

The default model produces compact reach and deposition fields and systematically under-runs most observed trajectories. Impact-rich and short simulated paths correlate with stronger under-run. The rotational sphere model produces much broader reach, higher kinetic-energy and jump-height envelopes, and strong over-run. This pattern suggests a structural mismatch rather than a simple registration error.

### Chant Sura

The rotational model improves trajectory shape and energy metrics in small DEM-backed contact fixtures, including held-out segments. However, rebound velocity, jump-height envelope, and impact timing errors remain large enough that contact realism should not be considered solved.

### Shape and Terrain Confounding

Tschamut block groups show different errors by block class, but block shape, release path, mass, terrain roughness, and stopping regions are not independently isolated. Shape-contact may help, but terrain/material calibration could also explain part of the mismatch.

## Hazard-Map Readiness

The workflow is ready for research/pilot review of conditional source-zone hazard-map products:

- reach probability;
- deposition density;
- maximum kinetic-energy and jump-height envelopes;
- exceedance layers;
- sampling-weighted conditional variants;
- labelled map packages with explicit non-annualized semantics;
- GeoTIFF export for GIS inspection.

It is not ready for operational hazard mapping because it lacks calibrated source frequencies, annual exceedance semantics, exposure/vulnerability, validated operational thresholds, and reviewed production workflows.

## Probabilistic Semantics Assessment

Phase 1 is a strong foundation for map-product clarity. It prevents unweighted diagnostics from being relabelled as annualized probability products and rejects unsupported annual-frequency configurations. The main scientific gap is not syntax; it is calibrated physical probability and source-frequency evidence.

## GIS Readiness Assessment

GeoTIFF export closes the first practical GIS gap for single-raster review. Current TIFFs are intended to round-trip existing hazard values and carry CRS, affine-transform, NODATA, checksum, and probability-semantics metadata through manifests. Remaining GIS work includes verified COG writing, compression, layer package conventions, regional tiling, source-zone package indexing, map styling, metadata profiles, and practitioner QA workflows.

## Reproducibility Assessment

The project is unusually strong in reproducibility for a research prototype. Manifests record provenance, output identity, validation status, warnings, and generated artifact identities. Large public or licensed datasets remain outside git, with scripts and metadata describing reproducible acquisition and preprocessing.

## Operational Readiness Assessment

The project is not operationally ready. Operational use would require at least:

- reviewed and calibrated terrain/material assumptions;
- validated shape/contact or alternative stopping models;
- public and private benchmark expansion;
- annual source-frequency modelling;
- uncertainty and convergence diagnostics;
- GIS/regulatory product specification beyond single-layer GeoTIFF review;
- practitioner review and independent replication;
- exposure/vulnerability layers for any risk product.

## What Should Not Be Claimed

- Do not claim equivalence to closed-source reference implementations or any proprietary simulator.
- Do not claim operational hazard-map validity.
- Do not call current hazard layers risk maps.
- Do not interpret sampling-weighted maps as annual probabilities.
- Do not present passive shape metadata as shape-aware physics.
- Do not use the Tschamut rotational over-run as a default contact-model selection.
- Do not tune parameters after seeing benchmark outcomes without a documented calibration protocol.

## Comparison With Publicly Documented State of Practice

Publicly documented state-of-practice rockfall tools are ahead in mature operational workflows, active block-shape/contact treatment, practitioner GIS integration, terrain/material parameterization, and field-calibration practice. This project is stronger in open reproducibility, manifest discipline, no-tuning benchmark reporting, explicit probability semantics, and transparent failure-mode analysis.

The strategic goal should not be to copy proprietary workflows. The project can differentiate by remaining open, testable, provenance-rich, and explicit about uncertainty and probability semantics.

## Active Scientific Uncertainties

- Whether active non-spherical shape/contact reduces the Tschamut under-run without causing rotational over-run.
- Whether terrain/material calibration explains Tschamut stopping behavior better than shape/contact changes.
- Whether Chant Sura contact improvements generalize to deposition/runout benchmarks.
- Whether grouped Tschamut failure modes remain stable after additional public data cleaning or external benchmarks.
- What source-zone probability and block-population assumptions are defensible for Swiss pilot maps.

## Roadmap Implications

Recommended expert-review priorities:

1. Review Tschamut grouped failure modes and decide whether active shape-contact design is scientifically justified before implementation.
2. Review Chant Sura rebound, jump, and timing diagnostics to define acceptance criteria for any shape-contact prototype.
3. Define a no-tuning terrain/material calibration protocol before any parameter fitting.
4. Expand Mel de la Niva into a runnable external benchmark to reduce dataset-specific conclusions.
5. Continue GIS productization only as an additive packaging layer around clearly labelled, non-operational map products.

## External Review Focus

Experts should focus on:

- whether current benchmark evidence supports shape-contact implementation as the next physics step;
- whether existing validation metrics isolate contact physics well enough;
- whether source-zone and probability semantics are clear to hazard practitioners;
- whether GeoTIFF outputs and manifests are adequate for GIS review;
- what minimum evidence would be required before any operational pilot discussion.
