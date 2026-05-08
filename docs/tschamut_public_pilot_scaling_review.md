# Tschamut Public Pilot Scaling Review

Status: local manifest-based scaling and output-volume evidence.
This is a research diagnostic performance note, not validation evidence,
not an operational hazard-map claim, and not an annual or physical
probability product.

This review has been reconciled with
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`. The
generated scaling JSON and all source manifests remain ignored local artifacts;
the committed run-freeze records only paths, checksums, runtime, memory, file
count, and byte-count evidence.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py \
  --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json \
  --output-md docs/tschamut_public_pilot_scaling_review.md
```

## Observed Local Metrics

| Stage | Wall seconds | Output write seconds | Rows read/written | Files | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| validation | 4.066 | 2.340 | 81845 | 125 | 34531527 |
| hazard | 15.586 | 11.433 | 81710 | 55 | 192297963 |

Local ignored output tree totals:

- Files: `186`
- Bytes: `226925754`

External `/usr/bin/time` sidecars:

- Validation: `recorded` (`4.23` s elapsed, `41572` KiB max RSS)
- Hazard: `recorded` (`16.41` s elapsed, `390588` KiB max RSS)

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
- Largest hazard output bytes: `117305412`
- Next action: optimize or gate conditional-curve table and raster output modes before increasing ensemble size.

Do not add MPI, GPU, SLURM orchestration, annual frequency, physical
probability, or ensemble-size increases from this evidence alone.

## Claim Boundary

Current products remain conditional intensity-exceedance and
sampling-weighted conditional diagnostics. The scaling summary does not
introduce exposure, vulnerability, consequence, expected loss, return
period, annual frequency, physical probability, or operational map
semantics.
