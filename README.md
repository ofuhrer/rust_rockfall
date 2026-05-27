# rust_rockfall

`rust_rockfall` is an open, reproducible rockfall simulation and hazard-mapping
toolkit for Alpine terrain.

Current crate/model version: `v0.6.1`.

The project turns public geodata, terrain models, release-zone definitions, and
ensemble trajectory simulations into reviewable hazard-map products. It is built
around a Rust simulation core, Python workflow tools, and explicit provenance so
that model runs can be inspected, repeated, scaled, and improved without relying
on opaque processing steps.

The long-term goal is straightforward: make scientifically traceable rockfall
hazard modelling easier to run, easier to review, and easier to extend for real
Swiss terrain.

## Current Demonstration Snapshot

The repository now has a working end-to-end research workflow: local smoke runs,
AOI preparation, deterministic validation fixtures, GIS-oriented hazard outputs,
and a Balfrin path for bounded scaling experiments.

The strongest current performance evidence is diagnostic, not operational:

- Balfrin `postproc` diagnostic reducer-pressure runs are measured through
  `100` release zones. The largest run completed as job `4372447` with
  `34.16 MB` maximum RSS, `0:01.26` `/usr/bin/time` elapsed time, `304` output
  files, `121,172` output bytes, `61,119` manifest bytes, and `448,376`
  run-root bytes.
- The current bounded Balfrin hazard-throughput support run completed as job
  `4372656` with `6.93 s` workflow wall time, `379.1 MB` peak process memory,
  `57` hazard output files, and `31.4 MB` of hazard output. TB-603 remains the
  comparison baseline, but TB-619 is the current hazard-throughput anchor.
- The current larger-output GIS package stress path is COG-ready for the
  largest package-capable checked-in output: TB-631 packaged `39` files with
  `22` rasters, converted all `22` rasters, and preserved layer parity.
- The scientific evidence base has improved: source-frequency design-review
  evidence and a Chant Sura held-out runout-axis benchmark intake are staged.
  The current physical-probability readiness check now fails on calibration
  evidence; release-probability, block-population, source-frequency, and
  holdout evidence are staged as reviewable design evidence.

What this means: the code path is feasible for bounded Swiss-terrain
experiments on Balfrin, and the output footprint is small enough to keep
iterating. Swiss-wide execution, distributed execution, non-`postproc`
execution, physical-probability products, and operational hazard maps still need
separate evidence before they should be claimed.

## What This Project Provides

- A Rust rockfall simulation engine with deterministic test cases and validation
  hooks.
- Tools for preparing terrain, release-zone, scenario, and hazard-map workflows
  from public geodata.
- Ensemble and probabilistic workflow building blocks for conditional hazard
  layers.
- GIS-oriented outputs, map-package manifests, and review surfaces.
- Reproducible local and CI checks for model logic, workflow helpers, and
  repository consistency.
- A local-first workflow that can hand advanced scaling experiments to a
  separate HPC runbook when needed.

This repository is research and engineering software. It is not an official
hazard product, regulatory map, warning system, or risk/exposure/vulnerability
model.

## Quick Start

Install Rust, `cargo`, `rustfmt`, `clippy`, and `uv`. See
[`docs/onboarding.md`](docs/onboarding.md) for setup details.

Run the smallest smoke example:

```bash
cargo run -- run --config examples/inclined_plane.json --output /tmp/rust_rockfall_minimal_smoke.csv
head -5 /tmp/rust_rockfall_minimal_smoke.csv
```

This writes a deterministic trajectory CSV with columns for time, position,
velocity, energy diagnostics, and contact state. The example uses only
[`examples/inclined_plane.json`](examples/inclined_plane.json) and does not
download data.

Run a tiny validation-to-hazard smoke:

```bash
PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py run-local-smoke \
  --smoke-output-root /tmp/rust_rockfall_micro_validation_smoke \
  --format json
```

This uses the tracked `probabilistic_phase1_smoke` fixture, writes outputs
under `/tmp`, and verifies that at least one trajectory artifact and one hazard
layer were produced. It is a reproducibility smoke, not a scientific validation
claim.

Run the main local checks:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci
```

## CI Performance

[![Main performance trend](https://ofuhrer.github.io/rust_rockfall/performance/main_performance.svg)](https://ofuhrer.github.io/rust_rockfall/performance/)

The main-branch performance workflow publishes the latest synthetic benchmark
baseline and trend dashboard to
[`ofuhrer.github.io/rust_rockfall/performance/`](https://ofuhrer.github.io/rust_rockfall/performance/).
The page also includes Balfrin diagnostic-performance material. CI timings and
Balfrin scheduler evidence are kept separate; neither is a scientific
validation metric.

For focused debugging, run individual checks directly:

```bash
cargo test
cargo run -- verify --all
cargo run -- validate --all
```

## Working With AOIs

For area-of-interest workflows, start with the user manual:

[`docs/aoi_user_manual.md`](docs/aoi_user_manual.md)

It is the compact entry point for preparing an AOI, checking required public
inputs, producing reviewable map packages, and understanding the next command in
the workflow.

## Public Command Surface

Most files under `scripts/` are internal helpers used by tests, diagnostics, or
the AOI front door. New users should start with this smaller command surface:

- `cargo run -- run --config ... --output ...` for one simulation.
- `cargo test`, `cargo run -- verify --all`, and `cargo run -- validate --all`
  for Rust model checks.
- `PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci` for
  the local CI-equivalent check path.
- `PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py ...`
  for AOI status, preparation, candidate review, local smoke runs, and map
  packaging readiness.
- `PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run`
  for one bounded Balfrin `postproc` diagnostic run with prepare, submit,
  monitor, collect, and one run record under `$SCRATCH`.
- `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py`
  for portable pilot command plans without executing them.

Specialist scripts remain available for developers and agents, but they should
normally be reached through these commands or through a documented workflow.

## Advanced Scaling

The first path through the repository is local. Balfrin/HPC work is an advanced
scaling topic for already-prepared experiments. The public diagnostic path is
one runner: inspect the plan, then run it on Balfrin. Start small when changing
the workflow; use the 100-zone result as an evidence ceiling, not a default
development command.

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py plan \
  --release-zones 24 \
  --manifest-mode compact \
  --format text
```

When the plan points at the intended `$SCRATCH` run root, execute:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 24 \
  --manifest-mode compact \
  --format text
```

This writes a single `run_record.json` under the selected `$SCRATCH` run root.
The current reviewer-facing Balfrin evidence package is
[`docs/balfrin_scale_demonstration_management_package.md`](docs/balfrin_scale_demonstration_management_package.md).
It records the measured diagnostic series, bounded hazard-throughput support
point, reproduction commands, run roots, and boundaries. These are performance
and feasibility results, not operational or physical-probability claims. The
older Balfrin handoff, preflight, submit, and collect scripts remain
compatibility and forensic helpers; routine diagnostic runs should use the
single runner above. Larger hazard-throughput runs beyond the current TB-619
support point need a real >4-zone hazard package profile before submission; do
not use the historical package helpers as a shortcut around that profile.

## Development Workflow

Use the repository CI runner when changing code. This is the first-line local
verification path and mirrors the GitHub Actions suite layout:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci
```

For focused debugging, the same runner exposes narrower suites. The
clean-checkout Python suite used by GitHub Actions is:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite python
```

The full local Python suite is useful on machines that also have
local/generated artifacts:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite python-full
```

The Python test tiers are tracked in
[`tests/python_test_tiers.toml`](tests/python_test_tiers.toml), so new test
modules must be classified deliberately.

## Start Here

- [`docs/onboarding.md`](docs/onboarding.md) - set up a fresh checkout.
- [`docs/aoi_user_manual.md`](docs/aoi_user_manual.md) - run the AOI workflow
  front door.
- [`docs/project_overview.md`](docs/project_overview.md) - understand the model,
  workflow, and deeper documentation map.
- [`docs/swiss_scale_feasibility_projection.md`](docs/swiss_scale_feasibility_projection.md) -
  review the current Balfrin and Swiss-scale feasibility evidence.
- [`docs/current_maturity_snapshot.md`](docs/current_maturity_snapshot.md) -
  read current capability and claim boundaries.
- [`AGENTS.md`](AGENTS.md) - find the active backlog, orchestration strategy,
  and agent operating rules.

## Local Git Hooks

Install the lightweight pre-commit hook with:

```bash
scripts/install_git_hooks.sh
```

The hook runs `cargo fmt --check` and YAML syntax checks. GitHub Actions remains
the source of truth for full regression coverage.
