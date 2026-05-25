# TB-569 16-Zone Reduced-Output Handoff

Date: 2026-05-25

This records a no-submit 16-zone reduced-output handoff build. It generated a
review package only; no `sbatch` command was run, no live job was submitted, and
no operational, physical-probability, or scale-up claim is made.

## Command

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py \
  --artifact-dir /tmp/rust_rockfall/tb569_16_zone_handoff \
  --pressure-probe-root /tmp/rust_rockfall/tb569_16_zone_pressure \
  --requested-release-zone-batch-size 16 \
  --requested-reducer-chunk-count 2 \
  --requested-reducer-worker-count 2 \
  --format json \
  --json-output /tmp/rust_rockfall/tb569_16_zone_handoff/package.json \
  --text-output /tmp/rust_rockfall/tb569_16_zone_handoff/package.txt
```

The helper exited with status `2`, which is the expected fail-closed status for
a blocked no-submit package.

## Result

- Package status: `mixed_provenance`
- Package constraint status: `blocked`
- No-submit handoff status: `blocked`
- `sbatch_attempted`: `false`
- `balfrin_job_submitted`: `false`
- Requested release-zone batch size: `16`
- Requested reducer chunk count: `2`
- Requested reducer worker count: `2`
- Measured simultaneous release-zone batch max: `8`
- Measured reducer chunk max: `2`
- Measured reducer worker max: `2`

First blockers:

- Scenario/reducer gate: `release_zone_count`
- Handoff output-budget projection: `output_file_count`

The compact projection reduced manifest pressure to `16034` bytes, but it still
blocked on `52` output files and retained replay-critical families:
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`.

## Recovery

The package reports this recovery command as the current safe fallback:

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py \
  --artifact-dir /private/tmp/rust_rockfall/tb569_16_zone_handoff \
  --requested-release-zone-batch-size 2 \
  --requested-reducer-chunk-count 2 \
  --requested-reducer-worker-count 2 \
  --format json
```

For a true next larger package, the concrete follow-up is to reduce reducer and
replay metadata pressure before rebuilding the 16-zone handoff.
