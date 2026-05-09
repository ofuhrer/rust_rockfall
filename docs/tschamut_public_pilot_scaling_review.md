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
