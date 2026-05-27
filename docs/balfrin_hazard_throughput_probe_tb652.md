# TB-652 Balfrin 8-Zone Hazard-Throughput Probe

Date: 2026-05-27

## Result

The bounded 8-zone `postproc` diagnostic completed successfully on Balfrin.
The run is preserved under `$SCRATCH`:

```text
/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527
```

The run used the simplified diagnostic front door from the Balfrin checkout:

```bash
cd /users/olifu/work/rust_rockfall
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 8 \
  --reducer-chunks 2 \
  --reducer-workers 2 \
  --manifest-mode compact \
  --partition postproc \
  --time 00:30:00 \
  --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527 \
  --poll-seconds 10 \
  --monitor-timeout-seconds 3600 \
  --format json
```

## Scheduler And Run Shape

- Job id: `4377075`
- Terminal state: `COMPLETED`
- Partition: `postproc`
- Nodes: `1`
- Tasks: `1`
- CPUs per task: `16`
- Release zones: `8`
- Reducer chunks: `2`
- Reducer workers: `2`
- Manifest mode: `compact`
- Remote git head: `4b335c03e02e7d2e65704a3ae74e9662a3f2d42f`

The remote checkout was clean before submission. It was behind the local branch,
so the run used the already-present simplified Balfrin diagnostic runner rather
than newer local-only documentation and reporter changes.

## Collected Metrics

- Run status: `completed`
- Collection status: `complete`
- Elapsed wall time: `0:00.59`
- Peak RSS: `34.223` MB
- Run-root footprint: `41` files / `85,295` bytes
- Pressure-root footprint: `33` files / `24,704` bytes
- Pressure status: `measured_scratch_root`
- Scenario count: `8`
- Output files: `28`
- Output bytes: `14,397`
- Root files: `33`
- Manifest bytes: `11,458`
- Reducer wall time: `2.11` seconds

The local metrics reporter was updated to understand the single
`run_record.json` format used by `scripts/run_balfrin_diagnostic.py`. The fixed
report classifies the run as complete with `14` mandatory diagnostic metrics
measured and `0` blocked metrics. A corrected metrics report was copied to:

```text
/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527/metrics_report_fixed/
```

The older reporter on the remote checkout also wrote a compatibility report in
`metrics_report/`; that report is superseded for this run because it expects the
legacy probe bundle shape rather than the new single-run-record diagnostic
shape.

## Preserved Files

- `run_record.json`
- `diagnostic.sbatch`
- `logs/diagnostic.stdout`
- `logs/diagnostic.stderr`
- `time_verbose.txt`
- `multi_zone_reducer_pressure.json`
- `multi_zone_reducer_pressure.md`
- `slurm_accounting.psv`
- `metrics_report_fixed/tb652_metrics_report_fixed.json`
- `metrics_report_fixed/tb652_metrics_report_fixed.txt`

## Interpretation

This adds a successful measured 8-zone Balfrin `postproc` diagnostic point. It
does not supersede the existing larger diagnostic ceiling evidence, which still
points to a measured 32-zone single-node diagnostic ceiling and recommends a
40-zone next diagnostic run with fixed reducer fan-out. The next task should
thread this completed 8-zone run through the scale surfaces and explain whether
TB-619 or the 32-zone diagnostic remains the current planning anchor.

No operational, physical-probability, annual-frequency, risk, exposure,
vulnerability, Swiss-wide, distributed, or non-`postproc` claim is made by this
run.
