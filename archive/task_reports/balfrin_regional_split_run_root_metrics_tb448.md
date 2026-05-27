# Balfrin Regional Split Run-Root Metrics TB-448

- Collection time: `2026-05-22T00:40:53Z`
- Classification: `measured_run_root`
- Preservation status: `ready_for_demonstration_evidence`
- Job id: `4350232`
- Run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Remote checkout head during access preflight: `faef6d8ec055b0a9457932d4659a4c5f7f4c7399`
- Raw collection snapshots kept outside the repo: `/tmp/tb448_regional_split_metrics.json`, `/tmp/tb448_regional_split_preservation_gate.json`, `/tmp/tb448_slurm_accounting_4350232.psv`, `/tmp/tb448_remote_inventory_all.psv`, `/tmp/tb448_validation_family_counts.json`, `/tmp/tb448_slurm_4350232_log_tail.txt`

## Metrics Summary

- Metrics contract status: `complete`
- Validation output total: `130` files / `34,565,323` bytes
- Hazard output total: `53` files / `55,837,701` bytes
- Conditional curve rows: `729600`
- Collector wall time: `6.738646155004972` seconds
- Collector peak-memory field: `172.921875` MB
- Log audit: `nominal`, with `0` warning-like and `0` error-like lines

The live scheduler query for job `4350232` reported `State=COMPLETED`,
`ExitCode=0:0`, `Elapsed=00:00:24`, `AllocCPUS=16`, and batch-step
`MaxRSS=5488K`. The reused run root still contains older
`slurm_accounting_*.psv` files but no `slurm_accounting_4350232.psv`; therefore
the job-specific scheduler memory evidence is the `sacct` value above, while
the collector peak-memory field remains the preserved run-root/accounting
fallback value.

## Validation Output Families

The validation output total comes from the collector's command-plan footprint.
Direct command-plan validation families were:

| Family | Files | Bytes |
| --- | ---: | ---: |
| `diagnostics_json` | 1 | 3,778 |
| `trajectory_csv` | 1 | 244,190 |
| `deposition_csv` | 1 | 8,139 |
| `ensemble_trajectories_dir` | 60 | 14,462,028 |
| `ensemble_impact_events_dir` | 60 | 19,758,731 |

The family split above covers the explicit validation outputs referenced by
the command flags. The collector total is larger because it also counts
additional preservation files under the validation output parent directory.

## Hazard And Replay Families

Measured hazard/replay family counts from the preserved hazard manifest:

| Family | Count |
| --- | ---: |
| `hazard_layer` | 32 |
| `deposition_points` | 1 |
| `hazard_metadata` | 1 |
| `map_package_manifest` | 1 |
| `pilot_gis_package_manifest` | 1 |
| `trajectory_execution_plan` | 1 |
| `trajectory_execution_index` | 1 |
| `trajectory_merge_state` | 1 |
| `trajectory_chunk_manifest` | 2 |
| `reducer_execution_plan` | 1 |
| `reducer_execution_index` | 1 |
| `reducer_merge_state` | 1 |
| `reducer_chunk_manifest` | 2 |

The reducer/replay metadata is measured with trajectory plan id
`validation_balfrin_probe__trajectory_execution_plan__baa8922e4f488be92aa3007d`,
reducer plan id
`validation_balfrin_probe__execution_plan__cf958510cadf9a49a7c23873`,
trajectory decision counts `{"reused_completed_state": 2}`, reducer decision
counts `{"completed_state_reset_for_rerun": 2}`, merge order
`sorted_chunk_id`, and `merge_order_independent=true`.

## Preservation Evidence

The preservation gate reported:

- Gate status: `ready_for_demonstration_evidence`
- Metrics contract status: `complete`
- Required run-root entries status: `complete`
- Missing run-root entries: `[]`
- Output-family status: `sufficient`
- Missing required output families: `[]`
- Spatial/GIS artifact status: `declared`
- Blocked reasons: `[]`

Measured checksum entries were complete for:

| Label | Bytes | SHA-256 |
| --- | ---: | --- |
| `command_plan` | 6,794 | `2921b3eccba4d087efa7fca3581fcdd763c01467b3302a6532591a93fa4bd07c` |
| `probe_metrics` | 20,952 | `59accce6f186a244e1916ef4088b450736a5a268119fc36a18b7b3ae2cb375b8` |
| `hazard_manifest` | 92,458 | `fbb283417d8e8bb698e8d14567f7d815c16910eddda213032ab1820c078d3a52` |
| `scaling_summary` | 1,166 | `402f093432e8ab3f89ea97043d7736c2a54e70cdc2f8a835cdc771b0354b6cc7` |

Replay-critical pointers:

- Command plan: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/command_plan.json`
- Probe metrics: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/balfrin_probe_metrics.json`
- Output root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/output`
- Hazard manifest: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/output/validation_balfrin_probe_manifest.json`
- Scaling summary: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/output/validation_balfrin_probe_scaling_summary.json`
- Logs: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/logs`

## Boundary Note

This is read-only preservation and metrics collection for one completed
regional split `postproc` run root. It does not authorize a rerun, a non-`postproc`
partition, distributed execution, scale-up, operational hazard assessment,
annual-frequency claims, physical-probability claims, risk, exposure, or
vulnerability claims.
