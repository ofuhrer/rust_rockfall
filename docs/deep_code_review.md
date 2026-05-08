# Deep Code Review

Date: 2026-05-08

This review focuses on code quality, maintainability, correctness risk, safety,
duplication, architecture, and testability. It does not reassess the scientific
roadmap except where code structure affects scientific correctness.

## 1. Executive Summary

Overall code health is good for a research workbench: the Rust core has strong
unit and integration coverage, verification and validation commands pass, hazard
probability language is guarded against annual-frequency overclaiming, and
deterministic seed behavior has explicit tests.

The highest-value cleanup is not adding more features. It is hardening the
contracts around inputs and outputs:

- Runtime configuration parsing accepts unknown fields in Rust config structs.
  A misspelled physical parameter can silently fall back to a default.
- DEM parsing and the `Terrain` trait expose infallible runtime calls that can
  panic on malformed grids, nodata stencils, or direct out-of-domain calls.
- Hazard accumulation assumes one trajectory per trajectory CSV and does not
  reject mixed `trajectory_id` files, which can silently corrupt trajectory-level
  denominators and weighted probabilities.
- `scripts/build_hazard_layers.py`, `src/validation.rs`, and `src/shape.rs` are
  very large modules with multiple responsibilities, making future pilot-scale
  changes risky.
- Current execution and post-processing code is still memory-heavy and mostly
  serial; it is adequate for fixtures, but not yet shaped like the eventual
  10,000-trajectories-per-release-zone pilot workflow.

No confirmed critical defect was found by executing the test chain. The most
important risks are high-severity because they can lead to misleading results
when inputs are malformed or when users choose plausible but unsupported input
layouts.

## 2. Review Coverage

Inspected directories and files:

- Repository orientation: `AGENTS.md`, `README.md`, `Cargo.toml`.
- Rust core: `src/lib.rs`, `src/main.rs`, `src/io.rs`, `src/simulation.rs`,
  `src/integrator.rs`, `src/terrain.rs`, `src/dynamics.rs`, `src/geodata.rs`,
  `src/probabilistic.rs`, `src/validation.rs`, `src/shape.rs`,
  `src/manifest.rs`, `src/stochastic.rs`, `src/state.rs`.
- Tests: `tests/config_io_terrain.rs`, `tests/physics.rs`,
  `tests/hpc_readiness.rs`, `tests/probabilistic_phase1.rs`, and Python tests
  under `tests/test_*.py`.
- Scripts and workflows: `scripts/build_hazard_layers.py`,
  `scripts/run_performance_benchmark.py`,
  `scripts/run_dem_terrain_sensitivity.py`, `scripts/audit_case_schema.py`,
  `scripts/check_repo_consistency.py`, preprocessing, calibration, geodata,
  benchmark, and diagnostic scripts.
- Cases and artifacts: `verification/`, `validation/`, `calibration/`,
  `hazard/`, `examples/`, `.github/workflows/ci.yml`, `scripts/git-hooks/`.

Commands run:

| Command | Result |
| --- | --- |
| `git status -sb` | Clean tracked tree; untracked `docs/deep_repository_review.md` already existed. |
| `rg "unwrap\\(|expect\\(|panic!|todo!|unimplemented!|FIXME|TODO|HACK|deprecated|legacy" ...` | Found runtime-facing DEM panics, shape-contact guard panic, validation serialization expects, many test unwraps; no TODO/FIXME/HACK markers in scoped code. |
| `rg "NODATA|nodata|NaN|inf|clamp|default|fallback|seed|random|probability|weight|annual|risk" ...` | Used to inspect nodata, defaults, probability, and seed paths. |
| `rg "TODO|FIXME|HACK" src tests scripts validation verification hazard calibration` | No matches. |
| `cargo fmt --check` | Passed. |
| `cargo clippy --all-targets --all-features -- -D warnings` | Passed. |
| `cargo test` | Passed: 171 Rust tests across unit, integration, and doc-test targets. |
| `cargo run -- verify --all` | Passed all verification cases. |
| `cargo run -- validate --all` | Passed all validation cases, including optional/public cases present locally. |
| `python3 scripts/check_repo_consistency.py` | Passed. |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | Passed: 90 tests, 2 skipped. |
| `python3 scripts/audit_case_schema.py` | Passed for 55 YAML files. |
| `python3 -m pytest` | Not run: current Python reports `No module named pytest`. |

## 3. Critical Findings

No confirmed critical findings were found by the executed checks.

The closest critical-risk areas are the high-priority findings below: silent
unknown fields in runtime configs, DEM runtime panics, and unguarded trajectory
CSV semantics. These are not known to corrupt current checked-in fixtures, but
they can produce misleading output for plausible user inputs.

## 4. High-Priority Findings

### H1. Runtime configs and metadata are not strict against unknown fields

Evidence:

- `src/io.rs` reads configs with `serde_json::from_reader` into
  `SimulationConfig`, but the deserialized structs in `src/simulation.rs`,
  `src/terrain.rs`, `src/geodata.rs`, `src/probabilistic.rs`, and
  `src/shape.rs` do not use `#[serde(deny_unknown_fields)]`.
- `rg deny_unknown_fields src/*.rs` found no strict serde boundaries.
- `scripts/audit_case_schema.py` explicitly says runtime case loading remains
  backward compatible and that the audit helper reports unknown keys "before
  strict parsing becomes a default behavior."

Risk:

A typo such as `friction_coefficent`, `normal_restituton`, or a misspelled
terrain field can be ignored and default behavior can be used. That is a
scientific correctness risk because a run can look valid while using unintended
physics.

Recommended fix:

Introduce strict unknown-field handling for runtime simulation JSON first, then
extend to validation YAML and probabilistic/geodata sidecars. Use either
`#[serde(deny_unknown_fields)]` on stable config structs or a `serde_ignored`
reporting layer that produces clear errors while preserving planned compatibility
where necessary.

Suggested tests:

- `tests/config_io_terrain.rs`: misspelled top-level physical field fails.
- `tests/config_io_terrain.rs`: misspelled nested terrain field fails.
- `tests/probabilistic_phase1.rs`: unknown probabilistic sidecar fields fail or
  are explicitly reported according to the chosen compatibility policy.

### H2. DEM parsing and terrain calls can panic instead of returning errors

Evidence:

- `src/terrain.rs` parses `ncols`, `nrows`, `cellsize`, `xllcorner`,
  `yllcorner`, and `NODATA_value` but does not reject `ncols < 2`,
  `nrows < 2`, non-finite coordinates, non-finite nodata, or non-positive /
  non-finite cell sizes before interpolation.
- `src/terrain.rs` uses `self.ncols - 2` and `self.nrows - 2` in fractional cell
  lookup. A count-consistent `1 x 1` DEM can parse and later underflow or panic.
- `src/terrain.rs` implements the infallible `Terrain` trait for `DemGrid` by
  panicking on `try_height`/`try_normal` errors.
- `ClampedDemGrid::height_clamped` and `normal_clamped` use `expect(...)` after
  clamping; nodata in the interpolation stencil can still make this assumption
  false.

Risk:

Malformed or edge-case public DEM crops can terminate long runs, and panic
paths make it hard to produce provenance-rich "terrain_error" outcomes. This is
especially risky for Swiss pilot ingestion where DEM fixtures will be replaced
by real tiles and crops.

Recommended fix:

Fail fast in `DemGrid::from_ascii_grid_str` for invalid dimensions, non-finite
headers, non-positive cell size, and non-finite cell values except declared
nodata if supported. Then either keep the `Terrain` trait only for guaranteed
safe procedural terrains, or add fallible terrain sampling through the integrator
so DEM errors can become `SimulationError` or trajectory termination flags.

Suggested tests:

- `ncols 1` and `nrows 1` DEMs are rejected at parse time.
- `cellsize 0`, negative, `nan`, and `inf` are rejected.
- Clamped DEM with nodata in the edge interpolation stencil returns a controlled
  error or documented fallback, not a panic.

### H3. Hazard trajectory CSV semantics assume one trajectory per file

Evidence:

- `scripts/build_hazard_layers.py::read_trajectory_sample_batch` sets
  `trajectory_id` from the first row or file stem and returns one
  `TrajectorySampleBatch`.
- `HazardAccumulator.accumulate_trajectory` increments `trajectory_count` once
  per batch/file and accumulates occupancy sets across all rows in that file.
- There is no check that all `trajectory_id` values in a trajectory CSV are the
  same.

Risk:

A combined trajectory CSV with multiple `trajectory_id` values is a plausible
large-workflow input. The current code would treat it as one trajectory, causing
wrong reach/exceedance denominators and wrong sampling-weighted probabilities.
This is a high scientific-output risk because the layer labels would still look
valid.

Recommended fix:

Either reject trajectory CSV files containing more than one `trajectory_id`, or
explicitly split them by `trajectory_id` before accumulation. The minimal
behavior-preserving fix is rejection with a clear error that the current hazard
builder expects one trajectory per CSV.

Suggested tests:

- A trajectory CSV with two different `trajectory_id` values raises `SystemExit`
  with a specific message.
- A CSV without `trajectory_id` keeps the existing file-stem fallback.

### H4. Core review-relevant modules are too large and coupled

Evidence:

- `src/validation.rs`: 5,310 lines.
- `src/shape.rs`: 5,482 lines, including substantial tests and internal
  diagnostics.
- `scripts/build_hazard_layers.py`: 3,941 lines.
- `tests/config_io_terrain.rs`: 3,032 lines.

Risk:

Large modules combine parsing, execution, diagnostics, manifests, report
writing, and tests. This makes drift likely when adding real-site pilot features:
new schema fields must be updated in several places, and future contributors can
miss one of the hidden contracts.

Recommended fix:

Split by stable responsibility, not by convenience:

- Hazard: `inputs`, `accumulator`, `probability`, `raster_export`,
  `manifest`, `html_report`, `cli`.
- Validation: `case_schema`, `case_runner`, `comparators`, `terrain_material`,
  `reporting`.
- Shape: public shape metadata/API, dry-run contact tests, runtime diagnostic
  sidecars, and internal test fixtures.

Suggested tests:

Keep existing golden/fixture tests unchanged during the split. Add import-level
smoke tests for the new Python modules.

### H5. Pilot-scale execution remains memory-heavy and not yet streaming-first

Evidence:

- `src/simulation.rs::simulate_ensemble` returns `Vec<TrajectoryRun>` with all
  samples and impact events in memory.
- `scripts/build_hazard_layers.py::read_trajectory_sample_batch` reads each CSV
  into a tuple before accumulation.
- `HazardAccumulator` retains `deposition_points` for GeoJSON output.
- `write_geotiff_grid` builds a full `pixels` list and full `pixel_bytes` buffer
  before writing.

Risk:

The current structure is fine for fixtures and smoke pilots, but it will become
the bottleneck before national-scale orchestration. It also makes deterministic
parallelization harder because the contracts are currently "materialize then
reduce" rather than "stream rows into deterministic reducers."

Recommended fix:

Define a streaming reducer API before expanding output formats. Keep the
single-trajectory kernel deterministic, but introduce row/event iterators,
chunk manifests, and writer/reducer separation that can process large ensembles
without holding full trajectory samples in memory.

Suggested tests:

- Serial streaming reducer equals current in-memory reducer on fixtures.
- Chunked reducer equals serial reducer for reach, exceedance, weighted layers,
  deposition, and impact density.
- Memory-scale smoke test with many tiny trajectories does not retain samples.

## 5. Medium/Low-Priority Findings

### M1. Layer normalization mutates accumulator state

`scripts/build_hazard_layers.py::HazardAccumulator.layers` scales count grids in
place. A second call would double-normalize probabilities and densities. The
current CLI calls it once, but the method is not safe as a reusable API.

Fix: return normalized copies or split raw-count accumulators from immutable
layer construction.

### M2. Custom GeoTIFF writer is useful but fragile

`write_geotiff_grid` writes uncompressed Float64 GeoTIFFs manually using TIFF
tags and a GeoKey directory. Tests parse the fixture values and tags, which is
good, but there is no GDAL/QGIS compatibility check and no BigTIFF, tiling,
compression, or COG path.

Fix: keep current writer labelled as review-only, add optional external
validation when GDAL tools are available, and prevent large rasters that exceed
classic TIFF constraints.

### M3. Case ordering is hard-coded in the CLI

`src/main.rs::case_order` contains an explicit list of case IDs. This preserves
stable output order, but it will drift as validation cases evolve.

Fix: move ordering metadata into case YAML or use schema-level ordering with
fallback lexical order.

### M4. Schema logic is duplicated across Rust, Python, and docs

Examples:

- Rust probabilistic structs in `src/probabilistic.rs`.
- Python hazard-map package parsing in `scripts/build_hazard_layers.py`.
- YAML audit key lists in `scripts/audit_case_schema.py`.
- Documentation schemas and examples in `docs/`.

Risk is not current failure; risk is drift. For example, the audit script's
`hazard_layers.statistics` keys are narrower than the builder's supported
statistics, though current checked-in cases still pass.

Fix: generate validators from one small schema source, or add consistency tests
that compare supported field names across modules.

### M5. `TerrainClassParameterOverrides.apply` has a silent fallback

`src/geodata.rs` builds a scarring override and if `scarring.validate().is_err()`
it silently reverts to base scarring. Normal metadata validation should prevent
invalid overrides, but a direct call path would hide a bad override.

Fix: return a `Result<ContactParameters, GeodataError>` or make invalid override
states unrepresentable after validation.

### M6. Python scripts mostly terminate with `SystemExit`

This is acceptable for command-line scripts, but it weakens reuse and targeted
unit testing for modules such as hazard accumulation, benchmark preparation, and
geodata preparation.

Fix: introduce narrow exception types for reusable logic and translate them to
`SystemExit` only at CLI boundaries.

### L1. DEM extent naming can confuse center vs footprint semantics

`DemGrid::xmax_m` and `ymax_m` return the maximum cell-center coordinate, while
`footprint_xmax_m` and `footprint_ymax_m` return the raster footprint. The code
has both, but the shorter names are easy to misuse in future GIS work.

Fix: rename or deprecate center-extent names in favor of explicit
`xmax_center_m` / `footprint_xmax_m`.

### L2. Ignored local artifacts are present in the workspace

`find` saw `.DS_Store` and `__pycache__` files under tests/scripts/hazard and
calibration paths. `git ls-files` confirms they are not tracked, and `.gitignore`
covers them. This is not a repository defect, but local cleanup would reduce
review noise.

## 6. Code Smell Inventory

| File/function/module | Issue type | Evidence | Risk | Recommended fix | Suggested test |
| --- | --- | --- | --- | --- | --- |
| `src/io.rs::read_config` and config structs | Silent unknown fields | No `deny_unknown_fields`; direct serde parse | Misspelled physics fields use defaults | Strict deserialization or `serde_ignored` reporting | Unknown top-level and nested field failures |
| `src/terrain.rs::DemGrid::from_ascii_grid_str` | Incomplete input validation | Does not reject `ncols < 2`, `nrows < 2`, non-finite headers | Panic or invalid interpolation | Validate header invariants before constructing | Malformed DEM parser tests |
| `src/terrain.rs::impl Terrain for DemGrid` | Runtime panic path | `unwrap_or_else(... panic!)` | Long run aborts instead of controlled error | Fallible terrain sampling or safe adapter | Out-of-domain/nodata DEM run returns error |
| `src/terrain.rs::ClampedDemGrid` | Unsafe assumption | `expect` after clamping | Nodata stencil can panic | Return controlled error or documented nodata policy | Edge nodata clamped test |
| `scripts/build_hazard_layers.py::read_trajectory_sample_batch` | Hidden input convention | Uses first `trajectory_id` only | Wrong denominators for combined CSV | Reject or split mixed IDs | Mixed-ID CSV test |
| `scripts/build_hazard_layers.py::HazardAccumulator.layers` | Mutating query method | Scales internal count grids | Double normalization if reused | Return layer copies | Calling `layers()` twice is idempotent or disallowed |
| `scripts/build_hazard_layers.py::write_geotiff_grid` | Whole-raster buffering | Builds `pixels` and `pixel_bytes` | Memory spike for pilot rasters | Stream strips or use writer library | Large-grid smoke with bounded memory |
| `src/simulation.rs::simulate_ensemble` | Full materialization | Returns all trajectories/samples | Pilot-scale memory pressure | Streaming writer/reducer contract | Streaming equals materialized fixture |
| `src/main.rs::case_order` | Hard-coded registry | Explicit case IDs | New cases sort unexpectedly | Put ordering in YAML or level/family metadata | New case order test without code edit |
| `scripts/audit_case_schema.py` | Duplicated schema | Separate key lists from Rust/Python parsers | Field support drift | Centralize schema constants | Compare audit keys with builder-supported keys |

## 7. Duplication And Dead-Code Audit

No tracked dead-code marker or TODO/FIXME/HACK backlog was found in scoped code.
`rg "TODO|FIXME|HACK"` returned no matches under `src`, `tests`, `scripts`,
`validation`, `verification`, `hazard`, or `calibration`.

Duplication risks:

- Validation/case schema knowledge appears in `src/validation.rs`,
  `scripts/audit_case_schema.py`, checked-in YAML cases, and documentation.
- Probabilistic metadata is represented in both `src/probabilistic.rs` and
  `scripts/build_hazard_layers.py`.
- Geodata metadata validation exists in Rust (`src/geodata.rs`) while public
  benchmark and real-site validators exist in Python scripts.
- Hazard report metadata, manifest output, HTML text, raster export, and reducer
  state live in one Python file, increasing coupling.

Dead-code or obsolete-path observations:

- `shape_contact_v0` has substantial dry-run/test scaffolding and an explicit
  runtime guard. This is not dead code; it is intentionally inactive. Keep the
  guard and labels clear.
- Calibration experiment outputs under `calibration/experiments/` are tracked
  small artifacts. They should remain explicitly labelled as calibration
  evidence, not validation or defaults.
- Ignored `__pycache__` and `.DS_Store` files are local artifacts only, not
  tracked repository content.

## 8. Error-Handling And Runtime-Safety Audit

Good patterns:

- `SimulationConfig::validate` rejects non-finite and invalid core physics
  values before normal CLI execution.
- Unsupported `shape_contact_v0` runtime execution is blocked by validation.
- Probabilistic metadata rejects annual-frequency generation and inappropriate
  physical-probability labels in Phase 1.

Runtime-safety risks:

- DEM terrain paths can panic through the infallible `Terrain` trait.
- Direct callers of `integrator::simulate_fixed_step_with_events` can bypass
  `SimulationConfig::validate`; invalid `IntegratorSettings` are not validated
  inside the integrator.
- Validation code contains several `expect(...)` calls for serialization and
  prevalidated shape metadata. These are lower risk than DEM panics, but they
  are still runtime-facing during validation/report generation.
- Python parsers often use `SystemExit`. This is acceptable for CLI execution,
  but it should not leak into reusable library boundaries as workflows become
  more modular.

## 9. Determinism And Reproducibility Audit

Strengths:

- `tests/hpc_readiness.rs` covers derived seed dependence on case and trajectory
  ID, same-seed reproducibility, order-independent ensemble results, and chunk
  manifest contracts.
- Hazard chunk merging sorts by `chunk_id`, and deposition input is assigned to
  the first chunk only, avoiding double-counting in the current chunked reducer.
- Weighted hazard tests cover uniform weights, nonuniform weights, missing
  metadata, filters, and event-weighted significant impact density.

Remaining risks:

- The current trajectory reducer contract is file-oriented, not trajectory-ID
  oriented. That weakens reproducibility if future producers emit combined CSVs.
- Floating-point summation order is deterministic in current sorted merges, but
  future parallel reducers need an explicit merge/rounding contract for weighted
  grids and conditional curves.
- Manifest checksums and row counts exist in some workflows but are not yet a
  universal contract for every large output path.

## 10. Terrain/GIS/Indexing Audit

Strengths:

- Tests cover bottom-origin DEM interpolation, clamped DEM behavior, terrain
  class lookup, Swiss terrain metadata against DEM dimensions/extents, GeoTIFF
  values, and CRS tag presence.
- `GridSpec.cell` uses top-row raster indexing consistently with ESRI ASCII
  output orientation.
- `geotiff_affine_transform` uses `[cell_size, 0, xmin, 0, -cell_size, ymax]`,
  matching north-up raster convention.

Risks:

- DEM header validation is incomplete, as described in H2.
- Explicit grid parsing rejects non-positive dimensions and cell size, but does
  not explicitly reject `nan`/`inf` coordinate or cell-size inputs from the CLI.
- Classic TIFF writing is not guarded against very large rasters or byte counts.
- QGIS/GDAL compatibility is documented as a target, but only repository-local
  GeoTIFF parser tests were observed in the automated suite.
- `xmax_m`/`ymax_m` center-extent naming can be confused with footprint extents.

## 11. Hazard/Probability Code Audit

Strengths:

- Annual-frequency generation is schema-visible but rejected.
- Physical probability columns are rejected by the Phase 1 hazard builder.
- Weighted conditional maps are explicitly normalized by filtered sampling
  weight, and significant-impact density uses event-weight sum semantics.
- Conditional intensity-exceedance curve rows include probability mode,
  denominator, numerator, weighted flag, and annualized flag.

Risks:

- One-file-per-trajectory is not enforced.
- `HazardAccumulator.layers` mutates counts to probabilities in place.
- Weighted and unweighted layer semantics are implemented in Python separately
  from Rust probabilistic metadata validation, creating drift risk.
- The hazard builder has many stringly typed layer keys. Tests cover current
  keys, but future additions can easily miss manifest/HTML/conditional-curve
  sections.

## 12. Performance And Scaling Code Audit

Current bottleneck risks:

- Rust ensemble results are materialized as vectors of full trajectory samples.
- Python hazard inputs are parsed into Python objects per row and per file.
- Raster grids are nested Python lists.
- GeoTIFF export buffers the full raster as Float64 bytes.
- Chunked hazard reduction is local-threaded and deterministic, but partial
  accumulators are still in memory.
- CSV remains central for trajectories, with Parquet support focused on impact
  events rather than full trajectory/event stream contracts.

Recommendation:

Keep performance work coupled to pilot workflows, but make the next performance
cleanup structural: streaming reducers and explicit chunk contracts before
format churn or distributed orchestration.

## 13. Test Gap Analysis

| Priority | Test purpose | Likely file | Failure mode caught | Minimal fixture |
| --- | --- | --- | --- | --- |
| High | Unknown runtime config fields fail clearly | `tests/config_io_terrain.rs` | Silent default due typo | JSON with `friction_coefficent` |
| High | Malformed DEM dimensions rejected | `tests/config_io_terrain.rs` | `ncols - 2` underflow/panic | `1 x 1` ESRI ASCII grid |
| High | DEM non-finite/invalid headers rejected | `tests/config_io_terrain.rs` | NaN/inf/zero cell size | Small ASCII headers |
| High | Mixed `trajectory_id` CSV rejected or split | `tests/test_hazard_layers.py` | Wrong hazard denominator | Two-ID trajectory CSV |
| High | `HazardAccumulator.layers` cannot double-normalize | `tests/test_hazard_layers.py` | Reused accumulator changes results | Tiny one-cell accumulator |
| Medium | Explicit grid rejects NaN/inf CLI values | `tests/test_hazard_layers.py` | Invalid raster metadata | CLI args with `nan` |
| Medium | GDAL/QGIS-readable GeoTIFF smoke, if tools exist | Python integration test | Local parser passes but GIS fails | Tiny GeoTIFF fixture |
| Medium | Streaming/chunked reducer equals serial | `tests/test_hazard_layers.py` | Parallel reducer drift | 3 trajectories, 2 chunks |
| Medium | Validation serialization expects cannot panic | Rust validation tests | Report generation panic | Terrain/material gaps fixture |
| Medium | Private-data-absent paths skip gracefully | Python/Rust validation tests | Local-only data hard failure | Missing optional paths |

## 14. Refactoring Recommendations

1. Strict config boundary
   - Objective: reject or report unknown runtime config fields.
   - Files: `src/io.rs`, `src/simulation.rs`, nested config structs, tests.
   - Strategy: start with `SimulationConfig` JSON only; keep defaults unchanged.
   - Tests: unknown top-level and nested fields.
   - Risk: Medium; may expose stale fixtures.

2. DEM parser and fallible terrain hardening
   - Objective: eliminate DEM panic paths for malformed inputs.
   - Files: `src/terrain.rs`, `src/simulation.rs`, `src/integrator.rs`, tests.
   - Strategy: add parse validation first; then decide whether to add fallible
     sampling to the integrator.
   - Tests: malformed DEMs, nodata edge cases, out-of-domain cases.
   - Risk: Medium.

3. Enforce trajectory CSV granularity
   - Objective: prevent mixed-trajectory CSVs from corrupting denominators.
   - Files: `scripts/build_hazard_layers.py`, `tests/test_hazard_layers.py`,
     hazard docs if behavior is documented.
   - Strategy: reject mixed IDs first; split-by-ID later only if needed.
   - Tests: mixed ID, no ID fallback, one ID success.
   - Risk: Low.

4. Split hazard builder into modules
   - Objective: reduce coupling in `scripts/build_hazard_layers.py`.
   - Files: new `scripts/hazard_layers/` package plus current tests.
   - Strategy: mechanical extraction with no behavior changes.
   - Tests: entire Python unittest suite and fixture output comparisons.
   - Risk: Medium.

5. Separate raw accumulation from layer normalization
   - Objective: make reducer state reusable and prevent double normalization.
   - Files: hazard accumulator module/tests.
   - Strategy: keep raw counts immutable during `build_layers`.
   - Tests: repeated layer build idempotence.
   - Risk: Low.

6. Streaming trajectory/hazard reducer prototype
   - Objective: reduce memory pressure for pilot-scale ensembles.
   - Files: `src/simulation.rs`, `src/io.rs`, hazard scripts, tests.
   - Strategy: add opt-in streaming path; preserve existing outputs.
   - Tests: streaming equals current materialized outputs.
   - Risk: High.

7. Split validation module by responsibility
   - Objective: make validation schemas, runners, comparators, and reporters
     independently testable.
   - Files: `src/validation.rs` split into submodules.
   - Strategy: no behavior change; keep public API stable.
   - Tests: full Rust suite and validation command.
   - Risk: Medium.

8. Consolidate schema constants
   - Objective: reduce drift between Rust parsers, Python scripts, and audits.
   - Files: `src/probabilistic.rs`, `scripts/audit_case_schema.py`,
     `scripts/build_hazard_layers.py`, schema docs.
   - Strategy: generate or cross-test field lists.
   - Tests: schema consistency tests.
   - Risk: Medium.

9. Add optional external raster validation
   - Objective: verify GeoTIFF outputs with standard GIS tooling when available.
   - Files: tests or scripts around hazard layers.
   - Strategy: skip gracefully if GDAL/rasterio unavailable.
   - Tests: tiny GeoTIFF metadata/value check with external reader.
   - Risk: Low.

## 15. Recommended Next Development Prompt

Use this prompt for the next focused implementation task:

> You are working in `/Users/fuhrer/Desktop/rust_rockfall`. Fix only the highest-priority code-safety issue: runtime simulation JSON configs silently accepting unknown fields. Do not change simulator defaults or physics. Inspect `src/io.rs`, `src/simulation.rs`, nested config structs/enums, and existing config tests. Implement strict unknown-field rejection or explicit `serde_ignored` reporting for `io::read_config` so misspelled top-level and nested physical/terrain fields fail with clear errors. Add focused tests in `tests/config_io_terrain.rs` for an unknown top-level key and an unknown nested terrain/parameter key. Keep existing examples and validation cases passing. Run `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test`, `cargo run -- verify --all`, `cargo run -- validate --all`, and `python3 scripts/check_repo_consistency.py`. Do not modify physics behavior, calibration parameters, generated outputs, or roadmap documents.

