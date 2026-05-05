# rust_rockfall

`rust_rockfall` is an independent, open, research-oriented implementation of a small computational core for 3D rockfall trajectory experiments.

Current crate/model version: `v0.5.0`.

The long-term goal is a transparent research tool for probabilistic rockfall hazard-map layers in Alpine terrain in Switzerland. The project is literature-based and transparent by design. It does not contain RAMMS::ROCKFALL code, does not decompile or inspect proprietary binaries, and does not claim numerical equivalence with RAMMS::ROCKFALL or any other operational hazard tool. The current implementation is experimental and is not validated for operational hazard assessment.

The roadmap is documented in `docs/roadmap_hazard_mapping.md`. It frames future map outputs such as runout probability, deposition density, maximum kinetic energy, maximum jump height, and scenario uncertainty layers. Risk mapping is a later, separate workflow because it requires exposure and vulnerability data beyond the current simulator.

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
- opt-in `scarring_contact_v1` compactable-soil impact energy-loss diagnostics
- optional per-impact CSV/JSON diagnostics for reconstructing contact and scarring events
- CSV trajectory output from a CLI

Unsupported in v0.5.0: calibrated terrain roughness fields, convex polyhedral contact, hard-contact complementarity solvers, calibrated scarring with drag torque or slip-dependent friction, forest interaction, fragmentation, GIS production workflows, GPU/HPC execution, and Python bindings.

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
- `docs/roadmap_hazard_mapping.md`
- `docs/swisstopo_data_strategy.md`
- `docs/dataset_strategy.md`
- `docs/chant_sura_contact_validation.md`
- `docs/hazard_layers.md`
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

Large public datasets are downloaded on demand with `scripts/download_datasets.py`. The repository includes small public-derived validation fixtures for Tschamut 2014 and Chant Sura 2020. Tschamut is used for deposition/runout distribution diagnostics on a lightweight terrain proxy. Chant Sura includes a first-flight kinematic subset, small RF16 DEM-backed segmented-contact subsets, and a held-out RF16 contact subset for contact-model generalization checks. These fixtures are research validation diagnostics, not calibrated field validation or operational hazard assessment.

The default CI/local suite should run:

```bash
cargo test
cargo run -- verify --all
```

Optional large public-data validation cases skip gracefully until data have been downloaded and preprocessed.

## Calibration

Calibration experiments are separate from validation and live under `calibration/`. The controlled Tschamut trajectory-level experiment can be reproduced with:

```bash
python3 scripts/run_tschamut_calibration.py
```

It writes ignored intermediate files under `calibration/results/` and committed summaries under `calibration/experiments/tschamut_v0_3/`. The resulting parameters are research diagnostics only, not project defaults and not operational hazard parameters.

The first impact-level scarring calibration workflow can be reproduced with:

```bash
python3 scripts/calibrate_scarring_impact.py
```

It uses a semi-empirical proxy dataset to exercise `ImpactEvent` diagnostics and parameter sensitivity. It is not field validation and the selected parameters are not used by validation cases.

The first real-data impact-level scarring experiment uses public Chant Sura / ESurf 2019 scar and jump-energy tables:

```bash
python3 scripts/preprocess_scarring_real_data.py
python3 scripts/calibrate_scarring_impact.py \
  --config calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/config.yaml
```

This experiment is exploratory: impact-normal components are inferred, energy transitions are not pure scarring losses, and the selected parameters are not model defaults.

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

The HTML report is a diagnostic review layer. The `standard_v0` directory name is a stable v0-series output path; the report header and JSON diagnostics carry the exact current model version. It includes interpretation notes, known v0 limitations, plot captions, case-specific checked/not-checked scope, and neutral skipped status for optional public-data cases. Synthetic and analytic reports do not imply operational hazard validation.

## Hazard Layers

The first hazard-layer workflow consumes existing CSV/JSON outputs and writes diagnostic research rasters/vectors under `hazard/results/`:

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
python3 scripts/build_hazard_layers.py \
  --case validation/cases/validation_tschamut_baseline.yaml \
  --output-dir hazard/results/tschamut_baseline \
  --cell-size 5
```

Generated layers include reach probability, deposition density, maximum kinetic energy, maximum jump height, and significant impact density when impact events are available. These are hazard indicators only, not risk maps and not operational Swiss hazard products.

The hazard builder writes both metadata JSON and a `run_manifest_v1` sidecar.
For larger pilot-style runs, pass the explicit grid arguments
`--grid-xmin`, `--grid-ymin`, `--grid-ncols`, `--grid-nrows`, and
`--grid-cell-size` so all layers use a fixed reference grid instead of
auto-discovered bounds.

Future Swiss pilot workflows should use authoritative swisstopo geodata,
especially swissALTI3D for bare-earth terrain. The current repository contains
metadata fixtures and a tiny synthetic swissALTI3D-style validation crop only;
it does not download or commit national swisstopo datasets. Run
`cargo run -- validate --case validation/cases/swissalti3d_pilot.yaml` to
exercise the terrain-source metadata and manifest contract, or
`cargo run -- validate --case validation/cases/swissalti3d_release_zone_pilot.yaml`
to also exercise deterministic source-area release generation, or
`cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml`
to include the opt-in terrain/material-class parameter lookup fixture. Run
`cargo run -- validate --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml`
before building additive exceedance hazard layers for the same synthetic pilot
stack. See
`docs/swisstopo_data_strategy.md` and `docs/swiss_terrain_ingestion_pilot.md`.

For ensemble-based reach, energy, and jump-height layers, opt into
`outputs.ensemble_trajectories_dir` in the case YAML. For ensemble impact
density, opt into `outputs.ensemble_impact_events_dir`. Without those fields,
trajectory-derived layers use the representative CSV while deposition density
can still use the ensemble deposition CSV.

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
