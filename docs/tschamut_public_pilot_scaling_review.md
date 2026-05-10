# Tschamut Public Pilot Scaling Review

Status: local manifest-based scaling and output-volume evidence.
This is a research diagnostic performance note, not validation evidence,
not an operational hazard-map claim, and not an annual or physical
probability product.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py \
  --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json \
  --output-md docs/tschamut_public_pilot_scaling_review.md
```

## Observed Local Metrics

| Stage | Wall seconds | Output write seconds | Rows read/written | Files | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| validation | 3.750 | 2.535 | 81845 | 125 | 34562779 |
| hazard | 12.172 | 8.687 | 81710 | 58 | 192717542 |

Local ignored output tree totals:

- Files: `188`
- Bytes: `267522045`

External `/usr/bin/time` sidecars:

- Validation: `missing`
- Hazard: `missing`

## Reducer Evidence

- Mode: `chunked_local_threads`
- Worker count: `2`
- Chunk count: `2`
- Merge order: `sorted_chunk_id`
- Merge-order independent: `True`

## Bottleneck Decision

- Status: `no_default_change_recommended`
- Primary bottleneck: `hazard_conditional_curve_output_volume`
- Largest hazard output kind: `conditional_intensity_exceedance_curves`
- Largest hazard output bytes: `117670336`
- Next action: optimize or gate conditional-curve table and raster output modes before increasing ensemble size.

Do not add MPI, GPU, SLURM orchestration, annual frequency, physical
probability, or ensemble-size increases from this evidence alone.

## Claim Boundary

Current products remain conditional intensity-exceedance and
sampling-weighted conditional diagnostics. The scaling summary does not
introduce exposure, vulnerability, consequence, expected loss, return
period, annual frequency, physical probability, or operational map
semantics.

## Balfrin CSV-grid suppression evidence (clean main, conditional-only)

A clean balfrin `main` benchmark was executed on identical Tschamut
gate_v1 inputs with:

- `--conditional-curve-export summary-only`
- `--reducer-workers 2`
- `--grid-csv-export` set to `full` and `none`.

| Mode | Output bytes | Output-write seconds | Wall time | Largest output kind |
| --- | ---: | ---: | ---: | --- |
| `full` | 75,046,369 | 5.3310 | 0:11.57 | `csv_grid` (59,518,059 bytes) |
| `none` | 15,522,667 | 2.7450 | 0:06.54 | `geotiff` (11,678,624 bytes) |

Change from `full` -> `none`:

- `csv_grid` output removed (no `.csv` hazard-grid files in `none`)
- output bytes: `-59,523,702` (-79.3%)
- output-write seconds: `-2.5859` (-48.5%)
- wall time: `-5.03s` (-43.5%)

Remaining bottleneck in `none` mode:

- geotiff + esri_ascii_grid write path, plus non-serialization hazard-stage cost.

Operational scope for this evidence:

- conditional hazard diagnostics only
- no annual/physical semantics
- no default or validator semantic change
- `--grid-csv-export none` is an explicit opt-in scaling mode.

Do not add MPI, GPU, SLURM orchestration, annual frequency, physical probability,
or ensemble-size increases from this evidence alone.

## Local chunk-count scaling smoke (not balfrin evidence)

Location: `/Users/fuhrer/Desktop/rust_rockfall` (laptop/local checkout), not
`/users/olifu/work/rust_rockfall`.

Chunk-count runs (same fixed workload, same outputs policy):

| Trajectory/Reducer Workers | Trajectory Chunks | Reducer Chunks | Wall time (s) | Output write seconds | Output bytes | Output files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2/2` | 2 | 2 | `21.20` | `6.0881` | `15,582,152` | `46` |
| `4/4` | 4 | 4 | `27.61` | `9.5276` | `15,617,393` | `50` |
| `8/8` | 8 | 8 | `32.08` | `8.3838` | `15,687,566` | `58` |

Finding:

- Small Tschamut gate_v1 workload: increasing chunk count from 2 to 4/8 added chunk
  management overhead and did not improve runtime.
- Current locally recommended small-gate mode remains:
  `--trajectory-workers 2 --reducer-workers 2 --conditional-curve-export summary-only --grid-csv-export none`.
- Confirmed clean balfrin-scale chunk-count evidence still requires runs from
  `/users/olifu/work/rust_rockfall`.

## Repeat-run drift classification (same inputs, same command plan)

- Repeat run completed with stable command plan, `trajectory_workers=2`,
  `reducer_workers=2`, `--conditional-curve-export summary-only`,
  `--grid-csv-export none`.
- Wall time improved on reuse (`~9.25s` -> `~4.61s`) with stable
  `trajectory_execution_plan_id`.
- Numeric outputs remained hash-stable (GeoTIFF, ESRI ASCII, GeoJSON, hazard CSV/
  conditional diagnostics).
- Observed drift was limited to provenance/metadata artifacts such as manifests,
  execution plans/indexes, chunk manifests, and pilot GIS/metadata sidecars.
- Acceptable repeat-run rule:
  manifest byte identity is not required; numerical hazard/product hashes should be
  stable; orchestration decisions should be coherent; snapshot first/repeat
  manifests before rerun when provenance diffing is required.
