# Public Benchmark Baseline Results

Status: no-tuning baseline execution inventory for the unified public
benchmark framework. This report records what can be run with the current
repository and what remains metadata-only. It does not tune parameters, change
defaults, change validation semantics, or claim operational hazard validity.

## Scope

Executed or prepared benchmarks:

| Benchmark | Current execution status | Model configurations | Primary output |
| --- | --- | --- | --- |
| Tschamut 2014 | Runnable all-usable public benchmark | `translational_v0`, `sphere_rotational_v1` | deposition/runout metrics, grouped failure modes, explicit-grid hazard layers |
| Chant Sura | Runnable checked-in fixture benchmark | first-flight, contact, extended contact, held-out contact; default and rotational where available | trajectory/contact, energy, jump-height, rebound, timing metrics |
| Chant Sura EOTA221 | Passive metadata benchmark | no active shape-contact physics | EOTA111/EOTA221 provenance and passive shape QA |
| Mel de la Niva | Opt-in runnable scaffold | path-endpoint/deposition smoke cases when public raw archives are locally cached | public archive inventory, LV03 DSM crop, generated baseline/rotational cases, and explicit limitations |

The generated manifests and result products are ignored artifacts under
`validation/results/public_benchmarks/`, `validation/results/`, and
`hazard/results/public_benchmarks/`.

## Commands Run

Preparation:

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

Validation:

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

## Reproducibility And Provenance

| Dataset | Manifest status | CRS/provenance status | Exclusion status |
| --- | --- | --- | --- |
| Tschamut 2014 | `run_manifest_v1` and hazard manifests written for both contact modes | EnviDat observations, public swissALTI3D tile checksum, `scan_surface_fit_v1`, LV95/EPSG:2056 terrain crop, explicit hazard grid | all 80 processed shared LPS/overview runs included; 31 overview rows remain data-availability exclusions from the processed public intersection |
| Chant Sura | preparation manifest written from checked-in processed fixtures | EnviDat DOI/license recorded; RF16 DEM contact fixtures retain EPSG:2056 metadata where available | deterministic model-selection, extended, and held-out fixtures already recorded |
| Chant Sura EOTA221 | passive shape manifest written | EOTA111 and EOTA221 shape rows recorded from public shape summary | no active validation run; metadata QA only |
| Mel de la Niva | opt-in runnable smoke manifest written when public archives are locally cached | Zenodo DOI/license, archive checksums, EPSG:21781/LV03 CRS, and generated DSM crop provenance recorded | both public LAS trajectories selected; timing limitation recorded |

## Tschamut Results

All 80 usable public Tschamut runs were included with deterministic seed
`34014`, ensemble size `6`, public swissALTI3D 2 m terrain, and
`scan_surface_fit_v1` registration.

| Model | Releases | Simulated trajectories | Observed mean runout (m) | Simulated mean runout (m) | Mean runout error (m) | Deposition centroid error (m) | Cloud mean nearest error (m) | Overlap fraction | Lateral spread error (m) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | 80 | 480 | 98.401 | 63.398 | 35.003 under-run | 34.635 | 18.890 | 0.8375 | 9.709 |
| `sphere_rotational_v1` | 80 | 480 | 98.401 | 202.953 | 104.552 over-run | 103.915 | 80.314 | 0.0000 | 14.609 |

Tschamut interpretation:

- The current default remains a systematic under-run model on public
  swissALTI3D terrain.
- The opt-in rotational sphere model over-runs the same benchmark strongly.
- The split is consistent with the all-runs grouped-validation report:
  registration is no longer the dominant explanation, and the remaining error
  is structural rather than a simple parameter offset.
- No contact-model default decision should be made from Tschamut alone because
  Chant Sura trajectory/contact evidence and Tschamut deposition/runout evidence
  stress different model behavior.

### Tschamut Hazard-Layer Inventory

Hazard layers were generated with explicit grid source, no plots, 308 x 309
cells at 2 m.

| Model | Reach nonzero cells | Deposition cells | Significant-impact cells | Max kinetic energy (J) | Max jump height (m) | 10 kJ exceedance cells | 2 m jump exceedance cells | Hazard wall time (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `translational_v0` | 740 | 82 | 696 | 10699 | 1.722 | 3 | 0 | 17.39 |
| `sphere_rotational_v1` | 5125 | 282 | 3616 | 26153 | 7.229 | 3588 | 717 | 13.55 |

Hazard interpretation:

- The default output is compact, impact-rich, and low jump-height.
- The rotational output has much broader reach, significant-impact footprint,
  kinetic-energy exceedance, and jump-height exceedance.
- These layers are diagnostic hazard products, not risk maps.

## Chant Sura Results

The Chant Sura benchmark currently consists of checked-in first-flight and
small DEM-backed contact fixtures. It stresses trajectory/contact realism more
than deposition/runout.

| Case | Model | Observed contacts | Trajectory shape mean error (m) | Energy mean relative error | Jump-height envelope error (m) | Rebound velocity mean error (m/s) | Impact timing mean error (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| First-flight subset | `translational_v0` | n/a | 0.000013 | 0.000051 | n/a | n/a | n/a |
| RF16 contact | `translational_v0` | 2 | 0.418 | 0.394 | 0.731 | 4.899 | 0.628 |
| RF16 contact | `sphere_rotational_v1` | 2 | 0.378 | 0.289 | 0.750 | 4.902 | 0.628 |
| Extended contact | `translational_v0` | 11 | 0.563 | 0.498 | 0.713 | 4.281 | 0.683 |
| Extended contact | `sphere_rotational_v1` | 11 | 0.529 | 0.427 | 0.742 | 4.355 | 0.683 |
| Held-out contact | `translational_v0` | 9 | 0.505 | 0.440 | 0.713 | 4.099 | 0.474 |
| Held-out contact | `sphere_rotational_v1` | 9 | 0.475 | 0.391 | 0.744 | 4.150 | 0.477 |

Chant Sura interpretation:

- First-flight kinematics are effectively reproduced because the fixture is
  mostly ballistic and intentionally short.
- `sphere_rotational_v1` consistently improves trajectory shape and
  translational energy metrics on RF16 contact fixtures.
- Jump-height envelope and rebound velocity do not improve, so the rotational
  sphere model is not a complete contact solution.
- These fixtures remain small and should not be used as deposition/runout
  validation.

## Chant Sura EOTA221 Passive Shape QA

The EOTA221 preparation manifest found:

| Shape summary | Value |
| --- | --- |
| All EOTA shape rows | 2 |
| EOTA221 rows | 1 |
| EOTA221 point count | 24 |
| EOTA221 bounding dimensions from fixture (m) | 1.4136 x 1.4136 x 0.7068 |
| Current dynamics status | passive metadata only |

Interpretation:

- EOTA221 is ready as a provenance and shape-class benchmark input.
- It is not yet an active shape-contact validation because the current
  simulator still uses equivalent-sphere contact unless a future version adds
  opt-in active shape physics.
- Any future EOTA221 validation must prove that passive sidecars stay inert for
  existing contact models and only affect dynamics when an explicit active
  shape-contact model is selected.

## Mel de la Niva Status

The Mel de la Niva workflow now has an opt-in runnable package:

| Item | Status |
| --- | --- |
| Zenodo public source | recorded |
| License | CC BY 4.0 recorded |
| CRS | EPSG:21781 / LV03 retained for the first generated package |
| Required raw archives for runnable package | trajectory LAS, GIS shapes, SfM DSM |
| Runnable validation cases | generated under ignored `validation/results/public_benchmarks/mel_de_la_niva_runnable/cases/` |
| Terrain/hazard layers | DSM crop generated; hazard layers not part of the first smoke package |

The first package should be generated explicitly:

```bash
python3 scripts/prepare_mel_de_la_niva_benchmark.py \
  --download-runnable-archives \
  --make-runnable \
  --output-root validation/results/public_benchmarks/mel_de_la_niva_runnable
```

It is not a calibrated high-energy validation result. The LAS trajectory files
used by this package do not carry timing fields, so the workflow compares
path-endpoint/deposition references and preserves the timing limitation in the
manifest. `observed_runout_m` is horizontal release-to-matched-deposited-block
endpoint displacement. The package records nearest-neighbor deposition match
distances and applies no hard match threshold in this first smoke workflow, so
those matches remain QA evidence rather than strong field-validation evidence.
The generated active block masses use a documented 2670 kg/m3 density
assumption, not measured Mel de la Niva block densities.

## Cross-Dataset Stress Matrix

| Stress target | Dataset(s) | Current evidence |
| --- | --- | --- |
| Trajectory realism | Chant Sura | rotational sphere improves shape/energy metrics but not rebound/jump metrics |
| Contact timing/rebound | Chant Sura | both current contact modes retain large rebound-velocity and timing errors |
| Deposition/runout realism | Tschamut | default under-runs; rotational sphere over-runs |
| Shape/orientation behavior | Chant Sura EOTA221, Tschamut sidecars | passive metadata is available; no active shape-contact validation yet |
| Hazard-footprint realism | Tschamut | explicit-grid diagnostic layers expose compact default footprint versus broad rotational footprint |
| External high-energy generalization | Mel de la Niva | first runnable endpoint/deposition smoke workflow implemented; timed trajectory validation remains incomplete |
| Lateral-spread issues | Tschamut | rotational sphere has larger lateral-spread error and broader hazard footprint |
| Terrain/material sensitivity | Tschamut, future Mel de la Niva | remains confounded with contact and shape effects; no calibration performed |

## Readiness Matrix

| Benchmark | Ready now | Partial workflow only | Registration uncertain | Shape metadata incomplete | GIS/hazard layers incomplete | Calibration meaningful now |
| --- | --- | --- | --- | --- | --- | --- |
| Tschamut 2014 | yes, for no-tuning grouped deposition/runout diagnostics | no | bounded by `scan_surface_fit_v1`, not dominant in current result | mixed-block all-runs case remains passive/no single sidecar | no, explicit-grid hazard layers generated | no |
| Chant Sura | yes, for small trajectory/contact fixtures | yes, full-campaign runout not included | low for checked-in RF16 fixture, but subset is small | EOTA summary exists but active dynamics absent | yes, hazard layers are not the primary product | no |
| Chant Sura EOTA221 | yes, for passive shape QA | yes | not applicable as standalone trajectory workflow | no for basic EOTA111/EOTA221 shape rows; yes for run-level orientation histories | not applicable | no |
| Mel de la Niva | opt-in generated cases | yes, runnable smoke scaffold | LV03 retained; timing incomplete | raw block-shape ingestion not active | yes | no |

## Major Failure Modes Observed

1. Tschamut exposes a structural deposition/runout split: the default model
   stops too early, while rotational sphere transport persists too far.
2. Chant Sura exposes a partial benefit of rotational coupling for trajectory
   shape and energy, but not for rebound velocity, jump-height envelope, or
   impact timing.
3. EOTA221 confirms that shape/orientation data are available, but the current
   benchmark can only carry those data passively.
4. Mel de la Niva is the largest remaining workflow gap because it has public
   high-energy data but no reproducible runnable package yet.

## Recommended Use Of This Baseline

- Use Tschamut as the no-tuning deposition/runout and hazard-footprint baseline
  for active shape-contact and terrain/material decisions.
- Use Chant Sura as the trajectory/contact realism baseline for any future
  active shape-contact model.
- Use EOTA221 only as passive shape-readiness until active shape dynamics are
  implemented.
- Treat Mel de la Niva as the next ingestion target after the shape-contact
  design path is stable enough to benefit from a high-energy external
  benchmark.
