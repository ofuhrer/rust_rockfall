# Synthetic Scale Performance Benchmark Results

Status: historical measured local benchmark result from the May 5, 2026
synthetic scale matrix. This document remains useful for trend context, but
current routine benchmark profiles and default commands are defined in
`docs/performance_benchmarking.md` and
`docs/performance_benchmark_profile_reference.md`. It does not change physics,
validation semantics, or output formats.

## Setup

Run date: May 5, 2026.

Environment:

- OS/kernel: Darwin 25.3.0, arm64
- CPU: Apple M1
- logical CPUs: 8
- memory: 16 GiB
- Rust: `rustc 1.95.0`, `cargo 1.95.0`
- Python: `3.11.11`
- build mode: `cargo run` development profile

Generated benchmark outputs were written under ignored:

```text
validation/results/performance_synthetic_scale/
```

The generated directory occupied about `363 MB` after the full run. It should not be committed.

## Commands Run

Full default matrix:

```bash
rm -rf validation/results/performance_synthetic_scale
python3 scripts/run_performance_benchmark.py
```

The full matrix completed. Nothing was skipped.

Validation/check commands after the benchmark:

```bash
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
cargo test
python3 -m unittest tests/test_hazard_layers.py tests/test_performance_benchmark.py
cargo run -- validate --all
cargo clippy --all-targets --all-features -- -D warnings
```

## Matrix

The benchmark ran:

- release counts: `50`, `100`, `200`;
- contact models: `translational_v0`, `sphere_rotational_v1`;
- validation output modes:
  - summary/deposition only;
  - full ensemble trajectory CSVs;
  - full ensemble impact-event CSVs;
  - both trajectory and impact-event CSVs;
- hazard layers for trajectory-output cases:
  - with PNG plots;
  - with `--no-plots`.

The resulting `summary.csv` contains `48` rows: `24` validation rows and `24` hazard post-processing rows.

## Validation Timing Summary

Validation manifests include representative and release-zone trajectory executions, so the manifest `trajectory_count` is `release_count + 3` for these cases.

| Release count | Mean total wall s | Mean simulation s | Mean output write s | Mean output bytes | Mean output files | Trajectories | Impact events |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 0.452 | 0.227 | 0.203 | 6.30 MB | 53 | 53 | 12,051 |
| 100 | 0.929 | 0.502 | 0.400 | 12.62 MB | 103 | 103 | 23,487 |
| 200 | 1.688 | 1.012 | 0.646 | 25.25 MB | 203 | 203 | 46,347 |

Scaling is roughly linear in release count for both simulation time and output volume. The output-write share grows with enabled debug outputs but does not yet dominate all validation modes.

## Output-Mode Effects

| Output mode | Mean total wall s | Mean simulation s | Mean output write s | Mean output bytes | Mean output files |
|---|---:|---:|---:|---:|---:|
| Summary/deposition only | 0.613 | 0.581 | 0.002 | 31.8 kB | 3 |
| Trajectories only | 0.769 | 0.503 | 0.243 | 9.02 MB | 120 |
| Impact events only | 1.378 | 0.736 | 0.614 | 20.43 MB | 120 |
| Trajectories + impacts | 1.332 | 0.502 | 0.805 | 29.42 MB | 236 |

Impact-event CSVs are currently more expensive than trajectory CSVs for this synthetic benchmark because the cases generate many impacts: up to `46,347` impact events at the 200-release scale. When both trajectory and impact outputs are enabled, output writing becomes comparable to or larger than simulation time.

## Contact-Model Comparison

| Contact model | Mean validation wall s | Mean simulation s | Mean output write s | Mean output bytes | Mean trajectories/s |
|---|---:|---:|---:|---:|---:|
| `translational_v0` | 0.960 | 0.571 | 0.362 | 14.11 MB | 228 |
| `sphere_rotational_v1` | 1.086 | 0.590 | 0.470 | 15.34 MB | 219 |

The rotational model is slightly slower and writes slightly larger trajectory outputs in this synthetic setup. The difference is not large enough to make contact-model arithmetic the dominant engineering bottleneck. It also changes the physical runout strongly in this synthetic terrain, so runtime comparisons should be interpreted as model-and-path comparisons rather than pure per-step cost comparisons.

## Hazard-Layer Timing

| Hazard mode | Mean total wall s | Mean hazard accumulation s | Mean output write s | Mean output bytes | Mean output files |
|---|---:|---:|---:|---:|---:|
| With PNG plots | 3.073 | 0.727 | 1.634 | 1.00 MB | 34.5 |
| `--no-plots` | 1.283 | 0.698 | 0.035 | 0.51 MB | 24.0 |

Hazard accumulation scales with release count and impact-event availability. PNG/report rendering adds a large fixed and semi-fixed cost: disabling plots reduced mean total hazard time by about `58%` and mean output-write time by about `98%`.

For the largest trajectory+impact cases:

| Case | Hazard mode | Total wall s | Hazard accumulation s | Output write s | Output bytes |
|---|---|---:|---:|---:|---:|
| 200 baseline, trajectories+impacts | with plots | 4.940 | 1.480 | 1.409 | 0.99 MB |
| 200 baseline, trajectories+impacts | no plots | 2.830 | 1.486 | 0.024 | 0.49 MB |
| 200 rotational, trajectories+impacts | with plots | 4.408 | 1.553 | 1.485 | 1.24 MB |
| 200 rotational, trajectories+impacts | no plots | 2.965 | 1.562 | 0.032 | 0.72 MB |

Once plots are disabled, hazard accumulation itself becomes the dominant hazard post-processing time.

## Scaling Observations

- Simulation throughput generally stays around `200-260 trajectories/s` for most validation modes, with slower outliers when impact-output runs also show longer measured simulation time.
- Output bytes scale approximately linearly with release count.
- File count scales directly with release count for per-trajectory and per-impact debug directories.
- Impact-event output can exceed trajectory output volume for high-contact synthetic cases.
- Hazard plot generation is expensive even when raster outputs are small.
- Hazard accumulation, not raster file writing, becomes the largest hazard cost when plots are disabled.

## Bottleneck Diagnosis

For validation-only runs, there is not one universal bottleneck:

- with summary/deposition-only output, simulation time dominates;
- with trajectory output, output writing is material but still below simulation time on average;
- with impact-event output, output writing becomes comparable to simulation time;
- with both trajectory and impact outputs, output writing is often the largest component.

For hazard-layer runs:

- with plots enabled, plotting/report output is a major bottleneck;
- with plots disabled, hazard accumulation is the main bottleneck;
- Geo-style raster format is not the measured limiter yet because current ASCII/CSV raster files are small relative to plotting and accumulation time.

## Decision Questions

**Is the simulation loop currently the bottleneck?**

Only for summary/deposition-only validation runs. It is not the dominant bottleneck once full trajectory and impact-event debug outputs are enabled, and it is not involved in hazard post-processing.

**Is CSV trajectory/impact output currently the bottleneck?**

Partly. CSV impact-event output is already expensive enough to compete with simulation time, and combined trajectory+impact output can dominate validation wall time. The benchmark supports treating output volume and file count as a near-term scaling concern, but the current 200-release scale is still small enough that a format migration should be based on one more larger/private benchmark before implementation.

**Is hazard plotting/report generation currently the bottleneck?**

Yes for plotted hazard runs. It is the clearest avoidable cost in the current benchmark. `--no-plots` reduced mean hazard total time from `3.073 s` to `1.283 s`.

**Does the evidence justify Parquet/Arrow now?**

Not yet as the immediate next step. Impact and trajectory CSV output are a credible future bottleneck, but the benchmark is still small and synthetic. The evidence supports designing a columnar-output plan, not implementing it before one larger real-site or private synthetic benchmark.

**Does the evidence justify GeoTIFF/COG now?**

Not for performance. GIS interoperability may still justify GeoTIFF/COG later, but this benchmark does not show ASCII/CSV raster writing as the limiting factor. Hazard accumulation and plotting dominate before raster file format.

**Does the evidence justify parallel execution now?**

Not as the immediate step. Simulation time scales roughly linearly and would benefit from parallelism at larger release counts, but output and hazard post-processing are already significant. Parallel execution without output and post-processing strategy would move the bottleneck rather than remove it.

## Recommendation

Immediate engineering priority: **plotting/reporting changes** for hazard-layer workflows.

The benchmark-driven refactor now separates production hazard-layer generation from optional PNG/HTML diagnostic rendering:

- use `--no-plots` as the recommended mode for benchmark and larger workflow runs;
- keep plot generation as an explicit secondary/reporting step for selected cases;
- inspect `run_manifest_v1.performance.accumulation_seconds`, `core_output_write_seconds`, `plot_render_seconds`, and `plots_enabled` to separate raster/statistic work from report rendering;
- preserve current CSV/ASCII outputs while measuring larger cases.

Secondary priority: prepare for **trajectory/impact output scaling**, especially impact-event CSV volume and per-trajectory file count. This should be planned but not implemented as Parquet/Arrow until a larger benchmark confirms that CSV output dominates beyond the 200-release synthetic scale.

Deferred:

- **Parquet/Arrow**: promising, but needs one larger benchmark or private real-site case first.
- **GeoTIFF/COG**: important for GIS interoperability, not currently a measured performance bottleneck.
- **Simulation-loop optimization**: not first; correctness and model fidelity remain more important, and output/hazard costs are already competitive.
- **Parallel ensemble execution**: useful later, but should follow clearer output/hazard data contracts.

## Next Measurement

Run the same script with a larger local-only synthetic matrix before changing formats:

```bash
python3 scripts/run_performance_benchmark.py \
  --counts 500 1000 \
  --hazard-plots no-plots
```

If that confirms output writing dominates, evaluate a compact trajectory/impact archive format. If hazard accumulation dominates, investigate tiled/streaming spatial reducers before changing raster export formats.
