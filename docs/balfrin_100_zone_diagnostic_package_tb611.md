# Balfrin 100-Zone Diagnostic Package TB-611

Date: 2026-05-26

Status: prepared no-submit 100-zone diagnostic package on Balfrin and measured
local pressure for the same shape.

Remote package root:

`/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526`

Remote checkout:

`/users/olifu/work/rust_rockfall`

Remote HEAD after fast-forward:

`bb22df0`

## Prepared Package

The package was prepared with:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py prepare \
  --release-zones 100 \
  --reducer-chunks 4 \
  --reducer-workers 4 \
  --manifest-mode compact \
  --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526 \
  --time 00:30:00 \
  --format json
```

Materialized remote files:

| File | Bytes |
| --- | ---: |
| `diagnostic.sbatch` | `1,340` |
| `run_record.json` | `7,356` |
| `tb611_prepare_stdout.json` | `7,356` |

Prepared package footprint: `3` files / `16,052` bytes.

No `sbatch` command was run.

## Submission Command

If a later task decides to submit this exact package, the prepared submit
command is:

```bash
sbatch --parsable /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/diagnostic.sbatch
```

The generated SLURM shape is one `postproc` node, one task, `16` CPUs,
`00:30:00` walltime, and output under:

- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/logs/diagnostic.stdout`
- `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/logs/diagnostic.stderr`

The diagnostic command inside the package is:

```bash
env PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py \
  --materialize-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/pressure_root \
  --release-zone-count 100 \
  --reducer-workers 4 \
  --reducer-chunk-count 4 \
  --output-family-mix trajectory_csv,deposition_csv,impact_events_csv,trajectory_merge_state,reducer_merge_state \
  --manifest-mode compact \
  --format json \
  --json-output /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/multi_zone_reducer_pressure.json \
  --markdown-output /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526/multi_zone_reducer_pressure.md
```

## Pressure Measurement

The same 100-zone diagnostic shape was measured locally without scheduler
submission:

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py \
  --materialize-root /tmp/tb611_100_zone_pressure_root \
  --release-zone-count 100 \
  --reducer-workers 4 \
  --reducer-chunk-count 4 \
  --output-family-mix trajectory_csv,deposition_csv,impact_events_csv,trajectory_merge_state,reducer_merge_state \
  --manifest-mode compact \
  --format json \
  --json-output /tmp/tb611_100_zone_pressure.json \
  --markdown-output /tmp/tb611_100_zone_pressure.md
```

Measured local pressure:

| Measure | Value |
| --- | ---: |
| Release zones | `100` |
| Scenarios | `100` |
| Reducer chunks | `4` |
| Reducer workers | `4` |
| Reducer wall time seconds | `13.55` |
| Output files | `304` |
| Output bytes | `121,016` |
| Scratch root files | `309` |
| Scratch root bytes | `207,258` |
| Manifest bytes | `60,703` |
| Sidecar files | `2` |
| Sidecar bytes | `215` |

Output-family pressure:

| Family | Files | Bytes |
| --- | ---: | ---: |
| `trajectory_csv` | `100` | `39,879` |
| `deposition_csv` | `100` | `10,400` |
| `impact_events_csv` | `100` | `13,980` |
| `trajectory_merge_state` | `1` | `110` |
| `reducer_merge_state` | `1` | `105` |

Manifest sizes:

| Manifest | Bytes |
| --- | ---: |
| `command_plan` | `1,066` |
| `probe_manifest` | `3,095` |
| `merge_manifest` | `29,562` |
| `output_manifest` | `26,980` |

The reducer-pressure helper classifies the shape as
`multi_zone_dry_run_blocked` because manifest, output-family, and reducer
runtime pressure remain visible. This is a sizing result, not a submission
failure.

## Projection Boundary

The Swiss-wide envelope helper still reports the 100-zone case as
`projection_only` with planning decision `defer`.

Projected 100-zone hazard-planning bands:

| Band | Low | Nominal | High |
| --- | ---: | ---: | ---: |
| Runtime seconds | `133.779` | `178.4` | `552.77` |
| Storage bytes | `12,862,070` | `39,536,020` | `2,675,271,200` |
| File count | `60` | `170` | `1,910` |
| Peak memory MB | `367.018` | `409.22` | `411.058` |

The readiness matrix keeps the 100-zone class at
`projection_only_deferred`, with `reducer_pressure` as the next blocker.

## Balfrin State At Preparation

Read-only Balfrin checks showed:

- login host: `balfrin-ln003`
- `$SCRATCH` filesystem: `/scratch/mch`
- scratch availability: about `45T` available on an `800T` filesystem, `95%`
  used
- `postproc` state: busy with running jobs, so this task stopped at package
  preparation as intended

## Pre-Submit No-Go Conditions

Do not submit this package if any of these are true:

- the remote checkout cannot fast-forward to the intended commit;
- the run root is not under `/scratch/mch/olifu/rust_rockfall`;
- available `$SCRATCH` space is materially below the prepared package and
  expected output budget plus cleanup margin;
- `postproc` queue state makes a bounded single-node diagnostic likely to sit
  or run outside the standing clearance;
- a later readiness matrix no longer classifies the 100-zone step as a useful
  diagnostic;
- the task intent shifts from diagnostic reducer pressure into hazard,
  operational, distributed, or physical-probability evidence.

## Boundary

This task prepared a package and measured the same diagnostic shape locally. It
did not submit a 100-zone job, produce Balfrin runtime/memory evidence, expand
to Swiss-wide execution, or create operational hazard, annual-frequency,
physical-probability, risk, exposure, or vulnerability claims.
