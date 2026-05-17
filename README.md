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
rebuildable reduced outputs, GIS/COG scope reporting, a metrics-remediation
checklist, AOI-to-command-plan dry-run composition, and one explicitly
authorized target-area probe. That bounded target-area probe completed on
Balfrin as SLURM job `4329024` under
`/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`.
It provides measured runtime/output evidence for the frozen target-area
contract, while peak-memory and split validation/hazard output metrics remain
incomplete. No further Balfrin execution is authorized by default.

Swiss-wide automation is still emerging. The repo now has deterministic
dry-run helpers for AOI product discovery, public-geodata cache verification,
AOI terrain preprocessing from staged tiles, terrain-driven release-zone
candidate stability checks, generic candidate-source-zone scenario generation,
second-site acquisition planning, site-level case-skeleton handoff, and
planning-only GIS scope summaries. It does not yet download all public inputs,
run arbitrary AOIs, execute second-site ensembles, produce hazard layers from
AOI handoff bundles, or generate physically annualized intensity-frequency
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

If the helper reports `backlog_refill_needed`, do a scoped gap-analysis and
backlog-refill pass before launching implementation workers.

## Key Documentation

- `docs/project_overview.md` - detailed model, validation, GIS, and workflow background.
- `AGENTS.md` - compact worker fast path for automated agents.
- `docs/agent_reference.md` - detailed agent policy for broad changes.
- `docs/task_backlog.md` - authoritative active TB task queue.
- `docs/current_maturity_snapshot.md` - current project maturity and capability gaps.
- `docs/balfrin_probe_slurm_driver.md` - SLURM-first Balfrin execution flow.
- `docs/balfrin_single_job_execution_sufficiency.md` - measured Balfrin runtime/output evidence.
- `docs/decision_log.md` - durable decisions.
- `docs/agent_work_log.md` - chronological completed TB history.
- `docs/swisstopo_data_strategy.md` - public geodata strategy and boundaries.
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md` - second-site public-context staging decision.
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
