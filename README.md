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
contract. Peak-memory and split validation/hazard output metrics were later
recovered from preserved/read-only sources; the attempted metrics-completion
rerun and the smallest multi-zone probe both failed closed before submission.
No further Balfrin execution is authorized by default. Future live Balfrin
submission requires an explicit user instruction for the exact bounded run,
GPT-5.5 Balfrin-worker routing, and the existing access, readiness,
authorization, output-budget, preservation, and evidence gates. Generated
packages, ready preflights, and previous approvals do not authorize a new run.

Swiss-wide automation is still emerging. The repo now has deterministic
dry-run helpers for AOI product discovery, public-geodata cache verification,
AOI terrain preprocessing from staged tiles, terrain-driven release-zone
candidate stability checks, generic candidate-source-zone scenario generation,
second-site acquisition planning, site-level case-skeleton handoff, and
planning-only GIS scope summaries. Post-TB-273, the AOI-to-map user path also
has a fixture-backed regression from AOI dry run to tiny hazard map, an AOI
hazard-map packager, a static QA review surface, and an optional observed
evidence overlay hook. It does not yet download all public inputs, run
arbitrary real AOIs end to end, execute second-site ensembles, or generate
physically annualized intensity-frequency products.

The second-site and physical-evidence boundaries are stricter than in earlier
milestones: Chant Sura / Fluelapass real-core inputs are classified as real,
fixture-backed, partial, missing, or metadata-mismatched before any
prepared-pilot dry run can look ready; observed benchmark intake now accepts or
rejects real packages deterministically; AOI map packages can carry accepted
observed runout/deposition or field-supported release-zone provenance overlays;
and release-zone provenance, block-population evidence, calibration inputs,
holdout evidence, and source-frequency records remain separated from
conditional sampling weights and hazard outputs.

Current products are diagnostic or sampling-weighted conditional hazard layers.
They are not annualized, not risk maps, and not operational Swiss hazard
products. Scientific closure remains inconclusive and physical credibility is
not established. Optional observed-evidence overlays are map-review evidence,
not calibration, physical probability, annual frequency, risk, or operational
approval. Risk, exposure, vulnerability, warning, and regulatory semantics are
out of scope.

## Quickstart

Prerequisites are Rust with `cargo`, `rustfmt`, and `clippy`, plus the
project-local `uv` Python environment. See `docs/onboarding.md` for setup.

```bash
cargo test
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
cargo run -- verify --all
cargo run -- validate --all
PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py
```

For active implementation work, use `docs/task_backlog.md` and the compact task
context helper:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
```

Local repository Python commands should use `PYENV_VERSION=system uv run python ...`
so pyenv shims and global packages do not affect results. GitHub Actions may
install `requirements-tools.txt` into its system Python; that file is kept in
sync with `pyproject.toml` for CI compatibility, not as a separate local policy.

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
- `docs/target_area_physical_evidence_acquisition_pack.md` - physical-evidence acquisition and claim-boundary pack.
- `docs/orchestration_strategy.md` - sequential worker orchestration and log-monitoring strategy.
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
