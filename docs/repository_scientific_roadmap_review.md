# Repository Scientific Roadmap Review

Status: strategic, scientific, technical, and roadmap review of the current
post-`d4bbdc4` repository state. This document is planning-only; it does not
change simulator behavior, defaults, validation cases, probability semantics,
or operational claims.

## Scope And Sources

This review treats `rust_rockfall` as an independent research codebase for
future Swiss Alpine rockfall hazard mapping from public geodata, primarily
swisstopo. The first concrete milestone remains a valley-scale pilot connecting
source/release and block-scenario semantics, deterministic trajectory
ensembles, uncertainty-aware hazard post-processing, GIS-ready outputs, and a
path to local/HPC scaling.

Inspected source paths include `AGENTS.md`, `README.md`, `CHANGELOG.md`,
`src/`, `validation/`, `verification/`, `hazard/`, `calibration/`, `scripts/`,
`examples/`, `data/datasets.yaml`, checked-in benchmark/report outputs where
small enough to inspect, and the relevant `docs/` and `background/` material.
Key documents include `docs/model_design.md`, `docs/literature_review.md`,
`docs/roadmap_hazard_mapping.md`, `docs/scalability_and_data_formats_review.md`,
`docs/hazard_layers.md`, `docs/hazard_map_semantics.md`,
`docs/pilot_gis_package.md`, `docs/dem_terrain_sensitivity_benchmark.md`,
`docs/probabilistic_scenario_model_design.md`, `docs/validation_plan.md`,
`docs/dataset_strategy.md`, `docs/swisstopo_data_strategy.md`, and
`docs/tschamut_swissalti3d_controlled_pilot_plan.md`.

Local background sources used for scientific claims are:

- `background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`
- `background/Leine-2021-Stability_of_rigid_body_motion-(published_version).pdf`
- `background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`
- `background/RAMMS_ROCK2_Manual.pdf`

## Repository Comprehension

### Implemented Physics

The current public trajectory kernel is an equivalent-sphere model. It supports
spherical mass/radius state, translational and angular diagnostics, exact
constant-gravity ballistic stepping, analytic terrain, strict and clamped ESRI
ASCII DEM fixtures, normal/tangential restitution, Coulomb friction, opt-in
`sphere_rotational_v1` rolling/contact diagnostics, deterministic release
perturbations, opt-in `stochastic_contact_v1`, opt-in
`scarring_contact_v1`, and per-impact/terrain-material diagnostics. Sources:
`README.md`, `CHANGELOG.md`, `docs/model_design.md`, `src/dynamics.rs`,
`src/integrator.rs`, `src/stochastic.rs`, `src/terrain.rs`, `src/validation.rs`.

The `shape_contact_v0` code is a pre-runtime/internal scaffold. It validates
metadata, support selection, diagnostics, and narrow synthetic contact steps,
but is blocked from public fixed-step simulation, validation, and benchmarks.
Sources: `CHANGELOG.md`, `docs/model_design.md`, `docs/shape_contact_v0_experimental_contract.md`,
`src/shape.rs`.

### Unsupported Physics

Unsupported capabilities remain scientifically important:

- active non-spherical trajectory dynamics and orientation evolution;
- convex polyhedral multi-contact, complementarity, persistent edge/face
  contact, and general hard-contact solvers;
- calibrated spatial terrain/material parameter libraries;
- calibrated roughness fields;
- calibrated scarring with drag torque, slip-dependent friction, and terrain
  deformation;
- forest, vegetation, engineered barriers, buildings-as-obstacles, rock sheds,
  nets, fragmentation, and block splitting;
- air drag, acoustic/seismic losses, operational warning, exposure,
  vulnerability, consequences, and risk modelling.

These omissions are visible in `README.md`, `AGENTS.md`,
`docs/model_design.md`, `docs/validation_plan.md`, and
`docs/roadmap_hazard_mapping.md`.

### Validation And Calibration Evidence

Verification is strong for implemented mechanics: analytic cases, synthetic DEM
cases, stochastic reproducibility, scarring diagnostics, terrain parsing, schema
tests, and HPC seed/order fixtures are present under `verification/`, `tests/`,
and `scripts/check_repo_consistency.py`.

Real-data evidence is useful but not operational validation:

- Chant Sura is the strongest trajectory/contact reference. It includes
  first-flight, DEM-backed segmented-contact, extended, held-out, scarring, and
  passive EOTA/shape-readiness materials, but contact observations are still
  proxy segment-boundary events. Sources: `docs/dataset_strategy.md`,
  `docs/validation_plan.md`, `docs/chant_sura_contact_validation.md`,
  `validation/cases/chant_sura_contact*.yaml`.
- Tschamut constrains deposition/runout distributions and failure modes, but
  checked-in cases still use public-derived terrain/proxy products rather than
  an executed private real swissALTI3D crop. Sources: `docs/validation_plan.md`,
  `docs/terrain_model.md`, `docs/tschamut_swissalti3d_controlled_pilot_plan.md`.
- Lu/Chant Sura ESurf tables support impact-level scarring calibration only.
  They do not validate trajectory skill or hazard-map skill. Sources:
  `docs/scarring_real_data_calibration.md`, `docs/dataset_strategy.md`.
- Mel de la Niva is registered as external high-energy/generalization evidence
  but remains optional and workflow-level until local archives are prepared.
  Sources: `docs/dataset_strategy.md`,
  `validation/benchmarks/mel_de_la_niva/README.md`.

Calibration discipline is a strength: calibration lives under `calibration/`,
selected parameters are documented as research diagnostics, and validation
cases are not silently retuned. Sources: `docs/validation_plan.md`,
`docs/dataset_strategy.md`, `calibration/README.md`.

### Hazard-Layer Capabilities

Hazard-layer generation is post-processing, not core physics. Current support
includes reach fraction, deposition density, maximum kinetic energy, maximum
jump height, significant-impact density from CSV or Parquet impact events,
threshold exceedance layers, unweighted standard-error diagnostics,
sampling-weighted conditional layers, CSV/ASCII grids, GeoJSON deposition
points, JSON metadata, `run_manifest_v1`, optional PNG/HTML reports, and
lightweight opt-in GeoTIFF. Sources: `docs/hazard_layers.md`,
`docs/hazard_map_semantics.md`, `scripts/build_hazard_layers.py`,
`tests/probabilistic_phase1.rs`, `tests/test_hazard_layers.py`.

The current gap is not "no hazard maps" or "no GeoTIFF." The gap is verified
pilot packaging: CRS/datum/grid/nodata semantics, QGIS review artifacts,
production COG/tiled outputs, and executable enforcement for all semantic
claims. `docs/pilot_gis_package.md` is now a good documentation scaffold, but
it is not yet an actual package fixture or acceptance test.

### Swiss Geodata Readiness

The repository has a credible Swiss geodata contract layer: swisstopo dataset
roles, LV95/EPSG:2056 and LN02 metadata, small swissALTI3D-style fixtures,
release-zone sidecars, terrain-class sidecars, and a controlled private
Tschamut/swissALTI3D pilot plan. Sources:
`docs/swisstopo_data_strategy.md`, `data/datasets.yaml`,
`docs/swiss_terrain_ingestion_pilot.md`,
`docs/tschamut_swissalti3d_controlled_pilot_plan.md`.

The missing evidence is still execution on a real, provenance-tracked
swissALTI3D crop with frozen release assumptions, manifest review, visual QA,
and performance observations. This will be pilot/confounding evidence, not
decisive physics validation.

### Probabilistic Semantics

The repo now has stronger semantic scaffolding than before: current products
are explicitly `unweighted_diagnostic` or `sampling_weighted_conditional`;
`conditional_probability`, `physical_probability`, and `annual_frequency` are
design-only or unsupported. Sources: `docs/hazard_map_semantics.md`,
`docs/probabilistic_scenario_model_design.md`,
`docs/weighted_hazard_layer_review.md`, `tests/probabilistic_phase1.rs`.

The remaining gap is enforcement coverage. Several semantic expectations are
documented review gates rather than executable manifest/schema checks. That is
acceptable for the current phase but should become near-term work before more
map products are produced.

### Scalability And HPC Readiness

The kernel architecture is deterministic and scaling-aware: single-trajectory
simulation is mostly separated from I/O, seeds derive from global seed, case ID,
and trajectory ID, ensemble order-independence is tested, explicit grids avoid
bounds-discovery scans, and impact-event Parquet/projected reads exist for
impact-density workflows. Sources: `src/simulation.rs`, `src/stochastic.rs`,
`tests/hpc_readiness.rs`, `docs/hazard_throughput_bottleneck_report.md`,
`docs/parquet_impact_benchmark_results.md`,
`docs/performance_benchmark_profile_reference.md`.

Remaining scaling gaps are central to the Swiss goal:

- no public deterministic multithreaded runner;
- no thread-safe streaming reducer;
- no local chunk/resume execution workflow;
- no deterministic tiled reducer merge implementation;
- no trajectory sample table and batched reader for trajectory-derived layers;
- no valley-scale performance budget tied to real pilot workloads;
- no CSCS/SLURM orchestration, correctly deferred until local contracts exist.

Performance should stay coupled to realistic scientific workflows. The repo has
enough benchmark evidence to justify a pilot performance gate, not enough to
pick generic kernel optimization independent of pilot workloads.

### Documentation And Reproducibility Maturity

Strengths: unusually explicit boundaries around validation, calibration,
probability, risk, proprietary equivalence, swisstopo provenance, semantic
versioning, and generated-artifact hygiene. Consistency tooling exists and
passes on the current tree.

Weaknesses:

- too many historical "next step" documents compete for authority;
- `docs/agent_work_log.md` is a large append-only subagent transcript with
  stale/pending entries and should not become a roadmap source of truth;
- `docs/tschamut_swissalti3d_controlled_pilot_plan.md` still references
  `current_state_gap_analysis_next_directions.md`, an older roadmap frame;
- local ignored/generated outputs and duplicate local `* 2.*` files make review
  noisier, though they are not staged;
- no formal validation maturity hierarchy exists yet.

## Scientific Literature And State-Of-Practice Drivers

### Block Shape And Non-Spherical Dynamics

Literature-backed claim: rock shape strongly affects runout, lateral spread,
rolling/tumbling mode, jump height, and energy partitioning; full rigid-body
models represent rocks as convex bodies with mass/inertia/orientation rather
than equivalent spheres. Sources: `docs/literature_review.md`,
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`,
`background/Leine-2021-Stability_of_rigid_body_motion-(published_version).pdf`,
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: passive shape metadata is valuable, but active
shape-contact must remain gated until diagnostics, validation, and non-regression
evidence exist.

### Contact Mechanics And Multi-Contact Behavior

Literature-backed claim: state-of-practice rigid-body rockfall models use local
contact frames, unilateral constraints, Coulomb friction, impact laws, and
potentially multiple contact points on DEM terrain. Sources:
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`,
`docs/literature_review.md`.

Repository implication: current contact laws are transparent and testable but
not a nonsmooth multi-contact solver; adding sophistication without better
validation would create plausible-looking but weakly grounded behavior.

### Restitution, Friction, Roughness, Terrain, And DEM Representation

Literature-backed claim: restitution/friction/roughness behavior depends on
material, slope geometry, impact velocity, block geometry, and spatial
variability; stochastic perturbations are common in simpler models. Sources:
`docs/literature_review.md`, `background/RAMMS_ROCK2_Manual.pdf`,
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`.

Literature-backed claim: lateral dispersion depends on slope gradient,
micro-topography, roughness, and DEM/model resolution. Source:
`docs/literature_review.md` citing Crosta and Agliardi 2004.

Repository inference: DEM resolution, smoothing, interpolation, cliff/nodata
handling, vegetation representation in DEM/surface products, and subgrid
roughness can control map patterns as strongly as contact parameters. This is
why `docs/dem_terrain_sensitivity_benchmark.md` should become a dry-runnable
benchmark before terrain/material calibration.

### Scarring, Soil Interaction, And Energy Loss

Literature-backed claim: effective restitution alone cannot represent impacts
into compactable soils; scarring involves penetration/deformation, drag-like
work, rebound-plane behavior, and calibration against impact observations.
Source:
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`.

Repository implication: `scarring_contact_v1` should remain an opt-in
impact-level diagnostic. It should not be tuned to explain Tschamut deposition
or used as a field-scale material model without a calibration/holdout design.

### Forest, Vegetation, Barriers, And Fragmentation

Literature-backed claim: forests, protection measures, and fragmentation are
important state-of-practice components for site-specific hazard assessment.
Sources:
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`,
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: implementation can wait, but pilot interpretation
cannot ignore whether the chosen corridor is forested or obstacle-dominated.
No-forest/no-obstacle assumptions must be visible.

### Release Zones, Block Size, Frequency, And Probability

Literature-backed claim: rockfall workflows separate starting-zone definition,
trajectory computation, terrain/protection interaction, block volume/shape
scenarios, and scenario statistics. Sources:
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`,
`background/RAMMS_ROCK2_Manual.pdf`.

Repository inference: for early Swiss automation, source-zone policy and block
population assumptions may dominate uncertainty more than fine-grained contact
constants. Conditional scenario tables and explicit denominator semantics
should precede annualized intensity-frequency products.

### Validation Against Field Data

Literature-backed claim: field experiments such as Chant Sura are essential for
trajectory, energy, contact, shape, and scarring evaluation; no local public
source supports claiming equivalence to proprietary RAMMS internals. Sources:
`docs/literature_review.md`, `docs/dataset_strategy.md`,
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`,
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: failures and mismatches should remain scientific
evidence, not triggers for hidden tuning or lower thresholds.

## Gap Analysis

### Blocking Workflow Gaps

| Current capability | Valley-scale pilot need | State-of-practice comparison | Swiss-wide need | Gap |
| --- | --- | --- | --- | --- |
| Controlled pilot plan and prep script | Executed no-tuning real swissALTI3D pilot | Site projects with real DEM/context layers | reproducible public-geodata pipeline | Pilot not yet run |
| Deterministic release-zone sidecar | defensible source-zone policy | source polygons/lines/areas plus expert context | national source masks | Derivation policy missing |
| Hazard builder plus semantics docs | accepted GIS/QGIS review package | GIS-ready rasters and legends | tiled COG/GeoTIFF products | Package fixture/QA not executable |
| Performance benchmark docs | pilot-scale throughput gate | production-oriented ensemble execution | local parallel/chunk/reducer contracts | No local parallel runner/reducer |

### Major Scientific Gaps

- equivalent-sphere physics cannot represent shape-driven runout/spread;
- no active public shape dynamics or multi-contact solver;
- DEM/terrain representation sensitivity is designed but not executed;
- no forest/barrier/fragmentation treatment;
- terrain classes are parameter lookups, not calibrated materials;
- scarring lacks field-scale validation and torque/slip coupling.

### Validation And Calibration Gaps

- no validation maturity hierarchy tying evidence to allowed claims;
- Chant Sura contact labels remain proxy segment contacts;
- Tschamut remains confounded by terrain/source/shape/vegetation/materials;
- Mel de la Niva is workflow smoke/generalization scaffold, not timed
  trajectory validation;
- no held-out terrain/material calibration protocol is implemented.

### Probabilistic Semantics Gaps

- no source-zone physical probability or annual frequency;
- no block population probability or fragmentation probability;
- semantic guide exists, but enforcement is partial;
- weighted convergence diagnostics are limited;
- no scenario uncertainty aggregation across terrain/source/block/model forms.

### GIS And Geodata Gaps

- no executed real swisstopo pilot;
- lightweight GeoTIFF exists, but verified COG/tiled products do not;
- QGIS package spec exists, but package fixture/acceptance test does not;
- DEM sensitivity benchmark is a scaffold, not a runnable fixture;
- orthophoto/hillshade QA is procedural, not automated.

### Performance And Scalability Gaps

- no deterministic local multithreaded public runner;
- no streaming hazard reducer or thread-safe accumulation contract;
- no local chunk/resume implementation;
- no trajectory sample table/batched reader for trajectory-derived layers;
- no performance regression guard tied to pilot workload and output volume;
- no SLURM/CSCS orchestration, appropriately deferred.

### Usability And Documentation Gaps

- roadmap authority is fragmented across many historical docs;
- `docs/agent_work_log.md` is too noisy to serve as an authoritative plan;
- stale references remain in at least one pilot doc;
- local ignored outputs, raw caches, and duplicate `* 2.*` files complicate
  review;
- current documentation is strong but could overproduce scaffolds without
  converting them into executable checks or pilot evidence.

## Review Of Existing Roadmap Assumptions

| Roadmap item | Scientific value | Engineering value | Complexity | Misleading-result risk | Private/unavailable dependency | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| Controlled Tschamut/swissALTI3D real-site pilot | Medium: pilot/confounding evidence, not decisive validation | Very high | Medium | Medium if overread | Medium: private crop likely needed | Immediate if data available |
| Shape-aware block scaffold | Very high long-term | Medium | High | High if public too early | Medium for shape/contact provenance | Medium-term gate and validation first |
| GeoTIFF/COG hazard raster export | Medium scientific, high interpretation value | High | Medium | Medium for CRS/nodata mistakes | Low | GeoTIFF/QGIS fixture immediate; COG deferred |
| Source-zone/block semantics | High | High | Medium | High if annual/physical labels appear too early | Medium for source policy evidence | Immediate enforcement and examples |
| Expanded Chant Sura validation | High for contact/shape | Medium | Medium | Medium: proxy contacts can be overread | Low/medium | Medium-term scientific priority |
| Terrain-class calibration | High only with holdout evidence | High | Medium/high | Very high hidden-tuning risk | Medium | Deferred until pilot + DEM sensitivity + maturity labels |
| Tiled reducers / trajectory columnar input | Medium scientific, high production value | Very high | High | Low/medium | Low | Defer until local parallel/streaming reducer bottleneck is measured |

## Critical Findings

1. The repo is scientifically cautious and has avoided the worst overclaims.
   That discipline should remain central.
2. The newest docs correctly address several prior gaps, but many are still
   scaffolds. The next step should produce evidence or executable checks, not
   just more planning prose.
3. The best immediate evidence remains the controlled real-site
   Tschamut/swissALTI3D pilot. It should be interpreted as workflow/confounder
   evidence only.
4. Hazard semantics is now documented well enough to enforce. Manifest/schema
   checks should be expanded before more map products are promoted.
5. DEM representation sensitivity is now recognized, but not yet measured. This
   should precede calibration and should run even without private data using a
   small deterministic fixture.
6. Shape remains the largest physics gap, but active public shape runtime work
   is still premature.
7. Performance matters now, but the next engineering step should be measured
   deterministic local parallelism/streaming reduction, not generic kernel
   optimization or SLURM.
8. Forest/obstacle relevance must be scoped before pilot conclusions.
9. Documentation volume is becoming a risk. Consolidation and validation
   maturity labels would improve contributor decisions more than another
   overlapping roadmap document.
