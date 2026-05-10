# Mid-Scale Balfrin Validation Probe Plan (Estimation-First, No Hazard Execution)

Status: planning artifact for next balfrin validation probes. Do not run the
hazard model from this document.

## Current calibrated anchor

Use this to keep probe planning aligned to measured balfrin evidence:

- `release-zone-count = 10`
- `ensemble-size = 1`
- `trajectory-count-per-zone = 6`
- `trajectory-workers = 2`
- `reducer-workers = 2`
- `trajectory-chunks = 2`
- `reducer-chunks = 2`
- `grid rows x cols = 304 x 300`
- `threshold-count = 2`
- `profile = scalable_conditional`
- `export geotiff = true`

Estimated reference point from estimator:

- `estimated_output_bytes ≈ 15,613,000`
- `estimated_output_file_count = 46`
- dominant output classes: `geotiff_raster, ascii_raster`

This is treated as the baseline control for mid-scale deltas.

## Candidate mid-scale probes (one-dimension-at-a-time)

Run the estimator before each candidate to pre-stage expected footprint and to
identify which model assumptions are being exercised:

```bash
UV_CACHE_DIR=/tmp/uv-cache python3 scripts/estimate_large_scale_execution.py <FLAGS> --format json
```

### 1) More release zones (trajectory-count constant)

- Vary `--release-zone-count` only: `20` (from `10`)
- other params same as baseline

Estimated behavior:

- output bytes: `15,737,999`
- file count: `46`
- dominant classes: `geotiff_raster, ascii_raster`
- growth notes: trajectory-count-replay pressure increases (`trajectory_replay` +15,000 bytes, threshold- and sidecar metadata +30,000 bytes)
- validates:
  - trajectory scaling in replay/metadata terms
  - conditional curve scaling (thresholds unchanged, but total trajectories doubled)

Exact probe command dimensions later:

- keep balfrin profile controls:
  - `--conditional-curve-export summary-only`
  - `--grid-csv-export none`
  - `--export-geotiff`
  - `--no-plots`
- keep `--trajectory-workers 2 --reducer-workers 2`
- synthetic command-plan input should represent roughly double release-cell volume while
  preserving profile controls.

### 2) More trajectories per zone

- Vary `--trajectory-count` only: `12` (from `6`)
- other params same as baseline

Estimated behavior:

- output bytes: `15,737,999`
- file count: `46`
- dominant classes: `geotiff_raster, ascii_raster`
- growth notes: trajectory count exceeds reference; replay metadata grows.
- validates:
  - trajectory replay coefficient
  - conditional curve scaling with higher trajectory volume

Exact probe command dimensions later:

- same profile/worker settings as above
- synthetic command-plan input should increase per-zone trajectory target while holding
  release-zone count at `10`.

### 3) Larger grid

- Vary grid only: `420 x 450` (from `304 x 300`)
- other params same as baseline

Estimated behavior:

- output bytes: `32,162,638`
- file count: `46`
- dominant classes: `geotiff_raster, ascii_raster`
- growth notes: raster surface dominates; first-order raster byte assumptions tested.
- validates:
  - raster scaling with cell count
  - conditional curve contribution relative to raster growth
  - output-class transition risk as grid resolution increases

Exact probe command dimensions later:

- same balfrin profile and workers as baseline
- synthetic input/grid geometry should be adjusted only in grid envelope / cell layout while preserving
  release/tgt trajectory policy.

### 4) Higher chunk count / chunk bookkeeping pressure

- Vary chunk cardinality only: `trajectory-chunks = 4`, `reducer-chunks = 4`
  (keep worker values at `2`)
- other params same as baseline

Estimated behavior:

- output bytes: `15,631,000`
- file count: `50`
- dominant classes: `geotiff_raster, ascii_raster`
- growth notes: chunk metadata scales with chunk count.
- validates:
  - chunk metadata linear growth assumption (now modeled as linear)
  - stale/mixed-orphan safety can be audited when outputs are present

Exact probe command dimensions later:

- same balfrin profile and workers as baseline
- use same synthetic command plan payload as baseline scenario
- provide explicit chunk settings in execution invocation so chunk cardinality is isolated.

## Recommended next execution probes on balfrin

Primary probe:

- **More release zones to 20** (candidate 1).
- Reasoning: directly tests the trajectory/replay growth assumption and scales one
  workload dimension with only moderate expected output increase.

Fallback probe (smaller and quicker):

- **More trajectories per zone to 12** (candidate 2).
- Reasoning: equivalent trajectory-volume pressure with smaller change to non-raster
  footprint assumptions.

## Success criteria for each balfrin follow-up run

For any candidate execution (not performed in this task), require:

- command completion without stale/orphan chunk anomalies
- trajectory/reducer orchestration decision coherence
- repeatability check where one rerun of the same command reuses valid completed state
- numerical output class stability (GeoTIFF / ESRI ASCII / GeoJSON / core hazard CSV diagnostics)
- manifest parse and schema checks pass
- captured wall time and output bytes include:
  - `output_write_seconds`
  - `output_write_kind_seconds`
  - `output_write_kind_bytes`
  - `output_bytes`
  - `output_file_count`

Non-goals:

- no annual/physical-semantic changes
- no defaults change
- no benchmark claims beyond local-mid-scale feasibility.

## Notes to carry into balfrin runbook

- Candidate planning remains local-laptop in this phase.
- These are still conditional-only scaling probes; not Swiss-scale operational evidence.
- If future balfrin runs show deviations, tighten the estimator’s per-dimension growth terms
  before using it to set larger frontier benchmarks.
