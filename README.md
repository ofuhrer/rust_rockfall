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
contract. Peak-memory and split validation/hazard output metrics were then
measured by the TB-307 metrics-completion rerun on `postproc` as SLURM job
`4339889`; the earlier blocked/failed-closed attempts remain history, not
current blockers. The smallest two-zone submit path still has no measured
multi-zone hazard result: TB-309 failed closed before `sbatch` because the
reviewed submit package did not match the executable pilot-run contract. The
current scale surface also includes reduced-output command-plan
enforcement, validation-output replay/debug budget inventories, a local
1/2/4/8/12-zone scaling ladder, a measured four-zone post-processing/reducer
package on Balfrin `postproc`, a read-only Balfrin run-root output-budget
auditor, and a compact scale evidence dashboard for workers. These surfaces
distinguish `measured_on_balfrin`,
`measured_on_balfrin_postproc_microbenchmark`, `fixture_backed`,
`scratch_local`, `projection_only`, `blocked_pre_submit`, and `failed_closed`
evidence so blocked, local, synthetic, or failed-closed branches are not
promoted to measured hazard scale capability.
The user has granted standing clearance for GPT-5.5 workers to submit and
actively monitor Balfrin jobs on the `postproc` partition, including multiple
concurrent jobs and filling that partition. If the work would keep `postproc`
fully busy for more than 6 hours, the run plan must be rediscussed. This
clearance does not relax access, readiness, authorization-record/audit,
output-budget, preservation, or evidence gates, and it does not authorize
non-postproc partitions, distributed execution, scale-up claims, or scientific
or operational claim upgrades.

Swiss-wide automation is still emerging. The repo now has deterministic
dry-run helpers for AOI product discovery, public-geodata cache verification,
mode-gated public-geodata staging, AOI terrain preprocessing from staged
tiles, terrain-driven release-zone candidate stability checks, generic
candidate-source-zone scenario generation, second-site acquisition planning,
site-level case-skeleton handoff, and planning-only GIS scope summaries. The
AOI-to-map user path now has a guided front door, a fixture-backed
bounds-to-review-map regression, an AOI hazard-map packager, and a static QA
review surface that exposes layer inventory, warnings, provenance, observed
overlay status, and the next recommended command. It does not yet download all
public inputs by default, run arbitrary real AOIs end to end, execute
second-site ensembles, or generate physically annualized intensity-frequency
products. The canonical quickstart documents the `workflow --format text`
front door, which prints `workflow_status`, `first_blocker`, `next_command`,
required inputs, generated outputs, and claim boundaries in one
copy-pasteable summary.

TB-338/TB-359 added and refreshed the current management-facing scale synthesis:
`docs/swiss_scale_feasibility_projection.md` and
`docs/balfrin_scale_demonstration_management_package.md`. The current answer is
that 10-zone single-AOI work is feasible under the present single-node/postproc
boundary, 100-zone work is conditionally feasible but deferred, and regional or
Swiss-wide execution is out of reach until public-geodata automation,
release/scenario generation, multi-zone hazard execution, reducer/manifest
pressure, and GIS/COG packaging blockers are reduced with measured evidence.
TB-340 through TB-359 moved the next workflow layer forward: real-AOI
public-geodata acquisition and cache-integrity planning, real-AOI terrain and
context preprocessing, release-zone candidate sweep/stability/review tooling,
candidate scenario pressure gates, an AOI prepared-pilot compiler, large-AOI GIS
manifest repair, regenerated multi-zone Balfrin submit contracts, fail-closed
two-zone/four-zone submit evidence, measured four-zone postproc/reducer
pressure, hazard-throughput no-op boundaries, and the latest Swiss-scale
projection refresh. These changes improve automation and evidence separation,
but they still do not provide measured multi-zone Balfrin hazard execution.

The canonical AOI quickstart lives in
[`docs/public_real_site_geodata_preparation.md#canonical-aoi-quickstart`](docs/public_real_site_geodata_preparation.md#canonical-aoi-quickstart).
Use that path for the command-level bounds-to-review-map walkthrough instead
of duplicating AOI helper steps in new docs.

Current next-backlog recommendations are deliberately execution- or
acquisition-oriented: acquire and preprocess real public geodata for arbitrary
AOIs, make release-zone and scenario generation defensible on real terrain,
repair/regenerate failed-closed multi-zone submit contracts before live
multi-zone scale steps, measure bounded multi-zone Balfrin hazard execution,
and pursue performance work only from measured bottlenecks. Physical-frequency,
calibration, risk/exposure/vulnerability, and operational claims remain
deferred.

The front-door `scripts/run_aoi_hazard_workflow.py status` mode now reports a
normalized `workflow_status`, `first_blocker`, `next_command`,
`expected_inputs`, and `expected_outputs` set so the next step is visible
without digging through nested helper reports.

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

Canonical AOI quickstart:
[`docs/public_real_site_geodata_preparation.md#canonical-aoi-quickstart`](docs/public_real_site_geodata_preparation.md#canonical-aoi-quickstart)
for the end-to-end user-facing AOI path, with helper commands kept linked from
that document.

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
- `docs/swiss_scale_feasibility_projection.md` - current measured-evidence Swiss-scale feasibility projection.
- `docs/balfrin_scale_demonstration_management_package.md` - management-facing Balfrin scale synthesis.
- `docs/output_budget_reducer_scaling_gate.md` - output/reducer budget and run-root audit contract.
- `docs/multi_zone_reducer_pressure_probe.md` - multi-zone pressure and local scaling ladder evidence.
- `docs/decision_log.md` - durable decisions.
- `docs/agent_work_log.md` - chronological completed TB history.
- `docs/swisstopo_data_strategy.md` - public geodata strategy and boundaries.
- `docs/chant_sura_fluelapass_real_context_acquisition_decision.md` - second-site public-context staging decision.
- `docs/target_area_physical_evidence_acquisition_pack.md` - physical-evidence acquisition and claim-boundary pack.
- `docs/orchestration_strategy.md` - sequential worker orchestration and log-monitoring strategy.
- `docs/validation_maturity_framework.md` - claim levels and validation maturity.
- `docs/opennhm_learnings_report.md` - OpenNHM/AvaFrame/DebrisFrame workflow lessons relevant to future user-facing GIS and AOI workflow design.

## Local Git Hooks

Install the lightweight pre-commit hook with:

```bash
scripts/install_git_hooks.sh
```

The hook runs `cargo fmt --check` and YAML syntax checks. There is no repository
pre-push hook; run task-specific tests and repository consistency checks before
committing or pushing. CI remains the source of truth for full regression
coverage.
