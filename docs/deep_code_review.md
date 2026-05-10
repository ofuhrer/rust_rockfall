# Deep Code Review

## 1. Executive Summary

Overall code health is good for a research codebase: the core Rust simulation path is deterministic by design, physics and hazard workflows have unusually broad automated coverage, CI is split into sensible jobs, and the repository shows strong discipline around explicit schema/version contracts.

The biggest reliability risks are not obvious numerical bugs; they are **silent fallback behavior and oversized orchestration modules**:

- `src/validation.rs` and `src/validation/metric_math.rs` still convert several missing/corrupt situations into `0.0` or empty structures instead of surfacing explicit failures, which can hide invalid validation results.
- Public/runtime-adjacent compatibility paths still panic in places (`src/terrain.rs`, `src/validation.rs`, `src/shape.rs`) instead of returning structured errors.
- A few key files have grown past maintainable size and now mix unrelated responsibilities: `src/validation.rs` (~4.5k lines), `scripts/build_hazard_layers.py` (~6.9k lines), `tests/test_hazard_layers.py` (~4.0k lines), and `scripts/check_repo_consistency.py` (~2.3k lines).
- Python validator scripts are highly duplicated, which raises long-term correctness risk because boundary-rule fixes must be applied in many places.

Highest-value cleanup areas, in order:

1. Remove silent metric/default masking in validation metrics and summary parsing.
2. Replace remaining panic/`expect` paths in runtime-facing or validation-facing code with structured errors.
3. Break up `build_hazard_layers.py` and the remaining bulk of `src/validation.rs`.
4. Consolidate shared validator-script logic into one library module.
5. Harden calibration scripts and add direct tests for them.

## 2. Review Coverage

### Directories and files inspected

- `/home/runner/work/rust_rockfall/rust_rockfall/src`
- `/home/runner/work/rust_rockfall/rust_rockfall/tests`
- `/home/runner/work/rust_rockfall/rust_rockfall/scripts`
- `/home/runner/work/rust_rockfall/rust_rockfall/examples`
- `/home/runner/work/rust_rockfall/rust_rockfall/verification`
- `/home/runner/work/rust_rockfall/rust_rockfall/validation`
- `/home/runner/work/rust_rockfall/rust_rockfall/calibration`
- `/home/runner/work/rust_rockfall/rust_rockfall/hazard`
- `/home/runner/work/rust_rockfall/rust_rockfall/.github/workflows`
- `/home/runner/work/rust_rockfall/rust_rockfall/Cargo.toml`
- `/home/runner/work/rust_rockfall/rust_rockfall/.python-version`
- `/home/runner/work/rust_rockfall/rust_rockfall/requirements-tools.txt`

### Commands run

- `git status -sb` — clean working tree before this review.
- `cargo fmt --check` — passed.
- `cargo clippy --all-targets --all-features -- -D warnings` — passed.
- `cargo test` — passed; Rust test logs showed all suites green.
- `cargo run -- verify --all` — passed.
- `cargo run -- validate --all` — passed.
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` — passed.
- `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` — passed.
- `python3 -m unittest discover -s tests -p 'test_*.py'` — exit code `0`; a direct follow-up summary extraction from that rerun showed `Ran 280 tests in 1.988s`.
- Repository-wide `rg` audits for:
  - `unwrap\(|expect\(|panic!|todo!|unimplemented!|FIXME|TODO|HACK|deprecated|legacy`
  - `NODATA|nodata|NaN|inf|clamp|default|fallback|seed|random|probability|weight|annual|risk`
  - `TODO|FIXME|HACK`

### Commands skipped

- `python3 -m pytest` — skipped as not applicable. No `pyproject.toml`, `pytest.ini`, or pytest-based suite was present, and `rg "pytest"` only found a documentation mention in `docs/autonomous_development_program.md:182`.

## 3. Critical Findings

### Critical 1 — Validation metrics still mask missing/corrupt states with sentinel defaults

**Evidence**

- `src/validation/metric_math.rs:1-27` returns `0.0` for empty inputs in both `mean()` and `percentile()`.
- `src/validation.rs:2450-2453` writes `release_zone_max_runout_m` as `runouts.last().copied().unwrap_or(0.0)`.
- `src/validation.rs:2596-2599` writes `trajectory_shape_max_error_m` as `position_errors.last().copied().unwrap_or_default()`.
- `src/validation.rs:3009-3010` silently parses malformed JSON count maps as empty maps via `serde_json::from_str(text).unwrap_or_default()`.

**Why this matters**

These are review-scope outputs, not transient UI values. A zero metric or empty count map is indistinguishable from a legitimate scientific result once it reaches manifests/reports. That means missing observations, malformed sidecars, or unexpectedly empty result sets can look valid.

**Risk**

- Wrong scientific review conclusions.
- Misleading validation summaries.
- Corrupt stop-state aggregate data being silently accepted.

**Recommendation**

Use explicit `Option<f64>` / `Result` / warning-bearing omission semantics for empty inputs and corrupt JSON sidecars. If schema compatibility forces numeric output, emit an additional explicit validity flag and fail loudly in internal aggregation paths.

### Critical 2 — Runtime-adjacent compatibility paths still panic instead of returning structured errors

**Evidence**

- `src/terrain.rs:543-551` panics on strict DEM `height()` / `normal()` queries.
- `src/terrain.rs:532-539` uses `expect(...)` in clamped DEM convenience methods.
- `src/validation.rs:857-859`, `1341-1355` use `expect(...)` after “validated” assumptions.
- `src/shape.rs:2710-2712` panics on missing simulated trajectories during internal validation comparisons.

**Why this matters**

The repository docs clearly prefer fallible terrain/contact APIs, but these panic paths are still public and still exercised by compatibility code. They create crash-only behavior exactly where the codebase most needs diagnostic clarity: malformed validation inputs, DEM extent mistakes, and internal validation drift.

**Risk**

- Abrupt process termination instead of actionable diagnostics.
- Harder CI/debug sessions when validation fixtures drift.
- Public API surface that remains easier to misuse than the docs imply.

**Recommendation**

Keep compatibility wrappers if needed, but narrow them aggressively: make panic-only helpers `#[cfg(test)]` or private where possible, and convert validation/aggregation `expect`/panic paths into `ValidationError`/`TerrainError` with context.

## 4. High-Priority Findings

### High 1 — `src/validation.rs` is still too large and still mixes too many responsibilities

**Evidence**

- `src/validation.rs:1-8` shows the submodule split exists.
- The file is still ~4,455 lines (`wc -l`).
- The same file still owns metric computation (`src/validation.rs:1716+`), release-zone metrics (`2437+`), observed trajectory comparison (`2463+`), stop-state CSV/manifest writing (`2888+`), terrain-material exposure aggregation (`3133+`), and parameter helpers (`4335+`).

**Why this matters**

The repository has already recognized the need for `metric_math`, `metrics`, `probabilistic`, `runner`, and `validation_io`, but the remaining top-level file is still an architectural bottleneck. It is difficult to review, hard to unit test in isolation, and a likely future merge-conflict hotspot.

### High 2 — `scripts/build_hazard_layers.py` has become a multi-subsystem monolith

**Evidence**

- File length is ~6,942 lines (`wc -l`).
- It owns reducer orchestration (`scripts/build_hazard_layers.py:1063-1211`, `1571+`).
- It owns grid discovery and accumulation (`1758-1781`, `1784+`).
- It owns scenario-table loading and probability metadata parsing (`4439-4478`, `4304+`, `4405+`).
- It owns CSV/Parquet readers (`4661+`, `4708+`).
- It owns GeoTIFF writing (`5350+`) and conditional curve export (`5528+`).
- It owns HTML summary generation (`6792+`).

**Why this matters**

This file now crosses orchestration, parsing, GIS export, reducer-state management, presentation, and hazard semantics. That hurts testability and makes “small safe edits” hard, especially for roadmap-critical hazard-layer work.

### High 3 — Validator scripts duplicate core policy logic across 16 separate files

**Evidence**

- There are `16` top-level `scripts/validate*.py` files.
- Repeated helper definitions show up across many scripts:
  - `validate_claim_boundary(...)` in `scripts/validate_block_release_probability_evidence.py:240`, `validate_source_frequency_evidence.py:190`, `validate_physical_frequency_reducer_preconditions.py:201`, `validate_scalable_conditional_execution.py:190`, and many others.
  - `scan_text_for_misleading_claims(...)` in `scripts/validate_block_release_probability_evidence.py:251`, `validate_source_frequency_evidence.py:201`, `validate_physical_source_frequency_design_gate.py:416`, and others.
  - `require_mapping`, `require_list`, `require_text` are repeated across the same validator set.
- The implementations are materially identical in the reviewed samples (`scripts/validate_block_release_probability_evidence.py:231-299` vs. `scripts/validate_source_frequency_evidence.py:181-243`).

**Why this matters**

This is not cosmetic duplication. These files encode claim boundaries, probability/frequency safety rules, and user-facing schema validation. A bug fix or wording change now needs to be applied in many places and can easily drift.

### High 4 — Python validator tests are tightly coupled to file paths, not module contracts

**Evidence**

- `20` test files use `importlib.util.spec_from_file_location(...)`.
- Example: `tests/test_block_release_probability_evidence.py:12-17`.
- Example: `tests/test_source_frequency_evidence.py:12-17`.

**Why this matters**

The tests exercise “script as file” rather than a stable Python module boundary. That makes reorganization harder, weakens static tooling, and encourages more copy-pasted single-file scripts instead of reusable libraries.

### High 5 — Calibration scripts contain hidden non-empty assumptions and are effectively untested

**Evidence**

- `scripts/run_tschamut_calibration.py:145` uses `fieldnames=list(rows[0])`.
- `scripts/run_tschamut_calibration.py:182`, `364`, `387` access `rows[0]` for “best” candidates.
- `scripts/calibrate_scarring_impact.py:92`, `329`, `370`, `387` do the same.
- `scripts/calibrate_scarring_impact.py:160-177` suppresses both stdout and stderr from `cargo run`, which makes failures harder to diagnose.
- No direct tests were found for `run_tschamut_calibration.py` or `calibrate_scarring_impact.py` under `/home/runner/work/rust_rockfall/rust_rockfall/tests`.

**Why this matters**

A malformed dataset, empty parameter grid, or empty result matrix currently turns into index errors or opaque subprocess failures. These scripts are important research workflows, so they should fail explicitly and reproducibly.

### High 6 — Several scripts contradict the documented Python environment policy

**Evidence**

- Docs say to use `uv` / `.venv` and not rely on system Python:
  - `README.md:63`
  - `docs/onboarding.md:78-113`
- Many scripts still tell the user to install PyYAML with system pip:
  - `scripts/run_performance_benchmark.py:25`
  - `scripts/run_tschamut_calibration.py:51`, `63`
  - `scripts/calibrate_scarring_impact.py:43`, `55`
  - `scripts/check_repo_consistency.py:1204`, `2154`
  - `scripts/download_datasets.py:29`

**Why this matters**

This is a direct docs/code mismatch. The repository guidance is trying to enforce a reproducible Python tool environment, but some scripts still point users toward ad hoc global installs.

### High 7 — Performance CI intentionally collapses multiple failure modes into “baseline unavailable”

**Evidence**

- `scripts/performance_ci_tracking.py:379-386` returns `None` for unreachable URL, timeout, and invalid JSON alike.
- `tests/test_performance_ci_tracking.py:46-65` and `133-141` explicitly lock in that behavior.
- `.github/workflows/performance_main.yml:54-57` falls back to `date -u` for `COMMIT_DATE` when the event payload lacks one.

**Why this matters**

This design prevents hard failures, which is useful, but it also makes corrupted published history, transient network failures, and “no baseline exists yet” look identical. The workflow timestamp fallback also weakens reproducibility for manual runs.

## 5. Medium/Low-Priority Findings

### Medium 1 — `metric_math` deposition-cloud comparison is quadratic

**Evidence**

- `src/validation/metric_math.rs:47-62` computes symmetric nearest-neighbour distance with nested scans.

**Risk**

Fine for today’s fixtures; likely too slow for larger deposition clouds or more ambitious validation sets.

### Medium 2 — Hazard grid bounds discovery stores all coordinates instead of streaming min/max

**Evidence**

- `scripts/build_hazard_layers.py:1765-1766` appends every `x` and `y` into `self.xs` / `self.ys`.
- `scripts/build_hazard_layers.py:1775-1781` only needs min/max at the end.

**Risk**

Avoidable memory growth on larger trajectory or deposition inputs.

### Medium 3 — Stop-state aggregate parsing hides malformed per-row JSON

**Evidence**

- `src/validation.rs:2973-2976` builds summary counts from JSON stored in CSV rows.
- `src/validation.rs:3009-3010` turns parse failure into an empty map.

**Risk**

A single malformed row silently reduces class counts instead of failing summary generation or at least emitting a warning.

### Medium 4 — Extensive `SystemExit` use makes script internals harder to reuse and test

**Evidence**

- `scripts/build_hazard_layers.py:1187-1191`, `4439-4478`, `4661-4674` and many validator scripts use `SystemExit` as ordinary control flow for data validation.

**Risk**

Acceptable for pure CLI boundaries, but the repository already imports these scripts directly in tests and sometimes from other scripts, so `SystemExit` now leaks past the true CLI layer.

### Low 1 — Ambiguous naming remains in a few important places

**Evidence**

- `src/validation.rs:71` — `SIGNIFICANT_IMPACT_TERRAIN_CLASS_SEQUENCE_EDGE_LIMIT` is not self-explanatory.
- `src/validation.rs` still uses `BenchmarkCase` for verification, validation, and benchmarking.

**Risk**

Mostly readability and onboarding cost.

### Low 2 — No active TODO/FIXME/HACK clutter was found

**Evidence**

- Repository-wide `rg "TODO|FIXME|HACK"` over the requested review scope returned no matches.

**Assessment**

This is a strength, not a problem: technical debt is mostly structural, not buried behind stale comments.

## 6. Code Smell Inventory

| File / function / module | Issue type | Evidence | Risk | Recommended fix | Suggested test |
|---|---|---|---|---|---|
| `src/validation/metric_math.rs::mean`, `percentile` | Silent sentinel defaults | `0.0` returned for empty inputs (`1-27`) | Missing data can masquerade as valid metrics | Return `Option<f64>` or force caller-side explicit handling | Unit tests for empty-runout / empty-position-error inputs |
| `src/validation.rs::compute_release_zone_metrics` | Hidden default | `runouts.last().copied().unwrap_or(0.0)` (`2450-2453`) | Empty release-zone results can look like zero runout | Fail or omit the metric explicitly when no runs exist | Validation-case test with empty release zone or no successful runs |
| `src/validation.rs::parse_json_count_map` | Silent corruption masking | `serde_json::from_str(text).unwrap_or_default()` (`3009-3010`) | Malformed stop-state rows silently erase counts | Return `Result` or emit manifest warning/error | Test malformed JSON in stop-state CSV summary path |
| `src/terrain.rs::Terrain for DemGrid` | Panic in public API | `panic!` on out-of-grid / normal failures (`543-551`) | Crash instead of structured error on DEM misuse | Narrow to test-only/private wrappers or return `TerrainError` | Public API test covering strict DEM misuse from a caller outside integrator |
| `src/validation.rs` | Oversized mixed-responsibility module | ~4,455 lines; metrics + IO + manifests + helpers | Hard review, weak isolation, merge conflicts | Move stop-state/exposure/sidecar logic into focused submodules | Split-unit tests per extracted module |
| `scripts/build_hazard_layers.py` | Oversized mixed-responsibility script | ~6,942 lines; reducer + GIS + readers + HTML | High maintenance and regression risk | Split into readers / reducers / exports / probability / report modules | Module-level tests replacing giant end-to-end-only coverage |
| `scripts/validate*.py` | Duplication | Repeated `validate_claim_boundary`, `scan_text_for_misleading_claims`, `require_*` helpers across 16 files | Policy drift and inconsistent fixes | Create shared validator utility module | Shared test suite for common validator helper behavior |
| `tests/test_*validator*.py` | Fragile import style | `spec_from_file_location(...)` in 20 tests | Refactors break tests unnecessarily | Import real modules from a package/module path | Smoke test that package imports succeed after refactor |
| `scripts/run_tschamut_calibration.py`, `scripts/calibrate_scarring_impact.py` | Hidden non-empty assumptions | Multiple `rows[0]` accesses (`145`, `182`, `364`, `387`; `92`, `329`, `370`, `387`) | Empty datasets/grid configs fail opaquely | Validate non-empty inputs/results before indexing | Tests for empty dataset, empty candidate grid, missing columns |
| `scripts/calibrate_scarring_impact.py::simulate_impact` | Debuggability gap | Suppresses `stdout` and `stderr` (`160-177`) | Cargo failures lose actionable context | Preserve stderr or capture/rewrap it in a user-facing error | Failing-subprocess regression test |
| `scripts/performance_ci_tracking.py::read_json_url` | Silent fallback | Any URL/timeout/JSON error returns `None` (`379-386`) | Corrupt baseline indistinguishable from missing baseline | Distinguish “missing”, “network error”, and “invalid JSON” | Tests for malformed HTTPS JSON and timeout classification |
| `src/validation/metric_math.rs::mean_nearest_distance` | Scaling bottleneck | O(N²) nested scan (`51-62`) | Larger cloud comparisons will become slow | Use spatial index or document fixture-size limit | Performance regression test on larger synthetic clouds |

## 7. Duplication And Dead-Code Audit

### Duplication

1. **Validator helper duplication is the main duplication problem in the repo.**  
   The repeated policy helpers across 16 validator scripts are substantial and safety-relevant, not cosmetic.

2. **Calibration workflow utilities are also duplicated.**  
   Both `scripts/run_tschamut_calibration.py` and `scripts/calibrate_scarring_impact.py` duplicate `load_yaml`, `write_yaml`, path resolution, candidate-grid expansion, CSV loading, and “pick best row” logic.

3. **The hazard-layer tests mirror the monolith.**  
   `tests/test_hazard_layers.py` is ~3,987 lines and reflects the same “everything in one place” architecture as `scripts/build_hazard_layers.py`.

### Dead/obsolete code

1. I did **not** find obvious fully-dead Rust modules or abandoned workflow trees in the requested scope.
2. I did find **live legacy compatibility paths** that are still intentionally supported:
   - legacy infallible terrain methods (`src/terrain.rs:6-31`, `543-551`)
   - legacy probability labels (`src/validation.rs:915`, `4023+`; `src/validation/runner.rs:266-273`)
   - legacy stop-state CSV compatibility tests (`tests/config_io_terrain.rs:2373+`)
3. Those paths are documented and still covered by tests, so they are not dead code, but they do expand the correctness surface and should keep a clear deprecation/containment strategy.

## 8. Error-Handling And Runtime-Safety Audit

### Main risks

- **Panic-based failures** remain in terrain compatibility APIs and a few validation helpers.
- **Silent fallbacks** remain in validation metrics and stop-state summary parsing.
- **Broad exception normalization** appears in many validator scripts:
  - e.g. `scripts/validate_source_frequency_evidence.py:218-225`
  - e.g. `scripts/validate_block_release_probability_evidence.py:273-280`
- **CLI-level `SystemExit` escapes into importable functions** in `build_hazard_layers.py` and validator scripts.
- **Calibration scripts assume non-empty tables and result sets** instead of validating them up front.

### Private-data-absent behavior

This area looks better than average:

- `cargo run -- validate --all` passed cleanly.
- No unexpected local-private-data hard failures appeared in the reviewed default suite.
- The repo continues to distinguish optional public-data/runtime workflows from the default validation chain.

## 9. Determinism And Reproducibility Audit

### Strong areas

- Ordered collections are used heavily in validation/reporting (`BTreeMap`, `BTreeSet`; e.g. `src/validation.rs:51`, `758`, `2921+`, `3133+`).
- Numerical sorting uses `f64::total_cmp` consistently in reviewed metric paths (`src/validation.rs:2038-2039`, `2441`, `2587`, `2715`, `2726`, `2737`).
- Seed derivation is explicit and deterministic (`src/stochastic.rs:39+`).
- Local parallel ensemble execution has dedicated determinism tests (seen in `cargo test` output: worker-count/order independence tests all passed).
- Hazard/reducer chunk execution signs inputs/execution policies with hashes (`scripts/build_hazard_layers.py:1286-1412`).

### Remaining reproducibility risks

1. **Performance history timestamps can become “time of manual rerun”, not commit time.**  
   `.github/workflows/performance_main.yml:54-57`.

2. **Baseline/history fetch failures are intentionally collapsed.**  
   `scripts/performance_ci_tracking.py:379-386`. This is deterministic, but it weakens observability and comparison quality.

3. **Silent metric defaults reduce reproducibility of meaning even when bytes are reproducible.**  
   The output may be deterministic but still semantically ambiguous.

## 10. Terrain/GIS/Indexing Audit

### Strong areas

- Terrain API documentation is explicit about fallible vs. legacy infallible methods (`src/terrain.rs:6-31`).
- DEM bottom-origin / cell-center semantics are tested (`cargo test` showed `dem_bilinear_interpolation_uses_bottom_origin`, `dem_grid_center_helpers_match_expected_values`, and related terrain tests passing).
- `GridSpec.cell` / `center` use consistent bottom-origin-to-raster-row transforms (`scripts/build_hazard_layers.py:65-77`).
- Hazard products explicitly keep annualized semantics disabled in the current phase (`scripts/build_hazard_layers.py:107-123`).

### Risks

1. **Strict DEM infallible queries still panic.**  
   `src/terrain.rs:543-551`.

2. **Hazard bounds discovery is memory-inefficient.**  
   `scripts/build_hazard_layers.py:1758-1781` stores every `x/y` before computing min/max.

3. **Stop-state class summaries can silently lose GIS/classification provenance if embedded JSON is malformed.**  
   `src/validation.rs:2973-3010`.

### Hypothesis to watch

I did not find a confirmed raster orientation bug. Current tests around DEM origin and clamped-normal behavior are a good sign. The bigger risk here is failure semantics and memory profile, not obviously incorrect indexing math.

## 11. Hazard/Probability Code Audit

### Strong areas

- Current code is disciplined about not claiming unsupported annual/risk semantics:
  - `scripts/build_hazard_layers.py:107-123`
  - validator scripts enforce `claim_boundary.* == false`
  - tests cover phase-1 annual/probability restrictions (`cargo test` output showed `annual_frequency_mode_is_rejected_in_phase1`, `physical_probability_requires_explicit_probability_columns`, etc.).

### Risks

1. **Probability/frequency claim-boundary logic is duplicated across many scripts.**  
   That increases the chance that one gate drifts from the others.

2. **Scenario/probability CSVs are eagerly loaded into memory.**  
   `scripts/build_hazard_layers.py:4439-4478`.

3. **Legacy probability labels remain in validation metadata.**  
   `src/validation.rs:914-928`, `src/validation/runner.rs:266-277`, `src/validation.rs:4023+`. This is documented, but it means readers still need to reason about both current and compatibility semantics.

## 12. Performance And Scaling Code Audit

### Main structure risks

- `scripts/build_hazard_layers.py` reads individual trajectory files fully into tuples (`4661-4684`) and deposition files into tuples (`4687-4695`).
- `scripts/build_hazard_layers.py` stores all bound-discovery coordinates (`1765-1766`) instead of streaming extents.
- `src/validation/metric_math.rs:51-62` uses quadratic nearest-neighbour scans.
- `scripts/performance_ci_tracking.py:147-154` writes several output files sequentially and non-atomically.
- `scripts/run_tschamut_calibration.py:135-137` and `scripts/calibrate_scarring_impact.py:97-123` eagerly load CSVs into lists.

### Scaling blockers most relevant to roadmap goals

1. Hazard-layer processing is still architecturally centralized in one Python script.
2. Validation aggregation still does some “small-fixture-friendly” math that will not scale gracefully.
3. Calibration workflows are still designed for small explicit grids, which is fine today, but they are not structured for clearer failure reporting or larger controlled sweeps.

## 13. Test Gap Analysis

### Priority 1 — Validation fallback masking

- **Purpose:** Ensure empty/corrupt metric inputs cannot silently become zeros/empty maps.
- **Likely file:** `tests/config_io_terrain.rs` or a new focused `tests/validation_metrics.rs`.
- **Failure mode caught:** corrupt stop-state JSON, empty release-zone runouts, empty trajectory error vectors being silently accepted.
- **Minimal fixture needed:** one malformed stop-state CSV row and one synthetic validation case with no successful runs.

### Priority 2 — Calibration script empty-input failure modes

- **Purpose:** Force explicit user-facing errors for empty datasets / empty candidate grids.
- **Likely file:** new Python tests for `scripts/run_tschamut_calibration.py` and `scripts/calibrate_scarring_impact.py`.
- **Failure mode caught:** `rows[0]` index errors and opaque “best row” failures.
- **Minimal fixture needed:** empty CSV and config with empty parameter grid.

### Priority 3 — Partial observed-velocity handling

- **Purpose:** Decide and lock down whether missing `vx/vy/vz` should error, warn, or use defaults.
- **Likely file:** new Rust validation tests near observed trajectory comparison.
- **Failure mode caught:** hidden initial-condition drift in trajectory validation.
- **Minimal fixture needed:** observed trajectory set with only one missing velocity component.

### Priority 4 — Malformed baseline/history handling in performance tracking

- **Purpose:** Distinguish “missing baseline” from “corrupt published baseline”.
- **Likely file:** `tests/test_performance_ci_tracking.py`.
- **Failure mode caught:** silently treating invalid JSON as absence.
- **Minimal fixture needed:** mocked HTTPS response with malformed JSON.

### Priority 5 — Validator boundary-value tests

- **Purpose:** Cover `1.0 ± tolerance`, zero/negative probabilities, and negative rates explicitly.
- **Likely file:** `tests/test_block_release_probability_evidence.py`, `tests/test_source_frequency_evidence.py`.
- **Failure mode caught:** off-by-tolerance or sign mistakes in future refactors.
- **Minimal fixture needed:** tiny YAML records with one edited numeric field each.

### Priority 6 — Hook behavior tests

- **Purpose:** Verify Python interpreter selection and failure messages in hook helpers.
- **Likely file:** new Python or shell tests around `scripts/git-hooks/python-env.sh`.
- **Failure mode caught:** silent fallback to an unintended interpreter.
- **Minimal fixture needed:** mocked environment variables / PATH stubs.

## 14. Refactoring Recommendations

### 1. Make validation metric emptiness explicit

- **Objective:** Remove silent `0.0` / empty-map masking from validation metrics.
- **Rationale:** Highest direct scientific correctness risk found in this review.
- **Files affected:** `src/validation.rs`, `src/validation/metric_math.rs`, related tests.
- **Behavior-preservation strategy:** Preserve output schema where necessary, but separate “metric missing/invalid” from numeric zero via explicit flags/warnings/errors.
- **Tests required:** empty input vectors, malformed stop-state JSON, no-run release-zone case.
- **Risk level:** Medium.

### 2. Replace panic/`expect` usage in validation/runtime-adjacent paths

- **Objective:** Convert crash-only compatibility paths into structured failures where feasible.
- **Rationale:** Better diagnostics and safer misuse boundaries.
- **Files affected:** `src/terrain.rs`, `src/validation.rs`, `src/shape.rs`.
- **Behavior-preservation strategy:** Keep public contracts stable; only change failure transport from panic to typed error where runtime already returns `Result`.
- **Tests required:** strict DEM misuse, missing internal validation trajectory, invalid passive shape metadata.
- **Risk level:** Medium.

### 3. Finish the `validation` module split

- **Objective:** Move sidecar writing, stop-state summary logic, and terrain-material exposure aggregation out of `src/validation.rs`.
- **Rationale:** The current top-level file is still too large to review or maintain safely.
- **Files affected:** `src/validation.rs`, `src/validation/validation_io.rs`, possibly new submodules.
- **Behavior-preservation strategy:** Refactor only; keep schemas, filenames, and metrics unchanged.
- **Tests required:** regression suite for existing CSV/manifest outputs.
- **Risk level:** Low-Medium.

### 4. Break `build_hazard_layers.py` into importable subsystems

- **Objective:** Separate readers, reducers, probability/map-package logic, raster export, and reporting.
- **Rationale:** Current file size and responsibility spread are now the dominant Python maintainability risk.
- **Files affected:** `scripts/build_hazard_layers.py`, `tests/test_hazard_layers.py`, possibly new modules under `scripts/`.
- **Behavior-preservation strategy:** Keep CLI flags, manifest schema, and output filenames unchanged.
- **Tests required:** keep existing smoke/fixture coverage; add module-level reader/export tests.
- **Risk level:** Medium.

### 5. Create a shared validator utility module

- **Objective:** Deduplicate `require_*`, claim-boundary checks, misleading-text scans, and YAML loading.
- **Rationale:** Reduces policy drift across 16 validator scripts.
- **Files affected:** validator scripts under `scripts/validate*.py`, related tests.
- **Behavior-preservation strategy:** Re-export old entry points; do not change CLI behavior.
- **Tests required:** shared helper tests plus spot checks that each validator still returns the same messages.
- **Risk level:** Low-Medium.

### 6. Turn validator tests into module-import tests

- **Objective:** Stop using `spec_from_file_location(...)` as the normal import mechanism.
- **Rationale:** Improves refactor safety and makes packaging boundaries clearer.
- **Files affected:** ~20 Python tests.
- **Behavior-preservation strategy:** Keep CLI smoke coverage separately if desired; change only import style.
- **Tests required:** package/module import smoke tests.
- **Risk level:** Low.

### 7. Harden calibration scripts for empty/malformed inputs

- **Objective:** Replace implicit indexing assumptions with validated preconditions and clearer errors.
- **Rationale:** These are reproducibility-critical research workflows and currently fail opaquely on empty inputs.
- **Files affected:** `scripts/run_tschamut_calibration.py`, `scripts/calibrate_scarring_impact.py`.
- **Behavior-preservation strategy:** Preserve nominal results; only improve failure handling and diagnostics.
- **Tests required:** empty CSV, empty candidate grid, failing subprocess diagnostics.
- **Risk level:** Low-Medium.

### 8. Align Python dependency messaging with documented `uv` workflow

- **Objective:** Make all user-facing dependency errors recommend `.venv` / `uv`, not global pip.
- **Rationale:** Removes a direct docs/code contradiction.
- **Files affected:** multiple scripts currently emitting `python3 -m pip install PyYAML`.
- **Behavior-preservation strategy:** Message-only change.
- **Tests required:** targeted message assertions in existing Python tests where practical.
- **Risk level:** Low.

### 9. Make performance baseline/history failures observable

- **Objective:** Preserve the “don’t fail the workflow” behavior while distinguishing missing baseline vs. corrupt baseline vs. network error.
- **Rationale:** Improves reproducibility review without destabilizing CI.
- **Files affected:** `scripts/performance_ci_tracking.py`, `.github/workflows/performance_main.yml`, tests.
- **Behavior-preservation strategy:** Keep output schema compatible; add status fields instead of removing `baseline_available`.
- **Tests required:** mocked invalid JSON and timeout cases.
- **Risk level:** Low.

## 15. Recommended Next Development Prompt

> Fix the highest-priority reliability issue in `src/validation.rs` and `src/validation/metric_math.rs`: remove silent fallback behavior that turns empty or corrupt validation data into `0.0` or empty maps. Keep output schemas stable where possible, but make empty metric inputs and malformed stop-state JSON explicit through typed errors, omitted metrics, or warning/validity fields. Add focused regression tests for empty runout vectors, empty position-error vectors, and malformed JSON in stop-state summary rows.
