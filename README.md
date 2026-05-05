# rust_rockfall

`rust_rockfall` is an independent, open, research-oriented implementation of a small computational core for 3D rockfall trajectory experiments.

Current crate/model version: `v0.3.0`.

The project is literature-based and transparent by design. It does not contain RAMMS::ROCKFALL code, does not decompile or inspect proprietary binaries, and does not claim numerical equivalence with RAMMS::ROCKFALL or any other operational hazard tool. The current implementation is experimental and is not validated for operational hazard assessment.

## Current Model

The first model is intentionally small:

- spherical block with mass, radius, and simple rotational diagnostics
- analytic terrain: inclined plane, paraboloid, and step terrain
- ESRI ASCII grid DEM reader for small validation fixtures
- gravity-driven free flight with exact constant-acceleration stepping
- impact response with normal and tangential restitution
- Coulomb friction during contact
- opt-in `sphere_rotational_v1` contact with rolling diagnostics
- deterministic seeded release perturbations
- opt-in `stochastic_contact_v1` impact roughness for seeded ensemble spread
- CSV trajectory output from a CLI

Unsupported in v0.3.0: calibrated terrain roughness fields, convex polyhedral contact, hard-contact complementarity solvers, compactable-soil scarring, forest interaction, fragmentation, GIS production workflows, GPU/HPC execution, and Python bindings.

## Versioning

The project uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

New physics must be explicit in configuration. Defaults are not changed silently.

## Quickstart

```bash
cargo test
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
cargo run -- verify --case verification/analytic/free_fall.yaml
cargo run -- verify --all
cargo run -- validate --all
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
- `docs/README.md`
- `CHANGELOG.md`

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

Large public datasets are downloaded on demand with `scripts/download_datasets.py`. The repository includes a small public-derived Tschamut 2014 validation subset for CI-scale smoke testing; it is not calibrated field validation.

The default CI/local suite should run:

```bash
cargo test
cargo run -- verify --all
```

Optional large public-data validation cases skip gracefully until data have been downloaded and preprocessed.

## Calibration

Calibration experiments are separate from validation and live under `calibration/`. The first controlled Tschamut experiment can be reproduced with:

```bash
python3 scripts/run_tschamut_calibration.py
```

It writes ignored intermediate files under `calibration/results/` and committed summaries under `calibration/experiments/tschamut_v0_3/`. The resulting parameters are research diagnostics only, not project defaults and not operational hazard parameters.

## Visualization

Optional diagnostic visualization tools live under `visualization/`. They consume existing CSV trajectory and JSON report outputs and generate PNG plots without adding dependencies to the Rust core:

```bash
cargo run -- verify --case verification/analytic/free_fall.yaml
python3 visualization/plot_case.py \
  --case verification/analytic/free_fall.yaml \
  --output-dir visualization/output/free_fall
```

Visualization is for inspection and debugging only; numerical verification and validation remain authoritative.

To build a local HTML report for the standard versioned verification/validation cases:

```bash
cargo run -- verify --all
cargo run -- validate --all
python3 visualization/build_report.py --render-plots
open visualization/reports/standard_v0/index.html
```

The HTML report is a diagnostic review layer. It includes interpretation notes, known v0 limitations, plot captions, case-specific checked/not-checked scope, and neutral skipped status for optional public-data cases. Synthetic and analytic reports do not imply operational hazard validation.

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
  && cargo run -- verify --all \
  && cargo run -- validate --all \
  && python3 scripts/check_repo_consistency.py
```

CI remains the source of truth; the hooks are a local guardrail.
