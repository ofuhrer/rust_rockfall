# TB-575 Balfrin 16-Zone Diagnostic Metrics

Date: 2026-05-26

## Summary

TB-575 promoted the completed simplified 16-zone Balfrin diagnostic run into
the current evidence and scale-readiness surfaces. The run used the compact
single-command diagnostic path rather than the older handoff/preflight package
stack.

The evidence is measured reducer-pressure diagnostic evidence. It is not an
operational hazard product, physical-probability product, distributed-execution
claim, or Swiss-wide claim.

## Run Record

- Run root:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525`
- Run record:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525/run_record.json`
- Job id: `4367731`
- Terminal state: `COMPLETED`
- Git head: `665971ee187673b5e1c6d1b99cb0f940de70f723`
- Partition: `postproc`
- Release zones: `16`
- Reducer chunks: `2`
- Reducer workers: `2`
- Manifest mode: `compact`

## Metrics

- Run-record status: `completed`
- Collection status: `complete`
- Pressure status: `measured_scratch_root`
- Reducer wall time: `3.07` seconds
- `/usr/bin/time -v` elapsed: `0:01.24`
- MaxRSS: `34.066` MB
- Diagnostic output files: `52`
- Diagnostic output bytes: `23661`
- Manifest size: `15898` bytes
- Pressure-root files: `57`
- Pressure-root bytes: `41328`
- Full run-root files: `65`
- Full run-root bytes: `110129`

## Promotion

The run record is now consumed directly by:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`

On Balfrin, the scale matrix includes the measured tier
`diagnostic_16_zone_reducer_pressure`, with job `4367731`, runtime `3.07`
seconds, and diagnostic output bytes `23661`.

Older measured runs remain present as historical comparison tiers, including
the regional split evidence from TB-565/TB-566.

## Boundary

This evidence measures compact reducer-pressure behavior for a 16-zone
single-node `postproc` diagnostic run. It does not update the operational batch
ceiling by itself; TB-576 is responsible for threading this measured diagnostic
ceiling into reducer-pressure constraints and next-run decisions.
