# TB-602 Hazard-Throughput Submission Package

Date: 2026-05-26

TB-602 prepared the next bounded hazard-throughput package and stopped at the
no-submit boundary. The package is ready for a later `postproc` submission.

## Package Status

- Status: `ready_for_bounded_postproc_submission`
- First blocker: none
- Balfrin remote HEAD: `71dedd44ccb4d396d1d76ead23da454be6aa39ec`
- Local package source HEAD: `71dedd44ccb4d396d1d76ead23da454be6aa39ec`
- Package artifact root: `/private/tmp/tb602_hazard_throughput_submission_package`
- Package JSON: `/private/tmp/tb602_hazard_throughput_submission_package/balfrin_regional_split_submission_package_v1.json`
- Package text: `/private/tmp/tb602_hazard_throughput_submission_package/balfrin_regional_split_submission_package_v1.txt`
- Handoff package: `/private/tmp/tb602_hazard_throughput_submission_package/handoff/balfrin_multi_release_zone_demo_package_v1.json`
- Authorization record: `/private/tmp/tb602_hazard_throughput_submission_package/handoff/balfrin_multi_zone_live_authorization_record_v1.yaml`

The generated package artifacts are scratch artifacts and are not committed.
The planned Balfrin run root is under `$SCRATCH`:

`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`

## Output Controls

The reviewed package keeps the scalable output profile:

- conditional-curve export: `summary-only`
- grid CSV export: `none`
- plots: disabled
- manifest mode: `compact`
- replay-critical families retained: `trajectory_csv`, `deposition_csv`,
  `impact_events_csv`, `trajectory_merge_state`, `reducer_merge_state`

The compact handoff reduced manifest pressure from `14056` to `8657` bytes and
sidecar files from `9` to `2`. The output-budget acceptance status is
`accepted`.

## Later Submit Command

The package records this exact later command but did not execute it:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /private/tmp/tb602_hazard_throughput_submission_package/handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /private/tmp/tb602_hazard_throughput_submission_package/handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

## Local Hazard-Throughput Profile

A local deterministic profile was also materialized at
`/tmp/tb602_hazard_throughput_profile` using the existing
`multi_zone_hazard_throughput_profile_v2` helper. It profiled 12 release zones
with explicit and auto grid modes. The dominant measured phase was
`accumulation_seconds`, and output pressure was led by GeoTIFF files in the
fixture. This profile is scratch evidence for package review only; the next
capability step is the Balfrin submission in TB-603.

## No-Submit Boundary

No Balfrin job was submitted by TB-602:

- `sbatch_attempted`: false
- `submit_command_executed`: false
- `balfrin_job_submitted`: false
- package generation only: true

This task changes the readiness state for the next bounded hazard-throughput
submission. It does not add operational, physical-probability, Swiss-wide,
distributed, risk, or non-`postproc` evidence.
