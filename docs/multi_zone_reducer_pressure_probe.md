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
