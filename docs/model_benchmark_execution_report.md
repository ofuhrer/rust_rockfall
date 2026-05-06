# Model Benchmark Execution Report

Status: expert-review package, not an operational hazard assessment.

This report freezes the current no-tuning benchmark evidence for external review of the simulator and hazard-map workflow. It summarizes the reproducible benchmark inventory already produced by the unified public benchmark framework and the checked-in validation suite. Generated validation and hazard outputs remain ignored; this document records commands, metrics, provenance expectations, and limitations needed to reproduce the package.

## Scope

The package covers:

- analytic and synthetic verification cases;
- checked-in Chant Sura trajectory/contact validation fixtures;
- registered public Tschamut all-usable grouped validation;
- passive Chant Sura EOTA221 shape-metadata QA;
- Mel de la Niva public benchmark scaffold status;
- hazard-layer and probabilistic Phase 1 smoke workflows;
- Phase 2A GeoTIFF hazard raster export smoke workflow;
- provenance, manifest, checksum, and timing instrumentation.

It does not tune parameters, change defaults, change physics, implement annualized hazard maps, or claim operational validity.

## Benchmark Inventory

| Dataset or workflow | Current role | Execution status | Primary evidence |
| --- | --- | --- | --- |
| Analytic verification | Equation and integrator checks | Checked in and run by `cargo test` / `verify --all` | Free fall, projectile motion, rebound, sliding, rolling, stochastic determinism |
| Synthetic validation | Parser, terrain, ensemble, output smoke tests | Checked in and run by `validate --all` | Terrain-source metadata, release-zone generation, terrain classes, hazard statistics, performance smoke |
| Tschamut 2014 public benchmark | Deposition, runout, grouped failure modes, hazard footprint | Runnable public workflow; all 80 processed shared LPS/overview runs analyzed | `docs/public_tschamut_all_runs_grouped_validation.md` |
| Chant Sura | Trajectory/contact realism, energy, jump, rebound timing | Runnable checked-in fixtures | `docs/chant_sura_contact_validation.md`, `docs/chant_sura_contact_generalization.md` |
| Chant Sura EOTA221 | Passive shape/orientation metadata QA | Metadata QA only; no active shape-contact dynamics | `docs/public_benchmark_results_baseline.md` |
| Mel de la Niva | External high-energy/generalization target | Opt-in runnable path-endpoint/deposition smoke scaffold; timed trajectory validation incomplete | `docs/public_benchmark_framework.md` |
| Hazard layers | Diagnostic and labelled Level 1/2 map products | Runnable from validation outputs; CSV/ASCII/GeoJSON/GeoTIFF additive outputs | `docs/hazard_layers.md` |
| Probabilistic Phase 1 smoke | End-to-end Level 1/2 semantics smoke | CI-safe fixture | `validation/cases/probabilistic_phase1_smoke.yaml` |
| GeoTIFF export smoke | GIS raster interoperability for existing hazard layers | Opt-in, additive, tested against CSV/ASCII values | `docs/hazard_layers.md` |

## Reproducible Commands

Public benchmark preparation commands are intentionally explicit and write generated data under ignored result roots:

```bash
python3 scripts/prepare_chant_sura_public_benchmark.py \
  --output-root validation/results/public_benchmarks/chant_sura_baseline

python3 scripts/prepare_chant_sura_eota221_benchmark.py \
  --output-root validation/results/public_benchmarks/chant_sura_eota221_baseline

python3 scripts/prepare_mel_de_la_niva_benchmark.py \
  --output-root validation/results/public_benchmarks/mel_de_la_niva_baseline

python3 scripts/prepare_tschamut_public_benchmark.py \
  --output-root validation/results/public_benchmarks/tschamut_all_runs \
  --run-limit 80 \
  --padding-m 250 \
  --force
```

Core validation commands:

```bash
cargo run -- validate --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_baseline.yaml
cargo run -- validate --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_trajectory_subset.yaml
cargo run -- validate --case validation/cases/chant_sura_contact.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_extended.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_extended_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_heldout.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_heldout_rotational.yaml
```

Tschamut explicit-grid hazard layers:

```bash
python3 scripts/build_hazard_layers.py \
  --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_baseline.yaml \
  --output-dir hazard/results/public_benchmarks/tschamut_all_runs_baseline \
  --grid-xmin 2696360 \
  --grid-ymin 1167382 \
  --grid-ncols 308 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots

python3 scripts/build_hazard_layers.py \
  --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_rotational.yaml \
  --output-dir hazard/results/public_benchmarks/tschamut_all_runs_rotational \
  --grid-xmin 2696360 \
  --grid-ymin 1167382 \
  --grid-ncols 308 \
  --grid-nrows 309 \
  --grid-cell-size 2 \
  --no-plots
```

Optional GIS export for expert review can be enabled additively after the smoke
case has generated its validation outputs:

```bash
cargo run -- validate --case validation/cases/probabilistic_phase1_smoke.yaml
```

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

## Tschamut All-Runs Summary

The public Tschamut benchmark uses EnviDat observations, public swissALTI3D 2 m terrain, deterministic release sampling, and `scan_surface_fit_v1` registration. It processes 80 shared LPS/overview runs and excludes 31 overview rows because no usable processed LPS row is available.

Registration and terrain QA:

- horizontal registration residual mean / p95 / max: 0.485 / 1.507 / 5.149 m;
- vertical registration residual RMSE / abs p95: 0.517 / 1.117 m;
- DEM crop: 308 x 309 cells at 2 m;
- LV95 extent: x 2696360-2696976, y 1167382-1168000;
- NODATA cells: 0;
- release and deposition points inside crop: 80/80 each.

### Runout and Deposition Metrics

| Contact model | Releases | Trajectories | Observed mean runout m | Simulated mean runout m | Signed error m | Deposition centroid error m | Cloud nearest error m | Overlap fraction | Lateral spread error m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | 80 | 480 | 98.401 | 63.398 | -35.003 | 34.635 | 18.890 | 0.8375 | 9.709 |
| `sphere_rotational_v1` | 80 | 480 | 98.401 | 202.953 | +104.552 | 103.915 | 80.314 | 0.0000 | 14.609 |

Interpretation: the default translational model systematically under-runs the public Tschamut observations, while the opt-in rotational sphere model strongly over-runs them. This is a structural diagnostic result, not a calibrated model-ranking result.

### Grouped Failure Modes

| Group | `translational_v0` signed error m | `sphere_rotational_v1` signed error m | Comment |
| --- | ---: | ---: | --- |
| Block 1, blocky/St. Leonard | -41.857 | +98.704 | Large default under-run and rotational over-run |
| Block 2, elongate-heavy | -41.364 | +98.523 | Similar to block 1 despite different mass/shape |
| Block 4, plate-like | -21.241 | +116.873 | Smaller default under-run, largest rotational over-run |
| Short observed runout class | -11.718 | +121.734 | Default sometimes near/over, rotational over-runs |
| Mid observed runout class | -45.523 | +102.659 | Default all under-run |
| Long observed runout class | -48.258 | +88.676 | Default all under-run |
| High significant-impact class | -56.927 | not dominant | Impact-rich default trajectories are systematically short |

The grouped analysis strengthens the hypothesis that current spherical contact and environmental assumptions are insufficient. Shape/contact effects, terrain/material effects, and stopping behavior remain confounded.

### Hazard-Layer Examples

Explicit-grid, no-plot Tschamut hazard products:

| Contact model | Reach cells | Deposition cells | Significant-impact cells | Max kinetic energy J | Max jump height m | KE > 10 kJ cells | Jump > 2 m cells | Hazard wall s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | 740 | 82 | 696 | 10699 | 1.722 | 3 | 0 | 17.39 |
| `sphere_rotational_v1` | 5125 | 282 | 3616 | 26153 | 7.229 | 3588 | 717 | 13.55 |

These rasters are hazard diagnostics and Level 1/2 map products when labelled with validated scenario metadata. They are not annualized hazard maps and are not risk maps.

## Chant Sura Summary

Chant Sura fixtures test trajectory/contact realism rather than deposition/runout realism.

| Fixture | Contacts | Model | Shape mean m | Energy relative mean | Jump envelope m | Rebound velocity mean m/s | Impact timing mean s |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| First-flight subset | 0 | `translational_v0` | 0.000013 | 0.000051 | proxy only | n/a | n/a |
| RF16 contact | 2 | `translational_v0` | 0.418 | 0.394 | 0.731 | 4.899 | 0.628 |
| RF16 contact | 2 | `sphere_rotational_v1` | 0.378 | 0.289 | 0.750 | 4.902 | 0.628 |
| Extended contact | 11 | `translational_v0` | 0.563 | 0.498 | 0.713 | 4.281 | 0.683 |
| Extended contact | 11 | `sphere_rotational_v1` | 0.529 | 0.427 | 0.742 | 4.355 | 0.683 |
| Held-out contact | 9 | `translational_v0` | 0.505 | 0.440 | 0.713 | 4.099 | 0.474 |
| Held-out contact | 9 | `sphere_rotational_v1` | 0.475 | 0.391 | 0.744 | 4.150 | 0.477 |

Interpretation: `sphere_rotational_v1` improves trajectory shape and energy metrics on these small contact fixtures, but rebound velocity, jump envelope, and timing errors remain substantial. These fixtures do not validate Tschamut-style deposition/runout.

## Passive Shape Metadata QA

The passive shape scaffold validates block dimensions, mass properties, orientation quaternions, and provenance without feeding shape inertia into current dynamics. For EOTA221, the public shape QA currently records one EOTA221 row with 24 points and bounding dimensions of approximately 1.4136 x 1.4136 x 0.7068 m. For Tschamut, passive sidecars are available for blocks 1, 2, and 4.

This proves metadata carriage and manifest propagation only. It does not prove shape-aware contact physics.

## Probabilistic Phase 1 Evidence

Phase 1 supports:

- `source_zone_metadata_v1` validation;
- `scenario_table_v1` validation;
- `map_package_manifest_v1` validation and writing;
- trajectory metadata propagation of source-zone, scenario, model-configuration, and sampling-weight identifiers;
- sampling-weighted conditional hazard layers;
- explicit labels that annualized fields are absent.

The smoke example proves a tiny end-to-end workflow: validated metadata, trajectory metadata propagation, weighted layers, labelled hazard manifest, and map-package manifest. It does not prove calibrated probabilities, physical occurrence probabilities, annual frequency, or operational hazard-map validity.

## GeoTIFF and GIS-Readiness Evidence

Phase 2A adds opt-in GeoTIFF export for every generated hazard raster layer. The export is deliberately additive: CSV grids, ESRI ASCII grids, GeoJSON deposition points, JSON metadata, and manifests remain available and unchanged.

Current GeoTIFF behavior:

| Capability | Current status | Review implication |
| --- | --- | --- |
| Raster values | Float64 cells written from the same in-memory layer values used for CSV/ASCII | GIS review can compare values directly against existing debug rasters |
| Grid alignment | Affine transform recorded from the hazard grid | Explicit-grid Swiss/Tschamut runs preserve DEM-cell alignment |
| CRS metadata | EPSG and terrain sidecar metadata propagated where available | QGIS/GIS inspection can verify projected Swiss coordinates |
| NODATA | Preserved in TIFF tags and manifest metadata | Empty cells remain distinguishable from zero-valued cells |
| Weighted labels | Weighted/unweighted layer names and map-package semantics remain in manifests | Probability semantics stay outside implicit raster styling |
| Checksums | GeoTIFF outputs are listed with artifact identity in manifests | External review can audit file identity |
| COG | Explicitly deferred; `--export-cog` fails rather than writing a non-COG file | Cloud/distribution packaging remains future work |

Fresh local smoke check for this review package generated 11 GeoTIFF outputs
from `validation/cases/probabilistic_phase1_smoke.yaml`, including unweighted,
weighted, and exceedance layers. The hazard manifest recorded
`raster_exports.formats: [csv_grid, esri_ascii_grid, geotiff]`,
`geotiff: true`, `cog: false`, and `compression: none`.

Recommended expert-review use:

- load GeoTIFF reach, deposition, kinetic-energy, jump-height, and exceedance rasters in QGIS;
- verify CRS, extent, transform, and NODATA metadata against the hazard manifest;
- compare layer names and map-package semantics before interpreting probability-like layers;
- treat all current GeoTIFFs as research/pilot hazard products, not operational products.

## Visual Artifact Inventory

The following visual artifacts are reproducible but generated under ignored result roots:

| Artifact | Source command or workflow | Review purpose | Commit policy |
| --- | --- | --- | --- |
| Tschamut registration QA overlay | `prepare_tschamut_public_benchmark.py` | Check scan/trajectory registration and crop coverage | Ignored generated output |
| Tschamut trajectory/deposition overlays | Tschamut validation outputs and hazard plotting mode | Compare reach envelope, stopping regions, and deposition overlap | Ignored generated output |
| Reach probability rasters | `build_hazard_layers.py --export-geotiff` | Review spatial reach footprint in QGIS and compare against CSV/ASCII | GeoTIFF generated on demand |
| Max kinetic-energy rasters | `build_hazard_layers.py --export-geotiff` | Review energy envelope and exceedance cells in GIS | GeoTIFF generated on demand |
| Max jump-height rasters | `build_hazard_layers.py --export-geotiff` | Review jump-height envelope in GIS | GeoTIFF generated on demand |
| Weighted vs unweighted smoke rasters | Phase 1 smoke fixture with `--export-geotiff` | Check probability labelling, unity-weight parity, and GIS metadata | Generated in test temp dirs |
| Grouped runout-error plots | Public Tschamut grouped analysis | Review systematic under/over-run structure | Generated on demand |

No generated PNG, HTML, validation result, hazard result, or raw public archive is committed as part of this expert-review package.

## Performance and Output Instrumentation

Current manifests include additive timing, output-volume, artifact-checksum, trajectory-count, impact-count, and hazard input-throughput fields. The benchmark evidence shows:

- diagnostic plotting can dominate hazard-stage wall time and is optional;
- explicit-grid hazard runs remove repeated auto-grid bounds scans from controlled benchmarks;
- projected Parquet impact reads improve significant-impact hazard accumulation;
- Python-level trajectory accumulation remains a known scalability limit;
- GeoTIFF export is additive and intended for GIS interoperability, not numerical changes.

Performance instrumentation is for engineering decisions only; timing values are not scientific pass/fail criteria.

## Provenance and Reproducibility

The benchmark framework records:

- source dataset identifiers, URLs or DOIs, and license fields where available;
- CRS, vertical datum, resolution, extent, NODATA, and terrain checksums;
- deterministic seeds and selected run IDs;
- excluded run IDs with reasons;
- command provenance and generated case paths;
- output artifact checksums where feasible;
- validation `execution_status` separated from `scientific_status`;
- manifest warnings for passive shape metadata and non-operational hazard products.

## Limitations

- Public Tschamut results remain a no-tuning diagnostic benchmark, not a calibrated reproduction.
- Chant Sura fixtures are small and contact-focused.
- EOTA221 is passive shape QA only.
- Mel de la Niva is opt-in runnable as a path-endpoint/deposition smoke
  workflow, but not yet a timed trajectory or calibrated high-energy validation
  benchmark.
- Annualized hazard maps, physical source-frequency models, exposure, vulnerability, and risk are out of scope.
- Current non-spherical shape metadata does not alter contact physics.
- Current hazard maps are conditional or sampling-weighted diagnostics unless explicitly supported by future frequency metadata.

## Review Questions

- Do Tschamut grouped failure modes point more strongly to shape/contact deficiencies, terrain/material assumptions, or release/deposition registration uncertainties?
- Are Chant Sura contact metrics sufficient to justify an active shape-contact prototype, or should rebound/jump diagnostics be strengthened first?
- Are the Level 1/2 probabilistic labels scientifically clear enough for conditional map review?
- Are GeoTIFF exports and manifests adequate for GIS expert review before regional tiling?
- Which additional public dataset should be made runnable next to reduce dataset-specific bias?
