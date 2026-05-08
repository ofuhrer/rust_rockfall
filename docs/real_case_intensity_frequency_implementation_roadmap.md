# Real-Case Intensity-Frequency Pilot Implementation Roadmap

Status: progress-aware implementation roadmap for reaching a public-dataset,
real-case Swiss pilot that produces grid-cell conditional intensity-exceedance
products and, later, true physical or annual intensity-frequency curves. This
document does not change simulator behavior, claim operational validity,
introduce annual frequencies, or redefine current hazard-map semantics.

## Target Definition

The long-term target is a reproducible workflow that starts from public Swiss
geodata and produces, for each hazard-grid cell in a real pilot domain, an
intensity curve such as kinetic-energy or jump-height exceedance versus
frequency.

There are two distinct milestones:

1. Conditional intensity-exceedance pilot: for each grid cell, report
   threshold-exceedance fractions or sampling-weighted conditional fractions
   over a documented source-zone, block-scenario, release-sampling, and model
   configuration set.
2. Physical or annual intensity-frequency pilot: for each grid cell, report
   exceedance frequency with physical probability or annual units, for example
   `1/year`.

The repository is close to milestone 1 at the tooling and contract level, but
milestone 1 is not complete until a selected public Swiss pilot domain has been
prepared, frozen, run, packaged, and reviewed. It is not yet close to milestone
2 because source-zone occurrence frequency, block-population frequency,
annualization, and validation semantics remain unsupported by
`docs/hazard_map_semantics.md` and `docs/probabilistic_scenario_model_design.md`.

## Current Baseline

Already available:

- deterministic equivalent-sphere trajectory ensembles;
- analytic and ESRI ASCII DEM terrain paths;
- small swissALTI3D-style fixtures with LV95/LN02 metadata;
- source-zone and terrain-class metadata sidecars;
- scenario metadata and `sampling_weighted_conditional` hazard layers;
- reach, deposition, maximum kinetic energy, maximum jump height, significant
  impact density, and threshold-exceedance layers;
- lightweight GeoTIFF export with value/metadata parity tests;
- explicit rejection/deferment of COG, annual frequency, and physical
  probability claims;
- dry-runnable DEM/terrain-representation sensitivity fixture;
- public real-site geodata manifest template and validator;
- source-zone/block-scenario policy template and validator;
- public real-site conditional pilot run-freeze template and command-plan
  validator;
- diagnostic pilot GIS package manifest behind explicit GeoTIFF export;
- deterministic local hazard-layer reducer chunks through `--reducer-workers`;
- strong verification and deterministic seed/order checks.

Main missing pieces, in priority order:

1. select one public Swiss pilot domain and prepare a reproducible local
   swisstopo geodata package without committing raw tiles;
2. apply a predeclared source-zone, release-cell, and block-scenario policy to
   that domain;
3. run DEM/terrain-representation sensitivity for the selected domain before
   interpreting model behavior;
4. execute a small frozen conditional pilot gate run and record convergence,
   performance, output volume, and limitations;
5. produce a real-pilot GIS/QGIS review package with CRS, nodata, value-parity,
   source-zone overlay, and claim-boundary QA;
6. measure and improve local single-node scaling for trajectory generation and
   reducer workflows only after the pilot gate exposes bottlenecks;
7. increase ensemble size toward the target trajectory count only after the
   small gate run is reproducible and interpretable;
8. defer physical/annual frequency semantics until source-frequency and
   block-population evidence are designed and reviewable.

## Phase 0: Roadmap And Claim Hygiene

Objective: keep the conditional and annual targets separate before new code is
added.

Current status: substantially complete. The repository now has
`docs/validation_maturity_framework.md`, claim-boundary checks in
`scripts/check_repo_consistency.py`, and user-facing wording that separates
current conditional intensity-exceedance products from future physical or
annual products. Future pilot reports still need to apply the maturity labels
consistently.

Implementation work:

- add a validation maturity framework and reference it from pilot reports;
- update user-facing roadmap language so "intensity-frequency" is reserved for
  future physical/annual products;
- use "conditional intensity-exceedance" for current threshold-exceedance
  curves based on trajectory counts or sampling weights;
- add consistency checks that reject unsupported report headings or manifest
  labels for annual frequency, return period, operational approval, or risk.

Likely affected areas:

- `docs/validation_maturity_framework.md`;
- `docs/hazard_map_semantics.md`;
- `docs/roadmap_hazard_mapping.md`;
- `docs/next_development_targets.md`;
- `scripts/check_repo_consistency.py`;
- report templates.

Phase 0 implementation should use the maturity levels in
`docs/validation_maturity_framework.md` so pilot reports can label current
evidence as diagnostic, conditional, or limited field-validation evidence
without implying physical probability, annual frequency, or operational
readiness.

Done when:

- every pilot artifact can state whether it is diagnostic, conditional,
  physical-probability, or annual-frequency;
- current workflows cannot accidentally label outputs as annual frequency.

Do not:

- add annual units or return-period labels;
- treat sampling weights as physical occurrence probabilities.

## Phase 1: Public Real-Site Geodata Preparation

Objective: make one small real Swiss pilot domain reproducible from public
input geodata without committing raw tiles.

Current status: selected-domain package complete at the share-safe manifest
level. The checked-in template
`data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml`,
selected-domain manifest
`data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`, and
`scripts/validate_public_real_site_geodata_manifest.py` define the public
Tschamut pilot geodata package. The selected manifest records public
swissALTI3D tile `2696-1167`, product/version/date, source and processed
checksums, EPSG:2056/LN02, crop extent, 2 m cell size, nodata, ignored
raw/processed output roots, and the deterministic preparation command. Local
execution still requires public downloads or preplaced ignored raw files; no
raw/processed products are committed.

Implementation work:

- choose one pilot domain with a bounded source area and runout corridor;
- define a local ignored directory layout for raw and processed public
  swisstopo inputs;
- implement or document a deterministic preparation script for swissALTI3D
  tile selection, crop, checksum, CRS/datum validation, and ESRI ASCII or
  GeoTIFF-derived internal DEM export;
- optionally prepare SWISSIMAGE hillshade/orthophoto context, GeoCover or
  geology notes, and swissTLM3D context overlays for QA;
- emit terrain metadata sidecars with source tile ids, product version/date,
  license notes, checksums, crop extent, cell size, nodata, CRS, and vertical
  datum;
- run the existing DEM/terrain sensitivity fixture or its real-site extension
  on the selected domain before simulation tuning.

Likely affected areas:

- `docs/swisstopo_data_strategy.md`;
- `docs/swiss_terrain_ingestion_pilot.md`;
- `docs/dem_terrain_sensitivity_benchmark.md`;
- `scripts/prepare_*_swisstopo_pilot.py`;
- `data/datasets.yaml`;
- ignored `data/raw/swisstopo/` and `data/processed/swisstopo/` paths.

Done when:

- a clean checkout plus documented public downloads can recreate the processed
  pilot DEM and metadata locally;
- terrain provenance and DEM sensitivity results are reviewable without raw
  geodata in git.

Do not:

- commit raw swissALTI3D, SWISSIMAGE, or large context products;
- use swisstopo terrain as validation evidence by itself.

## Phase 2: Source-Zone And Block-Scenario Policy V1

Objective: create defensible conditional scenario inputs for the real-site
pilot.

Current status: selected-domain policy complete at the share-safe contract
level. The policy semantics, template, validator, and selected Tschamut public
pilot policy `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
are implemented. The selected policy predeclares a Level 1 public-release
bounding source zone, deterministic release-cell grid, representative block
scenarios, and conditional-only sampling weights before any real conditional
pilot simulation results are inspected. It rejects unsupported annual or
physical probability claims.

Implementation work:

- implement a source-zone sidecar policy using Level 1 or Level 2 evidence from
  `docs/probabilistic_scenario_model_design.md`;
- for Level 1, require explicit manual interpretation notes and QA overlays;
- for Level 2, define predeclared slope, cliff, geology, inventory, or expert
  review criteria and keep those criteria independent of simulation results;
- generate deterministic release cells inside the selected source zone with
  stable `release_cell_id` values and documented sampling weights;
- define a small block-scenario table with stable ids, representative radius or
  mass, shape metadata, and sampling weights;
- keep all weights conditional-sampling weights unless a later phase provides
  physical evidence.

Likely affected areas:

- `src/probabilistic.rs`;
- release-zone parser and metadata validation code;
- `tests/probabilistic_phase1.rs`;
- `tests/fixtures/probabilistic_phase1/`;
- `validation/cases/*pilot*.yaml`;
- `docs/probabilistic_scenario_model_design.md`.
- `docs/source_zone_block_scenario_policy_v1.md`;
- `validation/templates/public_real_site_source_scenario_policy_v1.yaml`;
- `scripts/validate_source_scenario_policy.py`.

Done when:

- source-zone, release-cell, block-scenario, and trajectory metadata join
  deterministically across manifests and hazard packages;
- the pilot can generate conditional scenario ensembles without hidden
  probability claims.

Do not:

- implement a national source-zone algorithm before one pilot-domain policy is
  auditable;
- add annual source frequencies in this phase.

## Phase 3: Conditional Intensity-Exceedance Products

Objective: produce per-grid-cell conditional intensity curves over configured
thresholds.

Current status: implemented for fixture and workflow use, pending real-pilot
execution. The hazard-layer builder can emit threshold-exceedance rasters and a
tidy conditional curve table with current probability labels and `annualized:
false`. The remaining work is to run this on the selected real pilot domain
with frozen thresholds, scenario metadata, and an explicit grid.

Implementation work:

- formalize intensity measures for the first pilot, likely kinetic energy and
  jump height, with optional velocity or momentum only if already available and
  interpretable;
- extend hazard-layer configuration to support named threshold families and
  grouped curve metadata per grid cell;
- write curve outputs as threshold stacks or tidy tables:
  `cell_id`, grid coordinates, threshold, intensity measure, numerator,
  denominator, conditional fraction, standard error or convergence diagnostic,
  probability mode, source-zone id, scenario id, and block-scenario filters;
- include both unweighted diagnostic and sampling-weighted conditional modes
  where scenario metadata are complete;
- keep maximum-value layers as separate intensity-envelope diagnostics, not
  frequency curves.

Likely affected areas:

- `scripts/build_hazard_layers.py`;
- `docs/hazard_layers.md`;
- `docs/hazard_map_semantics.md`;
- `tests/test_hazard_layers.py`;
- `tests/fixtures/hazard/`;
- map-package manifest fixtures.

Done when:

- a tiny fixture proves that per-cell threshold curves match existing
  exceedance rasters;
- generated labels and manifests clearly say conditional exceedance, not annual
  frequency;
- outputs are readable by the pilot GIS package workflow.

Implementation note: the current hazard-layer builder writes
`conditional_intensity_exceedance_curves.csv` as a tidy table whenever
threshold-exceedance layers are configured. It records unweighted diagnostic
and sampling-weighted conditional denominators with `annualized: false`.

Do not:

- report "frequency" unless units and denominators are physical or annual;
- mix maximum-intensity maps with exceedance-frequency curves.

## Phase 4: Pilot GIS/QGIS Package

Objective: make the real-site conditional hazard package inspectable by a GIS
reviewer.

Current status: diagnostic GeoTIFF export and `pilot_gis_package_manifest_v1`
exist, and tests cover value/metadata parity and explicit COG rejection. The
remaining work is a real-pilot review package and visual QA. The current code
does not create a QGIS project, GeoPackage, production COG, tiled package, or
operational product.

Implementation work:

- create a tiny QGIS package fixture with GeoTIFF rasters, CSV/ASCII parity
  files, source-zone/context sidecars, manifests, and QA notes;
- for the real pilot, export CRS-correct GeoTIFFs for selected conditional
  exceedance thresholds, reach, deposition, maximum energy, and maximum jump
  height;
- include hillshade or orthophoto QA instructions without committing large
  images;
- record visual QA for CRS alignment, nodata, source-zone overlap, release-cell
  placement, and layer interpretation;
- keep COG and QGZ packaging deferred unless a verified writer/project package
  is added.

Current Phase 4 implementation provides a diagnostic
`pilot_gis_package_manifest_v1` inventory behind explicit
`--pilot-gis-package --export-geotiff` or `pilot_gis_package.enabled: true`
configuration. It records the review rasters, parity files, sidecars, QA note,
and claim boundaries, but does not create a QGIS project, GeoPackage, COG,
physical-probability layer, annual intensity-frequency layer, or operational
hazard product.

Likely affected areas:

- `scripts/build_hazard_layers.py`;
- `docs/pilot_gis_package.md`;
- `tests/test_hazard_layers.py`;
- `hazard/results/` only for intentional tiny fixtures.

Done when:

- a reviewer can inspect a small package in QGIS and confirm alignment,
  semantics, and value parity;
- the real pilot can produce a share-safe package report without raw geodata.

Do not:

- treat debug GeoTIFF as production COG;
- style maps with annual or risk language.

## Phase 5: Deterministic Local Parallel Execution And Streaming Reducers

Objective: make valley-scale ensembles feasible on one workstation or node
before SLURM orchestration.

Current status: partially implemented in hazard-layer post-processing. The
`--reducer-workers` path gives deterministic local chunking and reducer
manifests for current hazard products. The remaining gap is upstream
trajectory-generation scale: pilot-size trajectory execution, output-volume
control, chunk/resume contracts for trajectory/event outputs, and measured
single-node performance evidence.

Implementation work:

- add an opt-in deterministic parallel runner with worker-count-independent
  results;
- define chunk ids from scenario id, source-zone id, release-cell range,
  trajectory id range, model configuration, and global seed;
- add chunk manifests with config hash, input checksums, row counts, reducer
  counts, timings, file sizes, and completion status;
- implement streaming reducers for counts, threshold exceedances, maxima,
  deposition density, and significant-impact event density;
- support merge of partial reducer states independent of execution order;
- keep full trajectory/event CSV output as explicit debug/audit mode, not the
  default for large hazard runs.

Current Phase 5 implementation starts this path in the hazard-layer reducer:
`--reducer-workers N` partitions trajectory and impact input files into
deterministic local chunks, accumulates in-memory partial reducer states in
threads, merges chunks after sorting by chunk id, and writes
`hazard_reducer_chunk_manifest_v1` sidecars. It covers current conditional
diagnostic reducers for reach, threshold exceedance, maxima, deposition density,
and significant-impact density. It does not add SLURM orchestration,
distributed storage, annual source-frequency semantics, physical probabilities,
or a new simulator kernel.

Likely affected areas:

- `src/simulation.rs`;
- `src/stochastic.rs`;
- `src/manifest.rs`;
- validation runner and CLI orchestration paths;
- `scripts/build_hazard_layers.py` or a new reducer script/module;
- `tests/hpc_readiness.rs`;
- performance benchmark docs and scripts.

Done when:

- serial and parallel runs produce identical reduced hazard outputs;
- results are independent of worker count and chunk merge order;
- a benchmark report covers timing, memory, file count, bytes, and output mode
  for pilot-scale ensemble sizes.

Do not:

- add SLURM, MPI, GPU, or distributed frameworks before local chunk/reducer
  contracts are stable;
- optimize kernel internals without pilot bottleneck evidence.

## Phase 6: Public Real-Site Conditional Pilot Run

Objective: execute the first full public-dataset real-case pilot with
conditional intensity-exceedance curves.

Current status: pre-run freeze gate only. The template and validator can check
a populated run-freeze file and emit a command plan, but the checked-in state is
`template_not_run`. No public real-site conditional pilot output, convergence
evidence, QGIS package, or pilot report has been produced yet.

Implementation work:

- freeze terrain, source-zone, block-scenario, thresholds, seeds, physics
  settings, grid, and output plan before running;
- run the ensemble at a predeclared scale, starting with a small gate run and
  then increasing toward the target number of trajectories per release zone;
- generate conditional exceedance curves per cell and selected GIS rasters;
- record convergence diagnostics, runtime, memory, file count, and output
  volume;
- write a pilot report that classifies the result as pass, no-go, or
  inconclusive against workflow gates, not as operational validation.

Current Phase 6 implementation starts with the pre-run freeze gate:
`validation/templates/public_real_site_conditional_pilot_run_v1.yaml` and
`scripts/validate_public_real_site_conditional_pilot_run.py` define the
share-safe contract for frozen inputs, gate scale, target scale, explicit grid,
conditional thresholds, output budget, run-evidence metadata for completed
gate/target runs, and pass/no-go/inconclusive report classification. The
checked-in template is `template_not_run`; real local runs must copy it to an
ignored pilot directory and populate private paths, metrics, convergence notes,
and checksums before marking a run completed.

For populated non-template freeze files, the same validator can print
`public_real_site_conditional_pilot_command_plan_v1` with the exact upstream
validators, frozen validation run, and hazard-layer command needed to generate
conditional curves, selected GeoTIFFs, the GIS package manifest, and local
reducer manifests. This keeps Phase 6 executable while still leaving generated
products out of git.

Likely affected areas:

- `validation/cases/`;
- `validation/results/` and `hazard/results/` as ignored generated outputs;
- `docs/<pilot>_public_real_case_report.md`;
- run manifests and map-package manifests.

Done when:

- the entire public-data workflow is reproducible from documented inputs;
- per-grid-cell conditional intensity-exceedance products exist;
- limitations clearly identify DEM, source-zone, shape, forest, block-scenario,
  and frequency gaps.

Do not:

- tune parameters after seeing pilot outputs;
- claim physical or annual intensity-frequency.

## Phase 7: Physical Probability And Annual Frequency Design Gate

Objective: decide whether the repo has enough evidence to add true
intensity-frequency semantics.

Current status: not started beyond guardrails and schema-visible placeholders.
Current code paths reject or defer annual and physical probability claims.

Implementation work:

- define whether frequency means conditional event frequency, annual source
  frequency, or another time convention;
- design source-frequency inputs with evidence levels, units, time horizon, and
  uncertainty;
- design block-population or event-magnitude frequency semantics;
- define how overlapping source zones combine without double counting;
- define how source-zone, block, release-cell, terrain/model-form, and scenario
  uncertainty aggregate into per-cell curves;
- add validation and calibration separation rules for any frequency parameters;
- require at least one holdout or external evidence path before using annual
  outputs as more than exploratory diagnostics.

Likely affected areas:

- `docs/hazard_map_semantics.md`;
- `docs/probabilistic_scenario_model_design.md`;
- `docs/validation_plan.md`;
- `docs/dataset_strategy.md`;
- future source-frequency schemas and tests.

Done when:

- annual or physical probability modes have schemas, fixtures, manifest fields,
  rejection tests, and allowed/disallowed language;
- the roadmap can justify implementation without confusing calibration,
  scenario weighting, and validation.

Do not:

- back-fill annual frequencies from arbitrary sampling weights;
- calibrate frequency to match a single hazard map pattern.

## Phase 8: Annual Intensity-Frequency Prototype

Objective: implement a clearly experimental annual or physical
intensity-frequency prototype after Phase 7 passes.

Current status: not started and intentionally blocked by Phase 7.

Implementation work:

- add source-frequency and block-frequency fields to scenario metadata under a
  new explicit probability mode;
- propagate frequency weights through trajectory metadata and reducers;
- emit per-cell threshold curves with units such as `1/year` only when all
  required frequency fields and normalization conventions are present;
- add tests that reject incomplete frequency metadata and compare simple
  analytic frequency sums;
- produce a small fixture where annual exceedance frequency equals a manually
  checkable weighted sum over source/scenario trajectories.

Likely affected areas:

- `src/probabilistic.rs`;
- scenario and map-package schemas;
- `scripts/build_hazard_layers.py` or streaming reducer implementation;
- `tests/probabilistic_phase1.rs` or a new frequency test module;
- `tests/test_hazard_layers.py`;
- `docs/hazard_map_semantics.md`.

Done when:

- annual frequency is impossible to request without complete frequency metadata;
- per-cell intensity-frequency curves are reproducible, unit-labelled, and
  traceable to source/scenario frequency inputs;
- reports still state non-operational validation status unless future evidence
  changes that.

Do not:

- promote annual-frequency defaults;
- imply regulatory or operational hazard-map readiness.

## Prioritized Remaining Roadmap Items

The order below supersedes the older phase-number order for near-term work.
Several lower-numbered phases now have executable scaffolding, while their
real-pilot evidence remains missing.

| Priority | Item | Why this comes next | Done when |
| --- | --- | --- | --- |
| 1 | Prepare one public real-site swisstopo pilot package | Everything downstream depends on a concrete domain, DEM, CRS/datum metadata, and provenance. | A documented clean checkout plus public/local downloads can recreate the processed pilot DEM and metadata; no raw geodata are committed. |
| 2 | Apply a domain-specific source-zone and block-scenario policy | Conditional curves are uninterpretable without frozen source, release-cell, block, and sampling assumptions. | Source-zone sidecar, release-cell ids, scenario table, and policy manifest validate and join deterministically. |
| 3 | Run DEM/terrain sensitivity on that domain | DEM representation can dominate runout and map patterns; this must be checked before calibration or physics interpretation. | Terrain variants and map/metric differences are reported with fixed physics, fixed source policy, and no tuning. |
| 4 | Execute the small frozen conditional pilot gate run | This is the first end-to-end evidence that the real-case workflow works. | The run-freeze validator passes, generated outputs include conditional curves, manifests, checksums, GIS artifacts, performance numbers, and a pass/no-go/inconclusive report. |
| 5 | Produce and review the real-pilot GIS/QGIS package | Hazard-map outputs must be interpretable in a GIS before scaling or external review. | A reviewer can inspect CRS alignment, nodata, value parity, source-zone overlays, labels, and claim boundaries without raw geodata. |
| 6 | Measure local scaling and output-volume bottlenecks | Performance matters, but optimization should follow real pilot evidence. | Single-node timing, memory, row counts, file counts, reducer parity, and output-mode tradeoffs are documented for pilot-scale runs. |
| 7 | Increase ensemble size toward the target count | Larger ensembles are useful only after the small gate is reproducible and scientifically interpretable. | Convergence diagnostics show whether increasing toward roughly 10,000 trajectories per release zone is feasible and useful for the selected domain. |
| 8 | Design physical/source-frequency semantics | Annual products require source and block occurrence evidence, not just sampling weights. | Frequency units, source/block frequency inputs, uncertainty, overlap rules, schemas, and rejection tests are specified. |
| 9 | Implement an annual/physical intensity-frequency prototype | This should happen only after the design gate passes. | A small fixture proves annual or physical frequency sums with explicit units and complete provenance. |

## Earliest Useful Pilot

The earliest scientifically honest full-chain pilot should produce:

- a public-data real-site DEM and source-zone package;
- fixed block/scenario assumptions with sampling weights only;
- deterministic ensembles;
- per-cell conditional kinetic-energy and jump-height exceedance curves;
- reach, deposition, maximum energy, maximum jump-height, and selected
  threshold-exceedance GeoTIFFs;
- a QGIS review bundle;
- convergence and performance diagnostics;
- an explicit statement that outputs are conditional research diagnostics, not
  annual frequency, physical probability, risk, or operational hazard maps.

## Decision Gates

| Gate | Blocks | Pass condition |
| --- | --- | --- |
| Public geodata reproducibility | Real-site pilot | Public inputs, local processing, metadata, and checksums recreate the DEM/context package. |
| DEM sensitivity | Calibration and pilot interpretation | Terrain variants do not expose unresolved alignment, nodata, cliff, or smoothing artifacts that dominate the result. |
| Source-zone policy | Conditional pilot | Source geometry, release cells, and evidence level are documented before simulation. |
| Scenario semantics | Conditional curves | Block/scenario ids, sampling weights, and denominators join across outputs. |
| GIS package QA | Shareable pilot output | CRS, transform, nodata, value parity, source-zone overlays, and labels pass review. |
| Local scaling | Valley-scale ensemble | Serial/parallel/reducer parity and pilot-scale resource measurements are available. |
| Validation maturity | Public claims | Reports map evidence to maturity level and avoid unsupported validation claims. |
| Frequency semantics | Annual curves | Source/block frequency inputs, units, uncertainty, overlap rules, schemas, fixtures, and rejection tests exist. |

## Explicit Deferrals

- Annual-frequency maps before Phase 7.
- Physical probability maps before source and block probability evidence exists.
- Terrain/material calibration before DEM sensitivity, pilot evidence, and
  holdout policy.
- Public shape-contact runtime before shape-readiness validation passes.
- Forest/barrier physics before pilot-domain scoping.
- SLURM/CSCS orchestration before deterministic local parallelism and reducer
  contracts.
- COG/tiled production before local GeoTIFF/QGIS package acceptance and reducer
  contracts.
