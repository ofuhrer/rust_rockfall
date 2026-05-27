# Large-Scale Execution Probe (Projection-Only)

Status: analysis artifact for planning, not an operational benchmark.

This document describes a local, read-only estimator for conditional hazard-stage
execution growth as problem size increases.

The probe intentionally does **not** execute hazard runs. It projects output and
artifact growth from workload parameters and current output-profile controls.

- no full Swiss-scale simulation,
- no Slurm/MPI orchestration claims,
- no operational readiness assertion.

## Purpose

The current deterministic local stack is robust for small workloads, but we still
need to reason about future Swiss-scale pressure before running large-scale jobs.
This estimator provides a first-pass projection for:

- release-zone growth,
- ensemble and trajectory growth,
- chunking pressure on trajectory and reducer metadata,
- output volume growth by output class,
- profile-driven output-mode deltas.

## Supported Profiles

- `full_debug`
- `scalable_conditional`
- `provenance_audit`

These profiles follow [`docs/hazard_output_profile_contract.md`](hazard_output_profile_contract.md).

## Input Variables

- `--release-zone-count`
- `--ensemble-size`
- `--trajectory-count` (trajectories per release zone)
- `--grid-rows`, `--grid-cols`
- `--trajectory-workers`, `--reducer-workers`
- optional `--trajectory-chunks`, `--reducer-chunks` (explicit overrides)
- `--threshold-count`
- `--profile`
- GeoTIFF switch: `--export-geotiff` / `--no-export-geotiff`

## Estimated Outputs

The estimator returns:

- `estimated_output_bytes`
- `estimated_output_file_count`
- `output_bytes_by_class`
- `file_counts_by_class`
- `dominant_output_classes`
- `chunk_counts` (`trajectory_chunks`, `reducer_chunks`)
- growth notes and assumptions

Output bytes are currently decomposed into:

- raster bytes (`ascii_raster`, `geotiff_raster`),
- profile output classes (`grid_csv`, `conditional_curve`),
- replay/provenance support (`chunk_management`, `trajectory_replay`,
  `sidecar_metadata`),
- profile audit sidecars (`provenance_artifacts`, when applicable).

## Interpretation

- The model is anchored to clean Tschamut small-gate evidence where available
  (e.g., output deltas across `full_debug` and `scalable_conditional` families).
- Estimates are directional and monotonic, not exact.
- Scaling is best used to compare scenario alternatives, not to predict wall-clock
  execution time from first principles.

### Balfrin calibration cross-check

For comparison against measured clean balfrin small-gate evidence, use the same
workload geometry and 2×2 chunking:

- `--release-zone-count 10`
- `--ensemble-size 1`
- `--trajectory-count 6`
- `--grid-rows 304`
- `--grid-cols 300`
- `--trajectory-workers 2`
- `--reducer-workers 2`
- `--trajectory-chunks 2`
- `--reducer-chunks 2`
- `--threshold-count 2`

That setting should be interpreted as the probe-equivalent of the clean balfrin
`--trajectory-workers 2 --reducer-workers 2` conditional 2×2 reference.

Observed estimate class behavior at this configuration:

- `scalable_conditional`:
  - `estimated_output_bytes`: close to `15,579,398`
  - `estimated_output_file_count`: `46`
  - dominant classes: geotiff/ascii raster + sidecar + conditional curve.
- `provenance_audit`:
  - `estimated_output_file_count`: `50` (4 extra provenance manifests)
  - bytes increase primarily in `provenance_artifacts`.

Measured balfrin calibration points available (same command policy, now including
grid scaling):

- `420 × 450` grid with 20 release cells and 12 trajectories:
  - `output_bytes`: `32,124,792`
  - `output_file_count`: `46`
  - `grid-cell delta`: `~2.07×`
  - interpretation: raster bytes and write time increased approximately in proportion to cell count, while file count remained constant, supporting the probe’s raster-dominant scaling model.

Important:

- `--profile` and chunk settings are synthetic parameters in the probe and must
  be matched explicitly.
- A prior one-zone setup (`release-zone-count 1`) is useful for sensitivity but is
  not an apples-to-apples reference to the balfrin 2×2 benchmark.

## CLI

```bash
python3 scripts/estimate_large_scale_execution.py \
  --release-zone-count 120 \
  --ensemble-size 4 \
  --trajectory-count 25 \
  --grid-rows 2400 \
  --grid-cols 2500 \
  --trajectory-workers 8 \
  --reducer-workers 8 \
  --trajectory-chunks 8 \
  --reducer-chunks 8 \
  --threshold-count 4 \
  --profile scalable_conditional \
  --export-geotiff \
  --format json
```

## Current Limitations

- Not a benchmark.
- Does not replace empirical runs.
- Does not model filesystem/network contention explicitly.
- Does not assert numerical output correctness.
- Output coefficients are policy/probe approximations and should be re-calibrated
  when stable full Swiss-scale execution evidence exists.

Use this as a planning aid before larger-scale experiments are run.
