# AGENTS.md

## Role

This file is the operating guide for automated agents working in this repository. It is intentionally procedural; scientific background, model scope, implementation phases, and validation detail live in `docs/`.

Use this document to decide how to work. Use the docs to decide what to build.

## Source of Truth

- Project overview and quickstart: `README.md`
- Local prerequisites, installation, hooks, and onboarding checks: `docs/onboarding.md`
- Literature and background inventory: `docs/literature_review.md`
- Current equations, assumptions, and APIs: `docs/model_design.md`
- Phase ordering and future work: `docs/implementation_plan.md`
- Long-term hazard-mapping roadmap: `docs/roadmap_hazard_mapping.md`
- Scalability and output-format roadmap: `docs/scalability_and_data_formats_review.md`
- Dataset roles and validation boundaries: `docs/dataset_strategy.md`
- Required validation approach: `docs/validation_plan.md`
- Source material: `background/`

When these files conflict, preserve the safety constraints first, then update the docs so the repository tells one consistent story.

## Agent Workflow

- Inspect the relevant docs and code before changing behavior.
- Keep changes aligned with the current implementation phase unless the user explicitly asks to advance the phase.
- Make the smallest coherent change that improves the simulator, tests, or documentation.
- Add or update focused tests for every feature, behavior branch, physical model, parser, and output format change.
- Document any new equation, parameter, assumption, or limitation in the appropriate `docs/` file.
- For contact-model changes, update the Rust config types, benchmark YAML schema, validation parser, docs, verification cases, and consistency checks in the same change.
- For roughness-model changes, update the Rust config types, benchmark YAML schema, validation parser, docs, verification cases, visualization/reporting notes, and consistency checks in the same change.
- For soil/scarring-model changes, update the Rust config types, benchmark YAML schema, validation parser, docs, verification cases, visualization/reporting notes, and consistency checks in the same change.
- For dataset or validation-case changes, update `data/datasets.yaml`, preprocessing scripts, validation-ready schema/docs, and `docs/dataset_strategy.md` together so calibration, trajectory validation, deposition validation, and hazard mapping stay separated.
- For Swiss operational geodata changes, keep validation datasets and operational input datasets separate, update `docs/swisstopo_data_strategy.md`, preserve CRS/vertical-datum/provenance metadata, and never commit large swisstopo raw tiles.
- Keep seeded runs deterministic.
- Leave generated trajectory outputs out of git unless they are intentional fixtures.
- Keep generated hazard-layer products under `hazard/results/` and out of git unless they are intentional tiny fixtures.
- If local git hooks are not installed, install them with `scripts/install_git_hooks.sh` unless the user explicitly asks not to.

## Hard Boundaries

- Do not reverse-engineer binaries or proprietary tools.
- Do not copy protected implementation details.
- Do not claim equivalence with RAMMS::ROCKFALL or any proprietary model.
- Do not introduce undocumented physics or hidden parameter choices.
- Do not present this project as validated for operational hazard assessment.
- Do not describe hazard-map layers as risk maps unless exposure and vulnerability data are explicitly included.

## Long-Term Direction

- The long-term target is automated, reproducible rockfall hazard mapping for Switzerland's Alpine terrain from public geodata, primarily swisstopo.
- The first concrete milestone is a valley-scale pilot that demonstrates the full workflow from pragmatic release-zone and block-scenario generation through large trajectory ensembles to GIS-ready hazard outputs.
- Choose development priorities by importance to that national hazard-map goal. Close the largest scientific, workflow, performance, or reproducibility gaps first instead of adding features by convenience.
- Keep trajectory, impact, calibration, validation, release-zone, ensemble, and hazard-layer work aligned with future spatial hazard outputs.
- Future hazard outputs should be designed first around current conditional intensity-exceedance and diagnostic layers, and later around pixel-scale physical-probability or annual intensity-frequency information once source-frequency semantics are mature. Supporting layers include runout probability, deposition density, maximum kinetic energy, maximum jump height, significant-impact density, scenario uncertainty, and convergence diagnostics.
- Treat uncertainty estimation as a primary design constraint. It can be represented through scenario sampling, stochastic trajectory terms, sensitivity analysis, convergence summaries, or explicit probability models, but uncertainty provenance must remain visible.
- Release-zone generation and block location/size/shape/probability policies should be pragmatic and literature-informed. Prefer simple reproducible workflows when release-zone and block-probability uncertainty dominates over fine-grained physics detail.
- Performance and HPC readiness are core design targets. The code should support efficient single-socket execution, local parallelism, reproducible chunked ensembles, and a path to CSCS/SLURM orchestration; roughly 10,000 trajectories per release zone should be feasible where scientifically appropriate.
- Keep risk modelling separate from hazard modelling. Exposure, vulnerability, consequence modelling, and operational warning systems are out of scope unless a future phase explicitly introduces them.
- Treat hazard-layer generation as post-processing of simulation outputs, not core physics; document whether a layer comes from full trajectory ensembles, representative trajectories, deposition summaries, impact-event logs, or weighted scenario tables.
- Treat swisstopo datasets as operational input geodata for future Swiss pilot and hazard-map workflows, not as model-validation evidence by themselves.
- Preserve CRS, vertical datum, resolution, extent, source-tile ids, and provenance for all geospatial outputs.
- Treat CSV/JSON/ASCII/GeoJSON/PNG/HTML outputs as debug and small-review formats unless a document explicitly defines a production-scale use; prefer manifest-backed chunking, columnar trajectory/event storage, deterministic reducers, and CRS-aware raster exports for future large workflows.
- Do not commit large swissALTI3D, swissSURFACE3D, SWISSIMAGE, swissTLM3D, or swissBUILDINGS3D raw products; use metadata records and small intentional fixtures only.

## Code Expectations

- Use idiomatic Rust with explicit units in field and variable names where practical.
- Keep public APIs small and behavior-oriented.
- Keep modules focused; follow the existing `src/` module boundaries instead of creating broad utility modules.
- For real DEM, validation, or pilot runtime paths, use fallible terrain and
  integrator APIs (`try_height`, `try_normal`, `try_simulate_fixed_step*`) and
  propagate structured errors. Treat infallible `height`/`normal` and
  `simulate_fixed_step*` wrappers as compatibility helpers for analytic tests
  and simple callers only.
- Prefer structured parsers and serializers over ad hoc text handling.
- Prefer clear numerical code over premature optimization.

Before handoff, run these when a Rust toolchain is available:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
cargo run -- verify --all
cargo run -- validate --all
python3 scripts/check_repo_consistency.py
```

Repository Python scripts should normally run through the project-local `uv`
environment described in `docs/onboarding.md`. If direct `python3` uses an
older or incompatible system interpreter, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py
```

and record that substitution in the final response or commit notes.

If the toolchain is unavailable, state that clearly and still validate any changed JSON/TOML/Markdown with available local tools.

## HPC-Readiness Constraints

- Keep the single-trajectory kernel deterministic, stateless, and free of file I/O.
- Keep randomness explicit; derive ensemble seeds from global seed, case ID, and trajectory ID.
- Keep computation, orchestration, and output writing separate.
- Preserve reproducibility independent of trajectory execution order.
- Prioritize single-socket throughput and local parallel trajectory execution before cluster orchestration.
- Design outputs so summaries can be aggregated without requiring full trajectories to stay in memory.
- For large-ensemble or hazard-layer work, design run manifests, chunk identifiers, output row counts, checksums, deterministic reducer merge rules, and resume semantics before adding new execution frameworks.
- CSCS/SLURM orchestration is in scope for the hazard-map goal, but should follow stable local chunk/reducer contracts. Do not add MPI, GPU, or heavy distributed frameworks without an explicit phase change.

## Versioning Rules

- Use semantic versioning: `MAJOR.MINOR.PATCH`.
- Any new opt-in physics feature requires a `MINOR` bump.
- Any default physics change, output-breaking change, or silent numerical behavior change requires a justified `MAJOR` bump.
- Bug fixes that change numerical results may be `PATCH` only when the previous behavior was clearly incorrect and a regression test documents it.
- Update `Cargo.toml`, `README.md`, `docs/README.md`, `CHANGELOG.md`, schemas, and reports when versioned behavior changes.
- No silent behavior changes are allowed; preserve old defaults unless a versioned breaking change explicitly says otherwise.

## Commit and Push Discipline

Before committing:

- Run the full local test chain:

  ```bash
  cargo fmt --check \
    && cargo clippy --all-targets --all-features -- -D warnings \
    && cargo test \
    && cargo run -- verify --all \
    && cargo run -- validate --all \
    && python3 -m unittest discover -s tests -p 'test_*.py' \
    && python3 scripts/check_repo_consistency.py
  ```

  If system `python3` is incompatible, run the Python unittest and consistency
  checks through the project-local `uv` environment and record the exact
  command used.

- Do a quick consistency pass:
  - inspect `git status -sb`;
  - confirm generated outputs under `verification/results/`, `validation/results/`, `target/`, and downloaded raw data are not staged;
  - scan changed docs and CLI examples for stale command names or paths;
  - confirm new or changed features are covered by focused tests and listed in the relevant V&V docs when applicable.

Before pushing:

- Re-run the full local test chain, or run `scripts/git-hooks/pre-push` directly.
- Do a more thorough consistency pass:
  - review the staged or committed diff with `git show --stat --oneline HEAD` and targeted `git show` sections;
  - verify `README.md`, `AGENTS.md`, and relevant files in `docs/` agree on scope, commands, limitations, and validation status;
  - verify public dataset metadata includes source, DOI or URL, license, local path, and download/preprocessing status;
  - verify no proprietary data, large raw downloads, generated result reports, or unrelated local files are included;
  - verify CLI commands in docs still match the implemented subcommands;
  - verify all optional real-world validation cases skip gracefully when data are absent.

If a check is intentionally skipped, record the exact reason in the final response or commit notes.

## Test Coverage Expectations

- Every feature must have isolated tests that exercise its expected behavior directly.
- Every physics change must include analytic or conservation-style tests where possible.
- Every stochastic change must include fixed-seed reproducibility tests.
- Every parser, serializer, and CLI-facing change must include success and failure cases.
- Every bug fix must add a regression test that fails without the fix.
- Integration tests must cover representative end-to-end trajectories across supported terrain and contact modes.
- Maintain a comprehensive test suite that aims for exhaustive coverage of public APIs, edge cases, and failure paths.
- Do not remove or weaken tests unless the behavior contract is intentionally changed and documented.
- If exhaustive coverage is not feasible for a change, document the specific gap, why it remains, and what test should close it later.

## Review Checklist

- Does the change preserve the independent, literature-based framing?
- Are new assumptions explicit?
- Is each new feature tested individually?
- Does the comprehensive test suite still cover public APIs, edge cases, and failure paths?
- Are energy, contact, parser, output, and stochastic behavior changes tested?
- Are fixed-seed results deterministic?
- Are docs updated without duplicating material better owned by another doc?
- Are limitations still visible to future users and agents?
