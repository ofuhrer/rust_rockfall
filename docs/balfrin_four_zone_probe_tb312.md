# TB-312 Four-Zone Balfrin Postproc Probe

Date: 2026-05-19

## Submission

- Job id: `4340075`
- Run root: `/scratch/mch/olifu/rust_rockfall/probes/tb312_four_zone_postproc_probe_v1/tb312_20260519T224500Z`
- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote commit: `644250e62fa78f9d92c137d374446e8660b6c4a7`
- Partition: `postproc`
- Requested shape: one node, one task, `16` CPUs per task, `00:30:00` time cap
- SLURM state: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:11`
- Batch peak RSS: `5460K` (`5.33203125` MiB)

Pre-submit gates were rerun after fast-forwarding the Balfrin checkout from
`34ead5c8e39842e66c1051a7e474180296a1bbd6` to
`644250e62fa78f9d92c137d374446e8660b6c4a7`. The refreshed access preflight was
`ready_for_read_only_collection`, `ready_for_pre_submit=true`, with remote
checkout hygiene `pass` and dirty path count `0`.

The local scale dashboard reported the four-zone review package as
`ready_for_review` with output-budget status `accepted`, expected runtime
`0.997` seconds, expected file count `21`, and expected manifest pressure
`7104` bytes. The submitted job used the exact four-zone compact
post-processing/reducer package shape: `4` release zones, `4` scenarios,
`2` reducer chunks, and reduced-output families retained for replay.

## Measured Evidence

- Collected run-root status: `measured_run_root`
- Metrics contract: `complete`
- Probe wall time from the four-zone pressure manifest: `1.63` seconds
- Memory peak from SLURM accounting: `5.33203125` MiB
- Trajectory decision counts: `executed: 4`
- Reducer decision counts: `executed: 2`
- Preservation gate: `ready_for_demonstration_evidence`
- Output-budget audit profile: `next_larger_four_zone_review_only_probe`
- Output-budget audit: `compliant`
- Output-budget acceptance: `accepted`

Output-budget projection from the preserved run root:

- Output files: `25`
- Output bytes: `10238`
- Manifest bytes: `12220`
- Sidecar files: `10`
- Reducer chunks: `2`
- Reducer manifest bytes: `0`

Measured output-family counts:

- `trajectory_csv`: `4`
- `deposition_csv`: `4`
- `impact_events_csv`: `4`
- `trajectory_chunk_manifest`: `4`
- `reducer_chunk_manifest`: `2`
- `trajectory_merge_state`: `1`
- `reducer_merge_state`: `1`
- `map_package_manifest`: `1`
- `pilot_gis_package_manifest`: `1`

Replay hashes:

- `probe_manifest_sha256`: `6eccf5362b7a6752c2ffd4711b386f9e0fbf975f841cafff31f7bf1eb46f68f3`
- `command_plan_sha256`: `5ea6cb093cc6f47e2a7c5284b9f9f4b2df8705d5663f3e0a545a9f71b03346ac`
- `output_manifest_sha256`: `ba02b8dd51c585d8109eb4c29cfa7c6fc7d460ff247807ee8fe10bd7522e5854`

## Boundary

This is measured Balfrin `postproc` evidence for the exact four-zone compact
post-processing/reducer package only. It is not a hazard execution, not a
Swiss-wide scale-up, not distributed execution, not an annual-frequency or
physical-probability result, not risk/exposure/vulnerability evidence, and not
an operational hazard assessment.
