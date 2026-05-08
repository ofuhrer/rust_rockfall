# Deep Repository Review

Status: evidence-based review of the current local repository state after
recent development. This is a review artifact only. It does not change simulator
behavior, validation cases, default physics, probability semantics, or roadmap
priorities by itself.

## 1. Executive Summary

Overall health: strong for a reproducible research codebase, not yet a
pilot-ready or operational hazard tool. The repository has unusually explicit
boundaries around validation, calibration, probability language, risk, swisstopo
provenance, and proprietary-model non-equivalence. The automated Rust and
Python checks pass in the current local tree.

Biggest strengths:

- Clear separation of implemented equivalent-sphere physics from unsupported
  shape, multi-contact, forest, barrier, fragmentation, and annual-frequency
  capabilities in `README.md`, `AGENTS.md`, `docs/model_design.md`, and
  `docs/hazard_map_semantics.md`.
- Good verification coverage for analytic mechanics, deterministic stochastic
  behavior, schema parsing, passive shape scaffolding, scarring diagnostics,
  probabilistic metadata, GeoTIFF parity, and hazard reducer behavior.
- Current hazard-map language is safer than earlier roadmap wording:
  `docs/hazard_map_semantics.md` and
  `docs/validation_maturity_framework.md` correctly distinguish diagnostic,
  sampling-weighted conditional, future physical-probability, future annual
  frequency, and risk products.
- Public Swiss geodata preparation is now framed as provenance and workflow
  evidence, not validation evidence.

Biggest risks:

- Several roadmap/scalability documents are stale relative to recent
  implementation. The most important drift is that
  `docs/scalability_and_data_formats_review.md` and
  `docs/repository_scientific_roadmap_review.md` still describe chunk
  manifests and hazard reducers as absent/future, while
  `scripts/build_hazard_layers.py`, `docs/hazard_layers.md`, and
  `tests/test_hazard_layers.py` already implement and test an opt-in threaded
  hazard reducer.
- The standard pre-push gate omits the Python unit-test suite even though
  central workflows now live in Python.
- Performance evidence exists, but benchmark documents have split into old
  measured reports and newer profile-reference reports with different default
  profiles. This makes it easy to cite stale timing conclusions.
- The local working tree contains many ignored raw/generated artifacts
  (`scripts/audit_local_artifacts.py` reports about 12.75 GB). They are not
  tracked, but they make review and reproducibility audits noisy.
- There is still no executed public real-site pilot from public swisstopo
  inputs to conditional per-cell intensity-exceedance products, and there is no
  support for true annual intensity-frequency curves.

Recent development improved coherence in the main safety story. In particular,
the current `README.md`, `AGENTS.md`, `docs/hazard_map_semantics.md`, and
`docs/validation_maturity_framework.md` now avoid annual-frequency overclaims.
It also weakened coherence by leaving some older roadmap and scalability
documents behind the implementation.

## 2. Review Coverage

Primary documents inspected:

- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `docs/README.md`
- `docs/repository_scientific_roadmap_review.md`
- `docs/next_development_targets.md`
- `docs/roadmap_recommendation_matrix.md`
- `docs/hazard_map_semantics.md`
- `docs/validation_plan.md`
- `docs/dataset_strategy.md`
- `docs/model_design.md`
- `docs/hazard_layers.md`
- `docs/swisstopo_data_strategy.md`
- `docs/scalability_and_data_formats_review.md`
- `docs/validation_maturity_framework.md`
- `docs/public_real_site_geodata_preparation.md`
- `docs/source_zone_block_scenario_policy_v1.md`
- `docs/real_case_intensity_frequency_implementation_roadmap.md`
- `docs/dem_terrain_sensitivity_benchmark.md`
- benchmark/performance documents listed in `docs/README.md`

Implementation and workflow areas inspected:

- `src/`
- `tests/`
- `scripts/`
- `examples/`
- `verification/`
- `validation/`
- `calibration/`
- `hazard/`
- `data/datasets.yaml`
- tracked and ignored generated-output policy via git and
  `scripts/audit_local_artifacts.py`

Checks run:

- `git status -sb`
- `git diff --stat`
- `cargo run -- --help`
- `cargo run -- verify --help`
- `cargo run -- validate --help`
- `cargo run -- run --help`
- targeted `find`, `git ls-files`, `git check-ignore`, and `rg` inspections
- `cargo fmt --check`
- `cargo clippy --all-targets --all-features -- -D warnings`
- `cargo test`
- `cargo run -- verify --all`
- `cargo run -- validate --all`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`
- `python3 scripts/check_repo_consistency.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests`
- `python3 scripts/audit_local_artifacts.py`

Checks skipped:

- No expensive performance benchmark or real-site simulation was run. The user
  asked for review rather than new large artifacts, and existing benchmark
  reports already provide enough evidence for roadmap assessment.
- No private Tschamut/swissALTI3D pilot was run because required private/local
  DEM inputs are not committed and should remain outside git.
- No web search was used; the requested review was repository-internal and the
  local literature/background inventory was sufficient for claim alignment.

Worktree state:

- After writing this review document, `git status -sb` shows only
  `docs/deep_repository_review.md` as an untracked review artifact. The review
  treats the current checked-out code and documentation as the post-development
  state.

## 3. Capability Alignment Matrix

| Capability | Documented claim | Implementation status | Test coverage | Evidence level | Gaps | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| Trajectory physics | Equivalent-sphere translational model with opt-in rotational sphere, stochastic contact, and scarring diagnostics; no operational validation. | Implemented in `src/dynamics.rs`, `src/integrator.rs`, `src/simulation.rs`, `src/stochastic.rs`, and `src/validation.rs`. | Strong Rust analytic/synthetic coverage in `tests/physics.rs`, `tests/config_io_terrain.rs`, `verification/`. | V0 strong, V1 active, V2 partial. | Real field agreement remains limited; Tschamut and Chant Sura errors remain material. | Keep defaults stable; use pilot evidence before new default decisions. |
| Shape/contact scaffolding | Passive shape metadata and internal `shape_contact_v0` scaffold only; not public runtime physics. | Large internal scaffold in `src/shape.rs`; public simulation rejects `shape_contact_v0` through `src/simulation.rs` and validation guards. | Strong internal Rust tests plus public rejection tests. | V0/internal only. | Public exports and large compiled scaffold can look more mature than it is. | Preserve gated status; document in changelog and avoid public validation cases until evidence gate passes. |
| Terrain handling | Analytic terrain, strict/clamped ESRI ASCII DEM, swissALTI3D-style metadata fixtures. | Implemented in `src/terrain.rs`, `src/geodata.rs`, validation runner. | Rust parser/metadata tests; validation cases pass. | V0-V1. | No production GIS ingestion, no tiled DEM reader, no nodata repair workflow. | Keep external geodata preparation outside core; prioritize public real-site preparation and DEM sensitivity. |
| DEM sensitivity | Dry-runnable terrain-representation fixture plus real-site scaffold. | `scripts/run_dem_terrain_sensitivity.py` and docs exist. | Python tests pass. | V1 dry-run. | Current dry run compares terrain rasters only; trajectory/hazard-layer sensitivity is future. | Promote next step to trajectory/hazard-layer map-difference fixture. |
| Source-zone/block scenarios | Phase 1 source-zone metadata and scenario tables with sampling weights; no physical/annual probabilities. | `src/probabilistic.rs`, release-zone support in validation, policy template and validators. | Rust probabilistic tests and Python policy tests pass. | V0-V1. | Source-zone derivation policy is template-level; no real pilot domain policy applied. | Execute Phase 1 public real-site geodata prep, then freeze one source/block policy. |
| Hazard-map semantics | Current products are unweighted diagnostic or sampling-weighted conditional; annual/physical/risk unsupported. | Implemented in `src/probabilistic.rs` and `scripts/build_hazard_layers.py`; docs are explicit. | Rust and Python rejection/acceptance tests pass. | V0-V1; limited V2 when tied to validation case. | Some generated metadata still uses terms like "probability" for conditional fractions, requiring context. | Keep language checks expanding as new outputs are added. |
| Probabilistic/weighted maps | Sampling-weighted conditional rasters and tidy conditional intensity-exceedance table. | Implemented in hazard builder; trajectory metadata joins supported. | Python hazard tests and Rust `probabilistic_phase1` tests pass. | V1. | No overlapping source-zone semantics, physical probability, source frequency, or annualization. | Keep future frequency design gate separate. |
| GeoTIFF/QGIS package | Lightweight GeoTIFF export with value/metadata parity; QGIS package manifest only; COG deferred. | Implemented in `scripts/build_hazard_layers.py`; docs and tests exist. | Python GeoTIFF/COG/pilot-package tests pass. | V1. | No real QGIS project/package acceptance; no COG writer; no production raster tiling. | Build tiny review package and real-pilot package before COG work. |
| Validation maturity | V0-V5 framework exists; current outputs mostly V0-V2 with no V5. | `docs/validation_maturity_framework.md` and references in README/validation docs. | Consistency checks cover some claim hygiene. | Documentation framework. | Not all older reports carry explicit maturity labels. | Add maturity labels to active report templates and benchmark summaries. |
| Tschamut/swissALTI3D pilot | Controlled no-tuning real-site pilot remains gateway workflow evidence. | Public/proxy benchmark and private prep script exist; full controlled private/local pilot not run in this tree. | Validation cases pass on proxy/synthetic fixtures. | V2 deposition diagnostics; future V3 pilot evidence. | No share-safe real-site pilot report from public/predeclared inputs. | Keep #1 immediate work package if data are available. |
| Chant Sura validation | Primary trajectory/contact evidence; held-out contact split exists. | Validation cases and processed fixture subsets exist. | `cargo run -- validate --all` passes. | V2 partial. | Contact events are proxy segment-boundary events; no active shape validation. | Keep as shape-readiness evidence, not operational validation. |
| Calibration workflows | Calibration isolated under `calibration/`; selected parameters are not defaults. | Scripts and committed summaries exist. | Consistency checks and docs enforce separation; not all calibration scripts are in pre-push. | Research calibration only. | Some older experiment reports are static HTML/CSV; easy to overread outside context. | Add maturity/claim labels to calibration summaries where absent. |
| Performance/HPC readiness | Performance and HPC readiness are core targets; local parallelism and chunking before SLURM. | Deterministic seeds/order tests, performance manifests, Parquet impact tables, and opt-in threaded hazard reducer exist. | Rust HPC tests; Python reducer parity tests; performance scripts tested by Python suite. | V0-V1 engineering evidence. | No deterministic parallel trajectory runner, no resumeable execution chunks, no real pilot budget. Some roadmap docs stale. | Update scalability/roadmap docs; make Python workflow tests part of the standard gate. |
| Local parallelism/chunking/Parquet | Parquet impact outputs and local hazard reducer are available; trajectory Parquet and parallel trajectory execution future. | Implemented for impact Parquet and hazard reducer only. | Tests pass. | V1 for hazard reducer, not trajectory execution. | Roadmaps conflate missing trajectory runner with already implemented reducer. | Split roadmap item into "parallel trajectory execution" and "hazard reducer production hardening." |
| Forest/obstacle/fragmentation scoping | Scientifically important; implementation deferred. | Dataset roles and roadmap scoping docs exist; no physics implementation. | No direct implementation tests expected. | Planning only. | Pilot-domain scoping not applied to selected real site. | Keep early scoping before interpreting a Swiss valley pilot. |

## 4. Scientific Claim Audit

Supported claims:

- The implemented trajectory kernel is an equivalent-sphere research simulator
  with opt-in rotational, stochastic-contact, and scarring diagnostics. Evidence:
  `docs/model_design.md`, `src/dynamics.rs`, `src/integrator.rs`,
  `tests/physics.rs`, `cargo test`, `cargo run -- verify --all`.
- Current hazard products are diagnostic or sampling-weighted conditional, not
  annual-frequency or risk products. Evidence:
  `docs/hazard_map_semantics.md`, `src/probabilistic.rs`,
  `tests/probabilistic_phase1.rs`, `tests/test_hazard_layers.py`.
- GeoTIFF export exists and COG is explicitly deferred. Evidence:
  `docs/hazard_layers.md`, `scripts/build_hazard_layers.py`,
  Python hazard tests.
- Public swisstopo preparation is input-provenance work, not validation.
  Evidence: `docs/swisstopo_data_strategy.md`,
  `docs/public_real_site_geodata_preparation.md`, `data/datasets.yaml`.

Partially supported claims:

- "Performance and HPC readiness are core targets." The repo has good
  deterministic seed/order tests, timing manifests, benchmark reports, Parquet
  impact outputs, and an opt-in threaded hazard reducer. It does not yet have a
  parallel trajectory runner, resume semantics, or pilot-scale budget.
- "Pilot-ready GIS outputs." Numeric GeoTIFF and package manifests exist, but
  QGIS acceptance evidence and real pilot package QA are still missing.
- "Validation evidence." The repo has V0-V2 evidence, but not V3 site-scale
  hazard-pattern evidence, V4 cross-site generalization, or V5 operational
  reproducibility.

Unsupported or future-only claims:

- Physical probability, annual intensity-frequency, return periods, operational
  hazard assessment, and risk mapping.
- Active non-spherical shape dynamics in public simulation.
- Forest, barrier, building, fragmentation, MPI/GPU/SLURM, and national
  production workflows.

Overclaimed claims found:

- No current main user-facing operational overclaim was found in `README.md`,
  `AGENTS.md`, or `docs/hazard_map_semantics.md`.
- Several roadmap/scalability documents overstate absence of local hazard
  reducer/chunk evidence, which is the inverse of a capability overclaim but
  still a roadmap error.

Ambiguous claims:

- The phrase "reach probability" is historically entrenched in layer names and
  output files. `docs/hazard_map_semantics.md` explains the conditional
  denominator, but generated metadata and user-facing summaries should keep
  nearby "fraction of supplied trajectories" wording to avoid physical
  probability interpretation.
- "Intensity-frequency" appears in roadmap file names and long-term targets.
  The current `real_case_intensity_frequency_implementation_roadmap.md`
  correctly distinguishes current conditional intensity-exceedance from future
  physical/annual frequency, but older readers may infer too much from the
  title.

## 5. Documentation Consistency Audit

High-priority inconsistencies:

1. `docs/scalability_and_data_formats_review.md` is stale.
   It is labelled as a `v0.5.x` review, says release zones are "Not
   implemented" and "chunk manifests are still future work", and says no
   reducer merge contract exists. Current evidence contradicts this:
   `docs/hazard_layers.md` documents `--reducer-workers N`, and
   `tests/test_hazard_layers.py` verifies serial/chunked parity and
   `hazard_reducer_chunk_manifest_v1`.

2. `docs/repository_scientific_roadmap_review.md` is also stale on reducer
   status. It says there is "no thread-safe streaming reducer" and "No local
   parallel runner/reducer." That should be narrowed to no parallel trajectory
   runner, no resumeable execution chunks, and no tiled/distributed reducer.

3. Performance benchmark documentation has competing baselines.
   `docs/performance_benchmark_synthetic_scale_results.md` reports a May 5,
   2026 50/100/200-release "full default matrix"; `docs/performance_benchmarking.md`
   now describes the default standard profile as a 10-release no-plot run and
   points to `docs/performance_benchmark_profile_reference.md` as canonical.
   Older results remain useful but should be explicitly labelled historical.

Medium-priority inconsistencies:

- `CHANGELOG.md` does not yet mention recent claim-hygiene and roadmap-cleanup
  work, including the validation maturity framework, public real-site geodata
  preparation contract, source-zone/block-scenario policy, duplicate-doc
  cleanup, and copy-suffix consistency checks.
- `docs/README.md` is comprehensive but too broad to function as a clear source
  of truth. It lists more than 80 documents, including active contracts,
  historical records, session logs, benchmarks, and decision notes in one
  section before a short historical section. This creates authority ambiguity
  even though the index now explicitly demotes some older docs.
- Several active documents retain version-specific status labels such as
  `v0.5.x` or `v0.6.0` while the project version is `v0.6.1`. Some are valid
  historical records; others, such as current validation or scalability
  references, should be reviewed for current/historical labelling.

Low-priority cleanup:

- Ignored `.DS_Store` and `__pycache__` files are present locally.
- `docs/agent_work_log.md` and autonomous-session logs are useful audit traces
  but should not be treated as roadmap authorities.

## 6. Test And Validation Audit

What is strong:

- `cargo test` passes with Rust coverage for core mechanics, DEM parsing,
  stochastic determinism, scarring, passive shape metadata, public
  `shape_contact_v0` rejection, probabilistic metadata, and HPC seed/order
  invariants.
- `cargo run -- verify --all` passes all analytic, synthetic, stochastic, DEM,
  and scarring cases.
- `cargo run -- validate --all` passes all current validation cases, including
  swissALTI3D-style pilot fixtures, probabilistic smoke, Chant Sura contact
  variants, held-out Chant Sura, and Tschamut proxy cases.
- `python3 -m unittest discover tests` passes 90 tests, including hazard-layer
  semantics, GeoTIFF/COG behavior, chunked reducer parity, DEM sensitivity,
  performance benchmark scaffolding, local-artifact audit, public real-site
  geodata manifest validation, source-scenario policy validation, and
  repository claim hygiene.

Main gap:

- The standard `scripts/git-hooks/pre-push` chain runs Rust checks,
  verification, validation, and `scripts/check_repo_consistency.py`, but not
  the Python unit-test suite. This is now a central gap because many important
  repo workflows are implemented in Python.

Specific weak spots:

- Parser/schema behavior is good for current cases, but policy templates and
  source-zone derivation remain mostly documentation plus validators, not a
  real pilot application.
- Hazard semantics tests are strong for current Phase 1 modes, but future
  overlapping source zones, physical probabilities, and annual frequencies are
  intentionally absent.
- GIS output tests cover numeric and metadata parity, not QGIS project/package
  usability or visual alignment.
- DEM sensitivity tests cover terrain-raster perturbation metrics; they do not
  yet compare trajectory or hazard-layer changes.
- Performance checks are measurement scripts and reports, not regression
  budgets. That is appropriate, but docs should avoid implying performance
  readiness beyond measured scopes.

## 7. Examples And Case Audit

Examples:

- `examples/inclined_plane.json` is aligned with `cargo run -- run --config
  examples/inclined_plane.json --output trajectory.csv`.
- CLI help confirms implemented subcommands: `run`, `verify`, `validate`, and
  `benchmark`. Documented `cargo run -- verify --all`, `cargo run -- validate
  --all`, and case-specific commands match the CLI.

Verification and validation cases:

- Current checked-in cases are runnable and pass.
- Optional/private Tschamut/swissALTI3D templates are correctly outside
  `cargo run -- validate --all`.
- Chant Sura contact cases are scientifically labelled as proxy contact-event
  comparisons, not exact impact validation.
- Tschamut cases remain deposition/runout diagnostics on proxy terrain, not
  calibrated field validation.

Generated and local artifacts:

- Git tracking is clean for generated outputs and raw data: only `.gitkeep`
  files are tracked in `verification/results/`, `validation/results/`,
  `hazard/results/`, and `calibration/results/`; only `data/raw/.gitkeep` is
  tracked under `data/raw`.
- Local ignored artifacts are large: `scripts/audit_local_artifacts.py` reports
  about 12.75 GB, mostly under `validation/results/`, plus ignored raw public
  data and hazard outputs. This is acceptable for local experiments but risky
  for review noise and disk hygiene.

## 8. Roadmap Reassessment

Move up:

- Update stale roadmap/scalability documents before more roadmap prose is
  added. The repo already has a hazard reducer prototype; the next engineering
  item is not "add reducer" but "separate missing parallel trajectory execution
  and resumeable chunk orchestration from implemented hazard-reducer parity."
- Add Python unit tests to the standard local/pre-push gate or create a
  documented `quick`/`full` distinction that still runs the central hazard and
  geodata Python tests before pushes.
- Extend DEM sensitivity into trajectory/hazard-layer comparison, because the
  dry-run terrain-only fixture now exists and is the most important
  pilot-confounder test before calibration.

Keep high:

- Public or controlled real-site Tschamut/swissALTI3D pilot remains the best
  immediate evidence package, but it should be described as V3-oriented pilot
  evidence only if inputs, source policy, DEM sensitivity, GIS QA, and
  no-tuning gates are predeclared.
- Source-zone/block-scenario semantics remain early because conditional map
  denominators depend on them.
- GIS/QGIS package fixture remains important, with GeoTIFF correctness before
  COG optimization.

Move down or pause:

- More shape-contact runtime wiring should remain paused until shape-readiness
  evidence and decision gates are stronger. The scaffold is already large.
- More generic performance optimization should remain coupled to pilot-scale
  workloads. Measured bottlenecks shift between simulation, impact output,
  hazard accumulation, plotting, and file count.
- Annual intensity-frequency implementation should remain gated behind
  physical/source-frequency semantics and validation maturity.

Remove or archive:

- Do not delete historical documents automatically, but move older roadmap
  authorities into a clearer archive section. In particular, v0.5/v0.6.0
  current-state documents should not compete with
  `docs/next_development_targets.md`,
  `docs/roadmap_recommendation_matrix.md`, and
  `docs/real_case_intensity_frequency_implementation_roadmap.md`.

## 9. Prioritized Findings

### High

1. **Roadmap/scalability docs are stale on local reducer capability.**

   Evidence: `docs/scalability_and_data_formats_review.md` says release zones
   are not implemented, chunk manifests are future work, and no reducer merge
   contract exists. `docs/repository_scientific_roadmap_review.md` says there
   is no thread-safe streaming reducer. Current code and docs show otherwise:
   `docs/hazard_layers.md` documents `--reducer-workers N`, and
   `tests/test_hazard_layers.py` verifies serial/chunked parity and chunk
   manifests.

   Action: update the scalability and roadmap reviews to distinguish the
   implemented hazard-layer local threaded reducer from the missing parallel
   trajectory runner, resumeable chunks, tiled reducer, and SLURM orchestration.

2. **Python workflow tests are not part of the standard pre-push gate.**

   Evidence: `scripts/git-hooks/pre-push` runs Rust checks, `verify`,
   `validate`, and `scripts/check_repo_consistency.py`, but omits
   `python -m unittest discover tests`. Those Python tests cover the hazard
   builder, GeoTIFF/COG behavior, DEM sensitivity, performance benchmark
   scaffolding, geodata manifests, source-scenario policy, and artifact audits.

   Action: add a Python unit-test step to pre-push or define a documented full
   gate that must be used before roadmap/product changes.

3. **Performance documentation has competing "current" baselines.**

   Evidence: `docs/performance_benchmark_synthetic_scale_results.md` presents a
   50/100/200-release default matrix from May 5, 2026 and recommends plotting
   changes; `docs/performance_benchmarking.md` now says the standard profile is
   a short 10-release no-plot run and points to
   `docs/performance_benchmark_profile_reference.md` as canonical.

   Action: label older benchmark result docs as historical and route current
   engineering decisions through the latest profile-reference and pilot-coupled
   benchmark docs.

4. **The repository is still not ready for a full public real-case
   intensity-frequency map.**

   Evidence: `docs/real_case_intensity_frequency_implementation_roadmap.md`
   correctly says current products are close to conditional
   intensity-exceedance, not physical or annual intensity-frequency. Missing
   pieces include public real-site geodata preparation, source-zone policy
   application, block-scenario population/frequency semantics, local scaling
   budget, QGIS acceptance, and validation maturity evidence.

   Action: keep the immediate milestone as a conditional public real-site pilot
   and explicitly defer annual frequency.

### Medium

5. **`CHANGELOG.md` omits recent documentation and claim-hygiene changes.**

   Evidence: recent local changes add validation maturity references, public
   real-site/source-policy docs, duplicate-doc cleanup, and consistency checks,
   but `CHANGELOG.md` Unreleased currently stops at benchmark-profile and
   Parquet/scaffold entries.

   Action: add concise Unreleased entries before committing this work.

6. **Documentation authority is diffuse.**

   Evidence: `docs/README.md` lists a very large set of active, historical,
   benchmark, autonomous-session, and decision documents. It does demote some
   older records, but many older roadmaps remain in the main core list.

   Action: split the index into "current contracts", "current roadmap",
   "current evidence reports", and "historical/superseded" groups.

7. **Local ignored artifacts are very large and can distort review.**

   Evidence: `scripts/audit_local_artifacts.py` reports 106,337 files and about
   12.26 GB under `validation/results/`, plus raw public data and hazard
   outputs. Git ignore/tracking checks are clean, so this is local hygiene, not
   a repository leak.

   Action: add a documented cleanup recipe or expected local-artifact policy
   after large benchmark runs.

8. **Validation maturity labels are not consistently applied to older reports.**

   Evidence: `docs/validation_maturity_framework.md` exists and is referenced
   by current docs, but older benchmark, calibration, and validation reports do
   not all carry V0-V5 labels.

   Action: add maturity labels to active report templates first; update older
   reports only when touched.

9. **DEM sensitivity is still terrain-only at the checked-in dry-run level.**

   Evidence: `docs/dem_terrain_sensitivity_benchmark.md` documents terrain
   variant metrics and future trajectory/hazard-layer comparisons. The Python
   tests exercise the dry-run fixture, not real-site hazard sensitivity.

   Action: implement the next dry-runnable trajectory/hazard-layer sensitivity
   fixture before calibration.

### Low

10. **Local `.DS_Store` and `__pycache__` clutter is present.**

    Evidence: `find` output shows ignored `.DS_Store` and Python cache files in
    several directories. They are not tracked.

    Action: optionally extend `scripts/audit_local_artifacts.py` with a cleanup
    mode or document safe removal commands.

## 10. Recommended Next Development Tasks

1. **Reconcile scalability and roadmap documentation with current reducer
   implementation.**

   Objective: remove stale "no reducer/chunk manifest" claims while preserving
   missing trajectory-runner and resume gaps.

   Files likely affected: `docs/scalability_and_data_formats_review.md`,
   `docs/repository_scientific_roadmap_review.md`,
   `docs/roadmap_recommendation_matrix.md`,
   `docs/next_development_targets.md`.

   Definition of done: docs distinguish implemented local hazard reducer from
   missing parallel trajectory execution, tiled reducer, resume, and SLURM.

   Suggested checks: `python3 scripts/check_repo_consistency.py`,
   targeted `rg` for stale phrases.

2. **Add Python workflow tests to the standard gate.**

   Objective: make central Python workflow regressions visible before pushes.

   Files likely affected: `scripts/git-hooks/pre-push`,
   `docs/onboarding.md`, `AGENTS.md`.

   Definition of done: pre-push or a documented full gate runs
   `python -m unittest discover tests` through the selected repo Python.

   Suggested checks: `scripts/git-hooks/pre-push`.

3. **Update changelog and docs index authority.**

   Objective: make recent claim-hygiene/source-policy/document cleanup changes
   discoverable and reduce competing roadmap authorities.

   Files likely affected: `CHANGELOG.md`, `docs/README.md`.

   Definition of done: Unreleased entries cover recent work; docs index has
   clearer current versus historical sections.

   Suggested checks: `python3 scripts/check_repo_consistency.py`.

4. **Extend DEM sensitivity to trajectory/hazard-layer fixture.**

   Objective: compare reach, deposition, energy, jump, and exceedance layers
   across fixed terrain variants before calibration.

   Files likely affected: `scripts/run_dem_terrain_sensitivity.py`,
   `tests/test_dem_terrain_sensitivity.py`,
   `docs/dem_terrain_sensitivity_benchmark.md`,
   tiny fixtures under `verification/` or `tests/fixtures/`.

   Definition of done: CI-safe fixture generates deterministic map-difference
   metrics and report without private data.

   Suggested checks: Python unit tests plus `cargo run -- validate --all` if
   cases are added.

5. **Create a public real-site geodata preparation dry run.**

   Objective: move from template manifest to one selected public domain
   preparation workflow without committing raw swisstopo products.

   Files likely affected:
   `docs/public_real_site_geodata_preparation.md`,
   `data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml`,
   `scripts/validate_public_real_site_geodata_manifest.py`, future ignored
   local pilot dirs.

   Definition of done: manifest validator passes for a filled local manifest;
   share-safe report records tile inventory, CRS/datum, checksums, and no-run
   claim boundaries.

   Suggested checks: Python manifest tests and artifact audit.

6. **Apply source-zone/block-scenario policy to the selected pilot domain.**

   Objective: freeze conditional scenario inputs before simulation.

   Files likely affected:
   `validation/templates/public_real_site_source_scenario_policy_v1.yaml`,
   `scripts/validate_source_scenario_policy.py`,
   pilot docs and ignored local policies.

   Definition of done: local policy validates, stable source/release/block ids
   join through trajectory metadata and hazard package manifests.

   Suggested checks: policy unit tests and a tiny synthetic join fixture.

7. **Build a tiny QGIS package acceptance fixture.**

   Objective: prove that the existing GeoTIFF/package manifest is actually
   reviewable, not only file-level correct.

   Files likely affected: `scripts/build_hazard_layers.py`,
   `tests/test_hazard_layers.py`, `docs/pilot_gis_package.md`,
   `docs/hazard_layers.md`.

   Definition of done: tiny package includes GeoTIFFs, parity files, source
   sidecars, manifests, QA notes, and explicit non-COG/non-operational labels.

   Suggested checks: Python hazard tests; optional manual QGIS/raster-library
   smoke note.

8. **Define a pilot-coupled performance gate.**

   Objective: replace generic optimization discussion with a measurable
   pass/no-go report for real pilot workload size, output volume, file count,
   and reducer timings.

   Files likely affected: `docs/performance_benchmarking.md`,
   `docs/performance_benchmark_profile_reference.md`,
   `scripts/run_performance_benchmark.py`, pilot docs.

   Definition of done: benchmark report template records trajectory count,
   impact events, file count, bytes, timings, worker count, and whether the
   limiting path is simulation, output, hazard accumulation, plotting, or
   metadata.

   Suggested checks: smoke benchmark profile only; no large scale run in CI.

9. **Add validation maturity labels to active reports.**

   Objective: make overclaim boundaries visible where readers consume results.

   Files likely affected: active validation/benchmark report docs and report
   templates in scripts.

   Definition of done: reports state V0-V5 level, product semantics, and
   unsupported claims.

   Suggested checks: claim-hygiene consistency check.

## 11. Final Judgment

The repository is best described as a **reproducible research workbench with
early pilot workflow scaffolding**.

It is more mature than an experimental simulator because it has deterministic
mechanics, strong verification, public validation fixtures, calibration
separation, provenance manifests, probabilistic metadata checks, hazard-layer
post-processing, GeoTIFF export, benchmark instrumentation, and CI-safe Python
workflow tests.

It is not yet a pilot-ready research workflow for the full target because the
public real-site geodata package, applied source-zone/block policy,
trajectory/hazard DEM sensitivity, real pilot GIS QA, pilot-coupled performance
budget, and end-to-end share-safe public pilot report are still missing.

It is not an operationally validated hazard tool. Current products are
diagnostic or sampling-weighted conditional hazard indicators, not physical or
annual intensity-frequency maps, return-period maps, risk maps, or official
hazard assessments.
