# Repository Scientific Roadmap Review

Status: strategic, scientific, technical, and roadmap review. This document does
not change simulator behavior, defaults, validation cases, probability
semantics, or operational claims.

## Scope

This review inspected the repository as a research codebase for an independent,
open rockfall trajectory and hazard-layer workflow aimed at a future Swiss
valley-scale pilot and eventual reproducible Swiss Alpine hazard-map production
from public geodata. It uses local repository documents, checked-in source code,
validation/calibration fixtures, scripts, benchmark scaffolds, and local
background material.

Key source paths:

- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `docs/model_design.md`
- `docs/literature_review.md`
- `docs/roadmap_hazard_mapping.md`
- `docs/dataset_strategy.md`
- `docs/validation_plan.md`
- `docs/swisstopo_data_strategy.md`
- `docs/scalability_and_data_formats_review.md`
- `docs/performance_benchmarking.md`
- `docs/performance_benchmark_profile_reference.md`
- `docs/hazard_throughput_bottleneck_report.md`
- `docs/performance_benchmark_synthetic_scale_results.md`
- `docs/parquet_impact_benchmark_results.md`
- `docs/trajectory_parquet_next_step_decision.md`
- `docs/current_state_gap_analysis_next_directions.md`
- `docs/post_swiss_pilot_stack_next_step_decision.md`
- `background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`
- `background/Leine-2021-Stability_of_rigid_body_motion-(published_version).pdf`
- `background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`
- `background/RAMMS_ROCK2_Manual.pdf`

## Repository Comprehension

### Implemented Physics

The active public trajectory kernel is still an equivalent-sphere model. The
implemented physics are:

- spherical block with mass, radius, translational state, angular velocity, and
  energy diagnostics (`README.md`, `docs/model_design.md`, `src/geometry.rs`,
  `src/state.rs`);
- exact constant-gravity ballistic stepping (`docs/model_design.md`,
  `src/dynamics.rs`, `src/integrator.rs`);
- analytic terrain and small ESRI ASCII DEM terrain, including strict and
  clamped variants (`docs/model_design.md`, `src/terrain.rs`);
- default `translational_v0` impact response with normal/tangential restitution
  and Coulomb friction (`docs/model_design.md`, `src/dynamics.rs`);
- opt-in `sphere_rotational_v1` with sphere contact-point velocity, tangential
  impulse coupling, angular velocity updates, rolling diagnostics, and rolling
  resistance (`docs/model_design.md`, `src/dynamics.rs`);
- deterministic release perturbations and impact roughness under explicit seeds
  (`docs/model_design.md`, `src/stochastic.rs`, `src/simulation.rs`);
- opt-in `stochastic_contact_v1` impact-local normal/restitution/friction
  perturbations, not a spatial roughness map (`docs/model_design.md`);
- opt-in `scarring_contact_v1` compactable-soil impact energy-loss diagnostics
  with scar depth, area, drag force, and bounded translational energy loss
  (`docs/model_design.md`, `src/dynamics.rs`);
- optional per-impact event outputs and stopping/terrain-material diagnostics
  (`docs/stopping_behavior_diagnostic_report.md`,
  `docs/terrain_material_interaction_protocol.md`).

### Unsupported Physics

Unsupported or deliberately blocked capabilities include:

- active non-spherical dynamics and orientation-dependent runtime contact;
- polyhedral convex-body contact, edge/face/corner multi-contact, persistent
  contact, and nonsmooth complementarity solvers;
- calibrated terrain/material parameter libraries;
- calibrated spatial roughness fields;
- calibrated scarring with drag torque, slip-dependent friction, and terrain
  deformation;
- forest, vegetation, barriers, dams, nets, rock sheds, and fragmentation;
- air drag and seismic/acoustic losses;
- operational warning, risk modelling, exposure, vulnerability, and consequence
  workflows.

The `shape_contact_v0` label is present as an experimental pre-runtime scaffold
and internal diagnostic path, but it is explicitly blocked from public
simulation, validation, and benchmarks (`CHANGELOG.md`, `docs/model_design.md`,
`docs/post_shape_contact_v0_pause_next_step.md`, `src/integrator.rs`).

### Validation And Calibration Evidence

The repository has a strong verification posture for its implemented equations
and data contracts:

- analytic verification cases under `verification/analytic/`;
- synthetic terrain/contact cases under `verification/synthetic/`;
- stochastic reproducibility cases under `verification/stochastic/`;
- Rust and Python tests under `tests/`;
- case-schema, artifact, hazard-layer, performance, and terrain-material checks
  in `scripts/` and `tests/`.

Real-data validation is useful but still research-grade:

- Chant Sura is the strongest trajectory/contact reference. The repository
  includes first-flight, DEM-backed segmented-contact, extended, and held-out
  fixtures, but contact labels are segment-boundary proxies rather than full
  instrumented impact truth (`docs/dataset_strategy.md`,
  `docs/validation_plan.md`).
- Tschamut constrains deposition/runout distributions and failure modes, but
  current checked-in terrain is a public-derived proxy rather than official
  field terrain (`docs/dataset_strategy.md`, `docs/validation_plan.md`,
  `docs/terrain_model.md`).
- Lu/Chant Sura ESurf impact tables constrain impact-level scarring calibration
  only; they do not validate trajectory or hazard-map skill
  (`docs/dataset_strategy.md`, `docs/scarring_real_data_calibration.md`).
- Mel de la Niva is registered as a high-energy external generalization
  benchmark but remains optional and smoke-level unless local archives are
  prepared (`docs/dataset_strategy.md`,
  `validation/benchmarks/mel_de_la_niva/README.md`).

Calibration discipline is good: calibration lives under `calibration/`, selected
parameters are documented as research diagnostics, and validation cases are not
silently retuned (`docs/validation_plan.md`, `docs/dataset_strategy.md`).

### Hazard-Layer Capabilities

The hazard workflow is a post-processing layer, not core physics
(`docs/hazard_layers.md`, `scripts/build_hazard_layers.py`). It currently
supports:

- reach probability;
- deposition density;
- maximum kinetic energy;
- maximum jump height;
- significant-impact density from CSV or Parquet impact-event tables;
- threshold exceedance layers for kinetic energy, jump height, and velocity;
- unweighted binomial standard-error diagnostics for reach/exceedance layers;
- opt-in sampling-weighted conditional reach, deposition, impact-density, and
  exceedance layers;
- CSV grids, ESRI ASCII grids, GeoJSON deposition points, JSON metadata,
  `run_manifest_v1`, optional PNG/HTML reports, and opt-in lightweight GeoTIFF.

Limitations:

- current GeoTIFF is deliberately lightweight and uncompressed; COG requests
  fail explicitly (`docs/hazard_layers.md`);
- outputs are research diagnostics and hazard indicators, not operational maps
  or risk maps (`README.md`, `docs/roadmap_hazard_mapping.md`);
- weighted layers are conditional sampling-weighted diagnostics, not annual
  frequency or physical source probability (`docs/weighted_hazard_layer_review.md`,
  `docs/probabilistic_scenario_model_design.md`);
- production-scale tiled reducers and trajectory Parquet are still future work
  (`docs/scalability_and_data_formats_review.md`,
  `docs/trajectory_parquet_next_step_decision.md`).

### Swiss Geodata Readiness

The repository is geodata-aware but not yet a real Swiss pilot:

- swisstopo dataset roles, CRS, vertical datum, tile provenance, and no-large-
  raw-data policy are well documented (`docs/swisstopo_data_strategy.md`,
  `data/datasets.yaml`);
- small synthetic swissALTI3D-style LV95/LN02 fixtures validate metadata,
  release-zone, terrain-class, and manifest contracts
  (`validation/data/processed/swisstopo_pilot/`,
  `docs/swiss_terrain_ingestion_pilot.md`);
- a controlled private Tschamut/swissALTI3D pilot plan and preparation script
  exist (`docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `scripts/prepare_tschamut_swissalti3d_pilot.py`).

The missing evidence is execution on a real, provenance-tracked swissALTI3D crop
with documented release-zone assumptions, embedded performance-readiness
measurement, and visual QA. The current Swiss stack is therefore a credible
contract layer, not a demonstrated valley-scale workflow. Its first real-site
result should be framed as pilot and confounding evidence, not as decisive
physics validation.

### Probabilistic Semantics

The probability terminology is mature relative to the numerical capability:

- unweighted diagnostic maps are implemented;
- `sampling_weighted` conditional maps are implemented with strict validation;
- source-zone probability, annual release frequency, block-population
  probability, physical-probability layers, and annual-frequency layers remain
  design-only (`docs/probabilistic_scenario_model_design.md`,
  `docs/weighted_hazard_layer_review.md`).

This is the right boundary. The current repo should not label conditional
sampling-weighted maps as physical or annual probability.

### Scalability And HPC Readiness

The code has good deterministic kernel structure:

- single-trajectory simulation is separated from most file I/O
  (`src/integrator.rs`, `src/simulation.rs`);
- randomness is explicit and derives per-trajectory seeds from global seed,
  case ID, and trajectory ID (`src/stochastic.rs`, `src/simulation.rs`);
- impact-event Parquet and projected reads have been added for impact-density
  scale work (`CHANGELOG.md`, `docs/trajectory_parquet_next_step_decision.md`);
- manifests and explicit grids reduce provenance and bounds-discovery problems
  (`docs/scalability_and_data_formats_review.md`, `docs/hazard_layers.md`).

Remaining HPC gaps:

- no local parallel trajectory execution contract in the public runner;
- no formal chunk execution/resume workflow;
- no deterministic tiled reducer merge implementation for large hazard rasters;
- no trajectory Parquet writer/reader for reach, energy, jump, and velocity
  layers;
- no explicit valley-pilot performance budget or release-mode baseline tied to
  the 10,000-trajectories-per-release-zone design target;
- no first-class performance acceptance gate that says when to optimize the
  Python hazard accumulator, output writers, or the Rust kernel;
- no CSCS/SLURM orchestration, which should remain deferred until chunk and
  reducer contracts are stable (`AGENTS.md`,
  `docs/scalability_and_data_formats_review.md`).

### Performance State

Performance has already been measured more thoroughly than the previous
roadmap ranking implied. Current evidence:

- the standard profile is lightweight and usable for routine checks, while the
  scale profile can take tens of minutes and produce gigabytes of ignored
  artifacts (`docs/performance_benchmark_profile_reference.md`);
- explicit hazard grids remove avoidable bounds-discovery scans and are the
  right default for benchmark and pilot-style runs
  (`docs/hazard_throughput_bottleneck_report.md`);
- once plots are disabled, hazard accumulation is dominated by Python-level
  trajectory sample work, not raster writing or projected Parquet impact reads
  (`docs/hazard_throughput_bottleneck_report.md`);
- impact-event Parquet reduces file count and bytes, and projected reads are
  performance-positive for impact-density accumulation, but the current writer
  is still slower than CSV in measured cases
  (`docs/parquet_impact_benchmark_results.md`);
- trajectory CSV output remains a one-file-per-trajectory pressure point and
  feeds most hazard layers, but trajectory Parquet should be paired with a
  projected/batched reader rather than added as a writer-only feature
  (`docs/trajectory_parquet_next_step_decision.md`);
- simulation throughput is not the only bottleneck. Output writing and hazard
  post-processing are already competitive with or larger than simulation time
  in full-output workflows (`docs/performance_benchmark_synthetic_scale_results.md`,
  `docs/performance_benchmark_profile_reference.md`).

Conclusion: a performance task is warranted, but it should be a targeted
throughput-readiness component embedded in the real-site pilot, not a standalone
generic optimization package. The objective should be to establish release-mode
pilot budgets, locate the first bottleneck on real or representative pilot
inputs, and implement only the smallest measured improvement needed to keep the
valley-scale pilot credible.

### Documentation And Reproducibility Maturity

Documentation is broad, mostly consistent, and unusually explicit about
limitations. Strong points:

- clear separation of verification, validation, calibration, operational
  geodata, hazard, and risk (`README.md`, `AGENTS.md`,
  `docs/dataset_strategy.md`, `docs/validation_plan.md`);
- semantic-versioning rules and no-silent-physics-change policy (`AGENTS.md`,
  `CHANGELOG.md`);
- data-size and raw-geodata hygiene (`docs/swisstopo_data_strategy.md`,
  `data/datasets.yaml`);
- consistency checks (`scripts/check_repo_consistency.py`).

Weak points:

- many historical decision records now compete for "next step" authority;
- some docs say GeoTIFF export is missing while `docs/hazard_layers.md` now
  documents a lightweight opt-in GeoTIFF path. The stale statement should be
  reworded as "COG and production raster packaging are missing";
- the repo has local generated output clutter under ignored results, which is
  acceptable but makes review harder;
- `hazard/.DS_Store`, `validation/results/.DS_Store`, and Python bytecode
  caches are present locally. They are not staged, but artifact hygiene should
  stay visible.

## Literature And State-Of-Practice Drivers

### Block Shape And Non-Spherical Dynamics

Literature-backed claim: Rock shape strongly controls runout, lateral spreading,
rolling/tumbling modes, jump heights, and energy partitioning. Full 3D
shape-aware models represent rocks as convex polyhedra with orientation and
inertia, while simpler sphere models can produce unrealistic rolling behavior.
Sources: `docs/literature_review.md`;
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`;
`background/Leine-2021-Stability_of_rigid_body_motion-(published_version).pdf`;
`background/RAMMS_ROCK2_Manual.pdf`.

Literature-backed claim: Platy rocks require stable principal-axis rotational
behavior; numerical schemes that mishandle free rigid-body stability can
underestimate runout and lateral spread. Sources:
`background/Leine-2021-Stability_of_rigid_body_motion-(published_version).pdf`;
`docs/literature_review.md`.

Repository implication: passive shape metadata is useful, but the equivalent
sphere remains a major scientific gap. The paused `shape_contact_v0` scaffold is
scientifically important but not yet credible as a public model.

### Contact Mechanics And Multi-Contact Behavior

Literature-backed claim: State-of-practice rigid-body rockfall models use local
contact frames, hard unilateral constraints, Coulomb friction, impact laws, and
potentially multiple contact points for convex bodies on DEM terrain. Sources:
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`;
`docs/literature_review.md`.

Repository implication: current restitution/friction contact is transparent and
testable but not a nonsmooth multi-contact solver. Adding contact sophistication
without better validation may create plausible-looking but ungrounded behavior.

### Restitution, Friction, Roughness, And Terrain Classes

Literature-backed claim: Restitution/friction parameters are strongly affected
by terrain material, roughness, slope geometry, impact velocity, block geometry,
and spatial variability; stochastic parameter perturbations are common in
simpler models. Sources: `docs/literature_review.md`;
`background/RAMMS_ROCK2_Manual.pdf`;
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`.

Literature-backed claim: Lateral dispersion depends on slope gradient,
micro-topography, roughness, and DEM/model resolution. Source:
`docs/literature_review.md` citing Crosta and Agliardi 2004.

Repository implication: the current terrain-class raster is a parameter lookup
and provenance scaffold, not a calibrated material model. It should not be
optimized before real-terrain and validation splits are stronger.

### Scarring, Soil Interaction, And Energy Loss

Literature-backed claim: Effective restitution coefficients alone cannot
represent the complexity of impacts into compactable soils; scarring involves
soil deformation, penetration depth, drag-like work, sliding on a hard rebound
plane, and rebound from a scar. Source:
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`.

Literature-backed claim: Scarring models need impact-level validation and
calibration; Lu et al. used Chant Sura single-impact and multi-impact
experiments and still identified rotational drag and wider calibration data as
future work. Source:
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`.

Repository implication: `scarring_contact_v1` is correctly framed as a minimal,
opt-in diagnostic. It should remain impact-level until trajectory-scale
contact/terrain normal evidence improves.

### Forest, Vegetation, Barriers, And Fragmentation

Literature-backed claim: Forests, protection measures, and fragmentation are
important state-of-practice components for site-specific hazard assessment.
Sources: `background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`;
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: missing forest/barrier/fragmentation physics is a real
gap for Swiss valleys, but it is not the best immediate work unless the pilot
domain requires those effects. Fragmentation should remain separate from hazard
layers and not be simulated by silently changing block size mid-run.

### Release-Zone Modelling

Literature-backed claim: Rockfall modelling requires starting-zone definition,
trajectory computation, and interaction with terrain/protection elements as
distinct components. Source:
`background/Leine_2014_Simulation_of_rockfall_trajectories_with_consideration_of_rock_shape.pdf`.

External expert assessment: regional-scale source-area identification can be
derived from high-resolution DEM slope distributions combined with geological
and topographic map information. This is not yet represented by a local
implementation source; it should be added to the literature inventory before a
source-zone derivation algorithm is implemented.

Repository implication: deterministic polygon sampling is a useful scaffold,
but the missing scientific piece is a documented source-zone derivation policy
from slope, geology, inventory, or field interpretation. This should be treated
as an early hazard-map requirement, not as late orchestration detail.

### Block-Size And Source-Frequency Semantics

Literature-backed claim: State-of-practice workflows distinguish rock volume,
shape, release configuration, and scenario statistics, but operational
frequency semantics require site-specific expert assumptions. Source:
`background/RAMMS_ROCK2_Manual.pdf`.

Repository inference: For Swiss automated hazard mapping, source frequency and
block-population probability are likely more uncertain than fine-grained
contact constants at early pilot stage. The repo should implement explicit
scenario tables and conditional products before annualized maps.

### Uncertainty And Probabilistic Interpretation

Literature-backed claim: Rockfall hazard assessment relies on ensembles and
statistical trajectory outputs because release conditions, terrain interaction,
and block properties vary. Sources: `docs/literature_review.md`;
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: uncertainty provenance is central. Current
sampling-weighted layers are a correct first step, but annual-frequency layers
would be premature without source-frequency and block-population evidence.

### Validation Against Field Data

Literature-backed claim: Field experiments such as Chant Sura are essential for
validating energy, contact, trajectory, and scarring behavior; no public source
supports claiming equivalence to proprietary RAMMS internals. Sources:
`docs/literature_review.md`; `docs/dataset_strategy.md`;
`background/Lu-2019-Modelling_rockfall_impact_with_scarring-(published_version).pdf`;
`background/RAMMS_ROCK2_Manual.pdf`.

Repository implication: the repo's validation framing is scientifically sound,
but evidence remains partial. Validation should keep reporting failures as
information rather than lowering thresholds or tuning hidden parameters.

## Gap Analysis

### Blocking Workflow Gaps

| Current capability | Swiss valley-scale pilot needs | State-of-practice comparison | Long-term Swiss-wide need | Gap |
| --- | --- | --- | --- | --- |
| Synthetic swissALTI3D-style metadata fixture | Real swissALTI3D crop with provenance, performance budget, and visual QA | Mature tools use DEM projects with scenario inputs | tiled DEM ingestion and provenance | Real-site pilot evidence is missing |
| Deterministic release-zone fixture | defensible source-zone derivation and sampling | release points/lines/areas and scenario setup | national reproducible source masks | source-zone policy is an early blocker |
| Hazard post-processing scripts | GIS-ready hazard products and review package | raster/statistical outputs in GIS tools | tiled COG/GeoTIFF products | COG/production packaging missing |
| Local validation cases | controlled pilot run with no tuning | site project/scenario workflows | repeatable batch workflows | no executed valley-scale pilot |

### Major Scientific Gaps

- equivalent-sphere model cannot represent shape-driven runout, spreading, and
  orientation-dependent contact;
- no active non-spherical rigid-body orientation integration in public runtime;
- no multi-contact hard-contact solver;
- no calibrated terrain/material class library;
- no forest, barrier, or fragmentation modelling;
- scarring lacks torque/slip coupling and field-scale validation;
- forest and obstacles may be first-order boundary conditions in the chosen
  Swiss valley pilot; at minimum their relevance must be scoped before
  interpreting pilot hazard layers.

### Validation And Calibration Gaps

- Chant Sura contact observations are proxy segmented contacts, not full impact
  truth;
- Tschamut deposition evidence is confounded by proxy terrain, source
  assumptions, shape, vegetation, and material parameters;
- scarring calibration is impact-level and underdetermined;
- Mel de la Niva is not yet a timed trajectory validation case;
- no held-out terrain-class calibration/validation split exists.

### Probabilistic Semantics Gaps

- no source-zone physical probability or annual frequency;
- no block-size/shape population probability;
- no annualized intensity-frequency layers;
- no weighted convergence diagnostics beyond unweighted standard error;
- no scenario uncertainty aggregation across model form, terrain class, release
  source, and block class.

### GIS And Geodata Gaps

- real swisstopo ingestion is private-template only;
- COG production output is not implemented;
- no QGIS-ready pilot package with release zones, rasters, manifests, and QA
  layers;
- no release-zone derivation from slope/geology/inventory data;
- no orthophoto/hillshade QA workflow codified as a testable checklist.

### Performance And Scalability Gaps

- no trajectory Parquet table for trajectory-derived hazard layers;
- no chunk execution/resume workflow;
- no tiled reducer state and deterministic merge implementation;
- no local parallel public runner for large source-zone ensembles;
- no SLURM/CSCS orchestration, appropriately deferred;
- no explicit throughput budget for the first valley-scale pilot and no
  release-mode benchmark baseline that estimates whether 10,000 trajectories per
  source zone is feasible on local hardware;
- no performance regression guard for output volume, file count, hazard-stage
  accumulation, and simulation throughput;
- no benchmark-driven decision gate between optimizing trajectory accumulation,
  adding trajectory Parquet, adding local parallelism, or deferring all three.

### Usability And Documentation Gaps

- roadmap documents are numerous and some are stale relative to recent GeoTIFF,
  Parquet-impact, and stopping-diagnostic work;
- the immediate "do this next" path is less clear than the architecture;
- production/debug output distinction exists but should be repeated in new
  pilot docs;
- generated ignored results and local caches make review noisier.

## Review Of Existing Roadmap Assumptions

| Roadmap item | Scientific value | Engineering value | Complexity | Misleading-result risk | Private/unavailable data dependency | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| Controlled Tschamut/swissALTI3D real-site pilot with embedded performance gate | Medium: primarily workflow/confounding and pilot evidence, not decisive physics validation | Very high: exercises Swiss stack end to end and tests ensemble feasibility | Medium | Medium: poor results could be overinterpreted as physics validation | Medium: real crop likely local/private | Immediate |
| Shape-readiness validation and passive shape scenario semantics | Very high for trajectory realism and hazard interpretation | Medium to high: block scenarios affect pilot ensembles | Medium | Medium: proxy shape/contact evidence can be overread | Low for passive metadata, medium for active shape provenance | Immediate/medium-term scientific; active runtime remains gated |
| GeoTIFF/QGIS pilot package, verified COG later | Medium scientific, high interpretation value | Very high GIS value | Medium | Medium: CRS/nodata errors can mislead maps | Low | Immediate engineering after pilot setup; CRS-correct GeoTIFF first, COG later |
| Probabilistic source-zone/block semantics | High for hazard-map credibility | High for scenario reproducibility | Medium | High if annual labels precede frequency evidence | Medium: requires source/block assumptions | Immediate as design/checks; physical/annual implementation deferred |
| Expanded Chant Sura validation | High for contact/shape evidence | Medium | Medium | Medium: proxy contact labels remain limiting | Low to medium depending raw archive needs | Immediate/medium-term validation work |
| Forest/obstacle relevance scoping | Medium to high depending pilot domain | High for Swiss valley interpretation | Low to medium | Medium if ignored or silently folded into parameters | Medium: depends on pilot-domain context layers | Early scoping before pilot conclusions; implementation deferred |
| Terrain-class calibration framework | High if designed with held-out data | High | Medium to high | Very high hidden-tuning risk | Medium | Defer until real-site pilot and validation split are established |
| Tiled reducers / trajectory columnar input | Medium scientific, high production value | Very high | Medium to high | Low to medium | Low | Medium-term engineering after pilot-scale bottlenecks are measured |

## Critical Findings

1. The repo may be optimizing some engineering details before proving the real
   Swiss workflow. Impact Parquet and explicit grids are useful, but the largest
   missing evidence is still a real swissALTI3D pilot run with honest results
   and embedded throughput/file-count measurements.

2. Shape is the largest physics gap and is underweighted if treated only as a
   future active-contact feature. Shape-readiness validation, passive shape
   scenario semantics, and block-shape provenance should move earlier. Active
   shape contact itself remains high-risk: the internal `shape_contact_v0`
   result was uncertain/failed, and public runtime validation is blocked.

3. Terrain/material classes are schema-ready but scientifically weak. Using
   them as calibrated parameters before real-terrain and held-out evidence would
   confuse calibration with validation.

4. Probabilistic wording is currently disciplined. That discipline must be
   preserved: no annual-frequency labels until source frequency and block
   probability are explicit and validated.

5. The roadmap should distinguish "CRS-correct QGIS-inspectable GeoTIFF for a
   local pilot" from "verified COG/tiled Swiss production package."
   Cloud-optimized output is useful and aligned with modern standards, but the
   first pilot should prioritize CRS, transform, nodata, grid alignment, and
   inspectability over cloud optimization.

6. The current validation evidence supports `sphere_rotational_v1` as a
   recommended opt-in comparison, not a default change. Tschamut behavior shows
   translational under-run and rotational over-run patterns that are useful but
   not default-selection evidence.

7. Performance is now sufficiently measured to deserve an explicit pilot gate,
   but it should be merged into the real-site pilot rather than ranked as a
   separate work stream. The target of roughly 10,000 trajectories per release
   zone makes throughput, reduced outputs, file counts, and local parallelism
   core feasibility criteria.

8. Forest and obstacle relevance should move earlier as a scoping task. For a
   Swiss valley pilot, forest can be a first-order boundary condition affecting
   propagation probability and intensity. Implementation can stay deferred, but
   pilot conclusions should not ignore the domain's forest/obstacle context.

9. The repository is strongest as a transparent scientific workbench. Its next
   step should create evidence that decides between major branches, not just add
   one more feature.
