# Probabilistic Hazard-Layer Workflow

The first hazard-layer workflow converts existing simulation outputs into simple
spatial raster/vector products. It is a post-processing layer only: it does not
add physics, does not alter validation or calibration, and does not include risk
modelling.

## Scope

Current layers:

- `reach_probability`: fraction of supplied trajectory CSVs that touch each grid
  cell. This is the first runout/reach probability raster.
- `deposition_density`: fraction of ensemble deposition points in each grid cell.
- `max_kinetic_energy`: maximum sampled kinetic energy per cell.
- `max_jump_height`: maximum sampled height above terrain plus block radius per
  cell, where the terrain can be evaluated from case metadata.
- `significant_impact_density`: fraction of impact events per cell whose
  incoming normal speed is at least `0.05 m/s`.

Exports:

- CSV grid with row, column, cell center, and value.
- ESRI ASCII grid for lightweight GIS-style inspection.
- GeoJSON point file for deposition locations.
- JSON metadata and `run_manifest_v1` provenance sidecars.
- PNG layer plots when `matplotlib` is available.
- A local `index.html` report.

## Usage

Run a case first so the expected CSV/JSON outputs exist:

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
python3 scripts/build_hazard_layers.py \
  --case validation/cases/validation_tschamut_baseline.yaml \
  --output-dir hazard/results/tschamut_baseline \
  --cell-size 5
```

For a synthetic scarring case with impact-event diagnostics:

```bash
cargo run -- verify --case verification/synthetic/synthetic_scarring_energy_dissipation.yaml
python3 scripts/build_hazard_layers.py \
  --case verification/synthetic/synthetic_scarring_energy_dissipation.yaml \
  --output-dir hazard/results/synthetic_scarring \
  --cell-size 1
```

Open the generated report locally:

```bash
open hazard/results/tschamut_baseline/index.html
```

For production-style tile experiments, provide an explicit reference grid. When
all explicit-grid arguments are supplied, they override `--cell-size` for grid
construction and the metadata/manifest record `source: explicit`:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/validation_tschamut_baseline.yaml \
  --output-dir hazard/results/tschamut_baseline \
  --grid-xmin 0 \
  --grid-ymin 0 \
  --grid-ncols 100 \
  --grid-nrows 100 \
  --grid-cell-size 5
```

## How to Read the Layers

The generated HTML report includes a short interpretation section and per-layer
summary statistics. The most important distinction is the input source:

- trajectory-derived layers (`reach_probability`, `max_kinetic_energy`,
  `max_jump_height`) only represent the trajectory CSV files supplied to the
  script. Use `outputs.ensemble_trajectories_dir` for full ensemble layers;
- deposition-derived layers (`deposition_density`) can already represent the
  current validation ensemble, because validation writes an ensemble deposition
  CSV;
- impact-derived layers (`significant_impact_density`) are only produced when
  impact-event CSV output is available. Use
  `outputs.ensemble_impact_events_dir` for full ensemble impact density.

The probability/density rasters are normalized by the number of supplied samples
for that layer. Maximum-value rasters record the largest sampled value in a
cell; they are not expected values, design values, or calibrated hazard
intensities.

## Current Limitations

The current validation runner writes one representative full trajectory plus an
ensemble deposition CSV by default. Therefore, deposition density already
reflects the ensemble. Reach probability, maximum kinetic energy, and maximum
jump height become ensemble-based only when a case opts into
`outputs.ensemble_trajectories_dir` or when additional trajectory files are
passed explicitly with repeated `--trajectory` arguments.

Opt-in full ensemble trajectory output:

```yaml
outputs:
  trajectory_csv: validation/results/example_representative.csv
  ensemble_deposition_csv: validation/results/example_deposition.csv
  ensemble_trajectories_dir: validation/results/example_ensemble_trajectories
  ensemble_impact_events_dir: validation/results/example_ensemble_impacts
```

The hazard builder automatically prefers `ensemble_trajectories_dir` and
`ensemble_impact_events_dir` from a case file when those directories exist and
contain CSV files. This is the recommended mode for scientifically meaningful
small-to-medium ensemble reach, energy, jump-height, and significant-impact
layers. Keep it disabled for default CI-scale runs unless the extra files are
needed.

The hazard builder uses streaming CSV passes for raster accumulation. In
auto-grid mode it first scans inputs to discover bounds, then streams the same
inputs into accumulators. In explicit-grid mode it skips the bounds scan and
streams directly into the provided grid. Full trajectory and impact rows are not
retained in memory; deposition points are still retained for the small GeoJSON
debug export.

The workflow supports analytic plane/paraboloid/step terrain and ESRI ASCII DEM
terrain for jump-height estimation. Unsupported terrain metadata leaves
jump-height cells unset and records a warning in metadata.

## Swiss Geodata Metadata Requirements

The current CSV grids and ESRI ASCII grids are sufficient for development,
tests, and small diagnostic reports. They are not sufficient by themselves for
Swiss pilot or regional map products because they do not carry full geospatial
metadata.

Any hazard layer derived from swisstopo terrain should record:

- horizontal CRS, expected to be `EPSG:2056` / CH1903+ LV95 for Swiss workflows;
- vertical datum, expected to be LN02 when using standard swissALTI3D products;
- grid resolution, extent, cell alignment, nodata value, and raster dimensions;
- source terrain dataset, tile ids, source filenames, and product date/version;
- crop/resampling method and checksums where available;
- model version, config hash or case id, calibration status, random seed policy,
  ensemble size, and trajectory id range;
- whether each layer was derived from full ensemble trajectories,
  representative trajectories, deposition summaries, or impact-event logs.

For exchange outside this repository, the target raster format should become
GeoTIFF or Cloud-Optimized GeoTIFF so CRS, nodata, compression, and tiling are
standardized. GeoJSON remains useful for small vector overlays, while GeoPackage
is a better future target for larger release zones, deposits, and context
features.

## Hazard Versus Risk

These outputs describe simulated physical hazard indicators only. Risk mapping
requires exposure, vulnerability, temporal occurrence models, and consequence
models. Those are explicitly outside the current simulator.

## Swiss-Wide Scaling Path

For future Alpine/Swiss workflows, this layer can evolve without changing the
trajectory kernel:

- use swissALTI3D as the default bare-earth terrain foundation for pilot hazard
  domains;
- evolve the current opt-in per-trajectory ensemble CSV output toward chunked
  full-ensemble trajectory outputs;
- accumulate rasters tile-by-tile over DEM tiles and release-zone batches;
- preserve deterministic trajectory IDs and seeds for reproducibility;
- export GeoTIFF/Cloud-Optimized GeoTIFF and GeoPackage/GeoJSON products with
  CRS, extent, resolution, and provenance metadata;
- add scenario uncertainty layers for release, terrain, and material-parameter
  ensembles;
- keep calibration/validation metadata attached to every generated map product.

The first scaling review is documented in
`docs/hazard_workflow_scale_review.md`.
The swisstopo input-data strategy is documented in
`docs/swisstopo_data_strategy.md`.
