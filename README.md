# rust_rockfall

`rust_rockfall` is an independent, open implementation for scalable rockfall trajectory simulation and hazard-map generation for Switzerland's Alpine terrain.

Current crate/model version: `v0.6.1`.

The development goal is an automated, reproducible workflow that can produce rockfall hazard maps across Switzerland from public geodata, primarily swisstopo. The first concrete milestone is a valley-scale pilot that connects pragmatic release-zone and block-scenario generation, large deterministic trajectory ensembles, uncertainty-aware probabilistic post-processing, and GIS-ready hazard outputs. Development priorities are chosen by importance to that goal: close the largest workflow and scientific gaps first, prefer simple reproducible approaches when release-zone and block-probability uncertainty dominates, and treat performance and HPC readiness as core requirements rather than late additions.

The current hazard-map products are diagnostic or sampling-weighted conditional
layers, including conditional intensity-exceedance products over configured
trajectory/scenario sets. The future probabilistic target is pixel-scale
physical-probability or annual intensity-frequency information, or the closest
defensible national hazard-map quantity once physical source-frequency
semantics are mature. The implementation should support efficient single-socket
execution, local parallelism,
reproducible chunked ensembles, a path to CSCS/SLURM orchestration, and roughly
10,000 trajectories per release zone where appropriate. The project is
literature-based and transparent by design. It does not decompile or inspect
proprietary binaries, and it does not claim numerical equivalence with any
proprietary or operational hazard tool.

The roadmap is documented in `docs/roadmap_hazard_mapping.md`. It frames current
conditional products such as reach, deposition, maximum kinetic energy, maximum
jump height, threshold exceedance, and scenario uncertainty layers, plus future
physical-probability and annual intensity-frequency products. Claim levels are
defined in `docs/validation_maturity_framework.md`. Risk modelling,
exposure/vulnerability analysis, and operational warning systems are out of
scope; hazard maps must not be presented as risk maps or operational products
without separate validation and review.

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

Unsupported in v0.6.1: national release-zone derivation, calibrated terrain/material parameter libraries, convex polyhedral contact, hard-contact complementarity solvers, calibrated scarring with drag torque or slip-dependent friction, forest interaction, fragmentation, production SLURM orchestration, GPU execution, and Python bindings. Single-socket performance, local parallelism, manifest-backed chunking, scalable reducers, and CRS-aware GIS outputs are active design targets.

## Versioning

The project uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

New physics must be explicit in configuration. Defaults are not changed silently.

## Quickstart

Prerequisites for local development are Rust with `cargo`, `rustfmt`, and
`clippy`, plus a project-local `uv` Python environment for repository scripts.
See `docs/onboarding.md` for installation, hook setup, optional benchmark data,
and handoff checks.

```bash
cargo test
cargo run -- run --config examples/inclined_plane.json --output trajectory.csv
cargo run -- verify --case verification/analytic/free_fall.yaml
cargo run -- verify --all
cargo run -- validate --all
```

The output CSV contains time, position, velocity, speed, energy diagnostics, and contact state for every trajectory sample.

## Performance Tracking

Performance of the end-to-end workflow is tracked in CI with the opt-in
synthetic standard benchmark profile. Tracking includes both total workflow
runtime and component timings (terrain loading, release generation, simulation,
validation output writing, hazard accumulation, hazard output writing, and
bounds discovery).

- PRs run a benchmark comparison workflow and publish a baseline-vs-PR component
  timing table in the workflow summary.
- `main` runs publish a rolling trend chart to GitHub Pages under:
  `https://<OWNER>.github.io/<REPO>/performance/`
  (for this repository: `https://ofuhrer.github.io/rust_rockfall/performance/`).

![Main performance trend](https://ofuhrer.github.io/rust_rockfall/performance/main_performance.svg)

DEM safety checklist for validation and pilot cases:

- use strict `esri_ascii_grid` only when every possible trajectory query is
  expected to remain inside the DEM cell-center domain and away from nodata;
- use `esri_ascii_grid_clamped` / `ascii_dem_clamped` only when deterministic
  boundary extrapolation and nearest-valid-cell fallback are acceptable
  validation assumptions;
- treat any strict DEM terrain error as a failed input/workflow condition, not
  as a normal physical stop;
- keep CRS, vertical datum, nodata, extent, resolution, and source-tile
  provenance in the associated terrain metadata sidecar.

## Repository Notes

The `background/` folder contains third-party background material and publications. Those documents retain their own copyrights and licenses. They are used only as public scientific and grey-literature references for the independent implementation.

Core algorithm references used by the current design include:

- Leine et al. 2014, *Simulation of rockfall trajectories with consideration of rock shape*
- Leine et al. 2021, *Stability of rigid body motion through an extended intermediate axis theorem*
- Lu et al. 2019, *Modelling rockfall impact with scarring in compactable soils*
- Crosta and Agliardi 2004, *Parametric evaluation of 3D dispersion of rockfall trajectories*
- STONE / GRASS `r.stone` public documentation for point-like 3D rockfall modelling context

Core documentation:

- `docs/literature_review.md`
- `docs/model_design.md`
- `docs/architecture_boundaries.md`
- `docs/implementation_plan.md`
- `docs/onboarding.md`
- `docs/roadmap_hazard_mapping.md`
- `docs/swisstopo_data_strategy.md`
- `docs/dataset_strategy.md`
- `docs/chant_sura_contact_validation.md`
- `docs/hazard_layers.md`
- `docs/verification_plan.md`
- `docs/validation_plan.md`
- `docs/validation_maturity_framework.md`
- `docs/source_frequency_evidence_contract.md`
- `docs/block_release_probability_evidence_contract.md`
- `docs/physical_frequency_reducer_preconditions.md`
- `docs/annual_physical_validation_calibration_review_gate.md`
- `docs/annual_physical_prototype_preflight.md`
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
- `manifest`, `geodata`, `shape`: run metadata, Swiss geodata metadata helpers, and passive block-shape metadata
- `verification/results/`: JSON and CSV reports from `cargo run -- verify`
- `validation/results/`: JSON and CSV reports from `cargo run -- validate`

Use `python3 scripts/audit_local_artifacts.py` to inspect ignored raw-data and
generated-result caches. The audit is read-only and is only a local hygiene aid;
clean-clone reproduction must not depend on ignored cached outputs.

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

Generated layers include reach probability, deposition density, maximum kinetic energy, maximum jump height, significant impact density when impact events are available, conditional intensity-exceedance layers, sampling-weighted conditional layers, and uncertainty diagnostics where available. These are hazard indicators intended to develop future physical-probability or annual intensity-frequency quantities; current products are not annualized, not risk maps, and not operational Swiss hazard products.

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
For a local/private Tschamut rerun with a manually supplied real swissALTI3D-style
crop, use `scripts/prepare_tschamut_swissalti3d_pilot.py` to generate ignored
baseline and `sphere_rotational_v1` case files under `validation/private/`.
That workflow is documented in `docs/tschamut_swissalti3d_pilot.md` and does
not tune parameters or commit raw geodata.

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
  && .venv/bin/python -m unittest discover -s tests -p 'test_*.py' \
  && .venv/bin/python scripts/check_repo_consistency.py
```

CI remains the source of truth; the hooks are a local guardrail.
