# Multi-Zone Reducer Pressure Probe

Status: scratch-root probe, not a live Balfrin run.

This probe materializes a deterministic multi-zone scratch root and summarizes
the reducer/merge pressure, reducer-manifest bytes, sidecar counts, and
output-family bytes without relying on ignored live artifacts.

Reproduce with:

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py \
  --materialize-root /tmp/rust_rockfall/tb187_multi_zone_probe \
  --format json
```

## Measured Summary

- Probe root: `/tmp/rust_rockfall/tb218_multi_zone_probe`
- Release zones: `12`
- Scenarios: `12`
- Trajectory chunks: `12`
- Reducer workers: `2`
- Reducer chunks: `4`
- Merge order: `sorted_chunk_id`
- Merge-order independent: `true`
- Merge-order deterministic: `true`
- Reducer wall time: `2.99` s
- Manifest size: `21312` bytes
- Root file count: `66`
- Output file count: `62`
- Output bytes: `31906`
- Reducer manifest bytes: `964`
- Reducer manifest files: `4`
- Sidecar files: `21`
- Sidecar bytes: `4123`
- Primary output files: `36`
- Primary output bytes: `7586`
- Output family mix: `trajectory_csv, deposition_csv, impact_events_csv, trajectory_chunk_manifest, reducer_chunk_manifest, trajectory_execution_plan, trajectory_execution_index, trajectory_merge_state, reducer_execution_plan, reducer_execution_index, reducer_merge_state, diagnostics_json, map_package_manifest, pilot_gis_package_manifest`

## Output Families

- `trajectory_csv`: `12` files / `4678` bytes
- `trajectory_chunk_manifest`: `12` files / `2340` bytes
- `impact_events_csv`: `12` files / `1660` bytes
- `deposition_csv`: `12` files / `1248` bytes
- `reducer_chunk_manifest`: `4` files / `964` bytes
- `trajectory_execution_index`: `1` file / `422` bytes
- `reducer_execution_index`: `1` file / `226` bytes
- `reducer_merge_state`: `1` file / `105` bytes
- `pilot_gis_package_manifest`: `1` file / `105` bytes
- `map_package_manifest`: `1` file / `93` bytes
- `trajectory_merge_state`: `1` file / `109` bytes
- `trajectory_execution_plan`: `1` file / `76` bytes
- `reducer_execution_plan`: `1` file / `72` bytes
- `diagnostics_json`: `1` file / `143` bytes

## Bottleneck Labels

- `merge_order`: `sorted_chunk_id_deterministic`
- `manifest_size`: `manifest_pressure`
- `output_pressure`: `file_family_pressure`
- `reducer_runtime`: `reducer_runtime_pressure`
- `probe_blocker`: `multi_zone_dry_run_blocked`

## Recommended Reducer Constraints For TB-183

- Keep `merge_order` at `sorted_chunk_id`.
- Keep `merge_order_independent` set to `true`.
- Hold `reducer_worker_count` at `2` until a larger scratch probe says otherwise.
- Cap `reducer_chunk_count` at `4` for the next probe.
- Stage simultaneous release zones in batches of at most `8`.

## Conclusion

Reducer pressure is a blocker for a multi-zone Balfrin dry run at this probe
shape. The dominant signals are manifest pressure, output-family pressure, and
reducer-runtime pressure, so TB-183 should keep the reducer constraints above
in place before attempting a larger dry run.

## Regression Gate

The fixture-backed regression gate that enforces these budgets is:

```bash
PYENV_VERSION=system uv run python scripts/validate_multi_zone_reducer_pressure_gate.py \
  --materialize-root /tmp/rust_rockfall/tb218_multi_zone_gate_probe \
  --format json
```

Its warning and blocked thresholds are themselves fixture-backed and are
derived from deterministic 9-zone and 11-zone scratch profiles until real
Balfrin roots are measured.

## Handoff-Derived Projection

The scratch probe remains the reducer-pressure measurement source, but the
Balfrin multi-release-zone handoff now also projects the output budget from
the concrete `multi_zone_reducer_pressure_summary` command in its command
plan. That projection runs the fixture-backed gate against the command-plan
shape and records primary outputs, reducer manifests, sidecars, manifest
bytes, per-family budget checks, and first bottleneck labels in the handoff
package. If the projected command-plan shape exceeds the current gate, the
handoff package remains fail-closed even when the smaller requested submit
shape is otherwise within measured reducer maxima.

## TB-245 Current Handoff Projection

The current TB-245 recheck still stays `blocked_budget_reduction_needed`
rather than `budget_passes_no_reduction_needed`. The full baseline projection
records `12` release zones, `62` output files, `36432` output bytes, `26057`
manifest bytes, `21` sidecar files, and `964` reducer-manifest bytes.

TB-246 adds a compact manifest-pruning path that keeps the replay-safe
primary outputs plus the merge-state files and projection hashes while
pruning the chunk-manifest, execution-plan, execution-index, diagnostics, and
GIS sidecars. That compact projection now records `39` output files,
`23772` output bytes, `17788` manifest bytes, `2` sidecar files, and `0`
reducer-manifest bytes, but it still remains `blocked_budget_reduction_needed`
because the first blocked label is still `manifest_size_bytes`.

The compact projection now makes the replay-critical boundary explicit:
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state` remain, along with the
`probe_manifest`, `command_plan`, and `output_manifest` SHA-256 hashes that the
handoff report records for provenance. The budget can therefore be rechecked
without mutating the live handoff semantics, while still reporting the exact
remaining fields that prevent a smaller manifest.

## TB-266 Smallest Multi-Zone Handoff Budget Repair

The reviewed two-release-zone probe shape is still fail-closed, but the repair
path now reports a compact before/after budget envelope instead of only a
generic manifest-pressure label:

- Before: `62` output files, `21` sidecar files, `964` reducer-manifest bytes,
  `26057` manifest bytes.
- After compact pruning: `39` output files, `2` sidecar files, `0`
  reducer-manifest bytes, `17788` manifest bytes.

The retained replay-critical families are
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`. The blocker is still
`manifest_size_bytes`, but the follow-on report now keeps the replay-critical
field inventory and the compact retained families explicit so the next review
can see exactly what cannot be removed to pass the budget.

## Smallest Authorization Preflight Shape

The smallest bounded multi-zone authorization preflight consumes the reviewed
handoff package, a live-run authorization record, and the Balfrin read-only
access report before the submit path can reach `sbatch`:

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py \
  --reviewed-handoff-package /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml \
  --balfrin-access-preflight-json /tmp/balfrin_remote_access_preflight_tb226.json \
  --format json
```

For the reviewed smallest handoff, the reported run shape is `2` release
zones, `2` scenarios, `2` trajectory workers, `2` reducer workers, `2` reducer
chunks, summary-only conditional curves, no grid CSV export, GeoTIFF export,
and pilot GIS packaging. This stays within the measured reducer constraints
above while retaining the non-operational, no-scale-up, and no-distributed-run
boundaries.

TB-247 refreshes the preflight decision branch so the machine-readable answer is
one of `ready_for_authorization_review`, `blocked_missing_authorization`,
`blocked_reducer_budget`, or `blocked_access`. The current compact handoff
budget is still consumed before the authorization-record branch, so the
remaining `blocked_budget_reduction_needed` manifest-size blocker keeps the
smallest package at `blocked_reducer_budget` rather than making it reviewable.
The Balfrin access report status is still recorded separately, and the preflight
continues to state that it does not grant authorization or permit live
submission.

## TB-268 Evidence Integration Status

TB-267 did not produce measured multi-zone Balfrin evidence. The Balfrin access
preflight passed read-only, but the smallest two-release-zone authorization
preflight failed closed before submission with `blocked_reducer_budget`; the
first reducer/output bottleneck was `manifest_size_bytes`, and the required
authorization record was missing. No SLURM job id, metrics JSON, preservation
gate, or post-run collector output was promoted.

The current reducer-pressure, evidence-bundle, closure, next-action, and
Swiss-wide envelope helpers therefore classify the multi-zone state as
`blocked_incomplete`, not measured. The scaling frontier is a no-go until the
manifest-size reducer-budget blocker and the missing authorization record are
resolved. If a future preservation-checked two-zone Balfrin root is supplied,
the helpers can move the frontier to a reviewed next-larger package, but they
still keep `scale_up_authorized=false` and do not authorize a larger run.

## TB-287 Smallest Two-Zone Probe Gate

TB-287 did not submit a live Balfrin job. No separate exact user authorization
for the bounded two-zone submit was present at execution time, so no
`--authorized-submit` command or `sbatch` call was run.

The current read-only preflight also fails before submission with the exact
helper blocker `blocked_dirty_remote_checkout`: the Balfrin checkout reports no
tracked modifications, but it still contains untracked generated run files,
SLURM logs, and scratch helper scripts. The refreshed smallest authorization
preflight over `/tmp/tb287_balfrin_access_preflight.json` reports
`preflight_status=blocked_access`,
`balfrin_access_status=blocked_dirty_remote_checkout`,
`reducer_budget_status=ready`, `output_profile_status=ready`, and the
authorization record remains `missing`. The authorization-gated path report
keeps `submit_command_executed=false` and promotes no measured result.
