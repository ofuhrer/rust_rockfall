# rust_rockfall

`rust_rockfall` is an independent, open, research-oriented implementation of a small computational core for 3D rockfall trajectory experiments.

The project is literature-based and transparent by design. It does not contain RAMMS::ROCKFALL code, does not decompile or inspect proprietary binaries, and does not claim numerical equivalence with RAMMS::ROCKFALL or any other operational hazard tool. The current implementation is experimental and is not validated for operational hazard assessment.

## Current Model

The first model is intentionally small:

- spherical block with mass, radius, and simple rotational diagnostics
- analytic terrain: inclined plane, paraboloid, and step terrain
- ESRI ASCII grid DEM reader for small validation fixtures
- gravity-driven free flight with exact constant-acceleration stepping
- impact response with normal and tangential restitution
- Coulomb friction during contact
- deterministic seeded release perturbations
- CSV trajectory output from a CLI

Unsupported in v0: convex polyhedral contact, hard-contact complementarity solvers, compactable-soil scarring, forest interaction, fragmentation, GIS production workflows, visualization, GPU/HPC execution, and Python bindings.

## Quickstart

```bash
cargo test
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
cargo run -- verify --case verification/analytic/free_fall.yaml
cargo run -- verify --all
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
```

The output CSV contains time, position, velocity, speed, energy diagnostics, and contact state for every trajectory sample.

## Repository Notes

The `background/` folder contains third-party background material and publications. Those documents retain their own copyrights and licenses. They are used only as public scientific and grey-literature references for the independent implementation.

Core documentation:

- `docs/literature_review.md`
- `docs/model_design.md`
- `docs/implementation_plan.md`
- `docs/verification_plan.md`
- `docs/validation_plan.md`
- `docs/benchmark_catalog.md`
- `docs/datasets.md`
- `docs/validation_data_schema.md`

## Rust Crate Layout

- `terrain`: terrain abstractions, analytic terrain, DEM interpolation
- `geometry`: spherical block and future shape placeholders
- `state`: state, contact state, energy diagnostics, trajectory samples
- `dynamics`: gravity, contact response, Coulomb friction
- `integrator`: fixed-step trajectory execution
- `stochastic`: seeded release perturbations
- `simulation`: configuration and orchestration
- `io`: JSON configuration and CSV output
- `validation`: analytic validation helpers
- `verification/results/`: JSON and CSV reports from `cargo run -- verify`
- `validation/results/`: JSON and CSV reports from `cargo run -- validate`

## Verification and Validation

The repository separates:

- verification: analytic and procedural checks under `verification/`
- validation: real-world and synthetic validation cases under `validation/`
- calibration: future explicit parameter-fitting experiments only

Large public datasets are downloaded on demand with `scripts/download_datasets.py`; they are not required for normal tests.

The default CI/local suite should run:

```bash
cargo test
cargo run -- verify --all
```

Optional public-data validation cases skip gracefully until data have been downloaded and preprocessed.

## Visualization

Optional diagnostic visualization tools live under `visualization/`. They consume existing CSV trajectory and JSON report outputs and generate PNG plots without adding dependencies to the Rust core:

```bash
cargo run -- verify --case verification/analytic/free_fall.yaml
python3 visualization/plot_case.py \
  --case verification/analytic/free_fall.yaml \
  --output-dir visualization/output/free_fall
```

Visualization is for inspection and debugging only; numerical verification and validation remain authoritative.

To build a local HTML report for the standard v0 verification/validation cases:

```bash
cargo run -- verify --all
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
python3 visualization/build_report.py --render-plots
open visualization/reports/standard_v0/index.html
```

## Local Git Hooks

Optional hook templates are stored under `scripts/git-hooks/`. Install them with:

```bash
scripts/install_git_hooks.sh
```

The `pre-commit` hook runs `cargo fmt --check` and YAML syntax checks. The `pre-push` hook runs the full local chain:

```bash
cargo fmt --check \
  && cargo clippy --all-targets --all-features -- -D warnings \
  && cargo test \
  && cargo run -- verify --all
```

CI remains the source of truth; the hooks are a local guardrail.
