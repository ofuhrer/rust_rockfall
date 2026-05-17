# Initial Performance Benchmark Results

Status: first measurement pass after adding `run_manifest_v1` timing metadata. This document is a benchmark note, not a performance target. It does not change simulation physics, validation semantics, or output formats.

## Setup

Benchmarks were run on May 5, 2026 on the local development machine:

- OS/kernel: Darwin 25.3.0, arm64
- CPU: Apple M1
- logical CPUs: 8
- memory: 16 GiB
- Rust: `rustc 1.95.0`, `cargo 1.95.0`
- Python: `3.11.11`
- model version: `0.5.0`
- git hash in manifests: `e149cfd`
- build mode: `cargo run` development profile

Private Tschamut/swissALTI3D pilot inputs were not present under `validation/private/`, so the documented medium private benchmark could not be run. Instead, the first meaningful end-to-end measurement used the checked-in synthetic Swiss pilot fixture with full ensemble trajectories, full ensemble impact events, and exceedance hazard layers.

## Commands Run

```bash
cargo run -- validate --case validation/cases/performance_smoke.yaml

cargo run -- validate \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml

python3 scripts/build_hazard_layers.py \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml \
  --output-dir hazard/results/performance_initial_swiss_pilot \
  --cell-size 2

python3 scripts/build_hazard_layers.py \
  --case validation/cases/swissalti3d_hazard_statistics_pilot.yaml \
  --output-dir hazard/results/performance_initial_swiss_pilot_no_plots \
  --cell-size 2 \
  --no-plots
```

The generated result directories are ignored artifacts and should not be committed.

## Timing Results

Validation manifest timings count every trajectory execution performed by the validation runner, including representative and comparison/reproducibility trajectories. They are therefore kernel-workload counters, not just the number of ensemble CSVs written.

| Run | total wall s | terrain load s | release generation s | simulation s | output write s | hazard layer s | trajectories | impacts | trajectories/s | impacts/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `performance_smoke` validation | 0.0143 | 0.0009 | 0.000011 | 0.0054 | 0.0013 | n/a | 7 | 211 | 1288 | 38828 |
| `swissalti3d_hazard_statistics_pilot` validation | 0.0200 | 0.0019 | 0.000005 | 0.0043 | 0.0079 | n/a | 7 | 174 | 1632 | 40569 |
| hazard builder, with PNG plots | 1.7439 | 0.0 | 0.0 | 0.0 | 1.7012 | 0.0055 | 4 | 138 | n/a | n/a |
| hazard builder, `--no-plots` | 0.0351 | 0.0 | 0.0 | 0.0 | 0.0039 | 0.0053 | 4 | 138 | n/a | n/a |

## I/O Volume

| Run | output files | output bytes | Notes |
|---|---:|---:|---|
| `performance_smoke` validation | 3 | 2,838 | Manifest summary excludes the generated release-point CSV because it is release-zone provenance rather than a declared output entry. |
| `swissalti3d_hazard_statistics_pilot` validation | 11 | 160,848 | Includes ensemble deposition, trajectory directory, impact-event directory, diagnostics, and manifest summaries. |
| hazard builder, with PNG plots | 36 | 456,229 | PNG plots dominate byte volume and wall time for this tiny grid. |
| hazard builder, `--no-plots` | 25 | 26,046 | Core CSV/ASCII/GeoJSON/JSON outputs only; current no-plot runs skip HTML reports. |

## Bottleneck Assessment

For the current checked-in benchmark size, Rust simulation is not the bottleneck. The validation runs complete in about 20 ms in the development profile, and the measured simulation time is below 6 ms. Terrain loading and deterministic release generation are also negligible for the small fixture.

The clearest measured bottleneck is hazard-layer plotting/output rendering. Raster accumulation itself took about 5.5 ms, while writing the plotted hazard report took about 1.70 s. Running the same hazard build with `--no-plots` reduced total wall time from 1.74 s to 0.035 s and output volume from 456 kB to 26 kB.

The current benchmark is too small to justify changing trajectory or impact-event storage formats. CSV file count and bytes are visible in the manifests, but this fixture writes only four ensemble trajectories and four impact-event files. That does not exercise the expected large-ensemble I/O failure mode.

## Interpretation

The instrumentation is working: manifests now expose enough phase timings and output-volume metadata to distinguish simulation, output writing, and hazard post-processing. The first measurement also shows that optional diagnostic visualization can dominate wall time long before numerical simulation does.

The result should not be generalized to real Swiss pilot domains. A useful medium benchmark still needs a private DEM crop, tens to hundreds of release points, and explicit comparisons with full trajectory output enabled and disabled.

## Recommendation

Recommended next engineering direction: **E. no optimization yet; improve benchmark realism first.**

Reasoning:

- **A. Parquet/Arrow trajectory and impact output** is premature. The current data point does not yet show CSV trajectory or impact-event output as the limiting path.
- **B. GeoTIFF/COG hazard raster export** remains important for GIS interoperability, but the current bottleneck is not raster format size; it is optional PNG/report rendering in a tiny benchmark.
- **C. simulation-loop optimization** is not supported by the evidence. Kernel time is currently small relative to reporting overhead.
- **D. parallel ensemble execution** is likely important later, but the checked-in benchmark is too small to measure scaling or scheduling behavior.
- **E. improve benchmark realism first** is the evidence-based next step. The next benchmark should use a private swissALTI3D-style crop, 50-200 deterministic release points, and paired runs with full trajectory/impact outputs enabled and disabled.

## Next Benchmark Recipe

Run the private Tschamut/swissALTI3D pilot when data are available:

1. Prepare baseline and rotational private cases with `scripts/prepare_tschamut_swissalti3d_pilot.py`.
2. Run baseline and `sphere_rotational_v1` cases with ensemble deposition only.
3. Run the same cases with `ensemble_trajectories_dir` enabled.
4. Run again with `ensemble_impact_events_dir` enabled.
5. Build hazard layers with and without plots.
6. Compare manifests by `simulation_seconds`, `accumulation_seconds`, `core_output_write_seconds`, `plot_render_seconds`, `plots_enabled`, `trajectory_count`, `impact_event_count`, `output_file_count`, and `output_bytes`.

Only after that benchmark should the project choose between binary trajectory formats, tiled raster export, parallel ensemble execution, or simulation-kernel optimization.
