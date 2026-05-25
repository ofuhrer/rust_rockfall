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
- A documented path for scaling from local development to larger HPC-backed
  experiments.

This repository is research and engineering software. It is not an official
hazard product, regulatory map, warning system, or risk/exposure/vulnerability
model.

## Quick Start

Install Rust, `cargo`, `rustfmt`, `clippy`, and `uv`. See
[`docs/onboarding.md`](docs/onboarding.md) for setup details.

Run the main local checks:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci
```

Run the Rust tests directly:

```bash
cargo test
```

Run a small example simulation:

```bash
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
```

Verify benchmark and validation cases:

```bash
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
- `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py`
  for portable pilot command plans without executing them.

Specialist scripts remain available for developers and agents, but they should
normally be reached through these commands or through a documented workflow.

## Development Workflow

Use the repository CI runner when changing code:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci
```

For the clean-checkout Python suite used by GitHub Actions:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite python
```

For the full local Python suite on machines that also have local/generated
artifacts:

```bash
PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite python-full
```

The Python test tiers are tracked in
[`tests/python_test_tiers.toml`](tests/python_test_tiers.toml), so new test
modules must be classified deliberately.

## Documentation Map

- [`docs/project_overview.md`](docs/project_overview.md) - detailed model and
  workflow background.
- [`docs/onboarding.md`](docs/onboarding.md) - local setup.
- [`docs/aoi_user_manual.md`](docs/aoi_user_manual.md) - AOI workflow front
  door.
- [`docs/hazard_layers.md`](docs/hazard_layers.md) - hazard-layer outputs and
  semantics.
- [`docs/model_design.md`](docs/model_design.md) - model architecture.
- [`docs/validation_maturity_framework.md`](docs/validation_maturity_framework.md)
  - validation levels and claim boundaries.
- [`docs/swisstopo_data_strategy.md`](docs/swisstopo_data_strategy.md) - public
  geodata strategy.
- [`docs/current_maturity_snapshot.md`](docs/current_maturity_snapshot.md) -
  current project maturity snapshot.
- [`docs/task_backlog.md`](docs/task_backlog.md) - active implementation queue.
- [`AGENTS.md`](AGENTS.md) - compact guide for automated coding agents.

## Local Git Hooks

Install the lightweight pre-commit hook with:

```bash
scripts/install_git_hooks.sh
```

The hook runs `cargo fmt --check` and YAML syntax checks. GitHub Actions remains
the source of truth for full regression coverage.
