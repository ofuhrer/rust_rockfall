# TB-603 Balfrin Hazard-Throughput Run

Date: 2026-05-26

TB-603 submitted the reviewed bounded hazard-throughput package from TB-602 on
Balfrin `postproc`, monitored it to completion, and collected the run-root
metrics.

## Submission

- Job ID: `4372309`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:23`
- Node: `nid001225`
- Allocated CPUs: `16`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_tb603_20260526`
- Reviewed package:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb603_hazard_throughput_submission_package`
- Metrics JSON:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb603_probe_metrics.json`
- Metrics report:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb603_probe_metrics_report.json`

The package was regenerated on Balfrin under `$SCRATCH` before submission so
that the reviewed handoff and authorization-record paths existed on the
cluster. The submitted run used a fresh TB-603 run root instead of the older
`tschamut_public_balfrin_multi_release_zone_v1` root, which already contained
previous measured outputs.

## Metrics

- Metrics contract status: `complete`
- Hazard workflow wall time: `7.043564590974711 s`
- Full batch script measured time: `22.3286811549915 s`
- Hazard-stage measured time: `7.8358131679706275 s`
- Process peak memory: `357.796875 MB`
- Hazard output: `57` files / `31,439,786` bytes
- Validation output footprint: `130` files / `34,565,316` bytes
- Hazard manifest outputs: `50` entries / `17,417,138` bytes
- Conditional-curve rows represented: `729,600`
- Conditional-curve export mode: `summary-only`
- Conditional-curve CSV table written: `false`
- Trajectory chunk decisions: `{"executed": 2}`
- Reducer chunk decisions: `{"executed": 2}`
- Merge order: `sorted_chunk_id`
- Merge order independent: `true`

Checksums were recorded for the command plan, probe metrics, hazard manifest,
and scaling summary. No mandatory metrics were missing. Ancillary
per-output-kind timing/byte breakdowns and the legacy validation-output-mode
field were unavailable in this retained bundle.

## Output Boundary

The run preserved the scalable output controls from the package:

- conditional curves remained summary-only;
- the full conditional-curve CSV was suppressed;
- no full grid CSV was exported;
- plot generation stayed disabled;
- the run root stayed on `$SCRATCH`.

This is measured hazard-throughput evidence for a bounded `postproc` run. It
does not by itself close operational, physical-probability, Swiss-wide,
distributed, risk, or non-`postproc` claims.
