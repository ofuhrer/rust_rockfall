# Visualization

This directory contains lightweight diagnostic visualization tools for simulation outputs. Visualization is deliberately separate from the Rust simulation core: it consumes CSV trajectories and JSON reports after a run has completed.

## Current Outputs

The existing trajectory CSV already includes the fields needed for current plots:

- time
- position and velocity
- speed
- kinetic, rotational, potential, and total energy
- contact state
- angular velocity, contact-point tangential speed, and rolling residual

The verification/validation JSON reports provide case status, metrics, tolerances, warnings, and model metadata. No core output-format change is required for the initial visualization layer.

## Generate Plots

First generate a trajectory and diagnostics report:

```bash
cargo run -- verify --case verification/analytic/free_fall.yaml
```

Then render PNG diagnostics:

```bash
python3 visualization/plot_case.py \
  --case verification/analytic/free_fall.yaml \
  --output-dir visualization/output/free_fall
```

The script writes:

- `*_trajectory_xz.png`: x-z trajectory with terrain overlay where supported
- `*_trajectory_xy.png`: x-y plan view
- `*_energy.png`: kinetic, potential, and total energy over time
- `*_runout_histogram.png`: runout distribution when multiple trajectories are overlaid
- `*_summary.json`: runout, impact count, speed, and report metadata summary

SVG remains available explicitly:

```bash
python3 visualization/plot_case.py \
  --case verification/analytic/free_fall.yaml \
  --format svg
```

## Validation Cases

Validation cases use the same interface:

```bash
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
python3 visualization/plot_case.py \
  --case validation/cases/synthetic_plane_basic.yaml \
  --output-dir visualization/output/synthetic_plane_basic
```

Real-world validation cases skip until processed public observations are present. Visualization should be run after the relevant validation command has produced a trajectory CSV.

## Multiple Trajectories and Ensembles

Overlay multiple CSV trajectories by passing `--trajectory` more than once:

```bash
python3 visualization/plot_case.py \
  --trajectory run_a.csv \
  --trajectory run_b.csv \
  --output-dir visualization/output/ensemble_debug
```

The summary JSON reports simple runout and speed statistics, including median and p05/p95 percentiles. When multiple trajectory CSVs are provided, the script also writes a runout histogram. This is intended for deterministic, small ensembles and debugging. It is not a substitute for numerical validation metrics.

## HTML Reports

Generate a local HTML report that collects standard versioned case metadata, pass/fail/skipped status, numerical metrics, links to raw JSON/CSV outputs, and available PNG plots:

```bash
cargo run -- verify --all
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
python3 visualization/build_report.py --render-plots
```

Open the generated report in a browser:

```bash
open visualization/reports/standard_v0/index.html
```

The report generator reads descriptions, expected behavior, metrics, tolerances, and references directly from the YAML case definitions. It does not duplicate case documentation and does not run simulations itself. The `--render-plots` option only refreshes PNG plots from existing trajectory CSVs.

The report is meant for scientific inspection:

- skipped optional cases are shown as neutral status when required public validation data are not present locally;
- each case states what it checks and what it does not check;
- trajectory and energy plots include captions explaining the diagnostic purpose of each figure;
- stochastic cases that produce only summary metrics explain why no trajectory plot is expected;
- roughness-enabled cases are marked as opt-in and uncalibrated;
- synthetic cases are described as verification/regression checks, not evidence of operational hazard skill.

For a PDF copy, open the HTML report in a browser and use the browser print/save-as-PDF command. The report CSS is kept print-friendly, but the HTML and linked JSON/CSV artifacts remain the primary local outputs.

## Terrain Support

The current x-z terrain overlay supports:

- plane
- paraboloid
- step terrain

The interface is designed so DEM, GeoJSON, GeoTIFF, and larger geospatial layers can be added later without coupling visualization to the core simulator.

## Examples

Checked-in examples are under `visualization/examples/`:

- `analytic_free_fall/`
- `synthetic_inclined_plane_bounce_runout/`

These are small PNG/JSON artifacts generated from checked-in verification cases.

## Dependencies

The script uses `matplotlib` for PNG generation. PyYAML is required only when using `--case` to read YAML case files:

```bash
python3 -m pip install matplotlib PyYAML
```

Visualization is optional and is not part of CI.
