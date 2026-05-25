# Agent Reference

Detailed reference for broad implementation work. The root `AGENTS.md` is the
compact worker fast path; read this file only when a task changes broad model,
physics, output, versioning, HPC, or review policy.

---

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

Before handoff, run the focused checks named by the task. Use
`PYENV_VERSION=system uv run python ...` for repository Python helpers and avoid
plain `python`/`python3`, which can resolve through unavailable local shims.
Broader Rust or Python suites are appropriate for broad runtime changes, but
they are not a substitute for the task-specific checks in `docs/task_backlog.md`.
If a required toolchain is unavailable, state that clearly and still validate
changed JSON/TOML/Markdown with available local tools.

## HPC-Readiness Constraints

- Keep the single-trajectory kernel deterministic, stateless, and free of file I/O.
- Keep randomness explicit; derive ensemble seeds from global seed, case ID, and trajectory ID.
- Keep computation, orchestration, and output writing separate.
- Preserve reproducibility independent of trajectory execution order.
- Prioritize single-socket throughput and local parallel trajectory execution before cluster orchestration.
- Design outputs so summaries can be aggregated without requiring full trajectories to stay in memory.
- For large-ensemble or hazard-layer work, design run manifests, chunk identifiers, output row counts, checksums, deterministic reducer merge rules, and resume semantics before adding new execution frameworks.
- CSCS/SLURM orchestration is in scope for the hazard-map goal. Prefer simple
  chunk/reducer contracts before introducing MPI, GPU, or heavier distributed
  frameworks.
- The current measured Balfrin path is single-node SLURM execution with
  rebuildable reduced outputs. The user has granted standing clearance for
  GPT-5.5 workers to submit and actively monitor jobs on Balfrin's `postproc`
  partition, including multiple concurrent jobs and filling that partition. If
  the work would keep `postproc` fully busy for more than 6 hours, rediscuss
  before continuing.
- For `postproc` runs, keep the workflow practical: use a current checkout,
  reviewed package inputs, active monitoring, `$SCRATCH` run roots, and
  post-run collection so results can be replayed and compared. Treat
  non-`postproc`, distributed, and Swiss-wide work as explicit phase changes.

## Versioning Rules

- Use semantic versioning: `MAJOR.MINOR.PATCH`.
- Any new opt-in physics feature requires a `MINOR` bump.
- Any default physics change, output-breaking change, or silent numerical behavior change requires a justified `MAJOR` bump.
- Bug fixes that change numerical results may be `PATCH` only when the previous behavior was clearly incorrect and a regression test documents it.
- Update `Cargo.toml`, `README.md`, `docs/README.md`, `CHANGELOG.md`, schemas, and reports when versioned behavior changes.
- No silent behavior changes are allowed; preserve old defaults unless a versioned breaking change explicitly says otherwise.

## Commit and Push Discipline

Before committing:

- Run the focused task checks, `git diff --check`, and
  `scripts/git-hooks/pre-commit`.
- Inspect `git status --short --branch`.
- Confirm generated outputs under `verification/results/`,
  `validation/results/`, `hazard/results/`, `target/`, and downloaded raw data
  are not staged.
- Add focused tests for changed behavior. Update validation docs only when the
  change affects validation meaning or user-facing interpretation.

Before pushing, check the diff, confirm generated or downloaded artifacts are
not included, and make sure public commands/docs still match the code when the
task touched them.

If a check is intentionally skipped, record the exact reason in the final response or commit notes.

## Task Outcome Discipline

For execution and measurement tasks, be direct about whether a run happened. If
it did not, choose the next task that makes the run easier or more informative.

For backlog and guidance work, avoid process artifacts as first-class progress.
Prefer capability-first tasks: release/scenario/AOI automation,
restartability, runtime/output scaling, reducer-pressure measurement,
real-input staging, uncertainty interpretation, physical-evidence acquisition,
or simplification of the Python orchestration shell.

## Test Coverage Expectations

- Every feature must have isolated tests that exercise its expected behavior directly.
- Every physics change must include analytic or conservation-style tests where possible.
- Every stochastic change must include fixed-seed reproducibility tests.
- Every parser, serializer, and CLI-facing change must include success and failure cases.
- Every bug fix must add a regression test that fails without the fix.
- Integration tests must cover representative end-to-end trajectories across supported terrain and contact modes.
- Keep tests focused on behavior that matters. Do not remove useful regression
  coverage unless the behavior intentionally changed.

## Review Checklist

- Does the change preserve the independent, literature-based framing?
- Are new assumptions explicit?
- Is each new feature tested individually?
- Does the comprehensive test suite still cover public APIs, edge cases, and failure paths?
- Are energy, contact, parser, output, and stochastic behavior changes tested?
- Are fixed-seed results deterministic?
- Are docs updated without duplicating material better owned by another doc?
- Are limitations still visible to future users and agents?
