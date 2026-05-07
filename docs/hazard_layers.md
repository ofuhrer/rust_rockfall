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
- optional trajectory-level exceedance probability layers for configured
  thresholds:
  - `kinetic_energy_exceedance_<threshold>j`
  - `jump_height_exceedance_<threshold>m`
  - `velocity_exceedance_<threshold>mps`
- opt-in sampling-weighted conditional layers when `hazard_probability` is
  configured with `probability_model: sampling_weighted`:
  - `weighted_reach_probability`
  - `weighted_kinetic_energy_exceedance_<threshold>j`
  - `weighted_jump_height_exceedance_<threshold>m`
  - `weighted_velocity_exceedance_<threshold>mps`

Exports:

- CSV grid with row, column, cell center, and value.
- ESRI ASCII grid for lightweight GIS-style inspection.
- opt-in GeoTIFF raster per hazard layer with affine transform, nodata, EPSG
  metadata when available, and SHA-256 manifest identity.
- GeoJSON point file for deposition locations.
- JSON metadata and `run_manifest_v1` provenance sidecars.
- optional PNG layer plots when diagnostic rendering is enabled.
- optional local `index.html` report when diagnostic rendering is enabled.

## Usage

Run a case first so the expected CSV/JSON outputs exist:

```bash
cargo run -- validate --case validation/cases/validation_tschamut_baseline.yaml
python3 scripts/build_hazard_layers.py \
  --case validation/cases/validation_tschamut_baseline.yaml \
  --output-dir hazard/results/tschamut_baseline \
  --cell-size 5 \
  --no-plots
```

For a synthetic scarring case with impact-event diagnostics:

```bash
cargo run -- verify --case verification/synthetic/synthetic_scarring_energy_dissipation.yaml
python3 scripts/build_hazard_layers.py \
  --case verification/synthetic/synthetic_scarring_energy_dissipation.yaml \
  --output-dir hazard/results/synthetic_scarring \
  --cell-size 1
```

For production-style benchmark or pilot runs, `--no-plots` is recommended. It
writes only the core CSV, ASCII grid, GeoJSON, metadata JSON, and manifest
outputs. To render PNG plots and a local HTML diagnostic report for inspection,
omit `--no-plots`:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/validation_tschamut_baseline.yaml \
  --output-dir hazard/results/tschamut_baseline_report \
  --cell-size 5
open hazard/results/tschamut_baseline_report/index.html
```

To add GIS-ready GeoTIFF rasters without changing the CSV/ASCII outputs or
hazard values, pass `--export-geotiff` or set `hazard_exports.geotiff: true` in
the case file:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/probabilistic_phase1_smoke.yaml \
  --trajectory validation/results/probabilistic_phase1_smoke_trajectory.csv \
  --ensemble-trajectories-dir validation/results/probabilistic_phase1_smoke_trajectories \
  --output-dir hazard/results/probabilistic_phase1_smoke_geotiff \
  --cell-size 2 \
  --no-plots \
  --export-geotiff
```

The GeoTIFF writer is intentionally lightweight and dependency-free. It writes
uncompressed float64 GeoTIFFs so raster cell values round-trip exactly relative
to the CSV/ASCII grids. When the case has `terrain.metadata_path`, the TIFF and
manifest carry the available EPSG, affine transform, nodata, extent, and grid
metadata. Cloud-Optimized GeoTIFF is reserved for a later verified writer; COG
requests fail explicitly rather than producing non-COG files.

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

For diagnostic intensity-style interpretation, add opt-in exceedance layers. These
layers are additive and leave the existing reach, deposition, maximum-energy,
jump-height, and impact-density layers unchanged:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml \
  --output-dir hazard/results/swissalti3d_hazard_statistics \
  --cell-size 2 \
  --kinetic-energy-exceedance-j 5 \
  --kinetic-energy-exceedance-j 10 \
  --jump-height-exceedance-m 0.05 \
  --velocity-exceedance-mps 1.0
```

The same thresholds can be stored in a case file:

```yaml
hazard_layers:
  statistics:
    kinetic_energy_exceedance_j: [5.0, 10.0]
    jump_height_exceedance_m: [0.05, 0.10]
    velocity_exceedance_mps: [0.5, 1.0]
```

## Sampling-Weighted Conditional Maps

Weighted hazard layers are opt-in and use `trajectory_metadata_table_v1`.
They currently support only Monte Carlo-style `sampling_weight`; they do not
represent physical source probabilities, annual release frequencies, block-size
probability distributions, exposure, or risk.

```yaml
hazard_probability:
  probability_model: sampling_weighted
  metadata_path: validation/results/example_trajectory_metadata.csv
  weight_column: sampling_weight
  normalization_convention: conditioned_on_filter
  filters:
    source_zone_ids: []
    scenario_ids: []
    block_mass_kg_min: null
    block_mass_kg_max: null
```

Validation rules are deliberately strict:

- `probability_model` must be `sampling_weighted`;
- `normalization_convention` must be `conditioned_on_filter`;
- `weight_column` must be `sampling_weight`;
- metadata must contain `trajectory_id` and nonnegative finite weights;
- all supplied trajectory IDs must resolve to metadata rows;
- filters must leave positive total weight.

Weighted reach and weighted exceedance layers are normalized by the total
filtered sampling weight. If all weights are `1.0`, weighted layers match the
corresponding unweighted trajectory-count layers. Unweighted outputs are still
written unchanged whenever weighted maps are enabled.

Phase 1 map-package labelling is also opt-in. It does not change the weighted
or unweighted raster values; it only labels outputs and writes a
`map_package_manifest_v1` sidecar for auditability. The existing
`hazard_probability.probability_model: sampling_weighted` block remains the
numerical switch for weighted layers. A labelled weighted package uses the
external probability-mode label `sampling_weighted_conditional`:

```yaml
hazard_map_package:
  map_product_id: phase1_zone_a_weighted
  probability_mode: sampling_weighted_conditional
  normalization_scope: conditioned_on_filter
  source_zone_metadata_path: tests/fixtures/probabilistic_phase1/source_zone_valid.yaml
  scenario_table_path: tests/fixtures/probabilistic_phase1/scenario_level2_weighted.csv
  map_package_manifest_json: hazard/results/phase1_zone_a/map_package_manifest.json
```

The same fields can be supplied on the command line with
`--map-product-id`, `--probability-mode`, `--normalization-scope`,
`--source-zone-metadata-path`, `--scenario-table-path`, and
`--map-package-manifest-json`.

Hazard manifests for labelled runs include additive `hazard_map_package` and
`layer_semantics` sections. The package manifest records `map_product_id`,
`probability_mode`, `normalization_scope`, source-zone and scenario sidecars,
hazard manifest paths, layer semantics, limitations, and
`operational_status: research_diagnostic`. `annual_frequency` and
`physical_probability` labels remain schema-visible but are not generated by the
Phase 1 hazard builder. Existing runs without `hazard_map_package` remain
diagnostic and are not relabelled probabilistic.

A complete tiny Phase 1 smoke case is checked in at
`validation/cases/probabilistic_phase1_smoke.yaml`. It uses synthetic fixture
metadata only and writes generated files under ignored result directories:

```bash
cargo run -- validate --case validation/cases/probabilistic_phase1_smoke.yaml
python3 scripts/build_hazard_layers.py \
  --case validation/cases/probabilistic_phase1_smoke.yaml \
  --trajectory validation/results/probabilistic_phase1_smoke_trajectory.csv \
  --ensemble-trajectories-dir validation/results/probabilistic_phase1_smoke_trajectories \
  --output-dir hazard/results/probabilistic_phase1_smoke \
  --cell-size 2 \
  --no-plots
```

The explicit `--trajectory` plus `--ensemble-trajectories-dir` arguments make
the hazard input set match the trajectory metadata table exactly: one
representative trajectory plus the generated source-zone trajectories. This is
important for the smoke fixture because all `sampling_weight` values are `1.0`,
so weighted and unweighted trajectory-derived layers should match.

Hazard manifests also record additive artifact identity metadata. Generated
single-file outputs include SHA-256 checksums, and `input_artifacts` records the
case, diagnostics, trajectory CSV collection, deposition CSV, impact-event CSV
collection, and impact-event Parquet collection consumed by the hazard builder
when those inputs are available. Collection checksums are aggregate hashes over
member path, byte size, and file checksum so the manifest can identify inputs
without listing every row. For small collections, the manifest also records
member path, byte size, and SHA-256 entries directly; larger collections keep
the aggregate checksum and set `members_truncated` when the inline member list
is capped.

## Production Versus Diagnostic Rendering

The hazard builder is split into four phases:

1. input discovery/loading;
2. raster and statistic accumulation;
3. core output writing;
4. optional PNG/HTML diagnostic rendering.

`run_manifest_v1.performance` records this split with
`accumulation_seconds`, `core_output_write_seconds`, `plot_render_seconds`,
`plots_enabled`, and the backward-compatible `hazard_layer_seconds` and
`output_write_seconds` fields. `hazard_layer_seconds` is the same accumulation
timing; `output_write_seconds` is the sum of core output writing and optional
plot/report rendering.

Use `--no-plots` for larger runs, benchmark runs, and scripted production-style
hazard layer generation. Use plotted mode only when a human-readable local
diagnostic report is needed for a selected case.

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
  impact-event output is available. Use `outputs.ensemble_impact_events_dir`
  for per-trajectory CSVs or `outputs.ensemble_impact_events_parquet` for one
  batched `impact_events_table_v1` file.

The probability/density rasters are normalized by the number of supplied samples
for that layer. Maximum-value rasters record the largest sampled value in a
cell; they are not expected values, design values, or calibrated hazard
intensities. Exceedance rasters are normalized by trajectory count: a cell is
counted at most once per trajectory for each configured threshold.
Weighted rasters, when enabled, use the same cell-counting rule but replace the
trajectory count denominator with the filtered sum of `sampling_weight`.

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
  ensemble_impact_events_parquet: validation/results/example_impact_events.parquet
```

The hazard builder automatically prefers `ensemble_trajectories_dir` and one
case-defined full-ensemble impact-event source when those paths exist. If both
`ensemble_impact_events_dir` and `ensemble_impact_events_parquet` are present in
a case file, the Parquet table is used by default to avoid double-counting;
explicit CLI impact inputs override that default. CSV directories remain
easiest to inspect by hand; Parquet reduces file-count pressure for
impact-heavy runs. This is the
recommended mode for scientifically meaningful small-to-medium ensemble reach,
energy, jump-height, and significant-impact layers. Keep full debug outputs
disabled for default CI-scale runs unless the extra files are needed.

Parquet impact events can also be supplied explicitly:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/cases/example.yaml \
  --impact-events-parquet validation/results/example_impact_events.parquet \
  --output-dir hazard/results/example \
  --no-plots
```

Reading Parquet impact events requires `pyarrow` in the Python environment. CSV
impact-event directories remain supported and require no additional Python
columnar dependency.

The hazard builder uses streaming CSV passes for raster accumulation. In
auto-grid mode it first scans inputs to discover bounds, then streams the same
inputs into accumulators. In explicit-grid mode it skips the bounds scan and
streams directly into the provided grid. Full trajectory and impact rows are not
retained in memory; deposition points are still retained for the small GeoJSON
debug export.

Exceedance layers are also streaming-friendly. During each trajectory pass, the
builder only stores the set of cells where that one trajectory exceeded each
configured threshold; it does not retain all per-cell kinetic-energy,
jump-height, or velocity samples. Percentile rasters remain future work because
exact per-cell percentiles require heavier state or approximate streaming
quantile sketches.

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

When a case includes `terrain.metadata_path`, the hazard-layer
`run_manifest_v1` sidecar copies the same terrain CRS, vertical datum, extent,
resolution, nodata, source, license, and checksum fields used by validation
manifests. If hazard layers are built from ad hoc CLI inputs without a case
metadata sidecar, the raster files remain numerically valid but CRS/provenance
must be inherited from external workflow documentation.

For exchange outside this repository, use the opt-in GeoTIFF export when
available. Cloud-Optimized GeoTIFF remains a future target for compression,
tiling, and cloud/object-store access once a verified COG writer is selected.
GeoJSON remains useful for small vector overlays, while GeoPackage is a better
future target for larger release zones, deposits, and context features.

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
