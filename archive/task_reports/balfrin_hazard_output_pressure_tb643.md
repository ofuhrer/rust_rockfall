# TB-643 Balfrin Hazard Output Pressure Summary

Date: 2026-05-27

TB-643 measured reducer and metadata pressure for the largest available
hazard-throughput output root. Because TB-642 found that the current executable
hazard-throughput submit path cannot produce a supported run larger than TB-619,
the measured root is the TB-619 four-zone Balfrin run.

Run root:
`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527`

Hazard manifest:
`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527/output/validation_balfrin_probe_manifest.json`

## Measured Summary

- Metrics contract: `complete`.
- Hazard workflow wall time: `6.930015419959091` s.
- Peak process memory: `379.14453125` MB.
- Hazard output footprint from metrics report: `57` files /
  `31,439,445` bytes.
- Validation output footprint from metrics report: `130` files /
  `34,565,323` bytes.
- Conditional-curve rows represented: `729,600`.
- Hazard manifest size: `99,598` bytes.
- Manifest output entries: `50`.
- Manifest-accounted output files: `50`.
- Manifest-accounted output bytes: `17,416,952`.
- Sidecar / metadata files: `13`.
- Sidecar / metadata bytes: `213,126`.
- Primary hazard files: `37`.
- Primary hazard bytes: `17,203,826`.
- Missing manifest paths: `0`.

## Family Pressure

| Family | Files |
| --- | ---: |
| `hazard_layer` | 36 |
| `deposition_points` | 1 |
| `hazard_metadata` | 1 |
| `map_package_manifest` | 1 |
| `pilot_gis_package_manifest` | 1 |
| `reducer_chunk_manifest` | 2 |
| `reducer_execution_index` | 1 |
| `reducer_execution_plan` | 1 |
| `reducer_merge_state` | 1 |
| `trajectory_chunk_manifest` | 2 |
| `trajectory_execution_index` | 1 |
| `trajectory_execution_plan` | 1 |
| `trajectory_merge_state` | 1 |

The current four-zone hazard root is dominated by primary hazard layers rather
than reducer metadata bytes. Metadata pressure is still visible as manifest and
sidecar fan-out, but it is not yet the largest byte driver at this support
point.

## Pressure Driver

The first practical pressure driver for a larger hazard-throughput run is not
the measured TB-619 sidecar byte volume. It is the current package generator's
larger-than-four-zone replay-family contract:

- the eight-zone handoff probe from TB-642 failed output-budget acceptance;
- replay-critical `trajectory_csv`, `deposition_csv`, and `impact_events_csv`
  family counts would grow from the four-zone limit of `4` to `8`;
- the executable hazard-throughput package branch still emits a four-zone run,
  so there is no accepted >4-zone hazard-throughput manifest to measure.

## Recommended Change

Before submitting another hazard-throughput run beyond TB-619, add a real >4
zone package profile that either:

- writes replay-critical trajectory, deposition, and impact-event outputs in
  chunk-aligned files instead of one file per release zone; or
- explicitly accepts the larger per-family replay counts for the next bounded
  run size and records the expected manifest and sidecar budget.

This change should target the package generator and command plan, not the
diagnostic reducer-pressure runner. The 24/32/100-zone diagnostic series remains
useful performance evidence, but it does not measure hazard-throughput output
pressure.
