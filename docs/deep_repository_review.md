# Deep Repository Review

Status: evidence-based repository review of the current local tree after the
latest pull to `63851b9` (`Validate Tschamut pilot GIS package`). This is a
review artifact only. It does not change simulator behavior, default physics,
validation cases, calibration parameters, probability semantics, or roadmap
priorities by itself.

## 1. Executive Summary

Overall health: the repository tells a mostly coherent and scientifically
cautious story. It is a reproducible research workbench with increasingly
credible pilot-workflow scaffolding, not an operational hazard tool and not yet
a completed public real-site pilot workflow.

Recent development improved coherence in several important places:

- `src/terrain.rs` now rejects panic-prone DEM headers and invalid numeric
  values before runtime terrain queries.
- Runtime-facing config parsing now rejects unknown fields through
  `#[serde(deny_unknown_fields)]` in the core config types inspected in
  `src/simulation.rs`, `src/geometry.rs`, and `src/stochastic.rs`.
- `scripts/build_hazard_layers.py` now rejects multi-trajectory CSV samples in
  trajectory-sample paths and avoids in-place double normalization in hazard
  layer extraction.
- `tests/test_hazard_layers.py`, `tests/config_io_terrain.rs`, and
  `tests/test_pilot_gis_package_validator.py` cover recently fixed workflow
  risks.
- The standard repository consistency check and the Rust/Python test suites
  pass in the current local tree.

The biggest strengths are still the explicit separation between verification,
validation, calibration, pilot evidence, conditional hazard maps, future annual
frequency, and risk. `AGENTS.md`, `README.md`,
`docs/hazard_map_semantics.md`, `docs/validation_plan.md`, and
`docs/validation_maturity_framework.md` are broadly aligned on these
boundaries.

The biggest remaining risks are not hidden physics changes; they are evidence
and workflow interpretation risks:

- The tracked roadmap now claims the Tschamut pilot GIS/QGIS package is
  complete at an automated diagnostic-review level, but the current checkout
  does not contain the referenced ignored package manifest under
  `hazard/results/tschamut_public_pilot/gate_v1/`. At the same time,
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` and
  `docs/tschamut_public_conditional_pilot_gate_report.md` state the pilot
  remains a no-go gate with no generated GIS artifacts. This is the most
  important current story drift.
- `cargo run -- validate --all` reports all validation cases as passed, but the
  default human-readable output can hide that several passing cases remain
  diagnostic or weak-evidence cases with large errors. The repo documents this
  distinction elsewhere, but the CLI summary can still invite over-reading.
- The pilot GIS package validator proves manifest/file consistency, not real
  GeoTIFF readability or QGIS usability. Its unit tests use placeholder bytes
  for a "GeoTIFF" fixture, so the validator should not be treated as raster QA.
- Local ignored artifacts are very large: `scripts/audit_local_artifacts.py
  --json` reported about 12.75 GB, mostly under `validation/results/`. Git
  tracking is clean, but local caches can distort review and reproducibility
  discussions.
- Performance/HPC readiness is real at the contract and smoke-test level, but
  still lacks a deterministic parallel trajectory runner, resumeable execution
  chunks, tiled reducers, and a measured public pilot budget.

Recent development therefore improved code/workflow reliability but made one
documentation-evidence boundary sharper: "validated local package reviewed on
one machine" is not the same thing as "reproducible tracked pilot package
available from the repository."

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
- `docs/real_case_intensity_frequency_implementation_roadmap.md`
- `docs/pilot_gis_package.md`
- `docs/tschamut_public_pilot_gis_package_review.md`
- `docs/tschamut_public_conditional_pilot_gate_report.md`
- `docs/agent_work_log.md`

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
- `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
- benchmark and report outputs small enough to inspect from tracked metadata
  and documented summaries

Checks run:

- `git pull`
- `git status -sb`
- `git log --oneline -5`
- targeted `rg` searches for stale roadmap terms and for `operational`,
  `validated`, `risk`, `annual`, `probability`, `COG`, `GeoTIFF`, `RAMMS`,
  `default`, and `calibrated`
- `rg` searches for `TODO`, `FIXME`, `HACK`, `unwrap`, `expect`, `panic`,
  `default`, `fallback`, `seed`, `random`, `probability`, and related
  correctness terms during code inspection
- `cargo run -- --help`
- `cargo run -- run --help`
- `cargo run -- verify --help`
- `cargo run -- validate --help`
- `cargo run -- benchmark --help`
- `git ls-files 'hazard/results/*' 'validation/results/*'
  'verification/results/*' 'data/raw/*' 'validation/private/*'
  'data/private/*' 'target/*'`
- `python3 scripts/validate_public_real_site_geodata_manifest.py
  data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
- `python3 scripts/validate_source_scenario_policy.py
  validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `python3 scripts/validate_public_real_site_conditional_pilot_run.py
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml
  --print-command-plan`
- a targeted shell check for the referenced Tschamut pilot GIS package manifest
  under `hazard/results/tschamut_public_pilot/gate_v1/`
- `python3 scripts/audit_local_artifacts.py --json`
- `cargo fmt --check`
- `cargo clippy --all-targets --all-features -- -D warnings`
- `cargo test`
- `cargo run -- verify --all`
- `cargo run -- validate --all`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/check_repo_consistency.py`
- `python3 -m unittest tests.test_pilot_gis_package_validator`
- `python3 scripts/audit_case_schema.py`

Observed check results:

- `cargo fmt --check`: passed.
- `cargo clippy --all-targets --all-features -- -D warnings`: passed.
- `cargo test`: passed all Rust tests observed during review: 57 library
  tests, 2 binary tests, 64 config/IO/terrain tests, 6 HPC-readiness tests, 34
  physics tests, 10 probabilistic Phase 1 tests, and doc-tests.
- `cargo run -- verify --all`: passed all verification cases.
- `cargo run -- validate --all`: passed all validation cases.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: passed 119 tests
  with 2 skipped.
- `python3 scripts/check_repo_consistency.py`: passed.
- `python3 scripts/audit_case_schema.py`: passed for 55 YAML files.
- `python3 scripts/audit_local_artifacts.py --json`: passed and reported
  about 12.75 GB of ignored local artifacts.

Checks skipped:

- `python3 -m pytest` was attempted as an exploratory check and failed because
  `pytest` is not installed in the current environment. The repository's
  Python suite was run through `unittest` instead.
- No expensive performance benchmark or large real-site simulation was run.
  The task is a review task, and the repository explicitly says not to create
  large artifacts for documentation review.
- No private or raw swisstopo data workflow was run. The current public
  Tschamut manifest intentionally points to local/ignored data paths, and raw
  geodata should not be committed.
- No manual QGIS inspection was run from this review.

## 3. Capability Alignment Matrix

| Capability | Documented claim | Implementation status | Test coverage | Evidence level | Gaps | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| Trajectory physics | Equivalent-sphere translational model with opt-in rotational sphere, stochastic contact, and scarring diagnostics; no operational validation. | Implemented in `src/dynamics.rs`, `src/integrator.rs`, `src/simulation.rs`, `src/stochastic.rs`, and `src/validation.rs`. | Strong Rust analytic/synthetic coverage in `tests/physics.rs`, `tests/config_io_terrain.rs`, and `verification/`. | Strong V0, active V1, partial V2. | Real field agreement remains limited; no shape, forest, fragmentation, or barrier physics. | Keep defaults stable; use pilot and validation evidence before changing numerical behavior. |
| Unsupported physics boundaries | Shape dynamics, multi-contact, forest, barriers, fragmentation, operational risk, and annual frequency are future/unsupported. | Boundaries are explicit in `README.md`, `AGENTS.md`, `docs/model_design.md`, and `docs/hazard_map_semantics.md`. | Consistency and parser tests support several boundaries. | Documentation plus some enforcement. | Boundary language can be weakened by future roadmap titles if not repeated near outputs. | Keep unsupported labels in generated manifests, reports, and package validators. |
| Shape/contact scaffolding | Passive shape metadata and internal `shape_contact_v0` scaffold exist; public runtime is gated. | `src/shape.rs` and related tests exist; public config rejects runtime `shape_contact_v0`. | Rust tests cover internal behavior and public rejection. | V0/internal only. | Large scaffold may look more mature than evidence supports. | Keep active shape-contact deferred until shape-readiness validation gate is stronger. |
| Terrain handling | Analytic terrain and ESRI ASCII DEMs are supported; swisstopo workflows are provenance/input workflows. | `src/terrain.rs` parses and samples DEMs; parser now rejects invalid headers/values. | Rust parser tests and validation cases pass. | V0-V1. | No tiled DEM reader, no production nodata repair workflow, no full raster stack ingestion. | Prioritize DEM sensitivity and public real-site preparation before calibration. |
| DEM sensitivity | Dedicated terrain-representation sensitivity is a major future work package. | Dry-runnable tooling and no-go gate exist; selected Tschamut gate blocks on missing local DEM. | Python tests and gate validators pass. | V1 dry-run/workflow. | No real trajectory/hazard-layer sensitivity results yet. | Extend to deterministic trajectory/hazard map-difference fixture. |
| Source-zone/block scenarios | Conditional source-zone and block-scenario policies exist; no physical/annual frequencies. | Policy validator and selected Tschamut source policy exist. | Python policy tests and validator pass. | V1 contract/scaffold. | Policy is not yet connected to a completed real-site trajectory ensemble. | Keep early; freeze selected pilot scenario semantics before running ensembles. |
| Hazard-map semantics | Current outputs are diagnostic or sampling-weighted conditional; annual frequency and risk are unsupported. | Implemented in `src/probabilistic.rs` and `scripts/build_hazard_layers.py`. | Rust probabilistic tests and Python hazard tests pass. | V0-V1. | Overlapping source zones, physical probabilities, and annual frequencies remain undefined. | Add semantics guide references to all active package/report outputs. |
| Probabilistic/weighted maps | Weighted conditional maps and tidy conditional intensity-exceedance tables are supported. | Hazard builder joins trajectory metadata and computes conditional layers. | Python tests cover weighted behavior, mixed-trajectory rejection, and layer idempotence. | V1. | No source-frequency model or per-cell annual curve. | Do not label current curves as annual intensity-frequency. |
| GeoTIFF/QGIS package | CRS-correct GeoTIFF first; COG optimization later; pilot package manifest can be validated. | GeoTIFF export and pilot package validator exist. | Python GeoTIFF and pilot-package validator tests pass. | V1 for manifest/package contract; weaker for GIS usability. | Current checkout lacks the referenced real-pilot package manifest; tests use placeholder GeoTIFF bytes in validator fixture. | Reconcile package evidence and add real tiny GeoTIFF readability/QGIS acceptance fixture. |
| Validation maturity | V0-V5 maturity framework exists; current repo is not V5. | `docs/validation_maturity_framework.md` and validation docs define levels. | Consistency checks provide partial claim hygiene. | Documentation framework. | CLI validation summaries do not surface maturity/scientific status enough. | Add maturity/status labels to active report templates and default CLI output. |
| Tschamut/swissALTI3D pilot | Controlled no-tuning public/real-site pilot is the immediate gateway. | Public geodata manifest, source policy, DEM-sensitivity no-go gate, conditional pilot no-go gate, and GIS package review docs exist. | Validators pass. | Pilot scaffold/no-go evidence. | No generated trajectories, hazard layers, conditional curves, performance budget, or reproducible local GIS package in current checkout. | Treat as not yet run; next work should produce a reproducible conditional pilot package or clearly mark local-only evidence. |
| Chant Sura validation | Main external trajectory/contact validation evidence. | Validation cases and reports exist. | `cargo run -- validate --all` passes. | Partial V2. | Large errors remain in some diagnostic contact metrics; no active shape validation. | Use as shape-readiness evidence, not proof of operational validity. |
| Calibration workflows | Calibration is separate from defaults and validation. | `calibration/` scripts/reports exist; selected values are not default physics. | Repository checks and docs support separation. | Research calibration evidence. | Older static reports can be overread if maturity labels are absent. | Keep calibration after holdout policy and pilot evidence. |
| Performance/HPC readiness | Single-socket throughput, local parallelism, deterministic chunking, and eventual CSCS/SLURM path are roadmap goals. | Seed/order tests, benchmark scripts, local hazard reducer, Parquet impact support, and artifact audit exist. | Rust HPC tests and Python workflow tests pass. | V1 engineering evidence. | No deterministic parallel trajectory runner, resume semantics, tiled reducer, NUMA/I/O concurrency evidence, or pilot-scale budget. | Couple performance work to the public pilot; do not start speculative distributed orchestration. |
| Local parallelism/chunking/Parquet | Local reducer and chunk manifests exist for hazard layers; trajectory Parquet/parallel runner remain future. | `scripts/build_hazard_layers.py` supports reducer workers; impact Parquet support exists. | Python reducer parity tests pass. | V1 for hazard reducer only. | Documentation can conflate implemented hazard reducer with missing trajectory execution chunks. | Split roadmap language by workflow stage. |
| Forest/obstacle/fragmentation | Scientifically important; implementation deferred. | Planning/scoping only; selected Tschamut manifest says forest/obstacle relevance is not scoped. | No implementation tests expected. | Planning only. | Swiss valley pilot interpretation may be confounded without scoping. | Scope forest/obstacle relevance before interpreting pilot results. |

## 4. Scientific Claim Audit

Supported claims:

- The core simulator is an equivalent-sphere research model with deterministic
  verification coverage. Evidence: `docs/model_design.md`,
  `src/dynamics.rs`, `src/integrator.rs`, `tests/physics.rs`,
  `cargo test`, and `cargo run -- verify --all`.
- Current hazard products are diagnostic or sampling-weighted conditional, not
  annual-frequency or risk products. Evidence:
  `docs/hazard_map_semantics.md`, `src/probabilistic.rs`,
  `tests/probabilistic_phase1.rs`, and `tests/test_hazard_layers.py`.
- Public swisstopo preparation is operational input/provenance work, not model
  validation evidence. Evidence: `docs/swisstopo_data_strategy.md`,
  `docs/dataset_strategy.md`, `docs/public_real_site_geodata_preparation.md`,
  and `data/datasets.yaml`.
- The repository is explicit that it does not claim equivalence with RAMMS or
  other proprietary tools. Evidence: `AGENTS.md`, `README.md`, and
  `docs/literature_review.md`.

Partially supported claims:

- Performance/HPC readiness is supported by deterministic seed/order tests,
  benchmark scaffolding, local hazard reducer parity tests, and artifact audit.
  It is not yet supported by a pilot-scale trajectory execution benchmark or
  a deterministic parallel trajectory runner.
- GIS readiness is supported for generated GeoTIFF layers and manifest-backed
  pilot-package validation. It is not yet supported by a reproducible checked
  real-pilot package in the current checkout or by QGIS acceptance evidence.
- Validation evidence is meaningful at V0-V2. It is not yet V3 site-scale
  hazard-pattern validation, V4 cross-site generalization, or V5 operational
  reproducibility.

Unsupported or future-only claims:

- Annual intensity-frequency curves per grid cell, return periods, physical
  source frequency, risk maps, exposure/vulnerability modeling, and operational
  hazard assessment.
- Public runtime active non-spherical shape dynamics.
- Forest, barrier, building, fragmentation, MPI/GPU/SLURM, or national
  production workflows.

Overclaimed claims found:

- No major operational overclaim was found in `README.md`, `AGENTS.md`, or
  `docs/hazard_map_semantics.md`.
- The most important overstatement is narrower: `docs/next_development_targets.md`
  marks the pilot GIS/QGIS package target complete at automated
  diagnostic-review level even though the referenced real-pilot package is not
  reproducible from the current checkout and the tracked pilot gate still says
  `gis_package_generated: no-go`.

Ambiguous claims:

- "Passed" in validation output means the case contract executed and its
  thresholds were satisfied. It does not always mean strong scientific
  validation. This is documented elsewhere, but the default CLI summary should
  carry that distinction.
- "Intensity-frequency" appears in roadmap titles. The current roadmap text
  usually explains that current products are conditional exceedance curves, but
  the title can still be read as a promise of annual frequency.
- "Probability" in layer names and metadata is safe only when paired with
  denominator and conditional/sampling semantics.

## 5. Documentation Consistency Audit

High-priority inconsistencies:

1. **Pilot GIS package evidence is contradictory.**

   Evidence: `docs/next_development_targets.md` says Target 5 is complete at
   automated diagnostic-review level and cites
   `docs/tschamut_public_pilot_gis_package_review.md`. That review says the
   validator passed for
   `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json`.
   The current checkout does not contain that manifest, and the tracked gate in
   `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
   records `gis_package_generated: no-go`. The tracked no-go report also says
   no trajectories, hazard layers, conditional curves, GIS artifacts, runtime,
   memory, file counts, or checksums exist yet.

   Required correction: either mark the GIS package review as historical
   local-only evidence and downgrade the roadmap target, or add a small
   committed fixture/package contract that can be reproduced and validated from
   a clean checkout. Do not describe the real-pilot GIS package as complete
   without reproducible evidence.

2. **Validation maturity is documented but not sufficiently visible in default
   validation output.**

   Evidence: `docs/validation_maturity_framework.md` distinguishes V0-V5
   evidence. `cargo run -- validate --all` passes, but the default summary
   prints `Passed` for proxy/diagnostic cases whose scientific interpretation
   remains limited.

   Required correction: add maturity/scientific-status labels to default
   validation summaries or make the documented review command use
   `--json-lines` with status fields.

3. **Roadmap authority is diffuse.**

   Evidence: `docs/README.md` indexes active contracts, scientific roadmaps,
   historical reports, benchmark reports, autonomous logs, and session records.
   It is better than earlier versions, but still too easy for an agent to cite
   a historical report as current roadmap authority.

   Required correction: split the index into current governing documents,
   current evidence reports, historical/superseded records, and work logs.

Medium-priority inconsistencies:

- `docs/repository_scientific_roadmap_review.md` has a status tied to an older
  commit (`post-332e626`) even though the repository is now at `63851b9`.
  Much of the content remains useful, but the status label should either be
  updated or explicitly marked as a snapshot.
- Some benchmark/performance docs describe historical measurement profiles,
  while newer docs emphasize pilot-coupled performance and local parallelism.
  They need clearer "current baseline" versus "historical result" labels.
- `CHANGELOG.md` contains a patch-candidate numerical-fix note for
  `translational_v0`. Because `AGENTS.md` treats default numerical behavior as
  version-sensitive, release notes should keep tying that entry to the
  regression tests proving the old behavior was incorrect.

Low-priority cleanup:

- `docs/agent_work_log.md` is useful as an audit trail, but it should not be
  treated as a roadmap authority.
- Local ignored `.DS_Store` and Python cache files exist; they are not tracked.

## 6. Test And Validation Audit

What is strong:

- Rust verification and unit tests are broad for the current implemented
  mechanics, parser behavior, deterministic seeds, shape gating, scarring
  diagnostics, and probabilistic metadata.
- Python workflow tests now cover central repository workflows, including
  hazard layers, pilot package validation, DEM sensitivity scaffolds,
  performance scaffolding, geodata manifests, source-scenario policies, and
  repository consistency checks.
- `cargo run -- verify --all` and `cargo run -- validate --all` pass.
- Real/private geodata remains outside git; only `.gitkeep` files are tracked
  in generated-output directories.

Main gaps:

- The pilot GIS package validator does not prove GeoTIFF readability. In
  `tests/test_pilot_gis_package_validator.py`, the artifact named as a GeoTIFF
  is placeholder bytes, so the validator is currently a manifest/package
  contract check rather than GIS raster QA.
- Default validation output does not make validation maturity visible enough.
  This is a communication/test-output problem, not a failed validation case.
- DEM sensitivity is still mostly dry-run and gate-level. It has not yet been
  extended to trajectory and hazard-layer stability metrics for a real public
  pilot domain.
- Deterministic reproducibility is tested for seeds and reducers, but not for
  a full parallel trajectory runner because that runner does not yet exist.
- Performance benchmarks are smoke and report workflows, not regression
  budgets for a pilot-scale workload.

Specific test additions that would reduce risk:

- A tiny real GeoTIFF fixture or raster-library smoke test for the pilot GIS
  package validator.
- A validation CLI test that asserts default summaries expose maturity or
  scientific-status labels.
- A clean-checkout test or consistency rule that prevents docs from marking an
  ignored pilot package complete unless a committed fixture, manifest, or
  no-go report supports that claim.
- A deterministic trajectory/hazard DEM-sensitivity fixture.
- A small local-parallel trajectory execution reproducibility test once that
  feature exists.

## 7. Examples And Case Audit

Examples:

- `examples/inclined_plane.json` remains aligned with the implemented
  `cargo run -- run --config examples/inclined_plane.json --output
  trajectory.csv` style.
- CLI help confirms the implemented subcommands are `run`, `verify`,
  `validate`, and `benchmark`.

Verification and validation cases:

- Checked-in verification and validation cases are runnable and pass.
- Optional/private real-site data paths are correctly not required by
  `cargo run -- validate --all`.
- Chant Sura cases remain useful validation evidence, but they should be read
  as partial field evidence and shape-readiness context, not proof that the
  current model captures full non-spherical impact physics.
- The Tschamut public conditional pilot is correctly represented by the tracked
  pilot gate as no-go/no-run, but this conflicts with the later GIS package
  target completion language.

Generated and local artifacts:

- `git ls-files` confirmed generated output and raw data directories only
  track `.gitkeep` files in the inspected patterns.
- Local ignored artifacts are large: `scripts/audit_local_artifacts.py --json`
  reported `12752444149` ignored bytes in total, with
  `validation/results/` alone containing `106352` files and `12264504996`
  bytes. This is not a git leak, but it is a review hazard because local
  evidence can be mistaken for repository-reproducible evidence.

## 8. Roadmap Reassessment

Move up:

- **Reconcile the pilot GIS package evidence state.** This should happen before
  more roadmap ranking changes, because the current documents disagree about
  whether the real-pilot package exists as reproducible evidence.
- **Make validation maturity visible in outputs.** The framework exists; the
  next improvement is to put it where users see "Passed".
- **Add true raster-readability/QGIS package smoke evidence.** GeoTIFF export
  exists, but package validation should not stop at placeholder bytes and
  checksums.
- **Extend DEM sensitivity into trajectory/hazard-layer comparison.** This is
  a central pilot confounder and should precede calibration.

Keep high:

- **Controlled public/real-site Tschamut pilot with embedded performance
  readiness.** It remains the best immediate end-to-end milestone, but it is
  pilot evidence, not decisive physics validation.
- **Source-zone/block-scenario semantics.** Conditional denominators and any
  future frequency semantics depend on this.
- **Deterministic local parallel execution.** This remains warranted, but it
  should be coupled to pilot workload measurements and not treated as generic
  optimization.

Move down or pause:

- **Active shape-contact runtime wiring.** Keep paused until shape-readiness
  evidence and decision gates justify exposing the scaffold.
- **Terrain/material calibration.** Keep deferred until holdout policy, pilot
  evidence, and DEM/source-zone confounders are controlled.
- **COG/cloud optimization.** Keep GeoTIFF correctness, CRS metadata, grid
  alignment, nodata, and QGIS inspectability ahead of cloud optimization.
- **Annual intensity-frequency.** Keep explicitly gated behind physical source
  frequency semantics and validation maturity.

Remove or archive:

- Do not delete historical reports automatically, but move or label older
  roadmap/evidence records so they cannot compete with active governing
  documents.

## 9. Prioritized Findings

### Critical

No critical code or documentation issue was found that currently makes the
repository claim operational validity, corrupt tracked outputs, or silently
change default physics during this review. The repo still needs strong caution
because several high-priority evidence gaps can mislead readers if left
unfixed.

### High

1. **Pilot GIS package completion is overstated relative to reproducible
   repository evidence.**

   Evidence: `docs/next_development_targets.md` marks Target 5 complete and
   `docs/tschamut_public_pilot_gis_package_review.md` records a validator pass
   for an ignored manifest path. The current checkout does not contain that
   manifest. `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
   and `docs/tschamut_public_conditional_pilot_gate_report.md` say the pilot is
   still no-go with no generated GIS package.

   Risk: readers may believe the real Tschamut pilot GIS package is
   reproducibly complete when only local/ignored evidence was reviewed.

   Action: downgrade/clarify the roadmap target or add a committed tiny
   reproducible package fixture and a clean-checkout consistency rule.

2. **Default validation summaries can blur execution pass with scientific
   validation strength.**

   Evidence: `cargo run -- validate --all` passes all cases, including
   diagnostic/proxy cases with limited scientific maturity. The maturity
   framework exists, but the default CLI output does not put that maturity next
   to the pass result.

   Risk: users can confuse "case contract passed" with "field-validated
   operational model."

   Action: add maturity/scientific-status labels to validation summaries and
   active report templates.

3. **Pilot GIS package validation is not raster QA.**

   Evidence: `scripts/validate_pilot_gis_package.py` validates package
   manifests, checksums, unsupported labels, CRS/datum/grid metadata, parity
   inventories, and hazard manifest links. Its tests use placeholder bytes for
   a GeoTIFF artifact.

   Risk: a package can pass the validator while containing an unreadable or
   semantically wrong raster.

   Action: add a tiny valid GeoTIFF fixture or optional `rasterio`/GDAL-backed
   smoke path; at minimum check TIFF magic and expected raster metadata for
   committed fixtures.

4. **The full public real-case intensity-frequency target remains far beyond
   the current implemented evidence.**

   Evidence: current code supports conditional hazard layers and weighted
   conditional exceedance tables, not annual source-frequency semantics. The
   Tschamut pilot gate is still no-go and no local reproducible public pilot
   package is present.

   Risk: roadmap titles can outrun implemented probability semantics.

   Action: keep the next milestone as a conditional public real-site pilot and
   explicitly defer physical/annual intensity-frequency curves.

### Medium

5. **Forest/obstacle relevance is still unscoped for the selected pilot
   domain.**

   Evidence: `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
   records forest/obstacle relevance as not scoped.

   Risk: a Swiss valley pilot can fail or appear successful for reasons
   unrelated to the trajectory kernel.

   Action: perform a pilot-domain forest/obstacle relevance scoping report
   before interpreting real-site pilot hazard patterns.

6. **Local artifact volume can make local evidence look more reproducible than
   it is.**

   Evidence: `scripts/audit_local_artifacts.py --json` reported about
   12.75 GB of ignored local artifacts.

   Risk: review docs can accidentally cite local-only outputs.

   Action: add a cleanup/reproduction policy and make reports distinguish
   tracked, ignored-local, and externally hosted evidence.

7. **Performance readiness remains contract-level and pilot-coupled, not a
   completed scaling capability.**

   Evidence: tests and reports cover deterministic seeds, local reducer
   parity, and benchmark scaffolds; no deterministic parallel trajectory
   runner or pilot-scale budget exists.

   Risk: "HPC readiness" can be overread as cluster readiness.

   Action: keep performance work tied to the first public pilot and implement
   deterministic local parallel trajectory execution before SLURM/CSCS work.

8. **Documentation authority remains broad.**

   Evidence: `docs/README.md` indexes many active and historical documents.

   Risk: future agents may pick stale reports as governing references.

   Action: split current contracts, current roadmap, evidence reports,
   historical records, and work logs more aggressively.

9. **Versioning rationale for default numerical bug fixes should remain
   explicit.**

   Evidence: `CHANGELOG.md` notes a `translational_v0` patch-candidate
   numerical bug fix that changes default numerical results.

   Risk: future changes can cite this as precedent for unversioned default
   changes.

   Action: keep the changelog entry tied to regression tests and the
   "previous behavior was clearly incorrect" rule in `AGENTS.md`.

### Low

10. **Local cache clutter exists but is ignored.**

    Evidence: ignored `.DS_Store` and `__pycache__` files are present locally.

    Action: optional cleanup command or audit script mode; no repository change
    is required.

## 10. Recommended Next Development Tasks

1. **Reconcile the Tschamut pilot GIS package evidence state.**

   Objective: make roadmap and evidence documents agree on whether the pilot
   GIS package is reproducible, local-only, or not yet generated.

   Rationale: this is the clearest current repository story drift.

   Files likely affected: `docs/next_development_targets.md`,
   `docs/roadmap_recommendation_matrix.md`,
   `docs/tschamut_public_pilot_gis_package_review.md`,
   `docs/tschamut_public_conditional_pilot_gate_report.md`,
   optionally `scripts/check_repo_consistency.py`.

   Definition of done: a clean checkout can either validate the claimed
   fixture/package, or the docs explicitly mark the real-pilot package review
   as historical local-only and Target 5 as incomplete for reproducibility.

   Suggested tests/checks: `python3 scripts/check_repo_consistency.py`,
   targeted check that the referenced manifest exists or is labelled local-only.

2. **Strengthen pilot GIS package raster QA.**

   Objective: ensure package validation can catch unreadable or malformed
   GeoTIFF artifacts.

   Rationale: manifest-level correctness is not enough for GIS readiness.

   Files likely affected: `scripts/validate_pilot_gis_package.py`,
   `tests/test_pilot_gis_package_validator.py`, `docs/pilot_gis_package.md`,
   `docs/hazard_layers.md`.

   Definition of done: at least one tiny valid GeoTIFF fixture is inspected for
   raster readability, CRS/transform/nodata consistency, and parity with the
   package manifest.

   Suggested tests/checks: targeted Python unittest, hazard-layer GeoTIFF
   tests, optional raster-library smoke when dependency is available.

3. **Expose validation maturity in default validation outputs.**

   Objective: keep "Passed" from being mistaken for operational validation.

   Rationale: scientific claim safety should be visible at the point of result
   consumption.

   Files likely affected: `src/main.rs`, `src/validation.rs`,
   validation report templates, `docs/validation_plan.md`,
   `docs/validation_maturity_framework.md`.

   Definition of done: default validation summaries show maturity/scientific
   status or diagnostic status for every case.

   Suggested tests/checks: CLI output tests or snapshot-style assertions,
   `cargo run -- validate --all`, consistency check.

4. **Extend DEM sensitivity to trajectory and hazard-layer stability.**

   Objective: compare map products across DEM resolution/interpolation/
   smoothing variants before calibration.

   Rationale: terrain representation can dominate pilot results.

   Files likely affected: `scripts/run_dem_terrain_sensitivity.py`,
   `tests/test_dem_terrain_sensitivity.py`,
   `docs/dem_terrain_sensitivity_benchmark.md`, small fixtures.

   Definition of done: CI-safe fixture produces deterministic trajectory and
   hazard map-difference diagnostics without private data.

   Suggested tests/checks: Python unit tests, `cargo run -- verify --all` if
   verification fixtures are added.

5. **Produce the first reproducible conditional public real-site pilot package
   from public inputs.**

   Objective: create a no-tuning, share-safe pilot evidence package with
   provenance, source policy, trajectories, hazard layers, conditional
   exceedance tables, GIS outputs, and performance report.

   Rationale: this remains the central milestone for the Swiss hazard-map goal.

   Files likely affected: pilot docs under `docs/`, validation pilot manifests
   under `validation/pilot_runs/`, ignored local output directories, manifest
   validators, hazard package docs.

   Definition of done: all artifacts are either tracked tiny fixtures or
   explicitly ignored-local with checksums and reproduction commands; report
   states conditional/non-annual semantics.

   Suggested tests/checks: manifest validators, source-policy validator,
   artifact audit, hazard-layer builder tests, consistency check.

6. **Implement deterministic local parallel trajectory execution prototype.**

   Objective: add order-independent local parallel execution for trajectory
   ensembles before SLURM or distributed orchestration.

   Rationale: roughly 10,000 trajectories per release zone is a pilot
   feasibility issue, not late optimization.

   Files likely affected: Rust orchestration modules, CLI runner, manifest
   schema/tests, performance benchmark scripts.

   Definition of done: fixed-seed results and reducer inputs are identical
   independent of worker count and execution order for a small fixture.

   Suggested tests/checks: deterministic parallel/serial parity test,
   benchmark smoke profile, `cargo test`, `cargo run -- verify --all`.

7. **Scope forest/obstacle relevance for the selected pilot domain.**

   Objective: record whether forest, buildings, barriers, or other obstacles
   are likely first-order confounders in the pilot area.

   Rationale: this affects interpretation of pilot success/failure even before
   implementation.

   Files likely affected: `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`,
   `docs/swisstopo_data_strategy.md`, pilot report docs.

   Definition of done: pilot manifest and report identify available public
   layers, expected relevance, unsupported effects, and interpretation limits.

   Suggested tests/checks: geodata manifest validator, consistency check.

8. **Clarify docs authority and historical status.**

   Objective: make it hard for contributors to confuse active roadmap with
   historical evidence.

   Rationale: the repo now has enough docs that source-of-truth drift is a
   practical risk.

   Files likely affected: `docs/README.md`, selected roadmap/report headers.

   Definition of done: active contracts, current roadmap, current evidence
   reports, historical records, and work logs are clearly separated.

   Suggested tests/checks: `python3 scripts/check_repo_consistency.py`,
   targeted `rg` for stale status labels.

9. **Define pilot-coupled performance pass/no-go reporting.**

   Objective: record trajectory count, event count, file count, bytes, runtime,
   worker count, memory, and bottleneck category for the pilot.

   Rationale: performance work should remain coupled to scientific workflows.

   Files likely affected: `docs/performance_benchmarking.md`,
   benchmark scripts, pilot report templates.

   Definition of done: a smoke benchmark and future pilot report template
   share the same metrics and explicitly avoid cluster-readiness claims.

   Suggested tests/checks: benchmark smoke profile, Python benchmark tests,
   artifact audit.

## 11. Final Judgment

The repository is currently best described as a **reproducible research
workbench with strong verification and early pilot workflow scaffolding**.

It is more mature than an experimental simulator because it has deterministic
core mechanics, broad verification cases, runnable validation cases,
calibration separation, hazard-layer post-processing, conditional probability
semantics, CRS-aware GeoTIFF output, public geodata provenance scaffolding,
benchmark tooling, and passing Rust/Python checks.

It is not yet a pilot-ready research workflow for the full target because the
public real-site workflow has not produced a clean, reproducible end-to-end
package with public inputs, source policy, deterministic large ensemble,
hazard layers, conditional per-cell exceedance products, GIS QA, performance
budget, and interpretation report.

It is not an operationally validated hazard tool. Current products are
diagnostic or sampling-weighted conditional hazard indicators. They are not
physical annual intensity-frequency curves, return-period maps, risk maps, or
official hazard assessments.
