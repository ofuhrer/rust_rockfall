# Balfrin 100-Zone Diagnostic Run TB-612

Date: 2026-05-26

Status: measured 100-zone diagnostic reducer-pressure run on Balfrin
`postproc`.

Run root:

`/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526`

Remote checkout:

`/users/olifu/work/rust_rockfall`

Job:

- SLURM job id: `4372447`
- partition: `postproc`
- job name: `rr-diag-100z`
- state: `COMPLETED`
- exit code: `0:0`
- elapsed: `00:00:01`
- requested CPUs: `16`
- allocated CPUs: `16`
- batch MaxRSS: `5,468K`
- `/usr/bin/time -v` maximum RSS: `34.16 MB`
- `/usr/bin/time -v` elapsed: `0:01.26`

## Command

The submitted command used the prepared TB-611 package:

```bash
PYENV_VERSION=system uv run python scripts/run_balfrin_diagnostic.py run \
  --release-zones 100 \
  --reducer-chunks 4 \
  --reducer-workers 4 \
  --manifest-mode compact \
  --run-root /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526 \
  --time 00:30:00 \
  --poll-seconds 30 \
  --monitor-timeout-seconds 21600 \
  --format text
```

Final runner summary:

```text
status: completed
run_root: /scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526
job_id: 4372447
release_zone_count: 100
pressure_status: measured_scratch_root
output_file_count: 304
output_byte_count: 121172
max_rss_mb: 34.16
```

## Collected Pressure Evidence

The collected run record reports:

| Measure | Value |
| --- | ---: |
| Release zones | `100` |
| Scenarios | `100` |
| Reducer chunks | `4` |
| Reducer workers | `4` |
| Reducer wall time seconds | `13.55` |
| Output files | `304` |
| Output bytes | `121,172` |
| Pressure-root files | `309` |
| Pressure-root bytes | `212,978` |
| Run-root files | `318` |
| Run-root bytes | `448,376` |
| Manifest bytes | `61,119` |
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
| `command_plan` | `1,222` |
| `probe_manifest` | `3,199` |
| `merge_manifest` | `29,666` |
| `output_manifest` | `27,032` |

The pressure helper still labels the synthetic reducer shape as
`multi_zone_dry_run_blocked` because manifest, output-family, and reducer
runtime pressure remain visible. That label is the helper's pressure
classification, not a scheduler failure.

## Interpretation

This run establishes measured single-node `postproc` scheduler evidence for a
100-zone diagnostic reducer-pressure workload. It materially extends the
diagnostic series beyond 16, 24, 32, and 40 zones.

It does not establish 100-zone hazard throughput, physical probability,
operational readiness, distributed execution, non-`postproc` behavior, or
Swiss-wide execution. The next step is to promote the measured diagnostic
series into the Swiss-scale feasibility projection and keep the distinction
between diagnostic reducer pressure and hazard/scientific claims.
