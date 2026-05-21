# OpenNHM Learnings For `rust_rockfall`

Date regenerated: 2026-05-21  
Authoring context: local repository inspection plus refreshed OpenNHM/AvaFrame/DebrisFrame public documentation and source review.

## Summary

OpenNHM is relevant to `rust_rockfall`, but the strongest lessons are workflow and product-delivery lessons rather than direct physics-transfer lessons. AvaFrame is a mature Python natural-hazard framework with documented computational modules, statistical analysis, regional splitting, plotting/reporting, test data, and a QGIS Processing connector. DebrisFrame is younger, but it follows the same pattern: domain-specific hazard tooling built on shared natural-hazard workflow infrastructure.

The main takeaway for this repository is that the rockfall physics core can remain Rust-first and independent, while the user-facing layer should become more like OpenNHM: GIS-native, module-oriented, documented by user tasks, and explicit about input/output contracts.

Recommended direction:

1. Keep the strict `rust_rockfall` claim boundaries around diagnostic, conditional, non-operational products.
2. Add a stable user manual layer above the current dense evidence/task documentation.
3. Promote the AOI-to-map path into one named workflow contract.
4. Prototype QGIS styles first, then a QGIS Processing connector.
5. Treat regional splitting, scenario execution, and raster aggregation as first-class workflow modules.
6. Adopt a clearer config-precedence model inspired by AvaFrame, but keep typed YAML/JSON schemas instead of moving to `.ini`.
7. Do not copy AvaFrame rock-avalanche physics assumptions without independent validation.

## What I Inspected

Local `rust_rockfall` files and surfaces:

- `README.md`
- `Cargo.toml`
- `AGENTS.md`
- `src/main.rs`
- `src/*.rs`
- `docs/project_overview.md`
- `docs/hazard_layers.md`
- `docs/hazard_map_semantics.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/run_aoi_hazard_workflow.py`
- selected validation, verification, hazard, and workflow inventories

External sources:

- OpenNHM homepage and code/documentation pages
- AvaFrame current documentation
- AvaFrame QGIS connector documentation
- AvaFrame probability/statistics documentation
- AvaFrame regional modelling documentation
- AvaFrame rock-avalanche documentation
- DebrisFrame documentation and repository
- OpenNHM QGIS connector repository
- current OpenNHM news around AvaFrame 2.0 and QGIS connector migration

I also inspected shallow clones of the relevant GitHub repositories under `/tmp/opennhm_inspect/`:

- `OpenNHM/AvaFrame`
- `OpenNHM/DebrisFrame`
- `OpenNHM/OpenNHMQGisConnector`

I did not run AvaFrame, DebrisFrame, QGIS, or local `rust_rockfall` simulations for this report.

## Local Repository Baseline

`rust_rockfall` is currently an independent Rust implementation for rockfall trajectory simulation and hazard-map generation from public Swiss geodata. The Rust binary exposes `run`, `verify`, `validate`, and `benchmark` commands. The Python layer handles AOI workflow planning, public geodata preparation, hazard-layer construction, GIS package generation, reporting, SLURM/Balfrin evidence handling, and repository consistency checks.

Current strengths:

- The physical and operational claim boundaries are unusually clear. Current products are diagnostic or sampling-weighted conditional layers, not annualized probabilities, not risk maps, and not operational hazard products.
- The Rust core is compact and readable: terrain, geometry, dynamics, integration, state, simulation, IO, validation, stochastic/probabilistic metadata, manifest, and geodata helpers.
- Verification and validation are separated from calibration and future operational claims.
- The hazard-layer builder already produces GIS-relevant artifacts: CSV grids, ESRI ASCII grids, optional GeoTIFFs, GeoJSON deposition points, manifests, metadata, and diagnostic reports.
- `scripts/run_aoi_hazard_workflow.py` is a useful front door because it reports status, blockers, next commands, expected paths, and claim boundaries in one place.

Current friction:

- The user-facing path is still scattered across many scripts and documentation pages.
- The repository has a strong evidence system, but a new user has to infer the product workflow from many gates and reports.
- QGIS/GIS support is export-oriented rather than interactive.
- Regional-scale work is documented through probes, Balfrin packages, and scale gates, but not yet presented as one clean module/workflow.
- The report and task-history corpus is useful for auditability, but it is not a substitute for a stable user manual.

## OpenNHM/AvaFrame Patterns Worth Learning From

### 1. QGIS As A Primary User Interface

OpenNHM's current QGIS connector exposes AvaFrame workflows through QGIS Processing. The documented connector includes operational and experimental tools for dense-flow runs, alpha-beta calculations, probability analysis, regional input splitting, regional modelling computation, snow slide, rock avalanche, scarp calculation, default-config extraction, peak-file loading, version checks, and updates.

Important details:

- The connector accepts GIS-native inputs such as DEM layers and release vector layers.
- It copies inputs into the expected project structure.
- It invokes the Python computational/workflow package.
- It loads output rasters back into QGIS.
- It applies styles where available.
- It keeps advanced configuration available, but not mandatory for standard users.

`rust_rockfall` already has the harder backend pieces for GIS review. The missing layer is a GIS-native interface that makes existing outputs usable without asking the user to manually run several Python commands and then load rasters by hand.

Recommended local implication:

- Build QGIS styles for current hazard layers before building a full connector.
- Then prototype a QGIS Processing plugin that calls `scripts/run_aoi_hazard_workflow.py` and loads generated map-package outputs.
- Keep claim boundaries in the algorithm help text, output manifest, layer names, and report header.

### 2. Module Families Make A Large Framework Navigable

AvaFrame groups capabilities into memorable module families:

- `com*`: computational models
- `in*`: input and transformation utilities
- `ana*`: analysis/statistics/test utilities
- `out*`: output and plotting
- `log*`: reporting
- `runScripts`: executable workflows

`rust_rockfall` should not copy those names directly, but it should copy the idea. The current repo is easy for an agent to search, but harder for a domain user to navigate.

Recommended local module/workflow families:

- `simulate`: Rust core runs and trajectory output
- `inputs`: DEM, CRS, public geodata, AOI manifests
- `sources`: release zones, block scenarios, sampling weights
- `validate`: verification, validation, holdout, calibration separation
- `hazard`: reducer, layers, semantics, map packages
- `regional`: split, execute, merge, summarize
- `review`: visualization, QGIS, QA reports

This can start as documentation and CLI grouping. It does not require a major Rust refactor.

### 3. Configuration Precedence Is Explicit

AvaFrame's config utilities support default module config, local overrides, expert config files inside an avalanche directory, direct override files, and batch config directories. That pattern matters more than the `.ini` format.

`rust_rockfall` currently uses JSON, YAML, CLI arguments, source-zone policies, AOI manifests, run-freeze records, and generated manifests. The pieces are good, but the precedence rules are not presented as one simple user-facing model.

Recommended local config precedence:

1. built-in model defaults;
2. repository templates;
3. AOI/site manifest;
4. source-zone and block-scenario policy;
5. validation or hazard case file;
6. run-freeze/authorization record;
7. explicit CLI override;
8. generated output manifest.

Keep typed YAML/JSON and validators. Do not move toward untyped `.ini` files.

### 4. Probability Maps Are Simple To Explain

AvaFrame's probability analysis computes, per raster cell, the fraction of simulations where a selected peak variable exceeds a threshold. The QGIS connector exposes both probability runs and probability analysis over existing result directories.

`rust_rockfall` already has a more rigorous semantics model:

- `unweighted_diagnostic`
- `sampling_weighted_conditional`
- explicit unsupported boundaries for physical probability and annual frequency
- explicit hazard-versus-risk separation

This is a strength. The OpenNHM lesson is presentation, not semantics. Users understand "fraction of simulations exceeding a threshold" quickly. `rust_rockfall` should present conditional layers that simply, while preserving denominators and claim metadata.

Recommended local wording:

- "diagnostic fraction of supplied trajectories"
- "sampling-weighted conditional fraction over documented scenario filters"
- "not annualized"
- "not physical probability"
- "not risk"
- "not operational"

Those phrases should appear in QGIS labels, report headers, manifests, and legends.

### 5. Regional Splitting Is A Named Workflow

AvaFrame's `com7Regional` is a useful reference even though it is documented as experimental. It splits a larger setup into multiple avalanche directories, based on release-feature grouping and scenarios, then supports concurrent execution and merged raster outputs.

This is close to the future `rust_rockfall` AOI/regional path. The current repo already contains many ingredients: source-zone policies, scenario tables, prepared pilots, output-budget gates, reducer manifests, and Balfrin evidence packages. What is missing is one concise public contract for "regional rockfall computation".

Recommended local contract:

- one AOI manifest;
- one public geodata/cache contract;
- one source-zone layer with `group`, `zone_id`, `scenario_id`, and optional `sampling_weight`;
- one terrain-crop/output-grid contract;
- one execution-plan table;
- one reducer/aggregation contract;
- one map package and QA review output.

### 6. Separate Data Repositories Scale Better

OpenNHM has separate repositories for code and data. `rust_rockfall` currently keeps small fixtures in the repo and ignores raw public data locally. That is fine now. If public benchmark packages, terrain crops, observed overlays, and demonstration cases grow, a separate benchmark/data repository would reduce code-repo weight while improving reproducibility.

Recommended trigger for a future split:

- public data fixtures become too large for normal code review;
- multiple benchmark sites need stable versioning;
- QGIS examples need downloadable packages;
- CI needs fixed external test packs.

## OpenNHM Patterns To Avoid Or Treat Carefully

### Do Not Transfer Dense-Flow Physics To Rockfall By Default

AvaFrame and DebrisFrame mostly target avalanche and debris-flow processes. Rockfall trajectory simulation has different state variables, contact mechanics, block-shape concerns, forest/fragmentation interactions, and validation needs. Shared infrastructure is valuable; physics defaults and calibration assumptions are not directly transferable.

### Treat AvaFrame Rock-Avalanche Support As Workflow Reference Only

AvaFrame has a `com6RockAvalanche` module, but the documentation frames it as experimental and not fully tested. It may still offer useful ideas for release-thickness rasters, scarp workflows, and QGIS exposure, but it should not be used as a scientific validation target for this repository.

### Do Not Let UI Simplicity Weaken Claim Boundaries

OpenNHM's probability-map phrasing is accessible, but `rust_rockfall` needs to keep its stricter distinctions between diagnostic fractions, conditional sampling weights, physical probability, annual frequency, and risk. The UI should be simpler; the metadata should remain strict.

## Recommended Backlog Items

### Near-Term Documentation

1. Add `docs/user_manual/README.md` with a stable navigation layer:
   - overview;
   - installation;
   - first simulation;
   - AOI quickstart;
   - inputs/geodata;
   - source zones/scenarios;
   - hazard layers;
   - map review;
   - limitations.

2. Add `docs/aoi_conditional_workflow_contract.md` with the canonical phase model:
   - prepare inputs;
   - derive release candidates;
   - generate scenarios;
   - run ensemble;
   - reduce hazard layers;
   - package map;
   - review.

3. Add `docs/config_precedence.md` describing the typed YAML/JSON precedence model.

### Near-Term GIS

4. Add a small `qgis/styles/` or `gis/styles/` bundle for current output layers:
   - reach probability;
   - deposition density;
   - maximum kinetic energy;
   - maximum jump height;
   - intensity-exceedance layers;
   - observed overlays.

5. Add `docs/qgis_connector_design.md` describing a first QGIS Processing connector:
   - input parameters;
   - command invocation;
   - output discovery;
   - styling;
   - failure handling;
   - non-operational wording.

### Medium-Term Workflow

6. Add `scripts/run_aoi_hazard_workflow.py schema` or `describe-config` mode.

7. Add a regional splitting contract with stable fields:
   - `group`;
   - `zone_id`;
   - `scenario_id`;
   - `sampling_weight`;
   - expected DEM crop;
   - expected output grid;
   - reducer merge method.

8. Add one small fixture-backed "regional split and merge" example that does not depend on Balfrin.

### Later

9. Prototype the QGIS Processing connector after the style bundle and workflow contract stabilize.

10. Evaluate a separate public benchmark/data repository once fixtures become too large or numerous for the main repo.

## Decision Matrix

| Learning | Benefit | Risk | Recommended Action |
| --- | --- | --- | --- |
| QGIS Processing front door | Major usability gain for domain users | Plugin maintenance and environment friction | Start with styles and a design doc, then prototype. |
| OpenNHM-style module families | Easier onboarding and documentation | Could create duplicate vocabulary | Use as user-manual grouping, not a Rust refactor. |
| Config precedence model | Fewer ambiguous overrides | More schema/documentation work | Document precedence and add a CLI schema/describe mode. |
| Probability-map presentation | Makes outputs understandable | Could imply physical probability | Pair simple labels with strict manifests and legends. |
| Regional splitting contract | Clarifies Swiss/AOI scale path | Could overpromise scale readiness | Keep evidence labels and claim boundaries. |
| Separate data repo | Cleaner code repo later | More release/version management | Defer until benchmark data volume justifies it. |
| AvaFrame rock-avalanche module | Some workflow ideas | Physics mismatch and experimental status | Use only as workflow reference. |

## Sources

- [OpenNHM homepage](https://opennhm.org/)
- [OpenNHM code page](https://opennhm.org/code/)
- [OpenNHM documentation page](https://opennhm.org/documentation/)
- [OpenNHM GitHub organization](https://github.com/OpenNHM)
- [AvaFrame documentation](https://docs.avaframe.org/en/latest/)
- [OpenNHM QGIS connector documentation](https://docs.avaframe.org/en/latest/connector.html)
- [AvaFrame probability/statistics documentation](https://docs.avaframe.org/en/latest/moduleAna4Stats.html)
- [AvaFrame regional modelling documentation](https://docs.avaframe.org/en/latest/moduleCom7Regional.html)
- [AvaFrame rock-avalanche documentation](https://docs.avaframe.org/en/latest/moduleCom6RockAvalanche.html)
- [OpenNHM/AvaFrame](https://github.com/OpenNHM/AvaFrame)
- [OpenNHM/DebrisFrame](https://github.com/OpenNHM/DebrisFrame)
- [OpenNHM/OpenNHMQGisConnector](https://github.com/OpenNHM/OpenNHMQGisConnector)
- [AvaFrame 2.0 Zenodo record](https://zenodo.org/records/20025261)

## Final Assessment

The most useful OpenNHM lesson is product architecture: a scientific core becomes much more usable when wrapped in clear workflow modules, stable configuration precedence, GIS-native execution, styled outputs, and task-oriented documentation. `rust_rockfall` already has stronger claim-boundary discipline than many modelling tools. The next step is to make that rigor easier to use, not to dilute it.
