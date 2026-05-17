# rust_rockfall

`rust_rockfall` is an independent, open implementation for scalable rockfall
trajectory simulation and hazard-map generation for Switzerland's Alpine
terrain from public geodata, primarily swisstopo.

Current crate/model version: `v0.6.1`.

## Current Status

The repository currently supports a reproducible, non-operational conditional
diagnostic workflow with measured Tschamut same-scale evidence and a measured
Balfrin single-release-zone demonstration. The current Balfrin path includes a
frozen demonstration contract, SLURM execution evidence, a live
interruption/resume proof, a canonical evidence bundle, replay smoke checks,
rebuildable reduced outputs, GIS/COG scope reporting, and AOI-to-command-plan
dry-run composition.

Swiss-wide automation is still emerging. The repo now has deterministic
dry-run helpers for AOI product discovery, public-geodata cache verification,
AOI terrain preprocessing from staged tiles, terrain-driven release-zone
candidate stability checks, generic candidate-source-zone scenario generation,
second-site acquisition planning, and site-level case-skeleton handoff. It
does not yet download all public inputs, run arbitrary AOIs, execute
second-site ensembles, or generate physically annualized intensity-frequency
products.

Current products are diagnostic or sampling-weighted conditional hazard layers.
They are not annualized, not risk maps, and not operational Swiss hazard
products. Scientific closure remains inconclusive and physical credibility is
not established. Risk, exposure, vulnerability, warning, and regulatory
semantics are out of scope.

## Quickstart

Prerequisites are Rust with `cargo`, `rustfmt`, and `clippy`, plus the
project-local `uv` Python environment. See `docs/onboarding.md` for setup.

```bash
cargo test
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
cargo run -- verify --all
cargo run -- validate --all
PYENV_VERSION=system uv run python scripts/check_repo_consistency.py
```

For active implementation work, use `docs/task_backlog.md` and the compact task
context helper:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
```

## Key Documentation

- `docs/project_overview.md` - detailed model, validation, GIS, and workflow background.
- `AGENTS.md` - compact worker fast path for automated agents.
- `docs/agent_reference.md` - detailed agent policy for broad changes.
- `docs/task_backlog.md` - authoritative active TB task queue.
- `docs/current_maturity_snapshot.md` - current project maturity and capability gaps.
- `docs/decision_log.md` - durable decisions.
- `docs/agent_work_log.md` - chronological completed TB history.
- `docs/swisstopo_data_strategy.md` - public geodata strategy and boundaries.
- `docs/validation_maturity_framework.md` - claim levels and validation maturity.

## Local Git Hooks

Install the lightweight pre-commit hook with:

```bash
scripts/install_git_hooks.sh
```

The hook runs `cargo fmt --check` and YAML syntax checks. There is no repository
pre-push hook; run task-specific tests and repository consistency checks before
committing or pushing. CI remains the source of truth for full regression
coverage.
