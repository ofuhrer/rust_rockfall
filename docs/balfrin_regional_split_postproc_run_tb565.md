# Balfrin Regional Split Postproc Run TB-565

Date: 2026-05-25

This note records one bounded regional split `postproc` run submitted from the
reviewed TB-564 package gates. It is measured Balfrin execution evidence only;
it does not authorize distributed execution, Swiss-wide execution, operational
hazard products, annual-frequency products, physical-probability claims, risk,
exposure, or vulnerability claims.

## Package And Queue Context

- Remote package root: `/scratch/mch/olifu/rust_rockfall/submission_packages/tb565_regional_split_package`
- Remote package generation transcript: `/tmp/tb565_remote_package_generation.txt`
- Package generation checkout HEAD: `0008dccc14b292d6fb8981a55acc71df74bdfa76`
- Package status: `ready_for_bounded_postproc_submission`
- First blocker: `None`
- Authorization preflight status: `ready_for_authorization_review`
- Remote/local head alignment: `0008dccc14b292d6fb8981a55acc71df74bdfa76`
- Package JSON SHA-256: `9874d7304f478f8670488b9fcbf567906094fee49cc3510b0b7d188dc00e22b8`
- Package text SHA-256: `0460458158192aa3ce54437df7d65d26df5bdb9efbf7e03245d7e4a9871dc0ac`
- Access preflight SHA-256: `120726b979448a5753d82ee1fcbb9792da7b5282e74c19f338b257e873ed0ad7`
- Reviewed handoff package SHA-256: `f76d904107b421d330513ded82d31fc124e61d8cded7bc13e7986380c92194a0`
- Authorization record SHA-256: `d3dc27a03a467ca2778e2c314fba1d23fb8f6c3774cf7c630e4e5ea228405cdb`

The final pre-submit queue snapshot was captured at `2026-05-25T19:27:39Z`.
It showed 11 idle `postproc` nodes, two mixed nodes, one reserved node, and no
blocking pending jobs. `/scratch/mch` was close to full but still reported
about `8.9T` available.

Because Balfrin `/tmp` is `tmpfs`, the package helper was updated before
submission to allow reviewed package roots under
`/scratch/mch/olifu/rust_rockfall`. The task did not use Balfrin `/tmp` for
package roots or run roots.

## Submission

- Submit transcript: `/tmp/tb565_submit_output.txt`
- Submitted at: `2026-05-25T19:28:20Z`
- Job id: `4367244`
- Partition: `postproc`
- Run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Nodes: `1`
- Tasks: `1`
- CPUs per task: `16`
- Time limit: `00:30:00`

## Scheduler Result

- Monitor transcript: `/tmp/tb565_job_4367244_monitor.txt`
- Evidence transcript: `/tmp/tb565_job_4367244_evidence.txt`
- Job state: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:24`
- Node: `nid001225`
- Batch-step MaxRSS: `5512K`
- Extern-step MaxRSS: `700K`

The run root contains a stale `balfrin_submission_report.json` from an earlier
blocked attempt. The TB-565 result therefore uses the job-specific `sacct`
record, new `slurm-4367244` logs, updated command plan, and updated metrics
files rather than that stale report.

## Measured Run-Root Outputs

- Context git hash: `0008dccc14b292d6fb8981a55acc71df74bdfa76`
- Full run time from run-root file: `23.070187418023124` seconds
- Hazard-stage time from run-root file: `6.210399252013303` seconds
- Metrics contract status: `complete`
- Validation output: `130` files / `34,565,330` bytes
- Hazard output: `57` files / `57,670,915` bytes
- Conditional curve rows: `729600`
- Collector total wall seconds: `5.261369686049875`
- Collector memory peak: `172.921875` MB
- Run-root status: `measured_run_root`

Current file hashes:

| File | SHA-256 |
| --- | --- |
| `command_plan.json` | `2921b3eccba4d087efa7fca3581fcdd763c01467b3302a6532591a93fa4bd07c` |
| `probe.sbatch` | `1dd53ab977233248e2e1f19188e32fe2773c0dff3984cad5e51eca840d66afb3` |
| `balfrin_probe_metrics.json` | `c66b4845a9cd6b86ab5ee19f19de6817b2da36d28f04fddac31b9a859b3246d0` |
| `balfrin_probe_summary.json` | `c66b4845a9cd6b86ab5ee19f19de6817b2da36d28f04fddac31b9a859b3246d0` |
| `logs/slurm-4367244.out` | `400690d7320396bf4585a45a18aca12ea1f62c51af4fa8c070baa189c74a3d42` |
| `logs/slurm-4367244.err` | `86c751cc23fa1c7be44897cdf2d48ee5b81c3a38d7e520890a854c100651bbff` |

## Log Tail Summary

The job log reported valid public real-site geodata and source-zone policy
inputs, a passing validation case, hazard layers written to the run-root
`output` directory, and a probe metrics summary written to the run root. The
stderr log contained the Rust build/run line and no job-failure text.
