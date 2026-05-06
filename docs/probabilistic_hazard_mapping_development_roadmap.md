# Probabilistic Hazard Mapping Development Roadmap

Status: development roadmap for selected Swiss-region hazard-map production. This
document reframes the project objective around transparent, reproducible,
probabilistic rockfall hazard maps. It does not implement physics, tune
parameters, change defaults, or claim operational hazard-map validity.

## Purpose

The practical target is to generate reviewable probabilistic rockfall hazard
maps for selected Swiss regions using open methods, explicit assumptions, and
reproducible provenance. Scientific model development remains important, but it
is no longer the organizing objective by itself. Contact-model research,
including active shape-contact physics, should support the map product when it
addresses map-relevant failure modes that cannot be handled by source-zone,
scenario, terrain/material, or uncertainty workflows.

This roadmap preserves the existing benchmark discipline:

- public Tschamut grouped validation remains the main deposition/runout
  evidence base;
- Chant Sura remains trajectory/contact validation evidence;
- Mel de la Niva and other public benchmarks should be added as independent
  validation evidence, not as tuning targets;
- RAMMS comparisons remain public-evidence gap analyses only, with no copying of
  proprietary internals and no equivalence claims.

## Product Reframe

The project should now be organized around the questions a map reviewer needs to
answer:

- which source zones were included, and how were they defined;
- which release-frequency or activity assumptions were used;
- which block-size, block-shape, and release-condition scenarios were sampled;
- which terrain, material, forest, barrier, and environmental assumptions were
  included or explicitly omitted;
- whether a layer is conditional on a release scenario, sampling-weighted, or
  annualized;
- how uncertainty and sensitivity are represented;
- whether GIS outputs carry CRS, vertical datum, grid alignment, nodata,
  scenario, and provenance metadata;
- which validation/calibration evidence constrains the model and which
  assumptions remain unsupported;
- whether the workflow scales from a slope pilot to a selected regional domain
  without losing deterministic reproducibility.

The current simulator can already support early conditional map products. It
cannot yet support annualized probabilistic hazard maps without a source-frequency
model, block-volume probability model, scenario probability semantics, validation
of probabilistic inputs, and GIS-ready outputs.

## Minimum Viable Hazard-Map Product

### What Can Be Produced Now

With current model capabilities, the minimum viable product is a conditional or
sampling-weighted scenario map for a bounded source-zone pilot. It can use the
existing deterministic simulation kernel, source-area metadata, trajectory
metadata, sampling weights, and hazard-layer builder to produce transparent
research layers for review.

The product is useful when it is labelled as:

- conditional on a specified source zone, release sampling policy, terrain
  input, block scenario set, model version, and seed policy;
- sampling-weighted when scenario weights are used only to correct or express
  the sampling design;
- not annualized unless source activity and release-frequency assumptions are
  explicit, justified, and propagated into the layer units.

### Required Review Layers

The minimum layer set should include:

- `reach_probability`: fraction or weight-normalized fraction of trajectories
  that touch each cell;
- `deposition_density`: fraction or weight-normalized fraction of final
  deposition points per cell;
- kinetic-energy intensity: maximum and threshold exceedance layers, with units
  and thresholds recorded;
- jump-height intensity: maximum and threshold exceedance layers, with terrain
  source and terrain-evaluation policy recorded;
- exceedance layers for kinetic energy, jump height, and velocity where
  thresholds are relevant to the review question;
- source-zone and scenario metadata layers or tables, including source-zone id,
  release-cell ids, release sampling policy, block scenario ids, block mass or
  volume class, and model configuration id;
- uncertainty or sensitivity indicators showing variation across source-zone,
  block-size, terrain/material, and model-variant assumptions.

### Required Labels

Every map package must state one of these probability semantics:

- `unweighted_diagnostic`: trajectory-count layers with no probability claim;
- `sampling_weighted_conditional`: weighted layers normalized over the sampled
  scenario set, conditional on the specified source/scenario filter;
- `physical_probability`: conditional probability using physical scenario
  probabilities but no temporal frequency;
- `annual_frequency`: annualized exceedance or reach frequency using explicit
  source activity and release-frequency assumptions.

The current production target should be Level 1 or Level 2. Level 3 and Level 4
require additional evidence and workflow maturity.

### What Cannot Yet Be Claimed

Current outputs must not be presented as:

- operational Swiss hazard maps;
- risk maps;
- RAMMS-equivalent products;
- calibrated design-intensity products;
- annual probabilities unless a temporal source-frequency model is included;
- physically complete block-shape products while shape metadata remains passive
  or active shape-contact is only design work.

## Maturity Levels

### Level 0: Diagnostic Simulation Outputs

Objective: Produce transparent trajectory and post-processing diagnostics for
verification, validation, and workflow debugging.

Required inputs:

- analytic terrain, small DEM fixtures, or public benchmark terrain proxies;
- explicit release points or small release-point CSVs;
- explicit block parameters;
- model configuration and seed policy.

Required model capabilities:

- deterministic single-trajectory kernel;
- current sphere translational and opt-in rotational modes;
- optional roughness, scarring, passive shape metadata, and impact diagnostics;
- hazard-layer post-processing over existing simulation outputs.

Required metadata/provenance:

- case id, model version, config hash where available;
- seed policy, trajectory ids, output row counts;
- dataset role and validation/calibration status.

Required validation evidence:

- synthetic verification;
- public benchmark comparison where applicable;
- no claim beyond diagnostic interpretation.

Required GIS outputs:

- CSV, JSON, ESRI ASCII, GeoJSON, PNG/HTML diagnostics as appropriate.

Remaining limitations:

- no complete probability semantics;
- no CRS-bearing raster product;
- no source-frequency model;
- no regional scalability guarantee.

Go/no-go criteria:

- go when diagnostics reproduce deterministically and no generated large outputs
  are required in git;
- no-go for map-product language unless probability, source-zone, and GIS
  metadata are added.

### Level 1: Conditional Source-Zone Hazard Maps

Objective: Produce GIS-reviewable hazard layers conditional on a documented
source zone and scenario set.

Required inputs:

- swissALTI3D-style terrain crop with LV95/LN02 metadata;
- source-zone polygon or raster mask with provenance;
- deterministic release-cell sampling policy;
- explicit block scenario set;
- terrain/material assumptions labelled as uncalibrated, literature-based,
  transferred, or calibrated.

Required model capabilities:

- deterministic ensembles over source-zone release cells;
- full-ensemble reach, deposition, intensity, and exceedance layer generation;
- explicit-grid or reference-grid rasterization;
- manifest-backed output provenance.

Required metadata/provenance:

- CRS, vertical datum, extent, cell size, nodata, terrain source tile ids;
- source-zone id, sampling mode, release-cell ids, trajectory ids;
- scenario ids, block classes, model configuration id, calibration status;
- probability semantics set to conditional or unweighted diagnostic.

Required validation evidence:

- Tschamut and Chant Sura evidence cited as model-performance context;
- documented limitations for the selected region;
- no local tuning unless a separate calibration protocol is approved.

Required GIS outputs:

- CRS-aware raster exports as the target, preferably GeoTIFF/COG;
- interim CSV/ASCII only as development artifacts;
- vector source-zone/release overlays in GeoJSON or GeoPackage.

Remaining limitations:

- no annual probability;
- source-zone activity not quantified;
- block-volume distribution may be scenario-defined rather than probabilistic;
- forest, barriers, and environmental factors may be omitted or sensitivity-only.

Go/no-go criteria:

- go when source-zone geometry, terrain metadata, scenario set, and layer
  semantics are complete enough for independent review;
- no-go if a reviewer cannot reconstruct what the map is conditional on.

### Level 2: Sampling-Weighted Scenario Hazard Maps

Objective: Combine multiple source-zone, block, release-condition, and model
  scenarios with explicit sampling weights while remaining conditional on the
  chosen scenario universe.

Required inputs:

- Level 1 inputs;
- scenario table with source-zone ids, block-size classes, block-shape classes,
  release-condition classes, terrain/material assumption ids, and sampling
  weights;
- normalization convention and filters.

Required model capabilities:

- trajectory metadata table joined to hazard-layer generation;
- sampling-weighted reach and exceedance layers;
- deterministic seed derivation independent of trajectory execution order;
- scenario-filtered map generation.

Required metadata/provenance:

- probability mode, weight column, normalization convention, total included
  weight, excluded filters, and absolute probability mass if applicable;
- scenario table checksum and version;
- map package manifest tying rasters to scenario ids and trajectory id ranges.

Required validation evidence:

- Level 1 evidence;
- sensitivity checks showing how weights affect reach, deposition, and intensity
  patterns;
- public benchmark comparison with no tuning to Tschamut, Chant Sura, and Mel de
  la Niva where data are available.

Required GIS outputs:

- weighted and unweighted layers side by side for audit;
- scenario contribution or sensitivity layers;
- map index describing units and conditioning.

Remaining limitations:

- sampling weights are not release frequencies;
- physical scenario probabilities may still be subjective or design-only;
- annual exceedance cannot be inferred without temporal occurrence rates.

Go/no-go criteria:

- go when weights are nonnegative, normalized according to a documented
  convention, and traceable to scenario definitions;
- no-go if weights are used to hide calibration or to imply annual probability.

### Level 3: Annualized Probabilistic Hazard Maps

Objective: Produce annual-frequency or time-window hazard layers for a selected
region using explicit source activity and scenario-frequency assumptions.

Required inputs:

- Level 2 inputs;
- source-zone activity model or inventory-based frequency model;
- block-volume or block-mass frequency distribution;
- source-zone conditional release probabilities or annual rates;
- documented time horizon and assumptions for independence or event counting.

Required model capabilities:

- physical probability and annual-frequency probability modes;
- layer units that distinguish probability in a time window, annual frequency,
  and conditional exceedance;
- scenario aggregation that preserves absolute probability mass;
- uncertainty propagation over source activity, volume distribution, terrain, and
  material assumptions.

Required metadata/provenance:

- temporal units, source-frequency model id, source activity evidence,
  block-volume distribution source, scenario probabilities, uncertainty model,
  and calibration/validation status;
- annual-frequency checksums and reducer manifests.

Required validation evidence:

- independent benchmark validation for trajectory and deposition behavior;
- calibration protocol separating training and holdout evidence;
- inventory or historical event evidence for source-frequency assumptions where
  available;
- uncertainty report showing dominant assumptions and unsupported components.

Required GIS outputs:

- annual reach or exceedance frequency rasters;
- conditional component rasters for audit;
- uncertainty/sensitivity rasters;
- source-zone and scenario tables in GIS-readable packages.

Remaining limitations:

- still hazard, not risk;
- operational acceptability requires external expert review;
- source-frequency uncertainty may dominate physics uncertainty.

Go/no-go criteria:

- go when frequency assumptions are explicit, reviewed, and separable from model
  calibration;
- no-go if frequency is guessed only to make annualized labels possible.

### Level 4: Operationally Reviewable Regional Hazard Products

Objective: Produce a reproducible regional hazard package suitable for expert
  review as an operational candidate, while still avoiding claims of official
  validity unless accepted by the responsible review process.

Required inputs:

- Level 3 inputs;
- complete regional terrain tiles and source-zone inventory;
- documented forest, barrier, and environmental assumptions or exclusions;
- regional QA overlays such as hillshade, SWISSIMAGE, geological context, and
  infrastructure context where relevant to hazard review;
- external review requirements.

Required model capabilities:

- tiled, resumable, deterministic regional orchestration;
- chunked trajectory/event storage or direct streaming reducers;
- GeoTIFF/COG raster products and GIS vector packages;
- QA reports, completion manifests, checksums, and failure reporting.

Required metadata/provenance:

- per-tile and per-region manifests;
- terrain tile ids, source versions, checksums, preprocessing operations;
- chunk ids, trajectory id ranges, reducer merge rules, random seed policy;
- calibration status, validation evidence, known exclusions, and review status.

Required validation evidence:

- multi-site validation across public benchmarks and any approved local evidence;
- calibration and holdout separation;
- uncertainty and sensitivity protocol accepted by reviewers;
- comparison to available field observations without hidden tuning.

Required GIS outputs:

- COG rasters aligned to Swiss reference grids;
- release-zone, scenario, and metadata vector/table packages;
- map package index and machine-readable manifests;
- human-readable QA report.

Remaining limitations:

- not a risk product without exposure and vulnerability;
- not official unless accepted through the relevant authority or review process;
- protective structures and forest effects may require additional models.

Go/no-go criteria:

- go when the product is reproducible from source data, manifests, and scenario
  definitions and when limitations are visible in the map package;
- no-go if large parts of source activity, terrain/material policy, or QA
  evidence remain informal.

## Re-Ranked Development Priorities

| Rank | Priority | Rationale | Roadmap action |
| --- | --- | --- | --- |
| 1 | Map semantics and scenario model | Probability labels, conditioning, source-zone identity, and normalization determine whether a layer can be interpreted. | Promote to immediate mainline work. |
| 2 | Source-zone definition and release sampling | Hazard maps are source-zone products, not just trajectory collections. | Promote ahead of new physics. |
| 3 | GIS-ready conditional outputs | Swiss review workflows need CRS, vertical datum, reference grids, and GeoTIFF/COG-style rasters. | Promote ahead of annualization. |
| 4 | Scenario weighting and normalization | Current weighted layers are useful only when their conditional semantics are explicit. | Promote as Level 2 mainline. |
| 5 | Uncertainty communication | Conditional and weighted maps need sensitivity layers before users can judge robustness. | Promote into every map phase. |
| 6 | Regional workflow orchestration | Selected Swiss regions require tiled, resumable execution and chunk manifests. | Promote after Level 1 output semantics. |
| 7 | Validation and calibration protocol | Tschamut, Chant Sura, and Mel de la Niva constrain credibility but must not become hidden tuning loops. | Keep central and explicit. |
| 8 | Terrain/material parameter policy | Material assumptions strongly affect runout and energy, but calibration must be separated from map semantics. | Reframe as map-readiness support. |
| 9 | Performance and scalable formats | Needed for regional runs, but premature before product semantics and reducer contracts. | Reframe around map production, not raw speed. |
| 10 | Active shape-contact physics | WP1 shows block/shape effects matter, but conditional map generation should not wait for new physics. | Keep as supporting research until map criteria require it. |
| 11 | Forest, barrier, and environmental assumptions | Important for real regions, but require separate model and evidence policies. | Defer from minimum viable product; include as sensitivity/exclusion metadata. |
| 12 | Risk modelling | Requires exposure and vulnerability. | Explicitly out of scope for this roadmap. |

## Existing Roadmap Item Disposition

### Promoted

- probabilistic scenario identity and probability semantics;
- source-zone metadata, deterministic source-cell sampling, and release-zone
  provenance;
- trajectory metadata and scenario-weight joins;
- CRS/reference-grid metadata and GeoTIFF/COG export;
- chunk manifests, reducer checksums, and regional workflow reproducibility;
- uncertainty and sensitivity layer design.

### Reframed

- hazard-layer prototypes become the seed of Level 1 and Level 2 map products,
  not just diagnostic reports;
- weighted hazard layers become sampling-weighted conditional maps until source
  activity and physical scenario probabilities exist;
- RAMMS gap analysis becomes a product-gap inventory for maps, GIS, source
  models, and validation, not a target for copying physics;
- terrain/material calibration becomes a documented map-readiness protocol rather
  than a way to repair every benchmark discrepancy;
- scalability work becomes tile/reducer/manifest work tied to selected Swiss
  regions.

### Deferred

- annualized hazard maps until source activity, block-volume frequency, and
  temporal occurrence assumptions are explicit;
- operational regional products until the workflow has external review,
  complete geodata provenance, and accepted uncertainty communication;
- forest, barrier, and protection-structure modelling until there is a scoped
  evidence and validation plan;
- full polyhedral contact and multi-shape active contact until the minimal
  shape-contact design passes go/no-go criteria;
- GIS productization beyond necessary GeoTIFF/COG and metadata export.

### Supporting Research

- active shape-contact physics;
- rotational/contact-model variants;
- scarring and roughness model refinements;
- block-shape metadata expansion;
- benchmark expansion and no-tuning comparative analysis;
- terrain/material calibration experiments.

These items remain valuable, but they should feed map-credibility decisions
rather than define the main development sequence.

## Staged Development Roadmap

## Phase 1: Map Semantics And Scenario Model

Objective: make every future map layer explicit about what probability, scenario,
and source-zone quantity it represents.

Status: complete for Level 1 conditional and Level 2 sampling-weighted
semantics. The repository now includes source-zone, scenario-table, and
map-package parsers/validators; opt-in propagation into
`trajectory_metadata_table_v1`; labelled hazard manifests and
`map_package_manifest_v1` output; and a CI-safe smoke example. `physical_probability`
and `annual_frequency` remain schema-visible but unsupported for generated Phase
1 map products.

Deliverables:

- map-semantics schema covering unweighted, sampling-weighted, physical
  probability, and annual-frequency modes;
- source-zone, scenario, block-class, terrain/material-assumption, and model
  configuration identifiers;
- normalization conventions for conditional and weighted layers;
- map-package manifest outline.

Implementation tasks:

- extend design documents and schemas before code changes;
- define scenario-table fields for source zone, release cell, block class,
  shape class, release condition, model configuration, and sampling weight;
- define how trajectory metadata joins to hazard-layer generation;
- define failure reporting for missing or inconsistent probability fields.

Documentation tasks:

- update hazard-layer, probabilistic scenario, and dataset-strategy docs with
  product labels;
- add examples distinguishing conditional output from annual hazard probability;
- state that risk remains out of scope.

Tests/checks:

- schema consistency checks for probability mode and normalization;
- documentation consistency check for allowed probability labels;
- fixed-seed metadata examples.

Scientific risks:

- scenario weights may be mistaken for physical probabilities;
- block-size distributions may be asserted without evidence.

Product risks:

- users may read a conditional layer as annual hazard if labels are weak;
- map packages may become complex before GIS outputs are usable.

Dependencies:

- existing trajectory metadata design;
- current weighted hazard-layer prototype;
- dataset role separation.

Success criteria:

- a reviewer can tell what each layer is conditional on;
- no layer can be labelled annualized without temporal fields;
- existing defaults and unweighted outputs remain unchanged.

Stop/defer criteria:

- defer annual-frequency work if source activity evidence is unavailable;
- stop if map labels cannot be represented in manifests without ambiguity.

## Phase 2: GIS-Ready Conditional Hazard Products

Objective: produce Level 1 conditional source-zone hazard maps for a small Swiss
pilot domain with GIS metadata and reviewable layers.

Status: first implementation slice complete for additive GeoTIFF export of
existing hazard rasters. The current writer preserves raster values as float64
GeoTIFF, records affine/nodata/EPSG metadata where available, and leaves COG
compression/tiling/overview guarantees deferred.

Deliverables:

- reference-grid definition with EPSG:2056/LN02 metadata;
- GeoTIFF or COG export path for reach, deposition, energy, jump-height, and
  exceedance layers;
- source-zone and release-cell vector/table outputs;
- map package manifest with terrain, source-zone, scenario, seed, and model
  provenance.

Implementation tasks:

- add CRS-bearing raster export outside the trajectory kernel;
- make hazard layers align to an explicit reference grid;
- write source-zone and release-cell metadata with checksums;
- keep CSV/ASCII debug outputs as optional development artifacts.

Documentation tasks:

- document map-package contents and layer units;
- document CRS, vertical datum, nodata, extent, and grid-alignment requirements;
- mark outputs as conditional research products.

Tests/checks:

- CRS/reference-grid metadata validation;
- GeoTIFF/COG smoke checks where dependencies are available;
- raster alignment and nodata checks;
- deterministic regeneration of a small pilot map package.

Scientific risks:

- conditional maps may overstate confidence if source-zone and material
  assumptions are weak;
- current sphere contact may under-run contact-rich releases.

Product risks:

- GIS users may expect operational status from standard raster formats;
- missing source-zone provenance would undermine reviewability.

Dependencies:

- Phase 1 map semantics;
- swisstopo terrain-ingestion metadata;
- existing hazard-layer builder.

Success criteria:

- a complete conditional map package can be regenerated from checked-in or
  documented local inputs;
- every raster carries or is packaged with CRS and provenance;
- limitations are visible in the package.

Stop/defer criteria:

- defer if CRS-bearing export cannot be verified;
- stop if source-zone definition is informal or not reproducible.

## Phase 3: Regional Pilot Workflow

Objective: scale from a single slope/corridor to a selected Swiss regional pilot
without changing physics or losing reproducibility.

Deliverables:

- tiled terrain and source-zone input layout;
- chunk manifest schema for trajectory ranges, source-zone batches, tile ids,
  reducer states, checksums, and completion status;
- deterministic job partitioning and merge rules;
- regional QA report template.

Implementation tasks:

- define chunk ids from source-zone id, release-cell range, scenario id,
  trajectory id range, and global seed;
- add tile-wise or chunk-wise hazard accumulation;
- define reducer merge operations for counts, weighted counts, maxima, and
  exceedances;
- separate debug trajectory storage from production reduced layers.

Documentation tasks:

- document regional execution layout and restart/resume policy;
- document what artifacts are audit records and what artifacts are map products;
- document storage policy for raw trajectories, events, and reduced layers.

Tests/checks:

- order-independent seed and reducer tests;
- chunk merge equivalence with a single local run;
- manifest completeness checks;
- generated-output staging checks.

Scientific risks:

- region-wide source-zone assumptions may vary more than the current model can
  represent;
- terrain/material class policy may dominate runout results.

Product risks:

- too many debug files can make runs unmanageable;
- incomplete chunks can be mistaken for complete regional products.

Dependencies:

- Phase 2 GIS-ready outputs;
- scalability and data-format decisions;
- regional terrain/source-zone pilot inputs.

Success criteria:

- a regional pilot can be resumed, audited, and merged deterministically;
- chunk outputs can be traced to source zones, scenarios, and input tiles;
- map layers are complete or explicitly marked incomplete.

Stop/defer criteria:

- defer region expansion if single-pilot map semantics are not settled;
- stop if reducer merge rules cannot be made deterministic.

## Phase 4: Validation, Calibration, And Uncertainty Protocol

Objective: define how model evidence, calibration, and uncertainty support map
interpretation without hiding parameter tuning.

Deliverables:

- validation matrix linking Tschamut, Chant Sura, Mel de la Niva, synthetic
  verification, and regional pilot evidence to map claims;
- terrain/material calibration protocol with training/holdout separation;
- uncertainty layer design for source zones, block scenarios, terrain/material
  classes, model variants, and source frequency;
- failure-reporting format for worse-than-baseline results.

Implementation tasks:

- add evaluation scripts only after the protocol is documented;
- compute no-tuning benchmark comparisons for each candidate model/configuration;
- preserve baseline and opt-in model outputs side by side;
- add uncertainty/sensitivity reducers where needed.

Documentation tasks:

- document calibration status in manifests and map packages;
- document what evidence supports trajectory shape, runout, deposition, contact
  timing, energy, and map-layer interpretation;
- keep operational validity disclaimers visible.

Tests/checks:

- benchmark cases skip gracefully when data are absent;
- calibration and validation cases remain separated;
- uncertainty outputs are labelled by assumption family and not as risk layers.

Scientific risks:

- calibration may overfit public benchmarks;
- source-frequency uncertainty may be larger than contact-model differences.

Product risks:

- map users may prefer a tuned-looking map over a transparent uncertainty report;
- failure cases may be underreported unless required by workflow checks.

Dependencies:

- public benchmark framework and dataset metadata;
- Phase 1-3 map semantics and outputs;
- agreed terrain/material parameter policy.

Success criteria:

- every map package states calibration status and validation evidence;
- sensitivity outputs make dominant uncertainties visible;
- worse model results are reported rather than hidden.

Stop/defer criteria:

- defer calibration if holdout evidence is insufficient;
- stop if parameter changes would silently alter defaults.

## Phase 5: Improved Physics Such As Active Shape-Contact

Objective: introduce opt-in physics improvements only when they address
map-relevant failures and pass pre-defined verification and no-tuning evaluation.

Deliverables:

- implementation-ready active shape-contact specification derived from
  `active_shape_contact_design.md`;
- minimal opt-in model name and version, for example `shape_contact_v0`;
- verification suite for inertia, quaternion normalization, free flight,
  flat-plane contact, dissipative impacts, determinism, and backward
  compatibility;
- no-tuning Tschamut, Chant Sura, and Mel de la Niva comparison report.

Implementation tasks:

- start with one shape type if approved, such as principal-dimensions box;
- implement deterministic orientation initialization and simple support-point
  contact only after go/no-go questions are resolved;
- keep fallback to current sphere modes;
- do not change defaults.

Documentation tasks:

- document active state variables, inertia usage, contact geometry, energy
  accounting, and diagnostics;
- document which WP1 failure modes improved, worsened, or remained unresolved;
- document map-layer impact of the new physics.

Tests/checks:

- mass/inertia consistency;
- quaternion normalization;
- free-flight conservation;
- flat-plane resting/contact sanity;
- energy non-creation under dissipative impacts;
- deterministic fixed-seed behavior;
- backward compatibility for current models;
- no-tuning public Tschamut comparison;
- Chant Sura trajectory/contact comparison.

Scientific risks:

- active shape contact may add energy or over-run in a rotational-style way;
- WP1 block effects remain confounded with terrain/path effects;
- terrain/material calibration might be the more important missing factor.

Product risks:

- a new model may delay conditional map products without improving map
  credibility enough;
- users may treat an opt-in shape model as validated before benchmark evidence
  supports it.

Dependencies:

- Phase 4 evaluation protocol;
- active shape-contact go/no-go resolution;
- existing passive shape metadata and benchmark sidecars.

Success criteria:

- contact-rich early stopping is reduced without broad high-energy over-run;
- block-specific behavior for Tschamut blocks 1, 2, and 4 is reported;
- Chant Sura trajectory/contact diagnostics are preserved or improved;
- failures are reported if the new model is worse.

Stop/defer criteria:

- defer if terrain/material calibration is a clearer explanation of map errors;
- stop if energy accounting, support-point selection, or orientation semantics
  are not clear enough before coding.

## Phase 6: Scale-Up And Operationalization

Objective: mature selected-region products into operationally reviewable regional
hazard packages, without claiming official status unless external review accepts
them.

Deliverables:

- regional map package format with COG rasters, vector overlays, metadata tables,
  manifests, QA report, and reproducibility instructions;
- annual-frequency mode where source activity evidence supports it;
- external-review checklist;
- production storage and retention policy.

Implementation tasks:

- harden tiled orchestration and resumable reducers;
- implement annual-frequency aggregation only after Phase 1-4 requirements are
  met;
- add map package validation checks;
- add optional context overlays for forest, barriers, geology, roads, and
  buildings without converting hazard to risk.

Documentation tasks:

- document operational-use boundary and review status;
- document annual-frequency assumptions and uncertainty;
- document excluded effects and known weak regions.

Tests/checks:

- complete map package validation;
- reproducibility from manifests;
- regional chunk completeness and checksum checks;
- optional dependency checks for GIS export.

Scientific risks:

- source-frequency and environmental assumptions may dominate all physics
  improvements;
- validation evidence may not span the selected region's terrain and lithology.

Product risks:

- users may treat reviewable products as official products;
- context overlays may be misread as exposure or risk.

Dependencies:

- Level 3 probability semantics;
- regional source-zone inventory and frequency evidence;
- GIS export and chunked workflow maturity;
- external review process.

Success criteria:

- selected-region products are reproducible, auditable, and explicit about
  probability semantics;
- maps include uncertainty/sensitivity layers and failure notes;
- no operational validity is claimed without review.

Stop/defer criteria:

- defer operationalization if external review criteria are unavailable;
- stop if annualization cannot be justified from source activity evidence.

## What Shape-Contact Physics Contributes To Hazard Mapping

Shape-contact physics matters because WP1 Tschamut evidence shows that block and
contact-rich behavior are map-relevant. The baseline model under-runs on average
and systematically under-runs high-impact/contact-rich releases. The current
rotational sphere mode moves too far in the opposite direction, over-running
most public Tschamut releases and producing broad high-energy output. A minimal
active shape-contact model could reduce early stopping while avoiding the
rotational-style systematic over-run.

Shape-contact physics does not solve:

- source-zone definition;
- source activity or annual release frequency;
- block-volume frequency distributions;
- terrain/material parameter policy;
- forest, barriers, or protection structures;
- GIS export and regional workflow scale;
- uncertainty communication;
- operational validation.

It should not block conditional map generation because Level 1 and Level 2 maps
can still be valuable when they are honestly labelled as conditional products
from the current model. These products expose source-zone, terrain, scenario,
and workflow gaps that must be solved regardless of the contact model.

Shape-contact becomes necessary for map credibility when:

- benchmark evidence shows that current sphere modes systematically bias reach,
  deposition, energy, or jump-height layers for the target source/terrain class;
- source-zone and terrain/material assumptions are documented well enough that
  contact physics is a leading residual error;
- opt-in shape-contact verification and no-tuning validation show improvement
  without energy creation or broad over-run;
- block-specific map interpretation depends on shape classes rather than only
  mass/radius scenarios.

## What Is Required Before Calling Outputs Probabilistic Hazard Maps

Before an output is called a probabilistic hazard map, it must include more than
a set of trajectory-count rasters.

Temporal frequency:

- annual or time-window labels require source-zone release rates or occurrence
  probabilities;
- temporal units and event-count assumptions must be recorded;
- without this, the output is conditional or scenario-weighted, not annualized.

Source activity:

- source zones must have documented activity assumptions or inventory evidence;
- dormant, uncertain, and active zones must be distinguishable;
- source-zone inclusion and exclusion rules must be reproducible.

Block-volume distributions:

- block mass, radius, volume, or shape scenarios must be tied to a documented
  distribution or explicitly labelled as design scenarios;
- sampling weights must not be confused with physical block-frequency weights;
- block-specific uncertainty must be carried into map summaries.

Scenario weights:

- weights must state whether they are sampling corrections, subjective scenario
  weights, physical probabilities, or annual rates;
- normalization must state whether layers are conditioned on a filter or carry
  absolute probability mass;
- excluded scenarios and filters must be recorded.

Uncertainty:

- uncertainty should cover source zones, release locations, block volumes,
  terrain/material assumptions, model variants, and source frequencies;
- sensitivity layers should be part of the map package, not optional prose only;
- unsupported assumptions must remain visible.

Validation evidence:

- trajectory, deposition, contact, energy, and map-layer evidence must be cited
  by dataset role;
- calibration and validation evidence must remain separated;
- public benchmark failures must be reported even when the new product is worse.

Conditional output versus hazard probability:

- a conditional map answers "where do simulated blocks go if this source/scenario
  set releases";
- a sampling-weighted conditional map answers the same question with weights over
  a defined scenario sample;
- an annualized probabilistic hazard map answers "how often is this location
  expected to be reached or exceeded under stated source activity and scenario
  frequency assumptions";
- risk maps additionally require exposure, vulnerability, and consequence
  modelling and are outside this roadmap.

## Immediate Next Decisions

The next development decisions should be made in this order:

1. settle the map-semantics and scenario-model schema;
2. choose the minimum GIS-ready raster export path for Level 1 products;
3. define source-zone and release-cell metadata for the first selected Swiss
   pilot region;
4. define scenario weighting and uncertainty outputs for Level 2 products;
5. design regional chunk manifests and deterministic reducer merges;
6. decide whether active shape-contact is ready to implement based on the
   go/no-go criteria in the design document and the map-product evaluation
   needs.

This order keeps the project focused on transparent Swiss hazard-map production
while preserving the scientific benchmark work needed to understand and improve
the physics.
