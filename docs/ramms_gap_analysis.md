# RAMMS Gap Analysis

Status: strategic comparison against publicly documented RAMMS::ROCKFALL
capabilities, accessed 2026-05-06. This document does not implement code, tune
parameters, optimize performance, claim operational validity, or claim
equivalence with RAMMS::ROCKFALL.

## Scope And Evidence Rules

This analysis uses RAMMS only as a public state-of-practice reference for Swiss
rockfall modelling. It does not reverse engineer proprietary code, binaries, or
private workflows.

Evidence labels:

- **Documented**: stated in public RAMMS/WSL/SLF pages, manuals, or public
  papers.
- **Inferred**: a reasonable implication of documented public workflow, but not
  an implementation detail.
- **Unknown**: proprietary implementation or validation detail not available
  from public sources.

Main RAMMS public sources:

- RAMMS::Rockfall official page:
  <https://ramms.ch/ramms-rockfall/>
- RAMMS non-smooth mechanics overview:
  <https://ramms.ch/ramms-rockfall/non-smooth-mechanics-framework/>
- RAMMS::Rockfall User Manual:
  <https://ramms.ch/wp-content/uploads/RAMMS_ROCK2_Manual.pdf>
- RAMMS FAQ / workflow learning resources:
  <https://ramms.ch/faq/>
- SLF rockfall experiment overview:
  <https://www.wsl.ch/en/projects/rockfall-experiments/>
- Leine et al. 2014, *Simulation of rockfall trajectories with consideration
  of rock shape*, DOI `10.1007/s11044-013-9393-4`
- Lu et al. 2019, *Modelling rockfall impact with scarring in compactable
  soils*, DOI `10.1007/s10346-019-01238-z`
- Caviezel et al. 2021, *The relevance of rock shape over mass*, DOI
  `10.1038/s41467-021-25794-y`

Important evidence boundary:

- Public RAMMS pages and manuals document the capability-level model: real
  rock shapes, non-smooth rigid-body mechanics, terrain/material categories,
  statistical result products, and practitioner workflows.
- They do not expose all proprietary implementation choices, numerical
  tolerances, default-calibration data, or production quality-control
  procedures. Those remain **unknown** here.
- Where this document says "RAMMS is ahead", it means "ahead in publicly
  documented user-facing capability or published scientific maturity", not
  "verified superior for every site or metric".

## Current Local Project Snapshot

The local project is an open research simulator with:

- deterministic equivalent-sphere dynamics;
- default `translational_v0` and opt-in `sphere_rotational_v1`;
- opt-in stochastic roughness and compactable-soil scarring diagnostics;
- analytic terrain, ESRI ASCII DEMs, swissALTI3D-style terrain metadata,
  release-zone metadata, and terrain-class fixtures;
- Chant Sura trajectory/contact validation;
- registered public Tschamut benchmark reproduction on public swissALTI3D 2 m
  terrain;
- 10-run and 25-run Tschamut no-tuning results;
- public Tschamut passive block-shape sidecars and inertness checks;
- full-ensemble hazard-layer post-processing with reach, deposition, maximum
  energy, jump height, significant-impact density, and exceedance layers;
- sampling-weighted conditional hazard-layer prototype;
- manifests, provenance, benchmarking, Parquet impact-event output, and
  explicit-grid hazard accumulation.

Recent scientific findings:

- `translational_v0` under-runs public Tschamut by about 30 m in both 10-run and
  25-run subsets.
- `sphere_rotational_v1` over-runs public Tschamut strongly in both subsets.
- Chant Sura supports `sphere_rotational_v1` as a recommended opt-in
  trajectory/contact model, but not as a default.
- Grouped Tschamut analysis suggests structural deficiencies rather than a
  simple scalar parameter error.
- Shape/contact and terrain/material effects remain confounded.

## Maturity Matrix

| Dimension | Local project | Public RAMMS capability | Gap category | Priority |
| --- | --- | --- | --- | --- |
| Openness and reproducibility | Open code, public workflows, manifests, no-tuning reports | Proprietary software; public manuals and publications, but internals not open | Local strength | Strategic differentiator |
| Basic trajectory physics | Verified sphere free flight, restitution/friction, optional sphere rotation | Documented hard-contact rigid-body approach on 3D terrain | Critical scientific gap | High |
| Block shape | Passive metadata only; active sphere | Documented convex-hull/polyhedral real rock shapes and RockBuilder workflow | Critical scientific gap | Highest |
| Orientation/inertia | Angular velocity for sphere; no orientation state in dynamics | Documented quaternion orientation and principal inertial behaviour | Critical scientific gap | High |
| Contact mechanics | Restitution/friction plus simple rotational impulse | Documented nonsmooth/frictional contact at rock edges/corners; exact internals unknown | Critical scientific gap | High |
| Motion regimes | Free flight, impact, sliding, rolling diagnostics | Documented sliding, rolling, skipping, jumping and stopping transitions | Numerical/physical gap | High |
| Terrain/materials | Optional terrain class lookup, not calibrated | Documented terrain/soil categories with material parameters and scarring | Scientific/calibration gap | High |
| Scarring | Opt-in simplified translational energy loss | Documented hybrid rigid-body plus scarring mechanisms for soft soils | Scientific gap | Medium-high |
| Forest | No forest interaction | Documented forest polygons, densities, DBH distributions | Operational/scientific gap | Medium |
| Barriers/obstacles | Not implemented | Public docs include obstacle/impact-analysis workflows; the public dam-interaction page explicitly notes a specific dam-interaction model is not yet implemented in RAMMS::Rockfall | Operational/product gap with caveat | Medium |
| Fragmentation | Not implemented | Manual states rocks are considered indestructible in the described model | Intentionally out of scope for parity | Low |
| Validation maturity | Chant Sura, Tschamut, scarring experiments, transparent public reports | Public RAMMS tied to SLF/WSL experimental campaigns and application testing | Validation gap | High |
| Hazard layers | CSV/ASCII/GeoJSON/PNG/HTML diagnostics and conditional weighted prototype | Documented statistic mode with reach probability and cell statistics for velocity, energy, jump height, rotational velocity, scar metrics | Product/statistics gap | Medium-high |
| GIS workflow | ESRI ASCII input/output, metadata, no GeoTIFF export yet | Manual documents ESRI ASCII, GeoTIFF, ASCII XYZ and shapefile workflows | GIS/product gap | High |
| Probability semantics | Explicit distinction between unweighted, sampling-weighted, physical probability, annual frequency | RAMMS public docs emphasize statistical trajectory analysis; exact probability semantics remain workflow-specific | Local strength plus product gap | Medium |
| Scalability | Benchmarks, Parquet impacts, explicit grids, no tiling/HPC | Official page mentions reduced-output mode for very large trajectory sets | Engineering gap | Medium |
| User interface | CLI/docs/scripts | Mature GUI, visualization, scenario tools | Productization gap | Medium-low for research |

## A. Physics And Numerical Model

### Block Representation

**RAMMS documented capability.** The official page states that RAMMS accounts for
real rock shapes and arbitrary three-dimensional polyhedral bodies. The manual
describes rock bodies as convex-hull polyhedra derived from point clouds, and
the RockBuilder workflow supports realistic shape libraries.

**Local state.** The active model is an equivalent sphere. Passive
`shape_metadata_v1` can record dimensions, inertia diagnostics, and orientation
metadata, but it does not affect contact.

**Gap.** Critical scientific gap. This is the largest physics difference.
Public Tschamut and Chant Sura both point toward shape as a structural missing
state, but current local results are not yet sufficient to isolate shape from
terrain/material effects.

### Rotation And Orientation

**RAMMS documented capability.** Public documentation describes translational
and rotational motion, orientation tracking with quaternions, gyroscopic effects,
and principal moments of inertia for arbitrary shapes.

**Local state.** `sphere_rotational_v1` carries angular velocity and spherical
rotational energy. There is no active orientation state and no non-spherical
inertia in dynamics.

**Gap.** Critical numerical/physical gap. The local project has a useful first
rotational sphere model, but it cannot represent wheel-like, platy, elongate, or
tumbling shape-stabilized trajectories.

### Contact Mechanics And Motion Regimes

**RAMMS documented capability.** Public RAMMS material distinguishes itself from
simple rebound models by using rigid-body hard-contact mechanics and frictional
operators acting at rock surfaces, edges, and corners. The manual describes
sliding, rolling, skipping, and jumping as represented motion modes.

**Local state.** Contact is restitution/friction based, with optional spherical
rotational tangential impulse. Sliding and rolling are simplified sphere
regimes; roughness and scarring are add-ons, not a full contact framework.

**Gap.** Critical scientific gap. Public RAMMS documentation indicates a
fundamentally different contact philosophy. The local project should not try to
copy undocumented internals, but it does need a documented independent
shape/contact design if it wants to close this class of mismatch.

### Terrain Interaction, Roughness, And Materials

**RAMMS documented capability.** The manual describes deterministic ground
categories and default soil categories, including wet/soft soils, talus,
boulder fields, roads, bedrock, forest soil, and snow. It also describes
scarring layers and material-dependent parameters.

**Local state.** Terrain-class rasters can override existing contact/scarring
parameters, but no calibrated parameter library exists. `stochastic_contact_v1`
perturbs impact normals/coefficients; `scarring_contact_v1` adds simplified
impact-level energy loss.

**Gap.** Critical calibration gap. The local project has the schema and
diagnostics, but not the field-calibrated material model needed for Swiss
hazard-map credibility.

### Forest, Barriers, Obstacles, And Fragmentation

**RAMMS documented capability.** Public RAMMS resources describe forest
workflows using tree density and DBH distributions, and result-analysis tools
for trajectory impacts on polygon/shapefile regions. The RAMMS website also
documents research pages for dam/shed interactions, but one public dam page
states that the described dam-interaction model is not yet implemented in
RAMMS::Rockfall. The manual section reviewed here states rocks are
indestructible for the described model, so fragmentation is not a RAMMS parity
target from that public evidence.

**Local state.** No forest, barrier, shed, deadwood, obstacle, or fragmentation
physics exists.

**Gap.** Operational/product and scientific gap for real hazard workflows. It
is not the immediate next scientific gap because current Tschamut/Chant Sura
failure modes already arise without these features. Protection-measure modelling
should be treated as a later product layer unless a specific public source
documents an implemented RAMMS::Rockfall feature and an equivalent open
requirement.

### Probabilistic Treatment

**RAMMS documented capability.** Public docs distinguish trajectory inspection
from statistic mode and describe reach probability, number of rocks, number of
deposited rocks, and cell statistics over many trajectories. The manual
emphasizes deterministic terrain parameters and statistical spread from initial
conditions.

**Local state.** The local project explicitly separates unweighted diagnostics,
sampling-weighted conditional maps, physical probability, annual frequency, and
risk. Only sampling-weighted conditional reach/exceedance maps are implemented.

**Gap.** Mixed. RAMMS is ahead in practitioner-ready statistical map products;
the local project is arguably stronger in explicit probability terminology and
manifested semantics, but lacks physical source-frequency models.

## B. Validation And Calibration

### Benchmark Datasets

**RAMMS documented capability.** RAMMS is publicly associated with SLF/WSL field
experiments, including Chant Sura / Flüela Pass, Spitsbergen, Walenstadt/St.
Léonard-style experimental references, and public papers on shape and scarring.
SLF describes these datasets as inputs for testing and validating RAMMS.

**Local state.** The local project uses Chant Sura for trajectory/contact
validation, Lu/ESurf-style impact data for scarring calibration, and Tschamut
for deposition/runout validation. It has public Tschamut reproduction and
failure-mode reports.

**Gap.** RAMMS is clearly ahead in breadth and maturity of field testing. The
local project is strong in open reproducibility and no-tuning discipline.

### Calibration Philosophy

**RAMMS documented capability.** Public material describes calibrated terrain
categories and field experiments. Exact calibration procedures and default
parameter derivations are partly public through manuals/papers but not a fully
open implementation-level workflow.

**Local state.** Calibration is deliberately separated: scarring is calibrated
at impact level, validation remains held out, and Tschamut is not tuned.

**Gap.** The local project needs a terrain/material calibration protocol with
training/held-out splits. Its discipline is a strength, but it lacks calibrated
parameter sets.

### Trajectory And Deposition Realism

**RAMMS documented capability.** Public RAMMS output includes trajectory,
velocity, energy, jump height, and rotational variables; publications emphasize
shape, rotation, scarring, and field observations.

**Local state.** Chant Sura supports `sphere_rotational_v1` for trajectory shape
and energy; public Tschamut shows default under-run and rotational over-run.

**Gap.** Critical. The local model has transparent diagnostics but is not yet
field-realistic for Tschamut deposition/runout.

## C. Hazard Outputs And GIS Workflow

### Raster Products And Hazard Semantics

**RAMMS documented capability.** Statistic Mode asks which cells are affected,
how many trajectories pass, velocity/kinetic-energy/jump-height/rotational
velocity values per cell, and reach probability. The manual describes mean,
median, quantile, and maximum statistics for cell values, with default quantiles
including 90%, 95%, and 99%.

**Local state.** Current layers include reach probability, deposition density,
max kinetic energy, max jump height, impact density, and threshold exceedance.
Exact percentile rasters are not implemented; weighted layers are
sampling-weighted conditional only.

**Gap.** Important product/scientific gap. The local project needs percentile
or quantile layers, convergence diagnostics, and clearer intensity-map
conventions for engineering interpretation.

### GIS Formats And CRS

**RAMMS documented capability.** Manual inputs include ESRI ASCII, GeoTIFF, and
ASCII XYZ, with GIS shapefile workflows for terrain/forest/material polygons.

**Local state.** The project supports ESRI ASCII and metadata-rich manifests,
but not CRS-bearing GeoTIFF/COG outputs or robust shapefile/GeoPackage
workflows.

**Gap.** Critical productization gap for Swiss pilots. GeoTIFF/COG output is a
high-value engineering step after scientific metric grouping.

## D. Engineering And Software Architecture

### Provenance And Reproducibility

**RAMMS documented capability.** RAMMS provides a mature GUI, scenario logs, and
engineering workflow tools. Public pages mention automatic CSV/HTML reporting
and reduced-output mode.

**Local state.** The local project has open source code, deterministic seeds,
manifested terrain/release/class/shape provenance, checksums, benchmark
profiles, and documented no-tuning workflows.

**Gap / strength.** This is a local strength. RAMMS is stronger as a finished
engineering product, but the local project is more transparent and auditable for
research.

### Scalability And Data Formats

**RAMMS documented capability.** The official page advertises reduced-output
mode for tens or hundreds of thousands of trajectories. Details are public at
the capability level, not implementation level.

**Local state.** The project has Parquet impact events, explicit grids,
streaming hazard input paths, and benchmark instrumentation. It lacks trajectory
Parquet, tiled reducers, distributed orchestration, and resume/chunk merging.

**Gap.** Important engineering gap, but not the immediate scientific blocker.
Current bottlenecks are known; further performance work should follow larger
benchmark or pilot needs.

## E. Scientific Workflow Maturity

The local project differs philosophically from RAMMS:

- It prioritizes open reproducibility over operational polish.
- It keeps calibration separated from validation.
- It documents failure modes before adding physics.
- It treats probability semantics explicitly rather than relying on one
  workflow convention.
- It is not trying to become a black-box engineering product in the near term.

This is a scientific strength, but it also means the local project should not
claim field hazard-map readiness until shape, terrain/material calibration, and
GIS outputs mature.

## Where The Local Project Is Already Stronger Or More Modern

- **Open auditability.** Code, tests, docs, benchmark scripts, and generated
  workflows are inspectable.
- **No-tuning discipline.** Public Tschamut results are reported even when they
  show under-run/over-run.
- **Manifest provenance.** Terrain metadata, CRS, vertical datum, release-zone
  metadata, output summaries, and passive shape metadata are explicit.
- **Probability semantics.** The project carefully separates unweighted,
  sampling-weighted, physical probability, annual frequency, hazard, and risk.
- **Benchmark instrumentation.** Runtime, output volume, and hazard-throughput
  measurements guide engineering choices.
- **Dataset role separation.** Chant Sura, Lu/scarring, Tschamut, synthetic
  cases, and swisstopo-style geodata have distinct roles.

These are research-platform strengths, not evidence of operational superiority.

## Where RAMMS Is Clearly Ahead

- Real/polyhedral rock shape in active dynamics.
- Orientation-aware rigid-body dynamics and contact-point mechanics.
- Mature terrain/material categories and engineering workflows.
- Forest and protection-measure workflows.
- GUI-driven scenario setup, visualization, and practitioner tooling.
- Statistic Mode products with cell statistics and quantiles.
- Larger-scale operational workflow maturity.
- Broader field calibration/application history documented by SLF/WSL context
  and publications.

## Where The Project Follows A Different Philosophy

The local project is not a RAMMS clone. Its core philosophy is:

- independent literature-based implementation;
- transparent equations and limitations;
- public reproducibility before operational polish;
- no parameter tuning without a documented calibration/validation split;
- explicit probability and uncertainty semantics;
- incremental scientific experiments before broad productization.

This philosophy is appropriate for an open research tool. It is slower than
copying a mature product workflow, but safer scientifically.

## Gap Categorization

| Gap | Category | Priority | Why |
| --- | --- | --- | --- |
| Active non-spherical shape/contact | Critical scientific gap | Highest | Current public Tschamut failure modes and shape literature both point here. |
| Terrain/material calibration protocol | Critical scientific/calibration gap | High | Needed before field hazard credibility; should not mask missing shape physics. |
| Grouped validation metrics across public Tschamut | Critical validation gap | High | Needed to judge shape/contact or calibration work without overfitting. |
| GeoTIFF/COG and GIS package output | Operational/product gap | High | Required for practical Swiss pilot map review. |
| All-usable-run public Tschamut expansion | Validation gap | Medium-high | Improves block/path/outlier evidence, but may not change model structure. |
| Source frequency / physical probability model | Scientific workflow gap | Medium | Required for annual hazard probability, not immediate model diagnosis. |
| Tiled reducers / trajectory Parquet / HPC | Engineering gap | Medium | Needed for scale, but not current scientific blocker. |
| Forest/barrier/deadwood/obstacle interaction | Operational/scientific gap | Medium | Important for real sites, but after shape/material basics. |
| Fragmentation | Likely lower priority / out of scope | Low | Not clearly required by RAMMS manual parity and outside current evidence. |
| GUI/product workflow | Productization gap | Low-medium | Useful later; not needed for research credibility. |

## Ranked Future Work Packages

1. **Grouped validation and all-usable public Tschamut expansion.**
   - Strategic value: highest immediate evidence gain.
   - Risk: low.
   - Purpose: define success/failure criteria before new physics.

2. **Shape-contact design and minimal active shape prototype.**
   - Strategic value: highest physics value.
   - Risk: high unless staged.
   - Purpose: close the largest gap with RAMMS and shape literature.

3. **Terrain/material calibration protocol.**
   - Strategic value: high.
   - Risk: high if used to compensate for missing shape.
   - Purpose: turn terrain classes from schema into scientifically controlled
     parameters.

4. **GIS-ready hazard products.**
   - Strategic value: high engineering value.
   - Risk: medium.
   - Purpose: make Swiss pilot outputs reviewable in standard GIS workflows.

5. **Probabilistic source/block scenario model.**
   - Strategic value: high for hazard maps.
   - Risk: medium.
   - Purpose: move from conditional diagnostics to physical probability.

6. **Performance/scaling architecture.**
   - Strategic value: medium now, high later.
   - Risk: medium.
   - Purpose: support regional/Swiss-wide ensembles once scientific workflows
     need it.

7. **Operationalization / GUI / practitioner workflow.**
   - Strategic value: low now, high only after science matures.
   - Risk: high distraction.

## What Should NOT Be Copied From RAMMS Philosophy

- Do not treat a mature GUI/product workflow as a substitute for open
  scientific validation.
- Do not hide calibration choices behind default terrain categories without
  documenting training data, held-out validation, and uncertainty.
- Do not collapse probability semantics into a single "reach probability" term
  when maps may be unweighted, sampling-weighted, conditional, or annualized.
- Do not try to reproduce proprietary internals or undocumented algorithms.
- Do not prioritize operational features such as protection structures before
  the core open model explains current public benchmark failures.
- Do not make default physics changes simply because a state-of-practice tool
  exposes a capability.

## Where This Project Can Differentiate Scientifically

- Open, executable public benchmarks with negative results preserved.
- Explicit failure-mode reports before model extensions.
- Dataset-role discipline: impact calibration, trajectory validation,
  deposition validation, and hazard-map post-processing remain separate.
- Manifested provenance for terrain, release zones, terrain classes, shape,
  probability semantics, and outputs.
- Auditable probability taxonomy from unweighted diagnostics to future annual
  exceedance frequency.
- A public bridge between experimental datasets such as Chant Sura/Tschamut and
  open hazard-layer generation.
- A staged shape-contact program that can be reviewed independently of
  calibration.

## Roadmap Recommendation

Immediate next work package:

> Expand grouped public Tschamut validation and define no-tuning success
> criteria for future model comparisons.

This should include all usable public runs, block/shape class grouping,
observed-runout quantiles, impact-count classes, lateral spread, energy/jump
layers, and outlier QA.

Next scientific work package:

> Design and implement a minimal active shape-contact prototype only after the
> grouped metrics define what must improve and what must not degrade.

The prototype should start with shape/orientation state and a very limited,
well-tested contact extension. It should not attempt to reproduce RAMMS
internals.

Next engineering work package:

> Add GIS-ready GeoTIFF/COG hazard export with CRS/provenance metadata for
> public and private Swiss pilot workflows.

This should follow the scientific grouping work because the exported maps must
carry clear semantics.

Explicitly deferred:

- terrain/material calibration runs before a held-out protocol exists;
- annual-frequency hazard maps before source-frequency inputs exist;
- trajectory Parquet or tiled reducers until a larger workflow requires them;
- forest/barrier/deadwood modules until core shape/material mismatch is better
  understood;
- any operational hazard claim.

## Bottom Line

RAMMS::ROCKFALL is publicly documented as a mature, shape-aware, rigid-body,
terrain-material and GIS-oriented rockfall tool. The local project is much
younger and scientifically weaker in active physics and operational workflow,
especially for shape/contact and calibrated terrain interaction.

The local project is already strong as an open research platform: transparent
benchmarks, manifests, probability semantics, and failure-mode analysis are
more auditable than typical proprietary workflows. The strategic path is not to
copy RAMMS, but to close the most consequential public gaps in an open,
testable order: grouped validation first, active shape/contact second,
terrain/material calibration third, and GIS/product scaling around those
validated semantics.
