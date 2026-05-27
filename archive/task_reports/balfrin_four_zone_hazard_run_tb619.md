# TB-619 Balfrin Four-Zone Hazard-Throughput Run

Date: 2026-05-27

TB-619 submitted the TB-618 reviewed package on Balfrin `postproc`, monitored
it to completion, and collected the run-root metrics.

## Submission

- Job ID: `4372656`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:30`
- Node: `nid001225`
- Batch MaxRSS from `sacct`: `5636K`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527`
- Package root:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package`
- Reviewed handoff package:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_release_zone_demo_package_v1.json`
- Authorization record:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_zone_live_authorization_record_v1.yaml`
- Metrics JSON:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527/balfrin_probe_metrics.json`
- Accounting record:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/tb619_sacct.psv`

The run used a fresh TB-619 root because the generated historical default
four-zone root already contained older evidence.

## Metrics

- Metrics contract status: `complete`
- Hazard workflow wall time: `6.930015419959091 s`
- Process peak memory: `379.14453125 MB`
- Hazard output: `57` files / `31,439,445` bytes
- Validation output footprint: `130` files / `34,565,323` bytes
- Conditional-curve rows represented: `729,600`
- Run-root files: `68`
- Run-root bytes: `31,528,478`
- Output root files: `57`
- Conditional-curve export mode: `summary-only`
- Full conditional-curve CSV: not written
- Full grid CSV: not written
- Plots: disabled

Ancillary metrics for `validation_output_mode`, `output_write_kind_seconds`,
and `output_write_kind_bytes` remain unavailable in the retained bundle, but no
mandatory metrics are missing.

## Interpretation

This is measured four-zone hazard-throughput evidence on Balfrin `postproc`.
It is comparable in output shape to the TB-603 bounded hazard-throughput run
and should be integrated into the scale-readiness summaries before drawing the
next bottleneck conclusion.

This run does not establish Swiss-wide, distributed, non-`postproc`,
operational, physical-probability, annual-frequency, risk, exposure, or
vulnerability evidence.
