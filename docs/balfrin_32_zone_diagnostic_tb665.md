# TB-665 Balfrin 32-Zone Diagnostic

Date: 2026-05-27

## Result

The planned 32-zone single-node `postproc` diagnostic completed successfully on
Balfrin.

- run root:
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527`
- job id: `4377419`
- terminal state: `COMPLETED`
- partition: `postproc`
- nodes: `1`
- tasks: `1`
- CPUs per task: `16`
- remote git head: `4b335c03e02e7d2e65704a3ae74e9662a3f2d42f`

## Run Shape

- release zones: `32`
- reducer chunks: `4`
- reducer workers: `4`
- manifest mode: `compact`
- output family mix: `trajectory_csv`, `deposition_csv`,
  `impact_events_csv`, `trajectory_merge_state`, `reducer_merge_state`
- requested time limit: `00:45:00`

The run command was:

```bash
cd /users/olifu/work/rust_rockfall
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 32 \
  --reducer-chunks 4 \
  --reducer-workers 4 \
  --manifest-mode compact \
  --partition postproc \
  --time 00:45:00 \
  --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/tb665_32_zone_20260527 \
  --poll-seconds 10 \
  --monitor-timeout-seconds 3600 \
  --format json
```

## Collected Metrics

- run status: `completed`
- collection status: `complete`
- scheduler elapsed: `00:00:01`
- scheduler exit code: `0:0`
- `/usr/bin/time` elapsed: `0:01.46`
- peak RSS: `33.531` MB
- reducer wall time: `5.39` seconds
- pressure status: `measured_scratch_root`
- scenario count: `32`
- output files: `100`
- output bytes: `42,188`
- root files in pressure report: `105`
- manifest bytes: `24,426`
- pressure-root footprint: `105` files / `73,471` bytes
- run-root footprint: `113` files / `177,458` bytes

## Preserved Files

The run root contains the required replay and accounting artifacts:

- `run_record.json`
- `diagnostic.sbatch`
- `logs/diagnostic.stdout`
- `logs/diagnostic.stderr`
- `time_verbose.txt`
- `multi_zone_reducer_pressure.json`
- `multi_zone_reducer_pressure.md`
- `slurm_accounting.psv`
- `pressure_root/command_plan.json`

## Next Diagnostic Size

The pressure report keeps the diagnostic planning recommendation at a
40-release-zone next diagnostic with fixed reducer fan-out. The current run
repeats the 32-zone diagnostic scale on the simplified runner and confirms that
the current Balfrin path remains low-pressure for this shape.

## Boundary

This is measured single-node `postproc` diagnostic reducer-pressure evidence.
It is not hazard-throughput, physical-probability, annual-frequency,
operational, risk, exposure, vulnerability, distributed, Swiss-wide, or
non-`postproc` evidence.
