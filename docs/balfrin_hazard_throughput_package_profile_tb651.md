# TB-651 Larger Hazard-Throughput Package Profile

Date: 2026-05-27

## Result

The larger local profile now produces a bounded >4-zone candidate rather than an
output-budget blocker. The 8-zone handoff package is budget-acceptable under the
current fixture-backed thresholds, with warnings because it sits on the measured
limit for release-zone batch size, reducer chunks, and reducer workers.

The package is therefore technically ready for the next bounded review/submit
step, subject to the submit path carrying an explicit authorization flag.

## Commands

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py \
  --materialize-root /tmp/tb651_multi_zone_profile \
  --profile multi_zone \
  --format json \
  --json-output /tmp/tb651_multi_zone_profile.json \
  --markdown-output /tmp/tb651_multi_zone_profile.md

PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py \
  --artifact-dir /tmp/tb651_handoff_8 \
  --requested-release-zone-batch-size 8 \
  --requested-reducer-chunk-count 2 \
  --requested-reducer-worker-count 2 \
  --format json \
  --json-output /tmp/tb651_handoff_8.json

PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py \
  --format json > /tmp/tb651_rebuild_output_profile.json
```

## Local Hazard-Throughput Profile

- Profile status: `profiled_scratch_root`
- Profile id: `multi_zone`
- Release-zone count: `12`
- Output files: `29`
- Output bytes: `1,144,550`
- Total wall time: `0.148265` seconds
- Largest phase: `accumulation_seconds` at `0.037769` seconds

File-family counts:

- `geotiff`: `11` files / `813,890` bytes
- `esri_ascii_grid`: `11` files / `280,720` bytes
- `json`: `6` files / `46,440` bytes
- `geojson`: `1` file / `3,500` bytes

Manifest-family bytes:

- `reducer_execution_plan`: `13,746`
- `reducer_chunk_manifest`: `13,645`
- `hazard_metadata`: `13,035`
- `reducer_execution_index`: `3,855`

The dominant local phase is trajectory accumulation. The next optimization
target remains batching or vectorizing trajectory-cell updates while preserving
per-cell maxima, reach counts, exceedance semantics, and reducer merge
determinism.

## 8-Zone Handoff Package

- Review readiness: `ready_for_review`
- Submission classification: `blocked_pending_new_human_authorization`
- Authorization classification: `blocked_pending_authorization`
- Scenario pressure: `warning`
- Requested release-zone batch size: `8`
- Requested reducer chunk count: `2`
- Requested reducer worker count: `2`
- Scenario count: `24`

Output-budget projection:

- Gate status: `fixture_backed_ready`
- Projection status: `acceptable`
- Output files: `35`
- Output bytes: `26,422`
- Manifest bytes: `22,570`
- Primary output files: `24`
- Primary output bytes: `5,042`
- Sidecar files: `9`
- Sidecar bytes: `1,560`

Replay-critical families retained:

- `trajectory_csv`
- `deposition_csv`
- `impact_events_csv`
- `trajectory_merge_state`
- `reducer_merge_state`

Constraint-pressure warnings:

- `simultaneous_release_zone_batch_size=8` reaches the measured max `8`
- `reducer_chunk_count=2` reaches the measured max `2`
- `reducer_worker_count=2` reaches the measured max `2`
- scenario pressure first warning: `release_zone_count`

## Decision

The package no longer fails closed on output, manifest, or replay-critical
retention. It is a bounded 8-zone candidate at the current measured constraint
limit. The next Balfrin task should either submit this bounded candidate with the
explicit approved submit flag, or record the exact remote/access/queue blocker.

No operational, physical-probability, annual-frequency, risk, exposure,
vulnerability, Swiss-wide, distributed, or non-`postproc` claim is made by this
profile.
